extends Node2D
## HUD overlay - health, energy, growth bars, score, minimap, all menus.

var game_ref: Node2D = null  # Reference to main.gd node

func set_game_ref(ref: Node2D) -> void:
	game_ref = ref

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	if !game_ref:
		return

	match game_ref.state:
		GameData.State.BOOT: _draw_boot()
		GameData.State.TITLE: _draw_title()
		GameData.State.NARRATIVE: _draw_narrative()
		GameData.State.MISSION_BRIEF: _draw_mission_brief()
		GameData.State.LEVEL_INTRO: _draw_level_intro()
		GameData.State.PLAYING:
			_draw_hud()
			_draw_tutorial()
			_draw_screen_effects()
		GameData.State.PAUSED:
			_draw_hud()
			_draw_pause()
		GameData.State.LEVEL_COMPLETE:
			_draw_hud()
			_draw_level_complete()
		GameData.State.SCIENCE_POPUP:
			_draw_hud()
			_draw_science_popup()
		GameData.State.GAME_OVER:
			_draw_hud()
			_draw_game_over()
		GameData.State.VICTORY: _draw_victory()

# ── HELPER ───────────────────────────────────────────────────────────────────

func _text(text: String, x: float, y: float, color: Color = Color.WHITE,
		size: int = 16, halign: int = 0) -> void:
	var font = ThemeDB.fallback_font
	if !font:
		return
	var pos = Vector2(x, y + size)
	if halign == 1:  # center
		var w = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		pos.x -= w * 0.5
	elif halign == 2:  # right
		var w = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		pos.x -= w
	# Shadow
	draw_string(font, pos + Vector2(2, 2), text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(0, 0, 0, 0.8))
	draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _box(x: float, y: float, w: float, h: float, bg: Color, border: Color) -> void:
	draw_rect(Rect2(x, y, w, h), bg)
	draw_rect(Rect2(x, y, w, h), border, false, 2.0)

# ── SCREENS ──────────────────────────────────────────────────────────────────

func _draw_boot() -> void:
	draw_rect(Rect2(0, 0, 960, 540), Color.BLACK)
	var alpha = clampf(game_ref.boot_timer, 0, 1)
	_text("CompLaB3D", 480, 160, Color(0.37, 0.77, 0.92, alpha), 24, 1)
	_text("presents", 480, 200, Color(0.53, 0.53, 0.53, alpha), 16, 1)
	if game_ref.boot_timer > 0.8:
		_text("A Game Based on Real Science", 480, 270, Color(0.37, 0.81, 0.37, clampf((game_ref.boot_timer - 0.8) * 2, 0, 1)), 16, 1)

func _draw_title() -> void:
	var t = GameData.game_time
	draw_rect(Rect2(0, 0, 960, 540), Color(0.024, 0.047, 0.094))

	# Floating particles
	for i in range(20):
		var px = fmod(t * 15 + i * 30, 1000) - 20
		var py = 80 + sin(t + i * 1.7) * 180
		draw_rect(Rect2(px, py, 6, 6), Color(0.1, 0.23, 0.4, 0.3))

	# Title
	var ty = 70 + sin(t * 1.5) * 6
	_text("ARKE", 480, ty, Color(0.16, 0.81, 0.69), 40, 1)
	_text("Guardians of Earth", 480, ty + 56, Color(0.77, 0.63, 0.35), 20, 1)

	# Methi sprite
	var tex = SpriteFactory.get_tex("methi_down")
	if tex:
		draw_texture_rect(tex, Rect2(464, 200 + sin(t * 2) * 8, 32, 32), false)

	# Blink prompt
	if sin(t * 3) > 0:
		_text("PRESS ENTER", 480, 300, Color(1, 0.84, 0), 16, 1)

	_text("Based on CompLaB3D Research", 480, 380, Color(0.53, 0.53, 0.53), 14, 1)
	_text("Pore-Scale Reactive Transport", 480, 404, Color(0.4, 0.4, 0.4), 12, 1)
	_text("University of Georgia", 480, 450, Color(0.27, 0.27, 0.27), 12, 1)

