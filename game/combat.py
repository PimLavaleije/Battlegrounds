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

    post_rewards: dict[str, list] = {"player": [], "enemy": []}

    _apply_combat_auras(p_board)
    _apply_combat_auras(e_board)
    _apply_rally_effects(p_board, e_board, post_rewards["player"])
    _apply_rally_effects(e_board, p_board, post_rewards["enemy"])

    while p_board and e_board and safety < 300:
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

        # Roaring Recruiter: Dragon aanvaller krijgt buff voor aanval
        if "Dragon" in attacker.types:
            for ally in attacker_board:
                if ally.dead or ally is attacker:
                    continue
                if ally.passive and ally.passive.get("type") == "on_dragon_attack_buff_it":
                    mult = 2 if ally.golden else 1
                    attacker.attack += ally.passive.get("attack", 3) * mult
                    attacker.health += ally.passive.get("health", 1) * mult
                    attacker.max_health += ally.passive.get("health", 1) * mult

        # Kies doelwit
        target, target_idx = _choose_target(attacker, defender_board)
        if target is None:
            break

        # Megawindfury = 4x (zeldzaam, alleen via specifieke effecten); windfury = 2x; anders 1x
        attacks = 4 if attacker.megawindfury else (2 if attacker.windfury else 1)
        for _ in range(attacks):
            if not p_board or not e_board:
                break
            step = _do_attack(attacker, target, target_idx, side_name,
                              atk_idx, p_board, e_board, current_side, post_rewards)
            steps.append(step)

            # Na aanval doden verwerken
            deaths = _collect_deaths(p_board, e_board)
            if deaths:
                death_step = _process_deaths(deaths, p_board, e_board, steps, post_rewards)
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
        "post_combat_rewards": post_rewards,
    }


def _choose_target(attacker: Minion, defender_board: list[Minion]) -> tuple[Minion | None, int]:
    alive = [(i, m) for i, m in enumerate(defender_board) if not m.dead]
    if not alive:
        return None, -1

    # Zapp valt laagste aanval aan; bij gelijke aanval willekeurig
    if attacker.zapp:
        alive.sort(key=lambda x: x[1].attack)
        min_atk = alive[0][1].attack
        tied = [(i, m) for i, m in alive if m.attack == min_atk]
        chosen = random.choice(tied)
        return chosen[1], chosen[0]

    # Taunt targets
    taunt_targets = [(i, m) for i, m in alive if m.taunt]
    if taunt_targets:
        chosen = random.choice(taunt_targets)
    else:
        chosen = random.choice(alive)
    return chosen[1], chosen[0]


