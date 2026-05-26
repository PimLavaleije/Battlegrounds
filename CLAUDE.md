# Battlegrounds – Project Instructies voor Claude

## Wat is dit project?
Een Hearthstone Battlegrounds kloon in Python/Flask-SocketIO. Meerdere spelers spelen via de browser; de UI is volledig in het **Nederlands**. Combat is serverside gesimuleerd; de frontend speelt een animeerbare replay af.

## Hoe starten

```bash
cd C:\Users\pimla\Documents\battlegrounds
pip install -r requirements.txt
python server.py
# → http://localhost:5000
```

## Technologie-stack
- **Backend**: Python 3.12, Flask 3, Flask-SocketIO 5 (gevent async)
- **Frontend**: Vanilla JS + Socket.IO client (geen framework)
- **Realtime**: WebSockets via Socket.IO rooms (room_code per lobby)
- **Geen database** – alles in memory

## Bestandsstructuur

```
server.py                  – Flask + alle Socket.IO event handlers
game/
  game_manager.py          – Room/lobby-routing; delegeert naar GameState
  game_state.py            – Spellogica per room (rondes, combat, shop)
  player.py                – Spelersstatus, shop-acties, battlecry, triples
  combat.py                – Serverside auto-battle simulatie + death processing
  minion.py                – Minion-klasse (stats, take_damage, clone, serialisatie)
  shop.py                  – Shop pool beheer (per-tier trekken)
  matchmaking.py           – Spelers aan elkaar koppelen per ronde
  data/
    minions.py             – TOKENS + MINIONS dicts (de volledige minion pool)
    heroes.py              – HEROES_LIST (heldgegevens)
static/
  js/
    main.js                – Hoofdlogica frontend, event handlers
    socket_client.js       – SocketClient wrapper (alle emit/on)
    game_ui.js             – GameUI.renderShop / renderBoard; buildOvalCard
    portraits.js           – PORTRAITS dict + getCardImageUrl (wiki card images)
    combat_replay.js       – Animeerbare combat replay speler
    dragdrop.js            – Drag & drop voor board herschikken
  css/
    style.css              – Hoofd-stijl (Hearthstone-look, ovale kaarten)
    animations.css         – Combat animaties
templates/
  index.html               – Enige HTML pagina (alles één-pagina-app)
```

## Architectuurregels

### Backend
- **Alle spellogica zit serverside** – de client vertrouwt nooit zijn eigen state.
- Socket.IO events sturen altijd het volledige `player_update` terug (inclusief shop en board).
- `game_manager.py` kent alleen rooms; `game_state.py` kent alleen spellogica.
- `combat.py` werkt op **clones** van het echte board – nooit het echte board muteren.

### Minion data
- `TOKENS` in `minions.py` = minions die niet in de winkel zitten (opgeroepen door deathrattles e.d.)
- `MINIONS` = de shopbare pool, gegroepeerd op tier
- `ALL_MINIONS = {**TOKENS, **MINIONS}` – `Minion.from_id()` zoekt hier in
- Elke minion heeft: `id, name, tier, attack, health, tribe, abilities, description`
- Optioneel: `deathrattle`, `battlecry`, `passive`, `end_of_turn`

### Kaartafbeeldingen
- Portretten: emoji fallback + echte Hearthstone wiki afbeelding
- Wiki URL-formaat: `https://hearthstone.wiki.gg/images/thumb/{cardId}.png/200px-{cardId}.png`
- `portraits.js` bevat `PORTRAITS` dict: `{ emoji, cardId, bg }`
- Als `cardId` null is → emoji fallback. Bij afbeelding-fout → ook emoji fallback.

