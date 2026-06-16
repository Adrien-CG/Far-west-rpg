"""Batiment Restaurant.

Plan du fichier:
01 - Restaurant: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding
from goods_services import service_default_price


class Restaurant(ConfiguredBuilding):
    building_type_name = "Restaurant"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Restaurant",
            inventory={"vivres_secs": 0, "vivres_frais": 0},
            production={"prix_repas": service_default_price("repas")},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
