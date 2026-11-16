class_name GripModifier
extends SkeletonModifier3D
## Lleva las manos de primera persona a lo que el jugador sujeta.
##
## Cuando el objeto llega a las manos, busca con rayos en su malla dónde apoyar
## las palmas: con dos manos, en la esquina de delante de cada costado (en lo
## redondo, algo más atrás), a varias alturas; lo que cabe en una mano (una
## lata, una botella, el palo de la escoba), por el medio, solo con la derecha y
## con los dedos cerrados alrededor. Esos puntos se guardan en los ejes del
## objeto, así que las manos van pegadas a él lo mires como lo mires y aunque se
## mueva (D-028). Como lo que se lleva va derecho en el mundo, al mirar abajo su
## parte de abajo se esconde: las manos pasan a agarrarlo más arriba. Y si gira
## tanto que sus costados dejan de quedar a los lados (al inspeccionarlo), lo
## vuelven a agarrar por los que ahora sí lo están.
##
## El modelo solo tiene antebrazos: cada uno se orienta para que la palma quede
## sobre el objeto, mirándolo, sin doblar la muñeca de más y con el final de la
## manga fuera de la vista.

## Los dos brazos: nombre de sus huesos y lado (-1 izquierda, +1 derecha).
const SIDES: Dictionary = {&"Left": -1.0, &"Right": 1.0}
## Punto de la palma, en los ejes del hueso de la mano (Y va hacia los dedos).
const PALM: Vector3 = Vector3(0.0, 0.06, 0.0)
## Hueco entre la superficie del objeto y el centro de la palma.
const PALM_GAP: float = 0.018
## Del codo a la muñeca; de la muñeca al final de la manga, y lo que abulta.
const FOREARM: float = 0.3
const SLEEVE: float = 0.36
const SLEEVE_RADIUS: float = 0.06
## Dónde queda la muñeca respecto al centro de la palma, más o menos, al sujetar.
const WRIST_BELOW: float = 0.07
const WRIST_BEHIND: float = 0.03
## Alturas a las que puede ir el agarre dentro del objeto (0 es su base y 1 su
## parte de arriba): con dos manos, la más baja que se vea desde los ojos; con
## una, siempre la misma.
const GRIP_HEIGHTS: Array[float] = [0.25, 0.4, 0.55, 0.7, 0.82, 0.94]
const ONE_HAND_HEIGHT: float = 0.45
## Con dos manos, el agarre va a la esquina de delante de cada costado (partes
## de su fondo), con los dedos rodeándola: más atrás, la cara de delante
## taparía las manos. En lo redondo, eso ya es la cara de delante: si ahí la
## superficie mira demasiado al frente, el agarre se retrasa hacia el costado.
const GRIP_NEAR: Array[float] = [0.92, 0.6, 0.3]
const SIDE_FACING: float = 0.65
## Una palma a menos de esto del borde de abajo de la vista ya no se ve bien; al
## buscarle otro sitio, se pide algo más de margen (para que no vaya y venga).
const HIDDEN_MARGIN: float = 0.03
const SEEN_MARGIN: float = 0.06
## Las manos agarran cuando el objeto ya ha llegado a ellas (se mueve poco
## respecto a la cámara y está a su alcance), o tras esperar esto.
const SETTLED_SPEED: float = 0.8
const SETTLED_REACH: float = 1.2
const GRIP_WAIT: float = 0.5
## Cada cuánto se mira si las manos se han quedado fuera de la vista.
const HIDDEN_CHECK: float = 0.2
## Lo que cabe en una mano: así de estrecho y así de ligero, como mucho.
const ONE_HAND_WIDTH: float = 0.14
const ONE_HAND_WEIGHT: float = 1.5
## Hacia dónde apuntan los dedos (en los ejes de la cámara): al frente y algo
## arriba. Con dos manos rodean la esquina; con una, el objeto entero.
const FINGERS_TWO_HANDS: Vector3 = Vector3(0.0, 0.45, -0.89)
const FINGERS_ONE_HAND: Vector3 = Vector3(0.0, 0.25, -0.97)
## Hacia dónde va el antebrazo derecho (del codo a la muñeca) si nada lo impide.
const FOREARM_TWO_HANDS: Vector3 = Vector3(-0.31, 0.84, -0.45)
const FOREARM_ONE_HAND: Vector3 = Vector3(-0.2, 0.62, -0.76)
## Lo más que se dobla la muñeca, en radianes.
const WRIST_BEND: float = 0.75
## Lo que se cierran los dedos, por falange: alrededor de algo estrecho y
## alrededor de una esquina.
const CURL: float = 0.85
const CURL_TWO_HANDS: float = 0.4
const CURL_SHARES: Dictionary = {&"Proximal": 1.0, &"Intermediate": 1.1, &"Distal": 0.7}
const FINGERS: Array[StringName] = [&"Index", &"Middle", &"Ring", &"Little"]
## Rapidez con la que las manos llegan al objeto (o lo dejan) y cambian de agarre.
const BLEND_SPEED: float = 7.0
const REGRIP_SPEED: float = 14.0
## Un costado deja de servir cuando ya casi no mira hacia su lado.
const SIDE_LIMIT: float = 0.3

