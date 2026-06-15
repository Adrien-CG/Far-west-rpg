from building_management.accounting import open_accounting_menu
from building_management.ranch import open_ranch_employee_menu, open_ranch_improvement_menu
from building_management.saloon import open_saloon_employee_menu, open_saloon_improvement_menu


def open_improvement_menu(game, building):
    if building.building_type == "Ranch":
        open_ranch_improvement_menu(game, building)
    elif building.building_type == "Saloon":
        open_saloon_improvement_menu(game, building)
    else:
        print("\nAucune amelioration specifique pour ce batiment.")


def open_employee_menu(game, building):
    if building.building_type == "Ranch":
        open_ranch_employee_menu(game, building)
    elif building.building_type == "Saloon":
        open_saloon_employee_menu(game, building)
    else:
        print("\nAucun menu employe specifique pour ce batiment.")
