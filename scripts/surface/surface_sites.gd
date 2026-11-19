class_name SurfaceSites
extends Node3D
## Los sitios de La Plaza (F3-14, docs/SUPERFICIE.md 9): pone lo que se usa en los
## edificios menores que monta el kit ([KitMinor]): sus puertas, cada una con su cierre,
## y sus escaleras; y, la primera vez que se sube en la partida, el botín donde puede
## haberlo. También lo que no es de ningún edificio del kit: las señales de la Jauría (los
## huesos roídos donde come) y la marca de tu padre.
##
## Las puertas y las escaleras se ponen igual en todos los equipos (mismo nombre, mismo
## sitio), así que se nombran por la red; cómo está cerrada cada puerta sale de su nombre
## (siempre igual) y lo que se le haga se guarda en el mundo ([DepotWorld]). El botín lo
## pone el anfitrión una vez por partida: el mundo recuerda que ya está ("botin").

## Lo que puede haber en cada clase de sitio, con su peso.
const LOOT: Dictionary = {
	"quiosco":
	{
		"papeles": 4.0,
		"cerillas": 3.0,
		"lata_conserva": 2.0,
		"bolsa_plastico": 1.5,
		"billetes": 1.2,
		"botella_verde": 1.0,
		"etiqueta": 1.0,
		"radio_bolsillo": 0.3,
	},
	"tienda":
	{
		"trapo": 3.0,
		"lata_conserva": 3.0,
		"vendas": 1.5,
		"aguja_hilo": 1.0,
		"botas": 1.0,
		"cuerda": 1.0,
		"mascara": 0.8,
		"pan": 0.6,
		"linterna": 0.5,
		"botiquin": 0.4,
	},
	"trastero":
	{
		"lena": 3.0,
		"lata_conserva": 2.0,
		"botella_marron": 2.0,
		"bombilla": 1.2,
		"destornillador": 1.2,
		"cuerda": 1.0,
		"cubo": 1.0,
		"martillo": 0.8,
		"chatarra_cobre": 0.8,
		"cepillo_alambre": 0.6,
		"palanca": 0.3,
	},
	"palomar": {"papeles": 2.0, "lata_vacia": 2.0, "prismaticos": 1.0},
	"transformador": {"chatarra_cobre": 4.0, "bombilla": 1.0, "destornillador": 0.8},
}
## Lo que hay siempre en algunos sitios (clase -> índice del sitio -> objeto): los
## prismáticos del palomero, colgados en su altillo.
const FIXED: Dictionary = {"palomar": {2: "prismaticos"}}
## Lo que se queda vacío de cada clase (de cada sitio donde podría haber algo).
const EMPTY: Dictionary = {
	"quiosco": 0.3, "tienda": 0.35, "trastero": 0.45, "palomar": 0.2, "transformador": 0.35
}
## El botín se pone en los edificios de La Plaza (los de los demás barrios, cuando se
## pueda ir a ellos).
const LOOT_PREFIX: String = "PLZ-"
const WORLD_ID: String = "botin"
## Las puertas se dejan de dibujar desde aquí (de lejos las tapa el volumen del edificio).
const DOOR_RANGE: float = 160.0
## Donde come la Jauría: en el plano, cuántos montones de huesos y en qué radio.
const BONE_SITES: Array[Dictionary] = [
	{"centro": Vector2(220.0, 98.0), "montones": 6, "radio": 24.0},
	{"centro": Vector2(265.0, 170.0), "montones": 4, "radio": 30.0},
	{"centro": Vector2(300.0, 250.0), "montones": 3, "radio": 18.0},
]

var city: City
var world: DepotWorld
var items: WorldItems
var doors: Array[SurfaceDoor] = []
var ladders: Array[Climbable] = []


func setup(surface_city: City, surface_world: DepotWorld, surface_items: WorldItems) -> void:
	city = surface_city
	world = surface_world
	items = surface_items
	name = "Sitios"


func _ready() -> void:
	if city == null:
		return
	var ids: Array = city.kit_models.keys()
	ids.sort()
	for id: Variant in ids:
		var model: Node3D = city.kit_models[id]
		for door: Dictionary in model.get_meta(&"kit_puertas", []):
			_add_door(model, door)
		for ladder: Dictionary in model.get_meta(&"kit_trepables", []):
			var climbable: Climbable = Climbable.make(ladder["pie"], ladder["tamano"])
			model.add_child(climbable)
			ladders.append(climbable)
	_add_bones()


## Cómo empieza cerrada la puerta [param id] (de entre [param weights]): su cierre y si
## está abierta. Sale de su nombre: siempre la misma.
static func initial_state(id: String, weights: Dictionary) -> Dictionary:
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = hash(id + ":cierre")
	var lock: String = _pick(weights, rng)
	return {"cierre": lock, "abierta": lock.is_empty() and rng.randf() < 0.5}


## El botín de un sitio de la clase [param kind] con [param rng]: un objeto o "".
static func roll_loot(kind: String, rng: RandomNumberGenerator) -> String:
	if rng.randf() < float(EMPTY.get(kind, 0.5)):
		return ""
	return _pick(LOOT.get(kind, {}), rng)


