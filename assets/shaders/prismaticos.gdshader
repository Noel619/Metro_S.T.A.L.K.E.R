// Mirar por los prismáticos (F3-05): lo de fuera de las dos lentes, negro de tinta, con el
// borde de cada lente algo más oscuro, como un aro dibujado.
shader_type canvas_item;

uniform float aspect = 1.7778;
uniform vec4 tinta : source_color = vec4(0.06, 0.055, 0.05, 1.0);

void fragment() {
	vec2 uv = UV * 2.0 - 1.0;
	uv.x *= aspect;
	float radius = 0.66;
	float d = min(length(uv - vec2(-0.45, 0.0)), length(uv - vec2(0.45, 0.0)));
	float outside = smoothstep(radius - 0.02, radius + 0.01, d);
	float rim = smoothstep(radius - 0.07, radius - 0.02, d) * (1.0 - outside);
	COLOR = vec4(tinta.rgb, clamp(outside + rim * 0.55, 0.0, 1.0));
}
