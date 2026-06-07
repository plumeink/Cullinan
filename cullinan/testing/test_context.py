# -*- coding: utf-8 -*-
"""Test utilities for mocking frozen dependencies.

After Cullinan injects dependencies, attributes are immutable by default
(see :func:`~cullinan.core.application_context._freeze_dependencies`).
``TestContext`` provides the canonical bypass for testing scenarios.

Usage::

    from cullinan.testing import TestContext

    ctx = ApplicationContext()
    # ... register definitions, ctx.refresh()
    svc = ctx.get("UserService")

    # Permanent replacement
    TestContext.mock_permanently(svc, 'database', mock_db)

    # Temporary replacement (auto-restore)
    with TestContext.mock(svc, 'database', mock_db):
        result = svc.database_query()
"""


class TestContext:
    """Test helper for mocking frozen DI dependencies.

    All methods use ``object.__setattr__`` to bypass the frozen
    ``__setattr__`` guard installed by
    :func:`~cullinan.core.application_context._freeze_dependencies`.

    Example::

        from cullinan.testing import TestContext

        # Permanent mock
        TestContext.mock_permanently(svc, 'db', mock_db)

        # Context manager (auto-restore)
        with TestContext.mock(svc, 'db', mock_db):
            assert svc.db is mock_db
        # Original restored here
    """

    @staticmethod
    def mock_permanently(instance, attr_name: str, value):
        """Replace a frozen dependency permanently (no restore)."""
        object.__setattr__(instance, attr_name, value)

    @staticmethod
    def mock(instance, attr_name: str, mock_value):
        """Context manager that temporarily replaces a frozen dependency.

        Returns a :class:`_MockContext` that restores the original
        dependency on exit.

        Usage::

            with TestContext.mock(svc, 'db', mock_db):
                # mock_db is active
                ...
            # Original db restored
        """
        original = getattr(instance, attr_name)
        object.__setattr__(instance, attr_name, mock_value)
        return _MockContext(instance, attr_name, original)


class _MockContext:
    """Internal context manager for temporary mock replacement."""

    __slots__ = ('instance', 'attr_name', 'original')

    def __init__(self, instance, attr_name: str, original):
        self.instance = instance
        self.attr_name = attr_name
        self.original = original

    def __enter__(self):
        return self.instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        object.__setattr__(self.instance, self.attr_name, self.original)
        return False
