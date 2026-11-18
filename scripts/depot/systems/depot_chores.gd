class_name DepotChores
extends Node3D
## El primer día (F2-05, docs/DEPOSITO.md 4.1): el local sucio, con lo que dejó
## el antiguo dueño, y la nota de la administración clavada en la puerta con lo
## que hay que hacer antes de abrir. Cada cosa se tacha sola al hacerla.
##
## Monta las manchas, las telarañas, la lámpara, la persiana, la estufa, el cubo
## y el contenedor; en el anfitrión, abre las cajas del antiguo dueño y lleva la
## cuenta de lo hecho.

const CHORES: Array[String] = [
	"telaranas", "barrer", "fregar", "basura", "cajas", "bombilla", "persiana", "estufa"
]
const CHORE_TEXT: Dictionary = {
	"telaranas": "Quitar las telarañas",
	"barrer": "Barrer el polvo",
	"fregar": "Fregar las manchas",
	"basura": "Sacar la basura al contenedor",
	"cajas": "Vaciar las cajas del antiguo dueño",
	"bombilla": "Cambiar la bombilla del mostrador",
	"persiana": "Desatascar la persiana",
	"estufa": "Encender la estufa",
}
const STATE_ID: String = "tareas"
## Cada cuánto mira el anfitrión lo que está hecho (segundos).
const CHECK_SECONDS: float = 0.5
## Tirones para abrir una caja (unidades del gesto PULL).
const OPEN_WORK: float = 1.2
## [kind, posición, radio, semilla] de cada mancha del suelo.
const DIRT: Array = [
	[DirtFixture.Kind.DUST, Vector3(-0.6, 0.0, 1.6), 0.6, 1.0],
	[DirtFixture.Kind.DUST, Vector3(1.5, 0.0, 0.6), 0.55, 2.0],
	[DirtFixture.Kind.DUST, Vector3(-2.9, 0.0, 0.4), 0.5, 3.0],
	[DirtFixture.Kind.DUST, Vector3(2.9, 0.0, -1.6), 0.6, 4.0],
	[DirtFixture.Kind.DUST, Vector3(-3.0, 0.0, -2.2), 0.5, 5.0],
	[DirtFixture.Kind.DUST, Vector3(0.6, 0.0, -0.9), 0.5, 6.0],
	[DirtFixture.Kind.STAIN, Vector3(3.3, 0.0, 1.2), 0.45, 7.0],
	[DirtFixture.Kind.STAIN, Vector3(-0.2, 0.0, 2.35), 0.4, 8.0],
	[DirtFixture.Kind.STAIN, Vector3(2.2, 0.0, -2.6), 0.5, 9.0],
]
## [posición, giro (grados), tamaño] de cada telaraña.
const COBWEBS: Array = [
	[Vector3(-4.38, 2.55, 3.0), Vector3(0.0, 120.0, 0.0), 0.8],
	[Vector3(4.38, 2.55, 3.05), Vector3(0.0, -120.0, 0.0), 0.7],
	[Vector3(-4.4, 2.5, -1.2), Vector3(0.0, 90.0, 0.0), 0.75],
	[Vector3(4.4, 2.5, -3.5), Vector3(0.0, -135.0, 0.0), 0.8],
	[Vector3(-1.2, 2.45, 1.45), Vector3(0.0, 180.0, 0.0), 0.6],
]
## La nota de la puerta, por dentro.
const NOTE_AT: Vector3 = Vector3(3.88, 1.5, DepotRoom.FRONT_INNER - 0.035)

var room: DepotRoom
var station: Station
var items: WorldItems
var world: DepotWorld

var shutter: ShutterFixture
var door: DoorFixture
var lamp: LampFixture
var stove: StoveFixture
var bin: TrashBinFixture
var dumpster: DumpsterFixture
var note: NoteFixture
var dirt: Array[DirtFixture] = []
var cobwebs: Array[CobwebFixture] = []
## La primera vez se mira enseguida (y se escribe la nota).
var _check: float = CHECK_SECONDS
var _hold: Dictionary = {}


