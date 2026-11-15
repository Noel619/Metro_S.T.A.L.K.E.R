class_name KitMasonry
extends KitRules
## Las reglas de las casas de muros de carga: la estalinka y la casa obrera estalinista, con
## las piezas de kit_estalinka (tools/blender/recipes/kit_estalinka.py). A diferencia de los
## bloques de paneles, siguen cualquier huella del plano: rectas, curvas alrededor de la
## plaza (un vano por tramo), en L o recortadas.
##
## Cada lado de la huella es fachada de calle o de patio (los puntos de "patios" de la ficha
## dicen qué lados miran a un patio). La de calle lleva los bajos almohadillados con
## escaparates, los portales y el arco; ventanas con recercado, con cornisilla o frontón en
## las plantas nobles; balcones de balaustres en los vanos centrales, pilastras, imposta y
## cornisa. La del patio es lisa, con la escalera de servicio y su puerta. La casa obrera es
## más pobre: sin almohadillado ni pilastras, con alero en vez de cornisa.
##
## El daño sigue a la maqueta: la huella se corta a lo largo de su lado más largo en trozos
## de alturas distintas (con las mismas semillas). Donde un trozo alto mira a uno bajo se ve
## el corte; lo intacto lleva su cubierta a cuatro aguas, y lo hundido, escombros encima.

const BAY: float = 3.2
const STOREY: float = 3.4
const WALL: float = 0.64
const PLINTH: float = 0.6
const GROUND: float = PLINTH + STOREY
## Del suelo al primer descansillo de la escalera de servicio.
const BACK_HEIGHT: float = PLINTH + STOREY * 0.5
## Alto de la cornisa y de lo que sube la cubierta por encima de ella.
const CORNICE: float = 0.77
const ROOF_RISE: float = 3.2
const ROOF_INSET: float = 4.4
## Metros de fachada por portal (y por escalera de servicio en el patio).
const PORTAL_EVERY: float = 18.0
## Tonos de cada casa: ocre, salmón, crema, amarillo, gris y verde pálido.
const TINTS: Array[Color] = [
	Color(1.0, 1.0, 1.0),
	Color(1.0, 0.9, 0.84),
	Color(0.99, 0.99, 0.93),
	Color(1.0, 0.96, 0.8),
	Color(0.9, 0.9, 0.9),
	Color(0.9, 0.95, 0.88),
]
## La chapa de las cubiertas, pintada hace mucho: verde, roja o gris.
const ROOF_COLORS: Array[Color] = [Color("#4d5850"), Color("#5e4840"), Color("#55585a")]
const RUBBLE_COLOR: Color = Color("#4d4943")
## De dónde sale el hollín de cada hueco (x del centro, altura de lo alto), en la pieza.
const SOOT_SOURCES: Dictionary = {
	"ventana": Vector2(1.6, 3.05),
	"balcon": Vector2(1.6, 2.95),
	"patio": Vector2(1.6, 2.95),
	"escalera": Vector2(1.6, 2.5),
}
const RUBBLE_MODELS: PackedStringArray = [
	"res://assets/models/escombros.glb", "res://assets/models/escombros_grande.glb"
]

var _storey: float
var _worker: bool
var _outline: PackedVector2Array
var _axis: Vector2
var _span: Vector2
## Los trozos del daño a lo largo del eje: [desde, hasta, plantas, roto].
var _chunks: Array[Array] = []
var _edges: Array[Dictionary] = []
var _tint: Color
var _roof_color: Color
var _fire: Vector3 = Vector3(-1.0, -1.0, 0.0)
var _fire_chance: float = 0.0


func build(parent: Node3D) -> void:
	_setup()
	_damage_chunks()
	_plan_edges()
	for edge: Dictionary in _edges:
		_facade(edge)
	_corners_pieces()
	_cuts()
	_roofs(parent)


# --------------------------------------------------------------------------
# Preparación
# --------------------------------------------------------------------------


