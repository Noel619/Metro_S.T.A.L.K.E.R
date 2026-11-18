extends "res://tests/test_case.gd"
## La maqueta construida de verdad, con su física: lo que se pisa coincide con el plano.

## La ciudad se levanta una vez para todos los tests (tarda un par de segundos).
static var _city: City


func before_each() -> void:
	if _city == null:
		_city = City.new()
		_city.name = "CiudadDePrueba"
		get_tree().root.add_child(_city)
		_city.build(CityPlan.load_default())
		await get_tree().physics_frame
		await get_tree().physics_frame


func test_every_sector_and_building_is_built() -> void:
	var sectors: int = 0
	for child: Node in _city.get_children():
		if String(child.name).begins_with("Sector_"):
			sectors += 1
			assert_true(child.has_node("Lejos"), "%s sin versión lejana" % child.name)
	assert_eq(sectors, 48)
	assert_eq(_city.buildings_by_id.size(), _city.plan.data["edificios"].size())
	assert_eq(int(_city.stats["vehiculos"]), _city.plan.data["vehiculos"].size())
	assert_eq(int(_city.stats["arboles"]), _city.plan.data["arboles"].size())


func test_vehicles_are_their_models() -> void:
	# Cada vehículo es su modelo a la medida del plano (ninguno queda como caja), los
	# quemados tienen el suyo, los tranvías volcados yacen de costado y los barcos del río
	# están en el hielo o en el agua.
	var placed: Dictionary = {}
	for by_model: Dictionary in _city.props.vehicles().values():
		for model: String in by_model:
			var list: Array = placed.get(model, [])
			for entry: Array in by_model[model]:
				list.append(entry[0])
			placed[model] = list
	assert_false(placed.has("caja"), "vehículos sin modelo")
	for model: String in [
		"autobus", "autobus_quemado", "trolebus", "tranvia_quemado", "blindado", "barco"
	]:
		assert_true(placed.has(model), "falta %s" % model)
	# El tren quemado de la vía 1: coches de 24 m.
	var coach: Transform3D = placed["coche_tren_quemado"][0]
	var mesh: Mesh = null
	for node: Node in _city.find_children("CocheTrenQuemado", "MultiMeshInstance3D", true, false):
		mesh = (node as MultiMeshInstance3D).multimesh.mesh
	assert_almost(mesh.get_aabb().size.x * coach.basis.get_scale().x, 24.0, 0.6, "largo")
	var lying: int = 0
	for tram: Transform3D in placed["tranvia"]:
		if absf(tram.basis.y.normalized().y) < 0.2:
			lying += 1
	assert_eq(lying, 2, "tranvías de costado")
	# Las barcazas, metidas en el hielo o en el agua de los desagües del puerto.
	var ice: float = float(_city.plan.river["hielo"])
	var water: float = float(_city.plan.river["agua"])
	for barge: Transform3D in placed["barcaza"]:
		var y: float = barge.origin.y
		assert_true(absf(y - ice) < 0.05 or absf(y - water) < 0.05, "barcaza a %.2f" % y)


func test_ground_collision_follows_the_relief() -> void:
	# La glorieta (llana), la cuesta de la loma (norte-sur: delataría un relieve al revés) y
	# el hielo del río. En el centro de la glorieta está el Monumento al Minero.
	for point: Vector2 in [Vector2(395.0, 345.0), Vector2(1000.0, 830.0), Vector2(700.0, 706.0)]:
		var hit: Dictionary = _ray_down(point, [])
		assert_false(hit.is_empty(), "nada bajo %s" % point)
		# En el río se pisa el hielo: el relieve es su lecho, debajo.
		var expected: float = _city.plan.height_at(point)
		if _city.plan.is_on_river(point):
			expected = maxf(expected, float(_city.plan.river["hielo"]))
		if not hit.is_empty():
			assert_almost(hit["position"].y, expected, 0.35, "en %s" % point)


