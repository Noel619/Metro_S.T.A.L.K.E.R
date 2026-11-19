extends Node3D
## Revisión de La Plaza jugable (F3-06, F3-14): la superficie entera con una toma
## preparada, vista con la cámara del jugador (para las capturas de tools/capture.sh).
##
## Argumentos (después de "--"): --toma=mirador|ganzuas|escalera|trasteros y --hora=HH.
## - mirador: en la azotea del peristilo del vestíbulo, junto a la argolla (con la cuerda
##   atada), mirando a la plaza.
## - ganzuas: delante de la puerta del quiosco Q2, con las ganzúas en la cerradura.
## - escalera: al pie de la escalera de servicio de la sala, mirando arriba.
## - trasteros: en el primer patio, delante de las casetas (con una abierta) y el palomar.

const LEVEL: String = "res://scenes/surface/superficie.tscn"
const ROOF: float = 10.5
const KIOSK_DOOR: String = "PLZ-Q2_puerta_0"
const SHED_ROW: String = "PLZ-P1"

var level: SurfaceLevel
var toma: String = "mirador"


func _ready() -> void:
	var hour: float = 11.0
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--toma="):
			toma = arg.get_slice("=", 1)
		elif arg.begins_with("--hora="):
			hour = float(arg.get_slice("=", 1))
	level = load(LEVEL).instantiate()
	add_child(level)
	GameState.minute = hour * 60.0
	level.env.override(Weather.fixed(290.0, Weather.Wind.BRISA))
	level.call("_apply_sky")
	_stage.call_deferred()


func _stage() -> void:
	for _i in 30:
		await get_tree().physics_frame
	var help: CanvasLayer = level.find_child("Ayuda", false, false) as CanvasLayer
	if help != null:
		help.visible = false
	level.jauria.pack.paused = true
	var player: Player = level.local_player()
	if player == null:
		return
	var camera: Camera3D = player.find_child("Camara", true, false) as Camera3D
	camera.add_to_group(&"capture_camera")
	match toma:
		"ganzuas":
			await _lockpick(player)
		"escalera":
			_ladder(player)
		"trasteros":
			_sheds(player)
		_:
			_lookout(player)


func _lookout(player: Player) -> void:
	level.world.set_value("cuerda_vestibulo", "atada", true)
	var bay: Vector2 = Vector2.from_angle(TAU * SurfaceLevel.ROPE_BAY / SurfaceLevel.BAYS)
	player.global_position = level.vestibule_point(bay.x * 11.0, bay.y * 11.0, ROOF + 0.05)
	player.rotation.y = SurfaceLevel.yaw_towards(bay.rotated(0.25))
	player.head_pitch = -0.12


func _ladder(player: Player) -> void:
	var ladder: Climbable = level.lookout
	player.global_position = ladder.hang_point(0.0, 1.3)
	player.rotation.y = ladder.facing_yaw()
	player.head_pitch = 0.95


func _lockpick(player: Player) -> void:
	var door: SurfaceDoor = _door(KIOSK_DOOR)
	if door == null:
		return
	level.world.set_values(door.fixture_id, {"cierre": "cerradura", "abierta": false})
	var front: Transform3D = door.global_transform
	var spot: Vector3 = front * Vector3(door.size.x * 0.75, 0.0, 0.75)
	player.global_position = spot
	var target: Vector3 = front * Vector3(door.size.x * 0.85, 1.05, 0.0)
	var flat: Vector3 = Vector3(target.x - spot.x, 0.0, target.z - spot.z)
	player.rotation.y = atan2(-flat.x, -flat.z)
	player.head_pitch = -0.25
	level.items.give(player, &"ganzuas")
	for _i in 40:
		await get_tree().physics_frame
	var view: LockpickView = LockpickView.open(player, door)
	if view != null:
		view.set_pins[0] = true
		view.set_pins[1] = true
		view.side = 2.0
		view.lift = 0.42


func _sheds(player: Player) -> void:
	var row: Node3D = level.city.kit_models.get(SHED_ROW) as Node3D
	if row == null:
		return
	var doors: Array = row.get_meta(&"kit_puertas", [])
	if doors.is_empty():
		return
	var first: Dictionary = doors[mini(2, doors.size() - 1)]
	var open_door: SurfaceDoor = _door(first["id"])
	if open_door != null:
		level.world.set_values(open_door.fixture_id, {"cierre": "rota", "abierta": true})
	var hinge: Transform3D = row.global_transform * (first["bisagra"] as Transform3D)
	var spot: Vector3 = hinge * Vector3(-2.5, 0.0, 6.5)
	player.global_position = spot + Vector3.UP * 0.1
	var target: Vector3 = hinge * Vector3(0.4, 1.0, 0.0)
	var flat: Vector3 = Vector3(target.x - spot.x, 0.0, target.z - spot.z)
	player.rotation.y = atan2(-flat.x, -flat.z)
	player.head_pitch = -0.08


func _door(id: String) -> SurfaceDoor:
	for door: SurfaceDoor in level.sites.doors:
		if door.fixture_id == id:
			return door
	return null
