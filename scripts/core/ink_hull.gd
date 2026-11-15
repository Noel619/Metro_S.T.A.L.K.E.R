class_name InkHull
extends RefCounted
## Contorno por casco invertido para objetos clave, personas y criaturas (F1-03).
##
## A cada malla de un nodo le añade una copia (el casco) con las normales
## suavizadas: los vértices que comparten posición promedian su normal, así el
## casco no se abre en las esquinas de las piezas con aristas vivas. El shader
## contorno_casco.gdshader lo hincha unos píxeles y lo pinta de tinta por detrás.
## Las mallas del casco se guardan en caché: cada malla se procesa una sola vez.

const SHADER: Shader = preload("res://assets/shaders/contorno_casco.gdshader")
const NOISE: Texture2D = preload("res://assets/textures/ruido_trazo.png")
const SUFFIX: String = "_contorno"
## Precisión con la que se considera que dos vértices están en el mismo sitio.
const WELD: float = 1000.0

static var _meshes: Dictionary = {}
static var _materials: Dictionary = {}


## Añade el contorno a todas las mallas de [param root] (y de sus hijos).
static func add_to(root: Node, width_px: float = 2.6) -> void:
	for node: Node in root.find_children("*", "MeshInstance3D", true, false):
		var source: MeshInstance3D = node as MeshInstance3D
		if source.mesh == null or source.name.ends_with(SUFFIX):
			continue
		if source.get_node_or_null(NodePath(source.name + SUFFIX)) != null:
			continue
		var hull: MeshInstance3D = MeshInstance3D.new()
		hull.name = source.name + SUFFIX
		hull.mesh = hull_mesh(source.mesh)
		hull.material_override = _material(width_px)
		hull.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		source.add_child(hull)


## Quita los contornos que haya añadido [method add_to].
static func remove_from(root: Node) -> void:
	for node: Node in root.find_children("*" + SUFFIX, "MeshInstance3D", true, false):
		node.queue_free()


## Copia de la malla con las normales suavizadas (solo posiciones, normales e índices).
static func hull_mesh(source: Mesh) -> ArrayMesh:
	if _meshes.has(source):
		return _meshes[source]
	var result: ArrayMesh = ArrayMesh.new()
	for surface: int in source.get_surface_count():
		var arrays: Array = source.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var sums: Dictionary = {}
		for i: int in vertices.size():
			var key: Vector3i = Vector3i((vertices[i] * WELD).round())
			sums[key] = sums.get(key, Vector3.ZERO) + normals[i]
		var smooth: PackedVector3Array = PackedVector3Array()
		smooth.resize(vertices.size())
		for i: int in vertices.size():
			var key: Vector3i = Vector3i((vertices[i] * WELD).round())
			smooth[i] = (sums[key] as Vector3).normalized()
		var hull_arrays: Array = []
		hull_arrays.resize(Mesh.ARRAY_MAX)
		hull_arrays[Mesh.ARRAY_VERTEX] = vertices
		hull_arrays[Mesh.ARRAY_NORMAL] = smooth
		hull_arrays[Mesh.ARRAY_INDEX] = arrays[Mesh.ARRAY_INDEX]
		result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, hull_arrays)
	_meshes[source] = result
	return result


static func _material(width_px: float) -> ShaderMaterial:
	if _materials.has(width_px):
		return _materials[width_px]
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = SHADER
	material.set_shader_parameter("grosor_px", width_px)
	material.set_shader_parameter("boil_noise", NOISE)
	_materials[width_px] = material
	return material
