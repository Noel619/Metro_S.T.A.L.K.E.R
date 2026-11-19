extends "res://tests/test_case.gd"
## Las distracciones (F3-07): lo que se lanza suena al caer según lo que es y dónde
## cae (una botella en el granito se rompe), el despertador suena cuando se le acaba
## la cuerda, y un ruido lejos de ti lleva a la manada a mirar allí.

var _world: Node3D
var _player: Player
var _items: WorldItems
var _heard: Array[NoiseEvent] = []


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 12.0 * 60.0
	_heard.clear()


func after_each() -> void:
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_a_thrown_can_clanks_where_it_lands() -> void:
	await _build_world()
	var can: Carryable = await _hold(&"lata_vacia")
	PlayerThrow.throw(_player, 1.0)
	await _seconds(0.2)
	assert_true(_player.held_item() == null, "ha salido de la mano")
	assert_true(can.body().linear_velocity.length() > 5.0, "y vuela")
	await _seconds(2.5)
	var clank: Array = _heard.filter(func(event: NoiseEvent) -> bool: return event.kind == &"golpe")
	assert_false(clank.is_empty(), "al caer suena")
	if not clank.is_empty():
		var landed: NoiseEvent = clank[0]
		assert_true(landed.position.distance_to(_player.global_position) > 6.0, "lejos de ti")


func test_a_bottle_breaks_on_stone() -> void:
	await _build_world()
	await _hold(&"botella_verde")
	_player.rotation.y = PI * 0.5
	PlayerThrow.throw(_player, 1.0)
	await _seconds(2.5)
	var glass: Array = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == &"cristal"
	)
	assert_false(glass.is_empty(), "contra el granito se rompe")
	if not glass.is_empty():
		assert_almost((glass[0] as NoiseEvent).radius, NoiseRules.sound_radius(&"cristal"), 0.01)
	var broken: bool = false
	for item: Carryable in _items.items():
		if item.state.data.id == &"botella_rota":
			broken = true
	assert_true(broken, "y quedan los cristales")
	var soft: Dictionary = SurfaceItems.landing_noise(ItemState.load_data(&"trapo"), 5.0, &"nieve")
	assert_true(float(soft["radius"]) < 2.0, "un trapo no se oye")


func test_the_alarm_clock_rings_when_wound_out() -> void:
	await _build_world()
	var clock: Carryable = await _hold(&"despertador")
	var own: Workable = Workable.find(clock.body(), &"despertador")
	assert_true(own != null and own.self_use, "se le da cuerda en la mano")
	own.work(_player, &"despertador", 2.0)
	assert_almost(
		float(clock.state.extra.get("cuerda", 0.0)), 4.0, 0.01, "dos vueltas, dos minutos"
	)
	_player.interact()
	await _seconds(6.0)
	var rings: Array = _heard.filter(
		func(event: NoiseEvent) -> bool: return event.kind == &"despertador"
	)
	assert_false(rings.is_empty(), "se acaba la cuerda y suena")
	if not rings.is_empty():
		assert_almost(
			(rings[0] as NoiseEvent).radius, NoiseRules.sound_radius(&"despertador"), 0.01
		)


func test_a_noise_away_from_you_draws_the_pack() -> void:
	await _build_world()
	# Tú, lejos, fuera de su vista (en campo abierto se te recortaría contra el cielo).
	_player.global_position = Vector3(60.0, 0.0, 80.0)
	var dogs: Array[Dog] = []
	var nav: CityNav = CityNav.empty(Rect2i(-150, -150, 300, 300))
	for index: int in 3:
		var dog: Dog = Dog.new()
		dog.setup(Pack.COATS[index], index, 1.0)
		dog.nav = nav
		_world.add_child(dog)
		dog.global_position = Vector3(-40.0, 0.4, -40.0) + Pack.ring_offset(index, 2.0)
		dogs.append(dog)
	var pack: Pack = Pack.new()
	pack.hold_routine = true
	_world.add_child(pack)
	pack.set_dogs(dogs)
	pack.force_mode(Pack.Mode.RONDA)
	await _seconds(0.5)
	var stimuli: Stimuli = Stimuli.find(get_tree())
	stimuli.make_noise(Vector3(-40.0, 0.2, -25.0), NoiseRules.sound_radius(&"cristal"), &"cristal")
	await _seconds(1.0)
	assert_eq(pack.mode, Pack.Mode.INVESTIGAR, "van a ver qué ha sido")
	if pack.target() != null:
		assert_true(pack.target().position.distance_to(Vector3(-40.0, 0.2, -25.0)) < 6.0, "allí")
	assert_true(pack.memory.is_fair())


func _hold(item_id: StringName) -> Carryable:
	var item: Carryable = _items.give(_player, item_id)
	await _seconds(0.5)
	return item


## Un campo de nieve con un patio de granito (al este, x > 4), los estímulos, las cosas
## sueltas y un jugador que mira al norte.
func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(200.0, 1.0, 200.0))
	var stone: StaticBody3D = _box(Vector3(20.0, -0.45, 0.0), Vector3(30.0, 1.0, 40.0))
	stone.set_meta(Ground.META, &"granito")
	var stimuli: Stimuli = Stimuli.new()
	_world.add_child(stimuli)
	stimuli.noise_made.connect(func(event: NoiseEvent) -> void: _heard.append(event))
	_world.add_child(Tracks.new())
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
	_player.global_position = Vector3(0.0, 0.0, 0.0)
	_player.rotation.y = 0.0
	await _seconds(0.2)


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


func _seconds(seconds: float) -> void:
	for _i in int(seconds * 60.0):
		await get_tree().physics_frame