func test_the_river_has_open_water_and_ice() -> void:
	# El agua abierta no se pisa (se cae al lecho) y el hielo sí, a su nivel; el remolcador
	# flota en el agua templada de la central.
	var river: Dictionary = _city.plan.river
	var level: float = float(river["agua"])
	assert_true(int(_city.stats["rio"]["triangulos_agua"]) > 2000, "triángulos de agua")
	assert_true(int(_city.stats["rio"]["placas"]) > 1000, "placas de hielo")
	var flat: Array = river["superficie"]["puntos"]
	var triangles: Array = river["superficie"]["triangulos"]
	var slush: Array = river["superficie"]["orilla"]
	var tested: int = 0
	var fell: int = 0
	for t: int in range(0, triangles.size(), 3 * 41):
		var center: Vector2 = Vector2.ZERO
		var edge: float = 0.0
		for k: int in 3:
			var v: int = int(triangles[t + k])
			center += Vector2(flat[v * 2], flat[v * 2 + 1]) / 3.0
			edge += float(slush[v])
		if edge > 0.0:
			continue
		tested += 1
		var hit: Dictionary = _ray_down(center, [])
		if not hit.is_empty() and hit["position"].y < level - 0.3:
			fell += 1
	assert_true(tested > 20, "puntos de agua: %d" % tested)
	assert_true(fell > tested * 0.85, "se cae al agua en %d de %d" % [fell, tested])
	var on_ice: Dictionary = _ray_down(Vector2(700.0, 706.0), [])
	assert_almost(on_ice["position"].y, float(river["hielo"]), 0.05, "el hielo de orilla")
	for by_model: Dictionary in _city.props.vehicles().values():
		for entry: Array in by_model.get("remolcador", []):
			assert_almost((entry[0] as Transform3D).origin.y, level, 0.05, "el remolcador flota")


func test_buildings_are_solid_and_known() -> void:
	var tested: int = 0
	for building: Dictionary in _city.plan.data["edificios"]:
		if int(building["dano"]) != 1 or building["tipo"] not in ["bloque9", "jrushchovka"]:
			continue
		var center: Vector2 = CityGeometry.centroid(CityPlan.ring(building["huella"][0]))
		var hit: Dictionary = _ray_down(center, [])
		assert_eq(_city.building_of(hit.get("collider")).get("id"), building["id"])
		var roof: float = float(building["cota"]) + float(building["altura"])
		assert_almost(hit["position"].y, roof, 0.05, "cubierta de %s" % building["id"])
		tested += 1
	assert_true(tested >= 5, "hay bloques intactos que probar")


