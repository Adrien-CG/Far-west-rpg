"""Batiment Charpentier.

Plan du fichier:
01 - Carpenter: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding


class Carpenter(ConfiguredBuilding):
    building_type_name = "Charpentier"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Charpentier",
            inventory={"bois": 0, "planche": 0, "outils": 0},
            production={"commandes": []},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
