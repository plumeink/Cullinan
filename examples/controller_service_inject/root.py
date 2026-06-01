from cullinan import configure, module, run

from . import controllers as _controllers  # noqa: F401
from . import services as _services  # noqa: F401


@module(packages=["examples.controller_service_inject"])
class RootModule:
    """Business-layer example using controller, service, and Inject()."""


def configure_example():
    return configure(root_module=RootModule)


def main():
    configure_example()
    run()