def _do_attack(attacker: Minion, target: Minion, target_idx: int,
               side_name: str, atk_idx: int,
               p_board: list, e_board: list, current_side: int,
               post_rewards: dict | None = None) -> dict:
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

    target_pre_health = target.health  # voor excess damage berekening

    # Schade aan doelwit
    # Poisonous (oud mechanic): vernietigt elk target
    # Venomous (Season 13): vernietigt alleen het EERSTE target per combat
    _venom_active = attacker.venomous and not getattr(attacker, '_venomous_used', False)
    _kill_damage  = attacker.poisonous or _venom_active
    result_t = target.take_damage(9999 if _kill_damage else attacker.attack)
    if _venom_active and result_t.get("damage", 0) > 0:
        attacker._venomous_used = True   # verbruikt voor rest van dit combat
    step["target_damage"] = result_t["damage"]
    step["target_shield_broken"] = result_t.get("shield_broken", False)
    if result_t.get("damage", 0) > 0 and target.health <= 0:
        target.killed_by_uid = attacker.uid

    # Hardy Orca: als doelwit schade ontvangt, buff alle andere vrienden op verdedigend bord
    defender_board_ref = e_board if current_side == 0 else p_board
    if not result_t.get("shielded") and result_t.get("damage", 0) > 0:
        if target.passive and target.passive.get("type") == "on_self_damaged":
            _trigger_self_damaged_passive(target, defender_board_ref, step)
        # Very Hungry Winterfinner: buff a hand minion (tracked as post-combat reward)
        if target.passive and target.passive.get("type") == "on_self_damage_buff_hand" and post_rewards is not None:
            mult = 2 if target.golden else 1
            atk = target.passive.get("attack", 2) * mult
            hp = target.passive.get("health", 1) * mult
            side_key = "enemy" if current_side == 0 else "player"
            post_rewards[side_key].append({"type": "buff_random_hand", "attack": atk, "health": hp})
        # Iridescent Skyblazer / Trigore: Beast neemt schade
        if "Beast" in target.types:
            for ally in defender_board_ref:
                if ally.dead or ally is target:
                    continue
                if ally.passive and ally.passive.get("type") == "on_beast_damage_buff_other_beast":
                    mult = 2 if ally.golden else 1
                    others = [a for a in defender_board_ref if not a.dead and a is not target]
                    if others:
                        chosen = random.choice(others)
                        chosen.attack += ally.passive.get("attack", 2) * mult
                        chosen.health += ally.passive.get("health", 1) * mult
                        chosen.max_health += ally.passive.get("health", 1) * mult
                elif ally.passive and ally.passive.get("type") == "on_beast_damage_buff_self_health":
                    mult = 2 if ally.golden else 1
                    ally.health += ally.passive.get("health", 2) * mult
                    ally.max_health += ally.passive.get("health", 2) * mult

        # Wyvern Outrider: gratis refresh als het zelf schade neemt (max 3/beurt)
        if target.passive and target.passive.get("type") == "on_self_damage_free_refresh":
            max_per_turn = target.passive.get("max_per_turn", 3)
            triggered = getattr(target, "_wyvern_count", 0)
            if triggered < max_per_turn:
                target._wyvern_count = triggered + 1
                count = 2 if target.golden else 1
                if post_rewards is not None:
                    defender_rewards = post_rewards["enemy" if current_side == 0 else "player"]
                    defender_rewards.append({"type": "free_refreshes_post_combat", "count": count})

    # Wildfire Elemental: excess damage naar aangrenzende vijandelijke minion(s) bij kill
    if (attacker.passive and attacker.passive.get("type") == "after_kill_excess_damage"
            and target.health <= 0 and not result_t.get("shielded", False)
            and not attacker.poisonous):
        excess = max(0, attacker.attack - target_pre_health)
        if excess > 0:
            defender_board_exc = e_board if current_side == 0 else p_board
            adj_indices = [i for i in [target_idx - 1, target_idx + 1]
                           if 0 <= i < len(defender_board_exc)]
            if attacker.golden:
                exc_targets = [defender_board_exc[i] for i in adj_indices
                               if not defender_board_exc[i].dead]
            else:
                candidates = [defender_board_exc[i] for i in adj_indices
                              if not defender_board_exc[i].dead]
                exc_targets = [random.choice(candidates)] if candidates else []
            for t_exc in exc_targets:
                exc_res = t_exc.take_damage(excess)
                step["events"].append({"type": "excess_damage", "uid": t_exc.uid,
                                       "damage": exc_res["damage"]})

    # Tegenslag – venomous target doodt aanvaller (eerste keer dat het schade uitdeelt)
    _target_venom_active = target.venomous and not getattr(target, '_venomous_used', False)
    _target_kill = target.poisonous or _target_venom_active
    result_a = attacker.take_damage(9999 if _target_kill else target.attack)
    if _target_venom_active and result_a.get("damage", 0) > 0:
        target._venomous_used = True
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
    # Officiële BG: deathrattles triggeren in volgorde van inkomst (oudste eerst)
    deaths.sort(key=lambda x: x[0].play_order)
    return deaths


