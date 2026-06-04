import random
import time
from game.player import Player
from game.shop import ShopManager
from game.combat import simulate_combat, calculate_damage
from game.data.trinkets import TRINKETS
from game.matchmaking import make_matchups
from game.data.heroes import HEROES_LIST
from game.minion import Minion
from game.data.spells import SPELLS_BY_TIER

_SPELLS_FLAT = {s["id"]: s for tier_spells in SPELLS_BY_TIER.values() for s in tier_spells}
_BOUNTY_SPELLS = [s for s in _SPELLS_FLAT.values() if "bounty" in s["id"]]


def _apply_hero_combat_auras(board: list, enemy_board: list, hero: dict | None):
    """Applies hero passives at start of combat on the (already cloned) combat board."""
    if not hero:
        return
    from game.minion import Minion as _M
    effect = hero.get("ability", {}).get("effect")
    ab = hero.get("ability", {})

    if effect == "all_will_burn":
        bonus = ab.get("attack", 2)
        for m in board + enemy_board:
            m.attack += bonus

    elif effect == "wingmen":
        atk = ab.get("attack", 2)
        hp  = ab.get("health", 1)
        if board:
            board[0].attack += atk
            board[0].health += hp
            board[0].max_health += hp
            if len(board) > 1:
                board[-1].attack += atk
                board[-1].health += hp
                board[-1].max_health += hp

    elif effect == "alakir_start_of_combat":
        # Al'Akir: left-most minion gets Windfury + Divine Shield + Taunt
        if board:
            m = board[0]
            m.windfury = True; m.divine_shield = True; m.taunt = True
            for kw in ("windfury", "divine_shield", "taunt"):
                if kw not in m.abilities:
                    m.abilities.append(kw)

    elif effect == "wax_warband":
        # Queen Wagtoggle: give a friendly minion of each TYPE +1/+1
        atk = ab.get("attack", 1); hp = ab.get("health", 1)
        seen_types: set = set()
        for m in board:
            for t in m.types:
                if t not in seen_types:
                    seen_types.add(t)
                    m.attack += atk; m.health += hp; m.max_health += hp
                    break
        if not any(m.types for m in board):  # no typed minions: buff first
            if board:
                board[0].attack += atk; board[0].health += hp; board[0].max_health += hp

    elif effect == "fragrant_phylactery":
        # Tamsin Roame: lowest-attack minion gets Deathrattle: give other minions its stats
        alive = [m for m in board if not m.dead]
        if alive:
            lowest = min(alive, key=lambda m: m.attack)
            lowest.deathrattle = {"type": "give_stats_to_others"}
            if "deathrattle" not in lowest.abilities:
                lowest.abilities.append("deathrattle")

    elif effect == "tentacular":
        # Ozumat: when there's space, summon a 2/2 Tentacle with Taunt
        if len(board) < 7:
            tentacle = _M.from_id("tentacle")
            board.append(tentacle)

    elif effect == "sprout_it_out":
        # Greybough passive: tracked at combat time via a flag
        # Stored on hero so summon handlers can reference it
        pass  # handled in _summon_token in combat.py via hero check

    elif effect == "broodmother":
        # Onyxia: Avenge (N): summon 1/1 Whelp that attacks immediately
        # This is tracked per combat as a hero-level avenge
        pass  # handled in _process_deaths

    elif effect == "ozumat_tentacle":
        pass  # alias handled above


