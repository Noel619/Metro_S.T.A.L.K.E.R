extends "res://tests/test_case.gd"


func before_each() -> void:
	GameState.reset_for_new_game("  Prueba  ")


func test_reset_sets_starting_values() -> void:
	assert_eq(GameState.player_name, "Prueba", "el nombre se guarda sin espacios")
	assert_eq(GameState.day, 1)
	assert_eq(GameState.rubles, GameState.STARTING_RUBLES)
	assert_eq(GameState.debt, 0)


func test_spend_only_if_enough() -> void:
	assert_true(GameState.try_spend(100))
	assert_eq(GameState.rubles, GameState.STARTING_RUBLES - 100)
	assert_false(GameState.try_spend(1000), "no se puede gastar más de lo que hay")
	assert_false(GameState.try_spend(-5), "no se puede gastar una cantidad negativa")
	assert_eq(GameState.rubles, GameState.STARTING_RUBLES - 100)


func test_rubles_changed_signal() -> void:
	var received: Array = []
	var on_changed: Callable = func(total: int, delta: int) -> void: received.append([total, delta])
	EventBus.rubles_changed.connect(on_changed)
	GameState.add_rubles(25)
	GameState.add_rubles(0)
	EventBus.rubles_changed.disconnect(on_changed)
	assert_eq(received, [[GameState.STARTING_RUBLES + 25, 25]])


func test_state_roundtrip() -> void:
	GameState.add_rubles(42)
	GameState.day = 7
	GameState.flags["rastro_padre_1"] = true
	var saved: Dictionary = GameState.save_state()
	GameState.reset_for_new_game("Otra persona")
	GameState.load_state(saved)
	assert_eq(GameState.player_name, "Prueba")
	assert_eq(GameState.day, 7)
	assert_eq(GameState.rubles, GameState.STARTING_RUBLES + 42)
	assert_eq(GameState.flags, {"rastro_padre_1": true})
