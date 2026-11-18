class_name CityProps
extends RefCounted
## Lo que hay por la calle y entre los edificios, en volúmenes sencillos: los vehículos
## del atasco, los árboles (los tumbados apuntan lejos de la bomba), los puentes, las
## tuberías elevadas, las vallas, las torres de la línea eléctrica y los muros del borde.
##
## Los vehículos y los árboles se reparten por sectores como instancias (MultiMesh); las
## estructuras, como mallas troceadas por sectores.

## Los modelos de los vehículos (tools/blender/recipes/vehiculos.py; el coche, de
## superficie.py). Los quemados que tienen modelo propio llevan "_quemado".
const VEHICLE_MODELS: PackedStringArray = [
	"coche",
	"coche_quemado",
	"autobus",
	"autobus_quemado",
	"trolebus",
	"tranvia",
	"tranvia_quemado",
	"camion",
	"camion_quemado",
	"furgoneta",
	"furgoneta_quemado",
	"blindado",
	"bombero",
	"bombero_quemado",
	"vagon",
	"coche_tren",
	"coche_tren_quemado",
	"locomotora",
	"locomotora_quemado",
	"barca",
	"barcaza",
	"remolcador",
	"barco",
]
## Lo que vuelca boca abajo; lo demás, de costado.
const FLIPS_OVER: PackedStringArray = ["coche", "barca"]
## Escora máxima (grados) de los barcos que se quedaron en el hielo o varados.
const BOAT_LIST: Dictionary = {"barca": 9.0, "barcaza": 2.0, "remolcador": 6.0, "barco": 4.0}
## Colores apagados de los coches abandonados (multiplican la pintura del modelo).
const CAR_TINTS: Array[Color] = [
	Color("#c9c2b0"), Color("#9fae9b"), Color("#a3a9b3"), Color("#b79c8f"), Color("#bdb59a")
]
## Los de los demás vehículos: la pintura ya la lleva el modelo, solo se ensucia algo.
const VEHICLE_TINTS: Array[Color] = [
	Color("#ffffff"), Color("#e9e4d9"), Color("#dfe2d8"), Color("#ece2d8")
]
## El de los quemados con modelo propio (ya son pardos y negros); sin él, más oscuro.
const BURNT_TINT: Color = Color(0.82, 0.8, 0.78)
## Alto y color de cada vehículo cuando no hay modelo y es una caja (el plano da el largo y
## el ancho).
const VEHICLE_HEIGHT: Dictionary = {
	"coche": 1.5,
	"furgoneta": 2.3,
	"autobus": 3.0,
	"camion": 3.1,
	"tranvia": 3.4,
	"trolebus": 3.3,
	"blindado": 2.5,
	"vagon": 3.6,
	"coche_tren": 4.0,
	"locomotora": 4.3,
	"barcaza": 2.6,
	"remolcador": 4.5,
	"barco": 6.0,
	"barca": 0.9,
	"bombero": 3.0,
}
const VEHICLE_COLOR: Dictionary = {
	"furgoneta": Color("#8a8370"),
	"autobus": Color("#8b7c4f"),
	"camion": Color("#5f6553"),
	"tranvia": Color("#7b4b3d"),
	"trolebus": Color("#5d6b74"),
	"blindado": Color("#545a43"),
	"vagon": Color("#5e4c3f"),
	"coche_tren": Color("#4f5c4b"),
	"locomotora": Color("#3c3b38"),
	"barcaza": Color("#4e4239"),
	"remolcador": Color("#5b3f34"),
	"barco": Color("#62584c"),
	"barca": Color("#5a4a3a"),
	"bombero": Color("#8a3b2e"),
	"coche": Color("#7a7a72"),
}
## Alto de los muros de la autovía caída, al oeste y al norte del mapa.
const BORDER_WALL_HEIGHT: float = 10.0
const STRUCTURE_COLOR: Color = Color("#77736b")
## Lo que queda la losa del puente por debajo de la calzada (el firme).
const DECK_GAP: float = 0.02

var plan: CityPlan
## La caja de cada modelo de vehículo (la de su colisión, en sus coordenadas): la medida
## del vehículo, con la que se escala a lo que mide en el plano. La pone City al cargar
## los modelos; un vehículo sin ella es una caja.
var model_boxes: Dictionary = {}
## Tableros de los puentes: lo que se pisa encima del hielo.
var _decks: Array[Dictionary] = []


