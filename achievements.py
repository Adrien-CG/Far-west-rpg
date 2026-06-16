"""Succes de partie et succes globaux."""


ACHIEVEMENTS = {
    "bartender": {
        "name": "Bartender",
        "description": "Le joueur a construit son premier saloon.",
    },
    "rancher": {
        "name": "Le rêve américain",
        "description": "Le joueur a construit son premier ranch.",
    },
}


def achievement_data(achievement_id):
    return ACHIEVEMENTS[achievement_id]


def is_unlocked(game, achievement_id):
    return achievement_id in getattr(game, "achievements", [])
