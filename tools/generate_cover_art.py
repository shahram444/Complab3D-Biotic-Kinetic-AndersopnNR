#!/usr/bin/env python3
"""Generate a BRIGHT 8-bit pixel art cover for itch.io (630x500).
Classic NES box art style with vivid colors that pop on any background.
"""
from PIL import Image, ImageDraw
import math, random

W, H = 630, 500
img = Image.new("RGBA", (W, H), (20, 50, 100, 255))
draw = ImageDraw.Draw(img)
rng = random.Random(42)

# === BRIGHT BACKGROUND GRADIENT ===
# Deep ocean blue at top -> teal midground -> warm earth brown at bottom
for y in range(H):
    t = y / H
    if t < 0.35:
        r = int(15 + 25 * t / 0.35)
        g = int(35 + 50 * t / 0.35)
        b = int(90 + 40 * t / 0.35)
    elif t < 0.65:
        tt = (t - 0.35) / 0.3
        r = int(40 + 30 * tt)
        g = int(85 - 20 * tt)
        b = int(130 - 50 * tt)
    else:
        tt = (t - 0.65) / 0.35
        r = int(70 + 50 * tt)
        g = int(65 + 15 * tt)
        b = int(80 - 40 * tt)
    for x in range(W):
        img.putpixel((x, y), (r, g, b, 255))

# === PIXEL FONT ===
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
    'V': ["10001","10001","10001","10001","01010","01010","00100"],
    '3': ["11110","00001","00001","01110","00001","00001","11110"],
    ':': ["00000","00100","00100","00000","00100","00100","00000"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    '-': ["00000","00000","00000","11111","00000","00000","00000"],
}

def draw_text(text, start_x, start_y, px_size, color, shadow=None, outline=None):
    cx = start_x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT.get(' '))
        if glyph is None:
            cx += 6 * px_size
            continue
        for ry, row in enumerate(glyph):
            for rx, bit in enumerate(row):
                if bit == '1':
                    bx = cx + rx * px_size
                    by = start_y + ry * px_size
                    # Outline (thicker shadow)
                    if outline:
                        for od in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                            draw.rectangle([bx + od[0]*px_size, by + od[1]*px_size,
                                            bx + od[0]*px_size + px_size - 1, by + od[1]*px_size + px_size - 1],
                                           fill=(*outline, 255))
                    # Shadow
                    if shadow:
                        draw.rectangle([bx + px_size, by + px_size,
                                        bx + px_size * 2 - 1, by + px_size * 2 - 1],
                                       fill=(*shadow, 255))
                    draw.rectangle([bx, by, bx + px_size - 1, by + px_size - 1],
                                   fill=(*color, 255))
        cx += 6 * px_size

def text_width(text, px_size):
    return len(text) * 6 * px_size - px_size

# === GRAIN PARTICLES (bottom half) ===
def draw_grain(cx, cy, radius, col_m, col_l, col_d):
    for dy in range(-radius - 1, radius + 2):
        for dx in range(-radius - 1, radius + 2):
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= radius + 0.5:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    if dist > radius - 1.8:
                        c = (30, 20, 10)
                    elif (dx - dy) > radius * 0.3:
                        c = col_l
                    elif (dx - dy) < -radius * 0.3:
                        c = col_d
                    else:
                        c = col_m
                    img.putpixel((px, py), (*c, 255))

GRAIN = (180, 140, 75)
GRAIN_L = (220, 185, 120)
GRAIN_D = (120, 90, 45)

grains = [
    (55, 420, 38), (170, 450, 32), (300, 440, 42), (445, 458, 30),
    (565, 425, 40), (120, 385, 24), (385, 395, 27), (525, 390, 22),
    (35, 360, 20), (235, 380, 22), (495, 370, 18), (605, 395, 25),
    (18, 310, 16), (165, 320, 14), (355, 330, 17), (535, 315, 15),
    (615, 340, 13), (85, 335, 12), (455, 335, 13),
]
for gx, gy, gr in grains:
    draw_grain(gx, gy, gr, GRAIN, GRAIN_L, GRAIN_D)

