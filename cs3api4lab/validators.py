import tornado.web as web
from cs3api4lab.common.strings import Role, Grantee, State
from http import HTTPStatus as code


class RequestValidator:

    @staticmethod
    def validate_body_arg(arg, request):
        if arg not in request.keys() or not request[arg]:
            RequestValidator.return_bad_request(arg)

    @staticmethod
    def validate_body_enum_arg(arg, request, enums):
        if arg not in request.keys() or request[arg] not in enums:
            RequestValidator.return_bad_request(arg)

    @staticmethod
    def validate_query_arg(arg):
        if not arg:
            RequestValidator.return_bad_request(arg)

    @staticmethod
    def validate_post_share_request(request):
        RequestValidator.validate_body_arg('endpoint', request)
        RequestValidator.validate_body_arg('file_path', request)
        RequestValidator.validate_body_arg('grantee', request)
        RequestValidator.validate_body_arg('idp', request)
        RequestValidator.validate_body_enum_arg('role', request, Role.roles())
        RequestValidator.validate_body_enum_arg('grantee_type', request, Grantee.grantee_types())

    @staticmethod
    def validate_put_share_request(request):
        RequestValidator.validate_body_arg('share_id', request)
        RequestValidator.validate_body_enum_arg('role', request, Role.roles())

    @staticmethod
    def validate_put_received_share_request(request):
        RequestValidator.validate_body_arg('share_id', request)
        RequestValidator.validate_body_enum_arg('state', request, State.states())

    @staticmethod
    def validate_share_status(state):
        if state not in State.states():
            RequestValidator.return_bad_request('state')

    @staticmethod
    def validate_received_share_state(request):
        if 'state' not in request.keys() or request['state'] not in State.states():
            RequestValidator.return_bad_request('state')

    @staticmethod
    def validate_share_id(request):
        args = request.query_arguments
        keys = args.keys()
        if 'share_id' not in keys or not args['share_id']:
            RequestValidator.return_bad_request('share id')

    @staticmethod
    def return_bad_request(value):
        raise web.HTTPError(code.BAD_REQUEST, "Incorrect request: %s" % value)
    