func _add_door(model: Node3D, spec: Dictionary) -> void:
	var start: Dictionary = initial_state(spec["id"], spec["cierres"])
	var door: SurfaceDoor = SurfaceDoor.new()
	door.initial_lock = StringName(start["cierre"])
	door.initial_open = start["abierta"]
	door.lock_point = spec["punto"]
	var meshes: Dictionary = {
		"candado": city.kit_mesh("candado"), "cadena": city.kit_mesh("cadena")
	}
	door.setup(spec["id"], spec["bisagra"], spec["tamano"], city.kit_mesh(spec["pieza"]), meshes)
	for visual: Node in door.find_children("*", "GeometryInstance3D", true, false):
		(visual as GeometryInstance3D).visibility_range_end = DOOR_RANGE
	model.add_child(door)
	doors.append(door)


## En el anfitrión: abre a los perros el interior de los menores y el paso de sus puertas
## abiertas (las cerradas los dejan fuera); cuando una puerta se abre o se cierra, su paso
## cambia con ella.
func carve(nav: CityNav) -> void:
	if nav == null:
		return
	var by_id: Dictionary = {}
	for door: SurfaceDoor in doors:
		by_id[door.fixture_id] = door
	for id: Variant in city.kit_models:
		carve_model(nav, city.kit_models[id], by_id)


## Lo mismo para un edificio ([param by_id]: sus puertas por su id).
static func carve_model(nav: CityNav, model: Node3D, by_id: Dictionary) -> void:
	for polygon: PackedVector2Array in model.get_meta(&"kit_interiores", []):
		nav.open_polygon(polygon)
	for passage: Dictionary in model.get_meta(&"kit_pasos", []):
		nav.set_points(passage["llegada"], false)
		var gap: PackedVector2Array = passage["hueco"]
		var door: SurfaceDoor = by_id.get(passage["puerta"]) as SurfaceDoor
		nav.set_points(gap, door != null and not door.is_open())
		if door != null:
			door.refreshed.connect(func() -> void: nav.set_points(gap, not door.is_open()))


## En el anfitrión, la primera vez que se sube en la partida (después de recuperar lo que
## se dejó): el botín de los edificios de La Plaza.
func seed_loot() -> void:
	if world == null or items == null or bool(world.value(WORLD_ID, "sembrado", false)):
		return
	var game_seed: int = randi()
	world.set_values(WORLD_ID, {"sembrado": true, "semilla": game_seed})
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	var ids: Array = city.kit_models.keys()
	ids.sort()
	for id: Variant in ids:
		if not String(id).begins_with(LOOT_PREFIX):
			continue
		var model: Node3D = city.kit_models[id]
		var points: Array = model.get_meta(&"kit_botin", [])
		for index: int in points.size():
			var spot: Dictionary = points[index]
			rng.seed = hash("%s:%d:%d" % [id, index, game_seed])
			var item: String = roll_loot(String(spot["tipo"]), rng)
			var fixed: Dictionary = FIXED.get(String(spot["tipo"]), {})
			if fixed.has(index):
				item = fixed[index]
			if item.is_empty():
				continue
			var at: Vector3 = model.global_transform * (spot["punto"] as Vector3)
			var turn: Basis = Basis(Vector3.UP, rng.randf() * TAU)
			items.spawn_item(StringName(item), Transform3D(turn, at + Vector3.UP * 0.04))


## Los huesos roídos donde come la Jauría: una malla repetida, sobre el suelo.
func _add_bones() -> void:
	var mesh: Mesh = city.kit_mesh("huesos")
	if mesh == null:
		return
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = hash("huesos")
	var spots: Array[Transform3D] = []
	for site: Dictionary in BONE_SITES:
		for _pile: int in int(site["montones"]):
			var plan: Vector2 = (
				(site["centro"] as Vector2)
				+ Vector2.from_angle(rng.randf() * TAU) * (sqrt(rng.randf()) * float(site["radio"]))
			)
			var where: Vector3 = CityPlan.to_world(plan, city.surface_height(plan))
			spots.append(
				Transform3D(Basis(Vector3.UP, rng.randf() * TAU), where + Vector3.UP * 0.01)
			)
	var multimesh: MultiMesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = mesh
	multimesh.instance_count = spots.size()
	for index: int in spots.size():
		multimesh.set_instance_transform(index, spots[index])
	var bones: MultiMeshInstance3D = MultiMeshInstance3D.new()
	bones.name = "Huesos"
	bones.multimesh = multimesh
	bones.visibility_range_end = 120.0
	add_child(bones)


static func _pick(weights: Dictionary, rng: RandomNumberGenerator) -> String:
	var total: float = 0.0
	for key: Variant in weights:
		total += float(weights[key])
	var roll: float = rng.randf() * total
	for key: Variant in weights:
		roll -= float(weights[key])
		if roll <= 0.0:
			return String(key)
	return ""
