extends CanvasLayer
## Cambios de escena con transición.
##
## De momento la transición es un fundido a papel. En la Fase 1 pasará a ser un
## fundido "dibujado". En cooperativo, el anfitrión decide el cambio y todos los
## jugadores lo siguen.

signal scene_changed(path: String)

const FADE_TIME: float = 0.35
const PAPER_COLOR: Color = Color("#F2E6CF")

var _cover: ColorRect
var _busy: bool = false


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	_cover = ColorRect.new()
	_cover.color = PAPER_COLOR
	_cover.modulate.a = 0.0
	_cover.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cover.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_cover)


## Cambia de escena. En cooperativo, solo el anfitrión puede pedirlo.
func go_to(path: String) -> void:
	if not multiplayer.is_server():
		push_warning("Solo el anfitrión cambia de escena.")
		return
	_go_to_everywhere.rpc(path)


@rpc("authority", "call_local", "reliable")
func _go_to_everywhere(path: String) -> void:
	if _busy:
		return
	_busy = true
	await _fade_to(1.0)
	var err: Error = get_tree().change_scene_to_file(path)
	if err != OK:
		push_error("No se pudo cargar la escena %s (%s)." % [path, error_string(err)])
	await get_tree().process_frame
	await _fade_to(0.0)
	_busy = false
	scene_changed.emit(path)


func _fade_to(alpha: float) -> void:
	var tween: Tween = create_tween()
	tween.tween_property(_cover, "modulate:a", alpha, FADE_TIME)
	await tween.finished
