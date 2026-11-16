extends "res://tests/test_case.gd"
## El kit de arquitectura (F3-16): las piezas que piden las reglas existen, sus medidas casan
## con las de las reglas (las recetas de Blender y Godot tienen que decir lo mismo) y el
## mismo edificio sale siempre igual.

var _kit: BuildingKit


func before_each() -> void:
	_kit = BuildingKit.new()


func test_every_piece_the_rules_ask_for_exists() -> void:
	for kind: String in ["jrushchovka", "bloque9", "torre16"]:
		for damage: int in range(1, 5):
			for fire: String in ["no", "parcial", "total"]:
				var node: Node3D = _kit.build(_spec(kind, damage, fire))
				var missing: PackedStringArray = node.get_meta(&"kit_faltan")
				var label: String = "%s, daño %d, incendio %s" % [kind, damage, fire]
				assert_true(missing.is_empty(), "%s: faltan %s" % [label, ", ".join(missing)])
				assert_true(int(node.get_meta(&"kit_piezas")) > 100, "%s: casi vacío" % label)
				node.free()


func test_masonry_houses_follow_any_footprint() -> void:
	# Una L, una curva (como las casas de la plaza) y un recorte con astillas.
	var curve: PackedVector2Array = PackedVector2Array()
	for k: int in 21:
		var angle: float = deg_to_rad(200.0 + k * 3.0)
		curve.append(Vector2(cos(angle), sin(angle)) * 100.0)
	for k: int in range(20, -1, -1):
		var angle: float = deg_to_rad(200.0 + k * 3.0)
		curve.append(Vector2(cos(angle), sin(angle)) * 84.0)
	var shapes: Dictionary = {
		"ele":
		PackedVector2Array(
			[
				Vector2(0, 0),
				Vector2(60, 0),
				Vector2(60, 16),
				Vector2(16, 16),
				Vector2(16, 50),
				Vector2(0, 50)
			]
		),
		"curva": curve,
		"recorte":
		PackedVector2Array(
			[Vector2(0, 0), Vector2(40, 0), Vector2(40.2, 0.1), Vector2(40, 16), Vector2(0, 16)]
		),
	}
	for shape: String in shapes:
		for kind: String in ["estalinka", "estalinka_baja", "prerrevolucion"]:
			for damage: int in range(1, 5):
				var spec: Dictionary = {
					"tipo": kind,
					"clave": "PRUEBA-%s-%s-%d" % [shape, kind, damage],
					"huella": shapes[shape],
					"pisos": {"estalinka": 7, "estalinka_baja": 3, "prerrevolucion": 3}[kind],
					"dano": damage,
					"incendio": "parcial",
					"patios": PackedVector2Array([Vector2(30, 40)]),
					"arco": true,
					"bomba": Vector2(800.0, 600.0),
				}
				var node: Node3D = _kit.build(spec)
				var missing: PackedStringArray = node.get_meta(&"kit_faltan")
				var label: String = "%s %s, daño %d" % [kind, shape, damage]
				assert_true(missing.is_empty(), "%s: faltan %s" % [label, ", ".join(missing)])
				assert_true(int(node.get_meta(&"kit_piezas")) > 60, "%s: casi vacío" % label)
				node.free()


func test_wooden_houses_pick_their_state() -> void:
	# Ardieron casi todas: con incendio total o daño 4 quedan los restos.
	assert_eq(KitWhole.state_of({"dano": 1, "incendio": "total"}), "quemada")
	assert_eq(KitWhole.state_of({"dano": 4, "incendio": "no"}), "quemada")
	assert_eq(KitWhole.state_of({"dano": 3, "incendio": "parcial"}), "cascaron")
	assert_eq(KitWhole.state_of({"dano": 2, "incendio": "no"}), "chamuscada")
	assert_eq(KitWhole.state_of({"dano": 1, "incendio": "no"}), "intacta")
	for kind: String in ["casa_madera", "barracon"]:
		for damage: int in range(1, 5):
			for fire: String in ["no", "parcial", "total"]:
				var spec: Dictionary = _spec("jrushchovka", damage, fire)
				spec["tipo"] = kind
				spec["huella"] = PackedVector2Array(
					[Vector2(0, 0), Vector2(9, 0), Vector2(9, 8), Vector2(0, 8)]
				)
				var node: Node3D = _kit.build(spec)
				var missing: PackedStringArray = node.get_meta(&"kit_faltan")
				assert_true(missing.is_empty(), "%s: faltan %s" % [kind, ", ".join(missing)])
				assert_eq(int(node.get_meta(&"kit_piezas")), 1, "%s es una casa entera" % kind)
				node.free()


