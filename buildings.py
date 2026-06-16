import random
from dataclasses import asdict, dataclass, field

from goods_services import service_default_price
from jobs import job_base_salary, job_definition, job_salary_coefficient


@dataclass
class Building:
    building_id: str
    name: str
    building_type: str
    owner: str
    level: int
    is_public: bool = False
    location: str = "Ville"
    visible: bool = True
    building_kind: str = "economique"
    features: dict[str, bool] = field(default_factory=dict)
    hidden_stats: dict[str, object] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    production: dict[str, object] = field(default_factory=dict)
    employees: list[str] = field(default_factory=list)
    employee_roles: dict[str, str] = field(default_factory=dict)
    employee_tasks: dict[str, str] = field(default_factory=dict)
    employee_contracts: dict[str, dict[str, object]] = field(default_factory=dict)
    upgrades: list[str] = field(default_factory=list)
    current_balance: float = 0
    current_result: float = 0
    balance_history: list[int] = field(default_factory=list)
    result_history: list[int] = field(default_factory=list)
    account_journal: list[str] = field(default_factory=list)
    under_construction: bool = False
    investment_value: float = 0
    lifetime_revenue: float = 0
    lifetime_expenses: float = 0
    annual_sales: float = 0
    annual_purchases: float = 0
    annual_wages: float = 0
    previous_annual_sales: float = 0
    previous_annual_purchases: float = 0
    previous_annual_wages: float = 0
    previous_annual_stock_value: float = 0
    previous_annual_result: float = 0
    fire_risk: float = 0.01
    accounting: dict[str, object] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def ensure_employee_contracts(building):
    """Synchronise les employés d'un bâtiment avec leurs contrats."""
    contracts = getattr(building, "employee_contracts", None)
    if contracts is None:
        building.employee_contracts = {}
        contracts = building.employee_contracts

    ordered_ids = list(dict.fromkeys(list(building.employees) + list(contracts.keys())))
    for employee_id in ordered_ids:
        contract = contracts.setdefault(employee_id, {})
        role = contract.get("role") or building.employee_roles.get(employee_id, "Employé")
        contract["role"] = role
        contract["wage"] = contract.get("wage", employee_salary(role))
        if employee_id in building.employee_tasks and "task" not in contract:
            contract["task"] = building.employee_tasks[employee_id]
        if employee_id not in building.employees:
            building.employees.append(employee_id)
        building.employee_roles[employee_id] = role
        if "task" in contract:
            building.employee_tasks[employee_id] = contract["task"]
    return contracts


def employee_ids(building):
    return list(ensure_employee_contracts(building).keys())


def employee_contract_for(building, employee_id):
    return ensure_employee_contracts(building).get(employee_id, {})


def employee_role(building, employee_id, default="Employé"):
    return employee_contract_for(building, employee_id).get("role", default)


def employee_wage(building, employee_id):
    contract = employee_contract_for(building, employee_id)
    return contract.get("wage", employee_salary(contract.get("role", "Employé")))


def employee_task(building, employee_id, default=None):
    return employee_contract_for(building, employee_id).get("task", default)


def set_employee_contract(building, employee_id, role, wage=None, task=None):
    ensure_employee_contracts(building)
    contract = {"role": role, "wage": employee_salary(role) if wage is None else wage}
    if task:
        contract["task"] = task
    building.employee_contracts[employee_id] = contract
    if employee_id not in building.employees:
        building.employees.append(employee_id)
    building.employee_roles[employee_id] = role
    if task:
        building.employee_tasks[employee_id] = task
    else:
        building.employee_tasks.pop(employee_id, None)


def remove_employee_contract(building, employee_id):
    ensure_employee_contracts(building)
    if employee_id in building.employees:
        building.employees.remove(employee_id)
    building.employee_roles.pop(employee_id, None)
    building.employee_tasks.pop(employee_id, None)
    building.employee_contracts.pop(employee_id, None)


def employee_salary(role):
    return job_base_salary(role)


