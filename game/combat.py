import random
import copy
from game.minion import Minion
from game.data.minions import MINIONS, ALL_MINIONS


def simulate_combat(player_board: list[Minion], enemy_board: list[Minion]) -> dict:
    """
    Simuleert auto-battle tussen twee boards.
    Geeft een dict terug met steps (voor frontend replay) en de winnaar.
    """
    p_board = [m.clone() for m in player_board]
    e_board = [m.clone() for m in enemy_board]

    steps = []
    p_atk_idx = 0
    e_atk_idx = 0
    current_side = 0  # 0 = speler valt aan, 1 = vijand valt aan
    safety = 0

    # Bepaal wie begint: meer minions gaat eerst; gelijkspel = muntopgooi
    if len(e_board) > len(p_board):
        current_side = 1
    elif len(e_board) == len(p_board):
        current_side = random.randint(0, 1)

    _apply_combat_auras(p_board)
    _apply_combat_auras(e_board)

    while p_board and e_board and safety < 150:
        safety += 1

        if current_side == 0:
            attacker_board = p_board
            defender_board = e_board
            side_name = "player"
            atk_idx = p_atk_idx % len(p_board)
        else:
            attacker_board = e_board
            defender_board = p_board
            side_name = "enemy"
            atk_idx = e_atk_idx % len(e_board)

        attacker = attacker_board[atk_idx]

        # Kies doelwit
        target, target_idx = _choose_target(attacker, defender_board)
        if target is None:
            break

        # Mega-windfury (golden windfury) = 4x, gewone windfury = 2x, anders 1x
        attacks = 4 if attacker.megawindfury else (2 if attacker.windfury else 1)
        for _ in range(attacks):
            if not p_board or not e_board:
                break
            step = _do_attack(attacker, target, target_idx, side_name,
                              atk_idx, p_board, e_board, current_side)
            steps.append(step)

            # Na aanval doden verwerken
            deaths = _collect_deaths(p_board, e_board)
            if deaths:
                death_step = _process_deaths(deaths, p_board, e_board, steps)
                if death_step:
                    steps.extend(death_step)
            p_board = [m for m in p_board if not m.dead]
            e_board = [m for m in e_board if not m.dead]

            if not p_board or not e_board:
                break

            # Ververs board-referenties zodat cleave-indexen en target-keuze kloppen
            if current_side == 0:
                attacker_board = p_board
                defender_board = e_board
            else:
                attacker_board = e_board
                defender_board = p_board

            # Herkies doelwit voor volgende aanval (windfury / mega-windfury)
            if attacker.dead:
                break
            target, target_idx = _choose_target(attacker, defender_board)
            if target is None:
                break

        # Volgende aanvaller
        if current_side == 0:
            p_atk_idx = (p_atk_idx + 1) % max(len(p_board), 1)
        else:
            e_atk_idx = (e_atk_idx + 1) % max(len(e_board), 1)

        current_side = 1 - current_side

    # Bepaal winnaar
    if p_board and not e_board:
        winner = "player"
        survivors = p_board
    elif e_board and not p_board:
        winner = "enemy"
        survivors = e_board
    else:
        winner = "tie"
        survivors = []

    return {
        "steps": steps,
        "winner": winner,
        "surviving_minions": [m.to_dict() for m in survivors],
    }


def _choose_target(attacker: Minion, defender_board: list[Minion]) -> tuple[Minion | None, int]:
    alive = [(i, m) for i, m in enumerate(defender_board) if not m.dead]
    if not alive:
        return None, -1

    # Zapp valt laagste aanval aan
    if attacker.zapp:
        alive.sort(key=lambda x: x[1].attack)
        return alive[0][1], alive[0][0]

    # Taunt targets
    taunt_targets = [(i, m) for i, m in alive if m.taunt]
    if taunt_targets:
        chosen = random.choice(taunt_targets)
    else:
        chosen = random.choice(alive)
    return chosen[1], chosen[0]


