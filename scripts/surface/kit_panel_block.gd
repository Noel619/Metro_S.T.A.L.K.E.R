class_name KitPanelBlock
extends KitRules
## Las reglas de los bloques de paneles: la jrushchovka (5 plantas), el bloque de 9 y la
## torre de 16, con las piezas de kit_paneles (tools/blender/recipes/kit_paneles.py).
##
## El bloque es un rectángulo: la fachada de los portales ("frente"), la de enfrente
## ("trasera") y los testeros, ciegos salvo en la torre. Las fachadas largas se parten en
## columnas de un vano (un panel por habitación) y el bloque, en secciones de un portal:
## en cada una, la escalera (con el portal abajo y las ventanas desfasadas media planta),
## las cocinas a sus lados y, detrás, los balcones (o las logias de los bloques altos).
##
## El daño se cuenta en plantas por columna, con las mismas semillas que la maqueta
## (CityBuildings): 2, se hunde el extremo que mira a la bomba; 3, trozos de alturas
## desiguales; 4, muñones. Lo que queda encima de cada columna hundida son los muñones de
## la planta caída; donde una columna alta mira a una baja se ve el corte, con los forjados
## y las habitaciones al aire. El fuego quema plantas enteras de una sección y deja el
## hollín encima de cada ventana (lo pinta el shader de los muros).

## Medidas del kit (las mismas que la receta de Blender).
const BAY: float = 3.2
const STOREY: float = 2.8
const WALL: float = 0.3
const PLINTH: float = 0.9
const PARAPET: float = 0.6
const TECH: float = 1.6
const LOGGIA: float = 1.2
const PORTAL_HEIGHT: float = PLINTH + STOREY * 0.5
## Metros de fachada por portal.
const SECTION_LENGTH: Dictionary = {"jrushchovka": 16.0, "bloque9": 18.0, "torre16": 1000.0}
## Tonos de cada bloque (multiplican el gris de los paneles).
const TINTS: Array[Color] = [
	Color(1.0, 1.0, 1.0),
	Color(0.95, 0.97, 1.0),
	Color(1.0, 0.97, 0.91),
	Color(0.93, 0.95, 0.92),
	Color(0.98, 0.94, 0.9),
]
## La pintura de los balcones y de las logias (cada vecino la suya, ya desvaída).
const BALCONY_TINTS: Array[Color] = [
	Color(0.62, 0.74, 0.82),
	Color(0.72, 0.8, 0.68),
	Color(0.86, 0.79, 0.64),
	Color(0.8, 0.62, 0.58),
	Color(0.72, 0.72, 0.68),
	Color(0.92, 0.9, 0.84),
]
## De dónde sale el hollín de cada hueco: x del centro y altura de lo alto, en la pieza.
const SOOT_SOURCES: Dictionary = {
	"ventana": Vector2(1.6, 2.3),
	"cocina": Vector2(1.6, 2.3),
	"balcon": Vector2(1.5, 2.3),
	"logia": Vector2(1.5, 2.3),
	"escalera": Vector2(1.6, 2.0),
}
## Las piezas de muro de cada clase de hueco.
const WALLS: Dictionary = {
	"ventana": "panel_ventana",
	"cocina": "panel_cocina",
	"balcon": "panel_balcon",
	"logia": "panel_logia",
	"ciego": "panel_ciego",
}
## La carpintería de cada clase de hueco.
const INSERTS: Dictionary = {
	"ventana": "ventana",
	"cocina": "cocina",
	"balcon": "puerta_balcon",
	"logia": "puerta_balcon",
}
## Probabilidad de que falte un panel, por nivel de daño.
const MISSING_PANEL: Array[float] = [0.0, 0.012, 0.035, 0.12, 0.2]
const ROOF_COLOR: Color = Color("#2f2c29")
const RUBBLE_COLOR: Color = Color("#4d4943")
const RUBBLE_MODELS: PackedStringArray = [
	"res://assets/models/escombros.glb", "res://assets/models/escombros_grande.glb"
]

## Plantas en pie y si su remate está roto, por columna (de la esquina 0 a la 1 del frente).
var standing: PackedInt32Array = PackedInt32Array()
var broken: Array[bool] = []

