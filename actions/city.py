"""Actions qui peuvent apparaitre hors d'un batiment obligatoire.

Une action peut etre generale, venir d'une competence, ou etre proposee par un
batiment mais affichee sur la vue ville. Exemple: chercher des plantes vient du
cabinet medical, mais apparait dehors.
"""


def get_city_actions(game):
    actions = []
    actions.extend(get_general_city_actions(game))
    for building in game.city.buildings:
        city_actions = getattr(building, "city_actions", None)
        if city_actions:
            actions.extend(city_actions(game))
    return actions


def get_general_city_actions(game):
    result = ["Construire", "Finir le tour"]
    character = game.character
    if "Prospection" in getattr(character, "skills", []) and character.inventory.get("materiel_prospection", 0) > 0:
        result.append("Prospecter la région")
    if "Chasse" in getattr(character, "skills", []) and has_long_weapon(character):
        result.append("Chasser")
    if "Criminalité" in getattr(character, "skills", []):
        result.append("Trouver un repaire")
    return result


def has_long_weapon(character):
    return any(item in character.inventory for item in ["fusil_springfield", "carabine_spencer"])
