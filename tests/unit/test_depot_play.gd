extends "res://tests/test_case.gd"
## El depósito jugable de principio a fin (F2-05 a F2-11): el primer día, la
## descontaminación, el banco, las etiquetas, la caja, un cliente, la comida, el
## impuesto y dormir. Se juega con el jugador del anfitrión, pidiendo el trabajo
## como lo pide el ratón (en unidades del gesto).

const LEVEL: String = "res://scenes/depot/deposito.tscn"
const SAVE_PATH: String = "user://test_deposito.json"

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


func after_each() -> void:
	_level.free()
	SaveSystem.delete_save()
	SaveSystem.save_path = _original_save
	GameState.reset_for_new_game("")
	GameState.clock_running = false


func test_first_day_checklist() -> void:
	var chores: DepotChores = _level.chores
	assert_eq(chores.done().size(), 0, "el primer día no hay nada hecho")
	assert_true(chores.note.is_shown(), "la nota de la administración está en la puerta")
	# Telarañas, polvo y manchas: a pasadas, con la escoba, la mano o la fregona.
	await _hold(&"escoba")
	for web: CobwebFixture in chores.cobwebs:
		_work_on(web, &"escoba", 3.0)
	for patch: DirtFixture in chores.dirt:
		if patch.kind == DirtFixture.Kind.DUST:
			_work_on(patch, &"escoba", 4.0)
	await _drop()
	await _hold(&"fregona")
	for patch: DirtFixture in chores.dirt:
		if patch.kind == DirtFixture.Kind.STAIN:
			_work_on(patch, &"fregona", 4.0)
	await _drop()
	# La persiana: con la palanca, tirando hacia abajo; después sube con F.
	await _hold(&"palanca")
	_player.global_position = Vector3(0.0, 0.03, 2.3)
	_work_on(chores.shutter, &"palanca", 4.0)
	assert_false(chores.shutter.is_jammed(), "desatascada")
	await _drop()
	chores.shutter.request_use(&"")
	assert_true(chores.shutter.is_open(), "y sube")
	# La bombilla: desenroscar la fundida (al revés del reloj) y enroscar la nueva.
	_work_on(chores.lamp, Workable.HANDS, -2.0)
	assert_eq(chores.lamp.bulb(), "ninguna", "la fundida cae")
	await _hold(&"bombilla")
	_work_on(chores.lamp, &"bombilla", 2.0)
	assert_true(chores.lamp.is_lit(), "la nueva da luz")
	assert_true(_player.held_item() == null, "la bombilla se ha gastado")
	# La estufa: leña y una cerilla.
	await _hold(&"lena")
	_work_on(chores.stove, &"lena", 1.0)
	await _hold(&"cerillas")
	_work_on(chores.stove, &"cerillas", 1.0)
	assert_true(chores.stove.is_lit(), "la estufa arde")
	await _drop()
	# Las cajas del antiguo dueño: se abren tirando de las solapas.
	var opened: int = 0
	for item: Carryable in _items.items():
		if item.state.extra.has("contenido"):
			chores.open_box(item)
			opened += 1
	assert_eq(opened, 4, "había cuatro cajas")
	await _frames(10)
	assert_true(_find(&"bombilla_fundida") != null, "la bombilla fundida está por ahí")
	assert_true(_find(&"radio_bolsillo") != null, "de las cajas sale lo que había")
	# La basura al cubo, la bolsa fuera y al contenedor.
	for item: Carryable in _items.items():
		if item.state.data.trash:
			item.give_to(_player.peer_id)
			await _frames(2)
			_work_on(chores.bin, &"basura", 1.0)
			await _frames(2)
	assert_true(chores.bin.count() > 5, "el cubo se llena")
	chores.bin.request_use(&"")
	await _frames(5)
	assert_eq(chores.bin.count(), 0, "se saca la bolsa")
	var bag: Carryable = _find(&"bolsa_basura")
	assert_true(bag != null, "sale la bolsa llena")
	bag.give_to(_player.peer_id)
	await _frames(2)
	_work_on(chores.dumpster, &"basura", 1.0)
	assert_eq(chores.dumpster.bags(), 1, "la bolsa va al contenedor")
	await _frames(40)
	assert_eq(chores.done().size(), DepotChores.CHORES.size(), "todo hecho")
	assert_eq(
		(chores.note.paper()["tachados"] as Array).size(), DepotChores.CHORES.size(), "y tachado"
	)


