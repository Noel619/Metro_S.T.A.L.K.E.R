"""Los vehículos de la evacuación: los que se quedaron en el atasco, en las cocheras, en
las vías y en el río helado, abandonados hace dos años (README, «La ambientación de la
superficie»).

Ninguno es un modelo real: se parecen a los de una ciudad soviética de provincias (el
autobús de morro chato, el trolebús de ventanas largas, el tranvía de dos colores, el
camión de cabina redonda, la furgoneta «hogaza», el blindado de ocho ruedas, el camión de
bomberos con su escalera, el material del ferrocarril y los barcos del río).

Todos con lo que les han hecho dos inviernos: óxido en las juntas y los bajos, la mitad
de los cristales rotos (queda el negro del interior), ruedas pinchadas, abolladuras y
nieve encima (la pone el material «nevado»). Los quemados ya no tienen pintura ni goma:
chapa parda con hollín y ceniza, ningún cristal, y descansan sobre las llantas.

Coordenadas de Blender: X hacia delante (a lo largo del vehículo), Y a la izquierda, Z
arriba; el origen en el suelo, en el centro (los del ferrocarril, en lo alto del carril;
los barcos, en la línea del hielo, con el casco metido debajo). La caja de colisión es
la medida del vehículo: la maqueta escala cada modelo a lo que mide en el plano
(CityProps).
"""

from __future__ import annotations

import math
import random
from typing import Callable

import bmesh
import bpy
from mathutils import Vector

import tumansk_bpy as tb

SNOW = "#B9B4A6"
GLASS = "#1E2126"
HOLE = "#0B0A0B"
TYRE = "#1C1B1B"
HUB = "#4C4A47"
CHASSIS = "#2B2927"
RUST = "#7A3F27"
RUST_DARK = "#4E2A1C"
SOOT = "#1E1B19"
ASH = "#8A857B"
CHROME = "#7E807F"
LAMP = "#8C8A78"
#: Lo que queda de la pintura de un vehículo quemado (se mezcla con su color).
BURNT = "#3A3330"
#: Radio de la llanta de un quemado respecto al de la rueda (la goma ardió).
RIM = 0.64


def _material() -> bpy.types.Material:
    """El de la nieve en lo de arriba: el color lo llevan los vértices."""
    return tb.material("nevado", SNOW)


def _mix(a: str, b: str, t: float) -> str:
    """Mezcla dos colores hexadecimales (``t`` = 0 es ``a``)."""
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


class Paint:
    """Los colores de un vehículo. Quemado, de la pintura queda un poco bajo el hollín y
    el óxido, y no queda ni un cristal."""

    def __init__(self, seed: int, burnt: bool) -> None:
        self.rng = random.Random(seed)
        self.burnt = burnt

    def __call__(self, color: str) -> str:
        return _mix(color, BURNT, 0.82) if self.burnt else color

    def glass(self, broken: float) -> str:
        return HOLE if self.burnt or self.rng.random() < broken else GLASS

    def drop(self, radius: float) -> float:
        """Lo que baja un quemado sobre las llantas de radio ``radius`` (nada si no ardió)."""
        return radius * (1.0 - RIM) if self.burnt else 0.0


def _solid(
    mb: tb.MeshBuilder,
    outline: list[tuple[float, float]],
    thickness: float,
    center: tuple[float, float, float],
    color: str,
    *,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    cuts: int = 2,
    shape: Callable[[Vector], None] | None = None,
) -> list:
    """Un prisma (``MeshBuilder.prism``) con las caras partidas en ``cuts``: las manchas, las
    abolladuras y la oclusión se pintan por vértice. ``shape`` deforma cada vértice (los
    cascos en V, los costados que se cierran hacia arriba)."""
    before = set(mb.bm.faces)
    faces = mb.prism(outline, thickness, center, color, rotation=rotation)
    if shape is not None:
        for vert in dict.fromkeys(v for f in faces for v in f.verts):
            shape(vert.co)
    if cuts > 0:
        edges = list(dict.fromkeys(e for f in faces for e in f.edges))
        bmesh.ops.subdivide_edges(mb.bm, edges=edges, cuts=cuts, use_grid_fill=True)
    return mb._finish_piece(before, color, 0.0, smooth=False)


def _shell(mb: tb.MeshBuilder, size: tuple[float, float, float], center: tuple[float, float, float], color: str,
           bevel: float, cuts: int = 3) -> list:
    """La chapa: una caja con las esquinas redondeadas y las caras partidas."""
    return mb.box(size, center, color, bevel=bevel, segments=2, cuts=cuts, jitter=0.03)


def _windows(mb: tb.MeshBuilder, paint: Paint, side: float, z0: float, z1: float,
             spans: list[tuple[float, float, int]], broken: float, frame: str, gap: float = 0.08) -> None:
    """Ventanas en el costado ``side`` (la y de la chapa, con su signo). ``spans`` son los
    tramos (x0, x1, cuántas): cristales oscuros o, los rotos, el negro de dentro, con
    montantes entre ellos."""
    out = 1.0 if side > 0 else -1.0
    zc, height = (z0 + z1) / 2.0, z1 - z0
    for x0, x1, count in spans:
        step = (x1 - x0) / count
        for k in range(count):
            mb.box((step - gap, 0.02, height), (x0 + step * (k + 0.5), side + out * 0.012, zc), paint.glass(broken))
        for k in range(count + 1):
            mb.box((gap, 0.03, height + 0.04), (x0 + step * k, side + out * 0.017, zc), paint(frame))


def _door(mb: tb.MeshBuilder, paint: Paint, side: float, x: float, width: float, z0: float, z1: float,
          color: str, broken: float = 0.6) -> None:
    """Una puerta de dos hojas en el costado ``side``, con sus cristales (casi siempre
    rotos: se rompían para salir)."""
    out = 1.0 if side > 0 else -1.0
    mb.box((width, 0.03, z1 - z0), (x, side + out * 0.015, (z0 + z1) / 2.0), paint(color))
    pane_z = z0 + (z1 - z0) * 0.6
    for dx in (-width / 4.0, width / 4.0):
        mb.box((width / 2.0 - 0.12, 0.02, (z1 - z0) * 0.55), (x + dx, side + out * 0.035, pane_z),
               paint.glass(broken))


