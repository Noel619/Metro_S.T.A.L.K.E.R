extends "res://tests/test_case.gd"
## La mochila puesta y el cinturón (F3-03): ponérsela y quitársela, colgar y
## sacar del cinturón, lo que pesa y suena lo que se lleva puesto, y que al
## dormir se deja todo a los pies.

const LEVEL: String = "res://scenes/depot/deposito.tscn"
const SAVE_PATH: String = "user://test_equipo.json"

var _level: DepotLevel
var _player: Player
var _items: WorldItems
var _original_save: String = ""


func before_each() -> void:
	DepotLevel.continue_saved = false
	_original_save = SaveSystem.save_path
	SaveSystem.save_path = SAVE_PATH
	_level = load(LEVEL).instantiate()
	add_child(_level)
	await _frames(20)
	_player = _level.local_player()
	_items = _level.items
	# Junto a la mochila, mirándola.
	_player.move_to(DepotLevel.BACKPACK_SPOT + Vector3(0.0, 0.0, 0.9), 0.0)
	await _frames(5)


func after_each() -> void:
	_level.free()
	SaveSystem.delete_save()
	SaveSystem.save_path = _original_save
	GameState.reset_for_new_game("")
	GameState.clock_running = false


func test_wear_the_backpack_and_take_it_off() -> void:
	var bag: Backpack = _backpack()
	var uid: int = bag.item.state.uid
	bag.stash(ItemState.create(&"lata_conserva", 900), Vector2i(2, 2))
	await _frames(2)
	var full_weight: float = bag.item.state.weight()
	_player.gear.request_backpack(uid)
	await _frames(5)
	assert_true(_player.gear.wearing(), "se la ha puesto")
	assert_true(_items.find_item(uid) == null, "ya no está en el suelo")
	assert_almost(_player.carried_weight(), full_weight, 0.001, "pesa lo que lleva dentro")
	assert_true(_player.gear.rattle() > 0.9, "y la lata suelta suena")
	assert_true(
		(_player.get_node(^"Avatar") as PlayerAvatar).backpack_visible, "los demás se la ven puesta"
	)
	_player.gear.request_backpack(0)
	await _frames(10)
	assert_false(_player.gear.wearing(), "se la ha quitado")
	var again: Backpack = _backpack()
	assert_true(again != null and again.item.state.uid == uid, "es la misma mochila")
	assert_false(again.is_open(), "en el suelo, cerrada")
	assert_eq(again.grid().entries.size(), 1, "con la lata dentro")
	var ahead: Vector3 = again.item.body().global_position - _player.global_position
	assert_true(ahead.dot(-_player.global_basis.z) > 0.2, "delante de quien se la quita")
	assert_almost(_player.carried_weight(), 0.0, 0.001)


func test_an_open_backpack_closes_when_worn() -> void:
	var bag: Backpack = _backpack()
	bag.toggle()
	await _frames(2)
	assert_true(bag.is_open())
	_player.gear.request_backpack(bag.item.state.uid)
	await _frames(5)
	assert_true(_player.gear.wearing())
	_player.gear.request_backpack(0)
	await _frames(10)
	assert_false(_backpack().is_open(), "puesta no va abierta")


func test_the_belt_holds_three_small_things() -> void:
	var torch: Carryable = await _hold(&"linterna")
	var torch_uid: int = torch.state.uid
	_player.gear.request_belt(0)
	await _frames(5)
	assert_true(_player.held_item() == null, "se cuelga la linterna")
	assert_eq(_player.gear.belt_state(0).data.id, &"linterna")
	assert_true(_items.find_item(torch_uid) == null)
	# Con algo en la mano, el hueco ocupado se cambia.
	await _hold(&"navaja")
	_player.gear.request_belt(0)
	await _frames(20)
	assert_eq(_player.gear.belt_state(0).data.id, &"navaja", "la navaja al cinturón")
	var back: Carryable = _player.held_item()
	assert_true(back != null and back.state.uid == torch_uid, "y la misma linterna a la mano")
	_player.gear.request_belt(2)
	await _frames(5)
	assert_eq(_player.gear.belt_state(2).data.id, &"linterna")
	# Con las manos vacías, se saca.
	_player.gear.request_belt(2)
	await _frames(20)
	assert_true(_player.held_item() != null and _player.held_item().state.uid == torch_uid)
	assert_true(_player.gear.belt_state(2) == null)
	await _drop()
	# Lo grande no se cuelga.
	var battery: Carryable = await _hold(&"bateria_coche")
	_player.gear.request_belt(1)
	await _frames(5)
	assert_true(_player.held_item() == battery, "una batería no va al cinturón")
	assert_true(_player.gear.belt_state(1) == null)
	assert_true(PlayerGear.fits_belt(ItemState.load_data(&"palanca")), "la palanca (3 en fila), sí")
	assert_false(PlayerGear.fits_belt(ItemState.load_data(&"cuerda")), "la cuerda (2 × 2), tampoco")


func test_on_the_back_it_slows_less_than_in_the_hands() -> void:
	var battery: Carryable = await _hold(&"bateria_coche")
	var in_hands: float = _player.carry_slowdown()
	var bag: Backpack = _backpack()
	_items.remove_item(battery)
	await _frames(3)
	bag.stash(ItemState.create(&"bateria_coche", 901))
	await _frames(2)
	_player.gear.request_backpack(bag.item.state.uid)
	await _frames(5)
	var on_back: float = _player.carry_slowdown()
	assert_true(
		on_back > in_hands, "a la espalda frena menos (%.2f frente a %.2f)" % [on_back, in_hands]
	)
	assert_true(on_back < 1.0, "pero frena")


func test_at_night_everything_is_left_at_the_feet() -> void:
	var bag: Backpack = _backpack()
	var uid: int = bag.item.state.uid
	_player.gear.request_backpack(uid)
	await _hold(&"brujula")
	_player.gear.request_belt(1)
	await _frames(5)
	assert_true(_player.gear.wearing())
	_player.gear.unload()
	await _frames(10)
	assert_false(_player.gear.wearing())
	assert_true(_player.gear.belt_state(1) == null)
	assert_true(_items.find_item(uid) != null, "la mochila, en el suelo")
	var compass: bool = _items.items().any(
		func(item: Carryable) -> bool: return item.state.data.id == &"brujula"
	)
	assert_true(compass, "y la brújula del cinturón, también: así se guardan")


func test_opening_it_outside_takes_longer() -> void:
	var bag: Backpack = _backpack()
	var workable: Workable = Workable.find(bag.item.body(), Workable.HANDS)
	_player.surface = true
	workable.work(_player, Workable.HANDS, Backpack.TOGGLE_WORK + 0.01, Vector3.INF)
	await _frames(3)
	assert_false(bag.is_open(), "fuera no basta con lo que basta en el depósito")
	workable.work(_player, Workable.HANDS, Backpack.TOGGLE_WORK_OUTSIDE, Vector3.INF)
	await _frames(3)
	assert_true(bag.is_open(), "hay que mantener las manos más rato")
	_player.surface = false


func _backpack() -> Backpack:
	for item: Carryable in _items.items():
		if item.state.data.id == &"mochila" and not item.get_parent().is_queued_for_deletion():
			return Backpack.of(item.body())
	return null


func _hold(item_id: StringName) -> Carryable:
	await _drop()
	var item: Carryable = _items.give(_player, item_id, {})
	await _frames(15)
	assert_true(_player.held_item() == item, "lleva %s" % item_id)
	return item


func _drop() -> void:
	var held: Carryable = _player.held_item()
	if held != null:
		_items.remove_item(held)
		await _frames(3)


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
