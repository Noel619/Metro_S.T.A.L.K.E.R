class_name Player
extends CharacterBody3D
## Un jugador en primera persona. Versión del depósito: tranquila, sin estamina.
##
## Cada jugador manda sobre su propio movimiento (no hay retraso al andar ni al
## mirar) y lo replica a los demás; el anfitrión manda sobre el mundo. Los demás
## lo ven como un [PlayerAvatar]; él solo ve sus manos ([FirstPersonArms]).
##
## Coger, girar, inspeccionar y soltar: "interactuar" coge lo que se tiene
## delante y lo vuelve a soltar; con el botón secundario pulsado, el objeto se
## acerca a los ojos y el ratón lo gira en vez de mover la mirada.

const GROUP: StringName = &"players"
const WALK_SPEED: float = 2.3
const ACCELERATION: float = 10.0
const GRAVITY: float = 9.8
const LOOK_LIMIT: float = 1.43
const REACH: float = 2.2
const PAD_LOOK_SPEED: float = 2.4
const INSPECT_TURN_SPEED: float = 0.012
## Kilos que reducen la velocidad a la mitad.
const HALF_SPEED_WEIGHT: float = 22.0
const EYE_HEIGHTS: Dictionary = {"chico": 1.57, "chica": 1.51}
## Dónde quedan las manos respecto a los ojos: al llevar algo y al inspeccionarlo.
const HOLD_OFFSET: Vector3 = Vector3(0.0, -0.26, -0.62)
const INSPECT_OFFSET: Vector3 = Vector3(0.0, -0.07, -0.44)
const LAYER_PLAYERS: int = 1 << 1
const MASK_PLAYERS: int = (1 << 0) | (1 << 2)
const MASK_REACH: int = (1 << 0) | (1 << 2) | (1 << 4)
const SYNCED: PackedStringArray = [
	".:position", ".:rotation", ".:head_pitch", ".:move_speed", ".:hold_euler", ".:inspecting"
]

var peer_id: int = 1
var variant: String = "chico"
var slot: int = 0
## Inclinación de la mirada, en radianes (positivo: hacia arriba).
var head_pitch: float = 0.0
## Velocidad a la que anda ahora mismo.
var move_speed: float = 0.0
## Giro del objeto que lleva, respecto a su cuerpo.
var hold_euler: Vector3 = Vector3.ZERO
## Tiene el objeto cerca de los ojos y lo está girando.
var inspecting: bool = false
## Para pruebas y bots: sustituye a las teclas de movimiento.
var scripted_input: Vector2 = Vector2.ZERO

var _head: Node3D
var _camera: Camera3D
var _avatar: PlayerAvatar
var _arms: FirstPersonArms
var _reticle: Reticle
var _held: Carryable
var _focus: Interactable


## El jugador de un peer, si está en la escena.
static func find(tree: SceneTree, peer: int) -> Player:
	if peer == 0:
		return null
	for node: Node in tree.get_nodes_in_group(GROUP):
		if (node as Player).peer_id == peer:
			return node as Player
	return null


## Monta el jugador. Se llama igual en todos los equipos, antes de entrar en escena.
func setup(new_peer: int, new_variant: String, new_slot: int) -> void:
	peer_id = new_peer
	variant = new_variant if EYE_HEIGHTS.has(new_variant) else "chico"
	slot = new_slot
	name = "jugador_%d" % peer_id
	add_to_group(GROUP)
	collision_layer = LAYER_PLAYERS
	collision_mask = MASK_PLAYERS
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = 0.27
	capsule.height = 1.7
	var shape: CollisionShape3D = CollisionShape3D.new()
	shape.name = "Cuerpo"
	shape.shape = capsule
	shape.position.y = 0.85
	add_child(shape)
	_head = Node3D.new()
	_head.name = "Cabeza"
	_head.position.y = EYE_HEIGHTS[variant]
	add_child(_head)
	_avatar = PlayerAvatar.new()
	_avatar.name = "Avatar"
	_avatar.variant = variant
	_avatar.player_slot = slot
	add_child(_avatar)
	var sync: MultiplayerSynchronizer = MultiplayerSynchronizer.new()
	sync.name = "Sincronizador"
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	for property: String in SYNCED:
		config.add_property(NodePath(property))
		config.property_set_spawn(NodePath(property), true)
		config.property_set_replication_mode(
			NodePath(property), SceneReplicationConfig.REPLICATION_MODE_ALWAYS
		)
	sync.replication_config = config
	add_child(sync)
	set_multiplayer_authority(peer_id)


