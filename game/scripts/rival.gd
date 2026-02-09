extends Node2D
## Rival microbe - competes with METHI for substrates.
## Wanders through pores, eats nutrients, creates competition.

const T := GameData.TILE

var tile_x: int = 0
var tile_y: int = 0
var target_pos := Vector2.ZERO
var moving := false
var world_ref: Node2D = null
var anim_timer: float = 0.0
var eat_flash: float = 0.0
var move_dir: int = 1  # Preferred direction: 0=random, 1=right, 2=down, 3=left, 4=up

func init_at(tx: int, ty: int, world: Node2D) -> void:
	tile_x = tx
	tile_y = ty
	position = Vector2(tx * T, ty * T)
	target_pos = position
	world_ref = world
	move_dir = randi_range(1, 4)

func _process(delta: float) -> void:
	anim_timer += delta
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

func do_move() -> void:
	if moving or !world_ref:
		return

	# Movement AI: prefer current direction, but turn randomly
	var dirs = [Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0), Vector2i(0,-1)]
	var preferred = dirs[move_dir - 1] if move_dir >= 1 and move_dir <= 4 else dirs[0]

	# Try preferred direction first
	var ntx = tile_x + preferred.x
	var nty = tile_y + preferred.y
	if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
		_move_to(ntx, nty)
		# Small chance to change direction
		if randf() < 0.2:
			move_dir = randi_range(1, 4)
		return

	# Try random directions
	dirs.shuffle()
	for d in dirs:
		ntx = tile_x + d.x
		nty = tile_y + d.y
		if world_ref.is_walkable_tile(world_ref.get_tile(ntx, nty)):
			_move_to(ntx, nty)
			# Update preferred direction
			if d == Vector2i(1,0): move_dir = 1
			elif d == Vector2i(0,1): move_dir = 2
			elif d == Vector2i(-1,0): move_dir = 3
			elif d == Vector2i(0,-1): move_dir = 4
			return

func _move_to(ntx: int, nty: int) -> void:
	tile_x = ntx
	tile_y = nty
	target_pos = Vector2(ntx * T, nty * T)
	moving = true

func on_eat() -> void:
	eat_flash = 0.3

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
