extends "res://tests/test_case.gd"
## La salida (docs/SUPERFICIE.md, 1): de la reja de la escalera a la esclusa del
## vestíbulo, la compuerta, y de vuelta al depósito, que sigue como se dejó. Lo
## que se lleva en las manos sube y baja con uno. En solitario.

const DEPOT: String = "res://scenes/depot/deposito.tscn"
const SURFACE: String = "res://scenes/surface/superficie.tscn"

var _next: String = ""
var _levels: Array[Node] = []


func before_each() -> void:
	DepotLevel.continue_saved = false
	_next = ""
	Sortie.scene_changer = func(path: String) -> void: _next = path


func after_each() -> void:
	for level: Node in _levels:
		if is_instance_valid(level):
			level.free()
	Sortie.scene_changer = Callable()
	Sortie.arrived()
	Sortie.carried.clear()
	SaveSystem.clear_parked()
	GameState.clock_running = false
	GameState.reset_for_new_game("")


func test_the_grate_only_opens_in_the_day() -> void:
	var depot: DepotLevel = await _open(DEPOT)
	var player: Player = depot.local_player()
	GameState.minute = 21.0 * 60.0
	depot.exit.request_use(&"")
	await _frames(5)
	assert_false(depot.exit.is_open(), "de noche, la guardia no abre")
	GameState.minute = 9.0 * 60.0
	depot.exit.request_use(&"")
	await _frames(5)
	assert_true(depot.exit.is_open(), "de día, sí")
	assert_true(player != null)
	GameState.minute = 20.0 * 60.0 + 1.0
	await _frames(5)
	assert_false(depot.exit.is_open(), "a las 20 la cierran")


func test_going_up_and_coming_back_keeps_the_day() -> void:
	var depot: DepotLevel = await _open(DEPOT)
	var player: Player = depot.local_player()
	GameState.minute = 9.0 * 60.0
	depot.world.set_value("prueba", "marca", 7)
	depot.exit.request_use(&"")
	await _frames(int(DepotExit.FOLD_SECONDS * 60.0) + 10)
	# Delante de la reja, con una lata en la mano, y escaleras arriba.
	player.global_position = DepotExit.arrival(0)
	player.rotation.y = -PI / 2.0
	await _frames(20)
	var can: Carryable = depot.items.give(player, &"lata_conserva")
	await _frames(30)
	assert_eq(player.held_item(), can, "lleva una lata")
	player.scripted_input = Vector2(0.0, -1.0)
	for _i in 600:
		await get_tree().physics_frame
		if not _next.is_empty():
			break
	player.scripted_input = Vector2.ZERO
	assert_eq(_next, Sortie.SURFACE_SCENE, "todos en la escalera: se sube")
	assert_eq(Sortie.arriving, Sortie.UP)
	assert_true(Sortie.carried.has(player.peer_id), "la lata va con él")
	assert_true(SaveSystem.has_parked(DepotWorld.SAVE_KEY), "el depósito queda aparcado")
	depot.free()
	_next = ""
	# Arriba: en la esclusa, con la lata y la compuerta cerrada.
	var surface: SurfaceLevel = await _open(SURFACE)
	await _frames(40)
	var top: Player = surface.local_player()
	assert_true(top != null, "aparece arriba")
	assert_true(surface.in_lock(top.global_position), "en la esclusa")
	assert_true(top.is_on_floor(), "pisa el rellano")
	assert_true(top.surface_rules, "con las reglas de la superficie")
	assert_true(top.held_item() != null, "con la lata en la mano")
	if top.held_item() != null:
		assert_eq(top.held_item().state.data.id, &"lata_conserva")
	assert_false(surface.hatch.is_open(), "la compuerta está cerrada")
	# El volante: una vuelta y algo.
	surface.hatch.workables[0].work(top, Workable.HANDS, 0.7)
	assert_false(surface.hatch.is_open(), "con media vuelta no basta")
	surface.hatch.workables[0].work(top, Workable.HANDS, 0.7)
	assert_true(surface.hatch.is_open(), "se abre")
	var heard: Array = surface.stimuli.recent.filter(
		func(event: NoiseEvent) -> bool: return event.kind == Hatch.NOISE
	)
	assert_eq(heard.size(), 1, "abrirla suena")
	await _frames(int(SurfaceLevel.LEAVE_SECONDS * 60.0) + 20)
	assert_eq(_next, "", "con la compuerta abierta no se baja")
	surface.hatch.request_use(&"")
	await _frames(int(SurfaceLevel.LEAVE_SECONDS * 60.0) + 30)
	assert_eq(_next, Sortie.DEPOT_SCENE, "cerrada y todos dentro: se baja")
	assert_true(SaveSystem.has_parked("superficie"), "la superficie queda aparcada")
	surface.free()
	# Abajo: delante de la reja, con la lata, y el depósito como se dejó.
	var back: DepotLevel = await _open(DEPOT)
	await _frames(40)
	var bottom: Player = back.local_player()
	assert_true(bottom != null)
	assert_true(bottom.global_position.distance_to(DepotExit.arrival(0)) < 1.0, "al pie de la reja")
	assert_eq(back.world.value("prueba", "marca", 0), 7, "el depósito sigue como se dejó")
	assert_true(bottom.held_item() != null, "la lata ha bajado")
	assert_false(back.exit.is_open(), "la reja, cerrada")
	assert_false(SaveSystem.has_parked(DepotWorld.SAVE_KEY))


func _open(path: String) -> Node:
	var level: Node = load(path).instantiate()
	add_child(level)
	_levels.append(level)
	await _frames(10)
	return level


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
