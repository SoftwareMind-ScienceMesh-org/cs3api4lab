class Cs3Base:
    _log = None

    auth = None
    file_api = None
    share_api = None
    storage_api = None
    lock_api = None
    user_api = None
    share_api = None
    ocm_share_api = None

    def __init__(self, log):
        self._log = log

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, log):
        self._log = log

        if self.auth:
            if (self.auth.log):
                self.auth.log = log
        if self.file_api:
            self.file_api.log = log
        if self.share_api:
            self.share_api.log = log
        if self.storage_api:
            self.storage_api.log = log
        if self.lock_api:
            self.lock_api.log = log
        if self.user_api:
            self.user_api.log = log
        if self.share_api:
            self.share_api.log = log
        if self.ocm_share_api:
            self.ocm_share_api.log = log

