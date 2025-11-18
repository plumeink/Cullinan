title: "示例与演示"
slug: "examples"
module: []
tags: ["examples"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/examples.md"
related_tests: []
related_examples: ["examples/hello_http.py"]
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# 示例与演示

本文列出了 Cullinan 仓库中维护的可运行示例。每个示例包含：路径、简要说明，以及在常见平台上的运行方式。

## Hello HTTP

- **路径**：`examples/hello_http.py`
- **说明**：最小化的 HTTP 服务，返回简单问候。

### 运行方式

在 Windows（PowerShell）中：

```powershell
python examples\hello_http.py
```

在 Linux / macOS 中：

```bash
python examples/hello_http.py
```

预期行为：

- 启动一个 HTTP 服务。
- 在 `http://localhost:4080/hello` 上提供响应。

## Controller + DI + Middleware 示例

- **路径**：`examples/controller_di_middleware.py`
- **说明**：演示控制器、依赖注入与中间件的集成用法。

### 运行方式

在 Windows（PowerShell）中：

```powershell
python examples\controller_di_middleware.py
```

在 Linux / macOS 中：

```bash
python examples/controller_di_middleware.py
```

预期行为：

- 通过中间件记录请求处理过程。
- 展示注入的服务如何参与请求处理管线。

<!-- ...后续如仓库新增示例，可按相同格式在此补充... -->
