"""Economie: offres, revenus, consommation et transactions.

Plan du fichier:
01 - holder helpers: argent et inventaire d'un personnage ou batiment.
02 - price helpers: prix nationaux, transport et poids.
03 - exchange functions: achats/ventes/echange local.
04 - market cycle: variation naturelle des prix nationaux.
05 - offer/revenue/consumption entries: points d'entree de simulation.
06 - offer id helpers: identifiants courts des lignes d'offre.

Important: il n'y a que trois fonctions d'echange commercial generiques:
`buy_from_national_market`, `sell_to_national_market` et `local_trade`.
Le reste du module sert a construire l'offre, calculer les revenus et traiter
la consommation.
"""

import random
import unicodedata
from copy import deepcopy

from goods_services import ITEM_CATALOG, item_definition, item_id
from game_state import BASE_MARKET_PRICES, job_has_included_board, property_type_has_owner_board
from housing import housing_offer_row, vacant_listed_housing_units
from housing_rules import sync_property_housing
from items.animals import ANIMAL_CATALOG, animal_allowed_in_character_inventory, animal_definition, is_animal_id
from accounting import ensure_building_accounting, record_accounting_charge, record_accounting_product, result_total
from buildings import Building, employee_ids, employee_role, employee_salary, employee_wage
from character import generate_consumption_needs, generate_preferences
import math


def normalize_text(value):
    """Normalise un texte pour comparer des ids et libelles sans accent."""
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    return "".join(char for char in value if not unicodedata.combining(char))


def holder_money(holder):
    return getattr(holder, "current_balance", getattr(holder, "money", 0))


def set_holder_money(holder, amount):
    if hasattr(holder, "current_balance"):
        holder.current_balance = round(amount, 2)
    else:
        holder.money = round(amount, 2)


def add_money(holder, amount):
    set_holder_money(holder, holder_money(holder) + amount)


def remove_money(holder, amount, allow_negative=False):
    if not allow_negative and holder_money(holder) < amount:
        return False
    set_holder_money(holder, holder_money(holder) - amount)
    return True


def holder_inventory(holder):
    inventory = getattr(holder, "inventory", None)
    if inventory is None:
        holder.inventory = {}
        inventory = holder.inventory
    return inventory


def is_character_holder(holder):
    """Reconnait joueur et PNJ sans importer leurs classes."""
    return hasattr(holder, "is_player") or holder.__class__.__name__ in {"Character", "NPC", "CharacterBase"}


def can_receive_inventory_item(holder, good_id):
    """Bloque les animaux dans les inventaires de personnages."""
    normalized = item_id(good_id)
    if is_animal_id(normalized) and is_character_holder(holder):
        return animal_allowed_in_character_inventory(normalized)
    return True


def market_price(game_or_city, good_id):
    city = getattr(game_or_city, "city", game_or_city)
    normalized = item_id(good_id)
    prices = getattr(city, "market_prices", None) or BASE_MARKET_PRICES
    if normalized in prices:
        return prices[normalized]
    if normalized in ANIMAL_CATALOG:
        return animal_definition(normalized).get("base_price", 0)
    return item_definition(normalized).get("base_price", 0)


def transport_cost(game_or_city, good_id):
    city = getattr(game_or_city, "city", game_or_city)
    unit = 0.1 if city_has_train_station(city) else getattr(city, "transport_cost_per_weight", 0.5)
    if item_id(good_id) in ANIMAL_CATALOG:
        return 0
    return item_definition(item_id(good_id)).get("weight", 0) * unit


def unit_transport_cost(city):
    return 0.1 if city_has_train_station(city) else getattr(city, "transport_cost_per_weight", 0.5)


def good_weight(good_id):
    normalized = item_id(good_id)
    if normalized not in ITEM_CATALOG:
        return 0
    return item_definition(normalized).get("weight", 0)


def inventory_weight(inventory):
    return round(sum(good_weight(item) * quantity for item, quantity in inventory.items()), 2)