func _init(city_plan: CityPlan) -> void:
	plan = city_plan
	_prepare_decks()


## Altura de lo que se pisa en un punto: el tablero de un puente si lo hay; si no, el
## terreno.
func surface_height(point: Vector2) -> float:
	for deck: Dictionary in _decks:
		var a: Vector2 = deck["from"]
		var b: Vector2 = deck["to"]
		var along: Vector2 = b - a
		var f: float = (point - a).dot(along) / along.length_squared()
		var across: float = absf((point - a).cross(along)) / along.length()
		if f >= 0.0 and f <= 1.0 and across <= deck["half_width"]:
			return lerpf(deck["height_from"], deck["height_to"], f)
	return plan.height_at(point)


## Vehículos de cada sector: para cada sector, las instancias por modelo (el suyo, el
## quemado si lo tiene, o "caja"), cada una con su transformación y su color.
func vehicles() -> Dictionary:
	var result: Dictionary = {}
	var index: int = 0
	for vehicle: Dictionary in plan.data["vehiculos"]:
		index += 1
		var point: Vector2 = Vector2(vehicle["pos"][0], vehicle["pos"][1])
		var model: String = _vehicle_model(vehicle)
		var placed: Transform3D = _vehicle_transform(vehicle, model, index)
		_add_instance(
			result, plan.sector_of(point), model, placed, _vehicle_color(vehicle, model, index)
		)
	return result


## El modelo de un vehículo: el suyo (el quemado, si lo tiene) o una caja.
func _vehicle_model(vehicle: Dictionary) -> String:
	var kind: String = vehicle["tipo"]
	if vehicle["estado"] == "quemado" and model_boxes.has(kind + "_quemado"):
		return kind + "_quemado"
	return kind if model_boxes.has(kind) else "caja"


## Dónde y cómo queda un vehículo: escalado a lo que mide en el plano, volcado si lo
## tumbaron (boca abajo o de costado) e inclinado si cayó en un socavón o, un barco,
## escorado en el hielo.
func _vehicle_transform(vehicle: Dictionary, model: String, index: int) -> Transform3D:
	var kind: String = vehicle["tipo"]
	var point: Vector2 = Vector2(vehicle["pos"][0], vehicle["pos"][1])
	var size: Array = plan.data["medidas_vehiculos"][kind]
	var yaw: Basis = Basis(Vector3.UP, deg_to_rad(vehicle["angulo"]))
	# La altura de lo que pisa la da el plano si está en el tránsito (la calzada va por
	# debajo de la rasante) o sobre una vía; si no, el relieve o el tablero de un puente.
	var ground: float = float(vehicle["z"]) if vehicle.has("z") else surface_height(point)
	var basis: Basis
	var origin: Vector3 = CityPlan.to_world(point, ground)
	if model == "caja":
		var height: float = VEHICLE_HEIGHT.get(kind, 2.0)
		basis = yaw * Basis.from_scale(Vector3(size[0], height, size[1]))
		origin.y += height * 0.5
	else:
		var box: AABB = model_boxes[model]
		var scale: float = float(size[0]) / box.size.x
		basis = yaw * Basis.from_scale(Vector3.ONE * scale)
		if vehicle["estado"] == "volcado" and kind in FLIPS_OVER:
			# Boca abajo, sobre el techo (o la borda).
			basis = basis * Basis(Vector3.RIGHT, PI)
			origin.y += box.end.y * scale
		elif vehicle["estado"] == "volcado":
			# De costado: la onda lo tumbó. La huella sigue centrada en su sitio.
			basis = basis * Basis(Vector3.RIGHT, PI * 0.5)
			origin.y += box.size.z * 0.5 * scale
			origin -= yaw * Vector3(0.0, 0.0, box.get_center().y * scale)
	var tilt: Basis = _vehicle_tilt(vehicle, index)
	return Transform3D(yaw * tilt * (yaw.inverse() * basis), origin)


## Lo que se inclina un vehículo: el que cayó en un socavón, de morro hacia el fondo y algo
## ladeado (lo da el plano); los barcos, escorados en el hielo (un poco cada uno).
func _vehicle_tilt(vehicle: Dictionary, index: int) -> Basis:
	var pitch: float = float(vehicle.get("cabeceo", 0.0))
	var roll: float = float(vehicle.get("alabeo", 0.0))
	if BOAT_LIST.has(vehicle["tipo"]) and vehicle["estado"] != "volcado":
		var most: float = BOAT_LIST[vehicle["tipo"]]
		roll = most * sin(index * 12.9898)
		pitch = most * 0.25 * cos(index * 78.233)
	return Basis(Vector3.BACK, -deg_to_rad(pitch)) * Basis(Vector3.RIGHT, deg_to_rad(roll))


