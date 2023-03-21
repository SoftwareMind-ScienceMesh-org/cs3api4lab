from tornado.httputil import HTTPServerRequest
from unittest import TestCase
from cs3api4lab.validators import RequestValidator
import json
from tornado.web import HTTPError
from cs3api4lab.common.strings import Role, Grantee, State


class TestValidators(TestCase):

    def _mock_request_body_request(self):
        request = {}
        request['endpoint'] = '/'
        request['file_path'] = '/path'
        request['grantee'] = 'grantee'
        request['idp'] = 'idp'
        request['role'] = Role.VIEWER.value
        request['grantee_type'] = Grantee.USER.value
        return request

    def test_fails_post_share_request(self):
        # body = self._mock_request_body()
        # body['idp'] = ""
        # request = HTTPServerRequest(body=bytes(json.dumps(body).encode('utf-8')))
        # body = request.body.strip().decode("utf-8")
        # request = json.loads(body)
        # request = {}

        request = {}
        request['endpoint'] = '/'
        request['file_path'] = '/path'
        request['grantee'] = 'grantee'
        request['idp'] = 'idp'
        request['role'] = Role.VIEWER.value
        request['grantee_type'] = Grantee.USER.value

        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_post_share_request(request)
        self.assertEqual('Incorrect request: endpoint', cm.exception.log_message)

    def test_pass_post_share_request(self):
        request = {}
        request['endpoint'] = '/'
        request['file_path'] = '/path'
        request['grantee'] = 'grantee'
        request['idp'] = 'idp'
        request['role'] = Role.VIEWER.value
        request['grantee_type'] = Grantee.USER.value
        RequestValidator.validate_post_share_request(request)

    def test_pass_put_share_request(self):
        request = {}
        request['share_id'] = '123'
        request['role'] = Role.VIEWER.value
        RequestValidator.validate_put_share_request(request)

    def test_pass_put_received_share_request(self):
        request = {}
        request['share_id'] = '123'
        request['role'] = Role.VIEWER.value
        RequestValidator.validate_put_share_request(request)
    

