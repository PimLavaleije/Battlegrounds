# Hearthstone Battlegrounds Season 13 Mechanics Checklist

Season 13 systems
Trinket offering engine
Special Trinket restrictions
Hand protection
Fodder
Chromadrake
Economy
Combat sequencing
Trigger queue
Golden/triples
Alle tribes
Heroes
Tavern spells
Space constraints
Damage rules
Duos
Regression tests
Claude audit section

# Hearthstone Battlegrounds Season 13 Mechanics Checklist
Gebruik dit als verificatielijst. Markeer per regel:
- TRUE / FALSE / PARTIAL
- Bron of observatie
- Patch-afhankelijk?
- Edge cases?

## 0. Scope
- Game mode: Hearthstone Battlegrounds
- Season: 13, “CATACLYSM CALLS”
- Start: 14 april 2026
- Patchbasis: 35.2 en latere hotfixes/balance patches
- Niet inbegrepen tenzij apart genoemd:
  - Constructed Hearthstone
  - Arena
  - Cosmetics-only systems
  - Oude Anomaly/Quest/Timewarped Tavern-seasons

## 1. Season 13 global systems
- Anomalies zijn uit de Tavern verwijderd.
- Timewarped Tavern is uit de Tavern verwijderd.
- Trinkets zijn het centrale returning seasonal mechanic.
- Elke speler krijgt een Lesser Trinket-aanbieding op Turn 6.
- Elke speler krijgt een Greater Trinket-aanbieding op Turn 9.
- Trinkets worden met Gold gekocht.
- Je kiest maximaal één Trinket per offering.
- Trinkets hebben permanente effecten voor de rest van de game, tenzij de individuele tekst iets anders zegt.
- Trinkets kunnen minion-type-affiliaties hebben.
- Trinkets tonen in Season 13 hun affiliated minion types onderaan de kaart.
- Lesser/Greater-status is zichtbaar via het icoon linksboven op de Trinket.

## 2. Trinket offering engine

### 2.1 Offering moment
- Lesser Trinket offering gebeurt op Turn 6.
- Greater Trinket offering gebeurt op Turn 9.
- Elke offering bevat 4 verschillende Trinkets.
- De speler koopt één aangeboden Trinket met Gold.
- Je kunt geen duplicaat krijgen van een Trinket die je al hebt.
- Uitzondering: als er een Lesser- en Greater-versie van “dezelfde” Trinket bestaan, kun je beide krijgen.

### 2.2 Pool modifiers
De pool van mogelijke Trinkets wordt beïnvloed door:
- Minion types die in de game/lobby aanwezig zijn.
- Minions in je warband.
- Kaarten in je hand.
- Je hero power.
- Specifieke interne Trinket-offering rules.

### 2.3 “In a type”
Een speler is “in” een minion type als:
- Turn 6: je 2 minions van dat type hebt.
- Turn 9: je 3 minions van dat type hebt.
- Je kunt tegelijk “in” meerdere types zijn.
- Meer dan de threshold verhoogt de kans niet verder volgens de officiële uitleg.
- Sommige heroes tellen altijd als “in” een type.
  - Voorbeeld: Azshara heeft altijd toegang tot Naga Trinkets.
- 3 of meer distinct minion types plaatst je “in” Menagerie.
- 3 typeless minions plaatst je “in” No Type.

### 2.4 Guaranteed most-common type
- In elke Trinket offering krijg je altijd minstens één Trinket voor je meest voorkomende type waarin je “in” bent.
- Dit geldt voor Lesser én Greater offerings.
- Als er meerdere meest voorkomende types tied zijn, moet Claude nagaan hoe tie-break intern werkt; officiële tekst zegt alleen “most common type”.

### 2.5 Neutral/no-type guarantees
- Je krijgt altijd minstens één Trinket zonder type.
- Sommige typeless Trinkets zijn vaker aangeboden dan andere:
  - Transcribing Typewriter
  - Goldenizing Supply
  - Reflective Pendant
  - Souvenir Stand
  - Trip Vouchers
  - Colorful Compass
  - Warband Whistle
  - Manipulator Portrait
  - Gold-plated Compass

### 2.6 Cost rules
- De meeste Trinkets kosten 1–4 Gold.
- In elke offering zit minstens één Trinket die 2 Gold of minder kost.
- Als je een Trinket krijgt voor een minion type waarin je niet “in” bent, wordt de kost van die Trinket met 2 verminderd.

