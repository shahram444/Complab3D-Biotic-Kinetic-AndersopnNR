extends Node2D
## Procedural pore-geometry world generation, flow field, and tile rendering.

const T := GameData.TILE
const Tile := GameData.Tile

var map: Array = []     # 2D array of Tile enum
var flow_dir: Array = []  # 2D: 0=none, 1=right, 2=down, 3=left, 4=up
var flow_spd: Array = []  # 2D: float speed
var dist_map: Array = []  # 2D: distance to nearest solid
var map_w: int = 0
var map_h: int = 0
var env_idx: int = 0

var _rng := RandomNumberGenerator.new()

# ── GENERATION ───────────────────────────────────────────────────────────────

func generate(level_def: Dictionary) -> void:
	env_idx = level_def.get("env", 0)
	map_w = level_def.get("w", 30)
	map_h = level_def.get("h", 20)
	_rng.seed = env_idx * 1000 + map_w * 31 + map_h * 17 + level_def.get("goal", 5) * 137

	# Initialize all solid
	map.resize(map_h)
	flow_dir.resize(map_h)
	flow_spd.resize(map_h)
	dist_map.resize(map_h)
	for y in range(map_h):
		map[y] = []
		flow_dir[y] = []
		flow_spd[y] = []
		dist_map[y] = []
		map[y].resize(map_w)
		flow_dir[y].resize(map_w)
		flow_spd[y].resize(map_w)
		dist_map[y].resize(map_w)
		for x in range(map_w):
			map[y][x] = Tile.SOLID
			flow_dir[y][x] = 0
			flow_spd[y][x] = 0.0
			dist_map[y][x] = 999

	# Generate based on environment
	match env_idx:
		0: _gen_soil(level_def)
		1: _gen_deep_sediment(level_def)
		2: _gen_methane_seeps(level_def)
		3: _gen_permafrost(level_def)
		4: _gen_hydrothermal(level_def)
		_: _gen_soil(level_def)

	_ensure_connectivity()
	_place_inlet_outlet()
	_compute_flow(level_def.get("flow", 0.5))
	_compute_distance()

	if level_def.get("toxic", 0.0) > 0:
		_add_toxic(level_def.get("toxic", 0.15))

	queue_redraw()

# ── ENVIRONMENT GENERATORS ───────────────────────────────────────────────────

func _gen_soil(def: Dictionary) -> void:
	# Wide channels between round grains - friendly, open
	_fill_all(Tile.PORE)
	var gs = def.get("grain", [2, 3])
	var avg_r = (gs[0] + gs[1]) * 0.5
	var avg_area = PI * avg_r * avg_r
	var num = int(map_w * map_h * (1.0 - def.get("porosity", 0.6)) / maxf(avg_area, 4.0))
	for _i in range(num):
		var gx = _rng.randi_range(2, map_w - 3)
		var gy = _rng.randi_range(2, map_h - 3)
		var gr = _rng.randi_range(gs[0], gs[1])
		_place_circle(gx, gy, gr, Tile.SOLID)
	_add_borders()

func _gen_deep_sediment(def: Dictionary) -> void:
	# Maze-like: tight channels carved from solid
	_fill_all(Tile.SOLID)
	var cw = int((map_w - 2) / 2)
	var ch = int((map_h - 2) / 2)
	var visited = []
	visited.resize(ch)
	for y in range(ch):
		visited[y] = []
		visited[y].resize(cw)
		for x in range(cw):
			visited[y][x] = false

	# Recursive backtracker maze
	var stack: Array = []
	var cx = 0
	var cy = 0
	visited[cy][cx] = true
	stack.push_back(Vector2i(cx, cy))
	var dirs = [Vector2i(0,-1), Vector2i(1,0), Vector2i(0,1), Vector2i(-1,0)]

	while stack.size() > 0:
		var neighbors = []
		for d in dirs:
			var nx = cx + d.x
			var ny = cy + d.y
			if nx >= 0 and nx < cw and ny >= 0 and ny < ch and !visited[ny][nx]:
				neighbors.append(Vector2i(d.x, d.y))
		if neighbors.size() > 0:
			var chosen = neighbors[_rng.randi_range(0, neighbors.size() - 1)]
			var nx = cx + chosen.x
			var ny = cy + chosen.y
			# Carve passage
			map[1 + cy * 2][1 + cx * 2] = Tile.PORE
			map[1 + cy * 2 + chosen.y][1 + cx * 2 + chosen.x] = Tile.PORE
			map[1 + ny * 2][1 + nx * 2] = Tile.PORE
			visited[ny][nx] = true
			stack.push_back(Vector2i(cx, cy))
			cx = nx
			cy = ny
		else:
			var prev = stack.pop_back()
			cx = prev.x
			cy = prev.y

	# Widen passages aggressively for better navigation
	var map_copy = []
	for y in range(map_h):
		map_copy.append(map[y].duplicate())
	for y in range(2, map_h - 2):
		for x in range(2, map_w - 2):
			if map_copy[y][x] == Tile.PORE and _rng.randf() < 0.6:
				# Open up adjacent cells in 1-2 directions
				var widen_dirs = [Vector2i(0,-1),Vector2i(1,0),Vector2i(0,1),Vector2i(-1,0)]
				var num_opens = 1 if _rng.randf() < 0.5 else 2
				for _o in range(num_opens):
					var d = _rng.randi_range(0, 3)
					var nx = x + widen_dirs[d].x
					var ny = y + widen_dirs[d].y
					if ny > 0 and ny < map_h-1 and nx > 0 and nx < map_w-1:
						map[ny][nx] = Tile.PORE
	_add_borders()

