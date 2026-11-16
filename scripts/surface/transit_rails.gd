class_name TransitRails
extends RefCounted
## Las vías del tren y del tranvía de un sector (CityTransit.tracks, de transito.json). En
## los tramos abiertos, el balasto, las traviesas de hormigón (como instancias) y los
## carriles, a la altura de la rasante de la vía; en los pasos a nivel y en el tranvía, los
## carriles a ras de lo que se pisa, con su garganta.
##
## Cada TransitSector levanta los segmentos de cada vía que CityTransit le reparte: los
## recorta por sus lindes (el corte sale igual desde los dos lados) y cuenta la textura y
## las traviesas desde el principio de la vía, así que los sectores empalman sin costura.
##
## Medidas soviéticas: ancho de vía de 1520 mm (el tranvía, 1524), carril de 15 cm sobre
## traviesas de hormigón de 2,7 m cada 0,55 m y 30 cm de balasto.

## Del plano de formación (la rasante de la vía) a lo alto del balasto y de las traviesas
## en el asiento del carril (lo alto del carril lo da transito.json).
const BALLAST_TOP: float = 0.30
const SLEEPER_TOP: float = 0.42
## Media anchura del balasto arriba y al pie; el pie se hunde bajo la rasante.
const BALLAST_HALF: Vector2 = Vector2(1.7, 2.4)
const BALLAST_FOOT: float = 0.15
## Del eje de la vía al de cada carril: medio ancho de vía más media cabeza (el tren y el
## tranvía).
const RAIL_OFFSET: float = 0.7975
const TRAM_OFFSET: float = 0.7995
## Corte del carril desde su eje y sobre la traviesa (patín, alma y cabeza, en sentido
## antihorario), para [constant RAIL_HEIGHT] de alto.
const RAIL_PROFILE: Array[Vector2] = [
	Vector2(0.075, 0.0),
	Vector2(0.075, 0.012),
	Vector2(0.0085, 0.03),
	Vector2(0.0085, 0.11),
	Vector2(0.0375, 0.12),
	Vector2(0.0375, 0.15),
	Vector2(-0.0375, 0.15),
	Vector2(-0.0375, 0.12),
	Vector2(-0.0085, 0.11),
	Vector2(-0.0085, 0.03),
	Vector2(-0.075, 0.012),
	Vector2(-0.075, 0.0),
]
const RAIL_HEIGHT: float = 0.15
## Cada cuánto va una traviesa (el modelo "traviesa" tiene el origen en lo alto del
## asiento del carril, donde apoya el patín).
const SLEEPER_STEP: float = 0.55
## El carril a ras: lo que asoma sobre la calle, el ancho de la cabeza y el de la garganta.
const FLUSH_LIFT: float = 0.006
const HEAD_WIDTH: float = 0.075
const GROOVE_WIDTH: float = 0.045
const BALLAST_COLOR: Color = Color(0.46, 0.44, 0.42, 0.55)
const STEEL_COLOR: Color = Color(0.3, 0.29, 0.28, 0.15)
const GROOVE_COLOR: Color = Color(0.12, 0.12, 0.12, 0.3)
## El tope: la caja que choca (desde su origen, a lo alto del carril; hacia delante, sobre
## los últimos metros de la vía): media anchura, de dónde a dónde a lo largo y en alto.
const STOP_HALF_WIDTH: float = 1.45
const STOP_ALONG: Vector2 = Vector2(-0.2, 3.0)
const STOP_HEIGHT: Vector2 = Vector2(-0.57, 1.35)

var transit: CityTransit
var out: TransitSector
var edges: TransitEdges
var stats: Dictionary = {}
var _rail_top: float = 0.57


func _init(city_transit: CityTransit, sector: TransitSector, edge_builder: TransitEdges) -> void:
	transit = city_transit
	out = sector
	edges = edge_builder
	_rail_top = float(transit.plan.transit.get("ferrocarril", {}).get("carril", 0.57))


func build() -> void:
	stats = {"traviesas": 0, "via_m": 0.0, "a_ras_m": 0.0, "desvios": 0, "topes": 0}
	_build_turnouts()
	_build_stops()
	var pairs: PackedInt32Array = out.tracks
	var n: int = 0
	while n < pairs.size():
		var index: int = pairs[n]
		var first: int = pairs[n + 1]
		var last: int = first
		n += 2
		while n < pairs.size() and pairs[n] == index and pairs[n + 1] == last + 1:
			last += 1
			n += 2
		_build_run(transit.tracks[index], first, last)


