from action_system import action


def get_ranch_actions(building):
    # Actions disponibles quand le joueur entre dans un Ranch.
    return [
        action("Acheter des provisions", buy_ranch_goods),
    ]


def buy_ranch_goods(game, building):
    print("\nLe ranch vendra plus tard des provisions et du betail au joueur.")
