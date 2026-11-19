class_name LockpickView
extends Node3D
## Las ganzúas en una cerradura (F3-06, docs/SUPERFICIE.md 4.3): la cerradura vista de
## lado, cortada, delante de ti, con el cilindro y sus pines, la ganzúa y la llave de
## tensión. Con el ratón, a los lados se pasa de pin en pin (con la ganzúa abajo) y
## arriba y abajo se levanta el pin. Cada pin tiene su punto, la línea de corte:
## llevarlo ahí y quedarse quieto un momento lo deja puesto (la llave de tensión cede
## un poco). Pasarse lo atasca y hay que bajar la ganzúa para soltarlo; forzarlo deprisa
## tuerce la ganzúa y, si se tuerce mucho, se parte. El miedo hace temblar la mano.
## Con todos los pines puestos, el cilindro gira y se abre.
##
## Esc, F o el botón derecho la dejan. El tiempo no se para y no se puede andar. Solo
## existe en el equipo de quien abre; el resultado se lo lleva [SurfaceDoor].

## Se ha acabado: [param opened], abierta; si no, se ha partido una ganzúa (o se ha dejado:
## entonces no se emite).
signal finished(opened: bool)

## Dónde va, en el marco de la cámara.
const DISTANCE: float = 0.3
const DROP: float = 0.015
## Lo que mide: el paso entre pines, el radio del cilindro y lo que sube un pin entero.
const PITCH: float = 0.024
const PLUG_RADIUS: float = 0.012
const TRAVEL: float = 0.016
## El ratón: lo que mueve cada píxel de lado (en pines) y de alto (en recorrido).
const SIDE_PER_PIXEL: float = 0.012
const LIFT_PER_PIXEL: float = 0.004
## Con la ganzúa más alta que esto no se pasa de un pin a otro.
const FREE_LIFT: float = 0.12
## El punto de cada pin: lo que se puede errar y lo que hay que quedarse quieto.
const TOLERANCE: float = 0.07
const SET_SECONDS: float = 0.4
## Forzar: por encima de esta velocidad (recorridos por segundo) se tuerce la ganzúa.
const SAFE_SPEED: float = 1.6
const BEND_RATE: float = 0.35
const OVERSET_BEND: float = 0.25
const BEND_RECOVERY: float = 0.08
## El miedo: lo que tiembla la punta con el miedo entero (en recorrido).
const TREMBLE: float = 0.09
## Lo que tarda en girar el cilindro al final.
const TURN_SECONDS: float = 0.5
## Se deja si quien abre se aleja más que esto.
const MAX_DISTANCE: float = 1.8
const BRASS: Color = Color("#b08d57")
const STEEL: Color = Color("#6f747a")
const HOUSING: Color = Color("#8b8f92")
const BACKDROP: Color = Color("#201e1c")
const PICK: Color = Color("#c9c9c9")

## La que está abierta (solo hay una).
static var active: LockpickView = null

var player: Player
var door: SurfaceDoor
## Dónde está el punto de cada pin (de 0 a 1) y si ya está puesto.
var targets: PackedFloat32Array = PackedFloat32Array()
var set_pins: Array[bool] = []
## La ganzúa: bajo qué pin está (contando a trozos) y lo alta que va (de 0 a 1).
var side: float = 0.0
var lift: float = 0.0
## Lo torcida que está (a 1 se parte).
var bend: float = 0.0

var _dwell: float = 0.0
var _overset: bool = false
var _last_lift: float = 0.0
var _turning: float = -1.0
var _clock: float = 0.0
var _pins: Array[Node3D] = []
var _pick: Node3D
var _wrench: Node3D
var _plug: Node3D


static func is_open() -> bool:
	return active != null and is_instance_valid(active)


## Abre la cerradura de [param lock_door] para [param who] (delante de su cámara).
static func open(who: Player, lock_door: SurfaceDoor) -> LockpickView:
	var camera: Camera3D = who.get_viewport().get_camera_3d()
	if camera == null:
		return null
	if is_open():
		active.close()
	var view: LockpickView = LockpickView.new()
	view.player = who
	view.door = lock_door
	view.targets = lock_door.pins()
	for _index: int in view.targets.size():
		view.set_pins.append(false)
	view.name = "Ganzuas"
	view.position = Vector3(0.0, -DROP, -DISTANCE)
	camera.add_child(view)
	return view


