import importlib
from models import *
from models.buildings.buildings_config import *
from game_values import *
from methods import *

### PARTIE PRODUCTEUR ###

#classe des offres
class Offer:
    _id_compteur = 0
    def __init__(self, item, producer, quantity, **kwargs):
        Offer._id_compteur += 1
        #information
        self.nature: str = item.nature
        self.family: str = item.family
        self.type_: str = item.type_
        self.producer: str = producer
        #rules
        self.savings_use: bool = item.saving_use
        self.fractionnable: bool = item.fractionnable
        #economic values
        self.price: float = kwargs.get("price", item.price)
        self.quantity = float(quantity) if self.fractionnable else int(quantity)
        self.weight: float = item.weight
        self.utility : float = kwargs.get("utility", item.utility)

#méthode pour créer une offre

#méthode pour supprimer une  offre

#classe des demandes
class Demand:
    _id_counter = 0
    def __init__(self, item):
        Demand._id_counter += 1
        #information
        pass

#récupère la méthode d'exploitation selon le type de bâtiment
def get_exploitation(type_):
    method_name = f"{type_}_exploitation"
    module = importlib.import_module(f"models.building.{type_}.{method_name}")
    return getattr(module, method_name)

#appel des méthodes d'exploitation de chaque bâtiment et création de la liste d'offre
def exploitation_global():
    offer_global = []
    demand_global = []

    for b in BUILDINGS_LIST:
        type_ = Building[b].type_
        method = get_exploitation(type_)
        result = method(b)
        offer_global.append(result[0])
        demand_global.append(result[1])

    offer_global -= demand_global

    return offer_global

### PARTIE REVENUE ###

def income():
    return

### PARTIE CONSOMMATEUR ###

#création de la demande

### PARTIE OFFRE/DEMANDE ###

def calcul_utility_ratio(utility, coefficient, income, price):
    ratio = utility*coefficient*income/price
    return ratio

def preference(offer_global):
    for p in POPULATION :
        preference_sorted = []
        preference_table = Character[p].preference
        income = Character[p].income
        for item in preference_table :
            for coef in item :
                for x in object_filter(Offer, offer_global, "type_", item):
                    utility = getattr(Offer[x], "utility")
                    price = getattr(Offer[x], "price")
                    calcul_utility_ratio(utility, coef, income, p)

            

    return

def cunsumption():
    offer_global = exploitation_global()

    for p in POPULATION :
        table_preference = Character[p].preference
        preference(offer_global)
    

### METHODE ECONOMIQUE ###

#echange local
def local_exchange(item, price, quantity, buyer, seller):
    return

#ratio pour le rendement d'échelle des national price
NATIONAL_PRICE_RATIO = 0.1

#achat sur le marché national
def national_purchase(item, quantity, buyer):
    return

#fonction prix depuis marché naional
def national_sell(item, quantity, seller):
    return

#vente sur le marché national
def national_price_buying(item):
    return

#fonctions prix vers le marché national
def national_price_selling(item):
    return

