extends Node2D
## METHI - The methanotrophic archaea player character.
## Handles movement, flow riding, eating, growth, and division.

const T := GameData.TILE
const BAL := GameData.BAL

var tile_x: int = 0
var tile_y: int = 0
var target_pos := Vector2.ZERO
var moving := false
var direction := "down"  # down, up, left, right

var health: float = BAL["max_health"]
var energy: float = BAL["max_energy"]
var growth: float = 0.0
var alive := true
var score: int = 0
var colonies_placed: int = 0
var substrates_eaten: int = 0
var methane_eaten: int = 0
var n2o_prevented: int = 0

var move_timer: float = 0.0
var move_interval: float = 1.0 / BAL["move_speed"]
var anim_frame: int = 0
var anim_timer: float = 0.0
var hurt_timer: float = 0.0
var eat_timer: float = 0.0
var death_timer: float = 0.0
var invincible_timer: float = 0.0
var flash_timer: float = 0.0
var riding_flow := false

var world_ref: Node2D = null  # Reference to world node

signal died
signal divided(tile_pos: Vector2i)
signal ate_substrate(sub_type: int)

func init_at(tx: int, ty: int, world: Node2D) -> void:
	tile_x = tx
	tile_y = ty
	position = Vector2(tx * T, ty * T)
	target_pos = position
	world_ref = world
	health = BAL["max_health"]
	energy = BAL["max_energy"]
	growth = 0.0
	alive = true
	score = 0
	colonies_placed = 0
	substrates_eaten = 0
	methane_eaten = 0
	n2o_prevented = 0
	moving = false
	direction = "right"
	hurt_timer = 0.0
	eat_timer = 0.0
	death_timer = 0.0
	invincible_timer = 0.0
	riding_flow = false
	visible = true

func _process(delta: float) -> void:
	if !alive:
		death_timer += delta
		# Fade out
		if death_timer > 2.0:
			modulate.a = maxf(0, 1.0 - (death_timer - 2.0))
		queue_redraw()
		return

	_handle_movement(delta)
	_handle_flow_riding(delta)
	_update_survival(delta)
	_update_timers(delta)
	_check_death()
	queue_redraw()

func _handle_movement(delta: float) -> void:
	move_timer -= delta
	if move_timer <= 0 and !moving:
		var dx := 0
		var dy := 0
		if Input.is_action_pressed("move_up"):
			dy = -1; direction = "up"
		elif Input.is_action_pressed("move_down"):
			dy = 1; direction = "down"
		elif Input.is_action_pressed("move_left"):
			dx = -1; direction = "left"
		elif Input.is_action_pressed("move_right"):
			dx = 1; direction = "right"

		if (dx != 0 or dy != 0) and world_ref:
			var ntx = tile_x + dx
			var nty = tile_y + dy
			var tile = world_ref.get_tile(ntx, nty)
			if world_ref.is_walkable_tile(tile):
				tile_x = ntx
				tile_y = nty
				target_pos = Vector2(ntx * T, nty * T)
				moving = true
				move_timer = move_interval

func _handle_flow_riding(delta: float) -> void:
	if !world_ref:
		return
	riding_flow = Input.is_action_pressed("ride_flow")
	if riding_flow:
		var flow = world_ref.get_flow(tile_x, tile_y)
		if flow["speed"] > 0.05 and !moving:
			var flow_dirs = [Vector2i(0,0), Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0), Vector2i(0,-1)]
			var fd: Vector2i = flow_dirs[flow["dir"]]
			if fd != Vector2i.ZERO:
				var ntx = tile_x + fd.x
				var nty = tile_y + fd.y
				if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
					tile_x = ntx
					tile_y = nty
					target_pos = Vector2(ntx * T, nty * T)
					moving = true
					move_timer = move_interval / BAL["flow_ride_mult"]
					# Small energy cost for planktonic movement
					energy -= 0.5

	# Smooth position interpolation
	if moving:
		var speed = BAL["move_speed"] * T * 2.8
		var diff = target_pos - position
		var dist = diff.length()
		if dist < speed * delta:
			position = target_pos
			moving = false
		else:
			position += diff.normalized() * speed * delta