def property_good_price(city, good_id):
    return round(market_price(city, good_id) + transport_cost(city, good_id), 2)


def city_has_train_station(city):
    return any(building.building_type == "Gare" for building in getattr(city, "buildings", []))


def run_market_price_cycle(app):
    """Etape economique naturelle: les prix nationaux suivent leur cycle."""
    fluctuate_market_prices(app.game.city)
    app.log_turn_step("Cycle des prix", "Prix nationaux mis a jour.")


def fluctuate_market_prices(city):
    """Fait varier les prix autour de leur prix de base selon un cycle naturel."""
    city.market_prices = getattr(city, "market_prices", {}) or BASE_MARKET_PRICES.copy()
    season_index = {"Printemps": 0, "Été": 1, "Automne": 2, "Hiver": 3}.get(city.season, 0)
    year_offset = max(0, getattr(city, "year", 1865) - 1865)
    for index, (key, base_price) in enumerate(BASE_MARKET_PRICES.items()):
        # Chaque bien a une phase differente, mais le resultat reste deterministe.
        phase = (season_index + year_offset * 4 + index * 0.73) / 4
        multiplier = 1 + math.sin(phase * math.tau) * 0.1
        city.market_prices[key] = round(base_price * multiplier, 4)


def buy_from_national_market(game, buyer, good_id, quantity, allow_negative=False):
    """Achete au marche national: prix national + transport."""
    good_id = item_id(good_id)
    if good_id not in ITEM_CATALOG or item_definition(good_id).get("type") != "bien":
        return transaction_result(False, "Bien inconnu ou non achetable.", good_id, quantity, 0)
    quantity = normalize_quantity(good_id, quantity)
    if quantity is None:
        return transaction_result(False, "Quantite invalide.", good_id, 0, 0)
    unit_price = market_price(game, good_id) + transport_cost(game, good_id)
    total = round(unit_price * quantity, 2)
    if not remove_money(buyer, total, allow_negative=allow_negative):
        return transaction_result(False, "Argent insuffisant.", good_id, quantity, total)
    inventory = holder_inventory(buyer)
    inventory[good_id] = inventory.get(good_id, 0) + quantity
    return transaction_result(True, "Achat national effectue.", good_id, quantity, total)


def sell_to_national_market(game, seller, good_id, quantity):
    """Vend au marche national: prix national - transport - 10%."""
    good_id = item_id(good_id)
    if good_id not in ITEM_CATALOG or item_definition(good_id).get("type") != "bien":
        return transaction_result(False, "Bien inconnu ou non vendable.", good_id, quantity, 0)
    quantity = normalize_quantity(good_id, quantity)
    if quantity is None:
        return transaction_result(False, "Quantite invalide.", good_id, 0, 0)
    inventory = holder_inventory(seller)
    if inventory.get(good_id, 0) < quantity:
        return transaction_result(False, "Stock insuffisant.", good_id, quantity, 0)
    unit_gain = max(0, (market_price(game, good_id) - transport_cost(game, good_id)) * 0.9)
    total = round(unit_gain * quantity, 2)
    move_inventory(inventory, {}, good_id, quantity)
    add_money(seller, total)
    if isinstance(seller, Building):
        category = "production_sold" if seller.building_type in ["Ranch", "Mine"] else "merchandise_sold"
        record_accounting_product(seller, category, total, cash=False)
        seller.account_journal.append(f"Vente nationale - {item_definition(good_id)['label']} : {format_money(total)}")
    return transaction_result(True, "Vente nationale effectuee.", good_id, quantity, total)


