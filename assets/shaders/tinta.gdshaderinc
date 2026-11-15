// Cuerpo común del sombreado por bandas de Tumansk (ver tinta.gdshader).
// Lo incluyen tinta.gdshader (opaco) y tinta_recorte.gdshader (con recorte
// por alfa, para papeles, carteles y hojas). Variantes, con #define antes del
// #include:
// - TINTA_SUELO: el suelo de la ciudad (tinta_suelo.gdshader). El color y la
//   nieve salen de data/ciudad/suelo.png, proyectado desde arriba.
// - TINTA_FACHADA: fachadas de la maqueta (tinta_fachada.gdshader). La textura
//   (las ventanas) solo se aplica donde el alfa del color de vértice lo pide.
// - TINTA_HITO: los hitos de la ciudad (tinta_hito.gdshader). La niebla nunca
//   los borra del todo: el jugador se orienta con ellos.
// - TINTA_TRANSITO: los pavimentos de la ciudad (tinta_transito.gdshader). La nieve
//   va a parches como en el suelo; cuánta cubre la dice el alfa del color de vértice.

global uniform int tinta_rampa;
#ifdef TINTA_HITO
// Niebla de la superficie (la fija Atmosphere; el color llega en sRGB).
global uniform vec4 tinta_niebla;
global uniform float tinta_niebla_densidad;
// Cuánto puede tapar la niebla a un hito, como mucho.
uniform float hito_niebla_max : hint_range(0.0, 1.0) = 0.78;
#endif
#ifdef TINTA_SUELO
// RGB: color del suelo bajo la nieve; A: cuánta nieve lo cubre.
uniform sampler2D ground_map : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
// Metros que cubre ground_map (el mapa jugable, con el origen en la esquina suroeste).
uniform vec2 ground_size = vec2(1600.0, 1200.0);
#endif

uniform vec4 albedo_color : source_color = vec4(1.0);
uniform sampler2D albedo_texture : source_color, hint_default_white, filter_linear_mipmap, repeat_enable;
uniform bool use_vertex_color = true;
uniform sampler2D ramps : hint_default_white, filter_linear, repeat_disable;
// Fila de la rampa: -1 usa la de la zona (tinta_rampa); 3 piel; 4 metal.
uniform int ramp_row : hint_range(-1, 4) = -1;
uniform float snow_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 snow_color : source_color = vec4(0.86, 0.85, 0.81, 1.0);
uniform float rim_strength : hint_range(0.0, 1.0) = 0.0;
uniform vec4 emission_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float emission_energy : hint_range(0.0, 16.0) = 0.0;

const float RAMP_ROWS = 5.0;

varying vec3 world_normal;
varying vec3 world_position;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float value_noise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x),
			mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x),
			mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y),
		f.z);
}

void vertex() {
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void fragment() {
#ifdef TINTA_FACHADA
	vec3 base = albedo_color.rgb * mix(vec3(1.0), texture(albedo_texture, UV).rgb, COLOR.a);
#else
	vec3 base = albedo_color.rgb * texture(albedo_texture, UV).rgb;
#endif
	if (use_vertex_color) {
		base *= COLOR.rgb;
	}
#ifdef TINTA_TRANSITO
	// Manchas grandes de suciedad y hollín: el pavimento nunca es del todo uniforme.
	base *= mix(0.88, 1.05, value_noise(world_position * 0.13));
#endif
#ifdef TINTA_SUELO
	// El plano tiene el norte en -Z; la primera fila de ground_map es el borde norte.
	vec2 plan = vec2(world_position.x, -world_position.z);
	vec4 ground = texture(ground_map, vec2(plan.x / ground_size.x, 1.0 - plan.y / ground_size.y));
	base *= ground.rgb;
#endif
	if (snow_amount > 0.0) {
#if defined(TINTA_SUELO) || defined(TINTA_TRANSITO)
		// Nieve vieja a parches: cubre lo que pide el suelo y resbala de las cuestas.
		float n = value_noise(world_position * 0.31) * 0.55 + value_noise(world_position * 1.7) * 0.3
			+ value_noise(world_position * 7.0) * 0.15;
#ifdef TINTA_SUELO
		float amount = ground.a;
#else
		float amount = COLOR.a;
#endif
		float cover = amount * smoothstep(0.62, 0.9, normalize(world_normal).y) * snow_amount;
		float snow = smoothstep(n - 0.06, n + 0.06, cover);
#else
		float n = value_noise(world_position * 3.0) * 0.6 + value_noise(world_position * 11.0) * 0.4;
		float snow = smoothstep(0.55, 0.8, normalize(world_normal).y + (n - 0.5) * 0.35) * snow_amount;
#endif
		// Nieve vieja: ceniza, hollín y pisadas, nunca blanca del todo.
		float dirt = value_noise(world_position * 1.7) * 0.7 + value_noise(world_position * 23.0) * 0.3;
		float soot = smoothstep(0.7, 0.82, value_noise(world_position * 5.0 + 17.0));
		vec3 old_snow = snow_color.rgb * mix(0.84, 1.03, dirt) * (1.0 - soot * 0.18);
		base = mix(base, old_snow, snow);
	}
	ALBEDO = base;
#ifdef TINTA_RECORTE
	ALPHA = albedo_color.a * texture(albedo_texture, UV).a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
#endif
	ROUGHNESS = 1.0;
	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	EMISSION = emission_color.rgb * emission_energy + base * fresnel * rim_strength * 0.5;
#ifdef TINTA_HITO
	float fog_amount = 1.0 - exp(-tinta_niebla_densidad * length(VERTEX));
	FOG = vec4(srgb_to_linear(tinta_niebla.rgb), min(fog_amount, hito_niebla_max));
#endif
}

void light() {
	float row = float(ramp_row < 0 ? tinta_rampa : ramp_row);
	// Las bandas dependen solo del ángulo con la luz; la caída con la distancia y
	// las sombras proyectadas (ATTENUATION) se aplican después, suaves.
	float t = clamp(dot(NORMAL, LIGHT) * 0.5 + 0.5, 0.0, 1.0);
	// Las rampas se guardan a la mitad para admitir brillos por encima de 1.
	vec3 band = texture(ramps, vec2(t, (row + 0.5) / RAMP_ROWS)).rgb * 2.0;
	// LIGHT_COLOR ya viene multiplicado por PI.
	DIFFUSE_LIGHT += band * LIGHT_COLOR / PI * ATTENUATION;
}