## Los segmentos seguidos [param first]..[param last] de un tramo.
func _build_run(track: Dictionary, first: int, last: int) -> void:
	var points: PackedVector2Array = track["puntos"]
	var line: PackedVector2Array = points.slice(first, last + 2)
	var start: float = (track["largo"] as PackedFloat32Array)[first]
	if bool(track["abierta"]):
		var heights: PackedFloat32Array = (track["z"] as PackedFloat32Array).slice(first, last + 2)
		var loose: Array = [
			bool(track["puntas"][0]) and first == 0,
			bool(track["puntas"][1]) and last == points.size() - 2,
		]
		_open_track(line, heights, start, loose, track)
	else:
		var rails: Array = track["carriles"]
		for side: int in 2:
			var rail: PackedVector2Array = rails[side]
			_flush_rail(rail.slice(first, last + 2), start, side == 0)


## Vía sobre balasto: el balasto, los dos carriles (sin los trozos que ponen las agujas y
## el corazón de un desvío) y las traviesas (sin las de los desvíos, que son de madera).
func _open_track(
	line: PackedVector2Array,
	heights: PackedFloat32Array,
	start: float,
	loose: Array,
	track: Dictionary
) -> void:
	for part: Array in _clip(line, heights, start):
		var full: PackedVector2Array = part[0]
		var full_z: PackedFloat32Array = part[1]
		var s0: float = part[2]
		var lengths: PackedFloat32Array = TransitEdges.arc_lengths(full)
		var kept: PackedInt32Array = TransitEdges.simplify(full, full_z, full_z)
		var points: PackedVector2Array = PackedVector2Array()
		var z: PackedFloat32Array = PackedFloat32Array()
		for k: int in kept:
			points.append(full[k])
			z.append(full_z[k])
		var sides: Array = [points, TransitEdges.line_normals(points), z, z, false]
		var ballast: Array = []
		for n: int in points.size():
			var f: float = z[n]
			(
				ballast
				. append(
					[
						Vector2(BALLAST_HALF.y, f - BALLAST_FOOT),
						Vector2(BALLAST_HALF.x, f + BALLAST_TOP),
						Vector2(-BALLAST_HALF.x, f + BALLAST_TOP),
						Vector2(-BALLAST_HALF.y, f - BALLAST_FOOT),
					]
				)
			)
		edges.extrude(sides, ballast, "balasto", BALLAST_COLOR, true, s0)
		for side: int in 2:
			var length: float = lengths[lengths.size() - 1]
			for stretch: Vector2 in _rail_ranges(track.get("huecos", []), side, s0, length):
				var piece: Array = _slice(full, full_z, lengths, stretch.x, stretch.y)
				_rail(
					piece[0], piece[1], RAIL_OFFSET if side == 0 else -RAIL_OFFSET, s0 + stretch.x
				)
		# La punta suelta de una vía (el final de un apartadero, el borde del cráter).
		if loose[0] and full[0] == line[0]:
			edges.cap(sides, ballast, 0, "balasto", BALLAST_COLOR)
		if loose[1] and full[full.size() - 1] == line[line.size() - 1]:
			edges.cap(sides, ballast, points.size() - 1, "balasto", BALLAST_COLOR)
		_sleepers(full, full_z, s0, track.get("sin_traviesas", []))
		stats["via_m"] += lengths[lengths.size() - 1]


## Un carril a [param offset] del eje de una polilínea (con la rasante de cada punto),
## sin los puntos que no hacen falta.
func _rail(
	line: PackedVector2Array, formation: PackedFloat32Array, offset: float, start: float
) -> void:
	if line.size() < 2:
		return
	var kept: PackedInt32Array = TransitEdges.simplify(line, formation, formation)
	var points: PackedVector2Array = PackedVector2Array()
	var z: PackedFloat32Array = PackedFloat32Array()
	for k: int in kept:
		points.append(line[k])
		z.append(formation[k])
	var scale: float = (_rail_top - SLEEPER_TOP) / RAIL_HEIGHT
	var profiles: Array = []
	for f: float in z:
		var profile: Array = []
		for corner: Vector2 in RAIL_PROFILE:
			profile.append(Vector2(offset + corner.x, f + SLEEPER_TOP + corner.y * scale))
		profiles.append(profile)
	var sides: Array = [points, TransitEdges.line_normals(points), z, z, false]
	edges.extrude(sides, profiles, "metal", STEEL_COLOR, false, start)


