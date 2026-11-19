@tool
extends Node3D
## Mesa del botín (F3-18): lo que se puede juntar en la superficie, de lo más
## común a lo muy raro, extendido sobre una mesa larga del depósito al volver de
## una salida. Una fila por rareza (de delante atrás: común, poco común, raro y
## muy raro), con su cartel, y cada objeto con su etiqueta de cartón escrita a
## mano con el nombre de su ficha (data/items).
##
## Como la mesa del equipo, es la vitrina de los modelos: todos llevan el
## contorno de los objetos clave y se colocan desde código. Cada fila reparte
## sus objetos según lo que miden, y para las capturas hay una cámara de cerca
## por cada [constant PER_CAMERA] objetos, además de la de la mesa entera.

const MODELS_DIR: String = "res://assets/models/"
const TABLE_TOP: float = 0.75
const TAG_TEXTURE: String = "res://assets/ui/etiqueta_precio.svg"
const CUTOUT_SHADER: String = "res://assets/shaders/tinta_recorte.gdshader"
const BASE_MATERIAL: String = "res://assets/materials/base_vertex.tres"
const RAMPS: String = "res://assets/textures/rampas.png"
const INK: Color = Color("#1b1a22")
const TAG_PIXEL: float = 0.00036
const SIGN_PIXEL: float = 0.00062
## La parte de la etiqueta donde cabe el texto (sin la punta del agujero).
const TAG_TEXT_SHARE: float = 0.78
## Entre un objeto y el siguiente, y entre filas.
const ITEM_GAP: float = 0.07
const ROW_STEP: float = 0.54
## La primera fila (la de delante).
const FIRST_ROW: float = 0.78
## Objetos por cámara de cerca.
const PER_CAMERA: int = 4
## Las filas, de delante atrás: su cartel, el nombre de sus cámaras de cerca y sus
## objetos (modelo y giro en grados).
const ROWS: Array = [
	[
		"Común",
		"Comun",
		[
			["leche_condensada", 20.0],
			["lata_espadines", -14.0],
			["tarro_pepinillos", 0.0],
			["azucar", 12.0],
			["velas", -8.0],
			["jabon", 18.0],
			["taza_esmaltada", -30.0],
			["manoplas", 0.0],
			["gorro_orejeras", 15.0],
			["cinta_aislante", 0.0],
			["clavos", -6.0],
			["marco_foto", 8.0],
		],
	],
	[
		"Poco común",
		"PocoComun",
		[
			["pila_petaca", 12.0],
			["filtro", 0.0],
			["analgesicos", -10.0],
			["yodo", 0.0],
			["jeringa", 8.0],
			["llave_inglesa", 0.0],
			["alicates", 10.0],
			["valvulas", 0.0],
			["quinque", 0.0],
			["reloj_pulsera", 70.0],
			["paquete_correos", -8.0],
		],
	],
	[
		"Raro",
		"Raro",
		[
			["antibioticos", 10.0],
			["pastillas_antirradiacion", -12.0],
			["botiquin_militar", 8.0],
			["bateria_coche", -10.0],
			["camara_fotos", 6.0],
			["hornillo", 0.0],
			["medalla", -6.0],
			["samovar", 0.0],
		],
	],
	[
		"Muy raro",
		"MuyRaro",
		[
			["insulina", 8.0],
			["microscopio", -20.0],
			["icono", 4.0],
			["reloj_bolsillo", 0.0],
		],
	],
]

var _props: Node3D


func _ready() -> void:
	_rebuild()
	if not Engine.is_editor_hint():
		StyleDirector.set_zone(StyleDirector.ZONE_DEPOT, true)
		for camera: Node in get_tree().get_nodes_in_group(&"capture_camera"):
			var target: Node3D = camera.get_node_or_null("Mira")
			if target != null:
				(camera as Camera3D).look_at(target.global_position)


## Deja solo una cámara para las capturas (por ejemplo, con
## [code]--call=MesaBotin:only:CamaraRaro1[/code]).
func only(camera_name: String) -> void:
	for camera: Node in get_tree().get_nodes_in_group(&"capture_camera"):
		if camera.name != camera_name:
			camera.remove_from_group(&"capture_camera")


