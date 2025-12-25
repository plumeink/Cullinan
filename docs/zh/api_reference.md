title: "API 参考"
slug: "api-reference"
module: []
tags: ["api", "reference"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/api_reference.md"
related_tests: []
related_examples: []
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# API 参考

> **说明（v0.90）**：核心模块已重新组织。新的 API 结构请参阅 [IoC/DI 2.0](wiki/ioc_di_v2.md) 和 [导入迁移指南](import_migration_090.md)。

本文档用于汇总 Cullinan 的公共 API 概览，并为后续自动生成或手动维护的 API 页面提供入口。推荐的结构包括：模块索引、每个模块的公有符号与签名、以及重新生成 API 文档的步骤说明。

## 模块索引（示例）

以下模块列表仅为示例，具体内容应根据实际代码结构和自动化生成结果补全：

- `cullinan.app` — 应用创建与运行入口
- `cullinan.application` — 应用生命周期与启动流程
- `cullinan.core` — IoC/DI 核心（Provider、Registry、Scope、注入 API）
- `cullinan.controller` — 控制器与 RESTful API 装饰器
- `cullinan.service` — Service 基类与 `@service` 装饰器
- `cullinan.middleware` — 中间件基类与扩展点

## 公共符号与签名（建议结构）

每个模块建议按以下结构列出公共符号：

- 模块路径，例如：`cullinan.controller`
- 简要说明：模块的主要职责与使用场景
- 公有类与函数列表（示例）：
  - `@controller(...)` — 控制器装饰器，负责自动注册控制器与路由
  - `@get_api(url=..., query_params=..., body_params=..., headers=...)` — GET 接口装饰器
  - `@post_api(url=..., body_params=..., headers=...)` — POST 接口装饰器
  - `Inject`, `InjectByName` — 属性/构造器注入标记

完整 API 参考可以通过自动生成脚本或手工整理的方式填充上述结构。

## 重新生成 API 文档（步骤示例）

在后续实现自动化时，可以选择使用静态分析脚本生成 API 索引并更新本页面。典型流程示例：

1. 在 `docs/work/` 目录下维护一个用于扫描模块并生成 Markdown 片段的脚本（例如 `generate_api_reference.py`）。
2. 脚本输出按模块划分的 API 列表（类、函数、签名、简要说明），写入 `docs/work/api_modules.md` 或直接更新本页面。
3. 在 CI 或本地构建流程中定期运行该脚本，保证 API 参考与源码保持同步。

具体实现细节可根据项目约定和工具链选择进行补充。
