from action_system import action


def get_saloon_actions(building):
    # Pour ajouter une action au Saloon, ajoute une ligne action(...) dans cette liste.
    # Une condition permet de masquer l'action tant que le batiment n'a pas la bonne option.
    return [
        action("Boire une biere", drink_beer),
        action("Jouer au poker", play_poker, condition=has_poker_table),
    ]


def has_poker_table(game, building):
    # Exemple de condition : le poker apparait seulement si ce Saloon a une table.
    return building.features.get("table_poker", False)


def play_poker(game, building):
    entry_cost = 10

    if game.character.money < entry_cost:
        print("\nIl te faut 10 pieces d'or pour t'asseoir a la table.")
        return

    game.character.money -= entry_cost

    score = game.character.sociability + game.character.intelligence
    if score >= 12:
        winnings = 25
        game.character.money += winnings
        building.current_balance += entry_cost
        print(f"\nBelle main. Tu gagnes {winnings - entry_cost} pieces d'or nettes.")
    else:
        building.current_balance += entry_cost
        print("\nMauvaise main. Tu perds ta mise.")


def drink_beer(game, building):
    price = 2

    if game.character.money < price:
        print("\nTu n'as pas assez d'argent pour une biere.")
        return

    if building.inventory.get("biere", 0) <= 0:
        print("\nLe saloon n'a plus de biere.")
        return

    game.character.money -= price
    building.inventory["biere"] -= 1
    building.current_balance += price
    game.character.health = min(game.character.max_health, game.character.health + 1)

    print("\nTu bois une biere. Rien de glorieux, mais ca remet un peu d'aplomb.")
