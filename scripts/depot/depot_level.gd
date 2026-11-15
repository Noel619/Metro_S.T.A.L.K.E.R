extends Node3D
## El depósito jugable (Fase 2).
##
## Monta la sala, pone los objetos sueltos y hace aparecer a los jugadores. El
## juego funciona siempre con un anfitrión: en solitario eres tú, sin invitados.
##
## Mientras no existan el menú y la firma de la escritura (Fase 5), la partida
## se abre con argumentos (después de "--") o con teclas de desarrollo:
##   --chica            juegas con la chica (por defecto, el chico)
##   --host             abres la partida a otros jugadores (F9)
##   --join=DIRECCION   te unes a la partida de otro (F10: en esta máquina)

const MODELS_DIR: String = "res://assets/models/"
const BASE_MATERIAL: String = "res://assets/materials/base_vertex.tres"
const FLOOR: float = 0.025
const SHELF_X: float = -1.95
const SHELF_LEVELS: Array[float] = [0.09, 0.51, 0.93, 1.35, 1.77]
const BENCH_TOP: float = 0.93
const SPAWN_POINTS: Array[Vector3] = [
	Vector3(0.5, 0.03, 0.7),
	Vector3(-0.5, 0.03, 0.9),
	Vector3(1.2, 0.03, 0.2),
	Vector3(-0.9, 0.03, 0.1)
]
const HELP: String = (
	"WASD andar · F coger y soltar · botón derecho: acercar y girar · Esc soltar el ratón\n"
	+ "F9 abrir la partida · F10 unirse a una partida de esta máquina · F1 ocultar"
)

var items: WorldItems
var _players: Node3D
var _player_spawner: MultiplayerSpawner
var _static: Node3D
var _variant: String = "chico"
var _label: Label


func _ready() -> void:
	StyleDirector.set_zone(StyleDirector.ZONE_DEPOT, true)
	_variant = GameState.protagonist
	var join_address: String = ""
	var open_to_others: bool = false
	for arg: String in OS.get_cmdline_user_args():
		if arg == "--chica":
			_variant = "chica"
		elif arg == "--host":
			open_to_others = true
		elif arg.begins_with("--join="):
			join_address = arg.get_slice("=", 1)
	_build_room()
	items = WorldItems.new()
	items.name = "Objetos"
	add_child(items)
	_players = Node3D.new()
	_players.name = "Jugadores"
	add_child(_players)
	_player_spawner = MultiplayerSpawner.new()
	_player_spawner.name = "Generador"
	_player_spawner.spawn_function = _build_player
	_players.add_child(_player_spawner)
	_player_spawner.spawn_path = _player_spawner.get_path_to(_players)
	_add_help()
	NetSession.joined.connect(_on_joined)
	NetSession.peer_left.connect(_on_peer_left)
	NetSession.ended.connect(_on_session_ended)
	if not join_address.is_empty():
		NetSession.join(join_address)
		return
	if open_to_others:
		NetSession.host()
	_start_as_host()


func _unhandled_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_F1:
			_label.visible = not _label.visible
		KEY_F9:
			if NetSession.mode == NetSession.Mode.SOLO:
				NetSession.host()
		KEY_F10:
			if NetSession.mode == NetSession.Mode.SOLO:
				_clear_world()
				NetSession.join("127.0.0.1")


## El jugador de este equipo, si ya ha aparecido.
func local_player() -> Player:
	return Player.find(get_tree(), multiplayer.get_unique_id())


func players() -> Array[Player]:
	var found: Array[Player] = []
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		found.append(node as Player)
	return found


## Un invitado pide su jugador al anfitrión cuando ya tiene la escena cargada.
@rpc("any_peer", "call_remote", "reliable")
func request_player(variant: String) -> void:
	if multiplayer.is_server():
		_spawn_player(multiplayer.get_remote_sender_id(), variant)


func _start_as_host() -> void:
	_stock()
	_spawn_player(multiplayer.get_unique_id(), _variant)


func _spawn_player(peer: int, variant: String) -> void:
	if Player.find(get_tree(), peer) != null or players().size() >= NetSession.MAX_PLAYERS:
		return
	var slot: int = _free_slot()
	_player_spawner.spawn({"peer": peer, "variant": variant, "slot": slot})


func _free_slot() -> int:
	var used: Array[int] = []
	for player: Player in players():
		used.append(player.slot)
	for slot: int in NetSession.MAX_PLAYERS:
		if not used.has(slot):
			return slot
	return 0


func _build_player(values: Dictionary) -> Node:
	var player: Player = Player.new()
	player.setup(values["peer"], values["variant"], values["slot"])
	var point: Vector3 = SPAWN_POINTS[int(values["slot"]) % SPAWN_POINTS.size()]
	player.position = point
	player.rotation.y = PI
	return player


func _on_joined() -> void:
	request_player.rpc_id(Carryable.HOST_PEER, _variant)


func _on_peer_left(peer: int) -> void:
	if not multiplayer.is_server():
		return
	var player: Player = Player.find(get_tree(), peer)
	if player == null:
		return
	if player.held_item() != null:
		player.held_item().request_drop()
	player.queue_free()


## Se ha cortado la conexión: vuelta a una partida en solitario.
func _on_session_ended() -> void:
	_clear_world()
	_start_as_host.call_deferred()


func _clear_world() -> void:
	for player: Player in players():
		player.remove_from_group(Player.GROUP)
		player.free()
	for child: Node in items.get_children():
		if not child is MultiplayerSpawner:
			child.free()


