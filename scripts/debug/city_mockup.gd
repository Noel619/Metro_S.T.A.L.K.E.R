extends Node3D
## La maqueta automática de la ciudad (F3-15): herramienta de desarrollo, no el juego.
##
## Levanta Tumansk entera desde el plano (data/ciudad/) en volúmenes sencillos para
## probar recorridos, vistas, sectores de carga y rendimiento antes de construir.
##
## Tab: andar o volar · ratón: mirar (clic para capturarlo, Esc para soltarlo) · WASD,
## Mayús, C, Espacio: moverse · 1-9 y 0: vistas (con Mayús, las de la red de tránsito) ·
## R: recorrer la ruta siguiente (Mayús+R, la anterior; Retroceso, parar; + y -, más o
## menos deprisa) · F2: rutas · F3: sectores y zonas · F4: hitos a la vista · N: niebla ·
## O: oclusión · P: tinta · L: linterna · B: prueba de rendimiento · V: comprobar los hitos
## en toda la ciudad · F1: hora, clima y estilo · F9: oculta el texto.

## Vistas fijas: posición y punto al que miran, en el plano (x, y) y en metros sobre lo
## que se pisa (z). Son también las cámaras de las capturas de revisión. "niebla" y "capas"
## se aplican mientras la vista es la cámara activa.
const VIEWS: Array[Dictionary] = [
	{
		"name": "salida",
		"title": "La salida del metro, hacia la plaza",
		"from": Vector3(358.0, 302.0, 1.7),
		"to": Vector3(490.0, 395.0, 28.0),
		"fov": 64.0,
	},
	{
		"name": "avenida",
		"title": "La avenida, hacia el puente y la Casa de los Sóviets",
		"from": Vector3(503.6, 411.7, 1.7),
		"to": Vector3(1069.0, 1039.7, 45.0),
		"fov": 58.0,
	},
	{
		"name": "bloques",
		"title": "Los Bloques y la Torre",
		"from": Vector3(200.0, 420.0, 1.7),
		"to": Vector3(300.0, 604.0, 26.0),
		"fov": 62.0,
	},
	{
		"name": "rio",
		"title": "El Muelle Sur: el río helado y la loma",
		"from": Vector3(500.0, 616.0, 1.7),
		"to": Vector3(760.0, 900.0, 22.0),
		"fov": 60.0,
	},
	{
		"name": "puente",
		"title": "El Puente del Progreso y su vano hundido",
		"from": Vector3(686.0, 618.0, 1.7),
		"to": Vector3(804.7, 746.1, -4.0),
		"fov": 62.0,
	},
	{
		"name": "centro",
		"title": "Desde lo alto de la Escalinata se domina la orilla sur",
		"from": Vector3(939.0, 891.0, 1.7),
		"to": Vector3(630.7, 552.9, -2.0),
		"fov": 62.0,
	},
	{
		"name": "industria",
		"title": "La zona industrial y la central",
		"from": Vector3(950.0, 300.0, 1.7),
		"to": Vector3(1420.0, 440.0, 40.0),
		"fov": 62.0,
	},
	{
		"name": "zona_cero",
		"title": "La Zona Cero: el Edificio Partido y el cráter",
		"from": Vector3(1180.0, 900.0, 1.7),
		"to": Vector3(1292.0, 985.0, 22.0),
		"fov": 62.0,
	},
	{
		"name": "aerea",
		"title": "La ciudad entera, sin niebla",
		"from": Vector3(-170.0, -280.0, 400.0),
		"to": Vector3(820.0, 640.0, 0.0),
		"fov": 50.0,
		"niebla": "sin",
	},
	{
		"name": "rutas",
		"title": "Las rutas y los sectores de la orilla sur, sin niebla",
		"from": Vector3(330.0, -160.0, 520.0),
		"to": Vector3(560.0, 560.0, 0.0),
		"fov": 55.0,
		"niebla": "sin",
		"capas": ["rutas", "sectores"],
	},
	{
		"name": "escalinata",
		"title": "La Escalinata desde el rellano de abajo",
		"from": Vector3(858.2, 805.6, 1.7),
		"to": Vector3(927.8, 882.9, 1.6),
		"fov": 62.0,
	},
	{
		"name": "esquina",
		"title": "Un cruce del Barrio Obrero: bordillos, pasos de cebra y sumideros",
		"from": Vector3(553.0, 198.0, 1.6),
		"to": Vector3(571.0, 214.0, -0.6),
		"fov": 66.0,
	},
	{
		"name": "vano",
		"title": "El tablero del puente se corta en el vano hundido",
		"from": Vector3(738.9, 664.1, 1.7),
		"to": Vector3(767.9, 705.3, -3.0),
		"fov": 62.0,
	},
	{
		"name": "loma",
		"title": "Las escaleras de la loma, del Muelle Norte al Bulevar",
		"from": Vector3(1099.0, 801.5, 1.7),
		"to": Vector3(1118.0, 862.0, 2.5),
		"fov": 60.0,
	},
	{
		"name": "estacion",
		"title": "Los andenes de la estación, entre la vía principal y las de andén",
		"from": Vector3(132.0, 28.0, 1.7),
		"to": Vector3(330.0, 33.0, -0.4),
		"fov": 62.0,
	},
	{
		"name": "playa",
		"title": "La playa de vías desde su entrada",
		"from": Vector3(872.0, 40.0, 2.4),
		"to": Vector3(1010.0, 110.0, -1.0),
		"fov": 62.0,
	},
	{
		"name": "paso_nivel",
		"title": "Un paso a nivel del apartadero de la fábrica",
		"from": Vector3(920.6, 156.0, 1.7),
		"to": Vector3(925.6, 182.0, -0.4),
		"fov": 62.0,
	},
	{
		"name": "desvio",
		"title": "Un desvío del escape de la playa de vías: agujas, corazón y palanca",
		"from": Vector3(927.0, 66.0, 1.7),
		"to": Vector3(950.1, 73.6, -0.5),
		"fov": 62.0,
	},
	{
		"name": "topes",
		"title": "El tope al final de una vía de la playa",
		"from": Vector3(1224.0, 111.2, 1.7),
		"to": Vector3(1245.0, 109.6, 0.4),
		"fov": 62.0,
	},
	{
		"name": "tranvia",
		"title": "El tranvía por la mediana de la Avenida",
		"from": Vector3(559.6, 482.6, 1.7),
		"to": Vector3(597.0, 523.0, -0.3),
		"fov": 62.0,
	},
	{
		"name": "socavon",
		"title": "El socavón de la avenida: la calle cayó al túnel de la línea 1",
		"from": Vector3(538.0, 444.0, 1.7),
		"to": Vector3(553.5, 461.2, 2.0),
		"fov": 64.0,
	},
	{
		"name": "socavon_galeria",
		"title": "La galería de la calefacción, hundida frente a la fábrica",
		"from": Vector3(1096.5, 311.0, 1.7),
		"to": Vector3(1103.0, 317.0, 0.3),
		"fov": 64.0,
	},
	{
		"name": "socavon_agua",
		"title": "Una tubería del agua reventó por la helada y se llevó la calle",
		"from": Vector3(343.2, 446.2, 1.7),
		"to": Vector3(345.0, 452.0, 0.3),
		"fov": 64.0,
	},
	{
		"name": "vestibulo",
		"title": "El vestíbulo del metro, la salida, desde la plaza",
		"from": Vector3(357.5, 333.5, 1.7),
		"to": Vector3(326.0, 299.5, 7.0),
		"fov": 62.0,
	},
	{
		"name": "soviets",
		"title": "La Casa de los Sóviets cierra la avenida",
		"from": Vector3(962.0, 929.0, 1.7),
		"to": Vector3(1069.0, 1039.7, 26.0),
		"fov": 62.0,
	},
	{
		"name": "calle_rota",
		"title": "La calle de la Planta: el firme levantado en placas, bordillos movidos y matojos",
		"from": Vector3(1372.5, 1039.0, 1.7),
		"to": Vector3(1356.0, 1050.0, 0.3),
		"fov": 64.0,
	},
	{
		"name": "atasco",
		"title": "El atasco de la avenida Soviética: autobuses, camiones y coches quemados",
		"from": Vector3(854.1, 896.7, 3.0),
		"to": Vector3(911.0, 959.8, 0.5),
		"fov": 62.0,
	},
	{
		"name": "barcos",
		"title": "Los barcos de pasajeros, atrapados en el hielo frente a la Estación Fluvial",
		"from": Vector3(872.0, 728.0, 1.7),
		"to": Vector3(930.0, 765.0, 3.0),
		"fov": 62.0,
	},
]
## Niebla: la del juego, una ligera (para ver lejos) o ninguna (todo detallado).
const FOG_MODES: PackedStringArray = ["juego", "ligera", "sin"]
const FOG_SCALE: Dictionary = {"juego": 1.0, "ligera": 0.2, "sin": 0.0}
const NEAR_DISTANCE: Dictionary = {"juego": 450.0, "ligera": 900.0, "sin": 5000.0}
## Y a qué distancia se ven los modelos del kit en vez de los volúmenes.
const KIT_DISTANCE: Dictionary = {"juego": 200.0, "ligera": 450.0, "sin": 5000.0}
## Velocidades de los recorridos: paso real, ×4 y ×16.
const ROUTE_SPEEDS: Array[float] = [1.0, 4.0, 16.0]
const COMPASS: PackedStringArray = ["E", "NE", "N", "NO", "O", "SO", "S", "SE"]
const DEBUG_PANEL: Script = preload("res://scripts/debug/debug_panel.gd")
const HELP: String = (
	"Tab andar/volar · 1-9 y 0 vistas (Mayús: tránsito) · R recorrido (Mayús+R atrás, + -)"
	+ " · F2 rutas · F3 sectores · F4 hitos a la vista\n"
	+ "N niebla · O oclusión · P tinta · L linterna · B prueba de rendimiento"
	+ " · V comprobar hitos · F1 hora y estilo · F9 texto"
)

