# Middleware Chain Architecture Design
# 中间件链架构设计文档

**Status**: Design Document (仅设计，暂不实现)  
**Version**: 1.0  
**Last Updated**: 2025-11-09  

---

## 目录

1. [概述](#概述)
2. [设计目标](#设计目标)
3. [架构模型](#架构模型)
4. [接口设计](#接口设计)
5. [实现策略](#实现策略)
6. [示例用例](#示例用例)
7. [性能考量](#性能考量)
8. [集成路径](#集成路径)
9. [未来扩展](#未来扩展)

---

## 概述

### 背景

Cullinan Web 框架当前缺少标准化的中间件系统，导致横切关注点（logging, authentication, rate limiting等）的处理分散且难以复用。本设计文档提出一个基于**洋葱模型**的中间件链架构，旨在提供：

- **可组合性**: 中间件可自由组合和排序
- **可扩展性**: 易于添加新的中间件
- **类型安全**: 使用 Python 类型提示
- **性能优化**: 最小化运行时开销

### 洋葱模型 (Onion Model)

```
Request Flow:
    ↓
[Middleware 1: Logging] ←────────────────┐
    ↓ (request)                          │ (response)
[Middleware 2: Authentication] ←──────┐  │
    ↓ (request)                       │  │
[Middleware 3: Rate Limiting] ←────┐  │  │
    ↓ (request)                    │  │  │
[Handler: Business Logic]          │  │  │
    ↓ (response)                   │  │  │
Response ──────────────────────────┘  │  │
    ↓                                 │  │
Response ─────────────────────────────┘  │
    ↓                                    │
Response ────────────────────────────────┘
```

每个中间件形成一个"层"，请求向内传递，响应向外传递。

---

## 设计目标

### 功能性目标

1. **标准化接口**: 统一的中间件接口，符合 Python Protocol
2. **异步支持**: 完全支持 Tornado 的异步模式
3. **灵活配置**: 支持全局、路由级、处理器级的中间件配置
4. **错误处理**: 优雅处理中间件链中的异常
5. **上下文传递**: 在中间件间传递请求上下文

### 非功能性目标

1. **性能**: 中间件调用开销 < 1ms per request
2. **可测试性**: 中间件独立可测试
3. **向后兼容**: 不破坏现有代码
4. **文档完善**: 提供清晰的使用文档和示例

---

## 架构模型

### 核心组件

```python
from typing import Protocol, Callable, Awaitable, Any, Optional
from dataclasses import dataclass

# 1. Request 和 Response 类型定义
@dataclass
class MiddlewareRequest:
    """中间件请求上下文.
    
    封装 Tornado RequestHandler，提供统一接口供中间件访问请求信息。
    """
    handler: Any  # Tornado RequestHandler
    method: str
    path: str
    headers: dict
    query_params: dict
    body: Optional[bytes]
    context: dict  # 中间件间共享上下文
    
    def get_header(self, name: str, default: Any = None) -> Any:
        """获取请求头."""
        return self.headers.get(name, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文值，供后续中间件使用."""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文值."""
        return self.context.get(key, default)


@dataclass
class MiddlewareResponse:
    """中间件响应对象.
    
    封装 HTTP 响应，中间件可修改响应内容。
    """
    status_code: int = 200
    headers: dict = None
    body: Any = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
    
    def set_header(self, name: str, value: str) -> None:
        """设置响应头."""
        self.headers[name] = value
    
    def set_status(self, code: int) -> None:
        """设置状态码."""
        self.status_code = code
    
    def set_body(self, body: Any) -> None:
        """设置响应体."""
        self.body = body


# 2. 中间件协议
class Middleware(Protocol):
    """中间件协议接口.
    
    所有中间件必须实现此接口。使用 Protocol 而非 ABC 以支持结构化子类型。
    """
    
    async def process(
        self,
        request: MiddlewareRequest,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        """处理请求并调用下一个中间件/处理器.
        
        Args:
            request: 中间件请求上下文
            next_handler: 调用链中的下一个处理器（中间件或最终处理器）
        
        Returns:
            MiddlewareResponse: 响应对象
        
        中间件可以：
        1. 在调用 next_handler 前修改 request（前置处理）
        2. 调用 next_handler(request) 继续链
        3. 在 next_handler 返回后修改 response（后置处理）
        4. 短路请求（不调用 next_handler 直接返回响应）
        
        示例:
            async def process(self, request, next_handler):
                # 前置处理
                logger.info(f"Incoming: {request.method} {request.path}")
                
                # 调用下一个处理器
                response = await next_handler(request)
                
                # 后置处理
                response.set_header('X-Processing-Time', str(elapsed))
                
                return response
        """
        ...
```

### 中间件执行栈

```python
class MiddlewareStack:
    """中间件执行栈.
    
    管理中间件链的构建和执行。采用洋葱模型递归构建调用链。
    """
    
    def __init__(self, middlewares: list[Middleware]):
        """初始化中间件栈.
        
        Args:
            middlewares: 中间件列表，按执行顺序排列
        """
        self.middlewares = middlewares
    
    async def execute(
        self,
        request: MiddlewareRequest,
        final_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        """执行中间件链.
        
        Args:
            request: 请求对象
            final_handler: 最终业务逻辑处理器
        
        Returns:
            MiddlewareResponse: 最终响应
        
        实现说明:
        采用递归嵌套的方式构建调用链：
        1. 从最后一个中间件开始
        2. 每个中间件包装前一个中间件
        3. 形成 middleware_n -> ... -> middleware_1 -> final_handler 的调用链
        """
        # 构建调用链（从最内层开始）
        handler = final_handler
        
        # 反向遍历中间件列表
        for middleware in reversed(self.middlewares):
            handler = self._wrap_middleware(middleware, handler)
        
        # 执行整个链
        return await handler(request)
    
    def _wrap_middleware(
        self,
        middleware: Middleware,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]:
        """包装中间件为异步函数.
        
        Args:
            middleware: 要包装的中间件
            next_handler: 下一个处理器
        
        Returns:
            包装后的异步函数
        """
        async def wrapped(request: MiddlewareRequest) -> MiddlewareResponse:
            return await middleware.process(request, next_handler)
        
        return wrapped
```

---

## 接口设计

### 1. 中间件基类 (可选)

虽然使用 Protocol 不强制继承，但提供基类方便实现：

```python
class BaseMiddleware:
    """中间件基类（可选）.
    
    提供默认实现和辅助方法。
    """
    
    async def process(
        self,
        request: MiddlewareRequest,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        """默认实现：直接调用下一个处理器."""
        return await next_handler(request)
    
    def __call__(self, *args, **kwargs):
        """支持函数式调用."""
        return self.process(*args, **kwargs)
```

### 2. 中间件管理器

```python
from typing import List, Dict, Optional

class MiddlewareManager:
    """中间件管理器.
    
    负责注册、配置和管理中间件。
    """
    
    def __init__(self):
        """初始化管理器."""
        self._global_middlewares: List[Middleware] = []
        self._route_middlewares: Dict[str, List[Middleware]] = {}
    
    def add_global_middleware(self, middleware: Middleware) -> None:
        """添加全局中间件（应用到所有路由）.
        
        Args:
            middleware: 中间件实例
        """
        self._global_middlewares.append(middleware)
    
    def add_route_middleware(self, route: str, middleware: Middleware) -> None:
        """为特定路由添加中间件.
        
        Args:
            route: 路由路径（如 '/api/users'）
            middleware: 中间件实例
        """
        if route not in self._route_middlewares:
            self._route_middlewares[route] = []
        self._route_middlewares[route].append(middleware)
    
    def get_middleware_stack(self, route: Optional[str] = None) -> MiddlewareStack:
        """获取指定路由的中间件栈.
        
        Args:
            route: 路由路径，None 表示只返回全局中间件
        
        Returns:
            MiddlewareStack: 中间件执行栈
        """
        middlewares = self._global_middlewares.copy()
        
        if route and route in self._route_middlewares:
            middlewares.extend(self._route_middlewares[route])
        
        return MiddlewareStack(middlewares)
    
    def clear(self) -> None:
        """清空所有中间件（测试用）."""
        self._global_middlewares.clear()
        self._route_middlewares.clear()


# 全局中间件管理器实例
_middleware_manager: Optional[MiddlewareManager] = None

def get_middleware_manager() -> MiddlewareManager:
    """获取全局中间件管理器."""
    global _middleware_manager
    if _middleware_manager is None:
        _middleware_manager = MiddlewareManager()
    return _middleware_manager
```

### 3. 装饰器支持

```python
from functools import wraps

def use_middleware(*middlewares: Middleware):
    """装饰器：为处理器添加中间件.
    
    用法:
        @use_middleware(LoggingMiddleware(), AuthMiddleware())
        @get_api(url='/api/users')
        def get_users(self):
            return {"users": [...]}
    
    Args:
        *middlewares: 要应用的中间件
    """
    def decorator(func):
        # 存储中间件元数据
        if not hasattr(func, '_middlewares'):
            func._middlewares = []
        func._middlewares.extend(middlewares)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 实际执行由框架处理
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
```

---

## 实现策略

### Phase 1: 核心实现（2-3周）

1. **基础结构**
   - [ ] 实现 `MiddlewareRequest` 和 `MiddlewareResponse`
   - [ ] 实现 `Middleware` Protocol
   - [ ] 实现 `MiddlewareStack`
   - [ ] 实现 `MiddlewareManager`

2. **框架集成**
   - [ ] 修改 `request_handler` 支持中间件链
   - [ ] 添加中间件配置入口
   - [ ] 更新 Controller 装饰器支持中间件

3. **测试**
   - [ ] 单元测试（覆盖率 > 90%）
   - [ ] 集成测试
   - [ ] 性能基准测试

### Phase 2: 标准中间件库（2周）

实现常用中间件：

1. **LoggingMiddleware**: 请求/响应日志
2. **AuthenticationMiddleware**: 身份验证
3. **AuthorizationMiddleware**: 权限检查
4. **RateLimitMiddleware**: 速率限制
5. **CORSMiddleware**: 跨域资源共享
6. **CompressionMiddleware**: 响应压缩
7. **CacheMiddleware**: 响应缓存
8. **ErrorHandlerMiddleware**: 统一错误处理

### Phase 3: 文档与生态（1周）

1. **文档**
   - [ ] 架构文档
   - [ ] API 参考
   - [ ] 最佳实践指南
   - [ ] 示例代码

2. **工具**
   - [ ] 中间件生成器
   - [ ] 调试工具
   - [ ] 性能分析工具

---

## 示例用例

### 示例 1: 日志中间件

```python
import time
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    """记录请求和响应的中间件."""
    
    async def process(
        self,
        request: MiddlewareRequest,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        # 记录请求
        start_time = time.time()
        logger.info(f"→ {request.method} {request.path}")
        
        # 调用下一个处理器
        response = await next_handler(request)
        
        # 记录响应
        elapsed = time.time() - start_time
        logger.info(
            f"← {request.method} {request.path} "
            f"{response.status_code} ({elapsed:.3f}s)"
        )
        
        # 添加处理时间头
        response.set_header('X-Processing-Time', f"{elapsed:.3f}")
        
        return response
```

### 示例 2: 身份验证中间件

```python
class AuthenticationMiddleware:
    """JWT 身份验证中间件."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    async def process(
        self,
        request: MiddlewareRequest,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        # 获取 Authorization 头
        auth_header = request.get_header('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            # 返回 401 未授权
            response = MiddlewareResponse(status_code=401)
            response.set_body({'error': 'Missing or invalid authorization header'})
            return response
        
        # 提取 token
        token = auth_header[7:]  # 去掉 'Bearer '
        
        try:
            # 验证 token（示意）
            user = self._verify_token(token)
            
            # 将用户信息存入上下文
            request.set_context('user', user)
            
            # 继续处理
            return await next_handler(request)
        
        except Exception as e:
            # 返回 401
            response = MiddlewareResponse(status_code=401)
            response.set_body({'error': f'Authentication failed: {str(e)}'})
            return response
    
    def _verify_token(self, token: str) -> dict:
        """验证 JWT token（示意）."""
        import jwt
        return jwt.decode(token, self.secret_key, algorithms=['HS256'])
```

### 示例 3: 速率限制中间件

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimitMiddleware:
    """基于 IP 的速率限制中间件."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """初始化速率限制器.
        
        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)  # IP -> [timestamp, ...]
    
    async def process(
        self,
        request: MiddlewareRequest,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        # 获取客户端 IP
        client_ip = request.handler.request.remote_ip
        
        # 清理过期记录
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip]
            if ts > cutoff
        ]
        
        # 检查是否超限
        if len(self._requests[client_ip]) >= self.max_requests:
            response = MiddlewareResponse(status_code=429)  # Too Many Requests
            response.set_body({
                'error': 'Rate limit exceeded',
                'retry_after': self.window_seconds
            })
            response.set_header('Retry-After', str(self.window_seconds))
            return response
        
        # 记录本次请求
        self._requests[client_ip].append(now)
        
        # 继续处理
        return await next_handler(request)
```

### 示例 4: CORS 中间件

```python
class CORSMiddleware:
    """跨域资源共享中间件."""
    
    def __init__(
        self,
        allow_origins: list[str] = ['*'],
        allow_methods: list[str] = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers: list[str] = ['*'],
        max_age: int = 86400
    ):
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.max_age = max_age
    
    async def process(
        self,
        request: MiddlewareRequest,
        next_handler: Callable[[MiddlewareRequest], Awaitable[MiddlewareResponse]]
    ) -> MiddlewareResponse:
        # 处理 OPTIONS 预检请求
        if request.method == 'OPTIONS':
            response = MiddlewareResponse(status_code=204)
            self._add_cors_headers(response, request)
            return response
        
        # 处理正常请求
        response = await next_handler(request)
        self._add_cors_headers(response, request)
        
        return response
    
    def _add_cors_headers(
        self,
        response: MiddlewareResponse,
        request: MiddlewareRequest
    ) -> None:
        """添加 CORS 响应头."""
        origin = request.get_header('Origin')
        
        if self.allow_origins == ['*'] or origin in self.allow_origins:
            response.set_header('Access-Control-Allow-Origin', origin or '*')
        
        response.set_header(
            'Access-Control-Allow-Methods',
            ', '.join(self.allow_methods)
        )
        
        if self.allow_headers == ['*']:
            requested_headers = request.get_header('Access-Control-Request-Headers')
            if requested_headers:
                response.set_header('Access-Control-Allow-Headers', requested_headers)
        else:
            response.set_header(
                'Access-Control-Allow-Headers',
                ', '.join(self.allow_headers)
            )
        
        response.set_header('Access-Control-Max-Age', str(self.max_age))
```

### 使用示例

```python
from cullinan import configure, run
from cullinan.controller import get_api, controller
from cullinan.middleware import (
    get_middleware_manager,
    LoggingMiddleware,
    AuthenticationMiddleware,
    RateLimitMiddleware,
    CORSMiddleware,
)

# 配置全局中间件
middleware_manager = get_middleware_manager()
middleware_manager.add_global_middleware(LoggingMiddleware())
middleware_manager.add_global_middleware(CORSMiddleware())
middleware_manager.add_global_middleware(RateLimitMiddleware(max_requests=100))

# 为特定路由添加认证
auth_middleware = AuthenticationMiddleware(secret_key='your-secret-key')
middleware_manager.add_route_middleware('/api/admin/*', auth_middleware)

# 定义 Controller
@controller(url='/api')
class UserController:
    
    @get_api(url='/users')
    def get_users(self):
        """公开 API - 不需要认证."""
        return {"users": [{"id": 1, "name": "Alice"}]}
    
    @get_api(url='/admin/users')
    def admin_get_users(self):
        """管理 API - 需要认证."""
        # 从上下文获取已认证用户
        user = self.request.get_context('user')
        return {"admin_users": [...], "requester": user}

# 启动应用
if __name__ == '__main__':
    configure(user_packages=['my_app'])
    run(port=8080)
```

---

## 性能考量

### 1. 性能目标

- **中间件链开销**: < 1ms per request (对于3-5个中间件)
- **内存开销**: < 10KB per request
- **并发处理**: 支持 10,000+ concurrent requests

### 2. 优化策略

#### A. 中间件栈缓存

```python
class CachedMiddlewareManager(MiddlewareManager):
    """带缓存的中间件管理器."""
    
    def __init__(self):
        super().__init__()
        self._stack_cache: Dict[Optional[str], MiddlewareStack] = {}
    
    def get_middleware_stack(self, route: Optional[str] = None) -> MiddlewareStack:
        """获取中间件栈（带缓存）."""
        if route not in self._stack_cache:
            self._stack_cache[route] = super().get_middleware_stack(route)
        return self._stack_cache[route]
    
    def clear_cache(self) -> None:
        """清空缓存."""
        self._stack_cache.clear()
```

#### B. 异步优化

```python
# 使用 asyncio.gather 并行执行独立操作
async def parallel_middleware_init():
    """并行初始化多个中间件."""
    middlewares = [
        LoggingMiddleware(),
        RateLimitMiddleware(),
        CORSMiddleware(),
    ]
    # 如果中间件有异步初始化，可并行执行
    await asyncio.gather(*[m.init() for m in middlewares if hasattr(m, 'init')])
```

#### C. 懒加载

```python
class LazyMiddleware:
    """懒加载中间件包装器."""
    
    def __init__(self, middleware_class, *args, **kwargs):
        self.middleware_class = middleware_class
        self.args = args
        self.kwargs = kwargs
        self._instance = None
    
    async def process(self, request, next_handler):
        if self._instance is None:
            self._instance = self.middleware_class(*self.args, **self.kwargs)
        return await self._instance.process(request, next_handler)
```

### 3. 性能测试

```python
import asyncio
import time

async def benchmark_middleware_stack():
    """性能基准测试."""
    
    # 创建中间件栈
    middlewares = [
        LoggingMiddleware(),
        AuthenticationMiddleware('secret'),
        RateLimitMiddleware(),
    ]
    stack = MiddlewareStack(middlewares)
    
    # 模拟请求
    async def final_handler(request):
        return MiddlewareResponse(body={'result': 'ok'})
    
    request = MiddlewareRequest(
        handler=None,
        method='GET',
        path='/api/test',
        headers={},
        query_params={},
        body=None,
        context={}
    )
    
    # 预热
    for _ in range(100):
        await stack.execute(request, final_handler)
    
    # 测试
    iterations = 10000
    start = time.perf_counter()
    
    for _ in range(iterations):
        await stack.execute(request, final_handler)
    
    elapsed = time.perf_counter() - start
    avg = (elapsed / iterations) * 1000  # ms
    
    print(f"Average middleware chain time: {avg:.4f}ms")
    print(f"Throughput: {iterations/elapsed:.0f} req/s")
```

---

## 集成路径

### 第一步：修改 request_handler

```python
# cullinan/controller.py

async def request_handler_with_middleware(
    self,
    func: Callable,
    params: Tuple,
    headers: Optional[dict],
    type: str,
    get_request_body: bool = False
) -> None:
    """支持中间件的请求处理器."""
    from cullinan.middleware import get_middleware_manager, MiddlewareRequest, MiddlewareResponse
    
    # 获取中间件栈
    manager = get_middleware_manager()
    stack = manager.get_middleware_stack(route=self.request.path)
    
    # 构建中间件请求
    middleware_request = MiddlewareRequest(
        handler=self,
        method=type.upper(),
        path=self.request.path,
        headers=dict(self.request.headers),
        query_params=self.request.arguments,
        body=self.request.body,
        context={}
    )
    
    # 定义最终处理器
    async def final_handler(req: MiddlewareRequest) -> MiddlewareResponse:
        # 调用原始处理器逻辑
        # （省略原有 request_handler 的实现）
        # ...
        return MiddlewareResponse(
            status_code=200,
            body=result
        )
    
    # 执行中间件链
    response = await stack.execute(middleware_request, final_handler)
    
    # 写入响应
    self.set_status(response.status_code)
    for name, value in response.headers.items():
        self.set_header(name, value)
    if response.body:
        self.write(response.body)
    self.finish()
```

### 第二步：更新装饰器

```python
# 添加对中间件装饰器的支持
@use_middleware(AuthenticationMiddleware('secret'))
@get_api(url='/api/users')
def get_users(self):
    user = self.request.get_context('user')
    return {"users": [...], "authenticated_as": user}
```

### 第三步：配置入口

```python
# cullinan/__init__.py

def configure(
    user_packages: list = None,
    middlewares: list = None,  # 新增参数
    **kwargs
):
    """配置 Cullinan 应用.
    
    Args:
        user_packages: 用户应用包列表
        middlewares: 全局中间件列表
        **kwargs: 其他配置选项
    """
    if middlewares:
        from cullinan.middleware import get_middleware_manager
        manager = get_middleware_manager()
        for middleware in middlewares:
            manager.add_global_middleware(middleware)
    
    # 其他配置逻辑...
```

---

## 未来扩展

### 1. 中间件组合器

```python
class MiddlewareComposer:
    """中间件组合器 - 支持中间件链的高级组合."""
    
    @staticmethod
    def combine(*middlewares: Middleware) -> Middleware:
        """组合多个中间件为一个."""
        class CombinedMiddleware:
            async def process(self, request, next_handler):
                stack = MiddlewareStack(list(middlewares))
                return await stack.execute(request, next_handler)
        return CombinedMiddleware()
    
    @staticmethod
    def conditional(
        condition: Callable[[MiddlewareRequest], bool],
        middleware: Middleware
    ) -> Middleware:
        """条件中间件 - 仅在满足条件时执行."""
        class ConditionalMiddleware:
            async def process(self, request, next_handler):
                if condition(request):
                    return await middleware.process(request, next_handler)
                return await next_handler(request)
        return ConditionalMiddleware()
```

### 2. 中间件生命周期钩子

```python
class LifecycleMiddleware(Protocol):
    """支持生命周期的中间件."""
    
    async def on_startup(self) -> None:
        """应用启动时调用."""
        ...
    
    async def on_shutdown(self) -> None:
        """应用关闭时调用."""
        ...
    
    async def process(self, request, next_handler):
        """处理请求."""
        ...
```

### 3. 中间件依赖注入

```python
from typing import TypeVar, Type

T = TypeVar('T')

class DependencyInjection:
    """中间件依赖注入容器."""
    
    def __init__(self):
        self._services = {}
    
    def register(self, service_type: Type[T], instance: T) -> None:
        """注册服务."""
        self._services[service_type] = instance
    
    def resolve(self, service_type: Type[T]) -> T:
        """解析服务."""
        return self._services.get(service_type)

# 使用示例
class DatabaseMiddleware:
    def __init__(self, db: Database):  # 依赖注入
        self.db = db
    
    async def process(self, request, next_handler):
        request.set_context('db', self.db)
        return await next_handler(request)
```

### 4. 插件系统

```python
class MiddlewarePlugin:
    """中间件插件接口."""
    
    def install(self, manager: MiddlewareManager) -> None:
        """安装插件."""
        ...
    
    def uninstall(self, manager: MiddlewareManager) -> None:
        """卸载插件."""
        ...

# 示例：安全插件
class SecurityPlugin(MiddlewarePlugin):
    def install(self, manager):
        manager.add_global_middleware(CORSMiddleware())
        manager.add_global_middleware(CSRFMiddleware())
        manager.add_global_middleware(RateLimitMiddleware())
```

---

## 总结

本设计文档提出了 Cullinan Web 框架的中间件链架构，基于洋葱模型实现：

**核心优势**:
- ✅ 清晰的接口设计（基于 Protocol）
- ✅ 灵活的组合能力（可自由组合中间件）
- ✅ 性能优化（缓存、异步、懒加载）
- ✅ 向后兼容（不破坏现有代码）
- ✅ 易于测试（中间件独立可测）

**实施路径**:
1. Phase 1: 核心实现（2-3周）
2. Phase 2: 标准中间件库（2周）
3. Phase 3: 文档与生态（1周）

**下一步行动**:
1. 评审本设计文档
2. 获取社区反馈
3. 开始 Phase 1 实现

---

**附录**:
- [性能基准测试脚本](#)
- [中间件开发指南](#)
- [常见问题 FAQ](#)
