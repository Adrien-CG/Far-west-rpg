import json
from pathlib import Path

from buildings import Building, normalize_ranch_data, specialize_building
from character import Character, NPC, generate_consumption_needs
from game_state import BASE_MARKET_PRICES, City, GameState
from housing import housing_building_from_dict, housing_unit_from_dict
from ids import make_building_id
from items.animals import clean_character_inventory_from_animals


SAVE_DIR = Path("saves")
ALL_TIME_ACHIEVEMENTS_PATH = SAVE_DIR / "all_time_achievements.json"


def load_all_time_achievements():
    SAVE_DIR.mkdir(exist_ok=True)
    if not ALL_TIME_ACHIEVEMENTS_PATH.exists():
        return []

    try:
        with ALL_TIME_ACHIEVEMENTS_PATH.open("r", encoding="utf-8") as save_file:
            data = json.load(save_file)
    except (OSError, json.JSONDecodeError):
        return []

    return data.get("achievements", [])


def save_all_time_achievements(achievements):
    SAVE_DIR.mkdir(exist_ok=True)
    with ALL_TIME_ACHIEVEMENTS_PATH.open("w", encoding="utf-8") as save_file:
        json.dump({"achievements": sorted(set(achievements))}, save_file, indent=2, ensure_ascii=False)


def reset_all_time_achievements():
    if ALL_TIME_ACHIEVEMENTS_PATH.exists():
        ALL_TIME_ACHIEVEMENTS_PATH.unlink()


def save_character(character):
    SAVE_DIR.mkdir(exist_ok=True)

    filename = character.name.lower().replace(" ", "_")
    save_path = SAVE_DIR / f"{filename}.json"

    with save_path.open("w", encoding="utf-8") as save_file:
        json.dump(character.to_dict(), save_file, indent=2, ensure_ascii=False)

    return save_path


def save_game(game):
    SAVE_DIR.mkdir(exist_ok=True)

    filename = game.character.name.lower().replace(" ", "_")
    save_path = SAVE_DIR / f"{filename}_game.json"

    with save_path.open("w", encoding="utf-8") as save_file:
        json.dump(game.to_dict(), save_file, indent=2, ensure_ascii=False)

    return save_path


def list_game_saves():
    SAVE_DIR.mkdir(exist_ok=True)
    return sorted(SAVE_DIR.glob("*_game.json"))


def get_save_display_name(save_path):
    try:
        with save_path.open("r", encoding="utf-8") as save_file:
            data = json.load(save_file)
    except (OSError, json.JSONDecodeError):
        return save_path.name

    character = data.get("character", {})
    character_name = character.get("name")

    if character_name:
        return character_name

    return save_path.name


def delete_save(save_path):
    save_path.unlink()


def load_game(save_path):
    with save_path.open("r", encoding="utf-8") as save_file:
        data = json.load(save_file)

    character = character_from_dict(data.get("character", {}))
    city_data = data.get("city", {})
    city = city_from_dict(city_data)

    return GameState(
        character=character,
        city=city,
        action_points=data.get("action_points", 0.0),
        achievements=data.get("achievements", []),
        turn_log=data.get("turn_log", []),
        seasonal_occupation=data.get("seasonal_occupation", {}),
    )


def character_from_dict(data):
    name = data.get("name", "Personnage inconnu")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    if not first_name or not last_name:
        name_parts = name.split(" ", 1)
        first_name = first_name or name_parts[0]
        last_name = last_name or (name_parts[1] if len(name_parts) > 1 else "")

    return Character(
        first_name=first_name,
        last_name=last_name,
        name=name,
        sex=data.get("sex", "Homme"),
        age=data.get("age", 25),
        origin=data.get("origin", "Cowboy"),
        strength=data.get("strength", 5),
        sociability=data.get("sociability", data.get("agility", 5)),
        intelligence=data.get("intelligence", 5),
        income=data.get("income", 0),
        money=data.get("money", data.get("gold", 0)),
        respect=data.get("respect", 0),
        celebrite=data.get("celebrite", 0),
        condition=normalize_condition(data.get("condition", "en forme")),
        job=data.get("job"),
        employer_building_id=data.get("employer_building_id"),
        residence=data.get("residence"),
        monture=data.get("monture"),
        skills=data.get("skills", []),
        inventory=clean_character_inventory_from_animals(data.get("inventory", {})),
        preferences=data.get("preferences", {}),
        consumption_needs=data.get("consumption_needs", generate_consumption_needs(None)),
        mineral_claims=data.get("mineral_claims", []),
    )


def city_from_dict(data):
    existing_ids = set()
    buildings = []
    city_name = data.get("name", "Dusty Creek")
    if city_name == "Dust Creek":
        city_name = "Dusty Creek"

    for building_data in data.get("buildings", []):
        building = building_from_dict(building_data, existing_ids)
        buildings.append(building)
        existing_ids.add(building.building_id)

    population = [
        npc_from_dict(npc_data)
        for npc_data in data.get("population", [])
    ]

    market_prices = BASE_MARKET_PRICES.copy()
    market_prices.update(data.get("market_prices", {}))

    return City(
        name=city_name,
        day=data.get("day", 1),
        season="Été" if data.get("season") == "Ete" else data.get("season", "Printemps"),
        year=data.get("year", 1865),
        season_events=data.get("season_events", []),
        climat=data.get("climat", "tempéré"),
        humidite=data.get("humidite", "sec"),
        base_wage=data.get("base_wage", 7),
        transport_cost_per_weight=data.get("transport_cost_per_weight", 0.5),
        market_prices=market_prices,
        reputation=data.get("reputation", 0),
        security=data.get("security", 50),
        buildings=buildings,
        population=population,
        mineral_deposits=data.get("mineral_deposits", []),
        housing_units=[
            housing_unit_from_dict(housing_data)
            for housing_data in data.get("housing_units", [])
        ],
        housing_buildings=[
            housing_building_from_dict(housing_data)
            for housing_data in data.get("housing_buildings", [])
        ],
    )


