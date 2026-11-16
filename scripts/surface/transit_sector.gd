class_name TransitSector
extends RefCounted
## Lo que CityTransit levanta en un sector, en un hilo propio: las superficies del
## tránsito (enteras donde la rasante es plana, cortadas por la rejilla donde no), el
## relleno de los triángulos hondos, los escombros sobre la calle, la colisión aparte de
## los triángulos del anillo y lo que va en las lindes (con TransitEdges). Solo escribe
## en lo suyo.

## Estados de los triángulos de la rejilla (tools/ciudad/rejilla.py).
const NONE: int = 0
const FULL: int = 1
const BORDER: int = 2
const DEEP: int = 3
const RING: int = 4
## Lo lejos que llegan los sectores del borde del mapa.
const FAR: float = 100000.0
## Lo que oscurece el fondo de un socavón (al fondo de un hoyo llega menos luz).
const PIT_SHADE: float = 0.5

var transit: CityTransit
var plan: CityPlan
var sector: Vector2i
## Lo levantado: {material: MeshBuffer} y la colisión (vértices de tres en tres), en el
## espacio del sector (origen en su centro).
var meshes: Dictionary = {}
var collision: MeshBuffer = MeshBuffer.new()
## Instancias (las traviesas): {modelo: Array de Transform3D en el mundo}.
var instances: Dictionary = {}
var stats: Dictionary = {}
var edge_stats: Dictionary = {}
## Lo que le toca: pares (grupo, primer índice del triángulo), triángulos del relleno,
## aristas, muros, barandillas, ejes, pasos de cebra, pares (vía, tramo de la vía) de las
## vías del tren y del tranvía (CityTransit.tracks), los desvíos, los topes y las grietas.
var triangles: PackedInt32Array = PackedInt32Array()
var fills: PackedInt32Array = PackedInt32Array()
var edges: PackedInt32Array = PackedInt32Array()
var walls: PackedInt32Array = PackedInt32Array()
var rails: PackedInt32Array = PackedInt32Array()
var axes: PackedInt32Array = PackedInt32Array()
var crossings: PackedInt32Array = PackedInt32Array()
var tracks: PackedInt32Array = PackedInt32Array()
var turnouts: PackedInt32Array = PackedInt32Array()
var stops: PackedInt32Array = PackedInt32Array()
var cracks: PackedInt32Array = PackedInt32Array()

var _center: Vector2
var _origin: Vector2i
var _size: int
var _styles: Dictionary = {}
## Los lados por los que se recorta (los del borde del mapa no: lo de fuera es de este).
var _clip_low: Vector2
var _clip_high: Vector2


func _init(city_transit: CityTransit, which: Vector2i) -> void:
	transit = city_transit
	plan = transit.plan
	sector = which
	var rect: Rect2 = plan.sector_rect(sector)
	_center = rect.get_center()
	_size = transit.cells_per_sector
	_origin = sector * _size
	var grid: Vector2i = plan.sector_grid()
	_clip_low = Vector2(
		rect.position.x if sector.x > 0 else -INF, rect.position.y if sector.y > 0 else -INF
	)
	_clip_high = Vector2(
		rect.end.x if sector.x < grid.x - 1 else INF, rect.end.y if sector.y < grid.y - 1 else INF
	)


## Apunta algo que toca a este sector (en la lista [param field]).
func add_item(field: String, value: int) -> void:
	var list: PackedInt32Array = get(field)
	list.append(value)
	set(field, list)


## Levanta el sector (en un hilo del WorkerThreadPool).
func build() -> void:
	stats = {"piezas": 0, "rellenos": 0, "escombros": 0}
	for n: int in range(0, triangles.size(), 2):
		_surface(triangles[n], triangles[n + 1])
	_build_fill()
	_build_rubble_and_ring()
	var builder: TransitEdges = TransitEdges.new(transit, self)
	builder.build()
	edge_stats = builder.stats
	var rails: TransitRails = TransitRails.new(transit, self, builder)
	rails.build()
	edge_stats.merge(rails.stats)


## Los límites por los que se recorta lo del sector (en el borde del mapa, muy lejos: un
## rectángulo con lados infinitos no se puede restar).
func clip_bounds() -> Rect2:
	var far: Vector2 = Vector2.ONE * FAR
	var low: Vector2 = _clip_low.clamp(-far, far)
	return Rect2(low, _clip_high.clamp(-far, far) - low)


## ¿Es de este sector el punto (lo de fuera del mapa es de los sectores del borde)?
func owns(point: Vector2) -> bool:
	return plan.sector_of(point) == sector


## Un punto del plano a la altura [param height], en el espacio del sector.
func local(point: Vector2, height: float) -> Vector3:
	return Vector3(point.x - _center.x, height, _center.y - point.y)


