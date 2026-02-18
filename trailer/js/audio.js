/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   AUDIO: Web Audio API soundtrack engine
   Original industrial/cinematic score (inspired by 80s synth)
   ============================================================ */

const AudioEngine = (() => {
  let ctx = null;
  let masterGain = null;
  let started = false;
  let startTime = 0;

  /* ── INIT ── */
  function init() {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    masterGain = ctx.createGain();
    masterGain.gain.value = 0.7;
    masterGain.connect(ctx.destination);
    started = true;
    startTime = ctx.currentTime;
  }

  /* ── UTILITIES ── */
  function now() { return ctx ? ctx.currentTime - startTime : 0; }

  function createOsc(type, freq, startT, endT, gainVal, dest) {
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    g.gain.value = 0;
    osc.connect(g);
    g.connect(dest || masterGain);

    const absStart = startTime + startT;
    const absEnd = startTime + endT;

    // Attack-sustain-release envelope
    const attack = Math.min(0.05, (endT - startT) * 0.1);
    const release = Math.min(0.1, (endT - startT) * 0.2);
    g.gain.setValueAtTime(0, absStart);
    g.gain.linearRampToValueAtTime(gainVal, absStart + attack);
    g.gain.setValueAtTime(gainVal, absEnd - release);
    g.gain.linearRampToValueAtTime(0, absEnd);

    osc.start(absStart);
    osc.stop(absEnd + 0.1);
    return { osc, gain: g };
  }

  function createNoise(startT, endT, gainVal, filterFreq, dest) {
    const bufferSize = ctx.sampleRate * (endT - startT + 0.1);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;

    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const filt = ctx.createBiquadFilter();
    filt.type = 'bandpass';
    filt.frequency.value = filterFreq || 800;
    filt.Q.value = 2;
    const g = ctx.createGain();
    g.gain.value = 0;

    src.connect(filt);
    filt.connect(g);
    g.connect(dest || masterGain);

    const absStart = startTime + startT;
    const absEnd = startTime + endT;
    const attack = 0.005;
    const release = Math.min(0.05, (endT - startT) * 0.3);

    g.gain.setValueAtTime(0, absStart);
    g.gain.linearRampToValueAtTime(gainVal, absStart + attack);
    g.gain.setValueAtTime(gainVal, absEnd - release);
    g.gain.linearRampToValueAtTime(0, absEnd);

    src.start(absStart);
    src.stop(absEnd + 0.1);
    return { src, gain: g };
  }

  /* ── SUB BASS DRONE ── */
  function subDrone(startT, endT, freq, vol) {
    createOsc('sine', freq, startT, endT, vol || 0.15, masterGain);
    // Add subtle detuned layer
    createOsc('sine', freq * 1.003, startT, endT, (vol || 0.15) * 0.4, masterGain);
  }

  /* ── METALLIC HIT (industrial percussion) ── */
  function metalHit(t, intensity) {
    const vol = (intensity || 1) * 0.12;
    const dur = 0.15;
    createNoise(t, t + dur, vol, 3500, masterGain);
    createNoise(t, t + dur * 0.5, vol * 0.7, 8000, masterGain);
    createOsc('sine', 80, t, t + 0.08, vol * 0.8, masterGain);
  }

  /* ── KICK DRUM ── */
  function kick(t, vol) {
    const v = vol || 0.2;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = 'sine';
    osc.connect(g);
    g.connect(masterGain);

    const absT = startTime + t;
    osc.frequency.setValueAtTime(150, absT);
    osc.frequency.exponentialRampToValueAtTime(30, absT + 0.15);
    g.gain.setValueAtTime(v, absT);
    g.gain.exponentialRampToValueAtTime(0.001, absT + 0.3);
    osc.start(absT);
    osc.stop(absT + 0.35);
  }

  /* ── SYNTH PAD ── */
  function pad(startT, endT, freq, vol) {
    const v = vol || 0.06;
    createOsc('sawtooth', freq, startT, endT, v * 0.5, masterGain);
    createOsc('sawtooth', freq * 1.005, startT, endT, v * 0.5, masterGain);
    createOsc('sawtooth', freq * 0.995, startT, endT, v * 0.5, masterGain);
    // Octave below for warmth
    createOsc('triangle', freq * 0.5, startT, endT, v * 0.3, masterGain);
  }

  /* ── MELODIC NOTE ── */
  function note(t, dur, freq, vol, type) {
    createOsc(type || 'square', freq, t, t + dur, vol || 0.08, masterGain);
  }

  /* ── RISING SWEEP ── */
  function risingSweep(startT, endT, fromFreq, toFreq, vol) {
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = 'sawtooth';
    osc.connect(g);
    g.connect(masterGain);

    const absStart = startTime + startT;
    const absEnd = startTime + endT;

    osc.frequency.setValueAtTime(fromFreq, absStart);
    osc.frequency.exponentialRampToValueAtTime(toFreq, absEnd);
    g.gain.setValueAtTime(0, absStart);
    g.gain.linearRampToValueAtTime(vol || 0.06, absStart + 0.5);
    g.gain.setValueAtTime(vol || 0.06, absEnd - 0.3);
    g.gain.linearRampToValueAtTime(0, absEnd);

    osc.start(absStart);
    osc.stop(absEnd + 0.1);
  }

  /* ── IMPACT BOOM ── */
  function boom(t, vol) {
    kick(t, (vol || 1) * 0.35);
    createNoise(t, t + 0.4, (vol || 1) * 0.15, 400, masterGain);
    createOsc('sine', 40, t, t + 0.6, (vol || 1) * 0.2, masterGain);
  }

  /* ── STINGER (dramatic hit) ── */
  function stinger(t) {
    boom(t, 1.2);
    createOsc('sawtooth', 73.42, t, t + 2.0, 0.08, masterGain);  // D2
    createOsc('sawtooth', 73.72, t, t + 2.0, 0.06, masterGain);
    createOsc('square', 146.83, t, t + 1.5, 0.04, masterGain);   // D3
    createOsc('triangle', 36.71, t, t + 2.5, 0.1, masterGain);   // D1
  }

  /* ──────────────────────────────────────────────────────────
     COMPOSE THE FULL SCORE
     ~125 seconds of original industrial cinematic music
     ────────────────────────────────────────────────────────── */
  function composeScore() {
    if (!ctx) return;

    // ═══ SECTION 1: THE VOID (0-12s) ═══
    // Deep sub bass fade in
    subDrone(0, 12, 36.71, 0.08);     // D1
    subDrone(2, 12, 55.0, 0.04);      // modulating tone

    // Sparse metallic echoes
    metalHit(3.0, 0.3);
    metalHit(5.5, 0.4);
    metalHit(7.0, 0.5);
    metalHit(8.5, 0.3);
    metalHit(10.0, 0.6);
    metalHit(11.0, 0.4);

    // Eerie high tone
    createOsc('sine', 1200, 4, 10, 0.015, masterGain);
    createOsc('sine', 1800, 6, 11, 0.01, masterGain);

    // ═══ SECTION 2: THE AWAKENING (12-22s) ═══
    // Elder theme - deep, wise
    subDrone(12, 22, 36.71, 0.12);    // D1 sustained
    pad(12, 22, 146.83, 0.04);        // D3 pad

    // Melodic motif: D - F - A - G (original theme)
    const motif = [146.83, 174.61, 220.0, 196.0]; // D3, F3, A3, G3
    for (let i = 0; i < 4; i++) {
      note(13 + i * 1.8, 1.2, motif[i], 0.07, 'triangle');
    }

    // Sparse percussion
    for (let t = 12; t < 22; t += 2.5) {
      metalHit(t, 0.4);
    }

    // ═══ SECTION 3: WORLD REVEAL (22-38s) ═══
    // Music builds - bass pulse begins
    subDrone(22, 38, 73.42, 0.15);    // D2

    // Industrial pulse pattern (NOT the T2 rhythm - original pattern)
    // Pattern: hit-hit-rest-hit-rest-hit-hit-rest (8th notes at ~110 BPM)
    const beatDur38 = 60 / 110 * 0.5;
    const pulsePattern = [1,1,0,1,0,1,1,0];
    for (let bar = 0; bar < 6; bar++) {
      for (let i = 0; i < 8; i++) {
        const t = 22 + bar * (beatDur38 * 8) + i * beatDur38;
        if (t >= 38) break;
        if (pulsePattern[i]) {
          kick(t, 0.15);
          if (i === 0 || i === 5) metalHit(t, 0.5);
        }
      }
    }

    // Pad progression: Dm - Bb - Gm - A
    const chords38 = [
      { f: [146.83, 174.61, 220.0], t: 22, d: 4 },   // Dm
      { f: [116.54, 146.83, 174.61], t: 26, d: 4 },   // Bb
      { f: [98.0, 116.54, 146.83], t: 30, d: 4 },     // Gm
      { f: [110.0, 138.59, 164.81], t: 34, d: 4 }      // A
    ];
    for (const ch of chords38) {
      for (const f of ch.f) {
        pad(ch.t, ch.t + ch.d, f, 0.03);
      }
    }

    // Rising sweep for each world transition
    risingSweep(22, 26, 100, 400, 0.04);
    risingSweep(26, 30, 120, 500, 0.04);
    risingSweep(30, 34, 140, 600, 0.05);
    risingSweep(34, 38, 160, 800, 0.06);

    // ═══ SECTION 4: THE THREAT (38-50s) ═══
    // Aggressive - faster tempo, darker
    subDrone(38, 50, 73.42, 0.18);
    subDrone(38, 50, 55.0, 0.08);     // Tension: tritone hint

    // Driving beat at 130 BPM
    const beat50 = 60 / 130;
    for (let t = 38; t < 50; t += beat50) {
      kick(t, 0.22);
      if (Math.floor((t - 38) / beat50) % 2 === 1) {
        metalHit(t, 0.6);
      }
    }
    // Off-beat hi-hat noise
    for (let t = 38 + beat50 * 0.5; t < 50; t += beat50) {
      createNoise(t, t + 0.05, 0.04, 6000, masterGain);
    }

    // Menacing melody (rival theme)
    const rivalMelody = [146.83, 138.59, 130.81, 116.54, 130.81, 110.0, 98.0, 110.0];
    for (let i = 0; i < rivalMelody.length; i++) {
      note(38.5 + i * 1.4, 0.8, rivalMelody[i], 0.06, 'sawtooth');
    }

    // Stingers at dramatic moments
    boom(39.0, 0.8);
    boom(43.0, 0.9);
    boom(47.0, 1.0);

    // ═══ SECTION 5: POWER / GROWTH (50-65s) ═══
    // Heroic shift - major feel
    subDrone(50, 65, 73.42, 0.15);

    // CONSUME impact
    boom(51.0, 1.2);
    note(51.2, 2.0, 146.83, 0.1, 'square'); // D3

    // GROW impact
    boom(54.0, 1.2);
    note(54.2, 2.0, 174.61, 0.1, 'square'); // F3

    // MULTIPLY impact
    boom(57.0, 1.5);
    note(57.2, 2.0, 220.0, 0.1, 'square');  // A3

    // Build into driving section
    const beat65 = 60 / 140;
    for (let t = 59; t < 65; t += beat65) {
      kick(t, 0.2);
      metalHit(t + beat65 * 0.5, 0.5);
    }

    // Heroic chord at 60s
    pad(60, 65, 146.83, 0.05);
    pad(60, 65, 185.0, 0.04);
    pad(60, 65, 220.0, 0.05);

    // Main motif returns
    for (let i = 0; i < 4; i++) {
      note(60 + i * 1.0, 0.7, motif[i] * 2, 0.06, 'triangle');
    }

    // ═══ SECTION 6: JOURNEY MONTAGE (65-82s) ═══
    // Peak energy - full instrumentation
    subDrone(65, 82, 73.42, 0.2);

    // Fast driving beat at 150 BPM
    const beat82 = 60 / 150;
    for (let t = 65; t < 82; t += beat82) {
      kick(t, 0.22);
      const idx = Math.floor((t - 65) / beat82);
      if (idx % 4 === 2) metalHit(t, 0.7);
      if (idx % 2 === 1) createNoise(t, t + 0.04, 0.035, 7000, masterGain);
    }

    // Chapter stingers (one per environment transition)
    const chapterTimes = [66, 69.5, 72.5, 75.5, 78.5];
    for (const ct of chapterTimes) {
      boom(ct, 1.0);
    }

    // Ascending melody through the journey
    const journeyNotes = [
      146.83, 174.61, 196.0, 220.0,   // Chapter 1-2
      233.08, 261.63, 293.66, 329.63,  // Chapter 3-4
      349.23, 392.0, 440.0, 523.25,    // Chapter 5 peak
      587.33, 659.25, 698.46, 783.99   // Climax
    ];
    for (let i = 0; i < journeyNotes.length; i++) {
      const t = 65.5 + i * 1.0;
      if (t < 82) note(t, 0.6, journeyNotes[i], 0.055, 'square');
    }

    // Pad layers
    pad(65, 73, 146.83, 0.04);
    pad(65, 73, 220.0, 0.03);
    pad(73, 82, 196.0, 0.04);
    pad(73, 82, 293.66, 0.03);

    // Rising tension at end
    risingSweep(78, 82, 200, 2000, 0.05);

    // ═══ SECTION 7: THE STAKES (82-95s) ═══
    // Emotional, dramatic
    subDrone(82, 95, 36.71, 0.15);

    // Slow powerful beat
    const beat95 = 60 / 80;
    for (let t = 82; t < 92; t += beat95) {
      kick(t, 0.25);
      if (Math.floor((t - 82) / beat95) % 4 === 0) {
        metalHit(t, 0.8);
      }
    }

    // Emotional pad progression
    pad(82, 87, 146.83, 0.06);  // D
    pad(82, 87, 220.0, 0.05);   // A
    pad(82, 87, 293.66, 0.04);  // D5

    pad(87, 92, 174.61, 0.06);  // F
    pad(87, 92, 261.63, 0.05);  // C
    pad(87, 92, 349.23, 0.04);  // F5

    // Final motif - slow, emotional
    const finalMotif = [293.66, 349.23, 440.0, 392.0]; // D4, F4, A4, G4
    for (let i = 0; i < 4; i++) {
      note(83 + i * 2.2, 1.8, finalMotif[i], 0.08, 'triangle');
    }

    // Build to title
    risingSweep(90, 95, 50, 3000, 0.07);
    // Drums accelerate
    for (let i = 0; i < 12; i++) {
      const t = 91 + i * (0.4 - i * 0.025);
      if (t < 95) {
        kick(t, 0.15 + i * 0.02);
        metalHit(t, 0.3 + i * 0.05);
      }
    }

    // ═══ SECTION 8: TITLE REVEAL (95-108s) ═══
    // MASSIVE stinger on title
    stinger(96);

    // Epic sustained chord
    const titleChord = [73.42, 146.83, 220.0, 293.66, 440.0]; // D power chord
    for (const f of titleChord) {
      pad(96, 106, f, 0.05);
      createOsc('triangle', f, 96, 106, 0.04, masterGain);
    }

    // Slow heartbeat pulse
    for (let t = 98; t < 106; t += 1.5) {
      kick(t, 0.15);
    }

    // Theme one final time - triumphant
    for (let i = 0; i < 4; i++) {
      note(98 + i * 2.0, 1.5, motif[i] * 2, 0.07, 'triangle');
    }

    // Second stinger for subtitle
    boom(101.5, 1.0);

    // Tagline stinger
    boom(106, 0.8);

    // ═══ SECTION 9: CLOSING (108-125s) ═══
    // Fade out
    subDrone(108, 122, 73.42, 0.1);
    pad(108, 118, 146.83, 0.03);
    pad(108, 118, 220.0, 0.025);

    // Sparse final notes
    note(110, 2.0, 293.66, 0.04, 'triangle');
    note(113, 2.0, 220.0, 0.03, 'triangle');
    note(116, 3.0, 146.83, 0.03, 'triangle');

    // Final deep boom
    boom(119, 0.5);
    subDrone(119, 125, 36.71, 0.06);
  }

  /* ── SFX (gameplay sounds for demo moments) ── */
  function sfxEat(t) {
    note(t, 0.05, 523, 0.06, 'square');
    note(t + 0.05, 0.06, 784, 0.06, 'square');
    note(t + 0.1, 0.08, 1047, 0.05, 'square');
  }

  function sfxDivide(t) {
    for (let i = 0; i < 6; i++) note(t + i * 0.06, 0.1, 300 + i * 100, 0.04, 'square');
    note(t + 0.36, 0.25, 1200, 0.03, 'triangle');
  }

  function sfxEatMethane(t) {
    note(t, 0.06, 659, 0.05, 'triangle');
    note(t + 0.06, 0.06, 880, 0.05, 'triangle');
    note(t + 0.12, 0.12, 1175, 0.04, 'triangle');
    note(t + 0.18, 0.15, 1397, 0.03, 'triangle');
  }

  return {
    init, now, composeScore,
    sfxEat, sfxDivide, sfxEatMethane,
    get ctx() { return ctx; },
    get started() { return started; }
  };
})();
