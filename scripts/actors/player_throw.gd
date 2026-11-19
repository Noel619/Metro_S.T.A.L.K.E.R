class_name PlayerThrow
extends RefCounted
## Lanzar lo que se lleva (F3-07, docs/SUPERFICIE.md 4.4): con algo en la mano y nada
## que trabajar delante, mantener el botón izquierdo carga el brazo (lo que se lleva
## se echa atrás) y soltarlo lo lanza; cuanto más se carga, más lejos. Un toque no
## lanza nada. Lo que pesa demasiado no se lanza. Lo decide el anfitrión
## ([method Carryable.request_throw]).

const CHARGE_SECONDS: float = 0.9
## Por debajo de esto no se lanza (era un toque).
const MIN_CHARGE: float = 0.25
## La velocidad con la que sale, con poca carga y con toda.
const SPEED_MIN: float = 3.5
const SPEED_MAX: float = 12.0
## Lo que sube la trayectoria sobre la mirada.
const LOFT: float = 0.18

## De 0 a 1: lo cargado ahora.
var charge: float = 0.0

var _charging: bool = false


## Cada fotograma, en el equipo de quien lanza: [param pressing] es el botón izquierdo.
func update(player: Player, delta: float, pressing: bool) -> void:
	var held: Carryable = player.held_item()
	var can: bool = (
		held != null
		and player.work_target() == null
		and not player.inspecting
		and held.state.data.weight <= Carryable.THROW_MAX_WEIGHT
	)
	if pressing and can:
		_charging = true
		charge = minf(1.0, charge + delta / CHARGE_SECONDS)
	elif _charging:
		if not pressing and can and charge >= MIN_CHARGE:
			throw(player, charge)
		_charging = false
		charge = 0.0
	player.throw_charge = charge


## Lanza lo que lleva [param player] con [param amount] de carga (de 0 a 1).
static func throw(player: Player, amount: float) -> void:
	var held: Carryable = player.held_item()
	if held == null:
		return
	var share: float = clampf((amount - MIN_CHARGE) / (1.0 - MIN_CHARGE), 0.0, 1.0)
	var speed: float = lerpf(SPEED_MIN, SPEED_MAX, share)
	var direction: Vector3 = (player.look_direction() + Vector3.UP * LOFT).normalized()
	var velocity: Vector3 = (
		direction * speed + Vector3(player.velocity.x, 0.0, player.velocity.z) * 0.5
	)
	held.request_throw.rpc_id(Carryable.HOST_PEER, velocity)
