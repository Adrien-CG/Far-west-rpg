from action_system import action, run_action_menu
from building_management.shared import add_upgrade, employee_names, employees_with_role, open_role_recruitment
from character import ask_choice


RANCH_TASKS = [
    "Planter des piquets",
    "Garder le troupeau",
    "Amener le troupeau aux abattoirs",
]


def open_ranch_improvement_menu(game, building):
    # Le Ranch est un ensemble de batiments : ajoute ici grange, silo, logements, etc.
    while True:
        actions = [
            action("Construire une grange - 70 or", lambda g, b: add_upgrade(g, b, "Grange", 70)),
            action("Construire un silo - 60 or", lambda g, b: add_upgrade(g, b, "Silo", 60)),
            action("Construire des logements employes - 90 or", lambda g, b: add_upgrade(g, b, "Logements employes", 90)),
        ]

        should_continue = run_action_menu("Ameliorations du Ranch :", actions, game, building)

        if not should_continue:
            break


def open_ranch_employee_menu(game, building):
    # Les cowboys ont des taches sauvegardees dans building.employee_tasks.
    # La simulation de fin de tour utilisera ces taches plus tard.
    while True:
        print("\n=== Employes du Ranch ===")
        print(f"Employes actuels : {employee_names(game, building)}")

        actions = [
            action("Recruter un cowboy", lambda g, b: open_role_recruitment(g, b, "Cowboy", cowboy_limit(b))),
            action("Assigner les taches des cowboys", assign_cowboy_tasks, condition=has_cowboys),
        ]

        should_continue = run_action_menu("Gestion des employes :", actions, game, building)

        if not should_continue:
            break


def cowboy_limit(building):
    # Limite de base : 2 cowboys. Les logements employes augmentent cette limite.
    base_limit = 2

    if "Logements employes" in building.upgrades:
        return base_limit + 2

    return base_limit


def has_cowboys(game, building):
    return len(employees_with_role(building, "Cowboy")) > 0


def assign_cowboy_tasks(game, building):
    cowboys = employees_with_role(building, "Cowboy")
    choices = []

    for employee_id in cowboys:
        npc = game.city.get_npc_by_id(employee_id)
        current_task = building.employee_tasks.get(employee_id, "Aucune tache")
        label = f"{npc.name if npc else employee_id} - {current_task}"
        choices.append({"label": label, "employee_id": employee_id})

    choices.append({"label": "Retour", "employee_id": None})
    selected_employee = ask_choice("Quel cowboy veux-tu assigner ?", choices)

    if selected_employee["employee_id"] is None:
        return

    task_choices = [
        {"label": task_name, "task": task_name}
        for task_name in RANCH_TASKS
    ]
    task_choices.append({"label": "Retour", "task": None})
    selected_task = ask_choice("Quelle tache lui assigner ?", task_choices)

    if selected_task["task"] is None:
        return

    building.employee_tasks[selected_employee["employee_id"]] = selected_task["task"]
    print("\nTache assignee.")