def local_trade(game, seller, buyer, good_id, quantity, price, allow_buyer_negative=False):
    """Echange local entre deux personnages/batiments."""
    good_id = item_id(good_id)
    if not can_receive_inventory_item(buyer, good_id):
        return transaction_result(False, "Ce type d'animal ne va pas dans l'inventaire d'un personnage.", good_id, quantity, 0)
    quantity = normalize_quantity(good_id, quantity)
    if quantity is None:
        return transaction_result(False, "Quantite invalide.", good_id, 0, 0)
    seller_inventory = holder_inventory(seller)
    buyer_inventory = holder_inventory(buyer)
    if seller_inventory.get(good_id, 0) < quantity:
        return transaction_result(False, "Stock vendeur insuffisant.", good_id, quantity, 0)
    total = round(price * quantity, 2)
    if not remove_money(buyer, total, allow_negative=allow_buyer_negative):
        return transaction_result(False, "Argent acheteur insuffisant.", good_id, quantity, total)
    move_inventory(seller_inventory, buyer_inventory, good_id, quantity)
    add_money(seller, total)
    return transaction_result(True, "Echange local effectue.", good_id, quantity, total)


def move_inventory(source, target, good_id, quantity):
    source[good_id] = source.get(good_id, 0) - quantity
    if source[good_id] <= 0:
        source.pop(good_id, None)
    target[good_id] = target.get(good_id, 0) + quantity


def transfer_inventory_item(source, target, good_id, quantity):
    good_id = item_id(good_id)
    if not can_receive_inventory_item(target, good_id):
        return False
    if source.get(good_id, 0) < quantity:
        return False
    move_inventory(source, target, good_id, quantity)
    return True


def normalize_quantity(good_id, quantity):
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return None
    if quantity <= 0:
        return None
    if not item_definition(good_id).get("fractionable", False):
        if not quantity.is_integer():
            return None
        return int(quantity)
    return round(quantity, 4)


def transaction_result(success, message, good_id, quantity, amount):
    return {
        "success": success,
        "message": message,
        "good_id": good_id,
        "quantity": quantity,
        "amount": amount,
    }


def format_money(amount):
    amount = round(float(amount), 2)
    if amount.is_integer():
        return f"{int(amount)} $"
    return f"{amount:.2f} $"


def process_local_offer(game, exploitation_callback=None):
    """Construit la liste d'offre globale en interrogeant chaque batiment.

    Chaque type de batiment reste responsable de ses propres regles
    d'exploitation et d'offre. L'economie ne fait qu'accumuler le resultat.
    `exploitation_callback` est transitoire: il garde les anciens blocs non
    encore migres tout en centralisant deja l'accumulation des offres.
    """
    offers = []
    sync_property_housing(game.city)
    for building in game.city.buildings:
        if exploitation_callback:
            callback_offers = exploitation_callback(building)
            offers.extend(callback_offers or [])
            continue
        exploitation = getattr(building, "run_exploitation", None)
        if exploitation:
            exploitation(game)
        offer_provider = getattr(building, "generate_offers", None)
        if offer_provider:
            offers.extend(offer_provider(game))
    offers.extend(housing_offer_row(housing) for housing in vacant_listed_housing_units(game.city))
    assign_offer_ids(offers)
    return offers


def generate_offer_table(game):
    """Compatibilite: ancien nom de process_local_offer."""
    return process_local_offer(game)



# Revenus, preferences et demande --------------------------------------

OWNER_LIKE_JOBS = {
    "Proprietaire de ranch",
    "Proprietaire de saloon",
    "Tenancier du General Store",
    "Chirurgien barbier",
}

PUBLIC_EMPLOYEE_JOBS = {
    "Adjoint du sherif",
    "Employe du Post Office",
}

SKILLED_UNEMPLOYED_INCOME_SKILLS = {"Chasse", "Cuisine"}


