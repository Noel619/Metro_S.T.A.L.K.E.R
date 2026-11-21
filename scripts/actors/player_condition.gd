class_name PlayerCondition
extends Node
## Cómo está un jugador (F3-12, docs/SUPERFICIE.md 8): la sangre que le queda, sus
## heridas, si sangra y si ha muerto. Lo decide el anfitrión ([Wounds]) y lo cuenta a
## todos ([method set_state]); la IA lo lee (la sangre se huele de más lejos y deja
## rastro) y quien ha muerto ya no cuenta. En el equipo del herido, además, se nota:
## [signal hurt] (el golpe, el susto).

## Ha caído de alto (lo avisa [Footsteps] en todos los equipos).
signal fell(height: float)
## Le han hecho daño desde [param from] (en el equipo del herido).
signal hurt(from: Vector3)
## Ha cambiado (en todos los equipos).
signal changed

## La sangre que le queda: 1 entera; sin sangre, muere.
var blood: float = 1.0
## Sangra (una herida sin vendar): deja rastro y se huele más.
var bleeding: bool = false
## Ha muerto: ya no cuenta para nada.
var dead: bool = false
## Las heridas (en el anfitrión): {clase, sangrado por segundo}.
var wounds: Array[Dictionary] = []

## El anfitrión cuenta a todos cómo está este jugador.
@rpc("any_peer", "call_local", "reliable")
func set_state(new_blood: float, is_bleeding: bool, is_dead: bool) -> void:
	var sender: int = multiplayer.get_remote_sender_id()
	if sender != 0 and sender != Carryable.HOST_PEER:
		return
	blood = new_blood
	bleeding = is_bleeding
	dead = is_dead
	changed.emit()


## El anfitrión avisa al herido del golpe (para que lo note: la vista, el susto).
@rpc("any_peer", "call_local", "reliable")
func notify_hurt(from: Vector3) -> void:
	var sender: int = multiplayer.get_remote_sender_id()
	if sender != 0 and sender != Carryable.HOST_PEER:
		return
	hurt.emit(from)


## Cómo está, para llevarlo de una escena a otra.
func save_state() -> Dictionary:
	return {"sangre": blood, "heridas": wounds.duplicate(true)}


func load_state(data: Dictionary) -> void:
	blood = clampf(float(data.get("sangre", 1.0)), 0.0, 1.0)
	wounds.clear()
	for wound: Variant in data.get("heridas", []):
		if wound is Dictionary:
			wounds.append(wound)
	bleeding = not wounds.is_empty()
