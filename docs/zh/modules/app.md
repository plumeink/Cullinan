title: "cullinan.app 模块"
slug: "modules-app"
module: ["cullinan.app"]
tags: ["api", "module"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/modules/app.md"
related_tests: []
related_examples: []
estimate_pd: 0.8
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# cullinan.app

摘要：`cullinan.app` 模块文档占位。描述入口点以及如何创建应用实例。

建议记录的公有符号：App，main（如存在）

## 公共 API（自动生成）

<!-- generated: docs/work/generated_modules/cullinan_app.md -->

### cullinan.app

| 名称 | 类型 | 签名 / 值 |
| --- | --- | --- |
| `CullinanApplication` | class | `CullinanApplication(shutdown_timeout: int = 30)` |
| `create_app` | function | `create_app(shutdown_timeout: int = 30) -> cullinan.app.CullinanApplication` |

## 示例：创建并运行应用

```python
# 示例：创建并运行最小 Cullinan 应用
from cullinan.app import create_app

app = create_app()
# 注意：app.run() 会启动 IOLoop 并阻塞直到接收到关闭信号
# 在实际的 CLI 入口中使用它（不要在库的单元测试中直接调用）
# app.run()

# 若需编程化控制，可以使用 startup/shutdown:
# import asyncio
# asyncio.run(app.startup())
# asyncio.run(app.shutdown())
```

说明：`CullinanApplication.run()` 会注册信号处理器并启动 Tornado 的 IOLoop；在 CLI 入口调用。测试或程序化控制请用 `create_app()` 创建实例。
