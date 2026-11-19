class_name Pack
extends Node
## La Jauría (F3-10, docs/SUPERFICIE.md 7): seis perros guiados por la Vieja. Lo que
## decide la manada se decide aquí, en el anfitrión, con lo que perciben sus perros
## ([Perception]) y lo que se cuentan ladrando. Cada perro solo camina, se para y
## pone la pose que le toca ([Dog]).
##
## Modos:
## - Descanso: echados en la guarida, uno de guardia (de noche).
## - Ronda: recorren su ruta en grupo, parándose en sus sitios (de día, al paso; al
##   amanecer y al atardecer, la de caza, al trote).
## - Investigar: uno o dos van a ver un ruido o algo que se movió; los demás miran.
## - Rastreo: siguen un rastro hacia donde es más fresco (la sangre, sin descanso).
## - Tanteo: se acercan a unos 30 m de la presa, se paran y la miran; se abren.
## - Rodeo: la rodean, cortándole las salidas, y cierran el círculo.
## - Persecución: si la presa corre delante de ellos, o al cerrarse el rodeo.
## - Ataque: muerden de uno en uno y se apartan.
## - Comer: un cebo; la Vieja come primero.
## - Retirada: la presa se les ha ido (arriba, dentro): dan vueltas y se van.
##
## Prueba de justicia: cada decisión con sitio sale de algo que percibió algún perro
## de la manada ([member memory]).

enum Mode {
	DESCANSO, RONDA, INVESTIGAR, RASTREO, TANTEO, RODEO, PERSECUCION, ATAQUE, COMER, RETIRADA
}

const MODE_NAMES: PackedStringArray = [
	"descanso",
	"ronda",
	"investigar",
	"rastreo",
	"tanteo",
	"rodeo",
	"persecución",
	"ataque",
	"comer",
	"retirada",
]
## Los pelajes de los seis, por orden: la Vieja primero.
const COATS: PackedStringArray = ["vieja", "pardo", "negro", "pardo", "negro", "pardo"]
const SIZES: Array[float] = [1.06, 1.0, 0.97, 0.94, 1.02, 0.9]
## Cada cuánto piensa la manada.
const THINK_SECONDS: float = 0.25
## Lo que tiene que saber de una presa para ir a por ella, y de una pista para mirar.
const PREY_CERTAINTY: float = 0.45
const CLUE_CERTAINTY: float = 0.22
## Tanteo: a qué distancia se paran y cuánto tiempo miran.
const PROBE_DISTANCE: float = 28.0
const PROBE_SECONDS: Vector2 = Vector2(6.0, 10.0)
## Rodeo: el radio con el que empiezan, el que cierran y lo rápido que lo cierran.
const RING_START: float = 16.0
const RING_END: float = 6.0
const RING_CLOSE_SPEED: float = 0.7
## Persecución: si la presa va a esta velocidad o más, corre.
const RUNNING_PREY: float = 3.4
## Ataque: a qué distancia muerde, lo que tarda el mordisco en cerrar la boca y lo
## que se aparta después.
const BITE_REACH: float = 1.5
const BITE_DELAY: float = 0.35
const BITE_RETREAT: float = 5.0
const BITE_COOLDOWN: float = 3.5
## No llega a lo que está más alto que esto sobre lo que pisa (un techo de coche).
const REACH_HEIGHT: float = 1.0
## Comer un cebo: lo que dura.
const EAT_SECONDS: float = 40.0
## Se les ha ido: a los cuántos segundos sin poder llegar a la presa se van.
const GIVE_UP_SECONDS: float = 35.0
## El ladrido que avisa a los demás (y que se oye).
const BARK: StringName = &"ladrido"
const BARK_RADIUS: float = 45.0
## Lejos de todos los jugadores no miran ni huelen (no hay nada que percibir).
const SENSE_RANGE: float = 220.0
## Lo que es una presa y lo que no es una pista (sus propios ladridos, la comida).
const PREY_KINDS: Array[StringName] = [&"presa", &"sangre"]
const IGNORED_KINDS: Array[StringName] = [&"ladrido", &"cebo"]
## La comida que les atrae (el cebo: tocino, carne).
const BAIT_TOOL: StringName = &"cebo"

