"""Batiment Ranch.

Plan du fichier:
01 - Ranch: classe de creation et valeurs par defaut.
02 - prix betail/taureaux: prix lus via items.animals/economie.
03 - charge/force de travail: calculs saisonniers du ranch.
04 - attrition/velage: pertes, naissances et mortalite des taureaux.
05 - marche aux taureaux/messages: helpers pour le trail drive et le rapport.
"""

import math
import random

from building_types.base import TypedBuilding
from buildings import employee_contract, employee_ids, employee_role, random_bull_fertility, random_spanish_bull_name, set_employee_contract
from accounting import ensure_ranch_stock_split, prorate_cattle_sale_split, record_accounting_charge, record_accounting_product, reduce_ranch_cattle_stock
from building_types.general_store import general_store_price, store_sell_price
from character import NPC
from economy import market_price
from items.animals import animal_base_price


class Ranch(TypedBuilding):
    building_type_name = "Ranch"

    def __init__(
        self,
        building_id,
        name,
        owner,
        head_count=0,
        bulls=None,
        employees=None,
        upgrades=None,
        current_balance=0,
        is_public=False,
        under_construction=False,
    ):
        employees = employees or []
        super().__init__(
            building_id=building_id,
            name=name,
            building_type="Ranch",
            owner=owner,
            level=1,
            is_public=is_public,
            inventory={"fourrage": 0},
            production={
                "head_count": head_count,
                "workload": 0,
                "bulls": bulls if bulls is not None else [self.random_bull()],
            },
            features={},
            hidden_stats={},
            employees=employees[:],
            employee_roles={employee_id: "Cowboy" for employee_id in employees},
            employee_tasks={employee_id: "Garder le troupeau" for employee_id in employees},
            employee_contracts={
                employee_id: employee_contract("Cowboy", 7, "Garder le troupeau")
                for employee_id in employees
            },
            upgrades=upgrades or [],
            current_balance=current_balance,
            under_construction=under_construction,
        )

    @staticmethod
    def random_bull():
        return {
            "nom": random_spanish_bull_name(),
            "age": random.randint(1, 6),
            "fÃ©conditÃ©": random_bull_fertility(),
            "stock_type": "merchandise",
        }

    def city_actions(self, game):
        return []

    def building_actions(self, game):
        return ["Travailler au Ranch pour la saison", "Préparer un long trail drive"]

    def recruitable_jobs(self, game):
        return ["Cowboy"]

    def run_exploitation(self, game):
        return run_ranch_exploitation(game, self)

    def generate_housing_units(self, city):
        """Logements propres au ranch: maison du proprietaire, chambre, baraquements."""
        from housing_rules import sync_building_units

        owner_units = sync_building_units(city, self, "maison_campagne", 1, listed=False)
        if owner_units and not owner_units[0].occupants:
            owner_units[0].occupants = [self.owner]
        sync_building_units(city, self, "chambre", 1, listed=False)
        barrack_units = normalize_upgrades(self.upgrades).count("Baraquements") * 2
        sync_building_units(city, self, "baraquement", barrack_units, listed=False)


RANCH_BARN_CAPACITY = 100


