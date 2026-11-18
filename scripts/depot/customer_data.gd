class_name CustomerData
extends Resource
## Un cliente de la consigna (F2-09): quién es, cómo se le ve, qué busca, qué
## vende y el encargo que deja. Los clientes están en data/clientes/.

const DIR: String = "res://data/clientes/"

@export var id: StringName = &""
## Cómo firma sus papeles.
@export var signature: String = ""
@export_enum("chico", "chica") var variant: String = "chico"
@export var cloth_color: Color = Color("#6e6a5f")
## Lo que lleva encima para distinguirlo: "gorra", "gafas", "panuelo" (varios,
## separados por comas).
@export var accessories: String = ""
## Lo que busca: categorías ([enum ItemData.Category]) y objetos concretos.
@export var wants_categories: Array[int] = []
@export var wants_items: Array[StringName] = []
## Lo que paga por encima (o por debajo) de lo que vale algo.
@export_range(0.3, 2.0, 0.05) var buy_factor: float = 1.0
## Lo que trae para vender (uno al azar) y lo que pide por encima de su valor.
@export var sells: Array[StringName] = []
@export_range(0.5, 2.0, 0.05) var sell_factor: float = 1.15
## El papelito que deja al llegar a comprar o a vender (con su letra).
@export_multiline var buy_note: String = ""
@export_multiline var sell_note: String = ""
## El encargo que deja si no encuentra lo que busca: qué, cuánto paga, en
## cuántos días y la pista.
@export var job_item: StringName = &""
@export var job_text: String = ""
@export var job_pay: int = 0
@export var job_days: int = 3
@export_multiline var job_hint: String = ""


static func by_id(customer_id: StringName) -> CustomerData:
	var path: String = DIR + String(customer_id) + ".tres"
	return load(path) as CustomerData if ResourceLoader.exists(path) else null


## ¿Busca esto?
func wants(data: ItemData) -> bool:
	return wants_items.has(data.id) or wants_categories.has(int(data.category))
