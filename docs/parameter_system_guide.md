---
title: "Parameter System Guide"
slug: "parameter-system-guide"
module: ["cullinan.params", "cullinan.codec"]
tags: ["params", "api", "guide"]
author: "Plumeink"
reviewers: []
status: new
locale: en
translation_pair: "docs/zh/parameter_system_guide.md"
related_tests: ["tests/test_params.py", "tests/test_codec.py", "tests/test_resolver.py"]
related_examples: []
estimate_pd: 2
last_updated: "2026-01-08T00:00:00Z"
pr_links: []
---

# Parameter System Guide

> **Version**: 0.90+
> 
> This guide covers the new parameter system introduced in Cullinan 0.90, providing type-safe parameter handling with automatic conversion, validation, and model support.

## Overview

The parameter system provides a modern approach to handling HTTP request parameters:

- **Type-safe parameters**: Declare parameter types in function signatures
- **Automatic conversion**: String values converted to target types
- **Validation**: Built-in validators (ge, le, regex, etc.)
- **Multiple sources**: Path, Query, Body, Header, File
- **Model support**: dataclass and DynamicBody
- **Auto type inference**: Automatic type detection

## Module Structure

```
cullinan/
├── codec/           # Encoding/Decoding layer
│   ├── base.py     # BodyCodec / ResponseCodec abstractions
│   ├── errors.py   # DecodeError / EncodeError
│   ├── json_codec.py
│   ├── form_codec.py
│   └── registry.py # CodecRegistry
├── params/          # Parameter handling layer
│   ├── base.py     # Param base class + UNSET
│   ├── types.py    # Path/Query/Body/Header/File
│   ├── converter.py # TypeConverter
│   ├── auto.py     # Auto type inference
│   ├── dynamic.py  # DynamicBody
│   ├── validator.py # ParamValidator
│   ├── model.py    # ModelResolver (dataclass)
│   └── resolver.py # ParamResolver
└── middleware/
    └── body_decoder.py # BodyDecoderMiddleware
```

## Quick Start

### Basic Usage

```python
from cullinan import get_api, post_api
from cullinan.params import Path, Query, Body

@controller
class UserController:
    
    @get_api(url="/users/{id}")
    async def get_user(self, id: Path(int)):
        # id is already converted to int
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

### Using DynamicBody

```python
from cullinan.params import DynamicBody

@post_api(url="/users")
async def create_user(self, body: DynamicBody):
    # Access fields as attributes
    print(body.name)
    print(body.age)
    
    # Or use dict-like access
    email = body.get('email', 'default@example.com')
    
    return body.to_dict()
```

### Using dataclass Models

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
    # user is a typed dataclass instance
    return {
        "name": user.name,
        "age": user.age,
        "email": user.email
    }
```

## Parameter Types

### Path

URL path parameters, always required.

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

Query string parameters.

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

Request body parameters.

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

HTTP header parameters.

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

File upload parameters.

```python
@post_api(url="/upload")
async def upload_file(
    self,
    avatar: File(required=True, max_size=5*1024*1024),  # 5MB limit
    document: File(allowed_types=['application/pdf']),
):
    pass
```

## Validators

Built-in validation constraints:

| Validator | Types | Description |
|-----------|-------|-------------|
| `required` | All | Field is required |
| `ge` | Numeric | Greater than or equal |
| `le` | Numeric | Less than or equal |
| `gt` | Numeric | Greater than |
| `lt` | Numeric | Less than |
| `min_length` | String/List | Minimum length |
| `max_length` | String/List | Maximum length |
| `regex` | String | Regular expression match |

Example:

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

## Auto Type Inference

Use `AutoType` for automatic type detection:

```python
from cullinan.params import AutoType

@get_api(url="/search")
async def search(self, value: Query(AutoType)):
    # value will be auto-inferred:
    # "123" -> 123 (int)
    # "12.5" -> 12.5 (float)
    # "true" -> True (bool)
    # '{"a":1}' -> {"a": 1} (dict)
    pass
```

## Codec System

### Registering Custom Codecs

```python
from cullinan.codec import BodyCodec, get_codec_registry

class XmlBodyCodec(BodyCodec):
    content_types = ['application/xml', 'text/xml']
    priority = 30
    
    def decode(self, body: bytes, charset: str = 'utf-8'):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(body.decode(charset))
        return {child.tag: child.text for child in root}

# Register the codec
registry = get_codec_registry()
registry.register_body_codec(XmlBodyCodec)
```

### Body Decoder Middleware

The `BodyDecoderMiddleware` automatically decodes request bodies:

```python
from cullinan.middleware import BodyDecoderMiddleware, get_decoded_body

# Access decoded body in handlers
class MyController:
    @post_api(url="/data")
    async def handle_data(self):
        body = get_decoded_body(self.request)
        return body
```

## Backward Compatibility

The traditional parameter style is fully supported:

```python
# Traditional style (still works)
@post_api(url="/users", body_params=['name', 'age'])
async def create_user(self, body_params):
    name = body_params.get('name')
    age = body_params.get('age')
```

## Error Handling

Parameter errors return structured responses:

```python
from cullinan.params import ValidationError, ResolveError

# ValidationError for single parameter failures
# ResolveError for multiple parameter failures

# Error response format:
{
    "error": "Parameter validation failed",
    "details": [
        {"param": "age", "error": "must be >= 0", "constraint": "ge:0"}
    ]
}
```

## Best Practices

1. **Use type hints**: Always specify parameter types for clarity
2. **Set sensible defaults**: Provide defaults for optional parameters
3. **Validate early**: Use built-in validators instead of manual checks
4. **Use models for complex bodies**: dataclass for structured request bodies
5. **Use DynamicBody for flexibility**: When body structure varies

## API Reference

### cullinan.params

| Class | Description |
|-------|-------------|
| `Param` | Base parameter class |
| `Path` | URL path parameter |
| `Query` | Query string parameter |
| `Body` | Request body parameter |
| `Header` | HTTP header parameter |
| `File` | File upload parameter |
| `TypeConverter` | Type conversion utility |
| `Auto` | Auto type inference |
| `AutoType` | Auto type marker |
| `DynamicBody` | Dynamic request body container |
| `ParamValidator` | Parameter validation |
| `ModelResolver` | dataclass model resolution |
| `ParamResolver` | Parameter resolution orchestrator |

### cullinan.codec

| Class | Description |
|-------|-------------|
| `BodyCodec` | Request body codec abstract class |
| `ResponseCodec` | Response codec abstract class |
| `JsonBodyCodec` | JSON body decoder |
| `JsonResponseCodec` | JSON response encoder |
| `FormBodyCodec` | Form body decoder |
| `CodecRegistry` | Codec registry |
| `DecodeError` | Decoding error |
| `EncodeError` | Encoding error |

### cullinan.middleware

| Class | Description |
|-------|-------------|
| `BodyDecoderMiddleware` | Auto body decoding middleware |
| `get_decoded_body()` | Get decoded request body |

