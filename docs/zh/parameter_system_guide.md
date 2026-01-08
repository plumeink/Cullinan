---
title: "参数系统指南"
slug: "parameter-system-guide"
module: ["cullinan.params", "cullinan.codec"]
tags: ["params", "api", "guide"]
author: "Plumeink"
reviewers: []
status: new
locale: zh
translation_pair: "docs/parameter_system_guide.md"
related_tests: ["tests/test_params.py", "tests/test_codec.py", "tests/test_resolver.py"]
related_examples: []
estimate_pd: 2
last_updated: "2026-01-08T00:00:00Z"
pr_links: []
---

# 参数系统指南

> **版本**: 0.90+
> 
> 本指南介绍 Cullinan 0.90 版本引入的新参数系统，提供类型安全的参数处理，支持自动转换、校验和模型映射。

## 概述

参数系统提供了现代化的 HTTP 请求参数处理方式：

- **类型安全参数**：在函数签名中声明参数类型
- **自动类型转换**：字符串值自动转换为目标类型
- **参数校验**：内置校验器 (ge, le, regex 等)
- **多数据源**：Path, Query, Body, Header, File
- **模型支持**：dataclass 和 DynamicBody
- **自动类型推断**：自动检测值类型

## 模块结构

```
cullinan/
├── codec/           # 编解码层
│   ├── base.py     # BodyCodec / ResponseCodec 抽象
│   ├── errors.py   # DecodeError / EncodeError
│   ├── json_codec.py
│   ├── form_codec.py
│   └── registry.py # CodecRegistry
├── params/          # 参数处理层
│   ├── base.py     # Param 基类 + UNSET
│   ├── types.py    # Path/Query/Body/Header/File
│   ├── converter.py # TypeConverter
│   ├── auto.py     # Auto 类型推断
│   ├── dynamic.py  # DynamicBody
│   ├── validator.py # ParamValidator
│   ├── model.py    # ModelResolver (dataclass)
│   └── resolver.py # ParamResolver
└── middleware/
    └── body_decoder.py # BodyDecoderMiddleware
```

## 快速开始

### 基础用法

```python
from cullinan import get_api, post_api
from cullinan.params import Path, Query, Body

@controller
class UserController:
    
    @get_api(url="/users/{id}")
    async def get_user(self, id: Path(int)):
        # id 已经转换为 int 类型
        return {"id": id}
    
    @get_api(url="/users")
    async def list_users(
        self,
        page: Query(int, default=1, ge=1),
        size: Query(int, default=10, ge=1, le=100),
    ):
        return {"page": page, "size": size}
    
    @post_api(url="/users")
    async def create_user(
        self,
        name: Body(str, required=True),
        age: Body(int, default=0, ge=0),
    ):
        return {"name": name, "age": age}
```

### 使用 DynamicBody

```python
from cullinan.params import DynamicBody

@post_api(url="/users")
async def create_user(self, body: DynamicBody):
    # 属性访问
    print(body.name)
    print(body.age)
    
    # 字典式访问
    email = body.get('email', 'default@example.com')
    
    return body.to_dict()
```

### 使用 dataclass 模型

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CreateUserRequest:
    name: str
    age: int = 0
    email: Optional[str] = None

@post_api(url="/users")
async def create_user(self, user: CreateUserRequest):
    # user 是类型化的 dataclass 实例
    return {
        "name": user.name,
        "age": user.age,
        "email": user.email
    }
```

## 参数类型

### Path

URL 路径参数，始终必填。

```python
@get_api(url="/users/{user_id}/posts/{post_id}")
async def get_post(
    self,
    user_id: Path(int),
    post_id: Path(int, ge=1),
):
    pass
```

### Query

查询字符串参数。

```python
@get_api(url="/search")
async def search(
    self,
    q: Query(str, required=True),
    page: Query(int, default=1),
    limit: Query(int, default=10, ge=1, le=100),
):
    pass
```

### Body

请求体参数。

```python
@post_api(url="/articles")
async def create_article(
    self,
    title: Body(str, required=True, min_length=1, max_length=200),
    content: Body(str, required=True),
    published: Body(bool, default=False),
):
    pass
```

### Header

HTTP 请求头参数。

```python
@get_api(url="/protected")
async def protected_resource(
    self,
    auth: Header(str, alias='Authorization', required=True),
    request_id: Header(str, alias='X-Request-ID', required=False),
):
    pass
```

### File

文件上传参数。

```python
@post_api(url="/upload")
async def upload_file(
    self,
    avatar: File(required=True, max_size=5*1024*1024),  # 5MB 限制
    document: File(allowed_types=['application/pdf']),
):
    pass
