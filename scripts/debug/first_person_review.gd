extends Node3D
## Hoja de revisión de la vista en primera persona (Fase 2).
##
## Carga el depósito jugable, hace que el jugador coja un objeto y lo deja
## mirando hacia la sala con él entre las manos. La cámara es la del propio
## jugador. Sirve para ver cómo se colocan las manos según lo que se lleva.

const LEVEL: String = "res://scenes/depot/deposito.tscn"
const STAND_DISTANCE: float = 0.95

@export_enum("chico", "chica") var variant: String = "chico"
## Ficha del objeto que coge (data/items/). Vacío: manos libres.
@export var item_id: StringName = &"caja_carton_pequena"
## Lo acerca a los ojos, como al inspeccionarlo.
@export var inspecting: bool = false


func _ready() -> void:
	GameState.protagonist = variant
	var level: Node = load(LEVEL).instantiate()
	add_child(level)
	(level.find_child("Ayuda", false, false) as CanvasLayer).visible = false
	var player: Player = level.call("local_player")
	player.find_child("Camara", true, false).add_to_group(&"capture_camera")
	await _frames(40)
	var body: Node3D = _find_item(level)
	if body == null:
		return
	# Se pone delante, del lado de la sala, y lo mira.
	var target: Vector3 = body.global_position + GripModifier.bounds_of(body).get_center()
	var away: Vector3 = Vector3(0.2 - target.x, 0.0, 0.2 - target.z).normalized()
	player.position = Vector3(target.x, 0.03, target.z) + away * STAND_DISTANCE
	player.rotation.y = atan2(away.x, away.z)
	var eyes: Vector3 = player.position + Vector3.UP * Player.EYE_HEIGHTS[variant]
	player.head_pitch = atan2(target.y - eyes.y, STAND_DISTANCE)
	await _frames(6)
	player.interact()
	await _frames(40)
	# Media vuelta, hacia la sala.
	player.rotation.y += PI * 0.8
	player.head_pitch = -0.28
	if inspecting:
		Input.action_press(&"use_secondary")


func _find_item(level: Node) -> Node3D:
	var best: Node3D = null
	for item: Carryable in (level.get("items") as WorldItems).items():
		var body: Node3D = item.get_parent()
		if item.state.data.id != item_id:
			continue
		if best == null or body.global_position.y > best.global_position.y:
			best = body
	return best


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame
