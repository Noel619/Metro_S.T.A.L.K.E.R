class_name CityPlan
extends RefCounted
## El plano de Tumansk dentro de Godot: lee data/ciudad/ (plano.json, relieve.png,
## suelo.png y la red de tránsito, transito.json con su rasante.png, que genera `make
## ciudad`) y responde preguntas sobre él: la altura del terreno en un punto, el sector, la
## zona…
##
## Coordenadas del plano: metros, x hacia el este e y hacia el norte, con el origen en la
## esquina suroeste. En el mundo, x es el este, y es la altura y el norte es -z (como en la
## brújula): el punto (x, y) del plano a la altura h es Vector3(x, h, -y).
##
## Godot no importa data/ciudad/ (tiene .gdignore): los archivos se leen tal cual. Así el
## relieve conserva sus 16 bits, pero el plano solo se carga ejecutando desde el proyecto
## (el editor), no en una build exportada.

const DATA_DIR: String = "res://data/ciudad/"
const COLUMNS: String = "ABCDEFGH"

## El plano completo, tal como sale de plano.json.
var data: Dictionary = {}
## Tamaño del mapa jugable, en metros.
var size: Vector2 = Vector2.ZERO
## Lado de los sectores de carga, en metros.
var sector_size: float = 200.0
## Metros por celda del relieve.
var relief_resolution: float = 2.0
var relief_size: Vector2i = Vector2i.ZERO
## Alturas del relieve en metros, fila a fila de sur a norte; cada valor es el centro de
## su celda.
var heights: PackedFloat32Array = PackedFloat32Array()
## Suelo de la maqueta: color bajo la nieve (RGB) y cuánta nieve lo cubre (A). La primera
## fila es el borde norte.
var ground: Image
## La red de tránsito (transito.json): grupos de superficie con su regla de altura,
## aristas, muros, escaleras, marcas viales y detalles.
var transit: Dictionary = {}
## La rasante del tránsito, como [member heights]: el terreno nivelado sin escombros, con
## los muelles rellenos hasta el agua. Lo que se pisa va a esta altura más su nivel.
var transit_heights: PackedFloat32Array = PackedFloat32Array()
## Lo que el tránsito cubre de cada triángulo de la rejilla del relieve (rejilla.png): un
## byte por celda, fila a fila de sur a norte, con el estado del triángulo noroeste en los
## bits 0-2 y el del sureste en los 3-5.
var transit_grid: PackedByteArray = PackedByteArray()
## Cuánto se rebaja la colisión del relieve en cada punto de la rejilla (rebaje.png), en
## metros, fila a fila de sur a norte.
var transit_carve: PackedFloat32Array = PackedFloat32Array()
## Qué falló al cargar; vacío si nada.
var error: String = ""

var _zones: Dictionary = {}
var _river: PackedVector2Array = PackedVector2Array()


## Carga el plano de data/ciudad/. Si algo falla, [member error] dice qué.
static func load_default() -> CityPlan:
	var plan: CityPlan = CityPlan.new()
	plan.load_from(DATA_DIR)
	return plan


## Del plano (x, y) a la altura [param height] al mundo.
static func to_world(point: Vector2, height: float = 0.0) -> Vector3:
	return Vector3(point.x, height, -point.y)


## Del mundo al plano.
static func to_plan(position: Vector3) -> Vector2:
	return Vector2(position.x, -position.z)


## Nombre del sector (columnas A-H de oeste a este, filas 1-6 de sur a norte).
static func sector_name(sector: Vector2i) -> String:
	return COLUMNS[clampi(sector.x, 0, COLUMNS.length() - 1)] + str(sector.y + 1)


## Número fijo entre 0 y 1 para cada clave: el mismo que da azar() en tools/ciudad/.
static func chance(key: String) -> float:
	return key.md5_text().substr(0, 8).hex_to_int() / 4294967295.0


## ¿Es un hito (de los que se ven de lejos para orientarse)? Algunos edificios llevan la
## clave con valor nulo: la grúa que cuenta como hito es solo la primera de las cuatro.
static func is_landmark(building: Dictionary) -> bool:
	return building.get("hito") != null


## Un anillo de plano.json ([[x, y], …]) como polígono, sin repetir el primer punto.
static func ring(points: Array) -> PackedVector2Array:
	var result: PackedVector2Array = line(points)
	if result.size() > 2 and result[0].is_equal_approx(result[result.size() - 1]):
		result.remove_at(result.size() - 1)
	return result


## Una lista de puntos de plano.json como polilínea.
static func line(points: Array) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for point: Array in points:
		result.append(Vector2(point[0], point[1]))
	return result


