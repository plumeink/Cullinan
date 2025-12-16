#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick test for error policy"""

import sys
sys.path.insert(0, 'G:/pj/Cullinan - 副本 (3)')

from cullinan import configure
from cullinan.service import service, Service, get_service_registry, reset_service_registry
import logging

logging.basicConfig(level=logging.WARNING)

print("Testing WARN policy...")
reset_service_registry()
configure(startup_error_policy='warn')

@service
class FailingService(Service):
    def on_init(self):
        raise RuntimeError("Test failure")

@service  
class HealthyService(Service):
    def on_init(self):
        print("HealthyService initialized")

registry = get_service_registry()
try:
    registry.initialize_all()
    print("\n[SUCCESS] initialize_all() completed without raising exception")
except Exception as e:
    print(f"\n[FAIL] initialize_all() raised exception: {e}")
    sys.exit(1)

# Check if healthy service is available
healthy = registry.get_instance('HealthyService')
if healthy:
    print("[SUCCESS] Healthy service is available!")
    print("[SUCCESS] WARN policy works correctly!")
    sys.exit(0)
else:
    print("[FAIL] Healthy service not available")
    sys.exit(1)

