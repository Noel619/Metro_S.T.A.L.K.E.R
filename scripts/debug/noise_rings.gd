class_name NoiseRings
extends Node3D
## Dibuja cada ruido ([signal EventBus.noise_made]) como un círculo rojo en el
## suelo que crece hasta donde llegaría
## ([constant SurfaceMotion.METERS_PER_LOUDNESS]) y se apaga. Herramienta de
## desarrollo: deja ver lo que suenan los pasos mientras no haya nadie que los
## oiga (F3-09). Los ruidos solo existen en el anfitrión, así que solo él los ve.

## Lo que dura cada círculo y lo que tarda en llegar a su tamaño.
const LIFE: float = 1.2
const GROW: float = 0.35
## El rojo de lo importante (docs/ESTILO.md): un ruido es un peligro.
const COLOR: Color = Color("#c8323c")
## Ancho de la línea, en metros, y vueltas del círculo.
const WIDTH: float = 0.07
const SEGMENTS: int = 48
## Por debajo de este radio no se dibuja.
const MIN_RADIUS: float = 0.1

## Con esto, los círculos se quedan enteros y sin apagarse (para las capturas).
var frozen: bool = false


func _ready() -> void:
	EventBus.noise_made.connect(_on_noise)


func _exit_tree() -> void:
	if EventBus.noise_made.is_connected(_on_noise):
		EventBus.noise_made.disconnect(_on_noise)


## Dibuja un ruido de [param loudness] en [param where].
func show_noise(where: Vector3, loudness: float) -> void:
	var radius: float = loudness * SurfaceMotion.METERS_PER_LOUDNESS
	if radius < MIN_RADIUS or not visible:
		return
	var ring: MeshInstance3D = MeshInstance3D.new()
	ring.mesh = _ring_mesh(radius)
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.no_depth_test = true
	material.albedo_color = COLOR
	ring.material_override = material
	add_child(ring)
	ring.global_position = where + Vector3.UP * 0.04
	if frozen:
		return
	ring.scale = Vector3.ONE * 0.15
	var tween: Tween = ring.create_tween()
	tween.tween_property(ring, "scale", Vector3.ONE, GROW).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(material, "albedo_color:a", 0.0, LIFE)
	tween.tween_callback(ring.queue_free)


## Quita los círculos que haya.
func clear() -> void:
	for child: Node in get_children():
		child.queue_free()


func _on_noise(where: Vector3, loudness: float, _source: Node) -> void:
	show_noise(where, loudness)


## Un anillo plano de [param radius] metros, tumbado en el suelo.
static func _ring_mesh(radius: float) -> ArrayMesh:
	var tool: SurfaceTool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for index: int in SEGMENTS + 1:
		var angle: float = TAU * float(index) / float(SEGMENTS)
		var direction: Vector3 = Vector3(cos(angle), 0.0, sin(angle))
		tool.add_vertex(direction * maxf(0.0, radius - WIDTH / 2.0))
		tool.add_vertex(direction * (radius + WIDTH / 2.0))
	return tool.commit()