func _draw_narrative() -> void:
	if !game_ref or game_ref.dialogue_idx >= GameData.CUTSCENE.size():
		return

	var t = GameData.game_time
	var line = GameData.CUTSCENE[game_ref.dialogue_idx]
	var speaker: String = line["speaker"]
	var full_text: String = line["text"]
	var shown_text: String = full_text.substr(0, game_ref.dialogue_char)

	# Dark background with pore-like scene illustration
	draw_rect(Rect2(0, 0, 960, 540), Color(0.02, 0.02, 0.06))

	# Scene illustration area (top portion)
	_draw_cutscene_scene(speaker, t)

	# === DIALOGUE BOX (bottom 180px, visual novel style) ===
	var box_y = 360.0
	var box_h = 180.0
	# Box background
	draw_rect(Rect2(0, box_y, 960, box_h), Color(0.02, 0.02, 0.08, 0.95))
	# Top border with glow
	draw_rect(Rect2(0, box_y, 960, 4), Color(0.2, 0.3, 0.5, 0.8))
	draw_rect(Rect2(0, box_y + 4, 960, 2), Color(0.1, 0.15, 0.3, 0.4))

	# Portrait frame (left side)
	var portrait_x = 20.0
	var portrait_y = box_y + 16.0
	var portrait_size = 128.0

	# Portrait border
	draw_rect(Rect2(portrait_x - 4, portrait_y - 4, portrait_size + 8, portrait_size + 8),
		Color(0.15, 0.2, 0.35))
	draw_rect(Rect2(portrait_x - 2, portrait_y - 2, portrait_size + 4, portrait_size + 4),
		Color(0.05, 0.05, 0.12))

	# Draw portrait
	var tex_key = "elder" if speaker == "ELDER" else "methi_down"
	var tex = SpriteFactory.get_tex(tex_key)
	if tex:
		draw_texture_rect(tex, Rect2(portrait_x, portrait_y, portrait_size, portrait_size), false)
	elif speaker == "":
		# Narration - draw starfield in portrait
		draw_rect(Rect2(portrait_x, portrait_y, portrait_size, portrait_size), Color(0.02, 0.02, 0.06))
		for i in range(8):
			var sx = portrait_x + fmod(sin(i * 37) * 0.5 + 0.5, 1.0) * portrait_size
			var sy = portrait_y + fmod(cos(i * 53) * 0.5 + 0.5, 1.0) * portrait_size
			draw_rect(Rect2(sx, sy, 2, 2), Color(1, 1, 1, 0.5 + sin(t * 2 + i) * 0.3))

	# Speaker name
	var name_x = portrait_x + portrait_size + 24
	var name_y = box_y + 12
	var name_color: Color
	var name_str: String
	if speaker == "ELDER":
		name_str = "ARCHAEON PRIME"
		name_color = Color(0.28, 0.28, 0.82)
	elif speaker == "ARKE":
		name_str = "ARKE"
		name_color = Color(0.16, 0.81, 0.69)
	else:
		name_str = ""
		name_color = Color(0.5, 0.5, 0.7)

	if name_str != "":
		# Name background
		var name_w = 200.0
		draw_rect(Rect2(name_x - 4, name_y - 2, name_w, 24), Color(name_color, 0.15))
		draw_rect(Rect2(name_x - 4, name_y - 2, name_w, 24), name_color * Color(1,1,1,0.4), false, 2.0)
		_text(name_str, name_x + 4, name_y, name_color, 16)

	# Dialogue text (typewriter)
	var text_x = name_x
	var text_y = name_y + 32
	var text_lines = shown_text.split("\n")
	for i in range(text_lines.size()):
		var tc = Color(0.85, 0.85, 0.95) if speaker != "" else Color(0.6, 0.7, 0.85)
		_text(text_lines[i], text_x, text_y + i * 24, tc, 14)

	# Blinking cursor / advance prompt
	if game_ref.dialogue_char >= full_text.length():
		if sin(t * 4) > 0:
			_text(">>", 920, box_y + box_h - 28, Color(1, 0.84, 0), 14, 2)
	else:
		# Typing cursor
		var cursor_x = text_x + 8 * (shown_text.length() - shown_text.rfind("\n") - 1)
		var cursor_y_pos = text_y + (text_lines.size() - 1) * 24
		if sin(t * 8) > 0:
			draw_rect(Rect2(cursor_x, cursor_y_pos + 2, 8, 14), Color(1, 1, 1, 0.6))

	# Progress indicator
	_text("%d/%d" % [game_ref.dialogue_idx + 1, GameData.CUTSCENE.size()],
		920, box_y + 12, Color(0.3, 0.3, 0.4), 12, 2)

