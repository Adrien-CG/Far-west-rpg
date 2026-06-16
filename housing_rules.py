"""Regles de logement.

Plan du fichier:
01 - constantes de standing: hierarchie des logements.
02 - synchronisation: logements generes par les batiments.
03 - attribution: residence du joueur, des employes et tentes provisoires.
04 - affichage metier: libelles courts reutilises par l'UI.

Ce fichier contient les regles de jeu. Le catalogue des types de logements reste
dans housing.py, et l'interface ne fait qu'appeler ces fonctions.
"""

from housing import HOUSING_TYPES, MARRIED_FORBIDDEN_HOUSING_TYPES, HousingUnit, create_housing_unit, vacant_listed_housing_units


HOUSING_STANDING_ORDER = [
    "tente",
    "baraquement",
    "cabane",
    "chambre",
    "appartement",
    "maison_campagne",
    "maison_ville",
    "maison_bourgeoise",
]


def sync_property_housing(city):
    """Actualise les logements produits par les batiments existants."""
    for building in getattr(city, "buildings", []):
        generator = getattr(building, "generate_housing_units", None)
        if generator:
            generator(city)
    sync_married_residences(city.population)


def ensure_building_housing_units(city, building):
    """Point d'entree commun appele par l'UI; la regle vit dans le batiment."""
    generator = getattr(building, "generate_housing_units", None)
    if generator:
        return generator(city)
    return None


def improve_player_housing_if_needed(city, character):
    """En fin de tour, reloge seulement si le joueur n'a rien ou vit en tente."""
    sync_property_housing(city)
    current = current_housing_unit(city, character)
    if current and current.housing_type != "tente":
        return None
    return assign_best_unoccupied_owned_housing(city, character)


def assign_best_unoccupied_owned_housing(city, character):
    owned = [
        housing for housing in getattr(city, "housing_units", [])
        if housing.owner == character.name
        and (not housing.occupants or housing.occupants == [character.name])
    ]
    if not owned:
        return None
    best = max(owned, key=housing_standing_value)
    clear_character_residence(city, character)
    best.occupants = [character.name]
    character.residence = best.housing_id
    return best


def current_housing_unit(city, character):
    residence_id = getattr(character, "residence", None)
    if not residence_id:
        return None
    return next((housing for housing in getattr(city, "housing_units", []) if housing.housing_id == residence_id), None)


def housing_action_label(city, character):
    return "Déménager" if current_housing_unit(city, character) else "Trouver un logement"


def housing_standing_value(housing):
    try:
        return HOUSING_STANDING_ORDER.index(housing.housing_type)
    except ValueError:
        return -1


def sync_building_units(city, building, housing_type, target_count, listed=True):
    listed = listed and not building_is_countryside(building)
    existing = building_housing_units(city, building, housing_type)
    while len(existing) < target_count:
        housing_id = f"{building.building_id}_{housing_type}_{len(existing) + 1:03d}"
        city.housing_units.append(create_building_housing_unit(housing_id, building, housing_type, listed))
        existing = building_housing_units(city, building, housing_type)
    for housing in existing:
        if not housing.occupants or housing.occupants == ["voyageur"]:
            housing.listed = listed
    return existing


def create_building_housing_unit(housing_id, building, housing_type, listed):
    data = HOUSING_TYPES[housing_type]
    return HousingUnit(
        housing_id=housing_id,
        housing_type=housing_type,
        owner=building.owner,
        building_id=building.building_id,
        utility=data["utility"],
        salubrity=data["salubrity"],
        fire_risk=data["fire_risk"],
        rent_price=data["rent_price"],
        electricity=data.get("electricity", False),
        water=data.get("water", False),
        included_board=data.get("included_board", False),
        bath=data.get("bath", False),
        listed=listed,
    )


def building_housing_units(city, building, housing_type=None):
    units = [
        housing for housing in getattr(city, "housing_units", [])
        if housing.building_id == building.building_id
    ]
    if housing_type:
        units = [housing for housing in units if housing.housing_type == housing_type]
    return units


def run_temporary_housing(city, player):
    """Applique le logement provisoire de fin de tour et retourne un resume."""
    player_housing = improve_player_housing_if_needed(city, player)
    created = ensure_population_has_tents(city)
    detail = f"{created} tente(s) provisoire(s) générée(s)." if created else "Tout le monde a déjà un logement."
    if player_housing:
        detail += f" Le joueur occupe maintenant {housing_label(player_housing)}."
    return {"created": created, "player_housing": player_housing, "summary": detail}


