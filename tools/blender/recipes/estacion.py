"""El trozo de estación que se recorre en la Fase 2 (docs/DEPOSITO.md, 4.8).

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba (en
Godot, la Y de Blender pasa a ser -Z). El origen es el centro de la cara de
fuera del muro de la consigna, a ras de suelo: el pasillo va de y = 0 (el muro
de la consigna y de los locales vecinos) a y = -6 (la arquería que da al andén
central), y de x = -15 a x = 15. Lo cubre una bóveda de 3,9 m en los muros a
5 m en el centro.

- Al fondo a la derecha (x = 15), el arranque de las escaleras mecánicas, con la
  reja cerrada; al fondo a la izquierda (x = -15), el paso tapado con una
  barricada de cajas y vallas.
- La arquería de enfrente tiene cuatro arcos por los que se ve la estación (la
  tienda de campaña, la ropa tendida, la gente), cerrados con vallas y bultos.

Modelos: "estacion_pasillo" (el pasillo, con sus colisiones), "estacion_fondo"
(lo que se ve por los arcos, sin colisiones), "escalera_mecanica" (las tres
escaleras paradas y su túnel), "puesto_comida" (el quiosco de la sopa),
"ventanilla_admin" (la ventanilla de la administración con el buzón de los
pagos), "tablon_avisos", "contenedor_estacion" (con su ``tapa``),
"banco_estacion" y "farol_estacion" (el aplique de los muros).
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Matrix

import tumansk_bpy as tb

# Paleta: el metro es más frío que la consigna, pero está igual de gastado.
GRANITE_A = "#7E7A74"
GRANITE_B = "#6A6560"
GRANITE_RED = "#7A4A40"
GRANITE_WORN = "#8E8982"
GROUT = "#3A3632"
MARBLE = "#D6CDB8"
MARBLE_B = "#C9BFA8"
MARBLE_VEIN = "#A89E88"
FRIEZE = "#8A5A44"
PLASTER = "#C8BFA8"
PLASTER_STAIN = "#968B74"
VAULT = "#D0C7B0"
BRASS = "#B59A5A"
BRASS_DARK = "#7E6A3E"
IRON = "#3C3A37"
STEEL = "#7D817E"
RUST = "#8E4A2F"
GREEN = "#3F5248"
GREEN_LIGHT = "#55615A"
WOOD = "#8A5A3B"
WOOD_DARK = "#6E4A32"
WOOD_LIGHT = "#9A6845"
PLANK = "#7B5A3E"
CANVAS = "#7A7458"
CANVAS_DARK = "#5E5A44"
TARP_BLUE = "#4A5A6A"
RED_FADED = "#9A4A3E"
CREAM = "#E2D8BF"
SIGN_GREEN = "#2E4A3E"
SIGN_RED = "#7A2E28"
CHALK_BOARD = "#2A302C"
SILHOUETTE = "#2A2628"
SILHOUETTE_B = "#34302F"
RUBBER = "#252321"

HALF_L = 15.0
DEPTH = 6.0
ARCADE = -6.0
ARCADE_T = 0.7
WALL_T = 0.4
SPRING = 3.9
CROWN = 5.0
SKIRT = 0.3
FRIEZE_Z = (3.3, 3.6)
# La consigna: lo que ocupa su fachada y sus huecos (el resto del muro es de la estación).
DEPOT_HALF = 4.8
WINDOW = (-1.5, 1.5, 2.3)
DOOR = (3.4, 4.3, 2.1)
# El rótulo de la consigna, por encima del cajón de la persiana.
SIGN_Z = 2.98
# La ventanilla de la administración, en el muro de los locales: x de -9,6 a -8,4.
ADMIN_X = -9.0
ADMIN_HOLE = (ADMIN_X - 0.6, 1.0, ADMIN_X + 0.6, 1.9)
# Los arcos de la arquería: centro en x, medio ancho y altura de la imposta.
ARCHES = (-11.0, -6.0, 6.0, 11.0)
ARCH_HALF = 1.3
ARCH_IMPOST = 2.5
# La boca de las escaleras (x = 15) y el paso tapado (x = -15).
ESCALATOR_Y = (-5.2, -0.8)
ESCALATOR_H = 3.5
BLOCKED_Y = (-4.6, -1.4)
BLOCKED_H = 3.0
VAULT_R = ((DEPTH / 2.0) ** 2 + (CROWN - SPRING) ** 2) / (2.0 * (CROWN - SPRING))


def vault_z(y: float) -> float:
    """La altura de la bóveda (por dentro) en ``y`` (de 0 a -6)."""
    d = max(-DEPTH / 2.0, min(DEPTH / 2.0, y + DEPTH / 2.0))
    return SPRING + math.sqrt(VAULT_R ** 2 - d * d) - math.sqrt(VAULT_R ** 2 - (DEPTH / 2.0) ** 2)


def _placed(mb: tb.MeshBuilder, matrix: Matrix, build) -> None:
    """Construye con ``build(mb)`` y lleva lo construido a su sitio con ``matrix``."""
    before = set(mb.bm.faces)
    build(mb)
    faces = [f for f in mb.bm.faces if f not in before]
    for v in list(dict.fromkeys(v for f in faces for v in f.verts)):
        v.co = matrix @ v.co


def _arch_top(mb: tb.MeshBuilder, x_center: float, half: float, impost: float, y_range: tuple, color: str, steps: int = 10) -> None:
    """Cierra en medio punto un hueco rectangular que llega hasta ``impost + half``:
    las enjutas (por tiras convexas) y el intradós del arco, a través del muro."""
    top = impost + half
    y0, y1 = y_range
    thickness = y1 - y0
    for side in (-1.0, 1.0):
        for k in range(steps):
            a0 = math.pi / 2.0 * k / steps
            a1 = math.pi / 2.0 * (k + 1) / steps
            x_a, z_a = x_center + side * half * math.cos(a0), impost + half * math.sin(a0)
            x_b, z_b = x_center + side * half * math.cos(a1), impost + half * math.sin(a1)
            outline = [(x_a, z_a), (x_b, z_b), (x_b, top), (x_a, top)]
            area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(outline, outline[1:] + outline[:1]))
            if area < 0.0:
                outline.reverse()
            mb.prism(outline, thickness, (0.0, (y0 + y1) / 2.0, 0.0), color, rotation=(90.0, 0.0, 0.0))
    # El intradós: la cara curva de dentro del arco.
    for k in range(2 * steps):
        a0 = math.pi * k / (2 * steps)
        a1 = math.pi * (k + 1) / (2 * steps)
        p0 = (x_center + half * math.cos(a0), impost + half * math.sin(a0))
        p1 = (x_center + half * math.cos(a1), impost + half * math.sin(a1))
        mb.quad([(p1[0], y1, p1[1]), (p0[0], y1, p0[1]), (p0[0], y0, p0[1]), (p1[0], y0, p1[1])], color)


# --------------------------------------------------------------------------
# El pasillo
# --------------------------------------------------------------------------


def _floor(root: bpy.types.Object, rng: random.Random) -> list:
    """Losas de granito de 60 × 60 cm a cuadros, con una cenefa roja junto a los
    muros; gastadas por donde se pasa (de la puerta de la consigna al puesto)."""
    size = 0.6
    cols, rows = int(2 * HALF_L / size), int(DEPTH / size)
    objects = []
    for start in range(0, rows, 2):
        mb = tb.MeshBuilder(seed=700 + start)
        end = min(rows, start + 2)
        y1, y0 = -start * size, -end * size
        mb.box((2 * HALF_L, y1 - y0, 0.04), (0.0, (y0 + y1) / 2.0, -0.02), GROUT)
        for j in range(start, end):
            for i in range(cols):
                x = -HALF_L + (i + 0.5) * size
                y = -(j + 0.5) * size
                border = j in (0, rows - 1)
                color = GRANITE_RED if border else (GRANITE_A if (i + j) % 2 == 0 else GRANITE_B)
                if not border and 2.0 < x < 9.0 and y > -3.0 and rng.random() < 0.6:
                    color = GRANITE_WORN
                mb.box((size - 0.008, size - 0.008, 0.03), (x, y, 0.015 + rng.uniform(-0.002, 0.002)), color, rotation=(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0.0), jitter=0.06)
        objects.append(mb.finish(f"suelo_{start // 2}", tb.material("estacion", GRANITE_A), root))
    return objects


def _cladding(mb: tb.MeshBuilder, rng: random.Random, x_range: tuple, y_face: float, facing: float, holes: list) -> None:
    """Chapado de mármol de un muro (placas de 75 × 50 cm sobre el rodapié de
    granito, con un friso rojo arriba), en el plano y = ``y_face``, mirando a
    ``facing`` en Y. ``holes`` son rectángulos (x0, z0, x1, z1) que se respetan."""
    x0, x1 = x_range
    y = y_face + facing * 0.012

    def pieces(xa: float, xb: float, za: float, zb: float) -> list:
        """Lo que queda de [xa, xb] fuera de los huecos que cortan la franja [za, zb]."""
        spans = [(xa, xb)]
        for h in holes:
            if za < h[3] and zb > h[1]:
                cut = []
                for a, b in spans:
                    if b <= h[0] or a >= h[2]:
                        cut.append((a, b))
                        continue
                    if a < h[0]:
                        cut.append((a, h[0]))
                    if b > h[2]:
                        cut.append((h[2], b))
                spans = cut
        return [(a, b) for a, b in spans if b - a > 0.04]

    # El rodapié de granito.
    x = x0
    while x < x1 - 0.01:
        xb = min(x + 0.9, x1)
        for a, b in pieces(x, xb, 0.0, SKIRT):
            mb.box((b - a - 0.006, 0.03, SKIRT), ((a + b) / 2.0, y_face + facing * 0.015, SKIRT / 2.0), GRANITE_RED, jitter=0.05)
        x = xb
    # Las placas de mármol.
    row = 0
    z = SKIRT
    while z < FRIEZE_Z[0] - 0.01:
        zb = min(z + 0.5, FRIEZE_Z[0])
        x = x0 - (0.375 if row % 2 else 0.0)
        while x < x1 - 0.01:
            xa, xb = max(x, x0), min(x + 0.75, x1)
            x += 0.75
            color = rng.choice((MARBLE, MARBLE, MARBLE_B))
            vein = rng.random() < 0.35
            for a, b in pieces(xa, xb, z, zb):
                mb.box((b - a - 0.006, 0.024, zb - z - 0.006), ((a + b) / 2.0, y, (z + zb) / 2.0), color, jitter=0.04)
                if vein and b - a > 0.5:
                    mb.box((0.3, 0.002, 0.008), ((a + b) / 2.0, y + facing * 0.013, (z + zb) / 2.0), MARBLE_VEIN, rotation=(0.0, 25.0 if row % 2 else -20.0, 0.0))
        z = zb
        row += 1
    # El friso, con su moldura.
    x = x0
    while x < x1 - 0.01:
        xb = min(x + 1.5, x1)
        for a, b in pieces(x, xb, FRIEZE_Z[0], FRIEZE_Z[1]):
            mb.box((b - a, 0.04, FRIEZE_Z[1] - FRIEZE_Z[0]), ((a + b) / 2.0, y_face + facing * 0.02, sum(FRIEZE_Z) / 2.0), FRIEZE, jitter=0.03)
            mb.box((b - a, 0.07, 0.05), ((a + b) / 2.0, y_face + facing * 0.035, FRIEZE_Z[1] + 0.025), MARBLE_B, bevel=0.01)
        x = xb


def _walls(root: bpy.types.Object, rng: random.Random) -> list:
    objects = []
    # El muro de los locales (y = 0), mirando al pasillo (-Y): fuera de la consigna,
    # macizo; delante de ella, solo el chapado (su muro ya está detrás).
    mb = tb.MeshBuilder(seed=801)
    mb.slab((-HALF_L, -DEPOT_HALF), (0.0, SPRING), (0.0, WALL_T), PLASTER, holes=[ADMIN_HOLE], step=1.0, back=False)
    mb.slab((DEPOT_HALF, HALF_L), (0.0, SPRING), (0.0, WALL_T), PLASTER, step=1.0, back=False)
    mb.slab((-DEPOT_HALF, DEPOT_HALF), (SKIRT * 0.0, SPRING), (-0.004, 0.0), PLASTER, holes=[(WINDOW[0], 0.0, WINDOW[1], WINDOW[2]), (DOOR[0], 0.0, DOOR[1], DOOR[2])], step=1.0, back=False)
    holes = [
        (WINDOW[0] - 0.1, 0.0, WINDOW[1] + 0.1, WINDOW[2] + 0.95),
        (DOOR[0] - 0.1, 0.0, DOOR[1] + 0.1, DOOR[2] + 0.12),
        (ADMIN_HOLE[0] - 0.08, ADMIN_HOLE[1] - 0.1, ADMIN_HOLE[2] + 0.08, ADMIN_HOLE[3] + 0.1),
    ]
    _cladding(mb, rng, (-HALF_L, HALF_L), 0.0, -1.0, holes)
    # El recercado de la ventanilla y de la puerta, de granito.
    for x0, x1, height in ((WINDOW[0], WINDOW[1], WINDOW[2]), (DOOR[0], DOOR[1], DOOR[2])):
        for x in (x0 - 0.05, x1 + 0.05):
            mb.box((0.1, 0.06, height + 0.1), (x, -0.03, (height + 0.1) / 2.0), GRANITE_B, bevel=0.01)
        mb.box((x1 - x0 + 0.2, 0.06, 0.1), ((x0 + x1) / 2.0, -0.03, height + 0.05), GRANITE_B, bevel=0.01)
    # El rótulo de la consigna, pintado sobre una tabla encima de la ventanilla.
    mb.box((3.4, 0.05, 0.5), (0.0, -0.03, SIGN_Z), SIGN_GREEN, bevel=0.012)
    mb.box((3.3, 0.054, 0.42), (0.0, -0.031, SIGN_Z), "#355648")
    back = mb.finish("muro_locales", tb.material("estacion", MARBLE), root)
    tb.stain(back, PLASTER_STAIN, amount=0.45, scale=1.4, coverage=0.35, seed=802)
    objects.append(back)

    # La arquería (y = -6), mirando a la consigna (+Y): se hace mirando a -Y y se
    # gira media vuelta (x pasa a -x; los arcos son simétricos).
    mb = tb.MeshBuilder(seed=811)
    holes = [(-c - ARCH_HALF, 0.0, -c + ARCH_HALF, ARCH_IMPOST + ARCH_HALF) for c in ARCHES]
    _placed(
        mb,
        Matrix.Translation((0.0, ARCADE, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
        lambda b: b.slab((-HALF_L, HALF_L), (0.0, SPRING), (0.0, ARCADE_T), PLASTER, holes=holes, step=1.0),
    )
    for c in ARCHES:
        _arch_top(mb, c, ARCH_HALF, ARCH_IMPOST, (ARCADE - ARCADE_T, ARCADE), PLASTER)
    _placed(
        mb,
        Matrix.Translation((0.0, ARCADE, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
        lambda b: _cladding(b, rng, (-HALF_L, HALF_L), 0.0, -1.0, [(-c - ARCH_HALF - 0.12, 0.0, -c + ARCH_HALF + 0.12, FRIEZE_Z[1] + 0.1) for c in ARCHES]),
    )
    # Las archivoltas de granito alrededor de cada arco.
    for c in ARCHES:
        for k in range(16):
            a0, a1 = math.pi * k / 16, math.pi * (k + 1) / 16
            r0, r1 = ARCH_HALF, ARCH_HALF + 0.14
            pts = [
                (c + r0 * math.cos(a0), ARCH_IMPOST + r0 * math.sin(a0)),
                (c + r1 * math.cos(a0), ARCH_IMPOST + r1 * math.sin(a0)),
                (c + r1 * math.cos(a1), ARCH_IMPOST + r1 * math.sin(a1)),
                (c + r0 * math.cos(a1), ARCH_IMPOST + r0 * math.sin(a1)),
            ]
            area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))
            if area < 0.0:
                pts.reverse()
            mb.prism(pts, 0.05, (0.0, ARCADE + 0.025, 0.0), GRANITE_B, rotation=(90.0, 0.0, 0.0))
        for x in (c - ARCH_HALF - 0.07, c + ARCH_HALF + 0.07):
            mb.box((0.14, 0.05, ARCH_IMPOST), (x, ARCADE + 0.025, ARCH_IMPOST / 2.0), GRANITE_B)
    arcade = mb.finish("arqueria", tb.material("estacion", MARBLE), root)
    tb.stain(arcade, PLASTER_STAIN, amount=0.45, scale=1.4, coverage=0.35, seed=812)
    objects.append(arcade)

    # Los muros de los extremos, con la boca de las escaleras (derecha) y el paso
    # tapado (izquierda), y sus tímpanos hasta la bóveda.
    mb = tb.MeshBuilder(seed=821)
    length = (ARCADE - ARCADE_T, WALL_T)
    # Izquierdo (x = -15), mirando a +X.
    _placed(
        mb,
        Matrix.Translation((-HALF_L, 0.0, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
        lambda b: b.slab(length, (0.0, SPRING), (0.0, WALL_T), PLASTER, holes=[(BLOCKED_Y[0], 0.0, BLOCKED_Y[1], BLOCKED_H)], step=1.0),
    )
    # Derecho (x = 15), mirando a -X.
    _placed(
        mb,
        Matrix.Translation((HALF_L, 0.0, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
        lambda b: b.slab((-length[1], -length[0]), (0.0, SPRING), (0.0, WALL_T), PLASTER, holes=[(-ESCALATOR_Y[1], 0.0, -ESCALATOR_Y[0], ESCALATOR_H)], step=1.0),
    )
    outline = [(0.0, SPRING - 0.01), (ARCADE, SPRING - 0.01)] + [(ARCADE + DEPTH * k / 24.0, vault_z(ARCADE + DEPTH * k / 24.0)) for k in range(25)]
    # El contorno va en (y, z): se levanta con un giro que lleva su X a la Y del modelo.
    for x, sign in ((-HALF_L - WALL_T / 2.0, 1.0), (HALF_L + WALL_T / 2.0, -1.0)):
        pts = [(sign * p[0], p[1]) for p in outline]
        area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(pts, pts[1:] + pts[:1]))
        if area < 0.0:
            pts.reverse()
        _placed(
            mb,
            Matrix.Translation((x, 0.0, 0.0)) @ Matrix.Rotation(sign * math.pi / 2.0, 4, "Z"),
            lambda b, pts=pts: b.prism(pts, WALL_T, (0.0, 0.0, 0.0), PLASTER, rotation=(90.0, 0.0, 0.0)),
        )
    ends = mb.finish("extremos", tb.material("estacion", PLASTER), root)
    tb.stain(ends, PLASTER_STAIN, amount=0.5, scale=1.2, coverage=0.4, seed=822)
    objects.append(ends)
    return objects


def _vault(root: bpy.types.Object, rng: random.Random) -> list:
    """La bóveda enlucida, con arcos fajones cada 5 m y la moldura de arranque."""
    mb = tb.MeshBuilder(seed=901)
    segments_y, segments_x = 12, 30
    for i in range(segments_x):
        x0 = -HALF_L + 2 * HALF_L * i / segments_x
        x1 = -HALF_L + 2 * HALF_L * (i + 1) / segments_x
        for j in range(segments_y):
            y0 = ARCADE + DEPTH * j / segments_y
            y1 = ARCADE + DEPTH * (j + 1) / segments_y
            mb.quad([(x0, y0, vault_z(y0)), (x0, y1, vault_z(y1)), (x1, y1, vault_z(y1)), (x1, y0, vault_z(y0))], VAULT, cuts=1)
    for x in (-12.5, -7.5, -2.5, 2.5, 7.5, 12.5):
        for j in range(segments_y):
            y0 = ARCADE + DEPTH * j / segments_y
            y1 = ARCADE + DEPTH * (j + 1) / segments_y
            ym = (y0 + y1) / 2.0
            tilt = math.degrees(math.atan2(vault_z(y1) - vault_z(y0), y1 - y0))
            mb.box((0.35, y1 - y0 + 0.02, 0.12), (x, ym, (vault_z(y0) + vault_z(y1)) / 2.0 - 0.05), MARBLE_B, rotation=(tilt, 0.0, 0.0))
    for y in (-0.06, ARCADE + 0.06):
        mb.box((2 * HALF_L, 0.14, 0.12), (0.0, y, SPRING - 0.04), MARBLE_B, bevel=0.015)
    vault = mb.finish("boveda", tb.material("estacion", VAULT), root)
    tb.stain(vault, PLASTER_STAIN, amount=0.3, scale=0.9, coverage=0.4, seed=902)
    return [vault]


def _services(root: bpy.types.Object, rng: random.Random) -> list:
    """Los cables que se tendieron después, por encima del friso de los locales,
    y los ganchos de las lámparas en la clave."""
    mb = tb.MeshBuilder(seed=951)
    for k, z in enumerate((3.72, 3.78, 3.84)):
        points = []
        for x in range(-15, 16):
            sag = 0.03 * math.sin(x * 1.7 + k)
            points.append((float(x), -0.08 - k * 0.03, z - abs(sag)))
        mb.tube(points, 0.012 - k * 0.002, ("#2A2725", "#3A3028", "#2E3438")[k], segments=5)
    for x in range(-14, 15, 2):
        mb.box((0.03, 0.12, 0.03), (float(x), -0.06, 3.86), IRON)
    for x in (-10.0, -2.5, 2.5, 10.0):
        mb.bar((x, -3.0, CROWN - 0.01), (x, -3.0, CROWN - 0.35), 0.008, IRON, 6)
    cables = mb.finish("cables", tb.material("metal", IRON), root)
    return [cables]


def _blockades(root: bpy.types.Object, rng: random.Random) -> list:
    """Lo que tapa los arcos y el paso de la izquierda: vallas de obra, tablones,
    cajas y fardos. No se pasa, pero se ve por encima y por las rendijas."""
    mb = tb.MeshBuilder(seed=961)
    for c in ARCHES:
        y = ARCADE - ARCADE_T / 2.0
        # La valla: dos postes y tablones clavados, alguno torcido.
        for x in (c - ARCH_HALF + 0.12, c + ARCH_HALF - 0.12):
            mb.box((0.1, 0.1, 1.5), (x, y, 0.75), WOOD_DARK, bevel=0.01)
        for k in range(4):
            z = 0.25 + k * 0.33
            mb.box((2 * ARCH_HALF - 0.1, 0.035, 0.18), (c + rng.uniform(-0.05, 0.05), y - 0.07, z), rng.choice((PLANK, WOOD, WOOD_LIGHT)), rotation=(0.0, rng.uniform(-4, 4), 0.0), bevel=0.006, jitter=0.06)
        # Unos fardos y cajas detrás.
        for k in range(rng.randint(2, 4)):
            size = (rng.uniform(0.4, 0.8), rng.uniform(0.4, 0.6), rng.uniform(0.3, 0.6))
            mb.box(size, (c + rng.uniform(-0.9, 0.9), y - 0.55 - rng.uniform(0.0, 0.3), size[2] / 2.0), rng.choice((CANVAS, CANVAS_DARK, WOOD, TARP_BLUE)), rotation=(0.0, 0.0, rng.uniform(-15, 15)), bevel=0.03, jitter=0.06)
    # La barricada del paso de la izquierda: cajas apiladas y un somier.
    x = -HALF_L - WALL_T / 2.0
    for k in range(9):
        size = (rng.uniform(0.5, 0.8), rng.uniform(0.5, 0.8), rng.uniform(0.4, 0.7))
        level = k // 4
        mb.box(size, (x + rng.uniform(-0.1, 0.4), BLOCKED_Y[0] + 0.4 + (k % 4) * 0.8, size[2] / 2.0 + level * 0.65), rng.choice((WOOD, WOOD_DARK, CANVAS, "#6A5A48")), rotation=(0.0, 0.0, rng.uniform(-10, 10)), bevel=0.02, jitter=0.06)
    for k in range(9):
        mb.bar((x + 0.3, BLOCKED_Y[0] + 0.2 + k * 0.38, 1.4), (x + 0.3, BLOCKED_Y[0] + 0.2 + k * 0.38, 2.6), 0.012, IRON, 6)
    mb.box((0.05, BLOCKED_Y[1] - BLOCKED_Y[0], 1.2), (x + 0.3, sum(BLOCKED_Y) / 2.0, 2.0), "#5A5650")
    blockades = mb.finish("barricadas", tb.material("madera", WOOD), root)
    return [blockades]


def build_corridor() -> bpy.types.Object:
    root = tb.empty("estacion_pasillo-estatico")
    rng = random.Random(7)
    pieces = []
    pieces += _floor(root, rng)
    pieces += _walls(root, rng)
    pieces += _vault(root, rng)
    pieces += _services(root, rng)
    pieces += _blockades(root, rng)
    tb.collision_box("suelo", (2 * HALF_L + 2.0, DEPTH + 2.0, 0.2), (0.0, ARCADE / 2.0, -0.1), root)
    tb.collision_box("locales_izq", (HALF_L - DEPOT_HALF, WALL_T, SPRING), (-(HALF_L + DEPOT_HALF) / 2.0, WALL_T / 2.0, SPRING / 2.0), root)
    tb.collision_box("locales_der", (HALF_L - DEPOT_HALF, WALL_T, SPRING), ((HALF_L + DEPOT_HALF) / 2.0, WALL_T / 2.0, SPRING / 2.0), root)
    tb.collision_box("arqueria", (2 * HALF_L, ARCADE_T + 0.6, SPRING), (0.0, ARCADE - (ARCADE_T + 0.6) / 2.0 + 0.0, SPRING / 2.0), root)
    tb.collision_box("extremo_izq", (WALL_T + 0.8, DEPTH + 1.0, SPRING), (-HALF_L - (WALL_T + 0.8) / 2.0 + 0.3, ARCADE / 2.0, SPRING / 2.0), root)
    # El extremo de la derecha deja libre la boca de las escaleras mecánicas (se sube por ellas).
    x_right = HALF_L + WALL_T / 2.0 + 0.3
    y0, y1 = ESCALATOR_Y
    tb.collision_box("extremo_der", (WALL_T, y0 - (ARCADE - 0.5), SPRING), (x_right, (y0 + ARCADE - 0.5) / 2.0, SPRING / 2.0), root)
    tb.collision_box("extremo_der_fachada", (WALL_T, 0.5 - y1, SPRING), (x_right, (0.5 + y1) / 2.0, SPRING / 2.0), root)
    tb.collision_box("extremo_der_dintel", (WALL_T, y1 - y0, SPRING - ESCALATOR_H), (x_right, (y0 + y1) / 2.0, (SPRING + ESCALATOR_H) / 2.0), root)
    tb.collision_box("techo", (2 * HALF_L, DEPTH, 0.3), (0.0, ARCADE / 2.0, CROWN + 0.15), root)
    tb.paint({p: None for p in pieces}, samples=12, ao=0.45, ao_distance=0.4, seed=7)
    return root


# --------------------------------------------------------------------------
# Lo que se ve por los arcos
# --------------------------------------------------------------------------


def _person(mb: tb.MeshBuilder, x: float, y: float, height: float, rng: random.Random, facing: float = 0.0) -> None:
    """Una figura de gente, en silueta: cuerpo con abrigo, cabeza y, a veces, un bulto."""
    color = rng.choice((SILHOUETTE, SILHOUETTE_B))
    scale = height / 1.7
    mb.lathe([(0.0, 0.0), (0.2 * scale, 0.0), (0.22 * scale, 0.6 * scale), (0.2 * scale, 1.25 * scale), (0.12 * scale, 1.42 * scale), (0.0, 1.45 * scale)], (x, y, 0.0), color, segments=8)
    mb.sphere(0.11 * scale, (x, y, 1.56 * scale), color, segments=8)
    if rng.random() < 0.5:
        mb.box((0.3 * scale, 0.25 * scale, 0.35 * scale), (x + 0.18 * scale * math.cos(facing), y + 0.18 * scale * math.sin(facing), 1.0 * scale), color, rotation=(0.0, 0.0, math.degrees(facing)), bevel=0.03)
    if rng.random() < 0.4:
        mb.cylinder(0.13 * scale, 0.1 * scale, (x, y, 1.68 * scale), color, segments=8)


def build_background() -> bpy.types.Object:
    """La estación al otro lado de la arquería: el andén central lleno de vida
    (tiendas de campaña, ropa tendida, una hoguera, la gente), sin colisiones."""
    rng = random.Random(1001)
    root = tb.empty("estacion_fondo")
    mb = tb.MeshBuilder(seed=1001)
    far = ARCADE - ARCADE_T
    hall_depth = 10.0
    mb.box((2 * HALF_L + 6.0, hall_depth, 0.04), (0.0, far - hall_depth / 2.0, -0.02), GRANITE_B, cuts=4)
    for x in range(-16, 17, 2):
        for y in range(1, 9, 2):
            mb.box((1.96, 1.96, 0.012), (float(x), far - float(y), 0.006), rng.choice((GRANITE_A, GRANITE_B, "#5E5A55")))
    # El muro del fondo, lejos, y la bóveda grande.
    mb.box((2 * HALF_L + 6.0, 0.4, 7.0), (0.0, far - hall_depth, 3.5), "#5E5850")
    for k in range(12):
        y0 = far - hall_depth * k / 12
        y1 = far - hall_depth * (k + 1) / 12
        z0 = 6.0 + 1.6 * math.sin(math.pi * k / 12)
        z1 = 6.0 + 1.6 * math.sin(math.pi * (k + 1) / 12)
        mb.quad([(-HALF_L - 3.0, y1, z1), (HALF_L + 3.0, y1, z1), (HALF_L + 3.0, y0, z0), (-HALF_L - 3.0, y0, z0)], "#6E6658", cuts=2)
    # Las columnas del andén.
    for x in (-13.5, -8.5, -3.5, 3.5, 8.5, 13.5):
        mb.box((0.8, 0.8, 6.2), (x, far - 2.4, 3.1), MARBLE_B, bevel=0.03)
        mb.box((1.0, 1.0, 0.3), (x, far - 2.4, 0.15), GRANITE_RED)
    # Tiendas de campaña: prismas de lona con su palo y sus vientos.
    for x, y, w, d, h, color in ((-11.0, 4.6, 2.2, 1.8, 1.5, CANVAS), (-5.6, 5.2, 2.6, 2.0, 1.7, TARP_BLUE), (5.8, 4.8, 2.0, 1.8, 1.4, CANVAS_DARK), (11.2, 5.4, 2.4, 2.2, 1.6, RED_FADED), (0.4, 6.6, 3.0, 2.2, 1.8, CANVAS)):
        y_c = far - y
        outline = [(-w / 2.0, 0.0), (w / 2.0, 0.0), (0.0, h)]
        mb.prism(outline, d, (x, y_c, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.05)
        mb.bar((x, y_c + d / 2.0 + 0.05, 0.0), (x, y_c + d / 2.0 + 0.05, h + 0.15), 0.025, WOOD_DARK, 6)
    # Ropa tendida entre las columnas.
    for x0, x1, y in ((-13.5, -8.5, 2.4), (3.5, 8.5, 2.4), (-8.5, -3.5, 2.4)):
        y_c = far - y
        rope = [(x0 + (x1 - x0) * t / 10.0, y_c, 2.6 - 0.3 * math.sin(math.pi * t / 10.0)) for t in range(11)]
        mb.tube(rope, 0.008, "#8A8070", segments=4)
        for k in range(1, 10, 2):
            px, _, pz = rope[k]
            mb.box((0.35, 0.02, rng.uniform(0.4, 0.7)), (px, y_c, pz - 0.3), rng.choice((CREAM, "#8A9AA8", RED_FADED, "#A8A070", "#6A7A5A")), rotation=(0.0, rng.uniform(-4, 4), 0.0))
    # Una hoguera en un bidón, con gente alrededor; bultos, cajas y un carro.
    mb.cylinder(0.3, 0.85, (-2.6, far - 3.4, 0.425), RUST, segments=12)
    for k in range(6):
        size = (rng.uniform(0.4, 0.9), rng.uniform(0.4, 0.7), rng.uniform(0.3, 0.6))
        mb.box(size, (rng.uniform(-14.0, 14.0), far - rng.uniform(1.0, 7.0), size[2] / 2.0), rng.choice((WOOD, CANVAS, TARP_BLUE, CANVAS_DARK)), rotation=(0.0, 0.0, rng.uniform(0, 90)), bevel=0.03)
    for x, y, h in ((-3.3, 3.0, 1.72), (-1.9, 3.1, 1.6), (-2.7, 4.2, 1.2), (-9.4, 2.2, 1.76), (7.4, 3.6, 1.66), (9.9, 2.6, 1.7), (2.6, 4.0, 1.58), (12.6, 6.4, 1.74), (-12.9, 6.0, 1.68), (4.6, 7.4, 1.0)):
        _person(mb, x, far - y, h, rng, facing=rng.uniform(0, 2 * math.pi))
    hall = mb.finish("fondo", tb.material("estacion", GRANITE_B), root)
    tb.paint({hall: None}, samples=6, ao=0.35, ao_distance=0.6, seed=1001)
    return root


# --------------------------------------------------------------------------
# Las escaleras mecánicas
# --------------------------------------------------------------------------


def build_escalator() -> bpy.types.Object:
    """Las tres escaleras mecánicas paradas, que suben a 30° hacia la compuerta,
    con sus balaustradas de madera, las lámparas de columna apagadas y el túnel.
    El origen está en la boca (x = 0 es el muro del pasillo). La ``reja`` de abajo
    está cerrada con cadena y candado."""
    root = tb.empty("escalera_mecanica-estatico")
    rise = math.tan(math.radians(30.0))
    landing = 1.6
    run = 13.0
    y0, y1 = ESCALATOR_Y
    width = y1 - y0
    mb = tb.MeshBuilder(seed=1101)
    # El rellano de abajo y los peines.
    mb.box((landing, width, 0.04), (landing / 2.0, (y0 + y1) / 2.0, 0.02), "#5A5650", cuts=2)
    lanes = [y0 + 0.4 + k * 1.4 + 0.5 for k in range(3)]
    for y in lanes:
        mb.box((0.3, 0.95, 0.03), (landing - 0.15, y, 0.045), BRASS_DARK)
        # Los peldaños: dientes de sierra que suben.
        step = 0.4
        count = int(run / step)
        for k in range(count):
            x = landing + k * step
            z = k * step * rise
            mb.box((step, 0.95, 0.03), (x + step / 2.0, y, z + step * rise), "#3A3836")
            mb.box((0.02, 0.95, step * rise), (x + 0.01, y, z + step * rise / 2.0), "#2E2C2A")
    # Las balaustradas: cajones de madera inclinados con su pasamanos de goma.
    for k in range(4):
        y = y0 + 0.2 + k * 1.4
        length = run / math.cos(math.radians(30.0))
        mb.box((length, 0.26, 0.9), (landing + run / 2.0, y, run * rise / 2.0 + 0.45), WOOD, rotation=(0.0, -30.0, 0.0), bevel=0.02, jitter=0.05)
        mb.box((length, 0.1, 0.06), (landing + run / 2.0, y, run * rise / 2.0 + 0.95), RUBBER, rotation=(0.0, -30.0, 0.0), bevel=0.02)
        mb.box((landing, 0.26, 0.9), (landing / 2.0, y, 0.45), WOOD, bevel=0.02)
        mb.box((landing, 0.1, 0.06), (landing / 2.0, y, 0.95), RUBBER, bevel=0.02)
        # Las lámparas de columna (las de las escaleras de Moscú), apagadas.
        if 0 < k < 3:
            for j in range(4):
                x = landing + 2.0 + j * 3.0
                z = (x - landing) * rise + 0.9
                mb.bar((x, y, z), (x, y, z + 0.9), 0.025, BRASS_DARK, 8)
                mb.lathe([(0.0, 0.0), (0.07, 0.02), (0.08, 0.2), (0.05, 0.26), (0.0, 0.27)], (x, y, z + 0.9), "#C8C0A8", segments=10)
    # El túnel inclinado: una bóveda de medio punto sobre las escaleras.
    radius = width / 2.0 + 0.3
    for i in range(10):
        xa = landing + run * i / 10.0 - 0.5
        xb = landing + run * (i + 1) / 10.0 - 0.5
        for j in range(12):
            a0, a1 = math.pi * j / 12, math.pi * (j + 1) / 12
            ya, yb = (y0 + y1) / 2.0 + radius * math.cos(a0), (y0 + y1) / 2.0 + radius * math.cos(a1)
            za, zb = 2.6 + radius * math.sin(a0) * 0.8, 2.6 + radius * math.sin(a1) * 0.8
            h0, h1 = (xa - landing) * rise, (xb - landing) * rise
            mb.quad([(xa, yb, zb + max(0.0, h0)), (xa, ya, za + max(0.0, h0)), (xb, ya, za + max(0.0, h1)), (xb, yb, zb + max(0.0, h1))], "#4A4640")
    for y in (y0 - 0.3, y1 + 0.3):
        mb.box((run + landing, 0.2, 3.0), ((run + landing) / 2.0, y, run * rise / 2.0 + 1.0), "#4A4640", rotation=(0.0, -24.0, 0.0))
    stairs = mb.finish("escaleras", tb.material("estacion", "#4A4640"), root)
    # La reja: barrotes de hierro, con cadena y candado en el centro.
    gate = tb.MeshBuilder(seed=1102)
    gate.box((0.06, width, 0.06), (0.15, (y0 + y1) / 2.0, ESCALATOR_H - 0.3), IRON)
    gate.box((0.06, width, 0.06), (0.15, (y0 + y1) / 2.0, 0.12), IRON)
    gate.box((0.06, width, 0.05), (0.15, (y0 + y1) / 2.0, 1.2), IRON)
    k = 0
    y = y0 + 0.06
    while y < y1 - 0.03:
        gate.bar((0.15, y, 0.04), (0.15, y, ESCALATOR_H - 0.25), 0.012, IRON, 6)
        if k % 2 == 0:
            gate.lathe([(0.0, 0.0), (0.02, 0.02), (0.0, 0.06)], (0.15, y, ESCALATOR_H - 0.25), IRON, segments=6)
        y += 0.14
        k += 1
    for j in range(7):
        gate.lathe([(0.018, -0.006), (0.024, 0.0), (0.018, 0.006)], (0.1, (y0 + y1) / 2.0 - 0.18 + j * 0.06, 1.05 - 0.02 * math.sin(j)), STEEL, rotation=(90.0 if j % 2 else 0.0, 0.0, 0.0), segments=8)
    gate.box((0.03, 0.06, 0.07), (0.08, (y0 + y1) / 2.0 + 0.03, 0.98), BRASS, bevel=0.006)
    gate_obj = gate.finish("reja", tb.material("metal", IRON), root)
    tb.stain(gate_obj, RUST, amount=0.6, scale=6.0, coverage=0.35, seed=1103)
    tb.collision_box("reja", (0.3, width, ESCALATOR_H), (0.15, (y0 + y1) / 2.0, ESCALATOR_H / 2.0), root)
    tb.paint({stairs: None, gate_obj: None}, samples=8, ao=0.4, ao_distance=0.4, seed=1101)
    return root


# --------------------------------------------------------------------------
# El puesto de comida
# --------------------------------------------------------------------------


def build_food_stall() -> bpy.types.Object:
    """El quiosco de la sopa, pegado a la consigna: de tablas, con el mostrador al
    pasillo (hacia -Y), el samovar, las ollas en el hornillo, los tarros y el pan
    en la balda, la pizarra de los precios (la escribe Godot) y el toldo."""
    rng = random.Random(1201)
    root = tb.empty("puesto_comida-estatico")
    width, depth, height = 3.0, 1.7, 2.4
    counter_y, counter_h = -depth + 0.25, 1.0
    mb = tb.MeshBuilder(seed=1201)
    # Los costados y el fondo, de tablas.
    for side in (-1.0, 1.0):
        x = side * (width / 2.0 - 0.03)
        for k in range(10):
            y = -depth + 0.085 + k * 0.17
            mb.box((0.04, 0.165, height), (x, y, height / 2.0), rng.choice((PLANK, WOOD, "#6F5038")), bevel=0.004, jitter=0.06)
    for k in range(18):
        x = -width / 2.0 + 0.085 + k * 0.167
        mb.box((0.165, 0.04, height), (x, -0.03, height / 2.0), rng.choice((PLANK, WOOD, "#6F5038")), bevel=0.004, jitter=0.06)
    # El techo y el toldo a rayas.
    mb.box((width + 0.1, depth + 0.1, 0.06), (0.0, -depth / 2.0, height + 0.03), WOOD_DARK, bevel=0.01)
    for k in range(10):
        x0 = -width / 2.0 - 0.1 + k * (width + 0.2) / 10.0
        color = RED_FADED if k % 2 == 0 else CREAM
        mb.box(((width + 0.2) / 10.0, 0.8, 0.02), (x0 + (width + 0.2) / 20.0, -depth - 0.35, height - 0.12), color, rotation=(18.0, 0.0, 0.0), cuts=1, jitter=0.04)
    # El mostrador: frente de tablas y tablero gastado.
    mb.box((width - 0.08, 0.05, counter_h), (0.0, counter_y - 0.2, counter_h / 2.0), WOOD, bevel=0.006, cuts=2)
    mb.box((width - 0.02, 0.55, 0.05), (0.0, counter_y, counter_h + 0.025), WOOD_LIGHT, bevel=0.008, jitter=0.04)
    # La balda del fondo con los tarros y los panes.
    for z in (1.3, 1.75):
        mb.box((width - 0.12, 0.3, 0.03), (0.0, -0.2, z), WOOD_DARK, bevel=0.004)
        for k in range(7):
            x = -width / 2.0 + 0.3 + k * 0.38
            if z < 1.5:
                mb.cylinder(0.06, 0.16, (x, -0.2, z + 0.095), rng.choice(("#A8A070", "#8A6A40", "#C8B08A")), segments=10)
                mb.cylinder(0.065, 0.02, (x, -0.2, z + 0.185), STEEL, segments=10)
            else:
                mb.sphere(0.1, (x, -0.2, z + 0.06), "#6E4A2A", segments=10, scale=(1.3, 0.8, 0.6), jitter=0.05)
    # El hornillo con las dos ollas, junto al costado izquierdo.
    mb.box((0.9, 0.45, 0.8), (-0.85, -0.55, 0.4), IRON, bevel=0.01)
    for x in (-1.08, -0.62):
        mb.lathe([(0.0, 0.0), (0.17, 0.0), (0.18, 0.28), (0.16, 0.28), (0.16, 0.02), (0.0, 0.02)], (x, -0.55, 0.8), "#6E6A62", segments=14)
        mb.cylinder(0.155, 0.01, (x, -0.55, 1.03), "#8A6A3A", segments=14)
    # El samovar, sobre el mostrador a la derecha.
    sx, sy = 0.95, counter_y + 0.05
    mb.lathe([(0.0, 0.0), (0.1, 0.0), (0.12, 0.05), (0.08, 0.1), (0.15, 0.2), (0.16, 0.38), (0.12, 0.46), (0.05, 0.5), (0.06, 0.58), (0.0, 0.6)], (sx, sy, counter_h + 0.05), BRASS, segments=16)
    mb.bar((sx, sy - 0.15, counter_h + 0.2), (sx, sy - 0.24, counter_h + 0.18), 0.012, BRASS_DARK, 6)
    for side in (-1.0, 1.0):
        mb.tube([(sx + side * 0.15, sy, counter_h + 0.42), (sx + side * 0.22, sy, counter_h + 0.4), (sx + side * 0.21, sy, counter_h + 0.3)], 0.01, BRASS_DARK, segments=6)
    # Los cuencos apilados y un cucharón.
    for k in range(4):
        mb.lathe([(0.0, 0.0), (0.05, 0.0), (0.08, 0.05), (0.075, 0.05), (0.045, 0.006), (0.0, 0.006)], (-0.3, counter_y + 0.1, counter_h + 0.05 + k * 0.022), "#E3DCC6", segments=12)
    # La pizarra de los precios, colgada del techo sobre el mostrador.
    mb.box((1.2, 0.03, 0.55), (0.0, -depth + 0.02, height - 0.42), CHALK_BOARD, bevel=0.005)
    mb.box((1.26, 0.035, 0.6), (0.0, -depth + 0.025, height - 0.42), WOOD_DARK, bevel=0.005)
    stall = mb.finish("puesto", tb.material("madera", WOOD), root)
    tb.stain(stall, "#4A3A2E", amount=0.45, scale=3.0, coverage=0.35, seed=1202)
    tb.collision_box("mostrador", (width, 0.6, counter_h + 0.05), (0.0, counter_y - 0.03, (counter_h + 0.05) / 2.0), root)
    for side in (-1.0, 1.0):
        tb.collision_box(f"costado_{'izq' if side < 0 else 'der'}", (0.06, depth, height), (side * (width / 2.0 - 0.03), -depth / 2.0, height / 2.0), root)
    tb.collision_box("fondo", (width, 0.06, height), (0.0, -0.03, height / 2.0), root)
    tb.paint({stall: None}, samples=12, ao=0.45, ao_distance=0.35, seed=1201)
    return root


# --------------------------------------------------------------------------
# La ventanilla de la administración, el tablón y el resto
# --------------------------------------------------------------------------


def build_admin_window() -> bpy.types.Object:
    """La ventanilla de la administración: un hueco en el muro con su reja, la
    cortinilla echada, el poyete, el rótulo y, a la derecha, el buzón de los pagos
    (una caja de chapa verde con su ranura), mirando al pasillo (-Y). Los rótulos
    los escribe Godot sobre sus tablas."""
    root = tb.empty("ventanilla_admin-estatico")
    mb = tb.MeshBuilder(seed=1301)
    width, sill, top = 1.2, 1.0, 1.9
    # El marco y el fondo (la cortinilla echada, con luz detrás: la pone Godot).
    mb.box((width + 0.2, 0.12, 0.1), (0.0, -0.06, sill - 0.05), GRANITE_B, bevel=0.01)
    mb.box((width + 0.2, 0.12, 0.1), (0.0, -0.06, top + 0.05), GRANITE_B, bevel=0.01)
    for x in (-width / 2.0 - 0.05, width / 2.0 + 0.05):
        mb.box((0.1, 0.12, top - sill + 0.2), (x, -0.06, (sill + top) / 2.0), GRANITE_B, bevel=0.01)
    mb.box((width + 0.1, 0.3, 0.05), (0.0, -0.12, sill), GRANITE_A, bevel=0.01)
    # La reja: barrotes verticales y un pasaplatos abajo.
    for k in range(9):
        x = -width / 2.0 + 0.1 + k * 0.125
        mb.bar((x, -0.03, sill + 0.14), (x, -0.03, top), 0.008, IRON, 6)
    mb.box((width, 0.02, 0.02), (0.0, -0.03, sill + 0.14), IRON)
    # El rótulo.
    mb.box((2.3, 0.04, 0.32), (0.25, -0.04, top + 0.42), SIGN_RED, bevel=0.01)
    window = mb.finish("ventanilla", tb.material("estacion", GRANITE_B), root)
    curtain = tb.MeshBuilder(seed=1304)
    curtain.box((width, 0.02, top - sill), (0.0, 0.08, (sill + top) / 2.0), "#E0C890", cuts=3)
    for k in range(10):
        curtain.box((0.03, 0.01, top - sill), (-width / 2.0 + 0.06 + k * 0.12, 0.068, (sill + top) / 2.0), "#C8A870")
    curtain_obj = curtain.finish("cortinilla", tb.material("cortina_luz", "#E0C890"), root)
    # El buzón de los pagos.
    box = tb.MeshBuilder(seed=1302)
    bx = width / 2.0 + 0.55
    box.box((0.42, 0.22, 0.55), (bx, -0.11, 1.25), GREEN, bevel=0.02, cuts=2)
    box.box((0.46, 0.25, 0.04), (bx, -0.115, 1.54), GREEN_LIGHT, bevel=0.01, rotation=(6.0, 0.0, 0.0))
    box.box((0.26, 0.012, 0.03), (bx, -0.226, 1.38), "#151514")
    box.box((0.3, 0.008, 0.012), (bx, -0.228, 1.405), BRASS_DARK)
    box.box((0.3, 0.006, 0.11), (bx, -0.224, 1.17), CREAM)
    box.cylinder(0.02, 0.02, (bx + 0.12, -0.228, 1.05), BRASS, rotation=(90.0, 0.0, 0.0), segments=10)
    mailbox = box.finish("buzon", tb.material("metal", GREEN), root)
    tb.stain(mailbox, RUST, amount=0.5, scale=8.0, coverage=0.3, seed=1303)
    tb.collision_box("ventanilla", (width + 0.3, 0.32, 0.12), (0.0, -0.13, sill), root)
    tb.collision_box("buzon", (0.44, 0.24, 0.6), (bx, -0.12, 1.25), root)
    tb.paint({window: None, mailbox: None, curtain_obj: None}, samples=10, ao=0.4, ao_distance=0.3, ground_z=None, seed=1301)
    return root


def build_notice_board() -> bpy.types.Object:
    """El tablón de avisos de la estación: un tablero de contrachapado con marco y
    tejadillo, colgado del muro (espalda en y = 0, cara a -Y), y su rótulo. Los
    papeles los pone Godot."""
    root = tb.empty("tablon_avisos-estatico")
    width, height, bottom = 2.6, 1.4, 0.9
    mb = tb.MeshBuilder(seed=1401)
    mb.box((width, 0.03, height), (0.0, -0.015, bottom + height / 2.0), "#B0956A", cuts=4, jitter=0.04)
    for x in (-width / 2.0, width / 2.0):
        mb.box((0.06, 0.06, height + 0.06), (x, -0.03, bottom + height / 2.0), WOOD_DARK, bevel=0.006)
    for z in (bottom, bottom + height):
        mb.box((width + 0.06, 0.06, 0.06), (0.0, -0.03, z), WOOD_DARK, bevel=0.006)
    mb.box((width + 0.3, 0.32, 0.03), (0.0, -0.15, bottom + height + 0.18), WOOD_DARK, rotation=(14.0, 0.0, 0.0), bevel=0.006)
    mb.box((1.3, 0.035, 0.22), (0.0, -0.04, bottom + height + 0.05), SIGN_GREEN, bevel=0.008)
    board = mb.finish("tablon", tb.material("madera", "#B0956A"), root)
    tb.collision_box("tablon", (width + 0.1, 0.08, height + 0.1), (0.0, -0.04, bottom + height / 2.0), root)
    tb.paint({board: None}, samples=10, ao=0.35, ground_z=None, seed=1401)
    return root


def build_station_bin() -> bpy.types.Object:
    """El contenedor de la basura de la estación: de chapa, con ruedas, y la
    ``tapa`` con el origen en las bisagras (atrás), mirando al pasillo (-Y)."""
    root = tb.empty("contenedor_estacion-estatico")
    width, depth, height = 1.3, 0.85, 1.05
    mb = tb.MeshBuilder(seed=1501)
    mb.box((width, depth, height - 0.15), (0.0, 0.0, 0.15 + (height - 0.15) / 2.0), "#4A5A4E", bevel=0.02, cuts=3)
    for x in (-width / 2.0 + 0.12, width / 2.0 - 0.12):
        for y in (-depth / 2.0 + 0.12, depth / 2.0 - 0.12):
            mb.cylinder(0.07, 0.05, (x, y, 0.07), RUBBER, rotation=(0.0, 90.0, 0.0), segments=10)
    for z in (0.45, 0.8):
        mb.box((width + 0.02, 0.03, 0.05), (0.0, -depth / 2.0 - 0.01, z), "#3E4A40")
    mb.box((width + 0.12, 0.05, 0.05), (0.0, -depth / 2.0 - 0.04, height - 0.12), STEEL, bevel=0.01)
    body = mb.finish("contenedor", tb.material("metal", "#4A5A4E"), root)
    tb.stain(body, RUST, amount=0.6, scale=4.0, coverage=0.35, seed=1502)
    lid_root = tb.empty("tapa", root)
    lid_root.location = (0.0, depth / 2.0, height)
    lid = tb.MeshBuilder(seed=1503)
    lid.box((width + 0.04, depth + 0.04, 0.04), (0.0, -depth / 2.0, 0.02), "#3E4A40", bevel=0.01, cuts=2)
    lid_obj = lid.finish("tapa_malla", tb.material("metal", "#3E4A40"), lid_root)
    tb.collision_box("contenedor", (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({body: None, lid_obj: None}, samples=10, ao=0.4, seed=1501)
    return root


def build_bench() -> bpy.types.Object:
    """Un banco de la estación: listones de madera sobre patas de fundición."""
    root = tb.empty("banco_estacion-estatico")
    mb = tb.MeshBuilder(seed=1601)
    length = 1.8
    for k in range(4):
        mb.box((length, 0.09, 0.035), (0.0, -0.17 + k * 0.105, 0.45), WOOD_LIGHT, bevel=0.006, jitter=0.05)
    for k in range(3):
        mb.box((length, 0.035, 0.09), (0.0, 0.25, 0.6 + k * 0.12), WOOD_LIGHT, rotation=(-12.0, 0.0, 0.0), bevel=0.006, jitter=0.05)
    for x in (-length / 2.0 + 0.15, length / 2.0 - 0.15):
        mb.box((0.06, 0.5, 0.05), (x, 0.0, 0.42), IRON, bevel=0.006)
        mb.box((0.06, 0.05, 0.42), (x, -0.2, 0.21), IRON, bevel=0.006)
        mb.box((0.06, 0.05, 0.85), (x, 0.24, 0.425), IRON, rotation=(-8.0, 0.0, 0.0), bevel=0.006)
    bench = mb.finish("banco", tb.material("madera", WOOD_LIGHT), root)
    tb.collision_box("banco", (length, 0.55, 0.48), (0.0, 0.02, 0.24), root)
    tb.paint({bench: None}, samples=10, ao=0.4, seed=1601)
    return root


def build_wall_lamp() -> bpy.types.Object:
    """El aplique de los muros: brazo de latón y globo de cristal esmerilado
    ("globo"), con la espalda en y = 0 y mirando a -Y."""
    root = tb.empty("farol_estacion")
    mb = tb.MeshBuilder(seed=1701)
    mb.box((0.14, 0.03, 0.22), (0.0, -0.015, 0.0), BRASS_DARK, bevel=0.01)
    mb.tube([(0.0, -0.03, 0.0), (0.0, -0.18, 0.05), (0.0, -0.3, 0.02)], 0.014, BRASS, segments=8)
    mb.lathe([(0.0, 0.0), (0.05, 0.0), (0.06, 0.04), (0.0, 0.045)], (0.0, -0.3, -0.02), BRASS, segments=12)
    arm = mb.finish("brazo", tb.material("metal", BRASS), root)
    globe = tb.MeshBuilder(seed=1702)
    globe.sphere(0.12, (0.0, -0.3, -0.13), "#F0E6C8", segments=14)
    globe_obj = globe.finish("globo", tb.material("bombilla", "#F0E6C8"), root)
    tb.paint({arm: None, globe_obj: None}, samples=6, ao=0.2, ground_z=None, seed=1701)
    return root


def models() -> dict:
    return {
        "estacion_pasillo": build_corridor,
        "estacion_fondo": build_background,
        "escalera_mecanica": build_escalator,
        "puesto_comida": build_food_stall,
        "ventanilla_admin": build_admin_window,
        "tablon_avisos": build_notice_board,
        "contenedor_estacion": build_station_bin,
        "banco_estacion": build_bench,
        "farol_estacion": build_wall_lamp,
    }
