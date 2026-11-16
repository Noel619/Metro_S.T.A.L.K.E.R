class_name CityOverlays
extends Node3D
## Capas de ayuda de la maqueta, dibujadas encima de la ciudad (herramienta de desarrollo;
## en el juego no hay mapas): las rutas del plano, la rejilla de sectores con sus nombres y
## los de las zonas, y los hitos que se ven desde donde está la cámara.
##
## Las líneas son cintas 3D sin luz ni niebla; los rótulos se dibujan en 2D, encima de la
## imagen, para que se lean con cualquier niebla.

## Un color por destino de las rutas (R1, R2, R3, R4), como en la hoja de rutas.
const ROUTE_COLORS: Array[Color] = [
	Color("#b23a34"), Color("#2c6096"), Color("#408048"), Color("#96601e"), Color("#6e408c")
]
const FONT_PATH: String = "res://assets/fonts/pt_sans/PTSans-Bold.ttf"
const LABEL_SIZE: int = 18
const OUTLINE: Color = Color(0.96, 0.93, 0.86)

var routes: Node3D
var sectors: Node3D
var landmarks: Node3D
## Los puntos ciegos de la última comprobación de hitos (ver [method landmark_survey]).
var blind_spots: Node3D

var _plan: CityPlan
var _city: City
var _landmarks: Array[Dictionary] = []
## Rótulos: texto, posición en el mundo, color, tamaño y capa.
var _labels: Array[Dictionary] = []
var _canvas: Control
var _font: Font
var _labels_drawn: bool = false


## Construye las tres capas (empiezan ocultas).
func build(city: City) -> void:
	_city = city
	_plan = city.plan
	_font = load(FONT_PATH)
	routes = _layer("Rutas")
	sectors = _layer("Sectores")
	landmarks = _layer("Hitos")
	var layer: CanvasLayer = CanvasLayer.new()
	layer.name = "Rotulos"
	layer.layer = 5
	add_child(layer)
	_canvas = Control.new()
	_canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas.draw.connect(_draw_labels)
	layer.add_child(_canvas)
	_build_routes()
	_build_sectors()
	_build_landmarks()


## Qué hitos se ven desde [param eye] (sin contar la niebla: los hitos la atraviesan). Deja
## a la vista solo sus rótulos y devuelve sus nombres. Sirve para comprobar la regla del
## plano: desde cualquier punto se ven al menos dos hitos para orientarse.
func update_visible_landmarks(eye: Vector3, exclude: Array[RID]) -> PackedStringArray:
	var visible_names: PackedStringArray = []
	var space: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	for landmark: Dictionary in _landmarks:
		var target: Vector3 = landmark["target"]
		var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(eye, target)
		query.exclude = exclude
		var hit: Dictionary = space.intersect_ray(query)
		# Si el rayo choca cerca del destino, ha dado en el propio hito.
		var seen: bool = hit.is_empty() or Vector3(hit["position"]).distance_to(target) < 15.0
		(landmark["label"] as Dictionary)["seen"] = seen
		if seen:
			visible_names.append(landmark["name"])
	return visible_names


## Comprueba la regla de los hitos en toda la ciudad: desde cada punto de una rejilla de
## [param spacing] metros (a la altura de los ojos, fuera de los edificios) cuenta los hitos
## a la vista. Marca los puntos ciegos (rojo: ninguno; naranja: uno) en la capa "Ciegos" y
## devuelve el resumen: puntos, cuántos ven dos o más, y el reparto por zonas.
func landmark_survey(spacing: float, exclude: Array[RID]) -> Dictionary:
	var space: PhysicsDirectSpaceState3D = get_world_3d().direct_space_state
	var points: int = 0
	var good: int = 0
	var by_zone: Dictionary = {}
	var marks: Array[Array] = []
	var x: float = spacing * 0.5
	while x < _plan.size.x:
		var y: float = spacing * 0.5
		while y < _plan.size.y:
			var point: Vector2 = Vector2(x, y)
			y += spacing
			var ground: Dictionary = space.intersect_ray(
				PhysicsRayQueryParameters3D.create(
					CityPlan.to_world(point, 400.0), CityPlan.to_world(point, -60.0)
				)
			)
			if ground.is_empty() or not _city.building_of(ground["collider"]).is_empty():
				continue
			var eye: Vector3 = Vector3(ground["position"]) + Vector3.UP * MockupWalker.EYE_HEIGHT
			var seen: int = update_visible_landmarks(eye, exclude).size()
			var zone: String = _plan.zone_label(point)
			var tally: Vector2i = by_zone.get(zone, Vector2i.ZERO)
			by_zone[zone] = tally + Vector2i(1, 1 if seen >= 2 else 0)
			points += 1
			if seen >= 2:
				good += 1
			else:
				marks.append([eye, seen])
		x += spacing
	_mark_blind_spots(marks, spacing)
	return {"puntos": points, "con_dos": good, "zonas": by_zone, "ciegos": marks.size()}


