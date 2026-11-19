extends "res://tests/test_case.gd"
## Los tres escenarios de prueba de la Jauría (F3-10, README 7.7):
## 1. "Corres y te persiguen": verte quieto les hace tantear; correr, perseguirte y morder.
## 2. "Con el viento de cara pasas a 40 m sin que te huelan" (y con el viento a la espalda, sí).
## 3. "El cebo los entretiene y pasas".
## Y en todos, la prueba de justicia: cada decisión de la manada sale de algo percibido.

const DOG_SPOT: Vector3 = Vector3(0.0, 0.0, 0.0)

var _world: Node3D
var _player: Player
var _pack: Pack
var _items: WorldItems
var _env: SurfaceEnv
var _dogs: Array[Dog] = []


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 12.0 * 60.0
	_dogs.clear()


func after_each() -> void:
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_running_makes_them_chase_and_bite() -> void:
	await _build_arena(Weather.fixed(270.0, Weather.Wind.BRISA))
	# A 30 m, a su derecha, en campo abierto, de espaldas a ellos.
	_player.global_position = Vector3(30.0, 0.0, 0.0)
	_player.rotation.y = -PI * 0.5
	await _seconds(4.0)
	assert_true(
		_pack.mode == Pack.Mode.TANTEO or _pack.mode == Pack.Mode.RODEO,
		"te ven: tantean (%s)" % _pack.mode_name()
	)
	assert_true(_player.condition.blood >= 1.0, "aún no muerden")
	# Corre: se lanzan.
	_player.scripted_input = Vector2(0.0, -1.0)
	_player.scripted_run = true
	var chased: bool = false
	for _i in 30 * 60:
		await get_tree().physics_frame
		if _pack.mode == Pack.Mode.PERSECUCION:
			chased = true
		if _player.condition.blood < 1.0:
			break
	_player.scripted_input = Vector2.ZERO
	_player.scripted_run = false
	assert_true(chased, "correr delante de ellos los lanza")
	assert_true(_player.condition.blood < 1.0, "y muerden")
	assert_true(_player.condition.bleeding, "la mordedura sangra")
	assert_true(_pack.memory.is_fair(), "cada decisión sale de algo que percibieron")


func test_upwind_you_pass_unsmelled() -> void:
	# El viento viene de los perros (del sur) hacia ti: no te huelen.
	await _build_arena(Weather.fixed(180.0, Weather.Wind.VIENTO))
	_player.body.crouch_wanted = true
	_player.global_position = Vector3(-30.0, 0.0, -40.0)
	_player.rotation.y = -PI * 0.5
	await _seconds(0.5)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(20.0)
	_player.scripted_input = Vector2.ZERO
	assert_eq(_pack.mode, Pack.Mode.RONDA, "no se han enterado (%s)" % _pack.mode_name())
	assert_true(_pack.target() == null)
	# Con el viento a la espalda (del norte hacia ellos), sí.
	_env.override(Weather.fixed(0.0, Weather.Wind.VIENTO))
	await _seconds(3.0)
	assert_true(
		_pack.mode != Pack.Mode.RONDA, "con el viento a favor te huelen (%s)" % _pack.mode_name()
	)
	assert_true(_pack.memory.is_fair())


func test_bait_keeps_them_busy() -> void:
	await _build_arena(Weather.fixed(270.0, Weather.Wind.BRISA))
	_player.global_position = Vector3(25.0, 0.0, 0.0)
	await _seconds(4.0)
	assert_true(_pack.mode != Pack.Mode.RONDA, "te han visto")
	# El cebo, entre ellos y tú.
	_items.spawn_with(&"salo", Transform3D(Basis(), Vector3(8.0, 0.3, 0.0)))
	await _seconds(2.0)
	assert_eq(_pack.mode, Pack.Mode.COMER, "van a por el cebo")
	# Te alejas andando mientras comen.
	_player.rotation.y = -PI * 0.5
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(12.0)
	_player.scripted_input = Vector2.ZERO
	assert_eq(_pack.mode, Pack.Mode.COMER, "siguen comiendo")
	assert_almost(_player.condition.blood, 1.0, 0.001, "y pasas sin un rasguño")
	assert_true(_pack.memory.is_fair())


## Un campo con un muro (a 20 m al norte de los perros, que tapa la vista al que
## pasa detrás), los sistemas de la superficie, un jugador y la manada parada en
## el centro, despierta.
func _build_arena(weather: Weather) -> void:
	_world = Node3D.new()
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(300.0, 1.0, 300.0))
	_box(Vector3(0.0, 1.5, -20.0), Vector3(60.0, 3.0, 0.4))
	var stimuli: Stimuli = Stimuli.new()
	_world.add_child(stimuli)
	_env = SurfaceEnv.new()
	_world.add_child(_env)
	_env.override(weather)
	_world.add_child(Tracks.new())
	_items = WorldItems.new()
	_items.save_key = "objetos_prueba"
	_world.add_child(_items)
	_world.add_child(Wounds.new())
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	_player.global_position = Vector3(0.0, 0.0, 100.0)
	var nav: CityNav = CityNav.empty(Rect2i(-150, -150, 300, 300))
	# El muro, en coordenadas del plano (y = -z).
	nav.block_box(Vector2(0.0, 20.0), Vector2(60.0, 0.6), 0.0)
	for index: int in Pack.COATS.size():
		var dog: Dog = Dog.new()
		dog.setup(Pack.COATS[index], index, Pack.SIZES[index])
		dog.nav = nav
		_world.add_child(dog)
		dog.global_position = DOG_SPOT + Pack.ring_offset(index, 2.0) + Vector3.UP * 0.4
		_dogs.append(dog)
	_pack = Pack.new()
	_pack.hold_routine = true
	_world.add_child(_pack)
	_pack.set_dogs(_dogs)
	_pack.force_mode(Pack.Mode.RONDA)
	await _seconds(0.5)


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
