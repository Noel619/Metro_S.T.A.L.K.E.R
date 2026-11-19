class_name Player
extends CharacterBody3D
## Un jugador en primera persona. En el depósito, tranquilo: se agacha y se asoma,
## pero no corre. En la superficie ([member surface_rules]) corre mientras tiene
## aliento, salta y se encarama, y cada paso suena según lo que pisa ([PlayerBody],
## [Footsteps], docs/SUPERFICIE.md).
##
## Cada jugador manda sobre su propio movimiento (no hay retraso al andar ni al
## mirar) y lo replica a los demás; el anfitrión manda sobre el mundo. Los demás
## lo ven como un [PlayerAvatar]; él solo ve sus manos ([FirstPersonArms]).
##
## Coger, girar, inspeccionar y soltar: "interactuar" coge lo que se tiene
## delante y lo vuelve a soltar; con el botón secundario pulsado, el objeto se
## acerca a los ojos y el ratón lo gira en vez de mover la mirada.
##
## Trabajar: con el botón principal pulsado sobre algo que acepta lo que se
## lleva (o las manos), el ratón deja de mover la mirada y su movimiento es el
## gesto (pasadas, frotes, círculos, tirar). Se mide aquí y se le pide al
## anfitrión que lo aplique ([Workable]).
##
## Lo que se lleva va delante del pecho, nunca dentro del cuerpo: al mirar
## abajo sube en la vista en vez de meterse en la tripa, y la mirada no baja más
## de lo que las manos pueden seguirlo. Tampoco se anda a través de ello: si
## choca con una pared, el jugador se para (o se desliza a lo largo de ella).

const GROUP: StringName = &"players"
const WALK_SPEED: float = 2.3
const ACCELERATION: float = 10.0
const GRAVITY: float = 9.8
const LOOK_LIMIT: float = 1.43
const REACH: float = 2.2
const PAD_LOOK_SPEED: float = 2.4
const INSPECT_TURN_SPEED: float = 0.012
## Kilos que reducen la velocidad a la mitad.
const HALF_SPEED_WEIGHT: float = 22.0
const EYE_HEIGHTS: Dictionary = {"chico": 1.57, "chica": 1.51}
## Campo de visión vertical de la cámara, en grados.
const FOV: float = 72.0
## Cómo se lleva algo pequeño: su centro, a esta distancia de los ojos y así de
## por debajo de la línea de la mirada. Lo ancho se lleva más lejos y lo alto,
## más bajo, para que quepa entre los brazos y no tape toda la vista.
const CARRY_DISTANCE: float = 0.56
const CARRY_DROP: float = 0.2
## Lo que se lleva con las dos manos va algo más alto: si no, la cara de
## delante taparía las manos.
const TWO_HANDS_LIFT: float = 0.05
## Hasta este medio ancho y este medio alto, un objeto no cambia cómo se lleva.
const FREE_HALF_WIDTH: float = 0.15
const FREE_HALF_HEIGHT: float = 0.12
const TALL_DROP: float = 0.75
## Lo pesado cuelga más bajo: tanto por kilo, hasta un máximo.
const HEAVY_DROP: float = 0.16
const HEAVY_DROP_PER_KG: float = 0.012
## Lo que se lleva con una mano va un poco hacia la derecha, en esa mano; y lo
## que se coloca a su altura es el agarre, no el centro (una escoba sobresale).
const ONE_HAND_SIDE: float = 0.06
## Al inspeccionar, más cerca de los ojos; pero lo bastante lejos para que, lo
## gire como lo gire, no llegue a la cara.
const INSPECT_DISTANCE: float = 0.42
const INSPECT_DROP: float = 0.04
const INSPECT_CLEARANCE: float = 0.14
## El pecho queda a este radio de los ojos (medido en horizontal) y lo que se
## lleva, siempre al menos a este hueco de él.
const TORSO_RADIUS: float = 0.16
const TORSO_GAP: float = 0.04
## Margen para que las manos no lleguen justo al borde de lo que alcanzan.
const HANDS_MARGIN: float = 0.03
## Lo que se deja entre lo que se lleva y una pared al acercarlo al pecho.
const CARRY_SKIN: float = 0.005
## Al mirar arriba, lo ligero sube con la mirada hasta este ángulo; lo de este
## peso o más, solo hasta el otro (después se queda abajo y sale de la vista).
const HIGHEST_LIGHT: float = 0.9
const HIGHEST_HEAVY: float = 0.1
const HEAVY_WEIGHT: float = 15.0
## Rapidez con la que sube la mirada si lo que se coge no deja mirar tan abajo.
const PITCH_RECOVERY: float = 2.5
const LAYER_PLAYERS: int = 1 << 1
## Lo que para al jugador: el mundo, los objetos y los perros.
const MASK_PLAYERS: int = (1 << 0) | (1 << 2) | (1 << 3)
const MASK_REACH: int = (1 << 0) | (1 << 2) | (1 << 4)
## Lo que para a lo que se lleva: el mundo y los demás jugadores.
const MASK_CARRY: int = (1 << 0) | (1 << 1)
const SYNCED: PackedStringArray = [
	".:position",
	".:rotation",
	".:head_pitch",
	".:move_speed",
	".:hold_rotation",
	".:inspecting",
	".:working",
	".:crouch",
	".:lean",
	".:flashlight_on",
	".:panting",
]
## Saltar: la velocidad hacia arriba (un saltito de medio metro).
const JUMP_SPEED: float = 3.1
## Píxeles de ratón que hacen una unidad de cada gesto: una pasada de escoba, un
## frote, un tirón de palanca. Los círculos se miden en vueltas y mantener, en
## segundos.
const STROKE_PIXELS: float = 260.0
const SCRUB_PIXELS: float = 110.0
const PULL_PIXELS: float = 160.0
const HOLD_SECONDS: float = 1.0
## Cada cuánto se manda al anfitrión lo trabajado.
const WORK_SEND_SECONDS: float = 0.1
## Margen sobre el alcance con el que el anfitrión acepta el trabajo.
const WORK_RANGE_SLACK: float = 0.6
## Lo que el gesto mueve la herramienta sobre lo que se trabaja, como mucho.
const WORK_SWAY: float = 0.16
const SWAY_PER_PIXEL: float = 0.0016
const SWAY_RETURN: float = 6.0
## Lo que mide una herramienta para trabajar girándola en las manos (la
## escoba); las cortas se acercan enteras a lo que se trabaja.
const LONG_TOOL: float = 0.6
## Lo que se puede ajustar con la rueda mientras se lleva (el precio de una
## etiqueta, los billetes de un fajo).
const ADJUSTABLE: Array[StringName] = [&"etiqueta", &"billetes", &"tiza"]
## Con hambre se anda más despacio y tiembla lo que se lleva.
const HUNGRY_SPEED: float = 0.8
const HUNGRY_TREMBLE: float = 0.006

