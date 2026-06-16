"""Logements et batiments de logement.

Plan du fichier:
01 - HousingUnit: logement individuel propose ou occupe.
02 - HousingBuilding: batiment qui cree des logements.
03 - HOUSING_TYPES/BUILDING_TYPES: constantes de logement.
04 - create_*: creation des logements.
05 - offer/serialization helpers: offres et sauvegardes.
"""

from dataclasses import asdict, dataclass, field


@dataclass
class HousingUnit:
    housing_id: str
    housing_type: str
    owner: str
    building_id: str | None = None
    occupants: list[str] = field(default_factory=list)
    utility: int = 0
    salubrity: int = 0
    fire_risk: int = 0
    rent_price: float = 0
    electricity: bool = False
    water: bool = False
    included_board: bool = False
    bath: bool = False
    listed: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class HousingBuilding:
    housing_building_id: str
    name: str
    housing_type: str
    owner: str
    building_id: str | None = None
    visible_if_player_owned: bool = True
    location: str = "Ville"
    utility: int = 0
    salubrity: int = 0
    fire_risk: int = 0
    rent_price: float = 0
    electricity: bool = False
    water: bool = False
    included_board: bool = False
    bath: bool = False
    listed: bool = True
    unit_ids: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


HOUSING_TYPES = {
    "tente": {
        "label": "Tente",
        "utility": 25,
        "salubrity": 1,
        "fire_risk": 3,
        "rent_price": 0.25,
        "listed": True,
    },
    "bunkhouse": {
        "label": "Bunkhouse",
        "utility": 50,
        "salubrity": 2,
        "fire_risk": 2,
        "rent_price": 0.75,
        "listed": True,
    },
    "poorhouse": {
        "label": "Poorhouse",
        "utility": 35,
        "salubrity": 1,
        "fire_risk": 2,
        "rent_price": 0,
        "listed": False,
    },
    "cabane": {
        "label": "Cabane",
        "utility": 80,
        "salubrity": 2,
        "fire_risk": 3,
        "rent_price": 1,
        "listed": True,
    },
    "baraquement": {
        "label": "Baraquement",
        "utility": 60,
        "salubrity": 2,
        "fire_risk": 2,
        "rent_price": 0,
        "included_board": True,
        "listed": False,
    },
    "chambre": {
        "label": "Chambre",
        "utility": 130,
        "salubrity": 4,
        "fire_risk": 2,
        "rent_price": 1.5,
        "listed": True,
    },
    "appartement": {
        "label": "Appartement",
        "utility": 190,
        "salubrity": 5,
        "fire_risk": 2,
        "rent_price": 4,
        "listed": True,
    },
    "maison_ville": {
        "label": "Maison de ville",
        "utility": 260,
        "salubrity": 6,
        "fire_risk": 2,
        "rent_price": 7,
        "listed": True,
    },
    "maison_campagne": {
        "label": "Maison de campagne",
        "utility": 240,
        "salubrity": 5,
        "fire_risk": 2,
        "rent_price": 5,
        "listed": True,
    },
    "maison_bourgeoise": {
        "label": "Maison bourgeoise",
        "utility": 380,
        "salubrity": 8,
        "fire_risk": 1,
        "rent_price": 14,
        "listed": True,
    },
}


HOUSING_BUILDING_TYPES = {
    "pension": {
        "label": "Pension",
        "default_housing_type": "chambre",
        "location": "Ville",
        "visible_if_player_owned": True,
        "listed": True,
        "base_units": 3,
    },
    "immeuble": {
        "label": "Immeuble",
        "default_housing_type": "appartement",
        "location": "Ville",
        "visible_if_player_owned": True,
        "listed": True,
        "base_units": 4,
        "max_units": 6,
        "available_from_year": 1880,
    },
    "maison_ville": {
        "label": "Maison de ville",
        "default_housing_type": "maison_ville",
        "location": "Ville",
        "visible_if_player_owned": True,
        "listed": True,
        "base_units": 1,
    },
    "maison_bourgeoise": {
        "label": "Maison bourgeoise",
        "default_housing_type": "maison_bourgeoise",
        "location": "Ville",
        "visible_if_player_owned": True,
        "listed": True,
        "base_units": 1,
    },
    "poorhouse": {
        "label": "Poorhouse",
        "default_housing_type": "poorhouse",
        "location": "Ville",
        "visible_if_player_owned": True,
        "listed": False,
        "base_units": 8,
    },
    "cabane": {
        "label": "Cabane",
        "default_housing_type": "cabane",
        "location": "Ville",
        "visible_if_player_owned": True,
        "listed": True,
        "base_units": 1,
    },
}


