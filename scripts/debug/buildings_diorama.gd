@tool
extends Node3D
## Diorama de los edificios del kit de arquitectura (F3-16): cada tipo, con sus daños, en
## una calle nevada de Tumansk. Sirve para revisar las piezas montadas, los materiales y
## la luz a cualquier hora, sin abrir la maqueta entera.
##
## Los edificios salen de fichas como las del plano (BuildingKit), en coordenadas de plano
## (x al este, y al norte, en metros); el origen de la escena es el punto (0, 0).

const MODELS_DIR: String = "res://assets/models/"
const GROUND_MATERIAL: String = "res://assets/materials/nevado.tres"
## Dónde cae la bomba de este diorama: al noreste, como en Tumansk.
const BOMB: Vector2 = Vector2(900.0, 700.0)

## "bloques": una calle de Los Bloques hecha a mano, con cada tipo y cada daño. "plaza":
## las casas del plano que el kit sabe montar alrededor de [member center], tal como son.
@export_enum("bloques", "plaza") var escena: String = "bloques"
## Centro de la escena "plaza", en coordenadas de plano (la plaza del Trabajo).
@export var center: Vector2 = Vector2(430.0, 330.0)
## Radio de la escena "plaza", en metros.
@export var radius: float = 210.0
@export_enum("dia", "anochecer", "noche") var mood: String = "dia"
## Hora del día (0 a 24). Si es negativa, se usa [member mood].
@export_range(-1.0, 24.0) var hour: float = -1.0
@export_enum("despejado", "ventisca") var weather: String = "despejado"
## Enciende una linterna en cada cámara.
@export var flashlight: bool = false

var _built: Node3D


func _ready() -> void:
	_build()
	_apply_atmosphere()
	if not Engine.is_editor_hint():
		for camera: Node in get_tree().get_nodes_in_group(&"capture_camera"):
			var target: Node3D = camera.get_node_or_null("Mira")
			if target != null:
				(camera as Camera3D).look_at(target.global_position)
			if flashlight:
				Flashlight.attach(camera as Camera3D)


## Cambia la hora del día (la usa el panel de depuración).
func set_hour(value: float) -> void:
	hour = value
	_apply_atmosphere()


func _apply_atmosphere() -> void:
	if hour >= 0.0:
		Atmosphere.apply_hour($Entorno.environment, $Sol, hour, weather)
	else:
		Atmosphere.apply($Entorno.environment, $Sol, mood, weather)


## Las fichas de los edificios del diorama.
func specs() -> Array[Dictionary]:
	if escena == "plaza":
		return _plan_specs()
	return [
		{
			"tipo": "jrushchovka",
			"clave": "DIO-J1",
			"huella": _rect(0.0, 0.0, 64.0, 12.0),
			"pisos": 5,
			"dano": 1,
			"incendio": "parcial",
			"entrada": 0,
		},
		{
			"tipo": "bloque9",
			"clave": "DIO-B1",
			"huella": _rect(84.0, -6.0, 132.0, 7.0),
			"pisos": 9,
			"dano": 1,
			"incendio": "no",
			"entrada": 0,
		},
		# Segunda fila: los daños. La bomba está al noreste: lo que la mira cae antes.
		{
			"tipo": "jrushchovka",
			"clave": "DIO-J2",
			"huella": _rect(0.0, 44.0, 64.0, 56.0),
			"pisos": 5,
			"dano": 2,
			"incendio": "total",
			"entrada": 0,
		},
		{
			"tipo": "bloque9",
			"clave": "DIO-B3",
			"huella": _rect(84.0, 42.0, 148.0, 55.0),
			"pisos": 9,
			"dano": 3,
			"incendio": "parcial",
			"entrada": 0,
		},
		{
			"tipo": "jrushchovka",
			"clave": "DIO-J4",
			"huella": _rect(-84.0, 44.0, -36.0, 56.0),
			"pisos": 5,
			"dano": 4,
			"incendio": "total",
			"entrada": 0,
		},
		# Las casas de muros de carga, enteras: la de los mercaderes y la obrera.
		{
			"tipo": "prerrevolucion",
			"clave": "DIO-P1",
			"huella": _rect(-40.0, -2.0, -6.0, 10.0),
			"pisos": 2,
			"dano": 1,
			"incendio": "no",
			"patios": PackedVector2Array([Vector2(-23.0, 40.0)]),
		},
		{
			"tipo": "estalinka_baja",
			"clave": "DIO-O1",
			"huella": _rect(-84.0, -2.0, -50.0, 10.0),
			"pisos": 3,
			"dano": 1,
			"incendio": "no",
			"patios": PackedVector2Array([Vector2(-67.0, 40.0)]),
		},
		{
			"tipo": "torre16",
			"clave": "DIO-T1",
			"huella": _rect(156.0, -10.0, 182.0, 12.0),
			"pisos": 16,
			"dano": 1,
			"incendio": "parcial",
			"entrada": 0,
		},
	]