var peer_id: int = 1
var variant: String = "chico"
var slot: int = 0
## Inclinación de la mirada, en radianes (positivo: hacia arriba).
var head_pitch: float = 0.0
## Velocidad a la que anda ahora mismo.
var move_speed: float = 0.0
## Giro del objeto que lleva, respecto a su cuerpo.
var hold_rotation: Quaternion = Quaternion.IDENTITY
## Tiene el objeto cerca de los ojos y lo está girando.
var inspecting: bool = false
## Está trabajando algo con el botón principal.
var working: bool = false
## Para pruebas y bots: sustituye a las teclas de movimiento.
var scripted_input: Vector2 = Vector2.ZERO
## Para pruebas y bots: correr (sustituye a la tecla).
var scripted_run: bool = false
## Las reglas de la superficie: correr con aliento, saltar y encaramarse.
var surface_rules: bool = false:
	set(value):
		surface_rules = value
		if body != null:
			body.can_run = value
## De 0 (de pie) a 1 (agachado); lo replica quien lo controla.
var crouch: float = 0.0
## De -1 (asomado a la izquierda) a 1 (a la derecha), ya contando con las paredes.
var lean: float = 0.0
## Lleva la linterna encendida.
var flashlight_on: bool = false
## Se ha quedado sin aliento: jadea.
var panting: bool = false
## Postura y aliento (solo cuenta en el equipo de quien lo controla).
var body: PlayerBody
## Sus pasos (en todos los equipos).
var footsteps: Footsteps
## Cómo está: si sangra, si ha muerto (lo decide el anfitrión; F3-12).
var condition: PlayerCondition
## Su mochila y su cinturón (F3-03).
var pack: PlayerPack
## Su cuaderno (F3-04).
var notebook: PlayerNotebook
## El reloj de pulsera y los prismáticos (F3-05; solo en su equipo).
var optics: PlayerOptics
## Lo que tiemblan las manos por el miedo (metros; lo pone [Fear], en su equipo).
var tremble: float = 0.0
## Lo cargado para lanzar (de 0 a 1): lo que se lleva se echa atrás.
var throw_charge: float = 0.0

var _head: Node3D
var _camera: Camera3D
var _capsule: CapsuleShape3D
var _shape: CollisionShape3D
var _moves: PlayerMoves = PlayerMoves.new()
## La linterna que ven los demás (en el jugador de los otros equipos).
var _torch: SpotLight3D
var _jump_queued: bool = false
var _backpack_view: BackpackView
var _throw: PlayerThrow = PlayerThrow.new()
var _chalk: PlayerChalk = PlayerChalk.new()
var _avatar: PlayerAvatar
var _arms: FirstPersonArms
var _reticle: Reticle
var _held: Carryable
var _focus: Interactable
## Cuánto del recorrido entre el pecho y el sitio de lo que lleva está libre
## (la última vez que se miró si había una pared delante).
var _reach_share: float = 1.0
## Lo que se trabaja ahora (o se trabajaría al pulsar), dónde y de cara a dónde.
var _work_target: Workable
var _work_point: Vector3 = Vector3.ZERO
var _work_normal: Vector3 = Vector3.UP
## Trabajo medido y aún no enviado al anfitrión.
var _work_pending: float = 0.0
var _work_clock: float = 0.0
var _last_motion: Vector2 = Vector2.ZERO
## Lo que el gesto ha desplazado la herramienta (en píxeles de pantalla, con tope).
var _sway: Vector2 = Vector2.ZERO


