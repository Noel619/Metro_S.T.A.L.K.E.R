class_name Backpack
extends RefCounted
## La mochila y el cinturón (F3-03, docs/SUPERFICIE.md 4.1): una cuadrícula de 6 × 5
## donde cada cosa ocupa su forma (la de su ficha, [member ItemData.grid_shape]) y
## se puede girar, y tres huecos de cinturón para cosas pequeñas. Solo datos: se
## guarda y se replica dentro del estado de la partida ([member GameState.packs]),
## y lo cambia el anfitrión ([PlayerPack]).
##
## Lo que va suelto suena al andar: lo de metal o cristal que no tiene al lado algo
## blando (ropa, trapos, papeles, vendas). Empaquetar bien también es sigilo.

const SIZE: Vector2i = Vector2i(6, 5)
const BELT_SLOTS: int = 3
## En el cinturón cabe lo que ocupa uno o dos huecos de la cuadrícula.
const BELT_MAX_CELLS: int = 2
## Lo que suena si va suelto y lo que acolcha.
const RATTLY: Array[ItemData.Category] = [
	ItemData.Category.HERRAMIENTAS, ItemData.Category.ENVASES, ItemData.Category.CHATARRA
]
## Y lo que suena aunque no sea de esas clases (una lata llena).
const RATTLY_ITEMS: Array[StringName] = [&"lata_conserva", &"despertador", &"dosimetro"]
const SOFT: Array[ItemData.Category] = [ItemData.Category.ROPA]
const SOFT_ITEMS: Array[StringName] = [
	&"trapo", &"papeles", &"vendas", &"bolsa_plastico", &"carton_plegado"
]

## Lo que hay dentro: {estado (diccionario de [ItemState]), celda (Vector2i), girado}.
var entries: Array[Dictionary] = []
## El cinturón: el estado de lo que hay en cada hueco (o vacío).
var belt: Array[Dictionary] = [{}, {}, {}]


## La forma de [param data] (girada un cuarto de vuelta con [param rotated]),
## empezando en (0, 0).
static func shape_of(data: ItemData, rotated: bool) -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	for cell: Vector2i in data.grid_shape:
		cells.append(Vector2i(cell.y, cell.x) if rotated else cell)
	var low: Vector2i = Vector2i(999, 999)
	for cell: Vector2i in cells:
		low = Vector2i(mini(low.x, cell.x), mini(low.y, cell.y))
	for index: int in cells.size():
		cells[index] -= low
	return cells


## Cabe [param data] en [param cell] (girado o no), sin salirse ni pisar nada.
func fits(data: ItemData, cell: Vector2i, rotated: bool = false, ignore: int = -1) -> bool:
	var taken: Dictionary = _occupied(ignore)
	for part: Vector2i in shape_of(data, rotated):
		var at: Vector2i = cell + part
		if at.x < 0 or at.y < 0 or at.x >= SIZE.x or at.y >= SIZE.y or taken.has(at):
			return false
	return true


## Mete [param state] en [param cell]. Devuelve si cabía.
func place(state: ItemState, cell: Vector2i, rotated: bool = false) -> bool:
	if state.data == null or not fits(state.data, cell, rotated):
		return false
	entries.append({"estado": state.to_dict(), "celda": cell, "girado": rotated})
	return true


## Mete [param state] en el primer sitio donde quepa (de arriba abajo, de izquierda a
## derecha; si no cabe, girado). Devuelve si cabía.
func auto_place(state: ItemState) -> bool:
	if state.data == null:
		return false
	for rotated: bool in [false, true]:
		for y: int in SIZE.y:
			for x: int in SIZE.x:
				if place(state, Vector2i(x, y), rotated):
					return true
	return false


## Saca lo que hay en [param index] (y lo devuelve), o null.
func take(index: int) -> ItemState:
	if index < 0 or index >= entries.size():
		return null
	var entry: Dictionary = entries[index]
	entries.remove_at(index)
	return ItemState.from_dict(entry["estado"])


## Lo que ocupa la celda [param cell] (su índice), o -1.
func index_at(cell: Vector2i) -> int:
	for index: int in entries.size():
		var entry: Dictionary = entries[index]
		var data: ItemData = ItemState.load_data(StringName(entry["estado"].get("id", "")))
		if data == null:
			continue
		for part: Vector2i in shape_of(data, bool(entry["girado"])):
			if Vector2i(entry["celda"]) + part == cell:
				return index
	return -1


