class_name CityRiver
extends RefCounted
## El río helado y su agua (data/ciudad/rio.json, de tools/ciudad/rio.py), levantados por
## sectores: la superficie del agua abierta (con su aguanieve junto al hielo, para
## agua.gdshader) y las placas de hielo con su grosor, el de orilla, el fino, los témpanos
## rotos del borde y los sueltos. El hielo tiene colisión (se pisa); el agua, no: debajo
## está el lecho, que es el relieve.

## Color de la cara de arriba de cada clase de placa; el alfa, cuánta nieve la cubre.
## El hielo de orilla, gris azulado y con la nieve a parches (el viento la barre: el río se
## distingue de la tierra nevada); el fino, oscuro, casi sin nieve.
const TOP_COLORS: Dictionary = {
	"hielo": Color(0.58, 0.65, 0.69, 0.45),
	"fino": Color(0.3, 0.36, 0.4, 0.18),
	"temano": Color(0.6, 0.67, 0.71, 0.35),
	"suelto": Color(0.68, 0.74, 0.78, 0.25),
}
## Los cantos del hielo: azulados y sin nieve.
const SIDE_COLOR: Color = Color(0.5, 0.6, 0.64, 0.0)
## El río visto de lejos: una lámina al nivel del hielo.
const FAR_COLOR: Color = Color(0.7, 0.74, 0.76, 1.0)

var plan: CityPlan
## Por sector (Vector2i), en su espacio (el origen en su centro): la malla del agua, la del
## hielo, las caras de colisión del hielo (de tres en tres) y el río visto de lejos.
var water: Dictionary = {}
var ice: Dictionary = {}
var collision: Dictionary = {}
var far: Dictionary = {}
var stats: Dictionary = {"triangulos_agua": 0, "placas": 0}


func _init(city_plan: CityPlan) -> void:
	plan = city_plan


## Levanta el agua, el hielo y la lámina de lejos (si el plano trae el río).
func build() -> void:
	if plan.river.is_empty():
		return
	_build_water(plan.river["superficie"], float(plan.river["agua"]))
	_build_ice(plan.river["placas"])
	_build_far(float(plan.river["hielo"]))


## La superficie del agua, triángulo a triángulo en el sector de su centro. El alfa del color
## de cada vértice es el aguanieve (1 junto al hielo).
func _build_water(surface: Dictionary, level: float) -> void:
	var flat: Array = surface["puntos"]
	var triangles: Array = surface["triangulos"]
	var slush: Array = surface["orilla"]
	var points: PackedVector3Array = PackedVector3Array()
	points.resize(3)
	var colors: PackedColorArray = PackedColorArray()
	colors.resize(3)
	var normals: PackedVector3Array = PackedVector3Array([Vector3.UP, Vector3.UP, Vector3.UP])
	var uvs: PackedVector2Array = PackedVector2Array([Vector2.ZERO, Vector2.ZERO, Vector2.ZERO])
	var corners: PackedVector2Array = PackedVector2Array()
	corners.resize(3)
	for t: int in range(0, triangles.size(), 3):
		for k: int in 3:
			var v: int = int(triangles[t + k])
			corners[k] = Vector2(flat[v * 2], flat[v * 2 + 1])
			colors[k] = Color(1.0, 1.0, 1.0, float(slush[v]))
		var sector: Vector2i = plan.sector_of((corners[0] + corners[1] + corners[2]) / 3.0)
		var origin: Vector2 = plan.sector_rect(sector).get_center()
		for k: int in 3:
			points[k] = Vector3(corners[k].x - origin.x, level, origin.y - corners[k].y)
		_buffer(water, sector).add_polygon(points, normals, Color.WHITE, uvs, colors)
	stats["triangulos_agua"] = triangles.size() / 3


## Las placas de hielo: la cara de arriba (un plano, inclinado en los témpanos) y los cantos
## de cada anillo de su contorno hasta su grosor, con su colisión. Cada triángulo y cada
## canto van al sector de su centro (el hielo de orilla recorre el río entero).
func _build_ice(plates: Dictionary) -> void:
	var classes: Array = plates["clases"]
	for index: int in plates["clase"].size():
		var kind: String = classes[int(plates["clase"][index])]
		var flat: Array = plates["puntos"][index]
		var outline: PackedVector2Array = PackedVector2Array()
		for k: int in range(0, flat.size(), 2):
			outline.append(Vector2(flat[k], flat[k + 1]))
		var plane: Vector4 = Vector4(
			float(plates["z"][index]), float(plates["gx"][index]), float(plates["gy"][index]), 0.0
		)
		var center: Vector2 = Vector2(float(plates["cx"][index]), float(plates["cy"][index]))
		var thickness: float = float(plates["grosor"][index])
		_ice_top(outline, plates["triangulos"][index], plane, center, TOP_COLORS[kind])
		_ice_sides(outline, plates["anillos"][index], plane, center, thickness)
	stats["placas"] = plates["clase"].size()


