extends "res://tests/test_case.gd"
## El jugador en la superficie (F3-01): agacharse, correr con aliento, asomarse
## y el ruido de los pasos. Con un jugador de verdad sobre un suelo de prueba.

var _world: Node3D
var _floor: StaticBody3D
var _player: Player
var _noises: Array[float] = []


func before_each() -> void:
	_world = Node3D.new()
	_world.name = "MundoDePrueba"
	add_child(_world)
	_floor = _block(Vector3(40.0, 1.0, 40.0), Vector3(0.0, -0.5, 0.0))
	_player = Player.new()
	_player.setup(multiplayer.get_unique_id(), "chico", 0)
	_player.surface = true
	_world.add_child(_player)
	_noises.clear()
	EventBus.noise_made.connect(_on_noise)
	await _frames(10)


func after_each() -> void:
	EventBus.noise_made.disconnect(_on_noise)
	_world.free()


func test_gait_and_step_noise() -> void:
	assert_eq(SurfaceMotion.gait_of(0.1, false, false), SurfaceMotion.Gait.STILL)
	assert_eq(
		SurfaceMotion.gait_of(1.0, true, true), SurfaceMotion.Gait.CROUCH, "agachado no corre"
	)
	assert_eq(SurfaceMotion.gait_of(4.0, false, true), SurfaceMotion.Gait.RUN)
	var crouch: float = SurfaceMotion.step_noise(SurfaceMotion.Gait.CROUCH, 0.0, 0.0)
	var walk: float = SurfaceMotion.step_noise(SurfaceMotion.Gait.WALK, 0.0, 0.0)
	var run: float = SurfaceMotion.step_noise(SurfaceMotion.Gait.RUN, 0.0, 0.0)
	assert_true(crouch < walk and walk < run, "agachado, andando y corriendo, de menos a más")
	var loaded: float = SurfaceMotion.step_noise(SurfaceMotion.Gait.WALK, 20.0, 0.0)
	var rattling: float = SurfaceMotion.step_noise(SurfaceMotion.Gait.WALK, 0.0, 2.0)
	assert_true(loaded > walk, "cargado se oye más")
	assert_true(rattling > walk, "con latas sueltas en la mochila, también")
	assert_almost(SurfaceMotion.step_noise(SurfaceMotion.Gait.STILL, 30.0, 3.0), 0.0)


func test_breath_runs_out_and_comes_back() -> void:
	var motion: SurfaceMotion = SurfaceMotion.new()
	var heavy: SurfaceMotion = SurfaceMotion.new()
	for _i in 30:
		motion.update_breath(0.1, true, true, 0.0)
		heavy.update_breath(0.1, true, true, 20.0)
	assert_true(heavy.breath < motion.breath, "cargado se queda antes sin aliento")
	while not motion.winded:
		motion.update_breath(0.1, true, true, 0.0)
	assert_false(motion.can_run(), "sin aliento no se puede correr")
	assert_true(motion.heave() > 0.9, "y se le nota en la respiración")
	motion.update_breath(1.0, false, false, 0.0)
	assert_false(motion.can_run(), "hasta recuperar un poco, tampoco")
	for _i in 30:
		motion.update_breath(0.1, false, false, 0.0)
	assert_true(motion.can_run(), "parado, el aliento vuelve")


func test_running_is_faster_and_costs_breath() -> void:
	var walked: float = await _move_for(0.8, false)
	var ran: float = await _move_for(0.8, true)
	assert_true(
		ran > walked * 1.5,
		"corriendo se llega mucho más lejos (%.2f m frente a %.2f)" % [ran, walked]
	)
	assert_true(_player.motion.breath < 0.95, "y se gasta aliento")


func test_crouching_lowers_the_eyes_and_quiets_the_steps() -> void:
	await _move_for(2.0, false)
	var walking: Array[float] = _noises.duplicate()
	_player.set_crouching(true)
	await _frames(30)
	assert_true(_player.crouching)
	assert_true(_head().position.y < _player.standing_eyes() * 0.7, "los ojos bajan")
	_noises.clear()
	await _move_for(2.0, false)
	assert_true(walking.size() > 0 and _noises.size() > 0, "andando y agachado se oyen pasos")
	assert_true(_noises.size() < walking.size(), "agachado se dan menos pasos")
	assert_true(_noises.max() < walking.min(), "y suenan menos")
	_player.set_crouching(false)
	assert_false(_player.crouching, "sin nada encima se levanta")