func _setup() -> void:
	_worker = kind == "estalinka_baja"
	floors = int(spec.get("pisos", 3 if _worker else 7))
	_storey = float(spec.get("planta", 3.2 if _worker else STOREY))
	var cleaned: PackedVector2Array = CityGeometry.clean(spec["huella"])
	_axis = CityGeometry.long_axis(cleaned)
	_span = CityGeometry.extent(cleaned, _axis)
	cleaned.reverse()
	_outline = _merge_short(cleaned, 1.0)
	_origin = spec.get("origen", CityGeometry.centroid(_outline))
	_tint = TINTS[_rng.randi() % TINTS.size()]
	_roof_color = ROOF_COLORS[_rng.randi() % ROOF_COLORS.size()]
	_wear = clampf(0.2 + 0.2 * damage + _rng.randf_range(-0.1, 0.1), 0.0, 1.0)
	var fire: String = spec.get("incendio", "no")
	if fire == "total":
		_fire = Vector3(0, floors, 0.55)
	elif fire == "parcial":
		var first: int = _rng.randi_range(0, maxi(0, floors - 2))
		_fire = Vector3(first, mini(floors, first + _rng.randi_range(2, 3)), 0.5)
	_fire_chance = 0.5 if damage >= 3 else 0.004


## Quita los lados de menos de [param shortest] metros (las astillas de los recortes).
func _merge_short(points: PackedVector2Array, shortest: float) -> PackedVector2Array:
	var result: PackedVector2Array = points.duplicate()
	var changed: bool = true
	while changed and result.size() > 3:
		changed = false
		for i: int in result.size():
			var next: int = (i + 1) % result.size()
			if result[i].distance_to(result[next]) < shortest:
				result.remove_at(next)
				changed = true
				break
	return result


## Los trozos del daño, con las semillas de la maqueta (CityBuildings).
func _damage_chunks() -> void:
	var length: float = _span.y - _span.x
	_chunks = [[_span.x - 1.0, _span.y + 1.0, floors, false]]
	if damage < 2:
		return
	var blast_side: float = _bomb.dot(_axis)
	if damage == 2:
		if length < 12.0 or floors < 2:
			return
		var blast_first: bool = blast_side < (_span.x + _span.y) * 0.5
		var cut_length: float = length * (0.15 + 0.2 * CityPlan.chance(key + "/corte"))
		var cut: float = _span.x + cut_length if blast_first else _span.y - cut_length
		var kept: int = clampi(
			roundi(floors * (0.35 + 0.35 * CityPlan.chance(key + "/resto"))), 1, floors - 1
		)
		_chunks = [
			[_span.x - 1.0, cut, kept if blast_first else floors, blast_first],
			[cut, _span.y + 1.0, floors if blast_first else kept, not blast_first],
		]
		return
	_chunks = []
	var count: int = clampi(int(length / 9.0), 1, 3 + int(CityPlan.chance(key + "/trozos") * 3.0))
	for i: int in count:
		var from: float = _span.x + length * i / count
		var to: float = _span.x + length * (i + 1) / count
		var r: float = CityPlan.chance("%s/trozo/%d" % [key, i])
		var near_blast: float = (
			1.0 - clampf(absf((from + to) * 0.5 - blast_side) / maxf(length, 1.0), 0.0, 1.0)
		)
		var kept: int
		if damage == 4:
			kept = clampi(int(0.6 + 1.5 * r), 1, 2)
		else:
			var fraction: float = clampf(lerpf(0.45, 1.0, r) - near_blast * 0.2, 0.45, 1.0)
			kept = clampi(roundi(floors * fraction), 1, floors)
		_chunks.append(
			[from - (1.0 if i == 0 else 0.0), to + (1.0 if i == count - 1 else 0.0), kept, true]
		)


## El trozo del daño en el que cae un punto del plano.
func _chunk_at(point: Vector2) -> Array:
	var t: float = point.dot(_axis)
	for chunk: Array in _chunks:
		if t >= float(chunk[0]) and t < float(chunk[1]):
			return chunk
	return _chunks[_chunks.size() - 1]


