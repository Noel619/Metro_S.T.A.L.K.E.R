class_name SurfaceSandbox
extends Node3D
## El patio de pruebas de la superficie (F3-01): el patio de Los Bloques de los
## dioramas, para andar por él. Sirve para probar cómo se mueve el jugador fuera
## (agacharse, asomarse, correr mientras dura el aliento) y lo que suenan sus
## pasos en la nieve, en el hielo y sobre cristales rotos, con botín tirado por
## el patio y la mochila en el banco. No es la Zona 1 (F3-14): es un banco de
## pruebas, y no se guarda nada.
##
## Funciona en solitario y con otros jugadores, como el depósito: F9 abre la
## partida y F10 se une a una de esta máquina (o, después de "--", --host y
## --join=DIRECCION; --chica para jugar con la chica). Mientras no haya quien
## oiga los pasos (F3-09), cada uno se dibuja como un círculo rojo hasta donde
## llegaría ([NoiseRings]).

const DIORAMA: PackedScene = preload("res://scenes/style/diorama_patio.tscn")
const DEBUG_PANEL: Script = preload("res://scripts/debug/debug_panel.gd")
## Donde aparece cada jugador: a la entrada del patio, de cara a los bloques.
const SPAWN_POINTS: Array[Vector3] = [
	Vector3(1.2, 0.05, 9.0),
	Vector3(2.2, 0.05, 9.4),
	Vector3(0.2, 0.05, 9.4),
	Vector3(3.2, 0.05, 9.8),
]
## El suelo del patio mide 46 m: un poco antes del borde hay una pared que no se ve.
const EDGE: float = 22.5
## Si alguien se cae del mundo, vuelve a la entrada.
const FALL_LIMIT: float = -20.0
## Lo que se pisa y suena distinto: [tipo de suelo, centro, radio]. El resto del
## patio es nieve.
const PATCHES: Array[Array] = [
	[&"cristales", Vector3(-10.6, 0.0, -4.3), 1.9],
	[&"nieve_helada", Vector3(2.2, 0.0, 4.6), 1.6],
]
const GLASS_COLOR: Color = Color("#1f2228")
const ICE_COLOR: Color = Color("#a9b8bd")
## El botín, cerca de donde se encontraría: [objeto, junto a qué, dónde respecto
## a eso]. Lo del coche, a su lado; lo del quiosco, en la repisa de la ventanilla;
## la mochila, en el banco; lo que cayó de los pisos, al pie del bloque.
const LOOT: Array[Array] = [
	[&"mochila", &"banco_parque", Vector3(-0.4, 0.0, 0.0)],
	[&"taza_esmaltada", &"banco_parque", Vector3(0.55, 0.0, 0.05)],
	[&"bateria_coche", &"coche", Vector3(-1.0, 0.0, -1.35)],
	[&"llave_inglesa", &"coche", Vector3(0.2, 0.0, -1.45)],
	[&"radio_bolsillo", &"coche", Vector3(-0.35, 0.0, -1.6)],
	[&"gorro_orejeras", &"coche", Vector3(-1.85, 0.0, -1.4)],
	[&"chatarra_cobre", &"coche_quemado", Vector3(-1.2, 0.0, 1.45)],
	[&"palanca", &"coche_quemado", Vector3(0.3, 0.0, 1.6)],
	[&"linterna", &"coche_quemado", Vector3(1.3, 0.0, 1.35)],
	[&"cerillas", &"quiosco", Vector3(-0.55, 0.0, 1.07)],
	[&"lata_espadines", &"quiosco", Vector3(-0.3, 0.0, 1.07)],
	[&"pila_petaca", &"quiosco", Vector3(-0.06, 0.0, 1.07)],
	[&"leche_condensada", &"quiosco", Vector3(-0.9, 0.0, 1.7)],
	[&"botella_verde", &"quiosco", Vector3(0.7, 0.0, 1.6)],
	[&"botella_marron", &"contenedor", Vector3(-0.1, 0.0, 0.95)],
	[&"lata_conserva", &"contenedor", Vector3(-0.65, 0.0, 0.85)],
	[&"tarro_pepinillos", &"contenedor", Vector3(0.55, 0.0, 1.0)],
	[&"martillo", &"escombros_grande", Vector3(-3.75, 0.0, 0.6)],
	[&"clavos", &"escombros_grande", Vector3(-3.6, 0.0, -0.5)],
	[&"samovar", &"bloque_paneles", Vector3(-4.0, 0.0, 1.6)],
	[&"despertador", &"bloque_paneles", Vector3(-2.6, 0.0, 1.9)],
	[&"velas", &"bloque_paneles", Vector3(0.8, 0.0, 1.8)],
	[&"manoplas", &"bloque_paneles", Vector3(8.2, 0.0, 1.8)],
]
const HELP: String = (
	"WASD andar · Mayús correr (mientras dure el aliento) · C o Ctrl agacharse · Q E asomarse"
	+ " · T linterna\n"
	+ "F coger, soltar y usar · botón izquierdo (mantener): abrir la mochila"
	+ " · botón derecho: acercar y girar\n"
	+ "F1 panel (hora, clima, miedo) · F2 círculos de ruido · F3 ocultar esto"
	+ " · F5 reponer el botín · F9 abrir la partida · F10 unirse · Esc soltar el ratón"
)
const GAITS: Dictionary = {
	SurfaceMotion.Gait.STILL: "quieto",
	SurfaceMotion.Gait.CROUCH: "agachado",
	SurfaceMotion.Gait.WALK: "andando",
	SurfaceMotion.Gait.RUN: "corriendo",
}

