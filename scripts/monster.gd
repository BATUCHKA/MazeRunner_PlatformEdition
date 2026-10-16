extends Node2D
## A monster. Frozen like a statue while the lights are on. In the dark it
## wanders, walks toward any running footsteps it hears, and chases the player
## on sight. Monsters never enter safe rooms.
##
## Movement is tile-to-tile along paths from the level's AStarGrid2D, so
## monsters never get stuck on corners.

enum S { FROZEN, WANDER, HUNT, CHASE }

const CATCH_DISTANCE := 10.0
const SIGHT_RANGE := 110.0
const CHASE_BOOST := 1.25

var level: Node            # the Level node (scripts/level.gd)
var speed := 50.0
var hearing := 250.0
var state := S.FROZEN
var path: Array[Vector2i] = []

var _repath_t := 0.0
var _growl_t := 3.0
var _eyes: Node2D

@onready var sprite: AnimatedSprite2D = $Sprite


func setup(lvl: Node, cell: Vector2i, kind: String, spd: float, hear: float) -> void:
	level = lvl
	speed = spd
	hearing = hear
	global_position = level.cell_center(cell)
	sprite.sprite_frames = Art.sprite_frames(kind)
	sprite.play("idle")
	sprite.speed_scale = 0.0
	_eyes = preload("res://scripts/monster_eyes.gd").new()
	level.glow.add_child(_eyes)

	Phase.changed.connect(_on_phase)
	Events.noise_made.connect(_on_noise)
	Events.walls_shifted.connect(_on_walls_shifted)


func _exit_tree() -> void:
	if is_instance_valid(_eyes):
		_eyes.queue_free()


func cell() -> Vector2i:
	return level.world_to_cell(global_position)


## Cells this monster occupies or is about to step into (walls must not close on them).
func occupied_cells() -> Array[Vector2i]:
	var cells: Array[Vector2i] = [cell()]
	if not path.is_empty():
		cells.append(path[0])
	return cells


func _on_phase(p: Phase.P) -> void:
	if p == Phase.P.DARK:
		state = S.WANDER
		path.clear()
	else:
		state = S.FROZEN


func _on_noise(pos: Vector2) -> void:
	if state == S.FROZEN or state == S.CHASE or level.player.is_safe:
		return
	if global_position.distance_to(pos) < hearing:
		state = S.HUNT
		_go(level.world_to_cell(pos))


func _on_walls_shifted(_cells: Array) -> void:
	if not path.is_empty():
		_go(path.back())


func _go(target: Vector2i) -> void:
	var from := cell()
	var p: Array[Vector2i] = level.astar.get_id_path(from, target, true)
	if not p.is_empty() and p[0] == from:
		p.remove_at(0)
	path = p


func _physics_process(delta: float) -> void:
	var player: Node2D = level.player
	var dist := global_position.distance_to(player.global_position)
	_update_eyes(dist)

	if state == S.FROZEN:
		sprite.speed_scale = 0.0
		return
	sprite.speed_scale = 1.0

	var can_see: bool = not player.is_safe and dist < SIGHT_RANGE \
			and level.has_line_of_sight(global_position, player.global_position)
	if can_see:
		state = S.CHASE
	elif state == S.CHASE and (player.is_safe or dist > SIGHT_RANGE * 1.6):
		state = S.WANDER
		path.clear()

	if state == S.CHASE:
		_repath_t -= delta
		if _repath_t <= 0.0:
			_repath_t = 0.3
			_go(level.world_to_cell(player.global_position))

	if path.is_empty():
		if state == S.HUNT:
			state = S.WANDER
		_go(level.random_open_cell_near(cell(), 8))

	if not path.is_empty():
		var target: Vector2 = level.cell_center(path[0])
		var boost := CHASE_BOOST if state == S.CHASE else 1.0
		var step: float = speed * level.monster_speed_mult * boost * delta
		var dir := target - global_position
		if absf(dir.x) > 0.1:
			sprite.flip_h = dir.x < 0.0
		global_position = global_position.move_toward(target, step)
		sprite.play("run")
		if global_position.distance_to(target) < 0.5:
			path.remove_at(0)
	else:
		sprite.play("idle")

	if dist < CATCH_DISTANCE and not player.is_safe and player.invulnerable <= 0.0 and not player.frozen:
		Events.player_caught.emit()

	_growl_t -= delta
	if _growl_t <= 0.0:
		_growl_t = randf_range(2.5, 5.0)
		Sfx.play_at("growl", global_position, -2.0, 300.0)


## Glowing eyes live on a layer the darkness doesn't touch, so you can spot
## monsters in the dark (and see when they freeze).
func _update_eyes(dist: float) -> void:
	if not is_instance_valid(_eyes):
		return
	_eyes.global_position = global_position + Vector2(0, -20)
	_eyes.visible = Phase.phase != Phase.P.LIGHT and dist < 240.0
	_eyes.facing_left = sprite.flip_h
