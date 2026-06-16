"""Types de logements disponibles dans la ville.

Plan du fichier:
01 - HOUSING_CATALOG: vue items du catalogue de logements.
02 - housing_definition: recupere une definition de logement.
"""

HOUSING_CATALOG = {
    "tente": {
        "label": "Tente",
        "utility": 25,
        "salubrity": 1,
        "rent_price": 0.25,
        "listed": True,
    },
    "bunkhouse": {
        "label": "Bunkhouse",
        "utility": 50,
        "salubrity": 2,
        "rent_price": 0.75,
        "listed": True,
    },
    "poorhouse": {
        "label": "Poorhouse",
        "utility": 35,
        "salubrity": 1,
        "rent_price": 0,
        "listed": False,
    },
    "cabane": {
        "label": "Cabane",
        "utility": 80,
        "salubrity": 2,
        "rent_price": 1,
        "listed": True,
    },
    "baraquement": {
        "label": "Baraquement",
        "utility": 60,
        "salubrity": 2,
        "rent_price": 0,
        "included_board": True,
        "listed": False,
    },
    "chambre": {
        "label": "Chambre",
        "utility": 130,
        "salubrity": 4,
        "rent_price": 1.5,
        "listed": True,
    },
    "appartement": {
        "label": "Appartement",
        "utility": 190,
        "salubrity": 5,
        "rent_price": 4,
        "listed": True,
    },
    "maison_ville": {
        "label": "Maison de ville",
        "utility": 260,
        "salubrity": 6,
        "rent_price": 7,
        "listed": True,
    },
    "maison_campagne": {
        "label": "Maison de campagne",
        "utility": 240,
        "salubrity": 5,
        "rent_price": 5,
        "listed": True,
    },
    "maison_bourgeoise": {
        "label": "Maison bourgeoise",
        "utility": 380,
        "salubrity": 8,
        "rent_price": 14,
        "listed": True,
    }
}

def housing_definition(housing_type):
    return HOUSING_CATALOG[housing_type]