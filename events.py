"""Evenements aleatoires ou scenarises.

Plan du fichier:
01 - run_new_season_events: etape de fin de tour appelee par turn_phases.
02 - generate_season_events: evenements saisonniers actuels.
"""

import random


def run_new_season_events(app):
    app.game.city.season_events = generate_season_events(app.game)
    events = ", ".join(app.game.city.season_events) if app.game.city.season_events else "aucun événement"
    app.log_turn_step("Événements de nouvelle saison", events)


def generate_season_events(game):
    events = []
    if game.city.season == "Été" and random.randint(1, 10) == 1:
        events.append("Sécheresse")
    if game.city.season == "Hiver" and random.randint(1, 10) == 1:
        events.append("Hiver rude")
    return events