### Minion pool
- Gebruik **alleen de actuele BG-pool** van [hearthstone.wiki.gg/wiki/Battlegrounds](https://hearthstone.wiki.gg/wiki/Battlegrounds)
- De BG-pool wordt via de speciale queryurl opgehaald: `https://hearthstone.wiki.gg/wiki/Battlegrounds/{Minion_Name}` voor individuele stats
- Individuele BG-kaartpagina's: `https://hearthstone.wiki.gg/wiki/Battlegrounds/{Naam_Met_Underscores}`
- **Niet de klassieke Hearthstone standaard-kaarten gebruiken** (geen Alleycat, Murloc Tidehunter, etc. – die zijn verwijderd uit BG)

## Geïmplementeerde mechanics

### Combat (combat.py)
- Aanvallen, schade, tegenslag
- Divine Shield (blokt eerste treffer)
- Taunt (verplicht doelwit)
- Windfury (2× aanvallen)
- Cleave (raakt aangrenzende vijanden ook)
- Poisonous/Venomous (instant kill bij schade)
- Reborn (herrijst met 1 HP)
- Deathrattle types: `summon`, `summon_two`, `give_attack_random`, `deal_damage_all`, `summon_random_deathrattle`, `summon_equal_attack`, `buff_tribe_attack`, `give_divine_shield_deathrattles`, `summon_random_elemental`
- Passives bij dood: `beast_dies_buff`, `mech_dies_buff`, `demon_dies_damage`, `dragon_dies_buff`, `deathrattle_played_buff`
- Aura's bij combat start: `murloc_aura`, `pirate_aura`, `demon_aura`
- Schild-pop passives: `dragon_shield_pop`, `any_shield_pop`
- Baron/Titus check: deathrattles 2× triggeren
- Zapp Slywick: valt altijd laagste aanval aan

### Shop (player.py)
- Kopen, verkopen, reroll, freeze, tavern upgraden
- Triple detect → golden + discover mechanic
- Battlecry types: `summon`, `buff_tribe`, `buff_three_tribes`
- Brann: battlecries 2×
- Hero powers

## Taal
- **Alle UI-tekst is Nederlands**
- Python commentaar mag ook Nederlands of Engels
- Variabelenamen zijn Engels

## Nog niet geïmplementeerd (stubs)
- `Spellcraft` (Naga-mechanic)
- `Avenge` (trigger na vriend sterft na X keer)
- `Rally` (trigger als minion terugkeert)
- `Magnetic` (Mech merge)
- `Choose One` mechanic
- End-of-turn effecten voor individuele kaarten (Goldgrubber, Lightfang Enforcer, Micro Machine)
- Wrath Weaver schade aan held bij Demon aanval
- Herald of Flame ketting-schade

## GitHub
Remote: `https://github.com/PimLavaleije/Battlegrounds.git`
Branch: `master`
Na wijzigingen: `git add`, `git commit`, `git push origin master`

# Objective

You are auditing Hearthstone Battlegrounds Season 13 mechanics.

Your task is to:

1. Verify mechanics against official sources.
2. Detect contradictions.
3. Flag patch-dependent behavior.
4. Identify edge cases and undocumented interactions.
5. Never hallucinate uncertain mechanics.
6. Prefer accuracy over completeness.

You are not allowed to invent undocumented mechanics.

If evidence is insufficient:
- Say UNKNOWN
- Explain why
- Suggest a reproducible in-game test.

---

# Confidence Policy

Every mechanic must receive one of the following labels:

- TRUE
- FALSE
- PARTIAL
- UNKNOWN
- PATCH_DEPENDENT

Definitions:

### TRUE
Mechanic confirmed by official wording, in-game behavior, or reproducible testing.

### FALSE
Mechanic contradicted by official wording or reproducible testing.

### PARTIAL
Mechanic is correct but missing conditions, caveats, or edge cases.

### UNKNOWN
Insufficient evidence.

### PATCH_DEPENDENT
Behavior changed between patches or is unclear for Season 13.

Never present speculation as certainty.

---

# Source Priority

Use sources in this order:

1. Blizzard official patch notes
2. Blizzard developer posts
3. Official in-game card text
4. Reproducible in-game testing
5. Community testing
6. Datamining

Official wording overrides community assumptions.

Do not treat Reddit claims as facts unless corroborated.

---

# Required Verification Process

For every mechanic:

1. Identify exact mechanic.
2. Check official wording.
3. Check Season 13 relevance.
4. Check Solos vs Duos.
5. Check Tavern Tier restrictions.
6. Check hero-specific exceptions.
7. Check edge cases:
   - board full
   - hand full
   - simultaneous triggers
   - duplicate effects
   - golden minions
   - multiple copies
   - generated cards
   - tribe availability
8. Determine confidence level.

---

# Required Output Format

For every mechanic use:

## Mechanic
[mechanic name]

### Verdict
TRUE / FALSE / PARTIAL / UNKNOWN / PATCH_DEPENDENT

### Explanation
[reasoning]

### Evidence
[source]

### Patch
[patch if relevant]

### Solos/Duos
[behavior]

### Edge Cases
[list]

### Confidence
High / Medium / Low

---

# Critical Rule

Never hallucinate undocumented Hearthstone Battlegrounds mechanics.

If uncertain:
Say UNKNOWN.