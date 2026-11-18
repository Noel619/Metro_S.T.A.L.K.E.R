class_name NoteFixture
extends Fixture
## Un papel del mundo con estado (F2-05, F2-11): la lista del primer día en la
## puerta, el aviso de cada mañana bajo la persiana, el recibo del impuesto, el
## papelito que deja un cliente en el mostrador, el precinto… Lo escribe el
## anfitrión ([method write]) y se ve igual en todos los equipos; F lo acerca
## (cada uno el suyo).

## Lo que se aparta del sitio donde se pone (para que no parezca colocado).
var lie_flat: bool = false
var _card: PaperCard
var _area: Area3D
var _shown_text: String = ""
var _settle: float = 0.0


func _ready() -> void:
	_card = PaperCard.new()
	_card.name = "Papel"
	add_child(_card)
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(0.22, 0.24, 0.04)
	_area = add_reach_area(box, Vector3.ZERO, "Leer")
	add_use(_area, &"mirar")
	super._ready()


## Escribe el papel (solo el anfitrión): [param paper] es un [PaperCard].
func write(paper: Dictionary) -> void:
	set_values({"papel": paper, "visible": true})


func hide_paper() -> void:
	set_value("visible", false)


func is_shown() -> bool:
	return bool(value("visible", false))


func paper() -> Dictionary:
	var data: Variant = value("papel", {})
	return data if data is Dictionary else {}


func _on_looked(_player: Node) -> void:
	if is_shown():
		CloseUp.open(get_tree(), [paper()])


func _refresh() -> void:
	var shown: bool = is_shown() and not paper().is_empty()
	_card.visible = shown
	_area.collision_layer = REACH_LAYER if shown else 0
	if not shown:
		return
	var text: String = JSON.stringify(paper())
	if text != _shown_text:
		_shown_text = text
		_card.show_data(paper())
		var box: BoxShape3D = (_area.get_child(0) as CollisionShape3D).shape as BoxShape3D
		box.size = Vector3(_card.size.x, _card.size.y, 0.04)
		# Un papel nuevo cae y se asienta (F2-13).
		_settle = 1.0


func _process(delta: float) -> void:
	if _settle <= 0.0:
		return
	_settle = maxf(0.0, _settle - delta * 2.5)
	_card.position = Vector3(0.0, 0.0, 0.03 * _settle * _settle)
	_card.rotation.z = sin(_settle * 9.0) * 0.08 * _settle
