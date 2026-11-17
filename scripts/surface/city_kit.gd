class_name CityKit
extends RefCounted
## Los edificios del kit de arquitectura (F3-16) en la maqueta: monta con BuildingKit los
## que sabe montar (las viviendas de las cuatro familias y los singulares), cada uno con su
## ficha del plano, y prepara lo que necesita el terreno a su alrededor.
##
## - En ladera, la maqueta baja los muros de cada volumen hasta el punto más bajo de su
##   huella ("cota_min"); el kit pone el edificio a su cota. Para que no floten por el lado
##   de abajo, llevan un zócalo de cimentación ([method plinth]).
## - Los singulares que bajan bajo la calle (el foso de las escaleras del vestíbulo del
##   metro) dicen dónde no va el terreno (KitSingular, "kit_huecos"): no se dibuja
##   ([method cut_holes]) y su colisión se hunde ([method carve]).
## - Lo que va metido en los huecos de las fachadas (ventanas, puertas, escaparates y los
##   cuartos de detrás) no proyecta sombra: la sombra de un hueco la hace su muro, y en una
##   calle la mitad de las mallas del kit son eso ([const SHADOWLESS]).

## A partir de qué desnivel bajo la huella lleva zócalo un edificio.
const PLINTH_DROP: float = 0.15
## Cuánto baja el zócalo por debajo del punto más bajo de la huella.
const PLINTH_FOOT: float = 0.4
const PLINTH_COLOR: Color = Color("#6a655e")
## Cuánto se hunde la colisión del relieve bajo un hueco.
const HOLE_DEPTH: float = 40.0
## Cuánto se mete hacia dentro el volumen que proyecta la sombra de un edificio a media
## distancia ([method inset]).
const SHADOW_INSET: float = 0.4
## Las piezas que no proyectan sombra (por cómo empieza su nombre): lo que va en los huecos.
const SHADOWLESS: PackedStringArray = [
	"ventana",
	"puerta",
	"escaparate",
	"cocina",
	"escalera_",
	"habitacion",
	"tienda_interior",
	"logia_acristalada",
	"reja_",
]

var plan: CityPlan
var kit: BuildingKit
## Los triángulos (de tres en tres, en coordenadas de plano) de los huecos del terreno.
var holes: PackedVector2Array = PackedVector2Array()

var _courtyards: PackedVector2Array = PackedVector2Array()
var _hole_boxes: Array[Rect2] = []


func _init(city_plan: CityPlan) -> void:
	plan = city_plan
	kit = BuildingKit.new()
	for courtyard: Dictionary in plan.data.get("patios", []):
		_courtyards.append(CityGeometry.centroid(CityPlan.ring(courtyard["forma"][0])))
	for building: Dictionary in plan.data["edificios"]:
		var id: String = building["id"]
		if not KitSingular.MODELS.has(id):
			continue
		var hole: String = String(KitSingular.MODELS[id]) + KitSingular.HOLE_SUFFIX
		var meshes: Dictionary = kit.meshes_for(building["tipo"])
		if meshes.has(hole):
			var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
			var triangles: PackedVector2Array = KitSingular.holes_of(meshes[hole], center)
			holes.append_array(triangles)
	for i: int in range(0, holes.size() - 2, 3):
		_hole_boxes.append(Rect2(holes[i], Vector2.ZERO).expand(holes[i + 1]).expand(holes[i + 2]))


## ¿Lo monta el kit?
func supports(building: Dictionary) -> bool:
	return BuildingKit.supports_building(building)


## El edificio montado con el kit, con su origen en el centro de su ficha y a la cota 0
## (quien lo pone lo sube a la suya). Los singulares llevan dentro su colisión ("Colision").
func build(building: Dictionary) -> Node3D:
	var anchor: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	var spec: Dictionary = {
		"tipo": building["tipo"],
		"clave": building["id"],
		"huella": CityPlan.ring(building["huella"][0]),
		"centro": anchor,
		"origen": anchor,
		"pisos": int(building["pisos"]),
		"dano": int(building["dano"]),
		"incendio": building["incendio"],
		"patios": _courtyards,
		"arco": String(building.get("notas", "")).contains("Arco"),
		"bomba": plan.ground_zero(),
	}
	var model: Node3D = kit.build(spec)
	for piece: Node in model.get_children():
		if piece is GeometryInstance3D and casts_no_shadow(String(piece.name)):
			(piece as GeometryInstance3D).cast_shadow = (
				GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			)
	return model


## La ficha de un edificio con la huella metida [const SHADOW_INSET] hacia dentro (para el
## volumen que proyecta su sombra a media distancia sin quitarle la luz a su fachada). Si
## la huella es tan estrecha que desaparece, la de siempre.
func inset(building: Dictionary) -> Dictionary:
	var outline: PackedVector2Array = CityGeometry.clean(CityPlan.ring(building["huella"][0]))
	var largest: PackedVector2Array = PackedVector2Array()
	for polygon: PackedVector2Array in Geometry2D.offset_polygon(outline, -SHADOW_INSET):
		if absf(CityGeometry.signed_area(polygon)) > absf(CityGeometry.signed_area(largest)):
			largest = polygon
	if largest.size() < 3:
		return building
	var points: Array = []
	for point: Vector2 in largest:
		points.append([point.x, point.y])
	points.append([largest[0].x, largest[0].y])
	var result: Dictionary = building.duplicate()
	result["huella"] = [points]
	return result


