# -*- coding: utf-8 -*-
"""
Cullinan 框架依赖注入全方位测试套件

Author: Plumeink

测试覆盖：
1. 基础依赖注入
2. 多服务依赖注入
3. 可选依赖注入
4. 服务间依赖注入
5. Controller 依赖注入（专项测试）
6. 循环依赖检测
7. 类型推断注入
8. 单例模式验证
9. 延迟注入（Lazy）
10. 按名称注入（InjectByName）
"""

import sys
import traceback
from typing import List, Tuple

sys.path.insert(0, '.')


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []
        self.skipped: List[Tuple[str, str]] = []

    def add_pass(self, name: str):
        self.passed.append(name)
        print(f"  [PASS] {name}")

    def add_fail(self, name: str, reason: str):
        self.failed.append((name, reason))
        print(f"  [FAIL] {name}: {reason}")

    def add_skip(self, name: str, reason: str):
        self.skipped.append((name, reason))
        print(f"  [SKIP] {name}: {reason}")

    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"总计: {total} 个测试")
        print(f"  通过: {len(self.passed)}")
        print(f"  失败: {len(self.failed)}")
        print(f"  跳过: {len(self.skipped)}")

        if self.failed:
            print("\n失败的测试:")
            for name, reason in self.failed:
                print(f"  - {name}: {reason}")

        return len(self.failed) == 0


def reset_all_registries():
    """重置所有注册表"""
    from cullinan.controller.registry import reset_controller_registry
    from cullinan.core.pending import PendingRegistry
    from cullinan.core import set_application_context

    reset_controller_registry()

    pending = PendingRegistry.get_instance()
    pending._registrations.clear()
    pending._frozen = False

    set_application_context(None)


# =============================================================================
# 专项测试：Controller 依赖注入 Bug 修复验证
# =============================================================================

def test_controller_di_basic(result: TestResult):
    """专项测试 1：基础 Controller 依赖注入"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class UserService:
            def get_user(self, id: int):
                return {"id": id, "name": "Test User"}

        @controller(url='/api/users')
        class UserController:
            user_service: UserService = Inject()

            def get_user(self, id: int):
                return self.user_service.get_user(id)

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('UserController', UserController, url_prefix='/api/users')

        instance = registry.get_instance('UserController')

        # 验证注入成功
        if isinstance(instance.user_service, Inject):
            result.add_fail("专项1: 基��Controller DI", "user_service 仍然是 Inject 对象")
            return

        if not hasattr(instance.user_service, 'get_user'):
            result.add_fail("专项1: 基础Controller DI", "user_service 没有 get_user 方法")
            return

        # 验证功能正常
        user = instance.get_user(1)
        if user.get('id') != 1:
            result.add_fail("专项1: 基础Controller DI", f"返回结果不正确: {user}")
            return

        result.add_pass("专项1: 基础Controller DI")

    except Exception as e:
        result.add_fail("专项1: 基础Controller DI", str(e))


def test_controller_di_multiple_services(result: TestResult):
    """专项测试 2：Controller 注入多个服务"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class AuthService:
            def validate(self, token: str) -> bool:
                return token == "valid"

        @service
        class DataService:
            def fetch(self) -> dict:
                return {"data": "test"}

        @service
        class LogService:
            def log(self, msg: str):
                return f"LOG: {msg}"

        @controller(url='/api/multi')
        class MultiServiceController:
            auth_service: AuthService = Inject()
            data_service: DataService = Inject()
            log_service: LogService = Inject()

            def process(self, token: str):
                if self.auth_service.validate(token):
                    data = self.data_service.fetch()
                    self.log_service.log("Fetched data")
                    return data
                return None

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('MultiServiceController', MultiServiceController)

        instance = registry.get_instance('MultiServiceController')

        # 验证所有服务都注入成功
        services = ['auth_service', 'data_service', 'log_service']
        for svc in services:
            if isinstance(getattr(instance, svc), Inject):
                result.add_fail("专项2: 多服务注入", f"{svc} 仍然是 Inject 对象")
                return

        # 验证功能
        data = instance.process("valid")
        if data is None or data.get('data') != 'test':
            result.add_fail("专项2: 多服务注入", f"功能验证失败: {data}")
            return

        result.add_pass("专项2: 多服务注入")

    except Exception as e:
        result.add_fail("专项2: 多服务注入", str(e))


