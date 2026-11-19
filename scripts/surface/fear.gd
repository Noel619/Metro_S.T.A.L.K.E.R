class_name Fear
extends Node
## El miedo (F3-11, docs/SUPERFICIE.md 8): no tiene barra. Sube al ver perros cerca,
## al sentirse perseguido, al oírlos, al ser mordido, a oscuras y con poca sangre, y
## baja despacio cuando se está a salvo. Se nota en las manos y en lo que llevan
## (tiembla lo que se lleva y la linterna), en la vista al recibir un golpe y en el
## dibujo: el trazo vibra más y el tramado invade los bordes ([member StyleDirector.fear]).
##
## Es de cada equipo: lo calcula el de cada jugador con lo que ese jugador ve.

const TICK: float = 0.1
## Lo que sube y lo que baja por segundo.
const RISE: float = 1.4
const FALL: float = 0.07
## Los perros: a menos de esto, a la vista, dan miedo (más cuanto más cerca).
const DOG_SIGHT: float = 35.0
## Oírlos (a menos de esto, aunque no se vean).
const DOG_HEARING: float = 60.0
## Un golpe: lo que sube de golpe y lo que tiembla la vista.
const HURT_SPIKE: float = 0.6
const HURT_SHAKE: float = 0.06
const HURT_SHAKE_SECONDS: float = 0.45
## Las manos: lo que tiemblan con el miedo entero (metros).
const HANDS_TREMBLE: float = 0.012
## La linterna: lo que se mueve el haz con el miedo entero (radianes).
const TORCH_WOBBLE: float = 0.05

## De 0 a 1.
var level: float = 0.0
## Lo que se quiere ahora (para la depuración).
var wanted: float = 0.0

var _player: Player
var _clock: float = 0.0
var _spike: float = 0.0
var _shake: float = 0.0


func setup(player: Player) -> void:
	_player = player
	name = "Miedo"
	player.condition.hurt.connect(_on_hurt)


func _exit_tree() -> void:
	StyleDirector.fear = 0.0


func _process(delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		return
	_clock -= delta
	if _clock <= 0.0:
		_clock = TICK
		wanted = _measure()
	_spike = maxf(0.0, _spike - delta * 0.15)
	var target: float = clampf(maxf(wanted, _spike), 0.0, 1.0)
	level = move_toward(level, target, delta * (RISE if target > level else FALL))
	StyleDirector.fear = level
	_player.tremble = HANDS_TREMBLE * level * level
	_shake_view(delta)


func _measure() -> float:
	var fear: float = 0.0
	var eye: Vector3 = _player.eye_position()
	var looking: Vector3 = _player.look_direction()
	var space: PhysicsDirectSpaceState3D = _player.get_world_3d().direct_space_state
	for node: Node in get_tree().get_nodes_in_group(Dog.GROUP):
		var dog: Dog = node as Dog
		var to: Vector3 = dog.global_position + Vector3.UP * 0.6 - eye
		var distance: float = to.length()
		if distance > DOG_HEARING:
			continue
		var heard: float = 0.15 if dog.gait != Dog.Gait.STILL or dog.pose == &"grunir" else 0.08
		fear = maxf(fear, heard)
		if distance > DOG_SIGHT or looking.dot(to.normalized()) < 0.2:
			continue
		if Visibility.blocked(space, eye, eye + to, [_player.get_rid()]):
			continue
		var near: float = 1.0 - distance / DOG_SIGHT
		var threat: float = 0.35 + 0.5 * near
		if dog.gait == Dog.Gait.GALLOP or dog.pose == &"grunir" or dog.pose == &"morder":
			threat += 0.3
		fear = maxf(fear, threat)
	var light: float = Visibility.ambient(GameState.hour())
	if light < 0.3 and not _player.flashlight_on:
		fear = maxf(fear, 0.25)
	fear = maxf(fear, (1.0 - _player.condition.blood) * 0.7)
	return clampf(fear, 0.0, 1.0)


func _on_hurt(_from: Vector3) -> void:
	_spike = minf(1.0, maxf(_spike, level) + HURT_SPIKE)
	_shake = HURT_SHAKE_SECONDS


func _shake_view(delta: float) -> void:
	var camera: Camera3D = get_viewport().get_camera_3d()
	if camera == null:
		return
	var torch: SpotLight3D = camera.get_node_or_null(NodePath(Flashlight.NODE_NAME)) as SpotLight3D
	var t: float = Time.get_ticks_msec() / 1000.0
	if torch != null:
		var wobble: float = TORCH_WOBBLE * level * level
		torch.rotation = Vector3(sin(t * 17.0) * wobble, sin(t * 13.0 + 0.7) * wobble, 0.0)
	_shake = maxf(0.0, _shake - delta)
	var amount: float = HURT_SHAKE * _shake / HURT_SHAKE_SECONDS
	camera.h_offset = sin(t * 61.0) * amount
	camera.v_offset = sin(t * 47.0 + 1.1) * amount
