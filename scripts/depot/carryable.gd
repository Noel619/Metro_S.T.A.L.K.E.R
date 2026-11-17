class_name Carryable
extends Node
## Hace que un objeto físico se pueda coger, girar, inspeccionar y soltar.
##
## Es hijo del [RigidBody3D] del objeto. El anfitrión manda sobre la física:
## quien quiere coger algo se lo pide, y el anfitrión lleva el objeto hacia las
## manos de ese jugador con velocidades, no teletransportándolo. Así choca con
## lo que hay por medio y el peso se nota: lo pesado tarda en acomodarse, cuelga
## más bajo y se cae de las manos si se queda atascado.
##
## Lo que se mueven las manos al andar o al girar se sigue sin retraso (si no,
## al andar el objeto se quedaría atrás y acabaría dentro del cuerpo). Y quien
## lo lleva lo ve dibujado justo en sus manos (el nodo "Visual"): la física va
## a 60 pasos por segundo y, en los invitados, con la red de por medio; si lo
## dibujara donde está el cuerpo físico, temblaría o se quedaría atrás al girar.
## Solo cuando algo lo para de verdad se dibuja donde está.

signal holder_changed(peer_id: int)
## Ha cambiado su estado (en todos los equipos).
signal state_changed

## Peer que puede pedir sin que haya red de por medio (el propio anfitrión).
const HOST_PEER: int = 1
## Distancia máxima para coger algo, medida desde los ojos.
const GRAB_RANGE: float = 2.6
## Si el objeto se queda así de lejos de las manos tanto tiempo, se suelta solo.
const BREAK_DISTANCE: float = 0.5
const STUCK_TIME: float = 0.35
const MAX_SPEED: float = 12.0
const MAX_TURN_SPEED: float = 16.0
## Lo más deprisa que se corrige la distancia (o el giro) hasta las manos: si
## algo lo aprieta contra una pared, no se lo empuja con una fuerza sin límite.
const MAX_CORRECTION: float = 6.0
const MAX_TURN_CORRECTION: float = 10.0
## Lo ligero lleva siempre detección continua de choques; lo que se lleva, también.
const CCD_WEIGHT: float = 1.0
## Holgura que se deja al seguir el movimiento de las manos (m/s).
const FOLLOW_SLACK: float = 0.3
## Lo que se encoge la forma con la que se mira si cabe lo que se lleva.
const CAST_INSET: float = 0.01
## Hasta esta distancia de las manos, quien lo lleva lo ve en ellas; a partir
## de la otra, donde está de verdad. Se compara con donde estaban las manos en
## este rato: lo que dice la física puede llegar tarde (en los invitados, lo
## que tarda la red), y eso no es que algo lo pare.
const SHOWN_NEAR: float = 0.06
const SHOWN_FAR: float = 0.2
const RECENT_TIME: float = 0.6
const RECENT_TIME_HOST: float = 0.05
## En los invitados, lo que se mueve de más por los paquetes que llegan juntos.
const GUEST_SLACK: float = 0.05
## Por debajo de esta mezcla con donde está de verdad, se ve en las manos.
const IN_HANDS: float = 0.1
## Rapidez con la que el dibujo vuelve a su sitio al soltarlo.
const SETTLE: float = 12.0

var state: ItemState
## Quién lo lleva (0: nadie).
var holder_peer: int = 0
## Su estado tal como se replica ([method ItemState.to_dict]): lo cambia el
## anfitrión con [method set_values] y lo recibe quien llega tarde.
var synced_state: Dictionary = {}:
	set(value):
		synced_state = value
		if state != null and not value.is_empty():
			_load_values(value)

var _body: RigidBody3D
var _visual: Node3D
## La caja que envuelve sus mallas, en sus propios ejes.
var _bounds: AABB = AABB()
var _cast_shape: BoxShape3D
var _stuck_time: float = 0.0
## El sitio de las manos y cómo estaba quien lo lleva en el paso anterior.
var _last_target: Transform3D = Transform3D.IDENTITY
var _last_eyes: Vector3 = Vector3.ZERO
var _last_look: Vector2 = Vector2.ZERO
var _has_last: bool = false
## Quien lo lleva en este equipo ya lo ve en sus manos (no volando hacia ellas).
var _in_hands: bool = false
## Dónde ha querido tenerlo hace poco quien lo lleva en este equipo: [segundos, centro].
var _recent: Array[Vector4] = []


