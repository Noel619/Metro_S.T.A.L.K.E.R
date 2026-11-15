class_name City
extends Node3D
## La ciudad levantada desde el plano (data/ciudad/) en volúmenes sencillos: la maqueta
## automática de F3-15, para probar recorridos, vistas, sectores de carga y rendimiento
## antes de construir con el kit modular.
##
## La ciudad se divide en los sectores de 200 × 200 m del plano (A1-H6). Cada sector tiene
## una versión lejana ("Lejos": el relieve cada 8 m y los edificios en un solo bloque, del
## color de la niebla) y una detallada (el relieve cada 2 m, cada edificio con sus
## ventanas, los vehículos, los árboles y las estructuras), que se dibuja en lugar de la
## lejana cuando la cámara está a menos de [member near_distance] del sector (HLOD, con
## visibility_parent). Los hitos se dibujan siempre y la niebla nunca los borra del todo.
## Los edificios grandes y el relieve son oclusores: lo que tapan no se dibuja.

const MODELS_DIR: String = "res://assets/models/"
const RAMPS: String = "res://assets/textures/rampas.png"
const SHADERS_DIR: String = "res://assets/shaders/"
const BOX_MATERIAL: String = "res://assets/materials/nevado.tres"
const SNOW_COLOR: Color = Color(0.74, 0.72, 0.67)
## Metros entre los puntos del relieve: detallado y lejano.
const NEAR_STEP: float = 2.0
const FAR_STEP: float = 8.0
## Lo que tiene que medir un edificio para tapar lo de detrás.
const OCCLUDER_MIN_HEIGHT: float = 8.0
const OCCLUDER_MIN_AREA: float = 80.0
const PROP_MODELS: PackedStringArray = [
	"coche", "coche_quemado", "arbol_desnudo", "arbol_desnudo_b"
]

## Distancia al centro de un sector a partir de la cual se dibuja su versión lejana.
@export var near_distance: float = 450.0
## Distancia a la que se dejan de dibujar los vehículos y los árboles.
@export var props_distance: float = 300.0
## Hasta dónde llega el terreno de alrededor del mapa.
@export var surroundings_margin: float = 600.0

var plan: CityPlan
## Los edificios del plano por su id.
var buildings_by_id: Dictionary = {}
## Cifras de la construcción: segundos, sectores, triángulos, instancias…
var stats: Dictionary = {}

var _materials: Dictionary = {}
var _models: Dictionary = {}
var _builder: CityBuildings
var _terrain: CityTerrain
var _props: CityProps


## Levanta la ciudad entera (tarda unos segundos).
func build(city_plan: CityPlan) -> void:
	var started: int = Time.get_ticks_msec()
	plan = city_plan
	_builder = CityBuildings.new(plan)
	_terrain = CityTerrain.new(plan)
	_props = CityProps.new(plan)
	stats = {"triangulos_cerca": 0, "triangulos_lejos": 0, "vehiculos": 0, "arboles": 0}
	_make_materials()
	_load_models()
	var vehicles: Dictionary = _props.vehicles()
	var trees: Dictionary = _props.trees()
	var structures: Dictionary = _props.structures()
	var by_sector: Dictionary = {}
	for building: Dictionary in plan.data["edificios"]:
		var sector: Vector2i = plan.sector_of(Vector2(building["centro"][0], building["centro"][1]))
		if not by_sector.has(sector):
			by_sector[sector] = []
		by_sector[sector].append(building)
	var grid: Vector2i = plan.sector_grid()
	for row: int in grid.y:
		for column: int in grid.x:
			var sector: Vector2i = Vector2i(column, row)
			var props: Dictionary = vehicles.get(sector, {}).merged(trees.get(sector, {}))
			_build_sector(sector, by_sector.get(sector, []), props, structures.get(sector))
	_build_surroundings()
	_build_bounds()
	stats["sectores"] = grid.x * grid.y
	stats["edificios"] = buildings_by_id.size()
	stats["segundos"] = (Time.get_ticks_msec() - started) / 1000.0


## El registro del plano del edificio al que pertenece un cuerpo de colisión (vacío si
## no es un edificio).
func building_of(collider: Object) -> Dictionary:
	if collider is Node and (collider as Node).has_meta(&"edificio"):
		return buildings_by_id.get((collider as Node).get_meta(&"edificio"), {})
	return {}


## Lo que queda en pie de un edificio, en metros (para el panel).
func standing_height(building: Dictionary) -> float:
	return _builder.standing_height(building)


## Altura de lo que se pisa en un punto del plano (los puentes incluidos).
func surface_height(point: Vector2) -> float:
	return _props.surface_height(point)