def local_base_wage(city):
    """Salaire median local utilise comme base de recrutement."""
    return getattr(city, "base_wage", 7)


def default_role_wage(city, building, role):
    """Salaire propose si le joueur ne modifie pas le champ."""
    return round(local_base_wage(city) * job_salary_coefficient(role), 2)


def role_count(building, role):
    return len([
        employee_id for employee_id in employee_ids(building)
        if employee_role(building, employee_id) == role
    ])


def role_limit(building, role):
    """Limites communes de postes, basees sur les ameliorations du batiment."""
    upgrades = normalize_upgrades(getattr(building, "upgrades", []))
    normalized_upgrades = [normalize_text(upgrade) for upgrade in upgrades]
    building_type = normalize_text(building.building_type)
    if building_type == "saloon":
        limits = {"Barman": 1, "Cuisinier": 1 if "cuisine" in normalized_upgrades else 0, "Hotesse": room_count(building)}
        return limits.get(role, 0)
    if building_type == "ranch" and role == "Cowboy":
        return 1 + upgrades.count("Baraquements") * 2
    if building_type == "cabinet medical":
        return 1 if role == "Infirmière" and medical_bed_count(building) > 0 else 0
    if building_type == "general store":
        return 1 if role == "Commis" and "reserve" in normalized_upgrades else 0
    if building_type == "mine":
        if role == "Mineur":
            return 9999
        if role == "Garde":
            return 4 if "corps de garde" in normalized_upgrades else 0
        if role == "Ingénieur":
            return 1 if "bureau de l'ingenieur" in normalized_upgrades else 0
    return 0


def can_recruit_role(building, role):
    return role_count(building, role) < role_limit(building, role)


def recruitable_roles(building):
    """Liste les postes actuellement ouverts par le batiment."""
    provider = getattr(building, "recruitable_jobs", None)
    if provider:
        try:
            roles = provider(None)
        except TypeError:
            roles = provider()
        return [role for role in roles if role_limit(building, role) > 0]
    return []


def available_workers(population):
    available_jobs = {"Journalier", "Journaliere", "Chomeur", "Chomeuse", "Chômeur", "Chômeuse", "Oisif", "Oisive"}
    return [
        npc for npc in population
        if getattr(npc, "employer_building_id", None) is None and getattr(npc, "job", None) in available_jobs
    ]


def eligible_candidates_for_role(population, role, player_has_judgement=False):
    candidates = [
        npc for npc in available_workers(population)
        if can_npc_take_role(npc, role, population)
    ]
    if player_has_judgement:
        candidates.sort(key=lambda npc: job_skill_score(npc, role), reverse=True)
    else:
        random.shuffle(candidates)
    return candidates


def can_npc_take_role(npc, role, population=None):
    definition = job_definition(role)
    if spouse_is_important(npc, population) and role != "Infirmière":
        return False
    required_sex = definition.get("sex")
    if required_sex and getattr(npc, "sex", None) != required_sex:
        return False
    if definition.get("unmarried_only") and getattr(npc, "spouse_id", None):
        return False
    if getattr(npc, "sex", None) == "Femme" and getattr(npc, "spouse_id", None) and getattr(npc, "job", None) == "Oisive" and role != "Cuisinier":
        return False
    if getattr(npc, "strength", 0) < definition.get("min_strength", 0):
        return False
    required_skill = definition.get("skill")
    if required_skill and not has_skill(npc, required_skill):
        return False
    return True


def can_player_take_role(character, role):
    definition = job_definition(role)
    required_sex = definition.get("sex")
    if required_sex and getattr(character, "sex", None) != required_sex:
        return False
    if getattr(character, "strength", 0) < definition.get("min_strength", 0):
        return False
    required_skill = definition.get("skill")
    if required_skill and not has_skill(character, required_skill):
        return False
    return True


def job_skill_score(character, role):
    stat = job_definition(role).get("main_stat")
    if stat == "physique":
        return getattr(character, "strength", 0)
    if stat == "social":
        return getattr(character, "sociability", 0)
    if stat == "intelligence":
        return getattr(character, "intelligence", 0)
    return max(getattr(character, "strength", 0), getattr(character, "sociability", 0), getattr(character, "intelligence", 0))


