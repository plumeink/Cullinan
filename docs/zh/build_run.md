title: "本地构建与运行"
slug: "build-run"
module: []
tags: ["build", "run"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/build_run.md"
related_tests: []
related_examples: []
estimate_pd: 1.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# 本地构建与运行

本文说明如何在本地搭建 Cullinan 开发环境、以可编辑模式安装项目、运行测试以及启动示例应用，覆盖 Windows（PowerShell）、Linux 和 macOS。

## 前置条件

- Python 3.8 或更高版本
- Git

## 克隆仓库

在所有平台上均可使用以下命令：

```bash
git clone https://github.com/plumeink/Cullinan.git
cd Cullinan
```

## 创建并激活虚拟环境（可选但推荐）

在 Windows（PowerShell）中：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

在 Linux / macOS 中：

```bash
python -m venv .venv
source .venv/bin/activate
```

## 以可编辑模式安装依赖

在所有平台上：

```bash
python -m pip install -U pip
pip install -e .
```

如果在 `setup.py` 或 `pyproject.toml` 中定义了开发额外依赖，可按需安装，例如：

```bash
pip install -e .[dev]
```

## 运行测试

在所有平台上：

```bash
pytest -q
```

如项目使用不同的测试运行方式，可根据实际情况调整命令（例如使用 `python -m pytest`）。

## 运行示例应用

当前维护中的可运行示例已经统一收敛到项目根目录 `examples/` 下，并以小型包的
方式组织。建议先从最小示例开始，再进入更有针对性的主题示例。

### 最小应用

```powershell
python -m examples.minimal_app
```

然后访问 `http://localhost:4080/hello`，确认服务已启动。

### 业务分层与注入

```powershell
python -m examples.controller_service_inject
```

这个示例用于展示推荐的 `@service` + `@controller` + `Inject()` 路径。

### 中间件与模块边界

```powershell
python -m examples.middleware_and_module
```

该示例展示 `@module` 表达运行时边界归属，以及 `@middleware` 扩展请求处理管线。

### 参数绑定

```powershell
python -m examples.parameter_handling
```

可配合参数系统指南一起查看控制器方法上的 `Path`、`Query`、`Body` 写法。

### 示例级测试流

```powershell
python -m pytest examples/testing_flow/test_app.py -q
```

这条路径会通过 `configure(...)` 和 `get_asgi_app()` 直接验证示例，而不需要真的启动外部服务进程。
