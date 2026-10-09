extends Node2D
## One ring of the maze. Reads the map for Game.current_level, paints the tiles,
## spawns the player, hunters and items, and runs the blackout rules:
##   * lights die on the Phase timer
##   * on each blackout, some groups of walls flip (closed <-> open)
##   * the exit gate shuts after a number of blackouts, then reopens

const T := 16
const HUNTER_SCENE := preload("res://scenes/hunter.tscn")
const PICKUP_SCENE := preload("res://scenes/pickup.tscn")
const DARK_COLOR := Color(0.012, 0.012, 0.022)
const DIRS: Array[Vector2i] = [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]

@onready var floor_layer: TileMapLayer = $Floor
@onready var walls: TileMapLayer = $Walls
@onready var items: Node2D = $Items
@onready var hunters: Node2D = $Hunters
@onready var gate: StaticBody2D = $Gate
@onready var player: CharacterBody2D = $Player
@onready var darkness: CanvasModulate = $Darkness
@onready var glow: CanvasLayer = $Glow
@onready var hud: CanvasLayer = $HUD

var cfg: Dictionary
var map_size := Vector2i.ZERO
var base := {}            # Vector2i -> "#", ".", "s" or "X" (the parts that never move)
var shift_cells := {}     # Vector2i -> { "group": int, "closed_at_start": bool }
var group_flipped := {}   # group id -> bool
var astar := AStarGrid2D.new()
var start_cell := Vector2i.ZERO
var exit_cell := Vector2i.ZERO
var gate_open := true
var hunter_speed_mult := 1.0
var finished := false

var _spawns := []         # [char, cell] for hunters and items, filled by _parse

var _dark_tween: Tween
var _heartbeat_t := 0.0
var _was_safe := true


func _ready() -> void:
	cfg = Game.level()
	var tiles := MazeTiles.build()
	walls.tile_set = tiles
	floor_layer.tile_set = tiles

	_parse(load(cfg.map).MAP)
	_setup_astar()
	for c in base:
		_paint(c)
	_spawn()

	var cam: Camera2D = player.camera
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = map_size.x * T
	cam.limit_bottom = map_size.y * T
	cam.reset_smoothing.call_deferred()

	Phase.changed.connect(_on_phase)
	Events.player_caught.connect(_on_player_caught)
	Events.item_picked.connect(_on_item_picked)

	gate.position = cell_center(exit_cell)
	gate.set_open(true, true)
	darkness.color = Color.WHITE
	player.set_fuel(1.0)

	hud.setup(self)
	Phase.start(cfg.light, cfg.dark, cfg.warning)
	Events.message.emit("%s  -  %s" % [cfg.name.to_upper(), cfg.difficulty])


# ---------------------------------------------------------------- map

func _parse(text: String) -> void:
	var rows := text.strip_edges().split("\n")
	map_size = Vector2i(rows[0].length(), rows.size())
	for y in rows.size():
		var row: String = rows[y]
		for x in row.length():
			var c := Vector2i(x, y)
			var ch := row[x]
			match ch:
				"#":
					base[c] = "#"
				"s":
					base[c] = "s"
				"@":
					base[c] = "s"
					start_cell = c
				"X":
					base[c] = "X"
					exit_cell = c
				"1", "2", "3", "4":
					base[c] = "."
					shift_cells[c] = { "group": int(ch), "closed_at_start": true }
				"5", "6", "7", "8":
					base[c] = "."
					shift_cells[c] = { "group": int(ch) - 4, "closed_at_start": false }
				_:
					base[c] = "."
					if ch == "h" or ch == "m" or ch == "o":
						_spawns.append([ch, c])
	for g in cfg.groups:
		group_flipped[g] = false



func is_wall(c: Vector2i) -> bool:
	if not base.has(c):
		return true
	if shift_cells.has(c):
		var s: Dictionary = shift_cells[c]
		return s.closed_at_start != group_flipped[s.group]
	return base[c] == "#"


func _setup_astar() -> void:
	astar.region = Rect2i(Vector2i.ZERO, map_size)
	astar.cell_size = Vector2(T, T)
	astar.offset = Vector2(T / 2.0, T / 2.0)
	astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
	astar.update()
	for c in base:
		_update_astar(c)


func _update_astar(c: Vector2i) -> void:
	# hunters can't walk through walls, into safe rooms, or out of the exit
	astar.set_point_solid(c, is_wall(c) or base[c] == "s" or base[c] == "X")


