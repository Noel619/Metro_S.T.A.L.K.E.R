extends SceneTree
## Prueba de red del depósito (F2-14) con dos procesos de Godot.
##
## El anfitrión abre la partida y carga el depósito. El invitado se une, recibe
## su jugador y los objetos, anda, coge una lata del banco y se la lleva. Cada
## uno comprueba lo que ve del otro:
##
## - el invitado, que hay dos jugadores, que están todos los objetos y que la
##   lata que ha pedido coger le sigue (la mueve el anfitrión);
## - el anfitrión, que el jugador del invitado se mueve y que lleva la lata.
##
## No se lanza a mano: lo hace tools/test_net.sh. Este guion no nombra las
## clases del juego: se compila antes de que existan las autocargas.

const SCENE_PATH: String = "res://scenes/depot/deposito.tscn"
const TIMEOUT: float = 40.0
const EXPECTED_ITEMS: int = 28

var _role: String = ""
var _elapsed: float = 0.0
var _finished: bool = false
var _level: Node
var _guest_seen_moving: bool = false
var _guest_seen_carrying: bool = false
var _guest_start: Vector3 = Vector3.INF


func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="):
			_role = arg.get_slice("=", 1)
	if _role != "host" and _role != "client":
		_finish(false, "falta --role=host o --role=client")
		return
	_start.call_deferred()


func _start() -> void:
	await process_frame
	_level = load(SCENE_PATH).instantiate()
	root.add_child(_level)
	print("[%s] depósito cargado" % _role)
	if _role == "host":
		root.get_node("NetSession").peer_left.connect(_on_guest_left)
	else:
		_play_as_guest()


func _process(delta: float) -> bool:
	if _finished:
		return false
	_elapsed += delta
	if _elapsed > TIMEOUT:
		_finish(false, "tiempo agotado")
	elif _role == "host" and _level != null:
		_watch_guest()
	return false


## El anfitrión mira lo que hace el jugador del invitado.
func _watch_guest() -> void:
	for player: Node in _level.players():
		if player.peer_id == 1:
			continue
		if _guest_start == Vector3.INF:
			_guest_start = player.position
		elif player.position.distance_to(_guest_start) > 0.5:
			_guest_seen_moving = true
		if player.held_item() != null:
			_guest_seen_carrying = true


func _play_as_guest() -> void:
	if not await _until(
		func() -> bool: return _level.local_player() != null, "no llega su jugador"
	):
		return
	var me: Node = _level.local_player()
	var ready: Callable = func() -> bool:
		return _level.players().size() == 2 and _level.items.items().size() == EXPECTED_ITEMS
	if not await _until(ready, "faltan jugadores u objetos"):
		return
	print("[client] ve 2 jugadores y %d objetos; su color es el %d" % [EXPECTED_ITEMS, me.slot])
	# Anda un poco para que el anfitrión lo vea moverse.
	me.scripted_input = Vector2(0.0, 1.0)
	await _frames(45)
	me.scripted_input = Vector2.ZERO
	_carry_a_can(me)


## El invitado va a por una lata del banco, la coge, se la lleva y la suelta.
func _carry_a_can(me: Node) -> void:
	var can: Node = null
	for item: Node in _level.items.items():
		if item.state.data.id == &"lata_conserva" and item.get_parent().global_position.x > -1.0:
			can = item
			break
	var body: Node3D = can.get_parent()
	var resting: Vector3 = body.global_position
	me.position = Vector3(resting.x, 0.03, resting.z + 1.1)
	me.rotation.y = 0.0
	await _frames(2)
	# Mira al centro de la lata (la chica tiene los ojos más bajos que el chico).
	var eye: Vector3 = me.eye_position()
	var center: Vector3 = resting + Vector3(0.0, 0.05, 0.0)
	me.head_pitch = -atan2(eye.y - center.y, Vector2(eye.x - center.x, eye.z - center.z).length())
	if not await _until(func() -> bool: return me.focused() != null, "no tiene la lata delante"):
		return
	me.interact()
	if not await _until(
		func() -> bool: return me.held_item() == can, "el anfitrión no le da la lata"
	):
		return
	var lifted: Callable = func() -> bool:
		return body.global_position.distance_to(can.hold_target().origin) < 0.25
	if not await _until(lifted, "la lata no llega a sus manos"):
		return
	var failure: String = await _walk_with(me, can)
	if not failure.is_empty():
		_finish(false, failure)
		return
	var carried: float = body.global_position.distance_to(resting)
	if carried < 0.8 or not lifted.call():
		_finish(false, "la lata no le sigue (se ha movido %.2f m)" % carried)
		return
	me.interact()
	if not await _until(func() -> bool: return me.held_item() == null, "no la suelta"):
		return
	_finish(true, "ha cogido la lata, la ha llevado %.2f m y la ha soltado" % carried)


## Anda con la lata. La física es del anfitrión y llega con retraso, pero el
## invitado la dibuja en sus manos, también mientras anda. Devuelve el fallo, si lo hay.
func _walk_with(me: Node, can: Node) -> String:
	if not await _until(func() -> bool: return can.in_hands(), "no la ve en sus manos"):
		return "no la ve en sus manos"
	var slipped: int = 0
	me.scripted_input = Vector2(0.0, 1.0)
	for _i in 60:
		await physics_frame
		await process_frame
		slipped += 0 if can.in_hands() else 1
	me.scripted_input = Vector2.ZERO
	await _frames(30)
	if slipped > 0:
		return "al andar, la lata se le despega de las manos (%d veces)" % slipped
	return ""


func _until(condition: Callable, failure: String) -> bool:
	while not condition.call():
		if _finished:
			return false
		if _elapsed > TIMEOUT - 1.0:
			_finish(false, failure)
			return false
		await physics_frame
	return true


func _frames(count: int) -> void:
	for _i in count:
		await physics_frame


func _on_guest_left(_peer_id: int) -> void:
	var seen: bool = _guest_seen_moving and _guest_seen_carrying
	_finish(
		seen,
		(
			"invitado visto andando: %s; llevando la lata: %s"
			% [_guest_seen_moving, _guest_seen_carrying]
		)
	)


func _finish(success: bool, message: String) -> void:
	if _finished:
		return
	_finished = true
	print("[%s] %s: %s" % [_role, "OK" if success else "FALLO", message])
	quit(0 if success else 1)
