import random
import time
from game.player import Player
from game.shop import ShopManager
from game.combat import simulate_combat, calculate_damage
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


AI_NAMES = [
    "Rexxar", "Jaina", "Thrall", "Anduin", "Sylvanas",
    "Malfurion", "Valeera", "Garrosh",
]


class GameState:
    SHOP_TIMER = 45  # seconden
    HERO_SELECT_TIMER = 30

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
        hero_pool = list(HEROES_LIST)
        random.shuffle(hero_pool)
        for p in self.players.values():
            options = random.sample(hero_pool, min(3, len(hero_pool)))
            p.hero_options = options
            if p.is_ai:
                p.hero = random.choice(options)

    def select_hero(self, sid: str, hero_id: str) -> bool:
        p = self.players.get(sid)
        if not p:
            return False
        hero = next((h for h in p.hero_options if h["id"] == hero_id), None)
        if hero:
            p.hero = hero
            if hero["id"] == "the_lich_king":
                p.double_deathrattle = True
            if hero["id"] == "dinotamer_brann":
                p.double_battlecry = True
        return self._all_heroes_selected()

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
                p.frozen = False  # Bevroren shop blijft, maar unfreeze voor volgende ronde

            if p.is_ai:
                self._ai_take_turn(p)

    def get_round_data_for(self, sid: str) -> dict:
        p = self.players[sid]
        data = {
            "round_num": self.round_num,
            "player": p.to_dict(include_shop=True),
            "opponents": [op.public_dict() for op in self.players.values() if op.sid != sid],
            "timer": self.SHOP_TIMER,
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
        return data

    # ── Shop acties ─────────────────────────────────────────
    def buy_minion(self, sid: str, shop_index: int, target_index: int | None = None) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False, "message": "Speler niet gevonden."}
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
        candidates = [m for m in MINIONS.values() if m["tier"] == tier]
        if not candidates:
            candidates = list(MINIONS.values())
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
            return {"success": False, "message": "Speler niet gevonden."}
        result = p.pass_minion(hand_index)
        if not result["success"]:
            return result
        self._route_pass(sid, result["passed_item"], result)
        return result

    def sell_minion(self, sid: str, board_index: int) -> dict:
        p = self.players.get(sid)
        if not p or not p.alive:
            return {"success": False, "message": "Speler niet gevonden."}
        result = p.sell_minion(board_index)
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
        return p.sell_from_hand(hand_index)

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

            # Pas uitgestelde spreuk-effecten toe op vijandelijk board
            for spell_id in player.pending_combat_spells:
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
