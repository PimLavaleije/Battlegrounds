import random
from game.minion import Minion
from game.data.heroes import HEROES_LIST
from game.data.spells import SPELLS_BY_TIER

_SPELLS_FLAT = {s["id"]: s for tier_spells in SPELLS_BY_TIER.values() for s in tier_spells}
_BOUNTY_SPELLS = [s for s in _SPELLS_FLAT.values() if "bounty" in s["id"]]


class Player:
    MAX_BOARD = 7
    MAX_GOLD = 10

    def __init__(self, sid: str, name: str, is_ai: bool = False):
        self.sid = sid
        self.name = name
        self.is_ai = is_ai
        self.hp = 40
        self.tavern_tier = 1
        self.upgrade_cost = 5
        self.gold = 0
        self.board: list[Minion] = []
        self.shop: list[Minion | None] = []
        self.frozen = False
        self.hero: dict | None = None
        self.hero_options: list[dict] = []
        self.ready = False
        self.alive = True
        self.triple_tracker: dict[str, list[Minion]] = {}
        self.double_battlecry = False  # Brann (legacy flag kept for hero compat)
        self.battlecry_triggers = 1   # 1=normal, 2=Brann, 3=golden Brann
        self.double_deathrattle = False  # Baron / Lich King
        self.hand: list[Minion] = []
        self.pending_combat_spells: list[str] = []
        self.gold_next_turn_bonus = 0
        self.free_refreshes_available = 0
        self.next_spell_discount = 0
        self.kael_buy_count = 0  # Kael'thas: resets each turn
        self.ancestral_automaton_count = 0  # AA buff tracking
        self.spell_attack_bonus = 0  # permanent bonus from chromadrakes, shoalfin_mystic on-sell, etc.
        self.spell_health_bonus = 0  # permanent bonus from chromadrakes, shoalfin_mystic on-sell, etc.
        self.last_spell_cast: dict | None = None  # voor cataclysmic_harbinger
        self.cards_played_this_turn = 0  # voor brazen_buccaneer
        self.blood_gem_attack_bonus = 0  # permanent van prickly_piper deathrattle
        self.blood_gem_health_bonus = 0  # permanent van moon_bacon_jazzer battlecry

    # ── Turn setup ──────────────────────────────────────────
    def start_turn(self, round_num: int):
        base_gold = min(3 + round_num - 1, self.MAX_GOLD)
        bonus = self.gold_next_turn_bonus
        self.gold_next_turn_bonus = 0
        self.gold = min(base_gold + bonus, self.MAX_GOLD)
        self.ready = False
        if self.upgrade_cost > 0:
            self.upgrade_cost = max(0, self.upgrade_cost - 1)
        # Reset turn tracking
        self.last_spell_cast = None
        self.cards_played_this_turn = 0
        self._apply_start_of_round_hero()
        self._apply_start_of_turn_board()
        for m in self.board:
            if hasattr(m, "_hired_ritualist_triggered"):
                m._hired_ritualist_triggered = False

    def _apply_start_of_round_hero(self):
        if not self.hero:
            return
        effect = self.hero.get("ability", {}).get("effect")
        if effect == "clairvoyance":           # Nozdormu: first refresh free
            self.free_refreshes_available += 1
        self.kael_buy_count = 0               # Kael'thas counter resets each turn

    # ── Hero ability ────────────────────────────────────────
    def use_hero_power(self, target_index: int | None = None) -> dict:
        if not self.hero:
            return {"success": False, "message": "Geen held geselecteerd."}
        ab = self.hero.get("ability", {})
        if ab.get("type") != "hero_power":
            return {"success": False, "message": "Geen actieve held-spreuk."}
        cost = ab.get("cost", 2)
        if self.gold < cost:
            return {"success": False, "message": f"Niet genoeg goud (kost {cost})."}

        effect = ab.get("effect")
        self.gold -= cost

        if effect == "give_divine_shield":
            # George the Fallen: give a target minion Divine Shield
            if self.board and target_index is not None and 0 <= target_index < len(self.board):
                m = self.board[target_index]
                m.divine_shield = True
                if "divine_shield" not in m.abilities:
                    m.abilities.append("divine_shield")
                return {"success": True, "effect": "divine_shield", "target": m.to_dict()}

        elif effect == "brick_by_brick":
            # Pyramad: give a random minion +4 Health
            if self.board:
                t = random.choice(self.board)
                t.health += 4; t.max_health += 4
                return {"success": True, "effect": "brick_by_brick", "target": t.to_dict()}

        elif effect == "graveyard_shift":
            # Lich Bazhial: take self_damage HP, gain that much gold
            dmg = ab.get("self_damage", 2)
            self.hp -= dmg
            self.gold = min(self.gold + dmg, self.MAX_GOLD)
            return {"success": True, "effect": "graveyard_shift", "hp": self.hp, "gold": self.gold}

        elif effect == "blessing_nine_frogs":
            # Doctor Holli'dae: get a random Tavern spell
            import random as _r
            stat_spells = [s for tier_spells in SPELLS_BY_TIER.values() for s in tier_spells
                           if s["tier"] <= self.tavern_tier]
            if stat_spells:
                chosen = _r.choice(stat_spells)
                spell = {**chosen, "type": "spell", "cost": chosen.get("cost", 3)}
                self.hand.append(spell)
                return {"success": True, "effect": "blessing_nine_frogs", "spell": spell}

        elif effect == "smart_savings":
            # Gallywix: next reroll is free
            self.free_refreshes_available += 1
            return {"success": True, "effect": "smart_savings"}

        elif effect == "lucky_roll":
            # Snake Eyes: add a random minion of current tier to hand
            from game.data.minions import MINIONS as _MINS
            tier_pool = [mid for mid, d in _MINS.items() if d["tier"] == self.tavern_tier]
            if tier_pool:
                self.hand.append(Minion.from_id(random.choice(tier_pool)))
            return {"success": True, "effect": "lucky_roll"}

        elif effect == "tale_of_kings":
            # The Rat King: give all friendly minions +2/+2
            for m in self.board:
                m.attack += 2; m.health += 2; m.max_health += 2
            return {"success": True, "effect": "tale_of_kings"}

        elif effect == "sharpen_blades":
            # Edwin VanCleef: give a minion +1 Attack for each card in hand
            if self.board and target_index is not None and 0 <= target_index < len(self.board):
                bonus = len(self.hand)
                m = self.board[target_index]
                m.attack += bonus
                return {"success": True, "effect": "sharpen_blades", "target": m.to_dict()}

        return {"success": True}

    # ── Shop acties ─────────────────────────────────────────
    def can_buy(self) -> bool:
        return self.gold >= 3

    def buy_minion(self, shop_index: int, target_index: int | None = None) -> dict:
        if shop_index < 0 or shop_index >= len(self.shop):
            return {"success": False, "message": "Ongeldige winkel-index."}
        item = self.shop[shop_index]
        if item is None:
            return {"success": False, "message": "Geen minion op die plek."}
        # Spell dict in shop — redirect to spell handler
        if isinstance(item, dict):
            return self._cast_spell_from_shop(shop_index, target_index)
        minion = item
        if not self.can_buy():
            return {"success": False, "message": "Niet genoeg goud."}

        self.shop[shop_index] = None
        self.gold -= 3
        self.hand.append(minion)

        # Triple check
        triple_result = self._track_triple(minion)

        # Battlecry fires in play_from_hand, not on buy

        # Shop-event passives (wrath_weaver, deflect_o_bot, blazing_skyfin, kalecgos)
        passive_events = self._trigger_buy_passives(minion)

        # Ancestral Automaton: buff all existing AAs, set bonus on new one
        if minion.id == "ancestral_automaton":
            for m in self.board:
                if m.id == "ancestral_automaton":
                    m.attack += 3; m.health += 2; m.max_health += 2
            for m in self.hand:
                if isinstance(m, Minion) and m.id == "ancestral_automaton":
                    m.attack += 3; m.health += 2; m.max_health += 2
            minion.attack += self.ancestral_automaton_count * 3
            minion.health += self.ancestral_automaton_count * 2
            minion.max_health += self.ancestral_automaton_count * 2
            self.ancestral_automaton_count += 1

        # Hero passives on buy
        if self.hero:
            hero_effect = self.hero.get("ability", {}).get("effect")
            if hero_effect == "im_the_capn_now" and "Pirate" in minion.types:
                self.gold = min(self.gold + 1, self.MAX_GOLD)
            elif hero_effect == "verdant_spheres":
                self.kael_buy_count += 1
                if self.kael_buy_count % self.hero["ability"].get("threshold", 3) == 0:
                    self.hand.append({**_SPELLS_FLAT["tavern_coin"], "type": "spell", "cost": 0})

        return {
            "success": True,
            "minion": minion.to_dict(),
            "triple": triple_result,
            "battlecry": None,
            "passive_events": passive_events,
        }

    def sell_minion(self, board_index: int) -> dict:
        if board_index < 0 or board_index >= len(self.board):
            return {"success": False, "message": "Ongeldige board-index."}
        minion = self.board.pop(board_index)
        self.gold = min(self.gold + self._sell_gold(minion), self.MAX_GOLD)
        self._remove_from_triple(minion)
        self._recalculate_board_passives()
        sell_passive = self._trigger_sell_passive(minion)
        return {"success": True, "gold": self.gold, "sold": minion.to_dict(), "sell_passive": sell_passive}

    def reroll(self) -> dict:
        if self.free_refreshes_available > 0:
            self.free_refreshes_available -= 1
            return {"success": True, "gold": self.gold}
        if self.gold < 1:
            return {"success": False, "message": "Niet genoeg goud."}
        self.gold -= 1
        return {"success": True, "gold": self.gold}

    def toggle_freeze(self) -> dict:
        self.frozen = not self.frozen
        return {"success": True, "frozen": self.frozen}

    def upgrade_tavern(self) -> dict:
        if self.tavern_tier >= 6:
            return {"success": False, "message": "Al op maximaal tavern niveau."}
        if self.gold < self.upgrade_cost:
            return {"success": False, "message": f"Niet genoeg goud (kost {self.upgrade_cost})."}
        self.gold -= self.upgrade_cost
        self.tavern_tier += 1
        # Nieuwe upgrade kost voor volgende tier
        tier_costs = {2: 5, 3: 7, 4: 8, 5: 9, 6: 10}
        next_tier = self.tavern_tier + 1
        self.upgrade_cost = max(0, tier_costs.get(next_tier, 10) - (self.tavern_tier - 1))
        # Forest Warden Omu: gain gold after leveling
        if self.hero and self.hero.get("ability", {}).get("effect") == "everbloom":
            gain = self.hero["ability"].get("gold_gain", 2)
            self.gold = min(self.gold + gain, self.MAX_GOLD)
        return {"success": True, "tavern_tier": self.tavern_tier, "gold": self.gold}

    def move_minion(self, from_idx: int, to_idx: int) -> dict:
        if not (0 <= from_idx < len(self.board) and 0 <= to_idx < len(self.board)):
            return {"success": False, "message": "Ongeldige positie."}
        self.board.insert(to_idx, self.board.pop(from_idx))
        return {"success": True}

    # ── Triples ─────────────────────────────────────────────
    def _track_triple(self, minion: Minion) -> dict | None:
        key = minion.id
        if key not in self.triple_tracker:
            self.triple_tracker[key] = []
        self.triple_tracker[key].append(minion)

        if len(self.triple_tracker[key]) >= 3:
            copies = self.triple_tracker[key][:3]
            self.triple_tracker[key] = self.triple_tracker[key][3:]
            # Verwijder de 3 kopieën van board én hand
            for c in copies:
                if c in self.board:
                    self.board.remove(c)
                elif c in self.hand:
                    self.hand.remove(c)
            # Golden versie: basis×2 + alle geaccumuleerde buffs van de 3 kopieën
            golden = Minion.from_id(minion.id)
            golden.make_golden()
            extra_atk = sum(c.attack - c.base_attack for c in copies)
            extra_hp  = sum(c.health - c.base_health for c in copies)
            golden.attack     += extra_atk
            golden.health     += extra_hp
            golden.max_health += extra_hp
            self.hand.append(golden)  # golden gaat naar hand
            discover_tier = min(self.tavern_tier + 1, 6)
            return {"triple": True, "golden": golden.to_dict(), "discover_tier": discover_tier}
        return None

    def add_discover_minion(self, minion_id: str) -> dict:
        minion = Minion.from_id(minion_id)
        self.hand.append(minion)
        return {"success": True}

    def _remove_from_triple(self, minion: Minion):
        key = minion.id
        if key in self.triple_tracker and minion in self.triple_tracker[key]:
            self.triple_tracker[key].remove(minion)

    # ── Hand acties ─────────────────────────────────────────────
    def play_from_hand(self, hand_index: int, board_index: int = -1) -> dict:
        if hand_index < 0 or hand_index >= len(self.hand):
            return {"success": False, "message": "Ongeldige hand-index."}
        item = self.hand[hand_index]
        # Spell stored in hand (given by battlecry/deathrattle)
        if isinstance(item, dict) and item.get("type") == "spell":
            self.hand.pop(hand_index)
            effect = self._apply_spell(item, board_index if board_index >= 0 else None)
            spell_passives = self._trigger_spell_cast_passives()
            return {"success": True, "spell": item, "spell_effect": effect, "spell_passives": spell_passives}
        # Blood Gem — doelgericht +1/+1 item
        if isinstance(item, dict) and item.get("type") == "blood_gem":
            if not self.board:
                return {"success": False, "message": "Geen minions om Blood Gem op te spelen."}
            self.hand.pop(hand_index)
            target = self.board[board_index] if 0 <= board_index < len(self.board) else self.board[0]
            self._apply_blood_gem(target, item.get("bonus_keyword"), item.get("bonus_tribe"))
            return {"success": True, "blood_gem": True, "target": target.to_dict()}
        if len(self.board) >= self.MAX_BOARD:
            return {"success": False, "message": "Board is vol (max 7). Verkoop een minion om ruimte te maken."}
        minion = self.hand.pop(hand_index)
        if 0 <= board_index < len(self.board):
            self.board.insert(board_index, minion)
        else:
            self.board.append(minion)
        self.cards_played_this_turn += 1
        self._recalculate_board_passives()

        battlecry_result = None
        if minion.battlecry:
            battlecry_result = self._apply_battlecry(minion)
            for _ in range(self.battlecry_triggers - 1):
                self._apply_battlecry(minion)

        # Spellcraft: Naga generates free spell when played to board
        if "spellcraft" in minion.abilities and minion.spellcraft:
            sc_spell = self._generate_spellcraft_spell(minion)
            if sc_spell:
                self.hand.append(sc_spell)

        play_passives = self._trigger_play_passives(minion, battlecry_fired=bool(battlecry_result))
        return {"success": True, "battlecry": battlecry_result, "play_passives": play_passives}

    # ── Spreuken ─────────────────────────────────────────────────
    def _cast_spell_from_shop(self, shop_index: int, target_index: int | None = None) -> dict:
        """Koop een spreuk uit de winkel: gaat naar hand (niet direct gecastet)."""
        spell = self.shop[shop_index]
        cost = max(0, spell.get("cost", 3) - self.next_spell_discount)
        self.next_spell_discount = 0
        if self.gold < cost:
            return {"success": False, "message": f"Niet genoeg goud (kost {cost})."}
        self.shop[shop_index] = None
        self.gold -= cost
        self.hand.append(spell)
        return {"success": True, "spell": spell}

    def _apply_spell(self, spell: dict, target_index: int | None = None) -> dict:
        import random as _r
        sid = spell["id"]
        # Track voor cataclysmic_harbinger
        self.last_spell_cast = spell
        # Snapshot board stats voor spell-bonus berekening (post-apply)
        _pre_stats = {id(m): (m.attack, m.health) for m in self.board}

        def _target() -> "Minion | None":
            if not self.board:
                return None
            if target_index is not None and 0 <= target_index < len(self.board):
                return self.board[target_index]
            return self.board[0]

        def _give_taunt(m: "Minion"):
            m.taunt = True
            if "taunt" not in m.abilities:
                m.abilities.append("taunt")

        def _make_golden(m: "Minion"):
            if not m.golden:
                m.golden = True
                m.attack *= 2
                m.health *= 2
                m.max_health *= 2

        # ── Gold generation ─────────────────────────────────
        if sid == "tavern_coin":
            self.gold = min(self.gold + 1, self.MAX_GOLD)
        elif sid == "wealthy_bounty":
            self.gold = min(self.gold + 2, self.MAX_GOLD)

        # ── All-board buffs ─────────────────────────────────
        elif sid == "shiny_ring":
            for m in self.board:
                m.attack += 1; m.health += 1; m.max_health += 1
        elif sid == "azerite_empowerment":
            for _ in range(2):
                for m in self.board:
                    m.attack += 2; m.health += 2; m.max_health += 2
        elif sid == "conflagration":
            for m in self.board:
                m.attack += 2; m.health += 2; m.max_health += 2
        elif sid == "arcane_absorption":
            for m in self.board:
                m.attack += 1; m.health += 1; m.max_health += 1
        elif sid == "natural_blessing":
            for m in self.board:
                m.attack += 2; m.health += 3; m.max_health += 3
        elif sid == "eonars_favor":
            for m in self.board:
                m.attack += 1; m.health += 2; m.max_health += 2
        elif sid in ("easterly_winds", "fleeting_vigor", "robust_evolution"):
            for m in self.board:
                m.attack += 1
        elif sid == "mounting_avalanche":
            for m in self.board:
                m.attack += 2; m.health += 1; m.max_health += 1
        elif sid == "upper_hand":
            for m in self.board:
                m.attack += 2
        elif sid == "lost_staff_of_hamuul":
            for m in self.board:
                m.attack += 3; m.health += 3; m.max_health += 3
        elif sid == "eyes_of_the_earth_mother":
            for m in self.board:
                m.attack += 5; m.health += 5; m.max_health += 5
        elif sid == "channel_the_devourer":
            for m in self.board:
                m.attack += 4; m.health += 4; m.max_health += 4
        elif sid == "butchering":
            for m in self.board:
                m.attack += 5
        elif sid == "sanctify":
            for m in self.board:
                if m.divine_shield:
                    m.attack += 7
        elif sid == "queens_command":
            for m in self.board:
                m.attack += 3; m.health += 3; m.max_health += 3
                if "Naga" in m.types:
                    m.attack += 3; m.health += 3; m.max_health += 3
        elif sid == "wave_of_gold":
            for m in self.board:
                m.attack += 3; m.health += 2; m.max_health += 2
                if m.golden:
                    m.attack += 3; m.health += 2; m.max_health += 2
        elif sid == "misplaced_tea_set":
            seen = set()
            for m in self.board:
                tribe = m.types[0] if m.types else None
                if tribe and tribe not in seen:
                    seen.add(tribe)
                    m.attack += 2; m.health += 2; m.max_health += 2
        elif sid == "gem_confiscation":
            for m in self.board:
                m.divine_shield = True
                if "divine_shield" not in m.abilities:
                    m.abilities.append("divine_shield")
        elif sid == "unmasked_identity":
            tribes = {t for m in self.board for t in m.types}
            bonus = len(tribes)
            for m in self.board:
                m.attack += bonus

        # ── Tribe-specific buffs ────────────────────────────
        elif sid == "spitescale_special":
            for m in self.board:
                if "Murloc" in m.types:
                    m.attack += 3; m.health += 3; m.max_health += 3
        elif sid == "tomb_turning":
            for m in self.board:
                if m.deathrattle:
                    m.attack += 3; m.health += 3; m.max_health += 3

        # ── Random-target buffs ─────────────────────────────
        elif sid == "might_of_stormwind":
            for t in _r.sample(self.board, min(4, len(self.board))):
                t.attack += 1; t.health += 2; t.max_health += 2
        elif sid == "healthy_bounty":
            for t in _r.sample(self.board, min(3, len(self.board))):
                t.health += 4; t.max_health += 4
        elif sid == "hostile_bounty":
            for t in _r.sample(self.board, min(3, len(self.board))):
                t.attack += 4
        elif sid == "friendly_bounty":
            for t in _r.sample(self.board, min(3, len(self.board))):
                t.attack += 1; t.health += 1; t.max_health += 1
        elif sid == "back_to_back":
            for t in _r.sample(self.board, min(2, len(self.board))):
                t.attack += 3; t.health += 3; t.max_health += 3
        elif sid == "bargain_bundle":
            for t in _r.sample(self.board, min(3, len(self.board))):
                t.attack += 3; t.health += 3; t.max_health += 3
        elif sid == "overconfidence":
            if self.board:
                t = _r.choice(self.board)
                t.attack += 3; t.health += 3; t.max_health += 3

        # ── Single-target buffs (use _target()) ────────────
        elif sid == "pointy_arrow":
            t = _target()
            if t:
                t.attack += 4
        elif sid == "tavern_dish_banana":
            t = _target()
            if t:
                t.attack += 2; t.health += 2; t.max_health += 2
        elif sid == "a_new_sprout":
            t = _target()
            if t:
                t.attack += 1; t.health += 1; t.max_health += 1
        elif sid == "selfish_bounty":
            t = _target()
            if t:
                t.attack += 6; t.health += 6; t.max_health += 6
        elif sid == "temperature_shift":
            t = _target()
            if t:
                t.attack += 4; t.health += 4; t.max_health += 4
        elif sid == "fortify":
            t = _target()
            if t:
                t.health += 3; t.max_health += 3; _give_taunt(t)
        elif sid == "defenders_rites":
            t = _target()
            if t:
                t.attack += 6; t.health += 6; t.max_health += 6; _give_taunt(t)
        elif sid == "tricky_trousers":
            t = _target()
            if t:
                t.attack += 1; t.health += 2; t.max_health += 2
                t.taunt = not t.taunt
                if t.taunt and "taunt" not in t.abilities:
                    t.abilities.append("taunt")
                elif not t.taunt and "taunt" in t.abilities:
                    t.abilities.remove("taunt")
        elif sid == "deepwater_clan":
            t = _target()
            if t:
                t.attack += 2; t.health += 2; t.max_health += 2
            for m in self.board:
                if "Murloc" in m.types:
                    m.attack += 2; m.health += 2; m.max_health += 2
        elif sid == "brood_of_nozdormu":
            t = _target()
            if t:
                t.attack *= 2
        elif sid == "perfect_vision":
            t = _target()
            if t:
                t.attack = 20; t.health = 20; t.max_health = 20
        elif sid == "knockoff_wisdomball":
            t = _target()
            if t:
                t.attack += 5; t.health += 5; t.max_health += 5

        # ── Board manipulation ──────────────────────────────
        elif sid == "shifting_tide":
            _r.shuffle(self.board)
        elif sid == "boon_of_beetles":
            for _ in range(2):
                if len(self.board) < self.MAX_BOARD:
                    self.board.append(Minion.from_id("beetle"))

        # ── Add minions to hand ─────────────────────────────
        elif sid == "portal_in_a_fountain":
            from game.data.minions import MINIONS
            t5 = [mid for mid, d in MINIONS.items() if d["tier"] == 5]
            if t5:
                self.hand.append(Minion.from_id(_r.choice(t5)))
        elif sid == "portal_in_a_crystal":
            from game.data.minions import MINIONS
            pool = list(MINIONS.keys())
            for mid in _r.sample(pool, min(3, len(pool))):
                self.hand.append(Minion.from_id(mid))

        # ── Board copy / golden ─────────────────────────────
        elif sid == "cloning_conch":
            t = _target()
            if t and len(self.board) < self.MAX_BOARD:
                self.board.append(t.clone())
        elif sid == "golden_touch":
            t = _target()
            if t:
                _make_golden(t)

        # ── Pending combat effects (applied at combat start) ─
        elif sid == "corrupted_cupcakes":
            self.pending_combat_spells.append("corrupted_cupcakes")
        elif sid == "hired_headhunter":
            self.pending_combat_spells.append("hired_headhunter")

        # ── Spellcraft spells ────────────────────────────────
        elif sid == "sc_surf_n_surf":
            t = _target()
            if t:
                t.deathrattle = {"type": "summon", "token": "crab"}
                if "deathrattle" not in t.abilities:
                    t.abilities.append("deathrattle")
        elif sid == "sc_lava_lurker":
            t = _target()
            if t:
                t.attack += 2; t.health += 2; t.max_health += 2
        elif sid == "sc_reef_riffer":
            t = _target()
            if t:
                bonus = self.tavern_tier
                t.attack += bonus; t.health += bonus; t.max_health += bonus
        elif sid == "sc_deep_blue_crooner":
            t = _target()
            if t:
                t.attack += 2; t.health += 3; t.max_health += 3
        elif sid == "sc_deep_sea_angler":
            t = _target()
            if t:
                t.attack += 2; t.health += 6; t.max_health += 6; _give_taunt(t)
        elif sid == "sc_private_chef":
            t = _target()
            if t and t.types:
                from game.data.minions import MINIONS as _MINS
                tribe = t.types[0]
                candidates = [mid for mid, d in _MINS.items()
                              if tribe in d.get("types", []) and mid != t.id]
                if candidates:
                    self.hand.append(Minion.from_id(_r.choice(candidates)))
        elif sid == "sc_rimescale_priestess":
            from game.data.spells import SPELLS_BY_TIER as _SBT
            stat_spells = [s for tier_spells in _SBT.values() for s in tier_spells
                           if s["tier"] <= self.tavern_tier and "+" in s.get("description", "")]
            if stat_spells:
                chosen = _r.choice(stat_spells)
                self.hand.append({**chosen, "type": "spell", "cost": chosen.get("cost", 3)})
        elif sid == "sc_waverider":
            t = _target()
            if t:
                t.attack += 2; t.health += 2; t.max_health += 2
                if "Naga" in t.types and not t.windfury:
                    t.windfury = True
                    if "windfury" not in t.abilities:
                        t.abilities.append("windfury")
        elif sid == "sc_zesty_shaker":
            if self.board:
                t = _r.choice(self.board)
                t.attack += 2; t.health += 2; t.max_health += 2
        elif sid == "sc_darkcrest_strategist":
            from game.data.minions import MINIONS as _MINS2
            t1_nagas = [mid for mid, d in _MINS2.items()
                        if d["tier"] == 1 and "Naga" in d.get("types", [])]
            if t1_nagas:
                self.hand.append(Minion.from_id(_r.choice(t1_nagas)))
        elif sid == "sc_glowscale":
            t = _target()
            if t:
                t.divine_shield = True
                if "divine_shield" not in t.abilities:
                    t.abilities.append("divine_shield")
        elif sid == "sc_tranquil_meditative":
            for m in self.board:
                m.health += 2; m.max_health += 2
        elif sid == "sc_well_wisher":
            if self.board:
                t = _r.choice(self.board)
                t.attack += 3; t.health += 3; t.max_health += 3

        # Pas spell stat bonus toe op minions die gebuffed werden door de spreuk
        _ab, _hb = self._get_spell_stat_bonus()
        if _ab or _hb:
            for m in self.board:
                pre = _pre_stats.get(id(m))
                if pre is None:
                    continue
                if m.attack > pre[0]:
                    m.attack += _ab
                if m.health > pre[1]:
                    m.health += _hb
                    m.max_health += _hb

        return {"spell": sid}

    def _generate_spellcraft_spell(self, minion: "Minion") -> dict | None:
        sc = minion.spellcraft
        if not sc:
            return None
        return {
            "type": "spell",
            "id": sc["spell_id"],
            "name": f"Spellcraft: {sc['name']}",
            "tier": minion.tier,
            "cost": 0,
            "description": sc["description"],
            "targeted": sc.get("targeted", False),
        }

    def sell_from_hand(self, hand_index: int) -> dict:
        if hand_index < 0 or hand_index >= len(self.hand):
            return {"success": False, "message": "Ongeldige hand-index."}
        item = self.hand[hand_index]
        if isinstance(item, dict):
            return {"success": False, "message": "Spreuken kunnen niet verkocht worden."}
        minion = self.hand.pop(hand_index)
        self.gold = min(self.gold + self._sell_gold(minion), self.MAX_GOLD)
        self._remove_from_triple(minion)
        sell_passive = self._trigger_sell_passive(minion)
        return {"success": True, "gold": self.gold, "sold": minion.to_dict(), "sell_passive": sell_passive}

    # ── Battlecry logica ────────────────────────────────────
    def _apply_battlecry(self, minion: Minion) -> dict | None:
        bc = minion.battlecry
        if not bc:
            return None
        effect = bc.get("type")

        if effect == "summon" and len(self.board) < self.MAX_BOARD:
            token = Minion.from_id(bc["token"])
            self.board.append(token)
            return {"summoned": token.to_dict()}

        if effect == "buff_tribe":
            tribe = bc.get("tribe")
            targets = [m for m in self.board if tribe in m.types and m is not minion]
            if bc.get("include_hand"):
                targets += [m for m in self.hand if isinstance(m, Minion) and tribe in m.types and m is not minion]
            if bc.get("all"):
                for target in targets:
                    target.attack += bc.get("attack", 0)
                    target.health += bc.get("health", 0)
                    target.max_health += bc.get("health", 0)
                    if bc.get("add_taunt"):
                        target.taunt = True
                return {"buffed_all": [t.to_dict() for t in targets]} if targets else None
            elif targets:
                target = random.choice(targets)
                target.attack += bc.get("attack", 0)
                target.health += bc.get("health", 0)
                target.max_health += bc.get("health", 0)
                if bc.get("add_taunt"):
                    target.taunt = True
                return {"buffed": target.to_dict()}

        if effect == "make_self_golden":
            if not minion.golden:
                minion.make_golden()
            return {"golden": minion.to_dict()}

        if effect == "next_spell_discount":
            self.next_spell_discount += bc.get("amount", 1)
            return {"spell_discount": bc.get("amount", 1)}

        if effect == "gold_next_turn":
            self.gold_next_turn_bonus += bc.get("amount", 1)
            return {"gold_next_turn": bc.get("amount", 1)}

        if effect == "give_free_refreshes":
            self.free_refreshes_available += bc.get("count", 2)
            return {"free_refreshes": bc.get("count", 2)}

        if effect == "add_spell_to_hand":
            spell_id = bc.get("spell")
            spell = _SPELLS_FLAT.get(spell_id)
            if spell:
                self.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 3)})
                return {"spell_added": spell_id}

        if effect == "add_random_spell_to_hand":
            tier = bc.get("spell_tier", 1)
            pool = SPELLS_BY_TIER.get(tier, [])
            if pool:
                spell = random.choice(pool)
                self.hand.append({**spell, "type": "spell", "cost": spell.get("cost", tier)})
                return {"spell_added": spell["id"]}

        if effect == "add_random_minion_tribe_to_hand":
            from game.data.minions import MINIONS
            tribe = bc.get("tribe")
            pool = [m for m in MINIONS.values() if tribe in m.get("types", [])]
            if pool:
                data = random.choice(pool)
                self.hand.append(Minion.from_id(data["id"]))
                return {"minion_added": data["id"]}

        if effect == "add_random_chromadrake_to_hand":
            from game.data.minions import MINIONS
            pool = [m for mid, m in MINIONS.items() if "chromadrake" in mid]
            if pool:
                data = random.choice(pool)
                self.hand.append(Minion.from_id(data["id"]))
                return {"minion_added": data["id"]}

        if effect == "add_random_bounty_to_hand":
            if _BOUNTY_SPELLS:
                spell = random.choice(_BOUNTY_SPELLS)
                self.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 2)})
                return {"spell_added": spell["id"]}

        if effect == "cast_queens_command":
            multiplier = 2 if minion.golden else 1
            for m in self.board:
                atk = 3 * multiplier
                hp = 3 * multiplier
                if "Naga" in m.types:
                    atk *= 2
                    hp *= 2
                m.attack += atk
                m.health += hp
                m.max_health += hp
            return {"queens_command": True}

        if effect == "consume_tavern_minion":
            candidates = [(i, m) for i, m in enumerate(self.shop)
                          if m is not None and isinstance(m, Minion)]
            if candidates:
                idx, consumed = random.choice(candidates)
                self.shop[idx] = None
                multiplier = 2 if minion.golden else 1
                minion.attack += consumed.attack * multiplier
                minion.health += consumed.health * multiplier
                minion.max_health += consumed.health * multiplier
                return {"consumed": consumed.to_dict(), "gained_attack": consumed.attack * multiplier, "gained_health": consumed.health * multiplier}

        if effect == "spell_attack_bonus":
            self.spell_attack_bonus += bc.get("amount", 1) * (2 if minion.golden else 1)
            return {"spell_attack_bonus": bc.get("amount", 1)}

        if effect == "spell_health_bonus":
            self.spell_health_bonus += bc.get("amount", 1) * (2 if minion.golden else 1)
            return {"spell_health_bonus": bc.get("amount", 1)}

        if effect == "buff_tavern":
            tribe = bc.get("tribe")
            mult = 2 if minion.golden else 1
            for m in self.shop:
                if m is None or isinstance(m, dict):
                    continue
                if tribe is None or tribe in m.types:
                    m.attack += bc.get("attack", 0) * mult
                    m.health += bc.get("health", 0) * mult
                    m.max_health += bc.get("health", 0) * mult
            return {"buff_tavern": True}

        if effect == "buff_tavern_low":
            max_tier = bc.get("max_tier", 6)
            mult = 2 if minion.golden else 1
            for m in self.shop:
                if m is None or isinstance(m, dict):
                    continue
                if m.tier <= max_tier:
                    m.attack += bc.get("attack", 0) * mult
                    m.health += bc.get("health", 0) * mult
                    m.max_health += bc.get("health", 0) * mult
            return {"buff_tavern": True}

        if effect == "give_blood_gems":
            count = bc.get("count", 1) * (2 if minion.golden else 1)
            kw = bc.get("bonus_keyword")
            tribe = bc.get("bonus_tribe")
            for _ in range(count):
                self.hand.append(self._create_blood_gem(kw, tribe))
            return {"blood_gems": count}

        if effect == "blood_gem_health_bonus":
            self.blood_gem_health_bonus += bc.get("amount", 1) * (2 if minion.golden else 1)
            return {"blood_gem_health_bonus": bc.get("amount", 1)}

        return None

    def _trigger_buy_passives(self, bought: Minion) -> list[dict]:
        events = []
        for m in self.board:
            if not m.passive:
                continue
            ptype = m.passive.get("type")

            if ptype == "on_buy_count_buff":
                counter = getattr(m, "_buy_counter", 0) + 1
                m._buy_counter = counter
                threshold = m.passive.get("buy_count", 4)
                if counter >= threshold:
                    m._buy_counter = 0
                    mult = 2 if m.golden else 1
                    m.attack += m.passive.get("attack", 4) * mult
                    m.health += m.passive.get("health", 4) * mult
                    m.max_health += m.passive.get("health", 4) * mult
                    events.append({"type": "buy_passive", "uid": m.uid, "attack": m.attack, "health": m.health})

        return events

    def _trigger_play_passives(self, played: Minion, battlecry_fired: bool = False) -> list[dict]:
        """Fires passives that trigger when a minion is played from hand to board."""
        events = []
        for m in self.board:
            if not m.passive or m is played:
                continue
            ptype = m.passive.get("type")

            if ptype == "on_demon_bought" and "Demon" in played.types:
                m.attack += m.passive.get("attack", 2)
                m.health += m.passive.get("health", 1)
                m.max_health += m.passive.get("health", 1)
                dmg = m.passive.get("self_damage", 1)
                self.hp = max(0, self.hp - dmg)
                if self.hp == 0:
                    self.alive = False
                events.append({"type": "play_passive", "uid": m.uid, "attack": m.attack, "health": m.health, "self_damage": dmg})

            elif ptype == "on_battlecry_self" and battlecry_fired:
                m.attack += m.passive.get("attack", 1)
                m.health += m.passive.get("health", 1)
                m.max_health += m.passive.get("health", 1)
                events.append({"type": "play_passive", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "on_battlecry_tribe" and battlecry_fired:
                tribe = m.passive.get("tribe")
                for ally in self.board:
                    if tribe in ally.types:
                        ally.attack += m.passive.get("attack", 1)
                        ally.health += m.passive.get("health", 1)
                        ally.max_health += m.passive.get("health", 1)
                        events.append({"type": "play_passive", "uid": ally.uid, "attack": ally.attack, "health": ally.health})

            elif ptype == "on_quilboar_played" and "Quilboar" in played.types:
                count = m.passive.get("count", 1) * (2 if m.golden else 1)
                for _ in range(count):
                    self.hand.append(self._create_blood_gem())
                events.append({"type": "play_passive", "uid": m.uid, "blood_gems": count})

        return events

    def _sell_gold(self, minion: Minion) -> int:
        if minion.passive and minion.passive.get("type") == "on_sell_gold":
            total = minion.passive.get("total", 1)
            return total * 2 if minion.golden else total
        return 1

    def _trigger_sell_passive(self, sold: Minion) -> dict | None:
        if not sold.passive:
            return None
        ptype = sold.passive.get("type")
        multiplier = 2 if sold.golden else 1

        if ptype == "on_sell_self":
            token_id = sold.passive.get("token")
            if not token_id:
                return None
            results = []
            for _ in range(multiplier):
                token = Minion.from_id(token_id)
                self.hand.append(token)
                results.append(token.to_dict())
            return {"added_to_hand": results}

        if ptype == "on_sell_give_random_tier":
            from game.data.minions import MINIONS
            tier = sold.passive.get("tier", 1)
            pool = [m for m in MINIONS.values() if m["tier"] == tier]
            if not pool:
                return None
            results = []
            for _ in range(multiplier):
                data = random.choice(pool)
                minion = Minion.from_id(data["id"])
                self.hand.append(minion)
                results.append(minion.to_dict())
            return {"added_to_hand": results}

        if ptype == "on_sell_give_random_tribe":
            from game.data.minions import MINIONS
            tribe = sold.passive.get("tribe")
            pool = [m for m in MINIONS.values() if m.get("tribe") == tribe]
            if not pool:
                return None
            results = []
            for _ in range(multiplier):
                data = random.choice(pool)
                minion = Minion.from_id(data["id"])
                self.hand.append(minion)
                results.append(minion.to_dict())
            return {"added_to_hand": results}

        if ptype == "on_sell_buff_board":
            atk = sold.passive.get("attack", 0) * multiplier
            hp  = sold.passive.get("health", 0) * multiplier
            for m in self.board:
                m.attack      += atk
                m.health      += hp
                m.max_health  += hp
            return {"buffed_board": {"attack": atk, "health": hp}}

        if ptype == "on_sell_spell_stat_bonus":
            self.spell_attack_bonus += sold.passive.get("attack", 1) * multiplier
            self.spell_health_bonus += sold.passive.get("health", 1) * multiplier
            return {"spell_stat_bonus": True}

        if ptype == "on_sell_give_blood_gems":
            count = sold.passive.get("count", 2) * multiplier
            for _ in range(count):
                self.hand.append(self._create_blood_gem())
            return {"blood_gems": count}

        return None

    def _recalculate_board_passives(self):
        """Herbereken board-brede passieve effecten (bijv. Brann op board = double battlecry)."""
        self.double_battlecry = (
            any(m.id == "brann_bronzebeard" for m in self.board)
            or self.hero is not None and self.hero.get("ability", {}).get("effect") == "double_battlecry"
        )

    def _apply_start_of_turn_board(self):
        """Start-of-turn effecten van minions op het board (Accord-o-Tron, Plunder Pal, etc.)."""
        for m in self.board:
            sot = m.start_of_turn
            if not sot:
                continue
            mult = 2 if m.golden else 1
            stype = sot.get("type")
            if stype == "sot_gain_gold":
                amount = sot.get("amount", 1) * mult
                self.gold = min(self.gold + amount, self.MAX_GOLD)

    def trigger_end_of_turn(self) -> list[dict]:
        """Triggert alle end-of-turn effecten van minions op het board."""
        events = []
        for m in list(self.board):
            eot = m.end_of_turn
            if not eot:
                continue
            mult = 2 if m.golden else 1
            etype = eot.get("type")

            if etype == "eot_buff_adjacent_goldens":
                idx = self.board.index(m) if m in self.board else -1
                if idx < 0:
                    continue
                atk = eot.get("attack", 1) * mult
                golden_count = sum(1 for a in self.board if a.golden)
                repeats = 1 + golden_count
                for _ in range(repeats):
                    for adj_idx in [idx - 1, idx + 1]:
                        if 0 <= adj_idx < len(self.board):
                            self.board[adj_idx].attack += atk
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_buff_all":
                atk = eot.get("attack", 0) * mult
                hp = eot.get("health", 0) * mult
                for ally in self.board:
                    if ally is not m:
                        ally.attack += atk
                        ally.health += hp
                        ally.max_health += hp
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_get_random_spell":
                count = eot.get("count", 1) * mult
                pool = [s for tier_spells in SPELLS_BY_TIER.values() for s in tier_spells
                        if s.get("tier", 99) <= self.tavern_tier]
                for _ in range(count):
                    if pool:
                        spell = random.choice(pool)
                        self.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 3)})
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_get_random_bounty":
                count = eot.get("count", 1) * mult
                for _ in range(count):
                    if _BOUNTY_SPELLS:
                        spell = random.choice(_BOUNTY_SPELLS)
                        self.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 2)})
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_consume_highest_hp_tavern":
                shop_minions = [(i, sm) for i, sm in enumerate(self.shop)
                                if sm is not None and isinstance(sm, Minion)]
                if shop_minions:
                    shop_minions.sort(key=lambda x: x[1].health, reverse=True)
                    idx2, consumed = shop_minions[0]
                    self.shop[idx2] = None
                    m.attack += consumed.attack * mult
                    m.health += consumed.health * mult
                    m.max_health += consumed.health * mult
                    events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_get_mrrglton":
                if m.golden:
                    self.hand.append(Minion.from_id("mama_mrrglton"))
                    self.hand.append(Minion.from_id("papa_mrrglton"))
                else:
                    self.hand.append(Minion.from_id(random.choice(["mama_mrrglton", "papa_mrrglton"])))
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_last_spell_copy":
                if self.last_spell_cast:
                    count = eot.get("count", 1) * mult
                    for _ in range(count):
                        self.hand.append({**self.last_spell_cast, "type": "spell"})
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_buff_leftmost_tribe_plays":
                tribe = eot.get("tribe")
                atk = eot.get("attack", 0) * mult
                hp = eot.get("health", 0) * mult
                leftmost = next((a for a in self.board if tribe is None or tribe in a.types), None)
                if leftmost:
                    repeats = 1 + self.cards_played_this_turn
                    for _ in range(repeats):
                        leftmost.attack += atk
                        leftmost.health += hp
                        leftmost.max_health += hp
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_get_random_tier_tribe_every_n":
                tribe = eot.get("tribe")
                every = eot.get("every", 3)
                m._eot_counter = getattr(m, "_eot_counter", 0) + 1
                if m._eot_counter >= every:
                    m._eot_counter = 0
                    from game.data.minions import MINIONS as _MINS
                    pool = [mid for mid, d in _MINS.items()
                            if (tribe is None or tribe in d.get("types", []))
                            and d["tier"] <= self.tavern_tier]
                    for _ in range(mult):
                        if pool:
                            self.hand.append(Minion.from_id(random.choice(pool)))
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_spell_stat_bonus":
                self.spell_attack_bonus += eot.get("attack", 0) * mult
                self.spell_health_bonus += eot.get("health", 0) * mult
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_get_random_tier1":
                from game.data.minions import MINIONS as _MINS
                pool = [mid for mid, d in _MINS.items() if d["tier"] == 1]
                for _ in range(mult):
                    if pool:
                        self.hand.append(Minion.from_id(random.choice(pool)))
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_give_blood_gems":
                count = eot.get("count", 1) * mult
                kw = eot.get("bonus_keyword")
                tribe = eot.get("bonus_tribe")
                for _ in range(count):
                    self.hand.append(self._create_blood_gem(kw, tribe))
                events.append({"type": "eot", "uid": m.uid})

        return events

    def _get_spell_stat_bonus(self) -> tuple[int, int]:
        """Berekent totale spell stat bonus: permanent (chromadrakes) + on-board (enchanted_sentinel, humongozz)."""
        ab = self.spell_attack_bonus
        hb = self.spell_health_bonus
        for m in self.board:
            if m.passive and m.passive.get("type") == "spell_stat_bonus":
                mult = 2 if m.golden else 1
                ab += m.passive.get("attack", 0) * mult
                hb += m.passive.get("health", 0) * mult
        return ab, hb

    def _trigger_spell_cast_passives(self) -> list[dict]:
        """Triggert passives die afvuren als een tavern spreuk gecast wordt."""
        events = []
        for m in self.board:
            if not m.passive:
                continue
            ptype = m.passive.get("type")
            mult = 2 if m.golden else 1

            if ptype == "on_spell_cast_buff_all":
                atk = m.passive.get("attack", 1) * mult
                for ally in self.board:
                    ally.attack += atk
                events.append({"type": "spell_cast_passive", "uid": m.uid})

            elif ptype == "on_spell_cast_buff_divine_shield":
                atk = m.passive.get("attack", 3) * mult
                for ally in self.board:
                    if ally.divine_shield:
                        ally.attack += atk
                events.append({"type": "spell_cast_passive", "uid": m.uid})

            elif ptype == "on_spell_cast_buff_tribe_one":
                atk = m.passive.get("attack", 3) * mult
                hp = m.passive.get("health", 2) * mult
                seen_tribes: set = set()
                for ally in self.board:
                    for tribe in ally.types:
                        if tribe not in seen_tribes:
                            seen_tribes.add(tribe)
                            ally.attack += atk
                            ally.health += hp
                            ally.max_health += hp
                            break
                events.append({"type": "spell_cast_passive", "uid": m.uid})

            elif ptype == "on_spell_cast_buff_tribe_permanent":
                tribe = m.passive.get("tribe")
                atk = m.passive.get("attack", 1) * mult
                for ally in self.board:
                    if tribe is None or tribe in ally.types:
                        ally.attack += atk
                for item in self.hand:
                    if isinstance(item, Minion) and (tribe is None or tribe in item.types):
                        item.attack += atk
                events.append({"type": "spell_cast_passive", "uid": m.uid})

            elif ptype == "on_spell_cast_buff_tribe_random":
                tribe = m.passive.get("tribe")
                count = m.passive.get("count", 4)
                atk = m.passive.get("attack", 1) * mult
                hp = m.passive.get("health", 0) * mult
                eligible = [a for a in self.board if tribe is None or tribe in a.types]
                chosen = random.sample(eligible, min(count, len(eligible)))
                for a in chosen:
                    a.attack += atk
                    if hp:
                        a.health += hp
                        a.max_health += hp
                events.append({"type": "spell_cast_passive", "uid": m.uid})

            elif ptype == "on_spell_cast_buff_tavern_tribe":
                tribe = m.passive.get("tribe")
                atk = m.passive.get("attack", 1) * mult
                hp = m.passive.get("health", 1) * mult
                for shop_m in self.shop:
                    if shop_m is None or isinstance(shop_m, dict):
                        continue
                    if tribe is None or tribe in shop_m.types:
                        shop_m.attack += atk
                        shop_m.health += hp
                        shop_m.max_health += hp
                events.append({"type": "spell_cast_passive", "uid": m.uid})

        return events

    def _create_blood_gem(self, bonus_keyword: str | None = None, bonus_tribe: str | None = None) -> dict:
        bg: dict = {"type": "blood_gem", "id": "blood_gem", "name": "Blood Gem",
                    "cost": 0, "description": "Geef een minion +1/+1."}
        if bonus_keyword:
            bg["bonus_keyword"] = bonus_keyword
        if bonus_tribe:
            bg["bonus_tribe"] = bonus_tribe
        return bg

    def _apply_blood_gem(self, target: Minion, bonus_keyword: str | None = None,
                         bonus_tribe: str | None = None, _from_bounce: bool = False):
        """Past een Blood Gem toe op een minion: +1/+1 + permanente bonussen."""
        target.attack += 1 + self.blood_gem_attack_bonus
        target.health += 1 + self.blood_gem_health_bonus
        target.max_health += 1 + self.blood_gem_health_bonus
        if bonus_keyword:
            if bonus_tribe is None or bonus_tribe in target.types:
                setattr(target, bonus_keyword, True)
                if bonus_keyword not in target.abilities:
                    target.abilities.append(bonus_keyword)
        if not _from_bounce:
            if target.passive and target.passive.get("type") == "on_blood_gem_played_gold":
                if not getattr(target, "_hired_ritualist_triggered", False):
                    target._hired_ritualist_triggered = True
                    mult = 2 if target.golden else 1
                    self.gold = min(self.gold + target.passive.get("amount", 2) * mult, self.MAX_GOLD)
            if target.passive and target.passive.get("type") == "on_blood_gem_played_bounce":
                others = [m for m in self.board if m is not target]
                if others:
                    count = 2 if target.golden else 1
                    for _ in range(count):
                        self._apply_blood_gem(random.choice(others), _from_bounce=True)

    def _give_random_keyword(self, minion: Minion):
        keywords = ["taunt", "divine_shield", "reborn", "windfury"]
        kw = random.choice(keywords)
        setattr(minion, kw, True)
        if kw not in minion.abilities:
            minion.abilities.append(kw)

    # ── Schade ──────────────────────────────────────────────
    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    # ── Serialisatie ────────────────────────────────────────
    def to_dict(self, include_shop: bool = False) -> dict:
        d = {
            "sid": self.sid,
            "name": self.name,
            "is_ai": self.is_ai,
            "hp": self.hp,
            "tavern_tier": self.tavern_tier,
            "upgrade_cost": self.upgrade_cost,
            "gold": self.gold,
            "board": [m.to_dict() for m in self.board],
            "hand": [(m if isinstance(m, dict) else m.to_dict()) for m in self.hand],
            "frozen": self.frozen,
            "hero": self.hero,
            "ready": self.ready,
            "alive": self.alive,
        }
        if include_shop:
            d["shop"] = [
                (m if isinstance(m, dict) else m.to_dict()) if m else None
                for m in self.shop
            ]
        return d

    def public_dict(self) -> dict:
        """Wat andere spelers mogen zien."""
        return {
            "sid": self.sid,
            "name": self.name,
            "hp": self.hp,
            "tavern_tier": self.tavern_tier,
            "alive": self.alive,
            "hero": self.hero,
            "board_size": len(self.board),
        }
