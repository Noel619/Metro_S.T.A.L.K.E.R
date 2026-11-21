class_name DepotLevel
extends Node3D
## El depósito jugable (Fase 2): la antigua consigna de la estación y el trozo
## de pasillo que se recorre (docs/DEPOSITO.md).
##
## Monta el local ([DepotRoom]), el pasillo ([Station]), el estado de sus cosas
## ([DepotWorld]) y los sistemas: el primer día ([DepotChores]), procesar lo que
## llega ([DepotWorkshop]), el mostrador y los clientes ([DepotCounter]), la
## estación ([DepotStation]) y el día ([DepotDay]). Pone los objetos sueltos y
## hace aparecer a los jugadores. El juego funciona siempre con un anfitrión: en
## solitario eres tú, sin invitados.
##
## Si hay una partida guardada, sigue donde se quedó; si no, empieza el primer
## día. Mientras no existan el menú y la firma de la escritura (Fase 5), la
## partida se abre con argumentos (después de "--") o con teclas de desarrollo:
##   --chica            juegas con la chica (por defecto, el chico)
##   --nueva            empiezas de cero aunque haya una partida guardada
##   --host             abres la partida a otros jugadores (F9)
##   --join=DIRECCION   te unes a la partida de otro (F10: en esta máquina)

const FLOOR: float = DepotRoom.FLOOR
## Donde aparece cada jugador: junto al catre, como al despertar.
const SPAWN_POINTS: Array[Vector3] = DepotDay.WAKE_SPOTS
const HELP: String = (
	"WASD andar · F coger, soltar y usar · botón izquierdo (mantener): trabajar con lo que llevas"
	+ " · botón derecho: acercar y girar · rueda: precio y billetes\n"
	+ "F9 abrir la partida · F10 unirse a una partida de esta máquina · F1 ocultar"
	+ " · Esc soltar el ratón"
)

## Seguir la partida guardada si la hay (los tests lo apagan).
static var continue_saved: bool = true

var items: WorldItems
var room: DepotRoom
var station: Station
var world: DepotWorld
var chores: DepotChores
var workshop: DepotWorkshop
var counter: DepotCounter
var services: DepotStation
var day: DepotDay
var exit: DepotExit
var _fresh: bool = false
var _sync: LevelSync
var _players: Node3D
var _player_spawner: MultiplayerSpawner
var _variant: String = "chico"
var _label: Label


func _ready() -> void:
	_sync = LevelSync.new()
	_sync.name = "Sincronia"
	add_child(_sync)
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
		elif arg == "--nueva":
			_fresh = true
	Sortie.local_variant = _variant
	world = DepotWorld.new()
	world.name = "Mundo"
	add_child(world)
	room = DepotRoom.new()
	room.name = "Local"
	add_child(room)
	station = Station.new()
	station.name = "Estacion"
	add_child(station)
	items = WorldItems.new()
	items.name = "Objetos"
	add_child(items)
	_build_systems()
	_players = Node3D.new()
	_players.name = "Jugadores"
	add_child(_players)
	_player_spawner = MultiplayerSpawner.new()
	_player_spawner.name = "Generador"
	_player_spawner.spawn_function = _build_player
	_players.add_child(_player_spawner)
	_player_spawner.spawn_path = _player_spawner.get_path_to(_players)
	_add_help()
	EventBus.game_over.connect(_on_game_over)
	NetSession.joined.connect(_on_joined)
	NetSession.peer_left.connect(_on_peer_left)
	NetSession.ended.connect(_on_session_ended)
	if NetSession.mode == NetSession.Mode.CLIENT:
		# Ya estaba conectado: se vuelve de la superficie con el anfitrión.
		_sync.report({"variant": _variant})
		return
	if not join_address.is_empty():
		NetSession.join(join_address)
		return
	if open_to_others and NetSession.mode == NetSession.Mode.SOLO:
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
	await _sync.wait()
	var returning: bool = Sortie.arriving == Sortie.DOWN
	var loaded: bool = false
	if returning:
		# Se vuelve de la superficie: el depósito como se dejó al subir.
		loaded = not SaveSystem.restore_parked().is_empty()
	if not loaded and continue_saved and not _fresh and SaveSystem.has_save():
		loaded = SaveSystem.load_game() == OK
	if not loaded:
		_new_game()
	GameState.clock_running = true
	GameState.push()
	_spawn_player(multiplayer.get_unique_id(), _variant, returning)
	for peer: int in _sync.infos:
		_spawn_player(
			peer, String((_sync.infos[peer] as Dictionary).get("variant", "chico")), returning
		)
	if not _sync.peer_ready.is_connected(_on_peer_ready):
		_sync.peer_ready.connect(_on_peer_ready)
	if returning:
		_give_back_what_they_carried.call_deferred()
	Sortie.arrived()