## Nodo que define los ejes de la cámara (las manos cuelgan de ella).
var view: Node3D
## La cámara, para saber qué se ve.
var camera: Camera3D
## Dónde quiere cada mano el centro de su palma, en los ejes de la cámara. Para pruebas.
var targets: Dictionary = {}

var _body: Node3D
var _bounds: AABB = AABB()
## Los triángulos de su malla, en sus propios ejes (de tres en tres).
var _faces: PackedVector3Array = []
var _one_handed: bool = false
## Dónde puede agarrar cada mano, de abajo arriba, y dónde agarra: [punto,
## normal] en los ejes del objeto. El agarre que se quiere y el que se lleva
## ahora (que va hacia el otro al cambiar de agarre).
var _candidates: Dictionary = {}
var _grips: Dictionary = {}
var _held_grips: Dictionary = {}
## Cuánto manda el agarre sobre cada brazo (0: la animación; 1: el agarre).
var _amounts: Dictionary = {&"Left": 0.0, &"Right": 0.0}
## La última pose de agarre de cada brazo, para soltar el objeto con suavidad.
var _poses: Dictionary = {}
## Desde que se cogió, y dónde estaba el objeto (en los ejes de la cámara).
var _waited: float = 0.0
var _last_place: Vector3 = Vector3.ZERO
## El agarre se eligió sin que el objeto hubiera llegado (tardaba): se vuelve a
## elegir cuando llegue.
var _provisional: bool = false
## Dice si el objeto ya está en las manos (si no se da, se deduce de cómo se mueve).
var _arrived: Callable = Callable()
## Lo que falta para volver a mirar si las manos se ven.
var _hidden_check: float = 0.0


## ¿Se lleva con una sola mano algo con estas medidas (en metros) y este peso?
static func fits_one_hand(size: Vector3, weight: float) -> bool:
	return minf(size.x, size.z) <= ONE_HAND_WIDTH and weight <= ONE_HAND_WEIGHT


## Medias medidas, a lo largo de X, Y y Z, de una caja de medias medidas
## [param half] girada con [param turn].
static func extent(turn: Basis, half: Vector3) -> Vector3:
	return Vector3(
		absf(turn.x.x) * half.x + absf(turn.y.x) * half.y + absf(turn.z.x) * half.z,
		absf(turn.x.y) * half.x + absf(turn.y.y) * half.y + absf(turn.z.y) * half.z,
		absf(turn.x.z) * half.x + absf(turn.y.z) * half.y + absf(turn.z.z) * half.z
	)