func _build_sector(
	sector: Vector2i, buildings: Array, props: Dictionary, structures: Variant
) -> void:
	var rect: Rect2 = plan.sector_rect(sector)
	var center: Vector2 = rect.get_center()
	var node: Node3D = Node3D.new()
	node.name = "Sector_" + CityPlan.sector_name(sector)
	node.position = CityPlan.to_world(center)
	add_child(node)
	# Primero las mallas: la versión lejana tiene que estar completa antes de que los
	# nodos detallados la tomen como padre de visibilidad.
	var far: MeshBuffer = _terrain.sector_mesh(sector, FAR_STEP, 8.0)
	var occluders: MeshBuffer = MeshBuffer.new()
	occluders.append(far, Vector3.DOWN * 2.0)
	var built: Array[Array] = []
	for building: Dictionary in buildings:
		var anchor: Vector2 = Vector2(building["centro"][0], building["centro"][1])
		var offset: Vector3 = Vector3(anchor.x - center.x, 0.0, center.y - anchor.y)
		var mesh: MeshBuffer = _builder.build(building, anchor)
		if not CityPlan.is_landmark(building):
			far.append(mesh, offset)
		if _blocks_view(building):
			occluders.append(mesh, offset)
		built.append([building, mesh, offset])
	if structures is MeshBuffer:
		far.append(structures)
	var far_node: MeshInstance3D = MeshInstance3D.new()
	far_node.name = "Lejos"
	far_node.mesh = far.to_mesh(_materials["lejos"])
	far_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	far_node.visibility_range_begin = near_distance
	node.add_child(far_node)
	stats["triangulos_lejos"] += far.triangle_count()
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Colision"
	node.add_child(body)
	var heights: PackedFloat32Array = _terrain.sector_heights(sector, NEAR_STEP)
	var ground: CollisionShape3D = CollisionShape3D.new()
	ground.name = "Relieve"
	ground.shape = _terrain.heightmap_shape(NEAR_STEP, heights)
	ground.scale = Vector3(NEAR_STEP, 1.0, NEAR_STEP)
	body.add_child(ground)
	var near_terrain: MeshBuffer = _terrain.grid_mesh(rect, NEAR_STEP, heights, center, 3.0)
	_add_mesh(node, "Terreno", near_terrain, _materials["suelo"], NodePath("../Lejos"))
	var buildings_node: Node3D = Node3D.new()
	buildings_node.name = "Edificios"
	node.add_child(buildings_node)
	for entry: Array in built:
		var building: Dictionary = entry[0]
		var landmark: bool = CityPlan.is_landmark(building)
		var parent_path: NodePath = NodePath() if landmark else NodePath("../../Lejos")
		var material: Material = _materials["hito" if landmark else "fachada"]
		var instance: MeshInstance3D = _add_mesh(
			buildings_node, building["id"], entry[1], material, parent_path
		)
		instance.position = entry[2]
		_add_building_body(node, building, entry[1], entry[2])
		buildings_by_id[building["id"]] = building
	if structures is MeshBuffer:
		_add_mesh(node, "Estructuras", structures, _materials["fachada"], NodePath("../Lejos"))
		var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
		shape.backface_collision = true
		shape.set_faces((structures as MeshBuffer).faces())
		var holder: CollisionShape3D = CollisionShape3D.new()
		holder.name = "Estructuras"
		holder.shape = shape
		body.add_child(holder)
	_add_props(node, props)
	var occluder: ArrayOccluder3D = ArrayOccluder3D.new()
	occluder.set_arrays(occluders.vertices, occluders.indices)
	var occluder_node: OccluderInstance3D = OccluderInstance3D.new()
	occluder_node.name = "Oclusor"
	occluder_node.occluder = occluder
	node.add_child(occluder_node)


## Distancia a la que cada sector pasa a su versión lejana (muy grande: todo detallado).
func set_near_distance(distance: float) -> void:
	near_distance = distance
	for sector_node: Node in get_children():
		var far: GeometryInstance3D = sector_node.get_node_or_null("Lejos") as GeometryInstance3D
		if far != null:
			far.visibility_range_begin = distance


func _add_mesh(
	parent: Node,
	node_name: String,
	mesh: MeshBuffer,
	material: Material,
	visibility_parent: NodePath
) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh.to_mesh(material)
	parent.add_child(instance)
	if not visibility_parent.is_empty():
		instance.visibility_parent = visibility_parent
	stats["triangulos_cerca"] += mesh.triangle_count()
	return instance


func _add_building_body(
	sector_node: Node3D, building: Dictionary, mesh: MeshBuffer, offset: Vector3
) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Cuerpo_" + String(building["id"])
	body.position = offset
	body.set_meta(&"edificio", building["id"])
	var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	shape.backface_collision = true
	shape.set_faces(mesh.faces())
	var holder: CollisionShape3D = CollisionShape3D.new()
	holder.shape = shape
	body.add_child(holder)
	sector_node.get_node("Colision").add_child(body)


func _blocks_view(building: Dictionary) -> bool:
	if float(building["superficie"]) < OCCLUDER_MIN_AREA:
		return false
	return _builder.standing_height(building) >= OCCLUDER_MIN_HEIGHT


