class_name PaperCard
extends Node3D
## Un papel del mundo: una nota, una ficha de encargo, un recibo, una etiqueta,
## un cartel escrito a mano…
##
## Es un rectángulo con su dibujo (un SVG de assets/ui/) y el texto encima, con
## las tipografías del juego. Lo describe un diccionario, el mismo que usa
## [CloseUp] para verlo de cerca:
## [codeblock]
## {"svg": "papel_suelto", "ancho_m": 0.15,
##  "rotulos": [{"text": "…", "x": 20, "y": 30, "size": 28,
##               "font": "manuscrita", "color": "#3b3a40", "rot": -1}],
##  "tachados": [[x0, y0, x1, y1], …]}
## [/codeblock]
## Las posiciones y los tamaños van en píxeles del SVG (como los .json que
## acompañan a los SVG de tools/svg/generate.mjs). La cara mira hacia +Z y el
## centro del papel es el origen.

const UI_DIR: String = "res://assets/ui/"
const SHADER: String = "res://assets/shaders/tinta_recorte.gdshader"
const RAMPS: String = "res://assets/textures/rampas.png"
const INK: Color = Color("#2b2622")
const PENCIL: Color = Color("#3b3a40")
## Separación del texto sobre el papel (para que no parpadee).
const LIFT: float = 0.0006

static var _materials: Dictionary = {}

var data: Dictionary = {}
## Lo que mide en el mundo, en metros.
var size: Vector2 = Vector2.ZERO
var _paper: MeshInstance3D
var _text: Node3D


## Un papel listo para colocar.
static func create(paper: Dictionary) -> PaperCard:
	var card: PaperCard = PaperCard.new()
	card.show_data(paper)
	return card


## Un papel suelto escrito a lápiz, con varias líneas (una nota, un aviso).
static func note(lines: Array, width: float = 0.15, svg: String = "papel_suelto") -> Dictionary:
	var rotulos: Array = []
	var y: float = 34.0
	for line: Variant in lines:
		var text: String = str(line)
		var bold: bool = text.begins_with("*")
		(
			rotulos
			. append(
				{
					"text": text.trim_prefix("*"),
					"x": 22,
					"y": y,
					"size": 30 if bold else 26,
					"font": "manuscrita_negrita" if bold else "manuscrita",
					"color": "#2b2622",
					"rot": -1.5,
				}
			)
		)
		y += 36.0 if bold else 31.0
	return {"svg": svg, "ancho_m": width, "rotulos": rotulos}


## Tamaño natural del SVG, en píxeles.
static func svg_size(svg: String) -> Vector2:
	var texture: Texture2D = load(UI_DIR + svg + ".svg")
	return texture.get_size() if texture != null else Vector2(256, 320)


static func _material(svg: String) -> ShaderMaterial:
	if not _materials.has(svg):
		var material: ShaderMaterial = ShaderMaterial.new()
		material.shader = load(SHADER)
		material.set_shader_parameter("albedo_texture", load(UI_DIR + svg + ".svg"))
		material.set_shader_parameter("ramps", load(RAMPS))
		material.set_shader_parameter("use_vertex_color", false)
		_materials[svg] = material
	return _materials[svg]


## Pinta (o vuelve a pintar) el papel con [param paper].
func show_data(paper: Dictionary) -> void:
	data = paper.duplicate(true)
	var svg: String = str(data.get("svg", "papel_suelto"))
	var pixels: Vector2 = svg_size(svg)
	var width: float = float(data.get("ancho_m", 0.15))
	var scale_m: float = width / pixels.x
	size = pixels * scale_m
	if _paper == null:
		_paper = MeshInstance3D.new()
		_paper.name = "Papel"
		add_child(_paper)
		_text = Node3D.new()
		_text.name = "Texto"
		add_child(_text)
	var quad: QuadMesh = QuadMesh.new()
	quad.size = size
	_paper.mesh = quad
	_paper.material_override = _material(svg)
	for child: Node in _text.get_children():
		child.queue_free()
	for item: Variant in data.get("rotulos", []):
		if item is Dictionary:
			_text.add_child(_label(item, scale_m))
	for strike: Variant in data.get("tachados", []):
		if strike is Array and (strike as Array).size() == 4:
			_text.add_child(_strike(strike, scale_m))


func _label(item: Dictionary, scale_m: float) -> Label3D:
	var label: Label3D = Label3D.new()
	label.text = str(item.get("text", ""))
	label.font = UiFonts.get_font(StringName(str(item.get("font", "manuscrita"))))
	label.font_size = int(item.get("size", 26))
	label.pixel_size = scale_m
	label.modulate = Color(str(item.get("color", "#2b2622")))
	label.outline_size = 0
	label.shaded = true
	label.double_sided = false
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	label.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	label.position = _point(float(item.get("x", 0)), float(item.get("y", 0)), scale_m)
	label.rotation.z = -deg_to_rad(float(item.get("rot", 0)))
	return label


## Una raya de lápiz que tacha (de [x0, y0] a [x1, y1], en píxeles).
func _strike(values: Array, scale_m: float) -> MeshInstance3D:
	var from: Vector3 = _point(float(values[0]), float(values[1]), scale_m)
	var to: Vector3 = _point(float(values[2]), float(values[3]), scale_m)
	var box: BoxMesh = BoxMesh.new()
	box.size = Vector3(from.distance_to(to), 3.0 * scale_m, 0.0002)
	var line: MeshInstance3D = MeshInstance3D.new()
	line.mesh = box
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = Color("#3b3a40")
	line.material_override = material
	line.position = (from + to) / 2.0 + Vector3(0.0, 0.0, LIFT)
	line.rotation.z = atan2(to.y - from.y, to.x - from.x)
	return line


func _point(x: float, y: float, scale_m: float) -> Vector3:
	return Vector3(x * scale_m - size.x / 2.0, size.y / 2.0 - y * scale_m, LIFT)
