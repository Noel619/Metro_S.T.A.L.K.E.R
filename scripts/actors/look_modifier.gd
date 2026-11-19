class_name LookModifier
extends SkeletonModifier3D
## Inclina la columna y la cabeza hacia donde mira el jugador, y hacia un lado
## cuando se asoma (F3-01).
##
## Se aplica encima de la animación, así que el cuerpo puede moverse "a saltos"
## mientras la mirada sigue al ratón con suavidad. El giro se reparte entre
## varios huesos para que no parezca que solo se mueve el cuello.

## Reparto de la mirada entre los huesos, de abajo arriba.
const SHARES: Dictionary = {&"Spine": 0.12, &"Chest": 0.18, &"Neck": 0.3, &"Head": 0.4}
## Al asomarse se dobla sobre todo la cintura; la cabeza se endereza un poco.
const LEAN_SHARES: Dictionary = {&"Spine": 0.45, &"Chest": 0.4, &"Neck": 0.25, &"Head": -0.1}
## Lo que se inclina asomado del todo.
const LEAN_ANGLE: float = deg_to_rad(38.0)

## Ángulo de la mirada en radianes: positivo hacia arriba.
var pitch: float = 0.0
## Lo que se asoma, de -1 (a la izquierda) a 1 (a la derecha).
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
		# y asomarse a la derecha, girar alrededor de +Z (la cabeza va hacia -X).
		var turn: Quaternion = (
			Quaternion(Vector3.RIGHT, -pitch * float(SHARES[bone_name]))
			* Quaternion(Vector3.BACK, lean * LEAN_ANGLE * float(LEAN_SHARES[bone_name]))
		)
		var parent: int = skeleton.get_bone_parent(bone)
		var parent_rotation: Quaternion = Quaternion.IDENTITY
		if parent >= 0:
			parent_rotation = skeleton.get_bone_global_pose(parent).basis.get_rotation_quaternion()
		var local: Quaternion = skeleton.get_bone_pose_rotation(bone)
		skeleton.set_bone_pose_rotation(
			bone, parent_rotation.inverse() * turn * parent_rotation * local
		)
