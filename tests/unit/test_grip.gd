extends "res://tests/test_case.gd"
## Las manos de primera persona se colocan según el tamaño de lo que se lleva.

const LEVEL: String = "res://scenes/depot/deposito.tscn"


func test_small_and_light_things_fit_one_hand() -> void:
	assert_true(GripModifier.fits_one_hand(Vector3(0.08, 0.11, 0.08), 0.4), "una lata")
	assert_true(GripModifier.fits_one_hand(Vector3(0.08, 0.3, 0.08), 0.5), "una botella")
	assert_false(GripModifier.fits_one_hand(Vector3(0.3, 0.2, 0.22), 0.8), "una caja pequeña")
	assert_false(
		GripModifier.fits_one_hand(Vector3(0.1, 0.1, 0.1), 6.0), "algo pequeño pero pesado"
	)


func test_hands_go_to_the_sides_of_the_box() -> void:
	var small: AABB = AABB(Vector3(-0.15, -0.36, -0.72), Vector3(0.3, 0.2, 0.2))
	var big: AABB = AABB(Vector3(-0.32, -0.6, -0.95), Vector3(0.64, 0.4, 0.45))
	var near: Dictionary = GripModifier.grip_points(small, false)
	var far: Dictionary = GripModifier.grip_points(big, false)
	assert_true(near[&"Left"].x < small.position.x, "la izquierda, por fuera del costado izquierdo")
	assert_true(near[&"Right"].x > small.end.x, "la derecha, por fuera del derecho")
	assert_almost(near[&"Right"].x, small.end.x + GripModifier.PALM_GAP)
	assert_almost(near[&"Left"].x, -near[&"Right"].x, 0.001, "simétricas")
	assert_true(far[&"Right"].x > near[&"Right"].x + 0.1, "una caja grande separa las manos")
	assert_true(
		near[&"Right"].y > small.position.y and near[&"Right"].y < small.end.y, "a media altura"
	)
	assert_true(far[&"Right"].x <= GripModifier.MAX_SPREAD, "sin pasar de lo que dan los brazos")
	assert_true(far[&"Right"].z >= -GripModifier.FAR, "ni de su largo")


func test_one_hand_uses_only_the_right() -> void:
	var can: AABB = AABB(Vector3(-0.04, -0.3, -0.66), Vector3(0.08, 0.11, 0.08))
	var points: Dictionary = GripModifier.grip_points(can, true)
	assert_false(points.has(&"Left"), "la izquierda no hace falta")
	assert_almost(points[&"Right"].y, can.get_center().y, 0.001, "la coge por el medio")


func test_big_things_are_carried_lower_and_farther() -> void:
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	var player: Player = level.call("local_player")
	var small: Vector3 = player.hold_transform(2.0, Vector3(0.1, 0.1, 0.1)).origin
	var big: Vector3 = player.hold_transform(2.0, Vector3(0.32, 0.3, 0.25)).origin
	var eyes: Vector3 = player.eye_position()
	assert_true(big.y < small.y - 0.1, "más bajo")
	assert_true(big.distance_to(eyes) > small.distance_to(eyes) + 0.1, "y más lejos")
	assert_eq(player.hold_transform(2.0).origin, small, "lo pequeño se lleva igual que antes")
	level.free()


func test_arms_grip_what_the_player_picks_up() -> void:
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	var player: Player = level.call("local_player")
	await _frames(30)
	var grip: GripModifier = player.arms().grip
	var can: Carryable = _item(level, &"lata_conserva")
	var box: Carryable = _item(level, &"caja_carton_grande")
	assert_true(box.half_size().x > can.half_size().x * 3.0, "cada objeto conoce sus medidas")
	player.set_held_item(can)
	assert_true(grip.is_one_handed(), "la lata, con una mano")
	player.set_held_item(box)
	assert_false(grip.is_one_handed(), "la caja grande, con las dos")
	await _frames(3)
	await get_tree().process_frame
	assert_true(
		grip.targets.has(&"Left") and grip.targets.has(&"Right"), "las dos manos tienen sitio"
	)
	assert_true(grip.targets[&"Right"].x - grip.targets[&"Left"].x > 0.4, "separadas como la caja")
	player.set_held_item(null)
	await get_tree().process_frame
	await get_tree().process_frame
	assert_true(grip.targets.is_empty(), "al soltar, las manos quedan libres")
	level.free()


func _item(level: Node, item_id: StringName) -> Carryable:
	for item: Carryable in (level.get("items") as WorldItems).items():
		if item.state.data.id == item_id:
			return item
	return null


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
