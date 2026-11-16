class_name KitSingular
extends KitRules
## Los edificios singulares: los hitos y los sitios clave que no siguen ninguna serie (el
## vestíbulo del metro, la Casa de los Sóviets, el Edificio Partido…). Cada uno es un modelo
## entero, con su biblioteca y su receta (tools/blender/recipes/singular_*.py), hecho en el
## marco del plano (x al este, y al norte, z arriba) alrededor del "centro" de su ficha. Se
## pone tal cual, sin girarlo ni estirarlo, a la cota del edificio.
##
## Las piezas de un modelo son las mallas de la biblioteca que se llaman como él o empiezan
## por su nombre y un guion bajo. Dos no se dibujan:
## - "<modelo>_colision": su colisión, hecha a mano (suelos, muros, columnas; los escalones
##   y las escaleras son rampas), más sencilla que lo que se ve.
## - "<modelo>_hueco" (si la tiene): dónde no va el terreno, porque el edificio baja bajo la
##   cota de la calle (el foso de unas escaleras, un sótano abierto). Sus triángulos, en
##   coordenadas de plano, quedan en los metadatos del edificio ("kit_huecos"), para que
##   quien pone el suelo lo recorte.
##
## Están en el estado que fija el plano (el daño de los sitios clave se decide a mano), así
## que no tienen variantes.

## id del plano -> nombre del modelo.
const MODELS: Dictionary = {
	"PLZ-06": "vestibulo",
	"ZC-01": "partido",
	"CEN-SOV": "soviets",
	"CEN-SOVT": "torre_soviets",
}
const COLLISION_SUFFIX: String = "_colision"
const HOLE_SUFFIX: String = "_hueco"


func build(parent: Node3D) -> void:
	var model: String = MODELS[key]
	var outline: PackedVector2Array = CityGeometry.clean(spec["huella"])
	var center: Vector2 = spec.get("centro", CityGeometry.centroid(outline))
	_origin = spec.get("origen", center)
	var place: Transform3D = Transform3D(Basis(), _local(center, 0.0))
	var data: Color = Color(clampf(0.15 + 0.22 * damage, 0.0, 1.0), 0.0, 0.0, 0.0)
	var pieces: PackedStringArray = pieces_of(model, assembly.meshes)
	if pieces.is_empty():
		assembly.missing.append(model)
	for piece: String in pieces:
		assembly.put(piece, place, Color.WHITE, data)
	var hole: String = model + HOLE_SUFFIX
	if assembly.meshes.has(hole):
		parent.set_meta(&"kit_huecos", holes_of(assembly.meshes[hole], center))
	var collision: String = model + COLLISION_SUFFIX
	if not assembly.meshes.has(collision):
		assembly.missing.append(collision)
		return
	var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	shape.backface_collision = true
	shape.set_faces((assembly.meshes[collision] as Mesh).get_faces())
	var holder: CollisionShape3D = CollisionShape3D.new()
	holder.name = "Forma"
	holder.shape = shape
	holder.position = place.origin
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Colision"
	parent.add_child(body)
	body.add_child(holder)


## Las piezas que se dibujan de un modelo, en orden.
static func pieces_of(model: String, meshes: Dictionary) -> PackedStringArray:
	var result: PackedStringArray = []
	for name: String in meshes:
		if name.ends_with(COLLISION_SUFFIX) or name.ends_with(HOLE_SUFFIX):
			continue
		if name == model or name.begins_with(model + "_"):
			result.append(name)
	result.sort()
	return result


## Los triángulos (de tres en tres) del hueco del terreno de un modelo puesto en
## [param center], en coordenadas de plano.
static func holes_of(mesh: Mesh, center: Vector2) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for vertex: Vector3 in mesh.get_faces():
		result.append(center + Vector2(vertex.x, -vertex.z))
	return result
