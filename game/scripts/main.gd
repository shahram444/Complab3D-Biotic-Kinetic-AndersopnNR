extends Node2D
## Main game controller - state machine, scene management, UI overlays.

const S := GameData.State
const T := GameData.TILE

var state: int = S.BOOT
var boot_timer: float = 0.0
var dialogue_idx: int = 0
var dialogue_char: int = 0
var dialogue_timer: float = 0.0
var mission_idx: int = 0
var mission_char: int = 0
var mission_timer: float = 0.0
var intro_timer: float = 0.0
var complete_timer: float = 0.0
var death_timer: float = 0.0
var victory_timer: float = 0.0
var pause_sel: int = 0
var science_mode := false
var science_popup_idx: int = -1
var shown_facts: Dictionary = {}

# Scene nodes
var world_node: Node2D = null
var player_node: Node2D = null
var entity_layer: Node2D = null
var ui_layer: CanvasLayer = null
var cam: Camera2D = null
var hud_node: Node2D = null

# Substrate & colony tracking
var substrates: Array = []
var colonies: Array = []
var rivals: Array = []
var spawn_timer: float = 0.0
var rival_move_timer: float = 0.0

# Camera shake
var shake_intensity: float = 0.0
var shake_duration: float = 0.0

func _ready() -> void:
	_build_scene_tree()
	state = S.BOOT

func _build_scene_tree() -> void:
	# World layer
	world_node = preload("res://scripts/world.gd").new()
	world_node.name = "World"
	add_child(world_node)

	# Entity layer
	entity_layer = Node2D.new()
	entity_layer.name = "Entities"
	add_child(entity_layer)

	# Player
	player_node = preload("res://scripts/player.gd").new()
	player_node.name = "Player"
	add_child(player_node)
	player_node.died.connect(_on_player_died)
	player_node.divided.connect(_on_player_divided)
	player_node.ate_substrate.connect(_on_ate_substrate)
	player_node.visible = false

	# Camera
	cam = Camera2D.new()
	cam.name = "Camera"
	cam.zoom = Vector2.ONE
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 6.0
	add_child(cam)
	cam.make_current()

	# UI layer
	ui_layer = CanvasLayer.new()
	ui_layer.name = "UI"
	ui_layer.layer = 10
	add_child(ui_layer)

	hud_node = Node2D.new()
	hud_node.name = "HUD"
	hud_node.set_script(preload("res://scripts/hud.gd"))
	ui_layer.add_child(hud_node)

func _process(delta: float) -> void:
	GameData.game_time += delta
	_update_shake(delta)

	match state:
		S.BOOT: _update_boot(delta)
		S.TITLE: _update_title(delta)
		S.NARRATIVE: _update_narrative(delta)
		S.MISSION_BRIEF: _update_mission_brief(delta)
		S.LEVEL_INTRO: _update_level_intro(delta)
		S.PLAYING: _update_playing(delta)
		S.PAUSED: _update_paused(delta)
		S.LEVEL_COMPLETE: _update_level_complete(delta)
		S.SCIENCE_POPUP: _update_science_popup(delta)
		S.GAME_OVER: _update_game_over(delta)
		S.VICTORY: _update_victory(delta)

	if Input.is_action_just_pressed("toggle_mute"):
		AudioMgr.toggle_mute()

	queue_redraw()
	if hud_node and hud_node.has_method("set_game_ref"):
		hud_node.set_game_ref(self)

# ── STATE UPDATES ────────────────────────────────────────────────────────────

func _update_boot(delta: float) -> void:
	boot_timer += delta
	if boot_timer > 2.0 or Input.is_action_just_pressed("ui_confirm"):
		state = S.TITLE
		AudioMgr.play_title_music()

