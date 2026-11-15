class_name CityTerrain
extends RefCounted
## El relieve de la maqueta, sector a sector: una rejilla que sigue data/ciudad/relieve.png
## (con el río, la loma, el barranco, el cráter y los montones de escombros).
##
## Cada sector tiene dos mallas: la detallada (cada 2 m, la resolución del relieve) y la
## lejana (cada 8 m). Por el borde llevan un faldón vertical que tapa las rendijas cuando
## un sector detallado toca uno lejano. Las normales se calculan con las alturas de los
## vecinos, también al otro lado del borde, para que no se note la costura.

const WHITE: Color = Color(1.0, 1.0, 1.0, 0.0)

var plan: CityPlan
## Triángulos de la rejilla de [member hole_step] metros que no se dibujan (los tapa el
## tránsito: CityTransit.touched), dos por celda.
var holes: PackedByteArray = PackedByteArray()
var hole_step: float = 2.0


func _init(city_plan: CityPlan) -> void:
	plan = city_plan


## Puntos por lado de la rejilla de un sector.
func grid_size(step: float) -> int:
	return int(round(plan.sector_size / step)) + 1


## Alturas de un sector cada [param step] metros (fila 0 al sur, columna 0 al oeste).
func sector_heights(sector: Vector2i, step: float) -> PackedFloat32Array:
	var corner: Vector2 = plan.sector_rect(sector).position
	var n: int = grid_size(step)
	var result: PackedFloat32Array = PackedFloat32Array()
	result.resize(n * n)
	for j: int in n:
		for i: int in n:
			result[j * n + i] = plan.height_at(corner + Vector2(i, j) * step)
	return result


## La malla del relieve de un sector, con el origen en su centro. [param skirt] es lo que
## baja el faldón del borde.
func sector_mesh(sector: Vector2i, step: float, skirt: float) -> MeshBuffer:
	var rect: Rect2 = plan.sector_rect(sector)
	return grid_mesh(rect, step, sector_heights(sector, step), rect.get_center(), skirt)


## Rejilla de alturas como malla (vértices compartidos y normales suaves), con faldón.
func grid_mesh(
	rect: Rect2, step: float, grid: PackedFloat32Array, origin: Vector2, skirt: float
) -> MeshBuffer:
	var mesh: MeshBuffer = MeshBuffer.new()
	var nx: int = int(round(rect.size.x / step)) + 1
	var ny: int = int(round(rect.size.y / step)) + 1
	mesh.vertices.resize(nx * ny)
	mesh.normals.resize(nx * ny)
	mesh.colors.resize(nx * ny)
	mesh.uvs.resize(nx * ny)
	mesh.colors.fill(WHITE)
	mesh.uvs.fill(mesh.default_uv)
	for j: int in ny:
		for i: int in nx:
			var k: int = j * nx + i
			var p: Vector2 = rect.position + Vector2(i, j) * step
			mesh.vertices[k] = Vector3(p.x - origin.x, grid[k], origin.y - p.y)
			var west: float = grid[k - 1] if i > 0 else plan.height_at(p - Vector2(step, 0.0))
			var east: float = grid[k + 1] if i < nx - 1 else plan.height_at(p + Vector2(step, 0.0))
			var south: float = grid[k - nx] if j > 0 else plan.height_at(p - Vector2(0.0, step))
			var north: float = (
				grid[k + nx] if j < ny - 1 else plan.height_at(p + Vector2(0.0, step))
			)
			mesh.normals[k] = Vector3(west - east, 2.0 * step, north - south).normalized()
	var cells: int = plan.relief_size.x
	var first: Vector2i = Vector2i((rect.position / step).round())
	var with_holes: bool = not holes.is_empty() and is_equal_approx(step, hole_step)
	for j: int in ny - 1:
		for i: int in nx - 1:
			var a: int = j * nx + i
			var id: int = -1
			if with_holes and _inside_grid(first + Vector2i(i, j)):
				id = ((first.y + j) * cells + first.x + i) * 2
			# Con el norte en -Z, (a, a+nx, a+nx+1) gira en el sentido del reloj visto desde
			# arriba: es la cara delantera para Godot (el triángulo del noroeste); (a,
			# a+nx+1, a+1), el del sureste.
			if id < 0 or holes[id] == 0:
				mesh.indices.append_array([a, a + nx, a + nx + 1])
			if id < 0 or holes[id + 1] == 0:
				mesh.indices.append_array([a, a + nx + 1, a + 1])
	if skirt > 0.0:
		_skirt(mesh, nx, ny, skirt)
	return mesh


