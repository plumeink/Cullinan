# Cullinan 文档编写详细计划（工作文档）

说明：这是工作文档，记录执行细节、任务分解与责任分配；目标产出文档将被放在 `docs/` 与 `docs/zh/` 下并保持 1:1 对齐。

## 目标

- 基于源码实现（以代码为准，不依赖注释）编写完整文档集，涵盖：入门、示例、架构说明、模块说明、Wiki（组件/注入/生命周期/中间件/扩展）和 API 参考。
- 输出可直接用于 MkDocs 的 `docs/` 目录，并保证与 `docs/zh/` 的 1:1 对应。
- 工作文档与目标产出文档严格分离：所有分析、草稿、待办与验证记录放在 `docs/work/`；最终用户阅读材料放在 `docs/` 和 `docs/zh/`。

## 范围与优先级

- 优先级 High：`cullinan/core`（IoC/DI 实现）、`cullinan/application.py`、`cullinan/app.py`、`controller` 目录与示例代码。
- 优先级 Medium：中间件(`middleware`)、服务(`service`)、模块扫描(`module_scanner.py`)与注册机制(`websocket_registry.py`)。
- 优先级 Low：监控/测试示例与边缘工具目录。

## 输出清单（目标产出文档）

- `docs/getting_started.md`（入门）
- `docs/examples.md`（示例集合，可运行示例）
- `docs/architecture.md`（架构说明）
- `docs/wiki/components.md`
- `docs/wiki/injection.md`
- `docs/wiki/lifecycle.md`
- `docs/wiki/middleware.md`
- `docs/wiki/extensions.md`
- `docs/modules/app.md`、`docs/modules/application.md`、`docs/modules/core.md`、`docs/modules/controller.md`、`docs/modules/service.md`
- `docs/api_reference.md`（API）
- 对应的 `docs/zh/...` 文件 1:1 翻译

> 每个目标文档需在头部标注：基于源码版本：branch/commit <填写位置>（由开发者执行一次示例并在此处记录 commit/hash）。

## 里程碑（示例时间分配，可调整）

1. M1 - 目录与模板设定（0.5 天）：确认 MkDocs 结构、导航与工作目录分离（完成）。
2. M2 - 核心源码阅读与概念草稿（1.5 天）：读取 `cullinan/core` 并生成 `docs/work/core_concepts_draft.md`（进行中）。
3. M3 - 编写入门与最小可运行示例（2 天）：生成 `docs/getting_started.md` 与 `docs/examples.md` 可在 Windows PowerShell 下逐步运行的示例。
4. M4 - 模块文档与 Wiki 页面草稿（3 天）：逐模块完成草稿并放入 `docs/work/` 供审核。
5. M5 - API 参考与示例验证（2 天）：结合源码手工或半自动生成 API 参考，并由开发者验证准确性。
6. M6 - 中文翻译与 1:1 对齐（2 天）：生成 `docs/zh/`，并保证文件名与目录结构一致。

## 任务分解（AI 与开发者）

- AI 职责：
  - 快速解析源码实现，生成文档草稿、示例骨架与翻译初稿。
  - 生成工作文档（本目录下）以利审阅与二次加工。
  - 生成检查清单与自动化辅助脚本（若必要，量力而行）。

- 开发者职责：
  - 使用本仓库源码运行并验证示例代码、填写 commit/hash。 
  - 审核 AI 生成的实现细节引用（文件/函数/类）并修正不匹配之处。
  - 补充示例输出、代码片段或复杂交互场景的真实运行结果。

## 编写与质量要求

- 使用 UTF-8 编码。
- 禁止在日志或文档中使用 emoji。
- 问题分析必须以源码实现为准（忽略注释作为准据）。
- 每个目标文档须包含“源码引用表”：路径 + 关键类/函数 + 行号范围（开发者在审核时补充精确行号）。
- 文档结构应便于 AI 二次归纳（使用固定标题、编号任务、表格清单）。

## 校验门（Quality Gates）

每个里程碑完成后执行：

1. 构建/Smoke 测试：对示例运行基本检查（最小启动/请求）。
2. 静态检查：确保 Markdown 无编码或语法错误，导航链接有效。
3. 人工校验：开发者确认 API 与实现一致（在 `docs/work/review_tasks.md` 中打勾）。

## 复加工准备（为二次加工铺垫）

- 每个目标文档末尾附带“源代码引用表”和“未决问题”段落。
- 工作文档必须保留：决策记录、待办项、验证结果、开发者反馈与时间戳。
- 为便于自动化，使用统一元数据模板（YAML front-matter 可选）记录来源 commit/hash、生成时间与作者。

## 初始下一步（立即执行）

- AI：已生成并准备写入 `docs/work/core_concepts_draft.md`、`docs/work/review_tasks.md`、`docs/work/inventory.md` 与更新 `docs/work/progress_tracker.md`（本次操作包含这些文件）。
- 开发者：请在本仓库执行一次示例运行并在 `docs/work/progress_tracker.md` 的相应位置记录 commit/hash 和运行结果。


---

文件创建路径（工作文档）：
- `docs/work/documentation_plan.md`（本文件）


