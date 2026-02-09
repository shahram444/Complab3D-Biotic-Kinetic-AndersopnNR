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
		size: int = 8, halign: int = 0) -> void:
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
	draw_string(font, pos + Vector2(1, 1), text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(0, 0, 0, 0.8))
	draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _box(x: float, y: float, w: float, h: float, bg: Color, border: Color) -> void:
	draw_rect(Rect2(x, y, w, h), bg)
	draw_rect(Rect2(x, y, w, h), border, false, 1.0)

# ── SCREENS ──────────────────────────────────────────────────────────────────

func _draw_boot() -> void:
	draw_rect(Rect2(0, 0, 480, 270), Color.BLACK)
	var alpha = clampf(game_ref.boot_timer, 0, 1)
	_text("CompLaB3D", 240, 80, Color(0.37, 0.77, 0.92, alpha), 12, 1)
	_text("presents", 240, 100, Color(0.53, 0.53, 0.53, alpha), 8, 1)
	if game_ref.boot_timer > 0.8:
		_text("A Game Based on Real Science", 240, 135, Color(0.37, 0.81, 0.37, clampf((game_ref.boot_timer - 0.8) * 2, 0, 1)), 8, 1)

func _draw_title() -> void:
	var t = GameData.game_time
	draw_rect(Rect2(0, 0, 480, 270), Color(0.024, 0.047, 0.094))

	# Floating particles
	for i in range(20):
		var px = fmod(t * 15 + i * 30, 500) - 10
		var py = 40 + sin(t + i * 1.7) * 90
		draw_rect(Rect2(px, py, 3, 3), Color(0.1, 0.23, 0.4, 0.3))

	# Title
	var ty = 35 + sin(t * 1.5) * 3
	_text("METHI", 240, ty, Color(0.16, 0.81, 0.69), 20, 1)
	_text("Guardians of Earth", 240, ty + 28, Color(0.77, 0.63, 0.35), 10, 1)

	# Methi sprite
	var tex = SpriteFactory.get_tex("methi_down")
	if tex:
		draw_texture_rect(tex, Rect2(232, 100 + sin(t * 2) * 4, 16, 16), false)

	# Blink prompt
	if sin(t * 3) > 0:
		_text("PRESS ENTER", 240, 150, Color(1, 0.84, 0), 8, 1)

	_text("Based on CompLaB3D Research", 240, 190, Color(0.53, 0.53, 0.53), 7, 1)
	_text("Pore-Scale Reactive Transport", 240, 202, Color(0.4, 0.4, 0.4), 6, 1)
	_text("University of Georgia", 240, 225, Color(0.27, 0.27, 0.27), 6, 1)

func _draw_narrative() -> void:
	draw_rect(Rect2(0, 0, 480, 270), Color.BLACK)

	# Starfield background
	var t = GameData.game_time
	for i in range(40):
		var sx = fmod(sin(i * 73.1) * 0.5 + 0.5, 1.0) * 480
		var sy = fmod(cos(i * 97.3) * 0.5 + 0.5, 1.0) * 270
		var blink = 0.5 + sin(t * 1.5 + i * 0.7) * 0.3
		draw_rect(Rect2(sx, sy, 1, 1), Color(1, 1, 1, blink * 0.4))

	var lines = GameData.NARRATIVE_LINES
	var line_h = 14.0
	var start_y = 280.0 - game_ref.story_scroll

	for i in range(lines.size()):
		var y = start_y + i * line_h
		if y < -20 or y > 290:
			continue
		var alpha = 1.0
		if y < 30:
			alpha = clampf(y / 30.0, 0, 1)
		if y > 240:
			alpha = clampf((270.0 - y) / 30.0, 0, 1)

		var line = lines[i]
		var color = Color(0.78, 0.78, 0.91, alpha)
		var fsize = 8

		if "METHI" in line:
			color = Color(0.16, 0.81, 0.69, alpha)
			fsize = 11
		elif "MICROBES" in line:
			color = Color(0.37, 0.81, 0.37, alpha)
			fsize = 12
		elif "ENTER" in line:
			color = Color(1, 0.84, 0, alpha)
		elif "..." in line:
			color = Color(0.37, 0.77, 0.92, alpha)
		elif "mission" in line.to_lower():
			color = Color(1, 0.84, 0, alpha)
			fsize = 9
		elif "eat" in line.to_lower() or "grow" in line.to_lower():
			color = Color(0.37, 0.81, 0.37, alpha)
			fsize = 9

		_text(line, 240, y, color, fsize, 1)

		# Draw inline illustrations at key story moments
		if "invisible war" in line.to_lower() and alpha > 0.3:
			_draw_narrative_scene_earth(240, y + 14, alpha)
		elif "microbes" in line.to_upper() and line.strip_edges() == "The MICROBES." and alpha > 0.3:
			_draw_narrative_scene_microbes(240, y + 14, alpha)
		elif "pseudopods" in line.to_lower() and alpha > 0.3:
			_draw_narrative_scene_methi(240, y + 14, alpha)

	_text("ENTER to skip", 456, 258, Color(0.27, 0.27, 0.27, 0.5), 6, 2)

