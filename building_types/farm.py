"""Batiment Ferme.

Plan du fichier:
01 - Farm: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding


class Farm(ConfiguredBuilding):
    building_type_name = "Ferme"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Ferme",
            inventory={"vivres_secs": 0},
            production={"surface_cultivee": 0, "stock_production": {}},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