def process_turn_income(game):
    """Calcule les revenus de la saison sans encaisser deux fois les proprietaires.

    Les salaires sont verses directement dans la poche des salaries. Les revenus de
    proprietaire restent des revenus de reference : les dollars reels arrivent par
    les ventes, la consommation ou la gestion d'exploitation.
    """
    median_wage = median_local_wage(game.city)
    church = find_building_by_type(game.city, "Église")
    donation_pool = church.production.get("donations", 10) if church else 0
    donation_reserve = min(median_wage, donation_pool)
    distributable_donations = max(0, donation_pool - donation_reserve)
    unemployed_people = [npc for npc in game.city.population if is_unemployed(npc)]
    donation_by_person = unemployment_donation_share(distributable_donations, unemployed_people, median_wage)
    records = []

    reset_non_owner_income(game)
    process_player_income(game, median_wage, records)

    for npc in game.city.population:
        if npc.job == "Voyageur":
            continue
        if npc.job == "Pasteur":
            continue
        if is_owner_like_npc(game.city, npc):
            process_owner_income(game, npc, median_wage, records)
            continue
        if is_unemployed(npc):
            process_unemployed_income(game, npc, median_wage, donation_by_person, records)
            continue
        if npc.job in PUBLIC_EMPLOYEE_JOBS or npc.job == "Sherif":
            process_public_employee_income(game, npc, median_wage, records)
            continue
        if npc.job in ["Oisif", "Oisive"]:
            npc.income = 0
            continue
        process_private_employee_income(game, npc, records)

    process_pastor_income(game, church, donation_pool, donation_reserve, donation_by_person, len(unemployed_people), records)

    total_paid = round(sum(record["paid"] for record in records), 2)
    total_reference = round(sum(record["income"] for record in records), 2)
    summary = (
        f"salaire médian={format_money(median_wage)}, "
        f"{len(records)} revenu(s), {format_money(total_paid)} versés, "
        f"{format_money(total_reference)} de revenus de référence."
    )
    return {
        "median_wage": median_wage,
        "records": records,
        "summary": summary,
    }


def reset_non_owner_income(game):
    for npc in game.city.population:
        if npc.job not in OWNER_LIKE_JOBS and npc.job not in ["Voyageur", "Pasteur"]:
            npc.income = 0


def is_unemployed(npc):
    return getattr(npc, "job", None) in ["Chômeur", "Chômeuse", "Chomeur", "Chomeuse"]


def process_player_income(game, median_wage, records):
    paid = 0
    income = 0
    if getattr(game.character, "job", None):
        income += player_contract_wage(game) or employee_salary(game.character.job)
        paid += income
        game.character.money += income
        employer = player_employer_building(game)
        if employer:
            employer.annual_wages += income
            record_accounting_charge(employer, "wages", income)

    owner_income = player_owner_reference_income(game, median_wage)
    if owner_income is not None:
        income = max(income, owner_income)
        game.character.income = income
        records.append(income_record("player", game.character.name, "Propriétaire joueur", income, paid))
    elif income:
        game.character.income = income
        records.append(income_record("player", game.character.name, game.character.job, income, paid))


def process_private_employee_income(game, npc, records):
    role = employee_role_for_npc(game.city, npc)
    income = employee_contract_wage_for_npc(game.city, npc) or employee_salary(role or npc.job)
    npc.income = income
    paid_to = pay_npc_income_to_household(game.city, npc, income)
    employer = employer_building_for_npc(game.city, npc)
    if employer:
        employer.annual_wages += income
        record_accounting_charge(employer, "wages", income)
    records.append(income_record(npc.npc_id, npc.name, role or npc.job, income, income, paid_to))


def player_contract_wage(game):
    employer_id = getattr(game.character, "employer_building_id", None)
    if not employer_id:
        return None
    building = game.city.get_building_by_id(employer_id)
    if not building:
        return None
    contract = employee_contract_for(building, "player")
    return contract.get("wage")


def player_employer_building(game):
    employer_id = getattr(game.character, "employer_building_id", None)
    if not employer_id:
        return None
    return game.city.get_building_by_id(employer_id)


def process_public_employee_income(game, npc, median_wage, records):
    multiplier = 2 if npc.job == "Sherif" else 1.5
    income = round(median_wage * multiplier, 2)
    npc.income = income
    paid_to = pay_npc_income_to_household(game.city, npc, income)
    records.append(income_record(npc.npc_id, npc.name, npc.job, income, income, paid_to))


