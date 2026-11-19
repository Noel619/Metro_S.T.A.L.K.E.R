class_name PlayerGear
extends Node
## Lo que un jugador lleva encima sin tenerlo en las manos (F3-03): la mochila
## puesta y los tres huecos del cinturón.
##
## Cuelga del jugador, pero manda el anfitrión: es quien quita las cosas del
## mundo al ponérselas y las vuelve a crear al quitárselas, igual que al meter
## algo en la mochila ([D-063](docs/DECISIONES.md)). Lo que lleva cada uno se
## replica a todos, también a quien llega tarde.
##
## - La tecla de la mochila (I): con la mochila en las manos, o mirándola, se la
##   pone a la espalda (si estaba abierta, la cierra). Puesta, se la quita y la
##   deja en el suelo delante, cerrada. Abrirla es mantener las manos sobre ella,
##   y fuera eso es lento ([constant Backpack.TOGGLE_WORK_OUTSIDE]).
## - Las del cinturón (1, 2 y 3): con algo pequeño en la mano, lo cuelga de ese
##   hueco (si ya había algo, se cambian); con las manos vacías, lo saca.
## - Lo que se lleva puesto pesa y suena: frena (la mochila, la mitad que en las
##   manos), gasta aliento y lo suelto de la mochila hace ruido al andar.

const NODE_NAME: StringName = &"Equipo"
const BELT_SLOTS: int = 3
## Lo que cabe en un hueco del cinturón: hasta tres casillas en fila y este peso.
const BELT_CELLS: int = 3
const BELT_WEIGHT: float = 2.5
## A la espalda, el peso frena la mitad que en las manos.
const WORN_SLOWDOWN: float = 0.5
## Dónde se deja la mochila al quitársela: delante, a esta distancia, y lo que
## se separa de una pared si la hay.
const DROP_DISTANCE: float = 0.7
const WALL_GAP: float = 0.3
const MASK_FLOOR: int = 1 << 0

## La mochila puesta ([method ItemState.to_dict]) o vacío.
var backpack: Dictionary = {}
## Lo que cuelga de cada hueco del cinturón ([method ItemState.to_dict]) o vacío.
var belt: Array = [{}, {}, {}]
var player: Player


## El equipo de [param who], si lo tiene.
static func of(who: Node) -> PlayerGear:
	if who == null:
		return null
	return who.get_node_or_null(NodePath(NODE_NAME)) as PlayerGear


## ¿Cabe [param data] en un hueco del cinturón?
static func fits_belt(data: ItemData) -> bool:
	if data == null or data.weight > BELT_WEIGHT:
		return false
	var size: Vector2i = data.grid_size()
	return mini(size.x, size.y) <= 1 and maxi(size.x, size.y) <= BELT_CELLS


## Lo crea y lo cuelga de [param owner_player], con su sincronizador. Va después
## de dar al jugador su autoridad: la de este nodo es del anfitrión.
static func attach(owner_player: Player) -> PlayerGear:
	var gear: PlayerGear = PlayerGear.new()
	gear.name = NODE_NAME
	gear.player = owner_player
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	for property: String in [".:backpack", ".:belt"]:
		var path: NodePath = NodePath(property)
		config.add_property(path)
		config.property_set_spawn(path, true)
		config.property_set_replication_mode(
			path, SceneReplicationConfig.REPLICATION_MODE_ON_CHANGE
		)
	var sync: MultiplayerSynchronizer = MultiplayerSynchronizer.new()
	sync.name = "EquipoSync"
	sync.replication_config = config
	gear.add_child(sync)
	owner_player.add_child(gear)
	gear.set_multiplayer_authority(Carryable.HOST_PEER)
	return gear


func wearing() -> bool:
	return not backpack.is_empty()


## La mochila puesta, o null.
func backpack_state() -> ItemState:
	return ItemState.from_dict(backpack) if wearing() else null


## Lo que cuelga del hueco [param slot] del cinturón, o null.
func belt_state(slot: int) -> ItemState:
	if slot < 0 or slot >= BELT_SLOTS or (belt[slot] as Dictionary).is_empty():
		return null
	return ItemState.from_dict(belt[slot])


## Lo que pesa todo lo que lleva puesto (kg): la mochila con lo de dentro y el cinturón.
func weight() -> float:
	var total: float = 0.0
	var worn: ItemState = backpack_state()
	if worn != null:
		total += worn.weight()
	for slot: int in BELT_SLOTS:
		var hung: ItemState = belt_state(slot)
		if hung != null:
			total += hung.weight()
	return total


## Lo que suena suelto en la mochila puesta ([method BackpackGrid.rattle]).
func rattle() -> float:
	if not wearing():
		return 0.0
	return BackpackGrid.from_extra(backpack.get("extra", {})).rattle()


