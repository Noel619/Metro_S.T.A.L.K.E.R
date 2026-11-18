class_name TrashBinFixture
extends Fixture
## El cubo de basura de la consigna (F2-05): con algo que es basura en la mano,
## mantener el botón sobre el cubo lo tira dentro. Con F se saca la bolsa (si
## tiene algo): sale cerrada, para llevarla al contenedor del pasillo, y el cubo
## queda con una bolsa nueva.

## Lo que hay que mantener el botón para tirar algo (segundos).
const HOLD: float = 0.4
const CAPACITY: int = 10

var model: Node3D
var _fill: MeshInstance3D
var _hold: Dictionary = {}


func _ready() -> void:
	var body: Node = model.find_children("*", "StaticBody3D", true, false)[0]
	add_use(body)
	add_work(body, [&"basura"], Workable.Gesture.HOLD, "Tirar")
	var disc: CylinderMesh = CylinderMesh.new()
	disc.top_radius = 0.17
	disc.bottom_radius = 0.15
	disc.height = 0.02
	_fill = MeshInstance3D.new()
	_fill.name = "Relleno"
	_fill.mesh = disc
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = Color(0.16, 0.16, 0.18)
	_fill.material_override = material
	model.add_child(_fill)
	super._ready()


func count() -> int:
	return int(value("llenado", 0))


func _on_worked(player: Player, _tool: StringName, amount: float, _point: Vector3) -> void:
	var item: Carryable = player.held_item()
	if item == null or not item.state.data.trash or count() >= CAPACITY:
		return
	var held: float = float(_hold.get(player.peer_id, 0.0)) + amount
	if held < HOLD:
		_hold[player.peer_id] = held
		return
	_hold.erase(player.peer_id)
	consume_held(player)
	set_value("llenado", count() + 1)


func _on_used(_player: Player, _action: StringName) -> void:
	if count() <= 0:
		return
	var items: WorldItems = world_items()
	if items == null:
		return
	# La bolsa sale delante del cubo, hacia la sala.
	var where: Vector3 = model.global_position + Vector3(0.0, 0.05, -0.55)
	items.spawn_with(&"bolsa_basura", Transform3D(Basis.IDENTITY, where), {"bolsas": count()})
	set_values({"llenado": 0, "sacadas": int(value("sacadas", 0)) + 1})
	DustPuff.burst(self, where + Vector3(0.0, 0.2, 0.0), 0.4)


func _refresh() -> void:
	var share: float = float(count()) / CAPACITY
	_fill.visible = count() > 0
	_fill.position = Vector3(0.0, 0.08 + share * 0.4, 0.0)
