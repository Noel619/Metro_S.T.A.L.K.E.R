class_name PerceptionDebug
extends Node3D
## La herramienta de depuración de la percepción (F3-09, README 13.4): herramienta
## de desarrollo, no interfaz del juego. Con F3 dibuja, por encima de todo, lo que
## percibe y sabe cada agente:
## - el cono de vista, hasta donde vería a alguien de pie andando con esta luz;
## - lo que olería: la zona de la que le llega el olor con este viento;
## - los últimos ruidos que le llegaron (azul si los oyó, gris si no);
## - lo que recuerda: una cruz por cosa, más grande cuanto más seguro (rojo, lo
##   visto; azul, lo oído; verde, lo olido; amarillo, lo que le avisaron);
## - las marcas de olor de los rastros (puntos verdes);
## - y, encima, su estado y por qué hace lo que hace.
## Solo hay datos en el anfitrión, que es quien simula la IA.

const GROUP: StringName = &"percepcion"
const COLORS: Dictionary = {
	Percept.SIGHT: Color(0.85, 0.2, 0.15),
	Percept.HEARING: Color(0.2, 0.45, 0.9),
	Percept.SMELL: Color(0.2, 0.7, 0.3),
	Percept.TOLD: Color(0.9, 0.75, 0.15),
}
const REFRESH_SECONDS: float = 0.1
const ARC_STEPS: int = 24

var _mesh: ImmediateMesh
var _lines: MeshInstance3D
var _labels: Dictionary = {}
var _clock: float = 0.0


func _ready() -> void:
	visible = false
	_mesh = ImmediateMesh.new()
	_lines = MeshInstance3D.new()
	_lines.name = "Lineas"
	_lines.mesh = _mesh
	_lines.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	material.no_depth_test = true
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_lines.material_override = material
	add_child(_lines)


func _unhandled_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_F3:
		toggle()


## Muestra u oculta lo que perciben los agentes.
func toggle() -> void:
	visible = not visible
	if not visible:
		_mesh.clear_surfaces()
		for label: Label3D in _labels.values():
			label.queue_free()
		_labels.clear()


func _process(delta: float) -> void:
	if not visible:
		return
	_clock -= delta
	if _clock > 0.0:
		return
	_clock = REFRESH_SECONDS
	_mesh.clear_surfaces()
	_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	var env: SurfaceEnv = SurfaceEnv.find(get_tree())
	var alive: Array[Perception] = []
	for node: Node in get_tree().get_nodes_in_group(GROUP):
		var perception: Perception = node as Perception
		if perception.body == null or not is_instance_valid(perception.body):
			continue
		alive.append(perception)
		_draw_agent(perception, env)
	_draw_trails()
	_mesh.surface_end()
	_update_labels(alive)


func _draw_agent(perception: Perception, env: SurfaceEnv) -> void:
	var eye: Vector3 = perception.eye()
	var forward: Vector3 = perception.forward()
	var light: float = Visibility.ambient(env.hour()) if env != null else 1.0
	var weather: Weather = env.weather if env != null else null
	var factor: float = weather.sight_factor() if weather != null else 1.0
	var reach: float = Visibility.BASE_RANGE * light * factor * perception.sight_factor
	var half: float = deg_to_rad(perception.fov_degrees * 0.5)
	var sight: Color = Color(COLORS[Percept.SIGHT], 0.5)
	var last: Vector3 = eye
	for step: int in ARC_STEPS + 1:
		var angle: float = -half + 2.0 * half * step / ARC_STEPS
		var point: Vector3 = eye + forward.rotated(Vector3.UP, angle) * reach
		if step == 0 or step == ARC_STEPS:
			_line(eye, point, sight)
		if step > 0:
			_line(last, point, sight)
		last = point
	# El olor: de dónde le llegaría (los sitios desde los que alguien se olería).
	var smell: Color = Color(COLORS[Percept.SMELL], 0.45)
	var previous: Vector3 = Vector3.INF
	for step: int in ARC_STEPS * 2 + 1:
		var angle: float = TAU * step / (ARC_STEPS * 2)
		var from_target: Vector3 = Vector3(cos(angle), 0.0, sin(angle))
		var reach_smell: float = Perception.smell_range(
			weather, from_target, perception.smell_factor
		)
		var point: Vector3 = perception.body.global_position - from_target * reach_smell
		point.y = eye.y
		if previous != Vector3.INF:
			_line(previous, point, smell)
		previous = point
	for entry: Dictionary in perception.heard:
		var event: NoiseEvent = entry["event"]
		var heard: bool = eye.distance_to(event.position) <= float(entry["heard"])
		var color: Color = (
			Color(COLORS[Percept.HEARING], 0.7) if heard else Color(0.5, 0.5, 0.5, 0.4)
		)
		_circle(event.position + Vector3.UP * 0.2, float(entry["heard"]), color)
		if heard:
			_line(event.position, eye, color)
	for key: String in perception.knowledge.facts:
		var fact: Percept = perception.knowledge.facts[key]
		var color: Color = COLORS.get(fact.sense, Color.WHITE)
		_cross(fact.position + Vector3.UP * 0.3, 0.3 + fact.certainty * 0.9, color)
	var best: Percept = perception.knowledge.best()
	if best != null:
		_line(eye, best.position + Vector3.UP * 0.3, Color(1.0, 1.0, 1.0, 0.6))


