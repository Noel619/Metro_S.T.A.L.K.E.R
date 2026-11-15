extends "res://tests/test_case.gd"


func test_clean_leaves_polygons_clockwise_without_repeats() -> void:
	var square: PackedVector2Array = PackedVector2Array(
		[
			Vector2(0, 0),
			Vector2(10, 0),
			Vector2(10, 0.01),
			Vector2(10, 10),
			Vector2(0, 10),
			Vector2(0, 0)
		]
	)
	var cleaned: PackedVector2Array = CityGeometry.clean(square)
	assert_eq(cleaned.size(), 4)
	assert_true(CityGeometry.signed_area(cleaned) < 0.0, "en sentido horario")
	assert_almost(absf(CityGeometry.signed_area(cleaned)), 100.0, 0.01)


func test_clean_keeps_small_round_towers() -> void:
	var circle: PackedVector2Array = PackedVector2Array()
	for i: int in 40:
		circle.append(Vector2.RIGHT.rotated(TAU * i / 40.0) * 2.0)
	assert_eq(CityGeometry.clean(circle).size(), 40, "una chimenea de 2 m de radio sigue redonda")


func test_clean_removes_spikes() -> void:
	# Un pico de ida y vuelta, como las astillas de los recortes de manzana.
	var spiky: PackedVector2Array = PackedVector2Array(
		[
			Vector2(0, 0),
			Vector2(0, 10),
			Vector2(10, 10),
			Vector2(10, 20),
			Vector2(10, 10),
			Vector2(10, 0)
		]
	)
	assert_eq(CityGeometry.clean(spiky).size(), 4)


func test_slice_cuts_along_an_axis() -> void:
	var block: PackedVector2Array = CityGeometry.clean(
		PackedVector2Array([Vector2(0, 0), Vector2(30, 0), Vector2(30, 10), Vector2(0, 10)])
	)
	var pieces: Array[PackedVector2Array] = CityGeometry.slice(block, Vector2.RIGHT, 10.0, 20.0)
	assert_eq(pieces.size(), 1)
	assert_almost(absf(CityGeometry.signed_area(pieces[0])), 100.0, 0.01)
	assert_true(CityGeometry.signed_area(pieces[0]) < 0.0, "los trozos también en sentido horario")


func test_triangulate_concave_footprints() -> void:
	var l_shape: PackedVector2Array = PackedVector2Array(
		[
			Vector2(0, 0),
			Vector2(0, 20),
			Vector2(8, 20),
			Vector2(8, 8),
			Vector2(20, 8),
			Vector2(20, 0)
		]
	)
	assert_eq(CityGeometry.triangulate(l_shape).size(), 12)


func test_point_along_a_line() -> void:
	var line: PackedVector2Array = PackedVector2Array(
		[Vector2(0, 0), Vector2(10, 0), Vector2(10, 10)]
	)
	assert_almost(CityGeometry.length(line), 20.0)
	var halfway: Transform2D = CityGeometry.point_along(line, 15.0)
	assert_true(halfway.origin.is_equal_approx(Vector2(10, 5)))
	assert_true(halfway.x.is_equal_approx(Vector2(0, 1)), "mira hacia el norte")
	assert_eq(CityGeometry.subdivide(line, 4.0).size(), 7)


func test_faces_point_where_they_are_told() -> void:
	var mesh: MeshBuffer = MeshBuffer.new()
	var tint: PackedColorArray = PackedColorArray([Color.WHITE])
	# Los mismos puntos en los dos sentidos: las dos caras tienen que mirar arriba.
	var quad: PackedVector3Array = PackedVector3Array(
		[Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(1, 0, -1), Vector3(0, 0, -1)]
	)
	mesh.add_face(quad, Vector3.UP, tint)
	quad.reverse()
	mesh.add_face(quad, Vector3.UP, tint)
	for normal: Vector3 in mesh.normals:
		assert_true(normal.is_equal_approx(Vector3.UP))
	# Godot dibuja la cara delantera en el sentido del reloj vista desde delante: desde
	# arriba, (a, b, c) tiene que girar como las agujas, es decir, normal de Newell hacia abajo.
	for t: int in range(0, mesh.indices.size(), 3):
		var a: Vector3 = mesh.vertices[mesh.indices[t]]
		var b: Vector3 = mesh.vertices[mesh.indices[t + 1]]
		var c: Vector3 = mesh.vertices[mesh.indices[t + 2]]
		assert_true((b - a).cross(c - a).y < 0.0, "triángulo %d" % (t / 3))
