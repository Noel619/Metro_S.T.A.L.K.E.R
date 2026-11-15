// Siluetas lejanas (ruinas del horizonte): color plano, sin luz ni niebla del
// motor, fundidas con el color del horizonte (tinta_horizonte). Cuanto mayor es
// "capa", más cerca está la silueta y más oscura se ve, como en un decorado
// de papel recortado.
shader_type spatial;
render_mode unshaded, fog_disabled, shadows_disabled;

global uniform vec4 tinta_horizonte;

uniform float capa : hint_range(0.0, 1.0) = 0.5;

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void fragment() {
	vec3 horizon = srgb_to_linear(tinta_horizonte.rgb);
	float detail = dot(COLOR.rgb, vec3(0.2126, 0.7152, 0.0722));
	vec3 silhouette = horizon * mix(0.92, 0.55, capa) * mix(0.8, 1.15, clamp(detail * 3.0, 0.0, 1.0));
	ALBEDO = silhouette;
}
