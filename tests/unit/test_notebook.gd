extends "res://tests/test_case.gd"
## El cuaderno (F3-04): Tab lo saca con las manos libres; se dibuja con el lápiz (y los
## trazos se guardan como vectores, aligerados), la goma borra, la regla traza rectas,
## los sellos se estampan (el del reloj con la hora que marca el tuyo), se escriben notas
## y se pasan las hojas; el miedo hace temblar el trazo; se guarda con la partida y, si
## mueres, se pierde contigo.

var _world: Node3D
var _player: Player


func before_each() -> void:
	GameState.reset_for_new_game("Prueba")
	GameState.minute = 14.0 * 60.0 + 20.0


func after_each() -> void:
	if NotebookView.is_open():
		NotebookView.active.free()
	if _world != null:
		_world.free()
	GameState.reset_for_new_game("")


func test_drawing_a_stroke_keeps_it_as_a_vector() -> void:
	var view: NotebookView = await _open()
	assert_true(view != null and NotebookView.is_open(), "Tab saca el cuaderno")
	view.cursor = Vector2(1.2, 0.3)
	view.press(true)
	for step: int in 60:
		view.move_pencil(Vector2(4.0, 2.0 + sin(step * 0.2) * 3.0))
	view.press(false)
	await _frames(2)
	var page: Dictionary = GameState.notebook(_player.slot).pages[1]
	assert_eq((page["trazos"] as Array).size(), 1, "en la hoja de la derecha")
	var points: PackedVector2Array = Notebook.points_of(page["trazos"][0])
	assert_true(points.size() >= 3 and points.size() < 60, "aligerado (%d puntos)" % points.size())
	assert_almost(points[0].x, 0.2, 0.01, "empieza donde estaba el lápiz")
	assert_eq(int(page["trazos"][0]["c"]), 0, "de grafito")


func test_eraser_ruler_and_colours() -> void:
	var view: NotebookView = await _open()
	view.cursor = Vector2(0.2, 0.5)
	view.cycle_tool(2)
	assert_eq(view.tool(), "rojo")
	view.use_ruler(true)
	view.move_pencil(Vector2(400.0, 0.0))
	view.use_ruler(false)
	await _frames(2)
	var strokes: Array = GameState.notebook(_player.slot).pages[0]["trazos"]
	assert_eq(strokes.size(), 1, "la regla traza una recta")
	if strokes.size() == 1:
		var line: PackedVector2Array = Notebook.points_of(strokes[0])
		assert_eq(line.size(), 2, "de dos puntos")
		assert_almost(line[0].y, line[1].y, 0.001, "derecha")
		assert_eq(int(strokes[0]["c"]), 1, "en rojo")
	# La goma, sobre la recta.
	view.cycle_tool(-1)
	assert_eq(view.tool(), "goma")
	view.cursor = Vector2(0.4, 0.5)
	view.press(true)
	await _frames(15)
	view.press(false)
	await _frames(2)
	assert_true(
		(GameState.notebook(_player.slot).pages[0]["trazos"] as Array).is_empty(),
		"la goma la borra"
	)


func test_stamps_notes_and_pages() -> void:
	var view: NotebookView = await _open()
	view.tool_index = NotebookView.tools().find("reloj")
	view.cursor = Vector2(1.5, 0.2)
	view.press(true)
	view.press(false)
	view.tool_index = NotebookView.tools().find("perro")
	view.cursor = Vector2(1.5, 0.6)
	view.press(true)
	view.press(false)
	await _frames(2)
	var stamps: Array = GameState.notebook(_player.slot).pages[1]["sellos"]
	assert_eq(stamps.size(), 2, "dos sellos")
	if stamps.size() == 2:
		assert_eq(stamps[0]["t"], "visto a las 14:20", "el reloj escribe la hora del tuyo")
		assert_eq(stamps[1]["s"], "perro")
	view.cursor = Vector2(0.3, 0.8)
	view.start_note()
	view._note.text_submitted.emit("Perros en la estación")
	await _frames(2)
	var notes: Array = GameState.notebook(_player.slot).pages[0]["notas"]
	assert_eq(notes.size(), 1)
	if notes.size() == 1:
		assert_eq(notes[0]["t"], "Perros en la estación")
	view.turn(1)
	assert_eq(_player.notebook.spread, 1, "D pasa la hoja")
	view.tool_index = 0
	view.cursor = Vector2(0.5, 0.5)
	view.press(true)
	view.move_pencil(Vector2(60.0, 60.0))
	view.press(false)
	await _frames(2)
	assert_eq((GameState.notebook(_player.slot).pages[2]["trazos"] as Array).size(), 1, "en la 3")
	view.turn(-5)
	assert_eq(_player.notebook.spread, 0, "no hay hojas antes de la primera")


func test_fear_shakes_the_line() -> void:
	var view: NotebookView = await _open()
	_player.tremble = Fear.HANDS_TREMBLE
	view.cursor = Vector2(0.1, 0.5)
	view.press(true)
	for _step: int in 80:
		view._clock += 0.016
		view.move_pencil(Vector2(5.0, 0.0))
	view.press(false)
	await _frames(2)
	var line: PackedVector2Array = Notebook.points_of(
		GameState.notebook(_player.slot).pages[0]["trazos"][0]
	)
	var wander: float = 0.0
	for point: Vector2 in line:
		wander = maxf(wander, absf(point.y - 0.5))
	assert_true(wander > 0.003, "con miedo el trazo tiembla (%.4f)" % wander)


func test_it_is_saved_and_lost_with_you() -> void:
	var notebook: Notebook = Notebook.new()
	notebook.add_stroke(3, 2, PackedVector2Array([Vector2(0.1, 0.1), Vector2(0.5, 0.4)]))
	notebook.add_note(3, Vector2(0.2, 0.2), "Llave bajo la maceta")
	GameState.set_notebook(0, notebook)
	var saved: Dictionary = GameState.save_state()
	GameState.reset_for_new_game("Otra")
	assert_true(GameState.notebook(0).is_empty(), "una partida nueva, en blanco")
	GameState.load_state(saved)
	var loaded: Notebook = GameState.notebook(0)
	assert_eq((loaded.pages[3]["trazos"] as Array).size(), 1, "se guarda con la partida")
	assert_eq(loaded.pages[3]["notas"][0]["t"], "Llave bajo la maceta")
	GameState.lose_notebook(0)
	assert_true(GameState.notebook(0).is_empty(), "si mueres, se pierde contigo")


func test_hands_must_be_free() -> void:
	await _build_world()
	var items: WorldItems = WorldItems.new()
	items.save_key = "objetos_prueba"
	_world.add_child(items)
	items.give(_player, &"lata_vacia")
	for _i in 40:
		await get_tree().physics_frame
	assert_true(_player.held_item() != null, "lleva la lata")
	_player.notebook.toggle(get_viewport().get_camera_3d())
	assert_false(NotebookView.is_open(), "con algo en las manos no se saca")
	_player.held_item().request_drop()
	for _i in 20:
		await get_tree().physics_frame
	_player.notebook.toggle(get_viewport().get_camera_3d())
	assert_true(NotebookView.is_open(), "con las manos libres, sí")


func _open() -> NotebookView:
	await _build_world()
	_player.notebook.toggle(get_viewport().get_camera_3d())
	await _frames(2)
	return NotebookView.active


func _build_world() -> void:
	_world = Node3D.new()
	add_child(_world)
	_player = Player.new()
	_player.setup(1, "chico", 0)
	_world.add_child(_player)
	await _frames(5)


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().process_frame
