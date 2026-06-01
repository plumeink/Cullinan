# -*- coding: utf-8 -*-
"""Test backward compatible imports."""
import warnings
warnings.filterwarnings('ignore')

import pytest
from cullinan.core.pending import PendingRegistry

class TestBackwardCompatibleImports:
    """Test that old import paths still work."""
    
    def setup_method(self):
        PendingRegistry.reset()
    
    def teardown_method(self):
        PendingRegistry.reset()
    
    def test_import_from_cullinan_service(self):
        """Test import from cullinan.core.services."""
        from cullinan.core.services import service, Inject
        
        @service
        class TestService:
            pass
        
        pending = PendingRegistry.get_instance()
        assert pending.count == 1
        assert pending.contains("TestService")
    
    def test_import_from_cullinan_controller(self):
        """Test import from cullinan.web.controller."""
        from cullinan.web.controller import controller
        
        @controller(url="/api/test")
        class TestController:
            pass
        
        pending = PendingRegistry.get_instance()
        assert pending.count == 1
        assert pending.contains("TestController")
    
    def test_import_from_cullinan_core(self):
        """Test import from cullinan.core."""
        from cullinan.core import service, controller, Inject
        
        @service
        class MyService:
            pass
        
        @controller(url="/api")
        class MyController:
            my_service: MyService = Inject()
        
        pending = PendingRegistry.get_instance()
        assert pending.count == 2

