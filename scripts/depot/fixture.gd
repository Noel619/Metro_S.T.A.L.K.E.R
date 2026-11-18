class_name Fixture
extends Node3D
## Una cosa fija del local con estado propio: una mancha, una telaraña, la
## lámpara, la persiana… Su estado vive en [DepotWorld], por [member fixture_id];
## aquí se pinta según ese estado ([method _refresh]) y, en el anfitrión, se
## cambia ([method set_value]).
##
## Se construye igual en todos los equipos (mismo nombre y misma ruta), así que
## sus cuerpos y sus [Workable] se pueden nombrar por la red.

## Ha cambiado su estado.
signal refreshed

## La capa de lo que solo se alcanza con la mirada (Player.MASK_REACH).
const REACH_LAYER: int = 1 << 4

@export var fixture_id: String = ""

var world: DepotWorld
## Lo que se puede trabajar de esta cosa (puede colgar de su modelo).
var workables: Array[Workable] = []


func _ready() -> void:
	world = DepotWorld.find(self)
	if world != null:
		world.state_changed.connect(_on_state_changed)
	_refresh()


func value(key: String, default: Variant = null) -> Variant:
	return world.value(fixture_id, key, default) if world != null else default


## Cambia un valor (solo el anfitrión; en los demás no hace nada).
func set_value(key: String, new_value: Variant) -> void:
	if world != null:
		world.set_value(fixture_id, key, new_value)


func set_values(values: Dictionary) -> void:
	if world != null:
		world.set_values(fixture_id, values)


func is_authority() -> bool:
	return multiplayer.is_server()


## Pinta la cosa según su estado. Lo sobrescribe cada clase.
func _refresh() -> void:
	pass


## Hace que [param body] se pueda usar con F ([param verb]: "usar" o "mirar").
## Al usarlo se pide al anfitrión ([method request_use]), salvo "mirar", que es
## de cada uno ([method _on_looked]).
func add_use(body: Node, verb: StringName = &"usar", action: StringName = &"") -> Interactable:
	var interactable: Interactable = Interactable.new()
	interactable.name = "Uso" if action.is_empty() else "Uso_" + String(action)
	interactable.verb = verb
	body.add_child(interactable)
	interactable.interacted.connect(
		func(player: Node) -> void:
			if verb == &"mirar":
				_on_looked(player)
			else:
				request_use.rpc_id(Carryable.HOST_PEER, action)
	)
	return interactable


## Hace que [param body] se pueda trabajar con [param tools] y [param gesture];
## en el anfitrión, lo trabajado llega a [method _on_worked].
func add_work(
	body: Node, tools: Array, gesture: Workable.Gesture, work_name: String = ""
) -> Workable:
	var workable: Workable = Workable.new()
	workable.name = work_name if not work_name.is_empty() else "Trabajo_%d" % body.get_child_count()
	for tool: Variant in tools:
		workable.tools.append(StringName(tool))
	workable.gesture = gesture
	body.add_child(workable)
	workables.append(workable)
	workable.worked.connect(
		func(player: Node, tool: StringName, amount: float, point: Vector3) -> void:
			_on_worked(player as Player, tool, amount, point)
	)
	return workable


## Un área que solo sirve para alcanzar algo con la mirada (una mancha del
## suelo, la bombilla, la llave de la pila): no choca con nada.
func add_reach_area(shape: Shape3D, where: Vector3, area_name: String = "Alcance") -> Area3D:
	var area: Area3D = Area3D.new()
	area.name = area_name
	area.collision_layer = REACH_LAYER
	area.collision_mask = 0
	area.monitoring = false
	area.monitorable = true
	area.position = where
	var collision: CollisionShape3D = CollisionShape3D.new()
	collision.shape = shape
	area.add_child(collision)
	add_child(area)
	return area


## Un jugador usa esto. Decide el anfitrión.
@rpc("any_peer", "call_local", "reliable")
func request_use(action: StringName) -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	var player: Player = Player.find(get_tree(), sender)
	if player != null:
		_on_used(player, action)


## En el anfitrión: un jugador lo ha usado (F).
func _on_used(_player: Player, _action: StringName) -> void:
	pass


## En el anfitrión: un jugador lo ha trabajado con algo en la mano.
func _on_worked(_player: Player, _tool: StringName, _amount: float, _point: Vector3) -> void:
	pass


## En el equipo de quien mira: lo quiere ver de cerca.
func _on_looked(_player: Node) -> void:
	pass


## Los objetos sueltos de la escena (para quitar lo que se gasta o dar algo).
func world_items() -> WorldItems:
	return (
		get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
		if is_inside_tree()
		else null
	)


## Quita lo que lleva [param player] en las manos (se gasta). Solo el anfitrión.
func consume_held(player: Player) -> void:
	var held: Carryable = player.held_item()
	var items: WorldItems = world_items()
	if held != null and items != null:
		items.remove_item(held)


func _on_state_changed(id: String) -> void:
	if id == fixture_id:
		_refresh()
		refreshed.emit()
