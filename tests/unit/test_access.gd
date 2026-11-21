extends "res://tests/test_case.gd"
## Las puertas de la superficie y las herramientas de acceso (F3-06): una cerradura no
## se abre con F (se sacude), la palanca la revienta y se oye lejos; la cizalla corta
## candados y cadenas; las ganzúas abren despacio y sin ruido, el miedo hace temblar la
## punta y forzarlas las parte; una cuerda atada a un anclaje se queda colgando y se
## baja por ella.

var _world: Node3D
var _player: Player
var _items: WorldItems
var _state: DepotWorld
var _heard: Array[NoiseEvent] = []


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	_heard.clear()


func after_each() -> void:
	if LockpickView.is_open():
		LockpickView.active.free()
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_a_locked_door_rattles_and_the_crowbar_bursts_it() -> void:
	await _build_world()
	var door: SurfaceDoor = _door("puerta_prueba", SurfaceDoor.LOCK)
	await _seconds(0.2)
	door.request_use(&"")
	await _seconds(0.3)
	assert_false(door.is_open(), "cerrada, F no la abre")
	assert_false(_kinds().has(&"palanca"))
	await _hold(&"palanca")
	var work: Workable = Workable.find(door.get_node("Bisagra/Cuerpo"), &"palanca")
	assert_true(work != null, "se trabaja con la palanca")
	for _pull: int in 3:
		work.work(_player, &"palanca", 1.0)
	assert_true(door.is_locked(), "tres tirones no bastan")
	assert_true(_kinds().has(&"puerta"), "cada tirón cruje")
	work.work(_player, &"palanca", 1.0)
	await _seconds(1.5)
	assert_false(door.is_locked(), "reventada")
	assert_eq(door.lock(), SurfaceDoor.BROKEN)
	assert_true(door.is_open(), "y abierta")
	assert_true(door.angle() > 1.0, "la hoja ha girado")
	var burst: Array = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == &"palanca"
	)
	assert_false(burst.is_empty(), "se oye")
	if not burst.is_empty():
		assert_almost((burst[0] as NoiseEvent).radius, 30.0, 0.01, "en toda la plaza")


func test_the_cutters_cut_padlocks_and_chains() -> void:
	await _build_world()
	var padlocked: SurfaceDoor = _door("puerta_candado", SurfaceDoor.PADLOCK)
	var chained: SurfaceDoor = _door("puerta_cadena", SurfaceDoor.CHAIN, Vector3(3.0, 0.0, -1.0))
	await _seconds(0.2)
	assert_true(padlocked.get_node("Bisagra/Candado").visible, "se ve el candado")
	assert_true(chained.get_node("Cadena").visible, "y la cadena")
	await _hold(&"palanca")
	var crowbar: Workable = Workable.find(chained.get_node("Bisagra/Cuerpo"), &"palanca")
	assert_true(crowbar.accepts(&"palanca"))
	for _pull: int in 6:
		crowbar.work(_player, &"palanca", 1.0)
	assert_eq(chained.lock(), SurfaceDoor.CHAIN, "la palanca no puede con la cadena")
	for door: SurfaceDoor in [padlocked, chained]:
		var cut: Workable = Workable.find(door.get_node("Bisagra/Cuerpo"), &"cizalla")
		cut.work(_player, &"cizalla", 1.0)
		assert_true(door.is_locked(), "un apretón no basta")
		cut.work(_player, &"cizalla", 1.2)
		assert_false(door.is_locked(), "cortado")
	await _seconds(0.2)
	assert_false(padlocked.get_node("Bisagra/Candado").visible, "ya no está el candado")
	var snips: Array = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == &"cizalla"
	)
	assert_eq(snips.size(), 2, "cada corte se oye")
	padlocked.request_use(&"")
	await _seconds(0.2)
	assert_true(padlocked.is_open(), "y se abre con F")


func test_picking_a_lock_pin_by_pin() -> void:
	await _build_world()
	var door: SurfaceDoor = _door("puerta_ganzuas", SurfaceDoor.LOCK)
	await _seconds(0.2)
	await _hold(&"ganzuas")
	var work: Workable = Workable.find(door.get_node("Bisagra/Cuerpo"), &"ganzuas")
	work.begin(_player)
	assert_true(LockpickView.is_open(), "se ve la cerradura")
	var view: LockpickView = LockpickView.active
	var result: Array = []
	view.finished.connect(func(opened: bool) -> void: result.append(opened))
	var targets: PackedFloat32Array = view.targets
	assert_true(targets.size() >= 4, "una cerradura tiene cuatro o cinco pines")
	for pin: int in targets.size():
		# Bajar la ganzúa, pasar al pin y subir despacio hasta su punto.
		view.move_pick(Vector2(0.0, 400.0))
		view.move_pick(Vector2((pin - view.side) / LockpickView.SIDE_PER_PIXEL, 0.0))
		assert_eq(view.current_pin(), pin)
		var steps: int = 12
		for _step: int in steps:
			view.move_pick(Vector2(0.0, -targets[pin] / LockpickView.LIFT_PER_PIXEL / steps))
			await _seconds(0.05)
		await _seconds(LockpickView.SET_SECONDS + 0.15)
		assert_true(view.set_pins[pin], "el pin %d se queda puesto" % pin)
	await _seconds(LockpickView.TURN_SECONDS + 0.3)
	assert_eq(result, [true], "gira y se abre")
	assert_false(LockpickView.is_open())
	await _seconds(0.2)
	assert_false(door.is_locked(), "abierta con las ganzúas")
	var loud: Array = _heard.filter(func(event: NoiseEvent) -> bool: return event.radius > 3.0)
	assert_true(loud.is_empty(), "sin ruido")