func _draw_cutscene_scene(speaker: String, t: float) -> void:
	# Draw a pore-space illustration in the top area
	var scene_h = 350.0

	# Pore-like background with grain particles
	for i in range(25):
		var gx = fmod(sin(i * 47.3) * 0.5 + 0.5, 1.0) * 960
		var gy = fmod(cos(i * 31.7) * 0.5 + 0.5, 1.0) * scene_h
		var gr = 16 + sin(i * 17) * 8
		draw_rect(Rect2(gx - gr, gy - gr, gr * 2, gr * 2),
			Color(0.15, 0.1, 0.05, 0.4))
		draw_rect(Rect2(gx - gr + 2, gy - gr + 2, gr * 2 - 4, gr * 2 - 4),
			Color(0.2, 0.15, 0.08, 0.3))

	# Water/pore space between grains (subtle blue)
	for i in range(15):
		var wx = fmod(sin(i * 89.1 + t * 0.3) * 0.5 + 0.5, 1.0) * 960
		var wy = fmod(cos(i * 67.3 + t * 0.2) * 0.5 + 0.5, 1.0) * scene_h
		draw_rect(Rect2(wx, wy, 40, 4), Color(0.1, 0.2, 0.4, 0.2))

	# Character illustrations based on speaker
	if speaker == "ELDER":
		# Elder on the left, larger, with glow
		var elder_tex = SpriteFactory.get_tex("elder")
		if elder_tex:
			var bob = sin(t * 1.5) * 6
			draw_texture_rect(elder_tex, Rect2(120, 120 + bob, 160, 160), false,
				Color(1, 1, 1, 0.9))
			# Bioluminescent glow
			draw_rect(Rect2(110, 110 + bob, 180, 180),
				Color(0.2, 0.2, 0.7, 0.08 + sin(t * 2) * 0.04))
		# ARKE listening on the right
		var methi_tex = SpriteFactory.get_tex("methi_down")
		if methi_tex:
			var bob2 = sin(t * 2 + 1) * 4
			draw_texture_rect(methi_tex, Rect2(700, 170 + bob2, 96, 96), false,
				Color(1, 1, 1, 0.85))
	elif speaker == "ARKE":
		# ARKE on the right, speaking
		var methi_tex = SpriteFactory.get_tex("methi_right")
		if methi_tex:
			var bob = sin(t * 2) * 6
			draw_texture_rect(methi_tex, Rect2(680, 110 + bob, 160, 160), false,
				Color(1, 1, 1, 0.9))
		# Elder listening on the left
		var elder_tex = SpriteFactory.get_tex("elder")
		if elder_tex:
			var bob2 = sin(t * 1.5 + 1) * 4
			draw_texture_rect(elder_tex, Rect2(140, 160 + bob2, 96, 96), false,
				Color(1, 1, 1, 0.7))
	else:
		# Narration - atmospheric scene
		# Rising gas particles
		for i in range(10):
			var gx = 200 + i * 70
			var gy = scene_h - fmod(t * 20 + i * 40, scene_h + 20)
			var gc = Color(1, 0.3, 0.3, 0.3) if i % 2 == 0 else Color(0.3, 1, 0.3, 0.2)
			draw_rect(Rect2(gx, gy, 6, 12), gc)
			draw_rect(Rect2(gx - 2, gy + 12, 10, 4), gc * Color(1,1,1,0.5))

func _draw_mission_brief() -> void:
	if !game_ref:
		return
	var briefs = GameData.MISSION_BRIEFS
	var level_briefs: Array = []
	if GameData.current_level < briefs.size():
		level_briefs = briefs[GameData.current_level]
	if level_briefs.size() == 0 or game_ref.mission_idx >= level_briefs.size():
		return

	var t = GameData.game_time
	var line = level_briefs[game_ref.mission_idx]
	var speaker: String = line["speaker"]
	var full_text: String = line["text"]
	var shown_text: String = full_text.substr(0, game_ref.mission_char)

	# Dark background
	draw_rect(Rect2(0, 0, 960, 540), Color(0.02, 0.02, 0.06))

	# Level title at top
	var def = GameData.get_level_def()
	var fade = clampf(game_ref.mission_timer * 3, 0, 1)
	_text("MISSION BRIEFING", 480, 16, Color(0.31, 0.64, 0.94, fade), 20, 1)
	_text("Level %d: %s" % [GameData.current_level + 1, def["title"]], 480, 50, Color(1, 0.84, 0, fade), 16, 1)

	# Scene illustration area (top center)
	_draw_mission_scene(speaker, t)

	# === DIALOGUE BOX (bottom 180px, visual novel style) ===
	var box_y = 360.0
	var box_h = 180.0
	# Box background
	draw_rect(Rect2(0, box_y, 960, box_h), Color(0.02, 0.02, 0.08, 0.95))
	# Top border with glow
	draw_rect(Rect2(0, box_y, 960, 4), Color(0.2, 0.3, 0.5, 0.8))
	draw_rect(Rect2(0, box_y + 4, 960, 2), Color(0.1, 0.15, 0.3, 0.4))

	# Portrait frame (left side)
	var portrait_x = 20.0
	var portrait_y = box_y + 16.0
	var portrait_size = 128.0

	# Portrait border
	var border_col = Color(0.15, 0.2, 0.35) if speaker == "ELDER" else Color(0.1, 0.3, 0.25)
	draw_rect(Rect2(portrait_x - 4, portrait_y - 4, portrait_size + 8, portrait_size + 8), border_col)
	draw_rect(Rect2(portrait_x - 2, portrait_y - 2, portrait_size + 4, portrait_size + 4),
		Color(0.05, 0.05, 0.12))

	# Draw portrait
	var tex_key = "elder" if speaker == "ELDER" else "methi_down"
	var tex = SpriteFactory.get_tex(tex_key)
	if tex:
		draw_texture_rect(tex, Rect2(portrait_x, portrait_y, portrait_size, portrait_size), false)

	# Speaker name
	var name_x = portrait_x + portrait_size + 24
	var name_y = box_y + 12
	var name_color: Color
	var name_str: String
	if speaker == "ELDER":
		name_str = "ARCHAEON PRIME"
		name_color = Color(0.28, 0.28, 0.82)
	else:
		name_str = "ARKE"
		name_color = Color(0.16, 0.81, 0.69)

	# Name background
	var name_w = 200.0
	draw_rect(Rect2(name_x - 4, name_y - 2, name_w, 24), Color(name_color, 0.15))
	draw_rect(Rect2(name_x - 4, name_y - 2, name_w, 24), name_color * Color(1,1,1,0.4), false, 2.0)
	_text(name_str, name_x + 4, name_y, name_color, 16)

	# Dialogue text (typewriter)
	var text_x = name_x
	var text_y = name_y + 32
	var text_lines = shown_text.split("\n")
	for i in range(text_lines.size()):
		var tc = Color(0.85, 0.85, 0.95)
		_text(text_lines[i], text_x, text_y + i * 24, tc, 14)

	# Blinking cursor / advance prompt
	if game_ref.mission_char >= full_text.length():
		if sin(t * 4) > 0:
			_text(">>", 920, box_y + box_h - 28, Color(1, 0.84, 0), 14, 2)
	else:
		# Typing cursor
		var cursor_x = text_x + 8 * (shown_text.length() - shown_text.rfind("\n") - 1)
		var cursor_y_pos = text_y + (text_lines.size() - 1) * 24
		if sin(t * 8) > 0:
			draw_rect(Rect2(cursor_x, cursor_y_pos + 2, 8, 14), Color(1, 1, 1, 0.6))

	# Progress indicator
	_text("%d/%d" % [game_ref.mission_idx + 1, level_briefs.size()],
		920, box_y + 12, Color(0.3, 0.3, 0.4), 12, 2)

