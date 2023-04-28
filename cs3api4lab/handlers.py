import json

from jupyter_server.base.handlers import APIHandler
from tornado import gen, web
from grpc._channel import _InactiveRpcError
from cs3api4lab.exception.exceptions import *
from cs3api4lab.api.share_api_facade import ShareAPIFacade
from cs3api4lab.api.cs3_public_share_api import Cs3PublicShareApi
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from jupyter_server.utils import url_path_join
from cs3api4lab.utils.asyncify import get_or_create_eventloop
from cs3api4lab.utils.custom_logger import CustomLogger
from jupyter_server.base.handlers import log

class LoggingHandler(APIHandler):
    _logger = None
    @property
    def log(self):
        if self._logger is None:
            self._logger = CustomLogger(log())
            return self._logger
        else:
            return self._logger

class ShareHandler(LoggingHandler):
    _share_api = None
    _endpoint = "/api/cs3/shares"

    @property
    def share_api(self):
        if self._share_api is None:
            self._share_api = ShareAPIFacade(self.log)
            return self._share_api
        else:
            return self._share_api

    @web.authenticated
    @gen.coroutine
    def post(self):
        request = self.get_json_body()
        self.share_api.log.info(request['file_path'], http_method="POST", api_endpoint=self._endpoint)
        try:
            yield RequestHandler.async_handle_request(self,
                                                      self.share_api.create,
                                                      201,
                                                      request['endpoint'],
                                                      request['file_path'],
                                                      request['grantee'],
                                                      request['idp'],
                                                      request['role'],
                                                      request['grantee_type'])
        except KeyError as err:
            RequestHandler.handle_error(self, ParamError(err))

    @web.authenticated
    @gen.coroutine
    def delete(self):
        share_id = self.get_query_argument('share_id')
        self.share_api.log.info(share_id, http_method="DELETE", api_endpoint=f"{self._endpoint}/{share_id}")
        yield RequestHandler.async_handle_request(self, self.share_api.remove, 204, share_id)

    @web.authenticated
    @gen.coroutine
    def put(self):
        params = self.get_json_body()
        self.share_api.log.info("", http_method="PUT", api_endpoint=self._endpoint)
        try:
            yield RequestHandler.async_handle_request(self,
                                          self.share_api.update_share,
                                          204,
                                          params)
        except KeyError as err:
            RequestHandler.handle_error(self, ParamError(err))


class ListSharesHandler(LoggingHandler):
    _share_api = None
    _endpoint = "/api/cs3/shares/list"

    @property
    def share_api(self):
        if self._share_api is None:
            self._share_api = ShareAPIFacade(self.log)
            return self._share_api
        else:
            return self._share_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        self.share_api.log.info("", http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.share_api.list_shares, 200,
                                                  self.get_query_argument('filter_duplicates', default='false') in ['true', '1'])


class ListReceivedSharesHandler(LoggingHandler):
    _share_api = None
    _endpoint = "/api/cs3/shares/received"

    @property
    def share_api(self):
        if self._share_api is None:
            self._share_api = ShareAPIFacade(self.log)
            return self._share_api
        else:
            return self._share_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        status = self.get_query_argument('status', default=None)
        self.share_api.log.info(f"status: {str(status)}", http_method="GET", api_endpoint=self._endpoint)

        yield RequestHandler.async_handle_request(self, self.share_api.list_received, 200, status)

    @web.authenticated
    @gen.coroutine
    def put(self):
        body = self.get_json_body()
        self.share_api.log.info(f"", http_method="PUT", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.share_api.update_received, 200, body["share_id"], body["state"])


class ListSharesForFile(LoggingHandler):
    _share_api = None
    _endpoint = "/api/cs3/shares/file"

    @property
    def share_api(self):
        if self._share_api is None:
            self._share_api = ShareAPIFacade(self.log)
            return self._share_api
        else:
            return self._share_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        file_path = self.get_query_argument('file_path')
        self.share_api.log.info(file_path, http_method="GET", api_endpoint=f"{self._endpoint}/{file_path}")
        yield RequestHandler.async_handle_request(self, self.share_api.list_grantees_for_file, 200, file_path)

class HomeDirHandler(LoggingHandler):
    _file_api = None
    _endpoint = "/api/cs3/user/home_dir"

    @property
    def file_api(self):
        if self._file_api is None:
            self._file_api = Cs3FileApi(self.log)
            return self._file_api
        else:
            return self._file_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        self.file_api.log.info(f"", http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.file_api.get_home_dir, 200)

class PublicSharesHandler(LoggingHandler):
    _public_share_api = None
    _endpoint = "/api/cs3/public/shares"

    @property
    def public_share_api(self):
        if self._public_share_api is None:
            self._public_share_api = Cs3PublicShareApi(self.log)
            return self._public_share_api
        else:
            return self._public_share_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        token = self.get_query_argument('token', default=None)
        opaque_id = self.get_query_argument('opaque_id')
        self.public_share_api.log.info(opaque_id, http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.public_share_api.get_public_share, 200, opaque_id, token)

    @web.authenticated
    @gen.coroutine
    def post(self):
        request = self.get_json_body()
        self.public_share_api.log.info(str(request), http_method="POST", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self,
                                                  self.public_share_api.create_public_share,
                                                  201,
                                                  request['endpoint'],
                                                  request['file_path'],
                                                  request['password'],
                                                  request['exp_date'],
                                                  request['permissions'])

    @web.authenticated
    @gen.coroutine
    def delete(self):
        opaque_id = self.get_query_argument('opaque_id')
        self.public_share_api.log.info(opaque_id, http_method="DELETE", api_endpoint=f"{self._endpoint}/{opaque_id}")
        yield RequestHandler.async_handle_request(self, self.public_share_api.remove_public_share, 204, opaque_id)

    @web.authenticated
    @gen.coroutine
    def put(self):
        request = self.get_json_body()
        self.public_share_api.log.info(str(request), http_method="PUT", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.public_share_api.update_public_share,
                                                  204,
                                                  request['opaque_id'],
                                                  request['token'],
                                                  request['field_type'],
                                                  request['field_value'])