## Lo que sabe la manada: lo que ha percibido cada perro y lo que han decidido.
var memory: Knowledge = Knowledge.new()
var mode: Mode = Mode.RONDA
var dogs: Array[Dog] = []
## La ruta del día y la de caza (puntos del mundo) y la guarida.
var patrol: PackedVector3Array = PackedVector3Array()
var hunt: PackedVector3Array = PackedVector3Array()
var den: Vector3 = Vector3.ZERO
## Los sitios de la ruta donde se paran a descansar (índices) y lo que se paran.
var rests: Dictionary = {}
## Para pruebas y para el panel: no sigue la hora (se queda en el modo que se le pone).
var hold_routine: bool = false
## Para las capturas: la manada no piensa (cada perro sigue con lo último que se le dijo).
var paused: bool = false

var _think: float = 0.0
var _mode_time: float = 0.0
var _target: Percept
var _route_index: int = 0
var _rest_left: float = 0.0
var _probe_time: float = 8.0
var _ring: float = RING_START
var _attacker: int = -1
var _bitten: bool = false
var _bite_clock: float = 0.0
var _unreachable: float = 0.0
var _bait: Carryable
var _eaten: float = 0.0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 7203


## Los perros que forman la manada (los pone el nivel). El primero es la Vieja.
func set_dogs(members: Array[Dog]) -> void:
	dogs = members
	for dog: Dog in dogs:
		dog.perception.perceived.connect(_on_perceived.bind(dog))


func leader() -> Dog:
	return dogs[0] if not dogs.is_empty() else null


func mode_name() -> String:
	return MODE_NAMES[mode]


## La presa (o la pista) que la manada tiene entre ojos ahora.
func target() -> Percept:
	return _target


## Pone a la manada en un modo (las pruebas y el panel de depuración).
func force_mode(new_mode: Mode) -> void:
	_enter(new_mode)


func _physics_process(delta: float) -> void:
	if not multiplayer.is_server() or dogs.is_empty() or paused:
		return
	_mode_time += delta
	_bite_clock = maxf(0.0, _bite_clock - delta)
	_think -= delta
	if _think > 0.0:
		return
	_think = THINK_SECONDS
	memory.forget(THINK_SECONDS)
	_wake_senses()
	_decide()
	_act()


## Quién está despierto: de noche, solo la guardia; lejos de todos, nadie mira.
func _wake_senses() -> void:
	var players: Array[Node] = get_tree().get_nodes_in_group(Player.GROUP)
	for dog: Dog in dogs:
		var near: bool = false
		for node: Node in players:
			if (node as Node3D).global_position.distance_to(dog.global_position) < SENSE_RANGE:
				near = true
				break
		var watching: bool = mode != Mode.DESCANSO or dog == dogs[dogs.size() - 1]
		dog.perception.sleeping = not near or not watching


# -- Decidir -------------------------------------------------------------------


func _decide() -> void:
	var prey: Percept = _best_prey()
	var clue: Percept = _best_clue()
	var bait: Carryable = _visible_bait()
	match mode:
		Mode.COMER:
			_decide_eating(prey)
		Mode.ATAQUE, Mode.PERSECUCION, Mode.RODEO, Mode.TANTEO:
			_decide_hunting(prey, clue, bait)
		_:
			_decide_calm(prey, clue, bait)


## Comiendo: hasta acabar, salvo que la presa se les ponga encima.
func _decide_eating(prey: Percept) -> void:
	if _eaten >= EAT_SECONDS or _bait == null or not is_instance_valid(_bait):
		_finish_bait()
		_enter(Mode.RONDA)
	elif prey != null and _close_to_pack(prey.position, 4.0):
		_hunt(prey)


## Cazando: un cebo los distrae; si pierden a la presa, siguen su rastro o se van.
func _decide_hunting(prey: Percept, clue: Percept, bait: Carryable) -> void:
	if bait != null:
		_start_eating(bait)
	elif prey == null:
		_enter(Mode.RASTREO if clue != null else Mode.RETIRADA, clue)
	else:
		_hunt(prey)


