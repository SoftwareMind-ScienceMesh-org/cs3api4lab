import urllib.parse

import grpc
import requests
import time

import cs3.storage.provider.v1beta1.resources_pb2 as storage_provider
import cs3.types.v1beta1.types_pb2 as types
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
import cs3.rpc.v1beta1.code_pb2 as cs3code
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import webdav3.client as webdav

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager

from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_base import Cs3Base

class StorageApi(Cs3Base):
    def __init__(self, log):
        super().__init__(log)
        self.config = Cs3ConfigManager.get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        return

    def logStandardized(self, msg, file_path, time_start):
        self.log.debug('msg="%s" filepath="%s" elapsedTimems="%.1f"' % (msg, file_path, (time.time() - time_start) * 1000))

    def get_unified_file_ref(self, file_path, endpoint):
        stat = self.stat(file_path, endpoint)
        if stat.status.code != cs3code.CODE_OK:
            return None
        else:
            stat_unified = self._stat_internal(ref=storage_provider.Reference(
                resource_id=storage_provider.ResourceId(storage_id=stat.info.id.storage_id,
                                                        opaque_id=stat.info.id.opaque_id)))
            return storage_provider.Reference(path=stat_unified.info.path)

    def stat(self, file_path, endpoint='/'):
        ref = FileUtils.get_reference(file_path, endpoint)
        return self._stat_internal(ref)

    def _stat_internal(self, ref):
        return self.cs3_api.Stat(request=cs3sp.StatRequest(ref=ref, arbitrary_metadata_keys='*'),
                                 metadata=[('x-access-token', self.auth.authenticate())])

    def set_metadata(self, key, data, stat):
        opaque_id = urllib.parse.unquote(stat['inode']['opaque_id'])
        storage_id = urllib.parse.unquote(stat['inode']['storage_id'])
        reference = FileUtils.get_reference(opaque_id, storage_id)
        arbitrary_metadata = storage_provider.ArbitraryMetadata()
        arbitrary_metadata.metadata[key] = data

        set_metadata_response = self.cs3_api.SetArbitraryMetadata(
            request=cs3sp.SetArbitraryMetadataRequest(
                ref=reference,
                arbitrary_metadata=arbitrary_metadata),
            metadata=self._get_token())

        if set_metadata_response.status.code != cs3code.CODE_OK:
            self.log.error('msg="Unable to set metadata" file_path="%s" reason="%s"' % \
                           (file_path, set_metadata_response.status.message))
            raise Exception('Unable to set metadata for: ' + stat['filepath'] + ' ' + str(set_metadata_response.status))

    def get_metadata(self, file_path, endpoint):
        ref = self.get_unified_file_ref(file_path, endpoint)
        if ref:
            stat = self._stat_internal(ref)
            if stat.status.code == cs3code.CODE_OK:
                return stat.info.arbitrary_metadata.metadata
        return None

    def init_file_upload(self, file_path, endpoint, content_size):
        time_start = time.time()
        reference = FileUtils.get_reference(file_path, endpoint)
        meta_data = types.Opaque(
            map={"Upload-Length": types.OpaqueEntry(decoder="plain", value=str.encode(content_size))})

        req = cs3sp.InitiateFileUploadRequest(ref=reference, opaque=meta_data)
        init_file_upload_res = self.cs3_api.InitiateFileUpload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate())])

        if init_file_upload_res.status.code != cs3code.CODE_OK:
            self.log.error('msg="Failed to initiateFileUpload on write" file_path="%s" reason="%s"' % \
                           (file_path, init_file_upload_res.status.message))
            raise IOError(init_file_upload_res.status.message)

        self.logStandardized(f"writefile: InitiateFileUploadRes returned protocols={init_file_upload_res.protocols}", file_path, time_start)

        return init_file_upload_res

    def upload_content(self, file_path, content, content_size, init_file_upload_response):
        protocol = [p for p in init_file_upload_response.protocols if p.protocol == "simple"][0]
        if self.config.tus_enabled:
            headers = {
                'Tus-Resumable': '1.0.0',
                'File-Path': file_path,
                'File-Size': content_size,
                'x-access-token': self.auth.authenticate(),
                'X-Reva-Transfer': protocol.token
            }
        else:
            headers = {
                'x-access-token': self.auth.authenticate(),
                'Upload-Length': content_size,
                'X-Reva-Transfer': protocol.token
            }
        put_res = requests.put(url=protocol.upload_endpoint, data=content, headers=headers)

        return put_res

    def init_file_download(self, file_path, endpoint):
        time_start = time.time()
        reference = FileUtils.get_reference(file_path, endpoint)
        req = cs3sp.InitiateFileDownloadRequest(ref=reference)

        init_file_download_response = self.cs3_api.InitiateFileDownload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate())])

        if init_file_download_response.status.code == cs3code.CODE_NOT_FOUND:
            self.log.error('msg="File not found on read" filepath="%s" reason="%s"' % file_path, init_file_download_response.status.message)
            raise IOError('No such file or directory')

        elif init_file_download_response.status.code != cs3code.CODE_OK:
            self.log.error('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % file_path,
                           init_file_download_response.status.message)
            raise IOError(init_file_download_response.status.message)

        self.logStandardized(f"readfile: InitiateFileDownloadRes returned protocols={init_file_download_response.protocols}",
                             file_path, time_start)

        return init_file_download_response

    def download_content(self, init_file_download):
        protocol = [p for p in init_file_download.protocols if p.protocol == "simple"][0]
        # if file is shared via OCM the request needs to go through webdav
        if protocol.opaque and init_file_download.protocols[0].opaque.map['webdav-file-path'].value:
            download_url = protocol.download_endpoint + str(protocol.opaque.map['webdav-file-path'].value, 'utf-8')[1:]
            file_get = webdav.Client({}).session.request(
                method='GET',
                url=download_url,
                headers={
                    'X-Access-Token': str(protocol.opaque.map['webdav-token'].value, 'utf-8')}
            )
        else:
            headers = {
                'x-access-token': self.auth.authenticate(),
                'X-Reva-Transfer': protocol.token  # needed if the downloads pass through the data gateway in reva
            }
            file_get = requests.get(url=protocol.download_endpoint, headers=headers)
        return file_get

    def _get_token(self):
        return [('x-access-token', self.auth.authenticate())]
