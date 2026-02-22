#!/usr/bin/env python3
"""Generate pixel-perfect SVG renderings of actual game sprites for the manual.
Reads sprite data from sprite_factory.gd and ENV_PAL from game_data.gd,
outputs SVG code that can be pasted into manual HTML sections."""

import json, sys, math, random

# ── PALETTE (from sprite_factory.gd) ────────────────────────────────────────
PAL = {
    ".": None,           # transparent
    "k": "#000000",      # black (outline)
    "w": "#ffffff",      # white
    "W": "#cccccc",      # light gray
    "a": "#888888",      # gray
    "A": "#444444",      # dark gray
    "t": "#1a8a7a",      # body teal
    "T": "#2acfaf",      # highlight teal
    "L": "#5fffdf",      # bright glow
    "d": "#0a5a4a",      # dark teal
    "D": "#084038",      # darker teal
    "b": "#7a5a2a",      # brown
    "B": "#a48a5a",      # light brown
    "n": "#4a3a1a",      # dark brown
    "N": "#c4a060",      # tan
    "u": "#1a3a60",      # blue
    "U": "#3060a0",      # light blue
    "c": "#50b0c0",      # cyan
    "C": "#80d0e0",      # light cyan
    "o": "#ef8f3f",      # orange (Fe)
    "O": "#ffbf7f",      # light orange
    "y": "#dfdf3f",      # yellow (SO4)
    "Y": "#ffffaf",      # light yellow
    "r": "#ff4f4f",      # red (CH4)
    "R": "#ff9f7f",      # light red
    "g": "#4fdf6f",      # green (NO3)
    "G": "#8fff9f",      # light green
    "p": "#cf6fff",      # purple (Mn)
    "P": "#df9fff",      # light purple
    "i": "#4fa4ff",      # info blue (O2)
    "I": "#8fc8ff",      # light info blue
    "V": "#40c8d8",      # visor cyan
    "H": "#7888a0",      # helmet rim gray
    "X": "#90e8f0",      # visor shine
    "e": "#1a1a2e",      # pupil
    "s": "#ffff5f",      # glow/ready
    "h": "#ff6644",      # hurt
    "m": "#0a6a5a",      # mouth
    "f": "#3a7a5a",      # biofilm
    "F": "#5aaa7a",      # biofilm light
    "v": "#2a5a4a",      # biofilm dark
    "j": "#1a1aa0",      # elder body dark blue
    "J": "#4848d0",      # elder body blue highlight
    "q": "#5030a0",      # elder lower purple
    "Q": "#7050c0",      # elder purple highlight
    "z": "#b03030",      # rival body dark
    "Z": "#e06060",      # rival body light
}

# ── SPRITE DATA (from sprite_factory.gd) ────────────────────────────────────

METHI_DOWN = [
    "....kHHHHHk.....",
    "...kHHHHHHHk....",
    "..kHVVVVVVVHk...",
    "..kVXXVVVXXVk...",
    "..kVXwwVwwXVk...",
    "..kVVwekweVVk...",
    "..kHVVVVVVVHk...",
    "..kkHHkkkHHkk...",
    "..kTTTTTTTTTk...",
    "..kTTTTTTTTTk...",
    "..kTtTTTTTtTk...",
    "...ktTTTTTtk....",
    "....ktttttkk....",
    ".....kkkkk......",
    "......k.k.......",
    "................",
]

METHI_UP = [
    "....kHHHHHk.....",
    "...kHHHHHHHk....",
    "..kHHHHHHHHHk...",
    "..kHHHHHHHHHk...",
    "..kHHHHHHHHHk...",
    "..kHHHHHHHHHk...",
    "..kHHHHHHHHHk...",
    "..kkHHkkkHHkk...",
    "..kTTTTTTTTTk...",
    "..kTTTTTTTTTk...",
    "..kTtTTTTTtTk...",
    "...ktTTTTTtk....",
    "....ktttttkk....",
    ".....kkkkk......",
    "................",
    "................",
]

