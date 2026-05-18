from buildings import BUILDING_CATALOG, Building
from building_actions import get_building_action_choices, run_building_action
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

        choices = get_building_action_choices(building)

        if building.owner == game.character.name:
            choices.extend(
                [
                    {"label": "Gestion du batiment"},
                ]
            )

        choices.append({"label": "Retour en ville"})

        selected = ask_choice("Action disponible :", choices)
        label = selected["label"]

        if selected.get("action"):
            run_building_action(game, building, selected["action"])
        elif label == "Gestion du batiment":
            owned_business_menu(game, building)
        elif label == "Retour en ville":
            break


def install_building_feature(game, building):
    if building.building_type != "Saloon":
        print("\nAucune installation speciale disponible pour ce batiment.")
        return

    choices = []

    if not building.features.get("table_poker"):
        choices.append({"label": "Installer une table de poker - 40 or", "feature": "table_poker", "cost": 40})

    choices.append({"label": "Retour", "feature": None, "cost": 0})
    selected = ask_choice("Quelle installation veux-tu ajouter ?", choices)

    if selected["feature"] is None:
        return

    if game.character.money < selected["cost"]:
        print("\nTu n'as pas assez d'or.")
        return

    game.character.money -= selected["cost"]
    building.features[selected["feature"]] = True
    print("\nLa table de poker est installee. Les clients peuvent maintenant jouer.")


def public_building_menu(game, building):
    while True:
        print(f"\n=== {building.name} ===")
        print(f"ID : {building.building_id}")

        if building.building_type == "Bureau du sherif":
            choices = [
                {"label": "Consulter les avis de recherche"},
                {"label": "Signaler un probleme"},
                {"label": "Retour en ville"},
            ]
        elif building.building_type == "Post Office":
            choices = [
                {"label": "Lire le courrier"},
                {"label": "Envoyer une lettre"},
                {"label": "Retour en ville"},
            ]
        else:
            choices = [{"label": "Retour en ville"}]

        selected = ask_choice("Action disponible :", choices)

        if selected["label"] == "Consulter les avis de recherche":
            print("\nAucun avis urgent pour le moment.")
        elif selected["label"] == "Signaler un probleme":
            game.city.security += 1
            print("\nLe sherif note ton signalement. La securite de la ville augmente.")
        elif selected["label"] == "Lire le courrier":
            print("\nTu n'as pas encore de courrier.")
        elif selected["label"] == "Envoyer une lettre":
            print("\nLa lettre partira avec la prochaine diligence.")
        elif selected["label"] == "Retour en ville":
            break


def owned_business_menu(game, building):
    while True:
        print(f"\n=== Gestion : {building.name} ===")
        print(f"ID : {building.building_id}")
        print(f"Type : {building.building_type}")
        print(f"Niveau : {building.level}")

        selected = ask_choice(
            "Fenetre de gestion :",
            [
                {"label": "Documents financiers"},
                {"label": "Ameliorations"},
                {"label": "Installations speciales"},
                {"label": "Employes"},
                {"label": "Achats de marchandises"},
                {"label": "Retour en ville"},
            ],
        )

        if selected["label"] == "Documents financiers":
            show_building_report(game, building)
        elif selected["label"] == "Ameliorations":
            upgrade_building(game, building)
        elif selected["label"] == "Installations speciales":
            install_building_feature(game, building)
        elif selected["label"] == "Employes":
            employee_menu(game, building)
        elif selected["label"] == "Achats de marchandises":
            buy_supplies(game, building)
        elif selected["label"] == "Retour en ville":
            break


def show_building_report(game, building):
    print("\n=== Bilan du batiment ===")
    print(f"ID : {building.building_id}")
    print(f"Solde actuel : {building.current_balance}")
    print(f"Resultat actuel : {building.current_result}")
    print(f"Stocks : {building.inventory or 'Aucun'}")
    print(f"Installations : {visible_features(building)}")
    print(f"Employes : {employee_names(game, building)}")
    print(f"Ameliorations : {', '.join(building.upgrades) if building.upgrades else 'Aucune'}")
    print(f"Historique soldes : {building.balance_history or 'Aucun'}")
    print(f"Historique resultats : {building.result_history or 'Aucun'}")


