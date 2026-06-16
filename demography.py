"""Demographie: voyageurs, colons, departs et etats de sante.

Plan du fichier:
01 - constantes saison/sante: coefficients et risques.
02 - run_*: fonctions appelees par la fin de tour.
03 - voyageurs: calcul et creation des voyageurs.
04 - colons: arrivees, profils et departs.
05 - sante: accidents, priorites d'etat et resolution.
06 - petits helpers: roles, textes et normalisation.

Le module regroupe les regles de population utilisees par la fin de tour.
L'interface n'a donc plus besoin de connaitre le detail des calculs : elle
demande seulement a ce module de traiter une etape et d'ecrire le journal.
"""

import math
import random

from buildings import employee_ids, employee_role, remove_employee_contract
from game_state import city_global_income
from character import create_npc, create_traveler


SEASONAL_MOVEMENT_COEFFICIENTS = {
    "Printemps": 1,
    "Été": 1.5,
    "Automne": 1.2,
    "Hiver": 0.5,
}

SEASONAL_COLON_COEFFICIENTS = {
    "Printemps": 1,
    "Été": 1.5,
    "Automne": 1.2,
    "Hiver": 0,
}

HEALTH_INCIDENT_PROFILES = {
    "default": {
        "blessé": 0.03,
        "blessé gravement": 0.005,
        "malade": 0.015,
    },
    "cowboy": {
        "blessé": 0.07,
        "blessé gravement": 0.02,
        "malade": 0.01,
    },
}


def run_health_incidents(app):
    """Ajoute les nouveaux accidents et maladies au debut de la simulation."""
    alerts = app.turn_context.setdefault("messages", [])
    messages = assign_new_health_incidents(app.game, alerts)
    detail = " | ".join(messages) if messages else "Aucun nouvel accident ou maladie grave."
    app.log_turn_step("Accidents et maladies", detail)


def run_traveler_generation(app):
    """Supprime les voyageurs precedents puis genere ceux de la saison."""
    removed_count, traveler_count, travelers = create_season_travelers(app.game.city)
    traveler_names = ", ".join(traveler.name for traveler in travelers) if travelers else "aucun"
    app.log_turn_step(
        "Voyageurs",
        f"{removed_count} voyageur(s) précédent(s) supprimé(s). "
        f"{traveler_count} foyer(s), {len(travelers)} personne(s) générée(s) : {traveler_names}.",
    )


def run_colon_arrivals(app):
    """Genere les nouveaux colons de la saison."""
    colon_count, colons = create_season_colons(app.game.city)
    colon_names = ", ".join(colon.name for colon in colons) if colons else "aucun"
    app.log_turn_step(
        "Arrivées de colons",
        f"{colon_count} foyer(s), {len(colons)} personne(s) générée(s) : {colon_names}.",
    )


def run_colon_departures(app):
    """Fait partir les chomeurs excedentaires."""
    departure_message = process_colon_departures(app.game.city)
    app.log_turn_step("Départs de colons", departure_message)


def run_demography_summary(app):
    app.log_turn_step(
        "Démographie de fin de tour",
        "Voyageurs, colons et départs traités. Aucun calcul de criminalité pour l'instant.",
    )


def run_health_resolution(app):
    """Resout les guerisons et complications liees aux etats de sante."""
    messages = process_health_changes(app.game)
    detail = " | ".join(messages) if messages else "Aucune résolution ou complication de santé."
    app.log_turn_step("Résolution santé", detail)


def create_season_travelers(city):
    """Cree les voyageurs selon les chambres disponibles, le revenu local et la gare."""
    removed_count = remove_previous_travelers(city)
    traveler_count = seasonal_traveler_count(city)
    average_wage = average_unqualified_income(city.population)
    used_names = {npc.name for npc in city.population}
    travelers = []

    for index in range(traveler_count):
        travelers.extend(create_traveler_household(city, average_wage, used_names, index + 1))

    city.population.extend(travelers)
    return removed_count, traveler_count, travelers


def create_season_colons(city):
    """Cree les nouveaux colons sans emploi."""
    colon_count = seasonal_colon_count(city)
    used_names = {npc.name for npc in city.population}
    colons = []

    for index in range(colon_count):
        colons.extend(create_colon_household(city, used_names, index + 1))

    city.population.extend(colons)
    return colon_count, colons


def average_unqualified_income(population):
    incomes = [
        npc.income
        for npc in population
        if npc.job != "Voyageur" and npc.income > 0
    ]
    if not incomes:
        return 10
    return sum(incomes) / len(incomes)


