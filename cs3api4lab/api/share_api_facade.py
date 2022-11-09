import urllib.parse

import cs3.ocm.provider.v1beta1.provider_api_pb2_grpc as ocm_provider_api_grpc
import cs3.storage.provider.v1beta1.resources_pb2 as Resources

from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.common.strings import *
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.api.cs3_user_api import Cs3UserApi

from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi

from cs3api4lab.utils.share_utils import ShareUtils
from cs3api4lab.utils.model_utils import ModelUtils
from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.exception.exceptions import OCMDisabledError

from google.protobuf import json_format


class ShareAPIFacade:
    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        self.file_api = Cs3FileApi(log)

        channel = ChannelConnector().get_channel()
        self.provider_api = ocm_provider_api_grpc.ProviderAPIStub(channel)
        self.user_api = Cs3UserApi(log)

        self.share_api = Cs3ShareApi(log)
        self.ocm_share_api = Cs3OcmShareApi(log)

        self.storage_api = StorageApi(log)
        return

    def create(self, endpoint, file_path, opaque_id, idp, role=Role.EDITOR, grantee_type=Grantee.USER, reshare=True):
        """Creates a share or creates an OCM share if the user is not found in local domain"""
        file_path = FileUtils.remove_drives_names(file_path)
        if self._is_ocm_user(opaque_id, idp):
            if self.config.enable_ocm:
                return self.ocm_share_api.create(opaque_id, idp, idp, endpoint, file_path, grantee_type, role, reshare)
            else:
                raise OCMDisabledError('Cannot create OCM share - OCM functionality is disabled')
        else:
            return self.share_api.create(endpoint, file_path, opaque_id, idp, role, grantee_type)

    def update_share(self, params):
        """Updates a field of a share
            Paramterers:
                :param share_id
                :param role: EDITOR/VIEWER
            Parameters for OCM:
                :param share_id
                :param permissions: EDITOR/VIEWER or
                :param display_name
        """
        if self.is_share(params['share_id']):
            self.share_api.update(params['share_id'], params['role'])
        else:
            if not self.config.enable_ocm:
                raise OCMDisabledError('Cannot update OCM share - OCM functionality is disabled')
            else:
                self.ocm_share_api.update(
                    params['share_id'],
                    'permissions',
                    [params['role'], 'role']
                )

    def update_received(self, share_id, state):
        """Updates share's state
           :param share_id
           :param state: accepted/rejected/pending/invalid
        """
        if self.is_ocm_received_share(share_id):
            if self.config.enable_ocm:
                result = self.ocm_share_api.update_received(share_id, 'state', state)
            else:
                raise OCMDisabledError('Cannot update received OCM share - OCM functionality is disabled')
        else:
            result = json_format.MessageToDict(self.share_api.update_received(share_id, state))

        stat = self.file_api.stat_info(urllib.parse.unquote(result['share']['resourceId']['opaqueId']),
                                       result['share']['resourceId']['storageId'])  # todo remove this and use storage_logic
        return ModelUtils.map_share_to_base_model(result['share'], stat)

    def remove(self, share_id):
        """Removes a share with given opaque_id """

        if self.is_share(share_id):
            self.share_api.remove(share_id)
        else:
            if self.config.enable_ocm:
                return self.ocm_share_api.remove(share_id)
            else:
                raise OCMDisabledError('Cannot remove OCM share - OCM functionality is disabled')

    def list_shares(self, merge=True):
        """
        :return: created shares and OCM shares mapped to Jupyter model
        :param: merge - wether to combine all shares into one consistent list without duplicates
        :rtype: dict
        """
        shares = []
        share_list = self.share_api.list()
        if share_list.shares:
            shares += json_format.MessageToDict(share_list)['shares']
        if self.config.enable_ocm:
            ocm_share_list = self.ocm_share_api.list()
            if ocm_share_list.shares:
                shares += json_format.MessageToDict(ocm_share_list)['shares']
        if merge:
            shares = self._merge_shares(shares)
        return self.map_shares_to_model(shares)

    def _merge_shares(self, share_list):
        # https://github.com/cs3org/reva/issues/3243
        if self.config.dev_env:
            for share in share_list:
                share['resourceId']['opaqueId'] = share['resourceId']['opaqueId'].replace('fileid-/', 'fileid-')
        merged_shares = []
        for share in share_list:
            if not share['resourceId'] in list(map(lambda share: share['resourceId'], merged_shares)):
                merged_shares.append(share)
        return merged_shares

    def list_received(self, status=None):
        """
        :return: received shares and OCM received shares combined and mapped to Jupyter model
        :rtype: dict
        """
        shares_received = []
        share_list = self.share_api.list_received()

        if share_list.shares:
            shares_received += json_format.MessageToDict(share_list)['shares']

        if self.config.enable_ocm:
            ocm_share_list = self.ocm_share_api.list_received()
            if ocm_share_list.shares:
                shares_received += json_format.MessageToDict(ocm_share_list)['shares']

        mapped_shares_received = self.map_shares_to_model(shares_received, True)

        if status and shares_received:
            mapped_shares_received['content'] = list(filter(lambda share: share['state'] == status, mapped_shares_received['content']))

        return mapped_shares_received

    def list_grantees_for_file(self, file_path):
        """
        :param file_path: path to the file
        :return: list of grantees
        """

        file_path = FileUtils.remove_drives_names(file_path)
        file_path = FileUtils.check_and_transform_file_path(file_path)

        all_shares_list = []
        share_list = self.share_api.list(file_path)
        all_shares_list.extend(share_list.shares)

        if self.config.enable_ocm:
            ocm_share_list = self.ocm_share_api.list(file_path)
            all_shares_list.extend(ocm_share_list.shares)

        shares = []
        for share in all_shares_list:
            shares.append(ShareUtils.get_share_info(share))

        return {"file_path": file_path, "shares": shares}

    def _token(self):
        return [('x-access-token', self.auth.authenticate())]

    def _is_ocm_user(self, opaque_id, idp):
        """Checks if user is present in local provider"""
        return not bool(self.user_api.get_user_info(idp, opaque_id))

    def is_share(self, opaque_id):
        try:
            self.share_api.get(opaque_id)
        except Exception:
            return False
        return True

    def is_ocm_share(self, share_id):
        """Checks if share is present on shares list"""
        for share in self.share_api.list().shares:
            if share.id.opaque_id == share_id:
                return False
        return True

    def is_ocm_received_share(self, share_id):
        """Checks if share is present on OCM received shares list"""
        if self.config.enable_ocm:
            try:
                # if OCM is not enabled on IOP side this call will fail
                received_shares = self.ocm_share_api.list_received()
                for share in received_shares.shares:
                    if share_id == share.share.id.opaque_id:
                        return True
            except Exception as e:
                self.log.error("Error checking OCM " + str(e))
        return False

    def map_shares_to_model(self, list_response, received=False):
        respond_model = ModelUtils.create_respond_model()
        for share in list_response:
            if received:
                state = share['state']
                share = share['share']
                share['state'] = state
            try:
                user = self.user_api.get_user_info(share['owner']['idp'], share['owner']['opaqueId'])
                stat = self.file_api.stat_info(urllib.parse.unquote(share['resourceId']['opaqueId']),
                                               share['resourceId']['storageId'])
                # todo remove this and use storage_logic
                # stat = self.storage_logic.stat_info(urllib.parse.unquote(share.resource_id.opaque_id), share.resource_id.storage_id)

                if stat['type'] == Resources.RESOURCE_TYPE_FILE:
                    model = ModelUtils.map_share_to_file_model(share, stat, optional={
                        'owner': user['display_name']
                    })
                else:
                    model = ModelUtils.map_share_to_dir_model(share, stat, optional={
                        'owner': user['display_name']
                    })
                model['writable'] = ShareUtils.map_permissions_to_role(share['permissions']['permissions']) == 'editor'
            except Exception as e:
                self.log.error("Unable to map share " + share['resourceId']['opaqueId'] + ", " + e.__str__())
                continue

            if received:
                model['state'] = ShareUtils.map_state(share['state'])
            respond_model['content'].append(model)

        return respond_model
