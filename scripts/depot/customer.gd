class_name Customer
extends Node3D
## Alguien de la estación que no es un jugador: un cliente que viene a la
## ventanilla (F2-09) o la vendedora del puesto de comida (F2-11).
##
## Lo mueve el anfitrión (anda en línea recta de un punto a otro) y los demás lo
## ven por un sincronizador: dónde está, hacia dónde mira, si anda y qué cara
## pone. No habla: deja papelitos.

signal arrived

const WALK_SPEED: float = 1.05
const TURN_SPEED: float = 6.0
const ARRIVE_DISTANCE: float = 0.06
const SYNCED: PackedStringArray = [".:position", ".:rotation", ".:walking", ".:face"]

var data: CustomerData
## Anda (lo ve el avatar).
var walking: bool = false
## La cara que pone (una de [constant PlayerAvatar.EXPRESSIONS]).
var face: StringName = &"neutro":
	set(value):
		face = value
		if _avatar != null:
			_avatar.expression = value

var _avatar: PlayerAvatar
var _path: Array[Vector3] = []
var _facing: float = 0.0


## Monta el cliente. Igual en todos los equipos, antes de entrar en escena.
func setup(customer_id: StringName, where: Vector3) -> void:
	data = CustomerData.by_id(customer_id)
	name = "cliente_%s" % customer_id
	position = where
	_avatar = PlayerAvatar.new()
	_avatar.name = "Avatar"
	_avatar.variant = data.variant if data != null else "chico"
	_avatar.backpack_visible = false
	_avatar.bag_visible = false
	_avatar.mask_visible = false
	if data != null:
		_avatar.cloth_color = data.cloth_color
	add_child(_avatar)
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


func _ready() -> void:
	_facing = rotation.y


## Echa a andar por [param points] (en el mundo). Solo el anfitrión.
func walk(points: Array[Vector3]) -> void:
	_path = points.duplicate()
	walking = not _path.is_empty()


## Se vuelve hacia [param where].
func face_towards(where: Vector3) -> void:
	var flat: Vector3 = where - global_position
	flat.y = 0.0
	if flat.length() > 0.01:
		_facing = atan2(-flat.x, -flat.z)


func is_walking() -> bool:
	return walking


func _process(delta: float) -> void:
	if _avatar != null:
		_avatar.speed = WALK_SPEED if walking else 0.0
	if not multiplayer.is_server():
		return
	if not _path.is_empty():
		var target: Vector3 = _path[0]
		var flat: Vector3 = target - global_position
		flat.y = 0.0
		if flat.length() <= ARRIVE_DISTANCE:
			_path.pop_front()
			if _path.is_empty():
				walking = false
				arrived.emit()
		else:
			_facing = atan2(-flat.x, -flat.z)
			global_position += flat.normalized() * minf(WALK_SPEED * delta, flat.length())
	rotation.y = lerp_angle(rotation.y, _facing, minf(1.0, TURN_SPEED * delta))
