from action_system import action


# Prix utilises par les actions du General Store.
BUY_PRICES = {
    "arme": 45,
    "cereales": 5,
    "viande": 8,
}

SELL_PRICES = {
    "cereales": 3,
    "viande": 5,
}

STORE_STOCK_NAMES = {
    "arme": "armes",
    "cereales": "cereales",
    "viande": "viande",
}


def get_general_store_actions(building):
    # Ajouter une action de magasin = ajouter une ligne ici + une fonction si besoin.
    return [
        action("Acheter une arme", lambda game, selected_building: buy_item(game, selected_building, "arme")),
        action("Acheter des cereales", lambda game, selected_building: buy_item(game, selected_building, "cereales")),
        action("Acheter de la viande", lambda game, selected_building: buy_item(game, selected_building, "viande")),
        action("Vendre des cereales", lambda game, selected_building: sell_item(game, selected_building, "cereales")),
        action("Vendre de la viande", lambda game, selected_building: sell_item(game, selected_building, "viande")),
        action("Voir les stocks du magasin", show_store_stock),
    ]


def buy_item(game, building, item_name):
    stock_name = STORE_STOCK_NAMES[item_name]
    price = BUY_PRICES[item_name]

    if building.inventory.get(stock_name, 0) <= 0:
        print("\nLe magasin n'a plus cet article.")
        return

    if game.character.money < price:
        print("\nTu n'as pas assez d'argent.")
        return

    game.character.money -= price
    game.character.inventory[item_name] = game.character.inventory.get(item_name, 0) + 1
    building.inventory[stock_name] -= 1
    building.current_balance += price

    print(f"\nTu achetes : {item_name}.")


def sell_item(game, building, item_name):
    price = SELL_PRICES[item_name]

    if game.character.inventory.get(item_name, 0) <= 0:
        print("\nTu n'as pas cet objet a vendre.")
        return

    game.character.inventory[item_name] -= 1
    if game.character.inventory[item_name] == 0:
        del game.character.inventory[item_name]

    game.character.money += price
    building.inventory[STORE_STOCK_NAMES[item_name]] = building.inventory.get(STORE_STOCK_NAMES[item_name], 0) + 1
    building.current_balance -= price

    print(f"\nTu vends : {item_name}.")


def show_store_stock(game, building):
    print("\n=== Stocks du General Store ===")

    for item_name, quantity in building.inventory.items():
        print(f"- {item_name} : {quantity}")
