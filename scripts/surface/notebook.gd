class_name Notebook
extends RefCounted
## El cuaderno de un jugador (F3-04, docs/SUPERFICIE.md 5): veinticuatro páginas
## cuadriculadas con lo que se ha dibujado en ellas. Solo datos: los trazos son
## vectores (listas de puntos de la página, de 0 a 1, alisados y aligerados), los sellos
## y las notas, un sitio y su texto. Se guarda y se replica dentro del estado de la
## partida ([member GameState.notebooks]) y lo cambia el anfitrión ([PlayerNotebook]).
## Si mueres, se pierde contigo.

const PAGES: int = 24
## Los lápices: el de grafito y los de colores (rojo, azul y verde).
const INKS: Array[Color] = [Color("#3a3a3e"), Color("#a8392d"), Color("#2f4a86"), Color("#3c6a3a")]
const INK_NAMES: PackedStringArray = ["lápiz", "rojo", "azul", "verde"]
## Los sellos: peligro, entrada, botín, radiación, refugio, perro y el reloj (que escribe
## la hora que marca el tuyo).
const STAMPS: PackedStringArray = [
	"peligro", "entrada", "botin", "radiacion", "refugio", "perro", "reloj"
]
const CLOCK_STAMP: String = "reloj"
## Lo que cabe en una página, como mucho (la partida no crece sin fin).
const MAX_STROKES: int = 300
const MAX_POINTS: int = 400
const MAX_NOTE: int = 60
## Al guardar un trazo se quitan los puntos que no cambian su forma (en página).
const SIMPLIFY: float = 0.0015

## Cada página: {"trazos": [{"c": tinta, "p": [u, v, u, v…]}], "sellos": [{"s", "u", "v",
## "t"}], "notas": [{"u", "v", "t"}]}.
var pages: Array[Dictionary] = []


func _init() -> void:
	for _index: int in PAGES:
		pages.append(_empty_page())


## Añade un trazo de la tinta [param ink] a la página [param page]. Devuelve si cabía.
func add_stroke(page: int, ink: int, points: PackedVector2Array) -> bool:
	if not _valid(page) or points.size() < 2:
		return false
	var strokes: Array = pages[page]["trazos"]
	if strokes.size() >= MAX_STROKES:
		return false
	var light: PackedVector2Array = simplify(points, SIMPLIFY)
	var flat: Array = []
	for index: int in mini(light.size(), MAX_POINTS):
		var point: Vector2 = light[index].clamp(Vector2.ZERO, Vector2.ONE)
		flat.append(snappedf(point.x, 0.0005))
		flat.append(snappedf(point.y, 0.0005))
	strokes.append({"c": clampi(ink, 0, INKS.size() - 1), "p": flat})
	return true


## Borra de la página [param page] lo que la goma toca en [param point] (con su
## [param radius]): los trazos, los sellos y las notas. Devuelve cuántas cosas.
func erase_near(page: int, point: Vector2, radius: float) -> int:
	if not _valid(page):
		return 0
	var removed: int = 0
	for key: String in ["trazos", "sellos", "notas"]:
		var kept: Array = []
		for entry: Dictionary in pages[page][key]:
			if _touches(entry, point, radius):
				removed += 1
			else:
				kept.append(entry)
		pages[page][key] = kept
	return removed


## Estampa el sello [param stamp] en [param at] (con su texto: la hora del reloj).
func add_stamp(page: int, stamp: String, at: Vector2, text: String = "") -> bool:
	if not _valid(page) or not STAMPS.has(stamp):
		return false
	var stamps: Array = pages[page]["sellos"]
	if stamps.size() >= MAX_STROKES:
		return false
	stamps.append({"s": stamp, "u": at.x, "v": at.y, "t": text.left(MAX_NOTE)})
	return true


## Escribe una nota en [param at].
func add_note(page: int, at: Vector2, text: String) -> bool:
	var clean: String = text.strip_edges().left(MAX_NOTE)
	if not _valid(page) or clean.is_empty():
		return false
	var notes: Array = pages[page]["notas"]
	if notes.size() >= MAX_STROKES:
		return false
	notes.append({"u": at.x, "v": at.y, "t": clean})
	return true


## Los puntos de un trazo guardado.
static func points_of(stroke: Dictionary) -> PackedVector2Array:
	var flat: Array = stroke.get("p", [])
	var result: PackedVector2Array = PackedVector2Array()
	for index: int in range(0, flat.size() - 1, 2):
		result.append(Vector2(float(flat[index]), float(flat[index + 1])))
	return result


## Está en blanco (todas sus páginas).
func is_empty() -> bool:
	for page: Dictionary in pages:
		for key: String in ["trazos", "sellos", "notas"]:
			if not (page[key] as Array).is_empty():
				return false
	return true


## La hora del sello del reloj: "visto a las 14:20".
static func clock_text(minute: float) -> String:
	var total: int = int(minute)
	return "visto a las %02d:%02d" % [int(total / 60.0) % 24, total % 60]


## Aligera una línea (Ramer-Douglas-Peucker): quita los puntos a menos de
## [param tolerance] de la recta entre sus vecinos.
static func simplify(points: PackedVector2Array, tolerance: float) -> PackedVector2Array:
	if points.size() < 3:
		return points
	var keep: Array[bool] = []
	keep.resize(points.size())
	keep.fill(false)
	keep[0] = true
	keep[points.size() - 1] = true
	var stack: Array[Vector2i] = [Vector2i(0, points.size() - 1)]
	while not stack.is_empty():
		var span: Vector2i = stack.pop_back()
		var farthest: int = -1
		var distance: float = tolerance
		for index: int in range(span.x + 1, span.y):
			var gap: float = _segment_distance(points[index], points[span.x], points[span.y])
			if gap > distance:
				distance = gap
				farthest = index
		if farthest >= 0:
			keep[farthest] = true
			stack.append(Vector2i(span.x, farthest))
			stack.append(Vector2i(farthest, span.y))
	var result: PackedVector2Array = PackedVector2Array()
	for index: int in points.size():
		if keep[index]:
			result.append(points[index])
	return result


func to_dict() -> Dictionary:
	return {"paginas": pages.duplicate(true)}


static func from_dict(data: Dictionary) -> Notebook:
	var notebook: Notebook = Notebook.new()
	var saved: Variant = data.get("paginas", [])
	if not saved is Array:
		return notebook
	for index: int in mini((saved as Array).size(), PAGES):
		var page: Variant = saved[index]
		if not page is Dictionary:
			continue
		for key: String in ["trazos", "sellos", "notas"]:
			var entries: Variant = (page as Dictionary).get(key, [])
			if entries is Array:
				notebook.pages[index][key] = (entries as Array).duplicate(true)
	return notebook


func _valid(page: int) -> bool:
	return page >= 0 and page < PAGES


func _touches(entry: Dictionary, point: Vector2, radius: float) -> bool:
	if entry.has("p"):
		var line: PackedVector2Array = points_of(entry)
		if line.size() == 1:
			return line[0].distance_to(point) <= radius
		for index: int in line.size() - 1:
			if _segment_distance(point, line[index], line[index + 1]) <= radius:
				return true
		return false
	return (
		Vector2(float(entry.get("u", -1.0)), float(entry.get("v", -1.0))).distance_to(point)
		<= (radius + 0.02)
	)


static func _empty_page() -> Dictionary:
	return {"trazos": [], "sellos": [], "notas": []}


static func _segment_distance(point: Vector2, a: Vector2, b: Vector2) -> float:
	return point.distance_to(Geometry2D.get_closest_point_to_segment(point, a, b))