func _ready() -> void:
	shutter = _fixture(ShutterFixture.new(), "persiana") as ShutterFixture
	shutter.model = room.fixed("Persiana")
	door = _fixture(DoorFixture.new(), "puerta") as DoorFixture
	door.model = room.fixed("Puerta")
	lamp = _fixture(LampFixture.new(), "lampara_mostrador") as LampFixture
	lamp.model = room.fixed("Lampara_Mostrador")
	lamp.light = room.get_node_or_null(^"Luz_Mostrador") as OmniLight3D
	stove = _fixture(StoveFixture.new(), "estufa") as StoveFixture
	stove.model = room.fixed("Estufa")
	bin = _fixture(TrashBinFixture.new(), "cubo") as TrashBinFixture
	bin.model = room.fixed("Cubo")
	dumpster = _fixture(DumpsterFixture.new(), "contenedor") as DumpsterFixture
	dumpster.model = station.get_node(^"Fijo/Contenedor") as Node3D
	for index: int in DIRT.size():
		var entry: Array = DIRT[index]
		var patch: DirtFixture = DirtFixture.new()
		patch.kind = entry[0]
		patch.radius = entry[2]
		patch.seed = entry[3]
		patch.position = (entry[1] as Vector3) + Vector3(0.0, DepotRoom.FLOOR, 0.0)
		var prefix: String = "polvo" if patch.kind == DirtFixture.Kind.DUST else "mancha"
		dirt.append(_fixture(patch, "%s_%d" % [prefix, index]) as DirtFixture)
	for index: int in COBWEBS.size():
		var entry: Array = COBWEBS[index]
		var web: CobwebFixture = CobwebFixture.new()
		web.size = entry[2]
		web.position = entry[0]
		web.rotation_degrees = entry[1]
		cobwebs.append(_fixture(web, "telarana_%d" % index) as CobwebFixture)
	note = NoteFixture.new()
	note.position = NOTE_AT
	note.rotation_degrees.y = 180.0
	_fixture(note, "nota_tareas")
	for fixture: Node in [shutter, door, lamp, stove, bin, dumpster]:
		add_child(fixture)
	for fixture: Node in dirt:
		add_child(fixture)
	for fixture: Node in cobwebs:
		add_child(fixture)
	add_child(note)
	items.item_worked.connect(_on_item_worked)


func _fixture(fixture: Fixture, id: String) -> Fixture:
	fixture.fixture_id = id
	fixture.name = id.capitalize().replace(" ", "")
	return fixture


## Las tareas hechas (nombres de [constant CHORES]).
func done() -> Array:
	var value: Variant = world.value(STATE_ID, "hechas", [])
	return value if value is Array else []


func all_done() -> bool:
	return done().size() >= CHORES.size()


func _process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	_check += delta
	if _check < CHECK_SECONDS:
		return
	_check = 0.0
	var finished: Array = done().duplicate()
	for chore: String in CHORES:
		if not finished.has(chore) and _is_done(chore):
			finished.append(chore)
	if finished.size() != done().size():
		world.set_value(STATE_ID, "hechas", finished)
	var paper: Dictionary = note_paper(finished)
	if note.paper() != paper or not note.is_shown():
		note.write(paper)
	if finished.size() >= CHORES.size() and not GameState.flags.get("primer_dia_hecho", false):
		GameState.flags["primer_dia_hecho"] = true
		GameState.push()


func _is_done(chore: String) -> bool:
	var result: bool = false
	match chore:
		"telaranas":
			result = cobwebs.all(func(web: CobwebFixture) -> bool: return web.is_clean())
		"barrer":
			result = dirt.all(
				func(patch: DirtFixture) -> bool:
					return patch.kind != DirtFixture.Kind.DUST or patch.is_clean()
			)
		"fregar":
			result = dirt.all(
				func(patch: DirtFixture) -> bool:
					return patch.kind != DirtFixture.Kind.STAIN or patch.is_clean()
			)
		"basura":
			result = dumpster.bags() > 0 and bin.count() == 0 and _loose_trash() == 0
		"cajas":
			result = items.items().all(
				func(item: Carryable) -> bool: return not item.state.extra.has("contenido")
			)
		"bombilla":
			result = lamp.is_lit()
		"persiana":
			result = not shutter.is_jammed()
		"estufa":
			result = stove.is_lit()
	return result


