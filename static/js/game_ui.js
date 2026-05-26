// ── GameUI: rendert shop en board met ovale Hearthstone-stijl kaarten ──
const GameUI = {

  renderShop(shopSlots) {
    const container = document.getElementById("shop-slots");
    container.innerHTML = "";
    if (!shopSlots) return;
    shopSlots.forEach((minion, idx) => {
      if (!minion) {
        const empty = document.createElement("div");
        empty.className = "shop-empty-full";
        container.appendChild(empty);
      } else {
        const card = buildShopCard(minion);
        card.dataset.shopIndex = idx;
        card.addEventListener("click", () => SocketClient.buyMinion(idx));
        card.addEventListener("mouseenter", e => showTooltip(minion, e));
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
      container.innerHTML = '<div class="hand-empty-msg">Koop minions — klik om op board te zetten</div>';
      return;
    }
    hand.forEach((minion, idx) => {
      const card = buildShopCard(minion);
      card.dataset.handIndex = idx;

      // Klik = speel naar board
      card.addEventListener("click", () => SocketClient.playFromHand(idx));

      // Drag = kan naar sell-zone gesleept worden
      card.draggable = true;
      card.addEventListener("dragstart", e => {
        e.dataTransfer.setData("hand_index", idx);
        document.getElementById("sell-zone").classList.remove("hidden");
      });
      card.addEventListener("dragend", () => {
        document.getElementById("sell-zone").classList.add("hidden");
      });

      // Rechtsklik = verkoop
      card.addEventListener("contextmenu", e => {
        e.preventDefault();
        if (confirm(`Verkoop ${minion.name} voor 1💰?`)) SocketClient.sellFromHand(idx);
      });

      card.addEventListener("mouseenter", e => showTooltip(minion, e));
      card.addEventListener("mouseleave", hideTooltip);
      card.addEventListener("mousemove", moveTooltip);
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
  const imgUrl   = getCardImageUrl(minion.id);

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
  const imgUrl   = getCardImageUrl(minion.id);

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
    <div class="mc-atk">${minion.attack}</div>
    <div class="mc-hp">${minion.health}</div>
  `;

  return wrapper;
}

// ── Volledige kaart voor winkel (wiki card render) ────────────
function buildShopCard(minion) {
  const wrapper = document.createElement("div");
  wrapper.className = "shop-card-full";
  wrapper.dataset.uid = minion.uid;
  if (minion.golden) wrapper.classList.add("golden");

  const imgUrl   = getCardImageUrl(minion.id);
  const portrait = getPortrait(minion.id);

  const cost = document.createElement("div");
  cost.className = "shop-card-cost";
  cost.textContent = "3💰";
  wrapper.appendChild(cost);

  if (imgUrl) {
    const img = document.createElement("img");
    img.className = "shop-card-full-img";
    img.src = imgUrl;
    img.alt = minion.name;
    img.loading = "lazy";
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
    img.onerror = () => { img.style.display = "none"; fb.style.display = "flex"; };
    wrapper.appendChild(img);
    wrapper.appendChild(fb);
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
    const boardIdx = parseInt(e.dataTransfer.getData("board_index"));
    const handIdx  = parseInt(e.dataTransfer.getData("hand_index"));
    if (!isNaN(boardIdx) && e.dataTransfer.getData("board_index") !== "") SocketClient.sellMinion(boardIdx);
    else if (!isNaN(handIdx) && e.dataTransfer.getData("hand_index") !== "") SocketClient.sellFromHand(handIdx);
  });
});
