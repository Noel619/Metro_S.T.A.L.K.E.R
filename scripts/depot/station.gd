class_name Station
extends Node3D
## El trozo de estación que se recorre (F2-12, docs/DEPOSITO.md 4.8): el pasillo
## frente a la consigna, el puesto de comida, la ventanilla de la administración
## con su buzón, el tablón de avisos, el contenedor y la boca de las escaleras
## mecánicas, con la reja cerrada. Lo de detrás de la arquería se ve, pero no se
## pisa.
##
## Coordenadas de Godot: el pasillo va de z = 3,55 (la fachada de la consigna) a
## z = 9,55 (la arquería) y de x = -15 a x = 15. Lo que tiene estado (el buzón, el
## contenedor, la vendedora) lo montan los sistemas; aquí solo se dice dónde está.

const MODELS_DIR: String = "res://assets/models/"
## La fachada de la consigna y la arquería de enfrente.
const FRONT: float = DepotRoom.FRONT_OUTER
const ARCADE: float = FRONT + 6.0
const HALF_L: float = 15.0
## El puesto de comida, pegado a la consigna (su espalda en la fachada).
const STALL_CENTER: Vector3 = Vector3(6.7, 0.0, FRONT)
## Su mostrador (donde se deja el dinero y aparece el cuenco) y la vendedora.
const STALL_COUNTER: Vector3 = Vector3(6.7, 1.05, FRONT + 1.45)
const STALL_VENDOR: Vector3 = Vector3(6.4, 0.0, FRONT + 0.75)
## La ventanilla de la administración y su buzón (la ranura).
const ADMIN_CENTER: Vector3 = Vector3(-9.0, 0.0, FRONT)
const MAILBOX: Vector3 = Vector3(-7.85, 1.25, FRONT + 0.12)
## La mañana: donde aparecen las notas, al pie de la persiana (por dentro).
const NOTICE_BOARD: Vector3 = Vector3(0.0, 0.0, ARCADE)
const DUMPSTER: Vector3 = Vector3(-6.3, 0.0, FRONT + 0.45)
## La boca de las escaleras, con la reja.
const ESCALATOR: Vector3 = Vector3(HALF_L, 0.0, FRONT)
## Por donde entran y salen los clientes: el paso de la barricada, a la izquierda
## (se les ve aparecer por encima de las cajas) y el hueco del fondo de la derecha.
const ENTRY_LEFT: Vector3 = Vector3(-14.2, 0.0, FRONT + 3.0)
const ENTRY_RIGHT: Vector3 = Vector3(14.2, 0.0, FRONT + 3.0)
## Donde espera quien viene a la ventanilla de la consigna (de cara al mostrador).
const WINDOW_SPOT: Vector3 = Vector3(0.0, 0.0, FRONT + 0.75)
const WALL_LAMPS: Array[Vector3] = [
	Vector3(-12.0, 2.7, FRONT),
	Vector3(-5.6, 2.7, FRONT),
	Vector3(9.2, 2.7, FRONT),
	Vector3(13.0, 2.7, FRONT),
	Vector3(-13.6, 2.7, ARCADE),
	Vector3(-8.5, 2.7, ARCADE),
	Vector3(-3.4, 2.7, ARCADE),
	Vector3(3.4, 2.7, ARCADE),
	Vector3(8.5, 2.7, ARCADE),
	Vector3(13.6, 2.7, ARCADE),
]
const HANGING_LAMPS: Array[float] = [-10.0, -2.5, 2.5, 10.0]
const WARM: Color = Color(1.0, 0.8, 0.56)
const CHALK: Color = Color("#e8e4da")

var _static: Node3D


func _ready() -> void:
	_static = Node3D.new()
	_static.name = "Fijo"
	add_child(_static)
	place("estacion_pasillo", Vector3(0.0, 0.0, FRONT))
	place("estacion_fondo", Vector3(0.0, 0.0, FRONT))
	place("escalera_mecanica", ESCALATOR)
	place("puesto_comida", STALL_CENTER).name = "Puesto"
	place("ventanilla_admin", ADMIN_CENTER).name = "Ventanilla"
	place("tablon_avisos", NOTICE_BOARD, 180.0)
	place("contenedor_estacion", DUMPSTER).name = "Contenedor"
	for x: float in [-3.0, 3.0]:
		place("banco_estacion", Vector3(x, 0.0, ARCADE - 0.35), 180.0)
	_lights()
	_chalkboard()
	_signs()


## Pone un modelo fijo. [param yaw] en grados.
func place(model: String, where: Vector3, yaw: float = 0.0) -> Node3D:
	var node: Node3D = (load(MODELS_DIR + model + ".glb") as PackedScene).instantiate()
	node.position = where
	node.rotation_degrees.y = yaw
	_static.add_child(node)
	return node


