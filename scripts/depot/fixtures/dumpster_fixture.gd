class_name DumpsterFixture
extends Fixture
## El contenedor de la basura del pasillo (F2-05): con la bolsa (o cualquier
## basura) en la mano, mantener el botón sobre él la tira. La tapa se levanta y
## cae.

const HOLD: float = 0.5
const LID_OPEN: float = deg_to_rad(-70.0)

var model: Node3D
var _lid: Node3D
var _lid_angle: float = 0.0
var _lid_time: float = 0.0
var _hold: Dictionary = {}


func _ready() -> void:
	var body: Node = model.find_children("*", "StaticBody3D", true, false)[0]
	_lid = model.find_child("tapa", true, false) as Node3D
	add_work(body, [&"basura"], Workable.Gesture.HOLD, "Tirar")
	super._ready()


## Bolsas de basura tiradas (para la lista del primer día).
func bags() -> int:
	return int(value("bolsas", 0))


func _on_worked(player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	var item: Carryable = player.held_item()
	if item == null:
		return
	var held: float = float(_hold.get(player.peer_id, 0.0)) + amount
	if held < HOLD:
		_hold[player.peer_id] = held
		return
	_hold.erase(player.peer_id)
	var bag: bool = item.state.data.id == &"bolsa_basura"
	consume_held(player)
	set_values({"bolsas": bags() + (1 if bag else 0), "tiradas": int(value("tiradas", 0)) + 1})


func _refresh() -> void:
	_lid_time = 1.2


func _process(delta: float) -> void:
	if _lid == null or (_lid_time <= 0.0 and is_zero_approx(_lid_angle)):
		return
	_lid_time = maxf(0.0, _lid_time - delta)
	var target: float = LID_OPEN if _lid_time > 0.4 else 0.0
	_lid_angle = move_toward(_lid_angle, target, delta * 5.0)
	_lid.rotation.x = _lid_angle
