import copy
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
        self.hp = 30
        self.armor = 0
        self.tavern_tier = 1
        # Start op 6 zodat start_turn ronde 1 het naar 5 brengt (officiële BG: ronde 1 kost 5 goud)
        self.upgrade_cost = 6
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
        self.passes_this_turn = 0
        self.total_passes_game = 0
        self.pass_free_used_this_turn = 0
        self.gold_spent_this_turn = 0
        self.last_combat_lost = False
        self.eternal_knight_deaths = 0
        self.sanlayn_scribe_deaths = 0
        self.deathrattles_triggered_game = 0
        self.spells_cast_game = 0
        self.pending_egg_hatch: "Minion | None" = None
        self._pending_choose_one: dict | None = None
        self.trinkets: list[dict] = []  # actieve trofeeën van de speler
        self._hero_power_used = 0       # reset elke beurt; getoetst aan uses_per_turn
        self._pending_well_wisher_pass: dict | None = None
        self._mrrglton_played_count = 0   # Mama/Papa Mrrglton scaling
        self._orc_estra_played_count = 0  # Orc-estra Conductor scaling
        self._fodder_refreshes_remaining = 0   # Laboratory Assistant
        self._health_cost_spell_uses = 0       # Bazaar Dealer
        self._health_cost_refresh_uses = 0     # Malchezaar
        self._waveling_refresh_hooks = 0       # Waveling post-death persistent hooks
        self._patient_scout_tier_map: dict[int, int] = {}  # uid -> current discover tier

    # ── Turn setup ──────────────────────────────────────────
    def start_turn(self, round_num: int):
        self._current_round = round_num
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
        self.passes_this_turn = 0
        self.pass_free_used_this_turn = 0
        self.gold_spent_this_turn = 0
        self._bloodbound_used = 0
        self._hero_power_used = 0
        # Recalculate per-turn health-cost uses from board
        self._health_cost_spell_uses = 0
        self._health_cost_refresh_uses = 0
        for m in self.board:
            if m.passive:
                ptype = m.passive.get("type")
                mult = 2 if m.golden else 1
                if ptype == "health_cost_spell_per_turn":
                    self._health_cost_spell_uses += m.passive.get("count", 1) * mult
                elif ptype == "health_cost_refresh_per_turn":
                    self._health_cost_refresh_uses += m.passive.get("count", 2) * mult
        # Patient Scout: increment discover tier for each one on board
        for m in self.board:
            if m.id == "patient_scout":
                current = self._patient_scout_tier_map.get(m.uid, 1)
                self._patient_scout_tier_map[m.uid] = min(current + 1, 6)
        # Ichoron: remove temp divine shields applied last turn
        for m in self.board:
            if getattr(m, "_ichoron_temp_ds", False):
                m._ichoron_temp_ds = False
                m.divine_shield = False
                if "divine_shield" in m.abilities:
                    m.abilities.remove("divine_shield")
        self._apply_start_of_round_hero()
        self.apply_trinket_start_of_turn()
        self._apply_start_of_turn_board()
        for m in self.board:
            if hasattr(m, "_hired_ritualist_triggered"):
                m._hired_ritualist_triggered = False
            # Mantid King: remove temp keyword from last turn
            kw = getattr(m, '_mantid_keyword', None)
            if kw:
                m._mantid_keyword = None
                setattr(m, kw, False)
                if kw in m.abilities:
                    m.abilities.remove(kw)
            # Storm Splitter: reset per-turn flag
            if hasattr(m, '_storm_splitter_used'):
                m._storm_splitter_used = False
            # Zesty Shaker: reset eenmalige trigger
            if hasattr(m, '_zesty_triggered'):
                m._zesty_triggered = False
        self._update_transport_reactor()
        self._check_board_thresholds()
        # Spellcraft: verwijder tijdelijke keywords van vorige beurt
        for m in self.board:
            for undo in getattr(m, "_temp_sc_keywords", []):
                if "restore_deathrattle" in undo:
                    m.deathrattle = undo["restore_deathrattle"]
                    if undo.get("added_deathrattle_ability") and "deathrattle" in m.abilities:
                        m.abilities.remove("deathrattle")
                if undo.get("remove_taunt"):
                    m.taunt = False
                    if "taunt" in m.abilities:
                        m.abilities.remove("taunt")
                if undo.get("remove_windfury"):
                    m.windfury = False
                    if "windfury" in m.abilities:
                        m.abilities.remove("windfury")
                if undo.get("remove_divine_shield"):
                    m.divine_shield = False
                    if "divine_shield" in m.abilities:
                        m.abilities.remove("divine_shield")
                if "restore_stats" in undo:
                    rs = undo["restore_stats"]
                    m.attack = rs["attack"]
                    m.health = min(m.health, rs["health"])
                    m.max_health = rs["max_health"]
            m._temp_sc_keywords = []
        # Spellcraft: genereer spreuk voor elke Naga op het board
        for m in self.board:
            if "spellcraft" in m.abilities and m.spellcraft:
                sc_spell = self._generate_spellcraft_spell(m)
                if sc_spell:
                    self.hand.append(sc_spell)
        # Egg of the Endtimes: beurt-teller bijhouden
        self.pending_egg_hatch = None
        for item in self.hand:
            if isinstance(item, Minion) and item.id == "egg_of_the_endtimes":
                item._turns_in_hand = getattr(item, "_turns_in_hand", 0) + 1
                if item._turns_in_hand >= 2 and self.pending_egg_hatch is None:
                    self.pending_egg_hatch = item

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
            return {"success": False, "message": "No hero selected."}
        ab = self.hero.get("ability", {})
        if ab.get("type") != "hero_power":
            return {"success": False, "message": "No active hero power."}
        # Unlock tier check
        unlock_tier = ab.get("unlock_tier")
        if unlock_tier and self.tavern_tier < unlock_tier:
            return {"success": False, "message": f"Available from Tavern Tier {unlock_tier}."}
        unlock_turn = ab.get("unlock_turn")
        if unlock_turn and getattr(self, "_current_round", 1) < unlock_turn:
            return {"success": False, "message": f"Available from turn {unlock_turn}."}
        cost = ab.get("cost", 2)
        if self.gold < cost:
            return {"success": False, "message": f"Not enough gold (costs {cost})."}
        uses_per_turn = ab.get("uses_per_turn", 1)
        if self._hero_power_used >= uses_per_turn:
            return {"success": False, "message": "Hero power already used this turn."}

        effect = ab.get("effect")
        self.gold -= cost
        self._hero_power_used += 1

        # ── Targeted effects ──────────────────────────────────────
        if effect == "give_divine_shield":
            t = self.board[target_index] if (target_index is not None and 0 <= target_index < len(self.board)) else (self.board[0] if self.board else None)
            if t:
                t.divine_shield = True
                if "divine_shield" not in t.abilities: t.abilities.append("divine_shield")
            return {"success": True, "effect": "give_divine_shield"}

        elif effect == "sharpen_blades":
            atk = ab.get("attack", 2); hp = ab.get("health", 2)
            t = self.board[target_index] if (target_index is not None and 0 <= target_index < len(self.board)) else (self.board[0] if self.board else None)
            if t:
                t.attack += atk; t.health += hp; t.max_health += hp
            return {"success": True, "effect": "sharpen_blades"}

        # ── Board-wide / random effects ───────────────────────────
        elif effect == "brick_by_brick":
            # Pyramad: steel random tavern minion + verdubbel z'n health
            candidates = [(i, m) for i, m in enumerate(self.shop)
                          if m is not None and isinstance(m, Minion)]
            if candidates:
                idx, stolen = random.choice(candidates)
                self.shop[idx] = None
                stolen.health *= 2; stolen.max_health *= 2
                self.hand.append(stolen)
            return {"success": True, "effect": "brick_by_brick"}

        elif effect == "tale_of_kings":
            # The Rat King: discover van wisselende tribe
            from game.data.minions import MINIONS as _MINS
            tribes = ["Beast", "Demon", "Dragon", "Elemental", "Mech",
                      "Murloc", "Naga", "Pirate", "Quilboar", "Undead"]
            idx_t = self.hero.get("_rat_tribe_idx", 0)
            tribe = tribes[idx_t % len(tribes)]
            self.hero["_rat_tribe_idx"] = (idx_t + 1) % len(tribes)
            pool = [mid for mid, d in _MINS.items() if tribe in d.get("types", [])]
            if pool:
                picks = random.sample(pool, min(3, len(pool)))
                options = [Minion.from_id(p).to_dict() for p in picks]
                return {"success": True, "effect": "tale_of_kings",
                        "hero_power_discover": options, "tribe": tribe}
            return {"success": True, "effect": "tale_of_kings"}

        elif effect == "conviction":
            if self.board:
                t = random.choice(self.board); t.attack += 1; t.health += 1; t.max_health += 1
            return {"success": True, "effect": "conviction"}

        elif effect == "saturday_cthuns":
            # C'Thun: +1/+1 to a random minion (simplified; real = EOT)
            if self.board:
                t = random.choice(self.board); t.attack += 1; t.health += 1; t.max_health += 1
            return {"success": True, "effect": "saturday_cthuns"}

        # ── Gold / shop effects ───────────────────────────────────
        elif effect == "graveyard_shift":
            # Lich Baz'hial: steel een tavern kaart, neem 2 schade
            dmg = ab.get("self_damage", 2)
            self._on_hero_damaged(dmg)
            candidates = [(i, m) for i, m in enumerate(self.shop)
                          if m is not None and isinstance(m, Minion)]
            if candidates:
                idx, stolen = random.choice(candidates)
                self.shop[idx] = None
                self.hand.append(stolen)
            return {"success": True, "effect": "graveyard_shift"}

        elif effect == "smart_savings":
            # Gallywix: stel in dat de volgende verkoop +1 goud volgende beurt geeft
            self._smart_savings_active = True
            return {"success": True, "effect": "smart_savings"}

        elif effect == "temporal_tavern":
            # Infinite Toki: gratis refresh, inclusief 2 kaarten van hogere tier
            self.free_refreshes_available += 1
            self._temporal_tavern_bonus = True  # game_state.reroll() voegt hogere tier toe
            return {"success": True, "effect": "temporal_tavern"}

        elif effect == "wisdom_of_ancients":
            self.MAX_GOLD = min(self.MAX_GOLD + 1, 14)
            return {"success": True, "effect": "wisdom_of_ancients"}

        elif effect == "galakronds_greed":
            # Replace leftmost shop minion with one of a higher tier
            slot = next((i for i, m in enumerate(self.shop) if m and not isinstance(m, dict)), None)
            if slot is not None:
                current_tier = self.shop[slot].tier
                higher_pool = [mid for mid, d in __import__("game.data.minions", fromlist=["MINIONS"]).MINIONS.items()
                               if d["tier"] > current_tier]
                if higher_pool:
                    self.shop[slot] = Minion.from_id(random.choice(higher_pool))
            return {"success": True, "effect": "galakronds_greed"}

        elif effect == "bloodbound":
            uses = ab.get("uses_per_turn", 2)
            used = getattr(self, "_bloodbound_used", 0)
            if used >= uses:
                self.gold += cost  # refund
                return {"success": False, "message": f"Already used {uses}× this turn."}
            self._bloodbound_used = used + 1
            count = ab.get("gems", 2) * (1 if not getattr(self, "double_bloodbound", False) else 2)
            for _ in range(count):
                self.hand.append(self._create_blood_gem())
            return {"success": True, "effect": "bloodbound"}

        elif effect == "galaxy_lens":
            # Farseer Nobundo: copy last spell, reduce next cost by 1
            if self.last_spell_cast:
                spell = {**self.last_spell_cast, "type": "spell"}
                self.hand.append(spell)
            ab["cost"] = max(0, ab.get("cost", 3) - 1)
            return {"success": True, "effect": "galaxy_lens"}

        elif effect == "efficient_exchange":
            # Madam Goya: wissel een hand-minion met een tavern-minion
            hand_minions = [(i, m) for i, m in enumerate(self.hand) if isinstance(m, Minion)]
            shop_minions = [(i, m) for i, m in enumerate(self.shop)
                            if m is not None and isinstance(m, Minion)]
            if hand_minions and shop_minions:
                hi, hm = random.choice(hand_minions)
                si, sm = random.choice(shop_minions)
                self.hand[hi] = sm
                self.shop[si] = hm
            return {"success": True, "effect": "efficient_exchange"}

        elif effect == "lucky_roll":
            # Snake Eyes: gooi d6, krijg dat veel goud
            roll = random.randint(1, 6)
            self.gold = min(self.gold + roll, self.MAX_GOLD)
            return {"success": True, "effect": "lucky_roll", "roll": roll}

        # ── Spell / hand effects ──────────────────────────────────
        elif effect == "blessing_nine_frogs":
            stat_spells = [s for tier_spells in SPELLS_BY_TIER.values() for s in tier_spells
                           if s["tier"] <= self.tavern_tier]
            if stat_spells:
                chosen = random.choice(stat_spells)
                self.hand.append({**chosen, "type": "spell", "cost": chosen.get("cost", 3)})
            return {"success": True, "effect": "blessing_nine_frogs"}

        # ── Discover effects ──────────────────────────────────────
        elif effect in ("discover_dragon", "lead_explorer", "pirate_parrrrty",
                        "build_an_undead", "discover_magnetic_mech", "sign_new_artist",
                        "buried_treasure"):
            from game.data.minions import MINIONS as _MINS
            if effect == "discover_dragon":
                pool = [mid for mid, d in _MINS.items() if "Dragon" in d.get("types", []) and d["tier"] <= self.tavern_tier + 1]
            elif effect == "lead_explorer":
                # Kost stijgt +1 na elk gebruik
                ab["cost"] = ab.get("cost", 1) + 1
                pool = [mid for mid, d in _MINS.items() if d["tier"] == self.tavern_tier]
            elif effect == "pirate_parrrrty":
                pool = [mid for mid, d in _MINS.items() if "Pirate" in d.get("types", [])]
            elif effect == "build_an_undead":
                pool = [mid for mid, d in _MINS.items() if "Undead" in d.get("types", [])]
            elif effect == "discover_magnetic_mech":
                pool = [mid for mid, d in _MINS.items() if "Mech" in d.get("types", []) and d["tier"] <= self.tavern_tier + 1]
            elif effect == "sign_new_artist":
                pool = [mid for mid, d in _MINS.items() if d["tier"] <= self.tavern_tier]
            elif effect == "buried_treasure":
                uses = self.hero.get("_digs_done", 0)
                max_digs = ab.get("digs_remaining", 4)
                self.hero["_digs_done"] = uses + 1
                digs_done = uses + 1
                if digs_done >= max_digs:
                    pool = [mid for mid, d in _MINS.items() if d["tier"] <= self.tavern_tier]
                    chosen = random.choice(pool) if pool else None
                    if chosen:
                        m = Minion.from_id(chosen); m.make_golden(); self.hand.append(m)
                    return {"success": True, "effect": "buried_treasure_golden"}
                else:
                    return {"success": True, "effect": "buried_treasure_dig",
                            "digs_done": digs_done, "digs_remaining": max_digs - digs_done}
            else:
                pool = [mid for mid, d in _MINS.items()]
            if pool:
                picks = random.sample(pool, min(3, len(pool)))
                options = [Minion.from_id(p).to_dict() for p in picks]
                return {"success": True, "effect": effect, "hero_power_discover": options}
            return {"success": True}

        # ── Nieuw geïmplementeerde effecten ───────────────────────

        elif effect == "rune_of_damnation":
            # The Jailer: vernietig een Undead, krijg random Undead
            from game.data.minions import MINIONS as _MINS
            undead = [m for m in self.board if "Undead" in m.types]
            if undead:
                target = random.choice(undead)
                self.board.remove(target)
                pool = [mid for mid, d in _MINS.items() if "Undead" in d.get("types", [])]
                if pool:
                    self.hand.append(Minion.from_id(random.choice(pool)))
            return {"success": True, "effect": "rune_of_damnation"}

        elif effect == "see_the_light":
            # Xyrella: steel tavern minion, set stats naar 2/2
            candidates = [(i, m) for i, m in enumerate(self.shop)
                          if m is not None and isinstance(m, Minion)]
            if candidates:
                idx, chosen = (
                    (target_index, self.shop[target_index])
                    if (target_index is not None and 0 <= target_index < len(self.shop)
                        and isinstance(self.shop[target_index], Minion))
                    else random.choice(candidates)
                )
                self.shop[idx] = None
                chosen.attack = 2; chosen.health = 2; chosen.max_health = 2
                self.hand.append(chosen)
            return {"success": True, "effect": "see_the_light"}

        elif effect == "the_perfect_crime":
            # Togwaggle: steel alle tavern kaarten, kosten zakken 1 per beurt
            for i in range(len(self.shop)):
                if self.shop[i] is not None and isinstance(self.shop[i], Minion):
                    self.hand.append(self.shop[i])
                    self.shop[i] = None
            ab["cost"] = max(0, ab.get("cost", 11) - 1)
            return {"success": True, "effect": "the_perfect_crime"}

        elif effect == "three_wishes":
            # Zephrys: als je 2 kopieën hebt van een minion, geef de derde
            candidates = [(mid, copies) for mid, copies in self.triple_tracker.items()
                          if len(copies) == 2]
            if candidates:
                mid, _ = candidates[0]
                m = Minion.from_id(mid)
                self.hand.append(m)
                triple = self._track_triple(m)
                return {"success": True, "effect": "three_wishes", "triple": triple}
            self.gold += cost  # geen kandidaten, refund
            return {"success": False, "message": "No minion with 2 copies found."}

        elif effect == "embrace_your_rage":
            # Y'Shaarj: voeg een minion van jouw tier toe aan hand (vereenvoudigd; eigenlijk start-of-combat)
            from game.data.minions import MINIONS as _MINS
            pool = [mid for mid, d in _MINS.items() if d["tier"] == self.tavern_tier]
            if pool:
                self.hand.append(Minion.from_id(random.choice(pool)))
            return {"success": True, "effect": "embrace_your_rage"}

        elif effect == "bobs_burgles":
            # Tess: vereenvoudigd — geef 3 random minions van jouw tier (real: kopieën tegenstander)
            from game.data.minions import MINIONS as _MINS
            pool = [mid for mid, d in _MINS.items() if d["tier"] <= self.tavern_tier]
            picks = random.sample(pool, min(3, len(pool)))
            for p in picks:
                self.shop.append(Minion.from_id(p))
            return {"success": True, "effect": "bobs_burgles"}

        elif effect == "snicker_snack":
            # Shudderwock: trigger een battlecry van een boardminion
            if target_index is None or not (0 <= target_index < len(self.board)):
                self.gold += cost
                return {"success": False, "message": "Choose a board minion to trigger the Battlecry."}
            target_m = self.board[target_index]
            if not target_m.battlecry:
                self.gold += cost
                return {"success": False, "message": f"{target_m.name} has no Battlecry."}
            self._apply_battlecry(target_m)
            return {"success": True, "effect": "snicker_snack",
                    "player": self.to_dict(include_shop=True)}

        # Stubs voor complexe effecten die opponent data of combat tracking vereisen
        elif effect in ("ill_take_that", "reclaimed_souls", "friendly_wager",
                         "i_spy", "imprison", "spawning_pool"):
            self.gold += cost  # refund
            return {"success": False, "message": "This hero power is not yet implemented."}

        return {"success": True}

    # ── Shop acties ─────────────────────────────────────────
    def can_buy(self) -> bool:
        return self.gold >= 3

    def buy_minion(self, shop_index: int, target_index: int | None = None) -> dict:
        if shop_index < 0 or shop_index >= len(self.shop):
            return {"success": False, "message": "Invalid shop index."}
        item = self.shop[shop_index]
        if item is None:
            return {"success": False, "message": "No minion at that slot."}
        # Spell dict in shop — redirect to spell handler
        if isinstance(item, dict):
            return self._cast_spell_from_shop(shop_index, target_index)
        minion = item
        # Leeching Felhound: costs Health instead of Gold
        health_cost = minion.passive and minion.passive.get("type") == "health_cost_buy"
        if health_cost:
            if self.hp <= 0:
                return {"success": False, "message": "Not enough health."}
            self.shop[shop_index] = None
            self._on_hero_damaged(3)
            # Soul Rewinder / Ashen Corruptor: rewind the health cost
            self._trigger_health_cost_buy_rewind(3)
        else:
            if not self.can_buy():
                return {"success": False, "message": "Not enough gold."}
            self.shop[shop_index] = None
            self.gold -= 3
            self._on_gold_spent(3)
        self.hand.append(minion)
        self._on_card_added_to_hand(minion)
        self._apply_game_counter_buff(minion)

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
            return {"success": False, "message": "Invalid board index."}
        minion = self.board.pop(board_index)
        self.gold = min(self.gold + self._sell_gold(minion), self.MAX_GOLD)
        self._remove_from_triple(minion)
        self._recalculate_board_passives()
        sell_passive = self._trigger_sell_passive(minion)
        # Gallywix smart_savings: volgende beurt +1 goud
        if getattr(self, "_smart_savings_active", False):
            self._smart_savings_active = False
            self.gold_next_turn_bonus += 1
        result = {"success": True, "gold": self.gold, "sold": minion.to_dict(), "sell_passive": sell_passive}
        if sell_passive and sell_passive.get("discover_options"):
            result["sell_discover"] = sell_passive["discover_options"]
        return result

    def reroll(self) -> dict:
        if self.free_refreshes_available > 0:
            self.free_refreshes_available -= 1
            return {"success": True, "gold": self.gold}
        # Malchezaar: refresh costs Health instead of Gold
        if self._health_cost_refresh_uses > 0:
            self._health_cost_refresh_uses -= 1
            self._on_hero_damaged(1)
            self._trigger_health_cost_buy_rewind(1)
            return {"success": True, "gold": self.gold}
        if self.gold < 1:
            return {"success": False, "message": "Not enough gold."}
        self.gold -= 1
        self._on_gold_spent(1)
        return {"success": True, "gold": self.gold}

    def toggle_freeze(self) -> dict:
        self.frozen = not self.frozen
        return {"success": True, "frozen": self.frozen}

    def upgrade_tavern(self) -> dict:
        if self.tavern_tier >= 6:
            return {"success": False, "message": "Already at maximum tavern tier."}
        if self.gold < self.upgrade_cost:
            return {"success": False, "message": f"Not enough gold (costs {self.upgrade_cost})."}
        cost_paid = self.upgrade_cost
        self.gold -= cost_paid
        self._on_gold_spent(cost_paid)
        self.tavern_tier += 1
        # Reset naar basiskost voor volgende tier; start_turn verlaagt daarna 1/ronde
        # Officiële BG basiskost: T2→T3=7, T3→T4=8, T4→T5=9, T5→T6=10
        tier_costs = {3: 7, 4: 8, 5: 9, 6: 10}
        next_tier = self.tavern_tier + 1
        self.upgrade_cost = tier_costs.get(next_tier, 0)
        # Forest Warden Omu: gain gold after leveling
        if self.hero and self.hero.get("ability", {}).get("effect") == "everbloom":
            gain = self.hero["ability"].get("gold_gain", 2)
            self.gold = min(self.gold + gain, self.MAX_GOLD)
        return {"success": True, "tavern_tier": self.tavern_tier, "gold": self.gold}

    def move_minion(self, from_idx: int, to_idx: int) -> dict:
        if not (0 <= from_idx < len(self.board) and 0 <= to_idx < len(self.board)):
            return {"success": False, "message": "Invalid position."}
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
        if self.pending_egg_hatch is not None:
            egg = self.pending_egg_hatch
            self.pending_egg_hatch = None
            if egg in self.hand:
                self.hand.remove(egg)
            if egg.golden:
                minion.make_golden()
        self.hand.append(minion)
        self._on_card_added_to_hand(minion)
        self._apply_game_counter_buff(minion)
        return {"success": True}

    def _remove_from_triple(self, minion: Minion):
        key = minion.id
        if key in self.triple_tracker and minion in self.triple_tracker[key]:
            self.triple_tracker[key].remove(minion)

    # ── Hand acties ─────────────────────────────────────────────
    def play_from_hand(self, hand_index: int, board_index: int = -1) -> dict:
        if hand_index < 0 or hand_index >= len(self.hand):
            return {"success": False, "message": "Invalid hand index."}
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
                return {"success": False, "message": "No minions to play Blood Gem on."}
            self.hand.pop(hand_index)
            target = self.board[board_index] if 0 <= board_index < len(self.board) else self.board[0]
            self._apply_blood_gem(target, item.get("bonus_keyword"), item.get("bonus_tribe"), _from_hand=True)
            return {"success": True, "blood_gem": True, "target": target.to_dict()}
        if len(self.board) >= self.MAX_BOARD:
            # Catacomb Crasher: board overflow → buff all minions permanently
            for m in self.board:
                if m.passive and m.passive.get("type") == "on_board_overflow_buff_all":
                    mult = 2 if m.golden else 1
                    atk = m.passive.get("attack", 1) * mult
                    hp = m.passive.get("health", 1) * mult
                    for ally in self.board:
                        ally.attack += atk; ally.health += hp; ally.max_health += hp
                    break
            return {"success": False, "message": "Board is full (max 7). Sell a minion to make room."}
        minion = self.hand.pop(hand_index)
        if 0 <= board_index < len(self.board):
            self.board.insert(board_index, minion)
        else:
            self.board.append(minion)
        self.cards_played_this_turn += 1
        self._recalculate_board_passives()

        # Deep Blue Crooner: pas gestapelde "improve" bonus toe
        if minion.id == "deep_blue_crooner":
            improve = getattr(self, "_deep_blue_improve", 0)
            if improve:
                minion.attack += improve; minion.health += improve; minion.max_health += improve

        battlecry_result = None
        if minion.battlecry:
            battlecry_result = self._apply_battlecry(minion)
            for _ in range(self.battlecry_triggers - 1):
                self._apply_battlecry(minion)

        # Choose One battlecry
        choose_one_options = None
        if minion.choose_one:
            mult = 2 if minion.golden else 1
            self._pending_choose_one = {"uid": minion.uid, "effects": minion.choose_one, "mult": mult}
            choose_one_options = [
                {"index": i, "label": opt["label"]}
                for i, opt in enumerate(minion.choose_one)
            ]

        play_passives = self._trigger_play_passives(minion, battlecry_fired=bool(battlecry_result))

        # Spellcraft: Naga gespeeld → direct spreuk in hand voor deze beurt
        if "spellcraft" in minion.abilities and minion.spellcraft:
            sc_spell = self._generate_spellcraft_spell(minion)
            if sc_spell:
                self.hand.append(sc_spell)

        result = {"success": True, "battlecry": battlecry_result, "play_passives": play_passives}
        if choose_one_options:
            result["choose_one_options"] = choose_one_options
        return result

    def apply_choose_one(self, choice: int) -> dict:
        pending = self._pending_choose_one
        if not pending:
            return {"success": False, "message": "No pending choice."}
        effects = pending["effects"]
        if choice < 0 or choice >= len(effects):
            return {"success": False, "message": "Invalid choice."}
        effect = effects[choice]
        mult = pending["mult"]
        uid = pending["uid"]
        self._pending_choose_one = None

        minion = next((m for m in self.board if m.uid == uid), None)
        etype = effect["type"]

        if etype == "beast_reborn_buff":
            beasts = [m for m in self.board if "Beast" in m.types]
            target = random.choice(beasts) if beasts else minion
            if target:
                target.attack += effect.get("attack", 1) * mult
                target.health += effect.get("health", 1) * mult
                target.max_health += effect.get("health", 1) * mult
                target.reborn = True
                if "reborn" not in target.abilities:
                    target.abilities.append("reborn")

        elif etype == "self_attack_windfury":
            if minion:
                minion.attack += effect.get("attack", 4) * mult
                minion.windfury = True
                if "windfury" not in minion.abilities:
                    minion.abilities.append("windfury")

        elif etype == "spell_attack_bonus":
            self.spell_attack_bonus += effect.get("amount", 1) * mult

        elif etype == "spell_health_bonus":
            self.spell_health_bonus += effect.get("amount", 1) * mult

        elif etype == "blood_gem_both_bonus":
            amt = effect.get("amount", 1) * mult
            self.blood_gem_attack_bonus += amt
            self.blood_gem_health_bonus += amt

        elif etype == "give_blood_gems":
            count = effect.get("count", 4) * mult
            for _ in range(count):
                self.hand.append(self._create_blood_gem())

        return {"success": True}

    # ── Spreuken ─────────────────────────────────────────────────
    def _cast_spell_from_shop(self, shop_index: int, target_index: int | None = None) -> dict:
        """Koop een spreuk uit de winkel: gaat naar hand (niet direct gecastet)."""
        spell = self.shop[shop_index]
        cost = max(0, spell.get("cost", 3) - self.next_spell_discount)
        self.next_spell_discount = 0
        # Bazaar Dealer: costs Health instead of Gold
        if self._health_cost_spell_uses > 0:
            self._health_cost_spell_uses -= 1
            self.shop[shop_index] = None
            self._on_hero_damaged(cost)
            self._trigger_health_cost_buy_rewind(cost)
            self.hand.append(spell)
            self._on_card_added_to_hand(spell)
            return {"success": True, "spell": spell}
        if self.gold < cost:
            return {"success": False, "message": f"Not enough gold (costs {cost})."}
        self.shop[shop_index] = None
        self.gold -= cost
        if cost > 0:
            self._on_gold_spent(cost)
        self.hand.append(spell)
        self._on_card_added_to_hand(spell)
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
        elif sid == "blood_gem_barrage":
            # Give each friendly Quilboar a Blood Gem
            for m in self.board:
                if "Quilboar" in m.types:
                    self._apply_blood_gem(m)

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
                prev_dr = t.deathrattle
                had_dr_ability = "deathrattle" in t.abilities
                t.deathrattle = {"type": "summon", "token": "crab"}
                if not had_dr_ability:
                    t.abilities.append("deathrattle")
                if not hasattr(t, "_temp_sc_keywords"):
                    t._temp_sc_keywords = []
                t._temp_sc_keywords.append({"restore_deathrattle": prev_dr,
                                             "added_deathrattle_ability": not had_dr_ability})
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
                mult = 2 if any(m.id == "deep_blue_crooner" and m.golden for m in self.board) else 1
                atk_buff = 2 * mult + self.spell_attack_bonus
                hp_buff = 3 * mult + self.spell_health_bonus
                prev_atk = t.attack; prev_hp = t.health; prev_max = t.max_health
                t.attack += atk_buff; t.health += hp_buff; t.max_health += hp_buff
                if not hasattr(t, "_temp_sc_keywords"):
                    t._temp_sc_keywords = []
                t._temp_sc_keywords.append({"restore_stats": {"attack": prev_atk, "health": prev_hp, "max_health": prev_max}})
                self._deep_blue_improve = getattr(self, "_deep_blue_improve", 0) + (2 if mult == 2 else 1)
        elif sid == "sc_deep_sea_angler":
            t = _target()
            if t:
                t.attack += 2; t.health += 6; t.max_health += 6
                had_taunt = t.taunt
                _give_taunt(t)
                if not had_taunt:
                    if not hasattr(t, "_temp_sc_keywords"):
                        t._temp_sc_keywords = []
                    t._temp_sc_keywords.append({"remove_taunt": True})
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
                    if not hasattr(t, "_temp_sc_keywords"):
                        t._temp_sc_keywords = []
                    t._temp_sc_keywords.append({"remove_windfury": True})
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
                had_ds = t.divine_shield
                t.divine_shield = True
                if "divine_shield" not in t.abilities:
                    t.abilities.append("divine_shield")
                if not had_ds:
                    if not hasattr(t, "_temp_sc_keywords"):
                        t._temp_sc_keywords = []
                    t._temp_sc_keywords.append({"remove_divine_shield": True})
        elif sid == "sc_tranquil_meditative":
            mult = 2 if any(m.id == "tranquil_meditative" and m.golden for m in self.board) else 1
            self.spell_attack_bonus += 1 * mult
            self.spell_health_bonus += 1 * mult
        elif sid == "sc_well_wisher":
            candidates = [m for m in self.board if not m.golden]
            if candidates:
                chosen = _r.choice(candidates)
                self.board.remove(chosen)
                self._pending_well_wisher_pass = chosen.to_dict()

        # Zesty Shaker: als een spellcraft spreuk op hem gespeeld wordt, geef een kopie (1x/beurt)
        if spell.get("id", "").startswith("sc_") and target_index is not None:
            t = _target()
            if t and t.passive and t.passive.get("type") == "on_spellcraft_target_get_copy":
                if not getattr(t, "_zesty_triggered", False):
                    t._zesty_triggered = True
                    copies = 2 if t.golden else 1
                    for _ in range(copies):
                        self.hand.append({**spell, "type": "spell"})

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

        # Balinda Stonehearth: targeted spells cast twice
        if target_index is not None and spell.get("type") == "spell":
            for m in self.board:
                if m.passive and m.passive.get("type") == "targeted_spells_cast_twice":
                    if not getattr(self, "_balinda_recast", False):
                        self._balinda_recast = True
                        self._apply_spell(spell, target_index)
                        self._balinda_recast = False
                    break

        # Batty Terrorguard: after any spell, a random Demon consumes a tavern minion
        shop_minions = [(i, sm) for i, sm in enumerate(self.shop)
                        if sm is not None and isinstance(sm, Minion)]
        if shop_minions:
            for m in self.board:
                if m.passive and m.passive.get("type") == "on_spell_cast_demon_consume" and m is not None:
                    demons = [d for d in self.board if "Demon" in d.types and d is not m]
                    if demons:
                        demon = _r.choice(demons)
                        idx2, consumed = _r.choice(shop_minions)
                        self.shop[idx2] = None
                        dmult = 2 if demon.golden else 1
                        demon.attack += consumed.attack * dmult
                        demon.health += consumed.health * dmult
                        demon.max_health += consumed.health * dmult
                    break

        # Proud Privateer: Bounties cast twice
        if "bounty" in sid:
            for m in self.board:
                if m.passive and m.passive.get("type") == "on_bounty_cast_twice":
                    if not getattr(self, "_proud_recast", False):
                        self._proud_recast = True
                        self._apply_spell(spell, target_index)
                        self._proud_recast = False
                    break

        # Tidecaller Prophet: spells give extra +X/+X to all board minions this turn
        for m in self.board:
            if m.passive and m.passive.get("type") == "tavern_spell_bonus_scaling":
                mult = 2 if m.golden else 1
                bonus_atk = m.passive.get("attack", 1) * mult
                bonus_hp = m.passive.get("health", 1) * mult
                for ally in self.board:
                    ally.attack += bonus_atk
                    ally.health += bonus_hp
                    ally.max_health += bonus_hp
                break

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
            return {"success": False, "message": "Invalid hand index."}
        item = self.hand[hand_index]
        if isinstance(item, dict):
            return {"success": False, "message": "Spells cannot be sold."}
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

        if effect == "blood_gems_all_board":
            mult = 2 if minion.golden else 1
            count = bc.get("count", 2) * mult
            for ally in [m for m in self.board if m is not minion]:
                for _ in range(count):
                    self._apply_blood_gem(ally)
            return {"blood_gems_all_board": True}

        if effect == "blood_gem_with_keyword_tribe":
            tribe = bc.get("tribe")
            kw = bc.get("keyword", "divine_shield")
            mult = 2 if minion.golden else 1
            count = bc.get("count", 1) * mult
            for _ in range(count):
                self.hand.append(self._create_blood_gem(bonus_keyword=kw, bonus_tribe=tribe))
            return {"blood_gem_with_keyword": True}

        if effect == "get_slimy_shields":
            mult = 2 if minion.golden else 1
            count = bc.get("count", 2) * mult
            for _ in range(count):
                self.hand.append({
                    "type": "blood_gem", "id": "slimy_shield", "name": "Slimy Shield",
                    "cost": 0, "description": "Geef een minion +1/+1 en Taunt.",
                    "bonus_keyword": "taunt",
                })
            return {"slimy_shields": count}

        if effect == "discover_tribe":
            from game.data.minions import MINIONS
            tribe = bc.get("tribe")
            require = bc.get("require_tribe")
            if require and not any(require in m.types for m in self.board if m is not minion):
                return None
            pool = [m for m in MINIONS.values() if tribe in m.get("types", [])]
            if not pool:
                return None
            chosen = random.sample(pool, min(3, len(pool)))
            return {"discover_options": [{"id": m["id"], "name": m["name"], "tier": m["tier"],
                    "attack": m["attack"], "health": m["health"], "tribe": m.get("tribe"),
                    "description": m.get("description", ""), "abilities": m.get("abilities", []),
                    "golden": False} for m in chosen]}

        if effect == "discover_tribe_self_damage":
            from game.data.minions import MINIONS
            tribe = bc.get("tribe")
            pool = [m for m in MINIONS.values() if tribe in m.get("types", [])]
            if not pool:
                return None
            chosen = random.sample(pool, min(3, len(pool)))
            result = {"discover_options": [{"id": m["id"], "name": m["name"], "tier": m["tier"],
                       "attack": m["attack"], "health": m["health"], "tribe": m.get("tribe"),
                       "description": m.get("description", ""), "abilities": m.get("abilities", []),
                       "golden": False} for m in chosen],
                      "self_damage_tier": True}
            self._on_hero_damaged(minion.tier)
            return result

        if effect == "destroy_undead_get_copy":
            undead = [m for m in self.board if "Undead" in m.types and m is not minion]
            if not undead:
                return None
            target = random.choice(undead)
            self.board.remove(target)
            mult = 2 if minion.golden else 1
            for _ in range(mult):
                fresh = Minion.from_id(target.id)
                self.hand.append(fresh)
            return {"destroyed": target.to_dict()}

        if effect == "buff_tribe_by_gold_spent":
            tribe = bc.get("tribe")
            hp_per = bc.get("health", 1) * (2 if minion.golden else 1)
            atk_per = bc.get("attack", 0) * (2 if minion.golden else 1)
            bonus = self.gold_spent_this_turn
            targets = [m for m in self.board if tribe in m.types and m is not minion]
            if targets:
                t = random.choice(targets)
                t.health += hp_per + bonus * hp_per
                t.max_health += hp_per + bonus * hp_per
                if atk_per:
                    t.attack += atk_per + bonus * atk_per
                return {"buffed": t.to_dict()}

        if effect == "buff_random_board_by_spells":
            mult = 2 if minion.golden else 1
            repeats = 1 + self.cards_played_this_turn
            atk = bc.get("attack", 2) * mult
            hp = bc.get("health", 2) * mult
            targets = [m for m in self.board if m is not minion]
            if targets:
                t = random.choice(targets)
                for _ in range(repeats):
                    t.attack += atk
                    t.health += hp
                    t.max_health += hp
                self._check_board_thresholds()
                return {"buffed": t.to_dict()}

        if effect == "discover_tavern_spell":
            pool = [s for tier_spells in SPELLS_BY_TIER.values() for s in tier_spells
                    if s.get("tier", 99) <= self.tavern_tier]
            if pool:
                picks = random.sample(pool, min(3, len(pool)))
                return {"discover_options": [
                    {"id": s["id"], "name": s["name"], "tier": s["tier"],
                     "cost": s.get("cost", 3), "description": s.get("description", ""),
                     "type": "spell"}
                    for s in picks
                ]}

        if effect == "buff_tribe_improved_mrrglton":
            tribe = bc.get("tribe")
            mult = 3 if minion.golden else 1
            base_atk = bc.get("base_attack", 2)
            base_hp = bc.get("base_health", 0)
            per_atk = bc.get("per_mrrglton_attack", 2)
            per_hp = bc.get("per_mrrglton_health", 0)
            bonus_atk = (base_atk + per_atk * self._mrrglton_played_count) * mult
            bonus_hp = (base_hp + per_hp * self._mrrglton_played_count) * mult
            targets = [m for m in self.board if tribe in m.types and m is not minion]
            for t in targets:
                t.attack += bonus_atk
                t.health += bonus_hp
                t.max_health += bonus_hp
            # Count this Mrrglton as played (affects future casts)
            self._mrrglton_played_count += 1
            return {"buffed_all": [t.to_dict() for t in targets]} if targets else None

        if effect == "buff_target_orc_estra_scaling":
            mult = 2 if minion.golden else 1
            base_atk = bc.get("base_attack", 2) * mult
            base_hp = bc.get("base_health", 2) * mult
            per_atk = bc.get("per_orc_estra_attack", 2) * mult
            per_hp = bc.get("per_orc_estra_health", 2) * mult
            bonus_atk = base_atk + per_atk * self._orc_estra_played_count
            bonus_hp = base_hp + per_hp * self._orc_estra_played_count
            self._orc_estra_played_count += 1
            targets = [m for m in self.board if m is not minion] + [
                m for m in self.hand if isinstance(m, Minion) and m is not minion
            ]
            if targets:
                t = random.choice(targets)
                t.attack += bonus_atk
                t.health += bonus_hp
                t.max_health += bonus_hp
                return {"buffed": t.to_dict()}

        if effect == "buff_tavern_tribe":
            tribe = bc.get("tribe")
            mult = 2 if minion.golden else 1
            atk = bc.get("attack", 0) * mult
            hp = bc.get("health", 0) * mult
            count = 0
            for slot in self.shop:
                if slot is None or isinstance(slot, dict):
                    continue
                if tribe is None or tribe in slot.types:
                    slot.attack += atk
                    slot.health += hp
                    slot.max_health += hp
                    count += 1
            return {"buffed_tavern_tribe": tribe, "count": count}

        if effect == "add_fodder_to_refreshes":
            count = bc.get("count", 3)
            per_refresh = bc.get("fodder_per_refresh", 1)
            if minion.golden:
                per_refresh *= 2
            self._fodder_refreshes_remaining += count * per_refresh
            return {"fodder_refreshes": count}

        return None

    def _on_gold_spent(self, amount: int):
        """Bijhouden gouduitgaven per beurt + threshold-passives triggeren."""
        self.gold_spent_this_turn += amount
        for m in self.board:
            if not m.passive or m.passive.get("type") != "on_gold_spent_threshold":
                continue
            threshold = m.passive.get("threshold", 5)
            remaining = getattr(m, "_gold_threshold_remaining", threshold)
            remaining -= amount
            while remaining <= 0:
                remaining += threshold
                mult = 2 if m.golden else 1
                effect = m.passive.get("effect")
                if effect == "buff_tribe":
                    tribe = m.passive.get("tribe")
                    atk = m.passive.get("attack", 1) * mult
                    for ally in self.board:
                        if tribe in ally.types:
                            ally.attack += atk
                elif effect == "buff_two_random_tribe":
                    tribe = m.passive.get("tribe")
                    atk = m.passive.get("attack", 4) * mult
                    hp = m.passive.get("health", 4) * mult
                    targets = [a for a in self.board if tribe in a.types]
                    for t in random.sample(targets, min(2 * mult, len(targets))):
                        t.attack += atk
                        t.health += hp
                        t.max_health += hp
                elif effect == "blood_gems_tribe":
                    tribe = m.passive.get("tribe")
                    count = m.passive.get("count", 1) * mult
                    for ally in self.board:
                        if tribe in ally.types:
                            for _ in range(count):
                                self._apply_blood_gem(ally)
                elif effect == "get_spell":
                    spell_id = m.passive.get("spell")
                    if spell_id and spell_id in _SPELLS_FLAT:
                        for _ in range(mult):
                            self.hand.append({**_SPELLS_FLAT[spell_id], "type": "spell"})
            m._gold_threshold_remaining = remaining

    def _check_board_thresholds(self):
        """Controleer stat-drempel passives (scarlet_survivor, defiant_shipwright)."""
        for m in self.board:
            if not m.passive:
                continue
            ptype = m.passive.get("type")
            if ptype == "attack_threshold_divine_shield":
                if m.attack >= m.passive.get("threshold", 6) and not m.divine_shield:
                    m.divine_shield = True
                    if "divine_shield" not in m.abilities:
                        m.abilities.append("divine_shield")

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

            elif ptype == "on_pirate_gained_buff_all" and "Pirate" in bought.types:
                # Dastardly Drust: Pirate gained → buff all minions (+1/+1, goldens +2/+2)
                for ally in self.board:
                    mult = 4 if ally.golden else 2 if m.golden else 1
                    base_atk = m.passive.get("attack", 1)
                    base_hp = m.passive.get("health", 1)
                    ally.attack += base_atk * (2 if ally.golden else 1)
                    ally.health += base_hp * (2 if ally.golden else 1)
                    ally.max_health += base_hp * (2 if ally.golden else 1)
                events.append({"type": "buy_passive", "uid": m.uid})

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
                self._on_hero_damaged(dmg)
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

            elif ptype == "on_murloc_played_buff_hand_self" and "Murloc" in played.types and m is not played:
                # Bream Counter: in hand, buffs itself when a Murloc is played
                pass  # handled below (hand passives)

            elif ptype == "on_murloc_played_buff_board_hand" and "Murloc" in played.types:
                # Mrglin' Burglar: buff one board minion + one hand minion
                mult = 2 if m.golden else 1
                atk = m.passive.get("attack", 4) * mult
                hp = m.passive.get("health", 3) * mult
                board_targets = [a for a in self.board if a is not m and a is not played]
                if board_targets:
                    t = random.choice(board_targets)
                    t.attack += atk; t.health += hp; t.max_health += hp
                hand_minions = [h for h in self.hand if isinstance(h, Minion)]
                if hand_minions:
                    t2 = random.choice(hand_minions)
                    t2.attack += atk; t2.health += hp; t2.max_health += hp
                events.append({"type": "play_passive", "uid": m.uid})

            elif ptype == "on_beast_played_buff_attack" and "Beast" in played.types:
                # Lurking Leviathan: give played Beast +2 Attack, buff self permanently
                mult = 2 if m.golden else 1
                atk = m.passive.get("attack", 2) * mult
                played.attack += atk
                m.attack += atk; m.health += 1; m.max_health += 1
                events.append({"type": "play_passive", "uid": m.uid})

            elif ptype == "on_elemental_played_give_ds" and "Elemental" in played.types:
                # Ichoron: give played Elemental Divine Shield until next turn
                if not played.divine_shield:
                    played.divine_shield = True
                    if "divine_shield" not in played.abilities:
                        played.abilities.append("divine_shield")
                    played._ichoron_temp_ds = True
                events.append({"type": "play_passive", "uid": m.uid})

            elif ptype == "on_naga_played_buff_self" and "Naga" in played.types:
                # Groundbreaker: gain +1/+1, improved by every 4 spells cast
                mult = 2 if m.golden else 1
                base = m.passive.get("attack", 1) * mult
                bonus = (self.spells_cast_game // 4) * mult
                total = base + bonus
                m.attack += total; m.health += total; m.max_health += total
                events.append({"type": "play_passive", "uid": m.uid})

            elif ptype == "on_play_buff_by_tier":
                # One-Amalgam Tour Group: buff minions of played card's tier or lower
                mult = 2 if m.golden else 1
                atk = m.passive.get("attack", 1) * mult
                hp = m.passive.get("health", 1) * mult
                for ally in self.board:
                    if ally is not played and ally.tier <= played.tier:
                        ally.attack += atk; ally.health += hp; ally.max_health += hp
                events.append({"type": "play_passive", "uid": m.uid})

            elif ptype == "on_play_low_tier_buff_tribe" and played.tier <= m.passive.get("max_tier", 3):
                # Primitive Painter: play T3-: buff Murlocs
                tribe = m.passive.get("tribe")
                mult = 2 if m.golden else 1
                atk = m.passive.get("attack", 1) * mult
                hp = m.passive.get("health", 2) * mult
                for ally in self.board:
                    if tribe is None or tribe in ally.types:
                        ally.attack += atk; ally.health += hp; ally.max_health += hp
                events.append({"type": "play_passive", "uid": m.uid})

            elif ptype == "on_beast_played_buff_damage_beasts" and "Beast" in played.types:
                # Rabid Panther: buff all Beasts +3/+3, deal 1 damage to each
                mult = 2 if m.golden else 1
                atk = m.passive.get("attack", 3) * mult
                hp = m.passive.get("health", 3) * mult
                dmg = m.passive.get("damage", 1)
                for ally in self.board:
                    if "Beast" in ally.types:
                        ally.attack += atk; ally.health += hp; ally.max_health += hp
                        ally.health -= dmg
                events.append({"type": "play_passive", "uid": m.uid})

        # Bream Counter: check hand passives (minion in hand reacts to Murloc play)
        if "Murloc" in played.types:
            for item in self.hand:
                if isinstance(item, Minion) and item.passive:
                    if item.passive.get("type") == "on_murloc_played_buff_hand_self":
                        mult = 2 if item.golden else 1
                        item.attack += item.passive.get("attack", 4) * mult
                        item.health += item.passive.get("health", 4) * mult
                        item.max_health += item.passive.get("health", 4) * mult

        # Elemental played: trigger Nomi and Unleashed Mana Surge passives
        if "Elemental" in played.types:
            for m in self.board:
                if not m.passive or m is played:
                    continue
                ptype = m.passive.get("type")
                mult = 2 if m.golden else 1
                if ptype == "on_elemental_played_buff_tavern":
                    atk = m.passive.get("attack", 4) * mult
                    hp = m.passive.get("health", 4) * mult
                    for slot in self.shop:
                        if slot is None or isinstance(slot, dict):
                            continue
                        if "Elemental" in slot.types:
                            slot.attack += atk
                            slot.health += hp
                            slot.max_health += hp
                    events.append({"type": "play_passive", "uid": m.uid})
                elif ptype == "on_elemental_played_buff_board":
                    atk = m.passive.get("attack", 4) * mult
                    hp = m.passive.get("health", 4) * mult
                    for ally in self.board:
                        if "Elemental" in ally.types:
                            ally.attack += atk
                            ally.health += hp
                            ally.max_health += hp
                    events.append({"type": "play_passive", "uid": m.uid})

        # Tidecaller Prophet: track Murloc plays, improve after every N Murlocs
        if "Murloc" in played.types:
            for m in self.board:
                if not m.passive or m is played:
                    continue
                if m.passive.get("type") == "tavern_spell_bonus_scaling":
                    counter = getattr(m, "_tcp_murloc_count", 0) + 1
                    m._tcp_murloc_count = counter
                    threshold = m.passive.get("murlocs_per_upgrade", 2)
                    if counter >= threshold:
                        m._tcp_murloc_count = 0
                        mult = 2 if m.golden else 1
                        m.passive = {**m.passive,
                                     "attack": m.passive.get("attack", 1) + 1 * mult,
                                     "health": m.passive.get("health", 1) + 1 * mult}
                    events.append({"type": "play_passive", "uid": m.uid})

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

        if ptype == "on_sell_buff_tribe":
            # Plaguerunner: selling outside combat gives +4 Attack to all Undead (instead of +2 in combat)
            tribe = sold.passive.get("tribe")
            atk = sold.passive.get("attack", 4) * multiplier
            for m in self.board:
                if tribe is None or tribe in m.types:
                    m.attack += atk
            for item in self.hand:
                if isinstance(item, Minion) and (tribe is None or tribe in item.types):
                    item.attack += atk
            return {"buffed_tribe": tribe, "attack": atk}

        if ptype == "on_sell_pass" and not getattr(sold, '_jumping_jack_passed', False):
            sold._jumping_jack_passed = True
            return {"type": "sell_then_pass", "minion": sold.to_dict()}

        if ptype == "on_sell_if_lost_bonus_gold" and self.last_combat_lost:
            bonus = sold.passive.get("gold", 5) * multiplier - 1  # -1 want base gold al uitbetaald
            self.gold = min(self.gold + bonus, self.MAX_GOLD)
            return {"bonus_gold": bonus}

        if ptype == "on_sell_discover_tier_upgrading":
            from game.data.minions import MINIONS
            tier = self._patient_scout_tier_map.pop(sold.uid, sold.passive.get("base_tier", 1))
            tier = min(tier, 6)
            pool = [m for m in MINIONS.values() if m["tier"] == tier]
            if not pool:
                return None
            count = multiplier  # golden = 2 discovers
            options_list = []
            for _ in range(count):
                picks = random.sample(pool, min(3, len(pool)))
                options_list.append([
                    {"id": d["id"], "name": d["name"], "tier": d["tier"],
                     "attack": d.get("attack", 0), "health": d.get("health", 0),
                     "description": d.get("description", ""), "golden": False}
                    for d in picks
                ])
            return {"discover_options": options_list[0], "discover_tier": tier}

        return None

    def _recalculate_board_passives(self):
        """Herbereken board-brede passieve effecten (bijv. Brann op board = double battlecry)."""
        brann = next((m for m in self.board if m.id == "brann_bronzebeard"), None)
        hero_double = (self.hero is not None
                       and self.hero.get("ability", {}).get("effect") == "double_battlecry")
        if brann:
            self.battlecry_triggers = 3 if brann.golden else 2
        elif hero_double:
            self.battlecry_triggers = 2
        else:
            self.battlecry_triggers = 1
        self.double_battlecry = self.battlecry_triggers > 1

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

            elif etype == "eot_blood_gem_all_minions":
                count = eot.get("count", 1) * mult
                for ally in list(self.board):
                    for _ in range(count):
                        self._apply_blood_gem(ally)
                self._check_board_thresholds()
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_demon_consume_tavern":
                shop_minions = [(i, sm) for i, sm in enumerate(self.shop)
                                if sm is not None and isinstance(sm, Minion)]
                demons = [dm for dm in self.board if "Demon" in dm.types]
                for demon in demons:
                    if not shop_minions:
                        break
                    idx2, consumed = random.choice(shop_minions)
                    shop_minions = [(i, s) for i, s in shop_minions if i != idx2]
                    self.shop[idx2] = None
                    dmult = 2 if demon.golden else 1
                    demon.attack += consumed.attack * dmult * mult
                    demon.health += consumed.health * dmult * mult
                    demon.max_health += consumed.health * dmult * mult
                events.append({"type": "eot", "uid": m.uid})

            elif etype == "eot_get_satellite":
                # Moonsteel Juggernaut: get a 6/6 Magnetic Satellite, improve self
                satellite_id = eot.get("satellite_id", "magnetic_satellite")
                sat = Minion.from_id(satellite_id)
                self.hand.append(sat)
                if m.golden:
                    # Golden: get two satellites
                    self.hand.append(Minion.from_id(satellite_id))
                buff = eot.get("self_buff", 2) * mult
                m.attack += buff; m.health += buff; m.max_health += buff
                events.append({"type": "eot", "uid": m.uid})

        # Drakkari Enchanter: EOT effecten extra keer triggeren
        drakkari = next((m for m in self.board if m.passive and m.passive.get("type") == "double_eot"), None)
        if drakkari and events:
            extra = (3 if drakkari.golden else 2) - 1
            for _ in range(extra):
                for m in list(self.board):
                    eot = m.end_of_turn
                    if not eot:
                        continue
                    mult = 2 if m.golden else 1
                    etype = eot.get("type")
                    if etype == "eot_give_blood_gems":
                        count = eot.get("count", 1) * mult
                        kw = eot.get("bonus_keyword")
                        tribe = eot.get("bonus_tribe")
                        for _ in range(count):
                            self.hand.append(self._create_blood_gem(kw, tribe))
                    elif etype == "eot_blood_gem_all_minions":
                        for ally in list(self.board):
                            self._apply_blood_gem(ally)
                    elif etype == "eot_buff_adjacent_goldens":
                        pass  # skip complex re-runs

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
        self.spells_cast_game += 1
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

            elif ptype == "has_per_spell_cast":
                atk = m.passive.get("attack", 1) * mult
                hp = m.passive.get("health", 1) * mult
                m.attack += atk; m.health += hp; m.max_health += hp
                events.append({"type": "spell_cast_passive", "uid": m.uid})

        for item in self.hand:
            if isinstance(item, Minion) and item.passive and item.passive.get("type") == "has_per_spell_cast":
                mult = 2 if item.golden else 1
                item.attack += item.passive.get("attack", 1) * mult
                item.health += item.passive.get("health", 1) * mult
                item.max_health += item.passive.get("health", 1) * mult

        return events

    def _trigger_health_cost_buy_rewind(self, amount: int):
        """Soul Rewinder / Ashen Corruptor: undo the health cost when buying with HP."""
        for m in self.board:
            if not m.passive:
                continue
            if m.passive.get("type") != "on_health_cost_buy_rewind":
                continue
            mult = 2 if m.golden else 1
            # Restore the HP that was spent
            self.hp = min(self.hp + amount, 40)
            if self.hp > 0:
                self.alive = True
            # Soul Rewinder: give itself +1 Health
            if "self_health" in m.passive:
                gain = m.passive["self_health"] * mult
                m.health += gain
                m.max_health += gain
            # Ashen Corruptor: give shop minions +1/+1 this turn
            if "buff_tavern" in m.passive:
                val = m.passive["buff_tavern"] * mult
                for slot in self.shop:
                    if slot is None or isinstance(slot, dict):
                        continue
                    slot.attack += val
                    slot.health += val
                    slot.max_health += val

    def _on_card_added_to_hand(self, card):
        """Peggy Sturdybone: whenever any card enters hand, buff a random friendly Pirate."""
        for m in self.board:
            if not m.passive:
                continue
            if m.passive.get("type") != "on_card_added_to_hand_buff_pirate":
                continue
            if m is card:
                continue
            mult = 2 if m.golden else 1
            targets = [a for a in self.board if "Pirate" in a.types and a is not m]
            if targets:
                t = random.choice(targets)
                t.attack += m.passive.get("attack", 2) * mult
                hp_val = m.passive.get("health", 1) * mult
                t.health += hp_val
                t.max_health += hp_val

    def _on_hero_damaged(self, amount: int):
        """Verlaagt held-HP (armor eerst) en triggert Floating Watcher passives."""
        armor_absorbed = min(amount, self.armor)
        self.armor -= armor_absorbed
        remaining = amount - armor_absorbed
        actual = min(remaining, self.hp)
        self.hp = max(0, self.hp - remaining)
        if self.hp == 0:
            self.alive = False
        if actual > 0:
            for m in self.board:
                if not m.passive:
                    continue
                ptype = m.passive.get("type")
                mult = 2 if m.golden else 1
                if ptype == "on_hero_damage_buff_self":
                    m.attack += m.passive.get("attack", 2) * mult
                    m.health += m.passive.get("health", 2) * mult
                    m.max_health += m.passive.get("health", 2) * mult
                elif ptype == "on_hero_damage_buff_tribe":
                    tribe = m.passive.get("tribe")
                    atk = m.passive.get("attack", 0) * mult
                    hp = m.passive.get("health", 0) * mult
                    for ally in self.board:
                        if tribe is None or tribe in ally.types:
                            ally.attack += atk
                            ally.health += hp
                            ally.max_health += hp

    def _apply_game_counter_buff(self, minion: Minion):
        """Past historisch geaccumuleerde game-brede teller-buff toe op een nieuwe minion."""
        if not minion.passive:
            return
        ptype = minion.passive.get("type")
        mult = 2 if minion.golden else 1
        if ptype == "has_per_ek_death" and self.eternal_knight_deaths > 0:
            atk = minion.passive.get("attack", 2) * mult * self.eternal_knight_deaths
            hp = minion.passive.get("health", 1) * mult * self.eternal_knight_deaths
            minion.attack += atk; minion.health += hp; minion.max_health += hp
        elif ptype == "has_per_ss_death" and self.sanlayn_scribe_deaths > 0:
            atk = minion.passive.get("attack", 4) * mult * self.sanlayn_scribe_deaths
            hp = minion.passive.get("health", 4) * mult * self.sanlayn_scribe_deaths
            minion.attack += atk; minion.health += hp; minion.max_health += hp
        elif ptype == "has_per_deathrattle_triggered" and self.deathrattles_triggered_game > 0:
            atk = minion.passive.get("attack", 4) * mult * self.deathrattles_triggered_game
            hp = minion.passive.get("health", 2) * mult * self.deathrattles_triggered_game
            minion.attack += atk; minion.health += hp; minion.max_health += hp
        elif ptype == "has_per_spell_cast" and self.spells_cast_game > 0:
            atk = minion.passive.get("attack", 1) * mult * self.spells_cast_game
            hp = minion.passive.get("health", 1) * mult * self.spells_cast_game
            minion.attack += atk; minion.health += hp; minion.max_health += hp

    def _on_game_counter_increment(self, counter: str, amount: int = 1):
        """Verhoogt een game-brede teller en past de bijbehorende buff toe op alle minions."""
        if counter == "eternal_knight_deaths":
            self.eternal_knight_deaths += amount
            ptype, atk_per, hp_per = "has_per_ek_death", 2, 1
        elif counter == "sanlayn_scribe_deaths":
            self.sanlayn_scribe_deaths += amount
            ptype, atk_per, hp_per = "has_per_ss_death", 4, 4
        elif counter == "deathrattles_triggered":
            self.deathrattles_triggered_game += amount
            ptype, atk_per, hp_per = "has_per_deathrattle_triggered", 4, 2
        else:
            return
        for m in self.board:
            if m.passive and m.passive.get("type") == ptype:
                mult = 2 if m.golden else 1
                m.attack += atk_per * mult * amount
                m.health += hp_per * mult * amount
                m.max_health += hp_per * mult * amount
        for m in self.hand:
            if isinstance(m, Minion) and m.passive and m.passive.get("type") == ptype:
                mult = 2 if m.golden else 1
                m.attack += atk_per * mult * amount
                m.health += hp_per * mult * amount
                m.max_health += hp_per * mult * amount

    def _create_blood_gem(self, bonus_keyword: str | None = None, bonus_tribe: str | None = None) -> dict:
        bg: dict = {"type": "blood_gem", "id": "blood_gem", "name": "Blood Gem",
                    "cost": 0, "description": "Geef een minion +1/+1."}
        if bonus_keyword:
            bg["bonus_keyword"] = bonus_keyword
        if bonus_tribe:
            bg["bonus_tribe"] = bonus_tribe
        return bg

    def _apply_blood_gem(self, target: Minion, bonus_keyword: str | None = None,
                         bonus_tribe: str | None = None, _from_bounce: bool = False,
                         _from_hand: bool = False):
        """Past een Blood Gem toe op een minion: +1/+1 + permanente bonussen."""
        target.attack += 1 + self.blood_gem_attack_bonus
        target.health += 1 + self.blood_gem_health_bonus
        target.max_health += 1 + self.blood_gem_health_bonus
        # Defiant Shipwright: wanneer attack omhoog gaat (blood gem geeft altijd +1 atk), ook +1 health
        if target.passive and target.passive.get("type") == "on_attack_gained_health":
                hp_bonus = target.passive.get("health", 1) * (2 if target.golden else 1)
                target.health += hp_bonus
                target.max_health += hp_bonus
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
        # Hot Air Surveyor: blood gem van hand cast een extra keer
        if _from_hand and not _from_bounce:
            extra = sum(
                (2 if m.golden else 1)
                for m in self.board
                if m.passive and m.passive.get("type") == "blood_gem_extra_cast"
            )
            for _ in range(extra):
                self._apply_blood_gem(target, bonus_keyword, bonus_tribe, _from_bounce=True)
        self._check_board_thresholds()

    def _give_random_keyword(self, minion: Minion):
        keywords = ["taunt", "divine_shield", "reborn", "windfury"]
        kw = random.choice(keywords)
        setattr(minion, kw, True)
        if kw not in minion.abilities:
            minion.abilities.append(kw)

    # ── Trofeeën (Trinkets) ─────────────────────────────────
    def acquire_trinket(self, trinket: dict) -> dict:
        """Voeg trofee toe en pas onmiddellijke effecten toe."""
        self.trinkets.append(trinket)
        effect = trinket.get("effect", "")
        # Eénmalige goud-effecten
        if effect == "gain_gold":
            self.gold = min(self.gold + trinket.get("amount", 0), self.MAX_GOLD)
        elif effect == "gain_gold_and_max":
            gain = trinket.get("amount", 0)
            self.gold = min(self.gold + gain, self.MAX_GOLD)
            self.MAX_GOLD += trinket.get("max_bonus", 0)
        # Eénmalige board-buff
        elif effect == "buff_tribe":
            tribe = trinket.get("tribe")
            atk = trinket.get("attack", 0)
            hp  = trinket.get("health", 0)
            for m in self.board:
                if tribe is None or tribe in m.types:
                    m.attack += atk; m.health += hp; m.max_health += hp
        return {"success": True}

    def apply_trinket_start_of_turn(self):
        """Passive trofee-effecten die elke beurt triggeren."""
        for t in self.trinkets:
            effect = t.get("effect", "")
            if effect == "passive_tribe_attack":
                tribe = t.get("tribe")
                bonus = t.get("attack", 0)
                for m in self.board:
                    if tribe is None or tribe in m.types:
                        m.attack = max(m.attack, m.base_attack + bonus)
                        # Store as permanent bonus to survive board changes
            elif effect == "passive_tribe_stats":
                tribe = t.get("tribe")
                atk  = t.get("attack", 0)
                hp   = t.get("health", 0)
                for m in self.board:
                    if tribe is None or tribe in m.types:
                        if not getattr(m, f'_trinket_{t["id"]}_applied', False):
                            m.attack += atk; m.health += hp; m.max_health += hp
                            setattr(m, f'_trinket_{t["id"]}_applied', True)

    # ── Schade ──────────────────────────────────────────────
    def take_damage(self, amount: int):
        armor_absorbed = min(amount, self.armor)
        self.armor -= armor_absorbed
        self.hp = max(0, self.hp - (amount - armor_absorbed))
        if self.hp == 0:
            self.alive = False

    # ── Serialisatie ────────────────────────────────────────
    # ── Magnetic mechanic ────────────────────────────────────
    def magnetize(self, hand_index: int, board_index: int) -> dict:
        """Combineer een Magnetic minion met een compatibel board-doelwit."""
        if hand_index < 0 or hand_index >= len(self.hand):
            return {"success": False, "message": "Invalid hand index."}
        item = self.hand[hand_index]
        if not isinstance(item, Minion) or 'magnetic' not in item.abilities:
            return {"success": False, "message": "Not a Magnetic minion."}
        if board_index < 0 or board_index >= len(self.board):
            return {"success": False, "message": "Invalid board index."}
        target = self.board[board_index]
        mag = item
        if not any(t in target.types for t in mag.types):
            return {"success": False, "message": f"{target.name} is not a valid target."}

        self.hand.pop(hand_index)

        # Stats overnemen
        target.attack += mag.attack
        target.health += mag.health
        target.max_health += mag.health

        # Keywords overnemen (niet overschrijven)
        for kw in ('divine_shield', 'taunt', 'windfury', 'poisonous', 'venomous', 'cleave', 'reborn'):
            if getattr(mag, kw, False) and not getattr(target, kw, False):
                setattr(target, kw, True)
                if kw not in target.abilities:
                    target.abilities.append(kw)

        # Deathrattle overnemen als target er geen heeft
        if mag.deathrattle and not target.deathrattle:
            target.deathrattle = copy.deepcopy(mag.deathrattle)

        # Junk Jouster: Magnetize to self triggers buff all minions
        if target.passive and target.passive.get("type") == "on_magnetized_to_self_buff_all":
            mult = 2 if target.golden else 1
            atk = target.passive.get("attack", 3) * mult
            hp = target.passive.get("health", 2) * mult
            for ally in self.board:
                ally.attack += atk; ally.health += hp; ally.max_health += hp

        # Track total magnetize count for Ingenious Inventor
        self._total_magnetizes = getattr(self, "_total_magnetizes", 0) + 1
        # Apply to any Ingenious Inventor deathrattles on board
        for ally in self.board:
            if ally.deathrattle and ally.deathrattle.get("type") == "buff_all_mechs_attack_combat":
                ally._magnetize_count = getattr(ally, "_magnetize_count", 0) + 1

        return {"success": True, "target": target.to_dict()}

    # ── Pass mechanic ────────────────────────────────────────
    def _free_passes_available(self) -> int:
        total = sum(
            (2 if m.golden else 1)
            for m in self.board
            if m.passive and m.passive.get('type') == 'on_pass_free'
        )
        return max(0, total - self.pass_free_used_this_turn)

    def _update_transport_reactor(self):
        for m in self.board + [x for x in self.hand if isinstance(x, Minion)]:
            if m.passive and m.passive.get('type') == 'transport_reactor_pass_aura':
                mult = 2 if m.golden else 1
                old_bonus = getattr(m, '_tr_applied_bonus', 0)
                new_bonus = self.total_passes_game * mult
                diff = new_bonus - old_bonus
                if diff > 0:
                    m.attack += diff
                    m.health += diff
                    m.max_health += diff
                    m._tr_applied_bonus = new_bonus

    def pass_minion(self, hand_index: int) -> dict:
        if hand_index < 0 or hand_index >= len(self.hand):
            return {"success": False, "message": "Invalid hand index."}

        free = self._free_passes_available() > 0
        cost = 0 if free else 1
        if self.gold < cost:
            return {"success": False, "message": "Not enough gold (Pass costs 1 gold)."}

        item = self.hand.pop(hand_index)
        self.gold -= cost
        if free:
            self.pass_free_used_this_turn += 1

        is_first = self.passes_this_turn == 0
        self.passes_this_turn += 1
        self.total_passes_game += 1

        # Puddle Prancer: buff itself when being Passed
        if isinstance(item, Minion) and item.passive and item.passive.get('type') == 'on_received_buff_self':
            mult = 2 if item.golden else 1
            item.attack += item.passive.get('attack', 4) * mult
            item.health += item.passive.get('health', 4) * mult
            item.max_health += item.passive.get('health', 4) * mult

        # Passenger: first Pass this turn buffs self
        pass_events = []
        if is_first:
            for m in self.board:
                if m.passive and m.passive.get('type') == 'on_pass_buff_self':
                    mult = 2 if m.golden else 1
                    m.attack += m.passive.get('attack', 1) * mult
                    m.health += m.passive.get('health', 2) * mult
                    m.max_health += m.passive.get('health', 2) * mult
                    pass_events.append({'type': 'passenger_buff', 'uid': m.uid,
                                        'attack': m.attack, 'health': m.health})

        # Mantid King: random keyword until next turn
        mantid_events = []
        for m in self.board:
            if m.passive and m.passive.get('type') == 'on_pass_random_keyword':
                old_kw = getattr(m, '_mantid_keyword', None)
                if old_kw:
                    setattr(m, old_kw, False)
                    if old_kw in m.abilities:
                        m.abilities.remove(old_kw)
                kw = random.choice(['venomous', 'taunt', 'divine_shield'])
                m._mantid_keyword = kw
                setattr(m, kw, True)
                if kw not in m.abilities:
                    m.abilities.append(kw)
                mantid_events.append({'type': 'mantid_keyword', 'uid': m.uid, 'keyword': kw})

        # Storm Splitter: get copy of passed spell
        storm_events = []
        if isinstance(item, dict) and item.get('type') == 'spell':
            for m in self.board:
                if (m.passive and m.passive.get('type') == 'on_pass_spell_get_copy'
                        and not getattr(m, '_storm_splitter_used', False)):
                    m._storm_splitter_used = True
                    self.hand.append({**item})
                    storm_events.append({'type': 'storm_splitter', 'uid': m.uid})

        self._update_transport_reactor()

        return {
            "success": True,
            "passed_item": item.to_dict() if isinstance(item, Minion) else item,
            "pass_events": pass_events,
            "mantid_events": mantid_events,
            "storm_events": storm_events,
            "gold": self.gold,
        }

    def to_dict(self, include_shop: bool = False) -> dict:
        d = {
            "sid": self.sid,
            "name": self.name,
            "is_ai": self.is_ai,
            "hp": self.hp,
            "armor": self.armor,
            "tavern_tier": self.tavern_tier,
            "upgrade_cost": self.upgrade_cost,
            "gold": self.gold,
            "board": [m.to_dict() for m in self.board],
            "hand": [(m if isinstance(m, dict) else m.to_dict()) for m in self.hand],
            "frozen": self.frozen,
            "hero": self.hero,
            "ready": self.ready,
            "alive": self.alive,
            "pass_free_available": self._free_passes_available(),
            "passes_this_turn": self.passes_this_turn,
            "total_passes_game": self.total_passes_game,
            "trinkets": self.trinkets,
            "spell_attack_bonus": self.spell_attack_bonus,
            "spell_health_bonus": self.spell_health_bonus,
            "hero_power_used": self._hero_power_used,
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
            "armor": self.armor,
            "tavern_tier": self.tavern_tier,
            "alive": self.alive,
            "hero": self.hero,
            "board_size": len(self.board),
        }