MARRIED_FORBIDDEN_HOUSING_TYPES = {"chambre", "baraquement", "poorhouse"}


def create_housing_building(housing_building_id, building_type, owner, name=None, building_id=None, unit_count=1):
    data = HOUSING_BUILDING_TYPES[building_type]
    housing_type = data["default_housing_type"]
    unit_count = unit_count or data.get("base_units", 1)
    unit_ids = [
        f"{housing_building_id}_unit_{index:03d}"
        for index in range(1, unit_count + 1)
    ]
    building = HousingBuilding(
        housing_building_id=housing_building_id,
        name=name or data["label"],
        housing_type=building_type,
        owner=owner,
        building_id=building_id,
        visible_if_player_owned=data.get("visible_if_player_owned", True),
        location=data.get("location", "Ville"),
        utility=HOUSING_TYPES[housing_type]["utility"],
        salubrity=HOUSING_TYPES[housing_type]["salubrity"],
        fire_risk=HOUSING_TYPES[housing_type]["fire_risk"],
        rent_price=HOUSING_TYPES[housing_type]["rent_price"],
        electricity=HOUSING_TYPES[housing_type].get("electricity", False),
        water=HOUSING_TYPES[housing_type].get("water", False),
        included_board=HOUSING_TYPES[housing_type].get("included_board", False),
        bath=HOUSING_TYPES[housing_type].get("bath", False),
        listed=HOUSING_TYPES[housing_type].get("listed", True),
        unit_ids=unit_ids,
    )
    units = [
        create_housing_unit(unit_id, housing_type, owner, building_id)
        for unit_id in unit_ids
    ]
    return building, units


def create_housing_unit(housing_id, housing_type, owner, building_id=None):
    data = HOUSING_TYPES[housing_type]
    return HousingUnit(
        housing_id=housing_id,
        housing_type=housing_type,
        owner=owner,
        building_id=building_id,
        utility=data["utility"],
        salubrity=data["salubrity"],
        fire_risk=data["fire_risk"],
        rent_price=data["rent_price"],
        electricity=data.get("electricity", False),
        water=data.get("water", False),
        included_board=data.get("included_board", False),
        bath=data.get("bath", False),
        listed=data.get("listed", True),
    )


def vacant_listed_housing_units(city):
    return [
        housing
        for housing in getattr(city, "housing_units", [])
        if housing.listed and not housing.occupants
    ]


def housing_offer_row(housing):
    return {
        "type": "logement",
        "family": "logement",
        "id": housing.housing_type,
        "housing_id": housing.housing_id,
        "label": HOUSING_TYPES.get(housing.housing_type, {}).get("label", housing.housing_type),
        "utility": housing.utility,
        "price": housing.rent_price,
        "quantity": 1,
        "building_id": housing.building_id,
        "owner_id": housing.owner,
        "weight": 0,
        "fractionable": False,
        "salubrity": housing.salubrity,
        "fire_risk": housing.fire_risk,
        "electricity": housing.electricity,
        "water": housing.water,
        "included_board": housing.included_board,
        "bath": housing.bath,
    }


def housing_unit_from_dict(data):
    return HousingUnit(
        housing_id=data.get("housing_id", "housing_unknown"),
        housing_type=data.get("housing_type", "logement"),
        owner=data.get("owner", "Inconnu"),
        building_id=data.get("building_id"),
        occupants=data.get("occupants", []),
        utility=data.get("utility", 0),
        salubrity=data.get("salubrity", 0),
        fire_risk=data.get("fire_risk", 0),
        rent_price=data.get("rent_price", data.get("price", 0)),
        electricity=data.get("electricity", False),
        water=data.get("water", False),
        included_board=data.get("included_board", False),
        bath=data.get("bath", False),
        listed=data.get("listed", True),
    )


def housing_building_from_dict(data):
    return HousingBuilding(
        housing_building_id=data.get("housing_building_id", "housing_building_unknown"),
        name=data.get("name", "Logement"),
        housing_type=data.get("housing_type", "logement"),
        owner=data.get("owner", "Inconnu"),
        building_id=data.get("building_id"),
        visible_if_player_owned=data.get("visible_if_player_owned", True),
        location=data.get("location", "Ville"),
        utility=data.get("utility", 0),
        salubrity=data.get("salubrity", 0),
        fire_risk=data.get("fire_risk", 0),
        rent_price=data.get("rent_price", data.get("price", 0)),
        electricity=data.get("electricity", False),
        water=data.get("water", False),
        included_board=data.get("included_board", False),
        bath=data.get("bath", False),
        listed=data.get("listed", True),
        unit_ids=data.get("unit_ids", []),
    )
