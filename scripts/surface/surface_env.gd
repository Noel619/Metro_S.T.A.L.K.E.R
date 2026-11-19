class_name SurfaceEnv
extends Node
## Lo que comparten los sistemas de la superficie: la hora, el tiempo del día
## ([Weather]) y hacia dónde está el sol. Vive en el nivel de la superficie; la
## percepción, los pasos y la visibilidad lo buscan con [method find]. El tiempo
## sale del día y de la hora de [GameState], así que es el mismo en todos los
## equipos; el panel de depuración puede fijar otro ([method override]).

const GROUP: StringName = &"entorno_superficie"
## Cada cuánto se vuelve a calcular el tiempo (segundos reales).
const REFRESH_SECONDS: float = 1.0

## El sol (o la luna) de la escena: su eje Z apunta hacia él.
var sun: DirectionalLight3D
var weather: Weather = Weather.fixed(270.0, Weather.Wind.BRISA)

var _fixed: Weather
var _refresh: float = 0.0


## El entorno de la escena, si lo hay.
static func find(tree: SceneTree) -> SurfaceEnv:
	return tree.get_first_node_in_group(GROUP) as SurfaceEnv


func _ready() -> void:
	add_to_group(GROUP)
	_update()


func _process(delta: float) -> void:
	_refresh -= delta
	if _refresh <= 0.0:
		_refresh = REFRESH_SECONDS
		_update()


## Fija un tiempo (null vuelve al del día).
func override(fixed_weather: Weather) -> void:
	_fixed = fixed_weather
	_update()


func hour() -> float:
	return GameState.hour()


## Hacia dónde está el sol (de largo 1); hacia abajo si no hay sol.
func sun_direction() -> Vector3:
	if sun == null or not sun.is_inside_tree():
		return Vector3.DOWN
	return sun.global_basis.z.normalized()


## Lo que necesita [method Visibility.assess].
func context() -> Dictionary:
	return {"hour": hour(), "sun": sun_direction(), "weather": weather}


func _update() -> void:
	weather = _fixed if _fixed != null else Weather.at(GameState.day, GameState.minute)
