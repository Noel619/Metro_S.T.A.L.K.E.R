class_name ItemView
extends Node3D
## Cómo se ve el estado de un objeto (en todos los equipos): la etiqueta con su
## precio colgando, la bolsa de plástico si está embolsado, la cifra escrita en
## una etiqueta en blanco o en la faja de un fajo, las piezas de lo que se está
## reparando y la aguja y el piloto del dosímetro.
##
## Cuelga del nodo "Visual" del objeto: se mueve con lo que se dibuja.

const INK: Color = Color("#2b2622")
const PENCIL: Color = Color("#3b3a40")
## El dosímetro: lo que marca a fondo de escala, el giro de la aguja y lo que
## alcanza a medir.
const DOSIMETER_FULL: float = 2.0
const DOSIMETER_SWEEP: float = deg_to_rad(-90.0)
const DOSIMETER_RANGE: float = 3.5
const NEEDLE_SPRING: float = 60.0
const NEEDLE_DAMP: float = 7.0
## El color de los contactos limpios (los sucios están verdes de óxido).
const CLEAN_CONTACTS: Color = Color(1.6, 1.3, 0.75)

var item: Carryable
var items: WorldItems
var _tag: PaperCard
var _bag: MeshInstance3D
var _label: Label3D
var _needle: Node3D
var _lamp: MeshInstance3D
var _needle_angle: float = 0.0
var _needle_speed: float = 0.0
var _blink: float = 0.0
var _lamp_on: Material
var _lamp_off: Material
var _parts: Dictionary = {}


func _ready() -> void:
	# El objeto (su Carryable) se prepara después que su dibujo.
	if not item.is_node_ready():
		await item.ready
	var data: ItemData = item.state.data
	if data.tool == &"etiqueta" or data.tool == &"billetes":
		_label = Label3D.new()
		_label.name = "Cifra"
		_label.font = UiFonts.get_font(&"manuscrita_negrita")
		_label.font_size = 64
		_label.pixel_size = 0.00042 if data.tool == &"etiqueta" else 0.0003
		_label.modulate = PENCIL
		_label.outline_size = 0
		_label.shaded = true
		_label.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
		var top: float = item.bounds().end.y
		_label.position = Vector3(-0.008, top + 0.0012, 0.0)
		if data.tool == &"billetes":
			_label.rotation_degrees = Vector3(-90.0, 90.0, 0.0)
		add_child(_label)
	if data.id == &"dosimetro":
		_needle = item.visual().find_child("aguja", true, false) as Node3D
		_lamp = item.visual().find_child("piloto", true, false) as MeshInstance3D
		if _lamp != null:
			_lamp_off = _lamp.get_active_material(0)
			_lamp_on = load("res://assets/materials/bombilla.tres")
	var recipe: RepairRecipe = RepairRecipe.for_item(data.id)
	if recipe != null:
		for step: RepairStep in recipe.steps:
			if step.part.is_empty() or _parts.has(step.part):
				continue
			var found: Array[Node3D] = []
			for node: Node in item.visual().find_children(step.part + "*", "Node3D", true, false):
				found.append(node as Node3D)
			found.sort_custom(func(a: Node3D, b: Node3D) -> bool: return a.name < b.name)
			var rest: Array[Transform3D] = []
			for node: Node3D in found:
				rest.append(node.transform)
			_parts[step.part] = {"nodes": found, "rest": rest}
	item.state_changed.connect(refresh)
	refresh()


func _process(delta: float) -> void:
	if _needle == null or items == null:
		return
	var reading: float = radiation_at(items, item.body().global_position, item)
	var target: float = DOSIMETER_SWEEP * clampf(reading / DOSIMETER_FULL, 0.0, 1.0)
	# La aguja tiene inercia: se pasa un poco y oscila antes de pararse.
	_needle_speed += (target - _needle_angle) * NEEDLE_SPRING * delta
	_needle_speed *= exp(-NEEDLE_DAMP * delta)
	_needle_angle += _needle_speed * delta
	_needle.rotation.y = _needle_angle
	if _lamp != null:
		# El piloto parpadea más deprisa cuanto más marca.
		_blink += delta * (0.6 + reading * 6.0)
		var lit: bool = reading > 0.02 and fmod(_blink, 1.0) < 0.18
		_lamp.set_surface_override_material(0, _lamp_on if lit else _lamp_off)


## Lo que marca el dosímetro en [param where]: lo que emite cada objeto
## contaminado (no embolsado), según lo cerca que está. [param skip] no cuenta.
static func radiation_at(world_items: WorldItems, where: Vector3, skip: Carryable = null) -> float:
	var total: float = 0.0
	for other: Carryable in world_items.items():
		if other == skip or other.state.emission() <= 0.0:
			continue
		var distance: float = other.body().global_position.distance_to(where)
		if distance < DOSIMETER_RANGE:
			total += other.state.emission() / (0.25 + distance * distance)
	return total


func refresh() -> void:
	var state: ItemState = item.state
	_refresh_tag(state)
	_refresh_bag(state)
	if _label != null:
		var amount: int = int(
			state.extra.get("rublos" if state.data.tool == &"billetes" else "precio", 0)
		)
		_label.text = "%d ₽" % amount if amount > 0 else ""
	_refresh_parts(state)


