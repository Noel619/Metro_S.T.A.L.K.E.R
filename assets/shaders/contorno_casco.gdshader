// Contorno por casco invertido (F1-03): una copia de la malla, hinchada a lo
// largo de sus normales suavizadas y dibujada solo por detrás, en color de tinta.
//
// Da a los objetos clave, a las personas y a las criaturas un contorno más grueso
// y más de pincel que el del post-proceso. El grosor se mide en píxeles (igual de
// cerca que de lejos), tiembla a saltos con el trazo vivo y engorda con el miedo.
// La malla del casco la construye scripts/style/ink_hull.gd.
shader_type spatial;
render_mode unshaded, cull_front, depth_draw_opaque, shadows_disabled, fog_disabled;

global uniform vec4 tinta_color;
global uniform float tinta_miedo;
global uniform float tinta_trazo_fps;
global uniform float tinta_negro;

// Grosor del contorno a 1080p.
uniform float grosor_px = 2.6;
// Cuánto varía el grosor a lo largo del trazo (0 = regular).
uniform float irregularidad : hint_range(0.0, 1.0) = 0.45;
uniform sampler2D boil_noise : filter_linear, repeat_enable;

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void vertex() {
	vec4 clip = PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	vec3 view_normal = normalize((MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec2 offset = (PROJECTION_MATRIX * vec4(view_normal, 0.0)).xy;
	float offset_length = length(offset);
	offset = offset_length > 0.0001 ? offset / offset_length : vec2(0.0);
	// Trazo vivo: el grosor cambia a saltos, como el contorno del post-proceso.
	float fear = clamp(tinta_miedo, 0.0, 1.0);
	float step_index = floor(TIME * tinta_trazo_fps * (1.0 + fear * 0.5));
	vec2 seed = fract(vec2(step_index * 0.6180339, step_index * 0.3819660));
	vec2 noise_uv = VERTEX.xy * 3.1 + VERTEX.zx * 1.7 + seed;
	float wobble = textureLod(boil_noise, noise_uv, 0.0).r;
	float width = grosor_px * (1.0 + fear * 0.9) * (1.0 + (wobble - 0.5) * 2.0 * irregularidad);
	float res_scale = VIEWPORT_SIZE.y / 1080.0;
	clip.xy += offset * width * res_scale * 2.0 / VIEWPORT_SIZE * clip.w;
	POSITION = clip;
}

void fragment() {
	// De noche (tinta_negro = 1) la tinta es casi negra, como el relleno del post-proceso.
	ALBEDO = srgb_to_linear(tinta_color.rgb) * mix(1.0, 0.18, tinta_negro);
}