def employee_names(game, building):
    names = []

    for employee_id in building.employees:
        npc = game.city.get_npc_by_id(employee_id)
        names.append(npc.name if npc else employee_id)

    return ", ".join(names) if names else "Aucun"


def visible_features(building):
    enabled_features = [
        feature_name.replace("_", " ")
        for feature_name, is_enabled in building.features.items()
        if is_enabled
    ]

    return ", ".join(enabled_features) if enabled_features else "Aucune"


def upgrade_building(game, building):
    cost = 30 * (building.level + 1)

    if building.owner != game.character.name:
        print("\nTu ne peux pas ameliorer un batiment qui ne t'appartient pas.")
        return

    if game.character.money < cost:
        print(f"\nIl te faut {cost} pieces d'or pour ameliorer ce batiment.")
        return

    game.character.money -= cost
    building.level += 1
    building.upgrades.append(f"Niveau {building.level}")

    print(f"\n{building.name} passe au niveau {building.level}.")


def hire_employee(game, building):
    cost = 15

    if building.owner != game.character.name:
        print("\nTu ne peux pas recruter dans un batiment qui ne t'appartient pas.")
        return

    if game.character.money < cost:
        print(f"\nIl te faut {cost} pieces d'or pour recruter.")
        return

    available_workers = [
        npc
        for npc in game.city.population
        if npc.employer_building_id is None and npc.job in ["Journalier", "Journaliere", "Oisif", "Oisive"]
    ]

    if not available_workers:
        print("\nPersonne n'est disponible a l'embauche pour le moment.")
        return

    choices = [
        {"label": f"{npc.name} - {npc.job}", "npc": npc}
        for npc in available_workers
    ]
    choices.append({"label": "Retour", "npc": None})

    selected = ask_choice("Qui veux-tu recruter ?", choices)

    if selected["npc"] is None:
        return

    recruited_npc = selected["npc"]
    game.character.money -= cost
    recruited_npc.job = f"Employe - {building.name}"
    recruited_npc.employer_building_id = building.building_id
    building.employees.append(recruited_npc.npc_id)

    print(f"\n{recruited_npc.name} travaille maintenant a {building.name}.")


def employee_menu(game, building):
    while True:
        print("\n=== Employes ===")
        print(f"Employes actuels : {employee_names(game, building)}")

        selected = ask_choice(
            "Gestion des employes :",
            [
                {"label": "Recruter un employe"},
                {"label": "Retour"},
            ],
        )

        if selected["label"] == "Recruter un employe":
            hire_employee(game, building)
        elif selected["label"] == "Retour":
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
        selected = ask_choice(
            f"{game.city.name} - Que veux-tu faire ?",
            [
                {"label": "Voir la ville"},
                {"label": "Voir la population"},
                {"label": "Entrer dans un batiment"},
                {"label": "Voir les batiments constructibles"},
                {"label": "Construire un batiment"},
                {"label": "Travailler en ville"},
                {"label": "Voir le personnage"},
                {"label": "Passer au jour suivant"},
                {"label": "Sauvegarder"},
                {"label": "Quitter"},
            ],
        )

        label = selected["label"]

        if label == "Voir la ville":
            show_city(game)
        elif label == "Voir la population":
            show_population(game)
        elif label == "Entrer dans un batiment":
            enter_building(game)
        elif label == "Voir les batiments constructibles":
            show_building_catalog(game)
        elif label == "Construire un batiment":
            construct_building(game)
        elif label == "Travailler en ville":
            work_in_town(game)
        elif label == "Voir le personnage":
            show_character_sheet(game)
        elif label == "Passer au jour suivant":
            end_day(game)
        elif label == "Sauvegarder":
            save_current_game(game)
        elif label == "Quitter":
            save_current_game(game)
            print("\nA bientot.")
            break
