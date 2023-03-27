from unittest import TestCase
from cs3api4lab.validators import RequestValidator
from tornado.web import HTTPError
from cs3api4lab.common.strings import Role, Grantee


class TestValidators(TestCase):

    def test_validate_post_share_request(self):
        request = {}
        request['endpoint'] = '/'
        request['file_path'] = '/path'
        request['grantee'] = 'grantee'
        request['idp'] = 'idp'
        request['role'] = Role.VIEWER
        request['grantee_type'] = Grantee.USER
        RequestValidator.validate_post_share_request(request)

    def test_validate_post_share_request_fails(self):
        request = {}
        request['endpoint'] = '/'
        request['file_path'] = '/path'
        request['grantee'] = ''
        request['idp'] = 'idp'
        request['role'] = Role.VIEWER
        request['grantee_type'] = Grantee.USER

        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_post_share_request(request)
        self.assertEqual('Incorrect request: grantee', cm.exception.log_message)

    def test_validate_put_share_request(self):
        request = {}
        request['share_id'] = '123'
        request['role'] = Role.VIEWER
        RequestValidator.validate_put_share_request(request)

    def test_validate_put_share_request_fails(self):
        request = {}
        request['share_id'] = '123'
        request['role'] = 'role'
        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_put_share_request(request)
        self.assertEqual('Incorrect request: role', cm.exception.log_message)

    def test_validate_put_received_share_request(self):
        request = {}
        request['share_id'] = '123'
        request['role'] = Role.VIEWER
        RequestValidator.validate_put_share_request(request)

    def test_validate_put_received_share_request_fails(self):
        request = {}
        request['share_id'] = ''
        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_put_share_request(request)
        self.assertEqual('Incorrect request: share_id', cm.exception.log_message)