func _gen_methane_seeps(def: Dictionary) -> void:
	# Open areas with vent channels from bottom
	_gen_soil(def)
	# Add vertical vent channels
	var num_vents = _rng.randi_range(3, 6)
	for _v in range(num_vents):
		var vx = _rng.randi_range(4, map_w - 5)
		var vy = map_h - 2
		var width = _rng.randi_range(1, 2)
		while vy > 1:
			for w in range(-width, width + 1):
				if vx + w > 0 and vx + w < map_w - 1:
					map[vy][vx + w] = Tile.PORE
			vy -= 1
			vx += _rng.randi_range(-1, 1)
			vx = clampi(vx, 2, map_w - 3)

func _gen_permafrost(def: Dictionary) -> void:
	# Wide horizontal flow channels with ice-like obstructions
	_fill_all(Tile.SOLID)
	var num_channels = _rng.randi_range(4, 6)
	var spacing = map_h / (num_channels + 1)
	for i in range(num_channels):
		var base_y = spacing * (i + 1)
		var width = _rng.randi_range(2, 4)
		for x in range(map_w):
			var wobble = int(sin(x * 0.25 + i) * 1.5)
			for dy in range(-width, width + 1):
				var ty = base_y + dy + wobble
				if ty > 0 and ty < map_h - 1:
					map[ty][x] = Tile.PORE
	# Vertical connectors
	for _c in range(_rng.randi_range(8, 15)):
		var cx = _rng.randi_range(3, map_w - 4)
		var sy = _rng.randi_range(2, map_h - 3)
		var length = _rng.randi_range(4, spacing + 3)
		for dy in range(length):
			var ty = sy + dy
			if ty > 0 and ty < map_h - 1:
				map[ty][cx] = Tile.PORE
				if _rng.randf() < 0.4 and cx + 1 < map_w - 1:
					map[ty][cx + 1] = Tile.PORE
	# Mark wide channels as fast flow
	for y in range(map_h):
		for x in range(map_w):
			if map[y][x] == Tile.PORE:
				var count = 0
				for dy in range(-2, 3):
					var ty = y + dy
					if ty >= 0 and ty < map_h and map[ty][x] != Tile.SOLID:
						count += 1
				if count >= 4:
					map[y][x] = Tile.FLOW_FAST
	_add_borders()

func _gen_hydrothermal(def: Dictionary) -> void:
	# Complex: mix of chambers, vents, and narrow passages
	_fill_all(Tile.SOLID)
	# Chambers
	for _ch in range(_rng.randi_range(6, 10)):
		var cx = _rng.randi_range(5, map_w - 6)
		var cy = _rng.randi_range(5, map_h - 6)
		var r = _rng.randi_range(2, 4)
		_place_circle(cx, cy, r, Tile.PORE)
	# Connect chambers with tunnels
	for _t in range(_rng.randi_range(10, 18)):
		var sx = _rng.randi_range(3, map_w - 4)
		var sy = _rng.randi_range(3, map_h - 4)
		var dx_dir = _rng.randi_range(-1, 1)
		var dy_dir = _rng.randi_range(-1, 1)
		if dx_dir == 0 and dy_dir == 0:
			dx_dir = 1
		var length = _rng.randi_range(5, 15)
		var cx = sx
		var cy = sy
		for _s in range(length):
			if cx > 0 and cx < map_w - 1 and cy > 0 and cy < map_h - 1:
				map[cy][cx] = Tile.PORE
			cx += dx_dir
			cy += dy_dir
			if _rng.randf() < 0.3:
				dx_dir = _rng.randi_range(-1, 1)
			if _rng.randf() < 0.3:
				dy_dir = _rng.randi_range(-1, 1)
	# Vent columns from bottom
	for _v in range(_rng.randi_range(2, 4)):
		var vx = _rng.randi_range(5, map_w - 6)
		for vy in range(map_h - 2, 1, -1):
			map[vy][vx] = Tile.FLOW_FAST
			if _rng.randf() < 0.3:
				vx += _rng.randi_range(-1, 1)
				vx = clampi(vx, 2, map_w - 3)
	_add_borders()

