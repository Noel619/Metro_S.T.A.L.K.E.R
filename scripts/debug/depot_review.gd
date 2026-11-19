extends Node3D
## Revisión del depósito jugable (Fase 2): la consigna y el trozo de estación
## vistos desde varias cámaras (grupo "capture_camera"), para las capturas de
## tools/capture.sh.
##
## Sin argumentos se ve el primer día: sucio, con la persiana atascada y las
## cajas del antiguo dueño. Con "--abierto" (después de "--"), el local ya
## limpio y abierto: el relojero en la ventanilla con su papelito, un encargo en
## el corcho, una radio a medio arreglar en el banco, la pila corriendo y la
## vendedora en su puesto. Con "--mochila", la mochila abierta junto a la mesa de
## planificar, llena del botín de una salida.

const LEVEL: String = "res://scenes/depot/deposito.tscn"
## [nombre, desde, hacia] de cada cámara.
const VIEWS: Array = [
	["sala", Vector3(-3.6, 1.65, 2.6), Vector3(2.5, 1.0, -2.5)],
	["mostrador", Vector3(1.6, 1.6, 0.6), Vector3(-0.3, 1.0, 3.2)],
	["fondo", Vector3(2.8, 1.6, 2.4), Vector3(-2.5, 1.0, -3.0)],
	["dormir", Vector3(0.6, 1.6, -1.9), Vector3(-3.0, 0.6, -3.3)],
	["banco", Vector3(2.4, 1.6, 0.4), Vector3(4.4, 0.9, -0.8)],
	["ventanilla", Vector3(1.4, 1.6, 6.2), Vector3(-0.2, 1.1, 3.5)],
	["puesto", Vector3(3.6, 1.6, 6.8), Vector3(6.8, 1.2, 4.2)],
	["pasillo", Vector3(-2.5, 1.7, 7.8), Vector3(-12.0, 1.4, 4.5)],
	["arcos", Vector3(0.5, 1.7, 4.6), Vector3(4.0, 1.4, 9.6)],
	["escaleras", Vector3(6.0, 1.7, 6.0), Vector3(15.0, 1.6, 6.0)],
	["cliente", Vector3(0.2, 1.55, 2.3), Vector3(0.0, 1.35, 4.3)],
	["telarana", Vector3(-2.6, 1.7, 1.6), Vector3(-4.38, 2.4, 3.0)],
	["encargos", Vector3(-2.2, 1.5, 1.8), Vector3(-3.0, 1.4, 3.25)],
	["mochila", Vector3(1.47, 0.95, -2.42), Vector3(1.45, 0.03, -3.0)],
	["planificar", Vector3(2.9, 1.6, -1.25), Vector3(1.75, 0.3, -3.05)],
]
## Lo que se mete en la mochila con "--mochila": una salida que ha ido bien.
const LOOT: Array[StringName] = [
	&"bateria_coche",
	&"gorro_orejeras",
	&"leche_condensada",
	&"lata_espadines",
	&"filtro",
	&"pila_petaca",
	&"manoplas",
	&"tarro_pepinillos",
	&"analgesicos",
	&"cinta_aislante",
	&"reloj_pulsera",
	&"velas",
	&"botiquin_militar",
]

var level: DepotLevel


func _ready() -> void:
	DepotLevel.continue_saved = false
	level = load(LEVEL).instantiate()
	add_child(level)
	for view: Array in VIEWS:
		var camera: Camera3D = Camera3D.new()
		camera.name = "Camara_" + String(view[0])
		camera.fov = 70.0
		add_child(camera)
		camera.add_to_group(&"capture_camera")
		camera.look_at_from_position(view[1], view[2])
	if OS.get_cmdline_user_args().has("--abierto"):
		_open_for_business.call_deferred()
	if OS.get_cmdline_user_args().has("--mochila"):
		_fill_backpack.call_deferred()
	_hide_player.call_deferred()


## La mochila abierta junto a la mesa de planificar, con el botín de una salida.
func _fill_backpack() -> void:
	await get_tree().physics_frame
	for item: Carryable in level.items.items():
		var backpack: Backpack = Backpack.of(item.body())
		if backpack == null:
			continue
		backpack.toggle()
		for item_id: StringName in LOOT:
			backpack.stash(ItemState.create(item_id, 0))
		return


## Deja solo una cámara para las capturas (con --call=RevisionDeposito:only:Camara_mochila).
func only(camera_name: String) -> void:
	for camera: Node in get_tree().get_nodes_in_group(&"capture_camera"):
		if camera.name != camera_name:
			camera.remove_from_group(&"capture_camera")


## Las manos de primera persona del jugador no se ven desde otras cámaras.
func _hide_player() -> void:
	var player: Player = level.local_player()
	if player != null and player.arms() != null:
		player.arms().visible = false


## El local a media mañana, con todo en marcha.
func _open_for_business() -> void:
	var world: DepotWorld = level.world
	for patch: DirtFixture in level.chores.dirt:
		world.set_value(patch.fixture_id, "suciedad", 0.0)
	for web: CobwebFixture in level.chores.cobwebs:
		world.set_value(web.fixture_id, "suciedad", 0.0)
	world.set_values("persiana", {"atascada": false, "abierta": true})
	world.set_values("lampara_mostrador", {"bombilla": "buena"})
	world.set_values("estufa", {"lena": 0.8, "encendida": true})
	world.set_value("pila", "abierta", true)
	for item: Carryable in level.items.items():
		if item.state.extra.has("contenido"):
			level.chores.open_box(item)
	GameState.minute = 10.5 * 60.0
	(
		GameState
		. add_job(
			{
				"client": "Lev Abrámovich, relojero",
				"client_id": "relojero",
				"item": "radio_bolsillo",
				"want": "Una radio de bolsillo que suene",
				"pay": 70,
				"deadline": GameState.day + 3,
				"hint": "Si la arreglas, vuelvo a por ella.",
				"since": GameState.day,
			}
		)
	)
	var bench: Transform3D = Transform3D(
		Basis.from_euler(Vector3(0.0, PI / 2.0, 0.0)), DepotRoom.BENCH_MAT + Vector3(0, 0.05, 0)
	)
	var radio: Carryable = level.items.spawn_with(
		&"radio_bolsillo", bench, {"paso": 2, "avance": 1.5}
	)
	radio.set_values({"condition": 0.3})
	var counter: Transform3D = Transform3D(
		Basis.IDENTITY, DepotRoom.DEAL_SPOT + Vector3(0.1, 0.05, 0.0)
	)
	# Algo que el relojero no busca: así sigue esperando en la ventanilla.
	level.items.spawn_with(&"lata_conserva", counter, {}).set_values({"price": 14})
	level.counter.start_visit([&"relojero", "comprar"])
	await get_tree().physics_frame
	if level.counter.customer != null:
		level.counter.customer.global_position = Station.WINDOW_SPOT
		level.counter.customer.walk([Station.WINDOW_SPOT])