func _ice_top(
	outline: PackedVector2Array, triangles: Array, plane: Vector4, center: Vector2, color: Color
) -> void:
	var face: PackedVector3Array = PackedVector3Array()
	face.resize(3)
	var tint: PackedColorArray = PackedColorArray([color])
	for t: int in range(0, triangles.size(), 3):
		var a: Vector2 = outline[int(triangles[t])]
		var b: Vector2 = outline[int(triangles[t + 1])]
		var c: Vector2 = outline[int(triangles[t + 2])]
		var sector: Vector2i = plan.sector_of((a + b + c) / 3.0)
		var origin: Vector2 = plan.sector_rect(sector).get_center()
		face[0] = _local(a, _height(plane, center, a), origin)
		face[1] = _local(b, _height(plane, center, b), origin)
		face[2] = _local(c, _height(plane, center, c), origin)
		_buffer(ice, sector).add_face(face, Vector3.UP, tint)
		_collide(sector, face)


func _ice_sides(
	outline: PackedVector2Array, rings: Array, plane: Vector4, center: Vector2, thickness: float
) -> void:
	var quad: PackedVector3Array = PackedVector3Array()
	quad.resize(4)
	var tint: PackedColorArray = PackedColorArray([SIDE_COLOR])
	var start: int = 0
	for ring_size: Variant in rings:
		var count: int = int(ring_size)
		for k: int in count:
			var a: Vector2 = outline[start + k]
			var b: Vector2 = outline[start + (k + 1) % count]
			var sector: Vector2i = plan.sector_of((a + b) * 0.5)
			var origin: Vector2 = plan.sector_rect(sector).get_center()
			var top_a: float = _height(plane, center, a)
			var top_b: float = _height(plane, center, b)
			quad[0] = _local(a, top_a, origin)
			quad[1] = _local(b, top_b, origin)
			quad[2] = _local(b, top_b - thickness, origin)
			quad[3] = _local(a, top_a - thickness, origin)
			# Los anillos van con el hielo a la izquierda: fuera queda a la derecha.
			var outward: Vector2 = Vector2(b.y - a.y, a.x - b.x)
			_buffer(ice, sector).add_face(quad, Vector3(outward.x, 0.0, -outward.y), tint)
			_collide(sector, PackedVector3Array([quad[0], quad[1], quad[2]]))
			_collide(sector, PackedVector3Array([quad[0], quad[2], quad[3]]))
		start += count


## De lejos, el río es una lámina al nivel del hielo (si no, se vería el lecho).
func _build_far(level: float) -> void:
	var outline: PackedVector2Array = CityPlan.ring(plan.data["rio"]["poligono"][0])
	var triangles: PackedInt32Array = Geometry2D.triangulate_polygon(outline)
	var face: PackedVector3Array = PackedVector3Array()
	face.resize(3)
	var tint: PackedColorArray = PackedColorArray([FAR_COLOR])
	for t: int in range(0, triangles.size(), 3):
		var a: Vector2 = outline[triangles[t]]
		var b: Vector2 = outline[triangles[t + 1]]
		var c: Vector2 = outline[triangles[t + 2]]
		var sector: Vector2i = plan.sector_of((a + b + c) / 3.0)
		var origin: Vector2 = plan.sector_rect(sector).get_center()
		face[0] = _local(a, level, origin)
		face[1] = _local(b, level, origin)
		face[2] = _local(c, level, origin)
		_buffer(far, sector).add_face(face, Vector3.UP, tint)


func _collide(sector: Vector2i, triangle: PackedVector3Array) -> void:
	var faces: PackedVector3Array = collision.get(sector, PackedVector3Array())
	faces.append_array(triangle)
	collision[sector] = faces


static func _height(plane: Vector4, center: Vector2, point: Vector2) -> float:
	return plane.x + plane.y * (point.x - center.x) + plane.z * (point.y - center.y)


static func _local(point: Vector2, height: float, origin: Vector2) -> Vector3:
	return Vector3(point.x - origin.x, height, origin.y - point.y)


static func _buffer(by_sector: Dictionary, sector: Vector2i) -> MeshBuffer:
	if not by_sector.has(sector):
		by_sector[sector] = MeshBuffer.new()
	return by_sector[sector]
