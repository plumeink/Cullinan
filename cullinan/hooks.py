from cullinan.exceptions import MissingHeaderException


class MissingHeaderHandlerHook:

    @staticmethod
    def miss_header_handler(request, header_name):
        raise MissingHeaderException(request, header_name)

    hook = miss_header_handler

    @classmethod
    def set_hook(cls, hook):
        cls.hook = hook

    @classmethod
    def get_hook(cls):
        return cls.hook
