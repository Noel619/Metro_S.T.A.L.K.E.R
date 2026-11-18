class_name CloseUp
extends CanvasLayer
## Ver algo de cerca: una nota, una ficha, el libro de cuentas, un recibo.
##
## Es el mismo papel del mundo ([PaperCard]) dibujado grande, sobre la vista
## oscurecida, con el grano de papel encima. Mientras está abierto, el jugador
## no mira ni anda; F, Esc o cualquier botón lo cierra. Solo existe en el equipo
## de quien mira.

signal closed

const UI_DIR: String = "res://assets/ui/"
const PAPER_GRAIN: String = "res://assets/textures/papel.png"
## Lo que ocupa el papel de la pantalla, como mucho.
const FILL: float = 0.82

## Hay uno abierto (el jugador no debe moverse ni mirar).
static var active: CloseUp = null

var _holder: Control
var _pages: Array[Dictionary] = []
var _page: int = 0
var _opened_at: int = 0


## Abre [param papers] de cerca (uno o varios: se pasan con la rueda o A/D).
static func open(tree: SceneTree, papers: Array) -> CloseUp:
	if active != null and is_instance_valid(active):
		active.close()
	var view: CloseUp = CloseUp.new()
	for paper: Variant in papers:
		if paper is Dictionary:
			view._pages.append(paper)
	tree.root.add_child(view)
	return view


static func is_open() -> bool:
	return active != null and is_instance_valid(active)


func _ready() -> void:
	layer = 20
	active = self
	_opened_at = Time.get_ticks_msec()
	var shade: ColorRect = ColorRect.new()
	shade.color = Color(0.06, 0.05, 0.05, 0.72)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	_holder = Control.new()
	_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_holder)
	var grain: TextureRect = TextureRect.new()
	grain.texture = load(PAPER_GRAIN)
	grain.stretch_mode = TextureRect.STRETCH_TILE
	grain.set_anchors_preset(Control.PRESET_FULL_RECT)
	grain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var multiply: CanvasItemMaterial = CanvasItemMaterial.new()
	multiply.blend_mode = CanvasItemMaterial.BLEND_MODE_MUL
	grain.material = multiply
	add_child(grain)
	_show_page()
	get_viewport().size_changed.connect(_show_page)


func _exit_tree() -> void:
	if active == self:
		active = null


func _unhandled_input(event: InputEvent) -> void:
	# Lo que se pulsa justo al abrir es lo que lo ha abierto.
	if Time.get_ticks_msec() - _opened_at < 150:
		return
	var button: InputEventMouseButton = event as InputEventMouseButton
	if button != null and button.pressed:
		if button.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_turn(1)
		elif button.button_index == MOUSE_BUTTON_WHEEL_UP:
			_turn(-1)
		else:
			close()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed(&"move_right"):
		_turn(1)
	elif event.is_action_pressed(&"move_left"):
		_turn(-1)
	elif event.is_action_pressed(&"interact") or event.is_action_pressed(&"pause"):
		close()
	else:
		return
	get_viewport().set_input_as_handled()


func close() -> void:
	if is_queued_for_deletion():
		return
	if active == self:
		active = null
	closed.emit()
	queue_free()


func _turn(step: int) -> void:
	if _pages.size() < 2:
		return
	_page = clampi(_page + step, 0, _pages.size() - 1)
	_show_page()


func _show_page() -> void:
	for child: Node in _holder.get_children():
		child.queue_free()
	if _pages.is_empty():
		return
	var paper: Dictionary = _pages[_page]
	var svg: String = str(paper.get("svg", "papel_suelto"))
	var natural: Vector2 = PaperCard.svg_size(svg)
	var screen: Vector2 = get_viewport().get_visible_rect().size
	var fit: float = minf(screen.x * FILL / natural.x, screen.y * FILL / natural.y)
	var sheet: Control = Control.new()
	sheet.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sheet.scale = Vector2.ONE * fit
	sheet.position = (screen - natural * fit) / 2.0
	sheet.rotation_degrees = float(paper.get("giro", -1.2))
	sheet.pivot_offset = natural / 2.0
	_holder.add_child(sheet)
	var shadow: TextureRect = TextureRect.new()
	shadow.texture = load(UI_DIR + svg + ".svg")
	shadow.position = Vector2(8, 12)
	shadow.modulate = Color(0, 0, 0, 0.4)
	sheet.add_child(shadow)
	var page: TextureRect = TextureRect.new()
	page.texture = load(UI_DIR + svg + ".svg")
	sheet.add_child(page)
	for item: Variant in paper.get("rotulos", []):
		if not item is Dictionary:
			continue
		var values: Dictionary = item
		var label: Label = UiFonts.make_label(
			str(values.get("text", "")),
			StringName(str(values.get("font", "manuscrita"))),
			int(values.get("size", 26)),
			Color(str(values.get("color", "#2b2622")))
		)
		label.position = Vector2(float(values.get("x", 0)), float(values.get("y", 0)))
		label.rotation_degrees = float(values.get("rot", 0))
		sheet.add_child(label)
	for strike: Variant in paper.get("tachados", []):
		if strike is Array and (strike as Array).size() == 4:
			var line: Line2D = Line2D.new()
			line.width = 3.0
			line.default_color = Color("#3b3a40")
			line.points = PackedVector2Array(
				[Vector2(strike[0], strike[1]), Vector2(strike[2], strike[3])]
			)
			sheet.add_child(line)
	if _pages.size() > 1:
		var hint: Label = UiFonts.make_label(
			"%d / %d" % [_page + 1, _pages.size()], &"manuscrita", 30, Color("#e8dcc4")
		)
		hint.position = Vector2(screen.x / 2.0 - 30.0, screen.y - 56.0)
		_holder.add_child(hint)
