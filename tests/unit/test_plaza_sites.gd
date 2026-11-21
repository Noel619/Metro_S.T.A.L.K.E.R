extends "res://tests/test_case.gd"
## Los sitios de La Plaza (F3-14): en la superficie entera están las puertas de los
## quioscos y los trasteros, el botín de la primera visita, los huesos de la Jauría y la
## flecha de tu padre; y desde la sala del vestíbulo se sube por la escalera de servicio
## al ventanal alto y se sale a la azotea del peristilo, el mirador, de donde una cuerda
## atada a la argolla baja hasta el basamento.

const SURFACE: String = "res://scenes/surface/superficie.tscn"
## El vestíbulo (singular_vestibulo.py): la azotea del peristilo y su antepecho.
const ROOF: float = 10.5
const PARAPET_INNER: float = 12.05

var _surface: SurfaceLevel


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")


func after_each() -> void:
	if _surface != null and is_instance_valid(_surface):
		_surface.free()
	Sortie.arrived()
	SaveSystem.clear_parked()
	GameState.clock_running = false
	GameState.reset_for_new_game("")


func test_the_plaza_has_doors_loot_and_signs() -> void:
	await _open()
	var doors: Array[SurfaceDoor] = _surface.sites.doors
	assert_true(doors.size() > 30, "las puertas de los menores (%d)" % doors.size())
	var kiosk: SurfaceDoor = null
	for door: SurfaceDoor in doors:
		if door.fixture_id == "PLZ-Q1_puerta_0":
			kiosk = door
	assert_true(kiosk != null, "la del quiosco Q1")
	if kiosk != null:
		var building: Dictionary = _surface.city.buildings_by_id["PLZ-Q1"]
		var center: Vector3 = CityPlan.to_world(
			Vector2(building["centro"][0], building["centro"][1]), float(building["cota"])
		)
		assert_true(kiosk.global_position.distance_to(center) < 3.0, "en su quiosco")
	var near_plaza: int = 0
	for item: Carryable in _surface.items.items():
		if item.body().global_position.distance_to(_surface.vestibule_point(0.0, 0.0)) < 400.0:
			near_plaza += 1
	assert_true(near_plaza > 30, "el botín de la primera visita (%d)" % near_plaza)
	assert_true(bool(_surface.world.value(SurfaceSites.WORLD_ID, "sembrado", false)))
	var father: Array = _surface.chalk.marks().filter(
		func(mark: Dictionary) -> bool: return mark.get("padre", false)
	)
	assert_eq(father.size(), 1, "la flecha de tu padre")
	assert_true(_surface.sites.get_node_or_null("Huesos") != null, "los huesos de la Jauría")
	assert_true(_surface.sites.ladders.size() >= 1, "la escalera del palomar")


func test_up_the_service_ladder_to_the_lookout() -> void:
	await _open()
	var player: Player = _surface.local_player()
	var ladder: Climbable = _surface.lookout
	player.global_position = ladder.hang_point(0.05, 0.6)
	player.rotation.y = ladder.facing_yaw()
	player.head_pitch = 0.0
	await _frames(10)
	player.scripted_input = Vector2(0.0, -1.0)
	await _frames(60)
	assert_true(player.is_climbing(), "se agarra a la escalera")
	var floor_y: float = _surface.vestibule_point(0.0, 0.0, 0.0).y
	for _second: int in 14:
		await _frames(60)
		if not player.is_climbing():
			break
	assert_false(player.is_climbing(), "llega arriba")
	assert_true(player.global_position.y > floor_y + 10.9, "en el alféizar del ventanal")
	# Agachado, por el ventanal, y abajo, a la azotea.
	await _frames(150)
	player.scripted_input = Vector2.ZERO
	await _frames(30)
	assert_almost(player.global_position.y, floor_y + ROOF, 0.15, "en la azotea del peristilo")
	var radius: float = _rotunda_radius(player.global_position)
	assert_true(radius > 9.6 and radius < PARAPET_INNER, "fuera del tambor (%.2f m)" % radius)


func test_the_roof_holds_and_the_rope_reaches_the_podium() -> void:
	await _open()
	var space: PhysicsDirectSpaceState3D = _surface.get_world_3d().direct_space_state
	# La azotea se pisa (en el lado de la entrada, por ejemplo).
	var above: Vector3 = _surface.vestibule_point(0.0, -11.0, ROOF + 2.0)
	var hit: Dictionary = space.intersect_ray(
		PhysicsRayQueryParameters3D.create(above, above + Vector3.DOWN * 4.0)
	)
	assert_false(hit.is_empty(), "la azotea tiene suelo")
	if not hit.is_empty():
		var floor_y: float = _surface.vestibule_point(0.0, 0.0, 0.0).y
		assert_almost((hit["position"] as Vector3).y, floor_y + ROOF, 0.05)
	# Y el antepecho para.
	var from: Vector3 = _surface.vestibule_point(0.0, -11.0, ROOF + 0.4)
	var to: Vector3 = _surface.vestibule_point(0.0, -13.0, ROOF + 0.4)
	assert_false(space.intersect_ray(PhysicsRayQueryParameters3D.create(from, to)).is_empty())
	# La cuerda atada a la argolla baja hasta el basamento.
	var anchor: RopeAnchor = _surface.rope_anchor
	_surface.world.set_value(anchor.fixture_id, "atada", true)
	await _frames(10)
	assert_true(anchor.climbable() != null, "cuelga")
	if anchor.climbable() != null:
		var drop: float = anchor.climbable().height
		assert_true(drop > 10.0 and drop < 11.5, "hasta el basamento (%.2f m)" % drop)


func _open() -> void:
	_surface = load(SURFACE).instantiate()
	add_child(_surface)
	await _frames(40)


## La distancia horizontal de [param point] al centro de la rotonda del vestíbulo.
func _rotunda_radius(point: Vector3) -> float:
	var center: Vector3 = _surface.vestibule_point(0.0, 0.0, 0.0)
	return Vector2(point.x - center.x, point.z - center.z).length()


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