## Basura suelta que queda por el local (o la bolsa sin llevar al contenedor).
func _loose_trash() -> int:
	var count: int = 0
	for item: Carryable in items.items():
		if item.state.data.trash or item.state.data.id == &"bolsa_basura":
			count += 1
	return count


## La nota de la puerta, con lo hecho tachado.
static func note_paper(finished: Array) -> Dictionary:
	var rotulos: Array = [
		_line("Administración de la estación", 18, 22, 22, "rotulo_fino"),
		_line("Antes de abrir:", 22, 56, 30, "manuscrita_negrita"),
	]
	var strikes: Array = []
	var y: float = 96.0
	for index: int in CHORES.size():
		var chore: String = CHORES[index]
		var text: String = "%d. %s" % [index + 1, CHORE_TEXT[chore]]
		rotulos.append(_line(text, 22, y, 21, "manuscrita"))
		if finished.has(chore):
			strikes.append([20, y + 15, 22 + text.length() * 8.6, y + 13])
		y += 26.0
	if finished.size() >= CHORES.size():
		rotulos.append(_line("Bien. Ya puede abrir.", 60, y + 6, 26, "manuscrita_negrita"))
	return {"svg": "papel_suelto", "ancho_m": 0.17, "rotulos": rotulos, "tachados": strikes}


static func _line(text: String, x: float, y: float, size: int, font: String) -> Dictionary:
	var color: String = "#2b2622" if font != "rotulo_fino" else "#5b3f86"
	return {"text": text, "x": x, "y": y, "size": size, "font": font, "color": color, "rot": -1}


## Abrir una caja del antiguo dueño: tirar de las solapas con las manos.
func _on_item_worked(
	item: Carryable, _player: Node, tool: StringName, amount: float, _point: Vector3
) -> void:
	if tool != Workable.HANDS or amount <= 0.0 or not item.state.extra.has("contenido"):
		return
	var held: float = float(_hold.get(item.state.uid, 0.0)) + amount
	if held < OPEN_WORK:
		_hold[item.state.uid] = held
		return
	_hold.erase(item.state.uid)
	open_box(item)


## Abre una caja: lo de dentro sale alrededor y la caja de cartón se queda
## plegada (basura); la de madera, vacía. Solo el anfitrión.
func open_box(item: Carryable) -> void:
	var contents: Variant = item.state.extra.get("contenido", [])
	var center: Vector3 = item.body().global_position
	var top: Vector3 = item.body().global_transform * item.bounds().end
	var index: int = 0
	if contents is Array:
		for entry: Variant in contents:
			if not entry is Dictionary:
				continue
			var values: Dictionary = entry
			var angle: float = TAU * index / maxf(1.0, (contents as Array).size())
			var where: Vector3 = center + Vector3(cos(angle) * 0.35, 0.0, sin(angle) * 0.35)
			where.y = maxf(center.y, DepotRoom.FLOOR) + 0.25 + index * 0.06
			var state: ItemState = ItemState.create(StringName(str(values.get("id", ""))), 0)
			if state.data == null:
				continue
			state.condition = float(values.get("condition", 1.0))
			state.contamination = float(values.get("contamination", 0.0))
			var more: Variant = values.get("extra", {})
			state.extra = (more as Dictionary).duplicate(true) if more is Dictionary else {}
			items.spawn_state(state, Transform3D(Basis.from_euler(Vector3(0, angle, 0)), where))
			index += 1
	var leftover: Transform3D = item.body().global_transform
	var cardboard: bool = String(item.state.data.id).begins_with("caja_carton")
	if cardboard:
		items.remove_item(item)
		items.spawn_item(
			&"carton_plegado", Transform3D(Basis.IDENTITY, leftover.origin + Vector3(0, 0.05, 0))
		)
	else:
		var extra: Dictionary = item.state.extra.duplicate(true)
		extra.erase("contenido")
		item.set_values({"extra": extra})
	DustPuff.burst(self, Vector3(center.x, top.y, center.z), 1.0)
