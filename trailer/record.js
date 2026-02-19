#!/usr/bin/env node
/* ============================================================
   ARKE Trailer → MP4 Recorder
   Captures the HTML5 Canvas trailer frame-by-frame and renders
   audio offline, then combines into a 720p YouTube-ready MP4.
   ============================================================ */

const puppeteer = require('puppeteer-core');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

/* ── SETTINGS ── */
const FPS = 30;
const DURATION = 160;
const TOTAL_FRAMES = FPS * DURATION;
const CANVAS_W = 1920;
const CANVAS_H = 1080;
const OUT_W = 1280;
const OUT_H = 720;
const OUTPUT = path.join(__dirname, 'ARKE_Trailer_720p.mp4');
const AUDIO_WAV = path.join(__dirname, '_audio.wav');
const VIDEO_SILENT = path.join(__dirname, '_video_silent.mp4');
const CHROME = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
const PORT = 8765;

/* ── Simple HTTP server ── */
function startServer(dir, port) {
  const MIME = {
    '.html': 'text/html', '.css': 'text/css',
    '.js': 'application/javascript', '.png': 'image/png'
  };
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      const fp = path.join(dir, req.url === '/' ? 'index.html' : req.url);
      fs.readFile(fp, (err, data) => {
        if (err) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(fp)] || 'text/plain' });
        res.end(data);
      });
    });
    srv.listen(port, () => resolve(srv));
  });
}

/* ══════════════════════════════════════════════════════════════
   MAIN
   ══════════════════════════════════════════════════════════════ */