func _on_peer_ready(peer: int, info: Dictionary) -> void:
	_spawn_player(peer, String(info.get("variant", "chico")), true)


## Lo que cada uno traía en las manos al bajar, de vuelta a sus manos.
func _give_back_what_they_carried() -> void:
	await get_tree().create_timer(0.3).timeout
	for player: Player in players():
		var state: ItemState = Sortie.take_held(player.peer_id)
		if state != null:
			items.give_state(player, state)


## Se ha perdido la partida (muerte permanente): el depósito vuelve a estar como
## el primer día. Solo el anfitrión.
func _on_game_over() -> void:
	if not multiplayer.is_server():
		return
	if counter != null:
		counter.close_for_the_night()
	for item: Carryable in items.items():
		item.force_drop()
	world.load_state({})
	items.clear()
	_new_game()


## El primer día: el local como lo dejó el antiguo dueño.
func _new_game() -> void:
	SaveSystem.clear_parked()
	GameState.reset_for_new_game(GameState.player_name, _variant)
	_stock()
	EventBus.day_started.emit(GameState.day)


func _build_systems() -> void:
	var systems: Node3D = Node3D.new()
	systems.name = "Sistemas"
	add_child(systems)
	chores = DepotChores.new()
	chores.name = "PrimerDia"
	chores.room = room
	chores.station = station
	chores.items = items
	chores.world = world
	systems.add_child(chores)
	workshop = DepotWorkshop.new()
	workshop.name = "Taller"
	workshop.room = room
	workshop.items = items
	workshop.world = world
	systems.add_child(workshop)
	counter = DepotCounter.new()
	counter.name = "Mostrador"
	counter.room = room
	counter.station = station
	counter.items = items
	counter.world = world
	counter.shutter = chores.shutter
	systems.add_child(counter)
	services = DepotStation.new()
	services.name = "Servicios"
	services.room = room
	services.station = station
	services.items = items
	services.world = world
	services.counter = counter
	systems.add_child(services)
	day = DepotDay.new()
	day.name = "Dia"
	day.room = room
	day.counter = counter
	systems.add_child(day)
	exit = DepotExit.new()
	exit.name = "Subida"
	exit.station = station
	systems.add_child(exit)


func _spawn_player(peer: int, variant: String, at_the_stairs: bool = false) -> void:
	if Player.find(get_tree(), peer) != null or players().size() >= NetSession.MAX_PLAYERS:
		return
	var slot: int = _free_slot()
	_player_spawner.spawn(
		{"peer": peer, "variant": variant, "slot": slot, "escalera": at_the_stairs}
	)


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
	if bool(values.get("escalera", false)):
		player.position = DepotExit.arrival(int(values["slot"]))
		player.rotation.y = DepotExit.ARRIVAL_YAW
		return player
	var point: Vector3 = SPAWN_POINTS[int(values["slot"]) % SPAWN_POINTS.size()]
	player.position = point
	player.rotation.y = DepotDay.WAKE_YAW
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


