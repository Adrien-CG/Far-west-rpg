from dataclasses import asdict, dataclass, field
import random

from goods_services import ITEM_CATALOG, item_definition, preference_centers_for
from items.animals import clean_character_inventory_from_animals

MALE_FIRST_NAMES = [
    "Abel", "Abraham", "Ambrose", "Amos", "Augustus", "Bartholomew",
    "Benjamin", "Caleb", "Cassius", "Clyde", "Cornelius", "Cyrus",
    "Darius", "Elias", "Elijah", "Emmett", "Ephraim", "Ezra",
    "Felix", "Gideon", "Grady", "Harlan", "Hiram", "Hollis",
    "Isaac", "Jedediah", "Jesse", "Jonah", "Josiah", "Levi",
    "Lucius", "Malachi", "Marshall", "Micah", "Nathaniel", "Orson",
    "Phineas", "Quentin", "Rufus", "Samuel", "Silas", "Solomon",
    "Thaddeus", "Thomas", "Tobias", "Virgil", "Walter", "Wyatt",
    "Albert", "Alfred", "Andrew", "Arthur", "Bennett", "Booker",
    "Chester", "Clarence", "Clayton", "Clifford", "Daniel", "Duncan",
    "Edgar", "Edwin", "Everett", "Franklin", "George", "Grant",
    "Harvey", "Henry", "Howard", "Irving", "Jackson", "James",
    "Lawrence", "Luther", "Martin", "Milton", "Morgan", "Nelson",
    "Oscar", "Percival", "Preston", "Randolph", "Raymond", "Roland",
    "Seth", "Theodore", "Wallace", "Warren", "Wesley", "William",
]

FEMALE_FIRST_NAMES = [
    "Abigail", "Ada", "Adelaide", "Agnes", "Alice", "Beatrice",
    "Clara", "Clementine", "Cora", "Dorothy", "Edith", "Eleanor",
    "Eliza", "Esther", "Florence", "Georgia", "Grace", "Harriet",
    "Ida", "Josephine", "Lillian", "Louisa", "Mabel", "Martha",
    "Matilda", "Nora", "Opal", "Pearl", "Prudence", "Rose",
    "Sadie", "Sarah", "Susannah", "Vera", "Violet", "Winifred",
    "Annabelle", "Belle", "Bessie", "Caroline", "Charlotte", "Daisy",
    "Delilah", "Etta", "Evelyn", "Fannie", "Frances", "Gertrude",
    "Helen", "Henrietta", "Irene", "Jane", "Julia", "Katherine",
    "Laura", "Lucille", "Maggie", "Mae", "Margaret", "Marion",
    "Minnie", "Nancy", "Olive", "Pauline", "Rebecca", "Ruby",
    "Ruth", "Stella", "Virginia", "Vivian", "Willie",
]

LAST_NAMES = [
    "Abbott", "Bell", "Blackwood", "Boone", "Briggs", "Callahan",
    "Carver", "Cassidy", "Clay", "Cooper", "Crawford", "Dawson",
    "Doyle", "Drake", "Dunleavy", "Fletcher", "Garrett", "Graves",
    "Hale", "Harlow", "Hawkins", "Holliday", "Kincaid", "Langley",
    "McCoy", "Mercer", "Nolan", "Parker", "Pickett", "Reed",
    "Rourke", "Sawyer", "Slater", "Sullivan", "Turner", "Walker",
    "Whitmore", "Winchester", "Wolfe", "Wright", "Archer", "Barker",
    "Barlow", "Baxter", "Bishop", "Blevins", "Bradford", "Brennan",
    "Bridger", "Brooks", "Burke", "Caldwell", "Cannon", "Chambers",
    "Coleman", "Conway", "Dalton", "Ellis", "Foster", "Garrison",
    "Goodwin", "Hardin", "Harrington", "Hayes", "Henderson", "Houston",
    "Keller", "Laramie", "Lawson", "Maddox", "Mason", "Montgomery",
    "Owen", "Prescott", "Ramsey", "Remington", "Russell", "Sheridan",
    "Stafford", "Sterling", "Talbot", "Thornton", "Vaughn", "Watson",
    "Webster", "West", "Whitaker", "York",
]

