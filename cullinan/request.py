# -*- coding: utf-8 -*-

import urllib
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl


class Http(object):
    def __init__(self, api_url: str, headers, json_load_switch=False, no_decode=False, json_parse=False):
        self.api_url = api_url
        self.headers = headers
        self.no_decode = no_decode
        self.json_load_switch = json_load_switch
        self.json_parse = json_parse

    def add_header(self, name: str, value: str):
        self.headers.append([name, value])

    def get_headers(self):
        return self.headers

    def delete_header(self, name: str):
        if self.get_headers().__len__() > 0:
            for header in self.get_headers():
                if header[0] == name:
                    self.headers.remove(header)

    def post(self, uri: str, data=None, headers=None):
        url = self.api_url + uri
        request = urllib.request.Request(url, method="POST")
        if self.get_headers().__len__() > 0:
            for header in self.get_headers():
                request.add_header(header[0], header[1])
        if headers is not None:
            for header in headers:
                request.add_header(header[0], header[1])
        return self.http_status(request, data)

    def get(self, uri: str, data=None, headers=None):
        if data is not None:
            url = self.api_url + uri + '?' + data
        else:
            url = self.api_url + uri
        request = urllib.request.Request(url, method="GET")
        if self.get_headers().__len__() > 0:
            for header in self.get_headers():
                request.add_header(header[0], header[1])
        if headers is not None:
            for header in headers:
                request.add_header(header[0], header[1])
        return self.http_status(request)

    def delete(self, uri: str, data=None, headers=None):
        if data is not None:
            url = self.api_url + uri + '?' + data
        else:
            url = self.api_url + uri
        request = urllib.request.Request(url, method="DELETE")
        if self.get_headers().__len__() > 0:
            for header in self.get_headers():
                request.add_header(header[0], header[1])
        if headers is not None:
            for header in headers:
                request.add_header(header[0], header[1])
        return self.http_status(request)

    def put(self, uri: str, data=None, headers=None):
        url = self.api_url + uri
        request = urllib.request.Request(url, method="PUT")
        if self.get_headers().__len__() > 0:
            for header in self.get_headers():
                request.add_header(header[0], header[1])
        if headers is not None:
            for header in headers:
                request.add_header(header[0], header[1])
        return self.http_status(request, data)

    def patch(self, uri: str, data=None, headers=None):
        url = self.api_url + uri
        request = urllib.request.Request(url, method="PATCH")
        if self.get_headers().__len__() > 0:
            for header in self.get_headers():
                request.add_header(header[0], header[1])
        if headers is not None:
            for header in headers:
                request.add_header(header[0], header[1])
        return self.http_status(request, data)

    def http_status(self, request, data=None):
        try:
            context = ssl._create_unverified_context()
            if data is None:
                http_response = urllib.request.urlopen(request, context=context)
            else:
                if self.json_parse is True:
                    data = json.dumps(data)
                    data = bytes(data, encoding='utf8')
                    print('data=', data)
                    http_response = urllib.request.urlopen(request, data=data, context=context)
                else:
                    data = urllib.parse.urlencode(data)
                    data = bytes(data, encoding='utf8')
                    print('data=', data)
                    http_response = urllib.request.urlopen(request, data=data, context=context)
            if self.no_decode is True:
                return http_response.read()
            content = http_response.read().decode('utf-8')
            if self.json_load_switch is True:
                content = json.loads(content)
            return content
        except urllib.error.HTTPError as HTTPError:
            print('code:', HTTPError.code)
            print('reason:', HTTPError.reason)
            return HTTPError.code
