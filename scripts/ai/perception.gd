class_name Perception
extends Node
## Los sentidos de un agente (F3-09, docs/SUPERFICIE.md 6): vista, oído y olfato
## con viento, y su memoria ([Knowledge]). Solo trabaja en el anfitrión, que es
## quien simula la IA. Se pone como hijo del cuerpo del agente ([member body]),
## que mira hacia su -Z.
##
## - Vista: un cono; dentro de él y del alcance de vista de cada jugador
##   ([method Visibility.assess]), se va fijando: cuanto más cerca, antes. A medio
##   fijar solo sabe que "algo se movió por ahí".
## - Oído: cada ruido de [Stimuli] le llega con lo que tapan el viento, los muros y
##   pasar de dentro a fuera ([method NoiseRules.heard_radius]).
## - Olfato: el viento lleva el olor; a sotavento se huele de lejos, a barlovento
##   casi nada. Y los rastros de [Tracks], con el hocico cerca.
##
## Cada percepción se guarda en la memoria y se avisa con [signal perceived].

signal perceived(percept: Percept)

## Cada cuánto miran y huelen (segundos).
const TICK: float = 0.1
## Más allá de esto no se mira (ni con linterna).
const MAX_SIGHT: float = 260.0
## A medio fijar: desde aquí, "algo se movió".
const GLIMPSE: float = 0.35
## Lo que se olvida de lo que se estaba fijando, por segundo, al dejar de verlo.
const UNSEE_PER_SECOND: float = 0.5
## El olfato: sin viento, en redondo; con viento, a sotavento según su fuerza; a
## barlovento, esto.
const SMELL_DOWNWIND: Array[float] = [15.0, 30.0, 45.0, 60.0]
const SMELL_UPWIND: float = 5.0
## Muros que se cuentan como mucho entre un ruido y quien lo oye.
const MAX_WALLS: int = 3
const WORLD_MASK: int = 1 << 0

## El cuerpo del agente (mira hacia su -Z).
var body: Node3D
var knowledge: Knowledge = Knowledge.new()
## A qué altura van sus ojos y su hocico.
var eye_height: float = 0.7
## Ancho del cono de vista (grados).
var fov_degrees: float = 220.0
## Lo que multiplica el alcance de vista de cada jugador.
var sight_factor: float = 1.0
## Ve sobre todo lo que se mueve (lo quieto le cuesta).
var motion_sight: bool = true
## Lo que multiplica el alcance de cada ruido.
var hearing_factor: float = 1.3
## Lo que multiplica el alcance del olfato.
var smell_factor: float = 1.0
## Lo cerca que tiene que tener el hocico de un rastro para encontrarlo.
var trail_reach: float = 2.5
## Apagado (durmiendo, comiendo con la cabeza metida…): no mira ni huele, pero oye.
var sleeping: bool = false

## Lo fijado de cada jugador (de 0 a 1), por su peer.
var awareness: Dictionary = {}
## Los últimos ruidos que ha oído (para la depuración): {event, heard, walls}.
var heard: Array[Dictionary] = []

var _clock: float = 0.0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = hash(get_path())
	var stimuli: Stimuli = Stimuli.find(get_tree())
	if stimuli != null:
		stimuli.noise_made.connect(_on_noise)


func _physics_process(delta: float) -> void:
	if not multiplayer.is_server() or body == null:
		return
	_clock += delta
	if _clock < TICK:
		return
	var step: float = _clock
	_clock = 0.0
	knowledge.forget(step)
	if sleeping:
		return
	var env: SurfaceEnv = SurfaceEnv.find(get_tree())
	var space: PhysicsDirectSpaceState3D = body.get_world_3d().direct_space_state
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		var player: Player = node as Player
		if player.condition.dead:
			continue
		_look_at(player, step, env, space)
		_smell(player, env, space)
	_sniff_trail()


## Dónde tiene los ojos.
func eye() -> Vector3:
	return body.global_position + Vector3.UP * eye_height


