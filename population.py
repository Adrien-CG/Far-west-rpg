from dataclasses import asdict, dataclass, field
import random


MALE_FIRST_NAMES = [
    "Abel", "Abraham", "Ambrose", "Amos", "Augustus", "Bartholomew",
    "Benjamin", "Caleb", "Cassius", "Clyde", "Cornelius", "Cyrus",
    "Darius", "Elias", "Elijah", "Emmett", "Ephraim", "Ezra",
    "Felix", "Gideon", "Grady", "Harlan", "Hiram", "Hollis",
    "Isaac", "Jedediah", "Jesse", "Jonah", "Josiah", "Levi",
    "Lucius", "Malachi", "Marshall", "Micah", "Nathaniel", "Orson",
    "Phineas", "Quentin", "Rufus", "Samuel", "Silas", "Solomon",
    "Thaddeus", "Thomas", "Tobias", "Virgil", "Walter", "Wyatt",
]

FEMALE_FIRST_NAMES = [
    "Abigail", "Ada", "Adelaide", "Agnes", "Alice", "Beatrice",
    "Clara", "Clementine", "Cora", "Dorothy", "Edith", "Eleanor",
    "Eliza", "Esther", "Florence", "Georgia", "Grace", "Harriet",
    "Ida", "Josephine", "Lillian", "Louisa", "Mabel", "Martha",
    "Matilda", "Nora", "Opal", "Pearl", "Prudence", "Rose",
    "Sadie", "Sarah", "Susannah", "Vera", "Violet", "Winifred",
]

LAST_NAMES = [
    "Abbott", "Bell", "Blackwood", "Boone", "Briggs", "Callahan",
    "Carver", "Cassidy", "Clay", "Cooper", "Crawford", "Dawson",
    "Doyle", "Drake", "Dunleavy", "Fletcher", "Garrett", "Graves",
    "Hale", "Harlow", "Hawkins", "Holliday", "Kincaid", "Langley",
    "McCoy", "Mercer", "Nolan", "Parker", "Pickett", "Reed",
    "Rourke", "Sawyer", "Slater", "Sullivan", "Turner", "Walker",
    "Whitmore", "Winchester", "Wolfe", "Wright",
]

ORIGIN_WEIGHTS = {
    "Cowboy": 70,
    "Langue d'argent": 20,
    "Homme de l'Est": 10,
}

UNEMPLOYED_JOBS = ["Journalier", "Oisif", "Chômeur"]
FEMALE_SERVICE_JOBS = ["Journaliere", "Oisive", "Chômeuse"]


