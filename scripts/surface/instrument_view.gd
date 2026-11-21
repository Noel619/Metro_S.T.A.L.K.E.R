class_name InstrumentView
extends Node3D
## Los instrumentos que se leen en la mano (F3-05, docs/SUPERFICIE.md 4.2), en todos los
## equipos:
## - La brújula: la aguja busca el norte de verdad (el -Z del mundo), con su inercia.
## - El podómetro: en la ventanilla, los pasos de quien lo lleva desde que lo puso a
##   cero (mantener el botón izquierdo con él en la mano).
##
## Cuelga del nodo "Visual" del objeto, como [ItemView].

const NEEDLE_SPRING: float = 40.0
const NEEDLE_DAMP: float = 5.0
const DIGITS: int = 5

var item: Carryable

var _needle: Node3D
var _needle_speed: float = 0.0
var _counter: Label3D


func _ready() -> void:
	if not item.is_node_ready():
		await item.ready
	var tool: StringName = item.state.data.tool
	if tool == &"brujula":
		_needle = item.visual().find_child("aguja", true, false) as Node3D
	elif tool == &"podometro":
		var window: Node3D = item.visual().find_child("ventana", true, false) as Node3D
		_counter = Label3D.new()
		_counter.name = "Cifras"
		_counter.font = UiFonts.get_font(&"maquina")
		_counter.font_size = 48
		_counter.pixel_size = 0.00012
		_counter.modulate = Color("#e9e2cc")
		_counter.outline_size = 0
		_counter.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
		_counter.position = (window.position if window != null else Vector3(0.0, 0.0175, -0.004))
		_counter.position.y += 0.0004
		add_child(_counter)


func _process(delta: float) -> void:
	if _needle != null:
		_point_north(delta)
	if _counter != null:
		_counter.text = String.num_int64(steps()).pad_zeros(DIGITS).right(DIGITS)


## Los pasos que marca el podómetro: los de quien lo lleva, desde la última puesta a cero.
func steps() -> int:
	var holder: Player = Player.find(get_tree(), item.holder_peer) if item.is_held() else null
	if holder == null:
		return int(item.state.extra.get("marca", 0))
	return maxi(0, holder.footsteps.steps - int(item.state.extra.get("base", 0)))


func _point_north(delta: float) -> void:
	# La aguja gira sobre el eje de la caja; su norte, en reposo, es el -Z de la caja.
	var parent: Node3D = _needle.get_parent() as Node3D
	var north_local: Vector3 = parent.global_basis.inverse() * Vector3.FORWARD
	var wanted: float = atan2(-north_local.x, -north_local.z)
	var error: float = wrapf(wanted - _needle.rotation.y, -PI, PI)
	_needle_speed += error * NEEDLE_SPRING * delta
	_needle_speed *= exp(-NEEDLE_DAMP * delta)
	_needle.rotation.y += _needle_speed * delta