## Lo que se dibuja de un carril en un trozo de [param length] metros que empieza a
## [param s0] del principio del tramo: todo menos sus huecos.
static func _rail_ranges(gaps: Array, side: int, s0: float, length: float) -> Array[Vector2]:
	var cuts: Array[Vector2] = []
	for gap: Array in gaps:
		if int(gap[0]) == side and float(gap[2]) > s0 and float(gap[1]) < s0 + length:
			cuts.append(Vector2(float(gap[1]) - s0, float(gap[2]) - s0))
	cuts.sort()
	var ranges: Array[Vector2] = []
	var from: float = 0.0
	for cut: Vector2 in cuts:
		if cut.x > from + 0.01:
			ranges.append(Vector2(from, cut.x))
		from = maxf(from, cut.y)
	if length > from + 0.01:
		ranges.append(Vector2(from, length))
	return ranges


## El trozo de una polilínea (con sus alturas) entre dos distancias desde su principio.
static func _slice(
	points: PackedVector2Array,
	z: PackedFloat32Array,
	lengths: PackedFloat32Array,
	a: float,
	b: float
) -> Array:
	var line: PackedVector2Array = PackedVector2Array([TransitEdges.point_at(points, lengths, a)])
	var heights: PackedFloat32Array = PackedFloat32Array([TransitEdges.value_at(lengths, z, a)])
	for k: int in points.size():
		if lengths[k] > a + 1e-4 and lengths[k] < b - 1e-4:
			line.append(points[k])
			heights.append(z[k])
	line.append(TransitEdges.point_at(points, lengths, b))
	heights.append(TransitEdges.value_at(lengths, z, b))
	return [line, heights]


## Las traviesas de un trozo: cada [constant SLEEPER_STEP] metros desde el principio de la
## vía ([param s0] es lo que mide la vía hasta el primer punto del trozo), salvo donde van
## las de madera de un desvío ([param bare]: tramos del principio de la vía).
func _sleepers(points: PackedVector2Array, z: PackedFloat32Array, s0: float, bare: Array) -> void:
	var lengths: PackedFloat32Array = TransitEdges.arc_lengths(points)
	var total: float = lengths[lengths.size() - 1]
	var s: float = (ceilf(s0 / SLEEPER_STEP - 0.5) + 0.5) * SLEEPER_STEP - s0
	var k: int = 1
	while s <= total:
		while k < lengths.size() - 1 and lengths[k] < s:
			k += 1
		var span: float = maxf(lengths[k] - lengths[k - 1], 1e-6)
		var f: float = clampf((s - lengths[k - 1]) / span, 0.0, 1.0)
		var p: Vector2 = points[k - 1].lerp(points[k], f)
		if out.owns(p) and not _inside(bare, s0 + s):
			var height: float = lerpf(z[k - 1], z[k], f)
			var along: Vector3 = Vector3(
				points[k].x - points[k - 1].x, z[k] - z[k - 1], points[k - 1].y - points[k].y
			)
			var center: Vector3 = CityPlan.to_world(p, height + SLEEPER_TOP)
			var basis: Basis = Basis.looking_at(along.normalized(), Vector3.UP)
			out.add_instance("traviesa", Transform3D(basis, center))
			stats["traviesas"] += 1
		s += SLEEPER_STEP


static func _inside(ranges: Array, s: float) -> bool:
	for stretch: Array in ranges:
		if s >= float(stretch[0]) and s <= float(stretch[1]):
			return true
	return false


## Los desvíos que tocan al sector: las agujas y los contracarriles (carriles extruidos,
## cada sector lo suyo) y, como instancias, el corazón, las traviesas de madera y la
## palanca (del sector en el que caen).
func _build_turnouts() -> void:
	var turnouts: Array = transit.plan.transit.get("ferrocarril", {}).get("desvios", [])
	for index: int in out.turnouts:
		var turnout: Dictionary = turnouts[index]
		for blade: Array in turnout["agujas"]:
			_rail_along(blade)
		for check: Array in turnout["contracarriles"]:
			_rail_along(check)
		var heading: float = deg_to_rad(float(turnout["rumbo"]))
		var frog: Dictionary = turnout["corazon"]
		var model: String = "corazon_" + String(turnout["marca"]).replace("/", "_")
		if _place(model, frog["pos"], float(frog["z"]), deg_to_rad(float(frog["rumbo"])), 1.0):
			stats["desvios"] += 1
		for timber: Array in turnout["maderas"]:
			_place("traviesa_madera", timber, float(timber[2]), heading, float(timber[3]))
		_turnout_ballast(turnout["maderas"])
		var stand: Dictionary = turnout["palanca"]
		_place("palanca_aguja", stand["pos"], float(stand["z"]), heading, 1.0)


