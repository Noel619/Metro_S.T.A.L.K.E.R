// La ciudad lejana (la versión simple de cada sector): color plano de la niebla,
// sin luz. A esa distancia la niebla ya lo tapa todo, así que se ve igual que la
// versión detallada pero cuesta mucho menos. Lo que sigue destacando contra el
// cielo son las siluetas: el perfil de la ciudad.
shader_type spatial;
render_mode unshaded, fog_disabled, shadows_disabled;

// Niebla de la superficie (la fija Atmosphere; llega en sRGB).
global uniform vec4 tinta_niebla;

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void fragment() {
	ALBEDO = srgb_to_linear(tinta_niebla.rgb);
}