func _draw_mission_scene(speaker: String, t: float) -> void:
	# Draw characters in the scene area above the dialogue box
	var scene_h = 280.0

	# Subtle pore-space background
	for i in range(15):
		var gx = fmod(sin(i * 47.3) * 0.5 + 0.5, 1.0) * 960
		var gy = 80 + fmod(cos(i * 31.7) * 0.5 + 0.5, 1.0) * scene_h
		var gr = 12 + sin(i * 17) * 6
		draw_rect(Rect2(gx - gr, gy - gr, gr * 2, gr * 2),
			Color(0.1, 0.08, 0.04, 0.3))

	# Water streaks
	for i in range(8):
		var wx = fmod(sin(i * 89.1 + t * 0.3) * 0.5 + 0.5, 1.0) * 960
		var wy = 80 + fmod(cos(i * 67.3 + t * 0.2) * 0.5 + 0.5, 1.0) * scene_h
		draw_rect(Rect2(wx, wy, 30, 3), Color(0.1, 0.2, 0.4, 0.15))

	if speaker == "ELDER":
		# Elder speaking, larger and centered-left with glow
		var elder_tex = SpriteFactory.get_tex("elder")
		if elder_tex:
			var bob = sin(t * 1.5) * 6
			draw_texture_rect(elder_tex, Rect2(180, 140 + bob, 140, 140), false,
				Color(1, 1, 1, 0.9))
			# Bioluminescent glow
			draw_rect(Rect2(170, 130 + bob, 160, 160),
				Color(0.2, 0.2, 0.7, 0.08 + sin(t * 2) * 0.04))
		# ARKE listening on the right
		var methi_tex = SpriteFactory.get_tex("methi_down")
		if methi_tex:
			var bob2 = sin(t * 2 + 1) * 4
			draw_texture_rect(methi_tex, Rect2(640, 180 + bob2, 96, 96), false,
				Color(1, 1, 1, 0.75))
	else:
		# ARKE speaking
		var methi_tex = SpriteFactory.get_tex("methi_right")
		if methi_tex:
			var bob = sin(t * 2) * 6
			draw_texture_rect(methi_tex, Rect2(620, 140 + bob, 140, 140), false,
				Color(1, 1, 1, 0.9))
		# Elder listening on the left
		var elder_tex = SpriteFactory.get_tex("elder")
		if elder_tex:
			var bob2 = sin(t * 1.5 + 1) * 4
			draw_texture_rect(elder_tex, Rect2(200, 180 + bob2, 96, 96), false,
				Color(1, 1, 1, 0.7))

