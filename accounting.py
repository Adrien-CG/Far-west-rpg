"""Comptabilite des proprietes.

Les donnees comptables restent stockees dans chaque batiment. Ce module ne
depend pas de Tkinter: il peut donc etre utilise par l'interface, la fin de
tour, les tests et les futures IA.
"""

from copy import deepcopy

from buildings import BUILDING_CATALOG, normalize_ranch_data
from game_state import BASE_MARKET_PRICES
from goods_services import ITEM_CATALOG, item_definition, item_id


RESULT_KEYS = [
    "production_sold",
    "merchandise_sold",
    "services_sold",
    "stored_production",
    "raw_material_purchases",
    "merchandise_purchases",
    "raw_material_stock_variation",
    "merchandise_stock_variation",
    "wages",
    "taxes",
    "loan_repayments",
    "interest_expenses",
]


def ensure_building_accounting(building, city=None):
    accounting = building.accounting if isinstance(building.accounting, dict) else {}
    building.accounting = accounting
    accounting.setdefault("assets", {})
    accounting.setdefault("current_year", empty_result_lines())
    accounting.setdefault("season_current", empty_result_lines())
    accounting.setdefault("season_results", [])
    accounting.setdefault("annual_results", {})
    accounting.setdefault("balance_snapshots", {})
    accounting.setdefault("stock_opening", current_stock_values(building))
    accounting.setdefault("year_stock_opening", current_stock_values(building))
    accounting.setdefault("capital", initial_accounting_capital(building, city))
    accounting.setdefault("reserves", 0)
    accounting.setdefault("loans", 0)
    accounting.setdefault("last_year", city.year if city else 1865)
    accounting["assets"].update(default_asset_values(building, city))
    ensure_ranch_stock_split(building)
    return accounting


def empty_result_lines():
    return {key: 0 for key in RESULT_KEYS}


def default_asset_values(building, city=None):
    catalog = BUILDING_CATALOG.get(building.building_type, {})
    construction = building.production.get("construction_value", catalog.get("base_cost", building.investment_value or 0))
    improvements = max(0, building.investment_value - construction) if building.investment_value else estimated_upgrade_value(building)
    return {
        "construction": construction,
        "land": land_value(building),
        "improvements": improvements,
        "intangible": intangible_asset_value(building),
    }


def initial_accounting_capital(building, city=None):
    assets = default_asset_values(building, city)
    stocks = current_stock_values(building)
    cash = max(0, building.current_balance)
    overdraft = max(0, -building.current_balance)
    return round(sum(assets.values()) + sum(stocks.values()) + cash - overdraft, 2)


def estimated_upgrade_value(building):
    costs = {
        "Baraquements": 60,
        "Citerne": 70,
        "Grange": 90,
        "Chambre": 80,
        "Salle de bain": 50,
        "Cuisine": 60,
        "Cave": 70,
        "Table de jeu": 40,
        "Piano": 45,
        "Décoration et luminaire": 50,
        "Agrandissement": 120,
        "Réserve": 80,
        "Salle d'opération": 120,
        "Laboratoire": 100,
        "Salle de convalescence": 90,
        "Corps de garde": 100,
        "Concasseur": 150,
        "Treuil": 120,
        "Bureau de l'ingénieur": 180,
        "Machine à vapeur": 300,
        "Pompe à eau": 180,
    }
    return round(sum(costs.get(upgrade, 0) for upgrade in getattr(building, "upgrades", [])), 2)


def land_value(building):
    if building.building_type == "Ranch":
        return round(160 * 1.25, 2)
    if building_is_countryside(building):
        return 0
    if building.is_public:
        return 0
    return 5


def building_is_countryside(building):
    return building.building_type in ["Ranch", "Mine"]


def intangible_asset_value(building):
    deposit = building.hidden_stats.get("deposit") if isinstance(building.hidden_stats, dict) else None
    if not deposit:
        return 0
    return round(deposit.get("size", 0) * deposit.get("concentration", 4) * 0.02, 2)


