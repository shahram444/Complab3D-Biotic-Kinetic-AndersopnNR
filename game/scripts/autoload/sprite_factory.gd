extends Node
## Generates all pixel art sprites programmatically at startup.
## No external image files needed - authentic 8-bit style.

# Palette mapping: single character -> hex color
const PAL := {
	".": "",              # transparent
	"k": "#000000",       # black (outline)
	"w": "#ffffff",       # white
	"W": "#cccccc",       # light gray
	"a": "#888888",       # gray
	"A": "#444444",       # dark gray
	# Methi (teal archaea)
	"t": "#1a8a7a",       # body teal
	"T": "#2acfaf",       # highlight teal
	"L": "#5fffdf",       # bright glow
	"d": "#0a5a4a",       # dark teal
	"D": "#084038",       # darker teal
	# Brown (grains)
	"b": "#7a5a2a",       # brown
	"B": "#a48a5a",       # light brown
	"n": "#4a3a1a",       # dark brown
	"N": "#c4a060",       # tan
	# Blue (water)
	"u": "#1a3a60",       # blue
	"U": "#3060a0",       # light blue
	"c": "#50b0c0",       # cyan
	"C": "#80d0e0",       # light cyan
	# Substrates
	"o": "#ef8f3f",       # orange (Fe)
	"O": "#ffbf7f",       # light orange
	"y": "#dfdf3f",       # yellow (SO4)
	"Y": "#ffffaf",       # light yellow
	"r": "#ff4f4f",       # red (CH4)
	"R": "#ff9f7f",       # light red
	"g": "#4fdf6f",       # green (NO3)
	"G": "#8fff9f",       # light green
	"p": "#cf6fff",       # purple (Mn)
	"P": "#df9fff",       # light purple
	"i": "#4fa4ff",       # info blue (O2)
	"I": "#8fc8ff",       # light info blue
	# Visor / Helmet
	"V": "#40c8d8",       # visor cyan
	"H": "#7888a0",       # helmet rim gray
	"X": "#90e8f0",       # visor shine (bright cyan)
	# Eyes
	"e": "#1a1a2e",       # pupil
	# Special
	"s": "#ffff5f",       # glow/ready
	"h": "#ff6644",       # hurt
	"m": "#0a6a5a",       # mouth
	"f": "#3a7a5a",       # biofilm
	"F": "#5aaa7a",       # biofilm light
	"v": "#2a5a4a",       # biofilm dark
}

# ── SPRITE DATA ──────────────────────────────────────────────────────────────

# METHI: 16x16 explorer microbe with visor/helmet
# Little round archaea wearing a translucent sci-fi visor
# 'V' = visor cyan, 'H' = helmet rim gray, 'X' = visor shine
const METHI_DOWN := [
	"....kHHHHHk.....",
	"...kHHHHHHHk....",
	"..kHVVVVVVVHk...",
	"..kVXXVVVXXVk...",
	"..kVXwwVwwXVk...",
	"..kVVwekweVVk...",
	"..kHVVVVVVVHk...",
	"..kkHHkkkHHkk...",
	"..kTTTTTTTTTk...",
	"..kTTTTTTTTTk...",
	"..kTtTTTTTtTk...",
	"...ktTTTTTtk....",
	"....ktttttkk....",
	".....kkkkk......",
	"......k.k.......",
	"................",
]

const METHI_UP := [
	"....kHHHHHk.....",
	"...kHHHHHHHk....",
	"..kHHHHHHHHHk...",
	"..kHHHHHHHHHk...",
	"..kHHHHHHHHHk...",
	"..kHHHHHHHHHk...",
	"..kHHHHHHHHHk...",
	"..kkHHkkkHHkk...",
	"..kTTTTTTTTTk...",
	"..kTTTTTTTTTk...",
	"..kTtTTTTTtTk...",
	"...ktTTTTTtk....",
	"....ktttttkk....",
	".....kkkkk......",
	"................",
	"................",
]

const METHI_LEFT := [
	"................",
	"...kHHHHHk......",
	"..kHVVVVVHk.....",
	"..kVXXVVVVk.....",
	".kkVXweVVVk.....",
	".kHVVVVVVHk.....",
	".kkHHkkHHkk.....",
	".kTTTTTTTTk.....",
	"..kTTTTTTTk.....",
	"..kTtTTTtTk.....",
	"...ktTTTtk......",
	"....kttttk......",
	".....kkkk.......",
	"......k.........",
	"................",
	"................",
]

