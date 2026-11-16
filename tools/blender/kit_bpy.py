"""Utilidades del kit de arquitectura de Tumansk (F3-16).

Los edificios no se exportan enteros: cada familia (bloques de paneles,
casas estalinistas...) es una biblioteca de piezas, un .glb con una malla por
pieza. Godot monta cada edificio del plano con ellas
(scripts/surface/building_kit.gd).

Convenciones de una pieza (coordenadas de Blender):

- El origen es el arranque de un vano en la cara exterior del muro: x corre a
  lo largo de la fachada (de izquierda a derecha, vista desde fuera), z hacia
  arriba (z = 0 es el suelo de la planta) y el muro va de y = 0 hacia +y. Lo
  que sobresale (balcones, alféizares, cornisas) queda en y < 0. En Godot, x
  sigue igual, y es la altura y la fachada mira hacia +z.
- Cada pieza se pinta con la oclusión de su contexto: las piezas que tendrá
  alrededor al montarla (los paneles vecinos, el forjado, el balcón de arriba).
  El contexto no se exporta.
- Las piezas llevan varios materiales: "muro" (y sus variantes de estuco o
  ladrillo, con suciedad y hollín en el shader), "nevado" (lo que coge nieve),
  "vidrio", "metal" e "interior" (sin nieve: el falso interior detrás de los
  huecos).
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Iterable, Sequence

import bpy
from mathutils import Matrix, Vector

import tumansk_bpy as tb

# Carpinterías y cristal
FRAME = "#A9A291"
FRAME_WOOD = "#5A4432"
SASH_SHADOW = "#57524A"
CHAR = "#151312"
SOOT = "#1E1B19"
GLASS = "#1F2228"
CURTAINS = ("#8A8170", "#7A6262", "#6F7468", "#8C7E62")
PLANKS = ("#6B5844", "#5A4432", "#7A6650", "#4E3D2E")
FILM = "#7B7D77"
# Metal
METAL = "#40464A"
GALVANIZED = "#7C807F"
RUST = "#7E4128"
REBAR = "#4A3426"
# Interiores (casi negros: el post-proceso los vuelve tinta, como en un grabado)
ROOM_FLOOR = "#1C1915"
ROOM_CEILING = "#2E2A26"
WALLPAPERS = ("#3A392D", "#3B3034", "#2E3537", "#3F3629")
SILL_INSIDE = "#6E6A60"


# --------------------------------------------------------------------------
# La biblioteca
# --------------------------------------------------------------------------


class KitLibrary:
    """Biblioteca de piezas: la raíz y sus piezas, puestas en rejilla para mirarlas.

    Godot no usa esa posición: el ensamblador coloca cada pieza con su
    transformación.
    """

    def __init__(self, name: str, columns: int = 12, spacing: float = 7.0) -> None:
        self.root = tb.empty(name)
        self.columns = columns
        self.spacing = spacing
        self.pieces: list[bpy.types.Object] = []

    def add(
        self,
        piece: bpy.types.Object,
        context: Sequence[bpy.types.Object] = (),
        *,
        alpha: Callable[[Vector, Vector], float] = lambda position, normal: 0.0,
        samples: int = 12,
        ao: float = 0.5,
        ao_distance: float = 0.6,
        cavity_dark: float = 0.3,
        edge_light: float = 0.12,
        mottling: float = 0.05,
        ground_z: float | None = None,
        seed: int = 0,
    ) -> bpy.types.Object:
        """Pinta la pieza con la oclusión de su contexto, borra el contexto y la guarda.

        ``alpha(posición, normal)`` es la máscara que leen los shaders de muro (por
        defecto, 0: nada de plaqueta ni de revoque caído).
        """
        if piece.name in {p.name for p in self.pieces}:
            raise ValueError(f"Pieza repetida: {piece.name}")
        tb.paint(
            {piece: None},
            occluders=[piece, *context],
            samples=samples,
            ao=ao,
            ao_distance=ao_distance,
            cavity_dark=cavity_dark,
            edge_light=edge_light,
            mottling=mottling,
            ground_z=ground_z,
            seed=seed,
        )
        tb.set_alpha(piece, alpha)
        remove(context)
        index = len(self.pieces)
        piece.parent = self.root
        piece.location = ((index % self.columns) * self.spacing, (index // self.columns) * self.spacing, 0.0)
        self.pieces.append(piece)
        return piece


def facade_faces(position: Vector, normal: Vector) -> float:
    """Máscara de las caras de fachada (las que miran a la calle en y = 0): la plaqueta
    de los paneles va ahí y no en las mochetas ni en las juntas."""
    return 1.0 if normal.y < -0.9 and position.y < 0.004 else 0.0


def drip_cuts(drips: Iterable[tuple[float, float, float, float]]) -> list[float]:
    """Los cortes verticales que necesita un muro para pintar sus chorretones estrechos:
    los dos bordes de cada uno y, un poco más fuera, donde ya no hay mancha."""
    cuts = []
    for x, _, width, _ in drips:
        cuts += [x - width / 2.0 - 0.025, x - width / 2.0, x + width / 2.0, x + width / 2.0 + 0.025]
    return cuts


def drips(
    obj: bpy.types.Object,
    sources: Iterable[tuple[float, float, float, float]],
    color: str = "#4E4740",
    strength: float = 0.5,
) -> None:
    """Chorretones de óxido y suciedad pintados en el color base de la cara exterior.

    Cada uno es ``(x, z, ancho, largo)``: baja desde (x, z) y se desvanece. El muro
    tiene que tener los cortes de :func:`drip_cuts` para que la mancha sea estrecha.
    """
    mesh = obj.data
    layer = mesh.color_attributes.get("Base")
    target = Vector(tb.hex_to_linear(color))
    sources = list(sources)
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        if co.y > 0.005:
            continue
        weight = 0.0
        for x, z, width, length in sources:
            if abs(co.x - x) <= width / 2.0 + 1e-4 and z - length <= co.z <= z + 1e-4:
                weight = max(weight, (1.0 - (z - co.z) / length) ** 0.8)
        if weight > 0.0:
            base = Vector(layer.data[loop.index].color[:3])
            layer.data[loop.index].color = (*base.lerp(target, weight * strength), 1.0)


def remove(objects: Iterable[bpy.types.Object]) -> None:
    """Borra objetos auxiliares (el contexto de una pieza) con sus mallas."""
    for obj in objects:
        mesh = obj.data
        bpy.data.objects.remove(obj)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def materials(*names: str) -> list[bpy.types.Material]:
    """Los materiales de una pieza, en el orden de sus ``MeshBuilder.material(n)``."""
    return [tb.material(name, "#808080") for name in names]


# --------------------------------------------------------------------------
# Geometría auxiliar
# --------------------------------------------------------------------------


def ccw(outline: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """El contorno en sentido antihorario (como lo quiere ``MeshBuilder.prism``)."""
    points = list(outline)
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))
    return points if area > 0.0 else points[::-1]


def transform_faces(faces: Iterable, matrix: Matrix) -> None:
    """Mueve unas caras ya creadas (una hoja abierta, un balcón caído)."""
    for vert in dict.fromkeys(v for f in faces for v in f.verts):
        vert.co = matrix @ vert.co


def hinge(point: Iterable[float], axis: str, angle: float) -> Matrix:
    """Giro de ``angle`` grados alrededor de un eje (``"X"``, ``"Y"`` o ``"Z"``) que pasa por ``point``."""
    p = Vector(point)
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(angle), 4, axis) @ Matrix.Translation(-p)


def room(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    z_range: tuple[float, float],
    y_range: tuple[float, float],
    wallpaper: str,
    *,
    cuts: int = 2,
) -> list:
    """Caja de habitación vista desde dentro: fondo, suelo, techo y paredes, sin la cara
    de la ventana. Es el falso interior que se ve por los huecos."""
    (x0, x1), (z0, z1), (y0, y1) = x_range, z_range, y_range
    faces = []
    faces += mb.quad(((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)), wallpaper, cuts=cuts)
    faces += mb.quad(((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)), ROOM_FLOOR, cuts=cuts)
    faces += mb.quad(((x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)), ROOM_CEILING, cuts=cuts)
    faces += mb.quad(((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)), wallpaper, cuts=cuts)
    faces += mb.quad(((x1, y1, z0), (x1, y0, z0), (x1, y0, z1), (x1, y1, z1)), wallpaper, cuts=cuts)
    return faces


def rebar(
    mb: tb.MeshBuilder,
    start: Iterable[float],
    direction: Iterable[float],
    length: float,
    rng: random.Random,
    *,
    radius: float = 0.008,
) -> None:
    """Una varilla de la armadura que asoma de un hormigón roto, doblada a mitad."""
    a = Vector(start)
    d = Vector(direction).normalized()
    bend = d.orthogonal().normalized()
    bend.rotate(Matrix.Rotation(rng.uniform(0.0, math.tau), 3, d))
    mid = a + d * length * rng.uniform(0.35, 0.6)
    end = mid + (d + bend * rng.uniform(0.2, 0.9)).normalized() * length * rng.uniform(0.3, 0.6)
    mb.tube(tb.smooth_path([a, mid, end], steps=2), radius, REBAR, segments=4)


def broken_edge(
    x0: float,
    x1: float,
    low: float,
    high: float,
    rng: random.Random,
    *,
    step: float = 0.22,
) -> list[tuple[float, float]]:
    """Puntos de un borde roto entre x0 y x1 (de izquierda a derecha), con alturas
    entre ``low`` y ``high``: dientes de hormigón, nunca una línea recta."""
    count = max(2, round((x1 - x0) / step))
    points = []
    height = rng.uniform(low, high)
    for k in range(count + 1):
        x = x0 + (x1 - x0) * k / count
        height = min(high, max(low, height + rng.uniform(-1.0, 1.0) * (high - low) * 0.45))
        points.append((x, height))
    return points


def broken_slab(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    z_bottom: float,
    top: Sequence[tuple[float, float]],
    y_range: tuple[float, float],
    color: str,
    *,
    jitter: float = 0.05,
) -> list:
    """Placa de muro con el borde de arriba roto (``top``: puntos de :func:`broken_edge`).

    Es un prisma: el contorno (x, z) se extruye a lo largo de y.
    """
    x0, x1 = x_range
    outline = [(x0, z_bottom), (x1, z_bottom), *[(x, z) for x, z in reversed(top)]]
    if abs(top[-1][0] - x1) > 1e-6:
        outline.insert(2, (x1, top[-1][1]))
    if abs(top[0][0] - x0) > 1e-6:
        outline.append((x0, top[0][1]))
    y0, y1 = y_range
    return mb.prism(
        outline, y1 - y0, (0.0, (y0 + y1) / 2.0, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=jitter
    )


def chunk(mb: tb.MeshBuilder, center: Iterable[float], size: float, color: str, rng: random.Random) -> None:
    """Un cascote: trozo de hormigón o de ladrillo, girado al azar."""
    mb.box(
        (size * rng.uniform(0.8, 1.6), size * rng.uniform(0.6, 1.2), size * rng.uniform(0.35, 0.8)),
        center,
        color,
        rotation=(rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(0, 180)),
        bevel=min(0.02, size * 0.1),
        jitter=0.08,
    )


def corrugated(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    y: float,
    z_range: tuple[float, float],
    color: str,
    *,
    pitch: float = 0.14,
    depth: float = 0.018,
    thickness: float = 0.007,
    jitter: float = 0.0,
) -> list:
    """Chapa ondulada (de fibrocemento o de acero) de pie, con las ondas en vertical.

    Las ondas se sombrean suaves: así el contorno de tinta no dibuja una raya en cada
    una (de lejos se volverían una mancha negra) y la luz las marca con suavidad.
    """
    x0, x1 = x_range
    z0, z1 = z_range
    waves = max(1, round((x1 - x0) / pitch))
    front = []
    for k in range(waves * 4 + 1):
        x = x0 + (x1 - x0) * k / (waves * 4)
        front.append((x, y - depth * 0.5 * math.sin(k * math.pi / 2.0)))
    back = [(x, yy + thickness) for x, yy in reversed(front)]
    # El contorno va en (x, y) y se extruye en z: queda de pie sin girar.
    faces = mb.prism(front + back, z1 - z0, (0.0, 0.0, (z0 + z1) / 2.0), color, jitter=jitter)
    caps = []
    for face in faces:
        face.normal_update()
        if abs(face.normal.z) > 0.9:
            caps.append(face)
        else:
            face.smooth = True
    for cap in caps:
        for edge in cap.edges:
            edge.smooth = False
    return faces


def planks(
    mb: tb.MeshBuilder,
    opening: tuple[float, float, float, float],
    y: float,
    rng: random.Random,
    *,
    count: int | None = None,
    overhang: float = 0.16,
) -> None:
    """Tablones clavados sobre un hueco, torcidos, con huecos entre ellos."""
    x0, z0, x1, z1 = opening
    count = count or max(2, round((z1 - z0) / 0.36))
    for k in range(count):
        z = z0 + (z1 - z0) * (k + 0.5) / count + rng.uniform(-0.05, 0.05)
        width = rng.uniform(0.11, 0.2)
        mb.box(
            (x1 - x0 + overhang * 2.0 + rng.uniform(-0.05, 0.08), 0.03, width),
            ((x0 + x1) / 2.0 + rng.uniform(-0.04, 0.04), y - 0.015 - 0.032 * (k % 2), z),
            rng.choice(PLANKS),
            rotation=(0.0, rng.uniform(-13.0, 13.0), 0.0),
            bevel=0.006,
            jitter=0.1,
        )


def railing(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    y: float,
    z_range: tuple[float, float],
    color: str,
    *,
    bars: float = 0.24,
    post: float = 0.04,
) -> None:
    """Barandilla de acero soldado: postes, pasamanos, zócalo y barrotes verticales.

    Los barrotes van más separados que en la realidad (12 cm): con el contorno de tinta,
    tan juntos se volverían una mancha negra a veinte metros. Es lo que haría un dibujante.
    """
    x0, x1 = x_range
    z0, z1 = z_range
    for x in (x0 + post / 2.0, x1 - post / 2.0):
        mb.box((post, post, z1 - z0), (x, y, (z0 + z1) / 2.0), color)
    mb.box((x1 - x0, 0.05, 0.04), ((x0 + x1) / 2.0, y, z1 - 0.02), color)
    mb.box((x1 - x0, 0.03, 0.03), ((x0 + x1) / 2.0, y, z0 + 0.08), color)
    count = max(1, round((x1 - x0) / bars))
    for k in range(1, count):
        x = x0 + (x1 - x0) * k / count
        mb.box((0.02, 0.02, z1 - z0 - 0.1), (x, y, (z0 + z1) / 2.0 + 0.01), color)


def banded_wall(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    z_range: tuple[float, float],
    y_range: tuple[float, float],
    color: str,
    *,
    holes: Sequence[tuple[float, float, float, float]] = (),
    band: float = 0.42,
    gap: float = 0.025,
    gap_color: str = "#5E5446",
    step: float = 0.6,
    ring: float = 0.08,
) -> None:
    """Muro almohadillado (los bajos estalinistas, las tablas del barracón): bandas con la
    junta pintada.

    Las juntas van enrasadas y de color, en el mismo plano que las bandas: una ranura,
    aunque sea de un milímetro, deja asomar el canto de las bandas, y el contorno de tinta
    lo dibujaría a puntos.
    """
    x0, x1 = x_range
    z0, z1 = z_range
    y0, y1 = y_range
    z = z0
    while z < z1 - 1e-6:
        top = min(z1, z + band)
        joint = min(top, z + band - gap) if top - z > gap * 2.0 else top
        clipped = [(a, max(b, z), c, min(d, joint)) for a, b, c, d in holes if b < joint and d > z]
        mb.slab((x0, x1), (z, joint), (y0, y1), color, holes=clipped, step=step, jitter=0.02, back=False, ring=ring)
        if joint < top:
            gaps = [(a, max(b, joint), c, min(d, top)) for a, b, c, d in holes if b < top and d > joint]
            mb.slab((x0, x1), (joint, top), (y0, y0 + 0.04), gap_color, holes=gaps, back=False)
        z = top


def moulding(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    profile: Sequence[tuple[float, float]],
    color: str,
    *,
    jitter: float = 0.0,
    mitre: bool | tuple[bool, bool] = False,
) -> list:
    """Moldura recta a lo largo de x con el perfil ``profile``: puntos (y, z) de su
    sección, con y < 0 hacia fuera del muro (alféizares, guardapolvos, impostas).

    Las caras de arriba y de abajo de una moldura van inclinadas (vierteaguas), no
    planas: vista a ras, una cara plana de pocos centímetros ocupa menos de un píxel y el
    contorno de tinta la dibujaría a puntos. Inclinada, su altura sigue viéndose.

    Con ``mitre`` (los dos extremos, o (izquierdo, derecho)), los extremos vuelven hasta el
    muro a inglete, como si la moldura doblara: sin un canto plano de frente, que de lejos
    se vería de canto. Los extremos que se juntan con otra pieza van rectos.
    """
    x0, x1 = x_range
    faces = mb.prism(ccw(profile), x1 - x0, ((x0 + x1) / 2.0, 0.0, 0.0), color, rotation=(90.0, 0.0, 90.0), jitter=jitter)
    left, right = (mitre, mitre) if isinstance(mitre, bool) else mitre
    for vert in dict.fromkeys(v for f in faces for v in f.verts):
        if left and abs(vert.co.x - x0) < 1e-6:
            vert.co.x = x0 - vert.co.y
        elif right and abs(vert.co.x - x1) < 1e-6:
            vert.co.x = x1 + vert.co.y
    return faces


def moulding_run(
    mb: tb.MeshBuilder,
    x_range: tuple[float, float],
    profile: Sequence[tuple[float, float]],
    color: str,
    *,
    holes: Sequence[tuple[float, float, float, float]] = (),
    jitter: float = 0.0,
) -> None:
    """Una moldura corrida (un zócalo, una imposta) partida donde la cortan los huecos
    ``(x0, z0, x1, z1)``: solo cuenta su ancho."""
    start, end = x_range
    for a, _, c, _ in sorted(holes) + [(end, 0.0, end, 0.0)]:
        if min(a, end) - start > 0.05:
            moulding(mb, (start, min(a, end)), profile, color, jitter=jitter)
        start = max(start, c)


def corner(mb: tb.MeshBuilder, profile: Sequence[tuple[float, float]], color: str) -> None:
    """La esquina que sobresale de una moldura corrida (imposta, cornisa, alero) con la
    sección ``profile`` de :func:`moulding`: las dos fachadas se cortan a inglete.

    La esquina está en el origen: una fachada sigue hacia +x (con el muro en y = 0) y la
    otra hacia +y (con el muro en x = 0); la pieza ocupa lo de fuera (x < 0, y < 0). La
    sección empieza y acaba contra el muro.
    """
    section = ccw([(-y, z) for y, z in profile])
    for (o0, z0), (o1, z1) in zip(section, section[1:]):
        mb.quad(((-o0, 0.0, z0), (-o0, -o0, z0), (-o1, -o1, z1), (-o1, 0.0, z1)), color)
        mb.quad(((-o0, -o0, z0), (0.0, -o0, z0), (0.0, -o1, z1), (-o1, -o1, z1)), color)


def offset_polygon(polygon: Sequence[tuple[float, float]], offset: float) -> list[Vector]:
    """Un contorno convexo desplazado hacia fuera (``offset`` > 0) o hacia dentro, con las
    esquinas a inglete. Devuelve los puntos en sentido antihorario."""
    points = [Vector(p) for p in ccw(polygon)]
    count = len(points)
    result = []
    for k in range(count):
        before = (points[k] - points[k - 1]).normalized()
        after = (points[(k + 1) % count] - points[k]).normalized()
        n_before = Vector((before.y, -before.x))
        n_after = Vector((after.y, -after.x))
        result.append(points[k] + (n_before + n_after) * (offset / (1.0 + n_before.dot(n_after))))
    return result


def outline(
    mb: tb.MeshBuilder,
    polygon: Sequence[tuple[float, float]],
    profile: Sequence[tuple[float, float]],
    color: str,
    *,
    step: float = 0.6,
) -> None:
    """Moldura alrededor de un contorno convexo de la fachada (un recercado, un frontón,
    los cantos de un sillar), con las esquinas a inglete.

    ``polygon`` son puntos (x, z) en la cara del muro (y = 0). ``profile`` es la sección,
    sin la cara que va contra el muro: puntos (o, d), con o hacia fuera del contorno y d
    lo que sale del muro (hacia -y). Empieza y acaba contra el muro; con dos puntos, va de
    fuera (el muro) hacia dentro y hacia delante. Los cantos van en derrame (inclinados)
    y no a escuadra: vista casi de frente, una cara a escuadra de pocos centímetros ocupa
    menos de un píxel y el contorno de tinta la dibujaría a puntos.
    """
    section = ccw(profile) if len(profile) > 2 else list(profile)
    rings = [offset_polygon(polygon, o) for o, _ in section]
    count = len(rings[0])
    for k in range(count):
        length = (rings[0][(k + 1) % count] - rings[0][k]).length
        segments = max(1, math.ceil(length / step))
        for i in range(len(section) - 1):
            d0, d1 = section[i][1], section[i + 1][1]
            a0, b0 = rings[i][k], rings[i][(k + 1) % count]
            a1, b1 = rings[i + 1][k], rings[i + 1][(k + 1) % count]
            for s in range(segments):
                f0, f1 = s / segments, (s + 1) / segments
                quad = ((a0.lerp(b0, f0), d0), (a0.lerp(b0, f1), d0), (a1.lerp(b1, f1), d1), (a1.lerp(b1, f0), d1))
                mb.quad([(p.x, -d, p.y) for p, d in quad], color)


def raised(
    mb: tb.MeshBuilder,
    polygon: Sequence[tuple[float, float]],
    depth: float,
    color: str,
    *,
    splay: float = 0.03,
) -> None:
    """Un relieve que sale del muro con el contorno ``polygon`` (convexo: puntos (x, z) de
    su cara de delante, a ``depth`` del muro) y los cantos en derrame: los trazos de una
    letra, una estrella, un emblema. Lo que no es convexo se hace con varios."""
    points = ccw(polygon)
    outline(mb, points, [(splay, 0.0), (0.0, depth)], color)
    mb.polygon([(x, -depth, z) for x, z in points], color)


def block(
    mb: tb.MeshBuilder,
    rect: tuple[float, float, float, float],
    depth: float,
    color: str,
    *,
    splay: float = 0.04,
    cuts: int = 0,
) -> None:
    """Un bloque que sale del muro (sillar, ménsula, tablero, clave) con los cantos en
    derrame: ``rect`` (x0, z0, x1, z1) es su cara de delante, a ``depth`` del muro, y los
    cantos llegan al muro ``splay`` más allá."""
    x0, z0, x1, z1 = rect
    outline(mb, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], [(splay, 0.0), (0.0, depth)], color)
    mb.quad(((x0, -depth, z0), (x1, -depth, z0), (x1, -depth, z1), (x0, -depth, z1)), color, cuts=cuts)


def ring(
    mb: tb.MeshBuilder,
    half: tuple[float, float],
    profile: Sequence[tuple[float, float]],
    color: str,
    *,
    step: float = 1.5,
) -> None:
    """Moldura que da la vuelta a una planta rectangular (centrada en el origen, de
    semilados ``half``), con las esquinas a inglete: zócalos, vierteaguas, impostas.

    ``profile`` es la sección por fuera, sin la cara que va contra el muro: puntos
    (o, z), con o lo que sale del muro. Cada lado se parte cada ``step`` metros como
    mucho, para que recoja la oclusión y las manchas por vértice.
    """
    points = ccw(profile)
    hx, hy = half
    corners = ((1.0, -1.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0))

    def corner(index: int, offset: float, z: float) -> Vector:
        sx, sy = corners[index % 4]
        return Vector((sx * (hx + offset), sy * (hy + offset), z))

    for side in range(4):
        count = max(1, math.ceil(2.0 * (hy if side % 2 == 0 else hx) / step))
        for (o0, z0), (o1, z1) in zip(points, points[1:]):
            a0, b0 = corner(side, o0, z0), corner(side + 1, o0, z0)
            a1, b1 = corner(side, o1, z1), corner(side + 1, o1, z1)
            for k in range(count):
                f0, f1 = k / count, (k + 1) / count
                mb.quad((a0.lerp(b0, f0), a0.lerp(b0, f1), a1.lerp(b1, f1), a1.lerp(b1, f0)), color)


def balusters(
    mb: tb.MeshBuilder,
    start: Vector,
    end: Vector,
    z: float,
    height: float,
    color: str,
    *,
    spacing: float = 0.19,
    segments: int = 8,
) -> None:
    """Fila de balaustres torneados entre dos puntos, de pie sobre ``z``."""
    length = (end - start).length
    count = max(1, round(length / spacing))
    h = height
    profile = [(0.0, 0.0), (0.055, 0.0), (0.055, h * 0.08), (0.038, h * 0.12), (0.06, h * 0.38), (0.035, h * 0.72), (0.03, h * 0.82), (0.045, h * 0.88), (0.045, h), (0.0, h)]
    for k in range(count):
        p = start.lerp(end, (k + 0.5) / count)
        mb.lathe(profile, (p.x, p.y, z), color, segments=segments)


# --------------------------------------------------------------------------
# Carpinterías
# --------------------------------------------------------------------------

# Estados de una ventana. "intacta" y "cortina" conservan los cristales; "rota", los
# picos y una hoja abierta; "tapiada", tablones por fuera; "plastico", un plástico
# clavado (alguien vivió allí después); "quemada", el marco carbonizado y las mochetas
# negras; "vacia", el hueco desnudo.
WINDOW_STATES = ("intacta", "cortina", "rota", "tapiada", "plastico", "quemada", "vacia")


class Sash:
    """Una hoja de una carpintería: su rectángulo, sus paños y por dónde gira.

    ``panes`` son rectángulos ``(x0, z0, x1, z1)`` relativos a la hoja (de 0 a 1) y su
    clase: "vidrio" o "tabla" (el plafón de madera de una puerta).
    """

    def __init__(self, rect: tuple[float, float, float, float], panes: list, hinge_side: str = "izquierda") -> None:
        self.rect = rect
        self.panes = panes
        self.hinge_side = hinge_side

    def pane_rects(self, bar: float) -> list[tuple[tuple[float, float, float, float], str]]:
        x0, z0, x1, z1 = self.rect
        w, h = x1 - x0, z1 - z0
        result = []
        for (u0, v0, u1, v1), kind in self.panes:
            result.append(
                (
                    (
                        x0 + max(bar, u0 * w + (bar / 2.0 if u0 > 0 else 0.0)),
                        z0 + max(bar, v0 * h + (bar / 2.0 if v0 > 0 else 0.0)),
                        x0 + min(w - bar, u1 * w - (bar / 2.0 if u1 < 1 else 0.0)),
                        z0 + min(h - bar, v1 * h - (bar / 2.0 if v1 < 1 else 0.0)),
                    ),
                    kind,
                )
            )
        return result


def window_layout(opening: tuple[float, float, float, float], kind: str, frame: float = 0.06) -> list[Sash]:
    """Las hojas de las carpinterías soviéticas de madera, según el hueco.

    - "habitacion": hoja estrecha con ventanillo (la fortochka) y hoja ancha.
    - "cocina": dos hojas iguales, la izquierda con ventanillo.
    - "puerta": puerta de balcón, cristal arriba y plafón abajo.
    - "escalera": paño fijo partido en cuatro.
    - "portal": puerta de dos hojas con cristales altos y montante.
    - "escaparate": luna grande con montante (bajos comerciales).
    - "alta": la ventana estalinista, alta, con travesaño y montante.
    """
    x0, z0, x1, z1 = opening
    ix0, iz0, ix1, iz1 = x0 + frame, z0 + frame, x1 - frame, z1 - frame
    width = ix1 - ix0
    glass = "vidrio"
    if kind == "habitacion":
        split = ix0 + width * 0.42
        return [
            Sash((ix0, iz0, split, iz1), [((0, 0, 1, 0.66), glass), ((0, 0.66, 1, 1), glass)], "izquierda"),
            Sash((split, iz0, ix1, iz1), [((0, 0, 1, 1), glass)], "derecha"),
        ]
    if kind == "cocina":
        split = ix0 + width * 0.5
        return [
            Sash((ix0, iz0, split, iz1), [((0, 0, 1, 0.68), glass), ((0, 0.68, 1, 1), glass)], "izquierda"),
            Sash((split, iz0, ix1, iz1), [((0, 0, 1, 1), glass)], "derecha"),
        ]
    if kind == "puerta":
        return [Sash((ix0, iz0, ix1, iz1), [((0, 0.42, 1, 1), glass), ((0, 0, 1, 0.42), "tabla")], "izquierda")]
    if kind == "escalera":
        return [
            Sash(
                (ix0, iz0, ix1, iz1),
                [((0, 0, 0.5, 0.5), glass), ((0.5, 0, 1, 0.5), glass), ((0, 0.5, 0.5, 1), glass), ((0.5, 0.5, 1, 1), glass)],
                "izquierda",
            )
        ]
    if kind == "portal":
        top = iz1 - 0.38
        split = ix0 + width * 0.5
        return [
            Sash((ix0, iz0, split, top), [((0, 0.45, 1, 1), glass), ((0, 0, 1, 0.45), "tabla")], "izquierda"),
            Sash((split, iz0, ix1, top), [((0, 0.45, 1, 1), glass), ((0, 0, 1, 0.45), "tabla")], "derecha"),
            Sash((ix0, top, ix1, iz1), [((0, 0, 1, 1), glass)], "izquierda"),
        ]
    if kind == "escaparate":
        top = iz1 - 0.55
        return [
            Sash((ix0, iz0, ix1, top), [((0, 0, 1, 1), glass)], "izquierda"),
            Sash((ix0, top, ix1, iz1), [((0, 0, 0.5, 1), glass), ((0.5, 0, 1, 1), glass)], "izquierda"),
        ]
    if kind == "alta":
        # Ventana estalinista: dos hojas partidas por un travesaño y el montante arriba.
        top = iz0 + (iz1 - iz0) * 0.76
        split = ix0 + width * 0.5
        return [
            Sash((ix0, iz0, split, top), [((0, 0, 1, 0.5), glass), ((0, 0.5, 1, 1), glass)], "izquierda"),
            Sash((split, iz0, ix1, top), [((0, 0, 1, 0.5), glass), ((0, 0.5, 1, 1), glass)], "derecha"),
            Sash((ix0, top, ix1, iz1), [((0, 0, 0.5, 1), glass), ((0.5, 0, 1, 1), glass)], "izquierda"),
        ]
    raise ValueError(f"Carpintería desconocida: {kind}")


def _shard(mb: tb.MeshBuilder, rect: tuple[float, float, float, float], y: float, rng: random.Random) -> None:
    """Un pico de cristal en una esquina del paño."""
    x0, z0, x1, z1 = rect
    corner_x, corner_z = rng.choice(((x0, z0), (x1, z0), (x0, z1), (x1, z1)))
    sx = 1.0 if corner_x == x0 else -1.0
    sz = 1.0 if corner_z == z0 else -1.0
    a = rng.uniform(0.25, 0.75) * (x1 - x0)
    b = rng.uniform(0.25, 0.75) * (z1 - z0)
    points = [(corner_x, corner_z), (corner_x + sx * a, corner_z), (corner_x + sx * a * 0.2, corner_z + sz * b * 0.35), (corner_x, corner_z + sz * b)]
    if sx * sz < 0:
        points.reverse()
    mb.prism(points, 0.005, (0.0, y, 0.0), GLASS, rotation=(90.0, 0.0, 0.0))


def _sash(
    mb: tb.MeshBuilder,
    sash: Sash,
    y: float,
    color: str,
    state: str,
    rng: random.Random,
    *,
    bar: float = 0.045,
    depth: float = 0.055,
) -> list:
    """Una hoja: el bastidor con sus paños (cristal, tabla o nada) y lo que quede de ellos."""
    faces = []
    panes = sash.pane_rects(bar)
    faces += mb.slab(
        (sash.rect[0], sash.rect[2]), (sash.rect[1], sash.rect[3]), (y, y + depth), color,
        holes=[r for r, _ in panes], jitter=0.05,
    )
    for rect, kind in panes:
        x0, z0, x1, z1 = rect
        if kind == "tabla":
            faces += mb.box((x1 - x0 + 0.01, 0.02, z1 - z0 + 0.01), ((x0 + x1) / 2.0, y + depth * 0.6, (z0 + z1) / 2.0), color, jitter=0.05)
            continue
        if state in ("intacta", "cortina"):
            with mb.material(1):
                faces += mb.box((x1 - x0 + 0.01, 0.006, z1 - z0 + 0.01), ((x0 + x1) / 2.0, y + depth * 0.55, (z0 + z1) / 2.0), GLASS)
        elif state in ("rota", "tapiada") and rng.random() < 0.6:
            with mb.material(1):
                for _ in range(rng.randint(1, 2)):
                    before = set(mb.bm.faces)
                    _shard(mb, rect, y + depth * 0.55, rng)
                    faces += [f for f in mb.bm.faces if f not in before]
    return faces


def window(
    mb: tb.MeshBuilder,
    opening: tuple[float, float, float, float],
    kind: str,
    state: str,
    rng: random.Random,
    *,
    depth: float,
    wall: float,
    frame_color: str = FRAME,
    sill: bool = True,
    inner: bool = False,
    open_sash: int | None = None,
    open_angle: float | None = None,
) -> None:
    """Carpintería de madera de doble hoja en un hueco ``(x0, z0, x1, z1)``.

    ``depth`` es lo que se mete el marco desde la cara exterior del muro y ``wall``
    el espesor del muro (detrás, el alféizar interior). Materiales: 0 la madera y la
    chapa (cogen nieve), 1 el cristal y 2 lo de dentro. Rota, se abre una de las
    hojas que giran (``open_sash`` dice cuál; los montantes y los fijos, nunca),
    ``open_angle`` grados (por defecto, entre 35 y 70 al azar).
    """
    x0, z0, x1, z1 = opening
    frame = 0.06
    burnt = state == "quemada"
    color = CHAR if burnt else frame_color
    if state == "vacia":
        # Quedan astillas del marco arrancado y algún clavo.
        for _ in range(rng.randint(2, 4)):
            side = rng.choice(("izquierda", "derecha", "abajo"))
            length = rng.uniform(0.15, 0.45)
            if side == "abajo":
                center = (rng.uniform(x0 + 0.2, x1 - 0.2), depth + 0.04, z0 + 0.02)
                size = (length, 0.05, 0.03)
            else:
                center = (x0 + 0.02 if side == "izquierda" else x1 - 0.02, depth + 0.04, rng.uniform(z0 + 0.2, z1 - 0.2))
                size = (0.03, 0.05, length)
            mb.box(size, center, FRAME_WOOD, rotation=(rng.uniform(-8, 8), 0.0, rng.uniform(-6, 6)), jitter=0.1)
        return
    # El cerco (el marco fijo al muro). Quemado, le faltan trozos.
    if burnt:
        bars = [
            ((x0, z0, x0 + frame, z1), "v"), ((x1 - frame, z0, x1, z1), "v"),
            ((x0, z0, x1, z0 + frame), "h"), ((x0, z1 - frame, x1, z1), "h"),
        ]
        for (a, b, c, d), direction in bars:
            pieces = rng.randint(1, 3)
            for k in range(pieces):
                if rng.random() < 0.4:
                    continue
                if direction == "v":
                    lo, hi = b + (d - b) * k / pieces, b + (d - b) * (k + 1) / pieces
                    hi -= rng.uniform(0.0, 0.25) * (hi - lo)
                    mb.box((c - a, 0.07, hi - lo), ((a + c) / 2.0, depth + 0.035, (lo + hi) / 2.0), CHAR, jitter=0.1)
                else:
                    lo, hi = a + (c - a) * k / pieces, a + (c - a) * (k + 1) / pieces
                    hi -= rng.uniform(0.0, 0.25) * (hi - lo)
                    mb.box((hi - lo, 0.07, d - b), ((lo + hi) / 2.0, depth + 0.035, (b + d) / 2.0), CHAR, jitter=0.1)
        # Las mochetas, negras de humo.
        lining = depth + 0.08
        for size, center in (
            ((0.004, lining, z1 - z0), (x0 + 0.002, lining / 2.0, (z0 + z1) / 2.0)),
            ((0.004, lining, z1 - z0), (x1 - 0.002, lining / 2.0, (z0 + z1) / 2.0)),
            ((x1 - x0, lining, 0.004), ((x0 + x1) / 2.0, lining / 2.0, z1 - 0.002)),
        ):
            mb.box(size, center, SOOT)
    else:
        mb.slab((x0, x1), (z0, z1), (depth, depth + 0.08), color, holes=[(x0 + frame, z0 + frame, x1 - frame, z1 - frame)], jitter=0.04)
    # Las hojas exteriores.
    sashes = window_layout(opening, kind, frame)
    swinging = {"habitacion": 2, "cocina": 2, "puerta": 1, "portal": 2, "alta": 2}.get(kind, 0)
    open_index = -1
    if state == "rota" and swinging > 0:
        open_index = open_sash if open_sash is not None else rng.randrange(swinging)
    for index, sash in enumerate(sashes):
        if burnt:
            if rng.random() < 0.5:
                continue
            sx0, sz0, sx1, sz1 = sash.rect
            for _ in range(rng.randint(1, 2)):
                mb.box((0.045, 0.05, (sz1 - sz0) * rng.uniform(0.3, 0.8)), (rng.choice((sx0 + 0.03, sx1 - 0.03)), depth + 0.03, sz0 + (sz1 - sz0) * rng.uniform(0.3, 0.6)), CHAR, rotation=(0.0, rng.uniform(-10, 10), 0.0), jitter=0.1)
            continue
        faces = _sash(mb, sash, depth, color, state, rng)
        if index == open_index:
            # La hoja suelta cuelga hacia la calle: se lee desde fuera y no choca con la de dentro.
            sx0, _, sx1, _ = sash.rect
            pivot_x = sx0 if sash.hinge_side == "izquierda" else sx1
            swing = open_angle if open_angle is not None else rng.uniform(35.0, 70.0)
            angle = swing * (-1.0 if sash.hinge_side == "izquierda" else 1.0)
            transform_faces(faces, hinge((pivot_x, depth, 0.0), "Z", angle))
    # Las hojas interiores (las ventanas soviéticas son dobles). Por defecto no: doblan las
    # líneas del contorno y, tras el cristal oscuro, apenas se ven.
    if inner and not burnt and kind not in ("portal", "escaparate"):
        inner_y = depth + 0.15
        holes = [r for sash in sashes for r, _ in sash.pane_rects(0.045)]
        mb.slab((x0 + frame, x1 - frame), (z0 + frame, z1 - frame), (inner_y, inner_y + 0.05), SASH_SHADOW, holes=holes, jitter=0.05)
    # Alféizares: la chapa de fuera (con nieve) y la tabla de dentro.
    if sill and kind not in ("puerta", "portal"):
        mb.box(
            (x1 - x0 + 0.06, depth + 0.08, 0.014), ((x0 + x1) / 2.0, (depth - 0.06) / 2.0, z0 - 0.006),
            RUST if burnt else GALVANIZED, rotation=(7.0, 0.0, 0.0), jitter=0.06,
        )
    if sill and kind not in ("puerta", "portal", "escaparate"):
        with mb.material(2):
            mb.box((x1 - x0 + 0.1, 0.24, 0.035), ((x0 + x1) / 2.0, wall + 0.1, z0 + 0.03), SOOT if burnt else SILL_INSIDE, jitter=0.05)
    if state == "cortina":
        _curtains(mb, opening, wall + 0.12, rng)
    elif state == "tapiada":
        planks(mb, opening, 0.0, rng)
    elif state == "plastico":
        _film(mb, opening, depth, rng)


def _curtains(mb: tb.MeshBuilder, opening: tuple[float, float, float, float], y: float, rng: random.Random) -> None:
    """Cortinas recogidas a los lados, por dentro, como las dejaron al irse."""
    x0, z0, x1, z1 = opening
    color = rng.choice(CURTAINS)
    with mb.material(2):
        for side in (-1.0, 1.0):
            if rng.random() < 0.25:
                continue
            width = (x1 - x0) * rng.uniform(0.22, 0.38)
            start = x0 - 0.05 if side < 0 else x1 + 0.05 - width
            folds = max(3, round(width / 0.07))
            front = [(start + width * k / folds, y + 0.025 * math.sin(k * math.pi * 0.9)) for k in range(folds + 1)]
            back = [(x, yy + 0.012) for x, yy in reversed(front)]
            mb.prism(front + back, z1 - z0 + 0.1, (0.0, 0.0, (z0 + z1) / 2.0 + 0.05), color, jitter=0.06)
        mb.box((x1 - x0 + 0.3, 0.03, 0.03), ((x0 + x1) / 2.0, y, z1 + 0.12), METAL)


def _film(mb: tb.MeshBuilder, opening: tuple[float, float, float, float], depth: float, rng: random.Random) -> None:
    """Plástico clavado con listones sobre un hueco: alguien pasó aquí el invierno."""
    x0, z0, x1, z1 = opening
    faces = mb.box((x1 - x0 + 0.08, 0.006, z1 - z0 + 0.08), ((x0 + x1) / 2.0, depth - 0.02, (z0 + z1) / 2.0), FILM, cuts=4, jitter=0.05)
    for vert in dict.fromkeys(v for f in faces for v in f.verts):
        u = (vert.co.x - x0) / max(x1 - x0, 1e-6)
        w = (vert.co.z - z0) / max(z1 - z0, 1e-6)
        sag = max(0.0, math.sin(math.pi * min(max(u, 0.0), 1.0)) * math.sin(math.pi * min(max(w, 0.0), 1.0)))
        vert.co.y += sag * rng.uniform(0.05, 0.09)
    for z in (z0 - 0.02, z1 + 0.02):
        mb.box((x1 - x0 + 0.14, 0.025, 0.04), ((x0 + x1) / 2.0, depth - 0.04, z), rng.choice(PLANKS), rotation=(0.0, rng.uniform(-3, 3), 0.0), jitter=0.08)
    for x in (x0 - 0.02, x1 + 0.02):
        mb.box((0.04, 0.025, z1 - z0 + 0.1), (x, depth - 0.04, (z0 + z1) / 2.0), rng.choice(PLANKS), jitter=0.08)
