import ast
import math
import random
import tkinter as tk
import traceback
from copy import deepcopy
from pprint import pformat
from tkinter import messagebox, simpledialog, ttk

from turn_system import run_end_turn
from accounting import (
    accounting_balance_asset_lines,
    accounting_balance_errors,
    accounting_balance_liability_lines,
    accounting_capital_contribution,
    accounting_current_year_lines,
    accounting_display_line,
    accounting_pay_dividends,
    accounting_remove_capital,
    close_annual_accounting,
    close_season_accounting,
    current_stock_values,
    ensure_building_accounting,
    prorate_cattle_sale_split,
    record_accounting_charge,
    record_accounting_product,
    reduce_ranch_cattle_stock,
    restore_ranch_cattle_stock,
    result_result_lines,
    result_total,
    snapshot_asset_lines,
    snapshot_liability_lines,
    split_ranch_cattle_sale,
    split_result_lines,
)
from achievements import ACHIEVEMENTS
from buildings import (
    BUILDING_CATALOG,
    Building,
    available_workers,
    can_npc_take_role,
    can_player_take_role,
    can_recruit_role,
    create_building_for_construction,
    default_role_wage,
    eligible_candidates_for_role,
    employee_contract_for,
    employee_ids,
    employee_role,
    employee_salary,
    employee_task,
    employee_wage,
    ensure_employee_contracts,
    normalize_bull,
    normalize_ranch_data,
    recruitable_roles,
    remove_employee_contract,
    role_count,
    role_limit,
    set_employee_contract,
)
from character import CHARACTER_QUESTIONS, Character, next_question_id
from demography import improved_health_condition, medical_patients, health_severity
from economy import (
    good_weight,
    inventory_weight,
    market_price,
    process_consumption,
    process_income,
    process_local_offer,
    property_good_price,
    sell_to_national_market,
    transfer_inventory_item,
    transport_cost,
    unit_transport_cost,
)
from game_state import (
    BASE_MARKET_PRICES,
    city_global_income,
    create_new_game,
    job_has_included_board,
    property_type_has_owner_board,
)
from building_types.general_store import (
    build_general_store_offers,
    general_store_available_quantity,
    general_store_can_auto_sell,
    general_store_goods,
    general_store_price,
    general_store_storage_capacity,
    player_general_store_can_sell,
    refresh_general_store_weapon_offer_stock,
    store_sell_price,
)
from building_types.barber_shop import build_barber_shop_offer
from building_types.medical_office import build_medical_clinic_offer
from building_types.saloon import (
    build_saloon_offer,
    saloon_inventory_quantity,
    saloon_storage_capacity,
    saloon_storage_used,
)
from building_types.ranch import (
    RANCH_BARN_CAPACITY,
    apply_bull_mortality,
    apply_ranch_attrition,
    apply_ranch_calving,
    bull_market_price,
    cattle_head_count,
    cattle_market_price,
    character_workforce_contribution,
    npc_workforce_contribution,
    ranch_birth_message,
    ranch_food_production,
    ranch_forage_gain,
    ranch_loss_message,
    ranch_attrition_loss,
    ranch_attrition_rate,
    ranch_workload,
    random_bull_market,
    run_ranch_exploitation,
)
from building_types.mine import (
    ensure_mine_defaults,
    mine_discontent_delta,
    mine_ore_inventory_items,
    mine_security_penalty,
    run_mine_exploitation,
)
from building_types.base import building_management_tabs, building_produces_housing_units
from goods_services import ITEM_CATALOG, item_definition, item_id, item_label, service_base_utility, service_default_price
from housing import HOUSING_TYPES, MARRIED_FORBIDDEN_HOUSING_TYPES
from housing_rules import (
    assign_employee_housing,
    available_housing_for_character,
    building_housing_units,
    character_is_married,
    clear_character_residence,
    ensure_building_housing_units,
    housing_action_label,
    housing_choice_label,
    housing_label,
    housing_mode_label,
    sync_property_housing,
)
from ids import make_building_id
from character import FEMALE_FIRST_NAMES, LAST_NAMES, MALE_FIRST_NAMES, NPC, create_npc, create_traveler, generate_consumption_needs, generate_preferences, pick_unique_name
from actions.prospecting import (
    claim_deposit,
    deposit_label,
    full_deposit_debug_label,
    mark_deposit_mined,
    prospect_region,
    remove_claim,
)
from saves import (
    delete_save,
    get_save_display_name,
    list_game_saves,
    load_all_time_achievements,
    load_game,
    reset_all_time_achievements,
    save_all_time_achievements,
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
        self.game_menu_window = None

        self.footer = tk.Frame(self.root)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8))
        self.character_label = tk.Label(self.footer, text="", anchor=tk.W)
        self.character_label.pack(side=tk.LEFT, padx=(0, 12))
        self.status_label = tk.Label(self.footer, text="", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.money_label = tk.Label(self.footer, text="")
        self.money_label.pack(side=tk.LEFT, padx=12)
        self.time_label = tk.Label(self.footer, text="", fg="#6b1f1f")
        self.time_label.pack(side=tk.LEFT, padx=(0, 12))
        self.social_button = tk.Button(self.footer, text="Social", command=self.show_social)
        self.profile_button = tk.Button(self.footer, text="Profil", command=self.show_profile)
        self.menu_button = tk.Button(self.footer, text="Menu", command=self.show_game_menu)
        self.footer_game_buttons_visible = False
        self.root.bind("<Escape>", self.open_game_menu_from_key)
        self.root.bind("<Control-Shift-C>", self.toggle_debug_mode_from_key)
        self.root.bind("<Control-Shift-c>", self.toggle_debug_mode_from_key)
        self.root.bind("<Control-Shift-dollar>", self.debug_add_money_from_key)
        self.root.bind("<Control-Shift-KeyPress-4>", self.debug_add_money_from_key)

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

    def scrollable_area(self, parent):
        outer = tk.Frame(parent)
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=content, anchor=tk.NW)

        def configure_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def configure_width(event):
            canvas.itemconfigure(window_id, width=event.width)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", configure_width)
        canvas.bind("<MouseWheel>", on_mousewheel)
        content.bind("<MouseWheel>", on_mousewheel)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return content

    def update_footer(self):
        if self.game:
            self.character_label.config(text=self.game.character.name)
            self.money_label.config(text=f"Dollars : {format_money(self.game.character.money)}")
            if self.debug_mode:
                self.time_label.config(text=f"Temps : {self.game.action_points}/{WEEK_ACTION_POINTS}")
            else:
                self.time_label.config(text="")
            self.show_footer_game_buttons()
        else:
            self.character_label.config(text="")
            self.money_label.config(text="")
            self.time_label.config(text="")
            self.hide_footer_game_buttons()

    def show_footer_game_buttons(self):
        """Affiche les boutons disponibles uniquement quand une partie existe."""
        if self.footer_game_buttons_visible:
            return

        self.social_button.pack(side=tk.RIGHT, padx=(4, 0))
        self.profile_button.pack(side=tk.RIGHT)
        self.menu_button.pack(side=tk.RIGHT, padx=(0, 4))
        self.footer_game_buttons_visible = True

    def hide_footer_game_buttons(self):
        """Cache Menu / Profil / Social sur le menu principal et la creation."""
        if not self.footer_game_buttons_visible:
            return

        self.social_button.pack_forget()
        self.profile_button.pack_forget()
        self.menu_button.pack_forget()
        self.footer_game_buttons_visible = False

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
        if self.game_menu_window and self.game_menu_window.winfo_exists():
            self.game_menu_window.lift()
            return

        menu_window = tk.Toplevel(self.root)
        self.game_menu_window = menu_window
        menu_window.title("Menu")
        menu_window.geometry("300x310")
        menu_window.transient(self.root)
        menu_window.protocol("WM_DELETE_WINDOW", self.close_game_menu)

        center = tk.Frame(menu_window)
        center.pack(expand=True, fill=tk.BOTH, padx=16, pady=16)
        tk.Label(center, text="Menu", font=("Arial", 16, "bold")).pack(pady=(0, 12))

        def close_then(command):
            menu_window.destroy()
            self.game_menu_window = None
            command()

        self.add_button(center, "Sauvegarder", self.save_current_game)
        self.add_button(center, "Succes", lambda: close_then(self.show_game_achievements))
        self.add_button(center, "Parametres", lambda: close_then(self.show_settings))
        self.add_button(center, "Sauvegarder et quitter", lambda: close_then(self.save_and_quit_to_menu))
        self.add_button(center, "Retour", self.close_game_menu)

    def close_game_menu(self):
        if self.game_menu_window and self.game_menu_window.winfo_exists():
            self.game_menu_window.destroy()
        self.game_menu_window = None

    # Menu principal -----------------------------------------------------

    def show_main_menu(self):
        frame = self.set_screen("Menu principal")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text="Menu principal", font=("Arial", 18, "bold")).pack(pady=(0, 16))
        self.add_button(center, "Nouvelle partie", self.show_map_selection)
        self.add_button(center, "Charger une partie", self.show_load_menu)
        self.add_button(center, "Succes", self.show_all_time_achievements)
        self.add_button(center, "Parametres", self.show_settings)
        self.add_button(center, "Quitter", self.root.destroy)

    def show_map_selection(self):
        frame = self.set_screen("Nouvelle partie")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text="Vers ou voulez-vous migrer ?", font=("Arial", 16, "bold")).pack(pady=(0, 16))
        self.add_button(center, "Dusty Creek", lambda: self.start_character_creation("Dusty Creek"))
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
        self.set_status("Mode debug activé." if self.debug_mode else "Mode debug désactivé.")
        self.show_settings()

    def toggle_debug_mode_from_key(self, event=None):
        self.debug_mode = not self.debug_mode
        self.set_status("Mode debug activé." if self.debug_mode else "Mode debug désactivé.")
        self.update_footer()
        if self.game:
            self.show_city()

    # Succes -------------------------------------------------------------

    def show_all_time_achievements(self):
        frame = self.set_screen("Succes")
        tk.Label(frame, text="Succes du joueur", font=("Arial", 18, "bold")).pack(anchor=tk.W, pady=(0, 12))
        self.render_achievements(self.scrollable_area(frame), load_all_time_achievements())
        self.add_button(frame, "Reinitialiser", self.reset_all_time_achievements_menu)
        self.add_button(frame, "Retour", self.show_main_menu)

    def show_game_achievements(self):
        if not self.game:
            return

        frame = self.set_screen("Succes")
        tk.Label(frame, text="Succes de la partie", font=("Arial", 18, "bold")).pack(anchor=tk.W, pady=(0, 12))
        self.render_achievements(self.scrollable_area(frame), self.game.achievements)
        self.add_button(frame, "Retour", self.show_city)

    def render_achievements(self, parent, unlocked_achievements):
        unlocked = set(unlocked_achievements)
        for achievement_id, data in ACHIEVEMENTS.items():
            is_unlocked = achievement_id in unlocked
            state = "Debloque" if is_unlocked else "Non debloque"
            text = f"{data['name']} - {state}"
            if is_unlocked:
                text = f"{text}\n{data['description']}"
            tk.Label(
                parent,
                text=text,
                justify=tk.LEFT,
                anchor=tk.W,
                font=("Arial", 11, "bold" if is_unlocked else "normal"),
            ).pack(fill=tk.X, pady=6)

    def reset_all_time_achievements_menu(self):
        if messagebox.askyesno("Reinitialiser", "Supprimer les succes globaux du joueur ?"):
            reset_all_time_achievements()
            self.set_status("Succès globaux réinitialisés.")
            self.show_all_time_achievements()

    def unlock_achievement(self, achievement_id):
        if achievement_id not in ACHIEVEMENTS:
            return

        unlocked_now = achievement_id not in self.game.achievements
        if unlocked_now:
            self.game.achievements.append(achievement_id)

        all_time = load_all_time_achievements()
        if achievement_id not in all_time:
            all_time.append(achievement_id)
            save_all_time_achievements(all_time)
        if unlocked_now:
            self.show_achievement_popup(achievement_id)

    def show_achievement_popup(self, achievement_id):
        data = ACHIEVEMENTS[achievement_id]
        popup = tk.Toplevel(self.root)
        popup.title("Succès débloqué")
        popup.transient(self.root)
        popup.grab_set()
        popup.geometry("360x180")

        frame = tk.Frame(popup, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Succès débloqué", font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))
        tk.Label(frame, text=data["name"], font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 6))
        tk.Label(frame, text=data["description"], wraplength=320, justify=tk.LEFT).pack(anchor=tk.W, fill=tk.X)
        tk.Button(frame, text="Fermer", command=popup.destroy).pack(anchor=tk.E, pady=(16, 0))

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
                self.set_status("Sélectionne une sauvegarde.")
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

        self.set_status(f"Partie chargée : {self.game.character.name}")
        self.show_city()

    def show_delete_confirmation(self, save_path):
        self.set_profile_return(lambda: self.show_delete_confirmation(save_path))
        display_name = get_save_display_name(save_path)
        frame = self.set_screen("Supprimer une sauvegarde")
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text=f"Supprimer définitivement {display_name} ?", font=("Arial", 14, "bold")).pack(pady=12)
        self.add_button(center, "Oui, supprimer", lambda: self.delete_selected_save(save_path))
        self.add_button(center, "Non", self.show_load_menu)

    def delete_selected_save(self, save_path):
        delete_save(save_path)
        self.set_status("Sauvegarde supprimée.")
        self.show_load_menu()

    # Creation de personnage -------------------------------------------

    def start_character_creation(self, city_name):
        self.character_city_name = city_name
        self.character_data = {
            "origin": None,
            "strength": 4,
            "sociability": 4,
            "intelligence": 4,
            "money": 45,
            "skills": [],
        }
        self.character_starting_activity = "hard"
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
        self.character_age = 25
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
                self.set_status("Réponse obligatoire.")
                return
            on_validate(value)

        entry.bind("<Return>", validate)
        self.add_button(center, "Valider", validate)
        self.add_button(center, "Aléatoire", randomize)
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
            "money": 45,
            "skills": [],
        }
        self.character_starting_activity = "hard"
        self.answered_question_ids = set()
        self.show_character_question(CHARACTER_QUESTIONS[0]["id"])

    def answer_character_question(self, question_id, selected):
        self.answered_question_ids.add(question_id)

        for stat_name, value in selected.get("set_stats", {}).items():
            self.character_data[stat_name] = value

        for stat_name, bonus in selected.get("stats", {}).items():
            self.character_data[stat_name] += bonus

        if "set_money" in selected:
            self.character_data["money"] = selected["set_money"]
        else:
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
            self.show_starting_activity_question()

    def show_starting_activity_question(self):
        frame = self.set_screen("Creation de personnage")
        center = tk.Frame(frame)
        center.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            center,
            text="Dans quelle activité allez-vous vous lancer ?",
            font=("Arial", 14, "bold"),
            wraplength=720,
        ).pack(pady=(0, 16))

        choices = self.starting_activity_choices()
        for choice in choices:
            self.add_button(
                center,
                choice["label"],
                lambda selected=choice: self.answer_starting_activity(selected),
                width=54,
            )
        self.add_back_button(frame, self.restart_character_questions)

    def starting_activity_choices(self):
        choices = []
        if self.character_has_skill("Jeu") or self.character_has_skill("Charisme"):
            choices.append({
                "label": "Je veux ouvrir mon propre saloon.",
                "activity": "saloon",
            })
        if self.character_has_skill("Élevage"):
            choices.append({
                "label": "Je vais construire mon ranch et élever mes bêtes.",
                "activity": "ranch",
            })
        if self.character_has_skill("Prospection"):
            choices.append({
                "label": "Je vais trouver de l'or !",
                "activity": "prospection",
                "message": "Je vous souhaite bonne chance, mais je ne peux rien pour vous.",
            })
        choices.append({
            "label": "La liberté ça se mérite laissez-moi faire. (mode difficile)",
            "activity": "hard",
        })
        return choices

    def character_has_skill(self, skill_name):
        return any(normalize_text(skill) == normalize_text(skill_name) for skill in self.character_data["skills"])

    def answer_starting_activity(self, selected):
        self.character_starting_activity = selected["activity"]
        if selected.get("message"):
            messagebox.showinfo("Bonne chance", selected["message"])
        self.finish_character_creation()

    def question_by_id(self, question_id):
        for question_data in CHARACTER_QUESTIONS:
            if question_data["id"] == question_id:
                return question_data
        raise ValueError(f"Question inconnue : {question_id}")

    def finish_character_creation(self):
        name = f"{self.character_first_name} {self.character_last_name}"
        character = Character(
            first_name=self.character_first_name,
            last_name=self.character_last_name,
            name=name,
            sex=self.character_sex,
            age=self.character_age,
            origin=self.character_data["origin"] or "Nouvel arrivant",
            strength=self.character_data["strength"],
            sociability=self.character_data["sociability"],
            intelligence=self.character_data["intelligence"],
            income=0,
            money=self.character_data["money"],
            condition="en forme",
            skills=self.character_data["skills"],
        )
        self.game = create_new_game(
            character,
            city_name=self.character_city_name,
            player_starting_activity=self.character_starting_activity,
        )
        save_game(self.game)
        self.set_status(f"Personnage créé : {character.name}")
        self.show_city()

    # Ville --------------------------------------------------------------

    def show_city(self):
        self.set_profile_return(self.show_city)
        frame = self.set_screen(f"{self.game.city.name} - Vue ville")
        header = tk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(header, text=self.game.city.name, font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        population_count = len(self.game.city.population)
        total_income = city_global_income(self.game.city)
        right_header = tk.Frame(header)
        right_header.pack(side=tk.RIGHT)
        tk.Label(right_header, text=current_weekday_label(self.game), font=("Arial", 11, "bold")).pack(anchor=tk.E)
        if self.debug_mode:
            tk.Label(
                right_header,
                text=f"Debug temps : {self.game.action_points}/{WEEK_ACTION_POINTS}",
                fg="#6b1f1f",
            ).pack(anchor=tk.E)
        tk.Label(right_header, text=f"Population : {population_count} | Revenu global : {total_income}").pack(anchor=tk.E)

        body = tk.Frame(frame)
        body.pack(fill=tk.BOTH, expand=True)

        action_panel = tk.LabelFrame(body, text="Actions")
        action_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.city_actions = [
            action("Construire", 0, self.show_construction),
            action(housing_action_label(self.game.city, self.game.character), 0.1, self.show_available_housing),
        ]
        if player_has_medical_laboratory(self.game):
            self.city_actions.append(action("Chercher des plantes médicinales", 2, self.search_medicinal_plants))
        if has_skill(self.game.character, "Criminalité"):
            self.city_actions.append(action("Trouver un repère", 1, self.find_hideout))
        if self.debug_mode:
            self.city_actions.extend([
                action("Ajouter des dollars", 0, self.debug_add_money),
                action("Claim un filon", 0, self.debug_show_deposit_claims),
                action("Voir population", 0, self.debug_show_population),
                action("Journal du dernier tour", 0, self.debug_show_turn_log),
            ])
        self.city_actions.append(action("Finir le tour", 0, self.finish_turn))
        action_list = tk.Listbox(action_panel)
        action_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for action_data in self.city_actions:
            action_list.insert(tk.END, action_label(action_data, show_cost=self.debug_mode))
            if action_data[0] in DEBUG_ACTION_LABELS:
                action_list.itemconfig(action_list.size() - 1, fg="#b00000")
        action_list.bind("<Double-Button-1>", lambda _event: self.run_list_action(action_list, self.city_actions))

        city_buildings = [building for building in self.game.city.buildings if not building_is_countryside(building)]
        countryside_buildings = [building for building in self.game.city.buildings if building_is_countryside(building)]
        city_housing_buildings = [
            housing for housing in getattr(self.game.city, "housing_buildings", [])
            if housing.owner == self.game.character.name and housing.visible_if_player_owned and housing.location != "Campagne"
        ]
        countryside_housing_buildings = [
            housing for housing in getattr(self.game.city, "housing_buildings", [])
            if housing.owner == self.game.character.name and housing.visible_if_player_owned and housing.location == "Campagne"
        ]

        city_panel = tk.LabelFrame(body, text="Ville")
        city_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        city_building_list = tk.Listbox(city_panel, height=8)
        city_building_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for building in city_buildings:
            city_building_list.insert(tk.END, building_list_label(building))
            color_owned_building(city_building_list, tk.END, building, self.game.character.name)
        for housing in city_housing_buildings:
            city_building_list.insert(tk.END, housing_building_list_label(housing))
            city_building_list.itemconfig(city_building_list.size() - 1, fg="#1f7a1f")
        city_building_list.bind("<Double-Button-1>", lambda _event: self.enter_selected_building(city_building_list, city_buildings))

        countryside_panel = tk.LabelFrame(body, text="Campagne (à une demi-journée)")
        countryside_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        countryside_building_list = tk.Listbox(countryside_panel, height=8)
        countryside_building_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for building in countryside_buildings:
            countryside_building_list.insert(tk.END, building_list_label(building))
            color_owned_building(countryside_building_list, tk.END, building, self.game.character.name)
        for housing in countryside_housing_buildings:
            countryside_building_list.insert(tk.END, housing_building_list_label(housing))
            countryside_building_list.itemconfig(countryside_building_list.size() - 1, fg="#1f7a1f")
        countryside_building_list.bind("<Double-Button-1>", lambda _event: self.enter_selected_building(countryside_building_list, countryside_buildings))

    def run_list_action(self, listbox, actions):
        selection = listbox.curselection()
        if selection:
            self.run_action(actions[selection[0]])

    def run_action(self, action_data):
        _label, cost, command = action_data
        if not self.consume_action_time(cost):
            return
        command()

    def consume_action_time(self, cost):
        if cost <= 0:
            return True

        if self.game.action_points + cost > WEEK_ACTION_POINTS:
            if messagebox.askyesno(
                "Semaine terminee",
                "Cette action depasse le temps disponible. Veux-tu finir le tour ?",
            ):
                self.finish_turn(confirm=False)
            return False

        self.game.action_points = round(self.game.action_points + cost, 2)
        self.update_footer()
        return True

    def finish_turn(self, confirm=True):
        if confirm and not messagebox.askyesno("Finir le tour", "Êtes-vous sûr de vouloir finir le tour ?"):
            return

        self.show_season_occupation()

    def show_season_occupation(self):
        self.set_profile_return(self.show_season_occupation)
        frame = self.set_screen("Occupation de la saison")
        tk.Label(frame, text="Que veux-tu faire cette saison ?", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))
        tk.Label(
            frame,
            text="Ce choix remplacera les anciennes petites actions de travail pendant le tour.",
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 8))

        occupations = self.available_player_occupations()
        occupation_list = tk.Listbox(frame, height=14)
        occupation_list.pack(fill=tk.BOTH, expand=True, pady=8)
        for occupation in occupations:
            occupation_list.insert(tk.END, occupation["label"])
        occupation_list.selection_set(0)

        buttons = tk.Frame(frame)
        buttons.pack(fill=tk.X, pady=8)
        self.add_button(buttons, "Valider", lambda: self.confirm_season_occupation(occupation_list, occupations))
        self.add_button(buttons, "Retour", self.show_city)

    def available_player_occupations(self):
        occupations = [{"label": "Ne rien faire de particulier", "type": "idle"}]
        for building in self.player_owned_buildings():
            if building.under_construction:
                continue
            if building.building_type == "Ranch":
                occupations.append({
                    "label": f"Travailler au ranch - {building.name}",
                    "type": "ranch_work",
                    "building_id": building.building_id,
                })
            elif building.building_type == "Saloon":
                occupations.append({
                    "label": f"Tenir le bar - {building.name}",
                    "type": "saloon_bar",
                    "building_id": building.building_id,
                })
                if "Cuisine" in normalize_upgrades(building.upgrades):
                    occupations.append({
                        "label": f"Préparer les repas - {building.name}",
                        "type": "saloon_meals",
                        "building_id": building.building_id,
                    })
            elif building.building_type == "Cabinet médical":
                occupations.append({
                    "label": f"S'occuper de la clinique - {building.name}",
                    "type": "clinic_care",
                    "building_id": building.building_id,
                })
            elif building.building_type == "Mine":
                occupations.append({
                    "label": f"Miner - {building.name}",
                    "type": "mine_work",
                    "building_id": building.building_id,
                })
                if player_can_supervise_mine(self.game.character, building):
                    occupations.append({
                        "label": f"Superviser la mine - {building.name}",
                        "type": "mine_supervision",
                        "building_id": building.building_id,
                    })

        current_job = getattr(self.game.character, "job", None)
        current_employer_id = getattr(self.game.character, "employer_building_id", None)
        current_employer = self.game.city.get_building_by_id(current_employer_id) if current_employer_id else None
        if current_job and current_employer and not current_employer.under_construction:
            occupations.append({
                "label": f"Travailler comme {current_job} - {current_employer.name}",
                "type": "employment",
                "building_id": current_employer.building_id,
                "role": current_job,
            })

        if not self.player_owned_buildings():
            occupations.extend(self.available_job_application_occupations())

        if has_skill(self.game.character, "Prospection") and self.game.character.inventory.get("materiel_prospection", 0) > 0:
            occupations.append({"label": "Prospecter la région", "type": "prospect_region"})
        if has_skill(self.game.character, "Chasse") and character_has_item_family(self.game.character, "arme_longue"):
            occupations.append({"label": "Chasser", "type": "hunt"})
        return occupations

    def player_owned_buildings(self):
        return [building for building in self.game.city.buildings if self.is_player_owner(building)]

    def available_job_application_occupations(self):
        occupations = []
        for building in self.game.city.buildings:
            if building.is_public or building.under_construction or self.is_player_owner(building):
                continue
            for role in recruitable_roles(building):
                if can_recruit_role(building, role) and can_player_take_role(self.game.character, role):
                    occupations.append({
                        "label": f"Postuler comme {role} - {building.name}",
                        "type": "job_application",
                        "building_id": building.building_id,
                        "role": role,
                    })
        return occupations

    def confirm_season_occupation(self, occupation_list, occupations):
        selection = occupation_list.curselection()
        if not selection:
            self.set_status("Choisis une occupation pour la saison.")
            return
        self.game.seasonal_occupation = occupations[selection[0]]
        self.show_end_turn_processing_screen()

    def find_hideout(self):
        self.set_status("Tu cherches un repère discret. Le script de criminalité sera ajouté plus tard.")

    def show_available_housing(self):
        sync_property_housing(self.game.city)
        self.set_profile_return(self.show_available_housing)
        title = housing_action_label(self.game.city, self.game.character)
        frame = self.set_screen(title)
        tk.Label(frame, text=title, font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))

        options = available_housing_for_character(self.game.city, self.game.character)
        if not options:
            tk.Label(frame, text="Aucun logement libre disponible.").pack(anchor=tk.W, pady=8)
            self.add_button(frame, "Retour", self.show_city)
            return

        housing_list = tk.Listbox(frame, height=14)
        housing_list.pack(fill=tk.BOTH, expand=True, pady=8)
        for housing in options:
            housing_list.insert(tk.END, housing_choice_label(self.game.city, housing))
        housing_list.selection_set(0)

        def choose():
            selection = housing_list.curselection()
            if not selection:
                self.show_validation_error("Choisis un logement.")
                return
            self.choose_city_housing(options[selection[0]])

        housing_list.bind("<Double-Button-1>", lambda _event: choose())
        self.add_button(frame, "Choisir", choose)
        self.add_button(frame, "Retour", self.show_city)

    def choose_city_housing(self, housing):
        if housing.housing_type in MARRIED_FORBIDDEN_HOUSING_TYPES and character_is_married(self.game.city, self.game.character):
            self.show_validation_error("Ce type de logement ne convient pas aux personnes mariées.")
            return
        clear_character_residence(self.game.city, self.game.character)
        housing.occupants = [self.game.character.name]
        self.game.character.residence = housing.housing_id
        self.set_status(f"Résidence choisie : {housing_label(housing)} pour {format_money(housing.rent_price)} par saison.")
        self.show_city()

    def apply_player_occupation(self):
        occupation = getattr(self.game, "seasonal_occupation", {}) or {"type": "idle"}
        occupation_type = occupation.get("type")
        occupied_building = self.game.city.get_building_by_id(occupation.get("building_id")) if occupation.get("building_id") else None
        if occupied_building and occupied_building.under_construction:
            self.game.seasonal_occupation = {"type": "idle"}
            self.log_turn_step("Occupation du joueur", f"{occupied_building.name} est encore en construction, occupation annulée.")
            return

        if occupation_type == "job_application":
            self.remove_player_from_employer()
            building = self.game.city.get_building_by_id(occupation.get("building_id"))
            role = occupation.get("role")
            if building and not building.under_construction and role and not self.player_owned_buildings() and can_recruit_role(building, role) and can_player_take_role(self.game.character, role):
                set_employee_contract(building, "player", role)
                self.game.character.job = role
                self.game.character.employer_building_id = building.building_id
                self.log_turn_step("Occupation du joueur", f"{self.game.character.name} obtient le poste : {role} chez {building.name}.")
            else:
                self.log_turn_step("Occupation du joueur", "Candidature impossible, aucun poste pris.")
                occupation = {"type": "idle"}
                self.game.seasonal_occupation = occupation
        elif occupation_type != "employment" and getattr(self.game.character, "job", None):
            old_job = self.game.character.job
            self.remove_player_from_employer()
            self.log_turn_step("Occupation du joueur", f"{self.game.character.name} ne travaille pas comme {old_job} cette saison et perd son poste.")

        if occupation_type == "employment":
            employer = self.game.city.get_building_by_id(occupation.get("building_id"))
            if not employer or employer.under_construction or getattr(self.game.character, "employer_building_id", None) != employer.building_id:
                self.remove_player_from_employer()
                self.game.seasonal_occupation = {"type": "idle"}
                self.log_turn_step("Occupation du joueur", "Emploi introuvable, occupation annulée.")
            else:
                self.log_turn_step("Occupation du joueur", f"{self.game.character.name} travaille comme {self.game.character.job} chez {employer.name}.")
        elif occupation_type == "prospect_region":
            self.resolve_player_prospecting()
        elif occupation_type in ["hunt", "mine_work", "mine_supervision"]:
            self.log_turn_step("Occupation du joueur", f"{occupation.get('label')} : script de résolution à ajouter.")
        elif occupation.get("label"):
            self.log_turn_step("Occupation du joueur", occupation["label"])

    def remove_player_from_employer(self):
        employer_id = getattr(self.game.character, "employer_building_id", None)
        if employer_id:
            building = self.game.city.get_building_by_id(employer_id)
            if building:
                remove_employee_contract(building, "player")
        self.game.character.job = None
        self.game.character.employer_building_id = None

    def resolve_player_prospecting(self):
        if not has_skill(self.game.character, "Prospection") or self.game.character.inventory.get("materiel_prospection", 0) <= 0:
            self.log_turn_step("Prospection", "Prospection impossible : compétence ou matériel manquant.")
            return
        deposit = prospect_region(self.game.city, self.game.character, "player")
        messages = self.turn_context.setdefault("messages", [])
        if deposit:
            message = f"Tu as découvert un filon : {deposit_label(deposit)}."
            messages.append(message)
            self.log_turn_step("Prospection", f"{message} Détail debug : {full_deposit_debug_label(deposit)}")
        else:
            messages.append("Tu n'as découvert aucun filon cette saison.")
            self.log_turn_step("Prospection", "Aucun filon découvert.")

    def show_end_turn_processing_screen(self):
        frame = self.set_screen("Fin de tour")
        frame.configure(bg="black")
        tk.Label(
            frame,
            text=f"{self.game.city.season} {self.game.city.year}",
            fg="white",
            bg="black",
            font=("Arial", 34, "bold"),
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.root.after(80, self.run_end_turn_pipeline)

    def run_end_turn_pipeline(self):
        run_end_turn(self)
    def end_turn_accounting_close(self):
        messages = close_season_accounting(self.game.city)
        for message in messages:
            self.log_turn_step("Comptabilité", message)

    def end_turn_ai_management(self):
        """Décisions des propriétaires PNJ. A remplir après la mécanique de gestion."""
        self.log_turn_step("Gestion IA", "Aucun calcul pour l'instant.")

    def end_turn_local_offer(self):
        """Construit la table d'offre des biens et services locaux."""
        offers = process_local_offer(self.game, self.process_building_turn_and_offer)
        self.turn_context["offer_table"] = offers
        self.log_turn_step("Offre locale", f"{len(offers)} offre(s) g?n?r?e(s).")

    def process_building_turn_and_offer(self, building):
        """Appelle l'exploitation du fichier de batiment puis retourne ses offres."""
        if building.building_type == "Ranch":
            result = run_ranch_exploitation(self.game, building)
            for title, detail in result.get("logs", []):
                self.log_turn_step(title, detail)
            self.turn_context.setdefault("messages", []).extend(result.get("messages", []))
            return result.get("offers", [])
        if building.building_type == "Mine":
            self.log_turn_step(f"Mine - {building.name}", run_mine_exploitation(self.game, building))
            return []
        if building.building_type == "Saloon":
            return build_saloon_offer(self.game, building)
        if building.building_type == "General Store":
            return build_general_store_offers(self.game, building)
        if building.building_type in ["Chirurgien barbier", "Barber shop"]:
            return build_barber_shop_offer(self.game, building)
        if building.building_type == "Cabinet m?dical":
            return build_medical_clinic_offer(self.game, building)
        return []


    def end_turn_income(self):
        """Calcule les revenus : salaires, propriétaires et revenus locaux."""
        income_table = process_income(self.game)
        self.turn_context["income_table"] = income_table
        self.log_turn_step("Revenus", income_table["summary"])

    def end_turn_demand_and_consumption(self):
        """Compare revenus, offres et préférences individuelles, puis encaisse les services."""
        consumption_table = process_consumption(self.game, self.turn_context.get("offer_table", []))
        self.turn_context["consumption_table"] = consumption_table
        self.turn_context["preference_lists"] = consumption_table["preference_lists"]
        self.turn_context["demand_table"] = consumption_table["demand_table"]
        self.log_turn_step("Demande et consommation", consumption_table["summary"])

    def end_turn_cleanup(self, new_year_started):
        for building in self.game.city.buildings:
            building.under_construction = False
            remove_legacy_workforce_keys(building)
            refresh_stored_goods(building)
        if new_year_started:
            archive_annual_results(self.game.city)
        self.log_turn_step("Nettoyage et sauvegarde", f"Constructions débloquées. Archivage annuel : {new_year_started}.")
        save_game(self.game)

    def log_turn_step(self, title, detail):
        self.game.turn_log.append(f"[{title}] {detail}")










    def show_city_after_turn(self):
        self.show_city()
        self.show_turn_messages()

    def show_turn_messages(self):
        messages = self.turn_context.get("messages", []) if hasattr(self, "turn_context") else []
        if not messages:
            return
        messagebox.showinfo("Bilan de saison", "\n\n".join(messages))

    def show_turn_transition(self, text, done_command):
        transition = tk.Toplevel(self.root)
        transition.overrideredirect(True)
        transition.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}")
        transition.configure(bg="black")
        transition.attributes("-alpha", 0.0)
        transition.transient(self.root)

        label = tk.Label(transition, text=text, fg="white", bg="black", font=("Arial", 34, "bold"))
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        def fade_in(step=0):
            alpha = min(0.92, step / 10)
            transition.attributes("-alpha", alpha)
            if step < 10:
                self.root.after(35, lambda: fade_in(step + 1))
            else:
                self.root.after(650, fade_out)

        def fade_out(step=10):
            alpha = max(0.0, step / 10)
            transition.attributes("-alpha", alpha)
            if step > 0:
                self.root.after(35, lambda: fade_out(step - 1))
            else:
                transition.destroy()
                done_command()

        fade_in()

    def enter_selected_building(self, listbox, buildings):
        selection = listbox.curselection()
        if selection:
            if selection[0] >= len(buildings):
                self.set_status("Ce logement n'a pas encore de menu dédié.")
                return
            building = buildings[selection[0]]
            if building.under_construction:
                self.show_validation_error("Ce bâtiment est encore en construction. Il sera accessible au prochain tour.")
                return
            travel_cost = building_entry_cost(building)
            if not self.consume_action_time(travel_cost):
                return
            if building.building_type == "General Store":
                self.show_trade(building)
                return
            self.show_building(building)

    def save_current_game(self):
        save_path = save_game(self.game)
        self.set_status(f"Partie sauvegardée : {save_path}")

    def save_and_quit_to_menu(self):
        self.save_current_game()
        self.game = None
        self.show_main_menu()

    def debug_add_money(self):
        self.game.character.money += 100
        self.set_status("Debug : 100 dollars ajoutés.")
        self.show_city()

    def debug_add_money_from_key(self, event=None):
        if not self.game:
            return
        self.game.character.money += 100
        self.set_status("Debug : 100 dollars ajoutés.")
        self.update_footer()

    def debug_show_deposit_claims(self):
        if not self.debug_mode:
            self.set_status("Active le mode debug pour claim un filon.")
            return

        self.set_profile_return(self.debug_show_deposit_claims)
        frame = self.set_screen("Filons - Debug")
        tk.Label(frame, text="Claim un filon - Debug", font=("Arial", 15, "bold"), fg="#b00000").pack(anchor=tk.W, pady=(0, 10))
        tk.Label(frame, text="Choisis un filon caché à attribuer au joueur.", fg="#b00000").pack(anchor=tk.W, pady=(0, 8))

        deposits = [
            deposit for deposit in getattr(self.game.city, "mineral_deposits", [])
            if not deposit.get("claimed_by") and not deposit.get("mine_building_id")
        ]
        if not deposits:
            tk.Label(frame, text="Aucun filon disponible.", fg="#b00000").pack(anchor=tk.W, pady=8)
            self.add_button(frame, "Retour", self.show_city)
            return

        deposit_list = tk.Listbox(frame, height=12)
        deposit_list.pack(fill=tk.BOTH, expand=True, pady=8)
        for deposit in deposits:
            deposit_list.insert(tk.END, full_deposit_debug_label(deposit))
            deposit_list.itemconfig(tk.END, fg="#b00000")

        deposit_list.bind("<Double-Button-1>", lambda _event: self.debug_claim_selected_deposit(deposit_list, deposits))
        self.add_button(frame, "Claim le filon sélectionné", lambda: self.debug_claim_selected_deposit(deposit_list, deposits))
        self.add_button(frame, "Retour", self.show_city)

    def debug_claim_selected_deposit(self, deposit_list, deposits):
        selection = deposit_list.curselection()
        if not selection:
            self.set_status("Choisis un filon à claim.")
            return

        deposit = deposits[selection[0]]
        claim_deposit(self.game.character, deposit, "player")
        self.set_status(f"Debug : filon claimé - {deposit_label(deposit)}")
        self.show_city()

    def debug_show_population(self):
        self.set_profile_return(self.debug_show_population)
        frame = self.set_screen("Population - Debug")
        tk.Label(frame, text="Population - Debug", font=("Arial", 15, "bold"), fg="#b00000").pack(anchor=tk.W, pady=(0, 10))
        tk.Label(frame, text="Double-clique sur un personnage pour voir toutes ses variables.", fg="#b00000").pack(anchor=tk.W, pady=(0, 8))

        npc_list = tk.Listbox(frame, height=18)
        npc_list.pack(fill=tk.BOTH, expand=True)
        for npc in self.game.city.population:
            npc_list.insert(tk.END, (
                f"{npc.name} | {npc.sex} | {npc.age} ans | {npc.job} | "
                f"origine={npc.origin} | physique={npc.strength} | social={npc.sociability} | "
                f"intelligence={npc.intelligence} | etat={getattr(npc, 'condition', 'en forme')} | "
                f"revenu={npc.income} | dollars={npc.money}"
            ))
            npc_list.itemconfig(tk.END, fg="#b00000")

        def open_selected_npc(event=None):
            selection = npc_list.curselection()
            if not selection:
                return
            self.debug_show_npc_detail(self.game.city.population[selection[0]])

        npc_list.bind("<Double-Button-1>", open_selected_npc)
        self.add_button(frame, "Voir le personnage sélectionné", open_selected_npc)
        self.add_button(frame, "Modifier le personnage sélectionné", lambda: self.debug_edit_selected_npc(npc_list))
        self.add_button(frame, "Retour", self.show_city)

    def debug_edit_selected_npc(self, npc_list):
        selection = npc_list.curselection()
        if not selection:
            self.set_status("Choisis un personnage à modifier.")
            return
        self.debug_edit_character(self.game.city.population[selection[0]], self.debug_show_population)

    def debug_show_npc_detail(self, npc):
        self.set_profile_return(lambda: self.debug_show_npc_detail(npc))
        frame = self.set_screen(f"Debug - {npc.name}")
        tk.Label(frame, text=f"Debug - {npc.name}", font=("Arial", 15, "bold"), fg="#b00000").pack(anchor=tk.W, pady=(0, 10))

        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        text_widget = tk.Text(text_frame, wrap=tk.WORD, fg="#b00000")
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.insert(tk.END, pformat(npc.to_dict(), width=100, sort_dicts=False))
        text_widget.configure(state=tk.DISABLED)

        self.add_button(frame, "Modifier", lambda: self.debug_edit_character(npc, lambda: self.debug_show_npc_detail(npc)))
        self.add_button(frame, "Retour", self.debug_show_population)

    def debug_show_turn_log(self):
        lines = self.game.turn_log or ["Aucun journal de tour disponible."]
        self.show_text_panel("Journal du dernier tour - Debug", "\n".join(lines), self.show_city)

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
                f"Dollars : {format_money(character.money)}",
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
        self.profile_list(columns, "Compétences", character.skills)
        self.profile_list(columns, "Proprietes", owned_buildings, fg="#1f7a1f")
        self.profile_list(columns, "Relations", ["Alliance : aucune", "Mariage : aucun", "Enfants : aucun"])
        if self.debug_mode:
            self.profile_list(
                columns,
                "Debug",
                [
                    f"Physique : {character.strength}",
                    f"Social : {character.sociability}",
                    f"Intelligence : {character.intelligence}",
                    describe_health(character),
                ],
                fg="#b00000",
            )
            self.add_button(frame, "Modifier le personnage - Debug", lambda: self.debug_edit_character(character, self.show_profile))

        self.add_button(frame, "Retour", self.profile_return_command)

    def debug_edit_character(self, character, back_command):
        if not self.debug_mode:
            self.set_status("Active le mode debug pour modifier les personnages.")
            return

        self.set_profile_return(lambda: self.debug_edit_character(character, back_command))
        frame = self.set_screen(f"Modifier - {character.name}")
        tk.Label(frame, text=f"Modifier - {character.name}", font=("Arial", 15, "bold"), fg="#b00000").pack(anchor=tk.W, pady=(0, 10))

        form_area = tk.Frame(frame)
        form_area.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(form_area, highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_area, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas)
        content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        entries = {}
        for field, label in editable_character_fields(character):
            row = tk.Frame(content)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, width=24, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row)
            entry.insert(0, debug_field_to_text(getattr(character, field, "")))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[field] = entry

        help_text = (
            "Listes : sépare par des virgules. "
            "Inventaire : exemple colt_navy=1, vivres_secs=4. "
            "Dictionnaires/listes complexes : tu peux aussi coller une syntaxe Python valide."
        )
        tk.Label(content, text=help_text, fg="#b00000", wraplength=760, justify=tk.LEFT).pack(fill=tk.X, pady=(8, 4))

        buttons = tk.Frame(frame)
        buttons.pack(fill=tk.X, pady=8)
        self.add_button(buttons, "Enregistrer", lambda: self.debug_save_character(character, entries, back_command))
        self.add_button(buttons, "Retour", back_command)

    def debug_save_character(self, character, entries, back_command):
        try:
            apply_debug_character_entries(character, entries)
        except ValueError as error:
            self.show_validation_error(str(error))
            return
        self.set_status(f"Debug : {character.name} modifié.")
        self.update_footer()
        back_command()

    def profile_list(self, parent, title, values, fg=None):
        panel = tk.LabelFrame(parent, text=title)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        if not values:
            values = ["Aucun"]
        for value in values:
            tk.Label(panel, text=f"- {value}", anchor=tk.W, justify=tk.LEFT, fg=fg).pack(fill=tk.X, padx=8, pady=2)

    # Social -------------------------------------------------------------

    def show_social(self):
        if not self.game:
            return

        frame = self.set_screen("Social")
        tk.Label(frame, text="Personnages importants", font=("Arial", 18, "bold")).pack(anchor=tk.W, pady=(0, 12))

        important_npcs = [npc for npc in self.game.city.population if is_social_important(npc)]
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
                    text="\n".join(social_relation_lines(npc, self.game.city.population)),
                    anchor=tk.W,
                    justify=tk.LEFT,
                ).pack(fill=tk.X)

        self.add_button(frame, "Retour", self.profile_return_command)

    # Batiments ----------------------------------------------------------

    def show_building(self, building):
        normalize_ranch_data(building)
        self.set_profile_return(lambda: self.show_building(building))
        frame = self.set_screen(building.name)
        center = tk.Frame(frame)
        center.pack(expand=True)

        tk.Label(center, text=building_display_name(building), font=("Arial", 18, "bold")).pack(pady=(0, 8))
        if building.building_type != "General Store":
            tk.Label(center, text=f"Propriétaire : {building.owner}", font=("Arial", 11)).pack(pady=(0, 18))
        if building.building_type == "Bureau du sherif":
            sheriff = self.find_sheriff()
            if sheriff:
                tk.Label(center, text=f"Sherif : {sheriff.name}", font=("Arial", 11, "bold")).pack(pady=(0, 18))
        if building.building_type == "Ranch":
            tk.Label(center, text=f"Bêtes du ranch : {cattle_head_count(building)}", font=("Arial", 11)).pack(pady=(0, 8))
            visible_assets = ranch_visible_assets(building)
        else:
            visible_assets = building_assets(building)
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

        for action_data in self.available_building_actions(building):
            self.add_button(center, action_label(action_data, show_cost=self.debug_mode), lambda selected=action_data: self.run_action(selected), width=34)
        self.add_button(center, "Sortir", self.show_city, width=34)

    def find_sheriff(self):
        for npc in self.game.city.population:
            if npc.job == "Sherif":
                return npc
        return None

    def search_medicinal_plants(self):
        quantity = random.choice([0, 1, 2, 3])
        if quantity > 0:
            self.game.character.inventory["plantes_medicinales"] = self.game.character.inventory.get("plantes_medicinales", 0) + quantity
            self.set_status(f"Tu as trouvé {quantity} plante(s) médicinale(s).")
        else:
            self.set_status("Tu n'as trouvé aucune plante médicinale.")

    def available_building_actions(self, building):
        if building.building_type == "Saloon":
            actions = self.saloon_actions(building)
        elif building.building_type == "Ranch":
            actions = self.ranch_actions(building)
        elif building.building_type == "General Store":
            actions = [action("Acheter / Vendre", 0, lambda: self.show_trade(building))]
        elif building.building_type == "Bureau du sherif":
            actions = [
                action("Regarder les primes", 0.1, lambda: self.set_status("Aucune prime disponible pour le moment.")),
                action("Candidater pour le bureau du shérif", 1, lambda: self.set_status("Candidature enregistrée pour plus tard.")),
            ]
        elif building.building_type == "Post Office":
            actions = [action("Poster une annonce pour un emploi", 0.1, lambda: self.set_status("Annonce d'emploi postée pour plus tard."))]
        elif building.building_type == "Église":
            actions = [
                action("Faire un don", 0.1, lambda: self.set_status("Le don sera traité par le script d'église plus tard.")),
            ]
            if is_sunday(self.game):
                actions.append(action("Assister à la messe", 1, lambda: self.set_status("La messe sera traitée par le script d'église plus tard.")))
        elif building.building_type in ["Chirurgien barbier", "Barber shop"]:
            actions = [
                action("Se faire couper", 0.1, lambda: self.set_status("La coupe sera traitée plus tard.")),
                action("Se faire soigner", 1, lambda: self.set_status("Les soins seront traités plus tard.")),
            ]
        elif building.building_type == "Cabinet médical":
            actions = []
            if "Laboratoire" in normalize_upgrades(building.upgrades):
                actions.append(action("Préparer un remède", 1, lambda: self.prepare_remedy(building)))
        else:
            actions = []

        if (not building.is_public or self.debug_mode) and (self.is_player_owner(building) or self.debug_mode):
            actions.append(action("Gestion", 0, lambda: self.show_management(building)))

        return actions

    def prepare_remedy(self, building):
        if building.inventory.get("remede", 0) >= MEDICAL_PHARMACY_CAPACITY:
            self.show_validation_error("La pharmacie est pleine.")
            return
        if not remove_first_available_item([self.game.character.inventory, building.inventory], "plantes_medicinales", 1):
            self.show_validation_error("Il faut une plante médicinale.")
            return
        building.inventory["remede"] = building.inventory.get("remede", 0) + 1
        self.set_status("Un remède a été préparé.")
        self.show_building(building)

    def saloon_actions(self, building):
        actions = []
        actions.append(action("Boire une bière", 0.1, lambda: self.drink_beer(building)))
        if building.features.get("table_poker"):
            actions.append(action("Faire une partie de poker", 1, lambda: self.pay_for_service(building, 10, "La vraie partie de poker sera ajoutée plus tard.")))
        if room_count(building) > 0:
            actions.append(action("Appeler une hôtesse", 1, lambda: self.pay_for_service(building, building.production.get("prix_hotesse", 2), "Une hôtesse vient tenir compagnie au joueur.")))
        if "Salle de bain" in building.upgrades:
            actions.append(action("Prendre un bain", 0.5, lambda: self.pay_for_service(building, building.production.get("prix_bain", 0.5), "Un bain chaud remet les idees en place.")))
        if "Cuisine" in building.upgrades:
            actions.append(action("Commander un repas", 0.5, lambda: self.pay_for_service(building, building.production.get("prix_repas", 1), "Le repas est servi.")))
        return actions

    def ranch_actions(self, building):
        if self.is_player_owner(building):
            actions = []
            if trail_drive_state(building):
                actions.append(action("Modifier le long trail drive", 0.1, lambda: self.modify_long_trail_drive(building)))
                actions.append(action("Annuler le long trail drive", 0.1, lambda: self.cancel_long_trail_drive(building)))
            elif self.game.city.season == "Automne":
                actions.append(action("Préparer un long trail drive", 1, lambda: self.show_trail_drive_cattle_step(building)))
            return actions
        return []

    def is_player_owner(self, building):
        return building.owner == self.game.character.name

    def spend(self, amount):
        if self.game.character.money < amount:
            self.show_validation_error("Tu n'as pas assez d'argent.")
            return False
        self.game.character.money -= amount
        return True

    def drink_beer(self, building):
        if saloon_inventory_quantity(building, "fut_biere") <= 0:
            self.show_validation_error("Il n'y a plus de bière en stock.")
            return
        price = building.production.get("prix_biere", 0.5)
        if not self.spend(price):
            return
        remove_saloon_good(building, "fut_biere", 1)
        building.current_balance += price
        record_building_sale(building, price)
        self.set_status("Tu bois une bière.")
        self.show_building(building)

    def pay_for_service(self, building, price, message):
        if not self.spend(price):
            return
        building.current_balance += price
        record_building_sale(building, price)
        self.set_status(message)
        self.show_building(building)

    def show_trail_drive_cattle_step(self, building, draft=None):
        ensure_bulls(building)
        self.set_profile_return(lambda: self.show_trail_drive_cattle_step(building, draft))
        frame = self.set_screen("Long trail drive - Bétail à vendre")
        tk.Label(frame, text="Long trail drive - bétail à vendre", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))

        if draft is None:
            draft = {
                "sell_cattle": 0,
                "sell_bulls": [],
                "cowboys": [],
                "hired_cowboys": [],
                "buy_cattle": 0,
                "buy_bulls": [],
                "bull_market": random_bull_market(self.game.character),
            }
        draft.setdefault("bull_market", random_bull_market(self.game.character))
        self.render_trail_drive_cattle_form(frame, building, draft)

    def render_trail_drive_cattle_form(self, frame, building, draft):
        max_cattle = max(0, cattle_head_count(building))
        cattle_var = tk.IntVar(value=draft["sell_cattle"])
        counter = tk.Frame(frame)
        counter.pack(anchor=tk.W, pady=8)
        tk.Label(counter, text="Vaches à vendre").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(counter, text="-", width=3, command=lambda: cattle_var.set(max(0, cattle_var.get() - 1))).pack(side=tk.LEFT)
        tk.Label(counter, textvariable=cattle_var, width=5).pack(side=tk.LEFT)
        tk.Button(counter, text="+", width=3, command=lambda: cattle_var.set(min(max_cattle, cattle_var.get() + 1))).pack(side=tk.LEFT)
        tk.Label(counter, text=f"/ {max_cattle}").pack(side=tk.LEFT, padx=(8, 0))

        bulls = building.production.get("bulls", [])
        selected_bulls = list(draft.get("sell_bulls", []))
        self.render_bull_selection_columns(frame, "Taureaux à vendre", bulls, selected_bulls)

        def next_step():
            draft["sell_cattle"] = cattle_var.get()
            draft["sell_bulls"] = selected_bulls
            self.show_trail_drive_cowboy_step(building, draft)

        self.add_button(frame, "Suivant", next_step)
        self.add_button(frame, "Retour", lambda: self.show_building(building))

    def render_bull_selection_columns(self, parent, title, available_bulls, selected_bulls):
        panel = tk.LabelFrame(parent, text=title)
        panel.pack(fill=tk.BOTH, expand=True, pady=10)
        left = tk.LabelFrame(panel, text="Disponibles")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 4), pady=8)
        right = tk.LabelFrame(panel, text="Choisis")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 8), pady=8)

        available_list = tk.Listbox(left, height=8)
        available_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        selected_list = tk.Listbox(right, height=8)
        selected_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        def refresh():
            available_list.delete(0, tk.END)
            selected_list.delete(0, tk.END)
            for bull in available_bulls:
                if bull not in selected_bulls:
                    available_list.insert(tk.END, trail_bull_label(bull))
            for bull in selected_bulls:
                selected_list.insert(tk.END, trail_bull_label(bull))

        def add_selected(event=None):
            visible_bulls = [bull for bull in available_bulls if bull not in selected_bulls]
            selection = available_list.curselection()
            if not selection:
                return
            selected_bulls.append(visible_bulls[selection[0]])
            refresh()

        available_list.bind("<Double-Button-1>", add_selected)
        tk.Button(left, text="Choisir", command=add_selected).pack(fill=tk.X, padx=8, pady=(0, 8))
        refresh()

    def show_trail_drive_cowboy_step(self, building, draft):
        self.set_profile_return(lambda: self.show_trail_drive_cowboy_step(building, draft))
        frame = self.set_screen("Long trail drive - Cowboys")
        tk.Label(frame, text="Long trail drive - équipe", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))

        available = trail_available_cowboys(self.game, building)
        selected = list(draft.get("cowboys", []))
        hired = list(draft.get("hired_cowboys", []))

        columns = tk.Frame(frame)
        columns.pack(fill=tk.BOTH, expand=True)
        left = tk.LabelFrame(columns, text="Disponibles")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right = tk.LabelFrame(columns, text="Choisis")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        available_list = tk.Listbox(left, height=12)
        available_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        for entry in available:
            available_list.insert(tk.END, trail_cowboy_label(self.game, entry))

        selected_list = tk.Listbox(right, height=12)
        selected_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        def refresh_selected():
            selected_list.delete(0, tk.END)
            for entry in selected + hired:
                selected_list.insert(tk.END, trail_cowboy_label(self.game, entry))

        def add_selected(event=None):
            selection = available_list.curselection()
            if not selection:
                return
            entry = available[selection[0]]
            if entry not in selected:
                selected.append(entry)
                refresh_selected()

        def hire_cowboy():
            hired.append(create_trail_cowboy(self.game, skilled=False))
            refresh_selected()

        def hire_skilled_cowboy():
            hired.append(create_trail_cowboy(self.game, skilled=True))
            refresh_selected()

        available_list.bind("<Double-Button-1>", add_selected)
        self.add_button(left, "Choisir", add_selected)
        self.add_button(left, f"Recruter un cowboy ({format_money(employee_salary('Cowboy') * 2)})", hire_cowboy)
        self.add_button(left, f"Recruter un trail boss ({format_money(employee_salary('Cowboy') * 3)})", hire_skilled_cowboy)
        refresh_selected()

        def next_step():
            crew = selected + hired
            if not any(trail_entry_has_skill(self.game, entry, "Élevage") for entry in crew):
                self.show_validation_error("Il faut au moins un personnage avec la compétence Élevage.")
                return
            draft["cowboys"] = selected
            draft["hired_cowboys"] = hired
            self.show_trail_drive_purchase_step(building, draft)

        self.add_button(frame, "Suivant", next_step)
        self.add_button(frame, "Retour", lambda: self.show_trail_drive_cattle_step(building, draft))

    def show_trail_drive_purchase_step(self, building, draft):
        self.set_profile_return(lambda: self.show_trail_drive_purchase_step(building, draft))
        frame = self.set_screen("Long trail drive - Achats")
        tk.Label(frame, text="Long trail drive - achats avant départ", font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 10))

        cattle_var = tk.IntVar(value=draft.get("buy_cattle", 0))
        counter = tk.Frame(frame)
        counter.pack(anchor=tk.W, pady=8)
        tk.Label(counter, text=f"Bêtes à acheter ({format_money(cattle_market_price(self.game.city))} pièce)").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(counter, text="-", width=3, command=lambda: cattle_var.set(max(0, cattle_var.get() - 1))).pack(side=tk.LEFT)
        tk.Label(counter, textvariable=cattle_var, width=5).pack(side=tk.LEFT)
        tk.Button(counter, text="+", width=3, command=lambda: cattle_var.set(cattle_var.get() + 1)).pack(side=tk.LEFT)

        market = draft.setdefault("bull_market", random_bull_market())
        selected_bulls = list(draft.get("buy_bulls", []))
        self.render_bull_selection_columns(frame, "Taureaux à acheter", market, selected_bulls)

        def confirm():
            draft["buy_cattle"] = cattle_var.get()
            draft["buy_bulls"] = selected_bulls
            self.confirm_long_trail_drive(building, draft)

        self.add_button(frame, "Confirmer", confirm)
        self.add_button(frame, "Retour", lambda: self.show_trail_drive_cowboy_step(building, draft))

    def confirm_long_trail_drive(self, building, draft):
        if trail_drive_state(building):
            self.show_validation_error("Un long trail drive est déjà préparé.")
            return

        sell_cattle = draft.get("sell_cattle", 0)
        sell_bulls = list(draft.get("sell_bulls", []))
        buy_cattle = draft.get("buy_cattle", 0)
        buy_bulls = list(draft.get("buy_bulls", []))
        crew = list(draft.get("cowboys", []))
        hired = list(draft.get("hired_cowboys", []))
        merchandise_cost = buy_cattle * cattle_market_price(self.game.city) + sum(bull_market_price(bull) for bull in buy_bulls)
        wage_cost = sum(entry.get("wage", 0) for entry in hired)
        total_cost = merchandise_cost + wage_cost
        if building.current_balance < total_cost:
            self.show_validation_error(f"Il faut {format_money(total_cost)} pour confirmer.")
            return

        bulls = building.production.get("bulls", [])
        sell_split = split_ranch_cattle_sale(building, sell_cattle)
        building.production["head_count"] = max(0, cattle_head_count(building) - sell_cattle)
        building.production["bulls"] = [bull for bull in bulls if bull not in sell_bulls]
        if merchandise_cost:
            record_accounting_charge(building, "merchandise_purchases", merchandise_cost)
        if wage_cost:
            record_accounting_charge(building, "wages", wage_cost)
        for bull in buy_bulls:
            bull["stock_type"] = "merchandise"

        removed_npcs = []
        for entry in crew:
            if entry["type"] == "player":
                continue
            npc = self.game.city.get_npc_by_id(entry["npc_id"])
            if not npc:
                continue
            removed_npcs.append({"npc": npc.to_dict(), "contract": employee_contract_for(building, npc.npc_id), "role": employee_role(building, npc.npc_id, "Cowboy")})
            remove_employee_contract(building, npc.npc_id)
            self.game.city.population = [person for person in self.game.city.population if person.npc_id != npc.npc_id]

        for entry in hired:
            removed_npcs.append({"npc": entry["npc"].to_dict(), "role": "Cowboy"})

        building.production["trail_drive"] = {
            "sell_cattle": sell_cattle,
            "sell_bulls": sell_bulls,
            "buy_cattle": buy_cattle,
            "buy_bulls": buy_bulls,
            "sell_cattle_split": sell_split,
            "bull_market": list(draft.get("bull_market", [])),
            "crew": crew,
            "hired_cowboys": [entry["npc"].to_dict() for entry in hired],
            "removed_npcs": removed_npcs,
            "merchandise_cost": merchandise_cost,
            "wage_cost": wage_cost,
            "total_cost": total_cost,
        }
        self.set_status("Long trail drive préparé. Il sera traité à la fin du tour.")
        self.show_building(building)

    def cancel_long_trail_drive(self, building):
        self.restore_long_trail_drive(building, refund=True)
        self.set_status("Long trail drive annulé.")
        self.show_building(building)

    def modify_long_trail_drive(self, building):
        draft = draft_from_trail_drive(building)
        if self.restore_long_trail_drive(building, refund=True):
            self.set_status("Long trail drive restauré. Tu peux le modifier.")
            self.show_trail_drive_cattle_step(building, draft)

    def restore_long_trail_drive(self, building, refund=False):
        trail_drive = trail_drive_state(building)
        if not trail_drive:
            return False

        building.production["head_count"] = cattle_head_count(building) + trail_drive.get("sell_cattle", 0)
        restore_ranch_cattle_stock(building, trail_drive.get("sell_cattle_split", {}))
        building.production.setdefault("bulls", []).extend(trail_drive.get("sell_bulls", []))
        for removed in trail_drive.get("removed_npcs", []):
            npc = npc_from_saved_data(removed["npc"])
            if not self.game.city.get_npc_by_id(npc.npc_id):
                self.game.city.population.append(npc)
            contract = removed.get("contract", {})
            set_employee_contract(
                building,
                npc.npc_id,
                contract.get("role", removed.get("role", "Cowboy")),
                contract.get("wage"),
                contract.get("task"),
            )
            npc.employer_building_id = building.building_id
            npc.job = employee_role(building, npc.npc_id, "Cowboy")

        if refund:
            if trail_drive.get("merchandise_cost", 0):
                record_accounting_charge(building, "merchandise_purchases", -trail_drive.get("merchandise_cost", 0))
            if trail_drive.get("wage_cost", 0):
                record_accounting_charge(building, "wages", -trail_drive.get("wage_cost", 0))
        building.production.pop("trail_drive", None)
        return True

    # General Store ------------------------------------------------------

    def show_trade(self, building):
        self.set_profile_return(lambda: self.show_trade(building))
        frame = self.set_screen("General Store - Acheter / Vendre")
        left = tk.LabelFrame(frame, text="Achats")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right = tk.LabelFrame(frame, text="Vente")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        buy_items = list(general_store_goods())
        buy_labels = []
        buy_by_label = {}
        for item in buy_items:
            price = general_store_price(self.game.city, item)
            quantity = general_store_available_quantity(building, item)
            stock_text = "" if quantity is None else f" | stock : {quantity}"
            label = f"{item_label(item)} - {format_money(price)}{stock_text}"
            buy_labels.append(label)
            buy_by_label[label] = item
        buy_var = tk.StringVar(value=buy_labels[0] if buy_labels else "")
        buy_combo = ttk.Combobox(left, textvariable=buy_var, values=buy_labels, state="readonly")
        buy_combo.pack(fill=tk.X, padx=8, pady=(8, 4))
        self.add_button(left, "Acheter", lambda: self.buy_selected_store_item(building, buy_var, buy_by_label))

        sellable_items = [
            (item, quantity)
            for item, quantity in self.game.character.inventory.items()
            if quantity > 0 and item_id(item) in general_store_goods()
        ]
        if not sellable_items:
            tk.Label(right, text="Inventaire vide.").pack(anchor=tk.W, padx=8, pady=8)
        else:
            sell_labels = []
            sell_by_label = {}
            for item, quantity in sellable_items:
                price = store_sell_price(self.game.city, item)
                label = f"{item_label(item)} x{quantity} - {format_money(price)}"
                sell_labels.append(label)
                sell_by_label[label] = item
            sell_var = tk.StringVar(value=sell_labels[0])
            ttk.Combobox(right, textvariable=sell_var, values=sell_labels, state="readonly").pack(fill=tk.X, padx=8, pady=(8, 4))
            self.add_button(right, "Vendre", lambda: self.sell_selected_store_item(building, sell_var, sell_by_label))

        self.add_button(frame, "Retour", self.show_city)

    def buy_selected_store_item(self, building, selected_var, items_by_label):
        item = items_by_label.get(selected_var.get())
        if not item:
            self.show_validation_error("Choisis un article.")
            return
        self.buy_item(building, item)

    def sell_selected_store_item(self, building, selected_var, items_by_label):
        item = items_by_label.get(selected_var.get())
        if not item:
            self.show_validation_error("Choisis un article.")
            return
        self.sell_item(building, item)

    def buy_item(self, building, item):
        item = item_id(item)
        quantity = general_store_available_quantity(building, item)
        if quantity == 0:
            self.show_validation_error("Cet article est épuisé.")
            return
        price = general_store_price(self.game.city, item)
        if self.game.character.money < price:
            self.show_validation_error("Tu n'as pas assez d'argent.")
            return
        if inventory_weight(self.game.character.inventory) + good_weight(item) > self.game.character.strength:
            self.show_validation_error("Ton inventaire est trop lourd.")
            return
        if not self.consume_action_time(0.1):
            return
        if not self.spend(price):
            return
        self.game.character.inventory[item] = self.game.character.inventory.get(item, 0) + 1
        if quantity is not None:
            building.inventory[item] = max(0, building.inventory.get(item, 0) - 1)
        building.current_balance += price
        record_building_sale(building, price, "merchandise_sold")
        self.set_status(f"Achat : {item_label(item)}.")
        self.show_trade(building)

    def sell_item(self, building, item):
        item = item_id(item)
        if self.game.character.inventory.get(item, 0) <= 0:
            self.show_validation_error("Tu n'as pas cet objet en stock.")
            return
        if not self.consume_action_time(0.1):
            return
        price = store_sell_price(self.game.city, item)
        self.game.character.inventory[item] -= 1
        if self.game.character.inventory[item] == 0:
            del self.game.character.inventory[item]
        self.game.character.money += price
        building.current_balance -= price
        building.inventory[item] = building.inventory.get(item, 0) + 1
        building.annual_purchases += price
        building.lifetime_expenses += price
        record_accounting_charge(building, "merchandise_purchases", price, cash=False)
        self.set_status(f"Vente : {item_label(item)}.")
        self.show_trade(building)

    def can_afford_orders(self, orders):
        total_cost = sum(quantity * price for quantity, price in orders)
        if self.game.character.money < total_cost:
            self.show_validation_error(f"Il faut {format_money(total_cost)} pour cet achat.")
            return False
        return True

    def show_validation_error(self, message):
        self.set_status(message)
        messagebox.showwarning("Donnee invalide", message)

    # Gestion ------------------------------------------------------------

    def show_management(self, building, view="accounting"):
        normalize_ranch_data(building)
        self.set_profile_return(lambda: self.show_management(building, view))
        frame = self.set_screen(f"Gestion - {building.name}")
        left = tk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        right = tk.Frame(frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(left, text=f"Gestion\n{building.name}", font=("Arial", 13, "bold")).pack(pady=(0, 10))
        tab_labels = {
            "accounting": "Comptabilité",
            "inventory": "Inventaire",
            "stock": management_stock_label(building),
            "employees": "Employés",
            "housing": "Logement",
            "upgrades": "Amélioration",
        }
        available_tabs = building_management_tabs(building, self.game)
        if view not in available_tabs:
            view = available_tabs[0] if available_tabs else "inventory"
        for tab in available_tabs:
            self.add_button(left, tab_labels.get(tab, tab), lambda selected=tab: self.show_management(building, selected))
        self.add_button(left, "Retour", lambda: self.show_building(building))

        self.render_management_view(right, building, view)

    def render_management_view(self, parent, building, view):
        if view.startswith("accounting"):
            self.render_accounting(parent, building, view)
            return
        if view == "stock":
            if building.building_type == "Saloon":
                self.render_saloon_stock(parent, building)
            elif building.building_type == "Ranch":
                self.render_ranch_herd(parent, building)
            elif building.building_type == "Cabinet médical":
                self.render_medical_stock(parent, building)
            elif building.building_type == "Mine":
                self.render_mine_production(parent, building)
            else:
                self.render_generic_production(parent, building)
            return
        if view == "inventory":
            self.render_common_building_inventory(parent, building)
            return
        if view == "employees":
            self.render_employees(parent, building)
            return
        if view == "housing":
            self.render_building_housing(parent, building)
            return
        if view == "upgrades":
            self.render_upgrades(parent, building)
            return
        self.render_accounting(parent, building, view)

    def show_accounting(self, building):
        self.show_management(building, "accounting")

    def render_accounting(self, parent, building, view="accounting"):
        ensure_building_accounting(building, self.game.city)
        nav = tk.Frame(parent)
        nav.pack(fill=tk.X, pady=(0, 8))
        views = [
            ("Bilan", "accounting"),
            ("Bilans archivés", "accounting_balance_history"),
            ("Résultat cumulé", "accounting_current_result"),
            ("Résultats saison", "accounting_season_results"),
            ("Résultats annuels", "accounting_year_results"),
        ]
        for label, target in views:
            tk.Button(nav, text=label, command=lambda selected=target: self.show_management(building, selected)).pack(side=tk.LEFT, padx=(0, 4))

        actions = tk.Frame(parent)
        actions.pack(fill=tk.X, pady=(0, 8))
        self.add_button(actions, "Ajouter du capital", lambda: self.accounting_add_capital(building))
        self.add_button(actions, "Retirer du capital", lambda: self.accounting_remove_capital(building))
        self.add_button(actions, "Se verser des dividendes", lambda: self.accounting_pay_dividends(building))

        if view == "accounting_balance_history":
            self.render_accounting_balance_history(parent, building)
        elif view == "accounting_season_results":
            self.render_accounting_season_results(parent, building)
        elif view == "accounting_year_results":
            self.render_accounting_year_results(parent, building)
        elif view == "accounting_current_result":
            self.render_accounting_result(parent, "Résultat cumulé année en cours", accounting_current_year_lines(building))
        else:
            columns = tk.Frame(parent)
            columns.pack(fill=tk.BOTH, expand=True)
            self.accounting_column(columns, "Actif", accounting_balance_asset_lines(building))
            self.accounting_column(columns, "Passif", accounting_balance_liability_lines(building))
            errors = accounting_balance_errors(building)
            if errors:
                tk.Label(parent, text="\n".join(errors), fg="#b00000", justify=tk.LEFT).pack(fill=tk.X, pady=8)

    def render_accounting_result(self, parent, title, lines):
        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)
        products, charges, totals = split_result_lines(lines)
        self.accounting_column(columns, f"{title} - Produits", products)
        self.accounting_column(columns, f"{title} - Charges", charges)
        self.accounting_column(columns, "Total", totals)

    def render_accounting_season_results(self, parent, building):
        seasons = ensure_building_accounting(building, self.game.city)["season_results"]
        if not seasons:
            tk.Label(parent, text="Aucun résultat saisonnier archivé.").pack(anchor=tk.W)
            return
        for result in reversed(seasons[-8:]):
            self.render_accounting_result(parent, f"Résultat {result['season']} {result['year']}", result_result_lines(result))

    def render_accounting_year_results(self, parent, building):
        years = ensure_building_accounting(building, self.game.city)["annual_results"]
        if not years:
            tk.Label(parent, text="Aucun résultat annuel archivé.").pack(anchor=tk.W)
            return
        for year in sorted(years.keys(), reverse=True):
            self.render_accounting_result(parent, f"Résultat année {year}", result_result_lines(years[year]))

    def render_accounting_balance_history(self, parent, building):
        balances = ensure_building_accounting(building, self.game.city)["balance_snapshots"]
        if not balances:
            tk.Label(parent, text="Aucun bilan annuel archivé.").pack(anchor=tk.W)
            return
        for year in sorted(balances.keys(), reverse=True):
            columns = tk.LabelFrame(parent, text=f"Bilan année {year}")
            columns.pack(fill=tk.BOTH, expand=True, pady=6)
            left = tk.Frame(columns)
            left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            right = tk.Frame(columns)
            right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.accounting_lines(left, snapshot_asset_lines(balances[year]))
            self.accounting_lines(right, snapshot_liability_lines(balances[year]))

    def accounting_add_capital(self, building):
        amount = self.ask_accounting_amount("Ajouter du capital", "Montant à ajouter au capital :")
        if amount is None:
            return
        if self.game.character.money < amount:
            self.show_validation_error("Le personnage n'a pas assez de dollars.")
            return
        self.game.character.money -= amount
        accounting_capital_contribution(building, self.game.city, amount, cash_amount=amount)
        self.set_status(f"Capital ajouté : {format_money(amount)}.")
        self.show_management(building, "accounting")

    def accounting_remove_capital(self, building):
        amount = self.ask_accounting_amount("Retirer du capital", "Montant à retirer du capital :")
        if amount is None:
            return
        if accounting_remove_capital(building, self.game.city, amount):
            self.game.character.money += amount
            self.set_status(f"Capital retiré : {format_money(amount)}.")
            self.show_management(building, "accounting")
        else:
            self.show_validation_error("Caisse ou capital insuffisant.")

    def accounting_pay_dividends(self, building):
        amount = self.ask_accounting_amount("Dividendes", "Montant des dividendes :")
        if amount is None:
            return
        if accounting_pay_dividends(building, self.game.city, amount):
            self.game.character.money += amount
            self.set_status(f"Dividendes versés : {format_money(amount)}.")
            self.show_management(building, "accounting")
        else:
            self.show_validation_error("Caisse ou réserves insuffisantes.")

    def ask_accounting_amount(self, title, prompt):
        value = simpledialog.askstring(title, prompt, parent=self.root)
        if value is None:
            return None
        amount = parse_positive_money(value)
        if amount is None or amount <= 0:
            self.show_validation_error("Entre un montant positif.")
            return None
        return amount

    def accounting_column(self, parent, title, lines):
        panel = tk.LabelFrame(parent, text=title)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.accounting_lines(panel, lines)

    def accounting_lines(self, parent, lines):
        for line in lines:
            text, color = accounting_display_line(line)
            tk.Label(parent, text=text, fg=color, justify=tk.LEFT, anchor=tk.NW).pack(fill=tk.X, padx=8, pady=2)

    def show_employees(self, building):
        self.show_management(building, "employees")

    def render_employees(self, parent, building):
        tk.Label(parent, text=f"Employés - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        employee_list = tk.Listbox(parent, height=8)
        employee_list.pack(fill=tk.BOTH, expand=True, pady=8)
        current_employee_ids = employee_ids(building)
        for employee_id in current_employee_ids:
            npc = self.game.city.get_npc_by_id(employee_id)
            role = employee_role(building, employee_id)
            employee_list.insert(tk.END, f"{npc.name if npc else employee_id} | {role} | Salaire : {format_money(employee_wage(building, employee_id))}")
        if not current_employee_ids:
            employee_list.insert(tk.END, "Aucun employé.")

        actions = tk.Frame(parent)
        actions.pack(fill=tk.X, pady=12)
        fire_button = tk.Button(
            actions,
            text="Renvoyer",
            command=lambda: self.fire_selected_employee(building, employee_list),
            state=tk.DISABLED,
        )
        fire_button.pack(fill=tk.X, pady=4)
        employee_list.bind(
            "<<ListboxSelect>>",
            lambda _event: fire_button.config(state=tk.NORMAL if employee_ids(building) and employee_list.curselection() else tk.DISABLED),
        )
        for role in recruitable_roles(building):
            if can_recruit_role(building, role):
                self.add_button(actions, f"Recruter : {role}", lambda selected_role=role: self.show_recruit_candidates(building, selected_role))

    def fire_selected_employee(self, building, employee_list):
        if not employee_list.curselection() or not employee_ids(building):
            self.set_status("Sélectionne un employé.")
            return
        self.fire_employee(building, employee_list)

    def show_recruit_candidates(self, building, role):
        self.set_profile_return(lambda: self.show_recruit_candidates(building, role))
        frame = self.set_screen(f"Recruter - {role}")
        tk.Label(frame, text=f"Recruter : {role}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        available_npcs = eligible_candidates_for_role(
            self.game.city.population,
            role,
            player_has_judgement=has_skill(self.game.character, "Jugement"),
        )
        if not available_npcs:
            tk.Label(frame, text="Aucun candidat disponible pour ce poste.").pack(anchor=tk.W, pady=8)
            self.add_button(frame, "Retour", lambda: self.show_employees(building))
            return

        wage_var = tk.StringVar(value=format_price_input(default_role_wage(self.game.city, building, role)))
        wage_frame = tk.Frame(frame)
        wage_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(wage_frame, text="Salaire propose").pack(side=tk.LEFT)
        tk.Entry(wage_frame, textvariable=wage_var, width=10).pack(side=tk.LEFT, padx=8)

        candidate_list = tk.Listbox(frame, height=12)
        candidate_list.pack(fill=tk.BOTH, expand=True, pady=8)
        for npc in available_npcs:
            candidate_list.insert(tk.END, npc_candidate_label(npc))

        self.add_button(frame, "Recruter", lambda: self.recruit_employee(building, candidate_list, available_npcs, role, wage_var))
        self.add_button(frame, "Retour", lambda: self.show_employees(building))

    def recruit_employee(self, building, candidate_list, available_npcs, role, wage_var=None):
        selection = candidate_list.curselection()
        if not selection:
            self.set_status("Selectionne un candidat.")
            return

        npc = available_npcs[selection[0]]
        if not can_npc_take_role(npc, role, self.game.city.population):
            self.set_status("Ce poste ne correspond pas a ce candidat.")
            return
        if not can_recruit_role(building, role):
            self.set_status("Ce poste est deja au complet.")
            self.show_employees(building)
            return

        wage = parse_optional_money(wage_var.get() if wage_var else "", default_role_wage(self.game.city, building, role))
        if wage is None:
            self.show_validation_error("Salaire invalide.")
            return

        set_employee_contract(building, npc.npc_id, role, wage)
        npc.job = role
        npc.employer_building_id = building.building_id
        npc.income = employee_wage(building, npc.npc_id)
        ensure_building_housing_units(self.game.city, building)
        assign_employee_housing(self.game.city, building, npc)
        self.set_status(f"{npc.name} recrute comme {role}.")
        self.show_employees(building)

    def show_fire_employee(self, building):
        self.set_profile_return(lambda: self.show_fire_employee(building))
        frame = self.set_screen(f"Renvoyer - {building.name}")
        tk.Label(frame, text=f"Renvoyer - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        if not employee_ids(building):
            tk.Label(frame, text="Aucun employé à renvoyer.").pack(anchor=tk.W, pady=8)
            self.add_button(frame, "Retour", lambda: self.show_employees(building))
            return

        employee_list = tk.Listbox(frame, height=12)
        employee_list.pack(fill=tk.BOTH, expand=True, pady=8)
        for employee_id in employee_ids(building):
            npc = self.game.city.get_npc_by_id(employee_id)
            role = employee_role(building, employee_id)
            employee_list.insert(tk.END, f"{npc_candidate_label(npc) if npc else employee_id} | Poste : {role}")

        self.add_button(frame, "Renvoyer", lambda: self.fire_employee(building, employee_list))
        self.add_button(frame, "Retour", lambda: self.show_employees(building))

    def fire_employee(self, building, employee_list):
        selection = employee_list.curselection()
        if not selection:
            self.set_status("Sélectionne un employé.")
            return

        employee_id = employee_ids(building)[selection[0]]
        npc = self.game.city.get_npc_by_id(employee_id)
        remove_employee_contract(building, employee_id)
        if npc:
            clear_character_residence(self.game.city, npc)
            npc.job = "Journalier" if npc.sex == "Homme" else "Journaliere"
            npc.employer_building_id = None
            npc.income = 0
            self.set_status(f"{npc.name} a été renvoyé.")
        else:
            self.set_status("Employé renvoyé.")
        self.show_employees(building)

    def render_building_housing(self, parent, building):
        ensure_building_housing_units(self.game.city, building)
        tk.Label(parent, text=f"Logement - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        if building.building_type == "Saloon" and room_count(building) > 0:
            mode = building.production.get("housing_mode", "voyageurs")
            tk.Label(parent, text=f"Usage des chambres : {housing_mode_label(mode)}").pack(anchor=tk.W, pady=(0, 6))
            self.add_button(parent, "Réserver aux voyageurs", lambda: self.set_saloon_housing_mode(building, "voyageurs"))
            self.add_button(parent, "Location longue durée", lambda: self.set_saloon_housing_mode(building, "location"))

        units = building_housing_units(self.game.city, building)
        if not units:
            tk.Label(parent, text="Aucun logement rattaché à ce bâtiment.").pack(anchor=tk.W, pady=8)
            return

        for housing in units:
            row = tk.Frame(parent, bd=1, relief=tk.SOLID, padx=8, pady=6)
            row.pack(fill=tk.X, pady=4)
            occupant_text = ", ".join(housing.occupants) if housing.occupants else "vide"
            listed_text = "offre publique" if housing.listed and not housing.occupants else "hors offre"
            tk.Label(
                row,
                text=f"{housing_label(housing)} | occupant : {occupant_text} | {format_money(housing.rent_price)} | {listed_text}",
                anchor=tk.W,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            if self.game.character.name in housing.occupants:
                tk.Button(row, text="Libérer", command=lambda h=housing: self.leave_housing(building, h)).pack(side=tk.RIGHT)
            elif not housing.occupants:
                tk.Button(row, text="Occuper", command=lambda h=housing: self.occupy_housing(building, h)).pack(side=tk.RIGHT)

    def set_saloon_housing_mode(self, building, mode):
        building.production["housing_mode"] = mode
        ensure_building_housing_units(self.game.city, building)
        if mode == "location":
            for housing in building_housing_units(self.game.city, building, "chambre"):
                if housing.occupants == ["voyageur"]:
                    housing.occupants = []
        self.set_status(f"Usage des chambres : {housing_mode_label(mode)}.")
        self.show_management(building, "housing")

    def occupy_housing(self, building, housing):
        if housing.housing_type in MARRIED_FORBIDDEN_HOUSING_TYPES and character_is_married(self.game.city, self.game.character):
            self.show_validation_error("Ce type de logement ne convient pas aux personnes mariées.")
            return
        clear_character_residence(self.game.city, self.game.character)
        housing.occupants = [self.game.character.name]
        self.game.character.residence = housing.housing_id
        self.set_status(f"Résidence choisie : {housing_label(housing)}.")
        self.show_management(building, "housing")

    def leave_housing(self, building, housing):
        housing.occupants = []
        if self.game.character.residence == housing.housing_id:
            self.game.character.residence = None
        self.set_status("Logement libéré.")
        self.show_management(building, "housing")

    def show_text_panel(self, title, text, back_command):
        self.set_profile_return(lambda: self.show_text_panel(title, text, back_command))
        frame = self.set_screen(title)
        tk.Label(frame, text=title, font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        text_color = "#b00000" if "Debug" in title else None
        tk.Label(frame, text=text, justify=tk.LEFT, anchor=tk.NW, fg=text_color).pack(fill=tk.BOTH, expand=True)
        self.add_button(frame, "Retour", back_command)

    def show_production(self, building):
        self.show_management(building, "stock")

    def render_generic_production(self, parent, building):
        title = f"{management_stock_label(building)} - {building.name}"
        tk.Label(parent, text=title, font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        entries = {}
        notebook = ttk.Notebook(parent)
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
            tk.Label(row, text=f"{label} ({format_money(price)} pièce)", width=34, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row)
            entry.insert(0, str(building.production.get(key, 0)))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[key] = entry

        if building.building_type == "Ranch":
            tk.Label(parent, text="Les prix du bétail sont fixés au niveau national pour l'instant.").pack(anchor=tk.W, pady=6)

        self.add_button(parent, "Valider", lambda: self.save_production(building, entries))

    def render_mine_production(self, parent, building):
        tk.Label(parent, text=f"Production - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        ensure_mine_defaults(building)

        settings = tk.LabelFrame(parent, text="Organisation du travail")
        settings.pack(fill=tk.X, pady=(0, 8))
        hours_var = tk.IntVar(value=building.production.get("work_hours", 8))
        timbering_var = tk.IntVar(value=building.production.get("timbering_m", 8))

        hours_row = tk.Frame(settings)
        hours_row.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(hours_row, text="Heures de travail", width=22, anchor=tk.W).pack(side=tk.LEFT)
        for value in [8, 10, 12]:
            tk.Radiobutton(hours_row, text=f"{value}h", variable=hours_var, value=value).pack(side=tk.LEFT)

        timbering_row = tk.Frame(settings)
        timbering_row.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(timbering_row, text="Étaiement", width=22, anchor=tk.W).pack(side=tk.LEFT)
        for value in [5, 8, 10]:
            tk.Radiobutton(timbering_row, text=f"{value}m", variable=timbering_var, value=value).pack(side=tk.LEFT)

        self.add_button(settings, "Enregistrer", lambda: self.save_mine_settings(building, hours_var.get(), timbering_var.get()))

        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)
        stock_panel = tk.LabelFrame(columns, text="Stock de minerai")
        stock_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        ore_items = mine_ore_inventory_items(building)
        if not ore_items:
            tk.Label(stock_panel, text="Aucun minerai en stock.").pack(anchor=tk.W, padx=8, pady=8)
        for item, quantity in ore_items:
            row = tk.Frame(stock_panel)
            row.pack(fill=tk.X, padx=8, pady=3)
            tk.Label(row, text=f"{item_label(item)} : {format_quantity(quantity)}").pack(side=tk.LEFT, fill=tk.X, expand=True, anchor=tk.W)
            tk.Button(row, text="Convoi", command=lambda selected=item: self.sell_mine_ore(building, selected)).pack(side=tk.RIGHT)

        supply_panel = tk.LabelFrame(columns, text="Approvisionnement")
        supply_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.render_stock_purchase_row(supply_panel, building, item_label("explosifs"), "explosifs", property_good_price(self.game.city, "explosifs"))
        if "Magasin de la mine" in normalize_upgrades(building.upgrades):
            store_panel = tk.LabelFrame(supply_panel, text="Magasin de la mine")
            store_panel.pack(fill=tk.X, padx=8, pady=8)
            price_entries = {}
            for item in ["vivres_secs", "tabac", "cafe"]:
                self.render_stock_purchase_row(store_panel, building, item_label(item), item, property_good_price(self.game.city, item))
                self.render_mine_store_price_row(store_panel, building, price_entries, item)
            self.add_button(store_panel, "Enregistrer les prix", lambda: self.save_mine_store_prices(building, price_entries))

    def save_mine_settings(self, building, hours, timbering):
        old_hours = building.production.get("work_hours", 8)
        old_timbering = building.production.get("timbering_m", 8)
        old_penalty = mine_security_penalty(old_hours, old_timbering)
        new_penalty = mine_security_penalty(hours, timbering)
        building.production["work_hours"] = hours
        building.production["timbering_m"] = timbering
        building.production["discontent"] = max(
            0,
            building.production.get("discontent", 0)
            + max(0, mine_discontent_delta(hours) - mine_discontent_delta(old_hours)),
        )
        security = building.production.get("security", 50)
        security -= max(0, new_penalty - old_penalty)
        if role_count(building, "Ingénieur") > 0:
            security += max(0, 5 - building.production.get("engineer_security_bonus", 0))
            building.production["engineer_security_bonus"] = 5
        building.production["security"] = max(0, min(100, security))
        self.set_status(f"Mine réglée : {hours}h, étayage {timbering}m.")
        self.show_management(building, "stock")

    def render_mine_store_price_row(self, parent, building, entries, item):
        row = tk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(row, text=f"Prix {item_label(item)}", width=18, anchor=tk.W).pack(side=tk.LEFT)
        entry = tk.Entry(row)
        entry.insert(0, format_price_input(building.production.get("mine_store_prices", {}).get(item, property_good_price(self.game.city, item))))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entries[item] = entry

    def save_mine_store_prices(self, building, entries):
        prices = building.production.setdefault("mine_store_prices", {})
        for item, entry in entries.items():
            price = parse_positive_money(entry.get())
            if price is None:
                replace_entry_text(entry, "0")
                self.show_validation_error("Entre un prix positif.")
                return
            prices[item] = price
        self.set_status("Prix du magasin de la mine enregistrés.")
        self.show_management(building, "stock")

    def sell_mine_ore(self, building, item):
        quantity = building.inventory.get(item, 0)
        if quantity <= 0:
            self.show_validation_error("Aucun minerai à vendre.")
            return
        result = sell_to_national_market(self.game, building, item, quantity)
        if not result["success"]:
            self.show_validation_error(result["message"])
            return
        self.set_status(f"Convoi vendu : {format_quantity(quantity)} {item_label(item)} pour {format_money(result['amount'])}.")
        self.show_management(building, "stock")

    def show_saloon_stock(self, building):
        self.show_management(building, "stock")

    def render_saloon_stock(self, parent, building):
        tk.Label(parent, text=f"Stock et prix - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        self.render_saloon_stock_v2(parent, building)
        return

        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)

        buy_column = tk.LabelFrame(columns, text="Stock")
        buy_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.render_stock_purchase_row(buy_column, building, "Fût de bière", "fut_biere", property_good_price(self.game.city, "fut_biere"))

        price_column = tk.LabelFrame(columns, text="Prix")
        price_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(price_column, text="Bière").pack(anchor=tk.W, padx=8, pady=6)
        price_entry = tk.Entry(price_column)
        price_entry.insert(0, str(building.production.get("prix_biere", 0.5)))
        price_entry.pack(fill=tk.X, padx=8, pady=6)
        self.add_button(price_column, "Enregistrer le prix", lambda: self.save_beer_price(building, price_entry))

    def render_saloon_stock_v2(self, parent, building):
        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)

        stock_column = tk.LabelFrame(columns, text="Stock")
        stock_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.render_saloon_storage_bar(stock_column, building)
        self.render_stock_purchase_row(stock_column, building, "Fût de bière", "fut_biere", property_good_price(self.game.city, "fut_biere"))
        if "Cuisine" in normalize_upgrades(building.upgrades):
            self.render_stock_purchase_row(stock_column, building, item_label("vivres_secs"), "vivres_secs", property_good_price(self.game.city, "vivres_secs"))
        self.render_building_inventory_transfer(stock_column, building)

        price_column = tk.LabelFrame(columns, text="Prix")
        price_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        price_entries = {}
        self.render_price_row(price_column, building, price_entries, "prix_biere", "Bière")
        if "Cuisine" in normalize_upgrades(building.upgrades):
            self.render_price_row(price_column, building, price_entries, "prix_repas", "Repas")
        if role_count(building, "Hotesse") > 0:
            self.render_price_row(price_column, building, price_entries, "prix_hotesse", "Hôtesse")
        if room_count(building) > 0:
            self.render_price_row(price_column, building, price_entries, "prix_chambre", "Chambre")
        if "Salle de bain" in normalize_upgrades(building.upgrades):
            self.render_price_row(price_column, building, price_entries, "prix_bain", "Bain")
        self.add_button(price_column, "Enregistrer les prix", lambda: self.save_saloon_prices(building, price_entries))

    def render_saloon_storage_bar(self, parent, building):
        used = saloon_storage_used(building)
        capacity = saloon_storage_capacity(building)
        row = tk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=(8, 12))
        tk.Label(row, text="Stockage").pack(anchor=tk.W)
        ttk.Progressbar(row, maximum=capacity, value=min(used, capacity)).pack(fill=tk.X, pady=4)

    def render_price_row(self, parent, building, entries, key, label):
        row = tk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(row, text=label, width=14, anchor=tk.W).pack(side=tk.LEFT)
        entry = tk.Entry(row)
        entry.insert(0, format_price_input(building.production.get(key, default_saloon_price(key))))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entries[key] = entry

    def render_stock_purchase_row(self, parent, building, label, inventory_key, unit_price):
        row = tk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(row, text=f"{label} | stock : {saloon_inventory_quantity(building, inventory_key)} | achat : {format_money(unit_price)}").pack(side=tk.LEFT, fill=tk.X, expand=True, anchor=tk.W)
        tk.Button(row, text="Acheter", command=lambda: self.ask_stock_purchase(building, inventory_key, label, unit_price)).pack(side=tk.RIGHT)

    def ask_stock_purchase(self, building, inventory_key, label, unit_price):
        quantity = simple_quantity_dialog(self.root, f"Acheter {label}", "Quantité à acheter :")
        if quantity is None:
            return
        if not building_has_storage_space(building, inventory_key, quantity):
            self.show_validation_error("Le stock du bâtiment est plein.")
            return
        total_cost = quantity * unit_price
        if building.current_balance < total_cost:
            self.show_validation_error(f"La caisse du bÃ¢timent doit contenir {format_money(total_cost)} pour cet achat.")
            return
        building.inventory[inventory_key] = building.inventory.get(inventory_key, 0) + quantity
        building.annual_purchases += total_cost
        building.lifetime_expenses += total_cost
        record_accounting_charge(building, "raw_material_purchases", total_cost)
        building.account_journal.append(f"Achat stock - {label} : {total_cost}")
        self.set_status(f"Achat : {quantity} {label}.")
        self.show_management(building, "stock")

    def save_saloon_stock(self, building, buy_entry, price_entry):
        buy_quantity = parse_positive_int(buy_entry.get())
        beer_price = parse_positive_int(price_entry.get())
        if buy_quantity is None or beer_price is None:
            self.show_validation_error("Entre un nombre entier positif.")
            return
        building.production["commande_biere"] = buy_quantity
        building.production["prix_biere"] = beer_price
        self.set_status("Stock enregistré.")
        self.show_management(building)

    def save_beer_price(self, building, price_entry):
        self.save_saloon_prices(building, {"prix_biere": price_entry})

    def save_saloon_prices(self, building, entries):
        for key, entry in entries.items():
            price = parse_positive_money(entry.get())
            if price is None:
                replace_entry_text(entry, "0")
                self.show_validation_error("Entre un nombre positif.")
                return
            building.production[key] = price
        self.set_status("Prix enregistrés.")
        self.show_management(building, "stock")

    def show_ranch_herd(self, building):
        self.show_management(building, "stock")

    def render_ranch_herd(self, parent, building):
        ensure_bulls(building)
        tk.Label(parent, text=f"{management_stock_label(building)} - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        total_cattle = cattle_head_count(building)
        tk.Label(parent, text=f"Nombre de têtes de bétail : {total_cattle}", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)
        bull_panel = tk.LabelFrame(columns, text="Taureaux")
        bull_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        bulls = building.production.get("bulls", [])
        if not bulls:
            tk.Label(bull_panel, text="Aucun taureau.").pack(anchor=tk.W, padx=8, pady=8)
        for bull in bulls:
            tk.Label(
                bull_panel,
                text=f"{bull.get('nom', 'Taureau')} - {bull.get('age', '?')} ans",
                anchor=tk.W,
            ).pack(fill=tk.X, padx=8, pady=3)

        if "Grange" in normalize_upgrades(building.upgrades):
            self.render_barn_inventory(columns, building)

        if self.debug_mode:
            debug_panel = tk.LabelFrame(parent, text="Debug")
            debug_panel.pack(fill=tk.X, pady=10)
            self.add_button(debug_panel, "Ajouter du bétail", lambda: self.debug_add_cattle(building))
            self.add_button(debug_panel, "Générer un taureau", lambda: self.debug_generate_bull(building))

    def debug_add_cattle(self, building):
        quantity = simple_quantity_dialog(self.root, "Debug - ajouter du bétail", "Nombre de têtes à ajouter :")
        if quantity is None:
            return
        building.production["head_count"] = cattle_head_count(building) + quantity
        self.set_status(f"Debug : {quantity} têtes de bétail ajoutées.")
        self.show_management(building, "stock")

    def render_barn_inventory(self, parent, building):
        barn_panel = tk.LabelFrame(parent, text="Grange")
        barn_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        forage = min(building.inventory.get("fourrage", 0), RANCH_BARN_CAPACITY)
        food = min(building.inventory.get("vivres_secs", 0), RANCH_BARN_CAPACITY)
        tk.Label(barn_panel, text="Fourrage").pack(anchor=tk.W, padx=8, pady=(8, 0))
        ttk.Progressbar(barn_panel, maximum=RANCH_BARN_CAPACITY, value=forage).pack(fill=tk.X, padx=8, pady=4)
        tk.Label(barn_panel, text=f"Vivres : {food}/{RANCH_BARN_CAPACITY}").pack(anchor=tk.W, padx=8, pady=(8, 0))
        ttk.Progressbar(barn_panel, maximum=RANCH_BARN_CAPACITY, value=food).pack(fill=tk.X, padx=8, pady=4)
        self.render_building_inventory_transfer(barn_panel, building)

    def render_common_building_inventory(self, parent, building):
        tk.Label(parent, text=f"Inventaire - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)

        list_panel = tk.LabelFrame(columns, text="Biens stockés")
        list_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        inventory_items = [
            (item, quantity)
            for item, quantity in sorted(building.inventory.items(), key=lambda entry: item_label(entry[0]))
            if quantity
        ]
        item_list = tk.Listbox(list_panel, height=min(12, max(4, len(inventory_items))))
        scrollbar = tk.Scrollbar(list_panel, orient=tk.VERTICAL, command=item_list.yview)
        item_list.configure(yscrollcommand=scrollbar.set)
        item_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        if len(inventory_items) > 12:
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8)
        for item, quantity in inventory_items:
            item_list.insert(tk.END, f"{item_label(item)} : {format_quantity(quantity)}")
        if not inventory_items:
            item_list.insert(tk.END, "Inventaire vide.")

        detail_panel = tk.LabelFrame(columns, text="Détail")
        detail_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_text = tk.Text(detail_panel, height=10, wrap=tk.WORD)
        detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        detail_text.config(state=tk.DISABLED)

        def selected_item():
            selection = item_list.curselection()
            if not selection or not inventory_items:
                return None
            return inventory_items[selection[0]][0]

        def refresh_detail(_event=None):
            item = selected_item()
            detail_text.config(state=tk.NORMAL)
            detail_text.delete("1.0", tk.END)
            if item:
                detail_text.insert(tk.END, f"{item_label(item)}\nQuantité : {format_quantity(building.inventory.get(item, 0))}")
                if self.debug_mode:
                    detail_text.insert(tk.END, "\n\nDEBUG\n")
                    detail_text.insert(tk.END, pformat(item_definition(item)))
            detail_text.config(state=tk.DISABLED)

        item_list.bind("<<ListboxSelect>>", refresh_detail)

        actions = tk.Frame(parent)
        actions.pack(fill=tk.X, pady=8)
        self.add_button(actions, "Déposer depuis l'inventaire du joueur", lambda: self.choose_inventory_transfer_item(building, "deposit"))
        self.add_button(actions, "Prendre dans le bâtiment", lambda: self.choose_inventory_transfer_item(building, "take"))

    def choose_inventory_transfer_item(self, building, mode):
        source = self.game.character.inventory if mode == "deposit" else building.inventory
        items = allowed_inventory_items(source, building)
        if not items:
            self.show_validation_error("Aucun bien compatible.")
            return
        popup = tk.Toplevel(self.root)
        popup.title("Transfert d'inventaire")
        popup.transient(self.root)
        popup.grab_set()
        tk.Label(popup, text="Choisis un bien").pack(anchor=tk.W, padx=10, pady=(10, 4))
        item_list = tk.Listbox(popup, height=min(12, max(4, len(items))))
        scrollbar = tk.Scrollbar(popup, orient=tk.VERTICAL, command=item_list.yview)
        item_list.configure(yscrollcommand=scrollbar.set)
        item_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        if len(items) > 12:
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        for item in items:
            item_list.insert(tk.END, f"{item_label(item)} : {format_quantity(source.get(item, 0))}")

        def confirm():
            if not item_list.curselection():
                return
            item = items[item_list.curselection()[0]]
            popup.destroy()
            self.ask_inventory_transfer(building, item, mode)

        tk.Button(popup, text="Choisir", command=confirm).pack(fill=tk.X, padx=10, pady=(0, 6))
        tk.Button(popup, text="Annuler", command=popup.destroy).pack(fill=tk.X, padx=10, pady=(0, 10))

    def render_building_inventory_transfer(self, parent, building):
        transfer_panel = tk.LabelFrame(parent, text="Transferts")
        transfer_panel.pack(fill=tk.BOTH, expand=True, padx=8, pady=10)

        player_items = allowed_inventory_items(self.game.character.inventory, building)
        building_items = allowed_inventory_items(building.inventory, building)

        tk.Label(transfer_panel, text="Déposer").pack(anchor=tk.W, padx=8, pady=(6, 2))
        if not player_items:
            tk.Label(transfer_panel, text="Aucun objet compatible.").pack(anchor=tk.W, padx=8)
        for item in player_items:
            self.render_inventory_transfer_row(transfer_panel, building, item, "deposit")

        tk.Label(transfer_panel, text="Prendre").pack(anchor=tk.W, padx=8, pady=(10, 2))
        if not building_items:
            tk.Label(transfer_panel, text="Aucun objet compatible.").pack(anchor=tk.W, padx=8)
        for item in building_items:
            self.render_inventory_transfer_row(transfer_panel, building, item, "take")

    def render_inventory_transfer_row(self, parent, building, item, mode):
        source = self.game.character.inventory if mode == "deposit" else building.inventory
        quantity = source.get(item, 0)
        row = tk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(row, text=f"{item_label(item)} : {format_quantity(quantity)}", anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        label = "Déposer" if mode == "deposit" else "Prendre"
        tk.Button(row, text=label, command=lambda: self.ask_inventory_transfer(building, item, mode)).pack(side=tk.RIGHT)

    def ask_inventory_transfer(self, building, item, mode):
        source = self.game.character.inventory if mode == "deposit" else building.inventory
        available = source.get(item, 0)
        quantity = simple_item_quantity_dialog(self.root, f"{'Déposer' if mode == 'deposit' else 'Prendre'} {item_label(item)}", "Quantité :", item, available)
        if quantity is None:
            return
        if mode == "deposit":
            self.deposit_item_to_building(building, item, quantity)
        else:
            self.take_item_from_building(building, item, quantity)

    def deposit_item_to_building(self, building, item, quantity):
        item = item_id(item)
        if not building_accepts_item(building, item):
            self.show_validation_error("Cet inventaire n'accepte pas ce type d'objet.")
            return
        if not building_has_storage_space(building, item, quantity):
            self.show_validation_error("Il n'y a pas assez de place dans cet inventaire.")
            return
        if not transfer_inventory_item(self.game.character.inventory, building.inventory, item, quantity):
            self.show_validation_error("Tu ne possèdes pas cette quantité.")
            return
        self.set_status(f"Dépôt : {format_quantity(quantity)} {item_label(item)}.")
        self.show_management(building, "stock")

    def take_item_from_building(self, building, item, quantity):
        item = item_id(item)
        added_weight = quantity * good_weight(item)
        if inventory_weight(self.game.character.inventory) + added_weight > self.game.character.strength:
            self.show_validation_error("Tu ne peux pas porter autant.")
            return
        if not transfer_inventory_item(building.inventory, self.game.character.inventory, item, quantity):
            self.show_validation_error("Le bâtiment ne possède pas cette quantité.")
            return
        self.set_status(f"Retrait : {format_quantity(quantity)} {item_label(item)}.")
        self.show_management(building, "stock")

    def debug_generate_bull(self, building):
        bull = random_bull_market()[0]
        building.production.setdefault("bulls", []).append(bull)
        self.set_status(f"Debug : taureau généré ({bull['nom']}).")
        self.show_management(building, "stock")

    def render_medical_stock(self, parent, building):
        tk.Label(parent, text=f"Pharmacie et convalescence - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        columns = tk.Frame(parent)
        columns.pack(fill=tk.BOTH, expand=True)

        has_convalescence = medical_bed_count(building) > 0
        has_laboratory = "Laboratoire" in normalize_upgrades(building.upgrades)

        if has_convalescence:
            patients_panel = tk.LabelFrame(columns, text="Patients en convalescence")
            patients_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
            patients = sorted(medical_patients(self.game.city.population), key=health_severity, reverse=True)
            if not patients:
                tk.Label(patients_panel, text="Aucun patient grave pour le moment.").pack(anchor=tk.W, padx=8, pady=8)
            for patient in patients:
                tk.Label(patients_panel, text=f"{patient.name} - {patient.condition}", anchor=tk.W).pack(fill=tk.X, padx=8, pady=3)

        inventory_panel = tk.LabelFrame(columns, text="Inventaire")
        inventory_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(inventory_panel, text=f"Remèdes : {building.inventory.get('remede', 0)}/{MEDICAL_PHARMACY_CAPACITY}").pack(anchor=tk.W, padx=8, pady=4)
        if has_laboratory:
            tk.Label(inventory_panel, text=f"Plantes médicinales : {building.inventory.get('plantes_medicinales', 0)}").pack(anchor=tk.W, padx=8, pady=4)
        self.add_button(inventory_panel, f"Commander un remède ({format_money(property_good_price(self.game.city, 'remede'))})", lambda: self.buy_medical_good(building, "remede"))
        if has_laboratory:
            self.add_button(inventory_panel, "Déposer une plante", lambda: self.deposit_medical_plant(building))
        self.render_building_inventory_transfer(inventory_panel, building)

        price_panel = tk.LabelFrame(columns, text="Tarifs")
        price_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        entries = {}
        price_rows = [
            ("tarif_blessure", "Blessure"),
            ("tarif_blessure_grave", "Blessure grave"),
            ("tarif_maladie", "Maladie"),
        ]
        if has_convalescence:
            price_rows.append(("tarif_convalescence", "Séjour en convalescence"))
        for key, label in price_rows:
            self.render_price_row(price_panel, building, entries, key, label)
        self.add_button(price_panel, "Enregistrer les tarifs", lambda: self.save_medical_prices(building, entries))

    def buy_medical_good(self, building, item):
        item = item_id(item)
        if item == "remede" and building.inventory.get("remede", 0) >= MEDICAL_PHARMACY_CAPACITY:
            self.show_validation_error("La pharmacie est pleine.")
            return
        price = property_good_price(self.game.city, item)
        if building.current_balance < price:
            self.show_validation_error(f"La caisse du bÃ¢timent doit contenir {format_money(price)} pour cet achat.")
            return
        building.inventory[item] = building.inventory.get(item, 0) + 1
        building.annual_purchases += price
        building.lifetime_expenses += price
        record_accounting_charge(building, "raw_material_purchases", price)
        building.account_journal.append(f"Achat stock - {item_label(item)} : {price}")
        self.set_status(f"Achat : {item_label(item)}.")
        self.show_management(building, "stock")

    def deposit_medical_plant(self, building):
        if self.game.character.inventory.get("plantes_medicinales", 0) <= 0:
            self.show_validation_error("Tu n'as pas de plante médicinale.")
            return
        self.game.character.inventory["plantes_medicinales"] -= 1
        if self.game.character.inventory["plantes_medicinales"] <= 0:
            self.game.character.inventory.pop("plantes_medicinales", None)
        building.inventory["plantes_medicinales"] = building.inventory.get("plantes_medicinales", 0) + 1
        self.set_status("Une plante médicinale a été déposée.")
        self.show_management(building, "stock")

    def save_medical_prices(self, building, entries):
        for key, entry in entries.items():
            value = parse_positive_money(entry.get())
            if value is None:
                self.show_validation_error("Entre un prix positif.")
                return
            building.production[key] = value
        self.set_status("Tarifs médicaux enregistrés.")
        self.show_management(building, "stock")

    def save_production(self, building, entries):
        new_values = {}
        for key, entry in entries.items():
            value = parse_positive_int(entry.get())
            if value is None:
                replace_entry_text(entry, "0")
                self.show_validation_error("Entre un nombre entier positif.")
                return
            new_values[key] = value

        if not self.production_orders_are_valid(building, new_values, entries):
            return

        for key, entry in entries.items():
            building.production[key] = new_values[key]
        self.set_status(f"{management_stock_label(building)} enregistré.")
        self.show_management(building)

    def production_orders_are_valid(self, building, values, entries):
        if building.building_type == "Saloon":
            orders = [
                (values.get("commande_biere", 0), property_good_price(self.game.city, "fut_biere")),
                (values.get("commande_vivres_secs", 0), property_good_price(self.game.city, "vivres_secs")),
            ]
            if not self.can_afford_orders(orders):
                for key in ["commande_biere", "commande_vivres_secs"]:
                    if key in entries:
                        replace_entry_text(entries[key], "0")
                return False
            return True

        return True

    def show_upgrades(self, building):
        self.show_management(building, "upgrades")

    def render_upgrades(self, parent, building):
        tk.Label(parent, text=f"Amelioration - {building.name}", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        self.render_upgrade_catalog(self.scrollable_area(parent), building)
        return
        added_any = False
        if building.building_type == "Saloon":
            normalized_upgrades = normalize_upgrades(building.upgrades)
            for upgrade, cost, limit in SALOON_LIMITED_UPGRADES:
                owned_count = normalized_upgrades.count(upgrade)
                if owned_count < limit and saloon_major_upgrade_count(building) < saloon_major_upgrade_limit(building):
                    label = f"{upgrade} - {format_money(cost)}"
                    if limit > 1:
                        label = f"{upgrade} ({owned_count}/{limit}) - {format_money(cost)}"
                    self.add_button(parent, label, lambda u=upgrade, c=cost: self.add_saloon_limited_upgrade(building, u, c))
                    added_any = True
            for key, label, cost in SALOON_EXTRA_FEATURES:
                if not building.features.get(key):
                    self.add_button(parent, f"{label} - {format_money(cost)}", lambda k=key, l=label, c=cost: self.add_feature(building, k, l, c))
                    added_any = True
        elif building.building_type == "Ranch":
            for upgrade, cost, repeatable in RANCH_UPGRADES:
                if repeatable or upgrade not in building.upgrades:
                    label = f"{upgrade} - {format_money(cost)}"
                    if repeatable:
                        label = f"{upgrade} x{building.upgrades.count(upgrade) + 1} - {format_money(cost)}"
                    self.add_button(parent, label, lambda u=upgrade, c=cost: self.add_ranch_upgrade(building, u, c))
                    added_any = True
        if not added_any:
            tk.Label(parent, text="Aucune amélioration disponible pour le moment.").pack(anchor=tk.W, pady=8)

    def render_upgrade_catalog(self, parent, building):
        if building.building_type == "Saloon":
            tk.Label(
                parent,
                text=f"Pièces construites : {saloon_major_upgrade_count(building)}/{saloon_major_upgrade_limit(building)}",
                anchor=tk.W,
            ).pack(fill=tk.X, pady=(0, 8))
            upgrades = SALOON_UPGRADES
        elif building.building_type == "Ranch":
            upgrades = RANCH_UPGRADES
        elif building.building_type == "Cabinet médical":
            tk.Label(
                parent,
                text=f"Lits de convalescence : {medical_bed_count(building)}/10",
                anchor=tk.W,
            ).pack(fill=tk.X, pady=(0, 8))
            upgrades = MEDICAL_UPGRADES
        elif building.building_type == "General Store":
            upgrades = GENERAL_STORE_UPGRADES
        elif building.building_type == "Barber shop":
            upgrades = BARBER_UPGRADES
        elif building.building_type == "Mine":
            upgrades = MINE_UPGRADES
        else:
            upgrades = []

        if not upgrades:
            tk.Label(parent, text="Aucune amélioration disponible pour le moment.").pack(anchor=tk.W, pady=8)
            return

        for upgrade in upgrades:
            self.render_upgrade_card(parent, building, upgrade)

    def render_upgrade_card(self, parent, building, upgrade):
        row = tk.Frame(parent, bd=1, relief=tk.SOLID, padx=8, pady=8)
        row.pack(fill=tk.X, pady=5)

        left = tk.Frame(row)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        title = upgrade["name"]
        count = upgrade_count(building, title)
        limit = upgrade_limit(building, upgrade)
        if limit is not None and limit > 1:
            title = f"{title} x{count}/{limit}"
        elif upgrade.get("repeatable") and count > 0:
            title = f"{title} x{count}"

        tk.Label(left, text=title, font=("Arial", 11, "bold"), anchor=tk.W).pack(fill=tk.X)
        tk.Label(left, text=upgrade["description"], wraplength=520, justify=tk.LEFT, anchor=tk.W).pack(fill=tk.X, pady=(2, 0))

        action_area = tk.Frame(row)
        action_area.pack(side=tk.RIGHT, padx=(10, 0))
        state = self.upgrade_state_for_player(building, upgrade)
        if state == "built":
            tk.Label(action_area, text="Construit", fg="#1f7a1f", font=("Arial", 10, "bold")).pack()
        elif state == "unavailable":
            tk.Label(action_area, text="Indisponible", fg="#777777", font=("Arial", 10, "bold")).pack()
        else:
            tk.Button(
                action_area,
                text=f"Construire\n{format_money(upgrade['cost'])}",
                command=lambda u=upgrade: self.add_upgrade_from_data(building, u),
                width=14,
            ).pack()

    def add_upgrade_from_data(self, building, upgrade):
        if upgrade["kind"] == "feature":
            self.add_feature(building, upgrade["key"], upgrade["name"], upgrade["cost"])
            return
        if upgrade["building_type"] == "Saloon":
            self.add_saloon_upgrade(building, upgrade)
            return
        if upgrade["building_type"] == "Cabinet médical":
            self.add_medical_upgrade(building, upgrade)
            return
        if upgrade["building_type"] == "General Store":
            self.add_upgrade(building, upgrade["name"], upgrade["cost"], allow_duplicate=False)
            self.show_management(building, "upgrades")
            return
        if upgrade["building_type"] == "Barber shop":
            self.add_upgrade(building, upgrade["name"], upgrade["cost"], allow_duplicate=False)
            self.show_management(building, "upgrades")
            return
        if upgrade["building_type"] == "Mine":
            self.add_mine_upgrade(building, upgrade)
            return
        self.add_ranch_upgrade(building, upgrade["name"], upgrade["cost"])

    def add_mine_upgrade(self, building, upgrade):
        if self.upgrade_state_for_player(building, upgrade) != "available":
            self.set_status("Cette amélioration n'est pas disponible.")
            self.show_management(building, "upgrades")
            return
        if not self.add_upgrade(building, upgrade["name"], upgrade["cost"], allow_duplicate=upgrade.get("repeatable", False)):
            return
        if upgrade["name"] == "Baraquements":
            building.production["discontent"] = max(0, building.production.get("discontent", 0) - 5)
            ensure_building_housing_units(self.game.city, building)
        self.show_management(building, "upgrades")

    def upgrade_state_for_player(self, building, upgrade):
        if building.building_type != "Mine" or not upgrade.get("requires_engineer"):
            return upgrade_state(building, upgrade)
        if mine_has_engineer_access(self.game, building):
            local_upgrade = dict(upgrade)
            local_upgrade.pop("requires_engineer", None)
            return upgrade_state(building, local_upgrade)
        return upgrade_state(building, upgrade)

    def add_medical_upgrade(self, building, upgrade):
        if upgrade_count(building, upgrade["name"]) >= upgrade.get("limit", 1):
            self.set_status("Amélioration déjà au maximum.")
            return
        if not self.spend_building_money_for_upgrade(building, upgrade["cost"]):
            return
        building.upgrades.append(upgrade["name"])
        building.investment_value += upgrade["cost"]
        if upgrade["name"] == "Salle de convalescence":
            building.production["convalescence_beds"] = medical_bed_count(building)
        update_medical_building_name(building)
        self.set_status(f"Amélioration construite : {upgrade['name']}.")
        self.show_management(building, "upgrades")

    def show_saloon_upgrades(self, building):
        self.show_management(building, "upgrades")

    def add_saloon_limited_upgrade(self, building, upgrade, cost):
        upgrade_limit = saloon_upgrade_limit(upgrade)
        if normalize_upgrades(building.upgrades).count(upgrade) >= upgrade_limit:
            self.set_status("Amélioration déjà au maximum.")
            return
        if saloon_major_upgrade_count(building) >= saloon_major_upgrade_limit(building):
            self.set_status("Le Saloon ne peut avoir que deux grandes améliorations.")
            return
        self.add_upgrade(building, upgrade, cost, allow_duplicate=True)
        self.show_management(building, "upgrades")

    def add_saloon_upgrade(self, building, upgrade):
        if upgrade_state(building, upgrade) != "available":
            self.set_status("Cette amélioration n'est pas disponible.")
            self.show_management(building, "upgrades")
            return
        self.add_upgrade(building, upgrade["name"], upgrade["cost"], allow_duplicate=upgrade.get("repeatable", False))
        self.show_management(building, "upgrades")

    def show_ranch_upgrades(self, building):
        self.show_management(building, "upgrades")

    def add_ranch_upgrade(self, building, upgrade, cost):
        self.add_upgrade(building, upgrade, cost, allow_duplicate=upgrade == "Baraquements")
        self.show_management(building, "upgrades")

    def add_upgrade(self, building, upgrade, cost, allow_duplicate=False):
        if upgrade in building.upgrades and not allow_duplicate:
            self.set_status("Amélioration déjà présente.")
            return False
        if not self.spend_building_money_for_upgrade(building, cost):
            return False
        building.upgrades.append(upgrade)
        building.investment_value += cost
        building.account_journal.append(f"Amélioration : {upgrade} (-{format_money(cost)})")
        self.set_status(f"Amélioration ajoutée : {upgrade}.")
        return True

    def add_feature(self, building, key, label, cost):
        if building.features.get(key):
            self.set_status("Amélioration déjà présente.")
            return False
        if not self.spend_building_money_for_upgrade(building, cost):
            return False
        building.features[key] = True
        building.investment_value += cost
        building.account_journal.append(f"Amélioration : {label} (-{format_money(cost)})")
        self.set_status(f"Amélioration ajoutée : {label}.")
        self.show_management(building, "upgrades")
        return True

    def spend_building_money_for_upgrade(self, building, cost):
        """Les améliorations sont optionnelles : elles ne peuvent pas créer de découvert."""
        if building.current_balance < cost:
            self.show_validation_error(
                f"La caisse du bâtiment ne suffit pas : {format_money(cost)} nécessaires, {format_money(building.current_balance)} disponibles."
            )
            return False
        building.current_balance -= cost
        return True

    # Construction -------------------------------------------------------

    def show_construction(self):
        self.set_profile_return(self.show_construction)
        frame = self.set_screen("Construire")
        tk.Label(frame, text="Construire", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))

        for building_type, data in BUILDING_CATALOG.items():
            if data.get("constructible", True) is False:
                continue
            self.add_button(
                frame,
                f"{building_type} - {format_money(data['base_cost'])}",
                lambda selected_type=building_type: self.show_construct_name(selected_type),
            )
        self.add_button(frame, "Retour", self.show_city)

    def show_construct_name(self, building_type):
        self.set_profile_return(lambda: self.show_construct_name(building_type))
        data = BUILDING_CATALOG[building_type]
        if building_type == "Mine":
            self.show_mine_claim_selection()
            return
        if building_type == "Ranch" and player_owns_ranch(self.game):
            self.show_validation_error("Tu possèdes déjà un ranch.")
            self.show_construction()
            return
        if building_type == "Cabinet médical" and not has_skill(self.game.character, "Médecine"):
            self.show_validation_error("Il faut la compétence Médecine pour ouvrir un cabinet médical.")
            self.show_construction()
            return
        if self.game.character.money < data["base_cost"]:
            self.set_status("Tu n'as pas assez d'argent.")
            return

        frame = self.set_screen(f"Construire {building_type}")
        tk.Label(frame, text="Nom du bâtiment", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        entry = tk.Entry(frame)
        entry.insert(0, default_building_name(building_type, self.game.character))
        entry.pack(fill=tk.X, pady=8)
        self.add_button(frame, "Valider", lambda: self.construct_building(building_type, entry.get().strip() or building_type))
        self.add_button(frame, "Retour", self.show_construction)

    def show_mine_claim_selection(self):
        self.set_profile_return(self.show_mine_claim_selection)
        claims = getattr(self.game.character, "mineral_claims", []) or []
        if not claims:
            self.show_validation_error("Tu dois d'abord découvrir et revendiquer un filon.")
            self.show_construction()
            return

        frame = self.set_screen("Construire une mine")
        tk.Label(frame, text="Choisir un filon", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        claim_list = tk.Listbox(frame, height=10)
        claim_list.pack(fill=tk.BOTH, expand=True, pady=8)
        for claim in claims:
            claim_list.insert(tk.END, deposit_label(claim))
        self.add_button(frame, "Suivant", lambda: self.show_mine_name(claim_list, claims))
        self.add_button(frame, "Retour", self.show_construction)

    def show_mine_name(self, claim_list, claims):
        selection = claim_list.curselection()
        if not selection:
            self.set_status("Choisis un filon.")
            return
        claim = claims[selection[0]]
        self.set_profile_return(lambda: self.show_mine_name(claim_list, claims))
        frame = self.set_screen("Nom de la mine")
        tk.Label(frame, text="Nom de la mine", font=("Arial", 15, "bold")).pack(anchor=tk.W, pady=(0, 10))
        tk.Label(frame, text=deposit_label(claim), anchor=tk.W).pack(fill=tk.X, pady=(0, 8))
        entry = tk.Entry(frame)
        entry.insert(0, default_building_name("Mine", self.game.character))
        entry.pack(fill=tk.X, pady=8)
        self.add_button(frame, "Valider", lambda: self.construct_building("Mine", entry.get().strip() or "Mine", claim.get("deposit_id")))
        self.add_button(frame, "Retour", self.show_mine_claim_selection)

    def construct_building(self, building_type, building_name, deposit_id=None):
        data = BUILDING_CATALOG[building_type]
        selected_claim = None
        if building_type == "Mine":
            selected_claim = next(
                (claim for claim in getattr(self.game.character, "mineral_claims", []) if claim.get("deposit_id") == deposit_id),
                None,
            )
            if not selected_claim:
                self.show_validation_error("Filon introuvable dans tes revendications.")
                self.show_construction()
                return
        if building_type == "Ranch" and player_owns_ranch(self.game):
            self.show_validation_error("Tu possèdes déjà un ranch.")
            self.show_construction()
            return
        if building_type == "Cabinet médical" and not has_skill(self.game.character, "Médecine"):
            self.show_validation_error("Il faut la compétence Médecine pour ouvrir un cabinet médical.")
            self.show_construction()
            return
        if self.game.character.money < data["base_cost"]:
            self.show_validation_error("Tu n'as pas assez d'argent.")
            return
        if not self.spend(data["base_cost"]):
            return

        existing_ids = {building.building_id for building in self.game.city.buildings}
        building_id = make_building_id(building_type, existing_ids)
        hidden_stats = deepcopy(data.get("hidden_stats", {}))
        if selected_claim:
            selected_claim = remove_claim(self.game.character, deposit_id)
            hidden_stats["deposit"] = selected_claim
            mark_deposit_mined(self.game.city, selected_claim.get("deposit_id"), building_id)
        new_building = create_building_for_construction(
            building_type,
            building_id,
            building_name,
            self.game.character.name,
            hidden_stats=hidden_stats,
            under_construction=True,
        )
        new_building.investment_value = data["base_cost"]
        new_building.account_journal = [f"Construction : {building_name} (-{format_money(data['base_cost'])})"]
        self.game.city.buildings.append(new_building)
        if building_type == "Saloon":
            self.unlock_achievement("bartender")
        if building_type == "Ranch":
            self.unlock_achievement("rancher")
        self.set_status(f"Construction lancée : {building_name}. Le bâtiment sera accessible au prochain tour.")
        self.show_city()


GOOD_CATALOG = ITEM_CATALOG
GENERAL_STORE_EXTRA_GOODS = {"materiel_prospection"}
GENERAL_STORE_GOODS = []
LIMITED_GENERAL_STORE_GOODS = {"colt_navy", "fusil_springfield", "carabine_spencer"}
WEEK_ACTION_POINTS = 14
MEDICAL_PHARMACY_CAPACITY = 10
DEBUG_ACTION_LABELS = {"Ajouter des dollars", "Claim un filon", "Voir population", "Journal du dernier tour"}
SEASONAL_MOVEMENT_COEFFICIENTS = {
    "Printemps": 1,
    "Été": 1.5,
    "Automne": 1.2,
    "Hiver": 0.5,
}
SEASONAL_COLON_COEFFICIENTS = {
    "Printemps": 1,
    "Été": 1.5,
    "Automne": 1.2,
    "Hiver": 0,
}
HEALTH_INCIDENT_PROFILES = {
    "default": {
        "blessé": 0.03,
        "blessé gravement": 0.005,
        "malade": 0.015,
    },
    "cowboy": {
        "blessé": 0.07,
        "blessé gravement": 0.02,
        "malade": 0.01,
    },
}
WEEKDAYS = [
    "Dimanche",
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
]
TRAIL_CATTLE_PRICE = BASE_MARKET_PRICES["boeuf"]

SALOON_UPGRADES = [
    {
        "building_type": "Saloon",
        "kind": "upgrade",
        "name": "Chambre",
        "description": "Permet d'accueillir des voyageurs ou de permettre à vos hôtesses de recevoir leurs clients.",
        "cost": 80,
        "limit": 2,
        "counts_as_room_choice": True,
    },
    {
        "building_type": "Saloon",
        "kind": "upgrade",
        "name": "Salle de bain",
        "description": "L'hygiène est un luxe dans l'Ouest pour lequel certains sont prêts à payer fort.",
        "cost": 50,
        "limit": 1,
        "counts_as_room_choice": True,
    },
    {
        "building_type": "Saloon",
        "kind": "upgrade",
        "name": "Cuisine",
        "description": "Permet la vente de repas chauds.",
        "cost": 60,
        "limit": 1,
        "counts_as_room_choice": True,
    },
    {
        "building_type": "Saloon",
        "kind": "upgrade",
        "name": "Cave",
        "description": "Augmente votre capacité de stockage.",
        "cost": 70,
        "limit": 1,
    },
    {
        "building_type": "Saloon",
        "kind": "feature",
        "key": "table_poker",
        "name": "Table de jeu",
        "description": "Attire plus de clients.",
        "cost": 40,
        "limit": 1,
    },
    {
        "building_type": "Saloon",
        "kind": "feature",
        "key": "piano",
        "name": "Piano",
        "description": "Attire plus de clients.",
        "cost": 45,
        "limit": 1,
    },
    {
        "building_type": "Saloon",
        "kind": "upgrade",
        "name": "Décoration et luminaire",
        "description": "Attire plus de clients.",
        "cost": 65,
        "limit": 1,
    },
    {
        "building_type": "Saloon",
        "kind": "upgrade",
        "name": "Agrandissement",
        "description": "Permet de recevoir plus de clients et d'ajouter des pièces.",
        "cost": 120,
        "limit": 1,
    },
]

SALOON_LIMITED_UPGRADES = [
    (upgrade["name"], upgrade["cost"], upgrade["limit"])
    for upgrade in SALOON_UPGRADES
    if upgrade.get("counts_as_room_choice")
]
SALOON_EXTRA_FEATURES = [
    (upgrade["key"], upgrade["name"], upgrade["cost"])
    for upgrade in SALOON_UPGRADES
    if upgrade["kind"] == "feature"
]

RANCH_UPGRADES = [
    {
        "building_type": "Ranch",
        "kind": "upgrade",
        "name": "Baraquements",
        "description": "Permet de loger vos employés.",
        "cost": 90,
        "repeatable": True,
    },
    {
        "building_type": "Ranch",
        "kind": "upgrade",
        "name": "Citerne",
        "description": "Réduit les risques de pertes de bétail pendant une sécheresse.",
        "cost": 60,
        "limit": 1,
    },
    {
        "building_type": "Ranch",
        "kind": "upgrade",
        "name": "Grange",
        "description": "Permet de stocker du fourrage, ce qui réduit l'attrition hivernale mais augmente la charge de travail en été.",
        "cost": 70,
        "limit": 1,
    },
    {
        "building_type": "Ranch",
        "kind": "upgrade",
        "name": "Manège et écurie",
        "description": "Permet de faire l'élevage de chevaux.",
        "cost": 110,
        "limit": 1,
    },
    {
        "building_type": "Ranch",
        "kind": "upgrade",
        "name": "Culture et potager",
        "description": "Transforme le surplus de travail en vivres.",
        "cost": 75,
        "limit": 1,
    },
    {
        "building_type": "Ranch",
        "kind": "upgrade",
        "name": "Élevage domestique",
        "description": "Transforme le surplus de travail en vivres.",
        "cost": 75,
        "limit": 1,
    },
]

MEDICAL_UPGRADES = [
    {
        "building_type": "Cabinet médical",
        "kind": "upgrade",
        "name": "Salle d'opération",
        "description": "Permet de traiter les blessures les plus graves dans de meilleures conditions.",
        "cost": 50,
        "limit": 1,
    },
    {
        "building_type": "Cabinet médical",
        "kind": "upgrade",
        "name": "Laboratoire",
        "description": "Permet de préparer des remèdes à partir de plantes médicinales.",
        "cost": 40,
        "limit": 1,
    },
    {
        "building_type": "Cabinet médical",
        "kind": "upgrade",
        "name": "Salle de convalescence",
        "description": "Ajoute deux lits pour suivre les patients les plus mal en point.",
        "cost": 30,
        "limit": 5,
    },
]

GENERAL_STORE_UPGRADES = [
    {
        "building_type": "General Store",
        "kind": "upgrade",
        "name": "Réserve",
        "description": "Débloque l'emploi de commis. Avec un commis, la capacité de stock augmente de 400.",
        "cost": 60,
        "limit": 1,
    },
]

BARBER_UPGRADES = [
    {
        "building_type": "Barber shop",
        "kind": "upgrade",
        "name": "Salle de bain",
        "description": "Permettra de proposer des bains quand le service sera branché au barber.",
        "cost": 50,
        "limit": 1,
    },
]

MINE_UPGRADES = [
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Corps de garde",
        "description": "Débloque quatre emplois de garde.",
        "cost": 0,
        "limit": 1,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Concasseur",
        "description": "Prépare le traitement du minerai. Effet simulé plus tard.",
        "cost": 0,
        "limit": 1,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Treuil",
        "description": "Facilite la remontée du minerai. Effet simulé plus tard.",
        "cost": 0,
        "limit": 1,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Bureau de l'ingénieur",
        "description": "Débloque l'emploi d'ingénieur.",
        "cost": 0,
        "limit": 1,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Magasin de la mine",
        "description": "Permettra aux mineurs d'acheter vivres, tabac et café sur place.",
        "cost": 0,
        "limit": 1,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Baraquements",
        "description": "Ajoute dix logements de type baraquement pour les mineurs et augmente le contentement.",
        "cost": 0,
        "repeatable": True,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Machine à vapeur",
        "description": "Disponible si un ingénieur est embauché.",
        "cost": 0,
        "limit": 1,
        "requires_engineer": True,
    },
    {
        "building_type": "Mine",
        "kind": "upgrade",
        "name": "Pompe à eau",
        "description": "Disponible après installation de la machine à vapeur.",
        "cost": 0,
        "limit": 1,
        "requires_upgrade": "Machine à vapeur",
    },
]

def action(label, cost, command):
    return (label, cost, command)


def action_label(action_data, show_cost=False):
    label, cost, _command = action_data
    if show_cost and cost > 0:
        return f"{label} ({format_action_cost(cost)})"
    return label


def format_action_cost(cost):
    if cost == 0.1:
        return "0.1"
    return str(int(cost)) if float(cost).is_integer() else str(cost)


def current_weekday_label(game):
    weekday_index = current_weekday_index(game)
    return f"{WEEKDAYS[weekday_index]} - {game.city.season} {game.city.year}"


def current_weekday_index(game):
    points = game.action_points
    if points > 12:
        weekday_index = 6
    elif points > 10:
        weekday_index = 5
    elif points > 8:
        weekday_index = 4
    elif points > 6:
        weekday_index = 3
    elif points > 4:
        weekday_index = 2
    elif points > 2:
        weekday_index = 1
    else:
        weekday_index = 0

    return weekday_index


def is_sunday(game):
    return current_weekday_index(game) == 0


def building_entry_cost(building):
    if building.building_type == "Ranch":
        return 1
    return 0


def archive_annual_results(city):
    closed_year = city.year - 1
    messages = close_annual_accounting(city, closed_year)
    for building in city.buildings:
        accounting = ensure_building_accounting(building, city)
        closed_result = result_total(accounting["annual_results"].get(str(closed_year), empty_result_lines()))
        building.account_journal.append(
            f"Clôture annuelle {closed_year} : résultat {format_money(closed_result)}. Résultat en cours remis à zéro."
        )
        building.previous_annual_sales = building.annual_sales
        building.previous_annual_purchases = building.annual_purchases
        building.previous_annual_wages = building.annual_wages
        building.previous_annual_stock_value = sum(current_stock_values(building).values())
        building.previous_annual_result = closed_result
        building.annual_sales = 0
        building.annual_purchases = 0
        building.annual_wages = 0
    return messages


def building_is_countryside(building):
    return building.building_type in ["Ranch", "Mine", "Ferme", "Camp de bucheron"]


def color_owned_building(listbox, index, building, player_name):
    if building.owner == player_name:
        listbox.itemconfig(listbox.size() - 1, fg="#1f7a1f")


def management_stock_label(building):
    if building.building_type == "Saloon":
        return "Stock et prix"
    if building.building_type == "Ranch":
        return "Troupeau et grange" if "Grange" in normalize_upgrades(building.upgrades) else "Troupeau"
    if building.building_type == "Cabinet médical":
        return "Pharmacie"
    return "Production"


def record_building_sale(building, amount, category="services_sold"):
    building.lifetime_revenue += amount
    building.annual_sales += amount
    record_accounting_product(building, category, amount, cash=False)







def building_allowed_families(building):
    if building.building_type == "Ranch":
        return {"vivres"}
    if building.building_type == "Saloon":
        return {"vivres", "alcool", "boisson"}
    if is_medical_building(building):
        return {"medecine"}
    return None


def is_medical_building(building):
    return "Cabinet" in building.building_type


def building_accepts_item(building, item):
    item = item_id(item)
    if item not in ITEM_CATALOG:
        return False
    if building.building_type == "Mine":
        return mine_accepts_item(building, item)
    families = building_allowed_families(building)
    return families is None or item_definition(item).get("family") in families


def mine_accepts_item(building, item):
    data = item_definition(item)
    family = data.get("family")
    if family == "minerai" or family == "outil":
        return True
    if item in {"bois", "planche"}:
        return True
    if "Magasin de la mine" in normalize_upgrades(building.upgrades):
        return family == "vivres" or item in {"tabac", "cafe"}
    return False


def allowed_inventory_items(inventory, building):
    return [
        item_id(item)
        for item, quantity in inventory.items()
        if quantity > 0 and building_accepts_item(building, item_id(item))
    ]


def building_has_storage_space(building, item, quantity):
    item = item_id(item)
    if building.building_type == "Saloon":
        return saloon_storage_used(building) + quantity * good_weight(item) <= saloon_storage_capacity(building)
    if building.building_type == "Ranch" and item_definition(item).get("family") == "vivres":
        stored_food = sum(
            quantity_value
            for stored_item, quantity_value in building.inventory.items()
            if stored_item in ITEM_CATALOG and item_definition(stored_item).get("family") == "vivres"
        )
        return stored_food + quantity <= RANCH_BARN_CAPACITY
    if is_medical_building(building) and item == "remede":
        return building.inventory.get("remede", 0) + quantity <= MEDICAL_PHARMACY_CAPACITY
    return True


def player_has_medical_laboratory(game):
    if not game:
        return False
    return any(
        building.building_type == "Cabinet médical"
        and building.owner == game.character.name
        and "Laboratoire" in normalize_upgrades(building.upgrades)
        for building in game.city.buildings
    )


def remove_first_available_item(inventories, item, quantity):
    remaining = quantity
    for inventory in inventories:
        available = inventory.get(item, 0)
        if available <= 0:
            continue
        removed = min(available, remaining)
        inventory[item] = available - removed
        if inventory[item] <= 0:
            inventory.pop(item, None)
        remaining -= removed
        if remaining <= 0:
            return True
    return False



def medical_default_price(building, condition):
    prices = {
        "blessé": building.production.get("tarif_blessure", service_default_price("soin_blessure")),
        "blessé gravement": building.production.get("tarif_blessure_grave", service_default_price("soin_blessure_grave")),
        "malade": building.production.get("tarif_maladie", service_default_price("soin_maladie")),
    }
    return prices.get(condition, 5)


def medical_success_chance(character, condition, building):
    chance = 45 + character.intelligence * 3
    if has_skill(character, "Médecine"):
        chance += 20
    upgrades = normalize_upgrades(building.upgrades)
    if condition == "blessé gravement" and "Salle d'opération" in upgrades:
        chance += 15
    if condition == "malade" and "Laboratoire" in upgrades:
        chance += 10
    return max(10, min(95, chance))




def has_skill(character, skill_name):
    normalized = normalize_text(skill_name)
    return any(normalize_text(skill) == normalized for skill in character.skills)


def character_has_item_family(character, family):
    inventory = getattr(character, "inventory", {}) or {}
    for item, quantity in inventory.items():
        if quantity <= 0:
            continue
        normalized_item = item_id(item)
        if normalized_item in ITEM_CATALOG and item_definition(normalized_item).get("family") == family:
            return True
    return False


def player_occupation_matches(game, occupation_type, building=None, role=None):
    occupation = getattr(game, "seasonal_occupation", {}) or {}
    if occupation.get("type") != occupation_type:
        return False
    if building and occupation.get("building_id") != building.building_id:
        return False
    if role and occupation.get("role") != role:
        return False
    return True


def player_role_occupation_matches(game, building, role):
    occupation = getattr(game, "seasonal_occupation", {}) or {}
    if occupation.get("type") not in ["employment", "job_application"]:
        return False
    return occupation.get("building_id") == building.building_id and occupation.get("role") == role




def normalize_text(value):
    return (
        value.lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
    )


def format_money(amount):
    value = float(amount)
    if value.is_integer():
        return f"{int(value)}$"
    return f"{value:.2f}".replace(".", ",") + "$"



def trail_drive_message(sold_cattle, bought_cattle, sale_amount, losses):
    sold_text = "aucune bête vendue" if sold_cattle == 0 else ("une bête vendue" if sold_cattle == 1 else f"{sold_cattle} bêtes vendues")
    bought_text = "aucune bête achetée" if bought_cattle == 0 else ("une bête achetée" if bought_cattle == 1 else f"{bought_cattle} bêtes achetées")
    lost_text = "aucune bête perdue" if losses == 0 else ("une bête perdue" if losses == 1 else f"{losses} bêtes perdues")
    return f"Résultat du long trail drive : {sold_text}, {bought_text}, {format_money(sale_amount)} encaissés, {lost_text}."


def npc_from_removed_trail(npc_id, removed_npcs):
    for removed in removed_npcs:
        npc_data = removed.get("npc", {})
        if npc_data.get("npc_id") == npc_id:
            return npc_from_saved_data(npc_data)
    return None


def add_owner_income(game, owner_name, amount):
    if owner_name == game.character.name:
        game.character.money += amount
        game.character.income += amount
        return
    owner = next((npc for npc in game.city.population if npc.name == owner_name), None)
    if owner:
        owner.money += amount
        owner.income += amount


def add_owner_money(game, owner_name, amount):
    if owner_name == game.character.name:
        game.character.money += amount
        return True
    owner = next((npc for npc in game.city.population if npc.name == owner_name), None)
    if owner:
        owner.money += amount
        return True
    return False


def stock_market_value(building):
    if building.building_type == "Ranch":
        return cattle_head_count(building) * building.production.get("market_cattle_price", BASE_MARKET_PRICES["boeuf"])
    if building.building_type == "Saloon":
        return (
            saloon_inventory_quantity(building, "fut_biere") * BASE_MARKET_PRICES["fut_biere"]
            + saloon_inventory_quantity(building, "vivres_secs") * BASE_MARKET_PRICES["vivres_secs"]
        )
    return 0


def refresh_stored_goods(building):
    remove_legacy_workforce_keys(building)
    building.production["stored_goods_value"] = stock_market_value(building)


def remove_legacy_workforce_keys(building):
    for key in [
        "workforce_bonus",
        "bar_workforce",
        "meal_workforce",
        "player_bar_work_actions",
        "player_meal_work_actions",
        "player_ranch_work_actions",
    ]:
        building.production.pop(key, None)




def remove_saloon_good(building, inventory_key, quantity):
    remaining = quantity
    if inventory_key == "fut_biere" and building.inventory.get("fut_biere", 0) <= 0 and building.inventory.get("biere", 0) > 0:
        inventory_key = "biere"
    available = building.inventory.get(inventory_key, 0)
    removed = min(available, remaining)
    building.inventory[inventory_key] = available - removed
    if building.inventory.get(inventory_key) == 0:
        building.inventory.pop(inventory_key, None)


def default_saloon_price(key):
    prices = {
        "prix_biere": service_default_price("biere"),
        "prix_repas": service_default_price("repas"),
        "prix_hotesse": service_default_price("hotesse"),
        "prix_bain": service_default_price("bain"),
        "prix_chambre": service_default_price("chambre"),
        "tarif_blessure": service_default_price("soin_blessure"),
        "tarif_blessure_grave": service_default_price("soin_blessure_grave"),
        "tarif_maladie": service_default_price("soin_maladie"),
        "tarif_convalescence": 4,
    }
    return prices.get(key, 1)


def format_price_input(value):
    return f"{float(value):.2f}".replace(".", ",")


def ensure_bulls(building):
    normalize_ranch_data(building)
    bulls = building.production.setdefault("bulls", [])
    for index, bull in enumerate(bulls):
        bulls[index] = normalize_bull(bull)


def player_owns_ranch(game):
    return any(
        building.building_type == "Ranch" and building.owner == game.character.name
        for building in game.city.buildings
    )


def trail_drive_state(building):
    return building.production.get("trail_drive")


def draft_from_trail_drive(building):
    trail_drive = trail_drive_state(building) or {}
    hired = []
    for npc_data in trail_drive.get("hired_cowboys", []):
        npc = npc_from_saved_data(npc_data)
        skilled = any(normalize_text(skill) == normalize_text("Élevage") for skill in npc.skills)
        hired.append({
            "type": "hired",
            "npc": npc,
            "wage": employee_salary("Cowboy") * (3 if skilled else 2),
        })
    return {
        "sell_cattle": trail_drive.get("sell_cattle", 0),
        "sell_bulls": list(trail_drive.get("sell_bulls", [])),
        "cowboys": list(trail_drive.get("crew", [])),
        "hired_cowboys": hired,
        "buy_cattle": trail_drive.get("buy_cattle", 0),
        "buy_bulls": list(trail_drive.get("buy_bulls", [])),
        "bull_market": list(trail_drive.get("bull_market", random_bull_market())),
    }



def trail_bull_label(bull, show_debug=False):
    return f"{bull.get('nom', 'Taureau')} - {bull.get('age', '?')} ans"


def trail_available_cowboys(game, building):
    entries = [{"type": "player"}]
    for employee_id in employee_ids(building):
        npc = game.city.get_npc_by_id(employee_id)
        if npc and employee_role(building, employee_id) == "Cowboy":
            entries.append({"type": "npc", "npc_id": npc.npc_id})
    return entries


def trail_cowboy_label(game, entry):
    if entry["type"] == "player":
        return f"{game.character.name} | Joueur | compétences : {format_items(game.character.skills)}"
    npc = entry.get("npc") or game.city.get_npc_by_id(entry.get("npc_id"))
    if not npc:
        return "Cowboy inconnu"
    wage = entry.get("wage")
    wage_text = f" | salaire trail : {format_money(wage)}" if wage else ""
    return f"{npc.name} | {npc.job} | compétences : {format_items(npc.skills)}{wage_text}"


def trail_entry_has_skill(game, entry, skill_name):
    if entry["type"] == "player":
        return has_skill(game.character, skill_name)
    npc = entry.get("npc") or game.city.get_npc_by_id(entry.get("npc_id"))
    return bool(npc and any(normalize_text(skill) == normalize_text(skill_name) for skill in npc.skills))


def create_trail_cowboy(game, skilled=False):
    used_names = {npc.name for npc in game.city.population}
    first_name, last_name = pick_unique_name(used_names, "Homme")
    npc_id = f"npc_trail_cowboy_{len(game.city.population) + random.randint(1000, 9999)}"
    skills = ["Élevage"] if skilled else []
    wage_multiplier = 3 if skilled else 2
    npc = NPC(
        npc_id=npc_id,
        first_name=first_name,
        last_name=last_name,
        name=f"{first_name} {last_name}",
        sex="Homme",
        age=random.randint(18, 45),
        origin="Cowboy",
        strength=random.randint(7, 10),
        sociability=random.randint(3, 6),
        intelligence=random.randint(3, 6),
        income=0,
        money=random.randint(5, 25),
        skills=skills,
        condition="en forme",
        job="Trail boss" if skilled else "Cowboy",
    )
    npc.preferences = generate_preferences(npc)
    npc.consumption_needs = generate_consumption_needs(npc)
    return {"type": "hired", "npc": npc, "wage": employee_salary("Cowboy") * wage_multiplier}


def npc_from_saved_data(data):
    return NPC(
        npc_id=data.get("npc_id", "npc_unknown"),
        first_name=data.get("first_name", "Inconnu"),
        last_name=data.get("last_name", ""),
        name=data.get("name", "Inconnu"),
        sex=data.get("sex", "Homme"),
        age=data.get("age", 30),
        origin=data.get("origin", "Cowboy"),
        strength=data.get("strength", 5),
        sociability=data.get("sociability", 5),
        intelligence=data.get("intelligence", 5),
        income=data.get("income", 0),
        money=data.get("money", 0),
        respect=data.get("respect", 0),
        celebrite=data.get("celebrite", 0),
        skills=data.get("skills", []),
        condition=data.get("condition", "en forme"),
        job=data.get("job", "Cowboy"),
        employer_building_id=data.get("employer_building_id"),
        spouse_id=data.get("spouse_id"),
        notable=data.get("notable", False),
        inventory=data.get("inventory", {}),
        trait=data.get("trait", "néant"),
        preferences=data.get("preferences", {}),
        consumption_needs=data.get("consumption_needs", generate_consumption_needs(None)),
    )




def building_display_name(building):
    if building.building_type == "Cabinet médical":
        return medical_building_display_name(building)
    if building.building_type.lower() in building.name.lower():
        return building.name
    return f"{building.name} ({building.building_type})"


def building_list_label(building):
    name = building_display_name(building)
    if building.under_construction:
        return f"{name} (en construction)"
    return name


def housing_building_list_label(housing):
    return f"{housing.name} ({housing.housing_type})"


def debug_building_text(building):
    return "\n".join([
        "Debug",
        debug_workforce_text(building),
        f"Stocks : {building.inventory}",
        f"Production : {building.production}",
        f"Contrats employés : {ensure_employee_contracts(building)}",
        f"Caractéristiques cachées : {building.hidden_stats}",
        f"Solde : {building.current_balance}",
        f"Résultat : {building.current_result}",
    ])


def debug_workforce_text(building):
    return "Forces de travail : calculées depuis l'occupation de saison"


def building_assets(building):
    assets = normalize_upgrades(building.upgrades)
    for key, label, _cost in SALOON_EXTRA_FEATURES:
        if building.features.get(key):
            assets.append(label)
    return compact_counted_names(assets)


def ranch_visible_assets(building):
    return compact_counted_names([
        upgrade for upgrade in normalize_upgrades(building.upgrades)
        if upgrade == "Baraquements"
    ])


def compact_counted_names(values):
    result = []
    for value in dict.fromkeys(values):
        count = values.count(value)
        if value == "Chambre" and count > 1:
            result.append(f"Chambres x{count}")
        else:
            result.append(f"{value} x{count}" if count > 1 else value)
    return result


def production_stock_lines(building):
    if building.building_type == "Saloon":
        return [
            ("Fûts de bière", saloon_inventory_quantity(building, "fut_biere")),
            (item_label("vivres_secs"), saloon_inventory_quantity(building, "vivres_secs")),
        ]

    return [
        ("Têtes de bétail", cattle_head_count(building)),
        ("Fourrage", building.inventory.get("fourrage", 0)),
    ]


def production_sell_fields(building):
    if building.building_type == "Saloon":
        return [
            ("prix_biere", "Prix de vente de la bière"),
            ("prix_repas", "Prix des repas"),
            ("prix_hotesse", "Prix de l'hotesse"),
            ("prix_bain", "Prix du bain"),
        ]

    return []


def production_buy_fields(building):
    if building.building_type == "Saloon":
        return [
            ("commande_biere", "Fûts de bière à commander", BASE_MARKET_PRICES["fut_biere"]),
            ("commande_vivres_secs", "Vivres secs à commander", BASE_MARKET_PRICES["vivres_secs"]),
        ]

    return []








def player_can_supervise_mine(character, building):
    return (
        building.building_type == "Mine"
        and has_skill(character, "Ingénierie")
        and "Bureau de l'ingénieur" in normalize_upgrades(building.upgrades)
    )


def mine_has_engineer_access(game, building):
    return (
        role_count(building, "Ingénieur") > 0
        or (
            building.owner == game.character.name
            and player_can_supervise_mine(game.character, building)
        )
    )




def spouse_is_important(npc, population):
    if not population or not npc.spouse_id:
        return False

    spouse = next((person for person in population if person.npc_id == npc.spouse_id), None)
    return bool(spouse and is_important_person(spouse))


def is_important_person(npc):
    important_jobs = ["Sherif", "Proprietaire", "Maire", "Juge", "Conseiller", "Politique"]
    return any(job_part in npc.job for job_part in important_jobs)


def is_social_important(npc):
    if npc.job.startswith("Tenancier"):
        return False
    return npc.notable or is_important_person(npc)


def social_relation_lines(npc, population):
    lines = []
    if npc.spouse_id:
        spouse = next((person for person in population if person.npc_id == npc.spouse_id), None)
        if spouse:
            relation_label = "Épouse" if spouse.sex == "Femme" else "Époux"
            lines.append(f"{relation_label} : {spouse.name}")

    if not lines:
        lines.append("Relations connues : aucune")
    return lines






def saloon_major_upgrade_count(building):
    limited_names = [
        upgrade["name"]
        for upgrade in SALOON_UPGRADES
        if upgrade.get("counts_as_room_choice")
    ]
    return len([upgrade for upgrade in normalize_upgrades(building.upgrades) if upgrade in limited_names])


def saloon_major_upgrade_limit(building):
    return 4 if "Agrandissement" in normalize_upgrades(building.upgrades) else 2


def saloon_upgrade_limit(upgrade):
    for name, _cost, limit in SALOON_LIMITED_UPGRADES:
        if name == upgrade:
            return limit
    return 1


def upgrade_count(building, upgrade_name):
    if upgrade_name == "Table de jeu":
        return 1 if building.features.get("table_poker") else 0
    for key, label, _cost in SALOON_EXTRA_FEATURES:
        if label == upgrade_name:
            return 1 if building.features.get(key) else 0
    return normalize_upgrades(building.upgrades).count(upgrade_name)


def upgrade_limit(building, upgrade):
    if upgrade.get("repeatable"):
        return None
    return upgrade.get("limit", 1)


def upgrade_state(building, upgrade):
    count = upgrade_count(building, upgrade["name"])
    limit = upgrade_limit(building, upgrade)
    if limit is not None and count >= limit:
        return "built"
    if upgrade.get("requires_engineer") and role_count(building, "Ingénieur") <= 0:
        return "unavailable"
    required_upgrade = upgrade.get("requires_upgrade")
    if required_upgrade and required_upgrade not in normalize_upgrades(building.upgrades):
        return "unavailable"
    if saloon_entertainment_choice_blocked(building, upgrade):
        return "unavailable"
    if upgrade.get("counts_as_room_choice") and saloon_major_upgrade_count(building) >= saloon_major_upgrade_limit(building):
        return "unavailable"
    return "available"


def saloon_entertainment_choice_blocked(building, upgrade):
    if building.building_type != "Saloon" or "Agrandissement" in normalize_upgrades(building.upgrades):
        return False
    if upgrade["name"] == "Table de jeu":
        return building.features.get("piano", False)
    if upgrade["name"] == "Piano":
        return building.features.get("table_poker", False)
    return False


def room_count(building):
    return normalize_upgrades(building.upgrades).count("Chambre")


def medical_bed_count(building):
    return min(10, normalize_upgrades(building.upgrades).count("Salle de convalescence") * 2)


def medical_building_display_name(building):
    owner_last_name = last_name_from_owner(building.owner)
    upgrades = normalize_upgrades(building.upgrades)
    has_convalescence = medical_bed_count(building) > 0
    has_core_room = "Salle d'opération" in upgrades or "Laboratoire" in upgrades
    if has_convalescence and has_core_room:
        return f"Clinique du Dr {owner_last_name}"
    return f"Dr. {owner_last_name}"


def update_medical_building_name(building):
    if building.building_type == "Cabinet médical":
        building.name = medical_building_display_name(building)


def last_name_from_owner(owner):
    return owner.split()[-1] if owner else "Inconnu"


def normalized_upgrade_name(upgrade):
    if upgrade == "Chambres d'hotel":
        return "Chambre"
    return upgrade


def normalize_upgrades(upgrades):
    return [normalized_upgrade_name(upgrade) for upgrade in upgrades]


def default_building_name(building_type, character):
    owner_name = character.last_name or character.name
    if building_type == "Saloon":
        return f"Saloon {owner_name}"
    if building_type == "Ranch":
        return f"Ranch {owner_name}"
    if building_type == "Cabinet médical":
        return f"Dr. {owner_name}"
    if building_type == "Mine":
        return f"Mine {owner_name}"
    return f"{building_type} {owner_name}"


def replace_entry_text(entry, value):
    entry.delete(0, tk.END)
    entry.insert(0, value)


def editable_character_fields(character):
    fields = [
        ("first_name", "Prénom"),
        ("last_name", "Nom"),
        ("name", "Nom complet"),
        ("sex", "Sexe"),
        ("age", "Âge"),
        ("origin", "Origine"),
        ("strength", "Physique"),
        ("sociability", "Social"),
        ("intelligence", "Intelligence"),
        ("income", "Revenu"),
        ("money", "Dollars"),
        ("respect", "Respect"),
        ("celebrite", "Célébrité"),
        ("condition", "État"),
        ("job", "Métier"),
        ("employer_building_id", "Employeur bâtiment"),
        ("residence", "Résidence"),
        ("skills", "Compétences"),
        ("inventory", "Inventaire"),
        ("consumption_needs", "Besoins conso"),
        ("mineral_claims", "Claims miniers"),
    ]
    if hasattr(character, "npc_id"):
        fields.insert(0, ("npc_id", "ID PNJ"))
        fields.extend([
            ("spouse_id", "Époux/épouse ID"),
            ("notable", "Important"),
            ("trait", "Attribut"),
            ("preferences", "Préférences"),
        ])
    return [(field, label) for field, label in fields if hasattr(character, field)]


def debug_field_to_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if all(not isinstance(item, (dict, list)) for item in value) else repr(value)
    if isinstance(value, dict):
        return ", ".join(f"{key}={val}" for key, val in value.items()) if all(not isinstance(val, (dict, list)) for val in value.values()) else repr(value)
    return str(value)


def apply_debug_character_entries(character, entries):
    int_fields = {"age", "strength", "sociability", "intelligence", "income", "money", "respect", "celebrite"}
    list_fields = {"skills"}
    dict_fields = {"inventory", "consumption_needs"}
    python_fields = {"preferences", "mineral_claims"}
    bool_fields = {"notable"}
    nullable_fields = {"job", "employer_building_id", "residence", "spouse_id"}

    for field, entry in entries.items():
        raw_value = entry.get().strip()
        if field in int_fields:
            setattr(character, field, parse_debug_int(raw_value, field))
        elif field in bool_fields:
            setattr(character, field, parse_debug_bool(raw_value))
        elif field in list_fields:
            setattr(character, field, parse_debug_list(raw_value))
        elif field in dict_fields:
            setattr(character, field, parse_debug_dict(raw_value))
        elif field in python_fields:
            setattr(character, field, parse_debug_python_value(raw_value, getattr(character, field)))
        elif field in nullable_fields:
            setattr(character, field, raw_value or None)
        else:
            setattr(character, field, raw_value)

    if hasattr(character, "first_name") and hasattr(character, "last_name"):
        if not getattr(character, "name", ""):
            character.name = f"{character.first_name} {character.last_name}".strip()
        else:
            parts = character.name.split(maxsplit=1)
            character.first_name = parts[0] if parts else character.first_name
            character.last_name = parts[1] if len(parts) > 1 else character.last_name


def parse_debug_int(value, field):
    if value == "":
        return 0
    try:
        return int(float(value.replace(",", ".")))
    except ValueError as exc:
        raise ValueError(f"Le champ {field} doit être un nombre.") from exc


def parse_debug_bool(value):
    return value.strip().lower() in {"1", "true", "vrai", "oui", "yes"}


def parse_debug_list(value):
    if not value:
        return []
    if value.startswith("["):
        parsed = parse_debug_python_value(value, [])
        if not isinstance(parsed, list):
            raise ValueError("La valeur doit être une liste.")
        return parsed
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_debug_dict(value):
    if not value:
        return {}
    if value.startswith("{"):
        parsed = parse_debug_python_value(value, {})
        if not isinstance(parsed, dict):
            raise ValueError("La valeur doit être un dictionnaire.")
        return parsed
    result = {}
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError("Format attendu pour un dictionnaire : cle=valeur, autre=2.")
        key, raw = [piece.strip() for piece in part.split("=", 1)]
        result[item_id(key)] = parse_debug_number(raw)
    return result


def parse_debug_number(value):
    value = value.replace(",", ".")
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"Valeur numérique invalide : {value}") from exc
    return int(number) if number.is_integer() else round(number, 4)


def parse_debug_python_value(value, default):
    if not value:
        return default
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError) as exc:
        raise ValueError("Syntaxe Python invalide pour ce champ complexe.") from exc


def parse_positive_int(value):
    value = value.strip()
    if not value.isdigit():
        return None
    return int(value)


def parse_positive_money(value):
    value = value.strip().replace(",", ".")
    try:
        number = float(value)
    except ValueError:
        return None
    if number < 0:
        return None
    return round(number, 2)


def parse_optional_money(value, default):
    value = str(value or "").strip()
    if not value:
        return round(default, 2)
    return parse_positive_money(value)


def simple_quantity_dialog(parent, title, prompt):
    value = simpledialog.askstring(title, prompt, parent=parent)
    if value is None:
        return None
    quantity = parse_positive_int(value)
    if quantity is None:
        messagebox.showwarning("Donnee invalide", "Entre un nombre entier positif.")
        return None
    return quantity


def simple_item_quantity_dialog(parent, title, prompt, item, maximum):
    value = simpledialog.askstring(title, prompt, parent=parent)
    if value is None:
        return None
    item = item_id(item)
    if item_definition(item).get("fractionable", False):
        quantity = parse_positive_money(value)
    else:
        quantity = parse_positive_int(value)
    if quantity is None or quantity <= 0:
        messagebox.showwarning("Donnée invalide", "Entre une quantité positive.")
        return None
    if quantity > maximum:
        messagebox.showwarning("Donnée invalide", "Quantité insuffisante.")
        return None
    return quantity


def npc_candidate_label(npc):
    return f"{npc.first_name} {npc.last_name} | {npc.sex} | {npc.age} ans | {npc.job}"


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


def format_quantity(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def format_items(values):
    if isinstance(values, list):
        return ", ".join(values) if values else "vide"
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
    condition = getattr(character, "condition", "en forme")
    if condition != "en forme":
        return f"Etat : {condition}."
    return "Etat : en forme."


def launch_app():
    app = GameApp()
    app.run()

