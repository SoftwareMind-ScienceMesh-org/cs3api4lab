import random
import string

from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.share_api_facade import ShareAPIFacade
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.tests.extensions import ExtCs3FileApi, ExtCs3ShareApi, ExtCs3OcmShareApi, ExtStorageApi, \
    ExtCs3ShareApiFacade, Cs3ConfigManager, ExtAuthenticator
from traitlets.config import LoggingConfigurable
import cs3.rpc.v1beta1.code_pb2 as cs3code
from collections import namedtuple


class ShareTestBase: 
    storage_id = '123e4567-e89b-12d3-a456-426655440000'
    receiver_role = 'editor'
    receiver_grantee_type = 'user'

    def setUp(self): 
        self.log = LoggingConfigurable().log
        self.config = Cs3ConfigManager().get_config()
        self.file_api = Cs3FileApi(self.log)
        self.share_api = Cs3ShareApi(self.log)
        self.ocm_api = Cs3OcmShareApi(self.log)
        self.uni_api = ShareAPIFacade(self.log)
        self.auth = ExtAuthenticator(self.config, self.log)
        self.storage_api = StorageApi(self.log)

        marie_ext_config = {
            "reva_host": "127.0.0.1: 29000",
            "auth_token_validity": 3600,
            "endpoint": "/",
            "mount_dir": "/home",
            "home_dir": "/",
            "chunk_size": 4194304,
            "secure_channel": False,
            "client_cert": "",
            "client_key": "",
            "ca_cert": "",
            "authenticator_class": "cs3api4lab.auth.RevaPassword",
            "client_id": "marie",
            "client_secret": "radioactivity",
	        "locks_expiration_time": 10,
	        "tus_enabled": True,
  	        "enable_ocm": False
            }
        marie_ext_config = namedtuple('MarieConfig', marie_ext_config)(**marie_ext_config)

        richard_local_config = {
            "reva_host": "127.0.0.1: 19000",
            "auth_token_validity": 3600,
            "endpoint": "/",
            "mount_dir": "/home",
            "home_dir": "/",
            "chunk_size": 4194304,
            "secure_channel": False,
            "client_cert": "",
            "client_key": "",
            "ca_cert": "",
            "authenticator_class": "cs3api4lab.auth.RevaPassword",
            "client_id": "richard",
            "client_secret": "superfluidity",
	        "locks_expiration_time": 10,
	        "tus_enabled": True,
  	        "enable_ocm": False
        }
        richard_local_config = namedtuple('richardConfig', richard_local_config)(**richard_local_config)

        self.marie_uni_api = ExtCs3ShareApiFacade(self.log, marie_ext_config)
        self.marie_file_api = ExtCs3FileApi(self.log, marie_ext_config)
        self.marie_share_api = ExtCs3ShareApi(self.log, marie_ext_config)
        self.marie_ocm_share_api = ExtCs3OcmShareApi(self.log, marie_ext_config)
        self.marie_storage_api = ExtStorageApi(self.log, marie_ext_config)

        self.richard_uni_api = ExtCs3ShareApiFacade(self.log, richard_local_config)
        self.richard_file_api = ExtCs3FileApi(self.log, richard_local_config)
        self.richard_share_api = ExtCs3ShareApi(self.log, richard_local_config)
        self.richard_ocm_share_api = ExtCs3OcmShareApi(self.log, richard_local_config)
        self.richard_storage_api = ExtStorageApi(self.log, richard_local_config)

        self.content = "op98^*^8asdasMnb23Bo!ml;)Wk"

    def read_file_content(self, file_api, file_path): 
        content = ''
        for chunk in file_api.read_file(file_path): 
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            content += chunk.decode('utf-8')
        return content

    def create_ocm_share(self, user, ocm_receiver_id, ocm_receiver_idp, file_path): 
        self.create_test_file(user, file_path)
        if user == 'einstein': 
            return self.ocm_api.create(ocm_receiver_id,
                                       ocm_receiver_idp,
                                       ocm_receiver_idp,
                                       self.storage_id, file_path)
        elif user == 'marie':
            return self.marie_ocm_share_api.create(ocm_receiver_id,
                                                   ocm_receiver_idp,
                                                   ocm_receiver_idp,
                                                   self.storage_id, file_path)
        elif user == 'richard':
            return self.richard_ocm_share_api.create(ocm_receiver_id,
                                                     ocm_receiver_idp,
                                                     ocm_receiver_idp,
                                                     self.storage_id, file_path)
        else:
            raise Exception("Invalid user")

    def create_share(self, user, receiver_id, receiver_idp, file_path): 
        self.create_test_file(user, file_path)
        if user == 'einstein': 
            return self.share_api.create(self.storage_id,
                                         file_path,
                                         receiver_id,
                                         receiver_idp,
                                         self.receiver_role,
                                         self.receiver_grantee_type)
        elif user == 'marie':
            return self.marie_share_api.create(self.storage_id,
                                               file_path,
                                               receiver_id,
                                               receiver_idp,
                                               self.receiver_role,
                                               self.receiver_grantee_type)
        elif user == 'richard':
            return self.richard_share_api.create(self.storage_id,
                                                 file_path,
                                                 receiver_id,
                                                 receiver_idp,
                                                 self.receiver_role,
                                                 self.receiver_grantee_type)
        else:
            raise Exception("Invalid user")

    def create_container_share(self, user, receiver_id, receiver_idp, container_path): 
        self.create_test_container(user, container_path)
        if user == 'einstein': 
            return self.share_api.create(self.storage_id,
                                         container_path,
                                         receiver_id,
                                         receiver_idp,
                                         self.receiver_role,
                                         self.receiver_grantee_type)
        elif user == 'marie':
            return self.marie_share_api.create(self.storage_id,
                                               container_path,
                                               receiver_id,
                                               receiver_idp,
                                               self.receiver_role,
                                               self.receiver_grantee_type)
        elif user == 'richard':
            return self.richard_share_api.create(self.storage_id,
                                                 container_path,
                                                 receiver_id,
                                                 receiver_idp,
                                                 self.receiver_role,
                                                 self.receiver_grantee_type)
        else:
            raise Exception("Invalid user")

    def clear_locks_on_file(self, file, endpoint='/'): 
        metadata = self.storage_api.get_metadata(file, endpoint)
        for lock in list(metadata.keys()): 
            self.storage_api.set_metadata({lock: "{}"}, file, endpoint)


    def remove_test_share(self, user, share_id): 
        if user == 'einstein': 
            self.share_api.remove(share_id)
        elif user == 'marie':
            self.marie_share_api.remove(share_id)
        elif user == 'richard':
            self.richard_share_api.remove(share_id)
        else:
            raise Exception("Invalid user")

    def remove_test_ocm_share(self, user, share_id): 
        if user == 'einstein': 
            self.ocm_api.remove(share_id)
        elif user == 'marie':
            self.marie_ocm_share_api.remove(share_id)
        elif user == 'richard':
            self.richard_ocm_share_api.remove(share_id)
        else:
            raise Exception("Invalid user")

    def create_test_file(self, user, file_path): 
        if user == 'einstein': 
            self.file_api.write_file(file_path,
                                     self.content,
                                     self.storage_id)
        elif user == 'marie':
            self.marie_file_api.write_file(file_path,
                                           self.content,
                                           self.storage_id)
        elif user == 'richard':
            self.richard_file_api.write_file(file_path,
                                             self.content,
                                             self.storage_id)
        else:
            raise Exception("Invalid user")

    def create_test_container(self, user, container_path): 
        if user == 'einstein': 
            self.file_api.create_directory(container_path)
        elif user == 'marie':
            self.marie_file_api.create_directory(container_path)
        elif user == 'richard':
            self.richard_file_api.create_directory(container_path)
        else:
            raise Exception("Invalid user")

    def remove_test_file(self, user, file_path): 
        if user == 'einstein': 
            self.file_api.remove(file_path, self.storage_id)
        elif user == 'marie':
            self.marie_file_api.remove(file_path, self.storage_id)
        elif user == 'richard':
            self.richard_file_api.remove(file_path, self.storage_id)
        else:
            raise Exception("Invalid user")

    def get_random_suffix(self): 
        return '-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

    def clean_up_file(self, user, file_name): 
        try: 
            self.remove_test_file(user, file_name)
        except Exception as ex: 
            print(str(ex))

    def clean_up_share(self, user, share_id): 
        try: 
            self.remove_test_share(user, share_id)
        except Exception as ex: 
            print(str(ex))

    def remove_share_and_file_by_path(self, user, file_path): 
        if user == 'einstein': 
            share_api = self.share_api
            storage = self.storage_api
        elif user == 'marie':
            share_api = self.marie_share_api
            storage = self.marie_storage_api
        elif user == 'richard':
            share_api = self.richard_share_api
            storage = self.richard_storage_api
        else:
            raise Exception("Incorrect user")

        stat = storage.stat(file_path)
        if stat.status.code == cs3code.CODE_NOT_FOUND or stat.status.code == cs3code.CODE_INTERNAL: 
            self.create_test_file(user, file_path)
        #todo the code above won't be necessary after https: //github.com/cs3org/reva/issues/2847 is fixed

        shares = share_api.list_shares_for_filepath(file_path) #todo this won't work on CERNBOX
        if shares: 
            for share in shares: 
                share_api.remove(share['opaque_id'])

        self.remove_test_file(user, file_path)
