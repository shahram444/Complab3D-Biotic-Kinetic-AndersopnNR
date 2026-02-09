/**
 * PORELIFE: Microbe Survivor
 * Retro Audio System (Web Audio API)
 */

(function() {
    let ctx = null;
    let muted = false;
    let masterGain = null;
    let musicGain = null;
    let sfxGain = null;
    let currentMusic = null;

    function init() {
        try {
            ctx = new (window.AudioContext || window.webkitAudioContext)();
            masterGain = ctx.createGain();
            masterGain.gain.value = 0.4;
            masterGain.connect(ctx.destination);

            musicGain = ctx.createGain();
            musicGain.gain.value = 0.25;
            musicGain.connect(masterGain);

            sfxGain = ctx.createGain();
            sfxGain.gain.value = 0.5;
            sfxGain.connect(masterGain);
        } catch(e) {
            console.warn('Web Audio not available');
        }
    }

    function resume() {
        if (ctx && ctx.state === 'suspended') ctx.resume();
    }

    function toggleMute() {
        muted = !muted;
        if (masterGain) masterGain.gain.value = muted ? 0 : 0.4;
        return muted;
    }

    // ─── SOUND EFFECT GENERATORS ────────────────────────────

    function playNote(freq, duration, type, gainNode, volume) {
        if (!ctx) return;
        resume();
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = type || 'square';
        osc.frequency.value = freq;
        g.gain.value = volume || 0.3;
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        osc.connect(g);
        g.connect(gainNode || sfxGain);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + duration);
    }

    function playNoise(duration, gainNode, volume) {
        if (!ctx) return;
        resume();
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        const g = ctx.createGain();
        g.gain.value = volume || 0.1;
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        source.connect(g);
        g.connect(gainNode || sfxGain);
        source.start();
    }

    // ─── SOUND EFFECTS ──────────────────────────────────────

    const sfx = {
        eat() {
            playNote(523, 0.05, 'square');
            setTimeout(() => playNote(784, 0.08, 'square'), 50);
            setTimeout(() => playNote(1047, 0.1, 'square'), 100);
        },

        eatNutrient() {
            playNote(659, 0.06, 'triangle');
            setTimeout(() => playNote(880, 0.06, 'triangle'), 60);
            setTimeout(() => playNote(1175, 0.12, 'triangle'), 120);
        },

        move() {
            playNote(220, 0.03, 'square', sfxGain, 0.05);
        },

        divide() {
            for (let i = 0; i < 6; i++) {
                setTimeout(() => playNote(300 + i * 100, 0.12, 'square'), i * 60);
            }
            setTimeout(() => playNote(1200, 0.3, 'triangle'), 360);
        },

        hurt() {
            playNote(200, 0.1, 'sawtooth');
            setTimeout(() => playNote(150, 0.15, 'sawtooth'), 80);
            playNoise(0.15, sfxGain, 0.08);
        },

        die() {
            for (let i = 0; i < 5; i++) {
                setTimeout(() => {
                    playNote(400 - i * 60, 0.2, 'sawtooth');
                    playNoise(0.1, sfxGain, 0.05);
                }, i * 120);
            }
        },

        levelComplete() {
            const melody = [523, 659, 784, 1047, 784, 1047, 1319];
            melody.forEach((f, i) => {
                setTimeout(() => playNote(f, 0.15, 'square'), i * 120);
            });
        },

        menuSelect() {
            playNote(440, 0.05, 'square');
            setTimeout(() => playNote(660, 0.08, 'square'), 50);
        },

        menuConfirm() {
            playNote(523, 0.08, 'triangle');
            setTimeout(() => playNote(784, 0.12, 'triangle'), 80);
        },

        sciencePopup() {
            playNote(330, 0.1, 'sine');
            setTimeout(() => playNote(440, 0.1, 'sine'), 100);
            setTimeout(() => playNote(554, 0.15, 'sine'), 200);
        },

        warning() {
            playNote(200, 0.15, 'square');
            setTimeout(() => playNote(180, 0.15, 'square'), 200);
        },

        colonyPlace() {
            playNote(392, 0.08, 'triangle');
            setTimeout(() => playNote(523, 0.08, 'triangle'), 80);
            setTimeout(() => playNote(659, 0.15, 'triangle'), 160);
        }
    };

    // ─── MUSIC SYSTEM ───────────────────────────────────────

    let musicTimer = null;
    let musicPlaying = false;

    function stopMusic() {
        musicPlaying = false;
        if (musicTimer) {
            clearInterval(musicTimer);
            musicTimer = null;
        }
    }

    // Simple procedural chiptune music
    function playMusic(worldIdx) {
        stopMusic();
        if (!ctx) return;
        resume();
        musicPlaying = true;

        const patterns = [
            // World 1: Upbeat, curious
            { bpm: 140, notes: [
                [262,0.2],[330,0.2],[392,0.2],[330,0.2],
                [262,0.2],[392,0.2],[523,0.2],[392,0.2],
                [349,0.2],[440,0.2],[523,0.2],[440,0.2],
                [349,0.2],[262,0.2],[330,0.4],[0,0.2]
            ], bass: [131,131,175,175,131,131,165,165] },
            // World 2: Slow, tense
            { bpm: 90, notes: [
                [220,0.3],[0,0.1],[262,0.3],[247,0.3],
                [220,0.3],[0,0.1],[196,0.3],[220,0.5],
                [262,0.3],[0,0.1],[294,0.3],[262,0.3],
                [247,0.3],[220,0.3],[196,0.5],[0,0.2]
            ], bass: [110,110,131,131,110,110,98,98] },
            // World 3: Ominous, pulsing
            { bpm: 120, notes: [
                [196,0.2],[0,0.1],[233,0.2],[196,0.2],
                [175,0.2],[0,0.1],[196,0.3],[0,0.1],
                [233,0.2],[262,0.2],[233,0.2],[196,0.2],
                [175,0.2],[165,0.2],[175,0.4],[0,0.2]
            ], bass: [98,98,88,88,98,98,82,82] },
            // World 4: Fast, energetic
            { bpm: 170, notes: [
                [392,0.15],[523,0.15],[659,0.15],[523,0.15],
                [392,0.15],[330,0.15],[392,0.3],[0,0.1],
                [440,0.15],[523,0.15],[659,0.15],[784,0.15],
                [659,0.15],[523,0.15],[440,0.3],[0,0.1]
            ], bass: [196,196,220,220,196,196,175,175] }
        ];

        const pattern = patterns[worldIdx % patterns.length];
        const beatTime = 60 / pattern.bpm;
        let noteIdx = 0;
        let bassIdx = 0;
        let beatCount = 0;

        musicTimer = setInterval(() => {
            if (!musicPlaying) return;
            const note = pattern.notes[noteIdx % pattern.notes.length];
            if (note[0] > 0) {
                playNote(note[0], note[1] * beatTime, 'square', musicGain, 0.15);
            }
            // Bass on every other beat
            if (beatCount % 2 === 0) {
                const bassNote = pattern.bass[bassIdx % pattern.bass.length];
                playNote(bassNote, beatTime * 1.5, 'triangle', musicGain, 0.12);
                bassIdx++;
            }
            noteIdx++;
            beatCount++;
        }, beatTime * 1000 * 0.5);
    }

    function playTitleMusic() {
        stopMusic();
        if (!ctx) return;
        resume();
        musicPlaying = true;

        const melody = [262, 330, 392, 523, 392, 330, 262, 196, 262, 330, 392, 440, 523, 659, 523, 440];
        let idx = 0;

        musicTimer = setInterval(() => {
            if (!musicPlaying) return;
            playNote(melody[idx % melody.length], 0.3, 'triangle', musicGain, 0.1);
            if (idx % 2 === 0) {
                playNote(melody[idx % melody.length] / 2, 0.5, 'triangle', musicGain, 0.08);
            }
            idx++;
        }, 400);
    }

    PL.Audio = {
        init,
        resume,
        toggleMute,
        isMuted() { return muted; },
        sfx,
        playMusic,
        playTitleMusic,
        stopMusic
    };
})();