## Las cuatro esquinas, empezando por el principio del frente (sentido antihorario).
var _corners: PackedVector2Array
var _axis: Vector2
var _inward: Vector2
var _length: float
var _depth: float
var _count: int
var _width: float
var _tint: Color
var _stairs: Dictionary = {}
var _section_of: PackedInt32Array = PackedInt32Array()
var _kitchens: Dictionary = {}
var _balconies: Dictionary = {}
var _fire: Dictionary = {}
var _fire_chance: float = 0.0


func build(parent: Node3D) -> void:
	_setup()
	_damage_columns()
	_plan_sections()
	_plan_fire()
	for edge: int in 4:
		_facade(edge)
	_corners_pieces()
	_cuts()
	_roofs(parent)
	_collision(parent)


# --------------------------------------------------------------------------
# Preparación
# --------------------------------------------------------------------------


func _setup() -> void:
	floors = int(spec.get("pisos", 9 if kind == "bloque9" else (16 if kind == "torre16" else 5)))
	var outline: PackedVector2Array = CityGeometry.clean(spec["huella"])
	outline.reverse()
	if outline.size() != 4:
		push_warning("%s: la huella no es un rectángulo; se usa su caja." % key)
		outline = _bounding_rectangle(outline)
	_origin = spec.get("origen", CityGeometry.centroid(outline))
	var front: int = _front_edge(outline)
	_corners = PackedVector2Array()
	for i: int in 4:
		_corners.append(outline[(front + i) % 4])
	_length = _corners[0].distance_to(_corners[1])
	_depth = _corners[1].distance_to(_corners[2])
	_axis = (_corners[1] - _corners[0]) / _length
	_inward = Vector2(-_axis.y, _axis.x)
	_count = maxi(1, roundi(_length / BAY))
	_width = _length / _count
	_tint = TINTS[_rng.randi() % TINTS.size()]
	_wear = clampf(0.15 + 0.22 * damage + _rng.randf_range(-0.1, 0.1), 0.0, 1.0)


## El lado de los portales: el que dice la ficha o el largo que mira más al sur.
func _front_edge(outline: PackedVector2Array) -> int:
	if spec.has("entrada"):
		return posmod(int(spec["entrada"]), 4)
	var best: int = 0
	var best_score: float = INF
	for i: int in 4:
		var edge: Vector2 = outline[(i + 1) % 4] - outline[i]
		var outward: Vector2 = Vector2(edge.y, -edge.x).normalized()
		# Los lados largos primero; entre ellos, el que mira al sur.
		var score: float = -edge.length() * 10.0 + outward.y
		if score < best_score:
			best_score = score
			best = i
	return best


func _bounding_rectangle(points: PackedVector2Array) -> PackedVector2Array:
	var axis: Vector2 = CityGeometry.long_axis(points)
	var across: Vector2 = Vector2(-axis.y, axis.x)
	var along: Vector2 = CityGeometry.extent(points, axis)
	var side: Vector2 = CityGeometry.extent(points, across)
	return PackedVector2Array(
		[
			axis * along.x + across * side.x,
			axis * along.y + across * side.x,
			axis * along.y + across * side.y,
			axis * along.x + across * side.y,
		]
	)


## Las plantas que quedan en pie en cada columna, con las semillas de la maqueta.
func _damage_columns() -> void:
	standing.resize(_count)
	standing.fill(floors)
	broken.resize(_count)
	broken.fill(false)
	if damage < 2:
		return
	# La maqueta corta a lo largo del lado más largo de la huella; puede ir al revés que el
	# frente, y entonces sus trozos se cuentan desde el otro extremo.
	var maquette_axis: Vector2 = CityGeometry.long_axis(CityGeometry.clean(spec["huella"]))
	var same: bool = maquette_axis.dot(_axis) > 0.0
	var bomb_along: float = (_bomb - _corners[0]).dot(_axis)
	if damage == 2:
		if _length < 12.0 or floors < 2:
			return
		var cut: float = _length * (0.15 + 0.2 * CityPlan.chance(key + "/corte"))
		var kept: int = clampi(
			roundi(floors * (0.35 + 0.35 * CityPlan.chance(key + "/resto"))), 1, floors - 1
		)
		var near_start: bool = bomb_along < _length * 0.5
		var lowered: Vector2 = Vector2(0.0, cut) if near_start else Vector2(_length - cut, _length)
		_lower(lowered, kept)
		return
	var chunks: int = clampi(int(_length / 9.0), 1, 3 + int(CityPlan.chance(key + "/trozos") * 3.0))
	for i: int in chunks:
		var span: Vector2 = Vector2(_length * i / chunks, _length * (i + 1) / chunks)
		if not same:
			span = Vector2(_length - span.y, _length - span.x)
		var r: float = CityPlan.chance("%s/trozo/%d" % [key, i])
		var near_blast: float = (
			1.0 - clampf(absf((span.x + span.y) * 0.5 - bomb_along) / maxf(_length, 1.0), 0.0, 1.0)
		)
		var kept: int
		if damage == 4:
			kept = clampi(int(0.6 + 1.5 * r), 1, 2)
		else:
			var fraction: float = clampf(lerpf(0.45, 1.0, r) - near_blast * 0.2, 0.45, 1.0)
			kept = clampi(roundi(floors * fraction), 1, floors)
		_lower(span, kept)


