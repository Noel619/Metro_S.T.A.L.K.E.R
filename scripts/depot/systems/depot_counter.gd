class_name DepotCounter
extends Node3D
## El mostrador (F2-09, F2-10): la caja de los rublos, el libro de cuentas, el
## tablón de los encargos, el reloj y los clientes.
##
## Con la persiana subida, entre las 9 y las 19 y sin precinto, el anfitrión
## hace venir a los clientes de uno en uno. Cada uno anda hasta la ventanilla y
## deja un papelito con lo que quiere (docs/DEPOSITO.md 4.5):
## - Comprar: busca en el mostrador algo de lo suyo. Si la etiqueta le parece
##   bien, deja ese dinero; si no, lo que cree que vale (una vez puede subir).
##   Coger sus billetes es aceptar (entran solos en la caja); quitarle el objeto
##   es no venderlo. Si no encuentra nada, a veces deja un encargo.
## - Vender: deja un objeto con su precio. Un fajo con ese dinero (o casi) al
##   lado es comprárselo.
## - Recoger un encargo: paga lo prometido por lo que encargó.

enum Phase { NONE, COMING, WAITING, OFFERED, LEAVING }

## Lo que tarda en volver a venir alguien (segundos, al azar entre los dos).
const COOLDOWN: Vector2 = Vector2(20.0, 45.0)
## Lo que espera en la ventanilla sin que pase nada, y con una oferta hecha.
const PATIENCE: float = 80.0
const OFFER_PATIENCE: float = 14.0
## Lo que tiene que estar quieto algo en el mostrador para que lo mire.
const SETTLE: float = 1.0
## Lo que acepta de menos al vendernos algo.
const SELL_TOLERANCE: float = 0.85
## Lo contaminado que no compra (si no está embolsado).
const REFUSE_CONTAMINATION: float = 0.25
const OPEN_HOUR: float = 9.0
const CLOSE_HOUR: float = 19.0
## La zona del trato: la parte del mostrador que da a la ventanilla.
const DEAL_SIZE: Vector3 = Vector3(1.3, 0.5, 0.75)
const DEAL_CENTER: Vector3 = Vector3(0.05, DepotRoom.COUNTER_TOP + 0.24, 3.17)
## Dónde deja el cliente sus cosas (su lado del mostrador) y su papelito.
const CUSTOMER_SIDE: Vector3 = Vector3(-0.3, DepotRoom.COUNTER_TOP + 0.03, 3.42)
const SLIP_AT: Vector3 = Vector3(0.42, DepotRoom.COUNTER_TOP + 0.004, 3.3)
## Por dónde pasan por el pasillo, delante del puesto de comida y del contenedor.
const PASSING_Z: float = Station.FRONT + 2.3
## El orden de los primeros días: quién viene y a qué.
const FIRST_VISITS: Array = [[&"relojero", "comprar"]]
const REGULARS: Array[StringName] = [&"vecina", &"chatarrero", &"relojero"]

var room: DepotRoom
var station: Station
var items: WorldItems
var world: DepotWorld
## La persiana (para saber si está abierto).
var shutter: ShutterFixture

var cash_box: CashBoxFixture
var ledger: LedgerFixture
var board: JobBoard
var clock: WallClock
var slip: NoteFixture
var customer: Customer
var phase: Phase = Phase.NONE
## La visita en curso: qué viene a hacer y con qué.
var visit: Dictionary = {}

