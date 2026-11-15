"""Utilidades comunes para las recetas de modelos de Tumansk.

Blender 5 se usa como módulo de Python (``pip install bpy``). Cada receta de
``recipes/`` construye sus modelos con estas funciones y ``build_assets.py``
los exporta a ``assets/models/`` como ``.glb``.

Reglas del estilo (ver docs/ESTILO.md):

- Nada es perfectamente recto: imperfección controlada y siempre determinista
  (todo depende de semillas, así que dos ejecuciones dan el mismo modelo).
- Biseles generosos para que el sombreado por bandas quede limpio.
- El color base, la oclusión y las cavidades se pintan en los colores por
  vértice, como una ilustración pintada a mano.

Convenciones de nombre que entiende tools/godot/post_import.gd:

- ``<nombre>-fisico`` / ``<nombre>-estatico``: la raíz del modelo pasa a ser un
  cuerpo físico (RigidBody3D / StaticBody3D).
- ``<nombre>-colcaja`` / ``<nombre>-colconvexa``: malla de colisión.
- El nombre del material elige el material de Godot si existe
  ``assets/materials/<nombre>.tres``.
"""

from __future__ import annotations

import contextlib
import io
import math
import random
from collections.abc import Iterable
from pathlib import Path

# bpy tiene que importarse antes que bmesh y mathutils: es quien los hace visibles.
import bpy  # isort: skip
import bmesh  # isort: skip
from mathutils import Euler, Matrix, Quaternion, Vector, noise
from mathutils.bvhtree import BVHTree

COLLISION_SUFFIXES = ("-colcaja", "-colconvexa")


# --------------------------------------------------------------------------
# Escena y materiales
# --------------------------------------------------------------------------


def reset_scene() -> None:
    """Empieza cada modelo desde una escena vacía."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hex_to_linear(hex_color: str) -> tuple[float, float, float]:
    """Convierte un color sRGB en hexadecimal a valores lineales."""
    value = hex_color.lstrip("#")
    srgb = [int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb)


def material(name: str, hex_color: str) -> bpy.types.Material:
    """Material con nombre: Godot lo sustituirá por el suyo si existe."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*hex_to_linear(hex_color), 1.0)
    if mat.node_tree is not None:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    return mat


def is_collision(obj: bpy.types.Object) -> bool:
    return obj.name.endswith(COLLISION_SUFFIXES)


# --------------------------------------------------------------------------
# Construcción
# --------------------------------------------------------------------------