def current_stock_values(building):
    ensure_ranch_stock_split(building)
    return {
        "products": stock_products_value(building),
        "raw_materials": stock_raw_materials_value(building),
        "merchandise": stock_merchandise_value(building),
    }


def stock_products_value(building):
    if building.building_type == "Ranch":
        price = cattle_market_price_from_building(building)
        cattle_value = building.production.get("product_cattle_count", 0) * price
        bull_value = sum(bull_market_price(bull) for bull in building.production.get("bulls", []) if bull.get("stock_type") == "products")
        return round(cattle_value + bull_value, 2)
    if building.building_type == "Mine":
        return round(sum(quantity * market_price_from_building(building, item) for item, quantity in building.inventory.items() if is_ore(item)), 2)
    return 0


def stock_raw_materials_value(building):
    return round(sum(building.inventory.get(item, 0) * market_price_from_building(building, item) for item in raw_material_items_for_building(building)), 2)


def stock_merchandise_value(building):
    if building.building_type == "Ranch":
        price = cattle_market_price_from_building(building)
        cattle_value = building.production.get("merchandise_cattle_count", cattle_head_count(building)) * price
        bull_value = sum(bull_market_price(bull) for bull in building.production.get("bulls", []) if bull.get("stock_type", "merchandise") == "merchandise")
        return round(cattle_value + bull_value, 2)
    if building.building_type == "General Store":
        return round(sum(quantity * market_price_from_building(building, item) for item, quantity in building.inventory.items() if item_id(item) in ITEM_CATALOG), 2)
    return 0


def raw_material_items_for_building(building):
    if building.building_type == "Saloon":
        return ["fut_biere", "vivres_secs"]
    if building.building_type == "Ranch":
        return ["vivres_secs", "fourrage"]
    if building.building_type == "Mine":
        return ["explosifs", "outils", "bois", "planche", "vivres_secs"]
    if building.building_type in ["Cabinet médical", "Cabinet mÃ©dical"]:
        return ["plantes_medicinales", "remede"]
    return []


def is_ore(item):
    normalized = item_id(item)
    return normalized in ITEM_CATALOG and item_definition(normalized).get("family") == "minerai"


def market_price_from_building(building, item):
    normalized = item_id(item)
    if normalized not in ITEM_CATALOG:
        return 0
    return BASE_MARKET_PRICES.get(normalized, item_definition(normalized).get("base_price", 0))


def cattle_market_price_from_building(building):
    return building.production.get("market_cattle_price", BASE_MARKET_PRICES.get("betail", 25))


def cattle_head_count(building):
    return int(building.production.get("head_count", 0))


def bull_market_price(bull):
    return 40 if bull.get("age", 0) >= 5 else 50


def ensure_ranch_stock_split(building):
    if building.building_type != "Ranch":
        return
    normalize_ranch_data(building)
    production = building.production
    production.setdefault("product_cattle_count", 0)
    production.setdefault("merchandise_cattle_count", max(0, cattle_head_count(building) - production.get("product_cattle_count", 0)))
    total = production.get("product_cattle_count", 0) + production.get("merchandise_cattle_count", 0)
    head_count = cattle_head_count(building)
    if total != head_count:
        delta = head_count - total
        if delta >= 0:
            production["merchandise_cattle_count"] += delta
        else:
            reduce_ranch_cattle_stock(building, abs(delta))
    for bull in production.get("bulls", []):
        bull.setdefault("stock_type", "merchandise")


def reduce_ranch_cattle_stock(building, quantity):
    production = building.production
    merchandise = min(quantity, production.get("merchandise_cattle_count", 0))
    production["merchandise_cattle_count"] = production.get("merchandise_cattle_count", 0) - merchandise
    remaining = quantity - merchandise
    if remaining:
        production["product_cattle_count"] = max(0, production.get("product_cattle_count", 0) - remaining)


def split_ranch_cattle_sale(building, quantity):
    ensure_ranch_stock_split(building)
    production = building.production
    merchandise = min(quantity, production.get("merchandise_cattle_count", 0))
    products = max(0, quantity - merchandise)
    production["merchandise_cattle_count"] = production.get("merchandise_cattle_count", 0) - merchandise
    production["product_cattle_count"] = max(0, production.get("product_cattle_count", 0) - products)
    return {"merchandise": merchandise, "products": products}


