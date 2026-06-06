from cullinan import application, configure


@configure(user_packages=["examples.controller_service_inject"], server_port=4082)
@application
def main(): ...


__all__ = ["main"]

if __name__ == "__main__":
    main()