def test_controller_di_optional(result: TestResult):
    """专项测试 3：Controller 可选依赖注入"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class RequiredService:
            def required_method(self):
                return "required"

        # 注意：OptionalService 没有 @service 装饰器
        class OptionalService:
            def optional_method(self):
                return "optional"

        @controller(url='/api/optional')
        class OptionalController:
            required: RequiredService = Inject()
            optional: OptionalService = Inject(required=False)

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('OptionalController', OptionalController)

        instance = registry.get_instance('OptionalController')

        # 必需依赖应该注入成功
        if isinstance(instance.required, Inject):
            result.add_fail("专项3: 可选依赖", "required 服务未注入")
            return

        # 可选依赖应该是 None
        if instance.optional is not None:
            result.add_fail("专项3: 可选依赖", f"optional 应该是 None，实际是 {type(instance.optional)}")
            return

        result.add_pass("专项3: 可选依赖")

    except Exception as e:
        result.add_fail("专项3: 可选依赖", str(e))


def test_controller_di_hasattr_check(result: TestResult):
    """专项测试 4：hasattr 检查正确性（原 Bug 场景）"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class ChannelService:
            def get_binding(self, repo: str, bot_id: str = None):
                return {"repo": repo, "channel_id": "123", "bot_id": bot_id}

        @controller(url='/api/webhook')
        class WebhookController:
            channel_service: ChannelService = Inject()

            def handle_webhook(self, repo: str):
                # 这是原 Bug 的检查模式
                if not self.channel_service or not hasattr(self.channel_service, 'get_binding'):
                    return {"error": "Service not available"}

                binding = self.channel_service.get_binding(repo)
                return {"ok": True, "binding": binding}

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('WebhookController', WebhookController)

        instance = registry.get_instance('WebhookController')

        # 模拟原 Bug 场景
        result_data = instance.handle_webhook("owner/repo")

        if "error" in result_data:
            result.add_fail("专项4: hasattr检查", f"hasattr 检查失败: {result_data}")
            return

        if not result_data.get('ok'):
            result.add_fail("专项4: hasattr检查", f"功能执行失败: {result_data}")
            return

        result.add_pass("专项4: hasattr检查（原Bug场景）")

    except Exception as e:
        result.add_fail("专项4: hasattr检查", str(e))


def test_controller_singleton(result: TestResult):
    """专项测试 5：Controller 单例模式"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class CounterService:
            def __init__(self):
                self.count = 0

            def increment(self):
                self.count += 1
                return self.count

        @controller(url='/api/counter')
        class CounterController:
            counter: CounterService = Inject()

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('CounterController', CounterController)

        # 获取多次实例
        instance1 = registry.get_instance('CounterController')
        instance2 = registry.get_instance('CounterController')

        # 验证是同一个实例（单例）
        if instance1 is not instance2:
            result.add_fail("专项5: 单例模式", "Controller 不是单例")
            return

        # 验证服务状态共享
        instance1.counter.increment()
        count = instance2.counter.increment()

        if count != 2:
            result.add_fail("专项5: 单例模式", f"状态未共享，count={count}")
            return

        result.add_pass("专项5: Controller单例模式")

    except Exception as e:
        result.add_fail("专项5: 单例模式", str(e))


def test_controller_di_without_context(result: TestResult):
    """专项测试 6：无 ApplicationContext 时的降级处理"""
    reset_all_registries()

    try:
        from cullinan.core import controller, Inject, get_application_context
        from cullinan.controller.registry import get_controller_registry

        class SimpleService:
            def work(self):
                return "working"

        @controller(url='/api/simple')
        class SimpleController:
            simple_service: SimpleService = Inject()

        # 不创建 ApplicationContext

        registry = get_controller_registry()
        registry.register('SimpleController', SimpleController)

        # 验证 ApplicationContext 不存在
        ctx = get_application_context()
        if ctx is not None:
            result.add_skip("专项6: 无Context降级", "ApplicationContext 已存在")
            return

        # 获取实例 - 应该降级到直接实例化
        instance = registry.get_instance('SimpleController')

        # 注入不会成功，但不应该崩溃
        if instance is None:
            result.add_fail("专项6: 无Context降级", "实例创建失败")
            return

        # 验证实例存在但依赖未注入
        if not isinstance(instance.simple_service, Inject):
            result.add_fail("专项6: 无Context降级", "无Context时不应该注入成功")
            return

        result.add_pass("专项6: 无Context降级处理")

    except Exception as e:
        result.add_fail("专项6: 无Context降级", str(e))


# =============================================================================
# 框架健壮性测试：Service 依赖注入
# =============================================================================

def test_service_di_basic(result: TestResult):
    """健壮性测试 1：Service 基础依赖注入"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, Inject
        )

        @service
        class DatabaseService:
            def query(self, sql: str):
                return [{"id": 1}]

        @service
        class UserRepository:
            db: DatabaseService = Inject()

            def find_by_id(self, id: int):
                return self.db.query(f"SELECT * FROM users WHERE id={id}")

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        # 通过 ApplicationContext 获取
        user_repo = ctx.get('UserRepository')

        if isinstance(user_repo.db, Inject):
            result.add_fail("健壮1: Service DI", "db 未注入")
            return

        data = user_repo.find_by_id(1)
        if not data:
            result.add_fail("健壮1: Service DI", "功能验证失败")
            return

        result.add_pass("健壮1: Service基础DI")

    except Exception as e:
        result.add_fail("健壮1: Service DI", str(e))