def empty(name: str, parent: bpy.types.Object | None = None) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def mesh_object(
    name: str,
    bm: bmesh.types.BMesh,
    mat: bpy.types.Material | None = None,
    parent: bpy.types.Object | None = None,
    smooth: bool = True,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if mat is not None:
        mesh.materials.append(mat)
    if smooth:
        mesh.shade_smooth()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def box(
    name: str,
    size: Iterable[float],
    center: Iterable[float] = (0.0, 0.0, 0.0),
    *,
    cuts: int = 0,
    bevel: float = 0.0,
    segments: int = 2,
    mat: bpy.types.Material | None = None,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    """Caja con biseles. ``cuts`` subdivide las caras para poder deformarlas."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    if cuts > 0:
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    if bevel > 0.0:
        bm.normal_update()
        sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > 0.5]
        bmesh.ops.bevel(
            bm,
            geom=sharp,
            offset=bevel,
            segments=segments,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )
    return mesh_object(name, bm, mat, parent)


def collision_box(
    name: str,
    size: Iterable[float],
    center: Iterable[float],
    parent: bpy.types.Object,
) -> bpy.types.Object:
    """Malla auxiliar que Godot convierte en una colisión de caja."""
    return box(f"{name}-colcaja", size, center, parent=parent)


class MeshBuilder:
    """Construye una malla con muchas piezas (baldosas, tablones, barras...).

    Cada pieza lleva su propio color base, que se guarda por esquina en el
    atributo "Base"; ``paint`` lo usa después como color de partida. Las piezas
    con bisel se sombrean suaves; las demás, planas.
    """

    def __init__(self, seed: int = 0) -> None:
        self.bm = bmesh.new()
        self.base = self.bm.loops.layers.color.new("Base")
        self.rng = random.Random(seed)

    def _finish_piece(self, before: set, color: str, jitter: float, smooth: bool) -> list:
        faces = [f for f in self.bm.faces if f not in before]
        # Las capas de color de bmesh guardan sRGB (no lineal).
        hex_value = color.lstrip("#")
        srgb = Vector(int(hex_value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        if jitter > 0.0:
            srgb *= 1.0 + self.rng.uniform(-jitter, jitter)
        value = (min(1.0, srgb.x), min(1.0, srgb.y), min(1.0, srgb.z), 1.0)
        for face in faces:
            face.smooth = smooth
            for loop in face.loops:
                loop[self.base] = value
        return faces

    def box(
        self,
        size: Iterable[float],
        center: Iterable[float],
        color: str,
        *,
        rotation: Iterable[float] = (0.0, 0.0, 0.0),
        bevel: float = 0.0,
        segments: int = 1,
        jitter: float = 0.0,
        cuts: int = 0,
    ) -> list:
        """Caja; ``rotation`` en grados (X, Y, Z) y ``jitter`` varía el color.

        Con ``cuts`` las caras se subdividen: hace falta para que las manchas y el
        hollín (``stain``, ``scorch``) puedan variar dentro de una misma pieza.
        """
        before = set(self.bm.faces)
        matrix = Matrix.LocRotScale(
            Vector(center), Euler([math.radians(a) for a in rotation]).to_quaternion(), Vector(size)
        )
        result = bmesh.ops.create_cube(self.bm, size=1.0, matrix=matrix, calc_uvs=True)
        if cuts > 0:
            edges = list({edge for vert in result["verts"] for edge in vert.link_edges})
            bmesh.ops.subdivide_edges(self.bm, edges=edges, cuts=cuts, use_grid_fill=True)
        if bevel > 0.0:
            self.bm.normal_update()
            piece_edges = {edge for face in self.bm.faces if face not in before for edge in face.edges}
            edges = [
                edge
                for edge in piece_edges
                if len(edge.link_faces) == 2 and edge.calc_face_angle(0.0) > 0.5
            ]
            bmesh.ops.bevel(
                self.bm, geom=edges, offset=bevel, segments=segments, profile=0.5,
                affect="EDGES", clamp_overlap=True,
            )
        return self._finish_piece(before, color, jitter, smooth=bevel > 0.0)

    def cylinder(
        self,
        radius: float,
        depth: float,
        center: Iterable[float],
        color: str,
        *,
        rotation: Iterable[float] = (0.0, 0.0, 0.0),
        radius_top: float | None = None,
        segments: int = 16,
        caps: bool = True,
        jitter: float = 0.0,
    ) -> list:
        """Cilindro (o tronco de cono) a lo largo de su eje Z local."""
        before = set(self.bm.faces)
        matrix = Matrix.LocRotScale(
            Vector(center), Euler([math.radians(a) for a in rotation]).to_quaternion(), None
        )
        bmesh.ops.create_cone(
            self.bm, cap_ends=caps, cap_tris=False, segments=segments, radius1=radius,
            radius2=radius if radius_top is None else radius_top, depth=depth, matrix=matrix,
        )
        faces = self._finish_piece(before, color, jitter, smooth=True)
        axis = (matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        for face in faces:
            face.normal_update()
            if abs(face.normal.dot(axis)) > 0.99:
                face.smooth = False
        return faces

    def sphere(
        self,
        radius: float,
        center: Iterable[float],
        color: str,
        segments: int = 16,
        scale: Iterable[float] = (1.0, 1.0, 1.0),
        jitter: float = 0.0,
    ) -> list:
        before = set(self.bm.faces)
        matrix = Matrix.LocRotScale(Vector(center), None, Vector(scale))
        bmesh.ops.create_uvsphere(
            self.bm, u_segments=segments, v_segments=max(6, segments // 2), radius=radius, matrix=matrix
        )
        return self._finish_piece(before, color, jitter, smooth=True)

    def flip(self, faces: list) -> None:
        """Da la vuelta a las caras (para el interior de pantallas y cubos)."""
        bmesh.ops.reverse_faces(self.bm, faces=faces)

    def bar(self, start: Iterable[float], end: Iterable[float], radius: float, color: str, segments: int = 8) -> list:
        """Barra cilíndrica entre dos puntos (tubos, cables, varillas)."""
        a, b = Vector(start), Vector(end)
        direction = b - a
        rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized()).to_euler()
        return self.cylinder(
            radius, direction.length, (a + b) / 2.0, color,
            rotation=[math.degrees(r) for r in rotation], segments=segments,
        )

    def finish(
        self,
        name: str,
        mat: bpy.types.Material | None = None,
        parent: bpy.types.Object | None = None,
    ) -> bpy.types.Object:
        bmesh.ops.remove_doubles(self.bm, verts=list(self.bm.verts), dist=0.00001)
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        if mat is not None:
            mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = parent
        return obj


# --------------------------------------------------------------------------
# Imperfección controlada
# --------------------------------------------------------------------------


def box_bulge_offset(
    point: Vector, center: Vector, half: Vector, amount: float
) -> Vector:
    """Desplazamiento que hincha las caras de una caja, más en el centro de cada cara.

    Es un campo, no depende de la malla: así la caja y lo que va pegado encima
    (cinta, etiquetas) se deforman igual.
    """
    q = Vector((point - center)[i] / half[i] for i in range(3))
    axis = max(range(3), key=lambda i: abs(q[i]))
    falloff = 1.0
    for i in range(3):
        if i != axis:
            falloff *= max(0.0, 1.0 - q[i] * q[i])
    direction = Vector((0.0, 0.0, 0.0))
    direction[axis] = 1.0 if q[axis] >= 0.0 else -1.0
    return direction * amount * falloff


def apply_bulge(obj: bpy.types.Object, center: Iterable[float], half: Iterable[float], amount: float) -> None:
    c, h = Vector(center), Vector(half)
    for v in obj.data.vertices:
        v.co += box_bulge_offset(v.co, c, h, amount)


def wobble(obj: bpy.types.Object, amount: float, scale: float = 3.0, seed: int = 0) -> None:
    """Ondulación suave y determinista: que nada parezca hecho con regla."""
    offset = Vector((seed * 13.17, seed * 7.31, seed * 3.77))
    shifts = (Vector((0.0, 0.0, 0.0)), Vector((31.4, 0.0, 0.0)), Vector((0.0, 47.2, 0.0)))
    for v in obj.data.vertices:
        p = v.co * scale + offset
        v.co += Vector(noise.noise(p + s) for s in shifts) * amount


def stain(
    obj: bpy.types.Object,
    hex_color: str,
    *,
    amount: float = 0.6,
    scale: float = 3.0,
    coverage: float = 0.3,
    seed: int = 0,
    stretch_z: float = 1.0,
) -> None:
    """Manchas (óxido, humedad, suciedad) sobre el color base del atributo "Base".

    Con ``stretch_z`` < 1 las manchas se alargan en vertical, como chorretones.
    """
    mesh = obj.data
    layer = mesh.color_attributes.get("Base")
    if layer is None:
        raise ValueError(f"{obj.name} no tiene colores base: créalo con MeshBuilder")
    target = Vector(hex_to_linear(hex_color))
    offset = Vector((seed * 3.1, seed * 1.3, seed * 2.7))
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        position = Vector((co.x, co.y, co.z * stretch_z)) * scale + offset
        value = noise.noise(position) * 0.5 + 0.5
        weight = min(1.0, max(0.0, (value - (1.0 - coverage)) / 0.15)) * amount
        color = Vector(layer.data[loop.index].color[:3]).lerp(target, weight)
        layer.data[loop.index].color = (*color, 1.0)


def scorch(
    obj: bpy.types.Object,
    regions: list[tuple[Iterable[float], float, float]],
    hex_color: str = "#141211",
    strength: float = 0.9,
) -> None:
    """Hollín de incendio sobre el color base: sale de cada región y sube.

    Cada región es ``(punto, ancho, alto)``: el punto es el borde superior de
    una ventana quemada; la mancha se ensancha un poco al subir y se desvanece.
    """
    mesh = obj.data
    layer = mesh.color_attributes.get("Base")
    if layer is None:
        raise ValueError(f"{obj.name} no tiene colores base: créalo con MeshBuilder")
    target = Vector(hex_to_linear(hex_color))
    sources = [(Vector(point), width, height) for point, width, height in regions]
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        weight = 0.0
        for point, width, height in sources:
            rise = co.z - point.z
            if rise < -0.25 or rise > height:
                continue
            spread = width * (0.5 + 0.35 * max(rise, 0.0) / height)
            side = abs(co.x - point.x) / max(spread, 0.01)
            wiggle = 0.25 * noise.noise(Vector((co.x * 3.0, co.z * 1.5, point.x)))
            fade = (1.0 - max(rise, 0.0) / height) * (1.0 - min(1.0, side + wiggle))
            weight = max(weight, fade)
        if weight > 0.0:
            color = Vector(layer.data[loop.index].color[:3]).lerp(target, min(1.0, weight * strength * 1.6))
            layer.data[loop.index].color = (*color, 1.0)


def dent(obj: bpy.types.Object, center: Iterable[float], radius: float, depth: float) -> None:
    """Abolladura suave hacia dentro alrededor de ``center``."""
    c = Vector(center)
    obj.data.update()
    for v in obj.data.vertices:
        distance = (v.co - c).length
        if distance < radius:
            weight = 0.5 * (1.0 + math.cos(math.pi * distance / radius))
            v.co -= v.normal * depth * weight


# --------------------------------------------------------------------------
# Pintura por vértice: color base, oclusión, cavidades y manchas
# --------------------------------------------------------------------------


def _hemisphere(samples: int, seed: int) -> list[Vector]:
    """Direcciones repartidas por el hemisferio +Z, con peso de coseno."""
    rng = random.Random(seed)
    golden = math.pi * (3.0 - math.sqrt(5.0))
    directions = []
    for i in range(samples):
        u = (i + rng.random()) / samples
        radius = math.sqrt(u)
        theta = golden * i
        x, y = radius * math.cos(theta), radius * math.sin(theta)
        directions.append(Vector((x, y, math.sqrt(max(0.0, 1.0 - u)))))
    return directions


def _world_bvh(objects: list[bpy.types.Object], ground_z: float | None) -> BVHTree:
    vertices: list[Vector] = []
    polygons: list[tuple[int, ...]] = []
    for obj in objects:
        base = len(vertices)
        matrix = obj.matrix_world
        vertices.extend(matrix @ v.co for v in obj.data.vertices)
        polygons.extend(tuple(base + i for i in p.vertices) for p in obj.data.polygons)
    if ground_z is not None:
        base = len(vertices)
        size = 50.0
        vertices.extend(
            Vector((x, y, ground_z)) for x, y in ((-size, -size), (size, -size), (size, size), (-size, size))
        )
        polygons.append((base, base + 1, base + 2, base + 3))
    return BVHTree.FromPolygons(vertices, polygons)


def _base_colors(mesh: bpy.types.Mesh, hex_color: str | None) -> list[tuple[float, float, float]]:
    """Color base de cada esquina: el atributo "Base" si existe (MeshBuilder), si no ``hex_color``."""
    layer = mesh.color_attributes.get("Base")
    if layer is not None and layer.domain == "CORNER":
        return [tuple(layer.data[i].color[:3]) for i in range(len(mesh.loops))]
    base = hex_to_linear(hex_color or "#ffffff")
    return [base] * len(mesh.loops)


def paint(
    colors: dict[bpy.types.Object, str | None],
    *,
    ao: float = 0.55,
    ao_distance: float = 0.25,
    samples: int = 32,
    cavity_dark: float = 0.35,
    edge_light: float = 0.12,
    mottling: float = 0.06,
    ground_z: float | None = 0.0,
    seed: int = 0,
) -> None:
    """Pinta los colores por vértice de varias piezas a la vez.

    Todas las piezas se tapan entre sí al calcular la oclusión, y el suelo
    (``ground_z``) también, para que el objeto "pese" sobre él.
    """
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not is_collision(o)]
    bvh = _world_bvh(meshes, ground_z)
    directions = _hemisphere(samples, seed)
    up = Vector((0.0, 0.0, 1.0))
    noise_offset = Vector((seed * 5.3, seed * 1.7, seed * 9.1))
    for obj, hex_color in colors.items():
        mesh = obj.data
        mesh.update()
        corner_base = _base_colors(mesh, hex_color)
        matrix = obj.matrix_world
        normal_matrix = matrix.to_3x3()
        count = len(mesh.vertices)
        neighbours: list[list[int]] = [[] for _ in range(count)]
        for edge in mesh.edges:
            a, b = edge.vertices
            neighbours[a].append(b)
            neighbours[b].append(a)
        # Cavidad: >0 en los huecos, <0 en las aristas que sobresalen.
        cavity = [0.0] * count
        for i, v in enumerate(mesh.vertices):
            if neighbours[i]:
                n = v.normal
                cavity[i] = sum(
                    n.dot((mesh.vertices[j].co - v.co).normalized()) for j in neighbours[i]
                ) / len(neighbours[i])
        for _ in range(2):
            cavity = [
                0.5 * cavity[i] + 0.5 * sum(cavity[j] for j in neighbours[i]) / max(1, len(neighbours[i]))
                for i in range(count)
            ]
        values = []
        for i, v in enumerate(mesh.vertices):
            position = matrix @ v.co
            normal = (normal_matrix @ v.normal).normalized()
            rotation: Quaternion = up.rotation_difference(normal)
            origin = position + normal * 0.002
            hits = 0.0
            for direction in directions:
                hit, _, _, distance = bvh.ray_cast(origin, rotation @ direction, ao_distance)
                if hit is not None:
                    hits += 1.0 - 0.5 * (distance / ao_distance)
            occlusion = hits / samples
            shade = (1.0 - ao * occlusion)
            shade *= 1.0 - cavity_dark * max(0.0, cavity[i]) * 4.0
            shade *= 1.0 + edge_light * max(0.0, -cavity[i]) * 4.0
            shade *= 1.0 + mottling * noise.noise(position * 4.0 + noise_offset)
            values.append(shade)
        attribute = mesh.color_attributes.get("Color") or mesh.color_attributes.new(
            name="Color", type="BYTE_COLOR", domain="CORNER"
        )
        for loop in mesh.loops:
            shade = values[loop.vertex_index]
            color = tuple(min(1.0, max(0.0, c * shade)) for c in corner_base[loop.index])
            attribute.data[loop.index].color = (*color, 1.0)
        # El color base ya está dentro de "Color": se quita para que solo se exporte uno.
        base_layer = mesh.color_attributes.get("Base")
        if base_layer is not None:
            mesh.color_attributes.remove(base_layer)
        attribute = mesh.color_attributes["Color"]
        mesh.color_attributes.active_color = attribute
        mesh.color_attributes.render_color_index = mesh.color_attributes.active_color_index


# --------------------------------------------------------------------------
# Exportación
# --------------------------------------------------------------------------


def export_glb(root: bpy.types.Object, path: Path) -> None:
    """Exporta ``root`` y todos sus hijos a un .glb."""
    path.parent.mkdir(parents=True, exist_ok=True)
    objects = [root, *root.children_recursive]
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    # El exportador escribe una línea por pieza; se silencia para no ensuciar la salida.
    with contextlib.redirect_stdout(io.StringIO()):
        _export_gltf(path)


def _export_gltf(path: Path) -> None:
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_vertex_color="ACTIVE",
        export_normals=True,
        export_tangents=False,
        export_texcoords=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_extras=False,
    )
