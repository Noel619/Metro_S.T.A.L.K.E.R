class_name SurfaceDoor
extends Fixture
## Una puerta de la superficie (F3-06, docs/SUPERFICIE.md 4.3): la de un quiosco, un
## trastero o el transformador. Con F se abre y se cierra si nada la cierra; si algo
## la cierra, se sacude (y suena un poco) y no se abre. Lo que la puede cerrar:
## - "cerradura": la suya. Las ganzúas la abren (sin ruido, despacio: [LockpickView])
##   y la palanca la revienta (se oye en toda la plaza).
## - "candado": en una armella. La cizalla lo corta, las ganzúas lo abren y la palanca
##   arranca la armella.
## - "cadena": con su candado, entre la hoja y el marco. Solo la cizalla.
## - "atrancada": hinchada por el hielo o con algo detrás. Solo la palanca.
## Lo que se rompe o se corta ya no cierra ("rota" o nada). Su estado vive en el
## mundo ([DepotWorld], que se guarda): "abierta", "cierre", "palanca" y "cizalla" (lo
## que se lleva hecho con cada una).
##
## La hoja gira sobre su bisagra. Su marco: el origen abajo, en el eje de la bisagra;
## +x a lo largo de la hoja cerrada, +y arriba y +z hacia donde se abre.

const LOCK: StringName = &"cerradura"
const PADLOCK: StringName = &"candado"
const CHAIN: StringName = &"cadena"
const STUCK: StringName = &"atrancada"
const BROKEN: StringName = &"rota"
## Con qué se abre cada cierre.
const PICKABLE: Array[StringName] = [LOCK, PADLOCK]
const CUTTABLE: Array[StringName] = [PADLOCK, CHAIN]
const FORCEABLE: Array[StringName] = [LOCK, PADLOCK, STUCK]
## Tirones de palanca para reventarla y apretones de cizalla para cortar.
const FORCE_WORK: float = 4.0
const CUT_WORK: float = 2.0
## Cada tirón de palanca cruje (aunque no ceda).
const CREAK: StringName = &"puerta"
## Lo que gira abierta (grados, hacia +z) y lo que tarda.
const OPEN_DEGREES: float = 100.0
const SWING_SECONDS: float = 1.1
## Las herramientas.
const PICKS: StringName = &"ganzuas"
const CROWBAR: StringName = &"palanca"
const CUTTERS: StringName = &"cizalla"
## Lo que se gastan las ganzúas cuando se parte una.
const PICK_WEAR: float = 0.34

## Lo que mide la hoja: ancho, alto y grueso.
var size: Vector3 = Vector3(0.8, 2.0, 0.05)
## Cómo está al empezar la partida (antes de que nadie la toque).
var initial_lock: StringName = &""
var initial_open: bool = false
## Dónde cuelga el candado o la cadena, en el marco de la bisagra.
var lock_point: Vector3 = Vector3.ZERO

var _pivot: Node3D
var _leaf: AnimatableBody3D
var _padlock: Node3D
var _chain: Node3D
var _angle: float = 0.0
var _shake: float = 0.0


## Monta la puerta: [param id] es su nombre en el mundo; [param hinge], su bisagra (en el
## marco del padre); [param leaf_mesh], la hoja, hecha en el marco de la bisagra (o null:
## una tabla); [param lock_meshes], las mallas del candado y de la cadena ("candado",
## "cadena"), si las hay.
func setup(
	id: String,
	hinge: Transform3D,
	leaf_size: Vector3,
	leaf_mesh: Mesh = null,
	lock_meshes: Dictionary = {}
) -> void:
	fixture_id = id
	name = id.validate_node_name()
	size = leaf_size
	transform = hinge
	if lock_point == Vector3.ZERO:
		lock_point = Vector3(size.x - 0.12, 1.05, size.z * 0.5 + 0.02)
	_pivot = Node3D.new()
	_pivot.name = "Bisagra"
	add_child(_pivot)
	var visual: MeshInstance3D = MeshInstance3D.new()
	visual.name = "Hoja"
	if leaf_mesh != null:
		visual.mesh = leaf_mesh
	else:
		var plank: BoxMesh = BoxMesh.new()
		plank.size = size
		visual.mesh = plank
		visual.position = size * 0.5 * Vector3(1.0, 1.0, 0.0)
	_pivot.add_child(visual)
	_leaf = AnimatableBody3D.new()
	_leaf.name = "Cuerpo"
	_leaf.sync_to_physics = false
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	shape.position = Vector3(size.x * 0.5, size.y * 0.5, 0.0)
	_leaf.add_child(shape)
	_pivot.add_child(_leaf)
	_padlock = _hang(lock_meshes.get("candado") as Mesh, _pivot, "Candado")
	_chain = _hang(lock_meshes.get("cadena") as Mesh, self, "Cadena")


func _ready() -> void:
	add_use(_leaf)
	add_work(_leaf, [CROWBAR], Workable.Gesture.PULL, "Palanca")
	add_work(_leaf, [CUTTERS], Workable.Gesture.PULL, "Cizalla")
	var picking: Workable = add_work(_leaf, [PICKS], Workable.Gesture.PICK, "Ganzuas")
	picking.begun.connect(_on_pick_begun)
	super._ready()
	_angle = _target_angle()
	_apply()


func lock() -> StringName:
	return StringName(str(value("cierre", String(initial_lock))))