### 2.7 Duplicate / restriction rules
- Je kunt geen exact duplicaat aangeboden krijgen van een Trinket die je al bezit.
- Lesser/Greater equivalenten kunnen wel samen bestaan.
- Je krijgt niet meer dan één Trinket voor een minion type dat niet je meest voorkomende type is.
- Je kunt niet meer dan één Menagerie Trinket aangeboden krijgen.

## 3. Special Trinket restrictions

### 3.1 Board-size / board-state gated
- Shrine of Evolution en Sacrificial Altar:
  - Je kunt niet meer dan één van deze twee aangeboden krijgen.
  - Je kunt ze niet aangeboden krijgen tenzij je 6+ minions controleert.
- Lens Case:
  - Niet aangeboden tenzij je een Tier 3-minion controleert.
- Magician’s Top Hat:
  - Niet aangeboden als je 5 of meer minions in hand + board hebt.
- Gilded Anchor:
  - Niet aangeboden tenzij je een Golden minion controleert.
- Divine Signet:
  - Niet aangeboden tenzij je een Divine Shield-minion controleert.
- Tiger Carving:
  - Alleen aangeboden als je Trigore the Lasher, Iridescent Skyblazer, Spiked Savior of Rabid Panther controleert.

### 3.2 Tribe/lobby gated
- Bob-blehead:
  - Niet aangeboden in Demon lobbies.
- Leapfrogger Portrait:
  - Voorbeeld van typed Trinket die alleen aangeboden wordt als je “in” Beasts bent.
- Chromatic Tear:
  - Voorbeeld van typed Dragon Trinket die ook aangeboden kan worden als je niet “in” Dragons bent.

### 3.3 Mechanic-history gated
- Baller Portrait:
  - Alleen aangeboden als je deze game een Baller hebt verkocht.
- Ur’zul Sticker / Flaming Portrait:
  - Niet aangeboden als je deze game de Tavern nog niet hebt gebuffed.
- Murky Sticker:
  - Alleen aangeboden als je meerdere Battlecries hebt getriggerd.
- Dramaloc Sticker:
  - Alleen aangeboden als je een minion met 10+ Attack in hand hebt.
- Fancy Spellbook / Heart of the Forest:
  - Niet aangeboden tenzij je deze game je Tavern Spells hebt gebuffed.
- Herald Sticker / Blood Amulet / Unholy Sanctum / Thornspike Pauldron:
  - Niet aangeboden tenzij je een Deathrattle-minion controleert.

### 3.4 Health/Armor gated
- Safety Patch:
  - Niet aangeboden als je 16+ total Health + Armor hebt.
  - Niet aangeboden in Duos.

### 3.5 Tavern Tier gated
- Scraper Sticker / Beatboxer Portrait:
  - Niet aangeboden als je onder Tavern Tier 3 bent.

### 3.6 Hero-specific restrictions
- Souvenir Stand / Ornate Clock / Trip Vouchers:
  - Niet aangeboden aan Marin of Buttons.
- Cho’Gall Sticker:
  - Niet aangeboden aan Cho of Gall.
- Corrupted Tome:
  - Niet aangeboden aan Mr. Clocksworth.
- Skipper Portrait:
  - Niet aangeboden aan Gallywix of Flurgl.
- Kaleidoscope:
  - Niet aangeboden aan Voone of ETC.
- Goblin Wallet / Bob’s Tip Jar:
  - Niet aangeboden aan Gallywix.
- Fish Portrait:
  - Niet aangeboden aan Greybough.

  ## 4. Hand protection
- Als een Trinket een kaart genereert terwijl je hand vol is, gaat die kaart niet verloren.
- De kaart wacht tot er ruimte is.
- Dit geldt voor alle Trinket-generated cards.
- Claude moet checken:
  - Wordt de kaart in queue gezet?
  - Komt ze direct zodra er handruimte ontstaat?
  - Blijft de volgorde behouden bij meerdere generated cards?
  - Geldt dit ook als meerdere Trinkets tegelijk kaarten genereren?

  ## 5. Fodder — Demon mechanic