func _draw_level_intro() -> void:
	var def = GameData.get_level_def()
	var env = def.get("env", 0)
	var info = GameData.WORLD_INTROS[env] if env < GameData.WORLD_INTROS.size() else GameData.WORLD_INTROS[0]
	var ep = GameData.get_env_pal()

	draw_rect(Rect2(0, 0, 960, 540), Color.html(ep["bg"]))

	var t = game_ref.intro_timer
	var fade = clampf(t * 2, 0, 1)

	_text(info["title"], 480, 40, Color(1, 1, 1, fade), 36, 1)
	_text(info["sub"], 480, 96, Color.html(ep["grain_l"]).lightened(0.3) * Color(1,1,1,fade), 20, 1)

	if t > 0.3:
		var a2 = clampf((t - 0.3) * 3, 0, 1)
		_text("Level %d: %s" % [GameData.current_level + 1, def["title"]],
			480, 140, Color(1, 0.84, 0, a2), 16, 1)

	if t > 0.5:
		var a3 = clampf((t - 0.5) * 2, 0, 1)
		var lines = info["text"].split("\n")
		for i in range(lines.size()):
			_text(lines[i], 80, 184 + i * 22, Color(0.78, 0.78, 0.91, a3), 14)

	if t > 1.0:
		var a4 = clampf((t - 1.0) * 2, 0, 1)
		# Show available substrates
		_text("Available substrates:", 80, 400, Color(0.53, 0.53, 0.53, a4), 14)
		var subs: Array = def.get("subs", [])
		for i in range(subs.size()):
			var sd = GameData.SUBSTRATES[subs[i]]
			_text("%s (%s) +%d energy" % [sd["name"], sd["formula"], sd["energy"]],
				120, 424 + i * 20, Color.html(sd["color"]) * Color(1,1,1,a4), 12)

		_text("Goal: Place %d colonies" % def["goal"],
			480, 496, Color(0.37, 0.81, 0.37, a4), 16, 1)

	if t > 1.5 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 480, 520, Color(1, 0.84, 0), 16, 1)

func _draw_hud() -> void:
	if !game_ref or !game_ref.player_node:
		return
	var p = game_ref.player_node
	var def = GameData.get_level_def()
	var hud_y = 476.0

	# Background
	draw_rect(Rect2(0, hud_y, 960, 64), Color(0.04, 0.04, 0.1, 0.88))
	draw_rect(Rect2(0, hud_y, 960, 2), Color(0.23, 0.23, 0.42))

	# HP bar
	_text("HP", 8, hud_y + 4, Color(0.78, 0.78, 0.91), 12)
	draw_rect(Rect2(40, hud_y + 6, 108, 14), Color(0.1, 0.1, 0.17))
	var hw = maxf(0, (p.health / GameData.BAL["max_health"]) * 104)
	var hc: Color
	if p.health > 60:
		hc = Color(0.27, 0.87, 0.37)   # green
	elif p.health > 35:
		hc = Color(0.94, 0.77, 0.27)   # yellow
	elif p.health > 15:
		hc = Color(0.94, 0.43, 0.17)   # orange
	else:
		hc = Color(0.94, 0.13, 0.13)   # red (critical)
		if sin(GameData.game_time * 8) > 0:
			hc = Color(1, 0.3, 0.3)    # flash when critical
	draw_rect(Rect2(42, hud_y + 8, hw, 10), hc)

	# Energy bar
	_text("EN", 8, hud_y + 22, Color(0.78, 0.78, 0.91), 12)
	draw_rect(Rect2(40, hud_y + 24, 108, 14), Color(0.1, 0.1, 0.17))
	var ew = maxf(0, (p.energy / GameData.BAL["max_energy"]) * 104)
	draw_rect(Rect2(42, hud_y + 26, ew, 10), Color(0.37, 0.62, 0.94))

	# Growth bar
	_text("GR", 8, hud_y + 40, Color(0.78, 0.78, 0.91), 12)
	draw_rect(Rect2(40, hud_y + 42, 108, 14), Color(0.1, 0.1, 0.17))
	var gw = maxf(0, (p.growth / GameData.BAL["division_cost"]) * 104)
	draw_rect(Rect2(42, hud_y + 44, gw, 10), Color(0.37, 0.81, 0.37))
	if p.can_divide() and sin(GameData.game_time * 4) > 0:
		draw_rect(Rect2(42, hud_y + 44, 104, 10), Color(1, 1, 0.37, 0.3))
		_text("SPACE!", 156, hud_y + 40, Color(1, 1, 0.37), 12)

	# Colony counter
	var col_count = game_ref.colonies.size()
	var col_goal = def.get("goal", 5)
	_text("Colony: %d/%d" % [col_count, col_goal], 200, hud_y + 4, Color(0.78, 0.78, 0.91), 14)

	# Score + methane
	_text("Score: %d" % (GameData.total_score + p.score), 952, hud_y + 4, Color(1, 0.84, 0), 14, 2)
	_text("CH4: %d" % p.methane_eaten, 952, hud_y + 24, Color(1, 0.31, 0.31), 12, 2)

	# Level
	_text("Lv%d" % (GameData.current_level + 1), 952, hud_y + 44, Color(0.53, 0.53, 0.53), 12, 2)

	# Science mode indicator
	if game_ref.science_mode:
		_text("[SCIENCE: Q]", 480, hud_y + 22, Color(0.31, 0.64, 0.94), 12, 1)

	# Flow ride indicator
	if p.riding_flow:
		_text("[RIDING FLOW]", 480, hud_y + 4, Color(0.31, 0.64, 0.94), 12, 1)
	elif p.can_ride_flow() and !p.can_divide():
		_text("SHIFT: ride flow", 480, hud_y + 44, Color(0.4, 0.4, 0.6), 10, 1)

	# Flow direction compass (above minimap)
	_draw_flow_compass(hud_y)

	# Redox ladder (compact, left side above HUD bar)
	_draw_redox_ladder(hud_y)

	# Minimap
	_draw_minimap(hud_y)