(async () => {
  console.log('=== ARKE Trailer Recorder ===');
  console.log(`Output: ${OUTPUT}`);
  console.log(`Resolution: ${OUT_W}x${OUT_H} @ ${FPS}fps, ${DURATION}s`);
  console.log(`Total frames: ${TOTAL_FRAMES}\n`);

  /* ── 1. Start server ── */
  const server = await startServer(__dirname, PORT);
  console.log(`HTTP server on port ${PORT}`);

  /* ── 2. Launch browser ── */
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    protocolTimeout: 600000,  // 10 min timeout for audio rendering
    args: [
      '--no-sandbox', '--disable-setuid-sandbox',
      '--disable-gpu', '--disable-dev-shm-usage',
      '--disable-software-rasterizer',
      `--window-size=${CANVAS_W},${CANVAS_H}`
    ]
  });
  const page = await browser.newPage();
  await page.setViewport({ width: CANVAS_W, height: CANVAS_H });
  console.log('Browser launched');

  /* ── 3. Load trailer page ── */
  await page.goto(`http://localhost:${PORT}/index.html`, { waitUntil: 'networkidle0' });
  await page.waitForSelector('#screen');
  console.log('Page loaded');

  /* ══════════════════════════════════════════════════════════
     PHASE A: Render audio offline
     - Uses OfflineAudioContext
     - Encodes to WAV inside the browser
     - Returns base64 in chunks to avoid memory issues
     ══════════════════════════════════════════════════════════ */
  console.log('\n--- Phase A: Rendering audio offline ---');

  // Step 1: Render audio and store WAV base64 in window.__wavChunks
  const audioChunkCount = await page.evaluate(async (duration) => {
    const sampleRate = 44100;
    const offCtx = new OfflineAudioContext(2, sampleRate * duration, sampleRate);

    const compressor = offCtx.createDynamicsCompressor();
    compressor.threshold.value = -18; compressor.knee.value = 4;
    compressor.ratio.value = 8; compressor.attack.value = 0.003;
    compressor.release.value = 0.15; compressor.connect(offCtx.destination);
    const masterGain = offCtx.createGain();
    masterGain.gain.value = 0.75; masterGain.connect(compressor);
    const startTime = 0;
    function abs(t) { return startTime + t; }

    function osc(type, freq, t, dur, vol, dest) {
      const o = offCtx.createOscillator(); const g = offCtx.createGain();
      o.type = type; o.frequency.value = freq; g.gain.value = 0;
      o.connect(g); g.connect(dest || masterGain);
      const a = abs(t), e = abs(t + dur);
      const att = Math.min(0.008, dur * 0.05), rel = Math.min(0.08, dur * 0.15);
      g.gain.setValueAtTime(0, a); g.gain.linearRampToValueAtTime(vol, a + att);
      g.gain.setValueAtTime(vol, e - rel); g.gain.linearRampToValueAtTime(0, e);
      o.start(a); o.stop(e + 0.05);
    }
    function oscSweep(type, fs, fe, t, dur, vol, dest) {
      const o = offCtx.createOscillator(); const g = offCtx.createGain();
      o.type = type; o.connect(g); g.connect(dest || masterGain);
      const a = abs(t);
      o.frequency.setValueAtTime(fs, a);
      o.frequency.exponentialRampToValueAtTime(Math.max(1, fe), a + dur * 0.8);
      g.gain.setValueAtTime(vol, a); g.gain.exponentialRampToValueAtTime(0.001, a + dur);
      o.start(a); o.stop(a + dur + 0.05);
    }
    function noiseBurst(t, dur, vol, fFreq, Q, fType, dest) {
      const len = Math.ceil(sampleRate * (dur + 0.05));
      const buf = offCtx.createBuffer(1, len, sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      const src = offCtx.createBufferSource(); src.buffer = buf;
      const filt = offCtx.createBiquadFilter();
      filt.type = fType || 'bandpass'; filt.frequency.value = fFreq || 2000; filt.Q.value = Q || 3;
      const g = offCtx.createGain(); g.gain.value = 0;
      src.connect(filt); filt.connect(g); g.connect(dest || masterGain);
      const a = abs(t);
      g.gain.setValueAtTime(vol, a); g.gain.exponentialRampToValueAtTime(0.001, a + dur);
      src.start(a); src.stop(a + dur + 0.05);
    }
    function noiseSwept(t, dur, vol, f1, f2, Q, dest) {
      const len = Math.ceil(sampleRate * (dur + 0.1));
      const buf = offCtx.createBuffer(1, len, sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      const src = offCtx.createBufferSource(); src.buffer = buf;
      const filt = offCtx.createBiquadFilter();
      filt.type = 'bandpass'; filt.frequency.value = f1; filt.Q.value = Q || 5;
      const g = offCtx.createGain();
      src.connect(filt); filt.connect(g); g.connect(dest || masterGain);
      const a = abs(t), e = abs(t + dur);
      filt.frequency.setValueAtTime(f1, a); filt.frequency.exponentialRampToValueAtTime(f2, e);
      g.gain.setValueAtTime(0, a); g.gain.linearRampToValueAtTime(vol, a + dur * 0.1);
      g.gain.linearRampToValueAtTime(vol * 0.8, e - dur * 0.2);
      g.gain.linearRampToValueAtTime(0, e);
      src.start(a); src.stop(e + 0.1);
    }
    function anvil(t, vol) {
      const v = vol || 0.14;
      noiseBurst(t, 0.18, v*0.8, 3200, 12); noiseBurst(t, 0.03, v*1.2, 6500, 5);
      osc('sine', 987, t, 0.25, v*0.15); osc('sine', 1318, t, 0.15, v*0.08);
      oscSweep('sine', 120, 40, t, 0.12, v*0.6);
    }
    function heavyAnvil(t, vol) {
      const v = vol || 0.18;
      noiseBurst(t, 0.22, v*0.9, 2400, 15); noiseBurst(t, 0.04, v*1.4, 5000, 6);
      noiseBurst(t, 0.12, v*0.4, 800, 4); osc('sine', 740, t, 0.3, v*0.12);
      oscSweep('sine', 180, 30, t, 0.18, v*0.7);
    }
    function kick(t, vol) {
      const v = vol || 0.25;
      oscSweep('sine', 160, 28, t, 0.28, v); osc('sine', 36, t, 0.35, v*0.5);
      noiseBurst(t, 0.015, v*0.6, 4000, 2, 'highpass');
    }
    function tick(t, vol) {
      const v = vol || 0.06; noiseBurst(t, 0.04, v, 5500, 20); osc('sine', 2200, t, 0.02, v*0.3);
    }
    function clang(t, vol) {
      const v = vol || 0.08;
      noiseBurst(t, 0.3, v*0.5, 4200, 25); osc('sine', 1480, t, 0.4, v*0.3);
      osc('sine', 2100, t, 0.25, v*0.15); osc('sine', 680, t, 0.35, v*0.2);
    }
    function subPulse(t, dur, freq, vol) {
      const v = vol || 0.18; const f = freq || 41.2;
      osc('sine', f, t, dur, v); osc('sine', f*1.003, t, dur, v*0.3);
      osc('triangle', f*2, t, dur, v*0.08);
    }
    function darkPad(t, dur, freq, vol) {
      const v = vol || 0.04;
      const filt = offCtx.createBiquadFilter();
      filt.type = 'lowpass'; filt.frequency.value = 800; filt.Q.value = 1; filt.connect(masterGain);
      osc('sawtooth', freq, t, dur, v, filt); osc('sawtooth', freq*1.007, t, dur, v*0.7, filt);
      osc('sawtooth', freq*0.993, t, dur, v*0.7, filt); osc('sawtooth', freq*0.5, t, dur, v*0.4, filt);
    }
    function darkNote(t, dur, freq, vol) {
      const v = vol || 0.06;
      const filt = offCtx.createBiquadFilter();
      filt.type = 'lowpass'; filt.frequency.value = 1200; filt.Q.value = 2; filt.connect(masterGain);
      osc('sawtooth', freq, t, dur, v, filt); osc('square', freq*1.002, t, dur, v*0.3, filt);
      osc('triangle', freq*0.5, t, dur, v*0.2, filt);
    }
    function stinger(t, vol) {
      const v = vol || 1.0;
      heavyAnvil(t, 0.2*v); kick(t, 0.35*v); noiseBurst(t, 0.5, 0.12*v, 300, 2, 'lowpass');
      darkPad(t, 3.0, 82.41, 0.06*v); darkPad(t, 3.0, 123.47, 0.04*v);
      darkPad(t, 2.5, 164.81, 0.04*v); osc('sine', 41.2, t, 3.5, 0.15*v);
    }
    function boom(t, vol) {
      const v = vol || 1.0;
      kick(t, 0.3*v); noiseBurst(t, 0.4, 0.1*v, 300, 2, 'lowpass');
      osc('sine', 30, t, 0.8, 0.18*v); noiseBurst(t, 0.08, 0.08*v, 1200, 3);
    }
    function heartbeat(t, vol) {
      const v = vol || 0.12;
      oscSweep('sine', 80, 30, t, 0.15, v); oscSweep('sine', 65, 25, t+0.18, 0.12, v*0.7);
    }

    const BPM = 95, BEAT = 60/BPM, SIXTEENTH = BEAT/4, BAR = BEAT*4;
    const E1=41.2,E2=82.41,G2=98.0,A2=110.0,B2=123.47;
    const D3=146.83,E3=164.81,G3=196.0,A3=220.0,B3=246.94;
    const D4=293.66,E4=329.63;
    const MP=[1,0,0,0,1,0,0.7,0,0,0.3,1,0,1,0,0,0];
    const BP=[1,0,0.4,0,1,0.3,0.7,0,0.4,0.3,1,0,1,0.3,0.5,0];
    const FP=[1,0.5,0.7,0.4,1,0.5,0.7,0.4,1,0.5,0.7,0.5,1,0.7,1,0.7];
    function pp(p,t,v2) {
      const v=v2||1.0;
      for(let i=0;i<16;i++){const h=p[i];if(h<=0)continue;const ht=t+i*SIXTEENTH;
      if(h>=0.8)anvil(ht,0.14*v*h);else if(h>=0.5)anvil(ht,0.08*v*h);else tick(ht,0.06*v*h);}
    }
    function motif(t,vol,oct){const m=oct||1,v=vol||0.06;
      darkNote(t,BEAT*1.5,E3*m,v);darkNote(t+BEAT*1.5,BEAT,G3*m,v*0.9);
      darkNote(t+BEAT*2.5,BEAT*1.5,D3*m,v*0.85);darkNote(t+BEAT*4.0,BEAT,E3*m,v*0.8);
      darkNote(t+BEAT*5.0,BEAT*2.5,B2*m,v*0.95);}
    function counter(t,vol,oct){const m=oct||1,v=vol||0.05;
      darkNote(t,BEAT,G3*m,v);darkNote(t+BEAT,BEAT,A3*m,v*0.9);
      darkNote(t+BEAT*2,BEAT*1.5,E3*m,v*0.85);darkNote(t+BEAT*3.5,BEAT*2,D3*m,v);}

    // S1: VOID (0-12)
    subPulse(0,12,E1,0.06);osc('sine',E1*1.5,0,12,0.02);osc('sine',1480,2,8,0.008);osc('sine',2100,4,9,0.005);
    anvil(3,0.06);anvil(5.2,0.08);tick(6.5,0.04);anvil(7.8,0.10);tick(8.8,0.03);anvil(9.5,0.07);
    tick(10.2,0.04);anvil(10.8,0.12);tick(11.2,0.05);anvil(11.5,0.10);
    heartbeat(8,0.04);heartbeat(10,0.06);heartbeat(11.5,0.08);
    // S2: ARKE (12-20)
    subPulse(12,8,E1,0.1);for(let t=12;t<16;t+=BEAT*2)heartbeat(t,0.08);
    for(let i=0;i<16;i++)if(MP[i]>=0.8)anvil(15+i*SIXTEENTH,0.07);
    pp(MP,15+BAR,0.65);pp(MP,15+BAR*2,0.75);darkPad(13,7,E2,0.03);darkPad(15,5,B2,0.02);motif(16,0.04,1);
    // S3: ELDER (20-27)
    subPulse(20,7,E1,0.1);for(let t=20;t<27;t+=BEAT*2)heartbeat(t,0.07);
    for(let b=0;b<Math.floor(7/BAR);b++)pp(MP,20+b*BAR,0.7+b*0.05);
    darkPad(20,7,E2,0.035);darkPad(20,7,G2,0.025);darkPad(23,4,B2,0.03);counter(22,0.04,1);boom(21,0.7);
    // S4: ELDER CALLS (27-38)
    for(let t=27;t<38;t+=BEAT){kick(t,0.12);osc('sine',E1,t,BEAT*0.8,0.1);}
    for(let b=0;b<Math.floor(11/BAR);b++){const bt=27+b*BAR;pp(MP,bt,0.8+b*0.04);if(b%2===0)clang(bt,0.05);}
    const br=[E2,E2,G2,A2,G2];for(let i=0;i<br.length;i++)subPulse(27+i*2.2,2.2,br[i]*0.5,0.07);
    darkPad(27,5.5,E2,0.03);darkPad(27,5.5,B2,0.025);darkPad(32.5,5.5,A2,0.03);darkPad(32.5,5.5,E3,0.025);
    motif(29,0.05,1);noiseSwept(35,3,0.03,500,3500,7);
    // S5: EARTH (38-63)
    subPulse(38,25,E1,0.09);for(let t=38;t<63;t+=BEAT){kick(t,0.11);osc('sine',E1,t,BEAT*0.7,0.09);}
    for(let b=0;b<Math.floor(25/BAR);b++){const bt=38+b*BAR;pp(MP,bt,0.8+b*0.02);if(b%3===0)clang(bt,0.05);}
    const wc=[[E2,B2],[D3,A2],[G2,D3],[A2,E3],[E2,B2,G3]];
    for(let w=0;w<5;w++){const wt=38+w*5;for(const f of wc[w])darkPad(wt,5,f,0.025);boom(wt+0.05,0.6+w*0.08);heavyAnvil(wt+0.1,0.08+w*0.01);}
    motif(40,0.05,1);counter(47,0.04,1);motif(54,0.05,1);noiseSwept(59,4,0.03,400,4500,6);
    // S6: RIVAL (63-69)
    subPulse(63,6,E1,0.12);for(let t=63;t<69;t+=BEAT){kick(t,0.15);osc('sine',E1,t,BEAT*0.6,0.13);}
    for(let b=0;b<Math.floor(6/BAR);b++){pp(BP,63+b*BAR,1.0);heavyAnvil(63+b*BAR,0.12);}
    boom(63.5,1.0);clang(64,0.1);darkPad(63,6,E2,0.04);darkPad(63,6,G2,0.035);darkPad(66,3,B2,0.04);
    darkNote(64,1,E3,0.06);darkNote(65.2,1,D3,0.055);darkNote(66.4,1,B2,0.05);darkNote(67.6,1.5,A2,0.06);
    noiseSwept(64,5,0.015,200,1200,4);
    // S7: THREAT (69-81)
    for(let t=69;t<81;t+=BEAT){kick(t,0.16);osc('sine',E1,t,BEAT*0.7,0.14);}
    const nb81=Math.floor(12/BAR);
    for(let b=0;b<nb81;b++){const bt=69+b*BAR;pp(b>=nb81-1?BP:MP,bt,1.0+b*0.04);heavyAnvil(bt,0.1+b*0.01);}
    const tm=[E3,D3,B2,A2,G2,A2,B2,G2];for(let i=0;i<tm.length;i++)darkNote(70+i*1.3,0.9,tm[i],0.05);
    darkPad(69,4,E2,0.04);darkPad(69,4,B2,0.03);darkPad(73,4,A2,0.04);darkPad(73,4,E3,0.03);
    darkPad(77,4,B2,0.04);darkPad(77,4,G2,0.035);boom(70,0.9);clang(74,0.1);boom(78,1.0);
    noiseSwept(71,10,0.015,200,1500,4);
    // S8: POWER (81-96)
    subPulse(81,15,E1,0.1);stinger(82,0.9);darkNote(82.3,2.5,E3,0.08);
    tick(83,0.05);tick(83.5,0.04);tick(84,0.05);boom(86,1.1);heavyAnvil(86,0.15);darkNote(86.3,2.5,G3,0.08);
    tick(87,0.05);tick(87.5,0.04);tick(88,0.05);stinger(90,1.2);darkNote(90.3,2.5,B3,0.09);
    for(let b=0;b<3;b++){pp(BP,91+b*BAR,0.8+b*0.12);kick(91+b*BAR,0.14+b*0.02);}
    for(let t=91;t<96;t+=BEAT){kick(t,0.13);osc('sine',E1,t,BEAT*0.7,0.1);}
    motif(92,0.06,1);darkPad(92,4,E2,0.04);darkPad(92,4,B2,0.035);darkPad(92,4,E3,0.03);
    // S9: JOURNEY (96-113)
    for(let t=96;t<113;t+=BEAT){kick(t,0.18);osc('sine',E1,t,BEAT*0.6,0.15);}
    const nb113=Math.floor(17/BAR);
    for(let b=0;b<nb113;b++){const bt=96+b*BAR;pp(b%4===3?FP:(b%2===0?MP:BP),bt,1.1);heavyAnvil(bt,0.12);if(b%2===1)clang(bt+BEAT*2,0.07);}
    const jb=[E2,E2,G2,A2,B2,A2,G2];for(let i=0;i<jb.length;i++)subPulse(96+i*17/7,17/7,jb[i]*0.5,0.1);
    [97,100.5,103.5,106.5,109.5].forEach((h,i)=>{boom(h,0.8+i*0.08);heavyAnvil(h,0.12+i*0.02);});
    darkNote(97,BEAT*1.2,E3,0.06);darkNote(98,BEAT*1.2,G3,0.06);darkNote(100.5,BEAT*1.2,D3,0.06);
    darkNote(101.5,BEAT*1.2,E3,0.06);darkNote(103.5,BEAT*1.2,G3,0.06);darkNote(104.5,BEAT*1.2,A3,0.06);
    darkNote(106.5,BEAT*1.2,B3,0.07);darkNote(107.5,BEAT*1.2,D4,0.07);darkNote(109.5,BEAT*1.5,E4,0.08);
    darkPad(96,8,E2,0.04);darkPad(96,8,B2,0.03);darkPad(104,9,A2,0.04);darkPad(104,9,E3,0.035);
    noiseSwept(109,4,0.04,300,6000,6);for(let i=0;i<16;i++)tick(111+i*0.12,0.04+i*0.003);
    // S10: STAKES (113-126)
    subPulse(113,13,E1,0.12);for(let t=113;t<123;t+=BEAT*2){kick(t,0.2);heavyAnvil(t,0.1);}
    for(let t=113;t<123;t+=BEAT)tick(t+BEAT*0.5,0.03);
    for(let t=113;t<123;t+=BEAT*2.5)heartbeat(t+BEAT,0.07);
    motif(114,0.07,1);counter(119,0.06,1);
    darkPad(113,3.5,E2,0.05);darkPad(113,3.5,G2,0.04);darkPad(113,3.5,B2,0.035);
    darkPad(116.5,3.5,A2,0.05);darkPad(116.5,3.5,E3,0.04);
    darkPad(120,3,G2,0.05);darkPad(120,3,D3,0.04);darkPad(120,3,B2,0.035);
    pp(BP,122,0.8);for(let i=0;i<16;i++){const ht=123+i*(0.2-i*0.008);if(ht<126.8){anvil(ht,0.08+i*0.008);if(i%3===0)kick(ht,0.1+i*0.01);}}
    noiseSwept(123,4,0.05,200,8000,5);oscSweep('sawtooth',80,2000,124,3,0.03);
    // S11: TITLE (126-139)
    stinger(127,1.3);clang(127,0.15);osc('sine',E1,127,4,0.2);osc('sine',E1*0.5,127,5,0.1);
    darkPad(127,10,E2,0.06);darkPad(127,10,B2,0.05);darkPad(127,10,E3,0.05);darkPad(127,10,G3,0.04);
    osc('triangle',E2,127,10,0.04);osc('triangle',E3,127,10,0.03);
    for(let t=128.5;t<137;t+=BEAT*3)heartbeat(t,0.08);for(let t=129;t<137;t+=BEAT*2)heavyAnvil(t,0.08);
    motif(129,0.07,2);boom(133,1.0);boom(137,0.7);clang(137,0.08);
    // S12: CLOSING (139-160)
    subPulse(139,16,E1,0.05);darkPad(139,10,E2,0.025);darkPad(139,10,B2,0.02);
    darkNote(141,2.5,E3,0.04);darkNote(144,2.5,G3,0.03);darkNote(147,3,B2,0.025);
    tick(141,0.03);anvil(143,0.04);tick(146,0.025);anvil(149,0.03);tick(152,0.02);
    heartbeat(150,0.06);heartbeat(153,0.04);osc('sine',E1,152,8,0.03);osc('sine',E1*0.5,153,7,0.015);

    // Render the audio offline
    console.log('Starting offline render...');
    const rendered = await offCtx.startRendering();
    console.log('Offline render complete');

    // Encode as WAV inside the browser (much smaller than transferring float arrays)
    const numCh = rendered.numberOfChannels;
    const numSamples = rendered.length;
    const ch0 = rendered.getChannelData(0);
    const ch1 = numCh > 1 ? rendered.getChannelData(1) : ch0;
    const bytesPerSample = 2;
    const blockAlign = 2 * bytesPerSample;
    const dataSize = numSamples * blockAlign;
    const wavSize = 44 + dataSize;

    // Build WAV in an ArrayBuffer
    const wavBuf = new ArrayBuffer(wavSize);
    const view = new DataView(wavBuf);
    const writeStr = (off, s) => { for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i)); };
    writeStr(0, 'RIFF'); view.setUint32(4, 36 + dataSize, true); writeStr(8, 'WAVE');
    writeStr(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 2, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(30, blockAlign, true); view.setUint16(32, 16, true);
    writeStr(36, 'data'); view.setUint32(40, dataSize, true);

    let off = 44;
    for (let i = 0; i < numSamples; i++) {
      let s0 = Math.max(-1, Math.min(1, ch0[i]));
      let s1 = Math.max(-1, Math.min(1, ch1[i]));
      view.setInt16(off, Math.round(s0 < 0 ? s0 * 0x8000 : s0 * 0x7FFF), true); off += 2;
      view.setInt16(off, Math.round(s1 < 0 ? s1 * 0x8000 : s1 * 0x7FFF), true); off += 2;
    }

    // Convert to base64 in chunks to avoid max string length issues
    const bytes = new Uint8Array(wavBuf);
    const CHUNK = 1024 * 1024; // 1MB chunks
    const chunks = [];
    for (let i = 0; i < bytes.length; i += CHUNK) {
      const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.length));
      let binary = '';
      for (let j = 0; j < slice.length; j++) binary += String.fromCharCode(slice[j]);
      chunks.push(btoa(binary));
    }
    window.__wavChunks = chunks;
    window.__wavChunkCount = chunks.length;
    return chunks.length;
  }, DURATION);

  console.log(`Audio rendered, ${audioChunkCount} chunks to transfer`);

  // Transfer WAV data in chunks
  const wavChunks = [];
  for (let i = 0; i < audioChunkCount; i++) {
    const chunk = await page.evaluate((idx) => window.__wavChunks[idx], i);
    wavChunks.push(chunk);
    console.log(`  Transferred chunk ${i + 1}/${audioChunkCount}`);
  }

  // Decode base64 and save
  const wavBuffers = wavChunks.map(c => Buffer.from(c, 'base64'));
  const wavFull = Buffer.concat(wavBuffers);
  fs.writeFileSync(AUDIO_WAV, wavFull);
  console.log(`Audio saved: ${AUDIO_WAV} (${(wavFull.length / 1024 / 1024).toFixed(1)}MB)`);

  /* ══════════════════════════════════════════════════════════
     PHASE B: Capture video frames
     ══════════════════════════════════════════════════════════ */
  console.log('\n--- Phase B: Capturing video frames ---');

  // Inject frame-by-frame control
  await page.evaluate((fps, duration) => {
    let fakeTime = 0;
    performance.now = () => fakeTime;

    const canvas = document.getElementById('screen');
    const ctx = canvas.getContext('2d');
    document.getElementById('overlay').classList.add('hidden');
    document.getElementById('container').classList.add('letterbox-wide');
    Camera.set(CFG.W / 2, CFG.H / 2, 1);
    Particles.clear();
    Scenes.reset();

    window.__renderFrame = function(frameNum) {
      const trailerTime = frameNum / fps;
      const dt = 1.0 / fps;
      fakeTime = frameNum * (1000 / fps);
      if (trailerTime >= duration) return false;

      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, CFG.W, CFG.H);
      Camera.update(dt);
      Scenes.render(ctx, trailerTime, dt);
      Particles.updateAll(dt);
      Particles.drawAll(ctx);
      TextRenderer.update(ctx, trailerTime);
      TextRenderer.drawScanlines(ctx, 0.03);

      if (trailerTime < 1.5) {
        ctx.save(); ctx.globalAlpha = Math.max(0, 1 - trailerTime / 1.5);
        ctx.fillStyle = '#000000'; ctx.fillRect(0, 0, CFG.W, CFG.H); ctx.restore();
      }

      const transitions = [
        { t: TIMELINE.PIXEL_AWAKEN.end - 0.3, dur: 0.6 },
        { t: TIMELINE.ARKE_CLOSEUP.end - 0.3, dur: 0.6 },
        { t: TIMELINE.ELDER_CLOSEUP.end - 0.3, dur: 0.6 },
        { t: TIMELINE.ELDER_CALLS.end - 0.3, dur: 0.6 },
        { t: TIMELINE.EARTH_CROSS.end - 0.3, dur: 0.6 },
        { t: TIMELINE.RIVAL_CLOSEUP.end - 0.2, dur: 0.4 },
        { t: TIMELINE.RIVALS_THREAT.end - 0.2, dur: 0.4 },
        { t: TIMELINE.POWER_GROW.end - 0.3, dur: 0.6 },
        { t: TIMELINE.JOURNEY_MONTAGE.end - 0.2, dur: 0.4 },
        { t: TIMELINE.EARTH_STAKES.end - 0.3, dur: 0.6 }
      ];
      for (const tr of transitions) {
        const elapsed = trailerTime - tr.t;
        if (elapsed < 0 || elapsed > tr.dur) continue;
        const half = tr.dur / 2;
        const alpha = elapsed < half ? elapsed / half : 1 - (elapsed - half) / half;
        ctx.save(); ctx.globalAlpha = Math.min(1, alpha * 0.9);
        ctx.fillStyle = '#000000'; ctx.fillRect(0, 0, CFG.W, CFG.H); ctx.restore();
      }

      const barH = 3, progress = trailerTime / duration;
      ctx.save(); ctx.globalAlpha = 0.3;
      ctx.fillStyle = '#1a1a2a'; ctx.fillRect(0, CFG.H - barH, CFG.W, barH);
      ctx.fillStyle = '#2acfaf'; ctx.fillRect(0, CFG.H - barH, CFG.W * progress, barH);
      ctx.restore();

      // Burn letterbox bars into the canvas
      ctx.fillStyle = '#000000';
      const bs = Math.round(CFG.H * 0.12);
      ctx.fillRect(0, 0, CFG.W, bs);
      ctx.fillRect(0, CFG.H - bs, CFG.W, bs);

      return true;
    };
  }, FPS, DURATION);

  console.log('Frame renderer injected');

  // Start ffmpeg to receive raw PNG frames
  const ffmpegVideo = spawn('ffmpeg', [
    '-y', '-f', 'image2pipe', '-framerate', String(FPS),
    '-i', 'pipe:0',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
    '-pix_fmt', 'yuv420p',
    '-vf', `scale=${OUT_W}:${OUT_H}`,
    '-movflags', '+faststart',
    VIDEO_SILENT
  ], { stdio: ['pipe', 'pipe', 'pipe'] });

  let ffmpegErr = '';
  ffmpegVideo.stderr.on('data', d => { ffmpegErr += d.toString(); });

  const startCapture = Date.now();
  let lastPct = -1;

  for (let frame = 0; frame < TOTAL_FRAMES; frame++) {
    const hasMore = await page.evaluate((f) => window.__renderFrame(f), frame);

    const canvasEl = await page.$('#screen');
    const pngBuffer = await canvasEl.screenshot({ type: 'png' });
    ffmpegVideo.stdin.write(pngBuffer);

    const pct = Math.floor((frame / TOTAL_FRAMES) * 100);
    if (pct !== lastPct && pct % 5 === 0) {
      const elapsed = ((Date.now() - startCapture) / 1000).toFixed(0);
      const eta = frame > 0 ? (((Date.now() - startCapture) / frame) * (TOTAL_FRAMES - frame) / 1000).toFixed(0) : '?';
      console.log(`  Frame ${frame}/${TOTAL_FRAMES} (${pct}%) — ${elapsed}s elapsed, ~${eta}s remaining`);
      lastPct = pct;
    }

    if (!hasMore) break;
  }

  ffmpegVideo.stdin.end();
  await new Promise((resolve, reject) => {
    ffmpegVideo.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited ${code}: ${ffmpegErr.slice(-500)}`));
    });
  });

  console.log(`Video captured in ${((Date.now() - startCapture) / 1000).toFixed(0)}s`);

  /* ── PHASE C: Combine video + audio ── */
  console.log('\n--- Phase C: Combining video + audio ---');
  // Re-encode WAV via raw PCM to fix header compatibility with ffmpeg
  const AUDIO_FIXED = AUDIO_WAV.replace('.wav', '_fixed.wav');
  execSync(`ffmpeg -y -f s16le -ar 44100 -ac 2 -i <(tail -c +45 "${AUDIO_WAV}") -c:a pcm_s16le "${AUDIO_FIXED}"`, { shell: '/bin/bash' });
  execSync(`ffmpeg -y -i "${VIDEO_SILENT}" -i "${AUDIO_FIXED}" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "${OUTPUT}"`);

  try { fs.unlinkSync(VIDEO_SILENT); } catch(e) {}
  try { fs.unlinkSync(AUDIO_WAV); } catch(e) {}
  try { fs.unlinkSync(AUDIO_FIXED); } catch(e) {}

  const stat = fs.statSync(OUTPUT);
  console.log(`\n=== DONE ===`);
  console.log(`Output: ${OUTPUT}`);
  console.log(`Size: ${(stat.size / 1024 / 1024).toFixed(1)} MB`);

  await browser.close();
  server.close();
  process.exit(0);
})().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});
