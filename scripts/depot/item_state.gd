class_name ItemState
extends RefCounted
## Un ejemplar concreto de un objeto: esta lata, con su abolladura y su dosis.
##
## Todo lo que existe en el mundo tiene un identificador, se puede guardar y se
## puede replicar (README 13.1): por eso el estado viaja como diccionario.

const ITEMS_DIR: String = "res://data/items/"
## La clave de [member extra] con lo que pesa lo que lleva dentro.
const INSIDE_WEIGHT: String = "peso_dentro"

var data: ItemData
## Identificador único en la partida.
var uid: int = 0
## De 0 (roto) a 1 (como nuevo).
var condition: float = 1.0
## De 0 (limpio) a 1 (hay que apartarlo).
var contamination: float = 0.0
## Precio escrito en su etiqueta; -1 si no tiene.
var price: int = -1
## Metido en una bolsa de plástico: ya no contamina lo de alrededor.
var bagged: bool = false
## Lo propio de cada clase de objeto (lo que lleva un fajo, si una caja está
## abierta, los pasos de una reparación…): valores que se pueden guardar en JSON.
var extra: Dictionary = {}


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
	state.bagged = bool(values.get("bagged", false))
	var more: Variant = values.get("extra", {})
	state.extra = (more as Dictionary).duplicate(true) if more is Dictionary else {}
	return state


func to_dict() -> Dictionary:
	return {
		"id": String(data.id),
		"uid": uid,
		"condition": condition,
		"contamination": contamination,
		"price": price,
		"bagged": bagged,
		"extra": extra.duplicate(true),
	}


## Lo que vale ahora mismo, sin regatear.
func value() -> int:
	return data.value(condition, contamination)


## Lo que pesa, con lo que lleva dentro (una mochila llena pesa más que vacía):
## lo de dentro lo apunta el anfitrión al meter o sacar algo, en [constant INSIDE_WEIGHT].
func weight() -> float:
	if data == null:
		return 0.0
	return data.weight + float(extra.get(INSIDE_WEIGHT, 0.0))


## Cuánto contamina lo de alrededor: nada si está embolsado.
func emission() -> float:
	return 0.0 if bagged else contamination
