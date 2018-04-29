#!/usr/bin/env python3
import os.path
import runpy

import setuptools
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

install_requires = [
    'flask~=0.12',
    'flask-cors~=3.0.3',
]

setup(
    name="xmpp-http-upload",
    version="0.3.0",
    description="Flask-based HTTP service to handle XMPP HTTP upload requests from Prosody mod_http_upload_external",
    long_description=long_description,
    url="https://github.com/horazont/xmpp-http-upload",
    author="Jonas Wielicki",
    author_email="jonas@wielicki.name",
    license="GPLv3+",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: POSIX",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: XMPP",
    ],
    keywords="xmpp http",
    install_requires=install_requires,
)
