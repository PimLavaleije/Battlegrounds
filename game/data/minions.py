# Minion pool counts per tier
POOL_SIZE = {1: 18, 2: 15, 3: 13, 4: 11, 5: 9, 6: 7}

# Shop size per tavern tier
SHOP_SIZE = {1: 3, 2: 4, 3: 4, 4: 5, 5: 5, 6: 6}

# Token minions (not in shop pool)
TOKENS = {
    "tabbycat": {
        "id": "tabbycat", "name": "Tabbycat", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Beast",
        "abilities": [], "token": True, "description": "Een klein katje."
    },
    "murloc_scout": {
        "id": "murloc_scout", "name": "Murloc Scout", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Murloc",
        "abilities": [], "token": True, "description": "Mrgglll!"
    },
    "joe_bot": {
        "id": "joe_bot", "name": "Jo-E Bot", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Mech",
        "abilities": [], "token": True, "description": "Een vrolijke robot."
    },
    "big_bad_wolf": {
        "id": "big_bad_wolf", "name": "Big Bad Wolf", "tier": 2,
        "attack": 3, "health": 2, "tribe": "Beast",
        "abilities": [], "token": True, "description": "Hoe beter om je mee op te eten."
    },
    "damaged_golem": {
        "id": "damaged_golem", "name": "Beschadigde Golem", "tier": 2,
        "attack": 2, "health": 1, "tribe": "Mech",
        "abilities": [], "token": True, "description": "Bijna kapot maar nog gevaarlijk."
    },
    "spider": {
        "id": "spider", "name": "Spider", "tier": 3,
        "attack": 1, "health": 1, "tribe": "Beast",
        "abilities": [], "token": True, "description": "Een kleine spin."
    },
    "guard_bot": {
        "id": "guard_bot", "name": "Guard Bot", "tier": 4,
        "attack": 2, "health": 3, "tribe": "Mech",
        "abilities": ["taunt"], "token": True, "description": "Beschermt zijn vrienden."
    },
}

