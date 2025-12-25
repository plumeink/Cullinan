# -*- coding: utf-8 -*-
"""Service decorators for Cullinan framework.

v0.90: This module now re-exports the new decorator system from cullinan.core.
The API remains the same, so existing code continues to work.

Usage:
    from cullinan.service import service

    @service
    class UserService:
        pass

    # Or with parameters
    @service(name="customService", scope="prototype")
    class AnotherService:
        pass
"""

# Re-export from the new decorator system
from cullinan.core.decorators import service, Inject, InjectByName, Lazy

__all__ = ['service', 'Inject', 'InjectByName', 'Lazy']
