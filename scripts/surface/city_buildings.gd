class_name CityBuildings
extends RefCounted
## Los edificios de la maqueta: cada edificio del plano como un volumen sencillo, a su
## altura y con lo que queda en pie según su daño.
##
## El daño sigue los niveles del plano (docs/CIUDAD.md): 1 · herido, entero; 2 · roto, se
## hunde el extremo que mira a la bomba (las últimas plantas); 3 · destripado, un cascarón
## de alturas desiguales; 4 · arrasado, muñones de una o dos plantas. Las torres, las
## chimeneas, los depósitos, las ruinas y los hitos conservan la altura que dice el plano
## (las excepciones a mano). Las casas de madera ardieron. Todo varía con la semilla de
## cada edificio (CityPlan.chance), siempre igual.
##
## Las fachadas llevan ventanas pintadas (el alfa del color marca dónde) y el hollín de
## los incendios oscurece la parte alta.

## El Edificio Partido: falta la mitad que miraba a la bomba.
const SPLIT_BY_BLAST: PackedStringArray = ["ZC-01"]
## Agujas dobladas por la onda: hacia dónde apunta la punta (grados desde el este).
const BENT_SPIRES: Dictionary = {"CEN-SOVT": 225.0}
## Tipos que conservan la altura del plano.
const KEEP_HEIGHT: PackedStringArray = [
	"chimenea",
	"torre",
	"torre_refrigeracion",
	"deposito_circular",
	"monton",
	"muralla",
	"ruina",
	"estadio",
	"tienda_campana",
]
## Grupos con ventanas, y el ancho de cada vano en metros.
const WINDOW_BAY: Dictionary = {
	"vivienda": 3.2, "servicios": 4.0, "especial": 4.2, "industria": 6.0, "madera": 3.0
}
## Color de cada tipo (sRGB). La nieve y el hollín se ponen encima; nunca blanco.
const COLORS: Dictionary = {
	"jrushchovka": Color("#8e897f"),
	"bloque9": Color("#88857f"),
	"torre16": Color("#83817c"),
	"estalinka": Color("#a08d70"),
	"estalinka_baja": Color("#998a70"),
	"prerrevolucion": Color("#8b604c"),
	"barracon": Color("#5f4b3b"),
	"casa_madera": Color("#5a4636"),
	"torre_estalinista": Color("#a59478"),
	"escuela": Color("#a2987c"),
	"guarderia": Color("#a0977f"),
	"comercio": Color("#8c897e"),
	"publico": Color("#9b8e77"),
	"monumental": Color("#a1927a"),
	"oficinas": Color("#8a8883"),
	"hospital": Color("#a19e90"),
	"hotel": Color("#86847e"),
	"nave": Color("#6e7476"),
	"almacen": Color("#76787a"),
	"industrial": Color("#7a7c7b"),
	"deposito_circular": Color("#7c7a75"),
	"torre_refrigeracion": Color("#8a877f"),
	"chimenea": Color("#7b6a5d"),
	"garajes": Color("#6c6964"),
	"cobertizo": Color("#6a665f"),
	"transformador": Color("#727470"),
	"quiosco": Color("#76705f"),
	"pabellon": Color("#928a78"),
	"iglesia": Color("#a0988a"),
	"torre": Color("#6c6a66"),
	"muralla": Color("#80614f"),
	"ruina": Color("#5e5a55"),
	"tienda_campana": Color("#6c6a52"),
	"monton": Color("#2f2c2b"),
	"estadio": Color("#7d7b75"),
}
## Metros que se entierran los muros por debajo del punto más bajo de la huella.
const FOUNDATION: float = 1.0

var plan: CityPlan


func _init(city_plan: CityPlan) -> void:
	plan = city_plan