## Lee los píxeles de un PNG en gris de 16 bits (el formato del relieve). Godot convierte
## esos PNG a 8 bits al cargarlos, así que se descomprimen aquí. Devuelve el ancho, el
## alto y los bytes en orden de PNG (filas de arriba abajo, cada valor en big-endian), o
## un diccionario vacío si el archivo no es de ese tipo.
static func decode_gray16(bytes: PackedByteArray) -> Dictionary:
	var signature: PackedByteArray = PackedByteArray([137, 80, 78, 71, 13, 10, 26, 10])
	if bytes.size() < 8 or bytes.slice(0, 8) != signature:
		return {}
	var width: int = 0
	var height: int = 0
	var compressed: PackedByteArray = PackedByteArray()
	var pos: int = 8
	while pos + 8 <= bytes.size():
		var length: int = bytes.decode_u32(pos)
		length = _swap32(length)
		var kind: String = bytes.slice(pos + 4, pos + 8).get_string_from_ascii()
		var body: PackedByteArray = bytes.slice(pos + 8, pos + 8 + length)
		if kind == "IHDR":
			width = _swap32(body.decode_u32(0))
			height = _swap32(body.decode_u32(4))
			# Solo gris de 16 bits sin entrelazar.
			if body[8] != 16 or body[9] != 0 or body[12] != 0:
				return {}
		elif kind == "IDAT":
			compressed.append_array(body)
		elif kind == "IEND":
			break
		pos += 12 + length
	var stride: int = width * 2
	var raw: PackedByteArray = compressed.decompress(
		height * (stride + 1), FileAccess.COMPRESSION_DEFLATE
	)
	if width == 0 or raw.size() != height * (stride + 1):
		return {}
	return {"width": width, "height": height, "bytes": _unfilter(raw, height, stride, 2)}


## Carga el plano desde una carpeta. Devuelve OK o el error (y lo deja en [member error]).
func load_from(directory: String) -> Error:
	var text: String = FileAccess.get_file_as_string(directory + "plano.json")
	if text.is_empty():
		return _fail("No está %splano.json: hay que ejecutar «make ciudad»." % directory)
	var parsed: Variant = JSON.parse_string(text)
	if not parsed is Dictionary:
		return _fail("plano.json no se puede leer.")
	data = parsed
	if not data.has("suelo"):
		return _fail("plano.json es de una versión anterior: hay que ejecutar «make ciudad».")
	size = Vector2(data["tamano"][0], data["tamano"][1])
	sector_size = data["sector"]
	var relief: Dictionary = data["relieve"]
	relief_resolution = relief["resolucion"]
	var decoded: Dictionary = decode_gray16(
		FileAccess.get_file_as_bytes(directory + String(relief["archivo"]))
	)
	if decoded.is_empty():
		return _fail("No se puede leer el relieve (%s)." % relief["archivo"])
	relief_size = Vector2i(decoded["width"], decoded["height"])
	heights = _heights_from(decoded["bytes"], relief_size)
	ground = Image.new()
	var ground_bytes: PackedByteArray = FileAccess.get_file_as_bytes(
		directory + String(data["suelo"]["archivo"])
	)
	if ground_bytes.is_empty() or ground.load_png_from_buffer(ground_bytes) != OK:
		return _fail("No se puede leer el suelo (%s)." % data["suelo"]["archivo"])
	for key: String in data["zonas"]:
		var zone: Dictionary = data["zonas"][key]
		if zone["poligono"] != null:
			_zones[key.to_int()] = ring(zone["poligono"][0])
	_river = ring(data["rio"]["poligono"][0])
	return _load_transit(directory)


## ¿Se cargó bien?
func is_loaded() -> bool:
	return error.is_empty() and not heights.is_empty()


## Altura del terreno (con los montones de escombros) en un punto del plano. Fuera del
## mapa se repite la del borde.
func height_at(point: Vector2) -> float:
	return _bilinear(heights, point)


## Altura de la rasante del tránsito en un punto (bilineal, como [method height_at]).
func transit_base_at(point: Vector2) -> float:
	return _bilinear(transit_heights, point)