## La malla de un material (se crea si no está).
func buffer(material: String) -> MeshBuffer:
	if not meshes.has(material):
		meshes[material] = MeshBuffer.new()
	return meshes[material]


## Añade una instancia de un modelo (en el mundo).
func add_instance(model: String, placed: Transform3D) -> void:
	if not instances.has(model):
		instances[model] = []
	instances[model].append(placed)


## Añade caras de colisión (un polígono convexo, en el espacio del sector).
func add_collision(points: PackedVector3Array) -> void:
	for i: int in range(1, points.size() - 1):
		collision.vertices.append(points[0])
		collision.vertices.append(points[i])
		collision.vertices.append(points[i + 1])


func _surface(index: int, start: int) -> void:
	if transit.mesh_normals.has(index):
		_emit_mesh(index, start)
		return
	var data: Dictionary = transit.groups[index]
	var points: Array = data["puntos"]
	var corners: Array = data["triangulos"]
	var poly: PackedVector2Array = PackedVector2Array()
	for n: int in 3:
		var v: int = int(corners[start + n]) * 2
		poly.append(Vector2(points[v], points[v + 1]))
	var triangle: PackedVector2Array = poly
	if GridClip.area(poly) < 0.0:
		poly.reverse()
	poly = _clip_to_sector(poly)
	if poly.size() < 3 or GridClip.area(poly) < 1e-6:
		return
	var style: Array = _style(index)
	# Donde la rasante es plana bajo el triángulo (o la regla es un plano) basta con el
	# trozo entero; si no, pieza a pieza siguiendo la rejilla.
	var flat: String = data["planos"]
	if flat.unicode_at(start / 3) == 49:
		_emit_polygon(index, poly, style)
		return
	# Las aristas que comparte con un triángulo entero van rectas (casan exactas con él).
	var straight: Array = []
	var mask: int = String(data["rectas"]).unicode_at(start / 3) - 48
	if mask > 0:
		var heights: PackedFloat32Array = PackedFloat32Array()
		for p: Vector2 in triangle:
			heights.append(transit.surface_z(index, p))
		straight = [triangle, heights, mask]
	var pieces: Array = GridClip.split(poly, CityTransit.STEP)
	for piece: Array in pieces:
		_emit_piece(index, piece, style, straight)
	stats["piezas"] += pieces.size()


func _clip_to_sector(poly: PackedVector2Array) -> PackedVector2Array:
	if _clip_low.x > -INF:
		poly = GridClip.clip_x(poly, _clip_low.x, true)
	if poly.size() >= 3 and _clip_high.x < INF:
		poly = GridClip.clip_x(poly, _clip_high.x, false)
	if poly.size() >= 3 and _clip_low.y > -INF:
		poly = GridClip.clip_y(poly, _clip_low.y, true)
	if poly.size() >= 3 and _clip_high.y < INF:
		poly = GridClip.clip_y(poly, _clip_high.y, false)
	return poly


## Material, color y ejes de la textura de un grupo.
func _style(index: int) -> Array:
	if _styles.has(index):
		return _styles[index]
	var data: Dictionary = transit.groups[index]
	var kind: String = data["clase"]
	var material: String = CityTransit.SURFACE_MATERIALS.get(kind, "losas")
	var tint: Color = CityTransit.SURFACE_COLORS.get(kind, Color.WHITE)
	# Cada grupo, un tono algo distinto (losas de otra partida, asfalto parcheado).
	var shade: float = 0.94 + 0.12 * CityPlan.chance("transito/%d" % index)
	tint = Color(tint.r * shade, tint.g * shade, tint.b * shade, tint.a)
	var angle: float = deg_to_rad(float(data["angulo"]))
	var tile: float = CityTransit.TILE.get(material, 2.0)
	var uv_axes: PackedVector2Array = PackedVector2Array(
		[Vector2(cos(angle), sin(angle)) / tile, Vector2(-sin(angle), cos(angle)) / tile]
	)
	_styles[index] = [material, tint, uv_axes]
	return _styles[index]


## Un trozo entero (un plano, o la rasante cuando es plana).
func _emit_polygon(index: int, poly: PackedVector2Array, style: Array) -> void:
	var uv_axes: PackedVector2Array = style[2]
	var points: PackedVector3Array = PackedVector3Array()
	var uvs: PackedVector2Array = PackedVector2Array()
	for p: Vector2 in poly:
		points.append(local(p, transit.surface_z(index, p)))
		uvs.append(Vector2(p.dot(uv_axes[0]), p.dot(uv_axes[1])))
	var normals: PackedVector3Array = PackedVector3Array()
	if transit.follows_base[index] == 1:
		# Sobre la rasante, las normales suaves de la rejilla (las mismas que a los vecinos).
		for p: Vector2 in poly:
			normals.append(transit.base_normal(p))
	else:
		var normal: Vector3 = transit.rule_normal(index, poly[0])
		normals.resize(points.size())
		normals.fill(normal)
	buffer(style[0]).add_polygon(points, normals, style[1], uvs)
	add_collision(points)


