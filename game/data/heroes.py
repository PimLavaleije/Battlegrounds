HEROES = {
    "pyramad": {
        "id": "pyramad",
        "name": "Pyramad",
        "description": "Tavern Spreuk: Geef een willekeurige vriend-minion +4 Leven. Kost 1 goud.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "buff_random_health", "amount": 4},
        "emoji": "🏺",
    },
    "ragnaros": {
        "id": "ragnaros",
        "name": "Ragnaros de Vuerheer",
        "description": "Aan het einde van het gevecht: Doe 8 schade aan een willekeurige vijand.",
        "ability": {"type": "end_of_combat", "effect": "deal_damage_random", "amount": 8},
        "emoji": "🔥",
    },
    "george": {
        "id": "george",
        "name": "George de Gevallene",
        "description": "Tavern Spreuk: Geef een vriend-minion Goddelijk Schild. Kost 2 goud.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "give_divine_shield"},
        "emoji": "⚔️",
    },
    "millificent": {
        "id": "millificent",
        "name": "Millificent Manastorm",
        "description": "Jouw winkel bevat altijd minstens 1 Mech.",
        "ability": {"type": "passive", "effect": "always_mech_in_shop"},
        "emoji": "⚙️",
    },
    "rat_king": {
        "id": "rat_king",
        "name": "The Rat King",
        "description": "Jouw minions krijgen elk +1/+1 aan het begin van de ronde.",
        "ability": {"type": "start_of_round", "effect": "buff_all", "attack": 1, "health": 1},
        "emoji": "👑",
    },
    "yogg": {
        "id": "yogg",
        "name": "Yogg-Saron",
        "description": "Na het spelen van een minion: Geef hem een willekeurig keyword.",
        "ability": {"type": "on_play", "effect": "give_random_keyword"},
        "emoji": "🐙",
    },
    "lich_king": {
        "id": "lich_king",
        "name": "Lich King",
        "description": "Jouw Sterf-effecten activeren een extra keer.",
        "ability": {"type": "passive", "effect": "double_deathrattle"},
        "emoji": "💀",
    },
    "sir_finley": {
        "id": "sir_finley",
        "name": "Sir Finley of the Sands",
        "description": "Tavern Spreuk: Ontdek een nieuw Tavern Spreuk. Kost 2 goud.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "discover_hero_power"},
        "emoji": "🐟",
    },
}

HEROES_LIST = list(HEROES.values())
