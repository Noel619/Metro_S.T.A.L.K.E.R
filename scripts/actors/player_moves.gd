class_name PlayerMoves
extends RefCounted
## Lo que el cuerpo del jugador hace con el mundo en la superficie (F3-01): mirar
## si cabe de pie, asomarse sin meter la cabeza en una pared, encaramarse a lo
## que llega a la cintura y trepar por escaleras y cuerdas ([Climbable]). Lo usa
## [Player], en el equipo de quien lo controla.

## Encaramarse: lo que tiene que medir el borde (sobre los pies), lo lejos que se
## busca delante y lo que se tarda.
const MANTLE_LOW: float = 0.45
const MANTLE_HIGH: float = 1.25
const MANTLE_REACH: float = 0.75
const MANTLE_TIME: float = 0.5
## Asomarse: lo que se deja entre la cabeza y una pared.
const LEAN_MARGIN: float = 0.15
## Trepar: lo que queda el cuerpo de los peldaños y lo que tira hacia ellos; arriba,
## si no se cabe donde dice la escalera, se prueba un poco más cerca del borde.
const HANG_GAP: float = 0.38
const HANG_PULL: float = 8.0
const LANDING_RETRY: float = 0.2
## Mirando más abajo que esto, adelante es bajar (y atrás, subir); al agarrarse
## arriba se mira hacia abajo.
const LOOKING_DOWN: float = -0.35
const GRAB_PITCH: float = -0.7

## Encaramándose: de dónde a dónde y cuánto lleva (de 0 a 1; negativo: no).
var _from: Vector3 = Vector3.ZERO
var _to: Vector3 = Vector3.ZERO
var _t: float = -1.0
var _crouch_before: bool = false
## A lo que está agarrado (o null).
var _climb: Climbable = null


## Hay sitio sobre la cabeza de [param player] (con el cuerpo de [param height]
## ahora) para ponerse de pie.
static func can_stand(player: Player, height: float) -> bool:
	if player.crouch <= 0.0 or not player.is_inside_tree():
		return true
	var space: PhysicsDirectSpaceState3D = player.get_world_3d().direct_space_state
	var from: Vector3 = player.global_position + Vector3.UP * (height - 0.05)
	var to: Vector3 = player.global_position + Vector3.UP * (PlayerBody.STAND_HEIGHT + 0.05)
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, to, Player.MASK_PLAYERS, [player.get_rid()]
	)
	return space.intersect_ray(query).is_empty()


## Lo que se puede asomar de verdad [param player] ([param amount], de -1 a 1): si
## hay una pared al lado, la cabeza se queda antes de tocarla.
static func free_lean(player: Player, amount: float) -> float:
	if is_zero_approx(amount) or not player.is_inside_tree():
		return amount
	var eyes: float = (
		Player.EYE_HEIGHTS[player.variant] * lerpf(1.0, PlayerBody.CROUCH_EYES, player.crouch)
	)
	var center: Vector3 = player.global_position + Vector3.UP * eyes
	var side: Vector3 = player.global_basis.x * signf(amount)
	var reach: float = absf(amount) * PlayerBody.LEAN_DISTANCE
	var space: PhysicsDirectSpaceState3D = player.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		center, center + side * (reach + LEAN_MARGIN), Player.MASK_PLAYERS, [player.get_rid()]
	)
	var hit: Dictionary = space.intersect_ray(query)
	if hit.is_empty():
		return amount
	var free: float = maxf(0.0, center.distance_to(hit["position"]) - LEAN_MARGIN)
	return signf(amount) * minf(absf(amount), free / PlayerBody.LEAN_DISTANCE)


## Está encaramándose.
func mantling() -> bool:
	return _t >= 0.0


## Si delante de [param player] hay un borde a la altura de la cintura y sitio
## encima, empieza a encaramarse a él ([param radius]: el de su cuerpo).
func try_mantle(player: Player, radius: float) -> bool:
	var held: Carryable = player.held_item()
	if held != null and held.state.data.weight > Player.HEAVY_WEIGHT:
		return false
	var space: PhysicsDirectSpaceState3D = player.get_world_3d().direct_space_state
	var forward: Vector3 = -player.global_basis.z
	forward.y = 0.0
	forward = forward.normalized()
	var ahead: Vector3 = player.global_position + forward * MANTLE_REACH
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		ahead + Vector3.UP * (MANTLE_HIGH + 0.1),
		ahead + Vector3.UP * (MANTLE_LOW - 0.05),
		Player.MASK_PLAYERS,
		[player.get_rid()]
	)
	var top: Dictionary = space.intersect_ray(query)
	if top.is_empty() or (top["normal"] as Vector3).y < 0.7:
		return false
	var rise: float = (top["position"] as Vector3).y - player.global_position.y
	if rise < MANTLE_LOW or rise > MANTLE_HIGH:
		return false
	# Sitio encima del borde para el cuerpo agachado.
	var landing: Vector3 = top["position"]
	if not fits_crouched(player, radius, landing):
		return false
	_start_mantle(player, landing + Vector3.UP * 0.02)
	return true


