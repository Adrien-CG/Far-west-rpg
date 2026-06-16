"""Animaux et betail special.

Plan du fichier:
01 - ANIMAL_CATALOG: constantes des animaux.
02 - animal_definition/label/price: acces aux definitions.
03 - animal rules: unique, troupeau, inventaire personnage interdit.
04 - base_animal_prices: prix nationaux de base des animaux.
"""

from copy import deepcopy


ANIMAL_CATALOG = {
    'taureau': {'id': 'taureau',
             'label': 'Taureau',
             'storage': 'unique',
             'character_inventory_allowed': False,
             'building_inventory_allowed': True,
             'herd_variable': None,
             'name': '',
             'base_price': 50,
             'fertility_values': [4, 8, 12, 16],
             'age_min': 0,
             'age_max': 6,
             'speed': 0,
             'carry': 0,
             'savings_use': False},
    'boeuf': {'id': 'boeuf',
           'label': 'Boeuf',
           'storage': 'herd',
           'character_inventory_allowed': False,
           'building_inventory_allowed': False,
           'herd_variable': 'head_count',
           'name': '',
           'base_price': 40,
           'fertility_values': [],
           'age_min': 0,
           'age_max': 10,
           'speed': 2,
           'carry': 180,
           'savings_use': False},
    'cheval': {'id': 'cheval',
            'label': 'Cheval',
            'storage': 'unique',
            'character_inventory_allowed': False,
            'building_inventory_allowed': True,
            'mount_allowed': True,
            'herd_variable': None,
            'name': '',
            'base_price': 30,
            'fertility_values': [],
            'age_min': 3,
            'age_max': 25,
            'speed': 10,
            'carry': 120}
}


def animal_definition(animal_id):
    return deepcopy(ANIMAL_CATALOG[animal_id])


def animal_label(animal_id):
    return ANIMAL_CATALOG[animal_id]["label"]


def animal_base_price(animal_id):
    return ANIMAL_CATALOG[animal_id]["base_price"]


def is_animal_id(item_id):
    return item_id in ANIMAL_CATALOG


def is_unique_animal(animal_id):
    return ANIMAL_CATALOG[animal_id].get("storage") == "unique"


def is_herd_animal(animal_id):
    return ANIMAL_CATALOG[animal_id].get("storage") == "herd"


def animal_allowed_in_character_inventory(animal_id):
    return ANIMAL_CATALOG.get(animal_id, {}).get("character_inventory_allowed", False)


def animal_allowed_in_building_inventory(animal_id):
    return ANIMAL_CATALOG.get(animal_id, {}).get("building_inventory_allowed", False)


def clean_character_inventory_from_animals(inventory):
    """Supprime les animaux d'un inventaire de personnage.

    Les animaux uniques doivent etre dans un inventaire de batiment ou dans
    `monture`; le betail de troupeau doit etre un chiffre de production.
    """
    for item_id in list(inventory.keys()):
        if is_animal_id(item_id) and not animal_allowed_in_character_inventory(item_id):
            inventory.pop(item_id, None)
    return inventory


def base_animal_prices():
    return {animal_id: data["base_price"] for animal_id, data in ANIMAL_CATALOG.items()}
