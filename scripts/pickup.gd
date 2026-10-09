extends Area2D
## A map piece (chest) or lantern oil (flask). Touch it to collect.

@export_enum("map", "oil") var kind := "map"

@onready var sprite: Sprite2D = $Sprite

var _t := randf() * TAU


func _ready() -> void:
	sprite.texture = load("res://art/0x72/chest_full_open_anim_f0.png" if kind == "map"
			else "res://art/0x72/flask_big_yellow.png")
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_t += delta * 3.0
	sprite.position.y = -4.0 + sin(_t) * 1.5


func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	Sfx.play("pickup", -4.0)
	Events.item_picked.emit(kind, global_position)
	queue_free()