## El jugador de un peer, si está en la escena.
static func find(tree: SceneTree, peer: int) -> Player:
	if peer == 0:
		return null
	for node: Node in tree.get_nodes_in_group(GROUP):
		if (node as Player).peer_id == peer:
			return node as Player
	return null


## Monta el jugador. Se llama igual en todos los equipos, antes de entrar en escena.
func setup(new_peer: int, new_variant: String, new_slot: int) -> void:
	peer_id = new_peer
	variant = new_variant if EYE_HEIGHTS.has(new_variant) else "chico"
	slot = new_slot
	name = "jugador_%d" % peer_id
	add_to_group(GROUP)
	# Antes que los objetos: lo que llevan sigue a donde ya está el jugador.
	process_priority = -1
	process_physics_priority = -1
	collision_layer = LAYER_PLAYERS
	collision_mask = MASK_PLAYERS
	body = PlayerBody.new()
	body.can_run = surface_rules
	_capsule = CapsuleShape3D.new()
	_capsule.radius = 0.27
	_capsule.height = PlayerBody.STAND_HEIGHT
	_shape = CollisionShape3D.new()
	_shape.name = "Cuerpo"
	_shape.shape = _capsule
	_shape.position.y = PlayerBody.STAND_HEIGHT * 0.5
	add_child(_shape)
	footsteps = Footsteps.new()
	footsteps.setup(self)
	add_child(footsteps)
	condition = PlayerCondition.new()
	condition.name = "Estado"
	add_child(condition)
	pack = PlayerPack.new()
	pack.setup(self)
	notebook = PlayerNotebook.new()
	notebook.setup(self)
	add_child(pack)
	add_child(notebook)
	pack.changed.connect(func() -> void: footsteps.loose_items = pack.contents().loose_items())
	_head = Node3D.new()
	_head.name = "Cabeza"
	_head.position.y = EYE_HEIGHTS[variant]
	add_child(_head)
	_avatar = PlayerAvatar.new()
	_avatar.name = "Avatar"
	_avatar.variant = variant
	_avatar.player_slot = slot
	add_child(_avatar)
	var sync: MultiplayerSynchronizer = MultiplayerSynchronizer.new()
	sync.name = "Sincronizador"
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	for property: String in SYNCED:
		config.add_property(NodePath(property))
		config.property_set_spawn(NodePath(property), true)
		config.property_set_replication_mode(
			NodePath(property), SceneReplicationConfig.REPLICATION_MODE_ALWAYS
		)
	sync.replication_config = config
	add_child(sync)
	set_multiplayer_authority(peer_id)


func _ready() -> void:
	if not is_local():
		_torch = SpotLight3D.new()
		_torch.name = "Linterna"
		_torch.position = Vector3(0.22, -0.18, 0.0)
		_torch.light_color = Color(1.0, 0.93, 0.8)
		_torch.light_energy = 7.0
		_torch.spot_range = 30.0
		_torch.spot_angle = 24.0
		_torch.spot_angle_attenuation = 1.6
		_torch.visible = false
		_head.add_child(_torch)
		return
	_avatar.shadow_only = true
	_camera = Camera3D.new()
	_camera.name = "Camara"
	_camera.fov = FOV
	_camera.near = 0.04
	_head.add_child(_camera)
	_camera.make_current()
	_arms = FirstPersonArms.new()
	_arms.name = "Manos"
	_camera.add_child(_arms)
	_arms.setup(variant)
	_reticle = Reticle.new()
	_reticle.name = "PuntoDeMira"
	add_child(_reticle)
	optics = PlayerOptics.new()
	optics.setup(self)
	add_child(optics)
	if DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _exit_tree() -> void:
	if _focus != null and is_instance_valid(_focus):
		_focus.set_focused(false)
	if is_local() and DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _unhandled_input(event: InputEvent) -> void:
	if not is_local() or CloseUp.is_open() or LockpickView.is_open() or NotebookView.is_open():
		return
	var wheel: InputEventMouseButton = event as InputEventMouseButton
	if wheel != null and wheel.pressed and _held != null:
		var step: int = 0
		if wheel.button_index == MOUSE_BUTTON_WHEEL_UP:
			step = 1
		elif wheel.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			step = -1
		if step != 0 and ADJUSTABLE.has(_held.state.data.tool):
			request_adjust.rpc_id(Carryable.HOST_PEER, step)
			get_viewport().set_input_as_handled()
			return
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		if working:
			feed_gesture(motion.relative)
		elif inspecting:
			turn_held(motion.relative * INSPECT_TURN_SPEED)
		else:
			var sensitivity: float = deg_to_rad(Settings.mouse_sensitivity)
			if optics != null:
				sensitivity *= optics.look_scale()
			look(-motion.relative.x * sensitivity, -motion.relative.y * sensitivity)
	elif event.is_action_pressed(&"interact"):
		interact()
	elif event.is_action_pressed(&"crouch"):
		body.crouch_wanted = not body.crouch_wanted
	elif event.is_action_pressed(&"flashlight"):
		flashlight_on = not flashlight_on
	elif event.is_action_pressed(&"jump") and surface_rules:
		_jump_queued = true
	elif event.is_action_pressed(&"backpack"):
		_use_backpack()
	elif event.is_action_pressed(&"notebook"):
		notebook.toggle(_camera)
	elif event.is_action_pressed(&"pause") and DisplayServer.get_name() != "headless":
		var captured: bool = Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if captured else Input.MOUSE_MODE_CAPTURED
	else:
		for slot: int in Backpack.BELT_SLOTS:
			if event.is_action_pressed(StringName("belt_%d" % (slot + 1))):
				pack.belt_key(slot)


