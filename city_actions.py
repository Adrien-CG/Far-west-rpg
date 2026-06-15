from action_system import action, run_action_menu
from buildings import BUILDING_CATALOG, Building
from building_actions import get_building_actions
from building_management import open_accounting_menu, open_employee_menu, open_improvement_menu
from character import ask_choice, ask_text
from ids import make_building_id
from saves import save_game


def show_city(game):
    city = game.city

    print(f"\n=== {city.name} - Jour {city.day} ===")
    print(f"Reputation : {city.reputation}")
    print(f"Securite : {city.security}")
    print("\nBatiments :")

    for building in city.buildings:
        print(
            f"- {building.name} ({building.building_type}) "
            f"| ID : {building.building_id} | Proprietaire : {building.owner} | Niveau : {building.level}"
        )


def show_character_sheet(game):
    character = game.character

    print("\n=== Fiche personnage ===")
    print(f"Nom : {character.name}")
    print(f"Sexe : {character.sex}")
    print(f"Age : {character.age}")
    print(f"Origine : {character.origin}")
    print(f"Vie : {character.health}/{character.max_health}")
    print(f"Force : {character.strength}")
    print(f"Sociabilite : {character.sociability}")
    print(f"Intelligence : {character.intelligence}")
    print(f"Argent : {character.money}")
    print(f"Revenu : {character.income}")
    print(f"Competences : {', '.join(character.skills) if character.skills else 'Aucune'}")
    print(f"Inventaire : {character.inventory or 'Vide'}")


def enter_building(game):
    building_choices = [
        {"label": f"{building.name} ({building.building_type})", "building": building}
        for building in game.city.buildings
    ]
    building_choices.append({"label": "Retour", "building": None})

    selected = ask_choice("Dans quel batiment veux-tu entrer ?", building_choices)

    if selected["building"] is None:
        return

    building_menu(game, selected["building"])


def show_population(game):
    print("\n=== Population de la ville ===")

    for npc in game.city.population:
        marker = " *" if npc.notable else ""
        spouse = game.city.get_npc_by_id(npc.spouse_id) if npc.spouse_id else None
        spouse_text = f" | Marie avec : {spouse.name}" if spouse else ""
        employer_text = ""

        if npc.employer_building_id:
            building = game.city.get_building_by_id(npc.employer_building_id)
            if building:
                employer_text = f" | Lieu : {building.name}"

        print(
            f"- {npc.name}{marker} | {npc.sex}, {npc.age} ans | {npc.origin} | {npc.job}"
            f" | For {npc.strength} / Soc {npc.sociability} / Int {npc.intelligence}"
            f" | Revenu {npc.income} | Argent {npc.money}"
            f"{employer_text}{spouse_text}"
        )


def building_menu(game, building):
    if building.is_public:
        public_building_menu(game, building)
        return

    business_building_menu(game, building)


def business_building_menu(game, building):
    while True:
        print(f"\n=== {building.name} ===")
        print(f"ID : {building.building_id}")
        print(f"Type : {building.building_type}")
        print(f"Proprietaire : {building.owner}")

        # Actions propres au type de batiment : Saloon, Ranch, General Store...
        actions = get_building_actions(building)

        if building.owner == game.character.name:
            # La gestion n'apparait que si le joueur possede ce batiment.
            actions.append(action("Gestion du batiment", owned_business_menu))

        should_continue = run_action_menu(
            "Action disponible :",
            actions,
            game,
            building,
            back_label="Retour en ville",
        )

        if not should_continue:
            break


def public_building_menu(game, building):
    while True:
        print(f"\n=== {building.name} ===")
        print(f"ID : {building.building_id}")

        should_continue = run_action_menu(
            "Action disponible :",
            public_building_actions(building),
            game,
            building,
            back_label="Retour en ville",
        )

        if not should_continue:
            break


def public_building_actions(building):
    # Les batiments publics peuvent aussi utiliser le systeme d'actions commun.
    if building.building_type == "Bureau du sherif":
        return [
            action("Consulter les avis de recherche", show_wanted_notices),
            action("Signaler un probleme", report_problem),
        ]

    if building.building_type == "Post Office":
        return [
            action("Lire le courrier", read_mail),
            action("Envoyer une lettre", send_letter),
        ]

    return []


def show_wanted_notices(game, building):
    print("\nAucun avis urgent pour le moment.")


def report_problem(game, building):
    game.city.security += 1
    print("\nLe sherif note ton signalement. La securite de la ville augmente.")


def read_mail(game, building):
    print("\nTu n'as pas encore de courrier.")


def send_letter(game, building):
    print("\nLa lettre partira avec la prochaine diligence.")


def owned_business_menu(game, building):
    while True:
        print(f"\n=== Gestion : {building.name} ===")
        print(f"ID : {building.building_id}")
        print(f"Type : {building.building_type}")
        print(f"Niveau : {building.level}")

        # Actions de gestion communes aux batiments possedes par le joueur.
        actions = [
            action("Comptabilite", open_accounting_menu),
            action("Ameliorations", open_improvement_menu),
            action("Employes", open_employee_menu),
            action("Achats de marchandises", buy_supplies),
        ]

        should_continue = run_action_menu(
            "Fenetre de gestion :",
            actions,
            game,
            building,
            back_label="Retour en ville",
        )

        if not should_continue:
            break


