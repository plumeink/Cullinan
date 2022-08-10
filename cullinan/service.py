# -*- coding: utf-8 -*-

service_list = {}


class Response(object):
    # TYPE_LIST = {"JSON": "application/json", "ROW": "text/xml", "FORM": "application/x-www-form-urlencoded"}
    __body__ = ''
    __headers__ = []
    __status__ = 200
    __status_msg__ = ''
    __is_static__ = False

    # __type__ = 'JSON'

    def set_status(self, status, msg):
        self.__status__ = status
        self.__status_msg__ = msg

    def get_status(self):
        return self.__status__

    def set_body(self, data):
        self.__body__ = data

    def add_header(self, name, value):
        self.__headers__.append([name, value])

    def set_is_static(self, boolean):
        self.__is_static__ = boolean

    def get_is_static(self):
        return self.__is_static__

    # def set_type(self, response_type):
    #     if response_type == self.TYPE_LIST["JSON"]:
    #         self.__type__ = response_type
    #     if response_type == self.TYPE_LIST["ROW"]:
    #         self.__type__ = response_type
    #     if response_type == self.TYPE_LIST["FORM"]:
    #         self.__type__ = response_type

    def get_body(self):
        return self.__body__

    def get_headers(self):
        return self.__headers__

    # def get_type(self):
    #     return self.__type__


class Service(object):
    response = Response()

    # @abstractmethod
    # def service(self):
    #     pass
    #
    # @abstractmethod
    # def set_info(self):
    #     pass


class StatusResponse(Response):
    def __init__(self, **kwargs):
        if kwargs.get("status", None) is not None and kwargs.get("status_msg", None) is not None:
            self.set_status(kwargs["status"], kwargs["status_msg"])
        if kwargs.get("headers", None) is not None:
            for key, value in kwargs["headers"]:
                self.add_header(key, value)
        if kwargs.get("body", None) is not None:
            self.set_body(kwargs["body"])


def response_build(**kwargs):
    return StatusResponse(**kwargs)


def service(cls):
    if service_list.get(cls.__name__, None) is None:
        service_list[cls.__name__] = cls()
