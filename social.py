"""Relations sociales, alliances, mariage et reputations personnelles."""


def important_people(game):
    return [npc for npc in game.city.population if getattr(npc, "notable", False)]


def relationship_summary(character):
    return {
        "spouse_id": getattr(character, "spouse_id", None),
        "respect": getattr(character, "respect", 0),
        "celebrite": getattr(character, "celebrite", 0),
    }