## Pide al anfitrión ponerse o quitarse la mochila: [param uid] es la que se
## lleva en las manos o se mira (0 para quitársela).
@rpc("any_peer", "call_local", "reliable")
func request_backpack(uid: int) -> void:
	if not _allowed():
		return
	var items: WorldItems = _items()
	if items == null:
		return
	if wearing():
		_take_off(items)
		return
	var target: Carryable = items.find_item(uid)
	if target == null or target.state.data.id != &"mochila":
		return
	if target.is_held() and target.holder_peer != player.peer_id:
		return
	if player.eye_position().distance_to(target.body().global_position) > Carryable.GRAB_RANGE:
		return
	var worn: Dictionary = target.state.to_dict()
	var extra: Dictionary = (worn.get("extra", {}) as Dictionary).duplicate(true)
	extra.erase(Backpack.OPEN_KEY)
	worn["extra"] = extra
	items.remove_item(target)
	backpack = worn


## Pide al anfitrión usar el hueco [param slot] del cinturón: colgar lo que se
## lleva en la mano (cambiándolo por lo que hubiera) o sacar lo que hay.
@rpc("any_peer", "call_local", "reliable")
func request_belt(slot: int) -> void:
	if not _allowed() or slot < 0 or slot >= BELT_SLOTS:
		return
	var items: WorldItems = _items()
	if items == null:
		return
	var held: Carryable = player.held_item()
	var hung: ItemState = belt_state(slot)
	if held != null:
		if not fits_belt(held.state.data):
			return
		var stored: Dictionary = held.state.to_dict()
		items.remove_item(held)
		_set_belt(slot, stored)
		if hung != null:
			items.give_state(player, hung)
	elif hung != null:
		_set_belt(slot, {})
		items.give_state(player, hung)


## Deja en el mundo todo lo que lleva puesto, a sus pies (al dormir o al irse de
## la partida). Solo el anfitrión.
func unload() -> void:
	var items: WorldItems = _items()
	if not multiplayer.is_server() or items == null:
		return
	if wearing():
		_take_off(items)
	# Lo del cinturón, a los lados de la mochila y el del medio, más cerca.
	var base: Vector3 = _drop_spot()
	var spots: Array[Vector3] = [
		Vector3(-0.45, 0.15, 0.0), Vector3(0.0, 0.15, 0.4), Vector3(0.45, 0.15, 0.0)
	]
	for slot: int in BELT_SLOTS:
		var hung: ItemState = belt_state(slot)
		if hung == null:
			continue
		_set_belt(slot, {})
		var where: Vector3 = base + player.global_basis * spots[slot]
		items.spawn_state(hung, Transform3D(player.global_basis, where))


## Lo olvida todo sin dejarlo en ningún sitio (al perder la partida). Solo el anfitrión.
func clear() -> void:
	if not multiplayer.is_server():
		return
	backpack = {}
	belt = [{}, {}, {}]


## Se quita la mochila y la deja en el suelo, delante, cerrada.
func _take_off(items: WorldItems) -> void:
	var state: ItemState = ItemState.from_dict(backpack)
	backpack = {}
	var facing: Basis = Basis(Vector3.UP, player.global_rotation.y + PI)
	items.spawn_state(state, Transform3D(facing, _drop_spot()))


## Un sitio en el suelo, delante del jugador (sin meterlo en una pared).
func _drop_spot() -> Vector3:
	var space: PhysicsDirectSpaceState3D = player.get_world_3d().direct_space_state
	var forward: Vector3 = -player.global_basis.z
	var chest: Vector3 = player.global_position + Vector3.UP * 0.9
	var reach: float = DROP_DISTANCE
	var ahead: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		chest, chest + forward * (DROP_DISTANCE + WALL_GAP), MASK_FLOOR, [player.get_rid()]
	)
	var wall: Dictionary = space.intersect_ray(ahead)
	if not wall.is_empty():
		reach = maxf(0.0, chest.distance_to(wall["position"]) - WALL_GAP)
	var above: Vector3 = chest + forward * reach
	var down: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		above, above + Vector3.DOWN * 3.0, MASK_FLOOR, [player.get_rid()]
	)
	var floor_hit: Dictionary = space.intersect_ray(down)
	if floor_hit.is_empty():
		return player.global_position + forward * reach + Vector3.UP * 0.05
	return (floor_hit["position"] as Vector3) + Vector3.UP * 0.01


func _set_belt(slot: int, value: Dictionary) -> void:
	var changed: Array = belt.duplicate(true)
	changed[slot] = value
	belt = changed


## ¿Lo pide el propio jugador, al anfitrión?
func _allowed() -> bool:
	if not multiplayer.is_server() or player == null:
		return false
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	return sender == player.peer_id


func _items() -> WorldItems:
	return get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
