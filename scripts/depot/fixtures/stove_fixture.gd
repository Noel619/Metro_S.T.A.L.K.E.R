class_name StoveFixture
extends Fixture
## La estufa de leña del rincón de dormir (F2-05): se carga con un haz de leña
## (mantener el botón con la leña en la mano) y se enciende con una cerilla.
## Arde mientras le queda leña; las brasas brillan por las rendijas.

## Lo que da un haz de leña (1 es la estufa llena) y lo que dura llena, en
## horas de juego.
const LOAD: float = 0.5
const FULL_HOURS: float = 14.0
## Cada cuánto manda el anfitrión lo que queda de leña (segundos).
const SYNC_SECONDS: float = 20.0
## Usos de una caja de cerillas.
const MATCHES: int = 12

var model: Node3D
var _embers: MeshInstance3D
var _glow: Material
var _dark: Material
var _fire: OmniLight3D
var _fuel_left: float = 0.0
var _sync_clock: float = 0.0
var _hold: Dictionary = {}


func _ready() -> void:
	var body: Node = (
		model if model is StaticBody3D else model.find_children("*", "StaticBody3D", true, false)[0]
	)
	_embers = model.find_child("brasas", true, false) as MeshInstance3D
	_dark = _embers.get_active_material(0) if _embers != null else null
	var glow: ShaderMaterial = load("res://assets/materials/bombilla.tres").duplicate()
	glow.set_shader_parameter("emission_color", Color(1.0, 0.45, 0.15))
	glow.set_shader_parameter("emission_energy", 4.0)
	_glow = glow
	_fire = OmniLight3D.new()
	_fire.name = "Fuego"
	_fire.light_color = Color(1.0, 0.55, 0.25)
	_fire.omni_range = 3.2
	_fire.light_energy = 0.0
	_fire.shadow_enabled = false
	_fire.position = Vector3(0.0, 0.5, 0.45)
	model.add_child(_fire)
	add_work(body, [&"lena"], Workable.Gesture.HOLD, "Cargar")
	add_work(body, [&"cerillas"], Workable.Gesture.HOLD, "Encender")
	super._ready()


func fuel() -> float:
	return float(value("lena", 0.0))


func is_lit() -> bool:
	return bool(value("encendida", false))


func _on_worked(player: Player, tool: StringName, amount: float, _point: Vector3) -> void:
	var key: String = "%d_%s" % [player.peer_id, tool]
	var held: float = float(_hold.get(key, 0.0)) + amount
	if held < 0.8:
		_hold[key] = held
		return
	_hold.erase(key)
	var item: Carryable = player.held_item()
	if item == null:
		return
	if tool == &"lena" and fuel() < 0.99:
		consume_held(player)
		_fuel_left = minf(1.0, fuel() + LOAD)
		set_value("lena", _fuel_left)
	elif tool == &"cerillas" and fuel() > 0.02 and not is_lit():
		var uses: int = int(item.state.extra.get("usos", MATCHES)) - 1
		if uses <= 0:
			consume_held(player)
		else:
			var extra: Dictionary = item.state.extra.duplicate()
			extra["usos"] = uses
			item.set_values({"extra": extra})
		set_value("encendida", true)


func _refresh() -> void:
	_fuel_left = fuel()
	if _embers != null:
		_embers.set_surface_override_material(0, _glow if is_lit() else _dark)


func _process(delta: float) -> void:
	if not is_lit():
		_fire.light_energy = 0.0
		return
	var t: float = Time.get_ticks_msec() / 1000.0
	_fire.light_energy = 0.9 + 0.25 * sin(t * 7.1) + 0.15 * sin(t * 13.7)
	if not is_authority() or not GameState.clock_running:
		return
	_fuel_left -= delta * GameState.MINUTES_PER_SECOND / (FULL_HOURS * 60.0)
	_sync_clock += delta
	if _fuel_left <= 0.0:
		set_values({"lena": 0.0, "encendida": false})
	elif _sync_clock >= SYNC_SECONDS:
		_sync_clock = 0.0
		set_value("lena", _fuel_left)
