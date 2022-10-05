import json
import time
import datetime
import grpc
import urllib.parse

import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.rpc.v1beta1.code_pb2 as cs3code


class LockManager:
    user = None
    lock_name = 'cs3apis4lab_lock'

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)

        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)

        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.user_api = Cs3UserApi(log)
        self.storage_api = StorageApi(log)
        self.locks_expiration_time = self.config.locks_expiration_time

    def generate_lock_entry(self):
        user = self._get_current_user()
        return urllib.parse.quote(json.dumps({
            "username": user.username,
            "idp": user.id.idp,
            "opaque_id": user.id.opaque_id,
            "updated": time.time(),
            "created": time.time()
        }))

    def _lock_file(self, stat):
        self.storage_api.set_metadata(self.lock_name, self.generate_lock_entry(), stat)

    def is_lock_mine(self, lock):
        user = self._get_current_user()
        if lock:
            return lock['username'] == user.username and lock['idp'] == user.id.idp and lock[
                'opaque_id'] == user.id.opaque_id
        return False

    def is_lock_expired(self, lock):
        if not lock:
            return True
        return time.time() - lock['updated'] > datetime.timedelta(seconds=self.locks_expiration_time).total_seconds()

    def resolve_file_path(self, stat):
        lock = self._get_lock(stat)

        is_locked = True if lock else False
        is_mine = self.is_lock_mine(lock)

        file_path = stat['file_path']
        if is_locked and not is_mine and not self.is_lock_expired(lock):
            file_name = file_path.split('/')[-1]
            file_dir = '/'.join(file_path.split('/')[0:-1])
            return self._resolve_directory(file_dir, '/') + self._get_conflict_filename(file_name)

        return file_path

    def _resolve_directory(self, dir_path,
                           endpoint):  # right now its possible to write in somone else's directory without it being shared
        stat = self.storage_api.stat(dir_path, endpoint)
        if stat.status.code == cs3code.CODE_OK:
            return dir_path
        else:
            return self.config.mount_dir + '/'

    def _get_conflict_filename(self, file_name):
        file_extension = file_name.split('.')[-1]
        name = '.'.join(file_name.split('.')[0:-1])
        return name + '-' + self._get_current_user().username + '.' + datetime.datetime.now().strftime(
            "%Y-%m-%d_%H_%M_%S") + '-conflict.' + file_extension

    def handle_locks(self, stat):
        lock = self._get_lock(stat)

        if not lock:
            self._lock_file(stat)
            return
        else:
            if self.is_lock_mine(lock):
                self._lock_file(stat)
                return
            if self.is_lock_expired(lock):
                self._lock_file(stat)
                return
        raise IOError("File locked")

    def _get_current_user(self):
        if self.user is None:
            self.user = self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                            metadata=[('x-access-token', self.auth.authenticate())])
        return self.user.user

    def _get_lock(self, stat):
        if not stat['arbitrary_metadata']:
            return None

        if not stat['arbitrary_metadata']['metadata'].get(self.lock_name):
            return None

        lock = stat['arbitrary_metadata']['metadata'].get(self.lock_name)
        return json.loads(urllib.parse.unquote(lock))
