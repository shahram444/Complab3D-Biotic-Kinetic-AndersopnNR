#!/usr/bin/env python3
"""Generate PowerPoint slides: Rival AI Flowchart + Code Reference."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ── Color palette ──────────────────────────────────────────────────────────
BG        = RGBColor(0x0A, 0x0E, 0x1A)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
GRAY      = RGBColor(0x88, 0x88, 0x99)
GOLD      = RGBColor(0xFF, 0xD7, 0x00)
TEAL      = RGBColor(0x2A, 0xCF, 0xAF)
RED       = RGBColor(0xE0, 0x60, 0x60)
RED_DARK  = RGBColor(0xB0, 0x30, 0x30)
BLUE      = RGBColor(0x4F, 0xA4, 0xFF)
GREEN     = RGBColor(0x4F, 0xDF, 0x6F)
ORANGE    = RGBColor(0xEF, 0x8F, 0x3F)
PURPLE    = RGBColor(0xCF, 0x6F, 0xFF)
DARK_BOX  = RGBColor(0x14, 0x18, 0x28)
BORDER    = RGBColor(0x2A, 0x2E, 0x42)
CODE_BG   = RGBColor(0x10, 0x14, 0x22)
CYAN      = RGBColor(0x50, 0xB0, 0xC0)
YELLOW    = RGBColor(0xFF, 0xFF, 0x5F)


def set_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_box(slide, left, top, w, h, fill_color, border_color=None, border_w=Pt(2)):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = border_w
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_diamond(slide, left, top, w, h, fill_color, border_color):
    shape = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, left, top, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(2)
    shape.shadow.inherit = False
    return shape


def set_text(shape, text, size=12, color=WHITE, bold=False, align=PP_ALIGN.CENTER):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = None
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = "Consolas"
    return tf


def add_text_multi(shape, lines, default_size=11, default_color=WHITE):
    """lines = [(text, size, color, bold), ...]"""
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    for i, line_data in enumerate(lines):
        text = line_data[0]
        sz = line_data[1] if len(line_data) > 1 else default_size
        col = line_data[2] if len(line_data) > 2 else default_color
        bld = line_data[3] if len(line_data) > 3 else False
        al = line_data[4] if len(line_data) > 4 else PP_ALIGN.CENTER
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = al
        p.space_after = Pt(2)
        run = p.add_run()
        run.text = text
        run.font.size = Pt(sz)
        run.font.color.rgb = col
        run.font.bold = bld
        run.font.name = "Consolas"


def add_arrow(slide, start_x, start_y, end_x, end_y, color=GRAY, width=Pt(2)):
    connector = slide.shapes.add_connector(
        1, start_x, start_y, end_x, end_y)  # 1 = straight
    connector.line.color.rgb = color
    connector.line.width = width
    # Add arrowhead
    connector.end_x = end_x
    connector.end_y = end_y
    return connector


def add_line(slide, x1, y1, x2, y2, color=GRAY, width=Pt(2)):
    shape = slide.shapes.add_connector(1, x1, y1, x2, y2)
    shape.line.color.rgb = color
    shape.line.width = width
    return shape


def add_free_text(slide, left, top, w, h, text, size=11, color=WHITE, bold=False, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = "Consolas"
    return txBox


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1: FLOWCHART
# ══════════════════════════════════════════════════════════════════════════════
slide1 = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
set_bg(slide1, BG)

# Title
add_free_text(slide1, Inches(0.5), Inches(0.2), Inches(12), Inches(0.5),
              "Rival Microbe AI — Decision Flowchart", 28, GOLD, True, PP_ALIGN.CENTER)
add_free_text(slide1, Inches(0.5), Inches(0.7), Inches(12), Inches(0.35),
              "rival.gd  →  do_move()  called every 0.4 seconds", 14, GRAY, False, PP_ALIGN.CENTER)

# ── Flowchart layout ──────────────────────────────────────────────────────
# Center column x positions
cx = Inches(5.8)   # center of chart
bw = Inches(2.6)   # box width
bh = Inches(0.7)   # box height
dw = Inches(2.8)   # diamond width
dh = Inches(1.0)   # diamond height

# Y positions for each row
y0 = Inches(1.2)   # START
y1 = Inches(2.1)   # Roll random
y2 = Inches(3.2)   # Decision 1: Seek?
y3 = Inches(4.5)   # Decision 2: Track?
y4 = Inches(5.7)   # Decision 3: Flow?
y5 = Inches(6.5)   # WANDER (fallback)

# Action boxes x positions (left and right of diamonds)
ax_left = Inches(1.2)
ax_right = Inches(10.0)

# ── START box ──
start = add_box(slide1, cx - Inches(1.0), y0, Inches(2.0), Inches(0.55), RED_DARK, RED, Pt(2))
set_text(start, "do_move()", 14, WHITE, True)

# Arrow: START → Roll
add_line(slide1, cx, y0 + Inches(0.55), cx, y1, GRAY)

# ── Roll random ──
roll = add_box(slide1, cx - Inches(1.3), y1, Inches(2.6), Inches(0.6), DARK_BOX, BORDER)
add_text_multi(roll, [
    ("var roll = randf()", 12, CYAN, True),
    ("Random 0.0 — 1.0", 10, GRAY),
])

# Arrow: Roll → Diamond 1
add_line(slide1, cx, y1 + Inches(0.6), cx, y2, GRAY)

# ── DECISION 1: SEEK FOOD ──
d1 = add_diamond(slide1, cx - Inches(1.4), y2, dw, dh, RGBColor(0x0F, 0x15, 0x25), GREEN)
add_text_multi(d1, [
    ("roll < 45-75%?", 11, GREEN, True),
    ("(seek_chance)", 9, GRAY),
])

# YES arrow → SEEK FOOD action box (left)
add_line(slide1, cx - Inches(1.4), y2 + Inches(0.5), ax_left + Inches(2.6), y2 + Inches(0.5), GREEN)
seek_box = add_box(slide1, ax_left, y2 - Inches(0.05), Inches(2.6), Inches(1.1), RGBColor(0x0A, 0x20, 0x10), GREEN)
add_text_multi(seek_box, [
    ("SEEK FOOD", 14, GREEN, True),
    ("_seek_substrate()", 10, CYAN),
    ("Find nearest substrate", 9, GRAY),
    ("within 12 tiles", 9, GRAY),
    ("Step toward it", 9, GRAY),
])
# YES label
add_free_text(slide1, cx - Inches(2.3), y2 + Inches(0.15), Inches(0.6), Inches(0.3),
              "YES", 10, GREEN, True, PP_ALIGN.CENTER)

# NO arrow → Diamond 2
add_line(slide1, cx, y2 + dh, cx, y3, GRAY)
add_free_text(slide1, cx + Inches(0.1), y2 + dh - Inches(0.05), Inches(0.5), Inches(0.3),
              "NO", 10, RED, True)

# ── DECISION 2: TRACK ARKE ──
d2 = add_diamond(slide1, cx - Inches(1.4), y3, dw, dh, RGBColor(0x0F, 0x15, 0x25), TEAL)
add_text_multi(d2, [
    ("roll < +15%?", 11, TEAL, True),
    ("player < 10 tiles", 9, GRAY),
])

# YES arrow → TRACK ARKE action box (right)
add_line(slide1, cx + Inches(1.4), y3 + Inches(0.5), ax_right, y3 + Inches(0.5), TEAL)
track_box = add_box(slide1, ax_right, y3 - Inches(0.05), Inches(2.6), Inches(1.1), RGBColor(0x0A, 0x18, 0x18), TEAL)
add_text_multi(track_box, [
    ("TRACK ARKE", 14, TEAL, True),
    ("_step_toward()", 10, CYAN),
    ("Move toward player", 9, GRAY),
    ("PLAYER_SENSE = 10", 9, GRAY),
    ("Compete for food zone", 9, GRAY),
])
add_free_text(slide1, cx + Inches(1.5), y3 + Inches(0.15), Inches(0.6), Inches(0.3),
              "YES", 10, TEAL, True, PP_ALIGN.CENTER)

# NO arrow → Diamond 3
add_line(slide1, cx, y3 + dh, cx, y4, GRAY)
add_free_text(slide1, cx + Inches(0.1), y3 + dh - Inches(0.05), Inches(0.5), Inches(0.3),
              "NO", 10, RED, True)

# ── DECISION 3: RIDE FLOW ──
d3 = add_diamond(slide1, cx - Inches(1.4), y4, dw, dh, RGBColor(0x0F, 0x15, 0x25), BLUE)
add_text_multi(d3, [
    ("flow > 0.1 &", 11, BLUE, True),
    ("40% chance?", 11, BLUE, True),
])

# YES arrow → RIDE FLOW action box (left)
add_line(slide1, cx - Inches(1.4), y4 + Inches(0.5), ax_left + Inches(2.6), y4 + Inches(0.5), BLUE)
flow_box = add_box(slide1, ax_left, y4 - Inches(0.05), Inches(2.6), Inches(1.1), RGBColor(0x0A, 0x12, 0x22), BLUE)
add_text_multi(flow_box, [
    ("RIDE FLOW", 14, BLUE, True),
    ("get_flow(tile_x, tile_y)", 10, CYAN),
    ("Follow flow_dir", 9, GRAY),
    ("speed > 0.1 required", 9, GRAY),
    ("40% chance per tick", 9, GRAY),
])
add_free_text(slide1, cx - Inches(2.3), y4 + Inches(0.15), Inches(0.6), Inches(0.3),
              "YES", 10, BLUE, True, PP_ALIGN.CENTER)

# NO arrow → WANDER
add_line(slide1, cx, y4 + dh, cx, y5, GRAY)
add_free_text(slide1, cx + Inches(0.1), y4 + dh - Inches(0.05), Inches(0.5), Inches(0.3),
              "NO", 10, RED, True)

# ── WANDER (fallback) ──
wander = add_box(slide1, cx - Inches(1.3), y5, Inches(2.6), Inches(0.65), RGBColor(0x20, 0x15, 0x0A), ORANGE)
add_text_multi(wander, [
    ("WANDER", 14, ORANGE, True),
    ("Try preferred dir → shuffle random", 9, GRAY),
])

# ── RIGHT SIDE: Hunger mechanic note ──
hunger_box = add_box(slide1, Inches(10.0), y2 - Inches(0.5), Inches(2.8), Inches(1.5),
                      RGBColor(0x1A, 0x10, 0x10), RED)
add_text_multi(hunger_box, [
    ("HUNGER SYSTEM", 13, RED, True),
    ("", 6, GRAY),
    ("hunger += delta * 0.3", 10, CYAN),
    ("", 6, GRAY),
    ("seek_chance =", 10, WHITE),
    ("  0.45 + hunger * 0.05", 10, YELLOW),
    ("  clamped to [0.45, 0.75]", 9, GRAY),
    ("", 6, GRAY),
    ("Resets to 0 on eat", 9, GREEN),
])

# ── Footer ──
add_free_text(slide1, Inches(0.3), Inches(7.1), Inches(12), Inches(0.3),
              "ARKE: Guardians of Earth  |  rival.gd  →  do_move() lines 47-115  |  Based on CompLaB3D Research",
              10, GRAY, False, PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2: CODE REFERENCE WITH INLINE COMMENTS
# ══════════════════════════════════════════════════════════════════════════════
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide2, BG)

# Title
add_free_text(slide2, Inches(0.5), Inches(0.15), Inches(12), Inches(0.5),
              "Rival AI — Code Reference with Inline Comments", 26, GOLD, True, PP_ALIGN.CENTER)
add_free_text(slide2, Inches(0.5), Inches(0.6), Inches(12), Inches(0.3),
              "rival.gd  —  Key sections annotated", 13, GRAY, False, PP_ALIGN.CENTER)

# Code sections
code_sections = [
    {
        "title": "1. CONSTANTS & STATE",
        "color": PURPLE,
        "code": [
            ("const SENSE_RANGE := 12", "# How far rival can 'smell' food (tiles)"),
            ("const PLAYER_SENSE := 10", "# Detection radius for ARKE (tiles)"),
            ("var hunger: float = 0.0", "# Increases over time → more aggressive"),
            ("var move_dir: int = 1", "# Preferred wander direction (1-4)"),
        ],
        "line_ref": "Lines 4-17"
    },
    {
        "title": "2. HUNGER GROWTH (every frame)",
        "color": RED,
        "code": [
            ("hunger += delta * 0.3", "# Hunger rises 0.3/sec continuously"),
        ],
        "line_ref": "Line 30"
    },
    {
        "title": "3. SEEK FOOD (45-75% chance)",
        "color": GREEN,
        "code": [
            ("var seek_chance = clampf(", ""),
            ("  0.45 + hunger * 0.05, 0.45, 0.75)", "# More hungry → more likely to seek"),
            ("if roll < seek_chance:", "# Random roll decides behavior"),
            ("  var best = _seek_substrate(subs)", "# Find nearest substrate in range"),
            ("  for s in subs:", "# Loop all substrates"),
            ("    if dist < SENSE_RANGE * T:", "# Within 12-tile smell radius?"),
            ("      best_pos = s.position", "# Remember closest one"),
            ("  return _step_toward(dx, dy)", "# Move one tile toward food"),
        ],
        "line_ref": "Lines 53-64, 117-132"
    },
    {
        "title": "4. TRACK ARKE (15% chance)",
        "color": TEAL,
        "code": [
            ("if roll < seek_chance + 0.15:", "# 15% chance to chase player"),
            ("  if absi(dx)+absi(dy) < PLAYER_SENSE:", "# Player within 10 tiles?"),
            ("    var toward = _step_toward(dx, dy)", "# Move toward ARKE's position"),
            ("    _move_to(ntx, nty)", "# Execute the move"),
        ],
        "line_ref": "Lines 67-80"
    },
    {
        "title": "5. RIDE FLOW (40% when available)",
        "color": BLUE,
        "code": [
            ("var flow = world_ref.get_flow(tile_x, tile_y)", "# Get flow at current tile"),
            ("if flow['speed'] > 0.1 and randf() < 0.4:", "# Flow exists + 40% chance"),
            ("  var fd = flow_dirs[flow['dir']]", "# Get flow direction vector"),
            ("  _move_to(tile_x + fd.x, tile_y + fd.y)", "# Ride the current"),
        ],
        "line_ref": "Lines 86-96"
    },
    {
        "title": "6. WANDER (fallback)",
        "color": ORANGE,
        "code": [
            ("var preferred = dirs[move_dir - 1]", "# Try preferred direction first"),
            ("if is_walkable_tile(get_tile(ntx, nty)):", "# Can we go that way?"),
            ("  _move_to(ntx, nty)", "# Move there"),
            ("  if randf() < 0.25: move_dir = randi(1,4)", "# 25% chance: pick new direction"),
            ("# else: dirs.shuffle() and try each", "# Fallback: random walkable tile"),
        ],
        "line_ref": "Lines 98-115"
    },
    {
        "title": "7. HUNGER RESET",
        "color": YELLOW,
        "code": [
            ("func on_eat() -> void:", "# Called when rival eats a substrate"),
            ("  eat_flash = 0.3", "# Visual feedback (red flash)"),
            ("  hunger = 0.0", "# Reset hunger → less aggressive"),
        ],
        "line_ref": "Lines 167-169"
    },
]

# Layout: 2 columns
col_w = Inches(6.1)
col_gap = Inches(0.3)
left_x = Inches(0.4)
right_x = left_x + col_w + col_gap
start_y = Inches(1.0)
section_gap = Inches(0.08)

cur_y_left = start_y
cur_y_right = start_y

for idx, section in enumerate(code_sections):
    # Alternate columns
    if idx < 4:
        cur_x = left_x
        cur_y = cur_y_left
    else:
        cur_x = right_x
        cur_y = cur_y_right

    # Section title bar
    title_h = Inches(0.32)
    title_box = add_box(slide2, cur_x, cur_y, col_w, title_h,
                        RGBColor(0x0A, 0x10, 0x1A), section["color"], Pt(1.5))
    tf = title_box.text_frame
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = f"  {section['title']}"
    run.font.size = Pt(11)
    run.font.color.rgb = section["color"]
    run.font.bold = True
    run.font.name = "Consolas"
    # Line ref on same line
    run2 = p.add_run()
    run2.text = f"    ({section['line_ref']})"
    run2.font.size = Pt(9)
    run2.font.color.rgb = GRAY
    run2.font.name = "Consolas"

    cur_y += title_h

    # Code lines
    code_h_per_line = Inches(0.22)
    code_h = code_h_per_line * len(section["code"]) + Inches(0.08)
    code_box = add_box(slide2, cur_x, cur_y, col_w, code_h,
                       CODE_BG, RGBColor(0x1A, 0x1E, 0x30), Pt(1))

    tf = code_box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Pt(8)
    tf.margin_top = Pt(4)

    for ci, (code, comment) in enumerate(section["code"]):
        if ci == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(1)
        p.space_before = Pt(1)

        # Code part
        run = p.add_run()
        run.text = code
        run.font.size = Pt(10)
        run.font.color.rgb = CYAN
        run.font.name = "Consolas"

        # Comment part
        if comment:
            run2 = p.add_run()
            run2.text = f"  {comment}"
            run2.font.size = Pt(9)
            run2.font.color.rgb = RGBColor(0x60, 0x70, 0x50)
            run2.font.name = "Consolas"

    cur_y += code_h + section_gap

    if idx < 4:
        cur_y_left = cur_y
    else:
        cur_y_right = cur_y

# Footer
add_free_text(slide2, Inches(0.3), Inches(7.1), Inches(12), Inches(0.3),
              "ARKE: Guardians of Earth  |  rival.gd  |  GDScript (Godot 4.2+)  |  Based on CompLaB3D Research",
              10, GRAY, False, PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3: PRIORITY SUMMARY (clean visual)
# ══════════════════════════════════════════════════════════════════════════════
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide3, BG)

add_free_text(slide3, Inches(0.5), Inches(0.2), Inches(12), Inches(0.5),
              "Rival AI — Decision Priority Summary", 28, GOLD, True, PP_ALIGN.CENTER)

# Priority cascade boxes
priorities = [
    ("1", "SEEK FOOD", "45–75%", "Detect substrates within 12 tiles\nHunger increases chance over time\n_seek_substrate() → _step_toward()", GREEN),
    ("2", "TRACK ARKE", "15%", "Follow player within 10 tiles\nCompete for same food zone\n_step_toward(player_pos)", TEAL),
    ("3", "RIDE FLOW", "~40%*", "If flow speed > 0.1 at current tile\n40% chance to follow current\nUses world pressure-driven flow field", BLUE),
    ("4", "WANDER", "Fallback", "Try preferred direction first\n25% chance to change direction\nIf blocked → shuffle & try random", ORANGE),
]

box_w = Inches(2.8)
box_h = Inches(3.2)
total_w = box_w * 4 + Inches(0.4) * 3
start_x = (Inches(13.333) - total_w) / 2
box_y = Inches(1.5)

for i, (num, title, chance, desc, color) in enumerate(priorities):
    bx = int(start_x) + i * int(box_w + Inches(0.4))

    # Main box
    box = add_box(slide3, bx, box_y, box_w, box_h, DARK_BOX, color, Pt(2))

    # Priority number circle
    circle = slide3.shapes.add_shape(MSO_SHAPE.OVAL, bx + Inches(1.05), box_y - Inches(0.25), Inches(0.5), Inches(0.5))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    set_text(circle, num, 18, BG, True)

    # Content
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_top = Pt(30)
    tf.margin_left = Pt(12)
    tf.margin_right = Pt(12)

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title
    run.font.size = Pt(18)
    run.font.color.rgb = color
    run.font.bold = True
    run.font.name = "Consolas"

    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(8)
    run2 = p2.add_run()
    run2.text = f"Chance: {chance}"
    run2.font.size = Pt(13)
    run2.font.color.rgb = GOLD
    run2.font.bold = True
    run2.font.name = "Consolas"

    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(16)
    run3 = p3.add_run()
    run3.text = desc
    run3.font.size = Pt(10)
    run3.font.color.rgb = GRAY
    run3.font.name = "Consolas"

    # Arrow between boxes (except last)
    if i < 3:
        arrow_x = bx + box_w + Inches(0.05)
        arrow_y = box_y + box_h / 2
        add_free_text(slide3, arrow_x, arrow_y - Inches(0.15), Inches(0.3), Inches(0.3),
                      "→", 20, GRAY, True, PP_ALIGN.CENTER)

# Footnote
add_free_text(slide3, Inches(0.5), Inches(5.2), Inches(12), Inches(0.5),
              "* Ride Flow only triggers if the current tile has flow speed > 0.1", 11, GRAY, False, PP_ALIGN.CENTER)

# Hunger note at bottom
hunger_note = add_box(slide3, Inches(3.5), Inches(5.7), Inches(6.3), Inches(1.2),
                       RGBColor(0x1A, 0x10, 0x10), RED, Pt(1.5))
add_text_multi(hunger_note, [
    ("HUNGER MECHANIC  (affects Priority #1)", 12, RED, True),
    ("", 4, GRAY),
    ("hunger += 0.3/sec  →  seek_chance grows from 45% to 75%", 11, CYAN),
    ("on_eat() resets hunger to 0  →  rival calms down after feeding", 11, GREEN),
    ("Effect: starving rivals become aggressive food-seekers", 10, GRAY),
])

# Footer
add_free_text(slide3, Inches(0.3), Inches(7.1), Inches(12), Inches(0.3),
              "ARKE: Guardians of Earth  |  rival.gd  |  GDScript (Godot 4.2+)  |  Based on CompLaB3D Research",
              10, GRAY, False, PP_ALIGN.CENTER)


# ── SAVE ──────────────────────────────────────────────────────────────────────
output_path = "/home/user/Complab3D-Biotic-Kinetic-AndersopnNR/docs/Rival_AI_Flowchart.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