def _arch(mb: tb.MeshBuilder, x: float, side: float, radius: float, bottom: float) -> None:
    """El paso de rueda: la sombra del hueco sobre la rueda, en el costado."""
    out = 1.0 if side > 0 else -1.0
    mb.box((radius * 2.3, 0.02, radius * 0.9), (x, side + out * 0.006, bottom + radius * 0.45), HOLE)


def _sink(mb: tb.MeshBuilder, paint: Paint, radius: float) -> None:
    """Un quemado ya no tiene goma: todo lo hecho baja hasta que las llantas tocan el
    suelo (las ruedas se ponen después)."""
    if paint.burnt:
        drop = paint.drop(radius)
        bmesh.ops.translate(mb.bm, vec=Vector((0.0, 0.0, -drop)), verts=list(mb.bm.verts))


def _wheel(mb: tb.MeshBuilder, paint: Paint, x: float, y: float, radius: float, width: float,
           flat: float = 0.35, twin: bool = False) -> None:
    """Una rueda (o dos gemelas) en (x, y): la cubierta y el tapacubos. Las pinchadas se
    aplastan contra el suelo; las de un quemado son solo la llanta oxidada."""
    side = 1.0 if y > 0 else -1.0
    offsets = (0.0, -side * (width + 0.03)) if twin else (0.0,)
    for dy in offsets:
        if paint.burnt:
            rim = radius * RIM
            mb.cylinder(rim, width * 0.8, (x, y + dy, rim), RUST_DARK, rotation=(90.0, 0.0, 0.0), segments=14)
            mb.cylinder(rim * 0.55, width * 0.85, (x, y + dy, rim), HUB, rotation=(90.0, 0.0, 0.0), segments=10)
            continue
        squash = 0.82 if paint.rng.random() < flat else 1.0
        center = (x, y + dy, radius * squash)
        tyre = mb.cylinder(radius, width, center, TYRE, rotation=(90.0, 0.0, 0.0), segments=18)
        if squash < 1.0:
            for vert in dict.fromkeys(v for f in tyre for v in f.verts):
                vert.co.z = max(vert.co.z, 0.0)
        mb.cylinder(radius * 0.48, width + 0.02, center, HUB, rotation=(90.0, 0.0, 0.0), segments=12)


def _smoke(xs: list[float], z: float, width: float) -> list:
    """El hollín que subió por encima de cada ventana de un quemado (``z``, lo alto de las
    ventanas)."""
    return [((x, 0.0, z), width, 0.7) for x in xs]


def _finish(mb: tb.MeshBuilder, name: str, root: bpy.types.Object, seed: int, size: tuple[float, float, float],
            paint: Paint, rust: float = 0.7, smoke: list | None = None, base: float = 0.0) -> bpy.types.Object:
    """Cierra el modelo: el óxido (y en los quemados el hollín, la ceniza y el humo que
    salió por las ventanas), una abolladura, la colisión y la luz. ``base`` es la z de
    abajo de la caja de colisión (los cascos de los barcos siguen bajo el hielo)."""
    obj = mb.finish(name, _material(), root)
    tb.stain(obj, RUST, amount=rust, scale=1.4, coverage=0.36, seed=seed)
    tb.stain(obj, RUST_DARK, amount=rust * 0.6, scale=4.0, coverage=0.22, seed=seed + 7, stretch_z=0.4)
    if paint.burnt:
        tb.stain(obj, RUST, amount=0.6, scale=0.9, coverage=0.4, seed=seed + 11)
        tb.stain(obj, ASH, amount=0.5, scale=2.2, coverage=0.25, seed=seed + 13)
        tb.stain(obj, SOOT, amount=0.9, scale=1.1, coverage=0.5, seed=seed + 3)
        if smoke:
            tb.scorch(obj, smoke)
    length, width, height = size
    tb.dent(obj, (length * 0.42, -width * 0.5, base + height * 0.45), radius=0.6, depth=0.07)
    tb.collision_box(name, size, (0.0, 0.0, base + height / 2.0), root)
    tb.paint({obj: None}, samples=12, seed=seed)
    return obj


# --------------------------------------------------------------------------
# Por la calle
# --------------------------------------------------------------------------


