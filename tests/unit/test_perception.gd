extends "res://tests/test_case.gd"
## La percepción común (F3-09): la vista se fija poco a poco y no atraviesa muros
## ni la espalda; de noche solo delata la linterna; el oído pierde con los muros y
## el viento; el olfato depende de hacia dónde sopla; los rastros se encuentran con
## el hocico; la memoria olvida y junta; y la prueba de justicia.

var _world: Node3D
var _agent: StaticBody3D
var _perception: Perception
var _player: Player
var _stimuli: Stimuli
var _env: SurfaceEnv
var _tracks: Tracks


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 12.0 * 60.0


func after_each() -> void:
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_seeing_takes_a_moment() -> void:
	await _build_world()
	# Delante y a la derecha, fuera del muro, andando.
	_player.global_position = Vector3(12.0, 0.0, -12.0)
	_player.scripted_input = Vector2(1.0, 0.0)
	await _frames(8)
	assert_true(_perception.knowledge.fact("presa_1") == null, "de golpe no se ve a nadie")
	await _frames(90)
	var seen: Percept = _perception.knowledge.fact("presa_1")
	assert_true(seen != null, "en un segundo y medio, sí")
	if seen != null:
		assert_eq(seen.sense, Percept.SIGHT)
		assert_true(seen.position.distance_to(_player.global_position) < 2.0)
	_player.scripted_input = Vector2.ZERO


func test_walls_and_the_back_hide_you() -> void:
	await _build_world()
	# Detrás del muro (z = -10, de x = -5 a 5).
	_player.global_position = Vector3(0.0, 0.0, -14.0)
	_player.scripted_input = Vector2(1.0, 0.0)
	await _frames(20)
	_player.scripted_input = Vector2.ZERO
	_player.global_position = Vector3(0.0, 0.0, -14.0)
	await _frames(60)
	assert_almost(float(_perception.awareness.get(1, 0.0)), 0.0, 0.001, "tras el muro, nada")
	# A su espalda, en campo abierto.
	_player.global_position = Vector3(0.0, 0.0, 12.0)
	_player.scripted_input = Vector2(1.0, 0.0)
	await _frames(90)
	_player.scripted_input = Vector2.ZERO
	assert_almost(float(_perception.awareness.get(1, 0.0)), 0.0, 0.001, "a la espalda, nada")


func test_the_night_hides_and_the_torch_betrays() -> void:
	await _build_world()
	GameState.minute = 23.0 * 60.0
	_player.global_position = Vector3(30.0, 0.0, -30.0)
	_player.rotation.y = 0.0
	_player.scripted_input = Vector2(0.0, -1.0)
	await _frames(90)
	assert_true(_perception.knowledge.fact("presa_1") == null, "de noche, a 40 m, no se ve")
	# Con la linterna apuntando al perro: se ve desde muy lejos.
	_player.look_at(Vector3(0.0, _player.global_position.y, 0.0))
	_player.flashlight_on = true
	await _frames(90)
	_player.scripted_input = Vector2.ZERO
	assert_true(_perception.knowledge.fact("presa_1") != null, "la linterna delata")


func test_walls_and_wind_hide_noise() -> void:
	await _build_world()
	_perception.knowledge = Knowledge.new()
	_stimuli.make_noise(Vector3(8.0, 0.0, 0.0), 9.0, NoiseRules.STEP, 1, false)
	assert_eq(_heard(NoiseRules.STEP), 1, "un paso a 8 m se oye")
	# Detrás del muro: 9 × 1,3 × 0,35 = 4 m.
	_stimuli.make_noise(Vector3(0.0, 0.0, -14.0), 9.0, &"golpe", 1, false)
	assert_eq(_heard(&"golpe"), 0, "con un muro en medio, no")
	_env.override(Weather.fixed(270.0, Weather.Wind.VENTISCA, true))
	_stimuli.make_noise(Vector3(-8.0, 0.0, 0.0), 9.0, &"tos", 1, false)
	assert_eq(_heard(&"tos"), 0, "con ventisca, tampoco")
	_stimuli.make_noise(Vector3(-8.0, 0.0, 0.0), 30.0, &"cristal", 1, false)
	assert_eq(_heard(&"cristal"), 1, "un cristal roto, sí")


func test_the_wind_carries_the_smell() -> void:
	await _build_world()
	# Del oeste: el aire va hacia +X. El perro está en el origen.
	_env.override(Weather.fixed(270.0, Weather.Wind.VIENTO))
	_perception.sleeping = false
	_perception.fov_degrees = 0.0
	_player.global_position = Vector3(30.0, 0.0, 0.0)
	await _frames(20)
	assert_false(_smelled(), "a barlovento, a 30 m, no le huele")
	_player.global_position = Vector3(-30.0, 0.0, 0.0)
	await _frames(20)
	assert_true(_smelled(), "a sotavento, a 30 m, sí")
	assert_almost(
		Perception.smell_range(Weather.fixed(270.0, Weather.Wind.CALMA), Vector3(1, 0, 0)),
		15.0,
		0.001,
		"sin viento, en redondo"
	)