func test_kit_buildings_replace_their_volumes_up_close() -> void:
	var expected: int = 0
	for building: Dictionary in _city.plan.data["edificios"]:
		if BuildingKit.supports_building(building):
			expected += 1
	assert_true(expected > 100, "el kit monta la mayoría de las viviendas")
	assert_eq(int(_city.stats["kit_edificios"]), expected)
	# Un bloque: en la versión detallada de su sector se ve su volumen hasta que se está cerca;
	# entonces, su modelo, a su cota. Sus piezas proyectan sombra solo de muy cerca: a media
	# distancia la proyecta su volumen (metido hacia dentro).
	var block: Dictionary = _first_kit_building("bloque9")
	var model: Node3D = _model_of(block)
	assert_true(model != null and not (model is MeshInstance3D), "el bloque es su modelo")
	if model == null:
		return
	assert_almost(model.position.y, float(block["cota"]), 0.001)
	var holder: Node = model.get_parent()
	var volume: GeometryInstance3D = holder.get_node("%s_Volumen" % block["id"])
	var shade: GeometryInstance3D = holder.get_node("%s_Sombra" % block["id"])
	assert_eq(volume.get_node(volume.visibility_parent), holder.get_parent().get_node("Lejos"))
	assert_almost(volume.visibility_range_begin, _city.kit_distance, 0.001)
	assert_eq(shade.get_node(shade.visibility_parent), volume)
	assert_eq(shade.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY)
	assert_almost(shade.visibility_range_begin, _city.kit_shadow_distance, 0.001)
	var near: int = 0
	var middle: int = 0
	for node: Node in model.find_children("*", "GeometryInstance3D", true, false):
		var piece: GeometryInstance3D = node
		var parent: Node = piece.get_node_or_null(piece.visibility_parent)
		if String(piece.name).ends_with("_Medio"):
			middle += 1
			assert_eq(parent, volume, "%s, a media distancia" % piece.name)
			assert_eq(piece.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
		elif piece.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			assert_eq(parent, volume, "%s (sin sombra), de cerca y a media distancia" % piece.name)
		else:
			near += 1
			assert_eq(parent, shade, "%s, con su sombra de cerca" % piece.name)
	assert_true(near > 5 and near == middle, "cada pieza con sombra tiene su copia sin ella")
	# Un hito: de lejos se ve su volumen, solo, y de cerca, su modelo.
	var landmark: Dictionary = _city.buildings_by_id["ZC-01"]
	var ruin: Node3D = _model_of(landmark)
	var landmark_volume: GeometryInstance3D = ruin.get_parent().get_node("ZC-01_Volumen")
	assert_true(landmark_volume.visibility_parent.is_empty(), "el hito se ve de lejos")
	assert_almost(landmark_volume.visibility_range_begin, _city.kit_distance, 0.001)
	for piece: Node in ruin.find_children("*", "GeometryInstance3D", true, false):
		var parent_path: NodePath = (piece as GeometryInstance3D).visibility_parent
		assert_eq(
			piece.get_node_or_null(parent_path),
			landmark_volume,
			"%s cambia con el hito" % piece.name
		)


func test_plinths_face_outward() -> void:
	# El zócalo de una casa en L, en ladera: un lado por cara, y todas miran hacia fuera de la
	# huella, también las dos del rincón (que miran hacia el centro de la ficha).
	var kit: CityKit = CityKit.new(_city.plan)
	var ring: Array = [[0, 0], [20, 0], [20, 8], [8, 8], [8, 20], [0, 20], [0, 0]]
	var anchor: Vector2 = Vector2(6.0, 6.0)
	var building: Dictionary = {
		"centro": [anchor.x, anchor.y], "huella": [ring], "cota": 5.0, "cota_min": 4.0
	}
	var mesh: MeshBuffer = kit.plinth(building)
	assert_eq(mesh.triangle_count(), 12, "dos triángulos por lado")
	var outline: PackedVector2Array = CityPlan.ring(ring)
	for t: int in range(0, mesh.indices.size(), 3):
		var middle: Vector3 = Vector3.ZERO
		for k: int in 3:
			middle += mesh.vertices[mesh.indices[t + k]] / 3.0
		var normal: Vector3 = mesh.normals[mesh.indices[t]]
		var probe: Vector2 = anchor + Vector2(middle.x + normal.x, -middle.z - normal.z)
		assert_false(
			Geometry2D.is_point_in_polygon(probe, outline), "cara %d hacia fuera" % (t / 3)
		)
		assert_almost(normal.y, 0.0, 0.001)
	# Bajo la cota y hasta 40 cm por debajo del punto más bajo.
	var lowest: float = INF
	for vertex: Vector3 in mesh.vertices:
		lowest = minf(lowest, vertex.y)
	assert_almost(lowest, -1.0 - CityKit.PLINTH_FOOT, 0.001)
	assert_true(kit.plinth({"cota": 5.0, "cota_min": 4.95}).is_empty(), "en llano, sin zócalo")


func test_singular_buildings_collide_as_their_model() -> void:
	# En el vestíbulo se entra: en medio de la sala se pisa su suelo, tres escalones por
	# encima de la acera (su volumen era un bloque macizo).
	var vestibule: Dictionary = _city.buildings_by_id["PLZ-06"]
	var hall: Vector2 = Vector2(326.0, 299.5)
	var ground: float = float(vestibule["cota"])
	var hit: Dictionary = _ray(hall, ground + 5.0, ground - 30.0)
	assert_eq(_city.building_of(hit.get("collider")).get("id"), "PLZ-06")
	assert_true(not hit.is_empty() and hit["position"].y > ground + 0.3, "el suelo de la sala")
	assert_true(not hit.is_empty() and hit["position"].y < ground + 3.0, "bajo la cúpula")


func test_metro_vestibule_goes_below_the_street() -> void:
	# El terreno no tapa el foso de las escaleras: por algún punto del hueco se ve (y se
	# pisa) lo que hay bajo la calle. Si el relieve siguiera ahí, todo rayo pararía en él.
	var vestibule: Dictionary = _city.buildings_by_id["PLZ-06"]
	var holes: PackedVector2Array = _model_of(vestibule).get_meta(&"kit_huecos")
	assert_true(holes.size() >= 3, "el vestíbulo dice dónde no va el terreno")
	var box: Rect2 = Rect2(holes[0], Vector2.ZERO)
	for point: Vector2 in holes:
		box = box.expand(point)
	var ground: float = float(vestibule["cota"])
	var lowest: float = INF
	for j: int in int(box.size.y):
		for i: int in int(box.size.x):
			var point: Vector2 = box.position + Vector2(i + 0.5, j + 0.5)
			var hit: Dictionary = _ray(point, ground + 1.5, ground - 30.0)
			if not hit.is_empty():
				lowest = minf(lowest, hit["position"].y)
	assert_true(lowest < ground - 2.0, "se baja bajo la calle (lo más bajo: %.2f)" % lowest)


func test_a_walker_climbs_into_the_soviets_breach() -> void:
	# El escombro del boquete de la fachada noreste de la Casa de los Sóviets sale hasta la
	# calle: por él se sube al boquete y se baja por dentro al cuarto que quedó detrás. Si la
	# colisión de la fachada no estuviera abierta, se quedaría arriba, contra el muro (a 9 m).
	var building: Dictionary = _city.buildings_by_id["CEN-SOV"]
	var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	# El marco de su receta: u a lo largo de la fachada principal y v hacia el noreste.
	var turn: float = deg_to_rad(-42.0)
	var street: Vector2 = center + Vector2(-8.0, 46.0).rotated(turn)
	var inside: Vector2 = center + Vector2(-8.0, 22.0).rotated(turn)
	var ground: float = float(building["cota"])
	var end: float = await _walk(street, inside, 35.0)
	assert_true(end > ground + 2.5 and end < ground + 6.0, "dentro, a %.1f m" % (end - ground))


func test_bridge_deck_is_walkable() -> void:
	var point: Vector2 = _city.plan.axis_point(455.0)
	assert_true(_city.plan.height_at(point) < -5.0, "bajo el puente está el hielo")
	var hit: Dictionary = _ray_down(point, [])
	assert_true(hit["position"].y > -1.0, "el tablero está a la altura de la calle")
	assert_almost(hit["position"].y, _city.surface_height(point), 0.3)


func test_walker_lands_on_the_ground() -> void:
	var walker: MockupWalker = MockupWalker.new()
	get_tree().root.add_child(walker)
	var point: Vector2 = Vector2(358.0, 302.0)
	var ground: float = _city.plan.height_at(point)
	walker.global_position = CityPlan.to_world(point, ground + 3.0)
	for _i: int in 90:
		await get_tree().physics_frame
	assert_true(walker.is_on_floor(), "de pie en el suelo")
	assert_almost(walker.global_position.y, ground, 0.25)
	walker.queue_free()


func test_transit_is_built_and_cuts_the_terrain() -> void:
	var stats: Dictionary = _city.stats["transito"]
	assert_true(int(stats["triangulos"]) > 100000, "la red de tránsito se levanta entera")
	assert_eq(int(stats["detalles"]), _detail_count())
	# En medio de la calzada de la avenida, lo que se pisa va por debajo del relieve: la
	# colisión del relieve está rebajada y se pisa el asfalto.
	var roadway: Vector2 = _city.plan.axis_point(150.0, 18.0)
	var hit: Dictionary = _ray_down(roadway, [])
	var level: float = float(_city.plan.transit["niveles"]["calzada"])
	assert_almost(hit["position"].y, _city.plan.transit_base_at(roadway) + level, 0.02)
	assert_true(hit["position"].y < _city.plan.height_at(roadway) - 0.1, "bajo el relieve")


func test_surfaces_sit_at_their_level() -> void:
	var plan: CityPlan = _city.plan
	var levels: Dictionary = plan.transit["niveles"]
	# La cama del tranvía en medio de la avenida (a la altura de la calzada), su mediana, su
	# calzada, su acera y el tablero del puente.
	var places: Array = [
		[plan.axis_point(150.0, 0.0), levels["via_tranvia"]],
		[plan.axis_point(150.0, 5.0), levels["isleta"]],
		[plan.axis_point(150.0, -20.0), levels["calzada"]],
		[plan.axis_point(150.0, 32.0), levels["losas"]],
	]
	for place: Array in places:
		var point: Vector2 = place[0]
		var hit: Dictionary = _ray_down(point, [])
		assert_almost(
			hit["position"].y, plan.transit_base_at(point) + float(place[1]), 0.02, "en %s" % point
		)
	var deck: Vector2 = plan.axis_point(455.0, 5.0)
	var rule: Dictionary = plan.transit["puente"]["regla"]
	var expected: float = lerpf(
		float(rule["z0"]),
		float(rule["z1"]),
		clampf((deck.y - float(rule["o"][1])) / float(rule["largo"]), 0.0, 1.0)
	)
	assert_almost(_ray_down(deck, [])["position"].y, expected + float(levels["calzada"]), 0.02)


func test_escalinata_steps_are_level_and_climb() -> void:
	var plan: CityPlan = _city.plan
	var stairs: Dictionary = plan.transit["escaleras"][0]
	var treads: Array = stairs["pisadas"]
	var previous: float = -INF
	for tread: Array in treads:
		# Justo pasada la arista (la rampa de colisión del peldaño de arriba no llega).
		var front: float = float(tread[0]) + 0.04
		if front < 650.0:
			continue
		for t: float in [-15.0, 0.0, 15.0]:
			var hit: Dictionary = _ray_down(plan.axis_point(front, t), [])
			assert_almost(hit["position"].y, float(tread[2]), 0.01, "peldaño en s=%.1f" % front)
		assert_true(float(tread[2]) > previous, "cada peldaño, más alto")
		previous = float(tread[2])


func test_a_walker_climbs_a_curb_and_a_flight() -> void:
	var plan: CityPlan = _city.plan
	# De la calzada de la avenida a su acera, cruzando el bordillo.
	var start: Vector2 = plan.axis_point(150.0, 24.0)
	var end: float = await _walk(start, plan.axis_point(150.0, 32.0), 7.0)
	assert_almost(end, plan.transit_base_at(plan.axis_point(150.0, 32.0)) + 0.03, 0.12)
	# Y un tramo de la Escalinata hacia arriba.
	var bottom: Vector2 = plan.axis_point(652.0, 0.0)
	var climbed: float = await _walk(bottom, plan.axis_point(664.0, 0.0), 12.0)
	assert_true(climbed > _city.surface_height(bottom) + 1.2, "sube un tramo entero")


func test_tracks_are_built() -> void:
	var stats: Dictionary = _city.stats["transito"]
	assert_true(int(stats["traviesas"]) > 11000, "traviesas: %d" % int(stats["traviesas"]))
	assert_true(float(stats["via_m"]) > 7000.0, "vía sobre balasto: %.0f m" % stats["via_m"])
	assert_true(float(stats["a_ras_m"]) > 5000.0, "vía a ras: %.0f m" % stats["a_ras_m"])
	# Cada desvío y cada tope, una vez (en el sector en el que cae).
	var railway: Dictionary = _city.plan.transit["ferrocarril"]
	assert_eq(int(stats["desvios"]), railway["desvios"].size())
	assert_eq(int(stats["topes"]), railway["topes"].size())


func test_a_buffer_stop_stops_a_walker() -> void:
	# Por la vía hacia el tope: el madero de choque no deja pasar.
	var stop: Dictionary = _city.plan.transit["ferrocarril"]["topes"][0]
	var heading: float = deg_to_rad(float(stop["rumbo"]))
	var forward: Vector2 = Vector2(cos(heading), sin(heading))
	var base: Vector2 = Vector2(stop["pos"][0], stop["pos"][1])
	var height: float = float(stop["z"]) + 1.0
	var space: PhysicsDirectSpaceState3D = _city.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		CityPlan.to_world(base - forward * 6.0, height),
		CityPlan.to_world(base + forward * 1.0, height)
	)
	var hit: Dictionary = space.intersect_ray(query)
	assert_false(hit.is_empty(), "nada choca contra el tope")
	if not hit.is_empty():
		var reached: Vector2 = CityPlan.to_plan(hit["position"])
		assert_almost(reached.distance_to(base), 0.2, 0.3, "choca en el madero")


