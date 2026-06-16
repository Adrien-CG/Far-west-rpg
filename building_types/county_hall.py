"""Batiment public County hall.

Plan du fichier:
01 - CountyHall: creation et valeurs de depart.
02 - building_actions: actions publiques a definir.
"""

from building_types.configured import ConfiguredPublicBuilding


class CountyHall(ConfiguredPublicBuilding):
    building_type_name = "County hall"

    def __init__(self, building_id="county_hall_001", name="County hall", owner="Ville", current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="County hall",
            inventory={},
            production={"taxes": 0, "decisions": []},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def building_actions(self, game):
        return []
    
    
