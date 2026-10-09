extends CharacterBody2D
## The runner. Walking is silent; running is fast but makes noise hunters can hear.

@export var walk_speed := 70.0
@export var run_speed := 120.0
## Seconds between noise pulses while running.
@export var noise_interval := 0.25

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var lantern: PointLight2D = $Lantern
@onready var wall_light: PointLight2D = $WallLight
@onready var camera: Camera2D = $Camera2D

var frozen := false          # true during level transitions / after being caught
var is_safe := false         # set by the level while standing in a safe room
var invulnerable := 0.0      # seconds of grace after a respawn
var fuel := 1.0              # lantern fuel 0..1 (only drains on Hard)

var _noise_t := 0.0
var _step_t := 0.0
var _light_tween: Tween
var _shake_tween: Tween


func _ready() -> void:
	sprite.sprite_frames = Art.sprite_frames("knight_m")
	sprite.play("idle")
	lantern.energy = 0.0
	wall_light.energy = 0.0


func _physics_process(delta: float) -> void:
	invulnerable = maxf(invulnerable - delta, 0.0)
	sprite.modulate.a = 0.35 if invulnerable > 0.0 and int(invulnerable * 10.0) % 2 == 0 else 1.0

	if frozen:
		velocity = Vector2.ZERO
		sprite.play("idle")
		return

	var dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var running := Input.is_action_pressed("run")
	velocity = dir * (run_speed if running else walk_speed)
	move_and_slide()

	if dir == Vector2.ZERO:
		sprite.play("idle")
		sprite.speed_scale = 1.0
		return

	sprite.play("run")
	sprite.speed_scale = 1.5 if running else 1.0
	if dir.x != 0.0:
		sprite.flip_h = dir.x < 0.0

	_step_t -= delta
	if _step_t <= 0.0:
		_step_t = 0.2 if running else 0.34
		Sfx.play("step", -5.0 if running else -18.0, randf_range(0.85, 1.15))

	if running:
		_noise_t -= delta
		if _noise_t <= 0.0:
			_noise_t = noise_interval
			Events.noise_made.emit(global_position)


## Lantern on in the dark, off in daylight (it would only wash out the colours).
func set_dark(dark: bool) -> void:
	if _light_tween:
		_light_tween.kill()
	_light_tween = create_tween().set_parallel()
	_light_tween.tween_property(lantern, "energy", 1.2 if dark else 0.0, 0.3)
	_light_tween.tween_property(wall_light, "energy", 0.8 if dark else 0.0, 0.3)


func set_fuel(value: float) -> void:
	fuel = clampf(value, 0.0, 1.0)
	lantern.texture_scale = lerpf(0.42, 1.0, fuel)
	wall_light.texture_scale = lerpf(0.32, 0.6, fuel)


func respawn(pos: Vector2) -> void:
	global_position = pos
	velocity = Vector2.ZERO
	invulnerable = 2.0
	frozen = false


func shake(strength := 4.0, duration := 0.4) -> void:
	if _shake_tween:
		_shake_tween.kill()
	_shake_tween = create_tween()
	var steps := 8
	for i in steps:
		var falloff := 1.0 - float(i) / steps
		_shake_tween.tween_property(camera, "offset",
				Vector2(randf_range(-1, 1), randf_range(-1, 1)) * strength * falloff, duration / steps)
	_shake_tween.tween_property(camera, "offset", Vector2.ZERO, 0.05)