func test_trails_are_found_with_the_nose() -> void:
	await _build_world()
	_perception.fov_degrees = 0.0
	_tracks.drop(Vector3(1.5, 0.0, 0.5), 1)
	await _frames(20)
	var trail: Percept = _perception.knowledge.best([&"rastro"])
	assert_true(trail != null, "encuentra el rastro")
	if trail != null:
		assert_eq(trail.truth, 1)
	_tracks.drop(Vector3(40.0, 0.0, 0.0), 1, true)
	var blood: Dictionary = _tracks.freshest_near(Vector3(40.0, 0.0, 0.0), 1.0, true)
	assert_false(blood.is_empty())
	assert_true(_tracks.age_of(blood) < 0.01, "recién puesta")


func test_memory_forgets_and_joins() -> void:
	var memory: Knowledge = Knowledge.new()
	var seen: Percept = Percept.create(Percept.SIGHT, Vector3(10, 0, 0), 1.0, &"presa", 1.0)
	seen.subject = 2
	assert_eq(memory.remember(seen), "presa_2")
	var noise: Percept = Percept.create(Percept.HEARING, Vector3(13, 0, 0), 0.9, &"paso", 2.0)
	assert_eq(memory.remember(noise), "presa_2", "lo que oye cerca de lo que vio, es lo mismo")
	assert_eq(memory.fact("presa_2").subject, 2)
	var far: Percept = Percept.create(Percept.HEARING, Vector3(60, 0, 0), 0.5, &"golpe", 2.0)
	assert_true(memory.remember(far).begins_with("indicio"), "lejos, es otra cosa")
	memory.forget(5.0)
	assert_true(memory.fact("presa_2").certainty < 0.6, "se va olvidando")
	memory.forget(20.0)
	assert_true(memory.facts.is_empty(), "y al final se olvida")


func test_every_decision_comes_from_a_percept() -> void:
	var memory: Knowledge = Knowledge.new()
	var seen: Percept = Percept.create(Percept.SIGHT, Vector3(10, 0, 0), 1.0, &"presa", 1.0)
	memory.remember(seen)
	memory.decide(&"perseguir", seen)
	memory.decide(&"descansar")
	assert_true(memory.is_fair())
	var invented: Percept = Percept.create(Percept.SIGHT, Vector3(3, 0, 0), 1.0, &"presa", 1.0)
	memory.decide(&"ir_a", invented)
	assert_false(memory.is_fair(), "una decisión sin percepción detrás no es justa")


## Un campo con un muro delante del perro (en z = -10), los estímulos, el entorno,
## los rastros, un perro (un cuerpo en el origen mirando a -Z) y un jugador.
func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(300.0, 1.0, 300.0))
	_box(Vector3(0.0, 2.0, -10.0), Vector3(10.0, 4.0, 0.4))
	_stimuli = Stimuli.new()
	_world.add_child(_stimuli)
	_env = SurfaceEnv.new()
	_world.add_child(_env)
	_env.override(Weather.fixed(270.0, Weather.Wind.CALMA))
	_tracks = Tracks.new()
	_world.add_child(_tracks)
	_agent = StaticBody3D.new()
	_agent.name = "Perro"
	var shape: CollisionShape3D = CollisionShape3D.new()
	var sphere: SphereShape3D = SphereShape3D.new()
	sphere.radius = 0.3
	shape.shape = sphere
	shape.position.y = 0.5
	_agent.add_child(shape)
	_world.add_child(_agent)
	_perception = Perception.new()
	_perception.body = _agent
	_agent.add_child(_perception)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	_player.global_position = Vector3(100.0, 0.0, 100.0)
	await _frames(10)


func _heard(kind: StringName) -> int:
	var count: int = 0
	for key: String in _perception.knowledge.facts:
		var fact: Percept = _perception.knowledge.facts[key]
		if fact.sense == Percept.HEARING and fact.kind == kind:
			count += 1
	return count


func _smelled() -> bool:
	for key: String in _perception.knowledge.facts:
		var fact: Percept = _perception.knowledge.facts[key]
		if fact.sense == Percept.SMELL and fact.time > Stimuli.clock() - 0.25:
			return true
	return false


func _box(center: Vector3, size: Vector3) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = center
	_world.add_child(body)


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
