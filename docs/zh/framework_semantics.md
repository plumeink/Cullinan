title: "框架语义规则"
slug: "framework-semantics"
tags: ["guide", "semantics", "diagnostics"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/framework_semantics.md"
related_tests: ["tests/regression/test_component_reliability.py", "tests/core/test_injection_annotation_parsing.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# 框架语义规则

本文定义 Cullinan **保证什么**、哪些行为只是兼容保留，以及哪些场景现在会触发 warning 或启动期失败。目标是把 Cullinan 的运行时模型讲清楚：先写装饰器式业务代码，通过导入执行完成发现，在需要时再引入明确的运行时边界。

> **推荐下一步：** [架构设计](architecture.md)、[工程实践](how-to/index.md)  
> **如果你要查符号而不是读解释：** 请转到 [API 参考](reference/index.md)。

## 推荐的语义化包路径

Cullinan 当前推荐的主路径是：

- `cullinan` —— 应用启动入口（`configure`、`run`、`get_asgi_app`）
- `cullinan.application` —— `Application`、`module` 等高级应用语义
- `cullinan.web` —— 控制器、路由装饰器、请求/响应、参数与中间件
- `cullinan.core` —— IoC/DI、生命周期与语义诊断

像 `cullinan.runtime`、`cullinan.transport`、`cullinan.support` 这样的更底层层级仍然可用，但不应成为普通业务应用的默认入门路径。

这也意味着默认学习路径**不是先学 Tornado 再学 Cullinan**。Tornado 与 ASGI 是框架边界之后的执行后端；对应用代码真正构成主契约的，是 Cullinan 自身的 Web 与 application 语义。

## 1. 组件发现依赖“导入执行”，不是静态 AST 扫描，也不是显式 app 注册

Cullinan 通过**导入 Python 模块**并执行装饰器来发现组件。

- 受保证：模块顶层定义、且在模块导入时就执行到的 `@service`、`@controller`、`@component`、`@provider`
- 不受保证：定义在函数、工厂、条件分支或其他局部作用域里的类；这些定义通常要等运行到对应代码块时装饰器才会执行

```python
from cullinan.core import component


@component
class TopLevelCache:
    pass


def build_repository():
    @component
    class LocalRepository:
        pass

    return LocalRepository
```

`TopLevelCache` 属于受支持的自动发现路径；`LocalRepository` 不属于自动顶层扫描契约。Cullinan 现在会对这类写法发 warning，如果它发生在 `refresh()` 之后，则会直接失败。如果某段能力需要更强的归属、reload 或热插拔运行时保证，应通过 `@module` 表达边界，而不是退回到手工 app 注册思路。

## 2. `Inject()` 是严格类型契约

只有当 Cullinan 能把注解归一化为**稳定且唯一**的依赖契约时，`Inject()` 才会成功。

当前支持的典型形式包括：

- `T`
- `"T"`
- `Optional[T]`
- `Annotated[T, ...]`
- `Final[T]`
- `Provider[T]`
- `list[T]`、`set[T]`、`tuple[T, ...]`
- `Union[A, B]` / `A | B`（前提是最终只命中一个候选）

Cullinan 已不再回退到属性名猜测。如果注解缺失、不受支持或存在歧义，启动会直接以类型化诊断失败。

## 3. `InjectByName()` 的语义是“显式名称绑定”

`InjectByName()` 按组件注册名解析，而不是按类型解析。

推荐写法：

```python
from cullinan.core import InjectByName


class ReportController:
    report_service: "ReportService" = InjectByName("ReportService")
```

兼容写法：

```python
class ReportController:
    report_service = InjectByName()
```

兼容写法目前仍会回退到属性名，但 Cullinan 现在会给出 warning，因为这种绑定在重构时更容易悄悄失效。即使使用按名注入，也建议保留真实类型注解，便于表达语义与静态检查。

## 4. `refresh()` 之后注册会被冻结

`ApplicationContext.refresh()` 是结构边界：

- 会消费并注册 pending 的装饰器组件
- 会完成定义校验与预热
- 会冻结相关注册表

从这一刻开始，再去新增装饰器组件就不再是受支持的运行时变更路径。Cullinan 现在会给出明确的语义错误，并附上修复建议。

## 5. 作用域规则是强约束，不是“尽量工作”

Cullinan 把作用域兼容性视为硬规则。尤其是 `singleton` 组件不能直接依赖 `request` 作用域组件。现在这类情况会给出结构化生命周期诊断，而不是等到更晚阶段以不稳定方式出错。

## 6. 兼容 API 只是兼容，不是推荐入口

像 `@injectable`、`@inject_constructor`、`get_injection_registry()` 这样的旧接口仍然保留，目的是让历史代码还能导入，但它们**不再代表推荐编程模型**。现在使用这些 API 时，Cullinan 会发出 warning。

## 7. 如何理解新的 warning 和报错

Cullinan 现在把关键诊断统一表达为：

- **语义规则**：框架当前强制执行的契约
- **当前问题**：运行时实际观察到的现象
- **建议**：最安全、最受支持的修复方式

当框架能够确定你违反了核心语义时，会直接失败；当代码虽然还能运行，但明显容易误导开发者时，则会发 warning。
