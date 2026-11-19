class_name City
extends Node3D
## La ciudad levantada desde el plano (data/ciudad/) en volúmenes sencillos: la maqueta
## automática de F3-15, para probar recorridos, vistas, sectores de carga y rendimiento
## antes de construir con el kit modular.
##
## Las calles, aceras, plazas, escaleras y sendas son la red de tránsito (CityTransit, desde
## data/ciudad/transito.json), con sus bordillos, muros, pasos de cebra, tapas y sumideros.
##
## La ciudad se divide en los sectores de 200 × 200 m del plano (A1-H6). Cada sector tiene
## una versión lejana ("Lejos": el relieve cada 8 m y los edificios en un solo bloque, del
## color de la niebla) y una detallada (el relieve cada 2 m, cada edificio con sus
## ventanas, los vehículos, los árboles y las estructuras), que se dibuja en lugar de la
## lejana cuando la cámara está a menos de [member near_distance] del sector (HLOD, con
## visibility_parent). Los hitos se dibujan siempre y la niebla nunca los borra del todo.
## Los edificios grandes y el relieve son oclusores: lo que tapan no se dibuja.
##
## Los edificios que sabe montar el kit de arquitectura (F3-16: las viviendas de las cuatro
## familias y los singulares) son sus modelos a menos de [member kit_distance] (CityKit, con
## [member kit_buildings]); más lejos, sus volúmenes. Es un relevo por edificio dentro del
## de su sector, porque un bloque del kit son unas sesenta mallas. Y las sombras de esas
## mallas solo se dibujan a menos de [member kit_shadow_distance]: más allá, la sombra del
## edificio la proyecta su volumen.

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
## Los árboles (los vehículos los dice CityProps.VEHICLE_MODELS).
const PROP_MODELS: PackedStringArray = ["arbol_desnudo", "arbol_desnudo_b"]
## Materiales del tránsito: textura (assets/textures/pavimentos/), nieve y fila de rampas.
const TRANSIT_MATERIALS: Dictionary = {
	"asfalto": ["asfalto", 0.75],
	"acera": ["asfalto", 0.85],
	"losas": ["losas", 0.85],
	"plaza": ["granito", 0.85],
	"adoquin": ["adoquin", 0.8],
	"granito": ["granito", 0.8],
	"bordillo": ["bordillo", 0.6],
	"hormigon": ["hormigon", 0.75],
	"grava": ["grava", 0.9],
	"balasto": ["grava", 0.8],
	"tierra": ["tierra", 0.9],
	"derrumbe": ["derrumbe", 0.85],
	"grieta": ["", 0.8],
	"pintura": ["pintura", 0.6],
	"metal": ["", 0.3],
}
const PAVEMENTS_DIR: String = "res://assets/textures/pavimentos/"
## Lo que miden los matojos (ancho y alto) antes de su escala.
const TUFT_SIZE: Vector2 = Vector2(0.8, 0.6)
## Los detalles pequeños (la basura, los cascotes, los matojos, los baches, las tapas) solo
## se dibujan cerca: de lejos no se distinguen y son muchos.
const SMALL_DETAILS: PackedStringArray = [
	"cascotes_a",
	"cascotes_b",
	"cascotes_c",
	"ladrillos",
	"neumatico",
	"carton",
	"rama",
	"escombros",
	"escombros_grande",
	"matojo",
	"bache_a",
	"bache_b",
	"bache_c",
	"bordillo_suelto",
	"tapa_redonda",
	"tapa_cuadrada",
	"tapa_suelta_redonda",
	"tapa_suelta_cuadrada",
	"pozo_redondo",
	"pozo_cuadrado",
	"sumidero",
]
const SMALL_DISTANCE: float = 110.0

