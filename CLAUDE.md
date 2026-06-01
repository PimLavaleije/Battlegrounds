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
- Optioneel: `deathrattle`, `battlecry`, `passive`, `end_of_turn`, `start_of_turn`, `avenge`, `rally`, `spellcraft`

### Kaartafbeeldingen
- Portretten: emoji fallback + echte Hearthstone wiki afbeelding
- Wiki URL-formaat: `https://hearthstone.wiki.gg/images/thumb/{cardId}.png/200px-{cardId}.png`
- `portraits.js` bevat `PORTRAITS` dict: `{ emoji, cardId, bg }`
- Als `cardId` null is → emoji fallback. Bij afbeelding-fout → ook emoji fallback.

### Frontend / UI
- Fonts: **Cinzel** (serif, voor titels/namen) + **Nunito** (sans-serif, voor UI) via Google Fonts `<link>` in `index.html`
- `style.css` bevat alle visuele styling; `animations.css` bevat alle `@keyframes` en utility-klassen
- Utility animatieklassen: `anim-bounce-in`, `anim-card-appear`, `anim-takehit`, `anim-death`, `anim-attack-right/left`, `anim-gold-flash`, `anim-hp-damage`, etc.
- Shop-kaarten krijgen `anim-card-appear` met staggered `animationDelay` bij elke render
- HUD-stats: HP flash bij schade (`anim-hp-damage`), goud flash bij toename (`anim-gold-flash`)

