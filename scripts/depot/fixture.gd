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

@export var fixture_id: String = ""

var world: DepotWorld


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


func _on_state_changed(id: String) -> void:
	if id == fixture_id:
		_refresh()
		refreshed.emit()
