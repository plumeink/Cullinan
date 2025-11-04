# python
# -*- coding: utf-8 -*-

import json
import inspect
import tornado.web
import tornado.websocket
import types
import functools
import contextvars
import logging
import time
import os
import json
from cullinan.hooks import MissingHeaderHandlerHook
from cullinan.service import service_list
from typing import Callable, Optional, Sequence, Tuple, TYPE_CHECKING, Any, Protocol

class ResponseProtocol(Protocol):
    def push(self, resp: Any) -> Any: ...
    def pop(self, token: Any) -> None: ...
    def get(self) -> Any: ...

if TYPE_CHECKING:
    # help static analyzers: at type-check time `response` behaves like ResponseProtocol
    response: ResponseProtocol

logger = logging.getLogger(__name__)
# access logger (separate name so users can configure access logs separately)
access_logger = logging.getLogger('cullinan.access')

handler_list = []
header_list = []
controller_func_list = []
KEY_NAME_INDEX = {
    "url_params": 0,
    "query_params": 1,
    "body_params": 2,
    "file_params": 3,
}


class ResponseProxy:
    """
    contextvars `ContextVar` 代理，用作模块级的 response。
    - push(resp) 绑定实例，返回 token（用于 reset）
    - pop(token) 恢复上下文
    - get() 获取当前实例（可能为 None）
    - __getattr__ 委托到当前实例，便于原有代码直接调用 response.xxx
    """
    def __init__(self):
        self._ctx = contextvars.ContextVar("cullinan_response", default=None)

    def push(self, resp):
        return self._ctx.set(resp)

    def pop(self, token):
        try:
            self._ctx.reset(token)
        except Exception:
            pass

    def get(self):
        return self._ctx.get()

    def _ensure(self):
        resp = self.get()
        if resp is None:
            raise RuntimeError("no Response bound in this context")
        return resp

    def __getattr__(self, name):
        return getattr(self._ensure(), name)


class LazyResponseMeta(type):
    """
    元类：把模块名 `response` 当作惰性代理类对象。
    - 不在导入时实例化真实代理
    - 第一次读取或写入非私有成员时创建并缓存 ResponseProxy 实例
    """
    def __getattribute__(cls, name):
        # 私有或元属性仍使用类自身
        if name.startswith('_'):
            return super().__getattribute__(name)
        inst = cls.__dict__.get('_instance', None)
        if inst is None:
            inst = ResponseProxy()
            super().__setattr__('_instance', inst)
        return getattr(inst, name)

    def __setattr__(cls, name, value):
        if name.startswith('_'):
            return super().__setattr__(name, value)
        inst = cls.__dict__.get('_instance', None)
        if inst is None:
            inst = ResponseProxy()
            super().__setattr__('_instance', inst)
        setattr(inst, name, value)

    def __repr__(cls):
        inst = cls.__dict__.get('_instance', None)
        if inst is None:
            return "<lazy response (not initialized)>"
        return repr(inst)


# 模块级名为 `response` 的惰性代理类（*不是实例*，避免导入时的副作用）
class response(metaclass=LazyResponseMeta):
    """惰性响应代理类（模块级名，行为等同于原先的 ResponseProxy 实例）"""

    # Stubs to help static analysis / IDEs detect available methods (runtime is handled by metaclass).
    def push(self, resp):
        """Stub: real implementation lives in the lazily created ResponseProxy instance."""
        raise RuntimeError("response proxy not initialized")

    def pop(self, token):
        raise RuntimeError("response proxy not initialized")

    def get(self):
        raise RuntimeError("response proxy not initialized")

    def __getattr__(self, name):
        # stub fallback
        raise AttributeError(name)


