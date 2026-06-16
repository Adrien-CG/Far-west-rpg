"""Batiment public Fort.

Plan du fichier:
01 - Fort: creation et valeurs de depart.
02 - building_actions: actions publiques a definir.
"""

from building_types.configured import ConfiguredPublicBuilding


class Fort(ConfiguredPublicBuilding):
    building_type_name = "Fort"

    def __init__(self, building_id="fort_001", name="Fort", owner="Ville", current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            owner=owner,
            building_type="Fort",
            inventory={},
            production={"garnison": 0},
            hidden_stats={"securite": 0},
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def building_actions(self, game):
        return []
