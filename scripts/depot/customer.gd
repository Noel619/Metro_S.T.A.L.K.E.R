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
## Los complementos: [hueso, malla, color, posición, giro, escala].
const ACCESSORY_COLORS: Dictionary = {
	"gorra": Color("#3a3634"),
	"gafas": Color("#c8b070"),
	"panuelo": Color("#7a5a8a"),
}

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
	if data != null and not data.accessories.is_empty():
		_add_accessories.call_deferred()


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


## La gorra, las gafas o el pañuelo, colgados del hueso de la cabeza.
func _add_accessories() -> void:
	if _avatar == null:
		return
	var skeleton: Skeleton3D = _avatar.get_skeleton()
	if skeleton == null:
		return
	var head: int = skeleton.find_bone("Head")
	if head < 0:
		return
	var attachment: BoneAttachment3D = BoneAttachment3D.new()
	attachment.name = "Complementos"
	attachment.bone_name = "Head"
	skeleton.add_child(attachment)
	for accessory: String in data.accessories.split(",", false):
		var mesh: MeshInstance3D = _accessory_mesh(accessory.strip_edges())
		if mesh != null:
			attachment.add_child(mesh)


func _accessory_mesh(kind: String) -> MeshInstance3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = ACCESSORY_COLORS.get(kind, Color.GRAY)
	material.roughness = 0.9
	var mesh: MeshInstance3D = MeshInstance3D.new()
	mesh.name = kind
	match kind:
		"gorra":
			var cap: CylinderMesh = CylinderMesh.new()
			cap.top_radius = 0.1
			cap.bottom_radius = 0.115
			cap.height = 0.07
			mesh.mesh = cap
			mesh.position = Vector3(0.0, 0.16, 0.0)
			var brim: MeshInstance3D = MeshInstance3D.new()
			var board: BoxMesh = BoxMesh.new()
			board.size = Vector3(0.18, 0.012, 0.09)
			brim.mesh = board
			brim.material_override = material
			brim.position = Vector3(0.0, -0.03, -0.11)
			brim.rotation.x = deg_to_rad(-10.0)
			mesh.add_child(brim)
		"gafas":
			var rim: TorusMesh = TorusMesh.new()
			rim.inner_radius = 0.016
			rim.outer_radius = 0.021
			mesh.mesh = rim
			mesh.position = Vector3(0.033, 0.07, -0.1)
			mesh.rotation.x = PI / 2.0
			var other: MeshInstance3D = MeshInstance3D.new()
			other.mesh = rim
			other.material_override = material
			other.position = Vector3(-0.066, 0.0, 0.0)
			mesh.add_child(other)
		"panuelo":
			var scarf: SphereMesh = SphereMesh.new()
			scarf.radius = 0.125
			scarf.height = 0.2
			scarf.is_hemisphere = true
			mesh.mesh = scarf
			mesh.position = Vector3(0.0, 0.09, 0.012)
			mesh.scale = Vector3(1.0, 1.1, 1.08)
		_:
			return null
	mesh.material_override = material
	return mesh
