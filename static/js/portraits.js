// Minion portraits: BG card images via hearthstone.wiki.gg
const PORTRAITS = {
  // ── TIER 1 ────────────────────────────────────────────────
  wrath_weaver:        { emoji: "😡", cardId: "BGS_004_Battlegrounds",   bg: "#4a0d1a,#2d0610" },
  crackling_cyclone:   { emoji: "🌀", cardId: "BGS_119_Battlegrounds",   bg: "#0d1a3a,#060d1d" },
  harmless_bonehead:   { emoji: "💀", cardId: "BG28_300_Battlegrounds",  bg: "#2a0d3a,#15061d" },
  risen_rider:         { emoji: "🪦", cardId: "BG25_001_Battlegrounds",  bg: "#2a0d3a,#15061d" },
  twilight_hatchling:  { emoji: "🐣", cardId: "BG34_630_Battlegrounds",  bg: "#3a2500,#1d1300" },
  cord_puller:         { emoji: "🤖", cardId: "BG29_611_Battlegrounds",  bg: "#0d2a4a,#06152d" },
  manasaber:           { emoji: "🐱", cardId: "BG26_800_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },

  // ── TIER 2 ────────────────────────────────────────────────
  sellemental:         { emoji: "💧", cardId: "BGS_115_Battlegrounds",   bg: "#0d1a3a,#060d1d" },
  blazing_skyfin:      { emoji: "🐉", cardId: "BG25_040_Battlegrounds",  bg: "#3a2500,#1d1300" },
  scarlet_skull:       { emoji: "💀", cardId: "BG25_022_Battlegrounds",  bg: "#2a0d3a,#15061d" },
  humming_bird:        { emoji: "🐦", cardId: "BG26_805_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },
  sewer_rat:           { emoji: "🐀", cardId: "BG19_010_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },
  nerubian_deathswarmer: { emoji: "🦂", cardId: "BG25_011_Battlegrounds", bg: "#2a0d3a,#15061d" },
  glowgullet_warlord:  { emoji: "🐗", cardId: "BG32_430_Battlegrounds",  bg: "#2a1a0d,#150d06" },

  // ── TIER 3 ────────────────────────────────────────────────
  deflect_o_bot:       { emoji: "🤖", cardId: "BGS_071_Battlegrounds",   bg: "#0d2a4a,#06152d" },
  annoy_o_module:      { emoji: "🔔", cardId: "BG_BOT_911_Battlegrounds", bg: "#0d2a4a,#06152d" },
  deadly_spore:        { emoji: "☠️", cardId: "BGS_131_Battlegrounds",   bg: "#1a1a2a,#0d0d15" },
  floating_watcher:    { emoji: "👁️", cardId: "BG_GVG_100_Battlegrounds", bg: "#4a0d1a,#2d0610" },
  hardy_orca:          { emoji: "🐋", cardId: "BG34_312_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },
  cadaver_caretaker:   { emoji: "🧟", cardId: "BG30_125_Battlegrounds",  bg: "#2a0d3a,#15061d" },
  mama_mrrglton:       { emoji: "👑", cardId: "BG35_140_Battlegrounds",  bg: "#0d2a4a,#06152d" },

  // ── TIER 4 ────────────────────────────────────────────────
  tunnel_blaster:      { emoji: "💣", cardId: "BG_DAL_775_Battlegrounds", bg: "#1a1a2a,#0d0d15" },
  determined_defender: { emoji: "🛡️", cardId: "BG35_122_Battlegrounds",  bg: "#1a1a2a,#0d0d15" },
  king_bagurgle:       { emoji: "👑", cardId: "BGS_030_Battlegrounds",   bg: "#0d2a4a,#06152d" },
  plaguerunner:        { emoji: "🦠", cardId: "BG34_690_Battlegrounds",  bg: "#2a0d3a,#15061d" },
  imposing_percussionist: { emoji: "🥁", cardId: "BG26_525_Battlegrounds", bg: "#4a0d1a,#2d0610" },
  banana_slamma:       { emoji: "🍌", cardId: "BG26_802_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },
  monstrous_macaw:     { emoji: "🦜", cardId: "BGS_078_Battlegrounds",   bg: "#1a4a1a,#0d2d0d" },

  // ── TIER 5 ────────────────────────────────────────────────
  bile_spitter:        { emoji: "🐸", cardId: "BG33_318_Battlegrounds",  bg: "#0d2a4a,#06152d" },
  sewer_lord:          { emoji: "🐀", cardId: "BG35_604_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },
  tichondrius:         { emoji: "🦇", cardId: "BG26_523_Battlegrounds",  bg: "#4a0d1a,#2d0610" },
  divine_sparkbot:     { emoji: "✨", cardId: "BG33_809_Battlegrounds",  bg: "#0d2a4a,#06152d" },
  spiked_savior:       { emoji: "🦔", cardId: "BG29_808_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },
  kalecgos:            { emoji: "🐲", cardId: "BGS_041_Battlegrounds",   bg: "#3a2500,#1d1300" },
  sinrunner_blanchy:   { emoji: "🐴", cardId: "BG24_005_Battlegrounds",  bg: "#2a0d3a,#15061d" },

  // ── TIER 6 ────────────────────────────────────────────────
  goldrinn:            { emoji: "🐺", cardId: "BGS_018_Battlegrounds",   bg: "#1a4a1a,#0d2d0d" },
  elemental_of_surprise: { emoji: "⚡", cardId: "BG26_175_Battlegrounds", bg: "#0d1a3a,#060d1d" },
  eternal_summoner:    { emoji: "💀", cardId: "BG25_009_Battlegrounds",  bg: "#2a0d3a,#15061d" },
  ship_jumper:         { emoji: "🏴‍☠️", cardId: "BG35_700_Battlegrounds", bg: "#1a3a3a,#0d1d1d" },
  nightbane_ignited:   { emoji: "🔥", cardId: "BG29_815_Battlegrounds",  bg: "#3a2500,#1d1300" },
  moonsteel_juggernaut: { emoji: "⚙️", cardId: "BG31_171_Battlegrounds", bg: "#0d2a4a,#06152d" },
  rabid_panther:       { emoji: "🐆", cardId: "BG34_321_Battlegrounds",  bg: "#1a4a1a,#0d2d0d" },

  // ── TOKENS ────────────────────────────────────────────────
  skeleton:            { emoji: "🦴", cardId: null, bg: "#2a0d3a,#15061d" },
  whelp:               { emoji: "🐣", cardId: null, bg: "#3a2500,#1d1300" },
  microbot:            { emoji: "🔩", cardId: null, bg: "#0d2a4a,#06152d" },
  cubling:             { emoji: "📦", cardId: null, bg: "#1a4a1a,#0d2d0d" },
  turtle:              { emoji: "🐢", cardId: null, bg: "#1a4a1a,#0d2d0d" },
  quilboar_runt:       { emoji: "🐗", cardId: null, bg: "#2a1a0d,#150d06" },
  sewer_rat_token:     { emoji: "🐀", cardId: null, bg: "#1a4a1a,#0d2d0d" },
  eternal_knight:      { emoji: "⚔️", cardId: null, bg: "#2a0d3a,#15061d" },
  sky_pirate:          { emoji: "🏴‍☠️", cardId: null, bg: "#1a3a3a,#0d1d1d" },
};

function getPortrait(minionId) {
  return PORTRAITS[minionId] || { emoji: "⚔️", cardId: null, bg: "#1a1a2a,#0d0d15" };
}

function getPortraitBg(minionId, tribe) {
  const p = PORTRAITS[minionId];
  if (p) return `linear-gradient(160deg, ${p.bg})`;
  const tribeBg = {
    Beast:     "#1a4a1a,#0d2d0d",
    Murloc:    "#0d2a4a,#06152d",
    Demon:     "#4a0d1a,#2d0610",
    Mech:      "#0d2a4a,#06152d",
    Dragon:    "#3a2500,#1d1300",
    Undead:    "#2a0d3a,#15061d",
    Elemental: "#0d1a3a,#060d1d",
    Pirate:    "#1a3a3a,#0d1d1d",
    Naga:      "#0d3a2a,#061d15",
    Quilboar:  "#2a1a0d,#150d06",
  };
  return `linear-gradient(160deg, ${tribeBg[tribe] || "#1a1a2a,#0d0d15"})`;
}

// Returns wiki card image URL, or null if no cardId
function getCardImageUrl(minionId) {
  const p = PORTRAITS[minionId];
  if (p && p.cardId) {
    return `https://hearthstone.wiki.gg/images/thumb/${p.cardId}.png/200px-${p.cardId}.png`;
  }
  return null;
}
