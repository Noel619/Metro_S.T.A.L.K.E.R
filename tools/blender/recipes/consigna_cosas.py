"""Lo que hay en la consigna: los muebles del oficio y las cosas del antiguo dueño.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Los que
se cuelgan de un muro tienen la cara buena hacia -Y y la espalda en y = 0.

Del oficio: el corcho de los encargos, la caja de los rublos (su tapa es un nodo,
"tapa", con el origen en las bisagras), el libro de cuentas (cerrado; su tapa
también se abre), la caja de las etiquetas, el cubo de basura (con su bolsa,
"bolsa"), la fregona y el cepillo (se cogen), el rollo de bolsas, el tablero de
herramientas, el flexo (con "foco" donde va la luz), el reloj de pared ("aguja_horas"
y "aguja_minutos"), la
mesa de planificar y su tablero.

Del antiguo dueño: su silla con el cojín hundido, el calendario con los días
tachados hasta la Noche de la Caída, la lista de deudas clavada a la pared, la
planta muerta, las maletas que nadie recogió de la consigna, la alfombra gastada y
el perchero con su abrigo.
"""

from __future__ import annotations

import math
import random

import bpy

import tumansk_bpy as tb

WOOD = "#8A5A3B"
WOOD_DARK = "#6E4A32"
WOOD_LIGHT = "#9A6845"
VARNISH = "#7A4A2C"
CORK = "#B0855A"
CORK_DARK = "#8F6A45"
PAPER = "#E2D8BF"
PAPER_OLD = "#CDBF9C"
INK = "#2B2622"
IRON = "#3C3A37"
STEEL = "#7D7B74"
GREEN_PAINT = "#4F5E52"
RED_PAINT = "#8E3B2E"
LEATHER = "#5E3B26"
LEATHER_DARK = "#43291B"
CLOTH_GREY = "#5D5A52"
CLOTH_BROWN = "#6A5440"
SOIL = "#3E3127"
DRY = "#8C7A55"
CERAMIC = "#A2552F"
RUBBER = "#252321"
BAG_BLACK = "#24252A"
ENAMEL_WHITE = "#E3DCC6"


def _wall_hanging(name: str, solid: bool = False):
    """La raíz de lo que se cuelga: un cuerpo estático si tiene colisión (para
    poder usarlo), o solo el dibujo."""
    return tb.empty(f"{name}-estatico" if solid else name)


# --------------------------------------------------------------------------
# Del oficio
# --------------------------------------------------------------------------


def build_job_board() -> bpy.types.Object:
    """El corcho de los encargos: 1 × 0,7 m con marco de madera y el rótulo de
    madera pintado encima. Se cuelga por la espalda (y = 0)."""
    rng = random.Random(11)
    root = _wall_hanging("corcho_encargos", solid=True)
    width, height = 1.0, 0.7
    mb = tb.MeshBuilder(seed=11)
    mb.box((width, 0.025, height), (0.0, -0.0125, height / 2.0), CORK, cuts=4, jitter=0.05)
    for x in (-width / 2.0, width / 2.0):
        mb.box((0.05, 0.04, height + 0.05), (x, -0.02, height / 2.0), WOOD_DARK, bevel=0.006)
    for z in (0.0, height):
        mb.box((width + 0.05, 0.04, 0.05), (0.0, -0.02, z), WOOD_DARK, bevel=0.006)
    # Agujeros de chinchetas viejas y alguna chincheta suelta.
    for _ in range(14):
        mb.cylinder(0.004, 0.004, (rng.uniform(-0.45, 0.45), -0.026, rng.uniform(0.05, 0.65)), CORK_DARK, rotation=(90.0, 0.0, 0.0), segments=6)
    for _ in range(4):
        mb.cylinder(0.008, 0.012, (rng.uniform(-0.4, 0.4), -0.03, rng.uniform(0.1, 0.6)), rng.choice((RED_PAINT, "#C2A040", GREEN_PAINT)), rotation=(90.0, 0.0, 0.0), segments=8)
    # El rótulo: una tabla con las letras pintadas (barras de pintura).
    mb.box((0.62, 0.025, 0.12), (0.0, -0.02, height + 0.14), WOOD_LIGHT, bevel=0.006)
    board = mb.finish("corcho", tb.material("madera", CORK), root)
    tb.collision_box("corcho", (width + 0.05, 0.04, height + 0.05), (0.0, -0.02, height / 2.0), root)
    tb.paint({board: None}, samples=12, ao=0.35, ground_z=None, seed=11)
    return root