# Bright water in pores
for i in range(200):
    px = rng.randint(0, W - 1)
    py = rng.randint(280, H - 10)
    on_grain = any((px - gx)**2 + (py - gy)**2 < (gr + 5)**2 for gx, gy, gr in grains)
    if not on_grain:
        sz = rng.randint(3, 9)
        wc = (90, 150, 220) if rng.random() < 0.3 else (55, 110, 180)
        for dy in range(sz):
            for dx in range(sz):
                npx, npy = px + dx, py + dy
                if 0 <= npx < W and 0 <= npy < H:
                    old = img.getpixel((npx, npy))
                    if old[0] < 100 and old[2] > 40:
                        img.putpixel((npx, npy), (*wc, 255))

# Biofilm colonies (bright green blobs)
for bx, by, br in [(170, 420, 14), (385, 400, 12), (535, 398, 11), (275, 410, 10)]:
    for dy in range(-br, br + 1):
        for dx in range(-br, br + 1):
            if dx*dx + dy*dy <= br*br:
                px, py = bx + dx, by + dy
                if 0 <= px < W and 0 <= py < H:
                    c = (140, 235, 165) if rng.random() < 0.4 else (95, 195, 125)
                    img.putpixel((px, py), (*c, 255))

# === BRIGHT SUBSTRATE ORBS ===
def draw_orb(cx, cy, size, col, col_light, glow_size=5):
    for dy in range(-size - glow_size, size + glow_size + 1):
        for dx in range(-size - glow_size, size + glow_size + 1):
            dist = math.sqrt(dx*dx + dy*dy)
            if size < dist <= size + glow_size:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    a = 1 - (dist - size) / glow_size
                    old = img.getpixel((px, py))
                    nr = min(255, old[0] + int(col[0] * a * 0.5))
                    ng = min(255, old[1] + int(col[1] * a * 0.5))
                    nb = min(255, old[2] + int(col[2] * a * 0.5))
                    img.putpixel((px, py), (nr, ng, nb, 255))
    for dy in range(-size, size + 1):
        for dx in range(-size, size + 1):
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= size:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    if dist < size * 0.35:
                        c = (min(255, col_light[0]+30), min(255, col_light[1]+30), min(255, col_light[2]+30))
                    elif dist < size * 0.65:
                        c = col_light
                    elif dist < size * 0.85:
                        c = col
                    else:
                        c = (max(0, col[0]-30), max(0, col[1]-30), max(0, col[2]-30))
                    if dist > size - 1.3:
                        c = (max(0, c[0]-50), max(0, c[1]-50), max(0, c[2]-50))
                    img.putpixel((px, py), (*c, 255))

# Big bright substrates
draw_orb(95, 255, 10, (255, 90, 90), (255, 200, 200), 7)     # CH4 red
draw_orb(195, 300, 9, (90, 175, 255), (200, 230, 255), 6)     # O2 blue
draw_orb(535, 275, 10, (90, 230, 120), (200, 255, 210), 7)    # NO3 green
draw_orb(445, 295, 9, (250, 160, 70), (255, 220, 170), 6)     # Fe orange
draw_orb(55, 330, 8, (230, 230, 80), (255, 255, 200), 6)      # SO4 yellow
draw_orb(565, 330, 8, (210, 120, 255), (240, 190, 255), 6)    # Mn purple
draw_orb(310, 340, 9, (255, 90, 90), (255, 200, 200), 6)      # CH4

# Substrate labels
for x, y, label, col in [(110, 248, "CH4", (255,120,120)), (210, 293, "O2", (130,200,255)),
                           (550, 268, "NO3", (130,240,160)), (460, 288, "Fe", (255,190,110))]:
    draw_text(label, x, y, 2, col, (0,0,0))

# === FLOW ARROWS (bright cyan, visible) ===
for i in range(9):
    ax = 60 + i * 60
    ay = 355
    for dx in range(20):
        for dy in range(-2, 3):
            px, py = ax + dx, ay + dy
            if 0 <= px < W and 0 <= py < H:
                img.putpixel((px, py), (100, 180, 240, 255))
    for dy in range(-5, 6):
        px = ax + 20
        py2 = ay + dy
        if 0 <= px < W and 0 <= py2 < H and abs(dy) < 6:
            img.putpixel((px, py2), (100, 180, 240, 255))

draw_text("IN", 12, 348, 3, (100, 200, 255), (0, 30, 80), (0, 20, 60))
draw_text("OUT", W - 65, 348, 3, (100, 230, 130), (0, 50, 20), (0, 30, 10))