class EncapsulationHandler(object):
    @classmethod
    def set_fragment_method(cls, cls_obj: Any, func: Callable[[object, tuple, dict], None]):
        @functools.wraps(func)
        def dummy(self, *args, **kwargs):
            func(self, *args, **kwargs)

        setattr(cls_obj, func.__name__, dummy)

    @staticmethod
    def add_func(url: str, type: str) -> Callable:
        def inner(func: Callable):
            controller_func_list.append((url, func, type))

        return inner

    @staticmethod
    def add_url(url: str, f: Callable) -> object:
        # create servlet type plainly
        servlet = type('Servlet' + url.replace('/', ''), (Handler,), {})
        # attach the handler function as an instance method via set_fragment_method
        if len(handler_list) == 0:
            EncapsulationHandler.set_fragment_method(servlet, f)
            servlet.f = types.MethodType(f, servlet)
            handler_list.append((url, servlet))
            return servlet
        else:
            for item in handler_list:
                if url == item[0]:
                    EncapsulationHandler.set_fragment_method(item[1], f)
                    item[1].f = types.MethodType(f, item[1])
                    return item[1]
            else:
                EncapsulationHandler.set_fragment_method(servlet, f)
                servlet.f = types.MethodType(f, servlet)
                handler_list.append((url, servlet))
                return servlet

    @staticmethod
    def add_url_ws(url: str, cls: Callable) -> object:
        servlet = type('Servlet' + url.replace('/', ''), (tornado.websocket.WebSocketHandler,), {})
        setattr(servlet, 'service', service_list)
        if len(handler_list) == 0:
            for item in dir(cls):
                if not item.startswith('__') and not item.endswith('__'):
                    setattr(servlet, item, cls.__dict__[item])
            handler_list.append((url, servlet))
            return servlet
        else:
            for item in handler_list:
                if url == item[0]:
                    for i in dir(cls):
                        if not i.startswith('__') and not i.endswith('__'):
                            setattr(servlet, item, cls.__dict__[item])
                    return item[1]
            else:
                for item in dir(cls):
                    if not item.startswith('__') and not item.endswith('__'):
                        setattr(servlet, item, cls.__dict__[item])
                handler_list.append((url, servlet))
                return servlet


class Handler(tornado.web.RequestHandler):

    @classmethod
    def set_instance_method(cls, cls_name, func):
        """Forwarder used by the dynamic servlet factory so static analysis can see the method.

        The real registration uses EncapsulationHandler.set_fragment_method which sets an instance
        method on the class; this forwarder simply calls that implementation.
        """
        EncapsulationHandler.set_fragment_method(cls_name, func)

    def data_received(self, chunk):
        pass

    def set_default_headers(self):
        if header_list:
            for header in header_list:
                self.set_header(header[0], header[1])

    def options(self):
        pass


def request_resolver(self,
                     url_param_key_list: Optional[Sequence] = None,
                     url_param_value_list: Optional[Sequence] = None,
                     query_param_names: Optional[Sequence] = None,
                     body_param_names: Optional[Sequence] = None,
                     file_param_key_list: Optional[Sequence] = None) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict]]:
    """
    Unified resolver: accept optional sequences and normalize them to concrete tuples/lists.
    Returns (url_dict|None, query_dict|None, body_dict|None, file_dict|None).
    """
    # normalize inputs to concrete sequences
    url_param_key_list = tuple(url_param_key_list or ())
    url_param_value_list = tuple(url_param_value_list or ())
    query_param_names = tuple(query_param_names or ())
    body_param_names = tuple(body_param_names or ())
    file_param_key_list = list(file_param_key_list or [])

    url_dict = None
    query_dict = None
    body_dict = None
    file_dict = None

    # URL params
    if url_param_key_list:
        url_dict = {}
        for i, k in enumerate(url_param_key_list):
            try:
                url_dict[k] = url_param_value_list[i]
            except Exception:
                url_dict[k] = None
        logger.info("\t||| url_params %s", url_dict)

    # Query params
    if query_param_names:
        query_dict = {}
        for name in query_param_names:
            try:
                query_dict[name] = self.get_query_argument(name)
            except Exception:
                query_dict[name] = None
        logger.info("\t||| query_params %s", query_dict)

    # Body params
    if body_param_names:
        body_dict = {}
        ctype = (self.request.headers.get('Content-Type') or '').lower()
        is_json = ctype.startswith('application/json')
        if is_json:
            try:
                raw = self.request.body or b'{}'
                data = json.loads(raw)
            except Exception:
                data = {}
            for name in body_param_names:
                body_dict[name] = data.get(name)
        else:
            for name in body_param_names:
                try:
                    body_dict[name] = self.get_body_argument(name)
                except Exception:
                    body_dict[name] = None
        logger.info("\t||| body_params %s", body_dict)

    # File params
    if file_param_key_list:
        file_dict = {}
        for name in file_param_key_list:
            file_dict[name] = (self.request.files.get(name) if isinstance(self.request.files, dict) else None)
        logger.info("\t||| file_params %s", list((file_dict or {}).keys()))

    return url_dict, query_dict, body_dict, file_dict


def header_resolver(self, header_names: Optional[Sequence] = None) -> Optional[dict]:
    header_names = list(header_names or [])
    if header_names:
        need_header = {}
        for name in header_names:
            need_header[name] = self.request.headers.get(name)
            if need_header[name] is not None:
                logger.info("\t||| request_headers %s", {name: need_header[name]})
            else:
                miss_header_handler = MissingHeaderHandlerHook.get_hook()
                miss_header_handler(request=self, header_name=name)
        return need_header
    return None