## Distancia al centro de un sector a partir de la cual se dibuja su versión lejana.
@export var near_distance: float = 450.0
## Distancia a la que se dejan de dibujar los vehículos y los árboles.
@export var props_distance: float = 300.0
## Hasta dónde llega el terreno de alrededor del mapa.
@export var surroundings_margin: float = 600.0
## Monta con el kit de arquitectura los edificios que sabe montar (si no, todos son
## volúmenes, como en la maqueta de F3-15).
@export var kit_buildings: bool = true
## Distancia a un edificio del kit a partir de la cual se dibuja su volumen en vez de su
## modelo (con la niebla del juego, a 200 m apenas se distingue).
@export var kit_distance: float = 200.0
## Distancia a un edificio del kit (que no sea singular) a partir de la cual su modelo no
## proyecta sombras: las proyecta su volumen.
@export var kit_shadow_distance: float = 60.0

var plan: CityPlan
## Los edificios del plano por su id.
var buildings_by_id: Dictionary = {}
## Los edificios montados con el kit: id del plano -> su nodo (con sus metadatos: las
## puertas y el botín de los menores, KitMinor).
var kit_models: Dictionary = {}
## Cifras de la construcción: segundos, sectores, triángulos, instancias…
var stats: Dictionary = {}
## Lo que hay por la calle (los vehículos, los árboles y las estructuras) y dónde queda.
var props: CityProps:
	get:
		return _props

var _materials: Dictionary = {}
var _models: Dictionary = {}
var _builder: CityBuildings
var _terrain: CityTerrain
var _props: CityProps
var _transit: CityTransit
var _kit: CityKit
## Los volúmenes de los edificios montados con el kit: de lejos se ven ellos y de cerca, su
## modelo (su visibility_range_begin es kit_distance).
var _kit_volumes: Array[GeometryInstance3D] = []


## Levanta la ciudad entera (tarda unos segundos).
func build(city_plan: CityPlan) -> void:
	var started: int = Time.get_ticks_msec()
	plan = city_plan
	_builder = CityBuildings.new(plan)
	_terrain = CityTerrain.new(plan)
	_props = CityProps.new(plan)
	stats = {
		"triangulos_cerca": 0,
		"triangulos_lejos": 0,
		"vehiculos": 0,
		"arboles": 0,
		"kit_edificios": 0,
		"kit_piezas": 0,
	}
	_make_materials()
	_load_models()
	_transit = CityTransit.new(plan)
	_transit.build()
	_kit = CityKit.new(plan) if kit_buildings else null
	_kit_volumes.clear()
	_terrain.holes = _transit.touched
	if _kit != null:
		# El terreno no se dibuja donde los singulares bajan bajo la calle.
		_terrain.holes = _kit.cut_holes(_transit.touched, plan.relief_size, NEAR_STEP)
	_terrain.hole_step = NEAR_STEP
	stats["transito"] = _transit.stats
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


## Altura de lo que se pisa en un punto del plano: el tránsito si lo hay (la calzada, los
## peldaños, el tablero del puente…); si no, el relieve o el tablero de otro puente.
func surface_height(point: Vector2) -> float:
	var transit: float = _transit.surface_at(point) if _transit != null else NAN
	return _props.surface_height(point) if is_nan(transit) else transit


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
		# El volumen: la versión lejana, el oclusor y, si no lo monta el kit, todo.
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
	ground.shape = _terrain.heightmap_shape(NEAR_STEP, _carved(sector, heights))
	ground.scale = Vector3(NEAR_STEP, 1.0, NEAR_STEP)
	body.add_child(ground)
	var near_terrain: MeshBuffer = _terrain.grid_mesh(rect, NEAR_STEP, heights, center, 3.0)
	_add_mesh(node, "Terreno", near_terrain, _materials["suelo"], NodePath("../Lejos"))
	_add_transit(node, sector, body)
	var buildings_node: Node3D = Node3D.new()
	buildings_node.name = "Edificios"
	node.add_child(buildings_node)
	for entry: Array in built:
		var building: Dictionary = entry[0]
		buildings_by_id[building["id"]] = building
		if _kit != null and _kit.supports(building):
			_add_kit_building(node, buildings_node, building, entry[1], entry[2])
			continue
		var landmark: bool = CityPlan.is_landmark(building)
		var parent_path: NodePath = NodePath() if landmark else NodePath("../../Lejos")
		var material: Material = _materials["hito" if landmark else "fachada"]
		var instance: MeshInstance3D = _add_mesh(
			buildings_node, building["id"], entry[1], material, parent_path
		)
		instance.position = entry[2]
		_add_building_body(node, building, entry[1], entry[2])
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