## Los lados de la huella: su papel (calle o patio), sus vanos y lo que va en los bajos.
func _plan_edges() -> void:
	var courtyards: PackedVector2Array = spec.get("patios", PackedVector2Array())
	var longest_street: int = -1
	var count: int = _outline.size()
	for i: int in count:
		var a: Vector2 = _outline[i]
		var b: Vector2 = _outline[(i + 1) % count]
		var length: float = a.distance_to(b)
		var direction: Vector2 = (b - a) / length
		var outward: Vector2 = Vector2(direction.y, -direction.x)
		var role: String = "patio" if _faces_courtyard(a, b, outward, courtyards) else "calle"
		if _worker and role == "calle":
			role = "obrera"
		var bays: int = maxi(1, roundi(length / BAY))
		(
			_edges
			. append(
				{
					"index": i,
					"start": a,
					"direction": direction,
					"outward": outward,
					"length": length,
					"role": role,
					"bays": bays,
					"width": length / bays,
					"facing": outward.dot((_bomb - a).normalized()) > 0.35,
				}
			)
		)
		if role == "calle" and (longest_street < 0 or length > _edges[longest_street]["length"]):
			longest_street = i
	for edge: Dictionary in _edges:
		edge["ground"] = _ground_program(edge, edge["index"] == longest_street)


func _faces_courtyard(
	a: Vector2, b: Vector2, outward: Vector2, courtyards: PackedVector2Array
) -> bool:
	var middle: Vector2 = (a + b) * 0.5
	for point: Vector2 in courtyards:
		var toward: Vector2 = point - middle
		if toward.length() < 90.0 and toward.normalized().dot(outward) > 0.5:
			return true
	return false


## Qué va en cada vano de los bajos: portal, arco, escaparate, ventana, ciego o, en el
## patio, la escalera de servicio.
func _ground_program(edge: Dictionary, longest: bool) -> PackedStringArray:
	var bays: int = edge["bays"]
	var program: PackedStringArray = PackedStringArray()
	var role: String = edge["role"]
	var commercial: bool = bool(spec.get("comercios", not _worker))
	for bay: int in bays:
		var narrow: bool = float(edge["width"]) < 1.9
		if role == "calle":
			program.append("ciego" if narrow else ("escaparate" if commercial else "ventana"))
		else:
			program.append("ciego" if narrow else "ventana")
	if float(edge["length"]) < 8.0:
		return program
	var doors: int = maxi(1, roundi(float(edge["length"]) / PORTAL_EVERY))
	for k: int in doors:
		var bay: int = clampi(int(bays * (k + 0.5) / doors), 0, bays - 1)
		program[bay] = "portal" if role == "calle" else "escalera"
	if longest and bool(spec.get("arco", false)) and bays >= 3:
		var middle: int = int(bays / 2.0)
		if program[middle] == "portal":
			program[clampi(middle + 1, 0, bays - 1)] = "portal"
		program[middle] = "arco"
	return program


# --------------------------------------------------------------------------
# Fachadas
# --------------------------------------------------------------------------


func _facade(edge: Dictionary) -> void:
	var bays: int = edge["bays"]
	var role: String = edge["role"]
	var balcony_bays: Dictionary = {}
	if role == "calle" and bays >= 3:
		balcony_bays[int(bays / 2.0)] = true
		if bays >= 9:
			balcony_bays[int(bays / 4.0)] = true
			balcony_bays[int(bays * 3 / 4.0)] = true
	for bay: int in bays:
		var face: Dictionary = {
			"start": edge["start"] + edge["direction"] * (bay * float(edge["width"])),
			"direction": edge["direction"],
			"scale": float(edge["width"]) / BAY,
			"scale_y": _storey / STOREY,
		}
		var middle: Vector2 = face["start"] + edge["direction"] * (float(edge["width"]) * 0.5)
		var chunk: Array = _chunk_at(middle - edge["outward"] * 0.6)
		var kept: int = chunk[2]
		var program: String = edge["ground"][bay]
		if program == "escalera":
			_back_stairs(face, kept, bool(chunk[3]), edge)
			continue
		var below: Color = _ground_cell(face, program, edge)
		for f: int in range(1, kept):
			below = _upper_cell(face, f, below, edge, balcony_bays.has(bay), bay)
		_top(face, kept, bool(chunk[3]), below, edge)
		if role == "calle" and bay > 0 and bay % 2 == 0 and bays >= 4:
			_pilasters(face, kept)


