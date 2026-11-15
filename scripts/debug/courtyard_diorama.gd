@tool
extends Node3D
## Diorama B de la Fase 1: un patio de Los Bloques, años después de la guerra.
##
## Tres momentos del día ("dia", "anochecer", "noche") o una hora concreta, con el
## cielo, la luz y la niebla de scripts/surface/atmosphere.gd, y el clima
## (despejado o ventisca). Los objetos se colocan desde código para ajustar la
## composición rápido. La nieve, la ceniza y el humo son partículas: no pasan por
## el post-proceso. Las huellas son calcomanías sobre la nieve vieja.

const MODELS_DIR: String = "res://assets/models/"
const SMOKE_TEXTURE: String = "res://assets/textures/humo.png"
const BOOT_TEXTURE: String = "res://assets/textures/huella_bota.png"
const PAW_TEXTURE: String = "res://assets/textures/huella_perro.png"

@export_enum("dia", "anochecer", "noche") var mood: String = "dia"
## Hora del día (0 a 24). Si es negativa, se usa [member mood].
@export_range(-1.0, 24.0) var hour: float = -1.0
@export_enum("despejado", "ventisca") var weather: String = "despejado"
@export_range(0.0, 1.0) var fear: float = 0.0
## Enciende una linterna en cada cámara (para ver la noche como la verá el jugador).
@export var flashlight: bool = false

var _props: Node3D
var _weather_node: Node3D


func _ready() -> void:
	_build()
	_apply_atmosphere()
	if not Engine.is_editor_hint():
		StyleDirector.fear = fear
		for camera: Node in get_tree().get_nodes_in_group(&"capture_camera"):
			var target: Node3D = camera.get_node_or_null("Mira")
			if target != null:
				(camera as Camera3D).look_at(target.global_position)
			if flashlight:
				Flashlight.attach(camera as Camera3D)


## Cambia la hora del día (la usa el panel de depuración).
func set_hour(value: float) -> void:
	hour = value
	_apply_atmosphere()


## Cambia el clima: "despejado" o "ventisca".
func set_weather(value: String) -> void:
	weather = value
	_apply_atmosphere()
	_build_weather()


func _apply_atmosphere() -> void:
	if hour >= 0.0:
		Atmosphere.apply_hour($Entorno.environment, $Sol, hour, weather)
	else:
		Atmosphere.apply($Entorno.environment, $Sol, mood, weather)


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
	_place("quiosco", Vector3(-7.4, 0.0, 2.6), 62.0)
	_smoke(Vector3(-40.0, 10.0, -95.0), 1.0)
	_smoke(Vector3(55.0, 8.0, -120.0), 1.4)
	_smoke(Vector3(95.0, 40.0, -190.0), 2.2)
	# Huellas: alguien cruzó el patio hasta el quiosco… y la jauría pasó después.
	_boot_trail(Vector3(6.5, 0.0, 4.5), Vector3(-4.8, 0.0, -2.6), 7)
	_paw_trail(Vector3(8.0, 0.0, -1.0), Vector3(-1.0, 0.0, 4.8), 3)
	_build_weather()


## Nieve y ceniza cayendo; con ventisca, más nieve, más rápida y de lado.
func _build_weather() -> void:
	if is_instance_valid(_weather_node):
		_weather_node.free()
	_weather_node = Node3D.new()
	_weather_node.name = "Clima"
	_props.add_child(_weather_node)
	if weather == "ventisca":
		_falling(Color(0.8, 0.8, 0.78), 0.065, 6000, Vector3(1.0, -0.35, 0.25), 7.0)
		_streaks(1400)
	else:
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
func _falling(
	color: Color,
	flake_size: float,
	amount: int,
	direction: Vector3 = Vector3(0.2, -1.0, 0.1),
	speed: float = 1.0
) -> void:
	var process: ParticleProcessMaterial = ParticleProcessMaterial.new()
	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents = Vector3(18.0, 0.5, 14.0)
	process.direction = direction
	process.spread = 12.0
	process.initial_velocity_min = 0.6 * speed
	process.initial_velocity_max = 1.2 * speed
	process.gravity = Vector3(0.0, -0.4, 0.0)
	process.turbulence_enabled = true
	process.turbulence_noise_strength = 0.3
	# Copos con luz propia de la escena: de noche solo se ven dentro de la linterna.
	var flake: StandardMaterial3D = StandardMaterial3D.new()
	flake.albedo_texture = load(SMOKE_TEXTURE)
	flake.albedo_color = color
	flake.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	flake.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	flake.roughness = 1.0
	flake.metallic_specular = 0.0
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(flake_size, flake_size)
	quad.material = flake
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.amount = amount
	particles.lifetime = 14.0
	particles.preprocess = 14.0
	particles.process_material = process
	particles.draw_pass_1 = quad
	particles.position = Vector3(-6.0 if speed > 1.0 else 0.0, 13.0, 0.0)
	particles.visibility_aabb = AABB(Vector3(-30, -16, -16), Vector3(60, 18, 32))
	_weather_node.add_child(particles)