func _draw_flow_compass(hud_y: float) -> void:
	# Show flow direction: left = inlet (high pressure), right = outlet (low pressure)
	var cx = 200.0
	var cy = hud_y - 18.0
	var t = GameData.game_time

	# Background
	draw_rect(Rect2(cx - 4, cy - 4, 110, 16), Color(0, 0, 0, 0.4))

	# Animated arrow showing flow left->right
	var anim = fmod(t * 2.0, 1.0) * 8.0
	_text("IN", cx, cy - 4, Color(0.4, 0.7, 1.0, 0.7), 10)
	# Flow arrows
	for i in range(3):
		var ax = cx + 22 + i * 18 + anim
		draw_rect(Rect2(ax, cy + 2, 8, 2), Color(0.4, 0.7, 1.0, 0.5))
		draw_rect(Rect2(ax + 6, cy, 2, 6), Color(0.4, 0.7, 1.0, 0.5))
	_text("OUT", cx + 78, cy - 4, Color(0.37, 0.81, 0.37, 0.7), 10)

	# Toxic zone warning (if level has toxic zones)
	var def = GameData.get_level_def()
	if def.get("toxic", 0.0) > 0:
		var warn_x = cx + 120.0
		var warn_a = sin(t * 3.0) * 0.2 + 0.7
		draw_rect(Rect2(warn_x, cy - 2, 8, 8), Color(1.0, 0.3, 0.9, warn_a))
		_text("= TOXIC (H2S)", warn_x + 12, cy - 4, Color(1.0, 0.4, 0.9, 0.6), 10)

func _draw_redox_ladder(hud_y: float) -> void:
	# Show available substrates for current level with energy values
	var def = GameData.get_level_def()
	var subs: Array = def.get("subs", [])
	if subs.size() == 0:
		return

	var rx = 376.0
	var ry = hud_y + 4
	var spacing = 104.0 / maxf(1, subs.size())
	spacing = minf(spacing, 26.0)

	# Small vertical energy ladder
	for i in range(subs.size()):
		var sd = GameData.SUBSTRATES[subs[i]]
		var col = Color.html(sd["color"])
		var y = ry + i * spacing
		# Colored dot
		draw_rect(Rect2(rx, y + 2, 8, 8), col)
		# Formula + energy
		_text("%s +%d" % [sd["formula"], sd["energy"]], rx + 12, y, col * Color(1,1,1,0.85), 10)

func _draw_minimap(hud_y: float) -> void:
	if !game_ref or !game_ref.world_node:
		return
	var w_node = game_ref.world_node
	var p = game_ref.player_node
	var mm_w = 84.0
	var mm_h = 52.0
	var mm_x = 960.0 - mm_w - 8
	var mm_y = hud_y - mm_h - 8

	_box(mm_x - 2, mm_y - 2, mm_w + 4, mm_h + 4, Color(0, 0, 0, 0.7), Color(0.23, 0.23, 0.42))

	var sx = mm_w / w_node.map_w
	var sy = mm_h / w_node.map_h
	var ep = GameData.get_env_pal()

	for y in range(0, w_node.map_h, 2):
		for x in range(0, w_node.map_w, 2):
			var tile = w_node.get_tile(x, y)
			var col: Color = Color.TRANSPARENT
			if tile == GameData.Tile.SOLID:
				col = Color.html(ep["grain"]) * Color(1,1,1,0.6)
			elif tile == GameData.Tile.TOXIC:
				col = Color.html(ep["toxic"]) * Color(1,1,1,0.6)
			elif tile == GameData.Tile.BIOFILM:
				col = Color(0.23, 0.48, 0.29, 0.7)
			elif tile == GameData.Tile.OUTLET:
				col = Color(0.37, 0.81, 0.37, 0.7)
			if col.a > 0:
				draw_rect(Rect2(mm_x + x * sx, mm_y + y * sy,
					maxf(2, sx * 2), maxf(2, sy * 2)), col)

	# Player blip
	if p:
		var px = mm_x + p.tile_x * sx
		var py = mm_y + p.tile_y * sy
		var blink = sin(GameData.game_time * 6) > 0
		draw_rect(Rect2(px - 2, py - 2, 6, 6), Color.WHITE if blink else Color(0.16, 0.81, 0.69))

	# Colony blips
	for c in game_ref.colonies:
		if is_instance_valid(c):
			var cx = mm_x + (c.position.x / GameData.TILE) * sx
			var cy = mm_y + (c.position.y / GameData.TILE) * sy
			draw_rect(Rect2(cx, cy, 2, 2), Color(0.37, 0.81, 0.37, 0.8))