def restore_ranch_cattle_stock(building, split):
    ensure_ranch_stock_split(building)
    building.production["merchandise_cattle_count"] = building.production.get("merchandise_cattle_count", 0) + split.get("merchandise", 0)
    building.production["product_cattle_count"] = building.production.get("product_cattle_count", 0) + split.get("products", 0)


def prorate_cattle_sale_split(split, original_quantity, sold_quantity):
    if original_quantity <= 0 or sold_quantity <= 0:
        return {"merchandise": 0, "products": 0}
    ratio = sold_quantity / original_quantity
    merchandise = round_half_up(split.get("merchandise", 0) * ratio)
    merchandise = min(merchandise, sold_quantity)
    return {"merchandise": merchandise, "products": sold_quantity - merchandise}


def round_half_up(value):
    import math

    return math.floor(value + 0.5)


def accounting_balance_asset_lines(building):
    accounting = ensure_building_accounting(building)
    assets = accounting["assets"]
    stocks = current_stock_values(building)
    cash = max(0, building.current_balance)
    total = sum(assets.values()) + sum(stocks.values()) + cash
    return [
        "Actif immobilisé",
        accounting_line(f"Construction initiale : {format_money(assets['construction'])}", "stock"),
        accounting_line(f"Terrain : {format_money(assets['land'])}", "stock"),
        accounting_line(f"Améliorations : {format_money(assets['improvements'])}", "stock"),
        accounting_line(f"Titres immatériels : {format_money(assets['intangible'])}", "stock"),
        "",
        "Actif circulant",
        accounting_line(f"Stock produits : {format_money(stocks['products'])}", "stock"),
        accounting_line(f"Stock matières premières : {format_money(stocks['raw_materials'])}", "stock"),
        accounting_line(f"Stock marchandises : {format_money(stocks['merchandise'])}", "stock"),
        accounting_line(f"Caisse : {format_money(cash)}", "positive" if cash else "stock"),
        "",
        accounting_line(f"Total actif : {format_money(total)}", "stock"),
    ]


def accounting_balance_liability_lines(building):
    accounting = ensure_building_accounting(building)
    current_result = result_total(accounting["current_year"])
    overdraft = max(0, -building.current_balance)
    total = accounting["capital"] + accounting["reserves"] + current_result + accounting["loans"] + overdraft
    return [
        "Fonds propres",
        accounting_line(f"Capital : {format_money(accounting['capital'])}", "stock"),
        accounting_line(f"Réserve : {format_money(accounting['reserves'])}", "stock"),
        accounting_line(f"Résultat en cours : {format_money(current_result)}", "positive" if current_result >= 0 else "negative"),
        "",
        "Dettes",
        accounting_line(f"Emprunts : {format_money(accounting['loans'])}", "negative" if accounting["loans"] else "stock"),
        accounting_line(f"Découvert : {format_money(overdraft)}", "negative" if overdraft else "stock"),
        "",
        accounting_line(f"Total passif : {format_money(total)}", "stock"),
    ]


def accounting_balance_errors(building):
    accounting = ensure_building_accounting(building)
    assets = accounting["assets"]
    stocks = current_stock_values(building)
    active = round(sum(assets.values()) + sum(stocks.values()) + max(0, building.current_balance), 2)
    passive = round(accounting["capital"] + accounting["reserves"] + result_total(accounting["current_year"]) + accounting["loans"] + max(0, -building.current_balance), 2)
    if abs(active - passive) <= 0.01:
        return []
    message = f"Erreur bilan {building.name} : actif {format_money(active)} != passif {format_money(passive)}."
    if message not in building.account_journal:
        building.account_journal.append(message)
    return [message]


def accounting_current_year_lines(building):
    return result_result_lines({"lines": ensure_building_accounting(building)["current_year"]})