def process_unemployed_income(game, npc, median_wage, donation_by_person, records):
    skilled_income = 0
    if has_any_skill(npc, SKILLED_UNEMPLOYED_INCOME_SKILLS):
        skilled_income = random_normal_between(median_wage * 0.25, median_wage * 0.50)

    donation_income = donation_by_person
    income = round(skilled_income + donation_income, 2)
    npc.income = income
    paid_to = pay_npc_income_to_household(game.city, npc, income)
    records.append(income_record(npc.npc_id, npc.name, npc.job, income, income, paid_to))


def process_owner_income(game, npc, median_wage, records):
    income = owner_reference_income_for_name(game.city, npc.name, median_wage)
    npc.income = income
    records.append(income_record(npc.npc_id, npc.name, npc.job, income, 0))


def process_pastor_income(game, church, donation_pool, donation_reserve, donation_by_person, unemployed_count, records):
    pastor = next((npc for npc in game.city.population if npc.job == "Pasteur"), None)
    if not pastor:
        return
    pastor_income = round(donation_reserve + max(0, donation_pool - donation_reserve - donation_by_person * unemployed_count), 2)
    pastor.income = pastor_income
    paid_to = pay_npc_income_to_household(game.city, pastor, pastor_income)
    records.append(income_record(pastor.npc_id, pastor.name, "Pasteur", pastor_income, pastor_income, paid_to))
    if church:
        church.production["donations"] = donation_pool


def income_record(identifier, name, source, income, paid, paid_to=None):
    return {
        "id": identifier,
        "name": name,
        "source": source,
        "income": round(income, 2),
        "paid": round(paid, 2),
        "paid_to": paid_to or name,
    }


def median_local_wage(city):
    salaries = []
    for npc in city.population:
        if npc.job == "Voyageur" or npc.job in OWNER_LIKE_JOBS or npc.job in ["Oisif", "Oisive", "Chomeur", "Chomeuse"]:
            continue
        if npc.job == "Sherif":
            continue
        role = employee_role_for_npc(city, npc)
        if role:
            salaries.append(employee_contract_wage_for_npc(city, npc) or employee_salary(role))
        elif npc.job in PUBLIC_EMPLOYEE_JOBS:
            salaries.append(employee_salary(npc.job))

    if not salaries:
        return 7
    salaries = sorted(salaries)
    middle = len(salaries) // 2
    if len(salaries) % 2:
        return salaries[middle]
    return (salaries[middle - 1] + salaries[middle]) / 2


def unemployment_donation_share(distributable_donations, unemployed_people, median_wage):
    if not unemployed_people:
        return 0
    return round(min(median_wage * 0.75, distributable_donations / len(unemployed_people)), 2)


def random_normal_between(minimum, maximum):
    center = (minimum + maximum) / 2
    sigma = (maximum - minimum) / 6
    return round(max(minimum, min(maximum, random.gauss(center, sigma))), 2)


def pay_npc_income_to_household(city, npc, amount):
    receiver = spouse_income_receiver(city, npc)
    receiver.money += amount
    return receiver.name


def spouse_income_receiver(city, npc):
    if npc.sex != "Femme" or not npc.spouse_id:
        return npc
    spouse = city.get_npc_by_id(npc.spouse_id)
    return spouse or npc


def has_any_skill(npc, skills):
    return any(skill in npc.skills for skill in skills)


def find_building_by_type(city, building_type):
    normalized = normalize_text(building_type)
    return next((building for building in city.buildings if normalize_text(building.building_type) == normalized), None)


def is_owner_like_npc(city, npc):
    if npc.job in OWNER_LIKE_JOBS:
        return True
    return any(building.owner == npc.name and not building.is_public for building in city.buildings)


def employee_role_for_npc(city, npc):
    for building in city.buildings:
        if npc.npc_id in employee_ids(building):
            return employee_role(building, npc.npc_id)
    return None


def employee_contract_wage_for_npc(city, npc):
    for building in city.buildings:
        if npc.npc_id in employee_ids(building):
            return employee_wage(building, npc.npc_id)
    return None


