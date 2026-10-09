extends Node
## The blackout cycle (autoload "Phase"): LIGHT -> WARNING -> DARK -> LIGHT ...
## Everything that reacts to the lights listens to `changed`.

signal changed(phase: P)

enum P { LIGHT, WARNING, DARK }

var phase := P.LIGHT
var blackouts := 0          # how many DARK phases have finished this level
var times := { P.LIGHT: 6.0, P.WARNING: 1.0, P.DARK: 2.0 }
var timer := Timer.new()


func _ready() -> void:
	timer.one_shot = true
	add_child(timer)
	timer.timeout.connect(_next)


func start(light: float, dark: float, warning := 1.0) -> void:
	times = { P.LIGHT: light, P.WARNING: warning, P.DARK: dark }
	blackouts = 0
	_enter(P.LIGHT)


func stop() -> void:
	timer.stop()
	phase = P.LIGHT


func is_dark() -> bool:
	return phase == P.DARK


## 0..1, how much of the current phase is left.
func fraction_left() -> float:
	if timer.is_stopped():
		return 0.0
	return timer.time_left / times[phase]


func _next() -> void:
	match phase:
		P.LIGHT:
			_enter(P.WARNING)
		P.WARNING:
			_enter(P.DARK)
		P.DARK:
			blackouts += 1
			_enter(P.LIGHT)


func _enter(p: P) -> void:
	phase = p
	timer.start(times[p])
	changed.emit(p)