func test_cannot_stand_up_under_something() -> void:
	_player.set_crouching(true)
	await _frames(5)
	_block(Vector3(3.0, 0.2, 3.0), _player.global_position + Vector3(0.0, 1.3, 0.0))
	await _frames(3)
	_player.set_crouching(false)
	assert_true(_player.crouching, "debajo de una mesa no se puede poner de pie")


func test_leaning_moves_the_head_but_not_into_a_wall() -> void:
	_player.scripted_lean = 1.0
	await _frames(40)
	assert_almost(_head().position.x, SurfaceMotion.LEAN_DISTANCE, 0.02, "se asoma a la derecha")
	_player.scripted_lean = -1.0
	var wall: Vector3 = _player.global_position - _player.global_basis.x * 0.42 + Vector3.UP * 1.5
	_block(Vector3(0.2, 3.0, 3.0), wall)
	await _frames(40)
	var room: float = 0.42 - 0.1 - SurfaceMotion.LEAN_CLEARANCE
	assert_true(_head().position.x > -room - 0.03, "la pared de la izquierda le para la cabeza")
	assert_true(_head().position.x < -0.02, "pero algo se asoma")


func test_broken_glass_is_louder_than_snow() -> void:
	_floor.set_meta(SurfaceMotion.GROUND_META, &"nieve")
	await _move_for(1.5, false)
	assert_eq(_player.ground_kind(), &"nieve")
	var snow: Array[float] = _noises.duplicate()
	_noises.clear()
	var glass: Area3D = Area3D.new()
	glass.collision_layer = 1 << 5
	glass.monitoring = false
	glass.set_meta(SurfaceMotion.GROUND_META, &"cristales")
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(10.0, 0.2, 10.0)
	shape.shape = box
	glass.add_child(shape)
	_world.add_child(glass)
	await _move_for(1.5, false)
	assert_eq(_player.ground_kind(), &"cristales", "pisa los cristales, no la nieve de debajo")
	assert_true(snow.size() > 0 and _noises.size() > 0)
	assert_true(_noises.min() > snow.max() * 2.0, "sobre cristales, cada paso suena mucho más")


func test_others_see_the_posture() -> void:
	var avatar: PlayerAvatar = _player.get_node(^"Avatar") as PlayerAvatar
	_player.set_crouching(true)
	await _frames(5)
	assert_eq(avatar.animation(), &"agachado", "agachado y quieto")
	_player.scripted_input = Vector2(0.0, -1.0)
	await _frames(30)
	assert_eq(avatar.animation(), &"caminar_agachado", "andando agachado")
	_player.set_crouching(false)
	_player.scripted_run = true
	await _frames(40)
	assert_eq(avatar.animation(), &"correr", "corriendo")
	assert_eq(avatar.expression, &"esfuerzo", "y se le nota el esfuerzo en la cara")
	_player.scripted_run = false
	_player.scripted_input = Vector2.ZERO
	_player.scripted_lean = 1.0
	await _frames(40)
	assert_true(avatar.lean > 0.9, "el tronco se inclina al asomarse")
	assert_eq(avatar.expression, &"neutro")


func test_the_depot_stays_calm() -> void:
	_player.surface = false
	var calm: float = await _move_for(0.8, true)
	_player.surface = true
	var ran: float = await _move_for(0.8, true)
	assert_true(calm < ran * 0.7, "en el depósito no se corre (%.2f m frente a %.2f)" % [calm, ran])


## Anda hacia delante [param seconds] segundos (corriendo o no) desde el centro y
## devuelve lo que ha avanzado.
func _move_for(seconds: float, run: bool) -> float:
	_player.scripted_input = Vector2.ZERO
	_player.scripted_run = false
	_player.velocity = Vector3.ZERO
	_player.global_position = Vector3(0.0, 0.05, 0.0)
	await _frames(3)
	var start: Vector3 = _player.global_position
	_player.scripted_run = run
	_player.scripted_input = Vector2(0.0, -1.0)
	await get_tree().create_timer(seconds).timeout
	_player.scripted_input = Vector2.ZERO
	_player.scripted_run = false
	var moved: Vector3 = _player.global_position - start
	return Vector2(moved.x, moved.z).length()


func _head() -> Node3D:
	return _player.get_node(^"Cabeza") as Node3D


func _block(size: Vector3, where: Vector3) -> StaticBody3D:
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = where
	_world.add_child(body)
	return body


func _on_noise(_where: Vector3, loudness: float, source: Node) -> void:
	if source == _player:
		_noises.append(loudness)


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