### Minion pool
- Gebruik **alleen de actuele BG-pool** van [hearthstone.wiki.gg/wiki/Battlegrounds](https://hearthstone.wiki.gg/wiki/Battlegrounds)
- De BG-pool wordt via de speciale queryurl opgehaald: `https://hearthstone.wiki.gg/wiki/Battlegrounds/{Minion_Name}` voor individuele stats
- Individuele BG-kaartpagina's: `https://hearthstone.wiki.gg/wiki/Battlegrounds/{Naam_Met_Underscores}`
- **Niet de klassieke Hearthstone standaard-kaarten gebruiken** (geen Alleycat, Murloc Tidehunter, etc. – die zijn verwijderd uit BG)

## Geïmplementeerde mechanics

### Combat (combat.py)
- Aanvallen, schade, tegenslag
- Divine Shield, Taunt, Windfury, Megawindfury, Cleave, Poisonous/Venomous, Reborn
- Deathrattle types: `summon`, `summon_two`, `summon_count`, `give_attack_random`, `deal_damage_all`, `summon_random_deathrattle`, `summon_equal_attack`, `buff_tribe_attack`, `give_divine_shield_deathrattles`, `summon_random_elemental`, en meer
- Post-combat deathrattles: `give_blood_gems_post_combat`, `blood_gem_attack_bonus_post_combat`
- Passives bij dood: `beast_dies_buff`, `mech_dies_buff`, `demon_dies_damage`, `dragon_dies_buff`, `deathrattle_played_buff`, `taunt_dies_blood_gem`, `on_deathrattle_death_bg_bonus`
- Game-brede dood-tellers: `eternal_knight_died`, `sanlayn_scribe_died`, `deathrattle_triggered_game`, `old_soul_deaths`
- Aura's bij combat start: `murloc_aura`, `pirate_aura`, `demon_aura`
- Schild-pop passives: `dragon_shield_pop`, `any_shield_pop`
- Aanvals-passives: `on_dragon_attack_buff_it` (roaring_recruiter)
- Schade-passives: `on_self_damaged`, `on_beast_damage_buff_other_beast` (iridescent_skyblazer), `on_beast_damage_buff_self_health` (trigore), `on_self_damage_free_refresh` (wyvern_outrider → gratis refresh)
- Summon-passives: `on_mech_summon_buff_self` (deflect_o_bot)
- Overkill: `after_kill_excess_damage` (wildfire_elemental) — excess damage naar aangrenzend(e) minion(s)
- Falling Sky Golem: mid-combat +4/+2 per deathrattle + post-combat permanente counter
- Titus Rivendare / Baron: deathrattles 2× triggeren
- Zapp Slywick: valt altijd laagste aanval aan
- **Avenge** (Fase 3): `_avenge_counter` per minion; threshold-based; 9 types
- **Rally** (Fase 11): `buff_tribe_random`, `buff_tribe_all`, `buff_tribe_permanent` (dustbone_devastator, game-wide), `trigger_leftmost_deathrattle`, `give_tribe_keyword`, `cast_queens_command`, `give_random_bounty_post_combat`, `give_random_magnetic_mech_post_combat`, `chefs_choice_right_neighbor` (seafloor_recruiter)
- Expert Aviator rally: `summon_leftmost_hand` — pre-combat in game_state; permanent buff handminion

### game_state.py (Fases 9-10)
- **Tarecgosa** (Fase 9): combat-gewonnen stats/keywords bewaard op echt board na combat
- **Persistent Poet** (Fase 9): aangrenzende Dragons bewaren combat stats
- **Egg of the Endtimes** (Fase 10): 2-beurt handteller → `triple_discover` modal → T6 Dragon keuze

### Shop (player.py)
- Kopen, verkopen, reroll, freeze, tavern upgraden
- Triple detect → golden + discover mechanic
- Battlecry types: `summon`, `buff_tribe`, `buff_three_tribes`, `give_blood_gems`, `blood_gem_health_bonus`, `blood_gems_all_board`, `blood_gem_with_keyword_tribe`, `get_slimy_shields`, `discover_tribe`, `discover_tribe_self_damage`, `destroy_undead_get_copy`, `buff_tribe_by_gold_spent`, `buff_random_board_by_spells`, en meer
- Brann: battlecries 2×; battlecry_discover via bestaande discover modal
- Hero powers
- Goud-drempel passives: `on_gold_spent_threshold` → `buff_tribe`, `buff_two_random_tribe`, `blood_gems_tribe`, `get_spell`
- Stat-drempel passives: `attack_threshold_divine_shield` (scarlet_survivor)
- **Game-brede tellers** (Fase 7): `eternal_knight_deaths`, `sanlayn_scribe_deaths`, `deathrattles_triggered_game`, `spells_cast_game`; passive types: `has_per_ek_death`, `has_per_ss_death`, `has_per_deathrattle_triggered`, `has_per_spell_cast`
- **Held-schade hook** (Fase 8): `_on_hero_damaged()` triggert Floating Watcher (`on_hero_damage_buff_self`); wired voor graveyard_shift, on_demon_bought, discover_tribe_self_damage
- **Wrath Weaver**: volledig geïmplementeerd (buff + held-schade via `_on_hero_damaged`)
- Sell passives: `on_sell_if_lost_bonus_gold` (tortollan_blue_shell)
- **Blood Gems** (Fase 2): `blood_gem_extra_cast` (hot_air_surveyor), `eot_blood_gem_all_minions` (earthsong_shaman), `blood_gems_tribe_post_combat` (three_lil_quilboar)
- **EOT effecten**: `eot_blood_gem_all_minions`, `eot_demon_consume_tavern` (famished_felbat); Drakkari verdubbeling via `double_eot`
- **Pass mechanic** (Fase 4): `pass_minion()` in player; 1 goud kost; gratis via wanderer_cho; passenger, puddle_prancer, mantid_king, mirror_monster, storm_splitter, jumping_jack, transport_reactor
- **Magnetic mechanic** (Fase 5): `magnetize()` in player; stats + keywords + deathrattle overnemen; cross-tribe voor technical_element en prosthetic_hand
- **Spellcraft** (Fase 12): alle `sc_*` effecten geïmplementeerd; tijdelijke keyword-reversal (surf_n_surf deathrattle, deep_sea_angler taunt, waverider windfury, glowscale divine_shield) omgekeerd bij `start_turn`; Zesty Shaker `on_spellcraft_target_get_copy` passive
- **Spellcraft generatie**: Nagas op het board genereren hun spreuk aan het begin van elke beurt (`start_turn`), niet eenmalig bij spelen
- **Tranquil Meditative** spellcraft: buffed permanent `spell_attack_bonus` en `spell_health_bonus` (was: +2 health alle minions)
- **Blood Gems in hand**: eigen `blood-gem-card` kaarttype; klik triggert `SpellTarget` targeting mode → klik op board-minion om te targeten
- **Choose One mechanic**: geïmplementeerd voor Sprightly Scarab; `choose_one` veld op Minion; `choose_one_choice` socket event; modal met optieknoppen; `apply_choose_one()` in player
- **Hero power UI**: verplaatst naar eigen zijpaneel rechts van de hand met held-naam, beschrijving en activeerknop
- **Hero powers geïmplementeerd**: `bloodbound` (Death Speaker Blackthorn, max 2×/beurt), `conviction`, `saturday_cthuns`, `temporal_tavern`, `wisdom_of_ancients`, `galakronds_greed`, `galaxy_lens`, `efficient_exchange`, `discover_dragon`, `lead_explorer`, `pirate_parrrrty`, `build_an_undead`, `discover_magnetic_mech`, `buried_treasure`; discover-based powers hergebruiken `triple_discover` modal
- **Bugfix**: `game_state.reroll` crashte bij spelcontaining wanneer winkel een spreuk bevatte (`dict.to_dict()` → AttributeError)

## Taal
- **Alle UI-tekst is Nederlands**
- Python commentaar mag ook Nederlands of Engels
- Variabelenamen zijn Engels

## Nog niet geïmplementeerd (stubs)
- **Duos-only**: `loyal_mobster`, `doting_dracthyr`, `support_system`, `dark_dazzler`, `friendly_saloonkeeper`, `gathering_stormer`, `magnanimoose`, `selfless_sightseer`
- `ring_bearer`: combat aanvals-teller → cast Shiny Ring elke 2 aanvallen
- `storm_hammer` rally "geef Beasts deze Rally" (contagious effect)
- `lava_lurker` "eerste twee spellcraft per beurt permanent" per-minion tracking
- Floating Watcher in combat (held-schade mid-combat niet bijgehouden)
- Trinkets (trinkets.py aanwezig maar niet gekoppeld)
- Hero powers nog niet geïmplementeerd: `ill_take_that` (Rafaam), `saturday_cthuns` (C'Thun, vereenvoudigd), `sign_new_artist` (ETC), `imprison`, `friendly_wager`, `i_spy`, en diverse passive-type helden

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