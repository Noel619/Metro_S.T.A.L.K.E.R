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


func test_ground_collision_follows_the_relief() -> void:
	# La glorieta (llana), la cuesta de la loma (norte-sur: delataría un relieve al revés) y
	# el hielo del río. En el centro de la glorieta está el Monumento al Minero.
	for point: Vector2 in [Vector2(395.0, 345.0), Vector2(1000.0, 830.0), Vector2(700.0, 706.0)]:
		var hit: Dictionary = _ray_down(point, [])
		assert_false(hit.is_empty(), "nada bajo %s" % point)
		if not hit.is_empty():
			assert_almost(hit["position"].y, _city.plan.height_at(point), 0.35, "en %s" % point)


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


func _ray_down(point: Vector2, exclude: Array[RID]) -> Dictionary:
	var space: PhysicsDirectSpaceState3D = _city.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		CityPlan.to_world(point, 300.0), CityPlan.to_world(point, -50.0)
	)
	query.exclude = exclude
	return space.intersect_ray(query)
