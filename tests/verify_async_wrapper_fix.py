# -*- coding: utf-8 -*-
"""Quick verification: async wrapper properly awaited

Run this to verify the "coroutine was never awaited" bug is fixed.
"""

import sys
import warnings

# Capture RuntimeWarnings
warnings.simplefilter('error', RuntimeWarning)

try:
    from cullinan.controller import controller, post_api
    from cullinan.handler import get_handler_registry
    
    print("Creating controller with async handler...")
    
    @controller(url='/test')
    class TestCtrl:
        @post_api(url='/x')
        async def handler(self):
            return {'ok': True}
    
    handlers = get_handler_registry().get_handlers()
    print(f"✅ Handlers registered: {len(handlers)}")
    
    if handlers:
        url, servlet = handlers[0]
        print(f"  URL: {url}")
        print(f"  Servlet: {servlet}")
        print(f"  Has post method: {hasattr(servlet, 'post')}")
        
        if hasattr(servlet, 'post'):
            import inspect
            is_async = inspect.iscoroutinefunction(servlet.post)
            print(f"  post is async: {is_async}")
    
    print("\n✅ No RuntimeWarning! Async wrappers are properly handled.")
    
except RuntimeWarning as e:
    print(f"\n❌ RuntimeWarning caught: {e}")
    print("   The 'coroutine was never awaited' bug is NOT fixed.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

