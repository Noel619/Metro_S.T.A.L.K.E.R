class_name TransitEdges
extends RefCounted
## Lo que va en las lindes del tránsito (las aristas de transito.json): bordillos, bordes
## de jardín, bordillos bajos de las sendas, contrahuellas, escalones, muros entre dos
## niveles, pretiles (el muelle y el puente), los bordes rotos del vano hundido y el corte
## de la calle en el borde de los socavones. También
## los muros y las barandillas de las escaleras y las marcas viales (pasos de cebra y
## ejes). Lo levanta cada TransitSector para lo suyo: de cada línea, los tramos que caen en
## su sector.
##
## Cada arista se extruye con un perfil (un corte de través) que depende de su tipo y de la
## altura de lo que tiene a cada lado: el grupo de la izquierda y el de la derecha, o el
## terreno. Los perfiles se dan como (desplazamiento hacia la izquierda, altura) en sentido
## antihorario alrededor de la pieza, así que cada tramo sabe hacia dónde mira. Donde el
## terreno queda más alto que la arista, una cara del color del suelo cierra el corte.

## Bordillo: ancho, lo que asoma sobre la acera y su altura sobre la calzada cuando
## detrás no hay acera sino tierra.
const CURB_WIDTH: float = 0.15
const CURB_LIFT: float = 0.01
const CURB_HEIGHT: float = 0.16
## Rampa de colisión de los bordillos y las contrahuellas (se suben andando).
const RAMP: float = 0.25
## Bordillo de jardín (contra la tierra), del alcorque y bordillo bajo de las sendas.
const BORDER: Vector2 = Vector2(0.08, 0.02)
const PIT_BORDER: Vector2 = Vector2(0.08, 0.04)
const PATH_BORDER: Vector2 = Vector2(0.05, 0.03)
## Pretiles: grosor y altura sobre lo que se pisa; muros entre dos niveles con pretil
## cuando el desnivel pasa de [constant PARAPET_FROM].
const PARAPET: Vector2 = Vector2(0.3, 1.0)
const PARAPET_FROM: float = 0.5
## Lo que baja el borde del tablero sobre la losa del puente.
const DECK_EDGE: float = 0.45
## El corte de la calle en el borde de un socavón: lo que mide la costra (lo menos y lo que
## varía), la base de grava de debajo y lo que la ha socavado el agua bajo la costra.
const COLLAPSE_CRUST: Vector2 = Vector2(0.06, 0.07)
const COLLAPSE_BASE: float = 0.22
const COLLAPSE_RECESS: float = 0.14
const COLLAPSE_BASE_COLOR: Color = Color(0.52, 0.5, 0.47, 0.0)
const COLLAPSE_SOIL_COLOR: Color = Color(0.5, 0.45, 0.39, 0.0)
## La línea de seguridad de los andenes: desde dónde y hasta dónde, contando desde el borde.
const PLATFORM_LINE: Vector2 = Vector2(0.15, 0.25)
## Las grietas: lo que se levantan sobre lo que se pisa, lo que tardan en abrirse desde
## sus puntas y su color (casi negro; el alfa lo pone la nieve de su clase).
const CRACK_LIFT: float = 0.006
const CRACK_TAPER: float = 0.35
const CRACK_COLOR: Color = Color(0.09, 0.085, 0.08)
## Pintura de las marcas: lo que se levanta sobre la calzada y el ancho de los ejes.
const PAINT_LIFT: float = 0.012
const AXIS_WIDTH: float = 0.12
const DASH: Vector2 = Vector2(3.0, 6.0)
## Lo más largo que se deja un tramo recto de arista al simplificarla.
const SIMPLIFY_RUN: float = 16.0
## Material de cada tipo de arista.
const EDGE_MATERIALS: Dictionary = {
	"bordillo": "bordillo",
	"borde": "bordillo",
	"bordillo_bajo": "bordillo",
	"alcorque": "bordillo",
	"contrahuella": "granito",
	"escalon": "granito",
	"muro": "hormigon",
	"pretil": "granito",
	"rotura": "hormigon",
	"muro_escalera": "hormigon",
	"derrumbe": "derrumbe",
}
const EDGE_COLOR: Color = Color(0.64, 0.63, 0.6, 0.45)
const RISER_COLOR: Color = Color(0.7, 0.68, 0.65, 0.1)
const WALL_COLOR: Color = Color(0.72, 0.7, 0.66, 0.4)
const RAIL_COLOR: Color = Color(0.38, 0.28, 0.22, 0.2)
## Las rayas del eje que ya no se ven (de cada cien).
const DASH_GONE: float = 0.3
const PAINT_COLOR: Color = Color(0.86, 0.85, 0.8, 0.7)

