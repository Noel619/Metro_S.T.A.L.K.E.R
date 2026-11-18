extends "res://tests/test_case.gd"
## Las manos de primera persona sujetan lo que se lleva lo mires como lo mires,
## y lo que se lleva nunca se mete en el cuerpo ni en los ojos (F2-03).

const LEVEL: String = "res://scenes/depot/deposito.tscn"
## Un sitio despejado de la consigna, mirando hacia el fondo.
const OPEN_SPOT: Vector3 = Vector3(0.8, 0.03, 1.4)
## En la consigna, de cara al muro del fondo (su cara está en z = -3,75).
const WALL_SPOT: Vector3 = Vector3(1.6, 0.03, -1.4)
const WALL_FACE: float = -3.75
## El pecho: un eje vertical bajo los ojos y su radio.
const TORSO_RADIUS: float = 0.16
## Lo más lejos que puede quedar una palma de lo que sujeta.
const PALM_REACH: float = 0.04

var _level: Node
var _player: Player
## Dónde quedan las palmas, y la caja de lo que sujetan, al colocar las manos.
var _palms: Dictionary = {}


func before_each() -> void:
	_level = load(LEVEL).instantiate()
	add_child(_level)
	_player = _level.call("local_player")
	await _frames(30)
	_player.arms().grip.modification_processed.connect(_on_hands_placed)


func after_each() -> void:
	Input.action_release(&"use_secondary")
	_level.free()


func test_small_and_light_things_fit_one_hand() -> void:
	assert_true(GripModifier.fits_one_hand(Vector3(0.08, 0.11, 0.08), 0.4), "una lata")
	assert_true(GripModifier.fits_one_hand(Vector3(0.08, 0.3, 0.08), 0.5), "una botella")
	assert_false(GripModifier.fits_one_hand(Vector3(0.3, 0.2, 0.22), 0.8), "una caja pequeña")
	assert_false(
		GripModifier.fits_one_hand(Vector3(0.1, 0.1, 0.1), 6.0), "algo pequeño pero pesado"
	)


func test_extent_of_a_turned_box() -> void:
	var half: Vector3 = Vector3(0.3, 0.1, 0.2)
	assert_eq(GripModifier.extent(Basis(), half), half, "sin girar, sus medidas")
	var turned: Vector3 = GripModifier.extent(Basis(Vector3.UP, PI / 2.0), half)
	assert_almost(turned.x, 0.2, 0.001, "un cuarto de vuelta cambia el ancho por el fondo")
	assert_almost(turned.z, 0.3, 0.001)


func test_the_farther_the_lower_the_hands_must_hold() -> void:
	var near: float = GripModifier.highest_center(0.45, Player.FOV)
	var far: float = GripModifier.highest_center(0.9, Player.FOV)
	assert_true(near > far, "más lejos, más abajo: si no, se vería dónde acaban las mangas")
	assert_true(far < 0.0, "a casi un metro, por debajo del centro de la vista")


func test_grips_are_found_on_the_mesh() -> void:
	var bottle: Node3D = load("res://assets/models/botella_verde.glb").instantiate()
	add_child(bottle)
	var body: Node3D = bottle.find_children("*", "RigidBody3D", true, false)[0]
	var faces: PackedVector3Array = GripModifier.faces_of(body)
	var hit: Array = GripModifier.ray_hit(faces, Vector3(1.0, 0.1, 0.0), Vector3.LEFT)
	assert_false(hit.is_empty(), "un rayo desde la derecha toca la botella")
	assert_almost(
		(hit[0] as Vector3).x, 0.0375, 0.01, "en el cristal, no en la caja que la envuelve"
	)
	assert_true((hit[1] as Vector3).x > 0.8, "y la normal mira hacia quien llega")
	assert_true(GripModifier.ray_hit(faces, Vector3(1.0, 0.1, 0.3), Vector3.LEFT).is_empty())
	bottle.free()


func test_big_things_are_carried_lower_and_farther() -> void:
	var small_box: AABB = AABB(Vector3(-0.1, 0.0, -0.1), Vector3(0.2, 0.2, 0.2))
	var big_box: AABB = AABB(Vector3(-0.32, 0.0, -0.25), Vector3(0.64, 0.6, 0.5))
	var small: Vector3 = _player.hold_transform(2.0, small_box) * small_box.get_center()
	var big: Vector3 = _player.hold_transform(2.0, big_box) * big_box.get_center()
	var eyes: Vector3 = _player.eye_position()
	assert_true(big.y < small.y - 0.1, "más bajo")
	assert_true(big.distance_to(eyes) > small.distance_to(eyes) + 0.1, "y más lejos")