func test_sinkholes_open_the_street() -> void:
	# En el centro de cada socavón, lo primero que se pisa es su fondo (ni la calle ni el
	# terreno de debajo, que se rebaja bajo la malla).
	var holes: Array = _city.plan.transit["socavones"]
	assert_eq(int(_city.stats["transito"]["socavones"]), holes.size())
	assert_true(holes.size() >= 10, "socavones: %d" % holes.size())
	for hole: Dictionary in holes:
		var group: Dictionary = _city.plan.transit["grupos"][int(hole["grupo"])]
		var heights: Array = group["z"]
		var rim: int = hole["contorno"].size() / 2
		var street: float = 0.0
		for v: int in rim:
			street += float(heights[v])
		street = street / rim + 0.42
		var center: Vector2 = Vector2(hole["centro"][0], hole["centro"][1])
		var hit: Dictionary = _ray_down(center, [])
		assert_false(hit.is_empty(), "%s: nada en el centro" % hole["id"])
		if hit.is_empty():
			continue
		var floor_z: float = float(heights[heights.size() - 1])
		var depth: float = street - hit["position"].y
		assert_true(depth > 0.85 * float(hole["hondo"]), "%s: baja %.2f m" % [hole["id"], depth])
		assert_true(hit["position"].y < floor_z + 0.6, "%s: el fondo queda tapado" % hole["id"])
	# Las grietas y los carriles del tranvía que cuelgan sobre el socavón de la avenida.
	assert_true(int(_city.stats["transito"]["grietas"]) > 1500, "grietas")
	assert_true(float(_city.stats["transito"]["colgando_m"]) > 2.0, "carriles colgando")


