extends SceneTree
## Prueba de red de la salida (F3-14) con dos procesos de Godot: subir, coger algo y
## volver, los dos juntos.
##
## 1. En el depósito, el anfitrión abre la reja y los dos suben por las escaleras.
## 2. Arriba, el invitado ve a su compañero y a los seis perros de la Jauría (que el
##    anfitrión deja quietos) y va a la puerta del quiosco Q2. El anfitrión abre la
##    compuerta y, cuando el invitado está en la puerta, le da una palanca.
## 3. El invitado revienta la puerta (o la abre, si no estaba cerrada), suelta la
##    palanca, entra, coge algo de lo que hay dentro y lo guarda en la mochila.
## 4. Los dos entran en la esclusa; el anfitrión cierra la compuerta y se baja.
## 5. Abajo, lo que cogió sigue en su mochila.
##
## Los jugadores se ponen en su sitio de golpe, pero nunca con algo en las manos: lo
## que se lleva lo mueve la física del anfitrión y, lejos de las manos, se suelta.
##
## No se lanza a mano: lo hace tools/test_net.sh. Este guion no nombra las clases del
## juego: se compila antes de que existan las autocargas.

const DEPOT_PATH: String = "res://scenes/depot/deposito.tscn"
const TIMEOUT: float = 330.0
const KIOSK_DOOR: String = "PLZ-Q2_puerta_0"
const KIOSK: String = "PLZ-Q2"
const DOGS: int = 6
const HALL_FLOOR: float = 0.48

var _role: String = ""
var _elapsed: float = 0.0
var _finished: bool = false
var _level: Node
var _stage: String = "deposito"
var _taken: StringName = &""


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
	var script: Script = load("res://scripts/depot/depot_level.gd")
	script.set("continue_saved", false)
	_level = load(DEPOT_PATH).instantiate()
	root.add_child(_level)
	# Es la escena de ahora: al subir y al bajar, la cambia SceneRouter.
	current_scene = _level
	print("[%s] depósito cargado" % _role)
	if _role == "host":
		_host_depot()
	else:
		_guest_depot()


func _process(delta: float) -> bool:
	if _finished:
		return false
	_elapsed += delta
	if _elapsed > TIMEOUT:
		_finish(false, "tiempo agotado (%s)" % _stage)
	return false


# -- El anfitrión --------------------------------------------------------------


func _host_depot() -> void:
	var both: Callable = func() -> bool: return _level.players().size() == 2
	if not await _until(both, "el invitado no llega al depósito"):
		return
	var state: Node = root.get_node("GameState")
	state.set("minute", 9.0 * 60.0)
	state.push()
	_level.exit.set_value("abierta", true)
	print("[host] la reja abierta: arriba")
	await _climb_stairs(_level.local_player(), 0)
	var surface: Callable = func() -> bool: return _current_level_is("SurfaceLevel")
	if not await _until(surface, "no se sube"):
		return
	_level = _current_scene()
	_stage = "superficie"
	_host_surface()


func _host_surface() -> void:
	var players_up: Callable = func() -> bool: return _level.players().size() == 2
	if not await _until(players_up, "arriba no están los dos"):
		return
	_level.jauria.pack.set("paused", true)
	_level.world.set_values("compuerta", {"abierta": true})
	_level.hatch.snap()
	var guest: Node = _guest_player()
	var door: Node = _door()
	var at_door: Callable = func() -> bool:
		return guest.global_position.distance_to(door.global_position) < 2.5
	if not await _until(at_door, "el invitado no llega a la puerta del quiosco"):
		return
	await _frames(20)
	_level.items.give(guest, &"palanca")
	print("[host] arriba: la compuerta abierta y una palanca para el invitado")
	var state: Node = root.get_node("GameState")
	var looted: Callable = func() -> bool:
		return door.is_open() and not state.call("pack", guest.slot).entries.is_empty()
	if not await _until(looted, "el invitado no abre el quiosco ni guarda nada", 90.0):
		return
	var saved: Dictionary = state.call("pack", guest.slot).entries[0]["estado"]
	print("[host] el invitado ha abierto el quiosco y guarda %s" % saved.get("id", "?"))
	var me: Node = _level.local_player()
	me.global_position = _level.vestibule_point(2.7, -1.5, HALL_FLOOR + 0.05)
	var both_in: Callable = func() -> bool:
		return _level.in_lock(me.global_position) and _level.in_lock(guest.global_position)
	if not await _until(both_in, "no entran los dos en la esclusa"):
		return
	_level.world.set_values("compuerta", {"abierta": false})
	_level.hatch.snap()
	_host_return()


