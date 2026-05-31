# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 统一根容器实现。"""

from __future__ import annotations

import asyncio
import inspect
import logging
import threading
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .definition_registry import DefinitionRegistry
from .definitions import Definition, ScopeType
from .exceptions import (
    CircularDependencyError,
    ConditionNotMetError,
    CreationError,
    DependencyNotFoundError,
    DependencyTypeResolutionError,
    LifecycleError,
    RegistryFrozenError,
)
from .diagnostics import (
    format_circular_dependency_error,
    format_missing_dependency_error,
)
from .lifecycle_enhanced import LifecyclePhase
from .scope_manager import ScopeManager

logger = logging.getLogger(__name__)


class ContainerState(Enum):
    """根容器状态。"""

    CREATED = "created"
    REGISTERING = "registering"
    VALIDATING = "validating"
    WARMING_UP = "warming_up"
    ACTIVE = "active"
    DRAINING = "draining"
    CLOSED = "closed"


class ApplicationContext:
    """统一根容器。

    保留历史 ``ApplicationContext`` API，同时内部实现切换为单根容器模型。
    """

    __slots__ = (
        "_definition_registry",
        "_scope_manager",
        "_lock",
        "_resolving_stack",
        "_shutdown_handlers",
        "_lifecycle_instances",
        "_lifecycle_phases",
        "_startup_order",
        "_state",
        "_id",
        "_health_checks",
    )

    def __init__(self, container_id: Optional[str] = None):
        self._definition_registry = DefinitionRegistry()
        self._scope_manager = ScopeManager(root_id=container_id or hex(id(self)))
        self._lock = threading.RLock()
        self._resolving_stack: List[str] = []
        self._shutdown_handlers: List[Any] = []
        self._lifecycle_instances: Dict[str, Any] = {}
        self._lifecycle_phases: Dict[str, LifecyclePhase] = {}
        self._startup_order: List[str] = []
        self._state = ContainerState.CREATED
        self._id = self._scope_manager.root_id
        self._health_checks: List[Any] = []

    # ========================================================================
    # 注册 API
    # ========================================================================

    def register(self, definition: Definition) -> None:
        with self._lock:
            if self._definition_registry.is_frozen:
                raise RegistryFrozenError(
                    f"无法注册 '{definition.name}'：Registry 已冻结（refresh 后禁止修改）"
                )
            if self._state == ContainerState.CREATED:
                self._state = ContainerState.REGISTERING
            self._definition_registry.register(definition)

    def register_all(self, definitions: List[Definition]) -> None:
        for definition in definitions:
            self.register(definition)

    def add_health_check(self, callback) -> None:
        self._health_checks.append(callback)

    # ========================================================================
    # 生命周期 API
    # ========================================================================

    def refresh(self) -> None:
        with self._lock:
            if self._state == ContainerState.ACTIVE:
                logger.warning("ApplicationContext.refresh() 已被调用过，跳过")
                return
            if self._state == ContainerState.CLOSED:
                raise LifecycleError("已关闭的 ApplicationContext 不能再次 refresh")

            if self._state == ContainerState.CREATED:
                self._state = ContainerState.REGISTERING

            logger.info("ApplicationContext.refresh() 开始")
            self._process_pending_registrations()
            self._state = ContainerState.VALIDATING
            self._validate_definitions()
            self._state = ContainerState.WARMING_UP
            self._warm_up()
            self._definition_registry.freeze()
            self._run_health_checks()
            self._state = ContainerState.ACTIVE
            logger.info(
                "ApplicationContext.refresh() 完成，共注册 %s 个 Definition",
                self.definition_count,
            )

    def begin_draining(self) -> None:
        with self._lock:
            if self._state == ContainerState.CLOSED:
                return
            self._state = ContainerState.DRAINING
            self._scope_manager.begin_drain()

    def shutdown(self, timeout: float = 30.0) -> None:
        with self._lock:
            if self._state == ContainerState.CLOSED:
                return
            self.begin_draining()

        self._await_request_drained(timeout)
        self._execute_lifecycle_shutdown()

        for handler in self._shutdown_handlers:
            try:
                result = handler()
                if inspect.iscoroutine(result):
                    self._run_coroutine(result)
            except Exception as exc:
                logger.error("Shutdown handler 执行失败: %s", exc)

        self._scope_manager.clear_all()
        self._lifecycle_instances.clear()
        self._lifecycle_phases.clear()
        self._startup_order.clear()
        self._state = ContainerState.CLOSED
        logger.info("ApplicationContext.shutdown() 完成")

    def add_shutdown_handler(self, handler) -> None:
        self._shutdown_handlers.append(handler)

    # ========================================================================
    # 解析 API
    # ========================================================================

    def get(self, name: str) -> Any:
        definition = self._definition_registry.get(name)
        if definition is None:
            raise DependencyNotFoundError(
                message=format_missing_dependency_error(
                    dependency_name=name,
                    available_sources=self.list_definitions(),
                ),
                dependency_name=name,
                candidate_sources=[
                    {"source": definition_name, "reason": "name_mismatch"}
                    for definition_name in self.list_definitions()
                ],
            )
        return self._resolve(definition)

    def try_get(self, name: str) -> Optional[Any]:
        definition = self._definition_registry.get(name)
        if definition is None:
            return None
        if not definition.check_conditions(self):
            logger.debug("try_get('%s'): 条件不满足，返回 None", name)
            return None
        return self._resolve(definition)

    def has(self, name: str) -> bool:
        return self._definition_registry.has(name)

    def get_definition(self, name: str) -> Optional[Definition]:
        return self._definition_registry.get(name)

    def list_definitions(self) -> List[str]:
        return self._definition_registry.list_names()

    # ========================================================================
    # Request Context 代理
    # ========================================================================

    def enter_request_context(self):
        if self._state != ContainerState.ACTIVE:
            raise LifecycleError(
                f"容器状态为 {self._state.value}，当前不接受新的请求作用域"
            )
        return self._scope_manager.enter_request_context()

    def exit_request_context(self) -> None:
        self._scope_manager.exit_request_context()

    def is_request_active(self) -> bool:
        return self._scope_manager.is_request_active()

    # ========================================================================
    # 状态查询
    # ========================================================================

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> ContainerState:
        return self._state

    @property
    def is_frozen(self) -> bool:
        return self._definition_registry.is_frozen

    @property
    def is_refreshed(self) -> bool:
        return self._state in {
            ContainerState.WARMING_UP,
            ContainerState.ACTIVE,
            ContainerState.DRAINING,
            ContainerState.CLOSED,
        }

    @property
    def definition_count(self) -> int:
        return self._definition_registry.count

    @property
    def active_request_count(self) -> int:
        return self._scope_manager.active_request_count

    # ========================================================================
    # 内部方法
    # ========================================================================

    def _resolve(self, definition: Definition) -> Any:
        name = definition.name
        if name in self._resolving_stack:
            cycle_start = self._resolving_stack.index(name)
            chain = self._resolving_stack[cycle_start:] + [name]
            raise CircularDependencyError(
                message=format_circular_dependency_error(chain),
                dependency_chain=chain,
                dependency_name=name,
            )

        if not definition.check_conditions(self):
            raise ConditionNotMetError(
                message=f"依赖 '{name}' 的条件不满足",
                dependency_name=name,
                failed_conditions=[f"condition_{index}" for index, _ in enumerate(definition.conditions)],
            )

        if (
            definition.scope == ScopeType.REQUEST
            and any(
                self._definition_registry.get(parent_name)
                and self._definition_registry.get(parent_name).scope == ScopeType.SINGLETON
                for parent_name in self._resolving_stack
            )
        ):
            raise CreationError(
                message=f"singleton 组件不能直接依赖 request 作用域组件 '{name}'",
                dependency_name=name,
            )

        self._resolving_stack.append(name)
        try:
            return self._scope_manager.get(
                scope_type=definition.scope,
                name=name,
                factory=lambda: self._create_instance(definition),
            )
        finally:
            self._resolving_stack.pop()

    def _create_instance(self, definition: Definition) -> Any:
        try:
            instance = definition.factory(self)
            if instance is None:
                raise CreationError(
                    message=f"依赖 '{definition.name}' 的 factory 返回了 None",
                    dependency_name=definition.name,
                )
            return instance
        except (CreationError, CircularDependencyError, ConditionNotMetError):
            raise
        except Exception as exc:
            raise CreationError(
                message=f"创建依赖 '{definition.name}' 失败: {exc}",
                dependency_name=definition.name,
                cause=exc,
            ) from exc

    def _validate_definitions(self) -> None:
        self._validate_injection_contracts()
        self._validate_dependencies()
        self._validate_scope_constraints()

    def _validate_injection_contracts(self) -> None:
        from .decorators import Inject, InjectByName, Lazy, get_injection_markers

        for definition in self._definition_registry.values():
            target_cls = definition.type_
            if target_cls is None or not inspect.isclass(target_cls):
                continue

            markers = get_injection_markers(target_cls)
            if not markers:
                continue

            type_hints, raw_annotations, type_hint_error = self._get_class_type_hints(target_cls)

            for attr_name, marker in markers.items():
                dep_name = self._resolve_marker_dependency_name(
                    owner_cls=target_cls,
                    attr_name=attr_name,
                    marker=marker,
                    type_hints=type_hints,
                    raw_annotations=raw_annotations,
                    type_hint_error=type_hint_error,
                )
                required = getattr(marker, "required", True)
                if required and not self._definition_registry.has(dep_name):
                    raise DependencyNotFoundError(
                        message=(
                            f"组件 '{definition.name}' 的依赖字段 '{attr_name}' 需要组件 "
                            f"'{dep_name}'，但该组件未注册"
                        ),
                        dependency_name=dep_name,
                        injection_point=f"{target_cls.__module__}.{target_cls.__name__}.{attr_name}",
                        candidate_sources=[
                            {"source": candidate, "reason": "name_mismatch"}
                            for candidate in self.list_definitions()
                        ],
                    )

    def _validate_dependencies(self) -> None:
        visited: Set[str] = set()
        path: List[str] = []

        def visit(name: str) -> None:
            if name in path:
                cycle_start = path.index(name)
                chain = path[cycle_start:] + [name]
                raise CircularDependencyError(
                    message=format_circular_dependency_error(chain),
                    dependency_chain=chain,
                    dependency_name=name,
                )
            if name in visited:
                return

            definition = self._definition_registry.get(name)
            if definition is None:
                return

            path.append(name)
            for dep_name in definition.dependencies:
                if not self._definition_registry.has(dep_name):
                    raise DependencyNotFoundError(
                        message=f"依赖 '{definition.name}' 缺少被声明的组件 '{dep_name}'",
                        dependency_name=dep_name,
                        candidate_sources=[],
                    )
                visit(dep_name)
            path.pop()
            visited.add(name)

        for name in self._definition_registry.list_names():
            visit(name)

    def _validate_scope_constraints(self) -> None:
        for definition in self._definition_registry.values():
            if definition.scope != ScopeType.SINGLETON:
                continue
            for dep_name in definition.dependencies:
                dependency = self._definition_registry.get(dep_name)
                if dependency and dependency.scope == ScopeType.REQUEST:
                    raise LifecycleError(
                        f"singleton 组件 '{definition.name}' 不能直接依赖 request 组件 '{dep_name}'"
                    )

    def _warm_up(self) -> None:
        for definition_name in self._ordered_definition_names(self._warmup_candidates()):
            definition = self._definition_registry.get(definition_name)
            if definition is None:
                continue
            self._resolve(definition)
        self._execute_lifecycle_startup()

    def _warmup_candidates(self) -> List[str]:
        candidates: List[str] = []
        for definition in self._definition_registry.values():
            if definition.scope != ScopeType.SINGLETON:
                continue
            if definition.eager or definition.healthcheck is not None or self._definition_has_lifecycle(definition):
                candidates.append(definition.name)
        return candidates

    def _ordered_definition_names(self, names: List[str]) -> List[str]:
        selected = set(names)
        ordered: List[str] = []
        temporary: Set[str] = set()
        permanent: Set[str] = set()

        def visit(name: str) -> None:
            if name in permanent:
                return
            if name in temporary:
                cycle = list(temporary) + [name]
                raise CircularDependencyError(
                    message=format_circular_dependency_error(cycle),
                    dependency_chain=cycle,
                    dependency_name=name,
                )
            temporary.add(name)
            definition = self._definition_registry.get(name)
            if definition is not None:
                for dep_name in definition.dependencies:
                    if dep_name in selected:
                        visit(dep_name)
            temporary.remove(name)
            permanent.add(name)
            ordered.append(name)

        for name in names:
            visit(name)
        return ordered

    def _process_pending_registrations(self) -> None:
        from .pending import PendingRegistry

        pending = PendingRegistry.get_instance()
        registrations = pending.drain()
        if not registrations:
            pending.freeze()
            return

        for registration in registrations:
            try:
                scope = ScopeType[registration.scope.upper()]
            except KeyError:
                logger.warning("未知 scope '%s'，使用 SINGLETON", registration.scope)
                scope = ScopeType.SINGLETON

            cls = registration.cls
            definition = Definition(
                name=registration.name,
                type_=cls,
                scope=scope,
                factory=self._build_class_factory(cls),
                source=registration.get_source_location(),
                dependencies=registration.dependencies or (),
                conditions=registration.conditions,
                tags={"component_type": registration.component_type.value},
            )

            if self._definition_registry.has(registration.name):
                raise ValueError(f"Definition '{registration.name}' 已存在，禁止重复注册")

            self._definition_registry.register(definition)

            if registration.component_type.value == "controller":
                self._register_controller_routes(cls, registration.url_prefix or "")

        pending.freeze()

    def _build_class_factory(self, target_cls):
        def factory(ctx: "ApplicationContext") -> object:
            return ctx._create_class_instance(target_cls)

        return factory

    @staticmethod
    def _unwrap_route_func(method_func):
        original = getattr(method_func, "__cullinan_original_func__", None)
        if original is not None:
            return original
        wrapped = getattr(method_func, "__wrapped__", None)
        if wrapped is not None:
            return wrapped
        return method_func

    def _register_controller_routes(self, cls: type, url_prefix: str) -> None:
        try:
            from cullinan.controller.core import _controller_decoration_context
            from cullinan.controller.registry import get_controller_registry
            from cullinan.gateway import get_router
            from cullinan.handler import get_handler_registry

            gateway_router = get_router()
            handler_registry = get_handler_registry()
            func_list = _controller_decoration_context.get() or []
            _controller_decoration_context.set([])

            if not func_list:
                for attr_name in dir(cls):
                    if attr_name.startswith("_"):
                        continue
                    attr = getattr(cls, attr_name, None)
                    if not callable(attr):
                        continue
                    route_url = getattr(attr, "__cullinan_url__", None)
                    route_type = getattr(attr, "__cullinan_method__", None)
                    if route_url is None or route_type is None:
                        inner = getattr(attr, "__cullinan_original_func__", None) or getattr(attr, "__wrapped__", None)
                        if inner is not None:
                            route_url = getattr(inner, "__cullinan_url__", route_url)
                            route_type = getattr(inner, "__cullinan_method__", route_type)
                    if route_url is not None and route_type is not None:
                        func_list.append((route_url, attr, route_type))

            if not func_list:
                return

            controller_registry = get_controller_registry()
            controller_name = cls.__name__
            controller_registry.register(controller_name, cls, url_prefix=url_prefix)

            for method_url, method_func, http_method in func_list:
                original_func = self._unwrap_route_func(method_func)
                original_url = getattr(original_func, "__cullinan_url__", None)
                full_url = url_prefix + (original_url if original_url is not None else method_url)

                controller_registry.register_method(
                    controller_name,
                    method_url,
                    http_method,
                    method_func,
                )

                gateway_router.add_route(
                    method=http_method.upper(),
                    path=full_url,
                    handler=original_func,
                    controller_cls=cls,
                    controller_method_name=getattr(original_func, "__name__", ""),
                )
                handler_registry.register(full_url, original_func)
        except Exception as exc:
            logger.warning("注册 Controller %s 路由失败: %s", cls.__name__, exc)

    def _create_class_instance(self, cls: type) -> object:
        from .decorators import Inject, InjectByName, Lazy, get_injection_markers

        instance = cls()
        markers = get_injection_markers(cls)
        type_hints, raw_annotations, type_hint_error = self._get_class_type_hints(cls)

        for attr_name, marker in markers.items():
            if isinstance(marker, Lazy):
                dep_name = self._resolve_marker_dependency_name(
                    owner_cls=cls,
                    attr_name=attr_name,
                    marker=marker,
                    type_hints=type_hints,
                    raw_annotations=raw_annotations,
                    type_hint_error=type_hint_error,
                )
                setattr(instance, attr_name, _LazyProxy(self, dep_name))
            elif isinstance(marker, InjectByName):
                dep_name = self._resolve_marker_dependency_name(
                    owner_cls=cls,
                    attr_name=attr_name,
                    marker=marker,
                    type_hints=type_hints,
                    raw_annotations=raw_annotations,
                    type_hint_error=type_hint_error,
                )
                dep_instance = self.get(dep_name) if marker.required else self.try_get(dep_name)
                setattr(instance, attr_name, dep_instance)
            elif isinstance(marker, Inject):
                dep_name = self._resolve_marker_dependency_name(
                    owner_cls=cls,
                    attr_name=attr_name,
                    marker=marker,
                    type_hints=type_hints,
                    raw_annotations=raw_annotations,
                    type_hint_error=type_hint_error,
                )
                dep_instance = self.get(dep_name) if marker.required else self.try_get(dep_name)
                setattr(instance, attr_name, dep_instance)

        return instance

    @staticmethod
    def _get_class_type_hints(cls: type):
        import typing

        raw_annotations = dict(getattr(cls, "__annotations__", {}) or {})
        try:
            return typing.get_type_hints(cls), raw_annotations, None
        except Exception as exc:
            return {}, raw_annotations, exc

    @staticmethod
    def _describe_dependency_target(type_hint, raw_annotation) -> Optional[str]:
        import typing

        if type_hint is not None:
            if hasattr(type_hint, "__name__"):
                return type_hint.__name__
            origin = typing.get_origin(type_hint)
            if origin is typing.Union:
                non_none_args = [
                    arg for arg in typing.get_args(type_hint) if arg is not type(None)
                ]
                if len(non_none_args) == 1:
                    return ApplicationContext._describe_dependency_target(non_none_args[0], None)
            if origin is typing.Annotated:
                annotated_args = typing.get_args(type_hint)
                if annotated_args:
                    return ApplicationContext._describe_dependency_target(annotated_args[0], None)

        if isinstance(raw_annotation, str):
            return raw_annotation
        if hasattr(raw_annotation, "__forward_arg__"):
            return raw_annotation.__forward_arg__
        if hasattr(raw_annotation, "__name__"):
            return raw_annotation.__name__
        if raw_annotation is not None:
            return str(raw_annotation)
        return None

    def _resolve_marker_dependency_name(
        self,
        *,
        owner_cls: type,
        attr_name: str,
        marker,
        type_hints: Dict[str, Any],
        raw_annotations: Dict[str, Any],
        type_hint_error: Optional[Exception],
    ) -> str:
        from .decorators import InjectByName

        if isinstance(marker, InjectByName):
            return marker.name or self._infer_dependency_name(attr_name, None)

        explicit_name = getattr(marker, "name", None)
        if explicit_name:
            return explicit_name

        type_hint = type_hints.get(attr_name)
        raw_annotation = raw_annotations.get(attr_name)
        expected_type_name = self._describe_dependency_target(type_hint, raw_annotation)
        if expected_type_name and type_hint is not None:
            return expected_type_name

        fallback_candidate = self._infer_dependency_name(attr_name, None)
        message = (
            f"组件 '{owner_cls.__name__}' 的依赖字段 '{attr_name}' 类型解析失败；"
            f"期望类型: '{expected_type_name or '<unknown>'}'。"
            f"检测到属性名回退候选 '{attr_name} -> {fallback_candidate}'，该回退已被禁止。"
        )
        if type_hint_error is not None:
            message = (
                f"{message} 原始异常: {type(type_hint_error).__name__}: {type_hint_error}"
            )

        raise DependencyTypeResolutionError(
            message=message,
            dependency_name=expected_type_name or fallback_candidate,
            injection_point=f"{owner_cls.__module__}.{owner_cls.__name__}.{attr_name}",
            expected_type_name=expected_type_name,
            fallback_candidate=fallback_candidate,
            candidate_sources=[
                {"source": fallback_candidate, "reason": "forbidden_attribute_name_fallback"}
            ],
            cause=type_hint_error,
        )

    @staticmethod
    def _infer_dependency_name(attr_name: str, type_hint) -> str:
        import typing

        if type_hint and hasattr(type_hint, "__name__"):
            return type_hint.__name__
        if type_hint:
            origin = typing.get_origin(type_hint)
            if origin is typing.Union:
                non_none_args = [
                    arg for arg in typing.get_args(type_hint) if arg is not type(None)
                ]
                if len(non_none_args) == 1 and hasattr(non_none_args[0], "__name__"):
                    return non_none_args[0].__name__
            if origin is typing.Annotated:
                annotated_args = typing.get_args(type_hint)
                if annotated_args and hasattr(annotated_args[0], "__name__"):
                    return annotated_args[0].__name__
        parts = attr_name.split("_")
        return "".join(part.capitalize() for part in parts)

    def _definition_has_lifecycle(self, definition: Definition) -> bool:
        target_cls = definition.type_
        if target_cls is None:
            return False
        lifecycle_methods = (
            "on_post_construct",
            "on_post_construct_async",
            "on_startup",
            "on_startup_async",
            "on_shutdown",
            "on_shutdown_async",
            "on_pre_destroy",
            "on_pre_destroy_async",
        )
        for method_name in lifecycle_methods:
            if self._is_class_method_overridden(target_cls, method_name):
                return True
        return False

    @staticmethod
    def _is_class_method_overridden(target_cls: type, method_name: str) -> bool:
        for cls in target_cls.__mro__:
            if method_name not in cls.__dict__:
                continue
            if cls.__name__ in ("LifecycleAware", "SmartLifecycle", "object"):
                return False
            return True
        return False

    def _execute_lifecycle_startup(self) -> None:
        instances_with_phase = []
        for definition_name in self._ordered_definition_names(self._warmup_candidates()):
            definition = self._definition_registry.get(definition_name)
            if definition is None or definition.scope != ScopeType.SINGLETON:
                continue
            if not self._scope_manager.has(ScopeType.SINGLETON, definition_name):
                continue
            instance = self._scope_manager.get(
                scope_type=ScopeType.SINGLETON,
                name=definition_name,
                factory=lambda: self._create_instance(definition),
            )
            if not self._instance_has_lifecycle(instance):
                continue
            phase = 0
            if hasattr(instance, "get_phase") and callable(getattr(instance, "get_phase")):
                try:
                    phase = instance.get_phase()
                except Exception:
                    phase = 0
            instances_with_phase.append((definition_name, instance, phase))

        instances_with_phase.sort(key=lambda item: item[2])
        self._startup_order = [name for name, _, _ in instances_with_phase]

        for name, instance, _ in instances_with_phase:
            self._lifecycle_instances[name] = instance
            self._lifecycle_phases[name] = LifecyclePhase.POST_CONSTRUCT
            self._call_lifecycle_method(name, instance, "on_post_construct", "on_post_construct_async")

        for name, instance, _ in instances_with_phase:
            self._lifecycle_phases[name] = LifecyclePhase.STARTING
            self._call_lifecycle_method(name, instance, "on_startup", "on_startup_async")
            self._lifecycle_phases[name] = LifecyclePhase.RUNNING

    def _execute_lifecycle_shutdown(self) -> None:
        shutdown_order = list(reversed(self._startup_order))
        for name in shutdown_order:
            instance = self._lifecycle_instances.get(name)
            if instance is None:
                continue
            self._lifecycle_phases[name] = LifecyclePhase.STOPPING
            self._call_lifecycle_method(name, instance, "on_shutdown", "on_shutdown_async")

        for name in shutdown_order:
            instance = self._lifecycle_instances.get(name)
            if instance is None:
                continue
            self._lifecycle_phases[name] = LifecyclePhase.PRE_DESTROY
            self._call_lifecycle_method(name, instance, "on_pre_destroy", "on_pre_destroy_async")
            self._lifecycle_phases[name] = LifecyclePhase.DESTROYED

    def _call_lifecycle_method(self, name: str, instance: Any, sync_method: str, async_method: str) -> None:
        async_func = getattr(instance, async_method, None)
        if async_func and callable(async_func) and self._is_user_defined_method(instance, async_method):
            try:
                self._run_coroutine(async_func())
            except Exception as exc:
                logger.error("生命周期方法 %s.%s 执行失败: %s", name, async_method, exc)

        sync_func = getattr(instance, sync_method, None)
        if sync_func and callable(sync_func) and self._is_user_defined_method(instance, sync_method):
            try:
                result = sync_func()
                if inspect.iscoroutine(result):
                    self._run_coroutine(result)
            except Exception as exc:
                logger.error("生命周期方法 %s.%s 执行失败: %s", name, sync_method, exc)

    def _is_user_defined_method(self, instance: Any, method_name: str) -> bool:
        return self._is_class_method_overridden(type(instance), method_name)

    @staticmethod
    def _instance_has_lifecycle(instance: Any) -> bool:
        for method_name in (
            "on_post_construct",
            "on_post_construct_async",
            "on_startup",
            "on_startup_async",
            "on_shutdown",
            "on_shutdown_async",
            "on_pre_destroy",
            "on_pre_destroy_async",
        ):
            method = getattr(instance, method_name, None)
            if method and callable(method):
                if type(instance).__name__ in ("LifecycleAware", "SmartLifecycle"):
                    continue
                return True
        return False

    @staticmethod
    def _run_coroutine(coro) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(coro)
            else:
                loop.run_until_complete(coro)
        except RuntimeError:
            asyncio.run(coro)

    def _await_request_drained(self, timeout: float) -> None:
        deadline = time.monotonic() + max(timeout, 0)
        while self.active_request_count > 0:
            if time.monotonic() >= deadline:
                logger.warning(
                    "等待请求作用域清退超时，root=%s remaining=%s",
                    self.id,
                    self.active_request_count,
                )
                break
            time.sleep(0.01)

    def _run_health_checks(self) -> None:
        for definition in self._definition_registry.values():
            callback = definition.healthcheck
            if callback is None:
                continue
            instance = self.get(definition.name)
            result = callback(self, instance)
            if inspect.iscoroutine(result):
                result = asyncio.run(result)
            if result is False:
                raise LifecycleError(f"组件 '{definition.name}' 健康检查失败")

        for callback in self._health_checks:
            result = callback(self)
            if inspect.iscoroutine(result):
                result = asyncio.run(result)
            if result is False:
                raise LifecycleError("容器健康检查失败")

    def get_lifecycle_phase(self, name: str) -> Optional[LifecyclePhase]:
        return self._lifecycle_phases.get(name)

    def is_component_running(self, name: str) -> bool:
        return self._lifecycle_phases.get(name) == LifecyclePhase.RUNNING


class _LazyProxy:
    __slots__ = ("_ctx", "_dep_name", "_resolved", "_value")

    def __init__(self, ctx: ApplicationContext, dep_name: str):
        self._ctx = ctx
        self._dep_name = dep_name
        self._resolved = False
        self._value = None

    def _resolve(self):
        if not self._resolved:
            self._value = self._ctx.get(self._dep_name)
            self._resolved = True
        return self._value

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)


__all__ = ["ApplicationContext", "ContainerState"]