func _lower(span: Vector2, kept: int) -> void:
	for j: int in _count:
		var middle: float = (j + 0.5) * _width
		if middle >= span.x and middle < span.y:
			standing[j] = kept
			broken[j] = true


## Portales, cocinas y balcones de cada sección.
func _plan_sections() -> void:
	var sections: int = int(spec.get("portales", 0))
	if sections <= 0:
		sections = clampi(roundi(_length / SECTION_LENGTH[kind]), 1, maxi(1, int(_count / 3.0)))
	_section_of.resize(_count)
	for s: int in sections:
		var first: int = roundi(float(_count) * s / sections)
		var last: int = roundi(float(_count) * (s + 1) / sections)
		for j: int in range(first, last):
			_section_of[j] = s
		var stair: int = first + int((last - first - 1) / 2.0)
		_stairs[stair] = s
		_kitchens[stair - 1] = true
		_kitchens[stair + 1] = true
		_balconies[stair - 1] = true
		_balconies[stair + (2 if last - first >= 6 else 1)] = true


## Dónde hubo fuego: plantas seguidas de una sección (parcial) o de todas (total).
func _plan_fire() -> void:
	var fire: String = spec.get("incendio", "no")
	var sections: int = _stairs.size()
	if fire == "total":
		for s: int in sections:
			_fire[s] = Vector3(0, floors, 0.55)
	elif fire == "parcial":
		var s: int = _rng.randi() % maxi(1, sections)
		var first: int = _rng.randi_range(0, maxi(0, floors - 2))
		_fire[s] = Vector3(first, mini(floors, first + _rng.randi_range(2, 4)), 0.7)
	_fire_chance = 0.5 if damage >= 3 else 0.004


func _burnt(column: int, floor_index: int) -> bool:
	var section: int = _section_of[clampi(column, 0, _count - 1)]
	if _fire.has(section):
		var span: Vector3 = _fire[section]
		if floor_index >= int(span.x) and floor_index < int(span.y):
			return _rng.randf() < span.z
	return _rng.randf() < _fire_chance


# --------------------------------------------------------------------------
# Fachadas
# --------------------------------------------------------------------------


## Una fachada: el frente (0), el testero del final (1), la trasera (2) y el del principio (3).
func _facade(edge: int) -> void:
	var start: Vector2 = _corners[edge]
	var end: Vector2 = _corners[(edge + 1) % 4]
	var direction: Vector2 = (end - start).normalized()
	var long: bool = edge % 2 == 0
	var bays: int = _count if long else maxi(1, roundi(_depth / BAY))
	var width: float = start.distance_to(end) / bays
	var outward: Vector2 = Vector2(direction.y, -direction.x)
	var facing: bool = outward.dot((_bomb - _center()).normalized()) > 0.35
	var role: String = ["frente", "testero", "trasera", "testero"][edge]
	if kind == "torre16" and role == "testero":
		role = "trasera"
	for bay: int in bays:
		var column: int = bay if edge == 0 else (_count - 1 - bay if edge == 2 else 0)
		if edge == 1:
			column = _count - 1
		var face: Dictionary = {
			"start": start + direction * (bay * width),
			"direction": direction,
			"scale": width / BAY,
			"role": role,
			"column": column,
			"facing": facing,
		}
		if edge == 0 and _stairs.has(column):
			_stair_column(face)
		else:
			_column(face, bay)