## Las alturas de [param values] (el relieve o la rasante) en los puntos de la rejilla de
## [member relief_resolution] metros (las esquinas de las celdas): (ancho + 1) × (alto + 1)
## valores, fila a fila de sur a norte. Son las mismas que da [method height_at] en esos
## puntos (la media de las cuatro celdas que los rodean).
func vertex_grid(values: PackedFloat32Array) -> PackedFloat32Array:
	var nx: int = relief_size.x + 1
	var ny: int = relief_size.y + 1
	var result: PackedFloat32Array = PackedFloat32Array()
	result.resize(nx * ny)
	for j: int in ny:
		var south: int = clampi(j - 1, 0, relief_size.y - 1) * relief_size.x
		var north: int = clampi(j, 0, relief_size.y - 1) * relief_size.x
		for i: int in nx:
			var west: int = clampi(i - 1, 0, relief_size.x - 1)
			var east: int = clampi(i, 0, relief_size.x - 1)
			result[j * nx + i] = (
				(
					values[south + west]
					+ values[south + east]
					+ values[north + west]
					+ values[north + east]
				)
				* 0.25
			)
	return result


## El punto del plano sobre el terreno, en coordenadas del mundo.
func ground_point(point: Vector2, lift: float = 0.0) -> Vector3:
	return to_world(point, height_at(point) + lift)


## Columnas y filas de sectores.
func sector_grid() -> Vector2i:
	return Vector2i(ceili(size.x / sector_size), ceili(size.y / sector_size))


## Sector que contiene un punto (los de fuera del mapa cuentan en el del borde).
func sector_of(point: Vector2) -> Vector2i:
	var grid: Vector2i = sector_grid()
	return Vector2i(
		clampi(floori(point.x / sector_size), 0, grid.x - 1),
		clampi(floori(point.y / sector_size), 0, grid.y - 1)
	)


## Rectángulo de un sector en el plano.
func sector_rect(sector: Vector2i) -> Rect2:
	return Rect2(Vector2(sector) * sector_size, Vector2.ONE * sector_size)


## Zona del plano (1-8) que contiene el punto; 0 si no está en ninguna (el río).
func zone_at(point: Vector2) -> int:
	for zone: int in _zones:
		if Geometry2D.is_point_in_polygon(point, _zones[zone]):
			return zone
	return 0


## ¿Está el punto sobre el río (dentro de sus orillas)?
func is_on_river(point: Vector2) -> bool:
	return Geometry2D.is_point_in_polygon(point, _river)


## Nombre de una zona, o "el río" para la 0 cuando el punto está sobre el hielo.
func zone_label(point: Vector2) -> String:
	var zone: int = zone_at(point)
	if zone == 0:
		return "El río" if Geometry2D.is_point_in_polygon(point, _river) else "Fuera del plano"
	return "%d · %s" % [zone, data["zonas"][str(zone)]["nombre"]]


## Punto del eje monumental: [param along] avanza por la avenida hacia el noreste (0 es
## el centro de la plaza del Trabajo) y [param across] se aparta (positivo, al noroeste).
func axis_point(along: float, across: float = 0.0) -> Vector2:
	var axis: Dictionary = data["eje_monumental"]
	var angle: float = deg_to_rad(axis["angulo"])
	var origin: Vector2 = Vector2(axis["origen"][0], axis["origen"][1])
	return (
		origin + Vector2(cos(angle), sin(angle)) * along + Vector2(-sin(angle), cos(angle)) * across
	)


## La Zona Cero (donde cayó la bomba), en el plano.
func ground_zero() -> Vector2:
	return Vector2(data["zona_cero"][0], data["zona_cero"][1])


func _bilinear(values: PackedFloat32Array, point: Vector2) -> float:
	var fx: float = clampf(point.x / relief_resolution - 0.5, 0.0, relief_size.x - 1.001)
	var fy: float = clampf(point.y / relief_resolution - 0.5, 0.0, relief_size.y - 1.001)
	var i: int = int(fx)
	var j: int = int(fy)
	var k: int = j * relief_size.x + i
	var south: float = lerpf(values[k], values[k + 1], fx - i)
	var north: float = lerpf(values[k + relief_size.x], values[k + relief_size.x + 1], fx - i)
	return lerpf(south, north, fy - j)


func _load_transit(directory: String) -> Error:
	if not data.has("transito"):
		return _fail("plano.json no trae la red de tránsito: hay que ejecutar «make ciudad».")
	var text: String = FileAccess.get_file_as_string(
		directory + String(data["transito"]["archivo"])
	)
	var parsed: Variant = JSON.parse_string(text)
	if not parsed is Dictionary:
		return _fail("No se puede leer la red de tránsito (%s)." % data["transito"]["archivo"])
	transit = parsed
	var decoded: Dictionary = decode_gray16(
		FileAccess.get_file_as_bytes(directory + String(transit["rasante"]["archivo"]))
	)
	if decoded.is_empty() or Vector2i(decoded["width"], decoded["height"]) != relief_size:
		return _fail("No se puede leer la rasante del tránsito.")
	transit_heights = _heights_from(decoded["bytes"], relief_size)
	return _load_transit_grid(directory)


