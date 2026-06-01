from cullinan.application import configure, module, run

from . import controllers as _controllers  # noqa: F401


@module(packages=["examples.parameter_handling"])
class RootModule:
    """Parameter-system example bound to controller methods."""


def configure_example():
    return configure(root_module=RootModule)


def main():
    configure_example()
    run()
