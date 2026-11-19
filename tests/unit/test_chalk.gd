extends "res://tests/test_case.gd"
## La tiza (F3-08): mirando una pared a mano, mantener el botón dibuja una marca; la
## rueda cambia de símbolo; las marcas se guardan con el mundo y las ve cualquiera.

var _world: Node3D
var _player: Player
var _items: WorldItems
var _surface: DepotWorld
var _marks: ChalkMarks


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")


func after_each() -> void:
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_drawing_a_mark_on_a_wall() -> void:
	await _build_world()
	var chalk: Carryable = _items.give(_player, &"tiza")
	await _seconds(0.5)
	assert_eq(_player.held_item(), chalk)
	EventBus.item_adjusted.emit(_player, chalk, 1)
	await _seconds(0.1)
	assert_eq(int(chalk.state.extra.get("simbolo", 0)), 1, "la rueda cambia de símbolo")
	var drawer: PlayerChalk = PlayerChalk.new()
	drawer.update(_player, 0.016, false)
	assert_true(drawer.aiming, "mira la pared, a mano")
	for _i in 60:
		drawer.update(_player, 1.0 / 60.0, true)
		await get_tree().process_frame
	await _seconds(0.1)
	assert_eq(_marks.marks().size(), 1, "una marca en la pared")
	if not _marks.marks().is_empty():
		assert_eq(int(_marks.marks()[0]["s"]), 1, "con su símbolo")
	var saved: Dictionary = _surface.save_state()
	_surface.load_state({})
	assert_eq(_marks.marks().size(), 0)
	_surface.load_state(saved)
	assert_eq(_marks.marks().size(), 1, "se guarda con el mundo")
	# Lejos, no se dibuja.
	_marks.request_mark(_player.eye_position() + Vector3(0.0, 0.0, -9.0), Vector3.BACK, 0)
	assert_eq(_marks.marks().size(), 1, "fuera del alcance no vale")


func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(40.0, 1.0, 40.0))
	_box(Vector3(0.0, 1.5, -1.6), Vector3(6.0, 3.0, 0.3))
	_surface = DepotWorld.new()
	_surface.save_key = "superficie_prueba"
	_world.add_child(_surface)
	_items = WorldItems.new()
	_items.save_key = "objetos_prueba"
	_world.add_child(_items)
	_marks = ChalkMarks.new()
	_marks.setup(_surface)
	_world.add_child(_marks)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	_player.rotation.y = 0.0
	await _seconds(0.3)


func _box(center: Vector3, size: Vector3) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = center
	_world.add_child(body)


func _seconds(seconds: float) -> void:
	for _i in int(seconds * 60.0):
		await get_tree().physics_frame
