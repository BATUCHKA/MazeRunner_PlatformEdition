extends Control
## Title screen.

@onready var start_button: Button = %StartButton
@onready var demon: AnimatedSprite2D = %Demon
@onready var knight: AnimatedSprite2D = %Knight


func _ready() -> void:
	get_tree().paused = false
	knight.sprite_frames = Art.sprite_frames("knight_m")
	knight.play("idle")
	demon.sprite_frames = Art.sprite_frames("big_demon")
	demon.play("idle")
	start_button.pressed.connect(Game.new_run)
	start_button.grab_focus()
	%Quit.pressed.connect(get_tree().quit)


func _process(_delta: float) -> void:
	# the demon only "moves" when the title's lights flicker off
	var dark := fmod(Time.get_ticks_msec() / 1000.0, 4.0) > 3.3
	%Shade.color.a = 0.85 if dark else 0.0
	demon.speed_scale = 1.0 if dark else 0.0
