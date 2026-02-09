/**
 * PORELIFE: Microbe Survivor
 * Main Game Logic, State Machine, UI, Science Mode
 */

(function() {
    const S = PL.STATE;
    const T = PL.TILE;
    const E = () => PL.Engine;

    let state = S.BOOT;
    let gameTime = 0;
    let levelTime = 0;
    let currentLevel = 0;
    let levelData = null;
    let scienceMode = false;
    let storyScroll = 0;
    let storyComplete = false;
    let introTimer = 0;
    let levelIntroTimer = 0;
    let levelCompleteTimer = 0;
    let deathTimer = 0;
    let victoryTimer = 0;
    let sciencePopupIdx = -1;
    let totalScore = 0;
    let bootTimer = 0;
    let pauseSelection = 0;
    let shownScienceFacts = new Set();

    // ─── STATE TRANSITIONS ──────────────────────────────────

    function setState(newState) {
        state = newState;
    }

    function startGame() {
        currentLevel = 0;
        totalScore = 0;
        shownScienceFacts.clear();
        loadLevel(0);
    }

    function loadLevel(idx) {
        currentLevel = idx;
        if (idx >= PL.LEVELS.length) {
            // Victory!
            setState(S.VICTORY);
            victoryTimer = 0;
            PL.Audio.stopMusic();
            PL.Audio.sfx.levelComplete();
            return;
        }

        const def = PL.LEVELS[idx];
        levelData = PL.World.generate(def);

        const start = PL.World.findStartPosition();
        PL.Entities.player.init(start.x, start.y);
        PL.Entities.substrates.init();
        PL.Entities.colonies.init();
        PL.Engine.particles.clear();

        levelTime = 0;
        scienceMode = false;

        // Show world intro for first level of each world
        const prevWorld = idx > 0 ? PL.LEVELS[idx - 1].world : -1;
        if (def.world !== prevWorld) {
            setState(S.LEVEL_INTRO);
            levelIntroTimer = 0;
            PL.Audio.playMusic(def.world);
        } else {
            setState(S.LEVEL_INTRO);
            levelIntroTimer = 0;
        }

        // Center camera on player
        const cam = E().camera;
        cam.x = start.x * T - PL.NATIVE_W / 2;
        cam.y = start.y * T - PL.NATIVE_H / 2;
        cam.targetX = cam.x;
        cam.targetY = cam.y;
    }

    function completeLevel() {
        const def = PL.LEVELS[currentLevel];
        const p = PL.Entities.player;

        // Time bonus
        const timeBonus = Math.max(0, Math.floor(PL.BALANCE.SCORE_TIME_BONUS * (1 - levelTime / 120)));
        p.score += PL.BALANCE.SCORE_LEVEL + timeBonus;
        totalScore += p.score;

        setState(S.LEVEL_COMPLETE);
        levelCompleteTimer = 0;
        PL.Audio.sfx.levelComplete();
        E().screenFlash('#5fcf5f', 0.3);

        // Show science fact
        sciencePopupIdx = def.scienceIdx;
    }

    // ─── UPDATE ─────────────────────────────────────────────

    function update(dt) {
        gameTime += dt;
        const input = E().input;

        switch (state) {
            case S.BOOT:
                bootTimer += dt;
                if (bootTimer > 1.5 || input.wasPressed('CONFIRM')) {
                    setState(S.TITLE);
                    PL.Audio.init();
                    PL.Audio.playTitleMusic();
                }
                break;

            case S.TITLE:
                if (input.wasPressed('CONFIRM')) {
                    PL.Audio.resume();
                    PL.Audio.sfx.menuConfirm();
                    PL.Audio.stopMusic();
                    setState(S.STORY);
                    storyScroll = 0;
                    storyComplete = false;
                }
                break;

            case S.STORY:
                storyScroll += dt * 25;
                if (input.wasPressed('CONFIRM')) {
                    if (storyComplete) {
                        startGame();
                    } else {
                        storyScroll = PL.INTRO_STORY.length * 12;
                        storyComplete = true;
                    }
                }
                if (storyScroll > PL.INTRO_STORY.length * 12 + 60) {
                    storyComplete = true;
                }
                break;

            case S.LEVEL_INTRO:
                levelIntroTimer += dt;
                if (input.wasPressed('CONFIRM') && levelIntroTimer > 0.5) {
                    PL.Audio.sfx.menuConfirm();
                    setState(S.PLAYING);
                }
                break;

            case S.PLAYING:
                updatePlaying(dt);
                break;

            case S.PAUSED:
                if (input.wasPressed('PAUSE')) {
                    setState(S.PLAYING);
                    PL.Audio.sfx.menuSelect();
                }
                if (input.wasPressed('UP')) {
                    pauseSelection = Math.max(0, pauseSelection - 1);
                    PL.Audio.sfx.menuSelect();
                }
                if (input.wasPressed('DOWN')) {
                    pauseSelection = Math.min(2, pauseSelection + 1);
                    PL.Audio.sfx.menuSelect();
                }
                if (input.wasPressed('CONFIRM')) {
                    if (pauseSelection === 0) { setState(S.PLAYING); }
                    else if (pauseSelection === 1) { PL.Audio.toggleMute(); }
                    else if (pauseSelection === 2) { setState(S.TITLE); PL.Audio.playTitleMusic(); }
                    PL.Audio.sfx.menuConfirm();
                }
                break;

            case S.SCIENCE_POPUP:
                if (input.wasPressed('CONFIRM')) {
                    PL.Audio.sfx.menuConfirm();
                    // After science fact, go to next level
                    loadLevel(currentLevel + 1);
                }
                break;

            case S.LEVEL_COMPLETE:
                levelCompleteTimer += dt;
                if (levelCompleteTimer > 1.5 && input.wasPressed('CONFIRM')) {
                    // Show science fact
                    if (sciencePopupIdx >= 0 && !shownScienceFacts.has(sciencePopupIdx)) {
                        shownScienceFacts.add(sciencePopupIdx);
                        setState(S.SCIENCE_POPUP);
                        PL.Audio.sfx.sciencePopup();
                    } else {
                        loadLevel(currentLevel + 1);
                    }
                }
                break;

            case S.GAME_OVER:
                deathTimer += dt;
                if (deathTimer > 2 && input.wasPressed('CONFIRM')) {
                    // Restart current level
                    loadLevel(currentLevel);
                }
                break;

            case S.VICTORY:
                victoryTimer += dt;
                if (victoryTimer > 3 && input.wasPressed('CONFIRM')) {
                    setState(S.TITLE);
                    PL.Audio.playTitleMusic();
                }
                break;
        }

        // Global controls
        if (input.wasPressed('MUTE')) {
            PL.Audio.toggleMute();
        }
    }

    function updatePlaying(dt) {
        const input = E().input;
        levelTime += dt;

        // Pause
        if (input.wasPressed('PAUSE')) {
            setState(S.PAUSED);
            pauseSelection = 0;
            PL.Audio.sfx.menuSelect();
            return;
        }

        // Science mode toggle
        if (input.wasPressed('SCIENCE')) {
            scienceMode = !scienceMode;
            if (scienceMode) PL.Audio.sfx.sciencePopup();
        }

        // Update entities
        const p = PL.Entities.player;
        p.update(dt);
        PL.Entities.substrates.update(dt, PL.World.getWorldIdx());
        PL.Entities.colonies.update(dt);
        E().particles.update(dt);

        // Division
        if (input.wasPressed('ACTION') && p.alive && p.canDivide) {
            const colonyPos = p.divide();
            if (colonyPos) {
                PL.Entities.colonies.add(colonyPos.x, colonyPos.y);

                // Check level completion
                const def = PL.LEVELS[currentLevel];
                if (PL.Entities.colonies.getCount() >= def.colonyGoal) {
                    completeLevel();
                    return;
                }
            }
        }

        // Camera follow
        const mapSize = PL.World.getMapSize();
        E().camera.follow(p.x + 8, p.y + 8, mapSize.w, mapSize.h);
        E().camera.update(dt);

        // Player death
        if (!p.alive && p.deathTimer > 2.5) {
            setState(S.GAME_OVER);
            deathTimer = 0;
        }

        // Check if player reached outlet (bonus)
        const exit = PL.World.findExitPosition();
        if (p.tileX === exit.x && p.tileY === exit.y) {
            // Award bonus for reaching exit
            p.score += 100;
        }
    }

    // ─── DRAW ───────────────────────────────────────────────

    function draw() {
        const e = E();

        switch (state) {
            case S.BOOT: drawBoot(); break;
            case S.TITLE: drawTitle(); break;
            case S.STORY: drawStory(); break;
            case S.LEVEL_INTRO: drawLevelIntro(); break;
            case S.PLAYING: drawPlaying(); break;
            case S.PAUSED: drawPlaying(); drawPause(); break;
            case S.SCIENCE_POPUP: drawPlaying(); drawSciencePopup(); break;
            case S.LEVEL_COMPLETE: drawPlaying(); drawLevelComplete(); break;
            case S.GAME_OVER: drawPlaying(); drawGameOver(); break;
            case S.VICTORY: drawVictory(); break;
        }

        // Transition overlay
        e.transition.update(1/60);
        e.transition.draw();
    }

    // ─── SCENE DRAWS ────────────────────────────────────────

    function drawBoot() {
        const e = E();
        e.clear('#000000');

        const alpha = Math.min(1, bootTimer);
        e.drawText('CompLaB3D', PL.NATIVE_W / 2, 80, '#5fc4eb', 1.5, 'center', '#000');
        e.drawText('Presents', PL.NATIVE_W / 2, 105, '#888888', 1, 'center');

        if (bootTimer > 0.8) {
            const a2 = Math.min(1, (bootTimer - 0.8) * 2);
            e.drawText('A Game Based on Real Science', PL.NATIVE_W / 2, 140, '#5fcf5f', 0.8, 'center');
        }
    }

    function drawTitle() {
        const e = E();
        e.clear('#060e1e');

        // Animated background (pore-like)
        for (let i = 0; i < 40; i++) {
            const bx = (Math.sin(gameTime * 0.3 + i * 7) * 0.5 + 0.5) * PL.NATIVE_W;
            const by = (Math.cos(gameTime * 0.2 + i * 11) * 0.5 + 0.5) * PL.NATIVE_H;
            const bs = 3 + Math.sin(gameTime + i) * 2;
            e.drawRect(bx, by, bs, bs, '#0a1e3c', 0.3);
        }

        // Floating substrate particles
        for (let i = 0; i < 15; i++) {
            const px = (gameTime * 20 + i * 30) % (PL.NATIVE_W + 20) - 10;
            const py = 50 + Math.sin(gameTime + i * 2) * 80;
            const sprite = i % 2 === 0 ? PL.Sprites.doc[0] : PL.Sprites.nutrient[0];
            e.drawSprite(sprite, px, py, 0.4);
        }

        // Title
        const titleY = 40 + Math.sin(gameTime * 1.5) * 3;

        // Title shadow
        e.drawText('PORELIFE', PL.NATIVE_W / 2, titleY + 2, '#0a2f0a', 3, 'center');
        // Title main
        e.drawText('PORELIFE', PL.NATIVE_W / 2, titleY, '#5fcf5f', 3, 'center');
        // Title glow
        const glowAlpha = Math.sin(gameTime * 2) * 0.3 + 0.3;
        e.drawText('PORELIFE', PL.NATIVE_W / 2, titleY - 1, '#afffaf', 3, 'center');

        // Subtitle
        e.drawText('Microbe Survivor', PL.NATIVE_W / 2, titleY + 32, '#c4a35a', 1.2, 'center', '#000');

        // Paler sprite in center
        const palerX = PL.NATIVE_W / 2 - 8;
        const palerY = 110 + Math.sin(gameTime * 2) * 4;
        e.drawSprite(PL.Sprites.paler.down[0], palerX, palerY);

        // Blinking prompt
        if (Math.sin(gameTime * 3) > 0) {
            e.drawText('PRESS ENTER TO START', PL.NATIVE_W / 2, 155, '#ffd700', 1, 'center', '#000');
        }

        // Info
        e.drawText('Based on CompLaB3D Research', PL.NATIVE_W / 2, 190, '#888888', 0.8, 'center');
        e.drawText('Pore-Scale Reactive Transport', PL.NATIVE_W / 2, 202, '#666666', 0.7, 'center');

        // Credits
        e.drawText('UGA Graduate School', PL.NATIVE_W / 2, 225, '#444444', 0.7, 'center');
    }

    function drawStory() {
        const e = E();
        e.clear('#000000');

        const lines = PL.INTRO_STORY;
        const lineH = 12;
        const startY = PL.NATIVE_H - storyScroll;

        for (let i = 0; i < lines.length; i++) {
            const y = startY + i * lineH;
            if (y < -lineH || y > PL.NATIVE_H + lineH) continue;

            // Fade at edges
            let alpha = 1;
            if (y < 30) alpha = Math.max(0, y / 30);
            if (y > PL.NATIVE_H - 30) alpha = Math.max(0, (PL.NATIVE_H - y) / 30);

            const line = lines[i];
            const color = line.includes('PALER') ? '#5fcf5f' :
                         line.includes('PRESS') ? '#ffd700' :
                         line.includes('...') ? '#5fc4eb' : '#c8c8e8';

            e.getCtx().globalAlpha = alpha;
            e.drawText(line, PL.NATIVE_W / 2, y, color, 1, 'center', '#000');
            e.getCtx().globalAlpha = 1;
        }

        // Skip hint
        e.drawText('ENTER to skip', PL.NATIVE_W - 10, PL.NATIVE_H - 12, '#444444', 0.7, 'right');
    }

    function drawLevelIntro() {
        const e = E();
        const def = PL.LEVELS[currentLevel];
        const worldInfo = PL.WORLD_INTROS[def.world];
        const worldPal = PL.WORLD_PAL[def.world];

        e.clear(worldPal.bg);

        // Animated grain background
        for (let i = 0; i < 20; i++) {
            const gx = (i * 47 + Math.floor(gameTime * 5)) % PL.NATIVE_W;
            const gy = (i * 31) % PL.NATIVE_H;
            e.drawRect(gx, gy, 8 + i % 5, 8 + i % 4, worldPal.grain, 0.2);
        }

        // World title
        const fadeIn = Math.min(1, levelIntroTimer * 2);
        const titleColor = '#ffffff';
        e.getCtx().globalAlpha = fadeIn;

        e.drawText(worldInfo.title, PL.NATIVE_W / 2, 25, titleColor, 2.5, 'center', '#000');
        e.drawText(worldInfo.subtitle, PL.NATIVE_W / 2, 55, worldPal.grainLight, 1.2, 'center', '#000');

        // Level name
        if (levelIntroTimer > 0.3) {
            const a2 = Math.min(1, (levelIntroTimer - 0.3) * 3);
            e.getCtx().globalAlpha = a2;
            e.drawText('Level ' + (currentLevel + 1) + ': ' + def.title, PL.NATIVE_W / 2, 78, '#ffd700', 1, 'center', '#000');
        }

        // Description text
        if (levelIntroTimer > 0.5) {
            const a3 = Math.min(1, (levelIntroTimer - 0.5) * 2);
            e.getCtx().globalAlpha = a3;
            e.drawTextWrap(worldInfo.text, 30, 100, PL.NATIVE_W - 60, '#c8c8e8', 0.9, 12);
        }

        // Goal
        if (levelIntroTimer > 1) {
            const a4 = Math.min(1, (levelIntroTimer - 1) * 2);
            e.getCtx().globalAlpha = a4;
            e.drawText('Goal: Place ' + def.colonyGoal + ' colony cells', PL.NATIVE_W / 2, 205, '#5fcf5f', 1, 'center', '#000');
        }

        e.getCtx().globalAlpha = 1;

        // Continue prompt
        if (levelIntroTimer > 1.5 && Math.sin(gameTime * 3) > 0) {
            e.drawText('PRESS ENTER', PL.NATIVE_W / 2, 225, '#ffd700', 1, 'center', '#000');
        }
    }

    function drawPlaying() {
        const e = E();
        const cam = e.camera;
        const pal = PL.World.getPalette();

        // Clear with world bg color
        e.clear(pal ? pal.bg : '#000000');

        // Draw world tiles
        PL.World.drawWorld(cam, gameTime);

        // Draw colonies
        PL.Entities.colonies.draw(cam, gameTime);

        // Draw substrate
        PL.Entities.substrates.draw(cam, gameTime);

        // Draw player
        PL.Entities.player.draw(cam, gameTime);

        // Draw particles
        e.particles.draw();

        // Science mode overlay
        if (scienceMode) {
            drawScienceOverlay();
        }

        // Screen flash
        e.updateFlash(1/60);

        // Draw HUD
        drawHUD();
    }

    function drawHUD() {
        const e = E();
        const p = PL.Entities.player;
        const def = PL.LEVELS[currentLevel];
        const hudY = PL.NATIVE_H - 32;

        // HUD background
        e.drawRect(0, hudY, PL.NATIVE_W, 32, PL.PAL.UI_BG, 0.85);
        e.drawRect(0, hudY, PL.NATIVE_W, 1, PL.PAL.UI_BORDER);

        // Health bar
        e.drawText('HP', 4, hudY + 3, PL.PAL.UI_TEXT, 0.7);
        e.drawRect(20, hudY + 3, 52, 7, '#1a1a2a');
        const healthW = Math.max(0, (p.health / PL.BALANCE.MAX_HEALTH) * 50);
        const healthColor = p.health > 50 ? PL.PAL.UI_HEALTH :
                           p.health > 25 ? '#ef8844' : '#ef2020';
        e.drawRect(21, hudY + 4, healthW, 5, healthColor);
        // Health flash when low
        if (p.health < 25 && Math.sin(gameTime * 8) > 0) {
            e.drawRect(21, hudY + 4, healthW, 5, '#ffffff', 0.5);
        }

        // Growth bar
        e.drawText('GR', 4, hudY + 13, PL.PAL.UI_TEXT, 0.7);
        e.drawRect(20, hudY + 13, 52, 7, '#1a1a2a');
        const growthW = Math.max(0, (p.growth / PL.BALANCE.DIVISION_GROWTH_COST) * 50);
        e.drawRect(21, hudY + 14, growthW, 5, PL.PAL.UI_GROWTH);
        // Glow when full
        if (p.canDivide && Math.sin(gameTime * 4) > 0) {
            e.drawRect(21, hudY + 14, 50, 5, '#ffff5f', 0.3);
            e.drawText('SPACE to divide!', 80, hudY + 13, '#ffff5f', 0.7, 'left', '#000');
        }

        // Colony counter
        const colCount = PL.Entities.colonies.getCount();
        const colGoal = def ? def.colonyGoal : 5;
        e.drawText('Colony: ' + colCount + '/' + colGoal, 80, hudY + 3, '#c8c8e8', 0.7, 'left', '#000');

        // Score
        e.drawText('Score: ' + (totalScore + p.score), PL.NATIVE_W - 4, hudY + 3, '#ffd700', 0.7, 'right', '#000');

        // Level indicator
        const worldNames = ['W1', 'W2', 'W3', 'W4'];
        const wIdx = def ? def.world : 0;
        e.drawText(worldNames[wIdx] + '-' + ((currentLevel % 3) + 1), PL.NATIVE_W - 4, hudY + 13, '#888888', 0.7, 'right');

        // Science mode indicator
        if (scienceMode) {
            e.drawText('[SCIENCE]', PL.NATIVE_W / 2, hudY + 13, '#5fc4eb', 0.7, 'center');
        }

        // Mute indicator
        if (PL.Audio.isMuted()) {
            e.drawText('[MUTED]', PL.NATIVE_W / 2, hudY + 22, '#888888', 0.6, 'center');
        }

        // Mini-map
        drawMiniMap(hudY);
    }

    function drawMiniMap(hudY) {
        const e = E();
        const mapSize = PL.World.getMapSize();
        const p = PL.Entities.player;

        const mmW = 40;
        const mmH = 24;
        const mmX = PL.NATIVE_W - mmW - 4;
        const mmY = hudY - mmH - 4;

        // Background
        e.drawRect(mmX - 1, mmY - 1, mmW + 2, mmH + 2, '#000000', 0.7);
        e.drawRectOutline(mmX - 1, mmY - 1, mmW + 2, mmH + 2, PL.PAL.UI_BORDER);

        const scaleX = mmW / mapSize.w;
        const scaleY = mmH / mapSize.h;

        // Draw map at mini scale
        const ctx = e.getCtx();
        const pal = PL.World.getPalette();

        for (let y = 0; y < mapSize.h; y += 2) {
            for (let x = 0; x < mapSize.w; x += 2) {
                const tile = PL.World.getTile(x, y);
                let color = null;
                if (tile === PL.TILES.SOLID) color = pal.grain;
                else if (tile === PL.TILES.TOXIC) color = pal.toxic;
                else if (tile === PL.TILES.BIOFILM) color = '#3a7a3a';
                else if (tile === PL.TILES.OUTLET) color = '#5fcf5f';

                if (color) {
                    e.drawRect(mmX + x * scaleX, mmY + y * scaleY,
                              Math.max(1, scaleX * 2), Math.max(1, scaleY * 2), color, 0.7);
                }
            }
        }

        // Player blip
        const px = mmX + p.tileX * scaleX;
        const py = mmY + p.tileY * scaleY;
        const blink = Math.sin(gameTime * 6) > 0;
        if (blink) {
            e.drawRect(px - 1, py - 1, 3, 3, '#ffffff');
        } else {
            e.drawRect(px, py, 2, 2, '#5fcf5f');
        }

        // Colony blips
        PL.Entities.colonies.list.forEach(c => {
            e.drawRect(mmX + c.x * scaleX, mmY + c.y * scaleY, 1, 1, '#5fcf5f', 0.8);
        });
    }

    function drawScienceOverlay() {
        const e = E();
        const cam = e.camera;
        const mapSize = PL.World.getMapSize();
        const p = PL.Entities.player;

        // Semi-transparent overlay
        e.drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H - 32, '#000000', 0.3);

        // Draw flow arrows
        const startCol = Math.max(0, Math.floor(cam.x / T));
        const endCol = Math.min(mapSize.w, startCol + PL.COLS + 2);
        const startRow = Math.max(0, Math.floor(cam.y / T));
        const endRow = Math.min(mapSize.h, startRow + PL.ROWS + 3);

        for (let row = startRow; row < endRow; row += 2) {
            for (let col = startCol; col < endCol; col += 2) {
                const flow = PL.World.getFlow(col, row);
                if (flow.dir === 0 || flow.speed < 0.05) continue;

                const sx = cam.screenX(col * T + 4);
                const sy = cam.screenY(row * T + 4);

                // Flow arrow
                const sprite = flow.dir === 1 ? PL.Sprites.flowRight :
                              flow.dir === 3 ? PL.Sprites.flowLeft :
                              PL.Sprites.flowDown;
                const alpha = Math.min(0.8, flow.speed * 1.5);
                e.drawSprite(sprite, sx, sy, alpha);
            }
        }

        // Concentration heatmap around player
        for (let dy = -5; dy <= 5; dy++) {
            for (let dx = -5; dx <= 5; dx++) {
                const tx = p.tileX + dx;
                const ty = p.tileY + dy;
                const tile = PL.World.getTile(tx, ty);
                if (!PL.World.isWalkable(tile)) continue;

                // Simulated concentration (based on distance from inlet and flow)
                const dist = PL.World.getDistance(tx, ty);
                const flow = PL.World.getFlow(tx, ty);
                const conc = Math.max(0, 1 - tx / mapSize.w) * (0.5 + flow.speed);

                const sx = cam.screenX(tx * T);
                const sy = cam.screenY(ty * T);

                // Heatmap color
                const r = Math.floor(Math.min(255, conc * 50));
                const g = Math.floor(Math.min(255, conc * 255));
                const b = Math.floor(Math.min(255, (1 - conc) * 100));
                e.drawRect(sx, sy, T, T, `rgb(${r},${g},${b})`, 0.25);
            }
        }

        // Science info panel
        e.drawRect(2, 2, 140, 65, '#000000', 0.8);
        e.drawRectOutline(2, 2, 140, 65, '#5fc4eb');
        e.drawText('SCIENCE MODE', 6, 5, '#5fc4eb', 0.8, 'left');
        e.drawText('Flow: ' + PL.BALANCE.FLOW_SPEEDS[PL.World.getWorldIdx()].toFixed(1) + ' T/s', 6, 16, '#aaa', 0.7);

        // Monod growth at current position
        const substCount = PL.Entities.substrates.list.length;
        const simConc = Math.max(0.01, substCount / 20);
        const mu = PL.SCIENCE.mu_max * simConc / (PL.SCIENCE.Ks * 1e5 + simConc);
        e.drawText('mu=' + mu.toFixed(3) + ' /s', 6, 27, '#aaa', 0.7);
        e.drawText('C/Ks=' + (simConc / (PL.SCIENCE.Ks * 1e5)).toFixed(2), 6, 38, '#aaa', 0.7);

        const monodStr = 'mu = mu_max*C/(Ks+C)';
        e.drawText(monodStr, 6, 50, '#5fc4eb', 0.6);

        e.drawText('Q: toggle', 6, 60, '#666', 0.6);
    }

    function drawPause() {
        const e = E();

        // Overlay
        e.drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H, '#000000', 0.6);

        // Pause box
        const bx = PL.NATIVE_W / 2 - 60;
        const by = 60;
        e.drawRect(bx, by, 120, 90, '#0a0a2a', 0.95);
        e.drawRectOutline(bx, by, 120, 90, PL.PAL.UI_BORDER);

        e.drawText('PAUSED', PL.NATIVE_W / 2, by + 8, '#ffffff', 1.5, 'center');

        const options = ['Resume', PL.Audio.isMuted() ? 'Unmute' : 'Mute', 'Quit'];
        for (let i = 0; i < options.length; i++) {
            const color = i === pauseSelection ? '#ffd700' : '#888888';
            const prefix = i === pauseSelection ? '> ' : '  ';
            e.drawText(prefix + options[i], PL.NATIVE_W / 2, by + 35 + i * 16, color, 1, 'center', '#000');
        }
    }

    function drawSciencePopup() {
        const e = E();
        const fact = PL.SCIENCE_FACTS[sciencePopupIdx];
        if (!fact) return;

        // Overlay
        e.drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H, '#000000', 0.7);

        // Science box
        const bx = 15;
        const by = 15;
        const bw = PL.NATIVE_W - 30;
        const bh = PL.NATIVE_H - 50;

        e.drawRect(bx, by, bw, bh, '#0a0a2a', 0.95);
        e.drawRectOutline(bx, by, bw, bh, '#5fc4eb');

        // Header
        e.drawRect(bx + 1, by + 1, bw - 2, 20, '#0a1e3c');
        e.drawText('SCIENCE DISCOVERY', bx + bw / 2, by + 4, '#5fc4eb', 1, 'center');

        // Title
        e.drawText(fact.title, bx + bw / 2, by + 28, '#ffd700', 1.2, 'center', '#000');

        // Content
        e.drawTextWrap(fact.text, bx + 10, by + 48, bw - 20, '#c8c8e8', 0.75, 10);

        // Score
        e.drawText('+' + PL.BALANCE.SCORE_SCIENCE + ' pts', bx + bw / 2, by + bh - 20, '#5fcf5f', 0.8, 'center');

        // Continue
        if (Math.sin(gameTime * 3) > 0) {
            e.drawText('PRESS ENTER', bx + bw / 2, by + bh - 8, '#ffd700', 0.8, 'center');
        }
    }

    function drawLevelComplete() {
        const e = E();
        const p = PL.Entities.player;
        const def = PL.LEVELS[currentLevel];

        // Overlay
        const alpha = Math.min(0.7, levelCompleteTimer);
        e.drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H, '#000000', alpha);

        if (levelCompleteTimer < 0.5) return;

        // Box
        const bx = PL.NATIVE_W / 2 - 80;
        const by = 40;
        e.drawRect(bx, by, 160, 130, '#0a1a0a', 0.95);
        e.drawRectOutline(bx, by, 160, 130, '#5fcf5f');

        e.drawText('LEVEL COMPLETE!', PL.NATIVE_W / 2, by + 8, '#5fcf5f', 1.3, 'center', '#000');

        // Stats
        const statY = by + 35;
        e.drawText('Substrate eaten: ' + p.substrateEaten, bx + 10, statY, '#c8c8e8', 0.8);
        e.drawText('Colonies placed: ' + p.coloniesPlaced, bx + 10, statY + 14, '#c8c8e8', 0.8);
        e.drawText('Time: ' + Math.floor(levelTime) + 's', bx + 10, statY + 28, '#c8c8e8', 0.8);

        const timeBonus = Math.max(0, Math.floor(PL.BALANCE.SCORE_TIME_BONUS * (1 - levelTime / 120)));
        e.drawText('Time bonus: +' + timeBonus, bx + 10, statY + 42, '#ffd700', 0.8);
        e.drawText('Level score: ' + p.score, bx + 10, statY + 56, '#ffd700', 0.9);

        // Continue
        if (levelCompleteTimer > 1.5 && Math.sin(gameTime * 3) > 0) {
            e.drawText('PRESS ENTER', PL.NATIVE_W / 2, by + 118, '#ffd700', 0.9, 'center');
        }
    }

    function drawGameOver() {
        const e = E();

        // Red overlay
        const alpha = Math.min(0.7, deathTimer * 0.5);
        e.drawRect(0, 0, PL.NATIVE_W, PL.NATIVE_H, '#1a0000', alpha);

        if (deathTimer < 1) return;

        e.drawText('MICROBE LOST', PL.NATIVE_W / 2, 70, '#ef4444', 2, 'center', '#000');

        // Science death message
        const messages = [
            'Substrate limitation proved fatal.',
            'The geochemical environment was too hostile.',
            'Without nutrients, even microbes perish.',
            'Starvation: the ultimate substrate limitation.'
        ];
        const msg = messages[Math.floor(gameTime) % messages.length];
        e.drawText(msg, PL.NATIVE_W / 2, 105, '#888888', 0.8, 'center');

        e.drawText('Score: ' + (totalScore + PL.Entities.player.score), PL.NATIVE_W / 2, 135, '#ffd700', 1, 'center', '#000');

        if (deathTimer > 2 && Math.sin(gameTime * 3) > 0) {
            e.drawText('PRESS ENTER TO RETRY', PL.NATIVE_W / 2, 170, '#c8c8e8', 1, 'center');
        }
    }

    function drawVictory() {
        const e = E();
        e.clear('#060e1e');

        // Stars
        for (let i = 0; i < 30; i++) {
            const sx = (Math.sin(i * 73) * 0.5 + 0.5) * PL.NATIVE_W;
            const sy = (Math.cos(i * 97) * 0.5 + 0.5) * PL.NATIVE_H;
            const blink = Math.sin(gameTime * 2 + i) > 0.5 ? 1 : 0.3;
            e.drawRect(sx, sy, 1, 1, '#ffffff', blink);
        }

        // Title
        e.drawText('VICTORY!', PL.NATIVE_W / 2, 20, '#ffd700', 3, 'center', '#000');

        // Paler celebrates
        const px = PL.NATIVE_W / 2 - 8;
        const py = 55 + Math.sin(gameTime * 3) * 5;
        e.drawSprite(PL.Sprites.paler.glow, px, py);

        // Colony sprites around
        for (let i = 0; i < 6; i++) {
            const angle = (i / 6) * Math.PI * 2 + gameTime * 0.5;
            const cx = PL.NATIVE_W / 2 + Math.cos(angle) * 35 - 8;
            const cy = 65 + Math.sin(angle) * 20;
            e.drawSprite(PL.Sprites.colony, cx, cy, 0.8);
        }

        // Story
        if (victoryTimer > 1) {
            e.drawText('Paler has colonized the underground!', PL.NATIVE_W / 2, 100, '#5fcf5f', 0.9, 'center', '#000');
        }
        if (victoryTimer > 2) {
            e.drawText('From a single microbe to a thriving colony,', PL.NATIVE_W / 2, 120, '#c8c8e8', 0.8, 'center');
            e.drawText('life has spread through the pore space.', PL.NATIVE_W / 2, 132, '#c8c8e8', 0.8, 'center');
        }
        if (victoryTimer > 3) {
            e.drawText('Final Score: ' + totalScore, PL.NATIVE_W / 2, 155, '#ffd700', 1.3, 'center', '#000');
        }
        if (victoryTimer > 4) {
            e.drawText('Based on CompLaB3D', PL.NATIVE_W / 2, 180, '#5fc4eb', 0.8, 'center');
            e.drawText('Pore-Scale Biogeochemical', PL.NATIVE_W / 2, 192, '#5fc4eb', 0.7, 'center');
            e.drawText('Reactive Transport Simulator', PL.NATIVE_W / 2, 202, '#5fc4eb', 0.7, 'center');
        }
        if (victoryTimer > 5) {
            e.drawText('University of Georgia', PL.NATIVE_W / 2, 218, '#888888', 0.7, 'center');
        }

        if (victoryTimer > 3 && Math.sin(gameTime * 3) > 0) {
            e.drawText('PRESS ENTER', PL.NATIVE_W / 2, 233, '#ffd700', 0.8, 'center');
        }
    }

    // ─── EXPORT ─────────────────────────────────────────────
    PL.Game = {
        update,
        draw,
        getState() { return state; },
        getCurrentLevel() { return currentLevel; },
        getGameTime() { return gameTime; }
    };
})();