## La rejilla del tránsito (qué tapa de cada triángulo del relieve) y el rebaje.
func _load_transit_grid(directory: String) -> Error:
	var grid: Image = Image.new()
	var grid_bytes: PackedByteArray = FileAccess.get_file_as_bytes(
		directory + String(transit["rejilla"]["archivo"])
	)
	if grid_bytes.is_empty() or grid.load_png_from_buffer(grid_bytes) != OK:
		return _fail("No se puede leer la rejilla del tránsito.")
	grid.convert(Image.FORMAT_L8)
	if Vector2i(grid.get_width(), grid.get_height()) != relief_size:
		return _fail("La rejilla del tránsito no casa con el relieve.")
	var rows: PackedByteArray = grid.get_data()
	transit_grid.resize(rows.size())
	for j: int in relief_size.y:
		var src: int = (relief_size.y - 1 - j) * relief_size.x
		for i: int in relief_size.x:
			transit_grid[j * relief_size.x + i] = rows[src + i]
	var carve: Dictionary = decode_gray16(
		FileAccess.get_file_as_bytes(directory + String(transit["rebaje"]["archivo"]))
	)
	if carve.is_empty() or Vector2i(carve["width"], carve["height"]) != relief_size + Vector2i.ONE:
		return _fail("No se puede leer el rebaje del tránsito.")
	transit_carve = _millimeters_from(carve["bytes"], relief_size + Vector2i.ONE)
	return OK


func _fail(message: String) -> Error:
	error = message
	push_error("Plano de la ciudad: " + message)
	return ERR_CANT_OPEN


static func _swap32(value: int) -> int:
	return (
		((value & 0xFF) << 24)
		| ((value & 0xFF00) << 8)
		| ((value >> 8) & 0xFF00)
		| ((value >> 24) & 0xFF)
	)


## Deshace los filtros de PNG fila a fila (ninguno, resta, arriba, media y Paeth).
static func _unfilter(raw: PackedByteArray, rows: int, stride: int, bpp: int) -> PackedByteArray:
	var out: PackedByteArray = PackedByteArray()
	out.resize(rows * stride)
	for row: int in rows:
		var src: int = row * (stride + 1) + 1
		var dst: int = row * stride
		var up: int = dst - stride
		var filter: int = raw[src - 1]
		for i: int in stride:
			var left: int = out[dst + i - bpp] if i >= bpp else 0
			var above: int = out[up + i] if row > 0 else 0
			var value: int = raw[src + i]
			match filter:
				1:
					value += left
				2:
					value += above
				3:
					value += (left + above) >> 1
				4:
					var corner: int = out[up + i - bpp] if row > 0 and i >= bpp else 0
					value += _paeth(left, above, corner)
			out[dst + i] = value & 255
	return out


static func _paeth(a: int, b: int, c: int) -> int:
	var p: int = a + b - c
	var pa: int = absi(p - a)
	var pb: int = absi(p - b)
	var pc: int = absi(p - c)
	if pa <= pb and pa <= pc:
		return a
	return b if pb <= pc else c


## Pasa milímetros de 16 bits a metros y da la vuelta a las filas (la 0, la del sur).
static func _millimeters_from(bytes: PackedByteArray, grid: Vector2i) -> PackedFloat32Array:
	var result: PackedFloat32Array = PackedFloat32Array()
	result.resize(grid.x * grid.y)
	for j: int in grid.y:
		var src: int = (grid.y - 1 - j) * grid.x * 2
		var dst: int = j * grid.x
		for i: int in grid.x:
			result[dst + i] = ((bytes[src] << 8) | bytes[src + 1]) / 1000.0
			src += 2
	return result


## Pasa los valores de 16 bits a metros (valor / 100 - 50) y da la vuelta a las filas,
## para que la fila 0 sea el borde sur, como el eje y del plano.
static func _heights_from(bytes: PackedByteArray, grid: Vector2i) -> PackedFloat32Array:
	var result: PackedFloat32Array = PackedFloat32Array()
	result.resize(grid.x * grid.y)
	for j: int in grid.y:
		var src: int = (grid.y - 1 - j) * grid.x * 2
		var dst: int = j * grid.x
		for i: int in grid.x:
			result[dst + i] = ((bytes[src] << 8) | bytes[src + 1]) / 100.0 - 50.0
			src += 2
	return result