func _host_return() -> void:
	var depot: Callable = func() -> bool: return _current_level_is("DepotLevel")
	if not await _until(depot, "no se baja"):
		return
	_level = _current_scene()
	_stage = "vuelta"
	var state: Node = root.get_node("GameState")
	var guest_back: Callable = func() -> bool:
		for player: Node in _level.players():
			if player.peer_id != 1 and not state.call("pack", player.slot).entries.is_empty():
				return true
		return false
	if not await _until(guest_back, "abajo el invitado no trae nada"):
		return
	await _frames(60)
	_finish(true, "han subido, saqueado el quiosco y vuelto con el botín")


# -- El invitado ---------------------------------------------------------------


func _guest_depot() -> void:
	var mine: Callable = func() -> bool: return _level.local_player() != null
	if not await _until(mine, "no llega su jugador"):
		return
	var open: Callable = func() -> bool: return _level.exit.is_open()
	if not await _until(open, "no se abre la reja"):
		return
	await _climb_stairs(_level.local_player(), 1)
	var surface: Callable = func() -> bool:
		return _current_level_is("SurfaceLevel") and _current_scene().local_player() != null
	if not await _until(surface, "no sube"):
		return
	_level = _current_scene()
	_stage = "superficie"
	_guest_surface()


func _guest_surface() -> void:
	var me: Node = _level.local_player()
	var company: Callable = func() -> bool:
		return _level.players().size() == 2 and get_nodes_in_group(&"perros").size() == DOGS
	if not await _until(company, "no ve a su compañero y a los seis perros"):
		return
	print("[client] arriba, con su compañero y los %d perros de la Jauría" % DOGS)
	if not await _open_kiosk(me):
		return
	if not await _take_loot(me):
		return
	if not await _stash(me):
		return
	me.global_position = _level.vestibule_point(2.7, 1.5, HALL_FLOOR + 0.05)
	print("[client] en la esclusa con %s en la mochila" % _taken)
	_guest_return()


func _guest_return() -> void:
	var depot: Callable = func() -> bool:
		return _current_level_is("DepotLevel") and _current_scene().local_player() != null
	if not await _until(depot, "no baja"):
		return
	_level = _current_scene()
	_stage = "vuelta"
	var state: Node = root.get_node("GameState")
	var still: Callable = func() -> bool:
		for entry: Dictionary in state.call("pack", _level.local_player().slot).entries:
			if StringName(entry["estado"].get("id", "")) == _taken:
				return true
		return false
	if not await _until(still, "abajo no trae %s" % _taken):
		return
	_finish(true, "abajo, con %s en la mochila" % _taken)


## Va a la puerta del quiosco, recibe la palanca, la revienta (o la abre, si no estaba
## cerrada) y suelta la palanca.
func _open_kiosk(me: Node) -> bool:
	var door: Node = _door()
	if door == null:
		_finish(false, "no encuentra la puerta del quiosco")
		return false
	var hinge: Transform3D = door.global_transform
	var size: Vector3 = door.get("size")
	me.global_position = hinge * Vector3(size.x * 0.5, 0.05, 0.9)
	var target: Vector3 = hinge * Vector3(size.x * 0.5, 1.0, 0.0)
	_face(me, target)
	var crowbar: Callable = func() -> bool:
		return me.held_item() != null and me.held_item().state.data.id == &"palanca"
	if not await _until(crowbar, "no le llega la palanca"):
		return false
	await _frames(20)
	var body: Node = door.get_node("Bisagra/Cuerpo")
	for _pull in 8:
		if door.is_open() or not door.is_locked():
			break
		var work: Node = null
		for child: Node in body.get_children():
			if child.has_method("accepts") and child.accepts(&"palanca"):
				work = child
		if work == null:
			break
		me.apply_work(work, 1.0, target)
		await _frames(12)
	if not door.is_locked() and not door.is_open():
		door.request_use.rpc_id(1, &"")
	var opened: Callable = func() -> bool: return door.is_open()
	if not await _until(opened, "la puerta del quiosco no se abre (%s)" % door.lock()):
		return false
	print("[client] la puerta del quiosco, abierta (%s)" % door.lock())
	me.interact()
	return await _until(func() -> bool: return me.held_item() == null, "no suelta la palanca")


