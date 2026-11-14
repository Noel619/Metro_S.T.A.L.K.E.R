extends "res://tests/test_case.gd"

const TEST_PATH: String = "user://test_ajustes.cfg"

var _original_path: String
var _original_values: Dictionary


func before_each() -> void:
	_original_path = Settings.settings_path
	_original_values = {
		"scaling_mode": Settings.scaling_mode,
		"render_scale": Settings.render_scale,
		"mouse_sensitivity": Settings.mouse_sensitivity,
		"reduce_line_boil": Settings.reduce_line_boil,
	}
	Settings.settings_path = TEST_PATH


func after_each() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_PATH))
	Settings.settings_path = _original_path
	for key: String in _original_values:
		Settings.set(key, _original_values[key])


func test_roundtrip() -> void:
	Settings.scaling_mode = "fsr2"
	Settings.render_scale = 0.77
	Settings.mouse_sensitivity = 0.4
	Settings.reduce_line_boil = true
	assert_eq(Settings.save_settings(), OK)
	Settings.scaling_mode = "nativo"
	Settings.render_scale = 1.0
	Settings.mouse_sensitivity = 0.1
	Settings.reduce_line_boil = false
	Settings.load_settings()
	assert_eq(Settings.scaling_mode, "fsr2")
	assert_almost(Settings.render_scale, 0.77)
	assert_almost(Settings.mouse_sensitivity, 0.4)
	assert_true(Settings.reduce_line_boil)


func test_invalid_values_fall_back() -> void:
	var config: ConfigFile = ConfigFile.new()
	config.set_value("video", "scaling_mode", "magia")
	config.set_value("video", "render_scale", 9.0)
	config.save(TEST_PATH)
	Settings.load_settings()
	assert_eq(Settings.scaling_mode, "nativo")
	assert_almost(Settings.render_scale, 1.0)
