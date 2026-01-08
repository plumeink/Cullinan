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

> **说明（v0.90）**：核心模块已重新组织。新的 API 结构请参阅 [依赖注入指南](dependency_injection_guide.md) 和 [导入迁移指南](import_migration_090.md)。

本文档用于汇总 Cullinan 的公共 API 概览，并为后续自动生成或手动维护的 API 页面提供入口。推荐的结构包括：模块索引、每个模块的公有符号与签名、以及重新生成 API 文档的步骤说明。

## 模块索引（示例）

以下模块列表仅为示例，具体内容应根据实际代码结构和自动化生成结果补全：

- `cullinan.app` — 应用创建与运行入口
- `cullinan.application` — 应用生命周期与启动流程
- `cullinan.core` — IoC/DI 核心（Provider、Registry、Scope、注入 API）
- `cullinan.controller` — 控制器与 RESTful API 装饰器
- `cullinan.service` — Service 基类与 `@service` 装饰器
- `cullinan.middleware` — 中间件基类与扩展点
- `cullinan.codec` — 请求/响应编解码（JSON、Form 等）
- `cullinan.params` — 参数处理（Path、Query、Body、Header、File、校验器）

## v0.90+ 新增：参数系统

参数系统提供类型安全的请求参数处理。详见 [参数系统指南](parameter_system_guide.md)。

### cullinan.params (v0.90a4+)

| 符号 | 类型 | 说明 |
|------|------|------|
| `Param` | 类 | 参数基类 |
| `Path` | 类 | URL 路径参数标记 |
| `Query` | 类 | 查询字符串参数标记 |
| `Body` | 类 | 请求体参数标记 |
| `Header` | 类 | HTTP 请求头参数标记 |
| `File` | 类 | 文件上传参数标记 |
| `RawBody` | 类 | 原始请求体，使用 `bytes = RawBody()` (v0.90a5+) |
| `UNSET` | 哨兵 | 表示未设置的哨兵值 |
| `TypeConverter` | 类 | 类型转换工具 |
| `Auto` | 类 | 自动类型推断工具 |
| `AutoType` | 类 | 用于签名的自动类型标记 |
| `DynamicBody` | 类 | 动态请求体容器 |
| `SafeAccessor` | 类 | 链式安全访问器 |
| `EMPTY` | 哨兵 | 空值哨兵 |
| `ParamValidator` | 类 | 参数校验工具 |
| `ValidationError` | 异常 | 校验错误 |
| `ModelResolver` | 类 | dataclass 模型解析器 |
| `ModelError` | 异常 | 模型解析错误 |
| `ParamResolver` | 类 | 参数解析编排器 |
| `ResolveError` | 异常 | 参数解析错误 |

### cullinan.params (v0.90a5+)

| 符号 | 类型 | 说明 |
|------|------|------|
| `FileInfo` | 类 | 文件元数据容器 |
| `FileList` | 类 | 多文件容器 |
| `field_validator` | 装饰器 | Dataclass 字段校验器 |
| `validated_dataclass` | 装饰器 | 自动校验的 dataclass |
| `FieldValidationError` | 异常 | 字段校验错误 |
| `Response` | 装饰器 | 响应模型装饰器 |
| `ResponseModel` | 类 | 响应模型定义 |
| `ResponseSerializer` | 类 | 响应序列化工具 |
| `serialize_response` | 函数 | 便捷序列化函数 |
| `get_response_models` | 函数 | 获取函数的响应模型 |

### cullinan.params.model_handlers (v0.90a5+)

可插拔模型处理器架构，用于第三方库集成。

| 符号 | 类型 | 说明 |
|------|------|------|
| `ModelHandler` | 类 | 模型处理器抽象基类 |
| `ModelHandlerError` | 异常 | 模型处理器错误 |
| `ModelHandlerRegistry` | 类 | 模型处理器注册表 |
| `DataclassHandler` | 类 | 内置 dataclass 处理器 |
| `PydanticHandler` | 类 | 可选 Pydantic 处理器（安装后可用）|
| `get_model_handler_registry()` | 函数 | 获取全局处理器注册表 |
| `reset_model_handler_registry()` | 函数 | 重置注册表（测试用）|

### cullinan.codec

| 符号 | 类型 | 说明 |
|------|------|------|
| `BodyCodec` | 类 | 请求体编解码器抽象类 |
| `ResponseCodec` | 类 | 响应编码器抽象类 |
| `JsonBodyCodec` | 类 | JSON 请求体解码器 |
| `JsonResponseCodec` | 类 | JSON 响应编码器 |
| `FormBodyCodec` | 类 | Form 请求体解码器 |
| `CodecRegistry` | 类 | Codec 注册表 |
| `get_codec_registry()` | 函数 | 获取全局 Codec 注册表 |
| `reset_codec_registry()` | 函数 | 重置 Codec 注册表（测试用）|
| `DecodeError` | 异常 | 解码错误 |
| `EncodeError` | 异常 | 编码错误 |
| `CodecError` | 异常 | 编解码错误基类 |

### cullinan.middleware（新增）

| 符号 | 类型 | 说明 |
|------|------|------|
| `BodyDecoderMiddleware` | 类 | 自动请求体解码中间件 |
| `get_decoded_body()` | 函数 | 获取已解码的请求体 |
| `set_decoded_body()` | 函数 | 设置已解码的请求体（测试用）|

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