HEALTH_STATES = ["blessé", "malade", "blessé gravement"]
RANDOM_TRAITS = ["néant", "alcoolique", "moraliste", "croyant", "économe", "luxure"]
PHYSICAL_SKILLS = ["Élevage", "Chasse", "Prospection", "Dressage"]
SOCIAL_SKILLS = ["Jugement", "Charisme", "Jeu"]
INTELLIGENCE_SKILLS = ["Jugement", "Jeu", "Artificier"]
NEUTRAL_SKILLS = ["Cuisine"]
PREFERENCE_SPREAD = 0.1
ZERO_PREFERENCE = 0


@dataclass
class CharacterBase:
    """Base commune de donnees pour joueur et PNJ.

    Les classes `Character` et `NPC` gardent leurs constructeurs historiques
    pour ne pas casser les sauvegardes et l'interface, mais les champs communs
    restent documentes ici dans le fichier personnage.
    """
    first_name: str = ""
    last_name: str = ""
    name: str = ""
    sex: str = "Homme"
    age: int = 25
    origin: str = ""
    strength: int = 5
    sociability: int = 5
    intelligence: int = 5
    income: float = 0
    money: float = 0
    respect: int = 0
    celebrite: int = 0
    condition: str = "en forme"
    job: str | None = None
    employer_building_id: str | None = None
    residence: str | None = None
    monture: dict[str, object] | None = None
    skills: list[str] = field(default_factory=list)
    inventory: dict[str, float] = field(default_factory=dict)
    preferences: dict[str, dict[int, float]] = field(default_factory=dict)
    consumption_needs: dict[str, int] = field(default_factory=dict)
    mineral_claims: list[dict[str, object]] = field(default_factory=list)
    is_player: bool = False

    def to_dict(self):
        clean_character_inventory_from_animals(self.inventory)
        return asdict(self)


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
    income: int
    money: int
    respect: int = 0
    celebrite: int = 0
    skills: list[str] = field(default_factory=list)
    condition: str = "en forme"
    job: str = "Oisif"
    employer_building_id: str | None = None
    residence: str | None = None
    monture: dict[str, object] | None = None
    spouse_id: str | None = None
    notable: bool = False
    inventory: dict[str, int] = field(default_factory=dict)
    trait: str = "néant"
    preferences: dict[str, dict[int, float]] = field(default_factory=dict)
    consumption_needs: dict[str, int] = field(default_factory=dict)
    mineral_claims: list[dict[str, object]] = field(default_factory=list)
    is_player: bool = False

    def to_dict(self):
        clean_character_inventory_from_animals(self.inventory)
        return asdict(self)


def job_spec(npc_id, job, employer_building_id, character_class, important=False, extra_skills=None, weapon=False, fixed_age=None):
    return {
        "npc_id": npc_id,
        "character_class": character_class,
        "npc_type": "important" if important else "lambda",
        "age_group": "aléatoire",
        "sex": "Homme",
        "fixed_age": fixed_age,
        "job": job,
        "employer_building_id": employer_building_id,
        "notable": important,
        "extra_skills": extra_skills or [],
        "force_weapon": weapon,
        "income": income_for_job(job),
    }


def create_npc(
    npc_id,
    character_class="pas de préférence",
    npc_type="lambda",
    age_group="aléatoire",
    sex="aléatoire",
    job="Oisif",
    employer_building_id=None,
    notable=False,
    extra_skills=None,
    force_weapon=False,
    income=None,
    used_names=None,
    fixed_age=None,
):
    if used_names is None:
        used_names = set()

    sex = resolve_sex(sex)
    first_name, last_name = pick_unique_name(used_names, sex)
    origin = resolve_origin(character_class)
    strength, sociability, intelligence, dominant_stat = generate_stats(origin, npc_type, sex)
    skills = choose_skills(dominant_stat, sex, extra_skills or [])
    inventory = {}
    if force_weapon or should_receive_weapon(origin, dominant_stat, sex):
        inventory["colt_navy"] = 1

    income = income_for_job(job) if income is None else income
    age = fixed_age if fixed_age is not None else random_npc_age(age_group)
    if npc_type == "important":
        age = max(31, min(45, age))
    money = random_money(npc_type)

    trait = "croyant" if job == "Pasteur" else random.choice(RANDOM_TRAITS)
    npc = NPC(
        npc_id=npc_id,
        first_name=first_name,
        last_name=last_name,
        name=f"{first_name} {last_name}",
        sex=sex,
        age=age,
        origin=origin,
        strength=strength,
        sociability=sociability,
        intelligence=intelligence,
        income=income,
        money=money,
        skills=skills,
        condition="en forme",
        job=job,
        employer_building_id=employer_building_id,
        notable=notable,
        inventory=inventory,
        trait=trait,
    )
    npc.preferences = generate_preferences(npc)
    npc.consumption_needs = generate_consumption_needs(npc)
    return npc