def _apply_post_combat_rewards(player: Player, rewards: list):
    from game.data.minions import MINIONS
    for reward in rewards:
        rtype = reward.get("type")

        if rtype == "add_spell_post_combat":
            spell_id = reward.get("spell")
            spell = _SPELLS_FLAT.get(spell_id)
            if spell:
                player.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 3)})

        elif rtype == "give_random_bounty_post_combat":
            if _BOUNTY_SPELLS:
                spell = random.choice(_BOUNTY_SPELLS)
                player.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 2)})

        elif rtype == "give_random_chromadrake_post_combat":
            pool = [m for mid, m in MINIONS.items() if "chromadrake" in mid]
            if pool:
                data = random.choice(pool)
                player.hand.append(Minion.from_id(data["id"]))

        elif rtype == "give_random_magnetic_mech_post_combat":
            pool = [m for m in MINIONS.values() if "Mech" in m.get("types", [])]
            if pool:
                data = random.choice(pool)
                player.hand.append(Minion.from_id(data["id"]))

        elif rtype == "free_refreshes_post_combat":
            player.free_refreshes_available += reward.get("count", 1)

        elif rtype == "spell_discount_post_combat":
            player.next_spell_discount += 1

        elif rtype == "buff_random_hand":
            minions_in_hand = [m for m in player.hand if isinstance(m, Minion)]
            if minions_in_hand:
                target = random.choice(minions_in_hand)
                target.attack += reward.get("attack", 5)
                target.health += reward.get("health", 5)
                target.max_health += reward.get("health", 5)

        elif rtype == "give_blood_gems_post_combat":
            count = reward.get("count", 1) * (2 if reward.get("golden") else 1)
            kw = reward.get("bonus_keyword")
            tribe = reward.get("bonus_tribe")
            for _ in range(count):
                player.hand.append(player._create_blood_gem(kw, tribe))

        elif rtype == "blood_gem_attack_bonus_post_combat":
            amount = reward.get("amount", 1) * (2 if reward.get("golden") else 1)
            player.blood_gem_attack_bonus += amount

        elif rtype == "blood_gem_adjacent_post_combat":
            pass  # skulking_bristlemane: combat-positie niet beschikbaar post-combat

        elif rtype == "blood_gems_tribe_post_combat":
            tribe = reward.get("tribe")
            count = reward.get("count", 1) * (2 if reward.get("golden") else 1)
            for m in player.board:
                if tribe is None or tribe in m.types:
                    for _ in range(count):
                        player._apply_blood_gem(m)

        elif rtype == "avenge_chromadrake":
            count = 2 if reward.get("golden") else 1
            pool = [m for mid, m in MINIONS.items() if "chromadrake" in mid]
            for _ in range(count):
                if pool:
                    data = random.choice(pool)
                    player.hand.append(Minion.from_id(data["id"]))

        elif rtype == "avenge_spell":
            spell_id = reward.get("spell")
            spell = _SPELLS_FLAT.get(spell_id)
            count = 2 if reward.get("golden") else 1
            if spell:
                for _ in range(count):
                    player.hand.append({**spell, "type": "spell", "cost": spell.get("cost", 3)})

        elif rtype == "avenge_blood_gem_bonus":
            amount = reward.get("amount", 1) * (2 if reward.get("golden") else 1)
            stat = reward.get("stat", "health")
            if stat == "health":
                player.blood_gem_health_bonus += amount
            else:
                player.blood_gem_attack_bonus += amount

        elif rtype == "avenge_get_undead":
            count = 2 if reward.get("golden") else 1
            pool = [m for m in MINIONS.values() if "Undead" in m.get("types", [])]
            for _ in range(count):
                if pool:
                    data = random.choice(pool)
                    player.hand.append(Minion.from_id(data["id"]))

        elif rtype == "avenge_teammate_minion":
            pass  # Solos: geen teammate

        elif rtype == "reduce_upgrade_cost":
            amount = reward.get("amount", 1) * (2 if reward.get("golden") else 1)
            player.upgrade_cost = max(0, player.upgrade_cost - amount)

        elif rtype == "rally_buff_tribe_permanent":
            tribe = reward.get("tribe")
            atk = reward.get("attack", 0)
            hp = reward.get("health", 0)
            for m in player.board:
                if tribe is None or tribe in m.types:
                    m.attack += atk; m.health += hp; m.max_health += hp
            for m in player.hand:
                if isinstance(m, Minion) and (tribe is None or tribe in m.types):
                    m.attack += atk; m.health += hp; m.max_health += hp

        elif rtype == "rally_chefs_choice":
            tribes = reward.get("tribes", [])
            if tribes:
                tribe = random.choice(tribes)
                pool = [m for m in MINIONS.values() if tribe in m.get("types", [])]
                if pool:
                    player.hand.append(Minion.from_id(random.choice(pool)["id"]))

        elif rtype == "eternal_knight_died":
            player._on_game_counter_increment("eternal_knight_deaths", 1)

        elif rtype == "sanlayn_scribe_died":
            player._on_game_counter_increment("sanlayn_scribe_deaths", 1)

        elif rtype == "deathrattle_triggered_game":
            player._on_game_counter_increment("deathrattles_triggered", 1)

        elif rtype == "old_soul_deaths":
            count = reward.get("count", 0)
            for m in player.hand:
                if isinstance(m, Minion) and m.id == "old_soul" and not m.golden:
                    m._death_count = getattr(m, "_death_count", 0) + count
                    if m._death_count >= 15:
                        m.make_golden()
                        m._death_count = 0

        elif rtype == "waveling_refresh_hook":
            mult = 2 if reward.get("golden") else 1
            player._waveling_refresh_hooks += mult

        elif rtype == "buff_tavern_tribe_post_combat":
            # Dancing Barnstormer deathrattle: buff tribe in shop permanently
            tribe = reward.get("tribe")
            atk = reward.get("attack", 8)
            hp = reward.get("health", 8)
            for slot in player.shop:
                if slot is None or isinstance(slot, dict):
                    continue
                if tribe is None or tribe in slot.types:
                    slot.attack += atk
                    slot.health += hp
                    slot.max_health += hp

        elif rtype == "rokara_kill_buff":
            # Rokara (glory_of_combat): +1 Attack to the killing minion permanently
            if player.hero and player.hero.get("ability", {}).get("effect") == "glory_of_combat":
                uid = reward.get("uid")
                atk = reward.get("attack", 1)
                real_m = next((m for m in player.board if m.uid == uid), None)
                if real_m:
                    real_m.attack += atk

        elif rtype == "ill_take_that":
            # Rafaam: get a plain copy of the first enemy you killed
            if player.hero and player.hero.get("ability", {}).get("effect") == "ill_take_that":
                from game.minion import Minion as _M2
                from game.data.minions import ALL_MINIONS as _AM
                mid = reward.get("minion_id")
                if mid and mid in _AM:
                    player.hand.append(_M2.from_id(mid))

        elif rtype == "add_random_tier_spell_post_combat":
            from game.data.spells import SPELLS_BY_TIER as _SBT
            tier = reward.get("tier", 1)
            pool = _SBT.get(tier, [])
            if pool:
                spell = random.choice(pool)
                player.hand.append({**spell, "type": "spell", "cost": spell.get("cost", tier)})

        elif rtype == "get_random_battlecry_post_combat":
            from game.data.minions import MINIONS as _MINS
            pool = [m for m in _MINS.values()
                    if m.get("battlecry") and not m.get("removed") and not m.get("duo_only")]
            if pool:
                data = random.choice(pool)
                player.hand.append(Minion.from_id(data["id"]))

        elif rtype == "buff_token_post_combat":
            token_id = reward.get("token")
            atk = reward.get("attack", 0)
            hp = reward.get("health", 0)
            for m in player.board:
                if m.id == token_id:
                    m.attack += atk; m.health += hp; m.max_health += hp
            for item in player.hand:
                if isinstance(item, Minion) and item.id == token_id:
                    item.attack += atk; item.health += hp; item.max_health += hp
            # Store permanent bonus for future tokens
            key = f"_token_buff_{token_id}"
            existing = getattr(player, key, {"attack": 0, "health": 0})
            setattr(player, key, {"attack": existing["attack"] + atk,
                                  "health": existing["health"] + hp})

        elif rtype == "spread_stegodon_rally":
            tribe = reward.get("tribe")
            atk = reward.get("attack", 0)
            spread_rally = {"type": "buff_tribe_all", "tribe": tribe, "attack": atk, "health": 0}
            for m in player.board:
                if tribe is None or tribe in m.types:
                    m.rally = spread_rally
            for m in player.hand:
                if isinstance(m, Minion) and (tribe is None or tribe in m.types):
                    m.rally = spread_rally