## Los bajos de un vano. Devuelve el hollín que deja en la planta de encima.
func _ground_cell(face: Dictionary, program: String, edge: Dictionary) -> Color:
	var role: String = edge["role"]
	var base: Transform3D = _frame(face, 0.0)
	if role == "calle":
		assembly.put("imposta", _frame(face, GROUND), _tint)
	if role != "calle":
		# Patio y casa obrera: zócalo liso y una planta como las demás.
		assembly.put("zocalo_patio", base, _tint)
		var piece: String = "patio_ventana" if role == "patio" else "estuco_ventana"
		if program == "ciego":
			piece = "patio_ciego" if role == "patio" else "estuco_ciego"
		return _window_cell(face, 0, Color(_wear, 0.0, 0.0, 0.0), piece, edge)
	var tone: Color = _wall_tone()
	match program:
		"portal":
			assembly.put("bajo_portal", base, tone, Color(_wear, 0.0, 0.0, 0.0))
			assembly.put("puerta_e_" + _door_state(), base)
		"arco":
			assembly.put("bajo_arco", base, tone, Color(_wear, 0.0, 0.0, 0.0))
			assembly.put("reja_arco_abierta" if _rng.randf() < 0.5 else "reja_arco", base)
		"escaparate":
			var burnt: bool = _burnt(0)
			var state: String = "quemada" if burnt else _shop_state()
			var data: Color = Color(_wear, 0.0, 0.0, 0.0)
			if burnt:
				data = Color(_wear, 0.9, 1.6, 3.55)
			assembly.put("bajo_escaparate", base, tone, data)
			assembly.put("escaparate_" + state, base)
			assembly.put("tienda_interior", base)
			return Color(_wear, 0.75, 1.6, 3.55 - PLINTH) if burnt else Color(_wear, 0.0, 0.0, 0.0)
		"ventana":
			var burnt: bool = _burnt(0)
			var state: String = "quemada" if burnt else _window_state(0, edge["facing"])
			var data: Color = Color(_wear, 0.9, 1.6, 3.45) if burnt else Color(_wear, 0.0, 0.0, 0.0)
			assembly.put("bajo_ventana", base, tone, data)
			assembly.put("ventana_baja_" + _short_state(state), base)
			assembly.put(_room(burnt), _frame(face, PLINTH))
			return Color(_wear, 0.75, 1.6, 3.45 - PLINTH) if burnt else Color(_wear, 0.0, 0.0, 0.0)
		_:
			assembly.put("bajo_ciego", base, tone, Color(_wear, 0.0, 0.0, 0.0))
	return Color(_wear, 0.0, 0.0, 0.0)


## Una planta de un vano (de la 1 en adelante). Devuelve el hollín para la de encima.
func _upper_cell(
	face: Dictionary, f: int, below: Color, edge: Dictionary, balcony: bool, bay: int
) -> Color:
	var role: String = edge["role"]
	var narrow: bool = float(face["scale"]) * BAY < 1.9
	var piece: String = "patio_ventana" if role == "patio" else "estuco_ventana"
	if narrow:
		piece = "patio_ciego" if role == "patio" else "estuco_ciego"
	elif role == "calle":
		if balcony and f < floors - 1:
			piece = "estuco_balcon"
		elif f == 1:
			piece = "estuco_ventana_fronton" if bay % 2 == 0 else "estuco_ventana_cornisa"
		elif f == 2:
			piece = "estuco_ventana_cornisa"
	return _window_cell(face, f, below, piece, edge)


func _window_cell(face: Dictionary, f: int, below: Color, piece: String, edge: Dictionary) -> Color:
	var placement: Transform3D = _frame(face, PLINTH + f * _storey)
	var data: Color = _from_below(below, _storey)
	var tone: Color = _wall_tone()
	if piece.ends_with("ciego"):
		assembly.put(piece, placement, tone, data)
		return Color(_wear, 0.0, 0.0, 0.0)
	if f > 0 and _rng.randf() < [0.0, 0.006, 0.02, 0.08, 0.12][damage]:
		assembly.put("estuco_hueco", placement, tone, data)
		return Color(_wear, 0.0, 0.0, 0.0)
	var burnt: bool = _burnt(f)
	var opening: String = "balcon" if piece == "estuco_balcon" else "ventana"
	if piece == "patio_ventana":
		opening = "patio"
	var source: Vector2 = SOOT_SOURCES[opening]
	if burnt:
		data = Color(_wear, 0.9, source.x, source.y)
	assembly.put(piece, placement, tone, data)
	var state: String = "quemada" if burnt else _window_state(f, edge["facing"])
	match opening:
		"balcon":
			assembly.put("puerta_balcon_e_" + _short_state(state), placement)
			var fallen: bool = _rng.randf() < FALLEN_BALCONY[damage] * 0.6
			assembly.put(
				"balcon_balaustre_roto" if fallen else "balcon_balaustre", placement, _tint
			)
		"patio":
			assembly.put("ventana_patio_" + _short_state(state), placement)
		_:
			assembly.put("ventana_alta_" + state, placement)
	assembly.put(_room(burnt), placement)
	return Color(_wear, 0.75, source.x, source.y) if burnt else Color(_wear, 0.0, 0.0, 0.0)


