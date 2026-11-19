extends "res://tests/test_case.gd"
## La mochila en el depósito (F3-03): se abre con las manos, se mete y se saca
## lo que se lleva, pesa lo que lleva y lo guarda la partida.

const LEVEL: String = "res://scenes/depot/deposito.tscn"
const SAVE_PATH: String = "user://test_mochila.json"

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


func test_the_backpack_is_there_closed() -> void:
	var bag: Backpack = _backpack()
	assert_true(bag != null, "la mochila está junto a la mesa de planificar")
	assert_false(bag.is_open(), "cerrada")
	assert_true(bag.item.grabbable, "cerrada se puede coger")
	assert_eq(bag.grid().entries.size(), 0, "vacía")


func test_open_put_take_and_close() -> void:
	var bag: Backpack = _backpack()
	await _toggle(bag)
	assert_true(bag.is_open(), "se abre manteniendo las manos")
	assert_false(bag.item.grabbable, "abierta no se coge: se mete y se saca")
	# Meter una lata: deja de estar suelta y pasa a la cuadrícula.
	var can: Carryable = await _hold(&"lata_conserva")
	var uid: int = can.state.uid
	var can_weight: float = can.state.weight()
	bag.request_put(uid, Vector2i(2, 2))
	await _frames(5)
	assert_true(_player.held_item() == null, "ya no la lleva")
	assert_true(_items.find_item(uid) == null, "ya no está suelta por el depósito")
	var inside: BackpackGrid = bag.grid()
	assert_eq(inside.entries.size(), 1, "está dentro")
	assert_eq(inside.occupant(Vector2i(2, 2)), 0, "en la casilla a la que se apuntaba")
	var expected: float = bag.item.state.data.weight + can_weight
	assert_almost(bag.item.state.weight(), expected, 0.001, "la mochila pesa lo que lleva")
	assert_almost(bag.item.body().mass, expected, 0.001)
	# Algo grande va donde quepa, girado si hace falta.
	var battery: Carryable = await _hold(&"bateria_coche")
	bag.request_put(battery.state.uid, Vector2i(5, 4))
	await _frames(5)
	assert_eq(bag.grid().entries.size(), 2, "la batería también")
	assert_true(_player.held_item() == null)
	# Sacar la lata: vuelve a las manos, la misma.
	bag.request_take(Vector2i(2, 2))
	await _frames(20)
	var held: Carryable = _player.held_item()
	assert_true(held != null and held.state.uid == uid, "saca la misma lata")
	assert_eq(bag.grid().entries.size(), 1)
	await _drop()
	await _toggle(bag)
	assert_false(bag.is_open(), "se cierra igual que se abre")
	assert_true(bag.item.grabbable)


func test_what_does_not_fit_stays_in_the_hands() -> void:
	var bag: Backpack = _backpack()
	await _toggle(bag)
	for spot: Vector2i in [Vector2i(0, 0), Vector2i(3, 0)]:
		var samovar: Carryable = await _hold(&"samovar")
		bag.request_put(samovar.state.uid, spot)
		await _frames(5)
	var third: Carryable = await _hold(&"samovar")
	bag.request_put(third.state.uid, Vector2i(0, 3))
	await _frames(5)
	assert_true(_player.held_item() == third, "el tercer samovar no cabe: sigue en las manos")
	assert_eq(bag.grid().entries.size(), 2)


func test_contents_survive_saving() -> void:
	var bag: Backpack = _backpack()
	await _toggle(bag)
	var watch: Carryable = await _hold(&"reloj_bolsillo")
	watch.set_values({"condition": 0.7})
	await _frames(2)
	bag.request_put(watch.state.uid, Vector2i(1, 1))
	await _frames(5)
	var saved: Dictionary = _items.save_state()
	_items.load_state(JSON.parse_string(JSON.stringify(saved)))
	await _frames(10)
	var again: Backpack = _backpack()
	assert_true(again != null and again != bag, "la mochila vuelve a estar, cargada de nuevo")
	assert_true(again.is_open(), "abierta, como estaba")
	var inside: BackpackGrid = again.grid()
	assert_eq(inside.entries.size(), 1)
	assert_eq(inside.state_at(0).data.id, &"reloj_bolsillo")
	assert_almost(inside.state_at(0).condition, 0.7, 0.001, "con su estado")


func _backpack() -> Backpack:
	for item: Carryable in _items.items():
		if item.state.data.id == &"mochila" and not item.get_parent().is_queued_for_deletion():
			return Backpack.of(item.body())
	return null


## Mantiene las manos sobre la mochila hasta que se abre o se cierra.
func _toggle(bag: Backpack) -> void:
	await _drop()
	var workable: Workable = Workable.find(bag.item.body(), Workable.HANDS)
	assert_true(workable != null, "la mochila se trabaja con las manos")
	workable.work(_player, Workable.HANDS, Backpack.TOGGLE_WORK + 0.01, Vector3.INF)
	await _frames(3)


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
