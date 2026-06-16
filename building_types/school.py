"""Batiment public Ecole.

Plan du fichier:
01 - School: creation et valeurs de depart.
02 - building_actions: actions publiques a definir.
"""

from building_types.configured import ConfiguredPublicBuilding


class School(ConfiguredPublicBuilding):
    building_type_name = "Ecole"

    def __init__(self, building_id="school_001", name="École", owner="Ville", current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="École",
            inventory={"livre": 0, "papier": 0},
            production={"eleves": []},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def building_actions(self, game):
        return []
