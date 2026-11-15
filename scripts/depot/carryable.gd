class_name Carryable
extends Node
## Hace que un objeto físico se pueda coger, girar, inspeccionar y soltar.
##
## Es hijo del [RigidBody3D] del objeto. El anfitrión manda sobre la física:
## quien quiere coger algo se lo pide, y el anfitrión lleva el objeto hacia las
## manos de ese jugador con velocidades, no teletransportándolo. Así choca con
## lo que hay por medio y el peso se nota: lo pesado tarda en seguirte, cuelga
## más bajo y se cae de las manos si lo arrastras contra algo.

signal holder_changed(peer_id: int)

## Peer que puede pedir sin que haya red de por medio (el propio anfitrión).
const HOST_PEER: int = 1
## Distancia máxima para coger algo, medida desde los ojos.
const GRAB_RANGE: float = 2.6
## Si el objeto se queda así de lejos de las manos, se suelta solo.
const BREAK_DISTANCE: float = 1.1
const MAX_SPEED: float = 9.0
const MAX_TURN_SPEED: float = 12.0

var state: ItemState
## Quién lo lleva (0: nadie).
var holder_peer: int = 0

var _body: RigidBody3D
var _stuck_time: float = 0.0


func _ready() -> void:
	_body = get_parent() as RigidBody3D
	var interactable: Interactable = Interactable.of(_body)
	if interactable != null:
		interactable.interacted.connect(_on_interacted)


## Rigidez con la que un objeto de [param mass] kilos sigue a las manos.
static func follow_stiffness(mass: float) -> float:
	return clampf(22.0 / (1.0 + mass * 0.22), 3.5, 20.0)


func is_held() -> bool:
	return holder_peer != 0


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
	var player: Player = Player.find(get_tree(), peer)
	if player != null:
		player.set_held_item(self)
		_body.add_collision_exception_with(player)
	if multiplayer.is_server():
		_body.gravity_scale = 0.0 if is_held() else 1.0
		_body.sleeping = false
	holder_changed.emit(peer)


func _physics_process(delta: float) -> void:
	if not is_held() or not multiplayer.is_server():
		return
	var player: Player = Player.find(get_tree(), holder_peer)
	if player == null:
		_set_holder.rpc(0)
		return
	var target: Transform3D = player.hold_transform(_body.mass)
	var offset: Vector3 = target.origin - _body.global_position
	var stiffness: float = follow_stiffness(_body.mass)
	_body.linear_velocity = (offset * stiffness).limit_length(MAX_SPEED)
	var turn: Quaternion = (
		target.basis.get_rotation_quaternion()
		* _body.global_basis.get_rotation_quaternion().inverse()
	)
	var angle: float = turn.get_angle()
	if angle > PI:
		angle -= TAU
	var spin: Vector3 = turn.get_axis() * angle * stiffness
	_body.angular_velocity = spin.limit_length(MAX_TURN_SPEED) if angle != 0.0 else Vector3.ZERO
	# Atascado contra algo: acaba por caerse de las manos.
	_stuck_time = _stuck_time + delta if offset.length() > BREAK_DISTANCE else 0.0
	if _stuck_time > 0.35:
		_set_holder.rpc(0)


func _sender() -> int:
	var peer: int = multiplayer.get_remote_sender_id()
	return peer if peer != 0 else multiplayer.get_unique_id()
