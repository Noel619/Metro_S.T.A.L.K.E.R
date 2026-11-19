class_name ScaleFixture
extends Node3D
## La báscula del mostrador (F2-08): lo que se deja en los platos mueve la aguja.
## Cada equipo la mueve por su cuenta con lo que ve encima (los objetos ya están
## sincronizados), con inercia: oscila antes de pararse.

## A fondo de escala: el giro de la aguja y los kilos.
const SWEEP: float = deg_to_rad(-64.0)
const FULL_KG: float = 20.0
const SPRING: float = 45.0
const DAMP: float = 5.0
## Los platos, en los ejes de la báscula.
const PAN_SIZE: Vector3 = Vector3(0.72, 0.3, 0.32)
const PAN_CENTER: Vector3 = Vector3(0.0, 0.26, 0.0)

var model: Node3D
var _needle: Node3D
var _area: Area3D
var _angle: float = 0.0
var _speed: float = 0.0


func _ready() -> void:
	_needle = model.find_child("aguja", true, false) as Node3D
	_area = Area3D.new()
	_area.name = "Platos"
	_area.collision_layer = 0
	_area.collision_mask = WorldItems.LAYER_OBJECTS
	_area.monitorable = false
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = PAN_SIZE
	shape.shape = box
	_area.add_child(shape)
	_area.position = PAN_CENTER
	model.add_child(_area)


## Los kilos que hay ahora en los platos (lo que se lleva en la mano no cuenta).
func weight() -> float:
	var total: float = 0.0
	for body: Node3D in _area.get_overlapping_bodies():
		var item: Carryable = body.get_node_or_null(^"Carryable") as Carryable
		if item != null and not item.is_held():
			total += item.state.weight()
	return total


func _physics_process(delta: float) -> void:
	if _needle == null:
		return
	var target: float = SWEEP * clampf(weight() / FULL_KG, 0.0, 1.0)
	_speed += (target - _angle) * SPRING * delta
	_speed *= exp(-DAMP * delta)
	_angle += _speed * delta
	_needle.rotation.z = _angle
