class_name NoiseRules
extends RefCounted
## El ruido (F3-01): lo lejos que se oye cada cosa, en metros, con el aire en
## calma y nada en medio (su "alcance"). Lo usan los pasos de los jugadores, las
## herramientas y lo que cae, y lo lee la percepción de la IA (F3-09), que le
## quita lo que tapa el clima y lo que hay en medio. Ver docs/SUPERFICIE.md, 3.2.

## Alcance de un paso según el paso (PlayerBody.Gait).
const STEP_RADIUS: Dictionary = {
	PlayerBody.Gait.CROUCH: 3.0,
	PlayerBody.Gait.WALK: 9.0,
	PlayerBody.Gait.RUN: 22.0,
}
## Al caer: tanto por metro de caída, a partir de la mínima que suena.
const LANDING_PER_METER: float = 4.0
const LANDING_MIN_FALL: float = 1.5
## Lo que multiplica el suelo.
const GROUND: Dictionary = {
	&"nieve": 1.0,
	&"hielo": 1.4,
	&"granito": 0.85,
	&"losas": 0.85,
	&"asfalto": 0.85,
	&"hormigon": 0.85,
	&"baldosa": 0.9,
	&"tierra": 0.7,
	&"madera": 1.1,
	&"cascotes": 1.3,
	&"cristales": 2.0,
	&"chapa": 1.8,
	&"moqueta": 0.5,
}
const DEFAULT_GROUND: StringName = &"nieve"
## La carga: a partir de estos kilos, cada kilo más suena un 2 % más.
const LOAD_FREE_KG: float = 6.0
const LOAD_PER_KG: float = 0.02
## Lo que va suelto en la mochila: por cada cosa, andando y corriendo.
const RATTLE_WALK: float = 4.0
const RATTLE_RUN: float = 10.0
## Otros ruidos, por su clase.
const SOUNDS: Dictionary = {
	&"puerta": 6.0,
	&"puerta_oxidada": 12.0,
	&"palanca": 30.0,
	&"cristal": 25.0,
	&"cizalla": 12.0,
	&"ganzua": 2.0,
	&"despertador": 35.0,
	&"jadeo": 5.0,
	&"tripas": 2.0,
	&"compuerta": 18.0,
	&"golpe": 14.0,
}
## Lo que quita el clima al alcance, por la fuerza del viento (Weather.Wind).
const WIND_MASK: Array[float] = [0.0, 0.15, 0.4, 0.65]
## Cada muro entre el ruido y quien escucha deja esto; y pasar de dentro a fuera, esto otro.
const WALL_FACTOR: float = 0.35
const INSIDE_OUTSIDE: float = 0.5

## Clases de ruido (para la IA y para las ondas de tinta).
const STEP: StringName = &"paso"
const LANDING: StringName = &"caida"
const RATTLE: StringName = &"traqueteo"


## Lo que multiplica un suelo (los que no se conocen, como la nieve).
static func ground_factor(ground: StringName) -> float:
	return float(GROUND.get(ground, GROUND[DEFAULT_GROUND]))


## Alcance de un paso a paso [param gait] sobre [param ground] con [param load_kg] encima.
static func step_radius(gait: PlayerBody.Gait, ground: StringName, load_kg: float = 0.0) -> float:
	if not STEP_RADIUS.has(gait):
		return 0.0
	var load_factor: float = 1.0 + maxf(0.0, load_kg - LOAD_FREE_KG) * LOAD_PER_KG
	return float(STEP_RADIUS[gait]) * ground_factor(ground) * load_factor


## Alcance de lo que va suelto en la mochila ([param loose] cosas) a paso [param gait].
## Agachado y quieto no suena.
static func rattle_radius(gait: PlayerBody.Gait, loose: int) -> float:
	if loose <= 0:
		return 0.0
	match gait:
		PlayerBody.Gait.WALK:
			return RATTLE_WALK * sqrt(float(loose))
		PlayerBody.Gait.RUN:
			return RATTLE_RUN * sqrt(float(loose))
	return 0.0


## Alcance de caer [param fall] metros sobre [param ground]: nada si es poco.
static func landing_radius(fall: float, ground: StringName) -> float:
	if fall < LANDING_MIN_FALL:
		return 0.0
	return LANDING_PER_METER * fall * ground_factor(ground)


## Alcance de un ruido de clase [param kind] (de la tabla [constant SOUNDS]).
static func sound_radius(kind: StringName) -> float:
	return float(SOUNDS.get(kind, 0.0))


## Lo que queda de [param radius] para quien escucha: con viento de fuerza
## [param wind], [param walls] muros en medio y, si [param crosses] , el ruido
## pasa de dentro de un edificio a fuera (o al revés).
static func heard_radius(radius: float, wind: int, walls: int, crosses: bool = false) -> float:
	var result: float = radius * (1.0 - WIND_MASK[clampi(wind, 0, WIND_MASK.size() - 1)])
	result *= pow(WALL_FACTOR, maxi(walls, 0))
	if crosses:
		result *= INSIDE_OUTSIDE
	return result