def build_cash_box() -> bpy.types.Object:
    """La caja de los rublos: chapa verde con su cerradura y la tapa con el origen en
    las bisagras (de atrás). Dentro, los compartimentos de los billetes."""
    root = tb.empty("caja_rublos-estatico")
    width, depth, height = 0.34, 0.24, 0.1
    mb = tb.MeshBuilder(seed=21)
    mb.box((width, depth, 0.008), (0.0, 0.0, 0.004), GREEN_PAINT, bevel=0.002)
    for x in (-width / 2.0 + 0.004, width / 2.0 - 0.004):
        mb.box((0.008, depth, height), (x, 0.0, height / 2.0), GREEN_PAINT, bevel=0.002)
    for y in (-depth / 2.0 + 0.004, depth / 2.0 - 0.004):
        mb.box((width, 0.008, height), (0.0, y, height / 2.0), GREEN_PAINT, bevel=0.002)
    for x in (-0.06, 0.06):
        mb.box((0.006, depth - 0.02, height * 0.8), (x, 0.0, height * 0.4), "#3E4A40")
    mb.box((0.04, 0.012, 0.03), (0.0, -depth / 2.0 - 0.004, height - 0.02), "#A08A50", bevel=0.003)
    body = mb.finish("cuerpo", tb.material("metal", GREEN_PAINT), root)
    lid_root = tb.empty("tapa", root)
    lid_root.location = (0.0, depth / 2.0, height)
    lid = tb.MeshBuilder(seed=22)
    lid.box((width + 0.006, depth + 0.006, 0.012), (0.0, -depth / 2.0, 0.006), GREEN_PAINT, bevel=0.003)
    lid.box((0.08, 0.02, 0.008), (0.0, -depth + 0.01, 0.016), STEEL, bevel=0.002)
    lid_obj = lid.finish("tapa_malla", tb.material("metal", GREEN_PAINT), lid_root)
    tb.stain(body, "#7E4A2F", amount=0.6, scale=4.0, coverage=0.3, seed=23)
    tb.collision_box("caja", (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({body: None, lid_obj: None}, samples=12, ao=0.35, ground_z=0.0, seed=21)
    return root


def build_ledger() -> bpy.types.Object:
    """El libro de cuentas, cerrado: tapas de cartón jaspeado con lomo de tela y una
    cinta de registro. "tapa" se abre girando en Y (el origen, en el lomo)."""
    root = tb.empty("libro_cuentas-estatico")
    width, depth, thick = 0.24, 0.32, 0.045
    mb = tb.MeshBuilder(seed=31)
    mb.box((width - 0.008, depth - 0.008, thick - 0.012), (0.0, 0.0, thick / 2.0), PAPER_OLD, cuts=2, jitter=0.03)
    mb.box((width, depth, 0.005), (0.0, 0.0, 0.0025), "#3A4A5A", bevel=0.002)
    mb.box((0.02, depth, thick), (-width / 2.0, 0.0, thick / 2.0), "#2A2A30", bevel=0.004)
    mb.box((0.012, 0.004, 0.09), (0.03, -depth / 2.0 - 0.002, thick - 0.05), RED_PAINT)
    body = mb.finish("cuerpo", tb.material("papel", PAPER_OLD), root)
    cover_root = tb.empty("tapa", root)
    cover_root.location = (-width / 2.0, 0.0, thick)
    cover = tb.MeshBuilder(seed=32)
    cover.box((width, depth, 0.005), (width / 2.0, 0.0, -0.0025), "#3A4A5A", bevel=0.002, cuts=2, jitter=0.05)
    cover.box((0.12, 0.06, 0.002), (width / 2.0 + 0.01, -0.06, 0.0005), PAPER)
    cover_obj = cover.finish("tapa_malla", tb.material("papel", "#3A4A5A"), cover_root)
    tb.collision_box("libro", (width, depth, thick), (0.0, 0.0, thick / 2.0), root)
    tb.paint({body: None, cover_obj: None}, samples=12, ao=0.3, ground_z=0.0, seed=31)
    return root


def build_tag_box() -> bpy.types.Object:
    """La caja de las etiquetas: una caja de zapatos sin tapa, llena de etiquetas
    de cartón con su cordel, y un ovillo de cordel al lado."""
    rng = random.Random(41)
    root = tb.empty("caja_etiquetas-estatico")
    width, depth, height = 0.26, 0.16, 0.09
    mb = tb.MeshBuilder(seed=41)
    mb.box((width, depth, 0.006), (0.0, 0.0, 0.003), "#A8794E")
    for x in (-width / 2.0, width / 2.0):
        mb.box((0.006, depth, height), (x, 0.0, height / 2.0), "#A8794E", bevel=0.001)
    for y in (-depth / 2.0, depth / 2.0):
        mb.box((width, 0.006, height), (0.0, y, height / 2.0), "#A8794E", bevel=0.001)
    for k in range(14):
        x = -width / 2.0 + 0.02 + k * (width - 0.04) / 13.0
        mb.box((0.006, 0.07, 0.11), (x, rng.uniform(-0.02, 0.02), 0.07), rng.choice(("#C9A36F", "#BF9866", "#D1AC78")), rotation=(rng.uniform(-12, 12), rng.uniform(-8, 8), rng.uniform(-6, 6)))
    mb.sphere(0.035, (width / 2.0 + 0.05, 0.02, 0.035), "#C8B48A", segments=10)
    box = mb.finish("caja", tb.material("carton", "#A8794E"), root)
    tb.collision_box("caja", (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({box: None}, samples=12, ao=0.35, ground_z=0.0, seed=41)
    return root


def build_bin() -> bpy.types.Object:
    """El cubo de basura de chapa con su bolsa negra doblada por el borde. La bolsa
    ("bolsa") se oculta desde Godot cuando se saca."""
    root = tb.empty("cubo_basura-estatico")
    radius, height = 0.21, 0.55
    mb = tb.MeshBuilder(seed=51)
    mb.lathe([(0.0, 0.0), (radius - 0.02, 0.0), (radius - 0.01, 0.02), (radius, height), (radius - 0.012, height), (radius - 0.022, 0.03), (0.0, 0.03)], (0.0, 0.0, 0.0), "#6E7069", segments=20)
    for z in (0.12, 0.42):
        mb.lathe([(radius + 0.002, z - 0.012), (radius + 0.008, z), (radius + 0.002, z + 0.012)], (0.0, 0.0, 0.0), "#5A5C55", segments=20)
    bin_obj = mb.finish("cubo", tb.material("metal", "#6E7069"), root)
    bag_root = tb.empty("bolsa", root)
    bag = tb.MeshBuilder(seed=52)
    # La solapa que cae por fuera del borde (sube: mira hacia fuera) y el forro,
    # que baja por dentro (mira hacia dentro, que es desde donde se ve).
    bag.lathe([(radius + 0.025, height - 0.06), (radius + 0.02, height + 0.005), (radius - 0.025, height - 0.02), (radius - 0.03, 0.05), (0.0, 0.05)], (0.0, 0.0, 0.0), BAG_BLACK, segments=20, jitter=0.03)
    bag_obj = bag.finish("bolsa_malla", tb.material("plastico", BAG_BLACK), bag_root)
    tb.stain(bin_obj, "#7E4A2F", amount=0.6, scale=3.0, coverage=0.3, seed=53)
    tb.collision_box("cubo", (2.0 * radius, 2.0 * radius, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({bin_obj: None, bag_obj: None}, samples=12, ao=0.4, ground_z=0.0, seed=51)
    return root


def build_mop() -> bpy.types.Object:
    """La fregona: palo de madera, la pinza y la cabeza de tiras de algodón grises.
    De pie, con las tiras abajo (y = 0)."""
    rng = random.Random(61)
    root = tb.empty("fregona-fisico")
    mb = tb.MeshBuilder(seed=61)
    mb.bar((0.0, 0.0, 0.2), (0.0, 0.0, 1.3), 0.013, "#B08A5A", 8)
    mb.cylinder(0.03, 0.06, (0.0, 0.0, 0.2), "#3D6A5C", segments=10)
    for k in range(26):
        angle = 2.0 * math.pi * k / 26
        reach = rng.uniform(0.07, 0.12)
        end = (math.cos(angle) * reach, math.sin(angle) * reach, rng.uniform(0.0, 0.03))
        mb.tube([(math.cos(angle) * 0.02, math.sin(angle) * 0.02, 0.18), (math.cos(angle) * reach * 0.6, math.sin(angle) * reach * 0.6, 0.08), end], 0.008, rng.choice(("#9A968A", "#8A867B", "#A8A397")), segments=5)
    mop = mb.finish("fregona", tb.material("tela", "#9A968A"), root)
    tb.collision_box("fregona", (0.22, 0.22, 1.3), (0.0, 0.0, 0.65), root)
    tb.paint({mop: None}, samples=10, ao=0.3, seed=61)
    return root


def build_brush() -> bpy.types.Object:
    """El cepillo de fregar: lomo de madera con asa y cerdas duras."""
    rng = random.Random(71)
    root = tb.empty("cepillo-fisico")
    mb = tb.MeshBuilder(seed=71)
    mb.box((0.2, 0.065, 0.025), (0.0, 0.0, 0.035), WOOD_LIGHT, bevel=0.008)
    mb.box((0.12, 0.03, 0.03), (0.0, 0.0, 0.06), WOOD, bevel=0.01)
    for i in range(9):
        for j in range(3):
            mb.box((0.012, 0.012, 0.024), (-0.085 + i * 0.021, -0.02 + j * 0.02, 0.012), rng.choice(("#5A4A3A", "#4A3D30")), rotation=(rng.uniform(-6, 6), rng.uniform(-6, 6), 0.0))
    brush = mb.finish("cepillo", tb.material("madera", WOOD_LIGHT), root)
    tb.collision_box("cepillo", (0.2, 0.065, 0.075), (0.0, 0.0, 0.0375), root)
    tb.paint({brush: None}, samples=10, ao=0.3, seed=71)
    return root


def build_bag_roll() -> bpy.types.Object:
    """El rollo de bolsas de plástico en su soporte de alambre, en la pared."""
    root = _wall_hanging("rollo_bolsas", solid=True)
    mb = tb.MeshBuilder(seed=81)
    mb.box((0.26, 0.02, 0.04), (0.0, -0.01, 0.0), IRON, bevel=0.003)
    for x in (-0.12, 0.12):
        mb.bar((x, -0.01, 0.0), (x, -0.1, -0.05), 0.004, IRON, 6)
    mb.bar((-0.13, -0.1, -0.05), (0.13, -0.1, -0.05), 0.005, IRON, 6)
    mb.cylinder(0.045, 0.2, (0.0, -0.1, -0.05), "#C8CCC4", rotation=(0.0, 90.0, 0.0), segments=16)
    mb.box((0.18, 0.004, 0.16), (0.0, -0.147, -0.13), "#BFC4BC", rotation=(4.0, 0.0, 0.0), cuts=2, jitter=0.03)
    roll = mb.finish("rollo", tb.material("plastico", "#C8CCC4"), root)
    tb.collision_box("rollo", (0.26, 0.12, 0.14), (0.0, -0.08, -0.05), root)
    tb.paint({roll: None}, samples=10, ao=0.3, ground_z=None, seed=81)
    return root


def build_pegboard() -> bpy.types.Object:
    """El tablero de herramientas sobre el banco: contrachapado con las siluetas
    pintadas de lo que falta y unos ganchos."""
    root = _wall_hanging("tablero_herramientas")
    width, height = 1.4, 0.8
    mb = tb.MeshBuilder(seed=91)
    mb.box((width, 0.018, height), (0.0, -0.009, height / 2.0), "#B7966A", cuts=4, jitter=0.04)
    for x in (-width / 2.0, width / 2.0):
        mb.box((0.04, 0.03, height), (x, -0.015, height / 2.0), WOOD_DARK, bevel=0.004)
    # Siluetas pintadas: un martillo, una llave, unos alicates, un serrucho.
    for cx, cz, w, h in ((-0.45, 0.45, 0.06, 0.32), (-0.45, 0.62, 0.16, 0.05), (-0.15, 0.4, 0.05, 0.28), (0.12, 0.42, 0.14, 0.22), (0.45, 0.4, 0.3, 0.12)):
        mb.box((w, 0.004, h), (cx, -0.02, cz), "#5A3E2A")
    for x in (-0.45, -0.15, 0.12, 0.45):
        mb.bar((x, -0.018, 0.62), (x, -0.07, 0.64), 0.004, STEEL, 6)
    # Un destornillador y unos alicates que siguen colgados.
    mb.bar((-0.15, -0.06, 0.6), (-0.15, -0.06, 0.32), 0.006, STEEL, 6)
    mb.cylinder(0.014, 0.1, (-0.15, -0.06, 0.62), RED_PAINT, segments=8)
    board = mb.finish("tablero", tb.material("madera", "#B7966A"), root)
    tb.paint({board: None}, samples=10, ao=0.35, ground_z=None, seed=91)
    return root


def build_desk_lamp() -> bpy.types.Object:
    """El flexo del banco: base de fundición, dos brazos y la pantalla. "foco" es
    donde va la luz."""
    root = tb.empty("flexo-estatico")
    mb = tb.MeshBuilder(seed=101)
    mb.cylinder(0.08, 0.025, (0.0, 0.0, 0.0125), IRON, segments=14)
    mb.bar((0.0, 0.0, 0.02), (0.05, 0.0, 0.38), 0.009, "#3E4A40", 8)
    mb.bar((0.05, 0.0, 0.38), (0.32, 0.0, 0.46), 0.009, "#3E4A40", 8)
    mb.sphere(0.016, (0.05, 0.0, 0.38), IRON, segments=8)
    # La pantalla: por dentro (de arriba abajo, mira hacia dentro), el borde y por
    # fuera (de abajo arriba, mira hacia fuera).
    mb.lathe([(0.0, -0.008), (0.026, -0.008), (0.065, -0.095), (0.07, -0.09), (0.03, 0.0), (0.0, 0.0)], (0.34, 0.0, 0.47), "#3E4A40", rotation=(0.0, -25.0, 0.0), segments=16)
    lamp = mb.finish("flexo", tb.material("metal", "#3E4A40"), root)
    focus = tb.empty("foco", root)
    focus.location = (0.38, 0.0, 0.38)
    tb.collision_box("base", (0.16, 0.16, 0.03), (0.0, 0.0, 0.015), root)
    tb.paint({lamp: None}, samples=10, ao=0.3, ground_z=0.0, seed=101)
    return root


def build_wall_clock() -> bpy.types.Object:
    """El reloj de la consigna, de los de estación: esfera blanca con números de
    palo, aro negro y dos agujas que se mueven desde Godot: giran alrededor de la
    normal de la esfera (la Z de Godot; un ángulo negativo va en el sentido del
    reloj) y a 0 marcan las doce."""
    root = _wall_hanging("reloj_pared")
    radius = 0.17
    mb = tb.MeshBuilder(seed=111)
    mb.cylinder(radius + 0.02, 0.05, (0.0, -0.025, 0.0), "#1E1D1C", rotation=(90.0, 0.0, 0.0), segments=32)
    mb.cylinder(radius, 0.004, (0.0, -0.052, 0.0), ENAMEL_WHITE, rotation=(90.0, 0.0, 0.0), segments=32)
    for k in range(12):
        angle = 2.0 * math.pi * k / 12
        long = k % 3 == 0
        length = 0.035 if long else 0.02
        mid = radius - 0.02 - length / 2.0
        mb.box((0.008 if long else 0.005, 0.003, length), (math.sin(angle) * mid, -0.056, math.cos(angle) * mid), "#1E1D1C", rotation=(0.0, -math.degrees(angle), 0.0))
    face = mb.finish("esfera", tb.material("metal", ENAMEL_WHITE), root)
    hands = []
    for name, length, width in (("aguja_horas", 0.09, 0.012), ("aguja_minutos", 0.14, 0.008)):
        hand_root = tb.empty(name, root)
        hand_root.location = (0.0, -0.06 if name == "aguja_horas" else -0.064, 0.0)
        hand = tb.MeshBuilder(seed=112)
        hand.box((width, 0.003, length), (0.0, 0.0, length / 2.0 - 0.015), "#1E1D1C")
        hands.append(hand.finish(f"{name}_malla", tb.material("metal", "#1E1D1C"), hand_root))
    tb.paint({face: None, **{hand: None for hand in hands}}, samples=8, ao=0.2, ground_z=None, seed=111)
    return root


def build_planning_table() -> bpy.types.Object:
    """La mesa de planificar: una mesa de cocina con el hule gastado y un taburete."""
    root = tb.empty("mesa_planificacion-estatico")
    width, depth, height = 1.2, 0.7, 0.76
    mb = tb.MeshBuilder(seed=121)
    mb.box((width, depth, 0.035), (0.0, 0.0, height - 0.0175), WOOD, bevel=0.006)
    mb.box((width - 0.02, depth - 0.02, 0.004), (0.0, 0.0, height + 0.002), "#6E7F6A", cuts=3, jitter=0.04)
    for x in (-width / 2.0 + 0.05, width / 2.0 - 0.05):
        for y in (-depth / 2.0 + 0.05, depth / 2.0 - 0.05):
            mb.box((0.045, 0.045, height - 0.035), (x, y, (height - 0.035) / 2.0), WOOD_DARK, bevel=0.005)
    mb.box((width - 0.1, 0.02, 0.08), (0.0, -depth / 2.0 + 0.05, height - 0.08), WOOD_DARK, bevel=0.004)
    # El taburete.
    mb.cylinder(0.17, 0.035, (0.25, -0.6, 0.47), WOOD_LIGHT, segments=16)
    for k in range(3):
        angle = 2.0 * math.pi * k / 3 + 0.4
        mb.bar((0.25 + math.cos(angle) * 0.12, -0.6 + math.sin(angle) * 0.12, 0.45), (0.25 + math.cos(angle) * 0.18, -0.6 + math.sin(angle) * 0.18, 0.0), 0.016, WOOD_DARK, 8)
    table = mb.finish("mesa", tb.material("madera", WOOD), root)
    tb.collision_box("tablero", (width, depth, 0.04), (0.0, 0.0, height - 0.02), root)
    tb.collision_box("taburete", (0.34, 0.34, 0.49), (0.25, -0.6, 0.245), root)
    tb.paint({table: None}, samples=12, ao=0.4, ground_z=0.0, seed=121)
    return root


def build_wall_board() -> bpy.types.Object:
    """El tablero de la pared, sobre la mesa de planificar: corcho grande con un
    plano viejo de la ciudad a medio arrancar y chinchetas (en la Fase 3, tus
    páginas y el hilo de las rutas)."""
    rng = random.Random(131)
    root = _wall_hanging("tablero_pared")
    width, height = 1.6, 1.0
    mb = tb.MeshBuilder(seed=131)
    mb.box((width, 0.025, height), (0.0, -0.0125, height / 2.0), CORK, cuts=5, jitter=0.05)
    for x in (-width / 2.0, width / 2.0):
        mb.box((0.04, 0.035, height + 0.04), (x, -0.017, height / 2.0), WOOD_DARK, bevel=0.005)
    for z in (0.0, height):
        mb.box((width + 0.04, 0.035, 0.04), (0.0, -0.017, z), WOOD_DARK, bevel=0.005)
    # Lo que queda del plano viejo, roto en la esquina.
    mb.box((0.6, 0.003, 0.42), (-0.35, -0.028, 0.6), PAPER_OLD, rotation=(0.0, 3.0, 0.0), cuts=3, jitter=0.04)
    for _ in range(26):
        x0, z0 = rng.uniform(-0.62, -0.08), rng.uniform(0.42, 0.78)
        mb.box((rng.uniform(0.04, 0.2), 0.002, 0.004), (x0, -0.031, z0), "#6E6250", rotation=(0.0, rng.choice((0.0, 90.0, 35.0, -30.0)), 0.0))
    for _ in range(9):
        mb.cylinder(0.008, 0.012, (rng.uniform(-0.75, 0.75), -0.032, rng.uniform(0.08, 0.92)), rng.choice((RED_PAINT, "#C2A040", "#3E5A7A")), rotation=(90.0, 0.0, 0.0), segments=8)
    board = mb.finish("tablero", tb.material("madera", CORK), root)
    tb.paint({board: None}, samples=10, ao=0.3, ground_z=None, seed=131)
    return root


# --------------------------------------------------------------------------
# Del antiguo dueño
# --------------------------------------------------------------------------


def build_old_chair() -> bpy.types.Object:
    """Su silla: de madera curvada, con el cojín de lana hundido por los años y una
    pata atada con alambre."""
    root = tb.empty("silla_vieja-estatico")
    mb = tb.MeshBuilder(seed=141)
    seat = 0.45
    mb.box((0.44, 0.42, 0.035), (0.0, 0.0, seat), WOOD, bevel=0.008)
    for x in (-0.19, 0.19):
        for y in (-0.17, 0.17):
            mb.bar((x, y, 0.0), (x * 1.04, y * 1.04, seat - 0.02), 0.018, WOOD_DARK, 8)
    for x in (-0.19, 0.19):
        mb.bar((x, 0.19, seat), (x, 0.24, seat + 0.48), 0.017, WOOD_DARK, 8)
    for z in (seat + 0.3, seat + 0.46):
        mb.box((0.4, 0.025, 0.06), (0.0, 0.19 + 0.05 * (z - seat) / 0.48, z), WOOD, rotation=(-6.0, 0.0, 0.0), bevel=0.006)
    mb.bar((0.19, -0.17, 0.12), (0.19, -0.17, 0.2), 0.022, "#8A8A80", 6)
    mb.sphere(0.2, (0.0, 0.0, seat + 0.03), CLOTH_BROWN, segments=16, scale=(1.05, 1.0, 0.22), jitter=0.05)
    chair = mb.finish("silla", tb.material("madera", WOOD), root)
    # El hueco del cojín.
    for v in chair.data.vertices:
        if v.co.z > seat + 0.02 and abs(v.co.x) < 0.15 and abs(v.co.y) < 0.15:
            v.co.z -= 0.025 * max(0.0, 1.0 - (v.co.x ** 2 + v.co.y ** 2) / 0.0225)
    tb.collision_box("asiento", (0.44, 0.42, seat + 0.04), (0.0, 0.0, (seat + 0.04) / 2.0), root)
    tb.paint({chair: None}, samples=12, ao=0.4, ground_z=0.0, seed=141)
    return root


def build_calendar() -> bpy.types.Object:
    """El calendario de la pared: la lámina de arriba (un paisaje de abedules) y la
    hoja del mes con los días tachados hasta la Noche de la Caída; después, nada."""
    rng = random.Random(151)
    root = _wall_hanging("calendario")
    mb = tb.MeshBuilder(seed=151)
    mb.box((0.32, 0.004, 0.48), (0.0, -0.002, 0.0), PAPER_OLD, cuts=3, jitter=0.03)
    mb.box((0.28, 0.003, 0.2), (0.0, -0.005, 0.11), "#8FA095")
    for k in range(6):
        mb.box((0.01, 0.002, rng.uniform(0.1, 0.17)), (-0.11 + k * 0.045, -0.007, 0.08), "#E6E1D2")
    mb.box((0.28, 0.002, 0.03), (0.0, -0.006, -0.03), RED_PAINT)
    crossed = 19
    for day in range(31):
        row, col = divmod(day, 7)
        x, z = -0.12 + col * 0.04, -0.07 - row * 0.032
        mb.box((0.012, 0.002, 0.012), (x, -0.006, z), INK)
        if day < crossed:
            for angle in (45.0, -45.0):
                mb.box((0.028, 0.002, 0.003), (x, -0.008, z), "#5A2A22", rotation=(0.0, angle, 0.0))
    mb.cylinder(0.006, 0.01, (0.0, -0.006, 0.235), IRON, rotation=(90.0, 0.0, 0.0), segments=6)
    calendar = mb.finish("calendario", tb.material("papel", PAPER_OLD), root)
    tb.paint({calendar: None}, samples=6, ao=0.2, ground_z=None, seed=151)
    return root


def build_debt_list() -> bpy.types.Object:
    """La lista de deudas clavada con un clavo: nombres y cifras que nadie va a
    cobrar ya, unas tachadas."""
    rng = random.Random(161)
    root = _wall_hanging("lista_deudas")
    mb = tb.MeshBuilder(seed=161)
    mb.box((0.18, 0.003, 0.26), (0.0, -0.0015, 0.0), PAPER, rotation=(0.0, 4.0, 0.0), cuts=2, jitter=0.03)
    for k in range(9):
        z = 0.1 - k * 0.024
        mb.box((rng.uniform(0.05, 0.08), 0.002, 0.005), (-0.04, -0.004, z), INK)
        mb.box((0.03, 0.002, 0.005), (0.055, -0.004, z), INK)
        if rng.random() < 0.35:
            mb.box((0.14, 0.002, 0.003), (0.0, -0.006, z), "#7A2B25")
    mb.cylinder(0.005, 0.03, (0.0, -0.01, 0.115), IRON, rotation=(90.0, 0.0, 0.0), segments=6)
    paper = mb.finish("lista", tb.material("papel", PAPER), root)
    tb.paint({paper: None}, samples=6, ao=0.2, ground_z=None, seed=161)
    return root


def build_dead_plant() -> bpy.types.Object:
    """La planta muerta en su maceta de barro: tierra seca y los tallos doblados."""
    rng = random.Random(171)
    root = tb.empty("planta_muerta-estatico")
    mb = tb.MeshBuilder(seed=171)
    mb.lathe([(0.0, 0.0), (0.09, 0.0), (0.12, 0.2), (0.13, 0.2), (0.13, 0.22), (0.115, 0.22), (0.105, 0.03), (0.0, 0.03)], (0.0, 0.0, 0.0), CERAMIC, segments=18)
    mb.cylinder(0.11, 0.02, (0.0, 0.0, 0.19), SOIL, segments=18)
    for _ in range(7):
        angle = rng.uniform(0.0, 2.0 * math.pi)
        lean = rng.uniform(0.05, 0.25)
        top = (math.cos(angle) * lean, math.sin(angle) * lean, rng.uniform(0.35, 0.6))
        droop = (top[0] * 1.6, top[1] * 1.6, top[2] - rng.uniform(0.05, 0.2))
        mb.tube([(0.0, 0.0, 0.2), top, droop], 0.005, DRY, segments=5)
    plant = mb.finish("planta", tb.material("barro", CERAMIC), root)
    tb.collision_box("maceta", (0.26, 0.26, 0.22), (0.0, 0.0, 0.11), root)
    tb.paint({plant: None}, samples=10, ao=0.35, ground_z=0.0, seed=171)
    return root


def build_suitcases() -> bpy.types.Object:
    """Las maletas que nadie recogió de la consigna: tres, apiladas, con sus correas,
    sus cantoneras y el resguardo de cartón atado al asa."""
    rng = random.Random(181)
    root = tb.empty("maletas-estatico")
    mb = tb.MeshBuilder(seed=181)
    z = 0.0
    for width, depth, height, color in ((0.7, 0.42, 0.2, LEATHER), (0.62, 0.38, 0.17, "#6B5A3E"), (0.5, 0.32, 0.15, LEATHER_DARK)):
        turn = rng.uniform(-8.0, 8.0)
        mb.box((width, depth, height), (0.0, 0.0, z + height / 2.0), color, rotation=(0.0, 0.0, turn), bevel=0.02, cuts=2, jitter=0.05)
        for x in (-width / 4.0, width / 4.0):
            mb.box((0.035, depth + 0.006, height + 0.006), (x * math.cos(math.radians(turn)), x * math.sin(math.radians(turn)), z + height / 2.0), "#3A2A1E", rotation=(0.0, 0.0, turn))
        mb.box((0.12, 0.03, 0.03), (0.0, -depth / 2.0 - 0.01, z + height * 0.7), "#2A2018", rotation=(0.0, 0.0, turn), bevel=0.008)
        z += height
    mb.box((0.06, 0.004, 0.09), (0.08, -0.17, 0.42), "#C9A36F", rotation=(0.0, 0.0, 12.0))
    cases = mb.finish("maletas", tb.material("cuero", LEATHER), root)
    tb.collision_box("maletas", (0.72, 0.44, z), (0.0, 0.0, z / 2.0), root)
    tb.paint({cases: None}, samples=12, ao=0.4, ground_z=0.0, seed=181)
    return root


def build_rug() -> bpy.types.Object:
    """La alfombra del rincón de dormir: lana roja y ocre muy pisada, con el
    borde deshilachado."""
    rng = random.Random(191)
    root = tb.empty("alfombra")
    mb = tb.MeshBuilder(seed=191)
    width, depth = 1.9, 1.3
    mb.box((width, depth, 0.008), (0.0, 0.0, 0.004), "#7A3A2C", cuts=6, jitter=0.04)
    for inset, color in ((0.1, "#B08A4A"), (0.16, "#5A2A20")):
        mb.box((width - 2 * inset, 0.03, 0.002), (0.0, -depth / 2.0 + inset, 0.009), color)
        mb.box((width - 2 * inset, 0.03, 0.002), (0.0, depth / 2.0 - inset, 0.009), color)
        mb.box((0.03, depth - 2 * inset, 0.002), (-width / 2.0 + inset, 0.0, 0.009), color)
        mb.box((0.03, depth - 2 * inset, 0.002), (width / 2.0 - inset, 0.0, 0.009), color)
    mb.box((0.3, 0.3, 0.002), (0.0, 0.0, 0.009), "#B08A4A", rotation=(0.0, 0.0, 45.0))
    for x in range(30):
        for side in (-1.0, 1.0):
            mb.box((0.012, rng.uniform(0.02, 0.05), 0.003), (-width / 2.0 + 0.03 + x * (width - 0.06) / 29.0, side * (depth / 2.0 + 0.015), 0.002), "#C8B48A")
    rug = mb.finish("alfombra", tb.material("tela", "#7A3A2C"), root)
    tb.paint({rug: None}, samples=8, ao=0.2, ground_z=0.0, seed=191)
    return root


def build_coat_rack() -> bpy.types.Object:
    """El perchero de pie, con el abrigo del antiguo dueño todavía colgado y una
    bufanda."""
    root = tb.empty("perchero-estatico")
    mb = tb.MeshBuilder(seed=201)
    mb.bar((0.0, 0.0, 0.0), (0.0, 0.0, 1.8), 0.02, WOOD_DARK, 10)
    for k in range(3):
        angle = 2.0 * math.pi * k / 3
        mb.bar((0.0, 0.0, 0.02), (math.cos(angle) * 0.25, math.sin(angle) * 0.25, 0.0), 0.016, WOOD_DARK, 8)
        mb.bar((0.0, 0.0, 1.72), (math.cos(angle + 0.5) * 0.12, math.sin(angle + 0.5) * 0.12, 1.8), 0.01, WOOD_DARK, 6)
    # El abrigo: un cuerpo de tela que cuelga de un gancho, con los hombros caídos.
    mb.sphere(0.19, (0.06, -0.08, 1.38), CLOTH_GREY, segments=14, scale=(1.0, 0.55, 0.45), jitter=0.04)
    mb.lathe([(0.21, 0.6), (0.2, 1.0), (0.17, 1.32), (0.06, 1.42)], (0.06, -0.09, 0.0), CLOTH_GREY, segments=14, jitter=0.04)
    for side in (-1.0, 1.0):
        mb.tube([(0.06 + side * 0.17, -0.09, 1.36), (0.06 + side * 0.2, -0.12, 1.1), (0.06 + side * 0.19, -0.13, 0.86)], 0.045, CLOTH_GREY, segments=8)
    mb.tube([(0.0, -0.04, 1.62), (0.05, -0.1, 1.45), (0.1, -0.13, 1.2), (0.12, -0.14, 1.0)], 0.03, RED_PAINT, segments=6)
    rack = mb.finish("perchero", tb.material("madera", WOOD_DARK), root)
    tb.collision_box("perchero", (0.5, 0.5, 1.8), (0.0, 0.0, 0.9), root)
    tb.paint({rack: None}, samples=12, ao=0.35, ground_z=0.0, seed=201)
    return root


def models() -> dict:
    return {
        "corcho_encargos": build_job_board,
        "caja_rublos": build_cash_box,
        "libro_cuentas": build_ledger,
        "caja_etiquetas": build_tag_box,
        "cubo_basura": build_bin,
        "fregona": build_mop,
        "cepillo": build_brush,
        "rollo_bolsas": build_bag_roll,
        "tablero_herramientas": build_pegboard,
        "flexo": build_desk_lamp,
        "reloj_pared": build_wall_clock,
        "mesa_planificacion": build_planning_table,
        "tablero_pared": build_wall_board,
        "silla_vieja": build_old_chair,
        "calendario": build_calendar,
        "lista_deudas": build_debt_list,
        "planta_muerta": build_dead_plant,
        "maletas": build_suitcases,
        "alfombra": build_rug,
        "perchero": build_coat_rack,
    }
