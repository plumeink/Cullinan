# -*- coding: utf-8 -*-
"""
DEPRECATED: Old service module (v0.6.x)

This module is deprecated as of v0.7.0. Please use cullinan.service_new instead.

For migration, replace:
    from cullinan.service import service, Service
With:
    from cullinan import service, Service

The new service layer includes:
- Dependency injection support
- Lifecycle hooks (on_init, on_destroy)
- Enhanced registry pattern
- Better testability

See migration guide in docs/ for details.
"""

import warnings

# Keep old implementation for backward compatibility but warn users
warnings.warn(
    "cullinan.service is deprecated. Use 'from cullinan import service, Service' instead. "
    "The old service module will be removed in v0.8.0.",
    DeprecationWarning,
    stacklevel=2
)

service_list = {}


class Service(object):
    """DEPRECATED: Use cullinan.Service (from service_new module) instead."""
    pass


def service(cls):
    """DEPRECATED: Use @service decorator from cullinan.service_new instead."""
    if service_list.get(cls.__name__, None) is None:
        service_list[cls.__name__] = cls()
