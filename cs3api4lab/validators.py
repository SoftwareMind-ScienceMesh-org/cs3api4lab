import tornado.web as web
from cs3api4lab.common.strings import Role, Grantee, State
from http import HTTPStatus as code


class RequestValidator:

    @staticmethod
    def validate_post_share_request(request):
        RequestValidator.validate_endpoint(request)
        RequestValidator.validate_file_path(request)
        RequestValidator.validate_grantee(request)
        RequestValidator.validate_idp(request)
        RequestValidator.validate_role(request)
        RequestValidator.validate_grantee_type(request)


    @staticmethod
    def validate_put_share_request(request):
        RequestValidator.validate_received_share_id(request)
        RequestValidator.validate_role(request)

    @staticmethod
    def validate_delete_share_request(request):
        RequestValidator.validate_share_id(request)

    @staticmethod
    def validate_get_shares_request(request):
        args = request.get_query_arguments()
        keys = args.keys()
        if 'filter_duplicates' in keys:
            if args['filter_duplicates'] not in ['true', 'false']:
                RequestValidator.return_bad_request('filter_duplicates')

    @staticmethod
    def validate_get_received_shares_request(request):
        args = request.get_query_arguments()
        keys = args.keys()
        if 'state' in keys:
            RequestValidator.validate_share_state(args['state'])

    @staticmethod
    def validate_put_received_share_request(request):
        RequestValidator.validate_received_share_id(request)
        RequestValidator.validate_received_share_state(request)

    @staticmethod
    def validate_get_shares_for_file_request(request):
        if 'file_path' not in request.get_query_arguments().keys():
            RequestValidator.return_bad_request('file_path')
        RequestValidator.validate_file_path(request['file_path'])

    @staticmethod
    def validate_get_user_info_request(request):
        args = request.get_query_arguments()
        keys = args.keys()
        if 'idp' not in keys or not args['idp']:
            RequestValidator.return_bad_request('idp')
        if 'opaque_id' not in keys or not args['opaque_id']:
            RequestValidator.return_bad_request('opaque_id')

    @staticmethod
    def validate_get_user_claim_request(request):
        args = request.get_query_arguments()
        keys = args.keys()
        if 'claim' not in keys or not args['claim']:
            RequestValidator.return_bad_request('claim')
        if 'value' not in keys or not args['value']:
            RequestValidator.return_bad_request('value')

    @staticmethod
    def validate_role(request):
        if 'role' not in request.keys() or request['role'] not in [r.value for r in Role]:
            RequestValidator.return_bad_request('role')

    @staticmethod
    def validate_grantee_type(request):
        if 'grantee_type' not in request.keys() or request['grantee_type'] not in [g.value for g in Grantee]:
            RequestValidator.return_bad_request('grantee_type')

    @staticmethod
    def validate_grantee(request):
        return 'grantee' in request.keys() and request['grantee'] != "" and request['grantee'] is not None

    @staticmethod
    def validate_file_path(request):
        return request['file_path'] and request['file_path'] is not None

    @staticmethod
    def validate_endpoint(request):
        if 'endpoint' not in request.keys() or request['endpoint'] is None:
            RequestValidator.return_bad_request('endpoint')

    @staticmethod
    def validate_idp(request):
        if 'idp' not in request.keys() or not request['idp']:
            RequestValidator.return_bad_request('idp')

    @staticmethod
    def validate_share_state(state):
        if state not in [s.value for s in State]:
            RequestValidator.return_bad_request('state')

    @staticmethod
    def validate_received_share_state(request):
        if 'state' not in request.keys() or request['state'] not in [s.value for s in State]:
            RequestValidator.return_bad_request('state')

    @staticmethod
    def validate_share_id(request):
        args = request.get_query_arguments()
        keys = args.keys()
        if 'share_id' not in keys or not args['share_id']:
            RequestValidator.return_bad_request('share id')

    @staticmethod
    def validate_received_share_id(request):
        if 'share_id' not in request.keys() or not request['share_id']:
            RequestValidator.return_bad_request('share id')

    @staticmethod
    def return_bad_request(value):
        raise web.HTTPError(code.BAD_REQUEST, "Incorrect request: %s" % value)
    