@export_range(0.0, 24.0) var hour: float = 12.0
@export_enum("despejado", "ventisca") var weather: String = "despejado"

var plan: CityPlan
var city: City
var overlays: CityOverlays
var walker: MockupWalker
var fog_mode: String = "juego"

var _view_cameras: Array[Camera3D] = []
var _last_camera: Camera3D
var _user_state: Dictionary = {}
var _hud_layer: CanvasLayer
var _hud: Label
var _show_hud: bool = true
var _panel: CanvasLayer
var _route: Dictionary = {}
var _route_line: PackedVector2Array = PackedVector2Array()
var _route_distance: float = 0.0
var _route_speed: int = 0
var _route_look: Vector3 = Vector3.ZERO
var _ahead: Dictionary = {}
var _ahead_distance: float = 0.0
var _landmarks_in_sight: PackedStringArray = []
var _message: String = ""
var _message_time: float = 0.0
var _benchmarking: bool = false
var _hud_timer: float = 0.0


func _ready() -> void:
	_build_hud()
	plan = CityPlan.load_default()
	if not plan.is_loaded():
		_hud.text = "No se puede abrir el plano de la ciudad.\n" + plan.error
		return
	city = City.new()
	city.name = "Ciudad"
	add_child(city)
	city.build(plan)
	print("Maqueta de Tumansk: %s" % city.stats)
	overlays = CityOverlays.new()
	overlays.name = "Capas"
	add_child(overlays)
	overlays.build(city)
	for view: Dictionary in VIEWS:
		_add_view_camera(view)
	walker = MockupWalker.new()
	walker.name = "Visitante"
	add_child(walker)
	_go_to_view(0)
	walker.camera().make_current()
	_last_camera = walker.camera()
	_panel = DEBUG_PANEL.new()
	_panel.name = "PanelDepuracion"
	add_child(_panel)
	_panel.call(&"set_target", self)
	get_viewport().use_occlusion_culling = true
	set_fog(fog_mode)
	_say(
		"Ciudad levantada en %s s. Clic para mirar con el ratón." % _decimal(city.stats["segundos"])
	)