func _process(delta: float) -> void:
	if is_local():
		var reading: bool = CloseUp.is_open() or NotebookView.is_open()
		var looking: bool = optics != null and optics.looking_through()
		inspecting = (
			_held != null
			and not reading
			and not looking
			and _held.state.data.tool != &"prismaticos"
			and Input.is_action_pressed(&"use_secondary")
		)
		var pressing: bool = (
			Input.is_action_pressed(&"use_primary")
			and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
			and not reading
		)
		_update_work(delta, pressing)
		_chalk.update(self, delta, pressing and _backpack_view == null)
		_throw.update(self, delta, pressing and _backpack_view == null and not _chalk.aiming)
		var pad: Vector2 = Input.get_vector(&"look_left", &"look_right", &"look_up", &"look_down")
		if pad != Vector2.ZERO:
			look(-pad.x * PAD_LOOK_SPEED * delta, -pad.y * PAD_LOOK_SPEED * delta)
		# Lo que se acaba de coger no deja mirar tan abajo: la mirada sube sola.
		var lowest: float = lowest_pitch()
		if head_pitch < lowest:
			head_pitch = move_toward(head_pitch, lowest, PITCH_RECOVERY * delta)
	_head.rotation.x = head_pitch
	_head.position = Vector3(
		lean * PlayerBody.LEAN_DISTANCE,
		EYE_HEIGHTS[variant] * lerpf(1.0, PlayerBody.CROUCH_EYES, crouch),
		0.0
	)
	_capsule.height = lerpf(PlayerBody.STAND_HEIGHT, PlayerBody.CROUCH_HEIGHT, crouch)
	_shape.position.y = _capsule.height * 0.5
	if _camera != null:
		_camera.rotation.z = -lean * PlayerBody.LEAN_ROLL
		Flashlight.attach(_camera).visible = flashlight_on
	elif _torch != null:
		_torch.visible = flashlight_on
	_avatar.speed = move_speed
	_avatar.look_pitch = head_pitch
	_avatar.carrying = _held != null
	_avatar.crouch = crouch
	_avatar.lean = lean


func _physics_process(delta: float) -> void:
	if not is_local():
		return
	if _moves.mantling():
		_moves.step_mantle(self, delta)
		return
	var input: Vector2 = scripted_input
	var keys: bool = (
		Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
		and not CloseUp.is_open()
		and not LockpickView.is_open()
		and not NotebookView.is_open()
		and not pack.is_busy()
	)
	body.forced_crouch = pack.is_busy() or _backpack_view != null
	if pack.is_busy() or _backpack_view != null:
		input = Vector2.ZERO
	if input == Vector2.ZERO and keys:
		input = Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")
	# En una escalera o una cuerda se trepa (saltar es soltarse).
	var letting_go: bool = _jump_queued and _moves.climbing()
	_jump_queued = _jump_queued and not letting_go
	if _moves.step_climb(self, input, letting_go, _capsule.radius, delta):
		return
	var lean_input: float = 0.0
	if keys:
		lean_input = Input.get_axis(&"lean_left", &"lean_right")
	var wants_run: bool = scripted_run or (keys and Input.is_action_pressed(&"sprint"))
	body.update(
		delta,
		wants_run and input.y < -0.3,
		input != Vector2.ZERO,
		carried_weight(),
		lean_input,
		PlayerMoves.can_stand(self, _capsule.height)
	)
	crouch = body.crouch
	lean = PlayerMoves.free_lean(self, body.lean)
	panting = body.is_panting()
	var wish: Vector3 = (basis * Vector3(input.x, 0.0, input.y)).limit_length(1.0)
	var target: Vector3 = wish * body.target_speed() * carry_slowdown() * hunger_slowdown()
	var planar: Vector3 = Vector3(velocity.x, 0.0, velocity.z).move_toward(
		target, ACCELERATION * delta
	)
	planar = _stopped_by_held(planar, delta)
	var vertical: float = velocity.y - GRAVITY * delta if not is_on_floor() else 0.0
	if _jump_queued:
		_jump_queued = false
		if is_on_floor() and not _moves.try_mantle(self, _capsule.radius):
			vertical = JUMP_SPEED
		if _moves.mantling():
			return
	velocity = Vector3(planar.x, vertical, planar.z)
	move_and_slide()
	move_speed = Vector2(velocity.x, velocity.z).length()
	_push_objects()
	_update_focus()
	_update_work_target()


func is_local() -> bool:
	return is_multiplayer_authority()


## Gira la mirada: [param yaw] a los lados y [param pitch] arriba o abajo, en radianes.
func look(yaw: float, pitch: float) -> void:
	rotate_y(yaw)
	var inverted: float = -1.0 if Settings.invert_y else 1.0
	# Si ya está por debajo de lo permitido (acaba de coger algo), no baja más.
	var lowest: float = minf(lowest_pitch(), head_pitch)
	head_pitch = clampf(head_pitch + pitch * inverted, lowest, LOOK_LIMIT)