func _draw_narrative_scene_earth(cx: float, y: float, alpha: float) -> void:
	# Small pixel Earth with gas arrows rising
	var w = 50.0
	var x = cx - w * 0.5
	# Ground layer
	draw_rect(Rect2(x, y + 6, w, 12), Color(0.3, 0.2, 0.1, alpha * 0.6))
	draw_rect(Rect2(x, y + 3, w, 4), Color(0.2, 0.5, 0.2, alpha * 0.5))
	# Rising gas arrows (red for CH4)
	for i in range(5):
		var ax = x + 8 + i * 10
		var ay = y + 2 - sin(GameData.game_time * 2 + i) * 3
		draw_rect(Rect2(ax, ay, 2, 4), Color(1, 0.3, 0.3, alpha * 0.7))
		draw_rect(Rect2(ax - 1, ay + 4, 4, 1), Color(1, 0.3, 0.3, alpha * 0.4))

func _draw_narrative_scene_microbes(cx: float, y: float, alpha: float) -> void:
	# Row of little microbe silhouettes
	for i in range(7):
		var mx = cx - 42 + i * 14
		var my = y + 4 + sin(GameData.game_time * 3 + i * 1.2) * 2
		var col = Color(0.16, 0.81, 0.69, alpha * 0.8) if i % 2 == 0 else Color(0.37, 0.81, 0.37, alpha * 0.7)
		draw_rect(Rect2(mx, my, 6, 5), col)
		draw_rect(Rect2(mx + 1, my - 1, 4, 1), col * Color(1,1,1,0.7))
		draw_rect(Rect2(mx + 2, my + 1, 1, 1), Color(1, 1, 1, alpha * 0.9))

func _draw_narrative_scene_methi(cx: float, y: float, alpha: float) -> void:
	# Large METHI character preview
	var tex = SpriteFactory.get_tex("methi_down")
	if tex:
		var bob = sin(GameData.game_time * 2) * 3
		draw_texture_rect(tex, Rect2(cx - 16, y + 2 + bob, 32, 32), false,
			Color(1, 1, 1, alpha * 0.9))
		# Glow around character
		draw_rect(Rect2(cx - 20, y - 2 + bob, 40, 40),
			Color(0.16, 0.81, 0.69, alpha * 0.15))

func _draw_level_intro() -> void:
	var def = GameData.get_level_def()
	var env = def.get("env", 0)
	var info = GameData.WORLD_INTROS[env] if env < GameData.WORLD_INTROS.size() else GameData.WORLD_INTROS[0]
	var ep = GameData.get_env_pal()

	draw_rect(Rect2(0, 0, 480, 270), Color.html(ep["bg"]))

	var t = game_ref.intro_timer
	var fade = clampf(t * 2, 0, 1)

	_text(info["title"], 240, 20, Color(1, 1, 1, fade), 18, 1)
	_text(info["sub"], 240, 48, Color.html(ep["grain_l"]).lightened(0.3) * Color(1,1,1,fade), 10, 1)

	if t > 0.3:
		var a2 = clampf((t - 0.3) * 3, 0, 1)
		_text("Level %d: %s" % [GameData.current_level + 1, def["title"]],
			240, 70, Color(1, 0.84, 0, a2), 8, 1)

	if t > 0.5:
		var a3 = clampf((t - 0.5) * 2, 0, 1)
		var lines = info["text"].split("\n")
		for i in range(lines.size()):
			_text(lines[i], 40, 92 + i * 11, Color(0.78, 0.78, 0.91, a3), 7)

	if t > 1.0:
		var a4 = clampf((t - 1.0) * 2, 0, 1)
		# Show available substrates
		_text("Available substrates:", 40, 200, Color(0.53, 0.53, 0.53, a4), 7)
		var subs: Array = def.get("subs", [])
		for i in range(subs.size()):
			var sd = GameData.SUBSTRATES[subs[i]]
			_text("%s (%s) +%d energy" % [sd["name"], sd["formula"], sd["energy"]],
				60, 212 + i * 10, Color.html(sd["color"]) * Color(1,1,1,a4), 6)

		_text("Goal: Place %d colonies" % def["goal"],
			240, 248, Color(0.37, 0.81, 0.37, a4), 8, 1)

	if t > 1.5 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 240, 260, Color(1, 0.84, 0), 8, 1)

