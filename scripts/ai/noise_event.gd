class_name NoiseEvent
extends RefCounted
## Un ruido que acaba de sonar en la superficie: dónde, lo lejos que se oye (su
## alcance, ver [NoiseRules]), de qué clase es y quién lo ha hecho.

## Número del ruido, único en la partida (la memoria de la IA lo cita).
var id: int = 0
var position: Vector3 = Vector3.ZERO
## Alcance en metros, con el aire en calma y nada en medio.
var radius: float = 0.0
## Clase ([constant NoiseRules.STEP], [constant NoiseRules.LANDING], "cristal", "palanca"…).
var kind: StringName = &""
## El jugador que lo ha hecho (su peer), o 0 si no ha sido un jugador.
var source: int = 0
## El agente que lo ha hecho (su instance id: un ladrido), o 0; no se oye a sí mismo.
var emitter: int = 0
## Cuándo sonó, en segundos desde que arrancó el juego.
var time: float = 0.0