def create_traveler(npc_id, average_wage, used_names=None, sex="aléatoire"):
    traveler = create_npc(
        npc_id=npc_id,
        character_class="pas de préférence",
        npc_type="lambda",
        age_group="aléatoire",
        sex=sex,
        job="Voyageur",
        income=0,
        used_names=used_names,
    )
    traveler.money = round(average_wage * random.uniform(0.8, 1.6), 2)
    traveler.preferences = generate_traveler_preferences(traveler)
    traveler.consumption_needs = generate_consumption_needs(traveler)
    return traveler


def assign_population_preferences(population):
    for npc in population:
        npc.preferences = generate_preferences(npc)
        npc.consumption_needs = generate_consumption_needs(npc)


def generate_preferences(npc):
    return generate_preferences_from_catalog(npc)


def generate_consumption_needs(_character):
    """Besoins stables servant de centre aux envies saisonnières."""
    return {
        "cafe": draw_integer_normal_between(0, 10, 5),
        "tabac": draw_integer_normal_between(0, 10, 5),
    }


def draw_integer_normal_between(minimum, maximum, center):
    sigma = (maximum - minimum) / 6
    value = round(random.gauss(center, sigma))
    return max(minimum, min(maximum, value))


def generate_traveler_preferences(npc):
    centers = {}
    for item_id, data in ITEM_CATALOG.items():
        if data["type"] not in ["bien", "service"]:
            continue

        saturation = data["saturation"]
        if saturation == 0:
            centers[item_id] = []
        elif saturation == "unique":
            centers[item_id] = [0]
        elif saturation in ["elevee", "moyenne"]:
            centers[item_id] = preference_centers_for_npc(npc, item_id)[:1]
        elif saturation == "faible":
            centers[item_id] = preference_centers_for_npc(npc, item_id)[:3]
        else:
            centers[item_id] = preference_centers_for_npc(npc, item_id)

    centers["epargne_don"] = [0]
    centers["chambre"] = [1]
    return generate_preferences_from_centers(npc, centers)


def generate_preferences_from_catalog(npc):
    centers = {
        item_id: preference_centers_for_npc(npc, item_id)
        for item_id, data in ITEM_CATALOG.items()
        if data["type"] in ["bien", "service"]
    }
    centers["epargne_don"] = [1.2]
    return generate_preferences_from_centers(npc, centers)


def preference_centers_for_npc(npc, item_id):
    centers = preference_centers_for(item_id)
    bonus = preference_bonus_for_item(npc, item_id)
    if bonus:
        centers = [round(center + bonus, 4) for center in centers]
        if item_definition(item_id)["saturation"] in ["faible", "moyenne"]:
            step = largest_preference_step(preference_centers_for(item_id))
            next_value = round(centers[-1] - step, 4)
            while next_value > 0:
                centers.append(next_value)
                next_value = round(next_value - step, 4)
    return centers


def largest_preference_step(centers):
    if len(centers) < 2:
        return 0.2
    return max(round(abs(centers[index] - centers[index + 1]), 4) for index in range(len(centers) - 1))


def preference_bonus_for_item(npc, item_id):
    if item_definition(item_id)["family"] == "vivres":
        return 0.6
    trait = getattr(npc, "trait", "néant")
    if item_id == "biere" and trait == "alcoolique":
        return 1
    if item_id == "epargne_don" and trait in ["moraliste", "croyant", "économe"]:
        return 0.5
    return 0


def generate_preferences_from_centers(npc, centers):
    preferences = {}
    used_coefficients = set()

    for good, good_centers in centers.items():
        preferences[good] = {}
        for rank, center in enumerate(good_centers, start=1):
            preferences[good][rank] = preference_value(npc, good, rank, center, used_coefficients)

    return preferences