## Lo más alto en la vista (en radianes, respecto a su centro) que puede ir el
## centro de algo sujeto a [param distance] de los ojos sin que se vea dónde
## acaban las mangas. [param fov] es el campo de visión vertical, en grados.
static func highest_center(distance: float, fov: float) -> float:
	var half: float = deg_to_rad(fov) / 2.0
	var top: float = (
		(SLEEVE - SLEEVE_RADIUS - sin(half) * (distance - WRIST_BEHIND)) / cos(half) + WRIST_BELOW
	)
	return atan2(top, distance)


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


## Los triángulos de las mallas de un objeto, en sus propios ejes.
static func faces_of(body: Node3D) -> PackedVector3Array:
	var faces: PackedVector3Array = []
	var inverse: Transform3D = body.global_transform.affine_inverse()
	for node: Node in body.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = node as MeshInstance3D
		if mesh.mesh != null:
			faces.append_array((inverse * mesh.global_transform) * mesh.mesh.get_faces())
	return faces


## El primer punto de [param faces] que toca un rayo, con la normal de esa cara
## vuelta hacia el rayo: [punto, normal], o vacío si no toca nada.
static func ray_hit(faces: PackedVector3Array, from: Vector3, direction: Vector3) -> Array:
	var best: float = INF
	var hit: Array = []
	for index: int in range(0, faces.size() - 2, 3):
		var point: Variant = Geometry3D.ray_intersects_triangle(
			from, direction, faces[index], faces[index + 1], faces[index + 2]
		)
		if point == null or from.distance_to(point) >= best:
			continue
		best = from.distance_to(point)
		var normal: Vector3 = (
			(faces[index + 1] - faces[index]).cross(faces[index + 2] - faces[index]).normalized()
		)
		hit = [point, -normal if normal.dot(direction) > 0.0 else normal]
	return hit


## Empieza a sujetar [param body], que pesa [param weight] kilos. Las manos lo
## agarran cuando ha llegado a ellas: lo dice [param arrived] (sin argumentos,
## devuelve si ya está) o, si no se da, cuando deja de moverse respecto a la cámara.
func grip(body: Node3D, weight: float, arrived: Callable = Callable()) -> void:
	_body = body
	_arrived = arrived
	_bounds = bounds_of(body)
	_faces = faces_of(body)
	_one_handed = fits_one_hand(_bounds.size, weight)
	_candidates = {}
	_grips = {}
	_held_grips = {}
	_waited = 0.0
	_last_place = Vector3.INF
	_provisional = false


func release() -> void:
	_body = null
	_candidates = {}
	_grips = {}
	_held_grips = {}
	targets = {}


func is_one_handed() -> bool:
	return _body != null and _one_handed


func _process_modification_with_delta(delta: float) -> void:
	var skeleton: Skeleton3D = get_skeleton()
	if skeleton == null or view == null:
		return
	if _body != null and not is_instance_valid(_body):
		release()
	targets = {}
	var placed: Transform3D = Transform3D.IDENTITY
	if _body != null:
		# El objeto en los ejes de la cámara.
		placed = view.global_transform.affine_inverse() * _body.global_transform
		if _grips.is_empty() or _provisional:
			var settled: bool = _settled(placed.origin, delta)
			if settled or (_grips.is_empty() and _waited > GRIP_WAIT):
				_choose_grips(placed)
				_provisional = not settled
		elif _grips_lost(placed):
			_choose_grips(placed)
		elif _grips_hidden(placed, delta):
			_pick_grips(placed)
		var follow: float = 1.0 - exp(-REGRIP_SPEED * delta)
		for side: StringName in _grips:
			var goal: Array = _grips[side]
			var held: Array = _held_grips[side]
			held[0] = (held[0] as Vector3).lerp(goal[0], follow)
			held[1] = (held[1] as Vector3).lerp(goal[1], follow).normalized()
	var to_skeleton: Transform3D = (
		skeleton.global_transform.affine_inverse() * view.global_transform
	)
	for side: StringName in SIDES:
		var gripping: bool = _held_grips.has(side)
		_amounts[side] = move_toward(_amounts[side], 1.0 if gripping else 0.0, BLEND_SPEED * delta)
		if gripping:
			_poses[side] = _arm_pose(side, placed, to_skeleton)
		if _amounts[side] > 0.0 and _poses.has(side):
			_apply(skeleton, side, _poses[side], smoothstep(0.0, 1.0, _amounts[side]))
		elif not gripping:
			_poses.erase(side)