func test_overhead_lines_hang_over_the_streets() -> void:
	# El tendido del tranvía y del trolebús: los postes (en pie, torcidos, caídos o
	# partidos) y los cables. Los hilos que siguen tensos van a unos 5,8 m de lo que se pisa;
	# los rotos o caídos llegan al suelo.
	var lines: Array = _city.plan.transit["tendido"]["lineas"]
	assert_true(int(_city.stats["transito"]["cables"]) > 1000, "tramos de cable")
	var poles: int = 0
	for node: Node in _city.find_children("PosteTendido*", "MultiMeshInstance3D", true, false):
		poles += (node as MultiMeshInstance3D).multimesh.instance_count
	assert_true(poles > 150, "postes: %d" % poles)
	var tight: int = 0
	var down: int = 0
	for line: Dictionary in lines:
		if not is_equal_approx(float(line["grosor"]), 0.028):
			continue
		var lowest: float = INF
		for point: Array in line["puntos"]:
			var ground: float = _city.surface_height(Vector2(point[0], point[1]))
			lowest = minf(lowest, float(point[2]) - ground)
		if lowest > 5.0:
			tight += 1
		elif lowest < 0.3:
			down += 1
	assert_true(tight > 40, "hilos tensos: %d" % tight)
	assert_true(down > 40, "hilos en el suelo: %d" % down)