```

## 校验器

内置校验约束：

| 校验器 | 类型 | 说明 |
|--------|------|------|
| `required` | 所有 | 字段必填 |
| `ge` | 数值 | 大于等于 |
| `le` | 数值 | 小于等于 |
| `gt` | 数值 | 大于 |
| `lt` | 数值 | 小于 |
| `min_length` | 字符串/列表 | 最小长度 |
| `max_length` | 字符串/列表 | 最大长度 |
| `regex` | 字符串 | 正则表达式匹配 |

示例：

```python
@post_api(url="/register")
async def register(
    self,
    email: Body(str, regex=r'^[\w.-]+@[\w.-]+\.\w+$'),
    password: Body(str, min_length=8, max_length=128),
    age: Body(int, ge=18, le=120),
):
    pass
```

## 自动类型推断

使用 `AutoType` 进行自动类型检测：

```python
from cullinan.params import AutoType

@get_api(url="/search")
async def search(self, value: Query(AutoType)):
    # value 会自动推断类型:
    # "123" -> 123 (int)
    # "12.5" -> 12.5 (float)
    # "true" -> True (bool)
    # '{"a":1}' -> {"a": 1} (dict)
    pass
```

## Codec 系统

### 注册自定义 Codec

```python
from cullinan.codec import BodyCodec, get_codec_registry

class XmlBodyCodec(BodyCodec):
    content_types = ['application/xml', 'text/xml']
    priority = 30
    
    def decode(self, body: bytes, charset: str = 'utf-8'):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(body.decode(charset))
        return {child.tag: child.text for child in root}

# 注册 codec
registry = get_codec_registry()
registry.register_body_codec(XmlBodyCodec)
```

### 请求体解码中间件

`BodyDecoderMiddleware` 自动解码请求体：

```python
from cullinan.middleware import BodyDecoderMiddleware, get_decoded_body

# 在处理器中获取已解码的请求体
class MyController:
    @post_api(url="/data")
    async def handle_data(self):
        body = get_decoded_body(self.request)
        return body
```

## 向后兼容

传统参数风格完全支持：

```python
# 传统方式（仍然有效）
@post_api(url="/users", body_params=['name', 'age'])
async def create_user(self, body_params):
    name = body_params.get('name')
    age = body_params.get('age')
```

## 错误处理

参数错误返回结构化响应：

```python
from cullinan.params import ValidationError, ResolveError

# ValidationError 用于单个参数校验失败
# ResolveError 用于多个参数解析失败

# 错误响应格式：
{
    "error": "参数校验失败",
    "details": [
        {"param": "age", "error": "必须 >= 0", "constraint": "ge:0"}
    ]
}
```

## 最佳实践

1. **使用类型提示**：始终指定参数类型以提高代码清晰度
2. **设置合理的默认值**：为可选参数提供默认值
3. **尽早校验**：使用内置校验器而非手动检查
4. **复杂请求体使用模型**：结构化请求体使用 dataclass
5. **灵活场景使用 DynamicBody**：请求体结构变化时使用

## API 参考

### cullinan.params

| 类 | 说明 |
|---|------|
| `Param` | 参数基类 |
| `Path` | URL 路径参数 |
| `Query` | 查询字符串参数 |
| `Body` | 请求体参数 |
| `Header` | HTTP 请求头参数 |
| `File` | 文件上传参数 |
| `TypeConverter` | 类型转换工具 |
| `Auto` | 自动类型推断 |
| `AutoType` | 自动类型标记 |
| `DynamicBody` | 动态请求体容器 |
| `ParamValidator` | 参数校验器 |
| `ModelResolver` | dataclass 模型解析器 |
| `ParamResolver` | 参数解析编排器 |

### cullinan.codec

| 类 | 说明 |
|---|------|
| `BodyCodec` | 请求体编解码器抽象类 |
| `ResponseCodec` | 响应编码器抽象类 |
| `JsonBodyCodec` | JSON 请求体解码器 |
| `JsonResponseCodec` | JSON 响应编码器 |
| `FormBodyCodec` | Form 请求体解码器 |
| `CodecRegistry` | Codec 注册表 |
| `DecodeError` | 解码错误 |
| `EncodeError` | 编码错误 |

### cullinan.middleware

| 类 | 说明 |
|---|------|
| `BodyDecoderMiddleware` | 自动请求体解码中间件 |
| `get_decoded_body()` | 获取已解码的请求体 |

