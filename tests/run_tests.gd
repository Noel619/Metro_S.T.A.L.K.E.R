extends SceneTree
## Ejecuta todos los tests de tests/unit/ sin pantalla.
## Sale con código 1 si alguno falla.
##
## Uso: godot --headless --path . -s tests/run_tests.gd

const UNIT_DIR: String = "res://tests/unit/"


func _initialize() -> void:
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
			await test_case.before_each()
			await test_case.call(test_name)
			await test_case.after_each()
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
