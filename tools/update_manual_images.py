#!/usr/bin/env python3
"""
Update game manual HTML sections to use pixel-perfect renderings of actual
game sprites instead of organic/arbitrary SVG illustrations.

Like the Mario manual: same pixel art from the game, rendered at high resolution.
"""

import sys, os, random, math

# ── PALETTE ─────────────────────────────────────────────────────────────────
PAL = {
    ".": None, "k": "#000000", "w": "#ffffff", "W": "#cccccc",
    "a": "#888888", "A": "#444444",
    "t": "#1a8a7a", "T": "#2acfaf", "L": "#5fffdf", "d": "#0a5a4a", "D": "#084038",
    "b": "#7a5a2a", "B": "#a48a5a", "n": "#4a3a1a", "N": "#c4a060",
    "u": "#1a3a60", "U": "#3060a0", "c": "#50b0c0", "C": "#80d0e0",
    "o": "#ef8f3f", "O": "#ffbf7f", "y": "#dfdf3f", "Y": "#ffffaf",
    "r": "#ff4f4f", "R": "#ff9f7f", "g": "#4fdf6f", "G": "#8fff9f",
    "p": "#cf6fff", "P": "#df9fff", "i": "#4fa4ff", "I": "#8fc8ff",
    "V": "#40c8d8", "H": "#7888a0", "X": "#90e8f0", "e": "#1a1a2e",
    "s": "#ffff5f", "h": "#ff6644", "m": "#0a6a5a",
    "f": "#3a7a5a", "F": "#5aaa7a", "v": "#2a5a4a",
    "j": "#1a1aa0", "J": "#4848d0", "q": "#5030a0", "Q": "#7050c0",
    "z": "#b03030", "Z": "#e06060",
}

# ── SPRITES ─────────────────────────────────────────────────────────────────
METHI_DOWN = ["....kHHHHHk.....","...kHHHHHHHk....","..kHVVVVVVVHk...","..kVXXVVVXXVk...","..kVXwwVwwXVk...","..kVVwekweVVk...","..kHVVVVVVVHk...","..kkHHkkkHHkk...","..kTTTTTTTTTk...","..kTTTTTTTTTk...","..kTtTTTTTtTk...","...ktTTTTTtk....","....ktttttkk....","....kkkkkkk.....","......k.k.......","................"]
METHI_UP = ["....kHHHHHk.....","...kHHHHHHHk....","..kHHHHHHHHHk...","..kHHHHHHHHHk...","..kHHHHHHHHHk...","..kHHHHHHHHHk...","..kHHHHHHHHHk...","..kkHHkkkHHkk...","..kTTTTTTTTTk...","..kTTTTTTTTTk...","..kTtTTTTTtTk...","...ktTTTTTtk....","....ktttttkk....","....kkkkkkk.....","................","................"]
METHI_LEFT = ["................","...kHHHHHk......","..kHVVVVVHk.....","..kVXXVVVVk.....","kkVXweVVVk.....","kHVVVVVVHk.....","kkHHkkHHkk.....","kTTTTTTTTk.....","..kTTTTTTTk.....","..kTtTTTtTk.....","...ktTTTtk......","....kttttk......",".....kkkk.......","......k.........","................","................"]
METHI_RIGHT = ["................","......kHHHHHk...","....kHVVVVVHk..","....kVVVVXXVk..","....kVVVewXVkk.","....kHVVVVVHk..","....kkHHkkHHkk.","....kTTTTTTTk..","....kTTTTTTk...","....kTtTTtTk...","......ktTTtk....","......kttttk....",".......kkkk.....","........k.......","................","................"]
METHI_EAT = ["....kHHHHHk.....","...kHHHHHHHk....","..kHVVVVVVVHk...","..kVXXVVVXXVk...","..kVXwwVwwXVk...","..kVVwekweVVk...","..kHVVkkkVVHk...","..kkHkssskHkk...","..kTTTkkkTTTk...","..kTTTTTTTTTk...","..kTtTTTTTtTk...","...ktTTTTTtk....","....ktttttkk....","....kkkkkkk.....","................","................"]
METHI_GLOW = ["...skHHHHHks....","..skHHHHHHHks...","skHVVVVVVVHks..",".skVXXVVVXXVks..",".skVXwwVwwXVks..",".skVVwekweVVks..",".skHVVVVVVVHks..",".skkHHkkkHHkks..",".skLTTTTTTTLks..",".skLTTTTTTTLks..","..skLtTTTtLks...","...skLTTTLks....","....skkkkks.....","....sssssss.....","................","................"]
METHI_HURT = ["....kHHHHHk.....","...kHHHHHHHk....","..kHhhhhhhhHk...","..khhkkkhkkhk...","..khhhhhhhhhk...","..khhhhhhhhhk...","..kHhhhhhhhHk...","..kkHHkkkHHkk...","..khhhhhhhhhk...","..khhhhhhhhhk...","..khhhhhhhhhk...","...khhhhhhhhk...","....khhhhhhk....","....kkkkkkk.....","................","................"]
METHI_DIE = ["................","................",".....kkkkkk.....","....kaHHHHak....","...kaHaaaHaak...","...kaaaaaaaaak..","..kaaaaaaaaaaak.","..kaaaaaaaaaaak.","...kaaaaaaaak...","....kaaaaaak....","....kaaaak......","......kkkk......","................","................","................","................"]