var _customers: Node3D
var _spawner: MultiplayerSpawner
var _cooldown: float = 3.0
var _timer: float = 0.0
## Lo que lleva quieto en el mostrador cada objeto (por su uid), en segundos.
var _seen: Dictionary = {}
## Qué día vino por última vez cada cliente a recoger su encargo (por id del encargo).
var _job_visits: Dictionary = {}
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _ready() -> void:
	cash_box = CashBoxFixture.new()
	cash_box.fixture_id = "caja_rublos"
	cash_box.name = "CajaRublos"
	cash_box.model = room.fixed("CajaRublos")
	add_child(cash_box)
	ledger = LedgerFixture.new()
	ledger.fixture_id = "libro"
	ledger.name = "Libro"
	ledger.model = room.fixed("Libro")
	add_child(ledger)
	board = JobBoard.new()
	board.name = "Encargos"
	board.position = DepotRoom.JOB_BOARD
	board.rotation_degrees.y = 180.0
	add_child(board)
	clock = WallClock.new()
	clock.name = "Reloj"
	clock.model = room.fixed("Reloj")
	add_child(clock)
	slip = NoteFixture.new()
	slip.fixture_id = "papelito"
	slip.name = "Papelito"
	slip.position = SLIP_AT
	slip.rotation_degrees = Vector3(-90.0, 8.0, 0.0)
	add_child(slip)
	_customers = Node3D.new()
	_customers.name = "Clientes"
	add_child(_customers)
	_spawner = MultiplayerSpawner.new()
	_spawner.name = "Generador"
	_spawner.spawn_function = _build_customer
	_customers.add_child(_spawner)
	_spawner.spawn_path = _spawner.get_path_to(_customers)
	_rng.seed = 1931


## ¿Está abierto el mostrador ahora?
func is_open() -> bool:
	var hour: float = GameState.hour()
	return (
		shutter != null
		and shutter.is_open()
		and hour >= OPEN_HOUR
		and hour < CLOSE_HOUR
		and not GameState.is_sealed()
	)


## Lo que hay ahora en el mostrador, del lado del trato (sin lo que se lleva).
func on_counter() -> Array[Carryable]:
	var found: Array[Carryable] = []
	for item: Carryable in items.items():
		if item.is_held():
			continue
		var local: Vector3 = item.body().global_position - DEAL_CENTER
		if (
			absf(local.x) < DEAL_SIZE.x / 2.0
			and absf(local.y) < DEAL_SIZE.y / 2.0
			and absf(local.z) < DEAL_SIZE.z / 2.0
		):
			found.append(item)
	return found


func _process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	_timer -= delta
	match phase:
		Phase.NONE:
			_cooldown -= delta
			if _cooldown <= 0.0 and is_open():
				start_visit(_next_visit())
		Phase.WAITING:
			_wait(delta)
		Phase.OFFERED:
			_offered()


## Hace venir a alguien (solo el anfitrión): [param next] es [id, a qué viene,
## (encargo)].
func start_visit(next: Array) -> void:
	if next.is_empty() or customer != null:
		return
	var customer_id: StringName = next[0]
	var entry: Vector3 = Station.ENTRY_LEFT if _rng.randf() < 0.5 else Station.ENTRY_RIGHT
	customer = _spawner.spawn({"id": customer_id, "where": entry}) as Customer
	if customer == null:
		return
	visit = {"kind": next[1], "job": next[2] if next.size() > 2 else 0, "from": entry}
	phase = Phase.COMING
	var spot: Vector3 = Station.WINDOW_SPOT + Vector3(_rng.randf_range(-0.2, 0.2), 0.0, 0.0)
	customer.walk([Vector3(entry.x * 0.5, 0.0, PASSING_Z), spot])
	customer.arrived.connect(_on_arrived, CONNECT_ONE_SHOT)
	var visits: Dictionary = GameState.flags.get("visitas", {})
	visits[String(customer_id)] = int(visits.get(String(customer_id), 0)) + 1
	GameState.flags["visitas"] = visits


