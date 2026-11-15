@tool
extends Node3D
## Mesa del equipo (F1-08): el equipo del stalker y las herramientas, ordenados
## sobre una mesa, cada uno con su etiqueta de cartón escrita a mano. Es la
## vitrina de los modelos pequeños, que en los dioramas se ven de lejos.
##
## Todos llevan el contorno de los objetos clave. Como en el depósito, los
## objetos se colocan desde código y no se guardan en la escena.

const MODELS_DIR: String = "res://assets/models/"
const TABLE_TOP: float = 0.75
const TAG_TEXTURE: String = "res://assets/ui/etiqueta_precio.svg"
const CUTOUT_SHADER: String = "res://assets/shaders/tinta_recorte.gdshader"
const BASE_MATERIAL: String = "res://assets/materials/base_vertex.tres"
const RAMPS: String = "res://assets/textures/rampas.png"
const INK: Color = Color("#1b1a22")
## [modelo, posición sobre la mesa (x, z), giro, rótulo]. Filas de atrás adelante.
const LAYOUT: Array = [
	["palanca", Vector2(-0.74, -0.44), 0.0, "Palanca"],
	["mascara", Vector2(-0.22, -0.46), 8.0, "Máscara"],
	["despertador", Vector2(0.14, -0.44), -12.0, "Despertador"],
	["cizalla", Vector2(0.72, -0.44), 0.0, "Cizalla"],
	["cuerda", Vector2(-0.82, 0.0), -125.0, "Cuerda"],
	["cuaderno_abierto", Vector2(-0.26, -0.06), 0.0, "Cuaderno"],
	["prismaticos", Vector2(0.18, -0.06), 0.0, "Prismáticos"],
	["cuaderno", Vector2(0.52, -0.06), -6.0, ""],
	["linterna_dinamo", Vector2(0.84, -0.06), 180.0, "Dinamo"],
	["martillo", Vector2(-0.8, 0.36), 90.0, "Martillo"],
	["dosimetro", Vector2(-0.44, 0.32), 0.0, "Dosímetro"],
	["brujula", Vector2(-0.14, 0.32), 0.0, "Brújula"],
	["linterna", Vector2(0.12, 0.34), 180.0, "Linterna"],
	["lapiz", Vector2(0.38, 0.34), 90.0, "Lápiz"],
	["navaja", Vector2(0.62, 0.34), 90.0, "Navaja"],
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


func _rebuild() -> void:
	if _props != null:
		_props.free()
	_props = Node3D.new()
	_props.name = "Objetos"
	add_child(_props)
	_build_table()
	for item: Array in LAYOUT:
		var spot: Vector2 = item[1]
		var node: Node3D = load(MODELS_DIR + item[0] + ".glb").instantiate()
		node.position = Vector3(spot.x, TABLE_TOP, spot.y)
		node.rotation_degrees = Vector3(0, item[2], 0)
		_props.add_child(node)
		if not Engine.is_editor_hint():
			InkHull.add_to(node)
		if item[3] != "":
			_tag(item[3], Vector3(spot.x, TABLE_TOP, spot.y + _tag_offset(item[0])))
	for body: Node in _props.find_children("*", "RigidBody3D", true, false):
		(body as RigidBody3D).freeze = true


## Distancia de la etiqueta al centro del objeto: delante de él, hacia la cámara.
func _tag_offset(model: String) -> float:
	match model:
		"palanca", "cizalla":
			return 0.14
		"cuerda":
			return 0.24
		"martillo":
			return 0.13
		"brujula", "dosimetro", "prismaticos":
			return 0.21
		"lapiz", "navaja":
			return 0.12
		_:
			return 0.17


## Mesa de tablas: un tablero de madera oscura y un hule gastado encima.
func _build_table() -> void:
	var wood: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	wood.set_shader_parameter("albedo_color", Color("#6e4a32"))
	var dark: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	dark.set_shader_parameter("albedo_color", Color("#4a3426"))
	for i: int in 8:
		var z: float = -0.8 + i * 0.2 + 0.1
		var tone: ShaderMaterial = wood if i % 2 == 0 else dark
		_block(Vector3(2.7, 0.04, 0.195), Vector3(0, TABLE_TOP - 0.02, z), tone)
	for x: float in [-1.25, 1.25]:
		for z: float in [-0.72, 0.72]:
			_block(
				Vector3(0.07, TABLE_TOP - 0.04, 0.07), Vector3(x, (TABLE_TOP - 0.04) / 2.0, z), dark
			)
	var floor_material: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	floor_material.set_shader_parameter("albedo_color", Color("#7d746a"))
	_block(Vector3(8, 0.1, 8), Vector3(0, -0.05, 0), floor_material)


## Etiqueta de cartón tumbada sobre la mesa, con el nombre escrito a lápiz.
func _tag(text: String, position: Vector3) -> void:
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = load(CUTOUT_SHADER)
	material.set_shader_parameter("albedo_texture", load(TAG_TEXTURE))
	material.set_shader_parameter("ramps", load(RAMPS))
	material.set_shader_parameter("use_vertex_color", false)
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.17, 0.085)
	var card: MeshInstance3D = MeshInstance3D.new()
	card.mesh = quad
	card.material_override = material
	card.position = position + Vector3(0, 0.002, 0)
	card.rotation_degrees = Vector3(-90, 0, 0)
	_props.add_child(card)
	var label: Label3D = Label3D.new()
	label.text = text
	label.font = UiFonts.get_font(&"manuscrita_negrita")
	label.font_size = 64
	label.pixel_size = 0.00046
	label.modulate = INK
	label.outline_size = 0
	label.position = position + Vector3(0.01, 0.004, 0)
	label.rotation_degrees = Vector3(-90, 0, 0)
	_props.add_child(label)


func _block(size: Vector3, position: Vector3, material: Material) -> void:
	var box: BoxMesh = BoxMesh.new()
	box.size = size
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.mesh = box
	mesh.material_override = material
	mesh.position = position
	_props.add_child(mesh)
