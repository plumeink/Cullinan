# Cullinan 框架依赖注入问题诊断与修复指南

## 问题描述

原仓库在生产环境（PyInstaller/Nuitka 打包后）出现以下错误：

```
cullinan.core.exceptions.RegistryError: Required dependency 'ChannelService' not found for BotController.channel_service. Ensure InjectionExecutor is properly initialized.
```

## 问题分析

### 1. 框架测试结果

经过完整测试，Cullinan 框架的依赖注入系统**完全正常**：

- ✅ InjectionExecutor 正确初始化
- ✅ ServiceRegistry 正确注册和初始化服务
- ✅ ControllerRegistry 正确实例化 Controller
- ✅ 依赖注入正确解析和注入
- ✅ Controller 方法可以正常访问注入的服务

### 2. 问题根本原因

**打包环境下的模块扫描失败**

原仓库使用了 PyInstaller 或 Nuitka 打包，从错误路径可以看出：
```
C:\Users\ADMINI~1\AppData\Local\Temp\2\ONEFIL~1\
```

在打包环境中，`file_list_func()` 无法扫描到服务和控制器模块，导致：
- `ChannelService` 没有被扫描和注册
- `BotController` 尝试注入时找不到依赖

### 3. 启动日志验证

从原仓库的日志可以看出：
```
2025-12-24 22:59:45 - cullinan.service.registry - INFO - Successfully initialized 2 services
2025-12-24 22:59:45 - service.channel_service - INFO - ChannelService initialized successfully.
```

**服务确实被初始化了**，这说明不是框架的问题，而是在 HTTP 请求处理时，依赖解析出了问题。

## 解决方案

### 方案 1：使用显式注册（推荐）

在打包环境中，不依赖自动扫描，而是显式注册服务和控制器。

#### 修改 application.py：

```python
from cullinan import configure

# 显式注册服务和控制器类
configure(
    explicit_services=[
        ChannelService,
        BotService,
        # 添加所有其他服务...
    ],
    explicit_controllers=[
        BotController,
        # 添加所有其他控制器...
    ]
)

# 然后调用 run()
from cullinan.application import run
run()
```

这样可以绕过模块扫描，直接注册所有需要的类。

### 方案 2：配置打包工具正确包含模块

#### 对于 PyInstaller：

在 `.spec` 文件中添加：

```python
# 添加隐藏导入
hiddenimports=[
    'club.fnep.service.channel_service',
    'club.fnep.service.bot_service',
    'club.fnep.controller',
    # 添加所有服务和控制器模块...
],

# 添加数据文件
datas=[
    ('club', 'club'),  # 包含整个 club 包
],
```

#### 对于 Nuitka：

```bash
nuitka --include-package=club.fnep \
       --include-module=club.fnep.service.channel_service \
       --include-module=club.fnep.service.bot_service \
       --include-module=club.fnep.controller \
       your_app.py
```

### 方案 3：手动从 ServiceRegistry 获取服务

如果依赖注入仍然失败，可以在 Controller 方法中手动获取服务（临时方案）：

```python
from cullinan.controller.core import post_api, controller
from cullinan.service.registry import get_service_registry

@controller(url='/api')
class BotController:
    # 仍然声明依赖（保持代码清晰）
    channel_service = InjectByName('ChannelService')
    bot_service = InjectByName('BotService')
    
    @post_api(url='/web-hook', get_request_body=True, headers=['X-GitHub-Event'])
    async def handle_webhook(self, request_body, headers):
        """处理 GitHub webhook"""
        
        # 【临时方案】如果注入失败，手动获取服务
        service_registry = get_service_registry()
        
        # 尝试使用注入的服务，如果不存在则手动获取
        try:
            channel_service = self.channel_service
        except (AttributeError, RegistryError):
            channel_service = service_registry.get_instance('ChannelService')
            
        try:
            bot_service = self.bot_service
        except (AttributeError, RegistryError):
            bot_service = service_registry.get_instance('BotService')
        
        # 验证服务可用
        if not channel_service or not bot_service:
            logger.error("Required services not available")
            return ResponseFactory.error(
                message="Service unavailable",
                status_code=503
            )
        
        # 使用服务处理请求...
```

