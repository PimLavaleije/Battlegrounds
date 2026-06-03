// ── Spell targeting state (vanuit hand) ──────────────────────
const SpellTarget = {
  active: false,
  handIndex: null,
  start(handIndex) {
    this.active = true;
    this.handIndex = handIndex;
    document.getElementById("board-slots").classList.add("spell-targeting");
    showNotification("Click a minion on your board to target the spell. (Esc = cancel)", 30000);
  },
  cancel() {
    this.active = false;
    this.handIndex = null;
    document.getElementById("board-slots").classList.remove("spell-targeting");
    hideTooltip();
    document.getElementById("global-notification")?.classList.add("hidden");
  },
  confirm(boardIndex) {
    const idx = this.handIndex;
    this.cancel();
    SocketClient.playFromHand(idx, boardIndex);
  },
};

// ── Magnetic targeting state ──────────────────────────────────────────
const MagnetizeTarget = {
  active: false,
  handIndex: null,
  itemTypes: null,
  start(handIndex, itemTypes) {
    this.active = true;
    this.handIndex = handIndex;
    this.itemTypes = itemTypes;
    document.getElementById("board-slots").classList.add("magnetize-targeting");
    GameUI.renderBoard(State.player?.board);
    showNotification("Click a compatible minion to Magnetize. (Esc = play standalone)", 30000);
  },
  cancel() {
    this.active = false;
    this.handIndex = null;
    this.itemTypes = null;
    document.getElementById("board-slots").classList.remove("magnetize-targeting");
    hideTooltip();
    document.getElementById("global-notification")?.classList.add("hidden");
    GameUI.renderBoard(State.player?.board);
  },
  confirm(boardIndex) {
    const idx = this.handIndex;
    this.cancel();
    SocketClient.magnetize(idx, boardIndex);
  },
};

