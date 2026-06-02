// ── FantasyBg — Blizzard-stijl fantasie achtergrond ──────────
const FantasyBg = (function () {
  let canvas, ctx, W, H;
  let stars = [], orbs = [], shooters = [], runes = [];
  let aurora = [];
  let t = 0, shootTimer = 0, runeTimer = 0;

  const RUNE_CHARS = ['✦','✧','✴','⊕','◈','◆','⬡','⊛','⌬','⟡','❋','✶'];
  const ORB_COLS   = [
    '160,80,255', '80,200,255', '255,180,40',
    '255,60,140', '40,220,160', '100,140,255',
  ];

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
    stars    = Array.from({length: 220}, mkStar);
    aurora   = Array.from({length: 6},  (_, i) => mkAurora(i));
    orbs     = Array.from({length: 38}, mkOrb);
    shooters = []; runes = [];
  }

  // ── Factories ─────────────────────────────────────────────
  function mkStar() {
    const tier = Math.random();
    return {
      x: rnd(0, W), y: rnd(0, H * 0.76),
      r: tier < .6 ? rnd(.3,1.1) : tier < .88 ? rnd(.9,1.9) : rnd(1.7,3),
      base: rnd(.25,.78), alpha: 0,
      speed: rnd(.003,.016), phase: rnd(0, Math.PI*2),
      col: Math.random()<.55 ? '255,245,195'
         : Math.random()<.5  ? '205,180,255' : '175,225,255',
    };
  }
  function mkOrb() {
    const col = ORB_COLS[~~(Math.random()*ORB_COLS.length)];
    return {
      x: rnd(0,W), y: H*.4+rnd(0,H*.6),
      r: rnd(1.5,4.8), vx: rnd(-.2,.2), vy: -rnd(.05,.4),
      col, alpha: rnd(.3,.8), life: Math.random(),
    };
  }
  function mkAurora(i) {
    const pal=[
      '30,220,180','100,50,230','20,180,120',
      '60,30,210','30,130,255','180,40,200',
    ];
    return {
      baseY: H*(.07+i*.055), phase: i*1.1+Math.random(),
      speed: .00025+i*.00019,
      amp:   H*(.03+Math.random()*.058),
      col:   pal[i%pal.length],
      alpha: .05+Math.random()*.065,
      thick: 14+Math.random()*19,
    };
  }
  function mkShooter() {
    const ang=rnd(.08,.44), spd=rnd(5,11);
    return { x:rnd(0,W*.65), y:rnd(0,H*.34),
             vx:spd*Math.cos(ang), vy:spd*Math.sin(ang),
             alpha:1 };
  }
  function mkRune() {
    const col=ORB_COLS[~~(Math.random()*ORB_COLS.length)];
    return {
      x:rnd(W*.05,W*.95), y:H*.65+rnd(0,H*.3),
      ch:RUNE_CHARS[~~(Math.random()*RUNE_CHARS.length)],
      vx:rnd(-.25,.25), vy:-rnd(.18,.55),
      a:rnd(.15,.5), sz:rnd(10,24), rot:rnd(0,Math.PI*2),
      vrot:rnd(-.009,.009), col, life:1,
    };
  }

  // ── Animatielus ───────────────────────────────────────────
  function loop() {
    requestAnimationFrame(loop);
    t += .016;
    ctx.clearRect(0,0,W,H);

    drawSky();
    drawNebulae();
    drawAurorae();
    drawOrbs();
    drawStars();
    drawShooters();
    drawRunes();
    drawMist();
    drawCharacters();  // Blizzard silhouetten

    shootTimer++;
    if (shootTimer > rnd(160,430)) { shooters.push(mkShooter()); shootTimer=0; }
    runeTimer++;
    if (runeTimer>52 && runes.length<22) { runes.push(mkRune()); runeTimer=0; }
  }

  // ── Achtergrond ───────────────────────────────────────────
  function drawSky() {
    const g=ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,   '#010207');
    g.addColorStop(.28, '#03040f');
    g.addColorStop(.6,  '#060312');
    g.addColorStop(.85, '#090516');
    g.addColorStop(1,   '#0d0619');
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
  }

  function drawNebulae() {
    nbl(W*.12, H*.17, W*.32, '90,20,170',   .045);
    nbl(W*.83, H*.11, W*.28, '20,55,155',   .05);
    nbl(W*.54, H*.65, W*.38, '45,15,100',   .032);
    nbl(W*.3,  H*.44, W*.22, '10,80,130',   .028);
    nbl(W*.7,  H*.35, W*.18, '110,30,180',  .022);
  }
  function nbl(cx,cy,r,col,a) {
    const g=ctx.createRadialGradient(cx,cy,0,cx,cy,r);
    g.addColorStop(0,  `rgba(${col},${a})`);
    g.addColorStop(.45,`rgba(${col},${a*.35})`);
    g.addColorStop(1,  'rgba(0,0,0,0)');
    ctx.fillStyle=g;
    ctx.beginPath();
    ctx.ellipse(cx,cy,r,r*.55,t*.015+cy*.001,0,Math.PI*2);
    ctx.fill();
  }

  function drawAurorae() {
    aurora.forEach(a=>{
      a.phase+=a.speed;
      ctx.beginPath();
      for(let j=0;j<=80;j++){
        const x=(j/80)*W;
        const y=a.baseY
          +Math.sin(j*.12+a.phase)*a.amp
          +Math.sin(j*.07+a.phase*.65)*a.amp*.55
          +Math.sin(j*.23+a.phase*1.3)*a.amp*.25;
        j?ctx.lineTo(x,y):ctx.moveTo(x,y);
      }
      const pulse=.75+.25*Math.sin(a.phase*2.5);
      ctx.strokeStyle=`rgba(${a.col},${a.alpha*pulse})`;
      ctx.lineWidth=a.thick*pulse;
      ctx.shadowColor=`rgba(${a.col},.5)`;
      ctx.shadowBlur=26;
      ctx.stroke();
      ctx.shadowBlur=0;
    });
  }

  function drawOrbs() {
    orbs.forEach((o,i)=>{
      o.x+=o.vx; o.y+=o.vy; o.life-=.0022;
      if(o.life<=0||o.y<-20){orbs[i]=mkOrb();return;}
      const a=o.alpha*Math.min(o.life*4,1);
      const g=ctx.createRadialGradient(o.x,o.y,0,o.x,o.y,o.r*4);
      g.addColorStop(0,  `rgba(${o.col},${a})`);
      g.addColorStop(.35,`rgba(${o.col},${a*.45})`);
      g.addColorStop(1,  'rgba(0,0,0,0)');
      ctx.fillStyle=g; ctx.beginPath();
      ctx.arc(o.x,o.y,o.r*4,0,Math.PI*2); ctx.fill();
    });
  }

  function drawStars() {
    stars.forEach(s=>{
      s.phase+=s.speed;
      s.alpha=s.base*(.55+.45*Math.sin(s.phase));
      ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(${s.col},${s.alpha})`; ctx.fill();
      if(s.r>1.6){
        const arm=s.r*2.8;
        ctx.strokeStyle=`rgba(${s.col},${s.alpha*.45})`;
        ctx.lineWidth=.5; ctx.beginPath();
        ctx.moveTo(s.x-arm,s.y); ctx.lineTo(s.x+arm,s.y);
        ctx.moveTo(s.x,s.y-arm); ctx.lineTo(s.x,s.y+arm);
        ctx.stroke();
      }
    });
  }

  function drawShooters() {
    for(let i=shooters.length-1;i>=0;i--){
      const s=shooters[i];
      s.x+=s.vx; s.y+=s.vy; s.alpha-=.018;
      if(s.alpha<=0||s.x>W+60||s.y>H){shooters.splice(i,1);continue;}
      const tl=12;
      const g=ctx.createLinearGradient(s.x-s.vx*tl,s.y-s.vy*tl,s.x,s.y);
      g.addColorStop(0,'rgba(255,255,255,0)');
      g.addColorStop(1,`rgba(255,255,255,${s.alpha})`);
      ctx.strokeStyle=g; ctx.lineWidth=1.8; ctx.beginPath();
      ctx.moveTo(s.x-s.vx*tl,s.y-s.vy*tl); ctx.lineTo(s.x,s.y); ctx.stroke();
      ctx.beginPath(); ctx.arc(s.x,s.y,1.2,0,Math.PI*2);
      ctx.fillStyle=`rgba(255,255,255,${s.alpha})`; ctx.fill();
    }
  }

  function drawRunes() {
    for(let i=runes.length-1;i>=0;i--){
      const r=runes[i];
      r.x+=r.vx; r.y+=r.vy; r.rot+=r.vrot; r.life-=.0035;
      if(r.life<=0){runes.splice(i,1);continue;}
      const a=r.a*Math.min(r.life*3.5,1);
      ctx.save(); ctx.translate(r.x,r.y); ctx.rotate(r.rot);
      ctx.font=`${r.sz}px serif`; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillStyle=`rgba(${r.col},${a})`;
      ctx.shadowColor=`rgba(${r.col},${Math.min(a*1.2,1)})`; ctx.shadowBlur=10;
      ctx.fillText(r.ch,0,0); ctx.shadowBlur=0; ctx.restore();
    }
  }

  function drawMist() {
    const mH=H*.22;
    const g=ctx.createLinearGradient(0,H-mH,0,H);
    g.addColorStop(0,'rgba(10,5,25,0)');
    g.addColorStop(.4,'rgba(10,5,30,.18)');
    g.addColorStop(.75,'rgba(8,4,22,.45)');
    g.addColorStop(1,'rgba(5,2,15,.78)');
    ctx.fillStyle=g; ctx.fillRect(0,H-mH,W,mH);
  }

  // ════════════════════════════════════════════════════════════
  //  BLIZZARD KARAKTER SILHOUETTEN
  // ════════════════════════════════════════════════════════════
  function drawCharacters() {
    const gnd = H * .815;
    // Vloergrond
    groundFill(gnd);

    // Personages — van achter naar voor (rechts/links/midden)
    const pulse = Math.sin(t * .4) * .025;         // subtiele ademhaling
    const hover = Math.sin(t * .5) * H * .004;     // zweef-offset

    drawDeathwing(  W*.08,  gnd - H*.005, .42 + pulse);
    drawLichKing(   W*.23,  gnd,          .48 + pulse);
    drawRagnaros(   W*.5,   gnd,          .72 + pulse*1.2, hover);
    drawIllidan(    W*.77,  gnd,          .5  + pulse);
    drawYoggSaron(  W*.92,  gnd - H*.01,  .38 + pulse);
  }

  function groundFill(gnd) {
    ctx.fillStyle='#010205';
    ctx.shadowColor='rgba(100,40,220,.2)'; ctx.shadowBlur=30;
    ctx.beginPath();
    ctx.moveTo(0,H); ctx.lineTo(0, gnd+hill(0));
    for(let x=0;x<=W;x+=5) ctx.lineTo(x, gnd+hill(x/W));
    ctx.lineTo(W,H); ctx.closePath(); ctx.fill();
    ctx.shadowBlur=0;
  }
  function hill(f) {
    return Math.sin(f*Math.PI*3.4)*H*.024
          +Math.sin(f*Math.PI*7.1)*H*.011
          +Math.sin(f*Math.PI*1.3)*H*.017;
  }

  // ── Illidan Stormrage ─────────────────────────────────────
  // Demonenjager: slanke gestalte, grote vleermuisvleugels, dubbele warglaives
  function drawIllidan(cx, base, sc) {
    ctx.save();
    ctx.fillStyle='#010205';
    ctx.shadowColor='rgba(60,0,200,.55)'; ctx.shadowBlur=45*sc;

    const bh = H*.35*sc;   // lichaamshoogte
    const by = base - bh;

    // Vleugelspanwijdte
    const wingW = W*.22*sc;
    const wingH = H*.32*sc;

    // Linker vleugel
    wing(cx, by+bh*.3, cx-wingW, by-wingH*.1, cx-wingW*.7, base, -1, sc);
    // Rechter vleugel (gespiegeld)
    wing(cx, by+bh*.3, cx+wingW, by-wingH*.1, cx+wingW*.7, base, 1, sc);

    // Staart
    ctx.beginPath();
    ctx.moveTo(cx-4*sc, base-10*sc);
    ctx.quadraticCurveTo(cx-20*sc, base+15*sc, cx+5*sc, base+20*sc);
    ctx.quadraticCurveTo(cx+30*sc, base+15*sc, cx+18*sc, base);
    ctx.fill();

    // Benen
    ctx.fillRect(cx-10*sc, base-bh*.18, 9*sc, bh*.18);
    ctx.fillRect(cx+1*sc,  base-bh*.18, 9*sc, bh*.18);

    // Torso
    ctx.beginPath();
    ctx.moveTo(cx-13*sc, base-bh*.18);
    ctx.lineTo(cx-16*sc, base-bh*.65);
    ctx.lineTo(cx-8*sc,  base-bh*.72);
    ctx.lineTo(cx, by+5*sc);
    ctx.lineTo(cx+8*sc,  base-bh*.72);
    ctx.lineTo(cx+16*sc, base-bh*.65);
    ctx.lineTo(cx+13*sc, base-bh*.18);
    ctx.closePath(); ctx.fill();

    // Hoofd (met hoorns)
    ctx.beginPath();
    ctx.ellipse(cx, by, 10*sc, 13*sc, 0, 0, Math.PI*2); ctx.fill();
    ctx.beginPath(); // Linker hoorn
    ctx.moveTo(cx-6*sc, by-8*sc);
    ctx.lineTo(cx-16*sc, by-28*sc);
    ctx.lineTo(cx-8*sc,  by-8*sc); ctx.fill();
    ctx.beginPath(); // Rechter hoorn
    ctx.moveTo(cx+6*sc, by-8*sc);
    ctx.lineTo(cx+16*sc, by-28*sc);
    ctx.lineTo(cx+8*sc,  by-8*sc); ctx.fill();

    // Warglaive links
    glaive(cx-30*sc, by+bh*.35, -Math.PI*.18, sc);
    // Warglaive rechts
    glaive(cx+30*sc, by+bh*.35,  Math.PI*.18, sc);

    // Gloeiende ogen (groen/blauw)
    glowDot(cx-4*sc, by-2*sc, '80,255,160', .9, 4*sc);
    glowDot(cx+4*sc, by-2*sc, '80,255,160', .9, 4*sc);

    ctx.restore();
  }

  function wing(bx,by,tipx,tipy,basex,basey, dir, sc) {
    ctx.beginPath();
    ctx.moveTo(bx, by);
    ctx.bezierCurveTo(
      bx+dir*20*sc, tipy,
      tipx, tipy,
      tipx, tipy+30*sc
    );
    ctx.bezierCurveTo(
      tipx, tipy+60*sc,
      basex, basey-20*sc,
      basex, basey
    );
    ctx.bezierCurveTo(
      basex+dir*-10*sc, basey,
      bx+dir*5*sc, by+30*sc,
      bx, by
    );
    ctx.closePath(); ctx.fill();
    // Vleugelpijlers
    for(let i=1;i<4;i++){
      const fx=bx+dir*(tipx-bx)*.28*i;
      const fy=by+(tipy+30*sc-by)*.45*i;
      ctx.beginPath();
      ctx.moveTo(bx, by);
      ctx.lineTo(fx, fy);
      ctx.strokeStyle='#010205'; ctx.lineWidth=2*sc; ctx.stroke();
    }
  }

  function glaive(cx, cy, ang, sc) {
    ctx.save(); ctx.translate(cx,cy); ctx.rotate(ang);
    ctx.beginPath();
    ctx.moveTo(0, -30*sc); ctx.lineTo(-18*sc, 2*sc);
    ctx.lineTo(-8*sc, 0); ctx.lineTo(0, 20*sc);
    ctx.lineTo(8*sc,  0); ctx.lineTo(18*sc, 2*sc);
    ctx.closePath(); ctx.fill();
    // Midden handgreep
    ctx.fillRect(-3*sc, -18*sc, 6*sc, 38*sc);
    ctx.restore();
  }

  // ── Ragnaros de Vuurheer ──────────────────────────────────
  // Vurige reus: enorme bovenlichaam, gloeiende kern, sulfuras hamer
  function drawRagnaros(cx, base, sc, hover) {
    ctx.save();
    const by = base - H*.52*sc + hover;

    ctx.fillStyle='#010205';
    ctx.shadowColor='rgba(255,100,0,.6)'; ctx.shadowBlur=60*sc;

    // Lava-voetstuk / vuurring
    ctx.beginPath();
    ctx.ellipse(cx, base, 90*sc, 22*sc, 0, 0, Math.PI*2); ctx.fill();

    // Torso — massief en breed
    ctx.beginPath();
    ctx.moveTo(cx-70*sc, base-20*sc);
    ctx.bezierCurveTo(cx-80*sc, by+H*.18*sc, cx-90*sc, by, cx-50*sc, by);
    ctx.lineTo(cx, by-20*sc);
    ctx.lineTo(cx+50*sc, by);
    ctx.bezierCurveTo(cx+90*sc, by, cx+80*sc, by+H*.18*sc, cx+70*sc, base-20*sc);
    ctx.closePath(); ctx.fill();

    // Linker schouder & arm
    arm(cx-55*sc, by+30*sc, cx-110*sc, by+80*sc, sc);
    // Rechter schouder & arm
    arm(cx+55*sc, by+30*sc, cx+110*sc, by+80*sc, sc);

    // Vuist links (op grond)
    fist(cx-115*sc, by+88*sc, sc);
    // Sulfuras (enorme hamer) rechterhand omhoog
    sulfuras(cx+108*sc, by+82*sc, sc, hover);

    // Hoofd — breed met platte kroon
    ctx.beginPath();
    ctx.ellipse(cx, by-5*sc, 38*sc, 34*sc, 0, 0, Math.PI*2); ctx.fill();
    // Kroon-punten
    for(let i=-2;i<=2;i++){
      ctx.beginPath();
      ctx.moveTo(cx+i*15*sc-7*sc, by-34*sc);
      ctx.lineTo(cx+i*15*sc,       by-55*sc - Math.abs(i)*3*sc);
      ctx.lineTo(cx+i*15*sc+7*sc, by-34*sc);
      ctx.fill();
    }

    // Vuurogen (oranje-geel)
    glowDot(cx-14*sc, by-8*sc, '255,160,0', 1, 7*sc);
    glowDot(cx+14*sc, by-8*sc, '255,160,0', 1, 7*sc);

    // Vuurgloed kern
    const kg=ctx.createRadialGradient(cx,by+30*sc,0,cx,by+30*sc,60*sc);
    kg.addColorStop(0,'rgba(255,120,0,.12)');
    kg.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle=kg; ctx.beginPath();
    ctx.arc(cx,by+30*sc,60*sc,0,Math.PI*2); ctx.fill();

    ctx.restore();
  }

  function arm(sx,sy,ex,ey,sc) {
    ctx.beginPath();
    ctx.moveTo(sx-18*sc, sy-5*sc);
    ctx.quadraticCurveTo(sx+ex*.01, (sy+ey)*.5, ex-10*sc, ey);
    ctx.lineTo(ex+10*sc, ey+12*sc);
    ctx.quadraticCurveTo(sx, (sy+ey)*.5+15*sc, sx+18*sc, sy+5*sc);
    ctx.closePath(); ctx.fill();
  }

  function fist(cx,cy,sc) {
    ctx.beginPath();
    ctx.ellipse(cx, cy, 22*sc, 18*sc, Math.PI*.1, 0, Math.PI*2); ctx.fill();
  }

  function sulfuras(cx, cy, sc, hover) {
    ctx.save(); ctx.translate(cx, cy);
    ctx.rotate(-Math.PI*.22 + Math.sin(hover*.8)*.03);
    // Steel
    ctx.fillRect(-5*sc, -120*sc, 10*sc, 130*sc);
    // Hamerhoofd
    ctx.beginPath();
    ctx.moveTo(-35*sc, -140*sc); ctx.lineTo(-35*sc, -100*sc);
    ctx.lineTo(-12*sc, -90*sc);  ctx.lineTo(-12*sc, -80*sc);
    ctx.lineTo( 12*sc, -80*sc);  ctx.lineTo( 12*sc, -90*sc);
    ctx.lineTo( 35*sc, -100*sc); ctx.lineTo( 35*sc, -140*sc);
    ctx.closePath(); ctx.fill();
    // Rune-oog op hamer
    glowDot(0, -118*sc, '255,80,0', .9, 10*sc);
    ctx.restore();
  }

  // ── The Lich King (Arthas) ────────────────────────────────
  // Verborgen ridder: harnas, groot zwaard (Frostmourne) hoog geheven, cape
  function drawLichKing(cx, base, sc) {
    ctx.save();
    const bh = H*.38*sc;
    const by = base - bh;

    ctx.fillStyle='#010205';
    ctx.shadowColor='rgba(80,180,255,.5)'; ctx.shadowBlur=40*sc;

    // Cape (achter lichaam)
    ctx.beginPath();
    ctx.moveTo(cx-30*sc, by+15*sc);
    ctx.bezierCurveTo(cx-60*sc, by+bh*.4, cx-50*sc, base-20*sc, cx-20*sc, base+5*sc);
    ctx.lineTo(cx+20*sc, base+5*sc);
    ctx.bezierCurveTo(cx+50*sc, base-20*sc, cx+60*sc, by+bh*.4, cx+30*sc, by+15*sc);
    ctx.closePath(); ctx.fill();

    // Benen
    ctx.fillRect(cx-16*sc, base-bh*.28, 14*sc, bh*.28);
    ctx.fillRect(cx+2*sc,  base-bh*.28, 14*sc, bh*.28);
    // Laarzen
    boot(cx-12*sc, base, sc, -1);
    boot(cx+12*sc, base, sc,  1);

    // Torso/harnas
    ctx.beginPath();
    ctx.moveTo(cx-22*sc, base-bh*.28);
    ctx.lineTo(cx-26*sc, base-bh*.65);
    ctx.lineTo(cx-8*sc,  base-bh*.73);
    ctx.lineTo(cx, by+18*sc);
    ctx.lineTo(cx+8*sc,  base-bh*.73);
    ctx.lineTo(cx+26*sc, base-bh*.65);
    ctx.lineTo(cx+22*sc, base-bh*.28);
    ctx.closePath(); ctx.fill();

    // Arm links neer
    ctx.beginPath();
    ctx.moveTo(cx-22*sc, by+bh*.3);
    ctx.quadraticCurveTo(cx-40*sc, by+bh*.55, cx-36*sc, base-bh*.26);
    ctx.lineTo(cx-24*sc, base-bh*.26);
    ctx.quadraticCurveTo(cx-28*sc, by+bh*.5, cx-10*sc, by+bh*.3);
    ctx.closePath(); ctx.fill();

    // Arm rechts omhoog (zwaard vasthoudend)
    ctx.beginPath();
    ctx.moveTo(cx+10*sc, by+bh*.28);
    ctx.quadraticCurveTo(cx+32*sc, by-5*sc, cx+28*sc, by-35*sc);
    ctx.lineTo(cx+18*sc, by-30*sc);
    ctx.quadraticCurveTo(cx+22*sc, by+3*sc, cx+1*sc, by+bh*.25);
    ctx.closePath(); ctx.fill();

    // Hoofd/helm
    ctx.beginPath();
    ctx.ellipse(cx, by, 14*sc, 16*sc, 0, 0, Math.PI*2); ctx.fill();
    // Helm-kam (ridge)
    ctx.beginPath();
    ctx.moveTo(cx-5*sc, by-16*sc);
    ctx.bezierCurveTo(cx-2*sc, by-26*sc, cx+2*sc, by-26*sc, cx+5*sc, by-16*sc);
    ctx.fill();
    // Helm-vleugels
    helmWing(cx-13*sc, by-4*sc, sc, -1);
    helmWing(cx+13*sc, by-4*sc, sc,  1);

    // Frostmourne (zwaard omhoog)
    frostmourne(cx+30*sc, by-30*sc, sc);

    // Gloeiende ogen (blauw-wit)
    glowDot(cx-5*sc,  by-2*sc, '120,200,255', 1, 5*sc);
    glowDot(cx+5*sc,  by-2*sc, '120,200,255', 1, 5*sc);

    ctx.restore();
  }

  function boot(cx, base, sc, dir) {
    ctx.beginPath();
    ctx.moveTo(cx-8*sc, base-12*sc);
    ctx.lineTo(cx-8*sc, base); ctx.lineTo(cx+8*sc+dir*6*sc, base);
    ctx.lineTo(cx+8*sc, base-8*sc); ctx.lineTo(cx+8*sc, base-12*sc);
    ctx.closePath(); ctx.fill();
  }

  function helmWing(x, y, sc, dir) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x+dir*28*sc, y-16*sc);
    ctx.lineTo(x+dir*24*sc, y-6*sc);
    ctx.lineTo(x+dir*18*sc, y+8*sc);
    ctx.closePath(); ctx.fill();
  }

  function frostmourne(cx, cy, sc) {
    ctx.save(); ctx.translate(cx,cy); ctx.rotate(-Math.PI*.28);
    // Kling
    ctx.beginPath();
    ctx.moveTo(0, 0); ctx.lineTo(-8*sc, 20*sc);
    ctx.lineTo(-4*sc, 80*sc); ctx.lineTo(0, 100*sc);
    ctx.lineTo(4*sc, 80*sc);  ctx.lineTo(8*sc, 20*sc);
    ctx.closePath(); ctx.fill();
    // Gardebeschermer
    ctx.fillRect(-20*sc, 16*sc, 40*sc, 9*sc);
    // Handgreep
    ctx.fillRect(-4*sc, 25*sc, 8*sc, 30*sc);
    // Pommel
    ctx.beginPath();
    ctx.arc(0, 55*sc, 8*sc, 0, Math.PI*2); ctx.fill();
    // Rune-gloed op kling
    glowDot(0, 50*sc, '100,180,255', .75, 12*sc);
    ctx.restore();
  }

  // ── Deathwing ────────────────────────────────────────────
  // Verwoester: massieve drakenvleugels, gepantserd, vuurspuwend
  function drawDeathwing(cx, base, sc) {
    ctx.save();
    const by = base - H*.34*sc;

    ctx.fillStyle='#010205';
    ctx.shadowColor='rgba(220,60,0,.55)'; ctx.shadowBlur=50*sc;

    // Linker vleugel (groot)
    dragonWing(cx, by+15*sc, cx-W*.14*sc, by-H*.05*sc, cx-W*.1*sc, base-10*sc, sc, -1);
    // Rechter vleugel
    dragonWing(cx, by+15*sc, cx+W*.12*sc, by-H*.04*sc, cx+W*.08*sc, base-10*sc, sc,  1);

    // Lichaam
    ctx.beginPath();
    ctx.moveTo(cx-32*sc, base-12*sc);
    ctx.bezierCurveTo(cx-42*sc, by+40*sc, cx-36*sc, by+8*sc, cx-18*sc, by);
    ctx.lineTo(cx+18*sc, by);
    ctx.bezierCurveTo(cx+36*sc, by+8*sc, cx+42*sc, by+40*sc, cx+32*sc, base-12*sc);
    ctx.closePath(); ctx.fill();

    // Nek + hoofd
    ctx.beginPath();
    ctx.moveTo(cx-12*sc, by+5*sc);
    ctx.bezierCurveTo(cx-22*sc, by-20*sc, cx-18*sc, by-42*sc, cx-8*sc, by-52*sc);
    ctx.lineTo(cx+8*sc, by-52*sc);
    ctx.bezierCurveTo(cx+18*sc, by-42*sc, cx+22*sc, by-20*sc, cx+12*sc, by+5*sc);
    ctx.fill();

    // Drakenschedel + snuit
    ctx.beginPath();
    ctx.moveTo(cx-22*sc, by-52*sc);
    ctx.bezierCurveTo(cx-32*sc, by-68*sc, cx-12*sc, by-82*sc, cx-4*sc, by-78*sc);
    ctx.bezierCurveTo(cx+4*sc, by-88*sc, cx+20*sc, by-85*sc, cx+28*sc, by-62*sc);
    ctx.bezierCurveTo(cx+24*sc, by-48*sc, cx+8*sc, by-46*sc, cx+4*sc, by-52*sc);
    ctx.lineTo(cx-22*sc, by-52*sc); ctx.fill();

    // Hoorns
    dragonHorn(cx-12*sc, by-76*sc, sc, -1);
    dragonHorn(cx+12*sc, by-76*sc, sc,  1);

    // Ooggloed (oranje)
    glowDot(cx-8*sc, by-64*sc, '255,80,0', 1, 6*sc);
    glowDot(cx+8*sc, by-64*sc, '255,80,0', 1, 6*sc);

    // Gepantserde platen
    for(let i=0;i<5;i++){
      const px=cx-18*sc+i*9*sc;
      const py=by+18*sc+i*6*sc;
      ctx.beginPath();
      ctx.moveTo(px, py); ctx.lineTo(px+5*sc, py-10*sc); ctx.lineTo(px+10*sc, py);
      ctx.fill();
    }

    ctx.restore();
  }

  function dragonWing(bx,by,tipx,tipy,basex,basey,sc,dir) {
    ctx.beginPath();
    ctx.moveTo(bx, by);
    ctx.bezierCurveTo(bx+dir*15*sc, tipy+10*sc, tipx, tipy, tipx, tipy+25*sc);
    ctx.bezierCurveTo(tipx, tipy+55*sc, basex+dir*-8*sc, basey-25*sc, basex, basey);
    ctx.bezierCurveTo(basex+dir*-15*sc, basey-5*sc, bx+dir*8*sc, by+28*sc, bx, by);
    ctx.closePath(); ctx.fill();
    // Vleugelpezen
    for(let i=1;i<5;i++){
      ctx.beginPath();
      ctx.moveTo(bx, by);
      ctx.quadraticCurveTo(
        bx+dir*(tipx-bx)*.45*i*.7, tipy+15*sc+(i*12*sc),
        basex+(tipx-basex)*.3*(4-i), basey-8*sc
      );
      ctx.strokeStyle='rgba(0,0,0,.8)'; ctx.lineWidth=1.5*sc; ctx.stroke();
    }
  }

  function dragonHorn(x,y,sc,dir) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x+dir*6*sc, y-25*sc);
    ctx.lineTo(x+dir*15*sc, y-45*sc);
    ctx.lineTo(x+dir*12*sc, y-22*sc);
    ctx.closePath(); ctx.fill();
  }

  // ── Yogg-Saron ────────────────────────────────────────────
  // Oude god: reusachtig zwevend oog + tentakels uit de grond
  function drawYoggSaron(cx, base, sc) {
    ctx.save();
    const ey = base - H*.3*sc;

    ctx.fillStyle='#010205';
    ctx.shadowColor='rgba(120,0,200,.6)'; ctx.shadowBlur=55*sc;

    // Tentakels
    const tents = [
      {ox:-50,oy:0, cx1:-80,cy1:-60, ex:-65,ey2:-120},
      {ox:-25,oy:0, cx1:-15,cy1:-70, ex:-30,ey2:-140},
      {ox: 0, oy:0, cx1:25, cy1:-90, ex:10, ey2:-160},
      {ox: 25,oy:0, cx1:55, cy1:-60, ex:50, ey2:-120},
      {ox: 50,oy:0, cx1:72, cy1:-40, ex:80, ey2:-90 },
    ];
    tents.forEach(tk=>{
      const tx=cx+tk.ox*sc, ty=base+tk.oy*sc;
      const tcx=cx+tk.cx1*sc, tcy=base+tk.cy1*sc;
      const tex=cx+tk.ex*sc, tey=base+tk.ey2*sc;
      ctx.beginPath();
      ctx.moveTo(tx-6*sc, ty);
      ctx.quadraticCurveTo(tcx-4*sc, tcy, tex-4*sc, tey);
      ctx.lineTo(tex+4*sc, tey);
      ctx.quadraticCurveTo(tcx+4*sc, tcy, tx+6*sc, ty);
      ctx.closePath(); ctx.fill();
      // Tentakelpunt
      ctx.beginPath();
      ctx.arc(tex, tey, 5*sc, 0, Math.PI*2); ctx.fill();
    });

    // Centraal oog (vlesig oogbal)
    ctx.beginPath();
    ctx.ellipse(cx, ey, 45*sc, 35*sc, 0, 0, Math.PI*2); ctx.fill();

    // Ooglid boven
    ctx.beginPath();
    ctx.moveTo(cx-45*sc, ey);
    ctx.bezierCurveTo(cx-30*sc, ey-40*sc, cx+30*sc, ey-40*sc, cx+45*sc, ey);
    ctx.closePath(); ctx.fill();

    // Pupil
    ctx.beginPath();
    ctx.ellipse(cx, ey, 16*sc, 20*sc, 0, 0, Math.PI*2); ctx.fill();

    // Gloeiend iris (paars)
    glowDot(cx, ey, '200,0,255', .85, 22*sc);
    // Pupilgloed (geel)
    glowDot(cx, ey, '255,220,0', .7, 7*sc);

    ctx.restore();
  }

  // ── Hulpfuncties ─────────────────────────────────────────
  function glowDot(x, y, col, a, r) {
    const g=ctx.createRadialGradient(x,y,0,x,y,r);
    g.addColorStop(0,`rgba(${col},${a})`);
    g.addColorStop(.4,`rgba(${col},${a*.5})`);
    g.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle=g; ctx.beginPath();
    ctx.arc(x,y,r,0,Math.PI*2); ctx.fill();
  }

  function rnd(a,b) { return a+Math.random()*(b-a); }

  return { init };
})();