## Gira lo que lleva tal como se ve: [param amount].x de lado y [param amount].y
## de arriba abajo, en radianes. Los ejes son los de la cámara, así que tirar del
## ratón hacia un lado siempre lleva hacia allí la cara que se tiene delante.
func turn_held(amount: Vector2) -> void:
	var up: Vector3 = Basis(Vector3.RIGHT, head_pitch) * Vector3.UP
	var spin: Quaternion = Quaternion(up, amount.x) * Quaternion(Vector3.RIGHT, amount.y)
	hold_rotation = (spin * hold_rotation).normalized()


## Usa lo que tiene delante, o suelta lo que lleva.
func interact() -> void:
	if _held != null:
		_held.request_drop.rpc_id(Carryable.HOST_PEER)
	elif _focus != null:
		if _arms != null:
			_arms.reach()
		_focus.interact(self)


func eye_position() -> Vector3:
	return _head.global_position


func can_carry() -> bool:
	return _held == null


## Con qué trabaja ahora: la herramienta que lleva o las manos.
func current_tool() -> StringName:
	if _held == null:
		return Workable.HANDS
	return _held.state.data.tool


## Lo que trabajaría ahora con el botón principal (o null).
func work_target() -> Workable:
	return _work_target


## Convierte el movimiento del ratón en trabajo, según el gesto de lo que se
## trabaja, y mueve la herramienta sobre ello.
func feed_gesture(relative: Vector2) -> void:
	if _work_target == null:
		return
	var amount: float = 0.0
	match _work_target.gesture:
		Workable.Gesture.STROKE:
			amount = relative.length() / STROKE_PIXELS
		Workable.Gesture.SCRUB:
			amount = relative.length() / SCRUB_PIXELS
		Workable.Gesture.PULL:
			amount = maxf(relative.y, 0.0) / PULL_PIXELS
		Workable.Gesture.CIRCLE:
			# Lo que gira la dirección del ratón, en vueltas: en pantalla la Y va
			# hacia abajo, así que un ángulo positivo es el sentido del reloj.
			if _last_motion.length() > 0.5 and relative.length() > 0.5:
				amount = _last_motion.angle_to(relative) / TAU
	if relative.length() > 0.5:
		_last_motion = relative
	_sway = (_sway + relative).limit_length(WORK_SWAY / SWAY_PER_PIXEL)
	_work_pending += amount


## Pide al anfitrión que aplique [param amount] de trabajo sobre [param target]
## (en [param point]) con lo que se lleva. Sirve también a los tests y a los bots.
func apply_work(target: Workable, amount: float, point: Vector3 = Vector3.INF) -> void:
	if target == null or amount == 0.0:
		return
	var body: Node = target.get_parent()
	var where: Vector3 = point
	if where == Vector3.INF and body is Node3D:
		where = (body as Node3D).global_position
	request_work.rpc_id(Carryable.HOST_PEER, body.get_path(), current_tool(), amount, where)


## Un jugador trabaja algo. Decide el anfitrión: que sea él, que lo alcance y que
## lleve lo que dice llevar.
@rpc("any_peer", "call_local", "reliable")
func request_work(path: NodePath, tool: StringName, amount: float, point: Vector3) -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	if sender != peer_id or tool != current_tool():
		return
	if eye_position().distance_to(point) > REACH + WORK_RANGE_SLACK:
		return
	var workable: Workable = Workable.find(get_node_or_null(path), tool)
	if workable != null:
		workable.work(self, tool, amount, point)


## Pide al anfitrión que cambie con la rueda lo que lleva (el precio de una
## etiqueta, los billetes de un fajo): [param step] es +1 o -1.
@rpc("any_peer", "call_local", "reliable")
func request_adjust(step: int) -> void:
	if not multiplayer.is_server() or _held == null:
		return
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	if sender == peer_id:
		EventBus.item_adjusted.emit(self, _held, signi(step))


## El anfitrión lleva a este jugador a otro sitio (al despertar, al catre).
@rpc("any_peer", "call_local", "reliable")
func move_to(where: Vector3, yaw: float) -> void:
	var sender: int = multiplayer.get_remote_sender_id()
	if sender != 0 and sender != Carryable.HOST_PEER:
		return
	if not is_local():
		return
	global_position = where
	rotation.y = yaw
	head_pitch = 0.0
	velocity = Vector3.ZERO


## Lo que frena el hambre: de 1 (nada) a [constant HUNGRY_SPEED].
func hunger_slowdown() -> float:
	return HUNGRY_SPEED if GameState.hungry_days >= GameState.HUNGRY_SHAKE else 1.0


## Los kilos que lleva encima: lo de las manos, la mochila y el cinturón.
func carried_weight() -> float:
	var hands: float = _held.state.data.weight if _held != null else 0.0
	return hands + (pack.weight() if pack != null else 0.0)


## I: con algo en la mano, se guarda; si no, se abre la mochila (en la superficie,
## arrodillándose primero).
func _use_backpack() -> void:
	if _backpack_view != null:
		return
	if _held != null:
		pack.store_held()
		return
	if pack.is_busy() or _camera == null:
		return
	var seconds: float = PlayerPack.OPEN_SECONDS if surface_rules else 0.0
	if seconds <= 0.0:
		_open_backpack()
	else:
		pack.after_kneeling(seconds, _open_backpack)


