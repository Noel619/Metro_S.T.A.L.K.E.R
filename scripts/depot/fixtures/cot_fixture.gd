class_name CotFixture
extends Fixture
## El catre (docs/DEPOSITO.md 3): F duerme y termina el día, a partir de las 18.
## Antes, solo cruje (se mueve un poco la manta).

var model: Node3D
var day: DepotDay
var _blanket: Node3D
var _creak: float = 0.0


func _ready() -> void:
	var bodies: Array[Node] = model.find_children("*", "StaticBody3D", true, false)
	_blanket = model.find_child("manta", true, false) as Node3D
	add_use(bodies[0] if not bodies.is_empty() else model)
	super._ready()


func _on_used(_player: Player, _action: StringName) -> void:
	if day != null and day.can_sleep():
		day.sleep()
	else:
		set_value("crujidos", int(value("crujidos", 0)) + 1)


func _refresh() -> void:
	_creak = 1.0


func _process(delta: float) -> void:
	if _blanket == null or _creak <= 0.0:
		return
	_creak = maxf(0.0, _creak - delta * 3.0)
	_blanket.position.y = sin(_creak * 20.0) * 0.006 * _creak
