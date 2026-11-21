class_name KitMinor
extends KitRules
## Los edificios menores en los que se entra (F3-14): el quiosco de prensa, las tiendas de
## la evacuación, los trasteros, el palomar y el centro de transformación (kit_menores, de
## tools/blender/recipes/kit_menores.py). Cada uno es un modelo entero con su colisión
## ("<modelo>_colision", hecha a mano), que se coloca sobre la huella a lo largo de su lado
## más largo, estirado lo poco que haga falta; los trasteros son una hilera de casetas, con
## sus puertas hacia el patio.
##
## Lo que se mueve o se usa no va en el modelo. Sus puertas, sus escaleras y dónde puede
## haber botín quedan en los metadatos del edificio, en el marco de su nodo, para que la
## superficie ponga sus cosas fijas ([SurfaceSites]):
## - "kit_puertas": {"id", "bisagra" (Transform3D), "tamano", "pieza", "punto" (dónde
##   cuelga el candado, en el marco de la bisagra) y "cierres" (lo que la puede cerrar
##   y con qué probabilidad)}.
## - "kit_trepables": {"pie" (Transform3D: +z hacia quien trepa), "tamano"}.
## - "kit_botin": {"punto" (Vector3), "tipo" (el modelo)}.
## - "kit_interiores" y "kit_pasos": lo que pisan los perros (en el plano). El interior de
##   cada modelo y el paso de cada hueco: "llegada" (lo de delante y detrás del hueco, que
##   siempre se pisa) y "hueco" (la casilla del muro, que se cierra con su puerta: "puerta"
##   es su id, vacío si el hueco ya no tiene puerta).
##
## Los marcos de abajo son los del modelo en Godot: x a lo largo, y arriba, z hacia su
## fachada principal (la -y de Blender).