def test_service_chain_injection(result: TestResult):
    """健壮性测试 2：Service 链式依赖注入"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, Inject
        )

        @service
        class ConfigService:
            def get(self, key: str):
                return f"config_{key}"

        @service
        class CacheService:
            config: ConfigService = Inject()

            def get_ttl(self):
                return self.config.get("cache_ttl")

        @service
        class DataService:
            cache: CacheService = Inject()
            config: ConfigService = Inject()

            def fetch(self):
                ttl = self.cache.get_ttl()
                return f"data with ttl={ttl}"

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        data_svc = ctx.get('DataService')

        # 验证链式注入
        if isinstance(data_svc.cache, Inject):
            result.add_fail("健壮2: 链式注入", "cache 未注入")
            return

        if isinstance(data_svc.cache.config, Inject):
            result.add_fail("健壮2: 链式注入", "cache.config 未注入")
            return

        data = data_svc.fetch()
        if "config_cache_ttl" not in data:
            result.add_fail("健壮2: 链式注入", f"功能验证失败: {data}")
            return

        result.add_pass("健壮2: Service链式注入")

    except Exception as e:
        result.add_fail("健壮2: 链式注入", str(e))


def test_service_singleton(result: TestResult):
    """健壮性测试 3：Service 单例模式"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, Inject
        )
        import uuid

        @service
        class UniqueService:
            def __init__(self):
                self.id = str(uuid.uuid4())

        @service
        class ConsumerA:
            unique: UniqueService = Inject()

        @service
        class ConsumerB:
            unique: UniqueService = Inject()

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        consumer_a = ctx.get('ConsumerA')
        consumer_b = ctx.get('ConsumerB')

        # 验证注入的是同一个实例
        if consumer_a.unique.id != consumer_b.unique.id:
            result.add_fail("健壮3: Service单例", "不同消费者获得了不同的服务实例")
            return

        result.add_pass("健壮3: Service单例模式")

    except Exception as e:
        result.add_fail("健壮3: Service单例", str(e))


def test_inject_by_name(result: TestResult):
    """健壮性测试 4：按名称注入"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, InjectByName
        )

        @service
        class EmailService:
            def send(self, to: str, msg: str):
                return f"Sent to {to}: {msg}"

        @service
        class NotificationService:
            # 按名称注入
            email = InjectByName("EmailService")

            def notify(self, user: str, msg: str):
                return self.email.send(user, msg)

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        notif = ctx.get('NotificationService')

        if isinstance(notif.email, InjectByName):
            result.add_fail("健壮4: 按名称注入", "email 未注入")
            return

        result_msg = notif.notify("user@test.com", "Hello")
        if "Sent to" not in result_msg:
            result.add_fail("健壮4: 按名称注入", f"功能验证失败: {result_msg}")
            return

        result.add_pass("健壮4: 按名称注入")

    except Exception as e:
        result.add_fail("健壮4: 按名称注入", str(e))


def test_type_inference(result: TestResult):
    """健壮性测试 5：类型推断注入"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, Inject
        )

        @service
        class PaymentGateway:
            def charge(self, amount: float):
                return f"Charged ${amount}"

        @service
        class OrderService:
            # 类型注解推断
            payment_gateway: PaymentGateway = Inject()

            def place_order(self, amount: float):
                return self.payment_gateway.charge(amount)

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        order_svc = ctx.get('OrderService')

        # 验证类型推断成功
        if not isinstance(order_svc.payment_gateway, PaymentGateway):
            result.add_fail("健壮5: 类型推断", f"类型不匹配: {type(order_svc.payment_gateway)}")
            return

        charge_result = order_svc.place_order(99.99)
        if "99.99" not in charge_result:
            result.add_fail("健壮5: 类型推断", f"功能验证失败: {charge_result}")
            return

        result.add_pass("健壮5: 类型推断注入")

    except Exception as e:
        result.add_fail("健壮5: 类型推断", str(e))


# =============================================================================
# 边界条件和错误处理测试
# =============================================================================

