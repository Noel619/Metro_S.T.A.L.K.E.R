class_name RopeAnchor
extends Fixture
## Donde se puede atar una cuerda (F3-06, docs/SUPERFICIE.md 4.3): una barandilla, un
## tubo, el antepecho de una azotea. Con la cuerda en la mano, mantener el botón
## izquierdo sobre el anclaje la ata: la cuerda se gasta y queda colgando hasta el
## suelo, y por ella se baja y se sube ([Climbable]). Se queda puesta (se guarda con el
## mundo, "atada"): es un atajo para la próxima vez.
##
## Su marco: el origen en el borde, donde se ata, a la altura del rellano; +z hacia
## fuera (hacia el vacío, por donde cuelga) y +y arriba.

const ROPE_ITEM: StringName = &"cuerda"
## Lo que se aparta la cuerda del borde, lo que cuelga como mucho y lo que tarda en
## atarse (unidades del gesto HOLD: segundos).
const OFFSET: float = 0.12
const MAX_DROP: float = 30.0
const TIE_WORK: float = 1.5
const ROPE_COLOR: Color = Color("#8a7a5c")
const ROPE_RADIUS: float = 0.014

## Lo que se aparta la cuerda del borde (para librar una cornisa) y lo que se avanza
## tras el borde al subir (para quedar en la azotea, detrás de un antepecho).
var offset: float = OFFSET
var landing_depth: float = OFFSET + 1.0

var _area: Area3D
var _rope: MeshInstance3D
var _climb: Climbable


## Monta el anclaje [param id] en [param edge] (en el marco del padre).
func setup(id: String, edge: Transform3D) -> void:
	fixture_id = id
	name = id.validate_node_name()
	transform = edge


func _ready() -> void:
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = Vector3(0.6, 0.5, 0.5)
	_area = add_reach_area(shape, Vector3(0.0, 0.25, 0.0), "Anclaje")
	add_work(_area, [ROPE_ITEM], Workable.Gesture.HOLD, "Atar")
	super._ready()


## Hay una cuerda atada.
func is_tied() -> bool:
	return bool(value("atada", false))


## La escalera de cuerda (o null, si no está atada o aún no se ha medido).
func climbable() -> Climbable:
	return _climb


func _on_worked(player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	if is_tied() or amount <= 0.0 or player == null:
		return
	var held: Carryable = player.held_item()
	if held == null or held.state.data.id != ROPE_ITEM:
		return
	var progress: float = float(value("nudo", 0.0)) + amount / TIE_WORK
	if progress < 1.0:
		set_value("nudo", progress)
		return
	consume_held(player)
	set_values({"nudo": 1.0, "atada": true})


func _refresh() -> void:
	for workable: Workable in workables:
		workable.enabled = not is_tied()
	if is_tied() and _rope == null and is_inside_tree():
		_hang.call_deferred()


## Cuelga la cuerda: mide hasta el suelo y pone la cuerda que se ve y la que se trepa.
func _hang() -> void:
	if _rope != null or not is_inside_tree():
		return
	var top: Vector3 = global_transform * Vector3(0.0, 0.0, offset)
	var space: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		top, top + Vector3.DOWN * MAX_DROP, Player.MASK_PLAYERS
	)
	var hit: Dictionary = space.intersect_ray(query)
	var drop: float = top.y - (hit["position"] as Vector3).y if not hit.is_empty() else MAX_DROP
	_rope = MeshInstance3D.new()
	_rope.name = "Cuerda"
	var cylinder: CylinderMesh = CylinderMesh.new()
	cylinder.top_radius = ROPE_RADIUS
	cylinder.bottom_radius = ROPE_RADIUS
	cylinder.height = drop + 0.3
	cylinder.radial_segments = 6
	_rope.mesh = cylinder
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = ROPE_COLOR
	material.roughness = 1.0
	_rope.material_override = material
	_rope.position = Vector3(0.0, -drop * 0.5 + 0.15, offset)
	add_child(_rope)
	# Quien trepa queda por fuera, mirando al muro (hacia -z del anclaje); el pie de la
	# escalera, en el suelo.
	var foot: Transform3D = Transform3D(Basis(), Vector3(0.0, -drop, offset))
	_climb = Climbable.make(foot, Vector3(0.4, drop, 0.8), Climbable.ROPE)
	_climb.landing_depth = landing_depth
	add_child(_climb)
