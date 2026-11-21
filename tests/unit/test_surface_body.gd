extends "res://tests/test_case.gd"
## El cuerpo en la superficie (F3-01) y lo que se te ve (F3-02): agacharse,
## correr con aliento, encaramarse, el ruido de los pasos según el suelo y la
## visibilidad según la luz, la sombra, la silueta y lo que te tapa.

var _world: Node3D
var _player: Player
var _stimuli: Stimuli
var _heard: Array[NoiseEvent] = []


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	_heard.clear()


func after_each() -> void:
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_running_spends_breath_and_needs_it_back() -> void:
	var body: PlayerBody = PlayerBody.new()
	body.can_run = true
	var seconds: float = 0.0
	while not body.exhausted and seconds < 20.0:
		body.update(0.1, true, true, 0.0, 0.0)
		seconds += 0.1
	assert_almost(seconds, 8.0, 0.25, "sin carga, el aliento dura unos 8 s corriendo")
	assert_false(body.running)
	assert_true(body.is_panting())
	body.update(0.1, true, true, 0.0, 0.0)
	assert_false(body.running, "sin aliento no se corre")
	for _i in 30:
		body.update(0.1, false, false, 0.0, 0.0)
	assert_true(body.breath >= PlayerBody.RECOVERED)
	body.update(0.1, true, true, 0.0, 0.0)
	assert_true(body.running, "con algo de aliento, se vuelve a correr")
	var loaded: PlayerBody = PlayerBody.new()
	loaded.can_run = true
	var loaded_seconds: float = 0.0
	while not loaded.exhausted and loaded_seconds < 20.0:
		loaded.update(0.1, true, true, 20.0, 0.0)
		loaded_seconds += 0.1
	assert_true(loaded_seconds < seconds - 1.0, "con 20 kg se acaba antes")


func test_crouching_is_slow_and_low_and_the_depot_does_not_run() -> void:
	var body: PlayerBody = PlayerBody.new()
	body.crouch_wanted = true
	for _i in 10:
		body.update(0.1, true, true, 0.0, 0.0)
	assert_true(body.is_crouched())
	assert_almost(body.target_speed(), PlayerBody.CROUCH_SPEED, 0.001)
	assert_almost(body.eye_share(), PlayerBody.CROUCH_EYES, 0.001)
	assert_false(body.running, "agachado no se corre")
	body.crouch_wanted = false
	body.update(0.1, false, false, 0.0, 0.0, false)
	assert_true(body.is_crouched(), "sin sitio encima, sigue agachado")
	var depot: PlayerBody = PlayerBody.new()
	depot.update(0.1, true, true, 0.0, 0.0)
	assert_false(depot.running, "en el depósito no se corre")
	assert_almost(depot.target_speed(), PlayerBody.WALK_SPEED, 0.001)


func test_steps_sound_by_gait_ground_and_load() -> void:
	var walk: float = NoiseRules.step_radius(PlayerBody.Gait.WALK, &"nieve")
	assert_almost(walk, 9.0, 0.001)
	assert_almost(NoiseRules.step_radius(PlayerBody.Gait.CROUCH, &"nieve"), 3.0, 0.001)
	assert_almost(NoiseRules.step_radius(PlayerBody.Gait.RUN, &"nieve"), 22.0, 0.001)
	assert_almost(NoiseRules.step_radius(PlayerBody.Gait.WALK, &"cristales"), 18.0, 0.001)
	assert_almost(NoiseRules.step_radius(PlayerBody.Gait.WALK, &"desconocido"), 9.0, 0.001)
	assert_almost(NoiseRules.step_radius(PlayerBody.Gait.WALK, &"nieve", 16.0), 9.0 * 1.2, 0.001)
	assert_eq(NoiseRules.step_radius(PlayerBody.Gait.STILL, &"nieve"), 0.0, "quieto no suena")
	assert_eq(NoiseRules.landing_radius(1.0, &"nieve"), 0.0, "un metro no suena")
	assert_almost(NoiseRules.landing_radius(2.0, &"chapa"), 2.0 * 4.0 * 1.8, 0.001)
	assert_eq(NoiseRules.rattle_radius(PlayerBody.Gait.CROUCH, 3), 0.0)
	assert_true(
		(
			NoiseRules.rattle_radius(PlayerBody.Gait.RUN, 1)
			> NoiseRules.rattle_radius(PlayerBody.Gait.WALK, 1)
		)
	)


