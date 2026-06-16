"""Batiment General Store.

Plan du fichier:
01 - GeneralStore: classe de creation du magasin general.
02 - general_store_goods: biens vendus par defaut.
03 - stock helpers: quantites d'armes et capacite.
04 - price helpers: prix achat/vente du magasin.
05 - build_general_store_offers: exploitation du magasin.
"""

from building_types.base import TypedBuilding
from economy import market_price, transport_cost
from goods_services import ITEM_CATALOG, item_definition, item_id
import random


class GeneralStore(TypedBuilding):
    building_type_name = "General Store"

    def __init__(self, building_id, name, owner, inventory=None, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            building_type="General Store",
            owner=owner,
            level=1,
            inventory=inventory or {},
            production={
                "storage_capacity": 400,
                "sale_prices": {},
                "listed_goods": [],
            },
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def building_actions(self, game):
        return ["Acheter", "Vendre"]

    def recruitable_jobs(self, game):
        return ["Commis"]

    def generate_offers(self, game):
        return build_general_store_offers(game, self)


GENERAL_STORE_EXTRA_GOODS = {"materiel_prospection"}
LIMITED_GENERAL_STORE_GOODS = {"colt_navy", "fusil_springfield", "carabine_spencer"}


def general_store_goods():
    """Biens vendables par defaut dans le General Store."""
    return [
        item
        for item, data in ITEM_CATALOG.items()
        if data.get("type") == "bien"
        and data.get("saturation") != 0
        and data.get("family") not in ["medecine", "intermediaire"]
    ] + sorted(GENERAL_STORE_EXTRA_GOODS)


def refresh_general_store_weapon_offer_stock(building):
    for good_id in LIMITED_GENERAL_STORE_GOODS:
        building.inventory.setdefault(good_id, random_weapon_quantity(good_id))


def random_weapon_quantity(good_id):
    if good_id == "colt_navy":
        return random.randint(2, 4)
    if good_id == "carabine_spencer":
        return random.randint(1, 2)
    if good_id == "fusil_springfield":
        return random.randint(5, 7)
    return 0


def general_store_available_quantity(building, good_id):
    good_id = item_id(good_id)
    if good_id in LIMITED_GENERAL_STORE_GOODS:
        return building.inventory.get(good_id, 0)
    return None


def general_store_can_auto_sell(item):
    data = item_definition(item_id(item))
    return data.get("type") == "bien" and data.get("family") != "medecine" and data.get("family") != "intermediaire"


def player_general_store_can_sell(item):
    return general_store_can_auto_sell(item)


def general_store_storage_capacity(building):
    return building.production.get("storage_capacity", 400)


def general_store_price(city, good_id):
    """Prix public du General Store: national + transport + marge."""
    return round((market_price(city, good_id) + transport_cost(city, good_id)) * 1.1, 2)


def store_sell_price(city, good_id):
    """Prix auquel le magasin rachete au joueur ou a une propriete."""
    return round(max(0, market_price(city, good_id) - transport_cost(city, good_id)) * 0.9, 2)


def build_general_store_offers(game, building):
    refresh_general_store_weapon_offer_stock(building)
    offers = []
    for good_id in general_store_goods():
        data = item_definition(item_id(good_id))
        quantity = general_store_available_quantity(building, good_id)
        offers.append({
            "type": "bien",
            "family": data.get("family") or "divers",
            "id": data["id"],
            "label": data["label"],
            "utility": data.get("utility", 0) + 10,
            "price": general_store_price(game.city, good_id),
            "quantity": quantity if quantity is not None else float("inf"),
            "building_id": building.building_id,
            "owner_id": building.owner,
            "weight": data.get("weight", 0),
            "fractionable": data.get("fractionable", False),
        })
    return offers
