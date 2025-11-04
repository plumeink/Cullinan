# -*- coding: utf-8 -*-

service_list = {}


class Service(object):
    pass

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
