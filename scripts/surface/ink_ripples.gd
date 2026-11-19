class_name InkRipples
extends Node3D
## Las ondas de tinta (F3-01, D-061): mientras el juego no suena, lo que suena se
## ve. Cada ruido abre dos aros de tinta desde donde sonó hasta lo lejos que se
## oye, uno detrás del otro, y se borran. Es de cada equipo: no se replica (los
## ruidos que no son pasos los manda el anfitrión, ver [Stimuli]).
##
## Se puede quitar en los ajustes ([member Settings.sound_ripples]); cuando haya
## sonido quedará como ayuda de accesibilidad.

const GROUP: StringName = &"ondas_de_tinta"
const SHADER: String = "res://assets/shaders/onda.gdshader"
const NOISE: String = "res://assets/textures/ruido_trazo.png"
## Lo que dura una onda y lo que tarda la segunda.
const LIFE: float = 0.8
const SECOND_DELAY: float = 0.14
## Desde qué parte del alcance empieza a abrirse.
const START_SHARE: float = 0.12
## Lo alto de la banda: crece con el radio para que de lejos se siga viendo.
const BAND_BASE: float = 0.03
const BAND_PER_METER: float = 0.012
## Altura sobre el sitio del ruido.
const LIFT: float = 0.18
## Como mucho, tantas a la vez (las más viejas se reciclan).
const MAX_RINGS: int = 40
const SEGMENTS: int = 72

static var _mesh: ArrayMesh

## Para las capturas: los aros se quedan como están.
var paused: bool = false

var _material: ShaderMaterial
## Cada aro: {node, center, radius, strength, age (puede empezar negativa)}.
var _rings: Array[Dictionary] = []


## Las ondas de la escena, si las hay.
static func find(tree: SceneTree) -> InkRipples:
	return tree.get_first_node_in_group(GROUP) as InkRipples


## Lo fuerte que se dibuja un ruido de clase [param kind] que se oye a [param radius] m.
static func strength_of(kind: StringName, radius: float) -> float:
	var base: float = clampf(0.3 + radius / 30.0, 0.3, 1.0)
	if kind == NoiseRules.STEP:
		base *= 0.75
	return base


func _ready() -> void:
	add_to_group(GROUP)
	_material = ShaderMaterial.new()
	_material.shader = load(SHADER)
	_material.set_shader_parameter("ruido", load(NOISE))


func _process(delta: float) -> void:
	var index: int = 0
	while index < _rings.size():
		var ring: Dictionary = _rings[index]
		ring["age"] = float(ring["age"]) + (0.0 if paused else delta)
		var node: MeshInstance3D = ring["node"]
		var age: float = ring["age"]
		if age < 0.0:
			node.visible = false
			index += 1
			continue
		if age >= LIFE:
			node.queue_free()
			_rings.remove_at(index)
			continue
		var life: float = age / LIFE
		var grown: float = 1.0 - (1.0 - life) * (1.0 - life)
		var radius: float = float(ring["radius"]) * lerpf(START_SHARE, 1.0, grown)
		var band: float = BAND_BASE + BAND_PER_METER * float(ring["radius"])
		node.visible = true
		node.position = ring["center"]
		node.scale = Vector3(radius, band, radius)
		node.set_instance_shader_parameter(&"vida", life)
		index += 1


## Suena algo en [param position] que se oye a [param radius] metros, con
## [param strength] de 0 a 1. [param age]: lo que lleva ya abierta (las capturas).
func add(position: Vector3, radius: float, strength: float = 0.6, age: float = 0.0) -> void:
	if radius <= 0.3 or not Settings.sound_ripples:
		return
	for delay: float in [0.0, SECOND_DELAY]:
		var node: MeshInstance3D = MeshInstance3D.new()
		node.mesh = _ring_mesh()
		node.material_override = _material
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.visible = false
		node.set_instance_shader_parameter(&"fuerza", strength * (1.0 if delay == 0.0 else 0.6))
		node.set_instance_shader_parameter(&"semilla", randf() * 10.0)
		node.set_instance_shader_parameter(&"vueltas", maxf(2.0, radius * 0.9))
		add_child(node)
		(
			_rings
			. append(
				{
					"node": node,
					"center": position + Vector3.UP * LIFT,
					"radius": radius,
					"age": age - delay,
				}
			)
		)
	while _rings.size() > MAX_RINGS:
		(_rings[0]["node"] as Node).queue_free()
		_rings.remove_at(0)


## Cuántos aros hay ahora (para las pruebas).
func ring_count() -> int:
	return _rings.size()


## Una banda de radio 1 y alto 1, centrada: UV.x da la vuelta y UV.y la cruza.
static func _ring_mesh() -> ArrayMesh:
	if _mesh != null:
		return _mesh
	var vertices: PackedVector3Array = PackedVector3Array()
	var uvs: PackedVector2Array = PackedVector2Array()
	var indices: PackedInt32Array = PackedInt32Array()
	for i: int in SEGMENTS + 1:
		var angle: float = TAU * i / SEGMENTS
		var around: Vector3 = Vector3(cos(angle), 0.0, sin(angle))
		vertices.append(around + Vector3.DOWN * 0.5)
		vertices.append(around + Vector3.UP * 0.5)
		uvs.append(Vector2(float(i) / SEGMENTS, 0.0))
		uvs.append(Vector2(float(i) / SEGMENTS, 1.0))
		if i < SEGMENTS:
			var a: int = i * 2
			indices.append_array([a, a + 1, a + 2, a + 1, a + 3, a + 2])
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	_mesh = ArrayMesh.new()
	_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return _mesh