METHI_LEFT = [
    "................",
    "...kHHHHHk......",
    "..kHVVVVVHk.....",
    "..kVXXVVVVk.....",
    ".kkVXweVVVk.....",
    ".kHVVVVVVHk.....",
    ".kkHHkkHHkk.....",
    ".kTTTTTTTTk.....",
    "..kTTTTTTTk.....",
    "..kTtTTTtTk.....",
    "...ktTTTtk......",
    "....kttttk......",
    ".....kkkk.......",
    "......k.........",
    "................",
    "................",
]

METHI_RIGHT = [
    "................",
    "......kHHHHHk...",
    ".....kHVVVVVHk..",
    ".....kVVVVXXVk..",
    ".....kVVVewXVkk.",
    ".....kHVVVVVHk..",
    ".....kkHHkkHHkk.",
    ".....kTTTTTTTk..",
    ".....kTTTTTTk...",
    ".....kTtTTtTk...",
    "......ktTTtk....",
    "......kttttk....",
    ".......kkkk.....",
    ".........k......",
    "................",
    "................",
]

METHI_EAT = [
    "....kHHHHHk.....",
    "...kHHHHHHHk....",
    "..kHVVVVVVVHk...",
    "..kVXXVVVXXVk...",
    "..kVXwwVwwXVk...",
    "..kVVwekweVVk...",
    "..kHVVkkkVVHk...",
    "..kkHkssskHkk...",
    "..kTTTkkkTTTk...",
    "..kTTTTTTTTTk...",
    "..kTtTTTTTtTk...",
    "...ktTTTTTtk....",
    "....ktttttkk....",
    ".....kkkkk......",
    "................",
    "................",
]

METHI_GLOW = [
    "...skHHHHHks....",
    "..skHHHHHHHks...",
    ".skHVVVVVVVHks..",
    ".skVXXVVVXXVks..",
    ".skVXwwVwwXVks..",
    ".skVVwekweVVks..",
    ".skHVVVVVVVHks..",
    ".skkHHkkkHHkks..",
    ".skLTTTTTTTLks..",
    ".skLTTTTTTTLks..",
    "..skLtTTTtLks...",
    "...skLTTTLks....",
    "....skkkkks.....",
    ".....ssssss.....",
    "................",
    "................",
]

METHI_HURT = [
    "....kHHHHHk.....",
    "...kHHHHHHHk....",
    "..kHhhhhhhhHk...",
    "..khhkkkhkkhk...",
    "..khhhhhhhhhk...",
    "..khhhhhhhhhk...",
    "..kHhhhhhhhHk...",
    "..kkHHkkkHHkk...",
    "..khhhhhhhhhk...",
    "..khhhhhhhhhk...",
    "..khhhhhhhhhk...",
    "...khhhhhhhhk...",
    "....khhhhhhk....",
    ".....kkkkkk.....",
    "................",
    "................",
]

METHI_DIE = [
    "................",
    "................",
    ".....kkkkkk.....",
    "....kaHHHHak....",
    "...kaHaaaHaak...",
    "...kaaaaaaaaak..",
    "..kaaaaaaaaaaak.",
    "..kaaaaaaaaaaak.",
    "...kaaaaaaaak...",
    "....kaaaaaak....",
    ".....kaaaak.....",
    "......kkkk......",
    "................",
    "................",
    "................",
    "................",
]

ELDER = [
    "....kkkkkk......",
    "...kjjjjjjk.....",
    "..kjJjjjjJjk....",
    ".kjJwwjjwwJjk...",
    ".kjjwejjewjjk...",
    ".kjjjjjjjjjjk...",
    ".kjjjjmjjjjjk...",
    "..kjjjjjjjjk....",
    "..kkjjjjjjkk....",
    ".kqqkjjjjkqqk...",
    ".kqqqjjjjqqqk...",
    "..kqqqqqqqqk....",
    "...kqqqqqqk.....",
    "....kkkkkk......",
    "......k.k.......",
    "................",
]

