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
     SCENE 3: ELDER CALLS (12-22s) - Elder appears, dialogue
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
     SCENE 4: WORLD REVEAL (22-38s) - Pan across 5 environments
     ═══════════════════════════════════════════════════════════ */
  function renderWorldReveal(ctx, t, dt) {
    const sceneT = t - TIMELINE.WORLD_REVEAL.start;
    const sceneDur = TIMELINE.WORLD_REVEAL.end - TIMELINE.WORLD_REVEAL.start;

    // Determine which environment to show
    const envDur = sceneDur / 5;
    const envIdx = Math.min(4, Math.floor(sceneT / envDur));
    const envLocalT = sceneT - envIdx * envDur;
    const envProgress = envLocalT / envDur;

    const ep = ENV_PAL[envIdx];
    const land = getLandscape(envIdx);

    // Transition flash between environments
    let transAlpha = 0;
    if (envLocalT < 0.3) transAlpha = 1 - envLocalT / 0.3;

    // Slow pan across the landscape
    const panX = -envProgress * land.canvas.width * 0.3;

    ctx.fillStyle = ep.bg;
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Camera pan with zoom
    Camera.cinematicPan(
      land.canvas.width * 0.3, land.canvas.height * 0.5,
      land.canvas.width * 0.6, land.canvas.height * 0.5,
      0.7, 0.85,
      envDur, envLocalT
    );
    Camera.apply(ctx);
    ctx.drawImage(land.canvas, 0, 0);

    // Draw some substrate particles over landscape
    const subTypes = [['O2','NO3','CH4'], ['NO3','FE3','CH4'], ['SO4','CH4'], ['O2','NO3','CH4'], ['SO4','FE3','MN4','CH4']];
    const types = subTypes[envIdx];
    let seed = envIdx * 999 + Math.floor(t * 2);
    const rng = () => { seed = (seed * 16807) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };
    for (let i = 0; i < 12; i++) {
      const type = types[i % types.length];
      const info = SUBSTRATES[type];
      const sx = rng() * land.canvas.width;
      const sy = rng() * land.canvas.height;
      const pulse = 0.5 + Math.sin(t * 3 + i * 0.7) * 0.5;
      SpriteRenderer.drawGlow(ctx, info.sprite, sx, sy, 2, info.glow, 8, pulse * 0.7);
    }

    Camera.restore(ctx);

    // Environment name overlay
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    ctx.fillRect(0, CFG.H * 0.06, CFG.W, 60);
    ctx.font = 'bold 32px "Courier New", monospace';
    ctx.fillStyle = '#2acfaf';
    ctx.textAlign = 'center';
    ctx.shadowColor = '#2acfaf';
    ctx.shadowBlur = 10;
    ctx.fillText(`CHAPTER ${envIdx + 1}`, CFG.W / 2, CFG.H * 0.06 + 26);
    ctx.shadowBlur = 0;
    ctx.font = '22px "Courier New", monospace';
    ctx.fillStyle = '#8899aa';
    ctx.fillText(ep.name, CFG.W / 2, CFG.H * 0.06 + 52);
    ctx.restore();

    // Transition white flash
    if (transAlpha > 0) {
      ctx.save();
      ctx.globalAlpha = transAlpha * 0.6;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();
    }

    TextRenderer.drawVignette(ctx, 0.5);
  }

  /* ═══════════════════════════════════════════════════════════
     SCENE 5: RIVALS THREAT (38-50s) - Red rivals chase ARKE
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
    // Determine current scene
    if (t < TIMELINE.PIXEL_AWAKEN.start)       renderBlackOpen(ctx, t, dt);
    else if (t < TIMELINE.ELDER_CALLS.start)    renderPixelAwaken(ctx, t, dt);
    else if (t < TIMELINE.WORLD_REVEAL.start)   renderElderCalls(ctx, t, dt);
    else if (t < TIMELINE.RIVALS_THREAT.start)   renderWorldReveal(ctx, t, dt);
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