func _draw_trails() -> void:
	var tracks: Tracks = Tracks.find(get_tree())
	if tracks == null:
		return
	for mark: Dictionary in tracks.marks:
		var fresh: float = 1.0 - tracks.age_of(mark)
		var color: Color = (
			Color(0.7, 0.1, 0.1, fresh) if mark["blood"] else Color(0.2, 0.7, 0.3, fresh)
		)
		_cross(mark["position"] + Vector3.UP * 0.05, 0.15, color)


func _update_labels(alive: Array[Perception]) -> void:
	for perception: Perception in alive:
		var label: Label3D = _labels.get(perception)
		if label == null:
			label = Label3D.new()
			label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			label.no_depth_test = true
			label.fixed_size = true
			label.pixel_size = 0.0012
			label.font_size = 28
			label.outline_size = 6
			add_child(label)
			_labels[perception] = label
		label.global_position = perception.body.global_position + Vector3.UP * 1.6
		label.text = _summary(perception)
	for perception: Variant in _labels.keys():
		if not alive.has(perception):
			(_labels[perception] as Label3D).queue_free()
			_labels.erase(perception)


static func _summary(perception: Perception) -> String:
	var lines: PackedStringArray = []
	var owner: Node = perception.body
	if owner.has_method("debug_state"):
		lines.append(str(owner.call("debug_state")))
	var seen: PackedStringArray = []
	for peer: int in perception.awareness:
		if float(perception.awareness[peer]) > 0.0:
			seen.append("j%d %d%%" % [peer, roundi(float(perception.awareness[peer]) * 100.0)])
	if not seen.is_empty():
		lines.append("se fija: " + ", ".join(seen))
	var best: Percept = perception.knowledge.best()
	if best != null:
		lines.append(
			"sabe: %s por %s (%d%%)" % [best.kind, best.sense, roundi(best.certainty * 100.0)]
		)
	return "\n".join(lines)


func _line(from: Vector3, to: Vector3, color: Color) -> void:
	_mesh.surface_set_color(color)
	_mesh.surface_add_vertex(from)
	_mesh.surface_set_color(color)
	_mesh.surface_add_vertex(to)


func _circle(center: Vector3, radius: float, color: Color) -> void:
	var last: Vector3 = center + Vector3(radius, 0.0, 0.0)
	for step: int in range(1, ARC_STEPS + 1):
		var angle: float = TAU * step / ARC_STEPS
		var point: Vector3 = center + Vector3(cos(angle), 0.0, sin(angle)) * radius
		_line(last, point, color)
		last = point


func _cross(center: Vector3, size: float, color: Color) -> void:
	_line(center + Vector3(-size, 0.0, 0.0), center + Vector3(size, 0.0, 0.0), color)
	_line(center + Vector3(0.0, 0.0, -size), center + Vector3(0.0, 0.0, size), color)
	_line(center, center + Vector3.UP * size, color)
