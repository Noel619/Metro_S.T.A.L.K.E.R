extends SceneTree
## Escribe en project.godot los controles, los nombres de las capas y los buses
## de audio. Es la fuente de verdad de todo eso: para cambiarlos, edita este
## script y vuelve a ejecutarlo.
##
## Uso: godot --headless --path . -s tools/godot/setup_project.gd

const DEADZONE: float = 0.2
const BUS_LAYOUT_PATH: String = "res://default_bus_layout.tres"
const BUSES: PackedStringArray = ["Musica", "Ambiente", "Efectos", "Interfaz", "Voz"]

## Cada acción: teclas (físicas, independientes de la distribución del teclado),
## botones del ratón, botones del mando y ejes del mando ([eje, dirección]).
const ACTIONS: Array[Dictionary] = [
	{"name": "move_forward", "keys": [KEY_W], "axes": [[JOY_AXIS_LEFT_Y, -1.0]]},
	{"name": "move_back", "keys": [KEY_S], "axes": [[JOY_AXIS_LEFT_Y, 1.0]]},
	{"name": "move_left", "keys": [KEY_A], "axes": [[JOY_AXIS_LEFT_X, -1.0]]},
	{"name": "move_right", "keys": [KEY_D], "axes": [[JOY_AXIS_LEFT_X, 1.0]]},
	{"name": "look_up", "axes": [[JOY_AXIS_RIGHT_Y, -1.0]]},
	{"name": "look_down", "axes": [[JOY_AXIS_RIGHT_Y, 1.0]]},
	{"name": "look_left", "axes": [[JOY_AXIS_RIGHT_X, -1.0]]},
	{"name": "look_right", "axes": [[JOY_AXIS_RIGHT_X, 1.0]]},
	{"name": "sprint", "keys": [KEY_SHIFT], "buttons": [JOY_BUTTON_LEFT_STICK]},
	{"name": "crouch", "keys": [KEY_C, KEY_CTRL], "buttons": [JOY_BUTTON_B]},
	{"name": "jump", "keys": [KEY_SPACE], "buttons": [JOY_BUTTON_A]},
	{"name": "lean_left", "keys": [KEY_Q], "buttons": [JOY_BUTTON_LEFT_SHOULDER]},
	{"name": "lean_right", "keys": [KEY_E], "buttons": [JOY_BUTTON_RIGHT_SHOULDER]},
	{"name": "interact", "keys": [KEY_F], "buttons": [JOY_BUTTON_X]},
	{"name": "use_primary", "mouse": [MOUSE_BUTTON_LEFT], "axes": [[JOY_AXIS_TRIGGER_RIGHT, 1.0]]},
	{
		"name": "use_secondary",
		"mouse": [MOUSE_BUTTON_RIGHT],
		"axes": [[JOY_AXIS_TRIGGER_LEFT, 1.0]]
	},
	{"name": "flashlight", "keys": [KEY_T], "buttons": [JOY_BUTTON_DPAD_UP]},
	{"name": "notebook", "keys": [KEY_TAB], "buttons": [JOY_BUTTON_BACK]},
	{"name": "backpack", "keys": [KEY_I], "buttons": [JOY_BUTTON_Y]},
	{"name": "belt_1", "keys": [KEY_1], "buttons": [JOY_BUTTON_DPAD_LEFT]},
	{"name": "belt_2", "keys": [KEY_2], "buttons": [JOY_BUTTON_DPAD_DOWN]},
	{"name": "belt_3", "keys": [KEY_3], "buttons": [JOY_BUTTON_DPAD_RIGHT]},
	{"name": "pause", "keys": [KEY_ESCAPE], "buttons": [JOY_BUTTON_START]},
]

## Parámetros globales de los shaders del estilo (los mueve StyleDirector).
## Valores iniciales: los del depósito.
const SHADER_GLOBALS: Dictionary = {
	"tinta_miedo": ["float", 0.0],
	"tinta_radiacion": ["float", 0.0],
	"tinta_trazo_fps": ["float", 4.0],
	"tinta_trazo_amplitud": ["float", 0.6],
	"tinta_grosor": ["float", 1.6],
	"tinta_tramado": ["float", 0.6],
	"tinta_tramado_umbral": ["float", 0.14],
	"tinta_relleno": ["float", 0.012],
	"tinta_saturacion": ["float", 1.0],
	"tinta_contraste": ["float", 1.05],
	"tinta_papel": ["float", 0.3],
	"tinta_grano": ["float", 0.025],
	"tinta_vineta": ["float", 0.3],
	"tinta_negro": ["float", 0.0],
	"tinta_rampa": ["int", 1],
	"tinta_color": ["color", Color("#1b1a22")],
	"tinta_tinte": ["color", Color(1.0, 0.97, 0.92)],
	"tinta_horizonte": ["color", Color(0.66, 0.63, 0.54)],
}

