# -*- coding: utf-8 -*-
"""构造注入演示（Issue 6）.

运行方式::

    cd G:/pj/Cullinan_aiasset && python examples/constructor_injection_demo.py

核心演示：裸类型注解 = 构造函数注入，零样板代码。
"""

from cullinan.core.application_context import ApplicationContext
from cullinan.core.definitions import Definition, ScopeType


# ── 服务定义 ──────────────────────────────────────────────────────────

class DatabaseService:
    def query(self, sql: str) -> str:
        return f"result: [{sql}]"


class CacheService:
    def get(self, key: str) -> str:
        return f"cached({key})"


# ═══════════════════════════════════════════════════════════════════════
# 构造注入 — 无需 Inject()
# ═══════════════════════════════════════════════════════════════════════

class ReportService:
    database: DatabaseService   # ← 一行声明，框架自动注入
    cache: CacheService         # ← 无需 __init__，无需 self.x = x


class OptionalService:
    database: DatabaseService          # 必需
    notifier: "SomeNotifier" = None    # Optional — 未注册也 OK（= None）


# ═══════════════════════════════════════════════════════════════════════
# 混合构造注入 + field injection
# ═══════════════════════════════════════════════════════════════════════

from cullinan.core.decorators import Inject

class MixedService:
    database: DatabaseService          # ← 构造注入
    cache: CacheService = Inject()     # ← 传统 field injection (共存)


# ── 主程序 ────────────────────────────────────────────────────────────

def _reg(ctx, cls, name):
    """Helper: register a service in context."""
    ctx.register(Definition(
        name=name, factory=lambda c: c._create_class_instance(cls),
        scope=ScopeType.SINGLETON, source="demo", type_=cls,
    ))


def main():
    ctx = ApplicationContext()

    # 注册依赖（生产环境中由 @service + 扫描自动完成）
    _reg(ctx, DatabaseService, "db")
    _reg(ctx, CacheService, "cache")
    _reg(ctx, ReportService, "report")
    _reg(ctx, OptionalService, "optsvc")
    _reg(ctx, MixedService, "mixed")
    ctx.refresh()

    # ── 构造注入 ──
    report = ctx.get("report")
    print(f"[构造注入] ReportService.database = {report.database}")
    print(f"[构造注入] query → {report.database.query('SELECT 2')}")
    print(f"[构造注入] ReportService.cache   = {report.cache}")

    # ── Optional DI ──
    opt = ctx.get("optsvc")
    print(f"[Optional]  database = {opt.database}")
    print(f"[Optional]  notifier = {opt.notifier}")  # None

    # ── 混合 ──
    mixed = ctx.get("mixed")
    print(f"[混合模式] database ({type(mixed.database).__name__}) 来自构造注入")
    print(f"[混合模式] cache   ({type(mixed.cache).__name__}) 来自 field injection")

    ctx.shutdown()
    print("\n[OK] 构造注入演示完成。")


if __name__ == "__main__":
    main()
