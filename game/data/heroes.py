# heroes.py — Complete BG hero pool (Season 13 / Patch 35.2)
# Source: hearthstone.wiki.gg BG hero table
#
# ability.type:
#   "hero_power"  — active button, costs gold, player clicks
#   "passive"     — always-on or auto-triggered, no gold cost
#
# ability.cost   — gold cost (hero_power only)
# ability.effect — internal slug; many are stubs pending implementation
# armor          — starting armor value (absorbs damage before HP)
# hp_override    — only set when base HP differs from standard 40

HEROES = {
    # ── A ──────────────────────────────────────────────────────
    "af_kay": {
        "id": "af_kay", "name": "A. F. Kay", "armor": 15, "emoji": "😴",
        "description": "Skip your first two turns, then Discover two minions from Tier 3.",
        "ability": {"type": "passive", "effect": "procrastinate"},
    },
    "alakir": {
        "id": "alakir", "name": "Al'Akir", "armor": 15, "emoji": "🌪️",
        "description": "Start of Combat: Give your left-most minion Windfury, Divine Shield, and Taunt.",
        "ability": {"type": "passive", "effect": "alakir_start_of_combat"},
    },
    "alexstrasza": {
        "id": "alexstrasza", "name": "Alexstrasza", "armor": 10, "emoji": "🐉",
        "description": "Discover a Dragon. (Unlocks at Tier 4.)",
        "ability": {"type": "hero_power", "cost": 1, "effect": "discover_dragon", "unlock_tier": 4},
    },
    "ambassador_faelin": {
        "id": "ambassador_faelin", "name": "Ambassador Faelin", "armor": 14, "emoji": "🧭",
        "description": "Skip your first turn. Discover a Tier 2, 4, and 6 minion.",
        "ability": {"type": "passive", "effect": "expedition_plans"},
    },
    "aranna_starseeker": {
        "id": "aranna_starseeker", "name": "Aranna Starseeker", "armor": 12, "emoji": "🏹",
        "description": "After 14 friendly minions attack, the first minion you buy each turn is free.",
        "ability": {"type": "passive", "effect": "demon_hunter_training", "threshold": 14},
    },
    "arch_villain_rafaam": {
        "id": "arch_villain_rafaam", "name": "Arch-Villain Rafaam", "armor": 15, "emoji": "🦹",
        "description": "Next combat, get a plain copy of the first minion you kill.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "ill_take_that"},
    },
    "artanis": {
        "id": "artanis", "name": "Artanis", "armor": 18, "emoji": "🔮",
        "description": "Choose from 2 Protoss minions to get after you buy 14 cards.",
        "ability": {"type": "passive", "effect": "warp_gate", "threshold": 14},
    },
    # ── B ──────────────────────────────────────────────────────
    "brukan": {
        "id": "brukan", "name": "Bru'kan", "armor": 15, "emoji": "⚡",
        "description": "Choose an Element. Start of Combat: Call upon that Element.",
        "ability": {"type": "passive", "effect": "embrace_the_elements"},
    },
    "buttons": {
        "id": "buttons", "name": "Buttons", "armor": 16, "emoji": "🎁",
        "description": "On Turn 8, choose a Greater Trinket to buy.",
        "ability": {"type": "passive", "effect": "growing_collection", "turn": 8},
    },
    # ── C ──────────────────────────────────────────────────────
    "cthun": {
        "id": "cthun", "name": "C'Thun", "armor": 20, "emoji": "👁️",
        "description": "At end of turn, give a friendly minion +1/+1. Repeat 0 times.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "saturday_cthuns"},
    },
    "capn_hoggarr": {
        "id": "capn_hoggarr", "name": "Cap'n Hoggarr", "armor": 12, "emoji": "⚓",
        "description": "After you buy a Pirate, gain 1 Gold.",
        "ability": {"type": "passive", "effect": "im_the_capn_now"},
    },
    "captain_eudora": {
        "id": "captain_eudora", "name": "Captain Eudora", "armor": 14, "emoji": "💎",
        "description": "Dig for a Golden minion! (4 Digs left.)",
        "ability": {"type": "hero_power", "cost": 1, "effect": "buried_treasure", "digs_remaining": 4},
    },
    "captain_hooktusk": {
        "id": "captain_hooktusk", "name": "Captain Hooktusk", "armor": 14, "emoji": "☠️",
        "description": "Remove a friendly minion. Discover one from a Tier lower.",
        "ability": {"type": "passive", "effect": "trash_for_treasure"},
    },
    "cariel_roame": {
        "id": "cariel_roame", "name": "Cariel Roame", "armor": 18, "emoji": "⚔️",
        "description": "Give 1 random friendly minion +1/+1. After each combat, choose an improvement.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "conviction"},
    },
    "chenvaala": {
        "id": "chenvaala", "name": "Chenvaala", "armor": 15, "emoji": "❄️",
        "description": "After you play 3 Elementals, reduce the Cost of upgrading the Tavern by (3).",
        "ability": {"type": "passive", "effect": "avalanche", "threshold": 3, "discount": 3},
    },
    "cho": {
        "id": "cho", "name": "Cho", "armor": 14, "emoji": "🥊",
        "description": "Whenever you play a Golden minion, both you and Gall get a Triple Reward.",
        "ability": {"type": "passive", "effect": "double_trouble_cho"},
    },
    "cookie_the_cook": {
        "id": "cookie_the_cook", "name": "Cookie the Cook", "armor": 8, "emoji": "🍳",
        "description": "Throw a minion in your pot. When gathered 3, Discover from their types.",
        "ability": {"type": "passive", "effect": "stir_the_pot", "pot_capacity": 3},
    },
    # ── D ──────────────────────────────────────────────────────
    "dancin_deryl": {
        "id": "dancin_deryl", "name": "Dancin' Deryl", "armor": 16, "emoji": "🎩",
        "description": "When you play a minion, give it a +1/+1 hat that passes when sold.",
        "ability": {"type": "passive", "effect": "hat_trick"},
    },
    "death_speaker_blackthorn": {
        "id": "death_speaker_blackthorn", "name": "Death Speaker Blackthorn", "armor": 18, "emoji": "💀",
        "description": "Get 2 Blood Gems. (Twice per turn.)",
        "ability": {"type": "hero_power", "cost": 1, "effect": "bloodbound", "gems": 2, "uses_per_turn": 2},
    },
    "deathwing": {
        "id": "deathwing", "name": "Deathwing", "armor": 18, "emoji": "🔥",
        "description": "Start of Combat: Give ALL minions +2 Attack permanently.",
        "ability": {"type": "passive", "effect": "all_will_burn", "attack": 2},
    },
    "dinotamer_brann": {
        "id": "dinotamer_brann", "name": "Dinotamer Brann", "armor": 18, "emoji": "🦕",
        "description": "After you buy 5 Battlecry minions, get a Brann Bronzebeard.",
        "ability": {"type": "passive", "effect": "battle_brand", "threshold": 5},
    },
    "doctor_hollidaie": {
        "id": "doctor_hollidaie", "name": "Doctor Holli'dae", "armor": 14, "emoji": "🧪",
        "description": "Get a random Tavern spell.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "blessing_nine_frogs"},
    },
    "drekthar": {
        "id": "drekthar", "name": "Drek'Thar", "armor": 10, "emoji": "🐺",
        "description": "When you have space in combat, summon a copy of your highest-Attack minion.",
        "ability": {"type": "passive", "effect": "frostwolf_fervor"},
    },
    # ── E ──────────────────────────────────────────────────────
    "etc_band_manager": {
        "id": "etc_band_manager", "name": "E.T.C., Band Manager", "armor": 14, "emoji": "🎸",
        "description": "Discover a Buddy. (Unlocks at Tier 2.)",
        "ability": {"type": "hero_power", "cost": 3, "effect": "sign_new_artist", "unlock_tier": 2},
    },
    "edwin_vancleef": {
        "id": "edwin_vancleef", "name": "Edwin VanCleef", "armor": 18, "emoji": "🗡️",
        "description": "Give a minion +2/+2. Upgrades after you buy 5 cards.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "sharpen_blades", "attack": 2, "health": 2, "upgrade_threshold": 5},
    },
    "elise_starseeker": {
        "id": "elise_starseeker", "name": "Elise Starseeker", "armor": 15, "emoji": "🗺️",
        "description": "Discover a minion from your Tier. Costs (1) more after each use.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "lead_explorer"},
    },
    "enhanceo_mechano": {
        "id": "enhanceo_mechano", "name": "Enhance-o Mechano", "armor": 20, "emoji": "🔧",
        "description": "After each Refresh, give a minion in the Tavern a random Bonus Keyword.",
        "ability": {"type": "passive", "effect": "enhancification"},
    },
    "exarch_othaar": {
        "id": "exarch_othaar", "name": "Exarch Othaar", "armor": 15, "emoji": "💠",
        "description": "The next Tavern spell you buy costs (1) less. (Unlocks on Turn 3.)",
        "ability": {"type": "passive", "effect": "arcane_knowledge", "unlock_turn": 3},
    },
    # ── F ──────────────────────────────────────────────────────
    "farseer_nobundo": {
        "id": "farseer_nobundo", "name": "Farseer Nobundo", "armor": 15, "emoji": "🌊",
        "description": "Get a copy of the last Tavern spell you cast. Next Hero Power costs (1) less.",
        "ability": {"type": "hero_power", "cost": 3, "effect": "galaxy_lens"},
    },
    "flobbidinous_floop": {
        "id": "flobbidinous_floop", "name": "Flobbidinous Floop", "armor": 15, "emoji": "🔮",
        "description": "Choose a friendly minion. Transform it into your teammate's highest-Tier minion.",
        "ability": {"type": "passive", "effect": "glorious_gloop"},
    },
    "forest_lord_cenarius": {
        "id": "forest_lord_cenarius", "name": "Forest Lord Cenarius", "armor": 16, "emoji": "🌳",
        "description": "Increase your maximum Gold by 1.",
        "ability": {"type": "hero_power", "cost": 3, "effect": "wisdom_of_ancients"},
    },
    "forest_warden_omu": {
        "id": "forest_warden_omu", "name": "Forest Warden Omu", "armor": 6, "emoji": "🌿",
        "description": "After you upgrade the Tavern, gain 2 Gold.",
        "ability": {"type": "passive", "effect": "everbloom", "gold_gain": 2},
    },
    "fungalmancer_flurgl": {
        "id": "fungalmancer_flurgl", "name": "Fungalmancer Flurgl", "armor": 12, "emoji": "🐸",
        "description": "After you sell 5 minions, get a random Murloc.",
        "ability": {"type": "passive", "effect": "gone_fishing", "threshold": 5},
    },
    # ── G ──────────────────────────────────────────────────────
    "galakrond": {
        "id": "galakrond", "name": "Galakrond", "armor": 18, "emoji": "🌑",
        "description": "Choose a minion in the Tavern. Then choose a higher Tier minion to replace it.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "galakronds_greed"},
    },
    "galewing": {
        "id": "galewing", "name": "Galewing", "armor": 10, "emoji": "🦅",
        "description": "Choose a new flightpath. Complete it to get a bonus!",
        "ability": {"type": "passive", "effect": "dungars_gryphon"},
    },
    "gall": {
        "id": "gall", "name": "Gall", "armor": 14, "emoji": "😈",
        "description": "Whenever you play a Golden minion, both you and Cho get a Triple Reward.",
        "ability": {"type": "passive", "effect": "double_trouble_gall"},
    },
    "genn_worgen_king": {
        "id": "genn_worgen_king", "name": "Genn, Worgen King", "armor": 7, "emoji": "🐺",
        "description": "On Turn 4, Discover two Hero Powers to replace this.",
        "ability": {"type": "passive", "effect": "king_of_duality", "unlock_turn": 4},
    },
    "george_the_fallen": {
        "id": "george_the_fallen", "name": "George the Fallen", "armor": 15, "emoji": "✝️",
        "description": "Give a minion Divine Shield.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "give_divine_shield"},
    },
    "greybough": {
        "id": "greybough", "name": "Greybough", "armor": 16, "emoji": "🌲",
        "description": "Give +1/+2 and Taunt to minions you summon during combat.",
        "ability": {"type": "passive", "effect": "sprout_it_out", "attack": 1, "health": 2},
    },
    "guff_runetotem": {
        "id": "guff_runetotem", "name": "Guff Runetotem", "armor": 12, "emoji": "🦬",
        "description": "After you buy 20 Tiers' worth of cards, get a Triple Reward.",
        "ability": {"type": "passive", "effect": "natural_balance", "threshold": 20},
    },
    # ── H ──────────────────────────────────────────────────────
    "heistbaron_togwaggle": {
        "id": "heistbaron_togwaggle", "name": "Heistbaron Togwaggle", "armor": 14, "emoji": "👑",
        "description": "Steal all cards from the Tavern. Each turn, your next Hero Power costs (1) less.",
        "ability": {"type": "hero_power", "cost": 11, "effect": "the_perfect_crime"},
    },
    # ── I ──────────────────────────────────────────────────────
    "illidan_stormrage": {
        "id": "illidan_stormrage", "name": "Illidan Stormrage", "armor": 18, "emoji": "😈",
        "description": "Your left and right-most minions gain +2/+1 and attack immediately.",
        "ability": {"type": "passive", "effect": "wingmen", "attack": 2, "health": 1},
    },
    "infinite_toki": {
        "id": "infinite_toki", "name": "Infinite Toki", "armor": 10, "emoji": "⏰",
        "description": "Refresh the Tavern. Include two minions from a Tier higher than yours.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "temporal_tavern"},
    },
    "inge_iron_hymn": {
        "id": "inge_iron_hymn", "name": "Inge, the Iron Hymn", "armor": 17, "emoji": "🎵",
        "description": "Give a minion Attack equal to your Tier. (Swaps to Health next turn!)",
        "ability": {"type": "passive", "effect": "major_hymn"},
    },
    "ini_stormcoil": {
        "id": "ini_stormcoil", "name": "Ini Stormcoil", "armor": 15, "emoji": "🤖",
        "description": "After 9 friendly minions die, get a random Mech.",
        "ability": {"type": "passive", "effect": "mechgyver", "threshold": 9},
    },
    # ── J ──────────────────────────────────────────────────────
    "jandice_barov": {
        "id": "jandice_barov", "name": "Jandice Barov", "armor": 18, "emoji": "🎪",
        "description": "Swap a friendly non-Golden minion with a random one in the Tavern.",
        "ability": {"type": "passive", "effect": "swap_lock_and_shop"},
    },
    "jim_raynor": {
        "id": "jim_raynor", "name": "Jim Raynor", "armor": 16, "emoji": "🚀",
        "description": "Start the game with a 2/2 Battlecruiser. Add Battlecruiser Upgrade when Tavern Refreshed.",
        "ability": {"type": "passive", "effect": "lift_off"},
    },
    # ── K ──────────────────────────────────────────────────────
    "kaelthas_sunstrider": {
        "id": "kaelthas_sunstrider", "name": "Kael'thas Sunstrider", "armor": 16, "emoji": "🔥",
        "description": "After you buy 3 minions, get a Tavern Coin.",
        "ability": {"type": "passive", "effect": "verdant_spheres", "threshold": 3},
    },
    "kerrigan": {
        "id": "kerrigan", "name": "Kerrigan, Queen of Blades", "armor": 14, "emoji": "👾",
        "description": "Unlock Tier 2 Zerg. Costs (1) less each turn. Start the game with a 2/2 Larva.",
        "ability": {"type": "hero_power", "cost": 6, "effect": "spawning_pool"},
    },
    "king_mukla": {
        "id": "king_mukla", "name": "King Mukla", "armor": 16, "emoji": "🐒",
        "description": "At the start of your turn, get 2 Bananas and give everyone else one.",
        "ability": {"type": "passive", "effect": "bananarama", "bananas": 2},
    },
    "kurtrus_ashfallen": {
        "id": "kurtrus_ashfallen", "name": "Kurtrus Ashfallen", "armor": 14, "emoji": "🗡️",
        "description": "Once per turn, after you buy 3 minions, get a plain copy of one of them.",
        "ability": {"type": "passive", "effect": "glaive_ricochet", "threshold": 3},
    },
    # ── L ──────────────────────────────────────────────────────
    "lady_vashj": {
        "id": "lady_vashj", "name": "Lady Vashj", "armor": 16, "emoji": "🐍",
        "description": "At the start of each turn, get a random Spellcraft spell.",
        "ability": {"type": "passive", "effect": "relics_of_the_deep"},
    },
    "lich_bazhial": {
        "id": "lich_bazhial", "name": "Lich Baz'hial", "armor": 18, "emoji": "☠️",
        "description": "Steal a card from the Tavern. Take 2 damage.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "graveyard_shift", "self_damage": 2},
    },
    "loh_living_legend": {
        "id": "loh_living_legend", "name": "Loh, the Living Legend", "armor": 17, "emoji": "🏆",
        "description": "After 15 friendly minions attack, get a Triple Reward.",
        "ability": {"type": "passive", "effect": "heroic_inspiration", "threshold": 15},
    },
    "lord_barov": {
        "id": "lord_barov", "name": "Lord Barov", "armor": 14, "emoji": "⚖️",
        "description": "Guess which player will win their next combat. If correct, get 3 Tavern Coins.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "friendly_wager", "reward_coins": 3},
    },
    "lord_jaraxxus": {
        "id": "lord_jaraxxus", "name": "Lord Jaraxxus", "armor": 15, "emoji": "🔱",
        "description": "After friendly minions deal 150 damage, open a portal to the Twisting Nether!",
        "ability": {"type": "passive", "effect": "bloodfury", "threshold": 150},
    },
    # ── M ──────────────────────────────────────────────────────
    "madam_goya": {
        "id": "madam_goya", "name": "Madam Goya", "armor": 8, "emoji": "🎎",
        "description": "Pass a non-Golden minion.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "efficient_exchange"},
    },
    "maiev_shadowsong": {
        "id": "maiev_shadowsong", "name": "Maiev Shadowsong", "armor": 17, "emoji": "🌑",
        "description": "Choose a card in the Tavern to lock in your hand. After 2 turns, unlock it.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "imprison", "lock_turns": 2},
    },
    "malygos": {
        "id": "malygos", "name": "Malygos", "armor": 17, "emoji": "🔵",
        "description": "Replace a card with a random one of the same Tier. (Twice per turn.)",
        "ability": {"type": "passive", "effect": "arcane_alteration", "uses_per_turn": 2},
    },
    "marin_the_manager": {
        "id": "marin_the_manager", "name": "Marin the Manager", "armor": 12, "emoji": "💼",
        "description": "On Turn 5, choose a Lesser Trinket to buy.",
        "ability": {"type": "passive", "effect": "fantastic_treasure", "turn": 5},
    },
    "master_nguyen": {
        "id": "master_nguyen", "name": "Master Nguyen", "armor": 10, "emoji": "🌀",
        "description": "At the start of every turn, choose from 2 new Hero Powers.",
        "ability": {"type": "passive", "effect": "power_of_the_storm"},
    },
    "millhouse_manastorm": {
        "id": "millhouse_manastorm", "name": "Millhouse Manastorm", "armor": 16, "emoji": "🔮",
        "description": "Minions and Refreshes cost 2 Gold. Upgrading the Tavern costs (1) more.",
        "ability": {"type": "passive", "effect": "manastorm", "buy_cost": 2, "refresh_cost": 2, "upgrade_cost_penalty": 1},
    },
    "millificent_manastorm": {
        "id": "millificent_manastorm", "name": "Millificent Manastorm", "armor": 15, "emoji": "⚙️",
        "description": "Discover a Magnetic Mech. (Unlocks at Tier 4.)",
        "ability": {"type": "hero_power", "cost": 1, "effect": "discover_magnetic_mech", "unlock_tier": 4},
    },
    "mister_clocksworth": {
        "id": "mister_clocksworth", "name": "Mister Clocksworth", "armor": 18, "emoji": "⏱️",
        "description": "You only need 2 copies to make a minion Golden. Goldens give Tavern Coins instead.",
        "ability": {"type": "passive", "effect": "double_time"},
    },
    "morchie": {
        "id": "morchie", "name": "Morchie", "armor": 8, "emoji": "⌛",
        "description": "On Turn 5, visit the Minor Timewarp.",
        "ability": {"type": "passive", "effect": "warped_conflux", "turn": 5},
    },
    "mr_bigglesworth": {
        "id": "mr_bigglesworth", "name": "Mr. Bigglesworth", "armor": 19, "emoji": "🐱",
        "description": "After another hero dies, Discover a minion from their warband. It keeps enchantments.",
        "ability": {"type": "passive", "effect": "kelthuzads_kitty"},
    },
    "murloc_holmes": {
        "id": "murloc_holmes", "name": "Murloc Holmes", "armor": 12, "emoji": "🔍",
        "description": "Look at 2 minions. Guess which one your next opponent had last combat for a Tavern Coin.",
        "ability": {"type": "passive", "effect": "detective_for_hire"},
    },
    "murozond_unbounded": {
        "id": "murozond_unbounded", "name": "Murozond, Unbounded", "armor": 12, "emoji": "⏳",
        "description": "On Turn 8, visit the Major Timewarp.",
        "ability": {"type": "passive", "effect": "alternate_timeline", "turn": 8},
    },
    "mutanus_the_devourer": {
        "id": "mutanus_the_devourer", "name": "Mutanus the Devourer", "armor": 20, "emoji": "🦑",
        "description": "Sell a friendly minion. Spit its stats onto another.",
        "ability": {"type": "passive", "effect": "devour"},
    },
    # ── N ──────────────────────────────────────────────────────
    "nzoth": {
        "id": "nzoth", "name": "N'Zoth", "armor": 12, "emoji": "🐙",
        "description": "Start the game with a 2/2 Fish that gains all your Deathrattles in combat.",
        "ability": {"type": "passive", "effect": "avatar_of_nzoth"},
    },
    "nozdormu": {
        "id": "nozdormu", "name": "Nozdormu", "armor": 13, "emoji": "⌚",
        "description": "Your first Refresh each turn costs (0).",
        "ability": {"type": "passive", "effect": "clairvoyance"},
    },
    # ── O ──────────────────────────────────────────────────────
    "onyxia": {
        "id": "onyxia", "name": "Onyxia", "armor": 10, "emoji": "🐉",
        "description": "Avenge (4): Summon a 1/1 Whelp that attacks immediately. Improve this by +1/+1.",
        "ability": {"type": "passive", "effect": "broodmother", "avenge_count": 4},
    },
    "overlord_saurfang": {
        "id": "overlord_saurfang", "name": "Overlord Saurfang", "armor": 18, "emoji": "🪓",
        "description": "Minions in the Tavern have +1/+1. Improves after you buy 4 minions.",
        "ability": {"type": "passive", "effect": "for_the_horde", "upgrade_threshold": 4},
    },
    "ozumat": {
        "id": "ozumat", "name": "Ozumat", "armor": 15, "emoji": "🐙",
        "description": "When you have space in combat, summon a 2/2 Tentacle with Taunt.",
        "ability": {"type": "passive", "effect": "tentacular"},
    },
    # ── P ──────────────────────────────────────────────────────
    "patches_the_pirate": {
        "id": "patches_the_pirate", "name": "Patches the Pirate", "armor": 18, "emoji": "🏴‍☠️",
        "description": "Get a Pirate. After you buy a Pirate, your next Hero Power costs (1) less.",
        "ability": {"type": "hero_power", "cost": 3, "effect": "pirate_parrrrty"},
    },
    "patchwerk": {
        "id": "patchwerk", "name": "Patchwerk", "armor": 0, "hp_override": 70, "emoji": "🪡",
        "description": "Start the game with 30 extra Health.",
        "ability": {"type": "passive", "effect": "all_patched_up", "bonus_hp": 30},
    },
    "professor_putricide": {
        "id": "professor_putricide", "name": "Professor Putricide", "armor": 12, "emoji": "🧪",
        "description": "Craft a custom Undead.",
        "ability": {"type": "hero_power", "cost": 3, "effect": "build_an_undead"},
    },
    "pyramad": {
        "id": "pyramad", "name": "Pyramad", "armor": 14, "emoji": "🏺",
        "description": "Steal a random minion from the Tavern. Double its Health.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "brick_by_brick"},
    },
    # ── Q ──────────────────────────────────────────────────────
    "queen_azshara": {
        "id": "queen_azshara", "name": "Queen Azshara", "armor": 12, "emoji": "🌊",
        "description": "When your warband reaches 30 total Attack, begin your Naga Conquest.",
        "ability": {"type": "passive", "effect": "azsharas_ambition", "threshold": 30},
    },
    "queen_wagtoggle": {
        "id": "queen_wagtoggle", "name": "Queen Wagtoggle", "armor": 14, "emoji": "🎀",
        "description": "Start of Combat: Give a friendly minion of each type +1/+1.",
        "ability": {"type": "passive", "effect": "wax_warband", "attack": 1, "health": 1},
    },
    # ── R ──────────────────────────────────────────────────────
    "ragnaros_the_firelord": {
        "id": "ragnaros_the_firelord", "name": "Ragnaros the Firelord", "armor": 18, "emoji": "🔥",
        "description": "After you buy 16 cards, get Sulfuras.",
        "ability": {"type": "passive", "effect": "buy_insect", "threshold": 16},
    },
    "rakanishu": {
        "id": "rakanishu", "name": "Rakanishu", "armor": 15, "emoji": "⚡",
        "description": "Your Tavern spells that give stats grant an extra +1/+1.",
        "ability": {"type": "passive", "effect": "tavern_lighting", "bonus_attack": 1, "bonus_health": 1},
    },
    "reno_jackson": {
        "id": "reno_jackson", "name": "Reno Jackson", "armor": 16, "emoji": "💰",
        "description": "Once per game, make a friendly minion Golden.",
        "ability": {"type": "passive", "effect": "gonna_be_rich", "uses": 1},
    },
    "rock_master_voone": {
        "id": "rock_master_voone", "name": "Rock Master Voone", "armor": 15, "emoji": "🎸",
        "description": "At the end of every 3 turns, get a plain copy of the left-most card in your hand.",
        "ability": {"type": "passive", "effect": "upbeat_harmony", "interval": 3},
    },
    "rokara": {
        "id": "rokara", "name": "Rokara", "armor": 18, "emoji": "⚔️",
        "description": "After a friendly minion kills an enemy, give it +1 Attack permanently.",
        "ability": {"type": "passive", "effect": "glory_of_combat", "attack": 1},
    },
    # ── S ──────────────────────────────────────────────────────
    "scabbs_cutterbutter": {
        "id": "scabbs_cutterbutter", "name": "Scabbs Cutterbutter", "armor": 15, "emoji": "🕵️",
        "description": "Discover a plain copy of a minion from your next opponent's warband.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "i_spy"},
    },
    "shudderwock": {
        "id": "shudderwock", "name": "Shudderwock", "armor": 10, "emoji": "👹",
        "description": "Trigger een Battlecry van een vriendelijke minion. (Beschikbaar vanaf beurt 3.)",
        "ability": {"type": "hero_power", "cost": 2, "effect": "snicker_snack", "unlock_turn": 3, "targeted": True},
    },
    "silas_darkmoon": {
        "id": "silas_darkmoon", "name": "Silas Darkmoon", "armor": 14, "emoji": "🎡",
        "description": "Darkmoon Tickets are in the Tavern! Get 3 to Discover a minion of your Tier.",
        "ability": {"type": "passive", "effect": "come_one_come_all", "ticket_threshold": 3},
    },
    "sindragosa": {
        "id": "sindragosa", "name": "Sindragosa", "armor": 7, "emoji": "❄️",
        "description": "Minions cost (2). The Tavern offers one fewer minion and Freezes at end of each turn.",
        "ability": {"type": "passive", "effect": "stay_frosty", "buy_cost": 2},
    },
    "sir_finley_mrrgglton": {
        "id": "sir_finley_mrrgglton", "name": "Sir Finley Mrrgglton", "armor": 14, "emoji": "🐟",
        "description": "At the start of the game, Discover a Hero Power.",
        "ability": {"type": "passive", "effect": "adventure_discover_hero_power"},
    },
    "sire_denathrius": {
        "id": "sire_denathrius", "name": "Sire Denathrius", "armor": 11, "emoji": "🧛",
        "description": "At the start of the game, choose one of two Quests.",
        "ability": {"type": "passive", "effect": "whodunit"},
    },
    "skycapn_kragg": {
        "id": "skycapn_kragg", "name": "Skycap'n Kragg", "armor": 14, "emoji": "🦜",
        "description": "Gain 2 Gold. Increases by 1 each turn. (Once per game.)",
        "ability": {"type": "passive", "effect": "piggy_bank", "uses": 1},
    },
    "snake_eyes": {
        "id": "snake_eyes", "name": "Snake Eyes", "armor": 5, "emoji": "🎲",
        "description": "Roll a 6-sided die. Gain that much Gold. (Cannot be used again for that many turns!)",
        "ability": {"type": "hero_power", "cost": 1, "effect": "lucky_roll"},
    },
    "sneed": {
        "id": "sneed", "name": "Sneed", "armor": 20, "emoji": "⚙️",
        "description": "Start the game with a 2/1 Shredder that summons a minion from your hand.",
        "ability": {"type": "passive", "effect": "pilot_the_shredder"},
    },
    "sylvanas_windrunner": {
        "id": "sylvanas_windrunner", "name": "Sylvanas Windrunner", "armor": 10, "emoji": "🏹",
        "description": "Discover a plain copy of a minion that died last combat. (Unlocks on Turn 3.)",
        "ability": {"type": "hero_power", "cost": 2, "effect": "reclaimed_souls", "unlock_turn": 3},
    },
    # ── T ──────────────────────────────────────────────────────
    "taetthelan_bloodwatcher": {
        "id": "taetthelan_bloodwatcher", "name": "Tae'thelan Bloodwatcher", "armor": 18, "emoji": "📜",
        "description": "Every fourth Tavern spell you buy costs (0).",
        "ability": {"type": "passive", "effect": "reliquary_research", "interval": 4},
    },
    "tamsin_roame": {
        "id": "tamsin_roame", "name": "Tamsin Roame", "armor": 10, "emoji": "💀",
        "description": "Start of Combat: Give your lowest-Attack minion Deathrattle: Give your other minions this minion's stats.",
        "ability": {"type": "passive", "effect": "fragrant_phylactery"},
    },
    "tavish_stormpike": {
        "id": "tavish_stormpike", "name": "Tavish Stormpike", "armor": 14, "emoji": "🎯",
        "description": "Remove a minion in the Tavern. When you have space next combat, fire it at a random enemy.",
        "ability": {"type": "passive", "effect": "lock_and_load"},
    },
    "teron_gorefiend": {
        "id": "teron_gorefiend", "name": "Teron Gorefiend", "armor": 14, "emoji": "💀",
        "description": "Choose a friendly minion. Destroy it. When you have space, resummon an exact copy.",
        "ability": {"type": "passive", "effect": "rapid_reanimation"},
    },
    "tess_greymane": {
        "id": "tess_greymane", "name": "Tess Greymane", "armor": 17, "emoji": "🕵️",
        "description": "Refresh the Tavern with plain copies of your last opponent's warband.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "bobs_burgles"},
    },
    "the_curator": {
        "id": "the_curator", "name": "The Curator", "armor": 16, "emoji": "🖼️",
        "description": "Start the game with a 2/2 Amalgam with Venomous and all minion types.",
        "ability": {"type": "passive", "effect": "menagerist"},
    },
    "the_great_akazamzarak": {
        "id": "the_great_akazamzarak", "name": "The Great Akazamzarak", "armor": 12, "emoji": "🎩",
        "description": "Choose a Secret. Put it into the battlefield.",
        "ability": {"type": "passive", "effect": "prestidigitation"},
    },
    "the_jailer": {
        "id": "the_jailer", "name": "The Jailer", "armor": 10, "emoji": "🔒",
        "description": "Destroy a friendly Undead to get a random Undead.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "rune_of_damnation"},
    },
    "the_lich_king": {
        "id": "the_lich_king", "name": "The Lich King", "armor": 14, "emoji": "💀",
        "description": "Give a minion Reborn until next turn.",
        "ability": {"type": "passive", "effect": "reborn_rites"},
    },
    "the_nameless_one": {
        "id": "the_nameless_one", "name": "The Nameless One", "armor": 12, "emoji": "❓",
        "description": "Copy your teammate's Hero Power.",
        "ability": {"type": "passive", "effect": "copy_teammate_hero_power"},
    },
    "the_rat_king": {
        "id": "the_rat_king", "name": "The Rat King", "armor": 12, "emoji": "👑",
        "description": "Discover a minion of a specific minion type. Swaps type each turn.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "tale_of_kings"},
    },
    "thorim_stormlord": {
        "id": "thorim_stormlord", "name": "Thorim, Stormlord", "armor": 18, "emoji": "⚡",
        "description": "At the start of the game, Discover a Tier 7 minion to get after you spend 65 Gold.",
        "ability": {"type": "passive", "effect": "choose_your_champion", "gold_threshold": 65},
    },
    "tickatus": {
        "id": "tickatus", "name": "Tickatus", "armor": 17, "emoji": "🎠",
        "description": "Every 4 turns, Discover a Darkmoon Prize.",
        "ability": {"type": "passive", "effect": "prize_wall", "interval": 4},
    },
    "time_twister_chromie": {
        "id": "time_twister_chromie", "name": "Time Twister Chromie", "armor": 12, "emoji": "⌚",
        "description": "Refresh the Tavern with Tavern spells.",
        "ability": {"type": "passive", "effect": "mana_per_minute"},
    },
    "trade_prince_gallywix": {
        "id": "trade_prince_gallywix", "name": "Trade Prince Gallywix", "armor": 5, "emoji": "💰",
        "description": "After you sell a minion, gain 1 Gold next turn.",
        "ability": {"type": "hero_power", "cost": 1, "effect": "smart_savings"},
    },
    # ── V ──────────────────────────────────────────────────────
    "vanndar_stormpike": {
        "id": "vanndar_stormpike", "name": "Vanndar Stormpike", "armor": 12, "emoji": "🛡️",
        "description": "When you have space in combat, summon a copy of your highest-Health minion.",
        "ability": {"type": "passive", "effect": "stormpike_strength"},
    },
    "varden_dawngrasp": {
        "id": "varden_dawngrasp", "name": "Varden Dawngrasp", "armor": 18, "emoji": "❄️",
        "description": "After the Tavern is Refreshed, copy its highest-Tier minion and Freeze them both.",
        "ability": {"type": "passive", "effect": "twice_as_nice"},
    },
    "voljin": {
        "id": "voljin", "name": "Vol'jin", "armor": 17, "emoji": "👻",
        "description": "Choose 2 minions. They gain each other's Attack until next turn.",
        "ability": {"type": "passive", "effect": "spirit_swap"},
    },
    # ── X ──────────────────────────────────────────────────────
    "xyrella": {
        "id": "xyrella", "name": "Xyrella", "armor": 12, "emoji": "💫",
        "description": "Choose a minion in the Tavern. Set its stats to 2 and add it to your hand.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "see_the_light"},
    },
    # ── Y ──────────────────────────────────────────────────────
    "yshaarj": {
        "id": "yshaarj", "name": "Y'Shaarj", "armor": 18, "emoji": "👁️",
        "description": "Start of Combat: Summon and get a minion of your Tier.",
        "ability": {"type": "hero_power", "cost": 2, "effect": "embrace_your_rage"},
    },
    "yogg_saron": {
        "id": "yogg_saron", "name": "Yogg-Saron, Hope's End", "armor": 10, "emoji": "🐙",
        "description": "At the start of your turn, cast a random Tavern spell. (Unlocks on Turn 3.)",
        "ability": {"type": "passive", "effect": "puzzle_box", "unlock_turn": 3},
    },
    "ysera": {
        "id": "ysera", "name": "Ysera", "armor": 17, "emoji": "🌙",
        "description": "The Tavern offers an extra Dragon whenever it is Refreshed.",
        "ability": {"type": "passive", "effect": "dream_portal"},
    },
    # ── Z ──────────────────────────────────────────────────────
    "zephrys_the_great": {
        "id": "zephrys_the_great", "name": "Zephrys, the Great", "armor": 17, "emoji": "✨",
        "description": "If you have two copies of a minion, find the third.",
        "ability": {"type": "hero_power", "cost": 3, "effect": "three_wishes"},
    },
    "zerek_master_cloner": {
        "id": "zerek_master_cloner", "name": "Zerek, Master Cloner", "armor": 18, "emoji": "🧬",
        "description": "Once per game, summon an exact copy of a friendly minion.",
        "ability": {"type": "passive", "effect": "cloning_gallery", "uses": 1},
    },
}

HEROES_LIST = list(HEROES.values())