## Hacia dónde mira (horizontal, de largo 1).
func forward() -> Vector3:
	var ahead: Vector3 = -body.global_basis.z
	ahead.y = 0.0
	return ahead.normalized() if ahead.length() > 0.001 else Vector3.FORWARD


## Lo lejos que huele hacia [param from_target] (del rastro hacia el agente) con [param weather].
static func smell_range(weather: Weather, from_target: Vector3, factor: float = 1.0) -> float:
	if weather == null or weather.wind == Weather.Wind.CALMA:
		return SMELL_DOWNWIND[0] * factor
	var flat: Vector3 = Vector3(from_target.x, 0.0, from_target.z)
	if flat.length() < 0.01:
		return SMELL_DOWNWIND[0] * factor
	var along: float = maxf(0.0, flat.normalized().dot(weather.blowing()))
	var downwind: float = SMELL_DOWNWIND[weather.wind]
	return (SMELL_UPWIND + (downwind - SMELL_UPWIND) * pow(along, 1.5)) * factor


func _look_at(
	player: Player, step: float, env: SurfaceEnv, space: PhysicsDirectSpaceState3D
) -> void:
	var peer: int = player.peer_id
	var seen: float = float(awareness.get(peer, 0.0))
	var target: Vector3 = player.global_position + Vector3.UP * player.body_height() * 0.6
	var to: Vector3 = target - eye()
	var distance: float = to.length()
	var visible: bool = false
	var reach: float = 0.0
	if distance <= MAX_SIGHT and _in_cone(to):
		var context: Dictionary = env.context() if env != null else {"hour": 12.0}
		var result: Dictionary = Visibility.assess(
			space, eye(), player, context, motion_sight, [_body_rid()]
		)
		reach = float(result["range"]) * sight_factor
		visible = float(result["cover"]) > 0.0 and distance <= reach
	if visible:
		seen = minf(1.0, seen + step / (0.25 + 2.0 * distance / maxf(reach, 0.1)))
	else:
		seen = maxf(0.0, seen - step * UNSEE_PER_SECOND)
	awareness[peer] = seen
	if not visible:
		return
	if seen >= 1.0:
		var sure: Percept = Percept.create(
			Percept.SIGHT, player.global_position, 1.0, &"presa", Stimuli.clock()
		)
		sure.subject = peer
		sure.truth = peer
		_store(sure)
	elif seen >= GLIMPSE:
		var fuzz: float = distance * 0.12
		var where: Vector3 = (
			player.global_position
			+ Vector3(_rng.randf_range(-fuzz, fuzz), 0.0, _rng.randf_range(-fuzz, fuzz))
		)
		var glimpse: Percept = Percept.create(
			Percept.SIGHT, where, GLIMPSE, &"movimiento", Stimuli.clock()
		)
		glimpse.truth = peer
		_store(glimpse)


func _in_cone(to: Vector3) -> bool:
	var flat: Vector3 = Vector3(to.x, 0.0, to.z)
	if flat.length() < 0.5:
		return true
	return rad_to_deg(forward().angle_to(flat.normalized())) <= fov_degrees * 0.5


func _smell(player: Player, env: SurfaceEnv, space: PhysicsDirectSpaceState3D) -> void:
	var from_target: Vector3 = body.global_position - player.global_position
	var weather: Weather = env.weather if env != null else null
	var reach: float = smell_range(weather, from_target, smell_factor)
	if player.condition.bleeding:
		reach *= 1.5
	var distance: float = Vector2(from_target.x, from_target.z).length()
	if distance > reach:
		return
	# El olor no atraviesa un edificio: dentro con las puertas cerradas no se huele.
	if _walls_between(space, player.global_position + Vector3.UP, eye()) > 1:
		return
	var fuzz: float = distance * 0.2
	var where: Vector3 = (
		player.global_position
		+ Vector3(_rng.randf_range(-fuzz, fuzz), 0.0, _rng.randf_range(-fuzz, fuzz))
	)
	var sure: float = 0.35 + 0.4 * (1.0 - distance / reach)
	var kind: StringName = &"sangre" if player.condition.bleeding else &"presa"
	var percept: Percept = Percept.create(Percept.SMELL, where, sure, kind, Stimuli.clock())
	percept.truth = player.peer_id
	_store(percept)


