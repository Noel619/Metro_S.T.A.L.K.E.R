"""Edificio singular: el Edificio Partido (ZC-01), el Instituto de investigación Nº 9.

Un instituto de los años sesenta, sin copiar ninguno real: catorce plantas de estructura de
hormigón (pilares y forjados), fachadas largas de ventanas corridas entre antepechos de
plaqueta blanca y un testero ciego de plaqueta gris con el relieve del átomo y las letras
НИИ-9. La bomba cayó a 240 m, en la dirección de su eje largo: la mitad que la miraba
desapareció; la otra sigue en pie con los pisos abiertos al cráter, como una casa de
muñecas: los forjados rotos con su ferralla, trozos que cuelgan, pilares partidos, los
tabiques cortados y los laboratorios y los despachos con sus cosas al borde del vacío. Arriba
la bomba se llevó más. Aquí termina el juego.

Se puede subir: la escalera del extremo suroeste llega a todas las plantas y a la azotea,
por la caseta de salida que mira al cráter. En cada planta, el pasillo central lleva de la
escalera al borde. La entrada, con su marquesina, está en la fachada sureste, junto al
testero.

Coordenadas: las del plano (x al este, y al norte, z arriba), con el origen en el «centro»
de ZC-01 (el de la huella) y a su cota. Se construye en un marco propio: u a lo largo del eje
largo, hacia la bomba (el noreste), v de través (hacia el noroeste) y z arriba; ``_to_plan``
lo gira al plano.

Piezas: "partido" (la estructura, las fachadas, los tabiques y la escalera), "partido_cosas"
(los muebles y el equipo de los laboratorios), "partido_escombros" (la mitad caída, al pie
del corte) y "partido_colision" (no se dibuja: los forjados, los muros, la escalera como
rampas, el montón).
"""

from __future__ import annotations

import math
import random

from mathutils import Matrix, Vector, noise

import kit_bpy as kit
import tumansk_bpy as tb

ORIGIN = (1292.0, 985.0)  # el «centro» de ZC-01 en el plano
AXIS = math.radians(31.04)  # el eje largo, que apunta a la bomba (al noreste)

HALF_L, HALF_W = 18.0, 9.0  # la huella entera: 36 × 18 m
FLOORS = 14
STOREY = 3.3
BASE = 0.15  # el suelo de la planta baja, un escalón sobre la calle
SLAB = 0.22
SILL = 0.9  # el antepecho, sobre el forjado
SPANDREL = 0.25  # su grueso
PARAPET = 1.0
GABLE = 0.4  # el muro del testero suroeste
WALL_IN = -HALF_L + GABLE  # su cara de dentro
COLUMN = 0.45
COLUMN_U = (-12.0, -6.0, 0.0)
COLUMN_V = (-8.45, -1.8, 1.8, 8.45)
CORRIDOR = 1.5  # medio ancho del pasillo central
PARTITION = 0.15
PARTITION_U = (-12.0, -6.0)
INNER = HALF_W - SPANDREL  # la cara de dentro de las fachadas largas
MODULE = 1.5  # el paso de los montantes de las ventanas corridas
DOOR_H = 2.1
DADO_H = 1.4  # la pintura verde de abajo de las paredes

# La escalera: en el extremo suroeste, al noroeste del pasillo. Dos tramos por planta.
LANDING_U = (-13.4, -12.0)  # el rellano de cada planta (parte del forjado)
MID_U = (WALL_IN, -16.2)  # el descansillo de en medio
FLIGHT_A = (2.0, 3.3)  # el tramo que sube desde la planta, de través (v)
FLIGHT_B = (3.5, 4.8)  # el que llega a la de arriba
STAIR_HOLE = (WALL_IN, 1.9, -13.4, 4.9)  # el hueco en los forjados (u0, v0, u1, v1)
RISERS = 11  # por tramo: 11 × 0,15 = 1,65 m
RISER = STOREY / (2 * RISERS)
TREAD = 0.28
STAIR_DOOR = (-13.3, -12.4)  # la puerta del pasillo al rellano
ENTRANCE = (-16.5, -13.5)  # la entrada, en la fachada sureste

# Dónde acaba cada forjado (u), de abajo arriba (0, el suelo de la planta baja; 14, la
# azotea): arriba la bomba se llevó más.
CUTS = (3.0, 1.2, 0.4, -0.8, -2.1, -2.8, -1.9, -3.4, -2.6, -3.9, -4.6, -5.3, -6.4, -7.6, -9.5)
# Trozos de forjado que cuelgan del borde: planta -> (de v0 a v1, largo, grados).
HANGING = {4: (-9.0, -0.6, 3.2, 38.0), 7: (1.0, 9.0, 2.6, 62.0), 9: (-6.0, 4.0, 3.5, 24.0), 11: (-9.0, -2.0, 2.2, 75.0)}
# Las plantas que ardieron (el incendio parcial): ventanas quemadas y hollín.
BURNT = (5, 6, 7)

# Colores (sRGB).
CONCRETE = "#77726B"
CONCRETE_DARK = "#5C5852"
TILE = "#C4C1B6"  # la plaqueta blanca de los antepechos
TILE_GABLE = "#8E989C"  # la gris azulada del testero
RELIEF = "#D2CEC2"
GRANITE = "#5E5A56"
FRAME = "#6A5A48"
WALL_LOW = "#56645A"
WALL_HIGH = "#B8B3A3"
TERRAZZO = "#8A847A"
LINOLEUM = "#5D5F55"
PARQUET = "#6B5440"
STEEL = "#4A4E50"
SOOT = "#1E1B19"


# --------------------------------------------------------------------------
# Marcos y geometría auxiliar
# --------------------------------------------------------------------------


def _level(f: int) -> float:
    """La cara de arriba del forjado de la planta ``f`` (0, la planta baja; 14, la azotea)."""
    return BASE + f * STOREY


def _to_plan(mb: tb.MeshBuilder) -> None:
    kit.transform_faces(list(mb.bm.faces), Matrix.Rotation(AXIS, 4, "Z"))


def _from_plan(position: Vector) -> Vector:
    return Matrix.Rotation(-AXIS, 3, "Z") @ Vector(position)


def _placed(mb: tb.MeshBuilder, matrix: Matrix, build) -> None:
    """Construye algo en un marco y lo lleva a su sitio."""
    before = set(mb.bm.faces)
    build(mb)
    kit.transform_faces([f for f in mb.bm.faces if f not in before], matrix)


def _facing(mb: tb.MeshBuilder, corners: list, color: str, outward: Vector, *, cuts: int = 0) -> None:
    """Una cara de cuatro esquinas que mira hacia ``outward``."""
    a, b, c = (Vector(p) for p in corners[:3])
    if (b - a).cross(c - b).dot(Vector(outward)) < 0.0:
        corners = corners[::-1]
    mb.quad(corners, color, cuts=cuts)


