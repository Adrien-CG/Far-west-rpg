"""Batiment Marechal ferrant.

Plan du fichier:
01 - Farrier: creation et valeurs de depart.
02 - recruitable_jobs: emplois a definir avec les modalites.
"""

from building_types.configured import ConfiguredBuilding
from goods_services import service_default_price


class Farrier(ConfiguredBuilding):
    building_type_name = "Marechal ferrant"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Maréchal ferrant",
            inventory={"outils": 0, "fer": 0},
            production={
                "prix_ferrage": service_default_price("ferrage"),
                "prix_soins_equestres": service_default_price("soins_equestres"),
            },
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return []
