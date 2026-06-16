"""Batiment Comptoir de trappeur.

Plan du fichier:
01 - TrapperPost: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding


class TrapperPost(ConfiguredBuilding):
    building_type_name = "Comptoir de trappeur"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Comptoir de trappeur",
            inventory={"fourrure": 0, "cuir": 0},
            production={"prix_achat": {}, "prix_vente": {}},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