## El color de la instancia: tiñe la pintura del modelo (los coches, de colores apagados;
## los quemados, más oscuros) o es el de la caja.
func _vehicle_color(vehicle: Dictionary, model: String, index: int) -> Color:
	var kind: String = vehicle["tipo"]
	var burnt: bool = vehicle["estado"] == "quemado"
	if model == "caja":
		var color: Color = VEHICLE_COLOR.get(kind, STRUCTURE_COLOR)
		return (color.darkened(0.55) if burnt else color).srgb_to_linear()
	if burnt:
		return BURNT_TINT if model.ends_with("_quemado") else BURNT_TINT.darkened(0.5)
	if kind == "coche":
		return CAR_TINTS[index % CAR_TINTS.size()]
	return VEHICLE_TINTS[index % VEHICLE_TINTS.size()]


## Árboles de cada sector, por modelo ("arbol_desnudo" y "arbol_desnudo_b").
func trees() -> Dictionary:
	var result: Dictionary = {}
	var index: int = 0
	for tree: Dictionary in plan.data["arboles"]:
		index += 1
		var point: Vector2 = Vector2(tree["pos"][0], tree["pos"][1])
		var key: String = "arbol/%d" % index
		var model: String = "arbol_desnudo" if CityPlan.chance(key) < 0.55 else "arbol_desnudo_b"
		var basis: Basis
		var lift: float = 0.0
		if tree["estado"] == "tumbado":
			# Tumbado: la copa apunta lejos de la bomba, como en el plano.
			var heading: float = deg_to_rad(tree["rumbo"])
			var along: Vector3 = Vector3(cos(heading), 0.0, -sin(heading))
			basis = Basis(along.cross(Vector3.UP), along, Vector3.UP)
			lift = 0.3
		else:
			var size: float = clampf(float(tree["copa"]) / 2.0, 0.8, 1.25)
			var grown: float = size * (0.9 + 0.25 * CityPlan.chance(key + "/alto"))
			basis = (
				Basis(Vector3.UP, CityPlan.chance(key + "/giro") * TAU)
				* Basis.from_scale(Vector3.ONE * grown)
			)
		var ground: float = float(tree["z"]) if tree.has("z") else plan.height_at(point)
		var origin: Vector3 = CityPlan.to_world(point, ground + lift)
		_add_instance(result, plan.sector_of(point), model, Transform3D(basis, origin), Color.WHITE)
	return result


## Las estructuras troceadas por sectores: para cada sector, una malla con el origen en
## su centro.
func structures() -> Dictionary:
	var parts: Dictionary = {}
	_bridge_progreso(parts)
	_bridge_railway(parts)
	_pipes(parts)
	_fences(parts)
	_power_line(parts)
	_border_walls(parts)
	return parts


func _add_instance(
	result: Dictionary, sector: Vector2i, model: String, transform: Transform3D, color: Color
) -> void:
	if not result.has(sector):
		result[sector] = {}
	var by_model: Dictionary = result[sector]
	if not by_model.has(model):
		by_model[model] = []
	by_model[model].append([transform, color])


