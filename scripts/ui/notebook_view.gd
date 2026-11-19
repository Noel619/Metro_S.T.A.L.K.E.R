class_name NotebookView
extends Node3D
## El cuaderno abierto (F3-04, docs/SUPERFICIE.md 5): lo sujetas delante, con las dos
## manos, y la vista baja a la doble página. Se dibuja con el ratón: un lápiz va por las
## hojas y con el botón izquierdo pinta (de grafito o de color); la rueda cambia a la
## goma, a los lápices de colores y a los sellos (el del reloj escribe la hora que marca
## el tuyo); con el botón derecho pulsado, la regla. T escribe una nota donde está el
## lápiz; A y D pasan las hojas; Tab o Esc lo guardan.
##
## Lo que se ve son las hojas del modelo con la textura de dos SubViewports, cada uno con
## su [NotebookPage]. Hace falta luz para verlas (el papel lo ilumina la escena: de noche,
## la linterna). El miedo hace temblar el trazo. Solo existe en el equipo de quien
## dibuja; lo dibujado se guarda en el estado de la partida ([PlayerNotebook]).

signal closed

const MODEL: String = "res://assets/models/cuaderno_abierto.glb"
const PENCIL: String = "res://assets/models/lapiz.glb"
const PAGE_NODES: PackedStringArray = ["pagina_izquierda", "pagina_derecha"]
## Dónde va, en el marco de la cámara: delante, abajo y girado hacia ti.
const DISTANCE: float = 0.255
const DROP: float = 0.055
const TILT: float = deg_to_rad(62.0)
const RISE_SECONDS: float = 0.35
## El lápiz: lo que mueve cada píxel del ratón (en páginas) y lo que se aleja del papel.
const CURSOR_PER_PIXEL: float = 0.0011
const LIFT: float = 0.002
## Lo que tiene que moverse el lápiz para apuntar otro punto del trazo (en páginas).
const MIN_STEP: float = 0.004
const ERASER_RADIUS: float = 0.025
const ERASE_EVERY: float = 0.1
## El temblor del miedo (en páginas, con el miedo entero).
const TREMBLE: float = 0.006
## Lo que pasa la rueda: el lápiz, la goma, los colores y los sellos.
const PENS: PackedStringArray = ["lapiz", "goma", "rojo", "azul", "verde"]
const PEN_INKS: Dictionary = {"lapiz": 0, "rojo": 1, "azul": 2, "verde": 3}

## El que está abierto (solo hay uno).
static var active: NotebookView = null

var owner_notebook: PlayerNotebook
## Dónde está el lápiz: x de 0 a 2 por la doble página (de 0 a 1, la de la izquierda), y
## de arriba abajo.
var cursor: Vector2 = Vector2(1.5, 0.45)
var tool_index: int = 0
## El trazo que se está haciendo (en su página) y en qué página.
var stroke: PackedVector2Array = PackedVector2Array()
var stroke_page: int = -1
## Donde se empezó la regla (o INF).
var ruler_from: Vector2 = Vector2.INF

var _camera: Camera3D
var _model: Node3D
var _pages: Array[NotebookPage] = []
var _surfaces: Array[MeshInstance3D] = []
var _pencil: Node3D
var _note: LineEdit
var _label: Label
var _layer: CanvasLayer
var _rise: float = 0.0
var _erase_clock: float = 0.0
var _clock: float = 0.0
var _erasing: bool = false


static func is_open() -> bool:
	return active != null and is_instance_valid(active)


## Las herramientas, en el orden de la rueda.
static func tools() -> PackedStringArray:
	var result: PackedStringArray = PENS.duplicate()
	result.append_array(Notebook.STAMPS)
	return result


## Abre el cuaderno de [param notebook] delante de [param camera].
func open(notebook: PlayerNotebook, camera: Camera3D) -> void:
	owner_notebook = notebook
	_camera = camera
	name = "CuadernoAbierto"
	active = self
	camera.add_child(self)
	_build()
	owner_notebook.changed.connect(_refresh)
	_refresh()
	_place(0.0)