def preference_value(npc, good, rank, center, used_coefficients):
    if center == ZERO_PREFERENCE:
        return ZERO_PREFERENCE

    for _attempt in range(100):
        base_value = draw_preference_centered_on(center, preference_spread(good, rank))
        value = apply_preference_modifiers(base_value, npc, good)
        if value == ZERO_PREFERENCE:
            return ZERO_PREFERENCE
        if value not in used_coefficients:
            used_coefficients.add(value)
            return value

    # Secours rare : si les arrondis tombent trop souvent pareil, on décale très légèrement.
    value = apply_preference_modifiers(draw_preference_centered_on(center, preference_spread(good, rank)), npc, good)
    while value != ZERO_PREFERENCE and value in used_coefficients:
        value = round(value + 0.0001, 4)
    if value != ZERO_PREFERENCE:
        used_coefficients.add(value)
    return value


def draw_preference_centered_on(center, spread):
    minimum = center - spread
    maximum = center + spread
    # Ecart-type resserré : la majorité des tirages reste proche du centre.
    value = random.gauss(center, spread / 3)
    value = max(minimum, min(maximum, value))
    return round(value, 4)


def preference_spread(good, rank):
    if good in ITEM_CATALOG and ITEM_CATALOG[good]["saturation"] == "elevee" and rank == 1:
        return 0.4
    if good in ITEM_CATALOG and ITEM_CATALOG[good]["saturation"] == "elevee":
        return 0.2
    return PREFERENCE_SPREAD


def apply_preference_modifiers(value, npc, good):
    family = preference_family(good)
    trait = getattr(npc, "trait", "néant")
    if good == "coupe" and npc.sex == "Femme":
        return ZERO_PREFERENCE

    if good == "biere":
        if trait == "moraliste":
            return ZERO_PREFERENCE
        if npc.sex == "Femme":
            value -= 0.5

    if good == "hotesse":
        if npc.sex == "Femme" or trait in ["moraliste", "croyant"]:
            return ZERO_PREFERENCE
        if getattr(npc, "spouse_id", None):
            value -= 0.5

    if family == "arme_courte" and not allows_short_weapon_preference(npc):
        return ZERO_PREFERENCE

    if family == "arme_longue" and not allows_long_weapon_preference(npc):
        return ZERO_PREFERENCE

    return round(max(0, value), 4)


def preference_family(good):
    if good in ITEM_CATALOG:
        return ITEM_CATALOG[good]["family"]
    return good


def allows_short_weapon_preference(npc):
    if npc.sex == "Femme":
        return random.randint(1, 100) <= 10
    origin = getattr(npc, "origin", "")
    if origin == "Homme de l'Est":
        return random.randint(1, 100) <= 25
    if origin == "Langue d'argent":
        return random.randint(1, 100) <= 75
    return True


def allows_long_weapon_preference(npc):
    if npc.sex == "Femme":
        return random.randint(1, 100) <= 10
    origin = getattr(npc, "origin", "")
    if origin in ["Langue d'argent", "Homme de l'Est"]:
        return random.randint(1, 100) <= 50
    return True


def resolve_sex(sex):
    if sex in ["Homme", "homme", "hommes"]:
        return "Homme"
    if sex in ["Femme", "femme", "femmes"]:
        return "Femme"
    return random.choice(["Homme", "Femme"])


def resolve_origin(character_class):
    if character_class in ["Cowboy", "cowboy"]:
        return "Cowboy"
    if character_class in ["Langue d'argent", "langue d'argent"]:
        return "Langue d'argent"
    if character_class in ["Homme de l'Est", "homme de l'est"]:
        return "Homme de l'Est"
    return random.choice(["Cowboy", "Langue d'argent", "Homme de l'Est"])