def run_ranch_exploitation(game, building):
    """Exploitation saisonniere complete d'un ranch."""
    from buildings import normalize_ranch_data

    normalize_ranch_data(building)
    building.production["market_cattle_price"] = cattle_market_price(game.city)
    logs = []
    messages = []
    show_property_report = building.owner == game.character.name
    workload = ranch_workload(cattle_head_count(building), game.city.season, building)
    workforce = ranch_workforce(game, building)
    surplus = workforce - workload
    logs.append((
        f"Ranch - {building.name}",
        f"têtes={cattle_head_count(building)}, charge={round(workload, 4)}, force={round(workforce, 4)}, surplus={round(surplus, 4)}",
    ))
    building.production.pop("workforce_bonus", None)
    building.production["workload"] = 0
    building.production.pop("player_ranch_work_actions", None)

    process_ranch_barn_and_food(game, building, surplus, logs)
    lost_cattle = apply_ranch_attrition(building, game.city.season, game.city.season_events, surplus)
    if show_property_report and lost_cattle > 0:
        messages.append(ranch_loss_message(lost_cattle))
    logs.append((f"Ranch - {building.name}", f"attrition={lost_cattle}, troupeau restant={cattle_head_count(building)}"))

    born_cattle = 0
    if game.city.season == "Printemps":
        born_cattle = apply_ranch_calving(building)
    else:
        logs.append((f"Ranch - {building.name}", f"pas de vêlage en {game.city.season}"))
    if show_property_report and born_cattle > 0:
        messages.append(ranch_birth_message(born_cattle))
    logs.append((f"Ranch - {building.name}", f"vêlage={born_cattle}, troupeau final avant trail={cattle_head_count(building)}"))

    bull_messages = apply_bull_mortality(building, game.city.season)
    if show_property_report:
        messages.extend(bull_messages)
    if bull_messages:
        logs.append((f"Ranch - {building.name}", "taureaux morts : " + " | ".join(bull_messages)))

    if trail_drive_state(building) and game.city.season == "Automne":
        trail_message = process_long_trail_drive_turn(game, building, logs)
        if show_property_report:
            messages.append(trail_message)
        logs.append((f"Ranch - {building.name}", trail_message))
    elif trail_drive_state(building):
        logs.append((f"Ranch - {building.name}", f"long trail drive en attente : impossible hors automne ({game.city.season})"))

    return {"offers": [], "logs": logs, "messages": messages}


def ranch_workforce(game, building, crew_entries=None, removed_npcs=None):
    if crew_entries is not None:
        return sum(trail_entry_workforce(game, entry, removed_npcs or []) for entry in crew_entries)

    workforce = 0
    for employee_id in employee_ids(building):
        if employee_id == "player":
            if player_role_occupation_matches(game, building, "Cowboy"):
                workforce += character_workforce_contribution(game.character)
            continue
        if employee_role(building, employee_id) != "Cowboy":
            continue
        npc = game.city.get_npc_by_id(employee_id)
        if npc:
            workforce += npc_workforce_contribution(npc)
    if player_occupation_matches(game, "ranch_work", building):
        workforce += character_workforce_contribution(game.character)
    return workforce


def trail_entry_workforce(game, entry, removed_npcs):
    if entry["type"] == "player":
        return character_workforce_contribution(game.character)
    npc = None
    if entry["type"] == "npc":
        npc = game.city.get_npc_by_id(entry.get("npc_id")) or npc_from_removed_trail(entry.get("npc_id"), removed_npcs)
    elif entry["type"] == "hired":
        npc = entry.get("npc")
    return npc_workforce_contribution(npc) if npc else 0


def process_ranch_barn_and_food(game, building, surplus, logs):
    upgrades = normalize_upgrades(building.upgrades)
    if "Grange" in upgrades:
        forage_gain = ranch_forage_gain(game.city.season, surplus)
        if forage_gain:
            building.inventory["fourrage"] = min(RANCH_BARN_CAPACITY, building.inventory.get("fourrage", 0) + forage_gain)

    produced_food = ranch_food_production(game.city.season, surplus, upgrades)
    consumed_food = ranch_food_consumption(game, building)
    food_balance = produced_food - consumed_food
    logs.append((
        f"Ranch - {building.name}",
        f"grange/vivres : fourrage={building.inventory.get('fourrage', 0)}, vivres produits={produced_food}, vivres consommés={consumed_food}, solde={round(food_balance, 2)}",
    ))
    if food_balance > 0:
        store_or_sell_ranch_food(game, building, food_balance, logs)
    elif food_balance < 0:
        buy_ranch_food(game, building, abs(food_balance), logs)