## Tranquilos: un cebo, una presa, una pista o lo que toque a esa hora.
func _decide_calm(prey: Percept, clue: Percept, bait: Carryable) -> void:
	if bait != null:
		_start_eating(bait)
	elif prey != null:
		_hunt(prey)
	elif clue != null and mode != Mode.INVESTIGAR and mode != Mode.RASTREO:
		var trail: bool = clue.kind == &"rastro" or clue.kind == &"sangre"
		_enter(Mode.RASTREO if trail else Mode.INVESTIGAR, clue)
	elif mode == Mode.INVESTIGAR and _mode_time > 14.0:
		_enter(Mode.RONDA)
	elif mode == Mode.RASTREO and clue == null:
		_enter(Mode.RONDA)
	elif mode == Mode.RETIRADA and _mode_time > 12.0:
		_enter(Mode.RONDA)
	elif not hold_routine and (mode == Mode.RONDA or mode == Mode.DESCANSO):
		var resting: bool = is_night()
		if resting and mode != Mode.DESCANSO:
			_enter(Mode.DESCANSO)
		elif not resting and mode == Mode.DESCANSO:
			_enter(Mode.RONDA)


## Va a por una presa: tanteo, rodeo, persecución o ataque, según cómo esté.
func _hunt(prey: Percept) -> void:
	var running: bool = _prey_running(prey)
	if not _reachable(prey):
		_unreachable += THINK_SECONDS
		if _unreachable > GIVE_UP_SECONDS:
			memory.decide(&"retirarse", prey, Stimuli.clock())
			_forget_prey(prey)
			_enter(Mode.RETIRADA, prey)
			return
		if mode != Mode.RODEO:
			_enter(Mode.RODEO, prey)
		_target = prey
		_ring = maxf(_ring, 4.0)
		return
	_unreachable = 0.0
	if running and mode != Mode.PERSECUCION and mode != Mode.ATAQUE:
		_enter(Mode.PERSECUCION, prey)
		return
	match mode:
		Mode.TANTEO:
			_target = prey
			if _mode_time >= _probe_time:
				_enter(Mode.RODEO, prey)
		Mode.RODEO:
			_target = prey
			if _ring <= RING_END + 0.1 and _mode_time > 6.0:
				_enter(Mode.ATAQUE, prey)
		Mode.PERSECUCION:
			_target = prey
			if _nearest_to(prey.position) < BITE_REACH * 3.0:
				_enter(Mode.ATAQUE, prey)
		Mode.ATAQUE:
			_target = prey
		_:
			# La sangre no se tantea: se sigue y se ataca.
			_enter(Mode.PERSECUCION if prey.kind == &"sangre" else Mode.TANTEO, prey)


func _enter(new_mode: Mode, percept: Percept = null) -> void:
	if new_mode != mode:
		_mode_time = 0.0
	mode = new_mode
	_target = percept
	if percept != null:
		memory.decide(StringName(MODE_NAMES[new_mode]), percept, Stimuli.clock())
	else:
		memory.decide(StringName(MODE_NAMES[new_mode]))
	match new_mode:
		Mode.TANTEO:
			_probe_time = _rng.randf_range(PROBE_SECONDS.x, PROBE_SECONDS.y)
			_bark(percept)
		Mode.RODEO:
			_ring = RING_START
		Mode.PERSECUCION:
			_bark(percept)
		Mode.ATAQUE:
			_attacker = -1
			_bitten = false
		Mode.RONDA:
			_route_index = _nearest_route_point(_route())


# -- Actuar ----------------------------------------------------------------------


func _act() -> void:
	match mode:
		Mode.DESCANSO:
			_rest_at_den()
		Mode.RONDA:
			_walk_route()
		Mode.INVESTIGAR:
			_investigate()
		Mode.RASTREO:
			_track()
		Mode.TANTEO:
			_probe()
		Mode.RODEO:
			_surround()
		Mode.PERSECUCION:
			_chase()
		Mode.ATAQUE:
			_attack()
		Mode.COMER:
			_eat()
		Mode.RETIRADA:
			_retreat()


func _rest_at_den() -> void:
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		var spot: Vector3 = den + ring_offset(index, 2.5)
		if dog.global_position.distance_to(spot) > 1.5:
			dog.go_to(spot, Dog.Gait.WALK)
		else:
			dog.stop(&"vigilar" if index == dogs.size() - 1 else &"echado")
		dog.look_point = Vector3.INF
		dog.sniffing = false


