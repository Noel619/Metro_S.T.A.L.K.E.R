class_name KitAssembly
extends RefCounted
## Lo que se va montando de un edificio con el kit de arquitectura: dónde va cada pieza,
## con su color y sus datos por instancia. Al final, una MultiMesh por pieza (una llamada
## de dibujo cada una), con las piezas en orden alfabético para que el resultado sea
## siempre el mismo.
##
## Los datos de cada instancia los lee el shader de los muros (tinta_muro.gdshader):
## r, el desgaste; g, el hollín de un incendio; b y a, de dónde sale el hollín.

## Las mallas del kit por nombre, con sus materiales.
var meshes: Dictionary = {}
## Las piezas que se pidieron y el kit no tiene (las tests lo comprueban).
var missing: PackedStringArray = []

## pieza -> [Array[Transform3D], Array[Color] (colores), Array[Color] (datos)]. Arrays y no
## Packed*Array: estos se copian al sacarlos del diccionario y no se podrían ir llenando.
var _batches: Dictionary = {}


func _init(kit_meshes: Dictionary) -> void:
	meshes = kit_meshes


## Pone una pieza. [param color] multiplica el color de la pieza (el tono de cada panel,
## la pintura de cada balcón); [param data] son sus datos para el shader de los muros.
func put(
	piece: String,
	placement: Transform3D,
	color: Color = Color.WHITE,
	data: Color = Color(0.0, 0.0, 0.0, 0.0)
) -> void:
	if not meshes.has(piece):
		if not missing.has(piece):
			missing.append(piece)
		return
	if not _batches.has(piece):
		var placements: Array[Transform3D] = []
		var colors: Array[Color] = []
		var values: Array[Color] = []
		_batches[piece] = [placements, colors, values]
	var batch: Array = _batches[piece]
	(batch[0] as Array[Transform3D]).append(placement)
	(batch[1] as Array[Color]).append(color)
	(batch[2] as Array[Color]).append(data)


## Cuántas veces se ha puesto una pieza.
func count(piece: String) -> int:
	return (_batches[piece][0] as Array).size() if _batches.has(piece) else 0


## Las piezas usadas, en orden.
func pieces() -> PackedStringArray:
	var names: PackedStringArray = PackedStringArray(_batches.keys())
	names.sort()
	return names


## Total de instancias.
func instance_total() -> int:
	var total: int = 0
	for piece: String in _batches:
		total += count(piece)
	return total


## Crea las MultiMesh dentro de [param parent].
func flush(parent: Node3D) -> void:
	for piece: String in pieces():
		var batch: Array = _batches[piece]
		var placements: Array[Transform3D] = batch[0]
		var colors: Array[Color] = batch[1]
		var data: Array[Color] = batch[2]
		var multimesh: MultiMesh = MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.use_colors = true
		multimesh.use_custom_data = true
		multimesh.mesh = meshes[piece]
		multimesh.instance_count = placements.size()
		for i: int in placements.size():
			multimesh.set_instance_transform(i, placements[i])
			multimesh.set_instance_color(i, colors[i])
			multimesh.set_instance_custom_data(i, data[i])
		var node: MultiMeshInstance3D = MultiMeshInstance3D.new()
		node.name = piece
		node.multimesh = multimesh
		parent.add_child(node)
