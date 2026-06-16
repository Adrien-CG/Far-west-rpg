from building_types.base import TypedBuilding
from buildings import employee_contract


class SheriffOffice(TypedBuilding):
    building_type_name = "Bureau du sherif"

    def __init__(self, building_id="sheriff_office_001", owner="Ville", current_balance=60):
        super().__init__(
            building_id=building_id,
            name="Bureau du sherif",
            building_type="Bureau du sherif",
            owner=owner,
            level=1,
            is_public=True,
            employees=["npc_deputy_001"],
            employee_contracts={"npc_deputy_001": employee_contract("Adjoint du sherif", 9)},
            current_balance=current_balance,
        )

    def building_actions(self, game):
        return ["Regarder les primes", "Candidater pour le bureau du shériff"]
