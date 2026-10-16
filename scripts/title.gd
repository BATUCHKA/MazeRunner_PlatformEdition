extends Control
## Title screen.

@onready var buttons: HBoxContainer = %Buttons
@onready var demon: AnimatedSprite2D = %Demon
@onready var knight: AnimatedSprite2D = %Knight


func _ready() -> void:
	get_tree().paused = false
	knight.sprite_frames = Art.sprite_frames("knight_m")
	knight.play("idle")
	demon.sprite_frames = Art.sprite_frames("big_demon")
	demon.play("idle")
	_add_ring_buttons()
	%Quit.pressed.connect(get_tree().quit)


## One button per ring in Game.LEVELS, placed before Quit. Focus starts on the
## ring picked last time, so "Enter" replays it.
func _add_ring_buttons() -> void:
	for i in Game.LEVELS.size():
		var cfg: Dictionary = Game.LEVELS[i]
		var b := Button.new()
		b.text = "%s\n%s" % [cfg.name, cfg.difficulty]
		b.custom_minimum_size = Vector2(96, 0)
		b.add_theme_font_size_override("font_size", 11)
		b.pressed.connect(Game.new_run.bind(i))
		buttons.add_child(b)
		buttons.move_child(b, i)
		if i == Game.start_level:
			b.grab_focus.call_deferred()


func _process(_delta: float) -> void:
	# the demon only "moves" when the title's lights flicker off
	var dark := fmod(Time.get_ticks_msec() / 1000.0, 4.0) > 3.3
	%Shade.color.a = 0.85 if dark else 0.0
	demon.speed_scale = 1.0 if dark else 0.0
