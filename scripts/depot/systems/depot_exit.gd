class_name DepotExit
extends Fixture
## La subida (docs/SUPERFICIE.md, 1): la reja de las escaleras mecánicas, al fondo
## del pasillo, que la guardia abre de 7 a 20, y las escaleras paradas que suben
## hacia la compuerta. Con la reja abierta y todos los jugadores en las escaleras,
## se sube a la superficie.
##
## El modelo de las escaleras no tiene más colisión que la reja: aquí se ponen el
## rellano, la rampa de los peldaños y las balaustradas. Al volver de la superficie
## se aparece delante de la reja, en el pasillo, con la reja cerrada.

const OPEN_FROM: float = 7.0
const OPEN_UNTIL: float = 20.0
## Segundos que tienen que estar todos en las escaleras para subir.
const UP_SECONDS: float = 1.5
## Lo alto que hay que haber subido por las escaleras para que cuente.
const UP_HEIGHT: float = 1.2
## Las escaleras (en el marco del modelo: x hacia arriba, z de lado; ver estacion.py).
const LANDING: float = 1.6
const RUN: float = 13.0
const SLOPE: float = deg_to_rad(30.0)
const SIDE: Vector2 = Vector2(0.8, 5.2)
const BALUSTRADES: Array[float] = [0.8, 2.2, 3.6, 5.0]
## La rampa empieza un poco antes de las escaleras, para salir del rellano sin escalón.
const RAMP_LEAD: float = 0.37
## Al bajar: dónde aparece cada uno, en el pasillo delante de la reja (x y lo que se
## aparta de la fachada de la consigna), de cara al pasillo.
const ARRIVALS: Array[Vector2] = [
	Vector2(13.6, 1.6), Vector2(13.6, 3.0), Vector2(12.8, 2.3), Vector2(12.8, 3.7)
]
const ARRIVAL_YAW: float = PI / 2.0
## Lo que se pliega la reja al abrirse (hacia un lado).
const FOLDED: float = 0.12
const FOLD_SECONDS: float = 1.0

var station: Station

var _origin: Vector3
var _gate: Node3D
var _gate_shape: CollisionShape3D
var _fold: float = 0.0
var _clock: float = 0.0


func _ready() -> void:
	fixture_id = "reja"
	_origin = Station.ESCALATOR
	_find_gate()
	_build_collision()
	_build_sign()
	super._ready()


## Dónde aparece el jugador del puesto [param slot] al volver de la superficie.
static func arrival(slot: int) -> Vector3:
	var spot: Vector2 = ARRIVALS[slot % ARRIVALS.size()]
	return Vector3(spot.x, 0.03, Station.FRONT + spot.y)


## La guardia deja pasar a esta hora.
static func open_hours(hour: float) -> bool:
	return hour >= OPEN_FROM and hour < OPEN_UNTIL


func is_open() -> bool:
	return bool(value("abierta", false))


func _process(delta: float) -> void:
	_fold = move_toward(_fold, 1.0 if is_open() else 0.0, delta / FOLD_SECONDS)
	if _gate != null:
		# La reja se pliega hacia el lado del pasillo de la consigna (z pequeña).
		_gate.scale = Vector3(1.0, 1.0, lerpf(1.0, FOLDED, _fold))
	if _gate_shape != null:
		_gate_shape.disabled = _fold > 0.5
	if is_authority():
		_watch(delta)


func _on_used(_player: Player, _action: StringName) -> void:
	if is_open():
		set_value("abierta", false)
	elif open_hours(GameState.hour()):
		set_value("abierta", true)


## En el anfitrión: con la reja abierta y todos en las escaleras, se sube. Y a las
## 20, la guardia cierra.
func _watch(delta: float) -> void:
	if is_open() and not open_hours(GameState.hour()):
		set_value("abierta", false)
	var everyone: Array[Node] = get_tree().get_nodes_in_group(Player.GROUP)
	var up: bool = is_open() and not everyone.is_empty()
	for node: Node in everyone:
		if not on_stairs((node as Player).global_position):
			up = false
			break
	_clock = _clock + delta if up else 0.0
	if _clock >= UP_SECONDS:
		_clock = -INF
		set_value("abierta", false)
		Sortie.travel(get_tree(), false)


## Está subiendo por las escaleras (y ya ha subido algo).
func on_stairs(position: Vector3) -> bool:
	var local: Vector3 = position - _origin
	return (
		local.x > LANDING
		and local.x < LANDING + RUN
		and local.z > SIDE.x
		and local.z < SIDE.y
		and local.y > UP_HEIGHT
	)


func _find_gate() -> void:
	var model: Node = station.find_child("escalera_mecanica", true, false) if station else null
	if model == null:
		return
	var body: StaticBody3D = model.find_child("escalera_mecanica", true, false) as StaticBody3D
	if body == null and model is StaticBody3D:
		body = model as StaticBody3D
	if body == null:
		return
	_gate = body.find_child("reja", true, false) as Node3D
	_gate_shape = body.find_child("reja_colision", true, false) as CollisionShape3D
	add_use(body, &"usar")


## El rellano, la rampa de los peldaños (por las narices) y las balaustradas.
func _build_collision() -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Escaleras"
	body.position = _origin
	add_child(body)
	var width: float = SIDE.y - SIDE.x
	var middle: float = (SIDE.x + SIDE.y) / 2.0
	_box(body, Vector3(LANDING + 0.2, 0.2, width), Vector3(LANDING / 2.0, -0.08, middle))
	# Las narices de los peldaños: a 0,23 m al empezar y subiendo a 30°.
	var rise: float = tan(SLOPE)
	var first_nose: float = 0.4 * rise
	var start: float = LANDING - RAMP_LEAD
	var center_x: float = (start + LANDING + RUN) / 2.0
	var length: float = (LANDING + RUN - start) / cos(SLOPE)
	var tilt: Basis = Basis(Vector3.BACK, SLOPE)
	var surface: float = first_nose + (center_x - LANDING) * rise
	var center: Vector3 = Vector3(center_x, surface, middle) + tilt * Vector3(0.0, -0.1, 0.0)
	_box(body, Vector3(length, 0.2, width), center, tilt)
	for z: float in BALUSTRADES:
		var rail: Vector3 = center + tilt * Vector3(0.0, 0.55, 0.0)
		_box(body, Vector3(length, 0.9, 0.26), Vector3(rail.x, rail.y, z), tilt)
	for z: float in [SIDE.x - 0.25, SIDE.y + 0.25]:
		_box(body, Vector3(LANDING + RUN, 8.0, 0.3), Vector3((LANDING + RUN) / 2.0, 3.0, z))


func _box(body: StaticBody3D, size: Vector3, center: Vector3, turn: Basis = Basis()) -> void:
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	shape.transform = Transform3D(turn, center)
	body.add_child(shape)


## El cartel de la guardia, en el muro junto a la reja.
func _build_sign() -> void:
	var paper: Dictionary = PaperCard.note(
		["*SALIDA A LA SUPERFICIE", "Se abre de 7 a 20.", "Gobierno civil"], 0.3
	)
	var card: PaperCard = PaperCard.create(paper)
	card.name = "Cartel"
	card.position = _origin + Vector3(-0.03, 1.5, 5.6)
	card.rotation_degrees = Vector3(0.0, -90.0, 0.0)
	add_child(card)
