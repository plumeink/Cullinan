# Core 概念草稿（基于实现，不依赖注释）

说明：本草稿基于 `cullinan/core` 源码实现文件结构与函数/类命名推断职责。开发者需核对并补充精确行号与细节。

目录：
- 关键类/模块清单与职责
- IoC/DI 流程（对象构造 → 注入 → 解析）
- 生命周期钩子与增强点
- scope/provider 概念
- 重要辅助工具
- 源码引用（文件路径与候选类/函数）

## 关键类/模块（候选）

- `cullinan/core/context.py`
  - 责任：管理注入上下文、解析运行时依赖与作用域上下文。
  - 关键对象：Context（或类似命名）
  - 优先级：High

- `cullinan/core/registry.py`
  - 责任：注册可注入的提供者/组件映射（名字或类型到 provider 的注册）。
  - 关键对象：Registry、注册/查找接口
  - 优先级：High

- `cullinan/core/provider.py`
  - 责任：提供对象创建策略（工厂/单例/瞬时等），实现 provider 接口。
  - 关键对象：Provider 基类、工厂函数
  - 优先级：High

- `cullinan/core/injection.py` 与 `legacy_injection.py`
  - 责任：实现注入解析逻辑（基于类型/注解/构造函数参数注入），`legacy_injection` 可能包含兼容性或旧实现。
  - 关键对象：inject 函数、装饰器、参数解析器
  - 优先级：High

- `cullinan/core/scope.py`
  - 责任：定义作用域类型（Singleton/Request/Transient 等）和作用域边界管理。
  - 关键对象：Scope 枚举/类、作用域管理器
  - 优先级：High

- `cullinan/core/lifecycle.py` 与 `lifecycle_enhanced.py`
  - 责任：管理对象生命周期钩子（初始化/销毁/启动/停止等），`enhanced` 提供扩展或更细粒度的控制。
  - 关键对象：Lifecycle 管理器、回调注册
  - 优先级：High

- `cullinan/core/exceptions.py`
  - 责任：定义 IoC/DI 相关的异常类型（注入失败、循环依赖、未注册等）。
  - 优先级：High

- `cullinan/core/types.py`
  - 责任：类型别名和通用类型定义（例如 ProviderType、ScopeType 等）。
  - 优先级：Medium

- `cullinan/core/__init__.py`
  - 责任：对外暴露核心 API（简化导入路径）
  - 优先级：Medium

## IoC/DI 控制流（高层次）

1. 注册阶段（Registry）
   - 向 `registry` 注册类型到 provider 的映射。可以是显式注册或通过扫描（`module_scanner.py`）自动发现。
2. 解析/构建阶段（Context/Provider）
   - 客户端请求某个类型或 controller 实例。
   - `context` 或 `provider` 根据 scope 与注册信息决定是否复用实例或创建新实例。
3. 注入阶段（injection）
   - 在实例创建后或构造时，`injection` 模块负责解析构造函数参数或属性注入（基于类型提示或装饰器），并从 `context`/`registry` 中获取依赖实例。
4. 生命周期阶段（lifecycle）
   - 在实例创建/注入完成后，`lifecycle` 管理初始化回调（例如调用 `on_init`）并在容器关闭时触发销毁回调。

## 生命周期钩子与增强点

- 典型钩子：初始化（post-construct）、预销毁（pre-destroy）、启动（on_start）、停止（on_stop）。
- `lifecycle_enhanced.py` 可能实现更细的事件订阅、异步钩子或基于优先级的回调调度。

## Scope 与 Provider 说明

- Scope（作用域）决定 provider 是否返回相同实例（单例）或每次新建（瞬时/请求）。
- Provider 负责具体实例化逻辑，可能支持工厂方法、参数转发或懒加载。

## 重要辅助工具

- 异常类型（`exceptions.py`）：用于精确捕获注入错误并在文档中列出常见错误及排查建议。
- `types.py`：用于定义公共类型，文档中引用类型签名时应指向此文件。
- `registry.py` 与 `module_scanner.py`（顶层）：关联代码扫描与自动注册机制，示例中推荐使用显式注册以降低复杂度。

## 源码引用（文件列表与候选类/函数）

- `cullinan/core/context.py` — Context 管理（构造/解析/作用域边界）
- `cullinan/core/registry.py` — 注册/查找实现
- `cullinan/core/provider.py` — Provider 抽象与实现
- `cullinan/core/injection.py` — 注入核心逻辑
- `cullinan/core/legacy_injection.py` — 旧注入兼容实现
- `cullinan/core/scope.py` — 作用域定义与管理
- `cullinan/core/lifecycle.py` — 生命周期基础实现
- `cullinan/core/lifecycle_enhanced.py` — 生命周期增强实现
- `cullinan/core/exceptions.py` — 注入/解析相关异常类型
- `cullinan/core/types.py` — 公共类型定义
- `cullinan/__init__.py`, `cullinan/app.py`, `cullinan/application.py` — 框架启动与运行入口（示例中引用）

## 建议的文档结构（核心概念章节）

1. 概览：IoC/DI 的总体职责与高层控制流（简要）
2. 关键组件：Context / Registry / Provider / Injection / Lifecycle / Scope（每一项引用源码文件）
3. 示例流程：注册 → 请求实例 → 注入 → 生命周期回调（带示例伪代码）
4. 常见问题与调试：循环依赖、未注册类型、参数解析失败（引用 `exceptions.py`）
5. 参考：文件路径和待确认的行号范围（便于开发者填写）


---

文件创建路径（本次操作）:
- `docs/work/core_concepts_draft.md`


