from dataclasses import dataclass
from system.game_values import *
from ranch import *
from characters import *
#touts les élements communs aux bâtiments ainsi que la classe Building.

### PARTIE CREATION ###

#liste les types de bâtiments disponibles pour affichage

#config de la classe Building_type
@dataclass(slots=True)
class Building_type:
    def __init__(self, **kwargs):
        self.price: callable = kwargs.get ('price', 0)
        self.conditions: callable = kwargs.get ('conditions', True)
        base_actions = [
             {'name': 'Gestion', 'methode': None},
             {'name': 'Retour', 'methode': None}
        ]
        additional_actions = [kwargs.get('action', [])]
        self.actions: list = additional_actions + base_actions
        self.management_views: list = []
        self.exploitation = kwargs.get('exploitation', None) #enregistre la méthode d'exploitation

#config de la classe Building
@dataclass(slots=True)
class Building:
    _id_counter = 0
    def __init__(self, type_, owner, **kwargs):
        Building._id_counter += 1
        # building information
        self.type: str = f"{type_}" #saloon, ranch, hotel, etc.
        self.id_: str = f"b{type_[0].lower()}{Building._id_counter:06d}" #b + première lettre du type + numéro d'ordre (ex: bs000001 pour le premier saloon)
        self.family: str = self.building_type('family') #economic, public, housing
        self.name: str = kwargs.get("name", "Saloon") #nom du bâtiment par défaut type + nom du propriétaire (ex: Saloon Conway)
        self.owner: str = owner #id du propriétaire (ex: ch00001)
        self.date: str = f"{SEASON[0]},{DATE}" #enregistre la saison et l'année (exemple : "p1870" avec p pour printemps, e pour été, a pour automne et h pour hiver)
        # economic values
        self.production: dict = kwargs.get("production", {}) #variable de production du bâtiment (ex: prix de vente des services ou données du cattle drive)
        self.stock_capacity: int = kwargs.get("stock_capacity", 0) #taille de l'inventaire
        self.stock: dict =kwargs.get("stock", {}) #liste des bien à mettre avec une méthode si beaucoup de types différents (ex: [{"vivres_sec" : 0}, {"fut_biere" : 0}])
        self.housing: list = kwargs.get("housing", []) #liste des logements produits par le bâtiment (ex: ranch de base une maison de campagne et une chambre)
        self.employees: list = kwargs.get("employees", []) #liste des employés du bâtiment (id du personnage, salaire, poste)
        self.jobs: dict = kwargs.get("jobs", {"barman" : 1}) #liste des emplois disponibles dans le bâtiment (ex: {'mineur' : 999, 'garde' : 4} etc.)
        self.upgrades: list = kwargs.get("upgrades", []) #liste des améliorations réalisées sur le bâtiment (ex: "piano")
        self.upgrades_available: list = kwargs.get("upgrades_availabe", []) #liste des améliorations disponibles pour l'affichage
        # accountability values
        self.money: float = kwargs.get("money", 0) #argent disponible dans le bâtiment
        self.loan: list = kwargs.get("loan", []) #liste des prêts en cours (ex: {'amount' : 1000, 'interest_rate' : 0.05, 'due_date' : "p1870", 'due to' : "bank id"})
        self.accounting: dict = kwargs.get("accounting", {}) #bilan + résultat en cours
        self.saved_accounting: list = kwargs.get("saved_accounting", []) #liste des bilans et compte de résultat sauvegardés (ex: bilan de fin d'année) {'name' : "bilan 1870", 'terrain' : 100, 'construction' : 300, etc.}
        # building statues values
        self.under_construction: bool = kwargs.get("under_construction", True) #indique si le bâtiment est en construction ou pas (True/False)
        self.fire_risk: float = kwargs.get("fire_risk", 0.01) #pourcentage de chance
        self.location: int = kwargs.get("location", 0) #campagne = 1 ou ville = 0
        self.visible: bool = kwargs.get("visible", True) #indique si le bâtiment est visible sur l'interface ou pas (True/False)

    #récupérer les infos par défaut du batiment pour initialiser la classe
    def building_type(self, attribut):
            return self.type[attribut]
    
### PARTIE METHODES COMMUNES ###

#recruter un employé
def recruit_employees(building_id,character_id,wage,job):
    b = Building[building_id]
    c = Character[character_id]
    contract = [character_id,wage,job]
    b.employees.append(contract)
    b.jobs[job] -= 1
    c.job = f"{job}"
    c.income = wage
    return

#virer un employé

#modifier le salaire d'un employé

 