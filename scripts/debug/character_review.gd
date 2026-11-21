extends Node3D
## Hoja de revisión de los protagonistas (Fase 2).
##
## Los coloca dentro de los dioramas de la Fase 1, que es donde tienen que
## funcionar: en el patio de Los Bloques, con la luz fría de la superficie, y
## en el depósito, bajo la bombilla. Cada cámara del grupo "capture_camera" da
## una captura (tools/capture.sh).

const SETTINGS: Dictionary = {
	"superficie": "res://scenes/style/diorama_patio_dia.tscn",
	"deposito": "res://scenes/style/diorama_deposito_limpio.tscn",
}
const BOX_MODEL: String = "res://assets/models/caja_carton.glb"
const FLOOR_MASK: int = 1

@export_enum("superficie", "deposito") var setting: String = "superficie"

var _cast: Node3D
var _grounded: Array[Node3D] = []


func _ready() -> void:
	var stage: Node3D = load(SETTINGS[setting]).instantiate()
	add_child(stage)
	# Las cámaras del diorama no son las de esta hoja.
	for camera: Node in stage.find_children("*", "Camera3D", true, false):
		camera.remove_from_group(&"capture_camera")
	_cast = Node3D.new()
	_cast.name = "Personajes"
	add_child(_cast)
	if setting == "superficie":
		_build_surface()
	else:
		_build_depot()
	# Cuando la física del diorama está lista, cada uno pisa el suelo que tiene debajo.
	await get_tree().physics_frame
	await get_tree().physics_frame
	for node: Node3D in _grounded:
		_drop_to_floor(node)


func _build_surface() -> void:
	# Fila: cada uno de frente, de perfil y de espaldas.
	var turns: Array[float] = [0.0, -90.0, 180.0]
	for index: int in 6:
		var variant: String = "chico" if index < 3 else "chica"
		var avatar: PlayerAvatar = _avatar(variant, 0 if index < 3 else 1)
		avatar.position = Vector3((index - 2.5) * 0.95, 0.0, 2.5)
		avatar.rotation_degrees.y = 180.0 + turns[index % 3]
		avatar.preview(&"reposo", 0.4)
	_camera("Fila", Vector3(0.6, 1.5, 8.6), Vector3(0.0, 0.85, 2.5), 30.0)
	# Pareja: como se verían en una salida.
	var boy: PlayerAvatar = _avatar("chico", 0)
	boy.position = Vector3(-5.5, 0.0, 6.0)
	boy.rotation_degrees.y = 180.0 + 28.0
	boy.preview(&"reposo", 1.3)
	var girl: PlayerAvatar = _avatar("chica", 1)
	girl.position = Vector3(-4.9, 0.0, 6.2)
	girl.rotation_degrees.y = 180.0 - 16.0
	girl.preview(&"reposo", 3.1)
	girl.expression = &"cansado"
	_camera("Pareja", Vector3(-4.3, 1.2, 9.2), Vector3(-5.2, 0.95, 6.1), 34.0)
	_camera("Caras", Vector3(-5.0, 1.62, 7.7), Vector3(-5.18, 1.56, 6.1), 30.0)
	# En marcha.
	var poses: Array[Array] = [
		["chico", &"caminar", 0.05, -70.0, &"neutro"],
		["chica", &"caminar", 0.55, -80.0, &"esfuerzo"],
		["chico", &"caminar_cargando", 0.3, -50.0, &"esfuerzo"],
		["chica", &"reposo", 2.0, 40.0, &"miedo"],
	]
	for index: int in poses.size():
		var pose: Array = poses[index]
		var avatar: PlayerAvatar = _avatar(pose[0], index % 4)
		avatar.position = Vector3(4.4 + index * 1.15, 0.0, 6.4 + (index % 2) * 0.4)
		avatar.rotation_degrees.y = 180.0 + float(pose[3])
		avatar.preview(pose[1], pose[2])
		avatar.expression = pose[4]
	_camera("Marcha", Vector3(6.2, 1.1, 11.6), Vector3(6.1, 0.9, 6.5), 30.0)
	# En la superficie (F3-01): agachado, andando agachado, corriendo y asomándose.
	var stealth: Array[Array] = [
		["chico", &"agachado", 0.6, -60.0, 0.0],
		["chica", &"agachado_andar", 0.2, -80.0, 0.0],
		["chico", &"correr", 0.1, -80.0, 0.0],
		["chica", &"correr", 0.6, -100.0, 0.0],
		["chico", &"agachado_cargando", 1.0, -40.0, 0.0],
		["chica", &"reposo", 1.0, 0.0, 1.0],
	]
	for index: int in stealth.size():
		var pose: Array = stealth[index]
		var avatar: PlayerAvatar = _avatar(pose[0], index % 4)
		avatar.position = Vector3(-6.0 + index * 1.25, 0.0, -1.5 + (index % 2) * 0.3)
		avatar.rotation_degrees.y = 180.0 + float(pose[3])
		avatar.preview(pose[1], pose[2])
		avatar.lean = pose[4]
		avatar.expression = &"esfuerzo" if String(pose[1]).begins_with("correr") else &"miedo"
	_camera("Sigilo", Vector3(-2.9, 1.2, 4.6), Vector3(-2.9, 0.7, -1.4), 42.0)
	# Trepando (F3-06): por una escalera de pates, en dos momentos del ciclo.
	for index: int in 2:
		var climber: PlayerAvatar = _avatar("chico" if index == 0 else "chica", index)
		climber.position = Vector3(12.0 + index * 1.7, 0.4 + index * 0.5, -3.0)
		climber.rotation_degrees.y = 35.0 if index == 0 else -35.0
		climber.preview(&"trepar", 0.1 + index * 0.45)
		climber.expression = &"esfuerzo"
		climber.add_child(_ladder())
	_camera("Trepar", Vector3(12.85, 1.9, 2.6), Vector3(12.85, 1.4, -3.0), 40.0)


