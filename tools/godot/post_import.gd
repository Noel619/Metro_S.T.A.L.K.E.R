@tool
extends EditorScenePostImport
## Post-importación de los modelos .glb que generan las recetas de Blender.
##
## Convenciones de nombre (las pone la receta, ver tools/blender/):
## - Nodo que termina en "-fisico": pasa a ser un [RigidBody3D].
## - Nodo que termina en "-estatico": pasa a ser un [StaticBody3D].
## - Malla que termina en "-colcaja": se sustituye por una colisión de caja.
## - Malla que termina en "-colconvexa": se sustituye por una colisión convexa.
## - Materiales: si existe res://assets/materials/<nombre>.tres se usa ese; si
##   no, el material base, que pinta con los colores por vértice.

const MATERIALS_DIR: String = "res://assets/materials/"
const DEFAULT_MATERIAL_PATH: String = "res://assets/materials/base_vertex.tres"
const RIGID_SUFFIX: String = "-fisico"
const STATIC_SUFFIX: String = "-estatico"
const BOX_COLLISION_SUFFIX: String = "-colcaja"
const CONVEX_COLLISION_SUFFIX: String = "-colconvexa"


func _post_import(scene: Node) -> Object:
	for node: Node in _find_by_suffix(scene, RIGID_SUFFIX):
		_replace_with_body(node, RigidBody3D.new(), RIGID_SUFFIX)
	for node: Node in _find_by_suffix(scene, STATIC_SUFFIX):
		_replace_with_body(node, StaticBody3D.new(), STATIC_SUFFIX)
	for node: Node in _find_by_suffix(scene, BOX_COLLISION_SUFFIX):
		_replace_with_collision(node, true)
	for node: Node in _find_by_suffix(scene, CONVEX_COLLISION_SUFFIX):
		_replace_with_collision(node, false)
	_assign_materials(scene)
	_set_owner_recursive(scene, scene)
	return scene


func _find_by_suffix(root: Node, suffix: String) -> Array[Node]:
	var found: Array[Node] = []
	for child: Node in root.get_children():
		found.append_array(_find_by_suffix(child, suffix))
		if String(child.name).ends_with(suffix):
			found.append(child)
	return found


func _replace_with_body(node: Node, body: CollisionObject3D, suffix: String) -> void:
	var source: Node3D = node as Node3D
	body.name = String(source.name).trim_suffix(suffix)
	body.transform = source.transform
	var parent: Node = source.get_parent()
	# El cuerpo entra primero en la escena para que los hijos no pierdan a su dueño.
	parent.add_child(body)
	parent.move_child(body, source.get_index())
	for child: Node in source.get_children():
		child.reparent(body, false)
	parent.remove_child(source)
	source.free()


func _replace_with_collision(node: Node, as_box: bool) -> void:
	var mesh_instance: MeshInstance3D = node as MeshInstance3D
	if mesh_instance == null or mesh_instance.mesh == null:
		push_warning("'%s' no es una malla; se ignora." % node.name)
		return
	var parent: Node = mesh_instance.get_parent()
	if not parent is CollisionObject3D:
		push_warning("La colisión '%s' no cuelga de un cuerpo físico." % mesh_instance.name)
	var shape_node: CollisionShape3D = CollisionShape3D.new()
	var suffix: String = BOX_COLLISION_SUFFIX if as_box else CONVEX_COLLISION_SUFFIX
	shape_node.name = String(mesh_instance.name).trim_suffix(suffix) + "_colision"
	if as_box:
		var bounds: AABB = mesh_instance.mesh.get_aabb()
		var box: BoxShape3D = BoxShape3D.new()
		box.size = bounds.size
		shape_node.shape = box
		shape_node.transform = mesh_instance.transform * Transform3D(Basis(), bounds.get_center())
	else:
		shape_node.shape = mesh_instance.mesh.create_convex_shape(true, true)
		shape_node.transform = mesh_instance.transform
	var index: int = mesh_instance.get_index()
	parent.remove_child(mesh_instance)
	parent.add_child(shape_node)
	parent.move_child(shape_node, index)
	mesh_instance.free()


func _assign_materials(root: Node) -> void:
	for child: Node in root.get_children():
		_assign_materials(child)
	var mesh_instance: MeshInstance3D = root as MeshInstance3D
	if mesh_instance == null or mesh_instance.mesh == null:
		return
	for surface: int in mesh_instance.mesh.get_surface_count():
		var imported: Material = mesh_instance.mesh.surface_get_material(surface)
		var material_name: String = imported.resource_name if imported else ""
		var path: String = MATERIALS_DIR + material_name + ".tres"
		if material_name.is_empty() or not ResourceLoader.exists(path):
			path = DEFAULT_MATERIAL_PATH
		if ResourceLoader.exists(path):
			mesh_instance.set_surface_override_material(surface, load(path))


func _set_owner_recursive(node: Node, owner_node: Node) -> void:
	for child: Node in node.get_children():
		child.owner = owner_node
		_set_owner_recursive(child, owner_node)