var transit: CityTransit
var plan: CityPlan
## El sector que se levanta: solo se dibuja lo que cae en él.
var out: TransitSector
var stats: Dictionary = {}


func _init(city_transit: CityTransit, sector: TransitSector) -> void:
	transit = city_transit
	plan = transit.plan
	out = sector


func build() -> void:
	var data: Dictionary = plan.transit
	stats = {"aristas": 0, "muros": 0, "barandillas": 0, "franjas": 0, "grietas": 0}
	for index: int in out.edges:
		_build_edge(data["aristas"][index])
	for index: int in out.walls:
		_build_wall(data["muros"][index])
	for index: int in out.rails:
		_build_railing(data["barandillas"][index])
	_build_markings(data["marcas"])
	_build_cracks(data.get("grietas", []))


func _build_edge(edge: Dictionary) -> void:
	var flat: Array = edge["puntos"]
	var full: PackedVector2Array = PackedVector2Array()
	for k: int in range(0, flat.size(), 2):
		full.append(Vector2(flat[k], flat[k + 1]))
	# Donde faltan piezas del bordillo, el hueco que dejan; lo demás, la arista.
	var gaps: Array = edge.get("huecos", [])
	var kept: Array = [full]
	if not gaps.is_empty():
		var lengths: PackedFloat32Array = arc_lengths(full)
		kept = []
		var from: float = 0.0
		for gap: Array in gaps:
			if float(gap[0]) > from + 0.01:
				kept.append(sub_line(full, lengths, from, float(gap[0])))
			for part: PackedVector2Array in clip_line(
				sub_line(full, lengths, float(gap[0]), float(gap[1]))
			):
				_build_edge_part(edge, part, true)
			from = float(gap[1])
		if lengths[lengths.size() - 1] > from + 0.01:
			kept.append(sub_line(full, lengths, from, lengths[lengths.size() - 1]))
	# Solo lo que cae en el sector (el corte en el linde sale igual desde los dos lados).
	for line: PackedVector2Array in kept:
		for part: PackedVector2Array in clip_line(line):
			_build_edge_part(edge, part)
	stats["aristas"] += 1


func _build_edge_part(edge: Dictionary, part: PackedVector2Array, gap: bool = false) -> void:
	var line: PackedVector2Array = GridClip.subdivide(part, CityTransit.STEP)
	if line.size() < 2:
		return
	var left: int = edge["izq"]
	var right: int = edge["der"]
	var kind: String = edge["tipo"]
	var z_left: PackedFloat32Array = PackedFloat32Array()
	var z_right: PackedFloat32Array = PackedFloat32Array()
	for p: Vector2 in line:
		z_left.append(transit.surface_z(left, p))
		z_right.append(transit.surface_z(right, p) if right >= 0 else transit.terrain_z(p))
	var kept: PackedInt32Array = simplify(line, z_left, z_right)
	var short_line: PackedVector2Array = PackedVector2Array()
	var short_left: PackedFloat32Array = PackedFloat32Array()
	var short_right: PackedFloat32Array = PackedFloat32Array()
	for k: int in kept:
		short_line.append(line[k])
		short_left.append(z_left[k])
		short_right.append(z_right[k])
	var sides: Array = [short_line, line_normals(short_line), short_left, short_right, right < 0]
	if gap:
		_curb_gap(sides)
		return
	match kind:
		"bordillo":
			_curb(sides)
		"borde", "muro_escalera":
			_border(sides, BORDER)
		"bordillo_bajo":
			_border(sides, PATH_BORDER)
		"alcorque":
			_border(sides, PIT_BORDER)
		"contrahuella", "escalon":
			_riser(sides)
		"muro", "pretil", "rotura":
			_wall_edge(sides, kind, transit.group(left)["elevado"])
		"tierra", "fachada":
			_step_face(sides, String(transit.group(left)["clase"]), kind == "fachada")
		"anden":
			_drop_face(sides, true)
		"paso_nivel":
			_drop_face(sides, false)
		"derrumbe":
			_collapse(sides, String(transit.group(left)["clase"]))