## Lo que mide cada modelo en el kit (x, z) y si va en hilera.
const SIZES: Dictionary = {
	"quiosco": Vector2(4.0, 3.0),
	"tienda": Vector2(9.0, 7.0),
	"trastero": Vector2(3.0, 6.0),
	"palomar": Vector2(5.0, 5.0),
	"transformador": Vector2(8.0, 6.0),
}
const ROWS: PackedStringArray = ["trastero"]
## Las colisiones que comparten los modelos que solo cambian de piel.
const COLLISION_OF: Dictionary = {"tienda_cruz": "tienda_colision"}
## Las puertas de cada modelo (las de los estados que la conservan).
const DOORS: Dictionary = {
	"quiosco":
	[
		{
			"pieza": "quiosco_puerta",
			"bisagra": Vector3(1.29, 0.0, -1.5),
			"rumbo": 180.0,
			"tamano": Vector3(0.78, 1.98, 0.04),
			"punto": Vector3(0.68, 1.04, 0.06),
			"cierres": {"cerradura": 0.45, "candado": 0.3, "atrancada": 0.15, "": 0.1},
		}
	],
	"trastero":
	[
		{
			"pieza": "trastero_puerta",
			"bisagra": Vector3(-0.415, 0.15, 3.0),
			"rumbo": 0.0,
			"tamano": Vector3(0.83, 1.87, 0.03),
			"punto": Vector3(0.76, 1.1, 0.05),
			"cierres": {"candado": 0.55, "cadena": 0.1, "atrancada": 0.2, "": 0.15},
		}
	],
	"palomar":
	[
		{
			"pieza": "palomar_puerta",
			"bisagra": Vector3(1.3, 3.1, 0.34),
			"rumbo": 90.0,
			"tamano": Vector3(0.68, 1.62, 0.03),
			"punto": Vector3(0.62, 0.9, 0.04),
			"cierres": {"candado": 1.0},
		}
	],
	"transformador":
	[
		{
			"pieza": "transformador_puerta",
			"bisagra": Vector3(-0.59, 0.0, 2.98),
			"rumbo": 0.0,
			"tamano": Vector3(1.18, 2.18, 0.05),
			"punto": Vector3(1.05, 1.15, 0.06),
			"cierres": {"cadena": 0.8, "candado": 0.2},
		}
	],
}
## Las escaleras: el pie (en el borde de los peldaños) y hacia dónde mira quien sube.
const LADDERS: Dictionary = {
	"palomar": [{"pie": Vector3(2.32, 0.0, 0.0), "rumbo": 90.0, "tamano": Vector3(0.5, 3.1, 0.8)}],
}
## Dónde puede haber botín (sobre el mostrador, en los estantes, en los catres…).
const LOOT: Dictionary = {
	"quiosco":
	[
		Vector3(-1.2, 0.97, 1.1),
		Vector3(0.0, 0.97, 1.1),
		Vector3(1.2, 0.97, 1.1),
		Vector3(-1.75, 1.45, -0.3),
		Vector3(1.75, 1.45, 0.2),
		Vector3(-1.75, 1.95, 0.5),
		Vector3(0.5, 0.06, -0.6),
	],
	"quiosco_roto": [Vector3(0.0, 0.06, 0.0), Vector3(-1.2, 0.06, -0.5), Vector3(1.0, 0.97, 1.1)],
	"tienda":
	[
		Vector3(-2.9, 0.62, 2.35),
		Vector3(-1.0, 0.62, 2.35),
		Vector3(0.9, 0.62, 2.35),
		Vector3(2.8, 0.62, 2.35),
		Vector3(-2.9, 0.62, -2.35),
		Vector3(-1.0, 0.62, -2.35),
		Vector3(0.9, 0.62, -2.35),
		Vector3(2.8, 0.62, -2.35),
		Vector3(-1.2, 0.78, 0.0),
	],
	"tienda_caida":
	[
		Vector3(-2.9, 0.62, 2.35),
		Vector3(-1.0, 0.62, 2.35),
		Vector3(-2.9, 0.62, -2.35),
		Vector3(-1.0, 0.62, -2.35),
		Vector3(-1.2, 0.78, 0.0),
	],
	"trastero": [Vector3(-0.8, 0.74, -2.75), Vector3(0.6, 1.29, -2.75), Vector3(0.6, 0.17, 0.5)],
	"trastero_hundido": [Vector3(0.3, 0.17, 1.0)],
	"palomar": [Vector3(-0.4, 3.22, 1.05), Vector3(0.5, 3.13, -0.6), Vector3(0.8, 3.13, -1.0)],
	"transformador": [Vector3(-0.5, 0.06, -1.5), Vector3(2.0, 0.06, 1.5), Vector3(-3.0, 0.06, 2.0)],
}
## Las de la tienda caída y la de la Cruz Roja usan los de la tienda.
const LOOT_OF: Dictionary = {"tienda_cruz": "tienda"}
## Lo que se pisa dentro de cada modelo (en su marco: x y z). Queda a un metro de los
## muros: la rejilla de los perros es de casillas de un metro y entre dentro y fuera tiene
## que quedar al menos una de muro (si no, pasarían a través de las tablas). Bajo el
## palomar no hay muros.
const INTERIORS: Dictionary = {
	"quiosco": Rect2(-1.0, -0.5, 2.0, 1.0),
	"quiosco_roto": Rect2(-1.0, -0.5, 2.0, 1.0),
	"tienda": Rect2(-3.5, -2.5, 7.0, 5.0),
	"tienda_cruz": Rect2(-3.5, -2.5, 7.0, 5.0),
	"tienda_caida": Rect2(-3.5, -2.5, 3.5, 5.0),
	"trastero": Rect2(-0.5, -2.0, 1.0, 4.0),
	"trastero_hundido": Rect2(-0.5, -2.0, 1.0, 4.0),
	"transformador": Rect2(-3.0, 0.3, 5.0, 1.7),
	"palomar": Rect2(-2.6, -2.6, 5.2, 5.2),
}
## Los huecos sin puerta de cada modelo: su centro y hacia fuera (la puerta de lona de la
## tienda, la del quiosco destrozado y la del trastero hundido, que ya no están).
const OPENINGS: Dictionary = {
	"quiosco_roto": [[Vector3(0.9, 0.0, -1.5), Vector3(0.0, 0.0, -1.0)]],
	"tienda": [[Vector3(-4.5, 0.0, 0.0), Vector3(-1.0, 0.0, 0.0)]],
	"tienda_cruz": [[Vector3(-4.5, 0.0, 0.0), Vector3(-1.0, 0.0, 0.0)]],
	"tienda_caida": [[Vector3(-4.5, 0.0, 0.0), Vector3(-1.0, 0.0, 0.0)]],
	"trastero_hundido": [[Vector3(0.0, 0.0, 3.0), Vector3(0.0, 0.0, 1.0)]],
}
## El paso de un hueco: lo de delante y detrás (hacia dentro, negativo) y el propio hueco.
const APPROACH: Array[float] = [-0.9, -0.5, 0.5, 0.9]
const GAP: Array[float] = [-0.12, 0.12]
const COLLISION_SUFFIX: String = "_colision"