def ensure_population_has_tents(city):
    """Cree une tente non listee pour chaque habitant sans residence."""
    created = 0
    for npc in city.population:
        if npc.job == "Voyageur" or married_woman_waits_for_spouse_home(npc):
            continue
        if ensure_valid_residence(city, npc):
            continue
        create_personal_tent(city, npc)
        created += 1

    sync_married_residences(city.population)

    for npc in city.population:
        if npc.job == "Voyageur":
            continue
        if ensure_valid_residence(city, npc):
            continue
        create_personal_tent(city, npc)
        created += 1

    sync_married_residences(city.population)
    return created


def married_woman_waits_for_spouse_home(npc):
    return npc.sex == "Femme" and bool(npc.spouse_id)


def ensure_valid_residence(city, character):
    residence_id = getattr(character, "residence", None)
    if not residence_id:
        return False
    housing = next((unit for unit in city.housing_units if unit.housing_id == residence_id), None)
    if not housing:
        character.residence = None
        return False
    if character.name not in housing.occupants:
        housing.occupants.append(character.name)
    return True


def create_personal_tent(city, npc):
    housing_id = next_free_tent_id(city)
    tent = create_housing_unit(housing_id, "tente", npc.name, None)
    tent.listed = False
    tent.occupants = [npc.name]
    city.housing_units.append(tent)
    npc.residence = housing_id
    return tent


def next_free_tent_id(city):
    existing_ids = {housing.housing_id for housing in city.housing_units}
    index = len(existing_ids) + 1
    housing_id = f"tent_free_{index:04d}"
    while housing_id in existing_ids:
        index += 1
        housing_id = f"tent_free_{index:04d}"
    return housing_id


def housing_label(housing):
    return HOUSING_TYPES.get(housing.housing_type, {}).get("label", housing.housing_type)


def available_housing_for_character(city, character):
    return [
        housing
        for housing in vacant_listed_housing_units(city)
        if not (
            housing.housing_type in MARRIED_FORBIDDEN_HOUSING_TYPES
            and character_is_married(city, character)
        )
    ]


def housing_choice_label(city, housing):
    owner = housing.owner or "Inconnu"
    building = city.get_building_by_id(housing.building_id) if housing.building_id else None
    source = f" - {building.name}" if building else ""
    return f"{housing_label(housing)}{source} | propriétaire : {owner} | loyer : {format_money(housing.rent_price)}"


def housing_mode_label(mode):
    return "voyageurs" if mode == "voyageurs" else "location longue durée"


def character_is_married(city, character):
    spouse_id = getattr(character, "spouse_id", None)
    if spouse_id:
        return True
    if getattr(character, "sex", None) == "Femme":
        return False
    return any(npc.spouse_id == getattr(character, "npc_id", None) for npc in city.population)


def clear_character_residence(city, character):
    old_residence = getattr(character, "residence", None)
    if not old_residence:
        return
    for housing in city.housing_units:
        if housing.housing_id == old_residence:
            housing.occupants = [
                occupant for occupant in housing.occupants
                if occupant != character.name
            ]
    character.residence = None


def assign_employee_housing(city, building, npc):
    generator = getattr(building, "generate_housing_units", None)
    if generator:
        generator(city)
    if building.building_type == "Ranch" and npc.job == "Cowboy":
        for housing in building_housing_units(city, building):
            if housing.listed or housing.occupants:
                continue
            if housing.housing_type not in ["chambre", "baraquement"]:
                continue
            housing.occupants = [npc.name]
            npc.residence = housing.housing_id
            sync_married_residences(city.population)
            return housing
    if building.building_type == "Mine" and npc.job in ["Mineur", "Garde"]:
        preferred_types = ["baraquement", "tente"] if npc.job == "Mineur" else ["baraquement"]
        for housing_type in preferred_types:
            for housing in building_housing_units(city, building, housing_type):
                if housing.listed or housing.occupants:
                    continue
                housing.occupants = [npc.name]
                npc.residence = housing.housing_id
                sync_married_residences(city.population)
                return housing
    return None


def sync_married_residences(population):
    by_id = {npc.npc_id: npc for npc in population}
    for npc in population:
        if npc.sex != "Femme" or not npc.spouse_id:
            continue
        spouse = by_id.get(npc.spouse_id)
        if spouse:
            npc.residence = spouse.residence


def building_is_countryside(building):
    return building.building_type in ["Ranch", "Mine", "Ferme", "Camp de bucheron"]


def format_money(amount):
    amount = round(float(amount or 0), 2)
    if amount.is_integer():
        return f"{int(amount)}$"
    return f"{amount:.2f}$"
