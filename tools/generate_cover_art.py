#!/usr/bin/env python3
"""Generate a bright, readable 8-bit pixel art cover for itch.io.
Size: 630x500 (itch.io recommended). Bold, high contrast, large characters.
"""
from PIL import Image, ImageDraw
import math, random

W, H = 630, 500
img = Image.new("RGBA", (W, H), (10, 20, 50, 255))
draw = ImageDraw.Draw(img)
rng = random.Random(42)

# === PALETTE ===
TEAL = (42, 207, 175)
TEAL_BRIGHT = (95, 255, 223)
TEAL_DARK = (15, 80, 70)
GOLD = (255, 215, 0)
GOLD_DARK = (160, 120, 0)
WHITE = (255, 255, 255)
VISOR = (64, 200, 216)
VISOR_SHINE = (180, 245, 250)
HELMET = (140, 155, 180)
RED = (224, 80, 80)
RED_DARK = (160, 40, 40)
BLUE_ELDER = (60, 60, 200)
BLUE_ELDER_H = (100, 100, 240)
PURPLE = (100, 60, 180)
GRAIN = (160, 120, 60)
GRAIN_L = (200, 165, 100)
GRAIN_D = (100, 75, 35)
BIO_GREEN = (80, 180, 110)
BIO_LIGHT = (120, 220, 150)
WATER = (40, 80, 140)
WATER_L = (70, 130, 200)
CH4_RED = (255, 90, 90)
O2_BLUE = (90, 175, 255)
NO3_GREEN = (90, 230, 120)
FE_ORANGE = (250, 160, 70)
SO4_YELLOW = (230, 230, 80)
MN_PURPLE = (210, 120, 255)

# === BACKGROUND: Rich gradient (NOT black!) ===
for y in range(H):
    t = y / H
    # Top: deep blue, Middle: dark teal, Bottom: dark brown (underground feel)
    if t < 0.3:
        r = int(8 + 15 * t)
        g = int(15 + 30 * t)
        b = int(45 + 20 * t)
    elif t < 0.7:
        tt = (t - 0.3) / 0.4
        r = int(12 + 20 * tt)
        g = int(24 + 15 * tt)
        b = int(51 - 10 * tt)
    else:
        tt = (t - 0.7) / 0.3
        r = int(32 + 25 * tt)
        g = int(28 + 15 * tt)
        b = int(40 - 15 * tt)
    for x in range(W):
        img.putpixel((x, y), (r, g, b, 255))

# === LARGE PORE-SPACE SCENE (bottom half) ===

def draw_circle(cx, cy, radius, col_main, col_light, col_dark, outline=(0,0,0)):
    for dy in range(-radius - 1, radius + 2):
        for dx in range(-radius - 1, radius + 2):
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= radius + 0.5:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    if dist > radius - 1.5:
                        c = outline
                    elif (dx - dy) > radius * 0.3:
                        c = col_light
                    elif (dx - dy) < -radius * 0.3:
                        c = col_dark
                    else:
                        c = col_main
                    img.putpixel((px, py), (*c, 255))

# Grain clusters - big, visible
grains = [
    (60, 430, 35), (170, 460, 30), (300, 450, 40), (440, 465, 28),
    (560, 435, 38), (115, 395, 22), (380, 405, 25), (520, 400, 20),
    (40, 370, 18), (230, 390, 20), (490, 380, 16), (600, 405, 22),
    # Upper scattered
    (20, 320, 14), (160, 330, 12), (350, 340, 15), (530, 325, 13),
    (610, 350, 11), (80, 345, 10), (450, 345, 11),
]
for gx, gy, gr in grains:
    draw_circle(gx, gy, gr, GRAIN, GRAIN_L, GRAIN_D)

# Pore water between grains (bright blue patches)
for i in range(120):
    px = rng.randint(0, W - 1)
    py = rng.randint(300, H - 10)
    on_grain = any((px - gx)**2 + (py - gy)**2 < (gr + 4)**2 for gx, gy, gr in grains)
    if not on_grain:
        sz = rng.randint(3, 8)
        wc = WATER_L if rng.random() < 0.3 else WATER
        for dy in range(sz):
            for dx in range(sz):
                npx, npy = px + dx, py + dy
                if 0 <= npx < W and 0 <= npy < H:
                    old = img.getpixel((npx, npy))
                    if old[0] < 80:
                        img.putpixel((npx, npy), (*wc, 255))