func _open_backpack() -> void:
	_backpack_view = BackpackView.new()
	_backpack_view.open(pack, _camera)
	_backpack_view.closed.connect(func() -> void: _backpack_view = null)


## Está trepando por una escalera o una cuerda.
func is_climbing() -> bool:
	return _moves.climbing()


## Lo alto que es ahora (agachado, menos).
func body_height() -> float:
	return lerpf(PlayerBody.STAND_HEIGHT, PlayerBody.CROUCH_HEIGHT, crouch)


## Hacia dónde mira (de largo 1), con la inclinación de la cabeza.
func look_direction() -> Vector3:
	return -_head.global_basis.z.normalized()


## Dónde se dibuja [param item] mientras se trabaja con él: lo largo (la escoba)
## gira en las manos hasta apoyar la punta en lo que se trabaja; lo corto se
## acerca entero. El gesto lo mueve un poco sobre la superficie.
func work_pose(item: Carryable) -> Transform3D:
	var hold: Transform3D = carry_target(item, false)
	if not working or _work_target == null:
		return hold
	var data: ItemData = item.state.data
	var bounds: AABB = item.bounds()
	var tip_local: Vector3 = data.tip if data.tip != Vector3.ZERO else bounds.get_center()
	var right: Vector3 = _camera.global_basis.x if _camera != null else global_basis.x
	var up: Vector3 = _camera.global_basis.y if _camera != null else Vector3.UP
	var offset: Vector3 = (right * _sway.x - up * _sway.y) * SWAY_PER_PIXEL
	offset -= _work_normal * offset.dot(_work_normal)
	var aim: Vector3 = _work_point + _work_normal * 0.01 + offset
	var tip: Vector3 = hold * tip_local
	if bounds.size[bounds.get_longest_axis_index()] < LONG_TOOL:
		var reach: Vector3 = (aim - tip).limit_length(0.5)
		return Transform3D(hold.basis, hold.origin + reach)
	var grip: Vector3 = hold * bounds.get_center()
	var from: Vector3 = (tip - grip).normalized()
	var to: Vector3 = (aim - grip).normalized()
	if from.cross(to).length() < 0.0001:
		return hold
	var turn: Basis = Basis(from.cross(to).normalized(), from.angle_to(to))
	var basis: Basis = turn * hold.basis
	return Transform3D(basis, grip + turn * (hold.origin - grip))


func held_item() -> Carryable:
	return _held


## Las manos que ve este jugador (solo existen en su propio equipo).
func arms() -> FirstPersonArms:
	return _arms


func focused() -> Interactable:
	return _focus


## Lo llama el objeto cuando el anfitrión decide que este jugador lo lleva.
func set_held_item(item: Carryable) -> void:
	_held = item
	_reach_share = 1.0
	if not is_local():
		return
	hold_rotation = _pickup_rotation(item) if item != null else Quaternion.IDENTITY
	inspecting = false
	if _arms != null:
		if item != null:
			_arms.hold(item.visual(), item.state.data.weight, item.in_hands)
		else:
			_arms.hold(null)


## Cuánto frena lo que lleva (en las manos y a la espalda): de 1 (nada) hacia 0.
func carry_slowdown() -> float:
	return 1.0 / (1.0 + carried_weight() / HALF_SPEED_WEIGHT)


## Lo más que puede bajar la mirada ahora: sin nada en las manos, el límite de
## siempre; con algo, hasta donde las manos lo pueden seguir sin meterlo en el
## pecho (depende de lo que abulta).
func lowest_pitch() -> float:
	if _held == null:
		return -LOOK_LIMIT
	var hold: Dictionary = _placement(_held.state.data.weight, _held.bounds())
	return clampf(hold["lowest_pitch"], -LOOK_LIMIT, 0.0)


## Dónde debe estar un objeto de [param mass] kilos que este jugador lleva: el
## transform de su cuerpo. [param bounds] es la caja que lo envuelve, en sus
## propios ejes; se coloca por su centro. No tiene en cuenta las paredes (eso lo
## hace [method carry_target]).
func hold_transform(mass: float, bounds: AABB = AABB()) -> Transform3D:
	var hold: Dictionary = _placement(mass, bounds)
	var turn: Basis = hold["turn"]
	var center: Vector3 = hold["start"] + (hold["direction"] as Vector3) * float(hold["far"])
	return Transform3D(turn, center - turn * bounds.get_center())


## Dónde debe estar [param item] mientras lo lleva este jugador. Si hay una
## pared delante, se lo acerca al pecho en vez de meterlo en ella. Con
## [param cast] se vuelve a mirar si hay algo delante; si no, se usa lo que se
## vio la última vez (sirve fuera de la física, para dibujarlo).
func carry_target(item: Carryable, cast: bool = true) -> Transform3D:
	var bounds: AABB = item.bounds()
	var hold: Dictionary = _placement(item.state.data.weight, bounds)
	var turn: Basis = hold["turn"]
	var start: Vector3 = hold["start"]
	var direction: Vector3 = hold["direction"]
	var near: float = hold["near"]
	var far: float = hold["far"]
	if cast and is_inside_tree():
		_reach_share = _free_share(item, turn, start + direction * near, direction, far - near)
	var center: Vector3 = start + direction * lerpf(near, far, _reach_share)
	var shake: float = (
		tremble + (HUNGRY_TREMBLE if GameState.hungry_days >= GameState.HUNGRY_SHAKE else 0.0)
	)
	if shake > 0.0:
		var t: float = Time.get_ticks_msec() / 1000.0
		center += Vector3(sin(t * 23.0) + sin(t * 37.0) * 0.5, sin(t * 29.0 + 1.3), 0.0) * shake
	if throw_charge > 0.0:
		# Cargando el brazo: atrás y algo arriba.
		center += (-direction * 0.16 + Vector3.UP * 0.06) * throw_charge
	return Transform3D(turn, center - turn * bounds.get_center())