## Cambia la hora del día (la usa el panel de depuración).
func set_hour(value: float) -> void:
	hour = value
	_apply_atmosphere()


## Cambia el clima: "despejado" o "ventisca".
func set_weather(value: String) -> void:
	weather = value
	_apply_atmosphere()


## Niebla del juego, ligera o ninguna. Sin la del juego, se ve lejos y los sectores se
## dibujan detallados hasta más lejos.
func set_fog(mode: String) -> void:
	fog_mode = mode if FOG_MODES.has(mode) else "juego"
	if city != null:
		city.set_near_distance(NEAR_DISTANCE[fog_mode])
		city.set_kit_distance(KIT_DISTANCE[fog_mode])
	_apply_atmosphere()


## Lleva al visitante a una de las vistas fijas (0 es la primera).
func go_to_view(index: int) -> void:
	_go_to_view(index)


## Muestra solo las capas de la lista, separadas por comas: "rutas", "sectores", "hitos".
func show_layers(names: String) -> void:
	var wanted: PackedStringArray = names.split(",", false)
	overlays.routes.visible = wanted.has("rutas")
	overlays.sectors.visible = wanted.has("sectores")
	overlays.landmarks.visible = wanted.has("hitos")


## Enciende o apaga la linterna del visitante y de las vistas fijas.
func set_flashlight(on: bool) -> void:
	for camera: Camera3D in _view_cameras + [walker.camera()]:
		Flashlight.attach(camera).visible = on


