extends Node
## Procedural chiptune audio system using AudioStreamWAV.

var muted := false
var players: Array[AudioStreamPlayer] = []
var music_player: AudioStreamPlayer
const SAMPLE_RATE := 22050

func _ready() -> void:
	# Pre-create audio stream players for SFX
	for i in range(8):
		var p = AudioStreamPlayer.new()
		p.bus = "Master"
		p.volume_db = -6
		add_child(p)
		players.append(p)
	# Music player
	music_player = AudioStreamPlayer.new()
	music_player.bus = "Master"
	music_player.volume_db = -14
	add_child(music_player)

func toggle_mute() -> bool:
	muted = !muted
	AudioServer.set_bus_mute(0, muted)
	return muted

func _get_free_player() -> AudioStreamPlayer:
	for p in players:
		if !p.playing:
			return p
	return players[0]

# ── TONE GENERATION ──────────────────────────────────────────────────────────

func _gen_tone(freq: float, dur: float, vol: float = 0.5, wave: String = "square") -> AudioStreamWAV:
	var num_samples = int(SAMPLE_RATE * dur)
	var audio = AudioStreamWAV.new()
	audio.format = AudioStreamWAV.FORMAT_16_BITS
	audio.mix_rate = SAMPLE_RATE
	audio.stereo = false
	var data = PackedByteArray()
	data.resize(num_samples * 2)
	for i in range(num_samples):
		var t = float(i) / SAMPLE_RATE
		var envelope = minf(1.0, (dur - t) * 8.0) * minf(1.0, t * 200.0)
		var sample_val: float = 0.0
		match wave:
			"square":
				sample_val = 1.0 if fmod(t * freq, 1.0) < 0.5 else -1.0
			"triangle":
				sample_val = abs(fmod(t * freq, 1.0) * 4.0 - 2.0) - 1.0
			"sine":
				sample_val = sin(t * freq * TAU)
			"saw":
				sample_val = fmod(t * freq, 1.0) * 2.0 - 1.0
			"noise":
				sample_val = randf_range(-1.0, 1.0)
		sample_val *= vol * envelope
		var val = clampi(int(sample_val * 32767), -32768, 32767)
		data[i * 2] = val & 0xFF
		data[i * 2 + 1] = (val >> 8) & 0xFF
	audio.data = data
	return audio

func _play_tone(freq: float, dur: float, vol: float = 0.3, wave: String = "square") -> void:
	if muted: return
	var p = _get_free_player()
	p.stream = _gen_tone(freq, dur, vol, wave)
	p.volume_db = -6
	p.play()

func _play_delayed(freq: float, dur: float, delay: float, vol: float = 0.3, wave: String = "square") -> void:
	await get_tree().create_timer(delay).timeout
	_play_tone(freq, dur, vol, wave)

# ── SOUND EFFECTS ────────────────────────────────────────────────────────────

func sfx_eat() -> void:
	_play_tone(523, 0.05)
	_play_delayed(784, 0.06, 0.05)
	_play_delayed(1047, 0.08, 0.10)

func sfx_eat_methane() -> void:
	_play_tone(659, 0.06, 0.4, "triangle")
	_play_delayed(880, 0.06, 0.06, 0.4, "triangle")
	_play_delayed(1175, 0.12, 0.12, 0.4, "triangle")
	_play_delayed(1397, 0.15, 0.18, 0.3, "triangle")

func sfx_divide() -> void:
	for i in range(6):
		_play_delayed(300 + i * 100, 0.1, i * 0.06)
	_play_delayed(1200, 0.25, 0.36, 0.3, "triangle")

func sfx_hurt() -> void:
	_play_tone(200, 0.1, 0.4, "saw")
	_play_delayed(150, 0.12, 0.08, 0.4, "saw")

func sfx_die() -> void:
	for i in range(5):
		_play_delayed(400 - i * 60, 0.15, i * 0.1, 0.3, "saw")

func sfx_level_complete() -> void:
	var notes = [523, 659, 784, 1047, 784, 1047, 1319]
	for i in range(notes.size()):
		_play_delayed(notes[i], 0.12, i * 0.1, 0.3, "square")

func sfx_menu_select() -> void:
	_play_tone(440, 0.04, 0.2)
	_play_delayed(660, 0.06, 0.04, 0.2)

func sfx_menu_confirm() -> void:
	_play_tone(523, 0.06, 0.3, "triangle")
	_play_delayed(784, 0.1, 0.06, 0.3, "triangle")

func sfx_science() -> void:
	_play_tone(330, 0.08, 0.2, "sine")
	_play_delayed(440, 0.08, 0.08, 0.2, "sine")
	_play_delayed(554, 0.12, 0.16, 0.2, "sine")

func sfx_flow_ride() -> void:
	_play_tone(260, 0.15, 0.1, "sine")

func sfx_colony_place() -> void:
	_play_tone(392, 0.06, 0.25, "triangle")
	_play_delayed(523, 0.06, 0.06, 0.25, "triangle")
	_play_delayed(659, 0.12, 0.12, 0.25, "triangle")

# ── MUSIC ────────────────────────────────────────────────────────────────────

var _music_playing := false
var _music_timer: Timer = null

func stop_music() -> void:
	_music_playing = false
	if _music_timer and _music_timer.is_inside_tree():
		_music_timer.stop()
	if music_player:
		music_player.stop()

func play_env_music(env_idx: int) -> void:
	stop_music()
	_music_playing = true
	# Generate a simple looping melody
	var patterns = [
		# Soil: upbeat, curious
		[262,330,392,330,262,392,523,392,349,440,523,440,349,262,330,262],
		# Deep: slow, tense
		[220,0,262,247,220,0,196,220,262,0,294,262,247,220,196,220],
		# Seeps: ominous
		[196,0,233,196,175,0,196,0,233,262,233,196,175,165,175,196],
		# Permafrost: urgent
		[392,523,659,523,392,330,392,0,440,523,659,784,659,523,440,392],
		# Hydrothermal: epic
		[330,392,440,523,440,392,330,262,330,392,523,659,523,440,392,330],
	]
	var bpms = [140.0, 90.0, 120.0, 160.0, 130.0]
	var pat = patterns[env_idx % patterns.size()]
	var bpm = bpms[env_idx % bpms.size()]
	var beat_dur = 60.0 / bpm * 0.5

	# Combine notes into one WAV for looping
	var total_samples = 0
	var all_data = PackedByteArray()
	for note in pat:
		var dur = beat_dur * 0.9
		var n_samp = int(SAMPLE_RATE * dur)
		for s in range(n_samp):
			var t = float(s) / SAMPLE_RATE
			var env = minf(1.0, (dur - t) * 6.0) * minf(1.0, t * 100.0)
			var val_f = 0.0
			if note > 0:
				val_f = (1.0 if fmod(t * note, 1.0) < 0.5 else -1.0) * 0.12 * env
				# Add triangle bass
				val_f += (abs(fmod(t * note * 0.5, 1.0) * 4.0 - 2.0) - 1.0) * 0.06 * env
			var val = clampi(int(val_f * 32767), -32768, 32767)
			all_data.append(val & 0xFF)
			all_data.append((val >> 8) & 0xFF)
		# Small gap between notes
		var gap = int(SAMPLE_RATE * beat_dur * 0.1)
		for _g in range(gap):
			all_data.append(0)
			all_data.append(0)

	var stream = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = SAMPLE_RATE
	stream.stereo = false
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = 0
	stream.loop_end = all_data.size() / 2
	stream.data = all_data

	music_player.stream = stream
	music_player.play()

func play_title_music() -> void:
	play_env_music(0)