func _draw_tutorial() -> void:
	if !game_ref or !game_ref.player_node:
		return
	if GameData.current_level > 1:
		return  # Only show tutorial on first 2 levels
	var p = game_ref.player_node
	var t = GameData.game_time
	var hint_text := ""
	var hint_color := Color(1, 0.84, 0, 0.8)

	if p.substrates_eaten == 0 and t > 2.0:
		hint_text = "Move with ARROWS/WASD - touch substrates to eat them!"
	elif p.substrates_eaten > 0 and p.substrates_eaten < 3 and p.health < 80:
		hint_text = "Eating restores HP and Energy - keep moving to find food!"
	elif p.health < 40 and p.substrates_eaten > 0:
		hint_text = "Health is low! Find substrates quickly or you'll starve!"
		hint_color = Color(1, 0.3, 0.3, 0.8)
	elif p.can_divide() and p.colonies_placed == 0:
		hint_text = "Growth bar full! Press SPACE to place a colony!"
		hint_color = Color(0.37, 0.81, 0.37, 0.9)
	elif p.colonies_placed > 0 and p.colonies_placed < game_ref.colonies.size() + 1:
		var def = GameData.get_level_def()
		var goal = def.get("goal", 5)
		if game_ref.colonies.size() < goal:
			hint_text = "Colony placed! Keep eating to grow and place %d total." % goal
	elif p.can_ride_flow() and !p.riding_flow and p.substrates_eaten > 5:
		hint_text = "Hold SHIFT to ride the flow current (planktonic mode)!"
		hint_color = Color(0.31, 0.64, 0.94, 0.8)

	if hint_text != "":
		# Pulsing visibility
		var alpha = sin(t * 2.0) * 0.2 + 0.7
		hint_color.a *= alpha
		_box(80, 4, 800, 28, Color(0, 0, 0, 0.5 * alpha), Color(0.3, 0.3, 0.5, 0.3 * alpha))
		_text(hint_text, 480, 6, hint_color, 14, 1)

func _draw_screen_effects() -> void:
	if !game_ref or !game_ref.player_node:
		return
	# Eat flash
	if game_ref.eat_flash_timer > 0:
		var a = game_ref.eat_flash_timer / 0.15 * 0.15
		draw_rect(Rect2(0, 0, 960, 540), Color(game_ref.eat_flash_color, a))

	# Starvation warning - red vignette pulsing
	if game_ref.starvation_pulse > 0:
		var pulse = sin(game_ref.starvation_pulse) * 0.5 + 0.5
		var intensity = (1.0 - game_ref.player_node.health / 30.0) * 0.25
		var a = pulse * intensity
		# Red borders
		draw_rect(Rect2(0, 0, 960, 16), Color(0.8, 0, 0, a))
		draw_rect(Rect2(0, 524, 960, 16), Color(0.8, 0, 0, a))
		draw_rect(Rect2(0, 0, 16, 540), Color(0.8, 0, 0, a))
		draw_rect(Rect2(944, 0, 16, 540), Color(0.8, 0, 0, a))
		# Warning text
		if pulse > 0.7:
			_text("STARVING!", 480, 20, Color(1, 0.2, 0.2, a * 3), 16, 1)

func _draw_pause() -> void:
	draw_rect(Rect2(0, 0, 960, 540), Color(0, 0, 0, 0.6))
	_box(360, 120, 240, 200, Color(0.04, 0.04, 0.17, 0.95), Color(0.23, 0.23, 0.42))
	_text("PAUSED", 480, 136, Color.WHITE, 24, 1)
	var opts = ["Resume", "Mute" if !AudioMgr.muted else "Unmute", "Quit"]
	for i in range(opts.size()):
		var c = Color(1, 0.84, 0) if i == game_ref.pause_sel else Color(0.53, 0.53, 0.53)
		var prefix = "> " if i == game_ref.pause_sel else "  "
		_text(prefix + opts[i], 480, 190 + i * 32, c, 16, 1)