def result_result_lines(result):
    lines = result.get("lines", result)
    products = result_products_total(lines)
    charges = result_charges_total(lines)
    total = products - charges
    return [
        "Produits",
        accounting_line(f"Production vendue : {format_money(lines.get('production_sold', 0))}", "positive"),
        accounting_line(f"Marchandises vendues : {format_money(lines.get('merchandise_sold', 0))}", "positive"),
        accounting_line(f"Services vendus : {format_money(lines.get('services_sold', 0))}", "positive"),
        accounting_line(f"Production stockée : {format_money(lines.get('stored_production', 0))}", "positive" if lines.get("stored_production", 0) >= 0 else "negative"),
        accounting_line(f"Total produits : {format_money(products)}", "positive" if products >= 0 else "negative"),
        "",
        "Charges",
        accounting_line(f"Achats matières premières : {format_money(lines.get('raw_material_purchases', 0))}", "negative"),
        accounting_line(f"Achats marchandises : {format_money(lines.get('merchandise_purchases', 0))}", "negative"),
        accounting_line(f"Variation stock MP : {format_money(lines.get('raw_material_stock_variation', 0))}", "negative" if lines.get("raw_material_stock_variation", 0) >= 0 else "positive"),
        accounting_line(f"Variation stock marchandises : {format_money(lines.get('merchandise_stock_variation', 0))}", "negative" if lines.get("merchandise_stock_variation", 0) >= 0 else "positive"),
        accounting_line(f"Salaires : {format_money(lines.get('wages', 0))}", "negative"),
        accounting_line(f"Taxes : {format_money(lines.get('taxes', 0))}", "negative"),
        accounting_line(f"Remboursement emprunt : {format_money(lines.get('loan_repayments', 0))}", "negative"),
        accounting_line(f"Charges d'intérêts : {format_money(lines.get('interest_expenses', 0))}", "negative"),
        accounting_line(f"Total charges : {format_money(charges)}", "negative" if charges >= 0 else "positive"),
        "",
        accounting_line(f"Résultat : {format_money(total)}", "positive" if total >= 0 else "negative"),
    ]


def split_result_lines(lines):
    if "" not in lines:
        return lines, [], []
    first_blank = lines.index("")
    second_blank = lines.index("", first_blank + 1) if "" in lines[first_blank + 1:] else len(lines)
    return lines[:first_blank], lines[first_blank + 1:second_blank], lines[second_blank + 1:]


def result_products_total(lines):
    return round(lines.get("production_sold", 0) + lines.get("merchandise_sold", 0) + lines.get("services_sold", 0) + lines.get("stored_production", 0), 2)


def result_charges_total(lines):
    return round(
        lines.get("raw_material_purchases", 0)
        + lines.get("merchandise_purchases", 0)
        + lines.get("raw_material_stock_variation", 0)
        + lines.get("merchandise_stock_variation", 0)
        + lines.get("wages", 0)
        + lines.get("taxes", 0)
        + lines.get("loan_repayments", 0)
        + lines.get("interest_expenses", 0),
        2,
    )


def result_total(lines):
    return round(result_products_total(lines) - result_charges_total(lines), 2)


def record_accounting_product(building, category, amount, cash=True):
    accounting = ensure_building_accounting(building)
    if category not in empty_result_lines():
        return
    amount = round(amount, 2)
    accounting["season_current"][category] = round(accounting["season_current"].get(category, 0) + amount, 2)
    if cash and category != "stored_production":
        building.current_balance = round(building.current_balance + amount, 2)


def record_accounting_charge(building, category, amount, cash=True):
    accounting = ensure_building_accounting(building)
    if category not in empty_result_lines():
        return
    amount = round(amount, 2)
    accounting["season_current"][category] = round(accounting["season_current"].get(category, 0) + amount, 2)
    if cash and category not in ["raw_material_stock_variation", "merchandise_stock_variation"]:
        building.current_balance = round(building.current_balance - amount, 2)