const METHI_RIGHT := [
	"................",
	"......kHHHHHk...",
	".....kHVVVVVHk..",
	".....kVVVVXXVk..",
	".....kVVVewXVkk.",
	".....kHVVVVVHk..",
	".....kkHHkkHHkk.",
	".....kTTTTTTTk..",
	".....kTTTTTTk...",
	".....kTtTTtTk...",
	"......ktTTtk....",
	"......kttttk....",
	".......kkkk.....",
	".........k......",
	"................",
	"................",
]

const METHI_EAT := [
	"....kHHHHHk.....",
	"...kHHHHHHHk....",
	"..kHVVVVVVVHk...",
	"..kVXXVVVXXVk...",
	"..kVXwwVwwXVk...",
	"..kVVwekweVVk...",
	"..kHVVkkkVVHk...",
	"..kkHkssskHkk...",
	"..kTTTkkkTTTk...",
	"..kTTTTTTTTTk...",
	"..kTtTTTTTtTk...",
	"...ktTTTTTtk....",
	"....ktttttkk....",
	".....kkkkk......",
	"................",
	"................",
]

const METHI_GLOW := [
	"...skHHHHHks....",
	"..skHHHHHHHks...",
	".skHVVVVVVVHks..",
	".skVXXVVVXXVks..",
	".skVXwwVwwXVks..",
	".skVVwekweVVks..",
	".skHVVVVVVVHks..",
	".skkHHkkkHHkks..",
	".skLTTTTTTTLks..",
	".skLTTTTTTTLks..",
	"..skLtTTTtLks...",
	"...skLTTTLks....",
	"....skkkkks.....",
	".....ssssss.....",
	"................",
	"................",
]

const METHI_HURT := [
	"....kHHHHHk.....",
	"...kHHHHHHHk....",
	"..kHhhhhhhhHk...",
	"..khhkkkhkkhk...",
	"..khhhhhhhhhk...",
	"..khhhhhhhhhk...",
	"..kHhhhhhhhHk...",
	"..kkHHkkkHHkk...",
	"..khhhhhhhhhk...",
	"..khhhhhhhhhk...",
	"..khhhhhhhhhk...",
	"...khhhhhhhhk...",
	"....khhhhhhk....",
	".....kkkkkk.....",
	"................",
	"................",
]

const METHI_DIE := [
	"................",
	"................",
	".....kkkkkk.....",
	"....kaHHHHak....",
	"...kaHaaaHaak...",
	"...kaaaaaaaaak..",
	"..kaaaaaaaaaaak.",
	"..kaaaaaaaaaaak.",
	"...kaaaaaaaak...",
	"....kaaaaaak....",
	".....kaaaak.....",
	"......kkkk......",
	"................",
	"................",
	"................",
	"................",
]

# Substrate sprites 10x10
const SUB_O2 := [
	"..kkkkkk..",
	".kiiiiiik.",
	"kiIIIIIIik",
	"kiIIIIIIik",
	"kiIIIIIIik",
	"kiIIIIIIik",
	"kiIIIIIIik",
	"kiiiiiiiik",
	".kiiiiik..",
	"..kkkkkk..",
]

const SUB_NO3 := [
	"....kk....",
	"...kGGk...",
	"..kGGGGk..",
	".kGGGGGGk.",
	"kGGGGGGGGk",
	"kGGGGGGGGk",
	".kGGGGGGk.",
	"..kGGGGk..",
	"...kGGk...",
	"....kk....",
]

const SUB_MN4 := [
	"....kk....",
	"...kPPk...",
	"..kPPPPk..",
	"kkPPPPPPkk",
	"kPPPPPPPPk",
	"kPPPPPPPPk",
	"kkPPPPPPkk",
	"..kPPPPk..",
	"...kPPk...",
	"....kk....",
]

const SUB_FE3 := [
	"....kk....",
	"...kook...",
	"..koOOok..",
	".koOOOOok.",
	"koOOOOOOok",
	"koOOOOOOok",
	".koOOOOok.",
	"..koOOok..",
	"...kook...",
	"....kk....",
]