func _update_survival(delta: float) -> void:
	# Starvation
	health -= BAL["health_decay"] * delta
	energy -= BAL["energy_decay"] * delta

	# Toxic damage
	if world_ref:
		var current_tile = world_ref.get_tile(tile_x, tile_y)
		if current_tile == GameData.Tile.TOXIC and invincible_timer <= 0:
			health -= BAL["toxic_damage"] * delta
			hurt_timer = 0.12

	# Growth decay (slow)
	if growth > 0:
		growth -= 0.15 * delta
		growth = maxf(0, growth)

	# Clamp
	health = clampf(health, 0, BAL["max_health"])
	energy = clampf(energy, 0, BAL["max_energy"])
	growth = clampf(growth, 0, BAL["division_cost"])

func _update_timers(delta: float) -> void:
	anim_timer += delta
	if anim_timer > 0.2:
		anim_timer = 0
		anim_frame = (anim_frame + 1) % 2
	if hurt_timer > 0:
		hurt_timer -= delta
	if eat_timer > 0:
		eat_timer -= delta
	if invincible_timer > 0:
		invincible_timer -= delta
	if can_divide():
		flash_timer += delta
	else:
		flash_timer = 0

func _check_death() -> void:
	if health <= 0 and alive:
		alive = false
		death_timer = 0
		died.emit()

func eat(sub_type: int) -> void:
	var sub_data = GameData.SUBSTRATES[sub_type]
	health = minf(BAL["max_health"], health + sub_data["energy"])
	energy = minf(BAL["max_energy"], energy + sub_data["energy"] * 0.5)
	growth = minf(BAL["division_cost"], growth + sub_data["growth"])
	score += BAL["score_eat"]
	substrates_eaten += 1
	eat_timer = 0.12

	if sub_type == GameData.Sub.CH4:
		methane_eaten += 1
		score += BAL["score_methane"]
	elif sub_type == GameData.Sub.NO3:
		n2o_prevented += 1
		score += BAL["score_no3"]

	ate_substrate.emit(sub_type)

func can_divide() -> bool:
	return growth >= BAL["division_cost"]

func try_divide() -> bool:
	if !can_divide() or !world_ref:
		return false
	var pores = world_ref.get_adjacent_pores(tile_x, tile_y)
	if pores.size() == 0:
		return false

	# Pick best spot (furthest from solid)
	var best: Vector2i = pores[0]
	var best_dist: int = 0
	for p in pores:
		var d = world_ref.get_distance(p.x, p.y)
		if d > best_dist:
			best_dist = d
			best = p

	growth = 0
	colonies_placed += 1
	score += BAL["score_colony"]
	divided.emit(best)
	return true

func can_ride_flow() -> bool:
	if !world_ref:
		return false
	var flow = world_ref.get_flow(tile_x, tile_y)
	return flow["speed"] > 0.05

# ── DRAWING ──────────────────────────────────────────────────────────────────

func _draw() -> void:
	var time = GameData.game_time
	var bob = sin(time * 4.0) * 1.0 if alive else 0.0

	# Shadow
	if alive:
		draw_rect(Rect2(Vector2(3, 14 + bob), Vector2(10, 2)), Color(0, 0, 0, 0.3))

	# Select sprite
	var tex_key: String
	if !alive:
		tex_key = "methi_die"
	elif hurt_timer > 0:
		tex_key = "methi_hurt"
	elif eat_timer > 0:
		tex_key = "methi_eat"
	elif can_divide():
		tex_key = "methi_glow"
	else:
		tex_key = "methi_" + direction

	var tex = SpriteFactory.get_tex(tex_key)
	if tex:
		draw_texture(tex, Vector2(0, bob))

	# Division ready glow
	if can_divide() and alive:
		var glow = sin(flash_timer * 6.0) * 0.25 + 0.25
		draw_rect(Rect2(Vector2(-1, -1 + bob), Vector2(18, 18)),
			Color(1, 1, 0.37, glow))

	# Flow riding indicator
	if riding_flow and alive:
		var alpha = sin(time * 6.0) * 0.2 + 0.3
		draw_rect(Rect2(Vector2(-2, -2 + bob), Vector2(20, 20)),
			Color(0.3, 0.6, 1.0, alpha))

	# Health warning
	if alive and health < 25:
		var flash = 0.3 if sin(time * 8.0) > 0 else 0.0
		draw_rect(Rect2(Vector2(0, bob), Vector2(16, 16)), Color(1, 0, 0, flash))
