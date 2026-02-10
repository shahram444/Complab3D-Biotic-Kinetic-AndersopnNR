# How to Make a Game Like ARKE in Godot 4

A simple recipe. Follow step by step.

---

## Step 0: What You Need

- **Godot 4.2+** (free, download from godotengine.org)
- No art skills needed (we make all sprites with code)
- No plugins needed
- Total files: ~10 scripts, 1 scene

---

## Step 1: Create the Project

1. Open Godot → New Project → name it anything
2. Set display: `960 x 540`, stretch mode `canvas_items`
3. Create folders:
```
game/
  scenes/
  scripts/
    autoload/
```

---

## Step 2: Set Up Global Autoloads (The Brain)

Autoloads are scripts that load FIRST and are available everywhere.
Create 3 files in `scripts/autoload/`:

### game_data.gd - All Your Constants
```gdscript
extends Node

# Tile size in pixels
const TILE = 32
const VIEW_W = 960
const VIEW_H = 540

# Game states - like chapters of your game
enum State { TITLE, PLAYING, PAUSED, GAME_OVER, VICTORY }

# Tile types for your world grid
enum Tile { VOID, SOLID, PORE, BIOFILM, TOXIC }

# Level definitions - data-driven design!
var LEVELS = [
    { "name": "Level 1", "map_w": 30, "map_h": 17, "porosity": 0.6 },
    { "name": "Level 2", "map_w": 40, "map_h": 20, "porosity": 0.5 },
]
```

### sprite_factory.gd - Draw All Art With Code
```gdscript
extends Node

var textures = {}

func _ready():
    _generate_all()

func _generate_all():
    # Define your character as a grid of colored pixels
    var player_pixels = [
        "..GGGG..",
        ".GCCCGG.",
        "GCCBBCG.",   # B = blue visor
        "GCCCCCG.",
        ".GGGGGG.",
        "..GGGG..",
    ]
    textures["player"] = _make_tex(player_pixels)

# Turn pixel strings into a texture
func _make_tex(data: Array) -> ImageTexture:
    var h = data.size()
    var w = data[0].length()
    var img = Image.create(w, h, false, Image.FORMAT_RGBA8)
    for y in h:
        for x in w:
            var c = data[y][x]
            var color = _char_to_color(c)
            img.set_pixel(x, y, color)
    img.resize(w * 2, h * 2, Image.INTERPOLATE_NEAREST)  # 2x scale
    return ImageTexture.create_from_image(img)

func _char_to_color(c: String) -> Color:
    match c:
        "G": return Color(0.2, 0.7, 0.3)   # green
        "B": return Color(0.3, 0.6, 1.0)   # blue
        "C": return Color(0.1, 0.5, 0.4)   # cyan/teal
        "R": return Color(0.8, 0.2, 0.2)   # red
        _:   return Color(0, 0, 0, 0)       # transparent
```

### audio_manager.gd - Sound Effects
```gdscript
extends Node

var muted = false

func play_sfx(freq: float, duration: float = 0.1):
    if muted: return
    # Use AudioStreamGenerator for retro bleeps
    # Or just skip audio at first - add it later!
    pass
```

**Register them:** Project → Settings → Autoload → add all 3.

---

## Step 3: Build the World (Grid Map)

`scripts/world.gd` - Your world is just a 2D array of numbers.

