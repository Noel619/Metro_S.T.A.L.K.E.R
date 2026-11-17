"""Los detalles de la red de tránsito: tapas de registro, sumideros y las piezas de las vías.

Coordenadas de Blender: X a la derecha, Y hacia delante, Z hacia arriba (en Godot, la
Y de Blender es -Z). Todas las piezas se colocan como instancias desde la red de
tránsito (CityTransit), así que su origen es el punto por el que se colocan:

- Tapas y sumideros: en la superficie que se pisa, la cara de arriba a ras (asoman unos
  milímetros, como el hierro gastado de la calle). Los pozos abiertos (la tapa ya no está):
  el marco a ras y la boca negra. Las tapas sueltas, tiradas al lado: apoyan en el suelo.
- Bordillo suelto: una pieza de granito de un metro tumbada en la calzada (a lo largo de Y),
  apoyada en el suelo.
- Traviesas: el origen es lo alto del asiento del carril (donde apoya el patín); la
  traviesa va a lo largo de X, de lado a lado de la vía.
- Traviesa de madera de los desvíos: un metro de largo en X, para estirarla a lo que
  haga falta, con el carril apoyado en lo alto (el origen).
- Corazón del desvío (de marca 1/9 o 1/6): el origen es el punto matemático en lo alto
  del carril; las dos vías se separan hacia +Y, una a cada lado.
- Palanca del cambio: a ras de lo alto de las traviesas, junto a la punta de las agujas.
- Tope: en el eje de la vía y a lo alto del carril, sobre los últimos metros de la vía
  (que llega por -Y): el bastidor apoya en sus carriles.

Medidas de la vía soviética: ancho 1520 mm, carril de 15 cm (el de las vías de la
maqueta, TransitRails.RAIL_PROFILE), traviesa de hormigón Ш1 de 2,7 m con sujeción de
placa, clemas y tornillos.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Vector

import tumansk_bpy as tb

CAST_IRON = "#3A3735"
CAST_IRON_WORN = "#5A5652"
RUST = "#6E3B24"
DARK_PIT = "#121110"
CONCRETE = "#8C8780"
STEEL = "#4A4744"
STEEL_DARK = "#2E2C2A"
WOOD = "#3B2E25"
WOOD_OLD = "#4E4033"
WHITE_PAINT = "#C9C4B8"
BLACK_PAINT = "#1E1C1B"
RED_PAINT = "#8E2A22"
LAMP_GLASS = "#B9B2A0"
GRANITE = "#8A867F"
GRANITE_CHIP = "#A29E96"
SOIL_STUCK = "#4E463E"

# Carril: medio ancho de vía hasta el eje de cada carril y su perfil (x a la derecha, z
# desde lo alto del carril), cerrado por abajo.
RAIL_OFFSET = 0.7975
RAIL_PROFILE = [
    (0.075, -0.15), (0.075, -0.138), (0.0085, -0.12), (0.0085, -0.04), (0.0375, -0.03), (0.0375, 0.0),
    (-0.0375, 0.0), (-0.0375, -0.03), (-0.0085, -0.04), (-0.0085, -0.12), (-0.075, -0.138), (-0.075, -0.15),
]
# Marcas de los desvíos (la tangente del ángulo que abre el corazón).
FROG_MARKS = {"corazon_1_9": 1.0 / 9.0, "corazon_1_6": 1.0 / 6.0}


def _material() -> bpy.types.Material:
    """Un solo material: el color lo llevan los vértices (Godot pone el suyo)."""
    return tb.material("nevado", "#B3AEA2")


# --------------------------------------------------------------------------
# Barrido de un perfil a lo largo de un camino
# --------------------------------------------------------------------------


def sweep(
    mb: tb.MeshBuilder, profile: list, path: list, color: str, *, jitter: float = 0.0
) -> list:
    """Extruye un perfil cerrado (x a la derecha del camino, z hacia arriba) a lo largo de
    un camino de puntos (x, y, z), con inglete en los quiebros y tapas en las puntas."""
    before = set(mb.bm.faces)
    points = [Vector(p) for p in path]
    count = len(points)
    rings = []
    for i in range(count):
        back = points[i] - points[max(i - 1, 0)]
        ahead = points[min(i + 1, count - 1)] - points[i]
        back.z = 0.0
        ahead.z = 0.0
        if back.length < 1e-9:
            back = ahead
        if ahead.length < 1e-9:
            ahead = back
        tangent = (back.normalized() + ahead.normalized()).normalized()
        side = Vector((tangent.y, -tangent.x, 0.0))
        miter = 1.0 / max(0.5, side.dot(Vector((ahead.normalized().y, -ahead.normalized().x, 0.0))))
        rings.append([mb.bm.verts.new(points[i] + side * (x * miter) + Vector((0.0, 0.0, z))) for x, z in profile])
    faces = []
    sides = len(profile)
    for lower, upper in zip(rings, rings[1:]):
        for j in range(sides):
            k = (j + 1) % sides
            faces.append(mb.bm.faces.new((lower[j], lower[k], upper[k], upper[j])))
    faces.append(mb.bm.faces.new(list(reversed(rings[0]))))
    faces.append(mb.bm.faces.new(rings[-1]))
    bmesh.ops.recalc_face_normals(mb.bm, faces=faces)
    return mb._finish_piece(before, color, jitter, smooth=False)


def rail(mb: tb.MeshBuilder, path: list, color: str = STEEL, scale: float = 1.0) -> list:
    """Un carril a lo largo de un camino (lo alto del carril en la z de cada punto)."""
    profile = [(x * scale, z) for x, z in RAIL_PROFILE]
    return sweep(mb, profile, path, color)


def _ring(mb: tb.MeshBuilder, inner: float, outer: float, z0: float, z1: float, color: str, segments: int) -> list:
    return mb.lathe([(inner, z0), (outer, z0), (outer, z1), (inner, z1), (inner, z0)], (0.0, 0.0, 0.0), color,
                    segments=segments, sharp_angle=30.0)


# --------------------------------------------------------------------------
# Tapas de registro y sumidero
# --------------------------------------------------------------------------


def build_round_lid() -> bpy.types.Object:
    """Tapa de pozo de alcantarillado (fundición, 60 cm) en su marco: nervios en estrella,
    tres aros y dos agujeros para levantarla."""
    root = tb.empty("tapa_redonda")
    mb = tb.MeshBuilder(seed=211)
    # Marco: el aro de fundición, hundido en la calle.
    mb.lathe([(0.31, -0.12), (0.42, -0.12), (0.42, 0.003), (0.31, 0.003), (0.31, -0.12)], (0.0, 0.0, 0.0),
             CAST_IRON, segments=28, sharp_angle=30.0)
    # La tapa, un pelo más alta que el marco.
    mb.lathe([(0.0, -0.035), (0.298, -0.035), (0.298, 0.005), (0.0, 0.005)], (0.0, 0.0, 0.0), CAST_IRON,
             segments=28, sharp_angle=30.0)
    for radius in (0.09, 0.18, 0.27):
        _ring(mb, radius - 0.008, radius + 0.008, 0.004, 0.009, CAST_IRON_WORN, 28)
    for k in range(12):
        angle = k * 30.0
        r0, r1 = 0.098, 0.262
        middle = (r0 + r1) / 2.0
        center = (math.cos(math.radians(angle)) * middle, math.sin(math.radians(angle)) * middle, 0.0065)
        mb.box((r1 - r0, 0.014, 0.005), center, CAST_IRON_WORN, rotation=(0.0, 0.0, angle))
    for angle in (90.0, 270.0):
        center = (math.cos(math.radians(angle)) * 0.225, math.sin(math.radians(angle)) * 0.225, 0.0035)
        mb.box((0.05, 0.022, 0.004), center, DARK_PIT, rotation=(0.0, 0.0, angle + 90.0))
    lid = mb.finish("tapa_redonda", _material(), root)
    tb.stain(lid, RUST, amount=0.55, scale=6.0, coverage=0.35, seed=211)
    tb.paint({lid: None}, samples=16, ao=0.45, ao_distance=0.05, seed=211)
    return root


def _round_lid_top(mb: tb.MeshBuilder, lift: float) -> None:
    """La tapa redonda sin marco (con sus nervios, sus aros y sus agujeros), con la cara de
    arriba a `lift`."""
    mb.lathe([(0.0, lift - 0.04), (0.298, lift - 0.04), (0.298, lift), (0.0, lift)], (0.0, 0.0, 0.0), CAST_IRON,
             segments=28, sharp_angle=30.0)
    for radius in (0.09, 0.18, 0.27):
        _ring(mb, radius - 0.008, radius + 0.008, lift - 0.001, lift + 0.004, CAST_IRON_WORN, 28)
    for k in range(12):
        angle = k * 30.0
        r0, r1 = 0.098, 0.262
        middle = (r0 + r1) / 2.0
        center = (math.cos(math.radians(angle)) * middle, math.sin(math.radians(angle)) * middle, lift + 0.0015)
        mb.box((r1 - r0, 0.014, 0.005), center, CAST_IRON_WORN, rotation=(0.0, 0.0, angle))


def build_open_round_pit() -> bpy.types.Object:
    """El pozo redondo sin su tapa: el marco de fundición a ras y la boca, negra (lo que
    se ve de la calle es el agujero)."""
    root = tb.empty("pozo_redondo")
    mb = tb.MeshBuilder(seed=213)
    mb.lathe([(0.31, -0.12), (0.42, -0.12), (0.42, 0.005), (0.31, 0.005), (0.31, -0.12)], (0.0, 0.0, 0.0),
             CAST_IRON, segments=28, sharp_angle=30.0)
    # El escalón del asiento de la tapa, gastado, y la boca (a ras del asiento, sobre la
    # calle: lo que se ve es el negro del pozo).
    _ring(mb, 0.298, 0.312, -0.03, 0.002, CAST_IRON_WORN, 28)
    mb.lathe([(0.0, 0.0035), (0.3, 0.0035), (0.3, 0.004), (0.0, 0.004)], (0.0, 0.0, 0.0), DARK_PIT, segments=28,
             sharp_angle=30.0)
    pit = mb.finish("pozo_redondo", _material(), root)
    tb.stain(pit, RUST, amount=0.6, scale=6.0, coverage=0.4, seed=213)
    tb.paint({pit: None}, samples=12, ao=0.4, ao_distance=0.05, seed=213)
    return root


def build_loose_round_lid() -> bpy.types.Object:
    """La tapa redonda tirada en la calle, junto a su pozo: apoya en el suelo."""
    root = tb.empty("tapa_suelta_redonda")
    mb = tb.MeshBuilder(seed=217)
    _round_lid_top(mb, 0.04)
    for angle in (90.0, 270.0):
        center = (math.cos(math.radians(angle)) * 0.225, math.sin(math.radians(angle)) * 0.225, 0.0385)
        mb.box((0.05, 0.022, 0.004), center, DARK_PIT, rotation=(0.0, 0.0, angle + 90.0))
    lid = mb.finish("tapa_suelta_redonda", _material(), root)
    tb.stain(lid, RUST, amount=0.65, scale=6.0, coverage=0.45, seed=217)
    tb.paint({lid: None}, samples=12, ao=0.45, ao_distance=0.05, seed=217)
    return root


def build_square_lid() -> bpy.types.Object:
    """Tapa cuadrada de la red de cables (60 cm): rejilla de tacos en relieve."""
    root = tb.empty("tapa_cuadrada")
    mb = tb.MeshBuilder(seed=223)
    for x0, x1, y0, y1 in ((-0.39, 0.39, 0.31, 0.39), (-0.39, 0.39, -0.39, -0.31), (-0.39, -0.31, -0.31, 0.31),
                           (0.31, 0.39, -0.31, 0.31)):
        mb.box((x1 - x0, y1 - y0, 0.123), ((x0 + x1) / 2.0, (y0 + y1) / 2.0, -0.0585), CAST_IRON)
    mb.box((0.6, 0.6, 0.04), (0.0, 0.0, -0.015), CAST_IRON)
    for i in range(5):
        for j in range(5):
            x = -0.22 + i * 0.11
            y = -0.22 + j * 0.11
            mb.box((0.055, 0.055, 0.005), (x, y, 0.0075), CAST_IRON_WORN, rotation=(0.0, 0.0, 45.0))
    mb.box((0.06, 0.02, 0.004), (0.0, 0.25, 0.0055), DARK_PIT)
    lid = mb.finish("tapa_cuadrada", _material(), root)
    tb.stain(lid, RUST, amount=0.5, scale=6.0, coverage=0.35, seed=223)
    tb.paint({lid: None}, samples=16, ao=0.45, ao_distance=0.05, seed=223)
    return root


def build_open_square_pit() -> bpy.types.Object:
    """El pozo cuadrado de la red de cables sin su tapa: el marco a ras y la boca negra."""
    root = tb.empty("pozo_cuadrado")
    mb = tb.MeshBuilder(seed=229)
    for x0, x1, y0, y1 in ((-0.39, 0.39, 0.31, 0.39), (-0.39, 0.39, -0.39, -0.31), (-0.39, -0.31, -0.31, 0.31),
                           (0.31, 0.39, -0.31, 0.31)):
        mb.box((x1 - x0, y1 - y0, 0.123), ((x0 + x1) / 2.0, (y0 + y1) / 2.0, -0.0585), CAST_IRON)
    mb.box((0.62, 0.62, 0.0005), (0.0, 0.0, 0.0038), DARK_PIT)
    pit = mb.finish("pozo_cuadrado", _material(), root)
    tb.stain(pit, RUST, amount=0.6, scale=6.0, coverage=0.4, seed=229)
    tb.paint({pit: None}, samples=12, ao=0.4, ao_distance=0.05, seed=229)
    return root


def build_loose_square_lid() -> bpy.types.Object:
    """La tapa cuadrada tirada junto a su pozo: apoya en el suelo."""
    root = tb.empty("tapa_suelta_cuadrada")
    mb = tb.MeshBuilder(seed=233)
    mb.box((0.6, 0.6, 0.04), (0.0, 0.0, 0.02), CAST_IRON)
    for i in range(5):
        for j in range(5):
            mb.box((0.055, 0.055, 0.005), (-0.22 + i * 0.11, -0.22 + j * 0.11, 0.0425), CAST_IRON_WORN,
                   rotation=(0.0, 0.0, 45.0))
    lid = mb.finish("tapa_suelta_cuadrada", _material(), root)
    tb.stain(lid, RUST, amount=0.6, scale=6.0, coverage=0.45, seed=233)
    tb.paint({lid: None}, samples=12, ao=0.45, ao_distance=0.05, seed=233)
    return root


def build_loose_curb() -> bpy.types.Object:
    """Una pieza de bordillo de granito (1 m) arrancada por la helada, tumbada en la
    calzada: desportillada en las aristas, con la tierra pegada abajo."""
    root = tb.empty("bordillo_suelto")
    rng = random.Random(239)
    mb = tb.MeshBuilder(seed=239)
    mb.box((0.3, 1.0, 0.15), (0.0, 0.0, 0.075), GRANITE, bevel=0.012, cuts=2, jitter=0.03)
    for _ in range(5):
        y = rng.uniform(-0.45, 0.45)
        side = rng.choice((-1.0, 1.0))
        mb.box((0.06, rng.uniform(0.06, 0.14), 0.05), (side * 0.15, y, rng.uniform(0.02, 0.13)), GRANITE_CHIP,
               rotation=(rng.uniform(0, 30), rng.uniform(0, 30), rng.uniform(0, 30)))
    mb.box((0.26, 0.7, 0.012), (0.0, rng.uniform(-0.1, 0.1), 0.004), SOIL_STUCK, jitter=0.1)
    curb = mb.finish("bordillo_suelto", _material(), root)
    tb.wobble(curb, 0.004, scale=8.0, seed=239)
    tb.stain(curb, "#5E5A54", amount=0.4, scale=4.0, coverage=0.35, seed=239)
    tb.paint({curb: None}, samples=12, ao=0.5, ao_distance=0.1, seed=239)
    return root


def build_drain() -> bpy.types.Object:
    """Sumidero de la cuneta: rejilla de barrotes de través sobre el pozo oscuro."""
    root = tb.empty("sumidero")
    mb = tb.MeshBuilder(seed=227)
    width, depth = 0.8, 0.4
    for x0, x1, y0, y1 in ((-0.45, 0.45, 0.2, 0.25), (-0.45, 0.45, -0.25, -0.2), (-0.45, -0.4, -0.2, 0.2),
                           (0.4, 0.45, -0.2, 0.2)):
        mb.box((x1 - x0, y1 - y0, 0.13), ((x0 + x1) / 2.0, (y0 + y1) / 2.0, -0.062), CAST_IRON)
    # El pozo: oscuro, se ve entre los barrotes.
    mb.box((width, depth, 0.02), (0.0, 0.0, -0.3), DARK_PIT)
    for x, y in ((-0.4, 0.0), (0.4, 0.0)):
        mb.box((0.01, depth, 0.28), (x, y, -0.16), DARK_PIT)
    for x, y in ((0.0, -0.2), (0.0, 0.2)):
        mb.box((width, 0.01, 0.28), (x, y, -0.16), DARK_PIT)
    # Barrotes y los dos largueros.
    bars = 11
    for i in range(bars):
        x = -width / 2.0 + 0.045 + i * (width - 0.09) / (bars - 1)
        mb.box((0.03, depth, 0.05), (x, 0.0, -0.022), CAST_IRON_WORN)
    for y in (-0.1, 0.1):
        mb.box((width, 0.025, 0.035), (0.0, y, -0.03), CAST_IRON)
    drain = mb.finish("sumidero", _material(), root)
    tb.stain(drain, RUST, amount=0.6, scale=5.0, coverage=0.4, seed=227)
    tb.paint({drain: None}, samples=16, ao=0.6, ao_distance=0.08, seed=227)
    return root


# --------------------------------------------------------------------------
# Traviesas
# --------------------------------------------------------------------------


def build_sleeper() -> bpy.types.Object:
    """Traviesa de hormigón Ш1: sección trapecial, rebajada en el centro, con la placa,
    las dos clemas y los tornillos de cada asiento del carril."""
    root = tb.empty("traviesa")
    mb = tb.MeshBuilder(seed=229)
    before = set(mb.bm.faces)
    half = 1.35
    seat, bottom = -0.02, -0.21
    stations = [(-half, seat), (-0.55, seat), (-0.35, seat - 0.04), (0.35, seat - 0.04), (0.55, seat), (half, seat)]
    rings = []
    for x, top in stations:
        rings.append([
            mb.bm.verts.new((x, -0.14, bottom)),
            mb.bm.verts.new((x, -0.09, top)),
            mb.bm.verts.new((x, 0.09, top)),
            mb.bm.verts.new((x, 0.14, bottom)),
        ])
    faces = []
    for a, b in zip(rings, rings[1:]):
        for j in range(4):
            k = (j + 1) % 4
            faces.append(mb.bm.faces.new((a[j], a[k], b[k], b[j])))
    faces.append(mb.bm.faces.new(list(reversed(rings[0]))))
    faces.append(mb.bm.faces.new(rings[-1]))
    bmesh.ops.recalc_face_normals(mb.bm, faces=faces)
    mb._finish_piece(before, CONCRETE, 0.0, smooth=False)
    for side in (-1.0, 1.0):
        x = side * RAIL_OFFSET
        mb.box((0.18, 0.36, 0.02), (x, 0.0, -0.01), STEEL_DARK)
        for edge in (-1.0, 1.0):
            cx = x + edge * 0.095
            mb.box((0.06, 0.1, 0.03), (cx, 0.0, 0.006), STEEL)
            mb.cylinder(0.014, 0.05, (cx + edge * 0.012, 0.0, 0.03), STEEL, segments=6)
    sleeper = mb.finish("traviesa", _material(), root)
    tb.stain(sleeper, RUST, amount=0.4, scale=4.0, coverage=0.25, seed=229)
    tb.paint({sleeper: None}, samples=12, ao=0.5, ao_distance=0.1, ground_z=-0.12, seed=229)
    return root


def build_timber() -> bpy.types.Object:
    """Traviesa de madera de los desvíos (un metro: se estira a lo largo)."""
    root = tb.empty("traviesa_madera")
    mb = tb.MeshBuilder(seed=233)
    mb.box((1.0, 0.25, 0.16), (0.0, 0.0, -0.08), WOOD, bevel=0.012, jitter=0.08)
    mb.box((1.0, 0.004, 0.004), (0.0, 0.05, 0.0005), WOOD_OLD)
    timber = mb.finish("traviesa_madera", _material(), root)
    tb.stain(timber, BLACK_PAINT, amount=0.35, scale=3.0, coverage=0.3, seed=233)
    tb.paint({timber: None}, samples=10, ao=0.4, ao_distance=0.08, ground_z=-0.12, seed=233)
    return root


# --------------------------------------------------------------------------
# Desvío: corazón y palanca
# --------------------------------------------------------------------------


def build_frog(name: str, mark: float) -> bpy.types.Object:
    """Corazón de un desvío: la punta (los dos carriles que salen, unidos en una cuña),
    las patas de liebre (los que llegan, que se abren a los lados en la garganta) y el
    bloque de fundición que lo junta todo. Simétrico: vale para los dos lados."""
    root = tb.empty(name)
    mb = tb.MeshBuilder(seed=239)
    t = math.tan(math.atan(mark) / 2.0)
    head, gap = 0.075, 0.045
    start, end = -2.0, 2.5
    nose_tip = 0.45
    # La punta: los carriles que salen (x = ±y·t), cada uno con su perfil, y la cuña.
    for sign in (-1.0, 1.0):
        rail(mb, [(sign * y * t, y, 0.0) for y in (nose_tip + 0.3, 1.2, end)])
    # La cuña: de la punta hasta donde las dos cabezas se separan (el hueco en V del medio
    # queda abierto). En sentido antihorario.
    outline = [
        (0.0, nose_tip),
        (0.6 * t + head / 2.0, 0.6),
        (1.3 * t + head / 2.0, 1.3),
        (0.0, 1.0),
        (-(1.3 * t + head / 2.0), 1.3),
        (-(0.6 * t + head / 2.0), 0.6),
    ]
    mb.prism(outline, 0.15, (0.0, 0.0, -0.075), STEEL)
    # Las patas de liebre: llegan por su línea, en la garganta se abren y siguen junto a la
    # punta, a un hueco de pestaña.
    throat = -(head + gap) / (2.0 * t)
    for sign in (-1.0, 1.0):
        path = [
            (-sign * start * t, start, 0.0),
            (-sign * throat * t, throat, 0.0),
            (sign * (1.7 * t + head + gap), 1.7, 0.0),
            (sign * (2.1 * t + head + gap + 0.07), 2.1, 0.0),
        ]
        rail(mb, path)
    # El bloque de fundición, por debajo de las cabezas, y la placa de asiento.
    mb.box((0.62, end - throat + 0.8, 0.07), (0.0, (end + throat) / 2.0, -0.115), STEEL_DARK)
    mb.box((0.72, end - start + 0.4, 0.02), (0.0, (end + start) / 2.0, -0.16), STEEL_DARK)
    for y in (-0.6, 0.4, 1.4, 2.2):
        for sign in (-1.0, 1.0):
            mb.cylinder(0.016, 0.06, (sign * 0.28, y, -0.07), STEEL, rotation=(0.0, 90.0, 0.0), segments=6)
    frog = mb.finish(name, _material(), root)
    tb.stain(frog, RUST, amount=0.5, scale=3.0, coverage=0.35, seed=239)
    tb.paint({frog: None}, samples=12, ao=0.5, ao_distance=0.12, ground_z=-0.17, seed=239)
    return root


def build_switch_stand() -> bpy.types.Object:
    """Palanca del cambio de agujas: la caja del mecanismo, la palanca con su contrapeso a
    rayas y el farol indicador en su poste."""
    root = tb.empty("palanca_aguja")
    mb = tb.MeshBuilder(seed=241)
    mb.box((0.34, 0.62, 0.16), (0.0, 0.0, 0.08), STEEL_DARK, bevel=0.015)
    mb.box((0.12, 0.14, 0.1), (0.0, 0.18, 0.2), STEEL, bevel=0.01)
    pivot = Vector((0.0, 0.18, 0.24))
    tip = pivot + Vector((0.0, -0.95 * math.cos(math.radians(28.0)), 0.95 * math.sin(math.radians(28.0))))
    mb.bar(pivot, tip, 0.022, STEEL, 8)
    # El contrapeso: blanco y negro, para verlo de lejos.
    for k, color in enumerate((WHITE_PAINT, BLACK_PAINT, WHITE_PAINT)):
        offset = (k - 1) * 0.07
        mb.box((0.2, 0.07, 0.17), tip + Vector((0.0, offset, -0.02)), color, rotation=(-28.0, 0.0, 0.0), bevel=0.01)
    # El farol del indicador.
    mb.cylinder(0.025, 0.85, (0.0, -0.2, 0.585), STEEL, segments=8)
    mb.box((0.22, 0.22, 0.26), (0.0, -0.2, 1.14), BLACK_PAINT, bevel=0.015)
    for angle in (0.0, 90.0, 180.0, 270.0):
        direction = Vector((math.sin(math.radians(angle)), -math.cos(math.radians(angle)), 0.0))
        mb.box((0.14, 0.01, 0.14), Vector((0.0, -0.2, 1.14)) + direction * 0.112, LAMP_GLASS,
               rotation=(0.0, 0.0, angle))
    mb.box((0.26, 0.26, 0.04), (0.0, -0.2, 1.29), BLACK_PAINT, bevel=0.01)
    stand = mb.finish("palanca_aguja", _material(), root)
    tb.stain(stand, RUST, amount=0.55, scale=4.0, coverage=0.35, seed=241)
    tb.paint({stand: None}, samples=12, ao=0.45, ao_distance=0.15, seed=241)
    return root


# --------------------------------------------------------------------------
# Tope del final de la vía
# --------------------------------------------------------------------------


def build_buffer_stop() -> bpy.types.Object:
    """Tope de vía muerta: un bastidor de carriles viejos doblados con el madero de
    choque a la altura del enganche (pintado a franjas), la señal roja encima y, detrás,
    una pila de traviesas viejas contra la que descansa."""
    root = tb.empty("tope")
    rng = random.Random(251)
    mb = tb.MeshBuilder(seed=251)
    beam_z = 1.06
    # Bastidor: en cada carril, un poste delante y un tornapuntas hacia atrás.
    for side in (-1.0, 1.0):
        x = side * RAIL_OFFSET
        post = [(0.0, 0.05), (0.0, beam_z + 0.12)]
        for (y0, z0), (y1, z1) in zip(post, post[1:]):
            mb.bar((x, y0, z0), (x, y1, z1), 0.05, STEEL_DARK, 6)
        mb.bar((x, 0.12, beam_z + 0.05), (x, 2.7, 0.03), 0.05, STEEL_DARK, 6)
        mb.bar((x, 0.05, 0.35), (x, 1.6, 0.25), 0.035, STEEL_DARK, 6)
    mb.bar((-RAIL_OFFSET, 0.9, 0.62), (RAIL_OFFSET, 0.9, 0.62), 0.03, STEEL_DARK, 6)
    # El madero de choque, a franjas blancas y negras en diagonal.
    mb.box((2.9, 0.26, 0.34), (0.0, -0.06, beam_z), WOOD, bevel=0.015, jitter=0.05)
    stripes = 9
    width = 2.9 / stripes
    for k in range(stripes):
        x0 = -1.45 + k * width
        color = WHITE_PAINT if k % 2 == 0 else BLACK_PAINT
        outline = [(x0, beam_z - 0.16), (x0 + width, beam_z - 0.16), (x0 + width + 0.08, beam_z + 0.16),
                   (x0 + 0.08, beam_z + 0.16)]
        outline = [(min(1.45, max(-1.45, x)), z) for x, z in outline]
        mb.prism(outline, 0.012, (0.0, -0.195, 0.0), color, rotation=(90.0, 0.0, 0.0))
    # La señal: un cuadro rojo con su marco blanco, en un poste sobre el madero.
    mb.cylinder(0.03, 0.75, (0.0, 0.0, beam_z + 0.5), STEEL_DARK, segments=8)
    mb.box((0.52, 0.03, 0.52), (0.0, -0.05, beam_z + 0.72), WHITE_PAINT, bevel=0.008)
    mb.box((0.42, 0.012, 0.42), (0.0, -0.07, beam_z + 0.72), RED_PAINT)
    # La pila de traviesas viejas de detrás.
    for layer in range(4):
        for k in range(2):
            y = 1.15 + k * 0.32 + rng.uniform(-0.03, 0.03)
            z = -0.1 + layer * 0.17
            mb.box((2.7 - layer * 0.25, 0.26, 0.16), (rng.uniform(-0.05, 0.05), y + layer * 0.12, z), WOOD_OLD,
                   rotation=(0.0, rng.uniform(-1.5, 1.5), rng.uniform(-2.0, 2.0)), bevel=0.01, jitter=0.1)
    stop = mb.finish("tope", _material(), root)
    tb.stain(stop, RUST, amount=0.55, scale=2.5, coverage=0.35, seed=251)
    tb.paint({stop: None}, samples=12, ao=0.5, ao_distance=0.3, ground_z=-0.57, seed=251)
    return root


def models() -> dict:
    return {
        "tapa_redonda": build_round_lid,
        "tapa_cuadrada": build_square_lid,
        "pozo_redondo": build_open_round_pit,
        "pozo_cuadrado": build_open_square_pit,
        "tapa_suelta_redonda": build_loose_round_lid,
        "tapa_suelta_cuadrada": build_loose_square_lid,
        "bordillo_suelto": build_loose_curb,
        "sumidero": build_drain,
        "traviesa": build_sleeper,
        "traviesa_madera": build_timber,
        "corazon_1_9": lambda: build_frog("corazon_1_9", FROG_MARKS["corazon_1_9"]),
        "corazon_1_6": lambda: build_frog("corazon_1_6", FROG_MARKS["corazon_1_6"]),
        "palanca_aguja": build_switch_stand,
        "tope": build_buffer_stop,
    }
