class_name Weather
extends RefCounted
## El tiempo de cada día en la superficie: de dónde sopla el viento, con qué
## fuerza y si nieva. Sale de una semilla del día y de la hora, así que todos los
## equipos lo calculan igual sin mandárselo (el día y la hora ya se replican).
##
## Manda en el olfato de la IA (el viento lleva el olor), en lo que tapa el ruido
## y la vista, en cuánto duran las huellas y en lo que se ve (la nieve que cae y
## la que barre el suelo, los trapos, el humo). Ver docs/SUPERFICIE.md, 10.

enum Wind { CALMA, BRISA, VIENTO, VENTISCA }

## Lo probable de cada fuerza del viento al empezar el día.
const WIND_ODDS: Array[float] = [0.2, 0.4, 0.3, 0.1]
## De dónde suele venir el viento en invierno (rumbo en grados: 0 norte, 90 este):
## del oeste y del noroeste, y a veces del norte.
const PREVAILING: Array[float] = [270.0, 295.0, 315.0, 340.0, 250.0, 0.0]
## Lo que gira el viento a lo largo del día, como mucho (grados).
const DRIFT_DEGREES: float = 30.0
const SNOW_ODDS: float = 0.35
## Las horas de ventisca: empieza a una hora del día y dura unas horas.
const BLIZZARD_HOURS: Vector2 = Vector2(3.0, 6.0)
## Velocidad del viento en m/s para cada fuerza (para lo que se ve: nieve, trapos).
const WIND_SPEED: Array[float] = [0.4, 2.5, 6.0, 12.0]

## De dónde sopla, como rumbo en grados (0 norte, 90 este, en el sentido del reloj).
var from_bearing: float = 270.0
var wind: Wind = Wind.BRISA
var snowing: bool = false


## El tiempo del día [param day] al minuto [param minute].
static func at(day: int, minute: float) -> Weather:
	var result: Weather = Weather.new()
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = hash("tiempo_%d" % day)
	var base: float = PREVAILING[rng.randi() % PREVAILING.size()] + rng.randf_range(-15.0, 15.0)
	var roll: float = rng.randf()
	var strength: int = 0
	var total: float = 0.0
	for index: int in WIND_ODDS.size():
		total += WIND_ODDS[index]
		if roll < total:
			strength = index
			break
	var snows: bool = rng.randf() < SNOW_ODDS
	var drift_phase: float = rng.randf() * TAU
	var blizzard_start: float = rng.randf_range(8.0, 16.0) * 60.0
	var blizzard_length: float = rng.randf_range(BLIZZARD_HOURS.x, BLIZZARD_HOURS.y) * 60.0
	# El rumbo gira despacio a lo largo del día (dos vaivenes entre las 0 y las 24).
	var day_share: float = minute / GameState.DAY_MINUTES
	result.from_bearing = fposmod(
		base + DRIFT_DEGREES * sin(drift_phase + day_share * TAU * 2.0), 360.0
	)
	result.wind = strength as Wind
	if strength == Wind.VENTISCA:
		var inside: bool = minute >= blizzard_start and minute < blizzard_start + blizzard_length
		result.wind = Wind.VENTISCA if inside else Wind.VIENTO
	result.snowing = snows or result.wind == Wind.VENTISCA
	return result


## Un tiempo fijo (para pruebas, el panel de depuración y los dioramas).
static func fixed(bearing: float, strength: Wind, snows: bool = false) -> Weather:
	var result: Weather = Weather.new()
	result.from_bearing = fposmod(bearing, 360.0)
	result.wind = strength
	result.snowing = snows or strength == Wind.VENTISCA
	return result


## Hacia dónde va el aire, en el plano (x al este, y al norte), de largo 1.
func blowing_plan() -> Vector2:
	var radians: float = deg_to_rad(from_bearing)
	# Viene de ese rumbo, así que va hacia el contrario.
	return -Vector2(sin(radians), cos(radians))


## Hacia dónde va el aire, en el mundo de Godot (horizontal, de largo 1).
func blowing() -> Vector3:
	var plan: Vector2 = blowing_plan()
	return Vector3(plan.x, 0.0, -plan.y)


## Velocidad del aire (m/s), para lo que se ve.
func speed() -> float:
	return WIND_SPEED[wind]


## Nombre del clima para el ambiente ([Atmosphere]): con ventisca se cierra la niebla.
func atmosphere_name() -> String:
	return "ventisca" if wind == Wind.VENTISCA else "despejado"


## Cuánto se ve con este tiempo: lo que multiplica el alcance de la vista.
func sight_factor() -> float:
	if wind == Wind.VENTISCA:
		return 0.35
	return 0.7 if snowing else 1.0


## Segundos (reales) que dura un rastro de olor con este tiempo: unos 10 minutos;
## la nieve que cae lo tapa antes.
func scent_seconds() -> float:
	if wind == Wind.VENTISCA:
		return 120.0
	return 180.0 if snowing else 600.0


## Segundos (reales) que dura una huella en la nieve: toda la salida si no nieva.
func print_seconds() -> float:
	if wind == Wind.VENTISCA:
		return 120.0
	return 360.0 if snowing else 1800.0


## El rumbo en palabras (para la depuración): "del noroeste".
func from_words() -> String:
	var names: PackedStringArray = [
		"norte", "nordeste", "este", "sureste", "sur", "suroeste", "oeste", "noroeste"
	]
	return "del " + names[roundi(from_bearing / 45.0) % 8]
