########################################################################
# File name: xhu.py
# This file is part of: xmpp-http-upload
#
# LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
########################################################################
import contextlib
import errno
import fnmatch
import hashlib
import hmac
import json
import os
import pathlib
import shutil
import stat
import typing

import flask

app = flask.Flask("xmpp-http-upload")
app.config.from_envvar("XMPP_HTTP_UPLOAD_CONFIG")
application = app


if app.config['ENABLE_CORS']:
    from flask_cors import CORS
    CORS(app)


def sanitized_join(path: str, root: pathlib.Path) -> pathlib.Path:
    result = (root / path).absolute()
    if not str(result).startswith(str(root) + "/"):
        raise ValueError("resulting path is outside root")
    return result


def get_paths(base_path: pathlib.Path):
    data_file = pathlib.Path(str(base_path) + ".data")
    metadata_file = pathlib.Path(str(base_path) + ".meta")
    return data_file, metadata_file


def load_metadata(metadata_file):
    with metadata_file.open("r") as f:
        return json.load(f)


def get_info(path: str, root: pathlib.Path) -> typing.Tuple[
        pathlib.Path,
        dict]:
    dest_path = sanitized_join(
        path,
        pathlib.Path(app.config["DATA_ROOT"]),
    )
    data_file, metadata_file = get_paths(dest_path)
    return data_file, load_metadata(metadata_file)


def apply_quota(root: pathlib.Path, quota: int):
    """ Get the files, sorted by last modification date and the sum of their
        sizes.
    """
    if not quota:
        return

    file_list = []
    total_size = 0
    # We assume a file structure whereby files are are stored inside
    # uuid() directories inside the root dir and that there aren't any files in
    # the root dir itself.
    for uuid_dir in os.listdir(root):
        for path, dirnames, filenames in os.walk(root/uuid_dir):
            for name in [n for n in filenames if n.endswith('.data')]:
                fp = os.path.join(path, name)
                size = os.path.getsize(fp)
                total_size += size
                modified = os.stat(fp)[stat.ST_MTIME]
                file_list.append((modified, path, name, size))

    bytes = total_size - quota
    if (bytes > 0):
        # Remove files (oldest first) until we're under our quota
        file_list.sort(key=lambda a: a[0])
        while (bytes >= 0):
            modified, path, name, size = file_list.pop()
            shutil.rmtree(path)
            bytes -= size


@contextlib.contextmanager
def write_file(at: pathlib.Path):
    with at.open("xb") as f:
        try:
            yield f
        except:  # NOQA
            at.unlink()
            raise


@app.route("/")
def index():
    return flask.Response(
        "Welcome to XMPP HTTP Upload. State your business.",
        mimetype="text/plain",
    )


def stream_file(src, dest, nbytes):
    while nbytes > 0:
        data = src.read(min(nbytes, 4096))
        if not data:
            break
        dest.write(data)
        nbytes -= len(data)

    if nbytes > 0:
        raise EOFError


@app.route("/<path:path>", methods=["PUT"])
def put_file(path):
    try:
        dest_path = sanitized_join(
            path,
            pathlib.Path(app.config["DATA_ROOT"]),
        )
    except ValueError:
        return flask.Response(
            "Not Found",
            404,
            mimetype="text/plain",
        )

    verification_key = flask.request.args.get("v", "")
    length = int(flask.request.headers.get("Content-Length", 0))
    hmac_input = "{} {}".format(path, length).encode("utf-8")
    key = app.config["SECRET_KEY"]
    mac = hmac.new(key, hmac_input, hashlib.sha256)
    digest = mac.hexdigest()

    if not hmac.compare_digest(digest, verification_key):
        return flask.Response(
            "Invalid verification key",
            403,
            mimetype="text/plain",
        )

    content_type = flask.request.headers.get(
        "Content-Type",
        "application/octet-stream",
    )

    dest_path.parent.mkdir(parents=True, exist_ok=True, mode=0o770)

    quota = flask.request.args.get("q", "")
    if (quota):
        apply_quota(dest_path.parent.parent, int(quota))

    data_file, metadata_file = get_paths(dest_path)

    try:
        with write_file(data_file) as fout:
            stream_file(flask.request.stream, fout, length)

            with metadata_file.open("x") as f:
                json.dump(
                    {
                        "headers": {"Content-Type": content_type},
                    },
                    f,
                )
    except EOFError:
        return flask.Response(
            "Bad Request",
            400,
            mimetype="text/plain",
        )
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            return flask.Response(
                "Conflict",
                409,
                mimetype="text/plain",
            )
        raise

    return flask.Response(
        "Created",
        201,
        mimetype="text/plain",
    )


def generate_headers(response_headers, metadata_headers):
    for key, value in metadata_headers.items():
        response_headers[key] = value

    content_type = metadata_headers["Content-Type"]
    for mimetype_glob in app.config.get("NON_ATTACHMENT_MIME_TYPES", []):
        if fnmatch.fnmatch(content_type, mimetype_glob):
            break
    else:
        response_headers["Content-Disposition"] = "attachment"

    response_headers["X-Content-Type-Options"] = "nosniff"
    response_headers["X-Frame-Options"] = "DENY"
    response_headers["Content-Security-Policy"] = \
        "default-src 'none'; frame-ancestors 'none'; sandbox"


@app.route("/<path:path>", methods=["HEAD"])
def head_file(path):
    try:
        data_file, metadata = get_info(
            path,
            pathlib.Path(app.config["DATA_ROOT"])
        )

        stat = data_file.stat()
    except (OSError, ValueError):
        return flask.Response(
            "Not Found",
            404,
            mimetype="text/plain",
        )

    response = flask.Response()
    response.headers["Content-Length"] = str(stat.st_size)
    generate_headers(
        response.headers,
        metadata["headers"],
    )
    return response


@app.route("/<path:path>", methods=["GET"])
def get_file(path):
    try:
        data_file, metadata = get_info(
            path,
            pathlib.Path(app.config["DATA_ROOT"])
        )
    except (OSError, ValueError):
        return flask.Response(
            "Not Found",
            404,
            mimetype="text/plain",
        )

    response = flask.make_response(flask.send_file(
        str(data_file),
    ))
    generate_headers(
        response.headers,
        metadata["headers"],
    )
    return response
