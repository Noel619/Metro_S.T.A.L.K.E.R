extends Node
## Estado de la partida en curso: lo que se guarda y lo que comparte la red.
##
## Solo el anfitrión modifica este estado. Los invitados lo recibirán replicado
## cuando exista la economía (Fase 2).

const STARTING_RUBLES: int = 150
const SAVE_KEY: String = "game_state"

var player_name: String = ""
var day: int = 1
var rubles: int = STARTING_RUBLES
var debt: int = 0
var flags: Dictionary = {}


func _ready() -> void:
	SaveSystem.register_provider(SAVE_KEY, self)


## Deja el estado como al firmar la escritura del depósito.
func reset_for_new_game(new_player_name: String) -> void:
	player_name = new_player_name.strip_edges()
	day = 1
	rubles = STARTING_RUBLES
	debt = 0
	flags.clear()


func add_rubles(amount: int) -> void:
	if amount == 0:
		return
	rubles += amount
	EventBus.rubles_changed.emit(rubles, amount)


## Intenta gastar [param amount] rublos. Devuelve [code]false[/code] si no alcanza.
func try_spend(amount: int) -> bool:
	if amount < 0 or amount > rubles:
		return false
	add_rubles(-amount)
	return true


func save_state() -> Dictionary:
	return {
		"player_name": player_name,
		"day": day,
		"rubles": rubles,
		"debt": debt,
		"flags": flags.duplicate(true),
	}


func load_state(data: Dictionary) -> void:
	player_name = str(data.get("player_name", ""))
	day = int(data.get("day", 1))
	rubles = int(data.get("rubles", STARTING_RUBLES))
	debt = int(data.get("debt", 0))
	var loaded_flags: Variant = data.get("flags", {})
	flags = (loaded_flags as Dictionary).duplicate(true) if loaded_flags is Dictionary else {}
