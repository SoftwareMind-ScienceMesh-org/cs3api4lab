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

    # def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
    #     trace_id = str(uuid.uuid4())
    #     msg = f'traceId="{trace_id}" - {msg}'
    #     super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)