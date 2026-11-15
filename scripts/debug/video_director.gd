extends Node
## Director del vídeo de los dioramas (F1-14). Encadena planos: carga cada
## diorama, mueve su propia cámara entre dos puntos y anima la hora, el miedo y
## la linterna. Se graba con el modo película de Godot (tools/video.sh); al
## terminar el último plano, cierra el juego.

const SHOTS: Array[Dictionary] = [
	{
		"scene": "res://scenes/style/diorama_deposito_limpio.tscn",
		"title": "El depósito",
		"seconds": 5.0,
		"from": [Vector3(1.7, 1.6, 1.5), Vector3(-0.6, 1.0, -1.0)],
		"to": [Vector3(0.95, 1.42, -0.2), Vector3(0.4, 0.95, -1.4)],
	},
	{
		"scene": "res://scenes/style/diorama_deposito_abandonado.tscn",
		"title": "El primer día",
		"seconds": 4.0,
		"from": [Vector3(1.75, 1.62, 1.5), Vector3(-0.7, 0.9, -0.9)],
		"to": [Vector3(1.35, 1.5, 0.95), Vector3(-1.0, 0.7, -0.6)],
	},
	{
		"scene": "res://scenes/style/diorama_patio_dia.tscn",
		"title": "Los Bloques, de día",
		"seconds": 5.0,
		"from": [Vector3(1.2, 1.65, 10.5), Vector3(-0.5, 4.6, -6.0)],
		"to": [Vector3(-1.2, 1.65, 7.6), Vector3(1.0, 4.0, -6.0)],
	},
	{
		"scene": "res://scenes/style/diorama_patio_dia.tscn",
		"title": "Cae la tarde",
		"seconds": 6.0,
		"from": [Vector3(3.0, 1.7, 9.0), Vector3(14.0, 8.0, -40.0)],
		"to": [Vector3(3.0, 1.7, 9.0), Vector3(40.0, 13.0, -70.0)],
		"hour": [15.0, 20.5],
	},
	{
		"scene": "res://scenes/style/diorama_patio_noche.tscn",
		"title": "De noche, con linterna",
		"seconds": 5.0,
		"from": [Vector3(2.0, 1.65, 6.0), Vector3(-6.0, 0.8, -1.0)],
		"to": [Vector3(2.4, 1.65, 5.4), Vector3(6.0, 1.2, -5.0)],
		"flashlight": true,
	},
	{
		"scene": "res://scenes/style/diorama_patio_ventisca.tscn",
		"title": "Ventisca",
		"seconds": 4.0,
		"from": [Vector3(5.6, 1.5, 3.2), Vector3(-1.5, 2.2, -8.0)],
		"to": [Vector3(4.8, 1.5, 2.4), Vector3(-2.5, 2.0, -8.0)],
	},
	{
		"scene": "res://scenes/style/diorama_patio_anochecer.tscn",
		"title": "El miedo",
		"seconds": 4.0,
		"from": [Vector3(1.2, 1.65, 8.5), Vector3(-0.5, 3.0, -6.0)],
		"to": [Vector3(1.0, 1.6, 8.0), Vector3(-0.5, 2.8, -6.0)],
		"fear": [0.0, 1.0],
	},
]
const FADE: float = 0.35

var _index: int = -1
var _time: float = 0.0
var _scene: Node
var _camera: Camera3D
var _curtain: ColorRect
var _title: Label


func _ready() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	_curtain = ColorRect.new()
	_curtain.color = Color(0.06, 0.05, 0.06, 1.0)
	_curtain.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_curtain)
	_title = UiFonts.make_label("", &"rotulo", 34, Color("#f2e6cf"))
	_title.position = Vector2(48, 36)
	_title.add_theme_color_override("font_outline_color", Color("#1b1a22"))
	_title.add_theme_constant_override("outline_size", 8)
	layer.add_child(_title)
	_next_shot()


func _process(delta: float) -> void:
	_time += delta
	var shot: Dictionary = SHOTS[_index]
	var duration: float = shot["seconds"]
	if _time >= duration:
		_next_shot()
		return
	var t: float = smoothstep(0.0, 1.0, _time / duration)
	var from: Array = shot["from"]
	var to: Array = shot["to"]
	_camera.position = (from[0] as Vector3).lerp(to[0], t)
	_camera.look_at((from[1] as Vector3).lerp(to[1], t))
	if shot.has("fear"):
		StyleDirector.fear = lerpf(shot["fear"][0], shot["fear"][1], t)
	if shot.has("hour") and Engine.get_process_frames() % 2 == 0:
		_scene.call(&"set_hour", lerpf(shot["hour"][0], shot["hour"][1], t))
	var edge: float = minf(_time, duration - _time)
	_curtain.color.a = clampf(1.0 - edge / FADE, 0.0, 1.0)


func _next_shot() -> void:
	_index += 1
	if _index >= SHOTS.size():
		get_tree().quit()
		return
	if _scene != null:
		_scene.free()
	StyleDirector.fear = 0.0
	var shot: Dictionary = SHOTS[_index]
	_scene = load(shot["scene"]).instantiate()
	add_child(_scene)
	_camera = Camera3D.new()
	_camera.fov = 60.0
	_scene.add_child(_camera)
	_camera.make_current()
	if shot.get("flashlight", false):
		Flashlight.attach(_camera)
	if shot.has("hour"):
		_scene.call(&"set_hour", shot["hour"][0])
	_title.text = shot["title"]
	_time = 0.0
	_curtain.color.a = 1.0