## Los tableros de los puentes. El del Progreso va de orilla a orilla sobre el río (en
## tierra es calle) con la altura del tablero de la red de tránsito: la losa queda justo
## bajo la calzada.
func _prepare_decks() -> void:
	var bridge: Dictionary = _street("puente_progreso")
	var gap: Array = bridge["vano_hundido"]
	var half: float = float(bridge["ancho"]) * 0.5
	var rule: Dictionary = plan.transit["puente"]["regla"]
	var roadway: float = float(plan.transit["niveles"]["calzada"])
	# Donde el eje del puente entra y sale del río.
	var banks: Vector2 = Vector2(INF, -INF)
	var s: float = 372.0
	while s <= 632.0:
		if plan.is_on_river(plan.axis_point(s)):
			banks = Vector2(minf(banks.x, s), maxf(banks.y, s))
		s += 0.5
	for span: Vector2 in [Vector2(banks.x, gap[0]), Vector2(gap[1], banks.y)]:
		var from: Vector2 = plan.axis_point(span.x)
		var to: Vector2 = plan.axis_point(span.y)
		(
			_decks
			. append(
				{
					"from": from,
					"to": to,
					"half_width": half,
					"height_from": _ramp(rule, from) + roadway - DECK_GAP,
					"height_to": _ramp(rule, to) + roadway - DECK_GAP,
				}
			)
		)
	# El del ferrocarril: a la altura de la rasante de la vía en cada punta (el balasto, las
	# traviesas y los carriles los pone la red de tránsito encima).
	var railway: Dictionary = plan.data["puente_ferrocarril"]
	var a: Vector2 = Vector2(railway["puntos"][0][0], railway["puntos"][0][1])
	var b: Vector2 = Vector2(railway["puntos"][1][0], railway["puntos"][1][1])
	var levels: Array = plan.transit["puente_ferrocarril"]["z"]
	(
		_decks
		. append(
			{
				"from": a,
				"to": b,
				"half_width": float(railway["ancho"]) * 0.5,
				"height_from": float(levels[0]) - 0.05,
				"height_to": float(levels[1]) - 0.05,
			}
		)
	)


func _ramp(rule: Dictionary, point: Vector2) -> float:
	var origin: Vector2 = Vector2(rule["o"][0], rule["o"][1])
	var direction: Vector2 = Vector2(rule["d"][0], rule["d"][1])
	var f: float = clampf((point - origin).dot(direction) / float(rule["largo"]), 0.0, 1.0)
	return lerpf(float(rule["z0"]), float(rule["z1"]), f)


func _street(id: String) -> Dictionary:
	for street: Dictionary in plan.data["calles"]:
		if street["id"] == id:
			return street
	return {}


## El Puente del Progreso: dos tableros sobre pilas y, entre ellos, el vano central
## hundido, inclinado sobre el hielo (se baja con cuerda y se sube por el otro lado).
func _bridge_progreso(parts: Dictionary) -> void:
	var bridge: Dictionary = _street("puente_progreso")
	var gap: Array = bridge["vano_hundido"]
	var thickness: float = bridge["tablero"]
	var color: Color = Color("#807b72")
	# Las losas (los pretiles, las aceras y la calzada los pone la red de tránsito).
	for deck: Dictionary in _decks.slice(0, 2):
		var a: Vector3 = CityPlan.to_world(deck["from"], float(deck["height_from"]) - thickness)
		var b: Vector3 = CityPlan.to_world(deck["to"], float(deck["height_to"]) - thickness)
		_beam(parts, a, b, float(deck["half_width"]) * 2.0, thickness, color)
	var ice: float = plan.data["rio"]["hielo"]
	var top: float = float(_decks[0]["height_to"]) - 2.5
	var sunk_from: Vector3 = CityPlan.to_world(
		plan.axis_point(float(gap[0]) + 3.0), top - thickness
	)
	var sunk_to: Vector3 = CityPlan.to_world(plan.axis_point(float(gap[1]) - 3.0), ice + 0.2)
	_beam(parts, sunk_from, sunk_to, 28.0, thickness, color.darkened(0.15))
	for s: float in [440.0, float(gap[0]), float(gap[1]), 600.0]:
		var point: Vector2 = plan.axis_point(s)
		var deck_bottom: float = surface_height(point) - thickness
		var base: float = minf(plan.height_at(point), ice) - 1.0
		var middle: Vector3 = CityPlan.to_world(point, (deck_bottom + base) * 0.5)
		var axis: Vector3 = CityPlan.to_world(plan.axis_point(s + 1.0)) - CityPlan.to_world(point)
		var basis: Basis = Basis(
			axis.normalized() * 3.0,
			Vector3.UP * (deck_bottom - base) * 0.5,
			axis.normalized().cross(Vector3.UP) * 18.0
		)
		_box(parts, point, middle, basis, color.darkened(0.1))