var items: WorldItems
var diorama: Node3D
var rings: NoiseRings
var _players: Node3D
var _player_spawner: MultiplayerSpawner
var _variant: String = "chico"
var _help: Label
var _status: Label
var _last_noise: float = 0.0


func _ready() -> void:
	StyleDirector.set_zone(StyleDirector.ZONE_SURFACE, true)
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
	diorama = DIORAMA.instantiate()
	diorama.name = "Patio"
	add_child(diorama)
	# Las cámaras de las capturas del diorama sobran: aquí se mira con los ojos.
	for camera: Node in diorama.find_children("*", "Camera3D", true, false):
		camera.free()
	_build_ground()
	_build_edges()
	items = WorldItems.new()
	items.name = "Objetos"
	add_child(items)
	rings = NoiseRings.new()
	rings.name = "Ruidos"
	add_child(rings)
	_players = Node3D.new()
	_players.name = "Jugadores"
	add_child(_players)
	_player_spawner = MultiplayerSpawner.new()
	_player_spawner.name = "Generador"
	_player_spawner.spawn_function = _build_player
	_players.add_child(_player_spawner)
	_player_spawner.spawn_path = _player_spawner.get_path_to(_players)
	_build_overlay()
	EventBus.noise_made.connect(_on_noise)
	NetSession.joined.connect(_on_joined)
	NetSession.peer_left.connect(_on_peer_left)
	NetSession.ended.connect(_on_session_ended)
	if not join_address.is_empty():
		NetSession.join(join_address)
		return
	if open_to_others:
		NetSession.host()
	_start_as_host()


func _exit_tree() -> void:
	if EventBus.noise_made.is_connected(_on_noise):
		EventBus.noise_made.disconnect(_on_noise)


func _unhandled_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_F2:
			rings.visible = not rings.visible
			rings.clear()
		KEY_F3:
			_help.visible = not _help.visible
			_status.visible = _help.visible
		KEY_F5:
			restock()
		KEY_F9:
			if NetSession.mode == NetSession.Mode.SOLO:
				NetSession.host()
		KEY_F10:
			if NetSession.mode == NetSession.Mode.SOLO:
				_clear_world()
				NetSession.join("127.0.0.1")


func _physics_process(_delta: float) -> void:
	for player: Player in players():
		if player.is_local() and player.global_position.y < FALL_LIMIT:
			player.move_to(SPAWN_POINTS[player.slot % SPAWN_POINTS.size()], 0.0)


func _process(_delta: float) -> void:
	var player: Player = local_player()
	if player == null or not _status.visible:
		return
	var gait: SurfaceMotion.Gait = SurfaceMotion.gait_of(
		player.move_speed, player.crouching, player.running
	)
	var ground: StringName = player.ground_kind()
	_status.text = (
		"aliento %d %%%s · %s · %s · último paso: %.2f (%.0f m)"
		% [
			roundi(player.motion.breath * 100.0),
			" (sin aliento)" if player.motion.winded else "",
			GAITS[gait],
			String(ground) if ground != &"" else "suelo normal",
			_last_noise,
			_last_noise * SurfaceMotion.METERS_PER_LOUDNESS,
		]
	)


## El jugador de este equipo, si ya ha aparecido.
func local_player() -> Player:
	return Player.find(get_tree(), multiplayer.get_unique_id())


func players() -> Array[Player]:
	var found: Array[Player] = []
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		found.append(node as Player)
	return found


## Vuelve a poner el botín como al principio (lo que se lleva en las manos se
## queda). Solo el anfitrión.
func restock() -> void:
	if not multiplayer.is_server():
		return
	for item: Carryable in items.items():
		if not item.is_held():
			items.remove_item(item)
	for entry: Array in LOOT:
		_drop_item(entry[0], entry[1], entry[2])