## El modelo base que monta este edificio (de su ficha o del plano), o "" si no es de
## los que tiene el kit.
static func model_for(building: Dictionary) -> String:
	var name: String = String(building.get("nombre", ""))
	match String(building.get("tipo", "")):
		"quiosco":
			return "quiosco"
		"tienda_campana":
			return "tienda"
		"transformador":
			return "transformador" if name.begins_with("Centro de transformación") else ""
		"cobertizo":
			if name == "Palomar":
				return "palomar"
			if (
				name.contains("Trasteros")
				or name.contains("Cobertizos")
				or name.contains("Vestuarios")
			):
				return "trastero"
	return ""


func build(parent: Node3D) -> void:
	var base: String = model_for(spec)
	var outline: PackedVector2Array = CityGeometry.clean(spec["huella"])
	var axis: Vector2 = CityGeometry.long_axis(outline)
	var across: Vector2 = Vector2(-axis.y, axis.x)
	var along: Vector2 = CityGeometry.extent(outline, axis)
	var side: Vector2 = CityGeometry.extent(outline, across)
	var center: Vector2 = axis * (along.x + along.y) * 0.5 + across * (side.x + side.y) * 0.5
	_origin = spec.get("origen", center)
	axis = _facing(axis, center)
	var length: float = along.y - along.x
	var depth: float = side.y - side.x
	var size: Vector2 = SIZES[base]
	var units: int = maxi(1, roundi(length / size.x)) if ROWS.has(base) else 1
	var unit: float = length / units
	var x_axis: Vector3 = Vector3(axis.x, 0.0, -axis.y)
	var basis: Basis = Basis(
		x_axis * (unit / size.x), Vector3.UP, x_axis.cross(Vector3.UP) * (depth / size.y)
	)
	var faces: PackedVector3Array = PackedVector3Array()
	var doors: Array[Dictionary] = []
	var ladders: Array[Dictionary] = []
	var loot: Array[Dictionary] = []
	var interiors: Array[PackedVector2Array] = []
	var passages: Array[Dictionary] = []
	for index: int in units:
		var at: Vector2 = center + axis * (-length * 0.5 + (index + 0.5) * unit)
		var place: Transform3D = Transform3D(basis, _local(at, 0.0))
		var model: String = _variant(base)
		if not assembly.meshes.has(model):
			assembly.missing.append(model)
			continue
		assembly.put(model, place)
		faces.append_array(_collision(model, place))
		_add_doors(model, place, doors, passages)
		_add_ladders(model, place, ladders)
		var inside: Rect2 = INTERIORS.get(model, Rect2())
		if inside.has_area():
			interiors.append(_plan_rect(place, inside))
		for opening: Array in OPENINGS.get(model, []):
			passages.append(_passage(place, opening[0], opening[1], ""))
		for point: Vector3 in LOOT.get(LOOT_OF.get(model, model), []):
			loot.append({"punto": place * point, "tipo": base})
	parent.set_meta(&"kit_puertas", doors)
	parent.set_meta(&"kit_trepables", ladders)
	parent.set_meta(&"kit_botin", loot)
	parent.set_meta(&"kit_interiores", interiors)
	parent.set_meta(&"kit_pasos", passages)
	if faces.is_empty():
		return
	var shape: ConcavePolygonShape3D = ConcavePolygonShape3D.new()
	shape.backface_collision = true
	shape.set_faces(faces)
	var holder: CollisionShape3D = CollisionShape3D.new()
	holder.name = "Forma"
	holder.shape = shape
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Colision"
	parent.add_child(body)
	body.add_child(holder)


## El estado de cada pieza según el daño (y el nombre: la Cruz Roja).
func _variant(base: String) -> String:
	match base:
		"quiosco":
			return "quiosco_roto" if damage >= 2 else "quiosco"
		"tienda":
			if damage >= 3 or (damage == 2 and _rng.randf() < 0.35):
				return "tienda_caida"
			return (
				"tienda_cruz" if String(spec.get("nombre", "")).contains("Cruz Roja") else "tienda"
			)
		"trastero":
			var caved: float = [0.0, 0.08, 0.3, 0.6, 0.85][damage]
			return "trastero_hundido" if _rng.randf() < caved else "trastero"
	return base