## Cabe [param player] agachado (con un cuerpo de [param radius]) de pie en [param feet].
static func fits_crouched(player: Player, radius: float, feet: Vector3) -> bool:
	var space: PhysicsDirectSpaceState3D = player.get_world_3d().direct_space_state
	var room: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var probe: CapsuleShape3D = CapsuleShape3D.new()
	probe.radius = radius
	probe.height = PlayerBody.CROUCH_HEIGHT
	room.shape = probe
	room.transform = Transform3D(
		Basis(), feet + Vector3.UP * (PlayerBody.CROUCH_HEIGHT * 0.5 + 0.05)
	)
	room.collision_mask = Player.MASK_PLAYERS
	room.exclude = [player.get_rid()]
	return space.intersect_shape(room, 1).is_empty()


## Está agarrado a una escalera o a una cuerda.
func climbing() -> bool:
	return _climb != null and is_instance_valid(_climb)


## A lo que está agarrado (o null).
func climbing_on() -> Climbable:
	return _climb if climbing() else null


## Un paso de trepar: si [param player] está agarrado (o se agarra ahora) lo mueve
## y devuelve true; si no, false. [param input] es el de andar (y negativa:
## adelante: sube, o baja si se mira hacia abajo), [param jump] si ha saltado
## (suelta) y [param radius] el de su cuerpo.
func step_climb(player: Player, input: Vector2, jump: bool, radius: float, delta: float) -> bool:
	if not climbing():
		_climb = null
		if jump or not _grab(player, input):
			return false
	if jump:
		_climb = null
		return false
	var on: Climbable = _climb
	var level: float = on.level_of(player.global_position)
	var push: float = -input.y
	if player.head_pitch < LOOKING_DOWN:
		push = -push
	if push > 0.3 and level >= on.height - 0.08 and _leave_at_top(player, on, radius):
		return true
	if push < -0.3 and player.is_on_floor() and level < 0.3:
		_climb = null
		return false
	var hang: Vector3 = on.hang_point(clampf(level, -0.4, on.height), HANG_GAP)
	var pull: Vector3 = (hang - player.global_position) * HANG_PULL
	var rise: float = push * on.speed
	if level >= on.height and rise > 0.0:
		rise = 0.0
	player.velocity = Vector3(pull.x, rise, pull.z)
	player.move_and_slide()
	player.body.update(delta, false, false, player.carried_weight(), 0.0, true)
	player.crouch = player.body.crouch
	# Lo que sube o baja (lo usa la animación de trepar).
	player.move_speed = absf(player.velocity.y)
	return true


## Se agarra a lo que tiene delante, si empuja hacia ello (o, en un rellano, si anda
## hacia el borde de espaldas a ello: se da la vuelta y se agarra arriba).
func _grab(player: Player, input: Vector2) -> bool:
	if absf(input.y) < 0.3:
		return false
	var held: Carryable = player.held_item()
	if held != null and held.state.data.weight > Player.HEAVY_WEIGHT:
		return false
	var wish: Vector3 = player.global_basis * Vector3(input.x, 0.0, input.y)
	for node: Node in player.get_tree().get_nodes_in_group(Climbable.GROUP):
		var on: Climbable = node as Climbable
		if on == null:
			continue
		if input.y < 0.0 and on.holds(player.global_position) and on.faces(wish):
			_climb = on
			return true
		if on.at_top(player.global_position) and on.faces(-wish):
			_climb = on
			player.rotation.y = on.facing_yaw()
			player.head_pitch = minf(player.head_pitch, GRAB_PITCH)
			player.global_position = on.hang_point(on.height - 0.3, HANG_GAP)
			player.velocity = Vector3.ZERO
			return true
	return false


## Arriba: pasa al rellano, si cabe (agachado, si hace falta).
func _leave_at_top(player: Player, on: Climbable, radius: float) -> bool:
	for depth: float in [on.landing_depth, on.landing_depth - LANDING_RETRY]:
		var spot: Vector3 = on.landing(depth)
		if fits_crouched(player, radius, spot):
			_climb = null
			_start_mantle(player, spot)
			return true
	return false


func _start_mantle(player: Player, to: Vector3) -> void:
	_from = player.global_position
	_to = to
	_t = 0.0
	_crouch_before = player.body.crouch_wanted
	player.body.crouch_wanted = true


## Un paso de encaramarse: primero sube y después avanza, por encima del borde.
func step_mantle(player: Player, delta: float) -> void:
	_t = minf(1.0, _t + delta / MANTLE_TIME)
	var up: float = smoothstep(0.0, 0.6, _t)
	var along: float = smoothstep(0.35, 1.0, _t)
	player.global_position = Vector3(
		lerpf(_from.x, _to.x, along), lerpf(_from.y, _to.y, up), lerpf(_from.z, _to.z, along)
	)
	player.body.update(delta, false, false, player.carried_weight(), 0.0, false)
	player.crouch = player.body.crouch
	player.velocity = Vector3.ZERO
	player.move_speed = 0.0
	if _t >= 1.0:
		_t = -1.0
		player.body.crouch_wanted = _crouch_before
