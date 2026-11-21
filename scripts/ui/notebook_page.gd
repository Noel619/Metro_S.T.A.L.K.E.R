class_name NotebookPage
extends Node2D
## Una página del cuaderno, dibujada (F3-04): el papel cuadriculado, los trazos de lápiz,
## los sellos y las notas a mano, y lo que se está dibujando ahora (el trazo que sigue al
## lápiz, la regla, la goma o el sello que se va a estampar). Vive en un SubViewport
## cuya textura lleva la hoja del cuaderno 3D ([NotebookView]).

## Lo que mide la página en la textura (136 × 202 mm a 4 px/mm, como la cuadrícula).
const SIZE: Vector2 = Vector2(544.0, 808.0)
const PAPER: Color = Color("#ddd2b6")
const GRID: String = "res://assets/textures/pagina_cuadriculada.png"
## La tinta de los sellos (la de un tampón violeta) y lo que miden.
const STAMP_INK: Color = Color("#4b3f72")
const STAMP_SIZE: float = 34.0
const LINE_WIDTH: float = 2.4
const NOTE_SIZE: int = 30
const ERASER_COLOR: Color = Color(0.3, 0.3, 0.3, 0.5)

## Lo que hay en la página (la de [Notebook]: "trazos", "sellos" y "notas").
var page: Dictionary = {}
## El número de la página (se escribe abajo).
var number: int = 0
## Lo que se está dibujando: el trazo (en página, de 0 a 1) y su tinta; la regla.
var live: PackedVector2Array = PackedVector2Array()
var live_ink: int = 0
var ruler: PackedVector2Array = PackedVector2Array()
## Dónde está el lápiz en esta página (o fuera: x negativa) y con qué.
var cursor: Vector2 = Vector2(-1.0, -1.0)
var cursor_tool: String = ""
var eraser_radius: float = 0.025

var _grid: Texture2D
var _font: Font


func _ready() -> void:
	_grid = load(GRID) if ResourceLoader.exists(GRID) else null
	_font = UiFonts.get_font(&"manuscrita")


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, SIZE), PAPER)
	if _grid != null:
		draw_texture_rect(_grid, Rect2(Vector2.ZERO, SIZE), false, PAPER)
	for stroke: Dictionary in page.get("trazos", []):
		_line(Notebook.points_of(stroke), int(stroke.get("c", 0)))
	for stamp: Dictionary in page.get("sellos", []):
		var at: Vector2 = Vector2(float(stamp.get("u", 0.0)), float(stamp.get("v", 0.0))) * SIZE
		draw_stamp(self, String(stamp.get("s", "")), at, String(stamp.get("t", "")), STAMP_INK)
	for note: Dictionary in page.get("notas", []):
		var at: Vector2 = Vector2(float(note.get("u", 0.0)), float(note.get("v", 0.0))) * SIZE
		draw_string(
			_font,
			at,
			String(note.get("t", "")),
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			NOTE_SIZE,
			Notebook.INKS[0]
		)
	_line(live, live_ink)
	_line(ruler, live_ink, 0.6)
	draw_string(
		_font,
		Vector2(SIZE.x * 0.5 - 8.0, SIZE.y - 18.0),
		str(number + 1),
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		24,
		Color(0.45, 0.42, 0.38)
	)
	_draw_cursor()


