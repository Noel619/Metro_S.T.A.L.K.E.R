class_name PlayerPack
extends Node
## La mochila y el cinturón de un jugador (F3-03, docs/SUPERFICIE.md 4.1): guardar
## lo que se lleva en las manos, sacarlo, y los tres huecos del cinturón (1, 2, 3).
## Lo decide el anfitrión, que guarda la mochila en el estado de la partida
## ([method GameState.set_pack]); cada equipo la ve desde ahí.
##
## En la superficie, guardar y abrir la mochila es arrodillarse y quitársela: lleva
## su tiempo ([constant STORE_SECONDS], [constant OPEN_SECONDS]) y mientras tanto se
## está agachado y quieto. En el depósito se hace con calma, sin esperas.

## Ha cambiado lo que hay (en todos los equipos).
signal changed

const STORE_SECONDS: float = 1.0
const OPEN_SECONDS: float = 1.5
const BELT_SECONDS: float = 0.35

var player: Player
## Ocupado arrodillado (guardando o abriendo): de 0 a 1 lo que lleva; negativo, nada.
var busy: float = -1.0

var _busy_seconds: float = 0.0
var _then: Callable = Callable()


func setup(owner_player: Player) -> void:
	player = owner_player
	name = "Mochila"
	GameState.changed.connect(func() -> void: changed.emit())


## La mochila de este jugador ahora (una copia).
func contents() -> Backpack:
	return GameState.pack(player.slot)


## Lo que pesa (la mochila y el cinturón).
func weight() -> float:
	return contents().weight()


func _process(delta: float) -> void:
	if busy < 0.0:
		return
	busy += delta / maxf(_busy_seconds, 0.01)
	if busy >= 1.0:
		busy = -1.0
		if _then.is_valid():
			_then.call()
		_then = Callable()


## Está arrodillado con la mochila (no se mueve).
func is_busy() -> bool:
	return busy >= 0.0


## Guarda lo que lleva en la mano (en la superficie, tras arrodillarse).
func store_held() -> void:
	if player.held_item() == null or is_busy():
		return
	after_kneeling(STORE_SECONDS, func() -> void: request_store.rpc_id(Carryable.HOST_PEER))


## Saca lo que hay en la casilla [param index] de la mochila a las manos.
func take(index: int) -> void:
	if player.held_item() != null:
		return
	request_take.rpc_id(Carryable.HOST_PEER, index)


## La tecla de un hueco del cinturón: si las manos están vacías, saca lo que hay;
## si llevan algo pequeño, lo guarda ahí.
func belt_key(slot: int) -> void:
	if is_busy():
		return
	if player.held_item() == null:
		after_kneeling(
			BELT_SECONDS, func() -> void: request_belt_take.rpc_id(Carryable.HOST_PEER, slot)
		)
	else:
		after_kneeling(
			BELT_SECONDS, func() -> void: request_belt_store.rpc_id(Carryable.HOST_PEER, slot)
		)


## Mueve dentro de la mochila lo de [param index] a [param cell] (girado o no).
func arrange(index: int, cell: Vector2i, rotated: bool) -> void:
	request_move.rpc_id(Carryable.HOST_PEER, index, cell, rotated)


## Hace [param then] tras arrodillarse [param seconds] (en el depósito, enseguida).
func after_kneeling(seconds: float, then: Callable) -> void:
	if not player.surface_rules:
		then.call()
		return
	_busy_seconds = seconds
	busy = 0.0
	_then = then


# -- En el anfitrión ---------------------------------------------------------------

@rpc("any_peer", "call_local", "reliable")
func request_store() -> void:
	if not _from_owner():
		return
	var held: Carryable = player.held_item()
	if held == null:
		return
	var pack: Backpack = contents()
	if not pack.auto_place(held.state):
		return
	GameState.set_pack(player.slot, pack)
	_world_items().remove_item(held)


@rpc("any_peer", "call_local", "reliable")
func request_take(index: int) -> void:
	if not _from_owner() or player.held_item() != null:
		return
	var pack: Backpack = contents()
	var state: ItemState = pack.take(index)
	if state == null:
		return
	state.uid = 0
	GameState.set_pack(player.slot, pack)
	_world_items().give_state(player, state)


@rpc("any_peer", "call_local", "reliable")
func request_belt_store(slot: int) -> void:
	if not _from_owner():
		return
	var held: Carryable = player.held_item()
	if held == null:
		return
	var pack: Backpack = contents()
	if not pack.put_on_belt(held.state, slot):
		return
	GameState.set_pack(player.slot, pack)
	_world_items().remove_item(held)


@rpc("any_peer", "call_local", "reliable")
func request_belt_take(slot: int) -> void:
	if not _from_owner() or player.held_item() != null:
		return
	var pack: Backpack = contents()
	var state: ItemState = pack.take_from_belt(slot)
	if state == null:
		return
	state.uid = 0
	GameState.set_pack(player.slot, pack)
	_world_items().give_state(player, state)


@rpc("any_peer", "call_local", "reliable")
func request_move(index: int, cell: Vector2i, rotated: bool) -> void:
	if not _from_owner():
		return
	var pack: Backpack = contents()
	if pack.move(index, cell, rotated):
		GameState.set_pack(player.slot, pack)


func _from_owner() -> bool:
	if not multiplayer.is_server():
		return false
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	return sender == player.peer_id


func _world_items() -> WorldItems:
	return get_tree().get_first_node_in_group(WorldItems.GROUP) as WorldItems
