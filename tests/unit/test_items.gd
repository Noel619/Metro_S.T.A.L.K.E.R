extends "res://tests/test_case.gd"
## Modelo de datos de los objetos (F2-04).


func test_every_item_file_is_valid() -> void:
	var files: PackedStringArray = DirAccess.get_files_at(ItemState.ITEMS_DIR)
	assert_true(files.size() >= 10, "faltan fichas en data/items")
	for file_name: String in files:
		if not file_name.ends_with(".tres"):
			continue
		var data: ItemData = load(ItemState.ITEMS_DIR + file_name)
		assert_true(data != null, file_name)
		assert_eq(String(data.id), file_name.get_basename(), "el id coincide con el archivo")
		assert_true(ResourceLoader.exists("res://assets/models/%s.glb" % data.model), file_name)
		assert_true(
			data.grid_shape.has(Vector2i.ZERO), "la forma empieza en la esquina: " + file_name
		)
		# Lo que no es mercancía (la basura, los billetes, las etiquetas) no vale nada.
		var goods: bool = not data.trash and not data.tool in [&"billetes", &"etiqueta", &"basura"]
		assert_true(data.weight > 0.0 and (data.base_value > 0 or not goods), file_name)


func test_grid_shape_size_and_rotation() -> void:
	var broom: ItemData = ItemState.load_data(&"escoba")
	assert_eq(broom.grid_size(), Vector2i(1, 4))
	var turned: Array[Vector2i] = broom.rotated_shape(1)
	assert_eq(turned.size(), 4)
	for cell: Vector2i in turned:
		assert_eq(cell.y, 0, "tumbada ocupa una sola fila")
	assert_eq(broom.rotated_shape(4), broom.grid_shape, "cuatro giros la dejan igual")


func test_value_depends_on_condition_and_contamination() -> void:
	var can: ItemData = ItemState.load_data(&"lata_conserva")
	assert_eq(can.value(1.0, 0.0), can.base_value)
	assert_true(can.value(0.5, 0.0) < can.value(1.0, 0.0), "peor estado, menos valor")
	assert_true(can.value(1.0, 0.6) < can.value(1.0, 0.0), "contaminado vale menos")
	assert_true(can.value(0.05, 0.0) <= 2, "roto solo vale como chatarra")
	assert_true(can.value(1.0, 1.0) > 0, "nunca negativo")


func test_scrap_is_sold_by_weight() -> void:
	var drum: ItemData = ItemState.load_data(&"bidon")
	assert_eq(drum.value(1.0, 0.0), roundi(drum.base_value * drum.weight))


func test_state_roundtrip() -> void:
	var state: ItemState = ItemState.create(&"botella_verde", 42)
	state.condition = 0.4
	state.contamination = 0.25
	state.price = 7
	var copy: ItemState = ItemState.from_dict(state.to_dict())
	assert_eq(copy.data.id, &"botella_verde")
	assert_eq(copy.uid, 42)
	assert_almost(copy.condition, 0.4)
	assert_almost(copy.contamination, 0.25)
	assert_eq(copy.price, 7)
	assert_eq(copy.value(), state.value())
