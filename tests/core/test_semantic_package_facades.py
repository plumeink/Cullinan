from cullinan.application import Application, configure, get_asgi_app, module, run
from cullinan.application import bind_runtime_request_context, release_runtime_request_context
from cullinan.core import get_injection_registry, injectable
from cullinan.runtime import get_scan_stats_collector, list_submodules
from cullinan.support import get_config, get_packaging_mode
from cullinan.transport import ASGIAdapter, WebAdapter
from cullinan.web import Body, Path, WebRequest, WebResponse, controller, get_api, middleware


def test_semantic_application_facade_exports():
    assert Application is not None
    assert configure is not None
    assert run is not None
    assert get_asgi_app is not None
    assert module is not None


def test_semantic_web_facade_exports():
    assert controller is not None
    assert get_api is not None
    assert middleware is not None
    assert Path is not None
    assert Body is not None
    assert WebRequest is not None
    assert WebResponse is not None


def test_runtime_transport_support_and_core_facades():
    assert list_submodules is not None
    assert get_scan_stats_collector() is not None
    assert WebAdapter is not None
    assert ASGIAdapter is not None
    assert get_packaging_mode is not None
    assert get_config is not None
    assert injectable is not None
    assert get_injection_registry is not None
def test_application_facade_exports_runtime_context_helpers():
    assert bind_runtime_request_context is not None
    assert release_runtime_request_context is not None
