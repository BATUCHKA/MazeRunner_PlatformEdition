extends Control
## Shown when the run ends, either escaped or caught.


func _ready() -> void:
	get_tree().paused = false
	var escaped := Game.result == "escaped"
	%Headline.text = "YOU ESCAPED" if escaped else "CAUGHT IN THE DARK"
	%Headline.modulate = Color(0.6, 1, 0.7) if escaped else Color(1, 0.45, 0.4)
	var ring: String = Game.LEVELS[mini(Game.current_level, Game.LEVELS.size() - 1)].name
	var t := int(Game.run_time)
	var lines := []
	if escaped:
		if Game.start_level == 0:
			lines.append("All %d rings cleared." % Game.LEVELS.size())
		else:
			lines.append("Cleared %s to the end." % Game.LEVELS[Game.start_level].name)
	else:
		lines.append("Taken in %s." % ring)
	lines.append("Time  %d:%02d" % [t / 60, t % 60])
	lines.append("Times caught  %d" % Game.times_caught)
	%Stats.text = "\n".join(lines)
	%AgainButton.pressed.connect(Game.new_run)
	%TitleButton.pressed.connect(Game.to_title)
	%AgainButton.grab_focus()
