# -*- coding: utf-8 -*-
# @File   : service.py
# @license: Copyright(C) 2020 Ore Studio
# @Author : hansion
# @Date   : 2019-02-22
# @Desc   : service

service_list = {}


class Response(object):
    # TYPE_LIST = {"JSON": "application/json", "ROW": "text/xml", "FORM": "application/x-www-form-urlencoded"}
    __body__ = ''
    __headers__ = []
    __is_static__ = False
    # __type__ = 'JSON'

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


def service(cls):
    if service_list.get(cls.__name__, None) is None:
        service_list[cls.__name__] = cls()
