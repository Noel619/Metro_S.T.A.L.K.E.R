class_name WorldItems
extends Node3D
## Los objetos sueltos del mundo: los crea el anfitrión y los ven todos.
##
## Cada objeto es su modelo (un [RigidBody3D]) más los componentes que lo hacen
## jugable: [Interactable], [Carryable] y [TransformSync]. En los invitados la
## física está congelada: solo siguen lo que dice el anfitrión.

const MODELS_DIR: String = "res://assets/models/"
const LAYER_OBJECTS: int = 1 << 2
const MASK_OBJECTS: int = (1 << 0) | (1 << 1) | (1 << 2)

var _spawner: MultiplayerSpawner
var _next_uid: int = 1


func _ready() -> void:
	_spawner = MultiplayerSpawner.new()
	_spawner.name = "Generador"
	_spawner.spawn_function = _build
	add_child(_spawner)
	_spawner.spawn_path = _spawner.get_path_to(self)


## Pone un objeto en el mundo. Solo el anfitrión.
func spawn_item(
	item_id: StringName, where: Transform3D, condition: float = 1.0, contamination: float = 0.0
) -> Node3D:
	if not multiplayer.is_server():
		return null
	var state: ItemState = ItemState.create(item_id, _next_uid)
	if state.data == null:
		return null
	_next_uid += 1
	state.condition = condition
	state.contamination = contamination
	return _spawner.spawn({"state": state.to_dict(), "where": where}) as Node3D


## El componente [Carryable] de todos los objetos.
func items() -> Array[Carryable]:
	var found: Array[Carryable] = []
	for node: Node in find_children("*", "Carryable", true, false):
		found.append(node as Carryable)
	return found


func _build(values: Dictionary) -> Node:
	var state: ItemState = ItemState.from_dict(values["state"])
	var holder: Node3D = load(MODELS_DIR + state.data.model + ".glb").instantiate()
	holder.name = "objeto_%d" % state.uid
	var body: RigidBody3D = holder.find_children("*", "RigidBody3D", true, false)[0]
	body.transform = values["where"]
	body.mass = state.data.weight
	body.collision_layer = LAYER_OBJECTS
	body.collision_mask = MASK_OBJECTS
	body.continuous_cd = state.data.weight < Carryable.CCD_WEIGHT
	# Las mallas cuelgan de un nodo propio: quien lo lleva lo dibuja en sus manos
	# aunque el cuerpo físico vaya un poco por detrás (Carryable).
	var visual: Node3D = Node3D.new()
	visual.name = "Visual"
	body.add_child(visual)
	for child: Node in body.get_children():
		if child is MeshInstance3D:
			# Fuera del árbol, Godot no reconoce al dueño como antepasado y avisa.
			child.owner = null
			child.reparent(visual, false)
	body.linear_damp = 0.2
	body.angular_damp = 0.6
	if not multiplayer.is_server():
		body.freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
		body.freeze = true
	var interactable: Interactable = Interactable.new()
	interactable.name = "Interactable"
	body.add_child(interactable)
	var carryable: Carryable = Carryable.new()
	carryable.name = "Carryable"
	carryable.state = state
	body.add_child(carryable)
	var sync: TransformSync = TransformSync.new()
	sync.name = "TransformSync"
	body.add_child(sync)
	return holder
