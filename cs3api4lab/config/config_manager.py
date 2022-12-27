import os
from jupyter_core.paths import jupyter_config_path
from jupyter_server.services.config import ConfigManager
from traitlets.config import LoggingConfigurable
from traitlets import Unicode, Bool, CInt, Tuple


class Config(LoggingConfigurable):

    reva_host = Unicode(
        config=True,
        allow_none=False,
        help="""Address and port on which the Reva server is listening"""
    )
    client_id = Unicode(
        config=True,
        allow_none=False,
        help="""Client login to authenticate in Reva"""
    )
    client_secret = Unicode(
        config=True,
        allow_none=True,
        help="""Client password to authenticate in Reva"""
    )
    auth_token_validity = CInt(
        default_value=3600,
        config=True,
        allow_none=False,
        help="""The lifetime of the authenticating token"""
    )
    endpoint = Unicode(
        default_value="/",
        config=True,
        help="""Endpoint for Reva storage provider""",
        allow_none=False
    )
    mount_dir = Unicode(
        default_value="/",
        config=True,
        help="""root directory of the filesystem""",
        allow_none=False
    )
    home_dir = Unicode(
        config=True,
        allow_none=True,
        help="""Home directory of the user"""
    )
    root_dir_list = Tuple(
        config=True,
        allow_none=True,
        help="""list of root dirs, for example https://developer.sciencemesh.io/docs/iop/deployment/kubernetes/providers/"""
    )
    chunk_size = CInt(
        default_value=4194304,
        config=True,
        allow_none=False,
        help="""Size of the downloaded fragment from Reva"""
    )
    secure_channel = Bool(
        default_value=False,
        config=True,
        allow_none=False,
        help="""Secure channel flag"""
    )
    authenticator_class = Unicode(
        default_value="cs3api4lab.auth.RevaPassword",
        config=True,
        allow_none=False,
        help="""Authenticator class"""
    )
    login_type = Unicode(
        default_value="basic",
        config=True,
        allow_none=False,
        help="""Reva login type"""
    )
    locks_expiration_time = CInt(
        default_value=150,
        config=True,
        allow_none=False,
        help="""File lock lifetime in seconds"""
    )
    client_key = Unicode(
        config=True,
        allow_none=True,
        help="""Private key file path"""
    )
    client_cert = Unicode(
        config=True,
        allow_none=True,
        help="""Public key file path (PEM-encoded)"""
    )
    ca_cert = Unicode(
        config=True,
        allow_none=True,
        help="""Certificate authority file path"""
    )
    enable_ocm = Bool(
        default_value=False,
        config=True,
        help="""Flag to enable OCM functionality"""
    )
    tus_enabled = Bool(
        default_value=False,
        config=True,
        help="""Flag to enable TUS"""
    )
    eos_file = Unicode(
        config=True,
        allow_none=True,
        help="""EOS file location"""
    )
    kernel_path = Unicode(
        default_value="/",
        config=True,
        allow_none=False,
        help="""Path where the kernel starts"""
    )
    eos_token = Unicode(
        config=True,
        allow_none=True,
        help="""EOS token"""
    )
    oauth_file = Unicode(
        config=True,
        allow_none=True,
        help="""Path for OAuth file"""
    )
    oauth_token = Unicode(
        config=True,
        allow_none=True,
        help="""OAuth token"""
    )
    locks_api = Unicode(
        default_value='metadata',
        config=True,
        allow_none=False,
        help="""Locking API implementation to choose from 'cs3' (cs3apis 
        grpc locks) and 'metadata' (file arbitrary metadata, the default one)""",
    )

    def __init__(self):
        LoggingConfigurable.__init__(self)

        reva_host = self._get_config_value("reva_host")
        if reva_host:
            self.reva_host = reva_host

        client_id = self._get_config_value("client_id")
        if client_id:
            self.client_id = client_id

        client_secret = self._get_config_value("client_secret")
        if client_secret:
            self.client_secret = client_secret

        auth_token_validity = self._get_config_value("auth_token_validity")
        if auth_token_validity:
            self.auth_token_validity = auth_token_validity

        endpoint = self._get_config_value("endpoint")
        if endpoint:
            self.endpoint = endpoint

        mount_dir = self._get_config_value("mount_dir")
        if mount_dir:
            self.mount_dir = mount_dir

        homedir = self._get_config_value("homedir")
        if homedir:
            self.homedir = homedir

        root_dir_list = self._get_config_value("root_dir_list")
        if len(root_dir_list) > 0 and type(root_dir_list) is str:
            root_dir_list = tuple(dir.strip() for dir in root_dir_list.split(','))
        if root_dir_list:
            self.root_dir_list = root_dir_list

        chunk_size = self._get_config_value("chunk_size")
        if chunk_size:
            self.chunk_size = chunk_size

        secure_channel = self._get_config_value("secure_channel")
        if secure_channel in ["true", True]:
            self.secure_channel = True

        authenticator_class = self._get_config_value("authenticator_class")
        if authenticator_class:
            self.authenticator_class = authenticator_class

        login_type = self._get_config_value("login_type")
        if login_type:
            self.login_type = login_type

        locks_expiration_time = self._get_config_value("locks_expiration_time")
        if locks_expiration_time:
            self.locks_expiration_time = locks_expiration_time

        client_key = self._get_config_value("client_key")
        if client_key:
            self.client_key = client_key

        client_cert = self._get_config_value("client_cert")
        if client_cert:
            self.client_cert = client_cert

        ca_cert = self._get_config_value("ca_cert")
        if ca_cert:
            self.ca_cert = ca_cert

        tus_enabled = self._get_config_value("tus_enabled")
        if tus_enabled in ["true", True]:
            self.tus_enabled = True

        enable_ocm = self._get_config_value("enable_ocm")
        if enable_ocm in ["true", True]:
            self.enable_ocm = True

        kernel_path = self._get_config_value("kernel_path")
        if kernel_path:
            self.kernel_path = kernel_path

        eos_file = self._get_config_value("eos_file")
        if eos_file:
            self.eos_file = eos_file

        eos_token = self._get_config_value("eos_token")
        if eos_token:
            self.eos_token = eos_token

        oauth_file = self._get_config_value("oauth_file")
        if oauth_file:
            self.oauth_file = oauth_file

        oauth_token = self._get_config_value("oauth_token")
        if oauth_token:
            self.oauth_token = oauth_token

        locks_api = self._get_config_value("locks_api")
        if locks_api:
            self.locks_api = locks_api

    def _get_config_value(self, key):
        env = os.getenv("CS3_" + key.upper())
        if env:
            return env
        elif self._file_config(key) is not None:
            return self._file_config(key)
        else:
            return None

    __config_dir = "jupyter-config"
    __config_file_name = 'jupyter_cs3_config'
    __file_config = None

    def _file_config(self, key):
        if self.__file_config is None:
            config_path = jupyter_config_path()
            if self.__config_dir not in config_path:
                # add self._config_dir to the front, if set manually
                # might be os.path.join(os.getcwd(), 'cs3api4lab', self.__config_dir) depending on the environment setup"
                config_path.insert(0, os.path.join(os.getcwd(), self.__config_dir))
            cm = ConfigManager(read_config_path=config_path)
            try:
                config_file = cm.get(self.__config_file_name)
                self.__file_config = config_file.get("cs3", {})
            except Exception as e:
                self.log.warn("No config files found")
                self.__file_config = {}
        return self.__file_config[key] if key in self.__file_config else None


class Cs3ConfigManager:
    __config_instance = None

    @classmethod
    def get_config(cls):
        if not cls.__config_instance:
            cls.__config_instance = Config()
        return cls.__config_instance

    @classmethod
    def clean(cls):
        cls.__config_instance = None