# Main minion pool (shop-able)
MINIONS = {
    # ── TIER 1 ──────────────────────────────────────────────
    "alleycat": {
        "id": "alleycat", "name": "Alleycat", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Beast",
        "abilities": ["battlecry"],
        "battlecry": {"type": "summon", "token": "tabbycat"},
        "description": "Slagkreet: Roep een 1/1 Tabbycat op.",
    },
    "murloc_tidehunter": {
        "id": "murloc_tidehunter", "name": "Murloc Tidehunter", "tier": 1,
        "attack": 2, "health": 1, "tribe": "Murloc",
        "abilities": ["battlecry"],
        "battlecry": {"type": "summon", "token": "murloc_scout"},
        "description": "Slagkreet: Roep een 1/1 Murloc Scout op.",
    },
    "fiendish_servant": {
        "id": "fiendish_servant", "name": "Fiendish Servant", "tier": 1,
        "attack": 2, "health": 1, "tribe": "Demon",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "give_attack_random"},
        "description": "Sterf: Geef mijn aanval aan een willekeurige vriend.",
    },
    "vulgar_homunculus": {
        "id": "vulgar_homunculus", "name": "Vulgar Homunculus", "tier": 1,
        "attack": 2, "health": 4, "tribe": "Demon",
        "abilities": ["taunt"],
        "description": "Taunt.",
    },
    "righteous_protector": {
        "id": "righteous_protector", "name": "Righteous Protector", "tier": 1,
        "attack": 1, "health": 1, "tribe": None,
        "abilities": ["taunt", "divine_shield"],
        "description": "Taunt. Goddelijk Schild.",
    },
    "mecharoo": {
        "id": "mecharoo", "name": "Mecharoo", "tier": 1,
        "attack": 1, "health": 1, "tribe": "Mech",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon", "token": "joe_bot"},
        "description": "Sterf: Roep een 1/1 Jo-E Bot op.",
    },

    # ── TIER 2 ──────────────────────────────────────────────
    "scavenging_hyena": {
        "id": "scavenging_hyena", "name": "Scavenging Hyena", "tier": 2,
        "attack": 2, "health": 1, "tribe": "Beast",
        "abilities": ["passive_beast_dies"],
        "passive": {"type": "beast_dies_buff", "attack": 2, "health": 1},
        "description": "Als een vriend-Beast sterft: +2 Aanval, +1 Leven.",
    },
    "kindly_grandmother": {
        "id": "kindly_grandmother", "name": "Kindly Grandmother", "tier": 2,
        "attack": 1, "health": 1, "tribe": "Beast",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon", "token": "big_bad_wolf"},
        "description": "Sterf: Roep een 3/2 Big Bad Wolf op.",
    },
    "unstable_ghoul": {
        "id": "unstable_ghoul", "name": "Unstable Ghoul", "tier": 2,
        "attack": 1, "health": 3, "tribe": "Undead",
        "abilities": ["taunt", "deathrattle"],
        "deathrattle": {"type": "deal_damage_all", "amount": 1},
        "description": "Taunt. Sterf: Doe 1 schade aan alle minions.",
    },
    "harvest_golem": {
        "id": "harvest_golem", "name": "Harvest Golem", "tier": 2,
        "attack": 2, "health": 3, "tribe": "Mech",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon", "token": "damaged_golem"},
        "description": "Sterf: Roep een 2/1 Beschadigde Golem op.",
    },
    "pack_leader": {
        "id": "pack_leader", "name": "Pack Leader", "tier": 2,
        "attack": 3, "health": 3, "tribe": "Beast",
        "abilities": ["passive_beast_summoned"],
        "passive": {"type": "beast_summoned_buff", "attack": 3},
        "description": "Als een vriend-Beast wordt opgeroepen: +3 Aanval.",
    },
    "rockpool_hunter": {
        "id": "rockpool_hunter", "name": "Rockpool Hunter", "tier": 2,
        "attack": 2, "health": 3, "tribe": "Murloc",
        "abilities": ["battlecry"],
        "battlecry": {"type": "buff_tribe", "tribe": "Murloc", "attack": 1, "health": 1},
        "description": "Slagkreet: Geef een vriend-Murloc +1/+1.",
    },

    # ── TIER 3 ──────────────────────────────────────────────
    "infested_wolf": {
        "id": "infested_wolf", "name": "Infested Wolf", "tier": 3,
        "attack": 3, "health": 3, "tribe": "Beast",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_two", "token": "spider"},
        "description": "Sterf: Roep twee 1/1 Spiders op.",
    },
    "soul_juggler": {
        "id": "soul_juggler", "name": "Soul Juggler", "tier": 3,
        "attack": 3, "health": 3, "tribe": "Demon",
        "abilities": ["passive_demon_dies"],
        "passive": {"type": "demon_dies_damage", "amount": 3},
        "description": "Als een vriend-Demon sterft: Doe 3 schade aan een willekeurige vijand.",
    },
    "bronze_warden": {
        "id": "bronze_warden", "name": "Bronze Warden", "tier": 3,
        "attack": 2, "health": 1, "tribe": "Dragon",
        "abilities": ["divine_shield", "reborn"],
        "description": "Goddelijk Schild. Herboren.",
    },
    "arm_of_empire": {
        "id": "arm_of_empire", "name": "Arm of the Empire", "tier": 3,
        "attack": 2, "health": 5, "tribe": None,
        "abilities": ["taunt"],
        "description": "Taunt.",
    },
    "twilight_emissary": {
        "id": "twilight_emissary", "name": "Twilight Emissary", "tier": 3,
        "attack": 4, "health": 4, "tribe": "Dragon",
        "abilities": ["taunt"],
        "description": "Taunt.",
    },
    "houndmaster": {
        "id": "houndmaster", "name": "Houndmaster", "tier": 3,
        "attack": 4, "health": 3, "tribe": None,
        "abilities": ["battlecry"],
        "battlecry": {"type": "buff_tribe", "tribe": "Beast", "attack": 2, "health": 2, "add_taunt": True},
        "description": "Slagkreet: Geef een vriend-Beast +2/+2 en Taunt.",
    },

    # ── TIER 4 ──────────────────────────────────────────────
    "annoy_o_module": {
        "id": "annoy_o_module", "name": "Annoy-o-Module", "tier": 4,
        "attack": 2, "health": 4, "tribe": "Mech",
        "abilities": ["divine_shield", "taunt"],
        "description": "Goddelijk Schild. Taunt.",
    },
    "cave_hydra": {
        "id": "cave_hydra", "name": "Cave Hydra", "tier": 4,
        "attack": 2, "health": 4, "tribe": "Beast",
        "abilities": ["cleave"],
        "description": "Cleave (raakt ook aangrenzende vijanden).",
    },
    "drakonid_enforcer": {
        "id": "drakonid_enforcer", "name": "Drakonid Enforcer", "tier": 4,
        "attack": 3, "health": 6, "tribe": "Dragon",
        "abilities": ["passive_divine_shield_pop"],
        "passive": {"type": "dragon_shield_pop", "attack": 3, "health": 3},
        "description": "+3/+3 wanneer een vriend-Dragon's Goddelijk Schild wordt doorbroken.",
    },
    "bolvar_fireblood": {
        "id": "bolvar_fireblood", "name": "Bolvar, Fireblood", "tier": 4,
        "attack": 1, "health": 7, "tribe": None,
        "abilities": ["divine_shield", "passive_divine_shield_pop"],
        "passive": {"type": "any_shield_pop", "attack": 3},
        "description": "Goddelijk Schild. +3 Aanval wanneer een vriend-Goddelijk Schild doorbroken wordt.",
    },
    "security_rover": {
        "id": "security_rover", "name": "Security Rover", "tier": 4,
        "attack": 2, "health": 6, "tribe": "Mech",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_two", "token": "guard_bot"},
        "description": "Sterf: Roep twee 2/3 Guard Bots met Taunt op.",
    },

    # ── TIER 5 ──────────────────────────────────────────────
    "baron_rivendare": {
        "id": "baron_rivendare", "name": "Baron Rivendare", "tier": 5,
        "attack": 1, "health": 7, "tribe": None,
        "abilities": ["passive_double_deathrattle"],
        "description": "Jouw Sterf-effecten activeren twee keer.",
    },
    "junkbot": {
        "id": "junkbot", "name": "Junkbot", "tier": 5,
        "attack": 1, "health": 5, "tribe": "Mech",
        "abilities": ["passive_mech_dies"],
        "passive": {"type": "mech_dies_buff", "attack": 2, "health": 2},
        "description": "Als een vriend-Mech sterft: +2/+2.",
    },
    "brann_bronzebeard": {
        "id": "brann_bronzebeard", "name": "Brann Bronzebeard", "tier": 5,
        "attack": 2, "health": 4, "tribe": None,
        "abilities": ["passive_double_battlecry"],
        "description": "Jouw Slagkreten activeren twee keer.",
    },
    "lightfang_enforcer": {
        "id": "lightfang_enforcer", "name": "Lightfang Enforcer", "tier": 5,
        "attack": 2, "health": 2, "tribe": None,
        "abilities": [],
        "end_of_turn": {"type": "buff_one_per_tribe", "attack": 2, "health": 1},
        "description": "Einde beurt: Geef één minion van elk tribe-type +2/+1.",
    },

    # ── TIER 6 ──────────────────────────────────────────────
    "maexxna": {
        "id": "maexxna", "name": "Maexxna", "tier": 6,
        "attack": 2, "health": 8, "tribe": "Beast",
        "abilities": ["poisonous"],
        "description": "Giftig (dood elke minion die schade ontvangt).",
    },
    "zapp_slywick": {
        "id": "zapp_slywick", "name": "Zapp Slywick", "tier": 6,
        "attack": 7, "health": 10, "tribe": None,
        "abilities": ["zapp_targeting"],
        "description": "Valt altijd de vijand met de laagste aanval aan.",
    },
    "ghastcoiler": {
        "id": "ghastcoiler", "name": "Ghastcoiler", "tier": 6,
        "attack": 7, "health": 7, "tribe": "Undead",
        "abilities": ["deathrattle"],
        "deathrattle": {"type": "summon_random_deathrattle", "count": 2},
        "description": "Sterf: Roep 2 willekeurige Sterf-minions op.",
    },
    "amalgadon": {
        "id": "amalgadon", "name": "Amalgadon", "tier": 6,
        "attack": 6, "health": 6, "tribe": None,
        "abilities": ["amalgadon_passive"],
        "description": "Krijgt alle keywords van tribes op jouw board.",
    },
}

ALL_MINIONS = {**TOKENS, **MINIONS}

def get_minions_for_tier(tavern_tier):
    """Geeft alle minions terug die beschikbaar zijn voor dit tavern tier."""
    return [m for m in MINIONS.values() if m["tier"] <= tavern_tier]
