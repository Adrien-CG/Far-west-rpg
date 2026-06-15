import json
from pathlib import Path

from buildings import Building
from character import Character
from game_state import City, GameState
from ids import make_building_id
from population import NPC


SAVE_DIR = Path("saves")


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

    return GameState(character=character, city=city)


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
        health=data.get("health", 100),
        max_health=data.get("max_health", data.get("health", 100)),
        income=data.get("income", 0),
        money=data.get("money", data.get("gold", 0)),
        skills=data.get("skills", []),
        inventory=data.get("inventory", {}),
    )


def city_from_dict(data):
    existing_ids = set()
    buildings = []

    for building_data in data.get("buildings", []):
        building = building_from_dict(building_data, existing_ids)
        buildings.append(building)
        existing_ids.add(building.building_id)

    population = [
        npc_from_dict(npc_data)
        for npc_data in data.get("population", [])
    ]

    return City(
        name=data.get("name", "Dust Creek"),
        day=data.get("day", 1),
        reputation=data.get("reputation", 0),
        security=data.get("security", 50),
        buildings=buildings,
        population=population,
    )


def building_from_dict(data, existing_ids):
    building_type = data.get("building_type", "Batiment inconnu")
    building_id = data.get("building_id")

    if not building_id or building_id in existing_ids:
        building_id = make_building_id(building_type, existing_ids)

    return Building(
        building_id=building_id,
        name=data.get("name", building_type),
        building_type=building_type,
        owner=data.get("owner", "Inconnu"),
        level=data.get("level", 1),
        is_public=data.get("is_public", False),
        features=data.get("features", {}),
        hidden_stats=data.get("hidden_stats", {}),
        inventory=data.get("inventory", {}),
        production=data.get("production", {}),
        employees=data.get("employees", []),
        employee_roles=data.get("employee_roles", {}),
        employee_tasks=data.get("employee_tasks", {}),
        upgrades=data.get("upgrades", []),
        current_balance=data.get("current_balance", 0),
        current_result=data.get("current_result", 0),
        balance_history=data.get("balance_history", []),
        result_history=data.get("result_history", []),
        account_journal=data.get("account_journal", []),
    )


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
        health=data.get("health", 100),
        max_health=data.get("max_health", data.get("health", 100)),
        income=data.get("income", 0),
        money=data.get("money", 0),
        skills=data.get("skills", []),
        job=data.get("job", "Oisif"),
        employer_building_id=data.get("employer_building_id"),
        spouse_id=data.get("spouse_id"),
        notable=data.get("notable", False),
        inventory=data.get("inventory", {}),
    )
