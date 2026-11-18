extends "res://tests/test_case.gd"
## Los sistemas base del depósito jugable (Fase 2): el estado de la partida y el
## día, el estado de las cosas fijas, el trabajo con herramientas y los objetos
## que se guardan.

const LEVEL: String = "res://scenes/depot/deposito.tscn"


func before_each() -> void:
	DepotLevel.continue_saved = false


func after_each() -> void:
	GameState.reset_for_new_game("")
	GameState.clock_running = false


func test_a_day_charges_the_tax_and_counts_what_was_eaten() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.eat(1.0)
	GameState.end_day()
	assert_eq(GameState.day, 2)
	assert_eq(GameState.debt, GameState.TAX_PER_DAY, "se carga el impuesto de la noche")
	assert_eq(GameState.hungry_days, 0, "comió")
	assert_almost(GameState.minute, GameState.WAKE_MINUTE, 0.001, "se despierta a las 7")
	GameState.end_day()
	assert_eq(GameState.hungry_days, 1, "un día sin comer")
	assert_eq(GameState.debt, 2 * GameState.TAX_PER_DAY)
	assert_false(GameState.is_sealed())
	GameState.end_day()
	assert_true(GameState.is_sealed(), "con tres días de deuda se precinta el mostrador")
	assert_eq(GameState.pay_tax(70), -10, "lo que sobra queda a cuenta")
	assert_false(GameState.is_sealed())
	var paid: Array = GameState.entries_of(GameState.day).filter(
		func(entry: Dictionary) -> bool: return entry["kind"] == "impuesto"
	)
	assert_eq(paid.size(), 1, "el pago va al libro de cuentas")


func test_jobs_expire_after_their_day() -> void:
	GameState.reset_for_new_game("Prueba")
	var id: int = GameState.add_job({"client": "relojero", "item": "despertador", "deadline": 2})
	assert_eq(GameState.job(id)["state"], "abierto")
	GameState.end_day()
	assert_eq(GameState.job(id)["state"], "abierto", "el día 2 aún vale")
	GameState.end_day()
	assert_eq(GameState.job(id)["state"], "caducado")


func test_state_survives_saving() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 600.0
	GameState.record("venta", "Lata de conserva", 12)
	GameState.add_job({"client": "relojero", "item": "radio", "deadline": 5})
	var saved: Dictionary = GameState.save_state()
	GameState.reset_for_new_game("")
	GameState.load_state(saved)
	assert_eq(GameState.player_name, "Prueba")
	assert_almost(GameState.minute, 600.0, 0.001)
	assert_eq(GameState.ledger.size(), 1)
	assert_eq(GameState.jobs.size(), 1)
	assert_eq(GameState.time_text(), "10:00")


func test_fixture_state_is_shared_and_saved() -> void:
	var world: DepotWorld = DepotWorld.new()
	add_child(world)
	var seen: Array[String] = []
	world.state_changed.connect(func(id: String) -> void: seen.append(id))
	world.set_value("mancha_1", "polvo", 0.5)
	world.set_value("mancha_1", "polvo", 0.5)
	assert_eq(seen, ["mancha_1"], "solo avisa si cambia")
	assert_almost(world.value("mancha_1", "polvo", 1.0), 0.5, 0.001)
	assert_eq(world.value("bombilla", "estado", "fundida"), "fundida", "lo no tocado, por defecto")
	var saved: Dictionary = world.save_state()
	world.load_state({})
	assert_eq(world.value("mancha_1", "polvo", 1.0), 1.0)
	world.load_state(saved)
	assert_almost(world.value("mancha_1", "polvo", 1.0), 0.5, 0.001)
	world.free()


