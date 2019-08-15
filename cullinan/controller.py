# -*- coding: utf-8 -*-
# @File   : controller.py
# @license: Copyright(C) 2019 FNEP-Tech
# @Author : hansion, fox
# @Date   : 2019-02-15
# @Desc   : controller
import tornado.web
import types
import functools
from cullinan.service import service_list

url_list = []


class EncapsulationHandler(object):
    @classmethod
    def set_fragment_method(cls, cls_name, func):
        @functools.wraps(func)
        def dummy(self, *args, **kwargs):
            func(self, *args, **kwargs)

        setattr(cls_name, func.__name__, dummy)

    @staticmethod
    def add_url(**kwargs):

        def inner(f):
            url = kwargs['url']
            servlet = type('Servlet' + url.replace('/', ''), (Handler,),
                           {"set_instance_method": EncapsulationHandler.set_fragment_method})
            if url_list.__len__() == 0:
                servlet.set_instance_method(servlet, f)
                servlet.f = types.MethodType(f, servlet)
                url_list.append((url, servlet))
                return servlet
            else:
                for item in url_list:
                    if url == item[0]:
                        item[1].set_instance_method(item[1], f)
                        item[1].f = types.MethodType(f, item[1])
                        return item[1]
                else:
                    servlet.set_instance_method(servlet, f)
                    servlet.f = types.MethodType(f, servlet)
                    url_list.append((url, servlet))
                    return servlet

        return inner


class Handler(tornado.web.RequestHandler):

    def data_received(self, chunk):
        pass

    def set_default_headers(self):
        # 用来解决跨域问题
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-type, contenttype")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, PATCH, PUT, OPTIONS')

    def options(self):
        pass


def request_resolver(self, url_param_key_list, url_param_value_list, query_param_names, body_param_names):
    if url_param_key_list is not None and query_param_names is not None and body_param_names is not None:
        url_param_dict = {}
        for index in range(0, url_param_key_list.__len__()):
            url_param_dict[url_param_key_list[index]] = url_param_value_list[index]
        print("\t|||\t url_params", end="")
        print(url_param_dict)
        query_param_dict = {}
        for name in query_param_names:
            query_param_dict[name] = self.get_query_argument(name)
        print("\t|||\t query_params", end="")
        print(query_param_dict)
        body_param_dict = {}
        for name in body_param_names:
            body_param_dict[name] = self.get_body_argument(name)
        print("\t|||\t body_params", end="")
        print(body_param_dict)
        return url_param_dict, query_param_dict, body_param_dict
    elif query_param_names is not None and url_param_key_list is not None:
        url_param_dict = {}
        for index in range(0, url_param_key_list.__len__()):
            url_param_dict[url_param_key_list[index]] = url_param_value_list[index]
        print("\t|||\t url_params", end="")
        print(url_param_dict)
        query_param_dict = dict()
        for name in query_param_names:
            query_param_dict[name] = self.get_query_argument(name)
        print("\t|||\t query_params", end="")
        print(query_param_dict)
        return url_param_dict, query_param_dict, None
    elif url_param_key_list is not None and body_param_names is not None:
        url_param_dict = {}
        for index in range(0, url_param_key_list.__len__()):
            url_param_dict[url_param_key_list[index]] = url_param_value_list[index]
        print("\t|||\t url_params", end="")
        print(url_param_dict)
        body_param_dict = {}
        for name in body_param_names:
            body_param_dict[name] = self.get_body_argument(name)
        print("\t|||\t body_params", end="")
        print(body_param_dict)
        return url_param_dict, None, body_param_dict
    elif query_param_names is not None and body_param_names is not None:
        query_param_dict = {}
        for name in query_param_names:
            query_param_dict[name] = self.get_query_argument(name)
        print("\t|||\t query_params", end="")
        print(query_param_dict)
        body_param_dict = {}
        for name in body_param_names:
            body_param_dict[name] = self.get_body_argument(name)
        print("\t|||\t body_params", end="")
        print(body_param_dict)
        return None, query_param_dict, body_param_dict
    elif url_param_key_list is not None:
        url_param_dict = {}
        for index in range(0, url_param_key_list.__len__()):
            url_param_dict[url_param_key_list[index]] = url_param_value_list[index]
        print("\t|||\t url_params", end="")
        print(url_param_dict)
        return url_param_dict, None, None
    elif query_param_names is not None:
        query_param_dict = dict()
        for name in query_param_names:
            query_param_dict[name] = self.get_query_argument(name)
        print("\t|||\t query_params", end="")
        print(query_param_dict)
        return None, query_param_dict, None
    elif body_param_names is not None:
        body_param_dict = {}
        for name in body_param_names:
            body_param_dict[name] = self.get_body_argument(name)
        print("\t|||\t body_params", end="")
        print(body_param_dict)
        return None, None, body_param_dict
    else:
        return None, None, None


