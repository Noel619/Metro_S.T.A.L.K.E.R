class_name Visibility
extends RefCounted
## Cuánto se te ve (F3-02): lo lejos que alguien puede verte, según la luz donde
## estás, la sombra, la postura, el movimiento, tu silueta contra el cielo, el
## clima y lo que te tapa. Lo lee la vista de la IA (F3-09); ver
## docs/SUPERFICIE.md, 3.3.
##
## El cálculo está en dos partes: [method sight_range] son solo cuentas (se prueban
## sin escena) y [method assess] lanza los rayos (sombra, techo, silueta y
## cobertura) en el mundo de quien mira.

## Una persona de pie, andando, a plena luz.
const BASE_RANGE: float = 120.0
## La luz: de día, a la sombra, bajo techo, al anochecer y de noche.
const DAY_LIGHT: float = 1.0
const SHADE: float = 0.7
const INSIDE: float = 0.4
const DUSK_LIGHT: float = 0.5
const NIGHT_LIGHT: float = 0.08
const CROUCHED: float = 0.55
## El movimiento: quieto, andando, corriendo; y quieto para quien ve sobre todo
## el movimiento (los perros).
const STILL: float = 0.5
const STILL_FOR_MOTION_SIGHT: float = 0.35
const RUNNING: float = 1.4
const SILHOUETTE: float = 1.6
## La linterna encendida: si apunta a quien mira y si no.
const TORCH_FACING: float = 250.0
const TORCH_SIDE: float = 120.0
## Lo que tiene que apuntar la linterna hacia alguien para deslumbrarle (coseno).
const TORCH_CONE: float = 0.85
## Hasta dónde se mira si detrás de alguien solo hay cielo, y desde qué altura
## sobre los ojos de quien mira (si estás más bajo, detrás tienes el suelo).
const SKY_CHECK: float = 120.0
const SKY_MIN_RISE: float = -0.03
## Lo que se busca un techo encima (bajo techo: dentro) y el sol (sombra).
const ROOF_CHECK: float = 30.0
const SUN_CHECK: float = 80.0
## Los puntos del cuerpo que se miran para la cobertura, como parte de lo alto.
const BODY_POINTS: Array[float] = [0.12, 0.55, 0.92]
## Capas que tapan la vista: el mundo y lo que se mueve (no los jugadores).
const SIGHT_MASK: int = 1 << 0


## La luz que hay a la hora [param hour] al aire libre: 1 de día, 0,5 al
## anochecer y al amanecer, 0,08 de noche (como el ambiente de [Atmosphere]).
static func ambient(hour: float) -> float:
	var h: float = fposmod(hour, 24.0)
	if h < 5.0 or h >= 19.5:
		return NIGHT_LIGHT
	if h < 6.5:
		return lerpf(NIGHT_LIGHT, DUSK_LIGHT, smoothstep(5.0, 6.5, h))
	if h < 8.0:
		return lerpf(DUSK_LIGHT, DAY_LIGHT, smoothstep(6.5, 8.0, h))
	if h < 16.5:
		return DAY_LIGHT
	if h < 18.0:
		return lerpf(DAY_LIGHT, DUSK_LIGHT, smoothstep(16.5, 18.0, h))
	return lerpf(DUSK_LIGHT, NIGHT_LIGHT, smoothstep(18.0, 19.5, h))


## Lo lejos que se ve a alguien (en metros), solo con cuentas.
## [param light]: la luz donde está (de [method ambient], con la sombra y el
## techo); [param crouch]: de 0 a 1; [param speed]: m/s; [param silhouette]:
## detrás solo hay cielo; [param weather_factor]: de [method Weather.sight_factor];
## [param motion_sight]: quien mira ve sobre todo el movimiento; [param torch]: 0
## apagada, 1 encendida, 2 encendida y apuntándole.
static func sight_range(
	light: float,
	crouch: float,
	speed: float,
	silhouette: bool,
	weather_factor: float = 1.0,
	motion_sight: bool = false,
	torch: int = 0
) -> float:
	var posture: float = lerpf(1.0, CROUCHED, clampf(crouch, 0.0, 1.0))
	var motion: float = 1.0
	if speed < PlayerBody.STILL_THRESHOLD:
		motion = STILL_FOR_MOTION_SIGHT if motion_sight else STILL
	elif speed >= PlayerBody.RUN_THRESHOLD:
		motion = RUNNING
	var result: float = BASE_RANGE * light * posture * motion * weather_factor
	if silhouette:
		result *= SILHOUETTE
	match torch:
		1:
			result = maxf(result, TORCH_SIDE * weather_factor)
		2:
			result = maxf(result, TORCH_FACING * weather_factor)
	return result