## El balasto ensanchado bajo las traviesas largas de un desvío: a lo largo de sus
## centros, tan ancho como cada una (un centímetro por debajo del de las vías, para no
## pisarse con él donde coinciden).
func _turnout_ballast(timbers: Array) -> void:
	var line: PackedVector2Array = PackedVector2Array()
	var z: PackedFloat32Array = PackedFloat32Array()
	var profiles: Array = []
	for timber: Array in timbers:
		line.append(Vector2(timber[0], timber[1]))
		var formation: float = float(timber[2]) - SLEEPER_TOP
		z.append(formation)
		var half: float = float(timber[3]) * 0.5 + 0.25
		var top: float = formation + BALLAST_TOP - 0.01
		(
			profiles
			. append(
				[
					Vector2(half + 0.7, formation - BALLAST_FOOT),
					Vector2(half, top),
					Vector2(-half, top),
					Vector2(-half - 0.7, formation - BALLAST_FOOT),
				]
			)
		)
	var sides: Array = [line, TransitEdges.line_normals(line), z, z, false]
	edges.extrude(sides, profiles, "balasto", BALLAST_COLOR, true)


## Los topes del sector: el modelo y una caja de colisión.
func _build_stops() -> void:
	var stops: Array = transit.plan.transit.get("ferrocarril", {}).get("topes", [])
	for index: int in out.stops:
		var stop: Dictionary = stops[index]
		var heading: float = deg_to_rad(float(stop["rumbo"]))
		if not _place("tope", stop["pos"], float(stop["z"]), heading, 1.0):
			continue
		stats["topes"] += 1
		var base: Vector2 = Vector2(stop["pos"][0], stop["pos"][1])
		var forward: Vector2 = Vector2(cos(heading), sin(heading))
		var right: Vector2 = Vector2(forward.y, -forward.x)
		var corners: Array[Vector3] = []
		for along: float in [STOP_ALONG.x, STOP_ALONG.y]:
			for across: float in [-STOP_HALF_WIDTH, STOP_HALF_WIDTH]:
				for up: float in [STOP_HEIGHT.x, STOP_HEIGHT.y]:
					var p: Vector2 = base + forward * along + right * across
					corners.append(out.local(p, float(stop["z"]) + up))
		for face: Array in [
			[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]
		]:
			var polygon: PackedVector3Array = PackedVector3Array()
			for corner: int in face:
				polygon.append(corners[corner])
			out.add_collision(polygon)


## Una instancia de un modelo de la vía en el plano ([param pos]: x, y), a la altura
## [param z], mirando a [param heading] y estirada [param stretch] de lado a lado. Solo si
## cae en el sector; devuelve si se puso.
func _place(model: String, pos: Array, z: float, heading: float, stretch: float) -> bool:
	var point: Vector2 = Vector2(pos[0], pos[1])
	if not out.owns(point):
		return false
	var forward: Vector3 = Vector3(cos(heading), 0.0, -sin(heading))
	var basis: Basis = (
		Basis.looking_at(forward, Vector3.UP) * Basis.from_scale(Vector3(stretch, 1.0, 1.0))
	)
	out.add_instance(model, Transform3D(basis, CityPlan.to_world(point, z)))
	return true


## Un carril a lo largo de puntos [x, y, lo alto del carril] (y, en las agujas, lo ancho
## de su perfil en la punta: se afilan).
func _rail_along(points: Array) -> void:
	var line: PackedVector2Array = PackedVector2Array()
	for p: Array in points:
		line.append(Vector2(p[0], p[1]))
	var profiles: Array = []
	var z: PackedFloat32Array = PackedFloat32Array()
	for p: Array in points:
		var scale: float = float(p[3]) if p.size() > 3 else 1.0
		var top: float = float(p[2])
		z.append(top)
		var profile: Array = []
		for corner: Vector2 in RAIL_PROFILE:
			profile.append(Vector2(corner.x * scale, top - RAIL_HEIGHT + corner.y))
		profiles.append(profile)
	var sides: Array = [line, TransitEdges.line_normals(line), z, z, false]
	edges.extrude(sides, profiles, "metal", STEEL_COLOR, false)


