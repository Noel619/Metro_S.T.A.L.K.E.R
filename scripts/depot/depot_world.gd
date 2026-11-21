class_name DepotWorld
extends Node
## El estado de las cosas fijas del depósito y del trozo de estación: cada
## mancha de polvo, cada telaraña, la bombilla, la persiana, la estufa… Cada
## cosa ([Fixture]) tiene su identificador y un diccionario de valores.
##
## Lo cambia el anfitrión, que lo manda a todos (también a quien llega tarde),
## y se guarda con la partida. Lo que no se ha tocado no está: cada cosa sabe
## cómo es al principio.

## Ha cambiado el estado de la cosa [param id].
signal state_changed(id: String)

const GROUP: StringName = &"depot_world"
const SAVE_KEY: String = "deposito"

## Con qué clave se guarda (la superficie tiene el suyo: "superficie").
var save_key: String = SAVE_KEY

var _states: Dictionary = {}


## El de la escena de [param node].
static func find(node: Node) -> DepotWorld:
	if node == null or not node.is_inside_tree():
		return null
	return node.get_tree().get_first_node_in_group(GROUP) as DepotWorld


func _enter_tree() -> void:
	add_to_group(GROUP)
	SaveSystem.register_provider(save_key, self)


func _ready() -> void:
	NetSession.peer_joined.connect(_on_peer_joined)


func _exit_tree() -> void:
	SaveSystem.unregister_provider(save_key)


func state_of(id: String) -> Dictionary:
	return _states.get(id, {})


func value(id: String, key: String, default: Variant = null) -> Variant:
	return state_of(id).get(key, default)


## Cambia un valor de una cosa. Solo el anfitrión: lo manda a todos.
func set_value(id: String, key: String, new_value: Variant) -> void:
	set_values(id, {key: new_value})


## Cambia varios valores a la vez.
func set_values(id: String, values: Dictionary) -> void:
	if not multiplayer.is_server():
		return
	var state: Dictionary = state_of(id).duplicate(true)
	var changed: bool = false
	for key: String in values:
		if not state.has(key) or state[key] != values[key]:
			state[key] = values[key]
			changed = true
	if changed:
		_apply.rpc(id, state)


## Todos los identificadores con estado.
func ids() -> PackedStringArray:
	return PackedStringArray(_states.keys())


func save_state() -> Dictionary:
	return {"estados": _states.duplicate(true)}


func load_state(data: Dictionary) -> void:
	var loaded: Variant = data.get("estados", {})
	_replace((loaded as Dictionary).duplicate(true) if loaded is Dictionary else {})
	if multiplayer.is_server() and multiplayer.get_peers().size() > 0:
		_receive_all.rpc(_states)


@rpc("authority", "call_local", "reliable")
func _apply(id: String, state: Dictionary) -> void:
	_states[id] = state
	state_changed.emit(id)


@rpc("authority", "call_remote", "reliable")
func _receive_all(states: Dictionary) -> void:
	_replace(states)


## Cambia todo el estado de golpe y avisa a cada cosa que tenía o tiene estado
## (lo que deja de tenerlo vuelve a como era al principio).
func _replace(states: Dictionary) -> void:
	var touched: Array = _states.keys()
	_states = states
	for id: String in _states:
		if not touched.has(id):
			touched.append(id)
	for id: String in touched:
		state_changed.emit(id)


func _on_peer_joined(peer_id: int) -> void:
	if multiplayer.is_server():
		_receive_all.rpc_id(peer_id, _states)
