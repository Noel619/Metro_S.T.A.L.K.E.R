extends "res://tests/test_case.gd"
## El depósito jugable en solitario: jugador, interacción y objetos (F2-01 a F2-03).

const LEVEL: String = "res://scenes/depot/deposito.tscn"

var _level: Node
var _player: Player


func before_each() -> void:
	DepotLevel.continue_saved = false
	_level = load(LEVEL).instantiate()
	add_child(_level)
	_player = _level.call("local_player")
	await _frames(30)


func after_each() -> void:
	_level.free()
	GameState.clock_running = false


func test_player_spawns_on_the_floor_with_everything_in_place() -> void:
	assert_true(_player != null, "el anfitrión tiene jugador")
	assert_true(_player.is_on_floor(), "pisa el suelo")
	assert_eq(_player.slot, 0, "el anfitrión es el primer color")
	var items: Array[Carryable] = (_level.get("items") as WorldItems).items()
	assert_eq(items.size(), 29)
	for item: Carryable in items:
		var body: RigidBody3D = item.get_parent()
		assert_true(body.global_position.y > -0.05, "%s no atraviesa el suelo" % item.state.data.id)
		assert_almost(body.mass, item.state.data.weight, 0.001, "pesa lo que dice su ficha")


func test_walks_and_stops() -> void:
	var start: Vector3 = _player.position
	_player.scripted_input = Vector2(0.0, -1.0)
	await _frames(40)
	assert_true(_player.position.distance_to(start) > 0.6, "anda")
	assert_almost(_player.move_speed, Player.WALK_SPEED, 0.2)
	_player.scripted_input = Vector2.ZERO
	await _frames(30)
	assert_almost(_player.move_speed, 0.0, 0.05, "se para")


func test_pick_up_carry_and_drop() -> void:
	var can: Carryable = _bench_can()
	var body: RigidBody3D = can.get_parent()
	var resting: Vector3 = body.global_position
	_player.position = Vector3(resting.x, 0.03, resting.z + 1.1)
	_player.rotation.y = 0.0
	_player.head_pitch = -0.5
	await _frames(10)
	assert_true(_player.focused() == Interactable.of(body), "la tiene delante")
	_player.interact()
	await _frames(40)
	assert_true(_player.held_item() == can, "la lleva")
	assert_true(_player.focused() == null, "con las manos ocupadas no señala nada")
	var hands: Vector3 = can.hold_target().origin
	assert_true(body.global_position.distance_to(hands) < 0.05, "está en sus manos")
	_player.scripted_input = Vector2(0.0, 1.0)
	await _frames(50)
	_player.scripted_input = Vector2.ZERO
	assert_true(body.global_position.distance_to(resting) > 0.8, "viaja con él")
	_player.interact()
	await _frames(60)
	assert_true(_player.held_item() == null, "la suelta")
	assert_true(body.global_position.y < 0.3, "y cae al suelo")


func test_weight_is_felt() -> void:
	assert_true(
		Carryable.follow_stiffness(18.0) < Carryable.follow_stiffness(0.4) * 0.5,
		"lo pesado tarda más"
	)
	var light: float = _player.hold_transform(0.4).origin.y
	var heavy: float = _player.hold_transform(18.0).origin.y
	assert_true(heavy < light - 0.08, "lo pesado cuelga más bajo")
	var can: Carryable = _bench_can()
	_player.set_held_item(can)
	var with_can: float = _player.carry_slowdown()
	_player.set_held_item(_item(&"bidon"))
	assert_true(_player.carry_slowdown() < with_can - 0.3, "y frena más")
	_player.set_held_item(null)
	assert_almost(_player.carry_slowdown(), 1.0)


func test_interactable_highlight() -> void:
	var body: RigidBody3D = _bench_can().get_parent()
	var interactable: Interactable = Interactable.of(body)
	var mesh: MeshInstance3D = body.find_children("*", "MeshInstance3D", true, false)[0]
	interactable.set_focused(true)
	assert_true(mesh.material_overlay != null, "se resalta con un contorno")
	interactable.set_focused(false)
	assert_true(mesh.material_overlay == null, "y deja de resaltarse")
	assert_true(ResourceLoader.exists(interactable.icon_path()), "tiene icono")


func _bench_can() -> Carryable:
	for item: Carryable in (_level.get("items") as WorldItems).items():
		var body: Node3D = item.get_parent()
		if item.state.data.id == &"lata_conserva" and body.global_position.x > -1.0:
			return item
	return null


func _item(item_id: StringName) -> Carryable:
	for item: Carryable in (_level.get("items") as WorldItems).items():
		if item.state.data.id == item_id:
			return item
	return null


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
