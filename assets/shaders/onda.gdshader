// Las ondas de tinta (F3-01, D-061): lo que suena se ve mientras no hay sonido. Una banda
// vertical que se abre desde donde sonó, entrecortada y con el borde temblón, como las
// líneas de un ruido en un dibujo animado. Sin luz y sin escribir profundidad: la tapan
// las paredes, pero no tapa nada.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec4 tinta : source_color = vec4(0.1, 0.085, 0.075, 1.0);
uniform sampler2D ruido : filter_linear_mipmap, repeat_enable;
// De 0 (acaba de sonar) a 1 (se ha ido).
instance uniform float vida = 0.0;
// Lo fuerte que se dibuja: de 0 a 1.
instance uniform float fuerza = 1.0;
instance uniform float semilla = 0.0;
// Vueltas de la onda, para que los huecos no se estiren con el radio.
instance uniform float vueltas = 6.0;

void fragment() {
	float along = UV.x * vueltas + semilla;
	// Trazos y huecos a lo largo: más huecos a medida que se apaga.
	float dash = texture(ruido, vec2(along * 0.37, 0.21 + semilla * 0.13)).r;
	float gaps = smoothstep(0.3 + 0.25 * vida, 0.38 + 0.25 * vida, dash);
	// El borde de la banda tiembla: el trazo engorda y adelgaza.
	float wobble = texture(ruido, vec2(along * 1.9, 0.63)).r;
	float across = abs(UV.y - 0.5) * 2.0;
	float body = 1.0 - smoothstep(0.35 + 0.5 * wobble, 0.95, across);
	ALBEDO = tinta.rgb;
	ALPHA = gaps * body * fuerza * (1.0 - vida * vida);
}