def url_resolver(url: str) -> tuple:
    find_all = lambda origin, target: [i for i in range(origin.find(target), len(origin)) if origin[i] == target]
    before_list = find_all(url, "{")
    after_list = find_all(url, "}")
    url_param_list = []
    for index in range(0, len(before_list)):
        url_param_list.append(url[int(before_list[index]) + 1:int(after_list[index])])
    for url_param in url_param_list:
        url = url.replace(url_param, "[a-zA-Z0-9-]+")
    url = url.replace("{", "(").replace("}", ")/*")
    return url, url_param_list


class _SimpleResponse:
    """Fallback minimal response implementing the expected interface"""
    def __init__(self):
        self._headers = []
        self._status = 200
        self._body = ''

    def get_headers(self):
        return list(self._headers)

    def get_status(self):
        return self._status

    def get_body(self):
        return self._body


def emit_access_log(request, resp_obj, status_code, duration):
    """Emit an access log using the configured format.

    Formats supported via env var CULLINAN_ACCESS_LOG_FORMAT:
      - 'combined' (default): Apache combined-like format
      - 'json': structured JSON object

    This helper is public for testing or custom hooks; the framework calls it
    automatically from request_handler.
    """
    try:
        fmt = os.getenv('CULLINAN_ACCESS_LOG_FORMAT', 'combined').strip().lower()
        method = getattr(request, 'method', '-')
        uri = getattr(request, 'uri', getattr(request, 'path', '-'))
        client = getattr(request, 'remote_ip', None) or getattr(request, 'remote_addr', None) or getattr(request, 'remote_ip', None) or '-'
        # headers may be present on Tornado request
        headers = getattr(request, 'headers', {}) or {}
        referer = headers.get('Referer', headers.get('referer', '-'))
        user_agent = headers.get('User-Agent', headers.get('user-agent', '-'))
        # content length from response object if available
        content_length = '-'
        try:
            if resp_obj is not None and hasattr(resp_obj, 'get_body'):
                body = resp_obj.get_body()
                if isinstance(body, (bytes, bytearray)):
                    content_length = len(body)
                elif isinstance(body, str):
                    content_length = len(body.encode('utf-8'))
                elif hasattr(body, '__len__'):
                    content_length = len(body)
        except Exception:
            content_length = '-'

        if fmt == 'json':
            obj = {
                'remote_addr': client,
                'method': method,
                'path': uri,
                'status_code': status_code,
                'duration': round(duration, 3),
                'content_length': content_length,
                'referer': referer or '-',
                'user_agent': user_agent or '-',
            }
            access_logger.info(json.dumps(obj, ensure_ascii=False))
        else:
            # combined-like: remote - - [time] "METHOD URI HTTP/1.1" status length "referer" "user-agent" duration
            now = time.strftime('%d/%b/%Y:%H:%M:%S')
            line = '%s - - [%s] "%s %s HTTP/1.1" %s %s "%s" "%s" %.3f' % (
                client, now, method, uri, status_code or '-', content_length, referer or '-', user_agent or '-', duration)
            access_logger.info(line)
    except Exception:
        logger.exception('failed to emit access log')


