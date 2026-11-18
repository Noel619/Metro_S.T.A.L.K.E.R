class_name DirtFixture
extends Fixture
## Una mancha del suelo (F2-05): polvo y escombros que se barren con la escoba,
## o una mancha que se friega con la fregona. Cada pasada la deja más limpia y
## levanta un poco de polvo.

enum Kind { DUST, STAIN }

## Lo que quita cada pasada (unidades del gesto STROKE).
const PER_STROKE: float = 0.3
const SHADER: String = "res://assets/shaders/mancha.gdshader"
const COLORS: Dictionary = {
	Kind.DUST: Color(0.5, 0.45, 0.37),
	Kind.STAIN: Color(0.27, 0.24, 0.2),
}

@export var kind: Kind = Kind.DUST
@export var radius: float = 0.5
@export var seed: float = 0.0

var _mesh: MeshInstance3D
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