## Una baldosa por punto ciego, del tamaño de la rejilla (se lee desde el aire).
func _mark_blind_spots(marks: Array[Array], spacing: float) -> void:
	if blind_spots != null:
		blind_spots.free()
	blind_spots = _layer("Ciegos")
	blind_spots.visible = true
	var post: BoxMesh = BoxMesh.new()
	post.size = Vector3(spacing * 0.9, 0.6, spacing * 0.9)
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	material.disable_fog = true
	var multimesh: MultiMesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	multimesh.mesh = post
	multimesh.instance_count = marks.size()
	for i: int in marks.size():
		var place: Vector3 = Vector3(marks[i][0]) - Vector3.UP * (MockupWalker.EYE_HEIGHT - 0.5)
		multimesh.set_instance_transform(i, Transform3D(Basis(), place))
		var color: Color = Color("#c0392b") if int(marks[i][1]) == 0 else Color("#e08a1e")
		multimesh.set_instance_color(i, color)
	var instance: MultiMeshInstance3D = MultiMeshInstance3D.new()
	instance.multimesh = multimesh
	instance.material_override = material
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	blind_spots.add_child(instance)


func _process(_delta: float) -> void:
	# Se redibuja mientras se ve alguna capa y una vez más al ocultarlas todas (si no, los
	# rótulos se quedarían en pantalla, quietos, al cambiar de vista).
	var shown: bool = routes.visible or sectors.visible or landmarks.visible
	if _canvas != null and (shown or _labels_drawn):
		_canvas.queue_redraw()
	_labels_drawn = shown


## Las rutas del plano como una cinta por encima del suelo. Todas salen de la compuerta:
## cada una lleva su nombre a mitad de camino (escalonados para que no se pisen) y cada
## destino, el suyo al final.
func _build_routes() -> void:
	var destinations: PackedStringArray = []
	var per_destination: Dictionary = {}
	for route: Dictionary in _plan.data["rutas"]:
		var destination: String = route["destino"]
		if not destinations.has(destination):
			destinations.append(destination)
		var order: int = per_destination.get(destination, 0)
		per_destination[destination] = order + 1
		var color: Color = ROUTE_COLORS[destinations.find(destination) % ROUTE_COLORS.size()]
		color = color.lightened(0.18 * order)
		var line: PackedVector2Array = CityGeometry.subdivide(CityPlan.line(route["puntos"]), 3.0)
		routes.add_child(_ribbon(line, 3.0, 0.8, color))
		var middle: Vector2 = CityGeometry.point_along(line, CityGeometry.length(line) * 0.5).origin
		var text: String = "%s · %s" % [route["id"], route["nombre"]]
		var height: float = _city.surface_height(middle) + 6.0 + 7.0 * order
		_add_label(routes, text, CityPlan.to_world(middle, height), color, LABEL_SIZE)
		if order == 0:
			var end: Vector2 = line[line.size() - 1]
			var place: Vector3 = CityPlan.to_world(end, _city.surface_height(end) + 18.0)
			_add_label(routes, destination.to_upper(), place, color.darkened(0.3), LABEL_SIZE + 4)