ELDER = ["....kkkkkk......","...kjjjjjjk.....","..kjJjjjjJjk....","kjJwwjjwwJjk...","kjjwejjewjjk...",".kjjjjjjjjjjk...",".kjjjjmjjjjjk...","..kjjjjjjjjk....","..kkjjjjjjkk....",".kqqkjjjjkqqk...",".kqqqjjjjqqqk...","..kqqqqqqqqk....","...kqqqqqqk.....","....kkkkkk......","......k.k.......","................"]
RIVAL_BASE = ["...kkkk...","..kzZZzk..",".kzwZwZzk.",".kzeZeZzk.",".kzZZZZzk.",".kzZmZZzk.","..kzZZzk..","...kzzk...","....kk....",".........."]
COLONY = ["...kkkkkk...","..kfFFFFFk..","kfFFFFFFfk.","kfFFFFFFFFFk","kFFFFFFFFFFk","kFFFFFFFFFFk","kFFFFFFFFFFk","kfFFFFFFFfFk",".kfFFFFFFfk.","..kvFFFfvk..","...kkkkkk...","............"]

SUB_O2 = ["..kkkkkk..",".kiiiiiik.","kiIIIIIIik","kiIIIIIIik","kiIIIIIIik","kiIIIIIIik","kiIIIIIIik","kiiiiiiiik",".kiiiiik..","..kkkkkk.."]
SUB_NO3 = ["....kk....","...kGGk...","..kGGGGk..",".kGGGGGGk.","kGGGGGGGGk","kGGGGGGGGk",".kGGGGGGk.","..kGGGGk..","...kGGk...","....kk...."]
SUB_MN4 = ["....kk....","...kPPk...","..kPPPPk..","kkPPPPPPkk","kPPPPPPPPk","kPPPPPPPPk","kkPPPPPPkk","..kPPPPk..","...kPPk...","....kk...."]
SUB_FE3 = ["....kk....","...kook...","..koOOok..",".koOOOOok.","koOOOOOOok","koOOOOOOok",".koOOOOok.","..koOOok..","...kook...","....kk...."]
SUB_SO4 = ["...kkkk...","..kYYYYk..",".kYYYYYYk.","kYYYYYYYYk","kYYYYYYYYk","kYYYYYYYYk","kYYYYYYYYk",".kYYYYYYk.","..kYYYYk..","...kkkk..."]
SUB_CH4 = ["....kk....","...kRRk...","..kRrrRk..",".kRrrrrRk.",".kRrrrRRk.","kRRrrRRRRk","kRRRRRRRRk",".kRRRRRRk.","..kRRRRk..","...kkkk..."]

