extends "res://tests/test_case.gd"
## Los recortes contra la rejilla del relieve (GridClip): las piezas cubren justo el
## polígono, cada una dentro de un triángulo de la rejilla, y se restan sin dejar nada.


func test_split_keeps_the_area_in_single_triangles() -> void:
	var triangle: PackedVector2Array = PackedVector2Array(
		[Vector2(0.3, 0.7), Vector2(9.1, 2.2), Vector2(4.4, 7.9)]
	)
	var total: float = 0.0
	for piece: Array in GridClip.split(triangle, 2.0):
		var cell: Vector2i = piece[0]
		var k: int = piece[1]
		var poly: PackedVector2Array = piece[2]
		total += GridClip.area(poly)
		assert_true(GridClip.area(poly) > 0.0, "las piezas siguen en sentido antihorario")
		var center: Vector2 = Vector2.ZERO
		for p: Vector2 in poly:
			center += p
		center /= poly.size()
		assert_eq(Vector2i((center / 2.0).floor()), cell, "la pieza cae en su celda")
		var local: Vector2 = center / 2.0 - Vector2(cell)
		assert_eq(0 if local.y >= local.x else 1, k, "y en su triángulo de la celda")
	assert_almost(total, GridClip.area(triangle), 1e-3)


func test_subtract_leaves_the_difference() -> void:
	var square: PackedVector2Array = PackedVector2Array(
		[Vector2(0, 0), Vector2(4, 0), Vector2(4, 4), Vector2(0, 4)]
	)
	var hole: PackedVector2Array = PackedVector2Array(
		[Vector2(1, 1), Vector2(3, 1), Vector2(3, 2), Vector2(1, 2)]
	)
	var total: float = 0.0
	for poly: PackedVector2Array in GridClip.subtract(square, hole):
		total += GridClip.area(poly)
	assert_almost(total, 16.0 - 2.0, 1e-4)
	assert_true(GridClip.subtract(hole, square).is_empty(), "lo que queda dentro, se va")


func test_subdivide_cuts_at_every_grid_line() -> void:
	var line: PackedVector2Array = PackedVector2Array([Vector2(0.5, 0.25), Vector2(5.5, 1.75)])
	var cut: PackedVector2Array = GridClip.subdivide(line, 2.0)
	# Cruza x = 2 y x = 4, ninguna horizontal y la diagonal x - y = 2.
	assert_eq(cut.size(), 5)
	for k: int in cut.size() - 1:
		var middle: Vector2 = (cut[k] + cut[k + 1]) * 0.5 / 2.0
		var cell: Vector2 = middle.floor()
		for p: Vector2 in [cut[k], cut[k + 1]]:
			var q: Vector2 = p / 2.0 - cell
			assert_true(q.x >= -1e-4 and q.x <= 1.0001 and q.y >= -1e-4 and q.y <= 1.0001)
