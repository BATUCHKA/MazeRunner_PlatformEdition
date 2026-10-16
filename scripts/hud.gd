extends CanvasLayer
## On-screen info: lives, blackout timer, gate status, items, memory map,
## messages and the pause menu. Runs while paused so the pause menu works.

const HEART_FULL := preload("res://art/0x72/ui_heart_full.png")
const HEART_EMPTY := preload("res://art/0x72/ui_heart_empty.png")

@onready var hearts: HBoxContainer = %Hearts
@onready var level_label: Label = %LevelLabel
@onready var phase_label: Label = %PhaseLabel
@onready var phase_bar: ProgressBar = %PhaseBar
@onready var gate_label: Label = %GateLabel
@onready var items_label: Label = %ItemsLabel
@onready var safe_label: Label = %SafeLabel
@onready var minimap: Control = %MiniMap
@onready var banner: Label = %Banner
@onready var flash_rect: ColorRect = %Flash
@onready var pause_menu: Control = %PauseMenu

var level: Node
var _banner_tween: Tween
var _bar_fill: StyleBoxFlat


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	pause_menu.hide()
	banner.modulate.a = 0.0
	flash_rect.color.a = 0.0
	_bar_fill = phase_bar.get_theme_stylebox("fill").duplicate()
	phase_bar.add_theme_stylebox_override("fill", _bar_fill)
	Events.message.connect(show_message)
	%ResumeButton.pressed.connect(_toggle_pause)
	%QuitButton.pressed.connect(_quit_to_title)


func setup(lvl: Node) -> void:
	level = lvl
	level_label.text = "%s  %s" % [level.cfg.name, level.cfg.difficulty]
	minimap.setup(level)
	refresh()


func refresh() -> void:
	# one heart per starting life; extra heart slots in the scene stay hidden
	for i in hearts.get_child_count():
		var heart: TextureRect = hearts.get_child(i)
		heart.visible = i < Game.START_LIVES
		heart.texture = HEART_FULL if i < Game.lives else HEART_EMPTY
	if level == null:
		return
	if level.cfg.map_mode == "pieces":
		items_label.text = "Map pieces: %d" % Game.map_pieces
	elif level.cfg.lantern_fuel:
		items_label.text = "Lantern"
	else:
		items_label.text = ""


func _process(_delta: float) -> void:
	if level == null:
		return
	match Phase.phase:
		Phase.P.LIGHT:
			phase_label.text = "LIGHT"
			_bar_fill.bg_color = Color(1, 0.8, 0.4)
		Phase.P.WARNING:
			phase_label.text = "LIGHTS FAILING"
			_bar_fill.bg_color = Color(1, 0.45, 0.3)
		Phase.P.DARK:
			phase_label.text = "BLACKOUT"
			_bar_fill.bg_color = Color(0.55, 0.45, 0.9)
	phase_bar.value = Phase.fraction_left() * 100.0

	var n: int = level.blackouts_until_gate_change()
	var plural := "blackout" if n == 1 else "blackouts"
	if level.gate_open:
		gate_label.text = "Gate open - shuts in %d %s" % [n, plural]
		gate_label.modulate = Color(0.6, 1, 0.7)
	else:
		gate_label.text = "Gate SHUT - opens in %d %s" % [n, plural]
		gate_label.modulate = Color(1, 0.5, 0.45)

	if level.cfg.lantern_fuel:
		items_label.text = "Lantern oil: %d%%" % roundi(level.player.fuel * 100.0)
	safe_label.visible = level.player.is_safe
	items_label.visible = items_label.text != ""


func show_message(text: String) -> void:
	banner.text = text
	if _banner_tween:
		_banner_tween.kill()
	_banner_tween = create_tween()
	_banner_tween.tween_property(banner, "modulate:a", 1.0, 0.15)
	_banner_tween.tween_interval(1.6)
	_banner_tween.tween_property(banner, "modulate:a", 0.0, 0.5)


func flash(color: Color) -> void:
	flash_rect.color = color
	create_tween().tween_property(flash_rect, "color:a", 0.0, 0.6)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") or event.is_action_pressed("ui_cancel"):
		_toggle_pause()
		get_viewport().set_input_as_handled()


func _toggle_pause() -> void:
	var paused := not get_tree().paused
	get_tree().paused = paused
	pause_menu.visible = paused
	if paused:
		%ResumeButton.grab_focus()


func _quit_to_title() -> void:
	get_tree().paused = false
	Game.to_title()