```gdscript
extends Node2D

var map = []      # 2D array of tile types
var map_w = 30
var map_h = 17

func generate():
    # Start with all pores (open space)
    map = []
    for y in map_h:
        var row = []
        for x in map_w:
            row.append(GameData.Tile.PORE)
        map.append(row)

    # Drop random circles of SOLID (grains/walls)
    for i in range(20):
        var cx = randi_range(3, map_w - 3)
        var cy = randi_range(3, map_h - 3)
        var r = randi_range(1, 3)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx*dx + dy*dy <= r*r:
                    var nx = cx + dx
                    var ny = cy + dy
                    if nx > 0 and nx < map_w-1 and ny > 0 and ny < map_h-1:
                        map[ny][nx] = GameData.Tile.SOLID

func get_tile(x, y):
    if x < 0 or x >= map_w or y < 0 or y >= map_h:
        return GameData.Tile.VOID
    return map[y][x]

func is_walkable(x, y):
    var t = get_tile(x, y)
    return t == GameData.Tile.PORE or t == GameData.Tile.BIOFILM

# Draw the world tile by tile
func _draw():
    for y in map_h:
        for x in map_w:
            var pos = Vector2(x * GameData.TILE, y * GameData.TILE)
            var tile = map[y][x]
            if tile == GameData.Tile.SOLID:
                draw_rect(Rect2(pos, Vector2(32, 32)), Color(0.4, 0.3, 0.2))
            else:
                draw_rect(Rect2(pos, Vector2(32, 32)), Color(0.1, 0.15, 0.25))

func _process(_delta):
    queue_redraw()  # IMPORTANT: tells Godot to call _draw() every frame
```

**Key lesson:** The world is just numbers in a grid. SOLID=wall, PORE=walkable. Draw each number as a colored square. That's it.

---

## Step 4: Add the Player

`scripts/player.gd` - Grid-based movement, smooth animation.

```gdscript
extends Node2D

var tile_x = 5
var tile_y = 5
var target_pos = Vector2.ZERO
var health = 100.0
var moving = false
var move_cooldown = 0.0
const MOVE_SPEED = 2.5  # tiles per second

func init(start_x, start_y):
    tile_x = start_x
    tile_y = start_y
    position = Vector2(tile_x * GameData.TILE, tile_y * GameData.TILE)
    target_pos = position

func _process(delta):
    # Smooth movement toward target
    position = position.lerp(target_pos, delta * 8.0)

    # Movement cooldown
    move_cooldown -= delta
    if move_cooldown > 0: return

    # Read input
    var dx = 0
    var dy = 0
    if Input.is_action_pressed("ui_right"): dx = 1
    elif Input.is_action_pressed("ui_left"): dx = -1
    elif Input.is_action_pressed("ui_down"): dy = 1
    elif Input.is_action_pressed("ui_up"): dy = -1

    if dx != 0 or dy != 0:
        _try_move(dx, dy)

func _try_move(dx, dy):
    var world = get_parent().get_parent()  # adjust based on your tree
    var nx = tile_x + dx
    var ny = tile_y + dy
    if world.is_walkable(nx, ny):
        tile_x = nx
        tile_y = ny
        target_pos = Vector2(tile_x * GameData.TILE, tile_y * GameData.TILE)
        move_cooldown = 1.0 / MOVE_SPEED

func _draw():
    var tex = SpriteFactory.textures.get("player")
    if tex:
        draw_texture(tex, Vector2(-tex.get_width()/2, -tex.get_height()/2))
    else:
        draw_circle(Vector2(16, 16), 10, Color.GREEN)
    queue_redraw()
```

**Key lesson:** Player lives on a grid (tile_x, tile_y) but position smoothly slides toward the target. This feels good to play.

---

## Step 5: Add Collectibles (Substrates/Food)

`scripts/substrate.gd` - Things to pick up.

```gdscript
extends Node2D

var tile_x = 0
var tile_y = 0
var sub_type = "food"
var energy = 10
var lifetime = 18.0

func init(x, y, type, nrg):
    tile_x = x
    tile_y = y
    sub_type = type
    energy = nrg
    position = Vector2(x * GameData.TILE + 16, y * GameData.TILE + 16)

func _process(delta):
    lifetime -= delta

func _draw():
    # Glowing orb
    draw_circle(Vector2.ZERO, 8, Color(1, 0.3, 0.3, 0.6))  # glow
    draw_circle(Vector2.ZERO, 5, Color(1, 0.5, 0.5))        # core
    queue_redraw()
```

Spawn them in main.gd on a timer. Check collision with player by comparing tile positions.

---

## Step 6: Wire It All Together (Main Scene)

`scripts/main.gd` - The conductor of the orchestra.

