#!/usr/bin/env python3
"""Generate a nostalgic 8-bit pixel art cover image for ARKE: Guardians of Earth.
Style: Classic NES/Famicom game box art with pixel characters and atmospheric scene.
Output: 960x540 PNG (native game resolution), pixel-perfect at 2x scale.
"""
from PIL import Image, ImageDraw

# Work at 480x270 native, then scale up 2x for crisp pixels
W, H = 480, 270
img = Image.new("RGBA", (W, H), (5, 5, 15, 255))
draw = ImageDraw.Draw(img)

# === PALETTE (from sprite_factory.gd) ===
PAL = {
    "bg_deep":    (5, 5, 15),
    "bg_mid":     (10, 15, 35),
    "bg_top":     (15, 25, 50),
    # Grains
    "grain":      (122, 90, 42),
    "grain_l":    (164, 138, 90),
    "grain_d":    (74, 58, 26),
    "grain_a":    (196, 160, 96),
    # Pore/water
    "pore":       (20, 30, 55),
    "pore_l":     (30, 45, 70),
    "water":      (26, 58, 96),
    "water_l":    (48, 96, 160),
    # Teal (ARKE)
    "teal":       (26, 138, 122),
    "teal_h":     (42, 207, 175),
    "teal_glow":  (95, 255, 223),
    "teal_d":     (10, 90, 74),
    # Visor
    "visor":      (64, 200, 216),
    "visor_s":    (144, 232, 240),
    "helmet":     (120, 136, 160),
    # Elder
    "elder":      (26, 26, 160),
    "elder_h":    (72, 72, 208),
    # Rival
    "rival":      (176, 48, 48),
    "rival_h":    (224, 96, 96),
    # Substrates
    "ch4_r":      (255, 79, 79),
    "ch4_l":      (255, 159, 127),
    "o2_b":       (79, 164, 255),
    "o2_l":       (143, 200, 255),
    "no3_g":      (79, 223, 111),
    "no3_l":      (143, 255, 159),
    "fe_o":       (239, 143, 63),
    "fe_l":       (255, 191, 127),
    "so4_y":      (223, 223, 63),
    "mn_p":       (207, 111, 255),
    # Toxic
    "toxic":      (180, 40, 180),
    "toxic_g":    (220, 80, 220),
    # UI
    "gold":       (255, 215, 0),
    "white":      (255, 255, 255),
    "gray":       (136, 136, 136),
    "dark_gray":  (68, 68, 68),
    # Biofilm
    "bio":        (58, 122, 90),
    "bio_l":      (90, 170, 122),
}

import random
import math

rng = random.Random(42)

# === BACKGROUND: Underground pore-space scene ===

# Gradient sky (underground glow from above)
for y in range(H):
    t = y / H
    r = int(5 + 12 * (1 - t))
    g = int(5 + 20 * (1 - t))
    b = int(15 + 40 * (1 - t))
    for x in range(W):
        img.putpixel((x, y), (r, g, b, 255))