## Quién viene ahora: primero los encargos que alguien viene a recoger, luego
## los primeros clientes y después los de siempre.
func _next_visit() -> Array:
	for job: Dictionary in GameState.jobs:
		if str(job.get("state", "")) == "abierto" and int(job.get("since", 0)) < GameState.day:
			# Una vez al día como mucho.
			if int(_job_visits.get(int(job["id"]), 0)) != GameState.day:
				_job_visits[int(job["id"])] = GameState.day
				return [StringName(str(job.get("client_id", ""))), "encargo", int(job["id"])]
	var visits: Dictionary = GameState.flags.get("visitas", {})
	for first: Array in FIRST_VISITS:
		if int(visits.get(String(first[0]), 0)) == 0:
			return [first[0], first[1]]
	var who: StringName = REGULARS[_rng.randi() % REGULARS.size()]
	var data: CustomerData = CustomerData.by_id(who)
	var kind: String = "comprar"
	if data != null and not data.sells.is_empty() and _rng.randf() < 0.45:
		kind = "vender"
	return [who, kind]


func _on_arrived() -> void:
	if customer == null:
		return
	customer.face_towards(DepotRoom.DEAL_SPOT)
	var data: CustomerData = customer.data
	phase = Phase.WAITING
	_timer = PATIENCE
	_seen.clear()
	match str(visit.get("kind", "")):
		"vender":
			var item_id: StringName = data.sells[_rng.randi() % data.sells.size()]
			var where: Transform3D = Transform3D(
				Basis.IDENTITY, CUSTOMER_SIDE + Vector3(0.0, 0.05, 0.0)
			)
			var item: Carryable = items.spawn_with(item_id, where, {"de": String(data.id)})
			var ask: int = maxi(1, roundi(_value_of(item_id) * data.sell_factor))
			visit["item"] = item.state.uid if item != null else 0
			visit["ask"] = ask
			_write_slip(data.sell_note % ask if "%d" in data.sell_note else data.sell_note)
		"encargo":
			var job: Dictionary = GameState.job(int(visit.get("job", 0)))
			_write_slip(
				(
					"Vengo a por lo mío:\n%s.\nLo prometido: %d ₽."
					% [str(job.get("want", "")), int(job.get("pay", 0))]
				)
			)
		_:
			_write_slip(data.buy_note)


static func _value_of(item_id: StringName) -> int:
	var data: ItemData = ItemState.load_data(item_id)
	return data.value(1.0, 0.0) if data != null else 1


func _write_slip(text: String) -> void:
	var lines: Array = []
	for line: String in text.split("\n"):
		lines.append(line)
	if customer != null and customer.data != null:
		lines.append("")
		lines.append("— " + customer.data.signature)
	slip.write(PaperCard.note(lines, 0.12))


## Esperando: comprar (mira lo que hay en el mostrador) o vender (mira si hay
## dinero al lado de lo suyo).
func _wait(delta: float) -> void:
	if customer == null:
		phase = Phase.NONE
		return
	var kind: String = str(visit.get("kind", ""))
	if kind == "vender":
		_check_payment()
	else:
		var candidate: Carryable = _candidate(delta)
		if candidate != null:
			_offer(candidate)
			return
	if _timer <= 0.0:
		_give_up()


## Lo primero del mostrador que le interesa y lleva un rato quieto.
func _candidate(delta: float) -> Carryable:
	var still: Dictionary = {}
	for item: Carryable in on_counter():
		if not _interesting(item):
			continue
		var uid: int = item.state.uid
		var waited: float = float(_seen.get(uid, 0.0)) + delta
		still[uid] = waited
		if waited >= SETTLE:
			_seen = still
			return item
	_seen = still
	return null


func _interesting(item: Carryable) -> bool:
	var data: ItemData = item.state.data
	if data.trash or data.tool in [&"billetes", &"etiqueta", &"bolsa"]:
		return false
	if item.state.extra.has("de") or item.state.extra.has("contenido"):
		return false
	if str(visit.get("kind", "")) == "encargo":
		var job: Dictionary = GameState.job(int(visit.get("job", 0)))
		return StringName(str(job.get("item", ""))) == data.id and item.state.condition >= 0.5
	return customer.data.wants(data)


