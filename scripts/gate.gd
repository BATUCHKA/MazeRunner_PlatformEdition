extends StaticBody2D
## The exit gate. Blocks the exit tile while shut; the level opens and closes
## it on a blackout schedule.

@onready var shape: CollisionShape2D = $Shape

var is_open := true
var _bars_y := -14.0   # how far the bars are raised (-14 = open, 0 = shut)


func set_open(open: bool, instant := false) -> void:
	is_open = open
	shape.set_deferred("disabled", open)
	var target := -14.0 if open else 0.0
	if instant:
		_bars_y = target
		queue_redraw()
	else:
		create_tween().tween_method(_set_bars, _bars_y, target, 0.25 if not open else 0.8)


func _set_bars(y: float) -> void:
	_bars_y = y
	queue_redraw()


func _draw() -> void:
	# frame
	draw_rect(Rect2(-8, -8, 16, 2), Color(0.29, 0.23, 0.22))
	# iron bars, raised by _bars_y and clipped to the doorway
	var top := -8.0
	var bottom := 8.0 + _bars_y
	if bottom > top + 1.0:
		for x in [-6.0, -2.0, 2.0, 6.0]:
			draw_rect(Rect2(x - 0.75, top, 1.5, bottom - top), Color(0.55, 0.57, 0.62))
		draw_rect(Rect2(-8, bottom - 2.0, 16, 2), Color(0.38, 0.4, 0.45))
	if is_open:
		# a faint green glow on the stairs so the exit reads as "go"
		draw_circle(Vector2.ZERO, 6.0, Color(0.4, 1.0, 0.6, 0.18))