## Mueve lo que hay en [param index] a [param cell] (girado o no). Devuelve si cabía.
func move(index: int, cell: Vector2i, rotated: bool) -> bool:
	if index < 0 or index >= entries.size():
		return false
	var data: ItemData = _data(index)
	if data == null or not fits(data, cell, rotated, index):
		return false
	entries[index]["celda"] = cell
	entries[index]["girado"] = rotated
	return true


## Cabe en el cinturón (es pequeño).
static func belt_accepts(data: ItemData) -> bool:
	return data != null and data.grid_shape.size() <= BELT_MAX_CELLS


## Pone [param state] en el hueco [param slot] del cinturón. Devuelve si cabía.
func put_on_belt(state: ItemState, slot: int) -> bool:
	if slot < 0 or slot >= BELT_SLOTS or not belt[slot].is_empty():
		return false
	if not belt_accepts(state.data):
		return false
	belt[slot] = state.to_dict()
	return true


## Saca lo del hueco [param slot] del cinturón, o null.
func take_from_belt(slot: int) -> ItemState:
	if slot < 0 or slot >= BELT_SLOTS or belt[slot].is_empty():
		return null
	var state: ItemState = ItemState.from_dict(belt[slot])
	belt[slot] = {}
	return state


## Lo que pesa todo (la mochila y el cinturón), en kilos.
func weight() -> float:
	var total: float = 0.0
	for index: int in entries.size():
		var data: ItemData = _data(index)
		total += data.weight if data != null else 0.0
	for slot: Dictionary in belt:
		if not slot.is_empty():
			var data: ItemData = ItemState.load_data(StringName(slot.get("id", "")))
			total += data.weight if data != null else 0.0
	return total


## Las cosas que suenan al andar: lo de metal o cristal sin nada blando al lado.
func loose_items() -> int:
	var soft_cells: Dictionary = {}
	for index: int in entries.size():
		if _is_soft(_data(index)):
			for cell: Vector2i in _cells(index):
				soft_cells[cell] = true
	var loose: int = 0
	for index: int in entries.size():
		var data: ItemData = _data(index)
		if data == null or not (RATTLY.has(data.category) or RATTLY_ITEMS.has(data.id)):
			continue
		var padded: bool = false
		for cell: Vector2i in _cells(index):
			for step: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
				if soft_cells.has(cell + step):
					padded = true
		if not padded:
			loose += 1
	return loose


## Está vacía (la mochila y el cinturón).
func is_empty() -> bool:
	return entries.is_empty() and belt.all(func(slot: Dictionary) -> bool: return slot.is_empty())


func to_dict() -> Dictionary:
	var saved: Array = []
	for entry: Dictionary in entries:
		var cell: Vector2i = entry["celda"]
		saved.append(
			{"estado": entry["estado"], "celda": [cell.x, cell.y], "girado": entry["girado"]}
		)
	return {"mochila": saved, "cinturon": belt.duplicate(true)}


static func from_dict(data: Dictionary) -> Backpack:
	var pack: Backpack = Backpack.new()
	for value: Variant in data.get("mochila", []):
		if not value is Dictionary:
			continue
		var entry: Dictionary = value
		var cell: Array = entry.get("celda", [0, 0])
		(
			pack
			. entries
			. append(
				{
					"estado": entry.get("estado", {}),
					"celda": Vector2i(int(cell[0]), int(cell[1])),
					"girado": bool(entry.get("girado", false)),
				}
			)
		)
	var slots: Array = data.get("cinturon", [])
	for slot: int in BELT_SLOTS:
		pack.belt[slot] = slots[slot] if slot < slots.size() and slots[slot] is Dictionary else {}
	return pack


func _data(index: int) -> ItemData:
	return ItemState.load_data(StringName(entries[index]["estado"].get("id", "")))


func _cells(index: int) -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	var data: ItemData = _data(index)
	if data == null:
		return cells
	for part: Vector2i in shape_of(data, bool(entries[index]["girado"])):
		cells.append(Vector2i(entries[index]["celda"]) + part)
	return cells


func _occupied(ignore: int) -> Dictionary:
	var taken: Dictionary = {}
	for index: int in entries.size():
		if index == ignore:
			continue
		for cell: Vector2i in _cells(index):
			taken[cell] = true
	return taken


static func _is_soft(data: ItemData) -> bool:
	return data != null and (SOFT.has(data.category) or SOFT_ITEMS.has(data.id))