## Las alturas de la colisión del relieve de un sector, rebajadas bajo el tránsito y
## hundidas bajo los huecos de los singulares (el foso de las escaleras del vestíbulo).
func _carved(sector: Vector2i, heights: PackedFloat32Array) -> PackedFloat32Array:
	var result: PackedFloat32Array = heights.duplicate()
	var n: int = _terrain.grid_size(NEAR_STEP)
	var stride: int = _transit.cells.x + 1
	var first: Vector2i = sector * _transit.cells_per_sector
	for j: int in n:
		for i: int in n:
			var gx: int = mini(first.x + i, _transit.cells.x)
			var gy: int = mini(first.y + j, _transit.cells.y)
			result[j * n + i] -= _transit.carve[gy * stride + gx]
	if _kit != null:
		_kit.carve(result, plan.sector_rect(sector).position, n, NEAR_STEP)
	return result


## Un edificio montado con el kit de arquitectura (CityKit): su modelo a su cota y, si está
## en ladera, su zócalo. Su volumen se dibuja en la versión detallada del sector hasta que se
## está a menos de [member kit_distance]; entonces, el modelo. El volumen de un hito no va en
## la versión lejana: se dibuja solo, también de lejos. A media distancia, el modelo va sin
## sombras ([method _add_kit_shadow]). Choca como su volumen, salvo los singulares, que traen
## su colisión (en ellos se entra).
func _add_kit_building(
	sector_node: Node3D, holder: Node3D, building: Dictionary, volume: MeshBuffer, offset: Vector3
) -> void:
	var model: Node3D = _kit.build(building)
	model.position = offset + Vector3.UP * float(building["cota"])
	holder.add_child(model)
	kit_models[building["id"]] = model
	var plinth: MeshBuffer = _kit.plinth(building)
	if not plinth.is_empty():
		var base: MeshInstance3D = MeshInstance3D.new()
		base.name = "Zocalo"
		base.mesh = plinth.to_mesh(_models["caja"][1])
		model.add_child(base)
		stats["triangulos_cerca"] += plinth.triangle_count()
	var landmark: bool = CityPlan.is_landmark(building)
	var switch: MeshInstance3D = _add_mesh(
		holder,
		String(building["id"]) + "_Volumen",
		volume,
		_materials["hito" if landmark else "fachada"],
		NodePath() if landmark else NodePath("../../Lejos")
	)
	switch.position = offset
	switch.visibility_range_begin = kit_distance
	_kit_volumes.append(switch)
	var shade: MeshInstance3D = null
	if not KitSingular.MODELS.has(building["id"]):
		shade = _add_kit_shadow(holder, building, offset, switch)
	var bounds: AABB = switch.mesh.get_aabb()
	for piece: Node in model.find_children("*", "GeometryInstance3D", true, false):
		var geometry: GeometryInstance3D = piece
		if shade == null or geometry.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			geometry.visibility_parent = geometry.get_path_to(switch)
			continue
		# De cerca, con su sombra; a media distancia, una copia (que comparte la malla) sin ella.
		# La copia mide la distancia desde el centro del volumen, como la sombra: así cambian
		# a la vez.
		var copy: GeometryInstance3D = geometry.duplicate() as GeometryInstance3D
		copy.name = String(geometry.name) + "_Medio"
		copy.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		geometry.get_parent().add_child(copy)
		copy.custom_aabb = _relative(copy, sector_node).affine_inverse() * switch.transform * bounds
		copy.visibility_range_begin = kit_shadow_distance
		copy.visibility_parent = copy.get_path_to(switch)
		geometry.visibility_parent = geometry.get_path_to(shade)
	var body: Node = model.get_node_or_null("Colision")
	if body != null:
		body.set_meta(&"edificio", building["id"])
	else:
		_add_building_body(sector_node, building, volume, offset)
	stats["kit_edificios"] += 1
	stats["kit_piezas"] += int(model.get_meta(&"kit_piezas", 0))


