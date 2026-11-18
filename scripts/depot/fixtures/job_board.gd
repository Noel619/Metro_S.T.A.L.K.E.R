class_name JobBoard
extends Node3D
## El tablón de corcho de los encargos (F2-10): una ficha por encargo, clavada
## con su chincheta. Los caducados se tachan; los entregados se quitan. F sobre
## una ficha la acerca. Se pinta con lo que dice [member GameState.jobs].

const CARD_WIDTH: float = 0.2
const COLUMNS: int = 4
## Lo que ocupa el corcho (en los ejes del tablón: mira hacia +Z).
const ORIGIN: Vector2 = Vector2(-0.36, 0.56)
const STEP: Vector2 = Vector2(0.24, -0.17)

var _cards: Node3D
var _shown: String = ""


func _ready() -> void:
	_cards = Node3D.new()
	_cards.name = "Fichas"
	add_child(_cards)
	GameState.changed.connect(_rebuild)
	_rebuild()


## El papel de un encargo (assets/ui/ficha_encargo.svg).
static func card_of(job: Dictionary) -> Dictionary:
	var rotulos: Array = [
		{
			"text": "ENCARGO",
			"x": 34,
			"y": 34,
			"size": 40,
			"rot": 0,
			"font": "rotulo",
			"color": "#B4423A"
		},
		{
			"text": "de: %s" % str(job.get("client", "")),
			"x": 250,
			"y": 46,
			"size": 26,
			"rot": 0,
			"font": "manuscrita",
			"color": "#3B3A40",
		},
		{
			"text": str(job.get("want", job.get("item", ""))),
			"x": 40,
			"y": 98,
			"size": 34,
			"rot": -1,
			"font": "manuscrita_negrita",
			"color": "#3B3A40",
		},
	]
	var hint: String = str(job.get("hint", ""))
	var y: float = 142.0
	for line: String in _wrap(hint, 36):
		rotulos.append(
			{
				"text": line,
				"x": 40,
				"y": y,
				"size": 30,
				"rot": -1,
				"font": "manuscrita",
				"color": "#3B3A40"
			}
		)
		y += 44.0
	(
		rotulos
		. append(
			{
				"text": "Paga: %d ₽" % int(job.get("pay", 0)),
				"x": 40,
				"y": 270,
				"size": 30,
				"rot": -1,
				"font": "manuscrita_negrita",
				"color": "#3B3A40",
			}
		)
	)
	(
		rotulos
		. append(
			{
				"text": "Antes del día %d" % int(job.get("deadline", 0)),
				"x": 360,
				"y": 270,
				"size": 30,
				"rot": -1,
				"font": "manuscrita",
				"color": "#3B3A40",
			}
		)
	)
	var paper: Dictionary = {"svg": "ficha_encargo", "ancho_m": CARD_WIDTH, "rotulos": rotulos}
	if str(job.get("state", "")) == "caducado":
		paper["tachados"] = [[30, 60, 610, 370], [30, 370, 610, 60]]
	return paper


static func _wrap(text: String, width: int) -> Array[String]:
	var lines: Array[String] = []
	var line: String = ""
	for word: String in text.split(" ", false):
		if line.length() + word.length() + 1 > width and not line.is_empty():
			lines.append(line)
			line = word
		else:
			line = word if line.is_empty() else line + " " + word
	if not line.is_empty():
		lines.append(line)
	return lines.slice(0, 3)


func _rebuild() -> void:
	var visible_jobs: Array = GameState.jobs.filter(
		func(job: Dictionary) -> bool: return str(job.get("state", "")) != "entregado"
	)
	var key: String = JSON.stringify(visible_jobs)
	if key == _shown:
		return
	_shown = key
	for child: Node in _cards.get_children():
		child.queue_free()
	for index: int in mini(visible_jobs.size(), COLUMNS * 3):
		var job: Dictionary = visible_jobs[index]
		var paper: Dictionary = card_of(job)
		var card: PaperCard = PaperCard.create(paper)
		card.name = "Ficha_%d" % int(job.get("id", index))
		var cell: Vector2 = ORIGIN + Vector2(index % COLUMNS, index / COLUMNS) * STEP
		card.position = Vector3(cell.x, cell.y, 0.006 + index * 0.0004)
		card.rotation.z = deg_to_rad((index * 37 % 9) - 4.0)
		_cards.add_child(card)
		var area: Area3D = Area3D.new()
		area.collision_layer = Fixture.REACH_LAYER
		area.collision_mask = 0
		area.monitoring = false
		var shape: CollisionShape3D = CollisionShape3D.new()
		var box: BoxShape3D = BoxShape3D.new()
		box.size = Vector3(card.size.x, card.size.y, 0.03)
		shape.shape = box
		area.add_child(shape)
		card.add_child(area)
		var look: Interactable = Interactable.new()
		look.verb = &"mirar"
		area.add_child(look)
		look.interacted.connect(func(_player: Node) -> void: CloseUp.open(get_tree(), [paper]))
