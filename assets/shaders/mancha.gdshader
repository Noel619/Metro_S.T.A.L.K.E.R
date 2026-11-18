// Polvo y manchas del suelo del depósito (F2-05): un borrón irregular que se
// desvanece a medida que se barre o se friega. Se dibuja encima del suelo, con
// la luz de la escena, sin escribir profundidad.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, diffuse_lambert, specular_disabled;

uniform vec4 color : source_color = vec4(0.45, 0.4, 0.33, 1.0);
// Lo que queda de suciedad: 1 recién llegada, 0 limpio.
uniform float amount : hint_range(0.0, 1.0) = 1.0;
uniform float seed = 0.0;
// Con trazos de barrido (polvo) o con cerco (mancha de agua o de grasa).
uniform bool ring = false;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
	float total = 0.0;
	float weight = 0.5;
	for (int i = 0; i < 4; i++) {
		total += noise(p) * weight;
		p *= 2.1;
		weight *= 0.5;
	}
	return total;
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float edge = length(p) + (fbm(UV * 3.0 + seed) - 0.5) * 0.7;
	float shape = 1.0 - smoothstep(0.45, 0.95, edge);
	float grain = fbm(UV * 9.0 + seed * 1.7);
	float alpha = shape * mix(0.55, 1.0, grain);
	if (ring) {
		alpha = shape * (0.5 + 0.5 * smoothstep(0.55, 0.85, edge + 0.25)) * mix(0.7, 1.0, grain);
	}
	// Al limpiar, primero se va lo fino de los bordes y lo que queda se aclara.
	alpha *= smoothstep(0.0, 0.35, amount) * mix(0.35, 1.0, amount);
	alpha *= step(1.0 - amount * 1.1, shape * grain + 0.25);
	ALBEDO = color.rgb * mix(0.85, 1.1, grain);
	ALPHA = clamp(alpha * 1.15, 0.0, 0.92);
}