func test_pieces_match_the_rules_measures() -> void:
	var meshes: Dictionary = _kit.meshes_for("jrushchovka")
	# Las piezas de un vano ocupan su vano y su planta, y el muro entra hacia -z.
	for piece: String in ["panel_ventana", "panel_cocina", "panel_balcon", "panel_ciego"]:
		var box: AABB = (meshes[piece] as Mesh).get_aabb()
		assert_almost(box.position.x, 0.0, 0.01, piece)
		assert_almost(box.end.x, KitPanelBlock.BAY, 0.01, piece)
		assert_almost(box.end.y, KitPanelBlock.STOREY, 0.01, piece)
		assert_almost(box.position.z, -KitPanelBlock.WALL, 0.01, piece)
	var tops: Dictionary = {
		"panel_portal": KitPanelBlock.PORTAL_HEIGHT,
		"panel_remate": KitPanelBlock.STOREY * 0.5,
		"zocalo": KitPanelBlock.PLINTH,
	}
	for piece: String in tops:
		assert_almost((meshes[piece] as Mesh).get_aabb().end.y, tops[piece], 0.01, piece)
	# La logia entra en el muro lo que dicen las reglas (más el panel del fondo).
	var loggia: AABB = (meshes["panel_logia"] as Mesh).get_aabb()
	assert_almost(loggia.position.z, -(KitPanelBlock.LOGGIA + KitPanelBlock.WALL), 0.01)


func test_skins_change_materials_not_shapes() -> void:
	var plain: Dictionary = _kit.meshes_for("jrushchovka")
	var tiled: Dictionary = _kit.meshes_for("bloque9")
	var panel: Mesh = tiled["panel_ventana"]
	assert_eq(panel.surface_get_material(0).resource_name, "azulejo")
	assert_eq((plain["panel_ventana"] as Mesh).surface_get_material(0).resource_name, "muro")
	assert_eq(panel.get_aabb(), (plain["panel_ventana"] as Mesh).get_aabb())


func test_the_same_building_is_always_the_same() -> void:
	var first: Node3D = _kit.build(_spec("bloque9", 2, "parcial"))
	var second: Node3D = _kit.build(_spec("bloque9", 2, "parcial"))
	assert_eq(first.get_child_count(), second.get_child_count())
	for child: Node in first.get_children():
		var twin: Node = second.get_node_or_null(NodePath(child.name))
		assert_true(twin != null, "falta %s en el segundo" % child.name)
		if child is MultiMeshInstance3D and twin is MultiMeshInstance3D:
			var a: MultiMesh = (child as MultiMeshInstance3D).multimesh
			var b: MultiMesh = (twin as MultiMeshInstance3D).multimesh
			assert_eq(a.instance_count, b.instance_count, String(child.name))
			if a.instance_count > 0:
				assert_eq(
					a.get_instance_transform(0), b.get_instance_transform(0), String(child.name)
				)
	first.free()
	second.free()


func test_damage_lowers_the_end_facing_the_bomb() -> void:
	# La bomba al este: el extremo este de la jrushchovka es el que se hunde.
	var spec: Dictionary = _spec("jrushchovka", 2, "no")
	spec["bomba"] = Vector2(5000.0, 6.0)
	var block: KitPanelBlock = KitPanelBlock.new(
		spec, KitAssembly.new(_kit.meshes_for("jrushchovka"))
	)
	var holder: Node3D = Node3D.new()
	block.build(holder)
	holder.free()
	assert_eq(block.standing[0], 5, "el extremo oeste sigue entero")
	assert_true(block.standing[block.standing.size() - 1] < 5, "el extremo este se ha hundido")
	assert_true(block.broken[block.broken.size() - 1], "lo hundido acaba en muñones")


func test_plan_buildings_are_built() -> void:
	var plan: CityPlan = CityPlan.load_default()
	var built: int = 0
	for building: Dictionary in plan.data["edificios"]:
		if not BuildingKit.supports(building["tipo"]):
			continue
		var spec: Dictionary = {
			"tipo": building["tipo"],
			"clave": building["id"],
			"huella": CityPlan.ring(building["huella"][0]),
			"pisos": int(building["pisos"]),
			"dano": int(building["dano"]),
			"incendio": building["incendio"],
			"bomba": plan.ground_zero(),
			"arco": String(building.get("notas", "")).contains("Arco"),
		}
		var node: Node3D = _kit.build(spec)
		var missing: PackedStringArray = node.get_meta(&"kit_faltan")
		assert_true(missing.is_empty(), "%s: faltan %s" % [building["id"], ", ".join(missing)])
		node.free()
		built += 1
	assert_eq(built, 138, "todas las viviendas del plano: paneles, muros de carga y madera")


func _spec(kind: String, damage: int, fire: String) -> Dictionary:
	var length: float = 64.0 if kind == "jrushchovka" else (26.0 if kind == "torre16" else 80.0)
	var depth: float = 12.0 if kind == "jrushchovka" else (22.0 if kind == "torre16" else 13.0)
	return {
		"tipo": kind,
		"clave": "PRUEBA-%s-%d-%s" % [kind, damage, fire],
		"huella":
		PackedVector2Array(
			[Vector2(0.0, 0.0), Vector2(length, 0.0), Vector2(length, depth), Vector2(0.0, depth)]
		),
		"pisos": {"jrushchovka": 5, "bloque9": 9, "torre16": 16}[kind],
		"dano": damage,
		"incendio": fire,
		"entrada": 0,
		"bomba": Vector2(800.0, 600.0),
	}