func _column(face: Dictionary, bay: int) -> void:
	var column: int = face["column"]
	var plinth: String = "zocalo_respiradero" if bay % 3 == 1 else "zocalo"
	assembly.put(plinth, _frame(face, 0.0), _tint)
	var below: Color = Color(_wear, 0.0, 0.0, 0.0)
	for f: int in standing[column]:
		below = _cell(face, f, below)
	_top(face, standing[column], below)


## Una celda (un vano de una planta). Devuelve el hollín que deja en la de encima.
func _cell(face: Dictionary, f: int, below: Color) -> Color:
	var placement: Transform3D = _frame(face, PLINTH + f * STOREY)
	var tone: Color = _panel_tone()
	var data: Color = _from_below(below, STOREY)
	var opening: String = _opening(face, f)
	if opening != "ciego" and f > 0 and _rng.randf() < MISSING_PANEL[damage]:
		assembly.put("panel_caido", placement, tone, data)
		return Color(_wear, 0.0, 0.0, 0.0)
	if opening == "ciego":
		var fell: bool = _rng.randf() < MISSING_PANEL[damage] * 0.5
		assembly.put("panel_caido" if fell else "panel_ciego", placement, tone, data)
		return Color(_wear, 0.0, 0.0, 0.0)
	var burnt: bool = _burnt(face["column"], f)
	var source: Vector2 = SOOT_SOURCES[opening]
	if burnt:
		data = Color(_wear, 0.9, source.x, source.y)
	assembly.put(WALLS[opening], placement, tone, data)
	var state: String = "quemada" if burnt else _window_state(f, face["facing"])
	var inside: Transform3D = placement
	if opening == "logia":
		inside = placement * Transform3D(Basis(), Vector3(0.0, 0.0, -LOGGIA))
		_loggia(placement, burnt)
	elif opening == "balcon" and f > 0:
		_balcony(placement, burnt)
	assembly.put("%s_%s" % [INSERTS[opening], _insert_state(INSERTS[opening], state)], inside)
	assembly.put(_room(burnt), inside)
	return Color(_wear, 0.75, source.x, source.y) if burnt else Color(_wear, 0.0, 0.0, 0.0)


## La clase de hueco de una celda.
func _opening(face: Dictionary, f: int) -> String:
	var column: int = face["column"]
	match String(face["role"]):
		"testero":
			return "ciego"
		"frente":
			return "cocina" if _kitchens.has(column) else "ventana"
	if f > 0 and _balconies.has(column):
		return "balcon" if kind == "jrushchovka" else "logia"
	return "ventana"


## Lo que remata una columna: los muñones de la planta hundida o el peto.
func _top(face: Dictionary, kept: int, below: Color) -> void:
	var column: int = face["column"]
	var top: float = PLINTH + kept * STOREY
	var data: Color = _from_below(below, STOREY)
	if broken[column]:
		# Los testeros no tienen ventanas: sus muñones son bajos y de lado a lado.
		var stubs: Array = ["c", "d", "f"]
		if face["role"] != "testero":
			stubs = ["a", "b", "c", "d", "e", "f"]
		assembly.put("panel_roto_" + _pick(stubs), _frame(face, top), _panel_tone(), data)
	elif kept == floors:
		var parapet: String = "peto" if kind == "jrushchovka" else "peto_tecnico"
		if damage >= 2 and _rng.randf() < 0.08:
			parapet = "peto_roto"
		assembly.put(parapet, _frame(face, top), _tint, data)


