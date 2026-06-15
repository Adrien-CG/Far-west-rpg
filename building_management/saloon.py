from action_system import action, run_action_menu
from building_management.shared import add_feature, add_upgrade, employee_names, open_role_recruitment


LIMITED_SALOON_UPGRADES = ["Chambre", "Cuisine", "Salle de bain"]
MAX_LIMITED_UPGRADES = 2


def open_saloon_improvement_menu(game, building):
    # Les trois grandes ameliorations sont limitees a deux choix.
    # Table de poker et piano sont des installations separees, hors limite.
    while True:
        actions = [
            action("Ajouter une chambre - 80 or", lambda g, b: add_limited_upgrade(g, b, "Chambre", 80), condition=can_add_limited_upgrade),
            action("Ajouter une cuisine - 60 or", lambda g, b: add_limited_upgrade(g, b, "Cuisine", 60), condition=can_add_limited_upgrade),
            action("Ajouter une salle de bain - 50 or", lambda g, b: add_limited_upgrade(g, b, "Salle de bain", 50), condition=can_add_limited_upgrade),
            action("Installer une table de poker - 40 or", lambda g, b: add_feature(g, b, "table_poker", "Table de poker", 40), condition=lambda g, b: not b.features.get("table_poker")),
            action("Installer un piano - 45 or", lambda g, b: add_feature(g, b, "piano", "Piano", 45), condition=lambda g, b: not b.features.get("piano")),
        ]

        should_continue = run_action_menu("Ameliorations du Saloon :", actions, game, building)

        if not should_continue:
            break


def add_limited_upgrade(game, building, upgrade_name, cost):
    if saloon_limited_upgrade_count(building) >= MAX_LIMITED_UPGRADES:
        print("\nLe Saloon ne peut avoir que deux grandes ameliorations.")
        return

    add_upgrade(game, building, upgrade_name, cost)


def can_add_limited_upgrade(game, building):
    return saloon_limited_upgrade_count(building) < MAX_LIMITED_UPGRADES


def saloon_limited_upgrade_count(building):
    return len([upgrade for upgrade in building.upgrades if upgrade in LIMITED_SALOON_UPGRADES])


def open_saloon_employee_menu(game, building):
    # Les postes disponibles dependent des ameliorations installees dans ce Saloon.
    while True:
        print("\n=== Employes du Saloon ===")
        print(f"Employes actuels : {employee_names(game, building)}")

        actions = [
            action("Recruter un barman", lambda g, b: open_role_recruitment(g, b, "Barman", 1)),
            action("Recruter un cuisinier", lambda g, b: open_role_recruitment(g, b, "Cuisinier", 1), condition=lambda g, b: "Cuisine" in b.upgrades),
            action("Recruter une hotesse", lambda g, b: open_role_recruitment(g, b, "Hotesse", 2), condition=has_hostess_space),
            action("Recruter un musicien", lambda g, b: open_role_recruitment(g, b, "Musicien", 1), condition=lambda g, b: b.features.get("piano", False)),
        ]

        should_continue = run_action_menu("Gestion des employes :", actions, game, building)

        if not should_continue:
            break


def has_hostess_space(game, building):
    return "Chambre" in building.upgrades or "Salle de bain" in building.upgrades
