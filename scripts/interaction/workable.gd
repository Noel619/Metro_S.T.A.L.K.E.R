class_name Workable
extends Node
## Lo que se trabaja con algo en la mano (o con las manos): la escoba sobre el
## polvo, la palanca en la persiana, el destornillador en un tornillo…
##
## Es hijo de un cuerpo físico, como [Interactable]. El jugador, con el botón
## izquierdo pulsado, convierte el movimiento del ratón en trabajo según el
## [member gesture] y le pide al anfitrión que lo aplique; aquí solo se dice qué
## herramientas valen y se avisa (en el anfitrión) de cuánto se ha trabajado. Lo
## que pasa después lo decide quien escuche [signal worked].

## Alguien ha trabajado esto: [param amount] en unidades del gesto (una pasada
## de escoba, una vuelta de destornillador…), en [param point] (en el mundo). En
## [constant Gesture.CIRCLE] lleva signo: positivo es en el sentido del reloj
## (apretar).
signal worked(player: Node, tool: StringName, amount: float, point: Vector3)

## Pasadas largas (barrer, fregar), frotar corto (cepillar, limpiar contactos),
## círculos (atornillar, enroscar), tirar hacia abajo (la palanca) o mantener
## pulsado (comer, encender).
enum Gesture { STROKE, SCRUB, CIRCLE, PULL, HOLD }

## La "herramienta" de quien no lleva nada.
const HANDS: StringName = &"manos"

## Con qué se trabaja: el [member ItemData.tool] de lo que se lleva, o
## [constant HANDS].
@export var tools: Array[StringName] = []
@export var gesture: Gesture = Gesture.STROKE
@export var enabled: bool = true


## El componente de [param body] que acepta [param tool], si lo hay.
static func find(body: Node, tool: StringName) -> Workable:
	if body == null:
		return null
	for child: Node in body.get_children():
		var workable: Workable = child as Workable
		if workable != null and workable.accepts(tool):
			return workable
	return null


func accepts(tool: StringName) -> bool:
	return enabled and tools.has(tool)


## Aplica trabajo. Solo cuenta en el anfitrión.
func work(player: Node, tool: StringName, amount: float, point: Vector3 = Vector3.INF) -> void:
	if multiplayer.is_server() and accepts(tool) and amount != 0.0:
		worked.emit(player, tool, amount, point)
