class_name PlayerOptics
extends Node
## Lo que se mira (F3-05, docs/SUPERFICIE.md 4.2), en el equipo de quien lo controla:
## - El reloj de pulsera: con R se levanta la muñeca y se leen las agujas (la hora de
##   la partida).
## - Los prismáticos: con ellos en la mano, el botón derecho los lleva a los ojos:
##   mucho aumento, el borde de las dos lentes y el ratón más lento.

const ZOOM_FOV: float = 11.0
const ZOOM_SPEED: float = 5.0
const WATCH_MODEL: String = "res://assets/models/reloj_pulsera.glb"
const MASK_SHADER: String = "res://assets/shaders/prismaticos.gdshader"
## Dónde se ve la muñeca levantada (en el marco de la cámara) y lo que tarda en subir.
const WATCH_UP: Vector3 = Vector3(-0.07, -0.085, -0.26)
const WATCH_DOWN: Vector3 = Vector3(-0.1, -0.32, -0.26)
const WATCH_SECONDS: float = 0.25

var player: Player
## De 0 a 1: los prismáticos en los ojos.
var zoom: float = 0.0

var _watch: Node3D
var _hour_hand: Node3D
var _minute_hand: Node3D
var _raised: float = 0.0
var _mask: CanvasLayer


func setup(owner_player: Player) -> void:
	player = owner_player
	name = "Mirar"


## Está mirando por los prismáticos (o empezando a hacerlo).
func looking_through() -> bool:
	return zoom > 0.05


## Lo que se frena el ratón con los prismáticos (el aumento).
func look_scale() -> float:
	var camera: Camera3D = get_viewport().get_camera_3d()
	return camera.fov / Player.FOV if camera != null else 1.0


func _process(delta: float) -> void:
	var camera: Camera3D = get_viewport().get_camera_3d()
	if camera == null or player == null:
		return
	var captured: bool = (
		Input.mouse_mode == Input.MOUSE_MODE_CAPTURED or DisplayServer.get_name() == "headless"
	)
	var held: Carryable = player.held_item()
	var binoculars: bool = held != null and held.state.data.tool == &"prismaticos"
	var wants_zoom: bool = binoculars and captured and Input.is_action_pressed(&"use_secondary")
	zoom = move_toward(zoom, 1.0 if wants_zoom else 0.0, delta * ZOOM_SPEED)
	camera.fov = lerpf(Player.FOV, ZOOM_FOV, smoothstep(0.0, 1.0, zoom))
	_show_mask(zoom > 0.6)
	if player.arms() != null:
		player.arms().visible = zoom < 0.6
	if held != null and held.visual() != null:
		held.visual().visible = zoom < 0.6
	var wants_watch: bool = captured and Input.is_action_pressed(&"watch") and zoom <= 0.0
	_raised = move_toward(_raised, 1.0 if wants_watch else 0.0, delta / WATCH_SECONDS)
	_update_watch(camera)


func _update_watch(camera: Camera3D) -> void:
	if _raised <= 0.0:
		if _watch != null:
			_watch.visible = false
		return
	if _watch == null:
		_watch = (load(WATCH_MODEL) as PackedScene).instantiate()
		_watch.name = "Reloj"
		camera.add_child(_watch)
		_hour_hand = _watch.find_child("aguja_horas", true, false) as Node3D
		_minute_hand = _watch.find_child("aguja_minutos", true, false) as Node3D
	_watch.visible = true
	var up: float = smoothstep(0.0, 1.0, _raised)
	_watch.position = WATCH_DOWN.lerp(WATCH_UP, up)
	# La esfera mira a la cámara, con el 12 hacia arriba y la muñeca hacia abajo a la izquierda.
	_watch.rotation = Vector3(deg_to_rad(68.0), deg_to_rad(-12.0), deg_to_rad(-20.0))
	var minutes: float = GameState.minute
	if _hour_hand != null:
		_hour_hand.rotation.y = -TAU * fmod(minutes / 60.0, 12.0) / 12.0
	if _minute_hand != null:
		_minute_hand.rotation.y = -TAU * fmod(minutes, 60.0) / 60.0


func _show_mask(shown: bool) -> void:
	if _mask == null:
		if not shown:
			return
		_mask = CanvasLayer.new()
		_mask.name = "Lentes"
		_mask.layer = 5
		var rect: ColorRect = ColorRect.new()
		rect.set_anchors_preset(Control.PRESET_FULL_RECT)
		rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var material: ShaderMaterial = ShaderMaterial.new()
		material.shader = load(MASK_SHADER)
		var size: Vector2 = get_viewport().get_visible_rect().size
		material.set_shader_parameter("aspect", size.x / maxf(size.y, 1.0))
		rect.material = material
		_mask.add_child(rect)
		add_child(_mask)
	_mask.visible = shown
