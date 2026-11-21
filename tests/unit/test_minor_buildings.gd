extends "res://tests/test_case.gd"
## Los edificios menores en los que se entra (F3-14, KitMinor): los del plano se montan con
## su modelo y su colisión, sus puertas quedan en su fachada (y abren hacia fuera), la
## hilera de trasteros mira al patio, el palomar lleva su escalera, y cómo está cerrada
## cada puerta y lo que hay en cada sitio salen siempre igual.

var _kit: BuildingKit
var _plan: CityPlan


func before_each() -> void:
	_kit = BuildingKit.new()
	if _plan == null:
		_plan = CityPlan.load_default()


func test_the_plaza_minor_buildings_are_built_whole() -> void:
	for id: String in ["PLZ-Q1", "PLZ-Q4", "PLZ-C1", "PLZ-P1", "PLZ-P3", "PLZ-T1", "AVM-Q1"]:
		var building: Dictionary = _building(id)
		assert_true(BuildingKit.supports_building(building), "%s: el kit lo monta" % id)
		var node: Node3D = _kit.build(_spec(building))
		var missing: PackedStringArray = node.get_meta(&"kit_faltan")
		assert_true(missing.is_empty(), "%s: faltan %s" % [id, ", ".join(missing)])
		assert_true(node.get_node_or_null("Colision") != null, "%s: con su colisión" % id)
		assert_true(not (node.get_meta(&"kit_botin", []) as Array).is_empty(), "%s: botín" % id)
		node.free()
	# Lo que no es de estos sigue siendo un volumen.
	assert_false(BuildingKit.supports_building(_building("IND-09C")), "la subestación no")
	assert_false(BuildingKit.supports_building(_building("BLQ-PLY")), "la torre de socorristas no")


func test_doors_sit_on_their_facade_and_open_outwards() -> void:
	var node: Node3D = _kit.build(_spec(_building("PLZ-Q1")))
	var doors: Array = node.get_meta(&"kit_puertas", [])
	assert_eq(doors.size(), 1, "el quiosco entero tiene su puerta")
	var center: Vector3 = _center(node)
	for door: Dictionary in doors:
		var hinge: Transform3D = door["bisagra"]
		var size: Vector3 = door["tamano"]
		var middle: Vector3 = hinge * Vector3(size.x * 0.5, 0.0, 0.0)
		var flat: Vector3 = Vector3(middle.x - center.x, 0.0, middle.z - center.z)
		assert_true(flat.length() > 1.3, "en la fachada, no dentro (%.2f m)" % flat.length())
		var opening: Vector3 = hinge.basis.z
		assert_true(opening.dot(flat.normalized()) > 0.5, "se abre hacia fuera")
		assert_almost(hinge.basis.x.length(), 1.0, 0.001, "sin estirar")
	node.free()
	var wrecked: Node3D = _kit.build(_spec(_building("AVM-Q1")))
	assert_true((wrecked.get_meta(&"kit_puertas", []) as Array).is_empty(), "al roto le falta")
	wrecked.free()


func test_the_row_of_sheds_faces_the_courtyard() -> void:
	var building: Dictionary = _building("PLZ-P2")
	var node: Node3D = _kit.build(_spec(building))
	var doors: Array = node.get_meta(&"kit_puertas", [])
	var units: int = roundi(30.0 / KitMinor.SIZES["trastero"].x)
	assert_true(doors.size() >= units - 4, "casi todas las casetas con su puerta")
	var courtyard: Vector2 = _nearest_courtyard(building)
	var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	for door: Dictionary in doors:
		var out: Vector3 = (door["bisagra"] as Transform3D).basis.z
		var plan_out: Vector2 = Vector2(out.x, -out.z)
		assert_true(plan_out.dot((courtyard - center).normalized()) > 0.5, "hacia el patio")
	node.free()


func test_the_dovecote_has_its_ladder() -> void:
	var node: Node3D = _kit.build(_spec(_building("PLZ-P3")))
	var ladders: Array = node.get_meta(&"kit_trepables", [])
	assert_eq(ladders.size(), 1)
	var foot: Transform3D = ladders[0]["pie"]
	assert_almost(foot.origin.y, 0.0, 0.01, "de la nieve")
	assert_almost((ladders[0]["tamano"] as Vector3).y, 3.1, 0.01, "a la plataforma")
	var landing: Vector3 = foot * Vector3(0.0, 3.1, -0.55)
	var center: Vector3 = _center(node)
	var from_center: float = Vector2(landing.x - center.x, landing.z - center.z).length()
	assert_true(from_center < 2.2, "arriba se sale a la plataforma (%.2f m)" % from_center)
	assert_eq((node.get_meta(&"kit_puertas", []) as Array).size(), 1, "y el altillo, su puerta")
	node.free()