def _do_attack(attacker: Minion, target: Minion, target_idx: int,
               side_name: str, atk_idx: int,
               p_board: list, e_board: list, current_side: int) -> dict:
    step = {
        "type": "attack",
        "attacker_side": side_name,
        "attacker_idx": atk_idx,
        "attacker_uid": attacker.uid,
        "target_uid": target.uid,
        "target_idx": target_idx,
        "attacker_name": attacker.name,
        "target_name": target.name,
        "attacker_attack": attacker.attack,
        "target_attack": target.attack,
        "events": [],
    }

    # Schade aan doelwit
    result_t = target.take_damage(attacker.attack if not attacker.poisonous else 9999)
    step["target_damage"] = result_t["damage"]
    step["target_shield_broken"] = result_t.get("shield_broken", False)

    # Hardy Orca: als doelwit schade ontvangt, buff alle andere vrienden op verdedigend bord
    defender_board_ref = e_board if current_side == 0 else p_board
    if not result_t.get("shielded") and result_t.get("damage", 0) > 0:
        if target.passive and target.passive.get("type") == "on_self_damaged":
            _trigger_self_damaged_passive(target, defender_board_ref, step)

    # Tegenslag
    result_a = attacker.take_damage(target.attack if not target.poisonous else 9999)
    step["attacker_damage"] = result_a["damage"]
    step["attacker_shield_broken"] = result_a.get("shield_broken", False)

    # Hardy Orca: als aanvaller zelf schade ontvangt
    attacker_board_ref = p_board if current_side == 0 else e_board
    if not result_a.get("shielded") and result_a.get("damage", 0) > 0:
        if attacker.passive and attacker.passive.get("type") == "on_self_damaged":
            _trigger_self_damaged_passive(attacker, attacker_board_ref, step)

    # Bolvar / Drakonid: schild doorbroken passief
    defender_board = e_board if current_side == 0 else p_board
    attacker_board = p_board if current_side == 0 else e_board

    if result_t.get("shield_broken"):
        _trigger_shield_pop_passives(target, attacker_board, step)
    if result_a.get("shield_broken"):
        _trigger_shield_pop_passives(attacker, attacker_board, step)

    # Cleave (aangrenzende minions ontvangen ook schade; poisonous geldt ook)
    if attacker.cleave:
        adj = _get_adjacent(target_idx, defender_board)
        for adj_m in adj:
            cleave_dmg = 9999 if attacker.poisonous else attacker.attack
            adj_result = adj_m.take_damage(cleave_dmg)
            step["events"].append({
                "type": "cleave_damage",
                "target_uid": adj_m.uid,
                "damage": adj_result["damage"],
            })

    return step


def _get_adjacent(idx: int, board: list[Minion]) -> list[Minion]:
    adj = []
    if idx > 0:
        adj.append(board[idx - 1])
    if idx < len(board) - 1:
        adj.append(board[idx + 1])
    return adj


def _collect_deaths(p_board: list[Minion], e_board: list[Minion]) -> list[tuple[Minion, str]]:
    deaths = []
    for m in p_board:
        if m.is_dead() and not m.dead:
            m.dead = True
            deaths.append((m, "player"))
    for m in e_board:
        if m.is_dead() and not m.dead:
            m.dead = True
            deaths.append((m, "enemy"))
    return deaths


def _process_deaths(deaths: list, p_board: list[Minion], e_board: list[Minion], all_steps: list) -> list[dict]:
    result_steps = []

    for dead_minion, dead_side in deaths:
        death_step = {
            "type": "death",
            "side": dead_side,
            "uid": dead_minion.uid,
            "name": dead_minion.name,
            "events": [],
        }

        friendly_board = p_board if dead_side == "player" else e_board
        enemy_board = e_board if dead_side == "player" else p_board

        # Passive triggers op vriendelijke minions
        for m in friendly_board:
            if m.dead:
                continue
            if not m.passive:
                continue
            ptype = m.passive.get("type")

            if ptype == "beast_dies_buff" and dead_minion.tribe == "Beast":
                m.attack += m.passive.get("attack", 0)
                m.health += m.passive.get("health", 0)
                death_step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "mech_dies_buff" and dead_minion.tribe == "Mech":
                m.attack += m.passive.get("attack", 0)
                m.health += m.passive.get("health", 0)
                death_step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "demon_dies_damage" and dead_minion.tribe == "Demon":
                # Deal schade aan willekeurige vijand
                alive_enemies = [e for e in enemy_board if not e.dead]
                if alive_enemies:
                    target = random.choice(alive_enemies)
                    target.take_damage(m.passive.get("amount", 3))
                    death_step["events"].append({"type": "soul_juggler", "target_uid": target.uid})

        # Deathrattle
        if dead_minion.deathrattle:
            dr = dead_minion.deathrattle
            # Baron Rivendare check
            has_baron = any(m.id == "baron_rivendare" and not m.dead for m in friendly_board)
            triggers = 2 if has_baron else 1

            for _ in range(triggers):
                _apply_deathrattle(dead_minion, dr, friendly_board, enemy_board, death_step)

        # Reborn
        if dead_minion.reborn and not dead_minion.reborn_used:
            dead_minion.reborn_used = True
            if len(friendly_board) < 7:
                reborn_copy = dead_minion.clone()
                # Sinrunner Blanchy herrijst met volle HP
                full_hp = dead_minion.passive and dead_minion.passive.get("type") == "full_health_reborn"
                reborn_copy.health = reborn_copy.max_health if full_hp else 1
                reborn_copy.dead = False
                reborn_copy.reborn = False
                friendly_board.append(reborn_copy)
                death_step["events"].append({"type": "reborn", "uid": reborn_copy.uid, "name": reborn_copy.name})

        result_steps.append(death_step)

    return result_steps


