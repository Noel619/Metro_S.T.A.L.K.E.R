class_name CityNav
extends RefCounted
## Por dónde puede ir un perro (F3-10): una rejilla de 1 m sobre el plano de la
## ciudad, con lo que no se cruza marcado como obstáculo, y la búsqueda de caminos
## (A*). Sale de los datos del plano (no de la física): los edificios, el tambor del
## vestíbulo, los vehículos, las vallas, los escombros altos y los terraplenes del
## ferrocarril. Lo pequeño (troncos, farolas, cascotes) lo esquiva el propio cuerpo
## del perro al moverse.
##
## Todo va en coordenadas del plano (x al este, y al norte); [method CityPlan.to_world]
## lo lleva al mundo.

## Lo que mide cada casilla (m).
const CELL: float = 1.0
## Los escombros más altos que esto no se saltan.
const RUBBLE_HEIGHT: float = 1.2
## El vestíbulo del metro: su tambor y su columnata (el resto de su parcela es plaza).
const VESTIBULE_ID: String = "PLZ-06"
const VESTIBULE_CENTER: Vector2 = Vector2(326.0, 299.5)
const VESTIBULE_RADIUS: float = 12.6

## La zona que cubre la rejilla, en metros del plano.
var region: Rect2i = Rect2i()
var grid: AStarGrid2D = AStarGrid2D.new()


## Una rejilla vacía (todo se puede pisar) sobre [param area].
static func empty(area: Rect2i) -> CityNav:
	var nav: CityNav = CityNav.new()
	nav.region = area
	nav.grid.region = Rect2i(Vector2i.ZERO, area.size)
	nav.grid.cell_size = Vector2.ONE
	nav.grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	nav.grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	nav.grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	nav.grid.jumping_enabled = true
	nav.grid.update()
	return nav


## La rejilla de [param area] con los obstáculos de [param plan].
static func from_plan(plan: CityPlan, area: Rect2i) -> CityNav:
	var nav: CityNav = empty(area)
	var bounds: Rect2 = Rect2(area.position, area.size)
	for building: Dictionary in plan.data.get("edificios", []):
		if String(building["id"]) == VESTIBULE_ID:
			nav.block_disc(VESTIBULE_CENTER, VESTIBULE_RADIUS)
			continue
		for outline: PackedVector2Array in _rings_of(building["huella"]):
			if _rect_of(outline).intersects(bounds):
				nav.block_polygon(outline)
	for pile: Dictionary in plan.data.get("escombros", []):
		if float(pile.get("alto", 0.0)) < RUBBLE_HEIGHT:
			continue
		for outline: PackedVector2Array in _rings_of(pile["forma"]):
			if _rect_of(outline).intersects(bounds):
				nav.block_polygon(outline)
	var sizes: Dictionary = plan.data.get("medidas_vehiculos", {})
	for vehicle: Dictionary in plan.data.get("vehiculos", []):
		var center: Vector2 = Vector2(vehicle["pos"][0], vehicle["pos"][1])
		if not bounds.has_point(center):
			continue
		var size: Array = sizes.get(vehicle["tipo"], [4.5, 1.8])
		nav.block_box(center, Vector2(size[0], size[1]), deg_to_rad(float(vehicle["angulo"])))
	for fence: Dictionary in plan.data.get("vallas", []):
		var points: PackedVector2Array = CityPlan.line(fence["puntos"])
		for index: int in points.size() - 1:
			nav.block_segment(points[index], points[index + 1])
	for bank: Dictionary in plan.data.get("terraplenes", []):
		var half: float = float(bank.get("corona", 10.0)) * 0.5 + float(bank.get("talud", 5.0))
		var points: PackedVector2Array = CityPlan.line(bank["puntos"])
		for index: int in points.size() - 1:
			nav.block_segment(points[index], points[index + 1], half)
	return nav


## Se puede pisar el punto [param point] del plano.
func is_walkable(point: Vector2) -> bool:
	var cell: Vector2i = cell_of(point)
	return grid.is_in_boundsv(cell) and not grid.is_point_solid(cell)


## La casilla de un punto del plano.
func cell_of(point: Vector2) -> Vector2i:
	return Vector2i(
		floori((point.x - region.position.x) / CELL), floori((point.y - region.position.y) / CELL)
	)


## El centro de una casilla, en el plano.
func point_of(cell: Vector2i) -> Vector2:
	return Vector2(region.position) + (Vector2(cell) + Vector2(0.5, 0.5)) * CELL


