from building_types.base import TypedBuilding
from buildings import employee_contract


class PostOffice(TypedBuilding):
    building_type_name = "Post Office"

    def __init__(self, building_id="post_office_001", owner="Ville", current_balance=40):
        super().__init__(
            building_id=building_id,
            name="Post Office",
            building_type="Post Office",
            owner=owner,
            level=1,
            is_public=True,
            employees=["npc_post_worker_001"],
            employee_contracts={"npc_post_worker_001": employee_contract("Employe du Post Office", 8)},
            current_balance=current_balance,
        )

    def building_actions(self, game):
        return ["Poster une annonce pour un emploi"]