# ── ENV_PAL ─────────────────────────────────────────────────────────────────
ENV_PAL = [
    {"name":"The Soil Frontier","grain":"#7a5a2a","grain_l":"#a48a5a","grain_d":"#4a3a1a","grain_a":"#c4a060","pore":"#0c1420","pore_l":"#142030","water":"#1a3a60","water_l":"#3060a0","bg":"#060c18","toxic":"#8a3a8a","toxic_g":"#c060c0"},
    {"name":"The Deep Sediment","grain":"#4a3a2a","grain_l":"#6a5a4a","grain_d":"#2a1a0a","grain_a":"#5a4a3a","pore":"#060608","pore_l":"#0c0c14","water":"#0a1428","water_l":"#142038","bg":"#030306","toxic":"#6a2a2a","toxic_g":"#a04040"},
    {"name":"The Methane Seeps","grain":"#3a3040","grain_l":"#5a5060","grain_d":"#2a2030","grain_a":"#4a4050","pore":"#0a0610","pore_l":"#140c1c","water":"#1a1438","water_l":"#2a1a48","bg":"#06040a","toxic":"#7a1a6a","toxic_g":"#b040a0"},
    {"name":"The Permafrost Edge","grain":"#5a6a7a","grain_l":"#8a9aaa","grain_d":"#3a4a5a","grain_a":"#aabaca","pore":"#080c14","pore_l":"#0c1420","water":"#1a3050","water_l":"#3a5a8a","bg":"#040810","toxic":"#4a7a3a","toxic_g":"#70b050"},
    {"name":"The Hydrothermal Realm","grain":"#2a2a3a","grain_l":"#4a4a5a","grain_d":"#1a1a2a","grain_a":"#3a3a4a","pore":"#0a0608","pore_l":"#14080c","water":"#281418","water_l":"#3a1a20","bg":"#060304","toxic":"#8a4a1a","toxic_g":"#c07030"},
]


def s2svg(data, ps, w=None, h=None, bg=None):
    """Sprite data → SVG string. ps = pixel size."""
    rows = len(data)
    cols = max(len(r) for r in data)
    vw, vh = cols * ps, rows * ps
    if w is None: w = vw
    if h is None: h = vh
    o = [f'<svg width="{w}" height="{h}" viewBox="0 0 {vw} {vh}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated;">']
    if bg:
        o.append(f'<rect width="{vw}" height="{vh}" fill="{bg}"/>')
    for y, row in enumerate(data):
        for x, ch in enumerate(row):
            c = PAL.get(ch)
            if c:
                o.append(f'<rect x="{x*ps}" y="{y*ps}" width="{ps}" height="{ps}" fill="{c}"/>')
    o.append('</svg>')
    return '\n'.join(o)


