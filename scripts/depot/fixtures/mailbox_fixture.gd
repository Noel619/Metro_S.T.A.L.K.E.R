class_name MailboxFixture
extends Fixture
## El buzón de los pagos de la ventanilla de la administración (F2-11): con un
## fajo en la mano, mantener el botón sobre él lo echa por la ranura. Lo pagado
## rebaja la deuda; el recibo llega a la mañana siguiente.

signal paid(amount: int)

const HOLD: float = 0.6

var model: Node3D
var _hold: Dictionary = {}


func _ready() -> void:
	var bodies: Array[Node] = model.find_children("*", "StaticBody3D", true, false)
	var body: Node = bodies[0] if not bodies.is_empty() else model
	add_work(body, [&"billetes"], Workable.Gesture.HOLD, "Pagar")
	super._ready()


func _on_worked(player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	var item: Carryable = player.held_item()
	if item == null or item.state.data.tool != &"billetes":
		return
	var held: float = float(_hold.get(player.peer_id, 0.0)) + amount
	if held < HOLD:
		_hold[player.peer_id] = held
		return
	_hold.erase(player.peer_id)
	var rubles: int = int(item.state.extra.get("rublos", 0))
	consume_held(player)
	if rubles > 0:
		GameState.pay_tax(rubles)
		set_value("pagos", int(value("pagos", 0)) + 1)
		paid.emit(rubles)
