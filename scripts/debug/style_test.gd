extends Node3D
## Escena de calibración del estilo: primitivas y cajas bajo una luz cálida.
## La zona de estilo se elige con [member zone] (depósito o superficie).

@export var zone: StringName = &"deposito"
@export_range(0.0, 1.0) var fear: float = 0.0
## Vista de depuración del post-proceso (ver post_tinta.gdshader).
@export_range(0, 4) var debug_view: int = 0

@onready var _camera: Camera3D = $CamaraCaptura
@onready var _post: MeshInstance3D = $CamaraCaptura/InkPost


func _ready() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--debug-view="):
			debug_view = arg.get_slice("=", 1).to_int()
		elif arg.begins_with("--zone="):
			zone = StringName(arg.get_slice("=", 1))
	StyleDirector.set_zone(zone, true)
	StyleDirector.fear = fear
	_camera.look_at(Vector3(0.0, 0.45, 0.0))
	$Sol.rotation_degrees = Vector3(-42.0, 38.0, 0.0)
	# Escena estática: los objetos físicos no deben caerse durante la captura.
	for body: Node in find_children("*", "RigidBody3D", true, false):
		(body as RigidBody3D).freeze = true
	if debug_view != 0:
		var material: ShaderMaterial = _post.get_surface_override_material(0).duplicate()
		material.set_shader_parameter("debug_view", debug_view)
		_post.set_surface_override_material(0, material)
