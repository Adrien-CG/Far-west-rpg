import random
import tkinter as tk
from tkinter import ttk

from buildings import BUILDING_CATALOG, Building
from character import CHARACTER_QUESTIONS, Character, next_question_id
from game_state import create_new_game
from ids import make_building_id
from population import FEMALE_FIRST_NAMES, LAST_NAMES, MALE_FIRST_NAMES
from saves import (
    delete_save,
    get_save_display_name,
    list_game_saves,
    load_game,
    save_game,
)


class GameApp:
    """Interface Tkinter du jeu.

    Une seule fenetre est creee. Quand le joueur change d'endroit
    (menu, ville, batiment, gestion), on remplace simplement le contenu.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jeu Far West")
        self.root.geometry("940x600")

        self.game = None
        self.debug_mode = False
        self.current_frame = None
        self.profile_return_command = self.show_main_menu

        self.footer = tk.Frame(self.root)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8))
        self.character_label = tk.Label(self.footer, text="", anchor=tk.W)
        self.character_label.pack(side=tk.LEFT, padx=(0, 12))
        self.status_label = tk.Label(self.footer, text="", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.money_label = tk.Label(self.footer, text="")
        self.money_label.pack(side=tk.LEFT, padx=12)
        self.social_button = tk.Button(self.footer, text="Social", command=self.show_social)
        self.social_button.pack(side=tk.RIGHT, padx=(4, 0))
        self.profile_button = tk.Button(self.footer, text="Profil", command=self.show_profile)
        self.profile_button.pack(side=tk.RIGHT)
        self.menu_button = tk.Button(self.footer, text="Menu", command=self.show_game_menu)
        self.menu_button.pack(side=tk.RIGHT, padx=(0, 4))
        self.root.bind("<Escape>", self.open_game_menu_from_key)

        self.show_main_menu()

    def run(self):
        self.root.mainloop()

    def set_status(self, message):
        self.status_label.config(text=message)

    def set_screen(self, title):
        if self.current_frame:
            self.current_frame.destroy()

        self.root.title(title)
        self.update_footer()
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.current_frame = frame
        return frame

    def update_footer(self):
        if self.game:
            self.character_label.config(text=self.game.character.name)
            self.money_label.config(text=f"Dollars : {self.game.character.money}")
            self.profile_button.config(state=tk.NORMAL)
            self.social_button.config(state=tk.NORMAL)
            self.menu_button.config(state=tk.NORMAL)
        else:
            self.character_label.config(text="")
            self.money_label.config(text="")
            self.profile_button.config(state=tk.DISABLED)
            self.social_button.config(state=tk.DISABLED)
            self.menu_button.config(state=tk.DISABLED)

    def set_profile_return(self, command):
        self.profile_return_command = command

    def add_button(self, parent, label, command, width=28):
        button = tk.Button(parent, text=label, command=command, width=width)
        button.pack(fill=tk.X, pady=4)
        return button

    def add_back_button(self, frame, command):
        button = tk.Button(frame, text="Retour", command=command, width=16)
        button.place(relx=0.0, rely=1.0, anchor=tk.SW)
        return button

    def open_game_menu_from_key(self, event=None):
        if self.game:
            self.show_game_menu()

    def show_game_menu(self):
        if not self.game:
            return

        menu_window = tk.Toplevel(self.root)
        menu_window.title("Menu")
        menu_window.geometry("300x260")
        menu_window.transient(self.root)

        center = tk.Frame(menu_window)
        center.pack(expand=True, fill=tk.BOTH, padx=16, pady=16)
        tk.Label(center, text="Menu", font=("Arial", 16, "bold")).pack(pady=(0, 12))

        def close_then(command):
            menu_window.destroy()
            command()

        self.add_button(center, "Sauvegarder", self.save_current_game)
        self.add_button(center, "Parametres", lambda: close_then(self.show_settings))
        self.add_button(center, "Sauvegarder et quitter", lambda: close_then(self.save_and_quit_to_menu))
        self.add_button(center, "Retour", menu_window.destroy)

    # Menu principal -----------------------------------------------------

    def show_main_menu(self):
        frame = self.set_screen("Menu principal")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text="Menu principal", font=("Arial", 18, "bold")).pack(pady=(0, 16))
        self.add_button(center, "Nouvelle partie", self.show_map_selection)
        self.add_button(center, "Charger une partie", self.show_load_menu)
        self.add_button(center, "Parametres", self.show_settings)
        self.add_button(center, "Quitter", self.root.destroy)

    def show_map_selection(self):
        frame = self.set_screen("Nouvelle partie")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text="Vers ou voulez-vous migrer ?", font=("Arial", 16, "bold")).pack(pady=(0, 16))
        self.add_button(center, "Dust Creek", lambda: self.start_character_creation("Dust Creek"))
        self.add_back_button(frame, self.show_main_menu)

    def show_settings(self):
        frame = self.set_screen("Parametres")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text="Parametres", font=("Arial", 16, "bold")).pack(pady=(0, 12))
        debug_text = "Mode debug : actif" if self.debug_mode else "Mode debug : inactif"
        tk.Label(center, text=debug_text).pack(pady=8)
        self.add_button(center, "Activer / desactiver le debug", self.toggle_debug_mode)
        self.add_button(center, "Retour", self.profile_return_command if self.game else self.show_main_menu)

    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        self.set_status("Mode debug active." if self.debug_mode else "Mode debug desactive.")
        self.show_settings()

    # Chargement / suppression -----------------------------------------

    def show_load_menu(self):
        self.set_profile_return(self.show_load_menu)
        frame = self.set_screen("Charger une partie")
        tk.Label(frame, text="Charger une partie", font=("Arial", 16, "bold")).pack(anchor=tk.W)

        save_files = list_game_saves()
        if not save_files:
            tk.Label(frame, text="Aucune sauvegarde disponible.").pack(anchor=tk.W, pady=12)
            self.add_button(frame, "Retour", self.show_main_menu)
            return

        save_list = tk.Listbox(frame, height=14)
        save_list.pack(fill=tk.BOTH, expand=True, pady=10)
        for save_path in save_files:
            save_list.insert(tk.END, get_save_display_name(save_path))

        def selected_save_path():
            selection = save_list.curselection()
            if not selection:
                self.set_status("Selectionne une sauvegarde.")
                return None
            return save_files[selection[0]]

        def load_selection(event=None):
            save_path = selected_save_path()
            if save_path:
                self.load_selected_game(save_path)

        def delete_selection():
            save_path = selected_save_path()
            if save_path:
                self.show_delete_confirmation(save_path)

        save_list.bind("<Double-Button-1>", load_selection)

        actions = tk.Frame(frame)
        actions.pack(fill=tk.X, pady=(0, 4))
        tk.Button(actions, text="Charger", command=load_selection).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        tk.Button(actions, text="Supprimer", command=delete_selection).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Button(actions, text="Retour", command=self.show_main_menu).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

    def load_selected_game(self, save_path):
        try:
            self.game = load_game(save_path)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.set_status(f"Impossible de charger cette sauvegarde : {error}")
            return

        self.set_status(f"Partie chargee : {self.game.character.name}")
        self.show_city()

    def show_delete_confirmation(self, save_path):
        self.set_profile_return(lambda: self.show_delete_confirmation(save_path))
        display_name = get_save_display_name(save_path)
        frame = self.set_screen("Supprimer une sauvegarde")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text=f"Supprimer definitivement {display_name} ?", font=("Arial", 14, "bold")).pack(pady=12)
        self.add_button(center, "Non", self.show_load_menu)
        self.add_button(center, "Oui, supprimer", lambda: self.delete_selected_save(save_path))

    def delete_selected_save(self, save_path):
        delete_save(save_path)
        self.set_status("Sauvegarde supprimee.")
        self.show_load_menu()

    # Creation de personnage -------------------------------------------

    def start_character_creation(self, city_name):
        self.character_city_name = city_name
        self.character_data = {
            "origin": None,
            "strength": 4,
            "sociability": 4,
            "intelligence": 4,
            "money": 50,
            "skills": [],
        }
        self.answered_question_ids = set()
        self.show_title_question()

    def show_title_question(self):
        frame = self.set_screen("Creation de personnage")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text="Bonjour...", font=("Arial", 18, "bold")).pack(pady=(0, 12))
        tk.Label(center, text="Comment dois-je vous appeler ?").pack(pady=(0, 8))
        self.add_button(center, "Monsieur", lambda: self.choose_title("Monsieur", "Homme"))
        self.add_button(center, "Madame", lambda: self.choose_title("Madame", "Femme"))
        self.add_back_button(frame, self.show_map_selection)

    def choose_title(self, title, sex):
        self.character_title = title
        self.character_sex = sex
        self.show_first_name_question()

    def show_first_name_question(self):
        names = MALE_FIRST_NAMES if self.character_sex == "Homme" else FEMALE_FIRST_NAMES
        self.show_text_question(
            f"Bonjour {self.character_title} ?",
            lambda: random.choice(names),
            self.save_first_name,
            self.show_title_question,
        )

    def save_first_name(self, first_name):
        self.character_first_name = first_name
        self.show_last_name_question()

    def show_last_name_question(self):
        self.show_text_question(
            f"{self.character_first_name} comment ?",
            lambda: random.choice(LAST_NAMES),
            self.save_last_name,
            self.show_first_name_question,
        )

    def save_last_name(self, last_name):
        self.character_last_name = last_name
        self.show_age_question()

    def show_age_question(self):
        self.show_text_question("Age du personnage", lambda: "25", self.save_age, self.show_last_name_question)

    def save_age(self, age_text):
        if not age_text.isdigit() or not 12 <= int(age_text) <= 90:
            self.set_status("Entre un age entre 12 et 90.")
            self.show_age_question()
            return

        self.character_age = int(age_text)
        self.show_character_question(CHARACTER_QUESTIONS[0]["id"])

    def show_text_question(self, question, random_value, on_validate, on_back):
        frame = self.set_screen("Creation de personnage")
        center = tk.Frame(frame)
        center.pack(expand=True)

        default_value = random_value()
        tk.Label(center, text=question, font=("Arial", 15, "bold")).pack(pady=(0, 10))
        entry = tk.Entry(center, width=34)
        entry.insert(0, default_value)
        entry.pack(pady=6)
        entry.focus_set()

        def randomize():
            entry.delete(0, tk.END)
            entry.insert(0, random_value())

        def validate(event=None):
            value = entry.get().strip()
            if not value:
                self.set_status("Reponse obligatoire.")
                return
            on_validate(value)

        entry.bind("<Return>", validate)
        self.add_button(center, "Aleatoire", randomize)
        self.add_button(center, "Valider", validate)
        self.add_back_button(frame, on_back)

    def show_character_question(self, question_id):
        question_data = self.question_by_id(question_id)
        frame = self.set_screen("Creation de personnage")
        center = tk.Frame(frame)
        center.pack(expand=True, fill=tk.BOTH)

        tk.Label(center, text=question_data["question"], font=("Arial", 14, "bold"), wraplength=720).pack(pady=(0, 16))

        for answer in question_data["choices"]:
            self.add_button(
                center,
                answer["label"],
                lambda selected=answer, current_id=question_id: self.answer_character_question(current_id, selected),
                width=46,
            )
        self.add_back_button(frame, self.restart_character_questions)

    def restart_character_questions(self):
        self.character_data = {
            "origin": None,
            "strength": 4,
            "sociability": 4,
            "intelligence": 4,
            "money": 50,
            "skills": [],
        }
        self.answered_question_ids = set()
        self.show_age_question()

    def answer_character_question(self, question_id, selected):
        self.answered_question_ids.add(question_id)

        for stat_name, bonus in selected.get("stats", {}).items():
            self.character_data[stat_name] += bonus

        self.character_data["money"] += selected.get("money", 0)

        for skill in selected.get("skills", []):
            if skill not in self.character_data["skills"]:
                self.character_data["skills"].append(skill)

        if selected.get("origin"):
            self.character_data["origin"] = selected["origin"]

        next_id = next_question_id(question_id, selected, self.answered_question_ids)
        if next_id:
            self.show_character_question(next_id)
        else:
            self.finish_character_creation()

    def question_by_id(self, question_id):
        for question_data in CHARACTER_QUESTIONS:
            if question_data["id"] == question_id:
                return question_data
        raise ValueError(f"Question inconnue : {question_id}")

    def finish_character_creation(self):
        name = f"{self.character_first_name} {self.character_last_name}"
        strength = self.character_data["strength"]
        health = 80 + strength * 5
        character = Character(
            first_name=self.character_first_name,
            last_name=self.character_last_name,
            name=name,
            sex=self.character_sex,
            age=self.character_age,
            origin=self.character_data["origin"] or "Nouvel arrivant",
            strength=strength,
            sociability=self.character_data["sociability"],
            intelligence=self.character_data["intelligence"],
            health=health,
            max_health=health,
            income=0,
            money=self.character_data["money"],
            skills=self.character_data["skills"],
        )
        self.game = create_new_game(character, city_name=self.character_city_name)
        save_game(self.game)
        self.set_status(f"Personnage cree : {character.name}")
        self.show_city()

    # Ville --------------------------------------------------------------

    def show_city(self):
        self.set_profile_return(self.show_city)
        frame = self.set_screen(f"{self.game.city.name} - Vue ville")
        header = tk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(header, text=f"{self.game.city.name} - Jour {self.game.city.day}", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        population_count = len(self.game.city.population)
        total_income = sum(npc.income for npc in self.game.city.population)
        tk.Label(header, text=f"Population : {population_count} | Revenu global : {total_income}").pack(side=tk.RIGHT)

        body = tk.Frame(frame)
        body.pack(fill=tk.BOTH, expand=True)

        action_panel = tk.LabelFrame(body, text="Actions")
        action_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        building_panel = tk.LabelFrame(body, text="Batiments")
        building_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.city_actions = [
            ("Construire", self.show_construction),
        ]
        action_list = tk.Listbox(action_panel)
        action_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for label, _command in self.city_actions:
            action_list.insert(tk.END, label)
        action_list.bind("<Double-Button-1>", lambda _event: self.run_list_action(action_list, self.city_actions))

        building_list = tk.Listbox(building_panel)
        building_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for building in self.game.city.buildings:
            building_list.insert(tk.END, building_display_name(building))
        building_list.bind("<Double-Button-1>", lambda _event: self.enter_selected_building(building_list))

        self.add_button(action_panel, "Choisir", lambda: self.run_list_action(action_list, self.city_actions))
        self.add_button(building_panel, "Entrer", lambda: self.enter_selected_building(building_list))

    def run_list_action(self, listbox, actions):
        selection = listbox.curselection()
        if selection:
            _label, command = actions[selection[0]]
            command()

    def enter_selected_building(self, listbox):
        selection = listbox.curselection()
        if selection:
            self.show_building(self.game.city.buildings[selection[0]])

    def save_current_game(self):
        save_path = save_game(self.game)
        self.set_status(f"Partie sauvegardee : {save_path}")

    def save_and_quit_to_menu(self):
        self.save_current_game()
        self.game = None
        self.show_main_menu()

    # Profil joueur ------------------------------------------------------

    def show_profile(self):
        if not self.game:
            return

        frame = self.set_screen("Profil")
        character = self.game.character
        owned_buildings = [
            building.name
            for building in self.game.city.buildings
            if building.owner == character.name
        ]

        tk.Label(frame, text=character.name, font=("Arial", 18, "bold")).pack(anchor=tk.W, pady=(0, 10))
        tk.Label(
            frame,
            text="\n".join([
                f"Sexe : {character.sex}",
                f"Age : {character.age}",
                f"Origine : {character.origin}",
                f"Dollars : {character.money}",
                f"Revenu : {character.income}",
                "",
                describe_character(character),
                describe_health(character),
            ]),
            justify=tk.LEFT,
            anchor=tk.W,
        ).pack(anchor=tk.W)

        columns = tk.Frame(frame)
        columns.pack(fill=tk.BOTH, expand=True, pady=14)

        self.profile_list(columns, "Inventaire", format_dict(character.inventory))
        self.profile_list(columns, "Competences", character.skills)
        self.profile_list(columns, "Proprietes", owned_buildings)
        self.profile_list(columns, "Relations", ["Alliance : aucune", "Mariage : aucun", "Enfants : aucun"])
        if self.debug_mode:
            self.profile_list(
                columns,
                "Debug",
                [
                    f"Physique : {character.strength}",
                    f"Social : {character.sociability}",
                    f"Intelligence : {character.intelligence}",
                    f"Sante : {character.health}/{character.max_health}",
                ],
            )

        self.add_button(frame, "Retour", self.profile_return_command)

    def profile_list(self, parent, title, values):
        panel = tk.LabelFrame(parent, text=title)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        if not values:
            values = ["Aucun"]
        for value in values:
            tk.Label(panel, text=f"- {value}", anchor=tk.W, justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=2)

    # Social -------------------------------------------------------------

    def show_social(self):
        if not self.game:
            return

        frame = self.set_screen("Social")
        tk.Label(frame, text="Personnages importants", font=("Arial", 18, "bold")).pack(anchor=tk.W, pady=(0, 12))

        important_npcs = [npc for npc in self.game.city.population if npc.notable]
        if not important_npcs:
            tk.Label(frame, text="Aucun personnage important connu.").pack(anchor=tk.W)
        else:
            for npc in important_npcs:
                tk.Label(
                    frame,
                    text=f"{npc.name} - {npc.job}",
                    anchor=tk.W,
                    font=("Arial", 11, "bold"),
                ).pack(fill=tk.X, pady=(4, 0))
                tk.Label(
                    frame,
                    text=f"Origine : {npc.origin} | Dollars : {npc.money}",
                    anchor=tk.W,
                ).pack(fill=tk.X)

        self.add_button(frame, "Retour", self.profile_return_command)

    # Batiments ----------------------------------------------------------

    def show_building(self, building):
        self.set_profile_return(lambda: self.show_building(building))
        frame = self.set_screen(building.name)
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text=building.name, font=("Arial", 18, "bold")).pack(pady=(0, 8))
        tk.Label(center, text=f"Type : {building.building_type}", font=("Arial", 11)).pack()
        tk.Label(center, text=f"Proprietaire : {building.owner}", font=("Arial", 11)).pack(pady=(0, 18))
        if building.building_type == "Bureau du sherif":
            sheriff = self.find_sheriff()
            if sheriff:
                tk.Label(center, text=f"Sherif : {sheriff.name}", font=("Arial", 11, "bold")).pack(pady=(0, 18))
        visible_assets = building_assets(building)
        if building.building_type == "Ranch":
            tk.Label(center, text=f"Acres de terre : {building.production.get('acres', 160)}", font=("Arial", 11)).pack(pady=(0, 6))
            tk.Label(center, text=f"Terre {land_quality_phrase(building)}", font=("Arial", 11)).pack(pady=(0, 8))
        if visible_assets:
            tk.Label(center, text=", ".join(visible_assets), wraplength=520).pack(pady=(0, 10))
        if self.debug_mode:
            tk.Label(
                center,
                text=debug_building_text(building),
                justify=tk.LEFT,
                wraplength=620,
                fg="#6b1f1f",
            ).pack(pady=(0, 12))

        for label, command in self.available_building_actions(building):
            self.add_button(center, label, command, width=34)
        self.add_button(center, "Sortir", self.show_city, width=34)

    def find_sheriff(self):
        for npc in self.game.city.population:
            if npc.job == "Sherif":
                return npc
        return None

    def available_building_actions(self, building):
        if building.building_type == "Saloon":
            actions = self.saloon_actions(building)
        elif building.building_type == "Ranch":
            actions = self.ranch_actions(building)
        elif building.building_type == "General Store":
            actions = [("Acheter / Vendre", lambda: self.show_trade(building))]
        elif building.building_type == "Bureau du sherif":
            actions = [
                ("Regarder les primes", lambda: self.set_status("Aucune prime disponible pour le moment.")),
                ("Candidater pour le bureau du sherif", lambda: self.set_status("Candidature enregistree pour plus tard.")),
            ]
        elif building.building_type == "Post Office":
            actions = [("Poster une annonce pour un emploi", lambda: self.set_status("Annonce d'emploi postee pour plus tard."))]
        else:
            actions = []

        if self.is_player_owner(building) and building.building_type in ["Saloon", "Ranch"]:
            actions.append(("Gestion", lambda: self.show_management(building)))

        return actions

    def saloon_actions(self, building):
        actions = []
        if building.inventory.get("biere", 0) > 0:
            actions.append(("Boire une biere", lambda: self.drink_beer(building)))
        if building.features.get("table_poker"):
            actions.append(("Faire une partie de poker", lambda: self.pay_for_service(building, 10, "La vraie partie de poker sera ajoutee plus tard.")))
        if "Chambres d'hotel" in building.upgrades or "Salle de bain" in building.upgrades:
            actions.append(("Appeler une hotesse", lambda: self.pay_for_service(building, building.production.get("prix_hotesse", 10), "Une hotesse vient tenir compagnie au joueur.")))
        if "Salle de bain" in building.upgrades:
            actions.append(("Prendre un bain", lambda: self.pay_for_service(building, building.production.get("prix_bain", 3), "Un bain chaud remet les idees en place.")))
        if "Cuisine" in building.upgrades:
            actions.append(("Commander un repas", lambda: self.pay_for_service(building, building.production.get("prix_repas", 5), "Le repas est servi.")))

        if self.is_player_owner(building):
            actions.append(("Tenir le bar", lambda: self.work_for_turn("Tu prends le service derriere le bar pour ce tour.")))
            if "Cuisine" in building.upgrades:
                actions.append(("Preparer a manger", lambda: self.work_for_turn("Tu prepares les repas pour ce tour.")))
        return actions

    def ranch_actions(self, building):
        if self.is_player_owner(building):
            return [
                ("Surveiller le troupeau", lambda: self.set_player_task(building, "Surveiller le troupeau")),
                ("Accompagner le troupeau", lambda: self.set_player_task(building, "Accompagner le troupeau")),
                ("Planter des piquets", lambda: self.set_player_task(building, "Planter des piquets")),
            ]
        return [("Travailler en tant que journalier", lambda: self.work_for_turn("Tu te proposes comme journalier pour ce tour."))]

    def is_player_owner(self, building):
        return building.owner == self.game.character.name

    def spend(self, amount):
        if self.game.character.money < amount:
            self.set_status("Tu n'as pas assez d'argent.")
            return False
        self.game.character.money -= amount
        return True

    def drink_beer(self, building):
        price = building.production.get("prix_biere", 2)
        if not self.spend(price):
            return
        building.inventory["biere"] = max(0, building.inventory.get("biere", 0) - 1)
        building.current_balance += price
        self.set_status("Tu bois une biere.")
        self.show_building(building)

    def pay_for_service(self, building, price, message):
        if not self.spend(price):
            return
        building.current_balance += price
        self.set_status(message)
        self.show_building(building)

    def work_for_turn(self, message):
        self.game.character.income += 1
        self.set_status(message)

    def set_player_task(self, building, task):
        building.employee_tasks["player"] = task
        self.set_status(f"Tache du joueur : {task}")
        self.show_building(building)

    # General Store ------------------------------------------------------

    def show_trade(self, building):
        self.set_profile_return(lambda: self.show_trade(building))
        frame = self.set_screen("General Store - Acheter / Vendre")
        left = tk.LabelFrame(frame, text="Acheter")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right = tk.LabelFrame(frame, text="Vendre")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for item, price in BUY_PRICES.items():
            self.add_button(left, f"Acheter {item} - {price} or", lambda selected=item: self.buy_item(building, selected))
        for item, price in SELL_PRICES.items():
            self.add_button(right, f"Vendre {item} - {price} or", lambda selected=item: self.sell_item(building, selected))

        info = tk.Label(frame, text=f"Inventaire joueur : {format_items(self.game.character.inventory)}", justify=tk.LEFT)
        info.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        self.add_button(frame, "Retour", lambda: self.show_building(building))

    def buy_item(self, building, item):
        price = BUY_PRICES[item]
        if not self.spend(price):
            return
        self.game.character.inventory[item] = self.game.character.inventory.get(item, 0) + 1
        building.current_balance += price
        self.set_status(f"Achat : {item}.")
        self.show_trade(building)

    def sell_item(self, building, item):
        if self.game.character.inventory.get(item, 0) <= 0:
            self.set_status("Tu n'as pas cet objet.")
            return
        price = SELL_PRICES[item]
        self.game.character.inventory[item] -= 1
        if self.game.character.inventory[item] == 0:
            del self.game.character.inventory[item]
        self.game.character.money += price
        building.current_balance -= price
        self.set_status(f"Vente : {item}.")
        self.show_trade(building)

    def can_afford_orders(self, orders):
        total_cost = sum(quantity * price for quantity, price in orders)
        if self.game.character.money < total_cost:
            self.set_status(f"Il faut {total_cost} dollars pour cet achat.")
            return False
        return True

    # Gestion ------------------------------------------------------------

    def show_management(self, building):
        self.set_profile_return(lambda: self.show_management(building))
        frame = self.set_screen(f"Gestion - {building.name}")
        left = tk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        right = tk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(left, text=f"Gestion\n{building.name}", font=("Arial", 13, "bold")).pack(pady=(0, 10))
        self.add_button(left, "Comptabilite", lambda: self.show_accounting(building))
        self.add_button(left, "Production", lambda: self.show_production(building))
        self.add_button(left, "Employes", lambda: self.show_employees(building))
        self.add_button(left, "Developpement", lambda: self.show_upgrades(building))
        self.add_button(left, "Retour", lambda: self.show_building(building))

        tk.Label(right, text=self.accounting_text(building), justify=tk.LEFT, anchor=tk.NW).pack(fill=tk.BOTH, expand=True)

    def show_accounting(self, building):
        self.show_text_panel(f"Comptabilite - {building.name}", self.accounting_text(building), lambda: self.show_management(building))

    def accounting_text(self, building):
        return "\n".join([
            "Comptabilite en cours de creation.",
            "",
            f"Solde actuel : {building.current_balance}",
            f"Resultat actuel : {building.current_result}",
            f"Journal : {building.account_journal or 'Aucune entree'}",
        ])

    def show_employees(self, building):
        self.set_profile_return(lambda: self.show_employees(building))
        frame = self.set_screen(f"Employes - {building.name}")
        tk.Label(frame, text=f"Employes - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        lines = []
        for employee_id in building.employees:
            npc = self.game.city.get_npc_by_id(employee_id)
            role = building.employee_roles.get(employee_id, "Employe")
            lines.append(f"- {npc.name if npc else employee_id} | {role} | Salaire base : {employee_salary(role)}")
        if not lines:
            lines.append("Aucun employe.")
        tk.Label(frame, text="\n".join(lines), justify=tk.LEFT, anchor=tk.NW).pack(anchor=tk.W, fill=tk.X)

        fire_panel = tk.LabelFrame(frame, text="Renvoyer")
        fire_panel.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        if not building.employees:
            tk.Label(fire_panel, text="Aucun employe a renvoyer.").pack(anchor=tk.W, padx=8, pady=8)
        else:
            employee_list = tk.Listbox(fire_panel, height=5)
            employee_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            for employee_id in building.employees:
                npc = self.game.city.get_npc_by_id(employee_id)
                role = building.employee_roles.get(employee_id, "Employe")
                employee_list.insert(tk.END, f"{npc.name if npc else employee_id} - {role}")
            self.add_button(fire_panel, "Renvoyer", lambda: self.fire_employee(building, employee_list))

        recruit_panel = tk.LabelFrame(frame, text="Recruter")
        recruit_panel.pack(fill=tk.BOTH, expand=True, pady=12)

        available_npcs = available_workers(self.game.city.population)
        if not available_npcs:
            tk.Label(recruit_panel, text="Aucun candidat disponible.").pack(anchor=tk.W, padx=8, pady=8)
        else:
            candidate_list = tk.Listbox(recruit_panel, height=7)
            candidate_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            for npc in available_npcs:
                candidate_list.insert(tk.END, f"{npc.name} - {npc.job}")

            roles = recruitable_roles(building)
            role_frame = tk.Frame(recruit_panel)
            role_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
            added_role_button = False
            for role in roles:
                if can_recruit_role(building, role):
                    tk.Button(
                        role_frame,
                        text=f"Recruter comme {role}",
                        command=lambda selected_role=role: self.recruit_employee(building, candidate_list, available_npcs, selected_role),
                    ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
                    added_role_button = True
            if not added_role_button:
                tk.Label(role_frame, text="Tous les postes disponibles sont deja pourvus.").pack(anchor=tk.W)

        self.add_button(frame, "Retour", lambda: self.show_management(building))

    def recruit_employee(self, building, candidate_list, available_npcs, role):
        selection = candidate_list.curselection()
        if not selection:
            self.set_status("Selectionne un candidat.")
            return

        npc = available_npcs[selection[0]]
        if not can_npc_take_role(npc, role):
            self.set_status("Ce poste ne correspond pas a ce candidat.")
            return
        if not can_recruit_role(building, role):
            self.set_status("Ce poste est deja au complet.")
            self.show_employees(building)
            return

        building.employees.append(npc.npc_id)
        building.employee_roles[npc.npc_id] = role
        npc.job = role
        npc.employer_building_id = building.building_id
        npc.income = employee_salary(role)
        self.set_status(f"{npc.name} recrute comme {role}.")
        self.show_employees(building)

    def fire_employee(self, building, employee_list):
        selection = employee_list.curselection()
        if not selection:
            self.set_status("Selectionne un employe.")
            return

        employee_id = building.employees.pop(selection[0])
        npc = self.game.city.get_npc_by_id(employee_id)
        building.employee_roles.pop(employee_id, None)
        building.employee_tasks.pop(employee_id, None)
        if npc:
            npc.job = "Journalier" if npc.sex == "Homme" else "Journaliere"
            npc.employer_building_id = None
            npc.income = 0
            self.set_status(f"{npc.name} a ete renvoye.")
        else:
            self.set_status("Employe renvoye.")
        self.show_employees(building)

    def show_text_panel(self, title, text, back_command):
        self.set_profile_return(lambda: self.show_text_panel(title, text, back_command))
        frame = self.set_screen(title)
        tk.Label(frame, text=title, font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        tk.Label(frame, text=text, justify=tk.LEFT, anchor=tk.NW).pack(fill=tk.BOTH, expand=True)
        self.add_button(frame, "Retour", back_command)

    def show_production(self, building):
        self.set_profile_return(lambda: self.show_production(building))
        frame = self.set_screen(f"Production - {building.name}")
        tk.Label(frame, text=f"Production - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        entries = {}
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        stock_tab = tk.Frame(notebook)
        sell_tab = tk.Frame(notebook)
        buy_tab = tk.Frame(notebook)
        notebook.add(stock_tab, text="Stock")
        notebook.add(sell_tab, text="Vente / Prix")
        notebook.add(buy_tab, text="Achat")

        for label, value in production_stock_lines(building):
            row = tk.Frame(stock_tab)
            row.pack(fill=tk.X, pady=3, padx=8)
            tk.Label(row, text=label, width=34, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(value), anchor=tk.W).pack(side=tk.LEFT)

        for key, label in production_sell_fields(building):
            row = tk.Frame(sell_tab)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, width=34, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row)
            entry.insert(0, str(building.production.get(key, 0)))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[key] = entry

        for key, label, price in production_buy_fields(building):
            row = tk.Frame(buy_tab)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label} ({price} dollars piece)", width=34, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row)
            entry.insert(0, str(building.production.get(key, 0)))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[key] = entry

        if building.building_type == "Ranch":
            tk.Label(frame, text="Les prix du betail sont fixes au niveau national pour l'instant.").pack(anchor=tk.W, pady=6)

        self.add_button(frame, "Valider", lambda: self.save_production(building, entries))
        self.add_button(frame, "Retour", lambda: self.show_management(building))

    def save_production(self, building, entries):
        new_values = {
            key: safe_int(entry.get())
            for key, entry in entries.items()
        }
        if not self.production_orders_are_valid(building, new_values):
            return

        for key, entry in entries.items():
            building.production[key] = new_values[key]
        self.set_status("Production enregistree.")
        self.show_management(building)

    def production_orders_are_valid(self, building, values):
        if building.building_type == "Saloon":
            orders = [
                (values.get("commande_biere", 0), NATIONAL_PRICES["biere"]),
                (values.get("commande_cereales", 0), NATIONAL_PRICES["cereales"]),
                (values.get("commande_viande", 0), NATIONAL_PRICES["viande"]),
            ]
            return self.can_afford_orders(orders)

        sale_limits = {
            "vente_taureaux": building.production.get("taureaux", 0),
            "vente_genisses": building.production.get("genisses", 0),
            "vente_veaux": building.production.get("veaux", 0),
            "vente_vaches_matures": mature_cattle_count(building),
        }
        for key, limit in sale_limits.items():
            if values.get(key, 0) > limit:
                self.set_status("Impossible de vendre plus de betail que le stock disponible.")
                return False

        orders = [
            (values.get("achat_taureaux", 0), NATIONAL_PRICES["taureau"]),
            (values.get("achat_genisses", 0), NATIONAL_PRICES["genisse"]),
            (values.get("achat_fourrage", 0), NATIONAL_PRICES["fourrage"]),
        ]
        return self.can_afford_orders(orders)

    def show_upgrades(self, building):
        if building.building_type == "Saloon":
            self.show_saloon_upgrades(building)
        elif building.building_type == "Ranch":
            self.show_ranch_upgrades(building)

    def show_saloon_upgrades(self, building):
        self.set_profile_return(lambda: self.show_saloon_upgrades(building))
        frame = self.set_screen(f"Developpement - {building.name}")
        tk.Label(frame, text=f"Developpement - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        added_any = False
        for upgrade, cost, limit in SALOON_LIMITED_UPGRADES:
            owned_count = building.upgrades.count(upgrade)
            if owned_count < limit and saloon_major_upgrade_count(building) < SALOON_MAJOR_UPGRADE_LIMIT:
                label = f"{upgrade} - {cost} or"
                if limit > 1:
                    label = f"{upgrade} ({owned_count}/{limit}) - {cost} or"
                self.add_button(frame, label, lambda u=upgrade, c=cost: self.add_saloon_limited_upgrade(building, u, c))
                added_any = True
        for key, label, cost in SALOON_EXTRA_FEATURES:
            if not building.features.get(key):
                self.add_button(frame, f"{label} - {cost} or", lambda k=key, l=label, c=cost: self.add_feature(building, k, l, c))
                added_any = True
        if not added_any:
            tk.Label(frame, text="Aucun developpement disponible pour le moment.").pack(anchor=tk.W, pady=8)
        self.add_button(frame, "Retour", lambda: self.show_management(building))

    def add_saloon_limited_upgrade(self, building, upgrade, cost):
        upgrade_limit = saloon_upgrade_limit(upgrade)
        if building.upgrades.count(upgrade) >= upgrade_limit:
            self.set_status("Developpement deja au maximum.")
            return
        if saloon_major_upgrade_count(building) >= SALOON_MAJOR_UPGRADE_LIMIT:
            self.set_status("Le Saloon ne peut avoir que deux grandes ameliorations.")
            return
        self.add_upgrade(building, upgrade, cost, allow_duplicate=True)
        self.show_saloon_upgrades(building)

    def show_ranch_upgrades(self, building):
        self.set_profile_return(lambda: self.show_ranch_upgrades(building))
        frame = self.set_screen(f"Developpement - {building.name}")
        tk.Label(frame, text=f"Developpement - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        added_any = False
        for upgrade, cost, repeatable in RANCH_UPGRADES:
            if repeatable or upgrade not in building.upgrades:
                label = f"{upgrade} - {cost} or"
                if repeatable:
                    label = f"{upgrade} x{building.upgrades.count(upgrade) + 1} - {cost} or"
                self.add_button(frame, label, lambda u=upgrade, c=cost: self.add_ranch_upgrade(building, u, c))
                added_any = True
        if not added_any:
            tk.Label(frame, text="Aucun developpement disponible pour le moment.").pack(anchor=tk.W, pady=8)
        self.add_button(frame, "Retour", lambda: self.show_management(building))

    def add_ranch_upgrade(self, building, upgrade, cost):
        self.add_upgrade(building, upgrade, cost, allow_duplicate=upgrade == "Baraquements")
        if upgrade == "Systeme d'irrigation":
            building.hidden_stats["qualite_terre"] = "bonne et irriguee"
        self.show_ranch_upgrades(building)

    def add_upgrade(self, building, upgrade, cost, allow_duplicate=False):
        if upgrade in building.upgrades and not allow_duplicate:
            self.set_status("Developpement deja present.")
            return
        if not self.spend(cost):
            return
        building.upgrades.append(upgrade)
        building.account_journal.append(f"Developpement : {upgrade} (-{cost})")
        self.set_status(f"Developpement ajoute : {upgrade}.")

    def add_feature(self, building, key, label, cost):
        if building.features.get(key):
            self.set_status("Developpement deja present.")
            return
        if not self.spend(cost):
            return
        building.features[key] = True
        building.account_journal.append(f"Developpement : {label} (-{cost})")
        self.set_status(f"Developpement ajoute : {label}.")
        self.show_saloon_upgrades(building)

    # Construction -------------------------------------------------------

    def show_construction(self):
        self.set_profile_return(self.show_construction)
        frame = self.set_screen("Construire")
        tk.Label(frame, text="Construire", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        for building_type, data in BUILDING_CATALOG.items():
            self.add_button(
                frame,
                f"{building_type} - {data['base_cost']} or",
                lambda selected_type=building_type: self.show_construct_name(selected_type),
            )
        self.add_button(frame, "Retour", self.show_city)

    def show_construct_name(self, building_type):
        self.set_profile_return(lambda: self.show_construct_name(building_type))
        data = BUILDING_CATALOG[building_type]
        if self.game.character.money < data["base_cost"]:
            self.set_status("Tu n'as pas assez d'argent.")
            return

        frame = self.set_screen(f"Construire {building_type}")
        tk.Label(frame, text="Nom du batiment", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        entry = tk.Entry(frame)
        entry.insert(0, random_building_name(building_type))
        entry.pack(fill=tk.X, pady=8)
        self.add_button(frame, "Nom aleatoire", lambda: replace_entry_text(entry, random_building_name(building_type)))
        self.add_button(frame, "Valider", lambda: self.construct_building(building_type, entry.get().strip() or building_type))
        self.add_button(frame, "Retour", self.show_construction)

    def construct_building(self, building_type, building_name):
        data = BUILDING_CATALOG[building_type]
        if not self.spend(data["base_cost"]):
            return

        existing_ids = {building.building_id for building in self.game.city.buildings}
        self.game.city.buildings.append(
            Building(
                building_id=make_building_id(building_type, existing_ids),
                name=building_name,
                building_type=building_type,
                owner=self.game.character.name,
                level=1,
                features=data.get("features", {}).copy(),
                inventory=data.get("inventory", {}).copy(),
                production=data.get("production", {}).copy(),
                hidden_stats=data.get("hidden_stats", {}).copy(),
                upgrades=data.get("upgrades", []).copy(),
            )
        )
        self.set_status(f"Construction terminee : {building_name}.")
        self.show_city()


BUY_PRICES = {"arme": 45, "cereales": 5, "viande": 8}
SELL_PRICES = {"cereales": 3, "viande": 5}
NATIONAL_PRICES = {
    "taureau": 30,
    "genisse": 22,
    "veau": 12,
    "vache_mature": 28,
    "biere": 2,
    "cereales": 5,
    "viande": 8,
    "fourrage": 4,
}

SALOON_LIMITED_UPGRADES = [
    ("Chambres d'hotel", 80, 2),
    ("Cuisine", 60, 1),
    ("Salle de bain", 50, 1),
]
SALOON_MAJOR_UPGRADE_LIMIT = 2

SALOON_EXTRA_FEATURES = [
    ("table_poker", "Table de poker", 40),
    ("piano", "Piano", 45),
]

RANCH_UPGRADES = [
    ("Grange", 70, False),
    ("Systeme d'irrigation", 60, False),
    ("Baraquements", 90, True),
]

BUILDING_NAME_PARTS = {
    "Ranch": ["Ranch", "Domaine", "Elevage"],
    "Saloon": ["Saloon", "Taverne", "Maison"],
}

BUILDING_NAME_SUFFIXES = [
    "du Coyote",
    "de la Poussiere Rouge",
    "du Dernier Verre",
    "des Trois Collines",
    "du Vieux Puits",
    "Dawson",
    "McCoy",
    "Blackwood",
]


def employee_salary(role):
    salaries = {
        "Barman": 6,
        "Cuisinier": 6,
        "Hotesse": 5,
        "Musicien": 5,
        "Cowboy": 7,
        "Contremaitre": 11,
    }
    return salaries.get(role, 5)


def building_display_name(building):
    if building.building_type.lower() in building.name.lower():
        return building.name
    return f"{building.name} ({building.building_type})"


def debug_building_text(building):
    return "\n".join([
        "Debug",
        f"Stocks : {building.inventory}",
        f"Production : {building.production}",
        f"Caracteristiques cachees : {building.hidden_stats}",
        f"Solde : {building.current_balance}",
        f"Resultat : {building.current_result}",
    ])


def building_assets(building):
    assets = list(building.upgrades)
    for key, label, _cost in SALOON_EXTRA_FEATURES:
        if building.features.get(key):
            assets.append(label)
    return compact_counted_names(assets)


def compact_counted_names(values):
    result = []
    for value in dict.fromkeys(values):
        count = values.count(value)
        result.append(f"{value} x{count}" if count > 1 else value)
    return result


def production_stock_lines(building):
    if building.building_type == "Saloon":
        return [
            ("Biere", building.inventory.get("biere", 0)),
            ("Cereales", building.inventory.get("cereales", 0)),
            ("Viande", building.inventory.get("viande", 0)),
        ]

    return [
        ("Taureaux", building.production.get("taureaux", 0)),
        ("Genisses", building.production.get("genisses", 0)),
        ("Veaux", building.production.get("veaux", 0)),
        ("Vaches matures", mature_cattle_count(building)),
        ("Fourrage", building.inventory.get("fourrage", 0)),
    ]


def production_sell_fields(building):
    if building.building_type == "Saloon":
        return [
            ("prix_biere", "Prix de vente de la biere"),
            ("prix_repas", "Prix des repas"),
            ("prix_hotesse", "Prix de l'hotesse"),
            ("prix_bain", "Prix du bain"),
        ]

    return [
        ("vente_taureaux", "Taureaux a vendre"),
        ("vente_genisses", "Genisses a vendre"),
        ("vente_veaux", "Veaux a vendre"),
        ("vente_vaches_matures", "Vaches matures a vendre"),
    ]


def production_buy_fields(building):
    if building.building_type == "Saloon":
        return [
            ("commande_biere", "Biere a commander", NATIONAL_PRICES["biere"]),
            ("commande_cereales", "Cereales a commander", NATIONAL_PRICES["cereales"]),
            ("commande_viande", "Viande a commander", NATIONAL_PRICES["viande"]),
        ]

    return [
        ("achat_taureaux", "Taureaux a acheter", NATIONAL_PRICES["taureau"]),
        ("achat_genisses", "Genisses a acheter", NATIONAL_PRICES["genisse"]),
        ("achat_fourrage", "Fourrage a acheter", NATIONAL_PRICES["fourrage"]),
    ]


def mature_cattle_count(building):
    return building.production.get("vaches_matures", building.production.get("betes_matures", 0))


def available_workers(population):
    available_jobs = {"Journalier", "Journaliere", "Chomeur", "Chomeuse", "Oisif", "Oisive"}
    return [
        npc for npc in population
        if npc.employer_building_id is None and npc.job in available_jobs
    ]


def recruitable_roles(building):
    if building.building_type == "Saloon":
        roles = ["Barman"]
        if "Cuisine" in building.upgrades:
            roles.append("Cuisinier")
        if building.upgrades.count("Chambres d'hotel") > 0:
            roles.append("Hotesse")
        if building.features.get("piano"):
            roles.append("Musicien")
        return roles

    if building.building_type == "Ranch":
        return ["Cowboy", "Contremaitre"]

    return []


def can_recruit_role(building, role):
    return role_count(building, role) < role_limit(building, role)


def can_npc_take_role(npc, role):
    if role == "Hotesse":
        return npc.sex == "Femme"
    return True


def role_count(building, role):
    return len([
        employee_id for employee_id in building.employees
        if building.employee_roles.get(employee_id) == role
    ])


def role_limit(building, role):
    if building.building_type == "Saloon":
        limits = {"Barman": 1, "Cuisinier": 1, "Hotesse": building.upgrades.count("Chambres d'hotel"), "Musicien": 1}
        return limits.get(role, 0)

    if building.building_type == "Ranch":
        if role == "Contremaitre":
            return 1
        if role == "Cowboy":
            housing_count = building.upgrades.count("Baraquements") + building.upgrades.count("Logements employes")
            return max(2, housing_count * 2)

    return 0


def saloon_major_upgrade_count(building):
    limited_names = [name for name, _cost, _limit in SALOON_LIMITED_UPGRADES]
    return len([upgrade for upgrade in building.upgrades if upgrade in limited_names])


def saloon_upgrade_limit(upgrade):
    for name, _cost, limit in SALOON_LIMITED_UPGRADES:
        if name == upgrade:
            return limit
    return 1


def land_quality_phrase(building):
    quality = building.hidden_stats.get("qualite_terre", "semi-aride")
    if "Systeme d'irrigation" in building.upgrades:
        return "bonne et irriguee"
    return quality


def random_building_name(building_type):
    starts = BUILDING_NAME_PARTS.get(building_type, [building_type])
    return f"{random.choice(starts)} {random.choice(BUILDING_NAME_SUFFIXES)}"


def replace_entry_text(entry, value):
    entry.delete(0, tk.END)
    entry.insert(0, value)


def safe_int(value):
    try:
        return max(0, int(value))
    except ValueError:
        return 0


def format_dict(values):
    if not values:
        return []
    return [
        f"{key} : {value}"
        for key, value in values.items()
    ]


def format_items(values):
    items = format_dict(values)
    return ", ".join(items) if items else "vide"


def describe_character(character):
    physical = character.strength
    social = character.sociability
    mind = character.intelligence

    parts = []
    if physical >= 7:
        parts.append("une carrure qui impose le respect")
    elif physical >= 5:
        parts.append("assez solide pour tenir sa place")
    else:
        parts.append("pas un grand gaillard")

    if social >= 7:
        parts.append("une langue bien pendue")
    elif social >= 5:
        parts.append("un contact facile")
    else:
        parts.append("plutot discret")

    if mind >= 7:
        parts.append("un cerveau bien fait")
    elif mind >= 5:
        parts.append("un esprit correct")
    else:
        parts.append("pas toujours porte sur les grands calculs")

    return "Vous avez " + ", ".join(parts) + "."


def describe_health(character):
    if character.health <= character.max_health * 0.25:
        return "Etat : sur son lit de mort."
    if character.health <= character.max_health * 0.6:
        return "Etat : blesse."
    return "Etat : en forme."


def launch_app():
    app = GameApp()
    app.run()


def city_menu(game):
    app = GameApp()
    app.game = game
    app.show_city()
    app.run()