## La polilínea recortada por los límites del sector: los trozos que caen dentro.
func clip_line(line: PackedVector2Array) -> Array[PackedVector2Array]:
	var bounds: Rect2 = out.clip_bounds()
	var low: Vector2 = bounds.position
	var high: Vector2 = bounds.end
	var parts: Array[PackedVector2Array] = []
	var current: PackedVector2Array = PackedVector2Array()
	for k: int in line.size() - 1:
		var p: Vector2 = line[k]
		var q: Vector2 = line[k + 1]
		var t0: float = 0.0
		var t1: float = 1.0
		var d: Vector2 = q - p
		var ok: bool = true
		for axis: int in 2:
			if not ok:
				break
			var start: float = p[axis]
			var delta: float = d[axis]
			for limit: Array in [[low[axis], -1.0], [high[axis], 1.0]]:
				var bound: float = limit[0]
				if is_inf(bound):
					continue
				var sign: float = limit[1]
				if absf(delta) < 1e-12:
					if (start - bound) * sign > 0.0:
						ok = false
					continue
				var t: float = (bound - start) / delta
				if delta * sign > 0.0:
					t1 = minf(t1, t)
				else:
					t0 = maxf(t0, t)
		if not ok or t0 > t1 - 1e-9:
			if current.size() >= 2:
				parts.append(current)
			current = PackedVector2Array()
			continue
		var a: Vector2 = p + d * t0 if t0 > 0.0 else p
		var b: Vector2 = p + d * t1 if t1 < 1.0 else q
		if current.is_empty() or current[current.size() - 1].distance_squared_to(a) > 1e-12:
			if current.size() >= 2:
				parts.append(current)
			current = PackedVector2Array([a])
		current.append(b)
		if t1 < 1.0:
			parts.append(current)
			current = PackedVector2Array()
	if current.size() >= 2:
		parts.append(current)
	return parts


## Bordillo: la calzada a la izquierda; a la derecha la acera (el bordillo asoma un
## centímetro) o la tierra (asoma lo que una acera).
func _curb(sides: Array) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var to_terrain: bool = sides[4]
	var profiles: Array = []
	var ramps: Array = []
	var tops: PackedFloat32Array = PackedFloat32Array()
	for n: int in z_left.size():
		var top: float = z_left[n] + CURB_HEIGHT if to_terrain else z_right[n] + CURB_LIFT
		var back: float = minf(z_right[n], top) - 0.1 if to_terrain else z_right[n] - 0.02
		tops.append(top)
		(
			profiles
			. append(
				[
					Vector2(0.0, z_left[n] - 0.05),
					Vector2(0.0, top - 0.02),
					Vector2(-0.02, top),
					Vector2(-CURB_WIDTH, top),
					Vector2(-CURB_WIDTH, back),
				]
			)
		)
		ramps.append([Vector2(RAMP, z_left[n]), Vector2(0.0, top)])
	extrude(sides, profiles, "bordillo", EDGE_COLOR, false)
	_extrude_collision(sides, ramps)
	if to_terrain:
		_closure(sides, tops)


## Donde falta una pieza del bordillo: la tierra de su asiento, de lo alto de la acera (o
## del terreno) a la calzada, y la rampa de colisión para subir.
func _curb_gap(sides: Array) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var faces: Array = []
	var ramps: Array = []
	for n: int in z_left.size():
		var high: float = maxf(z_right[n], z_left[n] + 0.02)
		faces.append([Vector2(0.0, high), Vector2(0.0, z_left[n] - 0.05)])
		ramps.append([Vector2(RAMP, z_left[n]), Vector2(0.0, high)])
	extrude(sides, faces, "derrumbe", COLLAPSE_SOIL_COLOR, false)
	_extrude_collision(sides, ramps)


## Bordillo de jardín, de alcorque o de senda: dentro de lo pavimentado, con la cara de
## fuera hasta el terreno (o hasta la tierra del alcorque).
func _border(sides: Array, size: Vector2) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var profiles: Array = []
	var tops: PackedFloat32Array = PackedFloat32Array()
	for n: int in z_left.size():
		var top: float = z_left[n] + size.y
		tops.append(top)
		(
			profiles
			. append(
				[
					Vector2(size.x, z_left[n] - 0.03),
					Vector2(size.x, top),
					Vector2(0.0, top),
					Vector2(0.0, minf(z_right[n], z_left[n]) - 0.1),
				]
			)
		)
	extrude(sides, profiles, "bordillo", EDGE_COLOR, true)
	if sides[4]:
		_closure(sides, tops)


## Contrahuella (o escalón): de la pisada de abajo (derecha) a la de arriba (izquierda).
func _riser(sides: Array) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var profiles: Array = []
	var ramps: Array = []
	for n: int in z_left.size():
		profiles.append([Vector2(0.0, z_left[n]), Vector2(0.0, z_right[n] - 0.02)])
		ramps.append([Vector2(0.0, z_left[n]), Vector2(-RAMP, z_right[n])])
	extrude(sides, profiles, "granito", RISER_COLOR, false)
	_extrude_collision(sides, ramps)


