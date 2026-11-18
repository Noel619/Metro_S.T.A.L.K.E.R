// Cuerpo común del sombreado por bandas de Tumansk (ver tinta.gdshader).
// Lo incluyen tinta.gdshader (opaco) y tinta_recorte.gdshader (con recorte
// por alfa, para papeles, carteles y hojas). Variantes, con #define antes del
// #include:
// - TINTA_SUELO: el suelo de la ciudad (tinta_suelo.gdshader). El color y la
//   nieve salen de data/ciudad/suelo.png, proyectado desde arriba.
// - TINTA_FACHADA: fachadas de la maqueta (tinta_fachada.gdshader). La textura
//   (las ventanas) solo se aplica donde el alfa del color de vértice lo pide.
// - TINTA_HITO: los hitos de la ciudad (tinta_hito.gdshader). La niebla nunca
//   los borra del todo: el jugador se orienta con ellos.
// - TINTA_TRANSITO: los pavimentos de la ciudad (tinta_transito.gdshader). La nieve
//   va a parches como en el suelo; cuánta cubre la dice el alfa del color de vértice.
// - TINTA_MURO: los muros del kit de arquitectura (tinta_muro.gdshader). La
//   suciedad, los chorretones, el ladrillo, la plaqueta y el revoque caído se
//   calculan en el espacio del mundo, así que siguen de una pieza a la de al lado
//   sin repetirse; el hollín de los incendios sale de los datos de cada instancia.

global uniform int tinta_rampa;
// Luz que queda en la sombra, en fracción del tono medio de la rampa: sin ella, lo que
// no da al sol solo recibe la luz ambiente y se hunde en negro.
global uniform float tinta_sombra;
#ifdef TINTA_MURO
// Datos de cada instancia (MultiMesh con use_custom_data, ver BuildingKit): r, el
// desgaste (cuánto revoque se ha caído); g, el hollín de un incendio; b y a, de dónde
// sale el hollín: x y altura de lo alto del hueco quemado, en metros de la pieza.
varying vec4 muro_datos;
varying vec3 muro_local;
// Suciedad a gran escala (manchas) y chorretones verticales.
uniform float grime_amount : hint_range(0.0, 1.0) = 0.25;
uniform float streak_amount : hint_range(0.0, 1.0) = 0.28;
uniform vec4 grime_tint : source_color = vec4(0.6, 0.56, 0.5, 1.0);
// Aparejo de ladrillo: 0 ninguno; 1 en todo el muro; 2 solo donde se ha caído el
// revoque (el alfa del color dice dónde es más fácil y el desgaste, cuánto).
uniform int brick_mode : hint_range(0, 2) = 0;
// Ladrillo ruso: 250 × 65 mm más la junta de 12 mm.
uniform vec2 brick_size = vec2(0.262, 0.077);
// Lo que tiñe el color del muro para hacerlo ladrillo (1 si el muro ya es de ladrillo).
uniform vec4 brick_tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float mortar_dark : hint_range(0.0, 1.0) = 0.3;
// Plaqueta cerámica de los paneles (0: sin plaqueta). Solo en las caras con alfa.
uniform float tile_size = 0.0;
uniform vec4 soot_color : source_color = vec4(0.075, 0.066, 0.06, 1.0);
#endif
#ifdef TINTA_HITO
// Niebla de la superficie (la fija Atmosphere; el color llega en sRGB).
global uniform vec4 tinta_niebla;
global uniform float tinta_niebla_densidad;
// Cuánto puede tapar la niebla a un hito, como mucho.
uniform float hito_niebla_max : hint_range(0.0, 1.0) = 0.78;
#endif
#ifdef TINTA_SUELO
// RGB: color del suelo bajo la nieve; A: cuánta nieve lo cubre.
uniform sampler2D ground_map : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
// Metros que cubre ground_map (el mapa jugable, con el origen en la esquina suroeste).
uniform vec2 ground_size = vec2(1600.0, 1200.0);
#endif

uniform vec4 albedo_color : source_color = vec4(1.0);
uniform sampler2D albedo_texture : source_color, hint_default_white, filter_linear_mipmap, repeat_enable;
uniform bool use_vertex_color = true;
// Recorte de la textura: para láminas con varias casillas (las caras dibujadas).
uniform vec2 uv_scale = vec2(1.0, 1.0);
uniform vec2 uv_offset = vec2(0.0, 0.0);
uniform sampler2D ramps : hint_default_white, filter_linear, repeat_disable;
// Fila de la rampa: -1 usa la de la zona (tinta_rampa); 3 piel; 4 metal.
uniform int ramp_row : hint_range(-1, 4) = -1;
uniform float snow_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 snow_color : source_color = vec4(0.86, 0.85, 0.81, 1.0);
uniform float rim_strength : hint_range(0.0, 1.0) = 0.0;
uniform vec4 emission_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float emission_energy : hint_range(0.0, 16.0) = 0.0;

const float RAMP_ROWS = 5.0;

