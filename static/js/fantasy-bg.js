// ── WarCraft / StarCraft cinematic background ─────────────────
const FantasyBg = (function () {
  let canvas, ctx, W, H;
  let t = 0;
  let embers = [], smoke = [], lightning = [], voidRifts = [];
  let emberTimer = 0;
  let lightningTimer = 0, lightningFlash = 0;

  // ── Init ───────────────────────────────────────────────────
  function init() {
    canvas = document.createElement('canvas');
    canvas.id = 'fantasy-bg-canvas';
    canvas.style.cssText =
      'position:fixed;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;';
    document.body.insertBefore(canvas, document.body.firstChild);
    ctx = canvas.getContext('2d');
    resize();
    window.addEventListener('resize', () => { resize(); rebuild(); });
    rebuild();
    requestAnimationFrame(loop);
  }

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function rebuild() {
    embers    = Array.from({ length: 60 }, mkEmber);
    smoke     = Array.from({ length: 18 }, mkSmoke);
    lightning = [];
    voidRifts = Array.from({ length: 4 }, (_, i) => mkVoidRift(i));
  }

  // ── Factories ─────────────────────────────────────────────
  function rnd(a, b) { return a + Math.random() * (b - a); }

  function mkEmber() {
    return {
      x:   rnd(W * .1, W * .9),
      y:   H * rnd(.55, .95),
      vy:  -rnd(.3, 1.4),
      vx:  rnd(-.25, .25),
      r:   rnd(.8, 2.4),
      life: Math.random(),
      maxLife: rnd(.6, 1),
      col: Math.random() < .65 ? '255,140,30' : Math.random() < .6 ? '255,80,10' : '255,210,60',
    };
  }

  function mkSmoke() {
    return {
      x:  rnd(W * .05, W * .95),
      y:  H * rnd(.5, .85),
      r:  rnd(20, 70),
      vy: -rnd(.05, .22),
      vx: rnd(-.12, .12),
      alpha: rnd(.018, .055),
      life: Math.random(),
    };
  }

  function mkVoidRift(i) {
    // Vertical glowing void cracks — SC2 Dark Templar / void energy
    return {
      x:     W * (.1 + i * .25 + rnd(-.04, .04)),
      baseY: H * rnd(.15, .45),
      len:   H * rnd(.1, .22),
      alpha: rnd(.06, .14),
      phase: rnd(0, Math.PI * 2),
      speed: rnd(.0008, .002),
      col:   i % 2 === 0 ? '100,60,220' : '60,160,255',
    };
  }

  function mkLightning(x) {
    const segs = [];
    let cx = x, cy = H * .08;
    const target = H * rnd(.28, .55);
    while (cy < target) {
      const step = rnd(18, 38);
      cx += rnd(-32, 32);
      cy += step;
      segs.push({ x: cx, y: cy });
    }
    return { segs, alpha: 1, x };
  }

  // ── Main loop ─────────────────────────────────────────────
  function loop() {
    requestAnimationFrame(loop);
    t += .014;
    ctx.clearRect(0, 0, W, H);

    drawSky();
    drawVoidRifts();
    drawHorizonGlow();
    drawMountains();
    drawCitadel();
    drawSmoke();
    drawEmbers();
    drawLightning();
    drawForeground();
    drawVignette();

    // Spawn embers
    emberTimer++;
    if (emberTimer > 4) {
      emberTimer = 0;
      if (embers.length < 90) embers.push(mkEmber());
    }

    // Spawn lightning occasionally
    lightningTimer++;
    const interval = rnd(280, 620);
    if (lightningTimer > interval) {
      lightningTimer = 0;
      lightning.push(mkLightning(rnd(W * .1, W * .9)));
      lightningFlash = 1;
    }
    if (lightningFlash > 0) lightningFlash -= .06;
  }

  // ── Sky ────────────────────────────────────────────────────
  function drawSky() {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0,   '#02010a');
    g.addColorStop(.22, '#04020e');
    g.addColorStop(.5,  '#070314');
    g.addColorStop(.72, '#0e0410');
    g.addColorStop(.88, '#1a0608');
    g.addColorStop(1,   '#220a04');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // Lightning ambient flash
    if (lightningFlash > 0) {
      ctx.fillStyle = `rgba(140,160,255,${lightningFlash * .04})`;
      ctx.fillRect(0, 0, W, H);
    }

    // Stars — sparse, cold, distant
    ctx.save();
    for (let i = 0; i < 180; i++) {
      const sx = ((i * 137.508 + 23) % 1) * W;
      const sy = ((i * 97.31  + 11) % .52) * H;
      const sr = i % 7 === 0 ? .9 : .35;
      const sa = .2 + .5 * Math.sin(t * .8 + i);
      ctx.beginPath();
      ctx.arc(sx, sy, sr, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200,210,240,${sa})`;
      ctx.fill();
    }
    ctx.restore();
  }

  // ── Void rifts (SC2 / void energy) ────────────────────────
  function drawVoidRifts() {
    voidRifts.forEach(v => {
      v.phase += v.speed;
      const pulse = .7 + .3 * Math.sin(v.phase);
      const a = v.alpha * pulse;

      // Vertical crack glow
      const g = ctx.createLinearGradient(v.x, v.baseY, v.x, v.baseY + v.len);
      g.addColorStop(0,   `rgba(${v.col},0)`);
      g.addColorStop(.4,  `rgba(${v.col},${a})`);
      g.addColorStop(.6,  `rgba(${v.col},${a})`);
      g.addColorStop(1,   `rgba(${v.col},0)`);

      ctx.strokeStyle = g;
      ctx.lineWidth = 1.5 * pulse;
      ctx.shadowColor = `rgba(${v.col},${a * .8})`;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.moveTo(v.x, v.baseY);
      ctx.lineTo(v.x + Math.sin(v.phase * 1.7) * 6, v.baseY + v.len * .5);
      ctx.lineTo(v.x + Math.sin(v.phase * 2.3) * 4, v.baseY + v.len);
      ctx.stroke();
      ctx.shadowBlur = 0;
    });
  }

  // ── Horizon fire glow ──────────────────────────────────────
  function drawHorizonGlow() {
    const gndY = H * .72;

    // Deep orange fire on horizon
    const pulse = .88 + .12 * Math.sin(t * .7);
    const g1 = ctx.createRadialGradient(W * .5, gndY, 0, W * .5, gndY, W * .55);
    g1.addColorStop(0,   `rgba(200,60,5,${.22 * pulse})`);
    g1.addColorStop(.35, `rgba(160,35,2,${.12 * pulse})`);
    g1.addColorStop(.7,  `rgba(80,15,2,${.05 * pulse})`);
    g1.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle = g1;
    ctx.fillRect(0, gndY - H * .25, W, H * .35);

    // Secondary glow — deeper red smolder
    const g2 = ctx.createRadialGradient(W * .32, gndY, 0, W * .32, gndY, W * .3);
    g2.addColorStop(0,   `rgba(160,25,0,${.14 * pulse})`);
    g2.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle = g2;
    ctx.fillRect(0, gndY - H * .2, W * .6, H * .3);

    const g3 = ctx.createRadialGradient(W * .72, gndY, 0, W * .72, gndY, W * .28);
    g3.addColorStop(0,   `rgba(140,20,0,${.11 * pulse})`);
    g3.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle = g3;
    ctx.fillRect(W * .4, gndY - H * .2, W * .6, H * .3);
  }

  // ── Mountain silhouettes ───────────────────────────────────
  function drawMountains() {
    // Far mountains — blue-grey mist
    ctx.fillStyle = 'rgba(14,8,22,0.72)';
    ctx.beginPath();
    ctx.moveTo(0, H * .72);
    mountain(W * .06, H * .72, H * .19, 0.12);
    mountain(W * .22, H * .72, H * .26, 0.09);
    mountain(W * .41, H * .72, H * .21, 0.07);
    mountain(W * .58, H * .72, H * .28, 0.08);
    mountain(W * .74, H * .72, H * .23, 0.1);
    mountain(W * .90, H * .72, H * .18, 0.11);
    ctx.lineTo(W, H * .72); ctx.lineTo(W, H); ctx.lineTo(0, H);
    ctx.closePath(); ctx.fill();

    // Near mountains — darker, sharper
    ctx.fillStyle = 'rgba(8,4,14,0.88)';
    ctx.beginPath();
    ctx.moveTo(0, H * .82);
    mountain(W * .0,  H * .82, H * .13, 0.08);
    mountain(W * .18, H * .82, H * .16, 0.06);
    mountain(W * .37, H * .82, H * .11, 0.07);
    mountain(W * .55, H * .82, H * .18, 0.05);
    mountain(W * .72, H * .82, H * .12, 0.07);
    mountain(W * .88, H * .82, H * .15, 0.06);
    ctx.lineTo(W, H * .82); ctx.lineTo(W, H); ctx.lineTo(0, H);
    ctx.closePath(); ctx.fill();
  }

  function mountain(cx, base, height, jag) {
    const segs = 14;
    ctx.lineTo(cx - height * .7, base);
    for (let i = 0; i <= segs; i++) {
      const f = i / segs;
      const hf = Math.sin(f * Math.PI);
      const noise = (Math.sin(f * 17.3 + cx) * .5 + Math.sin(f * 31.1 + cx * .3) * .3) * jag * height;
      ctx.lineTo(cx - height * .7 + f * height * 1.4, base - hf * height + noise);
    }
    ctx.lineTo(cx + height * .7, base);
  }

  // ── Citadel / fortress silhouette ─────────────────────────
  function drawCitadel() {
    const gnd = H * .71;
    ctx.fillStyle = '#050108';
    ctx.shadowColor = 'rgba(180,40,5,.18)';
    ctx.shadowBlur = 24;

    // Central keep — Icecrown / Black Citadel feel
    const cx = W * .5, bw = W * .18, bh = H * .32;
    const tx = cx - bw / 2, ty = gnd - bh;

    // Main tower block
    ctx.fillRect(tx, ty, bw, bh);

    // Battlements on top
    const merlonW = bw / 9;
    for (let i = 0; i < 9; i++) {
      if (i % 2 === 0) ctx.fillRect(tx + i * merlonW, ty - H * .025, merlonW, H * .025);
    }

    // Central spire
    spire(cx, ty, W * .022, H * .12);

    // Left tower
    const lt = cx - bw * .78;
    ctx.fillRect(lt - W * .03, gnd - bh * .72, W * .06, bh * .72);
    spire(lt, gnd - bh * .72, W * .015, H * .09);
    battlements(lt - W * .03, gnd - bh * .72, W * .06, 5);

    // Right tower
    const rt = cx + bw * .78;
    ctx.fillRect(rt - W * .03, gnd - bh * .68, W * .06, bh * .68);
    spire(rt, gnd - bh * .68, W * .015, H * .085);
    battlements(rt - W * .03, gnd - bh * .68, W * .06, 5);

    // Connecting wall left
    ctx.fillRect(lt + W * .03, gnd - bh * .28, cx - bw / 2 - lt - W * .03, bh * .28);
    // Connecting wall right
    ctx.fillRect(cx + bw / 2, gnd - bh * .25, rt - W * .03 - (cx + bw / 2), bh * .25);

    // Far-left watchtower
    const flt = W * .12;
    ctx.fillRect(flt - W * .02, gnd - bh * .42, W * .04, bh * .42);
    spire(flt, gnd - bh * .42, W * .01, H * .065);

    // Far-right watchtower
    const frt = W * .88;
    ctx.fillRect(frt - W * .02, gnd - bh * .38, W * .04, bh * .38);
    spire(frt, gnd - bh * .38, W * .01, H * .06);

    // Arched gate
    gate(cx, gnd, W * .038, H * .09);

    // Window glows — warm orange flickering torches
    torchGlow(cx - bw * .3, gnd - bh * .45, '200,80,10');
    torchGlow(cx + bw * .3, gnd - bh * .45, '200,80,10');
    torchGlow(cx,           gnd - bh * .7,  '220,100,15');
    torchGlow(lt,           gnd - bh * .5,  '180,60,5');
    torchGlow(rt,           gnd - bh * .46, '180,60,5');

    ctx.shadowBlur = 0;
  }

  function spire(cx, base, w, h) {
    ctx.beginPath();
    ctx.moveTo(cx, base - h);
    ctx.lineTo(cx - w, base);
    ctx.lineTo(cx + w, base);
    ctx.closePath(); ctx.fill();
  }

  function battlements(x, y, w, count) {
    const mw = w / (count * 2 - 1);
    for (let i = 0; i < count; i++) {
      ctx.fillRect(x + i * mw * 2, y - H * .018, mw, H * .018);
    }
  }

  function gate(cx, gnd, w, h) {
    // Arch: cut out gate opening from silhouette (darker)
    ctx.fillStyle = '#020005';
    ctx.beginPath();
    ctx.moveTo(cx - w, gnd);
    ctx.lineTo(cx - w, gnd - h * .6);
    ctx.arc(cx, gnd - h * .6, w, Math.PI, 0);
    ctx.lineTo(cx + w, gnd);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#050108';
  }

  function torchGlow(x, y, col) {
    const flicker = .85 + .15 * Math.sin(t * 5.3 + x * .02);
    const g = ctx.createRadialGradient(x, y, 0, x, y, W * .035);
    g.addColorStop(0,   `rgba(${col},${.32 * flicker})`);
    g.addColorStop(.4,  `rgba(${col},${.1 * flicker})`);
    g.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, W * .035, 0, Math.PI * 2); ctx.fill();
  }

  // ── Smoke columns ─────────────────────────────────────────
  function drawSmoke() {
    smoke.forEach((s, i) => {
      s.x  += s.vx + Math.sin(t * .3 + i) * .08;
      s.y  += s.vy;
      s.life -= .0012;
      s.r  += .15;
      if (s.life <= 0 || s.y < -s.r) { smoke[i] = mkSmoke(); return; }
      const a = s.alpha * Math.min(s.life * 5, 1);
      const g = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, s.r);
      g.addColorStop(0,   `rgba(30,20,35,${a})`);
      g.addColorStop(.5,  `rgba(20,12,25,${a * .5})`);
      g.addColorStop(1,   'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    });
  }

  // ── Embers ────────────────────────────────────────────────
  function drawEmbers() {
    embers.forEach((e, i) => {
      e.x  += e.vx + Math.sin(t * 1.1 + i * .7) * .15;
      e.y  += e.vy;
      e.life -= .004;
      if (e.life <= 0 || e.y < H * .3) { embers[i] = mkEmber(); return; }
      const a = Math.min(e.life / e.maxLife, 1) * .9;
      const g = ctx.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 2.5);
      g.addColorStop(0,   `rgba(${e.col},${a})`);
      g.addColorStop(.5,  `rgba(${e.col},${a * .4})`);
      g.addColorStop(1,   'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(e.x, e.y, e.r * 2.5, 0, Math.PI * 2); ctx.fill();
      // Core dot
      ctx.beginPath(); ctx.arc(e.x, e.y, e.r * .6, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,240,180,${a})`; ctx.fill();
    });
  }

  // ── Lightning ─────────────────────────────────────────────
  function drawLightning() {
    for (let li = lightning.length - 1; li >= 0; li--) {
      const lx = lightning[li];
      lx.alpha -= .045;
      if (lx.alpha <= 0) { lightning.splice(li, 1); continue; }
      const a = lx.alpha;
      ctx.strokeStyle = `rgba(180,200,255,${a})`;
      ctx.lineWidth = 1.5;
      ctx.shadowColor = `rgba(120,150,255,${a * .8})`;
      ctx.shadowBlur = 18;
      ctx.beginPath();
      ctx.moveTo(lx.x, H * .08);
      lx.segs.forEach(s => ctx.lineTo(s.x, s.y));
      ctx.stroke();
      // Bright core
      ctx.strokeStyle = `rgba(220,230,255,${a * .7})`;
      ctx.lineWidth = .6;
      ctx.beginPath();
      ctx.moveTo(lx.x, H * .08);
      lx.segs.forEach(s => ctx.lineTo(s.x, s.y));
      ctx.stroke();
      ctx.shadowBlur = 0;
    }
  }

  // ── Foreground — dark ground ───────────────────────────────
  function drawForeground() {
    const gnd = H * .78;
    const g = ctx.createLinearGradient(0, gnd, 0, H);
    g.addColorStop(0,   '#050108');
    g.addColorStop(.3,  '#040007');
    g.addColorStop(1,   '#020005');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.moveTo(0, gnd + H * .02);
    // Uneven ground edge
    for (let x = 0; x <= W; x += 6) {
      const ny = gnd + Math.sin(x * .018) * H * .009 + Math.sin(x * .042) * H * .005;
      x === 0 ? ctx.moveTo(x, ny) : ctx.lineTo(x, ny);
    }
    ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
  }

  // ── Screen vignette ───────────────────────────────────────
  function drawVignette() {
    const g = ctx.createRadialGradient(W * .5, H * .5, H * .3, W * .5, H * .5, W * .75);
    g.addColorStop(0,   'rgba(0,0,0,0)');
    g.addColorStop(.7,  'rgba(0,0,0,0)');
    g.addColorStop(1,   'rgba(0,0,0,0.55)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }

  return { init };
})();