## Comprueba la regla del plano «desde cualquier punto se ven al menos dos hitos» en toda
## la ciudad (cada 20 m, a la altura de los ojos) y marca los puntos ciegos. Es una
## corrutina: espera a que la física tenga los edificios antes de lanzar los rayos.
func survey_landmarks() -> Dictionary:
	await get_tree().physics_frame
	await get_tree().physics_frame
	var started: int = Time.get_ticks_msec()
	var result: Dictionary = overlays.landmark_survey(20.0, [walker.get_rid()])
	var lines: PackedStringArray = []
	var zones: Dictionary = result["zonas"]
	for zone: String in zones:
		var tally: Vector2i = zones[zone]
		lines.append("  %s: %d %%" % [zone, roundi(100.0 * tally.y / maxi(1, tally.x))])
	var summary: String = (
		"Hitos: desde el %d %% de %d puntos se ven al menos dos (%d puntos ciegos marcados; %s s)."
		% [
			roundi(100.0 * result["con_dos"] / maxi(1, result["puntos"])),
			result["puntos"],
			result["ciegos"],
			_decimal((Time.get_ticks_msec() - started) / 1000.0),
		]
	)
	print(summary + "\n" + "\n".join(lines))
	_say(summary, 20.0)
	return result


## Para las capturas: solo se capturan las vistas de la lista (nombres separados por comas).
func capture_only(names: String) -> void:
	var wanted: PackedStringArray = names.split(",", false)
	for i: int in _view_cameras.size():
		if not wanted.has(String(VIEWS[i]["name"])):
			_view_cameras[i].remove_from_group(&"capture_camera")


## Para las capturas con el panel: la única cámara que se captura es la del visitante.
func capture_walker() -> void:
	for camera: Camera3D in _view_cameras:
		camera.remove_from_group(&"capture_camera")
	walker.camera().add_to_group(&"capture_camera")
	walker.camera().make_current()


## Posición de una vista en el mundo: (x, y) del plano y z metros sobre lo que se pisa.
func view_point(spec: Vector3) -> Vector3:
	var point: Vector2 = Vector2(spec.x, spec.y)
	return CityPlan.to_world(point, city.surface_height(point) + spec.z)


