class_name MazeTiles
## Builds the TileSet for res://art/maze_tiles.png in code (see tools/make_tiles.py
## for the atlas layout). Wall tiles get a collision square and a light occluder,
## so walls block both movement and the lantern's light.

const SIZE := 16
const SOURCE_ID := 0
const WALL_ROW := 0
const SHIFT_WALL_ROW := 1
const FLOOR_ROW := 2
const SAFE_FLOOR := Vector2i(8, 2)
const EXIT_FLOOR := Vector2i(9, 2)
const SHIFT_HINT_FLOOR := Vector2i(10, 2)

## Mask bits for picking a wall tile.
const N := 1
const E := 2
const W := 4
const FACE := 8


static func build() -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(SIZE, SIZE)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(0, 1)
	ts.set_physics_layer_collision_mask(0, 0)
	ts.add_occlusion_layer()
	ts.set_occlusion_layer_light_mask(0, 1)

	var src := TileSetAtlasSource.new()
	src.texture = load("res://art/maze_tiles.png")
	src.texture_region_size = Vector2i(SIZE, SIZE)
	ts.add_source(src, SOURCE_ID)

	var h := SIZE / 2.0
	var square := PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	var occluder := OccluderPolygon2D.new()
	occluder.polygon = square

	for row in [WALL_ROW, SHIFT_WALL_ROW]:
		for col in 16:
			var coords := Vector2i(col, row)
			src.create_tile(coords)
			var data := src.get_tile_data(coords, 0)
			data.add_collision_polygon(0)
			data.set_collision_polygon_points(0, 0, square)
			data.add_occluder_polygon(0)
			data.set_occluder_polygon(0, 0, occluder)
	for col in 11:
		src.create_tile(Vector2i(col, FLOOR_ROW))
	return ts