def seasonal_traveler_count(city):
    room_count = city_room_count(city)
    if room_count <= 0:
        return 0

    multiplier = (city_global_income(city) / 100) * seasonal_movement_coefficient(city)
    traveler_count = math.ceil(room_count * multiplier)
    traveler_count = max(1, traveler_count)
    if city_has_train_station(city):
        traveler_count *= 10
    return traveler_count


def seasonal_colon_count(city):
    multiplier = (city_global_income(city) / 100) * seasonal_colon_coefficient(city)
    colon_count = math.ceil(multiplier)
    if city_has_train_station(city):
        colon_count += vacant_jobs_count(city)
    return colon_count


def vacant_jobs_count(city):
    total = 0
    for building in city.buildings:
        if getattr(building, "under_construction", False):
            continue
        for role in recruitable_roles(building):
            total += max(0, role_limit(building, role) - role_count(building, role))
    return total


def seasonal_movement_coefficient(city):
    return SEASONAL_MOVEMENT_COEFFICIENTS.get(city.season, 1)


def seasonal_colon_coefficient(city):
    return SEASONAL_COLON_COEFFICIENTS.get(city.season, 1)


def city_room_count(city):
    return sum(
        normalize_upgrades(building.upgrades).count("Chambre")
        for building in city.buildings
        if building.building_type == "Saloon"
    )


def city_has_train_station(city):
    return any(
        "gare" in normalize_text(building.name) or "gare" in normalize_text(building.building_type)
        for building in city.buildings
    )


def remove_previous_travelers(city):
    removed_count = len([npc for npc in city.population if npc.job == "Voyageur"])
    city.population = [npc for npc in city.population if npc.job != "Voyageur"]
    return removed_count


def traveler_female_chance(city):
    return 25 if city_has_train_station(city) else 10


def random_arrival_sex(city):
    return "Femme" if random.randint(1, 100) <= traveler_female_chance(city) else "Homme"


def colon_origin(city):
    roll = random.randint(1, 100)
    if city_has_train_station(city):
        if roll <= 55:
            return "cowboy"
        if roll <= 85:
            return "langue d'argent"
        return "homme de l'est"

    if roll <= 75:
        return "cowboy"
    if roll <= 95:
        return "langue d'argent"
    return "homme de l'est"


def create_traveler_household(city, average_wage, used_names, index):
    primary = create_traveler(
        f"npc_traveler_{city.day:03d}_{len(city.population) + index:03d}",
        average_wage,
        used_names=used_names,
        sex=random_arrival_sex(city),
    )
    household = [primary]
    if random.randint(1, 100) <= 25:
        spouse = create_traveler(
            f"{primary.npc_id}_spouse",
            average_wage,
            used_names=used_names,
            sex="Femme" if primary.sex == "Homme" else "Homme",
        )
        marry_characters(primary, spouse, used_names=used_names)
        apply_married_traveler_budget_rules(primary, spouse)
        household.append(spouse)
    return household


def create_colon_household(city, used_names, index):
    sex = random_arrival_sex(city)
    primary = create_npc(
        npc_id=f"npc_colon_{city.day:03d}_{len(city.population) + index:03d}",
        character_class=colon_origin(city),
        npc_type="lambda",
        age_group="aléatoire",
        sex=sex,
        job="Chomeuse" if sex == "Femme" else "Chomeur",
        income=0,
        used_names=used_names,
    )
    primary.job = "Chomeuse" if primary.sex == "Femme" else "Chomeur"
    household = [primary]
    if random.randint(1, 100) <= 25:
        spouse = create_npc(
            npc_id=f"{primary.npc_id}_spouse",
            character_class="pas de préférence",
            npc_type="lambda",
            age_group=age_group_for_colon_spouse(primary),
            sex="Femme" if primary.sex == "Homme" else "Homme",
            job="Chomeuse" if primary.sex == "Homme" else "Chomeur",
            income=0,
            used_names=used_names,
        )
        marry_characters(primary, spouse, used_names=used_names)
        household.append(spouse)
    return household


def age_group_for_colon_spouse(primary):
    if primary.age <= 30:
        return "jeune"
    return "moyen"


def link_spouses(first, second):
    first.spouse_id = second.npc_id
    second.spouse_id = first.npc_id


def marry_characters(first, second, used_names=None):
    """Officialise un mariage et applique le nom familial au personnage feminin.

    La creation des deux personnages reste faite par `create_npc`; cette
    fonction ne gere que le lien social et les champs qui dependent du mariage.
    """
    link_spouses(first, second)
    woman, man = married_woman_and_man(first, second)
    if woman and man:
        old_name = woman.name
        woman.last_name = man.last_name
        woman.name = f"{woman.first_name} {woman.last_name}"
        if used_names is not None:
            used_names.discard(old_name)
            used_names.add(woman.name)