## Vehículos y árboles del sector como instancias (una MultiMesh por modelo).
func _add_props(sector_node: Node3D, props: Dictionary) -> void:
	if props.is_empty():
		return
	var holder: Node3D = Node3D.new()
	holder.name = "Objetos"
	sector_node.add_child(holder)
	for model: String in props:
		var instances: Array = props[model]
		var multimesh: MultiMesh = MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.use_colors = true
		multimesh.mesh = _models[model][0]
		multimesh.instance_count = instances.size()
		for i: int in instances.size():
			var placed: Transform3D = instances[i][0]
			placed.origin -= sector_node.position
			multimesh.set_instance_transform(i, placed)
			multimesh.set_instance_color(i, instances[i][1])
		var node: MultiMeshInstance3D = MultiMeshInstance3D.new()
		node.name = model.capitalize().replace(" ", "")
		node.multimesh = multimesh
		node.material_override = _models[model][1]
		node.visibility_range_end = props_distance
		holder.add_child(node)
		node.visibility_parent = NodePath("../../Lejos")
		var counter: String = "arboles" if model.begins_with("arbol") else "vehiculos"
		stats[counter] += instances.size()


## El terreno de alrededor del mapa: sin colisión (los bordes no se cruzan).
func _build_surroundings() -> void:
	var mesh: MeshBuffer = _terrain.surroundings_mesh(surroundings_margin, 25.0)
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = "Alrededores"
	instance.mesh = mesh.to_mesh(_materials["suelo"])
	add_child(instance)


## Paredes invisibles en el borde del mapa: más allá no se puede ir.
func _build_bounds() -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Bordes"
	add_child(body)
	var size: Vector2 = plan.size
	var walls: Array[Array] = [
		[Vector3(-1.0, 0.0, -size.y * 0.5), Vector3(2.0, 400.0, size.y + 4.0)],
		[Vector3(size.x + 1.0, 0.0, -size.y * 0.5), Vector3(2.0, 400.0, size.y + 4.0)],
		[Vector3(size.x * 0.5, 0.0, 1.0), Vector3(size.x + 4.0, 400.0, 2.0)],
		[Vector3(size.x * 0.5, 0.0, -size.y - 1.0), Vector3(size.x + 4.0, 400.0, 2.0)],
	]
	for wall: Array in walls:
		var box: BoxShape3D = BoxShape3D.new()
		box.size = wall[1]
		var holder: CollisionShape3D = CollisionShape3D.new()
		holder.shape = box
		holder.position = wall[0]
		body.add_child(holder)


func _make_materials() -> void:
	var ramps: Texture2D = load(RAMPS)
	var ground_image: Image = plan.ground.duplicate()
	ground_image.generate_mipmaps()
	var ground: ShaderMaterial = _shader_material("tinta_suelo", ramps, 0.9)
	ground.set_shader_parameter("ground_map", ImageTexture.create_from_image(ground_image))
	ground.set_shader_parameter("ground_size", plan.size)
	_materials["suelo"] = ground
	var windows: ImageTexture = _window_texture()
	for kind: String in ["fachada", "hito"]:
		var material: ShaderMaterial = _shader_material("tinta_" + kind, ramps, 0.55)
		material.set_shader_parameter("albedo_texture", windows)
		_materials[kind] = material
	var far: ShaderMaterial = ShaderMaterial.new()
	far.shader = load(SHADERS_DIR + "tinta_silueta.gdshader")
	_materials["lejos"] = far


func _shader_material(shader_name: String, ramps: Texture2D, snow: float) -> ShaderMaterial:
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = load(SHADERS_DIR + shader_name + ".gdshader")
	material.set_shader_parameter("ramps", ramps)
	material.set_shader_parameter("snow_amount", snow)
	material.set_shader_parameter("snow_color", SNOW_COLOR)
	return material


## Un vano de fachada: muro claro (lo tiñe el color del edificio) y una ventana oscura.
## Se repite cada vano y cada planta.
func _window_texture() -> ImageTexture:
	var image: Image = Image.create_empty(32, 32, false, Image.FORMAT_RGB8)
	image.fill(Color(1.0, 1.0, 1.0))
	image.fill_rect(Rect2i(8, 9, 16, 14), Color(0.3, 0.29, 0.31))
	image.fill_rect(Rect2i(7, 23, 18, 2), Color(0.86, 0.85, 0.83))
	image.generate_mipmaps()
	return ImageTexture.create_from_image(image)


## Las mallas de los modelos que se repiten (coches y árboles) y la caja de los demás
## vehículos, con sus materiales.
func _load_models() -> void:
	for model: String in PROP_MODELS:
		var scene: Node = (load(MODELS_DIR + model + ".glb") as PackedScene).instantiate()
		var found: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)
		var mesh_instance: MeshInstance3D = found[0] as MeshInstance3D
		_models[model] = [mesh_instance.mesh, mesh_instance.get_surface_override_material(0)]
		scene.free()
	var box: BoxMesh = BoxMesh.new()
	box.size = Vector3.ONE
	_models["caja"] = [box, load(BOX_MATERIAL)]
