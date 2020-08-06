# -*- coding: utf-8 -*-
# @File   : controller.py
# @license: Copyright(C) 2020 Ore Studio
# @Author : hansion, fox
# @Date   : 2019-02-15
# @Desc   : controller

import json
import tornado.web
import types
import functools
from cullinan.service import service_list

handler_list = []
controller_func_list = []
KEY_NAME_INDEX = {
    "url_params": 0,
    "query_params": 1,
    "body_params": 2,
}


class EncapsulationHandler(object):
    @classmethod
    def set_fragment_method(cls, cls_name, func):
        @functools.wraps(func)
        def dummy(self, *args, **kwargs):
            func(self, *args, **kwargs)

        setattr(cls_name, func.__name__, dummy)

    @staticmethod
    def add_func(**kwargs):
        def inner(func):
            controller_func_list.append((kwargs['url'], func, kwargs['type']))

        return inner

    @staticmethod
    def add_url(url, f):
        servlet = type('Servlet' + url.replace('/', ''), (Handler,),
                       {"set_instance_method": EncapsulationHandler.set_fragment_method})
        if handler_list.__len__() == 0:
            servlet.set_instance_method(servlet, f)
            servlet.f = types.MethodType(f, servlet)
            handler_list.append((url, servlet))
            return servlet
        else:
            for item in handler_list:
                if url == item[0]:
                    item[1].set_instance_method(item[1], f)
                    item[1].f = types.MethodType(f, item[1])
                    return item[1]
            else:
                servlet.set_instance_method(servlet, f)
                servlet.f = types.MethodType(f, servlet)
                handler_list.append((url, servlet))
                return servlet


class Handler(tornado.web.RequestHandler):

    def data_received(self, chunk):
        pass

    def set_default_headers(self):
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
        if self.request.headers.get("Content-Type") == 'application/json':
            json_data = self.request.body
            data = json.loads(json_data)
            for name in body_param_names:
                body_param_dict[name] = data[name]
        else:
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
        if self.request.headers.get("Content-Type") == 'application/json':
            json_data = self.request.body
            data = json.loads(json_data)
            for name in body_param_names:
                body_param_dict[name] = data[name]
        else:
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
        if self.request.headers.get("Content-Type") == 'application/json':
            json_data = self.request.body
            data = json.loads(json_data)
            for name in body_param_names:
                body_param_dict[name] = data[name]
        else:
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
        if self.request.headers.get("Content-Type") == 'application/json':
            json_data = self.request.body
            data = json.loads(json_data)
            for name in body_param_names:
                body_param_dict[name] = data[name]
        else:
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
        url = url.replace(url_param, "[a-zA-Z0-9-]+")
    url = url.replace("{", "(").replace("}", ")/*")
    return url, url_param_list


def request_handler(self, func, service, params, headers, type, get_request_body=False):
    global response
    global controller_self
    if type is 'get':
        controller_self = self.get_controller_self
    elif type is 'post':
        controller_self = self.post_controller_self
    elif type is 'patch':
        controller_self = self.patch_controller_self
    elif type is 'delete':
        controller_self = self.delete_controller_self
    elif type is 'put':
        controller_self = self.put_controller_self
    param_names = func.__code__.co_varnames
    param_names = list(param_names)
    if "self" in param_names:
        param_names.remove("self")
    else:
        raise Exception("controller参数必须含有self")
    if "service" in param_names:
        param_names.remove("service")
    else:
        raise Exception("controller参数必须含有service")
    if len(param_names) == 0:
        response = func(controller_self, service)
    else:
        param_list = []
        for item in param_names:
            if item in KEY_NAME_INDEX.keys():
                if KEY_NAME_INDEX[item] is not None:
                    param_list.append(params[KEY_NAME_INDEX[item]])
            elif item == 'request_body' and get_request_body is True:
                param_list.append(self.request.body)
            elif item == 'headers' and headers is not None:
                param_list.append(headers)
        if len(param_list) == 0:
            response = func(controller_self, service)
        elif len(param_list) == 1:
            response = func(controller_self, service, param_list[0])
        elif len(param_list) == 2:
            response = func(controller_self, service, param_list[0], param_list[1])
        elif len(param_list) == 3:
            response = func(controller_self, service, param_list[0], param_list[1], param_list[2])
        elif len(param_list) == 4:
            response = func(controller_self, service, param_list[0], param_list[1], param_list[2],
                            param_list[3])
        elif len(param_list) == 5:
            response = func(controller_self, service, param_list[0], param_list[1], param_list[2],
                            param_list[3], param_list[4])
    if response.get_headers().__len__() > 0:
        for header in response.get_headers():
            self.set_header(header[0], header[1])
    self.write(response.get_body())


def get_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_func(url=kwargs['url'], type='get')
        def get(self, *args):
            print("\t||| request:")
            request_handler(self,
                            func,
                            service_list[kwargs['service']],
                            request_resolver(self, self.get_controller_url_param_key_list + url_param_key_list, args,
                                             kwargs.get('query_params', None), None),
                            header_resolver(self, kwargs.get('headers', None)),
                            'get')

        return get


def post_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_func(url=kwargs['url'], type='post')
        def post(self, *args):
            print("\t||| request:")
            request_handler(self,
                            func,
                            service_list[kwargs['service']],
                            request_resolver(self, self.post_controller_url_param_key_list + url_param_key_list, args,
                                             kwargs.get('query_params', None),
                                             kwargs.get('body_params', None)),
                            header_resolver(self, kwargs.get('headers', None)),
                            'post',
                            kwargs.get('get_request_body', False))

        return post

    return inner


def patch_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_func(url=kwargs['url'], type='patch')
        def patch(self, *args):
            print("\t||| request:")
            request_handler(self,
                            func,
                            service_list[kwargs['service']],
                            request_resolver(self, self.patch_controller_url_param_key_list + url_param_key_list, args,
                                             kwargs.get('query_params', None),
                                             kwargs.get('body_params', None)),
                            header_resolver(self, kwargs.get('headers', None)),
                            'patch',
                            kwargs.get('get_request_body', False))

        return patch

    return inner


def delete_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_func(url=kwargs['url'], type='delete')
        def delete(self, *args):
            print("\t||| request:")
            request_handler(self,
                            func,
                            service_list[kwargs['service']],
                            request_resolver(self, self.delete_controller_url_param_key_list + url_param_key_list, args,
                                             kwargs.get('query_params', None), None),
                            header_resolver(self, kwargs.get('headers', None)),
                            'delete')

        return delete

    return inner


def put_api(**kwargs):
    def inner(func):
        url_param_key_list = None
        if kwargs['url'].find("{") is not -1:
            kwargs['url'], url_param_key_list = url_resolver(kwargs['url'])

        @EncapsulationHandler.add_func(url=kwargs['url'], type='put')
        def put(self, *args):
            print("\t||| request:")
            request_handler(self,
                            func,
                            service_list[kwargs['service']],
                            request_resolver(self, self.put_controller_url_param_key_list + url_param_key_list, args,
                                             kwargs.get('query_params', None), None),
                            header_resolver(self, kwargs.get('headers', None)),
                            'put')

        return put

    return inner


def controller(**kwargs):
    url = kwargs.get('url', '')
    global url_params
    if url is not '':
        url, url_params = url_resolver(url)

    def inner(cls):
        for item in controller_func_list:
            if controller_func_list.__len__() is not 0:
                handler = EncapsulationHandler.add_url(url + item[0], item[1])
                setattr(handler, item[2] + '_controller_self', cls)
                setattr(handler, item[2] + '_controller_url_param_key_list', url_params)
        controller_func_list.clear()

    return inner