func _apply_atmosphere() -> void:
	var environment: Environment = $Entorno.environment
	Atmosphere.apply_hour(environment, $Sol, hour, weather)
	var scale: float = FOG_SCALE.get(fog_mode, 1.0)
	environment.fog_enabled = scale > 0.0
	environment.fog_density *= scale
	RenderingServer.global_shader_parameter_set(&"tinta_niebla_densidad", environment.fog_density)


func _process(delta: float) -> void:
	if city == null:
		return
	_watch_camera()
	if not _route.is_empty():
		_follow_route(delta)
	_message_time = maxf(0.0, _message_time - delta)
	_hud_timer -= delta
	if _hud_timer <= 0.0:
		_hud_timer = 0.2
		_look_ahead()
		_update_hud()


func _input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key != null and key.pressed and key.keycode == KEY_F1:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _unhandled_input(event: InputEvent) -> void:
	if city == null:
		return
	var button: InputEventMouseButton = event as InputEventMouseButton
	if button != null and button.pressed and button.button_index == MOUSE_BUTTON_LEFT:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	var key: InputEventKey = event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if key.keycode >= KEY_0 and key.keycode <= KEY_9:
		# Con Mayús, las vistas de la red de tránsito (la undécima y siguientes); con Ctrl,
		# las del deterioro (la vigesimoprimera y siguientes).
		var index: int = wrapi(key.keycode - KEY_1, 0, 10) + (10 if key.shift_pressed else 0)
		index += 20 if key.ctrl_pressed else 0
		if index < VIEWS.size():
			_go_to_view(index)
		return
	match key.keycode:
		KEY_ESCAPE:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		KEY_TAB:
			_stop_route()
			walker.set_flying(not walker.flying)
			_say("Volando: la rueda cambia la velocidad." if walker.flying else "Andando.")
		KEY_R:
			_start_route(-1 if key.shift_pressed else 1)
		KEY_BACKSPACE:
			_stop_route()
		KEY_EQUAL, KEY_PLUS, KEY_KP_ADD:
			_route_speed = mini(_route_speed + 1, ROUTE_SPEEDS.size() - 1)
		KEY_MINUS, KEY_KP_SUBTRACT:
			_route_speed = maxi(_route_speed - 1, 0)
		KEY_F2:
			overlays.routes.visible = not overlays.routes.visible
		KEY_F3:
			overlays.sectors.visible = not overlays.sectors.visible
		KEY_F4:
			overlays.landmarks.visible = not overlays.landmarks.visible
		KEY_N:
			set_fog(FOG_MODES[(FOG_MODES.find(fog_mode) + 1) % FOG_MODES.size()])
		KEY_O:
			get_viewport().use_occlusion_culling = not get_viewport().use_occlusion_culling
		KEY_P:
			$InkPost.visible = not $InkPost.visible
		KEY_L:
			Flashlight.toggle(walker.camera())
		KEY_B:
			_run_benchmark()
		KEY_V:
			survey_landmarks()
		KEY_F9:
			_show_hud = not _show_hud


func _add_view_camera(view: Dictionary) -> void:
	var camera: Camera3D = Camera3D.new()
	camera.name = "Vista_" + String(view["name"])
	camera.fov = view["fov"]
	camera.far = 4000.0
	add_child(camera)
	camera.add_to_group(&"capture_camera")
	camera.look_at_from_position(view_point(view["from"]), view_point(view["to"]))
	_view_cameras.append(camera)


func _go_to_view(index: int) -> void:
	if index >= VIEWS.size():
		return
	_stop_route()
	var view: Dictionary = VIEWS[index]
	if float(view["from"].z) > 3.0 and not walker.flying:
		walker.set_flying(true)
	walker.place(view_point(view["from"]), view_point(view["to"]))
	_say("Vista %d: %s" % [(index + 1) % 10, view["title"]])