# ── HELPERS ──────────────────────────────────────────────────────────────────

func _fill_all(tile: int) -> void:
	for y in range(map_h):
		for x in range(map_w):
			map[y][x] = tile

func _place_circle(cx: int, cy: int, r: int, tile: int) -> void:
	for dy in range(-r, r + 1):
		for dx in range(-r, r + 1):
			if dx * dx + dy * dy <= r * r:
				var tx = cx + dx
				var ty = cy + dy
				if tx >= 1 and tx < map_w - 1 and ty >= 1 and ty < map_h - 1:
					map[ty][tx] = tile

func _add_borders() -> void:
	for x in range(map_w):
		map[0][x] = Tile.SOLID
		map[map_h - 1][x] = Tile.SOLID
	for y in range(map_h):
		map[y][0] = Tile.SOLID
		map[y][map_w - 1] = Tile.SOLID

func _ensure_connectivity() -> void:
	# Flood fill from first pore to find reachable set
	var start := Vector2i(-1, -1)
	for y in range(1, map_h - 1):
		for x in range(1, int(map_w * 0.3)):
			if is_walkable_tile(map[y][x]):
				start = Vector2i(x, y)
				break
		if start.x >= 0:
			break
	if start.x < 0:
		start = Vector2i(2, map_h / 2)
		map[start.y][start.x] = Tile.PORE

	var visited := {}
	var queue: Array = [start]
	visited[start] = true
	while queue.size() > 0:
		var c: Vector2i = queue.pop_front()
		for d in [Vector2i(0,-1),Vector2i(1,0),Vector2i(0,1),Vector2i(-1,0)]:
			var n = c + d
			if n.x >= 0 and n.x < map_w and n.y >= 0 and n.y < map_h:
				if !visited.has(n) and is_walkable_tile(map[n.y][n.x]):
					visited[n] = true
					queue.append(n)

	# Connect isolated pores via 2-wide paths for better navigation
	for y in range(1, map_h - 1):
		for x in range(1, map_w - 1):
			if is_walkable_tile(map[y][x]) and !visited.has(Vector2i(x, y)):
				var cx = x
				var cy = y
				for _step in range(map_w + map_h):
					if visited.has(Vector2i(cx, cy)):
						break
					if abs(cx - start.x) > abs(cy - start.y):
						cx += 1 if cx < start.x else -1
					else:
						cy += 1 if cy < start.y else -1
					cx = clampi(cx, 1, map_w - 2)
					cy = clampi(cy, 1, map_h - 2)
					# Carve 2-wide path for navigability
					if map[cy][cx] == Tile.SOLID:
						map[cy][cx] = Tile.PORE
					if cy + 1 < map_h - 1 and map[cy + 1][cx] == Tile.SOLID:
						map[cy + 1][cx] = Tile.PORE
					visited[Vector2i(cx, cy)] = true

	# Ensure right side reachable via 2-wide path
	var has_right = false
	for y in range(1, map_h - 1):
		if is_walkable_tile(map[y][map_w - 2]) and visited.has(Vector2i(map_w - 2, y)):
			has_right = true
			break
	if !has_right:
		var mid_y = map_h / 2
		for x in range(map_w - 2, 0, -1):
			if map[mid_y][x] == Tile.SOLID:
				map[mid_y][x] = Tile.PORE
			if mid_y + 1 < map_h - 1 and map[mid_y + 1][x] == Tile.SOLID:
				map[mid_y + 1][x] = Tile.PORE
			if visited.has(Vector2i(x, mid_y)):
				break

func _place_inlet_outlet() -> void:
	for x in range(map_w):
		for y in range(1, map_h - 1):
			if is_walkable_tile(map[y][x]):
				map[y][x] = Tile.INLET
				_place_outlet()
				return

func _place_outlet() -> void:
	for x in range(map_w - 1, -1, -1):
		for y in range(1, map_h - 1):
			if is_walkable_tile(map[y][x]):
				map[y][x] = Tile.OUTLET
				return