const SUB_SO4 := [
	"...kkkk...",
	"..kYYYYk..",
	".kYYYYYYk.",
	"kYYYYYYYYk",
	"kYYYYYYYYk",
	"kYYYYYYYYk",
	"kYYYYYYYYk",
	".kYYYYYYk.",
	"..kYYYYk..",
	"...kkkk...",
]

const SUB_CH4 := [
	"....kk....",
	"...kRRk...",
	"..kRrrRk..",
	".kRrrrrRk.",
	".kRrrrRRk.",
	"kRRrrRRRRk",
	"kRRRRRRRRk",
	".kRRRRRRk.",
	"..kRRRRk..",
	"...kkkk...",
]

# Colony cell 12x12
const COLONY := [
	"...kkkkkk...",
	"..kfFFFFFk..",
	".kfFFFFFFfk.",
	"kfFFFFFFFFFk",
	"kFFFFFFFFFFk",
	"kFFFFFFFFFFk",
	"kFFFFFFFFFFk",
	"kfFFFFFFFfFk",
	".kfFFFFFFfk.",
	"..kvFFFfvk..",
	"...kkkkkk...",
	"............",
]

# Flow arrow 8x8
const ARROW_R := [
	"........",
	"...k....",
	"...kU...",
	"..kUUU..",
	"..kUUU..",
	"...kU...",
	"...k....",
	"........",
]

const ARROW_D := [
	"........",
	"..kkkk..",
	"...UU...",
	"..UUUU..",
	"...UU...",
	"...kk...",
	"........",
	"........",
]

# ── TEXTURE CACHE ────────────────────────────────────────────────────────────
var textures := {}

func _ready() -> void:
	_generate_all()

func _generate_all() -> void:
	# Player sprites
	textures["methi_down"] = _make_tex(METHI_DOWN)
	textures["methi_up"] = _make_tex(METHI_UP)
	textures["methi_left"] = _make_tex(METHI_LEFT)
	textures["methi_right"] = _make_tex(METHI_RIGHT)
	textures["methi_eat"] = _make_tex(METHI_EAT)
	textures["methi_glow"] = _make_tex(METHI_GLOW)
	textures["methi_hurt"] = _make_tex(METHI_HURT)
	textures["methi_die"] = _make_tex(METHI_DIE)

	# Substrates
	textures["sub_o2"] = _make_tex(SUB_O2)
	textures["sub_no3"] = _make_tex(SUB_NO3)
	textures["sub_mn4"] = _make_tex(SUB_MN4)
	textures["sub_fe3"] = _make_tex(SUB_FE3)
	textures["sub_so4"] = _make_tex(SUB_SO4)
	textures["sub_ch4"] = _make_tex(SUB_CH4)

	# Colony
	textures["colony"] = _make_tex(COLONY)

	# Arrows
	textures["arrow_r"] = _make_tex(ARROW_R)
	textures["arrow_d"] = _make_tex(ARROW_D)

	# Generate tile textures for each environment
	for env_idx in range(GameData.ENV_PAL.size()):
		_generate_env_tiles(env_idx)

func _make_tex(data: Array, override_pal: Dictionary = {}) -> ImageTexture:
	var h = data.size()
	var w = data[0].length() if h > 0 else 0
	var img = Image.create(w, h, false, Image.FORMAT_RGBA8)

	var pal_to_use = PAL.duplicate()
	for key in override_pal:
		pal_to_use[key] = override_pal[key]

	for y in range(h):
		var row: String = data[y]
		for x in range(mini(w, row.length())):
			var ch = row[x]
			var hex = pal_to_use.get(ch, "")
			if hex != "" and hex != null:
				img.set_pixel(x, y, Color.html(hex))
			else:
				img.set_pixel(x, y, Color(0, 0, 0, 0))

	var tex = ImageTexture.create_from_image(img)
	return tex

