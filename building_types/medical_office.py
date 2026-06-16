"""Batiment Cabinet medical.

Plan du fichier:
01 - MedicalOffice: classe de creation du cabinet medical.
02 - build_medical_clinic_offer: exploitation de soins si le joueur s'en occupe.
03 - medical_service_utility: priorite des differents soins.
04 - building_owner_id/player_occupation_matches: petits helpers d'offre.
"""

from building_types.base import TypedBuilding
from goods_services import item_definition, service_base_utility, service_default_price


class MedicalOffice(TypedBuilding):
    building_type_name = "Cabinet médical"

    def __init__(self, building_id, name, owner, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            building_type="Cabinet médical",
            owner=owner,
            level=1,
            inventory={"plantes_medicinales": 0, "remede": 0},
            production={
                "commande_remede": 0,
                "tarif_blessure": service_default_price("soin_blessure"),
                "tarif_blessure_grave": service_default_price("soin_blessure_grave"),
                "tarif_maladie": service_default_price("soin_maladie"),
                "tarif_convalescence": 4,
                "patients": [],
            },
            upgrades=[],
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def city_actions(self, game):
        if "Laboratoire" in self.upgrades:
            return ["Chercher des plantes médicinales"]
        return []

    def building_actions(self, game):
        return ["Préparer un remède"]

    def recruitable_jobs(self, game):
        return ["Infirmière"]

    def generate_offers(self, game):
        return build_medical_clinic_offer(game, self)


def build_medical_clinic_offer(game, building):
    if not player_occupation_matches(game, "clinic_care", building):
        return []
    remedy_stock = building.inventory.get("remede", 0)
    if remedy_stock <= 0:
        return []

    service_specs = [
        ("soin_blessure", building.production.get("tarif_blessure", service_default_price("soin_blessure"))),
        ("soin_blessure_grave", building.production.get("tarif_blessure_grave", service_default_price("soin_blessure_grave"))),
        ("soin_maladie", building.production.get("tarif_maladie", service_default_price("soin_maladie"))),
    ]
    offers = []
    for service_id, price in service_specs:
        data = item_definition(service_id)
        offers.append({
            "type": data["type"],
            "family": data["family"],
            "id": data["id"],
            "label": data["label"],
            "utility": medical_service_utility(data["id"]),
            "price": price,
            "quantity": remedy_stock,
            "building_id": building.building_id,
            "owner_id": building_owner_id(game, building),
            "weight": data["weight"],
            "fractionable": data["fractionable"],
        })
    return offers


def medical_service_utility(service_id):
    return {
        "soin_blessure": 120,
        "soin_blessure_grave": 600,
        "soin_maladie": 500,
    }.get(service_id, service_base_utility(service_id))


def player_occupation_matches(game, occupation_type, building=None):
    occupation = getattr(game, "seasonal_occupation", {}) or {}
    if occupation.get("type") != occupation_type:
        return False
    return not building or occupation.get("building_id") == building.building_id


def building_owner_id(game, building):
    if building.owner == game.character.name:
        return "player"
    owner = next((npc for npc in game.city.population if npc.name == building.owner), None)
    return owner.npc_id if owner else None