## Los volúmenes que forman un edificio: cada uno con su planta ("outline", en sentido
## horario), su altura sobre la cota ("top") y su forma ("shape": flat, gable, taper,
## cooling, tower o mound; "ridge" es la altura de la cumbrera de las de dos aguas).
func pieces(building: Dictionary) -> Array[Dictionary]:
	var outline: PackedVector2Array = CityGeometry.clean(CityPlan.ring(building["huella"][0]))
	var kind: String = building["tipo"]
	var info: Dictionary = plan.data["tipos"][kind]
	var height: float = building["altura"]
	var shape: String = _shape_for(kind, outline)
	var keeps_height: bool = (
		kind in KEEP_HEIGHT or CityPlan.is_landmark(building) or info["grupo"] == "menor"
	)
	if building["id"] in SPLIT_BY_BLAST:
		return _split_by_blast(outline, height)
	if keeps_height:
		return [_piece(outline, height, shape, building)]
	if info["grupo"] == "madera":
		return [_burnt_wood(outline, building, shape)]
	var result: Array[Dictionary] = [_piece(outline, height, shape, building)]
	match int(building["dano"]):
		2:
			result = _collapsed_end(outline, building, shape)
		3:
			result = _slices(outline, building, 0.45, 1.0)
		4:
			result = _slices(outline, building, -1.0, -1.0)
	return result


## La malla del edificio, con el origen en [param origin] (un punto del plano a la cota 0).
func build(building: Dictionary, origin: Vector2) -> MeshBuffer:
	var mesh: MeshBuffer = MeshBuffer.new()
	var info: Dictionary = plan.data["tipos"][building["tipo"]]
	var ground: float = building["cota"]
	var bottom: float = float(building["cota_min"]) - FOUNDATION
	var style: Dictionary = _style(building, info)
	for piece: Dictionary in pieces(building):
		var outline: PackedVector2Array = piece["outline"]
		var top: float = ground + float(piece["top"])
		match String(piece["shape"]):
			"gable":
				_walls(mesh, outline, outline, Vector2(bottom, top), style, origin)
				_gable_roof(mesh, outline, top, ground + float(piece["ridge"]), style, origin)
			"taper":
				var thin: PackedVector2Array = _shrunk(outline, 0.55)
				_walls(mesh, outline, thin, Vector2(bottom, top), style, origin)
				_cap(mesh, thin, top, style["roof"], origin)
			"mound":
				var flat: PackedVector2Array = _shrunk(outline, 0.5)
				_walls(mesh, outline, flat, Vector2(bottom, top), style, origin)
				_cap(mesh, flat, top, style["roof"], origin)
			"cooling":
				_cooling_tower(mesh, outline, Vector2(bottom, top), style, origin)
			"tower":
				_tower(mesh, building, outline, Vector2(bottom, top), style, origin)
			_:
				_walls(mesh, outline, outline, Vector2(bottom, top), style, origin)
				_cap(mesh, outline, top, style["roof"], origin)
	return mesh


## Altura total de lo que queda en pie (para el panel de la maqueta).
func standing_height(building: Dictionary) -> float:
	var top: float = 0.0
	for piece: Dictionary in pieces(building):
		top = maxf(top, float(piece.get("ridge", piece["top"])))
	return top


func _shape_for(kind: String, outline: PackedVector2Array) -> String:
	match kind:
		"chimenea":
			return "taper"
		"torre_refrigeracion":
			return "cooling"
		"torre_estalinista":
			return "tower"
		"monton":
			return "mound"
		"casa_madera", "barracon", "prerrevolucion":
			return "gable" if outline.size() == 4 else "flat"
	return "flat"


func _piece(
	outline: PackedVector2Array, top: float, shape: String, building: Dictionary
) -> Dictionary:
	var piece: Dictionary = {"outline": outline, "top": top, "shape": shape}
	if shape == "gable":
		var info: Dictionary = plan.data["tipos"][building["tipo"]]
		piece["top"] = minf(top, int(building["pisos"]) * float(info["planta"]))
		piece["ridge"] = top
	return piece


func _split_by_blast(outline: PackedVector2Array, height: float) -> Array[Dictionary]:
	var center: Vector2 = CityGeometry.centroid(outline)
	var away: Vector2 = (center - plan.ground_zero()).normalized()
	var span: Vector2 = CityGeometry.extent(outline, away)
	var result: Array[Dictionary] = []
	for half: PackedVector2Array in CityGeometry.slice(
		outline, away, center.dot(away), span.y + 1.0
	):
		result.append({"outline": half, "top": height, "shape": "flat"})
	return result


