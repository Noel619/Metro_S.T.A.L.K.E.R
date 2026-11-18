class_name SinkFixture
extends Fixture
## La pila de descontaminación (F2-06): F en la llave abre o cierra el agua.
## Mientras corre, lo que hay dentro de la cubeta pierde contaminación; con el
## cepillo se frota (más y más deprisa: lo hace [DepotDecon]).

## Contaminación que quita el agua por segundo.
const WATER_RATE: float = 0.04
## Cada cuánto aplica el anfitrión el agua (segundos).
const TICK: float = 0.5
## La cubeta, en los ejes de la pila: medio ancho, medio fondo y alturas.
const BASIN_HALF: Vector2 = Vector2(0.36, 0.24)
const BASIN_Y: Vector2 = Vector2(0.58, 1.05)
const VALVE_OPEN: float = deg_to_rad(-120.0)

var model: Node3D
var _valve: Node3D
var _water: Node3D
var _valve_angle: float = 0.0
var _tick: float = 0.0
var _water_rest: Vector3 = Vector3.ONE


func _ready() -> void:
	_valve = model.find_child("llave", true, false) as Node3D
	_water = model.find_child("agua", true, false) as Node3D
	if _water != null:
		_water_rest = _water.scale
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = 0.1
	var where: Vector3 = (
		model.global_transform * _valve.position if _valve != null else model.position
	)
	var area: Area3D = add_reach_area(sphere, where, "Llave")
	add_use(area)
	super._ready()
	_valve_angle = VALVE_OPEN if is_running() else 0.0


func is_running() -> bool:
	return bool(value("abierta", false))


## ¿Está [param item] dentro de la cubeta?
func holds(item: Carryable) -> bool:
	if item.is_held():
		return false
	var local: Vector3 = model.global_transform.affine_inverse() * item.body().global_position
	return (
		absf(local.x) < BASIN_HALF.x
		and absf(local.z) < BASIN_HALF.y
		and local.y > BASIN_Y.x
		and local.y < BASIN_Y.y
	)


func _on_used(_player: Player, _action: StringName) -> void:
	set_value("abierta", not is_running())


func _process(delta: float) -> void:
	var target: float = VALVE_OPEN if is_running() else 0.0
	if _valve != null and not is_equal_approx(_valve_angle, target):
		_valve_angle = move_toward(_valve_angle, target, delta * 6.0)
		_valve.rotation.y = _valve_angle
	if _water != null:
		_water.visible = is_running()
		if is_running():
			var t: float = Time.get_ticks_msec() / 1000.0
			_water.scale = _water_rest * Vector3(1.0, 1.0 + sin(t * 9.0) * 0.03, 1.0)
	if not is_running() or not is_authority():
		return
	_tick += delta
	if _tick < TICK:
		return
	_tick = 0.0
	var items: WorldItems = world_items()
	if items == null:
		return
	for item: Carryable in items.items():
		if item.state.contamination > 0.0 and not item.state.bagged and holds(item):
			item.set_values(
				{"contamination": maxf(0.0, item.state.contamination - WATER_RATE * TICK)}
			)