def ranch_food_consumption(game, building):
    total = 0
    for employee_id in employee_ids(building):
        if employee_role(building, employee_id) != "Cowboy":
            continue
        npc = game.city.get_npc_by_id(employee_id)
        if npc:
            total += npc.preferences.get("vivres_secs", {}).get(1, 1)
    owner = ranch_owner_person(game, building)
    if owner is game.character:
        total += 1
    elif owner:
        total += owner.preferences.get("vivres_secs", {}).get(1, 1)
    return round(total, 2)


def ranch_owner_person(game, building):
    if building.owner == game.character.name:
        return game.character
    return next((npc for npc in game.city.population if npc.name == building.owner), None)


def store_or_sell_ranch_food(game, building, quantity, logs):
    current = building.inventory.get("vivres_secs", 0)
    stored = min(quantity, max(0, RANCH_BARN_CAPACITY - current))
    surplus = quantity - stored
    if stored > 0:
        building.inventory["vivres_secs"] = current + stored
    if surplus > 0:
        amount = surplus * store_sell_price(game.city, "vivres_secs")
        building.current_balance += amount
        record_building_sale(building, amount, "production_sold")
        building.account_journal.append(f"Vente de vivres : {amount}")
        logs.append((f"Ranch - {building.name}", f"surplus vivres vendu={round(surplus, 2)} pour {format_money(amount)}"))


def buy_ranch_food(game, building, quantity, logs):
    amount = quantity * general_store_price(game.city, "vivres_secs")
    building.current_balance -= amount
    building.annual_purchases += amount
    building.lifetime_expenses += amount
    record_accounting_charge(building, "raw_material_purchases", amount, cash=False)
    building.account_journal.append(f"Achats de vivres : {amount}")
    logs.append((f"Ranch - {building.name}", f"vivres achetés={round(quantity, 2)} au General Store pour {format_money(amount)}"))


def process_long_trail_drive_turn(game, building, logs):
    trail_drive = trail_drive_state(building)
    removed_npcs = trail_drive.get("removed_npcs", [])
    crew = list(trail_drive.get("crew", [])) + [
        {"type": "hired", "npc": npc_from_saved_data(data)}
        for data in trail_drive.get("hired_cowboys", [])
    ]
    sell_cattle = trail_drive.get("sell_cattle", 0)
    outbound_workload = ranch_workload(sell_cattle, game.city.season, building, multiplier_override=0.8)
    outbound_surplus = ranch_workforce(game, building, crew, removed_npcs) - outbound_workload
    lost_outbound = ranch_attrition_loss(sell_cattle, ranch_attrition_rate(game.city.season, game.city.season_events, outbound_surplus, 0), outbound_surplus)
    sold_cattle = max(0, sell_cattle - lost_outbound)
    sale_amount = (sold_cattle * cattle_market_price(game.city)) + sum(bull_market_price(bull) for bull in trail_drive.get("sell_bulls", []))
    building.current_balance += sale_amount
    sale_split = prorate_cattle_sale_split(trail_drive.get("sell_cattle_split", {}), sell_cattle, sold_cattle)
    cattle_price = cattle_market_price(game.city)
    product_sale = sale_split.get("products", 0) * cattle_price
    merchandise_sale = sale_split.get("merchandise", 0) * cattle_price + sum(bull_market_price(bull) for bull in trail_drive.get("sell_bulls", []))
    if product_sale:
        record_building_sale(building, product_sale, "production_sold")
    if merchandise_sale:
        record_building_sale(building, merchandise_sale, "merchandise_sold")
    add_owner_income(game, building.owner, sale_amount)

    buy_cattle = trail_drive.get("buy_cattle", 0)
    return_workload = ranch_workload(buy_cattle, game.city.season, building, multiplier_override=0.8)
    return_surplus = ranch_workforce(game, building, crew, removed_npcs) - return_workload
    lost_return = ranch_attrition_loss(buy_cattle, ranch_attrition_rate(game.city.season, game.city.season_events, return_surplus, 0), return_surplus)
    returned_cattle = max(0, buy_cattle - lost_return)
    ensure_ranch_stock_split(building)
    building.production["head_count"] = cattle_head_count(building) + returned_cattle
    building.production["merchandise_cattle_count"] = building.production.get("merchandise_cattle_count", 0) + returned_cattle
    building.production.setdefault("bulls", []).extend(trail_drive.get("buy_bulls", []))

    hired_ids = {data.get("npc_id") for data in trail_drive.get("hired_cowboys", [])}
    for removed in removed_npcs:
        npc_data = removed.get("npc", {})
        if npc_data.get("npc_id") in hired_ids:
            continue
        npc = npc_from_saved_data(npc_data)
        if not game.city.get_npc_by_id(npc.npc_id):
            game.city.population.append(npc)
        contract = removed.get("contract", {})
        set_employee_contract(
            building,
            npc.npc_id,
            contract.get("role", removed.get("role", "Cowboy")),
            contract.get("wage"),
            contract.get("task"),
        )

    building.production.pop("trail_drive", None)
    logs.append((
        f"Trail drive - {building.name}",
        f"aller charge={round(outbound_workload, 4)}, surplus={round(outbound_surplus, 4)}, pertes={lost_outbound}; retour charge={round(return_workload, 4)}, surplus={round(return_surplus, 4)}, pertes={lost_return}; vente={format_money(sale_amount)}",
    ))
    return trail_drive_message(sold_cattle, returned_cattle, sale_amount, lost_outbound + lost_return)


