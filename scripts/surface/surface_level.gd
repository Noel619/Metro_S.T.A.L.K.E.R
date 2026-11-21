class_name SurfaceLevel
extends Node3D
## La superficie jugable (Fase 3, docs/SUPERFICIE.md): la ciudad entera levantada
## desde el plano, con la luz de la hora del día y el tiempo del día, y los
## jugadores, que llegan a la esclusa del vestíbulo del metro (PLZ-06) por la
## escalera y vuelven por ella.
##
## Lo que cambia de una salida a otra (la compuerta, lo que se deja tirado) se
## guarda con la partida ([DepotWorld] con la clave "superficie" y [WorldItems] con
## "objetos_superficie") y queda aparcado mientras se está abajo.
##
## Para probarla sin pasar por el depósito se abre la escena directamente, con
## argumentos después de "--":
##   --chica          juegas con la chica
##   --hora=HH        empiezas a esa hora (por defecto, las 10)

const VESTIBULE_ID: String = "PLZ-06"
## El vestíbulo (tools/blender/recipes/singular_vestibulo.py): el centro de la rotonda
## respecto al del edificio, en el plano, y la dirección de la avenida.
const ROTUNDA_OFFSET: Vector2 = Vector2(-0.7, 5.0)
const AVENUE_DEGREES: float = 47.73
## La sala está tres escalones por encima de la acera; el muro de la compuerta, en x = 1,6
## del marco de la rotonda, y su hueco empieza en y = -0,8.
const HALL_FLOOR: float = 0.48
const LOCK_X: float = 1.6
const HATCH_Y0: float = -0.8
## La esclusa, en el marco de la rotonda: de la compuerta al fondo del foso de las
## escaleras y de lado a lado.
const LOCK_RANGE_X: Vector2 = Vector2(1.7, 22.0)
const LOCK_HALF_WIDTH: float = 3.0
## Donde aparece cada jugador al subir: en el rellano de la esclusa, mirando a la compuerta.
const ARRIVALS: Array[Vector2] = [
	Vector2(2.7, -1.5), Vector2(2.7, 1.5), Vector2(3.3, -0.5), Vector2(3.3, 0.6)
]
## El mirador (singular_vestibulo.py): la escalera de servicio sube por dentro del lado 12
## del tambor, apartada del muro, hasta su ventanal alto (por él se sale a la azotea del
## peristilo); la argolla de la cuerda está en el antepecho del lado 19, sobre la plaza, y
## la cuerda se aparta para librar la cornisa.
const BAYS: int = 20
const LADDER_BAY: int = 12
const LADDER_RADIUS: float = 8.47
const LADDER_TOP: float = 11.05
const ROPE_BAY: int = 19
const ROPE_RADIUS: float = 12.5
const PARAPET_TOP: float = 11.34
const ROPE_OFFSET: float = 0.55
## La marca de tu padre: una flecha de tiza en el muro, junto a la puerta, hacia el noreste.
const FATHER_BAY: int = 16
const FATHER_RADIUS: float = 9.59
const FATHER_HEIGHT: float = 1.9
const NORTH_EAST: Vector2 = Vector2(0.7071, 0.7071)
## Segundos que tienen que estar todos en la esclusa, con la compuerta cerrada, para bajar.
const LEAVE_SECONDS: float = 2.0
## Cada cuánto se rehace el cielo con la hora (segundos reales).
const SKY_SECONDS: float = 10.0
const DEFAULT_HOUR: float = 10.0
## Lo que se queda la imagen al morir todos antes de volver al depósito.
const GAME_OVER_SECONDS: float = 4.0
const HELP: String = (
	"WASD andar · Mayús correr · C agacharse · Q/E asomarse · Espacio saltar o encaramarse"
	+ " · T linterna · F usar · botón izquierdo (mantener): trabajar (el volante de la compuerta)"
	+ "\nPara volver: todos en la esclusa y la compuerta cerrada · F3 lo que perciben los perros"
	+ " · F1 ocultar · Esc soltar el ratón"
)

var plan: CityPlan
var city: City
var env: SurfaceEnv
var stimuli: Stimuli
var ripples: InkRipples
var tracks: Tracks
var world: DepotWorld
var items: WorldItems
var hatch: Hatch
var jauria: SurfacePack
var wounds: Wounds
var sites: SurfaceSites
var chalk: ChalkMarks
var lookout: Climbable
var rope_anchor: RopeAnchor

var _sync: LevelSync
var _players: Node3D
var _player_spawner: MultiplayerSpawner
var _variant: String = "chico"
## Dónde está puesto el modelo del vestíbulo (su origen es el centro del edificio).
var _vestibule: Transform3D = Transform3D.IDENTITY
var _sky_clock: float = 0.0
var _leave_clock: float = 0.0
## Se ha abierto la compuerta en esta visita: ya se puede volver.
var _armed: bool = false
var _label: Label


