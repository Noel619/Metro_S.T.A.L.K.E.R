class_name CityTransit
extends RefCounted
## La red de tránsito de la maqueta, levantada desde data/ciudad/transito.json: calzadas,
## aceras, plazas, sendas, peldaños y el tablero del puente, con lo que va en sus lindes
## (bordillos, bordes, contrahuellas, muros y pretiles), las marcas viales y los detalles
## (tapas de registro y sumideros).
##
## Cada superficie se corta por la rejilla del relieve detallado (2 m, con la diagonal del
## suroeste al noreste, como CityTerrain): cada pieza cae dentro de un solo triángulo del
## terreno y sigue la rasante del tránsito igual que el terreno sigue el relieve (donde la
## rasante es plana basta con el triángulo entero). Los triángulos del terreno que toca el
## tránsito no se dibujan: lo que queda en ellos sin tránsito (el relleno) se dibuja aparte,
## a la altura exacta del terreno, y las aristas cierran el escalón entre el borde del
## tránsito y el relleno. Así el terreno ni asoma entre las losas ni deja zanjas.
##
## Qué triángulos tapa el tránsito, el relleno exacto y cuánto se rebaja la colisión del
## relieve bajo el tránsito lo calcula tools/ciudad/rejilla.py (rejilla.png, rebaje.png y el
## relleno de transito.json). Los montones de escombros que caen en la calle se dibujan
## rebajados igual: asoman sobre el asfalto donde son altos. El tablero del puente va por
## el aire y no toca el terreno.
##
## Cada sector se levanta en su propio hilo (TransitSector).

const STEP: float = 2.0
## Lado de las celdas del índice con el que se busca qué se pisa en un punto.
const INDEX_CELL: float = 10.0
## Lo que tiene que levantar un montón de escombros sobre la rasante para dibujarse.
const RUBBLE_MIN: float = 0.05
## Material de cada clase de superficie (los materiales los crea City).
const SURFACE_MATERIALS: Dictionary = {
	"calzada": "asfalto",
	"adoquin": "adoquin",
	"acera": "acera",
	"losas": "losas",
	"plaza": "plaza",
	"paseo": "losas",
	"isleta": "losas",
	"alcorque": "tierra",
	"senda": "grava",
	"camino": "tierra",
	"peldano": "granito",
	"anden": "hormigon",
	"paso_nivel": "hormigon",
	"via_tranvia": "hormigon",
}
## Color de cada clase (multiplica la textura) y, en el alfa, cuánta nieve la cubre.
const SURFACE_COLORS: Dictionary = {
	"calzada": Color(0.31, 0.305, 0.3, 0.42),
	"adoquin": Color(0.46, 0.43, 0.4, 0.58),
	"acera": Color(0.5, 0.49, 0.47, 0.75),
	"losas": Color(0.68, 0.65, 0.6, 0.72),
	"plaza": Color(0.71, 0.67, 0.61, 0.72),
	"paseo": Color(0.7, 0.66, 0.58, 0.8),
	"isleta": Color(0.64, 0.62, 0.58, 0.85),
	"alcorque": Color(0.42, 0.36, 0.3, 0.92),
	"senda": Color(0.58, 0.52, 0.44, 0.9),
	"camino": Color(0.5, 0.44, 0.36, 0.85),
	"peldano": Color(0.68, 0.66, 0.63, 0.6),
	"anden": Color(0.62, 0.6, 0.57, 0.75),
	"paso_nivel": Color(0.5, 0.49, 0.47, 0.45),
	"via_tranvia": Color(0.56, 0.55, 0.52, 0.5),
}
## Metros de suelo que cubre la textura de cada material.
const TILE: Dictionary = {
	"asfalto": 4.0,
	"adoquin": 2.0,
	"acera": 4.0,
	"losas": 2.0,
	"plaza": 4.0,
	"granito": 2.0,
	"grava": 3.0,
	"tierra": 4.0,
	"hormigon": 2.0,
	"bordillo": 1.0,
}
## El color del terreno en los rellenos (como CityTerrain: lo pone el suelo de la maqueta).
const GROUND_COLOR: Color = Color(1.0, 1.0, 1.0, 0.0)

