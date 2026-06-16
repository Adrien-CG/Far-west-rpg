"""Catalogues des objets du jeu.

Ce dossier centralise les entrees par nature d'objet. Les anciens modules
restent disponibles pendant la migration pour garder le jeu stable.
"""

from items.animals import ANIMAL_CATALOG
from items.goods import GOODS_CATALOG
from items.housing import HOUSING_CATALOG
from items.services import SERVICE_CATALOG

__all__ = [
    "ANIMAL_CATALOG",
    "GOODS_CATALOG",
    "HOUSING_CATALOG",
    "SERVICE_CATALOG",
]