## Muro entre dos niveles (con pretil arriba si el desnivel es grande), pretil del muelle
## o del puente, y borde roto del tablero en el vano hundido.
func _wall_edge(sides: Array, kind: String, elevated: bool) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var parapet: bool = kind == "pretil"
	if kind == "muro":
		for n: int in z_left.size():
			parapet = parapet or z_left[n] - z_right[n] > PARAPET_FROM
	var profiles: Array = []
	for n: int in z_left.size():
		var bottom: float = minf(z_right[n], z_left[n]) - 0.1
		if elevated:
			bottom = z_left[n] - DECK_EDGE
		if kind == "rotura":
			profiles.append([Vector2(0.0, z_left[n]), Vector2(0.0, bottom)])
		elif parapet:
			(
				profiles
				. append(
					[
						Vector2(PARAPET.x, z_left[n] - 0.02),
						Vector2(PARAPET.x, z_left[n] + PARAPET.y),
						Vector2(0.0, z_left[n] + PARAPET.y),
						Vector2(0.0, bottom),
					]
				)
			)
		else:
			profiles.append([Vector2(0.0, z_left[n]), Vector2(0.0, z_right[n] - 0.05)])
	var material: String = "granito" if kind == "pretil" and not elevated else "hormigon"
	extrude(sides, profiles, material, WALL_COLOR, true)


## La cara entre el borde de un camino de tierra (o de la acera junto a una fachada) y lo
## que tiene al lado.
func _step_face(sides: Array, kind: String, facade: bool) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var profiles: Array = []
	var tops: PackedFloat32Array = PackedFloat32Array()
	for n: int in z_left.size():
		var bottom: float = z_left[n] - 0.6 if facade else minf(z_right[n], z_left[n]) - 0.05
		profiles.append([Vector2(0.0, z_left[n]), Vector2(0.0, bottom)])
		tops.append(z_left[n])
	var material: String = CityTransit.SURFACE_MATERIALS.get(kind, "tierra")
	var tint: Color = CityTransit.SURFACE_COLORS.get(kind, Color.WHITE)
	extrude(sides, profiles, material, tint, false)
	if not facade:
		_closure(sides, tops)


## Una cara de hormigón hasta el balasto: el borde de un andén (con la línea blanca de
## seguridad a lo largo) o la punta de la losa de un paso a nivel.
func _drop_face(sides: Array, stripe: bool) -> void:
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var faces: Array = []
	var line: Array = []
	for n: int in z_left.size():
		faces.append([Vector2(0.0, z_left[n]), Vector2(0.0, minf(z_right[n], z_left[n]) - 0.1)])
		var paint: float = z_left[n] + PAINT_LIFT * 0.25
		line.append([Vector2(PLATFORM_LINE.y, paint), Vector2(PLATFORM_LINE.x, paint)])
	extrude(sides, faces, "hormigon", WALL_COLOR, true)
	if stripe:
		extrude(sides, line, "pintura", PAINT_COLOR, false)


## El borde roto de un socavón (la calle a la izquierda, el hueco a la derecha): la
## costra de lo que se pisa (asfalto, losas, hormigón), de grosor desigual; debajo, la base
## de grava, socavada por el agua (la costra vuela sobre ella), y la tierra hasta la malla
## del socavón. La colisión, una cara a plomo.
func _collapse(sides: Array, kind: String) -> void:
	var line: PackedVector2Array = sides[0]
	var z_left: PackedFloat32Array = sides[2]
	var z_right: PackedFloat32Array = sides[3]
	var crust: Array = []
	var under: Array = []
	var base: Array = []
	var soil: Array = []
	var wall: Array = []
	for n: int in z_left.size():
		var top: float = z_left[n]
		var key: String = "derrumbe/%d/%d" % [roundi(line[n].x * 5.0), roundi(line[n].y * 5.0)]
		var thick: float = COLLAPSE_CRUST.x + COLLAPSE_CRUST.y * CityPlan.chance(key)
		var recess: float = COLLAPSE_RECESS * (0.3 + CityPlan.chance(key + "/b"))
		var low: float = top - thick - COLLAPSE_BASE * (0.7 + 0.6 * CityPlan.chance(key + "/c"))
		var bottom: float = minf(z_right[n], low - 0.05) - 0.05
		crust.append([Vector2(0.0, top + 0.002), Vector2(0.0, top - thick)])
		under.append([Vector2(0.0, top - thick), Vector2(recess, top - thick)])
		base.append([Vector2(recess, top - thick), Vector2(recess * 0.5, low)])
		soil.append([Vector2(recess * 0.5, low), Vector2(0.0, bottom)])
		wall.append([Vector2(0.0, top), Vector2(0.0, bottom)])
	var material: String = CityTransit.SURFACE_MATERIALS.get(kind, "asfalto")
	var tint: Color = CityTransit.SURFACE_COLORS.get(kind, Color.WHITE)
	extrude(sides, crust, material, Color(tint, 0.0), false)
	extrude(sides, under, "grava", COLLAPSE_BASE_COLOR, false)
	extrude(sides, base, "grava", COLLAPSE_BASE_COLOR, false)
	extrude(sides, soil, "derrumbe", COLLAPSE_SOIL_COLOR, false)
	_extrude_collision(sides, wall)


