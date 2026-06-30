from cullinan import application, configure


@configure(user_packages=["examples.parameter_handling"], server_port=4084)
@application
def main(): ...


__all__ = ["main"]
