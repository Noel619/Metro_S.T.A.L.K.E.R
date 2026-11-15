extends Node3D
## Hoja de revisión de la vista en primera persona (Fase 2).
##
## Carga el depósito jugable y deja al jugador en dos situaciones: con las
## manos vacías ante el banco y con una caja entre las manos. La cámara es la
## del propio jugador.

const LEVEL: String = "res://scenes/depot/deposito.tscn"

@export_enum("chico", "chica") var variant: String = "chico"
## Coge la caja de la balda antes de la captura.
@export var carrying: bool = true


func _ready() -> void:
	GameState.protagonist = variant
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	(level.find_child("Ayuda", false, false) as CanvasLayer).visible = false
	var player: Player = level.call("local_player")
	player.find_child("Camara", true, false).add_to_group(&"capture_camera")
	for _i in 40:
		await get_tree().physics_frame
	# Delante de la estantería, mirando a una caja pequeña de las baldas.
	var box: Node3D = null
	for item: Carryable in (level.get("items") as WorldItems).items():
		var body: Node3D = item.get_parent()
		if item.state.data.id == &"caja_carton_pequena" and body.global_position.y > 1.2:
			box = body
			break
	var target: Vector3 = box.global_position + Vector3.UP * 0.08
	player.position = Vector3(target.x + 0.95, 0.03, target.z)
	player.rotation.y = PI / 2.0
	var eyes: Vector3 = player.position + Vector3.UP * Player.EYE_HEIGHTS[variant]
	player.head_pitch = atan2(target.y - eyes.y, 0.95)
	if not carrying:
		return
	for _i in 6:
		await get_tree().physics_frame
	player.interact()
	for _i in 40:
		await get_tree().physics_frame
	player.rotation.y = 0.5
	player.head_pitch = -0.3