```gdscript
extends Node2D

var state = GameData.State.TITLE
var world_node: Node2D
var player_node: Node2D
var entity_layer: Node2D
var substrates = []
var spawn_timer = 0.0

func _ready():
    # Build the scene tree with code (no editor needed!)
    world_node = Node2D.new()
    world_node.set_script(load("res://scripts/world.gd"))
    add_child(world_node)

    entity_layer = Node2D.new()
    add_child(entity_layer)

    player_node = Node2D.new()
    player_node.set_script(load("res://scripts/player.gd"))
    entity_layer.add_child(player_node)

    # Add camera
    var cam = Camera2D.new()
    cam.enabled = true
    player_node.add_child(cam)

    # Generate world and place player
    world_node.generate()
    player_node.init(3, 8)
    state = GameData.State.PLAYING

func _process(delta):
    match state:
        GameData.State.TITLE:
            pass  # draw title screen
        GameData.State.PLAYING:
            _update_playing(delta)
        GameData.State.GAME_OVER:
            pass  # draw game over

func _update_playing(delta):
    # Spawn food every 1.2 seconds
    spawn_timer -= delta
    if spawn_timer <= 0:
        spawn_timer = 1.2
        _spawn_substrate()

    # Check collisions (simple tile matching)
    for sub in substrates:
        if sub.tile_x == player_node.tile_x and sub.tile_y == player_node.tile_y:
            player_node.health = min(100, player_node.health + 20)
            sub.queue_free()
            substrates.erase(sub)
            break

    # Remove expired substrates
    for sub in substrates:
        if sub.lifetime <= 0:
            sub.queue_free()
            substrates.erase(sub)

func _spawn_substrate():
    var sub = Node2D.new()
    sub.set_script(load("res://scripts/substrate.gd"))
    # Find random walkable tile
    var x = randi_range(1, world_node.map_w - 2)
    var y = randi_range(1, world_node.map_h - 2)
    if world_node.is_walkable(x, y):
        sub.init(x, y, "food", 10)
        entity_layer.add_child(sub)
        substrates.append(sub)
```

---

## Step 7: Add a HUD (Heads-Up Display)

`scripts/hud.gd` - Draw UI on top of everything.

```gdscript
extends Node2D

var game_ref  # set this to main.gd

func _draw():
    if not game_ref: return

    # Health bar background
    draw_rect(Rect2(10, 10, 104, 14), Color(0.2, 0.2, 0.2))
    # Health bar fill
    var hp = game_ref.player_node.health
    var color = Color.GREEN if hp > 50 else Color.YELLOW if hp > 25 else Color.RED
    draw_rect(Rect2(12, 12, hp, 10), color)

    # Label
    draw_string(ThemeDB.fallback_font, Vector2(12, 38), "HP", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)

func _process(_d):
    queue_redraw()
```

Put HUD on a **CanvasLayer** so it stays on screen when camera moves:
```gdscript
# In main.gd _ready():
var ui_layer = CanvasLayer.new()
ui_layer.layer = 10
add_child(ui_layer)
var hud = Node2D.new()
hud.set_script(load("res://scripts/hud.gd"))
hud.game_ref = self
ui_layer.add_child(hud)
```

---

## Step 8: Add Enemy AI

`scripts/rival.gd` - Simple but effective.