## La columna de la escalera: el portal, las ventanas de los descansillos y el remate.
func _stair_column(face: Dictionary) -> void:
	var column: int = face["column"]
	var kept: int = standing[column]
	var base: Transform3D = _frame(face, 0.0)
	assembly.put("panel_portal", base, _tint)
	assembly.put("puerta_portal_" + _door_state(), base)
	var fallen_canopy: float = [0.0, 0.08, 0.2, 0.6, 0.85][damage]
	assembly.put("marquesina_caida" if _rng.randf() < fallen_canopy else "marquesina", base)
	assembly.put("escalones", base)
	if _rng.randf() < [0.0, 0.6, 0.45, 0.15, 0.05][damage]:
		assembly.put("banco_portal", base * Transform3D(Basis(), Vector3(-0.75, 0.0, 0.85)))
	var below: Color = Color(_wear, 0.0, 0.0, 0.0)
	for k: int in maxi(0, kept - 1):
		var placement: Transform3D = _frame(face, PORTAL_HEIGHT + k * STOREY)
		var burnt: bool = _burnt(column, k + 1)
		var data: Color = _from_below(below, STOREY)
		var source: Vector2 = SOOT_SOURCES["escalera"]
		if burnt:
			data = Color(_wear, 0.8, source.x, source.y)
		assembly.put("panel_escalera", placement, _panel_tone(), data)
		var state: String = "quemada" if burnt else _window_state(k + 1, face["facing"])
		assembly.put("escalera_" + _insert_state("escalera", state), placement)
		assembly.put("escalera_interior", placement)
		below = Color(_wear, 0.6, source.x, source.y) if burnt else Color(_wear, 0.0, 0.0, 0.0)
	var top: float = PLINTH + kept * STOREY
	var remate: Color = _from_below(below, STOREY)
	assembly.put("panel_remate", _frame(face, top - STOREY * 0.5), _panel_tone(), remate)
	below.a -= STOREY * 0.5
	_top(face, kept, below)


func _balcony(placement: Transform3D, burnt: bool) -> void:
	var r: float = _rng.randf()
	var fallen: float = FALLEN_BALCONY[damage] + (0.2 if burnt else 0.0)
	if r < fallen * 0.6:
		assembly.put("balcon_caido", placement)
		return
	if r < fallen:
		assembly.put("balcon_arrancado", placement)
		return
	var style: float = _rng.randf()
	if burnt or style < 0.3:
		assembly.put("balcon_reja", placement)
	elif style < 0.68:
		assembly.put("balcon_chapa", placement)
		assembly.put("chapa_balcon", placement, _pick_color(BALCONY_TINTS))
	else:
		assembly.put("balcon_acristalado", placement)
		return
	if not burnt and _rng.randf() < 0.35:
		assembly.put(_pick(["trastos_a", "trastos_b"]), placement)


func _loggia(placement: Transform3D, burnt: bool) -> void:
	if _rng.randf() < FALLEN_BALCONY[damage] * 0.7:
		assembly.put("antepecho_roto", placement)
		return
	assembly.put("antepecho_logia", placement, _pick_color(BALCONY_TINTS))
	if not burnt and _rng.randf() < 0.3:
		assembly.put("logia_acristalada", placement)


## Las cocinas, las puertas de balcón y la escalera tienen menos estados que las ventanas.
func _insert_state(insert: String, state: String) -> String:
	if insert == "ventana":
		return state
	if insert == "escalera":
		return _stair_state(state)
	return _short_state(state)


func _room(burnt: bool) -> String:
	if burnt:
		return "habitacion_quemada"
	return _pick(["habitacion_a", "habitacion_b", "habitacion_c"])


## Las esquinas: tapan el hueco entre los zócalos (y las albardillas) que sobresalen.
func _corners_pieces() -> void:
	for edge: int in 4:
		var start: Vector2 = _corners[edge]
		var direction: Vector2 = (_corners[(edge + 1) % 4] - start).normalized()
		var face: Dictionary = {"start": start, "direction": direction, "scale": 1.0}
		assembly.put("esquina_zocalo", _frame(face, 0.0), _tint)
		var column: int = [0, _count - 1, _count - 1, 0][edge]
		if not broken[column] and standing[column] == floors:
			var cap: String = "esquina_peto" if kind == "jrushchovka" else "esquina_peto_tecnico"
			assembly.put(cap, _frame(face, PLINTH + floors * STOREY), _tint)


