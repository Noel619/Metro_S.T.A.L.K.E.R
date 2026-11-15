class_name MockupWalker
extends CharacterBody3D
## El visitante de la maqueta de la ciudad: anda (con colisión y a paso de persona, para
## medir recorridos) o vuela (sin colisión, para mirar). No es el controlador del juego
## (F3-01): solo una herramienta para recorrer la maqueta.
##
## WASD para moverse, ratón para mirar. Andando: Mayús corre, C se agacha, Espacio salta.
## Volando: Mayús va más rápido, Espacio sube, C baja y la rueda cambia la velocidad.

const EYE_HEIGHT: float = 1.62
const CROUCH_EYE_HEIGHT: float = 1.0
## Velocidades a pie en m/s: paso tranquilo, carrera y agachado.
const WALK_SPEED: float = 1.4
const RUN_SPEED: float = 5.0
const CROUCH_SPEED: float = 0.7
const JUMP_SPEED: float = 4.2
const GRAVITY: float = 9.8

## Velocidad de vuelo en m/s (la rueda del ratón la cambia).
@export var fly_speed: float = 25.0
@export var mouse_sensitivity: float = 0.0022

var flying: bool = false
## Mientras sea falso, el visitante no se mueve (por ejemplo, durante un recorrido).
var controls_enabled: bool = true

var _pitch: float = 0.0
var _camera: Camera3D
var _shape: CollisionShape3D


func _ready() -> void:
	_shape = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = 0.3
	capsule.height = 1.75
	_shape.shape = capsule
	_shape.position = Vector3(0.0, 0.875, 0.0)
	add_child(_shape)
	_camera = Camera3D.new()
	_camera.name = "Camara"
	_camera.position = Vector3(0.0, EYE_HEIGHT, 0.0)
	_camera.fov = 70.0
	_camera.far = 4000.0
	add_child(_camera)
	floor_max_angle = deg_to_rad(50.0)
	floor_snap_length = 0.6


## La cámara del visitante.
func camera() -> Camera3D:
	return _camera


## Pasa de andar a volar y al revés.
func set_flying(value: bool) -> void:
	flying = value
	_shape.disabled = flying
	velocity = Vector3.ZERO


## Coloca al visitante con los ojos en [param eye] mirando hacia [param target].
func place(eye: Vector3, target: Vector3) -> void:
	global_position = eye - Vector3.UP * EYE_HEIGHT
	var direction: Vector3 = target - eye
	rotation = Vector3(0.0, atan2(-direction.x, -direction.z), 0.0)
	_pitch = atan2(direction.y, Vector2(direction.x, direction.z).length())
	_camera.rotation = Vector3(_pitch, 0.0, 0.0)
	velocity = Vector3.ZERO


## Hacia dónde mira, en horizontal (para el panel).
func heading() -> Vector3:
	return -global_transform.basis.z


func _unhandled_input(event: InputEvent) -> void:
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-motion.relative.x * mouse_sensitivity)
		_pitch = clampf(_pitch - motion.relative.y * mouse_sensitivity, -1.5, 1.5)
		_camera.rotation = Vector3(_pitch, 0.0, 0.0)
	var button: InputEventMouseButton = event as InputEventMouseButton
	if button != null and button.pressed and flying:
		if button.button_index == MOUSE_BUTTON_WHEEL_UP:
			fly_speed = minf(fly_speed * 1.25, 400.0)
		elif button.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			fly_speed = maxf(fly_speed / 1.25, 2.0)


func _physics_process(delta: float) -> void:
	if not controls_enabled:
		return
	var input: Vector2 = Input.get_vector(
		&"move_left", &"move_right", &"move_forward", &"move_back"
	)
	var basis: Basis = global_transform.basis
	if flying:
		var direction: Vector3 = _camera.global_transform.basis * Vector3(input.x, 0.0, input.y)
		if Input.is_action_pressed(&"jump"):
			direction += Vector3.UP
		if Input.is_action_pressed(&"crouch"):
			direction += Vector3.DOWN
		var speed: float = fly_speed * (4.0 if Input.is_action_pressed(&"sprint") else 1.0)
		global_position += direction.limit_length(1.0) * speed * delta
		return
	var crouching: bool = Input.is_action_pressed(&"crouch")
	var speed_on_foot: float = WALK_SPEED
	if crouching:
		speed_on_foot = CROUCH_SPEED
	elif Input.is_action_pressed(&"sprint"):
		speed_on_foot = RUN_SPEED
	var wanted: Vector3 = (basis * Vector3(input.x, 0.0, input.y)).limit_length(1.0) * speed_on_foot
	velocity.x = wanted.x
	velocity.z = wanted.z
	if is_on_floor():
		if Input.is_action_just_pressed(&"jump"):
			velocity.y = JUMP_SPEED
	else:
		velocity.y -= GRAVITY * delta
	var eye: float = CROUCH_EYE_HEIGHT if crouching else EYE_HEIGHT
	_camera.position.y = move_toward(_camera.position.y, eye, delta * 3.0)
	move_and_slide()
