extends Node
## Estado de la partida en curso: lo que se guarda y lo que comparte la red.
##
## Solo el anfitrión lo modifica. Los invitados lo reciben entero cada vez que
## cambia ([method push]) y al unirse. La hora corre en todos los equipos a la
## vez y el anfitrión la corrige de vez en cuando.
##
## El impuesto funciona como una cuenta con la administración: cada noche se
## carga el del día ([member debt] sube) y cada pago la rebaja. Pagar de día
## adelanta el de esa noche; una deuda negativa es dinero a cuenta.

## Ha cambiado algo (en el anfitrión, al cambiarlo; en los invitados, al recibirlo).
signal changed

const STARTING_RUBLES: int = 150
const SAVE_KEY: String = "game_state"
## Minutos de juego por segundo real: un día, de las 7 a medianoche, son 34 minutos.
const MINUTES_PER_SECOND: float = 0.5
const WAKE_MINUTE: float = 7.0 * 60.0
const DAY_MINUTES: float = 24.0 * 60.0
const TAX_PER_DAY: int = 20
## Con esta deuda, la administración precinta el mostrador.
const SEAL_DEBT: int = 60
## Días seguidos sin comer: tiemblan las manos; se nubla la vista; mueres.
const HUNGRY_SHAKE: int = 1
const HUNGRY_BLUR: int = 3
const HUNGRY_DEATH: int = 5
## Cada cuánto corrige el anfitrión la hora de los invitados.
const CLOCK_SYNC_SECONDS: float = 5.0

var player_name: String = ""
## El protagonista elegido al firmar la escritura: "chico" o "chica".
var protagonist: String = "chico"
var day: int = 1
var rubles: int = STARTING_RUBLES
## Lo que se debe a la administración (negativo: dinero a cuenta).
var debt: int = 0
var flags: Dictionary = {}
## Minuto del día (de 0 a 1440).
var minute: float = WAKE_MINUTE
## Lo comido hoy: 1 es la comida de un día.
var fed_today: float = 0.0
## Días seguidos sin comer lo suficiente.
var hungry_days: int = 0
## Dosis de radiación acumulada (en las unidades del dosímetro).
var dose: float = 0.0
## El libro de cuentas: diccionarios {day, minute, kind, concept, amount}.
var ledger: Array = []
## Los encargos: diccionarios {id, client, item, pay, deadline, hint, state}.
var jobs: Array = []
## La hora corre (en el depósito sí; en los menús, no).
var clock_running: bool = false
## La mochila y el cinturón de cada jugador, por su puesto ("0" el anfitrión): lo que
## guarda [method Backpack.to_dict]. Lo cambia el anfitrión ([PlayerPack]).
var packs: Dictionary = {}

var _push_pending: bool = false
var _clock_sync: float = 0.0


func _ready() -> void:
	SaveSystem.register_provider(SAVE_KEY, self)
	# NetSession es una autocarga posterior: aún no existe.
	_listen_to_net.call_deferred()


func _process(delta: float) -> void:
	if not clock_running:
		return
	minute = minf(minute + delta * MINUTES_PER_SECOND, DAY_MINUTES)
	if multiplayer.is_server() and multiplayer.get_peers().size() > 0:
		_clock_sync += delta
		if _clock_sync >= CLOCK_SYNC_SECONDS:
			_clock_sync = 0.0
			_receive_clock.rpc(minute)


## Deja el estado como al firmar la escritura del depósito.
func reset_for_new_game(new_player_name: String, new_protagonist: String = "chico") -> void:
	player_name = new_player_name.strip_edges()
	protagonist = new_protagonist if new_protagonist == "chica" else "chico"
	day = 1
	rubles = STARTING_RUBLES
	debt = 0
	flags.clear()
	minute = WAKE_MINUTE
	# El reloj echa a andar cuando se entra en el local (DepotLevel).
	clock_running = false
	fed_today = 0.0
	hungry_days = 0
	dose = 0.0
	ledger.clear()
	jobs.clear()
	packs.clear()
	push()


## La mochila del jugador del puesto [param slot] (una copia: para cambiarla, [method set_pack]).
func pack(slot: int) -> Backpack:
	return Backpack.from_dict(packs.get(str(slot), {}))


## Cambia la mochila del puesto [param slot]. Solo el anfitrión: la manda a todos.
func set_pack(slot: int, value: Backpack) -> void:
	if not multiplayer.is_server():
		return
	packs[str(slot)] = value.to_dict()
	push()


func add_rubles(amount: int) -> void:
	if amount == 0:
		return
	rubles += amount
	EventBus.rubles_changed.emit(rubles, amount)
	push()


## Intenta gastar [param amount] rublos. Devuelve [code]false[/code] si no alcanza.
func try_spend(amount: int) -> bool:
	if amount < 0 or amount > rubles:
		return false
	add_rubles(-amount)
	return true


## Apunta un movimiento en el libro de cuentas. [param kind]: "venta", "compra",
## "comida", "impuesto", "encargo" o "deuda"; [param amount], con signo.
func record(kind: String, concept: String, amount: int) -> void:
	ledger.append(
		{"day": day, "minute": int(minute), "kind": kind, "concept": concept, "amount": amount}
	)
	push()


