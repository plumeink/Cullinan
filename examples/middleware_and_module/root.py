from cullinan.application import configure, module, run

from . import controllers as _controllers  # noqa: F401
from . import middleware as _middleware  # noqa: F401
from . import services as _services  # noqa: F401


@module(packages=["examples.middleware_and_module"])
class RootModule:
    """Runtime boundary example for package ownership and middleware scope."""


def configure_example():
    return configure(root_module=RootModule)


def main():
    configure_example()
    run()
