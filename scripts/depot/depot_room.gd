class_name DepotRoom
extends Node3D
## El local: la antigua consigna de la estación (docs/DEPOSITO.md), con lo que
## está fijo (la sala, el mostrador, las baldas, los muebles, las cosas del
## antiguo dueño) y las luces.
##
## Las cosas con estado propio (la persiana, la puerta, la lámpara, la estufa,
## las manchas…) son [Fixture] y las monta cada sistema; aquí solo se dice dónde
## van. Todo se construye igual en todos los equipos: los nombres de los nodos
## son fijos.
##
## Coordenadas de Godot: x de -4,5 a 4,5 y z de 3,25 (el muro del pasillo, por
## dentro) a -3,75 (el fondo). El pasillo de la estación queda en z > 3,55.

const MODELS_DIR: String = "res://assets/models/"
const FLOOR: float = 0.025
## La cara de fuera del muro del pasillo: ahí empieza el pasillo.
const FRONT_OUTER: float = 3.55
const FRONT_INNER: float = 3.25
const BACK: float = -3.75
const HALF_W: float = 4.5
## El tablero del mostrador y sus límites (en la ventanilla).
const COUNTER_TOP: float = 0.95
const COUNTER_INNER: float = 2.75
## Donde se hace el trato: el centro del mostrador, en la ventanilla.
const DEAL_SPOT: Vector3 = Vector3(-0.05, COUNTER_TOP, 3.15)
## Lo que hay encima del mostrador.
const CASH_BOX: Vector3 = Vector3(-1.12, COUNTER_TOP, 2.98)
const LEDGER: Vector3 = Vector3(-0.66, COUNTER_TOP, 2.98)
const SCALE: Vector3 = Vector3(1.0, COUNTER_TOP, 2.99)
## El banco de trabajo, contra el muro derecho, y su tablero.
const BENCH_CENTER: Vector3 = Vector3(4.0, FLOOR, -0.4)
const BENCH_TOP: float = 0.93
## El tapete del banco: donde se deja lo que se repara.
const BENCH_MAT: Vector3 = Vector3(3.95, BENCH_TOP, -0.2)
const TAG_BOX: Vector3 = Vector3(3.92, BENCH_TOP, 0.22)
## Las baldas de la consigna: sus pisos.
const RACK_LEVELS: Array[float] = [0.1, 0.62, 1.14, 1.66]
const RACKS: Array[Vector3] = [
	Vector3(-4.2, FLOOR, 1.55), Vector3(-4.2, FLOOR, -0.55), Vector3(-1.9, FLOOR, 0.35)
]
## Medio largo y medio fondo de una balda (a lo largo del muro y hacia la sala).
const RACK_HALF: Vector2 = Vector2(1.0, 0.275)
## La pila de descontaminación, junto a la puerta.
const SINK_CENTER: Vector3 = Vector3(4.18, FLOOR, 1.75)
## El fondo de la cubeta (por dentro) y su tamaño.
const SINK_FLOOR: float = 0.64
const STOVE_CENTER: Vector3 = Vector3(-1.35, FLOOR, -3.3)
const COT_CENTER: Vector3 = Vector3(-3.45, FLOOR, -3.25)
const PLANNING_CENTER: Vector3 = Vector3(2.6, FLOOR, -3.2)
const BIN_CENTER: Vector3 = Vector3(2.15, FLOOR, 2.95)
const CLOCK: Vector3 = Vector3(2.5, 2.3, FRONT_INNER)
const JOB_BOARD: Vector3 = Vector3(-3.0, 1.05, FRONT_INNER)
const DOOR_HINGE: Vector3 = Vector3(4.3, 0.0, FRONT_INNER + 0.15)
## Dónde cuelgan las lámparas: la del mostrador (la de la bombilla fundida), la
## del banco, la del almacén y la del rincón de dormir.
const LAMP_COUNTER: Vector3 = Vector3(0.0, 3.4, 2.15)
const LAMP_BENCH: Vector3 = Vector3(3.2, 3.02, -0.4)
const LAMP_STORE: Vector3 = Vector3(-2.7, 3.22, 0.6)
const LAMP_BACK: Vector3 = Vector3(-2.6, 3.22, -2.7)
## Lo que baja la luz de la lámpara desde la bóveda: justo por debajo del borde
## de la pantalla (si estuviera dentro, la pantalla la taparía casi entera).
const BULB_DROP: float = 0.88
## Las categorías de cada balda, de abajo arriba (los carteles que pones tú).
const RACK_SIGNS: Array = [
	[
		ItemData.Category.ENVASES,
		ItemData.Category.ROPA,
		ItemData.Category.MEDICINAS,
		ItemData.Category.COMIDA
	],
	[
		ItemData.Category.CHATARRA,
		ItemData.Category.HERRAMIENTAS,
		ItemData.Category.HERRAMIENTAS,
		ItemData.Category.ELECTRONICA
	],
	[
		ItemData.Category.CHATARRA,
		ItemData.Category.ENVASES,
		ItemData.Category.ELECTRONICA,
		ItemData.Category.COMIDA
	],
]
const CATEGORY_NAMES: Dictionary = {
	ItemData.Category.COMIDA: "Comida",
	ItemData.Category.MEDICINAS: "Medicinas",
	ItemData.Category.HERRAMIENTAS: "Herramientas",
	ItemData.Category.ELECTRONICA: "Electrónica",
	ItemData.Category.ROPA: "Ropa",
	ItemData.Category.CHATARRA: "Chatarra",
	ItemData.Category.ENVASES: "Envases",
}

