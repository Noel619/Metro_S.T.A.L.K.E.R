extends SceneTree
## Prueba de red del depósito (F2-14) con dos procesos de Godot.
##
## El anfitrión abre la partida y carga el depósito. El invitado se une, recibe
## su jugador y los objetos, y trabaja en el local como lo haría con el ratón:
##
## 1. Anda, coge una lata del banco, se la lleva y la suelta.
## 2. Coge la escoba y barre una mancha de polvo: el anfitrión aplica el trabajo
##    y el invitado ve la mancha limpia.
## 3. El anfitrión abre (persiana, hora) y hace venir al relojero, que deja dinero
##    por un despertador con su etiqueta. El invitado coge los billetes del
##    mostrador: es aceptar, y ve entrar el dinero en la caja.
## 4. El invitado se pone la mochila (F3-03): ya no está en el suelo y la lleva.
##    Al irse, el anfitrión la deja en el suelo, donde estaba él.
##
## Cada uno comprueba lo que ve del otro: el anfitrión, que el invitado anda,
## lleva cosas, barre, vende y se pone la mochila; el invitado, que todo eso le llega.
##
## No se lanza a mano: lo hace tools/test_net.sh. Este guion no nombra las
## clases del juego: se compila antes de que existan las autocargas.

const SCENE_PATH: String = "res://scenes/depot/deposito.tscn"
const TIMEOUT: float = 75.0
## Lo que dejó el antiguo dueño y la mochila.
const EXPECTED_ITEMS: int = 29
## La mancha de polvo que barre el invitado (DepotChores.DIRT[1]).
const DUST_INDEX: int = 1
const SALE_PRICE: int = 20

var _role: String = ""
var _elapsed: float = 0.0
var _finished: bool = false
var _level: Node
var _guest_seen_moving: bool = false
var _guest_seen_carrying: bool = false
var _guest_seen_wearing: bool = false
var _guest_start: Vector3 = Vector3.INF
var _sale_started: bool = false


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
	# Una partida nueva, sin tocar la guardada.
	var script: Script = load("res://scripts/depot/depot_level.gd")
	script.set("continue_saved", false)
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


## El anfitrión mira lo que hace el jugador del invitado y, cuando ha barrido,
## abre el mostrador y hace venir al relojero.
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
		if player.gear.wearing():
			_guest_seen_wearing = true
	if not _sale_started and _dust().call("is_clean"):
		_sale_started = true
		_open_for_a_sale()


func _open_for_a_sale() -> void:
	var world: Node = _level.world
	world.set_values("persiana", {"atascada": false, "abierta": true})
	var state: Node = root.get_node("GameState")
	state.set("minute", 10.0 * 60.0)
	state.push()
	var counter: Node = _level.counter
	counter.start_visit([&"relojero", "comprar"])
	var window: Vector3 = Vector3(0.0, 0.0, 4.3)
	counter.customer.global_position = window
	var path: Array[Vector3] = [window]
	counter.customer.walk(path)
	var spot: Vector3 = Vector3(-0.05, 1.0, 3.15)
	var clock: Node = _level.items.spawn_with(&"despertador", Transform3D(Basis.IDENTITY, spot), {})
	clock.set_values({"price": SALE_PRICE, "condition": 0.85})
	print("[host] abierto: el relojero en la ventanilla y un despertador en el mostrador")


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
	if not await _carry_a_can(me):
		return
	if not await _sweep(me):
		return
	if not await _accept_a_sale(me):
		return
	if not await _wear_backpack(me):
		return
	_finish(true, "ha barrido, ha vendido el despertador por %d ₽ y lleva la mochila" % SALE_PRICE)


## El invitado va a por una lata del banco, la coge, se la lleva y la suelta.
func _carry_a_can(me: Node) -> bool:
	var can: Node = null
	for item: Node in _level.items.items():
		if item.state.data.id == &"lata_conserva" and item.get_parent().global_position.x > -1.0:
			can = item
			break
	if not await _pick_up(me, can, "la lata"):
		return false
	var body: Node3D = can.get_parent()
	var resting: Vector3 = body.global_position
	var lifted: Callable = func() -> bool:
		return body.global_position.distance_to(can.hold_target().origin) < 0.25
	if not await _until(lifted, "la lata no llega a sus manos"):
		return false
	var failure: String = await _walk_with(me, can)
	if not failure.is_empty():
		_finish(false, failure)
		return false
	var carried: float = body.global_position.distance_to(resting)
	if carried < 0.8 or not lifted.call():
		_finish(false, "la lata no le sigue (se ha movido %.2f m)" % carried)
		return false
	me.interact()
	if not await _until(func() -> bool: return me.held_item() == null, "no la suelta"):
		return false
	print("[client] ha llevado la lata %.2f m y la ha soltado" % carried)
	return true


## Coge la escoba y barre una mancha: cada pasada se la pide al anfitrión.
func _sweep(me: Node) -> bool:
	var broom: Node = null
	for item: Node in _level.items.items():
		if item.state.data.id == &"escoba":
			broom = item
	var lying: Vector3 = broom.get_parent().global_transform * broom.bounds().get_center()
	if not await _pick_up(me, broom, "la escoba", Vector3(lying.x - 0.9, 0.03, lying.z)):
		return false
	var patch: Node3D = _dust()
	me.position = patch.global_position + Vector3(0.0, 0.03, 1.1)
	me.rotation.y = 0.0
	await _frames(2)
	_aim(me, patch.global_position)
	var work: Node = null
	for workable: Node in patch.workables:
		if workable.accepts(&"escoba"):
			work = workable
	for _i in 6:
		me.apply_work(work, 1.0, patch.global_position)
		await _frames(4)
	if not await _until(func() -> bool: return patch.is_clean(), "la mancha no se limpia"):
		return false
	me.interact()
	await _until(func() -> bool: return me.held_item() == null, "no suelta la escoba")
	print("[client] ha barrido la mancha y la ve limpia")
	return true


