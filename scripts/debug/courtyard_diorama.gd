@tool
extends Node3D
## Diorama B de la Fase 1: un patio de Los Bloques bajo la nieve.
##
## Los objetos se colocan desde código (como en el diorama del depósito) para
## ajustar la composición rápido. La nieve que cae son partículas: no pasan por
## el post-proceso, así que se ven limpias delante del dibujo.

const MODELS_DIR: String = "res://assets/models/"

## "dia": nublado. "anochecer": más oscuro, con niebla y miedo.
@export_enum("dia", "anochecer") var mood: String = "dia"
@export_range(0.0, 1.0) var fear: float = 0.0

var _props: Node3D


func _ready() -> void:
	_build()
	if mood == "anochecer":
		_dusk()
	if not Engine.is_editor_hint():
		StyleDirector.set_zone(StyleDirector.ZONE_SURFACE, true)
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
	_place("farola", Vector3(-3.6, 0.0, 0.5), 25.0)
	_place("farola", Vector3(9.0, 0.0, -5.5), 200.0)
	_place("banco_parque", Vector3(2.6, 0.0, -2.2), -12.0)
	_place("arbol_desnudo", Vector3(-6.5, 0.0, -4.5), 0.0)
	_place("arbol_desnudo_b", Vector3(5.8, 0.0, 2.8), 40.0)
	_place("arbol_desnudo_b", Vector3(-11.0, 0.0, 4.0), 120.0)
	_place("coche", Vector3(7.2, -0.12, -3.8), 74.0)
	_place("columpio", Vector3(-1.8, 0.0, -5.2), 8.0)
	_place("contenedor", Vector3(10.5, 0.0, -8.6), 4.0)
	_place("caja_carton_grande", Vector3(9.3, 0.0, -8.0), 30.0)
	_snowfall()


func _dusk() -> void:
	var environment: Environment = $Entorno.environment.duplicate()
	environment.background_color = Color(0.26, 0.28, 0.34)
	environment.ambient_light_color = Color(0.36, 0.42, 0.56)
	environment.ambient_light_energy = 0.5
	environment.fog_light_color = Color(0.28, 0.31, 0.38)
	environment.fog_density = 0.038
	$Entorno.environment = environment
	var sun: DirectionalLight3D = $Sol
	sun.light_color = Color(0.98, 0.66, 0.5)
	sun.light_energy = 0.55
	sun.rotation_degrees = Vector3(-9.0, -62.0, 0.0)


func _place(model: String, position: Vector3, yaw: float = 0.0) -> Node3D:
	var node: Node3D = load(MODELS_DIR + model + ".glb").instantiate()
	node.position = position
	node.rotation_degrees = Vector3(0.0, yaw, 0.0)
	_props.add_child(node)
	return node


func _snowfall() -> void:
	var material: ParticleProcessMaterial = ParticleProcessMaterial.new()
	material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	material.emission_box_extents = Vector3(18.0, 0.5, 14.0)
	material.direction = Vector3(0.2, -1.0, 0.1)
	material.spread = 12.0
	material.initial_velocity_min = 0.6
	material.initial_velocity_max = 1.2
	material.gravity = Vector3(0.0, -0.4, 0.0)
	material.turbulence_enabled = true
	material.turbulence_noise_strength = 0.3
	var flake: StandardMaterial3D = StandardMaterial3D.new()
	flake.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	flake.albedo_color = Color(0.93, 0.94, 0.96)
	flake.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.045, 0.045)
	quad.material = flake
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.amount = 1800
	particles.lifetime = 14.0
	particles.preprocess = 14.0
	particles.process_material = material
	particles.draw_pass_1 = quad
	particles.position = Vector3(0.0, 13.0, 0.0)
	particles.visibility_aabb = AABB(Vector3(-20, -16, -16), Vector3(40, 18, 32))
	_props.add_child(particles)