## Las casas de madera ardieron casi todas: de las quemadas quedan los restos.
func _burnt_wood(outline: PackedVector2Array, building: Dictionary, shape: String) -> Dictionary:
	var key: String = building["id"]
	var height: float = building["altura"]
	if building["incendio"] == "total" or int(building["dano"]) >= 4:
		return {
			"outline": outline, "top": 1.0 + CityPlan.chance(key + "/restos") * 0.8, "shape": "flat"
		}
	if int(building["dano"]) >= 3:
		return {"outline": outline, "top": height * 0.55, "shape": "flat"}
	return _piece(outline, height, shape, building)


## Daño 2: se hunde el extremo que mira a la bomba (las últimas plantas).
func _collapsed_end(
	outline: PackedVector2Array, building: Dictionary, shape: String
) -> Array[Dictionary]:
	var key: String = building["id"]
	var info: Dictionary = plan.data["tipos"][building["tipo"]]
	var floors: int = int(building["pisos"])
	var height: float = building["altura"]
	var axis: Vector2 = CityGeometry.long_axis(outline)
	var span: Vector2 = CityGeometry.extent(outline, axis)
	if span.y - span.x < 12.0 or floors < 2:
		return [_piece(outline, height, shape, building)]
	var blast_first: bool = plan.ground_zero().dot(axis) < (span.x + span.y) * 0.5
	var cut_length: float = (span.y - span.x) * (0.15 + 0.2 * CityPlan.chance(key + "/corte"))
	var cut: float = span.x + cut_length if blast_first else span.y - cut_length
	var kept: int = clampi(
		roundi(floors * (0.35 + 0.35 * CityPlan.chance(key + "/resto"))), 1, floors - 1
	)
	var low: float = kept * float(info["planta"])
	var result: Array[Dictionary] = []
	for part: PackedVector2Array in CityGeometry.slice(outline, axis, span.x - 1.0, cut):
		result.append({"outline": part, "top": low if blast_first else height, "shape": "flat"})
	for part: PackedVector2Array in CityGeometry.slice(outline, axis, cut, span.y + 1.0):
		result.append({"outline": part, "top": height if blast_first else low, "shape": "flat"})
	return result


## Daños 3 y 4: trozos de alturas desiguales, más bajos del lado de la bomba. Con
## [param low] negativo son muñones de una o dos plantas.
func _slices(
	outline: PackedVector2Array, building: Dictionary, low: float, high: float
) -> Array[Dictionary]:
	var key: String = building["id"]
	var info: Dictionary = plan.data["tipos"][building["tipo"]]
	var floors: int = int(building["pisos"])
	var height: float = building["altura"]
	var storey: float = minf(float(info["planta"]), 4.0)
	var axis: Vector2 = CityGeometry.long_axis(outline)
	var span: Vector2 = CityGeometry.extent(outline, axis)
	var length: float = span.y - span.x
	var count: int = clampi(int(length / 9.0), 1, 3 + int(CityPlan.chance(key + "/trozos") * 3.0))
	var blast_side: float = plan.ground_zero().dot(axis)
	var result: Array[Dictionary] = []
	for i: int in count:
		var from: float = span.x + length * i / count
		var to: float = span.x + length * (i + 1) / count
		var r: float = CityPlan.chance("%s/trozo/%d" % [key, i])
		var near_blast: float = (
			1.0 - clampf(absf((from + to) * 0.5 - blast_side) / maxf(length, 1.0), 0.0, 1.0)
		)
		var top: float
		if low < 0.0:
			top = minf(storey * (0.6 + 1.5 * r), height * 0.6)
		else:
			var fraction: float = clampf(lerpf(low, high, r) - near_blast * 0.2, low, high)
			top = maxi(1, roundi(floors * fraction)) * float(info["planta"])
		top = maxf(1.5, minf(top, height))
		for part: PackedVector2Array in CityGeometry.slice(
			outline, axis, from - (1.0 if i == 0 else 0.0), to + (1.0 if i == count - 1 else 0.0)
		):
			result.append({"outline": part, "top": top, "shape": "flat"})
	return result