RIVAL_BASE = [
    "...kkkk...",
    "..kzZZzk..",
    ".kzwZwZzk.",
    ".kzeZeZzk.",
    ".kzZZZZzk.",
    ".kzZmZZzk.",
    "..kzZZzk..",
    "...kzzk...",
    "....kk....",
    "..........",
]

COLONY = [
    "...kkkkkk...",
    "..kfFFFFFk..",
    ".kfFFFFFFfk.",
    "kfFFFFFFFFFk",
    "kFFFFFFFFFFk",
    "kFFFFFFFFFFk",
    "kFFFFFFFFFFk",
    "kfFFFFFFFfFk",
    ".kfFFFFFFfk.",
    "..kvFFFfvk..",
    "...kkkkkk...",
    "............",
]

SUB_O2 = [
    "..kkkkkk..",
    ".kiiiiiik.",
    "kiIIIIIIik",
    "kiIIIIIIik",
    "kiIIIIIIik",
    "kiIIIIIIik",
    "kiIIIIIIik",
    "kiiiiiiiik",
    ".kiiiiik..",
    "..kkkkkk..",
]

SUB_NO3 = [
    "....kk....",
    "...kGGk...",
    "..kGGGGk..",
    ".kGGGGGGk.",
    "kGGGGGGGGk",
    "kGGGGGGGGk",
    ".kGGGGGGk.",
    "..kGGGGk..",
    "...kGGk...",
    "....kk....",
]

SUB_MN4 = [
    "....kk....",
    "...kPPk...",
    "..kPPPPk..",
    "kkPPPPPPkk",
    "kPPPPPPPPk",
    "kPPPPPPPPk",
    "kkPPPPPPkk",
    "..kPPPPk..",
    "...kPPk...",
    "....kk....",
]

SUB_FE3 = [
    "....kk....",
    "...kook...",
    "..koOOok..",
    ".koOOOOok.",
    "koOOOOOOok",
    "koOOOOOOok",
    ".koOOOOok.",
    "..koOOok..",
    "...kook...",
    "....kk....",
]

SUB_SO4 = [
    "...kkkk...",
    "..kYYYYk..",
    ".kYYYYYYk.",
    "kYYYYYYYYk",
    "kYYYYYYYYk",
    "kYYYYYYYYk",
    "kYYYYYYYYk",
    ".kYYYYYYk.",
    "..kYYYYk..",
    "...kkkk...",
]

SUB_CH4 = [
    "....kk....",
    "...kRRk...",
    "..kRrrRk..",
    ".kRrrrrRk.",
    ".kRrrrRRk.",
    "kRRrrRRRRk",
    "kRRRRRRRRk",
    ".kRRRRRRk.",
    "..kRRRRk..",
    "...kkkk...",
]

