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

### Hello HTTP 示例

在 Windows（PowerShell）中：

```powershell
python examples\hello_http.py
```

在 Linux / macOS 中：

```bash
python examples/hello_http.py
```

然后在浏览器中访问 `http://localhost:4080/hello`，验证服务已成功启动。

### 中间件演示示例

在 Windows（PowerShell）中：

```powershell
python examples\middleware_demo.py
```

在 Linux / macOS 中：

```bash
python examples/middleware_demo.py
```

关于该示例的日志输出和行为说明，请参考中间件相关文档。
