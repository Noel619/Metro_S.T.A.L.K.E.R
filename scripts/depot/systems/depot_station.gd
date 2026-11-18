class_name DepotStation
extends Node3D
## Lo de la estación (F2-11, F2-12): el puesto de comida con su vendedora, el
## buzón de los pagos de la administración, el tablón de avisos y lo que llega
## cada mañana bajo la persiana: el aviso del impuesto y, si se pagó, el recibo
## con su sello. Con mucha deuda, la administración precinta el mostrador.

## Lo que cuesta cada cosa en el puesto.
const SOUP_PRICE: int = 10
const BREAD_PRICE: int = 4
## Lo que tarda la vendedora en coger el dinero y servir (segundos).
const SERVE_DELAY: float = 1.2
## La zona del mostrador del puesto donde se deja el dinero.
const STALL_ZONE: Vector3 = Vector3(1.2, 0.4, 0.45)
const HOLD: float = 0.6
const STATE_ID: String = "administracion"
## Dónde aparecen los papeles de la mañana, en el mostrador (bajo la persiana).
const MORNING_AT: Vector3 = Vector3(0.38, DepotRoom.COUNTER_TOP + 0.003, 3.36)
const RECEIPT_AT: Vector3 = Vector3(-0.32, DepotRoom.COUNTER_TOP + 0.004, 3.32)
const SEAL_AT: Vector3 = Vector3(0.0, DepotRoom.COUNTER_TOP + 0.08, 3.5)
const STAMP_COLOR: String = "#5b3f86"
## Los avisos del tablón de la estación: [texto, x, y, giro].
const NOTICES: Array = [
	[
		["*AVISO", "Se recuerda que el", "agua de la fuente", "es solo para beber."],
		-0.8,
		1.85,
		-3.0
	],
	[
		["*OBJETOS PERDIDOS", "Un guante de niño,", "azul. Preguntar en", "la administración."],
		-0.25,
		1.95,
		2.0
	],
	[["*NORMAS", "Prohibido encender", "fuego en el andén.", "Prohibido subir."], 0.32, 1.8, -1.5],
	[["Se cambia estufa", "por mantas.", "Tienda 14."], 0.85, 1.9, 4.0],
	[
		["*TURNOS DE GUARDIA", "Lunes: Brigada 2", "Martes: Brigada 1", "Miércoles: Brigada 3"],
		-0.55,
		1.35,
		1.0
	],
	[["Dibujo de Sasha,", "6 años:", "el sol de arriba."], 0.55, 1.3, -4.0],
]

var room: DepotRoom
var station: Station
var items: WorldItems
var world: DepotWorld
var counter: DepotCounter

var vendor: Customer
var morning: NoteFixture
var receipt: NoteFixture
var seal: NoteFixture
var _mailbox_hold: Dictionary = {}
var _stall_wait: Dictionary = {}


func _ready() -> void:
	morning = _note("aviso_manana", MORNING_AT, Vector3(-90.0, -12.0, 0.0))
	receipt = _note("recibo", RECEIPT_AT, Vector3(-90.0, 6.0, 0.0))
	seal = _note("precinto", SEAL_AT, Vector3(0.0, 180.0, 0.0))
	var admin: Node3D = station.get_node(^"Fijo/Ventanilla") as Node3D
	var mailbox: MailboxFixture = MailboxFixture.new()
	mailbox.fixture_id = "buzon"
	mailbox.name = "Buzon"
	mailbox.model = admin
	mailbox.paid.connect(_on_paid)
	add_child(mailbox)
	_notices()
	# La vendedora: está siempre detrás de su mostrador. La pone cada equipo.
	vendor = Customer.new()
	vendor.setup(&"vendedora", Station.STALL_VENDOR)
	vendor.rotation.y = 0.0
	add_child(vendor)
	EventBus.day_started.connect(_on_day_started)
	GameState.changed.connect(_refresh_seal)


func _note(id: String, where: Vector3, turn: Vector3) -> NoteFixture:
	var note: NoteFixture = NoteFixture.new()
	note.fixture_id = id
	note.name = id.capitalize().replace(" ", "")
	note.position = where
	note.rotation_degrees = turn
	add_child(note)
	return note


func _notices() -> void:
	for index: int in NOTICES.size():
		var entry: Array = NOTICES[index]
		var card: PaperCard = PaperCard.create(PaperCard.note(entry[0], 0.2))
		card.name = "Aviso_%d" % index
		card.position = Station.NOTICE_BOARD + Vector3(-float(entry[1]), float(entry[2]), -0.035)
		card.rotation_degrees = Vector3(0.0, 180.0, float(entry[3]))
		add_child(card)


func _process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	_serve(delta)


## El puesto: un fajo en su mostrador es pedir (sopa si llega, si no pan).
func _serve(delta: float) -> void:
	var waiting: Dictionary = {}
	for item: Carryable in items.items():
		if item.is_held() or item.state.data.tool != &"billetes":
			continue
		var local: Vector3 = item.body().global_position - Station.STALL_COUNTER
		if absf(local.x) > STALL_ZONE.x / 2.0 or absf(local.z) > STALL_ZONE.z / 2.0:
			continue
		if absf(local.y) > STALL_ZONE.y:
			continue
		var uid: int = item.state.uid
		var waited: float = float(_stall_wait.get(uid, 0.0)) + delta
		waiting[uid] = waited
		if waited >= SERVE_DELAY:
			waiting.erase(uid)
			sell_food(item)
	_stall_wait = waiting


