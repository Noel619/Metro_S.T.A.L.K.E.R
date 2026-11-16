class_name GripModifier
extends SkeletonModifier3D
## Lleva las manos de primera persona a los lados de lo que el jugador sujeta.
##
## La animación "sostener" deja las manos a una distancia fija. Este
## modificador las corrige cada fotograma con el tamaño y la posición reales
## del objeto: una caja grande separa las manos, una pequeña las junta, y lo
## que cabe en una mano (una lata, una botella) se lleva solo con la derecha
## mientras la izquierda baja. Como mira dónde está el objeto de verdad, las
## manos también lo siguen cuando se acerca a los ojos para inspeccionarlo o
## cuando se queda atrás porque pesa.

## Los dos brazos: nombre de sus huesos y lado (-1 izquierda, +1 derecha).
const SIDES: Dictionary = {&"Left": -1.0, &"Right": 1.0}
## Punto de la palma, en los ejes del hueso de la mano (Y va hacia los dedos).
const PALM: Vector3 = Vector3(0.0, 0.06, 0.0)
## Hueco entre el costado del objeto y el centro de la palma.
const PALM_GAP: float = 0.018
## Lo más que se separa una mano del centro, y lo cerca o lejos que llega.
const MAX_SPREAD: float = 0.46
const NEAR: float = 0.3
const FAR: float = 0.82
const LOWEST: float = -0.55
const HIGHEST: float = 0.12
## Altura del agarre dentro del objeto: 0 es su base y 1 su parte de arriba.
const GRIP_HEIGHT: float = 0.38
## Lo que cabe en una mano: así de estrecho y así de ligero, como mucho.
const ONE_HAND_WIDTH: float = 0.14
const ONE_HAND_WEIGHT: float = 1.5
## Dónde se va la mano que no hace falta (en los ejes de la cámara).
const IDLE_DROP: Vector3 = Vector3(-0.06, -0.42, 0.16)
## Rapidez con la que las manos alcanzan su sitio.
const FOLLOW: float = 16.0

## Nodo que define los ejes de la cámara (las manos cuelgan de ella).
var view: Node3D
## Dónde quiere cada mano su palma, en los ejes de la cámara. Para pruebas.
var targets: Dictionary = {}

var _body: Node3D
var _bounds: AABB
var _one_handed: bool = false
var _offsets: Dictionary = {&"Left": Vector3.ZERO, &"Right": Vector3.ZERO}


## ¿Se lleva con una sola mano algo con estas medidas (en metros) y este peso?
static func fits_one_hand(size: Vector3, weight: float) -> bool:
	return minf(size.x, size.z) <= ONE_HAND_WIDTH and weight <= ONE_HAND_WEIGHT


## Dónde va la palma de cada mano para sujetar una caja [param box], dada en
## los ejes de la cámara (X a la derecha, Y arriba, -Z al frente).
static func grip_points(box: AABB, one_handed: bool) -> Dictionary:
	var height: float = lerpf(box.position.y, box.end.y, 0.5 if one_handed else GRIP_HEIGHT)
	height = clampf(height, LOWEST, HIGHEST)
	var depth: float = clampf(box.get_center().z + 0.03, -FAR, -NEAR)
	var points: Dictionary = {
		&"Right": Vector3(clampf(box.end.x + PALM_GAP, PALM_GAP, MAX_SPREAD), height, depth)
	}
	if not one_handed:
		points[&"Left"] = Vector3(
			clampf(box.position.x - PALM_GAP, -MAX_SPREAD, -PALM_GAP), height, depth
		)
	return points


## Medidas de un objeto: la caja que envuelve sus mallas, en sus propios ejes.
static func bounds_of(body: Node3D) -> AABB:
	var bounds: AABB = AABB()
	var first: bool = true
	var inverse: Transform3D = body.global_transform.affine_inverse()
	for node: Node in body.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = node as MeshInstance3D
		var box: AABB = (inverse * mesh.global_transform) * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	return bounds


## Empieza a sujetar [param body], que pesa [param weight] kilos.
func grip(body: Node3D, weight: float) -> void:
	_body = body
	_bounds = bounds_of(body)
	_one_handed = fits_one_hand(_bounds.size, weight)


func release() -> void:
	_body = null
	targets = {}


func is_one_handed() -> bool:
	return _body != null and _one_handed


func _process_modification_with_delta(delta: float) -> void:
	var skeleton: Skeleton3D = get_skeleton()
	if skeleton == null or view == null:
		return
	if _body != null and not is_instance_valid(_body):
		release()
	# De los ejes de la cámara a los del esqueleto.
	var to_skeleton: Transform3D = (
		skeleton.global_transform.affine_inverse() * view.global_transform
	)
	targets = {}
	if _body != null:
		var box: AABB = (view.global_transform.affine_inverse() * _body.global_transform) * _bounds
		targets = grip_points(box, _one_handed)
	var weight: float = 1.0 - exp(-FOLLOW * delta)
	for side: StringName in SIDES:
		var arm: int = skeleton.find_bone(String(side) + "LowerArm")
		var hand: int = skeleton.find_bone(String(side) + "Hand")
		if arm < 0 or hand < 0:
			continue
		var wanted: Vector3 = Vector3.ZERO
		if targets.has(side):
			wanted = (
				to_skeleton * (targets[side] as Vector3)
				- skeleton.get_bone_global_pose(hand) * PALM
			)
		elif _body != null:
			# La mano que sobra baja y se aparta.
			var drop: Vector3 = Vector3(
				IDLE_DROP.x * float(SIDES[side]) * -1.0, IDLE_DROP.y, IDLE_DROP.z
			)
			wanted = to_skeleton.basis * drop
		_offsets[side] = (_offsets[side] as Vector3).lerp(wanted, weight)
		skeleton.set_bone_pose_position(arm, skeleton.get_bone_pose_position(arm) + _offsets[side])
