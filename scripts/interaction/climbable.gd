class_name Climbable
extends Node3D
## Lo que se sube trepando (F3-06, F3-14): una escalera de pates, una de mano o una
## cuerda. Su marco: el origen al pie, en el centro de los peldaños; +y arriba, hasta
## el rellano ([member height]); +z hacia quien trepa (los peldaños miran hacia ahí).
##
## Quien está delante (a menos de [member reach]) y empuja hacia ella, mirándola, se
## agarra: adelante sube y atrás baja. Arriba, adelante sale al rellano (que está
## detrás del borde, hacia -z); abajo, atrás suelta al tocar el suelo. Saltar suelta
## en cualquier sitio. Desde el rellano, andar hacia el borde, de espaldas a ella, es
## agarrarse para bajar. Los perros no trepan: arriba se está a salvo de ellos.

const GROUP: StringName = &"trepables"
const LADDER: StringName = &"escalera"
const ROPE: StringName = &"cuerda"

## Lo que mide: de ancho, de alto (del pie al rellano) y lo lejos que se alcanza.
@export var width: float = 0.6
@export var height: float = 3.0
@export var reach: float = 0.8
## Lo que se sube por segundo.
@export var speed: float = 1.1
## [constant LADDER] o [constant ROPE] (la cuerda se sube más despacio y cansa).
@export var kind: StringName = LADDER
## Lo que se avanza tras el borde al salir arriba (al rellano, a la azotea).
@export var landing_depth: float = 0.55


func _ready() -> void:
	add_to_group(GROUP)


## Una escalera o una cuerda de [param size] (ancho, alto y alcance) puesta en
## [param where] (el pie, con +z hacia quien trepa).
static func make(where: Transform3D, size: Vector3, type: StringName = LADDER) -> Climbable:
	var climbable: Climbable = Climbable.new()
	climbable.name = "Trepable"
	climbable.transform = where
	climbable.width = size.x
	climbable.height = size.y
	climbable.reach = size.z
	climbable.kind = type
	climbable.speed = 1.1 if type == LADDER else 0.6
	return climbable


## [param feet] (en el mundo) está delante de los peldaños, a su alcance.
func holds(feet: Vector3) -> bool:
	var local: Vector3 = global_transform.affine_inverse() * feet
	return (
		absf(local.x) <= width * 0.5 + 0.2
		and local.y >= -0.4
		and local.y <= height + 0.1
		and local.z >= -0.1
		and local.z <= reach
	)


## [param feet] está en el rellano, junto al borde de arriba.
func at_top(feet: Vector3) -> bool:
	var local: Vector3 = global_transform.affine_inverse() * feet
	return (
		absf(local.x) <= width * 0.5 + 0.25
		and local.y >= height - 0.3
		and local.y <= height + 0.6
		and local.z >= -1.0
		and local.z <= 0.2
	)


## [param direction] (se mira solo en horizontal) va hacia los peldaños.
func faces(direction: Vector3) -> bool:
	var into: Vector3 = -global_basis.z
	into.y = 0.0
	direction.y = 0.0
	if direction.length() < 0.01 or into.length() < 0.01:
		return false
	return direction.normalized().dot(into.normalized()) > 0.4


## La altura de [param feet] sobre el pie.
func level_of(feet: Vector3) -> float:
	return (global_transform.affine_inverse() * feet).y


## Dónde está quien trepa a la altura [param level]: delante de los peldaños, a
## [param gap] de ellos.
func hang_point(level: float, gap: float) -> Vector3:
	return global_transform * Vector3(0.0, level, gap)


## El rellano: [param depth] más allá del borde de arriba.
func landing(depth: float) -> Vector3:
	return global_transform * Vector3(0.0, height + 0.02, -depth)


## El rumbo (radianes) de quien mira a los peldaños.
func facing_yaw() -> float:
	var into: Vector3 = -global_basis.z
	return atan2(-into.x, -into.z)