## Una escalera de pates delante de quien trepa (en su marco: -z es su frente).
static func _ladder() -> Node3D:
	var ladder: Node3D = Node3D.new()
	ladder.name = "Escalera"
	var steel: StandardMaterial3D = StandardMaterial3D.new()
	steel.albedo_color = Color("#4a4e50")
	for x: float in [-0.24, 0.24]:
		ladder.add_child(_bar(Vector3(0.05, 4.0, 0.03), Vector3(x, 1.0, -0.36), steel))
	for k: int in 14:
		ladder.add_child(
			_bar(Vector3(0.5, 0.03, 0.03), Vector3(0.0, -0.6 + k * 0.28, -0.36), steel)
		)
	return ladder


static func _bar(size: Vector3, at: Vector3, material: Material) -> MeshInstance3D:
	var bar: MeshInstance3D = MeshInstance3D.new()
	var box: BoxMesh = BoxMesh.new()
	box.size = size
	bar.mesh = box
	bar.material_override = material
	bar.position = at
	return bar


func _build_depot() -> void:
	var boy: PlayerAvatar = _avatar("chico", 0)
	boy.position = Vector3(-0.45, 0.0, -0.1)
	boy.rotation_degrees.y = 180.0 + 20.0
	boy.preview(&"reposo", 1.3)
	var girl: PlayerAvatar = _avatar("chica", 1)
	girl.position = Vector3(0.5, 0.0, -0.35)
	girl.rotation_degrees.y = 180.0 - 24.0
	girl.preview(&"reposo_cargando", 0.5)
	# Lo que lleva entre las manos.
	var box: Node3D = load(BOX_MODEL).instantiate()
	box.scale = Vector3.ONE * 0.62
	girl.add_child(box)
	box.position = Vector3(0.0, 1.0, -0.33)
	for body: Node in box.find_children("*", "RigidBody3D", true, false):
		(body as RigidBody3D).freeze = true
	_camera("Pareja", Vector3(0.75, 1.3, 1.62), Vector3(0.0, 0.95, -0.2), 54.0)
	_camera("Caras", Vector3(0.3, 1.56, 0.95), Vector3(0.0, 1.5, -0.2), 34.0)


func _avatar(variant: String, slot: int) -> PlayerAvatar:
	var avatar: PlayerAvatar = PlayerAvatar.new()
	avatar.variant = variant
	avatar.player_slot = slot
	_cast.add_child(avatar)
	avatar.set_process(false)
	_grounded.append(avatar)
	return avatar


func _drop_to_floor(node: Node3D) -> void:
	var from: Vector3 = node.global_position + Vector3.UP * 2.0
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, from + Vector3.DOWN * 6.0, FLOOR_MASK
	)
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():
		node.global_position.y = (hit["position"] as Vector3).y


func _camera(camera_name: String, from: Vector3, target: Vector3, fov: float) -> void:
	var camera: Camera3D = Camera3D.new()
	camera.name = "Camara" + camera_name
	camera.fov = fov
	camera.position = from
	add_child(camera)
	camera.look_at(target)
	camera.add_to_group(&"capture_camera")
