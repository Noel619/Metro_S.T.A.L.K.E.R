class_name Atmosphere
extends RefCounted
## Ambiente de la superficie para cada hora del día: cielo, luz, niebla y estilo.
##
## Tres momentos de referencia (día, anochecer, noche) y una interpolación por
## horas entre ellos (el amanecer reutiliza el anochecer con el sol al este), que
## usará el reloj del mundo (Fase 4). El clima se aplica encima: con ventisca, la
## niebla se cierra. Los colores van en sRGB. Reglas: el cielo nunca es negro del
## todo, pero la noche es muy oscura: sin linterna prácticamente no se ve nada.

const SKY_SHADER: String = "res://assets/shaders/cielo.gdshader"
const CLOUD_NOISE: String = "res://assets/textures/nubes.png"
const HATCHING: String = "res://assets/textures/tramado.png"

const MOODS: Dictionary = {
	"dia":
	{
		"zenith": Color("#6e7273"),
		"horizon": Color("#9a968c"),
		"ground": Color("#4b4843"),
		"cloud_light": Color("#aeaba2"),
		"cloud_dark": Color("#6a6967"),
		"glow": Color("#f0dcb6"),
		"glow_strength": 0.35,
		"glow_size": 5.0,
		"coverage": 0.74,
		"ambient": Color("#706f6c"),
		"ambient_energy": 0.62,
		"fog": Color("#85827a"),
		"fog_density": 0.011,
		"sun": Color("#f2e6cc"),
		"sun_energy": 0.85,
		"sun_rotation": Vector3(-32.0, -40.0, 0.0),
		"style": &"superficie",
	},
	"anochecer":
	{
		"zenith": Color("#2e3040"),
		"horizon": Color("#a8775a"),
		"ground": Color("#2b2725"),
		"cloud_light": Color("#b9876a"),
		"cloud_dark": Color("#3e3541"),
		"glow": Color("#f29a66"),
		"glow_strength": 1.2,
		"glow_size": 4.0,
		"coverage": 0.62,
		"ambient": Color("#5a5262"),
		"ambient_energy": 0.6,
		"fog": Color("#5e4d45"),
		"fog_density": 0.012,
		"sun": Color("#ffa06a"),
		"sun_energy": 0.8,
		"sun_rotation": Vector3(-7.0, -24.0, 0.0),
		"style": &"superficie",
	},
	"noche":
	{
		"zenith": Color("#0a0d14"),
		"horizon": Color("#161b25"),
		"ground": Color("#07080b"),
		"cloud_light": Color("#2a3142"),
		"cloud_dark": Color("#0e1118"),
		"glow": Color("#8fa0c8"),
		"glow_strength": 0.35,
		"glow_size": 14.0,
		"coverage": 0.6,
		"ambient": Color("#1c2333"),
		"ambient_energy": 0.22,
		"fog": Color("#0b0d12"),
		"fog_density": 0.02,
		"sun": Color("#7d8db5"),
		"sun_energy": 0.08,
		"sun_rotation": Vector3(-35.0, 35.0, 0.0),
		"style": &"superficie_noche",
	},
}

## Horas de referencia: entre dos seguidas se interpola.
const HOURS: Array = [
	[0.0, "noche"],
	[5.0, "noche"],
	[6.5, "amanecer"],
	[8.0, "dia"],
	[16.5, "dia"],
	[18.0, "anochecer"],
	[19.5, "noche"],
	[24.0, "noche"],
]
## Con ventisca: la niebla se cierra y se vuelve gris (nunca blanca).
const BLIZZARD: Dictionary = {
	"fog_density": 0.055,
	"fog": Color("#7d7c78"),
	"fog_night": Color("#16181d"),
	"ambient_energy": 0.85,
	"sun_energy": 0.55,
}


## Aplica un momento del día al entorno y a la luz principal.
static func apply(
	environment: Environment, sun: DirectionalLight3D, mood: String, weather: String = "despejado"
) -> void:
	apply_values(environment, sun, _with_weather(values_for(mood), weather))


