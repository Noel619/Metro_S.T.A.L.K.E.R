extends Node
## Ajustes del jugador (no de la partida). Se guardan en user://ajustes.cfg.
##
## El equipo de referencia es un Ryzen 7 8700G con su gráfica integrada, así
## que el escalado 3D (FSR 2) está disponible desde el principio.

signal changed

const DEFAULT_PATH: String = "user://ajustes.cfg"
const SCALING_MODES: Dictionary = {
	"nativo": Viewport.SCALING_3D_MODE_BILINEAR,
	"fsr": Viewport.SCALING_3D_MODE_FSR,
	"fsr2": Viewport.SCALING_3D_MODE_FSR2,
}

## Ruta del archivo. Los tests la cambian para no tocar los ajustes reales.
var settings_path: String = DEFAULT_PATH

var scaling_mode: String = "nativo"
var render_scale: float = 1.0
var fullscreen: bool = false
var vsync: bool = true
var mouse_sensitivity: float = 0.25
var invert_y: bool = false
## Accesibilidad: trazo vivo más suave.
var reduce_line_boil: bool = false
var volumes: Dictionary = {
	"Master": 1.0,
	"Musica": 0.8,
	"Ambiente": 1.0,
	"Efectos": 1.0,
	"Interfaz": 0.8,
	"Voz": 1.0,
}


func _ready() -> void:
	load_settings()
	apply()


func load_settings() -> void:
	var config: ConfigFile = ConfigFile.new()
	if config.load(settings_path) != OK:
		return
	scaling_mode = str(config.get_value("video", "scaling_mode", scaling_mode))
	if not SCALING_MODES.has(scaling_mode):
		scaling_mode = "nativo"
	render_scale = clampf(float(config.get_value("video", "render_scale", render_scale)), 0.5, 1.0)
	fullscreen = bool(config.get_value("video", "fullscreen", fullscreen))
	vsync = bool(config.get_value("video", "vsync", vsync))
	mouse_sensitivity = float(config.get_value("controles", "mouse_sensitivity", mouse_sensitivity))
	invert_y = bool(config.get_value("controles", "invert_y", invert_y))
	reduce_line_boil = bool(config.get_value("accesibilidad", "reduce_line_boil", reduce_line_boil))
	for bus_name: String in volumes:
		volumes[bus_name] = clampf(
			float(config.get_value("audio", bus_name, volumes[bus_name])), 0.0, 1.0
		)


func save_settings() -> Error:
	var config: ConfigFile = ConfigFile.new()
	config.set_value("video", "scaling_mode", scaling_mode)
	config.set_value("video", "render_scale", render_scale)
	config.set_value("video", "fullscreen", fullscreen)
	config.set_value("video", "vsync", vsync)
	config.set_value("controles", "mouse_sensitivity", mouse_sensitivity)
	config.set_value("controles", "invert_y", invert_y)
	config.set_value("accesibilidad", "reduce_line_boil", reduce_line_boil)
	for bus_name: String in volumes:
		config.set_value("audio", bus_name, volumes[bus_name])
	return config.save(settings_path)


## Aplica los ajustes al juego en marcha.
func apply() -> void:
	var viewport: Viewport = get_viewport()
	viewport.scaling_3d_mode = SCALING_MODES[scaling_mode]
	viewport.scaling_3d_scale = render_scale
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_vsync_mode(
			DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED
		)
		if fullscreen:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	for bus_name: String in volumes:
		var bus_index: int = AudioServer.get_bus_index(bus_name)
		if bus_index >= 0:
			AudioServer.set_bus_volume_db(bus_index, linear_to_db(volumes[bus_name]))
	changed.emit()