## Cómo se lleva algo de [param mass] kilos que mide [param bounds]: desde dónde
## ([code]start[/code], los ojos o, con una mano, algo a su derecha) y hacia
## dónde queda su centro, lo cerca que puede ir sin tocar el pecho y lo lejos
## que se quiere, su giro en el mundo y lo más que se puede bajar la mirada sin
## que las manos lo pierdan.
func _placement(mass: float, bounds: AABB) -> Dictionary:
	var turn: Basis = Basis(hold_rotation)
	var extent: Vector3 = GripModifier.extent(turn, bounds.size / 2.0)
	var one_hand: bool = GripModifier.fits_one_hand(bounds.size, mass)
	var distance: float = CARRY_DISTANCE + maxf(0.0, maxf(extent.x, extent.z) - FREE_HALF_WIDTH)
	var drop: float = CARRY_DROP + minf(HEAVY_DROP, mass * HEAVY_DROP_PER_KG)
	if one_hand:
		drop -= (0.5 - GripModifier.ONE_HAND_HEIGHT) * 2.0 * extent.y
	else:
		drop += maxf(0.0, extent.y - FREE_HALF_HEIGHT) * TALL_DROP - TWO_HANDS_LIFT
	if inspecting:
		distance = maxf(INSPECT_DISTANCE, bounds.size.length() / 2.0 + INSPECT_CLEARANCE)
		drop = INSPECT_DROP
	# Nunca dentro del pecho. Si algo abulta más de lo que se alcanza, va más lejos.
	var clearance: float = TORSO_RADIUS + TORSO_GAP + extent.z
	var far: float = maxf(Vector2(distance, drop).length(), clearance * 1.05)
	# En la vista, por debajo de la mirada y donde las manos lo alcanzan.
	var hands: float = GripModifier.highest_center(far, FOV) - HANDS_MARGIN
	var screen: float = minf(-atan2(drop, distance), hands)
	# Cuanto más abajo, más lejos del pecho tiene que ir: no puede bajar de aquí.
	var lowest: float = -acos(clearance / far)
	var highest: float = minf(
		-lowest, lerpf(HIGHEST_LIGHT, HIGHEST_HEAVY, clampf(mass / HEAVY_WEIGHT, 0.0, 1.0))
	)
	var elevation: float = clampf(head_pitch + screen, lowest, maxf(lowest, highest))
	var yaw: Basis = Basis(Vector3.UP, rotation.y)
	var side: float = ONE_HAND_SIDE if one_hand and not inspecting else 0.0
	return {
		"turn": yaw * turn,
		"start": eye_position() + yaw * Vector3(side, 0.0, 0.0),
		"direction": yaw * Vector3(0.0, sin(elevation), -cos(elevation)),
		"near": minf(far, clearance / cos(elevation)),
		"far": far,
		"lowest_pitch": lowest - hands,
	}


## Al coger algo se queda derecho y de cara, por el lado que más se parezca a
## como estaba: como mucho gira un octavo de vuelta.
func _pickup_rotation(item: Carryable) -> Quaternion:
	var body: Node3D = item.get_parent() as Node3D
	var relative: Basis = Basis(Vector3.UP, -rotation.y) * body.global_basis.orthonormalized()
	var side: Vector3 = Vector3(relative.x.x, 0.0, relative.x.z)
	if side.length() < 0.3:
		return Quaternion.IDENTITY
	var quarters: float = roundf(atan2(-side.z, side.x) / (PI / 2.0))
	return Quaternion(Vector3.UP, quarters * PI / 2.0)


## La forma de lo que se lleva, para ver con qué choca.
func _carry_query(item: Carryable) -> PhysicsShapeQueryParameters3D:
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	query.shape = item.cast_shape()
	query.collision_mask = MASK_CARRY
	query.exclude = [get_rid(), item.body_rid()]
	return query


## Cuánto del camino que va de [param nearest] (lo más pegado al pecho que puede
## ir [param item]) a [param length] metros más allá, en [param direction], está
## libre: si hay una pared, se lleva más cerca en vez de meterlo en ella.
func _free_share(
	item: Carryable, turn: Basis, nearest: Vector3, direction: Vector3, length: float
) -> float:
	if length <= 0.0:
		return 1.0
	var space: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var query: PhysicsShapeQueryParameters3D = _carry_query(item)
	query.transform = Transform3D(turn, nearest)
	# Pegado al pecho ya toca algo. (Un barrido no ve lo que toca al empezar.)
	if not space.get_rest_info(query).is_empty():
		return 0.0
	query.motion = direction * length
	var safe: float = space.cast_motion(query)[0]
	return 1.0 if safe >= 1.0 else maxf(0.0, safe - CARRY_SKIN / length)


