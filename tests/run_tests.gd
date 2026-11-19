extends SceneTree
## Ejecuta todos los tests de tests/unit/ sin pantalla.
## Sale con código 1 si alguno falla. Un test también falla si provoca un error
## de script (un acceso a algo ya liberado, un método que no existe…): sin esto,
## el test se cortaba en ese punto y contaba como bueno.
##
## Uso: godot --headless --path . -s tests/run_tests.gd

const UNIT_DIR: String = "res://tests/unit/"

var _errors: ScriptErrors = ScriptErrors.new()


## Recoge los errores de script mientras corre un test.
class ScriptErrors:
	extends Logger
	var _lines: PackedStringArray = []
	var _mutex: Mutex = Mutex.new()

	func _log_error(
		function: String,
		file: String,
		line: int,
		code: String,
		_rationale: String,
		_editor_notify: bool,
		error_type: int,
		_script_backtrace: Array[ScriptBacktrace]
	) -> void:
		if error_type != ERROR_TYPE_SCRIPT:
			return
		_mutex.lock()
		_lines.append("error de script: %s (%s:%d, %s)" % [code, file.get_file(), line, function])
		_mutex.unlock()

	## Los errores recogidos desde la última vez.
	func take() -> PackedStringArray:
		_mutex.lock()
		var lines: PackedStringArray = _lines.duplicate()
		_lines.clear()
		_mutex.unlock()
		return lines


func _initialize() -> void:
	OS.add_logger(_errors)
	_run.call_deferred()


func _run() -> void:
	# Deja que las autocargas terminen su _ready().
	await process_frame
	var total: int = 0
	var failed: int = 0
	for file_name: String in _test_files():
		# Lo que un archivo deja colgado de la raíz (la ciudad de los tests de la maqueta, que
		# se levanta una vez para todos) se quita al acabar, para que no estorbe a los demás.
		var present: Array[Node] = root.get_children()
		var script: GDScript = load(UNIT_DIR + file_name)
		for method: Dictionary in script.get_script_method_list():
			var test_name: String = method["name"]
			if not test_name.begins_with("test_"):
				continue
			total += 1
			var test_case: Node = script.new()
			test_case.current_test = test_name
			root.add_child(test_case)
			_errors.take()
			await test_case.before_each()
			await test_case.call(test_name)
			await test_case.after_each()
			test_case.failures.append_array(_errors.take())
			if test_case.failures.is_empty():
				print("  ok    %s › %s" % [file_name, test_name])
			else:
				failed += 1
				print("  FALLO %s › %s" % [file_name, test_name])
				for failure: String in test_case.failures:
					print("        %s" % failure)
			test_case.queue_free()
			await process_frame
		for child: Node in root.get_children():
			if not present.has(child):
				child.free()
		await physics_frame
	print("\n%d tests, %d fallos." % [total, failed])
	quit(1 if failed > 0 else 0)


func _test_files() -> PackedStringArray:
	var files: PackedStringArray = []
	for file_name: String in DirAccess.get_files_at(UNIT_DIR):
		if file_name.begins_with("test_") and file_name.ends_with(".gd"):
			files.append(file_name)
	files.sort()
	return files
