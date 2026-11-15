class_name MeshBuffer
extends RefCounted
## Junta caras (posición, normal, color y UV) y las convierte en una malla.
##
## Cada cara se da con la dirección hacia la que mira (fuera de un muro, arriba en una
## cubierta) y la clase pone sus vértices en el orden que Godot espera, así que nadie
## tiene que acertar el sentido de giro a mano. Las normales son planas, como en el resto
## del estilo. El canal alfa del color se usa como máscara (por ejemplo, de las ventanas).

## UV para las caras que no dan la suya.
var default_uv: Vector2 = Vector2(0.5, 0.95)
var vertices: PackedVector3Array = PackedVector3Array()
var normals: PackedVector3Array = PackedVector3Array()
var colors: PackedColorArray = PackedColorArray()
var uvs: PackedVector2Array = PackedVector2Array()
var indices: PackedInt32Array = PackedInt32Array()


func is_empty() -> bool:
	return indices.is_empty()


func triangle_count() -> int:
	return indices.size() / 3


## Una cara plana y convexa (se triangula en abanico desde el primer punto). Si los
## puntos no la dejan mirando hacia [param facing], se le da la vuelta.
func add_face(
	points: PackedVector3Array,
	facing: Vector3,
	face_colors: PackedColorArray,
	face_uvs: PackedVector2Array = PackedVector2Array()
) -> void:
	var count: int = points.size()
	if count < 3:
		return
	var normal: Vector3 = _newell(points)
	if normal.length_squared() < 1e-12:
		return
	normal = normal.normalized()
	var flip: bool = normal.dot(facing) < 0.0
	if flip:
		normal = -normal
	var base: int = vertices.size()
	for i: int in count:
		vertices.append(points[i])
		normals.append(normal)
		colors.append(face_colors[mini(i, face_colors.size() - 1)])
		uvs.append(face_uvs[i] if i < face_uvs.size() else default_uv)
	for i: int in range(1, count - 1):
		# Godot dibuja la cara delantera con los vértices en el sentido del reloj.
		if flip:
			indices.append_array([base, base + i, base + i + 1])
		else:
			indices.append_array([base, base + i + 1, base + i])


## Un polígono horizontal cualquiera (también cóncavo) a la altura [param height], ya
## triangulado (índices de [method Geometry2D.triangulate_polygon]). [param to_local]
## pasa del plano al espacio de la malla.
func add_cap(
	outline: PackedVector2Array,
	triangles: PackedInt32Array,
	height: float,
	color: Color,
	origin: Vector2,
	facing_up: bool = true
) -> void:
	var facing: Vector3 = Vector3.UP if facing_up else Vector3.DOWN
	var face: PackedVector3Array = PackedVector3Array()
	face.resize(3)
	var tint: PackedColorArray = PackedColorArray([color])
	for t: int in range(0, triangles.size(), 3):
		for k: int in 3:
			var p: Vector2 = outline[triangles[t + k]]
			face[k] = Vector3(p.x - origin.x, height, origin.y - p.y)
		add_face(face, facing, tint)


## Una caja orientada: [param basis] lleva las medias medidas en sus columnas.
func add_box(center: Vector3, basis: Basis, color: Color) -> void:
	var tint: PackedColorArray = PackedColorArray([color])
	for axis: int in 3:
		for side: float in [-1.0, 1.0]:
			var normal: Vector3 = basis[axis] * side
			var u: Vector3 = basis[(axis + 1) % 3]
			var v: Vector3 = basis[(axis + 2) % 3]
			var middle: Vector3 = center + normal
			var face: PackedVector3Array = PackedVector3Array(
				[middle - u - v, middle + u - v, middle + u + v, middle - u + v]
			)
			add_face(face, normal, tint)


## Una viga o un muro entre dos puntos del eje inferior: [param width] de ancho y
## [param height] de alto, con el lado alto hacia arriba.
func add_beam(from: Vector3, to: Vector3, width: float, height: float, color: Color) -> void:
	var along: Vector3 = to - from
	if along.length_squared() < 1e-6:
		return
	var side: Vector3 = along.cross(Vector3.UP)
	if side.length_squared() < 1e-6:
		side = Vector3.RIGHT
	side = side.normalized() * (width * 0.5)
	var up: Vector3 = side.cross(along).normalized() * (height * 0.5)
	if up.y < 0.0:
		up = -up
	add_box((from + to) * 0.5 + up, Basis(along * 0.5, up, side), color)


## Añade todas las caras de otra malla, desplazadas.
func append(other: MeshBuffer, offset: Vector3 = Vector3.ZERO) -> void:
	var base: int = vertices.size()
	for p: Vector3 in other.vertices:
		vertices.append(p + offset)
	normals.append_array(other.normals)
	colors.append_array(other.colors)
	uvs.append_array(other.uvs)
	for index: int in other.indices:
		indices.append(base + index)


## La malla, con un material opcional.
func to_mesh(material: Material = null) -> ArrayMesh:
	var mesh: ArrayMesh = ArrayMesh.new()
	if is_empty():
		return mesh
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	if material != null:
		mesh.surface_set_material(0, material)
	return mesh


## Los triángulos como lista de vértices de tres en tres (para ConcavePolygonShape3D).
func faces(offset: Vector3 = Vector3.ZERO) -> PackedVector3Array:
	var result: PackedVector3Array = PackedVector3Array()
	result.resize(indices.size())
	for i: int in indices.size():
		result[i] = vertices[indices[i]] + offset
	return result


## Normal de un polígono por el método de Newell (aguanta puntos casi alineados). Sigue
## la regla de la mano derecha: puntos en sentido antihorario vistos desde delante.
static func _newell(points: PackedVector3Array) -> Vector3:
	var normal: Vector3 = Vector3.ZERO
	var count: int = points.size()
	for i: int in count:
		var a: Vector3 = points[i]
		var b: Vector3 = points[(i + 1) % count]
		normal.x += (a.y - b.y) * (a.z + b.z)
		normal.y += (a.z - b.z) * (a.x + b.x)
		normal.z += (a.x - b.x) * (a.y + b.y)
	return normal