var plan: CityPlan
## Lo levantado por sector (Vector2i): {material: MeshBuffer}, con el origen en el centro
## del sector. "suelo" es el relleno y los escombros (el material del terreno).
var meshes: Dictionary = {}
## Las caras de colisión de cada sector: un MeshBuffer cuyos vértices van de tres en tres
## (en el espacio del sector).
var collision: Dictionary = {}
## Detalles por sector: {modelo: Array de Transform3D en el mundo}.
var instances: Dictionary = {}
## Triángulos de la rejilla (dos por celda: [method triangle_id]) que tapa el tránsito: el
## terreno no los dibuja.
var touched: PackedByteArray = PackedByteArray()
## Cuánto se rebaja la colisión del relieve en cada punto de la rejilla.
var carve: PackedFloat32Array = PackedFloat32Array()
## Celdas de la rejilla a lo ancho y a lo alto, y celdas por sector.
var cells: Vector2i = Vector2i.ZERO
var cells_per_sector: int = 100
## Cifras de la construcción.
var stats: Dictionary = {}
## Las vías del tren y del tranvía, en tramos: {"puntos": PackedVector2Array, "z":
## PackedFloat32Array (la rasante de la vía; vacía si va a ras), "largo": lo que mide la vía
## hasta cada punto, "abierta": si lleva balasto y traviesas, "carril": del eje de la vía
## al de cada carril, "puntas": si cada extremo queda suelto (no sigue en otro tramo)}.
var tracks: Array = []

var groups: Array = []
## Por grupo: 1 si sigue la rasante; y el nivel de su clase.
var follows_base: PackedByteArray = PackedByteArray()
var group_level: PackedFloat32Array = PackedFloat32Array()
var vertex_heights: PackedFloat32Array = PackedFloat32Array()
var vertex_base: PackedFloat32Array = PackedFloat32Array()

var _levels: Dictionary = {}
var _sectors: Array[TransitSector] = []
## Índice de los triángulos de los grupos por celdas de [constant INDEX_CELL] metros:
## pares (grupo, primer índice del triángulo).
var _index: Dictionary = {}


func _init(city_plan: CityPlan) -> void:
	plan = city_plan


## Levanta toda la red (cada sector en un hilo).
func build() -> void:
	var started: int = Time.get_ticks_msec()
	_prepare()
	_assign()
	var task: int = WorkerThreadPool.add_group_task(
		_build_sector, _sectors.size(), -1, true, "Tránsito de la maqueta"
	)
	WorkerThreadPool.wait_for_group_task_completion(task)
	_merge()
	_build_details()
	# Los sectores guardan una referencia a esta red: se sueltan para que no queden vivos.
	_sectors.clear()
	stats["segundos"] = (Time.get_ticks_msec() - started) / 1000.0
	stats["triangulos"] = 0
	for sector: Vector2i in meshes:
		for material: String in meshes[sector]:
			stats["triangulos"] += (meshes[sector][material] as MeshBuffer).triangle_count()


## La altura de lo que se pisa del tránsito en un punto (NAN si no hay tránsito ahí). Si
## hay dos cosas (el tablero del puente sobre el hielo no cuenta como dos), la más alta.
func surface_at(point: Vector2) -> float:
	var cell: Vector2i = Vector2i((point / INDEX_CELL).floor())
	var found: float = NAN
	for n: int in range(0, (_index.get(cell, PackedInt32Array()) as PackedInt32Array).size(), 2):
		var pairs: PackedInt32Array = _index[cell]
		var index: int = pairs[n]
		var start: int = pairs[n + 1]
		var points: Array = groups[index]["puntos"]
		var corners: Array = groups[index]["triangulos"]
		var a: Vector2 = _corner(points, corners, start)
		var b: Vector2 = _corner(points, corners, start + 1)
		var c: Vector2 = _corner(points, corners, start + 2)
		if Geometry2D.point_is_inside_triangle(point, a, b, c):
			var z: float = surface_z(index, point)
			found = z if is_nan(found) else maxf(found, z)
	return found


static func _corner(points: Array, corners: Array, n: int) -> Vector2:
	var v: int = int(corners[n]) * 2
	return Vector2(points[v], points[v + 1])


## El grupo [param index] de transito.json.
func group(index: int) -> Dictionary:
	return groups[index]


