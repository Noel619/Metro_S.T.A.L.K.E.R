class_name BackpackView
extends Node3D
## La mochila abierta (F3-03, README 10.2: "la mochila abierta, en 3D"): la lona con
## su cuadrícula de 6 × 5 delante de ti, sobre las rodillas, con cada cosa en su sitio
## (su modelo, pequeño) y, debajo, los tres huecos del cinturón. Con el ratón se señala
## una cosa (se levanta un poco) y con el botón izquierdo se coge; I o Esc la cierran.
## El tiempo no se para.

signal closed

## Lo que mide cada casilla en la vista y dónde va la lona (en el marco de la cámara).
const CELL: float = 0.045
const DISTANCE: float = 0.4
const DROP: float = 0.13
const TILT: float = deg_to_rad(-48.0)
const CANVAS: Color = Color("#6b6250")
const LINE: Color = Color("#3e382d")
const BELT_GAP: float = 0.035
## Lo que se levanta lo señalado.
const HOVER_LIFT: float = 0.012

var pack: PlayerPack

var _camera: Camera3D
var _items: Node3D
var _hover: int = -1
var _hover_belt: int = -1
## Cada cosa dibujada: índice de la mochila (o -1 - hueco del cinturón) -> nodo.
var _drawn: Dictionary = {}


## Abre la vista delante de [param camera].
func open(owner_pack: PlayerPack, camera: Camera3D) -> void:
	pack = owner_pack
	_camera = camera
	name = "MochilaAbierta"
	position = Vector3(0.0, -DROP, -DISTANCE)
	rotation.x = TILT
	camera.add_child(self)
	_build_canvas()
	_items = Node3D.new()
	_items.name = "Cosas"
	add_child(_items)
	_refresh()
	pack.changed.connect(_refresh)
	if DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func close() -> void:
	if DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	closed.emit()
	queue_free()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"backpack") or event.is_action_pressed(&"pause"):
		close()
		get_viewport().set_input_as_handled()
		return
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion != null:
		_point_at(motion.position)
		return
	var click: InputEventMouseButton = event as InputEventMouseButton
	if click != null and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
		_point_at(click.position)
		if _hover >= 0:
			pack.take(_hover)
			close()
		elif _hover_belt >= 0:
			pack.belt_key(_hover_belt)
			close()
		get_viewport().set_input_as_handled()


## La casilla de la lona bajo un punto de la pantalla (o (-1, -1)).
func cell_under(screen: Vector2) -> Vector2i:
	var local: Vector2 = _on_canvas(screen)
	if local.x == INF:
		return Vector2i(-1, -1)
	var cell: Vector2i = Vector2i(floori(local.x / CELL), floori(local.y / CELL))
	if cell.x < 0 or cell.y < 0 or cell.x >= Backpack.SIZE.x or cell.y >= Backpack.SIZE.y:
		return Vector2i(-1, -1)
	return cell


func _point_at(screen: Vector2) -> void:
	var contents: Backpack = pack.contents()
	var cell: Vector2i = cell_under(screen)
	var hover: int = contents.index_at(cell) if cell.x >= 0 else -1
	var belt: int = -1
	if hover < 0:
		var local: Vector2 = _on_canvas(screen)
		var belt_top: float = Backpack.SIZE.y * CELL + BELT_GAP
		if local.x != INF and local.y >= belt_top and local.y <= belt_top + CELL * 2.0:
			belt = clampi(floori(local.x / (CELL * 2.0)), 0, Backpack.BELT_SLOTS - 1)
	if hover != _hover or belt != _hover_belt:
		_hover = hover
		_hover_belt = belt
		_lift()


## Un punto de la pantalla sobre la lona, en metros desde su esquina de arriba a la
## izquierda (x a la derecha, y hacia abajo); INF si no la toca.
func _on_canvas(screen: Vector2) -> Vector2:
	if _camera == null:
		return Vector2(INF, INF)
	var from: Vector3 = _camera.project_ray_origin(screen)
	var direction: Vector3 = _camera.project_ray_normal(screen)
	var plane: Plane = Plane(global_basis.y.normalized(), global_position)
	var hit: Variant = plane.intersects_ray(from, direction)
	if hit == null:
		return Vector2(INF, INF)
	var local: Vector3 = global_transform.affine_inverse() * (hit as Vector3)
	var width: float = Backpack.SIZE.x * CELL
	var height: float = Backpack.SIZE.y * CELL
	return Vector2(local.x + width * 0.5, local.z + height * 0.5)