func test_decontamination_brush_and_bag() -> void:
	var sink: SinkFixture = _level.workshop.sink
	var mask: Carryable = _spawn(&"mascara", sink.model.global_transform * Vector3(0.0, 0.75, 0.0))
	mask.set_values({"contamination": 0.8})
	await _frames(30)
	assert_true(sink.holds(mask), "la máscara está en la pila")
	var reading: float = ItemView.radiation_at(
		_items, mask.body().global_position + Vector3(0.5, 0, 0)
	)
	assert_true(reading > 0.3, "el dosímetro la nota")
	sink.request_use(&"")
	assert_true(sink.is_running(), "corre el agua")
	await _seconds(1.2)
	assert_true(mask.state.contamination < 0.8, "el agua quita algo")
	var before: float = mask.state.contamination
	await _hold(&"cepillo")
	_work_item(mask, &"cepillo", 3.0)
	assert_true(mask.state.contamination < before - 0.15, "el cepillo quita más")
	await _drop()
	var copper: Carryable = _spawn(&"chatarra_cobre", Vector3(0.5, 0.2, 0.5))
	copper.set_values({"contamination": 0.5})
	await _hold(&"bolsa_plastico")
	_work_item(copper, &"bolsa", 1.0)
	assert_true(copper.state.bagged, "embolsado")
	assert_almost(copper.state.emission(), 0.0, 0.001, "ya no contamina")
	assert_true(_player.held_item() == null, "la bolsa se gasta")


func test_bench_repair_step_by_step() -> void:
	var radio: Carryable = _spawn(&"radio_bolsillo", DepotRoom.BENCH_MAT + Vector3(0, 0.08, 0))
	radio.set_values({"condition": 0.3})
	await _frames(30)
	assert_true(_level.workshop.on_bench(radio), "está en el banco")
	var recipe: RepairRecipe = RepairRecipe.for_item(&"radio_bolsillo")
	assert_eq(recipe.steps.size(), 5)
	await _hold(&"destornillador")
	_work_item(radio, &"destornillador", 2.0)
	assert_eq(int(radio.state.extra.get("paso", 0)), 0, "apretar no afloja")
	_work_item(radio, &"destornillador", -4.5)
	assert_eq(int(radio.state.extra.get("paso", 0)), 1, "fuera los tornillos")
	await _drop()
	_work_item(radio, Workable.HANDS, 1.2)
	await _hold(&"cepillo_alambre")
	_work_item(radio, &"cepillo_alambre", 4.5)
	await _drop()
	_work_item(radio, Workable.HANDS, 1.2)
	await _hold(&"destornillador")
	_work_item(radio, &"destornillador", 4.5)
	assert_true(bool(radio.state.extra.get("reparado", false)), "reparada")
	assert_almost(radio.state.condition, recipe.repaired_condition, 0.001, "como nueva")
	# Lejos del banco no se repara.
	var boots: Carryable = _spawn(&"botas", Vector3(0.0, 0.2, 1.0))
	await _hold(&"aguja_hilo")
	_work_item(boots, &"aguja", 5.0)
	assert_false(bool(boots.state.extra.get("reparado", false)), "fuera del banco, no")