func _sides() -> Array[StringName]:
	if _one_handed:
		return [&"Right"]
	return [&"Left", &"Right"]


## ¿Ha llegado ya a las manos lo que se ha cogido? (Mientras vuela desde donde
## estaba, se mueve deprisa respecto a la cámara.)
func _settled(place: Vector3, delta: float) -> bool:
	_waited += delta
	var speed: float = place.distance_to(_last_place) / maxf(delta, 0.0001)
	_last_place = place
	if _arrived.is_valid():
		return bool(_arrived.call())
	return speed < SETTLED_SPEED and place.length() < SETTLED_REACH


## ¿Ha girado el objeto tanto que algún costado ya no mira a su lado?
func _grips_lost(placed: Transform3D) -> bool:
	for side: StringName in _grips:
		var normal: Vector3 = placed.basis * ((_grips[side] as Array)[1] as Vector3)
		if normal.normalized().x * float(SIDES[side]) < SIDE_LIMIT:
			return true
	return false


## ¿Han quedado las manos en el borde de abajo de la vista, o fuera? Lo que se
## lleva va derecho en el mundo, así que al mirar abajo gira respecto a la
## cámara y su parte de abajo se esconde. Se mira de vez en cuando.
func _grips_hidden(placed: Transform3D, delta: float) -> bool:
	if _one_handed or _candidates.is_empty():
		return false
	_hidden_check -= delta
	if _hidden_check > 0.0:
		return false
	_hidden_check = HIDDEN_CHECK
	for side: StringName in _held_grips:
		if _seen(placed, _held_grips[side]) > HIDDEN_MARGIN:
			return false
	return true


## Lo que se adentra en la vista una palma puesta en [param grip] (por debajo
## de cero, queda bajo su borde de abajo).
func _seen(placed: Transform3D, grip: Array) -> float:
	var normal: Vector3 = placed.basis * (grip[1] as Vector3)
	return _frustum()[0].dot(placed * (grip[0] as Vector3) + normal * PALM_GAP)


## Busca en la malla dónde pueden ir las palmas, con el objeto colocado así
## respecto a la cámara ([param placed]): primero, qué ejes suyos van de lado a
## lado, hacia uno y hacia arriba; después, con rayos en esos ejes, los puntos
## de cada costado a varias alturas, cerca de su esquina de delante.
func _choose_grips(placed: Transform3D) -> void:
	var axes: Array[int] = [0, 1, 2]
	var across: int = _strongest(placed.basis, axes, 0)
	axes.erase(across)
	var toward: int = _strongest(placed.basis, axes, 2)
	axes.erase(toward)
	var up: int = axes[0]
	var right: Vector3 = _axis(placed.basis, across, 0)
	var front: Vector3 = _axis(placed.basis, toward, 2)
	var top: Vector3 = _axis(placed.basis, up, 1)
	var half: Vector3 = _bounds.size / 2.0
	var center: Vector3 = _bounds.get_center()
	var heights: Array[float] = GRIP_HEIGHTS
	var depths: Array[float] = GRIP_NEAR
	if _one_handed:
		heights = [ONE_HAND_HEIGHT]
		depths = [0.0]
	_candidates = {}
	for side: StringName in _sides():
		var outward: Vector3 = right * float(SIDES[side])
		var found: Array = []
		for height: float in heights:
			for depth: float in depths:
				var aim: Vector3 = (
					center
					+ top * ((height - 0.5) * 2.0 * half[up])
					+ front * (depth * half[toward])
				)
				var hit: Array = ray_hit(_faces, aim + outward * (half[across] + 0.3), -outward)
				if not hit.is_empty() and (hit[1] as Vector3).dot(front) < SIDE_FACING:
					found.append(hit)
					break
		if found.is_empty():
			# Sin malla que tocar: el costado de la caja que lo envuelve.
			found.append([center + outward * half[across], outward])
		_candidates[side] = found
	_pick_grips(placed)


