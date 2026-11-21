extends Node3D
## Hoja de revisión de la Jauría (F3-10): los tres pelajes en sus poses, dentro del
## patio de Los Bloques de la Fase 1, con la luz de la superficie. Cada cámara del
## grupo "capture_camera" da una captura (tools/capture.sh).

const SETTING: String = "res://scenes/style/diorama_patio_dia.tscn"
const MODELS: Array[String] = ["perro_vieja", "perro_pardo", "perro_negro"]
## [modelo, animación, instante, x, z, giro (grados)]: tres filas.
const POSES: Array = [
	["perro_vieja", &"vigilar", 0.4, -3.0, 2.0, 30.0],
	["perro_pardo", &"quieto", 1.0, -1.4, 2.0, 60.0],
	["perro_negro", &"grunir", 0.3, 0.2, 2.0, 80.0],
	["perro_vieja", &"andar", 0.3, 1.8, 2.0, 90.0],
	["perro_pardo", &"trote", 0.2, -3.0, 4.0, 90.0],
	["perro_negro", &"galope", 0.15, -1.2, 4.0, 90.0],
	["perro_vieja", &"galope", 0.6, 0.8, 4.0, 90.0],
	["perro_pardo", &"acechar", 0.5, 2.8, 4.0, 90.0],
	["perro_negro", &"echado", 1.0, -3.0, 6.0, 70.0],
	["perro_vieja", &"aullar", 1.2, -1.2, 6.0, 90.0],
	["perro_pardo", &"comer", 0.4, 0.6, 6.0, 60.0],
	["perro_negro", &"morder", 0.45, 2.6, 6.0, 90.0],
	["perro_pardo", &"olfatear", 0.6, 4.4, 6.0, 120.0],
]


func _ready() -> void:
	var stage: Node3D = load(SETTING).instantiate()
	add_child(stage)
	for camera: Node in stage.find_children("*", "Camera3D", true, false):
		camera.remove_from_group(&"capture_camera")
	var cast: Node3D = Node3D.new()
	cast.name = "Perros"
	add_child(cast)
	var placed: Array[Node3D] = []
	for pose: Array in POSES:
		var model: Node3D = load("res://assets/models/%s.glb" % pose[0]).instantiate()
		cast.add_child(model)
		model.position = Vector3(pose[3], 0.0, pose[4])
		model.rotation_degrees.y = pose[5]
		var player: AnimationPlayer = model.find_child("AnimationPlayer", true, false)
		if player != null:
			player.play(pose[1])
			player.seek(pose[2], true)
			player.pause()
		placed.append(model)
	_camera("Manada", Vector3(0.6, 2.6, 13.0), Vector3(0.6, 0.5, 4.0), 40.0)
	_camera("Cerca", Vector3(-1.4, 0.9, 4.6), Vector3(-1.6, 0.6, 2.0), 40.0)
	_camera("Marcha", Vector3(0.0, 0.8, 9.2), Vector3(0.0, 0.5, 4.0), 45.0)
	await get_tree().physics_frame
	await get_tree().physics_frame
	for node: Node3D in placed:
		_drop_to_floor(node)


func _drop_to_floor(node: Node3D) -> void:
	var from: Vector3 = node.global_position + Vector3.UP * 2.0
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, from + Vector3.DOWN * 6.0, 1
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
