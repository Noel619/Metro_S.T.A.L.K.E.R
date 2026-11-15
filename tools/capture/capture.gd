extends SceneTree
## Hace capturas de una escena sin abrir el editor.
##
## Carga la escena, espera unos fotogramas para que la luz y los shaders se
## asienten y guarda una imagen por cada cámara del grupo "capture_camera".
## No se lanza a mano: lo hace tools/capture.sh.
##
## Argumentos (después de "--"):
##   --scene=res://ruta/escena.tscn   escena que se captura
##   --out=ruta/salida.png            imagen; con varias cámaras, se añade el nombre
##   --frames=30                      fotogramas de espera antes de capturar
##   --hide=Nodo                      oculta los nodos con ese nombre (p. ej. InkPost)
##   --post=parametro=valor           fija un parámetro del post-proceso (p. ej. debug_view=3)
##   --call=Nodo:metodo[:valor]       llama a un método de los nodos con ese nombre
##                                    (p. ej. PanelDepuracion:toggle o DioramaPatio:set_hour:18.5)

const CAMERA_GROUP: StringName = &"capture_camera"

var _scene_path: String = ""
var _out_path: String = ""
var _frames: int = 30
var _hidden: PackedStringArray = []
var _post_params: Dictionary = {}
var _calls: PackedStringArray = []


func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		var value: String = arg.get_slice("=", 1)
		if arg.begins_with("--scene="):
			_scene_path = value
		elif arg.begins_with("--out="):
			_out_path = value
		elif arg.begins_with("--frames="):
			_frames = maxi(1, value.to_int())
		elif arg.begins_with("--hide="):
			_hidden.append(value)
		elif arg.begins_with("--call="):
			_calls.append(arg.trim_prefix("--call="))
		elif arg.begins_with("--post="):
			var pair: String = arg.trim_prefix("--post=")
			_post_params[pair.get_slice("=", 0)] = pair.get_slice("=", 1).to_float()
	if _scene_path.is_empty() or _out_path.is_empty():
		printerr("Uso: --scene=res://... --out=salida.png [--frames=30]")
		quit(1)
		return
	_capture.call_deferred()


func _capture() -> void:
	var packed: PackedScene = load(_scene_path)
	if packed == null:
		printerr("No se pudo cargar %s" % _scene_path)
		quit(1)
		return
	var scene: Node = packed.instantiate()
	root.add_child(scene)
	if not _post_params.is_empty():
		for post: Node in scene.find_children("InkPost", "MeshInstance3D", true, false):
			var mesh: MeshInstance3D = post as MeshInstance3D
			var material: ShaderMaterial = mesh.get_surface_override_material(0).duplicate()
			for param: String in _post_params:
				material.set_shader_parameter(param, _post_params[param])
			mesh.set_surface_override_material(0, material)
	for node_name: String in _hidden:
		for node: Node in scene.find_children(node_name, "", true, false):
			if node is Node3D:
				(node as Node3D).visible = false
	for call: String in _calls:
		_call_on(scene, call)
	var cameras: Array[Node] = get_nodes_in_group(CAMERA_GROUP)
	if cameras.is_empty():
		# Sin cámaras del grupo: la cámara activa o, en escenas 2D, ninguna.
		cameras = [root.get_camera_3d()]
	for camera: Node in cameras:
		if camera != null:
			(camera as Camera3D).make_current()
		for _i in _frames:
			await process_frame
		await RenderingServer.frame_post_draw
		var path: String = _out_path
		if cameras.size() > 1:
			path = _out_path.get_basename() + "_" + String(camera.name).to_snake_case() + ".png"
		var image: Image = root.get_texture().get_image()
		var err: Error = image.save_png(path)
		if err != OK:
			printerr("No se pudo guardar %s (%s)" % [path, error_string(err)])
			quit(1)
			return
		print("Captura: %s (%dx%d)" % [path, image.get_width(), image.get_height()])
	quit(0)


func _call_on(scene: Node, call: String) -> void:
	var parts: PackedStringArray = call.split(":")
	if parts.size() < 2:
		printerr("--call necesita Nodo:metodo")
		return
	var targets: Array[Node] = scene.find_children(parts[0], "", true, false)
	if scene.name == parts[0]:
		targets.append(scene)
	for node: Node in targets:
		if parts.size() > 2:
			var value: Variant = parts[2]
			if parts[2].is_valid_int():
				value = parts[2].to_int()
			elif parts[2].is_valid_float():
				value = parts[2].to_float()
			node.call(parts[1], value)
		else:
			node.call(parts[1])