## Un triángulo de una malla propia (un socavón), con la altura, la normal suave y la
## textura de sus vértices; lo que cae fuera del sector se recorta. Cuanto más hondo, más
## oscuro ([constant PIT_SHADE]).
func _emit_mesh(index: int, start: int) -> void:
	var data: Dictionary = transit.groups[index]
	var points: Array = data["puntos"]
	var corners: Array = data["triangulos"]
	var heights: Array = data["z"]
	var texture: Array = data["uv"]
	var mesh_normals: PackedVector3Array = transit.mesh_normals[index]
	var corner: PackedVector2Array = PackedVector2Array()
	var ids: PackedInt32Array = PackedInt32Array()
	for n: int in 3:
		var v: int = int(corners[start + n])
		ids.append(v)
		corner.append(Vector2(points[v * 2], points[v * 2 + 1]))
	var poly: PackedVector2Array = corner.duplicate()
	if GridClip.area(poly) < 0.0:
		poly.reverse()
	poly = _clip_to_sector(poly)
	if poly.size() < 3 or GridClip.area(poly) < 1e-6:
		return
	var style: Array = _style(index)
	var tile: float = CityTransit.TILE.get(style[0], 4.0)
	var depth: Vector2 = transit.mesh_range[index]
	var tint: Color = style[1]
	var out_points: PackedVector3Array = PackedVector3Array()
	var out_normals: PackedVector3Array = PackedVector3Array()
	var uvs: PackedVector2Array = PackedVector2Array()
	var colors: PackedColorArray = PackedColorArray()
	for p: Vector2 in poly:
		var w: Vector3 = CityTransit.barycentric(p, corner[0], corner[1], corner[2])
		var z: float = 0.0
		var normal: Vector3 = Vector3.ZERO
		var uv: Vector2 = Vector2.ZERO
		for n: int in 3:
			var v: int = ids[n]
			z += float(heights[v]) * w[n]
			normal += mesh_normals[v] * w[n]
			uv += Vector2(texture[v * 2], texture[v * 2 + 1]) * w[n]
		out_points.append(local(p, z))
		out_normals.append(normal.normalized())
		uvs.append(uv / tile)
		var f: float = clampf((depth.y - z) / maxf(depth.y - depth.x, 0.5), 0.0, 1.0)
		var shade: float = 1.0 - PIT_SHADE * pow(f, 0.7)
		colors.append(Color(tint.r * shade, tint.g * shade, tint.b * shade, tint.a))
	buffer(style[0]).add_polygon(out_points, out_normals, tint, uvs, colors)
	add_collision(out_points)
	stats["piezas"] += 1


## Una pieza dentro de un triángulo de la rejilla, siguiendo la rasante con sus normales
## suaves (las de las esquinas, mezcladas como en la malla del terreno).
func _emit_piece(index: int, piece: Array, style: Array, straight: Array) -> void:
	var cell: Vector2i = piece[0]
	var k: int = piece[1]
	var poly: PackedVector2Array = piece[2]
	var uv_axes: PackedVector2Array = style[2]
	var count: int = poly.size()
	var points: PackedVector3Array = PackedVector3Array()
	var normals: PackedVector3Array = PackedVector3Array()
	var uvs: PackedVector2Array = PackedVector2Array()
	points.resize(count)
	normals.resize(count)
	uvs.resize(count)
	var inside: bool = transit.cell_inside(cell)
	var base: Vector3 = Vector3.ZERO
	var corner_normals: Array[Vector3] = [Vector3.UP, Vector3.UP, Vector3.UP]
	if inside:
		var corners: PackedInt32Array = transit.triangle_vertices(cell, k)
		for n: int in 3:
			base[n] = transit.vertex_base[corners[n]]
			corner_normals[n] = transit.vertex_normal(transit.vertex_base, corners[n])
	var level: float = transit.group_level[index]
	for n: int in count:
		var p: Vector2 = poly[n]
		if inside:
			var w: Vector3 = CityTransit.weights(p, cell, k)
			points[n] = local(p, _straight_z(p, straight, base.dot(w) + level))
			normals[n] = (
				(corner_normals[0] * w.x + corner_normals[1] * w.y + corner_normals[2] * w.z)
				. normalized()
			)
		else:
			points[n] = local(p, transit.surface_z(index, p))
			normals[n] = Vector3.UP
		uvs[n] = Vector2(p.dot(uv_axes[0]), p.dot(uv_axes[1]))
	buffer(style[0]).add_polygon(points, normals, style[1], uvs)
	add_collision(points)


