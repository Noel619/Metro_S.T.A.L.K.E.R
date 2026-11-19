extends "res://tests/test_case.gd"
## La mochila y el cinturón (F3-03): la cuadrícula con las formas y los giros, el
## cinturón para lo pequeño, el peso y lo que suena suelto; y guardar y sacar con el
## jugador (en la superficie, arrodillándose).

var _world: Node3D
var _player: Player
var _items: WorldItems


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")


func after_each() -> void:
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_things_fit_by_their_shape() -> void:
	var pack: Backpack = Backpack.new()
	var crowbar: ItemState = ItemState.create(&"palanca", 1)
	var can: ItemState = ItemState.create(&"lata_conserva", 2)
	assert_true(pack.auto_place(crowbar), "la palanca cabe")
	assert_true(pack.auto_place(can), "y una lata")
	assert_eq(pack.entries.size(), 2)
	var shape: Array[Vector2i] = Backpack.shape_of(crowbar.data, false)
	var turned: Array[Vector2i] = Backpack.shape_of(crowbar.data, true)
	assert_eq(shape.size(), turned.size(), "girada ocupa lo mismo")
	assert_eq(pack.index_at(Vector2i.ZERO), 0, "la palanca empieza arriba a la izquierda")
	assert_false(pack.fits(can.data, Vector2i.ZERO), "donde hay algo no cabe otra cosa")
	assert_false(pack.fits(can.data, Vector2i(6, 0)), "ni fuera")
	var taken: ItemState = pack.take(1)
	assert_eq(taken.data.id, &"lata_conserva")
	assert_eq(pack.entries.size(), 1)
	# Llena: treinta latas caben; la treinta y una, no.
	var full: Backpack = Backpack.new()
	for index: int in 30:
		assert_true(full.auto_place(ItemState.create(&"lata_conserva", index + 10)))
	assert_false(full.auto_place(ItemState.create(&"lata_conserva", 99)), "llena")


func test_the_belt_takes_small_things() -> void:
	var pack: Backpack = Backpack.new()
	assert_true(pack.put_on_belt(ItemState.create(&"brujula", 1), 0))
	assert_false(
		pack.put_on_belt(ItemState.create(&"lata_conserva", 2), 0), "el hueco está ocupado"
	)
	assert_false(pack.put_on_belt(ItemState.create(&"bidon", 3), 1), "lo grande no va al cinturón")
	assert_eq(pack.take_from_belt(0).data.id, &"brujula")
	assert_true(pack.take_from_belt(0) == null)


func test_weight_and_what_rattles() -> void:
	var pack: Backpack = Backpack.new()
	pack.place(ItemState.create(&"lata_conserva", 1), Vector2i(0, 0))
	pack.place(ItemState.create(&"palanca", 2), Vector2i(0, 3))
	assert_almost(pack.weight(), 0.4 + ItemState.load_data(&"palanca").weight, 0.001)
	assert_eq(pack.loose_items(), 2, "la lata y la palanca suenan sueltas")
	# Un trapo al lado de la lata la acolcha.
	pack.place(ItemState.create(&"trapo", 3), Vector2i(1, 0))
	assert_eq(pack.loose_items(), 1, "la lata, envuelta, ya no suena")
	var copy: Backpack = Backpack.from_dict(pack.to_dict())
	assert_eq(copy.entries.size(), 3, "se guarda y se carga")
	assert_eq(copy.loose_items(), 1)


func test_store_and_take_with_the_player() -> void:
	await _build_world()
	var can: Carryable = _items.give(_player, &"lata_conserva")
	await _frames(30)
	assert_eq(_player.held_item(), can)
	_player.pack.store_held()
	await _frames(20)
	assert_true(_player.held_item() != null, "en la superficie, guardar lleva un segundo")
	assert_true(_player.crouch > 0.3, "arrodillado")
	await _frames(60)
	assert_true(_player.held_item() == null, "guardada")
	assert_eq(_player.pack.contents().entries.size(), 1, "en la mochila")
	assert_true(_player.carried_weight() > 0.3, "y pesa")
	_player.pack.take(0)
	await _frames(30)
	assert_true(_player.held_item() != null, "sacada a las manos")
	assert_eq(_player.pack.contents().entries.size(), 0)
	# El cinturón: la tecla guarda lo pequeño y lo vuelve a sacar.
	_player.pack.belt_key(1)
	await _frames(40)
	assert_true(_player.held_item() == null, "al cinturón")
	_player.pack.belt_key(1)
	await _frames(40)
	assert_true(_player.held_item() != null, "y del cinturón a la mano")


func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(60.0, 1.0, 60.0)
	shape.shape = box
	body.add_child(shape)
	body.position = Vector3(0.0, -0.5, 0.0)
	_world.add_child(body)
	_items = WorldItems.new()
	_items.save_key = "objetos_prueba"
	_world.add_child(_items)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	await _frames(10)


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