## Elige, de los sitios posibles, el de cada palma: el más bajo que se vea bien
## (si ninguno se ve bien, el que más se vea).
func _pick_grips(placed: Transform3D) -> void:
	_grips = {}
	for side: StringName in _candidates:
		var found: Array = _candidates[side]
		var chosen: Array = found[0]
		if not _one_handed:
			for candidate: Array in found:
				if _seen(placed, candidate) > SEEN_MARGIN:
					chosen = candidate
					break
				if _seen(placed, candidate) > _seen(placed, chosen):
					chosen = candidate
		_grips[side] = chosen
		if not _held_grips.has(side):
			_held_grips[side] = chosen.duplicate()
	for side: StringName in _held_grips.keys():
		if not _grips.has(side):
			_held_grips.erase(side)


## De los ejes del objeto [param axes] (0, 1, 2), el que más se parece al eje
## [param camera_axis] de la cámara, visto desde ella.
static func _strongest(turn: Basis, axes: Array[int], camera_axis: int) -> int:
	var best: int = axes[0]
	for axis: int in axes:
		if absf(turn[axis][camera_axis]) > absf(turn[best][camera_axis]):
			best = axis
	return best


## El eje [param axis] del objeto, en sus propios ejes, con el sentido que va
## hacia el lado positivo del eje [param camera_axis] de la cámara.
static func _axis(turn: Basis, axis: int, camera_axis: int) -> Vector3:
	var direction: Vector3 = Vector3.ZERO
	direction[axis] = 1.0 if turn[axis][camera_axis] >= 0.0 else -1.0
	return direction


## Pose de un brazo para que su palma quede en su agarre: el antebrazo en los
## ejes del esqueleto y el giro de la mano respecto al antebrazo.
func _arm_pose(side: StringName, placed: Transform3D, to_skeleton: Transform3D) -> Dictionary:
	var sign: float = SIDES[side]
	var held: Array = _held_grips[side]
	var normal: Vector3 = (placed.basis * (held[1] as Vector3)).normalized()
	var palm: Vector3 = placed * (held[0] as Vector3) + normal * PALM_GAP
	targets[side] = palm
	# El eje X del hueso de la mano atraviesa la palma: en la derecha sale por el
	# dorso (hacia fuera del objeto); en la izquierda, por la palma.
	var across: Vector3 = normal * sign
	var hint: Vector3 = (FINGERS_ONE_HAND if _one_handed else FINGERS_TWO_HANDS).normalized()
	var fingers: Vector3 = hint - across * hint.dot(across)
	if fingers.length() < 0.2:
		fingers = Vector3.UP - across * across.y
	fingers = fingers.normalized()
	var hand: Basis = Basis(across, fingers, across.cross(fingers))
	var wrist: Vector3 = palm - hand * PALM
	var forearm: Vector3 = _forearm_direction(side, wrist, fingers)
	var side_axis: Vector3 = across - forearm * across.dot(forearm)
	if side_axis.length() < 0.1:
		side_axis = Vector3.RIGHT - forearm * forearm.x
	side_axis = side_axis.normalized()
	var arm: Basis = Basis(side_axis, forearm, side_axis.cross(forearm))
	var arm_pose: Transform3D = to_skeleton * Transform3D(arm, wrist - forearm * FOREARM)
	return {
		"arm": arm_pose,
		"hand": (arm.inverse() * hand).get_rotation_quaternion(),
		"curl": CURL if _one_handed else CURL_TWO_HANDS,
	}