# ── ENV_PAL (from game_data.gd) ────────────────────────────────────────────
ENV_PAL = [
    # 0: Soil Frontier
    {"name": "The Soil Frontier",
     "grain": "#7a5a2a", "grain_l": "#a48a5a", "grain_d": "#4a3a1a", "grain_a": "#c4a060",
     "pore": "#0c1420", "pore_l": "#142030", "water": "#1a3a60", "water_l": "#3060a0",
     "bg": "#060c18", "toxic": "#8a3a8a", "toxic_g": "#c060c0"},
    # 1: Deep Sediment
    {"name": "The Deep Sediment",
     "grain": "#4a3a2a", "grain_l": "#6a5a4a", "grain_d": "#2a1a0a", "grain_a": "#5a4a3a",
     "pore": "#060608", "pore_l": "#0c0c14", "water": "#0a1428", "water_l": "#142038",
     "bg": "#030306", "toxic": "#6a2a2a", "toxic_g": "#a04040"},
    # 2: Methane Seeps
    {"name": "The Methane Seeps",
     "grain": "#3a3040", "grain_l": "#5a5060", "grain_d": "#2a2030", "grain_a": "#4a4050",
     "pore": "#0a0610", "pore_l": "#140c1c", "water": "#1a1438", "water_l": "#2a1a48",
     "bg": "#06040a", "toxic": "#7a1a6a", "toxic_g": "#b040a0"},
    # 3: Permafrost Edge
    {"name": "The Permafrost Edge",
     "grain": "#5a6a7a", "grain_l": "#8a9aaa", "grain_d": "#3a4a5a", "grain_a": "#aabaca",
     "pore": "#080c14", "pore_l": "#0c1420", "water": "#1a3050", "water_l": "#3a5a8a",
     "bg": "#040810", "toxic": "#4a7a3a", "toxic_g": "#70b050"},
    # 4: Hydrothermal Realm
    {"name": "The Hydrothermal Realm",
     "grain": "#2a2a3a", "grain_l": "#4a4a5a", "grain_d": "#1a1a2a", "grain_a": "#3a3a4a",
     "pore": "#0a0608", "pore_l": "#14080c", "water": "#281418", "water_l": "#3a1a20",
     "bg": "#060304", "toxic": "#8a4a1a", "toxic_g": "#c07030"},
]


