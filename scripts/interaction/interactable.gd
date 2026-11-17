class_name Interactable
extends Node
## Componente que hace que algo del mundo se pueda usar.
##
## Se añade como hijo de un cuerpo físico (o de un área). El jugador que lo
## tiene delante, a su alcance, ve cómo el punto de lápiz se convierte en el
## icono de [member verb], y al pulsar "interactuar" se emite [signal interacted].
## Qué pasa después lo decide quien escuche la señal.

## El jugador [param player] ha usado esto.
signal interacted(player: Node)
## El jugador lo tiene delante (o deja de tenerlo).
signal focus_changed(focused: bool)

## Iconos dibujados de cada verbo (tools/svg/generate.mjs).
const ICONS: Dictionary = {
	&"coger": "res://assets/ui/icono_mano.svg",
	&"usar": "res://assets/ui/icono_mano.svg",
	&"mirar": "res://assets/ui/icono_lupa.svg",
}
const HIGHLIGHT: String = "res://assets/materials/resaltado.tres"

## Qué se hace con esto: decide el icono.
@export var verb: StringName = &"coger"
@export var enabled: bool = true

var _focus_count: int = 0


## El componente de un cuerpo, si lo tiene.
static func of(body: Node) -> Interactable:
	if body == null:
		return null
	for child: Node in body.get_children():
		if child is Interactable:
			return child as Interactable
	return null


func icon_path() -> String:
	return ICONS.get(verb, ICONS[&"usar"])


func interact(player: Node) -> void:
	if enabled:
		interacted.emit(player)


## Resaltado dibujado: un contorno de tinta más grueso mientras se mira.
func set_focused(focused: bool) -> void:
	_focus_count = maxi(0, _focus_count + (1 if focused else -1))
	var on: bool = _focus_count > 0
	var overlay: Material = load(HIGHLIGHT) if on else null
	for mesh: Node in get_parent().find_children("*", "MeshInstance3D", true, false):
		(mesh as MeshInstance3D).material_overlay = overlay
	focus_changed.emit(on)
