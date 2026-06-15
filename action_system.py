from character import ask_choice


def action(label, handler, condition=None):
    # Une action est une petite fiche : son texte, sa fonction, et une condition optionnelle.
    # Pour ajouter une action ailleurs, cree une ligne action("Texte", fonction).
    return {
        "label": label,
        "handler": handler,
        "condition": condition or always_available,
    }


def always_available(game, building=None):
    return True


def available_actions(actions, game, building=None):
    # Les actions dont la condition renvoie False ne seront pas affichees au joueur.
    return [
        current_action
        for current_action in actions
        if current_action["condition"](game, building)
    ]


def choose_action(prompt, actions, game, building=None, back_label="Retour"):
    # Transforme une liste d'actions en menu questionary, puis renvoie l'action choisie.
    choices = [
        {"label": current_action["label"], "action": current_action}
        for current_action in available_actions(actions, game, building)
    ]
    choices.append({"label": back_label, "action": None})

    selected = ask_choice(prompt, choices)
    return selected["action"]


def run_action(selected_action, game, building=None):
    # Les actions de ville recoivent seulement game.
    # Les actions de batiment recoivent game + building.
    if building is None:
        selected_action["handler"](game)
    else:
        selected_action["handler"](game, building)


def run_action_menu(prompt, actions, game, building=None, back_label="Retour"):
    # Renvoie False si le joueur choisit Retour/Quitter, True si une action a ete lancee.
    selected_action = choose_action(prompt, actions, game, building, back_label)

    if selected_action is None:
        return False

    run_action(selected_action, game, building)
    return True
