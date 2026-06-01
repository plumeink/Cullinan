from cullinan import service


@service
class InventoryService:
    def summary(self):
        return {
            "module_boundary": "examples.middleware_and_module",
            "items": ["apples", "oranges", "pears"],
        }

