class_name LookModifier
extends SkeletonModifier3D
## Inclina la columna y la cabeza hacia donde mira el jugador.
##
## Se aplica encima de la animación, así que el cuerpo puede moverse "a saltos"
## mientras la mirada sigue al ratón con suavidad. El giro se reparte entre
## varios huesos para que no parezca que solo se mueve el cuello.

## Reparto de la mirada entre los huesos, de abajo arriba.
const SHARES: Dictionary = {&"Spine": 0.12, &"Chest": 0.18, &"Neck": 0.3, &"Head": 0.4}

## Asomarse: lo que se inclina el cuerpo a cada lado, repartido entre la columna,
## el pecho y el cuello (en radianes, con [member lean] a 1).
const LEAN_ANGLE: float = 0.32
const LEAN_SHARES: Dictionary = {&"Spine": 0.35, &"Chest": 0.4, &"Neck": 0.15, &"Head": 0.1}

## Ángulo de la mirada en radianes: positivo hacia arriba.
var pitch: float = 0.0
## Asomarse: de -1 (a la izquierda) a 1 (a la derecha).
var lean: float = 0.0


func _process_modification() -> void:
	var skeleton: Skeleton3D = get_skeleton()
	if skeleton == null or (is_zero_approx(pitch) and is_zero_approx(lean)):
		return
	for bone_name: StringName in SHARES:
		var bone: int = skeleton.find_bone(bone_name)
		if bone < 0:
			continue
		# El modelo mira a +Z y su izquierda es +X: mirar arriba es girar hacia atrás,
		# y asomarse a la derecha (su -X) es girar sobre su eje de delante.
		var turn: Quaternion = Quaternion(Vector3.RIGHT, -pitch * float(SHARES[bone_name]))
		turn = Quaternion(Vector3.BACK, lean * LEAN_ANGLE * float(LEAN_SHARES[bone_name])) * turn
		var parent: int = skeleton.get_bone_parent(bone)
		var parent_rotation: Quaternion = Quaternion.IDENTITY
		if parent >= 0:
			parent_rotation = skeleton.get_bone_global_pose(parent).basis.get_rotation_quaternion()
		var local: Quaternion = skeleton.get_bone_pose_rotation(bone)
		skeleton.set_bone_pose_rotation(
			bone, parent_rotation.inverse() * turn * parent_rotation * local
		)