## Coloca al jugador local para una captura (tools/capturas_docs.sh): "patio",
## "asomado" (detrás del quiosco, asomándose) o "ruido" (desde arriba, con los
## círculos de ruido de cada forma de andar).
func view(name_of_view: String) -> void:
	var player: Player = local_player()
	if player == null:
		return
	_help.visible = false
	_status.visible = false
	match name_of_view:
		"asomado":
			# Pegado a la pared oeste del quiosco, junto a la esquina de atrás, y
			# asomándose por ella hacia el patio.
			var kiosk: Transform3D = _anchor(&"quiosco")
			player.move_to(kiosk * Vector3(-1.77, 0.05, -0.8), kiosk.basis.get_euler().y - PI / 2.0)
			player.set_crouching(true)
			player.scripted_lean = -1.0
		"ruido":
			_noise_overview(player)
		_:
			# Entre el banco (con la mochila) y el coche (con lo suyo al lado).
			player.move_to(Vector3(1.0, 0.05, 1.8), deg_to_rad(-36.0))
			player.head_pitch = deg_to_rad(-16.0)


func _start_as_host() -> void:
	_spawn_player(multiplayer.get_unique_id(), _variant)
	# Lo que hay en el patio entra en la física en el siguiente paso: hasta
	# entonces, el botín no encontraría dónde apoyarse.
	await get_tree().physics_frame
	restock()


## Un invitado pide su jugador al anfitrión cuando ya tiene la escena cargada.
@rpc("any_peer", "call_remote", "reliable")
func request_player(variant: String) -> void:
	if multiplayer.is_server():
		_spawn_player(multiplayer.get_remote_sender_id(), variant)


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
	player.surface = true
	player.position = SPAWN_POINTS[int(values["slot"]) % SPAWN_POINTS.size()]
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


## Se ha cortado la conexión: vuelta a jugar en solitario.
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


func _on_noise(_where: Vector3, loudness: float, source: Node) -> void:
	if source == local_player():
		_last_noise = loudness


## Dónde está [param model] en el patio del diorama (o el origen, si no está).
func _anchor(model: StringName) -> Transform3D:
	var node: Node3D = diorama.find_child(String(model), true, false) as Node3D
	return node.global_transform if node != null else Transform3D.IDENTITY


## Deja [param item_id] junto a [param model], en [param offset] respecto a él,
## sobre lo primero que haya debajo (el suelo, una repisa, el asiento del banco).
func _drop_item(item_id: StringName, model: StringName, offset: Vector3) -> void:
	var spot: Vector3 = _anchor(model) * offset
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = hash(String(item_id)) ^ hash(String(model))
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		Vector3(spot.x, 6.0, spot.z), Vector3(spot.x, -1.0, spot.z), 1 << 0
	)
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	var floor_y: float = (hit["position"] as Vector3).y if not hit.is_empty() else 0.0
	var turn: Basis = Basis(Vector3.UP, rng.randf_range(0.0, TAU))
	items.spawn_item(item_id, Transform3D(turn, Vector3(spot.x, floor_y + 0.02, spot.z)))


## El suelo del patio es nieve, y encima hay manchas que suenan distinto: unos
## cristales rotos junto al coche quemado y un charco helado.
func _build_ground() -> void:
	for node: Node in diorama.find_children("suelo_patio*", "StaticBody3D", true, false):
		node.set_meta(SurfaceMotion.GROUND_META, &"nieve")
	for entry: Array in PATCHES:
		var kind: StringName = entry[0]
		var center: Vector3 = entry[1]
		var radius: float = entry[2]
		var patch: Area3D = Area3D.new()
		patch.name = "Suelo_%s" % kind
		patch.collision_layer = 1 << 5
		patch.collision_mask = 0
		patch.monitoring = false
		patch.monitorable = false
		patch.set_meta(SurfaceMotion.GROUND_META, kind)
		var shape: CollisionShape3D = CollisionShape3D.new()
		var cylinder: CylinderShape3D = CylinderShape3D.new()
		cylinder.radius = radius
		cylinder.height = 0.2
		shape.shape = cylinder
		patch.add_child(shape)
		patch.position = center
		add_child(patch)
		if kind == &"cristales":
			patch.add_child(_glass_shards(radius))
		else:
			patch.add_child(_ice_sheet(radius))