## Lo que ofrece por [param item] (y por qué no, si no lo quiere: 0).
func offer_for(item: Carryable) -> int:
	if item.state.contamination > REFUSE_CONTAMINATION and not item.state.bagged:
		return 0
	if str(visit.get("kind", "")) == "encargo":
		return int(GameState.job(int(visit.get("job", 0))).get("pay", 0))
	var worth: float = item.state.value() * customer.data.buy_factor
	if bool(item.state.extra.get("reparado", false)):
		worth *= 1.15
	if item.state.price >= 0:
		return item.state.price if item.state.price <= worth * 1.05 else maxi(1, roundi(worth))
	return maxi(1, roundi(worth * 0.9))


func _offer(item: Carryable) -> void:
	var amount: int = offer_for(item)
	if amount <= 0:
		customer.face = &"miedo"
		_write_slip("Eso está contaminado.\nAsí no lo quiero.")
		_seen[item.state.uid] = -9999.0
		return
	var where: Transform3D = Transform3D(Basis.from_euler(Vector3(0, 0.3, 0)), CUSTOMER_SIDE)
	var wad: Carryable = items.spawn_with(
		&"billetes", where, {"rublos": amount, "de": String(customer.data.id)}
	)
	visit["item"] = item.state.uid
	visit["wad"] = wad.state.uid if wad != null else 0
	visit["offer"] = amount
	visit["raised"] = false
	customer.face = &"neutro"
	phase = Phase.OFFERED
	_timer = OFFER_PATIENCE


## Con su dinero en el mostrador: coger el dinero es aceptar; quitar el objeto,
## no vender.
func _offered() -> void:
	var item: Carryable = items.find_item(int(visit.get("item", 0)))
	var wad: Carryable = items.find_item(int(visit.get("wad", 0)))
	if wad == null:
		_back_to_waiting(item)
		return
	if wad.is_held():
		_accept(item, wad)
		return
	if item == null or not on_counter().has(item):
		items.remove_item(wad)
		customer.face = &"cansado"
		_back_to_waiting(null)
		return
	if _timer > 0.0:
		return
	# Una vez puede subir: a medio camino de lo que pide la etiqueta.
	var offer: int = int(visit.get("offer", 0))
	if not bool(visit.get("raised", false)) and item.state.price > offer:
		var raised: int = roundi((offer + item.state.price) / 2.0)
		var extra: Dictionary = wad.state.extra.duplicate()
		extra["rublos"] = raised
		wad.set_values({"extra": extra})
		visit["offer"] = raised
		visit["raised"] = true
		customer.face = &"esfuerzo"
		_timer = OFFER_PATIENCE
		return
	items.remove_item(wad)
	_leave(&"cansado")


func _back_to_waiting(_item: Carryable) -> void:
	visit.erase("wad")
	phase = Phase.WAITING
	_timer = minf(_timer + 10.0, PATIENCE)


## Trato hecho: sus billetes entran en la caja y se lleva lo suyo.
func _accept(item: Carryable, wad: Carryable) -> void:
	var amount: int = int(wad.state.extra.get("rublos", 0))
	var concept: String = item.state.data.display_name if item != null else "Venta"
	items.remove_item(wad)
	if item != null:
		items.remove_item(item)
	GameState.add_rubles(amount)
	if str(visit.get("kind", "")) == "encargo":
		var job_id: int = int(visit.get("job", 0))
		GameState.set_job_state(job_id, "entregado")
		GameState.record("encargo", "%s (%s)" % [concept, customer.data.signature], amount)
	else:
		GameState.record("venta", "%s a %s" % [concept, customer.data.signature], amount)
	_write_slip("Gracias.")
	_leave(&"sonrisa")


