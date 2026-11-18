class_name Reticle
extends CanvasLayer
## El punto de mira: un punto de lápiz que se convierte en un pequeño icono
## dibujado cuando hay algo que se puede usar (README 10.2).

const DOT: String = "res://assets/ui/icono_punto.svg"
const DOT_SIZE: float = 14.0
const ICON_SIZE: float = 46.0

var _image: TextureRect
var _current: String = ""


func _ready() -> void:
	layer = 10
	_image = TextureRect.new()
	_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_image.set_anchors_preset(Control.PRESET_CENTER)
	add_child(_image)
	show_target(null)


## Muestra el icono de lo que se tiene delante, o el punto si no hay nada.
func show_target(target: Interactable) -> void:
	var path: String = target.icon_path() if target != null else DOT
	if path == _current:
		return
	_current = path
	var size: float = ICON_SIZE if target != null else DOT_SIZE
	_image.texture = load(path)
	_image.custom_minimum_size = Vector2(size, size)
	_image.size = Vector2(size, size)
	_image.position = -Vector2(size, size) / 2.0
	_image.modulate.a = 0.95 if target != null else 0.7
