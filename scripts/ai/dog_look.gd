class_name DogLook
extends SkeletonModifier3D
## La cabeza de un perro (F3-10): sigue lo que le interesa (un ruido, una presa)
## y, al seguir un rastro, baja el hocico al suelo. Va encima de la animación, así
## que el cuerpo se mueve "a saltos" y la cabeza con suavidad.

## Reparto del giro entre el cuello y la cabeza.
const SHARES: Dictionary = {&"Neck": 0.55, &"Head": 0.45}
## Lo más que gira a cada lado y arriba o abajo (radianes).
const MAX_YAW: float = 1.1
const MAX_PITCH: float = 0.6
## Con el hocico al suelo: lo que baja.
const SNIFF_PITCH: float = 0.75
const FOLLOW_SPEED: float = 6.0

## Hacia dónde mirar, en el mundo (INF: al frente).
var target: Vector3 = Vector3.INF
## De 0 a 1: el hocico al suelo.
var sniff: float = 0.0

var _yaw: float = 0.0
var _pitch: float = 0.0


func _process_modification() -> void:
	var skeleton: Skeleton3D = get_skeleton()
	if skeleton == null:
		return
	var wanted_yaw: float = 0.0
	var wanted_pitch: float = -sniff * SNIFF_PITCH
	var head: int = skeleton.find_bone(&"Head")
	if target != Vector3.INF and head >= 0:
		# El modelo mira a +Z en su espacio (el perro está girado medio vuelta).
		var origin: Vector3 = skeleton.global_transform * skeleton.get_bone_global_pose(head).origin
		var local: Vector3 = skeleton.global_basis.inverse() * (target - origin)
		if local.length() > 0.3:
			wanted_yaw = clampf(atan2(local.x, local.z), -MAX_YAW, MAX_YAW)
			var flat: float = Vector2(local.x, local.z).length()
			wanted_pitch += clampf(atan2(local.y, flat), -MAX_PITCH, MAX_PITCH)
	var step: float = clampf(get_process_delta_time() * FOLLOW_SPEED, 0.0, 1.0)
	_yaw = lerpf(_yaw, wanted_yaw, step)
	_pitch = lerpf(_pitch, clampf(wanted_pitch, -1.2, MAX_PITCH), step)
	if is_zero_approx(_yaw) and is_zero_approx(_pitch):
		return
	for bone_name: StringName in SHARES:
		var bone: int = skeleton.find_bone(bone_name)
		if bone < 0:
			continue
		var share: float = float(SHARES[bone_name])
		# Girar a un lado es sobre su arriba; mirar arriba, sobre su izquierda (+X), hacia atrás.
		var turn: Quaternion = (
			Quaternion(Vector3.UP, _yaw * share) * Quaternion(Vector3.RIGHT, -_pitch * share)
		)
		var parent: int = skeleton.get_bone_parent(bone)
		var parent_rotation: Quaternion = Quaternion.IDENTITY
		if parent >= 0:
			parent_rotation = skeleton.get_bone_global_pose(parent).basis.get_rotation_quaternion()
		var local_rotation: Quaternion = skeleton.get_bone_pose_rotation(bone)
		skeleton.set_bone_pose_rotation(
			bone, parent_rotation.inverse() * turn * parent_rotation * local_rotation
		)
