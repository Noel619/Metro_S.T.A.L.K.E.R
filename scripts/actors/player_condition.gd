class_name PlayerCondition
extends Node
## Cómo está un jugador (F3-12): si sangra y si ha muerto. Lo decide el anfitrión y
## lo cuenta a todos ([method set_condition]); la IA lo lee (la sangre se huele de
## más lejos y deja rastro) y quien ha muerto ya no cuenta.

## Ha caído de alto (lo avisa [Footsteps] en todos los equipos).
signal fell(height: float)

## Sangra (una herida sin vendar): deja rastro y se huele más.
var bleeding: bool = false
## Ha muerto: ya no cuenta para nada.
var dead: bool = false

## El anfitrión cuenta a todos cómo está este jugador.
@rpc("any_peer", "call_local", "reliable")
func set_condition(is_bleeding: bool, is_dead: bool) -> void:
	var sender: int = multiplayer.get_remote_sender_id()
	if sender != 0 and sender != Carryable.HOST_PEER:
		return
	bleeding = is_bleeding
	dead = is_dead
