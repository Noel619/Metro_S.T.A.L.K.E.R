class_name Stimuli
extends Node
## Lo que pasa en la superficie y se puede percibir (F3-09): de momento, los
## ruidos. Vive en el nivel y solo cuenta en el anfitrión, que es quien simula la
## IA: los sentidos de cada agente escuchan [signal noise_made].
##
## Los ruidos que no son pasos (una puerta, la palanca, una botella que se rompe)
## se ven además en todos los equipos como ondas de tinta ([InkRipples]); los
## pasos, cada equipo los dibuja por su cuenta ([Footsteps]).

signal noise_made(event: NoiseEvent)

const GROUP: StringName = &"estimulos"
## Lo que se guardan los últimos ruidos (para la depuración).
const KEEP_SECONDS: float = 4.0

## Los últimos ruidos, del más viejo al más nuevo.
var recent: Array[NoiseEvent] = []

var _next_id: int = 1


## Los estímulos de la escena, si los hay.
static func find(tree: SceneTree) -> Stimuli:
	return tree.get_first_node_in_group(GROUP) as Stimuli


func _ready() -> void:
	add_to_group(GROUP)


func _process(_delta: float) -> void:
	var now: float = clock()
	while not recent.is_empty() and now - recent[0].time > KEEP_SECONDS:
		recent.pop_front()


## Suena algo en [param position] que se oye a [param radius] metros. Solo en el
## anfitrión; con [param show], todos los equipos lo ven como ondas de tinta.
func make_noise(
	position: Vector3,
	radius: float,
	kind: StringName,
	source: int = 0,
	show: bool = true,
	emitter: Object = null
) -> NoiseEvent:
	if radius <= 0.0 or not multiplayer.is_server():
		return null
	var event: NoiseEvent = NoiseEvent.new()
	event.id = _next_id
	_next_id += 1
	event.position = position
	event.radius = radius
	event.kind = kind
	event.source = source
	event.emitter = emitter.get_instance_id() if emitter != null else 0
	event.time = clock()
	recent.append(event)
	noise_made.emit(event)
	if show:
		_show.rpc(position, radius, kind)
	return event


## Segundos desde que arrancó el juego: el reloj de los estímulos y de la memoria.
static func clock() -> float:
	return Time.get_ticks_msec() / 1000.0


@rpc("authority", "call_local", "unreliable")
func _show(position: Vector3, radius: float, kind: StringName) -> void:
	var ripples: InkRipples = InkRipples.find(get_tree())
	if ripples != null:
		ripples.add(position, radius, InkRipples.strength_of(kind, radius))
