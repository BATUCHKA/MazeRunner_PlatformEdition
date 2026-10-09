extends Node2D
## Two glowing red eyes drawn on the Glow layer above the darkness.

var facing_left := false:
	set(value):
		if value != facing_left:
			facing_left = value
			queue_redraw()


func _process(_delta: float) -> void:
	# a slow pulse so they feel alive
	modulate.a = 0.75 + 0.25 * sin(Time.get_ticks_msec() * 0.006)


func _draw() -> void:
	var shift := -2.0 if facing_left else 2.0
	for x in [-3.0, 3.0]:
		draw_circle(Vector2(x + shift, 0), 3.0, Color(1, 0.15, 0.1, 0.25))
		draw_rect(Rect2(x + shift - 1, -0.5, 2, 1.5), Color(1, 0.35, 0.25))
