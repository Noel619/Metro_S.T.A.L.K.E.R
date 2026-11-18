class_name DoorFixture
extends Fixture
## La puerta de chapa de la consigna, al pasillo: se abre y se cierra con F.
## Gira hacia dentro, sobre sus bisagras.

const OPEN_ANGLE: float = deg_to_rad(-100.0)
const SPEED: float = 2.4

var model: Node3D
var _leaf: Node3D
var _angle: float = 0.0


func _ready() -> void:
	_leaf = model.find_child("hoja", true, false) as Node3D
	add_use(_leaf)
	super._ready()
	_angle = OPEN_ANGLE if is_open() else 0.0
	_leaf.rotation.y = _angle


func is_open() -> bool:
	return bool(value("abierta", false))


func _on_used(_player: Player, _action: StringName) -> void:
	set_value("abierta", not is_open())


func _process(delta: float) -> void:
	var target: float = OPEN_ANGLE if is_open() else 0.0
	if not is_equal_approx(_angle, target):
		_angle = move_toward(_angle, target, SPEED * delta)
		_leaf.rotation.y = _angle
