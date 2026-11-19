extends "res://tests/test_case.gd"
## La cuadrícula de la mochila (F3-03): encajar por forma, girar, buscar hueco,
## el peso y lo que suena suelto.


func _state(item_id: StringName, uid: int = 0) -> ItemState:
	return ItemState.create(item_id, uid)


func test_items_fit_by_shape_and_never_overlap() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	var wrench: ItemData = ItemState.load_data(&"llave_inglesa")
	assert_eq(grid.size, Vector2i(6, 5), "se empieza con una mochila de 6 × 5")
	assert_true(
		grid.put(_state(&"llave_inglesa", 1), Vector2i(0, 0), 0), "la llave, tumbada arriba"
	)
	assert_false(grid.fits(wrench, Vector2i(2, 0), 0), "no se monta encima de otra")
	assert_false(grid.fits(wrench, Vector2i(4, 0), 0), "ni se sale por el borde")
	assert_true(grid.fits(wrench, Vector2i(5, 0), 1), "de pie, en la última columna, sí cabe")
	assert_eq(grid.occupant(Vector2i(2, 0)), 0, "la casilla (2, 0) es de la llave")
	assert_eq(grid.occupant(Vector2i(3, 0)), -1, "la (3, 0) está libre")
	assert_eq(grid.free_cells(), 27, "tres casillas ocupadas de treinta")


func test_find_spot_prefers_the_aimed_cell_and_rotates_if_needed() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	var battery: ItemData = ItemState.load_data(&"bateria_coche")
	var spot: Dictionary = grid.find_spot(battery, Vector2i(4, 3))
	assert_false(spot.is_empty(), "una batería cabe en una mochila vacía")
	var cells: Array[Vector2i] = BackpackGrid.footprint(battery, spot["celda"], spot["giro"])
	assert_true(cells.has(Vector2i(4, 3)), "la deja cubriendo la casilla apuntada")
	assert_true(grid.put(_state(&"bateria_coche"), spot["celda"], spot["giro"]))
	# Un quinqué ocupa 1 × 3: en una columna libre cabe de pie; si no, girado.
	var lamp: ItemData = ItemState.load_data(&"quinque")
	var lamp_spot: Dictionary = grid.find_spot(lamp)
	assert_false(lamp_spot.is_empty(), "queda sitio para el quinqué")
	assert_true(grid.fits(lamp, lamp_spot["celda"], lamp_spot["giro"]))


func test_full_backpack_says_no() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	var samovar: ItemData = ItemState.load_data(&"samovar")
	assert_true(grid.put(_state(&"samovar"), Vector2i(0, 0), 0))
	assert_true(grid.put(_state(&"samovar"), Vector2i(3, 0), 0))
	assert_true(grid.find_spot(samovar).is_empty(), "no caben tres samovares")
	assert_true(grid.find_spot(ItemState.load_data(&"lata_conserva")).is_empty() == false)
	assert_false(BackpackGrid.accepts(ItemState.load_data(&"mochila")), "una mochila no va dentro")


func test_take_returns_the_same_item() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	var state: ItemState = _state(&"reloj_bolsillo", 7)
	state.condition = 0.6
	state.contamination = 0.2
	assert_true(grid.put(state, Vector2i(2, 2), 0))
	var back: ItemState = grid.take(grid.occupant(Vector2i(2, 2)))
	assert_eq(back.uid, 7, "sale el mismo ejemplar")
	assert_almost(back.condition, 0.6)
	assert_almost(back.contamination, 0.2)
	assert_eq(grid.entries.size(), 0)


func test_weight_and_saved_roundtrip() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	assert_true(grid.put(_state(&"bateria_coche"), Vector2i(0, 0), 0))
	assert_true(grid.put(_state(&"leche_condensada"), Vector2i(5, 4), 0))
	var expected: float = (
		ItemState.load_data(&"bateria_coche").weight
		+ ItemState.load_data(&"leche_condensada").weight
	)
	assert_almost(grid.weight(), expected)
	# Lo que se guarda es JSON: sobrevive a una vuelta por texto.
	var text: String = JSON.stringify({BackpackGrid.KEY: grid.to_value()})
	var again: BackpackGrid = BackpackGrid.from_extra(JSON.parse_string(text))
	assert_eq(again.entries.size(), 2)
	assert_almost(again.weight(), expected)
	assert_eq(again.occupant(Vector2i(5, 4)), 1, "cada cosa sigue en su casilla")


func test_loose_metal_rattles_and_packing_tight_silences_it() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	assert_true(grid.put(_state(&"lata_conserva"), Vector2i(2, 2), 0))
	assert_almost(grid.rattle(), 1.0, 0.0001, "una lata sola en medio suena del todo")
	# Rodeada de ropa, ya no se mueve.
	assert_true(grid.put(_state(&"manoplas"), Vector2i(0, 2), 0))
	assert_true(grid.put(_state(&"manoplas"), Vector2i(3, 2), 0))
	assert_true(grid.put(_state(&"gorro_orejeras"), Vector2i(2, 0), 0))
	assert_true(grid.put(_state(&"gorro_orejeras"), Vector2i(2, 3), 0))
	assert_almost(grid.rattle(), 0.0, 0.0001, "bien apretada no suena")
	# La ropa no suena aunque vaya suelta.
	var soft: BackpackGrid = BackpackGrid.new()
	assert_true(soft.put(_state(&"manoplas"), Vector2i(2, 2), 0))
	assert_almost(soft.rattle(), 0.0)


func test_fragile_items_are_listed() -> void:
	var grid: BackpackGrid = BackpackGrid.new()
	assert_true(grid.put(_state(&"tarro_pepinillos"), Vector2i(0, 0), 0))
	assert_true(grid.put(_state(&"cinta_aislante"), Vector2i(3, 0), 0))
	var fragile: Array[ItemState] = grid.fragile()
	assert_eq(fragile.size(), 1, "el tarro se rompe; la cinta aislante, no")
	assert_eq(fragile[0].data.id, &"tarro_pepinillos")
