class_name GridClip
extends RefCounted
## Recortes de polígonos convexos del plano contra la rejilla del relieve detallado.
##
## La rejilla tiene celdas de [param step] metros con la diagonal del suroeste al noreste
## (como las mallas de CityTerrain): cada celda son dos triángulos, el del noroeste (k = 0)
## y el del sureste (k = 1). Un punto que cae justo en una línea de la rejilla se calcula
## igual desde los dos lados (siempre desde el extremo menor del segmento), así que dos
## piezas vecinas comparten sus vértices exactos y no quedan rendijas.

## Lo que se considera un punto repetido.
const EPSILON: float = 1e-6


## Área con signo (positiva en sentido antihorario).
static func area(poly: PackedVector2Array) -> float:
	var total: float = 0.0
	var count: int = poly.size()
	for k: int in count:
		var a: Vector2 = poly[k]
		var b: Vector2 = poly[(k + 1) % count]
		total += a.x * b.y - b.x * a.y
	return total * 0.5


## La parte del polígono convexo con x <= [param c] (o x >= c si [param greater]).
static func clip_x(poly: PackedVector2Array, c: float, greater: bool) -> PackedVector2Array:
	return _clip(poly, Vector3(1.0, 0.0, c), greater)


## La parte con y <= [param c] (o y >= c).
static func clip_y(poly: PackedVector2Array, c: float, greater: bool) -> PackedVector2Array:
	return _clip(poly, Vector3(0.0, 1.0, c), greater)


## La parte con x - y <= [param c] (o x - y >= c): la diagonal de una celda.
static func clip_diagonal(poly: PackedVector2Array, c: float, greater: bool) -> PackedVector2Array:
	return _clip(poly, Vector3(1.0, -1.0, c), greater)


## La parte del polígono convexo a la izquierda de la recta de [param a] a [param b].
static func clip_left(poly: PackedVector2Array, a: Vector2, b: Vector2) -> PackedVector2Array:
	var normal: Vector2 = Vector2(b.y - a.y, a.x - b.x)
	return _clip(poly, Vector3(normal.x, normal.y, normal.dot(a)), false)


## Corta un triángulo (o un polígono convexo) por la rejilla. Devuelve las piezas, cada
## una dentro de un solo triángulo de la rejilla, como pares [celda (Vector2i), k, pieza].
static func split(poly: PackedVector2Array, step: float) -> Array:
	var pieces: Array = []
	var low: Vector2 = poly[0]
	var high: Vector2 = poly[0]
	for p: Vector2 in poly:
		low = low.min(p)
		high = high.max(p)
	var i0: int = floori(low.x / step)
	var i1: int = floori(high.x / step)
	var rest: PackedVector2Array = poly
	for i: int in range(i0, i1 + 1):
		var column: PackedVector2Array = rest
		if i < i1:
			column = clip_x(rest, (i + 1) * step, false)
			rest = clip_x(rest, (i + 1) * step, true)
		if column.size() < 3:
			continue
		_split_column(column, i, step, pieces)
	return pieces


## El polígono convexo menos otro convexo: hasta un trozo convexo por lado del que corta.
static func subtract(poly: PackedVector2Array, cutter: PackedVector2Array) -> Array:
	var result: Array = []
	var rest: PackedVector2Array = poly
	var count: int = cutter.size()
	var ccw: bool = area(cutter) > 0.0
	for k: int in count:
		var a: Vector2 = cutter[k]
		var b: Vector2 = cutter[(k + 1) % count]
		if not ccw:
			var swap: Vector2 = a
			a = b
			b = swap
		# Lo que queda a la derecha de este lado está fuera del que corta.
		var outside: PackedVector2Array = clip_left(rest, b, a)
		if outside.size() >= 3 and absf(area(outside)) > EPSILON:
			result.append(outside)
		rest = clip_left(rest, a, b)
		if rest.size() < 3:
			return result
	return result