def spouse_is_important(npc, population):
    if not population or not getattr(npc, "spouse_id", None):
        return False
    spouse = next((person for person in population if person.npc_id == npc.spouse_id), None)
    return bool(spouse and is_important_person(spouse))


def is_important_person(npc):
    important_jobs = ["Sherif", "Proprietaire", "Propriétaire", "Maire", "Juge", "Conseiller", "Politique"]
    return any(job_part in getattr(npc, "job", "") for job_part in important_jobs)


def has_skill(character, skill_name):
    normalized = normalize_text(skill_name)
    return any(normalize_text(skill) == normalized for skill in getattr(character, "skills", []))


def room_count(building):
    return normalize_upgrades(getattr(building, "upgrades", [])).count("Chambre")


def medical_bed_count(building):
    return min(10, normalize_upgrades(getattr(building, "upgrades", [])).count("Salle de convalescence") * 2)


def normalize_upgrades(upgrades):
    return ["Chambre" if upgrade == "Chambres d'hotel" else upgrade for upgrade in upgrades]


def normalize_text(value):
    return (
        str(value or "")
        .lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("Ã©", "e")
        .replace("Ã¨", "e")
        .replace("Ãª", "e")
        .replace("Ã ", "a")
    )



BUILDING_CATALOG = {
    "Ranch": {
        "base_cost": 90,
        "description": "Permet d'élever du bétail et de cultiver des céréales. Génère des revenus grâce à la vente de produits agricoles et de bétail. Plus le ranch est grand et bien entretenu, plus il peut produire et générer de revenus.",
        "features": {},
        "upgrades": ["Baraquements"],
        "inventory": {"fourrage": 0},
        "production": {
            "head_count": 0,
            "workload": 0,
            "bulls": [],
        },
        "hidden_stats": {},
    },
    "Saloon": {
        "base_cost": 80,
        "description": "Principal lieu de débauche et de rencontre d'une ville. Génère de l'argent grâce à la vente de boissons, de nourriture et d'autres services et vices. Plus le saloon est attrayant, plus il attire de clients et génère de revenus.",
        "features": {"table_poker": False, "piano": False},
        "inventory": {"fut_biere": 0, "vivres_secs": 0},
        "production": {
            "commande_biere": 0,
            "prix_biere": service_default_price("biere"),
            "commande_vivres_secs": 0,
            "prix_repas": service_default_price("repas"),
            "prix_hotesse": service_default_price("hotesse"),
            "prix_bain": service_default_price("bain"),
            "prix_chambre": service_default_price("chambre"),
        },
        "hidden_stats": {
            "attrait_clients": 6,
            "ambiance": 5,
            "reputation_biere": 5,
            "qualite_service": 5,
            "sensibilite_prix": 5,
        },
    },
    "Cabinet médical": {
        "base_cost": 100,
        "description": "Permet de soigner les habitants contre paiement. Un médecin compétent peut y stocker des remèdes, accueillir des patients en convalescence et préparer ses propres traitements avec un laboratoire.",
        "features": {},
        "inventory": {"plantes_medicinales": 0, "remede": 0},
        "production": {
            "commande_remede": 0,
            "tarif_blessure": service_default_price("soin_blessure"),
            "tarif_blessure_grave": service_default_price("soin_blessure_grave"),
            "tarif_maladie": service_default_price("soin_maladie"),
            "tarif_convalescence": 4,
            "patients": [],
        },
        "hidden_stats": {},
        "upgrades": [],
    },
    "General Store": {
        "base_cost": 140,
        "description": "Commerce général permettant de vendre des biens importés ou locaux.",
        "features": {},
        "inventory": {},
        "production": {
            "storage_capacity": 400,
            "sale_prices": {},
            "listed_goods": [],
        },
        "hidden_stats": {},
        "upgrades": [],
    },
    "Barber shop": {
        "base_cost": 60,
        "description": "Boutique de barbier proposant coupes et petits services de soin courant.",
        "features": {},
        "inventory": {},
        "production": {},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Mine": {
        "base_cost": 120,
        "description": "Exploite un filon revendiqué après prospection.",
        "features": {},
        "inventory": {},
        "production": {
            "workload": 0,
            "extracted": {},
            "work_hours": 8,
            "timbering_m": 8,
            "security": 50,
            "discontent": 0,
            "mine_store_prices": {
                "vivres_secs": 1,
                "tabac": 1,
                "cafe": 1,
            },
        },
        "hidden_stats": {},
        "upgrades": [],
    },
    "Ferme": {
        "base_cost": 75,
        "description": "Exploitation agricole. Modalites de production a definir.",
        "features": {},
        "inventory": {"vivres_secs": 0},
        "production": {"surface_cultivee": 0, "stock_production": {}},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Camp de bucheron": {
        "base_cost": 70,
        "description": "Exploitation forestiere. Modalites de production a definir.",
        "features": {},
        "inventory": {"bois": 0},
        "production": {"zone_de_coupe": 0, "stock_production": {}},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Banque": {
        "base_cost": 250,
        "description": "Etablissement financier. Depots et prets a definir.",
        "features": {},
        "inventory": {},
        "production": {"depots": 0, "prets": []},
        "hidden_stats": {"securite_coffre": 0},
        "upgrades": [],
    },
    "Tailleur": {
        "base_cost": 65,
        "description": "Atelier textile. Fabrication et vente a definir.",
        "features": {},
        "inventory": {"tissu": 0, "laine": 0, "coton": 0, "soie": 0},
        "production": {"prix_habits": {}},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Mar\u00e9chal ferrant": {
        "base_cost": 70,
        "description": "Atelier lie aux chevaux et au ferrage. Modalites a definir.",
        "features": {},
        "inventory": {"outils": 0, "fer": 0},
        "production": {
            "prix_ferrage": service_default_price("ferrage"),
            "prix_soins_equestres": service_default_price("soins_equestres"),
        },
        "hidden_stats": {},
        "upgrades": [],
    },
    "Charpentier": {
        "base_cost": 75,
        "description": "Atelier de bois et construction. Modalites a definir.",
        "features": {},
        "inventory": {"bois": 0, "planche": 0, "outils": 0},
        "production": {"commandes": []},
        "hidden_stats": {},
        "upgrades": [],
    },
    "H\u00f4tel": {
        "base_cost": 120,
        "description": "Logement commercial. Chambres et services a definir.",
        "features": {},
        "inventory": {"vivres_secs": 0},
        "production": {"prix_chambre": service_default_price("chambre"), "housing_mode": "location"},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Restaurant": {
        "base_cost": 85,
        "description": "Service de repas. Cuisine, stock et prix a definir.",
        "features": {},
        "inventory": {"vivres_secs": 0, "vivres_frais": 0},
        "production": {"prix_repas": service_default_price("repas")},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Comptoir de trappeur": {
        "base_cost": 70,
        "description": "Commerce de fourrures et produits de chasse. Modalites a definir.",
        "features": {},
        "inventory": {"fourrure": 0, "cuir": 0},
        "production": {"prix_achat": {}, "prix_vente": {}},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Journal": {
        "base_cost": 90,
        "description": "Presse locale. Tirage, influence et annonces a definir.",
        "features": {},
        "inventory": {"papier": 0},
        "production": {"tirage": 0, "prix_journal": 0},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Bureau": {
        "base_cost": 60,
        "description": "Bureau prive pour activites administratives ou professionnelles. Modalites a definir.",
        "features": {},
        "inventory": {},
        "production": {"contrats": []},
        "hidden_stats": {},
        "upgrades": [],
    },
    "Fort": {
        "base_cost": 0,
        "description": "Batiment public militaire. Modalites a definir.",
        "constructible": False,
        "features": {},
        "inventory": {},
        "production": {"garnison": 0},
        "hidden_stats": {"securite": 0},
        "upgrades": [],
    },
    "County hall": {
        "base_cost": 0,
        "description": "Batiment public administratif. Modalites a definir.",
        "constructible": False,
        "features": {},
        "inventory": {},
        "production": {"taxes": 0, "decisions": []},
        "hidden_stats": {},
        "upgrades": [],
    },
    "\u00c9cole": {
        "base_cost": 0,
        "description": "Batiment public d'enseignement. Modalites a definir.",
        "constructible": False,
        "features": {},
        "inventory": {"livre": 0, "papier": 0},
        "production": {"eleves": []},
        "hidden_stats": {},
        "upgrades": [],
    },

}


