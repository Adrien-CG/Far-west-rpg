from building_actions.general_store import get_general_store_actions
from building_actions.ranch import get_ranch_actions
from building_actions.saloon import get_saloon_actions


ACTION_PROVIDERS = {
    "General Store": get_general_store_actions,
    "Ranch": get_ranch_actions,
    "Saloon": get_saloon_actions,
}


def get_building_actions(building):
    provider = ACTION_PROVIDERS.get(building.building_type)

    if provider is None:
        return []

    return provider(building)


def get_building_action_choices(building):
    return [
        {"label": action["label"], "action": action}
        for action in get_building_actions(building)
        if action.get("condition", lambda selected_building, building_id: True)(
            building,
            building.building_id,
        )
    ]


def run_building_action(game, building, action):
    action["handler"](game, building)
