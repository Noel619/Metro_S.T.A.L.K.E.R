extends "res://tests/test_case.gd"

const TEST_PATH: String = "user://test_partida.json"

var _original_path: String


func before_each() -> void:
	_original_path = SaveSystem.save_path
	SaveSystem.save_path = TEST_PATH
	SaveSystem.delete_save()
	GameState.reset_for_new_game("Ana")


func after_each() -> void:
	SaveSystem.delete_save()
	SaveSystem.save_path = _original_path


func test_save_and_load_roundtrip() -> void:
	GameState.add_rubles(10)
	GameState.day = 3
	assert_eq(SaveSystem.save_game(), OK)
	assert_true(SaveSystem.has_save())
	GameState.reset_for_new_game("Otra")
	assert_eq(SaveSystem.load_game(), OK)
	assert_eq(GameState.player_name, "Ana")
	assert_eq(GameState.day, 3)
	assert_eq(GameState.rubles, GameState.STARTING_RUBLES + 10)


func test_file_has_version_and_no_temp_left() -> void:
	assert_eq(SaveSystem.save_game(), OK)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TEST_PATH))
	assert_eq(int(data["version"]), SaveSystem.SAVE_VERSION)
	assert_true(data["sections"].has(GameState.SAVE_KEY))
	assert_false(FileAccess.file_exists(TEST_PATH + ".tmp"), "no debe quedar el archivo temporal")


func test_death_deletes_save() -> void:
	assert_eq(SaveSystem.save_game(), OK)
	SaveSystem.delete_save()
	assert_false(SaveSystem.has_save())
	assert_eq(SaveSystem.load_game(), ERR_FILE_NOT_FOUND)


func test_overwrites_previous_save() -> void:
	assert_eq(SaveSystem.save_game(), OK)
	GameState.day = 9
	assert_eq(SaveSystem.save_game(), OK)
	GameState.day = 1
	assert_eq(SaveSystem.load_game(), OK)
	assert_eq(GameState.day, 9)
