from typing import TYPE_CHECKING

from cullinan import Inject, controller, get_api

if TYPE_CHECKING:
    from .services import InventoryService


@controller(url="/inventory")
class InventoryController:
    inventory_service: "InventoryService" = Inject()

    @get_api(url="/summary")
    def summary(self):
        return self.inventory_service.summary()