## Lo que hay en el depósito el primer día: lo que dejó el antiguo dueño (sus
## cajas cerradas, algo de mercancía en las baldas, basura) y lo justo para
## empezar a limpiar.
func _stock() -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 7
	# En las baldas de la consigna: [objeto, balda, a lo largo, piso].
	var on_racks: Array[Array] = [
		[&"lata_conserva", 0, -0.6, 3],
		[&"lata_conserva", 0, -0.45, 3],
		[&"botella_marron", 0, 0.3, 2],
		[&"botella_verde", 0, 0.5, 2],
		[&"cubo", 1, 0.5, 0],
		[&"botella_verde", 2, -0.5, 1],
		[&"lata_conserva", 2, 0.4, 3],
	]
	for entry: Array in on_racks:
		_item(entry[0], _on_rack(entry[1], entry[2], entry[3]), 90.0 + rng.randf_range(-6.0, 6.0))
	# Las cajas del antiguo dueño, cerradas, con lo suyo dentro.
	_box(
		&"caja_carton",
		_on_rack(0, -0.2, 1),
		[
			_content(&"bombilla"),
			_content(&"cerillas"),
			_content(&"vendas", 0.9),
			_content(&"lata_conserva", 0.8),
		]
	)
	_box(
		&"caja_carton_pequena",
		_on_rack(1, -0.3, 1),
		[
			_content(&"destornillador", 0.8),
			_content(&"cepillo_alambre", 0.7),
			_content(&"navaja", 0.7),
			_content(&"cuerda", 0.6),
		]
	)
	_box(
		&"caja_carton_grande",
		Vector3(-0.3, FLOOR + 0.01, -0.9),
		[
			_content(&"despertador", 0.85),
			_content(&"radio_bolsillo", 0.3, 0.0, 0.05),
			_content(&"linterna", 0.35),
			_content(&"botas", 0.35, 0.1),
			_content(&"aguja_hilo"),
		]
	)
	_box(
		&"caja_madera",
		Vector3(2.4, FLOOR + 0.01, -1.1),
		[
			_content(&"mascara", 0.7, 0.7),
			_content(&"chatarra_cobre", 1.0, 0.35),
			_content(&"botiquin", 0.9),
			_content(&"brujula", 0.8),
		]
	)
	# Junto a la mesa de planificación, la caja con lo que tu padre usaba para subir.
	_box(
		&"caja_madera",
		Vector3(1.1, FLOOR + 0.01, -3.3),
		[
			_content(&"ganzuas", 0.9),
			_content(&"tiza"),
			_content(&"cizalla", 0.85),
			_content(&"podometro", 0.9),
		],
		{"padre": true}
	)
	# Para trabajar: la escoba, la fregona, el cepillo, la palanca, el dosímetro y
	# la leña.
	var bench: Vector3 = DepotRoom.BENCH_CENTER
	_item(&"palanca", Vector3(bench.x - 0.1, DepotRoom.BENCH_TOP + 0.02, bench.z - 0.55), 80.0)
	_item(
		&"lata_conserva", Vector3(bench.x - 0.15, DepotRoom.BENCH_TOP + 0.01, bench.z - 0.1), 20.0
	)
	_item(&"dosimetro", Vector3(bench.x - 0.05, DepotRoom.BENCH_TOP + 0.01, bench.z + 0.5), -90.0)
	_item(&"escoba", Vector3(2.9, FLOOR + 0.02, 2.75), 90.0, -90.0)
	_item(&"fregona", Vector3(3.6, FLOOR + 0.02, 2.25), 0.0, 90.0)
	_item(&"cepillo", Vector3(3.75, FLOOR + 0.02, 1.25), 25.0)
	_item(&"lena", Vector3(-0.7, FLOOR + 0.01, -3.35), 10.0)
	_item(&"lena", Vector3(-0.7, FLOOR + 0.2, -3.3), -8.0)
	_item(&"bidon", Vector3(3.4, FLOOR + 0.01, -2.9))
	_item(&"caja_madera", Vector3(-4.0, FLOOR + 0.01, -2.0), 90.0)
	_item(&"radio", Vector3(-4.0, FLOOR + 0.55, -2.0), 90.0)
	# La basura que hay por el suelo.
	for entry: Array in [
		[&"papeles", Vector3(-1.4, FLOOR + 0.02, 1.9)],
		[&"papeles", Vector3(2.0, FLOOR + 0.02, -0.2)],
		[&"trapo", Vector3(-2.7, FLOOR + 0.02, -0.9)],
		[&"botella_rota", Vector3(1.2, FLOOR + 0.02, 2.0)],
		[&"lata_vacia", Vector3(0.3, FLOOR + 0.02, 0.9)],
		[&"lata_vacia", Vector3(-3.4, FLOOR + 0.02, 1.0)],
	]:
		_item(entry[0], entry[1], rng.randf_range(0.0, 360.0))


## Un sitio en una balda: [param rack] (de [constant DepotRoom.RACKS]), a lo
## largo de ella y en su piso [param level].
func _on_rack(rack_index: int, along: float, level: int) -> Vector3:
	var rack: Vector3 = DepotRoom.RACKS[rack_index]
	return Vector3(rack.x, FLOOR + DepotRoom.RACK_LEVELS[level] + 0.035, rack.z + along)


static func _content(
	item_id: StringName, condition: float = 1.0, contamination: float = 0.0, wear: float = 0.0
) -> Dictionary:
	var entry: Dictionary = {
		"id": String(item_id), "condition": condition, "contamination": contamination
	}
	if wear > 0.0:
		entry["extra"] = {"desgaste": wear}
	return entry


func _box(item_id: StringName, where: Vector3, contents: Array, more: Dictionary = {}) -> void:
	var extra: Dictionary = {"contenido": contents}
	extra.merge(more)
	items.spawn_with(
		item_id, Transform3D(Basis.from_euler(Vector3(0.0, PI / 2.0, 0.0)), where), extra
	)


func _item(item_id: StringName, where: Vector3, yaw: float = 0.0, lean: float = 0.0) -> void:
	var turn: Basis = Basis.from_euler(Vector3(0.0, deg_to_rad(yaw), deg_to_rad(lean)))
	items.spawn_item(item_id, Transform3D(turn, where))


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
