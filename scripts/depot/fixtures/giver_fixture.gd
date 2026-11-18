class_name GiverFixture
extends Fixture
## Algo de donde se saca una cosa con F, directamente a la mano: la caja de las
## etiquetas (una en blanco), el rollo de bolsas (una bolsa).

var model: Node3D
## Lo que da y con qué estado.
var item_id: StringName = &""
var extra: Dictionary = {}


func _ready() -> void:
	var bodies: Array[Node] = model.find_children("*", "StaticBody3D", true, false)
	add_use(bodies[0] if not bodies.is_empty() else model)
	super._ready()


func _on_used(player: Player, _action: StringName) -> void:
	var items: WorldItems = world_items()
	if items != null and player.held_item() == null:
		items.give(player, item_id, extra)
