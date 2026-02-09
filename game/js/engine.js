/**
 * PORELIFE: Microbe Survivor
 * Core Engine - Renderer, Input, Camera, Particles
 */

(function() {
    // ─── CANVAS & RENDERING ─────────────────────────────────
    let canvas, offscreen, ctx, offCtx;
    let scale = 1;

    function initRenderer() {
        canvas = document.getElementById('game-canvas');
        offscreen = document.createElement('canvas');
        offscreen.width = PL.NATIVE_W;
        offscreen.height = PL.NATIVE_H;
        ctx = canvas.getContext('2d');
        offCtx = offscreen.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        offCtx.imageSmoothingEnabled = false;
        resize();
        window.addEventListener('resize', resize);
    }

    function resize() {
        const ratio = PL.NATIVE_W / PL.NATIVE_H;
        let w = window.innerWidth;
        let h = window.innerHeight;
        if (w / h > ratio) {
            w = Math.floor(h * ratio);
        } else {
            h = Math.floor(w / ratio);
        }
        canvas.width = w;
        canvas.height = h;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';
        scale = w / PL.NATIVE_W;
        ctx.imageSmoothingEnabled = false;
    }

    function clear(color) {
        offCtx.fillStyle = color || '#000000';
        offCtx.fillRect(0, 0, PL.NATIVE_W, PL.NATIVE_H);
    }

    function present() {
        ctx.drawImage(offscreen, 0, 0, PL.NATIVE_W, PL.NATIVE_H, 0, 0, canvas.width, canvas.height);
    }

    // Draw a pixel-art sprite at position
    function drawSprite(sprite, x, y, alpha) {
        if (!sprite) return;
        const prevAlpha = offCtx.globalAlpha;
        if (alpha !== undefined) offCtx.globalAlpha = alpha;
        for (let row = 0; row < sprite.length; row++) {
            for (let col = 0; col < sprite[row].length; col++) {
                const color = sprite[row][col];
                if (color) {
                    offCtx.fillStyle = color;
                    offCtx.fillRect(Math.floor(x + col), Math.floor(y + row), 1, 1);
                }
            }
        }
        offCtx.globalAlpha = prevAlpha;
    }

    function drawRect(x, y, w, h, color, alpha) {
        const prevAlpha = offCtx.globalAlpha;
        if (alpha !== undefined) offCtx.globalAlpha = alpha;
        offCtx.fillStyle = color;
        offCtx.fillRect(Math.floor(x), Math.floor(y), Math.ceil(w), Math.ceil(h));
        offCtx.globalAlpha = prevAlpha;
    }

    function drawRectOutline(x, y, w, h, color) {
        offCtx.strokeStyle = color;
        offCtx.lineWidth = 1;
        offCtx.strokeRect(Math.floor(x) + 0.5, Math.floor(y) + 0.5, w - 1, h - 1);
    }

    // 8-bit bitmap font renderer
    const FONT_CHARS = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~";

    // Simple 4x6 pixel font (stored as bitmasks)
    const FONT_DATA = {};

    // Generate simple bitmap font data
    function initFont() {
        // We'll use canvas measureText as fallback with pixelated rendering
        // For authentic 8-bit feel, we draw text at small size
    }

    function drawText(text, x, y, color, size, align, shadow) {
        const sz = size || 1;
        const fontSize = 8 * sz;
        offCtx.font = fontSize + 'px monospace';
        offCtx.textBaseline = 'top';

        if (align === 'center') {
            offCtx.textAlign = 'center';
        } else if (align === 'right') {
            offCtx.textAlign = 'right';
        } else {
            offCtx.textAlign = 'left';
        }

        if (shadow) {
            offCtx.fillStyle = typeof shadow === 'string' ? shadow : '#000000';
            offCtx.fillText(text, Math.floor(x) + 1, Math.floor(y) + 1);
        }

        offCtx.fillStyle = color || '#ffffff';
        offCtx.fillText(text, Math.floor(x), Math.floor(y));
    }

    function drawTextWrap(text, x, y, maxWidth, color, size, lineHeight) {
        const sz = size || 1;
        const lh = lineHeight || 10 * sz;
        const lines = text.split('\n');
        let cy = y;
        lines.forEach(line => {
            const words = line.split(' ');
            let currentLine = '';
            words.forEach(word => {
                const testLine = currentLine ? currentLine + ' ' + word : word;
                offCtx.font = (8 * sz) + 'px monospace';
                const metrics = offCtx.measureText(testLine);
                if (metrics.width > maxWidth && currentLine) {
                    drawText(currentLine, x, cy, color, sz, 'left', true);
                    currentLine = word;
                    cy += lh;
                } else {
                    currentLine = testLine;
                }
            });
            if (currentLine) {
                drawText(currentLine, x, cy, color, sz, 'left', true);
                cy += lh;
            }
        });
        return cy - y;
    }

    // ─── CAMERA ─────────────────────────────────────────────
    const camera = {
        x: 0, y: 0,
        targetX: 0, targetY: 0,
        shakeX: 0, shakeY: 0,
        shakeIntensity: 0,
        shakeDuration: 0,

        follow(targetX, targetY, mapW, mapH) {
            this.targetX = targetX - PL.NATIVE_W / 2;
            this.targetY = targetY - (PL.NATIVE_H - 32) / 2; // account for HUD

            // Clamp to map bounds
            const maxX = mapW * PL.TILE - PL.NATIVE_W;
            const maxY = mapH * PL.TILE - (PL.NATIVE_H - 32);
            this.targetX = Math.max(0, Math.min(this.targetX, maxX));
            this.targetY = Math.max(0, Math.min(this.targetY, maxY));
        },

        update(dt) {
            // Smooth follow
            this.x += (this.targetX - this.x) * 6 * dt;
            this.y += (this.targetY - this.y) * 6 * dt;

            // Screen shake
            if (this.shakeDuration > 0) {
                this.shakeDuration -= dt;
                this.shakeX = (Math.random() - 0.5) * this.shakeIntensity * 2;
                this.shakeY = (Math.random() - 0.5) * this.shakeIntensity * 2;
                this.shakeIntensity *= 0.9;
            } else {
                this.shakeX = 0;
                this.shakeY = 0;
            }
        },

        shake(intensity, duration) {
            this.shakeIntensity = intensity;
            this.shakeDuration = duration;
        },

        screenX(worldX) { return worldX - Math.floor(this.x) + this.shakeX; },
        screenY(worldY) { return worldY - Math.floor(this.y) + this.shakeY; }
    };

    // ─── INPUT SYSTEM ───────────────────────────────────────
    const input = {
        keys: {},
        justPressed: {},
        _prev: {},

        init() {
            window.addEventListener('keydown', e => {
                if (!this.keys[e.code]) {
                    this.justPressed[e.code] = true;
                }
                this.keys[e.code] = true;
                // Prevent default for game keys
                if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','Enter'].includes(e.code)) {
                    e.preventDefault();
                }
            });
            window.addEventListener('keyup', e => {
                this.keys[e.code] = false;
            });
        },

        update() {
            // justPressed is consumed after one frame
            this._prev = { ...this.justPressed };
            this.justPressed = {};
        },

        isDown(action) {
            const binds = PL.KEYS[action];
            if (!binds) return false;
            return binds.some(k => this.keys[k]);
        },

        wasPressed(action) {
            const binds = PL.KEYS[action];
            if (!binds) return false;
            return binds.some(k => this._prev[k]);
        }
    };

    // ─── PARTICLE SYSTEM ────────────────────────────────────
    const particles = {
        list: [],

        emit(x, y, count, config) {
            for (let i = 0; i < count; i++) {
                this.list.push({
                    x: x + (Math.random() - 0.5) * (config.spread || 8),
                    y: y + (Math.random() - 0.5) * (config.spread || 8),
                    vx: (Math.random() - 0.5) * (config.speed || 20),
                    vy: (Math.random() - 0.5) * (config.speed || 20) - (config.rise || 0),
                    life: config.life || 0.5,
                    maxLife: config.life || 0.5,
                    size: config.size || 1,
                    color: config.colors ? config.colors[Math.floor(Math.random() * config.colors.length)] : '#ffffff',
                    gravity: config.gravity || 0,
                    friction: config.friction || 0.98,
                    sprite: config.sprite || null,
                    spriteIdx: 0
                });
            }
        },

        update(dt) {
            for (let i = this.list.length - 1; i >= 0; i--) {
                const p = this.list[i];
                p.vx *= p.friction;
                p.vy *= p.friction;
                p.vy += p.gravity * dt;
                p.x += p.vx * dt;
                p.y += p.vy * dt;
                p.life -= dt;
                if (p.sprite) {
                    p.spriteIdx = Math.floor((1 - p.life / p.maxLife) * p.sprite.length);
                    p.spriteIdx = Math.min(p.spriteIdx, p.sprite.length - 1);
                }
                if (p.life <= 0) {
                    this.list.splice(i, 1);
                }
            }
        },

        draw() {
            this.list.forEach(p => {
                const alpha = Math.max(0, p.life / p.maxLife);
                if (p.sprite) {
                    const s = p.sprite[p.spriteIdx];
                    if (s) drawSprite(s, camera.screenX(p.x), camera.screenY(p.y), alpha);
                } else {
                    drawRect(
                        camera.screenX(p.x), camera.screenY(p.y),
                        p.size, p.size,
                        p.color, alpha
                    );
                }
            });
        },

        clear() {
            this.list = [];
        }
    };

    // ─── SCREEN FLASH ───────────────────────────────────────
    let flashColor = null;
    let flashAlpha = 0;
    let flashDuration = 0;

    function screenFlash(color, duration) {
        flashColor = color;
        flashAlpha = 1;
        flashDuration = duration || 0.2;
    }

    function updateFlash(dt) {
        if (flashAlpha > 0) {
            flashAlpha -= dt / flashDuration;
            if (flashAlpha > 0) {
                drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H, flashColor, flashAlpha * 0.5);
            }
        }
    }

    // ─── TRANSITION SYSTEM ──────────────────────────────────
    const transition = {
        active: false,
        type: 'fade',
        progress: 0,
        duration: 0.5,
        direction: 'in', // 'in' = fade to black, 'out' = fade from black
        callback: null,

        start(type, direction, duration, callback) {
            this.active = true;
            this.type = type || 'fade';
            this.direction = direction;
            this.duration = duration || 0.5;
            this.progress = 0;
            this.callback = callback;
        },

        update(dt) {
            if (!this.active) return;
            this.progress += dt / this.duration;
            if (this.progress >= 1) {
                this.progress = 1;
                this.active = false;
                if (this.callback) this.callback();
            }
        },

        draw() {
            if (!this.active && this.progress < 1) return;
            let alpha;
            if (this.direction === 'in') {
                alpha = this.progress;
            } else {
                alpha = 1 - this.progress;
            }
            if (alpha <= 0) return;

            if (this.type === 'fade') {
                drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H, '#000000', alpha);
            } else if (this.type === 'iris') {
                // Iris wipe effect
                const maxR = Math.sqrt(PL.NATIVE_W * PL.NATIVE_W + PL.NATIVE_H * PL.NATIVE_H) / 2;
                const r = this.direction === 'in' ? maxR * (1 - this.progress) : maxR * this.progress;
                offCtx.save();
                offCtx.fillStyle = '#000000';
                offCtx.fillRect(0, 0, PL.NATIVE_W, PL.NATIVE_H);
                offCtx.globalCompositeOperation = 'destination-out';
                offCtx.beginPath();
                offCtx.arc(PL.NATIVE_W / 2, PL.NATIVE_H / 2, r, 0, Math.PI * 2);
                offCtx.fill();
                offCtx.globalCompositeOperation = 'source-over';
                offCtx.restore();
            }
        }
    };

    // ─── TIMING ─────────────────────────────────────────────
    let lastTime = 0;
    let accumulator = 0;
    const fixedDt = 1 / PL.FPS;

    function tick(timestamp) {
        if (!lastTime) lastTime = timestamp;
        let dt = (timestamp - lastTime) / 1000;
        lastTime = timestamp;

        // Clamp large frame gaps
        if (dt > 0.1) dt = 0.1;

        // Update
        if (PL.Game && PL.Game.update) {
            PL.Game.update(dt);
        }

        // Render
        if (PL.Game && PL.Game.draw) {
            PL.Game.draw();
        }

        // Present to screen
        present();

        // Consume input
        input.update();

        requestAnimationFrame(tick);
    }

    function start() {
        requestAnimationFrame(tick);
    }

    // ─── EXPORT ─────────────────────────────────────────────
    PL.Engine = {
        initRenderer,
        clear,
        present,
        drawSprite,
        drawRect,
        drawRectOutline,
        drawText,
        drawTextWrap,
        screenFlash,
        updateFlash,
        camera,
        input,
        particles,
        transition,
        start,
        getCtx() { return offCtx; }
    };
})();
