extends Node2D
## Colony cell entity - placed when METHI divides.

var age: float = 0.0
var pulse_timer: float = 0.0

func _ready() -> void:
	pulse_timer = randf() * TAU

func _process(delta: float) -> void:
	age += delta
	pulse_timer += delta
	queue_redraw()

func _draw() -> void:
	var tex = SpriteFactory.get_tex("colony")
	if tex:
		draw_texture(tex, Vector2(4, 4))

	# Pulse glow
	var pulse = sin(pulse_timer * 2.0) * 0.12 + 0.12
	draw_rect(Rect2(Vector2(4, 4), Vector2(24, 24)), Color(0.37, 0.81, 0.37, pulse))

	# Birth glow
	if age < 1.0:
		var glow = (1.0 - age) * 0.4
		draw_rect(Rect2(Vector2(-2, -2), Vector2(36, 36)), Color(0.37, 0.81, 0.37, glow))