def _process_deaths(deaths: list, p_board: list[Minion], e_board: list[Minion], all_steps: list,
                    post_rewards: dict | None = None) -> list[dict]:
    if post_rewards is None:
        post_rewards = {"player": [], "enemy": []}
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
        side_rewards = post_rewards[dead_side]

        # Passive triggers op vriendelijke minions
        for m in friendly_board:
            if m.dead:
                continue
            if not m.passive:
                continue
            ptype = m.passive.get("type")

            if ptype == "beast_dies_buff" and "Beast" in dead_minion.types:
                m.attack += m.passive.get("attack", 0)
                m.health += m.passive.get("health", 0)
                death_step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "mech_dies_buff" and "Mech" in dead_minion.types:
                m.attack += m.passive.get("attack", 0)
                m.health += m.passive.get("health", 0)
                death_step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "dragon_dies_buff" and "Dragon" in dead_minion.types:
                m.attack += m.passive.get("attack", 0)
                m.health += m.passive.get("health", 0)
                death_step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

            elif ptype == "demon_dies_damage" and "Demon" in dead_minion.types:
                alive_enemies = [e for e in enemy_board if not e.dead]
                if alive_enemies:
                    target = random.choice(alive_enemies)
                    target.take_damage(m.passive.get("amount", 3))
                    death_step["events"].append({"type": "soul_juggler", "target_uid": target.uid})

            elif ptype == "taunt_dies_blood_gem" and dead_minion.taunt:
                count = m.passive.get("count", 1) * (2 if m.golden else 1)
                side_rewards.append({"type": "give_blood_gems_post_combat", "count": count, "golden": False})

            elif ptype == "on_deathrattle_death_bg_bonus" and dead_minion.deathrattle:
                amount = m.passive.get("amount", 1) * (2 if m.golden else 1)
                side_rewards.append({"type": "blood_gem_attack_bonus_post_combat", "amount": amount, "golden": False})

        # Game-brede dood-tellers (eternal_knight, sanlayn_scribe, old_soul)
        if dead_minion.id == "eternal_knight":
            for m in friendly_board:
                if m.dead or m.id != "eternal_knight":
                    continue
                mult = 2 if m.golden else 1
                m.attack += 2 * mult; m.health += 1 * mult; m.max_health += 1 * mult
            side_rewards.append({"type": "eternal_knight_died"})
        elif dead_minion.id == "sanlayn_scribe":
            for m in friendly_board:
                if m.dead or m.id != "sanlayn_scribe":
                    continue
                mult = 2 if m.golden else 1
                m.attack += 4 * mult; m.health += 4 * mult; m.max_health += 4 * mult
            side_rewards.append({"type": "sanlayn_scribe_died"})
        side_rewards.append({"type": "old_soul_deaths", "count": 1})

        # Avenge – tel dood mee voor alle levende vriendelijke avenge-minions
        for m in friendly_board:
            if m.dead or not m.avenge:
                continue
            threshold = m.avenge.get("threshold", 1)
            m._avenge_counter = getattr(m, "_avenge_counter", 0) + 1
            if m._avenge_counter >= threshold:
                m._avenge_counter = 0
                _trigger_avenge(m, m.avenge, friendly_board, enemy_board, death_step, side_rewards)

        # Deathrattle
        if dead_minion.deathrattle:
            dr = dead_minion.deathrattle
            # Titus Rivendare: golden = 3 triggers, normal = 2 triggers
            titus = next((m for m in friendly_board if m.id == "titus_rivendare" and not m.dead), None)
            if titus:
                triggers = 3 if titus.golden else 2
            else:
                triggers = 1

            for _ in range(triggers):
                _apply_deathrattle(dead_minion, dr, friendly_board, enemy_board, death_step, side_rewards)

        # Reborn — insert at dead minion's position
        if dead_minion.reborn and not dead_minion.reborn_used:
            dead_minion.reborn_used = True
            alive_count = sum(1 for m in friendly_board if not m.dead)
            if alive_count < 7:
                reborn_copy = dead_minion.clone()
                full_hp = dead_minion.passive and dead_minion.passive.get("type") == "full_health_reborn"
                reborn_copy.health = reborn_copy.max_health if full_hp else 1
                reborn_copy.dead = False
                reborn_copy.reborn = False
                dead_idx = next((i for i, m in enumerate(friendly_board) if m is dead_minion), len(friendly_board))
                friendly_board.insert(dead_idx + 1, reborn_copy)
                death_step["events"].append({"type": "reborn", "uid": reborn_copy.uid, "name": reborn_copy.name})

        result_steps.append(death_step)

    return result_steps


def _alive_count(board: list) -> int:
    return sum(1 for m in board if not m.dead)


def _dead_idx(dead: Minion, board: list) -> int:
    for i, m in enumerate(board):
        if m is dead:
            return i
    return len(board)


