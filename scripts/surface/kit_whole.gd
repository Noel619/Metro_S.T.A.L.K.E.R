class_name KitWhole
extends KitRules
## Las casas que el kit tiene enteras: la isba y el barracón (kit_madera). Sus medidas son
## fijas en el plano, así que no se montan por vanos: se escoge la casa que toca por su
## daño y su incendio (en Tumansk ardieron casi todas) y se coloca sobre la huella, a lo
## largo de su lado más largo, estirada lo poco que haga falta para que encaje.
##
## Los estados siguen a la maqueta: con incendio total o daño 4 quedan los restos (la
## estufa y la chimenea entre los troncos carbonizados); con daño 3, el cascarón; con un
## incendio parcial o daño 2, chamuscada; si no, abandonada.

const MODELS: Dictionary = {
	"casa_madera":
	{
		"largo": 9.0,
		"fondo": 8.0,
		"alero": 3.4,
		"intacta": ["isba_a", "isba_b"],
		"chamuscada": ["isba_chamuscada"],
		"cascaron": ["isba_cascaron"],
		"quemada": ["isba_quemada_a", "isba_quemada_b"],
	},
	"barracon":
	{
		"largo": 30.0,
		"fondo": 11.0,
		"alero": 6.5,
		"intacta": ["barracon"],
		"chamuscada": ["barracon"],
		"cascaron": ["barracon_quemado"],
		"quemada": ["barracon_quemado"],
	},
}
## Hasta dónde llega lo que queda en pie, según el estado (para la colisión).
const STANDING: Dictionary = {"intacta": 1.0, "chamuscada": 1.0, "cascaron": 0.6, "quemada": 0.25}


func build(parent: Node3D) -> void:
	var model: Dictionary = MODELS[kind]
	var state: String = state_of(spec)
	var outline: PackedVector2Array = CityGeometry.clean(spec["huella"])
	var axis: Vector2 = CityGeometry.long_axis(outline)
	var across: Vector2 = Vector2(-axis.y, axis.x)
	var along: Vector2 = CityGeometry.extent(outline, axis)
	var side: Vector2 = CityGeometry.extent(outline, across)
	var center: Vector2 = axis * (along.x + along.y) * 0.5 + across * (side.x + side.y) * 0.5
	_origin = spec.get("origen", center)
	# La fachada principal mira a un extremo o al otro: cada casa, la suya.
	if _rng.randf() < 0.5:
		axis = -axis
	var x_axis: Vector3 = Vector3(axis.x, 0.0, -axis.y)
	var length: float = along.y - along.x
	var depth: float = side.y - side.x
	var basis: Basis = Basis(
		x_axis * (length / float(model["largo"])),
		Vector3.UP,
		x_axis.cross(Vector3.UP) * (depth / float(model["fondo"]))
	)
	var options: Array = model[state]
	assembly.put(options[_rng.randi() % options.size()], Transform3D(basis, _local(center, 0.0)))
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "Colision"
	parent.add_child(body)
	var height: float = float(model["alero"]) * float(STANDING[state])
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = Vector3(length, height, depth)
	var holder: CollisionShape3D = CollisionShape3D.new()
	holder.shape = shape
	holder.transform = Transform3D(
		Basis(x_axis, Vector3.UP, x_axis.cross(Vector3.UP)), _local(center, height * 0.5)
	)
	body.add_child(holder)


## El estado de una casa de madera según su ficha: "intacta", "chamuscada", "cascaron" o
## "quemada".
static func state_of(building: Dictionary) -> String:
	var fire: String = building.get("incendio", "no")
	var damage: int = int(building.get("dano", 1))
	if fire == "total" or damage >= 4:
		return "quemada"
	if damage == 3:
		return "cascaron"
	if fire == "parcial" or damage == 2:
		return "chamuscada"
	return "intacta"