func _rebuild() -> void:
	if _props != null:
		_props.free()
	_props = Node3D.new()
	_props.name = "Objetos"
	add_child(_props)
	var width: float = 0.0
	for index: int in ROWS.size():
		var row: Array = ROWS[index]
		width = maxf(width, _row(row[0], row[1], row[2], FIRST_ROW - ROW_STEP * index))
	_build_table(Vector2(width + 0.5, ROW_STEP * ROWS.size() + 0.3))
	for body: Node in _props.find_children("*", "RigidBody3D", true, false):
		(body as RigidBody3D).freeze = true


## Una fila: el cartel a la izquierda y los objetos uno detrás de otro, cada uno
## con su etiqueta delante. Devuelve lo que mide de ancho.
func _row(title: String, cameras_name: String, entries: Array, z: float) -> float:
	var slots: Array = []
	var sign: Vector2 = _tag_size(title, SIGN_PIXEL)
	var sign_width: float = sign.x
	var cursor: float = sign_width + ITEM_GAP
	for entry: Array in entries:
		var path: String = MODELS_DIR + entry[0] + ".glb"
		if not ResourceLoader.exists(path):
			continue
		var node: Node3D = load(path).instantiate()
		node.position = Vector3(0, TABLE_TOP, z)
		node.rotation_degrees = Vector3(0, entry[1], 0)
		_props.add_child(node)
		if not Engine.is_editor_hint():
			InkHull.add_to(node)
		var box: AABB = _bounds(node)
		var label: String = _label(entry[0])
		var slot: float = maxf(box.size.x, _tag_size(label, TAG_PIXEL).x)
		node.position.x = cursor + slot / 2.0 - box.get_center().x
		slots.append([node, label])
		cursor += slot + ITEM_GAP
	var width: float = cursor - ITEM_GAP
	var shift: float = -width / 2.0
	var sign_at: Vector3 = Vector3(shift + sign_width / 2.0, TABLE_TOP, z + 0.04)
	_tag(title, sign_at, SIGN_PIXEL, 5.0)
	# El cartel entra en la primera cámara de la fila.
	var chunk: Array = [
		AABB(sign_at - Vector3(sign.x, 0, sign.y) / 2.0, Vector3(sign.x, 0, sign.y))
	]
	var cameras: int = 0
	for index: int in slots.size():
		var node: Node3D = slots[index][0]
		node.position.x += shift
		var box: AABB = _bounds(node)
		var tag_at: Vector3 = Vector3(box.get_center().x, TABLE_TOP, box.end.z + 0.045)
		var tag: Vector2 = _tag(slots[index][1], tag_at, TAG_PIXEL, -2.0)
		var tag_box: AABB = AABB(
			tag_at - Vector3(tag.x / 2.0, 0, tag.y / 2.0), Vector3(tag.x, 0, tag.y)
		)
		chunk.append(box.merge(tag_box))
		if index % PER_CAMERA == PER_CAMERA - 1 or index == slots.size() - 1:
			cameras += 1
			_close_up("Camara%s%d" % [cameras_name, cameras], chunk)
			chunk = []
	return width


## Una cámara de cerca que encuadra unos cuantos objetos con sus etiquetas.
func _close_up(camera_name: String, boxes: Array) -> void:
	var frame: AABB = boxes[0]
	for box: AABB in boxes:
		frame = frame.merge(box)
	var camera: Camera3D = Camera3D.new()
	camera.name = camera_name
	camera.fov = 40.0
	camera.near = 0.02
	var target: Vector3 = frame.get_center()
	target.y = TABLE_TOP + frame.size.y * 0.3
	# Que quepa de ancho (con algo de aire), mirando desde arriba y por delante.
	var distance: float = maxf(frame.size.x * 0.84, frame.size.z * 1.45) + 0.1
	var elevation: float = deg_to_rad(52.0)
	_props.add_child(camera)
	camera.look_at_from_position(
		target + Vector3(0, sin(elevation), cos(elevation)) * distance, target
	)
	if not Engine.is_editor_hint():
		camera.add_to_group(&"capture_camera")


## El nombre de la ficha del objeto (o su modelo, si aún no tiene ficha).
func _label(model: String) -> String:
	if ResourceLoader.exists(ItemState.ITEMS_DIR + model + ".tres"):
		return ItemState.load_data(StringName(model)).display_name
	return model


## La caja que envuelve las mallas de [param node], en los ejes de la mesa.
func _bounds(node: Node3D) -> AABB:
	var result: AABB = AABB(node.position, Vector3.ZERO)
	var to_table: Transform3D = _props.global_transform.affine_inverse()
	for child: Node in node.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = child as MeshInstance3D
		if mesh.mesh == null or String(mesh.name).ends_with(InkHull.SUFFIX):
			continue
		result = result.merge(to_table * mesh.global_transform * mesh.get_aabb())
	return result