# Biofilm colonies (bright green)
for bx, by, br in [(170, 430, 12), (380, 410, 10), (530, 408, 9), (270, 418, 8)]:
    for dy in range(-br, br + 1):
        for dx in range(-br, br + 1):
            if dx*dx + dy*dy <= br*br:
                px, py = bx + dx, by + dy
                if 0 <= px < W and 0 <= py < H:
                    c = BIO_LIGHT if rng.random() < 0.4 else BIO_GREEN
                    img.putpixel((px, py), (*c, 255))

# === FLOATING SUBSTRATES (bright, visible orbs) ===

def draw_orb(cx, cy, size, col, col_light, glow_size=4):
    # Glow
    for dy in range(-size - glow_size, size + glow_size + 1):
        for dx in range(-size - glow_size, size + glow_size + 1):
            dist = math.sqrt(dx*dx + dy*dy)
            if size < dist <= size + glow_size:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    a = 1 - (dist - size) / glow_size
                    old = img.getpixel((px, py))
                    nr = min(255, old[0] + int(col[0] * a * 0.4))
                    ng = min(255, old[1] + int(col[1] * a * 0.4))
                    nb = min(255, old[2] + int(col[2] * a * 0.4))
                    img.putpixel((px, py), (nr, ng, nb, 255))
    # Core
    for dy in range(-size, size + 1):
        for dx in range(-size, size + 1):
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= size:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    if dist < size * 0.4:
                        c = col_light
                    elif dist < size * 0.75:
                        c = col
                    else:
                        c = (max(0, col[0] - 40), max(0, col[1] - 40), max(0, col[2] - 40))
                    # Outline
                    if dist > size - 1.2:
                        c = (max(0, c[0] - 60), max(0, c[1] - 60), max(0, c[2] - 60))
                    img.putpixel((px, py), (*c, 255))

# Big substrates scattered around
draw_orb(90, 270, 8, CH4_RED, (255, 180, 180), 6)    # CH4
draw_orb(180, 310, 7, O2_BLUE, (180, 220, 255), 5)    # O2
draw_orb(530, 290, 8, NO3_GREEN, (180, 255, 200), 6)  # NO3
draw_orb(440, 310, 7, FE_ORANGE, (255, 210, 160), 5)  # Fe
draw_orb(50, 340, 6, SO4_YELLOW, (255, 255, 200), 5)  # SO4
draw_orb(560, 340, 6, MN_PURPLE, (230, 180, 255), 5)  # Mn
draw_orb(300, 350, 7, CH4_RED, (255, 180, 180), 5)    # CH4
draw_orb(370, 290, 5, O2_BLUE, (180, 220, 255), 4)    # O2

# Labels next to substrates
def put_label(x, y, text, color):
    """Simple 1px text approximation - draw colored rectangle with text idea."""
    # We'll use draw.text with default font
    try:
        draw.text((x, y), text, fill=(*color, 255))
    except:
        pass

put_label(102, 265, "CH4", CH4_RED)
put_label(192, 305, "O2", O2_BLUE)
put_label(542, 285, "NO3", NO3_GREEN)
put_label(452, 305, "Fe3+", FE_ORANGE)

# === FLOW ARROWS (bright, visible) ===
for i in range(8):
    ax = 80 + i * 65
    ay = 360
    # Bright blue arrow
    for dx in range(18):
        for dy in range(-2, 3):
            px, py = ax + dx, ay + dy
            if 0 <= px < W and 0 <= py < H:
                old = img.getpixel((px, py))
                if old[0] < 120:
                    img.putpixel((px, py), (*WATER_L, 255))
    # Arrow head
    for dy in range(-5, 6):
        px = ax + 18
        py2 = ay + dy
        if 0 <= px < W and 0 <= py2 < H and abs(dy) < 6:
            old = img.getpixel((px, py2))
            if old[0] < 120:
                img.putpixel((px, py2), (*WATER_L, 255))

