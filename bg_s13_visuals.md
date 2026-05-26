# Hearthstone Battlegrounds Season 13 Visual Specification

# 1. Recruit Phase / Shop Phase / Tavern Phase

## 1.1 Overall Layout

Recruit phase is the non-combat planning phase.

Visual characteristics:

- Wooden tavern background.
- Bob the Bartender visible at the top center.
- Tavern minions shown in the shop row near the top.
- Friendly warband shown in the lower half of the screen.
- Hand cards visible at bottom.
- Gold count visible at bottom-right.
- Turn timer visible on right side.
- Hero portrait visible bottom-center.
- Hero power button near hero portrait.
- Tavern Tier upgrade button near top-left/top-center.
- Refresh/Reroll button visible near Tavern controls.

Recruit phase is identifiable because:
- Shop minions are visible.
- Timer countdown is active.
- Minions are draggable.
- No combat animations are playing.
- Bob’s Tavern UI is visible.

---

## 1.2 Spatial UI Regions

### TOP ZONE — Tavern Shop

Contains:

1. Bob portrait
2. Tavern Tier badge
3. Shop minions
4. Refresh button
5. Tavern upgrade button
6. Seasonal UI elements

Expected visual behavior:

- Shop minions glow blue when buyable.
- Shop minions display:
  - attack
  - health
  - tribe
  - keywords
  - tier gem

- Frozen Tavern:
  - icy/frost overlay on shop row.

- Buffed Tavern:
  - enhanced glow effects on Tavern minions.

Season 13:
- Tavern spells can appear alongside minions.
- Trinket offering appears on Turn 6 and Turn 9 as modal UI.

---

### MIDDLE ZONE — Board / Warband

Contains:

Friendly minions.

Board rules:

- Max 7 minions.
- Ordered left → right.
- Position matters.
- Taunts visually highlighted.
- Divine Shield visible as glowing golden shield.
- Reborn visible via undead-like icon.
- Magnetic merges visually into Mechs.
- Golden minions have animated golden borders.

Recruit phase board behavior:

- Minions can be repositioned.
- Dragging is enabled.
- No attack animations.
- Hover/click reveals enlarged card.

---

### BOTTOM ZONE — Player HUD

Contains:

1. Hero portrait
2. Health
3. Armor
4. Hero power
5. Gold
6. Hand

Visual cues:

Gold:
- Golden coin icons.
- Fraction format:
  current/max

Examples:
3/3
9/10
10/10

Hero power:
- Circular button.
- Lights up when usable.
- Greyed when unavailable.

Hand:
- Cards fan out horizontally.
- Triple rewards appear here.
- Tavern spells appear here.
- Generated cards appear here.

Full hand:
- New generated cards may wait in queue depending on mechanic.

---

### RIGHT SIDE — Timer

Recruit timer:

- Large countdown number.
- Decreases continuously.
- Final seconds visually emphasized.

Expected player interaction:

- Buy
- Sell
- Roll
- Freeze
- Upgrade Tavern
- Cast Tavern Spells
- Play minions
- Rearrange board
- Buy Trinkets

---

## 1.3 Recruit Phase State Detection

Claude should classify a screenshot as Recruit Phase if:

TRUE indicators:
- Shop row visible
- Bob visible
- Timer visible
- Gold visible
- Buyable minions shown
- Dragging enabled

FALSE indicators:
- Attack star effects
- Minions auto-attacking
- Damage explosions
- Opponent board occupying upper combat side

Confidence:
High if ≥4 TRUE indicators visible.

# 2. Combat Phase / Fight Phase

## 2.1 Overall Layout

Combat phase is the automatic battle phase.

Visual characteristics:

- Shop UI hidden.
- Opponent warband appears top side.
- Friendly warband appears bottom side.
- No draggable minions.
- Automatic attack sequencing.
- Combat animations active.

Combat phase identifiable because:

- Both boards visible.
- Minions attacking automatically.
- Damage star bursts visible.
- Health changes visible.
- Shop absent.

---

## 2.2 Spatial UI Regions

### TOP ZONE — Opponent Side

Contains:

1. Enemy hero portrait
2. Enemy hero health
3. Enemy armor
4. Enemy hero power icon
5. Enemy board

Board behavior:

- Enemy minions positioned left → right.
- Keywords visible.
- Golden borders preserved.
- Buff effects shown.

Combat-specific effects:

- Deathrattle VFX
- Summon VFX
- Divine Shield pops
- Venomous/poison indicators
- Taunt highlight

---

### CENTER ZONE — Combat Area

This is where attacks visually resolve.

Indicators:

Attacking minion:
- lunges forward
- attack trail animation
- damage star burst

Damage:
- floating numbers
- star impact graphics

Death:
- explosion/fade effect

Summons:
- portal/summoning animation

Divine Shield:
- golden bubble break

Reborn:
- corpse → immediate reappearance

Deathrattle:
- delayed trigger queue

Combat queue:
- animations occur sequentially.

---

### BOTTOM ZONE — Friendly Side

Contains:

1. Friendly hero portrait
2. Friendly board
3. Hero health
4. Hero power

Important:

- Gold becomes irrelevant.
- Shop hidden.
- Hand usually hidden/non-interactive.
- No dragging.

---

### LEFT SIDEBAR — Lobby State

Contains:

- Remaining players
- Health totals
- Eliminations
- Current opponent highlight

Visual rules:

Alive player:
- portrait visible

Dead player:
- skull indicator

Current opponent:
- highlighted frame

---

## 2.3 Combat State Detection

Claude should classify a screenshot as Combat Phase if:

TRUE indicators:
- Opponent board visible
- Auto attacks occurring
- Shop hidden
- Attack VFX
- Damage stars
- Simultaneous top/bottom boards

FALSE indicators:
- Bob visible
- Buyable minions
- Tavern row
- Roll button
- Upgrade Tavern button

Confidence:
High if ≥4 TRUE indicators visible.

---

## 2.4 Combat Animation Recognition

### Attack event

Visual signs:
- Minion moves forward
- Impact star
- Damage numbers

### Death event

Visual signs:
- Minion disappears
- Death VFX
- Deathrattle trigger may occur

### Summon event

Visual signs:
- New minion materializes
- Empty board slot filled

### Divine Shield trigger

Visual signs:
- Golden protective bubble
- Shield shatter animation

### Reborn trigger

Visual signs:
- Dead minion returns
- Reduced Health

### Cleave attack

Visual signs:
- Multiple minions damaged simultaneously

### Avenge trigger

Visual signs:
- Delayed activation after ally deaths

### Start-of-combat trigger

Visual signs:
- Buffs occur before first attack.

---

## 2.5 Phase Transition

Recruit → Combat:

Visual signs:
- Recruit UI disappears
- Combat banner appears
- Opponent board loads

Combat → Recruit:

Visual signs:
- Damage result shown
- Board fades
- Bob Tavern returns
- Shop minions generated
- Gold restored
- Timer begins