func _ready() -> void:
	_sync = LevelSync.new()
	_sync.name = "Sincronia"
	add_child(_sync)
	_variant = Sortie.local_variant
	var hour: float = DEFAULT_HOUR
	for arg: String in OS.get_cmdline_user_args():
		if arg == "--chica":
			_variant = "chica"
		elif arg.begins_with("--hora="):
			hour = clampf(float(arg.get_slice("=", 1)), 0.0, 23.9)
	if Sortie.arriving != Sortie.UP and multiplayer.is_server():
		# Abierta a mano para probarla: empieza a esa hora.
		GameState.minute = hour * 60.0
	plan = CityPlan.load_default()
	city = City.new()
	city.name = "Ciudad"
	add_child(city)
	if plan.is_loaded():
		city.build(plan)
	else:
		push_error("No se puede abrir el plano de la ciudad: " + plan.error)
	env = SurfaceEnv.new()
	env.name = "Tiempo"
	env.sun = get_node_or_null(^"Sol") as DirectionalLight3D
	add_child(env)
	stimuli = Stimuli.new()
	stimuli.name = "Estimulos"
	add_child(stimuli)
	ripples = InkRipples.new()
	ripples.name = "Ondas"
	add_child(ripples)
	tracks = Tracks.new()
	tracks.name = "Rastros"
	add_child(tracks)
	var debug: PerceptionDebug = PerceptionDebug.new()
	debug.name = "DepuracionPercepcion"
	add_child(debug)
	world = DepotWorld.new()
	world.name = "Mundo"
	world.save_key = "superficie"
	add_child(world)
	items = WorldItems.new()
	items.name = "Objetos"
	items.save_key = "objetos_superficie"
	add_child(items)
	wounds = Wounds.new()
	wounds.name = "Heridas"
	add_child(wounds)
	var loose: SurfaceItems = SurfaceItems.new()
	loose.setup(items)
	add_child(loose)
	chalk = ChalkMarks.new()
	chalk.setup(world)
	add_child(chalk)
	jauria = SurfacePack.new()
	jauria.setup(plan, city)
	add_child(jauria)
	_build_vestibule()
	sites = SurfaceSites.new()
	sites.setup(city, world, items)
	add_child(sites)
	_players = Node3D.new()
	_players.name = "Jugadores"
	add_child(_players)
	_player_spawner = MultiplayerSpawner.new()
	_player_spawner.name = "Generador"
	_player_spawner.spawn_function = _build_player
	_players.add_child(_player_spawner)
	_player_spawner.spawn_path = _player_spawner.get_path_to(_players)
	_add_help()
	_apply_sky()
	GameState.clock_running = true
	get_viewport().use_occlusion_culling = true
	if multiplayer.is_server():
		_start_as_host()
	else:
		_sync.report({"variant": _variant})


func _process(delta: float) -> void:
	_sky_clock += delta
	if _sky_clock >= SKY_SECONDS:
		_apply_sky()
	if multiplayer.is_server():
		_watch_leaving(delta)


func _unhandled_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_F1:
		_label.visible = not _label.visible


## El jugador de este equipo, si ya ha aparecido.
func local_player() -> Player:
	return Player.find(get_tree(), multiplayer.get_unique_id())


func players() -> Array[Player]:
	var found: Array[Player] = []
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		found.append(node as Player)
	return found


## Un punto del marco de la rotonda del vestíbulo (x hacia la escalera, y a la
## izquierda, z sobre la acera) en el mundo.
func vestibule_point(x: float, y: float, z: float = 0.0) -> Vector3:
	var plan_offset: Vector2 = ROTUNDA_OFFSET + Vector2(x, y).rotated(deg_to_rad(AVENUE_DEGREES))
	return _vestibule * Vector3(plan_offset.x, z, -plan_offset.y)


## Está dentro de la esclusa (del muro de la compuerta hacia la escalera).
func in_lock(position: Vector3) -> bool:
	var local: Vector3 = _vestibule.affine_inverse() * position
	var plan_offset: Vector2 = Vector2(local.x, -local.z) - ROTUNDA_OFFSET
	var frame: Vector2 = plan_offset.rotated(-deg_to_rad(AVENUE_DEGREES))
	return (
		frame.x >= LOCK_RANGE_X.x and frame.x <= LOCK_RANGE_X.y and absf(frame.y) <= LOCK_HALF_WIDTH
	)


## El rumbo de Godot para mirar hacia [param direction] del marco de la rotonda.
static func yaw_towards(direction: Vector2) -> float:
	var plan_direction: Vector2 = direction.rotated(deg_to_rad(AVENUE_DEGREES))
	return atan2(-plan_direction.x, plan_direction.y)


