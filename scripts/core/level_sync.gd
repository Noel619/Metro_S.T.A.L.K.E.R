class_name LevelSync
extends Node
## Que todos los equipos tengan la escena cargada antes de que el anfitrión haga
## aparecer lo que se replica (los jugadores, los objetos, los perros). Al cambiar
## de escena cada equipo tarda lo suyo (levantar la ciudad son unos segundos), y
## lo que el anfitrión hiciera aparecer antes de que un invitado tenga la escena
## se perdería para él.
##
## Cada nivel pone uno, con el mismo nombre, como primer hijo. Los invitados que
## ya estaban conectados al cargar la escena avisan de que la tienen (con lo que
## el anfitrión necesite saber de ellos: su protagonista) hasta que el anfitrión
## les contesta; el anfitrión espera a todos ([method wait]) o, como mucho,
## [constant TIMEOUT] segundos.

## Todos los equipos tienen la escena (en el anfitrión).
signal all_ready
## El anfitrión ha recibido el aviso de este invitado.
signal acknowledged
## Un invitado tiene la escena (en el anfitrión), también si llega tarde.
signal peer_ready(peer: int, info: Dictionary)

const TIMEOUT: float = 60.0
const RETRY_SECONDS: float = 1.0

## Lo que ha contado cada invitado de sí mismo (en el anfitrión): peer -> datos.
var infos: Dictionary = {}
## Ya están todos.
var done: bool = false

var _info: Dictionary = {}
var _acked: bool = false
var _retry: float = 0.0
var _waited: float = 0.0


func _ready() -> void:
	if multiplayer.is_server():
		multiplayer.peer_disconnected.connect(func(_peer: int) -> void: _check())
		# Sin invitados (o en solitario) ya están todos: el nivel sigue sin esperar.
		_check()


func _process(delta: float) -> void:
	if multiplayer.is_server():
		if not done:
			_waited += delta
			if _waited >= TIMEOUT:
				push_warning("No todos los invitados cargaron la escena: se sigue sin ellos.")
				_finish()
		return
	if _info.is_empty() or _acked:
		return
	_retry -= delta
	if _retry <= 0.0:
		_retry = RETRY_SECONDS
		report_ready.rpc_id(1, _info)


## Los invitados: avisar al anfitrión de que la escena está cargada.
func report(info: Dictionary) -> void:
	if multiplayer.is_server() or NetSession.mode != NetSession.Mode.CLIENT:
		return
	_info = info.duplicate()
	if _info.is_empty():
		_info = {"listo": true}
	_retry = 0.0


## El anfitrión: espera a que todos tengan la escena.
func wait() -> void:
	if not done:
		await all_ready


@rpc("any_peer", "call_remote", "reliable")
func report_ready(info: Dictionary) -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	var first: bool = not infos.has(sender)
	infos[sender] = info
	_acknowledge.rpc_id(sender)
	if first:
		peer_ready.emit(sender, info)
		_check()


@rpc("authority", "call_remote", "reliable")
func _acknowledge() -> void:
	if _acked:
		return
	_acked = true
	acknowledged.emit()


func _check() -> void:
	if done:
		return
	for peer: int in multiplayer.get_peers():
		if not infos.has(peer):
			return
	_finish()


func _finish() -> void:
	if done:
		return
	done = true
	all_ready.emit()
