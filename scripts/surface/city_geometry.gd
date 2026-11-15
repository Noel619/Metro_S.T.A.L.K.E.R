class_name CityGeometry
extends RefCounted
## Cuentas con polígonos del plano (x al este, y al norte), para levantar la ciudad.


## Área con signo (positiva si los puntos giran en sentido antihorario).
static func signed_area(points: PackedVector2Array) -> float:
	var area: float = 0.0
	var count: int = points.size()
	for i: int in count:
		var a: Vector2 = points[i]
		var b: Vector2 = points[(i + 1) % count]
		area += a.x * b.y - b.x * a.y
	return area * 0.5


## Quita puntos repetidos, alineados y picos de ida y vuelta (giros de menos de medio
## grado o de casi 180°), y deja el polígono en sentido horario.
static func clean(points: PackedVector2Array, tolerance: float = 0.05) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for p: Vector2 in points:
		if result.is_empty() or result[result.size() - 1].distance_to(p) > tolerance:
			result.append(p)
	if result.size() > 1 and result[0].distance_to(result[result.size() - 1]) <= tolerance:
		result.remove_at(result.size() - 1)
	var changed: bool = true
	while changed and result.size() > 3:
		changed = false
		for i: int in result.size():
			var u: Vector2 = result[i] - result[(i - 1 + result.size()) % result.size()]
			var w: Vector2 = result[(i + 1) % result.size()] - result[i]
			if absf(u.cross(w)) <= 0.009 * u.length() * w.length():
				result.remove_at(i)
				changed = true
				break
	if signed_area(result) > 0.0:
		result.reverse()
	return result


## Centro de masas del polígono.
static func centroid(points: PackedVector2Array) -> Vector2:
	var area: float = 0.0
	var center: Vector2 = Vector2.ZERO
	var count: int = points.size()
	for i: int in count:
		var a: Vector2 = points[i]
		var b: Vector2 = points[(i + 1) % count]
		var cross: float = a.x * b.y - b.x * a.y
		area += cross
		center += (a + b) * cross
	if absf(area) < 1e-6:
		var mean: Vector2 = Vector2.ZERO
		for p: Vector2 in points:
			mean += p
		return mean / maxf(1.0, points.size())
	return center / (3.0 * area)


## Dirección del lado más largo (el eje de un bloque o de una nave).
static func long_axis(points: PackedVector2Array) -> Vector2:
	var best: Vector2 = Vector2.RIGHT
	var best_length: float = 0.0
	for i: int in points.size():
		var edge: Vector2 = points[(i + 1) % points.size()] - points[i]
		if edge.length() > best_length:
			best_length = edge.length()
			best = edge / best_length
	return best


## Mínimo y máximo de las proyecciones de los puntos sobre un eje.
static func extent(points: PackedVector2Array, axis: Vector2) -> Vector2:
	var low: float = INF
	var high: float = -INF
	for p: Vector2 in points:
		var d: float = p.dot(axis)
		low = minf(low, d)
		high = maxf(high, d)
	return Vector2(low, high)


## Los trozos del polígono entre dos distancias a lo largo de [param axis].
static func slice(
	points: PackedVector2Array, axis: Vector2, from: float, to: float
) -> Array[PackedVector2Array]:
	var across: Vector2 = Vector2(-axis.y, axis.x)
	var span: Vector2 = extent(points, across)
	var a: float = span.x - 1.0
	var b: float = span.y + 1.0
	var band: PackedVector2Array = PackedVector2Array(
		[
			axis * from + across * a,
			axis * to + across * a,
			axis * to + across * b,
			axis * from + across * b
		]
	)
	var pieces: Array[PackedVector2Array] = []
	for piece: PackedVector2Array in Geometry2D.intersect_polygons(points, band):
		var cleaned: PackedVector2Array = clean(piece)
		if cleaned.size() >= 3 and absf(signed_area(cleaned)) > 1.0:
			pieces.append(cleaned)
	return pieces


## El polígono escalado respecto a un punto.
static func scaled(
	points: PackedVector2Array, center: Vector2, factor: float
) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for p: Vector2 in points:
		result.append(center + (p - center) * factor)
	return result


## Triángulos del polígono. Si el triangulador de Godot no puede (puntos casi alineados),
## prueba con el polígono recompuesto y, al final, con trozos convexos.
static func triangulate(points: PackedVector2Array) -> PackedInt32Array:
	var triangles: PackedInt32Array = Geometry2D.triangulate_polygon(points)
	if not triangles.is_empty():
		return triangles
	var parts: Array[PackedVector2Array] = Geometry2D.decompose_polygon_in_convex(points)
	var result: PackedInt32Array = PackedInt32Array()
	for part: PackedVector2Array in parts:
		for i: int in range(1, part.size() - 1):
			for p: Vector2 in [part[0], part[i], part[i + 1]]:
				result.append(_index_of(points, p))
	if result.has(-1):
		return PackedInt32Array()
	return result


## Una polilínea partida en tramos de [param step] metros como mucho.
static func subdivide(line: PackedVector2Array, step: float) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for i: int in line.size() - 1:
		var a: Vector2 = line[i]
		var b: Vector2 = line[i + 1]
		var parts: int = maxi(1, ceili(a.distance_to(b) / step))
		for k: int in parts:
			result.append(a.lerp(b, float(k) / parts))
	if not line.is_empty():
		result.append(line[line.size() - 1])
	return result


## Longitud de una polilínea.
static func length(line: PackedVector2Array) -> float:
	var total: float = 0.0
	for i: int in line.size() - 1:
		total += line[i].distance_to(line[i + 1])
	return total


## Punto a [param distance] metros del principio de una polilínea, y su dirección.
static func point_along(line: PackedVector2Array, distance: float) -> Transform2D:
	var left: float = maxf(0.0, distance)
	for i: int in line.size() - 1:
		var a: Vector2 = line[i]
		var b: Vector2 = line[i + 1]
		var piece: float = a.distance_to(b)
		if left <= piece or i == line.size() - 2:
			var direction: Vector2 = (b - a).normalized() if piece > 0.0 else Vector2.RIGHT
			return Transform2D(
				direction.angle(), a.lerp(b, clampf(left / maxf(piece, 1e-6), 0.0, 1.0))
			)
		left -= piece
	return Transform2D(0.0, line[0] if not line.is_empty() else Vector2.ZERO)


static func _index_of(points: PackedVector2Array, p: Vector2) -> int:
	for i: int in points.size():
		if points[i].is_equal_approx(p):
			return i
	return -1
