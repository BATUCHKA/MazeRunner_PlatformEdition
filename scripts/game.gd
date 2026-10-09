extends Node
## Global run state (autoload "Game"). Lives here so it survives scene changes.

const LEVEL_SCENE := "res://scenes/level.tscn"
const TITLE_SCENE := "res://scenes/title.tscn"
const END_SCENE := "res://scenes/end_screen.tscn"

## One entry per ring. Tweak these numbers to tune difficulty.
## groups: shift group id -> it flips on every Nth blackout.
const LEVELS := [
	{
		"name": "Outer Ring", "difficulty": "EASY", "map": "res://levels/outer_ring.gd",
		"light": 6.0, "warning": 1.2, "dark": 2.5,
		"gate_closes_after": 6, "gate_reopens_after": 2,
		"hunter": "big_zombie", "hunter_speed": 42.0, "hearing": 200.0,
		"map_mode": "full", "lantern_fuel": false,
		"groups": {1: 1, 2: 2},
	},
	{
		"name": "Inner Ring", "difficulty": "MEDIUM", "map": "res://levels/inner_ring.gd",
		"light": 5.0, "warning": 1.0, "dark": 3.0,
		"gate_closes_after": 4, "gate_reopens_after": 2,
		"hunter": "ogre", "hunter_speed": 52.0, "hearing": 240.0,
		"map_mode": "pieces", "lantern_fuel": false,
		"groups": {1: 1, 2: 1, 3: 2, 4: 3},
	},
	{
		"name": "The Core", "difficulty": "HARD", "map": "res://levels/the_core.gd",
		"light": 4.0, "warning": 0.8, "dark": 4.0,
		"gate_closes_after": 3, "gate_reopens_after": 2,
		"hunter": "big_demon", "hunter_speed": 62.0, "hearing": 290.0,
		"map_mode": "none", "lantern_fuel": true,
		"groups": {1: 1, 2: 1, 3: 1, 4: 2},
	},
]

const START_LIVES := 5

var lives := START_LIVES
var current_level := 0
var map_pieces := 0
var run_time := 0.0
var times_caught := 0
var result := ""            # "escaped" or "caught", read by the end screen
var respawn_point := Vector2.ZERO
var running := false        # true while a level is being played


func _process(delta: float) -> void:
	if running and not get_tree().paused:
		run_time += delta


func level() -> Dictionary:
	return LEVELS[current_level]


func new_run() -> void:
	lives = START_LIVES
	current_level = 0
	map_pieces = 0
	run_time = 0.0
	times_caught = 0
	result = ""
	_load_level()


func next_level() -> void:
	current_level += 1
	map_pieces = 0
	if current_level >= LEVELS.size():
		finish("escaped")
	else:
		_load_level()


func lose_life() -> bool:
	## Returns true if the run is over.
	lives -= 1
	times_caught += 1
	return lives <= 0


func finish(how: String) -> void:
	result = how
	running = false
	Phase.stop()
	get_tree().change_scene_to_file.call_deferred(END_SCENE)


func to_title() -> void:
	running = false
	Phase.stop()
	get_tree().change_scene_to_file.call_deferred(TITLE_SCENE)


func _load_level() -> void:
	running = true
	get_tree().change_scene_to_file.call_deferred(LEVEL_SCENE)
