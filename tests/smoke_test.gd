extends SceneTree
## Headless smoke test: plays through all four rings with a sped-up blackout
## cycle, walks the player around, lets monsters catch them, and checks the
## run reaches the end screen.
##   Godot --headless --path . --script res://tests/smoke_test.gd

var frames := 0
var log_lines := []
var phase_counts := {}
var shifts := 0
var caught := 0
var levels_seen := {}
var problems := []


var started := false
var want_catch := false
var die_mode := false


func _start() -> void:
	started = true
	die_mode = "die" in OS.get_cmdline_user_args()
	root.get_node("Game").new_run()
	root.get_node("Events").walls_shifted.connect(func(cells): shifts += 1)
	root.get_node("Events").player_caught.connect(func(): caught += 1)
	root.get_node("Phase").changed.connect(func(p): phase_counts[p] = phase_counts.get(p, 0) + 1)


func _process(_delta: float) -> bool:
	if not started:
		_start()
		return false
	frames += 1
	var phase = root.get_node("Phase")
	var game = root.get_node("Game")
	var scene = current_scene
	if scene and scene.name == "Level":
		levels_seen[game.current_level] = true
		# speed up the cycle
		if phase.timer.time_left > 0.4:
			phase.timer.start(0.4)
		var player = scene.player
		# wander: alternate directions
		var dirs = ["move_right", "move_down", "move_left", "move_up"]
		for a in dirs:
			Input.action_release(a)
		Input.action_press(dirs[(frames / 40) % 4])
		if (frames / 90) % 2 == 0:
			Input.action_press("run")
		else:
			Input.action_release("run")
		# every so often: check invariants
		if frames % 30 == 0:
			var pc = scene.world_to_cell(player.global_position)
			if scene.is_wall(pc):
				problems.append("player inside wall at %s (level %d)" % [pc, game.current_level])
			for h in scene.monsters.get_children():
				var hc = h.cell()
				if scene.is_wall(hc):
					problems.append("monster inside wall at %s" % hc)
		# after a while, let a monster reach the player once per level
		if frames % 300 == 150 or (die_mode and frames % 60 == 0):
			want_catch = true
		if die_mode and want_catch and phase.is_dark() and player.is_safe and scene.monsters.get_child_count() > 0:
			player.global_position = scene.monsters.get_child(0).global_position
		if want_catch and phase.is_dark() and scene.monsters.get_child_count() > 0 \
				and not player.is_safe and player.invulnerable <= 0.0 and not player.frozen:
			var h = scene.monsters.get_child(0)
			h.global_position = player.global_position + Vector2(4, 0)
			want_catch = false
		# then teleport to the exit when the gate is open
		if frames % 1500 == 1400 and not die_mode:
			if scene.gate_open:
				player.global_position = scene.cell_center(scene.exit_cell)
			else:
				player.global_position = scene.cell_center(scene.start_cell)
	if scene and scene.name == "EndScreen":
		print("END: result=", game.result, " lives=", game.lives, " caught=", game.times_caught)
		_report()
		return true
	if frames > 60 * 200:
		print("TIMEOUT in scene ", scene.name if scene else "none", " level ", game.current_level)
		_report()
		return true
	return false


func _report() -> void:
	print("frames=", frames, " levels_seen=", levels_seen.keys(), " phases=", phase_counts,
		" wall_shifts=", shifts, " caught_signals=", caught)
	print("problems: ", problems if problems else "none")