def employer_building_for_npc(city, npc):
    for building in city.buildings:
        if npc.npc_id in employee_ids(building):
            return building
    return None


def player_owner_reference_income(game, median_wage):
    owned_buildings = [
        building for building in game.city.buildings
        if building.owner == game.character.name and not building.is_public
    ]
    if not owned_buildings:
        return None
    return max(median_wage, sum(owner_building_reference_income(building) for building in owned_buildings))


def owner_reference_income_for_name(city, owner_name, median_wage):
    owned_buildings = [
        building for building in city.buildings
        if building.owner == owner_name and not building.is_public
    ]
    if not owned_buildings:
        return median_wage
    return max(median_wage, sum(owner_building_reference_income(building) for building in owned_buildings))


def owner_building_reference_income(building):
    if building.building_type == "Ranch":
        result = building.previous_annual_result or current_cash_result(building)
        return round(max(0, result) / 4, 2)

    result = getattr(building, "current_result", 0) or current_cash_result(building)
    if result > 0:
        building.production["zero_income_turns"] = 0
        building.production["last_owner_income"] = round(result, 2)
        return round(result, 2)

    previous_income = building.production.get("last_owner_income", 0)
    zero_turns = building.production.get("zero_income_turns", 0) + 1
    building.production["zero_income_turns"] = zero_turns
    if previous_income <= 0:
        return 0
    if zero_turns <= 1:
        return round(previous_income, 2)
    reduced = previous_income * (0.75 ** (zero_turns - 1))
    building.production["last_owner_income"] = round(reduced, 2)
    return round(reduced, 2)


def current_annual_result(building):
    return result_total(ensure_building_accounting(building)["current_year"])


def current_cash_result(building):
    lines = ensure_building_accounting(building)["current_year"]
    cash_products = lines.get("production_sold", 0) + lines.get("merchandise_sold", 0) + lines.get("services_sold", 0)
    cash_charges = (
        lines.get("raw_material_purchases", 0)
        + lines.get("merchandise_purchases", 0)
        + lines.get("wages", 0)
        + lines.get("taxes", 0)
        + lines.get("loan_repayments", 0)
        + lines.get("interest_expenses", 0)
    )
    return round(cash_products - cash_charges, 2)


def savings_donation_offer():
    return {
        "type": "service",
        "family": "epargne_don",
        "id": "epargne_don",
        "id_offre": "offre_globale_epargne_don",
        "label": "Épargne et don",
        "utility": 20,
        "price": 1,
        "quantity": float("inf"),
        "building_id": None,
        "owner_id": None,
    }


def preference_index_base(offer):
    offer_id = str(offer.get("id") or "")
    if offer_id.startswith("hotesse_"):
        return "hotesse"
    return offer_id


def character_has_included_board(game, character):
    if job_has_included_board(getattr(character, "job", None)):
        return True
    return any(
        building.owner == character.name and property_type_has_owner_board(building.building_type)
        for building in game.city.buildings
    )


def sorted_positive_rows(rows):
    return sorted([row for row in rows if row.get("ratio", 0) > 0], key=lambda row: row["ratio"], reverse=True)


def demand_offers_for_category(offers, category):
    return [offer for offer in offers if demand_category_for_offer(offer) == category]


def demand_category_for_offer(offer):
    offer_id = offer.get("id")
    family = offer.get("family")
    if offer_id in ["soins", "soin_blessure", "soin_maladie", "soin_blessure_grave"]:
        return "soins"
    if offer_id == "vivres_secs" or family == "vivres":
        return "vivres"
    if offer_id == "chambre" or family == "logement":
        return "logement"
    if offer_id == "biere" or family == "alcool":
        return "alcool"
    if offer_id == "hotesse" or str(offer_id).startswith("hotesse_"):
        return "hotesse"
    return "reste"


def rest_offer_quantity(character, offer):
    offer_id = offer.get("id")
    if offer_id == "biere":
        return beer_preference_count(character)
    if offer_id in ["repas", "bain", "coupe", "hotesse", "chambre"]:
        return len(character.preferences.get(offer_id, {1: 1}))
    return 1