func test_broken_pavement_plates_are_solid() -> void:
	# Las placas del firme roto se pisan: en el centro de cada una de las primeras, lo
	# primero que se toca está entre lo más bajo y lo más alto de su cara de arriba.
	var stats: Dictionary = _city.stats["transito"]
	assert_true(int(stats["placas"]) > 10000, "placas: %d" % int(stats["placas"]))
	assert_true(int(stats["restos"]) > 5000, "restos: %d" % int(stats["restos"]))
	var zone: Dictionary = _city.plan.transit["placas"][0]
	var flat: Array = zone["puntos"]
	var heights: Array = zone["z"]
	var first: int = 0
	for n: int in mini(6, zone["caras"].size()):
		var count: int = int(zone["caras"][n])
		var center: Vector2 = Vector2.ZERO
		var low: float = INF
		var high: float = -INF
		for k: int in range(first, first + count):
			center += Vector2(flat[k * 2], flat[k * 2 + 1])
			low = minf(low, float(heights[k]))
			high = maxf(high, float(heights[k]))
		center /= count
		first += count
		var hit: Dictionary = _ray_down(center, [])
		assert_false(hit.is_empty(), "nada bajo la placa %d" % n)
		if not hit.is_empty():
			var y: float = hit["position"].y
			assert_true(
				y > low - 0.02 and y < high + 0.02,
				"placa %d a %.2f (%.2f-%.2f)" % [n, y, low, high]
			)


