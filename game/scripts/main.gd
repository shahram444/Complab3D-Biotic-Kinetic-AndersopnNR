extends Node2D
## Main game controller - state machine, scene management, UI overlays.

const S := GameData.State
const T := GameData.TILE

var state: int = S.BOOT
var boot_timer: float = 0.0
var story_scroll: float = 0.0
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
var spawn_timer: float = 0.0

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
		story_scroll = 0

func _update_narrative(delta: float) -> void:
	story_scroll += delta * 22
	if Input.is_action_just_pressed("ui_confirm"):
		if story_scroll > GameData.NARRATIVE_LINES.size() * 12 + 40:
			_start_game()
		else:
			story_scroll = GameData.NARRATIVE_LINES.size() * 12 + 60

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

	# Camera follow
	if player_node and cam:
		cam.position = player_node.position + Vector2(8, 8)
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
	spawn_timer = 0.0
	science_mode = false

	# Camera snap
	if cam:
		cam.position = player_node.position + Vector2(8, 8)

	# Music for new world
	var prev_env = -1
	if idx > 0:
		prev_env = GameData.LEVELS[idx - 1].get("env", -1)
	if def["env"] != prev_env:
		AudioMgr.play_env_music(def["env"])

	state = S.LEVEL_INTRO
	intro_timer = 0

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

		# Flow movement
		var tx = int(s.position.x / T)
		var ty = int(s.position.y / T)
		var flow = world_node.get_flow(tx, ty)
		if flow["speed"] > 0:
			var flow_dirs = [Vector2.ZERO, Vector2(1,0), Vector2(0,1), Vector2(-1,0), Vector2(0,-1)]
			var fd: Vector2 = flow_dirs[flow["dir"]]
			s.position += fd * flow["speed"] * T * delta
			# Diffusion drift
			s.position.x += randf_range(-3, 3) * delta
			s.position.y += randf_range(-3, 3) * delta

		# Check bounds / solid
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
		# Find spawn location (left side)
		var spawn_x = -1
		var spawn_y = -1
		for _attempt in range(20):
			var ty = randi_range(1, world_node.map_h - 2)
			for tx in range(0, mini(5, world_node.map_w)):
				if world_node.is_walkable_tile(world_node.get_tile(tx, ty)):
					spawn_x = tx
					spawn_y = ty
					break
			if spawn_x >= 0:
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

func _on_ate_substrate(sub_type: int) -> void:
	pass  # Could add screen effects here

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
	if science_mode and state == S.PLAYING:
		_draw_science_overlay()

func _draw_science_overlay() -> void:
	if !world_node or !cam:
		return
	var cam_pos = cam.get_screen_center_position()
	var half = Vector2(GameData.VIEW_W, GameData.VIEW_H) * 0.5
	var start_x = int((cam_pos.x - half.x) / T)
	var end_x = start_x + GameData.COLS + 2
	var start_y = int((cam_pos.y - half.y) / T)
	var end_y = start_y + GameData.ROWS + 2

	for row in range(maxi(0, start_y), mini(world_node.map_h, end_y)):
		for col in range(maxi(0, start_x), mini(world_node.map_w, end_x)):
			var flow = world_node.get_flow(col, row)
			if flow["dir"] == 0 or flow["speed"] < 0.05:
				continue
			if (col + row) % 3 != 0:
				continue
			var pos = Vector2(col * T + 4, row * T + 4)
			var alpha = clampf(flow["speed"] * 1.2, 0.1, 0.7)
			var arrow_key = "arrow_r" if flow["dir"] == 1 or flow["dir"] == 3 else "arrow_d"
			var tex = SpriteFactory.get_tex(arrow_key)
			if tex:
				draw_texture(tex, pos, Color(1, 1, 1, alpha))