def beer_preference_count(character):
    return len(character.preferences.get("biere", {1: 1}))


def preference_for_offer(character, offer, rank):
    offer_id = offer.get("id")
    preferences = character.preferences or {}
    if str(offer_id).startswith("hotesse_"):
        return preference_rank_value(preferences.get("hotesse", {}), rank)
    if offer_id in preferences:
        return preference_rank_value(preferences[offer_id], rank)
    return 1


def preference_rank_value(values, rank):
    return values.get(rank, values.get(str(rank), 0))


def safe_offer_price(offer):
    price = offer.get("price", 0)
    if price is None or price <= 0:
        return 0.1
    return price



# Nouvelle demande ------------------------------------------------------

def build_city_preference_lists(game, offers):
    """Crée une liste unique de préférences et une table de besoins par personnage."""
    characters = [game.character, *game.city.population]
    return [
        build_character_preference_entry(game, character, offers)
        for character in characters
    ]


def build_character_preference_entry(game, character, offers):
    ensure_character_demand_data(character)
    needs = build_character_needs(game, character)
    return {
        "character_id": character_identifier(character),
        "needs": needs,
        "preferences": build_character_preference_list(game, character, offers, needs),
    }


def ensure_character_demand_data(character):
    if not getattr(character, "preferences", None):
        character.preferences = generate_preferences(character)
    if not getattr(character, "consumption_needs", None):
        character.consumption_needs = generate_consumption_needs(character)


def build_character_needs(game, character):
    trait = getattr(character, "trait", "néant")
    condition = normalize_text(getattr(character, "condition", "en forme"))
    food_need = 0 if character_has_included_board(game, character) else round(random_normal_between(6.5, 7.5), 2)
    needs = {
        "medical": condition in ["malade", "blesse gravement"],
        "vivres": food_need,
        "vetement": character_inventory_quantity(character, "haillon") > 0,
        "cafe": seasonal_individual_need(character, "cafe"),
        "tabac": seasonal_individual_need(character, "tabac"),
        "alcool": random.randint(7, 10) if trait == "alcoolique" else 0,
        "hotesse": 1 if trait == "luxure" else 0,
    }
    if getattr(character, "job", None) == "Voyageur":
        needs["vivres"] = round(random_normal_between(1.8, 2.2), 2)
    return needs


def seasonal_individual_need(character, key):
    base_needs = getattr(character, "consumption_needs", {}) or {}
    base = base_needs.get(key)
    if base is None:
        base = generate_consumption_needs(character).get(key, 0)
        character.consumption_needs = {**base_needs, key: base}
    return max(0, int(round(base + random.choice([-1, 0, 1]))))


def build_character_preference_list(game, character, offers, needs=None):
    needs = needs or build_character_needs(game, character)
    rows = []
    for offer in offers:
        rows.extend(preference_rows_for_offer(character, offer, needs))
    rows.extend(preference_rows_for_offer(character, savings_donation_offer(), needs))
    return sorted_positive_rows(rows)


def preference_rows_for_offer(character, offer, needs):
    if not offer_is_relevant_for_character(character, offer):
        return []
    if unique_offer_is_already_satisfied(character, offer):
        return []

    rows = []
    for rank in preference_ranks_for_offer(character, offer):
        coefficient = medical_preference_coefficient(offer) or preference_for_offer(character, offer, rank)
        price = safe_offer_price(offer)
        utility = offer.get("utility", 0)
        ratio = round(utility * coefficient * (getattr(character, "income", 0) / price), 4) if utility and coefficient else 0
        row = deepcopy(offer)
        row.update({
            "character_id": character_identifier(character),
            "index": f"{preference_index_base(offer)}{rank}",
            "demand_quantity": preference_quantity_for_offer(offer, needs),
            "coefficient": coefficient,
            "ratio": ratio,
        })
        rows.append(row)
    return rows