def create_starter_buildings(player_name, population=None, player_starting_activity=None):
    from building_types.barber_shop import BarberShop
    from building_types.church import Church
    from building_types.general_store import GeneralStore
    from building_types.post_office import PostOffice
    from building_types.sheriff_office import SheriffOffice

    ranch_1_owner = npc_name(population, "npc_ranch_001_owner", "Elias McCoy")
    ranch_2_owner = npc_name(population, "npc_ranch_002_owner", "Harlan Dawson")
    saloon_owner = npc_name(population, "npc_saloon_owner_001", "Silas Reed")
    general_store_owner = npc_name(population, "npc_general_store_owner_001", "Silas Reed")
    barber_owner = npc_name(population, "npc_barber_surgeon_001", "Edgar Bell")

    buildings = [
        create_starter_ranch("ranch_001", ranch_1_owner, ["npc_ranch_001_cowboy_001", "npc_ranch_001_cowboy_002"]),
        create_starter_ranch("ranch_002", ranch_2_owner, ["npc_ranch_002_cowboy_001", "npc_ranch_002_cowboy_002"]),
        create_starter_saloon(player_name if player_starting_activity == "saloon" else saloon_owner),
        GeneralStore(
            building_id="general_store_001",
            name="General Store",
            owner=general_store_owner,
            inventory=random_general_store_weapon_stock(),
            current_balance=100,
        ),
        SheriffOffice(),
        PostOffice(),
        Church(),
        BarberShop(
            building_id="barber_surgeon_001",
            owner=barber_owner,
            current_balance=50,
        ),
        *player_starting_buildings(player_name, player_starting_activity),
    ]
    return [apply_building_common_defaults(building) for building in buildings]