func test_carried_things_never_enter_the_body_or_the_eyes() -> void:
	for item_id: StringName in [&"lata_conserva", &"caja_carton_grande", &"bidon", &"escoba"]:
		var item: Carryable = await _carry(item_id)
		for pitch: float in [-1.43, -0.8, 0.0, 0.8, 1.43]:
			_player.head_pitch = pitch
			await _frames(40)
			var box: Array = _box(item.get_parent())
			var label: String = "%s mirando a %d grados" % [item_id, roundi(rad_to_deg(pitch))]
			assert_true(_torso_gap(box) > 0.0, label + ": fuera del pecho")
			assert_true(
				_distance(_player.eye_position(), box) > 0.15, label + ": lejos de los ojos"
			)


func test_looking_down_is_limited_while_carrying() -> void:
	assert_almost(_player.lowest_pitch(), -Player.LOOK_LIMIT, 0.001, "con las manos libres")
	await _carry(&"caja_carton_grande")
	var lowest: float = _player.lowest_pitch()
	assert_true(lowest > -1.0, "con una caja grande no se puede mirar tan abajo")
	_player.head_pitch = -Player.LOOK_LIMIT
	await _frames(40)
	assert_almost(_player.head_pitch, lowest, 0.01, "la mirada sube sola hasta donde se puede")
	_player.look(0.0, -0.5)
	assert_true(_player.head_pitch >= lowest - 0.001, "y no vuelve a bajar")
	await _carry(&"lata_conserva")
	assert_true(_player.lowest_pitch() < lowest - 0.2, "con una lata se puede mirar más abajo")


func test_hands_hold_it_wherever_you_look() -> void:
	for item_id: StringName in [&"botella_verde", &"caja_carton_pequena", &"bidon", &"escoba"]:
		var item: Carryable = await _carry(item_id)
		for pitch: float in [-1.2, -0.4, 0.0, 0.6, 1.3]:
			_player.head_pitch = pitch
			await _frames(30)
			await get_tree().process_frame
			_assert_palms_on(item, "%s a %d grados" % [item_id, roundi(rad_to_deg(pitch))])


func test_hands_hold_it_while_turning_fast() -> void:
	for item_id: StringName in [&"botella_verde", &"bidon"]:
		var item: Carryable = await _carry(item_id)
		for _i in 20:
			_player.look(0.12, 0.0)  # Unos 7 radianes por segundo.
			await get_tree().physics_frame
			await get_tree().process_frame
			_assert_palms_on(item, "%s girando" % item_id)


func test_carried_things_keep_up_when_walking() -> void:
	var item: Carryable = await _carry(&"bidon", Vector3(-6.0, 0.03, 6.5), -PI / 2.0)
	var body: RigidBody3D = item.get_parent()
	var center: Vector3 = item.bounds().get_center()
	_player.scripted_input = Vector2(0.0, -1.0)
	var worst: float = 0.0
	for _i in 60:
		await get_tree().physics_frame
		worst = maxf(
			worst, (item.hold_target() * center).distance_to(body.global_transform * center)
		)
	_player.scripted_input = Vector2.ZERO
	assert_true(worst < 0.08, "el bidón no se queda atrás al andar (%.2f m)" % worst)


func test_cannot_walk_through_what_you_carry() -> void:
	var item: Carryable = await _carry(&"caja_carton_pequena", WALL_SPOT, 0.0)
	var body: RigidBody3D = item.get_parent()
	_player.scripted_input = Vector2(0.0, -1.0)
	var closest: float = INF
	var deepest: float = INF
	for _i in 150:
		await get_tree().physics_frame
		var box: Array = _box(body)
		closest = minf(closest, _distance(_player.eye_position(), box))
		deepest = minf(deepest, -_farthest_along(box, Vector3.FORWARD))
	_player.scripted_input = Vector2.ZERO
	assert_true(_player.held_item() == item, "la sigue llevando")
	assert_true(closest > 0.15, "la cámara nunca se mete en la caja (%.2f m)" % closest)
	assert_true(deepest > WALL_FACE - 0.02, "la caja no se mete en la pared (%.3f)" % deepest)
	assert_true(_player.global_position.z > WALL_FACE + 0.4, "el jugador se para antes")


func test_inspecting_never_reaches_the_eyes() -> void:
	var item: Carryable = await _carry(&"caja_carton_grande")
	Input.action_press(&"use_secondary")
	await _frames(20)
	assert_true(_player.inspecting, "la está mirando de cerca")
	var closest: float = INF
	for _i in 60:
		_player.turn_held(Vector2(0.05, 0.07))
		await get_tree().physics_frame
		closest = minf(closest, _distance(_player.eye_position(), _box(item.get_parent())))
	Input.action_release(&"use_secondary")
	assert_true(closest > 0.15, "al girarla no llega a la cara (%.2f m)" % closest)


func test_turning_follows_the_mouse_as_seen() -> void:
	_player.head_pitch = -0.6
	_player.turn_held(Vector2(0.3, 0.0))
	var up: Vector3 = Basis(Vector3.RIGHT, -0.6) * Vector3.UP
	assert_almost(_player.hold_rotation.get_angle(), 0.3, 0.001)
	assert_true(
		_player.hold_rotation.get_axis().dot(up) > 0.999, "de lado: sobre el eje de la vista"
	)


