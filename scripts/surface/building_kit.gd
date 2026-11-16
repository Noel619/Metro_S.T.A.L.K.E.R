class_name BuildingKit
extends RefCounted
## El kit de arquitectura soviética (F3-16): monta cada edificio con las piezas que generan
## las recetas de tools/blender/recipes/kit_*.py, a partir de su ficha (la del plano o una
## hecha a mano para un diorama).
##
## La ficha de un edificio ([method build]) es un diccionario:
## - "tipo": el del plano (jrushchovka, bloque9, torre16…).
## - "huella": PackedVector2Array, la planta en metros (x al este, y al norte).
## - "origen": Vector2, el punto del plano que queda en el origen del nodo, a la cota 0.
##   Por defecto, el centro de la huella.
## - "pisos": las plantas. "dano": del 1 al 4 (docs/CIUDAD.md). "incendio": "no",
##   "parcial" o "total".
## - "clave": la semilla de todo lo que varía (el id del plano): el mismo edificio sale
##   siempre igual.
## - "bomba": Vector2, dónde cayó la bomba: el extremo que la mira se hunde antes y su
##   fachada pierde más cristales.
## - Opcionales de cada familia. Los bloques de paneles: "entrada" (el lado de los
##   portales, un índice de la huella) y "portales". Las casas de muros de carga:
##   "patios" (puntos dentro de los patios: los lados que los miran son fachadas de patio),
##   "comercios" (escaparates en los bajos de la calle) y "arco" (un arco al patio).
##
## Las casas de madera (la isba y el barracón) no se montan por vanos: el kit las tiene
## enteras y se escoge la de su estado (KitWhole). Los edificios singulares (los hitos y los
## sitios clave) son un modelo entero cada uno, por su id del plano (KitSingular).
##
## Cada pieza se repite con una MultiMesh: una llamada de dibujo por pieza y edificio.
## Algunos tipos visten las mismas piezas con otro material (sus "pieles"): los bloques
## altos llevan plaqueta en vez de hormigón pintado.

const LIBRARIES: PackedStringArray = [
	"res://assets/models/kit_paneles.glb",
	"res://assets/models/kit_estalinka.glb",
	"res://assets/models/kit_ladrillo.glb",
	"res://assets/models/kit_madera.glb",
	"res://assets/models/singular_vestibulo.glb",
	"res://assets/models/singular_partido.glb",
	"res://assets/models/singular_soviets.glb",
]
const MATERIALS_DIR: String = "res://assets/materials/"
## La familia de reglas que monta cada tipo del plano.
const FAMILIES: Dictionary = {
	"jrushchovka": "paneles",
	"bloque9": "paneles",
	"torre16": "paneles",
	"estalinka": "mamposteria",
	"estalinka_baja": "mamposteria",
	"prerrevolucion": "mamposteria",
	"casa_madera": "entera",
	"barracon": "entera",
}
## Los materiales que cambia cada tipo.
const SKINS: Dictionary = {
	"bloque9": {"muro": "azulejo"},
	"torre16": {"muro": "azulejo"},
}

var _base: Dictionary = {}
var _skinned: Dictionary = {}


func _init() -> void:
	for path: String in LIBRARIES:
		_load_library(path)


## ¿Sabe montar este tipo del plano?
static func supports(kind: String) -> bool:
	return FAMILIES.has(kind)


## ¿Sabe montar este edificio del plano (o esta ficha)? Los de los tipos del kit y los
## singulares, que van por su id.
static func supports_building(building: Dictionary) -> bool:
	var key: String = String(building.get("id", building.get("clave", "")))
	return supports(String(building.get("tipo", ""))) or KitSingular.MODELS.has(key)


## Los nombres de todas las piezas del kit.
func piece_names() -> PackedStringArray:
	var names: PackedStringArray = PackedStringArray(_base.keys())
	names.sort()
	return names


## Las mallas del kit para un tipo, con su piel.
func meshes_for(kind: String) -> Dictionary:
	if not SKINS.has(kind):
		return _base
	if not _skinned.has(kind):
		_skinned[kind] = _reskin(SKINS[kind])
	return _skinned[kind]


## Monta un edificio desde su ficha. El nodo guarda en sus metadatos cuántas piezas lleva
## ("kit_piezas") y las que ha pedido y el kit no tiene ("kit_faltan").
func build(spec: Dictionary) -> Node3D:
	var kind: String = spec["tipo"]
	var node: Node3D = Node3D.new()
	node.name = String(spec.get("clave", kind)).validate_node_name()
	var assembly: KitAssembly = KitAssembly.new(meshes_for(kind))
	var family: String = FAMILIES.get(kind, "")
	if KitSingular.MODELS.has(String(spec.get("clave", ""))):
		family = "singular"
	match family:
		"paneles":
			KitPanelBlock.new(spec, assembly).build(node)
		"mamposteria":
			KitMasonry.new(spec, assembly).build(node)
		"entera":
			KitWhole.new(spec, assembly).build(node)
		"singular":
			KitSingular.new(spec, assembly).build(node)
		_:
			push_error("El kit no sabe montar el tipo '%s'." % kind)
	assembly.flush(node)
	node.set_meta(&"kit_piezas", assembly.instance_total())
	node.set_meta(&"kit_faltan", assembly.missing)
	return node


func _load_library(path: String) -> void:
	if not ResourceLoader.exists(path):
		push_error("Falta la biblioteca del kit %s: genera los modelos (make models)." % path)
		return
	var scene: Node = (load(path) as PackedScene).instantiate()
	for found: Node in scene.find_children("*", "MeshInstance3D", true, false):
		var instance: MeshInstance3D = found as MeshInstance3D
		# Una copia con los materiales del juego (los pone la post-importación).
		var mesh: ArrayMesh = instance.mesh.duplicate() as ArrayMesh
		for surface: int in mesh.get_surface_count():
			var material: Material = instance.get_surface_override_material(surface)
			if material != null:
				mesh.surface_set_material(surface, material)
		_base[String(instance.name)] = mesh
	scene.free()


func _reskin(swaps: Dictionary) -> Dictionary:
	var replacements: Dictionary = {}
	for from: String in swaps:
		replacements[from] = load(MATERIALS_DIR + String(swaps[from]) + ".tres")
	var result: Dictionary = {}
	for piece: String in _base:
		var mesh: ArrayMesh = _base[piece]
		var swapped: ArrayMesh = null
		for surface: int in mesh.get_surface_count():
			var material: Material = mesh.surface_get_material(surface)
			if material == null or not replacements.has(material.resource_name):
				continue
			if swapped == null:
				swapped = mesh.duplicate() as ArrayMesh
			swapped.surface_set_material(surface, replacements[material.resource_name])
		result[piece] = swapped if swapped != null else mesh
	return result