## Mira desde [param eye] a [param target] (un jugador) en el mundo [param space]:
## devuelve el alcance, la distancia, la parte que se ve y si se le ve
## ([code]range, distance, cover, light, silhouette, visible[/code]).
## [param context] trae la hora ([code]hour[/code]), hacia dónde está el sol
## ([code]sun[/code], de largo 1) y el tiempo ([code]weather[/code], un [Weather]);
## [param exclude], los RID que no tapan (quien mira).
static func assess(
	space: PhysicsDirectSpaceState3D,
	eye: Vector3,
	target: Player,
	context: Dictionary,
	motion_sight: bool = false,
	exclude: Array[RID] = []
) -> Dictionary:
	var feet: Vector3 = target.global_position
	var height: float = target.body_height()
	var skip: Array[RID] = exclude.duplicate()
	skip.append(target.get_rid())
	var cover: float = cover_of(space, eye, feet, height, skip)
	var chest: Vector3 = feet + Vector3.UP * height * 0.6
	var light: float = light_at(space, chest, context, skip)
	var silhouette: bool = cover > 0.0 and against_sky(space, eye, chest, skip)
	var weather: Weather = context.get("weather") as Weather
	var torch: int = 0
	if target.flashlight_on:
		var facing: Vector3 = target.look_direction()
		torch = 2 if facing.dot((eye - chest).normalized()) > TORCH_CONE else 1
	var reach: float = sight_range(
		light,
		target.crouch,
		target.move_speed,
		silhouette,
		weather.sight_factor() if weather != null else 1.0,
		motion_sight,
		torch
	)
	# Lo que te tapa acorta el alcance: si solo asoma la cabeza, cuesta verla.
	reach *= lerpf(0.5, 1.0, cover)
	var distance: float = eye.distance_to(chest)
	return {
		"range": reach,
		"distance": distance,
		"cover": cover,
		"light": light,
		"silhouette": silhouette,
		"visible": cover > 0.0 and distance <= reach,
	}


## La parte de un cuerpo de pie en [param feet], de [param height] de alto, que
## se ve desde [param eye] (de 0 a 1: pies, pecho, cabeza).
static func cover_of(
	space: PhysicsDirectSpaceState3D,
	eye: Vector3,
	feet: Vector3,
	height: float,
	exclude: Array[RID]
) -> float:
	var seen: int = 0
	for share: float in BODY_POINTS:
		if not blocked(space, eye, feet + Vector3.UP * height * share, exclude):
			seen += 1
	return float(seen) / BODY_POINTS.size()


## La luz en [param point]: la del cielo a esa hora, menos bajo techo o a la
## sombra del sol. Lo que alumbra cerca (fuegos, velas) se sumará con F3-11.
static func light_at(
	space: PhysicsDirectSpaceState3D, point: Vector3, context: Dictionary, exclude: Array[RID]
) -> float:
	var hour: float = context.get("hour", 12.0)
	var light: float = ambient(hour)
	if blocked(space, point, point + Vector3.UP * ROOF_CHECK, exclude):
		return light * INSIDE
	var sun: Vector3 = context.get("sun", Vector3.ZERO)
	# A la sombra solo se está si hay sol (de día y por encima del horizonte).
	if light > DUSK_LIGHT and sun.y > 0.05:
		if blocked(space, point, point + sun * SUN_CHECK, exclude):
			light *= SHADE
	return light


## Visto desde [param eye], detrás de [param point] solo hay cielo.
static func against_sky(
	space: PhysicsDirectSpaceState3D, eye: Vector3, point: Vector3, exclude: Array[RID]
) -> bool:
	var direction: Vector3 = point - eye
	if direction.length() < 0.01:
		return false
	direction = direction.normalized()
	if direction.y < SKY_MIN_RISE:
		return false
	return not blocked(space, point, point + direction * SKY_CHECK, exclude)


## Hay algo del mundo entre [param from] y [param to].
static func blocked(
	space: PhysicsDirectSpaceState3D, from: Vector3, to: Vector3, exclude: Array[RID]
) -> bool:
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, to, SIGHT_MASK, exclude
	)
	query.hit_back_faces = false
	return not space.intersect_ray(query).is_empty()