# === PIXEL FONT (5x7, drawn at given scale) ===
FONT = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'E': ["11111","10000","10000","11110","10000","10000","11111"],
    'G': ["01111","10000","10000","10111","10001","10001","01110"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'D': ["11100","10010","10001","10001","10001","10010","11100"],
    'I': ["11111","00100","00100","00100","00100","00100","11111"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'S': ["01110","10001","10000","01110","00001","10001","01110"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'F': ["11111","10000","10000","11110","10000","10000","10000"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'B': ["11110","10001","10001","11110","10001","10001","11110"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'W': ["10001","10001","10001","10101","10101","11011","10001"],
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
    '3': ["11110","00001","00001","01110","00001","00001","11110"],
    ':': ["00000","00100","00100","00000","00100","00100","00000"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
}

def draw_text(text, start_x, start_y, px_size, color, shadow=None):
    cx = start_x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[' '])
        for ry, row in enumerate(glyph):
            for rx, bit in enumerate(row):
                if bit == '1':
                    bx = cx + rx * px_size
                    by = start_y + ry * px_size
                    if shadow:
                        draw.rectangle([bx + px_size, by + px_size,
                                        bx + px_size * 2 - 1, by + px_size * 2 - 1],
                                       fill=(*shadow, 255))
                    draw.rectangle([bx, by, bx + px_size - 1, by + px_size - 1],
                                   fill=(*color, 255))
        cx += 6 * px_size

def text_width(text, px_size):
    return len(text) * 6 * px_size - px_size

# === TITLE: "ARKE" huge and bright ===
title = "ARKE"
tw = text_width(title, 8)
tx = (W - tw) // 2
draw_text(title, tx, 25, 8, TEAL_BRIGHT, (0, 40, 35))

# Glow line under title
for x in range(tx - 20, tx + tw + 20):
    for dy in range(4):
        y = 88 + dy
        if 0 <= x < W and 0 <= y < H:
            a = max(0, 120 - dy * 35)
            old = img.getpixel((x, y))
            nr = min(255, old[0] + a // 5)
            ng = min(255, old[1] + a)
            nb = min(255, old[2] + int(a * 0.85))
            img.putpixel((x, y), (nr, ng, nb, 255))

# Subtitle: "GUARDIANS OF EARTH"
sub = "GUARDIANS OF EARTH"
sw = text_width(sub, 4)
sx = (W - sw) // 2
draw_text(sub, sx, 100, 4, GOLD, (60, 45, 0))

# === ARKE CHARACTER - HUGE (center, 6x scale = 96px) ===
METHI = [
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

pal = {
    ".": None, "k": (0, 0, 0),
    "H": HELMET, "V": VISOR, "X": VISOR_SHINE,
    "w": WHITE, "e": (26, 26, 46),
    "T": TEAL, "t": (26, 138, 122),
    "L": TEAL_BRIGHT, "d": TEAL_DARK,
    "s": (255, 255, 95), "m": (10, 106, 90),
}

scale = 6
arke_w = 16 * scale
arke_h = 16 * scale
arke_x = (W - arke_w) // 2
arke_y = 140

# Big teal glow behind ARKE
for dy in range(-30, arke_h + 30):
    for dx in range(-30, arke_w + 30):
        cx = arke_x + dx
        cy = arke_y + dy
        dist = math.sqrt((dx - arke_w // 2)**2 + (dy - arke_h // 2)**2)
        max_dist = arke_h * 0.7
        if dist < max_dist and 0 <= cx < W and 0 <= cy < H:
            a = max(0, int(50 * (1 - dist / max_dist)))
            old = img.getpixel((cx, cy))
            nr = min(255, old[0] + a // 4)
            ng = min(255, old[1] + a)
            nb = min(255, old[2] + int(a * 0.8))
            img.putpixel((cx, cy), (nr, ng, nb, 255))

# Draw ARKE
for ry, row in enumerate(METHI):
    for rx, ch in enumerate(row):
        c = pal.get(ch)
        if c is None:
            continue
        for sy in range(scale):
            for sx2 in range(scale):
                px = arke_x + rx * scale + sx2
                py = arke_y + ry * scale + sy
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), (*c, 255))

# === ELDER (left, 4x scale) ===
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

elder_pal = {
    ".": None, "k": (0, 0, 0),
    "j": BLUE_ELDER, "J": BLUE_ELDER_H,
    "w": WHITE, "e": (26, 26, 46), "m": (10, 106, 90),
    "q": PURPLE, "Q": (130, 90, 210),
}

es = 4
elder_x = 50
elder_y = 170

# Blue glow
for dy in range(-15, 16 * es + 15):
    for dx in range(-15, 16 * es + 15):
        cx = elder_x + dx
        cy = elder_y + dy
        dist = math.sqrt((dx - 32)**2 + (dy - 32)**2)
        if dist < 55 and 0 <= cx < W and 0 <= cy < H:
            a = max(0, int(35 * (1 - dist / 55)))
            old = img.getpixel((cx, cy))
            nr = min(255, old[0] + a // 4)
            ng = min(255, old[1] + a // 4)
            nb = min(255, old[2] + a)
            img.putpixel((cx, cy), (nr, ng, nb, 255))

for ry, row in enumerate(ELDER):
    for rx, ch in enumerate(row):
        c = elder_pal.get(ch)
        if c is None:
            continue
        for sy in range(es):
            for sx2 in range(es):
                px = elder_x + rx * es + sx2
                py = elder_y + ry * es + sy
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), (*c, 255))

# === RIVALS (right side, 3x scale, two of them) ===
RIVAL = [
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

rival_pal = {
    ".": None, "k": (0, 0, 0),
    "z": RED_DARK, "Z": RED,
    "w": WHITE, "e": (26, 26, 46), "m": (140, 30, 30),
}

for ri, (rx, ry, rs) in enumerate([(490, 180, 4), (540, 220, 3), (580, 170, 2)]):
    # Red glow
    glow_r = rs * 12
    for dy in range(-glow_r, glow_r):
        for dx in range(-glow_r, glow_r):
            cx = rx + 5 * rs + dx
            cy = ry + 5 * rs + dy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < glow_r and 0 <= cx < W and 0 <= cy < H:
                a = max(0, int(30 * (1 - dist / glow_r)))
                old = img.getpixel((cx, cy))
                nr = min(255, old[0] + a)
                ng = old[1]
                nb = old[2]
                img.putpixel((cx, cy), (nr, ng, nb, 255))

    for ry2, row in enumerate(RIVAL):
        for rx2, ch in enumerate(row):
            c = rival_pal.get(ch)
            if c is None:
                continue
            for sy in range(rs):
                for sx2 in range(rs):
                    px = rx + rx2 * rs + sx2
                    py = ry + ry2 * rs + sy
                    if 0 <= px < W and 0 <= py < H:
                        img.putpixel((px, py), (*c, 255))

# "!" above biggest rival
draw_text("!", 505, 160, 4, (255, 100, 100), (80, 0, 0))

# === BOTTOM INFO BAR ===
for y in range(H - 35, H):
    for x in range(W):
        img.putpixel((x, y), (12, 12, 25, 255))
for x in range(W):
    img.putpixel((x, H - 36), (60, 60, 110, 255))

draw_text("COMPLAB3D", 15, H - 28, 2, (80, 160, 200), (0, 30, 50))

brs = "BASED ON REAL SCIENCE"
bw = text_width(brs, 2)
draw_text(brs, W - bw - 15, H - 28, 2, (130, 130, 160), (30, 30, 50))

# === "IN" and "OUT" labels ===
draw_text("IN", 15, 360, 3, O2_BLUE, (0, 30, 60))
draw_text("OUT", W - 60, 360, 3, NO3_GREEN, (0, 40, 20))

# === STARS in upper area ===
for i in range(40):
    sx = rng.randint(5, W - 5)
    sy = rng.randint(3, 90)
    old = img.getpixel((sx, sy))
    if old[0] < 50 and old[1] < 70:
        b = rng.randint(160, 255)
        img.putpixel((sx, sy), (b, b, b, 255))
        if rng.random() < 0.3:
            for d in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = sx + d[0], sy + d[1]
                if 0 <= nx < W and 0 <= ny < H:
                    img.putpixel((nx, ny), (b//2, b//2, b//2, 255))

# === BORDER FRAME ===
frame = (70, 70, 120)
for x in range(W):
    for t in range(3):
        img.putpixel((x, t), (*frame, 255))
        img.putpixel((x, H - 1 - t), (*frame, 255))
for y in range(H):
    for t in range(3):
        img.putpixel((t, y), (*frame, 255))
        img.putpixel((W - 1 - t, y), (*frame, 255))

# Corner accents
bright = (110, 110, 170)
for i in range(6):
    for j in range(6 - i):
        for cx, cy in [(3, 3), (W - 4 - j, 3), (3, H - 4 - j), (W - 4 - j, H - 4 - j)]:
            px, py = cx + (i if cx < W // 2 else 0), cy + (i if cy < H // 2 else 0)
            if 0 <= px < W and 0 <= py < H:
                img.putpixel((px, py), (*bright, 255))

# === SCANLINES (very subtle) ===
for y in range(0, H, 3):
    for x in range(W):
        old = img.getpixel((x, y))
        nr = max(0, old[0] - 4)
        ng = max(0, old[1] - 4)
        nb = max(0, old[2] - 4)
        img.putpixel((x, y), (nr, ng, nb, 255))

# === SAVE ===
import os
os.makedirs("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/game/builds", exist_ok=True)

img.save("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/game/builds/cover_art.png")
img.save("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/docs/ARKE_cover_art.png")

print(f"Cover art saved! Size: {W}x{H}")
print(f"  game/builds/cover_art.png")
print(f"  docs/ARKE_cover_art.png")