def request_handler(self, func, params, headers, type, get_request_body=False):
    global controller_self
    start_time = time.time()
    # 选择 controller_self（保持原有分支逻辑）
    if type == 'get':
        controller_self = self.get_controller_self
    elif type == 'post':
        controller_self = self.post_controller_self
    elif type == 'patch':
        controller_self = self.patch_controller_self
    elif type == 'delete':
        controller_self = self.delete_controller_self
    elif type == 'put':
        controller_self = self.put_controller_self
    else:
        raise Exception("unsupported request type")

    # 注入 service 与 module-level proxy（controller 方法仍可通过 self.response 访问）
    setattr(controller_self, 'service', service_list)
    setattr(controller_self, 'response', response)
    setattr(controller_self, 'response_factory', response_build)

    # 构造真实 response 实例（若 response_build 可调用则调用），回退为 _SimpleResponse
    resp_instance = None
    try:
        if callable(response_build):
            resp_instance = response_build()
        else:
            resp_instance = response_build
    except Exception:
        logger.error('response_build failed, falling back to _SimpleResponse', exc_info=True)
        resp_instance = _SimpleResponse()

    if resp_instance is None:
        resp_instance = _SimpleResponse()

    # 绑定到 contextvars，返回 token
    token = response.push(resp_instance)

    try:
        # 使用 inspect.signature 获取参数名并构建参数列表
        sig = inspect.signature(func)
        param_names = [p.name for p in sig.parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        if param_names and param_names[0] == 'self':
            param_names = param_names[1:]

        param_list = []
        for name in param_names:
            if name in KEY_NAME_INDEX:
                idx = KEY_NAME_INDEX[name]
                try:
                    param_list.append(params[idx])
                except Exception:
                    param_list.append(None)
            elif name == 'request_body' and get_request_body:
                param_list.append(self.request.body)
            elif name == 'headers' and headers is not None:
                param_list.append(headers)
            else:
                param_list.append(None)

        # 调用目标函数
        response_ret = func(controller_self, *param_list) if len(param_list) > 0 else func(controller_self)

        # 返回值优先，否则使用 context 中绑定的实例
        if response_ret is not None and hasattr(response_ret, "get_headers") and hasattr(response_ret, "get_status") and hasattr(response_ret, "get_body"):
            resp_obj = response_ret
        else:
            resp_obj = response.get()

        # 写出 headers/status/body（保留全局 header_list 行为）
        if len(header_list) > 0:
            for header in header_list:
                self.set_header(header[0], header[1])
        if resp_obj and getattr(resp_obj, "get_headers", None):
            for header in (resp_obj.get_headers() or []):
                self.set_header(header[0], header[1])
        if resp_obj:
            try:
                self.set_status(resp_obj.get_status())
            except Exception:
                self.set_status(200)
            try:
                self.write(resp_obj.get_body())
            except Exception:
                self.write(str(getattr(resp_obj, 'get_body', lambda: '')()))
        else:
            self.set_status(204)

        # 恢复/清理真实 response 实例内部状态（兼容原有逻辑，但更健壮）
        try:
            real_resp = response.get()
            if real_resp is not None:
                if hasattr(real_resp, '__body__'):
                    real_resp.__body__ = ''
                if hasattr(real_resp, '__headers__'):
                    real_resp.__headers__ = []
                if hasattr(real_resp, '__status__'):
                    real_resp.__status__ = 200
                if hasattr(real_resp, '__status_msg__'):
                    real_resp.__status_msg__ = ''
                if hasattr(real_resp, '__is_static__'):
                    real_resp.__is_static__ = False
        except Exception:
            pass

        self.finish()
    finally:
        # access log: method, uri, status, duration, client ip
        try:
            duration = time.time() - start_time
            try:
                status_code = self.get_status()
            except Exception:
                # fallback: if resp_obj is present, try to read status
                status_code = getattr(resp_obj, 'get_status', lambda: None)()
            client_ip = getattr(self.request, 'remote_ip', None) or getattr(self.request, 'remote_addr', None)
            # delegate to emit_access_log which supports different formats
            emit_access_log(self.request, resp_obj, status_code, duration)
        except Exception:
            # don't let logging failures break response cleanup
            logger.exception('access log failed')
        # 一定要 pop，避免污染下一个请求/扫描
        response.pop(token)


def get_api(**kwargs: dict):
    def inner(func):
        url_param_key_list = []
        local_url = kwargs.get('url', '')
        if local_url.find("{") != -1:
            local_url, url_param_key_list = url_resolver(local_url)

        @EncapsulationHandler.add_func(url=local_url, type='get')
        def get(self, *args):
            logger.info("\t||| request:")
            # normalize potential None values into tuples/lists for static analysis
            caller_keys = tuple(self.get_controller_url_param_key_list or ()) if getattr(self, 'get_controller_url_param_key_list', None) is not None else tuple(url_param_key_list)
            url_values = tuple(args)
            query_params = tuple(kwargs.get('query_params') or ())
            file_params = list(kwargs.get('file_params') or [])

            request_handler(self,
                            func,
                            request_resolver(self, caller_keys + tuple(url_param_key_list),
                                             url_values,
                                             query_params, None,
                                             file_params),
                            header_resolver(self, list(kwargs.get('headers') or [])),
                            'get')

        return get

    return inner


def post_api(**kwargs: dict):
    def inner(func):
        url_param_key_list = []
        local_url = kwargs.get('url', '')
        if local_url.find("{") != -1:
            local_url, url_param_key_list = url_resolver(local_url)

        @EncapsulationHandler.add_func(url=local_url, type='post')
        def post(self, *args):
            logger.info("\t||| request:")
            caller_keys = tuple(self.post_controller_url_param_key_list or ()) if getattr(self, 'post_controller_url_param_key_list', None) is not None else tuple(url_param_key_list)
            url_values = tuple(args)
            query_params = tuple(kwargs.get('query_params') or ())
            body_params = list(kwargs.get('body_params') or [])
            file_params = list(kwargs.get('file_params') or [])

            request_handler(self,
                            func,
                            request_resolver(self, caller_keys + tuple(url_param_key_list),
                                             url_values,
                                             query_params,
                                             body_params,
                                             file_params),
                            header_resolver(self, list(kwargs.get('headers') or [])),
                            'post',
                            kwargs.get('get_request_body', False))

        return post

    return inner


def patch_api(**kwargs: dict):
    def inner(func):
        url_param_key_list = []
        local_url = kwargs.get('url', '')
        if local_url.find("{") != -1:
            local_url, url_param_key_list = url_resolver(local_url)

        @EncapsulationHandler.add_func(url=local_url, type='patch')
        def patch(self, *args):
            logger.info("\t||| request:")
            caller_keys = tuple(self.patch_controller_url_param_key_list or ()) if getattr(self, 'patch_controller_url_param_key_list', None) is not None else tuple(url_param_key_list)
            url_values = tuple(args)
            query_params = tuple(kwargs.get('query_params') or ())
            body_params = list(kwargs.get('body_params') or [])
            file_params = list(kwargs.get('file_params') or [])

            request_handler(self,
                            func,
                            request_resolver(self,
                                             caller_keys + tuple(url_param_key_list), url_values,
                                             query_params,
                                             body_params, file_params),
                            header_resolver(self, list(kwargs.get('headers') or [])),
                            'patch',
                            kwargs.get('get_request_body', False))

        return patch

    return inner


def delete_api(**kwargs: dict):
    def inner(func):
        url_param_key_list = []
        local_url = kwargs.get('url', '')
        if local_url.find("{") != -1:
            local_url, url_param_key_list = url_resolver(local_url)

        @EncapsulationHandler.add_func(url=local_url, type='delete')
        def delete(self, *args):
            logger.info("\t||| request:")
            caller_keys = tuple(self.delete_controller_url_param_key_list or ()) if getattr(self, 'delete_controller_url_param_key_list', None) is not None else tuple(url_param_key_list)
            url_values = tuple(args)
            query_params = tuple(kwargs.get('query_params') or ())
            file_params = list(kwargs.get('file_params') or [])

            request_handler(self,
                            func,
                            request_resolver(self,
                                             caller_keys + tuple(url_param_key_list), url_values,
                                             query_params, None, file_params),
                            header_resolver(self, list(kwargs.get('headers') or [])),
                            'delete')

        return delete

    return inner


def put_api(**kwargs: dict):
    def inner(func):
        url_param_key_list = []
        local_url = kwargs.get('url', '')
        if local_url.find("{") != -1:
            local_url, url_param_key_list = url_resolver(local_url)

        @EncapsulationHandler.add_func(url=local_url, type='put')
        def put(self, *args):
            logger.info("\t||| request:")
            caller_keys = tuple(self.put_controller_url_param_key_list or ()) if getattr(self, 'put_controller_url_param_key_list', None) is not None else tuple(url_param_key_list)
            url_values = tuple(args)
            query_params = tuple(kwargs.get('query_params') or ())
            file_params = list(kwargs.get('file_params') or [])

            request_handler(self,
                            func,
                            request_resolver(self,
                                             caller_keys + tuple(url_param_key_list), url_values,
                                             query_params, None, file_params),
                            header_resolver(self, list(kwargs.get('headers') or [])),
                            'put')

        return put

    return inner


def controller(**kwargs) -> Callable:
    url = kwargs.get('url', '')
    global url_params
    url_params = None
    if url != '':
        url, url_params = url_resolver(url)

    def inner(cls):
        for item in controller_func_list:
            if controller_func_list:
                handler = EncapsulationHandler.add_url(url + item[0], item[1])
                setattr(handler, item[2] + '_controller_self', cls)
                setattr(handler, item[2] + '_controller_url_param_key_list', url_params)
        controller_func_list.clear()

    return inner

class HttpResponse(object):
    # TYPE_LIST = {"JSON": "application/json", "ROW": "text/xml", "FORM": "application/x-www-form-urlencoded"}
    __body__ = ''
    __headers__ = []
    __status__ = 200
    __status_msg__ = ''
    __is_static__ = False

    # __type__ = 'JSON'

    def set_status(self, status, msg = ''):
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

class StatusResponse(HttpResponse):
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