func test_arms_grip_what_the_player_picks_up() -> void:
	var grip: GripModifier = _player.arms().grip
	var can: Carryable = await _carry(&"lata_conserva")
	assert_true(grip.is_one_handed(), "la lata, con una mano")
	assert_true(grip.targets.has(&"Right") and not grip.targets.has(&"Left"), "la derecha")
	var box: Carryable = await _carry(&"caja_carton_grande")
	assert_false(grip.is_one_handed(), "la caja grande, con las dos")
	assert_true(box.half_size().x > can.half_size().x * 3.0, "cada objeto conoce sus medidas")
	assert_true(
		grip.targets.has(&"Left") and grip.targets.has(&"Right"), "las dos manos tienen sitio"
	)
	assert_true(grip.targets[&"Right"].x - grip.targets[&"Left"].x > 0.6, "separadas como la caja")
	_player.interact()
	await _frames(20)
	assert_true(grip.targets.is_empty(), "al soltar, las manos quedan libres")


## Coge un objeto: lo pone delante del jugador, en [param spot], y se lo da.
func _carry(item_id: StringName, spot: Vector3 = OPEN_SPOT, yaw: float = 0.0) -> Carryable:
	if _player.held_item() != null:
		var previous: RigidBody3D = _player.held_item().get_parent()
		_player.interact()
		await _frames(20)
		previous.global_position = Vector3(-4.5, 0.6, 6.6)
	var item: Carryable = null
	for candidate: Carryable in (_level.get("items") as WorldItems).items():
		if candidate.state.data.id == item_id:
			item = candidate
			break
	var body: RigidBody3D = item.get_parent()
	_player.position = spot
	_player.rotation.y = yaw
	_player.head_pitch = 0.0
	body.global_transform = Transform3D(
		Basis(), spot + Basis(Vector3.UP, yaw) * Vector3(0.0, 0.0, -0.9)
	)
	body.linear_velocity = Vector3.ZERO
	body.angular_velocity = Vector3.ZERO
	await _frames(3)
	item.request_grab()
	for _i in 90:
		await get_tree().physics_frame
		if item.in_hands():
			break
	await _frames(15)
	return item


func _on_hands_placed() -> void:
	var grip: GripModifier = _player.arms().grip
	var skeleton: Skeleton3D = grip.get_skeleton()
	_palms = {}
	for side: StringName in grip.targets:
		var hand: int = skeleton.find_bone(String(side) + "Hand")
		_palms[side] = (
			skeleton.global_transform * (skeleton.get_bone_global_pose(hand) * GripModifier.PALM)
		)
	var item: Carryable = _player.held_item()
	if item != null:
		_palms[&"object"] = item.visual().global_transform
		_palms[&"bounds"] = item.bounds()


## Las palmas que agarran están sobre el objeto, tal como se dibuja.
func _assert_palms_on(item: Carryable, label: String) -> void:
	var sides: Array[StringName] = [&"Right"]
	if not _player.arms().grip.is_one_handed():
		sides.append(&"Left")
	for side: StringName in sides:
		if not _palms.has(side) or not _palms.has(&"object"):
			_fail("%s: la mano %s no agarra" % [label, side])
			continue
		var local: Vector3 = (_palms[&"object"] as Transform3D).affine_inverse() * _palms[side]
		var bounds: AABB = _palms[&"bounds"]
		var gap: float = local.distance_to(local.clamp(bounds.position, bounds.end))
		assert_true(gap < PALM_REACH, "%s: la mano %s a %.3f m de %s" % [label, side, gap, item])


## La caja de colisión de un cuerpo: [transform global, medias medidas].
func _box(body: RigidBody3D) -> Array:
	for node: Node in body.find_children("*", "CollisionShape3D", true, false):
		var shape: CollisionShape3D = node as CollisionShape3D
		if shape.shape is BoxShape3D:
			return [shape.global_transform, (shape.shape as BoxShape3D).size / 2.0]
	return [body.global_transform, Vector3.ONE * 0.05]


func _distance(point: Vector3, box: Array) -> float:
	var local: Vector3 = (box[0] as Transform3D).affine_inverse() * point
	var half: Vector3 = box[1]
	return local.distance_to(local.clamp(-half, half))


## Lo que queda entre el pecho del jugador y la caja (negativo: se mete).
func _torso_gap(box: Array) -> float:
	var nearest: float = INF
	for step: int in 25:
		var point: Vector3 = _player.global_position + Vector3.UP * lerpf(0.3, 1.45, step / 24.0)
		nearest = minf(nearest, _distance(point, box))
	return nearest - TORSO_RADIUS


## Lo más lejos que llega la caja en [param direction].
func _farthest_along(box: Array, direction: Vector3) -> float:
	var shape: Transform3D = box[0]
	var half: Vector3 = box[1]
	return shape.origin.dot(direction) + GripModifier.extent(shape.basis, half).dot(direction.abs())


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