## Ráfagas de la ventisca: trazos alargados en la dirección del viento.
func _streaks(amount: int) -> void:
	var process: ParticleProcessMaterial = ParticleProcessMaterial.new()
	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents = Vector3(20.0, 6.0, 14.0)
	process.direction = Vector3(1.0, -0.2, 0.25)
	process.spread = 4.0
	process.initial_velocity_min = 9.0
	process.initial_velocity_max = 14.0
	process.gravity = Vector3.ZERO
	# Trazos casi horizontales en pantalla, algo caídos hacia donde sopla el viento.
	process.angle_min = -16.0
	process.angle_max = -6.0
	var streak: StandardMaterial3D = StandardMaterial3D.new()
	streak.albedo_color = Color(0.82, 0.82, 0.8, 0.5)
	streak.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	streak.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	streak.roughness = 1.0
	streak.metallic_specular = 0.0
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(0.9, 0.014)
	quad.material = streak
	var particles: GPUParticles3D = GPUParticles3D.new()
	particles.amount = amount
	particles.lifetime = 3.0
	particles.preprocess = 3.0
	particles.process_material = process
	particles.draw_pass_1 = quad
	particles.position = Vector3(-14.0, 6.0, 2.0)
	particles.visibility_aabb = AABB(Vector3(-40, -20, -20), Vector3(80, 30, 40))
	_weather_node.add_child(particles)


## Fila de huellas de bota entre dos puntos, alternando pie izquierdo y derecho.
func _boot_trail(from: Vector3, to: Vector3, seed_value: int) -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = seed_value
	var direction: Vector3 = (to - from).normalized()
	var side: Vector3 = direction.cross(Vector3.UP)
	var yaw: float = atan2(direction.x, direction.z)
	var steps: int = int(from.distance_to(to) / 0.42)
	for i: int in steps:
		var left: float = 1.0 if i % 2 == 0 else -1.0
		var position: Vector3 = from + direction * (i * 0.42) + side * (0.11 * left)
		var age: float = rng.randf_range(0.8, 1.0)
		_print(BOOT_TEXTURE, position, yaw + rng.randf_range(-0.12, 0.12), Vector2(0.12, 0.3), age)


## Rastro de perro: cuatro patas por paso, con el andar torcido de la jauría.
func _paw_trail(from: Vector3, to: Vector3, seed_value: int) -> void:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = seed_value
	var direction: Vector3 = (to - from).normalized()
	var side: Vector3 = direction.cross(Vector3.UP)
	var yaw: float = atan2(direction.x, direction.z)
	var steps: int = int(from.distance_to(to) / 0.55)
	for i: int in steps:
		var base: Vector3 = from + direction * (i * 0.55) + side * sin(i * 0.7) * 0.25
		for paw: Vector2 in [Vector2(-0.09, 0.0), Vector2(0.09, 0.18)]:
			var position: Vector3 = base + side * paw.x + direction * paw.y
			var size: Vector2 = Vector2(0.11, 0.11)
			_print(PAW_TEXTURE, position, yaw + rng.randf_range(-0.3, 0.3), size, 0.95)


## Una huella: calcomanía que se proyecta sobre la nieve (y sobre lo que haya debajo).
func _print(texture_path: String, position: Vector3, yaw: float, size: Vector2, age: float) -> void:
	var decal: Decal = Decal.new()
	decal.texture_albedo = load(texture_path)
	decal.size = Vector3(size.x, 1.6, size.y)
	decal.position = position + Vector3(0.0, 0.4, 0.0)
	decal.rotation = Vector3(0.0, yaw, 0.0)
	decal.modulate = Color(1.0, 1.0, 1.0, age)
	decal.albedo_mix = 1.0
	decal.upper_fade = 0.2
	decal.lower_fade = 0.2
	decal.cull_mask = 1
	_props.add_child(decal)
