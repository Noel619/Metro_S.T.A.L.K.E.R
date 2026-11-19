class_name Backpack
extends Node
## La mochila (F3-03): un objeto que se abre, donde se mete el botín en su
## cuadrícula y de donde se saca ([BackpackGrid]).
##
## Es hijo del cuerpo de la mochila, como [Carryable]. Se abre y se cierra con
## las manos (mantener el botón principal, como las cajas). Abierta no se puede
## coger: con algo en la mano, "interactuar" sobre ella lo mete en la casilla a
## la que se apunta (o en la primera donde quepa, girado si hace falta); con las
## manos vacías, saca lo que haya en la casilla apuntada. Lo pide quien lo hace
## y lo decide el anfitrión. Lo de dentro se dibuja en su sitio (copias de sus
## modelos, sin física, encogidas si no caben en sus casillas) y la mochila pesa
## lo que lleva.

## Lo que hay que mantener las manos para abrirla o cerrarla (en segundos). Fuera
## es lento: se abre de rodillas, con todo a la vista (README 6.5).
const TOGGLE_WORK: float = 0.35
const TOGGLE_WORK_OUTSIDE: float = 1.6
## La cuadrícula en los ejes de la mochila (tools/blender/recipes/mochila.py):
## el lado de una casilla, la esquina de la casilla (0, 0) (al fondo, a la
## izquierda) y la altura del suelo de dentro.
const CELL: float = 0.075
const GRID_CORNER: Vector3 = Vector3(-0.225, 0.025, -0.1875)
## Lo más alto que se dibuja lo de dentro (lo que asoma por la boca).
const INSIDE_HEIGHT: float = 0.16
## Lo que se deja libre alrededor de cada objeto en sus casillas.
const CELL_MARGIN: float = 0.008
## La tapa: cerrada en 0, abierta cuando ha caído hacia atrás hasta el suelo.
const LID_OPEN: float = deg_to_rad(-202.0)
const LID_SPEED: float = 7.0
const MODELS_DIR: String = "res://assets/models/"
const OPEN_KEY: String = "abierta"
## Los giros que se prueban para que lo de dentro quepa en sus casillas: de pie
## o tumbado a lo largo de cada lado, y girado un cuarto de vuelta.
const FITS: Array[Vector3] = [
	Vector3.ZERO,
	Vector3(0.0, 90.0, 0.0),
	Vector3(0.0, 0.0, 90.0),
	Vector3(0.0, 90.0, 90.0),
	Vector3(90.0, 0.0, 0.0),
	Vector3(90.0, 90.0, 0.0),
]

var item: Carryable
var items: WorldItems
var _lid: Node3D
var _inside: Node3D
## Lo que hay dibujado dentro (para no rehacerlo si no cambia).
var _drawn: Array = []
var _hold: float = 0.0


## La mochila de [param body], si lo es.
static func of(body: Node) -> Backpack:
	if body == null:
		return null
	return body.get_node_or_null(^"Mochila") as Backpack


func _ready() -> void:
	if not item.is_node_ready():
		await item.ready
	_lid = item.visual().find_child("tapa", true, false) as Node3D
	_inside = Node3D.new()
	_inside.name = "Dentro"
	item.visual().add_child(_inside)
	item.state_changed.connect(_refresh)
	var interactable: Interactable = Interactable.of(item.body())
	if interactable != null:
		interactable.interacted.connect(_on_interacted)
	_refresh()
	if _lid != null:
		_lid.rotation.x = LID_OPEN if is_open() else 0.0


func _process(delta: float) -> void:
	if _lid == null:
		return
	var target: float = LID_OPEN if is_open() else 0.0
	_lid.rotation.x = lerpf(_lid.rotation.x, target, 1.0 - exp(-LID_SPEED * delta))


func is_open() -> bool:
	return bool(item.state.extra.get(OPEN_KEY, false))


## Lo que lleva.
func grid() -> BackpackGrid:
	return BackpackGrid.from_extra(item.state.extra)


