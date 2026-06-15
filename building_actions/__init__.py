from building_actions.general_store import get_general_store_actions
from building_actions.ranch import get_ranch_actions
from building_actions.saloon import get_saloon_actions


# Registre des actions par type de batiment.
# Pour ajouter un nouveau type, cree son fichier dans building_actions/
# puis ajoute une ligne ici : "Nom du type": fonction_get_actions.
ACTION_PROVIDERS = {
    "General Store": get_general_store_actions,
    "Ranch": get_ranch_actions,
    "Saloon": get_saloon_actions,
}


def get_building_actions(building):
    # Le menu demande ici quelles actions correspondent au type du batiment selectionne.
    provider = ACTION_PROVIDERS.get(building.building_type)

    if provider is None:
        return []

    return provider(building)