## Donde una columna alta mira a una más baja, el corte: forjados y habitaciones al aire.
func _cuts() -> void:
	for j: int in _count - 1:
		if standing[j] == standing[j + 1]:
			continue
		var high: int = j if standing[j] > standing[j + 1] else j + 1
		var low: int = j + 1 if high == j else j
		var at: Vector2 = _corners[0] + _axis * ((j + 1) * _width)
		var outward: Vector2 = _axis if low > high else -_axis
		var direction: Vector2 = Vector2(-outward.y, outward.x)
		var start: Vector2 = at if direction.dot(_inward) > 0.0 else at + _inward * _depth
		var bays: int = maxi(1, roundi(_depth / BAY))
		for bay: int in bays:
			var face: Dictionary = {
				"start": start + direction * (bay * _depth / bays),
				"direction": direction,
				"scale": _depth / bays / BAY,
			}
			for f: int in range(standing[low], standing[high]):
				assembly.put(
					_pick(["corte_a", "corte_b"]), _frame(face, PLINTH + f * STOREY), _tint
				)
			assembly.put("corte_roto", _frame(face, PLINTH + standing[high] * STOREY), _tint)


# --------------------------------------------------------------------------
# Cubiertas y colisión
# --------------------------------------------------------------------------


## Tramos de columnas seguidas con la misma altura: [primera, última + 1].
func _runs() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	var first: int = 0
	for j: int in range(1, _count + 1):
		if j == _count or standing[j] != standing[first] or broken[j] != broken[first]:
			result.append(Vector2i(first, j))
			first = j
	return result


func _roofs(parent: Node3D) -> void:
	var roof: MeshBuffer = MeshBuffer.new()
	var rubble: MeshBuffer = MeshBuffer.new()
	for run: Vector2i in _runs():
		var intact: bool = not broken[run.x] and standing[run.x] == floors
		var height: float = PLINTH + standing[run.x] * STOREY + 0.04
		var start_inset: float = WALL if run.x == 0 else 0.0
		var end_inset: float = WALL if run.y == _count else 0.0
		var cap: PackedVector2Array = _strip(
			run.x * _width + start_inset, run.y * _width - end_inset, WALL, _depth - WALL
		)
		var target: MeshBuffer = roof if intact else rubble
		var color: Color = (ROOF_COLOR if intact else RUBBLE_COLOR).srgb_to_linear()
		target.add_cap(cap, PackedInt32Array([0, 1, 2, 0, 2, 3]), height, color, _origin)
		if intact:
			_roof_props(run, height)
		else:
			_rubble_on(parent, run, height)
	var snow: Material = load("res://assets/materials/nevado.tres")
	for entry: Array in [["Cubierta", roof], ["Escombro", rubble]]:
		var buffer: MeshBuffer = entry[1]
		if buffer.is_empty():
			continue
		var instance: MeshInstance3D = MeshInstance3D.new()
		instance.name = entry[0]
		instance.mesh = buffer.to_mesh(snow)
		parent.add_child(instance)


## Lo que hay sobre la cubierta de un tramo intacto: la salida (o la caseta de los
## ascensores) de cada portal, las ventilaciones y las antenas.
func _roof_props(run: Vector2i, height: float) -> void:
	for stair: int in _stairs:
		if stair < run.x or stair >= run.y:
			continue
		var exit: String = "salida_cubierta" if kind == "jrushchovka" else "caseta_ascensor"
		var inset: float = 1.6 if kind == "jrushchovka" else 2.6
		assembly.put(exit, _roof_frame((stair + 0.5) * _width, inset, height, 0.0))
		for _i: int in _rng.randi_range(1, 3):
			var along: float = _rng.randf_range(run.x * _width + 1.5, run.y * _width - 1.5)
			var inward: float = _rng.randf_range(2.0, _depth - 2.0)
			var fallen: bool = _rng.randf() < 0.12 * damage
			var antenna: String = "antena_caida" if fallen else _pick(["antena_a", "antena_b"])
			var turn: float = _rng.randf_range(-PI, PI)
			assembly.put(antenna, _roof_frame(along, inward, height, turn))
	var along: float = run.x * _width + _width
	while along < run.y * _width - _width * 0.5:
		if _rng.randf() < 0.6:
			var turn: float = 0.0 if _rng.randf() < 0.5 else PI
			var inward: float = _depth * 0.5 + _rng.randf_range(-0.8, 0.8)
			assembly.put("ventilacion", _roof_frame(along, inward, height, turn))
		along += _width * 2.0