def player_starting_buildings(player_name, player_starting_activity):
    if player_starting_activity == "ranch":
        return [create_player_ranch(player_name)]
    return []


def create_starter_saloon(owner):
    from building_types.saloon import Saloon

    return Saloon(
        building_id="saloon_001",
        name=f"Saloon {last_name_from_name(owner)}",
        owner=owner,
        features={"table_poker": True, "piano": False},
        upgrades=[],
        current_balance=80,
    )


def create_player_ranch(player_name):
    from building_types.ranch import Ranch

    return Ranch(
        building_id="ranch_player_001",
        name=f"Ranch {last_name_from_name(player_name)}",
        owner=player_name,
        head_count=20,
        bulls=[{
            "nom": random_spanish_bull_name(),
            "age": random.randint(1, 6),
            "fécondité": random_bull_fertility(),
        }],
        upgrades=[],
        current_balance=90,
    )


def create_starter_ranch(building_id, owner, cowboy_ids):
    from building_types.ranch import Ranch

    upgrades = random.sample(
        ["Baraquements", "Citerne", "Grange"],
        random.randint(1, 2),
    )
    return Ranch(
        building_id=building_id,
        name=f"Ranch {last_name_from_name(owner)}",
        owner=owner,
        head_count=random.randint(40, 60),
        bulls=[{
            "nom": random_spanish_bull_name(),
            "age": random.randint(1, 6),
            "fécondité": random_bull_fertility(),
        }],
        employees=cowboy_ids[:],
        upgrades=upgrades,
        current_balance=30,
    )


