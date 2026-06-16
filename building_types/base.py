"""Outils communs aux classes de batiments."""

from buildings import Building


PUBLIC_OWNER = "Ville"
BUILDING_KIND_PUBLIC = "public"
BUILDING_KIND_HOUSING_PROVIDER = "batiment_logement"
BUILDING_KIND_ECONOMIC = "economique"
DEFAULT_FIRE_RISK = 0.01


def configure_common_building(
    building,
    *,
    location="Ville",
    visible=True,
    building_kind=BUILDING_KIND_ECONOMIC,
    fire_risk=DEFAULT_FIRE_RISK,
):
    """Applique les parametres communs a tous les batiments."""
    building.location = location
    building.visible = visible
    building.building_kind = building_kind
    building.fire_risk = fire_risk
    if building_kind == BUILDING_KIND_PUBLIC:
        building.is_public = True
        if not building.owner:
            building.owner = PUBLIC_OWNER
    return building


def building_management_tabs(building, game=None):
    """Onglets communs; les batiments specialises peuvent en ajouter."""
    tabs = []
    if building_uses_accounting(building):
        tabs.append("accounting")
    if building_has_inventory(building):
        tabs.append("inventory")
    stock_name = management_stock_view_name(building)
    if stock_name:
        tabs.append("stock")
    if building_has_employees(building, game):
        tabs.append("employees")
    if building_produces_housing_units(building, game):
        tabs.append("housing")
    if building_has_upgrades(building, game):
        tabs.append("upgrades")
    return tabs


def building_uses_accounting(building):
    return getattr(building, "building_kind", BUILDING_KIND_ECONOMIC) in {
        BUILDING_KIND_PUBLIC,
        BUILDING_KIND_ECONOMIC,
    }


def building_has_inventory(building):
    return isinstance(getattr(building, "inventory", None), dict)


def management_stock_view_name(building):
    if getattr(building, "building_type", "") == "Ranch":
        return "Troupeau et grange"
    if getattr(building, "building_type", "") == "Saloon":
        return "Stock et prix"
    if getattr(building, "building_type", "") == "Mine":
        return "Production"
    if getattr(building, "building_type", "") == "Cabinet médical":
        return "Pharmacie"
    return None


def building_has_employees(building, game=None):
    recruitable = getattr(building, "recruitable_jobs", None)
    if recruitable:
        try:
            if recruitable(game):
                return True
        except TypeError:
            if recruitable():
                return True
    return bool(getattr(building, "employees", []))


def building_produces_housing_units(building, game=None):
    """Vrai si le batiment produit des unites de logement.

    Ne pas confondre avec le type d'unite de logement dans `housing.py`
    (`chambre`, `cabane`, `appartement`, etc.).
    """
    if getattr(building, "building_kind", "") == BUILDING_KIND_HOUSING_PROVIDER:
        return True
    if getattr(building, "building_type", "") in {"Saloon", "General Store", "Barber shop", "Ranch", "Ferme", "Hôtel"}:
        return True
    if game and any(unit.building_id == building.building_id for unit in getattr(game.city, "housing_units", [])):
        return True
    return False


def building_has_upgrades(building, game=None):
    if getattr(building, "upgrades", []):
        return True
    available = getattr(building, "available_upgrades", None)
    if available:
        try:
            return bool(available(game))
        except TypeError:
            return bool(available())
    return False


class TypedBuilding(Building):
    """Base temporaire pour les batiments specialises.

    Elle herite de l'ancien dataclass `Building` pour garder les sauvegardes et
    l'interface compatibles pendant la migration.
    """

    building_type_name = "Batiment"

    def city_actions(self, game):
        return []

    def building_actions(self, game):
        return []

    def management_tabs(self, game):
        return building_management_tabs(self, game)

    def available_upgrades(self, game):
        return []

    def recruitable_jobs(self, game):
        return []

    def run_exploitation(self, game):
        return []

    def generate_offers(self, game):
        return []