func test_wind_and_walls_hide_noise() -> void:
	assert_almost(NoiseRules.heard_radius(20.0, Weather.Wind.CALMA, 0), 20.0, 0.001)
	assert_almost(NoiseRules.heard_radius(20.0, Weather.Wind.VIENTO, 0), 12.0, 0.001)
	assert_almost(NoiseRules.heard_radius(20.0, Weather.Wind.VENTISCA, 0), 7.0, 0.001)
	assert_almost(NoiseRules.heard_radius(20.0, Weather.Wind.CALMA, 1), 7.0, 0.001)
	assert_almost(NoiseRules.heard_radius(20.0, Weather.Wind.CALMA, 0, true), 10.0, 0.001)


func test_the_weather_of_a_day_is_the_same_everywhere() -> void:
	var a: Weather = Weather.at(4, 600.0)
	var b: Weather = Weather.at(4, 600.0)
	assert_almost(a.from_bearing, b.from_bearing, 0.0001)
	assert_eq(a.wind, b.wind)
	assert_eq(a.snowing, b.snowing)
	var west: Weather = Weather.fixed(270.0, Weather.Wind.VIENTO)
	var blowing: Vector2 = west.blowing_plan()
	assert_almost(blowing.x, 1.0, 0.001, "del oeste sopla hacia el este")
	assert_almost(blowing.y, 0.0, 0.001)
	assert_almost(west.blowing().z, 0.0, 0.001)
	var north: Weather = Weather.fixed(0.0, Weather.Wind.BRISA)
	assert_almost(north.blowing().z, 1.0, 0.001, "del norte (-Z) sopla hacia +Z")
	assert_eq(north.from_words(), "del norte")
	var days_with_snow: int = 0
	for day: int in range(1, 41):
		if Weather.at(day, 720.0).snowing:
			days_with_snow += 1
	assert_true(days_with_snow > 4 and days_with_snow < 30, "nieva algunos días, no todos")


func test_how_far_you_are_seen() -> void:
	var day: float = Visibility.sight_range(1.0, 0.0, 1.5, false)
	assert_almost(day, Visibility.BASE_RANGE, 0.001)
	var crouched_still: float = Visibility.sight_range(1.0, 1.0, 0.0, false)
	assert_almost(crouched_still, Visibility.BASE_RANGE * 0.55 * 0.5, 0.001)
	var dog: float = Visibility.sight_range(1.0, 1.0, 0.0, false, 1.0, true)
	assert_true(dog < crouched_still, "a quien ve el movimiento, quieto le cuesta más")
	assert_true(Visibility.sight_range(1.0, 0.0, 4.5, false) > day, "corriendo, más")
	assert_true(Visibility.sight_range(1.0, 0.0, 1.5, true) > day * 1.5, "contra el cielo")
	var night: float = Visibility.sight_range(Visibility.NIGHT_LIGHT, 0.0, 1.5, false)
	assert_true(night < 12.0, "de noche, sin linterna, casi nada")
	var torch: float = Visibility.sight_range(
		Visibility.NIGHT_LIGHT, 0.0, 1.5, false, 1.0, false, 2
	)
	assert_almost(torch, Visibility.TORCH_FACING, 0.001, "la linterna se ve desde muy lejos")
	var blizzard: float = Visibility.sight_range(1.0, 0.0, 1.5, false, 0.35)
	assert_almost(blizzard, day * 0.35, 0.001)
	assert_almost(Visibility.ambient(12.0), 1.0, 0.001)
	assert_almost(Visibility.ambient(2.0), Visibility.NIGHT_LIGHT, 0.001)
	assert_true(Visibility.ambient(17.5) < 1.0 and Visibility.ambient(17.5) > 0.3)