func test_a_walker_falls_into_a_sinkhole() -> void:
	for hole: Dictionary in _city.plan.transit["socavones"]:
		if String(hole["id"]) != "agua_juventud":
			continue
		var center: Vector2 = Vector2(hole["centro"][0], hole["centro"][1])
		var start: Vector2 = center + Vector2(0.0, -6.5)
		var street: float = _city.surface_height(start)
		var ended: float = await _walk(start, center, 10.0)
		assert_true(ended < street - 1.2, "acaba a %.2f m (la calle, a %.2f)" % [ended, street])
		return
	assert_true(false, "sin el socavón de la calle de la Juventud")


func test_platforms_and_ballast_sit_at_the_rail_level() -> void:
	var rails: Dictionary = _city.plan.transit["ferrocarril"]
	var formation: float = _formation("principal", Vector2(200.0, 34.0))
	# El andén isla al sur de la principal: 1,10 m sobre lo alto del carril.
	var platform: Dictionary = _ray_down(Vector2(200.0, 28.0), [])
	var expected: float = formation + float(rails["carril"]) + float(rails["anden"])
	assert_almost(platform["position"].y, expected, 0.01)
	# En el eje de la vía se pisa lo alto del balasto.
	var bed: Dictionary = _ray_down(Vector2(200.0, 34.0), [])
	assert_almost(bed["position"].y, formation + TransitRails.BALLAST_TOP, 0.02)