## Lo que remata un vano: los muñones de una planta caída, o la cornisa (el alero en el
## patio y en la casa obrera).
func _top(face: Dictionary, kept: int, broken: bool, below: Color, edge: Dictionary) -> void:
	var top: float = PLINTH + kept * _storey
	var data: Color = _from_below(below, _storey)
	if broken:
		var stub: String = "estuco_roto_" + _pick(["a", "b", "c", "d"])
		assembly.put(stub, _frame(face, top), _wall_tone(), data)
		return
	if kept < floors:
		return
	var cornice: String = "cornisa" if edge["role"] == "calle" else "alero"
	var flat: Dictionary = face.duplicate()
	flat["scale_y"] = 1.0
	assembly.put(cornice, _frame(flat, top), _tint, data)


## La escalera de servicio del patio: la puerta abajo, las ventanas desfasadas media planta
## y el remate.
func _back_stairs(face: Dictionary, kept: int, broken: bool, edge: Dictionary) -> void:
	# La puerta llega al primer descansillo, a media planta (también si la planta es baja).
	var landing: float = PLINTH + _storey * 0.5
	var door: Dictionary = face.duplicate()
	door["scale_y"] = landing / BACK_HEIGHT
	var base: Transform3D = _frame(door, 0.0)
	assembly.put("patio_puerta", base, _tint)
	assembly.put("puerta_patio_" + _pick(["cerrada", "tapiada", "arrancada"]), base)
	var below: Color = Color(_wear, 0.0, 0.0, 0.0)
	var source: Vector2 = SOOT_SOURCES["escalera"]
	for k: int in maxi(0, kept - 1):
		var placement: Transform3D = _frame(face, landing + k * _storey)
		var burnt: bool = _burnt(k + 1)
		var data: Color = _from_below(below, _storey)
		if burnt:
			data = Color(_wear, 0.8, source.x, source.y)
		assembly.put("patio_escalera", placement, _wall_tone(), data)
		var state: String = "quemada" if burnt else _window_state(k + 1, edge["facing"])
		assembly.put("escalera_e_" + _stair_state(state), placement)
		assembly.put("escalera_e_interior", placement)
		below = Color(_wear, 0.6, source.x, source.y) if burnt else Color(_wear, 0.0, 0.0, 0.0)
	var top: float = PLINTH + kept * _storey
	if kept >= 1:
		var half: Dictionary = face.duplicate()
		assembly.put("patio_remate", _frame(half, top - _storey * 0.5), _tint)
	below.a -= _storey * 0.5
	_top(face, kept, broken, below, edge)


## Pilastras de orden gigante en la junta de dos vanos: basa abajo y capitel arriba.
func _pilasters(face: Dictionary, kept: int) -> void:
	var top: int = mini(kept, floors) - 1
	for f: int in range(1, top + 1):
		var piece: String = "pilastra"
		if f == 1:
			piece = "pilastra_basa"
		elif f == top:
			piece = "pilastra_capitel"
		var upright: Dictionary = face.duplicate()
		upright["scale"] = 1.0
		assembly.put(piece, _frame(upright, PLINTH + f * _storey), _tint)