## La forma de colisión de la rejilla de un sector ([method sector_heights]): un
## HeightMapShape3D que hay que escalar por [param step] en x y en z (sus celdas miden 1).
func heightmap_shape(step: float, grid: PackedFloat32Array) -> HeightMapShape3D:
	var n: int = grid_size(step)
	var data: PackedFloat32Array = PackedFloat32Array()
	data.resize(n * n)
	# HeightMapShape3D va de -Z a +Z: su primera fila es la del norte.
	for row: int in n:
		var j: int = n - 1 - row
		for i: int in n:
			data[row * n + i] = grid[j * n + i]
	var shape: HeightMapShape3D = HeightMapShape3D.new()
	shape.map_width = n
	shape.map_depth = n
	shape.map_data = data
	return shape


## El terreno de alrededor del mapa, hasta [param margin] metros: el borde del relieve se
## alarga hacia fuera y se hunde un poco, para que el mundo no acabe en un corte.
func surroundings_mesh(margin: float, step: float) -> MeshBuffer:
	var outer: Rect2 = Rect2(-Vector2.ONE * margin, plan.size + Vector2.ONE * margin * 2.0)
	var inner: Rect2 = Rect2(Vector2.ZERO, plan.size)
	var nx: int = int(round(outer.size.x / step)) + 1
	var ny: int = int(round(outer.size.y / step)) + 1
	var grid: PackedFloat32Array = PackedFloat32Array()
	grid.resize(nx * ny)
	for j: int in ny:
		for i: int in nx:
			var p: Vector2 = outer.position + Vector2(i, j) * step
			var clamped: Vector2 = p.clamp(Vector2.ZERO, plan.size)
			var outside: float = p.distance_to(clamped)
			grid[j * nx + i] = plan.height_at(clamped) - 0.4 - minf(outside * 0.02, 8.0)
	var mesh: MeshBuffer = grid_mesh(outer, step, grid, Vector2.ZERO, 0.0)
	# Fuera las celdas que caen dentro del mapa (ahí están los sectores).
	var kept: PackedInt32Array = PackedInt32Array()
	for t: int in range(0, mesh.indices.size(), 3):
		var a: Vector3 = mesh.vertices[mesh.indices[t]]
		var b: Vector3 = mesh.vertices[mesh.indices[t + 1]]
		var c: Vector3 = mesh.vertices[mesh.indices[t + 2]]
		var center: Vector2 = CityPlan.to_plan((a + b + c) / 3.0)
		if not inner.grow(-step * 0.5).has_point(center):
			kept.append_array([mesh.indices[t], mesh.indices[t + 1], mesh.indices[t + 2]])
	mesh.indices = kept
	return mesh


func _inside_grid(cell: Vector2i) -> bool:
	return (
		cell.x >= 0 and cell.y >= 0 and cell.x < plan.relief_size.x and cell.y < plan.relief_size.y
	)


## Un faldón que cuelga del borde de la rejilla, con las caras hacia fuera.
func _skirt(mesh: MeshBuffer, nx: int, ny: int, depth: float) -> void:
	var edges: Array = [
		[_column(0, nx, ny, 1), Vector3.BACK],  # sur (+Z)
		[_column((ny - 1) * nx, nx, ny, 1), Vector3.FORWARD],  # norte (-Z)
		[_column(0, nx, ny, nx), Vector3.LEFT],  # oeste
		[_column(nx - 1, nx, ny, nx), Vector3.RIGHT],  # este
	]
	var tint: PackedColorArray = PackedColorArray([WHITE])
	for edge: Array in edges:
		var row: PackedInt32Array = edge[0]
		for i: int in row.size() - 1:
			var a: Vector3 = mesh.vertices[row[i]]
			var b: Vector3 = mesh.vertices[row[i + 1]]
			var down: Vector3 = Vector3.DOWN * depth
			mesh.add_face(PackedVector3Array([a, b, b + down, a + down]), edge[1], tint)


func _column(start: int, nx: int, ny: int, stride: int) -> PackedInt32Array:
	var result: PackedInt32Array = PackedInt32Array()
	var count: int = nx if stride == 1 else ny
	for i: int in count:
		result.append(start + i * stride)
	return result