## Hacia dónde va un antebrazo, del codo a la muñeca [param wrist]: como suele
## ir, sin doblar la muñeca más de la cuenta respecto a los dedos y con el final
## de la manga fuera de la vista.
func _forearm_direction(side: StringName, wrist: Vector3, fingers: Vector3) -> Vector3:
	var sign: float = SIDES[side]
	var rest: Vector3 = FOREARM_ONE_HAND if _one_handed else FOREARM_TWO_HANDS
	var direction: Vector3 = Vector3(rest.x * sign, rest.y, rest.z).normalized()
	direction = _within(direction, fingers, WRIST_BEND)
	var frustum: Array[Vector3] = _frustum()
	var sleeve_end: Vector3 = wrist - direction * SLEEVE
	if frustum[1 if sign > 0.0 else 2].dot(sleeve_end) < -SLEEVE_RADIUS:
		return direction  # Ya sale por el borde de su lado.
	# Que salga por abajo: lo justo para que el final de la manga no se vea.
	var down: Vector3 = frustum[0]
	var needed: float = (down.dot(wrist) + SLEEVE_RADIUS) / SLEEVE
	if direction.dot(down) >= needed:
		return direction
	if needed >= 1.0:
		return down
	var across: Vector3 = direction - down * direction.dot(down)
	if across.length() < 0.001:
		return down
	return down * needed + across.normalized() * sqrt(1.0 - needed * needed)


## Campo de visión vertical, en grados.
func _fov() -> float:
	return camera.fov if camera != null else Player.FOV


## Las normales hacia dentro de los bordes de la vista: abajo, derecha e izquierda.
func _frustum() -> Array[Vector3]:
	var half: float = deg_to_rad(_fov()) / 2.0
	var aspect: float = 16.0 / 9.0
	if camera != null and camera.is_inside_tree():
		var size: Vector2 = camera.get_viewport().get_visible_rect().size
		if size.y > 0.0:
			aspect = clampf(size.x / size.y, 1.0, 2.4)
	var wide: float = atan(tan(half) * aspect)
	return [
		Vector3(0.0, cos(half), -sin(half)),
		Vector3(-cos(wide), 0.0, -sin(wide)),
		Vector3(cos(wide), 0.0, -sin(wide)),
	]


## [param direction] girado hacia [param axis] lo justo para que entre los dos
## no haya más de [param angle] radianes.
static func _within(direction: Vector3, axis: Vector3, angle: float) -> Vector3:
	var between: float = direction.angle_to(axis)
	if between <= angle:
		return direction
	return axis.slerp(direction, angle / between).normalized()


## Aplica una pose de agarre a un brazo, mezclada con la animación en [param amount].
func _apply(skeleton: Skeleton3D, side: StringName, pose: Dictionary, amount: float) -> void:
	var arm: int = skeleton.find_bone(String(side) + "LowerArm")
	var hand: int = skeleton.find_bone(String(side) + "Hand")
	if arm < 0 or hand < 0:
		return
	var wanted: Transform3D = pose["arm"]
	var parent: int = skeleton.get_bone_parent(arm)
	if parent >= 0:
		wanted = skeleton.get_bone_global_pose(parent).affine_inverse() * wanted
	skeleton.set_bone_pose_position(
		arm, skeleton.get_bone_pose_position(arm).lerp(wanted.origin, amount)
	)
	skeleton.set_bone_pose_rotation(
		arm,
		skeleton.get_bone_pose_rotation(arm).slerp(wanted.basis.get_rotation_quaternion(), amount)
	)
	skeleton.set_bone_pose_rotation(
		hand, skeleton.get_bone_pose_rotation(hand).slerp(pose["hand"] as Quaternion, amount)
	)
	var curl: float = float(pose["curl"]) * amount
	if curl <= 0.0:
		return
	# Los dedos se cierran hacia la palma (girando sobre su eje Z).
	var sign: float = SIDES[side]
	for finger: StringName in FINGERS:
		for part: StringName in CURL_SHARES:
			var bone: int = skeleton.find_bone(String(side) + finger + part)
			if bone >= 0:
				var close: Quaternion = Quaternion(
					Vector3.BACK, sign * curl * float(CURL_SHARES[part])
				)
				skeleton.set_bone_pose_rotation(bone, skeleton.get_bone_pose_rotation(bone) * close)