func _update_title(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_confirm"):
		AudioMgr.sfx_menu_confirm()
		AudioMgr.stop_music()
		state = S.NARRATIVE
		dialogue_idx = 0
		dialogue_char = 0
		dialogue_timer = 0.0

func _update_narrative(delta: float) -> void:
	dialogue_timer += delta
	# Typewriter effect - advance chars
	var line = GameData.CUTSCENE[dialogue_idx]
	var full_len = line["text"].length()
	var chars_per_sec = 30.0
	dialogue_char = mini(int(dialogue_timer * chars_per_sec), full_len)

	if Input.is_action_just_pressed("ui_confirm"):
		if dialogue_char < full_len:
			# Skip to full text
			dialogue_char = full_len
			dialogue_timer = full_len / chars_per_sec + 1.0
		else:
			# Advance to next dialogue line
			dialogue_idx += 1
			dialogue_char = 0
			dialogue_timer = 0.0
			AudioMgr.sfx_menu_select()
			if dialogue_idx >= GameData.CUTSCENE.size():
				_start_game()

func _update_mission_brief(delta: float) -> void:
	mission_timer += delta
	var briefs = GameData.MISSION_BRIEFS
	var level_briefs: Array = []
	if GameData.current_level < briefs.size():
		level_briefs = briefs[GameData.current_level]
	if level_briefs.size() == 0:
		state = S.LEVEL_INTRO
		intro_timer = 0
		return

	var line = level_briefs[mission_idx]
	var full_len = line["text"].length()
	var chars_per_sec = 35.0
	mission_char = mini(int(mission_timer * chars_per_sec), full_len)

	if Input.is_action_just_pressed("ui_confirm"):
		if mission_char < full_len:
			mission_char = full_len
			mission_timer = full_len / chars_per_sec + 1.0
		else:
			mission_idx += 1
			mission_char = 0
			mission_timer = 0.0
			AudioMgr.sfx_menu_select()
			if mission_idx >= level_briefs.size():
				state = S.LEVEL_INTRO
				intro_timer = 0

func _update_level_intro(delta: float) -> void:
	intro_timer += delta
	if Input.is_action_just_pressed("ui_confirm") and intro_timer > 0.5:
		AudioMgr.sfx_menu_confirm()
		state = S.PLAYING
		player_node.visible = true

func _update_playing(delta: float) -> void:
	if Input.is_action_just_pressed("pause"):
		state = S.PAUSED
		pause_sel = 0
		AudioMgr.sfx_menu_select()
		return

	if Input.is_action_just_pressed("toggle_science"):
		science_mode = !science_mode
		if science_mode:
			AudioMgr.sfx_science()

	# Division
	if Input.is_action_just_pressed("action_divide") and player_node.alive and player_node.can_divide():
		if player_node.try_divide():
			_do_shake(3, 0.2)

	# Update substrates
	_update_substrates(delta)
	_update_colonies(delta)
	_update_rivals(delta)
	_update_popups(delta)

	# Eat flash
	if eat_flash_timer > 0:
		eat_flash_timer -= delta

	# Starvation urgency pulse
	if player_node.alive and player_node.health < 30:
		starvation_pulse += delta * 4.0
	else:
		starvation_pulse = 0.0

	# Camera follow
	if player_node and cam:
		cam.position = player_node.position + Vector2(T / 2, T / 2)
		# Clamp camera to map
		var map_size = world_node.map_w * T
		var map_h = world_node.map_h * T
		var half_w = GameData.VIEW_W * 0.5
		var half_h = GameData.VIEW_H * 0.5
		cam.position.x = clampf(cam.position.x, half_w, maxf(half_w, map_size - half_w))
		cam.position.y = clampf(cam.position.y, half_h, maxf(half_h, map_h - half_h))

	# Check death transition
	if !player_node.alive and player_node.death_timer > 2.5:
		state = S.GAME_OVER
		death_timer = 0

func _update_paused(_delta: float) -> void:
	if Input.is_action_just_pressed("pause"):
		state = S.PLAYING
	if Input.is_action_just_pressed("move_up"):
		pause_sel = maxi(0, pause_sel - 1)
		AudioMgr.sfx_menu_select()
	if Input.is_action_just_pressed("move_down"):
		pause_sel = mini(2, pause_sel + 1)
		AudioMgr.sfx_menu_select()
	if Input.is_action_just_pressed("ui_confirm"):
		AudioMgr.sfx_menu_confirm()
		match pause_sel:
			0: state = S.PLAYING
			1: AudioMgr.toggle_mute()
			2:
				state = S.TITLE
				AudioMgr.play_title_music()

func _update_level_complete(delta: float) -> void:
	complete_timer += delta
	if complete_timer > 1.5 and Input.is_action_just_pressed("ui_confirm"):
		var def = GameData.get_level_def()
		var sci_idx = GameData.current_level  # one fact per level
		if sci_idx < GameData.SCIENCE_FACTS.size() and !shown_facts.has(sci_idx):
			shown_facts[sci_idx] = true
			science_popup_idx = sci_idx
			state = S.SCIENCE_POPUP
			AudioMgr.sfx_science()
		else:
			_load_next_level()

func _update_science_popup(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_confirm"):
		AudioMgr.sfx_menu_confirm()
		_load_next_level()

func _update_game_over(delta: float) -> void:
	death_timer += delta
	if death_timer > 2 and Input.is_action_just_pressed("ui_confirm"):
		_load_level(GameData.current_level)

func _update_victory(delta: float) -> void:
	victory_timer += delta
	if victory_timer > 3 and Input.is_action_just_pressed("ui_confirm"):
		state = S.TITLE
		AudioMgr.play_title_music()

# ── GAME FLOW ────────────────────────────────────────────────────────────────

func _start_game() -> void:
	GameData.current_level = 0
	GameData.total_score = 0
	GameData.methane_prevented = 0
	GameData.n2o_prevented = 0
	shown_facts.clear()
	_load_level(0)

func _load_level(idx: int) -> void:
	GameData.current_level = idx
	if idx >= GameData.LEVELS.size():
		state = S.VICTORY
		victory_timer = 0
		AudioMgr.stop_music()
		AudioMgr.sfx_level_complete()
		return

	var def = GameData.LEVELS[idx]
	world_node.generate(def)

	var start = world_node.find_start()
	player_node.init_at(start.x, start.y, world_node)
	player_node.visible = false

	# Clear entities
	for s in substrates:
		if is_instance_valid(s):
			s.queue_free()
	substrates.clear()
	for c in colonies:
		if is_instance_valid(c):
			c.queue_free()
	colonies.clear()
	for r in rivals:
		if is_instance_valid(r):
			r.queue_free()
	rivals.clear()
	spawn_timer = 0.0
	rival_move_timer = 0.0
	science_mode = false
	eat_flash_timer = 0.0
	popup_texts.clear()
	starvation_pulse = 0.0

	# Spawn rival microbes
	var num_rivals = def.get("rivals", 0)
	for _r in range(num_rivals):
		_spawn_rival()

	# Camera snap
	if cam:
		cam.position = player_node.position + Vector2(T / 2, T / 2)

	# Music for new world
	var prev_env = -1
	if idx > 0:
		prev_env = GameData.LEVELS[idx - 1].get("env", -1)
	if def["env"] != prev_env:
		AudioMgr.play_env_music(def["env"])

	# Start with mission briefing, then level intro
	mission_idx = 0
	mission_char = 0
	mission_timer = 0.0
	state = S.MISSION_BRIEF

func _load_next_level() -> void:
	GameData.total_score += player_node.score
	GameData.methane_prevented += player_node.methane_eaten
	GameData.n2o_prevented += player_node.n2o_prevented
	_load_level(GameData.current_level + 1)

func _complete_level() -> void:
	var p = player_node
	p.score += GameData.BAL["score_level"]
	state = S.LEVEL_COMPLETE
	complete_timer = 0
	AudioMgr.sfx_level_complete()

# ── ENTITIES ─────────────────────────────────────────────────────────────────

func _update_substrates(delta: float) -> void:
	var def = GameData.get_level_def()
	spawn_timer -= delta
	if spawn_timer <= 0:
		_spawn_substrates(def)
		spawn_timer = GameData.BAL["substrate_spawn"]

	# Move and check collisions
	var to_remove: Array = []
	for i in range(substrates.size() - 1, -1, -1):
		var s = substrates[i]
		if !is_instance_valid(s):
			substrates.remove_at(i)
			continue

		# Flow movement - substrates only move through open pore space
		var tx = int(s.position.x / T)
		var ty = int(s.position.y / T)
		var flow = world_node.get_flow(tx, ty)
		if flow["speed"] > 0:
			var flow_dirs = [Vector2.ZERO, Vector2(1,0), Vector2(0,1), Vector2(-1,0), Vector2(0,-1)]
			var fd: Vector2 = flow_dirs[flow["dir"]]
			var new_pos = s.position + fd * flow["speed"] * T * delta
			# Check if new position is still in open pore (not solid)
			var check_tx = int(new_pos.x / T)
			var check_ty = int(new_pos.y / T)
			var check_tile = world_node.get_tile(check_tx, check_ty)
			if world_node.is_walkable_tile(check_tile):
				s.position = new_pos
				# Small diffusion drift (stays within pore)
				var drift_x = s.position.x + randf_range(-2, 2) * delta
				var drift_y = s.position.y + randf_range(-2, 2) * delta
				var dtx = int(drift_x / T)
				var dty = int(drift_y / T)
				if world_node.is_walkable_tile(world_node.get_tile(dtx, dty)):
					s.position.x = drift_x
					s.position.y = drift_y
			# If blocked by solid, substrate stays put (no teleporting through grains)

		# Check bounds / solid - remove if somehow ended up in solid
		var ntx = int(s.position.x / T)
		var nty = int(s.position.y / T)
		var tile = world_node.get_tile(ntx, nty)
		if tile == GameData.Tile.SOLID or tile == GameData.Tile.VOID \
			or ntx < 0 or ntx >= world_node.map_w or nty < 0 or nty >= world_node.map_h:
			to_remove.append(i)
			continue

		# Player collision
		var dx = s.position.x - player_node.position.x
		var dy = s.position.y - player_node.position.y
		if absf(dx) < T and absf(dy) < T and player_node.alive:
			player_node.eat(s.sub_type)
			if s.sub_type == GameData.Sub.CH4:
				AudioMgr.sfx_eat_methane()
			else:
				AudioMgr.sfx_eat()
			to_remove.append(i)
			continue

		# Lifetime
		s.lifetime -= delta
		if s.lifetime <= 0:
			to_remove.append(i)

	# Remove (reverse order)
	to_remove.sort()
	to_remove.reverse()
	for idx in to_remove:
		if idx < substrates.size():
			var s = substrates[idx]
			if is_instance_valid(s):
				s.queue_free()
			substrates.remove_at(idx)

func _spawn_substrates(def: Dictionary) -> void:
	var density: int = def.get("density", 2)
	var available_subs: Array = def.get("subs", [GameData.Sub.CH4])

	for _n in range(density):
		var spawn_x = -1
		var spawn_y = -1

		# 75% chance spawn at inlet (flow-carried), 25% random pore location
		var use_inlet = randf() < 0.75
		if use_inlet:
			for _attempt in range(20):
				var ty = randi_range(1, world_node.map_h - 2)
				for tx in range(0, mini(5, world_node.map_w)):
					if world_node.is_walkable_tile(world_node.get_tile(tx, ty)):
						spawn_x = tx
						spawn_y = ty
						break
				if spawn_x >= 0:
					break
		else:
			# Spawn at random walkable pore anywhere in the map
			for _attempt in range(30):
				var tx = randi_range(1, world_node.map_w - 2)
				var ty = randi_range(1, world_node.map_h - 2)
				if world_node.is_walkable_tile(world_node.get_tile(tx, ty)):
					spawn_x = tx
					spawn_y = ty
					break
		if spawn_x < 0:
			continue

		var sub_type: int = available_subs[randi_range(0, available_subs.size() - 1)]
		var sub_node = _create_substrate(sub_type)
		sub_node.position = Vector2(spawn_x * T + randf() * T, spawn_y * T + randf() * T)
		entity_layer.add_child(sub_node)
		substrates.append(sub_node)

func _create_substrate(sub_type: int) -> Node2D:
	var node = Node2D.new()
	node.set_meta("sub_type", sub_type)
	node.set_script(preload("res://scripts/substrate.gd"))
	node.sub_type = sub_type
	return node

func _update_colonies(_delta: float) -> void:
	# Colonies passively eat nearby substrates
	for c in colonies:
		if !is_instance_valid(c):
			continue
		for i in range(substrates.size() - 1, -1, -1):
			var s = substrates[i]
			if !is_instance_valid(s):
				continue
			var dist = c.position.distance_to(s.position)
			if dist < T * 1.5 and randf() < 0.02:
				if is_instance_valid(s):
					s.queue_free()
				substrates.remove_at(i)

func _spawn_rival() -> void:
	# Spawn rivals on the LEFT side near inlet where nutrients enter
	for _attempt in range(40):
		var rx = randi_range(2, int(world_node.map_w * 0.4))
		var ry = randi_range(1, world_node.map_h - 2)
		if world_node.is_walkable_tile(world_node.get_tile(rx, ry)):
			var rival_node = Node2D.new()
			rival_node.set_script(preload("res://scripts/rival.gd"))
			rival_node.init_at(rx, ry, world_node)
			entity_layer.add_child(rival_node)
			rivals.append(rival_node)
			return

func _update_rivals(delta: float) -> void:
	rival_move_timer -= delta
	if rival_move_timer > 0:
		return
	rival_move_timer = 0.4  # Rivals move every 0.4 seconds

	for rival in rivals:
		if !is_instance_valid(rival):
			continue
		rival.do_move(substrates, player_node.position if player_node else Vector2.ZERO)

		# Check if rival eats any substrates
		for i in range(substrates.size() - 1, -1, -1):
			var s = substrates[i]
			if !is_instance_valid(s):
				substrates.remove_at(i)
				continue
			var dx = s.position.x - rival.position.x
			var dy = s.position.y - rival.position.y
			if absf(dx) < T and absf(dy) < T:
				if is_instance_valid(s):
					s.queue_free()
				substrates.remove_at(i)
				rival.on_eat()
				break

func _on_player_died() -> void:
	AudioMgr.sfx_die()
	_do_shake(5, 0.5)

func _on_player_divided(tile_pos: Vector2i) -> void:
	# Place colony
	world_node.set_tile(tile_pos.x, tile_pos.y, GameData.Tile.BIOFILM)
	var colony_node = Node2D.new()
	colony_node.set_script(preload("res://scripts/colony_cell.gd"))
	colony_node.position = Vector2(tile_pos.x * T, tile_pos.y * T)
	entity_layer.add_child(colony_node)
	colonies.append(colony_node)
	AudioMgr.sfx_colony_place()
	_do_shake(2, 0.15)

	# Check level goal
	var def = GameData.get_level_def()
	if colonies.size() >= def.get("goal", 5):
		_complete_level()

var eat_flash_timer: float = 0.0
var eat_flash_color: Color = Color.WHITE
var popup_texts: Array = []  # [{text, pos, timer, color}]
var starvation_pulse: float = 0.0

func _on_ate_substrate(sub_type: int) -> void:
	var sub_data = GameData.SUBSTRATES[sub_type]
	eat_flash_timer = 0.15
	eat_flash_color = Color.html(sub_data["glow"])
	_do_shake(1.5, 0.1)
	# Floating +energy popup
	var popup = {
		"text": "+%d %s" % [sub_data["energy"], sub_data["formula"]],
		"pos": player_node.position + Vector2(T / 2, -T / 2),
		"timer": 1.2,
		"color": Color.html(sub_data["color"]),
	}
	popup_texts.append(popup)

func _update_popups(delta: float) -> void:
	for i in range(popup_texts.size() - 1, -1, -1):
		popup_texts[i]["timer"] -= delta
		popup_texts[i]["pos"].y -= delta * 40  # float upward
		if popup_texts[i]["timer"] <= 0:
			popup_texts.remove_at(i)

# ── CAMERA SHAKE ─────────────────────────────────────────────────────────────

func _do_shake(intensity: float, duration: float) -> void:
	shake_intensity = intensity
	shake_duration = duration

func _update_shake(delta: float) -> void:
	if shake_duration > 0:
		shake_duration -= delta
		shake_intensity *= 0.92
		if cam:
			cam.offset = Vector2(
				randf_range(-shake_intensity, shake_intensity),
				randf_range(-shake_intensity, shake_intensity)
			)
	else:
		if cam:
			cam.offset = Vector2.ZERO

# ── DRAWING (UI overlays) ───────────────────────────────────────────────────

func _draw() -> void:
	# These draw in world space - UI overlays are handled by HUD on CanvasLayer
	if state == S.PLAYING:
		if science_mode:
			_draw_science_overlay()
		# Floating popup texts in world space
		_draw_popups()

func _draw_science_overlay() -> void:
	if !world_node or !cam:
		return
	var cam_pos = cam.get_screen_center_position()
	var half = Vector2(GameData.VIEW_W, GameData.VIEW_H) * 0.5
	var start_x = int((cam_pos.x - half.x) / T)
	var end_x = start_x + GameData.COLS + 2
	var start_y = int((cam_pos.y - half.y) / T)
	var end_y = start_y + GameData.ROWS + 2

	var font = ThemeDB.fallback_font
	var t = GameData.game_time

	# Semi-transparent dark overlay for contrast
	var overlay_rect = Rect2(
		maxi(0, start_x) * T, maxi(0, start_y) * T,
		(end_x - start_x) * T, (end_y - start_y) * T)
	draw_rect(overlay_rect, Color(0, 0, 0.05, 0.35))

	for row in range(maxi(0, start_y), mini(world_node.map_h, end_y)):
		for col in range(maxi(0, start_x), mini(world_node.map_w, end_x)):
			var tile = world_node.get_tile(col, row)
			var pos = Vector2(col * T, row * T)

			if tile == GameData.Tile.SOLID:
				# Grid lines on solid (geology visualization)
				draw_rect(Rect2(pos, Vector2(T, T)), Color(0.3, 0.2, 0.1, 0.15), false, 1.0)
				continue

			var flow = world_node.get_flow(col, row)

			# Color-coded flow speed heat map on every walkable tile
			if flow["speed"] > 0.01:
				var spd_norm = clampf(flow["speed"] / 1.5, 0, 1)
				# Blue (slow) -> Cyan -> Green -> Yellow -> Red (fast)
				var heat_col: Color
				if spd_norm < 0.25:
					heat_col = Color(0.1, 0.2, 0.8, 0.25)  # blue
				elif spd_norm < 0.5:
					heat_col = Color(0.1, 0.7, 0.7, 0.3)   # cyan
				elif spd_norm < 0.75:
					heat_col = Color(0.2, 0.8, 0.2, 0.3)   # green
				else:
					heat_col = Color(0.9, 0.6, 0.1, 0.35)   # orange
				draw_rect(Rect2(pos + Vector2(1,1), Vector2(T-2, T-2)), heat_col)

			# Flow direction arrows (every 2nd tile, animated)
			if flow["dir"] > 0 and flow["speed"] > 0.05:
				if (col + row) % 2 == 0:
					var cx = pos.x + T * 0.5
					var cy = pos.y + T * 0.5
					var aoff = fmod(t * 2.0, 1.0) * 6.0
					var aa = clampf(flow["speed"] * 0.8, 0.15, 0.6)
					var ac = Color(1, 1, 1, aa)
					match flow["dir"]:
						1: # right
							draw_rect(Rect2(cx - 6 + aoff, cy - 1, 14, 2), ac)
							draw_rect(Rect2(cx + 5 + aoff, cy - 3, 2, 6), ac)
						2: # down
							draw_rect(Rect2(cx - 1, cy - 6 + aoff, 2, 14), ac)
							draw_rect(Rect2(cx - 3, cy + 5 + aoff, 6, 2), ac)
						3: # left
							draw_rect(Rect2(cx - 8 - aoff, cy - 1, 14, 2), ac)
							draw_rect(Rect2(cx - 8 - aoff, cy - 3, 2, 6), ac)
						4: # up
							draw_rect(Rect2(cx - 1, cy - 8 - aoff, 2, 14), ac)
							draw_rect(Rect2(cx - 3, cy - 8 - aoff, 6, 2), ac)

			# Speed label on every 4th tile
			if font and (col + row) % 4 == 0 and flow["speed"] > 0.05:
				var spd_str = "%.1f" % flow["speed"]
				draw_string(font, pos + Vector2(2, T - 4),
					spd_str, HORIZONTAL_ALIGNMENT_LEFT, -1, 8,
					Color(1, 1, 1, 0.5))

			# Tile type labels on every 3rd tile
			if font and (col * 3 + row) % 5 == 0:
				var label = ""
				var lc = Color.WHITE
				match tile:
					GameData.Tile.PORE:
						label = "PORE"
						lc = Color(0.5, 0.7, 1.0, 0.4)
					GameData.Tile.FLOW_FAST:
						label = "FAST"
						lc = Color(1.0, 0.8, 0.3, 0.5)
					GameData.Tile.TOXIC:
						label = "H2S"
						lc = Color(1.0, 0.3, 0.9, 0.6)
					GameData.Tile.INLET:
						label = "INLET"
						lc = Color(0.4, 0.7, 1.0, 0.7)
					GameData.Tile.OUTLET:
						label = "OUT"
						lc = Color(0.37, 0.81, 0.37, 0.7)
					GameData.Tile.BIOFILM:
						label = "BIO"
						lc = Color(0.37, 0.81, 0.37, 0.5)
				if label != "":
					draw_string(font, pos + Vector2(2, 10),
						label, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, lc)

	# Highlight player tile with crosshair
	if player_node and player_node.alive:
		var ptx = player_node.tile_x
		var pty = player_node.tile_y
		var pp = Vector2(ptx * T, pty * T)
		var pulse = sin(t * 4.0) * 0.15 + 0.6
		draw_rect(Rect2(pp - Vector2(2, 2), Vector2(T + 4, T + 4)),
			Color(0.16, 0.81, 0.69, pulse), false, 2.0)

func _draw_popups() -> void:
	var font = ThemeDB.fallback_font
	if !font:
		return
	for p in popup_texts:
		var alpha = clampf(p["timer"] / 0.6, 0, 1)
		var col: Color = p["color"]
		col.a = alpha
		# Shadow
		draw_string(font, p["pos"] + Vector2(2, 2), p["text"],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0, 0, 0, alpha * 0.8))
		draw_string(font, p["pos"], p["text"],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 14, col)
