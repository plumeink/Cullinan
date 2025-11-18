title: "cullinan.application 模块"
slug: "modules-application"
module: ["cullinan.application"]
tags: ["api", "module", "application"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/modules/application.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# cullinan.application

摘要：`cullinan.application` 模块文档占位。包含公有类、典型用法，及相关测试/示例链接。

建议记录的公有符号：Application，start，stop

示例用法：

（占位：展示典型 Application 使用的最小代码片段）

## 示例

### Hello HTTP（烟雾测试示例）

仓库包含一个最小示例 `examples/hello_http.py`，用于文档中的烟雾测试。该示例通过 Cullinan 的 handler registry 注册一个简单的 Tornado 处理器，启动一个短时 HTTP 服务器，发起一次验证请求，然后退出。

PowerShell（Windows）运行命令：

```powershell
pip install -U pip
pip install cullinan tornado
python examples\hello_http.py
```

观察到的输出（节选）：

```
INFO:__main__:Starting IOLoop... (will stop after one verification request)
INFO:__main__:Async Requesting http://127.0.0.1:4080/hello
INFO:tornado.access:200 GET /hello (127.0.0.1) 0.50ms
INFO:__main__:Response status: 200
INFO:__main__:Response body: Hello Cullinan
INFO:__main__:IOLoop stopped, exiting
```

说明：该示例适合用作文档或 CI 的烟雾测试（启动、验证请求、退出）。