## Altura de lo que se pisa del grupo [param index] en un punto: su regla más el nivel
## de su clase.
func surface_z(index: int, point: Vector2) -> float:
	if follows_base[index] == 1:
		return base_z(point) + group_level[index]
	var rule: Dictionary = groups[index]["regla"]
	if String(rule["tipo"]) == "rampa":
		return ramp_z(rule, point) + group_level[index]
	var slope: Array = rule.get("g", [0.0, 0.0])
	var origin: Array = rule.get("o", [0.0, 0.0])
	return (
		float(rule["z"])
		+ float(slope[0]) * (point.x - float(origin[0]))
		+ float(slope[1]) * (point.y - float(origin[1]))
		+ group_level[index]
	)


## La altura de una regla de rampa (el tablero del puente) en un punto.
func ramp_z(rule: Dictionary, point: Vector2) -> float:
	var origin: Vector2 = Vector2(rule["o"][0], rule["o"][1])
	var direction: Vector2 = Vector2(rule["d"][0], rule["d"][1])
	var f: float = clampf((point - origin).dot(direction) / float(rule["largo"]), 0.0, 1.0)
	return lerpf(float(rule["z0"]), float(rule["z1"]), f)


## La rasante del tránsito en un punto: lineal dentro de cada triángulo de la rejilla.
func base_z(point: Vector2) -> float:
	if not inside(point):
		return plan.transit_base_at(point)
	return grid_linear(vertex_base, point)


## La altura del terreno que se ve en un punto: la de la malla del relieve detallado.
func terrain_z(point: Vector2) -> float:
	if not inside(point):
		return plan.height_at(point)
	return grid_linear(vertex_heights, point)


## La normal suave de la rasante en un punto: la de las esquinas de su triángulo de la
## rejilla, mezcladas como en la malla del terreno (la misma desde los dos lados de una
## línea de la rejilla, así que no deja aristas marcadas).
func base_normal(point: Vector2) -> Vector3:
	if not inside(point):
		return Vector3.UP
	var cell: Vector2i = Vector2i(
		clampi(floori(point.x / STEP), 0, cells.x - 1),
		clampi(floori(point.y / STEP), 0, cells.y - 1)
	)
	var k: int = 0 if point.y / STEP - cell.y >= point.x / STEP - cell.x else 1
	var corners: PackedInt32Array = triangle_vertices(cell, k)
	var w: Vector3 = weights(point, cell, k)
	return (
		(
			vertex_normal(vertex_base, corners[0]) * w.x
			+ vertex_normal(vertex_base, corners[1]) * w.y
			+ vertex_normal(vertex_base, corners[2]) * w.z
		)
		. normalized()
	)


## La normal de una pieza que no sigue la rasante (un plano o la rampa del puente).
func rule_normal(index: int, point: Vector2) -> Vector3:
	var rule: Dictionary = groups[index]["regla"]
	var slope: Vector2 = Vector2.ZERO
	if String(rule["tipo"]) == "plano":
		var g: Array = rule.get("g", [0.0, 0.0])
		slope = Vector2(g[0], g[1])
	elif String(rule["tipo"]) == "rampa":
		var origin: Vector2 = Vector2(rule["o"][0], rule["o"][1])
		var direction: Vector2 = Vector2(rule["d"][0], rule["d"][1])
		var f: float = (point - origin).dot(direction) / float(rule["largo"])
		if f > 0.0 and f < 1.0:
			slope = direction * (float(rule["z1"]) - float(rule["z0"])) / float(rule["largo"])
	return Vector3(-slope.x, 1.0, slope.y).normalized()


## La normal en un punto de la rejilla de [param values], como la calcula CityTerrain.
func vertex_normal(values: PackedFloat32Array, v: int) -> Vector3:
	var nx: int = cells.x + 1
	var i: int = v % nx
	var j: int = v / nx
	var west: float = values[j * nx + maxi(i - 1, 0)]
	var east: float = values[j * nx + mini(i + 1, cells.x)]
	var south: float = values[maxi(j - 1, 0) * nx + i]
	var north: float = values[mini(j + 1, cells.y) * nx + i]
	return Vector3(west - east, 2.0 * STEP, north - south).normalized()