## La sombra de un edificio del kit a media distancia (de [member kit_shadow_distance] a
## [member kit_distance]): su volumen, metido hacia dentro para no quitarle la luz a su
## fachada, que solo proyecta sombra.
func _add_kit_shadow(
	holder: Node3D, building: Dictionary, offset: Vector3, switch: MeshInstance3D
) -> MeshInstance3D:
	var anchor: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	var shade: MeshInstance3D = MeshInstance3D.new()
	shade.name = String(building["id"]) + "_Sombra"
	shade.mesh = _builder.build(_kit.inset(building), anchor).to_mesh(_materials["fachada"])
	shade.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	shade.position = offset
	# Su distancia, desde el centro del volumen.
	shade.custom_aabb = switch.mesh.get_aabb()
	holder.add_child(shade)
	shade.visibility_parent = shade.get_path_to(switch)
	shade.visibility_range_begin = kit_shadow_distance
	return shade


## La transformación de [param node] respecto a su antepasado [param ancestor] (sin
## necesidad de estar en el árbol de escena).
static func _relative(node: Node3D, ancestor: Node) -> Transform3D:
	var result: Transform3D = Transform3D.IDENTITY
	var current: Node = node
	while current != ancestor and current is Node3D:
		result = (current as Node3D).transform * result
		current = current.get_parent()
	return result


## La red de tránsito del sector: una malla por material, su colisión y los detalles.
func _add_transit(node: Node3D, sector: Vector2i, body: StaticBody3D) -> void:
	var holder: Node3D = Node3D.new()
	holder.name = "Transito"
	node.add_child(holder)
	var by_material: Dictionary = _transit.meshes.get(sector, {})
	for material: String in by_material:
		var mesh: MeshBuffer = by_material[material]
		if mesh.is_empty():
			continue
		var shared: Material = _materials["suelo"] if material == "suelo" else _materials[material]
		_add_mesh(holder, material.capitalize(), mesh, shared, NodePath("../../Lejos"))
	var faces: MeshBuffer = _transit.collision.get(sector)
	if faces != null and not faces.vertices.is_empty():
		var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
		shape.backface_collision = true
		shape.set_faces(faces.vertices)
		var collision: CollisionShape3D = CollisionShape3D.new()
		collision.name = "Transito"
		collision.shape = shape
		body.add_child(collision)
	_add_props(node, _transit.instances.get(sector, {}), "Detalles")


## Distancia a la que cada sector pasa a su versión lejana (muy grande: todo detallado).
func set_near_distance(distance: float) -> void:
	near_distance = distance
	for sector_node: Node in get_children():
		var far: GeometryInstance3D = sector_node.get_node_or_null("Lejos") as GeometryInstance3D
		if far != null:
			far.visibility_range_begin = distance


## Distancia a la que los edificios del kit pasan de su volumen a su modelo.
## Una malla del kit de arquitectura por su nombre (la hoja de una puerta, el candado), o
## null.
func kit_mesh(piece: String) -> Mesh:
	if _kit == null:
		return null
	return _kit.kit.meshes_for("").get(piece) as Mesh


func set_kit_distance(distance: float) -> void:
	kit_distance = distance
	for volume: GeometryInstance3D in _kit_volumes:
		volume.visibility_range_begin = distance


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
	# Los modelos del kit que dejan ver dentro (los singulares, en los que se entra) o que se
	# han hundido a su manera no tapan como su volumen.
	if _kit != null and _kit.supports(building):
		if KitSingular.MODELS.has(building["id"]) or int(building["dano"]) >= 3:
			return false
	return _builder.standing_height(building) >= OCCLUDER_MIN_HEIGHT