## Escombros sobre el forjado de un tramo hundido y al pie de su fachada: los que caen
## fuera lo hacen del lado contrario a la bomba (docs/CIUDAD.md), más cuanto más se hundió.
func _rubble_on(parent: Node3D, run: Vector2i, height: float) -> void:
	var span: float = (run.y - run.x) * _width
	var heaps: int = maxi(1, roundi(span / 7.0))
	var lost: float = float(floors - standing[run.x]) / floors
	var bomb_behind: bool = (_bomb - _center()).dot(_inward) > 0.0
	for k: int in heaps:
		var along: float = run.x * _width + span * (k + _rng.randf_range(0.25, 0.75)) / heaps
		var across: float = _depth * _rng.randf_range(0.3, 0.7)
		var on_top: Vector2 = _corners[0] + _axis * along + _inward * across
		_heap(parent, _local(on_top, height - 0.1), _rng.randf_range(0.6, 0.95))
		if _rng.randf() > 0.35 + lost:
			continue
		var outside: float = -2.2 - 2.0 * lost if bomb_behind else _depth + 2.2 + 2.0 * lost
		var below: Vector2 = _corners[0] + _axis * along + _inward * outside
		_heap(parent, _local(below, -0.1), _rng.randf_range(0.9, 1.3) + lost)


func _heap(parent: Node3D, position: Vector3, size: float) -> void:
	var model: PackedScene = load(RUBBLE_MODELS[_rng.randi() % RUBBLE_MODELS.size()])
	var heap: Node3D = model.instantiate()
	heap.name = "Escombros_%d" % parent.get_child_count()
	heap.position = position
	heap.rotation.y = _rng.randf_range(-PI, PI)
	heap.scale = Vector3.ONE * size
	parent.add_child(heap)


## Una caja de colisión por tramo, del suelo a lo alto de lo que queda.
func _collision(parent: Node3D) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Colision"
	parent.add_child(body)
	for run: Vector2i in _runs():
		var top: float = PLINTH + standing[run.x] * STOREY
		if not broken[run.x] and standing[run.x] == floors:
			top += PARAPET if kind == "jrushchovka" else TECH
		var middle: Vector2 = (
			_corners[0] + _axis * ((run.x + run.y) * 0.5 * _width) + _inward * (_depth * 0.5)
		)
		var shape: BoxShape3D = BoxShape3D.new()
		shape.size = Vector3((run.y - run.x) * _width, top, _depth)
		var holder: CollisionShape3D = CollisionShape3D.new()
		holder.shape = shape
		var x_axis: Vector3 = Vector3(_axis.x, 0.0, -_axis.y)
		holder.transform = Transform3D(
			Basis(x_axis, Vector3.UP, x_axis.cross(Vector3.UP)), _local(middle, top * 0.5)
		)
		body.add_child(holder)


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------


## Un sitio de la cubierta: [param along] metros por el frente y [param inward] hacia dentro.
func _roof_frame(along: float, inward: float, height: float, turn: float) -> Transform3D:
	var point: Vector2 = _corners[0] + _axis * along + _inward * inward
	var x_axis: Vector3 = Vector3(_axis.x, 0.0, -_axis.y)
	var basis: Basis = Basis(x_axis, Vector3.UP, x_axis.cross(Vector3.UP))
	return Transform3D(basis.rotated(Vector3.UP, turn), _local(point, height))


## Una franja del bloque: de [param from] a [param to] metros por el frente y de
## [param near] a [param far] hacia dentro.
func _strip(from: float, to: float, near: float, far: float) -> PackedVector2Array:
	var a: Vector2 = _corners[0] + _axis * from
	var b: Vector2 = _corners[0] + _axis * to
	return PackedVector2Array(
		[a + _inward * near, b + _inward * near, b + _inward * far, a + _inward * far]
	)


func _center() -> Vector2:
	return _corners[0] + _axis * (_length * 0.5) + _inward * (_depth * 0.5)


## Los paneles nunca salen iguales, pero varían de tono y no de sitio: unos milímetros de
## desajuste abrirían rendijas por las que asoma el canto de la junta, y el contorno de
## tinta las dibujaría a puntos.
func _panel_tone() -> Color:
	var shade: float = 1.0 + _rng.randf_range(-0.035, 0.035)
	return Color(_tint.r * shade, _tint.g * shade, _tint.b * shade)