## Lo apuntado un día.
func entries_of(on_day: int) -> Array:
	return ledger.filter(func(entry: Dictionary) -> bool: return int(entry["day"]) == on_day)


## Un pago en la ventanilla de la administración. Devuelve la deuda que queda.
func pay_tax(amount: int) -> int:
	if amount <= 0:
		return debt
	debt -= amount
	record("impuesto", "Pago a la administración", -amount)
	return debt


## ¿Está precintado el mostrador por las deudas?
func is_sealed() -> bool:
	return debt >= SEAL_DEBT


## Come algo que alimenta [param nutrition] (1: un día).
func eat(nutrition: float) -> void:
	fed_today += maxf(nutrition, 0.0)
	push()


func add_dose(amount: float) -> void:
	if amount > 0.0:
		dose += amount


## La hora, como "07:05".
func time_text() -> String:
	var whole: int = int(minute)
	return "%02d:%02d" % [(whole / 60) % 24, whole % 60]


func hour() -> float:
	return minute / 60.0


## Se acaba el día (al dormir): se carga el impuesto, cuenta lo comido y empieza
## el siguiente a las 7. Solo el anfitrión.
func end_day() -> void:
	if not multiplayer.is_server():
		return
	var finished: int = day
	debt += TAX_PER_DAY
	record("deuda", "Impuesto del día %d" % finished, 0)
	hungry_days = 0 if fed_today >= 0.999 else hungry_days + 1
	fed_today = 0.0
	for job: Dictionary in jobs:
		if job.get("state", "abierto") == "abierto" and int(job.get("deadline", 0)) < finished + 1:
			job["state"] = "caducado"
	day += 1
	minute = WAKE_MINUTE
	EventBus.day_ended.emit(finished)
	EventBus.day_started.emit(day)
	push()


## Añade un encargo. Devuelve su id.
func add_job(job: Dictionary) -> int:
	var id: int = 1
	for other: Dictionary in jobs:
		id = maxi(id, int(other["id"]) + 1)
	var stored: Dictionary = job.duplicate(true)
	stored["id"] = id
	stored["state"] = "abierto"
	jobs.append(stored)
	push()
	return id


func job(id: int) -> Dictionary:
	for each: Dictionary in jobs:
		if int(each["id"]) == id:
			return each
	return {}


## Cambia el estado de un encargo ("abierto", "entregado", "caducado").
func set_job_state(id: int, state: String) -> void:
	var found: Dictionary = job(id)
	if not found.is_empty():
		found["state"] = state
		push()


## Manda el estado a los invitados (una vez por fotograma, aunque cambie más).
func push() -> void:
	changed.emit()
	if not multiplayer.is_server() or _push_pending:
		return
	_push_pending = true
	_send_now.call_deferred()


func save_state() -> Dictionary:
	return {
		"player_name": player_name,
		"protagonist": protagonist,
		"day": day,
		"rubles": rubles,
		"debt": debt,
		"flags": flags.duplicate(true),
		"minute": minute,
		"fed_today": fed_today,
		"hungry_days": hungry_days,
		"dose": dose,
		"ledger": ledger.duplicate(true),
		"jobs": jobs.duplicate(true),
		"packs": packs.duplicate(true),
	}


func load_state(data: Dictionary) -> void:
	player_name = str(data.get("player_name", ""))
	protagonist = "chica" if str(data.get("protagonist", "chico")) == "chica" else "chico"
	day = int(data.get("day", 1))
	rubles = int(data.get("rubles", STARTING_RUBLES))
	debt = int(data.get("debt", 0))
	var loaded_flags: Variant = data.get("flags", {})
	flags = (loaded_flags as Dictionary).duplicate(true) if loaded_flags is Dictionary else {}
	minute = float(data.get("minute", WAKE_MINUTE))
	fed_today = float(data.get("fed_today", 0.0))
	hungry_days = int(data.get("hungry_days", 0))
	dose = float(data.get("dose", 0.0))
	ledger = _array(data.get("ledger", []))
	jobs = _array(data.get("jobs", []))
	var loaded_packs: Variant = data.get("packs", {})
	packs = (loaded_packs as Dictionary).duplicate(true) if loaded_packs is Dictionary else {}
	push()


func _send_now() -> void:
	_push_pending = false
	if multiplayer.get_peers().size() > 0:
		_receive.rpc(_snapshot())


func _snapshot() -> Dictionary:
	var data: Dictionary = save_state()
	data["clock_running"] = clock_running
	return data


@rpc("authority", "call_remote", "reliable")
func _receive(data: Dictionary) -> void:
	load_state(data)
	clock_running = bool(data.get("clock_running", false))
	rubles_changed_quietly()


@rpc("authority", "call_remote", "unreliable_ordered")
func _receive_clock(value: float) -> void:
	minute = value


## En los invitados, avisa de que los rublos han cambiado (para la interfaz).
func rubles_changed_quietly() -> void:
	EventBus.rubles_changed.emit(rubles, 0)


func _listen_to_net() -> void:
	NetSession.peer_joined.connect(_on_peer_joined)


func _on_peer_joined(peer_id: int) -> void:
	if multiplayer.is_server():
		_receive.rpc_id(peer_id, _snapshot())


static func _array(value: Variant) -> Array:
	return (value as Array).duplicate(true) if value is Array else []