## La casilla a la que apunta un rayo (desde [param from], hacia [param direction],
## en el mundo): donde cruza el suelo de dentro. (-1, -1) si cae fuera.
func cell_at(from: Vector3, direction: Vector3) -> Vector2i:
	var to_local: Transform3D = item.body().global_transform.affine_inverse()
	var origin: Vector3 = to_local * from
	var ray: Vector3 = to_local.basis * direction
	if absf(ray.y) < 1e-4:
		return Vector2i(-1, -1)
	var t: float = (GRID_CORNER.y - origin.y) / ray.y
	if t < 0.0:
		return Vector2i(-1, -1)
	var hit: Vector3 = origin + ray * t
	var cell: Vector2i = Vector2i(
		floori((hit.x - GRID_CORNER.x) / CELL), floori((hit.z - GRID_CORNER.z) / CELL)
	)
	var size: Vector2i = BackpackGrid.SIZE
	if cell.x < 0 or cell.y < 0 or cell.x >= size.x or cell.y >= size.y:
		return Vector2i(-1, -1)
	return cell


## El centro de una casilla, en los ejes de la mochila.
static func cell_center(cell: Vector2i) -> Vector3:
	return GRID_CORNER + Vector3((cell.x + 0.5) * CELL, 0.0, (cell.y + 0.5) * CELL)


## Quien lleva [param held] quiere meterlo donde apunta. Devuelve si la mochila
## está abierta y se lo ha pedido al anfitrión (si no cabe, se queda en la mano).
func try_put(held: Carryable, from: Vector3, direction: Vector3) -> bool:
	if not is_open() or held == null or held == item:
		return false
	if not BackpackGrid.accepts(held.state.data):
		return false
	request_put.rpc_id(Carryable.HOST_PEER, held.state.uid, cell_at(from, direction))
	return true


## Mete en la mochila lo que lleva quien lo pide. Decide el anfitrión.
@rpc("any_peer", "call_local", "reliable")
func request_put(uid: int, aimed: Vector2i) -> void:
	if not multiplayer.is_server() or not is_open():
		return
	var player: Player = _near_player(_sender())
	if player == null:
		return
	var held: Carryable = player.held_item()
	if held == null or held.state.uid != uid or held == item:
		return
	var state: ItemState = ItemState.from_dict(held.state.to_dict())
	if stash(state, aimed):
		items.remove_item(held)


## Mete un objeto (su estado) en la casilla [param aimed] o donde quepa. Devuelve
## si cabía. Solo el anfitrión (lo usa quien mete algo y lo que llena una
## mochila desde código).
func stash(state: ItemState, aimed: Vector2i = Vector2i(-1, -1)) -> bool:
	if not multiplayer.is_server() or state == null:
		return false
	var contents: BackpackGrid = grid()
	var spot: Dictionary = contents.find_spot(state.data, aimed)
	if spot.is_empty():
		return false
	contents.put(state, spot["celda"], spot["giro"])
	_store(contents)
	return true


## Saca lo que hay en la casilla [param cell] y se lo da a quien lo pide.
## Decide el anfitrión.
@rpc("any_peer", "call_local", "reliable")
func request_take(cell: Vector2i) -> void:
	if not multiplayer.is_server() or not is_open():
		return
	var player: Player = _near_player(_sender())
	if player == null or player.held_item() != null:
		return
	var contents: BackpackGrid = grid()
	var index: int = contents.occupant(cell)
	if index < 0:
		return
	var state: ItemState = contents.take(index)
	_store(contents)
	items.give_state(player, state)


## Abre o cierra la mochila (en el anfitrión, al trabajarla con las manos).
func toggle() -> void:
	if not multiplayer.is_server():
		return
	var extra: Dictionary = item.state.extra.duplicate(true)
	extra[OPEN_KEY] = not is_open()
	item.set_values({"extra": extra})


## Mantener las manos sobre ella la abre o la cierra (fuera, más rato).
func on_worked(player: Node, tool: StringName, amount: float, _point: Vector3) -> void:
	if tool != Workable.HANDS or amount <= 0.0 or item.is_held():
		return
	var outside: bool = player is Player and (player as Player).surface
	_hold += amount
	if _hold >= (TOGGLE_WORK_OUTSIDE if outside else TOGGLE_WORK):
		_hold = 0.0
		toggle()


func _on_interacted(player: Node) -> void:
	if not is_open() or not player is Player:
		return
	var who: Player = player as Player
	if who.held_item() != null:
		return
	var ray: Array[Vector3] = who.aim_ray()
	var cell: Vector2i = cell_at(ray[0], ray[1])
	if cell.x >= 0:
		request_take.rpc_id(Carryable.HOST_PEER, cell)


func _store(contents: BackpackGrid) -> void:
	var extra: Dictionary = item.state.extra.duplicate(true)
	extra[BackpackGrid.KEY] = contents.to_value()
	extra[ItemState.INSIDE_WEIGHT] = snappedf(contents.weight(), 0.001)
	item.set_values({"extra": extra})


