"""Script de fin de tour.

Plan du fichier:
01 - imports d'etapes: modules specialises appeles dans l'ordre.
02 - TURN_STEPS: liste officielle des etapes.
03 - run_end_turn: ordonnanceur principal.
04 - prepare/advance/error: contexte, saison, erreurs et sauvegarde.

Le fichier doit rester lisible: il prepare le contexte, appelle les grandes
etapes dans l'ordre, avance la saison et rend la main a l'interface. Les regles
metier vivent dans les modules specialises.
"""

import traceback
from tkinter import messagebox

from demography import (
    run_colon_arrivals,
    run_colon_departures,
    run_demography_summary,
    run_health_incidents,
    run_health_resolution,
    run_traveler_generation,
)
from game_state import advance_season, age_population_one_year
from saves import save_game
from turn_phases import (
    run_accounting_close,
    run_ai_management,
    run_building_exploitation_and_offers,
    run_cleanup_and_save,
    run_demand_and_consumption,
    run_income,
    run_market_price_cycle,
    run_new_season_events,
    run_player_occupation,
    run_temporary_housing,
)


TURN_STEPS = [
    "temporary_housing",
    "player_occupation",
    "ai_management",
    "health_incidents",
    "building_exploitation_and_offers",
    "income",
    "preference_demand_consumption",
    "demography",
    "health_resolution",
    "accounting_close",
    "advance_time",
    "new_season_events",
    "cleanup_and_save",
]


def run_end_turn(app):
    """Execute la fin de tour pour l'application actuelle."""
    try:
        prepare_turn_context(app)
        app.log_turn_step("Début de fin de tour", f"{app.game.city.season} {app.game.city.year}")

        run_temporary_housing(app)
        run_player_occupation(app)
        run_ai_management(app)
        run_health_incidents(app)
        run_building_exploitation_and_offers(app)
        run_income(app)
        run_demand_and_consumption(app)
        run_traveler_generation(app)
        run_colon_arrivals(app)
        run_colon_departures(app)
        run_demography_summary(app)
        run_health_resolution(app)
        run_accounting_close(app)
        new_year_started = advance_turn_time(app)
        run_market_price_cycle(app)
        run_new_season_events(app)
        run_cleanup_and_save(app, new_year_started)

        event_text = f" Événement : {', '.join(app.game.city.season_events)}" if app.game.city.season_events else ""
        app.set_status(f"Tour terminé.{event_text}")
        app.show_turn_transition(f"{app.game.city.season} {app.game.city.year}", app.show_city_after_turn)
    except Exception as error:
        handle_turn_error(app, error)


def prepare_turn_context(app):
    app.game.turn_log = []
    app.turn_context = {
        "offer_table": [],
        "income_table": {},
        "demand_table": [],
        "preference_lists": [],
        "consumption_table": {},
        "messages": [],
    }


def advance_turn_time(app):
    """Avance la saison, puis vieillit tout le monde si l'annee change."""
    old_label = f"{app.game.city.season} {app.game.city.year}"
    app.game.action_points = 0.0
    app.game.city.day += 1
    new_year_started = advance_season(app.game.city)
    if new_year_started:
        age_population_one_year(app.game)
    app.log_turn_step(
        "Avancement du temps",
        f"{old_label} -> {app.game.city.season} {app.game.city.year}. Nouvelle année : {new_year_started}.",
    )
    return new_year_started


def handle_turn_error(app, error):
    detail = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    if app.game:
        app.game.turn_log.append(f"[Erreur fin de tour] {detail}")
    app.show_city()
    messagebox.showerror(
        "Erreur de fin de tour",
        "Le calcul de fin de tour a été interrompu. Le journal debug contient le détail technique.",
    )


def save_after_turn(game):
    return save_game(game)
