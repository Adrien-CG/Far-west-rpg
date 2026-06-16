"""Etat general de la partie.

Plan du fichier:
01 - constantes globales: prix, saisons et regles sociales.
02 - helpers de partie: revenu global, saison, vieillissement.
03 - City: donnees de carte et de ville.
04 - GameState: donnees de partie.
05 - create_new_game: creation de Dusty Creek.
"""

from dataclasses import asdict, dataclass, field

from buildings import Building, create_starter_buildings, normalize_ranch_data
from goods_services import base_market_prices
from housing import HousingBuilding, HousingUnit
from items.animals import ANIMAL_CATALOG
from character import NPC, assign_population_preferences, create_npc, job_spec
from actions.prospecting import generate_map_deposits


BASE_MARKET_PRICES = base_market_prices()
SEASONS = ["Printemps", "Été", "Automne", "Hiver"]

# Règles sociales simples liées aux métiers.
# Gîte : le travailleur est nourri sur place.
# Logement : le travailleur est logé par l'employeur.
JOBS_WITH_INCLUDED_BOARD = {"Cowboy"}
JOBS_WITH_INCLUDED_LODGING = {"Cowboy"}
PROPERTY_TYPES_WITH_OWNER_BOARD = {"Ranch"}
PROPERTY_TYPES_WITH_OWNER_LODGING = {"Ranch"}


def job_has_included_board(job):
    return job in JOBS_WITH_INCLUDED_BOARD


def job_has_included_lodging(job):
    return job in JOBS_WITH_INCLUDED_LODGING


def property_type_has_owner_board(building_type):
    return building_type in PROPERTY_TYPES_WITH_OWNER_BOARD


def property_type_has_owner_lodging(building_type):
    return building_type in PROPERTY_TYPES_WITH_OWNER_LODGING


def city_global_income(city):
    """Revenu global de la ville, utilise comme PIB local simplifie.

    Les voyageurs ne comptent pas : ils sont une population temporaire et ne
    doivent pas gonfler l'attractivite economique de la saison suivante.
    """
    return sum(npc.income for npc in city.population if npc.job != "Voyageur")


def advance_season(city):
    """Passe a la saison suivante et indique si une nouvelle annee commence."""
    current_index = SEASONS.index(city.season) if city.season in SEASONS else 0
    if current_index == len(SEASONS) - 1:
        city.season = SEASONS[0]
        city.year += 1
        return True

    city.season = SEASONS[current_index + 1]
    return False


def age_population_one_year(game):
    """Vieillit le joueur, les PNJ et tous les animaux connus."""
    game.character.age += 1
    for npc in game.city.population:
        npc.age += 1
    for building in game.city.buildings:
        if building.building_type == "Ranch":
            normalize_ranch_data(building)
        age_animals_in_container(building.production)
        age_animals_in_container(building.inventory)


def age_animals_in_container(container):
    """Parcourt listes/dictionnaires et vieillit les objets animaux trouves."""
    if isinstance(container, list):
        for value in container:
            age_animals_in_container(value)
        return

    if not isinstance(container, dict):
        return

    if is_animal_instance(container):
        container["age"] = container.get("age", 0) + 1

    for value in container.values():
        if isinstance(value, (dict, list)):
            age_animals_in_container(value)


def is_animal_instance(data):
    animal_type = data.get("animal_type") or data.get("type_animal")
    if animal_type in ANIMAL_CATALOG and "age" in data:
        return True
    # Les taureaux existants n'ont pas encore tous un champ animal_type.
    return "age" in data and ("fécondité" in data or "fÃ©conditÃ©" in data or "fertility" in data)


@dataclass
class City:
    name: str
    day: int = 1
    season: str = "Printemps"
    year: int = 1865
    season_events: list[str] = field(default_factory=list)
    climat: str = "tempéré"
    humidite: str = "sec"
    base_wage: float = 7
    transport_cost_per_weight: float = 0.5
    market_prices: dict[str, float] = field(default_factory=lambda: BASE_MARKET_PRICES.copy())
    reputation: int = 0
    security: int = 50
    buildings: list[Building] = field(default_factory=list)
    population: list[NPC] = field(default_factory=list)
    mineral_deposits: list[dict[str, object]] = field(default_factory=list)
    housing_units: list[HousingUnit] = field(default_factory=list)
    housing_buildings: list[HousingBuilding] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def get_building_by_id(self, building_id):
        for building in self.buildings:
            if building.building_id == building_id:
                return building

        return None

    def get_npc_by_id(self, npc_id):
        for npc in self.population:
            if npc.npc_id == npc_id:
                return npc

        return None


