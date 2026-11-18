class_name Drip
extends Node3D
## La gotera de la tubería de la consigna (docs/DEPOSITO.md 1): una gota cada
## pocos segundos y el charco oscuro donde cae. Solo se ve; no tiene estado.

const SHADER: String = "res://assets/shaders/mancha.gdshader"
## Cada cuánto cae una gota (segundos) y desde qué altura.
const PERIOD: float = 2.6

@export var height: float = 2.3

var _drops: CPUParticles3D


func _ready() -> void:
	var puddle: MeshInstance3D = MeshInstance3D.new()
	puddle.name = "Charco"
	var plane: PlaneMesh = PlaneMesh.new()
	plane.size = Vector2(0.55, 0.45)
	puddle.mesh = plane
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = load(SHADER)
	material.set_shader_parameter("color", Color(0.24, 0.17, 0.12))
	material.set_shader_parameter("seed", 4.2)
	material.set_shader_parameter("ring", true)
	puddle.material_override = material
	puddle.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	puddle.position.y = 0.005
	add_child(puddle)
	if DisplayServer.get_name() == "headless":
		return
	_drops = CPUParticles3D.new()
	_drops.name = "Gotas"
	_drops.amount = 2
	_drops.lifetime = PERIOD
	_drops.explosiveness = 0.0
	_drops.local_coords = false
	_drops.direction = Vector3.DOWN
	_drops.spread = 0.0
	_drops.initial_velocity_min = 0.0
	_drops.initial_velocity_max = 0.0
	_drops.gravity = Vector3(0.0, -9.8, 0.0)
	var drop: SphereMesh = SphereMesh.new()
	drop.radius = 0.008
	drop.height = 0.026
	_drops.mesh = drop
	var water: StandardMaterial3D = StandardMaterial3D.new()
	water.albedo_color = Color(0.55, 0.6, 0.62, 0.8)
	water.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	water.roughness = 0.1
	_drops.material_override = water
	# Desde la tubería; la gota desaparece al llegar al suelo.
	_drops.position.y = height
	var fall: float = sqrt(2.0 * height / 9.8)
	_drops.lifetime = fall
	_drops.preprocess = 0.0
	_drops.one_shot = false
	_drops.speed_scale = fall / PERIOD * 2.0
	add_child(_drops)
