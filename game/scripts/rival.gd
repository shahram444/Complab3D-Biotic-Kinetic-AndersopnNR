extends Node2D
## Rival microbe - competes with ARKE for substrates.
## Navigates pores seeking food, creates meaningful competition.

const T := GameData.TILE
const SENSE_RANGE := 6  # Tiles radius to detect substrates
const PLAYER_SENSE := 8 # Tiles radius to detect player (for competition)

var tile_x: int = 0
var tile_y: int = 0
var target_pos := Vector2.ZERO
var moving := false
var world_ref: Node2D = null
var anim_timer: float = 0.0
var eat_flash: float = 0.0
var move_dir: int = 1  # Preferred direction: 0=random, 1=right, 2=down, 3=left, 4=up
var hunger: float = 0.0 # Increases over time, makes rival more aggressive

func init_at(tx: int, ty: int, world: Node2D) -> void:
	tile_x = tx
	tile_y = ty
	position = Vector2(tx * T, ty * T)
	target_pos = position
	world_ref = world
	move_dir = randi_range(1, 4)
	hunger = 0.0

func _process(delta: float) -> void:
	anim_timer += delta
	hunger += delta * 0.3
	if eat_flash > 0:
		eat_flash -= delta

	# Smooth movement interpolation
	if moving:
		var speed = 2.0 * T * 2.5
		var diff = target_pos - position
		var dist = diff.length()
		if dist < speed * delta:
			position = target_pos
			moving = false
		else:
			position += diff.normalized() * speed * delta

	queue_redraw()

func do_move(substrate_nodes: Array = [], player_pos: Vector2 = Vector2.ZERO) -> void:
	if moving or !world_ref:
		return

	var dirs = [Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0), Vector2i(0,-1)]
	var roll = randf()
	var seek_chance = clampf(0.45 + hunger * 0.05, 0.45, 0.75)

	# 45-75% chance: Seek nearest substrate (increases with hunger)
	if roll < seek_chance and substrate_nodes.size() > 0:
		var best_dir = _seek_substrate(substrate_nodes, dirs)
		if best_dir != Vector2i.ZERO:
			var ntx = tile_x + best_dir.x
			var nty = tile_y + best_dir.y
			if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
				_move_to(ntx, nty)
				_update_dir(best_dir)
				return

	# 15% chance: Move toward player area (compete for same food zone)
	if roll < seek_chance + 0.15 and player_pos != Vector2.ZERO:
		var ptx = int(player_pos.x / T)
		var pty = int(player_pos.y / T)
		var dx = ptx - tile_x
		var dy = pty - tile_y
		if absi(dx) + absi(dy) < PLAYER_SENSE:
			var toward = _step_toward(dx, dy, dirs)
			if toward != Vector2i.ZERO:
				var ntx = tile_x + toward.x
				var nty = tile_y + toward.y
				if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
					_move_to(ntx, nty)
					_update_dir(toward)
					return

	# Remaining: follow flow or wander with preferred direction
	var preferred = dirs[move_dir - 1] if move_dir >= 1 and move_dir <= 4 else dirs[0]

	# Check if flow can guide us
	var flow = world_ref.get_flow(tile_x, tile_y)
	if flow["speed"] > 0.1 and randf() < 0.4:
		var flow_dirs = [Vector2i(0,0), Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0), Vector2i(0,-1)]
		if flow["dir"] >= 1 and flow["dir"] <= 4:
			var fd = flow_dirs[flow["dir"]]
			var ntx = tile_x + fd.x
			var nty = tile_y + fd.y
			if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
				_move_to(ntx, nty)
				_update_dir(fd)
				return

	# Try preferred direction
	var ntx = tile_x + preferred.x
	var nty = tile_y + preferred.y
	if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
		_move_to(ntx, nty)
		if randf() < 0.25:
			move_dir = randi_range(1, 4)
		return

	# Fallback: try random directions
	dirs.shuffle()
	for d in dirs:
		ntx = tile_x + d.x
		nty = tile_y + d.y
		if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
			_move_to(ntx, nty)
			_update_dir(d)
			return

