@tool
extends Node3D
## Diorama B de la Fase 1: un patio de Los Bloques, años después de la guerra.
##
## Tres momentos del día ("dia", "anochecer", "noche"), con el cielo, la luz y la
## niebla de scripts/surface/atmosphere.gd. Los objetos se colocan desde código
## para ajustar la composición rápido. La nieve, la ceniza y el humo son
## partículas: no pasan por el post-proceso.

const MODELS_DIR: String = "res://assets/models/"
const SMOKE_TEXTURE: String = "res://assets/textures/humo.png"

@export_enum("dia", "anochecer", "noche") var mood: String = "dia"
@export_range(0.0, 1.0) var fear: float = 0.0

var _props: Node3D


func _ready() -> void:
	_build()
	Atmosphere.apply($Entorno.environment, $Sol, mood)
	if not Engine.is_editor_hint():
		StyleDirector.fear = fear
		for camera: Node in get_tree().get_nodes_in_group(&"capture_camera"):
			var target: Node3D = camera.get_node_or_null("Mira")
			if target != null:
				(camera as Camera3D).look_at(target.global_position)


func _build() -> void:
	if _props != null:
		_props.free()
	_props = Node3D.new()
	_props.name = "Objetos"
	add_child(_props)
	_place("suelo_patio", Vector3.ZERO)
	_place("bloque_paneles", Vector3(0.0, 0.0, -11.0))
	_place("bloque_paneles_b", Vector3(17.5, 0.0, 1.0), -90.0)
	_place("bloque_paneles_b", Vector3(-17.5, 0.0, -2.0), 90.0)
	_place("ruinas_horizonte", Vector3(0.0, -2.0, 0.0))
	var zone_zero: Node3D = _place("zona_cero", Vector3(95.0, -4.0, -190.0), -20.0)
	zone_zero.scale = Vector3.ONE * 1.35
	_place("farola", Vector3(-3.6, 0.0, 0.5), 25.0)
	_place("farola_torcida", Vector3(9.0, 0.0, -5.5), 200.0)
	_place("postes_cables", Vector3(-12.5, 0.0, 6.5), 80.0)
	_place("banco_parque", Vector3(2.6, 0.0, -2.2), -12.0)
	_place("arbol_desnudo", Vector3(-6.5, 0.0, -4.5))
	_place("arbol_desnudo_b", Vector3(5.8, 0.0, 2.8), 40.0)
	_place("arbol_desnudo_b", Vector3(-11.0, 0.0, 4.0), 120.0)
	_place("coche", Vector3(7.2, -0.12, -3.8), 74.0)
	_place("coche_quemado", Vector3(-9.5, -0.05, -6.5), -28.0)
	_place("columpio", Vector3(-1.8, 0.0, -5.2), 8.0)
	_place("contenedor", Vector3(10.5, 0.0, -8.6), 4.0)
	_place("escombros_grande", Vector3(4.5, 0.0, -7.8), 30.0)
	_place("escombros", Vector3(-13.5, 0.0, -1.0), 70.0)
	_place("escombros", Vector3(13.8, 0.0, 4.5), 150.0)
	_place("caja_carton_grande", Vector3(9.3, 0.0, -8.0), 30.0)
	_smoke(Vector3(-40.0, 10.0, -95.0), 1.0)
	_smoke(Vector3(55.0, 8.0, -120.0), 1.4)
	_smoke(Vector3(95.0, 40.0, -190.0), 2.2)
	_falling(Color(0.86, 0.85, 0.82), 0.045, 1600)
	_falling(Color(0.24, 0.23, 0.22), 0.03, 500)


func _place(model: String, position: Vector3, yaw: float = 0.0) -> Node3D:
	var node: Node3D = load(MODELS_DIR + model + ".glb").instantiate()
	node.position = position
	node.rotation_degrees = Vector3(0.0, yaw, 0.0)
	_props.add_child(node)
	return node


## Columna de humo lejana.
func _smoke(position: Vector3, size: float) -> void:
	var process: ParticleProcessMaterial = ParticleProcessMaterial.new()
	process.direction = Vector3(0.15, 1.0, 0.0)
	process.spread = 10.0
	process.initial_velocity_min = 2.0 * size
	process.initial_velocity_max = 3.0 * size
	process.gravity = Vector3(0.6, 0.15, 0.0)
	process.scale_min = 6.0 * size
	process.scale_max = 11.0 * size
	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	process.emission_sphere_radius = 2.0 * size
	var puff: StandardMaterial3D = StandardMaterial3D.new()
	puff.albedo_texture = load(SMOKE_TEXTURE)
	puff.albedo_color = Color(0.17, 0.16, 0.15, 0.85)
	puff.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	puff.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	puff.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	var quad: QuadMesh = QuadMesh.new()
	quad.material = puff
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.amount = 40
	particles.lifetime = 24.0
	particles.preprocess = 24.0
	particles.process_material = process
	particles.draw_pass_1 = quad
	particles.position = position
	particles.visibility_aabb = AABB(Vector3(-60, -10, -60), Vector3(120, 140, 120))
	_props.add_child(particles)


## Nieve o ceniza cayendo alrededor de la cámara.
func _falling(color: Color, flake_size: float, amount: int) -> void:
	var process: ParticleProcessMaterial = ParticleProcessMaterial.new()
	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents = Vector3(18.0, 0.5, 14.0)
	process.direction = Vector3(0.2, -1.0, 0.1)
	process.spread = 12.0
	process.initial_velocity_min = 0.6
	process.initial_velocity_max = 1.2
	process.gravity = Vector3(0.0, -0.4, 0.0)
	process.turbulence_enabled = true
	process.turbulence_noise_strength = 0.3
	var flake: StandardMaterial3D = StandardMaterial3D.new()
	flake.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	flake.albedo_color = color
	flake.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(flake_size, flake_size)
	quad.material = flake
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.amount = amount
	particles.lifetime = 14.0
	particles.preprocess = 14.0
	particles.process_material = process
	particles.draw_pass_1 = quad
	particles.position = Vector3(0.0, 13.0, 0.0)
	particles.visibility_aabb = AABB(Vector3(-20, -16, -16), Vector3(40, 18, 32))
	_props.add_child(particles)
