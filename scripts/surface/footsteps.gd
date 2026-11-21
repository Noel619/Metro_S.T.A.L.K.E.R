class_name Footsteps
extends Node
## Los pasos de un jugador (F3-01): cuenta las zancadas, mira qué pisa y cuánto
## suena cada una, y lo que suena al caer de alto o al jadear.
##
## Funciona igual en todos los equipos y para todos los jugadores, con lo que ya
## se replica (dónde está, a qué velocidad va y si va agachado): cada equipo
## dibuja las ondas de tinta de los pasos que ve, y el anfitrión, además, se los
## da a la IA ([Stimuli]). Así el ruido de un invitado lo decide el anfitrión, sin
## fiarse de lo que diga su equipo.

## Un salto de más de esto en un fotograma es un traslado (despertar, subir), no un paso.
const TELEPORT: float = 3.0
## Hasta dónde se busca el suelo bajo los pies.
const GROUND_CHECK: float = 0.35
## Se dibujan las ondas de los pasos de quien está a menos de esto de la cámara.
const RIPPLE_DISTANCE: float = 80.0
## Lo fuerte que se dibujan las ondas de los pasos.
const RIPPLE_STRENGTH: Dictionary = {
	PlayerBody.Gait.CROUCH: 0.45,
	PlayerBody.Gait.WALK: 0.62,
	PlayerBody.Gait.RUN: 0.95,
}
## Cada cuánto suena el jadeo.
const PANT_SECONDS: float = 1.4

## Zancadas desde que se puso (el podómetro lee esto).
var steps: int = 0
## Lo último que se pisó y lo que sonó (para la depuración).
var last_ground: StringName = NoiseRules.DEFAULT_GROUND
var last_radius: float = 0.0
## Al caer de alto: lo que cayó la última vez (en metros).
var last_fall: float = 0.0
## Las cosas que van sueltas en la mochila y suenan al andar (la mochila lo dice: F3-03).
var loose_items: int = 0

var _player: Player
var _last: Vector3 = Vector3.INF
## Hacia dónde iba (para las huellas) y qué pie toca.
var _heading: float = 0.0
var _left: bool = false
var _stride_left: float = 0.0
var _airborne: bool = false
var _air_top: float = 0.0
var _pant_clock: float = 0.0


func setup(player: Player) -> void:
	_player = player
	name = "Pasos"


func _physics_process(delta: float) -> void:
	if _player == null or not _player.is_inside_tree():
		return
	var position: Vector3 = _player.global_position
	if _last == Vector3.INF:
		_last = position
		return
	var flat: Vector2 = Vector2(position.x - _last.x, position.z - _last.z)
	var moved: float = flat.length()
	if moved > 0.001:
		_heading = atan2(flat.x, flat.y)
	var teleported: bool = position.distance_to(_last) > TELEPORT
	_last = position
	if teleported:
		_airborne = false
		return
	var space: PhysicsDirectSpaceState3D = _player.get_world_3d().direct_space_state
	var hit: Dictionary = Ground.below(space, position, GROUND_CHECK, [_player.get_rid()])
	if _player.climbing:
		# Trepando no se cae: si se suelta, la caída cuenta desde donde se soltó.
		_airborne = true
		_air_top = position.y
		return
	if hit.is_empty():
		if not _airborne:
			_airborne = true
			_air_top = position.y
		_air_top = maxf(_air_top, position.y)
		return
	if _airborne:
		_airborne = false
		_landed(_air_top - position.y, space, hit)
	_pant(delta)
	var gait: PlayerBody.Gait = PlayerBody.gait_for(_player.move_speed, _player.crouch)
	if gait == PlayerBody.Gait.STILL:
		return
	_stride_left += moved / float(PlayerBody.STRIDES[gait])
	while _stride_left >= 1.0:
		_stride_left -= 1.0
		steps += 1
		_step(gait, space, hit)


## Pone a cero el podómetro.
func reset_count() -> void:
	steps = 0


func _step(gait: PlayerBody.Gait, space: PhysicsDirectSpaceState3D, hit: Dictionary) -> void:
	last_ground = Ground.material_of(space, hit, [_player.get_rid()])
	var load_kg: float = _player.carried_weight()
	last_radius = NoiseRules.step_radius(gait, last_ground, load_kg)
	var feet: Vector3 = hit["position"]
	_make(feet, last_radius, NoiseRules.STEP, RIPPLE_STRENGTH.get(gait, 0.5))
	_leave_tracks(feet)
	var rattle: float = NoiseRules.rattle_radius(gait, loose_items)
	if rattle > 0.0:
		_make(feet + Vector3.UP * 0.9, rattle, NoiseRules.RATTLE, 0.4)


## El olor (para la IA, en el anfitrión) y, en la nieve, la huella de la bota.
func _leave_tracks(feet: Vector3) -> void:
	var tracks: Tracks = Tracks.find(get_tree())
	if tracks == null:
		return
	var bleeding: bool = _player.condition != null and _player.condition.bleeding
	tracks.drop(feet, _player.peer_id, bleeding)
	_left = not _left
	if last_ground == NoiseRules.DEFAULT_GROUND:
		var side: Vector3 = Vector3(cos(_heading), 0.0, -sin(_heading)) * (0.11 if _left else -0.11)
		tracks.print_step(feet + side, _heading)


func _landed(fall: float, space: PhysicsDirectSpaceState3D, hit: Dictionary) -> void:
	last_fall = fall
	var ground: StringName = Ground.material_of(space, hit, [_player.get_rid()])
	var radius: float = NoiseRules.landing_radius(fall, ground)
	if radius > 0.0:
		_make(hit["position"], radius, NoiseRules.LANDING, 0.8)
	if _player.condition != null:
		_player.condition.fell.emit(fall)


func _pant(delta: float) -> void:
	if not _player.panting:
		_pant_clock = 0.0
		return
	_pant_clock -= delta
	if _pant_clock <= 0.0:
		_pant_clock = PANT_SECONDS
		_make(_player.eye_position(), NoiseRules.sound_radius(&"jadeo"), &"jadeo", 0.3)


## Un ruido de este jugador: la IA lo oye (en el anfitrión) y cada equipo lo ve
## si está cerca.
func _make(where: Vector3, radius: float, kind: StringName, strength: float) -> void:
	if radius <= 0.0:
		return
	if multiplayer.is_server():
		var stimuli: Stimuli = Stimuli.find(get_tree())
		if stimuli != null:
			stimuli.make_noise(where, radius, kind, _player.peer_id, false)
	var ripples: InkRipples = InkRipples.find(get_tree())
	var camera: Camera3D = get_viewport().get_camera_3d()
	if ripples == null or camera == null:
		return
	if camera.global_position.distance_to(where) <= RIPPLE_DISTANCE:
		ripples.add(where, radius, strength)
