extends Node
## Guardado único con muerte permanente.
##
## Hay un solo archivo de partida. Se escribe primero en un archivo temporal y
## luego se renombra, para que un corte no lo deje a medias. Al morir se borra:
## no hay vuelta atrás.
##
## Cualquier sistema puede aportar su parte registrándose como proveedor: un
## objeto con [code]save_state() -> Dictionary[/code] y
## [code]load_state(data: Dictionary) -> void[/code].
##
## Lo de una escena que no está cargada (el depósito mientras se está arriba, la
## superficie mientras se está abajo) queda "aparcado": su último estado se
## guarda igual en el archivo, y la escena lo recupera al volver
## ([method park_all], [method restore_parked]).

const SAVE_VERSION: int = 1
const DEFAULT_PATH: String = "user://partida.json"

## Ruta del archivo. Los tests la cambian para no tocar la partida real.
var save_path: String = DEFAULT_PATH

var _providers: Dictionary = {}
## Lo aparcado: clave -> su último estado.
var _parked: Dictionary = {}


func register_provider(key: String, provider: Object) -> void:
	assert(provider.has_method("save_state") and provider.has_method("load_state"))
	_providers[key] = provider


func unregister_provider(key: String) -> void:
	_providers.erase(key)


func has_save() -> bool:
	return FileAccess.file_exists(save_path)


## Guarda la partida. Solo el anfitrión guarda.
func save_game() -> Error:
	if not multiplayer.is_server():
		return ERR_UNAUTHORIZED
	var sections: Dictionary = _parked.duplicate(true)
	for key: String in _providers:
		sections[key] = _providers[key].save_state()
	var data: Dictionary = {
		"version": SAVE_VERSION,
		"saved_at": Time.get_datetime_string_from_system(true),
		"sections": sections,
	}
	var err: Error = _write_atomic(save_path, JSON.stringify(data, "\t"))
	if err == OK:
		EventBus.game_saved.emit()
	return err


func load_game() -> Error:
	if not has_save():
		return ERR_FILE_NOT_FOUND
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not parsed is Dictionary:
		return ERR_PARSE_ERROR
	var data: Dictionary = _migrate(parsed)
	var sections: Dictionary = data.get("sections", {})
	_parked.clear()
	for key: String in sections:
		if _providers.has(key):
			_providers[key].load_state(sections[key])
		elif sections[key] is Dictionary:
			_parked[key] = sections[key]
	return OK


## Aparca el estado de los proveedores de la escena (al irse de ella: lo que
## registró dejará de estar, pero su estado sigue en la partida). Los que no son
## de la escena (las autocargas, como el estado de la partida) siguen vivos.
func park_all() -> void:
	for key: String in _providers:
		var provider: Node = _providers[key] as Node
		if (
			provider != null
			and provider.is_inside_tree()
			and provider.get_parent() != get_tree().root
		):
			_parked[key] = _providers[key].save_state()


## Hay algo aparcado con esta clave.
func has_parked(key: String) -> bool:
	return _parked.has(key)


## Devuelve lo aparcado a los proveedores que hay ahora (al volver a una escena) y
## lo quita de lo aparcado. Devuelve las claves recuperadas.
func restore_parked() -> PackedStringArray:
	var restored: PackedStringArray = []
	for key: String in _providers:
		if _parked.has(key):
			_providers[key].load_state(_parked[key])
			_parked.erase(key)
			restored.append(key)
	return restored


## Olvida lo aparcado (partida nueva o perdida).
func clear_parked() -> void:
	_parked.clear()


## Muerte permanente: borra la partida (y lo aparcado).
func delete_save() -> void:
	_parked.clear()
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(save_path))


func _migrate(data: Dictionary) -> Dictionary:
	# Aquí se adaptarán las partidas antiguas cuando cambie SAVE_VERSION.
	return data


func _write_atomic(path: String, text: String) -> Error:
	var tmp_path: String = path + ".tmp"
	var file: FileAccess = FileAccess.open(tmp_path, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(text)
	file.close()
	var absolute_path: String = ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(absolute_path)
	return DirAccess.rename_absolute(ProjectSettings.globalize_path(tmp_path), absolute_path)