### 5.1 Definition
- Fodder-minions worden toegevoegd aan je persoonlijke minion pool.
- Bij Refresh kan een Fodder-minion in de Tavern verschijnen.
- Wanneer dat gebeurt:
  - Een hungry friendly Demon consumeert de Fodder.
  - Die Demon krijgt de Fodder-stats.
  - De Tavern-slot wordt opnieuw gevuld.
- Fodder is dus geen normale koopbare Tavern-minion in de gebruikelijke zin.
- Het is een shop-refresh-consume mechanic.

### 5.2 Te checken edge cases
- Wat gebeurt er zonder friendly Demon?
- Wat gebeurt er met meerdere Demons?
- Hoe wordt gekozen welke Demon consumeert?
- Werkt het met Golden Demons anders?
- Worden buffs op Fodder meegenomen?
- Zijn Fodder-stats permanent?
- Kan Fodder meerdere keren verschijnen?
- Wordt Fodder uit een persoonlijke pool verwijderd na consume?
- Telt consume als “eating”, “gaining stats”, “Tavern buff”, of geen van die keywords?
- Triggeren effects die afgaan op Refresh?
- Triggeren effects die afgaan op minions appearing in Tavern?
- Triggeren effects die afgaan op Tavern buffs?
- Kan een consumed Fodder ooit gekocht/frozen/ge-target worden?
- Als de Tavern vol is, gebeurt refill correct?
- Als Refresh via spell/hero power komt, werkt Fodder hetzelfde?

## 6. Chromadrake — Dragon mechanic

### 6.1 Definition
- Chromadrakes zijn Dragon-related tokens/effects.
- Er zijn vijf Chromadrake-kleuren:
  - Red Chromadrake
  - Bronze Chromadrake
  - Green Chromadrake
  - Black Chromadrake
  - Blue Chromadrake
- Elke Chromadrake heeft een uniek effect.
- Elke Chromadrake helpt Dragons.
- Elke Chromadrake verbetert of beïnvloedt Tavern Spells.

### 6.2 Te checken
- Zijn Chromadrakes minions, generated tokens, spell-generated entities of trinket-linked?
- Kunnen ze golden worden?
- Tellen ze als Dragons voor “in Dragons” Trinket logic?
- Zijn hun effecten aura’s, battlecries, deathrattles, start-of-combat, end-of-turn of passive?
- Werken ze met spellcraft/Tavern Spell modifiers?
- Worden Tavern Spell-buffs permanent of alleen shop-based?
- Hoe stacken meerdere Chromadrakes?
- Hoe stackt golden + non-golden?
- Wat gebeurt bij board vol?
- Wat gebeurt als een Tavern Spell duplicated wordt?

## 7. Economy
- Recruit phase en combat phase wisselen elkaar af.
- Gold groeit per turn volgens Battlegrounds-regels, met cap.
- Gold wordt gebruikt voor:
  - Minions kopen
  - Tavern refreshen
  - Tavern upgraden
  - Hero powers
  - Tavern Spells
  - Trinkets op Turn 6/9
- Unspent Gold draagt normaal niet over tenzij specifieke hero/card/effect dat doet.
- Minions verkopen geeft Gold volgens standaard sell rules.
- Tavern freeze behoudt de shop naar de volgende recruit phase.
- Refresh vervangt normaal de Tavern-aanbieding, tenzij frozen/locked/effect anders zegt.
- Tavern Tier bepaalt welke tiers in je Tavern kunnen verschijnen.
- Upgraden verhoogt Tavern Tier en beïnvloedt shop pool.
- Tavern Spells hebben eigen Tier/pool/prijs/effects.
- Sommige effecten buffen Tavern minions.
- Sommige effecten buffen Tavern Spells.

## 8. Combat basics
- Combat is automatisch.
- Minions vallen normaal van links naar rechts aan.
- Een minion target normaal willekeurig.
- Als er enemy Taunt-minions zijn, moet een attack target onder de Taunts kiezen.
- Divine Shield voorkomt de eerste damage instance op die minion.
- Venomous/Poisonous-achtige destroy effects moeten per actuele Battlegrounds wording gecheckt worden.
- Deathrattles triggeren wanneer minions sterven en hun death event resolved.
- Reborn summon’t een 1-Health versie na death, tenzij tekst anders zegt.
- Summons falen als board vol is.
- Combat buffs zijn meestal tijdelijk, tenzij expliciet permanent.
- Permanent buffs tijdens combat bestaan alleen als kaarttekst dat expliciet maakt.
- Start-of-combat effects resolven vóór eerste aanval.
- End-of-combat cleanup verwijdert tijdelijke summons/buffs/effects.

