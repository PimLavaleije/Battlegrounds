// Emoji-portret en achtergrondkleur per minion
const PORTRAITS = {
  // Tier 1
  alleycat:            { emoji: "🐱", bg: "#1a4a1a,#0d2d0d" },
  murloc_tidehunter:   { emoji: "🐸", bg: "#0d3a4a,#061d2d" },
  fiendish_servant:    { emoji: "😈", bg: "#4a0d1a,#2d0610" },
  vulgar_homunculus:   { emoji: "👹", bg: "#3a0d4a,#20062d" },
  righteous_protector: { emoji: "🛡️", bg: "#3a3010,#20190a" },
  mecharoo:            { emoji: "🤖", bg: "#0d2a4a,#06152d" },
  // Tier 1 tokens
  tabbycat:            { emoji: "🐱", bg: "#2a3a0d,#151d06" },
  murloc_scout:        { emoji: "🐟", bg: "#0d2a3a,#06151d" },
  joe_bot:             { emoji: "🔩", bg: "#1a2a3a,#0d151d" },
  // Tier 2
  scavenging_hyena:    { emoji: "🦴", bg: "#3a2010,#1d1008" },
  kindly_grandmother:  { emoji: "👵", bg: "#2a1a0d,#150d06" },
  unstable_ghoul:      { emoji: "💀", bg: "#2a0d3a,#15061d" },
  harvest_golem:       { emoji: "🏚️", bg: "#2a3a0d,#151d06" },
  pack_leader:         { emoji: "🐺", bg: "#1a3a1a,#0d1d0d" },
  rockpool_hunter:     { emoji: "🦀", bg: "#0d2a2a,#06151d" },
  big_bad_wolf:        { emoji: "🐺", bg: "#3a200d,#1d1006" },
  damaged_golem:       { emoji: "⚙️", bg: "#1a2a3a,#0d151d" },
  spider:              { emoji: "🕷️", bg: "#2a1a0d,#150d06" },
  // Tier 3
  infested_wolf:       { emoji: "🐺", bg: "#1a3a0d,#0d1d06" },
  soul_juggler:        { emoji: "🔮", bg: "#3a0d3a,#1d061d" },
  bronze_warden:       { emoji: "🐉", bg: "#3a2500,#1d1300" },
  arm_of_empire:       { emoji: "🦾", bg: "#2a1a0d,#150d06" },
  twilight_emissary:   { emoji: "🌑", bg: "#150d2a,#0a0615" },
  houndmaster:         { emoji: "🏹", bg: "#2a3a0d,#151d06" },
  // Tier 4
  annoy_o_module:      { emoji: "🔔", bg: "#0d2a4a,#06152d" },
  cave_hydra:          { emoji: "🦎", bg: "#0d3a1a,#061d0d" },
  drakonid_enforcer:   { emoji: "🐲", bg: "#3a150d,#1d0a06" },
  bolvar_fireblood:    { emoji: "⚡", bg: "#3a2a00,#1d1500" },
  security_rover:      { emoji: "🚗", bg: "#0d1a3a,#060d1d" },
  guard_bot:           { emoji: "🤖", bg: "#0d2a4a,#06152d" },
  // Tier 5
  baron_rivendare:     { emoji: "💀", bg: "#2a0d3a,#15061d" },
  junkbot:             { emoji: "🔧", bg: "#1a3a3a,#0d1d1d" },
  brann_bronzebeard:   { emoji: "🧔", bg: "#3a2500,#1d1300" },
  lightfang_enforcer:  { emoji: "✨", bg: "#3a3a00,#1d1d00" },
  // Tier 6
  maexxna:             { emoji: "🕷️", bg: "#3a0d0d,#1d0606" },
  zapp_slywick:        { emoji: "⚡", bg: "#2a2000,#151000" },
  ghastcoiler:         { emoji: "🐍", bg: "#0d0d2a,#060615" },
  amalgadon:           { emoji: "🦕", bg: "#1a3a0d,#0d1d06" },
};

function getPortrait(minionId) {
  return PORTRAITS[minionId] || { emoji: "⚔️", bg: "#1a1a1a,#0d0d0d" };
}

function getPortraitBg(minionId, tribe) {
  const p = PORTRAITS[minionId];
  if (p) return `linear-gradient(160deg, ${p.bg})`;
  // Fallback op tribe
  const tribeBg = {
    Beast:  "#1a4a1a,#0d2d0d",
    Murloc: "#0d2a4a,#06152d",
    Demon:  "#4a0d1a,#2d0610",
    Mech:   "#0d2a4a,#06152d",
    Dragon: "#3a2500,#1d1300",
    Undead: "#2a0d3a,#15061d",
  };
  const bg = tribeBg[tribe] || "#1a1a2a,#0d0d15";
  return `linear-gradient(160deg, ${bg})`;
}