func _draw_hud() -> void:
	if !game_ref or !game_ref.player_node:
		return
	var p = game_ref.player_node
	var def = GameData.get_level_def()
	var hud_y = 238.0

	# Background
	draw_rect(Rect2(0, hud_y, 480, 32), Color(0.04, 0.04, 0.1, 0.88))
	draw_rect(Rect2(0, hud_y, 480, 1), Color(0.23, 0.23, 0.42))

	# HP bar
	_text("HP", 4, hud_y + 2, Color(0.78, 0.78, 0.91), 6)
	draw_rect(Rect2(20, hud_y + 3, 54, 7), Color(0.1, 0.1, 0.17))
	var hw = maxf(0, (p.health / GameData.BAL["max_health"]) * 52)
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
	draw_rect(Rect2(21, hud_y + 4, hw, 5), hc)

	# Energy bar
	_text("EN", 4, hud_y + 11, Color(0.78, 0.78, 0.91), 6)
	draw_rect(Rect2(20, hud_y + 12, 54, 7), Color(0.1, 0.1, 0.17))
	var ew = maxf(0, (p.energy / GameData.BAL["max_energy"]) * 52)
	draw_rect(Rect2(21, hud_y + 13, ew, 5), Color(0.37, 0.62, 0.94))

	# Growth bar
	_text("GR", 4, hud_y + 20, Color(0.78, 0.78, 0.91), 6)
	draw_rect(Rect2(20, hud_y + 21, 54, 7), Color(0.1, 0.1, 0.17))
	var gw = maxf(0, (p.growth / GameData.BAL["division_cost"]) * 52)
	draw_rect(Rect2(21, hud_y + 22, gw, 5), Color(0.37, 0.81, 0.37))
	if p.can_divide() and sin(GameData.game_time * 4) > 0:
		draw_rect(Rect2(21, hud_y + 22, 52, 5), Color(1, 1, 0.37, 0.3))
		_text("SPACE!", 78, hud_y + 20, Color(1, 1, 0.37), 6)

	# Colony counter
	var col_count = game_ref.colonies.size()
	var col_goal = def.get("goal", 5)
	_text("Colony: %d/%d" % [col_count, col_goal], 100, hud_y + 2, Color(0.78, 0.78, 0.91), 7)

	# Score + methane
	_text("Score: %d" % (GameData.total_score + p.score), 476, hud_y + 2, Color(1, 0.84, 0), 7, 2)
	_text("CH4: %d" % p.methane_eaten, 476, hud_y + 12, Color(1, 0.31, 0.31), 6, 2)

	# Level
	_text("Lv%d" % (GameData.current_level + 1), 476, hud_y + 22, Color(0.53, 0.53, 0.53), 6, 2)

	# Science mode indicator
	if game_ref.science_mode:
		_text("[SCIENCE: Q]", 240, hud_y + 11, Color(0.31, 0.64, 0.94), 6, 1)

	# Flow ride indicator
	if p.riding_flow:
		_text("[RIDING FLOW]", 240, hud_y + 2, Color(0.31, 0.64, 0.94), 6, 1)
	elif p.can_ride_flow() and !p.can_divide():
		_text("SHIFT: ride flow", 240, hud_y + 22, Color(0.4, 0.4, 0.6), 5, 1)

	# Redox ladder (compact, left side above HUD bar)
	_draw_redox_ladder(hud_y)

	# Minimap
	_draw_minimap(hud_y)

func _draw_redox_ladder(hud_y: float) -> void:
	# Show available substrates for current level with energy values
	var def = GameData.get_level_def()
	var subs: Array = def.get("subs", [])
	if subs.size() == 0:
		return

	var rx = 188.0
	var ry = hud_y + 2
	var spacing = 52.0 / maxf(1, subs.size())
	spacing = minf(spacing, 13.0)

	# Small vertical energy ladder
	for i in range(subs.size()):
		var sd = GameData.SUBSTRATES[subs[i]]
		var col = Color.html(sd["color"])
		var y = ry + i * spacing
		# Colored dot
		draw_rect(Rect2(rx, y + 1, 4, 4), col)
		# Formula + energy
		_text("%s +%d" % [sd["formula"], sd["energy"]], rx + 6, y, col * Color(1,1,1,0.85), 5)

