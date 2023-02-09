from cs3api4lab.auth.authenticator import Authenticator


class Oauth(Authenticator):

    def __init__(self, cs3_config=None, log=None):
        super().__init__(cs3_config, log)

    def refresh_token(self):
        oauth_token = self._refresh_token_from_file_or_config()
        self.token = self._auth_in_iop(oauth_token, "bearer")

    def _refresh_token_from_file_or_config(self):
        """
        Get OAuth token from file or config value and try to convert IOP token (authentication process)
        """

        if self.cs3_config.oauth_file:

            try:
                with open(self.cs3_config.oauth_file, "r") as file:
                    oauth_token = file.read()
            except IOError as e:
                raise IOError(f"Error opening token file {self.cs3_config.oauth_file} exception: {e}")

        elif self.cs3_config.oauth_token:
            oauth_token = self.cs3_config.oauth_token
        else:
            raise AttributeError("Config hasn't OAuth token or token file.")

        if self._check_token(oauth_token) is False:
            self.raise_401_error()

        return oauth_token
