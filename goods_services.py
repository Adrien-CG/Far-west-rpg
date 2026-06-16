"""Pont de compatibilite pour biens et services.

Plan du fichier:
01 - SATURATION_CENTERS: valeurs de preference selon saturation.
02 - ITEM_CATALOG: catalogue combine biens + services.
03 - LEGACY_ITEM_IDS: anciens noms convertis vers les ids actuels.
04 - item_id/item_definition/item_label: acces generique aux definitions.
05 - base_market_prices: prix nationaux initiaux, biens + animaux.
06 - preference/service helpers: fonctions utilitaires historiques.
"""

from copy import deepcopy

from items.animals import ANIMAL_CATALOG, base_animal_prices
from items.goods import GOODS_CATALOG
from items.services import SERVICE_CATALOG, service_base_utility, service_default_price


SATURATION_CENTERS = {
    0: [],
    "unique": [1.0],
    "elevee": [0.8, 0.2],
    "moyenne": [1.0, 0.7, 0.3],
    "faible": [1.0, 0.8, 0.6, 0.4, 0.2],
}

DEFAULT_SAVINGS_USE = False
ITEM_CATALOG = {**GOODS_CATALOG, **SERVICE_CATALOG}


LEGACY_ITEM_IDS = {'Vivres': 'vivres_secs',
 'vivres': 'vivres_secs',
 'Vivres secs': 'vivres_secs',
 'Vivres séchées': 'vivres_secs',
 'Vivres frais': 'vivres_frais',
 'Vivres fraîche': 'vivres_frais',
 'Vivres fraîches': 'vivres_frais',
 'Conserves': 'conserves',
 'Vivres de luxe': 'vivres_luxe',
 'Sucre': 'sucre',
 'Confiserie': 'confiserie',
 'Confiseries': 'confiserie',
 'Tabac': 'tabac',
 'Café': 'cafe',
 'Cafe': 'cafe',
 'Thé': 'the',
 'The': 'the',
 'Cigarette': 'cigarette',
 'Cigarettes': 'cigarette',
 'Cigare': 'cigare',
 'Whisky': 'whisky',
 'Gnôle': 'gnole',
 'Gniole': 'gnole',
 'Gnole': 'gnole',
 'Vin': 'vin',
 'Cognac': 'cognac',
 'Bourbon': 'bourbon',
 'Charbon': 'charbon',
 'Fer': 'fer',
 'Minerai de fer': 'minerai_fer',
 'Cuivre': 'cuivre',
 'Minerai de cuivre': 'minerai_cuivre',
 'Nickel': 'nickel',
 'Minerai de nickel': 'minerai_nickel',
 'Or': 'or',
 "Minerai d'or": 'minerai_or',
 'Argent': 'argent',
 "Minerai d'argent": 'minerai_argent',
 'Acier': 'acier',
 'Bois': 'bois',
 'Planche': 'planche',
 'Bois de chauffage': 'bois_chauffage',
 'Charbon de bois': 'charbon_bois',
 'Laine': 'laine',
 'Coton': 'coton',
 'Soie': 'soie',
 'Tissu': 'tissu',
 'Outils': 'outils',
 'Explosif': 'explosifs',
 'Explosifs': 'explosifs',
 'explosif': 'explosifs',
 'explosifs': 'explosifs',
 'Papier': 'papier',
 'Journal': 'journal',
 'Livre': 'livre',
 'Engrais': 'engrais',
 'Pétrole': 'petrole',
 'Haillon': 'haillon',
 'Habit de travail': 'habit_travail',
 'Habits de travail': 'habit_travail',
 'Habit ordinaire': 'habit_ordinaire',
 'Habits ordinaire': 'habit_ordinaire',
 'Habits ordinaires': 'habit_ordinaire',
 'Habit élégant': 'habit_elegant',
 'Habits élégant': 'habit_elegant',
 'Habits élégants': 'habit_elegant',
 'Manteau': 'manteau',
 'Cache-poussière': 'cache_poussiere',
 'Cache poussière': 'cache_poussiere',
 'Colt Navy': 'colt_navy',
 'Colt navy': 'colt_navy',
 'Fusil Springfield': 'fusil_springfield',
 'Fusil springfield': 'fusil_springfield',
 'Carabine Spencer': 'carabine_spencer',
 'Carabine spencer': 'carabine_spencer',
 'Matériel de prospection': 'materiel_prospection',
 'Plantes médicinales': 'plantes_medicinales',
 'Bandage': 'bandage',
 'Bandages': 'bandage',
 'Remède': 'remede'}


def item_id(item_id_value):
    return LEGACY_ITEM_IDS.get(item_id_value, item_id_value)


def item_definition(item_id_value):
    normalized = item_id(item_id_value)
    if normalized in ITEM_CATALOG:
        return ITEM_CATALOG[normalized]
    if normalized in ANIMAL_CATALOG:
        return ANIMAL_CATALOG[normalized]
    raise KeyError(normalized)


def item_label(item_id_value):
    return item_definition(item_id_value)["label"]


def base_market_prices():
    prices = {
        item_id_value: data["base_price"]
        for item_id_value, data in GOODS_CATALOG.items()
    }
    prices.update(base_animal_prices())
    prices["betail"] = prices.get("boeuf", 40)
    return prices


def preference_centers_for(item_id_value):
    data = item_definition(item_id_value)
    return deepcopy(SATURATION_CENTERS[data["saturation"]])