func test_locks_and_loot_are_always_the_same() -> void:
	var weights: Dictionary = KitMinor.DOORS["trastero"][0]["cierres"]
	var counts: Dictionary = {}
	for index: int in 200:
		var id: String = "PLZ-P1_puerta_%d" % index
		var first: Dictionary = SurfaceSites.initial_state(id, weights)
		assert_eq(first, SurfaceSites.initial_state(id, weights), "la misma puerta, igual")
		counts[first["cierre"]] = int(counts.get(first["cierre"], 0)) + 1
	assert_true(int(counts.get("candado", 0)) > 80, "casi todas con candado")
	assert_true(counts.has("") and counts.has("atrancada"), "y alguna abierta o atrancada")
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	var found: Dictionary = {}
	for index: int in 300:
		rng.seed = index
		var item: String = SurfaceSites.roll_loot("quiosco", rng)
		if not item.is_empty():
			found[item] = true
			assert_true(ItemState.load_data(StringName(item)) != null, "%s existe" % item)
	assert_true(found.has("cerillas") and found.has("papeles"), "lo de un quiosco")
	for kind: String in SurfaceSites.LOOT:
		for item: String in SurfaceSites.LOOT[kind]:
			assert_true(ItemState.load_data(StringName(item)) != null, "%s (%s)" % [item, kind])


func test_dogs_go_in_only_through_open_doors() -> void:
	# Una hilera de trasteros del primer patio y una tienda de la evacuación.
	var shed_row: Dictionary = _building("PLZ-P1")
	var shed: Node3D = _kit.build(_spec(shed_row))
	var nav: CityNav = CityNav.empty(Rect2i(Vector2i(360, 420), Vector2i(60, 50)))
	nav.block_polygon(CityPlan.ring(shed_row["huella"][0]))
	var interiors: Array = shed.get_meta(&"kit_interiores", [])
	assert_false(interiors.is_empty(), "las casetas tienen interior")
	var passage: Dictionary = {}
	for each: Dictionary in shed.get_meta(&"kit_pasos", []):
		if not String(each["puerta"]).is_empty():
			passage = each
			break
	assert_false(passage.is_empty(), "y el paso de su puerta")
	var approach: PackedVector2Array = passage["llegada"]
	var inside: Vector2 = approach[0]
	var outward: Vector2 = (approach[approach.size() - 1] - approach[0]).normalized()
	var outside: Vector2 = approach[approach.size() - 1] + outward * 2.0
	var shut: SurfaceDoor = SurfaceDoor.new()
	shut.initial_lock = SurfaceDoor.PADLOCK
	SurfaceSites.carve_model(nav, shed, {passage["puerta"]: shut})
	assert_true(nav.is_walkable(inside), "dentro se pisa")
	assert_false(_reaches(nav, outside, inside), "con la puerta cerrada, no se entra")
	nav.set_points(passage["hueco"], false)
	assert_true(_reaches(nav, outside, inside), "abierta, se entra")
	shut.free()
	shed.free()
	var tent_spec: Dictionary = _building("PLZ-C1")
	var tent: Node3D = _kit.build(_spec(tent_spec))
	var tent_nav: CityNav = CityNav.empty(Rect2i(Vector2i(195, 75), Vector2i(40, 35)))
	tent_nav.block_polygon(CityPlan.ring(tent_spec["huella"][0]))
	SurfaceSites.carve_model(tent_nav, tent, {})
	var middle: Vector2 = Vector2(tent_spec["centro"][0], tent_spec["centro"][1])
	assert_true(tent_nav.is_walkable(middle), "dentro de la tienda se pisa")
	assert_true(_reaches(tent_nav, middle + Vector2(0.0, -12.0), middle), "y se entra")
	tent.free()


## Hay camino de [param from] a [param to] y acaba en [param to].
func _reaches(nav: CityNav, from: Vector2, to: Vector2) -> bool:
	var route: PackedVector2Array = nav.path(from, to)
	return not route.is_empty() and route[route.size() - 1].distance_to(to) < 0.8


func _building(id: String) -> Dictionary:
	for building: Dictionary in _plan.data["edificios"]:
		if building["id"] == id:
			return building
	return {}


func _spec(building: Dictionary) -> Dictionary:
	var courtyards: PackedVector2Array = PackedVector2Array()
	for courtyard: Dictionary in _plan.data["patios"]:
		courtyards.append(CityGeometry.centroid(CityPlan.ring(courtyard["forma"][0])))
	var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	return {
		"tipo": building["tipo"],
		"clave": building["id"],
		"nombre": building.get("nombre", ""),
		"huella": CityPlan.ring(building["huella"][0]),
		"centro": center,
		"origen": center,
		"pisos": int(building["pisos"]),
		"dano": int(building["dano"]),
		"incendio": building.get("incendio", "no"),
		"patios": courtyards,
	}


func _nearest_courtyard(building: Dictionary) -> Vector2:
	var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	var nearest: Vector2 = Vector2.INF
	for courtyard: Dictionary in _plan.data["patios"]:
		var middle: Vector2 = CityGeometry.centroid(CityPlan.ring(courtyard["forma"][0]))
		if middle.distance_to(center) < nearest.distance_to(center):
			nearest = middle
	return nearest


## El centro de la huella en el marco del nodo (el origen de la ficha es su centro).
func _center(_node: Node3D) -> Vector3:
	return Vector3.ZERO
