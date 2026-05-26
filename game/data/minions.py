# Minion pool counts per tier
POOL_SIZE = {1: 18, 2: 15, 3: 13, 4: 11, 5: 9, 6: 7}

# Shop size per tavern tier
SHOP_SIZE = {1: 3, 2: 4, 3: 4, 4: 5, 5: 5, 6: 6}

# Token minions (not in shop pool)
TOKENS = {
    "skeleton": {
        "id": "skeleton", "name": "Skelet", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Undead",
        "abilities": [], "token": True, "description": "Klein Undead skelet.",
    },
    "whelp": {
        "id": "whelp", "name": "Drakenwelp", "tier": 1,
        "attack": 3, "health": 3, "tribe": "Dragon",
        "abilities": [], "token": True, "description": "Een jonge draak.",
    },
    "microbot": {
        "id": "microbot", "name": "Microbot", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Mech",
        "abilities": [], "token": True, "description": "Een minuscule robot.",
    },
    "cubling": {
        "id": "cubling", "name": "Cubling", "tier": 1,
        "attack": 0, "health": 1, "tribe": "Beast",
        "abilities": ["taunt"], "token": True, "description": "Klein kubusbeest met Taunt.",
    },
    "turtle": {
        "id": "turtle", "name": "Schildpad", "tier": 2,
        "attack": 2, "health": 3, "tribe": "Beast",
        "abilities": ["taunt"], "token": True, "description": "Een schildpad met Taunt.",
    },
    "quilboar_runt": {
        "id": "quilboar_runt", "name": "Quilboar Jong", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Quilboar",
        "abilities": ["taunt"], "token": True, "description": "Een jong Quilboar met Taunt.",
    },
    "sewer_rat_token": {
        "id": "sewer_rat_token", "name": "Rioolrat", "tier": 2,
        "attack": 3, "health": 2, "tribe": "Beast",
        "abilities": [], "token": True, "description": "Een rat uit het riool.",
    },
    "eternal_knight": {
        "id": "eternal_knight", "name": "Eeuwige Ridder", "tier": 2,
        "attack": 4, "health": 2, "tribe": "Undead",
        "abilities": [], "token": True, "description": "Een eeuwige strijder.",
    },
    "sky_pirate": {
        "id": "sky_pirate", "name": "Luchtpiraat", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Pirate",
        "abilities": [], "token": True, "description": "Valt onmiddellijk aan.",
    },
}

