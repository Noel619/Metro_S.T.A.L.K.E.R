extends Node3D
## Escena de la Fase 0 ("Hola, Tumansk").
##
## Una caja generada por receta (tools/blender/recipes/caja_carton.py) e
## importada sola. El anfitrión la mueve; todos los jugadores la ven moverse a
## la vez gracias a [TransformSync].

const ORBIT_RADIUS: float = 0.6
const ORBIT_SPEED: float = 0.8
const LOOK_TARGET: Vector3 = Vector3(0.0, 0.2, 0.0)

var _time: float = 0.0

@onready var _box: Node3D = $Caja
@onready var _sun: DirectionalLight3D = $Sol
@onready var _camera: Camera3D = $CamaraCaptura


func _ready() -> void:
	_sun.rotation_degrees = Vector3(-48.0, 35.0, 0.0)
	_camera.look_at(LOOK_TARGET)
	for body: Node in _box.find_children("*", "RigidBody3D", true, false):
		(body as RigidBody3D).freeze = true
	_place_box()


func _physics_process(delta: float) -> void:
	if not NetSession.is_authority():
		return
	_time += delta
	_place_box()


func _place_box() -> void:
	var angle: float = _time * ORBIT_SPEED
	_box.position = Vector3(cos(angle), 0.0, sin(angle)) * ORBIT_RADIUS
	_box.rotation.y = -angle
