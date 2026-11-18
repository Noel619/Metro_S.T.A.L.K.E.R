"""Utilidades para modelar, esqueletar y animar personajes por código.

Complementa a ``tumansk_bpy``: las mismas reglas del estilo (formas robustas,
nada perfectamente recto, color pintado en los vértices), pero para cuerpos que
se doblan. Un personaje se construye así:

1. ``Sculpt``: piezas blandas (tubos por anillos, bultos, paneles con grosor)
   que llevan su color base y sus pesos de hueso desde que nacen. Al terminar
   se suavizan con una subdivisión Catmull-Clark.
2. ``build_armature``: el esqueleto, con los nombres del perfil humanoide de
   Godot para poder compartir animaciones entre personas (D-042).
3. ``Pose`` y ``bake_action``: las animaciones son funciones del tiempo que
   devuelven una pose; se muestrean y se guardan como acciones.

Coordenadas de Blender: el personaje mira hacia -Y, su izquierda es +X y Z es
arriba. (En Godot queda mirando a +Z, como espera el perfil humanoide.)
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

# bpy tiene que importarse antes que bmesh y mathutils.
import bpy  # isort: skip
import bmesh  # isort: skip
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

FRONT = Vector((0.0, -1.0, 0.0))
UP = Vector((0.0, 0.0, 1.0))
LEFT = Vector((1.0, 0.0, 0.0))

Weights = dict[str, float]
WeightSpec = Weights | Callable[[Vector], Weights]


# --------------------------------------------------------------------------
# Pequeñas ayudas
# --------------------------------------------------------------------------


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smooth(t: float) -> float:
    """Suaviza 0..1 con entrada y salida lentas."""
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def ramp(value: float, start: float, end: float) -> float:
    """0 antes de ``start``, 1 después de ``end``, suave en medio."""
    if start == end:
        return 1.0 if value >= end else 0.0
    return smooth((value - start) / (end - start))


def blend(a: Weights, b: Weights, t: float) -> Weights:
    """Mezcla dos repartos de pesos."""
    result: Weights = {}
    for name, value in a.items():
        result[name] = result.get(name, 0.0) + value * (1.0 - t)
    for name, value in b.items():
        result[name] = result.get(name, 0.0) + value * t
    return {name: value for name, value in result.items() if value > 1e-4}


def mirror_name(name: str) -> str:
    """Nombre del hueso del otro lado (Left ↔ Right)."""
    if name.startswith("Left"):
        return "Right" + name[4:]
    if name.startswith("Right"):
        return "Left" + name[5:]
    return name


def mirror_weights(weights: Weights) -> Weights:
    return {mirror_name(name): value for name, value in weights.items()}


def table(points: Sequence[Sequence[float]], x: float) -> list[float]:
    """Interpola una tabla ``[(x, a, b, ...)]`` ordenada por x."""
    if x <= points[0][0]:
        return list(points[0][1:])
    for (x0, *a), (x1, *b) in zip(points, points[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0)
            return [lerp(va, vb, t) for va, vb in zip(a, b)]
    return list(points[-1][1:])


# --------------------------------------------------------------------------
# Esculpir: anillos, bultos y paneles con color y pesos
# --------------------------------------------------------------------------


@dataclass
class Ring:
    """Sección de un tubo: una superelipse con el frente y la espalda distintos."""

    center: Vector
    rx: float
    front: float
    back: float | None = None
    side: Vector = field(default_factory=lambda: LEFT.copy())
    forward: Vector = field(default_factory=lambda: FRONT.copy())
    power: float = 2.0
    weights: Weights | None = None
    color: str | None = None
    # Multiplicador del radio según el índice del vértice (acolchados, pelo).
    ripple: Callable[[int], float] | None = None

    def point(self, index: int, segments: int) -> Vector:
        theta = 2.0 * math.pi * index / segments
        c, s = math.cos(theta), math.sin(theta)
        e = 2.0 / self.power
        depth = self.front if s >= 0.0 else (self.front if self.back is None else self.back)
        scale = self.ripple(index) if self.ripple is not None else 1.0
        x = self.rx * math.copysign(abs(c) ** e, c) * scale
        y = depth * math.copysign(abs(s) ** e, s) * scale
        return Vector(self.center) + self.side * x + self.forward * y


def path_rings(
    points: Sequence[Vector],
    radii: Sequence[Sequence[float]],
    *,
    forward: Vector = FRONT,
    weights: Sequence[Weights | None] | None = None,
    power: float = 2.0,
    colors: Sequence[str | None] | None = None,
) -> list[Ring]:
    """Anillos a lo largo de un camino (brazos, piernas, correas redondas).

    ``radii`` da ``(rx, frente[, espalda])`` por punto. Cada anillo se orienta
    perpendicular al camino, con ``forward`` como referencia del frente.
    """
    rings = []
    count = len(points)
    for i, point in enumerate(points):
        before, after = points[max(0, i - 1)], points[min(count - 1, i + 1)]
        axis = (Vector(after) - Vector(before)).normalized()
        front = (Vector(forward) - axis * Vector(forward).dot(axis)).normalized()
        side = front.cross(axis).normalized()
        r = radii[i]
        rings.append(
            Ring(
                Vector(point), r[0], r[1], r[2] if len(r) > 2 else None, side, front, power,
                weights[i] if weights is not None else None,
                colors[i] if colors is not None else None,
            )
        )
    return rings


class Profile:
    """Volumen definido por secciones a distintas alturas (un torso, una cabeza).

    Cada fila de la tabla es ``(z, rx, frente, espalda, y del centro)``. Sirve
    para crear los anillos del volumen y, sobre todo, para colocar cosas sobre
    su superficie: correas, botones, bolsillos, solapas.

    Los ángulos se miden como en ``Ring``: 0° es el costado izquierdo del
    personaje (+X), 90° el frente y 270° la espalda.
    """

    def __init__(self, rows: Sequence[Sequence[float]], power: float = 2.0) -> None:
        self.rows = sorted(rows)
        self.power = power

    def at(self, z: float) -> tuple[float, float, float, float]:
        rx, front, back, y = table(self.rows, z)
        return rx, front, back, y

    def ring(self, z: float, inflate: float = 0.0, scale: float = 1.0, **extra) -> Ring:
        rx, front, back, y = self.at(z)
        return Ring(
            Vector((0.0, y, z)),
            (rx + inflate) * scale,
            (front + inflate) * scale,
            (back + inflate) * scale,
            power=self.power,
            **extra,
        )

    def surface(self, degrees: float, z: float, offset: float = 0.0) -> Vector:
        """Punto de la superficie, separado ``offset`` hacia fuera."""
        ring = self.ring(z, offset)
        theta = math.radians(degrees)
        c, s = math.cos(theta), math.sin(theta)
        e = 2.0 / self.power
        depth = ring.front if s >= 0.0 else ring.back
        return ring.center + LEFT * ring.rx * math.copysign(abs(c) ** e, c) + FRONT * depth * math.copysign(abs(s) ** e, s)

    def normal(self, degrees: float, z: float) -> Vector:
        """Dirección hacia fuera en ese punto (aproximada, con diferencias)."""
        step = 2.0
        around = self.surface(degrees + step, z) - self.surface(degrees - step, z)
        along = self.surface(degrees, z + 0.01) - self.surface(degrees, z - 0.01)
        normal = around.cross(along)
        if normal.length < 1e-9:
            return (self.surface(degrees, z) - Vector((0.0, self.at(z)[3], z))).normalized()
        normal.normalize()
        outward = self.surface(degrees, z) - Vector((0.0, self.at(z)[3], z))
        return normal if normal.dot(outward) >= 0.0 else -normal

    def on(self, degrees: float, z: float, offset: float = 0.0) -> tuple[Vector, Vector]:
        """``(punto, normal)``: lo que piden ``Sculpt.strap`` y las solapas."""
        return self.surface(degrees, z, offset), self.normal(degrees, z)

    def patch(
        self, degrees: Sequence[float], heights: Sequence[float], offset: float = 0.0
    ) -> tuple[list[list[Vector]], list[list[Vector]]]:
        """Rejilla de puntos y normales sobre la superficie (para ``Sculpt.panel``)."""
        grid = [[self.surface(d, z, offset) for d in degrees] for z in heights]
        normals = [[self.normal(d, z) for d in degrees] for z in heights]
        return grid, normals


def spread(start: float, end: float, count: int) -> list[float]:
    """``count`` valores repartidos entre ``start`` y ``end``, ambos incluidos."""
    return [lerp(start, end, i / (count - 1)) for i in range(count)]


def tint(
    obj: bpy.types.Object, center: Iterable[float], radius: float, hex_color: str, amount: float = 0.5
) -> None:
    """Mancha suave de color alrededor de un punto (mejillas, nariz, rodilleras)."""
    import tumansk_bpy as tb

    layer = obj.data.color_attributes.get("Base")
    if layer is None:
        raise ValueError(f"{obj.name} no tiene colores base")
    target = Vector(tb.hex_to_linear(hex_color))
    c = Vector(center)
    for loop in obj.data.loops:
        distance = (obj.data.vertices[loop.vertex_index].co - c).length
        if distance < radius:
            weight = amount * 0.5 * (1.0 + math.cos(math.pi * distance / radius))
            color = Vector(layer.data[loop.index].color[:3]).lerp(target, weight)
            layer.data[loop.index].color = (*color, 1.0)


def grime(
    obj: bpy.types.Object,
    low: float,
    high: float,
    hex_color: str,
    amount: float = 0.6,
    *,
    scale: float = 9.0,
    seed: int = 0,
) -> None:
    """Suciedad que sube desde abajo: barro en las botas y en los bajos.

    Entre ``low`` y ``high`` (alturas) la mancha se desvanece, con el borde
    roto por un ruido para que no parezca un degradado.
    """
    import tumansk_bpy as tb
    from mathutils import noise

    layer = obj.data.color_attributes.get("Base")
    if layer is None:
        raise ValueError(f"{obj.name} no tiene colores base")
    target = Vector(tb.hex_to_linear(hex_color))
    offset = Vector((seed * 2.3, seed * 5.1, seed * 1.9))
    for loop in obj.data.loops:
        co = obj.data.vertices[loop.vertex_index].co
        ragged = 0.35 * noise.noise(co * scale + offset)
        weight = amount * smooth(1.0 - (co.z - low) / max(high - low, 1e-4) + ragged)
        if weight > 0.0:
            color = Vector(layer.data[loop.index].color[:3]).lerp(target, weight)
            layer.data[loop.index].color = (*color, 1.0)


def bump(value: float, center: float, width: float) -> float:
    """Campana de anchura ``width`` alrededor de ``center`` (para modelar relieves)."""
    return math.exp(-(((value - center) / width) ** 2))


class Sculpt:
    """Malla de un personaje: piezas con color base y pesos de hueso.

    Igual que ``tumansk_bpy.MeshBuilder``, el color de cada pieza se guarda en
    el atributo "Base" y ``tumansk_bpy.paint`` lo usa después como punto de
    partida. Los pesos van en la capa de deformación, por vértice.
    """

    def __init__(self, bones: Sequence[str], seed: int = 0) -> None:
        self.bm = bmesh.new()
        self.base = self.bm.loops.layers.color.new("Base")
        self.deform = self.bm.verts.layers.deform.verify()
        self.bones = list(bones)
        self.index = {name: i for i, name in enumerate(self.bones)}
        self.rng = random.Random(seed)

    # -- interno -----------------------------------------------------------

    def _vert(self, co: Vector, weights: WeightSpec | None) -> bmesh.types.BMVert:
        vert = self.bm.verts.new(co)
        self._weigh(vert, weights)
        return vert

    def _weigh(self, vert: bmesh.types.BMVert, weights: WeightSpec | None) -> None:
        if weights is None:
            return
        values = weights(vert.co) if callable(weights) else weights
        total = sum(values.values())
        if total <= 0.0:
            raise ValueError("Una pieza del personaje se ha quedado sin pesos")
        for name, value in values.items():
            if value > 0.0:
                vert[self.deform][self.index[name]] = value / total

    def _paint(self, faces: Iterable[bmesh.types.BMFace], color: str, jitter: float = 0.0) -> None:
        # Las capas de color de bmesh guardan sRGB (no lineal).
        value = color.lstrip("#")
        srgb = Vector(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        if jitter > 0.0:
            srgb *= 1.0 + self.rng.uniform(-jitter, jitter)
        rgba = (min(1.0, srgb.x), min(1.0, srgb.y), min(1.0, srgb.z), 1.0)
        for face in faces:
            face.smooth = True
            for loop in face.loops:
                loop[self.base] = rgba

    def _orient(self, faces: list[bmesh.types.BMFace]) -> None:
        """Deja las caras de una pieza mirando hacia fuera."""
        if not faces:
            return
        for face in faces:
            face.normal_update()
        center = Vector((0.0, 0.0, 0.0))
        for face in faces:
            center += face.calc_center_median()
        center /= len(faces)
        outward = sum((f.calc_center_median() - center).dot(f.normal) * f.calc_area() for f in faces)
        if outward < 0.0:
            bmesh.ops.reverse_faces(self.bm, faces=faces)

    # -- piezas ------------------------------------------------------------

    def tube(
        self,
        rings: Sequence[Ring],
        color: str,
        *,
        segments: int = 12,
        weights: WeightSpec | None = None,
        cap_start: float | None = 0.0,
        cap_end: float | None = 0.0,
        closed: bool = False,
        jitter: float = 0.0,
    ) -> list[bmesh.types.BMFace]:
        """Tubo que pasa por los anillos.

        ``cap_start`` y ``cap_end`` cierran los extremos con un polo desplazado
        esa distancia hacia fuera (``None`` los deja abiertos). ``closed`` une
        el último anillo con el primero (bufandas, cinturones, rosquillas).
        """
        loops: list[list[bmesh.types.BMVert]] = []
        for ring in rings:
            ring_weights = ring.weights if ring.weights is not None else weights
            loops.append([self._vert(ring.point(i, segments), ring_weights) for i in range(segments)])
        faces: list[bmesh.types.BMFace] = []
        pairs = list(zip(range(len(loops) - 1), range(1, len(loops))))
        if closed:
            pairs.append((len(loops) - 1, 0))
        for a, b in pairs:
            band = [
                self.bm.faces.new(
                    (loops[a][i], loops[a][(i + 1) % segments], loops[b][(i + 1) % segments], loops[b][i])
                )
                for i in range(segments)
            ]
            self._paint(band, rings[a].color or color, jitter)
            faces.extend(band)
        if not closed:
            for bulge, loop, ring, neighbour in (
                (cap_start, loops[0], rings[0], rings[1]),
                (cap_end, loops[-1], rings[-1], rings[-2]),
            ):
                if bulge is None:
                    continue
                axis = Vector(ring.center) - Vector(neighbour.center)
                axis = axis.normalized() if axis.length > 1e-6 else ring.side.cross(ring.forward)
                ring_weights = ring.weights if ring.weights is not None else weights
                pole = self._vert(Vector(ring.center) + axis * bulge, ring_weights)
                fan = [
                    self.bm.faces.new((loop[i], loop[(i + 1) % segments], pole)) for i in range(segments)
                ]
                # El abanico hereda el sentido del tubo: se corrige con toda la pieza.
                if loop is loops[0]:
                    bmesh.ops.reverse_faces(self.bm, faces=fan)
                self._paint(fan, ring.color or color, jitter)
                faces.extend(fan)
        self._orient(faces)
        return faces

    def blob(
        self,
        center: Iterable[float],
        radii: Iterable[float],
        color: str,
        weights: WeightSpec,
        *,
        rotation: Quaternion | None = None,
        segments: int = 10,
        rings: int = 5,
        jitter: float = 0.0,
    ) -> list[bmesh.types.BMFace]:
        """Bulto redondeado (un elipsoide)."""
        c, r = Vector(center), Vector(radii)
        q = rotation or Quaternion()
        side, forward, axis = q @ LEFT, q @ FRONT, q @ UP
        sections = []
        for k in range(1, rings + 1):
            phi = math.pi * k / (rings + 1)
            w = math.sin(phi)
            sections.append(Ring(c - axis * r.z * math.cos(phi), r.x * w, r.y * w, None, side, forward))
        pole = r.z * (1.0 - math.cos(math.pi / (rings + 1)))
        return self.tube(
            sections, color, segments=segments, weights=weights, cap_start=pole, cap_end=pole, jitter=jitter
        )

    def panel(
        self,
        grid: Sequence[Sequence[Vector]],
        thickness: float,
        color: str,
        weights: WeightSpec,
        *,
        normals: Sequence[Sequence[Vector]] | None = None,
        inner_color: str | None = None,
        rim_color: str | None = None,
        jitter: float = 0.0,
    ) -> list[bmesh.types.BMFace]:
        """Lámina con grosor que sigue una rejilla de puntos (solapas, correas, faldones).

        ``normals`` da la dirección "hacia fuera" en cada punto; si falta, se
        calcula con la propia rejilla. La cara de dentro y el canto pueden
        llevar otro color (el forro de piel de una orejera).
        """
        rows, cols = len(grid), len(grid[0])

        def normal(i: int, j: int) -> Vector:
            if normals is not None:
                return Vector(normals[i][j]).normalized()
            du = Vector(grid[min(rows - 1, i + 1)][j]) - Vector(grid[max(0, i - 1)][j])
            dv = Vector(grid[i][min(cols - 1, j + 1)]) - Vector(grid[i][max(0, j - 1)])
            return du.cross(dv).normalized()

        outer = [[None] * cols for _ in range(rows)]
        inner = [[None] * cols for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                n = normal(i, j)
                outer[i][j] = self._vert(Vector(grid[i][j]) + n * thickness * 0.5, weights)
                inner[i][j] = self._vert(Vector(grid[i][j]) - n * thickness * 0.5, weights)
        front, back, rim = [], [], []
        for i in range(rows - 1):
            for j in range(cols - 1):
                front.append(self.bm.faces.new((outer[i][j], outer[i + 1][j], outer[i + 1][j + 1], outer[i][j + 1])))
                back.append(self.bm.faces.new((inner[i][j], inner[i][j + 1], inner[i + 1][j + 1], inner[i + 1][j])))
        border = (
            [(i, 0) for i in range(rows)]
            + [(rows - 1, j) for j in range(1, cols)]
            + [(i, cols - 1) for i in range(rows - 2, -1, -1)]
            + [(0, j) for j in range(cols - 2, 0, -1)]
        )
        for (i0, j0), (i1, j1) in zip(border, border[1:] + border[:1]):
            rim.append(self.bm.faces.new((outer[i0][j0], inner[i0][j0], inner[i1][j1], outer[i1][j1])))
        self._paint(front, color, jitter)
        self._paint(back, inner_color or color, jitter)
        self._paint(rim, rim_color or color, jitter)
        faces = front + back + rim
        self._orient(faces)
        return faces

    def strap(
        self,
        path: Sequence[tuple[Vector, Vector]],
        width: float,
        thickness: float,
        color: str,
        weights: WeightSpec,
        *,
        columns: int = 2,
        jitter: float = 0.0,
    ) -> list[bmesh.types.BMFace]:
        """Correa plana que sigue un camino de ``(punto, normal hacia fuera)``."""
        grid, normals = [], []
        for i, (point, normal) in enumerate(path):
            before, after = path[max(0, i - 1)][0], path[min(len(path) - 1, i + 1)][0]
            tangent = (Vector(after) - Vector(before)).normalized()
            across = tangent.cross(Vector(normal)).normalized()
            grid.append(
                [Vector(point) + across * width * (j / (columns - 1) - 0.5) for j in range(columns)]
            )
            normals.append([Vector(normal)] * columns)
        return self.panel(grid, thickness, color, weights, normals=normals, jitter=jitter)

    def box(
        self,
        size: Iterable[float],
        center: Iterable[float],
        color: str,
        weights: WeightSpec,
        *,
        rotation: Quaternion | None = None,
        bevel: float = 0.0,
        cuts: int = 0,
        jitter: float = 0.0,
    ) -> list[bmesh.types.BMFace]:
        """Caja (hebillas, mochilas, botones cuadrados). Con ``cuts`` se puede deformar."""
        before_faces, before_verts = set(self.bm.faces), set(self.bm.verts)
        matrix = Matrix.LocRotScale(Vector(center), rotation or Quaternion(), Vector(size))
        result = bmesh.ops.create_cube(self.bm, size=1.0, matrix=matrix)
        if cuts > 0:
            edges = list({edge for vert in result["verts"] for edge in vert.link_edges})
            bmesh.ops.subdivide_edges(self.bm, edges=edges, cuts=cuts, use_grid_fill=True)
        if bevel > 0.0:
            self.bm.normal_update()
            edges = [
                edge
                for edge in {e for f in self.bm.faces if f not in before_faces for e in f.edges}
                if len(edge.link_faces) == 2 and edge.calc_face_angle(0.0) > 0.5
            ]
            bmesh.ops.bevel(self.bm, geom=edges, offset=bevel, segments=1, profile=0.5, affect="EDGES")
        for vert in self.bm.verts:
            if vert not in before_verts:
                self._weigh(vert, weights)
        faces = [f for f in self.bm.faces if f not in before_faces]
        self._paint(faces, color, jitter)
        return faces

    def move(self, faces: Iterable[bmesh.types.BMFace], offset: Callable[[Vector], Vector]) -> None:
        """Desplaza los vértices de unas caras (abombar, arrugar)."""
        for vert in {v for f in faces for v in f.verts}:
            vert.co += offset(vert.co)

    # -- final -------------------------------------------------------------

    def finish(
        self,
        name: str,
        mat: bpy.types.Material | None,
        parent: bpy.types.Object | None,
        *,
        subdivide: int = 1,
    ) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        if mat is not None:
            mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        for bone in self.bones:
            obj.vertex_groups.new(name=bone)
        if subdivide > 0:
            modifier = obj.modifiers.new("suavizado", "SUBSURF")
            modifier.levels = subdivide
            depsgraph = bpy.context.evaluated_depsgraph_get()
            smoothed = bpy.data.meshes.new_from_object(
                obj.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph
            )
            obj.modifiers.clear()
            old = obj.data
            obj.data = smoothed
            smoothed.name = name
            bpy.data.meshes.remove(old)
        obj.data.shade_smooth()
        _limit_weights(obj)
        obj.parent = parent
        return obj


def _limit_weights(obj: bpy.types.Object, limit: int = 4) -> None:
    """Como mucho ``limit`` huesos por vértice, y que sumen 1 (lo que espera Godot)."""
    groups = obj.vertex_groups
    for vert in obj.data.vertices:
        influences = sorted(((g.weight, g.group) for g in vert.groups), reverse=True)
        keep = [(w, g) for w, g in influences[:limit] if w > 1e-4]
        for _, group in influences:
            groups[group].remove([vert.index])
        total = sum(w for w, _ in keep)
        if total <= 0.0:
            raise ValueError(f"{obj.name}: el vértice {vert.index} no tiene pesos")
        for weight, group in keep:
            groups[group].add([vert.index], weight / total, "REPLACE")


def bvh_of(objects: Iterable[bpy.types.Object]) -> BVHTree:
    """Árbol para lanzar rayos contra unas mallas (pegar cosas a su superficie)."""
    vertices: list[Vector] = []
    polygons: list[tuple[int, ...]] = []
    for obj in objects:
        start = len(vertices)
        vertices.extend(obj.matrix_world @ v.co for v in obj.data.vertices)
        polygons.extend(tuple(start + i for i in p.vertices) for p in obj.data.polygons)
    return BVHTree.FromPolygons(vertices, polygons)


def sticker(
    name: str,
    grid: Sequence[Sequence[tuple[Vector, Vector]]],
    surface: BVHTree,
    bone: str,
    mat: bpy.types.Material,
    parent: bpy.types.Object,
    *,
    lift: float = 0.0015,
) -> bpy.types.Object:
    """Pegatina 2D sobre una superficie 3D (la cara dibujada).

    ``grid`` es una rejilla de rayos ``(origen, dirección)``; cada uno se lanza
    contra ``surface`` y la pegatina queda a ``lift`` de donde toca. Las UV
    recorren la rejilla de 0 a 1 (U a lo ancho, V de arriba abajo).
    """
    rows, cols = len(grid), len(grid[0])
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    deform = bm.verts.layers.deform.verify()
    verts = []
    for row in grid:
        line = []
        for origin, direction in row:
            hit, normal, _, _ = surface.ray_cast(origin, direction.normalized())
            if hit is None:
                raise ValueError(f"{name}: un rayo de la pegatina no toca la superficie")
            vert = bm.verts.new(hit + normal * lift)
            vert[deform][0] = 1.0
            line.append(vert)
        verts.append(line)
    for i in range(rows - 1):
        for j in range(cols - 1):
            corners = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            face = bm.faces.new([verts[a][b] for a, b in corners])
            face.smooth = True
            for loop, (a, b) in zip(face.loops, corners):
                loop[uv_layer].uv = (b / (cols - 1), 1.0 - a / (rows - 1))
    bm.normal_update()
    center = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    origin_hint = Vector(grid[rows // 2][cols // 2][0])
    if sum(f.normal.dot(origin_hint - center) for f in bm.faces) < 0.0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.vertex_groups.new(name=bone)
    obj.parent = parent
    return obj


# --------------------------------------------------------------------------
# Esqueleto
# --------------------------------------------------------------------------


@dataclass
class BoneSpec:
    name: str
    parent: str | None
    head: Vector
    tail: Vector


def build_armature(name: str, bones: Sequence[BoneSpec], parent: bpy.types.Object | None) -> bpy.types.Object:
    data = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for spec in bones:
        bone = data.edit_bones.new(spec.name)
        bone.head, bone.tail = Vector(spec.head), Vector(spec.tail)
        bone.use_connect = False
        if spec.parent is not None:
            bone.parent = data.edit_bones[spec.parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return obj


def bind(objects: Iterable[bpy.types.Object], armature: bpy.types.Object) -> None:
    """Cuelga las mallas del esqueleto, que pasa a deformarlas."""
    for obj in objects:
        obj.parent = armature
        modifier = obj.modifiers.new("esqueleto", "ARMATURE")
        modifier.object = armature


# --------------------------------------------------------------------------
# Poses y animación
# --------------------------------------------------------------------------


def aim(rest_dir: Vector, rest_up: Vector, direction: Vector, up: Vector) -> Quaternion:
    """Giro que lleva ``rest_dir`` a ``direction`` y deja ``rest_up`` lo más cerca de ``up``."""
    direction = direction.normalized()
    first = rest_dir.normalized().rotation_difference(direction)
    current = first @ rest_up
    current = (current - direction * current.dot(direction))
    wanted = up - direction * up.dot(direction)
    if current.length < 1e-6 or wanted.length < 1e-6:
        return first
    twist_angle = current.normalized().angle(wanted.normalized())
    if current.cross(wanted).dot(direction) < 0.0:
        twist_angle = -twist_angle
    return Quaternion(direction, twist_angle) @ first


class Rig:
    """Lo que hace falta del esqueleto en reposo para calcular poses."""

    def __init__(self, armature: bpy.types.Object) -> None:
        self.armature = armature
        bones = armature.data.bones
        self.names = [bone.name for bone in bones]
        self.parent = {bone.name: (bone.parent.name if bone.parent else None) for bone in bones}
        self.head = {bone.name: bone.head_local.copy() for bone in bones}
        self.tail = {bone.name: bone.tail_local.copy() for bone in bones}
        self.rest = {bone.name: bone.matrix_local.to_quaternion() for bone in bones}

    def direction(self, bone: str) -> Vector:
        return (self.tail[bone] - self.head[bone]).normalized()

    def length(self, bone: str) -> float:
        return (self.tail[bone] - self.head[bone]).length


class Pose:
    """Una pose: giros por hueso, descritos en los ejes del personaje en reposo.

    ``turn("LeftUpperLeg", LEFT, 20)`` levanta el muslo 20° alrededor del eje
    lateral, sin tener que pensar en los ejes locales de cada hueso. El giro de
    un hueso arrastra a sus hijos.
    """

    def __init__(self, rig: Rig) -> None:
        self.rig = rig
        self.rotation: dict[str, Quaternion] = {}
        self.offset: dict[str, Vector] = {}

    def turn(self, bone: str, axis: Vector, degrees: float) -> "Pose":
        delta = Quaternion(axis.normalized(), math.radians(degrees))
        self.rotation[bone] = delta @ self.rotation.get(bone, Quaternion())
        return self

    def set(self, bone: str, rotation: Quaternion) -> "Pose":
        self.rotation[bone] = rotation
        return self

    def move(self, bone: str, offset: Vector) -> "Pose":
        self.offset[bone] = self.offset.get(bone, Vector()) + Vector(offset)
        return self

    def accumulated(self, bone: str | None) -> Quaternion:
        """Giro total que llega a un hueso (el suyo y el de sus antepasados)."""
        if bone is None:
            return Quaternion()
        return self.accumulated(self.rig.parent[bone]) @ self.rotation.get(bone, Quaternion())

    def head(self, bone: str) -> Vector:
        """Posición de la cabeza de un hueso con la pose aplicada."""
        parent = self.rig.parent[bone]
        offset = self.offset.get(bone, Vector())
        if parent is None:
            return self.rig.head[bone] + offset
        relative = self.rig.head[bone] - self.rig.head[parent]
        return self.head(parent) + self.accumulated(parent) @ (relative + offset)

    def tail(self, bone: str) -> Vector:
        return self.head(bone) + self.accumulated(bone) @ (self.rig.tail[bone] - self.rig.head[bone])

    def point_at(self, bone: str, direction: Vector, up: Vector | None = None, rest_up: Vector | None = None) -> "Pose":
        """Orienta un hueso hacia ``direction`` (en el espacio del personaje)."""
        parent_total = self.accumulated(self.rig.parent[bone])
        local = parent_total.inverted() @ direction.normalized()
        if up is None or rest_up is None:
            self.rotation[bone] = self.rig.direction(bone).rotation_difference(local)
        else:
            self.rotation[bone] = aim(self.rig.direction(bone), rest_up, local, parent_total.inverted() @ up)
        return self

    def reach(self, upper: str, lower: str, target: Vector, pole: Vector) -> "Pose":
        """Cinemática inversa de dos huesos: la punta de ``lower`` va a ``target``.

        ``pole`` es hacia dónde apunta la articulación (la rodilla, hacia
        delante; el codo, hacia atrás y afuera).
        """
        origin = self.head(upper)
        a, b = self.rig.length(upper), self.rig.length(lower)
        to_target = Vector(target) - origin
        distance = min(max(to_target.length, abs(a - b) + 1e-4), a + b - 1e-4)
        axis = to_target.normalized()
        along = (a * a - b * b + distance * distance) / (2.0 * distance)
        height = math.sqrt(max(0.0, a * a - along * along))
        bend = Vector(pole) - axis * Vector(pole).dot(axis)
        bend = bend.normalized() if bend.length > 1e-6 else axis.orthogonal().normalized()
        joint = origin + axis * along + bend * height
        self.point_at(upper, joint - origin)
        self.point_at(lower, origin + axis * distance - joint)
        return self

    def hold(self, bone: str, rotation: Quaternion) -> "Pose":
        """Fija la orientación total de un hueso, hagan lo que hagan sus padres."""
        self.rotation[bone] = self.accumulated(self.rig.parent[bone]).inverted() @ rotation
        return self


def apply_pose(pose: Pose) -> None:
    """Pasa la pose a los huesos de Blender."""
    rig = pose.rig
    for bone in rig.armature.pose.bones:
        rest = rig.rest[bone.name]
        delta = pose.rotation.get(bone.name, Quaternion())
        bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = rest.inverted() @ delta @ rest
        # El desplazamiento se da en ejes del personaje; Blender lo quiere en los del hueso.
        offset = pose.offset.get(bone.name)
        bone.location = (0.0, 0.0, 0.0) if offset is None else rest.inverted() @ offset


def bake_action(
    rig: Rig,
    name: str,
    duration: float,
    sample: Callable[[float], Pose],
    *,
    fps: int = 24,
    moving: Iterable[str] = (),
) -> bpy.types.Action:
    """Muestrea ``sample(t)`` (t de 0 a 1) y lo guarda como una acción.

    Los nombres que acaban en ``-loop`` se importan en Godot en bucle; para que
    el bucle cierre, ``sample(0)`` y ``sample(1)`` deben dar la misma pose.
    ``moving`` son los huesos que además se desplazan.
    """
    armature = rig.armature
    if armature.animation_data is None:
        armature.animation_data_create()
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    armature.animation_data.action = action
    frames = max(1, round(duration * fps))
    moving = set(moving)
    previous: dict[str, Quaternion] = {}
    for frame in range(frames + 1):
        apply_pose(sample(frame / frames))
        for bone in armature.pose.bones:
            # Signo continuo: evita que la interpolación dé la vuelta larga.
            q = bone.rotation_quaternion.copy()
            if bone.name in previous and previous[bone.name].dot(q) < 0.0:
                q.negate()
                bone.rotation_quaternion = q
            previous[bone.name] = q
            bone.keyframe_insert("rotation_quaternion", frame=frame)
            if bone.name in moving:
                bone.keyframe_insert("location", frame=frame)
    # Cada acción va a su pista para que el exportador las saque todas.
    track = armature.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 0, action)
    armature.animation_data.action = None
    apply_pose(Pose(rig))
    return action
