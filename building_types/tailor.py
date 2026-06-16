"""Batiment Tailleur.

Plan du fichier:
01 - Tailor: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding


class Tailor(ConfiguredBuilding):
    building_type_name = "Tailleur"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Tailleur",
            inventory={"tissu": 0, "laine": 0, "coton": 0, "soie": 0},
            production={"prix_habits": {}},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