func _draw_level_complete() -> void:
	var p = game_ref.player_node
	var alpha = clampf(game_ref.complete_timer, 0, 0.7)
	draw_rect(Rect2(0, 0, 960, 540), Color(0, 0, 0, alpha))
	if game_ref.complete_timer < 0.5:
		return

	_box(200, 80, 560, 300, Color(0.04, 0.1, 0.04, 0.95), Color(0.37, 0.81, 0.37))
	_text("LEVEL COMPLETE!", 480, 96, Color(0.37, 0.81, 0.37), 24, 1)

	_text("Substrates eaten: %d" % p.substrates_eaten, 230, 150, Color(0.78, 0.78, 0.91), 14)
	_text("Methane consumed: %d" % p.methane_eaten, 230, 176, Color(1, 0.31, 0.31), 14)
	_text("N2O prevented: %d" % p.n2o_prevented, 230, 202, Color(0.31, 0.87, 0.44), 14)
	_text("Colonies placed: %d" % p.colonies_placed, 230, 228, Color(0.78, 0.78, 0.91), 14)
	_text("Score: %d" % p.score, 230, 266, Color(1, 0.84, 0), 16)

	if game_ref.complete_timer > 1.5 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 480, 350, Color(1, 0.84, 0), 16, 1)

func _draw_science_popup() -> void:
	if game_ref.science_popup_idx < 0:
		return
	var fact = GameData.SCIENCE_FACTS[game_ref.science_popup_idx]

	draw_rect(Rect2(0, 0, 960, 540), Color(0, 0, 0, 0.7))
	_box(40, 30, 880, 460, Color(0.04, 0.04, 0.17, 0.95), Color(0.31, 0.64, 0.94))

	draw_rect(Rect2(42, 32, 876, 36), Color(0.04, 0.12, 0.24))
	_text("SCIENCE DISCOVERY", 480, 36, Color(0.31, 0.64, 0.94), 16, 1)
	_text(fact["title"], 480, 80, Color(1, 0.84, 0), 20, 1)

	var lines = fact["text"].split("\n")
	for i in range(lines.size()):
		_text(lines[i], 70, 120 + i * 20, Color(0.78, 0.78, 0.91), 14)

	_text("+%d pts" % GameData.BAL["score_eat"], 480, 444, Color(0.37, 0.81, 0.37), 14, 1)
	if sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 480, 470, Color(1, 0.84, 0), 14, 1)

func _draw_game_over() -> void:
	var alpha = clampf(game_ref.death_timer * 0.5, 0, 0.7)
	draw_rect(Rect2(0, 0, 960, 540), Color(0.1, 0, 0, alpha))
	if game_ref.death_timer < 1:
		return

	_text("MICROBE LOST", 480, 140, Color(0.94, 0.27, 0.27), 32, 1)
	var msgs = [
		"Starvation: the ultimate substrate limitation.",
		"The geochemical environment was too hostile.",
		"Without nutrients, even archaea perish.",
		"Position matters - poor pore connectivity is fatal.",
	]
	_text(msgs[int(GameData.game_time) % msgs.size()], 480, 210, Color(0.53, 0.53, 0.53), 14, 1)
	_text("Score: %d" % (GameData.total_score + game_ref.player_node.score), 480, 260, Color(1, 0.84, 0), 20, 1)

	if game_ref.death_timer > 2 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER TO RETRY", 480, 330, Color(0.78, 0.78, 0.91), 16, 1)

func _draw_victory() -> void:
	var t = game_ref.victory_timer
	draw_rect(Rect2(0, 0, 960, 540), Color(0.024, 0.047, 0.094))

	# Stars
	for i in range(30):
		var sx = fmod(sin(i * 73) * 0.5 + 0.5, 1.0) * 960
		var sy = fmod(cos(i * 97) * 0.5 + 0.5, 1.0) * 540
		var blink = 1.0 if sin(GameData.game_time * 2 + i) > 0.5 else 0.3
		draw_rect(Rect2(sx, sy, 2, 2), Color(1, 1, 1, blink))

	_text("VICTORY!", 480, 30, Color(1, 0.84, 0), 40, 1)

	var tex = SpriteFactory.get_tex("methi_glow")
	if tex:
		draw_texture_rect(tex, Rect2(464, 100 + sin(GameData.game_time * 3) * 10, 32, 32), false)

	if t > 1:
		_text("Arke has colonized the underground!", 480, 160, Color(0.37, 0.81, 0.37), 16, 1)
	if t > 2:
		_text("From a single archaea to a thriving biofilm,", 480, 200, Color(0.78, 0.78, 0.91), 14, 1)
		_text("you prevented greenhouse gases from escaping.", 480, 224, Color(0.78, 0.78, 0.91), 14, 1)
	if t > 3:
		_text("Methane consumed: %d molecules" % int(GameData.methane_prevented), 480, 270, Color(1, 0.31, 0.31), 16, 1)
		_text("Final Score: %d" % GameData.total_score, 480, 310, Color(1, 0.84, 0), 24, 1)
	if t > 4:
		_text("Based on CompLaB3D", 480, 360, Color(0.31, 0.64, 0.94), 16, 1)
		_text("Pore-Scale Biogeochemical Reactive Transport", 480, 386, Color(0.31, 0.64, 0.94), 12, 1)
	if t > 5:
		_text("University of Georgia", 480, 424, Color(0.53, 0.53, 0.53), 14, 1)
	if t > 3 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 480, 510, Color(1, 0.84, 0), 14, 1)