def generate_stats(origin, npc_type, sex):
    dominant_stat = dominant_stat_for_origin(origin)
    stat_order = [dominant_stat, *random.sample([stat for stat in ["strength", "sociability", "intelligence"] if stat != dominant_stat], 2)]
    values = {
        stat_order[0]: random.randint(8, 11),
        stat_order[1]: random.randint(6, 9),
        stat_order[2]: random.randint(5, 8),
    }

    if sex == "Femme":
        values["strength"] -= 2
        values["sociability"] += 1

    if npc_type == "important":
        for stat in values:
            values[stat] += 2
        max_stat = 15
    else:
        max_stat = 12

    return (
        clamp_stat(values["strength"], max_stat),
        clamp_stat(values["sociability"], max_stat),
        clamp_stat(values["intelligence"], max_stat),
        dominant_stat,
    )


def dominant_stat_for_origin(origin):
    if origin == "Cowboy":
        return "strength"
    if origin == "Langue d'argent":
        return "sociability"
    return "intelligence"


def choose_skills(dominant_stat, sex, extra_skills):
    available = skills_for_dominant_stat(dominant_stat)
    if sex == "Femme" and dominant_stat == "strength" and random.randint(1, 100) > 10:
        available = ["Jugement", "Charisme"]
    available = available + NEUTRAL_SKILLS

    skills = [random.choice(available)]
    for skill in extra_skills:
        if skill not in skills:
            skills.append(skill)
    return skills


def skills_for_dominant_stat(dominant_stat):
    if dominant_stat == "strength":
        return PHYSICAL_SKILLS
    if dominant_stat == "sociability":
        return SOCIAL_SKILLS
    return INTELLIGENCE_SKILLS + ["Artificier"]


def should_receive_weapon(origin, dominant_stat, sex):
    if sex == "Femme":
        if origin == "Homme de l'Est":
            return False
        return random.randint(1, 100) <= 10

    if origin == "Cowboy" or dominant_stat == "strength":
        chance = 50
    elif origin == "Langue d'argent" or dominant_stat == "sociability":
        chance = 25
    else:
        chance = 10
    return random.randint(1, 100) <= chance


def random_money(npc_type="lambda"):
    if npc_type == "important":
        return max(51, min(120, round(random.gauss(70, 15), 2)))
    return max(5, min(25, round(random.gauss(15, 5), 2)))


def random_npc_age(age_group="aléatoire"):
    if age_group in ["jeune", "young"]:
        return random.randint(18, 30)
    if age_group in ["moyen", "middle"]:
        return random.randint(31, 45)
    if age_group in ["vieux", "old"]:
        return random.randint(36, 45)
    return random.choice([
        random.randint(18, 30),
        random.randint(18, 30),
        random.randint(18, 30),
        random.randint(31, 45),
        random.randint(36, 45),
    ])


def age_group_for_age(age):
    if age <= 30:
        return "jeune"
    if age <= 45:
        return "moyen"
    return "vieux"


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
        first_name = random.choice(first_names)
        last_name = f"{random.choice(LAST_NAMES)} {suffix}"
    else:
        first_name, last_name = random.choice(candidates)

    used_names.add(f"{first_name} {last_name}")
    return first_name, last_name


def income_for_job(job):
    incomes = {
        "Tenancier du General Store": 18,
        "Sherif": 16,
        "Adjoint du sherif": 9,
        "Employe du Post Office": 8,
        "Pasteur": 10,
        "Chirurgien barbier": 12,
        "Proprietaire de saloon": 18,
        "Proprietaire de ranch": 22,
        "Cowboy": 7,
        "Journalier": 4,
        "Journaliere": 3,
        "Oisif": 0,
        "Oisive": 0,
        "Chomeur": 0,
        "Chomeuse": 0,
    }
    return incomes.get(job, 0)


def random_health_state():
    if random.randint(1, 100) <= 92:
        return "en forme"
    return random.choice(HEALTH_STATES)


def clamp_stat(value, maximum):
    return max(5, min(maximum, value))


try:
    import questionary
except ImportError:
    questionary = None


@dataclass
class Character:
    first_name: str
    last_name: str
    name: str
    sex: str
    age: int
    origin: str
    strength: int
    sociability: int
    intelligence: int
    income: int
    money: int
    respect: int = 0
    celebrite: int = 0
    condition: str = "en forme"
    job: str | None = None
    employer_building_id: str | None = None
    residence: str | None = None
    monture: dict[str, object] | None = None
    skills: list[str] = field(default_factory=list)
    inventory: dict[str, int] = field(default_factory=dict)
    preferences: dict[str, dict[int, float]] = field(default_factory=dict)
    consumption_needs: dict[str, int] = field(default_factory=dict)
    mineral_claims: list[dict[str, object]] = field(default_factory=list)
    is_player: bool = True

    def to_dict(self):
        clean_character_inventory_from_animals(self.inventory)
        return asdict(self)