func _start_as_host() -> void:
	await _sync.wait()
	world.load_state({})
	SaveSystem.restore_parked()
	# Al llegar, la compuerta está cerrada: la cerró la guardia detrás del último.
	world.set_values("compuerta", {"abierta": false, "giro": 0.0})
	hatch.snap()
	# La primera vez en la partida: el botín y la flecha de tu padre.
	sites.seed_loot()
	_mark_from_father()
	_spawn_player(multiplayer.get_unique_id(), _variant)
	for peer: int in _sync.infos:
		_spawn_player(peer, String((_sync.infos[peer] as Dictionary).get("variant", "chico")))
	_sync.peer_ready.connect(
		func(peer: int, info: Dictionary) -> void:
			_spawn_player(peer, String(info.get("variant", "chico")))
	)
	_give_back_what_they_carried.call_deferred()
	jauria.start()
	sites.carve(jauria.nav)
	EventBus.game_over.connect(_on_game_over)
	Sortie.arrived()


## Han muerto todos: la partida se pierde y se vuelve al depósito, como el primer día.
func _on_game_over() -> void:
	if not multiplayer.is_server():
		return
	SaveSystem.delete_save()
	Sortie.carried.clear()
	await get_tree().create_timer(GAME_OVER_SECONDS).timeout
	Sortie.arriving = &""
	if Sortie.scene_changer.is_valid():
		Sortie.scene_changer.call(Sortie.DEPOT_SCENE)
	else:
		SceneRouter.go_to(Sortie.DEPOT_SCENE)


func _spawn_player(peer: int, variant: String) -> void:
	if Player.find(get_tree(), peer) != null or players().size() >= NetSession.MAX_PLAYERS:
		return
	var used: Array[int] = []
	for player: Player in players():
		used.append(player.slot)
	var slot: int = 0
	while used.has(slot):
		slot += 1
	_player_spawner.spawn({"peer": peer, "variant": variant, "slot": slot})


func _build_player(values: Dictionary) -> Node:
	var player: Player = Player.new()
	player.setup(values["peer"], values["variant"], values["slot"])
	player.surface_rules = true
	var spot: Vector2 = ARRIVALS[int(values["slot"]) % ARRIVALS.size()]
	player.position = vestibule_point(spot.x, spot.y, HALL_FLOOR + 0.05)
	player.rotation.y = yaw_towards(Vector2(-1.0, 0.0))
	if int(values["peer"]) == multiplayer.get_unique_id():
		var fear: Fear = Fear.new()
		fear.setup(player)
		player.add_child(fear)
	return player


## Lo que cada uno traía en las manos al subir, de vuelta a sus manos.
func _give_back_what_they_carried() -> void:
	await get_tree().create_timer(0.3).timeout
	for player: Player in players():
		var state: ItemState = Sortie.take_held(player.peer_id)
		if state != null:
			items.give_state(player, state)


## La compuerta: la hoja del modelo, que se mueve; y el sitio del vestíbulo.
func _build_vestibule() -> void:
	var building: Dictionary = city.buildings_by_id.get(VESTIBULE_ID, {})
	var leaf: MultiMeshInstance3D = city.find_child("vestibulo_compuerta", true, false)
	var leaf_mesh: Mesh = null
	if leaf != null and leaf.multimesh != null and leaf.multimesh.instance_count > 0:
		_vestibule = leaf.global_transform * leaf.multimesh.get_instance_transform(0)
		leaf_mesh = leaf.multimesh.mesh
		leaf.visible = false
	elif not building.is_empty():
		var center: Array = building["centro"]
		_vestibule = Transform3D(
			Basis(),
			CityPlan.to_world(Vector2(center[0], center[1]), float(building.get("cota", 0.0)))
		)
	# La esclusa no tiene más luz que la lámpara de pilas que dejó la guardia.
	var lamp: OmniLight3D = OmniLight3D.new()
	lamp.name = "LamparaEsclusa"
	lamp.light_color = Color(1.0, 0.82, 0.6)
	lamp.light_energy = 0.7
	lamp.omni_range = 6.0
	lamp.position = vestibule_point(2.8, 2.5, HALL_FLOOR + 2.5)
	add_child(lamp)
	hatch = Hatch.new()
	add_child(hatch)
	var hinge: Vector3 = vestibule_point(LOCK_X, HATCH_Y0)
	hatch.setup(leaf_mesh, _vestibule, hinge, deg_to_rad(AVENUE_DEGREES), HALL_FLOOR)
	world.state_changed.connect(
		func(id: String) -> void:
			if id == "compuerta" and hatch.is_open():
				_armed = true
	)
	_build_lookout()