def _apply_deathrattle(dead: Minion, dr: dict, friendly_board: list, enemy_board: list, step: dict,
                       post_rewards: list | None = None):
    dtype = dr.get("type")
    spawn_pos = _dead_idx(dead, friendly_board)  # insert tokens right after dead slot

    # Falling Sky Golem: buff voor elke deathrattle die triggert
    for _fsg in friendly_board:
        if _fsg.dead or _fsg.id != "falling_sky_golem":
            continue
        _fsg_mult = 2 if _fsg.golden else 1
        _fsg.attack += 4 * _fsg_mult
        _fsg.health += 2 * _fsg_mult
        _fsg.max_health += 2 * _fsg_mult
    if post_rewards is not None:
        post_rewards.append({"type": "deathrattle_triggered_game"})

    def _summon_token(token_id: str, overrides: dict | None = None) -> bool:
        from game.minion import Minion as M
        if _alive_count(friendly_board) >= 7:
            return False
        token = M.from_id(token_id)
        if overrides:
            for k, v in overrides.items():
                setattr(token, k, v)
        nonlocal spawn_pos
        friendly_board.insert(spawn_pos + 1, token)
        spawn_pos += 1
        step["events"].append({"type": "summon", "token": token.to_dict()})
        _trigger_pack_leader(token, friendly_board, step)
        # Deflect-o-Bot: Mech gesummond → buff deflect_o_bots
        if "Mech" in token.types:
            for ally in friendly_board:
                if ally.dead:
                    continue
                if ally.passive and ally.passive.get("type") == "on_mech_summon_buff_self":
                    ally_mult = 2 if ally.golden else 1
                    ally.attack += ally.passive.get("attack", 2) * ally_mult
                    ally.divine_shield = True
                    if "divine_shield" not in ally.abilities:
                        ally.abilities.append("divine_shield")
        # Banana Slamma: Beast gesummond → double (of triple voor golden) stats
        if "Beast" in token.types:
            for ally in friendly_board:
                if ally.dead or not ally.passive:
                    continue
                if ally.passive.get("type") == "on_beast_summon_double_stats":
                    factor = 3 if ally.golden else 2
                    token.attack *= factor
                    token.health *= factor
                    token.max_health *= factor
                    break
        return True

    if dtype == "summon":
        _summon_token(dr["token"])

    elif dtype == "summon_two":
        for _ in range(2):
            if not _summon_token(dr["token"]):
                break

    elif dtype == "give_attack_random":
        alive = [m for m in friendly_board if not m.dead and m is not dead]
        if alive:
            target = random.choice(alive)
            target.attack += dead.attack
            step["events"].append({"type": "buff", "uid": target.uid, "attack": target.attack, "health": target.health})

    elif dtype == "give_attack_two_random":
        alive = [m for m in friendly_board if not m.dead and m is not dead]
        chosen = random.sample(alive, min(2, len(alive)))
        for target in chosen:
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
        summoned = []
        for _ in range(count):
            prev_len = len(friendly_board)
            if not _summon_token(dr["token"]):
                break
            if len(friendly_board) > prev_len:
                summoned.append(friendly_board[spawn_pos])
        if dr.get("add_taunt"):
            for m in summoned:
                m.taunt = True
                if "taunt" not in m.abilities:
                    m.abilities.append("taunt")
        gems = dr.get("blood_gem_count", 0)
        if gems:
            for m in summoned:
                m.attack += gems
                m.health += gems
                m.max_health += gems

    elif dtype == "buff_tribe":
        tribe = dr.get("tribe")
        atk_buff = dr.get("attack", 0)
        hp_buff = dr.get("health", 0)
        for m in friendly_board:
            if m.dead or m is dead:
                continue
            if tribe is None or tribe in m.types:
                m.attack += atk_buff
                m.health += hp_buff
                step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    elif dtype == "buff_tribe_one":
        tribe = dr.get("tribe")
        atk_buff = dr.get("attack", 0)
        hp_buff = dr.get("health", 0)
        eligible = [m for m in friendly_board if not m.dead and m is not dead
                    and (tribe is None or tribe in m.types)]
        if eligible:
            target = random.choice(eligible)
            target.attack += atk_buff
            target.health += hp_buff
            step["events"].append({"type": "buff", "uid": target.uid, "attack": target.attack, "health": target.health})

    elif dtype == "buff_tribe_attack":
        tribe = dr.get("tribe")
        atk_buff = dr.get("attack", 0)
        for m in friendly_board:
            if m.dead or m is dead:
                continue
            if tribe is None or tribe in m.types:
                m.attack += atk_buff
                step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    elif dtype == "buff_adjacent":
        atk_buff = dr.get("attack", 0)
        hp_buff = dr.get("health", 0)
        add_taunt = dr.get("add_taunt", False)
        dead_i = _dead_idx(dead, friendly_board)
        for adj_idx in [dead_i - 1, dead_i + 1]:
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

    elif dtype == "summon_with_self_attack":
        _summon_token(dr["token"], {"attack": dead.attack})

    elif dtype == "summon_random_deathrattle":
        dr_minions = [mid for mid, data in MINIONS.items() if data.get("deathrattle")]
        count = dr.get("count", 2)
        for _ in range(count):
            if not dr_minions:
                break
            chosen_id = random.choice(dr_minions)
            if not _summon_token(chosen_id):
                break

    # ── New deathrattle types ────────────────────────────────
    elif dtype == "give_reborn_undead":
        eligible = [m for m in friendly_board if not m.dead and m is not dead
                    and "Undead" in m.types and not m.reborn]
        if eligible:
            target = random.choice(eligible)
            target.reborn = True
            step["events"].append({"type": "buff", "uid": target.uid, "attack": target.attack, "health": target.health})

    elif dtype == "buff_all_hp_deal_damage":
        hp_buff = dr.get("health", 1)
        dmg = dr.get("damage", 1)
        for m in friendly_board:
            if not m.dead and m is not dead:
                m.health += hp_buff
                m.max_health += hp_buff
                m.take_damage(dmg)
        step["events"].append({"type": "aoe_damage", "amount": dmg})

    elif dtype == "destroy_killer":
        # tracked via last_hit_by on the dead minion (set in _do_attack if we add that)
        killer_uid = getattr(dead, "killed_by_uid", None)
        if killer_uid:
            for m in enemy_board:
                if m.uid == killer_uid and not m.dead:
                    m.health = -9999
                    step["events"].append({"type": "aoe_damage", "amount": 0})
                    break

    elif dtype == "summon_random_beast_set_stats":
        beast_ids = [mid for mid, data in MINIONS.items()
                     if "Beast" in data.get("types", [])]
        if beast_ids:
            chosen_id = random.choice(beast_ids)
            atk = dr.get("attack", 6)
            hp = dr.get("health", 6)
            _summon_token(chosen_id, {"attack": atk, "health": hp, "max_health": hp})

    elif dtype == "summon_dead_mechs":
        count = dr.get("count", 2)
        dead_mechs = [m for m in friendly_board if m.dead and "Mech" in m.types][:count]
        for dead_m in dead_mechs:
            _summon_token(dead_m.id)

    elif dtype == "cast_queens_command":
        multiplier = 2 if dead.golden else 1
        for m in friendly_board:
            if not m.dead:
                atk = 3 * multiplier
                hp = 3 * multiplier
                if "Naga" in m.types:
                    atk *= 2
                    hp *= 2
                m.attack += atk
                m.health += hp
                step["events"].append({"type": "buff", "uid": m.uid, "attack": m.attack, "health": m.health})

    # ── Post-combat reward types (fired in combat, given after) ─
    elif dtype in ("add_spell_post_combat", "give_random_chromadrake_post_combat",
                   "give_random_bounty_post_combat", "give_random_magnetic_mech_post_combat",
                   "free_refreshes_post_combat", "spell_discount_post_combat",
                   "buff_random_hand"):
        if post_rewards is not None:
            reward = dict(dr)
            reward["type"] = dtype
            post_rewards.append(reward)

    elif dtype in ("give_blood_gems_post_combat", "blood_gem_attack_bonus_post_combat",
                   "blood_gem_adjacent_post_combat"):
        if post_rewards is not None:
            reward = {**dr, "golden": dead.golden}
            post_rewards.append(reward)

    elif dtype == "summon_undead_from_hand":
        # Deathly Striker: summon a random Undead from pool for this combat
        from game.data.minions import MINIONS as _MINS
        mult = 2 if dead.golden else 1
        pool = [mid for mid, d in _MINS.items() if "Undead" in d.get("types", []) and d["tier"] <= 4]
        for _ in range(mult):
            if pool and _alive_count(friendly_board) < 7:
                _summon_token(random.choice(pool))

    elif dtype == "cast_shifting_tide_adjacent":
        # Tide Raiser: pick a random adjacent minion and move it to a random position
        idx = next((i for i, m in enumerate(friendly_board) if m is dead), -1)
        if idx >= 0:
            adjacent = []
            if idx - 1 >= 0 and not friendly_board[idx - 1].dead:
                adjacent.append(idx - 1)
            if idx + 1 < len(friendly_board) and not friendly_board[idx + 1].dead:
                adjacent.append(idx + 1)
            mult = 2 if dead.golden else 1
            for _ in range(mult):
                if adjacent:
                    adj_i = random.choice(adjacent)
                    target = friendly_board.pop(adj_i)
                    new_pos = random.randint(0, len(friendly_board))
                    friendly_board.insert(new_pos, target)
                    step["events"].append({"type": "deathrattle", "uid": dead.uid,
                                           "effect": "shifting_tide", "moved_uid": target.uid})
                    adjacent = []  # only one per cast for golden (re-pick per trigger)

    elif dtype == "buff_all_mechs_attack_combat":
        # Ingenious Inventor: all Mechs +2 Attack this combat, +2 more per Magnetize
        mult = 2 if dead.golden else 1
        base_atk = dr.get("base_attack", 2) * mult
        magnetize_count = getattr(dead, "_magnetize_count", 0)
        total_atk = base_atk + base_atk * magnetize_count
        for ally in friendly_board:
            if not ally.dead and "Mech" in ally.types:
                ally.attack += total_atk
        step["events"].append({"type": "deathrattle", "uid": dead.uid, "effect": "buff_mechs", "attack": total_atk})

    elif dtype == "buff_tavern_tribe_post_combat":
        # Dancing Barnstormer deathrattle: buff Elementals in tavern post-combat
        mult = 2 if dead.golden else 1
        post_rewards.append({"type": "buff_tavern_tribe_post_combat",
                              "tribe": dr.get("tribe"), "attack": dr.get("attack", 8) * mult,
                              "health": dr.get("health", 8) * mult})

    elif dtype == "give_spell_post_combat":
        # Razorfen Flapper: get spell after combat
        spell_id = dr.get("spell", "blood_gem_barrage")
        mult = 2 if dead.golden else 1
        for _ in range(mult):
            post_rewards.append({"type": "add_spell_post_combat", "spell": spell_id})

    elif dtype == "waveling_refresh_hook":
        # Waveling: register persistent refresh buff hook
        mult = 2 if dead.golden else 1
        post_rewards.append({"type": "waveling_refresh_hook", "golden": dead.golden,
                              "attack": dr.get("attack", 3) * mult,
                              "health": dr.get("health", 3) * mult})

    elif dtype == "trigger_adjacent_battlecry":
        # Rylak Metalhead: trigger Battlecry of adjacent minion (simplified: buff nearby)
        idx = next((i for i, m in enumerate(friendly_board) if m is dead), -1)
        if idx >= 0:
            for adj_i in [idx - 1, idx + 1]:
                if 0 <= adj_i < len(friendly_board):
                    adj = friendly_board[adj_i]
                    if not adj.dead and adj.battlecry:
                        btype = adj.battlecry.get("type", "")
                        # Apply simple stat battlecries; skip complex ones
                        if btype == "buff_tribe":
                            tribe = adj.battlecry.get("tribe")
                            atk = adj.battlecry.get("attack", 0)
                            hp = adj.battlecry.get("health", 0)
                            for ally in friendly_board:
                                if not ally.dead and (tribe is None or tribe in ally.types):
                                    ally.attack += atk; ally.health += hp
                    break


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
    """Past start-of-combat aura's toe (Humming Bird, Amber Guardian e.d.)."""
    for m in board:
        if not m.passive:
            continue
        ptype = m.passive.get("type")
        if ptype == "beast_aura":
            for ally in board:
                if ally is not m and "Beast" in ally.types:
                    ally.attack += m.passive.get("attack", 0)

        elif ptype == "start_of_combat_buff_tribe":
            tribe = m.passive.get("tribe")
            eligible = [ally for ally in board if ally is not m and tribe in ally.types]
            if eligible:
                target = random.choice(eligible)
                target.attack += m.passive.get("attack", 0)
                target.health += m.passive.get("health", 0)
                if m.passive.get("divine_shield"):
                    target.divine_shield = True

        elif ptype == "start_of_combat_buff_tribe_all":
            tribe = m.passive.get("tribe")
            atk = m.passive.get("attack", 0)
            hp = m.passive.get("health", 0)
            exclude_self = m.passive.get("exclude_self", False)
            for ally in board:
                if exclude_self and ally is m:
                    continue
                if tribe is None or tribe in ally.types:
                    ally.attack += atk
                    ally.health += hp