func _generate_env_tiles(env_idx: int) -> void:
	var ep = GameData.ENV_PAL[env_idx]

	# Grain tile (16x16 with noise)
	for v in range(4):
		var img = Image.create(16, 16, false, Image.FORMAT_RGBA8)
		var rng = RandomNumberGenerator.new()
		rng.seed = env_idx * 1000 + v * 100
		for y in range(16):
			for x in range(16):
				var r = rng.randf()
				var col: String
				if r < 0.45:
					col = ep["grain"]
				elif r < 0.70:
					col = ep["grain_l"]
				elif r < 0.88:
					col = ep["grain_d"]
				else:
					col = ep["grain_a"]
				img.set_pixel(x, y, Color.html(col))
		textures["grain_%d_%d" % [env_idx, v]] = ImageTexture.create_from_image(img)

	# Pore tile (16x16)
	for v in range(4):
		var img = Image.create(16, 16, false, Image.FORMAT_RGBA8)
		var rng = RandomNumberGenerator.new()
		rng.seed = env_idx * 1000 + v * 100 + 50
		for y in range(16):
			for x in range(16):
				var r = rng.randf()
				var col: String
				if r < 0.65:
					col = ep["pore"]
				elif r < 0.85:
					col = ep["pore_l"]
				else:
					col = ep["water"]
				img.set_pixel(x, y, Color.html(col))
		textures["pore_%d_%d" % [env_idx, v]] = ImageTexture.create_from_image(img)

	# Fast flow tile
	for v in range(2):
		var img = Image.create(16, 16, false, Image.FORMAT_RGBA8)
		var rng = RandomNumberGenerator.new()
		rng.seed = env_idx * 1000 + v * 100 + 80
		for y in range(16):
			for x in range(16):
				var r = rng.randf()
				var col: String
				if r < 0.35:
					col = ep["water"]
				elif r < 0.65:
					col = ep["water_l"]
				elif r < 0.85:
					col = ep["pore_l"]
				else:
					col = ep["pore"]
				img.set_pixel(x, y, Color.html(col))
		textures["flow_%d_%d" % [env_idx, v]] = ImageTexture.create_from_image(img)

	# Toxic tile
	for v in range(2):
		var img = Image.create(16, 16, false, Image.FORMAT_RGBA8)
		var rng = RandomNumberGenerator.new()
		rng.seed = env_idx * 1000 + v * 100 + 90
		for y in range(16):
			for x in range(16):
				var r = rng.randf()
				var col: String
				if r < 0.4:
					col = ep["toxic"]
				elif r < 0.7:
					col = ep["toxic_g"]
				elif r < 0.85:
					col = ep["pore"]
				else:
					col = "#1a0a1a"
				img.set_pixel(x, y, Color.html(col))
		textures["toxic_%d_%d" % [env_idx, v]] = ImageTexture.create_from_image(img)

	# Biofilm tile
	var img = Image.create(16, 16, false, Image.FORMAT_RGBA8)
	var rng = RandomNumberGenerator.new()
	rng.seed = env_idx * 1000 + 200
	for y in range(16):
		for x in range(16):
			var r = rng.randf()
			var col: String
			if r < 0.45:
				col = "#2a5a4a"
			elif r < 0.75:
				col = "#3a7a5a"
			else:
				col = "#1a4a3a"
			img.set_pixel(x, y, Color.html(col))
	textures["biofilm_%d" % env_idx] = ImageTexture.create_from_image(img)

func get_tex(key: String) -> ImageTexture:
	return textures.get(key, null)

func get_sub_tex(sub_type: int) -> ImageTexture:
	match sub_type:
		GameData.Sub.O2: return textures.get("sub_o2")
		GameData.Sub.NO3: return textures.get("sub_no3")
		GameData.Sub.MN4: return textures.get("sub_mn4")
		GameData.Sub.FE3: return textures.get("sub_fe3")
		GameData.Sub.SO4: return textures.get("sub_so4")
		GameData.Sub.CH4: return textures.get("sub_ch4")
	return textures.get("sub_ch4")

func get_sub_key(sub_type: int) -> String:
	match sub_type:
		GameData.Sub.O2: return "sub_o2"
		GameData.Sub.NO3: return "sub_no3"
		GameData.Sub.MN4: return "sub_mn4"
		GameData.Sub.FE3: return "sub_fe3"
		GameData.Sub.SO4: return "sub_so4"
		GameData.Sub.CH4: return "sub_ch4"
	return "sub_ch4"