## Las casas del plano alrededor de [member center], con lo que el plano sabe de ellas: la
## huella, las plantas, el daño, el incendio, sus patios y si tienen un arco.
func _plan_specs() -> Array[Dictionary]:
	var plan: CityPlan = CityPlan.load_default()
	var courtyards: PackedVector2Array = PackedVector2Array()
	for courtyard: Dictionary in plan.data["patios"]:
		var middle: Vector2 = CityGeometry.centroid(CityPlan.ring(courtyard["forma"][0]))
		if middle.distance_to(center) < radius + 60.0:
			courtyards.append(middle)
	var result: Array[Dictionary] = []
	for building: Dictionary in plan.data["edificios"]:
		var at: Vector2 = Vector2(building["centro"][0], building["centro"][1])
		if not BuildingKit.supports(building["tipo"]) or at.distance_to(center) > radius:
			continue
		(
			result
			. append(
				{
					"tipo": building["tipo"],
					"clave": building["id"],
					"huella": CityPlan.ring(building["huella"][0]),
					"pisos": int(building["pisos"]),
					"dano": int(building["dano"]),
					"incendio": building["incendio"],
					"cota": float(building["cota"]),
					"patios": courtyards,
					"arco": String(building.get("notas", "")).contains("Arco"),
					"bomba": plan.ground_zero(),
				}
			)
		)
	return result


func _build() -> void:
	if _built != null:
		_built.free()
	_built = Node3D.new()
	_built.name = "Edificios"
	add_child(_built)
	var kit: BuildingKit = BuildingKit.new()
	var origin: Vector2 = center if escena == "plaza" else Vector2.ZERO
	for spec: Dictionary in specs():
		spec["origen"] = origin
		if not spec.has("bomba"):
			spec["bomba"] = BOMB
		var building: Node3D = kit.build(spec)
		building.position.y = float(spec.get("cota", 0.0))
		_built.add_child(building)
	_ground()


func _ground() -> void:
	var heights: Array[float] = []
	for building: Node in _built.get_children():
		heights.append((building as Node3D).position.y)
	heights.sort()
	var level: float = heights[int(heights.size() / 2.0)] if not heights.is_empty() else 0.0
	var plane: PlaneMesh = PlaneMesh.new()
	plane.size = Vector2(600.0, 600.0)
	plane.subdivide_width = 60
	plane.subdivide_depth = 60
	var material: ShaderMaterial = (load(GROUND_MATERIAL) as ShaderMaterial).duplicate()
	material.set_shader_parameter("albedo_color", Color("#6f6a62"))
	var ground: MeshInstance3D = MeshInstance3D.new()
	ground.name = "Suelo"
	ground.mesh = plane
	ground.material_override = material
	ground.position = Vector3(60.0 if escena == "bloques" else 0.0, level, -20.0)
	_built.add_child(ground)


static func _rect(x0: float, y0: float, x1: float, y1: float) -> PackedVector2Array:
	return PackedVector2Array([Vector2(x0, y0), Vector2(x1, y0), Vector2(x1, y1), Vector2(x0, y1)])