def married_woman_and_man(first, second):
    if first.sex == "Femme" and second.sex == "Homme":
        return first, second
    if second.sex == "Femme" and first.sex == "Homme":
        return second, first
    return None, None


def apply_married_traveler_budget_rules(first, second):
    for traveler in [first, second]:
        if traveler.sex == "Femme":
            traveler.money = 0
            traveler.preferences.setdefault("chambre", {})[1] = 0


def process_colon_departures(city):
    unemployed = [npc for npc in city.population if is_unemployed(npc)]
    non_unemployed_count = len([
        npc for npc in city.population
        if npc.job != "Voyageur" and not is_unemployed(npc)
    ])
    allowed_unemployed = max(3, round_half_up(non_unemployed_count * 0.03))
    departure_count = max(0, len(unemployed) - allowed_unemployed)
    if departure_count <= 0:
        return f"Aucun départ. Chômeurs : {len(unemployed)}, seuil toléré : {allowed_unemployed}."

    shuffled_unemployed = list(unemployed)
    random.shuffle(shuffled_unemployed)
    kept_unemployed = sorted(
        shuffled_unemployed,
        key=lambda npc: (npc.income, npc.money),
        reverse=True,
    )[:allowed_unemployed]
    kept_ids = {npc.npc_id for npc in kept_unemployed}
    departing = [npc for npc in unemployed if npc.npc_id not in kept_ids]
    for npc in departing:
        remove_departing_npc(city, npc)

    names = ", ".join(npc.name for npc in departing)
    return f"{len(departing)} chômeur(s) quittent la ville : {names}."


def is_unemployed(npc):
    return npc.job in ["Chomeur", "Chomeuse"]


def remove_departing_npc(city, npc):
    city.population = [person for person in city.population if person.npc_id != npc.npc_id]
    for survivor in city.population:
        if survivor.spouse_id == npc.npc_id:
            survivor.spouse_id = None


def assign_new_health_incidents(game, alerts=None):
    messages = []
    for npc in game.city.population:
        if npc.job == "Voyageur" or npc.condition != "en forme":
            continue
        incident = draw_health_incident(npc)
        if incident:
            apply_health_condition(npc, incident, game=game, alerts=alerts)
            messages.append(f"{npc.name} devient {incident}.")
    return messages


def draw_health_incident(npc):
    profile = HEALTH_INCIDENT_PROFILES["cowboy"] if is_cowboy_job(npc.job) else HEALTH_INCIDENT_PROFILES["default"]
    roll = random.random()
    cumulative = 0
    for condition in ["blessé", "blessé gravement", "malade"]:
        cumulative += profile[condition]
        if roll < cumulative:
            return condition
    return None


def is_cowboy_job(job):
    return job in ["Cowboy", "Trail boss"]


def apply_health_condition(character, new_condition, game=None, alerts=None):
    current_condition = getattr(character, "condition", "en forme")
    if health_condition_rank(new_condition) > health_condition_rank(current_condition):
        character.condition = new_condition
        alert = player_health_alert(character, new_condition, game)
        if alert and alerts is not None:
            alerts.append(alert)


def health_condition_rank(condition):
    return {
        "en forme": 0,
        "blessé": 1,
        "malade": 2,
        "blessé gravement": 3,
        "mort": 4,
    }.get(condition, 0)


def player_health_alert(character, new_condition, game):
    if not game:
        return None
    if character is game.character:
        return f"{character.name}, vous êtes {health_condition_phrase(new_condition)}."

    employee_info = player_employee_info(game, getattr(character, "npc_id", None))
    if not employee_info:
        return None
    role, building = employee_info
    return f"{character.name}, votre {role.lower()} de {building.name} {health_condition_verb(new_condition)}."


def player_employee_info(game, npc_id):
    if not npc_id:
        return None
    for building in game.city.buildings:
        if building.owner != game.character.name or npc_id not in employee_ids(building):
            continue
        return employee_role(building, npc_id, "employé"), building
    return None


def health_condition_phrase(condition):
    if condition == "malade":
        return "tombé malade"
    if condition == "blessé gravement":
        return "gravement blessé"
    if condition == "blessé":
        return "blessé"
    return condition


def health_condition_verb(condition):
    if condition == "malade":
        return "est tombé malade"
    if condition == "blessé gravement":
        return "s'est gravement blessé"
    if condition == "blessé":
        return "s'est blessé"
    return f"est {condition}"


