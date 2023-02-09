from cs3api4lab.auth.authenticator import Authenticator


class RevaPassword(Authenticator):

    def __init__(self, cs3_config=None, log=None):
        super().__init__(cs3_config, log)

    def refresh_token(self, client_id=None, client_secret_or_token=None):
        self.token = self._auth_in_iop(self.cs3_config.client_secret, "basic")