@dataclass
class GameState:
    character: object
    city: City
    action_points: float = 0.0
    achievements: list[str] = field(default_factory=list)
    turn_log: list[str] = field(default_factory=list)
    seasonal_occupation: dict[str, object] = field(default_factory=dict)

    def to_dict(self):
        return {
            "character": self.character.to_dict(),
            "city": self.city.to_dict(),
            "action_points": self.action_points,
            "achievements": self.achievements,
            "turn_log": self.turn_log,
            "seasonal_occupation": self.seasonal_occupation,
        }


def create_dusty_creek_population(player_starting_activity=None):
    """Cree la population initiale propre a la carte Dusty Creek.

    `character.py` sait creer un personnage; la carte decide ici quels PNJ
    existent au depart, quels emplois sont deja pourvus et quels notables ont
    une epouse.
    """
    used_names = set()
    population = []

    employed_specs = [
        job_spec("npc_general_store_owner_001", "Tenancier du General Store", "general_store_001", "Langue d'argent"),
        job_spec("npc_sheriff_001", "Sherif", "sheriff_office_001", "Cowboy", important=True, extra_skills=["Chasse", "Jugement"], weapon=True),
        job_spec("npc_deputy_001", "Adjoint du sherif", "sheriff_office_001", "Cowboy", weapon=True),
        job_spec("npc_post_worker_001", "Employe du Post Office", "post_office_001", "Homme de l'Est"),
        job_spec("npc_pastor_001", "Pasteur", "church_001", "Homme de l'Est", important=True, extra_skills=["Jugement"]),
        job_spec("npc_barber_surgeon_001", "Chirurgien barbier", "barber_surgeon_001", "Homme de l'Est"),
        job_spec("npc_ranch_001_owner", "Proprietaire de ranch", "ranch_001", "Cowboy", important=True, extra_skills=["Élevage", "Dressage"]),
        job_spec("npc_ranch_001_cowboy_001", "Cowboy", "ranch_001", "Cowboy", extra_skills=["Élevage"]),
        job_spec("npc_ranch_001_cowboy_002", "Cowboy", "ranch_001", "Cowboy"),
        job_spec("npc_ranch_002_owner", "Proprietaire de ranch", "ranch_002", "Cowboy", important=True, extra_skills=["Élevage", "Dressage"]),
        job_spec("npc_ranch_002_cowboy_001", "Cowboy", "ranch_002", "Cowboy", extra_skills=["Élevage"]),
        job_spec("npc_ranch_002_cowboy_002", "Cowboy", "ranch_002", "Cowboy"),
    ]
    if player_starting_activity != "saloon":
        employed_specs.insert(
            6,
            job_spec(
                "npc_saloon_owner_001",
                "Proprietaire de saloon",
                "saloon_001",
                "Langue d'argent",
                important=True,
                extra_skills=["Charisme", "Jeu"],
            ),
        )

    for spec in employed_specs:
        population.append(create_npc(used_names=used_names, **spec))

    important_people = [npc for npc in population if npc.notable]
    population.extend(create_initial_spouses(important_people, used_names))

    unemployed_count = max(5, round(len(population) * 0.10))
    female_unemployed_count = max(1, round(unemployed_count * 0.10))
    male_unemployed_count = unemployed_count - female_unemployed_count

    for index in range(male_unemployed_count):
        population.append(create_npc(
            npc_id=f"npc_unemployed_male_{index + 1:03d}",
            character_class="pas de préférence",
            npc_type="lambda",
            age_group="aléatoire",
            sex="Homme",
            job="Chomeur",
            used_names=used_names,
        ))

    for index in range(female_unemployed_count):
        population.append(create_npc(
            npc_id=f"npc_unemployed_female_{index + 1:03d}",
            character_class="pas de préférence",
            npc_type="lambda",
            age_group="aléatoire",
            sex="Femme",
            job="Chomeuse",
            used_names=used_names,
        ))

    assign_population_preferences(population)
    return population


def create_initial_spouses(important_people, used_names):
    """Cree les epouses de depart puis delegue le mariage a la demographie."""
    from demography import marry_characters

    spouses = []
    for person in important_people:
        spouse = create_npc(
            npc_id=f"{person.npc_id}_spouse",
            character_class="pas de préférence",
            npc_type="lambda",
            age_group=initial_spouse_age_group(person),
            sex="Femme" if person.sex == "Homme" else "Homme",
            job="Oisive" if person.sex == "Homme" else "Oisif",
            used_names=used_names,
        )
        marry_characters(person, spouse, used_names=used_names)
        spouses.append(spouse)
    return spouses


def initial_spouse_age_group(person):
    if person.age <= 30:
        return "jeune"
    return "moyen"


def create_new_game(character, city_name="Dusty Creek", player_starting_activity=None):
    population = create_dusty_creek_population(player_starting_activity=player_starting_activity)
    city = City(
        name=city_name,
        climat="tempéré",
        humidite="sec",
        buildings=create_starter_buildings(character.name, population, player_starting_activity),
        population=population,
        mineral_deposits=generate_map_deposits(),
    )

    return GameState(character=character, city=city)
