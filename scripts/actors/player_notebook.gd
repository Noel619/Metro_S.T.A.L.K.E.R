class_name PlayerNotebook
extends Node
## El cuaderno de un jugador (F3-04, docs/SUPERFICIE.md 5): Tab lo saca y lo vuelve a
## guardar ([NotebookView], solo en su equipo). Lo que se dibuja se manda al anfitrión,
## que lo guarda en el estado de la partida ([method GameState.set_notebook]); cada
## equipo lo ve desde ahí. Solo su dueño puede escribir en él.
##
## Sacarlo lleva su momento (se sujeta con las dos manos: hay que tenerlas libres) y
## mientras está abierto no se anda. El tiempo sigue.

## Ha cambiado lo que hay (en todos los equipos).
signal changed

var player: Player
var view: NotebookView
## La doble página abierta (la de la izquierda es la 2 × esta).
var spread: int = 0


func setup(owner_player: Player) -> void:
	player = owner_player
	name = "Cuaderno"
	GameState.changed.connect(func() -> void: changed.emit())


## Lo que hay ahora (una copia).
func contents() -> Notebook:
	return GameState.notebook(player.slot)


## Está abierto (en su equipo).
func is_open() -> bool:
	return view != null and is_instance_valid(view)


## Tab: lo saca o lo guarda. Con algo en las manos no se puede sujetar.
func toggle(camera: Camera3D) -> void:
	if is_open():
		view.close()
		return
	if player.held_item() != null or camera == null:
		return
	view = NotebookView.new()
	view.open(self, camera)
	view.closed.connect(func() -> void: view = null)


## Pide un trazo de la tinta [param ink] en la página [param page].
func draw_stroke(page: int, ink: int, points: PackedVector2Array) -> void:
	request_stroke.rpc_id(Carryable.HOST_PEER, page, ink, points)


func erase(page: int, point: Vector2, radius: float) -> void:
	request_erase.rpc_id(Carryable.HOST_PEER, page, point, radius)


func stamp(page: int, kind: String, at: Vector2, text: String) -> void:
	request_stamp.rpc_id(Carryable.HOST_PEER, page, kind, at, text)


func write(page: int, at: Vector2, text: String) -> void:
	request_note.rpc_id(Carryable.HOST_PEER, page, at, text)


@rpc("any_peer", "call_local", "reliable")
func request_stroke(page: int, ink: int, points: PackedVector2Array) -> void:
	if not _from_owner():
		return
	var notebook: Notebook = contents()
	if notebook.add_stroke(page, ink, points):
		GameState.set_notebook(player.slot, notebook)


@rpc("any_peer", "call_local", "reliable")
func request_erase(page: int, point: Vector2, radius: float) -> void:
	if not _from_owner():
		return
	var notebook: Notebook = contents()
	if notebook.erase_near(page, point, clampf(radius, 0.0, 0.1)) > 0:
		GameState.set_notebook(player.slot, notebook)


@rpc("any_peer", "call_local", "reliable")
func request_stamp(page: int, kind: String, at: Vector2, text: String) -> void:
	if not _from_owner():
		return
	var notebook: Notebook = contents()
	if notebook.add_stamp(page, kind, at, text):
		GameState.set_notebook(player.slot, notebook)


@rpc("any_peer", "call_local", "reliable")
func request_note(page: int, at: Vector2, text: String) -> void:
	if not _from_owner():
		return
	var notebook: Notebook = contents()
	if notebook.add_note(page, at, text):
		GameState.set_notebook(player.slot, notebook)


## En el anfitrión: lo pide su dueño.
func _from_owner() -> bool:
	if not multiplayer.is_server():
		return false
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	return sender == player.peer_id
