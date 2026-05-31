from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from game.game_manager import GameManager

app = Flask(__name__)
app.secret_key = "bg-secret-2024"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

manager = GameManager()


@app.route("/")
def index():
    return render_template("index.html")


# ── Lobby events ─────────────────────────────────────────────────────────────

@socketio.on("create_lobby")
def on_create_lobby(data):
    name = data.get("player_name", "Speler").strip() or "Speler"
    room_code = manager.create_lobby(request.sid, name)
    join_room(room_code)
    emit("lobby_created", {"room_code": room_code})
    emit("lobby_update", manager.get_lobby_state(room_code), to=room_code)


@socketio.on("join_lobby")
def on_join_lobby(data):
    name = data.get("player_name", "Speler").strip() or "Speler"
    room_code = data.get("room_code", "").upper().strip()
    result = manager.join_lobby(request.sid, room_code, name)
    if result["success"]:
        join_room(room_code)
        emit("joined_lobby", {"room_code": room_code})
        emit("lobby_update", manager.get_lobby_state(room_code), to=room_code)
    else:
        emit("error", {"message": result["message"]})


@socketio.on("start_game")
def on_start_game(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.start_game(request.sid, room_code)
    if not result["success"]:
        emit("error", {"message": result["message"]})
        return

    game = manager.get_game(room_code)
    # Stuur hero keuze naar elke menselijke speler
    for sid, player in game.players.items():
        if not player.is_ai:
            socketio.emit("hero_selection", {
                "heroes": player.hero_options,
                "timeout": game.HERO_SELECT_TIMER,
            }, to=sid)


@socketio.on("select_hero")
def on_select_hero(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.select_hero(request.sid, room_code, data.get("hero_id"))
    emit("hero_selected", {"hero_id": data.get("hero_id")})

    if result["all_selected"]:
        _start_round(room_code)


# ── Shop events ──────────────────────────────────────────────────────────────

@socketio.on("buy_minion")
def on_buy_minion(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.buy_minion(request.sid, room_code, data.get("shop_index", 0), data.get("target_index"))
    if result["success"]:
        emit("player_update", result["player"])
        if result.get("triple"):
            emit("triple_discover", {
                "golden": result["triple"]["golden"],
                "options": result["triple"].get("discover_options", []),
            })
        for pass_info in result.get("mirror_monster_passes", []):
            socketio.emit("player_update", pass_info["player"], to=pass_info["sid"])
    else:
        emit("error", {"message": result.get("message", "Kan niet kopen.")})


@socketio.on("choose_discover")
def on_choose_discover(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.choose_discover(request.sid, room_code, data.get("minion_id"))
    if result["success"]:
        emit("player_update", result["player"])


@socketio.on("sell_minion")
def on_sell_minion(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.sell_minion(request.sid, room_code, data.get("board_index", 0))
    if result["success"]:
        emit("player_update", result["player"])
        if result.get("pass_recipient"):
            socketio.emit("player_update", result["pass_recipient"]["player"],
                          to=result["pass_recipient"]["sid"])
    else:
        emit("error", {"message": result.get("message", "Kan niet verkopen.")})


@socketio.on("magnetize")
def on_magnetize(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.magnetize(
        request.sid, room_code,
        data.get("hand_index", 0), data.get("board_index", 0)
    )
    if result["success"]:
        emit("player_update", result["player"])
    else:
        emit("error", {"message": result.get("message", "Kan niet magnetizen.")})


@socketio.on("pass_minion")
def on_pass_minion(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.pass_minion(request.sid, room_code, data.get("hand_index", 0))
    if result["success"]:
        emit("player_update", result["player"])
        if result.get("pass_recipient"):
            socketio.emit("player_update", result["pass_recipient"]["player"],
                          to=result["pass_recipient"]["sid"])
    else:
        emit("error", {"message": result.get("message", "Kan niet passen.")})


@socketio.on("reroll")
def on_reroll(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.reroll(request.sid, room_code)
    if result["success"]:
        emit("player_update", result["player"])
    else:
        emit("error", {"message": result.get("message", "Niet genoeg goud.")})


@socketio.on("freeze")
def on_freeze(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.freeze(request.sid, room_code)
    emit("freeze_update", {"frozen": result["frozen"]})


@socketio.on("upgrade_tavern")
def on_upgrade_tavern(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.upgrade_tavern(request.sid, room_code)
    if result["success"]:
        emit("player_update", result["player"])
    else:
        emit("error", {"message": result.get("message", "Kan niet upgraden.")})


@socketio.on("play_from_hand")
def on_play_from_hand(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.play_from_hand(
        request.sid, room_code,
        data.get("hand_index", 0), data.get("board_index", -1)
    )
    if result["success"]:
        emit("player_update", result["player"])
        if result.get("battlecry_discover"):
            emit("triple_discover", {"options": result["battlecry_discover"]})
    else:
        emit("error", {"message": result.get("message", "Kan niet spelen.")})


@socketio.on("sell_from_hand")
def on_sell_from_hand(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.sell_from_hand(
        request.sid, room_code, data.get("hand_index", 0)
    )
    if result["success"]:
        emit("player_update", result["player"])
    else:
        emit("error", {"message": result.get("message", "Kan niet verkopen.")})


@socketio.on("move_minion")
def on_move_minion(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.move_minion(
        request.sid, room_code,
        data.get("from_index", 0), data.get("to_index", 0)
    )
    if result["success"]:
        emit("board_update", {"board": result["board"]})


@socketio.on("use_hero_power")
def on_use_hero_power(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.use_hero_power(request.sid, room_code, data.get("target_index"))
    if result["success"]:
        emit("player_update", result["player"])
    else:
        emit("error", {"message": result.get("message", "Held-spreuk mislukt.")})


@socketio.on("player_ready")
def on_player_ready(data):
    room_code = manager.get_player_room(request.sid)
    if not room_code:
        return
    result = manager.player_ready(request.sid, room_code)
    # Stuur bijgewerkte state terug als end-of-turn effecten zijn gevuurd
    if result.get("player"):
        emit("player_update", result["player"])
    ready_count = manager.get_ready_count(room_code)
    emit("ready_update", ready_count, to=room_code)

    if result["all_ready"]:
        _do_combat(room_code)


# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def _start_round(room_code: str):
    game = manager.get_game(room_code)
    if not game:
        return
    game.start_round()
    for sid, player in game.players.items():
        if not player.is_ai and player.alive:
            socketio.emit("round_start", game.get_round_data_for(sid), to=sid)
    # Stuur opponents info naar alle spelers
    socketio.emit("opponents_update", game.get_all_players_public(), to=room_code)


def _do_combat(room_code: str):
    game = manager.get_game(room_code)
    if not game:
        return

    socketio.emit("combat_starting", {}, to=room_code)
    combat_results = manager.resolve_combat(room_code)

    # Stuur combat replay naar elke speler
    for sid, result in combat_results.items():
        player = game.players.get(sid)
        if player and not player.is_ai:
            socketio.emit("combat_result", result, to=sid)

    # Eliminations
    eliminated = game.get_eliminations()
    if eliminated:
        socketio.emit("eliminations", {"players": eliminated}, to=room_code)

    # Game over check
    if game.is_game_over():
        winner = game.get_winner()
        socketio.emit("game_over", {"winner": winner}, to=room_code)
        return

    # Volgende ronde na korte pauze (combat replay tijd)
    def next_round():
        import gevent
        gevent.sleep(15)  # Geef clients tijd voor combat replay
        if room_code in manager.rooms:
            _start_round(room_code)

    import gevent
    gevent.spawn(next_round)


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_code = manager.get_player_room(sid)
    if room_code:
        manager.remove_player(sid)
        state = manager.get_lobby_state(room_code)
        if state:
            emit("lobby_update", state, to=room_code)


if __name__ == "__main__":
    print("Battlegrounds server start op http://localhost:5000")
    socketio.run(app, debug=True, port=5000, host="0.0.0.0")
