class_name Dog
extends CharacterBody3D
## Un perro de la Jauría (F3-10, docs/SUPERFICIE.md 7): su cuerpo, cómo se mueve y
## cómo se le ve. Lo que decide lo decide la manada ([Pack]), en el anfitrión; aquí
## se camina hacia donde se le manda por la rejilla de [CityNav], con el paso que se
## le pide, y se pone la pose que toca. Los demás equipos lo reciben replicado
## (dónde está, hacia dónde mira, su paso, su pose y lo que mira) y lo animan.
##
## Anima como los jugadores: la pose cambia 12 veces por segundo, "a saltos"; la
## cabeza ([DogLook]) sigue lo que le interesa con suavidad.

enum Gait { STILL, STALK, WALK, TROT, GALLOP }

const GROUP: StringName = &"perros"
const MODELS: Dictionary = {
	"vieja": "res://assets/models/perro_vieja.glb",
	"pardo": "res://assets/models/perro_pardo.glb",
	"negro": "res://assets/models/perro_negro.glb",
}
## Velocidad de cada paso (m/s), los metros que avanza cada ciclo de su animación
## (tools/blender/perro_anim.py) y su animación.
const SPEEDS: Dictionary = {
	Gait.STILL: 0.0, Gait.STALK: 0.8, Gait.WALK: 1.1, Gait.TROT: 2.9, Gait.GALLOP: 7.2
}
const CYCLES: Dictionary = {Gait.STALK: 0.8, Gait.WALK: 1.1, Gait.TROT: 1.6, Gait.GALLOP: 2.9}
const GAIT_ANIMATIONS: Dictionary = {
	Gait.STALK: &"acechar",
	Gait.WALK: &"andar",
	Gait.TROT: &"trote",
	Gait.GALLOP: &"galope",
}
## Las poses quietas.
const POSES: Dictionary = {
	&"quieto": &"quieto",
	&"vigilar": &"vigilar",
	&"grunir": &"grunir",
	&"olfatear": &"olfatear",
	&"comer": &"comer",
	&"echado": &"echado",
	&"aullar": &"aullar",
	&"morder": &"morder",
}
const ANIMATION_FPS: float = 12.0
const BLEND_TIME: float = 0.2
const GRAVITY: float = 9.8
const ACCELERATION: float = 9.0
## Lo que gira por segundo (radianes); galopando, menos.
const TURN_SPEED: float = 5.0
const GALLOP_TURN_SPEED: float = 2.6
## Llegó: a esta distancia del sitio.
const ARRIVE: float = 0.8
## Cada cuánto se rehace el camino si el sitio se mueve.
const REPATH_SECONDS: float = 1.0
## Se apartan de los demás perros a menos de esto.
const PERSONAL_SPACE: float = 1.4
const RADIUS: float = 0.32
const LAYER_DOGS: int = 1 << 3
const MASK_DOGS: int = (1 << 0) | (1 << 1) | (1 << 3)
const SYNCED: PackedStringArray = [
	".:position", ".:rotation", ".:gait", ".:pose", ".:move_speed", ".:look_point", ".:sniffing"
]

## El pelaje ("vieja", "pardo", "negro") y su puesto en la manada.
var coat: String = "pardo"
var index: int = 0
## Replicado: su paso, su pose (si está quieto), a qué velocidad va, qué mira y si
## lleva el hocico al suelo.
var gait: int = Gait.STILL
var pose: StringName = &"quieto"
var move_speed: float = 0.0
var look_point: Vector3 = Vector3.INF
var sniffing: bool = false
## Sus sentidos (en el anfitrión).
var perception: Perception
## Por dónde puede ir (en el anfitrión).
var nav: CityNav

var _model: Node3D
var _player: AnimationPlayer
var _look: DogLook
var _pending: float = 0.0
var _played: StringName = &""
var _goal: Vector3 = Vector3.INF
var _path: PackedVector2Array = PackedVector2Array()
var _path_index: int = 0
var _repath: float = 0.0
var _face: Vector3 = Vector3.INF


## Monta el perro (igual en todos los equipos, antes de entrar en escena).
func setup(new_coat: String, new_index: int, size: float) -> void:
	coat = new_coat if MODELS.has(new_coat) else "pardo"
	index = new_index
	name = "perro_%d" % index
	add_to_group(GROUP)
	collision_layer = LAYER_DOGS
	collision_mask = MASK_DOGS
	floor_max_angle = deg_to_rad(50.0)
	# De pie, como los jugadores: se mueve mejor que tumbada a lo largo del cuerpo.
	var shape: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	capsule.radius = RADIUS * size
	capsule.height = 0.9 * size
	shape.shape = capsule
	shape.position.y = 0.45 * size
	add_child(shape)
	_model = (load(MODELS[coat]) as PackedScene).instantiate()
	_model.name = "Modelo"
	# Los modelos miran a +Z; los cuerpos de Godot, a -Z.
	_model.rotation.y = PI
	_model.scale = Vector3.ONE * size
	add_child(_model)
	_player = _model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if _player != null:
		_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var skeleton: Skeleton3D = _model.find_child("Skeleton3D", true, false) as Skeleton3D
	if skeleton != null:
		_look = DogLook.new()
		_look.name = "Cabeza"
		skeleton.add_child(_look)
	var sync: MultiplayerSynchronizer = MultiplayerSynchronizer.new()
	sync.name = "Sincronizador"
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	for property: String in SYNCED:
		config.add_property(NodePath(property))
		config.property_set_spawn(NodePath(property), true)
		config.property_set_replication_mode(
			NodePath(property), SceneReplicationConfig.REPLICATION_MODE_ALWAYS
		)
	sync.replication_config = config
	add_child(sync)
	set_multiplayer_authority(1)
	perception = Perception.new()
	perception.name = "Sentidos"
	perception.body = self
	perception.eye_height = 0.95 * size
	add_child(perception)