func _lights() -> void:
	for index: int in WALL_LAMPS.size():
		var at: Vector3 = WALL_LAMPS[index]
		var facing_back: bool = at.z > FRONT + 1.0
		place("farol_estacion", at, 180.0 if facing_back else 0.0)
		var out: float = -0.3 if facing_back else 0.3
		var light: OmniLight3D = _light(
			"Farol_%d" % index, at + Vector3(0.0, -0.13, out), 0.9, 5.5, false
		)
		light.light_color = WARM
	for index: int in HANGING_LAMPS.size():
		var x: float = HANGING_LAMPS[index]
		var lamp: Node3D = place("lampara_colgante", Vector3(x, 4.65, FRONT + 3.0))
		lamp.scale = Vector3.ONE * 1.3
		var light: OmniLight3D = _light(
			"Colgante_%d" % index, Vector3(x, 3.45, FRONT + 3.0), 2.2, 9.0, true
		)
		light.light_color = Color(1.0, 0.86, 0.66)
	# El puesto de comida, con su bombilla; la ventanilla, con luz detrás de la
	# cortinilla; y lo de detrás de los arcos: la hoguera y alguna luz lejana.
	var stall: OmniLight3D = _light(
		"Puesto", STALL_CENTER + Vector3(0.0, 2.15, 0.9), 1.6, 5.0, true
	)
	stall.light_color = Color(1.0, 0.74, 0.46)
	var admin: OmniLight3D = _light("Administracion", ADMIN_CENTER + Vector3(0, 1.5, 0.7), 0.5, 2.5)
	admin.light_color = Color(1.0, 0.85, 0.6)
	var fire: OmniLight3D = _light("Hoguera", Vector3(-2.6, 1.3, ARCADE + 4.1), 3.0, 9.0)
	fire.light_color = Color(1.0, 0.55, 0.3)
	for x: float in [-11.5, -6.0, 6.0, 11.5]:
		var far: OmniLight3D = _light("Lejos_%d" % int(x), Vector3(x, 3.2, ARCADE + 3.0), 1.8, 10.0)
		far.light_color = Color(0.95, 0.8, 0.62)
	var stairs: OmniLight3D = _light("Escaleras", ESCALATOR + Vector3(4.0, 3.5, -3.0), 0.35, 6.0)
	stairs.light_color = Color(0.7, 0.75, 0.9)


func _light(
	light_name: String, where: Vector3, energy: float, reach: float, shadows: bool = false
) -> OmniLight3D:
	var light: OmniLight3D = OmniLight3D.new()
	light.name = light_name
	light.position = where
	light.light_energy = energy
	light.omni_range = reach
	light.omni_attenuation = 0.8
	light.shadow_enabled = shadows
	add_child(light)
	return light


## Los rótulos: el de la consigna, el de la administración, el del buzón y el
## del tablón.
func _signs() -> void:
	var cream: Color = Color("#e6dcc0")
	for entry: Array in [
		["CONSIGNA", 0.27, cream, Vector3(0.0, 2.98, FRONT + 0.06), 0.0],
		["ADMINISTRACIÓN", 0.16, cream, ADMIN_CENTER + Vector3(0.25, 2.32, 0.062), 0.0],
		["PAGOS", 0.06, Color("#7a2e28"), Vector3(MAILBOX.x, 1.17, FRONT + 0.232), 0.0],
		["AVISOS", 0.13, Color("#c8a860"), NOTICE_BOARD + Vector3(0.0, 2.35, -0.06), 180.0],
	]:
		var label: Label3D = SignText.make(entry[0], entry[1], entry[2])
		label.name = "Rotulo_" + String(entry[0]).to_lower()
		label.position = entry[3]
		label.rotation_degrees.y = entry[4]
		add_child(label)


## La pizarra del puesto, escrita con tiza.
func _chalkboard() -> void:
	var lines: Array[String] = ["Sopa ...... 10 ₽", "Pan ......... 4 ₽", "Té ........... 2 ₽"]
	for index: int in lines.size():
		var label: Label3D = Label3D.new()
		label.name = "Pizarra_%d" % index
		label.text = lines[index]
		label.font = UiFonts.get_font(&"manuscrita_negrita")
		label.font_size = 64
		label.pixel_size = 0.0017
		label.modulate = CHALK
		label.outline_size = 0
		label.shaded = true
		label.position = STALL_CENTER + Vector3(0.0, 2.12 - index * 0.15, 1.705)
		add_child(label)
