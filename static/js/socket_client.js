// ── Socket.io verbinding ─────────────────────────────────────
const socket = io();

const SocketClient = {
  createLobby(name)          { socket.emit("create_lobby",   { player_name: name }); },
  joinLobby(name, code)      { socket.emit("join_lobby",     { player_name: name, room_code: code }); },
  startGame()                { socket.emit("start_game",     {}); },
  selectHero(heroId)         { socket.emit("select_hero",    { hero_id: heroId }); },
  buyMinion(shopIndex)       { socket.emit("buy_minion",     { shop_index: shopIndex }); },
  sellMinion(boardIndex)     { socket.emit("sell_minion",    { board_index: boardIndex }); },
  reroll()                   { socket.emit("reroll",         {}); },
  freeze()                   { socket.emit("freeze",         {}); },
  upgradeTavern()            { socket.emit("upgrade_tavern", {}); },
  moveMinion(from, to)       { socket.emit("move_minion",    { from_index: from, to_index: to }); },
  playFromHand(handIdx, boardIdx) { socket.emit("play_from_hand", { hand_index: handIdx, board_index: boardIdx ?? -1 }); },
  sellFromHand(handIdx)      { socket.emit("sell_from_hand", { hand_index: handIdx }); },
  useHeroPower(targetIdx)    { socket.emit("use_hero_power", { target_index: targetIdx ?? null }); },
  playerReady()              { socket.emit("player_ready",   {}); },
  chooseDiscover(minionId)   { socket.emit("choose_discover", { minion_id: minionId }); },
};

// ── Verbinding ───────────────────────────────────────────────
socket.on("connect", () => {
  State.mySid = socket.id;
  console.log("Verbonden met server:", socket.id);
});

socket.on("disconnect", () => {
  showNotification("Verbinding verbroken. Ververs de pagina.");
});

// ── Lobby events ─────────────────────────────────────────────
socket.on("lobby_created", data => {
  State.roomCode = data.room_code;
  State.isHost = true;
});

socket.on("joined_lobby", data => {
  State.roomCode = data.room_code;
});

socket.on("lobby_update", data => {
  renderLobby(data);
});

socket.on("error", data => {
  showLandingError(data.message);
  showNotification(data.message);
});

// ── Hero selectie ────────────────────────────────────────────
socket.on("hero_selection", data => {
  renderHeroSelection(data.heroes, data.timeout);
});

socket.on("hero_selected", data => {
  // Bevestiging ontvangen
});

// ── Ronde start ──────────────────────────────────────────────
socket.on("round_start", data => {
  // Reset ready knop
  const readyBtn = document.getElementById("btn-ready");
  readyBtn.disabled = false;
  readyBtn.textContent = "✅ Klaar!";
  document.getElementById("ready-indicator").textContent = "";

  renderGame(data);
});

socket.on("opponents_update", players => {
  State.opponents = players.filter(p => p.sid !== State.mySid);
  renderOpponents(State.opponents);
});

// ── Shop updates ─────────────────────────────────────────────
socket.on("player_update", player => {
  onPlayerUpdate(player);
});

socket.on("board_update", data => {
  if (State.player) {
    State.player.board = data.board;
    GameUI.renderBoard(data.board);
    document.getElementById("board-count").textContent = `(${data.board.length}/7)`;
  }
});

socket.on("freeze_update", data => {
  onFreezeUpdate(data.frozen);
});

// ── Ready updates ────────────────────────────────────────────
socket.on("ready_update", data => {
  onReadyUpdate(data);
});

// ── Combat ───────────────────────────────────────────────────
socket.on("combat_starting", () => {
  showNotification("⚔️ Gevecht begint!", 2000);
});

socket.on("combat_result", data => {
  CombatReplay.start(data);
});

// ── Triple discover ──────────────────────────────────────────
socket.on("triple_discover", data => {
  showTripleDiscover(data.options);
});

// ── Eliminations ─────────────────────────────────────────────
socket.on("eliminations", data => {
  data.players.forEach(name => showElimination(name));
});

// ── Game over ────────────────────────────────────────────────
socket.on("game_over", data => {
  setTimeout(() => showGameOver(data.winner), 16000); // Na combat replay
});