var _static: Node3D


func _ready() -> void:
	_static = Node3D.new()
	_static.name = "Fijo"
	add_child(_static)
	place("consigna_sala", Vector3.ZERO)
	place("consigna_mostrador", Vector3(0.0, 0.0, FRONT_OUTER))
	for index: int in RACKS.size():
		var rack: Node3D = place("consigna_baldas", RACKS[index], 90.0)
		rack.name = "Baldas_%d" % index
	place("banco_trabajo", BENCH_CENTER, -90.0)
	place("pila_descontaminacion", SINK_CENTER, -90.0).name = "Pila"
	place("estanteria_metalica", Vector3(4.25, FLOOR, -2.35), -90.0)
	place("catre", COT_CENTER).name = "Catre"
	_furniture()
	_lights()
	place("consigna_persiana", Vector3(0.0, 0.0, FRONT_OUTER)).name = "Persiana"
	place("consigna_puerta", DOOR_HINGE).name = "Puerta"
	_rack_signs()


## Lo del oficio y lo que dejó el antiguo dueño.
func _furniture() -> void:
	place("bascula", SCALE, 180.0).name = "Bascula"
	place("caja_rublos", CASH_BOX, 180.0 + 8.0).name = "CajaRublos"
	place("libro_cuentas", LEDGER, 180.0 - 6.0).name = "Libro"
	place("caja_etiquetas", TAG_BOX, -90.0).name = "CajaEtiquetas"
	place("corcho_encargos", JOB_BOARD, 180.0).name = "Corcho"
	var jobs_sign: Label3D = SignText.make("ENCARGOS", 0.055, Color("#2e3a33"))
	jobs_sign.name = "Rotulo_encargos"
	jobs_sign.position = JOB_BOARD + Vector3(0.0, 0.84, -0.035)
	jobs_sign.rotation_degrees.y = 180.0
	_static.add_child(jobs_sign)
	place("reloj_pared", CLOCK, 180.0).name = "Reloj"
	place("cubo_basura", BIN_CENTER).name = "Cubo"
	place("rollo_bolsas", Vector3(HALF_W, 1.25, 1.15), -90.0).name = "RolloBolsas"
	place("tablero_herramientas", Vector3(HALF_W, 1.05, BENCH_CENTER.z), -90.0)
	place("flexo", Vector3(4.28, BENCH_TOP, -1.02), 180.0).name = "Flexo"
	place("mesa_planificacion", PLANNING_CENTER)
	place("tablero_pared", Vector3(PLANNING_CENTER.x, 1.05, BACK))
	place("estufa", STOVE_CENTER).name = "Estufa"
	place("alfombra", Vector3(-2.65, FLOOR + 0.002, -2.45))
	place("perchero", Vector3(0.75, FLOOR, -2.1), 35.0)
	# Lo del antiguo dueño.
	place("silla_vieja", Vector3(-1.75, FLOOR, 2.3), 25.0)
	place("calendario", Vector3(-HALF_W, 1.62, 2.92), 90.0)
	place("lista_deudas", Vector3(1.92, 1.46, FRONT_INNER), 180.0)
	place("planta_muerta", Vector3(-2.25, FLOOR, 2.98), 40.0)
	place("maletas", Vector3(-3.85, FLOOR, 2.82), 12.0)
	# La gotera de la tubería oxidada del muro derecho, al fondo.
	var drip: Drip = Drip.new()
	drip.name = "Gotera"
	drip.position = Vector3(4.18, FLOOR, -3.3)
	drip.height = 2.35
	_static.add_child(drip)
	# Las rayas con las que el antiguo dueño contaba los días, junto al catre.
	var tally: Label3D = Label3D.new()
	tally.name = "Rayas"
	tally.text = "IIII IIII IIII IIII IIII IIII\nIIII IIII IIII IIII IIII II"
	tally.font = UiFonts.get_font(&"manuscrita")
	tally.font_size = 64
	tally.pixel_size = 0.0011
	tally.modulate = Color(0.24, 0.23, 0.25, 0.85)
	tally.outline_size = 0
	tally.shaded = true
	tally.double_sided = false
	tally.position = Vector3(-3.05, 0.72, BACK + 0.016)
	tally.rotation_degrees.z = 2.5
	_static.add_child(tally)


