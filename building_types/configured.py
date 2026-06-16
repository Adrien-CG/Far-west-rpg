"""Batiments configures sans exploitation specifique pour l'instant.

Plan du fichier:
01 - ConfiguredBuilding: classe commune aux nouveaux batiments prives.
02 - ConfiguredPublicBuilding: classe commune aux nouveaux batiments publics.
03 - configured defaults: valeurs initiales sobres en attendant les modalites.
"""

from building_types.base import TypedBuilding


class ConfiguredBuilding(TypedBuilding):
    building_type_name = "Batiment economique"

    def __init__(
        self,
        building_id,
        name,
        owner,
        building_type,
        inventory=None,
        production=None,
        features=None,
        hidden_stats=None,
        upgrades=None,
        current_balance=0,
        under_construction=False,
    ):
        super().__init__(
            building_id=building_id,
            name=name,
            building_type=building_type,
            owner=owner,
            level=1,
            is_public=False,
            features=features or {},
            hidden_stats=hidden_stats or {},
            inventory=inventory or {},
            production=production or {},
            upgrades=upgrades or [],
            current_balance=current_balance,
            under_construction=under_construction,
        )


class ConfiguredPublicBuilding(TypedBuilding):
    building_type_name = "Batiment public"

    def __init__(
        self,
        building_id,
        name,
        owner,
        building_type,
        inventory=None,
        production=None,
        features=None,
        hidden_stats=None,
        upgrades=None,
        current_balance=0,
        under_construction=False,
    ):
        super().__init__(
            building_id=building_id,
            name=name,
            building_type=building_type,
            owner=owner,
            level=1,
            is_public=True,
            features=features or {},
            hidden_stats=hidden_stats or {},
            inventory=inventory or {},
            production=production or {},
            upgrades=upgrades or [],
            current_balance=current_balance,
            under_construction=under_construction,
        )