def world_grid(env_idx, gw=20, gh=12, ts=10, seed=42, por=0.6,
               toxic=False, vents=False, maze=False, layered=False,
               subs=None, rivals=0):
    """Generate a tile-grid SVG using actual game ENV_PAL colors."""
    ep = ENV_PAL[env_idx]
    rng = random.Random(seed + env_idx * 1000)
    tiles = [[0]*gw for _ in range(gh)]

    if maze:
        for y in range(gh):
            for x in range(gw):
                tiles[y][x] = 0
        cy = gh // 2
        for x in range(1, gw - 1):
            tiles[cy][x] = 1
            if rng.random() < 0.35:
                cy = max(1, min(gh - 2, cy + rng.choice([-1, 1])))
                tiles[cy][x] = 1
        for _ in range(10):
            sx, sy = rng.randint(2, gw - 3), rng.randint(1, gh - 2)
            tiles[sy][sx] = 1
            ln = rng.randint(2, 5)
            d = rng.choice([(0,1),(0,-1),(1,0),(-1,0)])
            for s in range(ln):
                ny, nx = sy + d[1]*s, sx + d[0]*s
                if 1 <= ny < gh-1 and 1 <= nx < gw-1:
                    tiles[ny][nx] = 1
    elif layered:
        for y in range(gh):
            for x in range(gw):
                tiles[y][x] = 0
        layers = [2, 5, 8] if gh >= 10 else [2, 5]
        for ly in layers:
            for x in range(gw):
                for dy in range(-1, 2):
                    ny = ly + dy
                    if 0 < ny < gh - 1:
                        tiles[ny][x] = 3
        for vx in [4, 10, 15]:
            sy = rng.randint(1, 3)
            for y in range(sy, min(sy + 4, gh - 1)):
                if 0 < vx < gw - 1:
                    tiles[y][vx] = 1
    else:
        for y in range(gh):
            for x in range(gw):
                tiles[y][x] = 1
        ng = int(gw * gh * (1.0 - por) / 4.0)
        for _ in range(ng):
            gx, gy = rng.randint(1, gw - 2), rng.randint(1, gh - 2)
            r = rng.choice([1, 1, 2])
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r*r:
                        tx, ty = gx + dx, gy + dy
                        if 0 <= tx < gw and 0 <= ty < gh:
                            tiles[ty][tx] = 0

    if vents:
        for vx in [rng.randint(5, 8), rng.randint(12, min(16, gw-2))]:
            for y in range(2, gh):
                if 0 <= vx < gw:
                    tiles[y][vx] = 1

    for x in range(gw):
        tiles[0][x] = 0; tiles[gh-1][x] = 0
    for y in range(gh):
        tiles[y][0] = 0; tiles[y][gw-1] = 0

    if toxic:
        for _ in range(4):
            tx, ty = rng.randint(3, gw - 4), rng.randint(2, gh - 3)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = tx + dx, ty + dy
                    if 0 < nx < gw-1 and 0 < ny < gh-1 and tiles[ny][nx] in (1, 3):
                        tiles[ny][nx] = 2

    # Inlet/Outlet
    for y in range(1, gh - 1):
        if tiles[y][1] in (1, 3):
            tiles[y][1] = 4; break
    for y in range(1, gh - 1):
        if tiles[y][gw-2] in (1, 3):
            tiles[y][gw-2] = 5; break

    sw, sh = gw * ts, gh * ts
    o = [f'<svg width="{sw}" height="{sh}" viewBox="0 0 {sw} {sh}" xmlns="http://www.w3.org/2000/svg" style="image-rendering:pixelated;">']
    o.append(f'<rect width="{sw}" height="{sh}" fill="{ep["bg"]}"/>')

    gc = [ep["grain"], ep["grain_l"], ep["grain_d"], ep["grain_a"]]
    pc = [ep["pore"], ep["pore_l"]]

    for y in range(gh):
        for x in range(gw):
            px, py = x * ts, y * ts
            t = tiles[y][x]
            v = (x * 7 + y * 13) % 4
            if t == 0:
                o.append(f'<rect x="{px}" y="{py}" width="{ts}" height="{ts}" fill="{gc[v]}"/>')
            elif t == 1:
                o.append(f'<rect x="{px}" y="{py}" width="{ts}" height="{ts}" fill="{pc[v%2]}"/>')
            elif t == 2:
                o.append(f'<rect x="{px}" y="{py}" width="{ts}" height="{ts}" fill="{ep["toxic"]}"/>')
                o.append(f'<rect x="{px+1}" y="{py+1}" width="{ts-2}" height="{ts-2}" fill="{ep["toxic_g"]}" opacity="0.4"/>')
            elif t == 3:
                o.append(f'<rect x="{px}" y="{py}" width="{ts}" height="{ts}" fill="{ep["water"]}"/>')
                o.append(f'<rect x="{px+2}" y="{py+ts//2}" width="{ts-4}" height="1" fill="{ep["water_l"]}" opacity="0.5"/>')
            elif t == 4:
                o.append(f'<rect x="{px}" y="{py}" width="{ts}" height="{ts}" fill="{pc[0]}"/>')
                o.append(f'<rect x="{px}" y="{py}" width="3" height="{ts}" fill="#3060a0" opacity="0.7"/>')
            elif t == 5:
                o.append(f'<rect x="{px}" y="{py}" width="{ts}" height="{ts}" fill="{pc[0]}"/>')
                o.append(f'<rect x="{px+ts-3}" y="{py}" width="3" height="{ts}" fill="#4fdf6f" opacity="0.7"/>')

    # ARKE sprite
    ax, ay = 2, gh // 2
    for y in range(1, gh - 1):
        for x in range(1, 5):
            if tiles[y][x] in (1, 3, 4):
                ax, ay = x, y; break
        if tiles[ay][ax] in (1, 3, 4):
            break
    apx, apy = ax * ts, ay * ts
    o.append(f'<rect x="{apx+1}" y="{apy}" width="{ts-2}" height="{ts//3}" fill="#7888a0"/>')
    o.append(f'<rect x="{apx+2}" y="{apy+1}" width="{ts-4}" height="{max(1,ts//3-1)}" fill="#40c8d8"/>')
    o.append(f'<rect x="{apx+1}" y="{apy+ts//3}" width="{ts-2}" height="{ts*2//3}" fill="#2acfaf"/>')
    o.append(f'<rect x="{apx}" y="{apy}" width="{ts}" height="{ts}" fill="none" stroke="#000" stroke-width="0.5"/>')

    # Substrates
    sub_colors = {"O2":"#4fa4ff","NO3":"#4fdf6f","Mn":"#cf6fff","Fe":"#ef8f3f","SO4":"#dfdf3f","CH4":"#ff4f4f"}
    if subs:
        placed = 0
        for y in range(2, gh - 2):
            for x in range(3, gw - 3, 3):
                if tiles[y][x] in (1, 3) and placed < len(subs) * 2:
                    st = subs[placed % len(subs)]
                    col = sub_colors.get(st, "#fff")
                    cx, cy2 = x * ts + ts // 2, y * ts + ts // 2
                    r = max(2, ts // 3)
                    o.append(f'<circle cx="{cx}" cy="{cy2}" r="{r}" fill="{col}" opacity="0.85"/>')
                    o.append(f'<circle cx="{cx-1}" cy="{cy2-1}" r="{max(1,r//3)}" fill="white" opacity="0.4"/>')
                    placed += 1

    # Rivals
    for ri in range(rivals):
        rx = rng.randint(gw // 3, gw - 3)
        ry = rng.randint(1, gh - 2)
        if tiles[ry][rx] in (1, 3):
            rpx, rpy = rx * ts, ry * ts
            o.append(f'<rect x="{rpx+1}" y="{rpy+1}" width="{ts-2}" height="{ts-2}" fill="#b03030" rx="1"/>')
            o.append(f'<rect x="{rpx+2}" y="{rpy+2}" width="{max(1,ts//3)}" height="{max(1,ts//4)}" fill="#e06060"/>')
            o.append(f'<rect x="{rpx}" y="{rpy}" width="{ts}" height="{ts}" fill="none" stroke="#000" stroke-width="0.5"/>')

    o.append('</svg>')
    return '\n'.join(o)


# ── Main: Output everything needed ─────────────────────────────────────────
if __name__ == "__main__":
    # Print all sprite SVGs
    print("METHI_DOWN_LARGE:")
    print(s2svg(METHI_DOWN, 12, 192, 192))
    print("\nMETHI_UP:")
    print(s2svg(METHI_UP, 5, 80, 80))
    print("\nMETHI_DOWN_SMALL:")
    print(s2svg(METHI_DOWN, 5, 80, 80))
    print("\nMETHI_LEFT:")
    print(s2svg(METHI_LEFT, 5, 80, 80))
    print("\nMETHI_RIGHT:")
    print(s2svg(METHI_RIGHT, 5, 80, 80))
    print("\nMETHI_EAT:")
    print(s2svg(METHI_EAT, 5, 80, 80))
    print("\nMETHI_GLOW:")
    print(s2svg(METHI_GLOW, 5, 80, 80))
    print("\nELDER_LARGE:")
    print(s2svg(ELDER, 8, 128, 128))
    print("\nRIVAL_LARGE:")
    print(s2svg(RIVAL_BASE, 15, 150, 150))
    print("\nCOLONY_LARGE:")
    print(s2svg(COLONY, 10, 120, 120))
