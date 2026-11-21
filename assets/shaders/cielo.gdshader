// Cielo pintado de Tumansk: invierno nuclear, siempre encapotado.
//
// Un techo bajo de nubes cubre casi todo el cielo. No son manchas sueltas, sino
// una capa continua con vetas largas que el viento estira, pintada a pinceladas
// anchas y suaves, sin contorno de tinta: el dibujo se reserva para el mundo. Por
// donde la capa clarea asoma un cielo pálido, y el sol (o la luna) es solo un
// resplandor difuso detrás. En el horizonte, todo se funde con la niebla.
// Nunca es negro: de noche la capa sigue recortándose contra el cielo.
// Los valores de cada hora del día están en scripts/surface/atmosphere.gd.
shader_type sky;

uniform vec4 zenith_color : source_color = vec4(0.44, 0.45, 0.46, 1.0);
uniform vec4 horizon_color : source_color = vec4(0.66, 0.63, 0.54, 1.0);
uniform vec4 ground_color : source_color = vec4(0.30, 0.29, 0.27, 1.0);
uniform vec4 cloud_light : source_color = vec4(0.72, 0.70, 0.63, 1.0);
uniform vec4 cloud_dark : source_color = vec4(0.42, 0.42, 0.43, 1.0);
uniform vec4 glow_color : source_color = vec4(0.95, 0.86, 0.70, 1.0);
// Color de la niebla: el horizonte acaba en él, para que el cielo y la ciudad se junten.
uniform vec4 haze_color : source_color = vec4(0.52, 0.51, 0.48, 1.0);
uniform float glow_strength : hint_range(0.0, 4.0) = 0.35;
uniform float glow_size : hint_range(1.0, 64.0) = 5.0;
// Cuánto cielo tapa la capa de nubes (1: encapotado del todo).
uniform float coverage : hint_range(0.0, 1.0) = 0.72;
uniform float cloud_scale = 1.0;
uniform float cloud_speed = 0.0015;
// Hacia dónde sopla el viento (las vetas se estiran en esa dirección).
uniform vec2 wind = vec2(0.8, 0.6);
// Pinceladas: cuánto se notan las vetas de pincel en la capa.
uniform float brush_strength : hint_range(0.0, 1.0) = 0.1;
uniform float brightness : hint_range(0.0, 2.0) = 1.0;
uniform sampler2D cloud_noise : filter_linear_mipmap, repeat_enable;

// Ruido en capas: grandes masas, vetas medianas y detalle fino.
float fbm(vec2 uv) {
	return texture(cloud_noise, uv).r * 0.55
		+ texture(cloud_noise, uv * 2.1 + vec2(0.31, 0.17)).g * 0.3
		+ texture(cloud_noise, uv * 4.7 + vec2(0.63, 0.41)).b * 0.15;
}

void sky() {
	vec3 dir = normalize(EYEDIR);
	float up = dir.y;

	// --- Cielo de fondo: pálido y lechoso, apenas más oscuro en lo alto ---
	vec3 color = mix(horizon_color.rgb, zenith_color.rgb, smoothstep(0.0, 0.7, up));
	color = mix(color, ground_color.rgb, smoothstep(0.0, -0.2, up));

	// --- Resplandor del sol (o de la luna) detrás de las nubes: ancho y difuso ---
	float toward_light = LIGHT0_ENABLED ? max(dot(dir, LIGHT0_DIRECTION), 0.0) : 0.0;
	float halo = pow(toward_light, glow_size) * glow_strength;
	float wide = pow(toward_light, max(glow_size * 0.25, 1.0)) * glow_strength * 0.35;

	// --- La capa de nubes, proyectada sobre un techo plano ---
	float dome = max(up, 0.0) + 0.1;
	vec2 plane = dir.xz / dome;
	// Se estira a lo largo del viento: vetas largas, no borlas.
	vec2 along = normalize(wind);
	vec2 across = vec2(-along.y, along.x);
	vec2 stretched = vec2(dot(plane, along) * 0.55, dot(plane, across));
	vec2 drift = along * TIME * cloud_speed;
	vec2 uv = stretched * 0.06 * cloud_scale + drift;
	float shape = fbm(uv);
	// Bordes muy suaves: donde la capa clarea, se deshace poco a poco.
	float threshold = 1.0 - coverage;
	float density = smoothstep(threshold - 0.12, threshold + 0.22, shape);
	// Dentro de la capa: más oscura donde es más gruesa y más clara del lado de la luz.
	float thick = smoothstep(threshold, threshold + 0.5, fbm(uv * 0.6 + vec2(0.5, 0.2)));
	vec2 toward = LIGHT0_ENABLED ? normalize(LIGHT0_DIRECTION.xz + vec2(0.0001)) : vec2(0.0);
	float lit = clamp(0.5 + (shape - fbm(uv + toward * 0.04)) * 4.0, 0.0, 1.0);
	float shade = clamp(mix(lit, 1.0 - thick, 0.55), 0.0, 1.0);
	// Pinceladas: vetas finas a lo largo del viento, como un pincel seco.
	float brush = texture(cloud_noise, vec2(dot(plane, along) * 0.015, dot(plane, across) * 0.25) + drift).g;
	shade = clamp(shade + (brush - 0.5) * brush_strength, 0.0, 1.0);
	vec3 cloud = mix(cloud_dark.rgb, cloud_light.rgb, shade);
	// La luz se cuela por la capa: el halo tiñe sus bordes y lo que tiene delante.
	cloud += glow_color.rgb * (halo * 0.6 + wide) * (1.0 - density * 0.5);

	color += glow_color.rgb * (halo + wide) * (1.0 - density);
	color = mix(color, cloud, density);

	// --- Horizonte: la capa se aleja y todo acaba en la niebla de la ciudad ---
	// Por debajo del techo de nubes queda una franja de luz baja, más viva del lado del
	// sol: al anochecer es lo único cálido del cielo.
	float azimuth = LIGHT0_ENABLED
		? max(dot(normalize(dir.xz + vec2(0.0001)), normalize(LIGHT0_DIRECTION.xz + vec2(0.0001))), 0.0)
		: 0.0;
	float band = (1.0 - smoothstep(0.0, 0.12, abs(up - 0.03))) * (0.35 + 0.65 * azimuth * azimuth);
	color += glow_color.rgb * band * glow_strength * 0.45;
	float haze = 1.0 - smoothstep(-0.02, 0.18, up);
	color = mix(color, haze_color.rgb + glow_color.rgb * band * glow_strength * 0.3, haze);

	COLOR = color * brightness;
}