func _ready() -> void:
	_body = get_parent() as RigidBody3D
	_visual = _body.get_node_or_null(^"Visual") as Node3D
	_bounds = GripModifier.bounds_of(_body)
	_cast_shape = BoxShape3D.new()
	_cast_shape.size = (_bounds.size - Vector3.ONE * CAST_INSET * 2.0).max(Vector3.ONE * 0.01)
	var interactable: Interactable = Interactable.of(_body)
	if interactable != null:
		interactable.interacted.connect(_on_interacted)


## Rigidez con la que un objeto de [param mass] kilos se acomoda en las manos.
static func follow_stiffness(mass: float) -> float:
	return clampf(22.0 / (1.0 + mass * 0.22), 3.5, 20.0)


func is_held() -> bool:
	return holder_peer != 0


## Cambia valores de su estado (las claves de [method ItemState.to_dict]). Solo
## el anfitrión: lo ven todos.
func set_values(values: Dictionary) -> void:
	if not multiplayer.is_server():
		return
	var merged: Dictionary = state.to_dict()
	merged.merge(values.duplicate(true), true)
	synced_state = merged


## El cuerpo físico del objeto.
func body() -> RigidBody3D:
	return _body


## La caja que envuelve sus mallas, en sus propios ejes.
func bounds() -> AABB:
	return _bounds


## La mitad de las medidas del objeto (ancho, alto y fondo).
func half_size() -> Vector3:
	return _bounds.size / 2.0


## Lo que se dibuja del objeto: es lo que agarran las manos.
func visual() -> Node3D:
	return _visual if _visual != null else _body


## Su forma, como una caja centrada, para mirar con qué choca.
func cast_shape() -> BoxShape3D:
	return _cast_shape


func body_rid() -> RID:
	return _body.get_rid()


## ¿Lo ve ya en sus manos quien lo lleva en este equipo? Mientras vuela hacia
## ellas (o si algo lo para), no.
func in_hands() -> bool:
	return _in_hands


## Dónde lo quiere ahora quien lo lleva (el transform de su cuerpo).
func hold_target() -> Transform3D:
	var player: Player = Player.find(get_tree(), holder_peer)
	return player.carry_target(self, false) if player != null else _body.global_transform


func _on_interacted(player: Node) -> void:
	if not is_held() and player is Player and (player as Player).can_carry():
		request_grab.rpc_id(HOST_PEER)


## Un jugador pide coger el objeto. Decide el anfitrión.
@rpc("any_peer", "call_local", "reliable")
func request_grab() -> void:
	if not multiplayer.is_server() or is_held():
		return
	var peer: int = _sender()
	var player: Player = Player.find(get_tree(), peer)
	if player == null or player.held_item() != null:
		return
	if player.eye_position().distance_to(_body.global_position) > GRAB_RANGE:
		return
	_set_holder.rpc(peer)


## El anfitrión se lo quita de las manos a quien lo lleve (porque desaparece).
func force_drop() -> void:
	if multiplayer.is_server() and is_held():
		_set_holder.rpc(0)


## Quien lo lleva pide soltarlo.
@rpc("any_peer", "call_local", "reliable")
func request_drop() -> void:
	if multiplayer.is_server() and holder_peer == _sender():
		_set_holder.rpc(0)


@rpc("authority", "call_local", "reliable")
func _set_holder(peer: int) -> void:
	var previous: Player = Player.find(get_tree(), holder_peer)
	if previous != null:
		previous.set_held_item(null)
		_body.remove_collision_exception_with(previous)
	holder_peer = peer
	_stuck_time = 0.0
	_has_last = false
	var player: Player = Player.find(get_tree(), peer)
	if player != null:
		# Su cuerpo no lo empuja: quien lo lleva se para antes de chocar con ello.
		_body.add_collision_exception_with(player)
		player.set_held_item(self)
	if multiplayer.is_server():
		_body.gravity_scale = 0.0 if is_held() else 1.0
		_body.continuous_cd = is_held() or state.data.weight < CCD_WEIGHT
		_body.sleeping = false
	holder_changed.emit(peer)