# Subtle water flow streaks in background
for i in range(40):
    sx = rng.randint(0, W)
    sy = rng.randint(60, H - 40)
    length = rng.randint(20, 60)
    alpha = rng.randint(15, 40)
    for dx in range(length):
        px = sx + dx
        py = sy + int(math.sin(dx * 0.15 + i) * 2)
        if 0 <= px < W and 0 <= py < H:
            old = img.getpixel((px, py))
            nr = min(255, old[0] + alpha // 4)
            ng = min(255, old[1] + alpha // 3)
            nb = min(255, old[2] + alpha // 2)
            img.putpixel((px, py), (nr, ng, nb, 255))

# === GRAIN CLUSTERS (pore geometry) ===

def draw_grain(cx, cy, radius, col_main, col_light, col_dark):
    """Draw a circular grain particle with shading."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx*dx + dy*dy <= radius*radius:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    # Simple shading
                    shade = dx - dy  # light from top-left
                    if shade > radius * 0.4:
                        c = col_light
                    elif shade < -radius * 0.4:
                        c = col_dark
                    else:
                        c = col_main
                    # Edge outline
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > radius - 1.2:
                        c = (max(0, c[0] - 40), max(0, c[1] - 40), max(0, c[2] - 40))
                    img.putpixel((px, py), (*c, 255))

# Bottom terrain - large grains
grain_positions = [
    # Bottom row
    (40, 240, 18), (90, 250, 14), (140, 235, 20), (200, 248, 16),
    (260, 238, 22), (320, 252, 12), (370, 242, 17), (420, 248, 15),
    (460, 235, 19),
    # Second row
    (65, 215, 12), (165, 210, 14), (310, 215, 11), (400, 218, 13),
    # Scattered upper
    (20, 180, 9), (110, 170, 11), (350, 175, 10), (450, 185, 8),
    # Left column grains
    (15, 120, 14), (8, 155, 10), (25, 90, 8),
    # Right column grains
    (465, 130, 12), (470, 165, 9), (455, 100, 7),
]

for gx, gy, gr in grain_positions:
    draw_grain(gx, gy, gr, PAL["grain"], PAL["grain_l"], PAL["grain_d"])

# === PORE CHANNELS between grains (brighter water areas) ===
for i in range(60):
    px = rng.randint(0, W - 1)
    py = rng.randint(140, H - 20)
    # Check not on a grain
    on_grain = False
    for gx, gy, gr in grain_positions:
        if (px - gx)**2 + (py - gy)**2 < (gr + 2)**2:
            on_grain = True
            break
    if not on_grain:
        sz = rng.randint(2, 5)
        wc = PAL["water_l"] if rng.random() < 0.3 else PAL["water"]
        for dy in range(sz):
            for dx in range(sz):
                npx, npy = px + dx, py + dy
                if 0 <= npx < W and 0 <= npy < H:
                    old = img.getpixel((npx, npy))
                    # Only draw on dark areas (pore space)
                    if old[0] < 60 and old[1] < 60:
                        img.putpixel((npx, npy), (*wc, 255))

# === BIOFILM COLONIES on some grains ===
bio_positions = [(140, 215, 8), (260, 218, 7), (370, 225, 6), (420, 232, 5)]
for bx, by, br in bio_positions:
    for dy in range(-br, br + 1):
        for dx in range(-br, br + 1):
            if dx*dx + dy*dy <= br*br:
                px, py = bx + dx, by + dy
                if 0 <= px < W and 0 <= py < H:
                    c = PAL["bio_l"] if rng.random() < 0.4 else PAL["bio"]
                    img.putpixel((px, py), (*c, 255))

# === FLOW ARROWS (subtle, showing left-to-right flow) ===
for i in range(12):
    ax = 50 + i * 35
    ay = 155 + int(math.sin(i * 0.8) * 15)
    a_col = (48, 96, 160, 100)
    # Arrow body
    for dx in range(8):
        for dy in range(-1, 2):
            px, py = ax + dx, ay + dy
            if 0 <= px < W and 0 <= py < H:
                old = img.getpixel((px, py))
                if old[0] < 80:
                    img.putpixel((px, py), (old[0] + 20, old[1] + 40, old[2] + 60, 255))
    # Arrow head
    for dy in range(-3, 4):
        px = ax + 8
        py2 = ay + dy
        if 0 <= px < W and 0 <= py2 < H:
            old = img.getpixel((px, py2))
            if old[0] < 80:
                img.putpixel((px, py2), (old[0] + 15, old[1] + 30, old[2] + 50, 255))

# === TOXIC ZONE (right side, purple glow) ===
for i in range(30):
    tx = rng.randint(380, 440)
    ty = rng.randint(150, 200)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            px, py = tx + dx, ty + dy
            if 0 <= px < W and 0 <= py < H:
                old = img.getpixel((px, py))
                if old[0] < 100:
                    a = rng.randint(20, 50)
                    img.putpixel((px, py), (min(255, old[0] + a), old[1], min(255, old[2] + a), 255))

# === SUBSTRATE MOLECULES floating ===

def draw_substrate(cx, cy, size, col, col_light):
    """Draw a small glowing substrate orb."""
    for dy in range(-size, size + 1):
        for dx in range(-size, size + 1):
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= size:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    if dist < size * 0.5:
                        c = col_light
                    elif dist < size * 0.8:
                        c = col
                    else:
                        c = (max(0, col[0] - 30), max(0, col[1] - 30), max(0, col[2] - 30))
                    img.putpixel((px, py), (*c, 255))
    # Glow
    for dy in range(-size - 2, size + 3):
        for dx in range(-size - 2, size + 3):
            dist = math.sqrt(dx*dx + dy*dy)
            if size < dist <= size + 2:
                px, py = cx + dx, cy + dy
                if 0 <= px < W and 0 <= py < H:
                    old = img.getpixel((px, py))
                    a = int(30 * (1 - (dist - size) / 2))
                    nr = min(255, old[0] + (col[0] * a) // 255)
                    ng = min(255, old[1] + (col[1] * a) // 255)
                    nb = min(255, old[2] + (col[2] * a) // 255)
                    img.putpixel((px, py), (nr, ng, nb, 255))

# Substrates scattered in pore space
substrates = [
    (75, 150, 4, PAL["ch4_r"], PAL["ch4_l"]),     # CH4
    (180, 135, 3, PAL["o2_b"], PAL["o2_l"]),        # O2
    (130, 165, 3, PAL["no3_g"], PAL["no3_l"]),      # NO3
    (290, 155, 4, PAL["fe_o"], PAL["fe_l"]),         # Fe
    (330, 140, 3, PAL["so4_y"], (255, 255, 200)),    # SO4
    (60, 120, 3, PAL["mn_p"], (220, 160, 255)),      # Mn
    (220, 160, 3, PAL["ch4_r"], PAL["ch4_l"]),       # CH4
    (400, 145, 3, PAL["ch4_r"], PAL["ch4_l"]),       # CH4 in toxic
    (155, 145, 2, PAL["o2_b"], PAL["o2_l"]),         # O2
    (350, 160, 2, PAL["no3_g"], PAL["no3_l"]),       # NO3
]

for sx, sy, sz, sc, sl in substrates:
    draw_substrate(sx, sy, sz, sc, sl)

# === ARKE - Main character (center, large, heroic) ===

# Draw ARKE at ~3x game scale (48x48 pixels), centered
arke_x, arke_y = 210, 85
scale = 3

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

sprite_pal = {
    ".": None, "k": (0, 0, 0),
    "H": (120, 136, 160), "V": (64, 200, 216), "X": (144, 232, 240),
    "w": (255, 255, 255), "e": (26, 26, 46),
    "T": (42, 207, 175), "t": (26, 138, 122),
    "L": (95, 255, 223), "d": (10, 90, 74),
    "s": (255, 255, 95), "m": (10, 106, 90),
}

# Glow aura behind ARKE
for dy in range(-22, 54):
    for dx in range(-22, 54):
        cx = arke_x + dx
        cy = arke_y + dy
        dist = math.sqrt((dx - 16)**2 + (dy - 16)**2)
        if dist < 38 and 0 <= cx < W and 0 <= cy < H:
            a = max(0, int(35 * (1 - dist / 38)))
            old = img.getpixel((cx, cy))
            nr = min(255, old[0] + a // 3)
            ng = min(255, old[1] + a)
            nb = min(255, old[2] + int(a * 0.85))
            img.putpixel((cx, cy), (nr, ng, nb, 255))

# Draw ARKE sprite
for row_idx, row in enumerate(METHI_DOWN):
    for col_idx, ch in enumerate(row):
        c = sprite_pal.get(ch)
        if c is None:
            continue
        for sy2 in range(scale):
            for sx2 in range(scale):
                px = arke_x + col_idx * scale + sx2
                py = arke_y + row_idx * scale + sy2
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), (*c, 255))

# === ELDER ARCHAEA (left side, smaller, mentor pose) ===
elder_x, elder_y = 60, 60
elder_scale = 2

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
    "j": (26, 26, 160), "J": (72, 72, 208),
    "w": (255, 255, 255), "e": (26, 26, 46),
    "m": (10, 106, 90),
    "q": (80, 48, 160), "Q": (112, 80, 192),
}

# Elder glow
for dy in range(-10, 42):
    for dx in range(-10, 42):
        cx = elder_x + dx
        cy = elder_y + dy
        dist = math.sqrt((dx - 12)**2 + (dy - 12)**2)
        if dist < 26 and 0 <= cx < W and 0 <= cy < H:
            a = max(0, int(20 * (1 - dist / 26)))
            old = img.getpixel((cx, cy))
            nr = min(255, old[0] + a // 3)
            ng = min(255, old[1] + a // 3)
            nb = min(255, old[2] + a)
            img.putpixel((cx, cy), (nr, ng, nb, 255))

for row_idx, row in enumerate(ELDER):
    for col_idx, ch in enumerate(row):
        c = elder_pal.get(ch)
        if c is None:
            continue
        for sy2 in range(elder_scale):
            for sx2 in range(elder_scale):
                px = elder_x + col_idx * elder_scale + sx2
                py = elder_y + row_idx * elder_scale + sy2
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), (*c, 255))

# === RIVAL MICROBES (right side, menacing) ===
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
    "z": (176, 48, 48), "Z": (224, 96, 96),
    "w": (255, 255, 255), "e": (26, 26, 46),
    "m": (140, 30, 30),
}

# Two rivals at different positions
for ri, (rx, ry, rs) in enumerate([(380, 70, 2), (420, 95, 2), (360, 105, 1)]):
    # Red glow
    for dy in range(-6, 26):
        for dx in range(-6, 26):
            cx = rx + dx
            cy = ry + dy
            dist = math.sqrt((dx - 8)**2 + (dy - 8)**2)
            if dist < 18 and 0 <= cx < W and 0 <= cy < H:
                a = max(0, int(15 * (1 - dist / 18)))
                old = img.getpixel((cx, cy))
                nr = min(255, old[0] + a)
                ng = old[1]
                nb = old[2]
                img.putpixel((cx, cy), (nr, ng, nb, 255))

    for row_idx, row in enumerate(RIVAL):
        for col_idx, ch in enumerate(row):
            c = rival_pal.get(ch)
            if c is None:
                continue
            for sy2 in range(rs):
                for sx2 in range(rs):
                    px = rx + col_idx * rs + sx2
                    py = ry + row_idx * rs + sy2
                    if 0 <= px < W and 0 <= py < H:
                        img.putpixel((px, py), (*c, 255))

# === TITLE TEXT (pixel art letters) ===

# Each letter is defined on a 5x7 grid
FONT_5x7 = {
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
    '3': ["11110","00001","00001","01110","00001","00001","11110"],
    ':': ["00000","00100","00100","00000","00100","00100","00000"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
}

def draw_text(text, start_x, start_y, pixel_size, color, shadow_color=None):
    """Draw pixel text using 5x7 font."""
    cx = start_x
    for ch in text.upper():
        glyph = FONT_5x7.get(ch, FONT_5x7.get(' '))
        if glyph is None:
            cx += 6 * pixel_size
            continue
        for row_idx, row in enumerate(glyph):
            for col_idx, bit in enumerate(row):
                if bit == '1':
                    px = cx + col_idx * pixel_size
                    py = start_y + row_idx * pixel_size
                    # Shadow
                    if shadow_color:
                        for sy2 in range(pixel_size):
                            for sx2 in range(pixel_size):
                                spx = px + pixel_size + sx2
                                spy = py + pixel_size + sy2
                                if 0 <= spx < W and 0 <= spy < H:
                                    img.putpixel((spx, spy), (*shadow_color, 255))
                    # Main pixel
                    for sy2 in range(pixel_size):
                        for sx2 in range(pixel_size):
                            npx = px + sx2
                            npy = py + sy2
                            if 0 <= npx < W and 0 <= npy < H:
                                img.putpixel((npx, npy), (*color, 255))
        cx += 6 * pixel_size

# "ARKE" - Main title, large
title = "ARKE"
title_w = len(title) * 6 * 4 - 4  # pixel_size=4
title_x = (W - title_w) // 2
draw_text(title, title_x, 10, 4, (42, 207, 175), (0, 50, 45))

# Underline glow
for x in range(title_x - 10, title_x + title_w + 10):
    if 0 <= x < W:
        for dy in range(3):
            y = 42 + dy
            if y < H:
                a = 80 - dy * 25
                old = img.getpixel((x, y))
                img.putpixel((x, y), (min(255, old[0] + a // 4), min(255, old[1] + a), min(255, old[2] + int(a * 0.8)), 255))

# "GUARDIANS OF EARTH" - Subtitle
sub = "GUARDIANS OF EARTH"
sub_w = len(sub) * 6 * 2 - 2
sub_x = (W - sub_w) // 2
draw_text(sub, sub_x, 50, 2, (255, 215, 0), (80, 60, 0))

# === BOTTOM BAR with game info ===
# Dark bar at bottom
for y in range(H - 22, H):
    for x in range(W):
        img.putpixel((x, y), (8, 8, 20, 255))
# Border line
for x in range(W):
    img.putpixel((x, H - 23), (50, 50, 90, 255))

# "CompLaB3D" text
draw_text("COMPLAB3D", 10, H - 18, 1, (80, 160, 200))

# "BASED ON REAL SCIENCE" text
draw_text("BASED ON REAL SCIENCE", W - 220, H - 18, 1, (100, 100, 120))

# === "INLET" and "OUTLET" labels ===
draw_text("IN", 8, 155, 1, (79, 164, 255))
# Small arrows from left
for i in range(4):
    ax = 22 + i * 10
    for dy in range(-1, 2):
        if 0 <= 157 + dy < H:
            img.putpixel((ax, 157 + dy), (48, 96, 160, 255))
            img.putpixel((ax + 1, 157 + dy), (48, 96, 160, 255))

draw_text("OUT", W - 28, 155, 1, (94, 207, 94))

# === SCANLINES effect (subtle, nostalgic) ===
for y in range(0, H, 2):
    for x in range(W):
        old = img.getpixel((x, y))
        # Very subtle darkening of every other line
        nr = max(0, old[0] - 6)
        ng = max(0, old[1] - 6)
        nb = max(0, old[2] - 6)
        img.putpixel((x, y), (nr, ng, nb, 255))

# === CORNER DECORATIONS (NES-style frame) ===
frame_col = (50, 50, 90)
# Top border
for x in range(W):
    img.putpixel((x, 0), (*frame_col, 255))
    img.putpixel((x, 1), (*frame_col, 255))
# Bottom border (above info bar)
for x in range(W):
    img.putpixel((x, H - 24), (*frame_col, 255))
# Left/right borders
for y in range(H):
    img.putpixel((0, y), (*frame_col, 255))
    img.putpixel((1, y), (*frame_col, 255))
    img.putpixel((W - 1, y), (*frame_col, 255))
    img.putpixel((W - 2, y), (*frame_col, 255))

# Corner flourishes
corner_pixels = [(2, 2), (3, 2), (2, 3), (4, 2), (2, 4), (3, 3)]
bright_frame = (80, 80, 140)
for dx, dy in corner_pixels:
    # Top-left
    img.putpixel((dx, dy), (*bright_frame, 255))
    # Top-right
    img.putpixel((W - 1 - dx, dy), (*bright_frame, 255))
    # Bottom-left
    img.putpixel((dx, H - 25 - dy), (*bright_frame, 255))
    # Bottom-right
    img.putpixel((W - 1 - dx, H - 25 - dy), (*bright_frame, 255))

# === STARS in upper dark area ===
for i in range(25):
    sx = rng.randint(5, W - 5)
    sy = rng.randint(3, 55)
    brightness = rng.randint(150, 255)
    # Avoid drawing over text area
    old = img.getpixel((sx, sy))
    if old[0] < 40 and old[1] < 60:
        img.putpixel((sx, sy), (brightness, brightness, brightness, 255))
        if rng.random() < 0.3:
            # Cross sparkle
            for d in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = sx + d[0], sy + d[1]
                if 0 <= nx < W and 0 <= ny < H:
                    img.putpixel((nx, ny), (brightness // 2, brightness // 2, brightness // 2, 255))

# === Rising CH4 gas particles (from bottom, dramatic) ===
for i in range(15):
    gx = rng.randint(100, 380)
    gy = rng.randint(140, 230)
    # Small red-orange rising particle
    c = PAL["ch4_r"] if rng.random() < 0.5 else PAL["fe_o"]
    for dy in range(-2, 3):
        for dx in range(-1, 2):
            px, py = gx + dx, gy + dy
            if 0 <= px < W and 0 <= py < H:
                old = img.getpixel((px, py))
                # Only on dark areas
                if old[0] < 100 and old[1] < 100:
                    a = max(0, 60 - abs(dy) * 20 - abs(dx) * 15)
                    nr = min(255, old[0] + (c[0] * a) // 255)
                    ng = min(255, old[1] + (c[1] * a) // 255)
                    nb = min(255, old[2] + (c[2] * a) // 255)
                    img.putpixel((px, py), (nr, ng, nb, 255))

# === SCALE UP 2x for final output ===
final = img.resize((960, 540), Image.NEAREST)

# Save
output_path = "/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/game/builds"
import os
os.makedirs(output_path, exist_ok=True)

final.save(f"{output_path}/cover_art.png")
# Also save to docs for easy access
final.save("/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/docs/ARKE_cover_art.png")

print(f"Cover art saved!")
print(f"  {output_path}/cover_art.png (960x540)")
print(f"  docs/ARKE_cover_art.png")
