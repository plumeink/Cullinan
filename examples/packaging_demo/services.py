# Example: Cullinan @service components for packaging demo
from cullinan import service


@service
class GreetingService:
    """Example service demonstrating DI registration in frozen environments."""

    def greet(self, name: str = "World") -> str:
        return f"Hello, {name} from Cullinan!"


@service
class CounterService:
    """Example service with state, verifying singleton behavior in frozen builds."""

    def __init__(self):
        self._count = 0

    def increment(self) -> int:
        self._count += 1
        return self._count

    @property
    def count(self) -> int:
        return self._count
