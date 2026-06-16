"""Batiment Barber shop.

Plan du fichier:
01 - BarberShop: classe de creation du barber.
02 - build_barber_shop_offer: offre de coupe.
03 - building_owner_id: retrouve le proprietaire pour encaisser plus tard.
"""

from building_types.base import TypedBuilding
from buildings import employee_contract
from goods_services import item_definition


class BarberShop(TypedBuilding):
    building_type_name = "Barber shop"

    def __init__(self, building_id, owner, current_balance=50, employees=None, under_construction=False):
        employees = employees or ["npc_barber_surgeon_001"]
        super().__init__(
            building_id=building_id,
            name="Barber shop",
            building_type="Barber shop",
            owner=owner,
            level=1,
            employees=employees,
            employee_roles={employee_id: "Chirurgien barbier" for employee_id in employees},
            employee_contracts={
                employee_id: employee_contract("Chirurgien barbier", 12)
                for employee_id in employees
            },
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def building_actions(self, game):
        return ["Se faire couper", "Se faire soigner"]

    def generate_offers(self, game):
        return build_barber_shop_offer(game, self)


def build_barber_shop_offer(game, building):
    data = item_definition("coupe")
    return [{
        "type": data["type"],
        "family": data["family"],
        "id": data["id"],
        "label": data["label"],
        "utility": data["utility"],
        "price": data["base_price"],
        "quantity": float("inf"),
        "building_id": building.building_id,
        "owner_id": building_owner_id(game, building),
        "weight": data["weight"],
        "fractionable": data["fractionable"],
    }]


def building_owner_id(game, building):
    if building.owner == game.character.name:
        return "player"
    owner = next((npc for npc in game.city.population if npc.name == building.owner), None)
    return owner.npc_id if owner else None