def accounting_capital_contribution(building, city, amount, cash_amount=None):
    accounting = ensure_building_accounting(building, city)
    amount = round(amount, 2)
    cash_amount = amount if cash_amount is None else round(cash_amount, 2)
    accounting["capital"] = round(accounting["capital"] + amount, 2)
    building.current_balance = round(building.current_balance + cash_amount, 2)
    building.account_journal.append(f"Apport en capital : {format_money(amount)}.")


def accounting_remove_capital(building, city, amount):
    accounting = ensure_building_accounting(building, city)
    amount = round(amount, 2)
    if amount <= 0 or accounting["reserves"] != 0 or building.current_balance < amount or accounting["capital"] < amount:
        return False
    accounting["capital"] = round(accounting["capital"] - amount, 2)
    building.current_balance = round(building.current_balance - amount, 2)
    building.account_journal.append(f"Retrait de capital : {format_money(amount)}.")
    return True


def accounting_pay_dividends(building, city, amount):
    accounting = ensure_building_accounting(building, city)
    amount = round(amount, 2)
    if amount <= 0 or building.current_balance < amount or accounting["reserves"] < amount:
        return False
    accounting["reserves"] = round(accounting["reserves"] - amount, 2)
    building.current_balance = round(building.current_balance - amount, 2)
    building.account_journal.append(f"Dividendes versés : {format_money(amount)}.")
    return True


def close_season_accounting(city):
    messages = []
    for building in city.buildings:
        accounting = ensure_building_accounting(building, city)
        opening = accounting.get("stock_opening", current_stock_values(building))
        closing = current_stock_values(building)
        season_lines = deepcopy(accounting.get("season_current", empty_result_lines()))
        season_lines["stored_production"] = round(season_lines.get("stored_production", 0) + closing["products"] - opening.get("products", 0), 2)
        season_lines["raw_material_stock_variation"] = round(season_lines.get("raw_material_stock_variation", 0) + opening.get("raw_materials", 0) - closing["raw_materials"], 2)
        season_lines["merchandise_stock_variation"] = round(season_lines.get("merchandise_stock_variation", 0) + opening.get("merchandise", 0) - closing["merchandise"], 2)
        result = {
            "year": city.year,
            "season": city.season,
            "lines": season_lines,
            "products_total": result_products_total(season_lines),
            "charges_total": result_charges_total(season_lines),
            "result": result_total(season_lines),
        }
        accounting["season_results"].append(result)
        add_result_lines(accounting["current_year"], season_lines)
        accounting["season_current"] = empty_result_lines()
        accounting["stock_opening"] = closing
        building.current_result = result["result"]
        building.result_history.append(result["result"])
        messages.append(f"{building.name} : résultat {city.season} {city.year} = {format_money(result['result'])}.")
        messages.extend(accounting_balance_errors(building))
    return messages


def add_result_lines(target, source):
    for key in empty_result_lines():
        target[key] = round(target.get(key, 0) + source.get(key, 0), 2)


def close_annual_accounting(city, closed_year):
    messages = []
    for building in city.buildings:
        accounting = ensure_building_accounting(building, city)
        current_year = deepcopy(accounting.get("current_year", empty_result_lines()))
        annual_result = {
            "year": closed_year,
            "lines": current_year,
            "products_total": result_products_total(current_year),
            "charges_total": result_charges_total(current_year),
            "result": result_total(current_year),
        }
        accounting["annual_results"][str(closed_year)] = annual_result
        accounting["balance_snapshots"][str(closed_year)] = accounting_balance_snapshot(building)
        close_result_into_equity(accounting, annual_result["result"])
        accounting["current_year"] = empty_result_lines()
        accounting["year_stock_opening"] = current_stock_values(building)
        building.current_result = 0
        messages.append(f"{building.name} : clôture {closed_year}, résultat {format_money(annual_result['result'])}.")
    return messages


def close_result_into_equity(accounting, result):
    result = round(result, 2)
    if result >= 0:
        accounting["reserves"] = round(accounting["reserves"] + result, 2)
        return
    loss = abs(result)
    reserve_used = min(accounting["reserves"], loss)
    accounting["reserves"] = round(accounting["reserves"] - reserve_used, 2)
    remaining_loss = round(loss - reserve_used, 2)
    if remaining_loss:
        accounting["capital"] = round(max(0, accounting["capital"] - remaining_loss), 2)