def ask_text(question):
    while True:
        if questionary:
            answer = questionary.text(question).ask()
            if answer is None:
                raise KeyboardInterrupt
        else:
            answer = input(question).strip()

        answer = answer.strip()
        if answer:
            return answer
        print("Réponse obligatoire.")


def ask_text_with_default(question, default_value):
    if questionary:
        answer = questionary.text(question, default=default_value).ask()
        if answer is None:
            raise KeyboardInterrupt

        answer = answer.strip()
        return answer or default_value

    answer = input(f"{question} [{default_value}] : ").strip()
    return answer or default_value


def ask_choice(question, choices):
    if not questionary:
        print(f"\n{question}")

        for index, choice in enumerate(choices, start=1):
            print(f"{index}. {choice['label']}")

        while True:
            answer = input("Ton choix : ").strip()

            if answer.isdigit():
                selected_index = int(answer) - 1
                if 0 <= selected_index < len(choices):
                    return choices[selected_index]

            print("Choix invalide. Entre le numéro correspondant.")

    labels = [choice["label"] for choice in choices]
    selected_label = questionary.select(question, choices=labels).ask()

    if selected_label is None:
        raise KeyboardInterrupt

    for choice in choices:
        if choice["label"] == selected_label:
            return choice

    raise ValueError(f"Choix inconnu : {selected_label}")


CHARACTER_QUESTIONS = [
    {
        "id": "origin",
        "question": "D'où venez-vous ?",
        "choices": [
            {
                "label": "Boston",
                "origin": "Boston",
                "set_stats": {"strength": 6, "sociability": 8, "intelligence": 8},
                "set_money": 200,
                "skills": [],
                "next": "skill_boston",
            },
            {
                "label": "Saint-Louis",
                "origin": "Saint-Louis",
                "set_stats": {"strength": 6, "sociability": 9, "intelligence": 7},
                "set_money": 45,
                "skills": ["Charisme"],
                "next": "skill_saint_louis",
            },
            {
                "label": "Abilene",
                "origin": "Abilene",
                "set_stats": {"strength": 9, "sociability": 6, "intelligence": 7},
                "set_money": 45,
                "skills": ["Élevage"],
                "next": "skill_abilene",
            },
            {
                "label": "Californie",
                "origin": "Californie",
                "set_stats": {"strength": 9, "sociability": 7, "intelligence": 6},
                "set_money": 45,
                "skills": ["Prospection"],
                "next": "skill_californie",
            },
        ],
    },
    {
        "id": "skill_boston",
        "question": "Quelle compétence avez-vous développée à Boston ?",
        "choices": [
            {"label": "J'ai appris à cerner les gens.", "stats": {"sociability": 1, "intelligence": 1}, "skills": ["Jugement"]},
            {"label": "J'ai fait des études.", "stats": {"intelligence": 2}, "skills": [], "next": "study_field"},
            {"label": "J'ai toujours su trouver les bons mots.", "stats": {"sociability": 2}, "skills": ["Charisme"]},
        ],
    },
    {
        "id": "study_field",
        "question": "Quelles études avez-vous faites ?",
        "choices": [
            {"label": "Médecine", "stats": {}, "skills": ["Médecine"]},
            {"label": "Ingénierie", "stats": {}, "skills": ["Ingénierie"]},
            {"label": "Finance", "stats": {}, "skills": ["Finance"]},
            {"label": "Journalisme", "stats": {}, "skills": ["Journalisme"]},
            {"label": "Droit", "stats": {}, "skills": ["Droit"]},
        ],
    },
    {
        "id": "skill_saint_louis",
        "question": "Quelle compétence avez-vous développée à Saint-Louis ?",
        "choices": [
            {"label": "J'ai commis quelques péchés.", "stats": {"strength": 2}, "skills": ["Criminalité"]},
            {"label": "J'ai appris à cerner les gens.", "stats": {"sociability": 1, "intelligence": 1}, "skills": ["Jugement"]},
            {"label": "J'ai écumé les tables de poker.", "stats": {"sociability": 1, "intelligence": 1}, "skills": ["Jeu"]},
        ],
    },
    {
        "id": "skill_abilene",
        "question": "Quelle compétence avez-vous développée à Abilene ?",
        "choices": [
            {"label": "J'ai commis quelques péchés.", "stats": {"strength": 2}, "skills": ["Criminalité"]},
            {"label": "J'ai vécu de la chasse.", "stats": {"strength": 2}, "skills": ["Chasse"]},
            {"label": "J'ai écumé les tables de poker.", "stats": {"sociability": 1, "intelligence": 1}, "skills": ["Jeu"]},
        ],
    },
    {
        "id": "skill_californie",
        "question": "Quelle compétence avez-vous développée en Californie ?",
        "choices": [
            {"label": "Je faisais sauter des trucs.", "stats": {"intelligence": 2}, "skills": ["Artificier"]},
            {"label": "J'ai travaillé dans un ranch.", "stats": {"strength": 2}, "skills": ["Élevage"]},
            {"label": "J'ai appris à cerner les gens.", "stats": {"sociability": 1, "intelligence": 1}, "skills": ["Jugement"]},
        ],
    },
]


