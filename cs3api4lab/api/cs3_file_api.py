"""
cs3_file_api.py

CS3 File API for the JupyterLab Extension

Authors:
"""
import http
import time
import urllib.parse
import grpc
import requests

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.v1beta1.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
from google.protobuf.json_format import MessageToDict

from cs3api4lab.exception.exceptions import ResourceNotFoundError, FileLockedError

from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.locks.factory import LockApiFactory
from cs3api4lab.utils.custom_logger import CustomLogger
from cs3api4lab.api.cs3_base import Cs3Base

class Cs3FileApi(Cs3Base):
    def __init__(self, log):
        super().__init__(log)
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(self.log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.storage_api = StorageApi(self.log)
        self.lock_api = LockApiFactory.create(self.log, self.config)

    def mount_point(self):
        """
        This returns current mount point for the user
        """
        request = cs3sp.GetHomeRequest()
        response = self.cs3_api.GetHome(request)
        return {
            "path": response.path
        }

    def stat_info(self, file_path, endpoint='/'):
        """
        Stat a file and returns (size, mtime) as well as other extended info using the given userid as access token.
        Note that endpoint here means the storage id. Note that fileid can be either a path (which MUST begin with /)
        or an id (which MUST NOT start with a /).
        """
        time_start = time.time()
        stat = self.storage_api.stat(file_path, endpoint)
        if stat.status.code == cs3code.CODE_OK:
            self.log.debug("Invoked stat", file_path=file_path, elapsed_timems=(CustomLogger.get_timems(time_start)))
            return {
                'inode': {'storage_id': stat.info.id.storage_id,
                          'opaque_id': stat.info.id.opaque_id},
                'filepath': stat.info.path,
                'userid': stat.info.owner.opaque_id,
                'size': stat.info.size,
                'mtime': stat.info.mtime.seconds,
                'type': stat.info.type,
                'mime_type': stat.info.mime_type,
                'idp': stat.info.owner.idp,
                'permissions': stat.info.permission_set,
                'arbitrary_metadata': MessageToDict(stat.info.arbitrary_metadata),
            }
        elif stat.status.code == cs3code.CODE_NOT_FOUND:
            self.log.error("Failed stat", file_path=file_path, reason=stat.status.message)
            raise FileNotFoundError(f"{stat.status.message}, file {file_path}")

        else:
            self._handle_error(stat)
        
    def read_file(self, stat, endpoint=None):
        """
        Read a file using the given userid as access token.
        """
        time_start = time.time()
        if stat:
            # additional request until this issue is resolved https://github.com/cs3org/reva/issues/3243
            if self.config.dev_env and "/home/" in stat['filepath']:
                opaque_id = urllib.parse.unquote(stat['inode']['opaque_id'])
                storage_id = urllib.parse.unquote(stat['inode']['storage_id'])
                stat = self.stat_info(opaque_id, storage_id)

            try:
                self.lock_api.set_lock(stat)
                self.log.info("Created lock", file_path=stat['filepath'], elapsed_timems=CustomLogger.get_timems(time_start))
                time_start = time.time()
            except IOError:
                self.log.error("File is locked, opening in read-only mode", file_path=stat['filepath'], reason="file locked")
        else:
            msg = f"{stat.status.code}: {stat.status.message}"
            self.log.error("Error when stating file for read", file_path=stat['filepath'], reason=msg)
            raise IOError('Error when stating file')

        init_file_download = self.storage_api.init_file_download(stat['filepath'], endpoint)
        time_end = time.time()
        self.log.info("Initialized download", file_path=stat['filepath'], elapsed_timems=CustomLogger.get_timems(time_start))
        time_start = time.time()#todo download time
        try:
            file_get = self.storage_api.download_content(init_file_download)
        except requests.exceptions.RequestException as e:
            self.log.error("Exception when downloading file from Reva", file_path=stat['filepath'], reason=e)
            raise IOError(e)

        size = len(file_get.content)
        chunk_size = self.config.chunk_size
        for i in range(0, size, chunk_size):
            yield file_get.content[i:i + self.config.chunk_size]

    def write_file(self, file_path, content, endpoint=None, format=None):
        """
        Write a file using the given userid as access token. The entire content is written
        and any pre-existing file is deleted (or moved to the previous version if supported).
        """
        stat = None
        try:
            stat = self.stat_info(file_path, endpoint)
            if stat:
                # additional request until this issue is resolved https://github.com/cs3org/reva/issues/3243
                if self.config.dev_env and "/home/" in stat['filepath']:
                    opaque_id = urllib.parse.unquote(stat['inode']['opaque_id'])
                    storage_id = urllib.parse.unquote(stat['inode']['storage_id'])
                    stat = self.stat_info(opaque_id, storage_id)

                # file_path = self.lock_manager.resolve_file_path(stat)
        except Exception as e:
            self.log.info("Creating new file", file_path=file_path, reason=e)

        if stat:
            # fixme - this might cause overwriting/locking issues due to unexpected error codes
            self.lock_api.set_lock(stat)

        content_size = FileUtils.calculate_content_size(content, format)
        init_file_upload = self.storage_api.init_file_upload(file_path, endpoint, content_size)
        time_start = time.time()
        try:
            upload_response = self.storage_api.upload_content(file_path, content, content_size, init_file_upload)
        except requests.exceptions.RequestException as e:
            self.log.error("Exception when uploading file to Reva", file_path=file_path, reason=e)
            raise IOError(e)

        if upload_response.status_code != http.HTTPStatus.OK:
            self.log.error("Error uploading file to Reva", file_path=file_path, reason=upload_response.reason)
            raise IOError(upload_response.reason)

        self.log.info("File uploaded", file_path=file_path, elapsed_timems=CustomLogger.get_timems(time_start))

        return file_path

    def remove(self, file_path, endpoint=None):
        """
        Remove a file or container using the given userid as access token.
        """
        time_start = time.time()
        reference = FileUtils.get_reference(file_path, endpoint)
        req = cs3sp.DeleteRequest(ref=reference)
        res = self.cs3_api.Delete(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            self.log.error("File or folder not found on remove", file_path=file_path, reason="not found")
            raise FileNotFoundError('No such file or directory')

        if res.status.code != cs3code.CODE_OK:
            self.log.error("Failed to remove file or folder", file_path=file_path, reason=res)
            raise IOError(res.status.message)

        self.log.debug("Invoked remove", file_path=file_path, elapsed_timems=CustomLogger.get_timems(time_start))

    def read_directory(self, path, endpoint=None):
        """
        Read a directory.
        """
        tstart = time.time()
        reference = FileUtils.get_reference(path, endpoint)
        req = cs3sp.ListContainerRequest(ref=reference)
        res = self.cs3_api.ListContainer(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            raise ResourceNotFoundError(f"directory {path} not found")

        if res.status.code != cs3code.CODE_OK:
            self.log.error("Failed to read container", file_path=path, reason=res.status.message)
            raise IOError(res.status.message)

        self.log.debug("Invoked read container", file_path=path, elapsed_timems=CustomLogger.get_timems(tstart))

        out = []
        for info in res.infos:
            if self.config.mount_dir != '/' and len(self.config.mount_dir) > 0 and info.path.startswith(self.config.mount_dir):
                info.path = info.path.rsplit(self.config.mount_dir)[-1]
            out.append(info)
        return out

    def move(self, source_path, destination_path, endpoint=None):
        """
        Move a file or container.
        """
        tstart = time.time()
        src_reference = FileUtils.get_reference(source_path, endpoint)
        dest_reference = FileUtils.get_reference(destination_path, endpoint)

        # fixme - this might cause overwriting issues due to unexpected error codes
        stat = self.storage_api.stat(destination_path, endpoint)

        if stat.status.code == cs3code.CODE_OK:
            self.log.error(f"Failed to move source={source_path}, destination={destination_path}", file_path=source_path,
                           reason="file already exists")
            raise IOError("file already exists")

        req = cs3sp.MoveRequest(source=src_reference, destination=dest_reference)
        res = self.cs3_api.Move(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            self.log.error(f"source not found", file_path=source_path, reason="not found")
            raise ResourceNotFoundError(f"source {source_path} not found")

        if res.status.code != cs3code.CODE_OK:
            self.log.error(f"Failed to move source: {source_path} to destination: {destination_path}", file_path=source_path,
                           reason=res.status.message)
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug("Invoked move", file_path=source_path, elapsed_timems=CustomLogger.get_timems(tstart))

    def create_directory(self, path, endpoint=None):
        """
        Create a directory.
        """
        tstart = time.time()
        reference = FileUtils.get_reference(path, endpoint)
        req = cs3sp.CreateContainerRequest(ref=reference)
        res = self.cs3_api.CreateContainer(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code != cs3code.CODE_OK:
            self.log.error("Failed to create container", file_path=path, reason=res.status.message)
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug("Invoked create container", file_path=path, elapsed_timems=CustomLogger.get_timems(tstart))

    def get_home_dir(self):
        return self.config.home_dir if self.config.home_dir else ""

    def _handle_error(self, response):
        self.log.error("Incorrect server response", file_path="", reason=str(response.status))
        raise Exception(f"Incorrect server response: {response.status.message}")
