# Cullinan 依赖注入快速参考

## 基本用法

### 1. 定义服务

```python
from cullinan.service import service

@service
class UserService:
    def __init__(self):
        self.name = "UserService"
    
    def get_user(self, user_id):
        return {"id": user_id, "name": "John"}
```

### 2. 注入服务到 Controller

```python
from cullinan.controller import controller
from cullinan.core import Inject, InjectByName

@controller(url='/api')
class UserController:
    # 方式1: 类型注解（推荐）
    user_service: UserService = Inject()
    
    # 方式2: 显式指定名称
    auth_service = InjectByName('AuthService')
    
    # 方式3: 可选依赖
    cache_service = InjectByName('CacheService', required=False)
```

### 3. 使用注入的服务

```python
@controller(url='/api')
class UserController:
    user_service: UserService = Inject()
    
    @get_api(url='/users/{user_id}')
    async def get_user(self, user_id):
        # 直接使用注入的服务
        user = self.user_service.get_user(user_id)
        return user
```

## 打包应用配置

### 使用显式注册（推荐）

```python
from cullinan import configure
from my_app.service.user_service import UserService
from my_app.service.auth_service import AuthService
from my_app.controller.user_controller import UserController

# 在 run() 之前配置
configure(
    explicit_services=[
        UserService,
        AuthService,
    ],
    explicit_controllers=[
        UserController,
    ]
)

from cullinan.application import run
run()
```

### PyInstaller 配置

```python
# your_app.spec
hiddenimports=[
    'my_app.service.user_service',
    'my_app.service.auth_service',
],
datas=[
    ('my_app', 'my_app'),
],
```

### Nuitka 配置

```bash
nuitka --include-package=my_app \
       --include-module=my_app.service.user_service \
       your_app.py
```

## 故障排查

### 检查已注册的服务

```python
from cullinan.service import get_service_registry

service_registry = get_service_registry()
print(f"服务数量: {service_registry.count()}")
print(f"服务列表: {list(service_registry._items.keys())}")
```

### 手动获取服务（回退方案）

```python
@controller(url='/api')
class UserController:
    user_service = InjectByName('UserService')
    
    @post_api(url='/users')
    async def create_user(self, request_body):
        # 尝试使用注入
        try:
            service = self.user_service
        except:
            # 回退：手动获取
            from cullinan.service import get_service_registry
            service_registry = get_service_registry()
            service = service_registry.get_instance('UserService')
        
        return service.create_user(request_body)
```

## 常见错误

### 错误 1: 服务未注册

```
RegistryError: Required dependency 'UserService' not found
```

**解决**: 确保服务使用了 `@service` 装饰器

### 错误 2: 名称不匹配

```
Available services: user_service, auth_service
```

**解决**: 使用实际的服务名称（可能是小写）

```python
# ✗ 错误
user_service = InjectByName('UserService')

# ✓ 正确
user_service = InjectByName('user_service')

# 或使用类型注解（自动推断）
user_service: UserService = Inject()
```

### 错误 3: 打包环境扫描失败

**解决**: 使用显式注册（见上文）

## 更多信息

- 完整指南: `docs/dependency_injection_guide.md`
- 故障排除: `docs/zh/dependency_injection_troubleshooting.md`
- API 文档: `docs/api_reference.md`