## Lo que hay en el depósito al empezar: de momento, lo del diorama limpio.
func _stock() -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 7
	var on_shelves: Array[Array] = [
		[&"caja_carton", -0.95, 0],
		[&"caja_carton_pequena", -1.18, 1],
		[&"caja_carton_pequena", -0.72, 1],
		[&"lata_conserva", -1.2, 2],
		[&"lata_conserva", -1.08, 2],
		[&"botella_marron", -0.8, 2],
		[&"botella_verde", -0.66, 2],
		[&"caja_carton_pequena", -0.95, 3],
		[&"caja_carton_pequena", -0.05, 0],
		[&"caja_carton_pequena", 0.42, 0],
		[&"caja_carton", 0.2, 1],
		[&"cubo", 0.0, 2],
		[&"lata_conserva", 0.38, 2],
		[&"caja_carton_pequena", 0.2, 3],
	]
	for entry: Array in on_shelves:
		var where: Vector3 = Vector3(SHELF_X, FLOOR + SHELF_LEVELS[entry[2]] + 0.01, entry[1])
		_item(entry[0], where, 90.0 + rng.randf_range(-6.0, 6.0))
	_item(&"lata_conserva", Vector3(0.05, BENCH_TOP, -1.3), 20.0)
	_item(&"lata_conserva", Vector3(0.16, BENCH_TOP, -1.42))
	_item(&"botella_verde", Vector3(0.9, BENCH_TOP, -1.5))
	_item(&"caja_carton_pequena", Vector3(0.6, BENCH_TOP, -1.42), -8.0)
	_item(&"caja_madera", Vector3(1.62, FLOOR + 0.01, -1.3), 8.0)
	_item(&"caja_carton_grande", Vector3(1.72, FLOOR + 0.01, -0.45), 14.0)
	_item(&"bidon", Vector3(1.85, FLOOR + 0.01, 0.5))
	_item(&"escoba", Vector3(1.98, FLOOR + 0.02, 1.2), 90.0, -9.0)


func _item(item_id: StringName, where: Vector3, yaw: float = 0.0, lean: float = 0.0) -> void:
	var turn: Basis = Basis.from_euler(Vector3(0.0, deg_to_rad(yaw), deg_to_rad(lean)))
	items.spawn_item(item_id, Transform3D(turn, where))


func _build_room() -> void:
	_static = Node3D.new()
	_static.name = "Sala"
	add_child(_static)
	_place("deposito_sala", Vector3.ZERO)
	_place("persiana_abierta", Vector3(0.6, 0.0, 1.82))
	_place("lampara_colgante", Vector3(0.3, 2.9, -0.4))
	_place("banco_trabajo", Vector3(0.45, FLOOR, -1.36))
	_place("estanteria_metalica", Vector3(SHELF_X, FLOOR, -0.95), 90.0)
	_place("estanteria_metalica", Vector3(SHELF_X, FLOOR, 0.2), 90.0)
	# El pasillo de la estación, de momento un decorado con suelo (F2-12).
	var marble: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	marble.set_shader_parameter("albedo_color", Color("#a89f8a"))
	var granite: ShaderMaterial = load(BASE_MATERIAL).duplicate()
	granite.set_shader_parameter("albedo_color", Color("#6d6660"))
	_block(Vector3(12.0, 0.2, 6.0), Vector3(0.6, -0.1, 4.8), granite, true)
	_block(Vector3(12.0, 5.0, 0.3), Vector3(0.6, 2.5, 7.4), marble, true)
	for x: float in [-3.4, -1.0, 2.2, 4.6]:
		_block(Vector3(0.7, 5.0, 0.7), Vector3(x, 2.5, 4.6), marble, true)
		_block(Vector3(0.9, 0.25, 0.9), Vector3(x, 0.12, 4.6), granite, false)
	_block(Vector3(1.6, 0.45, 0.45), Vector3(0.6, 0.23, 5.6), granite, true)
	for x: float in [-5.5, 6.7]:
		_block(Vector3(0.3, 5.0, 6.0), Vector3(x, 2.5, 4.8), marble, true)


func _place(model: String, where: Vector3, yaw: float = 0.0) -> Node3D:
	var node: Node3D = load(MODELS_DIR + model + ".glb").instantiate()
	node.position = where
	node.rotation_degrees.y = yaw
	_static.add_child(node)
	return node


func _block(size: Vector3, where: Vector3, material: Material, solid: bool) -> void:
	var box: BoxMesh = BoxMesh.new()
	box.size = size
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.mesh = box
	mesh.material_override = material
	if not solid:
		mesh.position = where
		_static.add_child(mesh)
		return
	var body: StaticBody3D = StaticBody3D.new()
	body.position = where
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = size
	var collision: CollisionShape3D = CollisionShape3D.new()
	collision.shape = shape
	body.add_child(mesh)
	body.add_child(collision)
	_static.add_child(body)


func _add_help() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	layer.name = "Ayuda"
	add_child(layer)
	_label = Label.new()
	_label.text = HELP
	_label.position = Vector2(24, 16)
	_label.add_theme_color_override("font_color", Color("#f2e6cf"))
	_label.add_theme_color_override("font_outline_color", Color("#1b1a22"))
	_label.add_theme_constant_override("outline_size", 6)
	layer.add_child(_label)
	_label.visible = (
		DisplayServer.get_name() != "headless" and not OS.get_cmdline_user_args().has("--sin-ayuda")
	)