func _compute_flow(base_speed: float) -> void:
	# Simplified pressure-driven flow: pressure gradient left to right
	var pressure: Array = []
	pressure.resize(map_h)
	for y in range(map_h):
		pressure[y] = []
		pressure[y].resize(map_w)
		for x in range(map_w):
			# Initialize with linear gradient so flow has a baseline
			pressure[y][x] = 1.0 - float(x) / float(map_w - 1)
	# Fixed boundary conditions
	for y in range(map_h):
		pressure[y][0] = 1.0
		pressure[y][map_w - 1] = 0.0

	# Jacobi iteration - include boundary cells in neighbor averaging
	for _iter in range(60):
		for y in range(1, map_h - 1):
			for x in range(1, map_w - 1):
				if map[y][x] == Tile.SOLID:
					continue
				var s = 0.0
				var c = 0
				for d in [Vector2i(0,-1),Vector2i(1,0),Vector2i(0,1),Vector2i(-1,0)]:
					var nx = x + d.x
					var ny = y + d.y
					if nx >= 0 and nx < map_w and ny >= 0 and ny < map_h:
						# Include border SOLID cells (they carry boundary pressure)
						if map[ny][nx] != Tile.SOLID or nx == 0 or nx == map_w - 1:
							s += pressure[ny][nx]
							c += 1
				if c > 0:
					pressure[y][x] = s / c

	# Flow direction from gradient
	for y in range(1, map_h - 1):
		for x in range(1, map_w - 1):
			if map[y][x] == Tile.SOLID:
				continue
			var max_grad = 0.0
			var best_dir = 0
			var dd = [[1,0,1],[-1,0,3],[0,1,2],[0,-1,4]]
			for d in dd:
				var nx = x + d[0]
				var ny = y + d[1]
				if nx >= 0 and nx < map_w and ny >= 0 and ny < map_h and map[ny][nx] != Tile.SOLID:
					var grad = pressure[y][x] - pressure[ny][nx]
					if grad > max_grad:
						max_grad = grad
						best_dir = d[2]
			flow_dir[y][x] = best_dir
			var spd = max_grad * base_speed * 35.0
			if map[y][x] == Tile.FLOW_FAST:
				spd *= 2.5
			flow_spd[y][x] = minf(spd, base_speed * 3.0)

func _compute_distance() -> void:
	var queue: Array = []
	for y in range(map_h):
		for x in range(map_w):
			if map[y][x] == Tile.SOLID:
				dist_map[y][x] = 0
				queue.append(Vector2i(x, y))
			else:
				dist_map[y][x] = 999
	while queue.size() > 0:
		var c: Vector2i = queue.pop_front()
		for d in [Vector2i(0,-1),Vector2i(1,0),Vector2i(0,1),Vector2i(-1,0)]:
			var n = c + d
			if n.x >= 0 and n.x < map_w and n.y >= 0 and n.y < map_h:
				if dist_map[n.y][n.x] > dist_map[c.y][c.x] + 1:
					dist_map[n.y][n.x] = dist_map[c.y][c.x] + 1
					queue.append(n)

func _add_toxic(coverage: float) -> void:
	var num_veins = _rng.randi_range(3, 7)
	for _v in range(num_veins):
		var vx = _rng.randi_range(3, map_w - 4)
		var vy = _rng.randi_range(2, map_h - 3)
		var vlen = _rng.randi_range(6, 18)
		var horiz = _rng.randf() < 0.5
		for step in range(vlen):
			var width = _rng.randi_range(1, 2)
			for dw in range(-width, width + 1):
				var tx = (vx + step) if horiz else (vx + dw)
				var ty = (vy + dw) if horiz else (vy + step)
				if tx > 1 and tx < map_w - 2 and ty > 1 and ty < map_h - 2:
					if map[ty][tx] == Tile.PORE:
						map[ty][tx] = Tile.TOXIC
			if _rng.randf() < 0.4:
				if horiz:
					vy += _rng.randi_range(-1, 1)
				else:
					vx += _rng.randi_range(-1, 1)

# ── QUERIES ──────────────────────────────────────────────────────────────────

func get_tile(x: int, y: int) -> int:
	if x < 0 or x >= map_w or y < 0 or y >= map_h:
		return Tile.SOLID
	return map[y][x]

func set_tile(x: int, y: int, tile: int) -> void:
	if x >= 0 and x < map_w and y >= 0 and y < map_h:
		map[y][x] = tile
		queue_redraw()

func get_flow(x: int, y: int) -> Dictionary:
	if x < 0 or x >= map_w or y < 0 or y >= map_h:
		return {"dir": 0, "speed": 0.0}
	return {"dir": flow_dir[y][x], "speed": flow_spd[y][x]}

