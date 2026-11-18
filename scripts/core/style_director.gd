extends Node
## Decide cómo se "dibuja" la imagen en cada momento.
##
## Mezcla el preajuste de la zona (depósito o superficie) con el miedo y la
## radiación, y lo publica en los parámetros globales de los shaders (tinta_*).
## Los cambios de zona se interpolan: al subir por la escalera mecánica, el
## dibujo pasa poco a poco de un estilo al otro.

signal zone_changed(zone: StringName)

const ZONE_DEPOT: StringName = &"deposito"
const ZONE_SURFACE: StringName = &"superficie"
const ZONE_SURFACE_NIGHT: StringName = &"superficie_noche"

## Valores de cada zona (ver docs/ESTILO.md). "rampa" es la fila de rampas.png.
const PRESETS: Dictionary = {
	ZONE_DEPOT:
	{
		"trazo_fps": 4.0,
		"trazo_amplitud": 0.6,
		"grosor": 1.6,
		"tramado": 0.3,
		"tramado_umbral": 0.07,
		"relleno": 0.003,
		"saturacion": 0.72,
		"contraste": 1.0,
		"papel": 0.3,
		"grano": 0.025,
		"vineta": 0.3,
		"negro": 0.0,
		"rampa": 1,
		"sombra": 0.55,
		"tinte": Color(1.0, 0.98, 0.95),
	},
	ZONE_SURFACE:
	{
		"trazo_fps": 8.0,
		"trazo_amplitud": 1.0,
		"grosor": 2.2,
		"tramado": 0.4,
		"tramado_umbral": 0.16,
		"relleno": 0.008,
		"saturacion": 0.5,
		"contraste": 1.08,
		"papel": 0.4,
		"grano": 0.06,
		"vineta": 0.5,
		"negro": 0.0,
		"rampa": 2,
		"sombra": 0.5,
		"tinte": Color(0.97, 0.95, 0.9),
	},
	ZONE_SURFACE_NIGHT:
	{
		"trazo_fps": 8.0,
		"trazo_amplitud": 1.0,
		"grosor": 2.2,
		"tramado": 0.5,
		"tramado_umbral": 0.1,
		"relleno": 0.002,
		"saturacion": 0.55,
		"contraste": 1.1,
		"papel": 0.35,
		"grano": 0.07,
		"vineta": 0.45,
		"negro": 1.0,
		"rampa": 2,
		"sombra": 0.35,
		"tinte": Color(0.9, 0.95, 1.0),
	},
}

## Segundos que tarda en pasar de una zona a otra.
@export var transition_time: float = 2.5

var zone: StringName = ZONE_DEPOT
## Miedo del jugador, de 0 a 1.
var fear: float = 0.0
## Radiación que se nota en la imagen, de 0 a 1.
var radiation: float = 0.0

var _from: Dictionary = {}
var _blend: float = 1.0


func _ready() -> void:
	_from = PRESETS[zone].duplicate()
	_apply(PRESETS[zone])


func _process(delta: float) -> void:
	if _blend < 1.0:
		_blend = minf(1.0, _blend + delta / maxf(transition_time, 0.001))
	_apply(_interpolated())


## Cambia de zona. Con [param instant], sin transición (por ejemplo, al cargar).
func set_zone(new_zone: StringName, instant: bool = false) -> void:
	if not PRESETS.has(new_zone):
		push_warning("Zona de estilo desconocida: %s" % new_zone)
		return
	_from = _interpolated()
	zone = new_zone
	_blend = 1.0 if instant else 0.0
	zone_changed.emit(zone)


func _interpolated() -> Dictionary:
	var target: Dictionary = PRESETS[zone]
	if _blend >= 1.0:
		return target.duplicate()
	var weight: float = smoothstep(0.0, 1.0, _blend)
	var result: Dictionary = {}
	for key: String in target:
		var to_value: Variant = target[key]
		var from_value: Variant = _from.get(key, to_value)
		if to_value is int:
			result[key] = to_value if weight > 0.5 else from_value
		else:
			result[key] = lerp(from_value, to_value, weight)
	return result


func _apply(values: Dictionary) -> void:
	var gentle: bool = Settings.reduce_line_boil
	for key: String in values:
		var value: Variant = values[key]
		if gentle and key == "trazo_amplitud":
			value = value * 0.3
		elif gentle and key == "trazo_fps":
			value = minf(value, 4.0)
		RenderingServer.global_shader_parameter_set("tinta_" + key, value)
	RenderingServer.global_shader_parameter_set("tinta_miedo", clampf(fear, 0.0, 1.0))
	RenderingServer.global_shader_parameter_set("tinta_radiacion", clampf(radiation, 0.0, 1.0))