## Una polilínea partida donde cruza las líneas de la rejilla (las verticales, las
## horizontales y las diagonales), para que cada tramo caiga en un solo triángulo.
static func subdivide(line: PackedVector2Array, step: float) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for k: int in line.size() - 1:
		var p: Vector2 = line[k]
		var q: Vector2 = line[k + 1]
		result.append(p)
		var cuts: Array[float] = []
		_crossings(p.x, q.x, step, cuts)
		_crossings(p.y, q.y, step, cuts)
		_crossings(p.x - p.y, q.x - q.y, step, cuts)
		cuts.sort()
		var last: float = 0.0
		for t: float in cuts:
			if t - last > 1e-5 and t < 1.0 - 1e-5:
				result.append(_point_on(p, q, t))
				last = t
	if not line.is_empty():
		result.append(line[line.size() - 1])
	return result


static func _split_column(column: PackedVector2Array, i: int, step: float, pieces: Array) -> void:
	var low: float = column[0].y
	var high: float = column[0].y
	for p: Vector2 in column:
		low = minf(low, p.y)
		high = maxf(high, p.y)
	var j0: int = floori(low / step)
	var j1: int = floori(high / step)
	var rest: PackedVector2Array = column
	for j: int in range(j0, j1 + 1):
		var cell: PackedVector2Array = rest
		if j < j1:
			cell = clip_y(rest, (j + 1) * step, false)
			rest = clip_y(rest, (j + 1) * step, true)
		if cell.size() < 3:
			continue
		var diagonal: float = (i - j) * step
		var north_west: PackedVector2Array = clip_diagonal(cell, diagonal, false)
		var south_east: PackedVector2Array = clip_diagonal(cell, diagonal, true)
		if north_west.size() >= 3 and area(north_west) > EPSILON:
			pieces.append([Vector2i(i, j), 0, north_west])
		if south_east.size() >= 3 and area(south_east) > EPSILON:
			pieces.append([Vector2i(i, j), 1, south_east])


## Sutherland-Hodgman contra el semiplano a·x + b·y <= c (o >= c), con [param line] =
## (a, b, c).
static func _clip(poly: PackedVector2Array, line: Vector3, greater: bool) -> PackedVector2Array:
	var out: PackedVector2Array = PackedVector2Array()
	var count: int = poly.size()
	if count == 0:
		return out
	var side: float = -1.0 if greater else 1.0
	for k: int in count:
		var p: Vector2 = poly[k]
		var q: Vector2 = poly[(k + 1) % count]
		var dp: float = (line.x * p.x + line.y * p.y - line.z) * side
		var dq: float = (line.x * q.x + line.y * q.y - line.z) * side
		if dp <= 0.0:
			_append(out, p)
		if (dp < 0.0 and dq > 0.0) or (dp > 0.0 and dq < 0.0):
			_append(out, _cross(p, q, line))
	if out.size() > 2 and out[0].distance_squared_to(out[out.size() - 1]) < EPSILON * EPSILON:
		out.remove_at(out.size() - 1)
	return out


## Donde el segmento cruza la recta, calculado siempre desde su extremo menor.
static func _cross(p: Vector2, q: Vector2, line: Vector3) -> Vector2:
	if q.x < p.x or (q.x == p.x and q.y < p.y):
		var swap: Vector2 = p
		p = q
		q = swap
	var dp: float = line.x * p.x + line.y * p.y - line.z
	var dq: float = line.x * q.x + line.y * q.y - line.z
	var point: Vector2 = p + (q - p) * (dp / (dp - dq))
	# En las rectas verticales u horizontales (las de la rejilla), la coordenada exacta.
	if line.y == 0.0:
		point.x = line.z / line.x
	elif line.x == 0.0:
		point.y = line.z / line.y
	return point


static func _append(out: PackedVector2Array, p: Vector2) -> void:
	if out.is_empty() or out[out.size() - 1].distance_squared_to(p) > EPSILON * EPSILON:
		out.append(p)


static func _crossings(a: float, b: float, step: float, cuts: Array[float]) -> void:
	if absf(b - a) < 1e-9:
		return
	var low: float = minf(a, b)
	var high: float = maxf(a, b)
	var first: int = floori(low / step) + 1
	var last: int = ceili(high / step) - 1
	for n: int in range(first, last + 1):
		cuts.append((n * step - a) / (b - a))


static func _point_on(p: Vector2, q: Vector2, t: float) -> Vector2:
	# Desde el extremo menor, como en los recortes.
	if q.x < p.x or (q.x == p.x and q.y < p.y):
		return q + (p - q) * (1.0 - t)
	return p + (q - p) * t
