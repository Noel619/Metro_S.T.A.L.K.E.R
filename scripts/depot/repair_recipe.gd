class_name RepairRecipe
extends Resource
## Cómo se repara un objeto en el banco de trabajo (F2-07): sus pasos en orden.
## Las recetas están en data/reparaciones/, con el nombre del objeto.

const DIR: String = "res://data/reparaciones/"

static var _cache: Dictionary = {}

@export var item_id: StringName = &""
@export var steps: Array[RepairStep] = []
## El estado con el que queda al terminar (menos lo que ya traía gastado).
@export_range(0.0, 1.0) var repaired_condition: float = 0.9


## La receta de [param item_id], si es reparable.
static func for_item(item_id: StringName) -> RepairRecipe:
	if not _cache.has(item_id):
		var path: String = DIR + String(item_id) + ".tres"
		_cache[item_id] = load(path) as RepairRecipe if ResourceLoader.exists(path) else null
	return _cache[item_id]


## El paso por el que va un objeto (o null si ya está reparado).
func step_of(state: ItemState) -> RepairStep:
	if bool(state.extra.get("reparado", false)):
		return null
	var index: int = int(state.extra.get("paso", 0))
	return steps[index] if index >= 0 and index < steps.size() else null
