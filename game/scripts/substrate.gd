extends Node2D
## Individual substrate particle entity with animation.

var sub_type: int = GameData.Sub.CH4
var lifetime: float = 18.0
var anim_timer: float = 0.0

func _ready() -> void:
	anim_timer = randf() * 10.0

func _process(delta: float) -> void:
	anim_timer += delta
	queue_redraw()

func _draw() -> void:
	var sub_data = GameData.SUBSTRATES.get(sub_type, {})
	var glow_color = Color.html(sub_data.get("glow", "#ffffff"))
	var time = anim_timer
	var bob = sin(time * 2.5) * 2.0

	# Glow behind
	var glow_size = 12.0 + sin(time * 3.0) * 2.0
	var glow_offset = (10.0 - glow_size) * 0.5
	draw_rect(Rect2(Vector2(glow_offset - 1, glow_offset - 1 + bob), Vector2(glow_size, glow_size)),
		Color(glow_color, 0.15))

	# Sprite
	var tex = SpriteFactory.get_sub_tex(sub_type)
	if tex:
		var alpha = 1.0 if lifetime > 3.0 else lifetime / 3.0
		draw_texture(tex, Vector2(0, bob), Color(1, 1, 1, alpha))

	# Energy value indicator (small text)
	var energy = sub_data.get("energy", 0)
	if energy > 0:
		var font = ThemeDB.fallback_font
		if font:
			draw_string(font, Vector2(10, -2 + bob), "+%d" % energy,
				HORIZONTAL_ALIGNMENT_LEFT, -1, 5, Color(glow_color, 0.6))
