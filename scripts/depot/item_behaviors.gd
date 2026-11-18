class_name ItemBehaviors
extends RefCounted
## Lo que se puede hacer con cada objeto además de cogerlo (docs/DEPOSITO.md, 4):
## lo que acepta que se le haga con algo en la mano ([Workable]) y cómo se dibuja
## su estado ([ItemView]: la etiqueta colgando, la bolsa, la cifra de un fajo,
## las piezas de lo que se repara, la aguja del dosímetro).
##
## Se monta igual en todos los equipos al crear el objeto ([WorldItems]); lo que
## pasa al trabajarlo lo decide el anfitrión, que escucha
## [signal WorldItems.item_worked].

## Los trabajos que admite cualquier objeto: atarle una etiqueta, embolsarlo y
## cepillarlo (en la pila).
const COMMON: Array = [
	["Etiquetar", &"etiqueta", Workable.Gesture.HOLD],
	["Embolsar", &"bolsa", Workable.Gesture.HOLD],
	["Cepillar", &"cepillo", Workable.Gesture.SCRUB],
]


static func attach(items: WorldItems, body: RigidBody3D, item: Carryable) -> void:
	var data: ItemData = item.state.data
	for entry: Array in COMMON:
		_add(items, body, item, entry[0], [entry[1]], entry[2])
	if data.nutrition > 0.0:
		_add(items, body, item, "Comer", [&"comida"], Workable.Gesture.HOLD).self_use = true
	if item.state.extra.has("contenido"):
		_add(items, body, item, "Abrir", [Workable.HANDS], Workable.Gesture.PULL)
	var recipe: RepairRecipe = RepairRecipe.for_item(data.id)
	if recipe != null:
		var repair: Workable = _add(items, body, item, "Reparar", [], Workable.Gesture.STROKE)
		var update: Callable = func() -> void: _update_repair(repair, recipe, item.state)
		item.state_changed.connect(update)
		update.call()
	# Lo pesado que cae levanta polvo (lo que pesa poco no se nota).
	item.landed.connect(
		func(speed: float) -> void:
			var amount: float = clampf(item.state.data.weight / 6.0 + speed / 6.0, 0.0, 1.2)
			if amount > 0.35:
				items.puff.rpc(item.body().global_position, amount)
	)
	var view: ItemView = ItemView.new()
	view.name = "Vista"
	view.item = item
	view.items = items
	body.get_node(^"Visual").add_child(view)


static func _add(
	items: WorldItems,
	body: RigidBody3D,
	item: Carryable,
	workable_name: String,
	tools: Array,
	gesture: Workable.Gesture
) -> Workable:
	var workable: Workable = Workable.new()
	workable.name = workable_name
	for tool: Variant in tools:
		workable.tools.append(StringName(tool))
	workable.gesture = gesture
	body.add_child(workable)
	workable.worked.connect(
		func(player: Node, tool: StringName, amount: float, point: Vector3) -> void:
			items.item_worked.emit(item, player, tool, amount, point)
	)
	return workable


## El paso de la reparación decide con qué y cómo se trabaja ahora.
static func _update_repair(repair: Workable, recipe: RepairRecipe, state: ItemState) -> void:
	var step: RepairStep = recipe.step_of(state)
	repair.tools.clear()
	repair.enabled = step != null
	if step != null:
		repair.tools.append(step.tool)
		repair.gesture = step.gesture
