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
# 快速（推荐）: 在入口脚本使用 framework 入口函数
from cullinan import application

if __name__ == '__main__':
    application.run()

# 高级（可选）: 编程化控制（例如在测试或需要添加关闭处理器时）
from cullinan.app import create_app

application_instance = create_app()
# 现在可以以编程方式调用 application_instance.startup()/application_instance.shutdown() 或 application_instance.add_shutdown_handler(...)
# application_instance.run()  # 在 CLI 入口调用
```

说明：`CullinanApplication.run()` 会注册信号处理器并启动 Tornado 的 IOLoop；在 CLI 入口调用。测试或程序化控制请用 `create_app()` 创建实例。
