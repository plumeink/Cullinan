title: "测试与验证"
slug: "testing"
module: []
tags: ["testing"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/testing.md"
related_tests: ["tests/web/test_web_runtime.py", "tests/di/test_core_constructor_injection.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# 测试与验证

本文说明测试体系整合后的当前仓库测试工作流。

## 仓库正式入口

请使用仓库虚拟环境执行：

```powershell
.venv\Scripts\python -m pytest
```

这就是当前仓库在测试清理后的正式命令。

## 测试发现配置

`pytest.ini` 定义了仓库默认规则：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -ra
```

`tests/conftest.py` 会把仓库根目录加入 `sys.path`，因此新测试不应再重复写本地 `sys.path.insert(...)` 引导代码。

## 测试目录结构

测试按主题组织：

- `tests/core`
- `tests/di`
- `tests/web`
- `tests/integration`
- `tests/regression`
- `tests/compat`
- `tests/helpers`

新增测试时，优先放入最接近的现有主题目录，而不是继续创建零散的顶层文件。

## 运行定向测试

示例：

```powershell
.venv\Scripts\python -m pytest tests\web\test_web_runtime.py -q
.venv\Scripts\python -m pytest tests\di\test_core_constructor_injection.py -q
```

通用的 `python -m pytest` 也可运行，但当前仓库文档标准统一使用 Windows 下的 `.venv\Scripts\python` 形式。

## 当前约定

1. 使用标准 pytest 测试与普通 `assert` 断言。
2. 避免脚本式的 “return True/False” 验证文件。
3. 需要共享初始化时，优先复用 `tests/conftest.py` 与 `tests/helpers/`。
4. 测试若修改全局 registry 或活动应用上下文，必须自行完成隔离与清理。

## 测试覆盖范围

当前测试集覆盖：

- 容器与生命周期行为
- 兼容层语义
- gateway / Web Runtime 行为
- 控制器路由与参数处理
- 集成与回归场景

## 相关文档

- [运行时整合概览](runtime_updates_v093.md)
- [架构设计](architecture.md)
- [Web Runtime 指南](web_runtime_guide.md)