varying vec3 world_normal;
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

void vertex() {
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
#ifdef TINTA_MURO
	muro_datos = INSTANCE_CUSTOM;
	muro_local = VERTEX;
#endif
}

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

#ifdef TINTA_MURO
// Junta de una rejilla (ladrillos, plaqueta): 1 en la junta, 0 en la pieza, sin dientes
// de sierra. [param gap] es el ancho de la junta en fracciones de pieza y [param w], lo
// que cambia p de un píxel al de al lado (fwidth).
float grid_joint(vec2 p, vec2 gap, vec2 w) {
	vec2 f = fract(p);
	vec2 edge = min(f, 1.0 - f);
	vec2 joint = 1.0 - smoothstep(gap * 0.5 - w, gap * 0.5 + w, edge);
	return max(joint.x, joint.y);
}

// Cuánto se ve una rejilla: de lejos, sus juntas se funden en un tono medio.
float grid_fade(vec2 w) {
	return 1.0 - smoothstep(0.18, 0.45, max(w.x, w.y));
}

// Hollín de un incendio en el punto [param p] de la pieza (x a lo largo, y la altura):
// sale de lo alto del hueco quemado ([param source]) y sube abriéndose.
float soot_plume(vec2 p, vec2 source) {
	float rise = p.y - source.y;
	float height = 3.3;
	if (rise < -0.35 || rise > height) {
		return 0.0;
	}
	float spread = 1.45 * (0.5 + 0.45 * max(rise, 0.0) / height);
	float side = abs(p.x - source.x) / spread;
	float wiggle = (value_noise(vec3(p.x * 2.3, p.y * 1.1, source.x * 5.0)) - 0.5) * 0.7;
	return (1.0 - max(rise, 0.0) / height) * (1.0 - clamp(side + wiggle, 0.0, 1.0));
}
#endif

