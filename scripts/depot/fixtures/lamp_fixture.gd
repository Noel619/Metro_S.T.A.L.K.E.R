class_name LampFixture
extends Fixture
## La lámpara del mostrador (F2-05): tiene la bombilla fundida. Con la mano se
## desenrosca (círculos al revés del reloj) y cae; con la bombilla nueva en la
## mano se enrosca (círculos en el sentido del reloj) y da luz. La lámpara se
## balancea mientras se trabaja.

## Vueltas para desenroscar o enroscar la bombilla.
const TURNS: float = 1.5
const SWING_DAMP: float = 1.6

## La lámpara colocada y su luz.
var model: Node3D
var light: OmniLight3D
var _bulb: MeshInstance3D
var _bulb_center: Vector3 = Vector3.ZERO
var _hands: Workable
var _new_bulb: Workable
var _lit: Material
var _unlit: Material
var _swing: float = 0.0
var _swing_speed: float = 0.0
var _last_progress: float = 0.0


func _ready() -> void:
	_bulb = model.find_child("bombilla", true, false) as MeshInstance3D
	_bulb_center = _bulb.get_aabb().get_center() if _bulb != null else Vector3(0, -0.8, 0)
	_unlit = _bulb.get_active_material(0) if _bulb != null else null
	_lit = load("res://assets/materials/bombilla.tres")
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = 0.2
	var area: Area3D = add_reach_area(sphere, model.position + _bulb_center, "Bombilla")
	_hands = add_work(area, [Workable.HANDS], Workable.Gesture.CIRCLE, "Desenroscar")
	_new_bulb = add_work(area, [&"bombilla"], Workable.Gesture.CIRCLE, "Enroscar")
	super._ready()


## "fundida", "ninguna" o "buena".
func bulb() -> String:
	return str(value("bombilla", "fundida"))


func is_lit() -> bool:
	return bulb() == "buena"


func _on_worked(player: Player, tool: StringName, amount: float, _point: Vector3) -> void:
	var progress: float = float(value("avance", 0.0))
	if tool == Workable.HANDS and bulb() == "fundida" and amount < 0.0:
		progress += -amount / TURNS
		if progress >= 1.0:
			set_values({"bombilla": "ninguna", "avance": 0.0})
			var items: WorldItems = world_items()
			if items != null:
				var where: Vector3 = model.global_transform * _bulb_center
				items.spawn_item(&"bombilla_fundida", Transform3D(Basis.IDENTITY, where))
			return
		set_value("avance", progress)
	elif tool == &"bombilla" and bulb() == "ninguna" and amount > 0.0:
		progress += amount / TURNS
		if progress >= 1.0:
			consume_held(player)
			set_values({"bombilla": "buena", "avance": 0.0})
			return
		set_value("avance", progress)


func _refresh() -> void:
	var state: String = bulb()
	_hands.enabled = state == "fundida"
	_new_bulb.enabled = state == "ninguna"
	if light != null:
		light.visible = state == "buena"
	if _bulb != null:
		_bulb.visible = state != "ninguna"
		_bulb.set_surface_override_material(0, _lit if state == "buena" else _unlit)
		# Mientras se enrosca o se desenrosca, la bombilla gira.
		var progress: float = float(value("avance", 0.0))
		if not is_equal_approx(progress, _last_progress):
			_swing_speed += 0.5
		_last_progress = progress


func _process(delta: float) -> void:
	if absf(_swing) < 0.0005 and absf(_swing_speed) < 0.0005:
		return
	# Un péndulo: la lámpara cuelga del techo y se mece al tocarla.
	_swing_speed += -_swing * 9.0 * delta
	_swing_speed *= exp(-SWING_DAMP * delta)
	_swing += _swing_speed * delta
	model.rotation.x = _swing * 0.12
	model.rotation.z = _swing * 0.07
