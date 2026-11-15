// Cielo pintado de Tumansk.
//
// Degradado del horizonte al cénit, resplandor del sol (o de la luna) detrás de
// las nubes y nubes a bandas, con contorno de tinta y tramado en su parte oscura.
// Nunca es negro: de noche las nubes siguen recortándose contra el cielo.
// Los valores de cada hora del día están en scripts/surface/atmosphere.gd.
shader_type sky;

uniform vec4 zenith_color : source_color = vec4(0.44, 0.45, 0.46, 1.0);
uniform vec4 horizon_color : source_color = vec4(0.66, 0.63, 0.54, 1.0);
uniform vec4 ground_color : source_color = vec4(0.30, 0.29, 0.27, 1.0);
uniform vec4 cloud_light : source_color = vec4(0.72, 0.70, 0.63, 1.0);
uniform vec4 cloud_dark : source_color = vec4(0.42, 0.42, 0.43, 1.0);
uniform vec4 glow_color : source_color = vec4(0.95, 0.86, 0.70, 1.0);
uniform vec4 ink_color : source_color = vec4(0.106, 0.102, 0.133, 1.0);
uniform float glow_strength : hint_range(0.0, 4.0) = 0.35;
uniform float glow_size : hint_range(1.0, 64.0) = 5.0;
uniform float coverage : hint_range(0.0, 1.0) = 0.72;
uniform float cloud_scale = 1.8;
uniform float cloud_speed = 0.003;
uniform float line_strength : hint_range(0.0, 1.0) = 0.5;
uniform float hatch_strength : hint_range(0.0, 1.0) = 0.25;
uniform float brightness : hint_range(0.0, 2.0) = 1.0;
uniform sampler2D cloud_noise : filter_linear_mipmap, repeat_enable;
uniform sampler2D hatching : filter_linear_mipmap, repeat_enable;

float cloud_shape(vec2 uv) {
	return texture(cloud_noise, uv).r * 0.88 + texture(cloud_noise, uv * 2.3 + 0.37).g * 0.12;
}

void sky() {
	vec3 dir = normalize(EYEDIR);
	float up = dir.y;
	vec3 color = mix(horizon_color.rgb, zenith_color.rgb, smoothstep(-0.02, 0.55, up));
	color = mix(color, ground_color.rgb, smoothstep(0.0, -0.25, up));

	float toward_light = LIGHT0_ENABLED ? max(dot(dir, LIGHT0_DIRECTION), 0.0) : 0.0;
	float glow = pow(toward_light, glow_size) * glow_strength;
	color += glow_color.rgb * glow;

	// Nubes proyectadas sobre una cúpula.
	float dome = max(up, 0.0) + 0.12;
	vec2 drift = vec2(TIME * cloud_speed, TIME * cloud_speed * 0.4);
	vec2 uv = dir.xz / dome * 0.18 * cloud_scale + drift;
	float shape = cloud_shape(uv);
	float threshold = 1.0 - coverage;
	float density = smoothstep(threshold, threshold + 0.06, shape);
	float near_horizon = smoothstep(-0.02, 0.12, up);
	// Nubes en dos tonos: el borde, más oscuro; el centro, más claro, y más aún del
	// lado del sol (o de la luna).
	vec2 toward = LIGHT0_ENABLED ? normalize(LIGHT0_DIRECTION.xz + vec2(0.0001)) : vec2(0.0);
	float core = smoothstep(threshold + 0.1, threshold + 0.13, cloud_shape(uv - toward * 0.025));
	float band = core * (0.55 + 0.45 * step(0.5, texture(cloud_noise, uv * 0.35).b));
	vec3 cloud = mix(cloud_dark.rgb, cloud_light.rgb, band) + glow_color.rgb * glow * 0.5 * core;
	color = mix(color, cloud, density * near_horizon);

	if (!AT_CUBEMAP_PASS) {
		float edge_width = max(fwidth(shape) * 1.6, 0.0005);
		float edge = 1.0 - smoothstep(0.0, edge_width, abs(shape - (threshold + 0.03)));
		color = mix(color, ink_color.rgb, edge * line_strength * near_horizon);
		float hatch = texture(hatching, uv * 5.0).g;
		color = mix(color, ink_color.rgb, (1.0 - hatch) * hatch_strength * density * (1.0 - band) * near_horizon);
	}
	COLOR = color * brightness;
}