def _apply_deathrattle(dead: Minion, dr: dict, friendly_board: list, enemy_board: list, step: dict):
    dtype = dr.get("type")

    if dtype == "summon" and len(friendly_board) < 7:
        token_id = dr["token"]
        from game.minion import Minion as M
        token = M.from_id(token_id)
        friendly_board.append(token)
        step["events"].append({"type": "summon", "token": token.to_dict()})
        _trigger_pack_leader(token, friendly_board, step)

    elif dtype == "summon_two":
        for _ in range(2):
            if len(friendly_board) >= 7:
                break
            from game.minion import Minion as M
            token = M.from_id(dr["token"])
            friendly_board.append(token)
            step["events"].append({"type": "summon", "token": token.to_dict()})
            _trigger_pack_leader(token, friendly_board, step)

    elif dtype == "give_attack_random":
        alive = [m for m in friendly_board if not m.dead and m is not dead]
        if alive:
            target = random.choice(alive)
            target.attack += dead.attack
            step["events"].append({"type": "buff", "uid": target.uid, "attack": target.attack, "health": target.health})

    elif dtype == "deal_damage_all":
        amount = dr.get("amount", 1)
        for m in friendly_board + enemy_board:
            if not m.dead:
                m.take_damage(amount)
        step["events"].append({"type": "aoe_damage", "amount": amount})

    elif dtype == "summon_count":
        count = dr.get("count", 1)
        for _ in range(count):
            if len(friendly_board) >= 7:
                break
            from game.minion import Minion as M
            token = M.from_id(dr["token"])
            friendly_board.append(token)
            step["events"].append({"type": "summon", "token": token.to_dict()})

    elif dtype == "buff_tribe":
        tribe = dr.get("tribe")
        atk_buff = dr.get("attack", 0)
        hp_buff = dr.get("health", 0)
        for m in friendly_board:
            if m.dead or m is dead:
                continue
            if tribe is None or m.tribe == tribe:
                m.attack += atk_buff
                m.health += hp_buff
                step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    elif dtype == "buff_tribe_attack":
        tribe = dr.get("tribe")
        atk_buff = dr.get("attack", 0)
        for m in friendly_board:
            if m.dead or m is dead:
                continue
            if tribe is None or m.tribe == tribe:
                m.attack += atk_buff
                step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    elif dtype == "buff_adjacent":
        atk_buff = dr.get("attack", 0)
        hp_buff = dr.get("health", 0)
        add_taunt = dr.get("add_taunt", False)
        dead_idx = None
        for i, m in enumerate(friendly_board):
            if m is dead:
                dead_idx = i
                break
        if dead_idx is not None:
            for adj_idx in [dead_idx - 1, dead_idx + 1]:
                if 0 <= adj_idx < len(friendly_board):
                    m = friendly_board[adj_idx]
                    if not m.dead:
                        m.attack += atk_buff
                        m.health += hp_buff
                        if add_taunt:
                            m.taunt = True
                        step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    elif dtype == "buff_all_health":
        amount = dr.get("amount", 1)
        for m in friendly_board:
            if not m.dead and m is not dead:
                m.health += amount
                step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    elif dtype == "summon_random_deathrattle":
        dr_minions = [mid for mid, data in MINIONS.items() if data.get("deathrattle")]
        count = dr.get("count", 2)
        for _ in range(count):
            if len(friendly_board) >= 7 or not dr_minions:
                break
            chosen_id = random.choice(dr_minions)
            from game.minion import Minion as M
            new_m = M.from_id(chosen_id)
            friendly_board.append(new_m)
            step["events"].append({"type": "summon", "token": new_m.to_dict()})


def _trigger_self_damaged_passive(damaged: Minion, board: list[Minion], step: dict):
    """Hardy Orca: als deze minion schade ontvangt → alle andere vrienden +1/+1."""
    buff_atk = damaged.passive.get("attack", 1)
    buff_hp = damaged.passive.get("health", 1)
    for ally in board:
        if ally is not damaged and not ally.dead:
            ally.attack += buff_atk
            ally.health += buff_hp
            step["events"].append({"type": "buff", "uid": ally.uid, "attack": ally.attack, "health": ally.health})


def _apply_combat_auras(board: list[Minion]):
    """Past start-of-combat aura's toe (Humming Bird e.d.)."""
    for m in board:
        if not m.passive:
            continue
        ptype = m.passive.get("type")
        if ptype == "beast_aura":
            for ally in board:
                if ally is not m and ally.tribe == "Beast":
                    ally.attack += m.passive.get("attack", 0)


def _trigger_pack_leader(new_minion: Minion, friendly_board: list, step: dict):
    pass


def _trigger_shield_pop_passives(popped: Minion, friendly_board: list, step: dict):
    for m in friendly_board:
        if m.dead:
            continue
        if not m.passive:
            continue
        ptype = m.passive.get("type")

        if ptype == "dragon_shield_pop" and popped.tribe == "Dragon":
            m.attack += m.passive.get("attack", 3)
            m.health += m.passive.get("health", 3)
            m.max_health += m.passive.get("health", 3)
            step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

        elif ptype == "any_shield_pop":
            m.attack += m.passive.get("attack", 3)
            step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})


def calculate_damage(winner_board: list[Minion], winner_tavern_tier: int) -> int:
    """Schade = winnaar tavern tier + som van tier van elke overlevende minion.
    Tokens (niet-koopbare minions) tellen als tier 1.
    Golden minions tellen hun basis tier, niet het dubbele."""
    minion_tier_sum = sum(max(m.tier, 1) for m in winner_board)
    return winner_tavern_tier + minion_tier_sum
