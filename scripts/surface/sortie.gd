class_name Sortie
extends RefCounted
## Subir a la superficie y volver (docs/SUPERFICIE.md, 1).
##
## Lo decide el anfitrión cuando todos los jugadores vivos están en la escalera
## (para subir) o en la esclusa con la compuerta cerrada (para bajar). Antes de
## cambiar de escena aparca el estado de la que se deja ([method SaveSystem.park_all]),
## que se recupera al volver, y se queda con lo que lleva cada jugador en las
## manos para dárselo en la otra escena. Lo que dura un cambio de escena vive aquí,
## en variables de la clase, que no se borran al cambiar de escena.

const SURFACE_SCENE: String = "res://scenes/surface/superficie.tscn"
const DEPOT_SCENE: String = "res://scenes/depot/deposito.tscn"
## Por dónde se llega: subiendo (a la esclusa) o bajando (al pie de la escalera).
const UP: StringName = &"subir"
const DOWN: StringName = &"bajar"

## Cómo se llega a la escena que se está cargando ("" si no es una salida: al
## empezar la partida o al despertar).
static var arriving: StringName = &""
## Lo que lleva cada jugador al cambiar de escena: peer -> {"mano": estado del objeto}.
static var carried: Dictionary = {}
## El protagonista de este equipo (para pedir el jugador en la escena nueva).
static var local_variant: String = "chico"
## Para las pruebas: quien cambia de escena en vez de [SceneRouter] (recibe la ruta).
static var scene_changer: Callable = Callable()


## Sube a la superficie (o baja al depósito, con [param down]). Solo el anfitrión.
static func travel(tree: SceneTree, down: bool) -> void:
	if not tree.root.multiplayer.is_server():
		return
	carried.clear()
	var items: WorldItems = tree.get_first_node_in_group(WorldItems.GROUP) as WorldItems
	for node: Node in tree.get_nodes_in_group(Player.GROUP):
		var player: Player = node as Player
		var held: Carryable = player.held_item()
		if held == null:
			continue
		carried[player.peer_id] = {"mano": held.state.to_dict()}
		# Lo que se lleva sale de esta escena: si no, volvería a aparecer en ella.
		if items != null:
			items.remove_item(held)
	SaveSystem.park_all()
	arriving = DOWN if down else UP
	var path: String = DEPOT_SCENE if down else SURFACE_SCENE
	if scene_changer.is_valid():
		scene_changer.call(path)
	else:
		SceneRouter.go_to(path)


## Lo que llevaba en las manos [param peer] al cambiar de escena (y lo olvida).
static func take_held(peer: int) -> ItemState:
	var entry: Dictionary = carried.get(peer, {})
	carried.erase(peer)
	if not entry.has("mano"):
		return null
	var state: ItemState = ItemState.from_dict(entry["mano"])
	state.uid = 0
	return state if state.data != null else null


## Se ha llegado: lo que dura el cambio de escena ya no hace falta.
static func arrived() -> void:
	arriving = &""