func _walk_route() -> void:
	var route: PackedVector3Array = _route()
	if route.is_empty():
		return
	var lead: Dog = leader()
	var gait: Dog.Gait = Dog.Gait.TROT if _hunting_hours() else Dog.Gait.WALK
	if _rest_left > 0.0:
		_rest_left -= THINK_SECONDS
		for index: int in dogs.size():
			var dog: Dog = dogs[index]
			var spot: Vector3 = route[_route_index] + ring_offset(index, 3.0)
			if dog.global_position.distance_to(spot) > 2.0:
				dog.go_to(spot, Dog.Gait.WALK)
			else:
				var poses: Array[StringName] = [&"echado", &"olfatear", &"quieto", &"vigilar"]
				dog.stop(poses[(index + int(_mode_time / 9.0)) % poses.size()])
		return
	var point: Vector3 = route[_route_index]
	if lead.global_position.distance_to(point) < 3.0:
		if rests.has(_route_index) and not _hunting_hours():
			_rest_left = float(rests[_route_index])
		_route_index = (_route_index + 1) % route.size()
		point = route[_route_index]
	lead.go_to(point, gait)
	lead.sniffing = _route_index % 3 == 1
	lead.look_point = Vector3.INF
	_follow(lead, gait, 3.0)


func _investigate() -> void:
	if _target == null:
		_enter(Mode.RONDA)
		return
	var spot: Vector3 = _target.position
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		if index < 2:
			if dog.global_position.distance_to(spot) > 2.5:
				dog.go_to(spot + ring_offset(index, 1.5), Dog.Gait.TROT)
				dog.sniffing = false
			else:
				dog.stop(&"olfatear")
				dog.sniffing = true
		else:
			dog.stop(&"vigilar")
			dog.face(spot)
		dog.look_point = spot + Vector3.UP * 0.5


func _track() -> void:
	var tracks: Tracks = Tracks.find(get_tree())
	var lead: Dog = leader()
	if tracks == null or lead == null:
		_enter(Mode.RONDA)
		return
	var blood: bool = _target != null and _target.kind == &"sangre"
	var mark: Dictionary = tracks.freshest_near(lead.global_position, 7.0, blood)
	if mark.is_empty():
		mark = tracks.freshest_near(lead.global_position, 7.0)
	if mark.is_empty():
		if _target != null and lead.global_position.distance_to(_target.position) > 3.0:
			lead.go_to(_target.position, Dog.Gait.TROT)
		else:
			_enter(Mode.INVESTIGAR, _target)
		return
	var ahead: Dictionary = _fresher_ahead(tracks, mark, blood)
	lead.go_to(ahead["position"], Dog.Gait.TROT if blood else Dog.Gait.WALK)
	lead.sniffing = true
	lead.look_point = Vector3.INF
	_follow(lead, Dog.Gait.TROT if blood else Dog.Gait.WALK, 2.5)


func _probe() -> void:
	if _target == null:
		return
	var prey: Vector3 = _target.position
	var lead: Dog = leader()
	var approach: Vector3 = _from_pack_to(prey)
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		# Se abren en abanico, a unos 30 m.
		var spread: float = deg_to_rad((index - (dogs.size() - 1) * 0.5) * 18.0)
		var spot: Vector3 = prey - approach.rotated(Vector3.UP, spread) * PROBE_DISTANCE
		if dog.global_position.distance_to(prey) > PROBE_DISTANCE + 2.0:
			dog.go_to(spot, Dog.Gait.STALK if dog == lead else Dog.Gait.WALK)
		else:
			dog.stop(&"vigilar" if index % 2 == 0 else &"grunir")
			dog.face(prey)
		dog.look_point = prey + Vector3.UP
		dog.sniffing = false


func _surround() -> void:
	if _target == null:
		return
	_ring = maxf(RING_END, _ring - RING_CLOSE_SPEED * THINK_SECONDS)
	var prey: Vector3 = _target.position
	var front: Vector3 = _from_pack_to(prey)
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		# La Vieja delante; los demás a los lados y detrás, cortando la huida.
		var angle: float = (
			0.0 if index == 0 else PI * (0.35 + 0.65 * float(index) / (dogs.size() - 1))
		)
		if index % 2 == 0:
			angle = -angle
		var spot: Vector3 = prey - front.rotated(Vector3.UP, angle) * _ring
		var far: bool = dog.global_position.distance_to(spot) > 4.0
		if dog.global_position.distance_to(spot) > 1.2:
			dog.go_to(spot, Dog.Gait.TROT if far else Dog.Gait.STALK)
		else:
			dog.stop(&"grunir")
			dog.face(prey)
		dog.look_point = prey + Vector3.UP
		dog.sniffing = false