def record_building_sale(building, amount, category="services_sold"):
    building.lifetime_revenue += amount
    building.annual_sales += amount
    record_accounting_product(building, category, amount, cash=False)


def add_owner_income(game, owner_name, amount):
    if owner_name == game.character.name:
        game.character.money += amount
        return
    owner = next((npc for npc in game.city.population if npc.name == owner_name), None)
    if owner:
        owner.money += amount


def trail_drive_state(building):
    return building.production.get("trail_drive")


def cattle_market_price(city):
    return market_price(city, "boeuf")


def bull_market_price(bull):
    return 40 if bull.get("age", 0) >= 5 else animal_base_price("taureau")


def cattle_head_count(building):
    from buildings import normalize_ranch_data

    normalize_ranch_data(building)
    return building.production.get("head_count", 0)


def ranch_workload(head_count, season, building=None, multiplier_override=None):
    first_slice = min(head_count, 50) * 0.02
    second_slice = min(max(head_count - 50, 0), 50) * 0.015
    third_slice = max(head_count - 100, 0) * 0.01
    base_workload = 1 + first_slice + second_slice + third_slice
    multiplier = multiplier_override if multiplier_override is not None else ranch_season_multiplier(season, building)
    return round(base_workload * multiplier, 4)


def ranch_season_multiplier(season, building):
    multipliers = {"Printemps": 1.5, "Été": 0.8, "Automne": 0.8, "Hiver": 1}
    multiplier = multipliers.get(season, 1)
    if building and season in ["Été", "Automne", "Hiver"] and "Grange" in normalize_upgrades(building.upgrades):
        multiplier += 0.2
    return multiplier


def npc_workforce_contribution(npc):
    if getattr(npc, "condition", "en forme") in ["blessé gravement", "malade"]:
        return 0
    contribution = npc.strength / 10
    if getattr(npc, "condition", "en forme") == "blessé":
        contribution /= 2
    return contribution


def character_workforce_contribution(character):
    if getattr(character, "condition", "en forme") in ["blessé gravement", "malade"]:
        return 0
    contribution = character.strength / 10
    if getattr(character, "condition", "en forme") == "blessé":
        contribution /= 2
    return contribution


