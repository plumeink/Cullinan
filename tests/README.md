# Cullinan 测试目录

`tests\` 现在按职责分层，`pytest` 是唯一正式入口；本次 application-first 更新相关覆盖也已经收敛到可直接收集的 pytest 测试。

## 运行方式

在仓库根目录执行：

```powershell
.venv\Scripts\python -m pytest
```

按目录执行：

```powershell
.venv\Scripts\python -m pytest tests\core
.venv\Scripts\python -m pytest tests\di
.venv\Scripts\python -m pytest tests\web
.venv\Scripts\python -m pytest tests\integration
.venv\Scripts\python -m pytest tests\regression
.venv\Scripts\python -m pytest tests\compat
```

## 目录结构

```text
tests/
├── compat/        # 兼容性与历史 API 行为
├── core/          # 核心模块、配置、扫描、异常与基础行为
├── di/            # IoC / DI、容器、生命周期、注册表
├── integration/   # 跨模块集成测试
├── regression/    # 历史缺陷回归与边界场景
├── web/           # Web runtime、请求处理、参数/模型/编解码
├── helpers/       # 共享 helper（非测试入口）
└── conftest.py    # 共享 pytest 启动配置
```

## 约定

1. 正式测试文件统一命名为 `test_*.py`。
2. 新增测试时优先放入对应领域目录；只有跨模块场景才放 `integration`。
3. 新增或刷新测试时，不再使用 `run_*`、`quick_*`、`verify_*`、`diagnose_*` 这类脚本式主线测试。
4. 历史 `if __name__ == "__main__"`、`main()`、`run_all_tests()` 直跑入口已清理；正式验证统一交给 pytest 收集。
5. 若需要共享测试工具，放到 `tests\helpers\`，不要直接作为测试入口执行。

## 编写建议

1. 优先编写可直接被 `pytest` 收集的测试函数或 `unittest.TestCase`。
2. 避免依赖 `if __name__ == "__main__"`、`print("[PASS]")`、`return True/False` 的手工执行模式。
3. 需要仓库根路径时，依赖 `tests\conftest.py` 提供的统一路径注入，不要在新文件里重复硬编码路径。

## 本次更新相关测试

- `tests\core\test_application_model_refactor.py`：application-first 启动、模块归属、runtime 切换
- `tests\core\test_public_api_boundaries.py`：顶层推荐 API、兼容导出 warning、公开边界收敛
- `tests\core\test_decorators.py`：装饰器注册元数据与重扫能力
- `tests\integration\test_adapter_integration.py`：ASGI / Tornado 适配器集成路径
- `tests\integration\test_gateway_integration.py`：gateway 端到端行为的 pytest 化集成覆盖
- `tests\web\test_openapi_generator.py`：OpenAPI 自动生成与公开 spec 路径覆盖
