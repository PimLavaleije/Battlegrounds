import random


def make_matchups(alive_sids: list[str], ghost_boards: dict) -> dict[str, str]:
    """
    Koppelt levende spelers aan elkaar voor gevecht.
    Bij oneven aantal: één speler vecht tegen een 'ghost' (oud board van uitgeschakelde speler).
    Returns: {player_sid: opponent_sid_or_ghost_key}
    """
    players = list(alive_sids)
    random.shuffle(players)

    matchups = {}
    i = 0
    while i < len(players) - 1:
        matchups[players[i]] = players[i + 1]
        matchups[players[i + 1]] = players[i]
        i += 2

    # Oneven: geef de laatste speler een ghost-tegenstander
    if len(players) % 2 == 1:
        last = players[-1]
        if ghost_boards:
            ghost_key = random.choice(list(ghost_boards.keys()))
            matchups[last] = f"ghost:{ghost_key}"
        else:
            # Geen ghosts: vecht tegen een willekeurige levende (niet zichzelf)
            others = [p for p in players if p != last]
            if others:
                matchups[last] = random.choice(others)

    return matchups