## La altura de un punto que cae en una arista recta del triángulo (la que comparte con un
## triángulo entero): la de la recta entre sus extremos. Si no, [param z].
static func _straight_z(point: Vector2, straight: Array, z: float) -> float:
	if straight.is_empty():
		return z
	var triangle: PackedVector2Array = straight[0]
	var heights: PackedFloat32Array = straight[1]
	var mask: int = straight[2]
	for e: int in 3:
		if not mask & (1 << e):
			continue
		var a: Vector2 = triangle[e]
		var b: Vector2 = triangle[(e + 1) % 3]
		var along: Vector2 = b - a
		var f: float = clampf((point - a).dot(along) / along.length_squared(), 0.0, 1.0)
		if point.distance_squared_to(a + along * f) < 1e-8:
			return lerpf(heights[e], heights[(e + 1) % 3], f)
	return z


## El relleno de los triángulos hondos: lo que no es tránsito, a la altura del terreno.
func _build_fill() -> void:
	var fill: Dictionary = plan.transit["relleno"]
	var ids: Array = fill["triangulos"]
	var points: Array = fill["puntos"]
	for n: int in fills:
		var id: int = ids[n]
		var cell: Vector2i = Vector2i((id / 2) % transit.cells.x, (id / 2) / transit.cells.x)
		var poly: PackedVector2Array = PackedVector2Array()
		for m: int in 3:
			poly.append(Vector2(points[n * 6 + m * 2], points[n * 6 + m * 2 + 1]))
		_emit_ground(cell, id % 2, poly, false)
		stats["rellenos"] += 1


## Los escombros sobre el tránsito (el terreno rebajado de los triángulos ocultos donde hay
## escombro: asoma donde el montón es alto) y la colisión de los triángulos del anillo.
func _build_rubble_and_ring() -> void:
	var grid: PackedByteArray = plan.transit_grid
	for j: int in range(_origin.y, mini(_origin.y + _size, transit.cells.y)):
		for i: int in range(_origin.x, mini(_origin.x + _size, transit.cells.x)):
			var code: int = grid[j * transit.cells.x + i]
			if code == 0:
				continue
			for k: int in 2:
				var state: int = (code >> (3 * k)) & 7
				var cell: Vector2i = Vector2i(i, j)
				if state & RING:
					_ring_collision(cell, k)
				state &= 3
				if state != FULL and state != DEEP:
					continue
				var rubble: float = 0.0
				for v: int in transit.triangle_vertices(cell, k):
					rubble = maxf(rubble, transit.vertex_heights[v] - transit.vertex_base[v])
				if rubble >= CityTransit.RUBBLE_MIN:
					_emit_ground(cell, k, CityTransit.triangle_polygon(cell, k), true)
					stats["escombros"] += 1


func _ring_collision(cell: Vector2i, k: int) -> void:
	var points: PackedVector3Array = PackedVector3Array()
	for p: Vector2 in CityTransit.triangle_polygon(cell, k):
		points.append(local(p, transit.terrain_z(p)))
	add_collision(points)


## Un trozo de terreno dentro de un triángulo de la rejilla, con el material del suelo:
## a la altura del relieve (el relleno) o rebajada (los escombros sobre el tránsito).
func _emit_ground(cell: Vector2i, k: int, poly: PackedVector2Array, carved: bool) -> void:
	var count: int = poly.size()
	var points: PackedVector3Array = PackedVector3Array()
	var normals: PackedVector3Array = PackedVector3Array()
	var uvs: PackedVector2Array = PackedVector2Array()
	points.resize(count)
	normals.resize(count)
	uvs.resize(count)
	var corners: PackedInt32Array = transit.triangle_vertices(cell, k)
	var heights: Vector3 = Vector3.ZERO
	var corner_normals: Array[Vector3] = [Vector3.UP, Vector3.UP, Vector3.UP]
	for n: int in 3:
		heights[n] = transit.vertex_heights[corners[n]]
		if carved:
			heights[n] -= transit.carve[corners[n]]
		corner_normals[n] = transit.vertex_normal(transit.vertex_heights, corners[n])
	for n: int in count:
		var p: Vector2 = poly[n]
		var w: Vector3 = CityTransit.weights(p, cell, k)
		points[n] = local(p, heights.dot(w))
		normals[n] = (
			(corner_normals[0] * w.x + corner_normals[1] * w.y + corner_normals[2] * w.z)
			. normalized()
		)
		uvs[n] = Vector2(0.5, 0.95)
	buffer("suelo").add_polygon(points, normals, CityTransit.GROUND_COLOR, uvs)
	if not carved:
		add_collision(points)
