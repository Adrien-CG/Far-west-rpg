"""Definitions legeres des catalogues d'objets.

Les catalogues restent de simples dictionnaires pour faciliter les sauvegardes
et les modifications a la main.
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ItemDefinition:
    id: str
    label: str
    nature: str
    family: str
    base_price: float = 0
    weight: float = 0
    utility: float = 0
    fractionable: bool = False
    saturation: str | int = 0
    perishable: bool = False
    savings_use: bool = False

    def to_dict(self):
        return asdict(self)
