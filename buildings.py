from dataclasses import asdict, dataclass, field


@dataclass
class Building:
    building_id: str
    name: str
    building_type: str
    owner: str
    level: int
    is_public: bool = False
    features: dict[str, bool] = field(default_factory=dict)
    hidden_stats: dict[str, int] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    production: dict[str, int] = field(default_factory=dict)
    employees: list[str] = field(default_factory=list)
    employee_roles: dict[str, str] = field(default_factory=dict)
    employee_tasks: dict[str, str] = field(default_factory=dict)
    upgrades: list[str] = field(default_factory=list)
    current_balance: int = 0
    current_result: int = 0
    balance_history: list[int] = field(default_factory=list)
    result_history: list[int] = field(default_factory=list)
    account_journal: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


BUILDING_CATALOG = {
    "Ranch": {
        "base_cost": 90,
        "description": "Permet d'élever du bétail et de cultiver des céréales. Génère des revenus grâce à la vente de produits agricoles et de bétail. Plus le ranch est grand et bien entretenu, plus il peut produire et générer de revenus.",
        "features": {},
        "upgrades": ["Baraquements"],
        "inventory": {"cereales": 0, "fourrage": 0},
        "production": {
            "acres": 160,
            "taureaux": 0,
            "genisses": 0,
            "veaux": 0,
            "vaches_matures": 0,
            "achat_taureaux": 0,
            "achat_genisses": 0,
            "achat_fourrage": 0,
            "vente_taureaux": 0,
            "vente_genisses": 0,
            "vente_veaux": 0,
            "vente_vaches_matures": 0,
        },
        "hidden_stats": {
            "fertilite": 6,
            "qualite_betail": 5,
            "securite_troupeau": 5,
            "cloture": "aucune cloture",
            "taux_enclosion": "aucune cloture",
            "qualite_terre": "semi-aride",
        },
    },
    "Saloon": {
        "base_cost": 80,
        "description": "Principal lieu de débauche et de rencontre d'une ville. Génère de l'argent grâce à la vente de boissons, de nourriture et d'autres services et vices. Plus le saloon est attrayant, plus il attire de clients et génère de revenus.",
        "features": {"table_poker": False, "piano": False},
        "inventory": {"biere": 0, "cereales": 0, "viande": 0},
        "production": {
            "commande_biere": 0,
            "prix_biere": 2,
            "commande_cereales": 0,
            "commande_viande": 0,
            "prix_repas": 5,
            "prix_hotesse": 10,
            "prix_bain": 3,
        },
        "hidden_stats": {"attrait_clients": 6, "ambiance": 5},
    },
}


def create_starter_buildings(player_name):
    return [
        Building(
            building_id="ranch_001",
            name="Ranch McCoy",
            building_type="Ranch",
            owner="Elias McCoy",
            level=1,
            inventory={"cereales": 10, "fourrage": 0},
            production={
                "acres": 160,
                "taureaux": 1,
                "genisses": 2,
                "veaux": 0,
                "vaches_matures": 1,
                "achat_taureaux": 0,
                "achat_genisses": 0,
                "achat_fourrage": 0,
                "vente_taureaux": 0,
                "vente_genisses": 0,
                "vente_veaux": 0,
                "vente_vaches_matures": 0,
            },
            features={},
            hidden_stats={
                "fertilite": 6,
                "qualite_betail": 5,
                "securite_troupeau": 5,
                "cloture": "aucune cloture",
                "taux_enclosion": "aucune cloture",
                "qualite_terre": "semi-aride",
            },
            employees=["npc_ranch_foreman_001", "npc_ranch_cowboy_001", "npc_ranch_cowboy_002"],
            employee_roles={
                "npc_ranch_foreman_001": "Contremaitre",
                "npc_ranch_cowboy_001": "Cowboy",
                "npc_ranch_cowboy_002": "Cowboy",
            },
            employee_tasks={
                "npc_ranch_cowboy_001": "Garder le troupeau",
                "npc_ranch_cowboy_002": "Garder le troupeau",
            },
            upgrades=["Baraquements"],
            current_balance=30,
        ),
        Building(
            building_id="general_store_001",
            name="General Store",
            building_type="General Store",
            owner="Silas Reed",
            level=1,
            inventory={},
            current_balance=100,
        ),
        Building(
            building_id="sheriff_office_001",
            name="Bureau du sherif",
            building_type="Bureau du sherif",
            owner="Ville",
            level=1,
            is_public=True,
            employees=["npc_deputy_001"],
            current_balance=60,
        ),
        Building(
            building_id="post_office_001",
            name="Post Office",
            building_type="Post Office",
            owner="Ville",
            level=1,
            is_public=True,
            employees=["npc_post_worker_001"],
            current_balance=40,
        ),
    ]