func _process(delta: float) -> void:
	if _look != null:
		_look.target = look_point
		_look.sniff = move_toward(_look.sniff, 1.0 if sniffing else 0.0, delta * 3.0)
	_animate(delta)


func _physics_process(delta: float) -> void:
	if not multiplayer.is_server():
		return
	var wanted: Vector3 = Vector3.ZERO
	if _goal != Vector3.INF and gait != Gait.STILL:
		wanted = _steer(delta)
	var planar: Vector3 = Vector3(velocity.x, 0.0, velocity.z).move_toward(
		wanted, ACCELERATION * delta
	)
	planar += _separation() * delta * 4.0
	velocity = Vector3(
		planar.x, velocity.y - GRAVITY * delta if not is_on_floor() else 0.0, planar.z
	)
	move_and_slide()
	move_speed = Vector2(velocity.x, velocity.z).length()
	_turn(delta, Vector3(velocity.x, 0.0, velocity.z))


## Va hacia [param where] (en el mundo) al paso [param new_gait].
func go_to(where: Vector3, new_gait: Gait) -> void:
	gait = new_gait
	pose = &"quieto"
	_face = Vector3.INF
	if _goal != Vector3.INF and _goal.distance_to(where) < 1.5 and not _path.is_empty():
		_goal = where
		return
	_goal = where
	_plan_path()


## Se para (y, con [param new_pose], se pone así).
func stop(new_pose: StringName = &"quieto") -> void:
	gait = Gait.STILL
	_goal = Vector3.INF
	_path = PackedVector2Array()
	set_pose(new_pose)


## Se pone en una pose (quieto).
func set_pose(new_pose: StringName) -> void:
	if new_pose != pose or not POSES.has(new_pose):
		pose = new_pose if POSES.has(new_pose) else &"quieto"
		_played = &""


## Se gira hacia [param where] (quieto).
func face(where: Vector3) -> void:
	_face = where


## Ha llegado a donde iba (o no va a ninguna parte).
func arrived() -> bool:
	return _goal == Vector3.INF or _flat_distance(_goal) <= ARRIVE


## Va a alguna parte.
func is_moving() -> bool:
	return gait != Gait.STILL and _goal != Vector3.INF


## Hacia dónde mira (horizontal).
func forward() -> Vector3:
	var ahead: Vector3 = -global_basis.z
	ahead.y = 0.0
	return ahead.normalized()


## Lo que dice la herramienta de depuración (F3).
func debug_state() -> String:
	var gait_names: PackedStringArray = ["quieto", "acecho", "paso", "trote", "galope"]
	return "%s · %s" % [name, String(pose) if gait == Gait.STILL else gait_names[gait]]


func _plan_path() -> void:
	_repath = REPATH_SECONDS
	_path_index = 0
	var here: Vector2 = CityPlan.to_plan(global_position)
	var there: Vector2 = CityPlan.to_plan(_goal)
	if nav == null or nav.line_free(here, there):
		_path = PackedVector2Array([there])
		return
	_path = nav.path(here, there)
	if _path.is_empty():
		_path = PackedVector2Array([there])


func _steer(delta: float) -> Vector3:
	_repath -= delta
	if _repath <= 0.0:
		_plan_path()
	if arrived():
		_goal = Vector3.INF
		gait = Gait.STILL
		return Vector3.ZERO
	while _path_index < _path.size() - 1:
		var corner: Vector3 = CityPlan.to_world(_path[_path_index], global_position.y)
		if _flat_distance(corner) > ARRIVE:
			break
		_path_index += 1
	var next: Vector3 = CityPlan.to_world(
		_path[mini(_path_index, _path.size() - 1)], global_position.y
	)
	var direction: Vector3 = next - global_position
	direction.y = 0.0
	if direction.length() < 0.01:
		return Vector3.ZERO
	return direction.normalized() * float(SPEEDS[gait])


func _separation() -> Vector3:
	var push: Vector3 = Vector3.ZERO
	for node: Node in get_tree().get_nodes_in_group(GROUP):
		if node == self:
			continue
		var other: Vector3 = (node as Node3D).global_position
		var away: Vector3 = global_position - other
		away.y = 0.0
		var distance: float = away.length()
		if distance > 0.01 and distance < PERSONAL_SPACE:
			push += away.normalized() * (PERSONAL_SPACE - distance)
	return push


func _turn(delta: float, moving: Vector3) -> void:
	var facing: Vector3 = moving
	if facing.length() < 0.2:
		if _face == Vector3.INF:
			return
		facing = _face - global_position
		facing.y = 0.0
		if facing.length() < 0.1:
			return
	var wanted: float = atan2(-facing.x, -facing.z)
	var speed: float = GALLOP_TURN_SPEED if gait == Gait.GALLOP else TURN_SPEED
	rotation.y = rotate_toward(rotation.y, wanted, speed * delta)


func _flat_distance(point: Vector3) -> float:
	return Vector2(point.x - global_position.x, point.z - global_position.z).length()


func _animate(delta: float) -> void:
	if _player == null:
		return
	var animation: StringName = POSES.get(pose, &"quieto")
	var scale: float = 1.0
	if gait != Gait.STILL and move_speed > 0.2:
		animation = GAIT_ANIMATIONS[gait]
		scale = move_speed / float(CYCLES[gait]) * _player.get_animation(animation).length
	if animation != _played:
		_played = animation
		_player.play(animation, BLEND_TIME)
	_player.speed_scale = scale
	_pending += delta
	if _pending >= 1.0 / ANIMATION_FPS:
		_player.advance(_pending)
		_pending = 0.0
