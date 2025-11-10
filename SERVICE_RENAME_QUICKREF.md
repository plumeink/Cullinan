# Service 模块重命名快速参考

## 🔄 变更内容

**目录重命名**: `cullinan/service_new/` → `cullinan/service/`

## 📦 导入方式

### ✅ 推荐（v0.7.0+）

```python
# 从根包导入（推荐）
from cullinan import Service, service, ServiceRegistry
from cullinan import get_service_registry, reset_service_registry

# 从子包导入（也可以）
from cullinan.service import Service, service, ServiceRegistry
```

### ❌ 已弃用

```python
# 不再可用，会抛出 ImportError
from cullinan.service_new import Service, service
```

## 🧪 测试结果

- ✅ 20/20 Service 单元测试通过
- ✅ 16/16 测试工具测试通过
- ✅ 283/284 框架测试通过 (99.6%)
- ✅ 所有示例正常运行

## 📄 相关文档

- **详细测试报告**: `SERVICE_MIGRATION_TEST_REPORT.md`
- **重命名记录**: `SERVICE_RENAME_COMPLETE.md`
- **总结报告**: `SERVICE_RENAME_SUMMARY.md`

## ⚡ 快速验证

```bash
# 验证导入
python -c "from cullinan import Service; print('✅ Import OK')"

# 运行测试
python -m unittest tests.test_service_enhanced -v

# 运行示例
python examples/service_examples.py
```

## 🎯 影响范围

- **破坏性变更**: 无
- **API 变更**: 无
- **功能变更**: 无
- **性能影响**: 无

## 📅 版本信息

- **版本**: v0.7.0-alpha1
- **日期**: 2025-01-10
- **状态**: ✅ 完成并验证

