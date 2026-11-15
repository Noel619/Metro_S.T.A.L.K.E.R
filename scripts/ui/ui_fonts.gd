class_name UiFonts
extends RefCounted
## Las tipografías del juego (F1-13). Todas con licencia OFL y con alfabeto
## latino completo (español) y cirílico. Ver docs/ESTILO.md.
##
## - manuscrita: Caveat. Tu letra: el cuaderno, las etiquetas, las notas.
## - maquina: PT Mono. Lo escrito a máquina: recibos, impresos, la administración.
## - rotulo: Oswald. Rótulos y carteles soviéticos, sellos, cabeceras.
## - texto: PT Sans. Textos largos y opciones (la radio de los ajustes).

const PATHS: Dictionary = {
	&"manuscrita": "res://assets/fonts/caveat/Caveat-Regular.ttf",
	&"manuscrita_negrita": "res://assets/fonts/caveat/Caveat-Bold.ttf",
	&"maquina": "res://assets/fonts/pt_mono/PTMono-Regular.ttf",
	&"rotulo": "res://assets/fonts/oswald/Oswald-SemiBold.ttf",
	&"rotulo_fino": "res://assets/fonts/oswald/Oswald-Regular.ttf",
	&"texto": "res://assets/fonts/pt_sans/PTSans-Regular.ttf",
	&"texto_negrita": "res://assets/fonts/pt_sans/PTSans-Bold.ttf",
	&"texto_cursiva": "res://assets/fonts/pt_sans/PTSans-Italic.ttf",
}

static var _cache: Dictionary = {}


static func get_font(key: StringName) -> Font:
	if not _cache.has(key):
		_cache[key] = load(PATHS.get(key, PATHS[&"texto"]))
	return _cache[key]


## Rótulo listo para colocar: texto, tipo de letra, tamaño y color.
static func make_label(text: String, key: StringName, size: int, color: Color) -> Label:
	var label: Label = Label.new()
	label.text = text
	label.add_theme_font_override("font", get_font(key))
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label