class GetPublicShareByTokenHandler(LoggingHandler):
    _public_share_api = None
    _endpoint = "/api/cs3/public/share"

    @property
    def public_share_api(self):
        if self._public_share_api is None:
            self._public_share_api = Cs3PublicShareApi(self.log)
            return self._public_share_api
        else:
            return self._public_share_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        self.public_share_api.log.info("", http_method="GET", api_endpoint=self._endpoint)
        token = self.get_query_argument('token')
        password = self.get_query_argument('password', default='')
        yield RequestHandler.async_handle_request(self, self.public_share_api.get_public_share_by_token, 200, token, password)


class ListPublicSharesHandler(LoggingHandler):
    _public_share_api = None
    _endpoint = "/api/cs3/public/shares/list"

    @property
    def public_share_api(self):
        if self._public_share_api is None:
            self._public_share_api = Cs3PublicShareApi(self.log)
            return self._public_share_api
        else:
            return self._public_share_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        self.public_share_api.log.info("", http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.public_share_api.list_public_shares, 200)


class UserInfoHandler(LoggingHandler):
    _user_api = None
    _endpoint = "/api/cs3/user"

    @property
    def user_api(self):
        if self._user_api is None:
            self._user_api = Cs3UserApi(self.log)
            return self._user_api
        else:
            return self._user_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        idp = self.get_query_argument('idp')
        opaque_id = self.get_query_argument('opaque_id')
        self.user_api.log.info(f"idp: {idp}, opaque_id: {opaque_id}", http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.user_api.get_user, 200, idp, opaque_id)

class UserInfoClaimHandler(LoggingHandler):
    _user_api = None
    _endpoint = "/api/cs3/user/claim"

    @property
    def user_api(self):
        if self._user_api is None:
            self._user_api = Cs3UserApi(self.log)
            return self._user_api
        else:
            return self._user_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        claim = self.get_query_argument('claim')
        value = self.get_query_argument('value')
        self.user_api.log.info(f"claim: {claim}, value: {value}", http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.user_api.get_user_info_by_claim, 200, claim, value)

class UserQueryHandler(LoggingHandler):
    _user_api = None
    _endpoint = "/api/cs3/user/query"

    @property
    def user_api(self):
        if self._user_api is None:
            self._user_api = Cs3UserApi(self.log)
            return self._user_api
        else:
            return self._user_api

    @web.authenticated
    @gen.coroutine
    def get(self):
        query = self.get_query_argument('query')
        self.user_api.log.info(f"query: {query}", http_method="GET", api_endpoint=self._endpoint)
        yield RequestHandler.async_handle_request(self, self.user_api.find_users_by_query, 200, query)

def setup_handlers(web_app, url_path):
    handlers = [
        (r"/api/cs3/shares", ShareHandler),
        (r"/api/cs3/shares/list", ListSharesHandler),
        (r"/api/cs3/shares/received", ListReceivedSharesHandler),
        (r"/api/cs3/shares/file", ListSharesForFile),
        (r"/api/cs3/public/shares", PublicSharesHandler),
        (r"/api/cs3/public/shares/list", ListPublicSharesHandler),
        (r"/api/cs3/public/share", GetPublicShareByTokenHandler),
        (r"/api/cs3/user", UserInfoHandler),
        (r"/api/cs3/user/claim", UserInfoClaimHandler),
        (r"/api/cs3/user/query", UserQueryHandler),
        (r"/api/cs3/user/home_dir", HomeDirHandler)
    ]

    for handler in handlers:
        pattern = url_path_join(web_app.settings['base_url'], handler[0])
        new_handler = tuple([pattern] + list(handler[1:]))
        web_app.add_handlers('.*$', [new_handler])

class RequestHandler(LoggingHandler):

    @staticmethod
    def handle_request(self, api_function, success_code, *args):
        try:
            response = api_function(*args)
        except Exception as err:
            self.log.error(err)
            RequestHandler.handle_error(self, err)
        else:
            RequestHandler.handle_response(self, response, success_code)

    @staticmethod
    async def async_handle_request(self, api_function, success_code, *args):
        try:
            loop = get_or_create_eventloop()
            response = await loop.run_in_executor(None, api_function, *args)
        except Exception as err:
            self.log.error(err)
            RequestHandler.handle_error(self, err)
        else:
            RequestHandler.handle_response(self, response, success_code)

    @staticmethod
    def handle_error(self, err):
        status = RequestHandler.get_response_code(err)
        response = {
            'error_message': '%s: %s' % (str(status), err.message if hasattr(err, 'message') else str(err))
        }
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.finish(json.dumps(response))

    @staticmethod
    def handle_response(self, response, success_code):
        self.set_header('Content-Type', 'application/json')
        self.set_status(success_code)
        if response is None:
            self.finish()
        else:
            self.finish(json.dumps(response))

    @staticmethod
    def get_response_code(err):
        if isinstance(err, ShareAlreadyExistsError):
            return 409
        if isinstance(err, (ShareNotFoundError, LockNotFoundError)):
            return 404
        if isinstance(err, (InvalidTypeError, KeyError, FileNotFoundError, ParamError)):
            return 400
        if isinstance(err, OCMDisabledError):
            return 501
        if isinstance(err, _InactiveRpcError):
            return 503
        return 500