@dataclass
class NPC:
    npc_id: str
    first_name: str
    last_name: str
    name: str
    sex: str
    age: int
    origin: str
    strength: int
    sociability: int
    intelligence: int
    health: int
    max_health: int
    income: int
    money: int
    skills: list[str] = field(default_factory=list)
    job: str = "Oisif"
    employer_building_id: str | None = None
    spouse_id: str | None = None
    notable: bool = False
    inventory: dict[str, int] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def generate_population():
    used_names = set()
    population = []

    fixed_jobs = [
        {
            "npc_id": "npc_general_store_owner_001",
            "first_name": "Silas",
            "last_name": "Reed",
            "sex": "Homme",
            "age": 46,
            "origin": "Langue d'argent",
            "job": "Tenancier du General Store",
            "employer_building_id": "general_store_001",
            "notable": True,
            "stat_bonus": {"sociability": 4},
            "skills": ["commerce", "negociation"],
            "income": 18,
            "money": 80,
        },
        {
            "npc_id": "npc_sheriff_001",
            "first_name": "Wyatt",
            "last_name": "Dawson",
            "sex": "Homme",
            "age": 41,
            "origin": "Cowboy",
            "job": "Sherif",
            "employer_building_id": "sheriff_office_001",
            "notable": True,
            "stat_bonus": {"strength": 4, "intelligence": 2},
            "skills": ["tir", "autorite", "enquete"],
            "inventory": {"revolver": 1},
            "income": 16,
            "money": 60,
        },
        {
            "npc_id": "npc_deputy_001",
            "first_name": "Caleb",
            "last_name": "Parker",
            "sex": "Homme",
            "age": 29,
            "origin": "Cowboy",
            "job": "Adjoint du sherif",
            "employer_building_id": "sheriff_office_001",
            "stat_bonus": {"strength": 2},
            "skills": ["tir", "patrouille"],
            "inventory": {"revolver": 1},
            "income": 9,
            "money": 35,
        },
        {
            "npc_id": "npc_post_worker_001",
            "first_name": "Thomas",
            "last_name": "Whitmore",
            "sex": "Homme",
            "age": 34,
            "origin": "Homme de l'Est",
            "job": "Employe du Post Office",
            "employer_building_id": "post_office_001",
            "stat_bonus": {"intelligence": 4},
            "skills": ["lecture", "ecriture", "comptabilite"],
            "income": 8,
            "money": 40,
        },
        {
            "npc_id": "npc_ranch_owner_001",
            "first_name": "Elias",
            "last_name": "McCoy",
            "sex": "Homme",
            "age": 52,
            "origin": "Cowboy",
            "job": "Proprietaire de ranch",
            "employer_building_id": "ranch_001",
            "notable": True,
            "stat_bonus": {"strength": 2, "sociability": 2},
            "skills": ["elevage", "gestion"],
            "income": 22,
            "money": 100,
        },
        {
            "npc_id": "npc_ranch_foreman_001",
            "first_name": "Hiram",
            "last_name": "Walker",
            "sex": "Homme",
            "age": 38,
            "origin": "Cowboy",
            "job": "Contremaitre",
            "employer_building_id": "ranch_001",
            "stat_bonus": {"strength": 3, "intelligence": 1},
            "skills": ["elevage", "discipline"],
            "income": 11,
            "money": 45,
        },
        {
            "npc_id": "npc_ranch_cowboy_001",
            "first_name": "Jonah",
            "last_name": "Bell",
            "sex": "Homme",
            "age": 27,
            "origin": "Cowboy",
            "job": "Cowboy",
            "employer_building_id": "ranch_001",
            "stat_bonus": {"strength": 2},
            "skills": ["elevage", "equitation"],
            "income": 7,
            "money": 25,
        },
        {
            "npc_id": "npc_ranch_cowboy_002",
            "first_name": "Levi",
            "last_name": "Cooper",
            "sex": "Homme",
            "age": 24,
            "origin": "Cowboy",
            "job": "Cowboy",
            "employer_building_id": "ranch_001",
            "stat_bonus": {"strength": 2},
            "skills": ["elevage", "equitation"],
            "income": 7,
            "money": 25,
        },
    ]

    for job_data in fixed_jobs:
        population.append(create_npc(used_names=used_names, **job_data))

    employed_count = len(population)
    unemployed_count = max(5, round(employed_count * 0.05))

    for index in range(unemployed_count):
        population.append(
            create_random_npc(
                npc_id=f"npc_unemployed_{index + 1:03d}",
                used_names=used_names,
                sex="Homme",
                job=random.choice(UNEMPLOYED_JOBS),
                employer_building_id=None,
            )
        )

    male_count = len([npc for npc in population if npc.sex == "Homme"])
    female_count = male_count // 2

    for index in range(female_count):
        population.append(
            create_random_npc(
                npc_id=f"npc_townswoman_{index + 1:03d}",
                used_names=used_names,
                sex="Femme",
                job=random.choice(FEMALE_SERVICE_JOBS),
                employer_building_id=None,
            )
        )

    create_marriages(population)
    return population


def create_random_npc(npc_id, used_names, sex, job, employer_building_id=None):
    first_name, last_name = pick_unique_name(used_names, sex)
    origin = random.choices(
        list(ORIGIN_WEIGHTS.keys()),
        weights=list(ORIGIN_WEIGHTS.values()),
        k=1,
    )[0]
    income = income_for_job(job)

    return create_npc(
        npc_id=npc_id,
        first_name=first_name,
        last_name=last_name,
        sex=sex,
        age=random.randint(14, 65),
        origin=origin,
        job=job,
        employer_building_id=employer_building_id,
        skills=skills_for_job(job),
        income=income,
        money=random.randint(3, 25) + income,
        used_names=used_names,
    )


