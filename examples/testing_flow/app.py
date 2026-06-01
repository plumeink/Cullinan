from cullinan import Inject, configure, controller, get_api, module, run, service


@service
class QuoteService:
    def sample(self) -> str:
        return "Public API testing keeps examples stable."


@controller(url="/notes")
class NotesController:
    quote_service: "QuoteService" = Inject()

    @get_api(url="/sample")
    def sample(self):
        return {"message": self.quote_service.sample(), "tested_via": "get_asgi_app()"}


@module(packages=["examples.testing_flow"])
class RootModule:
    """Testing example rooted on the public configuration surface."""


def configure_example():
    return configure(root_module=RootModule)


def main():
    configure_example()
    run()
