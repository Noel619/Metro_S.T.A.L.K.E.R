extends Node3D
## Revisión de la superficie jugable (Fase 3): la esclusa del vestíbulo, la compuerta,
## la sala, la salida a la plaza y el cuerpo en la superficie (agachado, corriendo,
## asomado, las ondas de tinta de los pasos), vistos desde cámaras fijas (grupo
## "capture_camera") para las capturas de tools/capture.sh.
##
## Argumentos (después de "--"): --hora=HH (por defecto, las 11) y --linterna.

const LEVEL: String = "res://scenes/surface/superficie.tscn"
const FLOOR: float = SurfaceLevel.HALL_FLOOR
## [nombre, desde, hacia], en el marco de la rotonda del vestíbulo (x hacia la escalera,
## y a la izquierda, z sobre la acera).
const VIEWS: Array = [
	["esclusa", Vector3(4.2, 1.6, FLOOR + 1.55), Vector3(1.6, -0.2, FLOOR + 1.1)],
	["compuerta", Vector3(-3.2, -2.4, FLOOR + 1.6), Vector3(2.4, 0.4, FLOOR + 1.2)],
	["sala", Vector3(1.2, 0.6, FLOOR + 1.6), Vector3(-1.0, -9.6, FLOOR + 1.6)],
	["salida", Vector3(-1.5, -17.5, 1.65), Vector3(40.0, -8.0, 2.5)],
	["cuerpo", Vector3(-2.6, -27.5, 1.3), Vector3(-2.6, -20.4, 0.7)],
	["ondas", Vector3(-14.0, -35.0, 7.0), Vector3(-2.6, -20.4, 0.0)],
]

var level: SurfaceLevel


func _ready() -> void:
	var hour: float = 11.0
	var torch: bool = false
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--hora="):
			hour = float(arg.get_slice("=", 1))
		elif arg == "--linterna":
			torch = true
	level = load(LEVEL).instantiate()
	add_child(level)
	GameState.minute = hour * 60.0
	level.env.override(Weather.fixed(290.0, Weather.Wind.BRISA))
	level.call("_apply_sky")
	for view: Array in VIEWS:
		var camera: Camera3D = Camera3D.new()
		camera.name = "Camara_" + String(view[0])
		camera.fov = 70.0
		add_child(camera)
		camera.add_to_group(&"capture_camera")
		var from: Vector3 = view[1]
		var to: Vector3 = view[2]
		camera.look_at_from_position(
			level.vestibule_point(from.x, from.y, from.z), level.vestibule_point(to.x, to.y, to.z)
		)
		if torch:
			Flashlight.attach(camera).visible = true
	_stage.call_deferred()


## La compuerta abierta, el jugador fuera de cámara y unos cuantos cuerpos con sus ondas.
func _stage() -> void:
	await get_tree().physics_frame
	level.world.set_values("compuerta", {"abierta": true})
	level.hatch.snap()
	var player: Player = level.local_player()
	if player != null:
		player.global_position = level.vestibule_point(-6.0, 6.0, FLOOR + 0.05)
		if player.arms() != null:
			player.arms().visible = false
	var poses: Array = [
		["chico", &"agachado_andar", 0.3, Vector2(-4.4, -20.2), 1.0, 0.0, PlayerBody.Gait.CROUCH],
		["chica", &"correr", 0.2, Vector2(-2.4, -20.6), 0.0, 0.0, PlayerBody.Gait.RUN],
		["chico", &"reposo", 1.0, Vector2(-0.6, -20.2), 0.0, 1.0, PlayerBody.Gait.STILL],
		["chica", &"caminar", 0.4, Vector2(-6.2, -20.4), 0.0, 0.0, PlayerBody.Gait.WALK],
	]
	level.ripples.paused = true
	for index: int in poses.size():
		var pose: Array = poses[index]
		var avatar: PlayerAvatar = PlayerAvatar.new()
		avatar.variant = pose[0]
		avatar.player_slot = index
		add_child(avatar)
		avatar.set_process(false)
		var spot: Vector2 = pose[3]
		var ground: Vector3 = _ground(level.vestibule_point(spot.x, spot.y, 2.0))
		avatar.global_position = ground
		avatar.rotation.y = SurfaceLevel.yaw_towards(Vector2(1.0, 0.0))
		avatar.preview(pose[1], pose[2])
		avatar.crouch = pose[4]
		avatar.lean = pose[5]
		var gait: PlayerBody.Gait = pose[6]
		if gait != PlayerBody.Gait.STILL:
			var radius: float = NoiseRules.step_radius(gait, &"nieve")
			level.ripples.add(ground, radius, Footsteps.RIPPLE_STRENGTH[gait], 0.32)


func _ground(from: Vector3) -> Vector3:
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, from + Vector3.DOWN * 10.0, 1
	)
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	return hit["position"] if not hit.is_empty() else from + Vector3.DOWN * 2.0