def ranch_forage_gain(season, surplus):
    if season == "Été":
        if -1 <= surplus < 0:
            return 25
        if 0 <= surplus <= 1:
            return 50
        if surplus > 1:
            return 75
    if season == "Automne" and surplus > 0:
        return 25
    return 0


def ranch_food_production(season, surplus, upgrades):
    if surplus <= 0:
        return 0
    food = 0
    if "Élevage domestique" in upgrades:
        food += 2
    if "Culture et potager" in upgrades:
        if season == "Automne":
            food += min(10, math.floor(surplus / 0.1))
        elif season in ["Été", "Hiver"]:
            food += min(5, math.floor(surplus / 0.2))
    return food


def apply_ranch_attrition(building, season, season_events, surplus):
    head_count = cattle_head_count(building)
    forage = building.inventory.get("fourrage", 0)
    rate = ranch_attrition_rate(season, season_events, surplus, forage, building)
    losses = ranch_attrition_loss(head_count, rate, surplus)
    ensure_ranch_stock_split(building)
    reduce_ranch_cattle_stock(building, losses)
    building.production["head_count"] = max(0, head_count - losses)
    if season == "Hiver":
        building.inventory["fourrage"] = 0
    return losses


def ranch_attrition_rate(season, season_events, surplus, forage=0, building=None):
    if season == "Hiver":
        rate = random.uniform(8, 10)
        if "Hiver rude" in season_events:
            rate += 3
        rate -= min(4, math.floor(min(forage, RANCH_BARN_CAPACITY) / 25))
    elif season == "Printemps":
        rate = random.uniform(2, 4)
    else:
        rate = random.uniform(0.5, 2)

    if season == "Été" and "Sécheresse" in season_events:
        rate += 2 if building and "Citerne" in normalize_upgrades(building.upgrades) else 4
    return max(0, rate)


def ranch_attrition_loss(head_count, rate, surplus):
    losses = round_half_up(head_count * rate / 100)
    if surplus < 0 and losses > 0:
        losses = round_half_up(losses * math.exp(abs(surplus)))
    cap_ratio = random_normal_between(0.53, 0.63)
    return min(round_half_up(head_count * cap_ratio), losses)


def apply_ranch_calving(building):
    head_count = cattle_head_count(building)
    remaining = head_count
    births = 0
    bull_births = 0
    bulls = sorted(building.production.get("bulls", []), key=lambda bull: bull.get("fécondité", bull.get("fÃ©conditÃ©", 0)), reverse=True)
    for bull in bulls:
        if remaining <= 0:
            break
        capacity = 50 if bull.get("age", 0) >= 3 else 25
        covered = min(remaining, capacity)
        births += round_half_up(covered * (0.20 + effective_bull_fertility(bull) / 100))
        remaining -= covered
    for _ in range(births):
        if random.random() < 0.001:
            bull_births += 1
    cattle_births = births - bull_births
    ensure_ranch_stock_split(building)
    building.production["head_count"] = head_count + births
    building.production["product_cattle_count"] = building.production.get("product_cattle_count", 0) + cattle_births
    for _ in range(bull_births):
        new_bull = random_bull_market()[0]
        new_bull["age"] = 0
        new_bull["stock_type"] = "products"
        building.production.setdefault("bulls", []).append(new_bull)
    return births


def effective_bull_fertility(bull):
    fertility = bull.get("fécondité", bull.get("fÃ©conditÃ©", 8))
    minimum = fertility - 4
    maximum = fertility + 4
    value = random.gauss(fertility, 4 / 3)
    return max(minimum, min(maximum, value))


def apply_bull_mortality(building, season):
    surviving_bulls = []
    messages = []
    for bull in building.production.get("bulls", []):
        if bull_dies_this_season(bull, season):
            messages.append(f"{bull.get('nom', 'Le taureau')} est mort cette saison.")
        else:
            surviving_bulls.append(bull)
    building.production["bulls"] = surviving_bulls
    return messages