## Las vistas pueden pedir su niebla y sus capas mientras son la cámara activa (así las
## capturas de revisión salen con lo que necesitan). Al volver al visitante, todo queda
## como estaba.
func _watch_camera() -> void:
	var current: Camera3D = get_viewport().get_camera_3d()
	if current == _last_camera:
		return
	if _last_camera == walker.camera():
		_user_state = {
			"niebla": fog_mode,
			"capas":
			[overlays.routes.visible, overlays.sectors.visible, overlays.landmarks.visible],
		}
	_last_camera = current
	var index: int = _view_cameras.find(current)
	if index < 0:
		set_fog(_user_state.get("niebla", "juego"))
		var shown: Array = _user_state.get("capas", [false, false, false])
		overlays.routes.visible = shown[0]
		overlays.sectors.visible = shown[1]
		overlays.landmarks.visible = shown[2]
		return
	var view: Dictionary = VIEWS[index]
	set_fog(view.get("niebla", "juego"))
	var layers: Array = view.get("capas", [])
	overlays.routes.visible = layers.has("rutas")
	overlays.sectors.visible = layers.has("sectores")
	overlays.landmarks.visible = layers.has("hitos")


func _start_route(step: int) -> void:
	var routes: Array = plan.data["rutas"]
	var index: int = routes.find(_route) if not _route.is_empty() else (-1 if step > 0 else 0)
	_route = routes[wrapi(index + step, 0, routes.size())]
	_route_line = CityGeometry.subdivide(CityPlan.line(_route["puntos"]), 1.0)
	_route_distance = 0.0
	walker.controls_enabled = false
	walker.set_flying(true)
	var ahead: Vector2 = CityGeometry.point_along(_route_line, 10.0).origin
	_route_look = CityPlan.to_world(ahead, city.surface_height(ahead) + MockupWalker.EYE_HEIGHT)
	overlays.routes.visible = true


func _stop_route() -> void:
	if _route.is_empty():
		return
	_route = {}
	walker.controls_enabled = true
	walker.set_flying(false)


## Recorre la ruta a paso de persona (1,4 m/s), o más deprisa, mirando hacia delante.
func _follow_route(delta: float) -> void:
	var length: float = CityGeometry.length(_route_line)
	var speed: float = MockupWalker.WALK_SPEED * ROUTE_SPEEDS[_route_speed]
	_route_distance = minf(_route_distance + speed * delta, length)
	var here: Vector2 = CityGeometry.point_along(_route_line, _route_distance).origin
	var ahead: Vector2 = CityGeometry.point_along(_route_line, _route_distance + 10.0).origin
	if _route_distance >= length - 0.01:
		ahead = here + CityGeometry.point_along(_route_line, length).x * 10.0
	var eye_height: float = MockupWalker.EYE_HEIGHT
	var eye: Vector3 = CityPlan.to_world(here, city.surface_height(here) + eye_height)
	var target: Vector3 = CityPlan.to_world(ahead, city.surface_height(ahead) + eye_height)
	_route_look = _route_look.lerp(target, 1.0 - exp(-delta * 3.0 * ROUTE_SPEEDS[_route_speed]))
	walker.place(eye, _route_look)


## El edificio que hay delante del centro de la pantalla (hasta 400 m).
func _look_ahead() -> void:
	var camera: Camera3D = get_viewport().get_camera_3d()
	if camera == null:
		return
	var from: Vector3 = camera.global_position
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, from - camera.global_transform.basis.z * 400.0
	)
	query.exclude = [walker.get_rid()]
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	_ahead = city.building_of(hit.get("collider")) if not hit.is_empty() else {}
	_ahead_distance = from.distance_to(hit["position"]) if not hit.is_empty() else 0.0
	_landmarks_in_sight = overlays.update_visible_landmarks(from, [walker.get_rid()])


