class_name RepairStep
extends Resource
## Un paso de una reparación del banco de trabajo (F2-07): con qué se hace,
## con qué gesto, cuánto trabajo pide y qué pieza cambia al hacerlo.

## Lo que pasa con la pieza al terminar el paso (y mientras se hace).
enum Effect { NONE, UNSCREW, SCREW, REMOVE, PUT_BACK, CLEAN, SEW }

## Lo que se escribe en la nota del banco: "Quitar los tornillos".
@export var label: String = ""
## Con qué se trabaja ([member ItemData.tool] o [constant Workable.HANDS]).
@export var tool: StringName = &"manos"
@export var gesture: Workable.Gesture = Workable.Gesture.STROKE
## Trabajo que pide, en unidades del gesto (vueltas, pasadas, segundos…).
@export var work: float = 1.0
## En los círculos: 1 apretar (sentido del reloj), -1 aflojar; 0, cualquiera.
@export_range(-1, 1) var direction: int = 0
## Los nodos del modelo que cambian (por su nombre; los que empiezan así).
@export var part: String = ""
@export var effect: Effect = Effect.NONE