## Aplica la hora del día (0 a 24), interpolando entre los momentos de referencia.
static func apply_hour(
	environment: Environment, sun: DirectionalLight3D, hour: float, weather: String = "despejado"
) -> void:
	apply_values(environment, sun, _with_weather(values_at(hour), weather))


## Valores de un momento de referencia ("amanecer" es el anochecer con el sol al este).
static func values_for(mood: String) -> Dictionary:
	if mood == "amanecer":
		var dawn: Dictionary = MOODS["anochecer"].duplicate()
		dawn["sun_rotation"] = Vector3(-7.0, 150.0, 0.0)
		return dawn
	return MOODS.get(mood, MOODS["dia"])


## Valores interpolados para una hora del día.
static func values_at(hour: float) -> Dictionary:
	var h: float = fposmod(hour, 24.0)
	for i: int in HOURS.size() - 1:
		var from_hour: float = HOURS[i][0]
		var to_hour: float = HOURS[i + 1][0]
		if h >= from_hour and h <= to_hour:
			var t: float = smoothstep(from_hour, to_hour, h)
			return _blend(values_for(HOURS[i][1]), values_for(HOURS[i + 1][1]), t)
	return values_for("noche")


static func _blend(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var result: Dictionary = {}
	for key: String in a:
		if a[key] is StringName or a[key] is String:
			result[key] = a[key] if t < 0.5 else b[key]
		else:
			result[key] = lerp(a[key], b[key], t)
	return result


static func _with_weather(values: Dictionary, weather: String) -> Dictionary:
	if weather != "ventisca":
		return values
	var result: Dictionary = values.duplicate()
	var night: float = 1.0 - clampf(values["sun_energy"] / 0.85, 0.0, 1.0)
	result["fog_density"] = BLIZZARD["fog_density"]
	result["fog"] = BLIZZARD["fog"].lerp(BLIZZARD["fog_night"], night)
	result["ambient_energy"] = values["ambient_energy"] * BLIZZARD["ambient_energy"]
	result["sun_energy"] = values["sun_energy"] * BLIZZARD["sun_energy"]
	result["coverage"] = 1.0
	return result


## Aplica un conjunto de valores (de [method values_for] o [method values_at]).
static func apply_values(
	environment: Environment, sun: DirectionalLight3D, values: Dictionary
) -> void:
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = load(SKY_SHADER)
	material.set_shader_parameter("cloud_noise", load(CLOUD_NOISE))
	material.set_shader_parameter("hatching", load(HATCHING))
	for key: String in ["zenith", "horizon", "ground", "cloud_light", "cloud_dark", "glow"]:
		var parameter: String = (
			key + "_color" if key != "cloud_light" and key != "cloud_dark" else key
		)
		material.set_shader_parameter(parameter, values[key])
	material.set_shader_parameter("glow_strength", values["glow_strength"])
	material.set_shader_parameter("glow_size", values["glow_size"])
	material.set_shader_parameter("coverage", values["coverage"])
	var sky: Sky = Sky.new()
	sky.sky_material = material
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = values["ambient"]
	environment.ambient_light_energy = values["ambient_energy"]
	environment.fog_enabled = true
	environment.fog_light_color = values["fog"]
	environment.fog_density = values["fog_density"]
	environment.fog_sky_affect = 0.0
	environment.fog_height = 1.5
	environment.fog_height_density = 0.04
	sun.light_color = values["sun"]
	sun.light_energy = values["sun_energy"]
	sun.rotation_degrees = values["sun_rotation"]
	RenderingServer.global_shader_parameter_set("tinta_horizonte", values["horizon"])
	# La ciudad lejana y los hitos hacen su propia niebla (ver tinta_silueta y tinta_hito).
	RenderingServer.global_shader_parameter_set("tinta_niebla", values["fog"])
	RenderingServer.global_shader_parameter_set("tinta_niebla_densidad", values["fog_density"])
	if StyleDirector.zone != values["style"]:
		StyleDirector.set_zone(values["style"], not environment.has_meta(&"aplicado"))
	environment.set_meta(&"aplicado", true)