## Mesa de tablas: un tablero de madera oscura, largo, con sus patas.
func _build_table(size: Vector2) -> void:
	var wood: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	wood.set_shader_parameter("albedo_color", Color("#6e4a32"))
	var dark: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	dark.set_shader_parameter("albedo_color", Color("#4a3426"))
	var middle: float = FIRST_ROW - ROW_STEP * (ROWS.size() - 1) / 2.0
	var boards: int = 12
	var board: float = size.y / boards
	for i: int in boards:
		var z: float = middle - size.y / 2.0 + board * (i + 0.5)
		var tone: ShaderMaterial = wood if i % 2 == 0 else dark
		_block(Vector3(size.x, 0.04, board - 0.005), Vector3(0, TABLE_TOP - 0.02, z), tone)
	for x: float in [-size.x / 2.0 + 0.1, size.x / 2.0 - 0.1]:
		for z: float in [middle - size.y / 2.0 + 0.1, middle + size.y / 2.0 - 0.1]:
			_block(
				Vector3(0.08, TABLE_TOP - 0.04, 0.08), Vector3(x, (TABLE_TOP - 0.04) / 2.0, z), dark
			)
	var floor_material: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	floor_material.set_shader_parameter("albedo_color", Color("#7d746a"))
	_block(Vector3(12, 0.1, 12), Vector3(0, -0.05, 0), floor_material)


## El texto de una etiqueta: los nombres largos van en dos renglones.
func _lines(text: String) -> String:
	if text.length() <= 15 or not text.contains(" "):
		return text
	var half: int = text.length() / 2
	var best: int = -1
	for index: int in text.length():
		if text[index] == " " and (best < 0 or absi(index - half) < absi(best - half)):
			best = index
	return text.substr(0, best) + "\n" + text.substr(best + 1)


## Lo que mide una etiqueta (ancho y fondo) con su texto.
func _tag_size(text: String, pixel: float) -> Vector2:
	var font: Font = UiFonts.get_font(&"manuscrita_negrita")
	var lines: PackedStringArray = _lines(text).split("\n")
	var text_width: float = 0.0
	for line: String in lines:
		var line_width: float = font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, 64).x
		text_width = maxf(text_width, line_width)
	var height: float = pixel * 64.0 * (2.1 if lines.size() == 1 else 3.0)
	# El dibujo de la etiqueta tiene la punta del agujero a la izquierda: el texto
	# cabe en el 78 % de la derecha.
	var width: float = (text_width * pixel + pixel * 64.0 * 0.6) / TAG_TEXT_SHARE
	return Vector2(maxf(height * 2.0, width), height)


## Etiqueta de cartón tumbada sobre la mesa, con el texto escrito a lápiz. Se
## alarga con el texto. Devuelve lo que mide.
func _tag(text: String, position: Vector3, pixel: float, turn: float) -> Vector2:
	var size: Vector2 = _tag_size(text, pixel)
	var holder: Node3D = Node3D.new()
	holder.position = position + Vector3(0, 0.002, 0)
	holder.rotation_degrees = Vector3(0, turn, 0)
	_props.add_child(holder)
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = load(CUTOUT_SHADER)
	material.set_shader_parameter("albedo_texture", load(TAG_TEXTURE))
	material.set_shader_parameter("ramps", load(RAMPS))
	material.set_shader_parameter("use_vertex_color", false)
	var quad: QuadMesh = QuadMesh.new()
	quad.size = size
	var card: MeshInstance3D = MeshInstance3D.new()
	card.mesh = quad
	card.material_override = material
	card.rotation_degrees = Vector3(-90, 0, 0)
	holder.add_child(card)
	var label: Label3D = Label3D.new()
	label.text = _lines(text)
	label.font = UiFonts.get_font(&"manuscrita_negrita")
	label.font_size = 64
	label.line_spacing = -18.0
	label.pixel_size = pixel
	label.modulate = INK
	label.outline_size = 0
	label.position = Vector3(size.x * 0.05, 0.002, 0)
	label.rotation_degrees = Vector3(-90, 0, 0)
	holder.add_child(label)
	return size


func _block(size: Vector3, position: Vector3, material: Material) -> void:
	var box: BoxMesh = BoxMesh.new()
	box.size = size
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.mesh = box
	mesh.material_override = material
	mesh.position = position
	_props.add_child(mesh)
