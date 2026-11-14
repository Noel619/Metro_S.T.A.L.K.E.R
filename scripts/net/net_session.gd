extends Node
## Sesión de red. El juego funciona SIEMPRE con un anfitrión:
##
## - En solitario, el anfitrión no tiene invitados ([OfflineMultiplayerPeer]).
## - En cooperativo, el anfitrión abre un servidor ENet y se unen hasta 3 invitados.
##
## El anfitrión (peer 1) tiene la autoridad sobre el mundo: IA, objetos,
## puertas e inventarios. Cada jugador controla su propio movimiento.

signal hosted
signal joined
signal join_failed
signal peer_joined(peer_id: int)
signal peer_left(peer_id: int)
signal ended

enum Mode { SOLO, HOST, CLIENT }

const DEFAULT_PORT: int = 24680
const MAX_PLAYERS: int = 4

var mode: Mode = Mode.SOLO


func _ready() -> void:
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected_to_server)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)
	start_solo()


## Partida en solitario: un anfitrión sin invitados.
func start_solo() -> void:
	multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	mode = Mode.SOLO


## Abre la partida a otros jugadores.
func host(port: int = DEFAULT_PORT) -> Error:
	var peer: ENetMultiplayerPeer = ENetMultiplayerPeer.new()
	var err: Error = peer.create_server(port, MAX_PLAYERS - 1)
	if err != OK:
		return err
	multiplayer.multiplayer_peer = peer
	mode = Mode.HOST
	hosted.emit()
	return OK


## Se une a la partida de otro jugador.
func join(address: String, port: int = DEFAULT_PORT) -> Error:
	var peer: ENetMultiplayerPeer = ENetMultiplayerPeer.new()
	var err: Error = peer.create_client(address, port)
	if err != OK:
		return err
	multiplayer.multiplayer_peer = peer
	mode = Mode.CLIENT
	return OK


## Cierra la conexión y vuelve a solitario.
func leave() -> void:
	if mode != Mode.SOLO and multiplayer.multiplayer_peer != null:
		multiplayer.multiplayer_peer.close()
	start_solo()
	ended.emit()


## ¿Este proceso manda sobre el mundo?
func is_authority() -> bool:
	return multiplayer.is_server()


func local_peer_id() -> int:
	return multiplayer.get_unique_id()


func _on_peer_connected(peer_id: int) -> void:
	peer_joined.emit(peer_id)


func _on_peer_disconnected(peer_id: int) -> void:
	peer_left.emit(peer_id)


func _on_connected_to_server() -> void:
	joined.emit()


func _on_connection_failed() -> void:
	start_solo()
	join_failed.emit()


func _on_server_disconnected() -> void:
	start_solo()
	ended.emit()
