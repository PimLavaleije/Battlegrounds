import random
from game.minion import Minion
from game.data.heroes import HEROES_LIST


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
        self.double_battlecry = False  # Brann
        self.double_deathrattle = False  # Baron / Lich King
        self.hand: list[Minion] = []

    # ── Turn setup ──────────────────────────────────────────
    def start_turn(self, round_num: int):
        self.gold = min(3 + round_num - 1, self.MAX_GOLD)
        self.ready = False
        # Upgrade kost daalt elke ronde (min 0)
        if self.upgrade_cost > 0:
            self.upgrade_cost = max(0, self.upgrade_cost - 1)
        # Pas hero-passief toe
        self._apply_start_of_round_hero()

    def _apply_start_of_round_hero(self):
        # Passive start-of-round effects go here as they are implemented.
        pass

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

        # George the Fallen: give a target minion Divine Shield
        if effect == "give_divine_shield" and self.board and target_index is not None:
            if 0 <= target_index < len(self.board):
                self.board[target_index].divine_shield = True
                return {"success": True, "effect": "divine_shield", "target": self.board[target_index].to_dict()}

        return {"success": True}

    # ── Shop acties ─────────────────────────────────────────
    def can_buy(self) -> bool:
        return self.gold >= 3 and len(self.hand) < 10

    def buy_minion(self, shop_index: int) -> dict:
        if shop_index < 0 or shop_index >= len(self.shop):
            return {"success": False, "message": "Ongeldige winkel-index."}
        minion = self.shop[shop_index]
        if minion is None:
            return {"success": False, "message": "Geen minion op die plek."}
        if not self.can_buy():
            return {"success": False, "message": "Kan niet kopen: vol board of te weinig goud."}

        self.shop[shop_index] = None
        self.gold -= 3
        self.hand.append(minion)

        # Triple check
        triple_result = self._track_triple(minion)

        # Battlecry
        battlecry_result = None
        if minion.battlecry:
            battlecry_result = self._apply_battlecry(minion)
            if self.double_battlecry and battlecry_result:
                self._apply_battlecry(minion)

        # Yogg-Saron is now a passive (puzzle_box) — no longer triggers on buy

        # Shop-event passives (wrath_weaver, deflect_o_bot, blazing_skyfin, kalecgos)
        passive_events = self._trigger_buy_passives(minion)

        return {
            "success": True,
            "minion": minion.to_dict(),
            "triple": triple_result,
            "battlecry": battlecry_result,
            "passive_events": passive_events,
        }

    def sell_minion(self, board_index: int) -> dict:
        if board_index < 0 or board_index >= len(self.board):
            return {"success": False, "message": "Ongeldige board-index."}
        minion = self.board.pop(board_index)
        self.gold = min(self.gold + 1, self.MAX_GOLD)
        self._remove_from_triple(minion)
        self._recalculate_board_passives()
        sell_passive = self._trigger_sell_passive(minion)
        return {"success": True, "gold": self.gold, "sold": minion.to_dict(), "sell_passive": sell_passive}

    def reroll(self) -> dict:
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
        if len(self.board) >= self.MAX_BOARD:
            return {"success": False, "message": "Board is vol (max 7)."}
        minion = self.hand.pop(hand_index)
        if 0 <= board_index < len(self.board):
            self.board.insert(board_index, minion)
        else:
            self.board.append(minion)
        self._recalculate_board_passives()
        return {"success": True}

    def sell_from_hand(self, hand_index: int) -> dict:
        if hand_index < 0 or hand_index >= len(self.hand):
            return {"success": False, "message": "Ongeldige hand-index."}
        minion = self.hand.pop(hand_index)
        self.gold = min(self.gold + 1, self.MAX_GOLD)
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
        return None

    def _trigger_buy_passives(self, bought: Minion) -> list[dict]:
        events = []
        for m in self.board:
            if not m.passive:
                continue
            ptype = m.passive.get("type")

            if ptype == "on_demon_bought" and "Demon" in bought.types:
                m.attack += m.passive.get("attack", 2)
                m.health += m.passive.get("health", 1)
                m.max_health += m.passive.get("health", 1)
                dmg = m.passive.get("self_damage", 1)
                self.hp = max(0, self.hp - dmg)
                if self.hp == 0:
                    self.alive = False
                events.append({"type": "buy_passive", "uid": m.uid, "attack": m.attack, "health": m.health, "self_damage": dmg})

            elif ptype == "on_mech_bought" and "Mech" in bought.types:
                m.attack += m.passive.get("attack", 2)
                m.divine_shield = True
                if "divine_shield" not in m.abilities:
                    m.abilities.append("divine_shield")
                events.append({"type": "buy_passive", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "on_battlecry_self" and (bought.battlecry or "battlecry" in bought.abilities):
                m.attack += m.passive.get("attack", 1)
                m.health += m.passive.get("health", 1)
                m.max_health += m.passive.get("health", 1)
                events.append({"type": "buy_passive", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "on_battlecry_tribe" and (bought.battlecry or "battlecry" in bought.abilities):
                tribe = m.passive.get("tribe")
                for ally in self.board:
                    if tribe in ally.types:
                        ally.attack += m.passive.get("attack", 1)
                        ally.health += m.passive.get("health", 1)
                        ally.max_health += m.passive.get("health", 1)
                        events.append({"type": "buy_passive", "uid": ally.uid, "attack": ally.attack, "health": ally.health})
        return events

    def _trigger_sell_passive(self, sold: Minion) -> dict | None:
        if not sold.passive:
            return None
        ptype = sold.passive.get("type")
        if ptype == "on_sell_self":
            token_id = sold.passive.get("token")
            if not token_id:
                return None
            token = Minion.from_id(token_id)
            for i, slot in enumerate(self.shop):
                if slot is None:
                    self.shop[i] = token
                    break
            else:
                self.shop.append(token)
            return {"added_to_shop": token.to_dict()}
        return None

    def _recalculate_board_passives(self):
        """Herbereken board-brede passieve effecten (bijv. Brann op board = double battlecry)."""
        self.double_battlecry = (
            any(m.id == "brann_bronzebeard" for m in self.board)
            or self.hero is not None and self.hero.get("ability", {}).get("effect") == "double_battlecry"
        )

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
            "hand": [m.to_dict() for m in self.hand],
            "frozen": self.frozen,
            "hero": self.hero,
            "ready": self.ready,
            "alive": self.alive,
        }
        if include_shop:
            d["shop"] = [m.to_dict() if m else None for m in self.shop]
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
