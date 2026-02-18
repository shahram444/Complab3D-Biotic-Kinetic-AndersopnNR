/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   AUDIO: Web Audio API soundtrack engine
   Dark industrial cinematic score — metallic, relentless, mechanical
   ============================================================ */

const AudioEngine = (() => {
  let ctx = null;
  let masterGain = null;
  let compressor = null;
  let started = false;
  let startTime = 0;

  /* ── INIT ── */
  function init() {
    ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Master compressor for that punchy industrial sound
    compressor = ctx.createDynamicsCompressor();
    compressor.threshold.value = -18;
    compressor.knee.value = 4;
    compressor.ratio.value = 8;
    compressor.attack.value = 0.003;
    compressor.release.value = 0.15;
    compressor.connect(ctx.destination);

    masterGain = ctx.createGain();
    masterGain.gain.value = 0.75;
    masterGain.connect(compressor);

    started = true;
    startTime = ctx.currentTime;
  }

  function now() { return ctx ? ctx.currentTime - startTime : 0; }
  function abs(t) { return startTime + t; }

  /* ════════════════════════════════════════════════════════════
     CORE SOUND BUILDING BLOCKS
     ════════════════════════════════════════════════════════════ */

  /* Basic oscillator with envelope */
  function osc(type, freq, t, dur, vol, dest) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.value = 0;
    o.connect(g);
    g.connect(dest || masterGain);

    const a = abs(t), e = abs(t + dur);
    const att = Math.min(0.008, dur * 0.05);
    const rel = Math.min(0.08, dur * 0.15);
    g.gain.setValueAtTime(0, a);
    g.gain.linearRampToValueAtTime(vol, a + att);
    g.gain.setValueAtTime(vol, e - rel);
    g.gain.linearRampToValueAtTime(0, e);
    o.start(a);
    o.stop(e + 0.05);
    return { o, g };
  }

  /* Oscillator with pitch sweep (for kicks, toms, industrial hits) */
  function oscSweep(type, freqStart, freqEnd, t, dur, vol, dest) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.connect(g);
    g.connect(dest || masterGain);

    const a = abs(t);
    o.frequency.setValueAtTime(freqStart, a);
    o.frequency.exponentialRampToValueAtTime(Math.max(1, freqEnd), a + dur * 0.8);
    g.gain.setValueAtTime(vol, a);
    g.gain.exponentialRampToValueAtTime(0.001, a + dur);
    o.start(a);
    o.stop(a + dur + 0.05);
  }

  /* Filtered noise burst (metallic, industrial percussion) */
  function noiseBurst(t, dur, vol, filterFreq, Q, filterType, dest) {
    const len = Math.ceil(ctx.sampleRate * (dur + 0.05));
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;

    const src = ctx.createBufferSource();
    src.buffer = buf;
    const filt = ctx.createBiquadFilter();
    filt.type = filterType || 'bandpass';
    filt.frequency.value = filterFreq || 2000;
    filt.Q.value = Q || 3;
    const g = ctx.createGain();
    g.gain.value = 0;

    src.connect(filt);
    filt.connect(g);
    g.connect(dest || masterGain);

    const a = abs(t);
    g.gain.setValueAtTime(vol, a);
    g.gain.exponentialRampToValueAtTime(0.001, a + dur);
    src.start(a);
    src.stop(a + dur + 0.05);
    return { src, filt, g };
  }

  /* Noise with filter sweep (risers, fallers, textures) */
  function noiseSwept(t, dur, vol, freqStart, freqEnd, Q, dest) {
    const len = Math.ceil(ctx.sampleRate * (dur + 0.1));
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;

    const src = ctx.createBufferSource();
    src.buffer = buf;
    const filt = ctx.createBiquadFilter();
    filt.type = 'bandpass';
    filt.frequency.value = freqStart;
    filt.Q.value = Q || 5;
    const g = ctx.createGain();

    src.connect(filt);
    filt.connect(g);
    g.connect(dest || masterGain);

    const a = abs(t), e = abs(t + dur);
    filt.frequency.setValueAtTime(freqStart, a);
    filt.frequency.exponentialRampToValueAtTime(freqEnd, e);
    g.gain.setValueAtTime(0, a);
    g.gain.linearRampToValueAtTime(vol, a + dur * 0.1);
    g.gain.linearRampToValueAtTime(vol * 0.8, e - dur * 0.2);
    g.gain.linearRampToValueAtTime(0, e);
    src.start(a);
    src.stop(e + 0.1);
  }

  /* ════════════════════════════════════════════════════════════
     INSTRUMENT PATCHES — Industrial / Metallic / Dark
     ════════════════════════════════════════════════════════════ */

  /* ANVIL HIT: The signature sound — metallic, ringing, industrial
     Multi-layered: filtered noise + resonant sine + high ring */
  function anvil(t, vol) {
    const v = vol || 0.14;
    // Body: sharp noise burst through tight bandpass (metallic resonance)
    noiseBurst(t, 0.18, v * 0.8, 3200, 12, 'bandpass');
    // Attack transient: very short high noise
    noiseBurst(t, 0.03, v * 1.2, 6500, 5, 'bandpass');
    // Metallic ring: sine at inharmonic frequency
    osc('sine', 987, t, 0.25, v * 0.15);   // resonant ring
    osc('sine', 1318, t, 0.15, v * 0.08);  // upper partial
    // Low thud body
    oscSweep('sine', 120, 40, t, 0.12, v * 0.6);
  }

  /* HEAVY ANVIL: Deeper, more powerful version */
  function heavyAnvil(t, vol) {
    const v = vol || 0.18;
    noiseBurst(t, 0.22, v * 0.9, 2400, 15, 'bandpass');
    noiseBurst(t, 0.04, v * 1.4, 5000, 6, 'bandpass');
    noiseBurst(t, 0.12, v * 0.4, 800, 4, 'bandpass');
    osc('sine', 740, t, 0.3, v * 0.12);
    oscSweep('sine', 180, 30, t, 0.18, v * 0.7);
  }

  /* INDUSTRIAL KICK: Deep, punchy, chest-shaking */
  function kick(t, vol) {
    const v = vol || 0.25;
    oscSweep('sine', 160, 28, t, 0.28, v);
    // Sub layer
    osc('sine', 36, t, 0.35, v * 0.5);
    // Click transient
    noiseBurst(t, 0.015, v * 0.6, 4000, 2, 'highpass');
  }

  /* MACHINE TICK: Lighter metallic tick for 16th note patterns */
  function tick(t, vol) {
    const v = vol || 0.06;
    noiseBurst(t, 0.04, v, 5500, 20, 'bandpass');
    osc('sine', 2200, t, 0.02, v * 0.3);
  }

  /* CLANG: Open metallic ring */
  function clang(t, vol) {
    const v = vol || 0.08;
    noiseBurst(t, 0.3, v * 0.5, 4200, 25, 'bandpass');
    osc('sine', 1480, t, 0.4, v * 0.3);
    osc('sine', 2100, t, 0.25, v * 0.15);
    osc('sine', 680, t, 0.35, v * 0.2);
  }

  /* SUB BASS PULSE: Dark pulsing low-end */
  function subPulse(t, dur, freq, vol) {
    const v = vol || 0.18;
    osc('sine', freq || 41.2, t, dur, v);           // E1
    osc('sine', (freq || 41.2) * 1.003, t, dur, v * 0.3); // detune
    osc('triangle', (freq || 41.2) * 2, t, dur, v * 0.08); // 1st harmonic
  }

  /* DARK PAD: Detuned saws filtered dark, for atmosphere */
  function darkPad(t, dur, freq, vol) {
    const v = vol || 0.04;
    // Create a filter node for darkness
    const filt = ctx.createBiquadFilter();
    filt.type = 'lowpass';
    filt.frequency.value = 800;
    filt.Q.value = 1;
    filt.connect(masterGain);

    osc('sawtooth', freq, t, dur, v, filt);
    osc('sawtooth', freq * 1.007, t, dur, v * 0.7, filt);
    osc('sawtooth', freq * 0.993, t, dur, v * 0.7, filt);
    osc('sawtooth', freq * 0.5, t, dur, v * 0.4, filt);
  }

  /* DARK NOTE: Single melodic note with dark timbre */
  function darkNote(t, dur, freq, vol) {
    const v = vol || 0.06;
    const filt = ctx.createBiquadFilter();
    filt.type = 'lowpass';
    filt.frequency.value = 1200;
    filt.Q.value = 2;
    filt.connect(masterGain);

    osc('sawtooth', freq, t, dur, v, filt);
    osc('square', freq * 1.002, t, dur, v * 0.3, filt);
    osc('triangle', freq * 0.5, t, dur, v * 0.2, filt);
  }

  /* STINGER: Massive dramatic hit */
  function stinger(t, vol) {
    const v = vol || 1.0;
    heavyAnvil(t, 0.2 * v);
    kick(t, 0.35 * v);
    noiseBurst(t, 0.5, 0.12 * v, 300, 2, 'lowpass');
    // Power chord: E minor
    darkPad(t, 3.0, 82.41, 0.06 * v);   // E2
    darkPad(t, 3.0, 123.47, 0.04 * v);  // B2
    darkPad(t, 2.5, 164.81, 0.04 * v);  // E3
    osc('sine', 41.2, t, 3.5, 0.15 * v);  // E1 sub
  }

  /* BOOM: Deep cinematic impact */
  function boom(t, vol) {
    const v = vol || 1.0;
    kick(t, 0.3 * v);
    noiseBurst(t, 0.4, 0.1 * v, 300, 2, 'lowpass');
    osc('sine', 30, t, 0.8, 0.18 * v);
    noiseBurst(t, 0.08, 0.08 * v, 1200, 3, 'bandpass');
  }

  /* HEARTBEAT: Slow double-thump like T2's underlying pulse */
  function heartbeat(t, vol) {
    const v = vol || 0.12;
    oscSweep('sine', 80, 30, t, 0.15, v);
    oscSweep('sine', 65, 25, t + 0.18, 0.12, v * 0.7);
  }

  /* ════════════════════════════════════════════════════════════
     THE SCORE — ~125 seconds
     Dark industrial cinematic — relentless, metallic, mechanical

     Key: E minor (Em)  |  Core BPM: 96
     Signature sound: Metallic anvil percussion pattern
     ════════════════════════════════════════════════════════════ */
  function composeScore() {
    if (!ctx) return;

    /* ── CONSTANTS ── */
    const BPM = 96;
    const BEAT = 60 / BPM;            // ~0.625s per beat
    const EIGHTH = BEAT / 2;           // ~0.3125s
    const SIXTEENTH = BEAT / 4;        // ~0.15625s
    const BAR = BEAT * 4;              // ~2.5s per bar

    // E minor scale frequencies
    const E1 = 41.2, B1 = 61.74, E2 = 82.41, G2 = 98.0, A2 = 110.0, B2 = 123.47;
    const D3 = 146.83, E3 = 164.81, G3 = 196.0, A3 = 220.0, B3 = 246.94;
    const D4 = 293.66, E4 = 329.63, G4 = 392.0, A4 = 440.0, B4 = 493.88;
    const E5 = 659.25;

    /* ── THE MAIN INDUSTRIAL RHYTHM PATTERN ──
       16th notes, 1 bar (16 steps)
       Pattern: X.x.X.x.Xx..X.x.  (X=heavy, x=light, .=rest)
       This is DIFFERENT from T2's pattern but has that same
       relentless, mechanical, factory-floor feel */
    const MAIN_PATTERN = [1, 0, 0.5, 0, 1, 0, 0.5, 0, 1, 0.5, 0, 0, 1, 0, 0.5, 0];

    /* Variation pattern for builds */
    const BUILD_PATTERN = [1, 0.5, 0.5, 0, 1, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 0, 1, 0.5, 1, 0.5];

    /* Double-time fill pattern */
    const FILL_PATTERN = [1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1, 1, 1, 1];

    /* Play a 1-bar rhythm pattern starting at time t */
    function playPattern(pattern, t, intensity) {
      const v = intensity || 1.0;
      for (let i = 0; i < 16; i++) {
        const hitVol = pattern[i];
        if (hitVol <= 0) continue;
        const hitT = t + i * SIXTEENTH;
        if (hitVol >= 0.8) {
          anvil(hitT, 0.14 * v * hitVol);
        } else {
          tick(hitT, 0.07 * v * hitVol);
        }
      }
    }

    /* ── THE MAIN MELODIC MOTIF ──
       Original 5-note motif in E minor, dark and fatalistic
       E3 - G3 - D3 - E3 - B2 (descending resolution)
       Rhythmically: long-short-long-short-looong */
    function playMotif(t, vol, octave) {
      const m = octave || 1;
      const v = vol || 0.06;
      darkNote(t,              BEAT * 1.5, E3 * m, v);
      darkNote(t + BEAT * 1.5, BEAT,       G3 * m, v * 0.9);
      darkNote(t + BEAT * 2.5, BEAT * 1.5, D3 * m, v * 0.85);
      darkNote(t + BEAT * 4.0, BEAT,       E3 * m, v * 0.8);
      darkNote(t + BEAT * 5.0, BEAT * 2.5, B2 * m, v * 0.95);
    }

    /* Counter-motif (response phrase) */
    function playCounter(t, vol, octave) {
      const m = octave || 1;
      const v = vol || 0.05;
      darkNote(t,              BEAT,       G3 * m, v);
      darkNote(t + BEAT,       BEAT,       A3 * m, v * 0.9);
      darkNote(t + BEAT * 2,   BEAT * 1.5, E3 * m, v * 0.85);
      darkNote(t + BEAT * 3.5, BEAT * 2,   D3 * m, v);
    }


    /* ═══════════════════════════════════════════════════════════
       SECTION 1: THE VOID (0-12s) — 0-~5 bars
       Darkness. Sub bass. Sparse metallic echoes in the dark.
       ═══════════════════════════════════════════════════════════ */

    // Deep sub drone fading in
    subPulse(0, 12, E1, 0.06);
    osc('sine', E1 * 1.5, 0, 12, 0.02);  // 5th harmonic hint

    // Eerie high metallic resonance (like distant factory)
    osc('sine', 1480, 2, 8, 0.008);
    osc('sine', 2100, 4, 9, 0.005);

    // Isolated anvil hits — like something stirring in the dark
    anvil(3.0, 0.06);
    anvil(5.2, 0.08);
    tick(6.5, 0.04);
    anvil(7.8, 0.10);
    tick(8.8, 0.03);
    anvil(9.5, 0.07);
    tick(10.2, 0.04);
    anvil(10.8, 0.12);      // getting closer...
    tick(11.2, 0.05);
    anvil(11.5, 0.10);

    // Heartbeat faintly emerges
    heartbeat(8, 0.04);
    heartbeat(10, 0.06);
    heartbeat(11.5, 0.08);


    /* ═══════════════════════════════════════════════════════════
       SECTION 2: AWAKENING (12-22s) — ~4 bars
       The machine starts. Rhythm crystallizes from chaos.
       Heartbeat → the Pattern begins.
       ═══════════════════════════════════════════════════════════ */

    // Sub bass deepens
    subPulse(12, 10, E1, 0.12);

    // Heartbeat continues, steadying
    for (let t = 12; t < 16; t += BEAT * 2) {
      heartbeat(t, 0.08);
    }

    // The Pattern emerges — sparse at first (just heavy hits)
    // Bar 1: only the heavy hits from the pattern
    for (let i = 0; i < 16; i++) {
      if (MAIN_PATTERN[i] >= 0.8) {
        const ht = 16 + i * SIXTEENTH;
        anvil(ht, 0.08);
      }
    }

    // Bar 2: full pattern starts — THE MACHINE AWAKENS
    playPattern(MAIN_PATTERN, 16 + BAR, 0.7);

    // Dark atmospheric pad
    darkPad(14, 8, E2, 0.03);
    darkPad(16, 6, B2, 0.02);

    // The motif enters — haunting, distant
    playMotif(17, 0.04, 1);


    /* ═══════════════════════════════════════════════════════════
       SECTION 3: WORLD REVEAL (22-38s) — ~6.5 bars
       Full industrial rhythm. Bass pulse locked in.
       Each world gets the machine treatment.
       ═══════════════════════════════════════════════════════════ */

    // Locked sub bass pulse on every beat
    for (let t = 22; t < 38; t += BEAT) {
      kick(t, 0.12);
      osc('sine', E1, t, BEAT * 0.8, 0.1);
    }

    // THE PATTERN — relentless, 6+ bars
    const numBars38 = Math.floor((38 - 22) / BAR);
    for (let bar = 0; bar < numBars38; bar++) {
      const bt = 22 + bar * BAR;
      playPattern(MAIN_PATTERN, bt, 0.85 + bar * 0.03);
      // Add clang accent on beat 1 of every other bar
      if (bar % 2 === 0) clang(bt, 0.06);
    }

    // Low bass riff under the rhythm (E - G - A - G progression)
    const bassRiff = [E2, E2, G2, G2, A2, A2, G2, G2];
    for (let i = 0; i < bassRiff.length; i++) {
      const bt = 22 + i * BAR * numBars38 / bassRiff.length;
      subPulse(bt, BAR * numBars38 / bassRiff.length, bassRiff[i] * 0.5, 0.08);
    }

    // Dark pad shifts for each world transition (~3.2s each)
    const worldDur = (38 - 22) / 5;
    const worldChords = [
      [E2, B2],                // Soil: Em
      [D3, A2],                // Deep: Dm
      [G2, D3],                // Seeps: G5
      [A2, E3],                // Perma: Am
      [E2, B2, G3]             // Hydro: Em full
    ];
    for (let w = 0; w < 5; w++) {
      const wt = 22 + w * worldDur;
      for (const f of worldChords[w]) {
        darkPad(wt, worldDur, f, 0.025);
      }
      // Boom on each world entry
      boom(wt + 0.05, 0.6 + w * 0.1);
    }

    // Motif plays during world reveal
    playMotif(24, 0.05, 1);
    playCounter(30, 0.04, 1);
    // Rising metallic tension
    noiseSwept(34, 4, 0.03, 500, 4000, 8);


    /* ═══════════════════════════════════════════════════════════
       SECTION 4: THE THREAT (38-50s) — ~5 bars
       Intensity increases. Double-time hints. Danger.
       ═══════════════════════════════════════════════════════════ */

    // Heavier sub
    for (let t = 38; t < 50; t += BEAT) {
      kick(t, 0.16);
      osc('sine', E1, t, BEAT * 0.7, 0.14);
    }

    // Pattern with increasing intensity
    const numBars50 = Math.floor((50 - 38) / BAR);
    for (let bar = 0; bar < numBars50; bar++) {
      const bt = 38 + bar * BAR;
      const pattern = bar >= numBars50 - 1 ? BUILD_PATTERN : MAIN_PATTERN;
      playPattern(pattern, bt, 1.0 + bar * 0.05);

      // Heavy anvil accent every bar
      heavyAnvil(bt, 0.1 + bar * 0.01);
    }

    // Menacing low melody — descending, threatening
    const threatMelody = [E3, D3, B2, A2, G2, A2, B2, G2];
    for (let i = 0; i < threatMelody.length; i++) {
      darkNote(39 + i * 1.4, 1.0, threatMelody[i], 0.055);
    }

    // Dark pad: Em → Cm → Bm (descending darkness)
    darkPad(38, 4, E2, 0.04);
    darkPad(38, 4, B2, 0.03);
    darkPad(42, 4, A2, 0.04);   // Am (relative minor feel)
    darkPad(42, 4, E3, 0.03);
    darkPad(46, 4, B2, 0.04);   // B5 (tension)
    darkPad(46, 4, G2, 0.035);

    // Danger stingers
    boom(39, 0.9);
    clang(43, 0.1);
    boom(47, 1.0);

    // Industrial noise texture underneath
    noiseSwept(40, 10, 0.015, 200, 1500, 4);


    /* ═══════════════════════════════════════════════════════════
       SECTION 5: POWER / GROWTH (50-65s) — ~6 bars
       Impact moments for CONSUME/GROW/MULTIPLY
       Then the machine resumes with heroic undertone
       ═══════════════════════════════════════════════════════════ */

    // Sub foundation
    subPulse(50, 15, E1, 0.1);

    // CONSUME — massive hit (51s)
    stinger(51, 0.9);
    darkNote(51.3, 2.5, E3, 0.08);
    // Sparse ticks after impact
    tick(52.0, 0.05); tick(52.5, 0.04); tick(53.0, 0.05);

    // GROW — second impact (54s)
    boom(54, 1.1);
    heavyAnvil(54, 0.15);
    darkNote(54.3, 2.5, G3, 0.08);
    tick(55.0, 0.05); tick(55.5, 0.04); tick(56.0, 0.05);

    // MULTIPLY — biggest impact (57s)
    stinger(57, 1.2);
    darkNote(57.3, 2.5, B3, 0.09);

    // The machine resumes — building back up
    for (let bar = 0; bar < 3; bar++) {
      const bt = 59 + bar * BAR;
      playPattern(BUILD_PATTERN, bt, 0.8 + bar * 0.15);
      kick(bt, 0.14 + bar * 0.03);
    }
    // Bass locked again
    for (let t = 59; t < 65; t += BEAT) {
      kick(t, 0.13);
      osc('sine', E1, t, BEAT * 0.7, 0.1);
    }

    // Motif returns — now with more power
    playMotif(60, 0.06, 1);

    // Heroic pad (adding the 5th — brighter but still dark)
    darkPad(60, 5, E2, 0.04);
    darkPad(60, 5, B2, 0.035);
    darkPad(60, 5, E3, 0.03);


    /* ═══════════════════════════════════════════════════════════
       SECTION 6: JOURNEY MONTAGE (65-82s) — ~7 bars
       PEAK INTENSITY. Everything at once.
       Fast cuts = double-time hints, max energy.
       ═══════════════════════════════════════════════════════════ */

    // Relentless sub
    for (let t = 65; t < 82; t += BEAT) {
      kick(t, 0.18);
      osc('sine', E1, t, BEAT * 0.6, 0.15);
    }

    // The Pattern at full power with variations
    const numBars82 = Math.floor((82 - 65) / BAR);
    for (let bar = 0; bar < numBars82; bar++) {
      const bt = 65 + bar * BAR;
      // Alternate between main and build patterns
      const pattern = bar % 4 === 3 ? FILL_PATTERN : (bar % 2 === 0 ? MAIN_PATTERN : BUILD_PATTERN);
      playPattern(pattern, bt, 1.1);
      // Heavy accent every bar
      heavyAnvil(bt, 0.12);
      // Clang on odd bars
      if (bar % 2 === 1) clang(bt + BEAT * 2, 0.07);
    }

    // Bass riff intensifies — moving between notes
    const journeyBass = [E2, E2, G2, A2, B2, A2, G2];
    for (let i = 0; i < journeyBass.length; i++) {
      const dur = (82 - 65) / journeyBass.length;
      subPulse(65 + i * dur, dur, journeyBass[i] * 0.5, 0.1);
    }

    // Chapter booms
    const chapterHits = [66, 69.5, 72.5, 75.5, 78.5];
    for (let i = 0; i < chapterHits.length; i++) {
      boom(chapterHits[i], 0.8 + i * 0.08);
      heavyAnvil(chapterHits[i], 0.12 + i * 0.02);
    }

    // Motif fragments — faster, more urgent
    darkNote(66, BEAT * 1.2, E3, 0.06);
    darkNote(67, BEAT * 1.2, G3, 0.06);
    darkNote(69.5, BEAT * 1.2, D3, 0.06);
    darkNote(70.5, BEAT * 1.2, E3, 0.06);
    // Ascending through the journey
    darkNote(72.5, BEAT * 1.2, G3, 0.06);
    darkNote(73.5, BEAT * 1.2, A3, 0.06);
    darkNote(75.5, BEAT * 1.2, B3, 0.07);
    darkNote(76.5, BEAT * 1.2, D4, 0.07);
    darkNote(78.5, BEAT * 1.5, E4, 0.08);  // Peak note!

    // Pad layers building
    darkPad(65, 8, E2, 0.04);
    darkPad(65, 8, B2, 0.03);
    darkPad(73, 9, A2, 0.04);
    darkPad(73, 9, E3, 0.035);

    // Rising metallic sweep to climax
    noiseSwept(78, 4, 0.04, 300, 6000, 6);

    // Ticking accelerates at very end
    for (let i = 0; i < 16; i++) {
      tick(80 + i * 0.12, 0.04 + i * 0.003);
    }


    /* ═══════════════════════════════════════════════════════════
       SECTION 7: THE STAKES (82-95s) — ~5 bars
       Emotional weight. Slower. The motif in full.
       Heartbeat returns. Building to the title.
       ═══════════════════════════════════════════════════════════ */

    // Deep sub
    subPulse(82, 13, E1, 0.12);

    // Slow, heavy beats — half-time feel
    for (let t = 82; t < 92; t += BEAT * 2) {
      kick(t, 0.2);
      heavyAnvil(t, 0.1);
    }

    // Light ticking continues underneath
    for (let t = 82; t < 92; t += BEAT) {
      tick(t + BEAT * 0.5, 0.03);
    }

    // Heartbeat — fate
    for (let t = 82; t < 92; t += BEAT * 2.5) {
      heartbeat(t + BEAT, 0.07);
    }

    // THE MOTIF — slow, full, emotional, final statement
    playMotif(83, 0.07, 1);
    // Counter-motif answers
    playCounter(88, 0.06, 1);

    // Emotional pad: Em → C → Am → B (cinematic chord progression)
    darkPad(82, 3.5, E2, 0.05);
    darkPad(82, 3.5, G2, 0.04);
    darkPad(82, 3.5, B2, 0.035);

    darkPad(85.5, 3.5, A2, 0.05);   // Am → C
    darkPad(85.5, 3.5, E3, 0.04);

    darkPad(89, 3, G2, 0.05);       // G
    darkPad(89, 3, D3, 0.04);
    darkPad(89, 3, B2, 0.035);

    // BUILD TO TITLE: accelerating pattern
    playPattern(BUILD_PATTERN, 91, 0.8);
    // Accelerating anvil hits into title
    for (let i = 0; i < 16; i++) {
      const ht = 92 + i * (0.2 - i * 0.008);
      if (ht < 95.8) {
        const hv = 0.08 + i * 0.008;
        anvil(ht, hv);
        if (i % 3 === 0) kick(ht, 0.1 + i * 0.01);
      }
    }

    // Rising sweep into title hit
    noiseSwept(92, 4, 0.05, 200, 8000, 5);
    oscSweep('sawtooth', 80, 2000, 93, 3, 0.03);


    /* ═══════════════════════════════════════════════════════════
       SECTION 8: TITLE REVEAL (95-108s)
       MASSIVE STINGER. Power chord sustain. Motif one final time.
       ═══════════════════════════════════════════════════════════ */

    // THE HIT — everything at once
    stinger(96, 1.3);
    clang(96, 0.15);
    // Extra sub impact
    osc('sine', E1, 96, 4, 0.2);
    osc('sine', E1 * 0.5, 96, 5, 0.1);  // Sub-sub

    // Sustained power chord: Em
    darkPad(96, 10, E2, 0.06);
    darkPad(96, 10, B2, 0.05);
    darkPad(96, 10, E3, 0.05);
    darkPad(96, 10, G3, 0.04);
    osc('triangle', E2, 96, 10, 0.04);
    osc('triangle', E3, 96, 10, 0.03);

    // Slow heartbeat under the title
    for (let t = 97.5; t < 106; t += BEAT * 3) {
      heartbeat(t, 0.08);
    }

    // Sparse heavy hits - like a clock ticking fate
    for (let t = 98; t < 106; t += BEAT * 2) {
      heavyAnvil(t, 0.08);
    }

    // The motif — final time, high octave, triumphant/fatalistic
    playMotif(98, 0.07, 2);  // octave up

    // Subtitle boom
    boom(101.5, 1.0);

    // Tagline stinger
    boom(106, 0.7);
    clang(106, 0.08);


    /* ═══════════════════════════════════════════════════════════
       SECTION 9: CLOSING (108-125s)
       Fade. Sparse echoes. The machine winds down.
       ═══════════════════════════════════════════════════════════ */

    // Fading sub
    subPulse(108, 12, E1, 0.06);

    // Sparse pad
    darkPad(108, 8, E2, 0.025);
    darkPad(108, 8, B2, 0.02);

    // Isolated motif notes — echoing into darkness
    darkNote(110, 2.5, E3, 0.04);
    darkNote(113, 2.5, G3, 0.03);
    darkNote(116, 3.0, B2, 0.025);

    // Last few metallic echoes
    tick(110, 0.03);
    anvil(112, 0.04);
    tick(115, 0.025);
    anvil(118, 0.03);

    // Final heartbeat
    heartbeat(119, 0.06);

    // Last sub rumble
    osc('sine', E1, 119, 6, 0.04);
    osc('sine', E1 * 0.5, 120, 5, 0.02);

    // Silence falls
  }

  /* ── SFX (gameplay sounds for demo moments) ── */
  function sfxEat(t) {
    osc('square', 523, t, 0.05, 0.06);
    osc('square', 784, t + 0.05, 0.06, 0.06);
    osc('square', 1047, t + 0.1, 0.08, 0.05);
  }

  function sfxDivide(t) {
    for (let i = 0; i < 6; i++) osc('square', 300 + i * 100, t + i * 0.06, 0.1, 0.04);
    osc('triangle', 1200, t + 0.36, 0.25, 0.03);
  }

  function sfxEatMethane(t) {
    osc('triangle', 659, t, 0.06, 0.05);
    osc('triangle', 880, t + 0.06, 0.06, 0.05);
    osc('triangle', 1175, t + 0.12, 0.12, 0.04);
    osc('triangle', 1397, t + 0.18, 0.15, 0.03);
  }

  return {
    init, now, composeScore,
    sfxEat, sfxDivide, sfxEatMethane,
    get ctx() { return ctx; },
    get started() { return started; }
  };
})();