def _trigger_pack_leader(new_minion: Minion, friendly_board: list, step: dict):
    pass


def _apply_rally_effects(board: list[Minion], enemy_board: list[Minion], post_rewards: list):
    """Fires Rally effects at start of combat for minions on board."""
    for m in board:
        if not m.rally:
            continue
        rtype = m.rally.get("type")
        multiplier = 2 if m.golden else 1

        if rtype == "buff_tribe_spread_rally":
            # Stomping Stegodon: give all other Beasts +attack AND give them this Rally
            tribe = m.rally.get("tribe")
            atk = m.rally.get("attack", 0) * multiplier
            spread_rally = {"type": "buff_tribe_all", "tribe": tribe,
                            "attack": m.rally.get("attack", 0), "health": 0}
            buffed = []
            for ally in board:
                if ally is not m and not ally.dead and (tribe is None or tribe in ally.types):
                    ally.attack += atk
                    ally.rally = spread_rally
                    buffed.append(ally)
            # Post-combat: spread the rally to real board minions permanently
            post_rewards.append({"type": "spread_stegodon_rally",
                                 "tribe": tribe, "attack": m.rally.get("attack", 0)})

        elif rtype == "buff_tribe_random":
            tribe = m.rally.get("tribe")
            eligible = [a for a in board if a is not m and not a.dead
                        and (tribe is None or tribe in a.types)]
            if eligible:
                target = random.choice(eligible)
                target.attack += m.rally.get("attack", 0) * multiplier
                target.health += m.rally.get("health", 0) * multiplier

        elif rtype == "buff_tribe_all" or rtype == "buff_tribe_others":
            tribe = m.rally.get("tribe")
            for ally in board:
                if ally is not m and not ally.dead and (tribe is None or tribe in ally.types):
                    ally.attack += m.rally.get("attack", 0) * multiplier
                    ally.health += m.rally.get("health", 0) * multiplier

        elif rtype == "trigger_leftmost_deathrattle":
            dr_m = next((a for a in board if a is not m and not a.dead and a.deathrattle), None)
            if dr_m:
                dummy_step = {"events": []}
                _apply_deathrattle(dr_m, dr_m.deathrattle, board, [], dummy_step, post_rewards)

        elif rtype == "give_tribe_keyword":
            tribe = m.rally.get("tribe")
            keyword = m.rally.get("keyword", "venomous")
            eligible = [a for a in board if a is not m and not a.dead
                        and (tribe is None or tribe in a.types)]
            if eligible:
                target = random.choice(eligible)
                setattr(target, keyword, True)
                target.poisonous = True  # venomous implies poisonous in combat

        elif rtype == "cast_queens_command":
            for ally in board:
                if not ally.dead:
                    ally.attack += 3 * multiplier
                    ally.health += 3 * multiplier
                    if "Naga" in ally.types:
                        ally.attack += 3 * multiplier
                        ally.health += 3 * multiplier

        elif rtype == "gain_target_attack":
            # Heroic Underdog: gain the Attack of a random enemy
            if enemy_board:
                target = random.choice([e for e in enemy_board if not e.dead] or enemy_board)
                gain = target.attack * multiplier
                m.attack += gain

        elif rtype == "remove_keywords_target":
            # Sin'dorei Straight Shot: remove Reborn and Taunt from a random enemy
            targets = [e for e in enemy_board if not e.dead and (e.reborn or e.taunt)]
            if targets:
                t = random.choice(targets)
                t.reborn = False; t.taunt = False
                t.abilities = [a for a in t.abilities if a not in ("reborn", "taunt")]

        elif rtype == "give_3_self_attack":
            # Dead Sea Ravager: give 3 other friendly minions this minion's Attack
            count = m.rally.get("count", 3) * multiplier
            eligible = [a for a in board if a is not m and not a.dead]
            targets = eligible[:count] if len(eligible) <= count else random.sample(eligible, count)
            for t in targets:
                t.attack += m.attack

        elif rtype in ("give_random_bounty_post_combat", "give_random_magnetic_mech_post_combat"):
            count = multiplier
            for _ in range(count):
                post_rewards.append({"type": rtype})

        elif rtype == "buff_tribe_permanent":
            tribe = m.rally.get("tribe")
            atk = m.rally.get("attack", 0)
            hp = m.rally.get("health", 0)
            if atk or hp:
                post_rewards.append({"type": "rally_buff_tribe_permanent",
                                     "tribe": tribe, "attack": atk * multiplier,
                                     "health": hp * multiplier})

        elif rtype == "chefs_choice_right_neighbor":
            idx = next((i for i, a in enumerate(board) if a is m), -1)
            if 0 <= idx < len(board) - 1:
                neighbor = board[idx + 1]
                if neighbor.types:
                    for _ in range(multiplier):
                        post_rewards.append({"type": "rally_chefs_choice",
                                             "tribes": list(neighbor.types)})


