// ── CombatReplay: speelt combat stap-voor-stap af ───────────
const CombatReplay = {
  STEP_DELAY:  850,
  EVENT_DELAY: 380,

  start(data) {
    showScreen("screen-combat");
    document.getElementById("combat-vs-name").textContent   = `vs ${data.opponent_name}`;
    document.getElementById("combat-enemy-label").textContent = data.opponent_name;
    if (State.player) document.getElementById("combat-player-hp").textContent = State.player.hp;
    document.getElementById("combat-enemy-hp").textContent  = "?";
    document.getElementById("combat-result-banner").classList.add("hidden");
    document.getElementById("combat-log").innerHTML = "";

    this._renderBoards(data.player_board, data.enemy_board);
    this._playSteps(data.steps, data).then(() => this._showResult(data));
  },

  _renderBoards(playerBoard, enemyBoard) {
    const pc = document.getElementById("combat-player-board");
    const ec = document.getElementById("combat-enemy-board");
    pc.innerHTML = ""; ec.innerHTML = "";
    playerBoard.forEach(m => pc.appendChild(buildCombatCard(m)));
    enemyBoard.forEach(m  => ec.appendChild(buildCombatCard(m)));
  },

  async _playSteps(steps, data) {
    for (const step of steps) {
      await this._sleep(this.STEP_DELAY);
      if (step.type === "attack") await this._doAttack(step);
      else if (step.type === "death") await this._doDeath(step);
    }
  },

  async _doAttack(step) {
    const pc = document.getElementById("combat-player-board");
    const ec = document.getElementById("combat-enemy-board");
    const isPlayer = step.attacker_side === "player";
    const attackerEl = this._uid(isPlayer ? pc : ec, step.attacker_uid);
    const targetEl   = this._uid(isPlayer ? ec : pc, step.target_uid);
    if (!attackerEl || !targetEl) return;

    // Aanvals-animatie
    attackerEl.classList.add(isPlayer ? "anim-attack-right" : "anim-attack-left");
    await this._sleep(350);
    attackerEl.classList.remove("anim-attack-right", "anim-attack-left");

    // Schade aan doelwit
    if (step.target_shield_broken) {
      this._shieldPop(targetEl);
      targetEl.querySelector(".divine-glow")?.classList.remove("divine-glow");
    } else if (step.target_damage > 0) {
      targetEl.classList.add("anim-takehit");
      this._floatText(targetEl, `-${step.target_damage}`);
      this._updateHp(targetEl, -step.target_damage);
      setTimeout(() => targetEl.classList.remove("anim-takehit"), 350);
    }

    // Tegenslag
    if (step.attacker_shield_broken) {
      this._shieldPop(attackerEl);
    } else if (step.attacker_damage > 0) {
      attackerEl.classList.add("anim-takehit");
      this._floatText(attackerEl, `-${step.attacker_damage}`);
      this._updateHp(attackerEl, -step.attacker_damage);
      setTimeout(() => attackerEl.classList.remove("anim-takehit"), 350);
    }

    this._log(`⚔️ ${step.attacker_name} → ${step.target_name} (${step.attacker_attack} damage)`);

    // Sub-events
    for (const ev of (step.events || [])) {
      await this._sleep(this.EVENT_DELAY);
      this._processEvent(ev);
    }
  },

  async _doDeath(step) {
    const pc = document.getElementById("combat-player-board");
    const ec = document.getElementById("combat-enemy-board");
    const board = step.side === "player" ? pc : ec;
    const el = this._uid(board, step.uid);
    if (el) {
      el.classList.add("anim-death");
      this._log(`💀 ${step.name} dies`);
      await this._sleep(450);
      el.remove();
    }
    for (const ev of (step.events || [])) {
      await this._sleep(this.EVENT_DELAY);
      this._processEvent(ev, step.side);
    }
  },

  _processEvent(ev, side = "player") {
    const pc = document.getElementById("combat-player-board");
    const ec = document.getElementById("combat-enemy-board");
    const friendlyBoard = side === "player" ? pc : ec;

    if (ev.type === "summon" && ev.token) {
      const card = buildCombatCard(ev.token);
      card.classList.add("anim-bounce-in");
      friendlyBoard.appendChild(card);
      this._log(`✨ ${ev.token.name} is summoned`);
    }
    if (ev.type === "buff") {
      const el = this._uid(pc, ev.uid) || this._uid(ec, ev.uid);
      if (el) {
        this._floatText(el, "⬆️", "buff");
        if (ev.attack !== undefined) this._setStat(el, ".mc-atk", ev.attack);
        if (ev.health !== undefined) this._setStat(el, ".mc-hp",  ev.health);
      }
    }
    if (ev.type === "aoe_damage") this._log(`💥 ${ev.amount} damage to everyone!`);
    if (ev.type === "reborn")     this._log(`🔮 ${ev.name} reborns with 1 health!`);
    if (ev.type === "soul_juggler") {
      const el = this._uid(ec, ev.target_uid) || this._uid(pc, ev.target_uid);
      if (el) { el.classList.add("anim-takehit"); this._floatText(el, "-3"); }
      this._log("🔥 Soul Juggler deals 3 damage");
    }
    if (ev.type === "pack_leader_buff") this._log("🐺 Pack Leader gives +3 Attack!");
  },

  _showResult(data) {
    const banner = document.getElementById("combat-result-banner");
    banner.classList.remove("hidden", "won", "lost", "tie");
    const res = data.your_result;
    if (res === "won") {
      banner.textContent = `🏆 Victory! (${data.opponent_name} takes ${data.damage_dealt} damage)`;
      banner.classList.add("won");
      this._log(`✅ You win! Opponent takes ${data.damage_dealt} damage.`, "won");
    } else if (res === "lost") {
      banner.textContent = `💀 Defeated! (You take ${data.damage_received} damage)`;
      banner.classList.add("lost");
      this._log(`❌ Opponent wins. You take ${data.damage_received} damage.`, "lost");
    } else {
      banner.textContent = "🤝 Draw!";
      banner.classList.add("tie");
      this._log("🤝 Draw.");
    }
    if (State.player) {
      State.player.hp = Math.max(0, State.player.hp - (data.damage_received || 0));
      document.getElementById("hud-hp").textContent          = State.player.hp;
      document.getElementById("combat-player-hp").textContent = State.player.hp;
    }
  },

  // ── Helpers ───────────────────────────────────────────────
  _uid(container, uid) {
    return uid ? container.querySelector(`[data-uid="${uid}"]`) : null;
  },
  _floatText(el, text, type) {
    const span = document.createElement("span");
    span.className = `float-text ${type || ""}`;
    span.textContent = text;
    el.style.position = "relative";
    el.appendChild(span);
    setTimeout(() => span.remove(), 900);
  },
  _shieldPop(el) {
    const d = document.createElement("div");
    d.className = "shield-pop";
    el.style.position = "relative";
    el.appendChild(d);
    el.classList.remove("divine-glow");
    setTimeout(() => d.remove(), 500);
  },
  _updateHp(el, delta) {
    const hpEl = el.querySelector(".mc-hp");
    if (hpEl) hpEl.textContent = Math.max(0, (parseInt(hpEl.textContent) || 0) + delta);
  },
  _setStat(el, selector, value) {
    const e = el.querySelector(selector);
    if (e) e.textContent = value;
  },
  _log(msg, cls = "") {
    const log = document.getElementById("combat-log");
    const div = document.createElement("div");
    div.className = `cle ${cls}`;
    div.textContent = msg;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  },
  _sleep: ms => new Promise(r => setTimeout(r, ms)),
};
