import random
import string
from game.game_state import GameState


class GameManager:
    MAX_PLAYERS_PER_ROOM = 8

    def __init__(self):
        self.rooms: dict[str, GameState] = {}
        self.sid_to_room: dict[str, str] = {}

    # ── Lobby beheer ─────────────────────────────────────────
    def create_lobby(self, sid: str, player_name: str) -> str:
        room_code = self._generate_code()
        game = GameState(room_code)
        game.add_player(sid, player_name)
        self.rooms[room_code] = game
        self.sid_to_room[sid] = room_code
        return room_code

    def join_lobby(self, sid: str, room_code: str, player_name: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False, "message": f"Kamer '{room_code}' bestaat niet."}
        if game.state != "lobby":
            return {"success": False, "message": "Het spel is al begonnen."}
        if len(game.players) >= self.MAX_PLAYERS_PER_ROOM:
            return {"success": False, "message": "Kamer is vol (max 8 spelers)."}
        game.add_player(sid, player_name)
        self.sid_to_room[sid] = room_code
        return {"success": True, "room_code": room_code}

    def get_lobby_state(self, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {}
        return {
            "room_code": room_code,
            "players": [
                {"sid": sid, "name": p.name, "is_host": (sid == game.host_sid)}
                for sid, p in game.players.items()
                if not p.is_ai
            ],
            "host_sid": game.host_sid,
            "state": game.state,
        }

    def start_game(self, sid: str, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False, "message": "Kamer niet gevonden."}
        if game.host_sid != sid:
            return {"success": False, "message": "Alleen de host kan het spel starten."}
        if len(game.players) < 1:
            return {"success": False, "message": "Er is minimaal 1 speler nodig."}

        # Vul op met AI bots tot 8
        game.fill_with_bots(8)
        game.start_hero_selection()
        return {"success": True}

    # ── Game acties ─────────────────────────────────────────
    def select_hero(self, sid: str, room_code: str, hero_id: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False, "all_selected": False}
        all_selected = game.select_hero(sid, hero_id)
        return {"success": True, "all_selected": all_selected}

    def buy_minion(self, sid: str, room_code: str, shop_index: int, target_index: int | None = None) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.buy_minion(sid, shop_index, target_index)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def sell_minion(self, sid: str, room_code: str, board_index: int) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.sell_minion(sid, board_index)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def choose_discover(self, sid: str, room_code: str, minion_id: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        return game.choose_discover(sid, minion_id)

    def reroll(self, sid: str, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.reroll(sid)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def freeze(self, sid: str, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        return game.freeze(sid)

    def upgrade_tavern(self, sid: str, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.upgrade_tavern(sid)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def play_from_hand(self, sid: str, room_code: str, hand_index: int, board_index: int = -1) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.play_from_hand(sid, hand_index, board_index)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def sell_from_hand(self, sid: str, room_code: str, hand_index: int) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.sell_from_hand(sid, hand_index)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def pass_minion(self, sid: str, room_code: str, hand_index: int) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.pass_minion(sid, hand_index)
        if result.get("success"):
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def move_minion(self, sid: str, room_code: str, from_idx: int, to_idx: int) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.move_minion(sid, from_idx, to_idx)
        if result["success"]:
            p = game.players[sid]
            result["board"] = [m.to_dict() for m in p.board]
        return result

    def use_hero_power(self, sid: str, room_code: str, target_index: int | None = None) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"success": False}
        result = game.use_hero_power(sid, target_index)
        if result["success"]:
            p = game.players[sid]
            result["player"] = p.to_dict(include_shop=True)
        return result

    def player_ready(self, sid: str, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"all_ready": False}
        return game.player_ready(sid)

    def resolve_combat(self, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {}
        return game.resolve_combat()

    def get_ready_count(self, room_code: str) -> dict:
        game = self.rooms.get(room_code)
        if not game:
            return {"ready": 0, "total": 0}
        alive = [p for p in game.players.values() if p.alive and not p.is_ai]
        ready = [p for p in alive if p.ready]
        return {"ready": len(ready), "total": len(alive)}

    # ── Navigatie ───────────────────────────────────────────
    def get_game(self, room_code: str) -> GameState | None:
        return self.rooms.get(room_code)

    def get_player_room(self, sid: str) -> str | None:
        return self.sid_to_room.get(sid)

    def remove_player(self, sid: str):
        room_code = self.sid_to_room.pop(sid, None)
        if room_code and room_code in self.rooms:
            self.rooms[room_code].remove_player(sid)
            if not self.rooms[room_code].players:
                del self.rooms[room_code]

    # ── Hulpfuncties ────────────────────────────────────────
    def _generate_code(self, length: int = 4) -> str:
        while True:
            code = "".join(random.choices(string.ascii_uppercase, k=length))
            if code not in self.rooms:
                return code
