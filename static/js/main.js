// ── Globale state ────────────────────────────────────────────
const State = {
  playerName: "", roomCode: "", isHost: false, mySid: null,
  player: null, opponents: [], roundNum: 0,
  shopTimer: null, heroTimer: null,
  inCombat: false,
};

// ── Scherm beheer ────────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

// ── Meldingen ────────────────────────────────────────────────
function showNotification(msg, ms = 3000) {
  const el = document.getElementById("global-notification");
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), ms);
}
function showElimination(name) {
  const el = document.getElementById("elimination-toast");
  el.textContent = `💀 ${name} is uitgeschakeld!`;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4000);
}
function showRoundBanner(text) {
  document.querySelector(".round-banner")?.remove();
  const div = document.createElement("div");
  div.className = "round-banner";
  div.innerHTML = `<div class="round-banner-text">${text}</div>`;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 1800);
}

// ── Landing ──────────────────────────────────────────────────
document.getElementById("btn-create").addEventListener("click", () => {
  const name = document.getElementById("input-name").value.trim();
  if (!name) { showLandingError("Voer een naam in."); return; }
  State.playerName = name;
  SocketClient.createLobby(name);
});
document.getElementById("btn-join-open").addEventListener("click", () => {
  document.getElementById("join-form").classList.toggle("hidden");
});
document.getElementById("btn-join-confirm").addEventListener("click", () => {
  const name = document.getElementById("input-name").value.trim();
  const code = document.getElementById("input-room").value.trim().toUpperCase();
  if (!name) { showLandingError("Voer een naam in."); return; }
  if (code.length !== 4) { showLandingError("Voer een geldige 4-letter code in."); return; }
  State.playerName = name;
  SocketClient.joinLobby(name, code);
});
document.getElementById("input-room").addEventListener("input", e => {
  e.target.value = e.target.value.toUpperCase();
});
function showLandingError(msg) {
  const el = document.getElementById("landing-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

// ── Lobby ─────────────────────────────────────────────────────
document.getElementById("btn-start").addEventListener("click", () => SocketClient.startGame());

function renderLobby(data) {
  State.roomCode = data.room_code;
  document.getElementById("lobby-code").textContent = data.room_code;
  const list = document.getElementById("lobby-players");
  list.innerHTML = "";
  data.players.forEach(p => {
    const div = document.createElement("div");
    div.className = "player-item";
    div.innerHTML = `<span>${p.is_host ? "👑" : "👤"}</span>
      <span>${escapeHtml(p.name)}</span>
      ${p.is_host ? '<span class="host-badge">HOST</span>' : ""}`;
    list.appendChild(div);
  });
  const isHost = data.host_sid === State.mySid;
  State.isHost = isHost;
  document.getElementById("btn-start").style.display   = isHost ? "block" : "none";
  document.getElementById("waiting-msg").style.display = isHost ? "none"  : "block";
  showScreen("screen-lobby");
}

// ── Hero selectie ─────────────────────────────────────────────
function renderHeroSelection(heroes, timeout) {
  showScreen("screen-hero-select");
  const container = document.getElementById("hero-cards");
  container.innerHTML = "";
  heroes.forEach(hero => {
    const card = document.createElement("div");
    card.className = "hero-card";
    const imgUrl = getHeroImageUrl(hero.id);
    card.innerHTML = `
      <div class="hero-card-portrait">
        ${imgUrl
          ? `<img src="${imgUrl}" alt="${escapeHtml(hero.name)}" loading="lazy"
                  onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
             <span class="hero-card-emoji" style="display:none">${hero.emoji || "⚔️"}</span>`
          : `<span class="hero-card-emoji">${hero.emoji || "⚔️"}</span>`
        }
      </div>
      <div class="hero-card-name">${escapeHtml(hero.name)}</div>
      <div class="hero-card-desc">${escapeHtml(hero.description)}</div>
    `;
    card.addEventListener("click", () => {
      clearInterval(State.heroTimer);
      SocketClient.selectHero(hero.id);
      showNotification(`Held geselecteerd: ${hero.name}`);
      document.querySelectorAll(".hero-card").forEach(c => c.style.opacity = "0.5");
      card.style.opacity = "1";
      card.style.borderColor = "var(--gold)";
    });
    container.appendChild(card);
  });
  // Countdown timer
  const fill = document.getElementById("hero-timer-fill");
  let remaining = timeout;
  fill.style.width = "100%";
  State.heroTimer = setInterval(() => {
    remaining--;
    fill.style.width = (remaining / timeout * 100) + "%";
    if (remaining <= 0) {
      clearInterval(State.heroTimer);
      SocketClient.selectHero(heroes[0].id);
    }
  }, 1000);
}

// ── Game scherm ───────────────────────────────────────────────
function renderGame(data) {
  State.player   = data.player;
  State.opponents = data.opponents;
  State.roundNum  = data.round_num;
  clearInterval(State.shopTimer);
  showScreen("screen-game");
  showRoundBanner(`Ronde ${data.round_num}`);
  updateHUD(data.player, data.round_num);
  renderOpponentsSidebar(data.opponents);
  GameUI.renderShop(data.player.shop);
  GameUI.renderBoard(data.player.board);
  GameUI.renderHand(data.player.hand || []);
  startShopTimer(data.timer || 45);
  setupHeroPower(data.player.hero);
}

function updateHUD(player, roundNum) {
  document.getElementById("hud-round").textContent = roundNum || State.roundNum;
  document.getElementById("hud-hp").textContent    = player.hp;
  document.getElementById("hud-tier").textContent  = player.tavern_tier;
  document.getElementById("hud-gold").textContent  = player.gold;
  document.getElementById("board-count").textContent = `(${player.board.length}/7)`;
  if (player.hero) {
    const heroEmoji = document.getElementById("hud-hero-emoji");
    const imgUrl = getHeroImageUrl(player.hero.id);
    if (imgUrl && !heroEmoji.dataset.loaded) {
      heroEmoji.innerHTML = `<img src="${imgUrl}" alt="${escapeHtml(player.hero.name)}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;vertical-align:middle" onerror="this.parentElement.textContent='${(player.hero.emoji || '⚔️').replace(/'/g,"\\'")}'">`;
      heroEmoji.dataset.loaded = "1";
    } else if (!imgUrl) {
      heroEmoji.textContent = player.hero.emoji || "⚔️";
    }
    document.getElementById("hud-hero-name").textContent = player.hero.name;
  }
  const upBtn = document.getElementById("btn-upgrade");
  document.getElementById("upgrade-cost").textContent = player.upgrade_cost;
  upBtn.disabled = player.tavern_tier >= 6;
  if (player.tavern_tier >= 6) upBtn.textContent = "⬆️ MAX";
}

function renderOpponentsSidebar(opponents) {
  const sidebar = document.getElementById("opponents-sidebar");
  sidebar.innerHTML = "";
  opponents.forEach(opp => {
    const div = document.createElement("div");
    div.className = `opp-portrait ${opp.alive ? "" : "dead"}`;
    div.innerHTML = `
      ${opp.alive ? (opp.hero?.emoji || "⚔️") : "💀"}
      <span class="opp-hp-badge">❤️${opp.hp}</span>
      <div class="opp-name-tip">${escapeHtml(opp.name)} | T${opp.tavern_tier}</div>
    `;
    sidebar.appendChild(div);
  });
}

function setupHeroPower(hero) {
  const panel = document.getElementById("hero-power-panel");
  if (!hero?.ability || hero.ability.type !== "hero_power") {
    panel.classList.add("hidden"); return;
  }
  panel.classList.remove("hidden");
  document.getElementById("hero-power-emoji").textContent = hero.emoji || "✨";
  document.getElementById("hp-hero-name").textContent     = hero.name || "";
  document.getElementById("hp-desc").textContent          = hero.description || "";
  document.getElementById("hero-power-cost").textContent  = hero.ability.cost ?? 2;
}

// ── Shop timer ────────────────────────────────────────────────
function startShopTimer(seconds) {
  const fill = document.getElementById("shop-timer-fill");
  let remaining = seconds;
  fill.style.width = "100%";
  fill.style.background = "linear-gradient(90deg,#207040,var(--gold))";
  State.shopTimer = setInterval(() => {
    remaining--;
    const pct = remaining / seconds * 100;
    fill.style.width = pct + "%";
    if (pct < 25) fill.style.background = "linear-gradient(90deg,#801010,#e04040)";
    if (remaining <= 0) { clearInterval(State.shopTimer); SocketClient.playerReady(); }
  }, 1000);
}

// ── Shop knoppen ──────────────────────────────────────────────
document.getElementById("btn-upgrade").addEventListener("click", () => SocketClient.upgradeTavern());
document.getElementById("btn-reroll").addEventListener("click",  () => SocketClient.reroll());
document.getElementById("btn-freeze").addEventListener("click",  () => SocketClient.freeze());
document.getElementById("btn-hero-power").addEventListener("click", () => SocketClient.useHeroPower());
document.getElementById("btn-ready").addEventListener("click", () => {
  clearInterval(State.shopTimer);
  SocketClient.playerReady();
  const btn = document.getElementById("btn-ready");
  btn.disabled = true;
  btn.textContent = "⏳ Wachten...";
});

// ── Updates van server ────────────────────────────────────────
function onPlayerUpdate(player) {
  State.player = player;
  updateHUD(player, State.roundNum);
  GameUI.renderShop(player.shop);
  GameUI.renderBoard(player.board);
  GameUI.renderHand(player.hand || []);
}
function onFreezeUpdate(frozen) {
  const btn = document.getElementById("btn-freeze");
  btn.classList.toggle("active", frozen);
  btn.textContent = frozen ? "❄️ Bevroren" : "❄️ Bevries";
}
function onReadyUpdate(data) {
  document.getElementById("ready-indicator").textContent = `${data.ready}/${data.total} klaar`;
}

// ── Game over ─────────────────────────────────────────────────
function showGameOver(winner) {
  clearInterval(State.shopTimer);
  clearInterval(State.heroTimer);
  const isWinner = winner === State.playerName;
  document.getElementById("game-over-icon").textContent    = isWinner ? "🏆" : "💀";
  document.getElementById("game-over-title").textContent   = isWinner ? "Gewonnen!" : "Verslagen!";
  document.getElementById("game-over-subtitle").textContent =
    isWinner ? "Jij bent de laatste staande!" : `${escapeHtml(winner)} heeft gewonnen.`;
  showScreen("screen-game-over");
}
document.getElementById("btn-play-again").addEventListener("click", () => {
  Object.assign(State, { playerName:"", roomCode:"", isHost:false, player:null });
  showScreen("screen-landing");
});

// ── Choose One overlay ────────────────────────────────────────
function showChooseOne(options) {
  const overlay = document.getElementById("choose-one-overlay");
  const container = document.getElementById("choose-one-options");
  container.innerHTML = "";
  options.forEach(opt => {
    const btn = document.createElement("button");
    btn.className = "choose-one-btn";
    btn.textContent = opt.label;
    btn.addEventListener("click", () => {
      overlay.classList.add("hidden");
      SocketClient.chooseOne(opt.index);
    });
    container.appendChild(btn);
  });
  overlay.classList.remove("hidden");
}

// ── Triple discover overlay ───────────────────────────────────
function showTripleDiscover(options) {
  const overlay = document.getElementById("triple-discover-overlay");
  const container = document.getElementById("discover-cards");
  container.innerHTML = "";

  options.forEach(minion => {
    const wrap = document.createElement("div");
    wrap.className = "discover-card-wrap";

    const card = buildOvalCard(minion, "board");
    card.style.pointerEvents = "none";

    wrap.appendChild(card);
    wrap.addEventListener("click", () => {
      overlay.classList.add("hidden");
      SocketClient.chooseDiscover(minion.id);
    });
    container.appendChild(wrap);
  });

  overlay.classList.remove("hidden");
}

// ── Hulp ──────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// Escape-toets annuleert spreuk- en magnetize-targeting
document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    if (SpellTarget.active) SpellTarget.cancel();
    if (MagnetizeTarget.active) MagnetizeTarget.cancel();
  }
});
