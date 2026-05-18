def get_ranch_actions(building):
    return [
        {
            "label": "Acheter des provisions",
            "handler": buy_ranch_goods,
        },
    ]


def buy_ranch_goods(game, building):
    print("\nLe ranch vendra plus tard des provisions et du betail au joueur.")