AI_NAMES = [
    "Rexxar", "Jaina", "Thrall", "Anduin", "Sylvanas",
    "Malfurion", "Valeera", "Garrosh",
]


class GameState:
    # Shop timer: ronde 1 = 60s, +15s per ronde, max 120s (officiële BG-regels)
    HERO_SELECT_TIMER = 30

    @staticmethod
    def shop_timer_for_round(round_num: int) -> int:
        return min(60 + (round_num - 1) * 15, 120)

    def __init__(self, room_code: str):
        self.room_code = room_code
        self.players: dict[str, Player] = {}  # {sid: Player}
        self.state = "lobby"  # lobby | hero_selection | round | game_over
        self.round_num = 0
        self.shop_manager = ShopManager()
        self.ghost_boards: dict[str, list[dict]] = {}  # boards van uitgeschakelde spelers
        self.round_start_time: float = 0
        self.host_sid: str | None = None

    # ── Spelers beheer ───────────────────────────────────────
    def add_player(self, sid: str, name: str) -> Player:
        p = Player(sid, name)
        self.players[sid] = p
        if self.host_sid is None:
            self.host_sid = sid
        return p

    def remove_player(self, sid: str):
        if sid in self.players:
            del self.players[sid]
        if self.host_sid == sid:
            remaining = list(self.players.keys())
            self.host_sid = remaining[0] if remaining else None

    def fill_with_bots(self, target: int = 8):
        current = len(self.players)
        ai_names = list(AI_NAMES)
        random.shuffle(ai_names)
        for i in range(target - current):
            fake_sid = f"bot_{i}_{random.randint(1000,9999)}"
            name = ai_names[i % len(ai_names)]
            p = Player(fake_sid, name, is_ai=True)
            self.players[fake_sid] = p

    # ── Hero selectie ────────────────────────────────────────
    def start_hero_selection(self):
        self.state = "hero_selection"
        hero_pool = [h for h in HEROES_LIST if not h.get("duo_only", False)]
        random.shuffle(hero_pool)
        for p in self.players.values():
            options = random.sample(hero_pool, min(3, len(hero_pool)))
            p.hero_options = options
            if p.is_ai:
                hero = random.choice(options)
                p.hero = hero
                p.hp = hero.get("hp_override", 30)
                p.armor = hero.get("armor", 0)

    def select_hero(self, sid: str, hero_id: str) -> bool:
        p = self.players.get(sid)
        if not p:
            return False
        hero = next((h for h in p.hero_options if h["id"] == hero_id), None)
        if hero:
            p.hero = hero
            p.hp = hero.get("hp_override", 30)
            p.armor = hero.get("armor", 0)
            if hero["id"] == "the_lich_king":
                p.double_deathrattle = True
            if hero["id"] == "dinotamer_brann":
                p.double_battlecry = True
            # Start-of-game passives
            self._apply_hero_start_of_game(p, hero)
        return self._all_heroes_selected()

    def _apply_hero_start_of_game(self, p: "Player", hero: dict):
        """Apply one-time start-of-game hero passives after hero selection."""
        effect = hero.get("ability", {}).get("effect")
        if effect == "menagerist":
            # The Curator: start with a 2/2 Amalgam with Venomous + all types
            p.board.append(Minion.from_id("amalgam"))
        elif effect == "pilot_the_shredder":
            # Sneed: start with a 2/1 Shredder (simplified: 2/1 Mech)
            from game.data.minions import ALL_MINIONS as _AM
            if "shredder" in _AM:
                p.board.append(Minion.from_id("shredder"))
            else:
                shred = Minion.from_id("microbot")
                shred.name = "Shredder"; shred.attack = 2; shred.health = 1
                shred.max_health = 1
                p.board.append(shred)
        elif effect == "avatar_of_nzoth":
            # N'Zoth: start with a 2/2 Fish (simplified token)
            fish = Minion.from_id("microbot")
            fish.name = "Fish of N'Zoth"; fish.attack = 2; fish.health = 2
            fish.max_health = 2
            p.board.append(fish)
        elif effect == "skycapn_kragg":
            # Skycap'n Kragg: gain 2 Gold once per game (handled as bonus_gold next turn)
            p.gold_next_turn_bonus += hero.get("ability", {}).get("piggy_bank_amount", 2)

    def _all_heroes_selected(self) -> bool:
        return all(p.hero is not None for p in self.players.values())

    # ── Ronde beheer ─────────────────────────────────────────
    def start_round(self):
        self.round_num += 1
        self.state = "round"
        self.round_start_time = time.time()

        for p in self.players.values():
            if not p.alive:
                continue
            p.start_turn(self.round_num)
            if not p.frozen:
                self.shop_manager.return_shop_to_pool(p.shop)
                p.shop = self.shop_manager.generate_shop(p.tavern_tier, p.hero)
            else:
                p.frozen = False

            # Sindragosa: auto-freeze at end-of-turn (handled here as start of NEXT turn)
            if getattr(p, "_sindragosa_freeze_eot", False):
                p._sindragosa_freeze_eot = False
                p.frozen = True  # will freeze the newly generated shop

            if p.is_ai:
                self._ai_take_turn(p)

    def get_round_data_for(self, sid: str) -> dict:
        p = self.players[sid]
        data = {
            "round_num": self.round_num,
            "player": p.to_dict(include_shop=True),
            "opponents": [op.public_dict() for op in self.players.values() if op.sid != sid],
            "timer": self.shop_timer_for_round(self.round_num),
        }
        if p.pending_egg_hatch is not None:
            from game.data.minions import MINIONS
            t6_dragons = [m for m in MINIONS.values() if m.get("tier") == 6 and "Dragon" in m.get("types", [])]
            chosen = random.sample(t6_dragons, min(3, len(t6_dragons)))
            is_golden = p.pending_egg_hatch.golden
            data["egg_hatch_options"] = [{"id": m["id"], "name": m["name"],
                                           "attack": (m.get("attack") or 0) * (2 if is_golden else 1),
                                           "health": (m.get("health") or 0) * (2 if is_golden else 1),
                                           "golden": is_golden,
                                           "description": m.get("golden_description" if is_golden else "description", ""),
                                           "abilities": m.get("abilities", [])} for m in chosen]
        # Trinket aanbod op ronde 6 (Lesser) en ronde 9 (Greater)
        trinket_offer = self.get_trinket_offer_for(sid)
        if trinket_offer:
            data["trinket_offer"] = trinket_offer
        return data

    # ── Shop acties ─────────────────────────────────────────
    def buy_minion(self, sid: str, shop_index: int, target_index: int | None = None) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False, "message": "Player not found."}
        result = p.buy_minion(shop_index, target_index)
        if result.get("triple"):
            tier = result["triple"].get("discover_tier", p.tavern_tier)
            result["triple"]["discover_options"] = self._discover_options(tier)
        if result.get("success"):
            bought_passive = (result.get("minion") or {}).get("passive") or {}
            if bought_passive.get("type") == "on_buy_copy_and_pass":
                self._handle_mirror_monster(sid, result)
        return result

    def _discover_options(self, tier: int) -> list:
        from game.data.minions import MINIONS
        candidates = [m for m in MINIONS.values()
                      if m["tier"] <= tier
                      and not m.get("removed", False)
                      and not m.get("duo_only", False)]
        if not candidates:
            candidates = [m for m in MINIONS.values()
                          if not m.get("removed", False) and not m.get("duo_only", False)]
        chosen = random.sample(candidates, min(3, len(candidates)))
        return [{
            "id": m["id"], "name": m["name"], "tier": m["tier"],
            "attack": m["attack"], "health": m["health"],
            "tribe": m.get("tribe"), "description": m.get("description", ""),
            "abilities": m.get("abilities", []),
            "taunt": "taunt" in m.get("abilities", []),
            "divine_shield": "divine_shield" in m.get("abilities", []),
            "reborn": "reborn" in m.get("abilities", []),
            "poisonous": "poisonous" in m.get("abilities", []),
            "windfury": "windfury" in m.get("abilities", []),
            "cleave": "cleave" in m.get("abilities", []),
            "golden": False, "uid": id(m),
        } for m in chosen]

    def choose_discover(self, sid: str, minion_id: str) -> dict:
        p = self.players.get(sid)
        if not p:
            return {"success": False}
        p.add_discover_minion(minion_id)
        result = {"success": True, "player": p.to_dict(include_shop=True)}
        from game.data.minions import ALL_MINIONS
        discovered_passive = ALL_MINIONS.get(minion_id, {}).get("passive") or {}
        if discovered_passive.get("type") == "on_buy_copy_and_pass":
            self._handle_mirror_monster(sid, result)
        return result

    def magnetize(self, sid: str, hand_index: int, board_index: int) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False}
        return p.magnetize(hand_index, board_index)

    def _route_pass(self, sid: str, minion_dict: dict, result: dict):
        """Stuur een minion-dict naar een willekeurige tegenstander en schrijf pass_recipient in result."""
        opponents = [op for op in self.players.values() if op.sid != sid and op.alive]
        if not opponents:
            return
        recipient = random.choice(opponents)
        m = Minion.from_dict(minion_dict)
        recipient.hand.append(m)
        result["pass_recipient"] = {
            "sid": recipient.sid,
            "player": recipient.to_dict(include_shop=True),
        }

    def _handle_mirror_monster(self, sid: str, result: dict):
        """Mirror Monster: pass 1 (of 2 bij golden) kopieën naar tegenstanders."""
        bought = result.get("minion") or {}
        is_golden = bought.get("golden", False)
        copies = 2 if is_golden else 1
        opponents = [op for op in self.players.values() if op.sid != sid and op.alive]
        if not opponents:
            return
        recipients = []
        for _ in range(copies):
            recipient = random.choice(opponents)
            copy = Minion.from_id("mirror_monster")
            recipient.hand.append(copy)
            recipients.append({"sid": recipient.sid, "player": recipient.to_dict(include_shop=True)})
        result["mirror_monster_passes"] = recipients

    def pass_minion(self, sid: str, hand_index: int) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False, "message": "Player not found."}
        result = p.pass_minion(hand_index)
        if not result["success"]:
            return result
        self._route_pass(sid, result["passed_item"], result)
        return result

    def sell_minion(self, sid: str, board_index: int) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False, "message": "Player not found."}
        result = p.sell_minion(board_index)
        # Return sold minion to pool so the shop doesn't deplete over rounds
        sold = result.get("sold")
        if sold:
            from game.minion import Minion as _M
            try:
                self.shop_manager.return_to_pool(_M.from_dict(sold))
            except Exception:
                pass
        sp = result.get("sell_passive") or {}
        if isinstance(sp, dict) and sp.get("type") == "sell_then_pass":
            self._route_pass(sid, sp["minion"], result)
        return result

    def reroll(self, sid: str) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False}
        result = p.reroll()
        if result["success"]:
            self.shop_manager.return_shop_to_pool(p.shop)
            p.shop = self.shop_manager.generate_shop(p.tavern_tier, p.hero)
            # Infinite Toki: vervang 2 random slots door hogere-tier kaarten
            if getattr(p, "_temporal_tavern_bonus", False):
                p._temporal_tavern_bonus = False
                higher_tier = min(p.tavern_tier + 1, 6)
                from game.data.minions import MINIONS as _MINS
                import random as _r
                higher_pool = [mid for mid, d in _MINS.items() if d["tier"] == higher_tier]
                if higher_pool:
                    slots = [i for i, m in enumerate(p.shop)
                             if m is not None and not isinstance(m, dict)]
                    for i in _r.sample(slots, min(2, len(slots))):
                        p.shop[i] = Minion.from_id(_r.choice(higher_pool))
            # Laboratory Assistant Fodder: inject into shop
            if p._fodder_refreshes_remaining > 0:
                fodder = Minion.from_id("fodder")
                p._fodder_refreshes_remaining -= 1
                # If Demon on board, it consumes the Fodder immediately (no slot needed)
                demons = [m for m in p.board if "Demon" in m.types]
                if demons:
                    consumer = random.choice(demons)
                    consumer.attack += fodder.attack
                    consumer.health += fodder.health
                    consumer.max_health += fodder.health
                else:
                    # No Demon available: add Fodder to shop as a normal card
                    p.shop.append(fodder)
            # Waveling: buff a random shop minion (+3/+3 per hook)
            if p._waveling_refresh_hooks > 0:
                shop_minions = [m for m in p.shop if m is not None and not isinstance(m, dict)]
                if shop_minions:
                    target = random.choice(shop_minions)
                    target.attack += 3 * p._waveling_refresh_hooks
                    target.health += 3 * p._waveling_refresh_hooks
                    target.max_health += 3 * p._waveling_refresh_hooks

            # Ysera (dream_portal): add an extra Dragon to the shop
            if p.hero and p.hero.get("ability", {}).get("effect") == "dream_portal":
                from game.data.minions import MINIONS as _MINS2
                dragon_pool = [mid for mid, d in _MINS2.items()
                               if "Dragon" in d.get("types", []) and d["tier"] <= p.tavern_tier
                               and not d.get("removed") and self.shop_manager.pool.get(mid, 0) > 0]
                if dragon_pool:
                    chosen_id = random.choice(dragon_pool)
                    if self.shop_manager.take_from_pool(chosen_id):
                        p.shop.append(Minion.from_id(chosen_id))

            # Overlord Saurfang (for_the_horde): shop minions get +X/+X
            if p.hero and p.hero.get("ability", {}).get("effect") == "for_the_horde":
                bonus = getattr(p, "_saurfang_shop_bonus", 1)
                for slot in p.shop:
                    if slot is not None and not isinstance(slot, dict):
                        slot.attack += bonus; slot.health += bonus; slot.max_health += bonus

            # Enhance-o Mechano (enhancification): give a random shop minion a random keyword
            if p.hero and p.hero.get("ability", {}).get("effect") == "enhancification":
                shop_m = [m for m in p.shop if m is not None and not isinstance(m, dict)]
                if shop_m:
                    t = random.choice(shop_m)
                    kw = random.choice(["divine_shield", "taunt", "windfury", "reborn", "poisonous"])
                    setattr(t, kw, True)
                    if kw not in t.abilities:
                        t.abilities.append(kw)

            # Varden Dawngrasp (twice_as_nice): copy highest-tier shop minion and freeze
            if p.hero and p.hero.get("ability", {}).get("effect") == "twice_as_nice":
                shop_m = [m for m in p.shop if m is not None and not isinstance(m, dict)]
                if shop_m:
                    highest = max(shop_m, key=lambda m: m.tier)
                    copy = highest.clone()
                    p.shop.append(copy)
                    p.frozen = True  # freeze the shop

        return {**result, "shop": [(m if isinstance(m, dict) else m.to_dict()) if m else None for m in p.shop]}

    def freeze(self, sid: str) -> dict:
        p = self.players.get(sid)
        if not p:
            return {"success": False}
        return p.toggle_freeze()

    def upgrade_tavern(self, sid: str) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False}
        return p.upgrade_tavern()

    def play_from_hand(self, sid: str, hand_index: int, board_index: int = -1) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False}
        result = p.play_from_hand(hand_index, board_index)
        # Battlecry discover: genereer opties als de battlecry dat vraagt
        bc = result.get("battlecry") or {}
        if isinstance(bc, dict) and "discover_options" in bc:
            result["battlecry_discover"] = bc["discover_options"]
        # Well Wisher spellcraft: route pending pass to a random opponent
        pending = getattr(p, "_pending_well_wisher_pass", None)
        if pending:
            p._pending_well_wisher_pass = None
            self._route_pass(sid, pending, result)
        return result

    def apply_choose_one(self, sid: str, choice: int) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False}
        result = p.apply_choose_one(choice)
        result["player"] = p.to_dict()
        return result

    def sell_from_hand(self, sid: str, hand_index: int) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False}
        result = p.sell_from_hand(hand_index)
        sold = result.get("sold")
        if sold:
            from game.minion import Minion as _M
            try:
                self.shop_manager.return_to_pool(_M.from_dict(sold))
            except Exception:
                pass
        return result

    # ── Trofeeën (Trinkets) ──────────────────────────────────
    TRINKET_ROUNDS = {6: "lesser", 9: "greater"}

    def _trinket_options_for_player(self, p: "Player", grade: str) -> list[dict]:
        """Genereer 4 trofee-opties; filter al bezeten IDs."""
        owned_ids = {t["id"] for t in p.trinkets}
        all_t = list(TRINKETS.values())
        # Eenvoudige lesser/greater scheiding: ID's met _1 = lesser, _2 = greater, rest middenmoot
        if grade == "lesser":
            pool = [t for t in all_t if not t["id"].endswith("_2") and t["id"] not in owned_ids]
        else:
            pool = [t for t in all_t if not t["id"].endswith("_1") and t["id"] not in owned_ids]
        if not pool:
            pool = [t for t in all_t if t["id"] not in owned_ids]
        return random.sample(pool, min(4, len(pool)))

    def get_trinket_offer_for(self, sid: str) -> dict | None:
        """Geeft trinket-aanbod als dit een trinket-ronde is, anders None."""
        grade = self.TRINKET_ROUNDS.get(self.round_num)
        if not grade:
            return None
        p = self.players.get(sid)
        if not p or not p.alive:
            return None
        options = self._trinket_options_for_player(p, grade)
        return {"grade": grade, "options": options}

    def select_trinket(self, sid: str, trinket_id: str) -> dict:
        p = self.players.get(sid)
        if not p:
            return {"success": False}
        trinket = TRINKETS.get(trinket_id)
        if not trinket:
            return {"success": False, "message": "Unknown trinket."}
        result = p.acquire_trinket(trinket)
        out = {"success": True, "player": p.to_dict(include_shop=True)}
        # Trinket discover: generate options and return them
        td = result.get("trinket_discover")
        if td:
            tier = td.get("tier", 6)
            count = td.get("count", 1)
            all_opts = []
            for _ in range(count):
                all_opts.append(self._discover_options(tier))
            out["trinket_discover"] = all_opts[0] if count == 1 else all_opts
        return out

    def move_minion(self, sid: str, from_idx: int, to_idx: int) -> dict:
        p = self.players.get(sid)
        if not p:
            return {"success": False}
        return p.move_minion(from_idx, to_idx)

    def use_hero_power(self, sid: str, target_index: int | None = None) -> dict:
        p = self.players.get(sid)
        if not p:
            return {"success": False}
        return p.use_hero_power(target_index)

    def player_ready(self, sid: str) -> dict:
        p = self.players.get(sid)
        eot_events = []
        if p:
            p.ready = True
            eot_events = p.trigger_end_of_turn()
        alive = [pl for pl in self.players.values() if pl.alive]
        all_ready = all(pl.ready or pl.is_ai for pl in alive)
        result: dict = {"all_ready": all_ready, "eot_events": eot_events}
        if p:
            result["player"] = p.to_dict(include_shop=True)
        return result

    # ── Combat ───────────────────────────────────────────────
    def resolve_combat(self) -> dict[str, dict]:
        alive_sids = [sid for sid, p in self.players.items() if p.alive and not p.is_ai]
        matchups = make_matchups(alive_sids, self.ghost_boards)

        results: dict[str, dict] = {}
        processed_pairs: set[frozenset] = set()

        # Verwerk ook AI spelers
        all_alive = [sid for sid, p in self.players.items() if p.alive]
        ai_sids = [sid for sid in all_alive if self.players[sid].is_ai]
        for ai_sid in ai_sids:
            opponents = [s for s in all_alive if s != ai_sid]
            if opponents:
                matchups[ai_sid] = random.choice(opponents)

        for p_sid, opp_ref in matchups.items():
            player = self.players.get(p_sid)
            if not player or not player.alive:
                continue

            pair_key = frozenset([p_sid, opp_ref if not opp_ref.startswith("ghost:") else opp_ref])

            # Haal tegenstander board op
            if opp_ref.startswith("ghost:"):
                ghost_key = opp_ref[6:]
                enemy_dicts = self.ghost_boards.get(ghost_key, [])
                enemy_board = [Minion.from_dict(d) for d in enemy_dicts]
                opp_name = f"Ghost van {ghost_key}"
                opp_tavern = 1
            else:
                opp = self.players.get(opp_ref)
                if not opp:
                    continue
                enemy_board = [m.clone() for m in opp.board]
                opp_name = opp.name
                opp_tavern = opp.tavern_tier
                # Flighty Scout van tegenstander: voeg kopie toe aan vijandelijk board
                for item in opp.hand:
                    if isinstance(item, Minion) and item.id == "flighty_scout" and len(enemy_board) < opp.MAX_BOARD:
                        scout = item.clone()
                        if item.golden:
                            scout.attack *= 2; scout.health *= 2; scout.max_health *= 2
                        enemy_board.append(scout)

            # Maelstrom Emergent: extra cast count
            maelstrom_extras = sum(
                (m.passive.get("extra", 1) * (2 if m.golden else 1))
                for m in player.board
                if m.passive and m.passive.get("type") == "double_combat_spells"
            )
            # Pas uitgestelde spreuk-effecten toe op vijandelijk board
            spell_list = player.pending_combat_spells * (1 + maelstrom_extras)
            for spell_id in spell_list:
                if spell_id == "corrupted_cupcakes":
                    for m in enemy_board:
                        m.attack = max(0, m.attack - 2)
                elif spell_id == "hired_headhunter":
                    if enemy_board:
                        enemy_board.pop(random.randrange(len(enemy_board)))
            player.pending_combat_spells.clear()

            # Clone board voor combat (muteert nooit het echte board)
            combat_board = [m.clone() for m in player.board]

            # Flighty Scout: voor elke kopie in hand, voeg een kopie toe aan combat board
            for item in player.hand:
                if isinstance(item, Minion) and item.id == "flighty_scout" and len(combat_board) < player.MAX_BOARD:
                    scout = item.clone()
                    if item.golden:
                        scout.attack *= 2; scout.health *= 2; scout.max_health *= 2
                    combat_board.append(scout)

            # Hero passives at combat start (op de clone, niet het echte board)
            _apply_hero_combat_auras(combat_board, enemy_board, player.hero)

            # Expert Aviator: rally — buff linker handminion permanent + summon als tijdelijk combat-minion
            for ci, cm in enumerate(combat_board):
                if cm.rally and cm.rally.get("type") == "summon_leftmost_hand":
                    hand_minions = [item for item in player.hand if isinstance(item, Minion)]
                    if hand_minions and len(combat_board) < player.MAX_BOARD:
                        leftmost = hand_minions[0]
                        mult = 2 if cm.golden else 1
                        atk_buff = cm.rally.get("attack", 1) * mult
                        hp_buff = cm.rally.get("health", 1) * mult
                        leftmost.attack += atk_buff
                        leftmost.health += hp_buff
                        leftmost.max_health += hp_buff
                        combat_board.append(leftmost.clone())

            # Diremuck Forager: SoC give a random hand minion +2/+2 then summon for combat
            for item in player.hand:
                if isinstance(item, Minion) and item.id == "diremuck_forager" and item in player.board:
                    pass  # Forager must be on board to trigger
            for cm in combat_board:
                if cm.id == "diremuck_forager":
                    mult = 2 if cm.golden else 1
                    hand_minions = [item for item in player.hand if isinstance(item, Minion)]
                    if hand_minions and len(combat_board) < player.MAX_BOARD:
                        chosen = random.choice(hand_minions)
                        chosen.attack += 2 * mult; chosen.health += 2 * mult; chosen.max_health += 2 * mult
                        combat_board.append(chosen.clone())
                    break

            # Choral Mrrrglr: SoC gain stats of all hand minions
            for cm in combat_board:
                if cm.id == "choral_mrrrglr":
                    mult = 2 if cm.golden else 1
                    for item in player.hand:
                        if isinstance(item, Minion):
                            cm.attack += item.attack * mult
                            cm.health += item.health * mult
                            cm.max_health += item.health * mult
                    break

            # Tarecgosa / persistent_poet: snapshot stats na hero-aura, voor combat
            preserve_uids: set[str] = set()
            for ci, cm in enumerate(combat_board):
                if cm.id == "tarecgosa":
                    preserve_uids.add(cm.uid)
                elif cm.id == "persistent_poet":
                    for adj_i in [ci - 1, ci + 1]:
                        if 0 <= adj_i < len(combat_board):
                            adj = combat_board[adj_i]
                            if "Dragon" in adj.types:
                                preserve_uids.add(adj.uid)
            pre_combat_stats = {cm.uid: {"attack": cm.attack, "health": cm.health,
                                         "abilities": list(cm.abilities)}
                                for cm in combat_board if cm.uid in preserve_uids}

            # Simuleer gevecht
            result = simulate_combat(combat_board, enemy_board)

            # Pas post-combat beloningen toe
            _apply_post_combat_rewards(player, result["post_combat_rewards"]["player"])

            # Old Soul: telt vriendelijke sterfgevallen terwijl het in hand zit
            initial_board_size = len(combat_board)
            player_survivors = len(result.get("surviving_minions", [])) if result.get("winner") == "player" else 0
            deaths_this_combat = max(0, initial_board_size - player_survivors)
            for item in player.hand:
                if isinstance(item, Minion) and item.id == "old_soul":
                    item._old_soul_deaths = getattr(item, "_old_soul_deaths", 0) + deaths_this_combat
                    target = item.passive.get("target", 15) if item.passive else 15
                    if item._old_soul_deaths >= target and not item.golden:
                        item.make_golden()
                        item._old_soul_deaths = 0
                    break

            # Tarecgosa / persistent_poet: bewaar combat-gewonnen stats/keywords op echte board
            if preserve_uids:
                for survivor_d in result["surviving_minions"]:
                    uid = survivor_d.get("uid")
                    if uid not in preserve_uids:
                        continue
                    real_m = next((m for m in player.board if m.uid == uid), None)
                    pre = pre_combat_stats.get(uid)
                    if real_m is None or pre is None:
                        continue
                    delta_atk = max(0, survivor_d.get("attack", 0) - pre["attack"])
                    delta_hp = max(0, survivor_d.get("health", 0) - pre["health"])
                    if delta_atk:
                        real_m.attack += delta_atk
                    if delta_hp:
                        real_m.health += delta_hp
                        real_m.max_health += delta_hp
                    for ability in survivor_d.get("abilities", []):
                        if ability not in pre["abilities"] and ability not in real_m.abilities:
                            real_m.abilities.append(ability)
                    if survivor_d.get("divine_shield") and not real_m.divine_shield:
                        real_m.divine_shield = True
                    if survivor_d.get("windfury") and not real_m.windfury:
                        real_m.windfury = True
                    if survivor_d.get("megawindfury") and not real_m.megawindfury:
                        real_m.megawindfury = True
                    if survivor_d.get("poisonous") and not real_m.poisonous:
                        real_m.poisonous = True
                    if survivor_d.get("venomous") and not real_m.venomous:
                        real_m.venomous = True
            if not opp_ref.startswith("ghost:"):
                opp_obj = self.players.get(opp_ref)
                if opp_obj:
                    _apply_post_combat_rewards(opp_obj, result["post_combat_rewards"]["enemy"])

            # Bereken schade
            damage_to_player = 0
            damage_to_opp = 0

            if result["winner"] == "player":
                survivor_minions = [Minion.from_dict(d) for d in result["surviving_minions"]]
                damage_to_opp = calculate_damage(survivor_minions, player.tavern_tier)
                if not opp_ref.startswith("ghost:"):
                    opp_obj = self.players.get(opp_ref)
                    if opp_obj:
                        opp_obj.take_damage(damage_to_opp)
            elif result["winner"] == "enemy":
                survivor_minions = [Minion.from_dict(d) for d in result["surviving_minions"]]
                damage_to_player = calculate_damage(survivor_minions, opp_tavern)
                player.take_damage(damage_to_player)

            your_result = result["winner"] if result["winner"] in ("tie",) else \
                ("won" if result["winner"] == "player" else "lost")
            player.last_combat_lost = (your_result == "lost")

            results[p_sid] = {
                "opponent_name": opp_name,
                "your_result": your_result,
                "damage_received": damage_to_player,
                "damage_dealt": damage_to_opp,
                "steps": result["steps"],
                "player_board": [m.to_dict() for m in player.board],
                "enemy_board": [m.to_dict() for m in enemy_board],
                "surviving_minions": result["surviving_minions"],
            }

            # Spiegel resultaat voor tegenstander (als het een echte speler is)
            if not opp_ref.startswith("ghost:") and opp_ref not in results:
                mirror_steps = _mirror_steps(result["steps"])
                results[opp_ref] = {
                    "opponent_name": player.name,
                    "your_result": "won" if your_result == "lost" else ("lost" if your_result == "won" else "tie"),
                    "damage_received": damage_to_opp,
                    "damage_dealt": damage_to_player,
                    "steps": mirror_steps,
                    "player_board": [m.to_dict() for m in enemy_board],
                    "enemy_board": [m.to_dict() for m in player.board],
                    "surviving_minions": result["surviving_minions"] if result["winner"] == "enemy" else [],
                }

        # Sla ghost boards op van uitgeschakelde spelers
        for sid, p in self.players.items():
            if not p.alive and p.board:
                self.ghost_boards[p.name] = [m.to_dict() for m in p.board]

        return results

    def get_eliminations(self) -> list[str]:
        return [p.name for p in self.players.values() if not p.alive]

    def is_game_over(self) -> bool:
        alive = [p for p in self.players.values() if p.alive]
        return len(alive) <= 1

    def get_winner(self) -> str | None:
        alive = [p for p in self.players.values() if p.alive]
        return alive[0].name if len(alive) == 1 else None

    def get_all_players_public(self) -> list[dict]:
        return [p.public_dict() for p in self.players.values()]

    # ── AI logica ────────────────────────────────────────────
    def _ai_take_turn(self, p: Player):
        # Probeer tavern te upgraden als genoeg goud
        if p.gold >= p.upgrade_cost + 3 and p.tavern_tier < 6:
            p.upgrade_tavern()

        # Koop zolang mogelijk
        for _ in range(10):
            shop_minions = [(i, m) for i, m in enumerate(p.shop) if m is not None]
            if not shop_minions or not p.can_buy():
                break
            idx, _ = random.choice(shop_minions)
            result = p.buy_minion(idx)
            if not result["success"]:
                break

        # Speel alle hand-kaarten naar het board
        while p.hand and len(p.board) < p.MAX_BOARD:
            p.play_from_hand(0)

        p.ready = True


def _mirror_steps(steps: list[dict]) -> list[dict]:
    """Spiegelt combat steps: player ↔ enemy voor de andere speler."""
    import copy
    mirrored = []
    for step in copy.deepcopy(steps):
        if step.get("type") == "attack":
            if step["attacker_side"] == "player":
                step["attacker_side"] = "enemy"
            else:
                step["attacker_side"] = "player"
        elif step.get("type") == "death":
            if step.get("side") == "player":
                step["side"] = "enemy"
            else:
                step["side"] = "player"
        mirrored.append(step)
    return mirrored
