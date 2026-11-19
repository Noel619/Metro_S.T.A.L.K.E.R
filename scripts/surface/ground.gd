class_name Ground
extends RefCounted
## Qué se pisa (F3-01): el suelo decide cuánto suena un paso ([NoiseRules]).
##
## Lo que tiene un suelo propio lo dice en sus metadatos ([constant META]: la chapa
## de un coche, los cascotes, los cristales de un escaparate). Lo demás, si está al
## aire libre, es nieve, porque es invierno; bajo techo, el suelo de dentro del
## edificio ([constant INSIDE_META], o el hormigón si no lo dice).

const META: StringName = &"suelo"
const INSIDE_META: StringName = &"suelo_interior"
const INSIDE_DEFAULT: StringName = &"hormigon"
## Lo que se busca un techo encima.
const ROOF_CHECK: float = 25.0
const MASK: int = 1 << 0


## El suelo del punto [param hit] (lo que devuelve un rayo hacia abajo) en [param space].
static func material_of(
	space: PhysicsDirectSpaceState3D, hit: Dictionary, exclude: Array[RID] = []
) -> StringName:
	var collider: Object = hit.get("collider")
	if collider != null and collider.has_meta(META):
		return StringName(collider.get_meta(META))
	var point: Vector3 = hit.get("position", Vector3.ZERO)
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		point + Vector3.UP * 0.3, point + Vector3.UP * ROOF_CHECK, MASK, exclude
	)
	var roof: Dictionary = space.intersect_ray(query)
	if roof.is_empty():
		return NoiseRules.DEFAULT_GROUND
	if collider != null and collider.has_meta(INSIDE_META):
		return StringName(collider.get_meta(INSIDE_META))
	return INSIDE_DEFAULT


## Lo que hay bajo [param feet] (un rayo corto hacia abajo), o vacío si no se pisa nada.
static func below(
	space: PhysicsDirectSpaceState3D, feet: Vector3, reach: float, exclude: Array[RID] = []
) -> Dictionary:
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		feet + Vector3.UP * 0.3, feet + Vector3.DOWN * reach, MASK, exclude
	)
	return space.intersect_ray(query)