## Las esquinas que sobresalen: sillares, la esquina de la imposta y la de la cornisa.
func _corners_pieces() -> void:
	var count: int = _edges.size()
	for i: int in count:
		var edge: Dictionary = _edges[i]
		var previous: Dictionary = _edges[(i - 1 + count) % count]
		var turn: float = (previous["direction"] as Vector2).cross(edge["direction"])
		var angle: float = (previous["direction"] as Vector2).angle_to(edge["direction"])
		if turn <= 0.0 or absf(angle) < deg_to_rad(25.0):
			continue
		var face: Dictionary = {
			"start": edge["start"],
			"direction": edge["direction"],
			"scale": 1.0,
			"scale_y": _storey / STOREY,
		}
		var chunk: Array = _chunk_at(edge["start"] + (edge["direction"] - edge["outward"]) * 0.6)
		var kept: int = chunk[2]
		var street: bool = edge["role"] == "calle" or previous["role"] == "calle"
		if street:
			assembly.put("esquina_bajos", _frame(face, 0.0), _tint)
			assembly.put("imposta_esquina", _frame(face, GROUND), _tint)
			for f: int in range(1, kept):
				assembly.put("esquina_planta", _frame(face, PLINTH + f * _storey), _tint)
		if not bool(chunk[3]) and kept == floors:
			var flat: Dictionary = face.duplicate()
			flat["scale_y"] = 1.0
			var cap: String = "cornisa_esquina" if street and not _worker else "alero_esquina"
			assembly.put(cap, _frame(flat, PLINTH + floors * _storey), _tint)


## Donde un trozo alto mira a uno más bajo, el corte con los forjados y las habitaciones.
func _cuts() -> void:
	for i: int in _chunks.size() - 1:
		var left: Array = _chunks[i]
		var right: Array = _chunks[i + 1]
		if int(left[2]) == int(right[2]):
			continue
		var high: Array = left if int(left[2]) > int(right[2]) else right
		var low: Array = right if high == left else left
		var at: float = float(left[1])
		var outward: Vector2 = _axis if high == left else -_axis
		var across: Vector2 = Vector2(-_axis.y, _axis.x)
		var line: PackedVector2Array = PackedVector2Array(
			[_axis * at - across * 5000.0, _axis * at + across * 5000.0]
		)
		for segment: PackedVector2Array in Geometry2D.intersect_polyline_with_polygon(
			line, _outline
		):
			_cut_face(segment, outward, int(low[2]), int(high[2]))


func _cut_face(segment: PackedVector2Array, outward: Vector2, low: int, high: int) -> void:
	var direction: Vector2 = Vector2(-outward.y, outward.x)
	var a: Vector2 = segment[0]
	var b: Vector2 = segment[segment.size() - 1]
	if (b - a).dot(direction) < 0.0:
		var swap: Vector2 = a
		a = b
		b = swap
	var length: float = a.distance_to(b)
	var bays: int = maxi(1, roundi(length / BAY))
	for bay: int in bays:
		var face: Dictionary = {
			"start": a + direction * (bay * length / bays),
			"direction": direction,
			"scale": length / bays / BAY,
			"scale_y": _storey / STOREY,
		}
		for f: int in range(low, high):
			assembly.put(
				_pick(["corte_e_a", "corte_e_b"]), _frame(face, PLINTH + f * _storey), _tint
			)
		assembly.put("corte_e_roto", _frame(face, PLINTH + high * _storey), _tint)


func _burnt(floor_index: int) -> bool:
	if floor_index >= int(_fire.x) and floor_index < int(_fire.y):
		return _rng.randf() < _fire.z
	return _rng.randf() < _fire_chance


func _shop_state() -> String:
	if damage >= 3:
		return _pick(["vacia", "quemada", "rota"])
	return _weighted({"intacta": 0.15, "rota": 0.35, "tapiada": 0.3, "vacia": 0.2})


func _room(burnt: bool) -> String:
	if burnt:
		return "habitacion_e_quemada"
	return "habitacion_e_" + _pick(["a", "b", "c"])


func _wall_tone() -> Color:
	var shade: float = 1.0 + _rng.randf_range(-0.025, 0.025)
	return Color(_tint.r * shade, _tint.g * shade, _tint.b * shade)


# --------------------------------------------------------------------------
# Cubiertas, escombros y colisión
# --------------------------------------------------------------------------