## Un carril a ras de lo que se pisa (pasos a nivel y tranvía): su cabeza y la garganta
## del lado de dentro de la vía, partidos por la rejilla para seguir la superficie.
## [param left] dice si es el carril de la izquierda (la vía queda a su derecha).
func _flush_rail(rail: PackedVector2Array, start: float, left: bool) -> void:
	var fine: PackedVector2Array = GridClip.subdivide(rail, CityTransit.STEP)
	for part: Array in _clip(fine, PackedFloat32Array(), start):
		var points: PackedVector2Array = part[0]
		var heights: PackedFloat32Array = PackedFloat32Array()
		for p: Vector2 in points:
			var z: float = transit.surface_at(p)
			heights.append((transit.terrain_z(p) if is_nan(z) else z) + FLUSH_LIFT)
		var sides: Array = [points, TransitEdges.line_normals(points), heights, heights, false]
		var head: Array = []
		var groove: Array = []
		# La garganta, del lado de la vía: a la derecha del carril de la izquierda.
		var near: float = HEAD_WIDTH * (-0.5 if left else 0.5)
		var far: float = near + (-GROOVE_WIDTH if left else GROOVE_WIDTH)
		for z: float in heights:
			head.append([Vector2(HEAD_WIDTH * 0.5, z), Vector2(-HEAD_WIDTH * 0.5, z)])
			groove.append(
				[Vector2(maxf(near, far), z - 0.001), Vector2(minf(near, far), z - 0.001)]
			)
		edges.extrude(sides, head, "metal", STEEL_COLOR, false, part[2])
		edges.extrude(sides, groove, "metal", GROOVE_COLOR, false, part[2])
		stats["a_ras_m"] += TransitEdges.arc_lengths(points)[points.size() - 1] * 0.5


## Los trozos de la polilínea (con sus alturas, si las trae) que caen en el sector: cada uno
## como [puntos, alturas, lo que mide la vía hasta su primer punto].
func _clip(line: PackedVector2Array, heights: PackedFloat32Array, start: float) -> Array:
	var bounds: Rect2 = out.clip_bounds()
	var parts: Array = []
	var points: PackedVector2Array = PackedVector2Array()
	var z: PackedFloat32Array = PackedFloat32Array()
	var part_start: float = start
	var along: float = start
	var has_z: bool = not heights.is_empty()
	for k: int in line.size() - 1:
		var p: Vector2 = line[k]
		var q: Vector2 = line[k + 1]
		var length: float = p.distance_to(q)
		var span: Vector2 = _span(p, q, bounds)
		if span.x < span.y:
			var a: Vector2 = p if span.x <= 0.0 else p + (q - p) * span.x
			var b: Vector2 = q if span.y >= 1.0 else p + (q - p) * span.y
			if points.is_empty() or points[points.size() - 1] != a:
				if points.size() >= 2:
					parts.append([points, z, part_start])
				points = PackedVector2Array([a])
				z = PackedFloat32Array()
				if has_z:
					z.append(lerpf(heights[k], heights[k + 1], maxf(span.x, 0.0)))
				part_start = along + length * maxf(span.x, 0.0)
			points.append(b)
			if has_z:
				z.append(lerpf(heights[k], heights[k + 1], minf(span.y, 1.0)))
		along += length
	if points.size() >= 2:
		parts.append([points, z, part_start])
	return parts


## La parte del segmento de [param p] a [param q] dentro del rectángulo, en fracciones del
## segmento (vacía si la primera no es menor que la segunda).
static func _span(p: Vector2, q: Vector2, bounds: Rect2) -> Vector2:
	var t0: float = 0.0
	var t1: float = 1.0
	var d: Vector2 = q - p
	for axis: int in 2:
		var low: float = bounds.position[axis]
		var high: float = bounds.end[axis]
		if absf(d[axis]) < 1e-12:
			if p[axis] < low or p[axis] > high:
				return Vector2(1.0, 0.0)
			continue
		var ta: float = (low - p[axis]) / d[axis]
		var tb: float = (high - p[axis]) / d[axis]
		t0 = maxf(t0, minf(ta, tb))
		t1 = minf(t1, maxf(ta, tb))
	return Vector2(t0, t1)
