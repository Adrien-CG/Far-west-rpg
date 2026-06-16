"""Batiment Mine.

Plan du fichier:
01 - Mine: classe de creation et valeurs par defaut.
02 - run_mine_exploitation: exploitation saisonniere actuelle.
03 - defaults/security helpers: valeurs de travail, securite et mecontentement.
04 - inventory helpers: lecture des minerais en stock.
"""

from building_types.base import TypedBuilding
from buildings import employee_ids, employee_role
from goods_services import ITEM_CATALOG, item_definition, item_id, item_label


class Mine(TypedBuilding):
    building_type_name = "Mine"

    def __init__(self, building_id, name, owner, deposit=None, current_balance=0, under_construction=False):
        super().__init__(
            building_id=building_id,
            name=name,
            building_type="Mine",
            owner=owner,
            level=1,
            inventory={},
            production={
                "workload": 0,
                "extracted": {},
                "work_hours": 8,
                "timbering_m": 8,
                "security": 50,
                "discontent": 0,
                "mine_store_prices": {
                    "vivres_secs": 1,
                    "tabac": 1,
                    "cafe": 1,
                },
            },
            hidden_stats={"deposit": deposit} if deposit else {},
            upgrades=[],
            current_balance=current_balance,
            under_construction=under_construction,
        )

    def recruitable_jobs(self, game):
        return ["Mineur", "Garde", "Ingénieur"]

    def city_actions(self, game):
        return []

    def run_exploitation(self, game):
        return run_mine_exploitation(game, self)

    def generate_housing_units(self, city):
        """Logements de mine: baraquements si construits, tentes de mineurs sinon."""
        from housing_rules import sync_building_units

        miner_count = role_count(self, "Mineur")
        barrack_units = normalize_upgrades(self.upgrades).count("Baraquements") * 10
        guard_units = 4 if "Corps de garde" in normalize_upgrades(self.upgrades) else 0
        sync_building_units(city, self, "baraquement", barrack_units + guard_units, listed=False)
        tent_needed = max(0, miner_count - barrack_units)
        sync_building_units(city, self, "tente", tent_needed, listed=False)


def run_mine_exploitation(game, building):
    ensure_mine_defaults(building)
    if player_occupation_matches(game, "mine_work", building):
        building.production["workload"] = building.production.get("workload", 0) + game.character.strength / 10
    if player_occupation_matches(game, "mine_supervision", building):
        building.production["supervised_by_player"] = True
    return (
        f"heures={building.production.get('work_hours', 8)}, "
        f"étayage={building.production.get('timbering_m', 8)}m, "
        f"sécurité={building.production.get('security', 50)}, "
        f"mécontentement={building.production.get('discontent', 0)}."
    )


def ensure_mine_defaults(building):
    production = building.production
    production.setdefault("work_hours", 8)
    production.setdefault("timbering_m", 8)
    production.setdefault("security", 50)
    production.setdefault("discontent", 0)
    production.setdefault("mine_store_prices", {"vivres_secs": 1, "tabac": 1, "cafe": 1})


def mine_discontent_delta(hours):
    return {8: 0, 10: 2, 12: 5}.get(hours, 0)


def mine_security_penalty(hours, timbering):
    hour_penalty = {8: 0, 10: 2, 12: 5}.get(hours, 0)
    timbering_penalty = {5: 0, 8: 2, 10: 4}.get(timbering, 0)
    return hour_penalty + timbering_penalty


def mine_ore_inventory_items(building):
    return [
        (item, quantity)
        for item, quantity in sorted(building.inventory.items(), key=lambda entry: item_label(entry[0]))
        if quantity > 0 and item_id(item) in ITEM_CATALOG and item_definition(item_id(item)).get("family") == "minerai"
    ]


def role_count(building, role):
    return len([
        employee_id for employee_id in employee_ids(building)
        if employee_role(building, employee_id) == role
    ])


def normalize_upgrades(upgrades):
    return ["Chambre" if upgrade == "Chambres d'hotel" else upgrade for upgrade in upgrades]


def player_occupation_matches(game, occupation_type, building=None):
    occupation = getattr(game, "seasonal_occupation", {}) or {}
    if occupation.get("type") != occupation_type:
        return False
    return not building or occupation.get("building_id") == building.building_id
