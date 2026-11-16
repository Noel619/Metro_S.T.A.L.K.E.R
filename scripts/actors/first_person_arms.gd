class_name FirstPersonArms
extends Node3D
## Las manos del jugador, vistas desde sus ojos.
##
## Cuelgan de la cámara. Casi siempre están bajas, fuera de la vista; suben
## cuando sujetan algo y salen un momento cuando tocan o cogen algo. Se mueven
## "a saltos", como el resto del dibujo.
##
## Al sujetar algo, [GripModifier] las coloca según el tamaño del objeto.

const MODELS: Dictionary = {
	"chico": "res://assets/models/manos_chico.glb",
	"chica": "res://assets/models/manos_chica.glb",
}
const BLEND_TIME: float = 0.18
const ANIMATION_FPS: float = 12.0

var holding: bool = false
## Coloca las manos alrededor de lo que se lleva.
var grip: GripModifier

var _player: AnimationPlayer
var _pending: float = 0.0
var _reaching: float = 0.0


func setup(variant: String) -> void:
	var model: Node3D = load(MODELS[variant]).instantiate()
	add_child(model)
	for mesh: Node in model.find_children("*", "MeshInstance3D", true, false):
		(mesh as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_player = model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	_player.play(&"reposo")
	_player.advance(0.0)
	grip = GripModifier.new()
	grip.name = "Agarre"
	grip.view = self
	(model.find_child("Skeleton3D", true, false) as Skeleton3D).add_child(grip)


## Empieza a sujetar un objeto (o lo suelta, con [code]null[/code]).
func hold(body: Node3D, weight: float = 0.0) -> void:
	holding = body != null
	if grip == null:
		return
	if body != null:
		grip.grip(body, weight)
	else:
		grip.release()


## La mano derecha sale a tocar o a coger algo.
func reach() -> void:
	if _player == null or holding:
		return
	_reaching = _player.get_animation(&"alcanzar").length
	_player.play(&"alcanzar", BLEND_TIME * 0.5)


func _process(delta: float) -> void:
	if _player == null:
		return
	if _reaching > 0.0:
		_reaching -= delta
	else:
		var animation: StringName = &"sostener" if holding else &"reposo"
		if _player.current_animation != animation:
			_player.play(animation, BLEND_TIME)
	_pending += delta
	if _pending >= 1.0 / ANIMATION_FPS:
		_player.advance(_pending)
		_pending = 0.0
