/**
 * PORELIFE: Microbe Survivor
 * Entities - Player (Paler), Substrate, Colony, Effects
 */

(function() {
    const T = PL.TILE;
    const TILES = PL.TILES;
    const B = PL.BALANCE;

    // ─── PLAYER (PALER) ─────────────────────────────────────
    const player = {
        x: 0, y: 0,           // World pixel position
        tileX: 0, tileY: 0,   // Current tile
        targetX: 0, targetY: 0,
        moving: false,
        direction: 'down',     // facing direction
        health: B.MAX_HEALTH,
        growth: 0,
        alive: true,
        score: 0,
        coloniesPlaced: 0,
        substrateEaten: 0,
        moveTimer: 0,
        moveInterval: 1 / B.MOVE_SPEED,
        animFrame: 0,
        animTimer: 0,
        hurtTimer: 0,
        eatTimer: 0,
        divisionReady: false,
        invincibleTimer: 0,
        deathTimer: 0,
        canDivide: false,
        flashTimer: 0,

        init(tileX, tileY) {
            this.tileX = tileX;
            this.tileY = tileY;
            this.x = tileX * T;
            this.y = tileY * T;
            this.targetX = this.x;
            this.targetY = this.y;
            this.health = B.MAX_HEALTH;
            this.growth = 0;
            this.alive = true;
            this.score = 0;
            this.coloniesPlaced = 0;
            this.substrateEaten = 0;
            this.moving = false;
            this.direction = 'right';
            this.hurtTimer = 0;
            this.eatTimer = 0;
            this.deathTimer = 0;
            this.invincibleTimer = 0;
            this.divisionReady = false;
            this.canDivide = false;
            this.flashTimer = 0;
        },

        update(dt) {
            if (!this.alive) {
                this.deathTimer += dt;
                return;
            }

            const input = PL.Engine.input;

            // Movement
            this.moveTimer -= dt;
            if (this.moveTimer <= 0 && !this.moving) {
                let dx = 0, dy = 0;
                if (input.isDown('UP'))    { dy = -1; this.direction = 'up'; }
                else if (input.isDown('DOWN'))  { dy = 1; this.direction = 'down'; }
                else if (input.isDown('LEFT'))  { dx = -1; this.direction = 'left'; }
                else if (input.isDown('RIGHT')) { dx = 1; this.direction = 'right'; }

                if (dx !== 0 || dy !== 0) {
                    const ntx = this.tileX + dx;
                    const nty = this.tileY + dy;
                    const tile = PL.World.getTile(ntx, nty);

                    if (PL.World.isWalkable(tile)) {
                        this.tileX = ntx;
                        this.tileY = nty;
                        this.targetX = ntx * T;
                        this.targetY = nty * T;
                        this.moving = true;
                        this.moveTimer = this.moveInterval;
                    }
                }
            }

            // Smooth movement interpolation
            if (this.moving) {
                const speed = B.MOVE_SPEED * T * 2.5;
                const ddx = this.targetX - this.x;
                const ddy = this.targetY - this.y;
                const dist = Math.sqrt(ddx * ddx + ddy * ddy);

                if (dist < speed * dt) {
                    this.x = this.targetX;
                    this.y = this.targetY;
                    this.moving = false;
                } else {
                    this.x += (ddx / dist) * speed * dt;
                    this.y += (ddy / dist) * speed * dt;
                }
            }

            // Animation
            this.animTimer += dt;
            if (this.animTimer > 0.2) {
                this.animTimer = 0;
                this.animFrame = (this.animFrame + 1) % 2;
            }

            // Starvation
            this.health -= B.HEALTH_DECAY_RATE * dt;
            if (this.growth > 0) {
                this.growth -= B.GROWTH_DECAY_RATE * dt;
                if (this.growth < 0) this.growth = 0;
            }

            // Toxic damage
            const currentTile = PL.World.getTile(this.tileX, this.tileY);
            if (currentTile === TILES.TOXIC) {
                if (this.invincibleTimer <= 0) {
                    this.health -= B.TOXIC_DAMAGE * dt;
                    this.hurtTimer = 0.15;
                    if (Math.random() < dt * 3) {
                        PL.Engine.camera.shake(2, 0.1);
                    }
                }
            }

            // Division readiness
            this.canDivide = this.growth >= B.DIVISION_GROWTH_COST;
            if (this.canDivide && !this.divisionReady) {
                this.divisionReady = true;
                this.flashTimer = 0;
                PL.Audio.sfx.sciencePopup();
            }
            if (!this.canDivide) this.divisionReady = false;

            // Flash when ready
            if (this.canDivide) {
                this.flashTimer += dt;
            }

            // Timers
            if (this.hurtTimer > 0) this.hurtTimer -= dt;
            if (this.eatTimer > 0) this.eatTimer -= dt;
            if (this.invincibleTimer > 0) this.invincibleTimer -= dt;

            // Health bounds
            this.health = Math.max(0, Math.min(B.MAX_HEALTH, this.health));
            this.growth = Math.max(0, Math.min(B.DIVISION_GROWTH_COST, this.growth));

            // Death
            if (this.health <= 0) {
                this.alive = false;
                this.deathTimer = 0;
                PL.Audio.sfx.die();
                PL.Engine.camera.shake(5, 0.5);
                PL.Engine.screenFlash('#ff0000', 0.3);
                // Death particles
                PL.Engine.particles.emit(this.x + 8, this.y + 8, 15, {
                    speed: 40, life: 1.0, size: 2,
                    colors: ['#5fcf5f', '#2f8f2f', '#888888', '#444444'],
                    gravity: 20, friction: 0.95
                });
            }
        },

        eat(type) {
            if (type === 'doc') {
                this.health = Math.min(B.MAX_HEALTH, this.health + B.DOC_HEALTH);
                this.growth = Math.min(B.DIVISION_GROWTH_COST, this.growth + B.DOC_GROWTH);
                this.score += B.SCORE_SUBSTRATE;
                PL.Audio.sfx.eat();
            } else {
                this.health = Math.min(B.MAX_HEALTH, this.health + B.NUTRIENT_HEALTH);
                this.growth = Math.min(B.DIVISION_GROWTH_COST, this.growth + B.NUTRIENT_GROWTH);
                this.score += B.SCORE_SUBSTRATE;
                PL.Audio.sfx.eatNutrient();
            }
            this.substrateEaten++;
            this.eatTimer = 0.15;

            // Eat particles
            PL.Engine.particles.emit(this.x + 8, this.y + 8, 5, {
                speed: 20, life: 0.4, size: 1,
                colors: type === 'doc' ? ['#ffd700', '#ffec80'] : ['#5fc4eb', '#a0e0ff'],
                rise: 15, friction: 0.9
            });
        },

        divide() {
            if (!this.canDivide) return false;

            // Find adjacent pore for colony
            const pores = PL.World.getAdjacentPores(this.tileX, this.tileY);
            if (pores.length === 0) return false;

            // Pick the best spot (furthest from solid = more room to grow)
            let bestPore = pores[0];
            let bestDist = 0;
            for (const p of pores) {
                const d = PL.World.getDistance(p.x, p.y);
                if (d > bestDist) {
                    bestDist = d;
                    bestPore = p;
                }
            }

            this.growth = 0;
            this.divisionReady = false;
            this.coloniesPlaced++;
            this.score += B.SCORE_COLONY;

            PL.Audio.sfx.divide();
            PL.Engine.camera.shake(3, 0.2);
            PL.Engine.screenFlash('#5fcf5f', 0.2);

            // Division particles
            PL.Engine.particles.emit(this.x + 8, this.y + 8, 10, {
                speed: 30, life: 0.6, size: 2,
                colors: ['#5fcf5f', '#8bef6b', '#ffff5f'],
                friction: 0.92, spread: 12
            });

            return bestPore;
        },

        draw(cam, time) {
            const E = PL.Engine;
            const sx = cam.screenX(this.x);
            const sy = cam.screenY(this.y);

            if (!this.alive) {
                // Death animation
                const frame = Math.min(1, Math.floor(this.deathTimer * 3));
                const alpha = Math.max(0, 1 - this.deathTimer);
                E.drawSprite(PL.Sprites.paler.die[frame], sx, sy, alpha);
                return;
            }

            // Select sprite
            let sprite;
            if (this.hurtTimer > 0) {
                sprite = PL.Sprites.paler.hurt;
            } else if (this.eatTimer > 0) {
                sprite = PL.Sprites.paler.eat;
            } else if (this.canDivide) {
                sprite = PL.Sprites.paler.glow;
            } else {
                const dirSprites = PL.Sprites.paler[this.direction];
                sprite = dirSprites[this.animFrame % dirSprites.length];
            }

            // Bobbing animation
            const bob = Math.sin(time * 4) * 1;

            // Draw shadow
            E.drawRect(sx + 3, sy + 14 + bob, 10, 2, '#000000', 0.3);

            // Draw sprite
            E.drawSprite(sprite, sx, sy + bob);

            // Glow effect when ready to divide
            if (this.canDivide) {
                const glow = Math.sin(this.flashTimer * 6) * 0.3 + 0.3;
                E.drawRect(sx - 1, sy - 1 + bob, 18, 18, '#ffff5f', glow);
            }

            // Health warning flash
            if (this.health < 25) {
                const flash = Math.sin(time * 8) > 0 ? 0.3 : 0;
                E.drawRect(sx, sy + bob, 16, 16, '#ff0000', flash);
            }
        }
    };

    // ─── SUBSTRATE SYSTEM ───────────────────────────────────
    const substrates = {
        list: [],
        spawnTimer: 0,
        spawnInterval: B.SUBSTRATE_SPAWN_RATE,

        init() {
            this.list = [];
            this.spawnTimer = 0;
        },

        update(dt, worldIdx) {
            this.spawnTimer -= dt;
            if (this.spawnTimer <= 0) {
                this.spawn(worldIdx);
                this.spawnTimer = this.spawnInterval;
            }

            const mapSize = PL.World.getMapSize();

            // Update each substrate
            for (let i = this.list.length - 1; i >= 0; i--) {
                const s = this.list[i];

                // Move along flow
                const flow = PL.World.getFlow(Math.floor(s.x / T), Math.floor(s.y / T));
                if (flow.speed > 0) {
                    const flowDirs = [[0,0],[1,0],[0,1],[-1,0],[0,-1]];
                    const fd = flowDirs[flow.dir] || [0, 0];
                    s.x += fd[0] * flow.speed * T * dt;
                    s.y += fd[1] * flow.speed * T * dt;

                    // Add slight random drift (diffusion)
                    s.x += (Math.random() - 0.5) * 5 * dt;
                    s.y += (Math.random() - 0.5) * 5 * dt;
                }

                // Check tile
                const tx = Math.floor(s.x / T);
                const ty = Math.floor(s.y / T);
                const tile = PL.World.getTile(tx, ty);

                // Remove if hit solid or out of bounds
                if (tile === TILES.SOLID || tile === TILES.VOID ||
                    tx < 0 || tx >= mapSize.w || ty < 0 || ty >= mapSize.h) {
                    this.list.splice(i, 1);
                    continue;
                }

                // Check collision with player
                const dx = s.x - player.x;
                const dy = s.y - player.y;
                if (Math.abs(dx) < T && Math.abs(dy) < T && player.alive) {
                    player.eat(s.type);
                    this.list.splice(i, 1);
                    continue;
                }

                // Lifetime
                s.life -= dt;
                if (s.life <= 0) {
                    this.list.splice(i, 1);
                    continue;
                }

                // Animation
                s.animTimer += dt;
            }
        },

        spawn(worldIdx) {
            const mapSize = PL.World.getMapSize();
            const density = B.SUBSTRATE_DENSITY[worldIdx] || 2;

            for (let n = 0; n < density; n++) {
                // Find inlet tiles or leftmost pores
                let spawnX = -1, spawnY = -1;
                const attempts = 20;
                for (let a = 0; a < attempts; a++) {
                    const ty = Math.floor(Math.random() * mapSize.h);
                    for (let tx = 0; tx < Math.min(5, mapSize.w); tx++) {
                        const tile = PL.World.getTile(tx, ty);
                        if (PL.World.isWalkable(tile)) {
                            spawnX = tx;
                            spawnY = ty;
                            break;
                        }
                    }
                    if (spawnX >= 0) break;
                }

                if (spawnX < 0) continue;

                const isDoc = Math.random() < 0.6;
                this.list.push({
                    x: spawnX * T + Math.random() * T,
                    y: spawnY * T + Math.random() * T,
                    type: isDoc ? 'doc' : 'nutrient',
                    life: 15 + Math.random() * 10,
                    animTimer: Math.random() * 10
                });
            }
        },

        draw(cam, time) {
            const E = PL.Engine;
            this.list.forEach(s => {
                const sx = cam.screenX(s.x);
                const sy = cam.screenY(s.y);
                const frame = Math.floor(s.animTimer * 3) % 2;

                // Float animation
                const float = Math.sin(s.animTimer * 2) * 2;

                // Select sprite
                const sprites = s.type === 'doc' ? PL.Sprites.doc : PL.Sprites.nutrient;
                const sprite = sprites[frame % sprites.length];

                // Glow behind
                const glowColor = s.type === 'doc' ? '#ffd700' : '#5fc4eb';
                const glowSize = 10 + Math.sin(s.animTimer * 3) * 2;
                E.drawRect(sx - 1 + (8 - glowSize/2), sy + float - 1 + (8 - glowSize/2),
                          glowSize, glowSize, glowColor, 0.15);

                // Draw sprite
                const alpha = s.life < 3 ? s.life / 3 : 1;
                E.drawSprite(sprite, sx, sy + float, alpha);
            });
        }
    };

    // ─── COLONY SYSTEM ──────────────────────────────────────
    const colonies = {
        list: [],

        init() {
            this.list = [];
        },

        add(tileX, tileY) {
            // Mark tile as biofilm
            PL.World.setTile(tileX, tileY, TILES.BIOFILM);

            this.list.push({
                x: tileX,
                y: tileY,
                age: 0,
                pulseTimer: Math.random() * Math.PI * 2
            });

            // Spawn particles
            PL.Engine.particles.emit(tileX * T + 8, tileY * T + 8, 8, {
                speed: 25, life: 0.5, size: 2,
                colors: ['#5fcf5f', '#3a7a3a', '#2a5a2a'],
                friction: 0.9, spread: 10
            });

            PL.Audio.sfx.colonyPlace();
        },

        update(dt) {
            this.list.forEach(c => {
                c.age += dt;
                c.pulseTimer += dt;

                // Colony passive eating (consume nearby substrate)
                for (let i = substrates.list.length - 1; i >= 0; i--) {
                    const s = substrates.list[i];
                    const stx = Math.floor(s.x / T);
                    const sty = Math.floor(s.y / T);
                    const dist = Math.abs(stx - c.x) + Math.abs(sty - c.y);
                    if (dist <= 1 && Math.random() < dt * 2) {
                        substrates.list.splice(i, 1);
                        // Small sparkle
                        PL.Engine.particles.emit(s.x, s.y, 3, {
                            speed: 10, life: 0.3, size: 1,
                            colors: ['#5fcf5f', '#ffd700'],
                            friction: 0.9
                        });
                    }
                }
            });
        },

        draw(cam, time) {
            const E = PL.Engine;
            this.list.forEach(c => {
                const sx = cam.screenX(c.x * T);
                const sy = cam.screenY(c.y * T);

                // Pulse animation
                const pulse = Math.sin(c.pulseTimer * 2) * 0.15 + 0.85;
                const sprite = pulse > 0.9 ? PL.Sprites.colonyGlow : PL.Sprites.colony;
                E.drawSprite(sprite, sx, sy);

                // Age glow
                if (c.age < 1) {
                    const glow = (1 - c.age);
                    E.drawRect(sx - 2, sy - 2, 20, 20, '#5fcf5f', glow * 0.4);
                }
            });
        },

        getCount() { return this.list.length; }
    };

    // ─── EXPORT ─────────────────────────────────────────────
    PL.Entities = {
        player,
        substrates,
        colonies
    };
})();
