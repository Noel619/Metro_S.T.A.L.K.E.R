class_name Wounds
extends Node
## Las heridas (F3-12, docs/SUPERFICIE.md 8). Lo decide el anfitrión: un mordisco
## quita sangre de golpe y abre una herida que sangra mientras no se vende; la
## sangre que se pierde gotea (se ve en la nieve y los perros la huelen) y, sin
## sangre, se muere. Vendarse (las vendas o el botiquín en la mano, mantener el
## botón izquierdo) corta la hemorragia. La sangre se recupera durmiendo.
##
## Cada equipo dibuja las gotas de los que sangran (con lo que se replica).

const GROUP: StringName = &"heridas"
## Un mordisco: la sangre que quita de golpe y lo que sangra la herida (por segundo:
## sola, unos cuatro minutos hasta vaciarse).
const BITE_LOSS: float = 0.15
const BITE_BLEEDING: float = 0.0035
## Cada cuánto gotea quien sangra.
const DROP_SECONDS: float = 0.8
## Segundos que hay que mantener el botón para vendarse.
const BANDAGE_SECONDS: float = 3.0
## Lo que cura del todo y lo que vende de una vez el botiquín.
const KIT_TOOL: StringName = &"botiquin"
const BANDAGE_TOOL: StringName = &"vendas"
const SYNC_SECONDS: float = 1.0
## Lo que se oye el grito de quien muerden.
const SCREAM_RADIUS: float = 30.0

## Lo que lleva vendándose cada jugador (en el anfitrión): peer -> segundos.
var _bandaging: Dictionary = {}
var _drop_clock: float = 0.0
var _sync_clock: float = 0.0


static func find(tree: SceneTree) -> Wounds:
	return tree.get_first_node_in_group(GROUP) as Wounds


func _ready() -> void:
	add_to_group(GROUP)
	var items: WorldItems = get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
	if items != null:
		items.item_worked.connect(_on_item_worked)


func _process(delta: float) -> void:
	_drop_clock += delta
	var drip: bool = _drop_clock >= DROP_SECONDS
	if drip:
		_drop_clock = 0.0
	if multiplayer.is_server():
		_bleed(delta)
	if drip:
		_drip()


## Un mordisco a [param player] desde [param from]. Solo el anfitrión.
func bite(player: Player, from: Vector3) -> void:
	if not multiplayer.is_server() or player.condition.dead:
		return
	var condition: PlayerCondition = player.condition
	condition.wounds.append({"clase": "mordedura", "sangrado": BITE_BLEEDING})
	condition.blood -= BITE_LOSS
	condition.notify_hurt.rpc_id(player.peer_id, from)
	# El grito se oye.
	var stimuli: Stimuli = Stimuli.find(get_tree())
	if stimuli != null:
		stimuli.make_noise(player.eye_position(), SCREAM_RADIUS, &"grito", player.peer_id)
	_check(player)


## Corta la hemorragia de la peor herida (las vendas) o de todas (el botiquín).
func bandage(player: Player, all: bool = false) -> void:
	if not multiplayer.is_server():
		return
	var condition: PlayerCondition = player.condition
	if condition.wounds.is_empty():
		return
	if all:
		condition.wounds.clear()
	else:
		var worst: int = 0
		for index: int in condition.wounds.size():
			if (
				float(condition.wounds[index]["sangrado"])
				> float(condition.wounds[worst]["sangrado"])
			):
				worst = index
		condition.wounds.remove_at(worst)
	_check(player)


## Mata a [param player]. Solo el anfitrión.
func kill(player: Player) -> void:
	if not multiplayer.is_server():
		return
	player.condition.wounds.clear()
	player.condition.blood = 0.0
	player.condition.set_state.rpc(0.0, false, true)
	# El cuaderno se pierde contigo.
	GameState.lose_notebook(player.slot)
	EventBus.player_died.emit(player.peer_id)
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		if not (node as Player).condition.dead:
			return
	EventBus.game_over.emit()


func _bleed(delta: float) -> void:
	_sync_clock += delta
	var send: bool = _sync_clock >= SYNC_SECONDS
	if send:
		_sync_clock = 0.0
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		var player: Player = node as Player
		var condition: PlayerCondition = player.condition
		if condition.dead or condition.wounds.is_empty():
			continue
		var rate: float = 0.0
		for wound: Dictionary in condition.wounds:
			rate += float(wound["sangrado"])
		condition.blood -= rate * delta
		if condition.blood <= 0.0:
			kill(player)
		elif send:
			condition.set_state.rpc(condition.blood, true, false)


func _check(player: Player) -> void:
	var condition: PlayerCondition = player.condition
	if condition.blood <= 0.0:
		kill(player)
		return
	condition.set_state.rpc(condition.blood, not condition.wounds.is_empty(), false)


## Las gotas de los que sangran: en la nieve (todos los equipos) y su olor (el anfitrión).
func _drip() -> void:
	var tracks: Tracks = Tracks.find(get_tree())
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		var player: Player = node as Player
		if not player.condition.bleeding or player.condition.dead:
			continue
		var feet: Vector3 = player.global_position
		if tracks != null:
			tracks.drop(feet, player.peer_id, true)
			tracks.print_blood(feet + Vector3(randf_range(-0.2, 0.2), 0.0, randf_range(-0.2, 0.2)))


func _on_item_worked(
	item: Carryable, player: Node, tool: StringName, amount: float, _point: Vector3
) -> void:
	if tool != BANDAGE_TOOL and tool != KIT_TOOL:
		return
	var who: Player = player as Player
	if who == null or who.held_item() != item:
		return
	var done: float = float(_bandaging.get(who.peer_id, 0.0)) + amount
	if done < BANDAGE_SECONDS:
		_bandaging[who.peer_id] = done
		return
	_bandaging.erase(who.peer_id)
	if who.condition.wounds.is_empty():
		return
	bandage(who, tool == KIT_TOOL)
	var items: WorldItems = get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
	if items != null:
		items.remove_item(item)
