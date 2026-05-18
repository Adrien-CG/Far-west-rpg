from dataclasses import asdict, dataclass, field

from buildings import Building, create_starter_buildings
from population import NPC, generate_population


@dataclass
class City:
    name: str
    day: int = 1
    reputation: int = 0
    security: int = 50
    buildings: list[Building] = field(default_factory=list)
    population: list[NPC] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def get_building_by_id(self, building_id):
        for building in self.buildings:
            if building.building_id == building_id:
                return building

        return None

    def get_npc_by_id(self, npc_id):
        for npc in self.population:
            if npc.npc_id == npc_id:
                return npc

        return None


@dataclass
class GameState:
    character: object
    city: City

    def to_dict(self):
        return {
            "character": self.character.to_dict(),
            "city": self.city.to_dict(),
        }


def create_new_game(character, city_name="Dust Creek"):
    city = City(
        name=city_name,
        buildings=create_starter_buildings(character.name),
        population=generate_population(),
    )

    return GameState(character=character, city=city)