func close() -> void:
	if active == self:
		active = null
	if stroke.size() >= 2:
		_finish_stroke()
	if _layer != null:
		_layer.queue_free()
	closed.emit()
	queue_free()


func _exit_tree() -> void:
	if active == self:
		active = null


## La herramienta de ahora.
func tool() -> String:
	return tools()[tool_index]


## La página que hay bajo el lápiz (su número) y dónde, en ella.
func page_under(at: Vector2) -> int:
	return owner_notebook.spread * 2 + (1 if at.x >= 1.0 else 0)


static func local_point(at: Vector2) -> Vector2:
	return Vector2(at.x - floorf(clampf(at.x, 0.0, 1.999)), at.y)


## Mueve el lápiz como lo haría el ratón ([param relative], en píxeles), pintando si
## [param pressing].
func move_pencil(relative: Vector2) -> void:
	cursor += relative * CURSOR_PER_PIXEL
	cursor = Vector2(clampf(cursor.x, 0.0, 1.999), clampf(cursor.y, 0.0, 1.0))
	if stroke_page >= 0:
		_extend_stroke()


## Pulsa el botón izquierdo (pinta, borra o estampa) o lo suelta.
func press(pressed: bool) -> void:
	var current: String = tool()
	if not pressed:
		_finish_stroke()
		_erasing = false
		return
	if PEN_INKS.has(current):
		stroke = PackedVector2Array([_shaky(local_point(cursor))])
		stroke_page = page_under(cursor)
	elif current == "goma":
		_erasing = true
		_erase_clock = 0.0
	elif Notebook.STAMPS.has(current):
		var text: String = (
			Notebook.clock_text(GameState.minute) if current == Notebook.CLOCK_STAMP else ""
		)
		owner_notebook.stamp(page_under(cursor), current, local_point(cursor), text)


## La regla: al pulsar el botón derecho se fija un extremo; al soltarlo, la recta.
func use_ruler(pressed: bool) -> void:
	if pressed:
		ruler_from = cursor
		return
	if ruler_from == Vector2.INF:
		return
	var from_page: int = page_under(ruler_from)
	if PEN_INKS.has(tool()) and from_page == page_under(cursor):
		var line: PackedVector2Array = PackedVector2Array(
			[local_point(ruler_from), _shaky(local_point(cursor))]
		)
		owner_notebook.draw_stroke(from_page, PEN_INKS[tool()], line)
	ruler_from = Vector2.INF


## La rueda: la herramienta siguiente o la anterior.
func cycle_tool(step: int) -> void:
	tool_index = wrapi(tool_index + step, 0, tools().size())
	_refresh()


## A y D: la doble página anterior o la siguiente.
func turn(step: int) -> void:
	_finish_stroke()
	owner_notebook.spread = clampi(owner_notebook.spread + step, 0, Notebook.PAGES / 2 - 1)
	_refresh()


## T: escribe una nota donde está el lápiz (se termina con Intro; Esc la deja).
func start_note() -> void:
	if _note != null:
		return
	_note = LineEdit.new()
	_note.max_length = Notebook.MAX_NOTE
	_note.placeholder_text = "Escribe y pulsa Intro"
	_note.add_theme_font_override("font", UiFonts.get_font(&"manuscrita"))
	_note.add_theme_font_size_override("font_size", 30)
	_note.anchor_left = 0.25
	_note.anchor_right = 0.75
	_note.anchor_top = 0.86
	_note.anchor_bottom = 0.93
	_layer.add_child(_note)
	_note.grab_focus()
	var page: int = page_under(cursor)
	var at: Vector2 = local_point(cursor)
	_note.text_submitted.connect(
		func(text: String) -> void:
			owner_notebook.write(page, at, text)
			_end_note()
	)


func _end_note() -> void:
	if _note != null:
		_note.queue_free()
		_note = null


