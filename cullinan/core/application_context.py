# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 统一根容器实现。"""

from __future__ import annotations

import ast
import asyncio
import inspect
import logging
import threading
import time
import types
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

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
from .injection_types import Provider
from .lifecycle_enhanced import LifecyclePhase
from .semantic_rules import (
    ComponentDiscoveryWarning,
    InjectionSemanticWarning,
    format_semantic_message,
    warn_semantic_once,
)
from .scope_manager import ScopeManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _InjectionTarget:
    display_name: str
    lookup_names: Tuple[str, ...]
    runtime_type: Optional[type] = None


@dataclass(frozen=True)
class _NormalizedInjectionAnnotation:
    kind: str
    annotation_repr: str
    targets: Tuple[_InjectionTarget, ...]
    optional: bool = False
    collection_kind: Optional[str] = None


@dataclass(frozen=True)
class _ResolvedInjectionBinding:
    kind: str
    annotation_repr: str
    target_labels: Tuple[str, ...]
    required: bool
    candidate_names: Tuple[str, ...] = ()
    collection_kind: Optional[str] = None


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
                    format_semantic_message(
                        "refresh-freeze",
                        f"组件 '{definition.name}' 试图在 refresh() 之后继续注册。",
                        "把所有结构性注册放到应用启动与 refresh() 之前完成。",
                    )
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
                raise LifecycleError(
                    format_semantic_message(
                        "refresh-freeze",
                        "已关闭的 ApplicationContext 不能再次 refresh().",
                        "如需重建应用，请创建新的 ApplicationContext 实例。",
                    )
                )

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
                message=format_semantic_message(
                    "lifecycle-request-scope",
                    f"singleton 组件解析到了 request 作用域组件 '{name}'。",
                    "改为延迟在 request 上下文内获取，或调整两者的作用域关系。",
                ),
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
        from .decorators import get_injection_markers

        for definition in self._definition_registry.values():
            target_cls = definition.type_
            if target_cls is None or not inspect.isclass(target_cls):
                continue

            markers = get_injection_markers(target_cls)
            if not markers:
                continue

            type_hints, raw_annotations, type_hint_error = self._get_class_type_hints(target_cls)

            for attr_name, marker in markers.items():
                self._resolve_marker_binding(
                    owner_cls=target_cls,
                    attr_name=attr_name,
                    marker=marker,
                    type_hints=type_hints,
                    raw_annotations=raw_annotations,
                    type_hint_error=type_hint_error,
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
                        message=format_semantic_message(
                            "inject-unique-binding",
                            f"组件 '{definition.name}' 声明依赖了未注册的组件 '{dep_name}'。",
                            "检查装饰器是否已执行、模块是否在 refresh() 前导入，以及依赖名称是否正确。",
                        ),
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
                        format_semantic_message(
                            "lifecycle-request-scope",
                            f"singleton 组件 '{definition.name}' 直接依赖了 request 组件 '{dep_name}'。",
                            "改为在 request 上下文内解析该依赖，或调整组件作用域。",
                        )
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

            if not registration.is_top_level:
                warn_semantic_once(
                    key=(
                        f"component-local:{registration.source_module}:{registration.source_qualname}:{registration.name}"
                    ),
                    rule_key="component-top-level",
                    problem=(
                        f"组件 '{registration.name}' 定义在局部作用域 ({registration.source_qualname})。"
                        "这类组件只有在运行到对应代码块时才会注册。"
                    ),
                    guidance=(
                        "将组件移动到模块顶层；如果必须动态创建，请不要依赖自动扫描与自动装配的稳定保证。"
                        "需要更强归属与热插拔语义时，请用 @module 明确边界。"
                    ),
                    category=ComponentDiscoveryWarning,
                    stacklevel=3,
                )

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
        from .decorators import Lazy, get_injection_markers

        instance = cls()
        markers = get_injection_markers(cls)
        type_hints, raw_annotations, type_hint_error = self._get_class_type_hints(cls)

        for attr_name, marker in markers.items():
            binding = self._resolve_marker_binding(
                owner_cls=cls,
                attr_name=attr_name,
                marker=marker,
                type_hints=type_hints,
                raw_annotations=raw_annotations,
                type_hint_error=type_hint_error,
            )
            if isinstance(marker, Lazy):
                setattr(instance, attr_name, _LazyProxy(lambda binding=binding: self._materialize_binding(binding)))
                continue
            setattr(instance, attr_name, self._materialize_binding(binding))

        return instance

    @staticmethod
    def _get_class_type_hints(cls: type):
        import typing

        try:
            raw_annotations = dict(inspect.get_annotations(cls, eval_str=False))
        except Exception:
            raw_annotations = dict(getattr(cls, "__annotations__", {}) or {})
        try:
            return typing.get_type_hints(cls, include_extras=True), raw_annotations, None
        except Exception as exc:
            return {}, raw_annotations, exc

    @staticmethod
    def _format_annotation_repr(annotation: Any) -> str:
        if isinstance(annotation, str):
            return annotation
        if hasattr(annotation, "__forward_arg__"):
            return str(annotation.__forward_arg__)
        if annotation is None:
            return "<unknown>"
        if hasattr(annotation, "__module__") and hasattr(annotation, "__qualname__"):
            return f"{annotation.__module__}.{annotation.__qualname__}"
        return repr(annotation)

    @staticmethod
    def _annotation_expr(node: ast.AST) -> str:
        return ast.unparse(node) if hasattr(ast, "unparse") else node.__class__.__name__

    @staticmethod
    def _flatten_union_ast(node: ast.AST) -> List[ast.AST]:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return (
                ApplicationContext._flatten_union_ast(node.left)
                + ApplicationContext._flatten_union_ast(node.right)
            )
        return [node]

    @staticmethod
    def _extract_ast_name(node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = ApplicationContext._extract_ast_name(node.value)
            if parent:
                return f"{parent}.{node.attr}"
            return node.attr
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    @staticmethod
    def _make_target_from_name(name: str) -> _InjectionTarget:
        lookup_names = []
        if name:
            lookup_names.append(name)
            if "." in name:
                lookup_names.append(name.rsplit(".", 1)[-1])
        deduped = []
        for item in lookup_names:
            if item not in deduped:
                deduped.append(item)
        return _InjectionTarget(
            display_name=name,
            lookup_names=tuple(deduped),
        )

    @staticmethod
    def _make_target_from_type(type_hint: type) -> _InjectionTarget:
        lookup_names = [type_hint.__name__]
        qualified_name = f"{type_hint.__module__}.{type_hint.__qualname__}"
        if qualified_name not in lookup_names:
            lookup_names.append(qualified_name)
        if type_hint.__qualname__ not in lookup_names:
            lookup_names.append(type_hint.__qualname__)
        return _InjectionTarget(
            display_name=type_hint.__name__,
            lookup_names=tuple(lookup_names),
            runtime_type=type_hint,
        )

    @staticmethod
    def _make_single_annotation(target: _InjectionTarget, annotation_repr: str, *, optional: bool = False) -> _NormalizedInjectionAnnotation:
        return _NormalizedInjectionAnnotation(
            kind="single",
            annotation_repr=annotation_repr,
            targets=(target,),
            optional=optional,
        )

    @staticmethod
    def _parse_runtime_annotation(annotation: Any) -> _NormalizedInjectionAnnotation:
        import typing

        annotation_repr = ApplicationContext._format_annotation_repr(annotation)
        if isinstance(annotation, str):
            return ApplicationContext._parse_string_annotation(annotation)
        if hasattr(annotation, "__forward_arg__"):
            return ApplicationContext._parse_string_annotation(annotation.__forward_arg__)
        if inspect.isclass(annotation):
            return ApplicationContext._make_single_annotation(
                ApplicationContext._make_target_from_type(annotation),
                annotation_repr,
            )

        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        if origin is typing.Annotated:
            if not args:
                raise ValueError("Annotated 缺少内部类型")
            return ApplicationContext._parse_runtime_annotation(args[0])
        if origin is typing.Final:
            if not args:
                raise ValueError("Final 缺少内部类型")
            return ApplicationContext._parse_runtime_annotation(args[0])
        if origin in (typing.Union, types.UnionType):
            non_none_args = [arg for arg in args if arg is not type(None)]
            has_none = len(non_none_args) != len(args)
            if has_none and len(non_none_args) == 1:
                normalized = ApplicationContext._parse_runtime_annotation(non_none_args[0])
                if normalized.kind != "single":
                    raise ValueError("Optional 仅支持包装单实例依赖")
                return _NormalizedInjectionAnnotation(
                    kind="single",
                    annotation_repr=annotation_repr,
                    targets=normalized.targets,
                    optional=True,
                )
            targets: List[_InjectionTarget] = []
            for arg in args:
                normalized = ApplicationContext._parse_runtime_annotation(arg)
                if normalized.kind != "single" or normalized.optional:
                    raise ValueError("Union 仅支持多个单实例候选")
                targets.extend(normalized.targets)
            return _NormalizedInjectionAnnotation(
                kind="union",
                annotation_repr=annotation_repr,
                targets=tuple(targets),
            )
        if origin is Provider:
            if len(args) != 1:
                raise ValueError("Provider[T] 必须且只能包含一个类型参数")
            normalized = ApplicationContext._parse_runtime_annotation(args[0])
            if normalized.kind != "single" or normalized.optional:
                raise ValueError("Provider[T] 仅支持单实例依赖")
            return _NormalizedInjectionAnnotation(
                kind="provider",
                annotation_repr=annotation_repr,
                targets=normalized.targets,
            )
        if origin in (list, set, tuple):
            if origin is tuple:
                if len(args) != 2 or args[1] is not Ellipsis:
                    raise ValueError("tuple 注入仅支持 tuple[T, ...] 形式")
                element_annotation = args[0]
                collection_kind = "tuple"
            else:
                if len(args) != 1:
                    raise ValueError("集合注入必须且只能包含一个元素类型")
                element_annotation = args[0]
                collection_kind = origin.__name__
            normalized = ApplicationContext._parse_runtime_annotation(element_annotation)
            if normalized.kind != "single" or normalized.optional:
                raise ValueError("集合注入仅支持单实例元素类型")
            return _NormalizedInjectionAnnotation(
                kind="collection",
                annotation_repr=annotation_repr,
                targets=normalized.targets,
                collection_kind=collection_kind,
            )

        raise ValueError(f"不支持的注解类型: {annotation_repr}")

    @staticmethod
    def _parse_string_annotation(annotation_text: str) -> _NormalizedInjectionAnnotation:
        try:
            expr = ast.parse(annotation_text, mode="eval").body
        except SyntaxError as exc:
            raise ValueError(f"无法解析注解表达式 '{annotation_text}'") from exc
        return ApplicationContext._parse_annotation_ast(expr, annotation_text)

    @staticmethod
    def _parse_annotation_ast(node: ast.AST, annotation_repr: str) -> _NormalizedInjectionAnnotation:
        base_name = ApplicationContext._extract_ast_name(node)
        if base_name:
            return ApplicationContext._make_single_annotation(
                ApplicationContext._make_target_from_name(base_name),
                annotation_repr,
            )

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            parts = ApplicationContext._flatten_union_ast(node)
            normalized_targets: List[_InjectionTarget] = []
            optional = False
            for part in parts:
                part_name = ApplicationContext._extract_ast_name(part)
                if part_name in {"None", "NoneType"}:
                    optional = True
                    continue
                normalized = ApplicationContext._parse_annotation_ast(part, ApplicationContext._annotation_expr(part))
                if normalized.kind != "single" or normalized.optional:
                    raise ValueError("Union 仅支持多个单实例候选")
                normalized_targets.extend(normalized.targets)
            if optional and len(normalized_targets) == 1:
                return _NormalizedInjectionAnnotation(
                    kind="single",
                    annotation_repr=annotation_repr,
                    targets=tuple(normalized_targets),
                    optional=True,
                )
            return _NormalizedInjectionAnnotation(
                kind="union",
                annotation_repr=annotation_repr,
                targets=tuple(normalized_targets),
            )

        if not isinstance(node, ast.Subscript):
            raise ValueError(f"不支持的注解表达式: {annotation_repr}")

        container_name = ApplicationContext._extract_ast_name(node.value)
        if container_name is None:
            raise ValueError(f"不支持的注解容器: {annotation_repr}")
        container_name = container_name.rsplit(".", 1)[-1]

        if container_name in {"Annotated", "Final"}:
            elements = ApplicationContext._subscript_elements(node.slice)
            if not elements:
                raise ValueError(f"{container_name} 缺少内部类型")
            normalized = ApplicationContext._parse_annotation_ast(elements[0], ApplicationContext._annotation_expr(elements[0]))
            return _NormalizedInjectionAnnotation(
                kind=normalized.kind,
                annotation_repr=annotation_repr,
                targets=normalized.targets,
                optional=normalized.optional,
                collection_kind=normalized.collection_kind,
            )
        if container_name == "Optional":
            elements = ApplicationContext._subscript_elements(node.slice)
            if len(elements) != 1:
                raise ValueError("Optional[T] 必须且只能包含一个类型参数")
            normalized = ApplicationContext._parse_annotation_ast(elements[0], ApplicationContext._annotation_expr(elements[0]))
            if normalized.kind != "single":
                raise ValueError("Optional 仅支持包装单实例依赖")
            return _NormalizedInjectionAnnotation(
                kind="single",
                annotation_repr=annotation_repr,
                targets=normalized.targets,
                optional=True,
            )
        if container_name == "Provider":
            elements = ApplicationContext._subscript_elements(node.slice)
            if len(elements) != 1:
                raise ValueError("Provider[T] 必须且只能包含一个类型参数")
            normalized = ApplicationContext._parse_annotation_ast(elements[0], ApplicationContext._annotation_expr(elements[0]))
            if normalized.kind != "single" or normalized.optional:
                raise ValueError("Provider[T] 仅支持单实例依赖")
            return _NormalizedInjectionAnnotation(
                kind="provider",
                annotation_repr=annotation_repr,
                targets=normalized.targets,
            )
        if container_name in {"list", "set"}:
            elements = ApplicationContext._subscript_elements(node.slice)
            if len(elements) != 1:
                raise ValueError(f"{container_name}[T] 必须且只能包含一个元素类型")
            normalized = ApplicationContext._parse_annotation_ast(elements[0], ApplicationContext._annotation_expr(elements[0]))
            if normalized.kind != "single" or normalized.optional:
                raise ValueError("集合注入仅支持单实例元素类型")
            return _NormalizedInjectionAnnotation(
                kind="collection",
                annotation_repr=annotation_repr,
                targets=normalized.targets,
                collection_kind=container_name,
            )
        if container_name == "tuple":
            elements = ApplicationContext._subscript_elements(node.slice)
            if len(elements) != 2 or not isinstance(elements[1], ast.Constant) or elements[1].value is not Ellipsis:
                raise ValueError("tuple 注入仅支持 tuple[T, ...] 形式")
            normalized = ApplicationContext._parse_annotation_ast(elements[0], ApplicationContext._annotation_expr(elements[0]))
            if normalized.kind != "single" or normalized.optional:
                raise ValueError("集合注入仅支持单实例元素类型")
            return _NormalizedInjectionAnnotation(
                kind="collection",
                annotation_repr=annotation_repr,
                targets=normalized.targets,
                collection_kind="tuple",
            )
        if container_name == "Union":
            elements = ApplicationContext._subscript_elements(node.slice)
            normalized_targets: List[_InjectionTarget] = []
            optional = False
            for element in elements:
                element_name = ApplicationContext._extract_ast_name(element)
                if element_name in {"None", "NoneType"}:
                    optional = True
                    continue
                normalized = ApplicationContext._parse_annotation_ast(element, ApplicationContext._annotation_expr(element))
                if normalized.kind != "single" or normalized.optional:
                    raise ValueError("Union 仅支持多个单实例候选")
                normalized_targets.extend(normalized.targets)
            if optional and len(normalized_targets) == 1:
                return _NormalizedInjectionAnnotation(
                    kind="single",
                    annotation_repr=annotation_repr,
                    targets=tuple(normalized_targets),
                    optional=True,
                )
            return _NormalizedInjectionAnnotation(
                kind="union",
                annotation_repr=annotation_repr,
                targets=tuple(normalized_targets),
            )

        raise ValueError(f"不支持的注解容器: {annotation_repr}")

    @staticmethod
    def _subscript_elements(node: ast.AST) -> List[ast.AST]:
        if isinstance(node, ast.Tuple):
            return list(node.elts)
        return [node]

    def _normalize_marker_annotation(
        self,
        *,
        owner_cls: type,
        attr_name: str,
        type_hints: Dict[str, Any],
        raw_annotations: Dict[str, Any],
        type_hint_error: Optional[Exception],
    ) -> _NormalizedInjectionAnnotation:
        type_hint = type_hints.get(attr_name)
        raw_annotation = raw_annotations.get(attr_name)
        try:
            if type_hint is not None:
                return self._parse_runtime_annotation(type_hint)
            if raw_annotation is not None:
                return self._parse_runtime_annotation(raw_annotation)
        except Exception as exc:
            cause = exc
        else:
            cause = type_hint_error

        message = format_semantic_message(
            "inject-unique-binding",
            (
                f"组件 '{owner_cls.__name__}' 的依赖字段 '{attr_name}' 类型解析失败；"
                f"原始注解: '{self._format_annotation_repr(raw_annotation)}'。"
            ),
            "为 Inject() 提供可稳定解析的类型注解；复杂场景改用 InjectByName('ExplicitName')。",
        )
        if cause is not None:
            message = (
                f"{message} 原始异常: {type(cause).__name__}: {cause}"
            )

        raise DependencyTypeResolutionError(
            message=message,
            dependency_name=attr_name,
            injection_point=f"{owner_cls.__module__}.{owner_cls.__name__}.{attr_name}",
            expected_type_name=self._format_annotation_repr(raw_annotation),
            candidate_sources=[],
            cause=cause,
        )

    def _resolve_marker_binding(
        self,
        *,
        owner_cls: type,
        attr_name: str,
        marker,
        type_hints: Dict[str, Any],
        raw_annotations: Dict[str, Any],
        type_hint_error: Optional[Exception],
    ) -> _ResolvedInjectionBinding:
        from .decorators import InjectByName

        injection_point = f"{owner_cls.__module__}.{owner_cls.__name__}.{attr_name}"
        required = getattr(marker, "required", True)
        explicit_name = getattr(marker, "name", None)

        if isinstance(marker, InjectByName) or explicit_name:
            self._warn_name_based_injection_semantics(
                owner_cls=owner_cls,
                attr_name=attr_name,
                explicit_name=explicit_name,
                raw_annotation=raw_annotations.get(attr_name),
            )
            dependency_name = explicit_name or marker.name or attr_name
            candidate_names = (dependency_name,) if self._definition_registry.has(dependency_name) else ()
            if required and not candidate_names:
                raise DependencyNotFoundError(
                    message=format_semantic_message(
                        "inject-by-name",
                        (
                            f"组件 '{owner_cls.__name__}' 的依赖字段 '{attr_name}' 需要显式组件 "
                            f"'{dependency_name}'，但该组件未注册。"
                        ),
                        "确认 InjectByName() 的名称与注册名一致；必要时改为 Inject() + 明确类型。",
                    ),
                    dependency_name=dependency_name,
                    injection_point=injection_point,
                    candidate_sources=[
                        {"source": candidate, "reason": "name_mismatch"}
                        for candidate in self.list_definitions()
                    ],
                )
            return _ResolvedInjectionBinding(
                kind="single",
                annotation_repr=dependency_name,
                target_labels=(dependency_name,),
                required=required,
                candidate_names=candidate_names,
            )

        normalized = self._normalize_marker_annotation(
            owner_cls=owner_cls,
            attr_name=attr_name,
            type_hints=type_hints,
            raw_annotations=raw_annotations,
            type_hint_error=type_hint_error,
        )
        return self._resolve_normalized_binding(
            normalized=normalized,
            injection_point=injection_point,
            dependency_name=attr_name,
            required=required,
        )

    def _warn_name_based_injection_semantics(
        self,
        *,
        owner_cls: type,
        attr_name: str,
        explicit_name: Optional[str],
        raw_annotation: Any,
    ) -> None:
        point = f"{owner_cls.__module__}.{owner_cls.__name__}.{attr_name}"
        if not explicit_name:
            warn_semantic_once(
                key=f"inject-by-name-implicit:{point}",
                rule_key="inject-by-name",
                problem=(
                    f"注入点 '{point}' 使用了未显式传名的 InjectByName()，当前会回退到属性名 '{attr_name}'。"
                ),
                guidance="推荐改为 InjectByName('ExactComponentName')，避免属性名与注册名漂移。",
                category=InjectionSemanticWarning,
                stacklevel=4,
            )

        if raw_annotation in (None, Any):
            warn_semantic_once(
                key=f"inject-by-name-annotation:{point}",
                rule_key="inject-by-name",
                problem=(
                    f"注入点 '{point}' 使用 InjectByName() 时缺少明确类型注解。"
                ),
                guidance="即使按名称解析，也建议补上准确类型注解以表达语义并帮助静态检查。",
                category=InjectionSemanticWarning,
                stacklevel=4,
            )

    def _resolve_normalized_binding(
        self,
        *,
        normalized: _NormalizedInjectionAnnotation,
        injection_point: str,
        dependency_name: str,
        required: bool,
    ) -> _ResolvedInjectionBinding:
        allow_missing = normalized.optional or not required

        if normalized.kind == "single":
            candidate_name = self._select_single_candidate(
                target=normalized.targets[0],
                injection_point=injection_point,
                dependency_name=dependency_name,
                normalized=normalized,
                allow_missing=allow_missing,
            )
            return _ResolvedInjectionBinding(
                kind="single",
                annotation_repr=normalized.annotation_repr,
                target_labels=tuple(target.display_name for target in normalized.targets),
                required=required,
                candidate_names=(candidate_name,) if candidate_name else (),
            )

        if normalized.kind == "provider":
            candidate_name = self._select_single_candidate(
                target=normalized.targets[0],
                injection_point=injection_point,
                dependency_name=dependency_name,
                normalized=normalized,
                allow_missing=not required,
            )
            return _ResolvedInjectionBinding(
                kind="provider",
                annotation_repr=normalized.annotation_repr,
                target_labels=tuple(target.display_name for target in normalized.targets),
                required=required,
                candidate_names=(candidate_name,) if candidate_name else (),
            )

        if normalized.kind == "collection":
            candidate_names = tuple(
                definition.name for definition in self._find_matching_definitions(normalized.targets[0])
            )
            if required and not candidate_names:
                self._raise_missing_binding(
                    dependency_name=dependency_name,
                    injection_point=injection_point,
                    normalized=normalized,
                )
            return _ResolvedInjectionBinding(
                kind="collection",
                annotation_repr=normalized.annotation_repr,
                target_labels=tuple(target.display_name for target in normalized.targets),
                required=required,
                candidate_names=candidate_names,
                collection_kind=normalized.collection_kind,
            )

        if normalized.kind == "union":
            viable_candidates = []
            ambiguous_targets = []
            for target in normalized.targets:
                matches = self._find_matching_definitions(target)
                if len(matches) > 1:
                    ambiguous_targets.append((target, matches))
                elif len(matches) == 1:
                    viable_candidates.append((target, matches[0]))
            if ambiguous_targets:
                target, matches = ambiguous_targets[0]
                self._raise_ambiguous_binding(
                    dependency_name=dependency_name,
                    injection_point=injection_point,
                    normalized=normalized,
                    candidates=matches,
                    extra_reason=f"联合候选 '{target.display_name}' 匹配到多个组件",
                )
            unique_names = {definition.name for _, definition in viable_candidates}
            if len(unique_names) == 1 and viable_candidates:
                chosen = viable_candidates[0][1].name
                return _ResolvedInjectionBinding(
                    kind="single",
                    annotation_repr=normalized.annotation_repr,
                    target_labels=tuple(target.display_name for target in normalized.targets),
                    required=required,
                    candidate_names=(chosen,),
                )
            if len(unique_names) > 1:
                self._raise_ambiguous_binding(
                    dependency_name=dependency_name,
                    injection_point=injection_point,
                    normalized=normalized,
                    candidates=[definition for _, definition in viable_candidates],
                    extra_reason="Union 中有多个候选同时可绑定",
                )
            if allow_missing:
                return _ResolvedInjectionBinding(
                    kind="single",
                    annotation_repr=normalized.annotation_repr,
                    target_labels=tuple(target.display_name for target in normalized.targets),
                    required=False,
                    candidate_names=(),
                )
            self._raise_missing_binding(
                dependency_name=dependency_name,
                injection_point=injection_point,
                normalized=normalized,
            )

        raise DependencyTypeResolutionError(
            message=format_semantic_message(
                "inject-unique-binding",
                f"注入点 '{injection_point}' 使用了当前不支持的注入语义 '{normalized.kind}'。",
                "改用 InjectByName('ExplicitName')，或将注解收敛为单一、可唯一绑定的类型契约。",
            ),
            dependency_name=dependency_name,
            injection_point=injection_point,
            expected_type_name=normalized.annotation_repr,
            candidate_sources=[],
        )

    def _select_single_candidate(
        self,
        *,
        target: _InjectionTarget,
        injection_point: str,
        dependency_name: str,
        normalized: _NormalizedInjectionAnnotation,
        allow_missing: bool,
    ) -> Optional[str]:
        matches = self._find_matching_definitions(target)
        if len(matches) == 1:
            return matches[0].name
        if not matches and allow_missing:
            return None
        if len(matches) > 1:
            self._raise_ambiguous_binding(
                dependency_name=dependency_name,
                injection_point=injection_point,
                normalized=normalized,
                candidates=matches,
            )
        self._raise_missing_binding(
            dependency_name=dependency_name,
            injection_point=injection_point,
            normalized=normalized,
        )

    def _find_matching_definitions(self, target: _InjectionTarget) -> List[Definition]:
        matches: List[Definition] = []
        for definition in self._definition_registry.values():
            if self._definition_matches_target(definition, target):
                matches.append(definition)
        return matches

    @staticmethod
    def _definition_matches_target(definition: Definition, target: _InjectionTarget) -> bool:
        if target.runtime_type is not None and definition.type_ is not None:
            try:
                if issubclass(definition.type_, target.runtime_type):
                    return True
            except TypeError:
                pass
        if definition.name in target.lookup_names:
            return True
        if definition.type_ is None:
            return False
        for candidate_type in getattr(definition.type_, "__mro__", (definition.type_,)):
            qualified_name = f"{candidate_type.__module__}.{candidate_type.__qualname__}"
            if (
                candidate_type.__name__ in target.lookup_names
                or candidate_type.__qualname__ in target.lookup_names
                or qualified_name in target.lookup_names
            ):
                return True
        return False

    def _raise_missing_binding(
        self,
        *,
        dependency_name: str,
        injection_point: str,
        normalized: _NormalizedInjectionAnnotation,
    ) -> None:
        raise DependencyNotFoundError(
            message=format_semantic_message(
                "inject-unique-binding",
                (
                    f"注入点 '{injection_point}' 无法找到可绑定组件；"
                    f"原始注解: '{normalized.annotation_repr}'，"
                    f"归一化语义: '{self._describe_normalized_kind(normalized)}'。"
                ),
                "确认目标组件已注册并在 refresh() 前完成导入；无法唯一表达时改用 InjectByName('ExplicitName')。",
            ),
            dependency_name=dependency_name,
            injection_point=injection_point,
            candidate_sources=[
                {"source": candidate, "reason": "name_mismatch"}
                for candidate in self.list_definitions()
            ],
        )

    def _raise_ambiguous_binding(
        self,
        *,
        dependency_name: str,
        injection_point: str,
        normalized: _NormalizedInjectionAnnotation,
        candidates: List[Definition],
        extra_reason: Optional[str] = None,
    ) -> None:
        reason = extra_reason or "多个候选同时满足注入条件"
        raise DependencyTypeResolutionError(
            message=format_semantic_message(
                "inject-unique-binding",
                (
                    f"注入点 '{injection_point}' 解析到多个候选；"
                    f"原始注解: '{normalized.annotation_repr}'，"
                    f"归一化语义: '{self._describe_normalized_kind(normalized)}'。"
                    f"{reason}。"
                ),
                "改用 InjectByName('ExplicitName')，或缩小类型范围直到只能绑定一个组件。",
            ),
            dependency_name=dependency_name,
            injection_point=injection_point,
            expected_type_name=normalized.annotation_repr,
            candidate_sources=[
                {"source": definition.name, "reason": "multiple_candidates"}
                for definition in candidates
            ],
        )

    @staticmethod
    def _describe_normalized_kind(normalized: _NormalizedInjectionAnnotation) -> str:
        if normalized.kind == "collection":
            return f"collection[{normalized.collection_kind}]"
        return normalized.kind

    def _materialize_binding(self, binding: _ResolvedInjectionBinding) -> Any:
        if binding.kind == "single":
            if not binding.candidate_names:
                return None
            dependency_name = binding.candidate_names[0]
            return self.get(dependency_name) if binding.required else self.try_get(dependency_name)

        if binding.kind == "provider":
            if not binding.candidate_names:
                return None
            dependency_name = binding.candidate_names[0]
            return Provider(lambda dependency_name=dependency_name: self.get(dependency_name))

        if binding.kind == "collection":
            values = [self.get(name) for name in binding.candidate_names]
            if binding.collection_kind == "set":
                return set(values)
            if binding.collection_kind == "tuple":
                return tuple(values)
            return list(values)

        raise DependencyTypeResolutionError(
            message=format_semantic_message(
                "inject-unique-binding",
                f"内部绑定结果包含未知类型 '{binding.kind}'。",
                "这是框架内部一致性错误，请检查注入绑定归一化流程。",
            ),
            dependency_name=",".join(binding.target_labels),
            candidate_sources=[],
        )

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
    __slots__ = ("_resolver", "_resolved", "_value")

    def __init__(self, resolver: Callable[[], Any]):
        self._resolver = resolver
        self._resolved = False
        self._value = None

    def _resolve(self):
        if not self._resolved:
            self._value = self._resolver()
            self._resolved = True
        return self._value

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)


__all__ = ["ApplicationContext", "ContainerState"]
