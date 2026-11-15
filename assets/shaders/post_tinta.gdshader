// Post-proceso del estilo entintado. Se dibuja en un rectángulo que cubre la
// pantalla (scenes/style/ink_post.tscn) y añade, en este orden:
//
// 1. Gradación de color de la zona: saturación, contraste y tinte.
// 2. Tramado: rayas de lápiz en las zonas oscuras. Se pegan al mundo (se
//    proyectan en coordenadas del mundo), así que no "nadan" al mover la cámara.
// 3. Relleno de tinta en los negros más profundos.
// 4. Contorno de tinta: siluetas (por profundidad) y pliegues (por normales).
// 5. Trazo vivo: el contorno y el tramado tiemblan a saltos, como un dibujo
//    animado a mano.
// 6. Papel, grano y viñeta.
//
// Todo lo dinámico llega por parámetros globales (tinta_*), que mueve
// scripts/core/style_director.gd según la zona, el miedo y la radiación.
shader_type spatial;
render_mode unshaded, depth_draw_never, depth_test_disabled, cull_disabled, fog_disabled, shadows_disabled;

global uniform float tinta_miedo;
global uniform float tinta_radiacion;
global uniform float tinta_trazo_fps;
global uniform float tinta_trazo_amplitud;
global uniform float tinta_grosor;
global uniform float tinta_tramado;
global uniform float tinta_tramado_umbral;
global uniform float tinta_relleno;
global uniform float tinta_saturacion;
global uniform float tinta_contraste;
global uniform float tinta_papel;
global uniform float tinta_grano;
global uniform float tinta_vineta;
// Cuánto se oscurece el relleno de tinta (0 = color de la tinta, 1 = casi negro). De noche, 1.
global uniform float tinta_negro;
// Los colores globales llegan en sRGB: se pasan a lineal en el fragmento.
global uniform vec4 tinta_color;
global uniform vec4 tinta_tinte;

uniform sampler2D screen_texture : hint_screen_texture, filter_linear, repeat_disable;
uniform sampler2D depth_texture : hint_depth_texture, filter_nearest, repeat_disable;
uniform sampler2D normal_texture : hint_normal_roughness_texture, filter_nearest, repeat_disable;
uniform sampler2D hatching : filter_linear_mipmap, repeat_enable;
uniform sampler2D paper : filter_linear_mipmap, repeat_enable;
uniform sampler2D boil_noise : filter_linear, repeat_enable;
uniform sampler2D grain : filter_linear, repeat_enable;

// Repeticiones del tramado por metro.
uniform float hatch_scale = 1.6;
uniform float line_depth_threshold = 0.035;
uniform float line_normal_threshold = 0.28;
uniform float line_opacity : hint_range(0.0, 1.0) = 0.92;
// Cuánto toma la línea del color del objeto (0 = tinta pura).
uniform float line_tint : hint_range(0.0, 1.0) = 0.25;
uniform float line_fade_start = 18.0;
uniform float line_fade_end = 60.0;
uniform float paper_scale = 1.4;
// Vista de depuración: 0 normal, 1 profundidad, 2 normales, 3 contorno, 4 tramado,
// 5 color de entrada, 6 relleno de tinta.
uniform int debug_view : hint_range(0, 6) = 0;

const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);

float linear_depth(vec2 uv, mat4 inv_projection) {
	float raw = texture(depth_texture, uv).r;
	vec4 view = inv_projection * vec4(uv * 2.0 - 1.0, raw, 1.0);
	return -view.z / view.w;
}

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

vec3 view_normal(vec2 uv) {
	return normalize(texture(normal_texture, uv).xyz * 2.0 - 1.0);
}

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

