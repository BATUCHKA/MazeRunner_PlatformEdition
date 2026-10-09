class_name Art
## Helpers for the 0x72 DungeonTileset II sprites in res://art/0x72/.


## Builds "idle" and "run" animations from files named
## <character>_idle_anim_f0..3.png and <character>_run_anim_f0..3.png.
static func sprite_frames(character: String) -> SpriteFrames:
	var frames := SpriteFrames.new()
	for anim in ["idle", "run"]:
		frames.add_animation(anim)
		frames.set_animation_speed(anim, 6.0 if anim == "idle" else 10.0)
		frames.set_animation_loop(anim, true)
		for i in 4:
			frames.add_frame(anim, load("res://art/0x72/%s_%s_anim_f%d.png" % [character, anim, i]))
	return frames
