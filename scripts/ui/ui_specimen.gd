extends Control
## Prueba de interfaz de la Fase 1 (F1-12): las primeras piezas en el estilo final,
## sobre la mesa del depósito. Sin cajas de texto: todo es papel, lápiz y tinta.
##
## - El cuaderno abierto con un mapa dibujado a lápiz (sale del plano de la ciudad).
## - Una etiqueta de precio escrita a mano.
## - El recibo del impuesto, a máquina, con el sello violeta encima.
## - Una ficha de encargo clavada con una chincheta.
##
## Las ilustraciones son SVG de tools/svg/generate.mjs; los textos los pone este
## script con las tipografías del juego, a partir del .json que acompaña a cada SVG.

const UI_DIR: String = "res://assets/ui/"
const WOOD: String = "res://assets/textures/madera_mesa.png"
const PAPER_GRAIN: String = "res://assets/textures/papel.png"
const STAMP_COLOR: Color = Color("#5b3f86")


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var table: TextureRect = TextureRect.new()
	table.texture = load(WOOD)
	table.stretch_mode = TextureRect.STRETCH_TILE
	table.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(table)
	_piece("cuaderno_doble", Vector2(24, 118), 0.7, -2.0, "cuaderno_mapa")
	_piece("recibo", Vector2(1190, 26), 0.58, 5.0, "recibo")
	_stamp(Vector2(1330, 250), 0.68, -16.0)
	_piece("ficha_encargo", Vector2(1120, 520), 0.72, -6.0, "ficha_encargo")
	_price_tag(Vector2(36, 752), 1.25, -14.0, "120 ₽")
	_overlay()


## Una pieza de papel: sombra, ilustración y, si los hay, sus rótulos.
func _piece(
	svg_name: String, at: Vector2, size: float, angle: float, labels_name: String
) -> Control:
	var holder: Control = Control.new()
	holder.position = at
	holder.scale = Vector2.ONE * size
	holder.rotation_degrees = angle
	add_child(holder)
	var texture: Texture2D = load(UI_DIR + svg_name + ".svg")
	var shadow: TextureRect = TextureRect.new()
	shadow.texture = texture
	shadow.position = Vector2(10, 14)
	shadow.modulate = Color(0, 0, 0, 0.35)
	holder.add_child(shadow)
	var paper: TextureRect = TextureRect.new()
	paper.texture = texture
	holder.add_child(paper)
	if svg_name != labels_name:
		var overlay: TextureRect = TextureRect.new()
		overlay.texture = load(UI_DIR + labels_name + ".svg")
		holder.add_child(overlay)
	_add_labels(holder, UI_DIR + labels_name + ".json")
	return holder


func _add_labels(holder: Control, path: String) -> void:
	if not FileAccess.file_exists(path):
		return
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	for item: Dictionary in data.get("rotulos", []):
		var label: Label = UiFonts.make_label(
			item["text"], StringName(item["font"]), int(item["size"]), Color(item["color"])
		)
		label.position = Vector2(item["x"], item["y"])
		label.rotation_degrees = item["rot"]
		holder.add_child(label)


## Sello violeta: el anillo es un SVG; el texto va en círculo, letra a letra.
func _stamp(at: Vector2, size: float, angle: float) -> void:
	var holder: Control = Control.new()
	holder.position = at
	holder.scale = Vector2.ONE * size
	holder.rotation_degrees = angle
	holder.modulate = Color(1, 1, 1, 0.82)
	add_child(holder)
	var ring: TextureRect = TextureRect.new()
	ring.texture = load(UI_DIR + "sello.svg")
	holder.add_child(ring)
	var center: Vector2 = Vector2(150, 150)
	var text: String = "ADMINISTRACIÓN DE LA ESTACIÓN · IMPUESTO · "
	var radius: float = 112.0
	for i: int in text.length():
		var angle_rad: float = TAU * i / text.length() - PI / 2.0
		var letter: Label = UiFonts.make_label(text[i], &"rotulo", 20, STAMP_COLOR)
		letter.size = Vector2(20, 26)
		letter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		letter.pivot_offset = Vector2(10, 13)
		letter.position = (
			center + Vector2(cos(angle_rad), sin(angle_rad)) * radius - letter.pivot_offset
		)
		letter.rotation = angle_rad + PI / 2.0
		holder.add_child(letter)
	var paid: Label = UiFonts.make_label("PAGADO", &"rotulo", 46, STAMP_COLOR)
	paid.position = Vector2(84, 74)
	holder.add_child(paid)
	var day: Label = UiFonts.make_label("DÍA 14", &"rotulo_fino", 28, STAMP_COLOR)
	day.position = Vector2(112, 190)
	holder.add_child(day)


func _price_tag(at: Vector2, size: float, angle: float, price: String) -> void:
	var holder: Control = Control.new()
	holder.position = at
	holder.scale = Vector2.ONE * size
	holder.rotation_degrees = angle
	add_child(holder)
	var tag: TextureRect = TextureRect.new()
	tag.texture = load(UI_DIR + "etiqueta_precio.svg")
	holder.add_child(tag)
	var text: Label = UiFonts.make_label(price, &"manuscrita_negrita", 52, Color("#1b1a22"))
	text.position = Vector2(92, 26)
	text.rotation_degrees = -4.0
	holder.add_child(text)


## Grano de papel y viñeta encima de todo, como en el dibujo en 3D.
func _overlay() -> void:
	var grain: TextureRect = TextureRect.new()
	grain.texture = load(PAPER_GRAIN)
	grain.stretch_mode = TextureRect.STRETCH_TILE
	grain.set_anchors_preset(Control.PRESET_FULL_RECT)
	var multiply: CanvasItemMaterial = CanvasItemMaterial.new()
	multiply.blend_mode = CanvasItemMaterial.BLEND_MODE_MUL
	grain.material = multiply
	grain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(grain)
	var gradient: Gradient = Gradient.new()
	gradient.set_color(0, Color(0, 0, 0, 0))
	gradient.set_color(1, Color(0.05, 0.03, 0.02, 0.4))
	var vignette_texture: GradientTexture2D = GradientTexture2D.new()
	vignette_texture.gradient = gradient
	vignette_texture.fill = GradientTexture2D.FILL_RADIAL
	vignette_texture.fill_from = Vector2(0.5, 0.5)
	vignette_texture.fill_to = Vector2(1.05, 1.05)
	var vignette: TextureRect = TextureRect.new()
	vignette.texture = vignette_texture
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vignette)