## Hacia dónde va el eje del modelo: su fachada (la z del modelo, a la derecha del eje)
## mira al patio más cercano si lo hay a menos de 80 m; si no, a un lado u otro.
func _facing(axis: Vector2, center: Vector2) -> Vector2:
	var nearest: Vector2 = Vector2.INF
	for courtyard: Vector2 in spec.get("patios", PackedVector2Array()):
		if courtyard.distance_to(center) < nearest.distance_to(center):
			nearest = courtyard
	if nearest != Vector2.INF and nearest.distance_to(center) < 80.0:
		# La fachada (+z del modelo) va hacia axis × arriba en el plano: (axis.y, -axis.x).
		var front: Vector2 = Vector2(axis.y, -axis.x)
		return axis if front.dot(nearest - center) >= 0.0 else -axis
	return axis if _rng.randf() < 0.5 else -axis


func _collision(model: String, place: Transform3D) -> PackedVector3Array:
	var name: String = COLLISION_OF.get(model, model + COLLISION_SUFFIX)
	var result: PackedVector3Array = PackedVector3Array()
	if not assembly.meshes.has(name):
		assembly.missing.append(name)
		return result
	for vertex: Vector3 in (assembly.meshes[name] as Mesh).get_faces():
		result.append(place * vertex)
	return result


func _add_doors(
	model: String, place: Transform3D, doors: Array[Dictionary], passages: Array[Dictionary]
) -> void:
	var square: Basis = place.basis.orthonormalized()
	for door: Dictionary in DOORS.get(model, []):
		var turn: Basis = Basis(Vector3.UP, deg_to_rad(float(door["rumbo"])))
		var hinge: Transform3D = Transform3D(square * turn, place * (door["bisagra"] as Vector3))
		var middle: Vector3 = (
			(door["bisagra"] as Vector3)
			+ turn * Vector3((door["tamano"] as Vector3).x * 0.5, 0.0, 0.0)
		)
		var id: String = "%s_puerta_%d" % [key, doors.size()]
		passages.append(_passage(place, middle, turn * Vector3.BACK, id))
		(
			doors
			. append(
				{
					"id": "%s_puerta_%d" % [key, doors.size()],
					"bisagra": hinge,
					"tamano": door["tamano"],
					"pieza": door["pieza"],
					"punto": door["punto"],
					"cierres": door["cierres"],
				}
			)
		)


## Un rectángulo del marco del modelo (x, z) en el plano.
func _plan_rect(place: Transform3D, rect: Rect2) -> PackedVector2Array:
	var result: PackedVector2Array = PackedVector2Array()
	for corner: Vector2 in [
		rect.position,
		rect.position + Vector2(rect.size.x, 0.0),
		rect.end,
		rect.position + Vector2(0.0, rect.size.y)
	]:
		result.append(_plan_of(place * Vector3(corner.x, 0.0, corner.y)))
	return result


## Los puntos del plano del paso de un hueco (su centro y hacia fuera, en el marco del modelo).
func _passage(place: Transform3D, middle: Vector3, outward: Vector3, door: String) -> Dictionary:
	var approach: PackedVector2Array = PackedVector2Array()
	for step: float in APPROACH:
		approach.append(_plan_of(place * (middle + outward * step)))
	var gap: PackedVector2Array = PackedVector2Array()
	for step: float in GAP:
		gap.append(_plan_of(place * (middle + outward * step)))
	return {"llegada": approach, "hueco": gap, "puerta": door}


## Un punto del marco del nodo en el plano.
func _plan_of(local: Vector3) -> Vector2:
	return Vector2(_origin.x + local.x, _origin.y - local.z)


func _add_ladders(model: String, place: Transform3D, ladders: Array[Dictionary]) -> void:
	var square: Basis = place.basis.orthonormalized()
	for ladder: Dictionary in LADDERS.get(model, []):
		var foot: Transform3D = Transform3D(
			square * Basis(Vector3.UP, deg_to_rad(float(ladder["rumbo"]))),
			place * (ladder["pie"] as Vector3)
		)
		ladders.append({"pie": foot, "tamano": ladder["tamano"]})