func test_tags_and_money_with_the_wheel() -> void:
	var workshop: DepotWorkshop = _level.workshop
	workshop.tag_box.request_use(&"")
	await _frames(10)
	var tag: Carryable = _player.held_item()
	assert_true(tag != null and tag.state.data.id == &"etiqueta", "sale una etiqueta en blanco")
	for _i in 6:
		_player.request_adjust(1)
	assert_eq(int(tag.state.extra.get("precio", 0)), 16, "la rueda sube el precio")
	var clock: Carryable = _spawn(&"despertador", Vector3(0.0, 0.2, 1.0))
	await _frames(5)
	_work_item(clock, &"etiqueta", 1.0)
	assert_eq(clock.state.price, 16, "la etiqueta queda atada")
	# La caja de los rublos: un fajo de diez, la rueda cuenta más.
	var start: int = GameState.rubles
	_level.counter.cash_box.request_use(&"")
	await _frames(10)
	var wad: Carryable = _player.held_item()
	assert_eq(int(wad.state.extra.get("rublos", 0)), 10)
	_player.request_adjust(1)
	_player.request_adjust(1)
	assert_eq(int(wad.state.extra.get("rublos", 0)), 12)
	assert_eq(GameState.rubles, start - 12, "sale de la caja")
	_work_on(_level.counter.cash_box, &"billetes", 1.0)
	assert_eq(GameState.rubles, start, "y vuelve a ella")


func test_a_customer_buys_from_the_counter() -> void:
	var counter: DepotCounter = _level.counter
	var shutter: ShutterFixture = _level.chores.shutter
	_level.world.set_values("persiana", {"atascada": false, "abierta": true})
	GameState.minute = 10.0 * 60.0
	counter.start_visit([&"relojero", "comprar"])
	assert_true(counter.customer != null, "viene el relojero")
	await _seconds(0.2)
	counter.customer.global_position = Station.WINDOW_SPOT
	counter.customer.walk([Station.WINDOW_SPOT])
	await _frames(10)
	assert_eq(counter.phase, DepotCounter.Phase.WAITING, "espera en la ventanilla")
	assert_true(counter.slip.is_shown(), "deja su papelito")
	var clock: Carryable = _spawn(&"despertador", DepotRoom.DEAL_SPOT + Vector3(0.0, 0.1, 0.0))
	clock.set_values({"price": 20, "condition": 0.85})
	await _seconds(1.6)
	assert_eq(counter.phase, DepotCounter.Phase.OFFERED, "lo mira y deja dinero")
	var wad: Carryable = _items.find_item(int(counter.visit["wad"]))
	assert_eq(int(wad.state.extra["rublos"]), 20, "la etiqueta le parece bien")
	var start: int = GameState.rubles
	var clock_uid: int = clock.state.uid
	wad.give_to(_player.peer_id)
	await _frames(10)
	assert_eq(GameState.rubles, start + 20, "coger los billetes es aceptar")
	assert_true(_items.find_item(clock_uid) == null, "se lleva el despertador")
	assert_eq(counter.phase, DepotCounter.Phase.LEAVING, "y se va")
	var sales: Array = GameState.ledger.filter(
		func(entry: Dictionary) -> bool: return entry["kind"] == "venta"
	)
	assert_eq(sales.size(), 1, "apuntado en el libro")
	assert_true(shutter.is_open())


func test_a_customer_leaves_a_job_when_nothing_suits() -> void:
	var counter: DepotCounter = _level.counter
	_level.world.set_values("persiana", {"atascada": false, "abierta": true})
	GameState.minute = 10.0 * 60.0
	counter.start_visit([&"relojero", "comprar"])
	counter.customer.global_position = Station.WINDOW_SPOT
	counter.customer.walk([Station.WINDOW_SPOT])
	await _frames(10)
	counter.call("_give_up")
	assert_eq(GameState.jobs.size(), 1, "deja un encargo")
	assert_eq(str(GameState.jobs[0]["item"]), "radio_bolsillo")
	await _frames(5)
	assert_eq(_level.counter.board.get_node(^"Fichas").get_child_count(), 1, "clavado en el corcho")