## El puente del ferrocarril: tablero y celosía de acero.
func _bridge_railway(parts: Dictionary) -> void:
	var deck: Dictionary = _decks[2]
	var a: Vector3 = CityPlan.to_world(deck["from"], float(deck["height_from"]) - 1.5)
	var b: Vector3 = CityPlan.to_world(deck["to"], float(deck["height_to"]) - 1.5)
	var steel: Color = Color("#4e5052")
	var width: float = float(deck["half_width"]) * 2.0
	_beam(parts, a, b, width, 1.5, steel)
	var side_dir: Vector3 = _across(deck["from"], deck["to"])
	var length: float = a.distance_to(b)
	var panels: int = maxi(1, roundi(length / 10.0))
	for side: float in [-1.0, 1.0]:
		var offset: Vector3 = side_dir * (width * 0.5 - 0.4) * side + Vector3.UP * 1.5
		var high: Vector3 = Vector3.UP * 7.0
		_beam(parts, a + offset + high, b + offset + high, 0.6, 0.6, steel)
		for k: int in panels + 1:
			var p: Vector3 = a.lerp(b, float(k) / panels) + offset
			_beam(parts, p, p + high, 0.5, 0.5, steel)
			if k < panels:
				var q: Vector3 = a.lerp(b, float(k + 1) / panels) + offset
				_beam(
					parts,
					p if k % 2 == 0 else p + high,
					q + high if k % 2 == 0 else q,
					0.4,
					0.4,
					steel
				)
	var ice: float = plan.data["rio"]["hielo"]
	for f: float in [0.33, 0.67]:
		var point: Vector2 = Vector2(deck["from"]).lerp(deck["to"], f)
		var top: float = float(deck["height_from"]) - 1.5
		_box(
			parts,
			point,
			CityPlan.to_world(point, (top + ice - 1.0) * 0.5),
			Basis.from_scale(Vector3(4.0, (top - ice + 1.0) * 0.5, width * 0.6)),
			steel.darkened(0.2)
		)


## Tuberías elevadas sobre postes. Cruzan las calles y el río a la altura del punto más
## bajo de sus dos orillas (para no hundirse en el hielo).
func _pipes(parts: Dictionary) -> void:
	for pipe: Dictionary in plan.data["tuberias"]:
		var line: PackedVector2Array = CityGeometry.subdivide(CityPlan.line(pipe["puntos"]), 6.0)
		var clearance: float = 5.0 if pipe["id"] == "bloques" else 3.5
		var heights: PackedFloat32Array = _bridged_heights(line, clearance)
		var color: Color = Color("#6c665d")
		var size: float = 2.4 if pipe["id"] == "carbon" else 1.0
		for i: int in line.size() - 1:
			var a: Vector3 = CityPlan.to_world(line[i], heights[i])
			var b: Vector3 = CityPlan.to_world(line[i + 1], heights[i + 1])
			_beam(parts, a, b, size, size, color)
			if pipe["id"] == "tubo_rio":
				# Dos tubos y la pasarela de servicio.
				var side: Vector3 = _across(line[i], line[i + 1])
				_beam(parts, a + side * 1.2, b + side * 1.2, 1.0, 1.0, color)
				_beam(
					parts,
					a - side * 1.4 + Vector3.UP * 0.4,
					b - side * 1.4 + Vector3.UP * 0.4,
					1.0,
					0.15,
					color.darkened(0.2)
				)
			var ground: float = plan.height_at(line[i])
			if i % 2 == 0 and heights[i] - ground < clearance + 1.0:
				_beam(
					parts,
					CityPlan.to_world(line[i], ground - 0.5),
					a,
					0.4,
					0.4,
					color.darkened(0.25)
				)


## Las vallas y tapias del plano, siguiendo el terreno.
func _fences(parts: Dictionary) -> void:
	for fence: Dictionary in plan.data["vallas"]:
		var name: String = fence["nombre"]
		var size: Vector2 = Vector2(0.12, 2.0)
		var color: Color = Color("#5d5a54")
		if name.contains("contenedores"):
			size = Vector2(2.4, 2.6)
			color = Color("#6b4a3a")
		elif name.contains("Tapia"):
			size = Vector2(0.5, 2.6)
			color = Color("#7a6a5c")
		elif name.contains("sacos"):
			size = Vector2(0.9, 1.3)
			color = Color("#6b6450")
		var line: PackedVector2Array = CityGeometry.subdivide(CityPlan.line(fence["puntos"]), 8.0)
		for i: int in line.size() - 1:
			var a: Vector3 = CityPlan.to_world(line[i], plan.height_at(line[i]) - 0.3)
			var b: Vector3 = CityPlan.to_world(line[i + 1], plan.height_at(line[i + 1]) - 0.3)
			_beam(parts, a, b, size.x, size.y + 0.3, color)


