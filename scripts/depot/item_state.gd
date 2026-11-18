class_name ItemState
extends RefCounted
## Un ejemplar concreto de un objeto: esta lata, con su abolladura y su dosis.
##
## Todo lo que existe en el mundo tiene un identificador, se puede guardar y se
## puede replicar (README 13.1): por eso el estado viaja como diccionario.

const ITEMS_DIR: String = "res://data/items/"

var data: ItemData
## Identificador único en la partida.
var uid: int = 0
## De 0 (roto) a 1 (como nuevo).
var condition: float = 1.0
## De 0 (limpio) a 1 (hay que apartarlo).
var contamination: float = 0.0
## Precio escrito en su etiqueta; -1 si no tiene.
var price: int = -1


static func create(item_id: StringName, new_uid: int = 0) -> ItemState:
	var state: ItemState = ItemState.new()
	state.data = load_data(item_id)
	state.uid = new_uid
	return state


static func load_data(item_id: StringName) -> ItemData:
	var path: String = ITEMS_DIR + String(item_id) + ".tres"
	if not ResourceLoader.exists(path):
		push_error("No existe la ficha del objeto '%s'." % item_id)
		return null
	return load(path) as ItemData


static func from_dict(values: Dictionary) -> ItemState:
	var state: ItemState = create(StringName(str(values.get("id", ""))), int(values.get("uid", 0)))
	state.condition = clampf(float(values.get("condition", 1.0)), 0.0, 1.0)
	state.contamination = clampf(float(values.get("contamination", 0.0)), 0.0, 1.0)
	state.price = int(values.get("price", -1))
	return state


func to_dict() -> Dictionary:
	return {
		"id": String(data.id),
		"uid": uid,
		"condition": condition,
		"contamination": contamination,
		"price": price,
	}


## Lo que vale ahora mismo, sin regatear.
func value() -> int:
	return data.value(condition, contamination)