void fragment() {
	vec2 pixel = 1.0 / VIEWPORT_SIZE;
	float res_scale = VIEWPORT_SIZE.y / 1080.0;
	float fear = clamp(tinta_miedo, 0.0, 1.0);
	vec3 ink = srgb_to_linear(tinta_color.rgb);
	vec3 tint = srgb_to_linear(tinta_tinte.rgb);

	// Trazo vivo: un desplazamiento suave que cambia a saltos (tinta_trazo_fps).
	float step_index = floor(TIME * tinta_trazo_fps * (1.0 + fear * 0.5));
	vec2 step_seed = fract(vec2(step_index * 0.6180339, step_index * 0.3819660));
	vec2 boil = (texture(boil_noise, SCREEN_UV * 1.7 + step_seed).rg - 0.5) * 2.0;
	vec2 line_uv = SCREEN_UV + boil * tinta_trazo_amplitud * (1.0 + fear * 2.5) * res_scale * pixel;

	// --- Color y gradación ---
	vec3 color = texture(screen_texture, SCREEN_UV).rgb;
	vec3 input_color = color;
	float luma = dot(color, LUMA);
	color = mix(vec3(luma), color, tinta_saturacion * (1.0 - fear * 0.45));
	color = max(vec3(0.0), (color - 0.18) * tinta_contraste + 0.18);
	color *= tint;
	luma = dot(color, LUMA);

	// --- Posición y normal en el mundo (para el tramado) ---
	float raw_depth = texture(depth_texture, SCREEN_UV).r;
	bool is_sky = raw_depth <= 0.000001;
	vec4 view_position = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, raw_depth, 1.0);
	view_position.xyz /= view_position.w;
	vec3 world_position = (INV_VIEW_MATRIX * vec4(view_position.xyz, 1.0)).xyz;
	vec3 center_normal = view_normal(line_uv);
	vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(center_normal, 0.0)).xyz);

	// --- Viñeta (también empuja el tramado con el miedo) ---
	vec2 centered = (SCREEN_UV - 0.5) * vec2(VIEWPORT_SIZE.x / VIEWPORT_SIZE.y, 1.0);
	float vignette = smoothstep(0.35, 1.0, length(centered) + (texture(boil_noise, SCREEN_UV * 0.6).r - 0.5) * 0.15);

	// --- Tramado ---
	vec3 blend = pow(abs(world_normal), vec3(4.0));
	blend /= max(dot(blend, vec3(1.0)), 0.0001);
	vec2 hatch_shift = step_seed * 0.02;
	vec4 hatch_tones = texture(hatching, world_position.zy * hatch_scale + hatch_shift) * blend.x
		+ texture(hatching, world_position.xz * hatch_scale + hatch_shift) * blend.y
		+ texture(hatching, world_position.xy * hatch_scale + hatch_shift) * blend.z;
	float darkness = clamp(1.0 - luma / max(tinta_tramado_umbral, 0.0001), 0.0, 1.0);
	darkness = clamp(darkness + vignette * fear * 0.9, 0.0, 1.0);
	float tone = darkness * 4.0;
	float hatch = 1.0;
	hatch = mix(hatch, hatch_tones.r, clamp(tone, 0.0, 1.0));
	hatch = mix(hatch, hatch_tones.g, clamp(tone - 1.0, 0.0, 1.0));
	hatch = mix(hatch, hatch_tones.b, clamp(tone - 2.0, 0.0, 1.0));
	hatch = mix(hatch, hatch_tones.a, clamp(tone - 3.0, 0.0, 1.0));
	if (is_sky) {
		hatch = 1.0;
	}
	color = mix(color, ink, (1.0 - hatch) * tinta_tramado);

	// --- Relleno de tinta en los negros ---
	// De noche (tinta_negro = 1) el relleno es casi negro: sin luz no se ve nada.
	vec3 deep_ink = ink * mix(1.0, 0.18, tinta_negro);
	float fill = 1.0 - smoothstep(tinta_relleno * 0.5, tinta_relleno, luma);
	color = mix(color, deep_ink, fill * float(!is_sky));

	// --- Contorno ---
	float center_depth = linear_depth(line_uv, INV_PROJECTION_MATRIX);
	float width = (tinta_grosor + fear * 1.5) * res_scale;
	float depth_edge = 0.0;
	float normal_edge = 0.0;
	for (int i = 0; i < 8; i++) {
		float angle = float(i) * 0.7853982;
		vec2 offset = vec2(cos(angle), sin(angle)) * width * pixel;
		float neighbour_depth = linear_depth(line_uv + offset, INV_PROJECTION_MATRIX);
		depth_edge = max(depth_edge, (center_depth - neighbour_depth) / max(center_depth, 0.001));
		normal_edge = max(normal_edge, 1.0 - dot(center_normal, view_normal(line_uv + offset)));
	}
	float line = smoothstep(line_depth_threshold, line_depth_threshold * 2.0, depth_edge);
	if (!is_sky) {
		line = max(line, smoothstep(line_normal_threshold, line_normal_threshold + 0.3, normal_edge));
	}
	line *= 1.0 - smoothstep(line_fade_start, line_fade_end, center_depth);
	// En la oscuridad total no se ven ni los contornos: solo donde llega algo de luz.
	line *= mix(1.0, smoothstep(tinta_relleno * 0.5, tinta_relleno * 3.0, luma), tinta_negro);
	vec3 line_color = mix(ink, min(color, vec3(1.0)) * 0.3, line_tint);
	color = mix(color, line_color, line * line_opacity);

	// --- Papel, grano y viñeta ---
	vec2 paper_uv = SCREEN_UV * vec2(VIEWPORT_SIZE.x / VIEWPORT_SIZE.y, 1.0) * paper_scale;
	color *= mix(1.0, texture(paper, paper_uv).r, tinta_papel);
	float grain_value = texture(grain, SCREEN_UV * VIEWPORT_SIZE / 256.0 + step_seed * 7.0).r - 0.5;
	float grain_amount = tinta_grano + tinta_radiacion * 0.3;
	color = max(vec3(0.0), color * (1.0 + grain_value * grain_amount * 2.0));
	color = mix(color, ink, vignette * tinta_vineta);

	ALBEDO = color;
	if (debug_view == 1) {
		ALBEDO = vec3(fract(center_depth));
	} else if (debug_view == 2) {
		ALBEDO = center_normal * 0.5 + 0.5;
	} else if (debug_view == 3) {
		ALBEDO = vec3(1.0 - line);
	} else if (debug_view == 4) {
		ALBEDO = vec3(hatch);
	} else if (debug_view == 5) {
		ALBEDO = input_color;
	} else if (debug_view == 6) {
		ALBEDO = vec3(fill);
	}
}