func _draw_minimap(hud_y: float) -> void:
	if !game_ref or !game_ref.world_node:
		return
	var w_node = game_ref.world_node
	var p = game_ref.player_node
	var mm_w = 42.0
	var mm_h = 26.0
	var mm_x = 480.0 - mm_w - 4
	var mm_y = hud_y - mm_h - 4

	_box(mm_x - 1, mm_y - 1, mm_w + 2, mm_h + 2, Color(0, 0, 0, 0.7), Color(0.23, 0.23, 0.42))

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
					maxf(1, sx * 2), maxf(1, sy * 2)), col)

	# Player blip
	if p:
		var px = mm_x + p.tile_x * sx
		var py = mm_y + p.tile_y * sy
		var blink = sin(GameData.game_time * 6) > 0
		draw_rect(Rect2(px - 1, py - 1, 3, 3), Color.WHITE if blink else Color(0.16, 0.81, 0.69))

	# Colony blips
	for c in game_ref.colonies:
		if is_instance_valid(c):
			var cx = mm_x + (c.position.x / GameData.TILE) * sx
			var cy = mm_y + (c.position.y / GameData.TILE) * sy
			draw_rect(Rect2(cx, cy, 1, 1), Color(0.37, 0.81, 0.37, 0.8))

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
		_box(40, 2, 400, 14, Color(0, 0, 0, 0.5 * alpha), Color(0.3, 0.3, 0.5, 0.3 * alpha))
		_text(hint_text, 240, 3, hint_color, 7, 1)

func _draw_screen_effects() -> void:
	if !game_ref or !game_ref.player_node:
		return
	# Eat flash
	if game_ref.eat_flash_timer > 0:
		var a = game_ref.eat_flash_timer / 0.15 * 0.15
		draw_rect(Rect2(0, 0, 480, 270), Color(game_ref.eat_flash_color, a))

	# Starvation warning - red vignette pulsing
	if game_ref.starvation_pulse > 0:
		var pulse = sin(game_ref.starvation_pulse) * 0.5 + 0.5
		var intensity = (1.0 - game_ref.player_node.health / 30.0) * 0.25
		var a = pulse * intensity
		# Red borders
		draw_rect(Rect2(0, 0, 480, 8), Color(0.8, 0, 0, a))
		draw_rect(Rect2(0, 262, 480, 8), Color(0.8, 0, 0, a))
		draw_rect(Rect2(0, 0, 8, 270), Color(0.8, 0, 0, a))
		draw_rect(Rect2(472, 0, 8, 270), Color(0.8, 0, 0, a))
		# Warning text
		if pulse > 0.7:
			_text("STARVING!", 240, 10, Color(1, 0.2, 0.2, a * 3), 8, 1)

func _draw_pause() -> void:
	draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0, 0.6))
	_box(180, 60, 120, 100, Color(0.04, 0.04, 0.17, 0.95), Color(0.23, 0.23, 0.42))
	_text("PAUSED", 240, 68, Color.WHITE, 12, 1)
	var opts = ["Resume", "Mute" if !AudioMgr.muted else "Unmute", "Quit"]
	for i in range(opts.size()):
		var c = Color(1, 0.84, 0) if i == game_ref.pause_sel else Color(0.53, 0.53, 0.53)
		var prefix = "> " if i == game_ref.pause_sel else "  "
		_text(prefix + opts[i], 240, 95 + i * 16, c, 8, 1)

func _draw_level_complete() -> void:
	var p = game_ref.player_node
	var alpha = clampf(game_ref.complete_timer, 0, 0.7)
	draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0, alpha))
	if game_ref.complete_timer < 0.5:
		return

	_box(100, 40, 280, 150, Color(0.04, 0.1, 0.04, 0.95), Color(0.37, 0.81, 0.37))
	_text("LEVEL COMPLETE!", 240, 48, Color(0.37, 0.81, 0.37), 12, 1)

	_text("Substrates eaten: %d" % p.substrates_eaten, 115, 75, Color(0.78, 0.78, 0.91), 7)
	_text("Methane consumed: %d" % p.methane_eaten, 115, 88, Color(1, 0.31, 0.31), 7)
	_text("N2O prevented: %d" % p.n2o_prevented, 115, 101, Color(0.31, 0.87, 0.44), 7)
	_text("Colonies placed: %d" % p.colonies_placed, 115, 114, Color(0.78, 0.78, 0.91), 7)
	_text("Score: %d" % p.score, 115, 133, Color(1, 0.84, 0), 8)

	if game_ref.complete_timer > 1.5 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 240, 175, Color(1, 0.84, 0), 8, 1)