func _roofs(parent: Node3D) -> void:
	var roof: MeshBuffer = MeshBuffer.new()
	var rubble: MeshBuffer = MeshBuffer.new()
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Colision"
	parent.add_child(body)
	var cleaned: PackedVector2Array = CityGeometry.clean(spec["huella"])
	for chunk: Array in _chunks:
		for piece: PackedVector2Array in CityGeometry.slice(
			cleaned, _axis, float(chunk[0]), float(chunk[1])
		):
			var polygon: PackedVector2Array = piece.duplicate()
			polygon.reverse()
			polygon = _merge_short(polygon, 1.0)
			var top: float = PLINTH + int(chunk[2]) * _storey
			var intact: bool = not bool(chunk[3]) and int(chunk[2]) == floors
			if intact:
				_hip_roof(roof, polygon, top + CORNICE * 0.7)
			else:
				var triangles: PackedInt32Array = CityGeometry.triangulate(piece)
				rubble.add_cap(piece, triangles, top + 0.05, RUBBLE_COLOR.srgb_to_linear(), _origin)
				_rubble_on(parent, polygon, top)
			_collision(body, polygon, top + (CORNICE + ROOF_RISE * 0.5 if intact else 0.0))
	var snow: Material = load("res://assets/materials/nevado.tres")
	for entry: Array in [["Cubierta", roof], ["Escombro", rubble]]:
		var buffer: MeshBuffer = entry[1]
		if buffer.is_empty():
			continue
		var instance: MeshInstance3D = MeshInstance3D.new()
		instance.name = entry[0]
		instance.mesh = buffer.to_mesh(snow)
		parent.add_child(instance)


## Cubierta a cuatro aguas sobre cualquier planta: los faldones suben desde el borde hasta
## la misma planta metida hacia dentro, y arriba queda una azotea. Encima, las buhardillas
## de los faldones de la calle y las chimeneas junto a la cumbrera.
func _hip_roof(buffer: MeshBuffer, polygon: PackedVector2Array, eave: float) -> void:
	var inset: float = ROOF_INSET
	var inner: PackedVector2Array = PackedVector2Array()
	while inset > 0.4:
		inner = _inset(polygon, inset)
		if not inner.is_empty():
			break
		inset *= 0.7
	var color: Color = _roof_color.srgb_to_linear()
	if inner.is_empty():
		buffer.add_cap(polygon, CityGeometry.triangulate(polygon), eave, color, _origin)
		return
	var rise: float = ROOF_RISE * inset / ROOF_INSET
	var count: int = polygon.size()
	for i: int in count:
		var j: int = (i + 1) % count
		var edge: Vector2 = polygon[j] - polygon[i]
		var outward: Vector3 = Vector3(edge.y, 0.0, edge.x).normalized()
		var face: PackedVector3Array = PackedVector3Array(
			[
				_local(polygon[i], eave),
				_local(polygon[j], eave),
				_local(inner[j], eave + rise),
				_local(inner[i], eave + rise),
			]
		)
		buffer.add_face(face, outward + Vector3.UP, PackedColorArray([color]))
		if edge.length() > 7.0 and _street_side(polygon[i], polygon[j]):
			_dormers(polygon[i], polygon[j], inner[i], inner[j], eave, rise)
	buffer.add_cap(inner, CityGeometry.triangulate(inner), eave + rise, color, _origin)
	# Las chimeneas, repartidas por la cumbrera: una cada catorce metros, más o menos.
	var ring: PackedVector2Array = inner.duplicate()
	ring.append(inner[0])
	var perimeter: float = CityGeometry.length(ring)
	var stacks: int = clampi(roundi(perimeter / 28.0), 1, 8)
	for k: int in stacks:
		var along: float = perimeter * (k + _rng.randf_range(0.3, 0.7)) / stacks
		var spot: Vector2 = CityGeometry.point_along(ring, along).origin
		var placement: Transform3D = Transform3D(
			Basis(Vector3.UP, _rng.randf_range(-PI, PI)), _local(spot, eave + rise - 0.25)
		)
		assembly.put("chimenea", placement)


func _street_side(a: Vector2, b: Vector2) -> bool:
	for edge: Dictionary in _edges:
		var start: Vector2 = edge["start"]
		if start.distance_to(a) < 0.5 and edge["role"] == "calle":
			return (start + edge["direction"] * float(edge["length"])).distance_to(b) < 0.5
	return false


func _dormers(
	a: Vector2, b: Vector2, inner_a: Vector2, inner_b: Vector2, eave: float, rise: float
) -> void:
	var length: float = a.distance_to(b)
	var direction: Vector2 = (b - a) / length
	var count: int = int(length / 9.0)
	for k: int in count:
		var t: float = (k + 0.5) / count
		var outer: Vector2 = a.lerp(b, t)
		var inner: Vector2 = inner_a.lerp(inner_b, t)
		var spot: Vector2 = outer.lerp(inner, 0.42)
		var face: Dictionary = {"start": spot, "direction": direction, "scale": 1.0}
		assembly.put("buhardilla", _frame(face, eave + rise * 0.3))


