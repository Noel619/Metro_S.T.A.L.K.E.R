class_name LedgerFixture
extends Fixture
## El libro de cuentas (F2-10): F lo abre y se ve de cerca, escrito a mano, día
## por día (de lo último a lo primero): ventas, compras, comida, el impuesto y
## lo que queda en la caja. Lo escribe [GameState]; aquí solo se lee.

const LINES_PER_PAGE: int = 16
const KIND_NAMES: Dictionary = {
	"venta": "Venta",
	"compra": "Compra",
	"comida": "Comida",
	"impuesto": "Impuesto",
	"encargo": "Encargo",
	"deuda": "Se debe",
}

var model: Node3D
var _cover: Node3D
var _open_time: float = 0.0


func _ready() -> void:
	var body: Node = model.find_children("*", "StaticBody3D", true, false)[0]
	_cover = model.find_child("tapa", true, false) as Node3D
	add_use(body, &"mirar")
	super._ready()


func _on_looked(_player: Node) -> void:
	_open_time = 0.6
	CloseUp.open(get_tree(), pages())


## Las páginas del libro, tal como están ahora: una por día, con lo último primero.
static func pages() -> Array:
	var result: Array = []
	for day: int in range(GameState.day, 0, -1):
		var entries: Array = GameState.entries_of(day)
		if entries.is_empty() and day != GameState.day:
			continue
		result.append(page_of(day, entries))
	return result


static func page_of(day: int, entries: Array) -> Dictionary:
	var rotulos: Array = [
		{
			"text": "Día %d" % day,
			"x": 120,
			"y": 70,
			"size": 54,
			"font": "manuscrita_negrita",
			"color": "#2b2622",
			"rot": -1,
		}
	]
	var y: float = 150.0
	var balance: int = 0
	for entry: Dictionary in entries.slice(0, LINES_PER_PAGE):
		var amount: int = int(entry.get("amount", 0))
		balance += amount
		var minute: int = int(entry.get("minute", 0))
		var kind: String = KIND_NAMES.get(str(entry.get("kind", "")), str(entry.get("kind", "")))
		rotulos.append(_line("%02d:%02d" % [minute / 60, minute % 60], 120, y, "#5a5450"))
		rotulos.append(_line("%s · %s" % [kind, str(entry.get("concept", ""))], 220, y, "#2b2622"))
		if amount != 0:
			var color: String = "#2b2622" if amount > 0 else "#8e3b2e"
			rotulos.append(_line("%+d ₽" % amount, 640, y, color))
		y += 44.0
	if day == GameState.day:
		rotulos.append(_line("En la caja: %d ₽" % GameState.rubles, 880, 150, "#2b2622", 40))
		var debt: String = (
			"Se debe a la administración: %d ₽" % GameState.debt
			if GameState.debt > 0
			else "Nada que deber"
		)
		rotulos.append(_line(debt, 880, 205, "#8e3b2e" if GameState.debt > 0 else "#2b2622", 34))
	elif balance != 0:
		rotulos.append(_line("Del día: %+d ₽" % balance, 880, 150, "#2b2622", 38))
	return {"svg": "cuaderno_doble", "ancho_m": 0.5, "rotulos": rotulos, "giro": 0.0}


static func _line(text: String, x: float, y: float, color: String, size: int = 34) -> Dictionary:
	return {
		"text": text,
		"x": x,
		"y": y,
		"size": size,
		"font": "manuscrita",
		"color": color,
		"rot": -0.6
	}


func _process(delta: float) -> void:
	if _cover == null:
		return
	_open_time = maxf(0.0, _open_time - delta) if not CloseUp.is_open() else 0.6
	var target: float = PI * 0.92 if _open_time > 0.0 else 0.0
	_cover.rotation.z = move_toward(_cover.rotation.z, target, delta * 5.0)
