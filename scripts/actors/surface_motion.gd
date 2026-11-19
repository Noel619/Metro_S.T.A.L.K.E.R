class_name SurfaceMotion
extends RefCounted
## Cómo se mueve el jugador en la superficie (F3-01): agacharse, correr mientras
## hay aliento, asomarse y el ruido de los pasos (README 6.4 y 6.8). En el
## depósito no se usa: allí se anda tranquilo y sin estamina.
##
## El ruido de cada paso depende de cómo se anda (agachado, andando, corriendo),
## de lo que se lleva encima (la carga y lo que va suelto en la mochila y suena)
## y del suelo. Es lo que oirán las criaturas y los saqueadores (F3-09):
## [signal EventBus.noise_made].

enum Gait { STILL, CROUCH, WALK, RUN }

## Velocidades (m/s): andar es [constant Player.WALK_SPEED].
const CROUCH_SPEED: float = 1.1
const RUN_SPEED: float = 4.4
## Agachado, los ojos bajan a esta parte de su altura, y el cuerpo a esta otra.
const CROUCH_EYES: float = 0.6
const CROUCH_BODY: float = 0.65
## Aliento (de 0 a 1): lo que gasta correr cada segundo y lo que se suma por cada
## 10 kg que se llevan; lo que se recupera andando y quieto. Sin aliento se deja
## de correr, y no se vuelve a poder hasta recuperar [constant RECOVERED].
const RUN_DRAIN: float = 0.1
const LOAD_DRAIN: float = 0.03
const RECOVER_WALKING: float = 0.06
const RECOVER_STILL: float = 0.15
const RECOVERED: float = 0.35
## Por debajo de esto se le nota: la vista sube y baja con la respiración.
const HEAVING: float = 0.4
## Lo que suena cada paso y cuántos se dan por segundo, según el paso.
const STEP_NOISE: Dictionary = {Gait.CROUCH: 0.12, Gait.WALK: 0.35, Gait.RUN: 0.85}
const STEPS_PER_SECOND: Dictionary = {Gait.CROUCH: 1.3, Gait.WALK: 1.9, Gait.RUN: 2.8}
## Lo que la carga y lo suelto suben el ruido de un paso.
const NOISE_PER_10_KG: float = 0.1
const RATTLE_NOISE: float = 0.08
## Cómo suena cada suelo (1 es lo normal). Lo dice la meta [constant GROUND_META]
## de lo que se pisa: el suelo, o una [Area3D] encima de él (unos cristales rotos
## en la nieve) en la capa de los detectores.
const GROUND_META: StringName = &"suelo"
const GROUNDS: Dictionary = {
	&"nieve": 0.7,
	&"hormigon": 1.0,
	&"nieve_helada": 1.3,
	&"escombros": 1.4,
	&"metal": 1.5,
	&"cristales": 1.9,
}
## A cuántos metros llega un ruido de 1. Solo para verlo (el patio de pruebas
## dibuja cada paso como un círculo de este tamaño); quien lo oye y desde dónde
## lo decidirán las criaturas (F3-09).
const METERS_PER_LOUDNESS: float = 12.0
## Por debajo de esta velocidad se está quieto.
const STILL_SPEED: float = 0.3
## Asomarse: lo que se aparta la cabeza, lo que se inclina y lo rápido que va.
const LEAN_DISTANCE: float = 0.38
const LEAN_ROLL: float = deg_to_rad(9.0)
const LEAN_SPEED: float = 7.0
## Lo que se deja entre la cabeza y una pared al asomarse.
const LEAN_CLEARANCE: float = 0.14

var breath: float = 1.0
## Se ha quedado sin aliento y aún no lo ha recuperado.
var winded: bool = false
var crouching: bool = false
## De -1 (a la izquierda) a 1 (a la derecha).
var lean: float = 0.0
var _step_clock: float = 0.0


## Cómo se anda a [param speed] m/s.
static func gait_of(speed: float, is_crouching: bool, running: bool) -> Gait:
	if speed < STILL_SPEED:
		return Gait.STILL
	if is_crouching:
		return Gait.CROUCH
	return Gait.RUN if running else Gait.WALK


## Lo que suena un paso: según el paso, la carga (kg), lo que va suelto en la
## mochila ([method BackpackGrid.rattle]) y el suelo (1 es lo normal; la nieve
## helada o los cristales, más).
static func step_noise(gait: Gait, load_kg: float, rattle: float, ground: float = 1.0) -> float:
	if gait == Gait.STILL:
		return 0.0
	var noise: float = STEP_NOISE[gait] * ground
	noise += load_kg / 10.0 * NOISE_PER_10_KG
	noise += rattle * RATTLE_NOISE
	return noise


## Lo que suena el suelo [param kind] (de [constant GROUNDS]; si no está, 1).
static func ground_loudness(kind: StringName) -> float:
	return float(GROUNDS.get(kind, 1.0))


## El tipo de suelo de [param node] (su meta [constant GROUND_META]), o vacío.
static func ground_kind(node: Object) -> StringName:
	var tagged: Node = node as Node
	if tagged == null or not tagged.has_meta(GROUND_META):
		return &""
	return StringName(tagged.get_meta(GROUND_META))


## ¿Puede echar a correr?
func can_run() -> bool:
	return not crouching and not winded and breath > 0.0


## Gasta o recupera aliento durante [param delta] segundos.
func update_breath(delta: float, running: bool, moving: bool, load_kg: float) -> void:
	if running:
		breath -= (RUN_DRAIN + load_kg / 10.0 * LOAD_DRAIN) * delta
		if breath <= 0.0:
			breath = 0.0
			winded = true
	else:
		breath += (RECOVER_WALKING if moving else RECOVER_STILL) * delta
		breath = minf(breath, 1.0)
		if winded and breath >= RECOVERED:
			winded = false


## Cuenta los pasos: devuelve true cuando cae uno.
func tick_steps(delta: float, gait: Gait) -> bool:
	if gait == Gait.STILL:
		_step_clock = 0.0
		return false
	_step_clock += delta * float(STEPS_PER_SECOND[gait])
	if _step_clock >= 1.0:
		_step_clock -= 1.0
		return true
	return false


## Lo que sube y baja la vista al respirar fuerte (0 con el aliento lleno).
func heave() -> float:
	return clampf((HEAVING - breath) / HEAVING, 0.0, 1.0)
