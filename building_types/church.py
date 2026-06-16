from building_types.base import TypedBuilding
from buildings import employee_contract


class Church(TypedBuilding):
    building_type_name = "Église"

    def __init__(self, building_id="church_001", owner="Ville", current_balance=30):
        super().__init__(
            building_id=building_id,
            name="Église",
            building_type="Église",
            owner=owner,
            level=1,
            is_public=True,
            employees=["npc_pastor_001"],
            employee_roles={"npc_pastor_001": "Pasteur"},
            employee_contracts={"npc_pastor_001": employee_contract("Pasteur", 10)},
            production={"donations": 10},
            current_balance=current_balance,
        )

    def building_actions(self, game):
        return ["Faire un don", "Assister à la messe"]
