from cullinan import application, configure


@configure(user_packages=["examples.parameter_handling"])
@application
def main(): ...


__all__ = ["main"]