## Entra en el quiosco y coge lo primero que encuentra.
func _take_loot(me: Node) -> bool:
	var building: Dictionary = _level.city.buildings_by_id[KIOSK]
	var center: Vector3 = Vector3(
		building["centro"][0], float(building["cota"]), -building["centro"][1]
	)
	# Las lambdas copian lo que capturan: lo encontrado se deja en una lista.
	var found: Array = [null]
	var settled: Callable = func() -> bool:
		for item: Node in _level.items.items():
			var body: Node3D = item.get_parent()
			if body.global_position.distance_to(center) < 3.5 and item.state.data.id != &"palanca":
				found[0] = item
				return true
		return false
	if not await _until(settled, "no hay nada en el quiosco"):
		return false
	var loot: Node = found[0]
	print("[client] dentro del quiosco hay %s (%.0f s)" % [loot.state.data.id, _elapsed])
	var body: Node3D = loot.get_parent()
	var spot: Vector3 = center + (body.global_position - center).normalized() * 0.2
	me.global_position = Vector3(spot.x, center.y + 0.05, spot.z)
	var look_at: Vector3 = body.global_transform * loot.bounds().get_center()
	_face(me, look_at)
	await _frames(4)
	_aim(me, look_at)
	if not await _until(func() -> bool: return me.focused() != null, "no tiene delante el botín"):
		return false
	me.interact()
	var held: Callable = func() -> bool: return me.held_item() == loot
	if not await _until(held, "el anfitrión no le da el botín"):
		return false
	_taken = loot.state.data.id
	print("[client] ha cogido %s del quiosco" % _taken)
	return true


## Guarda lo que ha cogido en la mochila (arrodillándose).
func _stash(me: Node) -> bool:
	me.get("pack").call("store_held")
	var state: Node = root.get_node("GameState")
	var stored: Callable = func() -> bool:
		return me.held_item() == null and not state.call("pack", me.slot).entries.is_empty()
	if not await _until(stored, "no guarda %s en la mochila" % _taken):
		return false
	print("[client] ha guardado %s en la mochila" % _taken)
	return true


# -- Lo común ------------------------------------------------------------------


## Sube por las escaleras mecánicas desde su sitio delante de la reja.
func _climb_stairs(me: Node, slot: int) -> void:
	var exit_script: Script = load("res://scripts/depot/systems/depot_exit.gd")
	me.global_position = exit_script.call("arrival", slot)
	me.rotation.y = -PI / 2.0
	await _frames(10)
	me.set("scripted_input", Vector2(0.0, -1.0))


func _guest_player() -> Node:
	for player: Node in _level.players():
		if player.peer_id != 1:
			return player
	return null


func _door() -> Node:
	for door: Node in _level.sites.doors:
		if door.fixture_id == KIOSK_DOOR:
			return door
	return null


func _current_scene() -> Node:
	return current_scene if current_scene != null else _level


func _current_level_is(type_name: String) -> bool:
	var scene: Node = current_scene
	if scene == null:
		return false
	var script: Script = scene.get_script()
	return script != null and script.get_global_name() == type_name


func _face(me: Node, target: Vector3) -> void:
	var flat: Vector3 = Vector3(
		target.x - me.global_position.x, 0.0, target.z - me.global_position.z
	)
	me.rotation.y = atan2(-flat.x, -flat.z)


func _aim(me: Node, target: Vector3) -> void:
	var eye: Vector3 = me.eye_position()
	var flat: float = Vector2(eye.x - target.x, eye.z - target.z).length()
	me.head_pitch = -atan2(eye.y - target.y, flat)


func _until(condition: Callable, failure: String, seconds: float = 40.0) -> bool:
	var waited: float = 0.0
	while not condition.call():
		if _finished:
			return false
		await physics_frame
		waited += 1.0 / 60.0
		if waited > seconds:
			_finish(false, failure)
			return false
	return true


func _frames(count: int) -> void:
	for _i in count:
		await physics_frame


func _finish(ok: bool, message: String) -> void:
	if _finished:
		return
	_finished = true
	print("[%s] %s: %s (%.0f s)" % [_role, "OK" if ok else "FALLO", message, _elapsed])
	quit(0 if ok else 1)
