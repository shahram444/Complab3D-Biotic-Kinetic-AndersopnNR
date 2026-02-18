/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   SPRITES: Pixel art sprite renderer matching the game exactly
   ============================================================ */

const SpriteRenderer = (() => {
  const cache = {};

  /* Render sprite data array to an offscreen canvas at given scale */
  function renderSprite(data, scale) {
    const s = scale || 1;
    const h = data.length;
    const w = data[0].length;
    const can = document.createElement('canvas');
    can.width = w * s;
    can.height = h * s;
    const c = can.getContext('2d');

    for (let y = 0; y < h; y++) {
      const row = data[y];
      for (let x = 0; x < row.length; x++) {
        const ch = row[x];
        const col = PAL[ch];
        if (col) {
          c.fillStyle = col;
          c.fillRect(x * s, y * s, s, s);
        }
      }
    }
    return can;
  }

  /* Get cached sprite at given scale */
  function get(name, scale) {
    const s = scale || 4;
    const key = name + '_' + s;
    if (!cache[key]) {
      const data = SPRITES[name];
      if (!data) return null;
      cache[key] = renderSprite(data, s);
    }
    return cache[key];
  }

  /* Draw sprite onto main canvas context */
  function draw(ctx, name, x, y, scale, alpha) {
    const can = get(name, scale);
    if (!can) return;
    if (alpha !== undefined && alpha < 1) {
      ctx.globalAlpha = alpha;
    }
    ctx.drawImage(can, Math.floor(x), Math.floor(y));
    ctx.globalAlpha = 1;
  }

  /* Draw sprite centered at x,y */
  function drawCentered(ctx, name, x, y, scale, alpha) {
    const can = get(name, scale);
    if (!can) return;
    if (alpha !== undefined && alpha < 1) ctx.globalAlpha = alpha;
    ctx.drawImage(can, Math.floor(x - can.width / 2), Math.floor(y - can.height / 2));
    ctx.globalAlpha = 1;
  }

  /* Draw with glow effect */
  function drawGlow(ctx, name, x, y, scale, glowColor, glowSize, alpha) {
    const can = get(name, scale);
    if (!can) return;
    ctx.save();
    if (alpha !== undefined) ctx.globalAlpha = alpha;
    ctx.shadowColor = glowColor || '#2acfaf';
    ctx.shadowBlur = glowSize || 20;
    ctx.drawImage(can, Math.floor(x - can.width / 2), Math.floor(y - can.height / 2));
    ctx.shadowBlur = 0;
    ctx.restore();
  }

  /* Generate procedural grain tile */
  function genGrainTile(envIdx, variant, tileSize) {
    const ep = ENV_PAL[envIdx];
    const ts = tileSize || 32;
    const can = document.createElement('canvas');
    can.width = ts; can.height = ts;
    const c = can.getContext('2d');
    const pxSize = ts / 16;

    // Seeded pseudo-random
    let seed = envIdx * 1000 + (variant || 0) * 100;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };

    const colors = [ep.grain, ep.grain_l, ep.grain_d, ep.grain_a];
    const weights = [0.45, 0.25, 0.18, 0.12];

    for (let y = 0; y < 16; y++) {
      for (let x = 0; x < 16; x++) {
        let r = rng();
        let col;
        if (r < weights[0]) col = colors[0];
        else if (r < weights[0] + weights[1]) col = colors[1];
        else if (r < weights[0] + weights[1] + weights[2]) col = colors[2];
        else col = colors[3];
        c.fillStyle = col;
        c.fillRect(x * pxSize, y * pxSize, pxSize, pxSize);
      }
    }
    return can;
  }

  /* Generate procedural pore tile */
  function genPoreTile(envIdx, variant, tileSize) {
    const ep = ENV_PAL[envIdx];
    const ts = tileSize || 32;
    const can = document.createElement('canvas');
    can.width = ts; can.height = ts;
    const c = can.getContext('2d');
    const pxSize = ts / 16;

    let seed = envIdx * 1000 + (variant || 0) * 100 + 50;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };

    for (let y = 0; y < 16; y++) {
      for (let x = 0; x < 16; x++) {
        let r = rng();
        let col;
        if (r < 0.65) col = ep.pore;
        else if (r < 0.85) col = ep.pore_l;
        else col = ep.water;
        c.fillStyle = col;
        c.fillRect(x * pxSize, y * pxSize, pxSize, pxSize);
      }
    }
    return can;
  }

  /* Generate toxic tile */
  function genToxicTile(envIdx, variant, tileSize) {
    const ep = ENV_PAL[envIdx];
    const ts = tileSize || 32;
    const can = document.createElement('canvas');
    can.width = ts; can.height = ts;
    const c = can.getContext('2d');
    const pxSize = ts / 16;

    let seed = envIdx * 1000 + (variant || 0) * 100 + 90;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };

    for (let y = 0; y < 16; y++) {
      for (let x = 0; x < 16; x++) {
        let r = rng();
        let col;
        if (r < 0.4) col = ep.toxic;
        else if (r < 0.7) col = ep.toxic_g;
        else if (r < 0.85) col = ep.pore;
        else col = '#1a0a1a';
        c.fillStyle = col;
        c.fillRect(x * pxSize, y * pxSize, pxSize, pxSize);
      }
    }
    return can;
  }

  /* Generate biofilm tile */
  function genBiofilmTile(tileSize) {
    const ts = tileSize || 32;
    const can = document.createElement('canvas');
    can.width = ts; can.height = ts;
    const c = can.getContext('2d');
    const pxSize = ts / 16;

    let seed = 12345;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };
    const colors = ['#2a5a4a', '#3a7a5a', '#1a4a3a'];

    for (let y = 0; y < 16; y++) {
      for (let x = 0; x < 16; x++) {
        c.fillStyle = colors[Math.floor(rng() * 3)];
        c.fillRect(x * pxSize, y * pxSize, pxSize, pxSize);
      }
    }
    return can;
  }

  /* Generate a complete pore-scale landscape (for wide shots) */
  function genLandscape(envIdx, cols, rows, porosity) {
    const ep = ENV_PAL[envIdx];
    const ts = 32;
    const can = document.createElement('canvas');
    can.width = cols * ts;
    can.height = rows * ts;
    const c = can.getContext('2d');

    // Fill background
    c.fillStyle = ep.bg;
    c.fillRect(0, 0, can.width, can.height);

    // Generate tile grid
    let seed = envIdx * 7777 + cols * 13;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed & 0x7fffffff) / 0x7fffffff; };
    const por = porosity || 0.6;

    const grid = [];
    for (let r = 0; r < rows; r++) {
      grid[r] = [];
      for (let col = 0; col < cols; col++) {
        // Edges are solid
        if (r === 0 || r === rows - 1 || col === 0 || col === cols - 1) {
          grid[r][col] = 'solid';
        } else {
          grid[r][col] = rng() < por ? 'pore' : 'solid';
        }
      }
    }

    // Smooth: remove isolated solids/pores
    for (let pass = 0; pass < 2; pass++) {
      for (let r = 1; r < rows - 1; r++) {
        for (let col = 1; col < cols - 1; col++) {
          let neighbors = 0;
          for (let dr = -1; dr <= 1; dr++) {
            for (let dc = -1; dc <= 1; dc++) {
              if (dr === 0 && dc === 0) continue;
              if (grid[r + dr][col + dc] === 'solid') neighbors++;
            }
          }
          if (grid[r][col] === 'solid' && neighbors < 2) grid[r][col] = 'pore';
          if (grid[r][col] === 'pore' && neighbors > 6) grid[r][col] = 'solid';
        }
      }
    }

    // Draw tiles
    const grainTiles = [];
    for (let v = 0; v < 4; v++) grainTiles.push(genGrainTile(envIdx, v, ts));
    const poreTiles = [];
    for (let v = 0; v < 4; v++) poreTiles.push(genPoreTile(envIdx, v, ts));

    for (let r = 0; r < rows; r++) {
      for (let col = 0; col < cols; col++) {
        const tile = grid[r][col] === 'solid'
          ? grainTiles[Math.floor(rng() * 4)]
          : poreTiles[Math.floor(rng() * 4)];
        c.drawImage(tile, col * ts, r * ts);
      }
    }

    return { canvas: can, grid };
  }

  return {
    renderSprite, get, draw, drawCentered, drawGlow,
    genGrainTile, genPoreTile, genToxicTile, genBiofilmTile, genLandscape
  };
})();