func test_walls_roofs_shade_and_sky_change_what_is_seen() -> void:
	await _build_world()
	var context: Dictionary = {
		"hour": 12.0, "sun": Vector3(0.0, 1.0, 1.0).normalized(), "weather": null
	}
	var space: PhysicsDirectSpaceState3D = _world.get_world_3d().direct_space_state
	# En campo abierto, de día y a 30 m: se te ve entero.
	_player.global_position = Vector3(0.0, 0.0, 0.0)
	await _frames(3)
	var open: Dictionary = Visibility.assess(space, Vector3(0.0, 1.6, 30.0), _player, context)
	assert_true(open["visible"], "a la vista")
	assert_almost(open["cover"], 1.0, 0.001)
	# Detrás del muro (en x = 10, entre z = -4 y 4), desde el otro lado: no.
	_player.global_position = Vector3(8.0, 0.0, 0.0)
	await _frames(3)
	var hidden: Dictionary = Visibility.assess(space, Vector3(14.0, 1.6, 0.0), _player, context)
	assert_false(hidden["visible"], "tras un muro no se te ve")
	assert_eq(hidden["cover"], 0.0)
	# Bajo el tejado (sobre x = -30): luz de dentro.
	_player.global_position = Vector3(-30.0, 0.0, 0.0)
	await _frames(3)
	var inside: Dictionary = Visibility.assess(space, Vector3(-30.0, 1.6, 20.0), _player, context)
	assert_almost(inside["light"], Visibility.INSIDE, 0.001, "bajo techo hay menos luz")
	# Encima de la caja alta, visto desde abajo: recortado contra el cielo.
	_player.global_position = Vector3(0.0, 4.0, -20.0)
	await _frames(3)
	var roof: Dictionary = Visibility.assess(space, Vector3(0.0, 1.6, 10.0), _player, context)
	assert_true(roof["silhouette"], "arriba, contra el cielo")
	assert_false(open["silhouette"], "en el suelo, detrás está el suelo")


func test_walking_makes_noise_that_the_host_hears() -> void:
	await _build_world()
	_player.global_position = Vector3(0.0, 0.0, 4.0)
	_player.rotation.y = 0.0
	await _frames(5)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _frames(90)
	_player.scripted_input = Vector2.ZERO
	var steps: Array[NoiseEvent] = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == NoiseRules.STEP
	)
	assert_true(steps.size() >= 3, "andar 1,5 s son varios pasos (%d)" % steps.size())
	assert_true(_player.footsteps.steps >= 3, "el podómetro los cuenta")
	if not steps.is_empty():
		assert_almost(steps[0].radius, 9.0, 0.01, "en la nieve, andando, 9 m")
		assert_eq(steps[0].source, _player.peer_id)
	var ripples: InkRipples = InkRipples.find(get_tree())
	assert_true(ripples.ring_count() > 0, "los pasos se ven como ondas de tinta")


func test_crouched_steps_are_quiet_and_metal_is_loud() -> void:
	await _build_world()
	_player.body.crouch_wanted = true
	_player.global_position = Vector3(0.0, 0.0, 4.0)
	await _frames(20)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _frames(120)
	var quiet: Array[NoiseEvent] = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == NoiseRules.STEP
	)
	assert_false(quiet.is_empty(), "agachado también suena")
	if not quiet.is_empty():
		assert_almost(quiet[-1].radius, 3.0, 0.01, "agachado, 3 m")
	_player.body.crouch_wanted = false
	_heard.clear()
	_player.global_position = Vector3(20.0, 0.1, 4.0)
	await _frames(40)
	await _frames(60)
	var loud: Array[NoiseEvent] = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == NoiseRules.STEP
	)
	assert_false(loud.is_empty())
	if not loud.is_empty():
		assert_almost(loud[-1].radius, 9.0 * 1.8, 0.01, "la chapa suena casi el doble")
	_player.scripted_input = Vector2.ZERO


