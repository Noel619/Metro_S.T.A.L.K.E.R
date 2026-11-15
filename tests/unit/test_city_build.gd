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


func _ray_down(point: Vector2, exclude: Array[RID]) -> Dictionary:
	var space: PhysicsDirectSpaceState3D = _city.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		CityPlan.to_world(point, 300.0), CityPlan.to_world(point, -50.0)
	)
	query.exclude = exclude
	return space.intersect_ray(query)
