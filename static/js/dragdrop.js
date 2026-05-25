// ── Drag & drop voor het board ──────────────────────────────
// Board drag-and-drop wordt afgehandeld in game_ui.js via native HTML5 drag API.
// Dit bestand bevat extra touch-support voor mobiele apparaten.

let touchDragging = null;
let touchOriginIndex = null;
let touchClone = null;

document.addEventListener("touchstart", e => {
  const card = e.target.closest(".minion-card");
  if (!card) return;
  const slot = card.closest(".board-slot");
  if (!slot) return;

  touchOriginIndex = parseInt(slot.dataset.slotIndex);
  touchDragging = card;

  // Maak een clone voor visuele feedback
  touchClone = card.cloneNode(true);
  touchClone.style.position = "fixed";
  touchClone.style.opacity  = "0.75";
  touchClone.style.pointerEvents = "none";
  touchClone.style.zIndex  = "999";
  touchClone.style.width   = card.offsetWidth + "px";
  document.body.appendChild(touchClone);

  document.getElementById("sell-zone").classList.remove("hidden");
}, { passive: true });

document.addEventListener("touchmove", e => {
  if (!touchClone) return;
  const touch = e.touches[0];
  touchClone.style.left = (touch.clientX - touchClone.offsetWidth / 2) + "px";
  touchClone.style.top  = (touch.clientY - touchClone.offsetHeight / 2) + "px";
}, { passive: true });

document.addEventListener("touchend", e => {
  if (!touchDragging) return;
  document.getElementById("sell-zone").classList.add("hidden");

  if (touchClone) {
    touchClone.remove();
    touchClone = null;
  }

  const touch = e.changedTouches[0];
  const target = document.elementFromPoint(touch.clientX, touch.clientY);

  // Verkopen
  const sellZone = document.getElementById("sell-zone");
  if (sellZone && sellZone.contains(target)) {
    if (touchOriginIndex !== null) {
      SocketClient.sellMinion(touchOriginIndex);
    }
    touchDragging = null;
    touchOriginIndex = null;
    return;
  }

  // Verplaatsen naar ander slot
  const destSlot = target ? target.closest(".board-slot") : null;
  if (destSlot) {
    const destIndex = parseInt(destSlot.dataset.slotIndex);
    if (!isNaN(destIndex) && destIndex !== touchOriginIndex && touchOriginIndex !== null) {
      SocketClient.moveMinion(touchOriginIndex, destIndex);
    }
  }

  touchDragging = null;
  touchOriginIndex = null;
});
