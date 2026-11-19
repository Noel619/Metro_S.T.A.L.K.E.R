class_name BackpackGrid
extends RefCounted
## La cuadrícula de la mochila (README 6.5): dónde va cada cosa, si cabe otra y
## cuánto pesa y cuánto suena lo que lleva.
##
## Cada objeto ocupa las casillas de su [member ItemData.grid_shape], girada un
## cuarto de vuelta las veces que diga su giro, a partir de su casilla (la de
## arriba a la izquierda). Lo que va suelto y es de metal o de cristal suena al
## andar ([member ItemData.rattles]): cuantas más casillas libres lo rodean, más.
## Empaquetar bien también es sigilo.
##
## Lo que lleva se guarda en el estado de la mochila ([member ItemState.extra],
## clave [constant KEY]) como valores de JSON, así que se guarda con la partida
## y llega a todos los equipos con el resto de su estado.

## La clave del contenido en el estado de la mochila.
const KEY: String = "mochila"
## La mochila con la que se empieza: 6 casillas de ancho y 5 de alto.
const SIZE: Vector2i = Vector2i(6, 5)
## Lo que no puede ir dentro de una mochila.
const NOT_INSIDE: Array[StringName] = [&"mochila"]

var size: Vector2i = SIZE
## Lo que lleva: {"estado": [method ItemState.to_dict], "celda": [x, y], "giro": vueltas}.
var entries: Array[Dictionary] = []


## La cuadrícula guardada en el estado de una mochila.
static func from_extra(extra: Dictionary, grid_size: Vector2i = SIZE) -> BackpackGrid:
	var grid: BackpackGrid = BackpackGrid.new()
	grid.size = grid_size
	var saved: Variant = extra.get(KEY, [])
	if saved is Array:
		for value: Variant in saved:
			if not value is Dictionary:
				continue
			var entry: Dictionary = value
			var state: ItemState = ItemState.from_dict(entry.get("estado", {}))
			if state.data == null:
				continue
			var cell: Vector2i = to_cell(entry.get("celda", [0, 0]))
			grid.entries.append(
				{
					"estado": state.to_dict(),
					"celda": [cell.x, cell.y],
					"giro": int(entry.get("giro", 0))
				}
			)
	return grid


## Lo que se guarda en el estado de la mochila (en [constant KEY]).
func to_value() -> Array:
	return entries.duplicate(true)


## El estado del objeto de la entrada [param index].
func state_at(index: int) -> ItemState:
	return ItemState.from_dict(entries[index]["estado"])


## Las casillas que ocupa la entrada [param index].
func cells_of(index: int) -> Array[Vector2i]:
	var entry: Dictionary = entries[index]
	var data: ItemData = ItemState.load_data(StringName(str(entry["estado"].get("id", ""))))
	return footprint(data, to_cell(entry["celda"]), int(entry["giro"]))


## Las casillas que ocuparía [param data] en [param cell] con [param turns] giros.
static func footprint(data: ItemData, cell: Vector2i, turns: int) -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	if data == null:
		return cells
	for offset: Vector2i in data.rotated_shape(turns):
		cells.append(cell + offset)
	return cells


## Ancho y alto que ocupa [param data] con [param turns] giros.
static func extent(data: ItemData, turns: int) -> Vector2i:
	var result: Vector2i = Vector2i.ZERO
	for offset: Vector2i in data.rotated_shape(turns):
		result = result.max(offset + Vector2i.ONE)
	return result


## La entrada que ocupa [param cell], o -1 si está libre.
func occupant(cell: Vector2i) -> int:
	for index: int in entries.size():
		if cells_of(index).has(cell):
			return index
	return -1


## ¿Puede ir [param data] en la mochila? (Otra mochila, no.)
static func accepts(data: ItemData) -> bool:
	return data != null and not NOT_INSIDE.has(data.id)