## Cristales rotos tirados por la nieve.
static func _glass_shards(radius: float) -> MultiMeshInstance3D:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 31
	var shard: PrismMesh = PrismMesh.new()
	shard.size = Vector3(0.07, 0.11, 0.004)
	shard.left_to_right = 0.3
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = GLASS_COLOR
	material.roughness = 0.15
	material.metallic_specular = 0.9
	shard.material = material
	var multimesh: MultiMesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = shard
	multimesh.instance_count = 160
	for index: int in multimesh.instance_count:
		var distance: float = radius * sqrt(rng.randf()) * 0.95
		var angle: float = rng.randf_range(0.0, TAU)
		var size: float = rng.randf_range(0.5, 1.6)
		var basis: Basis = Basis.from_euler(
			Vector3(PI / 2.0 + rng.randf_range(-0.25, 0.25), rng.randf_range(0.0, TAU), 0.0)
		)
		var where: Vector3 = Vector3(cos(angle) * distance, 0.03, sin(angle) * distance)
		multimesh.set_instance_transform(
			index, Transform3D(basis.scaled(Vector3.ONE * size), where)
		)
	var shards: MultiMeshInstance3D = MultiMeshInstance3D.new()
	shards.name = "Cristales"
	shards.multimesh = multimesh
	return shards


## Un charco helado: una lámina lisa y clara sobre la nieve.
static func _ice_sheet(radius: float) -> MeshInstance3D:
	var sheet: CylinderMesh = CylinderMesh.new()
	sheet.top_radius = radius
	sheet.bottom_radius = radius
	sheet.height = 0.03
	sheet.radial_segments = 28
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = ICE_COLOR
	material.roughness = 0.08
	sheet.material = material
	var ice: MeshInstance3D = MeshInstance3D.new()
	ice.name = "Hielo"
	ice.mesh = sheet
	ice.position.y = 0.02
	return ice


## Paredes que no se ven en el borde del patio.
func _build_edges() -> void:
	var edges: StaticBody3D = StaticBody3D.new()
	edges.name = "Bordes"
	add_child(edges)
	for side: Vector3 in [Vector3.RIGHT, Vector3.LEFT, Vector3.FORWARD, Vector3.BACK]:
		var shape: CollisionShape3D = CollisionShape3D.new()
		var box: BoxShape3D = BoxShape3D.new()
		box.size = Vector3(1.0, 6.0, EDGE * 2.0 + 2.0)
		shape.shape = box
		shape.position = side * (EDGE + 0.5) + Vector3.UP * 3.0
		shape.rotation.y = 0.0 if side.x != 0.0 else PI / 2.0
		edges.add_child(shape)


## Vista desde arriba de lo que se oye un paso en la nieve: agachado, andando y
## corriendo (de izquierda a derecha, delante) y, al fondo, andando sobre los
## cristales rotos, que suena más que correr por la nieve.
func _noise_overview(player: Player) -> void:
	rings.frozen = true
	rings.clear()
	var steps: Array[Array] = [
		[SurfaceMotion.Gait.CROUCH, Vector3(-5.5, 0.0, 6.5), &"nieve"],
		[SurfaceMotion.Gait.WALK, Vector3(-1.5, 0.0, 6.5), &"nieve"],
		[SurfaceMotion.Gait.RUN, Vector3(6.0, 0.0, 6.5), &"nieve"],
		[SurfaceMotion.Gait.WALK, PATCHES[0][1], &"cristales"],
	]
	for step: Array in steps:
		var ground: float = SurfaceMotion.ground_loudness(step[2])
		rings.show_noise(step[1], SurfaceMotion.step_noise(step[0], 0.0, 0.0, ground))
	var camera: Camera3D = Camera3D.new()
	camera.name = "CamaraRuido"
	camera.fov = 60.0
	add_child(camera)
	camera.global_position = Vector3(-1.5, 24.0, 17.0)
	camera.look_at(Vector3(-2.0, 0.0, 1.0))
	camera.make_current()
	player.move_to(Vector3(6.0, 0.05, 6.5), 0.0)


func _build_overlay() -> void:
	var panel: CanvasLayer = DEBUG_PANEL.new()
	panel.name = "PanelDepuracion"
	add_child(panel)
	panel.call(&"set_target", diorama)
	var layer: CanvasLayer = CanvasLayer.new()
	layer.name = "Ayuda"
	add_child(layer)
	_help = _label(Vector2(24, 16))
	_help.text = HELP
	layer.add_child(_help)
	_status = _label(Vector2(24, 100))
	layer.add_child(_status)
	var shown: bool = (
		DisplayServer.get_name() != "headless" and not OS.get_cmdline_user_args().has("--sin-ayuda")
	)
	_help.visible = shown
	_status.visible = shown


static func _label(where: Vector2) -> Label:
	var label: Label = Label.new()
	label.position = where
	label.add_theme_color_override("font_color", Color("#f2e6cf"))
	label.add_theme_color_override("font_outline_color", Color("#1b1a22"))
	label.add_theme_constant_override("outline_size", 6)
	return label