def build_bus(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Autobús urbano de morro chato: crema con la franja roja, ventanas corridas, tres
    puertas plegables a la derecha y el letrero de la línea, apagado."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    body, stripe, frame, door = paint("#A99E7C"), paint("#73392B"), "#8E866C", "#4D4A40"
    _shell(mb, (11.2, 2.48, 2.15), (0.0, 0.0, 1.625), body, 0.14)
    _shell(mb, (10.9, 2.36, 0.3), (-0.05, 0.0, 2.83), paint("#958C70"), 0.14, 2)
    for y in (-1.24, 1.24):
        out = 1.0 if y > 0 else -1.0
        mb.box((11.0, 0.03, 0.22), (0.0, y + out * 0.01, 1.08), stripe)
        for x in (3.2, -2.6):
            _arch(mb, x, y, 0.5, 0.6)
    _windows(mb, paint, 1.24, 1.62, 2.52, [(-5.2, 4.9, 8)], 0.45, frame)
    _windows(mb, paint, -1.24, 1.62, 2.52, [(-3.6, -0.1, 3), (1.35, 4.05, 2)], 0.45, frame)
    for x in (-4.35, 0.6, 4.75):
        _door(mb, paint, -1.24, x, 1.15, 0.62, 2.62, door)
    mb.box((0.03, 2.2, 1.0), (5.615, 0.0, 2.05), paint.glass(0.5))
    mb.box((0.03, 2.0, 0.7), (-5.615, 0.0, 2.15), paint.glass(0.4))
    mb.box((0.04, 1.4, 0.24), (5.62, 0.0, 2.72), "#16181A")
    mb.box((0.03, 1.8, 0.4), (-5.615, 0.0, 1.0), "#1F1E1C")
    for y in (-0.85, 0.85):
        mb.cylinder(0.11, 0.06, (5.62, y, 0.95), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
    for y in (-1.0, 1.0):
        mb.bar((5.55, y * 1.2, 2.45), (5.85, y * 1.42, 2.45), 0.02, CHASSIS, 5)
        mb.box((0.05, 0.2, 0.36), (5.86, y * 1.44, 2.25), CHASSIS)
    for x in (5.66, -5.66):
        mb.box((0.18, 2.5, 0.22), (x, 0.0, 0.7), paint(CHROME), bevel=0.03)
    mb.box((10.6, 2.2, 0.3), (0.0, 0.0, 0.5), CHASSIS)
    _sink(mb, paint, 0.5)
    for x, twin in ((3.2, False), (-2.6, True)):
        for y in (-1.05, 1.05):
            _wheel(mb, paint, x, y, 0.5, 0.3, 0.4, twin)
    smoke = _smoke([-4.6 + 1.3 * k for k in range(8)], 2.52 - paint.drop(0.5), 0.9)
    _finish(mb, name, root, seed, (11.5, 2.5, 3.0), paint, smoke=smoke)
    return root


def build_trolleybus(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Trolebús de ventanas largas: blanco sucio con la franja gris azulada, la caja de
    los equipos en el techo y las dos pértigas, una en su gancho y la otra suelta hacia
    arriba."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    body, band, frame, door = paint("#A8A69A"), paint("#4C5A64"), "#8F8D82", "#45443E"
    _shell(mb, (11.6, 2.48, 2.3), (0.0, 0.0, 1.7), body, 0.12)
    _shell(mb, (11.2, 2.3, 0.26), (0.0, 0.0, 2.98), paint("#9A988D"), 0.1, 2)
    mb.box((3.6, 1.6, 0.42), (-1.2, 0.0, 3.32), paint("#707269"), bevel=0.05)
    for y in (-1.24, 1.24):
        out = 1.0 if y > 0 else -1.0
        mb.box((11.4, 0.03, 0.3), (0.0, y + out * 0.01, 1.12), band)
        for x in (3.6, -2.4):
            _arch(mb, x, y, 0.52, 0.6)
    _windows(mb, paint, 1.24, 1.72, 2.68, [(-5.4, 5.0, 8)], 0.5, frame)
    _windows(mb, paint, -1.24, 1.72, 2.68, [(-5.5, -4.15, 1), (-2.6, -0.05, 2), (1.3, 4.0, 2)], 0.5, frame)
    for x in (-3.4, 0.6, 4.65):
        _door(mb, paint, -1.24, x, 1.2, 0.62, 2.78, door)
    mb.box((0.03, 2.2, 1.1), (5.815, 0.0, 2.15), paint.glass(0.5))
    mb.box((0.03, 2.0, 0.8), (-5.815, 0.0, 2.2), paint.glass(0.4))
    mb.box((0.04, 1.4, 0.24), (5.82, 0.0, 2.84), "#16181A")
    for y in (-0.85, 0.85):
        mb.cylinder(0.11, 0.06, (5.82, y, 0.95), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
    # Las pértigas: arrancan del techo hacia atrás; una sigue en su gancho y la otra se
    # soltó y apunta al cielo.
    base = (-2.6, 0.0, 3.55)
    mb.box((0.4, 0.9, 0.18), base, "#3C3D3A")
    mb.bar((base[0], -0.28, 3.62), (base[0] - 5.6, -0.3, 3.72), 0.035, "#2C2D2B", 6)
    mb.box((0.2, 0.3, 0.12), (base[0] - 3.2, -0.3, 3.64), "#2C2D2B")
    mb.bar((base[0], 0.28, 3.62), (base[0] - 4.8, 0.55, 6.1), 0.035, "#2C2D2B", 6)
    for x in (5.86, -5.86):
        mb.box((0.18, 2.5, 0.22), (x, 0.0, 0.7), paint(CHROME), bevel=0.03)
    mb.box((11.0, 2.2, 0.3), (0.0, 0.0, 0.5), CHASSIS)
    _sink(mb, paint, 0.52)
    for x, twin in ((3.6, False), (-2.4, True)):
        for y in (-1.05, 1.05):
            _wheel(mb, paint, x, y, 0.52, 0.3, 0.45, twin)
    smoke = _smoke([-4.5 + 1.3 * k for k in range(8)], 2.68 - paint.drop(0.52), 0.9)
    _finish(mb, name, root, seed, (12.0, 2.5, 3.6), paint, smoke=smoke)
    return root


#: Planta del tranvía: los extremos se estrechan hacia el testero.
TRAM_OUTLINE = [(-7.4, -0.95), (-6.2, -1.28), (6.2, -1.28), (7.4, -0.95), (7.4, 0.95), (6.2, 1.28),
                (-6.2, 1.28), (-7.4, 0.95)]


def build_tram(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Tranvía de dos colores: rojo abajo y crema arriba, los testeros estrechos con su
    parabrisas, tres puertas a la derecha, el pantógrafo plegado y los dos bogies bajo el
    faldón."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    low, high, frame, door = paint("#743A2E"), paint("#AFA387"), "#8B8068", "#3E3A33"
    _solid(mb, TRAM_OUTLINE, 1.0, (0.0, 0.0, 1.0), low, cuts=3)
    _solid(mb, TRAM_OUTLINE, 1.42, (0.0, 0.0, 2.19), high, cuts=3)
    roof = [(x * 0.97, y * 0.92) for x, y in TRAM_OUTLINE]
    _solid(mb, roof, 0.32, (0.0, 0.0, 3.04), paint("#9C927A"), cuts=2)
    _windows(mb, paint, 1.28, 1.75, 2.75, [(-6.1, 6.1, 10)], 0.45, frame)
    _windows(mb, paint, -1.28, 1.75, 2.75, [(-6.1, -5.35, 1), (-3.95, -0.7, 3), (0.7, 3.95, 3), (5.35, 6.1, 1)],
             0.45, frame)
    for x in (-4.65, 0.0, 4.65):
        _door(mb, paint, -1.28, x, 1.3, 0.55, 2.8, door)
    # Los testeros: el parabrisas de frente y los dos de los lados, que siguen la planta.
    for end in (1.0, -1.0):
        mb.box((0.03, 1.6, 1.05), (end * 7.415, 0.0, 2.25), paint.glass(0.5))
        mb.box((0.04, 1.2, 0.22), (end * 7.42, 0.0, 2.95), "#16181A")
        for side in (1.0, -1.0):
            angle = math.degrees(math.atan2(0.33, 1.2)) * end * side
            normal = Vector((0.33 * end, 1.2 * side, 0.0)).normalized()
            center = Vector((end * 6.8, side * 1.115, 2.25)) + normal * 0.015
            mb.box((1.05, 0.02, 0.95), tuple(center), paint.glass(0.5), rotation=(0.0, 0.0, -angle))
        for y in (-0.6, 0.6):
            mb.cylinder(0.1, 0.06, (end * 7.42, y, 1.05), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
        mb.box((0.25, 1.3, 0.22), (end * 7.48, 0.0, 0.62), CHASSIS)
    # El pantógrafo plegado: el rombo de barras sobre su base.
    mb.box((1.4, 1.2, 0.14), (0.0, 0.0, 3.27), "#3D3C39")
    for y in (-0.5, 0.5):
        mb.bar((-0.6, y, 3.35), (0.3, y, 3.6), 0.025, "#2A2A28", 5)
        mb.bar((0.3, y, 3.6), (0.9, y, 3.45), 0.025, "#2A2A28", 5)
    mb.bar((0.9, -0.75, 3.47), (0.9, 0.75, 3.47), 0.03, "#2A2A28", 5)
    for x in (4.4, -4.4):
        mb.box((2.6, 1.3, 0.3), (x, 0.0, 0.5), CHASSIS)
        for dx in (-0.9, 0.9):
            for y in (-0.76, 0.76):
                mb.cylinder(0.35, 0.12, (x + dx, y, 0.35), "#2F2C29", rotation=(90.0, 0.0, 0.0), segments=14)
    smoke = _smoke([-5.5 + 1.22 * k for k in range(10)], 2.75, 0.9)
    _finish(mb, name, root, seed, (15.0, 2.6, 3.5), paint, smoke=smoke)
    return root


def build_truck(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Camión de cabina redonda con el capó delante y la caja de tablas, con los arcos del
    toldo y lo que queda de la lona a jirones (en el quemado, ni lona ni la mitad de las
    tablas)."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    cab, wood, tarp = paint("#4E6461"), paint("#5B4A39"), "#55573E"
    # Capó, guardabarros, cabina y parabrisas.
    _shell(mb, (1.6, 1.7, 0.75), (3.1, 0.0, 1.38), cab, 0.12)
    for y in (-0.95, 0.95):
        mb.box((1.3, 0.5, 0.22), (3.05, y, 1.08), cab, bevel=0.08)
    _shell(mb, (1.55, 2.3, 1.4), (1.75, 0.0, 1.75), cab, 0.16)
    mb.box((0.03, 1.8, 0.55), (2.54, 0.0, 2.05), paint.glass(0.5))
    for y in (-1.15, 1.15):
        mb.box((0.8, 0.02, 0.48), (1.8, y + (0.012 if y > 0 else -0.012), 2.05), paint.glass(0.5))
    mb.box((0.03, 1.2, 0.5), (3.915, 0.0, 1.3), "#1F1E1C")
    mb.box((0.15, 2.3, 0.2), (3.98, 0.0, 0.85), paint(CHROME), bevel=0.03)
    for y in (-0.6, 0.6):
        mb.cylinder(0.11, 0.06, (3.92, y, 1.5), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
    # La caja: el suelo, los laterales de tablas y los arcos del toldo.
    mb.box((5.0, 2.45, 0.12), (-1.55, 0.0, 1.35), wood)
    for y in (-1.2, 1.2):
        for k in range(3):
            if burnt and paint.rng.random() < 0.45:
                continue
            mb.box((5.0, 0.05, 0.17), (-1.55, y, 1.5 + k * 0.2), wood, jitter=0.1)
    for x in (-4.0, 0.9):
        for k in range(3):
            mb.box((0.05, 2.45, 0.17), (x, 0.0, 1.5 + k * 0.2), wood, jitter=0.1)
    for x in (-3.8, -2.6, -1.4, -0.2, 0.8):
        mb.bar((x, -1.2, 2.0), (x, -1.2, 3.0), 0.025, "#3A3A36", 5)
        mb.bar((x, 1.2, 2.0), (x, 1.2, 3.0), 0.025, "#3A3A36", 5)
        mb.bar((x, -1.2, 3.0), (x, 1.2, 3.0), 0.025, "#3A3A36", 5)
    if not burnt:
        mb.box((2.6, 2.46, 0.04), (0.0, 0.0, 3.02), tarp, rotation=(4.0, 0.0, 0.0))
        for _ in range(4):
            mb.box((0.5, 0.02, paint.rng.uniform(0.4, 0.9)), (paint.rng.uniform(-3.5, 0.5), 1.22, 2.6), tarp,
                   rotation=(0.0, paint.rng.uniform(-8, 8), 0.0))
    mb.box((7.4, 1.0, 0.25), (0.0, 0.0, 0.75), CHASSIS)
    _sink(mb, paint, 0.5)
    for x, twin in ((3.0, False), (-2.6, True)):
        for y in (-0.98, 0.98):
            _wheel(mb, paint, x, y, 0.5, 0.3, 0.4, twin)
    _finish(mb, name, root, seed, (8.0, 2.5, 3.1), paint, smoke=_smoke([1.8], 2.3 - paint.drop(0.5), 1.2))
    return root


def build_van(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """La furgoneta «hogaza»: una caja de esquinas muy redondas, verde oliva, con el morro
    chato, sus ventanillas y la rueda de repuesto atrás."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    body = paint("#626549")
    _shell(mb, (5.0, 2.0, 1.75), (0.0, 0.0, 1.3), body, 0.32)
    mb.box((0.03, 1.3, 0.4), (2.505, 0.0, 1.62), paint.glass(0.5))
    for side in (1.0, -1.0):
        _windows(mb, paint, side, 1.42, 1.8, [(-1.9, 1.7, 4)], 0.4, body, 0.12)
    for y in (-0.72, 0.72):
        mb.cylinder(0.1, 0.06, (2.505, y, 1.2), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
    mb.box((0.12, 2.0, 0.16), (2.52, 0.0, 0.62), CHASSIS, bevel=0.03)
    mb.box((4.6, 1.6, 0.25), (0.0, 0.0, 0.48), CHASSIS)
    if not burnt:
        mb.cylinder(0.36, 0.22, (-2.6, 0.0, 1.05), TYRE, rotation=(0.0, 90.0, 0.0), segments=16)
    _sink(mb, paint, 0.4)
    for x in (1.45, -1.45):
        for y in (-0.88, 0.88):
            _wheel(mb, paint, x, y, 0.4, 0.24, 0.35)
    smoke = _smoke([-1.45, -0.55, 0.35, 1.25], 1.8 - paint.drop(0.4), 0.8)
    _finish(mb, name, root, seed, (5.2, 2.1, 2.2), paint, smoke=smoke)
    return root


#: Perfil del casco del blindado (x, z): la proa en cuña y la popa inclinada; la parte de
#: arriba se cierra hacia el techo.
BTR_LOW = [(-3.55, 0.6), (2.95, 0.6), (3.75, 1.15), (3.45, 1.32), (-3.7, 1.32)]
BTR_HIGH = [(-3.68, 1.3), (3.47, 1.3), (2.55, 1.85), (-2.95, 1.85)]


def build_armoured() -> bpy.types.Object:
    """El blindado de ocho ruedas del control junto al metro: el casco de chapas inclinadas
    con la proa en cuña, la torreta pequeña con su ametralladora, las escotillas y el verde
    que ya es óxido."""
    root = tb.empty("blindado-estatico")
    paint = Paint(851, False)
    mb = tb.MeshBuilder(seed=851)
    hull = "#4D5540"
    upright = (90.0, 0.0, 0.0)
    _solid(mb, BTR_LOW, 2.7, (0.0, 0.0, 0.0), hull, rotation=upright, cuts=3)

    def slope(co: Vector) -> None:
        if co.z > 1.5:
            co.y *= 0.8

    _solid(mb, BTR_HIGH, 2.7, (0.0, 0.0, 0.0), hull, rotation=upright, cuts=2, shape=slope)
    mb.cylinder(0.55, 0.45, (0.9, 0.0, 2.07), hull, segments=14, radius_top=0.46)
    mb.bar((1.4, 0.0, 2.12), (3.4, 0.0, 2.2), 0.05, "#2E302A", 8)
    for x, r in ((2.1, 0.3), (-1.2, 0.34), (-2.3, 0.34)):
        mb.cylinder(r, 0.08, (x, 0.0, 1.88), "#3E4434", segments=12)
    for y in (-1.0, 1.0):
        mb.box((0.9, 0.02, 0.62), (0.1, y * 1.358, 1.0), "#353A2D")
        mb.cylinder(0.1, 0.08, (3.3, y * 0.85, 1.32), LAMP, rotation=(0.0, 60.0, 0.0), segments=10)
    for y in (-1.38, 1.38):
        for x in (2.55, 1.2, -1.0, -2.35):
            _wheel(mb, paint, x, y, 0.55, 0.36, 0.3)
    _finish(mb, "blindado", root, 851, (7.5, 3.1, 2.4), paint)
    return root


def build_fire_engine(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Camión de bomberos: cabina roja, la caja con las persianas de los armarios, la
    escalera de aluminio encima y la devanadera atrás. Dos ardieron con lo que apagaban."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    red = paint("#7A2C25")
    _shell(mb, (1.5, 1.8, 0.75), (3.75, 0.0, 1.38), red, 0.12)
    _shell(mb, (1.6, 2.4, 1.55), (2.35, 0.0, 1.85), red, 0.16)
    mb.box((0.03, 2.0, 0.6), (3.165, 0.0, 2.2), paint.glass(0.4))
    for y in (-1.2, 1.2):
        mb.box((0.9, 0.02, 0.5), (2.4, y + (0.012 if y > 0 else -0.012), 2.2), paint.glass(0.4))
    mb.box((0.25, 0.9, 0.14), (2.4, 0.0, 2.7), paint("#3B4A6B"))
    _shell(mb, (5.6, 2.45, 1.85), (-1.45, 0.0, 1.85), red, 0.1)
    for y in (-1.225, 1.225):
        out = 1.0 if y > 0 else -1.0
        for k in range(4):
            mb.box((1.1, 0.03, 1.2), (-3.6 + k * 1.38, y + out * 0.015, 1.8), paint("#6E6A62"))
    for y in (-0.45, 0.45):
        mb.bar((-4.0, y, 2.9), (2.8, y, 2.95), 0.04, paint("#8E918F"), 6)
    for k in range(18):
        x = -3.9 + k * 0.38
        mb.bar((x, -0.45, 2.92), (x, 0.45, 2.92), 0.018, paint("#8E918F"), 4)
    mb.cylinder(0.4, 1.6, (-4.45, 0.0, 1.05), paint("#4A2622"), rotation=(90.0, 0.0, 0.0), segments=16)
    mb.box((0.15, 2.4, 0.2), (4.55, 0.0, 0.85), paint(CHROME), bevel=0.03)
    mb.box((8.4, 1.0, 0.3), (0.0, 0.0, 0.75), CHASSIS)
    _sink(mb, paint, 0.5)
    for x, twin in ((3.4, False), (-2.4, True)):
        for y in (-1.0, 1.0):
            _wheel(mb, paint, x, y, 0.5, 0.3, 0.6, twin)
    smoke = _smoke([2.4, -3.6, -1.5, 0.6], 2.45 - paint.drop(0.5), 1.2)
    _finish(mb, name, root, seed, (9.3, 2.5, 3.0), paint, rust=0.8, smoke=smoke)
    return root


# --------------------------------------------------------------------------
# En las vías (el origen, en lo alto del carril)
# --------------------------------------------------------------------------


def _bogie(mb: tb.MeshBuilder, x: float, axles: int, spacing: float, radius: float) -> None:
    """Un bogie: el bastidor y sus ejes, con las ruedas sobre los carriles (1520 mm)."""
    mb.box((spacing * (axles - 1) + 1.2, 2.2, 0.45), (x, 0.0, radius + 0.15), CHASSIS)
    for k in range(axles):
        ax = x + (k - (axles - 1) / 2.0) * spacing
        for y in (-0.76, 0.76):
            mb.cylinder(radius, 0.13, (ax, y, radius), "#2E2B28", rotation=(90.0, 0.0, 0.0), segments=16)


def build_boxcar() -> bpy.types.Object:
    """Vagón cerrado de mercancías: la caja de nervios verticales, color óxido, la puerta
    corredera entreabierta en el centro y el techo combado."""
    root = tb.empty("vagon-estatico")
    paint = Paint(871, False)
    mb = tb.MeshBuilder(seed=871)
    mb.box((13.8, 2.9, 2.75), (0.0, 0.0, 2.55), "#664636", cuts=6)
    _shell(mb, (13.9, 2.95, 0.35), (0.0, 0.0, 4.02), "#5A4034", 0.15, 2)
    for y in (-1.45, 1.45):
        out = 1.0 if y > 0 else -1.0
        for k in range(15):
            mb.box((0.08, 0.04, 2.7), (-6.5 + k * 0.93, y + out * 0.02, 2.55), "#5A3E31")
        mb.box((2.0, 0.06, 2.4), (0.6 * -out, y + out * 0.07, 2.45), "#4E372B")
        mb.box((0.7, 0.02, 2.3), (0.75 * out, y + out * 0.012, 2.4), HOLE)
    mb.box((14.0, 2.6, 0.35), (0.0, 0.0, 1.08), CHASSIS)
    for x in (-6.9, 6.9):
        mb.box((0.35, 0.4, 0.3), (x, 0.0, 1.05), "#3A3634")
        for y in (-0.9, 0.9):
            mb.cylinder(0.17, 0.3, (x * 1.02, y, 1.05), "#3A3634", rotation=(0.0, 90.0, 0.0), segments=10)
    for x in (4.9, -4.9):
        _bogie(mb, x, 2, 1.85, 0.475)
    _finish(mb, "vagon", root, 871, (14.0, 3.0, 4.2), paint, rust=0.9)
    return root


def build_coach(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Coche de viajeros: verde con la franja amarilla, la fila de ventanas (casi todas
    rotas), las puertas en las puntas y el techo redondo. Los del tren que no salió
    ardieron con las maletas dentro."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    body, stripe, frame = paint("#4C5A47"), paint("#9B8B4E"), "#3F4A3B"
    _shell(mb, (23.6, 3.05, 2.9), (0.0, 0.0, 2.65), body, 0.1, 6)
    _shell(mb, (23.4, 2.9, 0.5), (0.0, 0.0, 4.2), paint("#556052"), 0.24, 4)
    for side in (-1.525, 1.525):
        out = 1.0 if side > 0 else -1.0
        mb.box((23.0, 0.03, 0.12), (0.0, side + out * 0.01, 2.05), stripe)
        _windows(mb, paint, side, 2.35, 3.25, [(-9.6, 9.6, 16)], 0.65, frame, 0.18)
        for x in (-10.9, 10.9):
            mb.box((0.8, 0.03, 2.1), (x, side + out * 0.015, 2.4), paint("#33392F"))
            mb.box((0.5, 0.02, 0.6), (x, side + out * 0.035, 2.95), paint.glass(0.6))
    mb.box((23.8, 2.7, 0.35), (0.0, 0.0, 1.1), CHASSIS)
    for x in (8.8, -8.8):
        _bogie(mb, x, 2, 2.4, 0.475)
    smoke = _smoke([-9.0 + 1.2 * k for k in range(16)], 3.25, 1.0)
    _finish(mb, name, root, seed, (24.0, 3.1, 4.5), paint, smoke=smoke)
    return root


def build_locomotive(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Locomotora diésel de maniobras: el capó largo y estrecho, la cabina de lado a lado
    cerca de una punta, las pasarelas con su barandilla, las franjas rojas y los dos bogies
    de tres ejes."""
    root = tb.empty(f"{name}-estatico")
    paint = Paint(seed, burnt)
    mb = tb.MeshBuilder(seed=seed)
    body, stripe = paint("#3C483B"), paint("#7A3329")
    mb.box((16.6, 3.0, 0.3), (0.0, 0.0, 1.3), CHASSIS)
    _shell(mb, (9.4, 2.1, 2.5), (-2.6, 0.0, 2.7), body, 0.12, 4)
    _shell(mb, (2.8, 3.0, 3.1), (3.35, 0.0, 3.0), body, 0.12)
    _shell(mb, (2.9, 2.1, 1.9), (6.5, 0.0, 2.4), body, 0.12)
    for side in (-1.5, 1.5):
        out = 1.0 if side > 0 else -1.0
        _windows(mb, paint, side, 3.3, 4.1, [(2.2, 4.5, 2)], 0.5, "#2F382E", 0.14)
        mb.box((16.4, 0.03, 0.18), (0.0, side + out * 0.015, 1.3), stripe)
    for x in (4.765, 1.935):
        mb.box((0.03, 2.6, 0.8), (x, 0.0, 3.75), paint.glass(0.5))
    for side in (-1.42, 1.42):
        for k in range(12):
            x = -7.8 + k * 1.4
            mb.bar((x, side, 1.45), (x, side, 2.4), 0.02, "#2E2C29", 4)
        mb.bar((-7.8, side, 2.4), (7.8, side, 2.4), 0.025, "#2E2C29", 4)
    for k in range(5):
        mb.box((0.9, 1.6, 0.06), (-6.2 + k * 1.6, 0.0, 3.97), "#2F362E")
    mb.cylinder(0.18, 0.5, (-0.6, 0.0, 4.15), "#262624", segments=10)
    for x in (8.3, -8.3):
        mb.box((0.3, 2.2, 0.35), (x, 0.0, 1.15), CHASSIS)
    for y in (-0.6, 0.6):
        mb.cylinder(0.12, 0.06, (7.97, y, 3.0), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
        mb.cylinder(0.12, 0.06, (-7.32, y, 3.6), paint(LAMP), rotation=(0.0, 90.0, 0.0), segments=10)
    for x in (5.4, -5.4):
        _bogie(mb, x, 3, 1.85, 0.525)
    _finish(mb, name, root, seed, (17.0, 3.1, 4.5), paint, rust=0.75, smoke=_smoke([2.8, 3.9], 4.1, 1.2))
    return root


# --------------------------------------------------------------------------
# En el río helado (el origen, en la línea del hielo)
# --------------------------------------------------------------------------


def _v_hull(beam: float, bottom: float) -> Callable[[Vector], None]:
    """Cierra el casco por el fondo: abajo mide ``beam`` del ancho de arriba (y algo
    menos de largo)."""

    def shape(co: Vector) -> None:
        if co.z < bottom + 0.01:
            co.y *= beam
            co.x *= 0.96

    return shape


def _hull(mb: tb.MeshBuilder, outline: list[tuple[float, float]], top: float, bottom: float, color: str,
          beam: float, cuts: int = 3) -> None:
    """Casco de barco: los costados rectos hasta la línea del hielo (z = 0) y, debajo, la
    obra viva cerrándose en V hasta ``bottom`` (no se ve: queda en el hielo)."""
    _solid(mb, outline, top + 0.02, (0.0, 0.0, (top - 0.02) / 2.0), color, cuts=cuts)
    _solid(mb, outline, -bottom, (0.0, 0.0, bottom / 2.0), color, cuts=1, shape=_v_hull(beam, bottom))


def _ring(outline: list[tuple[float, float]], z: float, grow: float = 1.0) -> list[tuple[float, float, float]]:
    """El contorno cerrado a la altura ``z`` (la borda, una franja, una regala)."""
    points = [(x * grow, y * grow, z) for x, y in outline]
    return points + [points[0]]


def build_rowboat() -> bpy.types.Object:
    """Barca de remos de madera, con la nieve hasta la borda y los bancos asomando."""
    root = tb.empty("barca-estatico")
    paint = Paint(901, False)
    mb = tb.MeshBuilder(seed=901)
    outline = [(-2.4, -0.62), (0.9, -0.8), (2.0, -0.45), (2.5, 0.0), (2.0, 0.45), (0.9, 0.8), (-2.4, 0.62)]
    _solid(mb, outline, 0.8, (0.0, 0.0, 0.1), "#4F5F63", cuts=2, shape=_v_hull(0.5, -0.3))
    mb.tube(_ring(outline, 0.52, 1.015), 0.04, "#3A3128", segments=6)
    for x in (-0.9, 0.6):
        mb.box((0.25, 1.35, 0.05), (x, 0.0, 0.53), "#5A4A3A")
    mb.box((0.35, 1.0, 0.05), (-2.05, 0.0, 0.53), "#5A4A3A")
    _finish(mb, "barca", root, 901, (5.0, 1.6, 0.85), paint, rust=0.25, base=-0.3)
    return root


#: Perfil de la barcaza (x, z): la proa de cuchara y la popa recta.
BARGE_PROFILE = [(-29.6, -1.2), (26.5, -1.2), (30.0, 1.0), (30.0, 1.5), (-30.0, 1.5), (-30.0, -0.6)]


def build_barge() -> bpy.types.Object:
    """Barcaza de carga: el casco de acero con la proa de cuchara, la brazola de la bodega y
    las tapas de las escotillas, alguna caída dentro."""
    root = tb.empty("barcaza-estatico")
    paint = Paint(911, False)
    mb = tb.MeshBuilder(seed=911)
    _solid(mb, BARGE_PROFILE, 12.0, (0.0, 0.0, 0.0), "#3E3935", rotation=(90.0, 0.0, 0.0), cuts=6)
    mb.box((46.0, 9.6, 0.9), (-1.0, 0.0, 1.94), "#4A4440", cuts=4)
    for k in range(8):
        x = -21.1 + k * 5.73
        if paint.rng.random() < 0.3:
            mb.box((5.5, 9.3, 0.02), (x, 0.0, 2.4), HOLE)
            mb.box((5.5, 9.3, 0.15), (x, 0.0, 2.2), "#56504A", rotation=(8.0, 0.0, 0.0))
            continue
        mb.box((5.5, 9.4, 0.15), (x, paint.rng.uniform(-0.15, 0.15), 2.46), "#56504A",
               rotation=(0.0, 0.0, paint.rng.uniform(-1.5, 1.5)))
    for x in (-28.5, 27.0):
        for y in (-5.3, 5.3):
            mb.cylinder(0.18, 0.5, (x, y, 1.75), "#2E2A27", segments=10)
    _finish(mb, "barcaza", root, 911, (60.0, 12.0, 3.8), paint, rust=0.95, base=-1.2)
    return root


#: Planta del remolcador: la popa redonda y la proa afilada.
TUG_OUTLINE = [(-11.0, -2.2), (-10.2, -3.2), (5.0, -3.5), (9.0, -2.4), (11.0, 0.0), (9.0, 2.4), (5.0, 3.5),
               (-10.2, 3.2), (-11.0, 2.2)]


def build_tug() -> bpy.types.Object:
    """Remolcador de río: el casco negro con neumáticos colgados de defensa, la caseta con
    sus portillos, el puente de mando acristalado, la chimenea con la franja roja y el
    mástil."""
    root = tb.empty("remolcador-estatico")
    paint = Paint(921, False)
    mb = tb.MeshBuilder(seed=921)
    _hull(mb, TUG_OUTLINE, 1.3, -1.6, "#2E2C2B", 0.6)
    mb.tube(_ring(TUG_OUTLINE, 1.36, 1.005), 0.07, "#7A3329", segments=6)
    white, frame = "#A6A194", "#8A8578"
    mb.box((7.5, 4.4, 2.0), (-1.5, 0.0, 2.29), white, bevel=0.05, cuts=3)
    for y in (-2.21, 2.21):
        for k in range(5):
            mb.cylinder(0.17, 0.04, (-4.5 + k * 1.5, y, 2.45), paint.glass(0.4), rotation=(90.0, 0.0, 0.0),
                        segments=10)
    mb.box((3.0, 4.0, 1.9), (1.0, 0.0, 4.23), white, bevel=0.04, cuts=2)
    mb.box((3.4, 4.3, 0.12), (1.0, 0.0, 5.24), "#55524B")
    _windows(mb, paint, 2.0, 4.0, 4.9, [(-0.3, 2.3, 3)], 0.5, frame)
    _windows(mb, paint, -2.0, 4.0, 4.9, [(-0.3, 2.3, 3)], 0.5, frame)
    mb.box((0.03, 3.4, 0.85), (2.515, 0.0, 4.5), paint.glass(0.6))
    mb.cylinder(0.55, 2.4, (-3.6, 0.0, 4.48), "#3A2E2A", segments=14)
    mb.cylinder(0.57, 0.45, (-3.6, 0.0, 5.2), "#6E2E26", segments=14)
    mb.bar((1.6, 0.0, 5.3), (1.4, 0.0, 7.6), 0.06, "#2E2C29", 6)
    mb.bar((1.42, -0.9, 7.0), (1.42, 0.9, 7.0), 0.04, "#2E2C29", 5)
    mb.box((0.8, 1.2, 0.5), (-8.5, 0.0, 1.54), "#2E2A27")
    for x in (-8.0, -5.6, -3.2, -0.8, 1.6, 4.0):
        half = 3.2 + (x + 10.2) / 15.2 * 0.3
        for side in (-1.0, 1.0):
            mb.cylinder(0.38, 0.22, (x, side * (half + 0.13), 0.75), TYRE, rotation=(90.0, 0.0, 0.0), segments=14)
    _finish(mb, "remolcador", root, 921, (22.0, 7.0, 9.2), paint, rust=0.9, base=-1.6)
    return root


#: Planta del barco de pasajeros.
BOAT_OUTLINE = [(-18.0, -2.8), (-17.0, -3.7), (8.0, -4.0), (14.5, -2.6), (18.0, 0.0), (14.5, 2.6), (8.0, 4.0),
                (-17.0, 3.7), (-18.0, 2.8)]


def build_riverboat() -> bpy.types.Object:
    """Barco de pasajeros del río: el casco gris azulado con su franja, el salón con la
    fila de ventanas, la cubierta de arriba con su salón pequeño y el puente, y la
    barandilla de proa, con algún barrote menos."""
    root = tb.empty("barco-estatico")
    paint = Paint(931, False)
    mb = tb.MeshBuilder(seed=931)
    cream, frame = "#ADA690", "#8F8977"
    _hull(mb, BOAT_OUTLINE, 1.2, -1.3, "#3B4650", 0.7, cuts=4)
    mb.tube(_ring(BOAT_OUTLINE, 0.9, 1.006), 0.07, "#A49E8C", segments=6)
    mb.box((25.0, 7.0, 2.3), (-3.0, 0.0, 2.34), cream, bevel=0.06, cuts=4)
    for side in (-3.5, 3.5):
        _windows(mb, paint, side, 1.9, 2.95, [(-15.0, 9.0, 12)], 0.55, frame, 0.14)
    for y in (-2.0, 0.0, 2.0):
        mb.box((0.03, 1.6, 1.0), (9.515, y, 2.45), paint.glass(0.6))
    mb.box((14.0, 6.0, 2.1), (-5.0, 0.0, 4.53), cream, bevel=0.05, cuts=3)
    for side in (-3.0, 3.0):
        _windows(mb, paint, side, 4.0, 5.0, [(-11.5, 1.5, 7)], 0.55, frame, 0.14)
    mb.box((3.2, 4.0, 1.8), (3.6, 0.0, 4.38), cream, bevel=0.05, cuts=2)
    mb.box((0.03, 3.4, 0.8), (5.215, 0.0, 4.7), paint.glass(0.6))
    mb.box((3.5, 4.3, 0.12), (3.6, 0.0, 5.34), "#5E5A50")
    mb.bar((3.8, 0.0, 5.4), (3.6, 0.0, 7.4), 0.06, "#2E2C29", 6)
    # La barandilla de la cubierta de arriba, delante del puente, con algún hueco.
    for k in range(5):
        for y in (-3.4, 3.4):
            if paint.rng.random() < 0.15:
                continue
            x = 5.4 + k * 0.9
            mb.bar((x, y, 3.5), (x, y, 4.5), 0.025, "#3A3936", 4)
    for y in (-3.4, 3.4):
        mb.bar((5.4, y, 4.5), (9.0, y, 4.5), 0.03, "#3A3936", 4)
    mb.bar((9.0, -3.4, 4.5), (9.0, 3.4, 4.5), 0.03, "#3A3936", 4)
    _finish(mb, "barco", root, 931, (36.0, 8.0, 8.7), paint, rust=0.8, base=-1.3)
    return root


def models() -> dict:
    return {
        "autobus": lambda: build_bus("autobus", 801, False),
        "autobus_quemado": lambda: build_bus("autobus_quemado", 802, True),
        "trolebus": lambda: build_trolleybus("trolebus", 811, False),
        "tranvia": lambda: build_tram("tranvia", 821, False),
        "tranvia_quemado": lambda: build_tram("tranvia_quemado", 822, True),
        "camion": lambda: build_truck("camion", 831, False),
        "camion_quemado": lambda: build_truck("camion_quemado", 832, True),
        "furgoneta": lambda: build_van("furgoneta", 841, False),
        "furgoneta_quemado": lambda: build_van("furgoneta_quemado", 842, True),
        "blindado": build_armoured,
        "bombero": lambda: build_fire_engine("bombero", 861, False),
        "bombero_quemado": lambda: build_fire_engine("bombero_quemado", 862, True),
        "vagon": build_boxcar,
        "coche_tren": lambda: build_coach("coche_tren", 881, False),
        "coche_tren_quemado": lambda: build_coach("coche_tren_quemado", 882, True),
        "locomotora": lambda: build_locomotive("locomotora", 891, False),
        "locomotora_quemado": lambda: build_locomotive("locomotora_quemado", 892, True),
        "barca": build_rowboat,
        "barcaza": build_barge,
        "remolcador": build_tug,
        "barco": build_riverboat,
    }
