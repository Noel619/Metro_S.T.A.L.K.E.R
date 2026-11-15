class_name Atmosphere
extends RefCounted
## Ambiente de la superficie para cada hora del día: cielo, luz, niebla y estilo.
##
## De momento son tres momentos fijos (día, anochecer, noche). El sistema de
## hora y clima de la Fase 4 interpolará entre ellos. Los colores van en sRGB.
## Regla: el cielo nunca es negro.

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
		"horizon": Color("#b47a55"),
		"ground": Color("#2b2725"),
		"cloud_light": Color("#c58560"),
		"cloud_dark": Color("#3e3541"),
		"glow": Color("#ff9450"),
		"glow_strength": 1.4,
		"glow_size": 4.0,
		"coverage": 0.62,
		"ambient": Color("#5a5262"),
		"ambient_energy": 0.6,
		"fog": Color("#6a5348"),
		"fog_density": 0.012,
		"sun": Color("#ffa06a"),
		"sun_energy": 0.8,
		"sun_rotation": Vector3(-7.0, -24.0, 0.0),
		"style": &"superficie",
	},
	"noche":
	{
		"zenith": Color("#1a2133"),
		"horizon": Color("#3c4458"),
		"ground": Color("#15171d"),
		"cloud_light": Color("#68748f"),
		"cloud_dark": Color("#262c3d"),
		"glow": Color("#b9c9ef"),
		"glow_strength": 0.6,
		"glow_size": 12.0,
		"coverage": 0.55,
		"ambient": Color("#3f4a66"),
		"ambient_energy": 0.95,
		"fog": Color("#262c3a"),
		"fog_density": 0.014,
		"sun": Color("#9fb1dc"),
		"sun_energy": 0.65,
		"sun_rotation": Vector3(-35.0, 35.0, 0.0),
		"style": &"superficie_noche",
	},
}


## Aplica un momento del día al entorno y a la luz principal.
static func apply(environment: Environment, sun: DirectionalLight3D, mood: String) -> void:
	var values: Dictionary = MOODS.get(mood, MOODS["dia"])
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
	StyleDirector.set_zone(values["style"], true)