def employee_contract(role, wage, task=None):
    contract = {"role": role, "wage": wage}
    if task:
        contract["task"] = task
    return contract


def npc_name(population, npc_id, fallback):
    if population:
        for npc in population:
            if npc.npc_id == npc_id:
                return npc.name
    return fallback


def last_name_from_name(name):
    return name.split()[-1] if name else "Inconnu"


SPANISH_BULL_SYLLABLES = [
    "al",
    "bar",
    "cor",
    "del",
    "dor",
    "fer",
    "gar",
    "jos",
    "lor",
    "man",
    "mar",
    "nar",
    "ped",
    "ram",
    "ros",
    "san",
    "sol",
    "tor",
    "val",
    "zar",
]


def random_spanish_bull_name():
    first = random.choice(SPANISH_BULL_SYLLABLES)
    second = random.choice(SPANISH_BULL_SYLLABLES)
    while second == first:
        second = random.choice(SPANISH_BULL_SYLLABLES)
    return f"{first}{second}".capitalize()


def random_general_store_weapon_stock():
    return {
        "colt_navy": random.randint(2, 4),
        "carabine_spencer": random.randint(1, 2),
        "fusil_springfield": random.randint(5, 7),
    }


def random_bull_fertility():
    return random.choice([4, 8, 12, 16])


def create_building_for_construction(building_type, building_id, name, owner, hidden_stats=None, under_construction=True):
    """Cree le bon objet de batiment pour une nouvelle construction."""
    configured_types = {
        "Ferme",
        "Camp de bucheron",
        "Banque",
        "Tailleur",
        "Maréchal ferrant",
        "MarÃ©chal ferrant",
        "Charpentier",
        "Hôtel",
        "HÃ´tel",
        "Restaurant",
        "Comptoir de trappeur",
        "Journal",
        "Bureau",
        "Fort",
        "County hall",
        "École",
        "Ã‰cole",
    }
    if building_type == "Ranch":
        from building_types.ranch import Ranch

        building = Ranch(building_id=building_id, name=name, owner=owner, under_construction=under_construction)
    elif building_type in configured_types:
        from building_types import building_class_for

        building_class = building_class_for(building_type)
        if not building_class:
            raise KeyError(building_type)
        building = building_class(
            building_id=building_id,
            name=name,
            owner=owner,
            under_construction=under_construction,
        )
    elif building_type == "Saloon":
        from building_types.saloon import Saloon

        building = Saloon(building_id=building_id, name=name, owner=owner, under_construction=under_construction)
    elif building_type == "General Store":
        from building_types.general_store import GeneralStore

        building = GeneralStore(building_id=building_id, name=name, owner=owner, under_construction=under_construction)
    elif building_type == "Cabinet médical":
        from building_types.medical_office import MedicalOffice

        building = MedicalOffice(building_id=building_id, name=name, owner=owner, under_construction=under_construction)
    elif building_type == "Barber shop":
        from building_types.barber_shop import BarberShop

        building = BarberShop(building_id=building_id, owner=owner, under_construction=under_construction)
        building.name = name
    elif building_type == "Mine":
        from building_types.mine import Mine

        building = Mine(building_id=building_id, name=name, owner=owner, deposit=(hidden_stats or {}).get("deposit"), under_construction=under_construction)
    elif building_type == "Bureau du sherif":
        from building_types.sheriff_office import SheriffOffice

        building = SheriffOffice(building_id=building_id, owner=owner)
        building.name = name
        building.under_construction = under_construction
    elif building_type == "Post Office":
        from building_types.post_office import PostOffice

        building = PostOffice(building_id=building_id, owner=owner)
        building.name = name
        building.under_construction = under_construction
    elif building_type in ["Église", "Ã‰glise"]:
        from building_types.church import Church

        building = Church(building_id=building_id, owner=owner)
        building.name = name
        building.under_construction = under_construction
    else:
        data = BUILDING_CATALOG[building_type]
        building = Building(
            building_id=building_id,
            name=name,
            building_type=building_type,
            owner=owner,
            level=1,
            features=data.get("features", {}).copy(),
            hidden_stats=(hidden_stats or data.get("hidden_stats", {})).copy(),
            inventory=data.get("inventory", {}).copy(),
            production=data.get("production", {}).copy(),
            upgrades=data.get("upgrades", []).copy(),
            under_construction=under_construction,
        )
    building.hidden_stats.update(hidden_stats or {})
    building.investment_value = BUILDING_CATALOG.get(building_type, {}).get("base_cost", 0)
    building.account_journal = [f"Construction : {name}"]
    return apply_building_common_defaults(building)