## 8.1 Attack order
- Linker levende minion die nog in sequence aan de beurt is, valt aan.
- Na uiterst rechts loopt de attack pointer terug naar links.
- Nieuwe summons kunnen in de attack order terechtkomen afhankelijk van positie en huidige pointer.
- Windfury/Mega-Windfury/extra attacks moeten apart per huidige wording gecheckt worden.
- Als een minion sterft vóór zijn aanval, wordt hij overgeslagen.
- Als alle minions van één speler dood zijn, combat eindigt na pending queues.

## 8.2 Targeting
- Taunt forceert attacks naar Taunts.
- Stealth, Immune, Elusive, “can’t be attacked”, of specifieke BG-only modifiers moeten per tekst gecheckt worden.
- Random target selection kan door minions/heroes worden overschreven.
- Cleave/adjacent damage targett primair target plus buren volgens positie op dat moment.
- Als een adjacent target ontbreekt, wordt dat deel niet verplaatst naar ander target.

## 8.3 Damage
- Attack damage en counterattack damage worden gelijktijdig of in Hearthstone sequence-resolutie behandeld.
- Divine Shield voorkomt damage maar niet noodzakelijk “attacked”/“was attacked” triggers.
- Overkill-achtige mechanics bestaan alleen als actief in pool.
- Damage-based triggers moeten checken:
  - on damage dealt
  - on damage taken
  - after attack
  - whenever this attacks
  - after this survives damage
  - after friendly minion loses Divine Shield

  ## 9. Death and trigger handling
- Deathrattles gaan in een queue.
- Meerdere deaths tegelijk kunnen meerdere deathrattles tegelijk queued krijgen.
- Ordering is meestal board-position/order-of-play dependent, maar Claude moet patchspecifiek checken.
- Summon effects vereisen vrije board space.
- Als meerdere summons tegelijk proberen te resolven en er is beperkte space, resolven alleen de eerste die ruimte hebben.
- Deathrattle multipliers kunnen extra triggers veroorzaken.
- “Your first Deathrattle each combat triggers extra” telt alleen de eerste qualifying Deathrattle per combat.
- Deathrattle repeats kunnen met Titus/Rivendare-achtige effecten stacken afhankelijk van huidige card pool.
- Reborn en Deathrattle ordering moet gecheckt worden:
  - Eerst death event.
  - Deathrattle triggers.
  - Reborn summon timing.
  - Summoned minion positioning.
- Minions die tegelijk sterven kunnen nog elkaars “whenever a friendly minion dies” effecten triggeren als ze op dat moment valide zijn.

## 10. Triples and Golden
- Drie copies van dezelfde minion combineren tot een Golden minion.
- Golden minion houdt doorgaans enchantments/stat buffs via Battlegrounds combine rules.
- Triple reward geeft een Discover van een minion uit hogere Tavern Tier dan jouw huidige tier, tot max Tier 6.
- Triple reward kan alleen minions uit actieve lobby/pool aanbieden.
- Golden text is meestal ongeveer dubbel effect, maar niet altijd letterlijk; check kaarttekst.
- Golden minions tellen als één minion op board.
- Golden status telt voor effects die “Golden minion” vereisen.
- Tripling a Dragon telt voor Deathling Pet XP, maar dat is cosmetic/progression, niet combat relevant. 
- Hand triples kunnen automatisch combineren wanneer de derde copy naar hand komt.
- Board triples kunnen combineren wanneer derde copy played/summoned/obtained wordt, afhankelijk van source.
- Token triples en generated copies moeten apart gecheckt worden.

## 11. Tribes

### 11.1 Beasts
Main patterns:
- Summon during combat.
- Deathrattle chains.
- Beast-summon buffs.
- Attack/Health scaling via summoned Beasts.
- Token board-space management.
Check:
- Board full summon failures.
- Deathrattle multiplier interactions.
- Summoned Beast temporary vs permanent buffs.
- Leapfrogger-style effect propagation if present.
- Slamma-style summon stat multiplication if present.