## La etiqueta atada: cuelga de una esquina de arriba, con el precio a lápiz.
func _refresh_tag(state: ItemState) -> void:
	if state.price < 0:
		if _tag != null:
			_tag.queue_free()
			_tag = null
		return
	var paper: Dictionary = {
		"svg": "etiqueta_precio",
		"ancho_m": 0.075,
		"rotulos":
		[
			{
				"text": "%d ₽" % state.price,
				"x": 88,
				"y": 22,
				"size": 64,
				"font": "manuscrita_negrita",
				"color": "#1b1a22",
				"rot": -4,
			}
		],
	}
	if _tag == null:
		_tag = PaperCard.create(paper)
		_tag.name = "Etiqueta"
		var bounds: AABB = item.bounds()
		_tag.position = Vector3(bounds.end.x - 0.01, bounds.end.y - 0.03, bounds.end.z + 0.004)
		_tag.rotation_degrees = Vector3(0.0, 0.0, -18.0)
		add_child(_tag)
	else:
		_tag.show_data(paper)


## Embolsado: una bolsa de plástico transparente que lo envuelve.
func _refresh_bag(state: ItemState) -> void:
	if not state.bagged:
		if _bag != null:
			_bag.queue_free()
			_bag = null
		return
	if _bag != null:
		return
	var bounds: AABB = item.bounds()
	var shell: BoxMesh = BoxMesh.new()
	shell.size = bounds.size * 1.06 + Vector3.ONE * 0.01
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = Color(0.86, 0.88, 0.84, 0.32)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.roughness = 0.35
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	_bag = MeshInstance3D.new()
	_bag.name = "Bolsa"
	_bag.mesh = shell
	_bag.material_override = material
	_bag.position = bounds.get_center()
	add_child(_bag)


## Las piezas de una reparación: los pasos hechos, hechos; el de ahora, a medias.
func _refresh_parts(state: ItemState) -> void:
	var recipe: RepairRecipe = RepairRecipe.for_item(state.data.id)
	if recipe == null:
		return
	for part: Dictionary in _parts.values():
		var nodes: Array = part["nodes"]
		var rest: Array = part["rest"]
		for index: int in nodes.size():
			(nodes[index] as Node3D).transform = rest[index]
			(nodes[index] as Node3D).visible = true
	var done: bool = bool(state.extra.get("reparado", false))
	var current: int = recipe.steps.size() if done else int(state.extra.get("paso", 0))
	for index: int in mini(current + 1, recipe.steps.size()):
		var step: RepairStep = recipe.steps[index]
		var share: float = 1.0
		if index == current:
			share = clampf(float(state.extra.get("avance", 0.0)) / maxf(step.work, 0.01), 0.0, 1.0)
		if _parts.has(step.part):
			_apply(step, _parts[step.part], share)


func _apply(step: RepairStep, part: Dictionary, share: float) -> void:
	var nodes: Array = part["nodes"]
	var rest: Array = part["rest"]
	var count: int = nodes.size()
	for index: int in count:
		var node: Node3D = nodes[index]
		var base: Transform3D = rest[index]
		# Cada pieza de un grupo (los cuatro tornillos) va a su turno.
		var own: float = clampf(share * count - index, 0.0, 1.0)
		match step.effect:
			RepairStep.Effect.UNSCREW:
				node.visible = own < 1.0
				node.transform = base.translated_local(Vector3(0.0, 0.0, -0.006 * own))
				node.rotate_object_local(Vector3.BACK, own * TAU * 2.0)
			RepairStep.Effect.SCREW:
				node.visible = share * count > index
				node.transform = base.translated_local(Vector3(0.0, 0.0, -0.006 * (1.0 - own)))
			RepairStep.Effect.REMOVE:
				node.visible = share < 1.0
				node.transform = base.translated_local(Vector3(0.0, 0.0, -0.04 * share))
			RepairStep.Effect.PUT_BACK:
				node.visible = share > 0.0
				node.transform = base.translated_local(Vector3(0.0, 0.0, -0.04 * (1.0 - share)))
			RepairStep.Effect.CLEAN:
				var mesh: MeshInstance3D = node as MeshInstance3D
				if mesh != null:
					_tint(mesh, Color.WHITE.lerp(CLEAN_CONTACTS, share))
			RepairStep.Effect.SEW:
				node.scale = Vector3(1.0, maxf(0.02, 1.0 - share), maxf(0.02, 1.0 - share))
				node.visible = share < 1.0


## Tiñe una pieza (los contactos que se limpian): una copia propia del material.
func _tint(mesh: MeshInstance3D, color: Color) -> void:
	var material: Material = mesh.get_active_material(0)
	if material is ShaderMaterial:
		if not mesh.has_meta(&"tinted"):
			material = material.duplicate()
			mesh.set_surface_override_material(0, material)
			mesh.set_meta(&"tinted", true)
		(material as ShaderMaterial).set_shader_parameter("albedo_color", color)