func test_working_with_a_tool_reaches_the_host() -> void:
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	await _frames(20)
	var player: Player = level.call("local_player")
	var broom: Carryable = _item(level, &"escoba")
	assert_true(broom != null, "hay escoba")
	broom.give_to(player.peer_id)
	await _frames(30)
	assert_true(player.held_item() == broom, "lleva la escoba")
	assert_eq(player.current_tool(), &"escoba")
	# Una cosa que se barre, delante de sus pies.
	var target: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(0.6, 0.05, 0.6)
	shape.shape = box
	target.add_child(shape)
	var workable: Workable = Workable.new()
	workable.tools = [&"escoba"]
	target.add_child(workable)
	level.add_child(target)
	target.global_position = player.global_position - player.global_basis.z * 0.9
	var total: Array[float] = [0.0]
	workable.worked.connect(
		func(_who: Node, _tool: StringName, amount: float, _point: Vector3) -> void:
			total[0] += amount
	)
	player.head_pitch = -1.0
	await _frames(5)
	assert_true(player.work_target() == workable, "la tiene delante para barrerla")
	player.apply_work(workable, 1.5, target.global_position)
	await _frames(2)
	assert_almost(total[0], 1.5, 0.001, "el anfitrión aplica el trabajo")
	# Con las manos no se barre.
	assert_true(Workable.find(target, Workable.HANDS) == null)
	# Lejos no cuenta.
	player.apply_work(workable, 1.0, player.global_position + Vector3(0.0, 0.0, 9.0))
	await _frames(2)
	assert_almost(total[0], 1.5, 0.001, "lo que no alcanza no cuenta")
	level.free()


func test_gestures_measure_the_mouse() -> void:
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	await _frames(10)
	var player: Player = level.call("local_player")
	var target: StaticBody3D = StaticBody3D.new()
	var workable: Workable = Workable.new()
	workable.tools = [Workable.HANDS]
	workable.gesture = Workable.Gesture.CIRCLE
	target.add_child(workable)
	level.add_child(target)
	player.set("_work_target", workable)
	# Un círculo en el sentido del reloj (en pantalla, con la Y hacia abajo).
	for i: int in 33:
		var angle: float = TAU * i / 32.0
		player.feed_gesture(Vector2(cos(angle), sin(angle)) * 20.0)
	assert_almost(float(player.get("_work_pending")), 1.0, 0.05, "una vuelta")
	player.set("_work_pending", 0.0)
	workable.gesture = Workable.Gesture.PULL
	player.feed_gesture(Vector2(0.0, -300.0))
	player.feed_gesture(Vector2(0.0, Player.PULL_PIXELS))
	assert_almost(float(player.get("_work_pending")), 1.0, 0.001, "tirar es solo hacia abajo")
	player.set("_work_target", null)
	level.free()


func test_items_keep_their_state_when_saved() -> void:
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	await _frames(10)
	var items: WorldItems = level.get("items")
	var can: Carryable = _item(level, &"lata_conserva")
	can.set_values({"price": 15, "extra": {"etiqueta": true}, "contamination": 0.4})
	assert_eq(can.state.price, 15)
	assert_eq(can.synced_state["price"], 15, "el estado que se replica también")
	var uid: int = can.state.uid
	var where: Vector3 = can.body().global_position
	var count: int = items.items().size()
	var saved: Dictionary = items.save_state()
	items.load_state(saved)
	await _frames(2)
	assert_eq(items.items().size(), count, "vuelven todos")
	var back: Carryable = items.find_item(uid)
	assert_true(back != null, "con su identificador")
	assert_eq(back.state.price, 15)
	assert_almost(back.state.contamination, 0.4, 0.001)
	assert_eq(back.state.extra.get("etiqueta"), true)
	assert_true(back.body().global_position.distance_to(where) < 0.01, "donde estaba")
	items.remove_item(back)
	await _frames(2)
	assert_true(items.find_item(uid) == null, "se puede quitar")
	level.free()


func _item(level: Node, item_id: StringName) -> Carryable:
	for item: Carryable in (level.get("items") as WorldItems).items():
		if item.state.data.id == item_id:
			return item
	return null


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
