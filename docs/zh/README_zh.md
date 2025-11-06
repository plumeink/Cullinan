# Cullinan 框架文档

[English](../README.md) | **[中文](README_zh.md)**

欢迎使用 Cullinan！使用 Python 构建生产就绪的 Web 应用程序的完整文档。

---

## 📖 文档索引

### 快速开始
- **[完整指南](00-complete-guide.md)** ⭐ **从这里开始！**  
  包含所有特性的完整教程和示例

### 核心文档

0. [**完整指南**](00-complete-guide.md) 🌟  
   从基础到高级的完整框架指南
   - 安装与设置
   - 快速开始教程 → [示例](../../examples/basic/hello_world.py)
   - 控制器与服务 → [示例](../../examples/basic/crud_example.py)
   - 数据库、WebSocket、钩子
   - API 参考和常见问题

1. [**配置指南**](01-configuration_zh.md)  
   Cullinan 配置完整指南
   - 基础配置 → [示例](../../examples/config/config_example.py)
   - JSON 配置 → [示例](../../examples/config/cullinan.json)
   - 环境变量
   - 打包配置

2. [**打包指南**](02-packaging_zh.md)  
   应用打包部署指南
   - Nuitka 和 PyInstaller 支持
   - 跨平台构建 → [脚本](../../scripts/)
   - 不同打包模式
   - 平台特定说明

3. [**故障排查**](03-troubleshooting.md)  
   常见问题和解决方案
   - 模块未找到错误
   - Controller/Service 注册
   - 打包问题
   - 调试技巧 → [诊断工具](../../examples/packaging/diagnose_app.py)

4. [**快速参考**](04-quick-reference.md)  
   快速参考卡片
   - 配置语法
   - 打包命令
   - 常用模式

5. [**构建脚本**](05-build-scripts_zh.md)  
   构建脚本完整指南
   - 通用构建器 → [build_app.py](../../scripts/build_app.py)
   - 高级 Nuitka → [build_nuitka_advanced.py](../../scripts/build_nuitka_advanced.py)
   - 高级 PyInstaller → [build_pyinstaller_advanced.py](../../scripts/build_pyinstaller_advanced.py)
   - 跨平台支持
   - 编译器选项

6. [**sys.path 自动处理**](06-sys-path-auto-handling_zh.md) 🆕  
   项目根目录自动检测
   - 无需手动 `sys.path.append`
   - 简化的启动代码
   - 自动检测逻辑说明
   - 从旧方法迁移指南

---

## 🚀 快速开始

### 1. 安装

```bash
pip install cullinan
```

### 2. 创建第一个应用

```python
# app.py
from cullinan import configure, application
from cullinan.controller import controller, get_api

configure(user_packages=['__main__'])

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        return {'message': '你好，Cullinan！'}

if __name__ == '__main__':
    application.run()
```

**📝 完整示例：** [`examples/basic/hello_world.py`](../../examples/basic/hello_world.py)

### 3. 运行和测试

```bash
python app.py
# 访问: http://localhost:8080/api/hello
```

---

## 💡 示例目录

所有示例位于 [`examples/`](../../examples/)：

### 基础示例
- [`hello_world.py`](../../examples/basic/hello_world.py) - 最简单的应用
- [`crud_example.py`](../../examples/basic/crud_example.py) - 完整的 CRUD API
- [`test_controller.py`](../../examples/test_controller.py) - 控制器模式

### 配置示例
- [`config_example.py`](../../examples/config/config_example.py) - 代码配置
- [`cullinan.json`](../../examples/config/cullinan.json) - JSON 配置
- [`APP_CONFIG_EXAMPLE.md`](../../examples/APP_CONFIG_EXAMPLE.md) - 配置文档

### 打包示例
- [`packaging_test.py`](../../examples/packaging/packaging_test.py) - 打包测试
- [`diagnose_app.py`](../../examples/packaging/diagnose_app.py) - 诊断工具

---

## 🔗 按任务快速链接

### 我想要...

**快速开始**  
→ [完整指南](00-complete-guide.md) → [Hello World](../../examples/basic/hello_world.py)

**配置应用**  
→ [配置指南](01-configuration_zh.md) → [配置示例](../../examples/config/config_example.py)

**构建 REST API**  
→ [完整指南：控制器](00-complete-guide.md#控制器与路由) → [CRUD 示例](../../examples/basic/crud_example.py)

**打包部署**  
→ [打包指南](02-packaging_zh.md) → [构建脚本](05-build-scripts_zh.md)

**修复打包问题**  
→ [故障排查](03-troubleshooting_zh.md) → [诊断工具](../../examples/packaging/diagnose_app.py)

**使用构建脚本**  
→ [构建脚本指南](05-build-scripts_zh.md) → [脚本目录](../../scripts/)

---

## 🧪 测试

运行测试套件：

```bash
# 基础测试
python run_tests.py

# 生成覆盖率
python run_tests.py --coverage

# 详细输出
python run_tests.py --verbose

# 检查依赖
python run_tests.py --check-deps
```

---

## 📦 文件结构

```
docs/
├── README.md                    # 英文文档索引
├── 00-complete-guide.md         # 完整框架指南（英文）
├── ... (其他英文文档)
└── zh/                          # 中文文档目录
    ├── README_zh.md             # 本文件 - 中文文档索引
    ├── 00-complete-guide_zh.md  # ⭐ 完整框架指南
    ├── 01-configuration_zh.md   # 配置系统
    ├── 02-packaging_zh.md       # 打包和部署
    ├── 03-troubleshooting_zh.md # 常见问题和解决方案
    ├── 04-quick-reference_zh.md # 快速命令参考
    ├── 05-build-scripts_zh.md   # 构建脚本指南
    └── 06-sys-path-auto-handling_zh.md # sys.path 自动处理

examples/
├── basic/
│   ├── hello_world.py
│   ├── crud_example.py
│   └── test_controller.py
├── config/
│   ├── config_example.py
│   └── cullinan.json
└── packaging/
    ├── packaging_test.py
    └── diagnose_app.py

scripts/
├── build_app.py                # 通用构建器
├── build_nuitka_advanced.py    # 高级 Nuitka
└── build_pyinstaller_advanced.py # 高级 PyInstaller
```

---

## 🆘 获取帮助

- **GitHub Issues**: [报告错误](https://github.com/plumeink/Cullinan/issues)
- **Discussions**: [提问交流](https://github.com/plumeink/Cullinan/discussions)
- **文档**: [阅读文档](00-complete-guide.md)
- **示例**: [浏览示例](../../examples/)

---

## 📄 许可证

Cullinan 是开源软件，使用 MIT 许可证。

详见 [LICENSE](../../LICENSE)。

---

**祝你使用 Cullinan 编码愉快！🎉**