## Donde el terreno queda por encima del borde, una cara de suelo cierra el corte.
func _closure(sides: Array, tops: PackedFloat32Array) -> void:
	var z_right: PackedFloat32Array = sides[3]
	var profiles: Array = []
	var any: bool = false
	for n: int in tops.size():
		var high: float = maxf(z_right[n], tops[n])
		any = any or high > tops[n] + 0.005
		profiles.append([Vector2(0.0, tops[n]), Vector2(0.0, high)])
	if any:
		extrude(sides, profiles, "suelo", CityTransit.GROUND_COLOR, true)


## Muro de una escalera: sigue la línea de los peldaños con su pretil, o asoma lo justo
## sobre el terreno del otro lado si este queda más alto; baja hasta por debajo de los dos.
func _build_wall(wall: Dictionary) -> void:
	var points: Array = wall["puntos"]
	var line: PackedVector2Array = PackedVector2Array()
	var pitch: PackedFloat32Array = PackedFloat32Array()
	for point: Array in points:
		line.append(Vector2(point[0], point[1]))
		pitch.append(point[2])
	var fine: PackedVector2Array = GridClip.subdivide(line, CityTransit.STEP)
	var half: float = float(wall["grosor"]) * 0.5
	var profiles: Array = []
	var copings: Array = []
	var along: PackedFloat32Array = arc_lengths(line)
	var fine_along: PackedFloat32Array = arc_lengths(fine)
	for n: int in fine.size():
		var z_pitch: float = value_at(along, pitch, fine_along[n])
		var ground: float = transit.terrain_z(fine[n])
		var top: float = maxf(
			ground + float(wall["sobre_terreno"]), z_pitch + float(wall["pretil"])
		)
		var bottom: float = minf(ground, z_pitch) - 0.4
		(
			profiles
			. append(
				[
					Vector2(half, bottom),
					Vector2(half, top - 0.08),
					Vector2(-half, top - 0.08),
					Vector2(-half, bottom),
				]
			)
		)
		(
			copings
			. append(
				[
					Vector2(-half - 0.04, top - 0.08),
					Vector2(half + 0.04, top - 0.08),
					Vector2(half + 0.04, top),
					Vector2(-half - 0.04, top),
					Vector2(-half - 0.04, top - 0.08),
				]
			)
		)
	var sides: Array = [fine, line_normals(fine), PackedFloat32Array(), PackedFloat32Array(), false]
	var material: String = String(wall["material"])
	extrude(sides, profiles, material, WALL_COLOR, true)
	extrude(sides, copings, material, WALL_COLOR, false)
	cap(sides, profiles, 0, material)
	cap(sides, profiles, fine.size() - 1, material)
	cap(sides, copings, 0, material)
	cap(sides, copings, fine.size() - 1, material)
	stats["muros"] += 1


## Barandilla de tubo: el pasamanos y un poste cada metro y medio.
func _build_railing(rail: Dictionary) -> void:
	var points: Array = rail["puntos"]
	var since_post: float = 1.5
	for k: int in points.size():
		var p: Vector2 = Vector2(points[k][0], points[k][1])
		var top: Vector3 = out.local(p, float(points[k][2]))
		if k > 0:
			var q: Vector2 = Vector2(points[k - 1][0], points[k - 1][1])
			if out.owns((p + q) * 0.5):
				var start: Vector3 = out.local(q, float(points[k - 1][2]))
				out.buffer("metal").add_beam(
					start - Vector3.UP * 0.025, top - Vector3.UP * 0.025, 0.05, 0.05, RAIL_COLOR
				)
			since_post += p.distance_to(q)
		if since_post >= 1.5 or k == points.size() - 1:
			if out.owns(p):
				out.buffer("metal").add_beam(
					top - Vector3.UP * 0.95, top - Vector3.UP * 0.04, 0.045, 0.045, RAIL_COLOR
				)
			since_post = 0.0
	stats["barandillas"] += 1


