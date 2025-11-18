# 源码文件清单（Inventory）

说明：本清单列出 `cullinan/core` 及与文档相关的顶层模块文件，给出基于实现的一行职责推断与文档优先级（High/Medium/Low）。开发者应核对并在必要时调整职责描述与优先级。

## `cullinan/core`（High 优先级）

- `context.py` — 管理注入上下文与解析流程（Context 管理）：Priority: High
- `registry.py` — 组件/提供者注册与查找实现：Priority: High
- `provider.py` — Provider 抽象与实例化策略（工厂/单例/瞬时）：Priority: High
- `injection.py` — 注入解析逻辑（构造/参数/属性注入）：Priority: High
- `legacy_injection.py` — 向后兼容的注入实现或旧策略：Priority: High
- `scope.py` — 定义作用域类型与作用域边界管理：Priority: High
- `lifecycle.py` — 基础生命周期管理（init/destroy 回调）：Priority: High
- `lifecycle_enhanced.py` — 生命周期增强功能（更细粒度或异步钩子）：Priority: High
- `exceptions.py` — IoC/DI 相关异常定义（注入失败、循环依赖等）：Priority: High
- `types.py` — 公共类型与别名（ProviderType/ScopeType 等）：Priority: Medium
- `__init__.py` — 对外 API 暴露/快捷导入：Priority: Medium

## 其他顶层模块（建议优先级）

- `app.py` — 框架启动与请求入口示例（运行/入口）：Priority: High
- `application.py` — 应用级生命周期与配置载入：Priority: High
- `module_scanner.py` — 模块扫描与自动注册辅助：Priority: Medium
- `websocket_registry.py` — WebSocket 注册/管理（若有）：Priority: Medium
- `controller/` — 控制器实现与示例（HTTP/WebSocket 控制器）：Priority: High
- `middleware/` — 中间件实现示例与接口：Priority: Medium
- `service/` — 服务层示例与注入消费端：Priority: Medium
- `handler/` — 请求处理相关适配器或帮助器：Priority: Medium
- `logging_utils.py` — 日志封装工具（注意：禁止 emoji）：Priority: Low
- `monitoring/` — 监控/指标代码与示例：Priority: Low
- `testing/` — 测试用例与自检脚本（可用作示例参考）：Priority: Medium
- `config.py` — 配置解析与读取：Priority: Medium
- `path_utils.py` — 路径与文件工具函数：Priority: Low

## 使用建议

- 对 High 优先级文件先行进行功能对照与示例实现，确保文档覆盖核心 IoC/DI 流程。
- 在 `docs/work/core_concepts_draft.md` 中引用这些文件并让开发者补充确切行号与关键符号。


文件创建路径（本次操作）：
- `docs/work/inventory.md`