void fragment() {
	vec2 uv = UV * uv_scale + uv_offset;
#ifdef TINTA_FACHADA
	vec3 base = albedo_color.rgb * mix(vec3(1.0), texture(albedo_texture, uv).rgb, COLOR.a);
#else
	vec3 base = albedo_color.rgb * texture(albedo_texture, uv).rgb;
#endif
	if (use_vertex_color) {
		base *= COLOR.rgb;
	}
#ifdef TINTA_TRANSITO
	// Nada está limpio: manchas grandes de hollín, aceite y humedad, y otras más pequeñas
	// encima. Es el pavimento de una ciudad que nadie limpia desde hace dos años.
	float stain = value_noise(world_position * 0.045) * 0.55 + value_noise(world_position * 0.19) * 0.3
		+ value_noise(world_position * 0.9) * 0.15;
	base *= mix(0.62, 1.06, smoothstep(0.15, 0.85, stain));
#endif
#ifdef TINTA_MURO
	{
		vec3 n = normalize(world_normal);
		float wall = 1.0 - smoothstep(0.35, 0.65, abs(n.y));
		// Coordenadas sobre el muro: a lo largo (en horizontal) y la altura.
		vec2 along = normalize(vec2(-n.z, n.x) + vec2(1e-4, 0.0));
		vec2 uv = vec2(dot(world_position.xz, along), world_position.y);
		// Plaqueta: solo en las caras de fachada (alfa), con alguna pieza caída.
		if (tile_size > 0.0) {
			vec2 tp = uv / tile_size;
			vec2 tw = max(fwidth(tp), vec2(1e-4));
			float shown = grid_fade(tw) * wall * step(0.5, COLOR.a);
			float missing = step(0.965, hash(vec3(floor(tp), 7.0)));
			vec3 tiled = base * mix(mix(0.94, 1.05, hash(vec3(floor(tp), 1.0))), 0.72, missing);
			tiled = mix(tiled, base * 0.82, grid_joint(tp, vec2(0.1), tw));
			base = mix(base, tiled, shown);
		}
		if (brick_mode > 0) {
			vec2 bp = uv / brick_size;
			bp.x += mod(floor(bp.y), 2.0) * 0.5;
			vec2 bw = max(fwidth(bp), vec2(1e-4));
			float shown = grid_fade(bw);
			vec3 brick = base * brick_tint.rgb;
			vec3 bricks = mix(brick, brick * mix(0.86, 1.1, hash(vec3(floor(bp), 3.0))), shown);
			bricks = mix(bricks, brick * (1.0 - mortar_dark), grid_joint(bp, vec2(0.046, 0.156), bw) * shown);
			if (brick_mode == 1) {
				base = mix(base, bricks, wall);
			} else {
				// Revoque caído: manchas sueltas de medio metro a dos, que el ruido reparte por
				// el muro; el alfa (junto a los huecos y abajo) solo las hace algo más
				// probables y el desgaste del edificio, más grandes. Borde de tinta.
				float grain = value_noise(world_position * 0.9) * 0.65 + value_noise(world_position * 3.7) * 0.35;
				float m = (grain - 0.5) + (COLOR.a - 0.5) * 0.25 + muro_datos.r * 0.25 - 0.32;
				float mw = max(fwidth(m), 1e-4);
				base = mix(base, bricks, smoothstep(-mw, mw, m) * wall);
				base *= 1.0 - (1.0 - smoothstep(0.0, 2.5 * mw, abs(m))) * wall * 0.55;
			}
		}
		// Manchas grandes y chorretones de lluvia y hollín.
		float patches = value_noise(vec3(uv.x * 0.21, uv.y * 0.33, 0.5)) * 0.65
			+ value_noise(vec3(uv.x * 0.9, uv.y * 0.6, 4.2)) * 0.35;
		float streaks = smoothstep(0.55, 0.85, value_noise(vec3(uv.x * 3.1, uv.y * 0.06, 9.7)));
		float dirt = clamp((patches - 0.5) * grime_amount * 1.8 + streaks * streak_amount, -0.3, 1.0) * wall;
		base *= mix(vec3(1.0), grime_tint.rgb, max(dirt, 0.0));
		base *= 1.0 + max(-dirt, 0.0) * 0.18;
		if (muro_datos.g > 0.0) {
			float soot = soot_plume(muro_local.xy, muro_datos.ba);
			base = mix(base, soot_color.rgb, clamp(soot * muro_datos.g * 1.7, 0.0, 1.0));
		}
	}
#endif
#ifdef TINTA_SUELO
	// El plano tiene el norte en -Z; la primera fila de ground_map es el borde norte.
	vec2 plan = vec2(world_position.x, -world_position.z);
	vec4 ground = texture(ground_map, vec2(plan.x / ground_size.x, 1.0 - plan.y / ground_size.y));
	base *= ground.rgb;
#endif
	if (snow_amount > 0.0) {
#if defined(TINTA_SUELO) || defined(TINTA_TRANSITO)
		// Nieve vieja a parches: cubre lo que pide el suelo y resbala de las cuestas.
		float n = value_noise(world_position * 0.31) * 0.55 + value_noise(world_position * 1.7) * 0.3
			+ value_noise(world_position * 7.0) * 0.15;
#ifdef TINTA_SUELO
		float amount = ground.a;
#else
		float amount = COLOR.a;
#endif
		float cover = amount * smoothstep(0.62, 0.9, normalize(world_normal).y) * snow_amount;
		float snow = smoothstep(n - 0.06, n + 0.06, cover);
#else
		float n = value_noise(world_position * 3.0) * 0.6 + value_noise(world_position * 11.0) * 0.4;
		float snow = smoothstep(0.55, 0.8, normalize(world_normal).y + (n - 0.5) * 0.35) * snow_amount;
#endif
		// Nieve vieja: ceniza, hollín y pisadas, nunca blanca del todo.
		float dirt = value_noise(world_position * 1.7) * 0.7 + value_noise(world_position * 23.0) * 0.3;
		float soot = smoothstep(0.7, 0.82, value_noise(world_position * 5.0 + 17.0));
		vec3 old_snow = snow_color.rgb * mix(0.84, 1.03, dirt) * (1.0 - soot * 0.18);
		base = mix(base, old_snow, snow);
	}
	ALBEDO = base;
#ifdef TINTA_RECORTE
	ALPHA = albedo_color.a * texture(albedo_texture, uv).a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
#endif
	ROUGHNESS = 1.0;
	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	EMISSION = emission_color.rgb * emission_energy + base * fresnel * rim_strength * 0.5;
#ifdef TINTA_HITO
	float fog_amount = 1.0 - exp(-tinta_niebla_densidad * length(VERTEX));
	FOG = vec4(srgb_to_linear(tinta_niebla.rgb), min(fog_amount, hito_niebla_max));
#endif
}

void light() {
	float row = float(ramp_row < 0 ? tinta_rampa : ramp_row);
	float v = (row + 0.5) / RAMP_ROWS;
	// Las bandas dependen solo del ángulo con la luz; la caída con la distancia y
	// las sombras proyectadas (ATTENUATION) se aplican después, suaves.
	float t = clamp(dot(NORMAL, LIGHT) * 0.5 + 0.5, 0.0, 1.0);
	// Las rampas se guardan a la mitad para admitir brillos por encima de 1.
	vec3 band = texture(ramps, vec2(t, v)).rgb * 2.0;
	// Relleno de la sombra: el tono medio de la rampa (frío en la calle, cálido en el
	// depósito), rebajado. Las sombras propias y las proyectadas reciben lo mismo.
	vec3 fill = texture(ramps, vec2(0.56, v)).rgb * 2.0 * tinta_sombra;
	// LIGHT_COLOR ya viene multiplicado por PI.
	if (LIGHT_IS_DIRECTIONAL) {
		DIFFUSE_LIGHT += max(band * ATTENUATION, fill) * LIGHT_COLOR / PI;
	} else {
		DIFFUSE_LIGHT += max(band, fill) * LIGHT_COLOR / PI * ATTENUATION;
	}
}
