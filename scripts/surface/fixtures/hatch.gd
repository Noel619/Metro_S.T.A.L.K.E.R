class_name Hatch
extends Fixture
## La compuerta blindada de la esclusa del vestíbulo (docs/SUPERFICIE.md, 1): la
## puerta de la salida. Al llegar está cerrada; se abre girando el volante (círculos
## con las manos, botón izquierdo) y se cierra con F. Para volver abajo, todos en la
## esclusa y la compuerta cerrada. Abrirla y cerrarla suena ([constant NOISE]).
##
## Usa la hoja del modelo del vestíbulo (la pieza "vestibulo_compuerta", hecha
## abierta) y la hace girar sobre su bisagra; la colisión es suya, porque la del
## edificio no la lleva.

const NOISE: StringName = &"compuerta"
## Vueltas de volante para abrirla.
const TURNS_TO_OPEN: float = 1.2
## Lo que gira abierta (grados, hacia la sala) y lo que tarda en girar.
const OPEN_DEGREES: float = 95.0
const SWING_SECONDS: float = 1.4
## La hoja, en el marco de la bisagra: grosor, alto y ancho, y su centro.
const LEAF_SIZE: Vector3 = Vector3(0.14, 2.2, 1.6)
const LEAF_CENTER: Vector3 = Vector3(-0.07, 1.1, -0.8)

## Gira la hoja cuando está abierta: sobre esta bisagra, con este rumbo cerrada.
var _closed_yaw: float = 0.0
var _floor: float = 0.0
var _pivot: Node3D
var _angle: float = 0.0


## Monta la compuerta: [param leaf_mesh] es la hoja tal como está en el modelo
## (abierta) y [param model] dónde está puesto el modelo; [param hinge], la
## bisagra en el mundo; [param closed_yaw], el rumbo de la hoja cerrada (radianes);
## [param floor_height], la altura del suelo de la esclusa sobre la bisagra.
func setup(
	leaf_mesh: Mesh, model: Transform3D, hinge: Vector3, closed_yaw: float, floor_height: float
) -> void:
	fixture_id = "compuerta"
	name = "Compuerta"
	_closed_yaw = closed_yaw
	_floor = floor_height
	_pivot = Node3D.new()
	_pivot.name = "Bisagra"
	_pivot.position = hinge
	_pivot.rotation.y = closed_yaw + deg_to_rad(OPEN_DEGREES)
	add_child(_pivot)
	if leaf_mesh != null:
		var leaf: MeshInstance3D = MeshInstance3D.new()
		leaf.name = "Hoja"
		leaf.mesh = leaf_mesh
		# La malla está hecha abierta: se cuelga de la bisagra tal como estaba.
		leaf.transform = _pivot.transform.affine_inverse() * model
		_pivot.add_child(leaf)
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Cuerpo"
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = LEAF_SIZE
	shape.shape = box
	shape.position = LEAF_CENTER + Vector3.UP * floor_height
	body.add_child(shape)
	_pivot.add_child(body)
	add_use(body, &"usar")
	add_work(body, [Workable.HANDS], Workable.Gesture.CIRCLE, "Volante")


func is_open() -> bool:
	return bool(value("abierta", false))


func _process(delta: float) -> void:
	if _pivot == null:
		return
	var target: float = OPEN_DEGREES if is_open() else 0.0
	_angle = move_toward(_angle, target, delta * OPEN_DEGREES / SWING_SECONDS)
	_pivot.rotation.y = _closed_yaw + deg_to_rad(_angle)


## Deja la compuerta abierta o cerrada sin que gire (al llegar).
func snap() -> void:
	_angle = OPEN_DEGREES if is_open() else 0.0
	if _pivot != null:
		_pivot.rotation.y = _closed_yaw + deg_to_rad(_angle)


func _on_used(_player: Player, _action: StringName) -> void:
	if is_open():
		set_values({"abierta": false, "giro": 0.0})
		_sound()


func _on_worked(_player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	if is_open():
		return
	var turned: float = float(value("giro", 0.0)) + absf(amount)
	if turned >= TURNS_TO_OPEN:
		set_values({"abierta": true, "giro": 0.0})
		_sound()
	else:
		set_value("giro", turned)


func _sound() -> void:
	var stimuli: Stimuli = Stimuli.find(get_tree())
	if stimuli != null:
		var center: Vector3 = _pivot.global_position + Vector3.UP * (_floor + 1.1)
		stimuli.make_noise(center, NoiseRules.sound_radius(NOISE), NOISE)
