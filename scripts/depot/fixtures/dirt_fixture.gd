class_name DirtFixture
extends Fixture
## Una mancha del suelo (F2-05): polvo y escombros que se barren con la escoba,
## o una mancha que se friega con la fregona. Cada pasada la deja más limpia y
## levanta un poco de polvo.

enum Kind { DUST, STAIN }

## Lo que quita cada pasada (unidades del gesto STROKE).
const PER_STROKE: float = 0.3
## La arenilla y los trocitos del polvo (lo que se ve que hay que barrer).
const GRIT: int = 26
const GRIT_COLORS: Array[Color] = [
	Color(0.42, 0.38, 0.32), Color(0.3, 0.27, 0.23), Color(0.55, 0.5, 0.42), Color(0.62, 0.58, 0.5)
]
const SHADER: String = "res://assets/shaders/mancha.gdshader"
const COLORS: Dictionary = {
	Kind.DUST: Color(0.33, 0.29, 0.23),
	Kind.STAIN: Color(0.17, 0.15, 0.12),
}

@export var kind: Kind = Kind.DUST
@export var radius: float = 0.5
@export var seed: float = 0.0

var _mesh: MeshInstance3D
var _grit: MultiMeshInstance3D
var _material: ShaderMaterial
var _area: Area3D
var _work: Workable
var _shown: float = 1.0


func _ready() -> void:
	_material = ShaderMaterial.new()
	_material.shader = load(SHADER)
	_material.set_shader_parameter("color", COLORS[kind])
	_material.set_shader_parameter("seed", seed)
	_material.set_shader_parameter("ring", kind == Kind.STAIN)
	var quad: PlaneMesh = PlaneMesh.new()
	quad.size = Vector2.ONE * radius * 2.0
	_mesh = MeshInstance3D.new()
	_mesh.name = "Mancha"
	_mesh.mesh = quad
	_mesh.material_override = _material
	_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mesh.position.y = 0.004
	_mesh.rotation.y = seed
	add_child(_mesh)
	if kind == Kind.DUST:
		_add_grit()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(radius * 1.6, 0.04, radius * 1.6)
	_area = add_reach_area(box, Vector3(0.0, 0.02, 0.0))
	var tool: StringName = &"escoba" if kind == Kind.DUST else &"fregona"
	_work = add_work(_area, [tool], Workable.Gesture.STROKE, "Limpiar")
	super._ready()
	_shown = dirt()
	_material.set_shader_parameter("amount", _shown)


## Lo que queda de suciedad (1 al principio, 0 limpio).
func dirt() -> float:
	return float(value("suciedad", 1.0))


func is_clean() -> bool:
	return dirt() <= 0.0


func _on_worked(_player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	if amount <= 0.0 or is_clean():
		return
	var left: float = dirt() - amount * PER_STROKE
	set_value("suciedad", 0.0 if left < 0.04 else left)


func _refresh() -> void:
	var now: float = dirt()
	if now < _shown - 0.01 and kind == Kind.DUST:
		DustPuff.burst(self, global_position + Vector3(0.0, 0.05, 0.0), (_shown - now) * 3.0)
	_area.collision_layer = 0 if now <= 0.0 else REACH_LAYER
	_work.enabled = now > 0.0


func _process(delta: float) -> void:
	var now: float = dirt()
	if not is_equal_approx(_shown, now):
		_shown = move_toward(_shown, now, delta * 1.5)
		_material.set_shader_parameter("amount", _shown)
		_mesh.visible = _shown > 0.001
		_show_grit()


## Arenilla, piedrecitas y trocitos de papel repartidos por la mancha: se van
## al barrer, de fuera hacia dentro.
func _add_grit() -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = int(seed * 1000.0) + 17
	var multimesh: MultiMesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	var piece: BoxMesh = BoxMesh.new()
	piece.size = Vector3(1.0, 0.4, 1.0)
	multimesh.mesh = piece
	multimesh.instance_count = GRIT
	var placed: Array[Array] = []
	for index: int in GRIT:
		var angle: float = rng.randf() * TAU
		var reach: float = sqrt(rng.randf()) * radius * 0.85
		placed.append(
			[reach, angle, rng.randf_range(0.012, 0.045), rng.randi() % GRIT_COLORS.size()]
		)
	# Los de fuera primero: son los que se van antes.
	placed.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	for index: int in GRIT:
		var entry: Array = placed[index]
		var size: float = entry[2]
		var where: Vector3 = Vector3(
			cos(entry[1]) * entry[0], 0.004 + size * 0.2, sin(entry[1]) * entry[0]
		)
		var turn: Basis = Basis.from_euler(
			Vector3(rng.randf_range(-0.3, 0.3), rng.randf() * TAU, 0.0)
		)
		var shape: Vector3 = Vector3(size, size, size * rng.randf_range(0.5, 1.4))
		multimesh.set_instance_transform(index, Transform3D(turn.scaled(shape), where))
		multimesh.set_instance_color(index, GRIT_COLORS[entry[3]])
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	material.roughness = 1.0
	_grit = MultiMeshInstance3D.new()
	_grit.name = "Arenilla"
	_grit.multimesh = multimesh
	_grit.material_override = material
	_grit.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_grit)
	_show_grit()


func _show_grit() -> void:
	if _grit != null:
		_grit.multimesh.visible_instance_count = ceili(GRIT * clampf(_shown, 0.0, 1.0))