def sprite_to_svg(sprite_data, pixel_size, svg_w=None, svg_h=None, bg_color=None):
    """Convert a sprite (list of strings) to an SVG string with pixel-perfect rendering."""
    rows = len(sprite_data)
    cols = max(len(row) for row in sprite_data) if rows > 0 else 0

    if svg_w is None:
        svg_w = cols * pixel_size
    if svg_h is None:
        svg_h = rows * pixel_size

    parts = []
    parts.append(f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {cols * pixel_size} {rows * pixel_size}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated;">')

    if bg_color:
        parts.append(f'  <rect width="{cols * pixel_size}" height="{rows * pixel_size}" fill="{bg_color}"/>')

    for y, row in enumerate(sprite_data):
        for x, ch in enumerate(row):
            color = PAL.get(ch)
            if color:
                px = x * pixel_size
                py = y * pixel_size
                parts.append(f'  <rect x="{px}" y="{py}" width="{pixel_size}" height="{pixel_size}" fill="{color}"/>')

    parts.append('</svg>')
    return '\n'.join(parts)


def gen_world_tile_grid(env_idx, grid_w=20, grid_h=12, tile_size=10,
                        seed_val=42, porosity=0.6, has_toxic=False,
                        has_vents=False, is_maze=False, is_layered=False,
                        show_arke=True, show_substrates=True, sub_types=None,
                        show_rivals=0, show_inlet_outlet=True):
    """Generate a tile-grid SVG that looks like an actual game screenshot,
    using the real ENV_PAL colors."""
    ep = ENV_PAL[env_idx]
    rng = random.Random(seed_val + env_idx * 1000)

    # Generate tile map
    # 0=solid, 1=pore, 2=toxic, 3=flow_fast, 4=inlet, 5=outlet
    tiles = [[0]*grid_w for _ in range(grid_h)]

    if is_maze:
        # Maze-like generation (Deep Sediment)
        # Start all solid, carve corridors
        for y in range(grid_h):
            for x in range(grid_w):
                tiles[y][x] = 0
        # Carve main corridors
        cy = grid_h // 2
        for x in range(1, grid_w - 1):
            tiles[cy][x] = 1
            if x > 0 and rng.random() < 0.3:
                cy = max(1, min(grid_h - 2, cy + rng.choice([-1, 1])))
                tiles[cy][x] = 1
        # Add branches
        for _ in range(8):
            sx = rng.randint(2, grid_w - 3)
            sy = rng.randint(1, grid_h - 2)
            tiles[sy][sx] = 1
            length = rng.randint(2, 5)
            d = rng.choice([(0,1),(0,-1),(1,0)])
            for s in range(length):
                ny, nx = sy + d[1]*s, sx + d[0]*s
                if 1 <= ny < grid_h-1 and 1 <= nx < grid_w-1:
                    tiles[ny][nx] = 1
    elif is_layered:
        # Permafrost - horizontal layers
        for y in range(grid_h):
            for x in range(grid_w):
                tiles[y][x] = 0
        # Create horizontal channels
        for layer_y in [2, 5, 8]:
            for x in range(grid_w):
                for dy in range(-1, 2):
                    ny = layer_y + dy
                    if 0 < ny < grid_h - 1:
                        tiles[ny][x] = 3  # fast flow
        # Vertical connectors
        for vx in [4, 10, 15]:
            sy = rng.randint(1, 3)
            for y in range(sy, min(sy + 4, grid_h - 1)):
                tiles[y][vx] = 1
    else:
        # Circle-packing (Soil, Methane, Hydrothermal)
        # Start with pores
        for y in range(grid_h):
            for x in range(grid_w):
                tiles[y][x] = 1
        # Place grain circles
        num_grains = int(grid_w * grid_h * (1.0 - porosity) / 4.0)
        for _ in range(num_grains):
            gx = rng.randint(1, grid_w - 2)
            gy = rng.randint(1, grid_h - 2)
            r = rng.choice([1, 1, 2])
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r*r:
                        tx, ty = gx + dx, gy + dy
                        if 0 <= tx < grid_w and 0 <= ty < grid_h:
                            tiles[ty][tx] = 0

    # Add vent channels (Methane Seeps, Hydrothermal)
    if has_vents:
        for vx in [rng.randint(5, 8), rng.randint(12, 16)]:
            for y in range(2, grid_h):
                if 0 <= vx < grid_w:
                    tiles[y][vx] = 1

    # Borders
    for x in range(grid_w):
        tiles[0][x] = 0
        tiles[grid_h-1][x] = 0
    for y in range(grid_h):
        tiles[y][0] = 0
        tiles[y][grid_w-1] = 0

    # Add toxic zones
    if has_toxic:
        toxic_count = 0
        target = int(grid_w * grid_h * 0.15)
        for _ in range(5):
            tx = rng.randint(3, grid_w - 4)
            ty = rng.randint(2, grid_h - 3)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = tx + dx, ty + dy
                    if 0 < nx < grid_w - 1 and 0 < ny < grid_h - 1:
                        if tiles[ny][nx] == 1:
                            tiles[ny][nx] = 2
                            toxic_count += 1

    # Inlet/Outlet
    if show_inlet_outlet:
        for y in range(1, grid_h - 1):
            if tiles[y][1] == 1 or tiles[y][1] == 3:
                tiles[y][1] = 4
                break
        for y in range(1, grid_h - 1):
            if tiles[y][grid_w - 2] == 1 or tiles[y][grid_w - 2] == 3:
                tiles[y][grid_w - 2] = 5
                break

    # Render SVG
    svg_w = grid_w * tile_size
    svg_h = grid_h * tile_size
    parts = []
    parts.append(f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated;">')

    # Background
    parts.append(f'  <rect width="{svg_w}" height="{svg_h}" fill="{ep["bg"]}"/>')

    grain_colors = [ep["grain"], ep["grain_l"], ep["grain_d"], ep["grain_a"]]
    pore_colors = [ep["pore"], ep["pore_l"]]

    for y in range(grid_h):
        for x in range(grid_w):
            px = x * tile_size
            py = y * tile_size
            tile = tiles[y][x]
            v = (x * 7 + y * 13) % 4

            if tile == 0:  # Solid/grain
                col = grain_colors[v % len(grain_colors)]
                parts.append(f'  <rect x="{px}" y="{py}" width="{tile_size}" height="{tile_size}" fill="{col}"/>')
            elif tile == 1:  # Pore
                col = pore_colors[v % 2]
                parts.append(f'  <rect x="{px}" y="{py}" width="{tile_size}" height="{tile_size}" fill="{col}"/>')
            elif tile == 2:  # Toxic
                parts.append(f'  <rect x="{px}" y="{py}" width="{tile_size}" height="{tile_size}" fill="{ep["toxic"]}"/>')
                parts.append(f'  <rect x="{px+1}" y="{py+1}" width="{tile_size-2}" height="{tile_size-2}" fill="{ep["toxic_g"]}" opacity="0.4"/>')
            elif tile == 3:  # Fast flow
                col = ep["water"]
                parts.append(f'  <rect x="{px}" y="{py}" width="{tile_size}" height="{tile_size}" fill="{col}"/>')
                # Flow line
                parts.append(f'  <rect x="{px+2}" y="{py + tile_size//2}" width="{tile_size-4}" height="1" fill="{ep["water_l"]}" opacity="0.5"/>')
            elif tile == 4:  # Inlet
                parts.append(f'  <rect x="{px}" y="{py}" width="{tile_size}" height="{tile_size}" fill="{pore_colors[0]}"/>')
                parts.append(f'  <rect x="{px}" y="{py}" width="3" height="{tile_size}" fill="#3060a0" opacity="0.7"/>')
            elif tile == 5:  # Outlet
                parts.append(f'  <rect x="{px}" y="{py}" width="{tile_size}" height="{tile_size}" fill="{pore_colors[0]}"/>')
                parts.append(f'  <rect x="{px+tile_size-3}" y="{py}" width="3" height="{tile_size}" fill="#4fdf6f" opacity="0.7"/>')

    # Add ARKE sprite (small, 3x3 pixels at tile_size)
    if show_arke:
        # Find a pore tile near the inlet
        arke_x, arke_y = 2, grid_h // 2
        for y in range(1, grid_h - 1):
            for x in range(1, 5):
                if tiles[y][x] in (1, 3, 4):
                    arke_x, arke_y = x, y
                    break
            if tiles[arke_y][arke_x] in (1, 3, 4):
                break
        ax, ay = arke_x * tile_size, arke_y * tile_size
        # Mini ARKE: helmet + visor + body
        ts = tile_size
        parts.append(f'  <rect x="{ax+1}" y="{ay}" width="{ts-2}" height="{ts//3}" fill="#7888a0"/>')  # helmet
        parts.append(f'  <rect x="{ax+2}" y="{ay+1}" width="{ts-4}" height="{ts//3-1}" fill="#40c8d8"/>')  # visor
        parts.append(f'  <rect x="{ax+1}" y="{ay+ts//3}" width="{ts-2}" height="{ts*2//3}" fill="#2acfaf"/>')  # body
        parts.append(f'  <rect x="{ax}" y="{ay}" width="{ts}" height="{ts}" fill="none" stroke="#000" stroke-width="0.5"/>')

    # Add substrate orbs
    if show_substrates and sub_types:
        sub_colors = {
            "O2": "#4fa4ff", "NO3": "#4fdf6f", "Mn": "#cf6fff",
            "Fe": "#ef8f3f", "SO4": "#dfdf3f", "CH4": "#ff4f4f"
        }
        placed = 0
        for y in range(2, grid_h - 2):
            for x in range(3, grid_w - 3, 4):
                if tiles[y][x] in (1, 3) and placed < len(sub_types):
                    st = sub_types[placed % len(sub_types)]
                    col = sub_colors.get(st, "#ffffff")
                    cx = x * tile_size + tile_size // 2
                    cy_pos = y * tile_size + tile_size // 2
                    r = tile_size // 3
                    parts.append(f'  <circle cx="{cx}" cy="{cy_pos}" r="{r}" fill="{col}" opacity="0.85"/>')
                    parts.append(f'  <circle cx="{cx-1}" cy="{cy_pos-1}" r="{max(1,r//3)}" fill="white" opacity="0.4"/>')
                    placed += 1

    # Add rival microbes
    for ri in range(show_rivals):
        rx = rng.randint(grid_w // 3, grid_w - 3)
        ry = rng.randint(1, grid_h - 2)
        if tiles[ry][rx] in (1, 3):
            rpx = rx * tile_size
            rpy = ry * tile_size
            ts = tile_size
            parts.append(f'  <rect x="{rpx+1}" y="{rpy+1}" width="{ts-2}" height="{ts-2}" fill="#b03030" rx="1"/>')
            parts.append(f'  <rect x="{rpx+2}" y="{rpy+2}" width="{ts//3}" height="{ts//4}" fill="#e06060"/>')
            parts.append(f'  <rect x="{rpx}" y="{rpy}" width="{ts}" height="{ts}" fill="none" stroke="#000" stroke-width="0.5"/>')

    parts.append('</svg>')
    return '\n'.join(parts)


# ── GENERATE ALL ────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("SPRITE SVGs")
    print("=" * 80)

    # Character sprites at various sizes
    sprites = {
        "methi_down_large": (METHI_DOWN, 12, 192, 192),   # Main portrait
        "methi_up": (METHI_UP, 5, 80, 80),
        "methi_down": (METHI_DOWN, 5, 80, 80),
        "methi_left": (METHI_LEFT, 5, 80, 80),
        "methi_right": (METHI_RIGHT, 5, 80, 80),
        "methi_eat": (METHI_EAT, 5, 80, 80),
        "methi_glow": (METHI_GLOW, 5, 80, 80),
        "methi_hurt": (METHI_HURT, 5, 80, 80),
        "methi_die": (METHI_DIE, 5, 80, 80),
        "elder_large": (ELDER, 8, 128, 128),
        "rival_large": (RIVAL_BASE, 15, 150, 150),
        "colony_large": (COLONY, 10, 120, 120),
        "sub_o2": (SUB_O2, 6, 60, 60),
        "sub_no3": (SUB_NO3, 6, 60, 60),
        "sub_mn4": (SUB_MN4, 6, 60, 60),
        "sub_fe3": (SUB_FE3, 6, 60, 60),
        "sub_so4": (SUB_SO4, 6, 60, 60),
        "sub_ch4": (SUB_CH4, 6, 60, 60),
    }

    for name, (data, px, w, h) in sprites.items():
        print(f"\n--- {name} ---")
        svg = sprite_to_svg(data, px, w, h)
        print(svg)

    print("\n" + "=" * 80)
    print("WORLD TILE GRIDS")
    print("=" * 80)

    # World 1: Soil Frontier
    print("\n--- world_soil ---")
    print(gen_world_tile_grid(0, grid_w=20, grid_h=12, tile_size=10, seed_val=42,
                              porosity=0.65, sub_types=["O2","NO3","CH4"]))

    # World 2: Deep Sediment
    print("\n--- world_deep ---")
    print(gen_world_tile_grid(1, grid_w=20, grid_h=12, tile_size=10, seed_val=55,
                              porosity=0.50, is_maze=True,
                              sub_types=["NO3","Fe","CH4"], show_rivals=2))

    # World 3: Methane Seeps
    print("\n--- world_methane ---")
    print(gen_world_tile_grid(2, grid_w=20, grid_h=12, tile_size=10, seed_val=77,
                              porosity=0.58, has_toxic=True, has_vents=True,
                              sub_types=["SO4","CH4","Fe"], show_rivals=2))

    # World 4: Permafrost
    print("\n--- world_permafrost ---")
    print(gen_world_tile_grid(3, grid_w=20, grid_h=12, tile_size=10, seed_val=88,
                              is_layered=True, has_toxic=True,
                              sub_types=["O2","NO3","CH4"], show_rivals=3))

    # World 5: Hydrothermal
    print("\n--- world_hydrothermal ---")
    print(gen_world_tile_grid(4, grid_w=20, grid_h=12, tile_size=10, seed_val=99,
                              porosity=0.50, has_toxic=True, has_vents=True,
                              sub_types=["SO4","Fe","Mn","CH4"], show_rivals=4))

    # Level-specific tile grids (300x100 viewbox to match existing level-map containers)
    print("\n" + "=" * 80)
    print("LEVEL TILE GRIDS")
    print("=" * 80)

    level_configs = [
        # Lv1: First Breath - Soil, open, no rivals
        {"env": 0, "w": 30, "h": 10, "ts": 10, "seed": 101, "por": 0.70,
         "subs": ["O2","NO3","CH4"], "rivals": 0, "name": "level_1"},
        # Lv2: Roots of Life - Soil, 1 rival
        {"env": 0, "w": 30, "h": 10, "ts": 10, "seed": 102, "por": 0.65,
         "subs": ["O2","NO3","CH4"], "rivals": 1, "name": "level_2"},
        # Lv3: Into the Depths - Deep, maze, 2 rivals
        {"env": 1, "w": 30, "h": 10, "ts": 10, "seed": 103, "por": 0.50,
         "subs": ["NO3","Fe","CH4"], "rivals": 2, "maze": True, "name": "level_3"},
        # Lv4: The Hungry Dark - Deep, tight maze, 3 rivals
        {"env": 1, "w": 30, "h": 10, "ts": 10, "seed": 104, "por": 0.45,
         "subs": ["NO3","Mn","Fe","CH4"], "rivals": 3, "maze": True, "name": "level_4"},
        # Lv5: The Methane Vents - Methane, toxic, vents, 2 rivals
        {"env": 2, "w": 30, "h": 10, "ts": 10, "seed": 105, "por": 0.58,
         "subs": ["SO4","CH4"], "rivals": 2, "toxic": True, "vents": True, "name": "level_5"},
        # Lv6: Vent Guardians - Methane, more toxic, 3 rivals
        {"env": 2, "w": 30, "h": 10, "ts": 10, "seed": 106, "por": 0.55,
         "subs": ["SO4","CH4","Fe"], "rivals": 3, "toxic": True, "vents": True, "name": "level_6"},
        # Lv7: Thawing Grounds - Permafrost, layered, 3 rivals
        {"env": 3, "w": 30, "h": 10, "ts": 10, "seed": 107, "por": 0.55,
         "subs": ["O2","NO3","CH4"], "rivals": 3, "layered": True, "toxic": True, "name": "level_7"},
        # Lv8: The Great Thaw - Permafrost, fast, 4 rivals
        {"env": 3, "w": 30, "h": 10, "ts": 10, "seed": 108, "por": 0.50,
         "subs": ["NO3","SO4","CH4"], "rivals": 4, "layered": True, "toxic": True, "name": "level_8"},
        # Lv9: The Abyss - Hydrothermal, chambers, 4 rivals
        {"env": 4, "w": 30, "h": 10, "ts": 10, "seed": 109, "por": 0.50,
         "subs": ["SO4","Fe","Mn","CH4"], "rivals": 4, "toxic": True, "vents": True, "name": "level_9"},
        # Lv10: Earth's Last Stand - Hydrothermal, extreme, 5 rivals
        {"env": 4, "w": 30, "h": 10, "ts": 10, "seed": 110, "por": 0.45,
         "subs": ["SO4","Fe","Mn","CH4","NO3"], "rivals": 5, "toxic": True, "vents": True, "name": "level_10"},
    ]

    for lc in level_configs:
        print(f"\n--- {lc['name']} ---")
        print(gen_world_tile_grid(
            lc["env"], grid_w=lc["w"], grid_h=lc["h"], tile_size=lc["ts"],
            seed_val=lc["seed"], porosity=lc.get("por", 0.6),
            has_toxic=lc.get("toxic", False), has_vents=lc.get("vents", False),
            is_maze=lc.get("maze", False), is_layered=lc.get("layered", False),
            sub_types=lc["subs"], show_rivals=lc["rivals"]
        ))


if __name__ == "__main__":
    main()
