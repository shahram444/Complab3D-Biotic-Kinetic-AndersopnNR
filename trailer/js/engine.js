/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   ENGINE: Main rendering loop, initialization, compositing
   ============================================================ */

const Engine = (() => {
  let canvas, ctx;
  let running = false;
  let trailerTime = 0;
  let lastFrameTime = 0;
  let overlay;

  /* Scene transition state */
  let globalFadeAlpha = 1;   // starts fully black
  let endFadeAlpha = 0;

  /* ── INITIALIZATION ── */
  function init() {
    canvas = document.getElementById('screen');
    ctx = canvas.getContext('2d');
    overlay = document.getElementById('overlay');

    // Ensure crisp pixel art
    ctx.imageSmoothingEnabled = false;

    // Click to start
    overlay.addEventListener('click', start);

    // Also allow keyboard
    document.addEventListener('keydown', (e) => {
      if (!running && (e.code === 'Space' || e.code === 'Enter')) {
        e.preventDefault();
        start();
      }
    });
  }

  /* ── START TRAILER ── */
  function start() {
    if (running) return;
    running = true;
    trailerTime = 0;

    // Hide overlay
    overlay.classList.add('hidden');

    // Start audio
    AudioEngine.init();
    AudioEngine.composeScore();

    // Set initial camera
    Camera.set(CFG.W / 2, CFG.H / 2, 1);

    // Set letterbox
    document.getElementById('container').classList.add('letterbox-wide');

    // Reset systems
    Particles.clear();
    Scenes.reset();

    // Begin render loop
    lastFrameTime = performance.now();
    requestAnimationFrame(loop);
  }

  /* ── MAIN RENDER LOOP ── */
  function loop(timestamp) {
    if (!running) return;

    const dt = Math.min(0.05, (timestamp - lastFrameTime) / 1000);
    lastFrameTime = timestamp;
    trailerTime += dt;

    // Stop at end
    if (trailerTime >= CFG.DURATION) {
      running = false;
      // Show replay option
      renderEndScreen();
      return;
    }

    // Clear
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Update camera
    Camera.update(dt);

    // Render current scene
    Scenes.render(ctx, trailerTime, dt);

    // Render particles on top
    Particles.updateAll(dt);
    Particles.drawAll(ctx);

    // Render text / narration on top of everything
    TextRenderer.update(ctx, trailerTime);

    // Scanline overlay for retro feel
    TextRenderer.drawScanlines(ctx, 0.03);

    // Global fade from black at start
    if (trailerTime < 1.5) {
      globalFadeAlpha = Math.max(0, 1 - trailerTime / 1.5);
      ctx.save();
      ctx.globalAlpha = globalFadeAlpha;
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();
    }

    // Scene transition fades (between major sections)
    drawSceneTransitions();

    // Progress bar at very bottom
    drawProgressBar();

    requestAnimationFrame(loop);
  }

  /* ── SCENE TRANSITION FADES ── */
  function drawSceneTransitions() {
    // Brief fade-to-black between major sections
    const transitions = [
      { t: TIMELINE.PIXEL_AWAKEN.end - 0.3, dur: 0.6 },
      { t: TIMELINE.ELDER_CALLS.end - 0.3, dur: 0.6 },
      { t: TIMELINE.RIVALS_THREAT.end - 0.2, dur: 0.4 },
      { t: TIMELINE.POWER_GROW.end - 0.3, dur: 0.6 },
      { t: TIMELINE.JOURNEY_MONTAGE.end - 0.2, dur: 0.4 },
      { t: TIMELINE.EARTH_STAKES.end - 0.3, dur: 0.6 }
    ];

    for (const tr of transitions) {
      const elapsed = trailerTime - tr.t;
      if (elapsed < 0 || elapsed > tr.dur) continue;
      const half = tr.dur / 2;
      const alpha = elapsed < half
        ? elapsed / half
        : 1 - (elapsed - half) / half;
      ctx.save();
      ctx.globalAlpha = Math.min(1, alpha * 0.9);
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      ctx.restore();
    }
  }

  /* ── PROGRESS BAR ── */
  function drawProgressBar() {
    const barH = 3;
    const progress = trailerTime / CFG.DURATION;
    ctx.save();
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#1a1a2a';
    ctx.fillRect(0, CFG.H - barH, CFG.W, barH);
    ctx.fillStyle = '#2acfaf';
    ctx.fillRect(0, CFG.H - barH, CFG.W * progress, barH);
    ctx.restore();
  }

  /* ── END SCREEN ── */
  function renderEndScreen() {
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, CFG.W, CFG.H);

    // Logo
    SpriteRenderer.drawGlow(ctx, 'methi_glow', CFG.W / 2, CFG.H * 0.35, 6, '#5fffdf', 30, 1);

    ctx.save();
    ctx.font = 'bold 48px "Courier New", monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#2acfaf';
    ctx.shadowColor = '#5fffdf';
    ctx.shadowBlur = 20;
    ctx.fillText('ARKE: GUARDIANS OF EARTH', CFG.W / 2, CFG.H * 0.52);
    ctx.shadowBlur = 0;

    ctx.font = '24px "Courier New", monospace';
    ctx.fillStyle = '#667788';
    ctx.fillText('Click to replay', CFG.W / 2, CFG.H * 0.65);
    ctx.restore();

    TextRenderer.drawVignette(ctx, 0.5);
    TextRenderer.drawScanlines(ctx, 0.03);

    // Allow replay
    overlay.classList.remove('hidden');
    document.getElementById('play-text').textContent = 'REPLAY TRAILER';
  }

  /* ── BOOT ── */
  init();

  return { start };
})();