## Pasos de cebra y ejes, pintados sobre la calzada (cortados por la rejilla, para que
## sigan la calzada pieza a pieza).
func _build_markings(marks: Dictionary) -> void:
	var level: float = float(plan.transit["niveles"]["calzada"]) + PAINT_LIFT
	for index: int in out.crossings:
		var crossing: Dictionary = marks["pasos"][index]
		var angle: float = deg_to_rad(float(crossing["angulo"]))
		var along: Vector2 = Vector2(cos(angle), sin(angle)) * float(crossing["largo"]) * 0.5
		var across: Vector2 = Vector2(-sin(angle), cos(angle)) * float(crossing["ancho"]) * 0.5
		for stripe: Array in crossing["franjas"]:
			var center: Vector2 = Vector2(stripe[0], stripe[1])
			_paint(
				PackedVector2Array(
					[
						center - along - across,
						center + along - across,
						center + along + across,
						center - along + across
					]
				),
				level
			)
			stats["franjas"] += 1
	for index: int in out.axes:
		var axis: Dictionary = marks["ejes"][index]
		var line: PackedVector2Array = PackedVector2Array()
		for point: Array in axis["puntos"]:
			line.append(Vector2(point[0], point[1]))
		var dashed: bool = axis["tipo"] == "discontinua"
		var lengths: PackedFloat32Array = arc_lengths(line)
		var total: float = lengths[lengths.size() - 1]
		var start: float = 0.0
		var dash: int = 0
		while start < total:
			var end: float = minf(total, start + (DASH.x if dashed else total))
			# Gastada a trozos: de la discontinua faltan rayas enteras.
			if not dashed or CityPlan.chance("raya/%d/%d" % [index, dash]) >= DASH_GONE:
				_paint_stripe(line, lengths, start, end, level)
			start = end + (DASH.y if dashed else 0.0)
			dash += 1


## Las grietas de la calle (tools/ciudad/deterioro.py): tiras oscuras a ras de lo que se
## pisa, afiladas en las puntas y partidas por la rejilla para seguir la rasante. Llevan la
## nieve de su clase: donde la nieve tapa el pavimento, las tapa igual.
func _build_cracks(cracks: Array) -> void:
	for index: int in out.cracks:
		var crack: Dictionary = cracks[index]
		var line: PackedVector2Array = PackedVector2Array()
		for point: Array in crack["puntos"]:
			line.append(Vector2(point[0], point[1]))
		var fine: PackedVector2Array = GridClip.subdivide(line, CityTransit.STEP)
		if fine.size() < 2:
			continue
		var normals: PackedVector2Array = line_normals(fine)
		var lengths: PackedFloat32Array = arc_lengths(fine)
		var total: float = lengths[lengths.size() - 1]
		var half: float = float(crack["ancho"]) * 0.5
		var snow: float = (
			(CityTransit.SURFACE_COLORS.get(String(crack["clase"]), Color.WHITE) as Color).a
		)
		var color: Color = Color(CRACK_COLOR, snow)
		var heights: PackedFloat32Array = PackedFloat32Array()
		var widths: PackedFloat32Array = PackedFloat32Array()
		for k: int in fine.size():
			var z: float = transit.surface_at(fine[k])
			heights.append((transit.terrain_z(fine[k]) if is_nan(z) else z) + CRACK_LIFT)
			var taper: float = minf(lengths[k], total - lengths[k]) / CRACK_TAPER
			widths.append(half * clampf(taper, 0.15, 1.0))
		var drawn: bool = false
		for k: int in fine.size() - 1:
			if not out.owns((fine[k] + fine[k + 1]) * 0.5):
				continue
			var a: Vector2 = fine[k]
			var b: Vector2 = fine[k + 1]
			var points: PackedVector3Array = PackedVector3Array(
				[
					out.local(a - normals[k] * widths[k], heights[k]),
					out.local(b - normals[k + 1] * widths[k + 1], heights[k + 1]),
					out.local(b + normals[k + 1] * widths[k + 1], heights[k + 1]),
					out.local(a + normals[k] * widths[k], heights[k]),
				]
			)
			var up: PackedVector3Array = PackedVector3Array(
				[Vector3.UP, Vector3.UP, Vector3.UP, Vector3.UP]
			)
			var uvs: PackedVector2Array = PackedVector2Array([a, b, b, a])
			out.buffer("grieta").add_polygon(points, up, color, uvs)
			drawn = true
		if drawn:
			stats["grietas"] += 1


## Una franja de línea entre dos distancias a lo largo de la polilínea.
func _paint_stripe(
	line: PackedVector2Array, lengths: PackedFloat32Array, start: float, end: float, level: float
) -> void:
	var step: float = 1.0
	var s: float = start
	while s < end - 1e-3:
		var t: float = minf(end, s + step)
		var a: Vector2 = point_at(line, lengths, s)
		var b: Vector2 = point_at(line, lengths, t)
		var side: Vector2 = (b - a).orthogonal().normalized() * AXIS_WIDTH * 0.5
		_paint(PackedVector2Array([a + side, a - side, b - side, b + side]), level)
		s = t