## Nos vende algo: mira si hay dinero en el mostrador junto a lo suyo.
func _check_payment() -> void:
	var item: Carryable = items.find_item(int(visit.get("item", 0)))
	if item == null:
		_leave(&"neutro")
		return
	var ask: int = int(visit.get("ask", 0))
	var wads: Array[Carryable] = []
	var paid: int = 0
	for other: Carryable in on_counter():
		if other.state.data.tool == &"billetes" and not other.state.extra.has("de"):
			wads.append(other)
			paid += int(other.state.extra.get("rublos", 0))
	if wads.is_empty():
		return
	if paid < roundi(ask * SELL_TOLERANCE):
		customer.face = &"cansado"
		return
	for wad: Carryable in wads:
		items.remove_item(wad)
	# Si sobra, deja la vuelta; lo suyo pasa a ser nuestro.
	if paid > ask:
		var change: Transform3D = Transform3D(Basis.IDENTITY, CUSTOMER_SIDE)
		items.spawn_with(&"billetes", change, {"rublos": paid - ask})
	var extra: Dictionary = item.state.extra.duplicate()
	extra.erase("de")
	item.set_values({"extra": extra})
	var price: int = mini(paid, ask)
	GameState.record(
		"compra", "%s de %s" % [item.state.data.display_name, customer.data.signature], -price
	)
	_write_slip("Trato hecho.")
	_leave(&"sonrisa")


## No ha encontrado lo que buscaba: si tiene un encargo, lo deja en el tablón.
func _give_up() -> void:
	var data: CustomerData = customer.data
	var kind: String = str(visit.get("kind", ""))
	if kind == "vender":
		items.remove_item(items.find_item(int(visit.get("item", 0))))
	elif kind == "comprar" and not data.job_item.is_empty() and not _has_open_job(data.id):
		(
			GameState
			. add_job(
				{
					"client": data.signature,
					"client_id": String(data.id),
					"item": String(data.job_item),
					"want": data.job_text,
					"pay": data.job_pay,
					"deadline": GameState.day + data.job_days,
					"hint": data.job_hint,
					"since": GameState.day,
				}
			)
		)
		_write_slip("Te dejo un encargo\nen el tablón.")
	_leave(&"cansado")


func _has_open_job(customer_id: StringName) -> bool:
	for job: Dictionary in GameState.jobs:
		if (
			str(job.get("client_id", "")) == String(customer_id)
			and str(job.get("state", "")) == "abierto"
		):
			return true
	return false


func _leave(expression: StringName) -> void:
	if customer == null:
		phase = Phase.NONE
		return
	customer.face = expression
	phase = Phase.LEAVING
	var exit: Vector3 = visit.get("from", Station.ENTRY_LEFT)
	customer.walk([Vector3(exit.x * 0.5, 0.0, PASSING_Z), exit])
	customer.arrived.connect(_on_left, CONNECT_ONE_SHOT)


func _on_left() -> void:
	if customer != null:
		customer.queue_free()
	customer = null
	visit = {}
	phase = Phase.NONE
	_cooldown = _rng.randf_range(COOLDOWN.x, COOLDOWN.y)
	get_tree().create_timer(4.0).timeout.connect(
		func() -> void:
			if phase == Phase.NONE and multiplayer.is_server():
				slip.hide_paper()
	)


## Se acaba el día: quien esté se va sin más (solo el anfitrión).
func close_for_the_night() -> void:
	if not multiplayer.is_server():
		return
	if str(visit.get("kind", "")) == "vender":
		items.remove_item(items.find_item(int(visit.get("item", 0))))
	var wad: Carryable = items.find_item(int(visit.get("wad", 0)))
	if wad != null:
		items.remove_item(wad)
	if customer != null:
		customer.queue_free()
	customer = null
	visit = {}
	phase = Phase.NONE
	_cooldown = 3.0
	slip.hide_paper()


func _build_customer(values: Dictionary) -> Node:
	var built: Customer = Customer.new()
	built.setup(StringName(str(values["id"])), values["where"])
	return built