def preference_ranks_for_offer(character, offer):
    if medical_preference_coefficient(offer):
        return [1]
    offer_id = preference_index_base(offer)
    preferences = getattr(character, "preferences", {}) or {}
    ranks = sorted(int(rank) for rank in preferences.get(offer_id, {}).keys())
    return ranks or [1]


def medical_preference_coefficient(offer):
    if offer.get("id") in ["soin_blessure", "soin_blessure_grave", "soin_maladie"]:
        return 1
    return None


def offer_is_relevant_for_character(character, offer):
    offer_id = offer.get("id")
    condition = normalize_text(getattr(character, "condition", "en forme"))
    if offer_id == "soin_blessure":
        return condition == "blesse"
    if offer_id == "soin_blessure_grave":
        return condition == "blesse gravement"
    if offer_id == "soin_maladie":
        return condition == "malade"
    return True


def preference_quantity_for_offer(offer, needs):
    if demand_category_for_offer(offer) == "vivres":
        return round(needs.get("vivres", 0) / 7, 4)
    return 1


def unique_offer_is_already_satisfied(character, offer):
    offer_id = offer.get("id")
    if offer.get("type") != "bien" or offer_id not in ITEM_CATALOG:
        return False
    offer_data = item_definition(offer_id)
    if offer_data.get("saturation") != "unique":
        return False

    inventory = getattr(character, "inventory", {}) or {}
    offer_utility = offer_data.get("utility", 0)
    offer_family = offer_data.get("family")
    for owned_item, owned_quantity in inventory.items():
        if owned_quantity <= 0 or item_id(owned_item) not in ITEM_CATALOG:
            continue
        owned_data = item_definition(item_id(owned_item))
        if owned_data.get("family") == offer_family and owned_data.get("utility", 0) >= offer_utility:
            return True
    return False


def character_inventory_quantity(character, item):
    inventory = getattr(character, "inventory", {}) or {}
    return inventory.get(item_id(item), 0)


def character_identifier(character):
    return getattr(character, "npc_id", "player")


def flatten_preference_lists(preference_lists):
    rows = []
    for entry in preference_lists:
        rows.extend(entry.get("preferences", []))
    return rows


def demand_table_summary(demand_table):
    if not demand_table:
        return "Aucune demande générée."
    character_count = len({row.get("character_id") for row in demand_table})
    best_rows = demand_table[:5]
    examples = " | ".join(
        f"{row.get('character_id', '?')} -> {row.get('label', row.get('id', '?'))} ({row.get('family', '?')}, ratio {round(row.get('ratio', 0), 2)})"
        for row in best_rows
    )
    return f"{len(demand_table)} ligne(s) de préférence pour {character_count} personnage(s). Exemples : {examples}"




def process_income(game):
    """Point d'entree du calcul des revenus."""
    return process_turn_income(game)


def process_consumption(game, offers=None):
    """Point d'entree preference -> demande -> consommation.

    La consommation effective sera branchee ici plus tard. Pour l'instant on
    construit la liste de preferences et la table de demande exploitable.
    """
    offers = offers or []
    preference_lists = build_city_preference_lists(game, offers)
    demand_table = flatten_preference_lists(preference_lists)
    return {
        "preference_lists": preference_lists,
        "demand_table": demand_table,
        "summary": demand_table_summary(demand_table),
    }


def assign_offer_ids(offers):
    counters = {}
    for offer in offers:
        prefix = offer_id_prefix(offer)
        counters[prefix] = counters.get(prefix, 0) + 1
        offer["id_offre"] = f"{prefix}{counters[prefix]:04d}"


def offer_id_prefix(offer):
    if offer.get("type") == "logement" or offer.get("housing_id"):
        return "H"
    building_id = str(offer.get("building_id") or "")
    if building_id.startswith("saloon"):
        return "S"
    if building_id.startswith("general_store"):
        return "G"
    if "barber" in building_id:
        return "B"
    if "clinic" in building_id or "medical" in building_id:
        return "M"
    if "mine" in building_id:
        return "N"
    return "O"