## Un trozo de pintura (convexo) sobre la calzada: sobre el tablero del puente si cae en
## el río, si no sobre la rasante.
func _paint(quad: PackedVector2Array, level: float) -> void:
	if GridClip.area(quad) < 0.0:
		quad.reverse()
	var bridge: Dictionary = plan.transit["puente"]["regla"]
	for piece: Array in GridClip.split(quad, CityTransit.STEP):
		var poly: PackedVector2Array = piece[2]
		var center: Vector2 = Vector2.ZERO
		for p: Vector2 in poly:
			center += p
		center /= poly.size()
		if not out.owns(center):
			continue
		var on_bridge: bool = plan.is_on_river(center)
		var points: PackedVector3Array = PackedVector3Array()
		var normals: PackedVector3Array = PackedVector3Array()
		var uvs: PackedVector2Array = PackedVector2Array()
		for p: Vector2 in poly:
			var base: float = transit.ramp_z(bridge, p) if on_bridge else transit.base_z(p)
			points.append(out.local(p, base + level))
			normals.append(Vector3.UP)
			uvs.append(p * 0.5)
		out.buffer("pintura").add_polygon(points, normals, PAINT_COLOR, uvs)


## Extruye perfiles a lo largo de la línea: un perfil por punto (todos con el mismo número
## de puntos) y una cara por tramo de perfil y de línea. La textura cuenta a lo largo desde
## [param start] (lo que mide la línea antes de este trozo, para que no salte entre
## sectores).
func extrude(
	sides: Array, profiles: Array, material: String, tint: Color, collide: bool, start: float = 0.0
) -> void:
	var line: PackedVector2Array = sides[0]
	var normals: PackedVector2Array = sides[1]
	var lengths: PackedFloat32Array = arc_lengths(line)
	var tile: float = CityTransit.TILE.get(material, 1.0)
	var colors: PackedColorArray = PackedColorArray([tint])
	var mesh: MeshBuffer = null
	for s: int in line.size() - 1:
		if not out.owns((line[s] + line[s + 1]) * 0.5):
			continue
		if mesh == null:
			mesh = out.buffer(material)
		var a: Array = profiles[s]
		var b: Array = profiles[s + 1]
		for m: int in a.size() - 1:
			var a0: Vector2 = a[m]
			var a1: Vector2 = a[m + 1]
			var b0: Vector2 = b[m]
			var b1: Vector2 = b[m + 1]
			if absf(a1.y - a0.y) + absf(b1.y - b0.y) + absf(a1.x - a0.x) < 1e-4:
				continue
			var face: PackedVector3Array = PackedVector3Array(
				[
					_point(line[s], normals[s], a0),
					_point(line[s + 1], normals[s + 1], b0),
					_point(line[s + 1], normals[s + 1], b1),
					_point(line[s], normals[s], a1),
				]
			)
			var d: Vector2 = (a1 - a0) + (b1 - b0)
			var normal2: Vector2 = (normals[s] + normals[s + 1]).normalized()
			var facing: Vector3 = Vector3(normal2.x, 0.0, -normal2.y) * d.y + Vector3.UP * -d.x
			var uvs: PackedVector2Array = PackedVector2Array(
				[
					Vector2(start + lengths[s], a0.y + a0.x) / tile,
					Vector2(start + lengths[s + 1], b0.y + b0.x) / tile,
					Vector2(start + lengths[s + 1], b1.y + b1.x) / tile,
					Vector2(start + lengths[s], a1.y + a1.x) / tile,
				]
			)
			mesh.add_face(face, facing, colors, uvs)
			if collide:
				out.add_collision(face)


## Solo la colisión de un perfil (las rampas de los bordillos y de los peldaños).
func _extrude_collision(sides: Array, profiles: Array) -> void:
	var line: PackedVector2Array = sides[0]
	var normals: PackedVector2Array = sides[1]
	for s: int in line.size() - 1:
		if not out.owns((line[s] + line[s + 1]) * 0.5):
			continue
		var a: Array = profiles[s]
		var b: Array = profiles[s + 1]
		for m: int in a.size() - 1:
			(
				out
				. add_collision(
					PackedVector3Array(
						[
							_point(line[s], normals[s], a[m]),
							_point(line[s + 1], normals[s + 1], b[m]),
							_point(line[s + 1], normals[s + 1], b[m + 1]),
							_point(line[s], normals[s], a[m + 1]),
						]
					)
				)
			)