func _unhandled_input(event: InputEvent) -> void:
	if _note != null:
		if event.is_action_pressed(&"pause"):
			_end_note()
			get_viewport().set_input_as_handled()
		return
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null:
		move_pencil(motion.relative)
		get_viewport().set_input_as_handled()
		return
	var button: InputEventMouseButton = event as InputEventMouseButton
	if button != null:
		match button.button_index:
			MOUSE_BUTTON_LEFT:
				press(button.pressed)
			MOUSE_BUTTON_RIGHT:
				use_ruler(button.pressed)
			MOUSE_BUTTON_WHEEL_UP:
				if button.pressed:
					cycle_tool(-1)
			MOUSE_BUTTON_WHEEL_DOWN:
				if button.pressed:
					cycle_tool(1)
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed(&"notebook") or event.is_action_pressed(&"pause"):
		close()
	elif event.is_action_pressed(&"move_left"):
		turn(-1)
	elif event.is_action_pressed(&"move_right"):
		turn(1)
	elif event is InputEventKey and (event as InputEventKey).pressed:
		if (event as InputEventKey).keycode == KEY_T:
			start_note()
		else:
			return
	else:
		return
	get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_clock += delta
	_rise = minf(1.0, _rise + delta / RISE_SECONDS)
	_place(_rise)
	if _erasing:
		_erase_clock -= delta
		if _erase_clock <= 0.0:
			_erase_clock = ERASE_EVERY
			owner_notebook.erase(page_under(cursor), local_point(cursor), ERASER_RADIUS)
	_pose_pencil()
	for side: int in _pages.size():
		var page: NotebookPage = _pages[side]
		var here: bool = (cursor.x >= 1.0) == (side == 1)
		page.cursor = local_point(cursor) if here else Vector2(-1.0, -1.0)
		page.cursor_tool = tool()
		page.live = (
			stroke if stroke_page == owner_notebook.spread * 2 + side else PackedVector2Array()
		)
		page.live_ink = int(PEN_INKS.get(tool(), 0))
		page.ruler = PackedVector2Array()
		if ruler_from != Vector2.INF and here and page_under(ruler_from) == page_under(cursor):
			page.ruler = PackedVector2Array([local_point(ruler_from), local_point(cursor)])
		page.queue_redraw()


func _extend_stroke() -> void:
	if page_under(cursor) != stroke_page:
		_finish_stroke()
		return
	var point: Vector2 = _shaky(local_point(cursor))
	if stroke.is_empty() or stroke[stroke.size() - 1].distance_to(point) >= MIN_STEP:
		stroke.append(point)
		if stroke.size() >= Notebook.MAX_POINTS:
			_finish_stroke()


func _finish_stroke() -> void:
	if stroke_page >= 0 and stroke.size() >= 2:
		owner_notebook.draw_stroke(stroke_page, PEN_INKS.get(tool(), 0), stroke)
	stroke = PackedVector2Array()
	stroke_page = -1


## Un punto con el temblor del miedo.
func _shaky(point: Vector2) -> Vector2:
	var player: Player = owner_notebook.player
	var fear: float = clampf(player.tremble / Fear.HANDS_TREMBLE, 0.0, 1.0) if player else 0.0
	if fear <= 0.0:
		return point
	var shake: Vector2 = Vector2(
		sin(_clock * 31.0) + sin(_clock * 53.0 + 1.1) * 0.5,
		cos(_clock * 27.0) + cos(_clock * 47.0 + 0.4) * 0.5
	)
	return (point + shake * TREMBLE * fear).clamp(Vector2.ZERO, Vector2.ONE)


func _refresh() -> void:
	var notebook: Notebook = owner_notebook.contents()
	for side: int in _pages.size():
		var number: int = owner_notebook.spread * 2 + side
		_pages[side].page = notebook.pages[number]
		_pages[side].number = number
		_pages[side].queue_redraw()
	if _label != null:
		_label.text = _tool_name(tool())


