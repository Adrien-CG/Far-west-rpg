from action_system import action, run_action_menu


def open_accounting_menu(game, building):
    # Menu commun a tous les batiments economiques.
    # Pour l'instant les ecrans existent, les vrais calculs viendront avec la fin de tour.
    while True:
        actions = [
            action("Bilan", show_balance_sheet),
            action("Resultat", show_income_statement),
            action("Journal de comptes", show_account_journal),
        ]

        should_continue = run_action_menu(
            "Comptabilite :",
            actions,
            game,
            building,
        )

        if not should_continue:
            break


def show_balance_sheet(game, building):
    print("\n=== Bilan ===")
    print(f"Solde actuel : {building.current_balance}")
    print(f"Stocks : {building.inventory or 'Aucun'}")
    print(f"Ameliorations : {', '.join(building.upgrades) if building.upgrades else 'Aucune'}")


def show_income_statement(game, building):
    print("\n=== Resultat ===")
    print(f"Resultat actuel : {building.current_result}")
    print(f"Historique resultats : {building.result_history or 'Aucun'}")
    print(f"Historique soldes : {building.balance_history or 'Aucun'}")


def show_account_journal(game, building):
    print("\n=== Journal de comptes ===")

    if not building.account_journal:
        print("Aucune entree pour le moment.")
        return

    for entry in building.account_journal:
        print(f"- {entry}")
