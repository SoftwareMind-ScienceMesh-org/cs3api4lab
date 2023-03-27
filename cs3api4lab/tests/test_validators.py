from tornado.httputil import HTTPServerRequest
from unittest import TestCase
from cs3api4lab.validators import RequestValidator
from tornado.web import HTTPError
from cs3api4lab.common.strings import Role, Grantee, State


class TestValidators(TestCase):

    def test_validate_post_share_request(self):
        request = self._mock_request_body_request()
        RequestValidator.validate_post_share_request(request)

    def test_validate_post_share_request_fails(self):
        request = self._mock_request_body_request()
        request['grantee'] = ''
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
        self.assertEqual('Incorrect request: share id', cm.exception.log_message)

    def test_validate_get_shares_request(self):
        request = HTTPServerRequest()
        request.query_arguments = {'filter_duplicates': [b'true']}
        RequestValidator.validate_get_shares_request(request)

    def test_validate_get_shares_request_fails(self):
        request = HTTPServerRequest()
        request.query_arguments = {'filter_duplicates': [b'fail']}
        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_get_shares_request(request)
        self.assertEqual('Incorrect request: filter_duplicates', cm.exception.log_message)

    def test_validate_get_received_shares_request(self):
        request = HTTPServerRequest()
        request.query_arguments = {'state': State.PENDING}
        RequestValidator.validate_get_received_shares_request(request)

    def test_validate_get_received_shares_request_fails(self):
        request = HTTPServerRequest()
        request.query_arguments = {'state': 'fail'}
        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_get_received_shares_request(request)
        self.assertEqual('Incorrect request: state', cm.exception.log_message)

    def test_validate_get_user_claim_request(self):
        request = HTTPServerRequest()
        request.query_arguments = {'claim': 'claim', 'value': 'value'}
        RequestValidator.validate_get_user_claim_request(request)

    def test_validate_get_user_claim_request_fails(self):
        request = HTTPServerRequest()
        request.query_arguments = {'claim': 'claim'}
        with self.assertRaises(HTTPError) as cm:
            RequestValidator.validate_get_user_claim_request(request)
        self.assertEqual('Incorrect request: value', cm.exception.log_message)

    def _mock_request_body_request(self):
        request = {}
        request['endpoint'] = '/'
        request['file_path'] = '/path'
        request['grantee'] = 'grantee'
        request['idp'] = 'idp'
        request['role'] = Role.VIEWER
        request['grantee_type'] = Grantee.USER
        return request
