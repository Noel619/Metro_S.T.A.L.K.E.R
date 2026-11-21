// El agua abierta del río (CityRiver): negra y fría, con el cielo reflejado de refilón,
// rizos que corren con la corriente, aguanieve junto al hielo (el alfa del color de vértice:
// 1 en el borde) y hielo menudo que baja flotando. Opaca: la tinta la perfila como a todo
// lo demás, y la luz va por las mismas bandas que el resto del estilo (tinta.gdshaderinc).
shader_type spatial;
render_mode diffuse_lambert, cull_back;

global uniform int tinta_rampa;

uniform sampler2D ramps : hint_default_white, filter_linear, repeat_disable;
// Fila de la rampa: -1 usa la de la zona (tinta_rampa).
uniform int ramp_row : hint_range(-1, 4) = -1;
uniform vec4 water_color : source_color = vec4(0.045, 0.06, 0.07, 1.0);
uniform vec4 sky_color : source_color = vec4(0.58, 0.6, 0.6, 1.0);
uniform float reflection : hint_range(0.0, 1.0) = 0.42;
uniform vec4 slush_color : source_color = vec4(0.55, 0.58, 0.59, 1.0);
// La corriente, en metros por segundo en el plano del mundo (x, z): el Tumán corre al oeste.
uniform vec2 flow = vec2(-0.35, 0.0);
uniform float ripple_scale = 0.85;
uniform float ripple_strength : hint_range(0.0, 1.0) = 0.16;
// Cuánto hielo menudo baja flotando (0: nada).
uniform float frazil_amount : hint_range(0.0, 1.0) = 0.45;
uniform float glint_strength : hint_range(0.0, 2.0) = 0.7;

const float RAMP_ROWS = 5.0;

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

// La altura de los rizos: dos trenes que bajan con la corriente a distinta velocidad.
float ripples(vec2 p, float t) {
	vec2 q = p * ripple_scale;
	return value_noise(vec3(q - flow * t * 0.9, t * 0.3)) * 0.6
		+ value_noise(vec3(q * 2.3 - flow * t * 1.4, t * 0.45 + 5.0)) * 0.4;
}

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = world_position.xz;
	float t = TIME;
	float slush = COLOR.a;
	// La normal de los rizos (por diferencias), más quieta donde hay aguanieve.
	float e = 0.12;
	float h0 = ripples(p, t);
	vec2 slope = vec2(ripples(p + vec2(e, 0.0), t) - h0, ripples(p + vec2(0.0, e), t) - h0) / e;
	float strength = ripple_strength * (1.0 - slush * 0.85);
	vec3 n_world = normalize(vec3(-slope.x * strength, 1.0, -slope.y * strength));
	NORMAL = normalize((VIEW_MATRIX * vec4(n_world, 0.0)).xyz);
	// El hielo menudo: tortas de hielo que bajan con la corriente.
	vec2 drift = p - flow * t;
	float clumps = value_noise(vec3(drift * 0.5, 3.0)) * 0.7 + value_noise(vec3(drift * 2.2, 7.0)) * 0.3;
	float frazil = smoothstep(0.66, 0.7, clumps) * frazil_amount;
	// El aguanieve del borde, deshilachada.
	float edge = smoothstep(0.3, 0.9, slush + (clumps - 0.5) * 0.6);
	vec3 base = mix(water_color.rgb, slush_color.rgb, max(edge, frazil));
	ALBEDO = base;
	ROUGHNESS = 0.3;
	// El cielo reflejado, de refilón y donde no hay hielo.
	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	EMISSION = sky_color.rgb * fresnel * reflection * (1.0 - max(edge, frazil));
}

void light() {
	float row = float(ramp_row < 0 ? tinta_rampa : ramp_row);
	float band_t = clamp(dot(NORMAL, LIGHT) * 0.5 + 0.5, 0.0, 1.0);
	vec3 band = texture(ramps, vec2(band_t, (row + 0.5) / RAMP_ROWS)).rgb * 2.0;
	DIFFUSE_LIGHT += band * LIGHT_COLOR / PI * ATTENUATION;
	// Destellos del sol en los rizos: duros, como el resto del dibujo.
	vec3 halfway = normalize(LIGHT + VIEW);
	float glint = step(0.985, dot(NORMAL, halfway));
	SPECULAR_LIGHT += glint * LIGHT_COLOR * glint_strength * ATTENUATION * (1.0 - ALBEDO.r * 1.2);
}