func _near_player(peer: int) -> Player:
	var player: Player = Player.find(get_tree(), peer)
	if player == null:
		return null
	if player.eye_position().distance_to(item.body().global_position) > Carryable.GRAB_RANGE:
		return null
	return player


func _sender() -> int:
	var peer: int = multiplayer.get_remote_sender_id()
	return Carryable.HOST_PEER if peer == 0 else peer


## Pone al día lo que depende del estado: si se puede coger, lo que pesa y lo
## que se ve dentro.
func _refresh() -> void:
	item.grabbable = not is_open()
	if multiplayer.is_server():
		item.body().mass = maxf(0.05, item.state.weight())
	var contents: BackpackGrid = grid()
	var signature: Array = []
	if is_open():
		signature = contents.entries
	if signature == _drawn:
		return
	_drawn = signature.duplicate(true)
	for child: Node in _inside.get_children():
		child.queue_free()
	if not is_open():
		return
	for index: int in contents.entries.size():
		_inside.add_child(_draw_entry(contents, index))


## Una copia que solo se dibuja de lo que hay en la entrada [param index], en sus
## casillas, girada y encogida para que quepa.
func _draw_entry(contents: BackpackGrid, index: int) -> Node3D:
	var entry: Dictionary = contents.entries[index]
	var data: ItemData = contents.state_at(index).data
	var cell: Vector2i = BackpackGrid.to_cell(entry["celda"])
	var span: Vector2i = BackpackGrid.extent(data, int(entry["giro"]))
	var room: Vector3 = Vector3(
		span.x * CELL - CELL_MARGIN, INSIDE_HEIGHT, span.y * CELL - CELL_MARGIN
	)
	var copy: Node3D = visual_copy(data.model)
	copy.name = "objeto_%d" % index
	var best: Basis = Basis.IDENTITY
	var best_scale: float = -1.0
	var best_box: AABB = AABB()
	for turn: Vector3 in FITS:
		var basis: Basis = Basis.from_euler(turn * (PI / 180.0))
		var box: AABB = _bounds(copy, basis)
		var fit: float = minf(
			minf(room.x / maxf(box.size.x, 0.001), room.z / maxf(box.size.z, 0.001)),
			minf(room.y / maxf(box.size.y, 0.001), 1.0)
		)
		if fit > best_scale + 0.001:
			best_scale = fit
			best = basis
			best_box = box
	var corner: Vector3 = cell_center(cell) - Vector3(CELL, 0.0, CELL) * 0.5
	var footprint_center: Vector3 = corner + Vector3(span.x * CELL, 0.0, span.y * CELL) * 0.5
	var scaled: Basis = best.scaled(Vector3.ONE * best_scale)
	var low: Vector3 = best_box.get_center() * best_scale
	low.y = best_box.position.y * best_scale
	copy.transform = Transform3D(scaled, footprint_center - low)
	return copy


## Una copia del modelo [param model] que solo se dibuja (sin física).
static func visual_copy(model: String) -> Node3D:
	var scene: Node3D = load(MODELS_DIR + model + ".glb").instantiate()
	var copy: Node3D = Node3D.new()
	for node: Node in scene.find_children("*", "MeshInstance3D", true, false):
		var source: MeshInstance3D = node as MeshInstance3D
		if source.mesh == null:
			continue
		var piece: MeshInstance3D = MeshInstance3D.new()
		piece.mesh = source.mesh
		for surface: int in source.get_surface_override_material_count():
			piece.set_surface_override_material(
				surface, source.get_surface_override_material(surface)
			)
		var where: Transform3D = source.transform
		var parent: Node = source.get_parent()
		while parent != null and parent != scene:
			if parent is Node3D:
				where = (parent as Node3D).transform * where
			parent = parent.get_parent()
		piece.transform = where
		piece.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		copy.add_child(piece)
	scene.free()
	return copy


## La caja que envuelve las mallas de [param copy] giradas con [param basis].
static func _bounds(copy: Node3D, basis: Basis) -> AABB:
	var result: AABB = AABB()
	var first: bool = true
	for child: Node in copy.get_children():
		var piece: MeshInstance3D = child as MeshInstance3D
		if piece == null:
			continue
		var box: AABB = Transform3D(basis, Vector3.ZERO) * piece.transform * piece.mesh.get_aabb()
		result = box if first else result.merge(box)
		first = false
	return result
