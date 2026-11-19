class_name Tracks
extends Node3D
## Los rastros (F3-09, README 6.4): lo que se deja al pasar.
##
## - El olor: cada zancada de un jugador deja una marca de olor que dura unos
##   minutos (menos si nieva; la sangre, el triple). Solo existe en el anfitrión,
##   que es quien lo huele: los perros lo siguen hacia donde es más fresco.
## - Las huellas: botas y patas que se quedan marcadas en la nieve (calcomanías).
##   Las dibuja cada equipo, con lo que ya ve.

const GROUP: StringName = &"rastros"
const BOOT_TEXTURE: String = "res://assets/textures/huella_bota.png"
const PAW_TEXTURE: String = "res://assets/textures/huella_perro.png"
## La sangre dura el triple.
const BLOOD_FACTOR: float = 3.0
## Como mucho, tantas marcas de olor y tantas huellas (las más viejas se van).
const MAX_MARKS: int = 3000
const MAX_PRINTS: int = 900
## Cada cuánto se quitan las marcas viejas.
const PRUNE_SECONDS: float = 2.0
## Lo que miden las huellas en la nieve.
const BOOT_SIZE: Vector2 = Vector2(0.12, 0.3)
const PAW_SIZE: Vector2 = Vector2(0.11, 0.11)

## Las marcas de olor (en el anfitrión): {position, time, peer, blood}.
var marks: Array[Dictionary] = []

var _prints: Array[Decal] = []
var _print_times: Array[float] = []
var _prune: float = 0.0
var _boot: Texture2D
var _paw: Texture2D


## Los rastros de la escena, si los hay.
static func find(tree: SceneTree) -> Tracks:
	return tree.get_first_node_in_group(GROUP) as Tracks


func _ready() -> void:
	add_to_group(GROUP)
	_boot = load(BOOT_TEXTURE)
	_paw = load(PAW_TEXTURE)


func _process(delta: float) -> void:
	_prune -= delta
	if _prune > 0.0:
		return
	_prune = PRUNE_SECONDS
	var now: float = Stimuli.clock()
	var env: SurfaceEnv = SurfaceEnv.find(get_tree())
	var weather: Weather = env.weather if env != null else Weather.fixed(270.0, Weather.Wind.BRISA)
	var scent: float = weather.scent_seconds()
	while not marks.is_empty():
		var mark: Dictionary = marks[0]
		var life: float = scent * (BLOOD_FACTOR if mark["blood"] else 1.0)
		if now - float(mark["time"]) <= life:
			break
		marks.pop_front()
	var print_life: float = weather.print_seconds()
	for index: int in _prints.size():
		var age: float = (now - _print_times[index]) / print_life
		_prints[index].modulate.a = clampf(1.0 - age, 0.0, 1.0) * 0.95


## Deja una marca de olor en [param position] (solo el anfitrión). [param blood]:
## es sangre, que dura el triple y se huele más.
func drop(position: Vector3, peer: int, blood: bool = false) -> void:
	if not multiplayer.is_server():
		return
	marks.append({"position": position, "time": Stimuli.clock(), "peer": peer, "blood": blood})
	if marks.size() > MAX_MARKS:
		marks.pop_front()


## La marca de olor más fresca a menos de [param radius] de [param position]
## (vacío si no hay ninguna). Con [param blood_only], solo la sangre.
func freshest_near(position: Vector3, radius: float, blood_only: bool = false) -> Dictionary:
	var best: Dictionary = {}
	for index: int in range(marks.size() - 1, -1, -1):
		var mark: Dictionary = marks[index]
		if blood_only and not mark["blood"]:
			continue
		if (mark["position"] as Vector3).distance_to(position) <= radius:
			if best.is_empty() or float(mark["time"]) > float(best["time"]):
				best = mark
	return best


## Lo que lleva una marca (de 0, recién puesta, a 1, a punto de borrarse).
func age_of(mark: Dictionary) -> float:
	var env: SurfaceEnv = SurfaceEnv.find(get_tree())
	var weather: Weather = env.weather if env != null else Weather.fixed(270.0, Weather.Wind.BRISA)
	var life: float = weather.scent_seconds() * (BLOOD_FACTOR if mark["blood"] else 1.0)
	return clampf((Stimuli.clock() - float(mark["time"])) / life, 0.0, 1.0)


## Marca una huella en la nieve (de bota o de pata), mirando hacia [param yaw].
func print_step(position: Vector3, yaw: float, paw: bool = false) -> void:
	var decal: Decal
	if _prints.size() >= MAX_PRINTS:
		decal = _prints.pop_front()
		_print_times.pop_front()
	else:
		decal = Decal.new()
		decal.albedo_mix = 1.0
		decal.upper_fade = 0.2
		decal.lower_fade = 0.2
		decal.cull_mask = 1
		add_child(decal)
	var size: Vector2 = PAW_SIZE if paw else BOOT_SIZE
	decal.texture_albedo = _paw if paw else _boot
	decal.size = Vector3(size.x, 1.2, size.y)
	decal.global_position = position + Vector3.UP * 0.3
	decal.rotation = Vector3(0.0, yaw, 0.0)
	decal.modulate = Color(1.0, 1.0, 1.0, 0.95)
	_prints.append(decal)
	_print_times.append(Stimuli.clock())


## Cuántas huellas hay ahora (para las pruebas).
func print_count() -> int:
	return _prints.size()
