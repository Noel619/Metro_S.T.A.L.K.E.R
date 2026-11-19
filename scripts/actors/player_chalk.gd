class_name PlayerChalk
extends RefCounted
## Dibujar con la tiza (F3-08), en el equipo de quien la lleva: mirando una pared o el
## suelo a su alcance, se ve dónde quedaría la marca; mantener el botón izquierdo la
## dibuja (lleva [constant ChalkMarks.DRAW_SECONDS]) y se pide al anfitrión.

## Mira a algo donde se puede dibujar (entonces el botón dibuja y no lanza).
var aiming: bool = false

var _drawing: float = 0.0
var _hit: Dictionary = {}


func update(player: Player, delta: float, pressing: bool) -> void:
	var held: Carryable = player.held_item()
	var marks: ChalkMarks = ChalkMarks.find(player.get_tree())
	aiming = false
	if held == null or held.state.data.tool != ChalkMarks.TOOL or marks == null:
		_drawing = 0.0
		if marks != null:
			marks.preview(Vector3.ZERO, Vector3.UP, 0, 0.0, false)
		return
	var camera: Camera3D = player.get_viewport().get_camera_3d()
	var from: Vector3 = camera.global_position
	var to: Vector3 = from - camera.global_basis.z * Player.REACH
	var exclude: Array[RID] = [player.get_rid(), held.body_rid()]
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, to, 1 << 0, exclude
	)
	_hit = player.get_world_3d().direct_space_state.intersect_ray(query)
	aiming = not _hit.is_empty()
	var symbol: int = int(held.state.extra.get("simbolo", 0))
	if not aiming:
		_drawing = 0.0
		marks.preview(Vector3.ZERO, Vector3.UP, symbol, 0.0, false)
		return
	_drawing = _drawing + delta / ChalkMarks.DRAW_SECONDS if pressing else 0.0
	marks.preview(_hit["position"], _hit["normal"], symbol, clampf(_drawing, 0.0, 1.0), true)
	if _drawing >= 1.0:
		_drawing = 0.0
		marks.request_mark.rpc_id(Carryable.HOST_PEER, _hit["position"], _hit["normal"], symbol)
