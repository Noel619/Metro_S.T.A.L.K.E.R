extends "res://tests/test_case.gd"
## Las heridas (F3-12) y el miedo (F3-11): un mordisco quita sangre y sangra hasta
## vendarlo; sin sangre se muere y, si mueren todos, se pierde la partida; ver un
## perro cerca da miedo, y un golpe, más.

var _world: Node3D
var _player: Player
var _items: WorldItems
var _wounds: Wounds
var _over: bool = false


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 12.0 * 60.0
	_over = false
	EventBus.game_over.connect(_on_game_over)


func after_each() -> void:
	EventBus.game_over.disconnect(_on_game_over)
	if _world != null:
		_world.free()
	StyleDirector.fear = 0.0
	GameState.reset_for_new_game("")


func test_a_bite_bleeds_until_bandaged() -> void:
	await _build_world()
	_wounds.bite(_player, Vector3(1.0, 0.5, 0.0))
	await _frames(5)
	assert_almost(_player.condition.blood, 1.0 - Wounds.BITE_LOSS, 0.01, "un mordisco quita sangre")
	assert_true(_player.condition.bleeding, "y sangra")
	var before: float = _player.condition.blood
	await _frames(120)
	assert_true(_player.condition.blood < before, "sigue perdiendo sangre")
	var tracks: Tracks = Tracks.find(get_tree())
	assert_false(tracks.freshest_near(_player.global_position, 2.0, true).is_empty(), "y gotea")
	# Las vendas en la mano y el botón izquierdo mantenido tres segundos.
	var bandage: Carryable = _items.give(_player, &"vendas")
	await _frames(30)
	assert_eq(_player.held_item(), bandage)
	var own: Workable = Workable.find(bandage.body(), &"vendas")
	assert_true(own != null and own.self_use, "las vendas se usan sobre uno mismo")
	for _i in 4:
		own.work(_player, &"vendas", 1.0)
	await _frames(10)
	assert_false(_player.condition.bleeding, "vendado, deja de sangrar")
	assert_true(_player.held_item() == null, "las vendas se gastan")
	var after: float = _player.condition.blood
	await _frames(120)
	assert_almost(_player.condition.blood, after, 0.0001, "y ya no pierde sangre")


func test_without_blood_you_die_and_the_game_is_lost() -> void:
	await _build_world()
	for _i in 7:
		_wounds.bite(_player, Vector3.ZERO)
	await _frames(5)
	assert_true(_player.condition.dead, "sin sangre, muere")
	assert_true(_over, "muertos todos, se pierde la partida")


func test_seeing_a_dog_close_is_frightening() -> void:
	await _build_world()
	var fear: Fear = Fear.new()
	fear.setup(_player)
	_player.add_child(fear)
	await _frames(30)
	assert_true(fear.level < 0.05, "a pleno día, sin nada cerca, tranquilo")
	_player.condition.notify_hurt(Vector3.ZERO)
	await _frames(20)
	assert_true(fear.level > 0.3, "un golpe asusta (%.2f)" % fear.level)
	var dog: Dog = Dog.new()
	dog.setup("negro", 0, 1.0)
	_world.add_child(dog)
	dog.global_position = _player.global_position + Vector3(0.0, 0.3, -8.0)
	dog.stop(&"grunir")
	await _frames(90)
	assert_true(fear.level > 0.4, "un perro gruñendo a 8 m da miedo (%.2f)" % fear.level)
	assert_almost(StyleDirector.fear, fear.level, 0.001, "y se nota en el dibujo")
	assert_true(_player.tremble > 0.0, "y en las manos")


func _on_game_over() -> void:
	_over = true


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
	_world.add_child(Stimuli.new())
	_world.add_child(Tracks.new())
	_items = WorldItems.new()
	_items.save_key = "objetos_prueba"
	_world.add_child(_items)
	_wounds = Wounds.new()
	_world.add_child(_wounds)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
	_player.global_position = Vector3(0.0, 0.0, 0.0)
	await _frames(10)


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
