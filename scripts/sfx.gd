extends Node
## Sound effects (autoload "Sfx"). Sfx.play("pickup") for UI-style sounds,
## Sfx.play_at("growl", position) for sounds that come from a place in the world.

const SOUNDS := ["step", "rumble", "growl", "pickup", "caught", "lights_off", "lights_on",
		"tick", "gate", "heartbeat", "level_clear"]

var _streams := {}
var _players: Array[AudioStreamPlayer] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for s in SOUNDS:
		_streams[s] = load("res://audio/%s.wav" % s)
	for i in 8:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)


func play(sound: String, volume_db := 0.0, pitch := 1.0) -> void:
	for p in _players:
		if not p.playing:
			p.stream = _streams[sound]
			p.volume_db = volume_db
			p.pitch_scale = pitch
			p.play()
			return


## Plays a positional sound in the current scene; louder when the camera is close.
func play_at(sound: String, pos: Vector2, volume_db := 0.0, max_distance := 320.0) -> void:
	var scene := get_tree().current_scene
	if scene == null:
		return
	var p := AudioStreamPlayer2D.new()
	p.stream = _streams[sound]
	p.volume_db = volume_db
	p.max_distance = max_distance
	p.pitch_scale = randf_range(0.9, 1.1)
	p.global_position = pos
	p.finished.connect(p.queue_free)
	scene.add_child(p)
	p.play()
