# import uuid
# import logging
#
# class CustomLogger(logging.LoggerAdapter):
#     def __init__(self, logger):
#         traceId = str(uuid.uuid4())
#         super(CustomLogger, self).__init__(logger, {"traceId": traceId})
#
#     def process(self, msg, kwargs):
#         return f'traceId="{self.extra["traceId"]} {msg}', kwargs

import uuid

class CustomLogger():
    log = None
    traceId = None

    def __init__(self, log):
        self.log = log
        self.traceId = str(uuid.uuid4())

    def debug(self, msg, *args, **kwargs):
        self.log.debug(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log.info(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def warning(self, msg, *args, **kwags):
        self.log.warning(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log.error(f'traceId="{self.traceId}" {msg}', *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        self.log.error(f'traceId="{self.traceId}" {msg}', *args, exc_info=exc_info, **kwargs)