func _chase() -> void:
	if _target == null:
		return
	var prey: Vector3 = _target.position
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		# Cada uno un poco por su lado, para cerrarle el paso.
		var side: Vector3 = Vector3(sin(index * 2.1), 0.0, cos(index * 2.1)) * minf(3.0, index)
		dog.go_to(prey + side, Dog.Gait.GALLOP)
		dog.look_point = prey + Vector3.UP
		dog.sniffing = false
		_try_bite(dog)


func _attack() -> void:
	if _target == null:
		return
	var prey: Vector3 = _target.position
	# De uno en uno: el que ha mordido vuelve al corro y, pasado un rato, salta otro.
	if _attacker < 0 or (_bitten and _bite_clock <= 0.0):
		_attacker = _next_attacker(prey)
		_bitten = false
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		dog.look_point = prey + Vector3.UP
		dog.sniffing = false
		if index == _attacker and not _bitten:
			if dog.pose != &"morder":
				dog.go_to(prey, Dog.Gait.GALLOP)
				_try_bite(dog)
			continue
		var angle: float = TAU * index / dogs.size()
		var spot: Vector3 = prey + Vector3(cos(angle), 0.0, sin(angle)) * RING_END
		if dog.global_position.distance_to(spot) > 1.5:
			dog.go_to(spot, Dog.Gait.TROT)
		else:
			dog.stop(&"grunir")
			dog.face(prey)


func _eat() -> void:
	if _bait == null or not is_instance_valid(_bait):
		return
	var food: Vector3 = (_bait.get_parent() as Node3D).global_position
	_eaten += THINK_SECONDS
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		var spot: Vector3 = food if index == 0 else food + ring_offset(index, 2.2)
		if dog.global_position.distance_to(spot) > (1.0 if index == 0 else 1.6):
			dog.go_to(spot, Dog.Gait.TROT)
		else:
			dog.stop(&"comer" if index == 0 else &"grunir")
			dog.face(food)
		dog.look_point = food
		dog.sniffing = false


func _retreat() -> void:
	var spot: Vector3 = _target.position if _target != null else leader().global_position
	for index: int in dogs.size():
		var dog: Dog = dogs[index]
		if _mode_time < 6.0:
			dog.stop(&"olfatear" if index % 2 == 0 else &"grunir")
			dog.face(spot)
			dog.sniffing = true
		else:
			dog.sniffing = false
			_follow(leader(), Dog.Gait.WALK, 3.0)
			leader().go_to(_route()[_nearest_route_point(_route())], Dog.Gait.WALK)


# -- Morder ----------------------------------------------------------------------


func _try_bite(dog: Dog) -> void:
	if _bite_clock > 0.0 or _target == null:
		return
	var victim: Player = _victim_near(dog)
	if victim == null:
		return
	dog.stop(&"morder")
	dog.face(victim.global_position)
	_bite_clock = BITE_COOLDOWN
	_bitten = true
	memory.decide(&"morder", _target, Stimuli.clock())
	get_tree().create_timer(BITE_DELAY).timeout.connect(_close_jaws.bind(dog, victim))


func _close_jaws(dog: Dog, victim: Player) -> void:
	if not is_instance_valid(dog) or not is_instance_valid(victim) or victim.condition.dead:
		return
	if dog.global_position.distance_to(victim.global_position) > BITE_REACH + 0.4:
		return
	if victim.global_position.y - dog.global_position.y > REACH_HEIGHT:
		return
	var wounds: Wounds = Wounds.find(get_tree())
	if wounds != null:
		wounds.bite(victim, dog.global_position)
	# Se aparta antes del siguiente.
	var away: Vector3 = dog.global_position - victim.global_position
	away.y = 0.0
	dog.go_to(dog.global_position + away.normalized() * BITE_RETREAT, Dog.Gait.TROT)
	dog.set_pose(&"quieto")