// ── GameUI: rendert shop en board met ovale Hearthstone-stijl kaarten ──
const GameUI = {

  renderShop(shopSlots) {
    const container = document.getElementById("shop-slots");
    container.innerHTML = "";
    if (!shopSlots) return;
    shopSlots.forEach((item, idx) => {
      if (!item) {
        const empty = document.createElement("div");
        empty.className = "shop-empty-full";
        container.appendChild(empty);
      } else if (item.type === "spell") {
        const card = buildSpellCard(item);
        card.dataset.shopIndex = idx;
        card.style.animationDelay = `${idx * 50}ms`;
        card.classList.add("anim-card-appear");
        card.addEventListener("click", () => SocketClient.buyMinion(idx));
        card.addEventListener("mouseenter", e => showSpellTooltip(item, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
        container.appendChild(card);
      } else {
        const card = buildShopCard(item);
        card.dataset.shopIndex = idx;
        card.style.animationDelay = `${idx * 50}ms`;
        card.classList.add("anim-card-appear");
        card.addEventListener("click", () => SocketClient.buyMinion(idx));
        card.addEventListener("mouseenter", e => showTooltip(item, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
        container.appendChild(card);
      }
    });
  },

  renderHand(hand) {
    const container = document.getElementById("hand-slots");
    if (!container) return;
    container.innerHTML = "";
    if (!hand || hand.length === 0) {
      container.innerHTML = '<div class="hand-empty-msg">Buy minions — click to play to board</div>';
      return;
    }
    hand.forEach((item, idx) => {
      let card;
      if (item.type === "spell") {
        card = buildSpellCard(item);
        card.addEventListener("click", () => {
          if (item.targeted && State.player?.board?.length > 0) {
            SpellTarget.start(idx);
          } else {
            SocketClient.playFromHand(idx);
          }
        });
        card.addEventListener("mouseenter", e => showSpellTooltip(item, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
      } else if (item.type === "blood_gem") {
        card = buildBloodGemCard(item);
        card.dataset.handIndex = idx;
        card.addEventListener("click", () => {
          if (State.player?.board?.length > 0) {
            SpellTarget.start(idx);
          }
        });
        card.addEventListener("mouseenter", e => showBloodGemTooltip(item, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
      } else {
        card = buildShopCard(item, { showCost: false });
        card.dataset.handIndex = idx;

        card.addEventListener("click", () => {
          const isMagnetic = item.abilities?.includes('magnetic');
          const hasTarget = isMagnetic && State.player?.board?.some(
            m => m && item.types?.some(t => m.types?.includes(t))
          );
          if (isMagnetic && hasTarget) {
            MagnetizeTarget.start(idx, item.types);
          } else {
            SocketClient.playFromHand(idx);
          }
        });

        card.draggable = true;
        card.addEventListener("dragstart", e => {
          e.dataTransfer.setData("hand_index", idx);
          document.getElementById("sell-zone").classList.remove("hidden");
        });
        card.addEventListener("dragend", () => {
          document.getElementById("sell-zone").classList.add("hidden");
        });

        card.addEventListener("contextmenu", e => {
          e.preventDefault();
          if (confirm(`Sell ${item.name} for 1💰?`)) SocketClient.sellFromHand(idx);
        });

        const passCost = (State.player?.pass_free_available > 0) ? 0 : 1;
        const passBtn = document.createElement('div');
        passBtn.className = 'hand-pass-btn';
        passBtn.textContent = `📤 ${passCost}💰`;
        passBtn.title = 'Pass to random opponent';
        passBtn.addEventListener('click', e => {
          e.stopPropagation();
          SocketClient.passMinion(idx);
        });
        card.appendChild(passBtn);

        card.addEventListener("mouseenter", e => showTooltip(item, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
      }
      container.appendChild(card);
    });
  },

  renderBoard(board) {
    const container = document.getElementById("board-slots");
    container.innerHTML = "";
    const count = board ? board.length : 0;

    for (let i = 0; i < 7; i++) {
      if (board && board[i]) {
        const minion = board[i];
        const card = buildShopCard(minion, { showCost: false });
        card.dataset.boardIndex = i;

        if (!State.inCombat) {
          const isValidMagTarget = MagnetizeTarget.active &&
            minion.types?.some(t => MagnetizeTarget.itemTypes?.includes(t));
          if (isValidMagTarget) card.classList.add('magnetize-target');

          card.addEventListener("click", e => {
            if (MagnetizeTarget.active) {
              e.stopPropagation();
              if (isValidMagTarget) MagnetizeTarget.confirm(i);
              else MagnetizeTarget.cancel();
              return;
            }
            if (SpellTarget.active) {
              e.stopPropagation();
              SpellTarget.confirm(i);
            }
          });

          // Drag starten (voor verkopen of herschikken)
          card.draggable = true;
          card.addEventListener("dragstart", e => {
            e.dataTransfer.setData("board_index", i);
            document.getElementById("sell-zone").classList.remove("hidden");
          });
          card.addEventListener("dragend", () => {
            document.getElementById("sell-zone").classList.add("hidden");
          });

          // Drop op een gevulde slot = herschikken
          card.addEventListener("dragover", e => {
            e.preventDefault();
            card.classList.add("drag-over");
          });
          card.addEventListener("dragleave", () => card.classList.remove("drag-over"));
          card.addEventListener("drop", e => {
            e.preventDefault();
            card.classList.remove("drag-over");
            const from = parseInt(e.dataTransfer.getData("board_index"));
            if (!isNaN(from) && from !== i) SocketClient.moveMinion(from, i);
          });

          // Rechtsklik = verkopen
          card.addEventListener("contextmenu", e => {
            e.preventDefault();
            if (SpellTarget.active) { SpellTarget.cancel(); return; }
            if (confirm(`Verkoop ${minion.name} voor 1💰?`)) {
              SocketClient.sellMinion(i);
            }
          });
        }

        card.addEventListener("mouseenter", e => showTooltip(minion, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
        container.appendChild(card);
      } else {
        const empty = document.createElement("div");
        empty.className = "board-empty-slot";
        empty.dataset.slotIndex = i;
        empty.textContent = "+";

        if (!State.inCombat) {
          empty.addEventListener("dragover", e => {
            e.preventDefault();
            empty.classList.add("drag-over");
          });
          empty.addEventListener("dragleave", () => empty.classList.remove("drag-over"));
          empty.addEventListener("drop", e => {
            e.preventDefault();
            empty.classList.remove("drag-over");
            const from = parseInt(e.dataTransfer.getData("board_index"));
            if (!isNaN(from) && from !== i) SocketClient.moveMinion(from, i);
          });
        }
        container.appendChild(empty);
      }
    }
    document.getElementById("board-count").textContent = `(${count}/7)`;
  },
};

// ── Keyword SVG icons ────────────────────────────────────────
const KW_SVG = {
  // Divine Shield – gouden schild met middenkruis
  ds: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 1.5L13.5 4V9C13.5 12.5 8 14.5 8 14.5S2.5 12.5 2.5 9V4L8 1.5Z"
          stroke="#ffe860" stroke-width="1.4" fill="rgba(255,232,96,0.12)"/>
    <path d="M8 5.5V10.5M5.5 8H10.5" stroke="#ffe860" stroke-width="1.3" stroke-linecap="round"/>
  </svg>`,

  // Windfury – twee gebogen windstrepen
  wf: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2.5 5.5Q8 3 13.5 5.5" stroke="#7ab4ff" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M2.5 10.5Q8 8 13.5 10.5" stroke="#7ab4ff" stroke-width="1.8" stroke-linecap="round"/>
  </svg>`,

  // Mega-Windfury – drie windstrepen
  mwf: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 4Q8 2 14 4"   stroke="#60aaff" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M2 8Q8 6 14 8"   stroke="#60aaff" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M2 12Q8 10 14 12" stroke="#60aaff" stroke-width="1.5" stroke-linecap="round"/>
  </svg>`,

  // Reborn – kleine kroon
  rb: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 12V7L5 10L8 3.5L11 10L14 7V12H2Z"
          stroke="#6de87a" stroke-width="1.4" stroke-linejoin="round" fill="rgba(109,232,122,0.12)"/>
    <circle cx="2" cy="7"  r="1.1" fill="#6de87a"/>
    <circle cx="8" cy="3.5" r="1.1" fill="#6de87a"/>
    <circle cx="14" cy="7" r="1.1" fill="#6de87a"/>
  </svg>`,

  // Poisonous – gifdruppel
  psn: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 1.5Q12.5 7 12.5 10A4.5 4.5 0 0 1 3.5 10Q3.5 7 8 1.5Z"
          stroke="#5de05d" stroke-width="1.4" fill="rgba(93,224,93,0.15)"/>
    <circle cx="6.2" cy="9.5" r="0.9" fill="#5de05d"/>
    <circle cx="9.8" cy="9.5" r="0.9" fill="#5de05d"/>
    <path d="M6.2 11.5H9.8" stroke="#5de05d" stroke-width="1.1" stroke-linecap="round"/>
  </svg>`,

  // Deathrattle – schedel
  dr: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 2C4.5 2 3 4.5 3 7C3 9.5 4.5 10.5 4.5 12.5H11.5C11.5 10.5 13 9.5 13 7C13 4.5 11.5 2 8 2Z"
          stroke="#c06ee0" stroke-width="1.4" fill="rgba(192,110,224,0.12)"/>
    <circle cx="6" cy="7.2" r="1.3" fill="#c06ee0"/>
    <circle cx="10" cy="7.2" r="1.3" fill="#c06ee0"/>
    <path d="M5.5 11.5V13M8 11.5V13M10.5 11.5V13" stroke="#c06ee0" stroke-width="1.2" stroke-linecap="round"/>
  </svg>`,

  // Cleave – bijl
  clv: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <line x1="4.5" y1="13.5" x2="10.5" y2="4.5" stroke="#e08050" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M10.5 4.5C12 2.5 15 3 13.5 6.5C12.5 8.5 10 8 10.5 4.5Z"
          fill="#e08050" stroke="#e08050" stroke-width="0.5" stroke-linejoin="round"/>
  </svg>`,

  // Taunt – schild met uitroepteken
  taunt: `<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 1.5L13.5 4V9C13.5 12.5 8 14.5 8 14.5S2.5 12.5 2.5 9V4L8 1.5Z"
          stroke="#d4a820" stroke-width="1.4" fill="rgba(212,168,32,0.15)"/>
    <line x1="8" y1="5.5" x2="8" y2="9.5" stroke="#d4a820" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="8" cy="11.5" r="0.9" fill="#d4a820"/>
  </svg>`,
};

// ── Keyword-icons helper ─────────────────────────────────────
function buildKeywordIcons(minion) {
  const icons = [];
  if (minion.taunt)
    icons.push(`<span class="kw kw-taunt" title="Taunt">${KW_SVG.taunt}</span>`);
  if (minion.divine_shield)
    icons.push(`<span class="kw kw-ds" title="Divine Shield">${KW_SVG.ds}</span>`);
  if (minion.megawindfury)
    icons.push(`<span class="kw kw-mwf" title="Mega-Windfury">${KW_SVG.mwf}</span>`);
  else if (minion.windfury)
    icons.push(`<span class="kw kw-wf" title="Windfury">${KW_SVG.wf}</span>`);
  if (minion.reborn)
    icons.push(`<span class="kw kw-rb" title="Reborn">${KW_SVG.rb}</span>`);
  if (minion.poisonous || minion.venomous)
    icons.push(`<span class="kw kw-psn" title="Poisonous">${KW_SVG.psn}</span>`);
  if (minion.deathrattle)
    icons.push(`<span class="kw kw-dr" title="Deathrattle">${KW_SVG.dr}</span>`);
  if (minion.cleave)
    icons.push(`<span class="kw kw-clv" title="Cleave">${KW_SVG.clv}</span>`);
  return icons.join("");
}

// ── Bouw een oval portret-kaart (Hearthstone BG stijl) ──────
function buildOvalCard(minion, context) {
  const isShop = context === "shop";
  const wrapper = document.createElement("div");
  wrapper.className = isShop ? "shop-card" : "minion-card";
  wrapper.dataset.uid = minion.uid;

  if (minion.golden)        wrapper.classList.add("golden");
  if (minion.taunt)         wrapper.classList.add("taunt-ring");
  if (minion.divine_shield) wrapper.classList.add("divine-glow");
  if (minion.health <= 1 && !isShop) wrapper.classList.add("low-hp");

  const portrait = getPortrait(minion.id);
  const imgUrl   = getCardImageUrl(minion.id, !!minion.golden);
  const kwIcons  = buildKeywordIcons(minion);
  const shortName = minion.name.length > 12 ? minion.name.slice(0, 11) + "…" : minion.name;

  wrapper.innerHTML = `
    <div class="mc-portrait">
      ${imgUrl
        ? `<img class="mc-portrait-img" src="${imgUrl}" alt="${escapeHtml(minion.name)}" loading="lazy"
               onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
        : ""}
      <div class="mc-portrait-fallback" style="display:${imgUrl ? "none" : "flex"}">
        <span>${portrait.emoji}</span>
      </div>
    </div>
    ${kwIcons ? `<div class="mc-keywords">${kwIcons}</div>` : ""}
    <div class="mc-name">${escapeHtml(shortName)}</div>
    <div class="mc-atk">${minion.attack}</div>
    <div class="mc-hp">${minion.health}</div>
  `;

  return wrapper;
}

// ── Combat-versie van de kaart ────────────────────────────────
function buildCombatCard(minion) {
  const wrapper = document.createElement("div");
  wrapper.className = "combat-minion";
  wrapper.dataset.uid = minion.uid;

  if (minion.golden)        wrapper.classList.add("golden");
  if (minion.taunt)         wrapper.classList.add("taunt-ring");
  if (minion.divine_shield) wrapper.classList.add("divine-glow");

  const portrait = getPortrait(minion.id);
  const imgUrl   = getCardImageUrl(minion.id, !!minion.golden);
  const kwIcons  = buildKeywordIcons(minion);

  wrapper.innerHTML = `
    <div class="mc-portrait">
      ${imgUrl
        ? `<img class="mc-portrait-img" src="${imgUrl}" alt="${escapeHtml(minion.name)}" loading="lazy"
               onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
        : ""}
      <div class="mc-portrait-fallback" style="display:${imgUrl ? "none" : "flex"}">
        <span>${portrait.emoji}</span>
      </div>
    </div>
    ${kwIcons ? `<div class="mc-keywords">${kwIcons}</div>` : ""}
    <div class="mc-atk">${minion.attack}</div>
    <div class="mc-hp">${minion.health}</div>
  `;

  return wrapper;
}

// ── Volledige kaart voor winkel (wiki card render) ────────────
function buildShopCard(minion, opts = {}) {
  const { showCost = true } = opts;
  const wrapper = document.createElement("div");
  wrapper.className = "shop-card-full";
  wrapper.dataset.uid = minion.uid;
  if (minion.golden)        wrapper.classList.add("golden");
  if (minion.taunt)         wrapper.classList.add("taunt-outline");
  if (minion.divine_shield) wrapper.classList.add("divine-outline");

  const imgUrl   = getCardImageUrl(minion.id, !!minion.golden);
  const portrait = getPortrait(minion.id);

  if (showCost) {
    const cost = document.createElement("div");
    cost.className = "shop-card-cost";
    cost.textContent = "3💰";
    wrapper.appendChild(cost);
  }

  if (imgUrl) {
    const img = document.createElement("img");
    img.className = "shop-card-full-img";
    img.src = imgUrl;
    img.alt = minion.name;
    img.loading = "lazy";
    img.draggable = false;
    const fb = document.createElement("div");
    fb.className = "shop-card-full-fb";
    fb.style.display = "none";
    fb.innerHTML = `
      <div class="sfb-emoji">${portrait.emoji}</div>
      <div class="sfb-name">${escapeHtml(minion.name)}</div>
      <div class="sfb-stats">
        <div class="sfb-atk">${minion.attack}</div>
        <div class="sfb-hp">${minion.health}</div>
      </div>`;
    img.onerror = () => { img.style.display = "none"; fb.style.display = "flex"; atkBadge.style.display = "none"; hpBadge.style.display = "none"; };
    wrapper.appendChild(img);
    wrapper.appendChild(fb);
    // Stat overlays covering the baked-in stats in the card image
    const atkBadge = document.createElement("div");
    atkBadge.className = "sfc-atk";
    atkBadge.textContent = minion.attack;
    const hpBadge = document.createElement("div");
    hpBadge.className = "sfc-hp";
    hpBadge.textContent = minion.health;
    wrapper.appendChild(atkBadge);
    wrapper.appendChild(hpBadge);
    // Keyword icons row over image
    const kwIcons = buildKeywordIcons(minion);
    if (kwIcons) {
      const kwRow = document.createElement("div");
      kwRow.className = "sfc-keywords";
      kwRow.innerHTML = kwIcons;
      wrapper.appendChild(kwRow);
    }
  } else {
    const fb = document.createElement("div");
    fb.className = "shop-card-full-fb";
    fb.innerHTML = `
      <div class="sfb-emoji">${portrait.emoji}</div>
      <div class="sfb-name">${escapeHtml(minion.name)}</div>
      <div class="sfb-stats">
        <div class="sfb-atk">${minion.attack}</div>
        <div class="sfb-hp">${minion.health}</div>
      </div>`;
    wrapper.appendChild(fb);
  }

  return wrapper;
}

// ── Blood Gem kaart ──────────────────────────────────────────
function buildBloodGemCard(gem) {
  const wrapper = document.createElement("div");
  wrapper.className = "blood-gem-card";
  wrapper.dataset.uid = gem.id;
  const fb = document.createElement("div");
  fb.className = "spell-card-fb";
  fb.innerHTML = `
    <div class="sfb-emoji">💎</div>
    <div class="sfb-name">${escapeHtml(gem.name)}</div>
    <div class="bgem-desc">${escapeHtml(gem.description || '+1/+1')}</div>`;
  wrapper.appendChild(fb);
  return wrapper;
}

// ── Spreuk kaart ─────────────────────────────────────────────
function buildSpellCard(spell) {
  const wrapper = document.createElement("div");
  wrapper.className = "spell-card-full";
  wrapper.dataset.uid = spell.id;

  const cost = document.createElement("div");
  cost.className = "shop-card-cost";
  cost.textContent = `${spell.cost != null ? spell.cost : 3}💰`;
  wrapper.appendChild(cost);

  const portrait = SPELL_PORTRAITS[spell.id] || { emoji: "✨" };
  const fb = document.createElement("div");
  fb.className = "spell-card-fb";
  fb.innerHTML = `
    <div class="sfb-emoji">${portrait.emoji}</div>
    <div class="sfb-name">${escapeHtml(spell.name)}</div>
    <div class="spell-tier-badge">T${spell.tier}</div>`;
  wrapper.appendChild(fb);

  return wrapper;
}

function showSpellTooltip(spell, e) {
  const tip = document.getElementById("minion-tooltip");
  tip.innerHTML = `
    <div class="tip-name">✨ ${escapeHtml(spell.name)}</div>
    <div class="tip-tribe">Spell · Tier ${spell.tier}</div>
    ${spell.description ? `<div class="tip-desc">${escapeHtml(spell.description)}</div>` : ""}
  `;
  tip.classList.remove("hidden");
  moveTooltip(e);
}

function showBloodGemTooltip(gem, e) {
  const tip = document.getElementById("minion-tooltip");
  tip.innerHTML = `
    <div class="tip-name">💎 ${escapeHtml(gem.name)}</div>
    <div class="tip-tribe">Free · Click a board minion</div>
    ${gem.description ? `<div class="tip-desc">${escapeHtml(gem.description)}</div>` : ""}
  `;
  tip.classList.remove("hidden");
  moveTooltip(e);
}

// ── Tooltip ──────────────────────────────────────────────────
function showTooltip(minion, e) {
  const tip = document.getElementById("minion-tooltip");
  const kws = [];
  if (minion.taunt)         kws.push("Taunt");
  if (minion.divine_shield) kws.push("Divine Shield");
  if (minion.reborn)        kws.push("Reborn");
  if (minion.poisonous)     kws.push("Poisonous");
  if (minion.windfury)      kws.push("Windfury");
  if (minion.cleave)        kws.push("Cleave");
  if (minion.deathrattle)   kws.push("Deathrattle");

  tip.innerHTML = `
    <div class="tip-name">${escapeHtml(minion.name)}${minion.golden ? " ✨" : ""}</div>
    <div class="tip-tribe">${minion.tribe || "Neutral"} · Tier ${minion.tier}</div>
    <div class="tip-stats">
      <span class="atk">⚔️ ${minion.attack}</span>
      <span class="hp">❤️ ${minion.health}</span>
    </div>
    ${kws.length ? `<div class="tip-kws">${kws.join(" · ")}</div>` : ""}
    ${minion.description ? `<div class="tip-desc">${escapeHtml(minion.description)}</div>` : ""}
  `;
  tip.classList.remove("hidden");
  moveTooltip(e);
}

function hideTooltip() {
  document.getElementById("minion-tooltip").classList.add("hidden");
}

function moveTooltip(e) {
  const tip = document.getElementById("minion-tooltip");
  const x = Math.min(e.clientX + 14, window.innerWidth  - tip.offsetWidth  - 8);
  const y = Math.min(e.clientY - 10, window.innerHeight - tip.offsetHeight - 8);
  tip.style.left = x + "px";
  tip.style.top  = y + "px";
}

// ── Sell zone drag events ─────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const sz = document.getElementById("sell-zone");
  if (!sz) return;
  sz.addEventListener("dragover",  e => { e.preventDefault(); sz.classList.add("drag-over"); });
  sz.addEventListener("dragleave", ()   => sz.classList.remove("drag-over"));
  sz.addEventListener("drop", e => {
    e.preventDefault();
    sz.classList.remove("drag-over");
    sz.classList.add("hidden");
    const boardIdx = parseInt(e.dataTransfer.getData("board_index"));
    const handIdx  = parseInt(e.dataTransfer.getData("hand_index"));
    if (!isNaN(boardIdx) && e.dataTransfer.getData("board_index") !== "") SocketClient.sellMinion(boardIdx);
    else if (!isNaN(handIdx) && e.dataTransfer.getData("hand_index") !== "") SocketClient.sellFromHand(handIdx);
  });
});