func _lights() -> void:
	for lamp: Array in [
		["Mostrador", LAMP_COUNTER, 2.1],
		["Banco", LAMP_BENCH, 1.8],
		["Almacen", LAMP_STORE, 1.6],
		["Fondo", LAMP_BACK, 1.5],
	]:
		place("lampara_colgante", lamp[1]).name = "Lampara_" + lamp[0]
		var light: OmniLight3D = add_light(
			"Luz_" + lamp[0], lamp[1] + Vector3(0.0, -BULB_DROP, 0.0), lamp[2]
		)
		# Lo que rebota en el suelo y en los muros: un relleno suave, sin sombras.
		var bounce: OmniLight3D = OmniLight3D.new()
		bounce.name = "Rebote"
		bounce.light_color = light.light_color
		bounce.light_energy = lamp[2] * 0.22
		bounce.omni_range = 9.0
		bounce.omni_attenuation = 0.4
		bounce.light_specular = 0.0
		bounce.position = Vector3(0.0, -0.9, 0.0)
		light.add_child(bounce)
	var desk: OmniLight3D = add_light("Luz_Flexo", Vector3(3.9, BENCH_TOP + 0.36, -1.02), 0.7)
	desk.omni_range = 2.2
	desk.shadow_enabled = false


## Los carteles de las categorías, escritos por ti en papel nuevo y pegados al
## canto de cada balda.
func _rack_signs() -> void:
	for rack_index: int in RACKS.size():
		var rack: Vector3 = RACKS[rack_index]
		var signs: Array = RACK_SIGNS[rack_index]
		for level: int in RACK_LEVELS.size():
			var name_text: String = CATEGORY_NAMES[signs[level]]
			var paper: Dictionary = {
				"svg": "etiqueta_precio",
				"ancho_m": 0.16,
				"rotulos":
				[
					{
						"text": name_text,
						"x": 64,
						"y": 30,
						"size": 52,
						"font": "manuscrita_negrita",
						"color": "#2b2622",
						"rot": -3,
					}
				],
			}
			var card: PaperCard = PaperCard.create(paper)
			card.name = "Cartel_%d_%d" % [rack_index, level]
			# El canto de la balda que da a la sala (las baldas miran a +X).
			card.position = Vector3(
				rack.x + RACK_HALF.y + 0.012, rack.y + RACK_LEVELS[level] - 0.035, rack.z - 0.55
			)
			card.rotation_degrees = Vector3(0.0, 90.0, 0.0)
			_static.add_child(card)


## La categoría de la balda en [param where], si es una balda (-1 si no).
static func rack_category(where: Vector3) -> int:
	for rack_index: int in RACKS.size():
		var rack: Vector3 = RACKS[rack_index]
		if absf(where.x - rack.x) > RACK_HALF.y + 0.05:
			continue
		if absf(where.z - rack.z) > RACK_HALF.x + 0.05:
			continue
		var height: float = where.y - rack.y
		var level: int = -1
		for index: int in RACK_LEVELS.size():
			if height >= RACK_LEVELS[index] - 0.05:
				level = index
		if level >= 0:
			return RACK_SIGNS[rack_index][level]
	return -1


## Una luz cálida de bombilla, con sombras.
func add_light(light_name: String, where: Vector3, energy: float) -> OmniLight3D:
	var light: OmniLight3D = OmniLight3D.new()
	light.name = light_name
	light.position = where
	light.light_color = Color(1.0, 0.8, 0.56)
	light.light_energy = energy
	light.shadow_enabled = true
	light.omni_range = 7.5
	# Que llegue a los muros: la sala es grande para una bombilla.
	light.omni_attenuation = 0.6
	add_child(light)
	return light


## Pone un modelo fijo. [param yaw] en grados.
func place(model: String, where: Vector3, yaw: float = 0.0) -> Node3D:
	var node: Node3D = (load(MODELS_DIR + model + ".glb") as PackedScene).instantiate()
	node.position = where
	node.rotation_degrees.y = yaw
	_static.add_child(node)
	return node


## Un modelo fijo ya colocado, por su nombre (la persiana, la pila, el reloj…).
func fixed(node_name: String) -> Node3D:
	return _static.get_node_or_null(node_name) as Node3D


## La altura de la bóveda (por dentro) en [param x].
static func vault_height(x: float) -> float:
	var spring: float = 2.7
	var crown: float = 3.4
	var radius: float = (
		((2.0 * HALF_W) ** 2 / 4.0 + (crown - spring) ** 2) / (2.0 * (crown - spring))
	)
	var clamped: float = clampf(x, -HALF_W, HALF_W)
	return (
		spring + sqrt(radius * radius - clamped * clamped) - sqrt(radius * radius - HALF_W * HALF_W)
	)