## Mide cada vista unos segundos: fotogramas por segundo (media y peor), llamadas de dibujo
## y triángulos. El resultado sale en el panel y en la consola.
func _run_benchmark() -> void:
	if _benchmarking:
		return
	_benchmarking = true
	var previous: Camera3D = get_viewport().get_camera_3d()
	var lines: PackedStringArray = []
	var all_frames: float = 0.0
	var all_time: float = 0.0
	var worst: Dictionary = {}
	for i: int in _view_cameras.size():
		if VIEWS[i].has("niebla"):
			continue
		_view_cameras[i].make_current()
		_say("Prueba de rendimiento: %s…" % VIEWS[i]["title"])
		for _k: int in 20:
			await get_tree().process_frame
		var result: Dictionary = await _measure(90)
		result["vista"] = VIEWS[i]["name"]
		all_frames += result["fotogramas"]
		all_time += result["segundos"]
		if worst.is_empty() or result["peor_fps"] < worst["peor_fps"]:
			worst = result
		lines.append(
			(
				"  %-10s %5.1f fps (peor %5.1f) · %4d llamadas · %s triángulos"
				% [
					result["vista"],
					result["fps"],
					result["peor_fps"],
					result["llamadas"],
					_millions(result["triangulos"])
				]
			)
		)
	previous.make_current()
	var summary: String = (
		"Prueba de rendimiento: media %.0f fps; la peor vista, %s (%.0f fps en el peor momento)."
		% [all_frames / maxf(all_time, 0.001), worst.get("vista", "-"), worst.get("peor_fps", 0.0)]
	)
	print(summary + "\n" + "\n".join(lines))
	_say(summary, 20.0)
	_benchmarking = false


func _measure(frames: int) -> Dictionary:
	var total: float = 0.0
	var slowest: float = 0.0
	var calls: int = 0
	var triangles: int = 0
	var last: int = Time.get_ticks_usec()
	for _i: int in frames:
		await get_tree().process_frame
		var now: int = Time.get_ticks_usec()
		var frame: float = (now - last) / 1000000.0
		last = now
		total += frame
		slowest = maxf(slowest, frame)
		calls += RenderingServer.get_rendering_info(
			RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME
		)
		triangles += RenderingServer.get_rendering_info(
			RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME
		)
	return {
		"fotogramas": frames,
		"segundos": total,
		"fps": frames / maxf(total, 0.001),
		"peor_fps": 1.0 / maxf(slowest, 0.001),
		"llamadas": calls / frames,
		"triangulos": triangles / frames,
	}


func _build_hud() -> void:
	_hud_layer = CanvasLayer.new()
	_hud_layer.name = "Panel"
	add_child(_hud_layer)
	_hud = Label.new()
	_hud.position = Vector2(20, 14)
	_hud.add_theme_color_override("font_color", Color("#f2e6cf"))
	_hud.add_theme_color_override("font_outline_color", Color("#1b1a22"))
	_hud.add_theme_constant_override("outline_size", 6)
	_hud.add_theme_font_size_override("font_size", 17)
	_hud_layer.add_child(_hud)


func _update_hud() -> void:
	var on_view_camera: bool = _view_cameras.has(get_viewport().get_camera_3d())
	_hud_layer.visible = _show_hud and (not on_view_camera or _benchmarking)
	if not _hud_layer.visible:
		return
	var camera: Camera3D = walker.camera()
	var point: Vector2 = CityPlan.to_plan(camera.global_position)
	var lines: PackedStringArray = []
	var mode: String = (
		"recorrido" if not _route.is_empty() else ("volando" if walker.flying else "andando")
	)
	lines.append(
		(
			"MAQUETA DE TUMANSK · %s · %s · %s · niebla %s"
			% [
				mode,
				_clock(hour),
				weather,
				{"juego": "del juego", "ligera": "ligera", "sin": "ninguna"}[fog_mode]
			]
		)
	)
	lines.append(_location_line(point))
	if not _ahead.is_empty():
		lines.append(_building_line(_ahead, _ahead_distance))
	lines.append(_landmarks_line())
	lines.append(_performance_line())
	if not _route.is_empty():
		lines.append(_route_line_text())
	if _message_time > 0.0:
		lines.append(_message)
	lines.append(HELP)
	_hud.text = "\n".join(lines)