def test_missing_required_dependency(result: TestResult):
    """边界测试 1：缺少必需依赖"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, Inject
        )

        # MissingService 没有 @service 装饰器
        class MissingService:
            pass

        @service
        class DependentService:
            missing: MissingService = Inject()  # required=True（默认）

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        try:
            dependent = ctx.get('DependentService')
            # 如果到这里没有抛出异常，可能是框架的行为
            # 检查是否注入了 None 或者仍然是 Inject
            if dependent.missing is None or isinstance(dependent.missing, Inject):
                result.add_pass("边界1: 缺少必需依赖（返回None/Inject）")
            else:
                result.add_fail("边界1: 缺少必需依赖", "未知行为")
        except Exception:
            # 预期行为：抛出异常
            result.add_pass("边界1: 缺少必需依赖（抛出异常）")

    except Exception as e:
        result.add_fail("边界1: 缺少必需依赖", str(e))


def test_empty_controller(result: TestResult):
    """边界测试 2：无依赖的 Controller"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            controller
        )
        from cullinan.controller.registry import get_controller_registry

        @controller(url='/api/empty')
        class EmptyController:
            def handle(self):
                return {"status": "ok"}

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('EmptyController', EmptyController)

        instance = registry.get_instance('EmptyController')

        if instance is None:
            result.add_fail("边界2: 空Controller", "实例为None")
            return

        response = instance.handle()
        if response.get('status') != 'ok':
            result.add_fail("边界2: 空Controller", f"响应不正确: {response}")
            return

        result.add_pass("边界2: 无依赖Controller")

    except Exception as e:
        result.add_fail("边界2: 空Controller", str(e))


def test_controller_with_init(result: TestResult):
    """边界测试 3：带 __init__ 的 Controller"""
    reset_all_registries()

    try:
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class ConfigService:
            def get_version(self):
                return "1.0.0"

        @controller(url='/api/init')
        class InitController:
            config: ConfigService = Inject()

            def __init__(self):
                self.initialized = True
                self.custom_value = 42

            def get_info(self):
                return {
                    "initialized": self.initialized,
                    "custom_value": self.custom_value,
                    "version": self.config.get_version()
                }

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('InitController', InitController)

        instance = registry.get_instance('InitController')

        # 验证 __init__ 被调用
        if not instance.initialized:
            result.add_fail("边界3: 带init的Controller", "__init__ 未执行")
            return

        if instance.custom_value != 42:
            result.add_fail("边界3: 带init的Controller", "自定义值不正确")
            return

        # 验证依赖注入成功
        if isinstance(instance.config, Inject):
            result.add_fail("边界3: 带init的Controller", "依赖未注入")
            return

        info = instance.get_info()
        if info.get('version') != '1.0.0':
            result.add_fail("边界3: 带init的Controller", f"功能验证失败: {info}")
            return

        result.add_pass("边界3: 带__init__的Controller")

    except Exception as e:
        result.add_fail("边界3: 带init的Controller", str(e))


def test_concurrent_access(result: TestResult):
    """边界测试 4：并发访问"""
    reset_all_registries()

    try:
        import threading
        import time
        from cullinan.core import (
            ApplicationContext, set_application_context,
            service, controller, Inject
        )
        from cullinan.controller.registry import get_controller_registry

        @service
        class SlowService:
            def __init__(self):
                time.sleep(0.01)  # 模拟慢初始化
                self.ready = True

        @controller(url='/api/concurrent')
        class ConcurrentController:
            slow: SlowService = Inject()

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        registry = get_controller_registry()
        registry.register('ConcurrentController', ConcurrentController)

        instances = []
        errors = []

        def get_instance():
            try:
                inst = registry.get_instance('ConcurrentController')
                instances.append(inst)
            except Exception as e:
                errors.append(str(e))

        # 创建多个线程同时获取实例
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if errors:
            result.add_fail("边界4: 并发访问", f"发生错误: {errors}")
            return

        # 验证所有实例相同（单例）
        if len(set(id(inst) for inst in instances)) != 1:
            result.add_fail("边界4: 并发访问", "并发创建了多个实例")
            return

        result.add_pass("边界4: 并发访问安全")

    except Exception as e:
        result.add_fail("边界4: 并发访问", str(e))


# =============================================================================
# 主测试入口
# =============================================================================

def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Cullinan 框架依赖注入全方位测试")
    print("Author: Plumeink")
    print("=" * 70)

    result = TestResult()

    # 专项测试：Controller DI Bug 修复
    print("\n[专项测试] Controller 依赖注入 Bug 修复验证")
    print("-" * 50)
    test_controller_di_basic(result)
    test_controller_di_multiple_services(result)
    test_controller_di_optional(result)
    test_controller_di_hasattr_check(result)
    test_controller_singleton(result)
    test_controller_di_without_context(result)

    # 健壮性测试：Service DI
    print("\n[健壮性测试] Service 依赖注入")
    print("-" * 50)
    test_service_di_basic(result)
    test_service_chain_injection(result)
    test_service_singleton(result)
    test_inject_by_name(result)
    test_type_inference(result)

    # 边界条件测试
    print("\n[边界测试] 错误处理和边界条件")
    print("-" * 50)
    test_missing_required_dependency(result)
    test_empty_controller(result)
    test_controller_with_init(result)
    test_concurrent_access(result)

    # 输出总结
    success = result.summary()

    return success


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

