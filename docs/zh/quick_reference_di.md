# Cullinan 依赖注入快速参考

> **版本**: v0.90  
> **作者**: Plumeink

## 基本用法

### 1. 定义服务

```python
from cullinan.service import service, Service

@service
class UserService(Service):
    def __init__(self):
        super().__init__()
        self.name = "UserService"
    
    def get_user(self, user_id):
        return {"id": user_id, "name": "John"}
```

### 2. 注入服务到 Controller

```python
from cullinan.controller import controller, get_api
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
from cullinan.controller import controller, get_api
from cullinan.core import Inject

@controller(url='/api')
class UserController:
    user_service: UserService = Inject()
    
    @get_api(url='/users/<user_id>')
    async def get_user(self, url_param):
        user_id = url_param.get('user_id')
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

| 问题 | 解决方案 |
|------|----------|
| 依赖为 None | 确保服务使用 `@service` 装饰器 |
| 找不到服务 | 检查服务名称是否匹配（区分大小写） |
| 循环依赖 | 使用 `InjectByName()` 进行延迟解析 |
| 注入不生效 | 确保类继承自 `Service` 或 `Controller` |

## 另请参阅

- [依赖注入指南](dependency_injection_guide.md) - 完整 DI 文档
- [架构设计](architecture.md) - 系统架构概览
- [迁移指南](migration_guide.md) - 从旧版本迁移
