"""Etapes de fin de tour.

Plan du fichier:
01 - run_*: adaptateurs temporaires appeles par turn_system.
02 - commentaires: indiquent quelles etapes restent a migrer hors UI.

Ce module sert de zone de transition pendant la refonte. Chaque fonction
correspond a une etape lisible du tour. Certaines appellent encore des methodes
de l'interface parce que le detail metier n'a pas encore ete extrait, mais
`turn_system.py` peut deja rester un simple ordonnanceur.
"""

from events import run_new_season_events as process_new_season_events
from economy import run_market_price_cycle as process_market_price_cycle
from housing_rules import run_temporary_housing as process_temporary_housing


def run_temporary_housing(app):
    result = process_temporary_housing(app.game.city, app.game.character)
    app.log_turn_step("Logement provisoire", result["summary"])


def run_player_occupation(app):
    app.apply_player_occupation()


def run_ai_management(app):
    app.end_turn_ai_management()


def run_building_exploitation_and_offers(app):
    app.end_turn_local_offer()


def run_income(app):
    app.end_turn_income()


def run_demand_and_consumption(app):
    app.end_turn_demand_and_consumption()


def run_accounting_close(app):
    app.end_turn_accounting_close()


def run_new_season_events(app):
    process_new_season_events(app)


def run_market_price_cycle(app):
    process_market_price_cycle(app)


def run_cleanup_and_save(app, new_year_started):
    app.end_turn_cleanup(new_year_started)