func test_food_tax_and_sleep() -> void:
	var services: DepotStation = _level.services
	var start: int = GameState.rubles
	# La sopa: diez rublos en el mostrador del puesto.
	var wad: Carryable = _spawn(&"billetes", Station.STALL_COUNTER + Vector3(0.1, 0.05, 0.0))
	wad.set_values({"extra": {"rublos": 12}})
	await _seconds(1.8)
	var soup: Carryable = _find(&"sopa")
	assert_true(soup != null, "la vendedora sirve la sopa")
	var change: Carryable = _find(&"billetes")
	assert_true(change != null and int(change.state.extra["rublos"]) == 2, "y da la vuelta")
	soup.give_to(_player.peer_id)
	await _frames(3)
	_work_item(soup, &"comida", 2.0)
	assert_almost(GameState.fed_today, 1.0, 0.001, "comido")
	# El impuesto: un fajo por la ranura del buzón.
	_level.counter.cash_box.request_use(&"")
	await _frames(10)
	for _i in 10:
		_player.request_adjust(1)
	assert_eq(int(_player.held_item().state.extra["rublos"]), 20)
	var mailbox: MailboxFixture = services.get_node(^"Buzon")
	_work_on(mailbox, &"billetes", 1.0)
	assert_eq(GameState.debt, -20, "pagado por adelantado")
	assert_eq(GameState.rubles, start - 20)
	# Dormir: el catre no deja antes de las 18; después termina el día.
	_level.day.cot.request_use(&"")
	await _frames(5)
	assert_eq(GameState.day, 1, "aún no hay sueño")
	GameState.minute = 20.0 * 60.0
	_level.day.cot.request_use(&"")
	await _seconds(DepotDay.FADE + 0.8)
	assert_eq(GameState.day, 2, "nuevo día")
	assert_eq(GameState.debt, 0, "el impuesto de la noche, ya pagado")
	assert_eq(GameState.hungry_days, 0, "había comido")
	assert_true(SaveSystem.has_save(), "se guarda al dormir")
	assert_true(services.receipt.is_shown(), "el recibo llega por la mañana")
	assert_true(services.morning.is_shown(), "y el aviso del día")
	assert_true(_player.global_position.distance_to(DepotDay.WAKE_SPOTS[0]) < 0.3, "junto al catre")


func test_starving_starts_over() -> void:
	var chores: DepotChores = _level.chores
	_level.world.set_value(chores.dirt[0].fixture_id, "suciedad", 0.0)
	GameState.hungry_days = GameState.HUNGRY_DEATH - 1
	GameState.minute = 20.0 * 60.0
	_level.day.sleep()
	await _seconds(DepotDay.FADE + 0.5)
	assert_false(SaveSystem.has_save(), "la partida se borra")
	await _seconds(DepotDay.RESTART_DELAY + 1.0)
	CloseUp.active.close()
	assert_eq(GameState.day, 1, "vuelve a ser el primer día")
	assert_eq(GameState.hungry_days, 0)
	assert_almost(chores.dirt[0].dirt(), 1.0, 0.001, "el local, sucio otra vez")
	assert_eq(_items.items().size(), 28, "con lo que dejó el antiguo dueño")
	assert_true(GameState.clock_running, "y la hora corre")


## Pone [param item_id] en las manos del jugador.
func _hold(item_id: StringName) -> void:
	await _drop()
	_items.give(_player, item_id, {})
	await _frames(15)
	assert_true(
		_player.held_item() != null and _player.held_item().state.data.id == item_id,
		"lleva %s" % item_id
	)


func _drop() -> void:
	var held: Carryable = _player.held_item()
	if held != null:
		_items.remove_item(held)
		await _frames(3)


## Trabaja una cosa fija con lo que lleva (como lo pediría el ratón).
func _work_on(fixture: Fixture, tool: StringName, amount: float) -> void:
	for workable: Workable in fixture.workables:
		if workable.accepts(tool):
			workable.work(_player, tool, amount, Vector3.INF)
			return
	assert_true(false, "%s no se trabaja con %s" % [fixture.name, tool])


## Trabaja un objeto suelto con lo que lleva.
func _work_item(item: Carryable, tool: StringName, amount: float) -> void:
	var workable: Workable = Workable.find(item.body(), tool)
	if workable == null:
		assert_true(false, "%s no se trabaja con %s" % [item.state.data.id, tool])
		return
	workable.work(_player, tool, amount, item.body().global_position)


func _spawn(item_id: StringName, where: Vector3) -> Carryable:
	return _items.spawn_with(item_id, Transform3D(Basis.IDENTITY, where), {})


func _find(item_id: StringName) -> Carryable:
	for item: Carryable in _items.items():
		if item.state.data.id == item_id:
			return item
	return null


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame


func _seconds(time: float) -> void:
	await get_tree().create_timer(time).timeout
