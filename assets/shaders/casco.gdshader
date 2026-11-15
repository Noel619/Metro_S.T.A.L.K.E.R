// Contorno por casco invertido: el trazo grueso de personajes y objetos clave.
//
// Se pone como segunda pasada (next_pass) de un material. Dibuja el modelo otra
// vez, visto por dentro y un poco hinchado, de color tinta: lo que asoma por
// fuera de la silueta es la línea. El grosor se mide en píxeles (no depende de
// la distancia), sigue al grosor de la zona y al miedo (tinta_grosor,
// tinta_miedo) y cambia a saltos, como el contorno del post-proceso.
shader_type spatial;
render_mode unshaded, cull_front, shadows_disabled, specular_disabled;

global uniform float tinta_grosor;
global uniform float tinta_miedo;
global uniform float tinta_trazo_fps;
global uniform float tinta_negro;
// Los colores globales llegan en sRGB: se pasan a lineal en el fragmento.
global uniform vec4 tinta_color;

// Grosor respecto al del contorno de la zona.
uniform float width_scale : hint_range(0.0, 3.0) = 0.9;
// Cuánto varía el grosor a lo largo del trazo (0 = uniforme).
uniform float irregularity : hint_range(0.0, 1.0) = 0.45;

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void vertex() {
	float fear = clamp(tinta_miedo, 0.0, 1.0);
	float step_index = floor(TIME * tinta_trazo_fps * (1.0 + fear * 0.5));
	float wave = 0.5 + 0.5 * sin(dot(VERTEX, vec3(31.0, 17.0, 23.0)) + step_index * 1.7);
	float width = (tinta_grosor + fear * 1.5) * width_scale * (VIEWPORT_SIZE.y / 1080.0);
	width *= mix(1.0, 0.45 + 1.1 * wave, irregularity);
	vec4 clip = PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	vec2 direction = (PROJECTION_MATRIX * vec4(normalize(MODELVIEW_NORMAL_MATRIX * NORMAL), 0.0)).xy;
	float size = length(direction);
	if (size > 0.0001) {
		clip.xy += direction / size * width * 2.0 / VIEWPORT_SIZE * clip.w;
	}
	POSITION = clip;
}

void fragment() {
	ALBEDO = srgb_to_linear(tinta_color.rgb) * mix(1.0, 0.18, tinta_negro);
}