## Tapa el extremo de un muro: el perfil del punto [param index], mirando hacia fuera.
func cap(
	sides: Array, profiles: Array, index: int, material: String, tint: Color = WALL_COLOR
) -> void:
	var line: PackedVector2Array = sides[0]
	var normals: PackedVector2Array = sides[1]
	if not out.owns(line[index]):
		return
	var face: PackedVector3Array = PackedVector3Array()
	for p: Vector2 in profiles[index]:
		face.append(_point(line[index], normals[index], p))
	var other: int = 1 if index == 0 else index - 1
	var outward: Vector2 = (line[index] - line[other]).normalized()
	var facing: Vector3 = Vector3(outward.x, 0.0, -outward.y)
	out.buffer(material).add_face(face, facing, PackedColorArray([tint]))
	out.add_collision(face)


func _point(origin: Vector2, normal: Vector2, profile: Vector2) -> Vector3:
	return out.local(origin + normal * profile.x, profile.y)


## Los puntos que hacen falta de una línea partida por la rejilla: se quitan los que caen
## en línea recta con sus vecinos, en planta y en las dos alturas (en lo llano, casi
## todos). Los tramos no pasan de [constant SIMPLIFY_RUN] metros.
static func simplify(
	line: PackedVector2Array, z_left: PackedFloat32Array, z_right: PackedFloat32Array
) -> PackedInt32Array:
	var count: int = line.size()
	var kept: PackedInt32Array = PackedInt32Array([0])
	var anchor: int = 0
	for k: int in range(1, count - 1):
		var a: Vector2 = line[anchor]
		var b: Vector2 = line[k + 1]
		var span: float = a.distance_to(b)
		var straight: bool = span <= SIMPLIFY_RUN and span > 1e-6
		var m: int = anchor + 1
		while straight and m <= k:
			var f: float = clampf((line[m] - a).dot(b - a) / (span * span), 0.0, 1.0)
			straight = (
				line[m].distance_to(a.lerp(b, f)) < 0.002
				and absf(z_left[m] - lerpf(z_left[anchor], z_left[k + 1], f)) < 0.004
				and absf(z_right[m] - lerpf(z_right[anchor], z_right[k + 1], f)) < 0.004
			)
			m += 1
		if not straight:
			kept.append(k)
			anchor = k
	kept.append(count - 1)
	return kept


## Normales hacia la izquierda en cada punto, con inglete en las esquinas (el ancho de los
## perfiles se mantiene al doblar).
static func line_normals(line: PackedVector2Array) -> PackedVector2Array:
	var count: int = line.size()
	var result: PackedVector2Array = PackedVector2Array()
	result.resize(count)
	for k: int in count:
		var before: Vector2 = (line[k] - line[maxi(k - 1, 0)]).normalized()
		var after: Vector2 = (line[mini(k + 1, count - 1)] - line[k]).normalized()
		if k == 0:
			before = after
		if k == count - 1:
			after = before
		var n0: Vector2 = Vector2(-before.y, before.x)
		var n1: Vector2 = Vector2(-after.y, after.x)
		var miter: Vector2 = (n0 + n1).normalized()
		var scale: float = miter.dot(n1)
		result[k] = miter / maxf(scale, 0.5)
	return result


## Distancia acumulada a lo largo de la polilínea.
static func arc_lengths(line: PackedVector2Array) -> PackedFloat32Array:
	var result: PackedFloat32Array = PackedFloat32Array([0.0])
	for k: int in range(1, line.size()):
		result.append(result[k - 1] + line[k].distance_to(line[k - 1]))
	return result


static func value_at(along: PackedFloat32Array, values: PackedFloat32Array, s: float) -> float:
	for k: int in range(1, along.size()):
		if s <= along[k] or k == along.size() - 1:
			var span: float = along[k] - along[k - 1]
			var f: float = 0.0 if span <= 0.0 else clampf((s - along[k - 1]) / span, 0.0, 1.0)
			return lerpf(values[k - 1], values[k], f)
	return values[0]


## El trozo de una polilínea entre dos distancias desde su principio.
static func sub_line(
	line: PackedVector2Array, lengths: PackedFloat32Array, a: float, b: float
) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array([point_at(line, lengths, a)])
	for k: int in line.size():
		if lengths[k] > a + 1e-4 and lengths[k] < b - 1e-4:
			result.append(line[k])
	result.append(point_at(line, lengths, b))
	return result


static func point_at(line: PackedVector2Array, lengths: PackedFloat32Array, s: float) -> Vector2:
	for k: int in range(1, lengths.size()):
		if s <= lengths[k] or k == lengths.size() - 1:
			var span: float = lengths[k] - lengths[k - 1]
			var f: float = 0.0 if span <= 0.0 else clampf((s - lengths[k - 1]) / span, 0.0, 1.0)
			return line[k - 1].lerp(line[k], f)
	return line[0]