## ¿Cabe [param data] en [param cell] con [param turns] giros? [param skip] es una
## entrada que no cuenta (la que se está moviendo).
func fits(data: ItemData, cell: Vector2i, turns: int, skip: int = -1) -> bool:
	if not accepts(data):
		return false
	var taken: Dictionary = _taken(skip)
	for spot: Vector2i in footprint(data, cell, turns):
		if spot.x < 0 or spot.y < 0 or spot.x >= size.x or spot.y >= size.y:
			return false
		if taken.has(spot):
			return false
	return true


## Dónde cabe [param data]: primero tocando [param near] (si se da) y si no, en
## la primera casilla libre, de arriba abajo y de izquierda a derecha, sin girar
## o girado. Devuelve {"celda": Vector2i, "giro": int}, o vacío si no cabe.
func find_spot(data: ItemData, near: Vector2i = Vector2i(-1, -1)) -> Dictionary:
	if not accepts(data):
		return {}
	var turns: Array[int] = [0, 1]
	if near.x >= 0:
		# Que la casilla apuntada quede dentro de lo que ocupa: se prueban todas las
		# posiciones del objeto que la cubren, empezando por la que la deja arriba a
		# la izquierda.
		for turn: int in turns:
			for offset: Vector2i in data.rotated_shape(turn):
				var cell: Vector2i = near - offset
				if fits(data, cell, turn):
					return {"celda": cell, "giro": turn}
	for turn: int in turns:
		for y: int in size.y:
			for x: int in size.x:
				if fits(data, Vector2i(x, y), turn):
					return {"celda": Vector2i(x, y), "giro": turn}
	return {}


## Mete un objeto. Devuelve si cabía.
func put(state: ItemState, cell: Vector2i, turns: int) -> bool:
	if state == null or not fits(state.data, cell, turns):
		return false
	entries.append({"estado": state.to_dict(), "celda": [cell.x, cell.y], "giro": posmod(turns, 4)})
	return true


## Saca la entrada [param index] y devuelve su estado.
func take(index: int) -> ItemState:
	if index < 0 or index >= entries.size():
		return null
	var state: ItemState = state_at(index)
	entries.remove_at(index)
	return state


## Lo que pesa lo que lleva (sin la mochila).
func weight() -> float:
	var total: float = 0.0
	for entry: Dictionary in entries:
		var state: ItemState = ItemState.from_dict(entry["estado"])
		if state.data != null:
			total += state.weight()
	return total


## Las casillas libres.
func free_cells() -> int:
	return size.x * size.y - _taken().size()


## Cuánto suena lo que va suelto al andar: por cada objeto que suena, la parte
## de las casillas de su alrededor que están libres (de 0, bien apretado, a 1,
## suelto del todo). Las paredes de la mochila sujetan.
func rattle() -> float:
	var taken: Dictionary = _taken()
	var total: float = 0.0
	for index: int in entries.size():
		var data: ItemData = state_at(index).data
		if data == null or not data.rattles:
			continue
		var own: Array[Vector2i] = cells_of(index)
		var around: Dictionary = {}
		for cell: Vector2i in own:
			for step: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
				var next: Vector2i = cell + step
				if not own.has(next):
					around[next] = true
		var loose: int = 0
		for cell: Vector2i in around:
			var inside: bool = cell.x >= 0 and cell.y >= 0 and cell.x < size.x and cell.y < size.y
			if inside and not taken.has(cell):
				loose += 1
		total += float(loose) / maxf(1.0, around.size())
	return total


## Lo que se puede romper si se corre o se cae (los que tienen fragilidad).
func fragile() -> Array[ItemState]:
	var found: Array[ItemState] = []
	for index: int in entries.size():
		var state: ItemState = state_at(index)
		if state.data != null and state.data.fragility > 0.0:
			found.append(state)
	return found


func _taken(skip: int = -1) -> Dictionary:
	var taken: Dictionary = {}
	for index: int in entries.size():
		if index == skip:
			continue
		for cell: Vector2i in cells_of(index):
			taken[cell] = index
	return taken


## Una casilla guardada ([x, y], como en JSON) como [Vector2i].
static func to_cell(value: Variant) -> Vector2i:
	if value is Vector2i:
		return value
	if value is Array and (value as Array).size() >= 2:
		return Vector2i(int(value[0]), int(value[1]))
	return Vector2i.ZERO
