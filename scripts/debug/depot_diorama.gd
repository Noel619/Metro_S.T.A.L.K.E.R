@tool
extends Node3D
## Diorama A de la Fase 1: el depósito, en sus dos estados.
##
## - "abandonado": el primer día. Persiana cerrada, lámpara fundida, telarañas,
##   cajas por el suelo. Solo entra la luz fría del pasillo por la rendija.
## - "limpio": persiana subida, lámpara encendida y todo en su sitio.
##
## Los objetos se colocan desde código para poder ajustar la composición
## rápido. También se ven en el editor (es un script @tool), pero no se guardan
## en la escena.

const MODELS_DIR: String = "res://assets/models/"
const CEILING: float = 2.9
const FLOOR: float = 0.025
const SHELF_LEVELS: Array[float] = [0.09, 0.51, 0.93, 1.35, 1.77]
const COBWEB_TEXTURE: String = "res://assets/ui/telarana.svg"
const PAPER_TEXTURE: String = "res://assets/ui/papel_suelto.svg"
const CUTOUT_SHADER: String = "res://assets/shaders/tinta_recorte.gdshader"
const BASE_MATERIAL: String = "res://assets/materials/base_vertex.tres"
const RAMPS: String = "res://assets/textures/rampas.png"

@export_enum("abandonado", "limpio") var state: String = "limpio":
	set(value):
		state = value
		if is_node_ready():
			_rebuild()

var _props: Node3D
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


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
	_rng.seed = 7
	_place("deposito_sala", Vector3.ZERO)
	if state == "abandonado":
		_build_abandoned()
	else:
		_build_clean()
	for body: Node in _props.find_children("*", "RigidBody3D", true, false):
		(body as RigidBody3D).freeze = true
	$LucesLimpio.visible = state == "limpio"
	$LucesAbandonado.visible = state == "abandonado"
	var environment: Environment = $Entorno.environment
	if state == "limpio":
		environment.ambient_light_color = Color(0.36, 0.30, 0.36)
		environment.ambient_light_energy = 0.6
	else:
		environment.ambient_light_color = Color(0.2, 0.22, 0.3)
		environment.ambient_light_energy = 1.0


func _build_clean() -> void:
	_place("persiana_abierta", Vector3(0.6, 0.0, 1.82))
	_place("lampara_colgante", Vector3(0.3, CEILING, -0.4))
	_place("banco_trabajo", Vector3(0.45, FLOOR, -1.36))
	var bench_top: float = FLOOR + 0.9
	_place("lata", Vector3(0.05, bench_top, -1.3), Vector3(0, 20, 0))
	_place("lata", Vector3(0.14, bench_top, -1.42))
	_place("botella_verde", Vector3(0.9, bench_top, -1.5))
	_place("caja_carton_pequena", Vector3(0.62, bench_top, -1.45), Vector3(0, -8, 0))
	_place("cubo", Vector3(1.05, FLOOR + 0.22, -1.45))
	_place("estanteria_metalica", Vector3(-1.95, FLOOR, -0.95), Vector3(0, 90, 0))
	_place("estanteria_metalica", Vector3(-1.95, FLOOR, 0.2), Vector3(0, 90, 0))
	_shelf_box("caja_carton", -0.95, 0, 0.0)
	_shelf_box("caja_carton_pequena", -1.18, 1, 0.0)
	_shelf_box("caja_carton_pequena", -0.72, 1, 0.0)
	_shelf_box("lata", -1.2, 2, 0.05)
	_shelf_box("lata", -1.1, 2, -0.05)
	_shelf_box("botella_marron", -0.8, 2, 0.0)
	_shelf_box("botella_verde", -0.68, 2, 0.04)
	_shelf_box("caja_carton_pequena", -0.95, 3, 0.0)
	_shelf_box("caja_carton", -0.95, 4, 0.0)
	_shelf_box("caja_carton_pequena", -0.05, 0, 0.0)
	_shelf_box("caja_carton_pequena", 0.42, 0, 0.0)
	_shelf_box("caja_carton", 0.2, 1, 0.0)
	_shelf_box("cubo", 0.0, 2, 0.0)
	_shelf_box("lata", 0.35, 2, 0.0)
	_shelf_box("caja_carton_pequena", 0.2, 3, 0.0)
	_shelf_box("caja_carton_pequena", 0.0, 4, 0.0)
	_shelf_box("caja_carton_pequena", 0.4, 4, 0.0)
	_place("caja_madera", Vector3(1.62, FLOOR, -1.35), Vector3(0, 8, 0))
	_place("caja_madera_b", Vector3(1.6, FLOOR + 0.44, -1.33), Vector3(0, -6, 0))
	_place("caja_carton_grande", Vector3(1.75, FLOOR, -0.5), Vector3(0, 14, 0))
	_place("bidon", Vector3(1.85, FLOOR, 0.45))
	_place("escoba", Vector3(2.08, FLOOR, 1.05), Vector3(0, 90, -10))
	_build_hall()


