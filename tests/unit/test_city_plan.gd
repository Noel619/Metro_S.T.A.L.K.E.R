extends "res://tests/test_case.gd"

## El plano se carga una vez para todos los tests (tarda medio segundo).
static var _shared: CityPlan


func before_each() -> void:
	if _shared == null:
		_shared = CityPlan.load_default()


func test_loads_plan_relief_and_ground() -> void:
	assert_true(_shared.is_loaded(), _shared.error)
	assert_eq(_shared.size, Vector2(1600.0, 1200.0))
	assert_eq(_shared.relief_size, Vector2i(800, 600))
	assert_eq(_shared.ground.get_size(), Vector2i(1600, 1200))
	assert_eq(_shared.data["edificios"].size(), int(_shared.data["estadisticas"]["edificios"]))


func test_relief_keeps_its_16_bits() -> void:
	var low: float = INF
	var high: float = -INF
	for value: float in _shared.heights:
		low = minf(low, value)
		high = maxf(high, value)
	# plano.json redondea al centímetro; el PNG trunca.
	assert_almost(low, _shared.data["relieve"]["min"], 0.011)
	assert_almost(high, _shared.data["relieve"]["max"], 0.011)


func test_heights_at_known_places() -> void:
	# En el centro del río, el relieve es su lecho, 3,5 m bajo el hielo (rio.json).
	assert_almost(_shared.height_at(Vector2(700.0, 706.0)), -9.5, 0.05, "lecho del río")
	assert_almost(float(_shared.river["hielo"]), -6.0, 0.01, "hielo del río")
	assert_true(float(_shared.river["agua"]) < -6.0, "el agua, bajo el hielo")
	assert_almost(_shared.height_at(Vector2(430.0, 330.0)), 0.0, 0.5, "plaza del Trabajo")
	assert_true(_shared.height_at(Vector2(1500.0, 1110.0)) < -17.0, "fondo del cráter")
	assert_true(_shared.height_at(Vector2(1000.0, 1000.0)) > 11.0, "meseta del centro")
	# Fuera del mapa se repite el borde.
	assert_almost(
		_shared.height_at(Vector2(-50.0, 706.0)), _shared.height_at(Vector2(0.0, 706.0)), 0.01
	)


func test_world_and_plan_coordinates() -> void:
	var point: Vector2 = Vector2(430.0, 330.0)
	var world: Vector3 = CityPlan.to_world(point, 2.5)
	assert_eq(world, Vector3(430.0, 2.5, -330.0), "el norte es -Z")
	assert_eq(CityPlan.to_plan(world), point)


func test_sectors() -> void:
	assert_eq(CityPlan.sector_name(_shared.sector_of(Vector2(10.0, 10.0))), "A1")
	assert_eq(CityPlan.sector_name(_shared.sector_of(Vector2(430.0, 330.0))), "C2")
	assert_eq(CityPlan.sector_name(_shared.sector_of(Vector2(1590.0, 1190.0))), "H6")
	assert_eq(CityPlan.sector_name(_shared.sector_of(Vector2(-30.0, 5000.0))), "A6")
	assert_eq(_shared.sector_grid(), Vector2i(8, 6))
	assert_eq(_shared.sector_rect(Vector2i(2, 1)), Rect2(400.0, 200.0, 200.0, 200.0))


func test_zones() -> void:
	assert_eq(_shared.zone_at(Vector2(430.0, 330.0)), 1)
	assert_eq(_shared.zone_label(Vector2(700.0, 706.0)), "El río")
	assert_eq(_shared.zone_at(Vector2(1292.0, 985.0)), 8, "el Edificio Partido")


func test_chance_matches_the_python_generator() -> void:
	# int(md5("PLZ-02/dano")[:8], 16) / 0xFFFFFFFF, calculado con tools/ciudad/.
	assert_almost(CityPlan.chance("PLZ-02/dano"), 0.017121421177201303, 1e-12)


func test_axis_reaches_the_bridge() -> void:
	# La avenida termina en eje(372), donde empieza el puente (ver datos.py).
	var end: Array = _shared.data["calles"][0]["puntos"][1]
	assert_true(_shared.axis_point(372.0).distance_to(Vector2(end[0], end[1])) < 0.1)


func test_every_footprint_can_be_built() -> void:
	for building: Dictionary in _shared.data["edificios"]:
		var outline: PackedVector2Array = CityPlan.ring(building["huella"][0])
		var triangles: PackedInt32Array = Geometry2D.triangulate_polygon(outline)
		assert_true(triangles.size() >= 3, "%s no se puede triangular" % building["id"])
		assert_true(building.has("cota"), "%s no tiene cota" % building["id"])


func test_decoder_rejects_8_bit_images() -> void:
	var image: Image = Image.create_empty(4, 4, false, Image.FORMAT_L8)
	assert_true(CityPlan.decode_gray16(image.save_png_to_buffer()).is_empty())
	assert_true(CityPlan.decode_gray16(PackedByteArray([1, 2, 3])).is_empty())
