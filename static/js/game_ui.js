// ── GameUI: rendert shop en board met ovale Hearthstone-stijl kaarten ──
const GameUI = {

  renderShop(shopSlots) {
    const container = document.getElementById("shop-slots");
    container.innerHTML = "";
    if (!shopSlots) return;
    shopSlots.forEach((minion, idx) => {
      if (!minion) {
        const empty = document.createElement("div");
        empty.className = "shop-empty";
        empty.textContent = "—";
        container.appendChild(empty);
      } else {
        const card = buildOvalCard(minion, "shop");
        card.dataset.shopIndex = idx;

        // Kostprijs label
        const cost = document.createElement("div");
        cost.className = "shop-card-cost";
        cost.textContent = "3💰";
        card.appendChild(cost);

        card.addEventListener("click", () => SocketClient.buyMinion(idx));
        card.addEventListener("mouseenter", e => showTooltip(minion, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
        container.appendChild(card);
      }
    });
  },

  renderBoard(board) {
    const container = document.getElementById("board-slots");
    container.innerHTML = "";
    const count = board ? board.length : 0;

    for (let i = 0; i < 7; i++) {
      if (board && board[i]) {
        const minion = board[i];
        const card = buildOvalCard(minion, "board");
        card.dataset.boardIndex = i;

        // Drag & drop
        card.draggable = true;
        card.addEventListener("dragstart", e => {
          e.dataTransfer.setData("board_index", i);
          document.getElementById("sell-zone").classList.remove("hidden");
        });
        card.addEventListener("dragend", () => {
          document.getElementById("sell-zone").classList.add("hidden");
        });

        // Rechtsklik = verkopen
        card.addEventListener("contextmenu", e => {
          e.preventDefault();
          if (confirm(`Verkoop ${minion.name} voor 1💰?`)) {
            SocketClient.sellMinion(i);
          }
        });

        card.addEventListener("mouseenter", e => showTooltip(minion, e));
        card.addEventListener("mouseleave", hideTooltip);
        card.addEventListener("mousemove", moveTooltip);
        container.appendChild(card);
      } else {
        const empty = document.createElement("div");
        empty.className = "board-empty-slot";
        empty.dataset.slotIndex = i;
        empty.textContent = "+";

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
        container.appendChild(empty);
      }
    }
    document.getElementById("board-count").textContent = `(${count}/7)`;
  },
};

// ── Bouw een kaart op basis van de echte BG kaartafbeelding ──
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
  const imgUrl   = getCardImageUrl(minion.id);
  const imgHtml  = imgUrl
    ? `<img class="card-full-img" src="${imgUrl}" alt="${escapeHtml(minion.name)}" loading="lazy"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
    : "";

  wrapper.innerHTML = `
    ${imgHtml}
    <div class="card-fallback" style="display:${imgUrl ? "none" : "flex"}">
      <span class="card-fallback-emoji">${portrait.emoji}</span>
      <span class="card-fallback-name">${escapeHtml(minion.name)}</span>
    </div>
    <div class="mc-atk">${minion.attack}</div>
    <div class="mc-hp">${minion.health}</div>
  `;

  return wrapper;
}

// ── Combat-versie van de kaart (iets kleiner) ────────────────
function buildCombatCard(minion) {
  const wrapper = document.createElement("div");
  wrapper.className = "combat-minion";
  wrapper.dataset.uid = minion.uid;

  if (minion.golden)        wrapper.classList.add("golden");
  if (minion.taunt)         wrapper.classList.add("taunt-ring");
  if (minion.divine_shield) wrapper.classList.add("divine-glow");

  const portrait = getPortrait(minion.id);
  const imgUrl   = getCardImageUrl(minion.id);
  const imgHtml  = imgUrl
    ? `<img class="card-full-img" src="${imgUrl}" alt="${escapeHtml(minion.name)}" loading="lazy"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
    : "";

  wrapper.innerHTML = `
    ${imgHtml}
    <div class="card-fallback" style="display:${imgUrl ? "none" : "flex"}">
      <span class="card-fallback-emoji">${portrait.emoji}</span>
      <span class="card-fallback-name">${escapeHtml(minion.name)}</span>
    </div>
    <div class="mc-atk">${minion.attack}</div>
    <div class="mc-hp">${minion.health}</div>
  `;

  return wrapper;
}

// ── Tooltip ──────────────────────────────────────────────────
function showTooltip(minion, e) {
  const tip = document.getElementById("minion-tooltip");
  const kws = [];
  if (minion.taunt)         kws.push("Taunt");
  if (minion.divine_shield) kws.push("Goddelijk Schild");
  if (minion.reborn)        kws.push("Herboren");
  if (minion.poisonous)     kws.push("Giftig");
  if (minion.windfury)      kws.push("Windtoom");
  if (minion.cleave)        kws.push("Cleave");
  if (minion.deathrattle)   kws.push("Sterf-effect");

  tip.innerHTML = `
    <div class="tip-name">${escapeHtml(minion.name)}${minion.golden ? " ✨" : ""}</div>
    <div class="tip-tribe">${minion.tribe || "Neutraal"} · Tier ${minion.tier}</div>
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
    const idx = parseInt(e.dataTransfer.getData("board_index"));
    if (!isNaN(idx)) SocketClient.sellMinion(idx);
  });
});
