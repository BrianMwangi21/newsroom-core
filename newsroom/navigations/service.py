from superdesk import get_resource_service

from newsroom.types import NavigationModel
from newsroom.core.resources.service import NewshubAsyncResourceService


class NavigationsService(NewshubAsyncResourceService[NavigationModel]):
    resource_name = "navigations"

    async def on_delete(self, doc: NavigationModel):
        """Remove references in products to this navigation entry once it is deleted"""

        await super().on_delete(doc)

        navigation = doc.id
        products = get_resource_service("products").find(where={"navigations": str(navigation)})

        for product in products:
            product["navigations"].remove(navigation)
            get_resource_service("products").patch(product["_id"], product)
