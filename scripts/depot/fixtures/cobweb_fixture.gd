class_name CobwebFixture
extends Fixture
## Una telaraña de un rincón (F2-05): se quita con la escoba o con la mano, a
## pasadas. Es el dibujo de assets/ui/telarana.svg, recortado.

const PER_STROKE: float = 0.45

@export var size: float = 0.7

var _card: PaperCard
var _area: Area3D


func _ready() -> void:
	_card = PaperCard.create({"svg": "telarana", "ancho_m": size, "rotulos": []})
	_card.name = "Dibujo"
	add_child(_card)
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(size * 0.8, size * 0.4, 0.2)
	_area = add_reach_area(box, Vector3.ZERO)
	add_work(_area, [&"escoba", Workable.HANDS], Workable.Gesture.STROKE, "Quitar")
	super._ready()


func amount() -> float:
	return float(value("suciedad", 1.0))


func is_clean() -> bool:
	return amount() <= 0.0


func _on_worked(_player: Player, _tool: StringName, worked: float, _point: Vector3) -> void:
	if worked <= 0.0 or is_clean():
		return
	var left: float = amount() - worked * PER_STROKE
	set_value("suciedad", 0.0 if left < 0.05 else left)


func _refresh() -> void:
	var left: float = amount()
	_card.visible = left > 0.0
	_card.scale = Vector3.ONE * lerpf(0.35, 1.0, left)
	_area.collision_layer = 0 if left <= 0.0 else REACH_LAYER
	if left < 1.0 and left > 0.0:
		DustPuff.burst(self, global_position, 0.3, Color(0.75, 0.72, 0.66))
