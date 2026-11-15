extends Control
## Prueba de tipografías y de legibilidad (F1-13): cada familia, su uso y los
## tamaños en los que aparece en el juego, sobre papel, a 1080p.

const PAPER: Color = Color("#efe6d2")
const INK: Color = Color("#1b1a22")
const RED: Color = Color("#b4423a")
const SAMPLE: String = "El veloz murciélago hindú comía feliz cardillo y kiwi. ¿Qué? ¡Sí!"
const NUMBERS: String = "0123456789 · 35 ₽ · Nº 0417 · 18:10"
const CYRILLIC: String = "Съешь же ещё этих мягких французских булок"
const FAMILIES: Array = [
	[
		&"manuscrita",
		"Caveat · manuscrita",
		"Tu letra: el cuaderno, las notas, las etiquetas",
		[26, 34, 48]
	],
	[
		&"maquina",
		"PT Mono · a máquina",
		"Recibos, impresos y papeles de la administración",
		[18, 22, 30]
	],
	[
		&"rotulo",
		"Oswald · rótulos",
		"Carteles, sellos y cabeceras, al modo soviético",
		[20, 30, 48]
	],
	[
		&"texto",
		"PT Sans · texto",
		"Textos largos y opciones (la radio de los ajustes)",
		[16, 20, 28]
	],
]


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var paper: ColorRect = ColorRect.new()
	paper.color = PAPER
	paper.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(paper)
	var title: Label = UiFonts.make_label("TIPOGRAFÍAS DE TUMANSK", &"rotulo", 44, INK)
	title.position = Vector2(60, 28)
	add_child(title)
	var note: Label = UiFonts.make_label(
		"Prueba de legibilidad a 1080p · todas OFL, con español y cirílico", &"texto", 20, RED
	)
	note.position = Vector2(64, 88)
	add_child(note)
	var y: float = 140.0
	for family: Array in FAMILIES:
		y = _family(family, y)


func _family(family: Array, top: float) -> float:
	var key: StringName = family[0]
	var line: ColorRect = ColorRect.new()
	line.color = Color(INK, 0.25)
	line.position = Vector2(60, top)
	line.size = Vector2(1480, 2)
	add_child(line)
	var name_label: Label = UiFonts.make_label(family[1], &"texto_negrita", 22, INK)
	name_label.position = Vector2(60, top + 10)
	add_child(name_label)
	var usage: Label = UiFonts.make_label(family[2], &"texto_cursiva", 18, Color(INK, 0.75))
	usage.position = Vector2(60, top + 40)
	add_child(usage)
	var y: float = top + 8.0
	for size: int in family[3]:
		var sample: Label = UiFonts.make_label("%d px · %s" % [size, SAMPLE], key, size, INK)
		sample.position = Vector2(520, y)
		add_child(sample)
		y += size * 1.35
	var extra: Label = UiFonts.make_label(
		"%s · %s" % [NUMBERS, CYRILLIC], key, family[3][1], Color(INK, 0.8)
	)
	extra.position = Vector2(520, y)
	add_child(extra)
	return y + family[3][1] * 1.6 + 12.0
