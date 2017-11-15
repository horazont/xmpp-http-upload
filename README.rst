XMPP HTTP Upload Service
########################

This provides a Flask-based HTTP service which can be used with
`mod_http_upload_external <https://modules.prosody.im/mod_http_upload_external.html>`_.

Configuration
=============

The configuration file is specified using the environment variable
``XMPP_HTTP_UPLOAD_CONFIG``. It must contain the full path to the configuration
file.

The configuration file must contain the following keys:

``SECRET_KEY``
    A ``bytes`` object which is the shared secret between the Prosody module
    and this service. See the `mod_http_upload_external documentation
    <https://modules.prosody.im/mod_http_upload_external.html>`_ for details.

``DATA_ROOT``
    Path to the directory where the service stores the uploaded files.

Issues, Bugs, Limitations
=========================

* This service **does not handle any kind of quota**.
