/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   SCENES: All cinematic scene logic and rendering
   ============================================================ */

const Scenes = (() => {
  /* Pre-generated landscapes (cached on first use) */
  const landscapes = {};
  let dust = null;
  let methiAnimFrame = 0;
  let methiAnimTimer = 0;
  const methiFrames = ['methi_down', 'methi_right', 'methi_down', 'methi_left'];

  /* Flowing substrate entities for demo scenes */
  let flowingSubs = [];
  let rivalEntities = [];
  let colonyEntities = [];

  function getLandscape(envIdx) {
    if (!landscapes[envIdx]) {
      const cols = 60;
      const rows = 34;
      const porosity = [0.65, 0.48, 0.58, 0.55, 0.52][envIdx];
      landscapes[envIdx] = SpriteRenderer.genLandscape(envIdx, cols, rows, porosity);
    }
    return landscapes[envIdx];
  }

  /* Spawn substrate particles flowing across a landscape */
  function spawnFlowingSubs(envIdx, count) {
    const types = ['O2', 'NO3', 'CH4', 'SO4', 'FE3', 'MN4'];
    const subs = [];
    for (let i = 0; i < count; i++) {
      const type = types[Math.floor(Math.random() * types.length)];
      subs.push({
        type,
        x: -50 + Math.random() * 200,
        y: 100 + Math.random() * 900,
        speed: 30 + Math.random() * 60,
        wobble: Math.random() * Math.PI * 2,
        wobbleAmp: 5 + Math.random() * 15,
        wobbleSpeed: 1 + Math.random() * 2,
        scale: 3 + Math.floor(Math.random() * 3),
        alpha: 0.6 + Math.random() * 0.4
      });
    }
    return subs;
  }

  function updateFlowingSubs(subs, dt) {
    for (const s of subs) {
      s.x += s.speed * dt;
      s.wobble += s.wobbleSpeed * dt;
      if (s.x > CFG.W + 100) {
        s.x = -60;
        s.y = 100 + Math.random() * 900;
      }
    }
  }

  function drawFlowingSubs(ctx, subs) {
    for (const s of subs) {
      const info = SUBSTRATES[s.type];
      const yOff = Math.sin(s.wobble) * s.wobbleAmp;
      SpriteRenderer.drawGlow(ctx, info.sprite, s.x, s.y + yOff, s.scale, info.glow, 12, s.alpha);
    }
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 1: BLACK VOID OPENING (0-5s)
     ═══════════════════════════════════════════════════════════ */
  function renderBlackOpen(ctx, t, dt) {
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Subtle distant stars / dust motes
    if (t > 1) {
      const starAlpha = Math.min(1, (t - 1) / 2) * 0.3;
      ctx.save();
      ctx.globalAlpha = starAlpha;
      let seed = 42;
      const rng = () => { seed = (seed * 16807) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };
      for (let i = 0; i < 40; i++) {
        const sx = rng() * CFG.W;
        const sy = rng() * CFG.H;
        const ss = 1 + rng() * 2;
        const flicker = 0.5 + Math.sin(t * 2 + i) * 0.5;
        ctx.globalAlpha = starAlpha * flicker;
        ctx.fillStyle = '#3a5a7a';
        ctx.fillRect(Math.floor(sx), Math.floor(sy), ss, ss);
      }
      ctx.restore();
    }
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 2: PIXEL AWAKENING (5-12s) - ARKE appears from void
     ═══════════════════════════════════════════════════════════ */
  function renderPixelAwaken(ctx, t, dt) {
    const sceneT = t - TIMELINE.PIXEL_AWAKEN.start;
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    const cx = CFG.W / 2;
    const cy = CFG.H / 2;

    if (sceneT < 2) {
      // Single teal pixel appears and pulses
      const pulseAlpha = Math.min(1, sceneT / 0.5) * (0.6 + Math.sin(sceneT * 6) * 0.4);
      const pixSize = 4 + Math.sin(sceneT * 4) * 2;
      ctx.save();
      ctx.shadowColor = '#2acfaf';
      ctx.shadowBlur = 20 + Math.sin(sceneT * 5) * 10;
      ctx.globalAlpha = pulseAlpha;
      ctx.fillStyle = '#2acfaf';
      ctx.fillRect(cx - pixSize / 2, cy - pixSize / 2, pixSize, pixSize);
      ctx.restore();
    } else if (sceneT < 5) {
      // Zoom out to reveal ARKE sprite
      const revealT = (sceneT - 2) / 3;
      const scale = Camera.lerp(20, 6, Camera.easeInOut(revealT));
      const alpha = Math.min(1, revealT * 2);

      // Glow background
      ctx.save();
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, scale * 20);
      grad.addColorStop(0, `rgba(42,207,175,${0.15 * alpha})`);
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();

      SpriteRenderer.drawGlow(ctx, 'methi_down', cx, cy, Math.floor(scale), '#2acfaf', 30 * alpha, alpha);

      // Corner bracket markers (like in game HUD)
      if (revealT > 0.5) {
        const mAlpha = (revealT - 0.5) * 2;
        const spr = SpriteRenderer.get('methi_down', Math.floor(scale));
        if (spr) {
          const hw = spr.width / 2 + 8;
          const hh = spr.height / 2 + 8;
          ctx.save();
          ctx.globalAlpha = mAlpha;
          ctx.strokeStyle = '#2acfaf';
          ctx.lineWidth = 2;
          ctx.shadowColor = '#5fffdf';
          ctx.shadowBlur = 8;
          const len = 12;
          // Top-left
          ctx.beginPath(); ctx.moveTo(cx - hw, cy - hh + len); ctx.lineTo(cx - hw, cy - hh); ctx.lineTo(cx - hw + len, cy - hh); ctx.stroke();
          // Top-right
          ctx.beginPath(); ctx.moveTo(cx + hw - len, cy - hh); ctx.lineTo(cx + hw, cy - hh); ctx.lineTo(cx + hw, cy - hh + len); ctx.stroke();
          // Bottom-left
          ctx.beginPath(); ctx.moveTo(cx - hw, cy + hh - len); ctx.lineTo(cx - hw, cy + hh); ctx.lineTo(cx - hw + len, cy + hh); ctx.stroke();
          // Bottom-right
          ctx.beginPath(); ctx.moveTo(cx + hw - len, cy + hh); ctx.lineTo(cx + hw, cy + hh); ctx.lineTo(cx + hw, cy + hh - len); ctx.stroke();
          ctx.restore();
        }
      }
    } else {
      // ARKE fully visible, gentle bob animation
      const bob = Math.sin(sceneT * 3) * 6;
      const breathe = 1 + Math.sin(sceneT * 2) * 0.02;

      ctx.save();
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 200);
      grad.addColorStop(0, 'rgba(42,207,175,0.08)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();

      SpriteRenderer.drawGlow(ctx, 'methi_down', cx, cy + bob, 6, '#2acfaf', 25, 1);
    }
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 3: ARKE CLOSE-UP (12-20s) — Big face reveal
     ═══════════════════════════════════════════════════════════ */
  function renderArkeCloseup(ctx, t, dt) {
    const sceneT = t - TIMELINE.ARKE_CLOSEUP.start;
    const ch = CHARACTERS.ARKE;
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    const cx = CFG.W / 2;
    const cy = CFG.H * 0.40;

    // Radial glow background — teal aura
    const auraAlpha = Math.min(0.25, sceneT * 0.05);
    const grad = ctx.createRadialGradient(cx, cy, 40, cx, cy, 500);
    grad.addColorStop(0, `rgba(42,207,175,${auraAlpha})`);
    grad.addColorStop(0.5, `rgba(42,207,175,${auraAlpha * 0.3})`);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Particle ring spinning around character
    ctx.save();
    for (let i = 0; i < 24; i++) {
      const angle = (i / 24) * Math.PI * 2 + sceneT * 0.8;
      const dist = 220 + Math.sin(sceneT * 2 + i) * 20;
      const px = cx + Math.cos(angle) * dist;
      const py = cy + Math.sin(angle) * dist * 0.5;
      const pAlpha = 0.15 + Math.sin(sceneT * 3 + i * 0.5) * 0.1;
      ctx.globalAlpha = Math.min(pAlpha, sceneT * 0.1);
      ctx.fillStyle = '#2acfaf';
      ctx.shadowColor = '#5fffdf';
      ctx.shadowBlur = 8;
      ctx.fillRect(px - 2, py - 2, 4, 4);
    }
    ctx.restore();

    // ARKE sprite — BIG close-up, scale 24-28
    const spriteScale = Math.min(28, 12 + sceneT * 4);
    const spriteAlpha = Math.min(1, sceneT / 1.5);
    const bob = Math.sin(t * 2) * 4;
    SpriteRenderer.drawGlow(ctx, ch.sprite, cx, cy + bob, Math.floor(spriteScale), ch.color, 50 * spriteAlpha, spriteAlpha);

    // Corner scan brackets
    if (sceneT > 1.5) {
      const bAlpha = Math.min(1, (sceneT - 1.5) * 1.5);
      const spr = SpriteRenderer.get(ch.sprite, Math.floor(spriteScale));
      if (spr) {
        const hw = spr.width / 2 + 20, hh = spr.height / 2 + 20;
        ctx.save();
        ctx.globalAlpha = bAlpha * 0.7;
        ctx.strokeStyle = ch.color;
        ctx.lineWidth = 3;
        ctx.shadowColor = ch.glow;
        ctx.shadowBlur = 12;
        const len = 30;
        ctx.beginPath(); ctx.moveTo(cx - hw, cy - hh + len); ctx.lineTo(cx - hw, cy - hh); ctx.lineTo(cx - hw + len, cy - hh); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(cx + hw - len, cy - hh); ctx.lineTo(cx + hw, cy - hh); ctx.lineTo(cx + hw, cy - hh + len); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(cx - hw, cy + hh - len); ctx.lineTo(cx - hw, cy + hh); ctx.lineTo(cx - hw + len, cy + hh); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(cx + hw - len, cy + hh); ctx.lineTo(cx + hw, cy + hh); ctx.lineTo(cx + hw, cy + hh - len); ctx.stroke();
        ctx.restore();
      }
    }

    // "SCANNING..." text flicker
    if (sceneT > 1 && sceneT < 3) {
      const scanAlpha = Math.sin(sceneT * 8) * 0.3 + 0.5;
      ctx.save();
      ctx.globalAlpha = scanAlpha;
      ctx.font = '18px "Courier New", monospace';
      ctx.fillStyle = '#2acfaf';
      ctx.textAlign = 'left';
      ctx.fillText('SCANNING...', 80, CFG.H * 0.12);
      ctx.restore();
    }

    TextRenderer.drawVignette(ctx, 0.5);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 4: ELDER CLOSE-UP (20-27s) — Elder face reveal
     ═══════════════════════════════════════════════════════════ */
  function renderElderCloseup(ctx, t, dt) {
    const sceneT = t - TIMELINE.ELDER_CLOSEUP.start;
    const ch = CHARACTERS.ELDER;
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    const cx = CFG.W / 2;
    const cy = CFG.H * 0.40;

    // Purple/blue aura
    const auraAlpha = Math.min(0.2, sceneT * 0.04);
    const grad = ctx.createRadialGradient(cx, cy, 30, cx, cy, 450);
    grad.addColorStop(0, `rgba(72,72,208,${auraAlpha})`);
    grad.addColorStop(0.5, `rgba(112,80,192,${auraAlpha * 0.4})`);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Wisdom particles — slow drifting
    ctx.save();
    for (let i = 0; i < 30; i++) {
      const angle = (i / 30) * Math.PI * 2 + sceneT * 0.3;
      const dist = 150 + i * 12 + Math.sin(sceneT + i * 0.4) * 30;
      const px = cx + Math.cos(angle) * dist;
      const py = cy + Math.sin(angle) * dist * 0.6;
      const pAlpha = 0.1 + Math.sin(sceneT * 1.5 + i) * 0.08;
      ctx.globalAlpha = Math.min(pAlpha, sceneT * 0.08);
      ctx.fillStyle = i % 3 === 0 ? '#7050c0' : '#4848d0';
      ctx.shadowColor = '#7050c0';
      ctx.shadowBlur = 6;
      const sz = 2 + Math.sin(i * 1.2) * 1;
      ctx.fillRect(px - sz / 2, py - sz / 2, sz, sz);
    }
    ctx.restore();

    // ELDER sprite — BIG close-up
    const spriteScale = Math.min(26, 10 + sceneT * 5);
    const spriteAlpha = Math.min(1, sceneT / 1.2);
    const bob = Math.sin(t * 1.5) * 3;
    SpriteRenderer.drawGlow(ctx, ch.sprite, cx, cy + bob, Math.floor(spriteScale), ch.glow, 45 * spriteAlpha, spriteAlpha);

    // Ancient rune-like border decorations
    if (sceneT > 1) {
      const runeAlpha = Math.min(0.4, (sceneT - 1) * 0.3);
      ctx.save();
      ctx.globalAlpha = runeAlpha;
      ctx.strokeStyle = '#4848d0';
      ctx.lineWidth = 2;
      ctx.shadowColor = '#7050c0';
      ctx.shadowBlur = 10;
      // Top decorative line
      ctx.beginPath();
      ctx.moveTo(CFG.W * 0.2, CFG.H * 0.08);
      ctx.lineTo(CFG.W * 0.8, CFG.H * 0.08);
      ctx.stroke();
      // Bottom decorative line
      ctx.beginPath();
      ctx.moveTo(CFG.W * 0.2, CFG.H * 0.92);
      ctx.lineTo(CFG.W * 0.8, CFG.H * 0.92);
      ctx.stroke();
      // Diamond accents
      for (let d = 0; d < 5; d++) {
        const dx = CFG.W * (0.25 + d * 0.125);
        const dy = CFG.H * 0.08;
        ctx.beginPath();
        ctx.moveTo(dx, dy - 8); ctx.lineTo(dx + 6, dy); ctx.lineTo(dx, dy + 8); ctx.lineTo(dx - 6, dy);
        ctx.closePath();
        ctx.stroke();
      }
      ctx.restore();
    }

    TextRenderer.drawVignette(ctx, 0.5);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 5: ELDER CALLS (27-38s) - Elder appears, dialogue
     ═══════════════════════════════════════════════════════════ */
  function renderElderCalls(ctx, t, dt) {
    const sceneT = t - TIMELINE.ELDER_CALLS.start;
    const ep = ENV_PAL[0]; // Soil environment

    // Dark pore space background
    ctx.fillStyle = ep.bg;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Draw partial landscape in background
    const land = getLandscape(0);
    ctx.save();
    ctx.globalAlpha = 0.5;
    ctx.drawImage(land.canvas, -200, -100, CFG.W + 400, CFG.H + 200);
    ctx.restore();

    // Ambient substrate flow
    if (flowingSubs.length === 0) flowingSubs = spawnFlowingSubs(0, 15);
    updateFlowingSubs(flowingSubs, dt);
    drawFlowingSubs(ctx, flowingSubs);

    // ARKE on left side
    const arkeX = CFG.W * 0.3;
    const arkeY = CFG.H * 0.45;
    const bob = Math.sin(t * 3) * 5;
    SpriteRenderer.drawGlow(ctx, 'methi_down', arkeX, arkeY + bob, 6, '#2acfaf', 20, 1);

    // Elder on right side (fades in)
    if (sceneT > 1) {
      const elderAlpha = Math.min(1, (sceneT - 1) / 2);
      const elderX = CFG.W * 0.7;
      const elderY = CFG.H * 0.42;
      const elderBob = Math.sin(t * 2.5 + 1) * 4;

      // Elder entrance glow
      ctx.save();
      ctx.globalAlpha = elderAlpha * 0.3;
      const eGrad = ctx.createRadialGradient(elderX, elderY, 0, elderX, elderY, 120);
      eGrad.addColorStop(0, '#4848d0');
      eGrad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = eGrad;
      ctx.fillRect(elderX - 150, elderY - 150, 300, 300);
      ctx.restore();

      SpriteRenderer.drawGlow(ctx, 'elder', elderX, elderY + elderBob, 6, '#7050c0', 22, elderAlpha);
    }

    TextRenderer.drawVignette(ctx, 0.5);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 7: EARTH CROSS-SECTION (38-63s)
     FULL FRAME Earth — fills the entire screen.
     Right half opens to reveal geological cross-section.
     Narration text at top (earth_title) and bottom (earth_env).
     ═══════════════════════════════════════════════════════════ */
  function renderEarthCross(ctx, t, dt) {
    const sceneT = t - TIMELINE.EARTH_CROSS.start;
    const sceneDur = TIMELINE.EARTH_CROSS.end - TIMELINE.EARTH_CROSS.start;

    // Deep space background
    ctx.fillStyle = '#010108';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Stars
    let seed = 5555;
    const rng = () => { seed = (seed * 16807) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };
    ctx.save();
    for (let i = 0; i < 200; i++) {
      const sx = rng() * CFG.W;
      const sy = rng() * CFG.H;
      const brightness = 0.12 + Math.sin(t * 1.2 + i * 0.3) * 0.08;
      ctx.globalAlpha = brightness;
      ctx.fillStyle = i % 15 === 0 ? '#aaccff' : '#ffffff';
      ctx.fillRect(sx, sy, 1 + (rng() > 0.9 ? 1 : 0), 1);
    }
    ctx.restore();

    /* ── Phase 1 (0-5s): Earth fills the FULL FRAME
         Phase 2 (5-8s): Right half peels open to reveal layers
         Phase 3 (8+): Cross-section with highlighted environments ── */

    // Earth CENTERED on screen
    const earthCenterX = CFG.W * 0.5;
    const earthCenterY = CFG.H * 0.5;

    // Earth fills the visible area (letterbox bars cover top/bottom 12%)
    // Visible height ~820px so max radius ~370 to keep Earth fully visible
    const maxR = CFG.H * 0.34;
    let earthR, crossPhase;
    if (sceneT < 5) {
      earthR = maxR * 0.94 + sceneT * (maxR * 0.012);
      crossPhase = 0;
    } else if (sceneT < 8) {
      const zoomT = (sceneT - 5) / 3;
      earthR = maxR;
      crossPhase = Camera.easeInOut(zoomT);
    } else {
      earthR = maxR;
      crossPhase = 1;
    }

    // Which environment is currently active
    const envPhaseStart = 6;
    const envPhaseDur = (sceneDur - envPhaseStart) / 5;
    const currentEnvIdx = Math.min(4, Math.floor(Math.max(0, sceneT - envPhaseStart) / envPhaseDur));

    // Pixel size
    const pixSize = 4;

    // Draw the FULL FRAME Earth
    ctx.save();
    for (let py = -earthR - pixSize; py <= earthR + pixSize; py += pixSize) {
      for (let px = -earthR - pixSize; px <= earthR + pixSize; px += pixSize) {
        const dist = Math.sqrt(px * px + py * py);
        if (dist > earthR) continue;

        const nx = px / earthR;
        const ny = py / earthR;
        const nr = dist / earthR;

        const isCrossHalf = px > 0 && crossPhase > 0;
        const crossBlend = isCrossHalf ? Math.min(1, crossPhase * (1 + nx * 2)) : 0;

        let col;

        if (crossBlend < 0.5) {
          // SURFACE — continents, oceans, ice caps, 3D lighting
          const angle = Math.atan2(ny, nx);
          const n1 = Math.sin(angle * 6.3 + 1.2) * Math.cos(ny * 4.7 + 0.8);
          const n2 = Math.sin(angle * 11.1 + ny * 3.2) * 0.35;
          const n3 = Math.sin(angle * 2.8 - 0.5) * Math.cos(ny * 7.3) * 0.25;
          const surfNoise = n1 + n2 + n3;

          const lightX = -0.3, lightY = -0.4;
          const nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
          const lightDot = Math.max(0.15, nx * lightX + ny * lightY + nz * 0.7);
          const shade = 0.5 + lightDot * 0.5;

          if (Math.abs(ny) > 0.78) {
            const iceShade = Math.floor(190 * shade + 40);
            col = `rgb(${iceShade},${Math.floor(iceShade * 1.05)},${Math.floor(iceShade * 1.1)})`;
          } else if (nr > 0.94) {
            const rimFade = (nr - 0.94) / 0.06;
            const r = Math.floor((30 + rimFade * 50) * shade);
            const g = Math.floor((80 + rimFade * 60) * shade);
            const b = Math.floor((160 + rimFade * 40) * shade);
            col = `rgb(${r},${g},${b})`;
          } else if (surfNoise > 0.15) {
            const landDetail = Math.sin(px * 0.06 + py * 0.04) * 0.3;
            if (surfNoise > 0.5 + landDetail) {
              const v = Math.floor(60 * shade);
              col = `rgb(${v + 40},${v + 60},${v + 25})`;
            } else if (surfNoise > 0.3) {
              const v = Math.floor(shade * 50);
              col = `rgb(${v + 30},${v + 95},${v + 25})`;
            } else {
              const v = Math.floor(shade * 45);
              col = `rgb(${v + 50},${v + 80},${v + 20})`;
            }
          } else if (surfNoise > -0.1) {
            const v = Math.floor(shade * 50);
            col = `rgb(${v + 10},${v + 55},${v + 110})`;
          } else {
            const v = Math.floor(shade * 40);
            col = `rgb(${v + 10},${v + 30},${v + 80})`;
          }
        }

        if (crossBlend >= 0.5) {
          const depthFrac = 1.0 - nr;
          col = getLayerColor(depthFrac, px, py, t, nr, currentEnvIdx);
        }

        ctx.fillStyle = col;
        ctx.fillRect(earthCenterX + px, earthCenterY + py, pixSize, pixSize);
      }
    }
    ctx.restore();

    // Atmosphere glow ring
    ctx.save();
    ctx.globalAlpha = 0.2;
    const atmosGrad = ctx.createRadialGradient(
      earthCenterX, earthCenterY, earthR * 0.97,
      earthCenterX, earthCenterY, earthR * 1.08
    );
    atmosGrad.addColorStop(0, 'rgba(100,180,255,0.4)');
    atmosGrad.addColorStop(0.5, 'rgba(60,120,200,0.12)');
    atmosGrad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = atmosGrad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);
    ctx.restore();

    // Cross-section cut line
    if (crossPhase > 0.3) {
      ctx.save();
      ctx.globalAlpha = Math.min(0.4, (crossPhase - 0.3) * 1.2);
      ctx.strokeStyle = '#aaccdd';
      ctx.lineWidth = 1;
      ctx.setLineDash([6, 8]);
      ctx.beginPath();
      ctx.moveTo(earthCenterX, earthCenterY - earthR - 15);
      ctx.lineTo(earthCenterX, earthCenterY + earthR + 15);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
    }

    // Layer boundary arcs on the cross-section half
    if (crossPhase > 0.5) {
      const lineAlpha = (crossPhase - 0.5) * 2;
      ctx.save();
      ctx.globalAlpha = lineAlpha * 0.2;
      ctx.strokeStyle = '#889999';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 10]);
      for (const layer of EARTH_LAYERS) {
        const layerR = earthR * (1.0 - layer.y);
        if (layerR < 10) continue;
        ctx.beginPath();
        ctx.arc(earthCenterX, earthCenterY, layerR, -Math.PI * 0.5, Math.PI * 0.5);
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.restore();
    }

    // Highlight ring for active environment on the cross-section
    if (crossPhase > 0.7 && sceneT > envPhaseStart) {
      const activeLayer = EARTH_LAYERS.find(l => l.env === currentEnvIdx);
      if (activeLayer) {
        const pulse = 0.3 + Math.sin(t * 3) * 0.2;
        const innerR = earthR * (1.0 - activeLayer.y - activeLayer.h);
        const outerR = earthR * (1.0 - activeLayer.y);
        const ep = ENV_PAL[currentEnvIdx];
        ctx.save();
        ctx.globalAlpha = pulse;
        ctx.strokeStyle = ep.grain_l;
        ctx.lineWidth = 4;
        ctx.shadowColor = ep.grain_l;
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(earthCenterX, earthCenterY, outerR, -Math.PI * 0.48, Math.PI * 0.48);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(earthCenterX, earthCenterY, innerR, -Math.PI * 0.48, Math.PI * 0.48);
        ctx.stroke();
        ctx.restore();

        // Small ARKE inside the active layer
        if (sceneT > 9) {
          const arkeAlpha = Math.min(1, (sceneT - 9) * 1.5);
          const midR = (innerR + outerR) / 2;
          const arkeX = earthCenterX + midR * 0.7;
          const arkeY = earthCenterY + Math.sin(t * 2) * midR * 0.2;
          const arkeBob = Math.sin(t * 3) * 4;
          SpriteRenderer.drawGlow(ctx, 'methi_down', arkeX, arkeY + arkeBob, 4, '#2acfaf', 18, arkeAlpha);
        }
      }
    }

    // Schematic note (small, bottom-left corner)
    if (crossPhase > 0.5) {
      ctx.save();
      ctx.globalAlpha = Math.min(0.35, (crossPhase - 0.5) * 1.0);
      ctx.font = '13px "Courier New", monospace';
      ctx.fillStyle = '#556677';
      ctx.textAlign = 'left';
      ctx.fillText('SCHEMATIC — NOT TO SCALE', 30, CFG.H - 20);
      ctx.restore();
    }

    TextRenderer.drawVignette(ctx, 0.3);
  }

  /* Helper: get geological layer color from radial depth */
  function getLayerColor(depthFrac, px, py, t, nr, activeEnvIdx) {
    const n1 = Math.sin(px * 0.04 + py * 0.03) * 0.5;
    const n2 = Math.sin(px * 0.12 + py * 0.08 + 3.7) * 0.3;
    const n3 = Math.sin(px * 0.007 + py * 0.005) * 0.5;
    const detail = n1 + n2;

    for (const layer of EARTH_LAYERS) {
      if (depthFrac >= layer.y && depthFrac < layer.y + layer.h) {
        if (layer.env !== undefined) {
          const ep = ENV_PAL[layer.env];
          const grain = Math.sin(px * 0.2 + py * 0.15) * 0.3 + Math.sin(px * 0.07 - py * 0.04) * 0.4;
          // Active environment gets brighter
          const bright = (layer.env === activeEnvIdx) ? 1.15 : 0.85;
          if (grain > 0.3) return brightenColor(ep.grain_l, bright);
          if (grain > 0) return brightenColor(ep.grain, bright);
          if (grain > -0.25) return brightenColor(ep.grain_d, bright);
          return brightenColor(ep.grain_a || ep.grain_d, bright);
        }
        const c = layer.color;
        const r = parseInt(c.slice(1, 3), 16);
        const g = parseInt(c.slice(3, 5), 16);
        const b = parseInt(c.slice(5, 7), 16);
        const v = Math.floor(n3 * 12);
        return `rgb(${Math.max(0, Math.min(255, r + v))},${Math.max(0, Math.min(255, g + v))},${Math.max(0, Math.min(255, b + v))})`;
      }
    }

    if (depthFrac > 0.85) {
      const heat = Math.floor(80 + detail * 25 + (depthFrac - 0.85) * 350);
      return `rgb(${Math.min(200, heat)},${Math.floor(heat * 0.3)},${Math.floor(heat * 0.15)})`;
    }
    return '#1a1010';
  }

  /* Brighten/darken a hex color */
  function brightenColor(hex, factor) {
    const r = Math.min(255, Math.floor(parseInt(hex.slice(1, 3), 16) * factor));
    const g = Math.min(255, Math.floor(parseInt(hex.slice(3, 5), 16) * factor));
    const b = Math.min(255, Math.floor(parseInt(hex.slice(5, 7), 16) * factor));
    return `rgb(${r},${g},${b})`;
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 8: RIVAL CLOSE-UP (63-69s) — Menacing rival intro
     ═══════════════════════════════════════════════════════════ */
  function renderRivalCloseup(ctx, t, dt) {
    const sceneT = t - TIMELINE.RIVAL_CLOSEUP.start;
    const ch = CHARACTERS.RIVAL;
    ctx.fillStyle = '#0a0000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    const cx = CFG.W / 2;
    const cy = CFG.H * 0.40;

    // Red danger aura — pulsing
    const dangerPulse = 0.15 + Math.sin(t * 4) * 0.08;
    const grad = ctx.createRadialGradient(cx, cy, 30, cx, cy, 500);
    grad.addColorStop(0, `rgba(224,96,96,${dangerPulse})`);
    grad.addColorStop(0.6, `rgba(180,0,0,${dangerPulse * 0.4})`);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Red particle storm
    ctx.save();
    for (let i = 0; i < 40; i++) {
      const angle = (i / 40) * Math.PI * 2 + sceneT * 1.5;
      const dist = 100 + i * 10 + Math.sin(sceneT * 3 + i * 0.6) * 40;
      const px = cx + Math.cos(angle) * dist;
      const py = cy + Math.sin(angle) * dist * 0.5;
      const pAlpha = 0.2 + Math.sin(sceneT * 5 + i) * 0.15;
      ctx.globalAlpha = Math.min(pAlpha, sceneT * 0.12);
      ctx.fillStyle = i % 2 === 0 ? '#ff4444' : '#e06060';
      ctx.shadowColor = '#ff0000';
      ctx.shadowBlur = 5;
      ctx.fillRect(px - 2, py - 2, 3, 3);
    }
    ctx.restore();

    // Main rival — BIG
    const spriteScale = Math.min(30, 8 + sceneT * 6);
    const spriteAlpha = Math.min(1, sceneT / 1.0);
    SpriteRenderer.drawGlow(ctx, ch.sprite, cx, cy, Math.floor(spriteScale), ch.glow, 40 * spriteAlpha, spriteAlpha);

    // Flanking smaller rivals
    if (sceneT > 1.5) {
      const flankAlpha = Math.min(0.8, (sceneT - 1.5) * 0.6);
      const flankScale = Math.floor(spriteScale * 0.5);
      SpriteRenderer.drawGlow(ctx, ch.sprite, cx - 320, cy + 60, flankScale, '#ff4444', 20, flankAlpha);
      SpriteRenderer.drawGlow(ctx, ch.sprite, cx + 320, cy + 60, flankScale, '#ff4444', 20, flankAlpha);
    }

    // Exclamation marks
    if (sceneT > 2) {
      const warnAlpha = 0.5 + Math.sin(t * 6) * 0.5;
      ctx.save();
      ctx.globalAlpha = warnAlpha;
      ctx.font = 'bold 60px "Courier New", monospace';
      ctx.fillStyle = '#ff4444';
      ctx.shadowColor = '#ff0000';
      ctx.shadowBlur = 20;
      ctx.textAlign = 'center';
      ctx.fillText('!', cx - 180, cy - 200);
      ctx.fillText('!', cx + 180, cy - 200);
      ctx.restore();
    }

    // Screen shake effect via slight jitter
    if (sceneT > 0.5 && sceneT < 1.0) {
      Camera.shake(6, 0.5);
    }

    // Red vignette
    const redVig = 0.35 + Math.sin(t * 3) * 0.1;
    ctx.save();
    const dGrad = ctx.createRadialGradient(cx, cy, CFG.W * 0.3, cx, cy, CFG.W * 0.7);
    dGrad.addColorStop(0, 'rgba(0,0,0,0)');
    dGrad.addColorStop(1, `rgba(120,0,0,${redVig})`);
    ctx.fillStyle = dGrad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);
    ctx.restore();
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 9: RIVALS THREAT (69-81s) - Red rivals chase ARKE
     ═══════════════════════════════════════════════════════════ */
  function renderRivalsThreat(ctx, t, dt) {
    const sceneT = t - TIMELINE.RIVALS_THREAT.start;
    const ep = ENV_PAL[2]; // Methane seeps (dark, dangerous)

    ctx.fillStyle = ep.bg;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    const land = getLandscape(2);
    // Zoom into the action
    const zoomLevel = 1.2 + Math.sin(sceneT * 0.5) * 0.1;
    Camera.set(land.canvas.width * 0.4, land.canvas.height * 0.5, zoomLevel);
    Camera.apply(ctx);
    ctx.drawImage(land.canvas, 0, 0);

    // Draw toxic zones pulsing
    const toxicPulse = 0.5 + Math.sin(t * 4) * 0.3;
    for (let i = 0; i < 8; i++) {
      const tx = 400 + i * 180 + Math.sin(i * 2.3) * 100;
      const ty = 300 + Math.cos(i * 1.7) * 200;
      ctx.save();
      ctx.globalAlpha = toxicPulse * 0.4;
      ctx.fillStyle = ep.toxic_g;
      ctx.shadowColor = ep.toxic_g;
      ctx.shadowBlur = 20;
      ctx.fillRect(tx, ty, 64, 64);
      ctx.restore();
    }

    // ARKE running right
    const arkeX = land.canvas.width * 0.35 + sceneT * 40;
    const arkeY = land.canvas.height * 0.5 + Math.sin(sceneT * 5) * 20;
    methiAnimTimer += dt;
    if (methiAnimTimer > 0.2) { methiAnimFrame = (methiAnimFrame + 1) % 4; methiAnimTimer = 0; }
    SpriteRenderer.drawGlow(ctx, methiFrames[methiAnimFrame], arkeX, arkeY, 3, '#2acfaf', 15, 1);

    // Rivals chasing (3 of them)
    for (let r = 0; r < 3; r++) {
      const rDelay = r * 0.8;
      const rx = arkeX - 120 - r * 80 + Math.sin(sceneT * 3 + r * 2) * 20;
      const ry = arkeY + (r - 1) * 60 + Math.sin(sceneT * 4 + r) * 15;
      const pulse = 0.6 + Math.sin(t * 5 + r) * 0.4;

      // Red glow aura
      ctx.save();
      ctx.globalAlpha = pulse * 0.3;
      const rGrad = ctx.createRadialGradient(rx, ry, 0, rx, ry, 40);
      rGrad.addColorStop(0, '#ff0000');
      rGrad.addColorStop(1, 'rgba(255,0,0,0)');
      ctx.fillStyle = rGrad;
      ctx.fillRect(rx - 40, ry - 40, 80, 80);
      ctx.restore();

      SpriteRenderer.drawGlow(ctx, 'rival', rx, ry, 3, '#ff4444', 12, 1);

      // Exclamation mark
      ctx.save();
      ctx.fillStyle = '#ff4444';
      ctx.shadowColor = '#ff0000';
      ctx.shadowBlur = 8;
      ctx.font = 'bold 16px "Courier New", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('!', rx, ry - 25);
      ctx.restore();
    }

    Camera.restore(ctx);

    // Red danger vignette
    const dangerPulse = 0.3 + Math.sin(t * 3) * 0.15;
    ctx.save();
    const dGrad = ctx.createRadialGradient(CFG.W / 2, CFG.H / 2, CFG.W * 0.3, CFG.W / 2, CFG.H / 2, CFG.W * 0.7);
    dGrad.addColorStop(0, 'rgba(0,0,0,0)');
    dGrad.addColorStop(1, `rgba(180,0,0,${dangerPulse})`);
    ctx.fillStyle = dGrad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);
    ctx.restore();

    // Camera shake during intense moments
    if (sceneT > 3 && sceneT < 3.3) Camera.shake(4, 0.3);
    if (sceneT > 7 && sceneT < 7.3) Camera.shake(5, 0.3);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 6: POWER / GROWTH (50-65s) - Eating, growing, dividing
     ═══════════════════════════════════════════════════════════ */
  function renderPowerGrow(ctx, t, dt) {
    const sceneT = t - TIMELINE.POWER_GROW.start;
    const ep = ENV_PAL[0];

    ctx.fillStyle = '#020408';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    if (sceneT < 4) {
      // "CONSUME" - Close up of ARKE eating a red CH4 particle
      const progress = sceneT / 4;
      const land = getLandscape(0);
      ctx.save();
      ctx.globalAlpha = 0.4;
      ctx.drawImage(land.canvas, -300, -200, CFG.W + 600, CFG.H + 400);
      ctx.restore();

      const cx = CFG.W / 2;
      const cy = CFG.H / 2;
      const eatFrame = sceneT > 2 ? 'methi_eat' : 'methi_down';
      SpriteRenderer.drawGlow(ctx, eatFrame, cx, cy, 10, '#2acfaf', 30, 1);

      // CH4 particle approaching
      if (sceneT < 2.5) {
        const subX = cx + 200 - sceneT * 80;
        const subY = cy - 20;
        SpriteRenderer.drawGlow(ctx, 'sub_ch4', subX, subY, 6, '#ff4f4f', 15, 1);
      } else {
        // Eating burst
        const burstT = sceneT - 2.5;
        if (burstT < 0.5) {
          ctx.save();
          ctx.globalAlpha = 1 - burstT * 2;
          ctx.shadowColor = '#ff4f4f';
          ctx.shadowBlur = 40 * (1 - burstT * 2);
          ctx.fillStyle = '#ff4f4f';
          const bSize = 20 + burstT * 200;
          ctx.fillRect(cx - bSize / 2, cy - bSize / 2, bSize, bSize);
          ctx.restore();
        }
      }

      // HUD-style floating text
      if (sceneT > 2.6) {
        ctx.save();
        ctx.globalAlpha = Math.min(1, (sceneT - 2.6) * 3);
        ctx.font = 'bold 24px "Courier New", monospace';
        ctx.fillStyle = '#ff4f4f';
        ctx.shadowColor = '#ff4f4f';
        ctx.shadowBlur = 10;
        ctx.textAlign = 'center';
        ctx.fillText('+25 METHANE', cx, cy - 60 - (sceneT - 2.6) * 30);
        ctx.restore();
      }

    } else if (sceneT < 8) {
      // "GROW" - Growth bar filling up
      const growT = sceneT - 4;
      const cx = CFG.W / 2;
      const cy = CFG.H / 2;

      const land = getLandscape(1);
      ctx.save();
      ctx.globalAlpha = 0.3;
      ctx.drawImage(land.canvas, -200, -100, CFG.W + 400, CFG.H + 200);
      ctx.restore();

      // Pulsing ARKE with growing glow
      const glowSize = 20 + growT * 8;
      const glowAlpha = 0.5 + growT * 0.1;
      SpriteRenderer.drawGlow(ctx, 'methi_glow', cx, cy, 8, '#5fffdf', glowSize, 1);

      // Growth bar
      const barW = 400, barH = 30;
      const barX = cx - barW / 2;
      const barY = cy + 80;
      const fillPct = Math.min(1, growT / 3);

      ctx.save();
      // Bar background
      ctx.fillStyle = '#1a1a2a';
      ctx.fillRect(barX, barY, barW, barH);
      // Bar fill
      const barGrad = ctx.createLinearGradient(barX, barY, barX + barW * fillPct, barY);
      barGrad.addColorStop(0, '#2a8a4a');
      barGrad.addColorStop(1, fillPct > 0.9 ? '#ffff5f' : '#4fdf6f');
      ctx.fillStyle = barGrad;
      ctx.fillRect(barX + 2, barY + 2, (barW - 4) * fillPct, barH - 4);
      // Bar border
      ctx.strokeStyle = '#4fdf6f';
      ctx.lineWidth = 2;
      ctx.strokeRect(barX, barY, barW, barH);
      // Label
      ctx.font = 'bold 18px "Courier New", monospace';
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.fillText('GROWTH', cx, barY - 8);
      if (fillPct >= 1) {
        ctx.fillStyle = '#ffff5f';
        ctx.shadowColor = '#ffff5f';
        ctx.shadowBlur = 15;
        ctx.font = 'bold 28px "Courier New", monospace';
        ctx.fillText('[ SPACE ]', cx, barY + barH + 35);
      }
      ctx.restore();

    } else {
      // "MULTIPLY" - Division animation + colony placement
      const divT = sceneT - 8;
      const cx = CFG.W / 2;
      const cy = CFG.H / 2;

      const land = getLandscape(0);
      ctx.save();
      ctx.globalAlpha = 0.4;
      ctx.drawImage(land.canvas, -200, -100, CFG.W + 400, CFG.H + 200);
      ctx.restore();

      if (divT < 1.5) {
        // Division flash
        const flash = divT < 0.3 ? divT / 0.3 : Math.max(0, 1 - (divT - 0.3) / 0.5);
        ctx.save();
        ctx.globalAlpha = flash * 0.5;
        ctx.fillStyle = '#5fffdf';
        ctx.fillRect(0, 0, CFG.W, CFG.H);
        ctx.restore();

        // ARKE splits
        const splitDist = divT * 60;
        SpriteRenderer.drawGlow(ctx, 'methi_down', cx - splitDist, cy, 7, '#2acfaf', 25, 1);
        SpriteRenderer.drawGlow(ctx, 'methi_down', cx + splitDist, cy, 7, '#2acfaf', 25, 1);
      } else {
        // Colony network forming
        const netT = divT - 1.5;
        const numCols = Math.min(8, Math.floor(netT * 3) + 2);
        SpriteRenderer.drawGlow(ctx, 'methi_right', cx + 150, cy - 30, 6, '#2acfaf', 20, 1);

        for (let i = 0; i < numCols; i++) {
          const colAlpha = Math.min(1, (netT - i * 0.3) * 3);
          if (colAlpha <= 0) continue;
          const angle = (i / numCols) * Math.PI * 1.5 - Math.PI * 0.5;
          const dist = 80 + i * 25;
          const colX = cx - 50 + Math.cos(angle) * dist;
          const colY = cy + Math.sin(angle) * dist;
          SpriteRenderer.drawGlow(ctx, 'colony', colX, colY, 4, '#4fdf6f', 12, colAlpha);

          // Connection lines
          if (i > 0) {
            const prevAngle = ((i - 1) / numCols) * Math.PI * 1.5 - Math.PI * 0.5;
            const prevDist = 80 + (i - 1) * 25;
            const px = cx - 50 + Math.cos(prevAngle) * prevDist;
            const py = cy + Math.sin(prevAngle) * prevDist;
            ctx.save();
            ctx.globalAlpha = colAlpha * 0.3;
            ctx.strokeStyle = '#3a7a5a';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(colX, colY);
            ctx.stroke();
            ctx.restore();
          }
        }
      }
    }

    TextRenderer.drawVignette(ctx, 0.5);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 7: JOURNEY MONTAGE (65-82s) - Quick cuts, all worlds
     ═══════════════════════════════════════════════════════════ */
  function renderJourneyMontage(ctx, t, dt) {
    const sceneT = t - TIMELINE.JOURNEY_MONTAGE.start;
    const sceneDur = TIMELINE.JOURNEY_MONTAGE.end - TIMELINE.JOURNEY_MONTAGE.start;

    // Quick cuts: ~3.4s per environment
    const cutDur = sceneDur / 5;
    const envIdx = Math.min(4, Math.floor(sceneT / cutDur));
    const cutT = sceneT - envIdx * cutDur;
    const ep = ENV_PAL[envIdx];
    const land = getLandscape(envIdx);

    // Transition cut
    let cutFlash = 0;
    if (cutT < 0.15) cutFlash = 1 - cutT / 0.15;

    ctx.fillStyle = ep.bg;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Dynamic camera - faster panning
    const panProgress = cutT / cutDur;
    const zoomBase = [0.9, 1.1, 1.0, 0.85, 1.15][envIdx];
    Camera.cinematicPan(
      land.canvas.width * 0.2, land.canvas.height * 0.4,
      land.canvas.width * 0.7, land.canvas.height * 0.6,
      zoomBase, zoomBase + 0.2,
      cutDur, cutT
    );
    Camera.apply(ctx);
    ctx.drawImage(land.canvas, 0, 0);

    // ARKE in action - different pose per env
    const poses = ['methi_right', 'methi_left', 'methi_right', 'methi_right', 'methi_glow'];
    const arkeX = land.canvas.width * (0.3 + panProgress * 0.3);
    const arkeY = land.canvas.height * 0.5 + Math.sin(t * 5) * 15;
    SpriteRenderer.drawGlow(ctx, poses[envIdx], arkeX, arkeY, 3, '#2acfaf', 15, 1);

    // Substrate particles flowing
    const subTypes = [['O2','NO3','CH4'], ['NO3','FE3','CH4'], ['SO4','CH4'], ['O2','NO3','CH4'], ['SO4','FE3','MN4','CH4']];
    const types = subTypes[envIdx];
    for (let i = 0; i < 8; i++) {
      const type = types[i % types.length];
      const info = SUBSTRATES[type];
      const sx = (land.canvas.width * 0.1 + i * 180 + cutT * 80) % land.canvas.width;
      const sy = 100 + i * 100 + Math.sin(t * 2 + i) * 50;
      SpriteRenderer.drawGlow(ctx, info.sprite, sx, sy, 2, info.glow, 8, 0.7);
    }

    // Rivals (increasing count per env)
    const rivalCount = envIdx + 1;
    for (let r = 0; r < rivalCount; r++) {
      const rx = arkeX - 200 - r * 100 + Math.sin(t * 3 + r) * 40;
      const ry = arkeY + (r - rivalCount / 2) * 80;
      SpriteRenderer.drawGlow(ctx, 'rival', rx, ry, 2, '#ff4444', 10, 0.8);
    }

    // Colonies placed
    if (envIdx >= 2) {
      for (let c = 0; c < envIdx; c++) {
        const cx2 = arkeX - 300 + c * 100;
        const cy2 = arkeY + 100 + Math.sin(c * 1.5) * 60;
        SpriteRenderer.drawGlow(ctx, 'colony', cx2, cy2, 2, '#4fdf6f', 8, 0.6);
      }
    }

    Camera.restore(ctx);

    // White cut flash
    if (cutFlash > 0) {
      ctx.save();
      ctx.globalAlpha = cutFlash * 0.8;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();
    }

    // Speed lines during fast env
    if (envIdx >= 3) {
      ctx.save();
      ctx.globalAlpha = 0.15;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      for (let i = 0; i < 15; i++) {
        const ly = Math.random() * CFG.H;
        const lx = Math.random() * CFG.W * 0.3;
        ctx.beginPath();
        ctx.moveTo(lx, ly);
        ctx.lineTo(lx + 100 + Math.random() * 200, ly);
        ctx.stroke();
      }
      ctx.restore();
    }

    TextRenderer.drawVignette(ctx, 0.4);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 8: EARTH STAKES (82-95s) - Emotional, global scale
     ═══════════════════════════════════════════════════════════ */
  function renderEarthStakes(ctx, t, dt) {
    const sceneT = t - TIMELINE.EARTH_STAKES.start;

    // Deep space background
    ctx.fillStyle = '#010108';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Stars
    let seed = 7777;
    const rng = () => { seed = (seed * 16807) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };
    ctx.save();
    for (let i = 0; i < 100; i++) {
      const sx = rng() * CFG.W;
      const sy = rng() * CFG.H;
      const brightness = 0.2 + Math.sin(t * 2 + i * 0.3) * 0.15;
      ctx.globalAlpha = brightness;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(sx, sy, 1 + (rng() > 0.8 ? 1 : 0), 1);
    }
    ctx.restore();

    // Earth (stylized pixel art circle)
    const earthX = CFG.W / 2;
    const earthY = CFG.H / 2;
    const earthR = 160 + Math.sin(sceneT * 0.5) * 5;

    ctx.save();
    // Earth glow
    const eGrad = ctx.createRadialGradient(earthX, earthY, earthR * 0.8, earthX, earthY, earthR * 1.5);
    eGrad.addColorStop(0, 'rgba(60,120,200,0.2)');
    eGrad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = eGrad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Pixelated earth body
    const pixSize = 8;
    for (let py = -earthR; py < earthR; py += pixSize) {
      for (let px = -earthR; px < earthR; px += pixSize) {
        const dist = Math.sqrt(px * px + py * py);
        if (dist > earthR) continue;
        // Simple earth-like coloring
        const nx = px / earthR;
        const ny = py / earthR;
        const noise = Math.sin(px * 0.03 + 1) * Math.cos(py * 0.04 + 2) + Math.sin(px * 0.07) * 0.5;
        let col;
        if (noise > 0.3) col = '#2a6a2a';       // land
        else if (noise > 0) col = '#3a8a3a';     // light land
        else if (noise > -0.3) col = '#1a4a8a';  // ocean
        else col = '#1a3a6a';                     // deep ocean
        // Ice caps
        if (Math.abs(ny) > 0.75) col = '#c0d0e0';

        ctx.fillStyle = col;
        ctx.fillRect(earthX + px, earthY + py, pixSize, pixSize);
      }
    }
    ctx.restore();

    // Methane particles rising from earth (danger!)
    if (sceneT > 2) {
      const methaneAlpha = Math.min(1, (sceneT - 2) / 2);
      ctx.save();
      ctx.globalAlpha = methaneAlpha;
      for (let i = 0; i < 20; i++) {
        const angle = (i / 20) * Math.PI * 2 + sceneT * 0.3;
        const dist = earthR + 20 + ((sceneT - 2) * 15 + i * 8) % 200;
        const mx = earthX + Math.cos(angle) * dist;
        const my = earthY + Math.sin(angle) * dist;
        const pulse = 0.4 + Math.sin(t * 4 + i) * 0.4;
        ctx.globalAlpha = methaneAlpha * pulse * Math.max(0, 1 - (dist - earthR) / 200);
        SpriteRenderer.drawGlow(ctx, 'sub_ch4', mx, my, 2, '#ff4f4f', 10, 1);
      }
      ctx.restore();
    }

    // ARKE colonies forming shield (after 6s)
    if (sceneT > 6) {
      const shieldAlpha = Math.min(1, (sceneT - 6) / 2);
      const numShield = Math.min(16, Math.floor((sceneT - 6) * 4));
      ctx.save();
      for (let i = 0; i < numShield; i++) {
        const angle = (i / 16) * Math.PI * 2;
        const dist = earthR + 30;
        const sx = earthX + Math.cos(angle) * dist;
        const sy = earthY + Math.sin(angle) * dist;
        const pulse = 0.7 + Math.sin(t * 3 + i * 0.5) * 0.3;
        SpriteRenderer.drawGlow(ctx, 'colony', sx, sy, 2, '#4fdf6f', 10, shieldAlpha * pulse);
      }

      // Shield glow ring
      ctx.globalAlpha = shieldAlpha * 0.2;
      ctx.strokeStyle = '#2acfaf';
      ctx.lineWidth = 3;
      ctx.shadowColor = '#5fffdf';
      ctx.shadowBlur = 20;
      ctx.beginPath();
      ctx.arc(earthX, earthY, earthR + 35, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    TextRenderer.drawVignette(ctx, 0.4);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 9: TITLE REVEAL (95-108s) - ARKE logo + tagline
     ═══════════════════════════════════════════════════════════ */
  let titleExploded = false;

  function renderTitleReveal(ctx, t, dt) {
    const sceneT = t - TIMELINE.TITLE_REVEAL.start;

    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Flash on entry
    if (sceneT < 0.5) {
      ctx.save();
      ctx.globalAlpha = (1 - sceneT * 2) * 0.8;
      ctx.fillStyle = '#2acfaf';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();
    }

    // Title particle explosion
    if (sceneT > 0.3 && !titleExploded) {
      Particles.add(Particles.createTitleExplosion(CFG.W / 2, CFG.H * 0.42));
      titleExploded = true;
    }

    // Ambient glow behind title
    if (sceneT > 1) {
      const glowAlpha = Math.min(0.15, (sceneT - 1) * 0.03);
      const grad = ctx.createRadialGradient(CFG.W / 2, CFG.H * 0.42, 50, CFG.W / 2, CFG.H * 0.42, 400);
      grad.addColorStop(0, `rgba(42,207,175,${glowAlpha})`);
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, CFG.W, CFG.H);
    }

    // ARKE sprite above title
    if (sceneT > 2) {
      const sprAlpha = Math.min(1, (sceneT - 2) / 1.5);
      const bob = Math.sin(t * 2.5) * 6;
      SpriteRenderer.drawGlow(ctx, 'methi_glow', CFG.W / 2, CFG.H * 0.22 + bob, 8, '#5fffdf', 35, sprAlpha);
    }

    TextRenderer.drawVignette(ctx, 0.3);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 10: CLOSING (108-125s) - Features + fade out
     ═══════════════════════════════════════════════════════════ */
  function renderClosing(ctx, t, dt) {
    const sceneT = t - TIMELINE.CLOSING.start;

    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Gentle teal ambient
    const ambAlpha = Math.max(0, 0.06 - sceneT * 0.004);
    const grad = ctx.createRadialGradient(CFG.W / 2, CFG.H / 2, 100, CFG.W / 2, CFG.H / 2, 600);
    grad.addColorStop(0, `rgba(42,207,175,${ambAlpha})`);
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Small ARKE sprite
    if (sceneT < 12) {
      const sprAlpha = Math.max(0, 1 - sceneT / 12);
      const bob = Math.sin(t * 2) * 4;
      SpriteRenderer.drawGlow(ctx, 'methi_down', CFG.W / 2, CFG.H * 0.3 + bob, 4, '#2acfaf', 15, sprAlpha);
    }

    // Final fade to black
    if (sceneT > 13) {
      ctx.save();
      ctx.globalAlpha = Math.min(1, (sceneT - 13) / 4);
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();
    }
  }

  /* ═══════════════════════════════════════════════════════════
     MAIN SCENE DISPATCHER
     ═══════════════════════════════════════════════════════════ */
  function render(ctx, t, dt) {
    // Determine current scene from timeline
    if (t < TIMELINE.PIXEL_AWAKEN.start)        renderBlackOpen(ctx, t, dt);
    else if (t < TIMELINE.ARKE_CLOSEUP.start)   renderPixelAwaken(ctx, t, dt);
    else if (t < TIMELINE.ELDER_CLOSEUP.start)   renderArkeCloseup(ctx, t, dt);
    else if (t < TIMELINE.ELDER_CALLS.start)     renderElderCloseup(ctx, t, dt);
    else if (t < TIMELINE.EARTH_CROSS.start)     renderElderCalls(ctx, t, dt);
    else if (t < TIMELINE.RIVAL_CLOSEUP.start)   renderEarthCross(ctx, t, dt);
    else if (t < TIMELINE.RIVALS_THREAT.start)   renderRivalCloseup(ctx, t, dt);
    else if (t < TIMELINE.POWER_GROW.start)      renderRivalsThreat(ctx, t, dt);
    else if (t < TIMELINE.JOURNEY_MONTAGE.start) renderPowerGrow(ctx, t, dt);
    else if (t < TIMELINE.EARTH_STAKES.start)    renderJourneyMontage(ctx, t, dt);
    else if (t < TIMELINE.TITLE_REVEAL.start)    renderEarthStakes(ctx, t, dt);
    else if (t < TIMELINE.CLOSING.start)         renderTitleReveal(ctx, t, dt);
    else                                          renderClosing(ctx, t, dt);
  }

  function reset() {
    titleExploded = false;
    flowingSubs = [];
    methiAnimFrame = 0;
    methiAnimTimer = 0;
  }

  return { render, reset };
})();