def accounting_balance_snapshot(building):
    accounting = ensure_building_accounting(building)
    assets = deepcopy(accounting["assets"])
    stocks = current_stock_values(building)
    cash = max(0, building.current_balance)
    overdraft = max(0, -building.current_balance)
    current_result = result_total(accounting["current_year"])
    return {
        "assets": assets,
        "stocks": stocks,
        "cash": cash,
        "overdraft": overdraft,
        "capital": accounting["capital"],
        "reserves": accounting["reserves"],
        "current_result": current_result,
        "loans": accounting["loans"],
        "active_total": round(sum(assets.values()) + sum(stocks.values()) + cash, 2),
        "passive_total": round(accounting["capital"] + accounting["reserves"] + current_result + accounting["loans"] + overdraft, 2),
    }


def snapshot_asset_lines(snapshot):
    assets = snapshot.get("assets", {})
    stocks = snapshot.get("stocks", {})
    return [
        "Actif immobilisé",
        accounting_line(f"Construction initiale : {format_money(assets.get('construction', 0))}", "stock"),
        accounting_line(f"Terrain : {format_money(assets.get('land', 0))}", "stock"),
        accounting_line(f"Améliorations : {format_money(assets.get('improvements', 0))}", "stock"),
        accounting_line(f"Titres immatériels : {format_money(assets.get('intangible', 0))}", "stock"),
        "",
        "Actif circulant",
        accounting_line(f"Stock produits : {format_money(stocks.get('products', 0))}", "stock"),
        accounting_line(f"Stock matières premières : {format_money(stocks.get('raw_materials', 0))}", "stock"),
        accounting_line(f"Stock marchandises : {format_money(stocks.get('merchandise', 0))}", "stock"),
        accounting_line(f"Caisse : {format_money(snapshot.get('cash', 0))}", "positive" if snapshot.get("cash", 0) else "stock"),
        "",
        accounting_line(f"Total actif : {format_money(snapshot.get('active_total', 0))}", "stock"),
    ]


def snapshot_liability_lines(snapshot):
    current_result = snapshot.get("current_result", 0)
    overdraft = snapshot.get("overdraft", 0)
    return [
        "Fonds propres",
        accounting_line(f"Capital : {format_money(snapshot.get('capital', 0))}", "stock"),
        accounting_line(f"Réserve : {format_money(snapshot.get('reserves', 0))}", "stock"),
        accounting_line(f"Résultat en cours : {format_money(current_result)}", "positive" if current_result >= 0 else "negative"),
        "",
        "Dettes",
        accounting_line(f"Emprunts : {format_money(snapshot.get('loans', 0))}", "negative" if snapshot.get("loans", 0) else "stock"),
        accounting_line(f"Découvert : {format_money(overdraft)}", "negative" if overdraft else "stock"),
        "",
        accounting_line(f"Total passif : {format_money(snapshot.get('passive_total', 0))}", "stock"),
    ]


def accounting_line(text, kind):
    return {"text": text, "kind": kind}


def accounting_display_line(line):
    if isinstance(line, dict):
        colors = {"positive": "#1f7a1f", "negative": "#b00000", "stock": "black"}
        return line["text"], colors.get(line.get("kind"), "black")
    return line, "black"


def stocked_goods_lines(building):
    lines = []
    for line in building.account_journal:
        if line.startswith("Achat stock - "):
            label, amount = split_account_journal_amount(line.replace("Achat stock - ", ""))
            lines.append(accounting_line(f"- Achat {label} : {format_money(amount)}", "negative"))
    return lines


def split_account_journal_amount(text):
    if ":" not in text:
        return text, 0
    label, raw_amount = text.rsplit(":", 1)
    try:
        amount = float(raw_amount.strip())
    except ValueError:
        amount = 0
    return label.strip(), amount


def format_money(amount):
    amount = round(float(amount), 2)
    if amount.is_integer():
        return f"{int(amount)} $"
    return f"{amount:.2f} $"
