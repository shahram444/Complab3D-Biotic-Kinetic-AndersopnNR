/**
 * PORELIFE: Microbe Survivor
 * World Generation & Tile Rendering
 * Generates scientifically-inspired pore geometries
 */

(function() {
    const T = PL.TILE;
    const TILES = PL.TILES;

    // ─── WORLD STATE ────────────────────────────────────────
    let map = null;        // 2D tile array
    let flowMap = null;    // 2D flow direction array (0=none,1=right,2=down,3=left,4=up)
    let flowSpeed = null;  // 2D flow speed array
    let distMap = null;    // Distance to nearest solid
    let mapW = 0, mapH = 0;
    let worldIdx = 0;
    let pal = null;

    // Tile sprite caches (generated per world)
    let tileCache = {};

    // ─── SEEDED RANDOM ──────────────────────────────────────
    let seed = 12345;
    function setSeed(s) { seed = s; }
    function rand() {
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF;
        return (seed >>> 0) / 0xFFFFFFFF;
    }
    function randInt(min, max) {
        return Math.floor(rand() * (max - min + 1)) + min;
    }

    // ─── TILE GENERATION ────────────────────────────────────

    function generateTileSprites(worldPal) {
        tileCache = {};
        const p = worldPal;

        // Solid grain tile (with variation)
        tileCache.grain = [];
        for (let v = 0; v < 4; v++) {
            const s = new Array(16).fill(null).map(() => new Array(16).fill(null));
            for (let y = 0; y < 16; y++) {
                for (let x = 0; x < 16; x++) {
                    const r = Math.random();
                    if (r < 0.5) s[y][x] = p.grain;
                    else if (r < 0.75) s[y][x] = p.grainLight;
                    else if (r < 0.9) s[y][x] = p.grainDark;
                    else s[y][x] = p.grainAccent;
                }
            }
            tileCache.grain.push(s);
        }

        // Grain top (slightly lighter top edge)
        tileCache.grainTop = [];
        for (let v = 0; v < 2; v++) {
            const s = JSON.parse(JSON.stringify(tileCache.grain[v]));
            for (let x = 0; x < 16; x++) {
                s[0][x] = p.grainAccent;
                if (Math.random() > 0.3) s[1][x] = p.grainLight;
            }
            tileCache.grainTop.push(s);
        }

        // Pore tile (dark with subtle water)
        tileCache.pore = [];
        for (let v = 0; v < 4; v++) {
            const s = new Array(16).fill(null).map(() => new Array(16).fill(null));
            for (let y = 0; y < 16; y++) {
                for (let x = 0; x < 16; x++) {
                    const r = Math.random();
                    if (r < 0.7) s[y][x] = p.pore;
                    else if (r < 0.9) s[y][x] = p.poreLight;
                    else s[y][x] = p.water;
                }
            }
            tileCache.pore.push(s);
        }

        // Flow channel (slightly brighter water)
        tileCache.flow = [];
        for (let v = 0; v < 2; v++) {
            const s = new Array(16).fill(null).map(() => new Array(16).fill(null));
            for (let y = 0; y < 16; y++) {
                for (let x = 0; x < 16; x++) {
                    const r = Math.random();
                    if (r < 0.4) s[y][x] = p.water;
                    else if (r < 0.7) s[y][x] = p.waterLight;
                    else if (r < 0.9) s[y][x] = p.poreLight;
                    else s[y][x] = p.pore;
                }
            }
            tileCache.flow.push(s);
        }

        // Toxic tile
        tileCache.toxic = [];
        for (let v = 0; v < 2; v++) {
            const s = new Array(16).fill(null).map(() => new Array(16).fill(null));
            for (let y = 0; y < 16; y++) {
                for (let x = 0; x < 16; x++) {
                    const r = Math.random();
                    if (r < 0.4) s[y][x] = p.toxic;
                    else if (r < 0.7) s[y][x] = p.toxicGlow;
                    else if (r < 0.85) s[y][x] = p.pore;
                    else s[y][x] = '#2a0a2a';
                }
            }
            tileCache.toxic.push(s);
        }

        // Biofilm tile
        tileCache.biofilm = [];
        for (let v = 0; v < 2; v++) {
            const s = new Array(16).fill(null).map(() => new Array(16).fill(null));
            for (let y = 0; y < 16; y++) {
                for (let x = 0; x < 16; x++) {
                    const r = Math.random();
                    if (r < 0.5) s[y][x] = '#2a5a2a';
                    else if (r < 0.8) s[y][x] = '#3a7a3a';
                    else s[y][x] = '#1a4a1a';
                }
            }
            tileCache.biofilm.push(s);
        }

        // Inlet tile (glowing left edge)
        tileCache.inlet = new Array(16).fill(null).map((_, y) =>
            new Array(16).fill(null).map((_, x) => {
                if (x < 3) return '#3c7ab5';
                if (x < 5) return p.waterLight;
                return p.water;
            })
        );

        // Outlet tile (glowing right edge)
        tileCache.outlet = new Array(16).fill(null).map((_, y) =>
            new Array(16).fill(null).map((_, x) => {
                if (x > 12) return '#5fcf5f';
                if (x > 10) return '#3a7a3a';
                const r = Math.random();
                return r < 0.5 ? p.pore : p.poreLight;
            })
        );
    }

    // ─── MAP GENERATION ─────────────────────────────────────

    function generate(levelDef) {
        worldIdx = levelDef.world;
        pal = PL.WORLD_PAL[worldIdx];
        mapW = levelDef.mapW;
        mapH = levelDef.mapH;

        setSeed(levelDef.world * 1000 + levelDef.colonyGoal * 137 + mapW * 31 + mapH * 17);

        map = new Array(mapH).fill(null).map(() => new Array(mapW).fill(TILES.SOLID));
        flowMap = new Array(mapH).fill(null).map(() => new Array(mapW).fill(0));
        flowSpeed = new Array(mapH).fill(null).map(() => new Array(mapW).fill(0));

        // Step 1: Create pore structure based on world type
        switch (worldIdx) {
            case 0: generateSandyMaze(levelDef); break;
            case 1: generateClayLabyrinth(levelDef); break;
            case 2: generateToxicVeins(levelDef); break;
            case 3: generateFlowHighways(levelDef); break;
        }

        // Step 2: Ensure connectivity (flood fill from start)
        ensureConnectivity();

        // Step 3: Place inlet/outlet
        placeInletOutlet();

        // Step 4: Compute flow field
        computeFlowField();

        // Step 5: Compute distance map
        computeDistanceMap();

        // Step 6: Add toxic zones for world 3
        if (worldIdx === 2) {
            addToxicZones(levelDef);
        }

        // Generate tile sprites for this world
        generateTileSprites(pal);

        return { map, flowMap, flowSpeed, distMap, mapW, mapH, worldIdx, pal };
    }

    // ─── WORLD GENERATORS ───────────────────────────────────

    function generateSandyMaze(def) {
        // Wide channels between round grains
        // Start with all pore, then place circular grains
        for (let y = 0; y < mapH; y++) {
            for (let x = 0; x < mapW; x++) {
                map[y][x] = TILES.PORE;
            }
        }

        // Place circular grains
        const numGrains = Math.floor(mapW * mapH * (1 - def.porosity) / 6);
        for (let i = 0; i < numGrains; i++) {
            const gx = randInt(2, mapW - 3);
            const gy = randInt(2, mapH - 3);
            const gr = randInt(def.grainSize[0], def.grainSize[1]);
            for (let dy = -gr; dy <= gr; dy++) {
                for (let dx = -gr; dx <= gr; dx++) {
                    if (dx * dx + dy * dy <= gr * gr) {
                        const tx = gx + dx;
                        const ty = gy + dy;
                        if (tx >= 1 && tx < mapW - 1 && ty >= 1 && ty < mapH - 1) {
                            map[ty][tx] = TILES.SOLID;
                        }
                    }
                }
            }
        }

        // Border walls
        addBorderWalls();
    }

    function generateClayLabyrinth(def) {
        // Tight, narrow channels - maze-like
        // Start solid, carve tunnels
        for (let y = 0; y < mapH; y++) {
            for (let x = 0; x < mapW; x++) {
                map[y][x] = TILES.SOLID;
            }
        }

        // Recursive backtracker maze on coarser grid then expand
        const cellW = Math.floor((mapW - 2) / 2);
        const cellH = Math.floor((mapH - 2) / 2);
        const visited = new Array(cellH).fill(null).map(() => new Array(cellW).fill(false));
        const stack = [];

        let cx = 0, cy = 0;
        visited[cy][cx] = true;
        stack.push([cx, cy]);

        while (stack.length > 0) {
            const neighbors = [];
            const dirs = [[0,-1],[1,0],[0,1],[-1,0]];
            for (const [ddx, ddy] of dirs) {
                const nx = cx + ddx;
                const ny = cy + ddy;
                if (nx >= 0 && nx < cellW && ny >= 0 && ny < cellH && !visited[ny][nx]) {
                    neighbors.push([nx, ny, ddx, ddy]);
                }
            }

            if (neighbors.length > 0) {
                const [nx, ny, ddx, ddy] = neighbors[randInt(0, neighbors.length - 1)];
                // Carve passage
                const mx = 1 + cx * 2 + ddx;
                const my = 1 + cy * 2 + ddy;
                map[my][mx] = TILES.PORE;
                map[1 + ny * 2][1 + nx * 2] = TILES.PORE;
                map[1 + cy * 2][1 + cx * 2] = TILES.PORE;
                visited[ny][nx] = true;
                stack.push([cx, cy]);
                cx = nx;
                cy = ny;
            } else {
                const prev = stack.pop();
                cx = prev[0];
                cy = prev[1];
            }
        }

        // Widen some passages slightly for playability
        const mapCopy = map.map(r => [...r]);
        for (let y = 2; y < mapH - 2; y++) {
            for (let x = 2; x < mapW - 2; x++) {
                if (mapCopy[y][x] === TILES.PORE && rand() < 0.3) {
                    // Widen in a random direction
                    const d = randInt(0, 3);
                    const ddx = [0,1,0,-1][d];
                    const ddy = [-1,0,1,0][d];
                    if (y + ddy > 0 && y + ddy < mapH - 1 && x + ddx > 0 && x + ddx < mapW - 1) {
                        map[y + ddy][x + ddx] = TILES.PORE;
                    }
                }
            }
        }

        addBorderWalls();
    }

    function generateToxicVeins(def) {
        // Mixed: pore space with toxic veins running through
        generateSandyMaze(def); // Base structure

        // Toxic zones added later in addToxicZones
    }

    function generateFlowHighways(def) {
        // Wide main channels with branching side paths
        for (let y = 0; y < mapH; y++) {
            for (let x = 0; x < mapW; x++) {
                map[y][x] = TILES.SOLID;
            }
        }

        // Create main horizontal highways
        const numHighways = randInt(3, 5);
        const spacing = Math.floor(mapH / (numHighways + 1));
        for (let i = 0; i < numHighways; i++) {
            const baseY = spacing * (i + 1);
            const width = randInt(2, 4);
            for (let x = 0; x < mapW; x++) {
                const wobble = Math.floor(Math.sin(x * 0.3 + i) * 1.5);
                for (let dy = -width; dy <= width; dy++) {
                    const ty = baseY + dy + wobble;
                    if (ty > 0 && ty < mapH - 1) {
                        map[ty][x] = TILES.PORE;
                    }
                }
            }
        }

        // Add vertical connectors
        const numConnectors = randInt(mapW / 5, mapW / 3);
        for (let i = 0; i < numConnectors; i++) {
            const cx = randInt(3, mapW - 4);
            const startY = randInt(2, mapH - 3);
            const len = randInt(3, spacing + 2);
            const width = randInt(1, 2);
            for (let dy = 0; dy < len; dy++) {
                const ty = startY + dy;
                if (ty > 0 && ty < mapH - 1) {
                    for (let w = -width; w <= width; w++) {
                        const tx = cx + w;
                        if (tx > 0 && tx < mapW - 1) {
                            map[ty][tx] = TILES.PORE;
                        }
                    }
                }
            }
        }

        // Add some round chambers
        const numChambers = randInt(4, 8);
        for (let i = 0; i < numChambers; i++) {
            const cx = randInt(5, mapW - 6);
            const cy = randInt(5, mapH - 6);
            const r = randInt(2, 4);
            for (let dy = -r; dy <= r; dy++) {
                for (let dx = -r; dx <= r; dx++) {
                    if (dx * dx + dy * dy <= r * r) {
                        const tx = cx + dx;
                        const ty = cy + dy;
                        if (tx > 0 && tx < mapW - 1 && ty > 0 && ty < mapH - 1) {
                            map[ty][tx] = TILES.PORE;
                        }
                    }
                }
            }
        }

        // Mark highways as fast flow
        for (let y = 0; y < mapH; y++) {
            for (let x = 0; x < mapW; x++) {
                if (map[y][x] === TILES.PORE) {
                    // Check if in a main highway (wide channel)
                    let poreCount = 0;
                    for (let dy = -2; dy <= 2; dy++) {
                        const ty = y + dy;
                        if (ty >= 0 && ty < mapH && map[ty][x] === TILES.PORE) poreCount++;
                    }
                    if (poreCount >= 4) {
                        map[y][x] = TILES.FLOW_FAST;
                    }
                }
            }
        }

        addBorderWalls();
    }

    function addToxicZones(def) {
        const coverage = PL.BALANCE.TOXIC_COVERAGE[worldIdx] || 0.15;
        const numVeins = randInt(3, 6);

        for (let v = 0; v < numVeins; v++) {
            // Random vein path
            let vx = randInt(3, mapW - 4);
            let vy = randInt(2, mapH - 3);
            const vlen = randInt(8, 20);
            const vdir = rand() < 0.5 ? 'h' : 'v';

            for (let step = 0; step < vlen; step++) {
                const width = randInt(1, 2);
                for (let dw = -width; dw <= width; dw++) {
                    const tx = vdir === 'h' ? vx + step : vx + dw;
                    const ty = vdir === 'v' ? vy + step : vy + dw;
                    if (tx > 1 && tx < mapW - 2 && ty > 1 && ty < mapH - 2) {
                        if (map[ty][tx] === TILES.PORE) {
                            map[ty][tx] = TILES.TOXIC;
                        }
                    }
                }
                // Wobble
                if (rand() < 0.4) {
                    if (vdir === 'h') vy += randInt(-1, 1);
                    else vx += randInt(-1, 1);
                }
            }
        }
    }

    function addBorderWalls() {
        for (let x = 0; x < mapW; x++) {
            map[0][x] = TILES.SOLID;
            map[mapH - 1][x] = TILES.SOLID;
        }
        for (let y = 0; y < mapH; y++) {
            map[y][0] = TILES.SOLID;
            map[y][mapW - 1] = TILES.SOLID;
        }
    }

    // ─── CONNECTIVITY ───────────────────────────────────────

    function ensureConnectivity() {
        // Find a start pore
        let startX = -1, startY = -1;
        for (let y = 1; y < mapH - 1 && startX < 0; y++) {
            for (let x = 1; x < mapW / 3 && startX < 0; x++) {
                if (isWalkable(map[y][x])) {
                    startX = x;
                    startY = y;
                }
            }
        }

        if (startX < 0) {
            // No pore found, create one
            startX = 2;
            startY = Math.floor(mapH / 2);
            map[startY][startX] = TILES.PORE;
        }

        // Flood fill from start
        const visited = new Array(mapH).fill(null).map(() => new Array(mapW).fill(false));
        const queue = [[startX, startY]];
        visited[startY][startX] = true;
        const reachable = new Set();
        reachable.add(startY * mapW + startX);

        while (queue.length > 0) {
            const [cx, cy] = queue.shift();
            const dirs = [[0,-1],[1,0],[0,1],[-1,0]];
            for (const [dx, dy] of dirs) {
                const nx = cx + dx;
                const ny = cy + dy;
                if (nx >= 0 && nx < mapW && ny >= 0 && ny < mapH && !visited[ny][nx] && isWalkable(map[ny][nx])) {
                    visited[ny][nx] = true;
                    queue.push([nx, ny]);
                    reachable.add(ny * mapW + nx);
                }
            }
        }

        // Find isolated pore clusters and connect them
        for (let y = 1; y < mapH - 1; y++) {
            for (let x = 1; x < mapW - 1; x++) {
                if (isWalkable(map[y][x]) && !reachable.has(y * mapW + x)) {
                    // Carve a path toward the reachable set
                    let cx = x, cy = y;
                    let steps = 0;
                    while (!reachable.has(cy * mapW + cx) && steps < mapW + mapH) {
                        // Move toward start
                        if (Math.abs(cx - startX) > Math.abs(cy - startY)) {
                            cx += cx < startX ? 1 : -1;
                        } else {
                            cy += cy < startY ? 1 : -1;
                        }
                        cx = Math.max(1, Math.min(mapW - 2, cx));
                        cy = Math.max(1, Math.min(mapH - 2, cy));
                        if (map[cy][cx] === TILES.SOLID) {
                            map[cy][cx] = TILES.PORE;
                        }
                        reachable.add(cy * mapW + cx);
                        steps++;
                    }
                }
            }
        }

        // Make sure there's a path to the right side
        let hasRightPore = false;
        for (let y = 1; y < mapH - 1; y++) {
            if (isWalkable(map[y][mapW - 2]) && reachable.has(y * mapW + (mapW - 2))) {
                hasRightPore = true;
                break;
            }
        }
        if (!hasRightPore) {
            const midY = Math.floor(mapH / 2);
            for (let x = mapW - 2; x > 0; x--) {
                if (map[midY][x] === TILES.SOLID) {
                    map[midY][x] = TILES.PORE;
                }
                if (reachable.has(midY * mapW + x)) break;
            }
        }
    }

    function isWalkable(tile) {
        return tile === TILES.PORE || tile === TILES.TOXIC || tile === TILES.FLOW_FAST ||
               tile === TILES.INLET || tile === TILES.OUTLET || tile === TILES.BIOFILM;
    }

    // ─── INLET / OUTLET ─────────────────────────────────────

    function placeInletOutlet() {
        // Find leftmost pore column for inlet
        for (let x = 0; x < mapW; x++) {
            for (let y = 1; y < mapH - 1; y++) {
                if (isWalkable(map[y][x])) {
                    map[y][x] = TILES.INLET;
                    return placeOutlet();
                }
            }
        }
    }

    function placeOutlet() {
        // Find rightmost pore for outlet
        for (let x = mapW - 1; x >= 0; x--) {
            for (let y = 1; y < mapH - 1; y++) {
                if (isWalkable(map[y][x])) {
                    map[y][x] = TILES.OUTLET;
                    return;
                }
            }
        }
    }

    // ─── FLOW FIELD ─────────────────────────────────────────

    function computeFlowField() {
        // Simplified pressure-driven flow: left-to-right bias
        // Using a simple diffusion-based approach
        const pressure = new Array(mapH).fill(null).map(() => new Array(mapW).fill(0));
        const baseSpeed = PL.BALANCE.FLOW_SPEEDS[worldIdx] || 0.5;

        // Set boundary conditions: high pressure left, low right
        for (let y = 0; y < mapH; y++) {
            pressure[y][0] = 1.0;
            pressure[y][mapW - 1] = 0.0;
        }

        // Simple Jacobi iteration for pressure field
        for (let iter = 0; iter < 50; iter++) {
            for (let y = 1; y < mapH - 1; y++) {
                for (let x = 1; x < mapW - 1; x++) {
                    if (map[y][x] === TILES.SOLID) continue;
                    let sum = 0;
                    let count = 0;
                    const dirs = [[0,-1],[1,0],[0,1],[-1,0]];
                    for (const [dx, dy] of dirs) {
                        const nx = x + dx;
                        const ny = y + dy;
                        if (nx >= 0 && nx < mapW && ny >= 0 && ny < mapH && map[ny][nx] !== TILES.SOLID) {
                            sum += pressure[ny][nx];
                            count++;
                        }
                    }
                    if (count > 0) {
                        pressure[y][x] = sum / count;
                    }
                }
            }
        }

        // Compute flow direction from pressure gradient
        for (let y = 1; y < mapH - 1; y++) {
            for (let x = 1; x < mapW - 1; x++) {
                if (map[y][x] === TILES.SOLID) continue;

                let maxGrad = 0;
                let bestDir = 0;
                const dirs = [[1,0,1],[-1,0,3],[0,1,2],[0,-1,4]]; // dx,dy,direction

                for (const [dx, dy, dir] of dirs) {
                    const nx = x + dx;
                    const ny = y + dy;
                    if (nx >= 0 && nx < mapW && ny >= 0 && ny < mapH && map[ny][nx] !== TILES.SOLID) {
                        const grad = pressure[y][x] - pressure[ny][nx];
                        if (grad > maxGrad) {
                            maxGrad = grad;
                            bestDir = dir;
                        }
                    }
                }

                flowMap[y][x] = bestDir;
                let spd = maxGrad * baseSpeed * 40;
                if (map[y][x] === TILES.FLOW_FAST) spd *= 2.5;
                flowSpeed[y][x] = Math.min(spd, baseSpeed * 3);
            }
        }
    }

    // ─── DISTANCE MAP ───────────────────────────────────────

    function computeDistanceMap() {
        distMap = new Array(mapH).fill(null).map(() => new Array(mapW).fill(999));

        // BFS from all solid cells
        const queue = [];
        for (let y = 0; y < mapH; y++) {
            for (let x = 0; x < mapW; x++) {
                if (map[y][x] === TILES.SOLID) {
                    distMap[y][x] = 0;
                    queue.push([x, y]);
                }
            }
        }

        while (queue.length > 0) {
            const [cx, cy] = queue.shift();
            const dirs = [[0,-1],[1,0],[0,1],[-1,0]];
            for (const [dx, dy] of dirs) {
                const nx = cx + dx;
                const ny = cy + dy;
                if (nx >= 0 && nx < mapW && ny >= 0 && ny < mapH) {
                    if (distMap[ny][nx] > distMap[cy][cx] + 1) {
                        distMap[ny][nx] = distMap[cy][cx] + 1;
                        queue.push([nx, ny]);
                    }
                }
            }
        }
    }

    // ─── DRAWING ────────────────────────────────────────────

    function drawWorld(cam, time) {
        const E = PL.Engine;
        const startCol = Math.max(0, Math.floor(cam.x / T));
        const endCol = Math.min(mapW, startCol + PL.COLS + 2);
        const startRow = Math.max(0, Math.floor(cam.y / T));
        const endRow = Math.min(mapH, startRow + PL.ROWS + 3);

        for (let row = startRow; row < endRow; row++) {
            for (let col = startCol; col < endCol; col++) {
                const tile = map[row][col];
                const sx = cam.screenX(col * T);
                const sy = cam.screenY(row * T);
                const variation = ((col * 7 + row * 13) & 3);

                switch (tile) {
                    case TILES.SOLID: {
                        // Check if top face
                        const isTop = row > 0 && map[row - 1][col] !== TILES.SOLID;
                        const sprites = isTop ? tileCache.grainTop : tileCache.grain;
                        const v = variation % sprites.length;
                        E.drawSprite(sprites[v], sx, sy);
                        break;
                    }
                    case TILES.PORE: {
                        const v = variation % tileCache.pore.length;
                        E.drawSprite(tileCache.pore[v], sx, sy);

                        // Draw subtle flow indicators
                        if (flowMap[row][col] > 0 && flowSpeed[row][col] > 0.1) {
                            const flowAlpha = Math.min(0.4, flowSpeed[row][col] * 0.3);
                            const pulse = Math.sin(time * 2 + col * 0.5) * 0.15;
                            E.drawRect(sx, sy, T, T, pal.waterLight, flowAlpha + pulse);
                        }
                        break;
                    }
                    case TILES.FLOW_FAST: {
                        const v = variation % tileCache.flow.length;
                        E.drawSprite(tileCache.flow[v], sx, sy);

                        // Animated flow lines
                        const flowOffset = Math.floor(time * 8) % T;
                        for (let i = 0; i < 3; i++) {
                            const lx = (flowOffset + i * 6) % T;
                            E.drawRect(sx + lx, sy + 4 + i * 4, 3, 1, pal.waterLight, 0.5);
                        }
                        break;
                    }
                    case TILES.TOXIC: {
                        const v = variation % tileCache.toxic.length;
                        E.drawSprite(tileCache.toxic[v], sx, sy);

                        // Pulsing glow
                        const glow = Math.sin(time * 3 + col * 0.7 + row * 0.5) * 0.2 + 0.2;
                        E.drawRect(sx, sy, T, T, pal.toxicGlow, glow);

                        // Bubbles
                        if (Math.sin(time * 2 + col + row * 3) > 0.8) {
                            const bx = sx + 4 + Math.sin(time * 1.5 + col) * 3;
                            const by = sy + 2 + Math.cos(time * 2 + row) * 2;
                            E.drawSprite(PL.Sprites.toxicBubble[Math.floor(time * 2) % 2], bx, by);
                        }
                        break;
                    }
                    case TILES.BIOFILM: {
                        const v = variation % tileCache.biofilm.length;
                        E.drawSprite(tileCache.biofilm[v], sx, sy);
                        break;
                    }
                    case TILES.INLET: {
                        E.drawSprite(tileCache.inlet, sx, sy);
                        // Animated flow particles
                        const p = Math.sin(time * 4) * 0.3 + 0.5;
                        E.drawRect(sx, sy + 4, 4, 2, '#3c7ab5', p);
                        E.drawRect(sx, sy + 10, 4, 2, '#3c7ab5', 1 - p);
                        break;
                    }
                    case TILES.OUTLET: {
                        E.drawSprite(tileCache.outlet, sx, sy);
                        // Glowing exit
                        const p = Math.sin(time * 2) * 0.2 + 0.5;
                        E.drawRect(sx + 12, sy, 4, T, '#5fcf5f', p);
                        break;
                    }
                }
            }
        }
    }

    // ─── HELPERS ────────────────────────────────────────────

    function getTile(x, y) {
        if (x < 0 || x >= mapW || y < 0 || y >= mapH) return TILES.SOLID;
        return map[y][x];
    }

    function setTile(x, y, tile) {
        if (x >= 0 && x < mapW && y >= 0 && y < mapH) {
            map[y][x] = tile;
        }
    }

    function getFlow(x, y) {
        if (x < 0 || x >= mapW || y < 0 || y >= mapH) return { dir: 0, speed: 0 };
        return { dir: flowMap[y][x], speed: flowSpeed[y][x] };
    }

    function getDistance(x, y) {
        if (x < 0 || x >= mapW || y < 0 || y >= mapH) return 0;
        return distMap[y][x];
    }

    function findStartPosition() {
        // Find first inlet or leftmost pore
        for (let x = 0; x < mapW; x++) {
            for (let y = 0; y < mapH; y++) {
                if (map[y][x] === TILES.INLET) return { x, y };
            }
        }
        // Fallback
        for (let x = 1; x < mapW; x++) {
            for (let y = 1; y < mapH; y++) {
                if (isWalkable(map[y][x])) return { x, y };
            }
        }
        return { x: 1, y: 1 };
    }

    function findExitPosition() {
        for (let x = mapW - 1; x >= 0; x--) {
            for (let y = 0; y < mapH; y++) {
                if (map[y][x] === TILES.OUTLET) return { x, y };
            }
        }
        return { x: mapW - 2, y: Math.floor(mapH / 2) };
    }

    function getAdjacentPores(tx, ty) {
        const pores = [];
        const dirs = [[0,-1],[1,0],[0,1],[-1,0]];
        for (const [dx, dy] of dirs) {
            const nx = tx + dx;
            const ny = ty + dy;
            if (nx >= 0 && nx < mapW && ny >= 0 && ny < mapH) {
                const t = map[ny][nx];
                if (t === TILES.PORE || t === TILES.FLOW_FAST || t === TILES.INLET) {
                    pores.push({ x: nx, y: ny });
                }
            }
        }
        return pores;
    }

    // ─── EXPORT ─────────────────────────────────────────────
    PL.World = {
        generate,
        drawWorld,
        getTile,
        setTile,
        getFlow,
        getDistance,
        isWalkable,
        findStartPosition,
        findExitPosition,
        getAdjacentPores,
        getMapSize() { return { w: mapW, h: mapH }; },
        getWorldIdx() { return worldIdx; },
        getPalette() { return pal; }
    };
})();