### 11.2 Demons
Main patterns:
- Self-damage / hero Health as resource.
- Tavern consume/eat mechanics.
- Fodder in Season 13.
- Stat gain from consumed minions.
Check:
- Health rewinder effects.
- Armor vs Health payment.
- Fodder targeting.
- Tavern buffs before consume.
- Consume with no valid Demon.
- Consume with multiple valid Demons.
- Effects requiring damaged hero.
- Effects requiring Tavern buff this game.

### 11.3 Dragons
Main patterns:
- Start-of-combat buffs.
- Scaling from Tavern Spells.
- Chromadrake effects.
- Attack-based scaling.
Check:
- Chromadrake stacking.
- Start-of-combat ordering.
- Tavern Spell enhancement persistence.
- Dragon count for Trinket logic.
- Battlecry vs passive Dragon buffs.

### 11.4 Murlocs
Main patterns:
- Battlecries.
- Handbuffs.
- Summons from hand.
- Venomous/Poisonous-style lethality if present.
Check:
- Multiple Battlecry triggers for Murky Sticker eligibility.
- Hand size.
- Buffing leftmost/rightmost/random hand minions.
- Summon-from-hand board-space.
- Deathrattle hand summons.

### 11.5 Mechs
Main patterns:
- Magnetic/Magnetize.
- Divine Shield.
- Deathrattle summons.
- Beatboxer/scraper-style stat copying if present.
Check:
- Magnetic target legality.
- Magnetized stats/effects inheritance.
- Golden magnetic behavior.
- Divine Shield loss triggers.
- Polarizing Beatboxer edge cases.
- Tavern Tier restrictions for Mech Trinkets.

### 11.6 Pirates
Main patterns:
- Gold generation.
- APM economy.
- Attacks during combat.
- Selling/buying loops.
Check:
- Gold cap.
- Generated Gold timing.
- Extra attack ordering.
- Start-of-combat attack triggers.
- Skipper Portrait restrictions for Gallywix/Flurgl.

### 11.7 Elementals
Main patterns:
- Tavern buffing.
- Refresh scaling.
- Playing Elementals for buffs.
- Shop-size/economy loops.
Check:
- “Buffed Tavern this game” eligibility.
- Refresh-trigger ordering.
- Buffed minion consumed by Demon/Fodder interactions.
- Tavern Spell buffs.

### 11.8 Quilboar
Main patterns:
- Blood Gems.
- Blood Gem scaling.
- Deathrattle/Gem application.
- End-of-turn Gem effects.
Check:
- Blood Gem stats display.
- Permanent vs temporary Blood Gem buffs.
- Thornspike Pauldron Deathrattle gating.
- Blood Gem VFX bugs fixed in 35.2.

### 11.9 Naga
Main patterns:
- Spellcraft.
- Temporary Spellcraft buffs.
- Spell generation each turn.
- Azshara is always “in” Naga for Trinket access.
Check:
- Spellcraft doubling.
- Temporary buffs expire at end of turn/combat as written.
- Hand full with generated Spellcraft.
- Tavern Spell vs Spellcraft distinction.

### 11.10 Undead
Main patterns:
- Army-wide Attack scaling.
- Reborn.
- Deathrattle summons.
- Token chains.
Check:
- Reborn timing.
- Aura recalculation.
- Summon board space.
- Deathrattle gating for Trinkets.
- Permanent army Attack vs temporary combat buffs.

### 11.11 Menagerie
Main patterns:
- Multiple distinct minion types.
- “In Menagerie” if 3+ distinct types.
- Cross-tribe buffs.
Check:
- Dual-type minions count rules.
- All-type minions.
- Typeless minions.
- Maximum one Menagerie Trinket offered.

## 12. Heroes

### 12.1 Genn, Worgen King
- Nieuwe Season 13 hero.
- Heeft “King of Duality”.
- Werkt met twee Hero Powers.
Check:
- Wanneer kies/krijg je de twee Hero Powers?
- Zijn ze random, discovered, fixed, rotating?
- Kunnen passives + actives gecombineerd worden?
- Hoe werken cooldowns/costs?
- Trinket restrictions:
  - Niet expliciet genoemd in developer list, dus normale offering rules tenzij later aangepast.

### 12.2 Mister Clocksworth
- Nieuwe Season 13 hero.
- “Double Time”.
- Pushes minions to next upgrade faster.
Check:
- Wat is “upgrade” exact?
- Werkt het met triples?
- Werkt het met Tavern Tier?
- Werkt het met Goldenization?
- Trinket restriction:
  - Corrupted Tome kan niet aan Mr. Clocksworth worden aangeboden.