## Espera al relojero y coge sus billetes del mostrador.
func _accept_a_sale(me: Node) -> bool:
	var state: Node = root.get_node("GameState")
	var wad: Array = [null]
	var offered: Callable = func() -> bool:
		for item: Node in _level.items.items():
			if item.state.data.id == &"billetes" and item.state.extra.has("de"):
				wad[0] = item
				return true
		return false
	if not await _until(offered, "el relojero no deja dinero"):
		return false
	var start: int = state.get("rubles")
	# Coger los billetes es aceptar: el anfitrión los quita enseguida (entran en la caja).
	if not await _pick_up(me, wad[0], "los billetes", Vector3(-0.3, 0.03, 2.45), false):
		return false
	var paid: Callable = func() -> bool: return int(state.get("rubles")) == start + SALE_PRICE
	if not await _until(paid, "los billetes no entran en la caja"):
		return false
	var gone: Callable = func() -> bool:
		for item: Node in _level.items.items():
			if item.state.data.id == &"despertador":
				return false
		return true
	if not await _until(gone, "el relojero no se lleva el despertador"):
		return false
	print("[client] ha vendido el despertador y ve el dinero en la caja")
	return true


## Se pone la mochila que hay en el suelo. Lo decide el anfitrión cuando lo ve a
## su lado: la petición se repite cada segundo hasta que llega puesta.
func _wear_backpack(me: Node) -> bool:
	var bag: Node = null
	for item: Node in _level.items.items():
		if item.state.data.id == &"mochila":
			bag = item
	if bag == null:
		_finish(false, "no encuentra la mochila")
		return false
	var uid: int = bag.state.uid
	me.position = bag.get_parent().global_position + Vector3(0.0, 0.03, 0.9)
	me.rotation.y = 0.0
	while not me.gear.wearing():
		me.gear.request_backpack.rpc_id(1, uid)
		var waited: float = _elapsed
		while not me.gear.wearing() and _elapsed - waited < 1.0:
			if _finished or _elapsed > TIMEOUT - 1.0:
				_finish(false, "no le llega la mochila puesta")
				return false
			await physics_frame
	var lifted: Callable = func() -> bool: return _level.items.find_item(uid) == null
	if not await _until(lifted, "la mochila puesta sigue en el suelo"):
		return false
	print("[client] lleva la mochila puesta y ya no la ve en el suelo")
	return true


## Se pone delante de [param item], lo mira y lo coge (lo decide el anfitrión).
## Con [param wait_held], espera a tenerlo en las manos.
func _pick_up(
	me: Node, item: Node, what: String, stand: Vector3 = Vector3.INF, wait_held: bool = true
) -> bool:
	if item == null:
		_finish(false, "no encuentra %s" % what)
		return false
	var body: Node3D = item.get_parent()
	# Se mira al centro de lo que se ve (el origen de la escoba está en las cerdas).
	var center: Vector3 = body.global_transform * item.bounds().get_center()
	var spot: Vector3 = stand if stand != Vector3.INF else Vector3(center.x, 0.03, center.z + 1.1)
	me.position = spot
	me.rotation.y = atan2(spot.x - center.x, spot.z - center.z)
	await _frames(2)
	_aim(me, center)
	if not await _until(func() -> bool: return me.focused() != null, "no tiene delante %s" % what):
		return false
	me.interact()
	if not wait_held:
		return true
	return await _until(
		func() -> bool: return me.held_item() == item, "el anfitrión no le da %s" % what
	)


## Baja o sube la mirada hasta [param target] (la chica tiene los ojos más bajos).
func _aim(me: Node, target: Vector3) -> void:
	var eye: Vector3 = me.eye_position()
	var flat: float = Vector2(eye.x - target.x, eye.z - target.z).length()
	me.head_pitch = -atan2(eye.y - target.y, flat)


## La mancha de polvo de la prueba.
func _dust() -> Node3D:
	return _level.chores.dirt[DUST_INDEX]


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
	var sales: Array = root.get_node("GameState").get("ledger").filter(
		func(entry: Dictionary) -> bool: return entry["kind"] == "venta"
	)
	# Al irse, su mochila se queda en el suelo del depósito.
	var left_behind: bool = _level.items.items().any(
		func(item: Node) -> bool: return item.state.data.id == &"mochila"
	)
	var seen: bool = (
		_guest_seen_moving
		and _guest_seen_carrying
		and _dust().is_clean()
		and sales.size() == 1
		and _guest_seen_wearing
		and left_behind
	)
	_finish(
		seen,
		(
			(
				"invitado visto andando: %s; llevando cosas: %s; mancha barrida: %s; ventas: %d;"
				% [_guest_seen_moving, _guest_seen_carrying, _dust().is_clean(), sales.size()]
			)
			+ (
				" con la mochila puesta: %s; la deja al irse: %s"
				% [_guest_seen_wearing, left_behind]
			)
		)
	)


func _finish(success: bool, message: String) -> void:
	if _finished:
		return
	_finished = true
	print("[%s] %s: %s" % [_role, "OK" if success else "FALLO", message])
	quit(0 if success else 1)