func _build_canvas() -> void:
	var width: float = Backpack.SIZE.x * CELL
	var height: float = Backpack.SIZE.y * CELL
	var canvas: MeshInstance3D = MeshInstance3D.new()
	canvas.name = "Lona"
	var quad: QuadMesh = QuadMesh.new()
	quad.size = Vector2(width + 0.03, height + BELT_GAP + CELL * 2.0 + 0.03)
	quad.orientation = PlaneMesh.FACE_Y
	canvas.mesh = quad
	canvas.position = Vector3(0.0, -0.002, (BELT_GAP + CELL * 2.0) * 0.5)
	canvas.material_override = _flat(CANVAS)
	add_child(canvas)
	var lines: ImmediateMesh = ImmediateMesh.new()
	lines.surface_begin(Mesh.PRIMITIVE_LINES)
	for x: int in Backpack.SIZE.x + 1:
		lines.surface_add_vertex(Vector3(x * CELL - width * 0.5, 0.0, -height * 0.5))
		lines.surface_add_vertex(Vector3(x * CELL - width * 0.5, 0.0, height * 0.5))
	for y: int in Backpack.SIZE.y + 1:
		lines.surface_add_vertex(Vector3(-width * 0.5, 0.0, y * CELL - height * 0.5))
		lines.surface_add_vertex(Vector3(width * 0.5, 0.0, y * CELL - height * 0.5))
	# Los huecos del cinturón, debajo.
	var top: float = height * 0.5 + BELT_GAP
	for slot: int in Backpack.BELT_SLOTS + 1:
		var x: float = slot * CELL * 2.0 - width * 0.5
		lines.surface_add_vertex(Vector3(x, 0.0, top))
		lines.surface_add_vertex(Vector3(x, 0.0, top + CELL * 2.0))
	for z: float in [top, top + CELL * 2.0]:
		lines.surface_add_vertex(Vector3(-width * 0.5, 0.0, z))
		lines.surface_add_vertex(Vector3(-width * 0.5 + CELL * 2.0 * Backpack.BELT_SLOTS, 0.0, z))
	lines.surface_end()
	var grid: MeshInstance3D = MeshInstance3D.new()
	grid.name = "Cuadricula"
	grid.mesh = lines
	grid.material_override = _flat(LINE)
	add_child(grid)


func _refresh() -> void:
	for child: Node in _items.get_children():
		child.queue_free()
	_drawn.clear()
	var contents: Backpack = pack.contents()
	var width: float = Backpack.SIZE.x * CELL
	var height: float = Backpack.SIZE.y * CELL
	for index: int in contents.entries.size():
		var entry: Dictionary = contents.entries[index]
		var data: ItemData = ItemState.load_data(StringName(entry["estado"].get("id", "")))
		if data == null:
			continue
		var shape: Array[Vector2i] = Backpack.shape_of(data, bool(entry["girado"]))
		var span: Vector2i = Vector2i.ONE
		for part: Vector2i in shape:
			span = Vector2i(maxi(span.x, part.x + 1), maxi(span.y, part.y + 1))
		var cell: Vector2i = entry["celda"]
		var center: Vector3 = Vector3(
			(cell.x + span.x * 0.5) * CELL - width * 0.5,
			0.0,
			(cell.y + span.y * 0.5) * CELL - height * 0.5
		)
		_drawn[index] = _place_model(data, center, Vector2(span) * CELL, bool(entry["girado"]))
	for slot: int in Backpack.BELT_SLOTS:
		if contents.belt[slot].is_empty():
			continue
		var data: ItemData = ItemState.load_data(StringName(contents.belt[slot].get("id", "")))
		if data == null:
			continue
		var center: Vector3 = Vector3(
			(slot * 2.0 + 1.0) * CELL - width * 0.5, 0.0, height * 0.5 + BELT_GAP + CELL
		)
		_drawn[-1 - slot] = _place_model(data, center, Vector2(CELL * 2.0, CELL * 2.0), false)
	_lift()


## El modelo de una cosa, quieto y sin física, encajado en su hueco.
func _place_model(data: ItemData, center: Vector3, room: Vector2, rotated: bool) -> Node3D:
	var holder: Node3D = Node3D.new()
	holder.position = center
	_items.add_child(holder)
	var model: Node3D = load(WorldItems.MODELS_DIR + data.model + ".glb").instantiate()
	for body: Node in model.find_children("*", "CollisionObject3D", true, false):
		(body as CollisionObject3D).process_mode = Node.PROCESS_MODE_DISABLED
		if body is RigidBody3D:
			(body as RigidBody3D).freeze = true
	var bounds: AABB = _bounds_of(model)
	var footprint: float = maxf(bounds.size.x, bounds.size.z)
	var fit: float = minf(room.x, room.y) * 0.9 / maxf(footprint, 0.01)
	model.scale = Vector3.ONE * minf(fit, 1.0)
	model.rotation.y = PI * 0.5 if rotated else 0.0
	model.position = (
		-bounds.get_center() * model.scale.x + Vector3.UP * bounds.size.y * 0.5 * model.scale.x
	)
	holder.add_child(model)
	return holder


func _lift() -> void:
	for key: int in _drawn:
		var node: Node3D = _drawn[key]
		var raised: bool = key == _hover or (key < 0 and -1 - key == _hover_belt)
		node.position.y = HOVER_LIFT if raised else 0.0


static func _bounds_of(model: Node3D) -> AABB:
	var bounds: AABB = AABB()
	var first: bool = true
	for node: Node in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = node as MeshInstance3D
		var box: AABB = _relative(mesh, model) * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	return bounds


static func _relative(node: Node3D, ancestor: Node3D) -> Transform3D:
	var result: Transform3D = Transform3D.IDENTITY
	var current: Node = node
	while current != null and current != ancestor:
		if current is Node3D:
			result = (current as Node3D).transform * result
		current = current.get_parent()
	return result


static func _flat(color: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	material.no_depth_test = false
	return material