func _victim_near(dog: Dog) -> Player:
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		var player: Player = node as Player
		if player.condition.dead:
			continue
		if player.global_position.distance_to(dog.global_position) <= BITE_REACH:
			if player.global_position.y - dog.global_position.y <= REACH_HEIGHT:
				return player
	return null


func _next_attacker(prey: Vector3) -> int:
	var best: int = 0
	var best_distance: float = INF
	for index: int in dogs.size():
		if index == _attacker:
			continue
		var distance: float = dogs[index].global_position.distance_to(prey)
		if distance < best_distance:
			best_distance = distance
			best = index
	return best


# -- Lo que perciben -------------------------------------------------------------


## Un perro ha percibido algo: la manada lo sabe (y si es una presa que no
## esperaba, ladra y se lo cuenta a los que lo oyen).
func _on_perceived(percept: Percept, dog: Dog) -> void:
	memory.remember(percept.copy())
	if percept.sense == Percept.SIGHT and percept.kind == &"presa" and mode < Mode.TANTEO:
		_bark(percept, dog)


func _bark(percept: Percept, dog: Dog = null) -> void:
	if percept == null:
		return
	var who: Dog = dog if dog != null else leader()
	var stimuli: Stimuli = Stimuli.find(get_tree())
	if stimuli != null:
		stimuli.make_noise(who.global_position + Vector3.UP, BARK_RADIUS, BARK, 0, true, who)
	for other: Dog in dogs:
		if other == who:
			continue
		if other.global_position.distance_to(who.global_position) <= BARK_RADIUS:
			var told: Percept = other.perception.tell(percept, 0.75)
			memory.remember(told.copy())


## Lo más seguro que sabe la manada de una presa (vista, olida o sangre).
func _best_prey() -> Percept:
	var found: Percept = null
	for key: String in memory.facts:
		var fact: Percept = memory.facts[key]
		if not PREY_KINDS.has(fact.kind) or fact.certainty < PREY_CERTAINTY:
			continue
		if found == null or fact.certainty > found.certainty:
			found = fact
	return found


## Una pista: un ruido, algo que se movió, un rastro, o una presa de la que no se
## está seguro.
func _best_clue() -> Percept:
	var found: Percept = null
	for key: String in memory.facts:
		var fact: Percept = memory.facts[key]
		if fact.certainty < CLUE_CERTAINTY or IGNORED_KINDS.has(fact.kind):
			continue
		if PREY_KINDS.has(fact.kind) and fact.certainty >= PREY_CERTAINTY:
			continue
		if found == null or fact.certainty > found.certainty:
			found = fact
	return found


func _forget_prey(prey: Percept) -> void:
	for key: String in memory.facts.keys():
		if (memory.facts[key] as Percept).position.distance_to(prey.position) < 12.0:
			memory.facts.erase(key)
	for dog: Dog in dogs:
		for key: String in dog.perception.knowledge.facts.keys():
			var fact: Percept = dog.perception.knowledge.facts[key]
			if fact.position.distance_to(prey.position) < 12.0:
				dog.perception.knowledge.facts.erase(key)


## La presa corre: lo vio algún perro hace poco y va deprisa.
func _prey_running(prey: Percept) -> bool:
	if prey.subject == 0 or Stimuli.clock() - prey.time > 1.0:
		return false
	var player: Player = Player.find(get_tree(), prey.subject)
	return player != null and player.move_speed >= RUNNING_PREY


## Se puede llegar a donde está la presa (por el suelo, sin subir más de un metro).
func _reachable(prey: Percept) -> bool:
	var lead: Dog = leader()
	if lead == null:
		return false
	var nav: CityNav = lead.nav
	if nav != null and not nav.is_walkable(CityPlan.to_plan(prey.position)):
		return false
	if prey.subject != 0:
		var player: Player = Player.find(get_tree(), prey.subject)
		if player != null and player.global_position.y - _ground_under(player) > REACH_HEIGHT:
			return false
	return true


func _ground_under(player: Player) -> float:
	# Lo más bajo que pisan los perros cerca: el de cualquiera de ellos.
	var lowest: float = INF
	for dog: Dog in dogs:
		if dog.global_position.distance_to(player.global_position) < 12.0:
			lowest = minf(lowest, dog.global_position.y)
	return player.global_position.y if lowest == INF else lowest


