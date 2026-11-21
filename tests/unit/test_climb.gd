extends "res://tests/test_case.gd"
## Trepar (F3-06, F3-14): por una escalera de pates se sube a una azotea empujando
## hacia ella, arriba se sale al rellano, y desde el rellano, andando hacia el borde,
## se agarra uno (mirando abajo) para bajar hasta el suelo.

const ROOF: float = 3.0

var _world: Node3D
var _player: Player
var _ladder: Climbable


func after_each() -> void:
	if _world != null:
		_world.free()


func test_up_the_ladder_and_onto_the_roof() -> void:
	await _build_world()
	_player.global_position = Vector3(0.0, 0.0, 0.6)
	_player.rotation.y = 0.0
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(1.0)
	assert_true(_player.is_climbing(), "empujando hacia ella se agarra")
	assert_true(_player.global_position.y > 0.5, "y sube")
	assert_true(_player.climbing, "los demás lo ven trepar")
	var avatar: PlayerAvatar = _player.get("_avatar")
	var animation: AnimationPlayer = avatar.get("_player") if avatar != null else null
	if animation != null:
		assert_eq(animation.current_animation, &"trepar", "con su animación")
	await _seconds(4.0)
	_player.scripted_input = Vector2.ZERO
	await _seconds(0.5)
	assert_false(_player.is_climbing(), "arriba la suelta")
	assert_almost(_player.global_position.y, ROOF, 0.15, "en la azotea")
	assert_true(_player.global_position.z < -0.2, "pasado el borde")


func test_down_from_the_roof() -> void:
	await _build_world()
	# En la azotea, junto al borde, mirando hacia fuera (de espaldas a la escalera).
	_player.global_position = Vector3(0.0, ROOF + 0.05, -0.6)
	_player.rotation.y = PI
	await _seconds(0.3)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(0.3)
	assert_true(_player.is_climbing(), "andando hacia el borde se agarra")
	assert_true(_player.head_pitch < -0.35, "mirando abajo")
	# Mirando abajo, adelante es bajar.
	await _seconds(4.0)
	assert_false(_player.is_climbing(), "abajo la suelta")
	assert_true(_player.global_position.y < 0.2, "en el suelo")
	assert_true(_player.is_on_floor())
	await _seconds(0.2)
	assert_true(
		_player.footsteps.last_fall < 0.5, "bajar no es caerse (%.2f)" % _player.footsteps.last_fall
	)


func test_letting_go_falls() -> void:
	await _build_world()
	_player.global_position = Vector3(0.0, 0.0, 0.6)
	_player.scripted_input = Vector2(0.0, -1.0)
	await _seconds(1.2)
	_player.scripted_input = Vector2.ZERO
	var height: float = _player.global_position.y
	assert_true(height > 0.6)
	await _seconds(0.5)
	assert_almost(_player.global_position.y, height, 0.05, "quieto, se queda colgado")
	_player.set("_jump_queued", true)
	await _seconds(1.0)
	assert_false(_player.is_climbing(), "saltar es soltarse")
	assert_true(_player.global_position.y < 0.3, "y cae")


## Un suelo, una caseta de 3 m (su fachada en z = 0, hacia +z la calle) y una
## escalera de pates por fuera.
func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	_box(Vector3(0.0, -0.5, 0.0), Vector3(40.0, 1.0, 40.0))
	_box(Vector3(0.0, ROOF * 0.5, -3.0), Vector3(6.0, ROOF, 6.0))
	_ladder = Climbable.make(Transform3D.IDENTITY, Vector3(0.5, ROOF, 0.8))
	_world.add_child(_ladder)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_player.surface_rules = true
	_world.add_child(_player)
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