## La rejilla de sectores sobre el terreno, con el nombre de cada uno y los de las zonas.
func _build_sectors() -> void:
	var grid: Vector2i = _plan.sector_grid()
	var color: Color = Color(0.1, 0.09, 0.12, 0.85)
	for column: int in grid.x + 1:
		var x: float = column * _plan.sector_size
		var line: PackedVector2Array = CityGeometry.subdivide(
			PackedVector2Array([Vector2(x, 0.0), Vector2(x, _plan.size.y)]), 4.0
		)
		sectors.add_child(_ribbon(line, 1.2, 0.4, color))
	for row: int in grid.y + 1:
		var y: float = row * _plan.sector_size
		var line: PackedVector2Array = CityGeometry.subdivide(
			PackedVector2Array([Vector2(0.0, y), Vector2(_plan.size.x, y)]), 4.0
		)
		sectors.add_child(_ribbon(line, 1.2, 0.4, color))
	for row: int in grid.y:
		for column: int in grid.x:
			var sector: Vector2i = Vector2i(column, row)
			var center: Vector2 = _plan.sector_rect(sector).get_center()
			var place: Vector3 = CityPlan.to_world(center, _plan.height_at(center) + 2.0)
			_add_label(sectors, CityPlan.sector_name(sector), place, color, LABEL_SIZE)
	for key: String in _plan.data["zonas"]:
		var zone: Dictionary = _plan.data["zonas"][key]
		if not zone.has("rotulo"):
			continue
		var point: Vector2 = Vector2(zone["rotulo"][0], zone["rotulo"][1])
		var text: String = "%s · %s" % [key, String(zone["nombre"]).to_upper()]
		var place: Vector3 = CityPlan.to_world(point, _plan.height_at(point) + 2.0)
		_add_label(sectors, text, place, Color("#7a1e18"), LABEL_SIZE + 6)


## Los hitos, rotulados encima de su punto más alto. Sus rótulos solo se ven si el hito
## está a la vista (ver [method update_visible_landmarks]).
func _build_landmarks() -> void:
	var color: Color = Color("#3a2a1e")
	var tops: Dictionary = {}
	for building: Dictionary in _plan.data["edificios"]:
		if CityPlan.is_landmark(building):
			var number: int = int(building["hito"])
			var top: float = float(building["cota"]) + _city.standing_height(building)
			tops[number] = maxf(tops.get(number, -INF), top)
	for key: String in _plan.data["hitos"]:
		var landmark: Dictionary = _plan.data["hitos"][key]
		var point: Vector2 = Vector2(landmark["pos"][0], landmark["pos"][1])
		var top: float = tops.get(key.to_int(), _city.surface_height(point) + 8.0)
		var target: Vector3 = CityPlan.to_world(point, top - 1.0)
		var text: String = "%s · %s" % [key, landmark["nombre"]]
		var label: Dictionary = _add_label(
			landmarks, text, target + Vector3.UP * 4.0, color, LABEL_SIZE
		)
		label["seen"] = false
		_landmarks.append({"name": landmark["nombre"], "target": target, "label": label})


func _layer(layer_name: String) -> Node3D:
	var layer: Node3D = Node3D.new()
	layer.name = layer_name
	layer.visible = false
	add_child(layer)
	return layer


func _add_label(layer: Node3D, text: String, world: Vector3, color: Color, size: int) -> Dictionary:
	var label: Dictionary = {
		"text": text, "world": world, "color": color, "size": size, "layer": layer
	}
	_labels.append(label)
	return label


## Dibuja en pantalla los rótulos de las capas visibles que tiene delante la cámara.
func _draw_labels() -> void:
	var camera: Camera3D = get_viewport().get_camera_3d()
	if camera == null:
		return
	for label: Dictionary in _labels:
		if not (label["layer"] as Node3D).visible or not label.get("seen", true):
			continue
		var world: Vector3 = label["world"]
		if camera.is_position_behind(world):
			continue
		var size: int = label["size"]
		var text: String = label["text"]
		var width: float = _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		var place: Vector2 = camera.unproject_position(world) - Vector2(width * 0.5, 0.0)
		_canvas.draw_string_outline(
			_font, place, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 6, OUTLINE
		)
		_canvas.draw_string(_font, place, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, label["color"])


## Una cinta plana que sigue el suelo (sin luz ni niebla, para que se lea siempre).
func _ribbon(line: PackedVector2Array, width: float, lift: float, color: Color) -> MeshInstance3D:
	var mesh: MeshBuffer = MeshBuffer.new()
	var tint: PackedColorArray = PackedColorArray([color])
	for i: int in line.size() - 1:
		var a: Vector2 = line[i]
		var b: Vector2 = line[i + 1]
		var side: Vector2 = (b - a).orthogonal().normalized() * width * 0.5
		var ha: float = _city.surface_height(a) + lift
		var hb: float = _city.surface_height(b) + lift
		(
			mesh
			. add_face(
				PackedVector3Array(
					[
						CityPlan.to_world(a - side, ha),
						CityPlan.to_world(b - side, hb),
						CityPlan.to_world(b + side, hb),
						CityPlan.to_world(a + side, ha),
					]
				),
				Vector3.UP,
				tint
			)
		)
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	material.vertex_color_is_srgb = true
	material.disable_fog = true
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.mesh = mesh.to_mesh(material)
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return instance
