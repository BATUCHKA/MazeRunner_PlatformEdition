extends SceneTree
## Saves screenshots of the title and each ring in light and dark, for a quick
## visual check. Needs a window (not --headless):
##   Godot --path . --script res://tests/capture.gd -- <output_dir>

var out_dir := "user://captures"
var steps := []
var wait := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	steps = [
		[5, func(): change_scene_to_file("res://scenes/title.tscn")],
		[40, func(): pass],
		[1, func(): _shot("title")],
		[1, func(): root.get_node("Game").new_run()],
	]
	for ring in root.get_node("Game").LEVELS.size():
		steps += [
			[30, func(): Input.action_press("move_right")],
			[25, func(): Input.action_release("move_right")],
			[10, func(): _shot("ring%d_light" % ring)],
			[3, func(): root.get_node("Phase").timer.start(0.01)],   # -> warning
			[3, func(): root.get_node("Phase").timer.start(0.01)],   # -> dark
			[45, func(): pass],
			[1, func(): _shot("ring%d_dark" % ring)],
			[1, func(): root.get_node("Game").next_level()],
		]


func _process(_delta: float) -> bool:
	if wait > 0:
		wait -= 1
		return false
	if steps.is_empty():
		return true
	var s = steps.pop_front()
	s[1].call()
	wait = s[0]
	return false


func _shot(shot_name: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(out_dir)
	img.save_png(out_dir.path_join(shot_name + ".png"))
	print("saved ", shot_name)