func test_running_is_fast_and_loud_until_breath_runs_out() -> void:
	await _build_world()
	_player.global_position = Vector3(0.0, 0.0, 8.0)
	await _frames(5)
	_player.scripted_input = Vector2(0.0, -1.0)
	_player.scripted_run = true
	await _frames(60)
	assert_true(_player.move_speed > 4.0, "corre (%.1f m/s)" % _player.move_speed)
	assert_true(_player.body.breath < 1.0, "gasta aliento")
	var running: Array[NoiseEvent] = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == NoiseRules.STEP
	)
	assert_false(running.is_empty())
	if not running.is_empty():
		assert_almost(running[-1].radius, 22.0, 0.01, "corriendo, 22 m")
	_player.scripted_input = Vector2.ZERO
	_player.scripted_run = false


func test_the_head_stays_down_under_a_low_ceiling() -> void:
	await _build_world()
	_player.global_position = Vector3(-10.0, 0.0, 6.0)
	_player.body.crouch_wanted = true
	await _frames(30)
	var standing_eyes: float = Player.EYE_HEIGHTS["chico"]
	assert_true(_player.eye_position().y < standing_eyes * 0.7, "agachado, los ojos bajan")
	assert_true(_player.body_height() < 1.2)
	# Debajo de la losa baja (a 1,3 m) no se puede levantar.
	_player.global_position = Vector3(-10.0, 0.0, 0.0)
	await _frames(5)
	_player.body.crouch_wanted = false
	await _frames(30)
	assert_true(_player.crouch > 0.9, "sin sitio encima, sigue agachado")
	_player.global_position = Vector3(-10.0, 0.0, 8.0)
	await _frames(30)
	assert_true(_player.crouch < 0.05, "fuera, se levanta")


func test_climbing_onto_a_waist_high_box() -> void:
	await _build_world()
	# La caja de 1 m está en z = 12 (de 11,5 a 12,5), delante de quien mira a -Z.
	_player.global_position = Vector3(10.0, 0.0, 13.0)
	_player.rotation.y = 0.0
	await _frames(5)
	_player.set("_jump_queued", true)
	await _frames(50)
	assert_true(_player.global_position.y > 0.9, "encaramado (%.2f)" % _player.global_position.y)
	assert_true(_player.global_position.z < 12.6)


func test_leaning_stops_at_the_wall() -> void:
	await _build_world()
	# Pegado al muro de x = 10 por su lado izquierdo: a la derecha está el muro.
	_player.global_position = Vector3(9.5, 0.0, 0.0)
	_player.rotation.y = 0.0
	await _frames(5)
	var free: float = PlayerMoves.free_lean(_player, 1.0)
	assert_true(free < 0.6, "no se mete la cabeza en el muro (%.2f)" % free)
	var other_side: float = PlayerMoves.free_lean(_player, -1.0)
	assert_almost(other_side, -1.0, 0.001, "hacia el otro lado, del todo")


## Un campo de nieve con un muro, una losa baja, un tejado, una caja alta, una caja
## a la altura de la cintura y un trozo de chapa; los estímulos y las ondas; y un
## jugador con las reglas de la superficie.
func _build_world() -> void:
	_world = Node3D.new()
	_world.name = "Mundo"
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(200.0, 1.0, 200.0))
	_box(Vector3(10.0, 2.0, 0.0), Vector3(0.4, 4.0, 8.0))
	_box(Vector3(-10.0, 1.45, 0.0), Vector3(4.0, 0.3, 4.0))
	_box(Vector3(-30.0, 3.15, 0.0), Vector3(6.0, 0.3, 6.0))
	_box(Vector3(0.0, 2.0, -20.0), Vector3(4.0, 4.0, 4.0))
	_box(Vector3(10.0, 0.5, 12.0), Vector3(2.0, 1.0, 1.0))
	var metal: StaticBody3D = _box(Vector3(20.0, -0.45, 0.0), Vector3(6.0, 1.0, 12.0))
	metal.set_meta(Ground.META, &"chapa")
	_stimuli = Stimuli.new()
	_world.add_child(_stimuli)
	_stimuli.noise_made.connect(func(event: NoiseEvent) -> void: _heard.append(event))
	_world.add_child(InkRipples.new())
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	await _frames(10)


func _box(center: Vector3, size: Vector3) -> StaticBody3D:
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = center
	_world.add_child(body)
	return body


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
