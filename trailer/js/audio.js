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
     THE SCORE — ~160 seconds
     Dark industrial cinematic — relentless, metallic, mechanical
     Rhythm pattern closely inspired by Brad Fiedel's T2 Main Title

     Key: E minor (Em)  |  Core BPM: 95
     Signature sound: Metallic anvil percussion pattern
     ════════════════════════════════════════════════════════════ */
  function composeScore() {
    if (!ctx) return;

    /* ── CONSTANTS ── */
    const BPM = 95;
    const BEAT = 60 / BPM;            // ~0.632s per beat
    const EIGHTH = BEAT / 2;           // ~0.316s
    const SIXTEENTH = BEAT / 4;        // ~0.158s
    const BAR = BEAT * 4;              // ~2.526s per bar

    // E minor scale frequencies
    const E1 = 41.2, B1 = 61.74, E2 = 82.41, G2 = 98.0, A2 = 110.0, B2 = 123.47;
    const D3 = 146.83, E3 = 164.81, G3 = 196.0, A3 = 220.0, B3 = 246.94;
    const D4 = 293.66, E4 = 329.63, G4 = 392.0, A4 = 440.0, B4 = 493.88;
    const E5 = 659.25;

    /* ── THE MAIN INDUSTRIAL RHYTHM PATTERN ──
       16-step (16th notes), 1 bar
       Very close to T2's iconic pattern: X...X.x...X.X...
       Accents on positions 0,4,6,10,12 — with a subtle ghost on 9
       to make it just slightly different from Fiedel's original */
    const MAIN_PATTERN = [1, 0, 0, 0, 1, 0, 0.7, 0, 0, 0.3, 1, 0, 1, 0, 0, 0];

    /* Variation pattern for builds — fills in gaps */
    const BUILD_PATTERN = [1, 0, 0.4, 0, 1, 0.3, 0.7, 0, 0.4, 0.3, 1, 0, 1, 0.3, 0.5, 0];

    /* Double-time fill pattern */
    const FILL_PATTERN = [1, 0.5, 0.7, 0.4, 1, 0.5, 0.7, 0.4, 1, 0.5, 0.7, 0.5, 1, 0.7, 1, 0.7];

    /* Play a 1-bar rhythm pattern starting at time t */
    function playPattern(pattern, t, intensity) {
      const v = intensity || 1.0;
      for (let i = 0; i < 16; i++) {
        const hitVol = pattern[i];
        if (hitVol <= 0) continue;
        const hitT = t + i * SIXTEENTH;
        if (hitVol >= 0.8) {
          anvil(hitT, 0.14 * v * hitVol);
        } else if (hitVol >= 0.5) {
          anvil(hitT, 0.08 * v * hitVol);
        } else {
          tick(hitT, 0.06 * v * hitVol);
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
       SECTION 1: THE VOID (0-12s)
       Darkness. Sub bass. Sparse metallic echoes.
       ═══════════════════════════════════════════════════════════ */

    // Deep sub drone fading in
    subPulse(0, 12, E1, 0.06);
    osc('sine', E1 * 1.5, 0, 12, 0.02);

    // Eerie high metallic resonance (distant factory)
    osc('sine', 1480, 2, 8, 0.008);
    osc('sine', 2100, 4, 9, 0.005);

    // Isolated anvil hits — stirring in the dark
    anvil(3.0, 0.06);
    anvil(5.2, 0.08);
    tick(6.5, 0.04);
    anvil(7.8, 0.10);
    tick(8.8, 0.03);
    anvil(9.5, 0.07);
    tick(10.2, 0.04);
    anvil(10.8, 0.12);
    tick(11.2, 0.05);
    anvil(11.5, 0.10);

    // Heartbeat faintly emerges
    heartbeat(8, 0.04);
    heartbeat(10, 0.06);
    heartbeat(11.5, 0.08);


    /* ═══════════════════════════════════════════════════════════
       SECTION 2: ARKE CLOSEUP / AWAKENING (12-20s)
       The machine starts. Rhythm crystallizes.
       ═══════════════════════════════════════════════════════════ */

    subPulse(12, 8, E1, 0.1);

    // Heartbeat continues, steadying
    for (let t = 12; t < 16; t += BEAT * 2) {
      heartbeat(t, 0.08);
    }

    // Pattern emerges — sparse at first
    for (let i = 0; i < 16; i++) {
      if (MAIN_PATTERN[i] >= 0.8) {
        anvil(15 + i * SIXTEENTH, 0.07);
      }
    }

    // Full pattern starts
    playPattern(MAIN_PATTERN, 15 + BAR, 0.65);
    playPattern(MAIN_PATTERN, 15 + BAR * 2, 0.75);

    // Dark atmospheric pad
    darkPad(13, 7, E2, 0.03);
    darkPad(15, 5, B2, 0.02);

    // Motif enters — haunting, distant
    playMotif(16, 0.04, 1);


    /* ═══════════════════════════════════════════════════════════
       SECTION 3: ELDER CLOSEUP (20-27s)
       Deeper, more ceremonial. Ancient wisdom.
       ═══════════════════════════════════════════════════════════ */

    subPulse(20, 7, E1, 0.1);

    // Slower, weightier pattern
    for (let t = 20; t < 27; t += BEAT * 2) {
      heartbeat(t, 0.07);
    }

    // Pattern continues but with more weight
    const numBars27 = Math.floor((27 - 20) / BAR);
    for (let bar = 0; bar < numBars27; bar++) {
      playPattern(MAIN_PATTERN, 20 + bar * BAR, 0.7 + bar * 0.05);
    }

    // Deeper pad — purple/elder tones
    darkPad(20, 7, E2, 0.035);
    darkPad(20, 7, G2, 0.025);
    darkPad(23, 4, B2, 0.03);

    // Counter-motif for elder
    playCounter(22, 0.04, 1);

    // Boom on elder reveal
    boom(21, 0.7);


    /* ═══════════════════════════════════════════════════════════
       SECTION 4: ELDER CALLS / DIALOGUE (27-38s)
       Full industrial rhythm. Bass pulse locked in.
       ═══════════════════════════════════════════════════════════ */

    // Locked sub bass pulse
    for (let t = 27; t < 38; t += BEAT) {
      kick(t, 0.12);
      osc('sine', E1, t, BEAT * 0.8, 0.1);
    }

    // THE PATTERN — relentless
    const numBars38 = Math.floor((38 - 27) / BAR);
    for (let bar = 0; bar < numBars38; bar++) {
      const bt = 27 + bar * BAR;
      playPattern(MAIN_PATTERN, bt, 0.8 + bar * 0.04);
      if (bar % 2 === 0) clang(bt, 0.05);
    }

    // Bass riff
    const bassRiff4 = [E2, E2, G2, A2, G2];
    for (let i = 0; i < bassRiff4.length; i++) {
      const dur = (38 - 27) / bassRiff4.length;
      subPulse(27 + i * dur, dur, bassRiff4[i] * 0.5, 0.07);
    }

    // Dark pads
    darkPad(27, 5.5, E2, 0.03);
    darkPad(27, 5.5, B2, 0.025);
    darkPad(32.5, 5.5, A2, 0.03);
    darkPad(32.5, 5.5, E3, 0.025);

    // Motif
    playMotif(29, 0.05, 1);

    // Rising tension into earth cross
    noiseSwept(35, 3, 0.03, 500, 3500, 7);


    /* ═══════════════════════════════════════════════════════════
       SECTION 5: EARTH CROSS-SECTION (38-63s)
       Grand, scientific, revelatory. Each world gets a boom.
       The rhythm is steady, the pad shifts with each environment.
       ═══════════════════════════════════════════════════════════ */

    // Deep sustained sub
    subPulse(38, 25, E1, 0.09);

    // Locked beats
    for (let t = 38; t < 63; t += BEAT) {
      kick(t, 0.11);
      osc('sine', E1, t, BEAT * 0.7, 0.09);
    }

    // THE PATTERN — steady, scientific, relentless
    const numBars63 = Math.floor((63 - 38) / BAR);
    for (let bar = 0; bar < numBars63; bar++) {
      const bt = 38 + bar * BAR;
      playPattern(MAIN_PATTERN, bt, 0.8 + bar * 0.02);
      if (bar % 3 === 0) clang(bt, 0.05);
    }

    // Each world (~5s each): pad shifts + boom
    const worldDur = (63 - 38) / 5;
    const worldChords = [
      [E2, B2],          // Soil: Em
      [D3, A2],          // Deep: Dm
      [G2, D3],          // Seeps: G5
      [A2, E3],          // Perma: Am
      [E2, B2, G3]       // Hydro: Em full
    ];
    for (let w = 0; w < 5; w++) {
      const wt = 38 + w * worldDur;
      for (const f of worldChords[w]) {
        darkPad(wt, worldDur, f, 0.025);
      }
      boom(wt + 0.05, 0.6 + w * 0.08);
      heavyAnvil(wt + 0.1, 0.08 + w * 0.01);
    }

    // Motif during earth reveal
    playMotif(40, 0.05, 1);
    playCounter(47, 0.04, 1);
    playMotif(54, 0.05, 1);

    // Rising tension at end
    noiseSwept(59, 4, 0.03, 400, 4500, 6);


    /* ═══════════════════════════════════════════════════════════
       SECTION 6: RIVAL CLOSEUP (63-69s)
       Menacing. Dark. Red. The rhythm gets heavier.
       ═══════════════════════════════════════════════════════════ */

    subPulse(63, 6, E1, 0.12);

    // Heavy hits
    for (let t = 63; t < 69; t += BEAT) {
      kick(t, 0.15);
      osc('sine', E1, t, BEAT * 0.6, 0.13);
    }

    // Pattern intensifies
    const numBars69 = Math.floor((69 - 63) / BAR);
    for (let bar = 0; bar < numBars69; bar++) {
      playPattern(BUILD_PATTERN, 63 + bar * BAR, 1.0);
      heavyAnvil(63 + bar * BAR, 0.12);
    }

    // Danger stinger on entry
    boom(63.5, 1.0);
    clang(64, 0.1);

    // Menacing pad
    darkPad(63, 6, E2, 0.04);
    darkPad(63, 6, G2, 0.035);
    darkPad(66, 3, B2, 0.04);

    // Descending threat melody fragment
    darkNote(64, 1.0, E3, 0.06);
    darkNote(65.2, 1.0, D3, 0.055);
    darkNote(66.4, 1.0, B2, 0.05);
    darkNote(67.6, 1.5, A2, 0.06);

    // Industrial noise
    noiseSwept(64, 5, 0.015, 200, 1200, 4);


    /* ═══════════════════════════════════════════════════════════
       SECTION 7: RIVALS THREAT (69-81s)
       Intensity increases. Danger chase. Double-time hints.
       ═══════════════════════════════════════════════════════════ */

    for (let t = 69; t < 81; t += BEAT) {
      kick(t, 0.16);
      osc('sine', E1, t, BEAT * 0.7, 0.14);
    }

    const numBars81 = Math.floor((81 - 69) / BAR);
    for (let bar = 0; bar < numBars81; bar++) {
      const bt = 69 + bar * BAR;
      const pattern = bar >= numBars81 - 1 ? BUILD_PATTERN : MAIN_PATTERN;
      playPattern(pattern, bt, 1.0 + bar * 0.04);
      heavyAnvil(bt, 0.1 + bar * 0.01);
    }

    // Menacing melody
    const threatMelody = [E3, D3, B2, A2, G2, A2, B2, G2];
    for (let i = 0; i < threatMelody.length; i++) {
      darkNote(70 + i * 1.3, 0.9, threatMelody[i], 0.05);
    }

    // Dark pads
    darkPad(69, 4, E2, 0.04);
    darkPad(69, 4, B2, 0.03);
    darkPad(73, 4, A2, 0.04);
    darkPad(73, 4, E3, 0.03);
    darkPad(77, 4, B2, 0.04);
    darkPad(77, 4, G2, 0.035);

    // Danger stingers
    boom(70, 0.9);
    clang(74, 0.1);
    boom(78, 1.0);

    noiseSwept(71, 10, 0.015, 200, 1500, 4);


    /* ═══════════════════════════════════════════════════════════
       SECTION 8: POWER / GROWTH (81-96s)
       CONSUME / GROW / MULTIPLY impacts + machine resume
       ═══════════════════════════════════════════════════════════ */

    subPulse(81, 15, E1, 0.1);

    // CONSUME
    stinger(82, 0.9);
    darkNote(82.3, 2.5, E3, 0.08);
    tick(83.0, 0.05); tick(83.5, 0.04); tick(84.0, 0.05);

    // GROW
    boom(86, 1.1);
    heavyAnvil(86, 0.15);
    darkNote(86.3, 2.5, G3, 0.08);
    tick(87.0, 0.05); tick(87.5, 0.04); tick(88.0, 0.05);

    // MULTIPLY
    stinger(90, 1.2);
    darkNote(90.3, 2.5, B3, 0.09);

    // Machine resumes
    for (let bar = 0; bar < 3; bar++) {
      const bt = 91 + bar * BAR;
      playPattern(BUILD_PATTERN, bt, 0.8 + bar * 0.12);
      kick(bt, 0.14 + bar * 0.02);
    }
    for (let t = 91; t < 96; t += BEAT) {
      kick(t, 0.13);
      osc('sine', E1, t, BEAT * 0.7, 0.1);
    }

    // Motif returns
    playMotif(92, 0.06, 1);

    // Heroic pad
    darkPad(92, 4, E2, 0.04);
    darkPad(92, 4, B2, 0.035);
    darkPad(92, 4, E3, 0.03);


    /* ═══════════════════════════════════════════════════════════
       SECTION 9: JOURNEY MONTAGE (96-113s)
       PEAK INTENSITY. Everything at once. Max energy.
       ═══════════════════════════════════════════════════════════ */

    for (let t = 96; t < 113; t += BEAT) {
      kick(t, 0.18);
      osc('sine', E1, t, BEAT * 0.6, 0.15);
    }

    const numBars113 = Math.floor((113 - 96) / BAR);
    for (let bar = 0; bar < numBars113; bar++) {
      const bt = 96 + bar * BAR;
      const pattern = bar % 4 === 3 ? FILL_PATTERN : (bar % 2 === 0 ? MAIN_PATTERN : BUILD_PATTERN);
      playPattern(pattern, bt, 1.1);
      heavyAnvil(bt, 0.12);
      if (bar % 2 === 1) clang(bt + BEAT * 2, 0.07);
    }

    // Bass riff intensifies
    const journeyBass = [E2, E2, G2, A2, B2, A2, G2];
    for (let i = 0; i < journeyBass.length; i++) {
      const dur = (113 - 96) / journeyBass.length;
      subPulse(96 + i * dur, dur, journeyBass[i] * 0.5, 0.1);
    }

    // Chapter booms
    const chapterHits = [97, 100.5, 103.5, 106.5, 109.5];
    for (let i = 0; i < chapterHits.length; i++) {
      boom(chapterHits[i], 0.8 + i * 0.08);
      heavyAnvil(chapterHits[i], 0.12 + i * 0.02);
    }

    // Motif fragments — faster, more urgent
    darkNote(97, BEAT * 1.2, E3, 0.06);
    darkNote(98, BEAT * 1.2, G3, 0.06);
    darkNote(100.5, BEAT * 1.2, D3, 0.06);
    darkNote(101.5, BEAT * 1.2, E3, 0.06);
    darkNote(103.5, BEAT * 1.2, G3, 0.06);
    darkNote(104.5, BEAT * 1.2, A3, 0.06);
    darkNote(106.5, BEAT * 1.2, B3, 0.07);
    darkNote(107.5, BEAT * 1.2, D4, 0.07);
    darkNote(109.5, BEAT * 1.5, E4, 0.08);

    // Pad layers
    darkPad(96, 8, E2, 0.04);
    darkPad(96, 8, B2, 0.03);
    darkPad(104, 9, A2, 0.04);
    darkPad(104, 9, E3, 0.035);

    // Rising sweep
    noiseSwept(109, 4, 0.04, 300, 6000, 6);

    // Accelerating ticks
    for (let i = 0; i < 16; i++) {
      tick(111 + i * 0.12, 0.04 + i * 0.003);
    }


    /* ═══════════════════════════════════════════════════════════
       SECTION 10: EARTH STAKES (113-126s)
       Emotional weight. Slower. Heartbeat. Building to title.
       ═══════════════════════════════════════════════════════════ */

    subPulse(113, 13, E1, 0.12);

    // Half-time feel
    for (let t = 113; t < 123; t += BEAT * 2) {
      kick(t, 0.2);
      heavyAnvil(t, 0.1);
    }

    // Light ticking
    for (let t = 113; t < 123; t += BEAT) {
      tick(t + BEAT * 0.5, 0.03);
    }

    // Heartbeat — fate
    for (let t = 113; t < 123; t += BEAT * 2.5) {
      heartbeat(t + BEAT, 0.07);
    }

    // THE MOTIF — full, emotional
    playMotif(114, 0.07, 1);
    playCounter(119, 0.06, 1);

    // Emotional pads
    darkPad(113, 3.5, E2, 0.05);
    darkPad(113, 3.5, G2, 0.04);
    darkPad(113, 3.5, B2, 0.035);
    darkPad(116.5, 3.5, A2, 0.05);
    darkPad(116.5, 3.5, E3, 0.04);
    darkPad(120, 3, G2, 0.05);
    darkPad(120, 3, D3, 0.04);
    darkPad(120, 3, B2, 0.035);

    // BUILD TO TITLE
    playPattern(BUILD_PATTERN, 122, 0.8);
    for (let i = 0; i < 16; i++) {
      const ht = 123 + i * (0.2 - i * 0.008);
      if (ht < 126.8) {
        anvil(ht, 0.08 + i * 0.008);
        if (i % 3 === 0) kick(ht, 0.1 + i * 0.01);
      }
    }

    // Rising sweep
    noiseSwept(123, 4, 0.05, 200, 8000, 5);
    oscSweep('sawtooth', 80, 2000, 124, 3, 0.03);


    /* ═══════════════════════════════════════════════════════════
       SECTION 11: TITLE REVEAL (126-139s)
       MASSIVE STINGER. Power chord. Motif one final time.
       ═══════════════════════════════════════════════════════════ */

    // THE HIT
    stinger(127, 1.3);
    clang(127, 0.15);
    osc('sine', E1, 127, 4, 0.2);
    osc('sine', E1 * 0.5, 127, 5, 0.1);

    // Sustained power chord: Em
    darkPad(127, 10, E2, 0.06);
    darkPad(127, 10, B2, 0.05);
    darkPad(127, 10, E3, 0.05);
    darkPad(127, 10, G3, 0.04);
    osc('triangle', E2, 127, 10, 0.04);
    osc('triangle', E3, 127, 10, 0.03);

    // Slow heartbeat under title
    for (let t = 128.5; t < 137; t += BEAT * 3) {
      heartbeat(t, 0.08);
    }

    // Sparse heavy hits
    for (let t = 129; t < 137; t += BEAT * 2) {
      heavyAnvil(t, 0.08);
    }

    // Final motif — octave up
    playMotif(129, 0.07, 2);

    // Subtitle boom
    boom(133, 1.0);

    // Tagline stinger
    boom(137, 0.7);
    clang(137, 0.08);


    /* ═══════════════════════════════════════════════════════════
       SECTION 12: CLOSING (139-160s)
       Fade. Sparse echoes. The machine winds down to silence.
       ═══════════════════════════════════════════════════════════ */

    // Fading sub
    subPulse(139, 16, E1, 0.05);

    // Sparse pad
    darkPad(139, 10, E2, 0.025);
    darkPad(139, 10, B2, 0.02);

    // Isolated motif notes echoing
    darkNote(141, 2.5, E3, 0.04);
    darkNote(144, 2.5, G3, 0.03);
    darkNote(147, 3.0, B2, 0.025);

    // Metallic echoes
    tick(141, 0.03);
    anvil(143, 0.04);
    tick(146, 0.025);
    anvil(149, 0.03);
    tick(152, 0.02);

    // Final heartbeats
    heartbeat(150, 0.06);
    heartbeat(153, 0.04);

    // Last sub rumble
    osc('sine', E1, 152, 8, 0.03);
    osc('sine', E1 * 0.5, 153, 7, 0.015);

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
