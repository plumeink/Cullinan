# -*- coding: utf-8 -*-
"""Regression tests for controller method registration.

This covers a class of bugs where decorator context leaks or is cleared,
causing controllers to register with 0 methods and returning 200/empty body.

作者：Plumeink
"""

from cullinan.controller import controller, get_api, post_api, get_controller_registry


def test_controller_methods_registered_for_multiple_controllers():
    registry = get_controller_registry()
    registry.clear()

    @controller(url='/api/a')
    class AController:
        @get_api(url='')
        def a(self):
            return {'a': 1}

    @controller(url='/api/b')
    class BController:
        @post_api(url='/x', get_request_body=True)
        def b(self, request_body):
            return {'b': True}

    a_methods = registry.get_methods('AController')
    b_methods = registry.get_methods('BController')

    assert len(a_methods) == 1
    assert len(b_methods) == 1

    # Ensure correct method types
    assert a_methods[0][1] == 'get'
    assert b_methods[0][1] == 'post'

