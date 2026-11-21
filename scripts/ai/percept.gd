class_name Percept
extends RefCounted
## Algo que un agente ha percibido (F3-09): por qué sentido, dónde, cuándo y con
## cuánta certeza. Es lo único de lo que puede salir una decisión que tenga que ver
## con dónde estás ([Knowledge], la prueba de justicia).

const SIGHT: StringName = &"vista"
const HEARING: StringName = &"oido"
const SMELL: StringName = &"olfato"
## Lo que le cuenta otro de su especie (un ladrido): sale de lo que percibió ese otro.
const TOLD: StringName = &"aviso"

static var _next_id: int = 1

## Número único: las decisiones lo citan.
var id: int = 0
var sense: StringName = &""
## De quién es (el peer del jugador) si el sentido lo distingue; 0 si no se sabe.
## Para la prueba de justicia se guarda siempre quién fue de verdad ([member truth]).
var subject: int = 0
## Quién lo provocó de verdad (para las pruebas; la IA no lo lee).
var truth: int = 0
## Dónde cree que está (con el error del sentido).
var position: Vector3 = Vector3.ZERO
var time: float = 0.0
## De 0 a 1.
var certainty: float = 0.0
## Qué es: "presa", "paso", "ruido", "rastro", "sangre", "cebo", "ladrido"…
var kind: StringName = &""
## El estímulo del que sale (el número de un ruido, de una huella…), si lo hay.
var stimulus: int = 0
## De qué otra percepción sale (un aviso: la del que avisó).
var source: Percept


static func create(
	sense_name: StringName, where: Vector3, how_sure: float, what: StringName, when: float
) -> Percept:
	var percept: Percept = Percept.new()
	percept.id = _next_id
	_next_id += 1
	percept.sense = sense_name
	percept.position = where
	percept.certainty = clampf(how_sure, 0.0, 1.0)
	percept.kind = what
	percept.time = when
	return percept


## Una copia con el mismo número (para otra memoria: la de la manada). La certeza de
## cada memoria se olvida por su cuenta.
func copy() -> Percept:
	var twin: Percept = Percept.new()
	twin.id = id
	twin.sense = sense
	twin.subject = subject
	twin.truth = truth
	twin.position = position
	twin.time = time
	twin.certainty = certainty
	twin.kind = kind
	twin.stimulus = stimulus
	twin.source = source
	return twin


## La percepción original de la que sale esta (siguiendo los avisos hacia atrás).
func origin() -> Percept:
	var current: Percept = self
	while current.source != null:
		current = current.source
	return current
