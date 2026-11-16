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
## La traviesa: largo, ancho abajo y arriba, alto en el asiento del carril y en el centro
## (rebajado entre los dos asientos); y cada cuánto va una.
const SLEEPER_LENGTH: float = 2.7
const SLEEPER_WIDTH: Vector2 = Vector2(0.28, 0.18)
const SLEEPER_HEIGHT: Vector2 = Vector2(0.19, 0.15)
const SLEEPER_STEP: float = 0.55
## El carril a ras: lo que asoma sobre la calle, el ancho de la cabeza y el de la garganta.
const FLUSH_LIFT: float = 0.006
const HEAD_WIDTH: float = 0.075
const GROOVE_WIDTH: float = 0.045
const BALLAST_COLOR: Color = Color(0.46, 0.44, 0.42, 0.55)
const STEEL_COLOR: Color = Color(0.3, 0.29, 0.28, 0.15)
const GROOVE_COLOR: Color = Color(0.12, 0.12, 0.12, 0.3)
const SLEEPER_COLOR: Color = Color(0.62, 0.6, 0.57)

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


## La traviesa (con el origen en lo alto del asiento del carril y lo largo en x): una barra
## de sección trapecial, más baja en el centro.
static func sleeper_mesh() -> ArrayMesh:
	var mesh: MeshBuffer = MeshBuffer.new()
	var half: float = SLEEPER_LENGTH * 0.5
	var xs: PackedFloat32Array = PackedFloat32Array([-half, -0.55, -0.35, 0.35, 0.55, half])
	var bottom: float = -SLEEPER_HEIGHT.x
	var sections: Array = []
	for n: int in xs.size():
		var x: float = xs[n]
		var top: float = SLEEPER_HEIGHT.y - SLEEPER_HEIGHT.x if n in [2, 3] else 0.0
		(
			sections
			. append(
				[
					Vector3(x, bottom, SLEEPER_WIDTH.x * 0.5),
					Vector3(x, top, SLEEPER_WIDTH.y * 0.5),
					Vector3(x, top, -SLEEPER_WIDTH.y * 0.5),
					Vector3(x, bottom, -SLEEPER_WIDTH.x * 0.5),
				]
			)
		)
	var color: PackedColorArray = PackedColorArray([Color.WHITE])
	for n: int in xs.size() - 1:
		var a: Array = sections[n]
		var b: Array = sections[n + 1]
		for m: int in 3:
			var face: PackedVector3Array = PackedVector3Array([a[m], b[m], b[m + 1], a[m + 1]])
			var middle: Vector3 = (a[m] + a[m + 1]) * 0.5
			mesh.add_face(face, Vector3(0.0, middle.y + 0.2, middle.z), color)
	for n: int in [0, xs.size() - 1]:
		var end: Array = sections[n]
		var outward: Vector3 = Vector3(signf(xs[n]), 0.0, 0.0)
		mesh.add_face(PackedVector3Array(end), outward, color)
	return mesh.to_mesh()


func build() -> void:
	stats = {"traviesas": 0, "via_m": 0.0, "a_ras_m": 0.0}
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
		_open_track(line, heights, start, loose)
	else:
		var rails: Array = track["carriles"]
		for side: int in 2:
			var rail: PackedVector2Array = rails[side]
			_flush_rail(rail.slice(first, last + 2), start, side == 0)


## Vía sobre balasto: el balasto, los dos carriles y las traviesas.
func _open_track(
	line: PackedVector2Array, heights: PackedFloat32Array, start: float, loose: Array
) -> void:
	for part: Array in _clip(line, heights, start):
		var full: PackedVector2Array = part[0]
		var full_z: PackedFloat32Array = part[1]
		var kept: PackedInt32Array = TransitEdges.simplify(full, full_z, full_z)
		var points: PackedVector2Array = PackedVector2Array()
		var z: PackedFloat32Array = PackedFloat32Array()
		for k: int in kept:
			points.append(full[k])
			z.append(full_z[k])
		var sides: Array = [points, TransitEdges.line_normals(points), z, z, false]
		var ballast: Array = []
		var rails: Array = [[], []]
		var scale: float = (_rail_top - SLEEPER_TOP) / RAIL_HEIGHT
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
			for side: int in 2:
				var offset: float = RAIL_OFFSET if side == 0 else -RAIL_OFFSET
				var profile: Array = []
				for corner: Vector2 in RAIL_PROFILE:
					profile.append(Vector2(offset + corner.x, f + SLEEPER_TOP + corner.y * scale))
				rails[side].append(profile)
		var s0: float = part[2]
		edges.extrude(sides, ballast, "balasto", BALLAST_COLOR, true, s0)
		edges.extrude(sides, rails[0], "metal", STEEL_COLOR, false, s0)
		edges.extrude(sides, rails[1], "metal", STEEL_COLOR, false, s0)
		# La punta suelta de una vía (el final de un apartadero, el borde del cráter).
		if loose[0] and full[0] == line[0]:
			edges.cap(sides, ballast, 0, "balasto", BALLAST_COLOR)
		if loose[1] and full[full.size() - 1] == line[line.size() - 1]:
			edges.cap(sides, ballast, points.size() - 1, "balasto", BALLAST_COLOR)
		_sleepers(full, full_z, s0)
		stats["via_m"] += TransitEdges.arc_lengths(full)[full.size() - 1]


## Las traviesas de un trozo: cada [constant SLEEPER_STEP] metros desde el principio de la
## vía ([param s0] es lo que mide la vía hasta el primer punto del trozo).
func _sleepers(points: PackedVector2Array, z: PackedFloat32Array, s0: float) -> void:
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
		if out.owns(p):
			var height: float = lerpf(z[k - 1], z[k], f)
			var along: Vector3 = Vector3(
				points[k].x - points[k - 1].x, z[k] - z[k - 1], points[k - 1].y - points[k].y
			)
			var center: Vector3 = CityPlan.to_world(p, height + SLEEPER_TOP)
			var basis: Basis = Basis.looking_at(along.normalized(), Vector3.UP)
			out.add_instance("traviesa", Transform3D(basis, center))
			stats["traviesas"] += 1
		s += SLEEPER_STEP


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
