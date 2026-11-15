class_name KitRules
extends RefCounted
## Lo común de las reglas del kit de arquitectura (KitPanelBlock, KitMasonry): la ficha, el
## azar con semilla, el marco de cada pieza, los estados de las ventanas y el hollín.
##
## Todo lo que varía sale de [member _rng], sembrado con la clave del edificio: el mismo
## edificio sale siempre igual mientras las reglas pidan las cosas en el mismo orden.

## Probabilidad de que un balcón se haya caído, por nivel de daño.
const FALLEN_BALCONY: Array[float] = [0.0, 0.07, 0.18, 0.4, 0.55]

var spec: Dictionary
var assembly: KitAssembly
var kind: String
var key: String
var floors: int
var damage: int

var _rng: RandomNumberGenerator = RandomNumberGenerator.new()
var _origin: Vector2
var _bomb: Vector2
var _wear: float


func _init(building: Dictionary, kit_assembly: KitAssembly) -> void:
	spec = building
	assembly = kit_assembly
	kind = spec["tipo"]
	key = String(spec.get("clave", kind))
	damage = clampi(int(spec.get("dano", 1)), 1, 4)
	_rng.seed = hash(key)
	_bomb = spec.get("bomba", Vector2(1.0e5, 1.0e5))


## El marco de una pieza: x a lo largo de la fachada, y arriba y z hacia fuera.
## [param face] lleva "start", "direction" y "scale" (y, si se da, "scale_y").
func _frame(face: Dictionary, height: float) -> Transform3D:
	var direction: Vector2 = face["direction"]
	var x_axis: Vector3 = Vector3(direction.x, 0.0, -direction.y)
	var outward: Vector3 = Vector3(direction.y, 0.0, direction.x)
	var up: Vector3 = Vector3.UP * float(face.get("scale_y", 1.0))
	return Transform3D(
		Basis(x_axis * float(face["scale"]), up, outward), _local(face["start"], height)
	)


## El estado de una ventana: los cristales que quedan según el daño y si mira a la bomba.
func _window_state(f: int, facing: bool) -> String:
	if damage >= 3:
		return _weighted({"rota": 0.25, "vacia": 0.6, "quemada": 0.15})
	if f == 0 and _rng.randf() < 0.45:
		return "tapiada"
	var weights: Dictionary = {
		"intacta": 0.32,
		"cortina": 0.12,
		"rota": 0.3,
		"vacia": 0.1,
		"tapiada": 0.08,
		"plastico": 0.05
	}
	if damage == 2:
		weights = {
			"intacta": 0.12,
			"cortina": 0.05,
			"rota": 0.4,
			"vacia": 0.31,
			"tapiada": 0.07,
			"plastico": 0.04
		}
	var state: String = _weighted(weights)
	if facing and state in ["intacta", "cortina"] and _rng.randf() < 0.6:
		state = "rota"
	return state


## Las carpinterías pequeñas tienen menos estados que las ventanas.
func _short_state(state: String) -> String:
	return {"cortina": "intacta", "plastico": "tapiada"}.get(state, state)


## Los huecos de escalera no se tapian ni se cubren con plástico.
func _stair_state(state: String) -> String:
	return {"cortina": "intacta", "tapiada": "rota", "plastico": "rota"}.get(state, state)


func _door_state() -> String:
	if damage >= 3:
		return _pick(["arrancada", "abierta"])
	return _weighted({"cerrada": 0.3, "abierta": 0.3, "tapiada": 0.25, "arrancada": 0.15})


## El hollín de la ventana de abajo, visto desde una pieza [param rise] metros más arriba.
func _from_below(below: Color, rise: float) -> Color:
	if below.g <= 0.0:
		return Color(_wear, 0.0, 0.0, 0.0)
	return Color(_wear, below.g, below.b, below.a - rise)


func _pick(options: Array) -> String:
	return options[_rng.randi() % options.size()]


func _pick_color(options: Array[Color]) -> Color:
	return options[_rng.randi() % options.size()]


func _weighted(weights: Dictionary) -> String:
	var total: float = 0.0
	for option: String in weights:
		total += float(weights[option])
	var r: float = _rng.randf() * total
	for option: String in weights:
		r -= float(weights[option])
		if r <= 0.0:
			return option
	return weights.keys()[weights.size() - 1]


func _local(point: Vector2, height: float) -> Vector3:
	return Vector3(point.x - _origin.x, height, _origin.y - point.y)
