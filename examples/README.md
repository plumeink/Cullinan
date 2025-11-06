# Cullinan 示例代码

本目录包含 Cullinan 框架的各种使用示例。

## ⚠️ 使用前准备

### 安装 Cullinan

由于最新版本尚未发布到 PyPI，请从源码安装：

```bash
# 从项目根目录安装（开发模式）
pip install -e .

# 或者指定完整路径
pip install -e /path/to/Cullinan
```

### 验证安装

```bash
python -c "import cullinan; print('Cullinan installed successfully')"
```

---

## 目录结构

### 基础示例 (basic/)
- `test_controller.py` - Controller 基础示例

### 配置示例 (config/)
- `config_example.py` - 代码配置方式
- `cullinan.json` - JSON 配置文件示例
- `APP_CONFIG_EXAMPLE.md` - 配置说明文档

### 打包示例 (packaging/)
- `packaging_test.py` - 打包测试应用
- `diagnose_app.py` - 通用诊断工具
- `diagnose.py` - 基础诊断工具
- `nuitka_fix_template.py` - Nuitka 修复模板

## 快速开始

### 1. 基础使用

```python
from cullinan import Application
from cullinan.controller import Controller, request_mapping

@Controller('/api')
class HelloController:
    @request_mapping('/hello', method=['GET'])
    def hello(self, request):
        return {'message': 'Hello, Cullinan!'}

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

### 2. 使用配置（推荐打包时使用）

```python
from cullinan import configure, Application

# 配置用户包
configure(user_packages=['your_app'])

def main():
    app = Application()
    app.run()
```

### 3. 打包测试

运行打包测试示例：
```bash
python examples/packaging/packaging_test.py
```

使用诊断工具：
```bash
python examples/packaging/diagnose_app.py your_app
```

## 详细文档

- [完整配置指南](../docs/zh/CONFIGURATION_GUIDE.md)
- [打包指南](../docs/zh/packaging_guide.md)
- [配置快速参考](../docs/zh/CONFIG_QUICK_REFERENCE.md)
- [故障排查](../docs/zh/TROUBLESHOOTING_PACKAGING.md)

## 示例说明

### basic/ - 基础功能

演示 Cullinan 的基本功能，适合初学者。

### config/ - 配置系统

展示如何使用配置系统，特别是打包场景。

### packaging/ - 打包支持

包含打包测试和诊断工具，帮助你解决打包问题。

## 打包支持

Cullinan 完全支持 Nuitka 和 PyInstaller 打包：

### Nuitka
```bash
nuitka --standalone \
       --include-package=your_app \
       --include-package=cullinan \
       your_app/application.py
```

### PyInstaller
```bash
pyinstaller --onedir \
            --hidden-import=your_app \
            --collect-all=your_app \
            --collect-all=cullinan \
            your_app/application.py
```

## 获取帮助

如有问题，请：
1. 查看 [故障排查文档](../docs/zh/TROUBLESHOOTING_PACKAGING.md)
2. 运行诊断工具
3. 查看 [GitHub Issues](https://github.com/plumeink/Cullinan/issues)

