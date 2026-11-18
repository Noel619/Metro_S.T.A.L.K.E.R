class_name ShutterFixture
extends Fixture
## La persiana de la ventanilla (F2-05): el primer día está atascada. Se
## desatasca con la palanca (tirando hacia abajo); después sube y baja con F.
## Con ella subida, el mostrador está abierto y vienen clientes (F2-09).
##
## Las lamas suben de verdad: la cortina se mueve y las que entran en el cajón
## se ocultan. Atascada, tiembla al tocarla.

## Lo que mide el hueco (lo que sube la cortina para quedar abierta).
const HEIGHT: float = 2.3
## Lo que sube o baja por segundo (en partes del recorrido).
const SPEED: float = 0.5
## Tirones de palanca para desatascarla (unidades del gesto PULL).
const UNJAM_WORK: float = 3.0

## El modelo colocado ("Persiana", con su "cortina").
var model: Node3D
var _curtain: StaticBody3D
var _slats: Array[MeshInstance3D] = []
var _slat_tops: Array[float] = []
var _shown: float = 0.0
var _shake: float = 0.0
var _rest_x: float = 0.0


func _ready() -> void:
	_curtain = model.find_child("cortina", true, false) as StaticBody3D
	_rest_x = _curtain.position.x
	for node: Node in _curtain.get_children():
		var slat: MeshInstance3D = node as MeshInstance3D
		if slat != null and String(slat.name).begins_with("lama_"):
			_slats.append(slat)
			_slat_tops.append(slat.get_aabb().end.y)
	add_use(_curtain)
	add_work(_curtain, [&"palanca"], Workable.Gesture.PULL, "Palanca")
	super._ready()
	_shown = 1.0 if is_open() else 0.0
	_apply()


func is_jammed() -> bool:
	return bool(value("atascada", true))


func is_open() -> bool:
	return bool(value("abierta", false))


## Lo que se ve subida (de 0, cerrada, a 1, arriba del todo).
func shown() -> float:
	return _shown


func _on_used(_player: Player, _action: StringName) -> void:
	if is_jammed():
		# Atascada: solo tiembla.
		set_value("golpes", int(value("golpes", 0)) + 1)
		return
	set_value("abierta", not is_open())


func _on_worked(_player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	if not is_jammed() or amount <= 0.0:
		return
	var progress: float = float(value("palanca", 0.0)) + amount / UNJAM_WORK
	if progress >= 1.0:
		set_values({"atascada": false, "palanca": 1.0, "abierta": false})
	else:
		set_value("palanca", progress)


func _refresh() -> void:
	_shake = 1.0


func _process(delta: float) -> void:
	var target: float = 1.0 if is_open() else 0.0
	if not is_equal_approx(_shown, target) or _shake > 0.0:
		_shown = move_toward(_shown, target, SPEED * delta)
		_shake = maxf(0.0, _shake - delta * 2.5)
		_apply()


func _apply() -> void:
	var lift: float = _shown * HEIGHT
	var wobble: float = sin(Time.get_ticks_msec() * 0.06) * 0.006 * _shake
	_curtain.position = Vector3(_rest_x + wobble, lift, 0.0)
	for index: int in _slats.size():
		_slats[index].visible = _slat_tops[index] + lift <= HEIGHT + 0.06
