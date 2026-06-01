from cullinan import Inject, configure, controller, get_api, module, run, service


@service
class GreetingService:
    def build_message(self) -> str:
        return "Hello from the Cullinan public API."


@controller(url="/hello")
class HelloController:
    greeting_service: "GreetingService" = Inject()

    @get_api(url="")
    def hello(self):
        return {
            "message": self.greeting_service.build_message(),
            "entrypoint": "configure(root_module=...) + run()",
        }


@module(packages=["examples.minimal_app"])
class RootModule:
    """Recommended root boundary for the minimal example."""


def configure_example():
    return configure(root_module=RootModule)


def main():
    configure_example()
    run()