## Colores, ventanas y hollín de un edificio.
func _style(building: Dictionary, info: Dictionary) -> Dictionary:
	var key: String = building["id"]
	var base: Color = COLORS.get(building["tipo"], Color("#87837c"))
	base = base.darkened(0.12 * CityPlan.chance(key + "/tono")).lightened(
		0.05 * CityPlan.chance(key + "/luz")
	)
	if int(building["dano"]) >= 3:
		base = base.darkened(0.12)
	var soot: float = {"total": 0.55, "parcial": 0.28}.get(building["incendio"], 0.0)
	var bay: float = WINDOW_BAY.get(info["grupo"], 0.0)
	if building["tipo"] in KEEP_HEIGHT or info["grupo"] == "menor":
		bay = 0.0
	var wall: Color = base.srgb_to_linear()
	wall.a = 1.0 if bay > 0.0 else 0.0
	var sooted: Color = base.darkened(soot).srgb_to_linear()
	sooted.a = wall.a
	var roof: Color = base.darkened(0.18 + soot * 0.5).srgb_to_linear()
	roof.a = 0.0
	return {
		"wall": wall,
		"wall_top": sooted,
		"roof": roof,
		"bay": bay,
		"storey": float(info["planta"]),
		"ground": float(building["cota"]),
	}


## Muros entre dos anillos con el mismo número de puntos (el de arriba puede ser más
## estrecho). [param heights] es la altura de abajo y la de arriba.
func _walls(
	mesh: MeshBuffer,
	lower: PackedVector2Array,
	upper: PackedVector2Array,
	heights: Vector2,
	style: Dictionary,
	origin: Vector2
) -> void:
	var count: int = lower.size()
	var bay: float = style["bay"]
	var storey: float = style["storey"]
	var ground: float = style["ground"]
	var tint: PackedColorArray = PackedColorArray(
		[style["wall"], style["wall"], style["wall_top"], style["wall_top"]]
	)
	var along: float = 0.0
	for i: int in count:
		var a: Vector2 = lower[i]
		var b: Vector2 = lower[(i + 1) % count]
		var c: Vector2 = upper[(i + 1) % count]
		var d: Vector2 = upper[i]
		var edge: Vector2 = b - a
		var u0: float = along / maxf(bay, 1.0)
		along += edge.length()
		var u1: float = along / maxf(bay, 1.0)
		var v0: float = (heights.x - ground) / storey
		var v1: float = (heights.y - ground) / storey
		var outward: Vector3 = Vector3(-edge.y, 0.0, -edge.x)
		(
			mesh
			. add_face(
				PackedVector3Array(
					[
						_local(a, heights.x, origin),
						_local(b, heights.x, origin),
						_local(c, heights.y, origin),
						_local(d, heights.y, origin),
					]
				),
				outward,
				tint,
				PackedVector2Array(
					[Vector2(u0, v0), Vector2(u1, v0), Vector2(u1, v1), Vector2(u0, v1)]
				)
			)
		)


func _cap(
	mesh: MeshBuffer, outline: PackedVector2Array, height: float, color: Color, origin: Vector2
) -> void:
	var triangles: PackedInt32Array = CityGeometry.triangulate(outline)
	mesh.add_cap(outline, triangles, height, color, origin)


## Cubierta a dos aguas sobre una planta de cuatro lados, con la cumbrera a lo largo.
func _gable_roof(
	mesh: MeshBuffer,
	outline: PackedVector2Array,
	eave: float,
	ridge: float,
	style: Dictionary,
	origin: Vector2
) -> void:
	var p: PackedVector2Array = outline
	if p[0].distance_to(p[1]) < p[1].distance_to(p[2]):
		p = PackedVector2Array([outline[1], outline[2], outline[3], outline[0]])
	# Ahora los lados largos son p0-p1 y p2-p3; la cumbrera une los puntos medios de los cortos.
	var ridge_a: Vector2 = (p[3] + p[0]) * 0.5
	var ridge_b: Vector2 = (p[1] + p[2]) * 0.5
	var roof: PackedColorArray = PackedColorArray([style["roof"]])
	for side: Array in [[p[0], p[1], ridge_b, ridge_a], [p[2], p[3], ridge_a, ridge_b]]:
		(
			mesh
			. add_face(
				PackedVector3Array(
					[
						_local(side[0], eave, origin),
						_local(side[1], eave, origin),
						_local(side[2], ridge, origin),
						_local(side[3], ridge, origin),
					]
				),
				Vector3.UP,
				roof
			)
		)
	var gable: PackedColorArray = PackedColorArray([style["wall_top"]])
	for end: Array in [[p[1], p[2], ridge_b], [p[3], p[0], ridge_a]]:
		var edge: Vector2 = end[1] - end[0]
		mesh.add_face(
			PackedVector3Array(
				[
					_local(end[0], eave, origin),
					_local(end[1], eave, origin),
					_local(end[2], ridge, origin)
				]
			),
			Vector3(-edge.y, 0.0, -edge.x),
			gable
		)


