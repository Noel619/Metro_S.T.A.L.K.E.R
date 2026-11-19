extends Node3D
## Hoja de revisión del cuaderno (F3-04): el depósito, el jugador con el cuaderno abierto
## y, en la doble página, un mapa de La Plaza dibujado a mano (sale del plano, con el
## pulso de quien dibuja), con sus sellos y sus notas. La cámara es la del jugador.

const LEVEL: String = "res://scenes/depot/deposito.tscn"
## Lo que entra en la hoja de la izquierda, en metros del plano (x al este, y al norte).
const MAP: Rect2 = Rect2(190.0, 20.0, 350.0, 520.0)
const HAND: float = 0.0015
const NOTES: Array = [
	[Vector2(0.62, 0.52), "quioscos: cerillas, latas"],
	[Vector2(0.06, 0.93), "¡perros! (6)"],
	[Vector2(0.5, 0.17), "trasteros: candados"],
	[Vector2(0.2, 0.47), "salida"],
]
const STAMPS: Array = [
	["entrada", Vector2(327.0, 294.0)],
	["botin", Vector2(406.0, 399.0)],
	["botin", Vector2(405.0, 448.0)],
	["perro", Vector2(220.0, 98.0)],
	["perro", Vector2(265.0, 170.0)],
	["refugio", Vector2(526.0, 239.0)],
	["peligro", Vector2(479.0, 340.0)],
]
const DIARY: Array = [
	"Salida 1 — día 3",
	"9:10 subo. La compuerta: una vuelta",
	"La plaza, abierta: no cruzar de día",
	"Por el arco de Juventud 1 al patio",
	"Palomar: escalera. ¿Prismáticos?",
	"La Jauría come en la estación",
	"Flecha de papá: al noreste",
]

@export_enum("chico", "chica") var variant: String = "chico"


func _ready() -> void:
	GameState.protagonist = variant
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	var help: CanvasLayer = level.find_child("Ayuda", false, false) as CanvasLayer
	if help != null:
		help.visible = false
	var player: Player = level.call("local_player")
	var camera: Camera3D = player.find_child("Camara", true, false) as Camera3D
	camera.add_to_group(&"capture_camera")
	await _frames(40)
	GameState.set_notebook(player.slot, sketch(CityPlan.load_default()))
	player.rotation.y = PI * 0.15
	player.head_pitch = -0.15
	player.notebook.toggle(camera)
	await _frames(10)
	if NotebookView.is_open():
		NotebookView.active.cursor = Vector2(1.62, 0.66)


## Un cuaderno con La Plaza dibujada en la hoja de la izquierda y el diario de la salida
## en la de la derecha.
static func sketch(plan: CityPlan) -> Notebook:
	var notebook: Notebook = Notebook.new()
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 7
	if plan != null and plan.is_loaded():
		for building: Dictionary in plan.data["edificios"]:
			var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
			if not MAP.has_point(center):
				continue
			var ring: PackedVector2Array = CityPlan.ring(building["huella"][0])
			var line: PackedVector2Array = PackedVector2Array()
			for point: Vector2 in ring:
				line.append(_on_page(point) + _wobble(rng))
			notebook.add_stroke(0, 0, line)
	for stamp: Array in STAMPS:
		notebook.add_stamp(0, stamp[0], _on_page(stamp[1]))
	for note: Array in NOTES:
		notebook.add_note(0, note[0], note[1])
	# La ruta de la salida, en rojo: del vestíbulo, pegado a la Casa Curva Norte.
	var route: PackedVector2Array = PackedVector2Array()
	for point: Vector2 in [
		Vector2(327, 300), Vector2(350, 340), Vector2(372, 392), Vector2(395, 395)
	]:
		route.append(_on_page(point) + _wobble(rng))
	notebook.add_stroke(0, 1, route)
	for index: int in DIARY.size():
		notebook.add_note(1, Vector2(0.08, 0.1 + index * 0.075), DIARY[index])
	notebook.add_stamp(1, "reloj", Vector2(0.14, 0.72), Notebook.clock_text(14.0 * 60.0 + 20.0))
	notebook.add_stamp(1, "perro", Vector2(0.14, 0.82))
	notebook.add_note(1, Vector2(0.24, 0.835), "seis, guiados por una hembra")
	return notebook


static func _on_page(point: Vector2) -> Vector2:
	return Vector2(
		(point.x - MAP.position.x) / MAP.size.x, 1.0 - (point.y - MAP.position.y) / MAP.size.y
	)


static func _wobble(rng: RandomNumberGenerator) -> Vector2:
	return Vector2(rng.randf_range(-HAND, HAND), rng.randf_range(-HAND, HAND))


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
