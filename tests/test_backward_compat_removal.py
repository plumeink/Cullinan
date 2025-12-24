# -*- coding: utf-8 -*-
"""Test backward compatibility removal - verify new injection model works

Author: Plumeink
Date: 2025-12-24
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from cullinan.core import Inject, InjectByName, injectable, get_injection_registry
from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor
from cullinan.service import service, ServiceRegistry

logger = logging.getLogger(__name__)


# Test services
@service
class DatabaseService:
    def __init__(self):
        self.name = "DatabaseService"
    
    def query(self, sql: str):
        return f"Result: {sql}"


@service
class CacheService:
    def __init__(self):
        self.name = "CacheService"
    
    def get(self, key: str):
        return f"Cached: {key}"


def test_new_injection_model():
    """Test that new injection model works without backward compatibility"""
    logger.info("=" * 80)
    logger.info("Testing New Injection Model (No Backward Compatibility)")
    logger.info("=" * 80)
    
    # Setup
    logger.info("\n[1] Setting up registries...")
    injection_registry = get_injection_registry()
    service_registry = ServiceRegistry(auto_register=True)  # This uses add_provider_source now
    
    # Initialize InjectionExecutor
    logger.info("[2] Initializing InjectionExecutor...")
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)
    logger.info("✓ InjectionExecutor initialized")
    
    # Register services
    logger.info("\n[3] Registering services...")
    service_registry.register('DatabaseService', DatabaseService)
    service_registry.register('CacheService', CacheService)
    logger.info(f"✓ Registered {service_registry.count()} services")
    
    # Test Inject()
    logger.info("\n[4] Testing Inject() descriptor...")
    @injectable
    class TestController1:
        database: DatabaseService = Inject()
        
        def test(self):
            return self.database.query("SELECT * FROM users")
    
    controller1 = TestController1()
    result1 = controller1.test()
    assert "SELECT * FROM users" in result1
    logger.info(f"✓ Inject() works: {result1}")
    
    # Test InjectByName()
    logger.info("\n[5] Testing InjectByName() descriptor...")
    @injectable
    class TestController2:
        cache = InjectByName('CacheService')
        
        def test(self):
            return self.cache.get('user_123')
    
    controller2 = TestController2()
    result2 = controller2.test()
    assert "user_123" in result2
    logger.info(f"✓ InjectByName() works: {result2}")
    
    # Test @injectable with mixed injection
    logger.info("\n[6] Testing @injectable with mixed injection...")
    @injectable
    class TestController3:
        database: DatabaseService = Inject()
        cache = InjectByName('CacheService')
        
        def test(self):
            db_result = self.database.query("SELECT count(*)")
            cache_result = self.cache.get('count')
            return f"{db_result} | {cache_result}"
    
    controller3 = TestController3()
    result3 = controller3.test()
    assert "SELECT count(*)" in result3
    assert "count" in result3
    logger.info(f"✓ Mixed injection works: {result3}")
    
    # Test optional dependencies
    logger.info("\n[7] Testing optional dependencies...")
    @injectable
    class TestController4:
        database: DatabaseService = Inject()
        missing = InjectByName('MissingService', required=False)
        
        def test(self):
            db_result = self.database.query("SELECT 1")
            missing_result = "None" if self.missing is None else "Found"
            return f"{db_result} | Missing: {missing_result}"
    
    controller4 = TestController4()
    result4 = controller4.test()
    assert "SELECT 1" in result4
    assert "Missing: None" in result4
    logger.info(f"✓ Optional dependencies work: {result4}")
    
    # Verify cache stats
    logger.info("\n[8] Checking executor cache stats...")
    stats = executor.get_cache_stats()
    logger.info(f"✓ Total cached: {stats['total_cached']}, instances: {stats['instances']}")

    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS PASSED! ✓")
    logger.info("Backward compatibility successfully removed!")
    logger.info("=" * 80)
    
    return True


if __name__ == '__main__':
    try:
        success = test_new_injection_model()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