func _ready() -> void:
	if not is_local():
		return
	_avatar.shadow_only = true
	_camera = Camera3D.new()
	_camera.name = "Camara"
	_camera.fov = 72.0
	_camera.near = 0.04
	_head.add_child(_camera)
	_camera.make_current()
	_arms = FirstPersonArms.new()
	_arms.name = "Manos"
	_camera.add_child(_arms)
	_arms.setup(variant)
	_reticle = Reticle.new()
	_reticle.name = "PuntoDeMira"
	add_child(_reticle)
	if DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _exit_tree() -> void:
	if _focus != null and is_instance_valid(_focus):
		_focus.set_focused(false)
	if is_local() and DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _unhandled_input(event: InputEvent) -> void:
	if not is_local():
		return
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		if inspecting:
			hold_euler.y += motion.relative.x * INSPECT_TURN_SPEED
			hold_euler.x += motion.relative.y * INSPECT_TURN_SPEED
		else:
			var sensitivity: float = deg_to_rad(Settings.mouse_sensitivity)
			look(-motion.relative.x * sensitivity, -motion.relative.y * sensitivity)
	elif event.is_action_pressed(&"interact"):
		interact()
	elif event.is_action_pressed(&"pause") and DisplayServer.get_name() != "headless":
		var captured: bool = Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if captured else Input.MOUSE_MODE_CAPTURED


func _process(delta: float) -> void:
	_head.rotation.x = head_pitch
	_avatar.speed = move_speed
	_avatar.look_pitch = head_pitch
	_avatar.carrying = _held != null
	if not is_local():
		return
	_arms.holding = _held != null
	inspecting = _held != null and Input.is_action_pressed(&"use_secondary")
	var pad: Vector2 = Input.get_vector(&"look_left", &"look_right", &"look_up", &"look_down")
	if pad != Vector2.ZERO:
		look(-pad.x * PAD_LOOK_SPEED * delta, -pad.y * PAD_LOOK_SPEED * delta)


func _physics_process(delta: float) -> void:
	if not is_local():
		return
	var input: Vector2 = scripted_input
	if input == Vector2.ZERO and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		input = Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")
	var wish: Vector3 = (basis * Vector3(input.x, 0.0, input.y)).limit_length(1.0)
	var target: Vector3 = wish * WALK_SPEED * carry_slowdown()
	var planar: Vector3 = Vector3(velocity.x, 0.0, velocity.z).move_toward(
		target, ACCELERATION * delta
	)
	velocity = Vector3(
		planar.x, velocity.y - GRAVITY * delta if not is_on_floor() else 0.0, planar.z
	)
	move_and_slide()
	move_speed = Vector2(velocity.x, velocity.z).length()
	_push_objects()
	_update_focus()


func is_local() -> bool:
	return is_multiplayer_authority()


## Gira la mirada: [param yaw] a los lados y [param pitch] arriba o abajo, en radianes.
func look(yaw: float, pitch: float) -> void:
	rotate_y(yaw)
	var inverted: float = -1.0 if Settings.invert_y else 1.0
	head_pitch = clampf(head_pitch + pitch * inverted, -LOOK_LIMIT, LOOK_LIMIT)


## Usa lo que tiene delante, o suelta lo que lleva.
func interact() -> void:
	if _held != null:
		_held.request_drop.rpc_id(Carryable.HOST_PEER)
	elif _focus != null:
		if _arms != null:
			_arms.reach()
		_focus.interact(self)


func eye_position() -> Vector3:
	return _head.global_position


func can_carry() -> bool:
	return _held == null


func held_item() -> Carryable:
	return _held


func focused() -> Interactable:
	return _focus


## Lo llama el objeto cuando el anfitrión decide que este jugador lo lleva.
func set_held_item(item: Carryable) -> void:
	_held = item
	if is_local():
		hold_euler = Vector3.ZERO
		inspecting = false


## Cuánto frena lo que lleva: de 1 (nada) hacia 0.
func carry_slowdown() -> float:
	if _held == null:
		return 1.0
	return 1.0 / (1.0 + _held.state.data.weight / HALF_SPEED_WEIGHT)


## Dónde debe estar un objeto de [param mass] kilos que este jugador lleva.
func hold_transform(mass: float) -> Transform3D:
	var offset: Vector3 = INSPECT_OFFSET if inspecting else HOLD_OFFSET
	if not inspecting:
		# Lo pesado cuelga más bajo.
		offset.y -= minf(0.16, mass * 0.012)
	var head: Transform3D = Transform3D(
		Basis(Vector3.UP, rotation.y) * Basis(Vector3.RIGHT, head_pitch), eye_position()
	)
	var turn: Basis = Basis(Vector3.UP, rotation.y) * Basis.from_euler(hold_euler)
	return Transform3D(turn, head * offset)


## Empuja los objetos sueltos con los que choca. La física es del anfitrión.
func _push_objects() -> void:
	if not multiplayer.is_server():
		return
	for index: int in get_slide_collision_count():
		var collision: KinematicCollision3D = get_slide_collision(index)
		var body: RigidBody3D = collision.get_collider() as RigidBody3D
		if body != null:
			body.apply_central_impulse(-collision.get_normal() * 0.35 * minf(body.mass, 4.0))


func _update_focus() -> void:
	var found: Interactable = null
	if _held == null:
		var from: Vector3 = _camera.global_position
		var to: Vector3 = from - _camera.global_basis.z * REACH
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
			from, to, MASK_REACH, [get_rid()]
		)
		var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			found = Interactable.of(hit["collider"] as Node)
			if found != null and not found.enabled:
				found = null
	if found == _focus:
		return
	if _focus != null and is_instance_valid(_focus):
		_focus.set_focused(false)
	_focus = found
	if _focus != null:
		_focus.set_focused(true)
	_reticle.show_target(_focus)