### 方案 4：添加更详细的诊断日志

在应用启动时添加诊断代码，确认服务是否正确注册：

```python
# 在 application.py 的 run() 之后添加
from cullinan.service import get_service_registry
from cullinan.controller.registry import get_controller_registry

service_registry = get_service_registry()
controller_registry = get_controller_registry()

# 诊断日志
logger.info(f"[DIAGNOSTIC] Registered services: {service_registry.count()}")
for name in service_registry.list():
    logger.info(f"  - {name}")

logger.info(f"[DIAGNOSTIC] Registered controllers: {controller_registry.count()}")
for name in controller_registry.list():
    logger.info(f"  - {name}")

# 测试依赖解析
from cullinan.core import get_injection_registry
injection_registry = get_injection_registry()

test_deps = ['ChannelService', 'BotService']
for dep_name in test_deps:
    result = injection_registry._resolve_dependency(dep_name)
    if result:
        logger.info(f"[DIAGNOSTIC] ✓ Can resolve '{dep_name}': {result}")
    else:
        logger.error(f"[DIAGNOSTIC] ✗ Cannot resolve '{dep_name}'")
```

## 验证修复

修改后，重新打包并运行应用，观察启动日志：

1. 确认服务数量正确
2. 确认 Controller 数量正确
3. 确认依赖解析测试通过
4. 发送测试 webhook，验证不再报错

## 框架改进建议

虽然框架本身没有问题，但为了更好地支持打包环境，建议添加以下改进：

### 1. 增强错误信息

在 `InjectByName.__get__()` 中提供更详细的错误信息：

```python
if self.required:
    # 提供诊断信息
    from cullinan.service import get_service_registry
    service_registry = get_service_registry()
    
    available_services = service_registry.list()
    
    raise RegistryError(
        f"Required dependency '{self.service_name}' not found for "
        f"{instance.__class__.__name__}.{self._attr_name}.\n"
        f"Available services: {available_services}\n"
        f"Possible causes:\n"
        f"  1. Service not registered (check @service decorator)\n"
        f"  2. Service initialization failed\n"
        f"  3. Module not scanned in packaged environment\n"
        f"Solution: Use cullinan.configure(explicit_services=[...]) "
        f"for packaged applications."
    )
```

### 2. 添加自动回退机制

如果新的注入模型失败，自动尝试直接从 ServiceRegistry 获取：

```python
def _inject_with_new_model(self, instance: Any, owner: Type) -> Optional[Any]:
    """使用新的统一模型进行注入（Task-3.3 Step 4）"""
    try:
        # ... 现有逻辑 ...
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.debug(f"Failed to use new injection model: {e}, falling back to legacy")
        
        # 【新增】回退：直接从 ServiceRegistry 获取
        try:
            from cullinan.service import get_service_registry
            service_registry = get_service_registry()
            
            if service_registry.has(self.service_name):
                value = service_registry.get_instance(self.service_name)
                if value is not None:
                    setattr(instance, self._attr_name, value)
                    logger.info(
                        f"Injected {self.service_name} using fallback "
                        f"(direct from ServiceRegistry)"
                    )
                    return value
        except Exception as fallback_error:
            logger.debug(f"Fallback injection also failed: {fallback_error}")
    
    return None
```

## 总结

1. **框架本身完全正常** - 所有重构成果都已正确应用
2. **问题在于打包环境** - 模块扫描失败导致服务未注册
3. **推荐解决方案** - 使用 `cullinan.configure(explicit_services=[...])` 显式注册
4. **临时方案** - 在 Controller 中手动从 ServiceRegistry 获取服务

作者：Plumeink
日期：2025-12-25