## La línea de alta tensión: torres de celosía (de bulto) y cables.
func _power_line(parts: Dictionary) -> void:
	var steel: Color = Color("#55575a")
	for line_data: Dictionary in plan.data["lineas_electricas"]:
		var tops: Array[Vector3] = []
		for tower: Array in line_data["torres"]:
			var point: Vector2 = Vector2(tower[0], tower[1])
			var ground: float = plan.height_at(point)
			_box(
				parts,
				point,
				CityPlan.to_world(point, ground + 15.0),
				Basis.from_scale(Vector3(1.2, 15.0, 1.2)),
				steel
			)
			_box(
				parts,
				point,
				CityPlan.to_world(point, ground + 27.0),
				Basis.from_scale(Vector3(6.0, 0.4, 0.5)),
				steel
			)
			tops.append(CityPlan.to_world(point, ground + 26.5))
		for i: int in tops.size() - 1:
			for side: float in [-5.0, 5.0]:
				var offset: Vector3 = Vector3(side, 0.0, 0.0)
				_beam(parts, tops[i] + offset, tops[i + 1] + offset, 0.08, 0.08, steel)


## La autovía caída cierra el mapa por el oeste y el norte: un muro de hormigón y coches.
func _border_walls(parts: Dictionary) -> void:
	var wall: PackedVector2Array = PackedVector2Array(
		[Vector2(-5.0, 20.0), Vector2(-5.0, plan.size.y + 5.0), Vector2(1250.0, plan.size.y + 5.0)]
	)
	var line: PackedVector2Array = CityGeometry.subdivide(wall, 40.0)
	for i: int in line.size() - 1:
		var low: float = minf(plan.height_at(line[i]), plan.height_at(line[i + 1])) - 1.0
		var a: Vector3 = CityPlan.to_world(line[i], low)
		var b: Vector3 = CityPlan.to_world(line[i + 1], low)
		var r: float = CityPlan.chance("muro/%d" % i)
		_beam(
			parts,
			a,
			b,
			9.0,
			BORDER_WALL_HEIGHT * (0.8 + 0.4 * r) + 1.0,
			Color("#6e6a63").darkened(0.2 * r)
		)


## Alturas de una conducción elevada: [param clearance] metros sobre el suelo, pero sin
## bajar en los valles (el río, una calle hundida): ahí cruza recta, a la altura de la
## orilla más baja.
func _bridged_heights(line: PackedVector2Array, clearance: float) -> PackedFloat32Array:
	var target: PackedFloat32Array = PackedFloat32Array()
	for p: Vector2 in line:
		target.append(maxf(plan.height_at(p), 0.0) + clearance)
	var count: int = target.size()
	var rising: PackedFloat32Array = target.duplicate()
	var falling: PackedFloat32Array = target.duplicate()
	for i: int in range(1, count):
		rising[i] = maxf(rising[i - 1], target[i])
	for i: int in range(count - 2, -1, -1):
		falling[i] = maxf(falling[i + 1], target[i])
	var result: PackedFloat32Array = PackedFloat32Array()
	for i: int in count:
		result.append(maxf(target[i], minf(rising[i], falling[i])))
	return result


func _across(from: Vector2, to: Vector2) -> Vector3:
	var along: Vector3 = CityPlan.to_world(to) - CityPlan.to_world(from)
	return along.cross(Vector3.UP).normalized()


func _beam(
	parts: Dictionary, from: Vector3, to: Vector3, width: float, height: float, color: Color
) -> void:
	var middle: Vector2 = CityPlan.to_plan((from + to) * 0.5)
	var sector: Vector2i = plan.sector_of(middle)
	var origin: Vector3 = CityPlan.to_world(plan.sector_rect(sector).get_center())
	_part(parts, sector).add_beam(from - origin, to - origin, width, height, color.srgb_to_linear())


func _box(parts: Dictionary, point: Vector2, center: Vector3, basis: Basis, color: Color) -> void:
	var sector: Vector2i = plan.sector_of(point)
	var origin: Vector3 = CityPlan.to_world(plan.sector_rect(sector).get_center())
	_part(parts, sector).add_box(center - origin, basis, color.srgb_to_linear())


func _part(parts: Dictionary, sector: Vector2i) -> MeshBuffer:
	if not parts.has(sector):
		parts[sector] = MeshBuffer.new()
	return parts[sector]
