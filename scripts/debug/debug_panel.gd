extends CanvasLayer
## Panel de depuración del estilo (F1-11): herramienta de desarrollo, no interfaz
## del juego. Cambia en vivo el miedo, la radiación, la hora del día, el clima, la
## linterna, el trazo reducido y el preajuste de zona, para ver cómo reacciona el
## dibujo. Se muestra y se oculta con F1.
##
## La hora y el clima se aplican al diorama que se le pase con [method set_target]
## si este sabe hacerlo (métodos set_hour y set_weather).

const WEATHERS: PackedStringArray = ["despejado", "ventisca"]
const ZONES: Array[StringName] = [&"deposito", &"superficie", &"superficie_noche"]

var _target: Node
var _panel: PanelContainer
var _fear: HSlider
var _radiation: HSlider
var _hour: HSlider
var _hour_label: Label
var _weather: OptionButton
var _flashlight: CheckBox
var _gentle: CheckBox
var _zone: OptionButton
var _fps: Label
var _syncing: bool = false


func _ready() -> void:
	layer = 10
	_build()
	_panel.visible = false


func _process(_delta: float) -> void:
	if _panel.visible:
		_fps.text = "%d fps · %s" % [Engine.get_frames_per_second(), StyleDirector.zone]


func _unhandled_input(event: InputEvent) -> void:
	var key: InputEventKey = event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_F1:
		toggle()
		get_viewport().set_input_as_handled()


## Muestra u oculta el panel.
func toggle() -> void:
	_panel.visible = not _panel.visible
	if _panel.visible:
		sync()


## El diorama sobre el que actúan la hora y el clima.
func set_target(node: Node) -> void:
	_target = node
	sync()


## Pone los controles con los valores actuales (por si cambiaron con el teclado).
func sync() -> void:
	if _panel == null:
		return
	_syncing = true
	_fear.value = StyleDirector.fear
	_radiation.value = StyleDirector.radiation
	_gentle.button_pressed = Settings.reduce_line_boil
	_zone.selected = maxi(0, ZONES.find(StyleDirector.zone))
	var has_sky: bool = _target != null and _target.has_method(&"set_hour")
	_hour.editable = has_sky
	_weather.disabled = not has_sky
	if has_sky:
		var hour: float = _target.get(&"hour")
		if hour < 0.0:
			hour = {"dia": 12.0, "anochecer": 18.0, "noche": 23.0}.get(_target.get(&"mood"), 12.0)
		_hour.value = hour
		_weather.selected = maxi(0, WEATHERS.find(_target.get(&"weather")))
	_update_hour_label()
	var camera: Camera3D = get_viewport().get_camera_3d()
	var light: Node = null if camera == null else camera.get_node_or_null(^"Linterna")
	_flashlight.button_pressed = light != null and (light as Node3D).visible
	_syncing = false


func _build() -> void:
	_panel = PanelContainer.new()
	_panel.position = Vector2(24, 88)
	_panel.custom_minimum_size = Vector2(320, 0)
	add_child(_panel)
	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	_panel.add_child(box)
	var title: Label = Label.new()
	title.text = "Depuración del estilo (F1)"
	box.add_child(title)
	_fear = _slider(box, "Miedo", 0.0, 1.0, 0.05)
	_fear.value_changed.connect(_on_fear_changed)
	_radiation = _slider(box, "Radiación", 0.0, 1.0, 0.05)
	_radiation.value_changed.connect(_on_radiation_changed)
	_hour = _slider(box, "Hora", 0.0, 24.0, 0.25)
	_hour_label = box.get_child(box.get_child_count() - 2) as Label
	_hour.value_changed.connect(_on_hour_changed)
	_weather = OptionButton.new()
	for weather: String in WEATHERS:
		_weather.add_item(weather.capitalize())
	_weather.item_selected.connect(_on_weather_selected)
	box.add_child(_weather)
	_zone = OptionButton.new()
	for zone: StringName in ZONES:
		_zone.add_item("Estilo: %s" % zone)
	_zone.item_selected.connect(_on_zone_selected)
	box.add_child(_zone)
	_flashlight = CheckBox.new()
	_flashlight.text = "Linterna"
	_flashlight.toggled.connect(_on_flashlight_toggled)
	box.add_child(_flashlight)
	_gentle = CheckBox.new()
	_gentle.text = "Trazo vivo reducido (accesibilidad)"
	_gentle.toggled.connect(_on_gentle_toggled)
	box.add_child(_gentle)
	_fps = Label.new()
	box.add_child(_fps)


func _slider(parent: Container, text: String, low: float, high: float, step: float) -> HSlider:
	var label: Label = Label.new()
	label.text = text
	parent.add_child(label)
	var slider: HSlider = HSlider.new()
	slider.min_value = low
	slider.max_value = high
	slider.step = step
	slider.custom_minimum_size = Vector2(280, 0)
	parent.add_child(slider)
	return slider


func _update_hour_label() -> void:
	var minutes: int = roundi(_hour.value * 60.0)
	_hour_label.text = "Hora: %02d:%02d" % [minutes / 60 % 24, minutes % 60]
	if not _hour.editable:
		_hour_label.text += " (este diorama no tiene cielo)"


func _on_fear_changed(value: float) -> void:
	if not _syncing:
		StyleDirector.fear = value


func _on_radiation_changed(value: float) -> void:
	if not _syncing:
		StyleDirector.radiation = value


func _on_hour_changed(value: float) -> void:
	_update_hour_label()
	if not _syncing and _target != null and _target.has_method(&"set_hour"):
		_target.call(&"set_hour", value)


func _on_weather_selected(index: int) -> void:
	if not _syncing and _target != null and _target.has_method(&"set_weather"):
		_target.call(&"set_weather", WEATHERS[index])


func _on_zone_selected(index: int) -> void:
	if not _syncing:
		StyleDirector.set_zone(ZONES[index])


func _on_flashlight_toggled(on: bool) -> void:
	if _syncing:
		return
	var camera: Camera3D = get_viewport().get_camera_3d()
	if camera == null:
		return
	var light: SpotLight3D = Flashlight.attach(camera)
	light.visible = on


func _on_gentle_toggled(on: bool) -> void:
	if not _syncing:
		Settings.reduce_line_boil = on