def _side(side: float) -> Matrix:
    """El marco de una fachada larga (``side`` 1, la del noroeste; -1, la del sureste): x a
    lo largo (de izquierda a derecha, vista desde fuera), y hacia dentro y z arriba, con el
    origen en su plano (v = ±9)."""
    return Matrix(((-side, 0.0, 0.0, 0.0), (0.0, -side, 0.0, side * HALF_W), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _gable() -> Matrix:
    """El marco del testero suroeste: x a lo largo (visto desde fuera), y hacia dentro."""
    return Matrix(((0.0, 1.0, 0.0, -HALF_L), (-1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _flat(z: float) -> Matrix:
    """El marco de una placa horizontal hecha con ``MeshBuilder.slab``: su x es u, su z es v
    y su cara de delante (y = 0) mira arriba, a la altura ``z``."""
    return Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, z), (0.0, 0.0, 0.0, 1.0)))


def _across(u: float) -> Matrix:
    """El marco de un tabique de través, en ``u``: x a lo largo (v) e y hacia -u."""
    return Matrix(((0.0, -1.0, 0.0, u), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _ragged_plate(
    mb: tb.MeshBuilder, x0: float, end: float, z0: float, z1: float, y_range: tuple, color: str, rng: random.Random, *, reach: float = 0.45
) -> None:
    """Una placa vertical (x a lo largo, z arriba, de grueso en y) de ``x0`` a un final roto
    hacia ``end``: dientes de hormigón, nunca un corte recto."""
    edge = kit.broken_edge(z0, z1, end - reach, end + reach, rng, step=0.3)
    outline = [(x0, z0), *[(max(x0 + 0.05, x), z) for z, x in edge], (x0, z1)]
    y0, y1 = y_range
    mb.prism(kit.ccw(outline), y1 - y0, (0.0, (y0 + y1) / 2.0, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.04)


def _soot(mb: tb.MeshBuilder, faces: list, x: float, z: float, width: float, height: float) -> None:
    """Hollín sobre el color base de unas caras (en un marco con x a lo largo y z arriba):
    sube desde (x, z), se abre y se apaga."""
    target = Vector(int(SOOT[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
    for face in faces:
        for loop in face.loops:
            co = loop.vert.co
            rise = co.z - z
            if rise < -0.4 or rise > height:
                continue
            spread = width * (0.5 + 0.45 * max(rise, 0.0) / height)
            side = abs(co.x - x) / spread + 0.3 * noise.noise(Vector((co.x * 2.1, co.z * 0.8, x)))
            weight = (1.0 - max(rise, 0.0) / height) * max(0.0, 1.0 - side * side)
            if weight > 0.0:
                base = Vector(loop[mb.base][:3])
                loop[mb.base] = (*base.lerp(target, min(1.0, 0.9 * weight)), 1.0)


# --------------------------------------------------------------------------
# La estructura: forjados, pilares y lo que cuelga
# --------------------------------------------------------------------------


def _edge(f: int, rng: random.Random) -> list:
    """El borde roto del forjado ``f``: puntos (v, u) de un costado al otro."""
    cut = CUTS[f]
    return kit.broken_edge(-HALF_W, HALF_W, cut - 0.6, cut + 0.6, rng, step=0.45)


def _slab(mb: tb.MeshBuilder, f: int, edge: list, color: str) -> None:
    """El forjado ``f``: la parte entera hasta un poco antes del corte (con el hueco de la
    escalera, menos en la planta baja) y la parte rota, un prisma con el borde de dientes."""
    top = _level(f)
    thickness = 0.45 if f == 0 else SLAB
    split = min(u for _, u in edge) - 0.3
    holes = [] if f == 0 else [STAIR_HOLE]
    _placed(mb, _flat(top), lambda b: b.slab((-HALF_L, split), (-HALF_W, HALF_W), (0.0, thickness), color, holes=holes, step=1.5, jitter=0.03))
    outline = kit.ccw([(split, -HALF_W), *[(u, v) for v, u in edge], (split, HALF_W)])
    mb.prism(outline, thickness, (0.0, 0.0, top - thickness / 2.0), color, jitter=0.03)


def _rebar_fringe(mb: tb.MeshBuilder, edge: list, z: float, rng: random.Random) -> None:
    """La ferralla que asoma del borde de un forjado roto, doblada hacia abajo."""
    for (v0, u0), (v1, u1) in zip(edge, edge[1:]):
        for _ in range(rng.randint(0, 2)):
            t = rng.random()
            start = (u0 + (u1 - u0) * t - 0.05, v0 + (v1 - v0) * t, z - rng.uniform(0.05, SLAB - 0.05))
            kit.rebar(mb, start, (1.0, rng.uniform(-0.3, 0.3), rng.uniform(-0.9, -0.2)), rng.uniform(0.35, 1.1), rng, radius=0.01)


def _hanging(mb: tb.MeshBuilder, f: int, edge: list, rng: random.Random) -> None:
    """Un trozo de forjado que cuelga del borde, doblado sobre su ferralla."""
    v0, v1, length, angle = HANGING[f]
    hinge = min(u for v, u in edge if v0 - 0.5 <= v <= v1 + 0.5)
    top = _level(f)
    far = kit.broken_edge(v0, v1, length - 0.5, length + 0.4, rng, step=0.4)
    outline = kit.ccw([(0.0, v0), *[(u, v) for v, u in far], (0.0, v1)])
    before = set(mb.bm.faces)
    mb.prism(outline, SLAB, (0.0, 0.0, -SLAB / 2.0), CONCRETE, jitter=0.04)
    for v, u in far[1:-1:2]:
        kit.rebar(mb, (u - 0.05, v, -0.1), (1.0, rng.uniform(-0.2, 0.2), -0.5), rng.uniform(0.3, 0.8), rng, radius=0.01)
    turn = Matrix.Translation((hinge - 0.1, 0.0, top)) @ Matrix.Rotation(math.radians(angle), 4, "Y") @ Matrix.Rotation(math.radians(rng.uniform(-6.0, 6.0)), 4, "X")
    kit.transform_faces([face for face in mb.bm.faces if face not in before], turn)
    # La ferralla que lo sujeta, de borde a borde de la bisagra.
    for v in [v0 + (v1 - v0) * k / 6 for k in range(1, 6)]:
        mb.tube(tb.smooth_path([(hinge - 0.3, v, top - 0.12), (hinge + 0.05, v, top - 0.1), (hinge + 0.1, v, top - 0.25)], steps=2), 0.012, kit.REBAR, segments=4)


def _columns(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """Los pilares: enteros donde los dos forjados siguen; partidos, con su ferralla, donde
    el de arriba se fue."""
    half = COLUMN / 2.0
    for u in COLUMN_U:
        for v in COLUMN_V:
            for f in range(FLOORS):
                bottom, top = _level(f), _level(f + 1) - SLAB
                below = u + half < CUTS[f] - 0.5
                above = u + half < CUTS[f + 1] - 0.5
                if below and above:
                    mb.box((COLUMN, COLUMN, top - bottom), (u, v, (bottom + top) / 2.0), CONCRETE, jitter=0.03)
                elif below:
                    height = rng.uniform(0.5, 1.6)
                    edge = kit.broken_edge(-half, half, height - 0.25, height + 0.2, rng, step=0.12)
                    _placed(mb, Matrix.Translation((u, v, bottom)), lambda b, edge=edge: kit.broken_slab(b, (-half, half), 0.0, edge, (-half, half), CONCRETE))
                    for corner in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                        start = (u + corner[0] * (half - 0.05), v + corner[1] * (half - 0.05), bottom + height - 0.2)
                        kit.rebar(mb, start, (corner[0] * 0.2, corner[1] * 0.2, 1.0), rng.uniform(0.4, 0.9), rng, radius=0.012)


# --------------------------------------------------------------------------
# Las fachadas: antepechos de plaqueta, ventanas corridas, la entrada y el testero
# --------------------------------------------------------------------------


def _spandrels(mb: tb.MeshBuilder, rng: random.Random) -> dict:
    """Los antepechos de plaqueta de las dos fachadas largas, planta a planta (el de la
    azotea es el pretil), con el final roto junto al corte. Devuelve dónde acaba cada uno."""
    ends = {}
    for side in (-1.0, 1.0):
        v = side * (HALF_W - SPANDREL / 2.0)
        for f in range(FLOORS + 1):
            top = _level(f) + (PARAPET if f == FLOORS else SILL)
            bottom = _level(f) - (0.45 if f == 0 else SLAB) - (0.15 if f == 0 else 0.0)
            end = CUTS[f] + rng.uniform(-0.3, 0.7)
            ends[(side, f)] = end
            color = GRANITE if f == 0 else TILE
            slot = 0 if f == 0 else 3
            with mb.material(slot):
                if f == 0 and side < 0.0:  # la entrada parte el zócalo
                    mb.box((ENTRANCE[0] + HALF_L, SPANDREL, top - bottom), ((ENTRANCE[0] - HALF_L) / 2.0, v, (top + bottom) / 2.0), color, jitter=0.03)
                    _ragged_plate(mb, ENTRANCE[1], end, bottom, top, (v - SPANDREL / 2.0, v + SPANDREL / 2.0), color, rng)
                else:
                    _ragged_plate(mb, -HALF_L, end, bottom, top, (v - SPANDREL / 2.0, v + SPANDREL / 2.0), color, rng)
    return ends


def _ribbon_windows(mb: tb.MeshBuilder, rng: random.Random, ends: dict) -> None:
    """Las ventanas corridas, módulo a módulo, entre los antepechos y los forjados: casi
    todas reventadas; en las plantas que ardieron, quemadas, con el hollín encima."""
    for side in (-1.0, 1.0):

        def build(builder: tb.MeshBuilder, side=side) -> None:
            for f in range(FLOORS):
                z0, z1 = _level(f) + SILL, _level(f + 1) - SLAB
                end = min(ends[(side, f)], ends[(side, f + 1)]) - 0.4
                count = int((end + HALF_L) // MODULE)
                for k in range(count):
                    u0, u1 = -HALF_L + k * MODULE, -HALF_L + (k + 1) * MODULE
                    if f == 0 and side < 0.0 and ENTRANCE[0] - 0.01 < u0 < ENTRANCE[1]:
                        continue
                    x0, x1 = sorted((-side * u0, -side * u1))
                    nearness = (u1 + HALF_L) / max(end + HALF_L, 1.0)
                    if f in BURNT and nearness > 0.4:
                        state = "quemada"
                    else:
                        state = rng.choices(("vacia", "rota", "intacta", "tapiada"), weights=(0.3 + nearness, 0.5, 0.25 - 0.2 * nearness, 0.05))[0]
                    kit.window(builder, (x0, z0, x1, z1), "escaparate", state, rng, depth=0.1, wall=SPANDREL, frame_color=FRAME, sill=False)

        _placed(mb, _side(side), build)


def _burns(mb: tb.MeshBuilder) -> None:
    """El hollín de las plantas que ardieron, pintado en los antepechos de encima."""
    for side in (-1.0, 1.0):
        frame = _side(side)
        inverse = frame.inverted()
        for f in BURNT:
            z = _level(f + 1) - SLAB
            faces = [face for face in mb.bm.faces if z - 0.5 < face.calc_center_median().z < z + 3.5 and abs(abs(face.calc_center_median().y) - HALF_W) < 0.3]
            if not faces:
                continue
            kit.transform_faces(faces, inverse)
            for u in (CUTS[f] - 2.0, CUTS[f] - 5.5, CUTS[f] - 9.0):
                _soot(mb, faces, -side * u, z, 1.4, 3.0)
            kit.transform_faces(faces, frame)


def _entrance(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """La entrada de la fachada sureste: dos puertas de cristal con su montante y la
    marquesina de hormigón."""

    def build(builder: tb.MeshBuilder) -> None:
        z0, z1 = _level(0), _level(1) - SLAB
        for u0, u1, state in ((ENTRANCE[0], ENTRANCE[0] + 1.5, "rota"), (ENTRANCE[0] + 1.5, ENTRANCE[1], "vacia")):
            x0, x1 = u0, u1  # en la fachada sureste, x es u
            kit.window(builder, (x0, z0, x1, z0 + 2.4), "portal", state, rng, depth=0.1, wall=SPANDREL, frame_color=FRAME, sill=False, open_sash=1, open_angle=70.0)
            kit.window(builder, (x0, z0 + 2.4, x1, z1), "escalera", "rota", rng, depth=0.1, wall=SPANDREL, frame_color=FRAME, sill=False)

    _placed(mb, _side(-1.0), build)
    mb.box((ENTRANCE[1] - ENTRANCE[0] + 1.0, 2.4, 0.2), ((ENTRANCE[0] + ENTRANCE[1]) / 2.0, -HALF_W - 1.2, 3.1), CONCRETE, jitter=0.03)
    fascia = [(0.0, 2.92), (-0.08, 2.98), (-0.08, 3.28), (0.0, 3.34)]
    _placed(mb, Matrix.Translation((0.0, -HALF_W - 2.4, 0.0)), lambda b: kit.moulding(b, (ENTRANCE[0] - 0.5, ENTRANCE[1] + 0.5), fascia, CONCRETE_DARK, mitre=True))
    mb.box((ENTRANCE[1] - ENTRANCE[0] + 0.6, 0.6, BASE), ((ENTRANCE[0] + ENTRANCE[1]) / 2.0, -HALF_W - 0.3, BASE / 2.0), GRANITE)


def _gable_wall(mb: tb.MeshBuilder) -> None:
    """El testero suroeste: ciego, de plaqueta gris azulada, con el relieve del átomo y las
    letras НИИ-9."""
    top = _level(FLOORS) + PARAPET

    def build(builder: tb.MeshBuilder) -> None:
        with builder.material(3):
            builder.slab((-HALF_W, HALF_W), (-0.3, top), (0.0, GABLE), TILE_GABLE, step=3.0, jitter=0.02)
        _atom(builder, (0.0, 37.0))
        _inscription(builder, "НИИ-9", 30.6, 2.2)

    _placed(mb, _gable(), build)


def _relief_ring(
    mb: tb.MeshBuilder, center: tuple, rx: float, rz: float, width: float, depth: float, color: str, *, turn: float = 0.0, splay: float = 0.03, samples: int = 48
) -> None:
    """Un anillo elíptico en relieve, de una pieza (hecho de trozos, sus juntas se dibujarían):
    el canto de fuera y el de dentro en derrame y la cara de delante. En el marco de un
    muro: la cara en y = 0 y lo de fuera hacia -y; girado ``turn`` en su plano."""
    cx, cz = center
    c, s = math.cos(turn), math.sin(turn)
    rails = ((0.0, splay, 0.0), (0.0, 0.0, depth), (width, 0.0, depth), (width, -splay, 0.0))

    def point(a: float, shrink: float, push: float, d: float) -> tuple:
        normal = Vector((math.cos(a) / rx, math.sin(a) / rz)).normalized()
        x = (rx - shrink) * math.cos(a) + normal.x * push
        z = (rz - shrink) * math.sin(a) + normal.y * push
        return (cx + x * c - z * s, -d, cz + x * s + z * c)

    for i in range(samples):
        a0, a1 = 2.0 * math.pi * i / samples, 2.0 * math.pi * (i + 1) / samples
        mid = (a0 + a1) / 2.0
        n = Vector((math.cos(mid) / rx, math.sin(mid) / rz)).normalized()
        radial = Vector((n.x * c - n.y * s, 0.0, n.x * s + n.y * c))
        for r, outward in enumerate((radial + Vector((0.0, -1.0, 0.0)), Vector((0.0, -1.0, 0.0)), -radial + Vector((0.0, -1.0, 0.0)))):
            corners = [point(a0, *rails[r]), point(a1, *rails[r]), point(a1, *rails[r + 1]), point(a0, *rails[r + 1])]
            _facing(mb, corners, color, outward)


def _atom(mb: tb.MeshBuilder, center: tuple) -> None:
    """El átomo: tres órbitas y el núcleo, en relieve (las órbitas a fondos distintos para
    que donde se cruzan sus caras no coincidan)."""
    for k, turn in enumerate((0.0, math.pi / 3.0, 2.0 * math.pi / 3.0)):
        _relief_ring(mb, center, 4.4, 1.6, 0.32, 0.12 + 0.03 * k, RELIEF, turn=turn, samples=64)
    profile = [(0.95, 0.0), (0.85, 0.12), (0.8, 0.22), (0.6, 0.3), (0.0, 0.32)]
    mb.lathe(profile, (center[0], 0.0, center[1]), RELIEF, rotation=(90.0, 0.0, 0.0), segments=24, sharp_angle=35.0)
    for k in range(3):  # los electrones
        a = 0.7 + k * 2.1
        turn = k * math.pi / 3.0
        x, z = 4.4 * math.cos(a), 1.6 * math.sin(a)
        at = (center[0] + x * math.cos(turn) - z * math.sin(turn), center[1] + x * math.sin(turn) + z * math.cos(turn))
        mb.lathe([(0.32, 0.0), (0.26, 0.2), (0.0, 0.24)], (at[0], 0.0, at[1]), RELIEF, rotation=(90.0, 0.0, 0.0), segments=16, sharp_angle=35.0)


def _stroke(p: tuple, q: tuple, width: float) -> list:
    d = Vector((q[0] - p[0], q[1] - p[1])).normalized()
    n = Vector((-d.y, d.x)) * (width / 2.0)
    return [(p[0] - n.x, p[1] - n.y), (q[0] - n.x, q[1] - n.y), (q[0] + n.x, q[1] + n.y), (p[0] + n.x, p[1] + n.y)]


def _inscription(mb: tb.MeshBuilder, text: str, z0: float, h: float) -> None:
    """Letras de trazos en relieve: Н, И, el guion y el 9."""
    w, s, gap = h * 0.62, h * 0.16, h * 0.28
    widths = {"-": w * 0.6}
    total = sum(widths.get(c, w) for c in text) + gap * (len(text) - 1)
    x = -total / 2.0
    for letter in text:
        cw = widths.get(letter, w)
        rect = lambda a, b, c, d: [(x + a, z0 + b), (x + c, z0 + b), (x + c, z0 + d), (x + a, z0 + d)]  # noqa: E731
        strokes: list = []
        if letter == "Н":
            strokes = [rect(0.0, 0.0, s, h), rect(cw - s, 0.0, cw, h), rect(s, (h - s) / 2.0, cw - s, (h + s) / 2.0)]
        elif letter == "И":
            strokes = [rect(0.0, 0.0, s, h), rect(cw - s, 0.0, cw, h), _stroke((x + s * 0.6, z0 + s * 0.4), (x + cw - s * 0.6, z0 + h - s * 0.4), s)]
        elif letter == "-":
            strokes = [rect(0.0, h * 0.42, cw, h * 0.42 + s)]
        elif letter == "9":
            _relief_ring(mb, (x + cw / 2.0, z0 + h * 0.68), cw / 2.0, h * 0.32, s, 0.14, RELIEF, splay=0.025, samples=32)
            strokes.append(rect(cw - s, h * 0.1, cw, h * 0.68))
            strokes.append(_stroke((x + cw - s * 0.5, z0 + h * 0.12), (x + s * 0.8, z0 + s * 0.5), s))
        for k, polygon in enumerate(strokes):
            kit.raised(mb, polygon, 0.14 - 0.01 * (k % 3), RELIEF, splay=0.025)
        x += cw + gap


HUT = (WALL_IN, LANDING_U[1] + 0.25, 1.4, 5.4, 3.1)  # la caseta de la azotea: u0, u1, v0, v1, alto
HUT_DOOR = (2.0, 3.0)  # su puerta, en el muro de +u (de través, en v)


def _hut(mb: tb.MeshBuilder) -> None:
    """La caseta de la escalera en la azotea: sus cuatro muros (el de +u, con la puerta que
    mira al cráter) y el techo."""
    u0, u1, v0, v1, height = HUT
    roof = _level(FLOORS)
    door = HUT_DOOR
    hole = [(door[0], roof - 0.1, door[1], roof + DOOR_H)]
    _placed(mb, _across(u1), lambda b: b.slab((v0, v1), (roof, roof + height), (0.0, 0.25), CONCRETE, holes=hole, step=1.5))
    mb.box((0.25, v1 - v0, height), (u0 + 0.125, (v0 + v1) / 2.0, roof + height / 2.0), CONCRETE, jitter=0.03)
    mb.box((u1 - u0, 0.25, height), ((u0 + u1) / 2.0, v0 + 0.125, roof + height / 2.0), CONCRETE, jitter=0.03)
    mb.box((u1 - u0, 0.25, height), ((u0 + u1) / 2.0, v1 - 0.125, roof + height / 2.0), CONCRETE, jitter=0.03)
    mb.box((u1 - u0 + 0.3, v1 - v0 + 0.3, 0.2), ((u0 + u1) / 2.0, (v0 + v1) / 2.0, roof + height + 0.1), CONCRETE, jitter=0.03)


def _roof(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """La albardilla del pretil, la caseta de la escalera (con la puerta hacia el cráter) y
    el mástil de las antenas, doblado por la onda."""
    roof = _level(FLOORS)
    with mb.material(4):
        for side in (-1.0, 1.0):
            mb.box((CUTS[FLOORS] + HALF_L - 0.6, 0.34, 0.06), ((CUTS[FLOORS] - 0.6 - HALF_L) / 2.0, side * (HALF_W - 0.12), roof + PARAPET + 0.03), STEEL)
        mb.box((0.46, 2.0 * HALF_W, 0.06), (-HALF_L + 0.2, 0.0, roof + PARAPET + 0.03), STEEL)
    _hut(mb)
    u1, door = HUT[1], HUT_DOOR
    with mb.material(4):  # la hoja de la puerta, abierta hacia el cráter
        width = door[1] - door[0]
        swing = math.radians(80.0)
        mb.box((width, 0.05, DOOR_H), (u1 + width / 2.0 * math.cos(swing), door[1] + width / 2.0 * math.sin(swing), roof + DOOR_H / 2.0), STEEL, rotation=(0.0, 0.0, 80.0))
        # El mástil: un tubo con travesaños, doblado hacia el suroeste.
        base = Vector((-15.5, -5.5, roof))
        bend = Vector((-0.55, 0.1, 1.0)).normalized()
        knee = base + Vector((0.0, 0.0, 4.2))
        tip = knee + bend * 4.6
        mb.tube([base, knee, tip], 0.07, STEEL, segments=8)
        for t, length in ((0.45, 1.6), (0.8, 1.1)):
            p = knee + (tip - knee) * t
            mb.bar(p - Vector((0.0, length / 2.0, 0.0)), p + Vector((0.0, length / 2.0, 0.0)), 0.025, STEEL, 6)
        for k in range(3):
            a = 2.0 * math.pi * k / 3.0
            mb.bar(knee - Vector((0.0, 0.0, 1.2)), base + Vector((2.2 * math.cos(a), 2.2 * math.sin(a), 0.05)), 0.008, STEEL, 4)


# --------------------------------------------------------------------------
# Por dentro: tabiques, suelos y la escalera
# --------------------------------------------------------------------------


def _wall_end(f: int, rng: random.Random) -> float:
    """Hasta dónde llegan los tabiques largos de la planta ``f`` (entre dos forjados)."""
    return min(CUTS[f], CUTS[f + 1] + 1.5) - rng.uniform(0.2, 0.7)


def _two_tone(builder: tb.MeshBuilder, x_range: tuple, z0: float, z1: float, holes: list, step: float = 1.5) -> None:
    """Un tabique pintado: verde abajo y claro arriba (en su marco, de grueso en y)."""
    for a, b, color in ((z0, z0 + DADO_H, WALL_LOW), (z0 + DADO_H, z1, WALL_HIGH)):
        builder.slab(x_range, (a, b), (-PARTITION / 2.0, PARTITION / 2.0), color, holes=holes, step=step, jitter=0.04)


def _corridor_walls(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """Las paredes del pasillo, con las puertas de cada cuarto, y su final roto."""
    for f in range(FLOORS):
        z0, z1 = _level(f), _level(f + 1) - SLAB
        end = _wall_end(f, rng)
        for side in (-1.0, 1.0):
            v = side * CORRIDOR
            if side > 0.0:
                doors = [STAIR_DOOR, (-9.45, -8.55), (-4.0, -3.1)]
                start = WALL_IN
            else:
                doors = [(-15.3, -14.4), (-9.45, -8.55), (-4.0, -3.1)]
                start = WALL_IN if f > 0 else -12.0  # la planta baja: el vestíbulo, abierto
            split = min(end - 0.5, -1.0)
            holes = [(a, z0 - 0.1, b, z0 + DOOR_H) for a, b in doors if b < split - 0.2]

            def build(builder: tb.MeshBuilder, start=start, split=split, holes=holes, end=end, z0=z0, z1=z1) -> None:
                _two_tone(builder, (start, split), z0, z1, holes)
                for a, b, color in ((z0, z0 + DADO_H, WALL_LOW), (z0 + DADO_H, z1, WALL_HIGH)):
                    _ragged_plate(builder, split, end, a, b, (-PARTITION / 2.0, PARTITION / 2.0), color, rng, reach=0.3)

            _placed(mb, Matrix.Translation((0.0, v, 0.0)), build)


def _partitions(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """Los tabiques de través entre los cuartos: enteros si los dos forjados siguen; si no,
    rotos por arriba."""
    for f in range(FLOORS):
        z0, z1 = _level(f), _level(f + 1) - SLAB
        for u in PARTITION_U:
            if u + 0.3 > CUTS[f]:
                continue
            whole = u + 0.3 < CUTS[f + 1]
            for v0, v1 in ((CORRIDOR + PARTITION / 2.0, INNER), (-INNER, -CORRIDOR - PARTITION / 2.0)):

                def build(builder: tb.MeshBuilder, v0=v0, v1=v1, whole=whole, z0=z0, z1=z1) -> None:
                    if whole:
                        _two_tone(builder, (v0, v1), z0, z1, [])
                        return
                    builder.slab((v0, v1), (z0, z0 + DADO_H), (-PARTITION / 2.0, PARTITION / 2.0), WALL_LOW, step=1.5, jitter=0.04)
                    top = kit.broken_edge(v0, v1, z0 + DADO_H + 0.25, z0 + 2.5, rng, step=0.35)
                    kit.broken_slab(builder, (v0, v1), z0 + DADO_H, top, (-PARTITION / 2.0, PARTITION / 2.0), WALL_HIGH)

                _placed(mb, _across(u), build)


def _floors(mb: tb.MeshBuilder) -> None:
    """Los suelos de cada planta, a 3 mm sobre el forjado: terrazo en el pasillo y en la
    escalera, linóleo en los laboratorios y parqué en los despachos. Acaban antes del borde
    roto (el hormigón queda a la vista)."""
    up = Vector((0.0, 0.0, 1.0))
    for f in range(FLOORS):
        z = _level(f) + 0.003
        end = CUTS[f] - 0.75
        rects = [((WALL_IN, -CORRIDOR), (end, CORRIDOR), TERRAZZO)]
        for side in (-1.0, 1.0):
            v0, v1 = sorted((side * (CORRIDOR + 0.08), side * INNER))
            rooms = [(-12.0, -6.0, LINOLEUM), (-6.0, end, PARQUET if (f + int(side > 0)) % 2 else LINOLEUM)]
            if side > 0.0:  # la escalera: alrededor de su hueco
                rects += [((LANDING_U[0], v0), (-12.0, v1), TERRAZZO), ((WALL_IN, STAIR_HOLE[3]), (LANDING_U[0], v1), TERRAZZO)]
                if f == 0:
                    rects.append(((WALL_IN, v0), (LANDING_U[0], STAIR_HOLE[3]), TERRAZZO))
            else:
                rooms.insert(0, (WALL_IN, -12.0, TERRAZZO if f == 0 else "#7C7C74"))
            for u0, u1, color in rooms:
                if u1 - u0 > 0.3:
                    rects.append(((u0, v0), (min(u1, end), v1), color))
        for (u0, v0), (u1, v1), color in rects:
            if u1 - u0 < 0.2:
                continue
            _facing(mb, [(u0, v0, z), (u1, v0, z), (u1, v1, z), (u0, v1, z)], color, up, cuts=2)


def _stairs(mb: tb.MeshBuilder) -> None:
    """La escalera de dos tramos, de la planta baja a la azotea: peldaños, la losa de debajo,
    los descansillos y la barandilla del ojo."""
    for f in range(FLOORS):
        z = _level(f)
        mid = z + RISERS * RISER
        mb.box((MID_U[1] - MID_U[0], STAIR_HOLE[3] - STAIR_HOLE[1], 0.2), ((MID_U[0] + MID_U[1]) / 2.0, (STAIR_HOLE[1] + STAIR_HOLE[3]) / 2.0, mid - 0.1), CONCRETE, jitter=0.03)
        for (v0, v1), start, direction, base in ((FLIGHT_A, LANDING_U[0], -1.0, z), (FLIGHT_B, MID_U[1], 1.0, mid)):
            width = v1 - v0
            for i in range(RISERS - 1):
                u = start + direction * TREAD * (i + 0.5)
                top = base + RISER * (i + 1)
                mb.box((TREAD, width, RISER + 0.12), (u, (v0 + v1) / 2.0, top - (RISER + 0.12) / 2.0), TERRAZZO, jitter=0.02)
            # La losa inclinada de debajo.
            run = TREAD * (RISERS - 1)
            rise = RISER * RISERS
            length = math.hypot(run, rise)
            angle = math.degrees(math.atan2(rise, run))
            center = (start + direction * run / 2.0, (v0 + v1) / 2.0, base + rise / 2.0 - 0.22)
            mb.box((length, width, 0.15), center, CONCRETE, rotation=(0.0, -angle * direction, 0.0), jitter=0.03)
            # La barandilla del ojo: barrotes y el pasamanos.
            rail_v = v1 - 0.05 if v1 < 3.4 else v0 + 0.05
            with mb.material(4):
                for i in range(0, RISERS - 1, 2):
                    u = start + direction * TREAD * (i + 0.5)
                    foot = base + RISER * (i + 1)
                    mb.bar((u, rail_v, foot), (u, rail_v, foot + 0.9), 0.012, STEEL, 4)
                a = (start, rail_v, base + 0.9)
                b = (start + direction * run, rail_v, base + rise - RISER + 0.9)
                mb.bar(a, b, 0.025, "#3A2C22", 6)


# --------------------------------------------------------------------------
# Las cosas: muebles y equipo, sobre todo en los cuartos abiertos al vacío
# --------------------------------------------------------------------------


def _bench(mb: tb.MeshBuilder, center: tuple, length: float, depth: float, turn: float) -> None:
    """Una mesa de laboratorio: el cuerpo de armarios y la encimera oscura que vuela."""
    x, y, z = center
    mb.box((length, depth - 0.06, 0.82), (x, y, z + 0.41), "#5A645E", rotation=(0.0, 0.0, turn), bevel=0.01, jitter=0.05)
    mb.box((length + 0.04, depth, 0.05), (x, y, z + 0.845), "#2A2C2A", rotation=(0.0, 0.0, turn), jitter=0.05)


def _desk(mb: tb.MeshBuilder, center: tuple, turn: float, tilt: float = 0.0) -> None:
    x, y, z = center
    before = set(mb.bm.faces)
    mb.box((1.2, 0.7, 0.04), (0.0, 0.0, 0.74), "#6A5038", jitter=0.06)
    mb.box((0.4, 0.66, 0.7), (0.38, 0.0, 0.36), "#5E4632", jitter=0.06)
    for dx in (-0.56,):
        mb.box((0.04, 0.66, 0.72), (dx, 0.0, 0.36), "#5E4632", jitter=0.06)
    kit.transform_faces([f for f in mb.bm.faces if f not in before], Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Rotation(math.radians(tilt), 4, "X"))


def _chair(mb: tb.MeshBuilder, center: tuple, turn: float, fallen: bool) -> None:
    x, y, z = center
    before = set(mb.bm.faces)
    mb.box((0.42, 0.42, 0.04), (0.0, 0.0, 0.45), "#5A4636", jitter=0.08)
    mb.box((0.42, 0.04, 0.45), (0.0, 0.19, 0.7), "#5A4636", jitter=0.08)
    for dx in (-0.18, 0.18):
        for dy in (-0.18, 0.18):
            mb.box((0.03, 0.03, 0.45), (dx, dy, 0.225), "#3A2C22")
    tilt = Matrix.Translation((0.0, 0.0, 0.22)) @ Matrix.Rotation(math.radians(90.0), 4, "X") if fallen else Matrix()
    kit.transform_faces([f for f in mb.bm.faces if f not in before], Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ tilt)


def _cabinet(mb: tb.MeshBuilder, center: tuple, turn: float, color: str, height: float = 2.0) -> None:
    x, y, z = center
    mb.box((0.9, 0.45, height), (x, y, z + height / 2.0), color, rotation=(0.0, 0.0, turn), bevel=0.01, jitter=0.06)


def _room(mb: tb.MeshBuilder, rng: random.Random, f: int, u0: float, u1: float, side: float, kind: str) -> None:
    """Lo que hay en un cuarto (de u0 a u1, al lado ``side`` del pasillo): un laboratorio
    (mesas largas bajo las ventanas, una isla, la vitrina de gases, armarios) o un despacho
    (mesas, sillas, estanterías). Junto al borde roto, las cosas se han movido."""
    z = _level(f)
    inner, outer = side * (CORRIDOR + 0.6), side * (INNER - 0.5)
    open_room = u1 > CUTS[f] - 1.5
    length = (u1 - 0.3) - (u0 + 0.3)
    if length < 1.0:
        return
    if kind == "laboratorio":
        _bench(mb, ((u0 + u1) / 2.0 - 0.2, outer, z), min(length, 4.6), 0.8, 0.0)
        island = min(length - 1.4, 2.6)
        if island > 1.0:
            turn = rng.uniform(-25.0, 25.0) if open_room else 0.0
            _bench(mb, ((u0 + u1) / 2.0, (inner + outer) / 2.0, z), island, 1.2, turn)
            with mb.material(3):  # los estantes de reactivos encima
                mb.box((island * 0.8, 0.25, 0.5), ((u0 + u1) / 2.0, (inner + outer) / 2.0, z + 1.12), "#6C706A", rotation=(0.0, 0.0, turn), jitter=0.05)
        with mb.material(3):  # la vitrina de gases, contra el tabique
            mb.box((0.8, 1.2, 2.2), (u0 + 0.45, inner + side * 1.0, z + 1.1), "#7A7E76", bevel=0.01, jitter=0.05)
        with mb.material(1):
            front = u0 + 0.853
            _facing(mb, [(front, inner + side * 0.5, z + 0.95), (front, inner + side * 1.5, z + 0.95), (front, inner + side * 1.5, z + 1.75), (front, inner + side * 0.5, z + 1.75)], "#1F2228", Vector((1.0, 0.0, 0.0)))
        for k in range(rng.randint(2, 4)):
            _chair(mb, (rng.uniform(u0 + 0.6, u1 - 0.6), rng.uniform(min(inner, outer), max(inner, outer)), z), rng.uniform(0.0, 360.0), rng.random() < 0.4)
    else:
        for k in range(2):
            u = u0 + (k + 0.5) * length / 2.0 + 0.3
            if u > u1 - 0.6:
                continue
            tilt = rng.uniform(-8.0, 8.0) if open_room else 0.0
            _desk(mb, (u, (inner + outer) / 2.0 + side * 0.6, z), 90.0 * side + rng.uniform(-10.0, 10.0), tilt)
            _chair(mb, (u - 0.2, (inner + outer) / 2.0 - side * 0.1, z), rng.uniform(0.0, 360.0), rng.random() < 0.3)
        _cabinet(mb, (u0 + 0.3, inner + side * 1.2, z), 90.0, "#6A5038")
        _cabinet(mb, (u0 + 0.3, inner + side * 2.2, z), 90.0, "#6A5038", 1.8)
        with mb.material(3):  # la caja fuerte
            mb.box((0.6, 0.6, 1.1), (u0 + 0.45, outer - side * 0.1, z + 0.55), "#4F5652", bevel=0.01)
    # Papeles por el suelo.
    for _ in range(rng.randint(4, 10)):
        u, v = rng.uniform(u0 + 0.3, min(u1, CUTS[f] - 0.8)), rng.uniform(min(inner, outer), max(inner, outer))
        a = rng.uniform(0.0, math.pi)
        c, s = math.cos(a) * 0.15, math.sin(a) * 0.15
        d, e = -math.sin(a) * 0.105, math.cos(a) * 0.105
        _facing(mb, [(u - c - d, v - s - e, z + 0.006), (u + c - d, v + s - e, z + 0.006), (u + c + d, v + s + e, z + 0.006), (u - c + d, v - s + e, z + 0.006)], "#BDB6A2", Vector((0.0, 0.0, 1.0)))


def _things(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """Las cosas de todas las plantas: laboratorios y despachos a los dos lados del pasillo,
    la portería de la planta baja y algún armario volcado en el pasillo."""
    for f in range(FLOORS):
        for side in (-1.0, 1.0):
            kinds = ("laboratorio", "despacho") if (f + int(side > 0)) % 2 else ("despacho", "laboratorio")
            for (u0, u1), kind in zip(((-12.0, -6.0), (-6.0, CUTS[f] - 0.4)), kinds):
                if u1 - u0 > 1.2:
                    _room(mb, rng, f, u0 + PARTITION, u1, side, kind)
        if f > 0 and rng.random() < 0.6:
            u = rng.uniform(-11.0, CUTS[f] - 2.0)
            _cabinet(mb, (u, rng.uniform(-0.6, 0.6), _level(f) + 0.22), rng.uniform(0.0, 180.0), "#7A7E76", 0.45)
    # La portería del vestíbulo: el mostrador y la percha del guardarropa.
    z = _level(0)
    mb.box((2.4, 0.6, 1.1), (-14.5, -4.2, z + 0.55), "#6A5038", bevel=0.02, jitter=0.05)
    with mb.material(3):
        for k in range(6):
            mb.bar((-17.0 + k * 0.5, -8.2, z), (-17.0 + k * 0.5, -8.2, z + 1.7), 0.02, STEEL, 5)
        mb.bar((-17.1, -8.2, z + 1.65), (-14.4, -8.2, z + 1.65), 0.02, STEEL, 5)


# --------------------------------------------------------------------------
# Los escombros: la mitad que se cayó, al pie del corte
# --------------------------------------------------------------------------


MOUND_START = CUTS[3] - 4.2  # el montón entra en las plantas bajas como una ladera


def _mound_height(u: float, v: float) -> float:
    """El montón de cascotes al pie del corte: alto junto a él, bajando hacia la bomba y,
    hacia dentro, en ladera por las plantas bajas hasta el suelo."""
    along = u - CUTS[3]
    peak = 6.5 * math.exp(-((max(along, 0.0) - 1.5) / 6.5) ** 2)
    if along < 0.0:
        peak *= max(0.0, 1.0 + along / 4.0)
    core = peak * max(0.0, 1.0 - (v / 10.5) ** 2)
    rough = 0.9 * noise.noise(Vector((u * 0.35, v * 0.35, 3.1))) * min(1.0, peak / 2.0)
    return max(0.0, core + rough) + 0.02


def _rubble(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """El montón (una rejilla de cascote), losas caídas con su ferralla, pilares tumbados,
    trozos de antepecho con su plaqueta y cascotes sueltos."""
    up = Vector((0.0, 0.0, 1.0))
    us = [MOUND_START + k * 0.75 for k in range(int((HALF_L - MOUND_START) / 0.75) + 1)]
    vs = [-HALF_W + k * 0.75 for k in range(int(2.0 * HALF_W / 0.75) + 1)]
    for a, b in zip(us, us[1:]):
        for c, d in zip(vs, vs[1:]):
            corners = [(a, c, _mound_height(a, c)), (b, c, _mound_height(b, c)), (b, d, _mound_height(b, d)), (a, d, _mound_height(a, d))]
            _facing(mb, corners, CONCRETE_DARK, up)
    for _ in range(26):  # losas caídas
        u, v = rng.uniform(CUTS[2], HALF_L - 1.5), rng.uniform(-HALF_W + 1.0, HALF_W - 1.0)
        size = (rng.uniform(1.8, 4.2), rng.uniform(1.2, 3.0), SLAB)
        z = _mound_height(u, v) + 0.1
        turn = (rng.uniform(-40.0, 40.0), rng.uniform(-35.0, 35.0), rng.uniform(0.0, 180.0))
        mb.box(size, (u, v, z), CONCRETE, rotation=turn, jitter=0.06)
        for _ in range(rng.randint(1, 3)):
            kit.rebar(mb, (u, v, z), (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.2, 0.8)), rng.uniform(0.6, 1.5), rng, radius=0.012)
    for _ in range(7):  # pilares tumbados
        u, v = rng.uniform(CUTS[2] + 1.0, HALF_L - 2.0), rng.uniform(-HALF_W + 1.0, HALF_W - 1.0)
        mb.box((COLUMN, COLUMN, rng.uniform(2.0, 3.1)), (u, v, _mound_height(u, v) + 0.25), CONCRETE, rotation=(rng.uniform(60.0, 100.0), rng.uniform(-20.0, 20.0), rng.uniform(0.0, 180.0)), jitter=0.05)
    with mb.material(1):  # trozos de antepecho con su plaqueta
        for _ in range(9):
            u, v = rng.uniform(CUTS[2], HALF_L - 1.0), rng.choice((-1.0, 1.0)) * rng.uniform(5.0, HALF_W)
            mb.box((rng.uniform(1.4, 3.0), SPANDREL, SILL + SLAB), (u, v, _mound_height(u, v) + 0.3), TILE, rotation=(rng.uniform(-70.0, 70.0), rng.uniform(-30.0, 30.0), rng.uniform(0.0, 180.0)), jitter=0.05)
    for _ in range(220):  # cascotes
        u, v = rng.uniform(CUTS[3] - 0.5, HALF_L), rng.uniform(-HALF_W - 0.5, HALF_W + 0.5)
        kit.chunk(mb, (u, v, _mound_height(u, v) + 0.05), rng.uniform(0.2, 0.7), rng.choice((CONCRETE, CONCRETE_DARK, "#8A6A58")), rng)


# --------------------------------------------------------------------------
# Colisión
# --------------------------------------------------------------------------


def _collision(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """Lo que se pisa y lo que para: los forjados (hasta el borde), los antepechos (llegan a
    la cintura), el testero, los tabiques con sus puertas, los pilares, la escalera (rampas
    entre los descansillos), la caseta de la azotea y el montón de escombros."""
    for f in range(FLOORS + 1):
        top = _level(f)
        thickness = 0.45 if f == 0 else SLAB
        holes = [] if f == 0 else [STAIR_HOLE]
        end = CUTS[f] - 0.35
        _placed(mb, _flat(top), lambda b, end=end, holes=holes, thickness=thickness: b.slab((-HALF_L, end), (-HALF_W, HALF_W), (0.0, thickness), CONCRETE, holes=holes))
        for side in (-1.0, 1.0):
            height = PARAPET if f == FLOORS else SILL
            spans = [(-HALF_L, ENTRANCE[0]), (ENTRANCE[1], end)] if f == 0 and side < 0.0 else [(-HALF_L, end)]
            for a, b in spans:
                mb.box((b - a, SPANDREL, height + thickness), ((a + b) / 2.0, side * (HALF_W - SPANDREL / 2.0), top + (height - thickness) / 2.0), CONCRETE)
    mb.box((GABLE, 2.0 * HALF_W, _level(FLOORS) + PARAPET + 0.3), (-HALF_L + GABLE / 2.0, 0.0, (_level(FLOORS) + PARAPET - 0.3) / 2.0), CONCRETE)
    for f in range(FLOORS):
        z0, z1 = _level(f), _level(f + 1) - SLAB
        end = min(CUTS[f], CUTS[f + 1] + 1.5) - 0.5
        for side in (-1.0, 1.0):
            doors = [STAIR_DOOR, (-9.45, -8.55), (-4.0, -3.1)] if side > 0.0 else [(-15.3, -14.4), (-9.45, -8.55), (-4.0, -3.1)]
            start = WALL_IN if side > 0.0 or f > 0 else -12.0
            holes = [(a, z0 - 0.1, b, z0 + DOOR_H) for a, b in doors if b < end - 0.2]
            _placed(mb, Matrix.Translation((0.0, side * CORRIDOR, 0.0)), lambda b, start=start, end=end, holes=holes, z0=z0, z1=z1: b.slab((start, end), (z0, z1), (-PARTITION / 2.0, PARTITION / 2.0), CONCRETE, holes=holes))
        for u in PARTITION_U:
            if u + 0.3 < min(CUTS[f], CUTS[f + 1]):
                for v0, v1 in ((CORRIDOR, INNER), (-INNER, -CORRIDOR)):
                    _placed(mb, _across(u), lambda b, v0=v0, v1=v1, z0=z0, z1=z1: b.slab((v0, v1), (z0, z1), (-PARTITION / 2.0, PARTITION / 2.0), CONCRETE))
        for u in COLUMN_U:
            if u + COLUMN / 2.0 < min(CUTS[f], CUTS[f + 1]) - 0.5:
                for v in COLUMN_V:
                    mb.box((COLUMN, COLUMN, z1 - z0), (u, v, (z0 + z1) / 2.0), CONCRETE)
        # La escalera: el descansillo y los dos tramos como rampas.
        mid = z0 + RISERS * RISER
        mb.box((MID_U[1] - MID_U[0], STAIR_HOLE[3] - STAIR_HOLE[1], 0.2), ((MID_U[0] + MID_U[1]) / 2.0, (STAIR_HOLE[1] + STAIR_HOLE[3]) / 2.0, mid - 0.1), CONCRETE)
        run = TREAD * (RISERS - 1)
        for (v0, v1), start, direction, base in ((FLIGHT_A, LANDING_U[0], -1.0, z0), (FLIGHT_B, MID_U[1], 1.0, mid)):
            length = math.hypot(run, RISERS * RISER)
            angle = math.degrees(math.atan2(RISERS * RISER, run))
            center = (start + direction * run / 2.0, (v0 + v1) / 2.0, base + RISERS * RISER / 2.0 - 0.05)
            mb.box((length + 0.1, v1 - v0, 0.1), center, CONCRETE, rotation=(0.0, -angle * direction, 0.0))
    _hut(mb)
    # El montón: la rejilla, más gruesa.
    up = Vector((0.0, 0.0, 1.0))
    us = [MOUND_START + k * 1.5 for k in range(int((HALF_L - MOUND_START) / 1.5) + 1)]
    vs = [-HALF_W + k * 1.5 for k in range(int(2.0 * HALF_W / 1.5) + 1)]
    for a, b in zip(us, us[1:]):
        for c, d in zip(vs, vs[1:]):
            _facing(mb, [(a, c, _mound_height(a, c)), (b, c, _mound_height(b, c)), (b, d, _mound_height(b, d)), (a, d, _mound_height(a, d))], CONCRETE, up)


# --------------------------------------------------------------------------
# La biblioteca
# --------------------------------------------------------------------------


def _snow(position: Vector, normal: Vector) -> float:
    """El alfa: en el suelo (``nevado_parcial``), cuánta nieve ha entrado (junto al borde
    roto y junto a las ventanas reventadas; la azotea, entera); en la cara de fuera de los
    antepechos, la plaqueta."""
    p = _from_plan(position)
    n = _from_plan(normal)
    if n.z > 0.7:
        f = max(0, min(FLOORS, round((p.z - BASE) / STOREY)))
        if f == FLOORS:
            return 1.0
        edge = max(0.0, 1.0 - (CUTS[f] - p.x) / 3.5)
        window = max(0.0, (abs(p.y) - (HALF_W - 2.0)) / 1.75) * 0.55
        return min(1.0, max(edge, window))
    if abs(abs(p.y) - HALF_W) < 0.004 and abs(n.y) > 0.9:
        return 1.0
    if abs(p.x + HALF_L) < 0.004 and n.x < -0.9:
        return 1.0
    return 0.0


def build_kit() -> object:
    lib = kit.KitLibrary("singular_partido", columns=4, spacing=60.0)
    # La estructura, las fachadas y lo de dentro.
    rng = random.Random(901)
    mb = tb.MeshBuilder(seed=901)
    for f in range(FLOORS + 1):
        edge = _edge(f, rng)
        _slab(mb, f, edge, CONCRETE)
        if f > 0:
            _rebar_fringe(mb, edge, _level(f), rng)
        if f in HANGING:
            _hanging(mb, f, edge, rng)
    _columns(mb, rng)
    ends = _spandrels(mb, rng)
    _ribbon_windows(mb, rng, ends)
    _burns(mb)
    _entrance(mb, rng)
    _gable_wall(mb)
    _roof(mb, rng)
    with mb.material(5):
        _corridor_walls(mb, rng)
        _partitions(mb, rng)
    _floors(mb)
    _stairs(mb)
    _to_plan(mb)
    piece = mb.finish("partido", kit.materials("nevado_parcial", "vidrio", "interior", "azulejo", "metal", "sala"))
    tb.stain(piece, "#2A2522", amount=0.45, scale=0.7, coverage=0.35, seed=901, stretch_z=0.3)
    lib.add(piece, [], alpha=_snow, samples=6, ao=0.5, ao_distance=1.0, ground_z=0.0, seed=901)
    # Las cosas.
    mb = tb.MeshBuilder(seed=902)
    with mb.material(0):
        _things(mb, random.Random(902))
    _to_plan(mb)
    piece = mb.finish("partido_cosas", kit.materials("sala", "vidrio", "interior", "metal"))
    lib.add(piece, [], samples=6, ao=0.5, ao_distance=0.6, seed=902)
    # Los escombros.
    mb = tb.MeshBuilder(seed=903)
    _rubble(mb, random.Random(903))
    _to_plan(mb)
    piece = mb.finish("partido_escombros", kit.materials("nevado", "azulejo"))
    tb.stain(piece, "#3A332C", amount=0.4, scale=1.2, coverage=0.4, seed=903)
    lib.add(piece, [], alpha=lambda position, normal: 1.0 if abs(normal.z) < 0.5 else 0.0, samples=6, ao=0.6, ao_distance=0.8, ground_z=0.0, seed=903)
    # La colisión (no se dibuja).
    mb = tb.MeshBuilder(seed=904)
    _collision(mb, random.Random(904))
    _to_plan(mb)
    lib.add(mb.finish("partido_colision", kit.materials("colision")), [], samples=1, seed=904)
    return lib.root


def models() -> dict:
    return {"singular_partido": build_kit}