def bull_dies_this_season(bull, season):
    age = bull.get("age", 0)
    if age == 5:
        return random.randint(1, 100) <= 15
    if age >= 6:
        if season == "Hiver":
            return True
        return random.randint(1, 100) <= 25
    return False


def random_bull_market(character=None):
    market = [
        {"nom": random_bull_name(), "age": random.randint(1, 4), "fécondité": random.choice([4, 8, 12, 16])}
        for _index in range(5)
    ]
    if character and has_skill(character, "Élevage") and random.randint(1, 100) <= 75:
        market.sort(key=lambda bull: bull.get("fécondité", 0), reverse=True)
    return market


def random_bull_name():
    syllables = ["al", "bar", "cor", "del", "dor", "fer", "gar", "jos", "lor", "man", "mar", "nar", "ped", "ram", "ros", "san", "sol", "tor", "val", "zar"]
    first = random.choice(syllables)
    second = random.choice([syllable for syllable in syllables if syllable != first])
    return f"{first}{second}".capitalize()


def ranch_loss_message(losses):
    if losses == 0:
        return "Nous n'avons perdu aucune bête cette saison."
    if losses == 1:
        return "Nous avons perdu une bête cette saison."
    return f"Nous avons perdu {losses} bêtes cette saison."


def ranch_birth_message(births):
    if births == 0:
        return "Aucune bête est née cette saison."
    if births == 1:
        return "Une bête est née cette saison."
    return f"{births} bêtes sont nées cette saison."


def random_normal_between(minimum, maximum):
    center = (minimum + maximum) / 2
    deviation = (maximum - minimum) / 6
    return max(minimum, min(maximum, random.gauss(center, deviation)))


def round_half_up(value):
    return math.floor(value + 0.5)


def normalize_upgrades(upgrades):
    return ["Chambre" if upgrade == "Chambres d'hotel" else upgrade for upgrade in upgrades]


def normalize_text(value):
    return str(value).lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")


def has_skill(character, skill_name):
    normalized = normalize_text(skill_name)
    return any(normalize_text(skill) == normalized for skill in character.skills)


def trail_drive_message(sold_cattle, bought_cattle, sale_amount, losses):
    return (
        f"Résultat du long trail drive : {sold_cattle} bête(s) vendue(s), "
        f"{bought_cattle} bête(s) achetée(s), {losses} perte(s), "
        f"vente {format_money(sale_amount)}."
    )


def npc_from_removed_trail(npc_id, removed_npcs):
    for removed in removed_npcs:
        npc_data = removed.get("npc", {})
        if npc_data.get("npc_id") == npc_id:
            return npc_from_saved_data(npc_data)
    return None


def npc_from_saved_data(data):
    return NPC(
        npc_id=data.get("npc_id", "npc_unknown"),
        first_name=data.get("first_name", data.get("name", "Inconnu").split()[0]),
        last_name=data.get("last_name", data.get("name", "Inconnu").split()[-1]),
        name=data.get("name", "Inconnu"),
        sex=data.get("sex", "Homme"),
        age=data.get("age", 25),
        origin=data.get("origin", "Cowboy"),
        strength=data.get("strength", 7),
        sociability=data.get("sociability", 5),
        intelligence=data.get("intelligence", 5),
        income=data.get("income", 0),
        money=data.get("money", 0),
        job=data.get("job", "Cowboy"),
        employer_building_id=data.get("employer_building_id"),
        skills=data.get("skills", []),
        inventory=data.get("inventory", {}),
        preferences=data.get("preferences", {}),
        trait=data.get("trait", "néant"),
        condition=data.get("condition", "en forme"),
    )


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


def format_money(amount):
    amount = round(float(amount or 0), 2)
    if amount.is_integer():
        return f"{int(amount)}$"
    return f"{amount:.2f}$"