## La planta metida [param distance] metros hacia dentro, con los mismos vértices (cada
## lado se corre en paralelo y las esquinas son sus cruces). Vacía si se da la vuelta.
func _inset(polygon: PackedVector2Array, distance: float) -> PackedVector2Array:
	var count: int = polygon.size()
	var result: PackedVector2Array = PackedVector2Array()
	for i: int in count:
		var previous: Vector2 = polygon[(i - 1 + count) % count]
		var here: Vector2 = polygon[i]
		var next: Vector2 = polygon[(i + 1) % count]
		var d1: Vector2 = (here - previous).normalized()
		var d2: Vector2 = (next - here).normalized()
		var n1: Vector2 = Vector2(-d1.y, d1.x)
		var n2: Vector2 = Vector2(-d2.y, d2.x)
		var cross: Variant = Geometry2D.line_intersects_line(
			previous + n1 * distance, d1, here + n2 * distance, d2
		)
		result.append(here + n2 * distance if cross == null else cross)
	for i: int in count:
		var outer: Vector2 = polygon[(i + 1) % count] - polygon[i]
		var inner: Vector2 = result[(i + 1) % count] - result[i]
		if inner.dot(outer) <= 0.0:
			return PackedVector2Array()
	if CityGeometry.signed_area(result) <= 1.0:
		return PackedVector2Array()
	return result


## Escombros sobre el forjado de un trozo hundido y al pie de su fachada.
func _rubble_on(parent: Node3D, polygon: PackedVector2Array, top: float) -> void:
	var center: Vector2 = CityGeometry.centroid(polygon)
	var area: float = absf(CityGeometry.signed_area(polygon))
	for k: int in clampi(roundi(area / 60.0), 1, 6):
		var corner: Vector2 = polygon[_rng.randi() % polygon.size()]
		var spot: Vector2 = center.lerp(corner, _rng.randf_range(0.1, 0.6))
		_heap(parent, _local(spot, top - 0.1), _rng.randf_range(0.6, 0.95), k)
	var away: Vector2 = (center - _bomb).normalized()
	var reach: float = CityGeometry.extent(polygon, away).y - center.dot(away)
	var lost: float = float(floors - int(_chunk_at(center)[2])) / floors
	for k: int in roundi(1.0 + lost * 3.0):
		var side: Vector2 = Vector2(-away.y, away.x) * _rng.randf_range(-reach, reach) * 0.6
		var spot: Vector2 = center + away * (reach + 2.0 + 2.0 * lost) + side
		_heap(parent, _local(spot, -0.1), _rng.randf_range(0.9, 1.3) + lost, 10 + k)


func _heap(parent: Node3D, position: Vector3, size: float, index: int) -> void:
	var model: PackedScene = load(RUBBLE_MODELS[_rng.randi() % RUBBLE_MODELS.size()])
	var heap: Node3D = model.instantiate()
	heap.name = "Escombros_%d_%d" % [parent.get_child_count(), index]
	heap.position = position
	heap.rotation.y = _rng.randf_range(-PI, PI)
	heap.scale = Vector3.ONE * size
	parent.add_child(heap)


## La colisión de un trozo: sus muros y su tapa.
func _collision(body: StaticBody3D, polygon: PackedVector2Array, top: float) -> void:
	var walls: MeshBuffer = MeshBuffer.new()
	var count: int = polygon.size()
	var tint: PackedColorArray = PackedColorArray([Color.WHITE])
	for i: int in count:
		var a: Vector2 = polygon[i]
		var b: Vector2 = polygon[(i + 1) % count]
		var edge: Vector2 = b - a
		walls.add_face(
			PackedVector3Array([_local(a, -1.0), _local(b, -1.0), _local(b, top), _local(a, top)]),
			Vector3(edge.y, 0.0, edge.x),
			tint
		)
	walls.add_cap(polygon, CityGeometry.triangulate(polygon), top, Color.WHITE, _origin)
	var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	shape.backface_collision = true
	shape.set_faces(walls.faces())
	var holder: CollisionShape3D = CollisionShape3D.new()
	holder.shape = shape
	body.add_child(holder)
