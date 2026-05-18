from character import ask_choice, create_character
from city_actions import city_menu
from game_state import create_new_game
from saves import delete_save, get_save_display_name, list_game_saves, load_game, save_game


def start_new_game():
    selected_map = ask_choice(
        "Vers ou voulez-vous migrer ?",
        [
            {"label": "Dust Creek", "city_name": "Dust Creek"},
        ],
    )

    print("=== Creation de personnage ===")
    character = create_character()
    game = create_new_game(character, city_name=selected_map["city_name"])
    save_path = save_game(game)

    print("\nPersonnage cree avec succes !")
    print(f"Sauvegarde : {save_path}")

    city_menu(game)


def load_saved_game():
    save_files = list_game_saves()

    if not save_files:
        print("\nAucune sauvegarde disponible.")
        return

    choices = [
        {"label": get_save_display_name(save_path), "save_path": save_path}
        for save_path in save_files
    ]
    choices.append({"label": "Retour", "save_path": None})
    selected = ask_choice("Quelle partie veux-tu charger ?", choices)

    if selected["save_path"] is None:
        return

    selected_save_menu(selected["save_path"])


def selected_save_menu(save_path):
    display_name = get_save_display_name(save_path)
    selected = ask_choice(
        f"Que veux-tu faire avec {display_name} ?",
        [
            {"label": "Charger"},
            {"label": "Supprimer"},
            {"label": "Retour"},
        ],
    )

    if selected["label"] == "Charger":
        try:
            game = load_game(save_path)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"\nImpossible de charger cette sauvegarde : {error}")
            return

        print(f"\nPartie chargee : {display_name}")
        city_menu(game)
    elif selected["label"] == "Supprimer":
        confirmation = ask_choice(
            f"Supprimer definitivement {display_name} ?",
            [
                {"label": "Non"},
                {"label": "Oui"},
            ],
        )

        if confirmation["label"] == "Oui":
            delete_save(save_path)
            print("\nSauvegarde supprimee.")


def show_settings():
    print("\n=== Parametres ===")
    print("Aucun parametre disponible pour le moment.")


def main():
    while True:
        selected = ask_choice(
            "Menu principal",
            [
                {"label": "Nouvelle partie"},
                {"label": "Charger une partie"},
                {"label": "Parametres"},
                {"label": "Quitter"},
            ],
        )

        if selected["label"] == "Nouvelle partie":
            start_new_game()
        elif selected["label"] == "Charger une partie":
            load_saved_game()
        elif selected["label"] == "Parametres":
            show_settings()
        elif selected["label"] == "Quitter":
            print("\nA bientot.")
            break


if __name__ == "__main__":
    main()
