# -*- coding: utf-8 -*-
"""Regression: ResponseFactory-style code (using set_header) must work.

作者：Plumeink
"""

import json
import tornado.testing
import tornado.web

from cullinan.controller import controller, post_api
from cullinan.handler import get_handler_registry


class ResponseFactoryLike:
    @staticmethod
    def success(message: str):
        from cullinan.controller import response_build
        resp = response_build()
        resp.set_status(200)
        # legacy-style API
        resp.set_header('Content-Type', 'application/json')
        resp.set_body({'ok': True, 'message': message})
        return resp


@controller(url='/api')
class RFController:
    @post_api(url='/rf', get_request_body=True)
    def rf(self, request_body):
        _ = request_body
        return ResponseFactoryLike.success('hi')


class TestResponseFactoryCompat(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        handlers = get_handler_registry().get_handlers()
        return tornado.web.Application(handlers)

    def test_set_header_compat_and_body_not_empty(self):
        resp = self.fetch('/api/rf', method='POST', body='{}', headers={'Content-Type': 'application/json'})
        assert resp.code == 200
        assert resp.body
        data = json.loads(resp.body)
        assert data['ok'] is True
        assert data['message'] == 'hi'

