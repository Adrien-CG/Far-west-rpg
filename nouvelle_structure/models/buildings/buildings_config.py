from nouvelle_structure.system.game_values import *
from ranch import *
#touts les élements communs aux bâtiments ainsi que la classe Building.

#liste les types de bâtiments disponibles pour affichage
#name = nom affiché, build price et conditions renvoie les methodes qui sont dans la fiche batiment.
BUILDING_TYPES = [
    {"name" : "Ranch", "build" : ranch_build, "price" : ranch_price, "conditions" : ranch_conditions}
]

#config de la classe Building
class Building:
    _id_counter = 0
    def __init__(self, type, owner, **kwargs):
        Building._id_counter += 1
        # building information
        self.type = type #saloon, ranch, hotel, etc.
        self.id = f"{type[0].lower()}{Building._id_counter:06d}" #première lettre du type + numéro d'ordre (ex: s001 pour le premier saloon)
        self.family = self.building_type('family') #economic, public, housing
        self.name = kwargs.get("name", "Saloon") #nom du bâtiment par défaut type + nom du propriétaire (ex: Saloon Conway)
        self.owner = owner #id du propriétaire (ex: c00001)
        self.date = f"{SEASON[0]},{DATE}" #enregistre la saison et l'année (exemple : "p1870" avec p pour printemps, e pour été, a pour automne et h pour hiver)
        # economic values
        self.production = kwargs.get("production", [{}]) #variable de production du bâtiment (ex: prix de vente des services ou données du cattle drive)
        self.stock = kwargs.get("stock", [{"vivres_sec" : 0}, {"fut_biere" : 0}]) #liste des bien à mettre avec une méthode si beaucoup de types différents (ex: [{"vivres_sec" : 0}, {"fut_biere" : 0}])
        self.housing = kwargs.get("housing", [{}]) #liste des logements produits par le bâtiment (ex: ranch de base une maison de campagne et une chambre)
        self.employees = kwargs.get("employees", [{}]) #liste des employés du bâtiment (id du personnage, salaire, poste)
        self.jobs = kwargs.get("jobs", [{"barman" : 1}]) #liste des emplois disponibles dans le bâtiment (ex: {'mineur' : 999, 'garde' : 4} etc.)
        self.upgrades = kwargs.get("upgrades", [""]) #liste des améliorations réalisées sur le bâtiment (ex: "piano")
        # accountability values
        self.money = kwargs.get("money", 0) #argent disponible dans le bâtiment
        self.loan = kwargs.get("loan", [{}]) #liste des prêts en cours (ex: {'amount' : 1000, 'interest_rate' : 0.05, 'due_date' : "p1870", 'due to' : "bank id"})
        self.accounting = kwargs.get("accounting", [{},{}]) #bilan + résultat en cours
        self.saved_accounting = kwargs.get("saved_accounting", [{}]) #liste des bilans et compte de résultat sauvegardés (ex: bilan de fin d'année) {'name' : "bilan 1870", 'terrain' : 100, 'construction' : 300, etc.}
        # building statues values
        self.under_construction = kwargs.get("under_construction", True) #indique si le bâtiment est en construction ou pas (True/False)
        self.fire_risk = kwargs.get("fire_risk", 0.01) #pourcentage de chance
        self.location = kwargs.get("location", 0) #campagne = 1 ou ville = 0
        self.visible = kwargs.get("visible", True) #indique si le bâtiment est visible sur l'interface ou pas (True/False)

    def building_type(self, attribut):
            return self.type[attribut]