## Lo que se lleva va por delante y choca antes que el cuerpo: se puede andar
## hacia una pared mientras quepa entre ella y el pecho; después, solo a lo
## largo de ella. Lo mismo con los demás jugadores.
func _stopped_by_held(planar: Vector3, delta: float) -> Vector3:
	if _held == null:
		return planar
	# Mira si hay una pared delante, para dibujarlo donde lo pone el anfitrión.
	carry_target(_held)
	if planar == Vector3.ZERO:
		return planar
	var hold: Dictionary = _placement(_held.state.data.weight, _held.bounds())
	var nearest: Vector3 = hold["start"] + (hold["direction"] as Vector3) * float(hold["near"])
	var query: PhysicsShapeQueryParameters3D = _carry_query(_held)
	query.transform = Transform3D(hold["turn"], nearest + planar * delta)
	return _slide(planar, get_world_3d().direct_space_state.get_rest_info(query))


## Quita a [param planar] lo que empuja contra lo que se ha tocado ([param hit],
## de [method PhysicsDirectSpaceState3D.get_rest_info]). Suelos y techos no paran.
static func _slide(planar: Vector3, hit: Dictionary) -> Vector3:
	if hit.is_empty():
		return planar
	var normal: Vector3 = hit["normal"]
	normal.y = 0.0
	if normal.length() < 0.3:
		return planar
	normal = normal.normalized()
	var into: float = planar.dot(normal)
	return planar - normal * into if into < 0.0 else planar


## Empuja los objetos sueltos con los que choca. La física es del anfitrión. Lo
## que lleva alguien no se empuja: ya lo sujetan sus manos.
func _push_objects() -> void:
	if not multiplayer.is_server():
		return
	for index: int in get_slide_collision_count():
		var collision: KinematicCollision3D = get_slide_collision(index)
		var body: RigidBody3D = collision.get_collider() as RigidBody3D
		if body == null:
			continue
		var item: Carryable = body.get_node_or_null(^"Carryable") as Carryable
		if item != null and item.is_held():
			continue
		body.apply_central_impulse(-collision.get_normal() * 0.35 * minf(body.mass, 4.0))


func _update_focus() -> void:
	var found: Interactable = null
	if _held == null:
		var from: Vector3 = _camera.global_position
		var to: Vector3 = from - _camera.global_basis.z * REACH
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
			from, to, MASK_REACH, [get_rid()]
		)
		query.collide_with_areas = true
		var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			found = Interactable.of(hit["collider"] as Node)
			if found != null and not found.enabled:
				found = null
	if found == _focus:
		return
	if _focus != null and is_instance_valid(_focus):
		_focus.set_focused(false)
	_focus = found
	if _focus != null:
		_focus.set_focused(true)


## Busca lo que se trabajaría con lo que se lleva: lo que se tiene delante, a su
## alcance (también las áreas, como las manchas del suelo).
func _update_work_target() -> void:
	var tool: StringName = current_tool()
	var found: Workable = null
	if tool != &"" and _camera != null:
		var from: Vector3 = _camera.global_position
		var to: Vector3 = from - _camera.global_basis.z * REACH
		var exclude: Array[RID] = [get_rid()]
		if _held != null:
			exclude.append(_held.body_rid())
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
			from, to, MASK_REACH, exclude
		)
		query.collide_with_areas = true
		var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			found = Workable.find(hit["collider"] as Node, tool)
			if found != null:
				_work_point = hit["position"]
				_work_normal = hit["normal"]
		if found == null and _held != null:
			var own: Workable = Workable.find(_held.body(), tool)
			if own != null and own.self_use:
				found = own
				_work_point = _held.body().global_position
				_work_normal = _camera.global_basis.z
	if found != _work_target and _work_pending != 0.0:
		_send_work()
	_work_target = found
	_refresh_reticle()


## Mantener el botón principal sobre algo que se puede trabajar es trabajarlo:
## lo medido se manda al anfitrión a ratos.
func _update_work(delta: float, pressing: bool) -> void:
	var was_working: bool = working
	working = pressing and _work_target != null and is_instance_valid(_work_target)
	if working and not was_working:
		_work_target.begin(self)
	if working and _work_target.gesture == Workable.Gesture.HOLD:
		_work_pending += delta / HOLD_SECONDS
	if not working:
		_sway *= exp(-SWAY_RETURN * delta)
		_last_motion = Vector2.ZERO
	_work_clock += delta
	if _work_clock >= WORK_SEND_SECONDS or (was_working and not working):
		_send_work()


func _send_work() -> void:
	_work_clock = 0.0
	if _work_pending != 0.0 and _work_target != null and is_instance_valid(_work_target):
		apply_work(_work_target, _work_pending, _work_point)
	_work_pending = 0.0


## El punto de mira: lo que se puede usar; si no, lo que se puede trabajar.
func _refresh_reticle() -> void:
	if _reticle == null:
		return
	if _focus != null:
		_reticle.show_target(_focus)
	elif _work_target != null:
		_reticle.show_icon(Interactable.ICONS[&"usar"])
	else:
		_reticle.show_target(null)
