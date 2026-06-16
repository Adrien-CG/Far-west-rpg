import character

def is_player(chracter_id):
    """Vrai si le personnage est un joueur."""
    return character[chracter_id]["player"]

SALOON = {
    {
    # building information
    "type" : "", #saloon, ranch, hotel, etc.
    "id" : "",  #première lettre du type + numéro d'ordre (ex: s001 pour le premier saloon)
    "family" : "economic", #economic, public, housing
    "name" : "Saloon", #nom du bâtiment par défaut type + nom du propriétaire (ex: Saloon Conway)
    "owner" : "", #id du propriétaire (ex: c)
    "date" : "", #enregistre la saison et l'année (exemple : "p1870" avec p pour printemps, e pour été, a pour automne et h pour hiver)
    # economic values
    "production" : [{}], #variable de production du bâtiment (ex: prix de vente des services ou données du cattle drive)
    "stock" : [{"vivres_sec" : 0}, {"fut_biere" : 0}], #liste des bien à mettre avec une méthode si beaucoup de types différents (ex: [{"vivres_sec" : 0}, {"fut_biere" : 0}])
    "housing" : [{}], #liste des logements produits par le bâtiment (ex: ranch de base une maison de campagne et une chambre)
    "employees" : [{}], #liste des employés du bâtiment (id du personnage, salaire, poste)
    "jobs" : [{"barman" : 1}], #liste des emplois disponibles dans le bâtiment (ex: {'mineur' : 999, 'garde' : 4} etc.)
    "upgrades" : [""], #liste des améliorations réalisées sur le bâtiment (ex: "piano")
    # accountability values
    "money" : 0, #argent disponible dans le bâtiment
    "loan" : [{}], #liste des prêts en cours (ex: {'amount' : 1000, 'interest_rate' : 0.05, 'due_date' : "p1870", 'due to' : "bank id"})
    "accounting" : [
        {#bilan
            "building" : 0,
            "lands" : 0,
            "improvements" : 0,
            "licenses" : 0,
            "capital" : 0,
            "réserves" : 0,
        } 
        {#compte de résultat temporaire
            "ventes de marchandises" : 0,
            "ventes de services" : 0,
            "achat de marchandises" : 0,
            "salaires" : 0,
            "taxes" : 0,
            "remboursement de prêts" : 0,
            "charges d'intérêt" : 0,

        }
    ],
    "saved_accounting" : [{}], #liste des bilans et compte de résultat sauvegardés (ex: bilan de fin d'année) {'name' : "bilan 1870", 'terrain' : 100, 'construction' : 300, etc.}
    # building status values
    "under_construction" : True, #indique si le bâtiment est en construction ou pas (True/False)
    "fire_risk" : 1, #pourcentage de chance
    "location" : 0, #campagne = 1 ou ville = 0
    "visible" : True, #indique si le bâtiment est visible sur l'interface ou pas (True/False)
}
}
class Building:
    def __init__(self, type, **kwargs):
        self.id = id
        self.name = "Building"
        self.family = "Generic"
        self.under_construction = kwargs.get("under_construction", True)
        self.fire_risk = kwargs.get("fire_risk", 0.01)
        self.location =
        self.visible = kwargs.get(self.visible_statue(self), True)

    def charger_type(self, type):
        self.building_type = type

    def visible_statue(self):
        if self.family == "housing" and not is_player(self.owner):
            return False