func _draw_science_popup() -> void:
	if game_ref.science_popup_idx < 0:
		return
	var fact = GameData.SCIENCE_FACTS[game_ref.science_popup_idx]

	draw_rect(Rect2(0, 0, 480, 270), Color(0, 0, 0, 0.7))
	_box(20, 15, 440, 230, Color(0.04, 0.04, 0.17, 0.95), Color(0.31, 0.64, 0.94))

	draw_rect(Rect2(21, 16, 438, 18), Color(0.04, 0.12, 0.24))
	_text("SCIENCE DISCOVERY", 240, 18, Color(0.31, 0.64, 0.94), 8, 1)
	_text(fact["title"], 240, 40, Color(1, 0.84, 0), 10, 1)

	var lines = fact["text"].split("\n")
	for i in range(lines.size()):
		_text(lines[i], 35, 60 + i * 10, Color(0.78, 0.78, 0.91), 7)

	_text("+%d pts" % GameData.BAL["score_eat"], 240, 222, Color(0.37, 0.81, 0.37), 7, 1)
	if sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 240, 235, Color(1, 0.84, 0), 7, 1)

func _draw_game_over() -> void:
	var alpha = clampf(game_ref.death_timer * 0.5, 0, 0.7)
	draw_rect(Rect2(0, 0, 480, 270), Color(0.1, 0, 0, alpha))
	if game_ref.death_timer < 1:
		return

	_text("MICROBE LOST", 240, 70, Color(0.94, 0.27, 0.27), 16, 1)
	var msgs = [
		"Starvation: the ultimate substrate limitation.",
		"The geochemical environment was too hostile.",
		"Without nutrients, even archaea perish.",
		"Position matters - poor pore connectivity is fatal.",
	]
	_text(msgs[int(GameData.game_time) % msgs.size()], 240, 105, Color(0.53, 0.53, 0.53), 7, 1)
	_text("Score: %d" % (GameData.total_score + game_ref.player_node.score), 240, 130, Color(1, 0.84, 0), 10, 1)

	if game_ref.death_timer > 2 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER TO RETRY", 240, 165, Color(0.78, 0.78, 0.91), 8, 1)

func _draw_victory() -> void:
	var t = game_ref.victory_timer
	draw_rect(Rect2(0, 0, 480, 270), Color(0.024, 0.047, 0.094))

	# Stars
	for i in range(30):
		var sx = fmod(sin(i * 73) * 0.5 + 0.5, 1.0) * 480
		var sy = fmod(cos(i * 97) * 0.5 + 0.5, 1.0) * 270
		var blink = 1.0 if sin(GameData.game_time * 2 + i) > 0.5 else 0.3
		draw_rect(Rect2(sx, sy, 1, 1), Color(1, 1, 1, blink))

	_text("VICTORY!", 240, 15, Color(1, 0.84, 0), 20, 1)

	var tex = SpriteFactory.get_tex("methi_glow")
	if tex:
		draw_texture_rect(tex, Rect2(232, 50 + sin(GameData.game_time * 3) * 5, 16, 16), false)

	if t > 1:
		_text("Methi has colonized the underground!", 240, 80, Color(0.37, 0.81, 0.37), 8, 1)
	if t > 2:
		_text("From a single archaea to a thriving biofilm,", 240, 100, Color(0.78, 0.78, 0.91), 7, 1)
		_text("you prevented greenhouse gases from escaping.", 240, 112, Color(0.78, 0.78, 0.91), 7, 1)
	if t > 3:
		_text("Methane consumed: %d molecules" % int(GameData.methane_prevented), 240, 135, Color(1, 0.31, 0.31), 8, 1)
		_text("Final Score: %d" % GameData.total_score, 240, 155, Color(1, 0.84, 0), 12, 1)
	if t > 4:
		_text("Based on CompLaB3D", 240, 180, Color(0.31, 0.64, 0.94), 8, 1)
		_text("Pore-Scale Biogeochemical Reactive Transport", 240, 193, Color(0.31, 0.64, 0.94), 6, 1)
	if t > 5:
		_text("University of Georgia", 240, 212, Color(0.53, 0.53, 0.53), 7, 1)
	if t > 3 and sin(GameData.game_time * 3) > 0:
		_text("PRESS ENTER", 240, 255, Color(1, 0.84, 0), 7, 1)
