class_name TransformSync
extends MultiplayerSynchronizer
## Replica la posición y la rotación del nodo padre desde el anfitrión.
##
## Se añade como hijo de cualquier [Node3D] del mundo que se mueva. El nodo
## debe existir en la misma ruta en todos los jugadores (escena compartida o
## creado por un [MultiplayerSpawner]).

const SYNCED_PROPERTIES: PackedStringArray = [".:position", ".:rotation"]


func _init() -> void:
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	for property: String in SYNCED_PROPERTIES:
		var path: NodePath = NodePath(property)
		config.add_property(path)
		config.property_set_spawn(path, true)
		config.property_set_replication_mode(path, SceneReplicationConfig.REPLICATION_MODE_ALWAYS)
	replication_config = config
	root_path = NodePath("..")
