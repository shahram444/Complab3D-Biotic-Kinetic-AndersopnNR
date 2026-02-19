/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   TEXT: Cinematic narration, dialogue, and title rendering
   ============================================================ */

const TextRenderer = (() => {
  const activeTexts = [];

  /* Pixel font metrics */
  const FONTS = {
    whisper:   { size: 28, family: 'Courier New, monospace', color: '#8899aa', shadow: '#1a3a60', align: 'center', baseline: 0.85 },
    subtitle:  { size: 36, family: 'Courier New, monospace', color: '#c0d0e0', shadow: '#1a3a60', align: 'center', baseline: 0.65 },
    title:     { size: 52, family: 'Courier New, monospace', color: '#ffffff', shadow: '#2acfaf', align: 'center', baseline: 0.5, glow: true, glowColor: '#2acfaf', glowSize: 30 },
    impact:    { size: 72, family: 'Courier New, monospace', color: '#ff4f4f', shadow: '#000000', align: 'center', baseline: 0.5, glow: true, glowColor: '#ff4f4f', glowSize: 25 },
    chapter:   { size: 56, family: 'Courier New, monospace', color: '#2acfaf', shadow: '#000000', align: 'center', baseline: 0.5, glow: true, glowColor: '#2acfaf', glowSize: 20 },
    earth_title: { size: 48, family: 'Courier New, monospace', color: '#ffffff', shadow: '#000000', align: 'center', baseline: 0.08, glow: true, glowColor: '#2acfaf', glowSize: 25 },
    earth_env: { size: 40, family: 'Courier New, monospace', color: '#2acfaf', shadow: '#000000', align: 'center', baseline: 0.90, glow: true, glowColor: '#2acfaf', glowSize: 18 },
    logo:      { size: 140, family: 'Courier New, monospace', color: '#2acfaf', shadow: '#000000', align: 'center', baseline: 0.45, glow: true, glowColor: '#5fffdf', glowSize: 50, letterSpacing: 30 },
    logo_sub:  { size: 48, family: 'Courier New, monospace', color: '#ffffff', shadow: '#2acfaf', align: 'center', baseline: 0.58, glow: true, glowColor: '#2acfaf', glowSize: 15 },
    tagline:   { size: 32, family: 'Courier New, monospace', color: '#c0c0c0', shadow: '#000000', align: 'center', baseline: 0.68 },
    features:  { size: 28, family: 'Courier New, monospace', color: '#8899aa', shadow: '#000000', align: 'center', baseline: 0.72 },
    coming:    { size: 64, family: 'Courier New, monospace', color: '#ffffff', shadow: '#2acfaf', align: 'center', baseline: 0.5, glow: true, glowColor: '#ffffff', glowSize: 20 },
    credit:    { size: 22, family: 'Courier New, monospace', color: '#667788', shadow: '#000000', align: 'center', baseline: 0.82 }
  };

  /* Speaker portrait + dialogue box styling */
  const SPEAKERS = {
    ELDER: { color: '#4848d0', glowColor: '#7050c0', name: 'ARCHAEON PRIME', sprite: 'elder' },
    ARKE:  { color: '#2acfaf', glowColor: '#5fffdf', name: 'ARKE', sprite: 'methi_down' }
  };

  /* Queue narration from timeline */
  function queueNarration(entry, startTime) {
    activeTexts.push({
      text: entry.text,
      style: entry.style || 'subtitle',
      speaker: entry.speaker || null,
      startTime: startTime,
      duration: entry.dur,
      typewriter: true,
      typeSpeed: 35,  // chars per second
      phase: 0        // 0=typing, 1=hold, 2=fade
    });
  }

  /* Draw dialogue box with speaker portrait */
  function drawDialogue(ctx, speaker, text, progress, alpha) {
    const sp = SPEAKERS[speaker];
    if (!sp) return;

    ctx.save();
    ctx.globalAlpha = alpha;

    // Dialogue box background
    const boxW = 900, boxH = 140;
    const boxX = (CFG.W - boxW) / 2;
    const boxY = CFG.H * 0.72;

    // Dark semi-transparent box
    ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
    ctx.fillRect(boxX, boxY, boxW, boxH);

    // Border glow
    ctx.strokeStyle = sp.color;
    ctx.lineWidth = 2;
    ctx.shadowColor = sp.glowColor;
    ctx.shadowBlur = 10;
    ctx.strokeRect(boxX, boxY, boxW, boxH);
    ctx.shadowBlur = 0;

    // Speaker name
    ctx.fillStyle = sp.color;
    ctx.font = 'bold 20px "Courier New", monospace';
    ctx.fillText(sp.name, boxX + 90, boxY + 28);

    // Name underline
    ctx.fillStyle = sp.color;
    ctx.fillRect(boxX + 90, boxY + 34, ctx.measureText(sp.name).width, 2);

    // Portrait
    const portrait = SpriteRenderer.get(sp.sprite, 5);
    if (portrait) {
      ctx.shadowColor = sp.glowColor;
      ctx.shadowBlur = 15;
      ctx.drawImage(portrait, boxX + 8, boxY + 10, 72, 72);
      ctx.shadowBlur = 0;
    }

    // Text with typewriter effect
    const visibleChars = Math.floor(text.length * progress);
    const visibleText = text.substring(0, visibleChars);

    ctx.fillStyle = '#e0e0e0';
    ctx.font = '22px "Courier New", monospace';

    // Handle multi-line
    const lines = visibleText.split('\n');
    for (let i = 0; i < lines.length; i++) {
      ctx.fillText(lines[i], boxX + 90, boxY + 62 + i * 28);
    }

    // Blinking cursor
    if (progress < 1 && Math.floor(Date.now() / 300) % 2 === 0) {
      const lastLine = lines[lines.length - 1] || '';
      const cursorX = boxX + 90 + ctx.measureText(lastLine).width + 2;
      const cursorY = boxY + 46 + (lines.length - 1) * 28;
      ctx.fillStyle = sp.color;
      ctx.fillRect(cursorX, cursorY, 12, 20);
    }

    ctx.restore();
  }

  /* Draw cinematic text (titles, impacts, etc.) */
  function drawCinematicText(ctx, text, style, progress, alpha) {
    const s = FONTS[style] || FONTS.subtitle;
    ctx.save();
    ctx.globalAlpha = alpha;

    ctx.font = `bold ${s.size}px ${s.family}`;
    ctx.textAlign = s.align || 'center';
    ctx.textBaseline = 'middle';

    const cx = CFG.W / 2;
    const cy = CFG.H * (s.baseline || 0.5);

    // Glow
    if (s.glow) {
      ctx.shadowColor = s.glowColor;
      ctx.shadowBlur = s.glowSize * alpha;
    }

    // Shadow layer
    ctx.fillStyle = s.shadow || '#000000';
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
      ctx.fillText(lines[i], cx + 3, cy + 3 + i * (s.size * 1.3));
    }

    // Main text
    ctx.fillStyle = s.color;
    for (let i = 0; i < lines.length; i++) {
      // Letter spacing for logo
      if (s.letterSpacing) {
        const line = lines[i];
        let totalW = 0;
        for (let c = 0; c < line.length; c++) totalW += ctx.measureText(line[c]).width + s.letterSpacing;
        let startX = cx - totalW / 2;
        for (let c = 0; c < line.length; c++) {
          const charW = ctx.measureText(line[c]).width;
          ctx.fillText(line[c], startX + charW / 2, cy + i * (s.size * 1.3));
          startX += charW + s.letterSpacing;
        }
      } else {
        ctx.fillText(lines[i], cx, cy + i * (s.size * 1.3));
      }
    }

    ctx.shadowBlur = 0;
    ctx.restore();
  }

  /* Process and render all active texts */
  function update(ctx, currentTime) {
    for (const n of NARRATION) {
      const elapsed = currentTime - n.t;
      if (elapsed < 0 || elapsed > n.dur + 2.0) continue;

      // Calculate progress — SLOWER typing so users can read
      // Speaker dialogue: ~4 chars/sec effective, cinematic text: ~6 chars/sec
      let progress = Math.min(1, elapsed * (n.speaker ? 4 : 6) / Math.max(1, n.text.length));
      let alpha = 1;

      // Fade in — gentle 0.6s ease in
      if (elapsed < 0.6) alpha = elapsed / 0.6;
      // Fade out — starts 1.5s before end, fades over 1.8s for readability
      const fadeStart = n.dur - 1.5;
      if (elapsed > fadeStart) alpha = Math.max(0, 1 - (elapsed - fadeStart) / 1.8);

      if (alpha <= 0) continue;

      if (n.speaker) {
        drawDialogue(ctx, n.speaker, n.text, progress, alpha);
      } else {
        drawCinematicText(ctx, n.text, n.style || 'subtitle', progress, alpha);
      }
    }
  }

  /* Draw scanlines overlay for retro feel */
  function drawScanlines(ctx, alpha) {
    ctx.save();
    ctx.globalAlpha = (alpha || 0.04);
    ctx.fillStyle = '#000000';
    for (let y = 0; y < CFG.H; y += 4) {
      ctx.fillRect(0, y, CFG.W, 1);
    }
    ctx.restore();
  }

  /* Draw vignette (dark edges) */
  function drawVignette(ctx, intensity) {
    const grad = ctx.createRadialGradient(
      CFG.W / 2, CFG.H / 2, CFG.W * 0.25,
      CFG.W / 2, CFG.H / 2, CFG.W * 0.75
    );
    grad.addColorStop(0, 'rgba(0,0,0,0)');
    grad.addColorStop(1, `rgba(0,0,0,${intensity || 0.6})`);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, CFG.W, CFG.H);
  }

  return { queueNarration, drawDialogue, drawCinematicText, update, drawScanlines, drawVignette };
})();