### 12.3 Existing heroes and Trinket rules
- Azshara:
  - Altijd “in” Naga voor Trinket offering.
- Marin / Buttons:
  - Geen Souvenir Stand, Ornate Clock, Trip Vouchers.
- Cho / Gall:
  - Geen Cho’Gall Sticker.
- Gallywix:
  - Geen Skipper Portrait.
  - Geen Goblin Wallet.
  - Geen Bob’s Tip Jar.
- Flurgl:
  - Geen Skipper Portrait.
- Voone / ETC:
  - Geen Kaleidoscope.
- Greybough:
  - Geen Fish Portrait.

  ## 13. Tavern Spells
- Tavern Spells zijn koopbare shop-items naast minions.
- Tavern Spells kunnen door Chromadrakes worden enhanced.
- Sommige Season 13 Trinkets zijn afhankelijk van Tavern Spell buff history.
- Balinda Stonehearth preview: doubles effects of Spellcrafts, Blood Gems, and Tavern Spells.
Check:
- Tavern Spell cost modifications.
- Tavern Spell duplication.
- Tavern Spell generated cards with hand full.
- Tavern Spell buff persistence.
- Tavern Spell target legality.
- Whether a Tavern Spell counts as “spell” for all effects or only Tavern Spell-specific effects.

## 14. Space constraints
- Board max: 7 minions.
- Hand max: standard Hearthstone hand size unless BG-specific exceptions apply.
- Summons fail if board full.
- Generated Trinket cards wait if hand full.
- Generated non-Trinket cards may or may not wait depending on source; check source-specific text.
- Shop slots refill after Fodder consume.
- Freeze locks current shop contents unless effect says otherwise.
- Minions in hand can count for some Trinket offering restrictions.
- Board + hand count matters for Magician’s Top Hat restriction.

## 15. Persistence
- Recruit-phase stat buffs are usually permanent.
- Combat-phase stat buffs are usually temporary unless explicitly permanent.
- Tavern buffs persist on shop minions as long as source says.
- Buffs on consumed Tavern minions transfer to eater if consume uses current stats.
- Spellcraft buffs are usually temporary unless text says otherwise.
- Blood Gems are usually permanent stat buffs.
- Trinkets are permanent passive/triggered effects after bought.

## 16. Player damage
- After combat, loser takes damage based on surviving enemy board plus Tavern Tier rules.
- Damage cap exists in modern Battlegrounds but exact Season 13 value/conditions must be checked against current patch.
- Ties normally deal no damage.
- Summoned tokens may or may not count based on their Tavern Tier/token tier.
- Hero Armor modifies effective starting survivability.
Check:
- Current Season 13 damage cap.
- Whether cap disables after player death threshold.
- Duos-specific shared Health/damage handling.
- Damage from combat vs damage from effects.

## 17. Duos
- Duos uses teams of two.
- Some Trinkets are restricted differently in Duos.
- Safety Patch cannot be offered in Duos.
- Passing cards/portal mechanics may affect hand/full-hand interactions.
- Team Health and combat order differ from Solos.
Check:
- Trinket timing in Duos.
- Whether both teammates get independent Trinket offerings.
- Whether “your warband” means individual board only.
- Whether teammate board/hand affects Trinket offering.
- Whether generated cards waiting for hand space interact with passing.

## 18. Regression tests from 35.2
- Secret Sinstone copy from Search Through Time should resolve correctly before being added to hand.
- Blood Gem VFX from Glowgullet Warlord should originate correctly.
- Colorful Compass should not always grant Naga.
- Rocking and Rolling Darkmoon Prize should stack.
- Thornspike Pauldron should display correct Blood Gem stats in large card view.
- Golden Darkgaze Elder should show Blood Gem tooltip.
- Splinter of Aurum should trigger.
- Slamma Sticker should not cause summoned Beasts to have 1 Health.
- Alliance Keychain should grant stats based on the first minion that died, not a minion that attacked and died immediately if that is incorrect.
- Murkbrine Expeditioner should grant gained Health if leftmost hand card is a Spell.
- Polarizing Beatboxer should double stats correctly when Timewarped Wargear is magnetized to another minion.