```gdscript
extends Node2D

var tile_x = 0
var tile_y = 0
var target_pos = Vector2.ZERO
var move_timer = 0.0

func init(x, y):
    tile_x = x
    tile_y = y
    position = Vector2(x * GameData.TILE, y * GameData.TILE)
    target_pos = position

func do_move(food_list, player_pos):
    # Simple AI: 60% chance seek nearest food, 40% wander
    if randf() < 0.6 and food_list.size() > 0:
        # Find nearest food
        var best = null
        var best_dist = 999
        for f in food_list:
            var d = abs(f.tile_x - tile_x) + abs(f.tile_y - tile_y)
            if d < best_dist:
                best_dist = d
                best = f
        if best:
            # Step toward it
            var dx = sign(best.tile_x - tile_x)
            var dy = sign(best.tile_y - tile_y)
            _try_step(dx, dy)
            return
    # Wander randomly
    var dirs = [[1,0],[-1,0],[0,1],[0,-1]]
    dirs.shuffle()
    _try_step(dirs[0][0], dirs[0][1])

func _try_step(dx, dy):
    # Check walkable via world reference...
    tile_x += dx
    tile_y += dy
    target_pos = Vector2(tile_x * GameData.TILE, tile_y * GameData.TILE)

func _process(delta):
    position = position.lerp(target_pos, delta * 8.0)

func _draw():
    draw_circle(Vector2(16, 16), 10, Color.RED)
    queue_redraw()
```

---

## Step 9: Add a State Machine for Menus

Your `state` variable controls everything:

```
TITLE  →  press ENTER  →  PLAYING
PLAYING  →  health <= 0  →  GAME_OVER
PLAYING  →  press ESC  →  PAUSED
PAUSED  →  press ESC  →  PLAYING
PLAYING  →  goal reached  →  VICTORY
GAME_OVER  →  press ENTER  →  TITLE
```

In main.gd `_process`, use `match state:` to run the right code for each state.
In hud.gd `_draw`, use `match game_ref.state:` to draw the right screen.

---

## Step 10: Polish (What Makes It Feel Good)

These small touches make a HUGE difference:

| Polish | How | Why |
|--------|-----|-----|
| **Smooth movement** | `position.lerp(target, delta * 8.0)` | Grid movement that looks smooth |
| **Bobbing** | `sin(time * 4.0) * 2.0` on Y position | Characters feel alive |
| **Screen shake** | Offset camera by random amount, decay fast | Impact on events |
| **Glow circles** | `draw_circle()` with low alpha before sprite | Items look magical |
| **Flash on pickup** | Tint screen for 0.1 sec | Satisfying feedback |
| **Pulsing bars** | `sin(time)` on bar alpha when critical | Creates urgency |
| **Floating text** | "+20 HP" text that rises and fades | Shows what happened |

---

## The Recipe Summary

```
1. Autoloads     → Global data, sprite factory, audio
2. World         → 2D grid array + procedural generation + _draw()
3. Player        → Grid position + smooth lerp + input
4. Collectibles  → Spawn on timer + tile collision
5. Main          → State machine + entity management + camera
6. HUD           → CanvasLayer + draw bars/text over everything
7. Rivals        → Simple AI (seek food / wander)
8. Polish        → Lerp, sin(), glow, shake, flash
```

**Total: ~10 scripts, 1 scene file, 0 imported images.**

---

## Pro Tips

1. **No scene editor needed** - Build your tree with `Node2D.new()` and `add_child()` in code
2. **No art files needed** - Define sprites as character grids, convert to textures at startup
3. **Grid = simple collision** - If two things are on the same tile, they collide. No physics engine needed
4. **Data-driven levels** - Store level configs in dictionaries, loop through them
5. **`queue_redraw()` is essential** - Without it in `_process()`, your `_draw()` only runs once
6. **Start ugly, make it work, then make it pretty** - Get movement + collision working first
7. **Playtest constantly** - Run the game every 5 minutes while building

---

## File Checklist

```
scripts/
  autoload/
    game_data.gd        ← constants, enums, level data
    sprite_factory.gd   ← pixel art generated with code
    audio_manager.gd    ← sound effects
  main.gd               ← game loop, state machine, spawning
  world.gd              ← grid generation, flow, drawing tiles
  player.gd             ← movement, eating, health
  rival.gd              ← enemy AI
  substrate.gd          ← collectible food items
  colony_cell.gd        ← placed buildings/colonies
  hud.gd                ← all UI: bars, menus, screens
scenes/
  main.tscn             ← just one root Node2D with main.gd
project.godot           ← registers autoloads
```

That's it. Start with Steps 1-6 to get something playable in an afternoon, then add enemies and polish. Good luck!