func _paint(c: Vector2i) -> void:
	if is_wall(c):
		var mask := 0
		if is_wall(c + Vector2i.UP): mask |= MazeTiles.N
		if is_wall(c + Vector2i.RIGHT): mask |= MazeTiles.E
		if is_wall(c + Vector2i.LEFT): mask |= MazeTiles.W
		if not is_wall(c + Vector2i.DOWN): mask |= MazeTiles.FACE
		var row := MazeTiles.SHIFT_WALL_ROW if shift_cells.has(c) else MazeTiles.WALL_ROW
		walls.set_cell(c, MazeTiles.SOURCE_ID, Vector2i(mask, row))
		floor_layer.erase_cell(c)
		return
	walls.erase_cell(c)
	var tile: Vector2i
	if base[c] == "s":
		tile = MazeTiles.SAFE_FLOOR
	elif base[c] == "X":
		tile = MazeTiles.EXIT_FLOOR
	elif shift_cells.has(c):
		tile = MazeTiles.SHIFT_HINT_FLOOR
	else:
		# mostly plain floor, sometimes a cracked variant (stable per tile)
		var h := absi(hash(c))
		tile = Vector2i(0 if h % 10 < 8 else 1 + (h >> 4) % 7, MazeTiles.FLOOR_ROW)
	floor_layer.set_cell(c, MazeTiles.SOURCE_ID, tile)


func _spawn() -> void:
	player.global_position = cell_center(start_cell)
	Game.respawn_point = player.global_position
	for s in _spawns:
		var kind: String = s[0]
		var c: Vector2i = s[1]
		if kind == "h":
			var hunter := HUNTER_SCENE.instantiate()
			hunters.add_child(hunter)
			hunter.setup(self, c, cfg.hunter, cfg.hunter_speed, cfg.hearing)
		elif (kind == "m" and cfg.map_mode == "pieces") or (kind == "o" and cfg.lantern_fuel):
			var pickup := PICKUP_SCENE.instantiate()
			pickup.kind = "map" if kind == "m" else "oil"
			pickup.position = cell_center(c)
			items.add_child(pickup)


# ---------------------------------------------------------------- helpers used by hunters/HUD

func cell_center(c: Vector2i) -> Vector2:
	return Vector2(c) * T + Vector2(T / 2.0, T / 2.0)


func world_to_cell(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / T), floori(p.y / T))


func random_open_cell_near(c: Vector2i, radius: int) -> Vector2i:
	for i in 24:
		var t := c + Vector2i(randi_range(-radius, radius), randi_range(-radius, radius))
		if astar.is_in_boundsv(t) and not astar.is_point_solid(t):
			return t
	return c


func has_line_of_sight(from: Vector2, to: Vector2) -> bool:
	var query := PhysicsRayQueryParameters2D.create(from, to, 1)
	return get_world_2d().direct_space_state.intersect_ray(query).is_empty()


## Number of blackouts until the gate changes state (for the HUD).
func blackouts_until_gate_change() -> int:
	var cycle: int = cfg.gate_closes_after + cfg.gate_reopens_after
	var pos := Phase.blackouts % cycle
	if gate_open:
		return cfg.gate_closes_after - pos
	return cycle - pos


# ---------------------------------------------------------------- per frame

func _physics_process(delta: float) -> void:
	if finished:
		return
	var pc := world_to_cell(player.global_position)
	player.is_safe = base.get(pc, "#") == "s"
	if player.is_safe:
		Game.respawn_point = cell_center(pc)
		if not _was_safe:
			Events.message.emit("SAFE ROOM")
	_was_safe = player.is_safe

	if cfg.lantern_fuel:
		player.set_fuel(player.fuel - delta / 50.0)

	if gate_open and pc == exit_cell:
		_complete()
		return

	# heartbeat when a moving hunter is close
	_heartbeat_t -= delta
	if Phase.is_dark() and _heartbeat_t <= 0.0:
		var nearest := INF
		for h in hunters.get_children():
			nearest = minf(nearest, h.global_position.distance_to(player.global_position))
		if nearest < 120.0:
			Sfx.play("heartbeat", lerpf(0.0, -14.0, nearest / 120.0))
			_heartbeat_t = lerpf(0.45, 1.0, nearest / 120.0)


# ---------------------------------------------------------------- blackout cycle

func _on_phase(p: Phase.P) -> void:
	if finished:
		return
	if _dark_tween:
		_dark_tween.kill()
	match p:
		Phase.P.LIGHT:
			_dark_tween = create_tween()
			_dark_tween.tween_property(darkness, "color", Color.WHITE, 0.35)
			player.set_dark(false)
			Sfx.play("lights_on", -6.0)
			_update_gate()
		Phase.P.WARNING:
			# flicker: the lights are about to die
			var step: float = cfg.warning / 6.0
			_dark_tween = create_tween()
			for i in 3:
				_dark_tween.tween_property(darkness, "color", Color(0.4, 0.38, 0.45), step * 0.5)
				_dark_tween.tween_callback(Sfx.play.bind("tick", -8.0))
				_dark_tween.tween_property(darkness, "color", Color.WHITE, step * 1.5)
		Phase.P.DARK:
			_dark_tween = create_tween()
			_dark_tween.tween_property(darkness, "color", DARK_COLOR, 0.25)
			player.set_dark(true)
			Sfx.play("lights_off", -2.0)
			_shift_walls()


