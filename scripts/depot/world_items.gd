class_name WorldItems
extends Node3D
## Los objetos sueltos del mundo: los crea el anfitrión y los ven todos.
##
## Cada objeto es su modelo (un [RigidBody3D]) más los componentes que lo hacen
## jugable: [Interactable], [Carryable], [TransformSync] y un sincronizador de
## su estado. En los invitados la física está congelada: solo siguen lo que
## dice el anfitrión. Se guardan con la partida, cada uno donde está.

const MODELS_DIR: String = "res://assets/models/"
const LAYER_OBJECTS: int = 1 << 2
const MASK_OBJECTS: int = (1 << 0) | (1 << 1) | (1 << 2)
const SAVE_KEY: String = "objetos"

var _spawner: MultiplayerSpawner
var _next_uid: int = 1


func _enter_tree() -> void:
	SaveSystem.register_provider(SAVE_KEY, self)


func _exit_tree() -> void:
	SaveSystem.unregister_provider(SAVE_KEY)


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
	return spawn_state(state, where)


## Pone en el mundo un objeto con su estado (uno guardado, o uno que sale de otro
## sitio: de una caja, de la mano de un cliente). Solo el anfitrión.
func spawn_state(state: ItemState, where: Transform3D) -> Node3D:
	if not multiplayer.is_server() or state.data == null:
		return null
	if state.uid <= 0:
		state.uid = _next_uid
	_next_uid = maxi(_next_uid, state.uid + 1)
	return _spawner.spawn({"state": state.to_dict(), "where": where}) as Node3D


## Quita un objeto del mundo (se lo lleva un cliente, se come, va a la basura).
## Solo el anfitrión.
func remove_item(item: Carryable) -> void:
	if not multiplayer.is_server() or item == null:
		return
	item.force_drop()
	var holder: Node = item.get_parent()
	while holder != null and holder.get_parent() != self:
		holder = holder.get_parent()
	if holder != null:
		holder.queue_free()


## El objeto con ese identificador, si está en el mundo.
func find_item(uid: int) -> Carryable:
	for item: Carryable in items():
		if item.state.uid == uid:
			return item
	return null


## Quita todos los objetos (al cargar una partida o al irse del depósito).
func clear() -> void:
	for child: Node in get_children():
		if child != _spawner:
			child.free()


func save_state() -> Dictionary:
	var saved: Array = []
	for item: Carryable in items():
		if item.is_queued_for_deletion() or item.get_parent().is_queued_for_deletion():
			continue
		var where: Transform3D = (item.get_parent() as Node3D).global_transform
		saved.append({"state": item.state.to_dict(), "where": _transform_to_array(where)})
	return {"objetos": saved, "siguiente": _next_uid}


func load_state(data: Dictionary) -> void:
	if not multiplayer.is_server():
		return
	clear()
	_next_uid = maxi(1, int(data.get("siguiente", 1)))
	var saved: Variant = data.get("objetos", [])
	if not saved is Array:
		return
	for entry: Variant in saved:
		if not entry is Dictionary:
			continue
		var values: Dictionary = entry
		var state: ItemState = ItemState.from_dict(values.get("state", {}))
		if state.data != null:
			spawn_state(state, _array_to_transform(values.get("where", [])))


static func _transform_to_array(where: Transform3D) -> Array:
	var b: Basis = where.basis
	var o: Vector3 = where.origin
	return [b.x.x, b.x.y, b.x.z, b.y.x, b.y.y, b.y.z, b.z.x, b.z.y, b.z.z, o.x, o.y, o.z]


static func _array_to_transform(values: Variant) -> Transform3D:
	if not values is Array or (values as Array).size() != 12:
		return Transform3D.IDENTITY
	var v: Array = values
	return Transform3D(
		Vector3(v[0], v[1], v[2]),
		Vector3(v[3], v[4], v[5]),
		Vector3(v[6], v[7], v[8]),
		Vector3(v[9], v[10], v[11])
	)


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
	carryable.synced_state = state.to_dict()
	body.add_child(carryable)
	var sync: TransformSync = TransformSync.new()
	sync.name = "TransformSync"
	body.add_child(sync)
	body.add_child(_state_sync())
	return holder


## El sincronizador del estado del objeto: lo manda el anfitrión cuando cambia.
static func _state_sync() -> MultiplayerSynchronizer:
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	var path: NodePath = NodePath("Carryable:synced_state")
	config.add_property(path)
	config.property_set_spawn(path, true)
	config.property_set_replication_mode(path, SceneReplicationConfig.REPLICATION_MODE_ON_CHANGE)
	var sync: MultiplayerSynchronizer = MultiplayerSynchronizer.new()
	sync.name = "EstadoSync"
	sync.replication_config = config
	sync.root_path = NodePath("..")
	return sync