## Dibuja el sello [param kind] en [param at] (píxeles de la página) en [param canvas].
static func draw_stamp(
	canvas: CanvasItem, kind: String, at: Vector2, text: String, ink: Color
) -> void:
	var r: float = STAMP_SIZE * 0.5
	match kind:
		"peligro":
			var top: Vector2 = at + Vector2(0.0, -r)
			var left: Vector2 = at + Vector2(-r * 1.05, r * 0.75)
			var right: Vector2 = at + Vector2(r * 1.05, r * 0.75)
			canvas.draw_polyline(PackedVector2Array([top, right, left, top]), ink, 3.0, true)
			canvas.draw_line(
				at + Vector2(0.0, -r * 0.45), at + Vector2(0.0, r * 0.2), ink, 3.0, true
			)
			canvas.draw_circle(at + Vector2(0.0, r * 0.48), 2.2, ink)
		"entrada":
			var door: PackedVector2Array = PackedVector2Array(
				[
					at + Vector2(-r * 0.6, r),
					at + Vector2(-r * 0.6, -r),
					at + Vector2(r * 0.6, -r),
					at + Vector2(r * 0.6, r)
				]
			)
			canvas.draw_polyline(door, ink, 3.0, true)
			canvas.draw_line(
				at + Vector2(-r * 1.4, r * 0.2), at + Vector2(r * 0.1, r * 0.2), ink, 3.0, true
			)
			canvas.draw_polyline(
				PackedVector2Array(
					[
						at + Vector2(-r * 0.25, -r * 0.15),
						at + Vector2(r * 0.1, r * 0.2),
						at + Vector2(-r * 0.25, r * 0.55)
					]
				),
				ink,
				3.0,
				true
			)
		"botin":
			canvas.draw_arc(at, r * 0.85, 0.0, TAU, 24, ink, 3.0, true)
			canvas.draw_line(
				at + Vector2(-r * 0.45, 0.0), at + Vector2(r * 0.45, 0.0), ink, 3.0, true
			)
			canvas.draw_line(
				at + Vector2(0.0, -r * 0.45), at + Vector2(0.0, r * 0.45), ink, 3.0, true
			)
		"radiacion":
			canvas.draw_circle(at, r * 0.18, ink)
			for blade: int in 3:
				var angle: float = -PI * 0.5 + blade * TAU / 3.0
				var points: PackedVector2Array = PackedVector2Array(
					[at + Vector2.from_angle(angle) * r * 0.3]
				)
				for step: int in 7:
					var a: float = angle - 0.5 + step / 6.0
					points.append(at + Vector2.from_angle(a) * r)
				canvas.draw_colored_polygon(points, ink)
		"refugio":
			var house: PackedVector2Array = PackedVector2Array(
				[
					at + Vector2(-r * 0.7, r * 0.8),
					at + Vector2(-r * 0.7, -r * 0.1),
					at + Vector2(0.0, -r * 0.85),
					at + Vector2(r * 0.7, -r * 0.1),
					at + Vector2(r * 0.7, r * 0.8),
					at + Vector2(-r * 0.7, r * 0.8)
				]
			)
			canvas.draw_polyline(house, ink, 3.0, true)
			canvas.draw_rect(
				Rect2(at + Vector2(-r * 0.18, r * 0.3), Vector2(r * 0.36, r * 0.5)), ink
			)
		"perro":
			canvas.draw_circle(at + Vector2(0.0, r * 0.25), r * 0.38, ink)
			for toe: Vector2 in [
				Vector2(-0.55, -0.25), Vector2(-0.2, -0.6), Vector2(0.2, -0.6), Vector2(0.55, -0.25)
			]:
				canvas.draw_circle(at + toe * r, r * 0.17, ink)
		"reloj":
			canvas.draw_arc(at, r * 0.8, 0.0, TAU, 24, ink, 3.0, true)
			canvas.draw_line(at, at + Vector2(0.0, -r * 0.55), ink, 3.0, true)
			canvas.draw_line(at, at + Vector2(r * 0.4, 0.0), ink, 3.0, true)
			if not text.is_empty():
				canvas.draw_string(
					UiFonts.get_font(&"manuscrita"),
					at + Vector2(r * 1.1, r * 0.35),
					text,
					HORIZONTAL_ALIGNMENT_LEFT,
					-1,
					26,
					ink
				)


func _line(points: PackedVector2Array, ink: int, alpha: float = 0.9) -> void:
	if points.size() < 2:
		return
	var scaled: PackedVector2Array = PackedVector2Array()
	for point: Vector2 in points:
		scaled.append(point * SIZE)
	var color: Color = Notebook.INKS[clampi(ink, 0, Notebook.INKS.size() - 1)]
	color.a = alpha
	draw_polyline(scaled, color, LINE_WIDTH, true)


func _draw_cursor() -> void:
	if cursor.x < 0.0:
		return
	var at: Vector2 = cursor * SIZE
	if cursor_tool == "goma":
		draw_arc(at, eraser_radius * SIZE.x, 0.0, TAU, 24, ERASER_COLOR, 1.5, true)
	elif Notebook.STAMPS.has(cursor_tool):
		draw_stamp(self, cursor_tool, at, "", Color(STAMP_INK, 0.35))
