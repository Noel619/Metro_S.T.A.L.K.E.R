class_name DustPuff
extends CPUParticles3D
## Una nube de polvo pequeña que se levanta y se va sola (F2-13): al barrer, al
## soltar algo en el suelo, al abrir una caja vieja. Sin sonido: lo táctil es
## lo que se ve.

const SMOKE: String = "res://assets/textures/humo.png"

static var _material: StandardMaterial3D


## Levanta polvo en [param where] (en el mundo). [param amount], de 0 a 1.
static func burst(
	parent: Node, where: Vector3, amount: float = 1.0, color: Color = Color(0.62, 0.56, 0.48)
) -> DustPuff:
	if parent == null or not parent.is_inside_tree() or DisplayServer.get_name() == "headless":
		return null
	var puff: DustPuff = DustPuff.new()
	puff.amount = maxi(3, int(10 * clampf(amount, 0.0, 1.5)))
	puff.color = color
	parent.add_child(puff)
	puff.global_position = where
	puff.emitting = true
	puff.finished.connect(puff.queue_free)
	return puff


func _init() -> void:
	one_shot = true
	explosiveness = 0.85
	lifetime = 1.4
	local_coords = false
	direction = Vector3.UP
	spread = 70.0
	initial_velocity_min = 0.15
	initial_velocity_max = 0.5
	gravity = Vector3(0.0, 0.08, 0.0)
	damping_min = 0.6
	damping_max = 1.2
	scale_amount_min = 0.5
	scale_amount_max = 1.1
	var curve: Curve = Curve.new()
	curve.add_point(Vector2(0.0, 0.3))
	curve.add_point(Vector2(0.3, 1.0))
	curve.add_point(Vector2(1.0, 1.4))
	scale_amount_curve = curve
	var fade: Gradient = Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.55))
	fade.set_color(1, Color(1, 1, 1, 0.0))
	color_ramp = fade
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.22, 0.22)
	mesh = quad
	if _material == null:
		_material = StandardMaterial3D.new()
		_material.albedo_texture = load(SMOKE)
		_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_material.vertex_color_use_as_albedo = true
		_material.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		_material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	material_override = _material