func _shift_walls() -> void:
	var n := Phase.blackouts   # 0 on the first blackout
	var changed: Array[Vector2i] = []
	for g in cfg.groups:
		var every: int = cfg.groups[g]
		if (n + 1) % every != 0:
			continue
		if not _flip_is_safe(g):
			continue   # someone is standing where a wall would appear; try next time
		group_flipped[g] = not group_flipped[g]
		for c in shift_cells:
			if shift_cells[c].group == g:
				changed.append(c)
	if changed.is_empty():
		return

	var to_paint := {}
	for c in changed:
		_update_astar(c)
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				var nb: Vector2i = c + Vector2i(dx, dy)
				if base.has(nb):
					to_paint[nb] = true
	for c in to_paint:
		_paint(c)

	Events.walls_shifted.emit(changed)
	Sfx.play("rumble", -3.0)
	player.shake(3.0, 0.6)
	for c in changed:
		if cell_center(c).distance_to(player.global_position) < 200.0:
			_dust(cell_center(c))


func _flip_is_safe(g: int) -> bool:
	var blocked := {}
	# every tile the player's body touches
	var p := player.global_position
	for off in [Vector2(-6, -6), Vector2(6, -6), Vector2(-6, 6), Vector2(6, 6)]:
		blocked[world_to_cell(p + off)] = true
	for h in hunters.get_children():
		for c in h.occupied_cells():
			blocked[c] = true
	for c in shift_cells:
		if shift_cells[c].group == g and not is_wall(c) and blocked.has(c):
			return false
	return true


func _update_gate() -> void:
	var cycle: int = cfg.gate_closes_after + cfg.gate_reopens_after
	var open: bool = Phase.blackouts % cycle < cfg.gate_closes_after
	if open == gate_open:
		return
	gate_open = open
	gate.set_open(open)
	Sfx.play_at("gate", gate.global_position, 4.0, 2000.0)
	Events.gate_changed.emit(open)
	if open:
		Events.message.emit("THE GATE IS OPEN")
	else:
		hunter_speed_mult = minf(hunter_speed_mult * 1.15, 1.6)
		Events.message.emit("THE GATE HAS SHUT  -  HUNTERS GROW FASTER")


func _dust(pos: Vector2) -> void:
	var p := CPUParticles2D.new()
	p.position = pos
	p.one_shot = true
	p.amount = 12
	p.lifetime = 0.7
	p.explosiveness = 0.9
	p.spread = 180.0
	p.gravity = Vector2.ZERO
	p.initial_velocity_min = 10.0
	p.initial_velocity_max = 35.0
	p.scale_amount_min = 1.0
	p.scale_amount_max = 2.0
	p.color = Color(0.6, 0.5, 0.45, 0.8)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(7, 7)
	add_child(p)
	p.emitting = true
	p.finished.connect(p.queue_free)


# ---------------------------------------------------------------- events

func _on_player_caught() -> void:
	if finished or player.frozen or player.invulnerable > 0.0:
		return
	Sfx.play("caught")
	player.shake(6.0, 0.5)
	hud.flash(Color(0.8, 0.05, 0.05, 0.55))
	player.frozen = true
	var over := Game.lose_life()
	hud.refresh()
	await get_tree().create_timer(1.0).timeout
	if over:
		finished = true
		Game.finish("caught")
	else:
		player.respawn(Game.respawn_point)
		Events.message.emit("BACK IN THE SAFE ROOM")


func _on_item_picked(kind: String, _pos: Vector2) -> void:
	if kind == "map":
		Game.map_pieces += 1
		Events.message.emit("MAP PIECE FOUND")
	elif kind == "oil":
		player.set_fuel(player.fuel + 0.5)
		Events.message.emit("LANTERN REFILLED")
	hud.refresh()


func _complete() -> void:
	finished = true
	player.frozen = true
	Phase.stop()
	if _dark_tween:
		_dark_tween.kill()
	create_tween().tween_property(darkness, "color", Color.WHITE, 0.3)
	player.set_dark(false)
	Sfx.play("level_clear")
	var last := Game.current_level == Game.LEVELS.size() - 1
	Events.message.emit("YOU ESCAPED THE MAZE" if last else "%s CLEARED" % cfg.name.to_upper())
	await get_tree().create_timer(1.8).timeout
	Game.next_level()