def building_from_dict(data, existing_ids):
    building_type = data.get("building_type", "Batiment inconnu")
    if building_type == "Chirurgien barbier":
        building_type = "Barber shop"
    building_id = data.get("building_id")
    building_name = data.get("name", building_type)
    if building_name == "Chirurgien-barbier":
        building_name = "Barber shop"

    if not building_id or building_id in existing_ids:
        building_id = make_building_id(building_type, existing_ids)

    building = Building(
        building_id=building_id,
        name=building_name,
        building_type=building_type,
        owner=data.get("owner", "Inconnu"),
        level=data.get("level", 1),
        is_public=data.get("is_public", False),
        location=data.get("location", "Ville"),
        visible=data.get("visible", True),
        building_kind=data.get("building_kind", "economique"),
        features=data.get("features", {}),
        hidden_stats=data.get("hidden_stats", {}),
        inventory=data.get("inventory", {}),
        production=data.get("production", {}),
        employees=data.get("employees", []),
        employee_roles=data.get("employee_roles", {}),
        employee_tasks=data.get("employee_tasks", {}),
        employee_contracts=employee_contracts_from_data(data),
        upgrades=data.get("upgrades", []),
        current_balance=data.get("current_balance", 0),
        current_result=data.get("current_result", 0),
        balance_history=data.get("balance_history", []),
        result_history=data.get("result_history", []),
        account_journal=data.get("account_journal", []),
        under_construction=data.get("under_construction", False),
        investment_value=data.get("investment_value", data.get("current_balance", 0)),
        lifetime_revenue=data.get("lifetime_revenue", 0),
        lifetime_expenses=data.get("lifetime_expenses", 0),
        annual_sales=data.get("annual_sales", 0),
        annual_purchases=data.get("annual_purchases", 0),
        annual_wages=data.get("annual_wages", 0),
        previous_annual_sales=data.get("previous_annual_sales", 0),
        previous_annual_purchases=data.get("previous_annual_purchases", 0),
        previous_annual_wages=data.get("previous_annual_wages", 0),
        previous_annual_stock_value=data.get("previous_annual_stock_value", 0),
        previous_annual_result=data.get("previous_annual_result", 0),
        fire_risk=data.get("fire_risk", 0.01),
        accounting=data.get("accounting", {}),
    )
    return specialize_building(normalize_ranch_data(building))


def employee_contracts_from_data(data):
    contracts = data.get("employee_contracts")
    if contracts is not None:
        return contracts

    roles = data.get("employee_roles", {})
    tasks = data.get("employee_tasks", {})
    result = {}
    for employee_id in data.get("employees", []):
        role = roles.get(employee_id, "Employé")
        contract = {"role": role, "wage": default_contract_wage(role)}
        if employee_id in tasks:
            contract["task"] = tasks[employee_id]
        result[employee_id] = contract
    return result


def default_contract_wage(role):
    wages = {
        "Barman": 6,
        "Cuisinier": 6,
        "Hotesse": 5,
        "Cowboy": 7,
        "Infirmière": 6,
        "Adjoint du sherif": 9,
        "Employe du Post Office": 8,
        "Pasteur": 10,
        "Chirurgien barbier": 12,
        "Commis": 5,
        "Bonne": 4,
    }
    return wages.get(role, 5)


def npc_from_dict(data):
    return NPC(
        npc_id=data.get("npc_id", "npc_unknown"),
        first_name=data.get("first_name", "Inconnu"),
        last_name=data.get("last_name", ""),
        name=data.get("name", "Inconnu"),
        sex=data.get("sex", "Homme"),
        age=data.get("age", 30),
        origin=data.get("origin", "Cowboy"),
        strength=data.get("strength", 5),
        sociability=data.get("sociability", 5),
        intelligence=data.get("intelligence", 5),
        income=data.get("income", 0),
        money=data.get("money", 0),
        respect=data.get("respect", 0),
        celebrite=data.get("celebrite", 0),
        skills=data.get("skills", []),
        condition=normalize_condition(data.get("condition", "en forme")),
        job=data.get("job", "Oisif"),
        employer_building_id=data.get("employer_building_id"),
        residence=data.get("residence"),
        monture=data.get("monture"),
        spouse_id=data.get("spouse_id"),
        notable=data.get("notable", False),
        inventory=clean_character_inventory_from_animals(data.get("inventory", {})),
        trait=normalize_trait(data.get("trait", "néant")),
        preferences=data.get("preferences", {}),
        consumption_needs=data.get("consumption_needs", generate_consumption_needs(None)),
        mineral_claims=data.get("mineral_claims", []),
    )


def normalize_condition(condition):
    if condition == "inconscient":
        return "blessé gravement"
    return condition


def normalize_trait(trait):
    if trait == "vice":
        return "luxure"
    return trait