# === ARKE - HUGE CENTER CHARACTER (7x scale) ===
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
    "H": (160, 175, 200), "V": (80, 220, 235), "X": (200, 250, 255),
    "w": (255, 255, 255), "e": (26, 26, 46),
    "T": (55, 220, 190), "t": (35, 160, 140),
}

scale = 7
arke_w = 16 * scale
arke_h = 16 * scale
arke_x = (W - arke_w) // 2
arke_y = 128

# Bright teal glow behind ARKE
for dy in range(-35, arke_h + 35):
    for dx in range(-35, arke_w + 35):
        cx = arke_x + dx
        cy = arke_y + dy
        dist = math.sqrt((dx - arke_w//2)**2 + (dy - arke_h//2)**2)
        max_dist = arke_h * 0.75
        if dist < max_dist and 0 <= cx < W and 0 <= cy < H:
            a = max(0, int(70 * (1 - dist / max_dist)))
            old = img.getpixel((cx, cy))
            nr = min(255, old[0] + a // 4)
            ng = min(255, old[1] + int(a * 1.1))
            nb = min(255, old[2] + int(a * 0.9))
            img.putpixel((cx, cy), (nr, ng, nb, 255))

for ry, row in enumerate(METHI):
    for rx, ch in enumerate(row):
        c = pal.get(ch)
        if c is None:
            continue
        for sy in range(scale):
            for sx in range(scale):
                px = arke_x + rx * scale + sx
                py = arke_y + ry * scale + sy
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), (*c, 255))

# === ELDER (left, 4x scale) ===
ELDER = [
    "....kkkkkk......","...kjjjjjjk.....","..kjJjjjjJjk....",
    ".kjJwwjjwwJjk...",".kjjwejjewjjk...",".kjjjjjjjjjjk...",
    ".kjjjjmjjjjjk...","..kjjjjjjjjk....","..kkjjjjjjkk....",
    ".kqqkjjjjkqqk...",".kqqqjjjjqqqk...","..kqqqqqqqqk....",
    "...kqqqqqqk.....","....kkkkkk......","......k.k.......","................",
]

elder_pal = {
    ".": None, "k": (0, 0, 0),
    "j": (70, 70, 210), "J": (110, 110, 245),
    "w": (255, 255, 255), "e": (26, 26, 46), "m": (10, 106, 90),
    "q": (110, 70, 190), "Q": (140, 100, 220),
}

es = 4
elder_x = 40
elder_y = 158

# Blue glow
for dy in range(-18, 16*es+18):
    for dx in range(-18, 16*es+18):
        cx2, cy2 = elder_x + dx, elder_y + dy
        dist = math.sqrt((dx-32)**2 + (dy-32)**2)
        if dist < 58 and 0 <= cx2 < W and 0 <= cy2 < H:
            a = max(0, int(45 * (1 - dist/58)))
            old = img.getpixel((cx2, cy2))
            img.putpixel((cx2, cy2), (min(255, old[0]+a//5), min(255, old[1]+a//5), min(255, old[2]+a), 255))

for ry, row in enumerate(ELDER):
    for rx, ch in enumerate(row):
        c = elder_pal.get(ch)
        if c is None:
            continue
        for sy in range(es):
            for sx in range(es):
                px, py = elder_x + rx*es + sx, elder_y + ry*es + sy
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), (*c, 255))

# === RIVALS (right side) ===
RIVAL = [
    "...kkkk...","..kzZZzk..",".kzwZwZzk.",".kzeZeZzk.",
    ".kzZZZZzk.",".kzZmZZzk.","..kzZZzk..","...kzzk...","....kk....",".........."]

rival_pal = {".": None, "k": (0,0,0), "z": (180,50,50), "Z": (235,100,100),
             "w": (255,255,255), "e": (26,26,46), "m": (150,30,30)}

for ri, (rx, ry, rs) in enumerate([(495, 165, 4), (550, 210, 3), (585, 155, 2)]):
    glow_r = rs * 13
    for dy in range(-glow_r, glow_r):
        for dx in range(-glow_r, glow_r):
            cx2, cy2 = rx + 5*rs + dx, ry + 5*rs + dy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < glow_r and 0 <= cx2 < W and 0 <= cy2 < H:
                a = max(0, int(40 * (1 - dist/glow_r)))
                old = img.getpixel((cx2, cy2))
                img.putpixel((cx2, cy2), (min(255, old[0]+a), old[1], old[2], 255))

    for ry2, row in enumerate(RIVAL):
        for rx2, ch in enumerate(row):
            c = rival_pal.get(ch)
            if c is None:
                continue
            for sy in range(rs):
                for sx in range(rs):
                    px, py = rx + rx2*rs + sx, ry + ry2*rs + sy
                    if 0 <= px < W and 0 <= py < H:
                        img.putpixel((px, py), (*c, 255))

draw_text("!", 510, 145, 5, (255, 110, 110), (100, 0, 0))

# === TITLE: "ARKE" - huge, bright ===
title = "ARKE"
tw = text_width(title, 9)
tx = (W - tw) // 2

# Dark banner behind title for contrast
for y2 in range(12, 92):
    for x2 in range(W):
        old = img.getpixel((x2, y2))
        fade = 0.65
        if y2 < 20:
            fade *= (y2 - 12) / 8.0
        elif y2 > 84:
            fade *= (92 - y2) / 8.0
        img.putpixel((x2, y2), (int(old[0]*(1-fade)), int(old[1]*(1-fade)), int(old[2]*(1-fade)), 255))

draw_text(title, tx, 18, 9, (110, 255, 230), (5, 40, 35))

# Bright glow line under title
for x2 in range(tx - 25, tx + tw + 25):
    for dy in range(5):
        y2 = 84 + dy
        if 0 <= x2 < W and 0 <= y2 < H:
            a = max(0, 160 - dy * 40)
            old = img.getpixel((x2, y2))
            img.putpixel((x2, y2), (min(255, old[0]+a//5), min(255, old[1]+a), min(255, old[2]+int(a*0.85)), 255))

# Subtitle
sub = "GUARDIANS OF EARTH"
sw = text_width(sub, 4)
sx2 = (W - sw) // 2
draw_text(sub, sx2, 95, 4, (255, 225, 50), (50, 40, 0))

# === BOTTOM BAR ===
for y in range(H - 38, H):
    for x in range(W):
        img.putpixel((x, y), (15, 15, 30, 255))
for x in range(W):
    img.putpixel((x, H - 39), (80, 80, 140, 255))

draw_text("COMPLAB3D", 15, H - 30, 2, (100, 180, 220), (0, 30, 60))
brs = "BASED ON REAL SCIENCE"
bw = text_width(brs, 2)
draw_text(brs, W - bw - 15, H - 30, 2, (150, 150, 180), (30, 30, 60))

# === STARS ===
for i in range(50):
    sx, sy = rng.randint(5, W-5), rng.randint(3, 85)
    old = img.getpixel((sx, sy))
    if old[0] < 60:
        b = rng.randint(180, 255)
        img.putpixel((sx, sy), (b, b, b, 255))
        if rng.random() < 0.35:
            for d in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = sx+d[0], sy+d[1]
                if 0 <= nx < W and 0 <= ny < H:
                    img.putpixel((nx, ny), (b//2, b//2, b//2, 255))

# === BRIGHT BORDER FRAME ===
frame = (90, 90, 150)
bright = (140, 140, 200)
for x in range(W):
    for t in range(3):
        img.putpixel((x, t), (*frame, 255))
        img.putpixel((x, H-1-t), (*frame, 255))
for y in range(H):
    for t in range(3):
        img.putpixel((t, y), (*frame, 255))
        img.putpixel((W-1-t, y), (*frame, 255))
# Inner bright accent
for x in range(3, W-3):
    img.putpixel((x, 3), (*bright, 255))
    img.putpixel((x, H-4), (*bright, 255))
for y in range(3, H-3):
    img.putpixel((3, y), (*bright, 255))
    img.putpixel((W-4, y), (*bright, 255))

# === SUBTLE SCANLINES ===
for y in range(0, H, 3):
    for x in range(W):
        old = img.getpixel((x, y))
        img.putpixel((x, y), (max(0, old[0]-3), max(0, old[1]-3), max(0, old[2]-3), 255))

# === SAVE ===
import os
os.makedirs("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/game/builds", exist_ok=True)
img.save("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/game/builds/cover_art.png")
img.save("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/docs/ARKE_cover_art.png")
print(f"Cover art saved! {W}x{H}")
