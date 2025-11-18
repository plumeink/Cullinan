title: "测试与验证"
slug: "testing"
module: []
tags: ["testing"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/testing.md"
related_tests: ["tests/*"]
related_examples: []
estimate_pd: 1.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# 测试与验证

本文说明如何运行现有测试集、添加新的测试、使用示例进行烟雾测试，以及在 CI 中集成测试执行。示例命令覆盖 Windows（PowerShell）、Linux 和 macOS。

## 前置条件

- Python 3.8 或更高版本
- Git
- 已克隆并可用的 Cullinan 仓库（环境准备可参考 `docs/build_run.md`）

## 运行测试集

在以可编辑模式安装 Cullinan 之后（参见 `docs/build_run.md`），可以使用 `pytest` 运行测试。

在所有平台上：

```bash
pytest -q
```

如果倾向于通过 Python 模块方式调用，也可以使用：

```bash
python -m pytest -q
```

在 Windows 上，常见的做法是使用 `py` 启动器：

```powershell
py -3 -m pytest -q
```

## 运行单个测试模块

要运行单个测试文件（例如 `tests/test_core_injection.py`）：

在所有平台上：

```bash
pytest tests/test_core_injection.py -q
```

或使用 Python 模块方式：

```bash
python -m pytest tests/test_core_injection.py -q
```

## 添加新测试

在为新特性或缺陷修复添加测试时，建议遵循以下原则：

1. 将测试文件放置在 `tests/` 目录下。
2. 使用具有描述性的测试名称，并将相关测试组织在同一模块中。
3. 优先采用 `pytest` 风格的测试（函数或测试类），与现有测试集保持一致。
4. 确保测试具有确定性，不依赖外部服务，除非明确标注。

## 使用示例进行烟雾测试

Cullinan 在 `examples/` 目录下提供了可运行示例，可作为烟雾测试使用。

### 示例：Hello HTTP

在 Windows（PowerShell）中：

```powershell
python examples\hello_http.py
```

在 Linux / macOS 中：

```bash
python examples/hello_http.py
```

然后在浏览器中访问 `http://localhost:4080/hello`，验证服务是否正常响应。

### 示例：中间件演示

在 Windows（PowerShell）中：

```powershell
python examples\middleware_demo.py
```

在 Linux / macOS 中：

```bash
python examples/middleware_demo.py
```

日志输出将展示中间件和注入的服务如何参与请求处理。具体时间戳和 ID 会因运行环境不同而有所差异。

## 在 CI 中集成测试

在 CI 流水线中，通常需要执行以下步骤：

1. 准备 Python 运行环境。
2. 以可编辑模式安装依赖（可选安装开发额外依赖）。
3. 使用 `pytest` 运行测试集。

bash 风格的典型命令序列（可根据 CI 系统进行调整）：

```bash
python -m pip install -U pip
pip install -e .[dev]
pytest -q
```

在基于 Windows 的 CI 环境中使用 PowerShell 时，可使用类似命令：

```powershell
python -m pip install -U pip
pip install -e .[dev]
py -3 -m pytest -q
```

可根据 CI 提供商与具体环境调整命令与选项。
