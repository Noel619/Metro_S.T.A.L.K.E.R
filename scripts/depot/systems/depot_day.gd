class_name DepotDay
extends Node3D
## El día en el depósito (docs/DEPOSITO.md 3): la hora corre, el catre termina
## el día (a partir de las 18; a medianoche te quedas dormido donde estés), se
## carga el impuesto, cuenta lo comido, se guarda la partida y todos despiertan
## a las 7 junto al catre. El hambre se nota: un día sin comer tiembla lo que
## llevas y andas más despacio; tres, el tramado invade los bordes de la vista;
## cinco, mueres (y la partida se borra).

## Desde qué hora se puede dormir.
const SLEEP_FROM: float = 18.0
## Lo que dura el fundido a negro (segundos).
const FADE: float = 1.2
## Dónde despierta cada jugador (junto al catre, de cara al paso de la manta) y
## hacia dónde mira.
const WAKE_SPOTS: Array[Vector3] = [
	Vector3(-1.9, 0.03, -2.4),
	Vector3(-0.9, 0.03, -2.55),
	Vector3(-2.7, 0.03, -2.05),
	Vector3(-0.1, 0.03, -2.85),
]
const WAKE_YAW: float = PI

var room: DepotRoom
var counter: DepotCounter
var cot: CotFixture
var _sleeping: bool = false
var _fade: ColorRect
var _hunger: TextureRect
var _layer: CanvasLayer


func _ready() -> void:
	cot = CotFixture.new()
	cot.fixture_id = "catre"
	cot.name = "Catre"
	cot.model = room.fixed("Catre")
	cot.day = self
	add_child(cot)
	_layer = CanvasLayer.new()
	_layer.name = "Vista"
	_layer.layer = 15
	add_child(_layer)
	_hunger = TextureRect.new()
	_hunger.name = "Hambre"
	_hunger.texture = _hatching()
	_hunger.set_anchors_preset(Control.PRESET_FULL_RECT)
	_hunger.stretch_mode = TextureRect.STRETCH_SCALE
	_hunger.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hunger.visible = false
	_layer.add_child(_hunger)
	_fade = ColorRect.new()
	_fade.name = "Fundido"
	_fade.color = Color(0.03, 0.025, 0.03, 0.0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_fade)
	GameState.changed.connect(_refresh_hunger)
	_refresh_hunger()


func _process(_delta: float) -> void:
	if not multiplayer.is_server() or _sleeping:
		return
	if GameState.clock_running and GameState.minute >= GameState.DAY_MINUTES - 0.5:
		sleep()


## ¿Se puede dormir ya?
func can_sleep() -> bool:
	return GameState.hour() >= SLEEP_FROM


## Termina el día (solo el anfitrión): fundido, impuesto y hambre, guardar y
## despertar a las 7.
func sleep() -> void:
	if not multiplayer.is_server() or _sleeping:
		return
	_sleeping = true
	GameState.clock_running = false
	_fade_out.rpc()
	await get_tree().create_timer(FADE).timeout
	if counter != null:
		counter.close_for_the_night()
	GameState.end_day()
	if GameState.hungry_days >= GameState.HUNGRY_DEATH:
		_starved()
		return
	SaveSystem.save_game()
	var index: int = 0
	for node: Node in get_tree().get_nodes_in_group(Player.GROUP):
		var player: Player = node as Player
		var spot: Vector3 = WAKE_SPOTS[index % WAKE_SPOTS.size()]
		player.move_to.rpc_id(player.peer_id, spot, WAKE_YAW)
		index += 1
	await get_tree().create_timer(0.4).timeout
	GameState.clock_running = true
	GameState.push()
	_fade_in.rpc()
	_sleeping = false


## Se ha muerto de hambre: la nota y una partida nueva (la otra se borra).
func _starved() -> void:
	SaveSystem.delete_save()
	EventBus.game_over.emit()
	_show_death.rpc()
	_sleeping = false


@rpc("authority", "call_local", "reliable")
func _show_death() -> void:
	_fade.color.a = 1.0
	var note: Dictionary = PaperCard.note(
		["*Cinco días sin comer.", "", "La consigna se queda", "otra vez sin dueño."], 0.15
	)
	CloseUp.open(get_tree(), [note])


@rpc("authority", "call_local", "reliable")
func _fade_out() -> void:
	var tween: Tween = create_tween()
	tween.tween_property(_fade, "color:a", 1.0, FADE)


@rpc("authority", "call_local", "reliable")
func _fade_in() -> void:
	var tween: Tween = create_tween()
	tween.tween_interval(0.5)
	tween.tween_property(_fade, "color:a", 0.0, FADE * 1.5)


func _refresh_hunger() -> void:
	_hunger.visible = GameState.hungry_days >= GameState.HUNGRY_BLUR
	var days: float = float(GameState.hungry_days - GameState.HUNGRY_BLUR)
	_hunger.modulate.a = clampf(0.55 + days * 0.2, 0.0, 0.95)


## El tramado de los bordes: rayas de lápiz cruzadas que se espesan hacia fuera.
static func _hatching() -> Texture2D:
	var size: int = 256
	var image: Image = Image.create(size, size, false, Image.FORMAT_RGBA8)
	for y: int in size:
		for x: int in size:
			var u: float = (x - size / 2.0) / (size / 2.0)
			var v: float = (y - size / 2.0) / (size / 2.0)
			var edge: float = clampf((Vector2(u, v).length() - 0.55) / 0.5, 0.0, 1.0)
			var line: bool = (x + y) % 7 == 0 or (edge > 0.5 and (x - y + size) % 9 == 0)
			var alpha: float = edge * edge * (0.85 if line else 0.25)
			image.set_pixel(x, y, Color(0.11, 0.1, 0.13, alpha))
	return ImageTexture.create_from_image(image)