func is_open() -> bool:
	return bool(value("abierta", initial_open))


## Algo la cierra (no se abre con F).
func is_locked() -> bool:
	return not lock().is_empty() and lock() != BROKEN


## Los pines de su cerradura (o de su candado): cuántos son y dónde está el punto de
## cada uno (de 0 a 1), siempre los mismos para esta puerta.
func pins() -> PackedFloat32Array:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = hash(fixture_id + ":pines")
	var count: int = 3 if lock() == PADLOCK else 4 + rng.randi() % 2
	var result: PackedFloat32Array = PackedFloat32Array()
	for _index: int in count:
		result.append(rng.randf_range(0.3, 0.8))
	return result


## Lo que se ve abierta (radianes).
func angle() -> float:
	return _angle


func _on_used(player: Player, _action: StringName) -> void:
	if is_locked():
		# Se sacude y suena un poco: así se sabe que está cerrada.
		set_value("golpes", int(value("golpes", 0)) + 1)
		_noise(player.global_position, &"puerta", 0.5)
		return
	set_value("abierta", not is_open())
	_noise(global_position, &"puerta", 0.6)


func _on_worked(_player: Player, tool: StringName, amount: float, _point: Vector3) -> void:
	if amount <= 0.0 or not is_locked():
		return
	match tool:
		CROWBAR:
			if not FORCEABLE.has(lock()):
				return
			var progress: float = float(value("palanca", 0.0)) + amount / FORCE_WORK
			if progress >= 1.0:
				set_values({"palanca": 1.0, "cierre": String(BROKEN), "abierta": true})
				_noise(global_position, CROWBAR)
			else:
				set_value("palanca", progress)
				_noise(global_position, CREAK, 0.8)
		CUTTERS:
			if not CUTTABLE.has(lock()):
				return
			var cut: float = float(value("cizalla", 0.0)) + amount / CUT_WORK
			if cut >= 1.0:
				set_values({"cizalla": 1.0, "cierre": ""})
				_noise(global_position, CUTTERS)
			else:
				set_value("cizalla", cut)


## En el equipo de quien trabaja: con las ganzúas en la mano y la puerta cerrada con
## algo que se abre con ellas, se abre la vista de la cerradura.
func _on_pick_begun(player: Node) -> void:
	var who: Player = player as Player
	if who == null or not who.is_local() or not PICKABLE.has(lock()):
		return
	if LockpickView.is_open():
		return
	var view: LockpickView = LockpickView.open(who, self)
	if view != null:
		view.finished.connect(
			func(opened: bool) -> void: request_pick.rpc_id(Carryable.HOST_PEER, opened)
		)


## Lo que ha pasado con las ganzúas: [param opened], que se ha abierto; si no, que se
## ha partido una. Decide el anfitrión (las tiene que llevar en la mano).
@rpc("any_peer", "call_local", "reliable")
func request_pick(opened: bool) -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	var player: Player = Player.find(get_tree(), sender)
	if player == null or player.current_tool() != PICKS or not PICKABLE.has(lock()):
		return
	if opened:
		set_value("cierre", "")
		_noise(global_position, &"ganzua")
		return
	var picks: Carryable = player.held_item()
	var left: float = picks.state.condition - PICK_WEAR
	if left <= 0.0:
		var items: WorldItems = world_items()
		if items != null:
			items.remove_item(picks)
	else:
		picks.set_values({"condition": left})


func _refresh() -> void:
	_shake = 1.0
	var shown: StringName = lock()
	if _padlock != null:
		_padlock.visible = shown == PADLOCK
	if _chain != null:
		_chain.visible = shown == CHAIN


func _process(delta: float) -> void:
	var target: float = _target_angle()
	if is_equal_approx(_angle, target) and _shake <= 0.0:
		return
	_angle = move_toward(_angle, target, deg_to_rad(OPEN_DEGREES) / SWING_SECONDS * delta)
	_shake = maxf(0.0, _shake - delta * 3.0)
	_apply()


func _target_angle() -> float:
	return deg_to_rad(OPEN_DEGREES) if is_open() else 0.0


func _apply() -> void:
	if _pivot == null:
		return
	# Cerrada con algo, al sacudirla cede un dedo y vuelve.
	var rattle: float = sin(Time.get_ticks_msec() * 0.05) * 0.03 * _shake
	_pivot.rotation.y = -(_angle + absf(rattle))


func _noise(where: Vector3, kind: StringName, scale: float = 1.0) -> void:
	var stimuli: Stimuli = Stimuli.find(get_tree()) if is_inside_tree() else null
	if stimuli != null:
		stimuli.make_noise(where, NoiseRules.sound_radius(kind) * scale, kind)


## El candado (en la hoja) o la cadena (en el marco): su malla o, si no la hay, una caja.
func _hang(mesh: Mesh, parent: Node3D, node_name: String) -> Node3D:
	var holder: MeshInstance3D = MeshInstance3D.new()
	holder.name = node_name
	if mesh != null:
		holder.mesh = mesh
	else:
		var box: BoxMesh = BoxMesh.new()
		box.size = Vector3(0.06, 0.08, 0.03) if node_name == "Candado" else Vector3(0.1, 0.3, 0.04)
		holder.mesh = box
	holder.position = lock_point
	holder.visible = false
	parent.add_child(holder)
	return holder