def buy_supplies(game, building):
    available_supplies = supplies_for_building(building)
    choices = []

    for supply_name, unit_price in available_supplies.items():
        choices.append({"label": f"Acheter {supply_name} - {unit_price} or", "supply": supply_name, "price": unit_price})

    choices.append({"label": "Retour", "supply": None, "price": 0})
    selected = ask_choice("Quelle marchandise veux-tu acheter ?", choices)

    if selected["supply"] is None:
        return

    if game.character.money < selected["price"]:
        print("\nTu n'as pas assez d'or.")
        return

    game.character.money -= selected["price"]
    building.inventory[selected["supply"]] = building.inventory.get(selected["supply"], 0) + 1

    print(f"\n+1 {selected['supply']} ajoute au stock de {building.name}.")


def supplies_for_building(building):
    if building.building_type == "Ranch":
        return {"cereales": 5, "betail": 25}

    if building.building_type == "Saloon":
        return {"biere": 8, "produits de consommation": 12}

    return {}


def construct_building(game):
    choices = []

    for building_type, data in BUILDING_CATALOG.items():
        choices.append(
            {
                "label": f"{building_type} - {data['base_cost']} or",
                "building_type": building_type,
                "cost": data["base_cost"],
            }
        )

    choices.append({"label": "Retour", "building_type": None, "cost": 0})
    selected = ask_choice("Quel batiment veux-tu construire ?", choices)

    if selected["building_type"] is None:
        return

    if game.character.money < selected["cost"]:
        print("\nTu n'as pas assez d'or pour construire ce batiment.")
        return

    building_name = ask_text("Nom du batiment : ")
    existing_ids = {building.building_id for building in game.city.buildings}
    game.character.money -= selected["cost"]
    game.city.buildings.append(
        Building(
            building_id=make_building_id(selected["building_type"], existing_ids),
            name=building_name,
            building_type=selected["building_type"],
            owner=game.character.name,
            level=1,
            features=BUILDING_CATALOG[selected["building_type"]]["features"].copy(),
            inventory=BUILDING_CATALOG[selected["building_type"]]["inventory"].copy(),
            hidden_stats=BUILDING_CATALOG[selected["building_type"]]["hidden_stats"].copy(),
        )
    )

    print(f"\n{building_name} est maintenant construit.")


def show_building_catalog(game):
    print("\n=== Batiments constructibles ===")

    for building_type, data in BUILDING_CATALOG.items():
        print(f"- {building_type} : {data['base_cost']} or")
        print(f"  {data['description']}")


def work_in_town(game):
    earned_money = 10 + game.character.strength
    game.character.money += earned_money
    game.character.health = max(0, game.character.health - 5)

    print("\nTu aides aux travaux de la ville.")
    print(f"Tu gagnes {earned_money} pieces d'or, mais tu perds 5 points de vie.")


def end_day(game):
    game.city.day += 1

    print(f"\nLa ville passe au jour {game.city.day}.")

    for building in game.city.buildings:
        if building.level <= 0:
            continue

        result = calculate_building_result(building)

        building.current_result = result
        building.current_balance += result
        building.result_history.append(result)
        building.balance_history.append(building.current_balance)

    game.character.health = min(game.character.max_health, game.character.health + 3)
    print("Les batiments mettent a jour leur bilan.")


def calculate_building_result(building):
    if building.is_public:
        return 0

    if building.building_type == "Ranch":
        cereales = building.inventory.get("cereales", 0)
        betail = building.inventory.get("betail", 0)
        fertilite = building.hidden_stats.get("fertilite", 5)
        qualite_betail = building.hidden_stats.get("qualite_betail", 5)
        employee_bonus = len(building.employees) * 3

        consumed_cereales = min(cereales, betail)
        building.inventory["cereales"] = cereales - consumed_cereales

        income = betail * qualite_betail + consumed_cereales * fertilite + employee_bonus
        maintenance = 8 + building.level * 2
        return income - maintenance

    if building.building_type == "Saloon":
        biere = building.inventory.get("biere", 0)
        attrait_clients = building.hidden_stats.get("attrait_clients", 5)
        ambiance = building.hidden_stats.get("ambiance", 5)
        employee_bonus = len(building.employees) * 4

        served_beer = min(biere, building.level * 3 + len(building.employees))
        building.inventory["biere"] = biere - served_beer

        income = served_beer * attrait_clients + ambiance + employee_bonus
        maintenance = 10 + building.level * 3
        return income - maintenance

    return 0


def save_current_game(game):
    save_path = save_game(game)
    print(f"\nPartie sauvegardee : {save_path}")


def city_menu(game):
    while True:
        # Vue principale de la ville : plus tard l'interface pourra afficher ces actions
        # dans une zone separee de la liste des batiments et du bouton Construire.
        actions = [
            action("Voir la ville", show_city),
            action("Voir la population", show_population),
            action("Entrer dans un batiment", enter_building),
            action("Voir les batiments constructibles", show_building_catalog),
            action("Construire un batiment", construct_building),
            action("Travailler en ville", work_in_town),
            action("Voir le personnage", show_character_sheet),
            action("Passer au jour suivant", end_day),
            action("Sauvegarder", save_current_game),
        ]

        should_continue = run_action_menu(
            f"{game.city.name} - Que veux-tu faire ?",
            actions,
            game,
            back_label="Quitter",
        )

        if not should_continue:
            save_current_game(game)
            print("\nA bientot.")
            break
