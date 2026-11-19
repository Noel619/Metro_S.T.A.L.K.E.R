class_name SurfacePack
extends Node3D
## La Jauría en la superficie (F3-10): sus seis perros (replicados), la rejilla por
## la que se mueven ([CityNav]), sus rutas y su guarida, y la manada que decide
## ([Pack], en el anfitrión). La guarida es la de los garajes Volga y el territorio,
## Los Bloques, la playa y la plaza de la Estación (data/ciudad/plano.json, "amenazas");
## la avenida es su camino a la plaza, y pasa cerca del vestíbulo.
##
## Al llegar, la manada está donde la pone la hora: de noche en la guarida; de día,
## en algún punto de su ronda.

## La zona de la rejilla (metros del plano): La Plaza, la plaza de la Estación y el
## borde de Los Bloques, con la guarida.
const NAV_AREA: Rect2i = Rect2i(0, 0, 640, 560)
## La guarida (los garajes Volga).
const DEN: Vector2 = Vector2(96.0, 96.0)
## La ronda del día: de la guarida a la plaza de la Estación, por la avenida hasta
## el vestíbulo y de vuelta por Los Bloques.
const PATROL: Array[Vector2] = [
	Vector2(96.0, 96.0),
	Vector2(130.0, 120.0),
	Vector2(200.0, 135.0),
	Vector2(260.0, 150.0),
	Vector2(300.0, 175.0),
	Vector2(304.5, 231.5),
	Vector2(300.0, 285.0),
	Vector2(260.0, 320.0),
	Vector2(207.5, 297.5),
	Vector2(170.0, 250.0),
	Vector2(130.0, 190.0),
	Vector2(94.5, 126.5),
]
## Dónde se paran en la ronda (índice -> segundos).
const RESTS: Dictionary = {2: 60.0, 9: 40.0}
## La de caza (amanecer y atardecer): entra en La Plaza.
const HUNT: Array[Vector2] = [
	Vector2(96.0, 96.0),
	Vector2(200.0, 135.0),
	Vector2(300.0, 175.0),
	Vector2(340.0, 250.0),
	Vector2(380.0, 330.0),
	Vector2(420.0, 390.0),
	Vector2(470.0, 330.0),
	Vector2(430.0, 270.0),
	Vector2(340.0, 240.0),
	Vector2(260.0, 200.0),
	Vector2(150.0, 140.0),
]
## Al paso, los metros por segundo de la ronda.
const PATROL_SPEED: float = 1.1

var nav: CityNav
var pack: Pack
var dogs: Array[Dog] = []

var _plan: CityPlan
var _city: City
var _spawner: MultiplayerSpawner


func setup(plan: CityPlan, city: City) -> void:
	_plan = plan
	_city = city
	name = "Jauria"
	_spawner = MultiplayerSpawner.new()
	_spawner.name = "Generador"
	_spawner.spawn_function = _build_dog
	add_child(_spawner)
	_spawner.spawn_path = _spawner.get_path_to(self)
	pack = Pack.new()
	pack.name = "Manada"
	add_child(pack)


## En el anfitrión: la rejilla, las rutas y los seis perros donde los pone la hora.
func start() -> void:
	if not multiplayer.is_server():
		return
	if _plan != null and _plan.is_loaded():
		nav = CityNav.from_plan(_plan, NAV_AREA)
	pack.patrol = _route(PATROL)
	pack.hunt = _route(HUNT)
	pack.rests = RESTS
	pack.den = _world(DEN)
	var start_point: Vector3 = _starting_point()
	for index: int in Pack.COATS.size():
		var offset: Vector3 = Pack.ring_offset(index, 2.0 + index * 0.4)
		(
			_spawner
			. spawn(
				{
					"coat": Pack.COATS[index],
					"index": index,
					"size": Pack.SIZES[index],
					"where": start_point + offset + Vector3.UP * 0.6,
				}
			)
		)
	var members: Array[Dog] = []
	for child: Node in get_children():
		if child is Dog:
			(child as Dog).nav = nav
			members.append(child as Dog)
	dogs = members
	pack.set_dogs(members)
	pack.force_mode(Pack.Mode.DESCANSO if pack.is_night() else Pack.Mode.RONDA)


func _build_dog(values: Dictionary) -> Node:
	var dog: Dog = Dog.new()
	dog.setup(String(values["coat"]), int(values["index"]), float(values["size"]))
	dog.position = values["where"]
	return dog


## Dónde está la manada a esta hora: de noche en la guarida; de día, en su ronda.
func _starting_point() -> Vector3:
	if pack.is_night() or pack.patrol.is_empty():
		return pack.den
	var route: PackedVector3Array = pack.patrol
	var total: float = 0.0
	for index: int in route.size():
		total += route[index].distance_to(route[(index + 1) % route.size()])
	var seconds: float = GameState.minute / GameState.MINUTES_PER_SECOND
	var along: float = fmod(seconds * PATROL_SPEED, total)
	for index: int in route.size():
		var next: Vector3 = route[(index + 1) % route.size()]
		var length: float = route[index].distance_to(next)
		if along <= length:
			return route[index].lerp(next, along / maxf(length, 0.01))
		along -= length
	return route[0]


func _route(points: Array[Vector2]) -> PackedVector3Array:
	var route: PackedVector3Array = PackedVector3Array()
	for point: Vector2 in points:
		route.append(_world(nav.nearest_walkable(point) if nav != null else point))
	return route


func _world(point: Vector2) -> Vector3:
	var height: float = _city.surface_height(point) if _city != null else 0.0
	return CityPlan.to_world(point, height)