func _sniff_trail() -> void:
	var tracks: Tracks = Tracks.find(get_tree())
	if tracks == null:
		return
	var nose: Vector3 = body.global_position
	var mark: Dictionary = tracks.freshest_near(nose, trail_reach)
	if mark.is_empty():
		return
	var fresh: float = 1.0 - tracks.age_of(mark)
	var kind: StringName = &"sangre" if mark["blood"] else &"rastro"
	var percept: Percept = Percept.create(
		Percept.SMELL, mark["position"], 0.25 + 0.4 * fresh, kind, Stimuli.clock()
	)
	percept.truth = int(mark["peer"])
	_store(percept)


func _on_noise(event: NoiseEvent) -> void:
	if body == null or not is_instance_valid(body) or not body.is_inside_tree():
		return
	if event.emitter == body.get_instance_id():
		return
	var ear: Vector3 = eye()
	var distance: float = ear.distance_to(event.position)
	if distance > event.radius * hearing_factor:
		return
	var space: PhysicsDirectSpaceState3D = body.get_world_3d().direct_space_state
	var env: SurfaceEnv = SurfaceEnv.find(get_tree())
	var wind: int = env.weather.wind if env != null else 0
	var walls: int = _walls_between(space, event.position + Vector3.UP * 0.3, ear)
	var crosses: bool = _covered(space, event.position) != _covered(space, ear)
	var reach: float = NoiseRules.heard_radius(event.radius * hearing_factor, wind, walls, crosses)
	heard.append({"event": event, "heard": reach, "walls": walls})
	if heard.size() > 12:
		heard.pop_front()
	if distance > reach:
		return
	var sure: float = clampf(1.0 - distance / reach, 0.25, 1.0)
	var fuzz: float = distance * 0.15 * (1.0 - sure)
	var where: Vector3 = (
		event.position + Vector3(_rng.randf_range(-fuzz, fuzz), 0.0, _rng.randf_range(-fuzz, fuzz))
	)
	var percept: Percept = Percept.create(Percept.HEARING, where, sure, event.kind, event.time)
	percept.stimulus = event.id
	percept.truth = event.source
	_store(percept)


## Le cuentan algo (un ladrido de otro de la manada): sale de lo que percibió el otro.
func tell(from: Percept, certainty: float) -> Percept:
	var told: Percept = Percept.create(
		Percept.TOLD, from.position, certainty, from.kind, Stimuli.clock()
	)
	told.subject = from.subject
	told.truth = from.truth
	told.source = from
	_store(told)
	return told


func _store(percept: Percept) -> void:
	knowledge.remember(percept)
	perceived.emit(percept)


func _body_rid() -> RID:
	return (body as CollisionObject3D).get_rid() if body is CollisionObject3D else RID()


func _walls_between(space: PhysicsDirectSpaceState3D, from: Vector3, to: Vector3) -> int:
	var exclude: Array[RID] = []
	var rid: RID = _body_rid()
	if rid.is_valid():
		exclude.append(rid)
	var count: int = 0
	while count < MAX_WALLS:
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
			from, to, WORLD_MASK, exclude
		)
		var hit: Dictionary = space.intersect_ray(query)
		if hit.is_empty():
			break
		count += 1
		exclude.append(hit["rid"])
	return count


func _covered(space: PhysicsDirectSpaceState3D, point: Vector3) -> bool:
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		point + Vector3.UP * 0.3, point + Vector3.UP * Ground.ROOF_CHECK, WORLD_MASK
	)
	return not space.intersect_ray(query).is_empty()
