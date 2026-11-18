class_name SignText
extends RefCounted
## Los rótulos pintados de la estación y del local (CONSIGNA, ADMINISTRACIÓN,
## AVISOS…): texto con la tipografía de los rótulos, sombreado como lo demás,
## sobre la tabla que trae el modelo. Miran hacia +Z.


## Un rótulo de [param height] metros de alto (la altura de las mayúsculas, más o menos).
static func make(
	text: String, height: float, color: Color, font: StringName = &"rotulo"
) -> Label3D:
	var label: Label3D = Label3D.new()
	label.text = text
	label.font = UiFonts.get_font(font)
	label.font_size = 96
	# Oswald: las mayúsculas miden unos 0,7 del cuerpo de la letra.
	label.pixel_size = height / (96.0 * 0.72)
	label.modulate = color
	label.outline_size = 0
	label.shaded = true
	label.double_sided = false
	label.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return label
