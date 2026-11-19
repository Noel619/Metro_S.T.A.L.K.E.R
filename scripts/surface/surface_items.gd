class_name SurfaceItems
extends Node
## Lo que hacen las cosas sueltas en la superficie (F3-07, docs/SUPERFICIE.md 4.4), en
## el anfitrión:
## - Al caer, suenan según lo que son y dónde caen (una lata en el granito, una botella
##   que se rompe, un trapo que no se oye): la IA lo oye y todos ven las ondas.
## - El despertador: se le da cuerda (círculos con él en la mano: cada vuelta, un
##   minuto de juego) y, cuando se acaba, suena un rato donde esté.

## Los cristales: con este golpe se rompen (y se oyen de lejos).
const GLASS: Array[StringName] = [
	&"botella_marron", &"botella_verde", &"bombilla", &"bombilla_fundida"
]
const BREAK_SPEED: float = 3.0
const BROKEN: Dictionary = {&"botella_marron": &"botella_rota", &"botella_verde": &"botella_rota"}
## Lo blando apenas suena; la comida, poco; el metal, según el golpe.
const SOFT: Array[ItemData.Category] = [ItemData.Category.ROPA]
const METAL: Array[ItemData.Category] = [
	ItemData.Category.HERRAMIENTAS,
	ItemData.Category.ENVASES,
	ItemData.Category.CHATARRA,
	ItemData.Category.ELECTRONICA,
]
## La nieve amortigua.
const SNOW_DAMPING: float = 0.6
## El despertador: segundos reales por vuelta de cuerda (un minuto de juego), lo más que
## se le da y lo que suena.
const WIND_SECONDS_PER_TURN: float = 1.0 / GameState.MINUTES_PER_SECOND
const WIND_MAX_SECONDS: float = 600.0
const RING_SECONDS: float = 30.0
const RING_EVERY: float = 1.0
const ALARM_TOOL: StringName = &"despertador"
## El podómetro se pone a cero manteniendo el botón este rato.
const PEDOMETER_TOOL: StringName = &"podometro"
const RESET_SECONDS: float = 1.0

var items: WorldItems

var _ring_clock: float = 0.0
## Lo que lleva cada uno manteniendo el botón del podómetro: uid -> segundos.
var _resetting: Dictionary = {}


func setup(world_items: WorldItems) -> void:
	items = world_items
	name = "CosasSueltas"
	items.item_landed.connect(_on_landed)
	items.item_worked.connect(_on_worked)


func _process(delta: float) -> void:
	if not multiplayer.is_server() or items == null:
		return
	_ring_clock += delta
	if _ring_clock < RING_EVERY:
		return
	var step: float = _ring_clock
	_ring_clock = 0.0
	for item: Carryable in items.items():
		if item.state.data.tool == ALARM_TOOL:
			_tick_alarm(item, step)


## El ruido de [param item] al caer a [param speed] m/s sobre [param ground]:
## {"radius", "kind", "breaks"}.
static func landing_noise(data: ItemData, speed: float, ground: StringName) -> Dictionary:
	var radius: float = 4.0 + speed
	var kind: StringName = &"golpe"
	var breaks: bool = false
	if GLASS.has(data.id):
		breaks = speed >= BREAK_SPEED
		radius = NoiseRules.sound_radius(&"cristal") if breaks else 6.0 + speed
		kind = &"cristal" if breaks else &"golpe"
	elif SOFT.has(data.category) or data.id == &"trapo" or data.id == &"papeles":
		radius = 1.5
	elif data.category == ItemData.Category.COMIDA and data.id != &"lata_conserva":
		radius = 3.0
	elif METAL.has(data.category) or data.id == &"lata_conserva":
		radius = clampf(4.0 + speed * 2.2, 4.0, 22.0)
	if ground == NoiseRules.DEFAULT_GROUND and not breaks:
		radius *= SNOW_DAMPING
	return {"radius": radius, "kind": kind, "breaks": breaks}


func _on_landed(item: Carryable, speed: float) -> void:
	if not multiplayer.is_server():
		return
	var body: RigidBody3D = item.body()
	var space: PhysicsDirectSpaceState3D = body.get_world_3d().direct_space_state
	var hit: Dictionary = Ground.below(space, body.global_position, 0.6, [body.get_rid()])
	var ground: StringName = Ground.material_of(space, hit) if not hit.is_empty() else &"granito"
	var noise: Dictionary = landing_noise(item.state.data, speed, ground)
	var stimuli: Stimuli = Stimuli.find(get_tree())
	if stimuli != null:
		stimuli.make_noise(body.global_position, float(noise["radius"]), noise["kind"])
	if noise["breaks"] and BROKEN.has(item.state.data.id):
		var where: Transform3D = body.global_transform
		items.remove_item(item)
		items.spawn_item(BROKEN[item.state.data.id], where)


func _on_worked(
	item: Carryable, player: Node, tool: StringName, amount: float, _point: Vector3
) -> void:
	var who: Player = player as Player
	if who == null or who.held_item() != item:
		return
	if tool == PEDOMETER_TOOL:
		_reset_pedometer(item, who, amount)
		return
	if tool != ALARM_TOOL:
		return
	var extra: Dictionary = item.state.extra.duplicate(true)
	var wound: float = float(extra.get("cuerda", 0.0)) + absf(amount) * WIND_SECONDS_PER_TURN
	extra["cuerda"] = minf(wound, WIND_MAX_SECONDS)
	extra.erase("sonando")
	item.set_values({"extra": extra})


## Un segundo de un despertador: se le acaba la cuerda y suena, o suena y se calla.
func _tick_alarm(item: Carryable, step: float) -> void:
	var extra: Dictionary = item.state.extra.duplicate(true)
	if extra.has("sonando"):
		var stimuli: Stimuli = Stimuli.find(get_tree())
		if stimuli != null:
			var where: Vector3 = item.body().global_position
			stimuli.make_noise(where, NoiseRules.sound_radius(ALARM_TOOL), ALARM_TOOL)
		var left: float = float(extra["sonando"]) - step
		if left <= 0.0:
			extra.erase("sonando")
		else:
			extra["sonando"] = left
	elif float(extra.get("cuerda", 0.0)) > 0.0:
		var wound: float = float(extra["cuerda"]) - step
		if wound <= 0.0:
			extra.erase("cuerda")
			extra["sonando"] = RING_SECONDS
		else:
			extra["cuerda"] = wound
	else:
		return
	item.set_values({"extra": extra})


func _reset_pedometer(item: Carryable, who: Player, amount: float) -> void:
	var held: float = float(_resetting.get(item.state.uid, 0.0)) + amount
	if held < RESET_SECONDS:
		_resetting[item.state.uid] = held
		return
	_resetting.erase(item.state.uid)
	var extra: Dictionary = item.state.extra.duplicate(true)
	extra["base"] = who.footsteps.steps
	extra["marca"] = 0
	item.set_values({"extra": extra})
