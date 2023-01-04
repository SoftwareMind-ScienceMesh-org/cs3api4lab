# NOTE: this file was copied from https://github.com/jupyter-server/jupyter_server/blob/main/tests/services/contents
# and adjusted for the plugin use.

import json

from tornado.httpclient import HTTPClientError
from tornado.web import HTTPError


def expected_http_error(error, expected_code, expected_message=None):
    """Check that the error matches the expected output error."""
    is_expected = True
    e = error.value
    if isinstance(e, HTTPError):
        if expected_code != e.status_code:
            is_expected = False
        if expected_message is not None and expected_message != str(e):
            is_expected = False
        return is_expected
    elif any(
        [
            isinstance(e, HTTPClientError),
            isinstance(e, HTTPError),
        ]
    ):
        if expected_code != e.code:
            is_expected = False
        if expected_message:
            message = json.loads(e.response.body.decode())["message"]
            if expected_message != message:
                is_expected = False
    else:
        is_expected = False
    return is_expected