static func _tool_name(current: String) -> String:
	match current:
		"lapiz":
			return "lápiz"
		"goma":
			return "goma"
		"rojo", "azul", "verde":
			return "lápiz " + current
	return "sello: " + {"botin": "botín", "radiacion": "radiación"}.get(current, current)


## Sube a la vista (de 0 a 1) delante de la cámara.
func _place(amount: float) -> void:
	var eased: float = 1.0 - pow(1.0 - amount, 3.0)
	position = Vector3(0.0, -DROP - (1.0 - eased) * 0.25, -DISTANCE)
	rotation = Vector3(TILT, 0.0, 0.0)


func _build() -> void:
	_model = (load(MODEL) as PackedScene).instantiate()
	_freeze(_model)
	add_child(_model)
	# El lápiz que trae el modelo, tumbado en el lomo: ahora lo llevas en la mano.
	for node: Node in _model.find_children("lapiz*", "Node3D", true, false):
		(node as Node3D).visible = false
	for side: int in PAGE_NODES.size():
		var viewport: SubViewport = SubViewport.new()
		viewport.name = "Pagina_%d" % side
		viewport.size = Vector2i(NotebookPage.SIZE)
		viewport.transparent_bg = false
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		add_child(viewport)
		var page: NotebookPage = NotebookPage.new()
		page.eraser_radius = ERASER_RADIUS
		viewport.add_child(page)
		_pages.append(page)
		var surface: MeshInstance3D = (
			_model.find_child(PAGE_NODES[side], true, false) as MeshInstance3D
		)
		if surface != null:
			var material: StandardMaterial3D = StandardMaterial3D.new()
			material.albedo_texture = viewport.get_texture()
			material.roughness = 1.0
			surface.material_override = material
			_surfaces.append(surface)
	if ResourceLoader.exists(PENCIL):
		_pencil = (load(PENCIL) as PackedScene).instantiate()
		_freeze(_pencil)
		add_child(_pencil)
	_layer = CanvasLayer.new()
	_layer.name = "CuadernoTexto"
	add_child(_layer)
	_label = UiFonts.make_label("", &"manuscrita", 28, Color(0.9, 0.86, 0.76))
	_label.anchor_left = 0.04
	_label.anchor_top = 0.92
	_layer.add_child(_label)


## El punto de la hoja en el marco del cuaderno (sobre la superficie de su página).
func page_point(at: Vector2) -> Vector3:
	var side: int = 1 if at.x >= 1.0 else 0
	if side >= _surfaces.size():
		return Vector3.ZERO
	var surface: MeshInstance3D = _surfaces[side]
	var box: AABB = BackpackView._relative(surface, self) * surface.get_aabb()
	var local: Vector2 = local_point(at)
	return Vector3(
		box.position.x + local.x * box.size.x, box.end.y, box.position.z + local.y * box.size.z
	)


## El lápiz con la punta en el papel (la goma, del revés), echado como en la mano.
func _pose_pencil() -> void:
	if _pencil == null:
		return
	var touch: Vector3 = page_point(cursor) + Vector3.UP * LIFT
	# El cuerpo sube del papel hacia la mano (a la derecha y hacia ti). El modelo tiene la
	# punta en -x y la goma en +x, a 6,5 cm de su centro: con la goma, se le da la vuelta.
	var body: Vector3 = Vector3(0.55, 0.7, 0.45).normalized()
	var x_axis: Vector3 = -body if tool() == "goma" else body
	var y_axis: Vector3 = (Vector3.BACK - x_axis * x_axis.dot(Vector3.BACK)).normalized()
	var turn_basis: Basis = Basis(x_axis, y_axis, x_axis.cross(y_axis))
	var center: Vector3 = touch + body * 0.065
	_pencil.transform = Transform3D(turn_basis, center)


static func _freeze(root: Node) -> void:
	for body: Node in root.find_children("*", "CollisionObject3D", true, false):
		(body as CollisionObject3D).process_mode = Node.PROCESS_MODE_DISABLED
		if body is RigidBody3D:
			(body as RigidBody3D).freeze = true