def process_health_changes(game):
    messages = []
    for npc in list(game.city.population):
        if npc.job == "Voyageur" or npc.condition == "en forme":
            continue
        outcome = next_health_condition(npc.condition, game.city.season, game.city.season_events)
        if outcome != npc.condition:
            messages.append(f"{npc.name} : {npc.condition} -> {outcome}")
            npc.condition = outcome
    return messages


def next_health_condition(condition, season, season_events):
    complication_bonus = health_complication_bonus(condition, season, season_events)
    roll = random.randint(1, 100)
    if condition == "blessé":
        if roll <= 60:
            return "en forme"
        if roll <= 95:
            return "blessé"
        return "blessé gravement"
    if condition == "malade":
        complication_chance = min(50, 5 + complication_bonus)
        if roll <= complication_chance:
            return "malade"
        if roll <= complication_chance + 50:
            return "en forme"
        return "malade"
    if condition == "blessé gravement":
        complication_chance = min(60, 10 + complication_bonus)
        if roll <= complication_chance:
            return "blessé gravement"
        return "blessé"
    return condition


def health_complication_bonus(condition, season, season_events):
    bonus = 0
    if condition == "malade" and season == "Hiver":
        bonus += 5
    if "Hiver rude" in season_events:
        if condition == "malade":
            bonus += 10
        if condition == "blessé gravement":
            bonus += 5
    return bonus


def remove_dead_npc(city, npc):
    city.population = [person for person in city.population if person.npc_id != npc.npc_id]
    for building in city.buildings:
        remove_employee_contract(building, npc.npc_id)
    for survivor in city.population:
        if survivor.spouse_id == npc.npc_id:
            survivor.spouse_id = None


def medical_patients(population):
    return [
        npc for npc in population
        if npc.job != "Voyageur" and npc.condition in ["blessé", "malade", "blessé gravement"]
    ]


def health_severity(npc):
    return {"blessé gravement": 3, "malade": 2, "blessé": 1}.get(npc.condition, 0)


def improved_health_condition(condition):
    if condition == "blessé gravement":
        return "blessé"
    return "en forme"


def recruitable_roles(building):
    if building.building_type == "Saloon":
        roles = ["Barman"]
        if "Cuisine" in normalize_upgrades(building.upgrades):
            roles.append("Cuisinier")
        if room_count(building) > 0:
            roles.append("Hotesse")
        return roles
    if building.building_type == "Ranch":
        return ["Cowboy"]
    if building.building_type == "Cabinet médical" and medical_bed_count(building) > 0:
        return ["Infirmière"]
    if building.building_type == "General Store" and "Réserve" in normalize_upgrades(building.upgrades):
        return ["Commis"]
    if building.building_type == "Mine":
        roles = ["Mineur"]
        if "Corps de garde" in normalize_upgrades(building.upgrades):
            roles.append("Garde")
        if "Bureau de l'ingénieur" in normalize_upgrades(building.upgrades):
            roles.append("Ingénieur")
        return roles
    return []


def role_count(building, role):
    return len([
        employee_id for employee_id in employee_ids(building)
        if employee_role(building, employee_id) == role
    ])


def role_limit(building, role):
    upgrades = normalize_upgrades(building.upgrades)
    if building.building_type == "Saloon":
        limits = {"Barman": 1, "Cuisinier": 1, "Hotesse": room_count(building)}
        return limits.get(role, 0)
    if building.building_type == "Ranch" and role == "Cowboy":
        return 1 + upgrades.count("Baraquements") * 2
    if building.building_type == "Cabinet médical":
        return 1 if role == "Infirmière" and medical_bed_count(building) > 0 else 0
    if building.building_type == "General Store":
        return 1 if role == "Commis" and "Réserve" in upgrades else 0
    if building.building_type == "Mine":
        if role == "Mineur":
            return 9999
        if role == "Garde":
            return 4 if "Corps de garde" in upgrades else 0
        if role == "Ingénieur":
            return 1 if "Bureau de l'ingénieur" in upgrades else 0
    return 0


def room_count(building):
    return normalize_upgrades(building.upgrades).count("Chambre")


def medical_bed_count(building):
    return int(building.production.get("medical_beds", 0))


def normalize_upgrades(upgrades):
    return [normalized_upgrade_name(upgrade) for upgrade in upgrades]


def normalized_upgrade_name(upgrade):
    if upgrade == "Chambres d'hotel":
        return "Chambre"
    return upgrade


def normalize_text(value):
    return (
        str(value)
        .lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
    )


def round_half_up(value):
    return math.floor(value + 0.5)
