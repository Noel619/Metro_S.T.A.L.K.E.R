extends SceneTree
## Prueba de red con dos procesos de Godot conectados por ENet.
##
## El anfitrión carga la escena "Hola, Tumansk" y mueve la caja. El invitado
## carga la misma escena, no simula nada y comprueba que la caja se mueve en su
## pantalla gracias a la replicación.
##
## No se lanza a mano: lo hace tools/test_net.sh.

const SCENE_PATH: String = "res://scenes/debug/hola_tumansk.tscn"
const BOX_PATH: NodePath = ^"Caja"
const PORT: int = 24690
const TIMEOUT: float = 20.0
const REQUIRED_DISTANCE: float = 0.5
const REQUIRED_SAMPLES: int = 20

var _role: String = ""
var _elapsed: float = 0.0
var _box: Node3D
var _first_position: Vector3 = Vector3.INF
var _last_position: Vector3 = Vector3.INF
var _samples: int = 0
var _guest_joined: bool = false
var _finished: bool = false


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
	var net: Node = root.get_node("NetSession")
	if _role == "host":
		if net.host(PORT) != OK:
			_finish(false, "no se pudo abrir el puerto %d" % PORT)
			return
		net.peer_joined.connect(_on_guest_joined)
		net.peer_left.connect(_on_guest_left)
	else:
		if net.join("127.0.0.1", PORT) != OK:
			_finish(false, "no se pudo crear la conexión")
			return
	var scene: Node = load(SCENE_PATH).instantiate()
	root.add_child(scene)
	_box = scene.get_node(BOX_PATH)
	print("[%s] escena cargada" % _role)


func _process(delta: float) -> bool:
	if _finished:
		return false
	_elapsed += delta
	if _elapsed > TIMEOUT:
		_finish(false, "tiempo agotado (muestras: %d)" % _samples)
		return false
	if _role == "client" and _box != null:
		_sample_box()
	return false


func _sample_box() -> void:
	var position: Vector3 = _box.position
	if position.is_equal_approx(_last_position):
		return
	_last_position = position
	if _first_position == Vector3.INF:
		_first_position = position
		return
	_samples += 1
	var distance: float = _first_position.distance_to(position)
	if _samples >= REQUIRED_SAMPLES and distance >= REQUIRED_DISTANCE:
		_finish(true, "la caja se ha movido %.2f m en %d actualizaciones" % [distance, _samples])


func _on_guest_joined(peer_id: int) -> void:
	_guest_joined = true
	print("[host] se ha unido el invitado %d" % peer_id)


func _on_guest_left(_peer_id: int) -> void:
	_finish(_guest_joined, "el invitado ha terminado")


func _finish(success: bool, message: String) -> void:
	if _finished:
		return
	_finished = true
	print("[%s] %s: %s" % [_role, "OK" if success else "FALLO", message])
	quit(0 if success else 1)
