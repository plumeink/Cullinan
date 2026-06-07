# Example: Cullinan @controller components for packaging demo
from cullinan.core.decorators import controller


@controller
class HomeController:
    """Example controller demonstrating DI registration in frozen environments."""

    def index(self) -> dict:
        return {"status": "ok", "message": "Packaging demo is running!"}

    def health(self) -> dict:
        return {"status": "healthy"}