def create_npc(
    npc_id,
    first_name,
    last_name,
    sex,
    age,
    origin,
    job,
    employer_building_id=None,
    notable=False,
    stat_bonus=None,
    skills=None,
    inventory=None,
    income=0,
    money=20,
    used_names=None,
):
    stat_bonus = stat_bonus or {}
    inventory = inventory or {}
    skills = skills or []
    base_stats = stats_for_origin(origin, sex)

    strength = clamp_stat(base_stats["strength"] + stat_bonus.get("strength", 0))
    sociability = clamp_stat(base_stats["sociability"] + stat_bonus.get("sociability", 0))
    intelligence = clamp_stat(base_stats["intelligence"] + stat_bonus.get("intelligence", 0))
    health = 80 + strength * 5
    name = f"{first_name} {last_name}"

    if used_names is not None:
        used_names.add(name)

    return NPC(
        npc_id=npc_id,
        first_name=first_name,
        last_name=last_name,
        name=name,
        sex=sex,
        age=age,
        origin=origin,
        strength=strength,
        sociability=sociability,
        intelligence=intelligence,
        health=health,
        max_health=health,
        income=income,
        money=money,
        skills=skills,
        job=job,
        employer_building_id=employer_building_id,
        notable=notable,
        inventory=inventory,
    )


def pick_unique_name(used_names, sex):
    first_names = MALE_FIRST_NAMES if sex == "Homme" else FEMALE_FIRST_NAMES
    candidates = [
        (first_name, last_name)
        for first_name in first_names
        for last_name in LAST_NAMES
        if f"{first_name} {last_name}" not in used_names
    ]

    if not candidates:
        suffix = len(used_names) + 1
        return random.choice(first_names), f"{random.choice(LAST_NAMES)} {suffix}"

    first_name, last_name = random.choice(candidates)
    used_names.add(f"{first_name} {last_name}")
    return first_name, last_name


def stats_for_origin(origin, sex):
    female_strength_shift = -2 if sex == "Femme" else 0

    if origin == "Cowboy":
        return {
            "strength": random.randint(6, 9) + female_strength_shift,
            "sociability": random.randint(3, 6),
            "intelligence": random.randint(3, 6),
        }

    if origin == "Langue d'argent":
        return {
            "strength": random.randint(3, 6) + female_strength_shift,
            "sociability": random.randint(7, 10),
            "intelligence": random.randint(4, 7),
        }

    return {
        "strength": random.randint(2, 5) + female_strength_shift,
        "sociability": random.randint(4, 7),
        "intelligence": random.randint(7, 10),
    }


def income_for_job(job):
    incomes = {
        "Tenancier du General Store": 18,
        "Sherif": 16,
        "Adjoint du sherif": 9,
        "Employe du Post Office": 8,
        "Proprietaire de ranch": 22,
        "Contremaitre": 11,
        "Cowboy": 7,
        "Journalier": 4,
        "Journaliere": 3,
        "Couturiere": 4,
        "Aubergiste": 5,
        "Oisif": 0,
        "Oisive": 0,
        "Chomeur": 0,
        "Chomeuse": 0,
    }
    return incomes.get(job, 0)


def skills_for_job(job):
    skills = {
        "Journalier": ["travail manuel"],
        "Journaliere": ["service"],
        "Couturiere": ["couture"],
        "Aubergiste": ["service", "cuisine"],
        "Chomeur": [],
        "Chomeuse": [],
        "Oisif": [],
        "Oisive": [],
    }
    return skills.get(job, [])


def clamp_stat(value):
    return max(1, min(12, value))


def create_marriages(population):
    men = [npc for npc in population if npc.sex == "Homme" and npc.spouse_id is None and npc.age >= 18]
    women = [npc for npc in population if npc.sex == "Femme" and npc.spouse_id is None and npc.age >= 18]
    random.shuffle(men)
    random.shuffle(women)

    couples_to_create = min(len(men), len(women), random.randint(1, max(1, len(women))))

    for index in range(couples_to_create):
        husband = men[index]
        wife = women[index]
        husband.spouse_id = wife.npc_id
        wife.spouse_id = husband.npc_id
