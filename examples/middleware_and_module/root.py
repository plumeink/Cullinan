from cullinan import application, configure, module


@module(packages=["examples.middleware_and_module"])
class MiddlewareBoundary:
    """Advanced runtime boundary for the middleware example."""


@configure(user_packages=["examples.middleware_and_module"], server_port=4083)
@application(modules=[MiddlewareBoundary])
def main(): ...


__all__ = ["MiddlewareBoundary", "main"]