## Los índices de las tres esquinas de un triángulo de la rejilla, en el orden de
## [method weights]: suroeste, noreste y la tercera (noroeste o sureste).
func triangle_vertices(cell: Vector2i, k: int) -> PackedInt32Array:
	var nx: int = cells.x + 1
	var south_west: int = cell.y * nx + cell.x
	var third: int = south_west + nx if k == 0 else south_west + 1
	return PackedInt32Array([south_west, south_west + nx + 1, third])


## Pesos de las tres esquinas (suroeste, noreste, tercera) en un punto del triángulo.
static func weights(point: Vector2, cell: Vector2i, k: int) -> Vector3:
	var u: float = point.x / STEP - cell.x
	var v: float = point.y / STEP - cell.y
	if k == 0:
		return Vector3(1.0 - v, u, v - u)
	return Vector3(1.0 - u, v, u - v)


## El triángulo de la rejilla como polígono, en sentido antihorario.
static func triangle_polygon(cell: Vector2i, k: int) -> PackedVector2Array:
	var corner: Vector2 = Vector2(cell) * STEP
	if k == 0:
		return PackedVector2Array(
			[corner, corner + Vector2(STEP, STEP), corner + Vector2(0.0, STEP)]
		)
	return PackedVector2Array([corner, corner + Vector2(STEP, 0.0), corner + Vector2(STEP, STEP)])


## El triángulo [param k] (0: noroeste, 1: sureste) de la celda [param cell].
func triangle_id(cell: Vector2i, k: int) -> int:
	return (cell.y * cells.x + cell.x) * 2 + k


## ¿Toca el tránsito el triángulo de la rejilla?
func is_touched(cell: Vector2i, k: int) -> bool:
	if not cell_inside(cell):
		return false
	return touched[triangle_id(cell, k)] != 0


func grid_linear(values: PackedFloat32Array, point: Vector2) -> float:
	var fx: float = point.x / STEP
	var fy: float = point.y / STEP
	var i: int = clampi(floori(fx), 0, cells.x - 1)
	var j: int = clampi(floori(fy), 0, cells.y - 1)
	var u: float = fx - i
	var v: float = fy - j
	var nx: int = cells.x + 1
	var south_west: int = j * nx + i
	var corner: float = values[south_west]
	var opposite: float = values[south_west + nx + 1]
	if v >= u:
		return corner * (1.0 - v) + opposite * u + values[south_west + nx] * (v - u)
	return corner * (1.0 - u) + opposite * v + values[south_west + 1] * (u - v)


func inside(point: Vector2) -> bool:
	return point.x >= 0.0 and point.y >= 0.0 and point.x <= plan.size.x and point.y <= plan.size.y


