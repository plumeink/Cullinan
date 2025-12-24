# Cullinan 框架依赖注入问题排查指南

## 问题描述

当你在使用 Cullinan 框架时遇到以下错误：

```
cullinan.core.exceptions.RegistryError: Required dependency 'ServiceName' not found
```

这表示依赖注入系统无法找到指定的服务。

## 快速诊断

### 1. 检查服务是否注册

```python
from cullinan.service import get_service_registry

service_registry = get_service_registry()
print(f"已注册的服务: {list(service_registry._items.keys())}")
```

### 2. 检查服务是否初始化

```python
# 查看启动日志
# 应该看到类似：
# - cullinan.service.registry - INFO - Successfully initialized 2 services
```

### 3. 确认装饰器使用正确

```python
from cullinan.service import service

@service  # ✓ 正确
class MyService:
    pass

# ✗ 错误：忘记装饰器
class MyService:
    pass
```

## 常见问题和解决方案

### 问题 1: 打包环境下服务未注册

**症状**: 
- 开发环境正常
- 打包后（PyInstaller/Nuitka）报错
- 日志显示扫描到的模块数为 0

**原因**: 打包工具未包含服务模块，或框架无法扫描文件系统

**解决方案**: 使用显式注册

```python
from cullinan import configure
from my_app.service.user_service import UserService
from my_app.service.auth_service import AuthService
from my_app.controller.user_controller import UserController

# 显式注册所有服务和控制器
configure(
    explicit_services=[
        UserService,
        AuthService,
        # 添加所有其他服务...
    ],
    explicit_controllers=[
        UserController,
        # 添加所有其他控制器...
    ]
)

# 然后启动应用
from cullinan.application import run
run()
```

### 问题 2: 服务名称不匹配

**症状**: 
```
Required dependency 'UserService' not found
Available services: user_service, auth_service
```

**原因**: 服务名称使用了小写或不同的命名

**解决方案**: 使用正确的服务名称

```python
from cullinan.core import InjectByName

@controller(url='/api')
class UserController:
    # ✗ 错误：大小写不匹配
    user_service = InjectByName('UserService')
    
    # ✓ 正确：使用实际的服务名称
    user_service = InjectByName('user_service')
    
    # 或者使用类型注解（自动推断）
    from my_app.service.user_service import UserService
    user_service: UserService = Inject()
```

### 问题 3: 服务初始化失败

**症状**: 日志显示初始化错误

**原因**: 服务的 `__init__` 方法抛出异常

**解决方案**: 检查服务的初始化代码

```python
@service
class DatabaseService:
    def __init__(self):
        try:
            # 可能失败的初始化代码
            self.connection = self._connect()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # 不要 raise，让服务以降级模式运行
            self.connection = None
```

### 问题 4: Controller 未使用 @injectable

**症状**: Controller 的依赖始终为 None

**原因**: Controller 类没有 `@injectable` 装饰器

**解决方案**: 添加装饰器

```python
from cullinan.controller import controller
from cullinan.core import injectable, InjectByName

# ✓ 正确：同时使用 @controller 和 @injectable
@controller(url='/api')
class UserController:
    user_service = InjectByName('UserService')
    
# 注意：@controller 装饰器会自动添加 @injectable，
# 所以通常不需要手动添加
```

## 临时解决方案

如果依赖注入仍然失败，可以手动从注册表获取服务：

```python
from cullinan.controller import controller, post_api
from cullinan.service import get_service_registry
from cullinan.core import InjectByName

@controller(url='/api')
class UserController:
    user_service = InjectByName('UserService')
    
    @post_api(url='/users')
    async def create_user(self, request_body):
        # 尝试使用注入的服务
        try:
            service = self.user_service
        except Exception as e:
            # 回退：手动获取服务
            logger.warning(f"Injection failed, using fallback: {e}")
            service_registry = get_service_registry()
            service = service_registry.get_instance('UserService')
        
        # 验证服务可用
        if not service:
            return {"error": "Service unavailable"}, 503
        
        # 使用服务...
        result = service.create_user(request_body)
        return result
```

## 框架改进

从 v0.9.x 开始，框架已添加**自动回退机制**：

- 当新的注入模型失败时，自动尝试直接从 ServiceRegistry 获取
- 提供详细的错误信息，列出可用的服务
- 记录回退日志，方便诊断

这意味着大多数情况下，即使在打包环境中，依赖注入也能正常工作。

## 诊断工具

使用以下脚本诊断依赖注入问题：

```python
from cullinan.core import get_injection_registry
from cullinan.service import get_service_registry

def diagnose():
    """诊断依赖注入系统"""
    print("=== 依赖注入诊断 ===\n")
    
    # 1. 检查注册表
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    
    print(f"1. InjectionRegistry: {injection_registry}")
    print(f"2. ServiceRegistry: {service_registry}")
    
    # 2. 检查服务数量
    service_count = service_registry.count()
    print(f"\n已注册的服务数量: {service_count}")
    
    # 3. 列出所有服务
    print("\n已注册的服务:")
    for name in service_registry._items.keys():
        print(f"  - {name}")
    
    # 4. 测试依赖解析
    print("\n测试依赖解析:")
    test_service_name = "YourServiceName"  # 修改为你的服务名
    result = injection_registry._resolve_dependency(test_service_name)
    if result:
        print(f"  ✓ 可以解析 '{test_service_name}'")
    else:
        print(f"  ✗ 无法解析 '{test_service_name}'")

if __name__ == '__main__':
    diagnose()
```

## 获取帮助

如果以上方案都无法解决问题：

1. 查看完整文档：`docs/dependency_injection_guide.md`
2. 查看故障排除英文文档：`docs/DEPENDENCY_INJECTION_TROUBLESHOOTING.md`
3. 提交 Issue 到项目仓库，包含：
   - 完整的错误堆栈
   - 服务和 Controller 的代码
   - 启动日志

---

**作者**: Plumeink  
**更新时间**: 2025-12-25

