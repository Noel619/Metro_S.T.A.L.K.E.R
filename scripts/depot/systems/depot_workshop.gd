class_name DepotWorkshop
extends Node3D
## Procesar lo que llega (F2-06, F2-07, F2-08): la pila de descontaminación, el
## cepillo y las bolsas; el banco de trabajo con sus reparaciones; la báscula, las
## etiquetas de precio y lo que se cambia con la rueda (el precio de una etiqueta,
## los billetes de un fajo). Y comer lo que se lleva en la mano.
##
## En todos los equipos monta las cosas fijas; las reglas son del anfitrión.

## Lo que quita el cepillo por cada frotada (gesto SCRUB), en la pila.
const BRUSH_RATE: float = 0.07
## Lo que hay que mantener el botón para atar una etiqueta, embolsar o comer.
const TAG_HOLD: float = 0.6
const BAG_HOLD: float = 0.8
const EAT_HOLD: float = 1.5
## Dosis que suma estar junto a algo que marca 1 en el dosímetro, por segundo.
const DOSE_RATE: float = 0.01
const MAX_PRICE: int = 9999
## Lo que se aparta del tapete del banco lo que se repara (metros).
const BENCH_REACH: float = 0.75

var room: DepotRoom
var items: WorldItems
var world: DepotWorld

var sink: SinkFixture
var scale_fixture: ScaleFixture
var tag_box: GiverFixture
var bag_roll: GiverFixture
var _hold: Dictionary = {}


func _ready() -> void:
	sink = SinkFixture.new()
	sink.fixture_id = "pila"
	sink.name = "Pila"
	sink.model = room.fixed("Pila")
	add_child(sink)
	scale_fixture = ScaleFixture.new()
	scale_fixture.name = "Bascula"
	scale_fixture.model = room.fixed("Bascula")
	add_child(scale_fixture)
	tag_box = _giver("caja_etiquetas", "CajaEtiquetas", &"etiqueta", {"precio": 10})
	bag_roll = _giver("rollo_bolsas", "RolloBolsas", &"bolsa_plastico", {})
	items.item_worked.connect(_on_item_worked)
	EventBus.item_adjusted.connect(_on_item_adjusted)


func _giver(id: String, model_name: String, item_id: StringName, extra: Dictionary) -> GiverFixture:
	var giver: GiverFixture = GiverFixture.new()
	giver.fixture_id = id
	giver.name = model_name
	giver.model = room.fixed(model_name)
	giver.item_id = item_id
	giver.extra = extra
	add_child(giver)
	return giver


func _process(delta: float) -> void:
	if not multiplayer.is_server() or not GameState.clock_running:
		return
	# Lo contaminado que se tiene cerca suma dosis (F2-06: solo se acumula).
	var total: float = 0.0
	for player: Node in get_tree().get_nodes_in_group(Player.GROUP):
		total += ItemView.radiation_at(
			items, (player as Player).eye_position() - Vector3(0, 0.6, 0)
		)
	if total > 0.0:
		GameState.add_dose(total * DOSE_RATE * delta)


func _on_item_worked(
	item: Carryable, player: Node, tool: StringName, amount: float, _point: Vector3
) -> void:
	var who: Player = player as Player
	if who == null:
		return
	match tool:
		&"cepillo":
			brush(item, amount)
		&"bolsa":
			if _held_long(who, item, amount, BAG_HOLD):
				bag(item, who)
		&"etiqueta":
			if _held_long(who, item, amount, TAG_HOLD):
				tie_tag(item, who)
		&"comida":
			if item == who.held_item() and _held_long(who, item, amount, EAT_HOLD):
				eat(item, who)
	var recipe: RepairRecipe = RepairRecipe.for_item(item.state.data.id)
	if recipe != null:
		repair(item, recipe, tool, amount)


## Lo que se mantiene pulsado se cuenta por jugador y por objeto.
func _held_long(player: Player, item: Carryable, amount: float, needed: float) -> bool:
	var key: String = "%d_%d" % [player.peer_id, item.state.uid]
	var held: float = float(_hold.get(key, 0.0)) + amount
	if held < needed:
		_hold[key] = held
		return false
	_hold.erase(key)
	return true


