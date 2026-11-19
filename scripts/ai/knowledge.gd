class_name Knowledge
extends RefCounted
## La memoria de un agente (F3-09): lo que sabe de cada cosa que ha percibido,
## con cuánta certeza, y las decisiones que ha tomado con ello.
##
## Lo que ve lo reconoce (sabe qué jugador es); lo que oye o huele no: se junta con
## lo que ya sabía si está cerca ("eso que olí será lo que vi") y, si no, es un
## indicio nuevo. La certeza se va perdiendo; lo que no se renueva se olvida.
##
## Prueba de justicia (README 13.4): cada decisión que tiene que ver con dónde está
## alguien guarda la percepción de la que sale; [method is_fair] comprueba que todas
## las decisiones con sitio salen de algo que este agente percibió (o le avisaron).

## Lo que se pierde de certeza por segundo, según el sentido.
const FORGET_PER_SECOND: Dictionary = {
	Percept.SIGHT: 0.05,
	Percept.HEARING: 0.1,
	Percept.SMELL: 0.07,
	Percept.TOLD: 0.08,
}
const FORGET_BELOW: float = 0.05
## Lo que oye o huele a menos de esto de algo que ya sabía, se junta con ello.
const ASSOCIATE_RADIUS: float = 10.0
## Lo que se guarda (las percepciones y las decisiones más recientes).
const KEEP: int = 400
## Lo que es alguien concreto (una presa): lo que se percibe cerca sigue siéndolo.
const TARGET_KINDS: Array[StringName] = [&"presa", &"sangre"]

## Lo que sabe de cada cosa: clave -> la percepción más reciente que la sostiene.
var facts: Dictionary = {}
## Las decisiones tomadas: {time, what, percept (id o 0), position}.
var decisions: Array[Dictionary] = []
## Las percepciones que ha tenido, por número (para la prueba de justicia).
var perceived: Dictionary = {}

var _order: Array[int] = []
var _next_clue: int = 1


## Guarda una percepción: la junta con lo que ya sabía o la apunta como nueva.
## Devuelve la clave con la que la guarda.
func remember(percept: Percept) -> String:
	_keep(percept)
	var key: String = ""
	if percept.sense == Percept.SIGHT and percept.subject != 0:
		key = "presa_%d" % percept.subject
	else:
		key = _nearest_key(percept.position)
		if key.is_empty():
			key = "indicio_%d" % _next_clue
			_next_clue += 1
	var old: Percept = facts.get(key)
	if old == null or _replaces(old, percept):
		if old != null and percept.sense != Percept.SIGHT:
			# Lo que oye o huele cerca de lo que vio sigue siendo lo que vio.
			if percept.subject == 0 and old.subject != 0:
				percept.subject = old.subject
			if TARGET_KINDS.has(old.kind) and not TARGET_KINDS.has(percept.kind):
				percept.kind = old.kind
		facts[key] = percept
	return key


## Se pierde certeza con el tiempo (en [param delta] segundos).
func forget(delta: float) -> void:
	for key: String in facts.keys():
		var fact: Percept = facts[key]
		fact.certainty -= float(FORGET_PER_SECOND.get(fact.sense, 0.1)) * delta
		if fact.certainty < FORGET_BELOW:
			facts.erase(key)


## Lo más seguro que sabe de [param kinds] (todas las clases si está vacío), o null.
func best(kinds: Array[StringName] = []) -> Percept:
	var found: Percept = null
	for key: String in facts:
		var fact: Percept = facts[key]
		if not kinds.is_empty() and not kinds.has(fact.kind):
			continue
		if found == null or fact.certainty > found.certainty:
			found = fact
	return found


## Lo que sabe con esta clave, o null.
func fact(key: String) -> Percept:
	return facts.get(key)


## Apunta una decisión. Si tiene que ver con un sitio, [param percept] es la
## percepción de la que sale; se comprueba al decidir que la percibió de verdad.
func decide(what: StringName, percept: Percept = null, time: float = 0.0) -> void:
	(
		decisions
		. append(
			{
				"time": time,
				"what": what,
				"percept": percept.id if percept != null else 0,
				"position": percept.position if percept != null else Vector3.INF,
				"fair": percept == null or perceived.has(percept.id),
			}
		)
	)
	if decisions.size() > KEEP:
		decisions.pop_front()


## Todas las decisiones con sitio salen de algo que percibió (o le avisaron).
func is_fair() -> bool:
	for decision: Dictionary in decisions:
		if not bool(decision["fair"]):
			return false
	return true


func _keep(percept: Percept) -> void:
	perceived[percept.id] = percept
	_order.append(percept.id)
	while _order.size() > KEEP:
		perceived.erase(_order.pop_front())


func _replaces(old: Percept, new_percept: Percept) -> bool:
	if new_percept.time > old.time + 0.5:
		return new_percept.certainty >= old.certainty * 0.5
	return new_percept.certainty >= old.certainty


func _nearest_key(position: Vector3) -> String:
	var best_key: String = ""
	var best_distance: float = ASSOCIATE_RADIUS
	for key: String in facts:
		var distance: float = (facts[key] as Percept).position.distance_to(position)
		if distance < best_distance:
			best_distance = distance
			best_key = key
	return best_key
