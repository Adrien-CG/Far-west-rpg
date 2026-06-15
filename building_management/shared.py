from action_system import action, run_action_menu
from character import ask_choice


HIRABLE_JOBS = ["Journalier", "Journaliere", "Oisif", "Oisive", "Chomeur", "Chomeuse"]


def employee_names(game, building):
    # Convertit les npc_id stockes dans le batiment en noms lisibles.
    names = []

    for employee_id in building.employees:
        npc = game.city.get_npc_by_id(employee_id)
        role = building.employee_roles.get(employee_id, "Employe")
        task = building.employee_tasks.get(employee_id)
        task_text = f" - {task}" if task else ""
        names.append(f"{npc.name if npc else employee_id} ({role}{task_text})")

    return ", ".join(names) if names else "Aucun"


def employees_with_role(building, role):
    return [
        employee_id
        for employee_id, employee_role in building.employee_roles.items()
        if employee_role == role
    ]


def role_count(building, role):
    return len(employees_with_role(building, role))


def open_role_recruitment(game, building, role, limit):
    # Recrutement generique : chaque batiment choisit ses roles et ses limites.
    if role_count(building, role) >= limit:
        print(f"\nNombre maximum atteint pour le poste : {role}.")
        return

    available_workers = [
        npc
        for npc in game.city.population
        if npc.employer_building_id is None and npc.job in HIRABLE_JOBS
    ]

    if not available_workers:
        print("\nPersonne n'est disponible a l'embauche pour le moment.")
        return

    choices = [
        {"label": f"{npc.name} - {npc.job}", "npc": npc}
        for npc in available_workers
    ]
    choices.append({"label": "Retour", "npc": None})
    selected = ask_choice(f"Qui veux-tu recruter comme {role} ?", choices)

    if selected["npc"] is None:
        return

    recruited_npc = selected["npc"]
    recruited_npc.job = role
    recruited_npc.employer_building_id = building.building_id
    building.employees.append(recruited_npc.npc_id)
    building.employee_roles[recruited_npc.npc_id] = role

    print(f"\n{recruited_npc.name} travaille maintenant comme {role} a {building.name}.")


def add_upgrade(game, building, upgrade_name, cost):
    if upgrade_name in building.upgrades:
        print("\nCette amelioration existe deja.")
        return

    if game.character.money < cost:
        print(f"\nIl te faut {cost} pieces d'or.")
        return

    game.character.money -= cost
    building.upgrades.append(upgrade_name)
    building.account_journal.append(f"Achat amelioration : {upgrade_name} (-{cost})")

    print(f"\nAmelioration ajoutee : {upgrade_name}.")


def add_feature(game, building, feature_name, label, cost):
    if building.features.get(feature_name):
        print("\nCette installation existe deja.")
        return

    if game.character.money < cost:
        print(f"\nIl te faut {cost} pieces d'or.")
        return

    game.character.money -= cost
    building.features[feature_name] = True
    building.account_journal.append(f"Achat installation : {label} (-{cost})")

    print(f"\nInstallation ajoutee : {label}.")