def header_resolver(self, header_names):
    if header_names is not None:
        need_header = dict()
        for name in header_names:
            need_header[name] = self.request.headers[name]
        print("\t|||\t request_headers", end="")
        print(need_header)
        return need_header
    else:
        return None


def url_resolver(url):
    find_all = lambda origin, target: [i for i in range(origin.find(target), len(origin)) if origin[i] is target]
    before_list = find_all(url, "{")
    after_list = find_all(url, "}")
    url_param_list = []
    for index in range(0, before_list.__len__()):
        url_param_list.append(url[int(before_list[index]) + 1:int(after_list[index])])
    for url_param in url_param_list:
        url = url.replace(url_param, ".*")
    url = url.replace("{", "(").replace("}", ")")
    return url, url_param_list


def request_handler(self, func, service, params, headers):
    global response
    if headers is not None:
        if params[0] is not None and params[1] is not None and params[2] is not None:
            response = func(self, service, headers, params[0], params[1], params[2])
        elif params[0] is not None and params[1] is not None:
            response = func(self, service, headers, params[0], params[1])
        elif params[0] is not None and params[2] is not None:
            response = func(self, service, headers, params[0], params[2])
        elif params[1] is not None and params[2] is not None:
            response = func(self, service, headers, params[1], params[2])
        elif params[0] is not None:
            response = func(self, service, headers, params[0])
        elif params[1] is not None:
            response = func(self, service, headers, params[1])
        elif params[2] is not None:
            response = func(self, service, headers, params[2])
        else:
            response = func(self, service, headers)
    elif params[0] is not None and params[1] is not None and params[2] is not None:
        response = func(self, service, params[0], params[1], params[2])
    elif params[0] is not None and params[1] is not None:
        response = func(self, service, params[0], params[1])
    elif params[0] is not None and params[2] is not None:
        response = func(self, service, params[0], params[2])
    elif params[1] is not None and params[2] is not None:
        response = func(self, service, params[1], params[2])
    elif params[0] is not None:
        response = func(self, service, params[0])
    elif params[1] is not None:
        response = func(self, service, params[1])
    elif params[2] is not None:
        response = func(self, service, params[2])
    else:
        response = func(self, service)
    if response.get_is_static is True:
        self.render(response.get_body())
    if response.get_headers().__len__() > 0:
        for header in response.get_headers():
            self.set_header(header[0], header[1])
    self.write(response.get_body())


def get_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_url(url=kwargs['url'])
        def get(self, *args):
            print("\t||| request:")
            request_handler(self, func, service_list[kwargs['service']],
                            request_resolver(self, url_param_key_list, args, kwargs.get('query_params', None), None),
                            header_resolver(self, kwargs.get('headers', None)))
            # TODO(hansion@fnep-tech.com): Above need to add a judgment to identify whether there is this service

        return get

    return inner


def post_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_url(url=kwargs['url'])
        def post(self, *args):
            print("\t||| request:")
            request_handler(self, func, service_list[kwargs['service']],
                            request_resolver(self, url_param_key_list, args, kwargs.get('query_params', None),
                                             kwargs.get('body_params', None)),
                            header_resolver(self, kwargs.get('headers', None)))
            # TODO(hansion@fnep-tech.com): Above need to add a judgment to identify whether there is this service

        return post

    return inner


def patch_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_url(url=kwargs['url'])
        def patch(self, *args):
            print("\t||| request:")
            request_handler(self, func, service_list[kwargs['service']],
                            request_resolver(self, url_param_key_list, args, kwargs.get('query_params', None),
                                             kwargs.get('body_params', None)),
                            header_resolver(self, kwargs.get('headers', None)))
            # TODO(hansion@fnep-tech.com): Above need to add a judgment to identify whether there is this service

        return patch

    return inner


def delete_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_url(url=kwargs['url'])
        def delete(self, *args):
            print("\t||| request:")
            request_handler(self, func, service_list[kwargs['service']],
                            request_resolver(self, url_param_key_list, args, kwargs.get('query_params', None), None),
                            header_resolver(self, kwargs.get('headers', None)))
            # TODO(hansion@fnep-tech.com): Above need to add a judgment to identify whether there is this service

        return delete

    return inner


def put_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_url(url=kwargs['url'])
        def put(self, *args):
            print("\t||| request:")
            request_handler(self, func, service_list[kwargs['service']],
                            request_resolver(self, url_param_key_list, args, kwargs.get('query_params', None), None),
                            header_resolver(self, kwargs.get('headers', None)))
            # TODO(hansion@fnep-tech.com): Above need to add a judgment to identify whether there is this service

        return put

    return inner
