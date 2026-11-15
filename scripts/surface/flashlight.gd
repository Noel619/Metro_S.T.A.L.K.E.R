class_name Flashlight
extends RefCounted
## Linterna de mano: un foco que sale de la cámara, algo a la derecha y abajo,
## como si la llevaras en la mano. De noche es lo único que te deja ver, y
## también lo que antes te delata.

const NODE_NAME: StringName = &"Linterna"


## Pone una linterna en la cámara (o devuelve la que ya tiene).
static func attach(camera: Camera3D) -> SpotLight3D:
	var existing: SpotLight3D = camera.get_node_or_null(NodePath(NODE_NAME)) as SpotLight3D
	if existing != null:
		return existing
	var light: SpotLight3D = SpotLight3D.new()
	light.name = NODE_NAME
	light.position = Vector3(0.22, -0.18, 0.0)
	light.light_color = Color(1.0, 0.93, 0.8)
	light.light_energy = 7.0
	light.spot_range = 30.0
	light.spot_angle = 24.0
	light.spot_angle_attenuation = 1.6
	light.shadow_enabled = true
	camera.add_child(light)
	return light


## Enciende o apaga la linterna de la cámara.
static func toggle(camera: Camera3D) -> void:
	var light: SpotLight3D = attach(camera)
	light.visible = not light.visible
