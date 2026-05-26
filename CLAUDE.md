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
