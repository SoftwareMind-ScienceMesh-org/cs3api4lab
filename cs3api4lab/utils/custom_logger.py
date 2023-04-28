# import uuid
#
# class CustomLogger(logging.LoggerAdapter):
#     def __init__(self, logger):
#         traceId = str(uuid.uuid4())
#         super(CustomLogger, self).__init__(logger, {"traceId": traceId})
#
#     def process(self, msg, kwargs):
#         return f'traceId="{self.extra["traceId"]} {msg}', kwargs
from logging import Logger
import uuid
import time

class CustomLogger(Logger):
    log = None
    traceId = None

    def __init__(self, log):
        self.log = log
        self.traceId = str(uuid.uuid4())

    def debug(self, msg, *args, **kwargs):
        params = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
        self.log.debug(f'traceId="{self.traceId}" msg="{msg}" {params}', *args)
        # self.log.debug(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        params = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
        self.log.info(f'traceId="{self.traceId}" msg="{msg}" {params}', *args)
        #self.log.info(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def warning(self, msg, *args, **kwags):
        params = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
        self.log.warning(f'traceId="{self.traceId}" msg="{msg}" {params}', *args)
        # self.log.warning(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        params = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
        self.log.error(f'traceId="{self.traceId}" msg="{msg}" {params}', *args)
        # self.log.error(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        params = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
        self.log.error(f'traceId="{self.traceId}" msg="{msg}" {params}', *args, exc_info=True)
        # self.log.error(f'traceId="{self.traceId}" {msg}', *args, exc_info=exc_info, **kwargs)

    @staticmethod
    def get_timems(time_start):
        return round((time.time() - time_start) * 1000, 1)