def create_character():
    print("Bonjour...")
    title = ask_choice(
        "Comment dois-je vous appeler ?",
        [
            {"label": "Monsieur", "sex": "Homme"},
            {"label": "Madame", "sex": "Femme"},
        ],
    )
    sex = title["sex"]
    random_first_name = random.choice(MALE_FIRST_NAMES if sex == "Homme" else FEMALE_FIRST_NAMES)
    first_name = ask_text_with_default(f"Bonjour {title['label']} ?", random_first_name)

    random_last_name = random.choice(LAST_NAMES)
    last_name = ask_text_with_default(f"{first_name} comment ?", random_last_name)

    name = f"{first_name} {last_name}"
    answers = ask_character_questions()

    return Character(
        first_name=first_name,
        last_name=last_name,
        name=name,
        sex=sex,
        age=25,
        origin=answers["origin"],
        strength=answers["strength"],
        sociability=answers["sociability"],
        intelligence=answers["intelligence"],
        income=0,
        money=answers["money"],
        condition="en forme",
        skills=answers["skills"],
    )


def ask_character_questions():
    result = {
        "origin": None,
        "strength": 4,
        "sociability": 4,
        "intelligence": 4,
        "money": 45,
        "skills": [],
    }

    question_by_id = {
        question_data["id"]: question_data
        for question_data in CHARACTER_QUESTIONS
    }
    current_question_id = CHARACTER_QUESTIONS[0]["id"]
    answered_question_ids = set()

    while current_question_id:
        question_data = question_by_id[current_question_id]
        answered_question_ids.add(current_question_id)
        selected = ask_choice(question_data["question"], question_data["choices"])

        for stat_name, value in selected.get("set_stats", {}).items():
            result[stat_name] = value

        for stat_name, bonus in selected.get("stats", {}).items():
            result[stat_name] += bonus

        if "set_money" in selected:
            result["money"] = selected["set_money"]
        else:
            result["money"] += selected.get("money", 0)

        for skill in selected.get("skills", []):
            if skill not in result["skills"]:
                result["skills"].append(skill)

        if selected.get("origin"):
            result["origin"] = selected["origin"]

        current_question_id = next_question_id(
            current_question_id,
            selected,
            answered_question_ids,
        )

    if result["origin"] is None:
        result["origin"] = "Nouvel arrivant"

    return result


def next_question_id(current_question_id, selected_answer, answered_question_ids):
    if "next" in selected_answer:
        return selected_answer["next"]

    # Dans la création simplifiée, seule la question d'origine dirige vers
    # une question de compétence. Une question de compétence termine toujours.
    if current_question_id != CHARACTER_QUESTIONS[0]["id"]:
        return None

    question_ids = [question_data["id"] for question_data in CHARACTER_QUESTIONS]
    current_index = question_ids.index(current_question_id)

    for question_id in question_ids[current_index + 1:]:
        if question_id not in answered_question_ids:
            return question_id

    return None