func _seek_substrate(subs: Array, _dirs: Array) -> Vector2i:
	var best_dist := 999.0
	var best_pos := Vector2.ZERO
	var my_pos = Vector2(tile_x * T, tile_y * T)
	for s in subs:
		if !is_instance_valid(s):
			continue
		var dist = my_pos.distance_to(s.position)
		if dist < SENSE_RANGE * T and dist < best_dist:
			best_dist = dist
			best_pos = s.position
	if best_dist >= 999.0:
		return Vector2i.ZERO
	var dx = int(best_pos.x / T) - tile_x
	var dy = int(best_pos.y / T) - tile_y
	return _step_toward(dx, dy, [Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0), Vector2i(0,-1)])

func _step_toward(dx: int, dy: int, dirs: Array) -> Vector2i:
	# Pick direction that reduces distance to target
	if absi(dx) >= absi(dy):
		var d = Vector2i(signi(dx), 0) if dx != 0 else dirs[0]
		if world_ref.is_walkable_tile(world_ref.get_tile(tile_x + d.x, tile_y + d.y)):
			return d
		# Try perpendicular
		if dy != 0:
			d = Vector2i(0, signi(dy))
			if world_ref.is_walkable_tile(world_ref.get_tile(tile_x + d.x, tile_y + d.y)):
				return d
	else:
		var d = Vector2i(0, signi(dy)) if dy != 0 else dirs[1]
		if world_ref.is_walkable_tile(world_ref.get_tile(tile_x + d.x, tile_y + d.y)):
			return d
		if dx != 0:
			d = Vector2i(signi(dx), 0)
			if world_ref.is_walkable_tile(world_ref.get_tile(tile_x + d.x, tile_y + d.y)):
				return d
	return Vector2i.ZERO

func _update_dir(d: Vector2i) -> void:
	if d == Vector2i(1,0): move_dir = 1
	elif d == Vector2i(0,1): move_dir = 2
	elif d == Vector2i(-1,0): move_dir = 3
	elif d == Vector2i(0,-1): move_dir = 4

func _move_to(ntx: int, nty: int) -> void:
	tile_x = ntx
	tile_y = nty
	target_pos = Vector2(ntx * T, nty * T)
	moving = true

func on_eat() -> void:
	eat_flash = 0.3
	hunger = 0.0  # Reset hunger after eating

func _draw() -> void:
	var bob = sin(anim_timer * 3.0) * 2.0
	var time = anim_timer

	# Bright red pulsing glow so rival is always visible
	var pulse = sin(time * 2.5) * 0.15 + 0.4
	# Outer glow
	draw_rect(Rect2(Vector2(-2, -2 + bob), Vector2(36, 36)),
		Color(1.0, 0.2, 0.15, pulse * 0.35))
	# Inner dark background
	draw_rect(Rect2(Vector2(2, 2 + bob), Vector2(28, 28)),
		Color(0.3, 0.05, 0.05, 0.5))

	# Shadow
	draw_rect(Rect2(Vector2(4, 22 + bob), Vector2(24, 3)), Color(0, 0, 0, 0.35))

	# Draw rival sprite
	var tex = SpriteFactory.get_tex("rival")
	if tex:
		draw_texture(tex, Vector2(6, bob))

	# Red border markers
	var c = Color(1, 0.3, 0.3, 0.7)
	draw_rect(Rect2(Vector2(2, 2 + bob), Vector2(5, 2)), c)
	draw_rect(Rect2(Vector2(2, 2 + bob), Vector2(2, 5)), c)
	draw_rect(Rect2(Vector2(25, 2 + bob), Vector2(5, 2)), c)
	draw_rect(Rect2(Vector2(28, 2 + bob), Vector2(2, 5)), c)
	draw_rect(Rect2(Vector2(2, 22 + bob), Vector2(5, 2)), c)
	draw_rect(Rect2(Vector2(2, 19 + bob), Vector2(2, 5)), c)
	draw_rect(Rect2(Vector2(25, 22 + bob), Vector2(5, 2)), c)
	draw_rect(Rect2(Vector2(28, 19 + bob), Vector2(2, 5)), c)

	# Eat flash
	if eat_flash > 0:
		draw_rect(Rect2(Vector2(2, bob - 2), Vector2(28, 28)),
			Color(1, 0.3, 0.3, eat_flash))

	# "!" danger indicator above rival
	var font = ThemeDB.fallback_font
	if font:
		var ex_alpha = sin(time * 4.0) * 0.3 + 0.5
		draw_string(font, Vector2(10, -6 + bob), "!", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1, 0.3, 0.3, ex_alpha))
