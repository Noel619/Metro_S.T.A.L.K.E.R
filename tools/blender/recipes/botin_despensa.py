"""El botín de la despensa y de la casa: lo que se encuentra en los pisos, los
quioscos, las tiendas y los trasteros de la superficie.

- De comer: la leche condensada, los espadines en aceite, el tarro de pepinillos
  de alguna abuela y el azúcar en terrones.
- De la casa: las velas, el jabón de lavar y la taza de chapa esmaltada.
- De abrigo: las manoplas de lana y el gorro de orejeras.
- Personales: la foto enmarcada y el paquete de correos que nunca llegó.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Todo
descansa sobre z = 0 y lo que tiene cara (las etiquetas, la foto) la enseña hacia
-Y. Las reglas del botín (nada está intacto) están en tools/blender/botin_bpy.py.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Matrix, Vector

import botin_bpy as bb
import tumansk_bpy as tb

INK = "#1B1A22"
TIN = "#A9A49A"
TIN_DARK = "#86817A"
RUST = "#7E4128"
RUST_DARK = "#5A2E1C"
DIRT = "#4E4233"
WATER_STAIN = "#A38E66"
MILK_BLUE = "#3B5F8C"
MILK_CREAM = "#DAD5C4"
GOLD_TIN = "#B39552"
GOLD_DARK = "#8A7038"
GOLD_RELIEF = "#7E622E"
BRINE = "#8C9262"
GLASS_PALE = "#A9B2A6"
PICKLE = "#4F6B30"
PICKLE_DARK = "#3A5224"
GARLIC = "#D9D0B0"
PEPPER = "#2A2420"
LID_TIN = "#8C8670"
BOX_WHITE = "#D6D0BE"
SUGAR = "#E6E1D3"
SUGAR_SHADE = "#D2CCBC"
BOX_BLUE = "#4A6A9A"
BOX_RED = "#9A3A30"
CANDLE = "#E4DCC4"
WICK = "#2A2522"
KRAFT = "#9C7A52"
KRAFT_LIGHT = "#B08E62"
STRING = "#C8B48A"
SOAP = "#7A5428"
SOAP_DARK = "#5E3E1C"
SOAP_DRY = "#B8A070"
ENAMEL = "#E3DCC6"
ENAMEL_INSIDE = "#D2C8AC"
ENAMEL_BLUE = "#3E5A7A"
ENAMEL_CHIP = "#2A2724"
TEA = "#7A5A36"
CHERRY = "#A8302A"
LEAF = "#4E6A36"
WOOL = "#7A382E"
WOOL_DARK = "#6A2A22"
WOOL_WHITE = "#D8D0BC"
WOOL_GREY = "#6E6A62"
CLOTH_DARK = "#3C3D40"
SEAM = "#2A2826"
FUR = "#6E5C48"
FUR_TIP = "#8E7A62"
WOOD_DARK = "#5C3A24"
GILT = "#9A7A40"
MOUNT = "#D8CDB0"
SEPIA = "#A8906A"
SEPIA_DARK = "#5E4A34"
CRACK = "#E8E6DA"
BACKING = "#6A5A44"
WAX = "#7A2A22"
WAX_DARK = "#5A1C18"
LABEL = "#DCD2B4"
STAMP_BLUE = "#3A5A8A"
STAMP_RED = "#9A3A30"
STAMP_PAPER = "#E6E0CC"


def _turn(faces: list, pivot: Vector, degrees: float, axis: str | Vector) -> None:
    """Gira unas caras recién hechas alrededor de ``pivot``."""
    rotation = Matrix.Rotation(math.radians(degrees), 3, axis)
    for vert in dict.fromkeys(v for f in faces for v in f.verts):
        vert.co = pivot + rotation @ (vert.co - pivot)


def _can_profile(radius: float, height: float, rings: int) -> list[tuple[float, float]]:
    """Perfil de una lata engatillada: la tapa de abajo, hundida; el cuerpo, con
    ``rings`` anillos para que recoja las abolladuras; y la tapa de arriba, con los
    aros de dilatación."""
    r, h = radius, height
    points = [(0.0, 0.0025), (r - 0.005, 0.0025), (r - 0.0035, 0.0012), (r - 0.0005, 0.0), (r + 0.0017, 0.0007), (r + 0.002, 0.0038), (r, 0.0062)]
    for k in range(1, rings):
        points.append((r, 0.0062 + (h - 0.0124) * k / rings))
    points += [(r, h - 0.0062), (r + 0.002, h - 0.0038), (r + 0.0017, h - 0.0007), (r - 0.0005, h), (r - 0.0035, h - 0.0012), (r - 0.005, h - 0.0025)]
    points += [(r * 0.72, h - 0.0025), (r * 0.67, h - 0.0013), (r * 0.62, h - 0.0025), (r * 0.42, h - 0.0025), (r * 0.38, h - 0.0016), (r * 0.34, h - 0.0025), (0.0, h - 0.0025)]
    return points


# --------------------------------------------------------------------------
# De comer
# --------------------------------------------------------------------------


def build_condensed_milk() -> bpy.types.Object:
    """Leche condensada: la lata de la etiqueta azul y crema con las ondas, despegada
    a jirones por un costado. Abollada y con óxido en los cantos."""
    root = tb.empty("leche_condensada-fisico")
    r, h = 0.037, 0.082
    tin_mb = tb.MeshBuilder(seed=601)
    tin_mb.lathe(_can_profile(r, h, 12), (0.0, 0.0, 0.0), TIN, segments=28, sharp_angle=50.0)
    tin = tin_mb.finish("lata", tb.material("metal", TIN), root)

    label_mb = tb.MeshBuilder(seed=602)
    start, end, torn = 125.0, 425.0, 12.0
    bb.band(label_mb, r + 0.0004, 0.0085, h - 0.0085, MILK_CREAM, start=start, end=end, segments=28, rows=10, torn=torn, seed=602)
    inner_start, inner_end = start + torn, end - torn
    bb.band(label_mb, r + 0.0007, 0.0085, 0.025, MILK_BLUE, start=inner_start, end=inner_end, segments=28, rows=2)
    bb.band(label_mb, r + 0.0007, h - 0.025, h - 0.0085, MILK_BLUE, start=inner_start, end=inner_end, segments=28, rows=2)
    # Las ondas: dos rayas azules que suben y bajan alrededor de la lata.
    for middle, phase in ((0.036, 0.0), (0.047, 1.4)):
        steps = 72
        lower, upper = [], []
        for i in range(steps + 1):
            angle = inner_start + (inner_end - inner_start) * i / steps
            z = middle + 0.0042 * math.sin(math.radians(angle) * 6.0 + phase)
            lower.append(bb.around(r + 0.0009, angle, z - 0.0016))
            upper.append(bb.around(r + 0.0009, angle, z + 0.0016))
        label_mb.sheet([lower, upper], MILK_BLUE)
    label = label_mb.finish("etiqueta", tb.material("etiqueta", MILK_CREAM), root)

    tb.stain(tin, RUST, amount=0.75, scale=55.0, coverage=0.24, seed=603)
    tb.stain(tin, RUST_DARK, amount=0.6, scale=90.0, coverage=0.1, seed=604)
    tb.stain(label, WATER_STAIN, amount=0.5, scale=40.0, coverage=0.3, seed=605, stretch_z=0.5)
    tb.stain(label, DIRT, amount=0.35, scale=70.0, coverage=0.2, seed=606)
    for obj in (tin, label):
        tb.dent(obj, bb.around(r, 205.0, 0.034), radius=0.017, depth=0.003)
        tb.dent(obj, bb.around(r, 330.0, 0.07), radius=0.01, depth=0.0015)
    tb.collision_box("lata", (2.0 * r + 0.004, 2.0 * r + 0.004, h), (0.0, 0.0, h / 2.0), root)
    tb.paint({tin: None, label: None}, samples=12, ao=0.35, ao_distance=0.04, seed=601)
    return root


def build_sprats() -> bpy.types.Object:
    """Espadines en aceite: la lata plana de hojalata dorada, con el pez en relieve
    en la tapa y la llavecita de abrirla encima. Óxido en las pestañas."""
    root = tb.empty("lata_espadines-fisico")
    w, d, h = 0.104, 0.07, 0.024
    mb = tb.MeshBuilder(seed=611)
    mb.prism(bb.rounded_rect(w, d, 0.018, steps=4), h - 0.004, (0.0, 0.0, h / 2.0), GOLD_TIN, bevel=0.0015)
    rim = bb.rounded_rect(w + 0.0045, d + 0.0045, 0.02, steps=4)
    mb.prism(rim, 0.0028, (0.0, 0.0, 0.0014), GOLD_DARK, bevel=0.0009)
    mb.prism(rim, 0.0028, (0.0, 0.0, h - 0.0014), GOLD_DARK, bevel=0.0009)
    lid_z = h - 0.002
    # Un nervio alrededor de la tapa y el pez en relieve, con su ojo y la agalla.
    for side in (-1.0, 1.0):
        mb.box((w - 0.03, 0.0026, 0.0012), (0.0, side * (d / 2.0 - 0.009), lid_z + 0.0005), GOLD_RELIEF, bevel=0.0005)
        mb.box((0.0026, d - 0.03, 0.0012), (side * (w / 2.0 - 0.009), 0.0, lid_z + 0.0005), GOLD_RELIEF, bevel=0.0005)
    fish = [
        (0.027, 0.0), (0.021, 0.0062), (0.009, 0.0088), (-0.006, 0.0078), (-0.016, 0.0042), (-0.0225, 0.009),
        (-0.0265, 0.008), (-0.021, 0.0), (-0.0265, -0.008), (-0.0225, -0.009), (-0.016, -0.0042), (-0.006, -0.0078),
        (0.009, -0.0088), (0.021, -0.0062),
    ]
    mb.prism([(x * 1.15, y * 1.15) for x, y in fish], 0.0022, (0.002, -0.004, lid_z + 0.0011), GOLD_RELIEF, bevel=0.0007)
    mb.cylinder(0.0019, 0.0008, (0.0245, -0.002, lid_z + 0.0024), INK, segments=8)
    mb.box((0.0014, 0.011, 0.0008), (0.0185, -0.004, lid_z + 0.0023), GOLD_DARK)
    for k in range(4):
        mb.box((0.0014, 0.007 - k * 0.001, 0.0008), (0.009 - k * 0.0068, -0.004, lid_z + 0.0023), GOLD_DARK)
    can = mb.finish("lata", tb.material("metal", GOLD_TIN), root)

    # La llave: una varilla con la ranura en la punta y el ojo plano para el dedo.
    key = tb.MeshBuilder(seed=612)
    top = h + 0.0016
    start, finish = Vector((-0.03, -0.014, top)), Vector((0.016, 0.012, top))
    key.bar(start, finish, 0.0016, TIN, 8)
    key.box((0.007, 0.0036, 0.0034), finish + Vector((0.0028, 0.0016, 0.0)), TIN_DARK, rotation=(0.0, 0.0, 29.0), bevel=0.0008)
    eye = start - (finish - start).normalized() * 0.006
    key.lathe([(0.0035, -0.0008), (0.0072, -0.0008), (0.0072, 0.0008), (0.0035, 0.0008), (0.0035, -0.0008)], eye, TIN, segments=14)
    key_obj = key.finish("llave", tb.material("metal", TIN), root)

    tb.stain(can, RUST, amount=0.7, scale=60.0, coverage=0.26, seed=613)
    tb.stain(can, DIRT, amount=0.4, scale=35.0, coverage=0.2, seed=614)
    tb.stain(key_obj, RUST, amount=0.8, scale=80.0, coverage=0.35, seed=615)
    tb.dent(can, (0.035, -0.02, h), radius=0.02, depth=0.0015)
    tb.collision_box("lata", (w + 0.006, d + 0.006, h + 0.004), (0.0, 0.0, (h + 0.004) / 2.0), root)
    tb.paint({can: None, key_obj: None}, samples=12, ao=0.35, ao_distance=0.03, seed=611)
    return root


def build_pickles() -> bpy.types.Object:
    """Un tarro de pepinillos en salmuera, de los que se hacían en casa y se
    guardaban en el balcón: el vidrio deja ver los pepinillos apretados contra él,
    algún ajo y la pimienta. La tapa de hojalata, engatillada y oxidada."""
    rng = random.Random(621)
    root = tb.empty("tarro_pepinillos-fisico")
    radius, brine_top = 0.048, 0.118
    glass = tb.MeshBuilder(seed=621)
    profile = [(0.0, 0.004), (0.036, 0.003), (0.044, 0.0), (0.0475, 0.004), (radius, 0.01)]
    profile += [(radius, 0.01 + k * 0.0108) for k in range(1, 10)]
    profile += [(radius, brine_top - 0.0005), (radius, brine_top + 0.0005), (0.047, 0.124), (0.0435, 0.1305), (0.0385, 0.1345), (0.0365, 0.1365), (0.0365, 0.145), (0.0, 0.145)]
    glass.lathe(profile, (0.0, 0.0, 0.0), BRINE, segments=32, sharp_angle=60.0)
    jar = glass.finish("tarro", tb.material("vidrio", BRINE), root)
    bb.recolor(jar, lambda co: GLASS_PALE if co.z > brine_top else None)

    # Lo de dentro asoma un poco por fuera del vidrio: así se ve, como en un dibujo.
    food = tb.MeshBuilder(seed=622)
    for k in range(9):
        angle = k * 40.0 + rng.uniform(-10.0, 10.0)
        length = rng.uniform(0.058, 0.08)
        size = rng.uniform(0.0105, 0.0128)
        z = rng.uniform(0.012 + length / 2.0, brine_top - 0.006 - length / 2.0)
        center = bb.around(radius - size + 0.0017, angle, z)
        faces = food.sphere(size, center, PICKLE if k % 3 else PICKLE_DARK, segments=12, scale=(1.0, 1.0, length / (2.0 * size)), jitter=0.06)
        _turn(faces, center, rng.uniform(-14.0, 14.0), Vector((center.x, center.y, 0.0)).normalized())
    for k in range(3):
        center = bb.around(radius - 0.006 + 0.0012, 20.0 + k * 115.0 + rng.uniform(-10.0, 10.0), rng.uniform(0.09, 0.108))
        food.sphere(0.006, center, GARLIC, segments=8, scale=(1.0, 1.0, 1.5))
    for k in range(10):
        center = bb.around(radius - 0.0025 + 0.0011, rng.uniform(0.0, 360.0), rng.uniform(0.012, 0.112))
        food.sphere(0.0025, center, PEPPER, segments=6)
    contents = food.finish("pepinillos", tb.material("conserva", PICKLE), root)

    lid = tb.MeshBuilder(seed=623)
    lid.lathe([(0.0365, 0.1362), (0.0395, 0.1368), (0.0408, 0.1392), (0.0408, 0.1478), (0.0392, 0.1508), (0.035, 0.152), (0.026, 0.1514), (0.024, 0.1522), (0.0, 0.1522)], (0.0, 0.0, 0.0), LID_TIN, segments=32, sharp_angle=45.0)
    lid_obj = lid.finish("tapa", tb.material("metal", LID_TIN), root)
    tb.stain(lid_obj, RUST, amount=0.8, scale=70.0, coverage=0.35, seed=624)
    tb.stain(jar, DIRT, amount=0.35, scale=30.0, coverage=0.3, seed=625)
    tb.collision_box("tarro", (0.1, 0.1, 0.152), (0.0, 0.0, 0.076), root)
    tb.paint({jar: None, contents: None, lid_obj: None}, samples=12, ao=0.3, ao_distance=0.05, seed=621)
    return root


def build_sugar() -> bpy.types.Object:
    """Azúcar en terrones: la caja de cartón abierta por arriba, con las solapas
    dobladas, la última capa de terrones y tres terrones caídos al lado."""
    rng = random.Random(631)
    root = tb.empty("azucar-fisico")
    w, d, h, t = 0.11, 0.058, 0.072, 0.0022
    box = tb.MeshBuilder(seed=631)
    box.box((w, d, t), (0.0, 0.0, t / 2.0), BOX_WHITE, bevel=0.0008)
    for side in (-1.0, 1.0):
        box.box((w, t, h), (0.0, side * (d / 2.0 - t / 2.0), h / 2.0), BOX_WHITE, bevel=0.0008, cuts=3)
        box.box((t, d - 2.0 * t, h), (side * (w / 2.0 - t / 2.0), 0.0, h / 2.0), BOX_WHITE, bevel=0.0008, cuts=2)
    # Lo impreso: una banda azul alrededor, una raya roja y el rótulo (rayas de tinta).
    lift = 0.0005
    for side in (-1.0, 1.0):
        box.box((w + 0.0002, lift, 0.016), (0.0, side * (d / 2.0 + lift / 2.0), 0.024), BOX_BLUE)
        box.box((w + 0.0002, lift, 0.004), (0.0, side * (d / 2.0 + lift / 2.0), 0.038), BOX_RED)
        box.box((lift, d + 0.0002, 0.016), (side * (w / 2.0 + lift / 2.0), 0.0, 0.024), BOX_BLUE)
        for k in range(3):
            box.box((0.05 - k * 0.012, lift, 0.0022), (-0.012, side * (d / 2.0 + lift), 0.05 + k * 0.006), INK)
    # Las solapas: la de delante cae por fuera, la de atrás queda de pie y una lateral, abierta.
    flap = 0.028
    for side, angle in ((-1.0, 112.0), (1.0, 22.0)):
        hinge = Vector((0.0, side * (d / 2.0 - t / 2.0), h))
        direction = Vector((0.0, side * math.sin(math.radians(angle)), math.cos(math.radians(angle))))
        box.box((w - 0.002, t, flap), hinge + direction * (flap / 2.0), BOX_WHITE, rotation=(-side * angle, 0.0, 0.0), bevel=0.0006)
    hinge = Vector((w / 2.0 - t / 2.0, 0.0, h))
    direction = Vector((math.sin(math.radians(65.0)), 0.0, math.cos(math.radians(65.0))))
    box.box((t, d - 0.006, 0.024), hinge + direction * 0.012, BOX_WHITE, rotation=(0.0, 65.0, 0.0), bevel=0.0006)
    carton = box.finish("caja", tb.material("carton", BOX_WHITE), root)
    tb.apply_bulge(carton, (0.0, 0.0, h / 2.0), (w / 2.0, d / 2.0, h / 2.0), 0.0015)
    tb.stain(carton, WATER_STAIN, amount=0.75, scale=30.0, coverage=0.38, seed=632, stretch_z=0.4)
    tb.stain(carton, DIRT, amount=0.5, scale=55.0, coverage=0.25, seed=633)
    tb.dent(carton, (-w / 2.0, -d / 2.0, 0.012), radius=0.02, depth=0.002)

    cubes = tb.MeshBuilder(seed=634)
    size = 0.0158
    pitch_x, pitch_y = (w - 2.0 * t) / 6.0, (d - 2.0 * t) / 3.0
    for i in range(6):
        for j in range(3):
            if (i, j) in ((5, 0), (5, 1), (4, 0)):
                z = h - 0.03
            else:
                z = h - 0.012
            center = (-w / 2.0 + t + pitch_x * (i + 0.5), -d / 2.0 + t + pitch_y * (j + 0.5), z)
            cubes.box((size, size, size), center, SUGAR, rotation=(0.0, 0.0, rng.uniform(-4.0, 4.0)), bevel=0.0012, jitter=0.03)
    cubes.box((w - 2.0 * t - 0.002, d - 2.0 * t - 0.002, h - 0.04), (0.0, 0.0, (h - 0.04) / 2.0 + t), SUGAR_SHADE)
    for k, (x, y, turn) in enumerate(((0.075, -0.03, 20.0), (0.088, -0.006, -35.0), (0.071, 0.012, 50.0))):
        tilt = 25.0 if k == 1 else 0.0
        cubes.box((size, size, size), (x, y, size / 2.0 + (0.003 if tilt else 0.0)), SUGAR, rotation=(tilt, 0.0, turn), bevel=0.0012, jitter=0.03)
    sugar = cubes.finish("terrones", tb.material("azucar", SUGAR), root)
    tb.stain(sugar, "#C8BC98", amount=0.35, scale=90.0, coverage=0.25, seed=635)
    tb.collision_box("caja", (w, d, h), (0.0, 0.0, h / 2.0), root)
    tb.paint({carton: None, sugar: None}, samples=12, ao=0.4, ao_distance=0.04, seed=631)
    return root


# --------------------------------------------------------------------------
# De la casa
# --------------------------------------------------------------------------


def build_candles() -> bpy.types.Object:
    """Un paquete de velas de casa: cuatro velas de parafina atadas con su faja de
    papel y un cordel. La de arriba ya se encendió alguna noche sin luz."""
    root = tb.empty("velas-fisico")
    radius, length = 0.0095, 0.2
    mb = tb.MeshBuilder(seed=641)
    spots = [(-radius * 2.0, radius), (0.0, radius), (radius * 2.0, radius)]
    for y, z in spots:
        mb.cylinder(radius, length, (0.0, y, z), CANDLE, rotation=(0.0, 90.0, 0.0), segments=12, jitter=0.03)
        for end in (-1.0, 1.0):
            mb.bar((end * length / 2.0, y, z), (end * (length / 2.0 + 0.007), y + 0.001, z + 0.001), 0.0009, WICK, 6)
    # La de arriba, más corta: el cabo quemado, con el cráter, el pabilo negro y los goterones.
    top_y, top_z = -radius, radius + radius * math.sqrt(3.0)
    burnt = 0.135
    left = -length / 2.0
    mb.cylinder(radius, burnt, (left + burnt / 2.0, top_y, top_z), CANDLE, rotation=(0.0, 90.0, 0.0), segments=12, jitter=0.03)
    tip = left + burnt
    mb.lathe([(radius, 0.0), (radius * 0.98, 0.003), (radius * 0.7, 0.0045), (radius * 0.35, 0.0015), (0.0, 0.001)], (tip, top_y, top_z), "#D8CDB0", rotation=(0.0, 90.0, 0.0), segments=12)
    mb.bar((tip + 0.0012, top_y, top_z), (tip + 0.0085, top_y + 0.0012, top_z + 0.0028), 0.001, WICK, 6)
    for k, (dx, angle) in enumerate(((-0.004, 200.0), (-0.012, 240.0), (-0.02, 170.0))):
        a = math.radians(angle)
        mb.sphere(0.0022 - k * 0.0003, (tip + dx, top_y + radius * math.cos(a) * 0.95, top_z + radius * math.sin(a) * 0.95), "#DCD2BA", segments=6, scale=(1.6, 1.0, 1.0))
    mb.bar((left, top_y, top_z), (left - 0.007, top_y, top_z + 0.001), 0.0009, WICK, 6)
    candles = mb.finish("velas", tb.material("cera", CANDLE), root)

    wrap = tb.MeshBuilder(seed=642)
    middle = Vector((0.0, -radius * 0.5, radius * 1.6))
    hull = [(-0.031, 0.0), (0.031, 0.0), (0.033, 0.013), (0.009, top_z + radius + 0.0012), (-0.024, top_z + radius + 0.0012), (-0.034, 0.013)]
    path = [Vector((0.0, y, max(z, 0.0004))) for y, z in hull]
    path.append(path[0])
    path = tb.smooth_path(path, 3)
    bb.strap(wrap, path, 0.06, 0.0012, KRAFT_LIGHT, center=middle)
    for x in (-0.004, 0.004):
        string = [Vector((x, p.y, p.z)) + (Vector((0.0, p.y, p.z)) - middle).normalized() * 0.0012 for p in path]
        wrap.tube(string, 0.0011, STRING, segments=5, caps=False)
    wrap.sphere(0.003, (0.0, -0.01, top_z + radius + 0.004), STRING, segments=8)
    for k in range(2):
        wrap.box((0.024 - k * 0.006, 0.0008, 0.0016), (0.003 - k * 0.004, -0.0352, 0.008 + k * 0.0042), INK)
    paper = wrap.finish("faja", tb.material("papel_viejo", KRAFT_LIGHT), root)

    tb.stain(candles, "#B8AE92", amount=0.5, scale=40.0, coverage=0.3, seed=643)
    tb.stain(candles, DIRT, amount=0.3, scale=70.0, coverage=0.15, seed=644)
    tb.stain(paper, WATER_STAIN, amount=0.6, scale=45.0, coverage=0.35, seed=645)
    tb.collision_box("velas", (length + 0.016, 0.06, 0.042), (0.0, 0.0, 0.021), root)
    tb.paint({candles: None, paper: None}, samples=10, ao=0.4, ao_distance=0.03, seed=641)
    return root


def build_soap() -> bpy.types.Object:
    """Jabón de lavar: la pastilla parda con el sello hundido y media envoltura de
    papel de estraza, rasgada. Tiene una esquina mordida y polvo blanco seco."""
    root = tb.empty("jabon-fisico")
    w, d, h = 0.092, 0.056, 0.03
    mb = tb.MeshBuilder(seed=651)
    mb.box((w, d, h), (0.0, 0.0, h / 2.0), SOAP, bevel=0.006, segments=2, cuts=4)
    # El sello: un marco en relieve y tres bloques de "letras".
    top = h + 0.0005
    for side in (-1.0, 1.0):
        mb.box((0.058, 0.0024, 0.0012), (0.004, side * 0.016, top), SOAP_DARK, bevel=0.0005)
        mb.box((0.0024, 0.034, 0.0012), (0.004 + side * 0.028, 0.0, top), SOAP_DARK, bevel=0.0005)
    for k in range(3):
        mb.box((0.012, 0.014, 0.001), (-0.012 + k * 0.016, 0.0, top), SOAP_DARK, bevel=0.0004)
    soap = mb.finish("jabon", tb.material("jabon", SOAP), root)
    tb.dent(soap, (w / 2.0, -d / 2.0, h), radius=0.016, depth=0.006)
    tb.stain(soap, SOAP_DRY, amount=0.55, scale=50.0, coverage=0.25, seed=652)

    wrap = tb.MeshBuilder(seed=653)
    rng = random.Random(653)
    sleeve = 0.04
    x0, x1 = -w / 2.0 - 0.0015, -w / 2.0 + sleeve
    grid = []
    for j in range(9):
        # Alrededor de la pastilla (en el plano YZ), de abajo arriba por delante y de vuelta por detrás.
        t = j / 8.0
        angle = math.pi * 2.0 * t
        y = (d / 2.0 + 0.0012) * max(-1.0, min(1.0, 1.4 * math.cos(angle - math.pi / 2.0)))
        z = h / 2.0 + (h / 2.0 + 0.0012) * max(-1.0, min(1.0, 1.4 * math.sin(angle - math.pi / 2.0)))
        tear = rng.uniform(-0.008, 0.004)
        grid.append([Vector((x0, y, z)), Vector((x1 + tear, y, z))])
    wrap.sheet([[row[0] for row in grid], [row[1] for row in grid]], "#B9A47E")
    wrap.box((0.0012, d + 0.003, h + 0.003), (x0 - 0.0002, 0.0, h / 2.0), "#B9A47E", bevel=0.0006)
    paper = wrap.finish("papel", tb.material("papel_viejo", "#B9A47E"), root)
    bb.crumple(paper, 0.0008, 654)
    tb.stain(paper, "#6A4A2A", amount=0.5, scale=50.0, coverage=0.3, seed=655)
    tb.collision_box("jabon", (w + 0.003, d + 0.003, h + 0.002), (0.0, 0.0, h / 2.0), root)
    tb.paint({soap: None, paper: None}, samples=10, ao=0.35, ao_distance=0.03, seed=651)
    return root


def build_mug() -> bpy.types.Object:
    """Taza de chapa esmaltada: blanca con el borde azul y dos cerezas pintadas.
    Desconchada (asoma el hierro negro) y con el cerco del té por dentro."""
    rng = random.Random(661)
    root = tb.empty("taza_esmaltada-fisico")
    outer, inner, h = 0.0395, 0.0372, 0.086
    mb = tb.MeshBuilder(seed=661)
    rim = [(outer + 0.0006, h - 0.0008), (outer - 0.001, h), (inner + 0.0003, h - 0.0005)]
    profile = [(0.0, 0.0), (outer - 0.004, 0.0), (outer - 0.0008, 0.0016), (outer - 0.0004, 0.004)]
    profile += [(outer, 0.004 + (h - 0.012) * k / 8.0) for k in range(1, 9)]
    profile += [(outer, h - 0.0062), (outer, h - 0.0056)]
    mb.lathe([*profile, *rim[:2]], (0.0, 0.0, 0.0), ENAMEL, segments=28, sharp_angle=60.0)
    inside = [rim[1], rim[2], (inner, h - 0.004), (inner, 0.068), (inner, 0.0595), (inner, 0.058), (inner, 0.0545), (inner, 0.052), (inner, 0.0505)]
    inside += [(inner, 0.0505 - 0.0425 * k / 4.0) for k in range(1, 5)]
    inside += [(inner - 0.003, 0.0045), (0.0, 0.0045)]
    mb.lathe(inside, (0.0, 0.0, 0.0), ENAMEL_INSIDE, segments=28, sharp_angle=60.0)
    loop = tb.smooth_path(((outer - 0.001, 0.0, 0.07), (0.052, 0.0, 0.073), (0.06, 0.0, 0.062), (0.0605, 0.0, 0.036), (0.053, 0.0, 0.022), (outer - 0.001, 0.0, 0.02)), 5)
    bb.strap(mb, loop, 0.012, 0.003, ENAMEL, center=(0.049, 0.0, 0.046))
    # Las cerezas del frente, con sus rabitos y una hoja.
    for angle, z in ((-9.0, 0.046), (5.0, 0.043)):
        bb.disc(mb, bb.around(outer, angle, z), bb.around(1.0, angle, 0.0), 0.0052, CHERRY, thickness=0.0007, segments=12)
    for angle, z in ((-9.0, 0.046), (5.0, 0.043)):
        mb.box((0.0009, 0.0006, 0.013), bb.around(outer + 0.0008, angle * 0.5, z + 0.009), LEAF, rotation=(0.0, -angle * 1.5, -angle * 0.5))
    bb.disc(mb, bb.around(outer, 7.0, 0.062), bb.around(1.0, 7.0, 0.0), 0.0045, LEAF, thickness=0.0007, segments=10, squash=0.45)
    # Desconchones: en el borde, abajo y en el asa.
    for k in range(9):
        angle = rng.uniform(0.0, 360.0)
        z = rng.choice((rng.uniform(0.006, 0.02), rng.uniform(0.07, 0.082), rng.uniform(0.03, 0.06)))
        bb.disc(mb, bb.around(outer, angle, z), bb.around(1.0, angle, 0.0), rng.uniform(0.0015, 0.004), ENAMEL_CHIP, thickness=0.0006, segments=7, squash=rng.uniform(0.5, 1.0))
    mug = mb.finish("taza", tb.material("metal", ENAMEL), root)

    def colors(co: Vector) -> str | None:
        radial = math.hypot(co.x, co.y)
        if co.z > h - 0.0058 or co.z < 0.0018:
            return ENAMEL_BLUE
        if radial < inner + 0.0005 and 0.0515 < co.z < 0.0585:
            return TEA
        return None

    bb.recolor(mug, colors)
    tb.stain(mug, "#8A7A5A", amount=0.4, scale=45.0, coverage=0.25, seed=662)
    tb.collision_box("taza", (0.104, 0.082, h), (0.01, 0.0, h / 2.0), root)
    tb.paint({mug: None}, samples=14, ao=0.4, ao_distance=0.04, seed=661)
    return root


# --------------------------------------------------------------------------
# De abrigo
# --------------------------------------------------------------------------


def _ellipsoid_band(
    mb: tb.MeshBuilder,
    center: Vector,
    radii: tuple[float, float, float],
    v0: float,
    v1: float,
    color: str,
    turn: float,
    lift: float = 0.0012,
) -> None:
    """Franja de punto alrededor de un elipsoide tumbado a lo largo de su Y local, de
    ``v0`` a ``v1`` (en fracciones del semieje Y), girado ``turn`` grados en Z."""
    a, b, c = radii
    rotation = Matrix.Rotation(math.radians(turn), 3, "Z")
    rows = []
    for j in range(4):
        v = v0 + (v1 - v0) * j / 3.0
        ring = math.sqrt(max(0.0, 1.0 - v * v))
        row = []
        for i in range(25):
            theta = -2.0 * math.pi * i / 24.0
            local = Vector(((a * ring + lift) * math.cos(theta), b * v, (c * ring + lift) * math.sin(theta)))
            row.append(center + rotation @ local)
        rows.append(row)
    mb.sheet(rows, color)


def build_mittens() -> bpy.types.Object:
    """Manoplas de lana: un par de punto, granate con una franja blanca y el puño
    gris de canalé, unidas por un cordón para no perderlas. Con bolitas y barro."""
    root = tb.empty("manoplas-fisico")
    mb = tb.MeshBuilder(seed=671)
    radii = (0.05, 0.085, 0.016)
    for side, turn in ((-1.0, 10.0), (1.0, -8.0)):
        rotation = Matrix.Rotation(math.radians(turn), 3, "Z")
        hand = Vector((side * 0.062, 0.0, radii[2]))
        _turn(mb.sphere(1.0, hand, WOOL, segments=20, scale=radii, jitter=0.03), hand, turn, "Z")
        # El pulgar, por el lado de dentro, apuntando hacia delante.
        thumb = hand + rotation @ Vector((-side * 0.045, -0.02, 0.0))
        faces = mb.sphere(1.0, thumb, WOOL, segments=12, scale=(0.017, 0.034, 0.012))
        _turn(faces, thumb, turn + side * 32.0, "Z")
        _ellipsoid_band(mb, hand, radii, 0.08, 0.32, WOOL_WHITE, turn)
        _ellipsoid_band(mb, hand, radii, 0.4, 0.46, WOOL_WHITE, turn)
        # El puño: un tubo aplastado de canalé, más gris.
        cuff = hand + rotation @ Vector((0.0, -0.105, -0.002))
        mb.box((0.078, 0.05, 0.026), cuff, WOOL_GREY, rotation=(0.0, 0.0, turn), bevel=0.011, segments=2)
        for k in range(9):
            rib = cuff + rotation @ Vector((-0.032 + k * 0.008, 0.0, 0.0))
            mb.box((0.0032, 0.05, 0.0275), rib, "#5E5A52", rotation=(0.0, 0.0, turn), bevel=0.0014)
    # El cordón, de un puño al otro, haciendo una curva por delante.
    cord = tb.smooth_path(((-0.07, -0.13, 0.008), (-0.05, -0.165, 0.004), (0.0, -0.18, 0.0035), (0.05, -0.162, 0.004), (0.068, -0.128, 0.008)), 6)
    mb.tube(cord, 0.0024, WOOL_WHITE, segments=6)
    mittens = mb.finish("manoplas", tb.material("tela", WOOL), root)
    tb.wobble(mittens, amount=0.0016, scale=40.0, seed=672)
    tb.stain(mittens, WOOL_DARK, amount=0.5, scale=60.0, coverage=0.3, seed=673)
    tb.stain(mittens, DIRT, amount=0.55, scale=25.0, coverage=0.3, seed=674)
    tb.collision_box("manoplas", (0.22, 0.27, 0.035), (0.0, -0.04, 0.0175), root)
    tb.paint({mittens: None}, samples=12, ao=0.45, ao_distance=0.04, seed=671)
    return root


def _ring(
    mb: tb.MeshBuilder,
    rx: float,
    ry: float,
    z0: float,
    top,
    thickness: float,
    color: str,
    segments: int = 36,
    rows: int = 4,
) -> None:
    """Rodete cerrado alrededor de un óvalo (``rx`` × ``ry``): por fuera, por arriba,
    por dentro y por abajo. ``top(ángulo)`` da la altura de su borde de arriba."""

    def point(angle: float, z: float, out: float) -> Vector:
        a = math.radians(angle)
        return Vector(((rx + out) * math.sin(a), -(ry + out) * math.cos(a), z))

    angles = [360.0 * i / segments for i in range(segments + 1)]
    heights = [[z0 + (top(angle) - z0) * j / rows for angle in angles] for j in range(rows + 1)]
    outer = [[point(angle, heights[j][i], thickness) for i, angle in enumerate(angles)] for j in range(rows + 1)]
    inner = [[point(angle, heights[j][i], 0.0) for i, angle in enumerate(angles)] for j in range(rows, -1, -1)]
    mb.sheet(outer, color)
    mb.sheet([outer[-1], inner[0]], color)
    mb.sheet(inner, color)
    mb.sheet([inner[-1], outer[0]], color)


def build_ushanka() -> bpy.types.Object:
    """Gorro de orejeras: la copa de paño oscuro, con sus costuras y el botón, sobre
    un rodete de piel de conejo; delante, la visera vuelta hacia arriba, y a los
    lados las orejeras, subidas y atadas arriba con sus cintas. La piel, apelmazada."""
    root = tb.empty("gorro_orejeras-fisico")
    rx, ry = 0.088, 0.1
    crown_top = 0.165
    crown = tb.MeshBuilder(seed=681)
    profile = [(rx, 0.035), (rx + 0.003, 0.07), (rx * 0.97, 0.1), (rx * 0.86, 0.128), (rx * 0.66, 0.149), (rx * 0.38, 0.161), (0.0, crown_top)]
    faces = crown.lathe(profile, (0.0, 0.0, 0.0), CLOTH_DARK, segments=32)
    for vert in dict.fromkeys(v for f in faces for v in f.verts):
        vert.co.y *= ry / rx
    # Cuatro costuras de la copa al botón.
    for k in range(4):
        angle = math.radians(45.0 + k * 90.0)
        seam = [
            Vector(((radius + 0.0003) * math.sin(angle), -(radius + 0.0003) * math.cos(angle) * ry / rx, z + 0.0001))
            for radius, z in profile[1:]
        ]
        crown.tube(tb.smooth_path(seam, 3), 0.0009, "#36332E", segments=5)
    crown.sphere(0.0066, (0.0, 0.0, crown_top + 0.001), SEAM, segments=10, scale=(1.0, 1.0, 0.6))
    cap = crown.finish("copa", tb.material("tela", CLOTH_DARK), root)
    tb.stain(cap, "#5E5A52", amount=0.5, scale=30.0, coverage=0.3, seed=682)
    tb.stain(cap, DIRT, amount=0.4, scale=45.0, coverage=0.2, seed=688)

    fur = tb.MeshBuilder(seed=683)

    def top(angle: float) -> float:
        # Delante, la visera vuelta hacia arriba; a los lados, las orejeras subidas.
        side = abs(math.sin(math.radians(angle)))
        front = max(0.0, math.cos(math.radians(angle)))
        # Canto de mechones: sube y baja de un vértice al siguiente, como pelo.
        lumps = 0.0045 * (round(angle / 3.75) % 2) + 0.003 * math.sin(math.radians(angle) * 7.0)
        return 0.052 + 0.016 * front ** 2 + 0.05 * side ** 6 + lumps

    thickness = 0.024
    _ring(fur, rx - 0.003, ry - 0.003, 0.0, top, thickness, FUR, segments=96, rows=5)
    fur_obj = fur.finish("piel", tb.material("piel_conejo", FUR), root)
    tb.wobble(fur_obj, amount=0.0045, scale=38.0, seed=684)
    tb.wobble(fur_obj, amount=0.0015, scale=140.0, seed=689)
    tb.stain(fur_obj, FUR_TIP, amount=0.6, scale=80.0, coverage=0.4, seed=685)
    tb.stain(fur_obj, "#3E3226", amount=0.5, scale=35.0, coverage=0.28, seed=686)

    ties = tb.MeshBuilder(seed=687)
    knot = Vector((0.0, -0.004, crown_top + 0.004))
    for side in (-1.0, 1.0):
        ties.tube(tb.smooth_path(((side * (rx + 0.008), 0.0, top(90.0) - 0.006), (side * (rx - 0.004), -0.002, 0.13), (side * 0.05, -0.004, 0.158), (side * 0.008, -0.004, crown_top + 0.004)), 5), 0.0014, SEAM, segments=5)
        ties.tube(tb.smooth_path(((side * 0.004, -0.004, crown_top + 0.005), (side * 0.014, -0.028, crown_top + 0.004), (side * 0.024, -0.05, crown_top - 0.004)), 4), 0.0013, SEAM, segments=5)
    ties.sphere(0.0052, knot, SEAM, segments=8)
    ties_obj = ties.finish("cintas", tb.material("tela", SEAM), root)
    tb.collision_box("gorro", (2.0 * rx + 0.06, 2.0 * ry + 0.06, crown_top + 0.01), (0.0, 0.0, (crown_top + 0.01) / 2.0), root)
    tb.paint({cap: None, fur_obj: None, ties_obj: None}, samples=14, ao=0.45, ao_distance=0.06, seed=681)
    return root


# --------------------------------------------------------------------------
# Personales
# --------------------------------------------------------------------------


def build_photo_frame() -> bpy.types.Object:
    """Foto enmarcada: un marco de madera con el filo dorado, de pie sobre su
    patilla. Dentro, una pareja en sepia, desvaída; el cristal, roto en estrella."""
    rng = random.Random(691)
    root = tb.empty("marco_foto-fisico")
    w, h, depth = 0.14, 0.19, 0.016
    tilt = -11.0
    mb = tb.MeshBuilder(seed=691)
    front = -depth / 2.0
    mb.slab((-w / 2.0, w / 2.0), (0.0, h), (front, depth / 2.0), WOOD_DARK, holes=[(-0.052, 0.02, 0.052, 0.17)], bevel=0.003)
    mb.slab((-0.055, 0.055), (0.016, 0.174), (front + 0.0028, 0.004), GILT, holes=[(-0.049, 0.023, 0.049, 0.167)], bevel=0.0012)
    mb.box((0.1, 0.002, 0.152), (0.0, 0.0012, 0.095), MOUNT)
    mb.box((0.072, 0.0012, 0.098), (0.0, -0.0004, 0.1), SEPIA)
    # La pareja: dos cabezas y dos pares de hombros, en sepia oscura.
    for x, head_z, scale in ((-0.015, 0.124, 1.0), (0.016, 0.119, 0.92)):
        bb.disc(mb, (x, -0.0012, head_z), (0.0, -1.0, 0.0), 0.0085 * scale, SEPIA_DARK, thickness=0.0005, segments=12, squash=0.85)
        mb.prism(bb.ellipse(0.034 * scale, 0.04 * scale, 14), 0.0005, (x, -0.0013, head_z - 0.029 * scale), SEPIA_DARK, rotation=(90.0, 0.0, 0.0))
    mb.box((0.072, 0.0012, 0.03), (0.0, -0.0011, 0.065), "#8E7856")
    # El cristal roto: rayas claras que salen de un golpe en una esquina.
    hit = Vector((0.026, -0.0024, 0.142))
    for k in range(9):
        angle = math.radians(k * 40.0 + rng.uniform(-12.0, 12.0))
        length = rng.uniform(0.025, 0.07)
        direction = Vector((math.cos(angle), 0.0, math.sin(angle)))
        end = hit + direction * length
        end.x = max(-0.048, min(0.048, end.x))
        end.z = max(0.024, min(0.166, end.z))
        mid = (hit + end) / 2.0
        span = (end - hit).length
        mb.box((span, 0.0004, 0.0007), mid, CRACK, rotation=(0.0, -math.degrees(math.atan2(end.z - hit.z, end.x - hit.x)), 0.0))
    mb.box((0.124, 0.003, 0.174), (0.0, depth / 2.0 + 0.0015, 0.095), BACKING)
    for vert in mb.bm.verts:
        vert.co = Vector((0.0, front, 0.0)) + Matrix.Rotation(math.radians(tilt), 3, "X") @ (vert.co - Vector((0.0, front, 0.0)))
    # La patilla de detrás, hasta la mesa.
    hinge = Vector((0.0, front, 0.0)) + Matrix.Rotation(math.radians(tilt), 3, "X") @ Vector((0.0, depth / 2.0 + 0.003, 0.11))
    foot = Vector((0.0, hinge.y + 0.075, 0.002))
    span = foot - hinge
    mb.box((0.026, 0.003, span.length), (hinge + foot) / 2.0, BACKING, rotation=(math.degrees(math.atan2(span.y, -span.z)), 0.0, 0.0), bevel=0.001)
    frame = mb.finish("marco", tb.material("madera", WOOD_DARK), root)
    tb.stain(frame, "#8A6A48", amount=0.4, scale=60.0, coverage=0.25, seed=692)
    tb.stain(frame, DIRT, amount=0.35, scale=30.0, coverage=0.2, seed=693)
    tb.collision_box("marco", (w, 0.11, h), (0.0, 0.04, h / 2.0), root)
    tb.paint({frame: None}, samples=12, ao=0.4, ao_distance=0.04, seed=691)
    return root


def build_parcel() -> bpy.types.Object:
    """Paquete de correos: una caja envuelta en papel de estraza, atada en cruz con
    cordel y lacrada; la etiqueta con la dirección, los sellos y el matasellos. Nunca
    llegó a su destino."""
    rng = random.Random(701)
    root = tb.empty("paquete_correos-fisico")
    w, d, h = 0.26, 0.17, 0.1
    center = Vector((0.0, 0.0, h / 2.0))
    half = Vector((w / 2.0, d / 2.0, h / 2.0))
    body = tb.MeshBuilder(seed=701)
    body.box((w, d, h), center, KRAFT, bevel=0.006, segments=2, cuts=5)
    # Los pliegues del papel en los extremos.
    for side in (-1.0, 1.0):
        x = side * (w / 2.0 + 0.0006)
        body.prism([(-d / 2.0 + 0.004, h - 0.004), (d / 2.0 - 0.004, h - 0.004), (0.0, h * 0.42)], 0.0012, (x, 0.0, 0.0), KRAFT_LIGHT, rotation=(90.0, 0.0, 90.0 * side))
    paper = body.finish("papel", tb.material("papel_viejo", KRAFT), root)
    tb.apply_bulge(paper, center, half, 0.003)
    tb.stain(paper, WATER_STAIN, amount=0.6, scale=14.0, coverage=0.35, seed=702)
    tb.stain(paper, "#6E5236", amount=0.5, scale=40.0, coverage=0.2, seed=703)
    bb.crumple(paper, 0.0007, 704)

    marks = tb.MeshBuilder(seed=705)
    top = h + 0.0012
    # La etiqueta de la dirección, a la izquierda, con cuatro renglones a pluma.
    marks.box((0.11, 0.062, 0.0008), (-0.055, 0.01, top), LABEL, rotation=(0.0, 0.0, 2.0))
    for k in range(4):
        marks.box((0.08 - (k % 2) * 0.02, 0.0016, 0.0005), (-0.06 + (k % 2) * 0.008, -0.01 + k * 0.012, top + 0.0006), INK, rotation=(0.0, 0.0, 2.0 + rng.uniform(-1.5, 1.5)))
    # Los sellos y el matasellos, arriba a la derecha.
    for k, color in enumerate((STAMP_BLUE, STAMP_RED)):
        spot = Vector((0.085 + k * 0.03, 0.045, top))
        marks.box((0.024, 0.028, 0.0008), spot, STAMP_PAPER, rotation=(0.0, 0.0, rng.uniform(-3.0, 3.0)))
        marks.box((0.018, 0.021, 0.0006), spot + Vector((0.0, 0.0, 0.0006)), color, rotation=(0.0, 0.0, rng.uniform(-3.0, 3.0)))
    marks.lathe([(0.012, 0.0), (0.0138, 0.0), (0.0138, 0.0006), (0.012, 0.0006), (0.012, 0.0)], (0.1, 0.038, top + 0.0012), INK, segments=20)
    for k in range(3):
        marks.box((0.03, 0.0012, 0.0005), (0.12, 0.03 + k * 0.006, top + 0.0013), INK)
    labels = marks.finish("etiqueta", tb.material("etiqueta", LABEL), root)

    tie = tb.MeshBuilder(seed=706)
    knot = Vector((0.03, -0.01, h + 0.002))

    def loop(axis: str, offset: float) -> list[Vector]:
        lift = 0.0018
        if axis == "x":
            corners = [(-w / 2.0 - lift, h + lift), (w / 2.0 + lift, h + lift), (w / 2.0 + lift, -lift + 0.002), (-w / 2.0 - lift, -lift + 0.002)]
            points = [Vector((x, offset, z)) for x, z in corners]
        else:
            corners = [(-d / 2.0 - lift, h + lift), (d / 2.0 + lift, h + lift), (d / 2.0 + lift, -lift + 0.002), (-d / 2.0 - lift, -lift + 0.002)]
            points = [Vector((offset, y, z)) for y, z in corners]
        points.append(points[0])
        result = []
        for a, b in zip(points, points[1:]):
            for k in range(8):
                result.append(a.lerp(b, k / 8.0))
        result.append(points[-1])
        return result

    tie.tube(loop("x", knot.y), 0.0017, STRING, segments=5, caps=False)
    tie.tube(loop("y", knot.x), 0.0017, STRING, segments=5, caps=False)
    tie.sphere(0.0042, knot + Vector((0.0, 0.0, 0.001)), STRING, segments=8)
    for direction in ((0.03, -0.012), (0.018, 0.026)):
        tie.tube(tb.smooth_path((knot, knot + Vector((direction[0] * 0.5, direction[1] * 0.5, 0.002)), knot + Vector((direction[0], direction[1], 0.0006)))), 0.0015, STRING, segments=5)
    string = tie.finish("cordel", tb.material("cuerda", STRING), root)

    seals = tb.MeshBuilder(seed=707)
    for spot, normal in (
        (knot + Vector((0.0, 0.0, 0.004)), (0.0, 0.0, 1.0)),
        (Vector((w / 2.0 + 0.002, knot.y, h * 0.5)), (1.0, 0.0, 0.0)),
        (Vector((-w / 2.0 - 0.002, knot.y, h * 0.5)), (-1.0, 0.0, 0.0)),
    ):
        bb.disc(seals, spot, normal, 0.011, WAX, thickness=0.0035, segments=11, squash=0.88)
        bb.disc(seals, Vector(spot) + Vector(normal) * 0.0035, normal, 0.0065, WAX_DARK, thickness=0.0008, segments=10)
    wax = seals.finish("lacre", tb.material("lacre", WAX), root)
    tb.stain(wax, "#3A1210", amount=0.5, scale=200.0, coverage=0.3, seed=708)
    for obj in (labels, string, wax):
        tb.apply_bulge(obj, center, half, 0.003)
    tb.collision_box("paquete", (w + 0.01, d + 0.01, h + 0.008), (0.0, 0.0, (h + 0.008) / 2.0), root)
    tb.paint({paper: None, labels: None, string: None, wax: None}, samples=12, ao=0.4, ao_distance=0.05, seed=701)
    return root


def models() -> dict:
    return {
        "leche_condensada": build_condensed_milk,
        "lata_espadines": build_sprats,
        "tarro_pepinillos": build_pickles,
        "azucar": build_sugar,
        "velas": build_candles,
        "jabon": build_soap,
        "taza_esmaltada": build_mug,
        "manoplas": build_mittens,
        "gorro_orejeras": build_ushanka,
        "marco_foto": build_photo_frame,
        "paquete_correos": build_parcel,
    }