func _physics_process(delta: float) -> void:
	if not is_held() or not multiplayer.is_server():
		return
	var player: Player = Player.find(get_tree(), holder_peer)
	if player == null:
		_set_holder.rpc(0)
		return
	var target: Transform3D = player.carry_target(self)
	var center: Vector3 = _bounds.get_center()
	var wanted: Vector3 = target * center
	var offset: Vector3 = wanted - _body.global_transform * center
	var wanted_turn: Quaternion = target.basis.get_rotation_quaternion()
	# Lo que se han movido las manos porque el jugador anda o gira se sigue sin
	# retraso. Lo demás (acercarlo, girarlo) se nota según lo que pesa.
	var carried: Vector3 = Vector3.ZERO
	var turning: Vector3 = Vector3.ZERO
	if _has_last:
		var look_speed: Vector2 = (
			Vector2(
				angle_difference(_last_look.x, player.rotation.y), player.head_pitch - _last_look.y
			)
			/ delta
		)
		var radius: float = wanted.distance_to(player.eye_position())
		var bound: float = (
			player.eye_position().distance_to(_last_eyes) / delta
			+ (absf(look_speed.x) + absf(look_speed.y)) * radius
			+ FOLLOW_SLACK
		)
		carried = ((wanted - _last_target * center) / delta).limit_length(bound)
		var step: Quaternion = wanted_turn * _last_target.basis.get_rotation_quaternion().inverse()
		turning = (_rotation_vector(step) / delta).limit_length(absf(look_speed.x) + FOLLOW_SLACK)
	_last_target = target
	_last_eyes = player.eye_position()
	_last_look = Vector2(player.rotation.y, player.head_pitch)
	_has_last = true
	var stiffness: float = follow_stiffness(_body.mass)
	var correction: Vector3 = (offset * stiffness).limit_length(MAX_CORRECTION)
	_body.linear_velocity = (carried + correction).limit_length(MAX_SPEED)
	var error: Vector3 = _rotation_vector(
		wanted_turn * _body.global_basis.get_rotation_quaternion().inverse()
	)
	var straighten: Vector3 = (error * stiffness).limit_length(MAX_TURN_CORRECTION)
	_body.angular_velocity = (turning + straighten).limit_length(MAX_TURN_SPEED)
	# Atascado contra algo, lejos de las manos: acaba por caerse.
	_stuck_time = _stuck_time + delta if offset.length() > BREAK_DISTANCE else 0.0
	if _stuck_time > STUCK_TIME:
		_set_holder.rpc(0)


func _process(delta: float) -> void:
	if _visual == null:
		return
	var player: Player = null
	if holder_peer != 0 and holder_peer == multiplayer.get_unique_id():
		player = Player.find(get_tree(), holder_peer)
	if player == null:
		# Nadie de este equipo lo lleva: se dibuja donde está.
		_in_hands = false
		_recent.clear()
		if _visual.transform.is_equal_approx(Transform3D.IDENTITY):
			_visual.transform = Transform3D.IDENTITY
		else:
			_visual.transform = _visual.transform.interpolate_with(
				Transform3D.IDENTITY, 1.0 - exp(-SETTLE * delta)
			)
		return
	var target: Transform3D = player.carry_target(self, false)
	var center: Vector3 = _bounds.get_center()
	var now: float = Time.get_ticks_msec() / 1000.0
	var wanted: Vector3 = target * center
	_recent.append(Vector4(now, wanted.x, wanted.y, wanted.z))
	var window: float = RECENT_TIME_HOST if multiplayer.is_server() else RECENT_TIME
	while _recent[0].x < now - window:
		_recent.pop_front()
	# Lo lejos que está de donde se ha querido tener en este rato.
	var actual: Vector3 = _body.global_transform * center
	var gap: float = INF
	for past: Vector4 in _recent:
		gap = minf(gap, actual.distance_to(Vector3(past.y, past.z, past.w)))
	var slack: float = 0.0 if multiplayer.is_server() else GUEST_SLACK
	var stuck: float = smoothstep(SHOWN_NEAR + slack, SHOWN_FAR + slack, gap)
	_in_hands = stuck < IN_HANDS
	# Trabajando, se dibuja sobre lo que se trabaja (la física sigue en las manos).
	var pose: Transform3D = player.work_pose(self) if player.working else target
	var shown: Transform3D = pose.interpolate_with(_body.global_transform, stuck)
	_visual.transform = _body.global_transform.affine_inverse() * shown


func _load_values(values: Dictionary) -> void:
	var fresh: ItemState = ItemState.from_dict(values)
	state.condition = fresh.condition
	state.contamination = fresh.contamination
	state.price = fresh.price
	state.bagged = fresh.bagged
	state.extra = fresh.extra
	state_changed.emit()


## El giro [param turn] como un vector: su eje por el ángulo (el camino corto).
static func _rotation_vector(turn: Quaternion) -> Vector3:
	if turn.w < 0.0:
		turn = -turn
	var angle: float = turn.get_angle()
	if angle < 0.0001:
		return Vector3.ZERO
	return turn.get_axis() * angle


func _sender() -> int:
	var peer: int = multiplayer.get_remote_sender_id()
	return peer if peer != 0 else multiplayer.get_unique_id()
