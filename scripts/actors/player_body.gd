class_name PlayerBody
extends RefCounted
## El cuerpo del jugador (F3-01): agacharse, asomarse y correr con aliento. Solo
## cuentas, sin escena: el jugador le dice qué quiere hacer y lo que pesa lo que
## lleva, y le pregunta a qué velocidad andar y a qué altura van los ojos. Los
## pasos los cuenta [Footsteps].
##
## En el depósito no se corre ni se gasta aliento ([member can_run] a false);
## agacharse y asomarse valen en todas partes.

enum Gait { STILL, CROUCH, WALK, RUN }

const CROUCH_SPEED: float = 1.0
const WALK_SPEED: float = 2.3
const RUN_SPEED: float = 4.8
## Por encima de esta velocidad (m/s) se va corriendo; por debajo de la otra, quieto.
const RUN_THRESHOLD: float = 3.4
const STILL_THRESHOLD: float = 0.25
## Agachado si [member crouch] pasa de esto.
const CROUCHED: float = 0.5
## Segundos para agacharse o levantarse del todo.
const CROUCH_TIME: float = 0.28
## Los ojos agachado, como parte de la altura de pie.
const CROUCH_EYES: float = 0.6
## El cuerpo (la cápsula) de pie y agachado.
const STAND_HEIGHT: float = 1.7
const CROUCH_HEIGHT: float = 1.1
## Aliento por segundo: lo que gasta correr (sin carga) y lo que se recupera.
const RUN_DRAIN: float = 1.0 / 8.0
const WALK_GAIN: float = 1.0 / 12.0
const REST_GAIN: float = 1.0 / 7.0
## Sin aliento no se vuelve a correr hasta tener este.
const RECOVERED: float = 0.3
## Por debajo de esto se jadea.
const PANTING: float = 0.25
## Cada kilo que se lleva gasta el aliento corriendo un 2 % más rápido.
const DRAIN_PER_KG: float = 0.02
## Lo que mide cada zancada (un paso: un pie) según el paso.
const STRIDES: Dictionary = {Gait.CROUCH: 0.5, Gait.WALK: 0.75, Gait.RUN: 1.45}
## Asomarse: lo que se aparta la cabeza, lo que se inclina la vista y lo rápido.
const LEAN_DISTANCE: float = 0.35
const LEAN_ROLL: float = 0.14
const LEAN_SPEED: float = 6.0

## Se puede correr (en la superficie). En el depósito, no.
var can_run: bool = false
## De 0 (de pie) a 1 (agachado).
var crouch: float = 0.0
## Lo que quiere el jugador: agacharse (o levantarse, si no hay techo encima).
var crouch_wanted: bool = false
## Arrodillado por otra cosa (abriendo la mochila): agachado sin tocar lo que quiere.
var forced_crouch: bool = false
## De -1 (asomado a la izquierda) a 1 (a la derecha).
var lean: float = 0.0
## De 0 (sin aliento) a 1.
var breath: float = 1.0
## Se ha quedado sin aliento y aún no se ha recuperado.
var exhausted: bool = false
## Va corriendo ahora.
var running: bool = false


## Avanza [param delta] segundos. [param wants_run]: pulsa correr y anda hacia
## delante; [param moving]: se está moviendo; [param load_kg]: lo que lleva
## encima; [param lean_input]: de -1 a 1; [param can_stand]: hay sitio sobre la
## cabeza para levantarse.
func update(
	delta: float,
	wants_run: bool,
	moving: bool,
	load_kg: float,
	lean_input: float,
	can_stand: bool = true
) -> void:
	var wants_crouch: bool = crouch_wanted or forced_crouch or (crouch > 0.0 and not can_stand)
	crouch = move_toward(crouch, 1.0 if wants_crouch else 0.0, delta / CROUCH_TIME)
	var leaning: float = clampf(lean_input, -1.0, 1.0)
	lean = move_toward(lean, leaning, delta * LEAN_SPEED)
	if exhausted and breath >= RECOVERED:
		exhausted = false
	running = can_run and wants_run and moving and not exhausted and crouch < CROUCHED
	if running:
		breath -= delta * RUN_DRAIN * (1.0 + maxf(load_kg, 0.0) * DRAIN_PER_KG)
		if breath <= 0.0:
			breath = 0.0
			exhausted = true
			running = false
	elif can_run:
		breath += delta * (WALK_GAIN if moving else REST_GAIN)
	breath = clampf(breath, 0.0, 1.0)
	if not can_run:
		breath = 1.0
		exhausted = false


## La velocidad a la que quiere andar ahora, antes de lo que frena la carga.
func target_speed() -> float:
	if running:
		return RUN_SPEED
	return lerpf(WALK_SPEED, CROUCH_SPEED, crouch)


## Los ojos ahora, como parte de los de pie.
func eye_share() -> float:
	return lerpf(1.0, CROUCH_EYES, crouch)


## Lo alto del cuerpo ahora (la cápsula).
func body_height() -> float:
	return lerpf(STAND_HEIGHT, CROUCH_HEIGHT, crouch)


## Está agachado.
func is_crouched() -> bool:
	return crouch >= CROUCHED


## Jadea (sin aliento): se ve en el vaho y se oye.
func is_panting() -> bool:
	return can_run and (exhausted or breath < PANTING)


## El paso que corresponde a ir a [param speed] m/s con [param crouch_amount] de
## agachado. Lo usa cualquiera, también el anfitrión con un jugador de otro equipo.
static func gait_for(speed: float, crouch_amount: float) -> Gait:
	if speed < STILL_THRESHOLD:
		return Gait.STILL
	if crouch_amount >= CROUCHED:
		return Gait.CROUCH
	if speed >= RUN_THRESHOLD:
		return Gait.RUN
	return Gait.WALK