## La vendedora coge el dinero y pone la comida (y la vuelta) en el mostrador.
func sell_food(wad: Carryable) -> void:
	var amount: int = int(wad.state.extra.get("rublos", 0))
	var food: StringName = &""
	var price: int = 0
	if amount >= SOUP_PRICE:
		food = &"sopa"
		price = SOUP_PRICE
	elif amount >= BREAD_PRICE:
		food = &"pan"
		price = BREAD_PRICE
	if food.is_empty():
		vendor.face = &"cansado"
		return
	var where: Vector3 = wad.body().global_position
	items.remove_item(wad)
	var serve: Transform3D = Transform3D(
		Basis.IDENTITY, Station.STALL_COUNTER + Vector3(-0.25, 0.02, 0.05)
	)
	items.spawn_item(food, serve)
	if amount > price:
		items.spawn_with(
			&"billetes",
			Transform3D(Basis.IDENTITY, where + Vector3(0, 0.03, 0)),
			{"rublos": amount - price}
		)
	GameState.record("comida", "Sopa" if food == &"sopa" else "Pan", -price)
	vendor.face = &"sonrisa"
	get_tree().create_timer(3.0).timeout.connect(func() -> void: vendor.face = &"neutro")


func _on_paid(amount: int) -> void:
	var paid: int = int(world.value(STATE_ID, "pagado", 0)) + amount
	world.set_value(STATE_ID, "pagado", paid)
	_refresh_seal()


## Por la mañana (en el anfitrión): el aviso bajo la persiana y el recibo de lo
## que se pagó ayer.
func _on_day_started(day: int) -> void:
	if not multiplayer.is_server():
		return
	var paid: int = int(world.value(STATE_ID, "pagado", 0))
	world.set_value(STATE_ID, "pagado", 0)
	morning.write(morning_paper(day))
	if paid > 0:
		receipt.write(receipt_paper(day - 1, paid))
	else:
		receipt.hide_paper()
	_refresh_seal()


static func morning_paper(day: int) -> Dictionary:
	var lines: Array = ["*Día %d" % day, "Impuesto de hoy: %d ₽." % GameState.TAX_PER_DAY]
	if GameState.debt > 0:
		lines.append("Se nos debe: %d ₽." % GameState.debt)
		if GameState.debt >= GameState.SEAL_DEBT:
			lines.append("*Mostrador precintado")
			lines.append("hasta que pague.")
	elif GameState.debt < 0:
		lines.append("A cuenta: %d ₽." % -GameState.debt)
	else:
		lines.append("Está al corriente.")
	lines.append("Pagos en el buzón")
	lines.append("de la ventanilla.")
	lines.append("— Administración")
	return PaperCard.note(lines, 0.13)


static func receipt_paper(day: int, amount: int) -> Dictionary:
	var rotulos: Array = [
		_typed("RECIBO", 40, 40, 44),
		_typed("Administración de la estación", 40, 100, 24),
		_typed("Recibido: %d ₽" % amount, 40, 170, 30),
		_typed("Concepto: impuesto", 40, 220, 26),
		_typed("Día %d" % day, 40, 270, 26),
		{
			"text": "PAGADO",
			"x": 230,
			"y": 360,
			"size": 64,
			"font": "rotulo",
			"color": STAMP_COLOR,
			"rot": -14,
		},
		{
			"text": "DÍA %d" % day,
			"x": 290,
			"y": 440,
			"size": 34,
			"font": "rotulo_fino",
			"color": STAMP_COLOR,
			"rot": -14,
		},
	]
	return {"svg": "recibo", "ancho_m": 0.12, "rotulos": rotulos}


static func _typed(text: String, x: float, y: float, size: int) -> Dictionary:
	return {
		"text": text, "x": x, "y": y, "size": size, "font": "maquina", "color": "#2b2622", "rot": 0
	}


## El precinto: una tira de papel con sellos sobre el mostrador mientras se deba
## demasiado.
func _refresh_seal() -> void:
	if not multiplayer.is_server() or seal == null or not seal.is_inside_tree():
		return
	if GameState.is_sealed():
		if not seal.is_shown():
			(
				seal
				. write(
					{
						"svg": "marco_papel",
						"ancho_m": 0.9,
						"rotulos":
						[
							{
								"text": "PRECINTADO",
								"x": 90,
								"y": 70,
								"size": 80,
								"font": "rotulo",
								"color": STAMP_COLOR,
								"rot": -3,
							},
							{
								"text": "Por deudas con la administración",
								"x": 70,
								"y": 190,
								"size": 26,
								"font": "maquina",
								"color": "#2b2622",
								"rot": 0,
							},
						],
					}
				)
			)
	elif seal.is_shown():
		seal.hide_paper()