## Torre de refrigeración: un hiperboloide de anillos que se estrechan y se abren.
func _cooling_tower(
	mesh: MeshBuffer,
	outline: PackedVector2Array,
	heights: Vector2,
	style: Dictionary,
	origin: Vector2
) -> void:
	var profile: Array[Vector2] = [
		Vector2(0.0, 1.0),
		Vector2(0.3, 0.8),
		Vector2(0.62, 0.68),
		Vector2(0.85, 0.72),
		Vector2(1.0, 0.78)
	]
	var center: Vector2 = CityGeometry.centroid(outline)
	var below: float = heights.x
	var ring: PackedVector2Array = outline
	for step: Vector2 in profile.slice(1):
		var next: PackedVector2Array = CityGeometry.scaled(outline, center, step.y)
		var top: float = lerpf(style["ground"], heights.y, step.x)
		_walls(mesh, ring, next, Vector2(below, top), style, origin)
		ring = next
		below = top
	# Por arriba está abierta: se ve el hueco oscuro.
	_cap(mesh, ring, heights.y - 0.5, Color(style["roof"]).darkened(0.7), origin)


## Torre estalinista: el cuerpo, un remate más estrecho y la aguja (doblada si el plano
## lo cuenta).
func _tower(
	mesh: MeshBuffer,
	building: Dictionary,
	outline: PackedVector2Array,
	heights: Vector2,
	style: Dictionary,
	origin: Vector2
) -> void:
	var info: Dictionary = plan.data["tipos"][building["tipo"]]
	var ground: float = style["ground"]
	var body: float = (
		ground + minf(int(building["pisos"]) * float(info["planta"]), (heights.y - ground) * 0.8)
	)
	var tier: float = body + (heights.y - body) * 0.3
	var center: Vector2 = CityGeometry.centroid(outline)
	var upper: PackedVector2Array = CityGeometry.scaled(outline, center, 0.62)
	var base: PackedVector2Array = CityGeometry.scaled(outline, center, 0.3)
	_walls(mesh, outline, outline, Vector2(heights.x, body), style, origin)
	_cap(mesh, outline, body, style["roof"], origin)
	_walls(mesh, upper, upper, Vector2(body, tier), style, origin)
	_cap(mesh, upper, tier, style["roof"], origin)
	var tip: Vector2 = center
	var key: String = building["id"]
	if BENT_SPIRES.has(key):
		var angle: float = deg_to_rad(BENT_SPIRES[key])
		tip += Vector2(cos(angle), sin(angle)) * (heights.y - tier) * 0.45
	var apex: Vector3 = _local(tip, heights.y, origin)
	var spire: PackedColorArray = PackedColorArray([style["wall_top"]])
	for i: int in base.size():
		var a: Vector2 = base[i]
		var b: Vector2 = base[(i + 1) % base.size()]
		var edge: Vector2 = b - a
		mesh.add_face(
			PackedVector3Array([_local(a, tier, origin), _local(b, tier, origin), apex]),
			Vector3(-edge.y, 0.3, -edge.x),
			spire
		)


func _shrunk(outline: PackedVector2Array, factor: float) -> PackedVector2Array:
	return CityGeometry.scaled(outline, CityGeometry.centroid(outline), factor)


static func _local(point: Vector2, height: float, origin: Vector2) -> Vector3:
	return Vector3(point.x - origin.x, height, origin.y - point.y)