# Main minion pool (shop-able)
MINIONS = {
    # ── TIER 1 ──────────────────────────────────────────────
    "wrath_weaver": {
        "id": "wrath_weaver", "name": "Wrath Weaver", "tier": 1,
        "attack": 1, "health": 4, "tribe": "Demon",
        "abilities": [],
        "description": "Na Demon gespeeld: doe 1 schade aan jezelf, +2/+1.",
    },
    "crackling_cyclone": {
        "id": "crackling_cyclone", "name": "Crackling Cyclone", "tier": 1,
        "attack": 2, "health": 1, "tribe": "Elemental",
        "abilities": ["divine_shield", "windfury"],
        "description": "Goddelijk Schild. Windtoom.",
    },
    "harmless_bonehead": {
        "id": "harmless_bonehead", "name": "Harmless Bonehead", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Undead",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_two", "token": "skeleton"},
        "description": "Sterf: Roep twee 1/1 Skeletten op.",
    },
    "risen_rider": {
        "id": "risen_rider", "name": "Risen Rider", "tier": 1,
        "attack": 2, "health": 1, "tribe": "Undead",
        "abilities": ["taunt", "reborn"],
        "description": "Taunt. Herboren.",
    },
    "twilight_hatchling": {
        "id": "twilight_hatchling", "name": "Twilight Hatchling", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Dragon",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon", "token": "whelp"},
        "description": "Sterf: Roep een 3/3 Drakenwelp op.",
    },
    "cord_puller": {
        "id": "cord_puller", "name": "Cord Puller", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Mech",
        "abilities": ["divine_shield", "deathrattle"],
        "deathrattle": {"type": "summon", "token": "microbot"},
        "description": "Goddelijk Schild. Sterf: Roep een 1/1 Microbot op.",
    },
    "manasaber": {
        "id": "manasaber", "name": "Manasaber", "tier": 1,
        "attack": 4, "health": 1, "tribe": "Beast",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_two", "token": "cubling"},
        "description": "Sterf: Roep twee 0/1 Cublings met Taunt op.",
    },

    # ── TIER 2 ──────────────────────────────────────────────
    "sellemental": {
        "id": "sellemental", "name": "Sellemental", "tier": 2,
        "attack": 3, "health": 3, "tribe": "Elemental",
        "abilities": [],
        "description": "Als je dit verkoopt: Voeg een 3/3 Elemental toe aan je winkel.",
    },
    "blazing_skyfin": {
        "id": "blazing_skyfin", "name": "Blazing Skyfin", "tier": 2,
        "attack": 2, "health": 4, "tribe": "Dragon",
        "abilities": [],
        "description": "Na een Slagkreet: +1/+1.",
    },
    "scarlet_skull": {
        "id": "scarlet_skull", "name": "Scarlet Skull", "tier": 2,
        "attack": 2, "health": 1, "tribe": "Undead",
        "abilities": ["reborn", "deathrattle"],
        "deathrattle": {"type": "buff_tribe", "tribe": "Undead", "attack": 1, "health": 2, "all": True},
        "description": "Herboren. Sterf: Geef jouw Undead +1/+2.",
    },
    "humming_bird": {
        "id": "humming_bird", "name": "Humming Bird", "tier": 2,
        "attack": 1, "health": 4, "tribe": "Beast",
        "abilities": ["passive_beast_aura"],
        "passive": {"type": "beast_aura", "attack": 1},
        "description": "Gevecht start: Jouw Beesten krijgen +1 Aanval.",
    },
    "sewer_rat": {
        "id": "sewer_rat", "name": "Sewer Rat", "tier": 2,
        "attack": 3, "health": 2, "tribe": "Beast",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon", "token": "turtle"},
        "description": "Sterf: Roep een 2/3 Schildpad met Taunt op.",
    },
    "nerubian_deathswarmer": {
        "id": "nerubian_deathswarmer", "name": "Nerubian Deathswarmer", "tier": 2,
        "attack": 1, "health": 4, "tribe": "Undead",
        "abilities": ["battlecry"],
        "battlecry": {"type": "buff_tribe", "tribe": "Undead", "attack": 1, "health": 0, "all": True},
        "description": "Slagkreet: Jouw Undead krijgen +1 Aanval voor het hele spel.",
    },
    "glowgullet_warlord": {
        "id": "glowgullet_warlord", "name": "Glowgullet Warlord", "tier": 2,
        "attack": 2, "health": 2, "tribe": "Quilboar",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_two", "token": "quilboar_runt"},
        "description": "Sterf: Roep twee 1/1 Quilboar met Taunt op.",
    },

    # ── TIER 3 ──────────────────────────────────────────────
    "deflect_o_bot": {
        "id": "deflect_o_bot", "name": "Deflect-o-Bot", "tier": 3,
        "attack": 3, "health": 2, "tribe": "Mech",
        "abilities": ["divine_shield"],
        "description": "Goddelijk Schild. Elke keer dat je een Mech koopt: +2 Aanval en Goddelijk Schild.",
    },
    "annoy_o_module": {
        "id": "annoy_o_module", "name": "Annoy-o-Module", "tier": 3,
        "attack": 2, "health": 4, "tribe": "Mech",
        "abilities": ["divine_shield", "taunt"],
        "description": "Goddelijk Schild. Taunt.",
    },
    "deadly_spore": {
        "id": "deadly_spore", "name": "Deadly Spore", "tier": 3,
        "attack": 1, "health": 1, "tribe": None,
        "abilities": ["poisonous"],
        "description": "Giftig (dood elke minion die schade ontvangt).",
    },
    "floating_watcher": {
        "id": "floating_watcher", "name": "Floating Watcher", "tier": 3,
        "attack": 4, "health": 4, "tribe": "Demon",
        "abilities": [],
        "description": "Na onbeschermde schade aan je held: +2/+2.",
    },
    "hardy_orca": {
        "id": "hardy_orca", "name": "Hardy Orca", "tier": 3,
        "attack": 1, "health": 6, "tribe": "Beast",
        "abilities": ["taunt"],
        "description": "Taunt. Als dit schade ontvangt: andere vrienden +1/+1.",
    },
    "cadaver_caretaker": {
        "id": "cadaver_caretaker", "name": "Cadaver Caretaker", "tier": 3,
        "attack": 3, "health": 3, "tribe": "Undead",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_count", "token": "skeleton", "count": 3},
        "description": "Sterf: Roep drie 1/1 Skeletten op.",
    },
    "mama_mrrglton": {
        "id": "mama_mrrglton", "name": "Mama Mrrglton", "tier": 3,
        "attack": 5, "health": 3, "tribe": "Murloc",
        "abilities": ["battlecry"],
        "battlecry": {"type": "buff_tribe", "tribe": "Murloc", "attack": 3, "health": 0, "all": True},
        "description": "Slagkreet: Geef jouw andere Murlocs +3 Aanval.",
    },

    # ── TIER 4 ──────────────────────────────────────────────
    "tunnel_blaster": {
        "id": "tunnel_blaster", "name": "Tunnel Blaster", "tier": 4,
        "attack": 3, "health": 7, "tribe": None,
        "abilities": ["taunt", "deathrattle"],
        "deathrattle": {"type": "deal_damage_all", "amount": 3},
        "description": "Taunt. Sterf: Doe 3 schade aan alle minions.",
    },
    "determined_defender": {
        "id": "determined_defender", "name": "Determined Defender", "tier": 4,
        "attack": 5, "health": 5, "tribe": None,
        "abilities": ["taunt", "deathrattle"],
        "deathrattle": {"type": "buff_adjacent", "attack": 5, "health": 5, "add_taunt": True},
        "description": "Taunt. Sterf: Geef aangrenzende vrienden +5/+5 en Taunt.",
    },
    "king_bagurgle": {
        "id": "king_bagurgle", "name": "King Bagurgle", "tier": 4,
        "attack": 4, "health": 4, "tribe": "Murloc",
        "abilities": ["battlecry"],
        "battlecry": {"type": "buff_tribe", "tribe": "Murloc", "attack": 2, "health": 3, "all": True},
        "description": "Slagkreet: Geef jouw andere Murlocs +2/+3.",
    },
    "plaguerunner": {
        "id": "plaguerunner", "name": "Plaguerunner", "tier": 4,
        "attack": 4, "health": 2, "tribe": "Undead",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "buff_tribe", "tribe": "Undead", "attack": 2, "health": 0, "all": True},
        "description": "Sterf: Geef jouw Undead +2 Aanval.",
    },
    "imposing_percussionist": {
        "id": "imposing_percussionist", "name": "Imposing Percussionist", "tier": 4,
        "attack": 4, "health": 4, "tribe": "Demon",
        "abilities": ["battlecry"],
        "battlecry": {"type": "buff_tribe", "tribe": "Demon", "attack": 2, "health": 2},
        "description": "Slagkreet: Geef een vriend-Demon +2/+2.",
    },
    "banana_slamma": {
        "id": "banana_slamma", "name": "Banana Slamma", "tier": 4,
        "attack": 3, "health": 6, "tribe": "Beast",
        "abilities": [],
        "description": "Als een vriend-Beest wordt opgeroepen: verdubbel zijn stats.",
    },
    "monstrous_macaw": {
        "id": "monstrous_macaw", "name": "Monstrous Macaw", "tier": 4,
        "attack": 5, "health": 4, "tribe": "Beast",
        "abilities": [],
        "description": "Rally: Activeer het meest-linkse Sterf-effect.",
    },

    # ── TIER 5 ──────────────────────────────────────────────
    "bile_spitter": {
        "id": "bile_spitter", "name": "Bile Spitter", "tier": 5,
        "attack": 1, "health": 10, "tribe": "Murloc",
        "abilities": ["poisonous"],
        "description": "Giftig. Rally: een ander Murloc krijgt ook Giftig.",
    },
    "sewer_lord": {
        "id": "sewer_lord", "name": "Sewer Lord", "tier": 5,
        "attack": 4, "health": 6, "tribe": "Beast",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_two", "token": "sewer_rat_token"},
        "description": "Sterf: Roep twee 3/2 Rioolratten op.",
    },
    "tichondrius": {
        "id": "tichondrius", "name": "Tichondrius", "tier": 5,
        "attack": 3, "health": 6, "tribe": "Demon",
        "abilities": [],
        "description": "Na schade aan je held: Demonen +2/+1.",
    },
    "divine_sparkbot": {
        "id": "divine_sparkbot", "name": "Divine Sparkbot", "tier": 5,
        "attack": 4, "health": 2, "tribe": "Mech",
        "abilities": ["divine_shield", "taunt"],
        "description": "Goddelijk Schild. Taunt.",
    },
    "spiked_savior": {
        "id": "spiked_savior", "name": "Spiked Savior", "tier": 5,
        "attack": 8, "health": 2, "tribe": "Beast",
        "abilities": ["taunt", "reborn", "deathrattle"],
        "deathrattle": {"type": "buff_all_health", "amount": 1},
        "description": "Taunt. Herboren. Sterf: Geef alle vrienden +1 Leven.",
    },
    "kalecgos": {
        "id": "kalecgos", "name": "Kalecgos, Arcane Aspect", "tier": 5,
        "attack": 4, "health": 12, "tribe": "Dragon",
        "abilities": [],
        "description": "Na een Slagkreet: Jouw Draken +1/+1.",
    },
    "sinrunner_blanchy": {
        "id": "sinrunner_blanchy", "name": "Sinrunner Blanchy", "tier": 5,
        "attack": 8, "health": 8, "tribe": "Undead",
        "abilities": ["reborn"],
        "description": "Herboren. In gevecht: Herboren met vol Leven.",
    },

    # ── TIER 6 ──────────────────────────────────────────────
    "goldrinn": {
        "id": "goldrinn", "name": "Goldrinn, de Grote Wolf", "tier": 6,
        "attack": 8, "health": 8, "tribe": "Beast",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "buff_tribe_attack", "tribe": "Beast", "attack": 6},
        "description": "Sterf: Geef jouw Beesten +6 Aanval.",
    },
    "elemental_of_surprise": {
        "id": "elemental_of_surprise", "name": "Elemental of Surprise", "tier": 6,
        "attack": 8, "health": 8, "tribe": "Elemental",
        "abilities": ["divine_shield"],
        "description": "Goddelijk Schild.",
    },
    "eternal_summoner": {
        "id": "eternal_summoner", "name": "Eternal Summoner", "tier": 6,
        "attack": 8, "health": 1, "tribe": "Undead",
        "abilities": ["reborn", "deathrattle"],
        "deathrattle": {"type": "summon", "token": "eternal_knight"},
        "description": "Herboren. Sterf: Roep een 4/2 Eeuwige Ridder op.",
    },
    "ship_jumper": {
        "id": "ship_jumper", "name": "Ship Jumper", "tier": 6,
        "attack": 6, "health": 6, "tribe": "Pirate",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon", "token": "sky_pirate"},
        "description": "Sterf: Roep een 1/1 Luchtpiraat op met jouw Aanval.",
    },
    "nightbane_ignited": {
        "id": "nightbane_ignited", "name": "Nightbane, Ignited", "tier": 6,
        "attack": 16, "health": 8, "tribe": "Dragon",
        "abilities": ["taunt"],
        "description": "Taunt. Sterf: Geef 2 vrienden dit minion's Aanval.",
    },
    "moonsteel_juggernaut": {
        "id": "moonsteel_juggernaut", "name": "Moonsteel Juggernaut", "tier": 6,
        "attack": 8, "health": 8, "tribe": "Mech",
        "abilities": [],
        "description": "Einde beurt: Krijg een 6/6 Magnetic Satellite.",
    },
    "rabid_panther": {
        "id": "rabid_panther", "name": "Rabid Panther", "tier": 6,
        "attack": 4, "health": 8, "tribe": "Beast",
        "abilities": [],
        "description": "Na een vriend-Beest: Beesten +3/+3 en 1 schade.",
    },
}

ALL_MINIONS = {**TOKENS, **MINIONS}


def get_minions_for_tier(tavern_tier):
    """Geeft alle minions terug die beschikbaar zijn voor dit tavern tier."""
    return [m for m in MINIONS.values() if m["tier"] <= tavern_tier]
