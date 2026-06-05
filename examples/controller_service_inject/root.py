from cullinan import application, configure


@configure(user_packages=["examples.controller_service_inject"])
@application
def main(): ...


__all__ = ["main"]
