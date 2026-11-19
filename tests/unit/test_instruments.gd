extends "res://tests/test_case.gd"
## Los instrumentos (F3-05): la brújula señala el norte, el podómetro cuenta los pasos
## desde que se pone a cero, el reloj de pulsera marca la hora de la partida y los
## prismáticos acercan.

var _world: Node3D
var _player: Player
var _items: WorldItems


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 9.0 * 60.0 + 15.0


func after_each() -> void:
	Input.action_release(&"use_secondary")
	Input.action_release(&"watch")
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_the_compass_points_north() -> void:
	await _build_world()
	_player.rotation.y = -PI * 0.5
	var compass: Carryable = await _hold(&"brujula")
	await _seconds(3.0)
	var needle: Node3D = compass.visual().find_child("aguja", true, false) as Node3D
	assert_true(needle != null, "la brújula tiene aguja")
	if needle != null:
		var pointing: Vector3 = -needle.global_basis.z
		pointing.y = 0.0
		assert_true(
			pointing.normalized().dot(Vector3.FORWARD) > 0.97, "mire uno a donde mire, al norte"
		)


func test_the_pedometer_counts_steps_from_zero() -> void:
	await _build_world()
	var meter: Carryable = await _hold(&"podometro")
	var view: InstrumentView = (
		meter.visual().find_child("Instrumento", true, false) as InstrumentView
	)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(1.5)
	_player.scripted_input = Vector2.ZERO
	await _seconds(0.3)
	assert_true(view.steps() > 0, "lleva pasos contados")
	var reset: Workable = Workable.find(meter.body(), &"podometro")
	reset.work(_player, &"podometro", 1.1)
	await _seconds(0.2)
	assert_eq(view.steps(), 0, "a cero")
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(3.0)
	_player.scripted_input = Vector2.ZERO
	assert_true(view.steps() >= 6, "andando 3 s cuenta los pasos (%d)" % view.steps())
	assert_eq(view.steps(), _player.footsteps.steps - int(meter.state.extra.get("base", 0)))


func test_the_watch_and_the_binoculars() -> void:
	await _build_world()
	Input.action_press(&"watch")
	await _seconds(0.5)
	var watch: Node3D = _player.optics.find_child("Reloj", true, false) as Node3D
	if watch == null:
		watch = get_viewport().get_camera_3d().find_child("Reloj", true, false) as Node3D
	assert_true(watch != null and watch.visible, "con R se ve el reloj")
	if watch != null:
		var minutes: Node3D = watch.find_child("aguja_minutos", true, false) as Node3D
		assert_almost(minutes.rotation.y, -TAU * 15.0 / 60.0, 0.01, "las nueve y cuarto")
	Input.action_release(&"watch")
	await _hold(&"prismaticos")
	Input.action_press(&"use_secondary")
	await _seconds(0.6)
	var camera: Camera3D = get_viewport().get_camera_3d()
	assert_true(camera.fov < 20.0, "por los prismáticos se ve de cerca (%.1f°)" % camera.fov)
	assert_false(_player.inspecting, "no se inspeccionan: se mira por ellos")
	Input.action_release(&"use_secondary")
	await _seconds(0.6)
	assert_almost(camera.fov, Player.FOV, 0.5, "y al bajarlos, como antes")


func _hold(item_id: StringName) -> Carryable:
	if _player.held_item() != null:
		_items.remove_item(_player.held_item())
		await _seconds(0.1)
	var item: Carryable = _items.give(_player, item_id)
	await _seconds(0.5)
	return item


func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(100.0, 1.0, 100.0)
	shape.shape = box
	body.add_child(shape)
	body.position = Vector3(0.0, -0.5, 0.0)
	_world.add_child(body)
	_items = WorldItems.new()
	_items.save_key = "objetos_prueba"
	_world.add_child(_items)
	var loose: SurfaceItems = SurfaceItems.new()
	loose.setup(_items)
	_world.add_child(loose)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	await _seconds(0.2)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _seconds(seconds: float) -> void:
	for _i in int(seconds * 60.0):
		await get_tree().physics_frame
