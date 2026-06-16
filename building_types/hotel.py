"""Batiment Hotel.

Plan du fichier:
01 - Hotel: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding
from goods_services import service_default_price


class Hotel(ConfiguredBuilding):
    building_type_name = "Hotel"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Hôtel",
            inventory={"vivres_secs": 0},
            production={"prix_chambre": service_default_price("chambre"), "housing_mode": "location"},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