## Vehículos y árboles (o los detalles del tránsito) del sector como instancias: una
## MultiMesh por modelo. Cada instancia es una transformación, o un par (transformación,
## color).
func _add_props(sector_node: Node3D, props: Dictionary, holder_name: String = "Objetos") -> void:
	if props.is_empty():
		return
	var holder: Node3D = Node3D.new()
	holder.name = holder_name
	sector_node.add_child(holder)
	for model: String in props:
		var instances: Array = props[model]
		var multimesh: MultiMesh = MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.use_colors = true
		multimesh.mesh = _models[model][0]
		multimesh.instance_count = instances.size()
		for i: int in instances.size():
			var entry: Variant = instances[i]
			var placed: Transform3D = entry[0] if entry is Array else entry
			placed.origin -= sector_node.position
			multimesh.set_instance_transform(i, placed)
			multimesh.set_instance_color(i, entry[1] if entry is Array else Color.WHITE)
		var node: MultiMeshInstance3D = MultiMeshInstance3D.new()
		node.name = model.capitalize().replace(" ", "")
		node.multimesh = multimesh
		node.material_override = _models[model][1]
		node.visibility_range_end = SMALL_DISTANCE if model in SMALL_DETAILS else props_distance
		holder.add_child(node)
		node.visibility_parent = NodePath("../../Lejos")
		var counter: String = "arboles" if model.begins_with("arbol") else "vehiculos"
		if holder_name == "Objetos":
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
	for kind: String in TRANSIT_MATERIALS:
		var settings: Array = TRANSIT_MATERIALS[kind]
		# La pintura vial se recorta por el alfa de su textura: queda a trozos.
		var shader: String = "tinta_transito_recorte" if kind == "pintura" else "tinta_transito"
		var material: ShaderMaterial = _shader_material(shader, ramps, settings[1])
		if not String(settings[0]).is_empty():
			material.set_shader_parameter(
				"albedo_texture", load(PAVEMENTS_DIR + String(settings[0]) + ".png")
			)
		if kind == "metal":
			material.set_shader_parameter("ramp_row", 4)
		_materials[kind] = material


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


## Las mallas de los modelos que se repiten (los vehículos y los árboles) y la caja de lo
## que no tiene modelo, con sus materiales. De cada vehículo se apunta también su caja de
## colisión: es su medida, y con ella se escala a lo que mide en el plano.
func _load_models() -> void:
	for model: String in PROP_MODELS + CityProps.VEHICLE_MODELS:
		var scene: Node = (load(MODELS_DIR + model + ".glb") as PackedScene).instantiate()
		var found: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)
		var mesh_instance: MeshInstance3D = found[0] as MeshInstance3D
		_models[model] = [mesh_instance.mesh, mesh_instance.get_surface_override_material(0)]
		for node: Node in scene.find_children("*", "CollisionShape3D", true, false):
			var shape: CollisionShape3D = node as CollisionShape3D
			if shape.shape is BoxShape3D and model in CityProps.VEHICLE_MODELS:
				var size: Vector3 = (shape.shape as BoxShape3D).size
				_props.model_boxes[model] = AABB(shape.position - size * 0.5, size)
		scene.free()
	var box: BoxMesh = BoxMesh.new()
	box.size = Vector3.ONE
	_models["caja"] = [box, load(BOX_MATERIAL)]
	_load_detail_models()