## Cierra sin abrir (se deja).
func close() -> void:
	if active == self:
		active = null
	queue_free()


## El pin bajo la ganzúa.
func current_pin() -> int:
	return clampi(roundi(side), 0, targets.size() - 1)


## Cuántos pines están puestos.
func pins_set() -> int:
	return set_pins.count(true)


## Mueve la ganzúa como lo haría el ratón ([param relative], en píxeles).
func move_pick(relative: Vector2) -> void:
	if _turning >= 0.0:
		return
	lift = clampf(lift - relative.y * LIFT_PER_PIXEL, 0.0, 1.0)
	if lift <= FREE_LIFT:
		side = clampf(side + relative.x * SIDE_PER_PIXEL, 0.0, float(targets.size() - 1))


## Lo alto que está de verdad la punta, con el temblor del miedo.
func tip_height() -> float:
	var fear: float = clampf(player.tremble / Fear.HANDS_TREMBLE, 0.0, 1.0) if player else 0.0
	var shake: float = (sin(_clock * 23.0) * 0.6 + sin(_clock * 37.0 + 1.3) * 0.4) * fear
	return clampf(lift + shake * TREMBLE, 0.0, 1.0)


func _ready() -> void:
	active = self
	_build()
	_pose()


func _exit_tree() -> void:
	if active == self:
		active = null


func _unhandled_input(event: InputEvent) -> void:
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null:
		move_pick(motion.relative)
		get_viewport().set_input_as_handled()
		return
	var button: InputEventMouseButton = event as InputEventMouseButton
	var leaving: bool = (
		event.is_action_pressed(&"pause")
		or event.is_action_pressed(&"interact")
		or (button != null and button.pressed and button.button_index == MOUSE_BUTTON_RIGHT)
	)
	if leaving:
		close()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_clock += delta
	if not _still_valid():
		close()
		return
	if _turning >= 0.0:
		_turning += delta / TURN_SECONDS
		if _turning >= 1.0:
			finished.emit(true)
			close()
			return
	else:
		_work(delta)
	_pose()


## Un paso del trabajo: el pin bajo la ganzúa sube con ella; en su punto, quieto, se
## queda puesto; pasado, se atasca; deprisa, la ganzúa se tuerce.
func _work(delta: float) -> void:
	var speed: float = absf(lift - _last_lift) / maxf(delta, 0.0001)
	_last_lift = lift
	var pin: int = current_pin()
	var tip: float = tip_height()
	if set_pins[pin]:
		_dwell = 0.0
	elif _overset:
		bend += OVERSET_BEND * delta + maxf(0.0, speed - SAFE_SPEED) * BEND_RATE * delta
		if tip < targets[pin] - TOLERANCE:
			_overset = false
	elif tip > targets[pin] + TOLERANCE:
		_overset = true
		_dwell = 0.0
	elif absf(tip - targets[pin]) <= TOLERANCE:
		_dwell += delta
		if _dwell >= SET_SECONDS:
			set_pins[pin] = true
			_dwell = 0.0
	else:
		_dwell = 0.0
	if not _overset:
		bend += maxf(0.0, speed - SAFE_SPEED * 2.0) * BEND_RATE * 0.5 * delta
		bend = maxf(0.0, bend - BEND_RECOVERY * delta)
	if bend >= 1.0:
		finished.emit(false)
		close()
		return
	if pins_set() == targets.size():
		_turning = 0.0


func _still_valid() -> bool:
	if player == null or door == null or not is_instance_valid(player):
		return false
	if not is_instance_valid(door) or not SurfaceDoor.PICKABLE.has(door.lock()):
		return false
	if player.current_tool() != SurfaceDoor.PICKS:
		return false
	return player.global_position.distance_to(door.global_position) <= MAX_DISTANCE + door.size.x