func get_distance(x: int, y: int) -> int:
	if x < 0 or x >= map_w or y < 0 or y >= map_h:
		return 0
	return dist_map[y][x]

func is_walkable_tile(tile: int) -> bool:
	return tile == Tile.PORE or tile == Tile.TOXIC or tile == Tile.FLOW_FAST \
		or tile == Tile.INLET or tile == Tile.OUTLET or tile == Tile.BIOFILM

func find_start() -> Vector2i:
	for x in range(map_w):
		for y in range(map_h):
			if map[y][x] == Tile.INLET:
				return Vector2i(x, y)
	for x in range(1, map_w):
		for y in range(1, map_h):
			if is_walkable_tile(map[y][x]):
				return Vector2i(x, y)
	return Vector2i(1, 1)

func find_exit() -> Vector2i:
	for x in range(map_w - 1, -1, -1):
		for y in range(map_h):
			if map[y][x] == Tile.OUTLET:
				return Vector2i(x, y)
	return Vector2i(map_w - 2, map_h / 2)

func get_adjacent_pores(tx: int, ty: int) -> Array:
	var pores: Array = []
	for d in [Vector2i(0,-1),Vector2i(1,0),Vector2i(0,1),Vector2i(-1,0)]:
		var nx = tx + d.x
		var ny = ty + d.y
		if nx >= 0 and nx < map_w and ny >= 0 and ny < map_h:
			var t = map[ny][nx]
			if t == Tile.PORE or t == Tile.FLOW_FAST or t == Tile.INLET:
				pores.append(Vector2i(nx, ny))
	return pores

# ── DRAWING ──────────────────────────────────────────────────────────────────

func _draw() -> void:
	if map.size() == 0:
		return
	var cam_offset = Vector2.ZERO
	var parent_cam = get_viewport().get_camera_2d()
	if parent_cam:
		cam_offset = parent_cam.get_screen_center_position() - Vector2(GameData.VIEW_W, GameData.VIEW_H) * 0.5

	var start_col = maxi(0, int(cam_offset.x / T) - 1)
	var end_col = mini(map_w, start_col + GameData.COLS + 3)
	var start_row = maxi(0, int(cam_offset.y / T) - 1)
	var end_row = mini(map_h, start_row + GameData.ROWS + 3)

	var time = GameData.game_time
	var ep = GameData.get_env_pal()

	for row in range(start_row, end_row):
		for col in range(start_col, end_col):
			var tile = map[row][col]
			var pos = Vector2(col * T, row * T)
			var variation = ((col * 7 + row * 13) & 3)

			match tile:
				Tile.SOLID:
					var key = "grain_%d_%d" % [env_idx, variation % 4]
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
				Tile.PORE:
					var key = "pore_%d_%d" % [env_idx, variation % 4]
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
					# Subtle flow visualization
					if flow_dir[row][col] > 0 and flow_spd[row][col] > 0.08:
						var alpha = clampf(flow_spd[row][col] * 0.25, 0, 0.35)
						alpha += sin(time * 2.0 + col * 0.5) * 0.1
						draw_rect(Rect2(pos, Vector2(T, T)), Color.html(ep["water_l"]).darkened(0.3), true)
				Tile.FLOW_FAST:
					var key = "flow_%d_%d" % [env_idx, variation % 2]
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
					# Animated flow lines
					var off = int(time * 10) % T
					for i in range(3):
						var lx = (off + i * 12) % T
						draw_rect(Rect2(pos + Vector2(lx, 6 + i * 8), Vector2(6, 2)),
							Color.html(ep["water_l"]).lightened(0.2))
				Tile.TOXIC:
					var key = "toxic_%d_%d" % [env_idx, variation % 2]
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
					var glow = sin(time * 3.0 + col * 0.7 + row * 0.5) * 0.15 + 0.2
					draw_rect(Rect2(pos, Vector2(T, T)),
						Color(Color.html(ep["toxic_g"]), glow), true)
				Tile.BIOFILM:
					var key = "biofilm_%d" % env_idx
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
				Tile.INLET:
					var key = "pore_%d_0" % env_idx
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
					var p = sin(time * 4.0) * 0.3 + 0.5
					draw_rect(Rect2(pos, Vector2(8, T)),
						Color(0.24, 0.48, 0.71, p), true)
				Tile.OUTLET:
					var key = "pore_%d_0" % env_idx
					var tex = SpriteFactory.get_tex(key)
					if tex:
						draw_texture(tex, pos)
					var p = sin(time * 2.0) * 0.2 + 0.5
					draw_rect(Rect2(pos + Vector2(24, 0), Vector2(8, T)),
						Color(0.37, 0.81, 0.37, p), true)
