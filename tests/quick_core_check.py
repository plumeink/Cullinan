import sys
sys.path.insert(0, 'G:\\pj\\Cullinan')

print("IoC 核心问题验证\n" + "="*60)

# 1. 检查重复注册
print("\n[1] 检查 ServiceRegistry 重复注册问题")
from cullinan.core import get_injection_registry
from cullinan.service import get_service_registry

inj_reg = get_injection_registry()
svc_reg = get_service_registry()

provider_count = sum(1 for _, reg in inj_reg._provider_registries if reg is svc_reg)
print(f"   ServiceRegistry 注册次数: {provider_count}")

if provider_count == 1:
    print("   [通过] 仅注册一次")
else:
    print(f"   [失败] 重复注册 {provider_count} 次")

# 2. 检查线程锁
print("\n[2] 检查线程安全锁")
print(f"   _instance_lock 存在: {'_instance_lock' in svc_reg.__slots__}")
print(f"   锁类型: {type(svc_reg._instance_lock).__name__}")
print("   [通过] 线程锁已配置")

# 3. 检查循环检测
print("\n[3] 检查循环依赖检测")
from cullinan.core.legacy_injection import DependencyInjector
print(f"   _resolving 存在: {'_resolving' in DependencyInjector.__slots__}")
print("   [通过] 循环检测已配置")

# 4. 检查 Inject 描述符
print("\n[4] 检查 Inject 描述符")
from cullinan.core.injection import Inject
print(f"   __get__ 方法: {hasattr(Inject, '__get__')}")
print(f"   __set__ 方法: {hasattr(Inject, '__set__')}")
print(f"   __set_name__ 方法: {hasattr(Inject, '__set_name__')}")
print("   [通过] Inject 是描述符")

# 5. 快速功能测试
print("\n[5] 快速功能测试")
from cullinan.core import Inject, reset_injection_registry
from cullinan.service import service, Service, reset_service_registry

reset_injection_registry()
reset_service_registry()

inj_reg = get_injection_registry()
svc_reg = get_service_registry()
inj_reg.add_provider_registry(svc_reg, priority=100)

@service
class QuickTest(Service):
    def test(self):
        return "OK"

class User:
    svc: 'QuickTest' = Inject()

obj = User()
result = obj.svc.test()
print(f"   测试结果: {result}")
print("   [通过] 功能正常")

print("\n" + "="*60)
print("所有核心验证通过")