func _building_line(building: Dictionary, distance: float) -> String:
	# Los números del JSON llegan como float: la clave es "2", no "2.0".
	var damage: String = plan.data["niveles_dano"][str(int(building["dano"]))]["nombre"]
	var floors: int = int(building["pisos"])
	var fire: String = {"no": "sin incendio", "parcial": "incendio parcial"}.get(
		building["incendio"], "incendio total"
	)
	return (
		"Delante, a %d m: %s · %s · %d %s · %s m (en pie %s m) · daño %d, %s · %s"
		% [
			roundi(distance),
			building["id"],
			building["nombre"],
			floors,
			"planta" if floors == 1 else "plantas",
			_decimal(building["altura"]),
			_decimal(city.standing_height(building)),
			int(building["dano"]),
			damage.to_lower(),
			fire,
		]
	)


func _location_line(point: Vector2) -> String:
	return (
		"%s · %s · x %d  y %d · suelo %s m · mirando al %s"
		% [
			CityPlan.sector_name(plan.sector_of(point)),
			plan.zone_label(point),
			roundi(point.x),
			roundi(point.y),
			_decimal(city.surface_height(point)),
			_compass(walker.heading()),
		]
	)


func _landmarks_line() -> String:
	var count: int = _landmarks_in_sight.size()
	if count == 0:
		return "Hitos a la vista: ninguno"
	return "Hitos a la vista: %d · %s" % [count, ", ".join(_landmarks_in_sight)]


func _performance_line() -> String:
	var detailed: int = 0
	var camera_point: Vector2 = CityPlan.to_plan(get_viewport().get_camera_3d().global_position)
	var grid: Vector2i = plan.sector_grid()
	for row: int in grid.y:
		for column: int in grid.x:
			var center: Vector2 = plan.sector_rect(Vector2i(column, row)).get_center()
			if center.distance_to(camera_point) < city.near_distance:
				detailed += 1
	return (
		(
			"%d fps · %d llamadas de dibujo · %s triángulos · %d objetos"
			+ " · %d de %d sectores detallados · oclusión %s · tinta %s"
		)
		% [
			Engine.get_frames_per_second(),
			RenderingServer.get_rendering_info(
				RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME
			),
			_millions(
				RenderingServer.get_rendering_info(
					RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME
				)
			),
			RenderingServer.get_rendering_info(
				RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME
			),
			detailed,
			grid.x * grid.y,
			"sí" if get_viewport().use_occlusion_culling else "no",
			"sí" if $InkPost.visible else "no",
		]
	)


func _route_line_text() -> String:
	var length: float = CityGeometry.length(_route_line)
	var seconds: float = _route_distance / MockupWalker.WALK_SPEED
	return (
		(
			"Recorrido %s · %s · %s (%s): %d de %d m · %s andando sin parar"
			+ " · el plano calcula %d min a paso prudente · ×%d"
		)
		% [
			_route["id"],
			_route["destino"],
			_route["nombre"],
			_route["perfil"],
			roundi(_route_distance),
			roundi(length),
			_duration(seconds),
			int(_route["minutos"]),
			roundi(ROUTE_SPEEDS[_route_speed]),
		]
	)


func _say(text: String, seconds: float = 6.0) -> void:
	_message = text
	_message_time = seconds
	_hud_timer = 0.0


static func _decimal(value: float) -> String:
	return ("%.1f" % value).replace(".", ",")


static func _millions(value: int) -> String:
	if value >= 1000000:
		return ("%.2f M" % (value / 1000000.0)).replace(".", ",")
	return "%d k" % roundi(value / 1000.0)


static func _clock(value: float) -> String:
	var minutes: int = roundi(fposmod(value, 24.0) * 60.0)
	return "%02d:%02d" % [minutes / 60, minutes % 60]


static func _duration(seconds: float) -> String:
	var whole: int = roundi(seconds)
	return "%d:%02d" % [whole / 60, whole % 60]


## Rumbo de una dirección del mundo en la rosa de los vientos (el norte es -Z).
static func _compass(direction: Vector3) -> String:
	var angle: float = fposmod(rad_to_deg(atan2(-direction.z, direction.x)), 360.0)
	return COMPASS[roundi(angle / 45.0) % COMPASS.size()]
