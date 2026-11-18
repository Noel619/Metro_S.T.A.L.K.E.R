class_name CashBoxFixture
extends Fixture
## La caja de los rublos (F2-09): el dinero del depósito ([member GameState.rubles]).
## F saca un fajo (diez rublos, o lo que haya); con el fajo en la mano, la rueda
## cuenta más o menos billetes ([DepotCounter]) y mantener el botón sobre la caja
## lo devuelve. La tapa se abre al usarla.

const FIRST_WAD: int = 10
const LID_OPEN: float = deg_to_rad(-100.0)

var model: Node3D
var _lid: Node3D
var _lid_angle: float = 0.0
var _lid_time: float = 0.0
var _hold: Dictionary = {}


func _ready() -> void:
	var body: Node = model.find_children("*", "StaticBody3D", true, false)[0]
	_lid = model.find_child("tapa", true, false) as Node3D
	add_use(body)
	add_work(body, [&"billetes"], Workable.Gesture.HOLD, "Guardar")
	super._ready()


func _on_used(player: Player, _action: StringName) -> void:
	var items: WorldItems = world_items()
	if items == null or player.held_item() != null or GameState.rubles <= 0:
		return
	var amount: int = mini(FIRST_WAD, GameState.rubles)
	GameState.add_rubles(-amount)
	items.give(player, &"billetes", {"rublos": amount})
	set_value("usos", int(value("usos", 0)) + 1)


func _on_worked(player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	var item: Carryable = player.held_item()
	if item == null or item.state.data.tool != &"billetes":
		return
	var held: float = float(_hold.get(player.peer_id, 0.0)) + amount
	if held < 0.4:
		_hold[player.peer_id] = held
		return
	_hold.erase(player.peer_id)
	GameState.add_rubles(int(item.state.extra.get("rublos", 0)))
	consume_held(player)
	set_value("usos", int(value("usos", 0)) + 1)


func _refresh() -> void:
	_lid_time = 1.5


func _process(delta: float) -> void:
	if _lid == null or (_lid_time <= 0.0 and is_zero_approx(_lid_angle)):
		return
	_lid_time = maxf(0.0, _lid_time - delta)
	var target: float = LID_OPEN if _lid_time > 0.5 else 0.0
	_lid_angle = move_toward(_lid_angle, target, delta * 6.0)
	_lid.rotation.x = _lid_angle