func cell_inside(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < cells.x and cell.y < cells.y


func _prepare() -> void:
	groups = plan.transit["grupos"]
	_levels = plan.transit["niveles"]
	for data: Dictionary in groups:
		follows_base.append(1 if String(data["regla"]["tipo"]) == "terreno" else 0)
		group_level.append(float(_levels[data["clase"]]))
	cells = plan.relief_size
	cells_per_sector = int(round(plan.sector_size / STEP))
	vertex_heights = plan.vertex_grid(plan.heights)
	vertex_base = plan.vertex_grid(plan.transit_heights)
	carve = plan.transit_carve
	touched.resize(cells.x * cells.y * 2)
	for cell: int in cells.x * cells.y:
		var code: int = plan.transit_grid[cell]
		for k: int in 2:
			var state: int = (code >> (3 * k)) & 3
			touched[cell * 2 + k] = (
				1 if state == TransitSector.FULL or state == TransitSector.DEEP else 0
			)
	var grid: Vector2i = plan.sector_grid()
	for row: int in grid.y:
		for column: int in grid.x:
			_sectors.append(TransitSector.new(self, Vector2i(column, row)))
	_prepare_tracks()


## Los tramos de las vías del tren (abiertos o a ras en los pasos a nivel) y los del
## tranvía (a ras), con lo que mide cada uno hasta cada punto.
func _prepare_tracks() -> void:
	tracks.clear()
	for via: Dictionary in plan.transit.get("vias", []):
		var ends: PackedVector2Array = PackedVector2Array()
		for stretch: Dictionary in via["tramos"]:
			var flat: Array = stretch["puntos"]
			ends.append(Vector2(flat[0][0], flat[0][1]))
			ends.append(Vector2(flat[flat.size() - 1][0], flat[flat.size() - 1][1]))
		for stretch: Dictionary in via["tramos"]:
			var line: PackedVector2Array = PackedVector2Array()
			var heights: PackedFloat32Array = PackedFloat32Array()
			for p: Array in stretch["puntos"]:
				line.append(Vector2(p[0], p[1]))
				heights.append(p[2])
			var open: bool = String(stretch["tipo"]) == "abierta"
			var track: Dictionary = _track(line, heights if open else PackedFloat32Array())
			track["carril"] = TransitRails.RAIL_OFFSET
			if not open:
				track["carriles"] = _rails(line, TransitRails.RAIL_OFFSET)
			track["puntas"] = [_is_loose(ends, line[0]), _is_loose(ends, line[line.size() - 1])]
			tracks.append(track)
	for item: Dictionary in plan.transit.get("tranvias", []):
		var line: PackedVector2Array = PackedVector2Array()
		for p: Array in item["puntos"]:
			line.append(Vector2(p[0], p[1]))
		var track: Dictionary = _track(line, PackedFloat32Array())
		track["carril"] = TransitRails.TRAM_OFFSET
		track["carriles"] = _rails(line, TransitRails.TRAM_OFFSET)
		track["puntas"] = [false, false]
		tracks.append(track)


## Un tramo; si va a ras, con la línea de cada carril (la de la izquierda primero),
## calculada de una vez para que los sectores la corten igual.
static func _track(line: PackedVector2Array, heights: PackedFloat32Array) -> Dictionary:
	return {
		"puntos": line,
		"z": heights,
		"largo": TransitEdges.arc_lengths(line),
		"abierta": not heights.is_empty(),
		"carriles": [],
	}


static func _rails(line: PackedVector2Array, offset: float) -> Array:
	var normals: PackedVector2Array = TransitEdges.line_normals(line)
	var result: Array = []
	for side: float in [1.0, -1.0]:
		var rail: PackedVector2Array = PackedVector2Array()
		for k: int in line.size():
			rail.append(line[k] + normals[k] * offset * side)
		result.append(rail)
	return result


## ¿Acaba la vía en este punto (no sigue en otro de sus tramos)?
static func _is_loose(ends: PackedVector2Array, point: Vector2) -> bool:
	var count: int = 0
	for end: Vector2 in ends:
		if end.distance_to(point) < 0.05:
			count += 1
	return count <= 1


## Reparte entre los sectores lo que toca a cada uno (por su caja).
func _assign() -> void:
	for index: int in groups.size():
		var points: Array = groups[index]["puntos"]
		var triangles: Array = groups[index]["triangulos"]
		for t: int in range(0, triangles.size(), 3):
			var box: Rect2 = Rect2()
			for n: int in 3:
				var v: int = int(triangles[t + n]) * 2
				var p: Vector2 = Vector2(points[v], points[v + 1])
				box = Rect2(p, Vector2.ZERO) if n == 0 else box.expand(p)
			for sector: TransitSector in _sectors_in(box):
				sector.add_item("triangles", index)
				sector.add_item("triangles", t)
			var low: Vector2i = Vector2i((box.position / INDEX_CELL).floor())
			var high: Vector2i = Vector2i((box.end / INDEX_CELL).floor())
			for row: int in range(low.y, high.y + 1):
				for column: int in range(low.x, high.x + 1):
					var key: Vector2i = Vector2i(column, row)
					var pairs: PackedInt32Array = _index.get(key, PackedInt32Array())
					pairs.append_array([index, t])
					_index[key] = pairs
	var data: Dictionary = plan.transit
	var fill_ids: Array = data["relleno"]["triangulos"]
	for n: int in fill_ids.size():
		var id: int = fill_ids[n]
		_sector_of_cell(Vector2i((id / 2) % cells.x, (id / 2) / cells.x)).add_item("fills", n)
	_assign_lines(data["aristas"], "edges")
	_assign_lines(data["muros"], "walls")
	_assign_lines(data["barandillas"], "rails")
	_assign_lines(data["marcas"]["ejes"], "axes")
	var crossings: Array = data["marcas"]["pasos"]
	for index: int in crossings.size():
		var center: Vector2 = Vector2(crossings[index]["centro"][0], crossings[index]["centro"][1])
		for sector: TransitSector in _sectors_in(Rect2(center, Vector2.ZERO).grow(40.0)):
			sector.add_item("crossings", index)
	_assign_tracks()


## Reparte los tramos de las vías por sus segmentos: cada sector recibe, en orden, los
## pares (vía, segmento) que caen en él (con el ancho del balasto de margen).
func _assign_tracks() -> void:
	var margin: float = TransitRails.BALLAST_HALF.y + 0.5
	for index: int in tracks.size():
		var line: PackedVector2Array = tracks[index]["puntos"]
		for k: int in line.size() - 1:
			var box: Rect2 = Rect2(line[k], Vector2.ZERO).expand(line[k + 1]).grow(margin)
			for sector: TransitSector in _sectors_in(box):
				sector.add_item("tracks", index)
				sector.add_item("tracks", k)


## Reparte líneas por su caja (los puntos van seguidos, x e y, o de dos en dos o de tres
## en tres en listas).
func _assign_lines(items: Array, field: String) -> void:
	for index: int in items.size():
		var flat: Array = items[index]["puntos"]
		var box: Rect2 = Rect2()
		if not flat.is_empty() and flat[0] is Array:
			for k: int in flat.size():
				var p: Vector2 = Vector2(flat[k][0], flat[k][1])
				box = Rect2(p, Vector2.ZERO) if k == 0 else box.expand(p)
		else:
			for k: int in range(0, flat.size(), 2):
				var p: Vector2 = Vector2(flat[k], flat[k + 1])
				box = Rect2(p, Vector2.ZERO) if k == 0 else box.expand(p)
		for sector: TransitSector in _sectors_in(box.grow(1.0)):
			sector.add_item(field, index)


func _sectors_in(box: Rect2) -> Array[TransitSector]:
	var grid: Vector2i = plan.sector_grid()
	var low: Vector2i = plan.sector_of(box.position)
	var high: Vector2i = plan.sector_of(box.end)
	var result: Array[TransitSector] = []
	for row: int in range(low.y, high.y + 1):
		for column: int in range(low.x, high.x + 1):
			result.append(_sectors[row * grid.x + column])
	return result


func _build_sector(index: int) -> void:
	_sectors[index].build()


## Lo de cada sector, junto: sus mallas y su colisión.
func _merge() -> void:
	for sector: TransitSector in _sectors:
		if not sector.meshes.is_empty():
			meshes[sector.sector] = sector.meshes
		collision[sector.sector] = sector.collision
		for key: String in sector.stats:
			stats[key] = stats.get(key, 0) + sector.stats[key]
		for key: String in sector.edge_stats:
			stats[key] = stats.get(key, 0) + sector.edge_stats[key]
		for model: String in sector.instances:
			if not instances.has(sector.sector):
				instances[sector.sector] = {}
			var by_model: Dictionary = instances[sector.sector]
			by_model[model] = by_model.get(model, []) + sector.instances[model]


func _sector_of_cell(cell: Vector2i) -> TransitSector:
	var grid: Vector2i = plan.sector_grid()
	var sector: Vector2i = Vector2i(
		mini(cell.x / cells_per_sector, grid.x - 1), mini(cell.y / cells_per_sector, grid.y - 1)
	)
	return _sectors[sector.y * grid.x + sector.x]


## Tapas de registro y sumideros, como instancias por sector.
func _build_details() -> void:
	var details: Dictionary = plan.transit["detalles"]
	var count: int = 0
	for item: Dictionary in details["tapas"]:
		_add_detail("tapa_" + String(item["tipo"]), item)
		count += 1
	for item: Dictionary in details["sumideros"]:
		_add_detail("sumidero", item)
		count += 1
	stats["detalles"] = count


func _add_detail(model: String, item: Dictionary) -> void:
	var point: Vector2 = Vector2(item["pos"][0], item["pos"][1])
	var basis: Basis = Basis(Vector3.UP, deg_to_rad(float(item["angulo"])))
	var origin: Vector3 = CityPlan.to_world(point, float(item["z"]))
	var sector: Vector2i = plan.sector_of(point)
	if not instances.has(sector):
		instances[sector] = {}
	var by_model: Dictionary = instances[sector]
	if not by_model.has(model):
		by_model[model] = []
	by_model[model].append(Transform3D(basis, origin))
