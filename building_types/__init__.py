"""Classes specialisees des batiments.

Plan du fichier:
01 - imports: classes de batiments disponibles.
02 - BUILDING_CLASS_BY_TYPE: registre type -> classe.
03 - building_class_for: retrouve la classe d'un type.
04 - __all__: exports publics du paquet.
"""

from building_types.bank import Bank
from building_types.barber_shop import BarberShop
from building_types.carpenter import Carpenter
from building_types.church import Church
from building_types.county_hall import CountyHall
from building_types.farm import Farm
from building_types.farrier import Farrier
from building_types.fort import Fort
from building_types.general_store import GeneralStore
from building_types.hotel import Hotel
from building_types.lumber_camp import LumberCamp
from building_types.medical_office import MedicalOffice
from building_types.mine import Mine
from building_types.newspaper import Newspaper
from building_types.office import Office
from building_types.post_office import PostOffice
from building_types.ranch import Ranch
from building_types.restaurant import Restaurant
from building_types.saloon import Saloon
from building_types.school import School
from building_types.sheriff_office import SheriffOffice
from building_types.tailor import Tailor
from building_types.trapper_post import TrapperPost


BUILDING_CLASS_BY_TYPE = {
    "Banque": Bank,
    "Barber shop": BarberShop,
    "Bureau": Office,
    "Bureau du sherif": SheriffOffice,
    "Cabinet médical": MedicalOffice,
    "Cabinet mÃ©dical": MedicalOffice,
    "Camp de bucheron": LumberCamp,
    "Charpentier": Carpenter,
    "Comptoir de trappeur": TrapperPost,
    "County hall": CountyHall,
    "Ferme": Farm,
    "Fort": Fort,
    "General Store": GeneralStore,
    "Hôtel": Hotel,
    "HÃ´tel": Hotel,
    "Journal": Newspaper,
    "Maréchal ferrant": Farrier,
    "MarÃ©chal ferrant": Farrier,
    "Mine": Mine,
    "Post Office": PostOffice,
    "Ranch": Ranch,
    "Restaurant": Restaurant,
    "Saloon": Saloon,
    "Tailleur": Tailor,
    "École": School,
    "Ã‰cole": School,
    "Église": Church,
    "Ã‰glise": Church,
}


def building_class_for(building_type):
    return BUILDING_CLASS_BY_TYPE.get(building_type)


__all__ = [
    "BUILDING_CLASS_BY_TYPE",
    "Bank",
    "BarberShop",
    "Carpenter",
    "Church",
    "CountyHall",
    "Farm",
    "Farrier",
    "Fort",
    "GeneralStore",
    "Hotel",
    "LumberCamp",
    "MedicalOffice",
    "Mine",
    "Newspaper",
    "Office",
    "PostOffice",
    "Ranch",
    "Restaurant",
    "Saloon",
    "School",
    "SheriffOffice",
    "Tailor",
    "TrapperPost",
    "building_class_for",
]