## Frotar con el cepillo algo que está en la pila (con el agua corriendo o no).
func brush(item: Carryable, amount: float) -> void:
	if amount <= 0.0 or item.state.contamination <= 0.0 or not sink.holds(item):
		return
	var left: float = maxf(0.0, item.state.contamination - amount * BRUSH_RATE)
	item.set_values({"contamination": left})
	DustPuff.burst(
		self, item.body().global_position + Vector3(0, 0.1, 0), 0.3, Color(0.8, 0.85, 0.9)
	)


## Embolsar: la bolsa que se lleva envuelve el objeto y se gasta.
func bag(item: Carryable, player: Player) -> void:
	if item.state.bagged or item == player.held_item():
		return
	items.remove_item(player.held_item())
	item.set_values({"bagged": true})


## Atar la etiqueta que se lleva: el objeto pasa a tener su precio.
func tie_tag(item: Carryable, player: Player) -> void:
	var tag: Carryable = player.held_item()
	if tag == null or tag == item or item.state.data.tool == &"etiqueta":
		return
	var price: int = int(tag.state.extra.get("precio", 0))
	if price <= 0:
		return
	items.remove_item(tag)
	item.set_values({"price": price})


func eat(item: Carryable, player: Player) -> void:
	GameState.eat(item.state.data.nutrition)
	items.remove_item(item)
	DustPuff.burst(self, player.eye_position() - Vector3(0, 0.3, 0), 0.2, Color(0.85, 0.8, 0.7))


## Un paso de reparación: solo en el banco y con lo que pide el paso.
func repair(item: Carryable, recipe: RepairRecipe, tool: StringName, amount: float) -> void:
	var step: RepairStep = recipe.step_of(item.state)
	if step == null or step.tool != tool or not on_bench(item):
		return
	var work: float = amount
	if step.gesture == Workable.Gesture.CIRCLE and step.direction != 0:
		work = amount * step.direction
	if work <= 0.0:
		return
	var extra: Dictionary = item.state.extra.duplicate(true)
	var progress: float = float(extra.get("avance", 0.0)) + work
	var values: Dictionary = {}
	if progress >= step.work:
		var next: int = int(extra.get("paso", 0)) + 1
		extra["paso"] = next
		extra["avance"] = 0.0
		if next >= recipe.steps.size():
			extra["reparado"] = true
			var wear: float = float(extra.get("desgaste", 0.0))
			values["condition"] = maxf(item.state.condition, recipe.repaired_condition - wear)
	else:
		extra["avance"] = progress
	values["extra"] = extra
	item.set_values(values)


## ¿Está [param item] sobre el tapete del banco de trabajo?
func on_bench(item: Carryable) -> bool:
	if item.is_held():
		return false
	var where: Vector3 = item.body().global_position
	var mat: Vector3 = DepotRoom.BENCH_MAT
	return (
		Vector2(where.x - mat.x, where.z - mat.z).length() < BENCH_REACH
		and where.y > DepotRoom.BENCH_TOP - 0.05
		and where.y < DepotRoom.BENCH_TOP + 0.6
	)


## La rueda con una etiqueta o un fajo en la mano.
func _on_item_adjusted(_player: Node, item: Node, step: int) -> void:
	var held: Carryable = item as Carryable
	if held == null or not is_instance_valid(held):
		return
	var tool: StringName = held.state.data.tool
	var extra: Dictionary = held.state.extra.duplicate(true)
	if tool == &"etiqueta":
		var price: int = int(extra.get("precio", 0))
		extra["precio"] = clampi(price + step * price_step(price, step), 1, MAX_PRICE)
		held.set_values({"extra": extra})
	elif tool == &"billetes":
		var amount: int = int(extra.get("rublos", 0))
		var change: int = step * price_step(amount, step)
		# Lo que se añade sale de la caja; lo que se quita, vuelve a ella.
		if change > 0:
			change = mini(change, GameState.rubles)
		else:
			change = maxi(change, 1 - amount)
		if change == 0:
			return
		GameState.add_rubles(-change)
		extra["rublos"] = amount + change
		held.set_values({"extra": extra})


## De cuánto en cuánto cambia la rueda: de uno en uno hasta 20, de cinco hasta
## 100 y de diez en adelante.
static func price_step(amount: int, step: int) -> int:
	var basis: int = amount if step > 0 else amount - 1
	if basis < 20:
		return 1
	if basis < 100:
		return 5
	return 10
