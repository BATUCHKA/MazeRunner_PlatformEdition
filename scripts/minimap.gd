extends Control
## The memory map. It only updates the tiles you've been near, so after the
## walls shift it shows how the maze USED to look until you see it again.
##   full   (Easy)   - starts with the whole maze remembered
##   pieces (Medium) - starts blank; map pieces reveal big areas
##   none   (Hard)   - hidden

const PX := 2               # screen pixels per tile
const SEE_RADIUS := 4       # tiles remembered around the player

var level: Node
var memory := {}            # Vector2i -> 0 floor, 1 wall, 2 safe, 3 exit
var _t := 0.0


func setup(lvl: Node) -> void:
	level = lvl
	visible = level.cfg.map_mode != "none"
	custom_minimum_size = Vector2(level.map_size) * PX
	size = custom_minimum_size
	if level.cfg.map_mode == "full":
		for c in level.base:
			_remember(c)
	Events.item_picked.connect(_on_item_picked)


func _on_item_picked(kind: String, pos: Vector2) -> void:
	if kind == "map":
		reveal(level.world_to_cell(pos), 10)


func reveal(center: Vector2i, radius: int) -> void:
	for y in range(-radius, radius + 1):
		for x in range(-radius, radius + 1):
			if x * x + y * y <= radius * radius:
				var c := center + Vector2i(x, y)
				if level.base.has(c):
					_remember(c)


func _remember(c: Vector2i) -> void:
	if level.is_wall(c):
		memory[c] = 1
	else:
		memory[c] = {"s": 2, "X": 3}.get(level.base[c], 0)


func _process(delta: float) -> void:
	if not visible or level == null:
		return
	_t -= delta
	if _t <= 0.0:
		_t = 0.2
		reveal(level.world_to_cell(level.player.global_position), SEE_RADIUS)
	queue_redraw()


func _draw() -> void:
	if level == null:
		return
	draw_rect(Rect2(Vector2(-2, -2), size + Vector2(4, 4)), Color(0, 0, 0, 0.55))
	var colors := [Color(0.3, 0.26, 0.26, 0.9), Color(0.75, 0.66, 0.58), Color(0.3, 0.6, 0.6), Color(0.4, 1, 0.6)]
	for c in memory:
		draw_rect(Rect2(Vector2(c) * PX, Vector2(PX, PX)), colors[memory[c]])
	if Time.get_ticks_msec() / 250 % 2 == 0:
		var pc: Vector2 = level.player.global_position / level.T * PX
		draw_rect(Rect2(pc - Vector2(1.5, 1.5), Vector2(3, 3)), Color(1, 0.85, 0.3))
