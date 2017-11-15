import flask

app = flask.Flask("xmpp-http-upload")


@app.route("/")
def index():
    return flask.Response(
        "Welcome to XMPP HTTP Upload. State your business.",
        mimetype="text/plain",
    )


@app.route("/<path:path>", methods=["PUT"])
def put_file(path):
    pass


@app.route("/<path:path>", methods=["HEAD"])
def head_file(path):
    pass


@app.route("/<path:path>", methods=["GET"])
def get_file(path):
    pass