func _build_abandoned() -> void:
	_place("persiana_cerrada", Vector3(0.6, 0.0, 1.82))
	var lamp: Node3D = _place("lampara_colgante", Vector3(0.3, CEILING, -0.4))
	for mesh: Node in lamp.find_children("bombilla", "MeshInstance3D", true, false):
		var dark: ShaderMaterial = load("res://assets/materials/bombilla.tres").duplicate()
		dark.set_shader_parameter("emission_energy", 0.0)
		(mesh as MeshInstance3D).set_surface_override_material(0, dark)
	_place("banco_trabajo", Vector3(0.45, FLOOR, -1.36))
	var bench_top: float = FLOOR + 0.9
	_place("botella_verde", Vector3(0.2, bench_top + 0.038, -1.3), Vector3(90, 30, 0))
	_place("lata", Vector3(0.75, bench_top, -1.45), Vector3(0, 0, 0))
	_place("caja_carton_pequena", Vector3(0.95, bench_top, -1.5), Vector3(0, 25, 0))
	_place("estanteria_metalica", Vector3(-1.95, FLOOR, -0.95), Vector3(0, 90, 0))
	_shelf_box("caja_carton_pequena", -1.1, 1, 0.0, 27.0)
	_shelf_box("lata", -0.7, 3, 0.0)
	_shelf_box("caja_carton", -0.95, 4, 0.0, -12.0)
	# Cajas por el suelo, como las dejó el antiguo dueño.
	_place("caja_carton", Vector3(-1.45, FLOOR, 0.35), Vector3(0, 33, 0))
	_place("caja_carton_pequena", Vector3(-1.38, FLOOR + 0.38, 0.33), Vector3(0, -15, 0))
	_place("caja_carton_grande", Vector3(-1.0, FLOOR + 0.275, 1.05), Vector3(0, -20, 88))
	_place("caja_madera", Vector3(1.55, FLOOR, -1.25), Vector3(0, 21, 0))
	_place("caja_madera_b", Vector3(1.2, FLOOR + 0.22, -0.55), Vector3(90, -35, 0))
	_place("caja_carton", Vector3(1.75, FLOOR, 0.35), Vector3(0, -8, 0))
	_place("bidon", Vector3(1.9, FLOOR, 1.15))
	_place("cubo", Vector3(-0.3, FLOOR + 0.27, 0.9), Vector3(180, 0, 0))
	_place("escoba", Vector3(0.1, FLOOR + 0.03, 0.15), Vector3(-90, 0, 70))
	for i in 7:
		var position: Vector3 = Vector3(
			_rng.randf_range(-1.2, 1.4), FLOOR, _rng.randf_range(-0.8, 1.4)
		)
		var lying: bool = i % 2 == 0
		var model: String = "lata" if i < 4 else "botella_marron"
		var height: float = 0.037 if model == "lata" else 0.038
		_place(
			model,
			position + Vector3(0, height if lying else 0.0, 0),
			Vector3(90 if lying else 0, _rng.randf_range(0, 360), 0)
		)
	for i in 9:
		_paper(
			Vector3(
				_rng.randf_range(-1.5, 1.6), FLOOR + 0.004 + i * 0.0005, _rng.randf_range(-1.0, 1.5)
			)
		)
	_cobweb(Vector3(-1.98, 2.66, -1.58), 45.0, 0.9)
	_cobweb(Vector3(1.98, 2.66, -1.58), -45.0, 0.8)
	_cobweb(Vector3(-1.98, 2.0, -0.45), 90.0, 0.5)
	_cobweb(Vector3(0.62, 2.34, 1.5), 180.0, 0.6)


## Pasillo de la estación, que se ve por la persiana subida.
func _build_hall() -> void:
	var marble: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	marble.set_shader_parameter("albedo_color", Color("#a89f8a"))
	var granite: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	granite.set_shader_parameter("albedo_color", Color("#6d6660"))
	_block(Vector3(12, 0.2, 6), Vector3(0.6, -0.1, 4.8), granite)
	_block(Vector3(12, 5, 0.3), Vector3(0.6, 2.5, 7.4), marble)
	for x: float in [-3.4, -1.0, 2.2, 4.6]:
		_block(Vector3(0.7, 5, 0.7), Vector3(x, 2.5, 4.6), marble)
		_block(Vector3(0.9, 0.25, 0.9), Vector3(x, 0.12, 4.6), granite)
	_block(Vector3(1.6, 0.45, 0.45), Vector3(0.6, 0.23, 5.6), granite)


func _place(model: String, position: Vector3, rotation_deg: Vector3 = Vector3.ZERO) -> Node3D:
	var node: Node3D = load(MODELS_DIR + model + ".glb").instantiate()
	node.position = position
	node.rotation_degrees = rotation_deg
	_props.add_child(node)
	return node


## Coloca algo en una balda de la estantería de la pared izquierda.
func _shelf_box(model: String, z: float, level: int, x_offset: float, yaw: float = 0.0) -> void:
	var yaw_jitter: float = _rng.randf_range(-6.0, 6.0)
	_place(
		model,
		Vector3(-1.95 + x_offset, FLOOR + SHELF_LEVELS[level], z),
		Vector3(0, 90 + yaw + yaw_jitter, 0)
	)


func _cobweb(position: Vector3, yaw: float, size: float) -> void:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_texture = load(COBWEB_TEXTURE)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.roughness = 1.0
	material.metallic_specular = 0.0
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(size * 2.0, size)
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.mesh = quad
	mesh.material_override = material
	mesh.position = position
	mesh.rotation_degrees = Vector3(0, yaw, 0)
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_props.add_child(mesh)


func _paper(position: Vector3) -> void:
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = load(CUTOUT_SHADER)
	material.set_shader_parameter("albedo_texture", load(PAPER_TEXTURE))
	material.set_shader_parameter("ramps", load(RAMPS))
	material.set_shader_parameter("use_vertex_color", false)
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.21, 0.28)
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.mesh = quad
	mesh.material_override = material
	mesh.position = position
	mesh.rotation_degrees = Vector3(-90, _rng.randf_range(0, 360), 0)
	_props.add_child(mesh)


func _block(size: Vector3, position: Vector3, material: Material) -> void:
	var box: BoxMesh = BoxMesh.new()
	box.size = size
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.mesh = box
	mesh.material_override = material
	mesh.position = position
	_props.add_child(mesh)