def _trigger_avenge(avenger: Minion, avenge: dict, friendly_board: list, enemy_board: list,
                    step: dict, post_rewards: list):
    """Triggert het Avenge-effect van een minion."""
    atype = avenge.get("type")
    mult = 2 if avenger.golden else 1

    if atype == "avenge_summon":
        token_id = avenge.get("token")
        make_golden = avenge.get("golden_token") and avenger.golden
        for _ in range(mult):
            from game.minion import Minion as M
            if _alive_count(friendly_board) >= 7:
                break
            token = M.from_id(token_id)
            if make_golden:
                token.make_golden()
            spawn_pos = next((i for i, m in enumerate(friendly_board) if m is avenger), len(friendly_board))
            friendly_board.insert(spawn_pos + 1, token)
            step["events"].append({"type": "avenge_summon", "token": token.to_dict()})

    elif atype == "avenge_self_buff":
        atk = avenge.get("attack", 1) * mult
        hp = avenge.get("health", 1) * mult
        avenger.attack += atk
        avenger.health += hp
        avenger.max_health += hp
        step["events"].append({"type": "buff", "uid": avenger.uid,
                                "attack": avenger.attack, "health": avenger.health})

    elif atype == "avenge_divine_shield":
        for _ in range(mult):
            avenger.divine_shield = True
            step["events"].append({"type": "avenge_divine_shield", "uid": avenger.uid})

    elif atype == "avenge_blood_gems_tribe":
        tribe = avenge.get("tribe")
        count = avenge.get("count", 2) * mult
        for m in friendly_board:
            if m.dead or m is avenger:
                continue
            if tribe is None or tribe in m.types:
                for _ in range(count):
                    m.attack += 1
                    m.health += 1
                    m.max_health += 1
                step["events"].append({"type": "buff", "uid": m.uid,
                                        "attack": m.attack, "health": m.health})

    elif atype in ("avenge_chromadrake", "avenge_spell", "avenge_blood_gem_bonus",
                   "avenge_get_undead", "avenge_teammate_minion"):
        reward = {**avenge, "golden": avenger.golden}
        post_rewards.append(reward)


def _trigger_shield_pop_passives(popped: Minion, friendly_board: list, step: dict):
    for m in friendly_board:
        if m.dead:
            continue
        if not m.passive:
            continue
        ptype = m.passive.get("type")

        if ptype == "dragon_shield_pop" and "Dragon" in popped.types:
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