## Valores por defecto al importar. Las texturas del estilo (rampas, tramados)
## no admiten compresión con pérdidas.
const IMPORTER_DEFAULTS: Dictionary = {
	"scene": {"import_script/path": "res://tools/godot/post_import.gd"},
	"texture": {"compress/mode": 0, "detect_3d/compress_to": 0, "mipmaps/generate": true},
}

const LAYER_NAMES: Dictionary = {
	"3d_physics/layer_1": "mundo",
	"3d_physics/layer_2": "jugadores",
	"3d_physics/layer_3": "objetos",
	"3d_physics/layer_4": "criaturas",
	"3d_physics/layer_5": "interactuables",
	"3d_physics/layer_6": "detectores",
	"3d_render/layer_1": "mundo",
	"3d_render/layer_2": "primera_persona",
	"3d_render/layer_3": "solo_captura",
}


func _initialize() -> void:
	_write_actions()
	_write_layer_names()
	_write_shader_globals()
	_write_importer_defaults()
	var err: Error = ProjectSettings.save()
	var bus_err: Error = _write_bus_layout()
	if err != OK or bus_err != OK:
		printerr(
			(
				"No se pudo guardar la configuración: %s / %s"
				% [error_string(err), error_string(bus_err)]
			)
		)
		quit(1)
		return
	print(
		(
			"project.godot actualizado: %d acciones, %d capas y %d buses."
			% [ACTIONS.size(), LAYER_NAMES.size(), BUSES.size() + 1]
		)
	)
	quit(0)


func _write_actions() -> void:
	for action: Dictionary in ACTIONS:
		var events: Array[InputEvent] = []
		for key: int in action.get("keys", []):
			var key_event: InputEventKey = InputEventKey.new()
			key_event.physical_keycode = key as Key
			events.append(key_event)
		for button: int in action.get("mouse", []):
			var mouse_event: InputEventMouseButton = InputEventMouseButton.new()
			mouse_event.button_index = button as MouseButton
			events.append(mouse_event)
		for button: int in action.get("buttons", []):
			var joy_button: InputEventJoypadButton = InputEventJoypadButton.new()
			joy_button.button_index = button as JoyButton
			events.append(joy_button)
		for axis: Array in action.get("axes", []):
			var joy_motion: InputEventJoypadMotion = InputEventJoypadMotion.new()
			joy_motion.axis = axis[0] as JoyAxis
			joy_motion.axis_value = axis[1]
			events.append(joy_motion)
		ProjectSettings.set_setting(
			"input/" + action["name"], {"deadzone": DEADZONE, "events": events}
		)


func _write_layer_names() -> void:
	for key: String in LAYER_NAMES:
		ProjectSettings.set_setting("layer_names/" + key, LAYER_NAMES[key])


func _write_shader_globals() -> void:
	for global_name: String in SHADER_GLOBALS:
		var spec: Array = SHADER_GLOBALS[global_name]
		ProjectSettings.set_setting(
			"shader_globals/" + global_name, {"type": spec[0], "value": spec[1]}
		)


func _write_importer_defaults() -> void:
	for importer: String in IMPORTER_DEFAULTS:
		ProjectSettings.set_setting("importer_defaults/" + importer, IMPORTER_DEFAULTS[importer])


func _write_bus_layout() -> Error:
	while AudioServer.bus_count > 1:
		AudioServer.remove_bus(AudioServer.bus_count - 1)
	for bus_name: String in BUSES:
		AudioServer.add_bus()
		var index: int = AudioServer.bus_count - 1
		AudioServer.set_bus_name(index, bus_name)
		AudioServer.set_bus_send(index, &"Master")
	return ResourceSaver.save(AudioServer.generate_bus_layout(), BUS_LAYOUT_PATH)
