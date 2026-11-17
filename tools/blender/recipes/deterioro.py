"""Lo que cae dentro de los socavones de la ciudad (tools/ciudad/deterioro.py): los trozos
de la calle rota, lo que reventó debajo y el charco que se heló en el fondo.

Coordenadas de Blender: X a la derecha, Y hacia delante, Z hacia arriba (en Godot, la Y
de Blender es -Z). La red de tránsito (CityTransit) las coloca como instancias, giradas
hacia su rumbo (+Y), inclinadas con el talud y medio enterradas: el origen es lo que
apoya en el suelo.

- Trozos de asfalto (placa_asfalto_a/b/c): la costra de asfalto, de 8 cm, con su base de
  grava debajo, más pequeña (el agua se la llevó por los bordes). El origen, en el centro
  de la base, abajo.
- Losas rotas (losa_rota_a/b): unas losas de hormigón de la acera, partidas y montadas
  unas sobre otras.
- Tubería rota (tuberia_rota): un tubo de fundición de 60 cm a lo largo de Y, con su
  enchufe en una punta y la otra reventada por la helada. El origen, bajo el tubo.
- Colector roto (colector_roto): un tubo de hormigón de 1,2 m con la clave hundida en la
  mitad de delante y los trozos caídos al lado.
- Galería de la calefacción (canal_calefaccion): el canal de hormigón con los dos tubos
  forrados (el forro, roto a trozos) y las tapas caídas dentro.
- Charco helado (charco_helado): un metro de radio, la cara de arriba en el origen.
- Baches (bache_a/b/c): de medio metro de radio, encima de la calle (la maqueta no la
  corta): el agujero, oscuro y con hielo, la corona de asfalto desmigado alrededor y los
  trozos sueltos. Asoman unos milímetros; el origen, en la calle.

Y lo que deja el abandono por la calle (tools/ciudad/restos.py), con el origen en el suelo:

- Cascotes (cascotes_a/b/c): trozos de panel y de hormigón, ladrillos y alguna varilla,
  caídos de las fachadas o de la onda: un metro o metro y medio, bajos.
- Ladrillos (ladrillos): un puñado de ladrillos sueltos y partidos.
- Neumático (neumatico): una rueda vieja tumbada.
- Cartones (carton): cajas aplastadas, papeles y trapos, pegados al suelo por la helada.
- Rama (rama): una rama seca caída, de dos metros, con sus ramitas (a lo largo de Y).
- Farola arrancada (farola_mocha): la base de hormigón y el muñón del poste, partido, con
  los cables y las varillas al aire.

Todo de colores apagados: el hierro, oxidado; el hormigón, manchado de humedad y hollín.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy

import tumansk_bpy as tb

ASPHALT = "#3F3D3B"
ASPHALT_EDGE = "#55524F"
GRAVEL = "#76716A"
SOIL = "#5B5148"
CONCRETE = "#8A857C"
CONCRETE_DARK = "#6E6962"
SLAB = "#9A958C"
CAST_IRON = "#3A3735"
RUST = "#6E3B24"
RUST_DARK = "#4A2A1D"
STEEL = "#4A4744"
INSULATION = "#8B8473"
INSULATION_DIRT = "#5C564A"
ICE = "#8D979B"
FROST = "#B8BEC0"
DARK_INSIDE = "#1A1817"
PANEL = "#7E7A72"
PANEL_DARK = "#625E58"
BRICK = "#7A4A3A"
BRICK_DARK = "#5E3A2E"
REBAR = "#4A3426"
RUBBER = "#252322"
CARDBOARD = "#7F6E55"
PAPER = "#A39C8C"
RAG = "#57524C"
BARK = "#3E352D"
POLE = "#7D7A73"
WIRE = "#2B2826"


def _material() -> bpy.types.Material:
    """Un solo material: el color lo llevan los vértices (Godot pone el suyo)."""
    return tb.material("nevado", "#B3AEA2")


def _outline(rng: random.Random, radius: float, count: int, squash: float = 1.0) -> list:
    """Un contorno irregular (en sentido antihorario) alrededor del origen."""
    angles = sorted(rng.uniform(0.0, 2.0 * math.pi) for _ in range(count))
    return [(math.cos(a) * radius * rng.uniform(0.62, 1.0), math.sin(a) * radius * rng.uniform(0.62, 1.0) * squash)
            for a in angles]


def _shell(mb: tb.MeshBuilder, outer: float, inner: float, start: float, length: float, color: str, *,
           segments: int = 20, rings: int = 4, arc: tuple[float, float] | None = None,
           jagged: float = 0.0, axis_z: float | None = None) -> list:
    """Un tubo (o un trozo de su pared, de `arc` grados) a lo largo de Y, de `start` a
    `start + length`, con el eje a `axis_z` (si no, apoyado en z = 0). La punta de delante,
    mordida hasta `jagged` metros (reventada)."""
    before = set(mb.bm.faces)
    z0 = outer if axis_z is None else axis_z
    closed = arc is None
    a0, a1 = (0.0, 360.0) if closed else arc
    count = segments if closed else segments + 1
    angles = [math.radians(a0 + (a1 - a0) * j / segments) for j in range(count)]
    bites = [mb.rng.uniform(0.0, jagged) for _ in range(count)]
    grid_out = []
    grid_in = []
    for k in range(rings + 1):
        f = k / rings
        row_out = []
        row_in = []
        for j, a in enumerate(angles):
            y = start + length * f - (bites[j] * f**4)
            c, s = math.cos(a), math.sin(a)
            row_out.append(mb.bm.verts.new((c * outer, y, z0 + s * outer)))
            row_in.append(mb.bm.verts.new((c * inner, y, z0 + s * inner)))
        grid_out.append(row_out)
        grid_in.append(row_in)
    faces = []
    span = count if closed else count - 1
    for k in range(rings):
        for j in range(span):
            m = (j + 1) % count
            faces.append(mb.bm.faces.new((grid_out[k][j], grid_out[k + 1][j], grid_out[k + 1][m], grid_out[k][m])))
            faces.append(mb.bm.faces.new((grid_in[k][j], grid_in[k][m], grid_in[k + 1][m], grid_in[k + 1][j])))
    for k in (0, rings):
        for j in range(span):
            m = (j + 1) % count
            faces.append(mb.bm.faces.new((grid_out[k][j], grid_out[k][m], grid_in[k][m], grid_in[k][j])))
    if not closed:
        for j in (0, count - 1):
            for k in range(rings):
                faces.append(mb.bm.faces.new((grid_out[k][j], grid_in[k][j], grid_in[k + 1][j], grid_out[k + 1][j])))
    bmesh.ops.recalc_face_normals(mb.bm, faces=faces)
    return mb._finish_piece(before, color, 0.0, smooth=True)


# --------------------------------------------------------------------------
# Trozos de la calle
# --------------------------------------------------------------------------


def build_asphalt_chunk(name: str, seed: int, radius: float) -> bpy.types.Object:
    """Un trozo de calzada caído: la costra de asfalto (8 cm) y su base de grava, más
    pequeña y desigual, con algún terrón pegado."""
    root = tb.empty(name)
    rng = random.Random(seed)
    mb = tb.MeshBuilder(seed=seed)
    outline = _outline(rng, radius, rng.randint(7, 9), rng.uniform(0.6, 0.85))
    base = 0.2 + rng.uniform(-0.04, 0.04)
    inset = [(x * rng.uniform(0.78, 0.92), y * rng.uniform(0.78, 0.92)) for x, y in outline]
    mb.prism(inset, base, (0.0, 0.0, base / 2.0), GRAVEL, bevel=0.03, segments=1, jitter=0.05)
    mb.prism(outline, 0.08, (0.0, 0.0, base + 0.04), ASPHALT, bevel=0.012, segments=1, jitter=0.04)
    # Terrones de tierra pegados a la base.
    for _ in range(4):
        a = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(0.62, 0.78) * radius
        size = rng.uniform(0.08, 0.16)
        mb.box((size, size * 1.3, size), (math.cos(a) * r, math.sin(a) * r * 0.7, rng.uniform(0.03, 0.08)), SOIL,
               rotation=(rng.uniform(0, 40), 0, rng.uniform(0, 90)), bevel=0.02, jitter=0.1)
    piece = mb.finish(name, _material(), root)
    tb.wobble(piece, 0.012, scale=4.0, seed=seed)
    tb.stain(piece, ASPHALT_EDGE, amount=0.45, scale=3.0, coverage=0.35, seed=seed)
    tb.paint({piece: None}, samples=12, ao=0.5, ao_distance=0.2, seed=seed)
    return root


def build_broken_slabs(name: str, seed: int) -> bpy.types.Object:
    """Losas de acera (50 cm) partidas, caídas unas sobre otras."""
    root = tb.empty(name)
    rng = random.Random(seed)
    mb = tb.MeshBuilder(seed=seed)
    for k in range(4):
        half = 0.25
        cut = rng.uniform(0.1, 0.4)
        square = [(-half, -half), (half, -half), (half, half - cut), (half - cut * 1.3, half), (-half, half)]
        angle = rng.uniform(0.0, 360.0)
        tilt = (rng.uniform(-28.0, 28.0), rng.uniform(-22.0, 22.0), angle)
        x, y = math.cos(math.radians(k * 95.0)) * 0.32, math.sin(math.radians(k * 95.0)) * 0.32
        mb.prism(square, 0.06, (x, y, 0.05 + 0.04 * k), SLAB, rotation=tilt, bevel=0.008, segments=1, jitter=0.06)
    mb.box((0.9, 0.8, 0.06), (0.0, 0.0, 0.0), SOIL, bevel=0.03, jitter=0.1)
    piece = mb.finish(name, _material(), root)
    tb.stain(piece, CONCRETE_DARK, amount=0.5, scale=4.0, coverage=0.4, seed=seed)
    tb.paint({piece: None}, samples=12, ao=0.55, ao_distance=0.15, seed=seed)
    return root


# --------------------------------------------------------------------------
# Lo que reventó debajo
# --------------------------------------------------------------------------


def build_burst_main() -> bpy.types.Object:
    """Tubo de fundición del agua (60 cm) reventado por la helada: el enchufe de la junta
    atrás, una raja a lo largo y la punta de delante rota, con trozos sueltos."""
    root = tb.empty("tuberia_rota")
    rng = random.Random(613)
    mb = tb.MeshBuilder(seed=613)
    outer, inner = 0.32, 0.285
    _shell(mb, outer, inner, -1.8, 3.4, CAST_IRON, segments=22, rings=8, jagged=0.55)
    _shell(mb, 0.4, outer - 0.005, -1.95, 0.32, CAST_IRON, segments=22, rings=1, axis_z=outer)
    # El fondo del tubo, oscuro por dentro.
    mb.box((0.36, 3.0, 0.01), (0.0, -0.2, 0.05), DARK_INSIDE)
    # Trozos de la punta, caídos delante.
    for k in range(4):
        a = rng.uniform(40.0, 140.0)
        _shell(mb, outer, inner, 1.7 + k * 0.18, rng.uniform(0.15, 0.3), CAST_IRON, segments=3, rings=1,
               arc=(a, a + rng.uniform(25.0, 50.0)), axis_z=outer * rng.uniform(0.1, 0.4))
    piece = mb.finish("tuberia_rota", _material(), root)
    tb.stain(piece, RUST, amount=0.75, scale=3.0, coverage=0.55, seed=613)
    tb.stain(piece, RUST_DARK, amount=0.5, scale=8.0, coverage=0.3, seed=617)
    tb.paint({piece: None}, samples=12, ao=0.6, ao_distance=0.3, seed=613)
    return root


def build_broken_collector() -> bpy.types.Object:
    """Tubo de hormigón del colector (1,2 m por dentro): entero detrás; delante, la clave
    hundida y sus trozos caídos al lado. Manchado de la línea del agua."""
    root = tb.empty("colector_roto")
    rng = random.Random(619)
    mb = tb.MeshBuilder(seed=619)
    outer, inner = 0.72, 0.6
    _shell(mb, outer, inner, -1.6, 1.6, CONCRETE, segments=24, rings=3)
    _shell(mb, outer, inner, 0.02, 1.5, CONCRETE, segments=18, rings=3, arc=(150.0, 390.0), jagged=0.4)
    for k in range(3):
        a = rng.uniform(60.0, 120.0)
        _shell(mb, outer, inner, 0.2 + k * 0.45, rng.uniform(0.35, 0.55), CONCRETE_DARK, segments=4, rings=1,
               arc=(a, a + rng.uniform(25.0, 45.0)), axis_z=rng.uniform(0.0, 0.25))
    mb.box((1.0, 3.0, 0.02), (0.0, -0.1, 0.13), DARK_INSIDE)
    piece = mb.finish("colector_roto", _material(), root)
    tb.stain(piece, "#4C4842", amount=0.6, scale=2.0, coverage=0.4, seed=619, stretch_z=0.3)
    tb.paint({piece: None}, samples=12, ao=0.6, ao_distance=0.4, seed=619)
    return root


def build_heating_channel() -> bpy.types.Object:
    """La galería de la calefacción: el canal de hormigón (1,2 m por dentro) con los dos
    tubos forrados sobre sus apoyos (el forro, roto: asoma el acero oxidado) y las tapas
    caídas dentro; una sigue en su sitio."""
    root = tb.empty("canal_calefaccion")
    rng = random.Random(631)
    mb = tb.MeshBuilder(seed=631)
    length = 4.0
    mb.box((1.5, length, 0.15), (0.0, 0.0, 0.075), CONCRETE, bevel=0.01, cuts=3)
    for side in (-1.0, 1.0):
        mb.box((0.15, length, 1.0), (side * 0.675, 0.0, 0.5), CONCRETE, bevel=0.01, cuts=3)
    for y in (-1.4, 0.0, 1.4):
        for side in (-1.0, 1.0):
            mb.box((0.3, 0.25, 0.14), (side * 0.3, y, 0.22), CONCRETE_DARK, bevel=0.01)
    for side in (-1.0, 1.0):
        x = side * 0.3
        z = 0.29 + 0.2
        # El forro, a trozos; entre ellos, el tubo de acero.
        gap = rng.uniform(-0.8, 0.8)
        mb.bar((x, -length / 2, z), (x, gap - 0.35, z), 0.2, INSULATION, segments=12)
        mb.bar((x, gap + 0.35, z), (x, length / 2, z), 0.2, INSULATION, segments=12)
        mb.bar((x, -length / 2 - 0.05, z), (x, length / 2 + 0.05, z), 0.14, STEEL, segments=10)
    # Tapas: una en su sitio, dos caídas dentro.
    mb.box((1.6, 0.8, 0.12), (0.0, -1.55, 1.06), CONCRETE, bevel=0.01, cuts=2)
    for y, tilt in ((-0.3, (24.0, 8.0, 3.0)), (0.9, (-31.0, -12.0, -4.0))):
        mb.box((1.6, 0.8, 0.12), (0.05, y, 0.85), CONCRETE_DARK, rotation=tilt, bevel=0.01, cuts=2)
    piece = mb.finish("canal_calefaccion", _material(), root)
    tb.stain(piece, INSULATION_DIRT, amount=0.55, scale=3.0, coverage=0.45, seed=631)
    tb.stain(piece, RUST, amount=0.4, scale=6.0, coverage=0.25, seed=637)
    tb.paint({piece: None}, samples=12, ao=0.6, ao_distance=0.4, seed=631)
    return root


def build_ice_puddle() -> bpy.types.Object:
    """El charco helado del fondo: un metro de radio, liso, con escarcha a manchas."""
    root = tb.empty("charco_helado")
    rng = random.Random(641)
    mb = tb.MeshBuilder(seed=641)
    outline = []
    for k in range(18):
        a = k / 18 * 2.0 * math.pi
        r = rng.uniform(0.85, 1.0)
        outline.append((math.cos(a) * r, math.sin(a) * r * 0.85))
    mb.prism(outline, 0.04, (0.0, 0.0, -0.02), ICE, bevel=0.01, segments=1)
    piece = mb.finish("charco_helado", _material(), root)
    tb.stain(piece, FROST, amount=0.6, scale=3.5, coverage=0.4, seed=641)
    tb.paint({piece: None}, samples=8, ao=0.2, ao_distance=0.1, ground_z=-0.04, seed=641)
    return root


def build_pothole(name: str, seed: int, ice: bool) -> bpy.types.Object:
    """Un bache: lo hondo, casi negro (agua helada y barro), dentro de una corona de asfalto
    desmigado más clara (la base de grava asoma), y trozos de costra sueltos alrededor.
    Todo a unos milímetros sobre la calle: de lejos y de cerca, se lee como un agujero."""
    root = tb.empty(name)
    rng = random.Random(seed)
    mb = tb.MeshBuilder(seed=seed)
    rim = _outline(rng, 0.62, 13, rng.uniform(0.7, 0.95))
    hole = [(x * rng.uniform(0.62, 0.8), y * rng.uniform(0.62, 0.8)) for x, y in rim]
    # Cada capa, unos milímetros sobre la anterior (y la de abajo, sobre la calle): sin
    # parpadeos de lejos.
    mb.prism(rim, 0.012, (0.0, 0.0, 0.0), GRAVEL, jitter=0.05)
    mb.prism(hole, 0.012, (0.0, 0.0, 0.003), DARK_INSIDE, jitter=0.03)
    if ice:
        sheet = [(x * 0.7, y * 0.7) for x, y in hole]
        mb.prism(sheet, 0.004, (0.0, 0.0, 0.011), ICE, jitter=0.03)
    for _ in range(rng.randint(6, 11)):
        a = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(0.5, 0.85)
        size = rng.uniform(0.03, 0.09)
        mb.box((size * 1.4, size, 0.025), (math.cos(a) * r, math.sin(a) * r * 0.85, 0.008), ASPHALT,
               rotation=(rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(0, 180)), jitter=0.1)
    piece = mb.finish(name, _material(), root)
    tb.stain(piece, SOIL, amount=0.4, scale=5.0, coverage=0.4, seed=seed)
    tb.paint({piece: None}, samples=8, ao=0.3, ao_distance=0.05, ground_z=-0.01, seed=seed)
    return root


# --------------------------------------------------------------------------
# Lo que deja el abandono por la calle
# --------------------------------------------------------------------------


def build_debris(name: str, seed: int, radius: float) -> bpy.types.Object:
    """Cascotes sueltos: trozos de panel y de hormigón, algún ladrillo y una varilla
    retorcida, tirados en un corro bajo (cayeron de una fachada o los trajo la onda)."""
    root = tb.empty(name)
    rng = random.Random(seed)
    mb = tb.MeshBuilder(seed=seed)
    for _ in range(int(radius * 14)):
        r = radius * math.sqrt(rng.random())
        a = rng.uniform(0.0, 2.0 * math.pi)
        size = rng.uniform(0.06, 0.3) * (1.2 if r < radius * 0.4 else 0.8)
        high = size * rng.uniform(0.25, 0.6)
        mb.box((size * rng.uniform(0.9, 1.8), size * rng.uniform(0.6, 1.2), high),
               (r * math.cos(a), r * math.sin(a), high * 0.35), rng.choice((CONCRETE, PANEL, PANEL_DARK, SLAB)),
               rotation=(rng.uniform(-25, 25), rng.uniform(-25, 25), rng.uniform(0, 180)), bevel=0.012, jitter=0.08)
    for _ in range(int(radius * 5)):
        r = radius * math.sqrt(rng.random())
        a = rng.uniform(0.0, 2.0 * math.pi)
        mb.box((0.25 * rng.uniform(0.5, 1.0), 0.12, 0.065), (r * math.cos(a), r * math.sin(a), 0.03),
               rng.choice((BRICK, BRICK_DARK)), rotation=(rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(0, 180)),
               bevel=0.008, jitter=0.1)
    for _ in range(max(1, int(radius * 1.5))):
        x, y = rng.uniform(-0.5, 0.5) * radius, rng.uniform(-0.5, 0.5) * radius
        mb.bar((x, y, 0.04), (x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.6, 0.6), rng.uniform(0.05, 0.35)), 0.008,
               REBAR, 5)
    debris = mb.finish(name, _material(), root)
    tb.stain(debris, "#3A3632", amount=0.45, scale=2.0, coverage=0.35, seed=seed)
    tb.paint({debris: None}, samples=10, ao=0.55, ao_distance=0.2, seed=seed)
    return root


def build_bricks() -> bpy.types.Object:
    """Un puñado de ladrillos sueltos, enteros y partidos."""
    root = tb.empty("ladrillos")
    rng = random.Random(661)
    mb = tb.MeshBuilder(seed=661)
    for k in range(11):
        r = 0.45 * math.sqrt(rng.random())
        a = rng.uniform(0.0, 2.0 * math.pi)
        long = 0.25 if k % 3 else rng.uniform(0.1, 0.18)
        mb.box((long, 0.12, 0.065), (r * math.cos(a), r * math.sin(a), 0.032 + 0.06 * (k % 4 == 0)),
               rng.choice((BRICK, BRICK_DARK, "#8A5A46")), rotation=(rng.uniform(-12, 12), rng.uniform(-12, 12),
                                                                     rng.uniform(0, 180)), bevel=0.006, jitter=0.1)
    bricks = mb.finish("ladrillos", _material(), root)
    tb.stain(bricks, "#4A4440", amount=0.4, scale=4.0, coverage=0.3, seed=661)
    tb.paint({bricks: None}, samples=8, ao=0.5, ao_distance=0.1, seed=661)
    return root


def build_tyre() -> bpy.types.Object:
    """Una rueda vieja tumbada, con el dibujo gastado."""
    root = tb.empty("neumatico")
    mb = tb.MeshBuilder(seed=667)
    profile = [(0.2, 0.0), (0.3, 0.0), (0.33, 0.04), (0.33, 0.15), (0.3, 0.19), (0.2, 0.19), (0.19, 0.13),
               (0.19, 0.06), (0.2, 0.0)]
    mb.lathe(profile, (0.0, 0.0, 0.0), RUBBER, segments=24, sharp_angle=40.0)
    tyre = mb.finish("neumatico", _material(), root)
    tb.stain(tyre, "#3A3734", amount=0.4, scale=6.0, coverage=0.4, seed=667)
    tb.paint({tyre: None}, samples=8, ao=0.5, ao_distance=0.1, seed=667)
    return root


def build_cardboard() -> bpy.types.Object:
    """Cajas de cartón aplastadas, papeles y algún trapo, pegados al suelo por la helada."""
    root = tb.empty("carton")
    rng = random.Random(673)
    mb = tb.MeshBuilder(seed=673)
    for k in range(7):
        w, d = (rng.uniform(0.35, 0.7), rng.uniform(0.25, 0.5)) if k < 3 else (rng.uniform(0.12, 0.3),
                                                                               rng.uniform(0.1, 0.22))
        color = CARDBOARD if k < 3 else rng.choice((PAPER, RAG, "#8E8676"))
        mb.box((w, d, 0.008), (rng.uniform(-0.4, 0.4), rng.uniform(-0.3, 0.3), 0.006 + k * 0.003), color,
               rotation=(rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(0, 180)), jitter=0.08)
    trash = mb.finish("carton", _material(), root)
    tb.stain(trash, "#4A443C", amount=0.5, scale=5.0, coverage=0.4, seed=673)
    tb.paint({trash: None}, samples=6, ao=0.3, ao_distance=0.05, seed=673)
    return root


def build_branch() -> bpy.types.Object:
    """Una rama seca caída (dos metros, a lo largo de Y), con sus ramitas."""
    root = tb.empty("rama")
    rng = random.Random(677)
    mb = tb.MeshBuilder(seed=677)
    path = [(0.0, -1.0, 0.06), (0.05, -0.4, 0.07), (-0.04, 0.3, 0.05), (0.06, 1.0, 0.04)]
    for (x0, y0, z0), (x1, y1, z1), r in zip(path, path[1:], (0.06, 0.045, 0.03)):
        mb.bar((x0, y0, z0), (x1, y1, z1), r, BARK, 7)
    for _ in range(9):
        y = rng.uniform(-0.6, 0.9)
        side = rng.choice((-1.0, 1.0))
        end = (side * rng.uniform(0.2, 0.55), y + rng.uniform(0.1, 0.4), rng.uniform(0.04, 0.3))
        mb.bar((0.0, y, 0.05), end, 0.012, BARK, 5)
    branch = mb.finish("rama", _material(), root)
    tb.paint({branch: None}, samples=6, ao=0.4, ao_distance=0.1, seed=677)
    return root


def build_lamp_stump() -> bpy.types.Object:
    """La farola arrancada: su base de hormigón y el muñón del poste, partido en punta,
    con los cables y las varillas al aire."""
    root = tb.empty("farola_mocha")
    rng = random.Random(683)
    mb = tb.MeshBuilder(seed=683)
    mb.box((0.36, 0.36, 0.5), (0.0, 0.0, 0.25), POLE, bevel=0.03)
    stub = rng.uniform(0.7, 1.1)
    mb.cylinder(0.14, stub, (0.0, 0.0, 0.5 + stub / 2.0), POLE, radius_top=0.13, segments=8)
    for k in range(5):
        a = k / 5 * 2.0 * math.pi
        top = 0.5 + stub + rng.uniform(0.05, 0.3)
        mb.box((0.08, 0.06, top - stub - 0.45), (math.cos(a) * 0.09, math.sin(a) * 0.09, (stub + 0.5 + top) / 2.0),
               POLE, rotation=(rng.uniform(-10, 10), rng.uniform(-10, 10), math.degrees(a)))
    for _ in range(4):
        start = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0.5 + stub)
        end = (start[0] + rng.uniform(-0.4, 0.4), start[1] + rng.uniform(-0.4, 0.4), start[2] + rng.uniform(0.1, 0.5))
        mb.bar(start, end, 0.01, REBAR, 5)
    mb.bar((0.0, 0.0, 0.5 + stub), (0.5, 0.2, 0.02), 0.012, WIRE, 5)
    stump = mb.finish("farola_mocha", _material(), root)
    tb.stain(stump, RUST, amount=0.5, scale=3.0, coverage=0.3, seed=683)
    tb.paint({stump: None}, samples=8, ao=0.5, ao_distance=0.2, seed=683)
    return root


def models() -> dict:
    return {
        "placa_asfalto_a": lambda: build_asphalt_chunk("placa_asfalto_a", 601, 0.85),
        "placa_asfalto_b": lambda: build_asphalt_chunk("placa_asfalto_b", 603, 0.65),
        "placa_asfalto_c": lambda: build_asphalt_chunk("placa_asfalto_c", 607, 1.05),
        "losa_rota_a": lambda: build_broken_slabs("losa_rota_a", 609),
        "losa_rota_b": lambda: build_broken_slabs("losa_rota_b", 611),
        "tuberia_rota": build_burst_main,
        "colector_roto": build_broken_collector,
        "canal_calefaccion": build_heating_channel,
        "charco_helado": build_ice_puddle,
        "bache_a": lambda: build_pothole("bache_a", 651, False),
        "bache_b": lambda: build_pothole("bache_b", 653, True),
        "bache_c": lambda: build_pothole("bache_c", 659, False),
        "cascotes_a": lambda: build_debris("cascotes_a", 687, 0.6),
        "cascotes_b": lambda: build_debris("cascotes_b", 691, 0.85),
        "cascotes_c": lambda: build_debris("cascotes_c", 701, 1.2),
        "ladrillos": build_bricks,
        "neumatico": build_tyre,
        "carton": build_cardboard,
        "rama": build_branch,
        "farola_mocha": build_lamp_stump,
    }

