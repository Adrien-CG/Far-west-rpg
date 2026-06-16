"""Batiment Camp de bucheron.

Plan du fichier:
01 - LumberCamp: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding


class LumberCamp(ConfiguredBuilding):
    building_type_name = "Camp de bucheron"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Camp de bucheron",
            inventory={"bois": 0},
            production={"zone_de_coupe": 0, "stock_production": {}},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