## La cerradura cortada: la caja, el cilindro, los pines (cada uno con su muelle), la
## ganzúa y la llave de tensión.
func _build() -> void:
	var count: int = targets.size()
	var width: float = PITCH * (count + 1.5)
	# Una placa oscura detrás, para que la cerradura cortada se lea como un despiece.
	var backdrop: MeshInstance3D = _box(Vector3(width + 0.035, 0.1, 0.002), BACKDROP)
	backdrop.position = Vector3(width * 0.5 - PITCH, 0.008, -0.018)
	add_child(backdrop)
	var housing: MeshInstance3D = _box(Vector3(width, 0.07, 0.012), HOUSING)
	housing.position = Vector3(width * 0.5 - PITCH, 0.012, -0.008)
	add_child(housing)
	_plug = Node3D.new()
	_plug.name = "Cilindro"
	add_child(_plug)
	var plug: MeshInstance3D = MeshInstance3D.new()
	var cylinder: CylinderMesh = CylinderMesh.new()
	cylinder.top_radius = PLUG_RADIUS
	cylinder.bottom_radius = PLUG_RADIUS
	cylinder.height = width
	plug.mesh = cylinder
	plug.material_override = _flat(BRASS.darkened(0.15))
	plug.rotation.z = PI * 0.5
	plug.position = Vector3(width * 0.5 - PITCH, -PLUG_RADIUS, 0.0)
	_plug.add_child(plug)
	for index: int in count:
		var stack: Node3D = Node3D.new()
		stack.name = "Pin_%d" % index
		stack.position.x = index * PITCH
		add_child(stack)
		var key_pin: MeshInstance3D = _box(Vector3(0.006, 0.012, 0.006), BRASS)
		key_pin.name = "Llave"
		stack.add_child(key_pin)
		var driver: MeshInstance3D = _box(Vector3(0.006, 0.012, 0.006), STEEL)
		driver.name = "Conductor"
		stack.add_child(driver)
		var spring: MeshInstance3D = _box(Vector3(0.004, 0.014, 0.004), STEEL.lightened(0.25))
		spring.name = "Muelle"
		stack.add_child(spring)
		_pins.append(stack)
	_pick = Node3D.new()
	_pick.name = "Ganzua"
	add_child(_pick)
	var wire: MeshInstance3D = _box(Vector3(0.12, 0.0016, 0.002), PICK)
	wire.position = Vector3(-0.06, 0.0, 0.0)
	_pick.add_child(wire)
	var hook: MeshInstance3D = _box(Vector3(0.0016, 0.005, 0.002), PICK)
	hook.position = Vector3(0.0, 0.0025, 0.0)
	_pick.add_child(hook)
	_wrench = Node3D.new()
	_wrench.name = "Tension"
	_wrench.position = Vector3(-PITCH * 0.9, -PLUG_RADIUS * 1.6, 0.004)
	add_child(_wrench)
	var arm: MeshInstance3D = _box(Vector3(0.05, 0.003, 0.002), STEEL)
	arm.position = Vector3(-0.025, 0.0, 0.0)
	_wrench.add_child(arm)


## Pone cada pieza según cómo va: los pines puestos quedan en la línea de corte; el de
## la ganzúa sube con ella; la llave de tensión cede con cada pin puesto.
func _pose() -> void:
	var pin: int = current_pin()
	var tip: float = tip_height()
	for index: int in _pins.size():
		var height: float = 0.0
		if set_pins[index]:
			height = targets[index]
		elif index == pin:
			height = tip
		var raise: float = height * TRAVEL
		var key_pin: Node3D = _pins[index].get_node("Llave")
		var driver: Node3D = _pins[index].get_node("Conductor")
		var spring: Node3D = _pins[index].get_node("Muelle")
		# El pin de llave baja hasta el fondo del cilindro; encima, el conductor y el muelle.
		var bottom: float = -PLUG_RADIUS * 1.6 + raise
		key_pin.position.y = bottom + 0.006 + (targets[index] - 0.5) * 0.004
		driver.position.y = key_pin.position.y + 0.012
		spring.position.y = driver.position.y + 0.013
		spring.scale.y = clampf(1.0 - raise / 0.03, 0.4, 1.0)
	var under: float = side * PITCH
	_pick.position = Vector3(under, -PLUG_RADIUS * 1.6 + tip * TRAVEL - 0.0025, 0.0)
	var torn: float = sin(_clock * 40.0) * 0.004 * bend
	_pick.rotation.z = -0.05 * bend + torn
	var turn: float = 0.02 * pins_set() + (maxf(_turning, 0.0) * 0.9)
	_wrench.rotation.z = -turn
	_plug.rotation.x = maxf(_turning, 0.0) * PI * 0.5


func _box(box_size: Vector3, color: Color) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	var box: BoxMesh = BoxMesh.new()
	box.size = box_size
	instance.mesh = box
	instance.material_override = _flat(color)
	return instance


static func _flat(color: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	return material