## Los detalles del tránsito (modelos de tools/blender/recipes/transito.py): tapas de
## registro y sumideros de fundición (sin nieve: el calor de la alcantarilla la funde), los
## pozos abiertos y las tapas tiradas, los bordillos sueltos, traviesas de hormigón y de
## madera, corazones y palancas de los desvíos y topes. Lo que cayó en los socavones y los
## baches (tools/blender/recipes/deterioro.py): trozos de asfalto y losas rotas, la tubería,
## el colector o la galería reventados y el charco helado. Lo tirado por la calle (cascotes,
## ladrillos, basura, contenedores, montones de escombros) y las farolas, rotas o no. Y los
## matojos secos.
func _load_detail_models() -> void:
	var snow: Dictionary = {
		"tapa_redonda": 0.0,
		"tapa_cuadrada": 0.0,
		"sumidero": 0.0,
		"traviesa": 0.6,
		"traviesa_madera": 0.6,
		"corazon_1_9": 0.35,
		"corazon_1_6": 0.35,
		"palanca_aguja": 0.5,
		"tope": 0.6,
		"placa_asfalto_a": 0.6,
		"placa_asfalto_b": 0.6,
		"placa_asfalto_c": 0.6,
		"losa_rota_a": 0.6,
		"losa_rota_b": 0.6,
		"tuberia_rota": 0.3,
		"colector_roto": 0.45,
		"canal_calefaccion": 0.45,
		"charco_helado": 0.2,
		"pozo_redondo": 0.0,
		"pozo_cuadrado": 0.0,
		"tapa_suelta_redonda": 0.2,
		"tapa_suelta_cuadrada": 0.2,
		"bordillo_suelto": 0.5,
		"bache_a": 0.3,
		"bache_b": 0.3,
		"bache_c": 0.3,
		"cascotes_a": 0.55,
		"cascotes_b": 0.55,
		"cascotes_c": 0.55,
		"ladrillos": 0.5,
		"neumatico": 0.4,
		"carton": 0.5,
		"rama": 0.4,
		"contenedor": 0.4,
		"escombros": 0.6,
		"escombros_grande": 0.6,
		"farola": 0.3,
		"farola_torcida": 0.3,
		"farola_mocha": 0.3,
		"poste_tendido": 0.3,
		"poste_tendido_partido": 0.3,
		"poste_tendido_punta": 0.4,
	}
	for model: String in snow:
		var scene: Node = (load(MODELS_DIR + model + ".glb") as PackedScene).instantiate()
		var found: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)
		var material: ShaderMaterial = _shader_material(
			"tinta", load(RAMPS) as Texture2D, float(snow[model])
		)
		if (
			model.begins_with("tapa")
			or model.begins_with("corazon")
			or model.begins_with("pozo")
			or model.begins_with("farola")
			or model.begins_with("poste")
			or model in ["sumidero", "tuberia_rota", "contenedor"]
		):
			material.set_shader_parameter("ramp_row", 4)
		_models[model] = [(found[0] as MeshInstance3D).mesh, material]
		scene.free()
	_models["matojo"] = [_tuft_mesh(), _tuft_material()]


## Un matojo: tres planos cruzados (0,8 m de ancho y 0,6 de alto) con la mata de hierba
## seca de assets/textures/pavimentos/matojo.png; las normales, hacia arriba (la luz no
## dibuja los planos). El origen, abajo en el centro.
static func _tuft_mesh() -> ArrayMesh:
	var points: PackedVector3Array = PackedVector3Array()
	var normals: PackedVector3Array = PackedVector3Array()
	var uvs: PackedVector2Array = PackedVector2Array()
	var indices: PackedInt32Array = PackedInt32Array()
	for k: int in 3:
		var across: Vector3 = Vector3(cos(k * PI / 3.0), 0.0, sin(k * PI / 3.0)) * TUFT_SIZE.x * 0.5
		var base: int = points.size()
		var up: Vector3 = Vector3.UP * TUFT_SIZE.y
		points.append_array([-across, across, across + up, -across + up])
		uvs.append_array(
			[Vector2(0.0, 1.0), Vector2(1.0, 1.0), Vector2(1.0, 0.0), Vector2(0.0, 0.0)]
		)
		for _n: int in 4:
			normals.append(Vector3.UP)
		indices.append_array([base, base + 1, base + 2, base, base + 2, base + 3])
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = points
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: ArrayMesh = ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


func _tuft_material() -> ShaderMaterial:
	var material: ShaderMaterial = _shader_material("tinta_recorte", load(RAMPS) as Texture2D, 0.1)
	material.set_shader_parameter("albedo_texture", load(PAVEMENTS_DIR + "matojo.png"))
	material.set_shader_parameter("use_vertex_color", false)
	return material