## El mirador: la escalera de servicio de la sala a la azotea del peristilo y la argolla
## del antepecho, donde se puede atar una cuerda para bajar a la plaza.
func _build_lookout() -> void:
	var radial: Vector2 = Vector2.from_angle(TAU * LADDER_BAY / BAYS)
	var foot: Vector3 = vestibule_point(
		radial.x * LADDER_RADIUS, radial.y * LADDER_RADIUS, HALL_FLOOR
	)
	var inward: Vector3 = (
		vestibule_point(
			radial.x * (LADDER_RADIUS - 1.0), radial.y * (LADDER_RADIUS - 1.0), HALL_FLOOR
		)
		- foot
	)
	lookout = Climbable.make(
		Transform3D(_upright(inward), foot), Vector3(0.5, LADDER_TOP - HALL_FLOOR, 0.8)
	)
	lookout.name = "EscaleraServicio"
	add_child(lookout)
	var out: Vector2 = Vector2.from_angle(TAU * ROPE_BAY / BAYS)
	var edge: Vector3 = vestibule_point(out.x * ROPE_RADIUS, out.y * ROPE_RADIUS, PARAPET_TOP)
	var outward: Vector3 = (
		vestibule_point(out.x * (ROPE_RADIUS + 1.0), out.y * (ROPE_RADIUS + 1.0), PARAPET_TOP)
		- edge
	)
	rope_anchor = RopeAnchor.new()
	rope_anchor.offset = ROPE_OFFSET
	rope_anchor.landing_depth = ROPE_OFFSET + 1.0
	rope_anchor.setup("cuerda_vestibulo", Transform3D(_upright(outward), edge))
	add_child(rope_anchor)


## En el anfitrión, la primera vez: la flecha de tu padre en el muro del vestíbulo, junto
## a la puerta, señalando al noreste.
func _mark_from_father() -> void:
	if bool(world.value(ChalkMarks.WORLD_ID, "padre", false)):
		return
	var radial: Vector2 = Vector2.from_angle(TAU * FATHER_BAY / BAYS)
	var at: Vector3 = vestibule_point(
		radial.x * FATHER_RADIUS, radial.y * FATHER_RADIUS, FATHER_HEIGHT
	)
	var normal: Vector3 = (
		(
			vestibule_point(
				radial.x * (FATHER_RADIUS + 1.0), radial.y * (FATHER_RADIUS + 1.0), FATHER_HEIGHT
			)
			- at
		)
		. normalized()
	)
	# La flecha de la tiza apunta a lo largo del muro (arriba × normal); si el noreste queda
	# hacia el otro lado, se da la vuelta.
	var along: Vector3 = Vector3.UP.cross(normal)
	var north_east: Vector3 = Vector3(NORTH_EAST.x, 0.0, -NORTH_EAST.y)
	var turn: float = 0.0 if along.dot(north_east) >= 0.0 else PI
	chalk.place_mark(at, normal, ChalkMarks.SYMBOLS.find("flecha"), turn, true)
	world.set_value(ChalkMarks.WORLD_ID, "padre", true)


## Una base de pie (y arriba) con su z hacia [param forward] (en horizontal).
static func _upright(forward: Vector3) -> Basis:
	var z: Vector3 = Vector3(forward.x, 0.0, forward.z).normalized()
	return Basis(Vector3.UP.cross(z), Vector3.UP, z)


## En el anfitrión: si todos los vivos están en la esclusa con la compuerta cerrada
## (y se ha abierto en esta visita), se baja.
func _watch_leaving(delta: float) -> void:
	var everyone: Array[Player] = players()
	var ready_to_leave: bool = _armed and not hatch.is_open() and not everyone.is_empty()
	if ready_to_leave:
		for player: Player in everyone:
			if not in_lock(player.global_position):
				ready_to_leave = false
				break
	_leave_clock = _leave_clock + delta if ready_to_leave else 0.0
	if _leave_clock >= LEAVE_SECONDS:
		_leave_clock = -INF
		Sortie.local_variant = _variant
		Sortie.travel(get_tree(), true)


func _apply_sky() -> void:
	_sky_clock = 0.0
	var environment: WorldEnvironment = get_node_or_null(^"Ambiente") as WorldEnvironment
	var sun: DirectionalLight3D = get_node_or_null(^"Sol") as DirectionalLight3D
	if environment == null or sun == null:
		return
	Atmosphere.apply_hour(
		environment.environment, sun, GameState.hour(), env.weather.atmosphere_name()
	)


func _add_help() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	layer.name = "Ayuda"
	add_child(layer)
	_label = Label.new()
	_label.text = HELP
	_label.position = Vector2(16, 12)
	_label.add_theme_font_size_override("font_size", 14)
	_label.add_theme_color_override("font_color", Color(0.95, 0.92, 0.85))
	_label.add_theme_color_override("font_outline_color", Color(0.1, 0.09, 0.08))
	_label.add_theme_constant_override("outline_size", 4)
	layer.add_child(_label)