## El camino de [param from] a [param to] (puntos del plano, sin el de salida),
## alisado: solo quedan las esquinas. Vacío si no hay camino.
func path(from: Vector2, to: Vector2) -> PackedVector2Array:
	var start: Vector2i = cell_of(nearest_walkable(from))
	var goal: Vector2i = cell_of(nearest_walkable(to))
	if not grid.is_in_boundsv(start) or not grid.is_in_boundsv(goal):
		return PackedVector2Array()
	var cells: Array[Vector2i] = grid.get_id_path(start, goal)
	if cells.is_empty():
		return PackedVector2Array()
	var corners: PackedVector2Array = PackedVector2Array()
	var anchor: Vector2 = from
	var index: int = 1
	while index < cells.size():
		# Avanza mientras se vea en línea recta desde la última esquina.
		var far: int = index
		while far + 1 < cells.size() and line_free(anchor, point_of(cells[far + 1])):
			far += 1
		anchor = point_of(cells[far])
		corners.append(anchor)
		index = far + 1
	if not corners.is_empty() and is_walkable(to):
		corners[corners.size() - 1] = to
	return corners


## Se va en línea recta de [param a] a [param b] sin pisar un obstáculo.
func line_free(a: Vector2, b: Vector2) -> bool:
	var steps: int = maxi(1, ceili(a.distance_to(b) / (CELL * 0.5)))
	for step: int in steps + 1:
		if not is_walkable(a.lerp(b, float(step) / steps)):
			return false
	return true


## El punto que se puede pisar más cerca de [param point] (él mismo si se puede).
func nearest_walkable(point: Vector2, search: int = 6) -> Vector2:
	if is_walkable(point):
		return point
	var center: Vector2i = cell_of(point)
	for radius: int in range(1, search + 1):
		for dx: int in range(-radius, radius + 1):
			for dy: int in range(-radius, radius + 1):
				if maxi(absi(dx), absi(dy)) != radius:
					continue
				var cell: Vector2i = center + Vector2i(dx, dy)
				if grid.is_in_boundsv(cell) and not grid.is_point_solid(cell):
					return point_of(cell)
	return point


## Marca como obstáculo lo que queda dentro de un polígono del plano.
func block_polygon(outline: PackedVector2Array) -> void:
	var box: Rect2 = _rect_of(outline)
	var low: Vector2i = cell_of(box.position)
	var high: Vector2i = cell_of(box.end)
	for x: int in range(maxi(low.x, 0), mini(high.x + 1, region.size.x)):
		for y: int in range(maxi(low.y, 0), mini(high.y + 1, region.size.y)):
			if Geometry2D.is_point_in_polygon(point_of(Vector2i(x, y)), outline):
				grid.set_point_solid(Vector2i(x, y), true)


## Marca un rectángulo de [param size] (largo, ancho) centrado en [param center] y
## girado [param angle] (radianes).
func block_box(center: Vector2, size: Vector2, angle: float) -> void:
	var along: Vector2 = Vector2.from_angle(angle) * size.x * 0.5
	var across: Vector2 = Vector2.from_angle(angle + PI * 0.5) * size.y * 0.5
	block_polygon(
		PackedVector2Array(
			[
				center - along - across,
				center + along - across,
				center + along + across,
				center - along + across,
			]
		)
	)


## Marca un segmento (una valla) con [param half_width] a cada lado.
func block_segment(a: Vector2, b: Vector2, half_width: float = 0.5) -> void:
	var direction: Vector2 = (b - a).normalized()
	var side: Vector2 = Vector2(-direction.y, direction.x) * half_width
	block_polygon(PackedVector2Array([a - side, b - side, b + side, a + side]))


## Marca un círculo.
func block_disc(center: Vector2, radius: float) -> void:
	var low: Vector2i = cell_of(center - Vector2.ONE * radius)
	var high: Vector2i = cell_of(center + Vector2.ONE * radius)
	for x: int in range(maxi(low.x, 0), mini(high.x + 1, region.size.x)):
		for y: int in range(maxi(low.y, 0), mini(high.y + 1, region.size.y)):
			if point_of(Vector2i(x, y)).distance_to(center) <= radius:
				grid.set_point_solid(Vector2i(x, y), true)


## Los anillos de una forma del plano, venga como polígono ([[x, y], …]), como lista
## de polígonos o como lista de polígonos con agujeros (de los agujeros no hace caso).
static func _rings_of(shape: Array) -> Array[PackedVector2Array]:
	var rings: Array[PackedVector2Array] = []
	if shape.is_empty():
		return rings
	if shape[0] is Array and not (shape[0] as Array).is_empty() and (shape[0] as Array)[0] is Array:
		for part: Array in shape:
			rings.append_array(_rings_of(part))
		return rings
	rings.append(CityPlan.ring(shape))
	return rings


static func _rect_of(points: PackedVector2Array) -> Rect2:
	if points.is_empty():
		return Rect2()
	var box: Rect2 = Rect2(points[0], Vector2.ZERO)
	for point: Vector2 in points:
		box = box.expand(point)
	return box
