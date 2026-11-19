extends Node
## Visor del estilo: herramienta de desarrollo, no interfaz del juego.
##
## Flecha izquierda y derecha: cambia de diorama · C: cambia de cámara ·
## Flecha arriba y abajo: sube o baja el miedo · R: radiación sí/no · L: linterna ·
## F1: panel de depuración (hora, clima, miedo, radiación, estilo).

const SCENES: PackedStringArray = [
	"res://scenes/style/diorama_deposito_limpio.tscn",
	"res://scenes/style/diorama_deposito_abandonado.tscn",
	"res://scenes/style/diorama_patio_dia.tscn",
	"res://scenes/style/diorama_patio_anochecer.tscn",
	"res://scenes/style/diorama_patio_noche.tscn",
	"res://scenes/style/diorama_patio_ventisca.tscn",
	"res://scenes/style/diorama_equipo.tscn",
	"res://scenes/style/diorama_botin.tscn",
	"res://scenes/style/personajes_superficie.tscn",
	"res://scenes/style/personajes_deposito.tscn",
]
const DEBUG_PANEL: Script = preload("res://scripts/debug/debug_panel.gd")

const HELP: String = "← → diorama · C cámara · ↑ ↓ miedo · R radiación · L linterna · F1 panel"

var _index: int = 0
var _camera_index: int = 0
var _current: Node
var _label: Label
var _panel: CanvasLayer


func _ready() -> void:
	_panel = DEBUG_PANEL.new()
	_panel.name = "PanelDepuracion"
	add_child(_panel)
	var layer: CanvasLayer = CanvasLayer.new()
	add_child(layer)
	_label = Label.new()
	_label.position = Vector2(24, 16)
	_label.add_theme_color_override("font_color", Color("#f2e6cf"))
	_label.add_theme_color_override("font_outline_color", Color("#1b1a22"))
	_label.add_theme_constant_override("outline_size", 6)
	layer.add_child(_label)
	_load(0)


func _unhandled_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_RIGHT:
			_load(_index + 1)
		KEY_LEFT:
			_load(_index - 1)
		KEY_C:
			_activate_camera(_camera_index + 1)
		KEY_UP:
			StyleDirector.fear = minf(1.0, StyleDirector.fear + 0.1)
		KEY_DOWN:
			StyleDirector.fear = maxf(0.0, StyleDirector.fear - 0.1)
		KEY_R:
			StyleDirector.radiation = 0.0 if StyleDirector.radiation > 0.0 else 1.0
		KEY_L:
			var camera: Camera3D = get_viewport().get_camera_3d()
			if camera != null:
				Flashlight.toggle(camera)
	_panel.call(&"sync")
	_update_label()


func _load(index: int) -> void:
	_index = wrapi(index, 0, SCENES.size())
	if _current != null:
		_current.free()
	StyleDirector.fear = 0.0
	_current = load(SCENES[_index]).instantiate()
	add_child(_current)
	_activate_camera(0)
	_panel.call(&"set_target", _current)
	_update_label()


func _activate_camera(index: int) -> void:
	var cameras: Array[Node] = _current.find_children("*", "Camera3D", true, false)
	if cameras.is_empty():
		return
	_camera_index = wrapi(index, 0, cameras.size())
	(cameras[_camera_index] as Camera3D).make_current()


func _update_label() -> void:
	_label.text = (
		"%s · cámara %d · miedo %d%% · radiación %s\n%s"
		% [
			SCENES[_index].get_file().get_basename().trim_prefix("diorama_"),
			_camera_index + 1,
			roundi(StyleDirector.fear * 100.0),
			"sí" if StyleDirector.radiation > 0.0 else "no",
			HELP,
		]
	)
