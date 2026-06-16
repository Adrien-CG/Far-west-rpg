"""Batiment Saloon.

Plan du fichier:
01 - Saloon: classe de creation et valeurs par defaut.
02 - build_saloon_offer: exploitation du saloon et generation des offres.
03 - beer/meal/hostess helpers: calculs propres aux services du saloon.
04 - employee/occupation helpers: recuperation des employes et du joueur.
"""

from building_types.base import TypedBuilding
from buildings import employee_ids, employee_role
from economy import good_weight
from goods_services import ITEM_CATALOG, item_definition, item_id, service_base_utility, service_default_price


class Saloon(TypedBuilding):
    building_type_name = "Saloon"

    def __init__(
        self,
        building_id,
        name,
        owner,
        features=None,
        upgrades=None,
        current_balance=0,
        under_construction=False,
    ):
        super().__init__(
            building_id=building_id,
            name=name,
            building_type="Saloon",
            owner=owner,
            level=1,
            features=features or {"table_poker": False, "piano": False},
            hidden_stats={
                "attrait_clients": 6,
                "ambiance": 5,
                "reputation_biere": 5,
                "qualite_service": 5,
                "sensibilite_prix": 5,
            },
            inventory={"fut_biere": 0, "vivres_secs": 0},
            production={
                "commande_biere": 0,
                "prix_biere": service_default_price("biere"),
                "commande_vivres_secs": 0,
                "prix_repas": service_default_price("repas"),
                "prix_hotesse": service_default_price("hotesse"),
                "prix_bain": service_default_price("bain"),
                "prix_chambre": service_default_price("chambre"),
            },
            upgrades=upgrades or [],
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def building_actions(self, game):
        return ["Boire une bière", "Faire une partie de poker", "Commander un repas", "Prendre un bain"]

    def recruitable_jobs(self, game):
        return ["Barman", "Cuisinier", "Hotesse"]

    def generate_offers(self, game):
        return build_saloon_offer(game, self)

    def generate_housing_units(self, city):
        """Logements du saloon: chambres voyageurs ou location longue duree."""
        from housing_rules import building_housing_units, sync_building_units

        mode = self.production.get("housing_mode", "voyageurs")
        sync_building_units(city, self, "chambre", room_count(self), listed=(mode == "location"))
        if mode == "voyageurs":
            for housing in building_housing_units(city, self, "chambre"):
                if not housing.occupants:
                    housing.occupants = ["voyageur"]


def build_saloon_offer(game, building):
    offers = []
    upgrades = normalize_upgrades(building.upgrades)
    global_multiplier = saloon_global_utility_multiplier(building)

    beer_offer = saloon_beer_offer(game, building, global_multiplier)
    if beer_offer:
        offers.append(beer_offer)

    meal_offer = saloon_meal_offer(game, building, upgrades, global_multiplier)
    if meal_offer:
        offers.append(meal_offer)

    if "Salle de bain" in upgrades:
        offers.append(saloon_service_offer_entry(
            game,
            building,
            "bain",
            service_base_utility("bain"),
            building.production.get("prix_bain", service_default_price("bain")),
            9999,
            global_multiplier,
        ))

    offers.extend(saloon_hostess_offers(game, building, upgrades, global_multiplier))
    return offers


def room_count(building):
    return normalize_upgrades(building.upgrades).count("Chambre")


def saloon_beer_offer(game, building, global_multiplier):
    stock_quantity = saloon_inventory_quantity(building, "fut_biere") * 60
    if stock_quantity <= 0:
        return None

    capacity = 400 if "Agrandissement" in normalize_upgrades(building.upgrades) else 200
    barman = saloon_employee(game, building, "Barman")
    player_at_bar = player_occupation_matches(game, "saloon_bar", building) or player_role_occupation_matches(game, building, "Barman")
    if not barman and not player_at_bar:
        return None

    utility = service_base_utility("biere") + saloon_bar_social(game, barman, player_at_bar)
    if building.features.get("table_poker"):
        utility += 5
    quantity = min(stock_quantity, capacity)
    if quantity <= 0:
        return None
    return saloon_service_offer_entry(
        game,
        building,
        "biere",
        utility,
        building.production.get("prix_biere", service_default_price("biere")),
        quantity,
        global_multiplier,
    )


def saloon_bar_social(game, barman, player_at_bar):
    player_social = game.character.sociability
    if not barman:
        return player_social if player_at_bar else 0
    player_value = player_social if player_at_bar else 0
    return max(barman.sociability, player_value)


def saloon_meal_offer(game, building, upgrades, global_multiplier):
    if "Cuisine" not in upgrades:
        return None

    cook = saloon_employee(game, building, "Cuisinier")
    player_cooks = player_occupation_matches(game, "saloon_meals", building) or player_role_occupation_matches(game, building, "Cuisinier")
    capacity = 0
    has_cooking_skill = False
    if cook:
        capacity += cook.strength * 10
        has_cooking_skill = has_skill(cook, "Cuisine")
    if player_cooks:
        capacity += game.character.strength * 10
        has_cooking_skill = has_cooking_skill or has_skill(game.character, "Cuisine")
    capacity_limit = 200 if "Agrandissement" in upgrades else 100
    quantity = min(round_half_up(capacity), capacity_limit)
    if quantity <= 0:
        return None
    utility = saloon_meal_utility(building) + (5 if has_cooking_skill else 0)
    return saloon_service_offer_entry(
        game,
        building,
        "repas",
        utility,
        building.production.get("prix_repas", service_default_price("repas")),
        quantity,
        global_multiplier,
    )


def saloon_meal_utility(building):
    total_quantity = 0
    weighted_utility = 0
    for inventory_key, quantity in building.inventory.items():
        normalized_key = item_id(inventory_key)
        if normalized_key not in ITEM_CATALOG:
            continue
        data = item_definition(normalized_key)
        if data.get("type") != "bien" or data.get("family") != "vivres":
            continue
        total_quantity += quantity
        weighted_utility += quantity * data.get("utility", 0)

    if total_quantity <= 0:
        return service_base_utility("repas")
    return round(weighted_utility / total_quantity + 10, 4)


def saloon_hostess_offers(game, building, upgrades, global_multiplier):
    hostesses = saloon_employees(game, building, "Hotesse")
    offers = []
    for hostess in hostesses:
        utility = service_base_utility("hotesse") + hostess.sociability
        if has_skill(hostess, "Charisme"):
            utility += 10
        if len(hostesses) >= 2:
            utility += 5
        if "Salle de bain" in upgrades:
            utility += 5
        offers.append(saloon_service_offer_entry(
            game,
            building,
            "hotesse",
            utility,
            building.production.get("prix_hotesse", service_default_price("hotesse")),
            20,
            global_multiplier,
            offer_id=f"hotesse_{hostess.npc_id}",
            label=f"Hôtesse - {hostess.name}",
        ))
    return offers


def saloon_global_utility_multiplier(building):
    multiplier = 1
    if "Décoration et luminaire" in normalize_upgrades(building.upgrades):
        multiplier += 0.02
    if building.features.get("piano"):
        multiplier += 0.02
    return multiplier


def saloon_service_offer_entry(game, building, service_id, utility, price, quantity, utility_multiplier, offer_id=None, label=None):
    data = item_definition(service_id)
    return {
        "type": data["type"],
        "family": data["family"],
        "id": offer_id or service_id,
        "label": label or data["label"],
        "utility": round(utility * utility_multiplier, 4),
        "price": price,
        "quantity": quantity,
        "building_id": building.building_id,
        "owner_id": building_owner_id(game, building),
        "weight": data.get("weight", 0),
        "fractionable": data.get("fractionable", False),
    }


def saloon_inventory_quantity(building, inventory_key):
    if inventory_key == "fut_biere":
        return building.inventory.get("fut_biere", 0) + building.inventory.get("biere", 0)
    if inventory_key == "vivres_secs":
        return building.inventory.get("vivres_secs", 0) + building.inventory.get("vivres", 0) + building.inventory.get("viande", 0)
    return building.inventory.get(inventory_key, 0)


def saloon_storage_capacity(building):
    return 100 if "Cave" in normalize_upgrades(building.upgrades) else 20


def saloon_item_weight(inventory_key):
    if inventory_key == "vivres_secs":
        return ITEM_CATALOG["vivres_secs"]["weight"]
    return good_weight(inventory_key)


def saloon_storage_used(building):
    return (
        saloon_inventory_quantity(building, "fut_biere") * saloon_item_weight("fut_biere")
        + saloon_inventory_quantity(building, "vivres_secs") * saloon_item_weight("vivres_secs")
    )


def saloon_employee(game, building, role):
    employees = saloon_employees(game, building, role)
    return employees[0] if employees else None


def saloon_employees(game, building, role):
    result = []
    for employee_id in employee_ids(building):
        if employee_role(building, employee_id) != role:
            continue
        npc = game.city.get_npc_by_id(employee_id)
        if npc:
            result.append(npc)
    return result


def building_owner_id(game, building):
    if building.owner == game.character.name:
        return "player"
    owner = next((npc for npc in game.city.population if npc.name == building.owner), None)
    return owner.npc_id if owner else None


def player_occupation_matches(game, occupation_type, building=None, role=None):
    occupation = getattr(game, "seasonal_occupation", {}) or {}
    if occupation.get("type") != occupation_type:
        return False
    if building and occupation.get("building_id") != building.building_id:
        return False
    if role and occupation.get("role") != role:
        return False
    return True


def player_role_occupation_matches(game, building, role):
    occupation = getattr(game, "seasonal_occupation", {}) or {}
    if occupation.get("type") not in ["employment", "job_application"]:
        return False
    return occupation.get("building_id") == building.building_id and occupation.get("role") == role


def has_skill(character, skill_name):
    normalized = normalize_text(skill_name)
    return any(normalize_text(skill) == normalized for skill in character.skills)


def normalize_text(value):
    return str(value).lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")


def normalize_upgrades(upgrades):
    return ["Chambre" if upgrade == "Chambres d'hotel" else upgrade for upgrade in upgrades]


def round_half_up(value):
    return int(value + 0.5)