func _visible_bait() -> Carryable:
	var items: WorldItems = get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
	if items == null:
		return null
	for item: Carryable in items.items():
		if item.state.data.tool != BAIT_TOOL or item.is_held():
			continue
		var where: Vector3 = (item.get_parent() as Node3D).global_position
		for dog: Dog in dogs:
			if dog.perception.sleeping:
				continue
			# La comida se huele: con el viento, como a una presa (pero de más lejos).
			var env: SurfaceEnv = SurfaceEnv.find(get_tree())
			var weather: Weather = env.weather if env != null else null
			var reach: float = Perception.smell_range(weather, dog.global_position - where, 1.6)
			if dog.global_position.distance_to(where) <= reach:
				return item
	return null


func _start_eating(bait: Carryable) -> void:
	var where: Vector3 = (bait.get_parent() as Node3D).global_position
	var smelled: Percept = Percept.create(Percept.SMELL, where, 0.9, &"cebo", Stimuli.clock())
	leader().perception.knowledge.remember(smelled)
	memory.remember(smelled.copy())
	_bait = bait
	_eaten = 0.0
	_enter(Mode.COMER, smelled)


func _finish_bait() -> void:
	if _bait != null and is_instance_valid(_bait):
		var items: WorldItems = get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
		if items != null:
			items.remove_item(_bait)
	_bait = null


# -- Ayudas ----------------------------------------------------------------------


func _route() -> PackedVector3Array:
	return hunt if _hunting_hours() and not hunt.is_empty() else patrol


func _hunting_hours() -> bool:
	var hour: float = GameState.hour()
	return (hour >= 5.0 and hour < 8.0) or (hour >= 16.0 and hour < 19.0)


## Es de noche: la manada duerme en la guarida.
func is_night() -> bool:
	var hour: float = GameState.hour()
	return hour >= 21.0 or hour < 5.0


func _nearest_route_point(route: PackedVector3Array) -> int:
	var lead: Dog = leader()
	var best: int = 0
	var best_distance: float = INF
	for index: int in route.size():
		var distance: float = route[index].distance_to(lead.global_position)
		if distance < best_distance:
			best_distance = distance
			best = index
	return best


## Los demás siguen a [param lead] en grupo suelto, detrás y a los lados.
func _follow(lead: Dog, gait: Dog.Gait, spacing: float) -> void:
	var behind: Vector3 = -lead.forward()
	var side: Vector3 = behind.cross(Vector3.UP)
	for index: int in range(1, dogs.size()):
		var dog: Dog = dogs[index]
		var row: float = ceilf(index / 2.0)
		var lateral: float = (1.0 if index % 2 == 0 else -1.0) * spacing * 0.6
		var spot: Vector3 = lead.global_position + behind * row * spacing + side * lateral
		if dog.global_position.distance_to(spot) > 1.5:
			var far: bool = dog.global_position.distance_to(spot) > 10.0
			dog.go_to(spot, Dog.Gait.TROT if far else gait)
		else:
			dog.stop(&"quieto")
		dog.sniffing = index % 3 == 0
		dog.look_point = Vector3.INF


## Hacia dónde va la manada para llegar a [param point] (de la Vieja a él, horizontal).
func _from_pack_to(point: Vector3) -> Vector3:
	var lead: Dog = leader()
	var direction: Vector3 = point - lead.global_position
	direction.y = 0.0
	if direction.length() < 0.5:
		return Vector3.FORWARD
	return direction.normalized()


func _nearest_to(point: Vector3) -> float:
	var best: float = INF
	for dog: Dog in dogs:
		best = minf(best, dog.global_position.distance_to(point))
	return best


func _close_to_pack(point: Vector3, distance: float) -> bool:
	return _nearest_to(point) <= distance


func _fresher_ahead(tracks: Tracks, mark: Dictionary, blood: bool) -> Dictionary:
	# La marca más fresca un poco más allá de la que se huele: hacia ahí va el rastro.
	var ahead: Dictionary = tracks.freshest_near(mark["position"], 6.0, blood)
	return ahead if not ahead.is_empty() else mark


## Un sitio alrededor de un punto para el perro [param index] (en corro).
static func ring_offset(index: int, radius: float) -> Vector3:
	var angle: float = TAU * index / 6.0 + 0.4
	return Vector3(cos(angle), 0.0, sin(angle)) * radius
