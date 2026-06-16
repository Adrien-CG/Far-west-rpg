"""Batiment Banque.

Plan du fichier:
01 - Bank: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding


class Bank(ConfiguredBuilding):
    building_type_name = "Banque"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Banque",
            inventory={},
            production={"depots": 0, "prets": []},
            hidden_stats={"securite_coffre": 0},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
