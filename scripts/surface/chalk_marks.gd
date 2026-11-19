class_name ChalkMarks
extends Node3D
## Las marcas de tiza (F3-08, docs/SUPERFICIE.md 4.5): con la tiza en la mano, el botón
## izquierdo sobre una pared o el suelo dibuja una marca; la rueda cambia de símbolo
## (flecha, peligro, botín, sin salida, perro). Las marcas se quedan de una salida a
## otra (en el estado de la superficie, que se guarda) y las ve cualquiera.
##
## Las pide quien dibuja ([method request_mark]) y las decide el anfitrión; cada equipo
## las dibuja como calcomanías.

const GROUP: StringName = &"marcas_de_tiza"
const TOOL: StringName = &"tiza"
const SYMBOLS: PackedStringArray = ["flecha", "peligro", "botin", "sin_salida", "perro"]
const TEXTURES_DIR: String = "res://assets/textures/tiza_"
## Lo que mide una marca y lo que se tarda en dibujarla.
const SIZE: float = 0.42
const DRAW_SECONDS: float = 0.7
## Como mucho, tantas marcas (las más viejas se borran).
const MAX_MARKS: int = 200
const WORLD_ID: String = "tiza"
## Lo que se deja de margen al alcance de quien dibuja.
const REACH_SLACK: float = 0.6

var world: DepotWorld

var _textures: Array[Texture2D] = []
var _drawn: Array[Decal] = []
var _preview: Decal


static func find(tree: SceneTree) -> ChalkMarks:
	return tree.get_first_node_in_group(GROUP) as ChalkMarks


func setup(surface_world: DepotWorld) -> void:
	world = surface_world
	name = "Tiza"


func _ready() -> void:
	add_to_group(GROUP)
	for symbol: String in SYMBOLS:
		_textures.append(load(TEXTURES_DIR + symbol + ".png"))
	world.state_changed.connect(
		func(id: String) -> void:
			if id == WORLD_ID:
				_refresh()
	)
	EventBus.item_adjusted.connect(_on_item_adjusted)
	_refresh()


## Las marcas que hay: {"p": [x, y, z], "n": [x, y, z], "s": símbolo}.
func marks() -> Array:
	return world.value(WORLD_ID, "marcas", [])


## Quien dibuja pide una marca en [param position], sobre la superficie de normal
## [param normal], con el símbolo [param symbol]. Decide el anfitrión.
@rpc("any_peer", "call_local", "reliable")
func request_mark(position: Vector3, normal: Vector3, symbol: int) -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	if sender == 0:
		sender = multiplayer.get_unique_id()
	var player: Player = Player.find(get_tree(), sender)
	if player == null or player.held_item() == null or player.held_item().state.data.tool != TOOL:
		return
	if player.eye_position().distance_to(position) > Player.REACH + REACH_SLACK:
		return
	var list: Array = marks().duplicate(true)
	(
		list
		. append(
			{
				"p": [position.x, position.y, position.z],
				"n": [normal.x, normal.y, normal.z],
				"s": clampi(symbol, 0, SYMBOLS.size() - 1),
			}
		)
	)
	while list.size() > MAX_MARKS:
		list.pop_front()
	world.set_value(WORLD_ID, "marcas", list)


## Enseña dónde quedaría la marca (en el equipo de quien dibuja); oculta con [param shown] a false.
func preview(position: Vector3, normal: Vector3, symbol: int, amount: float, shown: bool) -> void:
	if not shown:
		if _preview != null:
			_preview.visible = false
		return
	if _preview == null:
		_preview = _decal()
		_preview.name = "Dibujando"
	_preview.visible = true
	_place(_preview, position, normal, symbol)
	_preview.modulate = Color(1.0, 1.0, 1.0, 0.15 + 0.6 * amount)


func _refresh() -> void:
	var list: Array = marks()
	while _drawn.size() < list.size():
		_drawn.append(_decal())
	while _drawn.size() > list.size():
		_drawn.pop_back().queue_free()
	for index: int in list.size():
		var mark: Dictionary = list[index]
		var p: Array = mark.get("p", [0, 0, 0])
		var n: Array = mark.get("n", [0, 1, 0])
		_place(
			_drawn[index],
			Vector3(p[0], p[1], p[2]),
			Vector3(n[0], n[1], n[2]),
			int(mark.get("s", 0))
		)


func _decal() -> Decal:
	var decal: Decal = Decal.new()
	decal.size = Vector3(SIZE, 0.2, SIZE)
	decal.upper_fade = 0.3
	decal.lower_fade = 0.3
	decal.albedo_mix = 1.0
	decal.cull_mask = 1
	add_child(decal)
	return decal


func _place(decal: Decal, position: Vector3, normal: Vector3, symbol: int) -> void:
	decal.texture_albedo = _textures[clampi(symbol, 0, _textures.size() - 1)]
	var up: Vector3 = normal.normalized()
	# La marca se proyecta a lo largo de la normal; en una pared, derecha (con el arriba del mundo).
	var reference: Vector3 = Vector3.UP if absf(up.dot(Vector3.UP)) < 0.9 else Vector3.FORWARD
	var side: Vector3 = reference.cross(up).normalized()
	var forward: Vector3 = side.cross(up).normalized()
	decal.global_transform = Transform3D(Basis(side, up, -forward), position + up * 0.05)


## La rueda con la tiza en la mano cambia de símbolo (en el anfitrión).
func _on_item_adjusted(_player: Node, item: Node, step: int) -> void:
	var chalk: Carryable = item as Carryable
	if chalk == null or chalk.state.data.tool != TOOL:
		return
	var extra: Dictionary = chalk.state.extra.duplicate(true)
	extra["simbolo"] = posmod(int(extra.get("simbolo", 0)) + step, SYMBOLS.size())
	chalk.set_values({"extra": extra})