## ¿Es una pieza de las que van en los huecos (y no proyectan sombra)?
static func casts_no_shadow(piece: String) -> bool:
	for prefix: String in SHADOWLESS:
		if piece.begins_with(prefix):
			return true
	return false


## El zócalo de un edificio en ladera: la huella extruida desde un poco por debajo de su
## punto más bajo hasta su cota, en el espacio del edificio (origen en el centro de la
## ficha, a la cota 0). Vacío si el suelo bajo la huella es casi llano.
func plinth(building: Dictionary) -> MeshBuffer:
	var mesh: MeshBuffer = MeshBuffer.new()
	var ground: float = building["cota"]
	var drop: float = ground - float(building["cota_min"])
	if drop < PLINTH_DROP:
		return mesh
	var anchor: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	var outline: PackedVector2Array = CityGeometry.clean(CityPlan.ring(building["huella"][0]))
	var top: float = -0.01
	var bottom: float = -drop - PLINTH_FOOT
	var tint: PackedColorArray = PackedColorArray([PLINTH_COLOR.srgb_to_linear()])
	var center: Vector3 = Vector3.ZERO
	for i: int in outline.size():
		var a: Vector2 = outline[i] - anchor
		var b: Vector2 = outline[(i + 1) % outline.size()] - anchor
		var face: PackedVector3Array = PackedVector3Array(
			[
				Vector3(a.x, bottom, -a.y),
				Vector3(b.x, bottom, -b.y),
				Vector3(b.x, top, -b.y),
				Vector3(a.x, top, -a.y),
			]
		)
		var middle: Vector3 = (face[0] + face[1]) / 2.0
		var outward: Vector3 = Vector3(middle.x - center.x, 0.0, middle.z - center.z)
		var side: Vector3 = (face[1] - face[0]).cross(Vector3.UP)
		mesh.add_face(face, side if side.dot(outward) >= 0.0 else -side, tint)
	return mesh


## Marca como huecos (los dos triángulos de cada celda de la rejilla de [param step] metros)
## las celdas que caen del todo dentro de los huecos de los singulares. [param cells] es
## el tamaño de la rejilla. Devuelve la máscara nueva.
func cut_holes(mask: PackedByteArray, cells: Vector2i, step: float) -> PackedByteArray:
	var result: PackedByteArray = mask.duplicate()
	if result.size() < cells.x * cells.y * 2:
		result.resize(cells.x * cells.y * 2)
	for box: Rect2 in _hole_boxes:
		var first: Vector2i = Vector2i((box.position / step).floor())
		var last: Vector2i = Vector2i((box.end / step).ceil())
		for j: int in range(maxi(first.y, 0), mini(last.y, cells.y)):
			for i: int in range(maxi(first.x, 0), mini(last.x, cells.x)):
				var corner: Vector2 = Vector2(i, j) * step
				var square: Array[Vector2] = [
					corner,
					corner + Vector2(step, 0.0),
					corner + Vector2(step, step),
					corner + Vector2(0.0, step),
				]
				if square.all(func(point: Vector2) -> bool: return inside(point)):
					var id: int = (j * cells.x + i) * 2
					result[id] = 1
					result[id + 1] = 1
	return result


## Hunde la colisión del relieve bajo los huecos: [param heights] son las alturas de una
## rejilla de [param n] × [param n] puntos cada [param step] metros desde [param corner].
func carve(heights: PackedFloat32Array, corner: Vector2, n: int, step: float) -> void:
	var area: Rect2 = Rect2(corner, Vector2.ONE * step * (n - 1))
	for box: Rect2 in _hole_boxes:
		if not area.intersects(box):
			continue
		var first: Vector2i = Vector2i(((box.position - corner) / step).floor())
		var last: Vector2i = Vector2i(((box.end - corner) / step).ceil())
		for j: int in range(maxi(first.y, 0), mini(last.y + 1, n)):
			for i: int in range(maxi(first.x, 0), mini(last.x + 1, n)):
				if inside(corner + Vector2(i, j) * step):
					heights[j * n + i] = minf(heights[j * n + i], -HOLE_DEPTH)


## ¿Cae el punto del plano dentro de algún hueco?
func inside(point: Vector2) -> bool:
	for k: int in _hole_boxes.size():
		if not _hole_boxes[k].grow(0.001).has_point(point):
			continue
		var i: int = k * 3
		if Geometry2D.point_is_inside_triangle(point, holes[i], holes[i + 1], holes[i + 2]):
			return true
	return false
