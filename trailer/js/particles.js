/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   PARTICLES: Particle effects (substrates, glow, dust, sparks)
   ============================================================ */

const Particles = (() => {
  const systems = [];

  class ParticleSystem {
    constructor(cfg) {
      this.x = cfg.x || 0;
      this.y = cfg.y || 0;
      this.particles = [];
      this.rate = cfg.rate || 5;          // particles per second
      this.maxLife = cfg.maxLife || 3;
      this.colors = cfg.colors || ['#ffffff'];
      this.sizeRange = cfg.sizeRange || [2, 6];
      this.speedRange = cfg.speedRange || [10, 50];
      this.dirRange = cfg.dirRange || [0, Math.PI * 2];
      this.gravity = cfg.gravity || 0;
      this.fadeOut = cfg.fadeOut !== false;
      this.emitting = true;
      this.glow = cfg.glow || false;
      this.glowColor = cfg.glowColor || '#ffffff';
      this.glowSize = cfg.glowSize || 10;
      this.burst = cfg.burst || false;
      this._accum = 0;

      if (this.burst) {
        for (let i = 0; i < (cfg.burstCount || 30); i++) this._emit();
        this.emitting = false;
      }
    }

    _emit() {
      const angle = this.dirRange[0] + Math.random() * (this.dirRange[1] - this.dirRange[0]);
      const speed = this.speedRange[0] + Math.random() * (this.speedRange[1] - this.speedRange[0]);
      this.particles.push({
        x: this.x + (Math.random() - 0.5) * 10,
        y: this.y + (Math.random() - 0.5) * 10,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: this.maxLife * (0.5 + Math.random() * 0.5),
        maxLife: this.maxLife,
        size: this.sizeRange[0] + Math.random() * (this.sizeRange[1] - this.sizeRange[0]),
        color: this.colors[Math.floor(Math.random() * this.colors.length)]
      });
    }

    update(dt) {
      if (this.emitting) {
        this._accum += dt * this.rate;
        while (this._accum >= 1) {
          this._emit();
          this._accum -= 1;
        }
      }
      for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vy += this.gravity * dt;
        p.life -= dt;
        if (p.life <= 0) this.particles.splice(i, 1);
      }
    }

    draw(ctx) {
      ctx.save();
      for (const p of this.particles) {
        const alpha = this.fadeOut ? Math.max(0, p.life / p.maxLife) : 1;
        ctx.globalAlpha = alpha;
        ctx.fillStyle = p.color;
        if (this.glow) {
          ctx.shadowColor = this.glowColor;
          ctx.shadowBlur = this.glowSize;
        }
        ctx.fillRect(
          Math.floor(p.x - p.size / 2),
          Math.floor(p.y - p.size / 2),
          Math.ceil(p.size),
          Math.ceil(p.size)
        );
      }
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
      ctx.restore();
    }

    get alive() { return this.particles.length > 0 || this.emitting; }
  }

  /* Create flowing substrate particles across screen */
  function createSubstrateFlow(x, y, type, speed) {
    const info = SUBSTRATES[type];
    return new ParticleSystem({
      x, y,
      rate: 0,
      maxLife: 8,
      colors: [info.color, info.glow],
      sizeRange: [3, 7],
      speedRange: [speed || 40, (speed || 40) * 1.5],
      dirRange: [Math.PI * 0.9, Math.PI * 1.1],  // flow left to right (inverted for screen)
      glow: true,
      glowColor: info.glow,
      glowSize: 8,
      burst: true,
      burstCount: 1
    });
  }

  /* Burst effect (for eating, division, impacts) */
  function createBurst(x, y, colors, count, speed, size) {
    return new ParticleSystem({
      x, y,
      colors: colors || ['#ffffff', '#2acfaf', '#5fffdf'],
      sizeRange: size || [2, 8],
      speedRange: [20, speed || 100],
      dirRange: [0, Math.PI * 2],
      maxLife: 1.5,
      glow: true,
      glowColor: colors ? colors[0] : '#2acfaf',
      glowSize: 12,
      burst: true,
      burstCount: count || 30
    });
  }

  /* Ambient floating dust */
  function createDust(width, height) {
    return new ParticleSystem({
      x: width / 2, y: height / 2,
      rate: 3,
      maxLife: 6,
      colors: ['#ffffff', '#aaaacc', '#8888aa'],
      sizeRange: [1, 3],
      speedRange: [2, 10],
      dirRange: [0, Math.PI * 2],
      gravity: -2
    });
  }

  /* Title particle explosion */
  function createTitleExplosion(x, y) {
    return new ParticleSystem({
      x, y,
      colors: ['#2acfaf', '#5fffdf', '#40c8d8', '#ffffff', '#ffff5f'],
      sizeRange: [3, 12],
      speedRange: [50, 300],
      dirRange: [0, Math.PI * 2],
      maxLife: 3.0,
      glow: true,
      glowColor: '#2acfaf',
      glowSize: 20,
      burst: true,
      burstCount: 80
    });
  }

  /* Manage active systems */
  function add(sys) { systems.push(sys); return sys; }

  function updateAll(dt) {
    for (let i = systems.length - 1; i >= 0; i--) {
      systems[i].update(dt);
      if (!systems[i].alive) systems.splice(i, 1);
    }
  }

  function drawAll(ctx) {
    for (const s of systems) s.draw(ctx);
  }

  function clear() { systems.length = 0; }

  return {
    ParticleSystem, createSubstrateFlow, createBurst, createDust,
    createTitleExplosion, add, updateAll, drawAll, clear
  };
})();