func test_forcing_the_picks_breaks_one() -> void:
	await _build_world()
	var door: SurfaceDoor = _door("puerta_forzada", SurfaceDoor.PADLOCK)
	await _seconds(0.2)
	var picks: Carryable = await _hold(&"ganzuas")
	Workable.find(door.get_node("Bisagra/Cuerpo"), &"ganzuas").begin(_player)
	var view: LockpickView = LockpickView.active
	var result: Array = []
	view.finished.connect(func(opened: bool) -> void: result.append(opened))
	# Arriba y abajo, deprisa, pasándose una y otra vez.
	for _shove: int in 80:
		if not LockpickView.is_open():
			break
		view.move_pick(Vector2(0.0, -300.0))
		await _seconds(0.05)
		view.move_pick(Vector2(0.0, 300.0))
		await _seconds(0.05)
	assert_eq(result, [false], "se parte")
	await _seconds(0.3)
	assert_true(door.is_locked(), "sigue cerrada")
	assert_almost(picks.state.condition, 1.0 - SurfaceDoor.PICK_WEAR, 0.01, "se gastan")


func test_fear_makes_the_tip_tremble() -> void:
	await _build_world()
	var door: SurfaceDoor = _door("puerta_miedo", SurfaceDoor.LOCK)
	await _seconds(0.2)
	await _hold(&"ganzuas")
	Workable.find(door.get_node("Bisagra/Cuerpo"), &"ganzuas").begin(_player)
	var view: LockpickView = LockpickView.active
	view.move_pick(Vector2(0.0, -100.0))
	var spread: float = 0.0
	for _frame: int in 30:
		await get_tree().process_frame
		spread = maxf(spread, absf(view.tip_height() - view.lift))
	assert_almost(spread, 0.0, 0.001, "tranquilo, la punta va donde la llevas")
	_player.tremble = Fear.HANDS_TREMBLE
	for _frame: int in 30:
		await get_tree().process_frame
		spread = maxf(spread, absf(view.tip_height() - view.lift))
	assert_true(spread > LockpickView.TOLERANCE * 0.5, "con miedo tiembla (%.3f)" % spread)


func test_a_rope_tied_to_an_anchor_stays_and_takes_you_down() -> void:
	await _build_world()
	# Una azotea de 4 m con su anclaje en el borde (que da a +z).
	_box(Vector3(0.0, 2.0, -12.0), Vector3(6.0, 4.0, 6.0))
	var anchor: RopeAnchor = RopeAnchor.new()
	anchor.setup("anclaje_prueba", Transform3D(Basis(), Vector3(0.0, 4.0, -9.0)))
	_world.add_child(anchor)
	await _seconds(0.2)
	_player.global_position = Vector3(0.0, 4.05, -9.6)
	_player.rotation.y = PI
	await _hold(&"cuerda")
	var tie: Workable = Workable.find(anchor.get_node("Anclaje"), &"cuerda")
	assert_true(tie != null, "con la cuerda en la mano se ata")
	tie.work(_player, &"cuerda", 1.0)
	assert_false(anchor.is_tied(), "lleva su rato")
	tie.work(_player, &"cuerda", 1.0)
	await _seconds(0.3)
	assert_true(anchor.is_tied(), "atada")
	assert_true(_player.held_item() == null, "la cuerda se ha gastado")
	assert_true(anchor.climbable() != null, "cuelga hasta el suelo")
	if anchor.climbable() != null:
		assert_almost(anchor.climbable().height, 4.0, 0.1)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(0.3)
	assert_true(_player.is_climbing(), "andando hacia el borde se agarra")
	await _seconds(8.0)
	_player.scripted_input = Vector2.ZERO
	assert_false(_player.is_climbing())
	assert_true(_player.global_position.y < 0.3, "abajo")
	assert_eq(_state.value("anclaje_prueba", "atada", false), true, "se queda puesta")


func _door(id: String, lock: StringName, at: Vector3 = Vector3(-0.4, 0.0, -1.0)) -> SurfaceDoor:
	var door: SurfaceDoor = SurfaceDoor.new()
	door.initial_lock = lock
	door.setup(id, Transform3D(Basis(), at), Vector3(0.8, 2.0, 0.05))
	_world.add_child(door)
	return door


func _kinds() -> Array[StringName]:
	var kinds: Array[StringName] = []
	for event: NoiseEvent in _heard:
		kinds.append(event.kind)
	return kinds


func _hold(item_id: StringName) -> Carryable:
	var held: Carryable = _player.held_item()
	if held != null:
		_items.remove_item(held)
		await _seconds(0.2)
	var item: Carryable = _items.give(_player, item_id)
	await _seconds(0.5)
	return item


## Un suelo, el mundo (el estado de las cosas fijas), los estímulos, los objetos y un
## jugador que mira al norte (-z), con la puerta delante.
func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(60.0, 1.0, 60.0))
	_state = DepotWorld.new()
	_state.save_key = "superficie_prueba"
	_world.add_child(_state)
	var stimuli: Stimuli = Stimuli.new()
	_world.add_child(stimuli)
	stimuli.noise_made.connect(func(event: NoiseEvent) -> void: _heard.append(event))
	_items = WorldItems.new()
	_items.save_key = "objetos_prueba"
	_world.add_child(_items)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	_player.global_position = Vector3(0.0, 0.0, 0.0)
	await _seconds(0.2)


func _box(center: Vector3, box_size: Vector3) -> StaticBody3D:
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = box_size
	shape.shape = box
	body.add_child(shape)
	body.position = center
	_world.add_child(body)
	return body


func _seconds(seconds: float) -> void:
	for _i in int(seconds * 60.0):
		await get_tree().physics_frame