func test_level_crossing_is_flush_with_the_rail() -> void:
	# El primer paso a nivel del apartadero de la fábrica: la losa, a lo alto del carril.
	for via: Dictionary in _city.plan.transit["vias"]:
		if String(via["id"]) != "fabrica":
			continue
		for stretch: Dictionary in via["tramos"]:
			if String(stretch["tipo"]) != "embebida":
				continue
			var middle: Array = stretch["puntos"][stretch["puntos"].size() / 2]
			var point: Vector2 = Vector2(middle[0], middle[1])
			var rail: float = _formation("fabrica", point) + TransitRails.SLEEPER_TOP
			rail += TransitRails.RAIL_HEIGHT
			assert_almost(_ray_down(point, [])["position"].y, rail, 0.03, "paso en %s" % point)
			return
	assert_true(false, "sin pasos a nivel en el apartadero de la fábrica")


## La rasante de una vía (el plano de formación) en el punto de su trazado más cercano.
func _formation(ident: String, point: Vector2) -> float:
	var best: float = INF
	var result: float = NAN
	for via: Dictionary in _city.plan.transit["vias"]:
		if String(via["id"]) != ident:
			continue
		for stretch: Dictionary in via["tramos"]:
			for p: Array in stretch["puntos"]:
				var d: float = point.distance_to(Vector2(p[0], p[1]))
				if d < best and String(stretch["tipo"]) == "abierta":
					best = d
					result = p[2]
	return result


## Lleva un cuerpo como el del visitante de [param from] hacia [param to] y devuelve a qué
## altura acaba.
func _walk(from: Vector2, to: Vector2, seconds: float) -> float:
	var body: CharacterBody3D = CharacterBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = 0.3
	capsule.height = 1.75
	shape.shape = capsule
	shape.position = Vector3(0.0, 0.875, 0.0)
	body.add_child(shape)
	body.floor_max_angle = deg_to_rad(50.0)
	body.floor_snap_length = 0.6
	get_tree().root.add_child(body)
	body.global_position = CityPlan.to_world(from, _city.surface_height(from) + 0.05)
	var direction: Vector3 = (CityPlan.to_world(to) - CityPlan.to_world(from)).normalized()
	var frames: int = int(seconds * Engine.physics_ticks_per_second)
	for _i: int in frames:
		var flat: Vector2 = CityPlan.to_plan(body.global_position)
		if flat.distance_to(to) < 0.3:
			break
		body.velocity.x = direction.x * 1.4
		body.velocity.z = direction.z * 1.4
		body.velocity.y = 0.0 if body.is_on_floor() else body.velocity.y - 9.8 / 60.0
		body.move_and_slide()
		await get_tree().physics_frame
	var height: float = body.global_position.y
	body.queue_free()
	return height


func _detail_count() -> int:
	var details: Dictionary = _city.plan.transit["detalles"]
	return details["tapas"].size() + details["sumideros"].size()


## El primer edificio de un tipo montado con el kit (intacto, para que tenga todas sus piezas).
func _first_kit_building(kind: String) -> Dictionary:
	for building: Dictionary in _city.plan.data["edificios"]:
		if building["tipo"] == kind and int(building["dano"]) == 1:
			return building
	return {}


## El nodo del modelo de un edificio montado con el kit (null si no lo hay).
func _model_of(building: Dictionary) -> Node3D:
	var center: Vector2 = Vector2(building["centro"][0], building["centro"][1])
	var sector: String = CityPlan.sector_name(_city.plan.sector_of(center))
	return _city.get_node_or_null("Sector_%s/Edificios/%s" % [sector, building["id"]]) as Node3D


func _ray(point: Vector2, from_height: float, to_height: float) -> Dictionary:
	var space: PhysicsDirectSpaceState3D = _city.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		CityPlan.to_world(point, from_height), CityPlan.to_world(point, to_height)
	)
	return space.intersect_ray(query)


func _ray_down(point: Vector2, exclude: Array[RID]) -> Dictionary:
	var space: PhysicsDirectSpaceState3D = _city.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		CityPlan.to_world(point, 300.0), CityPlan.to_world(point, -50.0)
	)
	query.exclude = exclude
	return space.intersect_ray(query)