def apply_building_common_defaults(building):
    """Ajoute les parametres communs manquants sur les anciens et nouveaux batiments."""
    public_types = {"Bureau du sherif", "Post Office", "Église", "Eglise", "Fort", "County hall", "École", "Ecole"}
    countryside_types = {"Ranch", "Mine", "Ferme", "Camp de bucheron"}
    housing_provider_types = {"Cabane", "Maison de ville", "Maison bourgeoise", "Pension", "Immeuble", "Poorhouse"}

    building.location = "Campagne" if building.building_type in countryside_types else getattr(building, "location", "Ville")
    building.visible = getattr(building, "visible", True)
    if building.building_type in public_types or getattr(building, "is_public", False):
        building.building_kind = "public"
        building.is_public = True
        if not building.owner:
            building.owner = "Ville"
    elif building.building_type in housing_provider_types:
        building.building_kind = "batiment_logement"
    else:
        building.building_kind = getattr(building, "building_kind", "economique")
    if getattr(building, "fire_risk", None) in [None, 0]:
        building.fire_risk = 0.01
    return building


def specialize_building(building):
    """Recree un batiment charge en sauvegarde avec sa classe specialisee."""
    try:
        specialized = create_building_for_construction(
            building.building_type,
            building.building_id,
            building.name,
            building.owner,
            hidden_stats=building.hidden_stats,
            under_construction=building.under_construction,
        )
    except (KeyError, TypeError):
        return apply_building_common_defaults(building)
    specialized.__dict__.update(building.__dict__)
    return apply_building_common_defaults(specialized)


def normalize_ranch_data(building):
    """Convertit les anciens ranchs vers le format simple actuel."""
    if building.building_type != "Ranch":
        return building

    production = building.production or {}
    bulls = production.get("bulls", [])
    if not isinstance(bulls, list):
        bulls = []

    if "head_count" not in production:
        production["head_count"] = (
            production.get("genisses", 0)
            + production.get("veaux", 0)
            + production.get("vaches_matures", production.get("betes_matures", 0))
        )

    production["workload"] = production.get("workload", 0)
    production["bulls"] = [normalize_bull(bull) for bull in bulls]

    for old_key in [
        "acres",
        "taureaux",
        "genisses",
        "veaux",
        "vaches_matures",
        "betes_matures",
        "achat_taureaux",
        "achat_genisses",
        "achat_fourrage",
        "commande_cereales",
        "vente_taureaux",
        "vente_genisses",
        "vente_veaux",
        "vente_vaches_matures",
    ]:
        production.pop(old_key, None)

    building.production = production
    building.inventory.pop("cereales", None)
    building.hidden_stats = {}
    allowed_ranch_upgrades = {
        "Baraquements",
        "Citerne",
        "Grange",
        "Manège et écurie",
        "Culture et potager",
        "Élevage domestique",
    }
    building.upgrades = [
        "Baraquements" if upgrade == "Logements employes" else upgrade
        for upgrade in building.upgrades
        if upgrade in allowed_ranch_upgrades or upgrade == "Logements employes"
    ]
    return building


def normalize_bull(bull):
    return {
        "nom": bull.get("nom") or bull.get("name") or random_spanish_bull_name(),
        "age": bull.get("age", random.randint(1, 6)),
        "fécondité": bull.get("fécondité", bull.get("fertility", random_bull_fertility())),
    }
