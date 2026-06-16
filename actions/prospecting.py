import math
import random
from copy import deepcopy


ORE_WEIGHTS = [
    ("charbon", 20),
    ("fer", 20),
    ("cuivre", 20),
    ("nickel", 15),
    ("argent", 15),
    ("or", 10),
]

CO_VEIN_RULES = {
    "charbon": ["fer"],
    "fer": ["cuivre", "charbon"],
    "cuivre": ["argent"],
    "argent": ["or"],
    "or": ["argent"],
    "nickel": ["cuivre"],
}


def generate_map_deposits():
    """Crée les filons cachés de la carte au lancement de la partie."""
    return [create_deposit(index + 1) for index in range(random_deposit_count())]


def random_deposit_count():
    return max(1, min(5, round(random.gauss(3, 1))))


def create_deposit(index):
    main_ore = weighted_choice(ORE_WEIGHTS)
    ores = [ore_entry(main_ore, 1)]
    if random.random() < 0.30:
        co_ore = random.choice(CO_VEIN_RULES[main_ore])
        co_share = round(random.uniform(0.10, 0.20), 4)
        ores[0]["share"] = round(1 - co_share, 4)
        ores.append(ore_entry(co_ore, co_share))

    size = random_deposit_size()
    concentration = random_concentration()
    return {
        "deposit_id": f"filon_{index:03d}",
        "ores": ores,
        "main_ore": main_ore,
        "size": size,
        "concentration": concentration,
        "claimed_by": None,
        "mine_building_id": None,
    }


def ore_entry(ore, share):
    return {
        "ore": ore,
        "share": share,
        "concentration": random_concentration(),
    }


def weighted_choice(weighted_values):
    total = sum(weight for _value, weight in weighted_values)
    roll = random.uniform(0, total)
    cursor = 0
    for value, weight in weighted_values:
        cursor += weight
        if roll <= cursor:
            return value
    return weighted_values[-1][0]


def random_deposit_size():
    """Taille bornée entre 2000 et 15000, avec beaucoup de petits filons."""
    while True:
        value = 2000 + random.expovariate(1 / 3500)
        if value <= 15000:
            return round(value)


def random_concentration():
    return weighted_choice([(3, 40), (4, 40), (5, 20)])


def prospect_region(city, prospector, owner_id):
    candidates = []
    for deposit in getattr(city, "mineral_deposits", []):
        if deposit.get("claimed_by"):
            continue
        chance = prospecting_chance(prospector, deposit)
        if random.uniform(0, 100) <= chance:
            candidates.append((chance, deposit))

    if not candidates:
        return None

    _chance, deposit = max(candidates, key=lambda entry: entry[0])
    claim_deposit(prospector, deposit, owner_id)
    return deepcopy(deposit)


def prospecting_chance(prospector, deposit):
    concentration = deposit.get("concentration", 4)
    modifier = 0
    if concentration == 3:
        modifier = 10
    elif concentration == 5:
        modifier = -10
    chance = prospector.intelligence * 2 + deposit.get("size", 0) / 1000 + modifier
    return max(0, min(95, chance))


def claim_deposit(prospector, deposit, owner_id):
    deposit["claimed_by"] = owner_id
    claims = getattr(prospector, "mineral_claims", None)
    if claims is None:
        prospector.mineral_claims = []
        claims = prospector.mineral_claims
    claims.append(deepcopy(deposit))


def remove_claim(prospector, deposit_id):
    claims = getattr(prospector, "mineral_claims", []) or []
    for index, claim in enumerate(claims):
        if claim.get("deposit_id") == deposit_id:
            return claims.pop(index)
    return None


def mark_deposit_mined(city, deposit_id, mine_building_id):
    for deposit in getattr(city, "mineral_deposits", []):
        if deposit.get("deposit_id") == deposit_id:
            deposit["mine_building_id"] = mine_building_id
            return deposit
    return None


def deposit_size_label(deposit):
    size = deposit.get("size", 0)
    if size > 10000:
        return "Important"
    if size >= 6000:
        return "Modéré"
    return "Faible"


def deposit_concentration_label(deposit):
    concentration = deposit.get("concentration", 4)
    if concentration >= 5:
        return "Élevée"
    if concentration == 4:
        return "Modérée"
    return "Faible"


def deposit_label(deposit):
    ores = ", ".join(ore["ore"] for ore in deposit.get("ores", []))
    return (
        f"{ores} | Abondance : {deposit_size_label(deposit)} | "
        f"Concentration : {deposit_concentration_label(deposit)}"
    )


def full_deposit_debug_label(deposit):
    ore_lines = [
        f"{ore['ore']} {round(ore.get('share', 0) * 100, 1)}% concentration {ore.get('concentration')}"
        for ore in deposit.get("ores", [])
    ]
    return (
        f"{deposit.get('deposit_id')} | taille={deposit.get('size')} | "
        f"concentration={deposit.get('concentration')} | " + "; ".join(ore_lines)
    )
