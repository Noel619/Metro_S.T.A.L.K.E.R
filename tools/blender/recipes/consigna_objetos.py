"""Los objetos sueltos del trabajo en la consigna: lo que se coge, se usa, se tira,
se repara o se come.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Todo
descansa sobre z = 0. Las herramientas que se empuñan llevan el nodo vacío
``agarre``; las que tienen piezas que se mueven o se quitan las llevan con nombre
(los tornillos de la radio, su tapa).

- Basura: la bolsa llena (``bolsa_basura``), papeles, un trapo, una botella rota,
  una lata aplastada, la bombilla fundida y el cartón de una caja vaciada.
- Para el primer día: la bombilla nueva, las cerillas, la leña.
- Del banco: el destornillador, el cepillo de alambre y la aguja con su carrete.
- Para reparar: la radio de bolsillo (``tapa`` y ``tornillo_0``..``tornillo_3``,
  y ``contactos``) y las botas con la costura abierta (``costura``).
- Del mostrador: el fajo de billetes con su faja (``faja``, donde se escribe la
  cifra) y la etiqueta en blanco (``carton``, donde se escribe el precio).
- De comer: la sopa del puesto en su cuenco y medio pan.
- Mercancía: el botiquín, las vendas y un manojo de chatarra de cobre.
"""

from __future__ import annotations

import math
import random

import bpy

import tumansk_bpy as tb

BAG = "#26272C"
BAG_SHINE = "#3A3C44"
PLASTIC = "#C9CEC6"
PAPER = "#D8CFB6"
NEWSPRINT = "#BDB49C"
INK = "#2B2622"
RAG = "#7A6B58"
GLASS_GREEN = "#3E6B45"
TIN = "#A9A49A"
TIN_RED = "#9A3A30"
GLASS = "#E8E2C8"
GLASS_DEAD = "#4A4540"
BRASS = "#B59A5A"
MATCH_BOX = "#C9A040"
MATCH_LABEL = "#8E3B2E"
BIRCH = "#D8D0BE"
BIRCH_DARK = "#3A3632"
WOOD_CUT = "#C8A070"
WIRE = "#6E6A62"
STEEL = "#7D817E"
STEEL_DARK = "#4A4E4C"
RED_HANDLE = "#9A3A2E"
WOOD = "#9A6845"
THREAD = "#3E5A7A"
SPOOL = "#C8A878"
BAKELITE = "#3B2E26"
CREAM = "#D9CFB0"
GREEN_CORROSION = "#5E8A6A"
LEATHER = "#4E3424"
LEATHER_WORN = "#6B4A33"
SOLE = "#2A2522"
NOTE = "#B8A98A"
NOTE_PRINT = "#7E8A6E"
BAND = "#E2D8BF"
TAG = "#C9A36F"
STRING = "#C8B48A"
ENAMEL = "#E3DCC6"
ENAMEL_BLUE = "#3E5A7A"
SOUP = "#9A6A3A"
BREAD = "#6E4A2A"
BREAD_CRUMB = "#C8A878"
OLIVE = "#5E6448"
CROSS_RED = "#A83A2E"
GAUZE = "#E6E1D2"
COPPER = "#B06A3A"
CARDBOARD = "#A8794E"


def _grip(root: bpy.types.Object, at: tuple[float, float, float]) -> None:
    marker = tb.empty("agarre", root)
    marker.location = at


def _crumple(obj: bpy.types.Object, amount: float, seed: int) -> None:
    """Arruga una pieza: empuja cada vértice hacia dentro o hacia fuera."""
    rng = random.Random(seed)
    for v in obj.data.vertices:
        v.co += v.normal * rng.uniform(-amount, amount)


# --------------------------------------------------------------------------
# Basura
# --------------------------------------------------------------------------


def build_trash_bag() -> bpy.types.Object:
    """La bolsa de basura llena y cerrada: un bulto negro con el nudo y las orejas."""
    root = tb.empty("bolsa_basura-fisico")
    mb = tb.MeshBuilder(seed=301)
    mb.sphere(0.2, (0.0, 0.0, 0.2), BAG, segments=18, scale=(1.0, 0.9, 1.05))
    mb.lathe([(0.0, 0.36), (0.05, 0.37), (0.025, 0.42), (0.03, 0.45), (0.0, 0.46)], (0.0, 0.0, 0.0), BAG_SHINE, segments=10)
    for side in (-1.0, 1.0):
        mb.sphere(0.035, (side * 0.05, 0.0, 0.47), BAG_SHINE, segments=8, scale=(1.3, 0.4, 0.8))
    bag = mb.finish("bolsa", tb.material("plastico", BAG), root)
    _crumple(bag, 0.012, 301)
    tb.collision_box("bolsa", (0.4, 0.36, 0.46), (0.0, 0.0, 0.23), root)
    tb.paint({bag: None}, samples=12, ao=0.4, seed=301)
    return root


def build_plastic_bag() -> bpy.types.Object:
    """Una bolsa del rollo, doblada: lo que embolsa lo contaminado."""
    root = tb.empty("bolsa_plastico-fisico")
    mb = tb.MeshBuilder(seed=311)
    mb.box((0.2, 0.13, 0.008), (0.0, 0.0, 0.004), PLASTIC, cuts=3, jitter=0.04)
    mb.box((0.19, 0.06, 0.006), (0.0, 0.02, 0.011), "#BEC3BB", rotation=(0.0, 0.0, 2.0))
    bag = mb.finish("bolsa", tb.material("plastico", PLASTIC), root)
    _crumple(bag, 0.002, 311)
    tb.collision_box("bolsa", (0.2, 0.13, 0.02), (0.0, 0.0, 0.01), root)
    tb.paint({bag: None}, samples=8, ao=0.3, seed=311)
    return root


def build_papers() -> bpy.types.Object:
    """Papeles: un periódico viejo doblado y tres bolas de papel arrugado."""
    rng = random.Random(321)
    root = tb.empty("papeles-fisico")
    mb = tb.MeshBuilder(seed=321)
    mb.box((0.3, 0.22, 0.006), (0.0, 0.0, 0.003), NEWSPRINT, rotation=(0.0, 0.0, 8.0), cuts=3)
    for k in range(6):
        mb.box((0.12, 0.004, 0.002), (-0.06, -0.08 + k * 0.03, 0.0065), "#5A564C", rotation=(0.0, 0.0, 8.0))
    for k in range(3):
        mb.sphere(0.045, (rng.uniform(-0.1, 0.1), rng.uniform(-0.06, 0.06), 0.045 + 0.005), rng.choice((PAPER, NEWSPRINT)), segments=8, jitter=0.05)
    papers = mb.finish("papeles", tb.material("papel", PAPER), root)
    _crumple(papers, 0.008, 321)
    tb.collision_box("papeles", (0.3, 0.24, 0.1), (0.0, 0.0, 0.05), root)
    tb.paint({papers: None}, samples=8, ao=0.35, seed=321)
    return root


def build_rag() -> bpy.types.Object:
    """Un trapo sucio hecho una bola."""
    root = tb.empty("trapo-fisico")
    mb = tb.MeshBuilder(seed=331)
    mb.sphere(0.09, (0.0, 0.0, 0.04), RAG, segments=12, scale=(1.3, 1.0, 0.45), jitter=0.05)
    mb.box((0.12, 0.08, 0.006), (0.1, 0.03, 0.006), RAG, rotation=(0.0, 0.0, 25.0), cuts=2)
    rag = mb.finish("trapo", tb.material("tela", RAG), root)
    _crumple(rag, 0.01, 331)
    tb.stain(rag, "#3A3028", amount=0.7, scale=12.0, coverage=0.4, seed=331)
    tb.collision_box("trapo", (0.26, 0.2, 0.08), (0.02, 0.0, 0.04), root)
    tb.paint({rag: None}, samples=8, ao=0.35, seed=331)
    return root


def build_broken_bottle() -> bpy.types.Object:
    """El culo de una botella rota, con el borde en picos, y dos cristales sueltos."""
    rng = random.Random(341)
    root = tb.empty("botella_rota-fisico")
    mb = tb.MeshBuilder(seed=341)
    mb.lathe([(0.0, 0.0), (0.034, 0.0), (0.036, 0.006), (0.036, 0.07), (0.033, 0.07), (0.033, 0.008), (0.0, 0.012)], (0.0, 0.0, 0.0), GLASS_GREEN, segments=14)
    for k in range(7):
        angle = 2.0 * math.pi * k / 7
        height = rng.uniform(0.02, 0.06)
        mb.box((0.02, 0.003, height), (math.cos(angle) * 0.0345, math.sin(angle) * 0.0345, 0.07 + height / 2.0 - 0.004), GLASS_GREEN, rotation=(0.0, 0.0, math.degrees(angle) + 90.0))
    for k in range(2):
        mb.box((0.04, 0.03, 0.003), (0.07 + k * 0.03, rng.uniform(-0.03, 0.03), 0.002), GLASS_GREEN, rotation=(0.0, 0.0, rng.uniform(0, 180)))
    bottle = mb.finish("botella", tb.material("vidrio_opaco", GLASS_GREEN), root)
    tb.collision_box("botella", (0.08, 0.08, 0.12), (0.0, 0.0, 0.06), root)
    tb.paint({bottle: None}, samples=8, ao=0.3, seed=341)
    return root


def build_crushed_can() -> bpy.types.Object:
    """Una lata vacía, aplastada de un pisotón."""
    root = tb.empty("lata_vacia-fisico")
    mb = tb.MeshBuilder(seed=351)
    mb.cylinder(0.04, 0.05, (0.0, 0.0, 0.025), TIN, segments=14)
    mb.cylinder(0.0405, 0.03, (0.0, 0.0, 0.025), TIN_RED, segments=14)
    can = mb.finish("lata", tb.material("metal", TIN), root)
    rng = random.Random(351)
    for v in can.data.vertices:
        v.co.x *= 1.0 + 0.18 * math.sin(v.co.z * 60.0 + rng.uniform(-0.3, 0.3))
        v.co.y *= 0.8
    tb.collision_box("lata", (0.1, 0.066, 0.05), (0.0, 0.0, 0.025), root)
    tb.paint({can: None}, samples=8, ao=0.3, seed=351)
    return root


def build_folded_cardboard() -> bpy.types.Object:
    """El cartón de una caja vaciada, aplastado y doblado por la mitad."""
    root = tb.empty("carton_plegado-fisico")
    mb = tb.MeshBuilder(seed=361)
    mb.box((0.62, 0.42, 0.012), (0.0, 0.0, 0.006), CARDBOARD, cuts=3)
    mb.box((0.6, 0.4, 0.012), (0.0, 0.01, 0.022), CARDBOARD, rotation=(0.0, 0.0, 1.5), cuts=3, jitter=0.05)
    mb.box((0.62, 0.065, 0.004), (0.0, 0.0, 0.03), "#D8B26A", rotation=(0.0, 0.0, 1.0))
    board = mb.finish("carton", tb.material("carton", CARDBOARD), root)
    _crumple(board, 0.004, 361)
    tb.collision_box("carton", (0.64, 0.44, 0.04), (0.0, 0.0, 0.02), root)
    tb.paint({board: None}, samples=8, ao=0.3, seed=361)
    return root


def _bulb(root: bpy.types.Object, glass_color: str, material: str, seed: int, soot: bool = False) -> None:
    """Una bombilla de pera tumbada sobre el costado (rosca hacia -X); con ``soot``,
    ennegrecida por dentro."""
    mb = tb.MeshBuilder(seed=seed)
    mb.lathe(
        [(0.0, 0.0), (0.012, 0.002), (0.016, 0.012), (0.03, 0.04), (0.032, 0.06), (0.026, 0.078), (0.012, 0.087), (0.0, 0.089)],
        (-0.04, 0.0, 0.032), glass_color, rotation=(0.0, 90.0, 0.0), segments=16,
    )
    glass = mb.finish("cristal", tb.material(material, glass_color), root)
    if soot:
        tb.stain(glass, "#2A2622", amount=0.8, scale=30.0, coverage=0.5, seed=seed)
    base = tb.MeshBuilder(seed=seed + 1)
    for k in range(4):
        base.cylinder(0.0135 if k % 2 == 0 else 0.0125, 0.006, (-0.043 - k * 0.006, 0.0, 0.032), BRASS, rotation=(0.0, 90.0, 0.0), segments=12)
    base.cylinder(0.006, 0.004, (-0.068, 0.0, 0.032), "#2A2522", rotation=(0.0, 90.0, 0.0), segments=8)
    base_obj = base.finish("rosca", tb.material("metal", BRASS), root)
    tb.collision_box("bombilla", (0.12, 0.066, 0.066), (-0.012, 0.0, 0.033), root)
    tb.paint({glass: None, base_obj: None}, samples=8, ao=0.25, seed=seed)


def build_bulb() -> bpy.types.Object:
    """La bombilla nueva, de 60 vatios (en una de las cajas del antiguo dueño)."""
    root = tb.empty("bombilla-fisico")
    _bulb(root, GLASS, "bombilla_apagada", 371)
    return root


def build_dead_bulb() -> bpy.types.Object:
    """La bombilla fundida: el cristal ennegrecido por dentro."""
    root = tb.empty("bombilla_fundida-fisico")
    _bulb(root, GLASS_DEAD, "vidrio_opaco", 381, soot=True)
    return root


def build_matches() -> bpy.types.Object:
    """Una caja de cerillas con su etiqueta y el raspador de los costados."""
    root = tb.empty("cerillas-fisico")
    mb = tb.MeshBuilder(seed=391)
    mb.box((0.052, 0.036, 0.015), (0.0, 0.0, 0.0075), MATCH_BOX, bevel=0.001)
    mb.box((0.04, 0.026, 0.001), (0.0, 0.0, 0.0155), MATCH_LABEL)
    mb.box((0.012, 0.012, 0.0012), (0.0, 0.0, 0.0162), "#E2D8BF")
    for side in (-1.0, 1.0):
        mb.box((0.044, 0.001, 0.011), (0.0, side * 0.0182, 0.0075), "#5A3A2A")
    box = mb.finish("caja", tb.material("carton", MATCH_BOX), root)
    tb.collision_box("cerillas", (0.052, 0.036, 0.015), (0.0, 0.0, 0.0075), root)
    tb.paint({box: None}, samples=8, ao=0.25, seed=391)
    return root


def build_firewood() -> bpy.types.Object:
    """Un haz de leña: tres troncos de abedul partidos, atados con alambre."""
    rng = random.Random(401)
    root = tb.empty("lena-fisico")
    mb = tb.MeshBuilder(seed=401)
    for y, z in ((-0.045, 0.045), (0.045, 0.045), (0.0, 0.12)):
        length = 0.42 + rng.uniform(-0.03, 0.03)
        mb.cylinder(0.045, length, (rng.uniform(-0.02, 0.02), y, z), BIRCH, rotation=(0.0, 90.0, 0.0), segments=10, jitter=0.05)
        for end in (-1.0, 1.0):
            mb.cylinder(0.04, 0.004, (end * length / 2.0, y, z), WOOD_CUT, rotation=(0.0, 90.0, 0.0), segments=10)
        for _ in range(5):
            mb.box((0.03, 0.004, 0.004), (rng.uniform(-0.18, 0.18), y + rng.choice((-1, 1)) * 0.03, z + 0.03), BIRCH_DARK, rotation=(rng.uniform(-30, 30), 0.0, 0.0))
    for x in (-0.12, 0.12):
        mb.lathe([(0.1, -0.005), (0.103, 0.0), (0.1, 0.005)], (x, 0.0, 0.07), WIRE, rotation=(0.0, 90.0, 0.0), segments=14)
    wood = mb.finish("lena", tb.material("madera", BIRCH), root)
    tb.collision_box("lena", (0.44, 0.19, 0.17), (0.0, 0.0, 0.085), root)
    tb.paint({wood: None}, samples=10, ao=0.35, seed=401)
    return root


# --------------------------------------------------------------------------
# Del banco
# --------------------------------------------------------------------------


def build_screwdriver() -> bpy.types.Object:
    """Destornillador plano de mango rojo, tumbado a lo largo de X (punta hacia +X)."""
    root = tb.empty("destornillador-fisico")
    mb = tb.MeshBuilder(seed=411)
    mb.lathe([(0.0, 0.0), (0.012, 0.003), (0.014, 0.03), (0.0125, 0.075), (0.008, 0.09), (0.0, 0.09)], (-0.11, 0.0, 0.014), RED_HANDLE, rotation=(0.0, 90.0, 0.0), segments=12)
    mb.cylinder(0.0035, 0.13, (0.045, 0.0, 0.014), STEEL, rotation=(0.0, 90.0, 0.0), segments=8)
    mb.box((0.012, 0.007, 0.0012), (0.114, 0.0, 0.014), STEEL_DARK)
    tool = mb.finish("destornillador", tb.material("metal", RED_HANDLE), root)
    _grip(root, (-0.07, 0.0, 0.014))
    tb.collision_box("destornillador", (0.24, 0.03, 0.03), (0.0, 0.0, 0.014), root)
    tb.paint({tool: None}, samples=8, ao=0.25, seed=411)
    return root


def build_wire_brush() -> bpy.types.Object:
    """Cepillo de alambre de mango largo, para los contactos y el óxido."""
    rng = random.Random(421)
    root = tb.empty("cepillo_alambre-fisico")
    mb = tb.MeshBuilder(seed=421)
    mb.box((0.24, 0.022, 0.014), (-0.02, 0.0, 0.03), WOOD, bevel=0.005)
    mb.box((0.09, 0.024, 0.01), (0.07, 0.0, 0.019), STEEL_DARK)
    for i in range(10):
        for j in range(3):
            mb.box((0.004, 0.004, 0.016), (0.032 + i * 0.0085, -0.007 + j * 0.007, 0.008), STEEL, rotation=(rng.uniform(-8, 8), rng.uniform(-8, 8), 0.0))
    brush = mb.finish("cepillo", tb.material("madera", WOOD), root)
    _grip(root, (-0.09, 0.0, 0.03))
    tb.collision_box("cepillo", (0.24, 0.026, 0.04), (-0.01, 0.0, 0.02), root)
    tb.paint({brush: None}, samples=8, ao=0.25, seed=421)
    return root


def build_needle() -> bpy.types.Object:
    """La aguja de coser cuero clavada en su carrete de hilo encerado."""
    root = tb.empty("aguja_hilo-fisico")
    mb = tb.MeshBuilder(seed=431)
    mb.cylinder(0.022, 0.006, (0.0, 0.0, 0.003), SPOOL, segments=14)
    mb.cylinder(0.019, 0.038, (0.0, 0.0, 0.025), THREAD, segments=14)
    mb.cylinder(0.022, 0.006, (0.0, 0.0, 0.047), SPOOL, segments=14)
    mb.bar((0.0, 0.0, 0.03), (0.05, 0.0, 0.07), 0.0012, STEEL, 6)
    mb.tube([(0.05, 0.0, 0.07), (0.07, 0.0, 0.06), (0.06, 0.01, 0.03), (0.02, 0.019, 0.03)], 0.0008, THREAD, segments=4)
    spool = mb.finish("carrete", tb.material("madera", SPOOL), root)
    tb.collision_box("aguja", (0.06, 0.05, 0.06), (0.01, 0.0, 0.03), root)
    tb.paint({spool: None}, samples=8, ao=0.25, seed=431)
    return root


# --------------------------------------------------------------------------
# Para reparar
# --------------------------------------------------------------------------


def build_pocket_radio() -> bpy.types.Object:
    """La radio de bolsillo, de pie, con el altavoz hacia -Y. La ``tapa`` de atrás
    lleva cuatro tornillos (``tornillo_0``..``tornillo_3``, que giran y salen hacia
    +Y); debajo están los ``contactos`` de la pila, verdes de óxido."""
    root = tb.empty("radio_bolsillo-fisico")
    width, depth, height = 0.15, 0.04, 0.095
    mb = tb.MeshBuilder(seed=441)
    mb.box((width, depth - 0.006, height), (0.0, -0.003, height / 2.0), BAKELITE, bevel=0.008, segments=2)
    mb.box((0.07, 0.002, 0.06), (-0.035, -depth / 2.0 - 0.001, height / 2.0), CREAM)
    for k in range(7):
        mb.box((0.06, 0.003, 0.003), (-0.035, -depth / 2.0 - 0.002, 0.026 + k * 0.007), "#6E6250")
    mb.box((0.05, 0.002, 0.022), (0.04, -depth / 2.0 - 0.001, 0.065), CREAM)
    for k in range(9):
        mb.box((0.0008, 0.002, 0.006 if k % 2 else 0.01), (0.02 + k * 0.005, -depth / 2.0 - 0.002, 0.065), INK)
    mb.cylinder(0.012, 0.008, (0.04, -depth / 2.0 - 0.003, 0.03), "#C8C2AE", rotation=(90.0, 0.0, 0.0), segments=14)
    mb.box((0.005, 0.004, 0.06), (width / 2.0 - 0.01, 0.0, height + 0.025), STEEL, bevel=0.001)
    body = mb.finish("cuerpo", tb.material("metal", BAKELITE), root)
    contacts = tb.MeshBuilder(seed=442)
    contacts.box((0.08, 0.004, 0.05), (0.0, depth / 2.0 - 0.009, height / 2.0), "#2A2522")
    for x in (-0.03, 0.03):
        contacts.box((0.012, 0.004, 0.02), (x, depth / 2.0 - 0.007, height / 2.0), GREEN_CORROSION)
    contacts_obj = contacts.finish("contactos", tb.material("metal", GREEN_CORROSION), root)
    cover_root = tb.empty("tapa", root)
    cover = tb.MeshBuilder(seed=443)
    cover.box((width - 0.004, 0.006, height - 0.004), (0.0, depth / 2.0 - 0.003, height / 2.0), "#4A3A30", bevel=0.003)
    cover_obj = cover.finish("tapa_malla", tb.material("metal", "#4A3A30"), cover_root)
    screws = []
    for index, (x, z) in enumerate(((-0.06, 0.012), (0.06, 0.012), (-0.06, height - 0.012), (0.06, height - 0.012))):
        screw = tb.MeshBuilder(seed=450 + index)
        screw.cylinder(0.0045, 0.003, (0.0, 0.0, 0.0), STEEL, rotation=(90.0, 0.0, 0.0), segments=8)
        screw.box((0.007, 0.0012, 0.0012), (0.0, 0.0018, 0.0), STEEL_DARK)
        obj = screw.finish(f"tornillo_{index}", tb.material("metal", STEEL), cover_root)
        obj.location = (x, depth / 2.0 + 0.0015, z)
        screws.append(obj)
    tb.stain(body, "#6E5A48", amount=0.4, scale=20.0, coverage=0.3, seed=441)
    tb.collision_box("radio", (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({body: None, contacts_obj: None, cover_obj: None, **{s: None for s in screws}}, samples=8, ao=0.3, seed=441)
    return root


def build_boots() -> bpy.types.Object:
    """Unas botas de trabajo gastadas; a la derecha se le ha abierto la ``costura``
    del costado (una raja que se cierra al coserla)."""
    root = tb.empty("botas-fisico")
    mb = tb.MeshBuilder(seed=461)
    for side, turn in ((-1.0, 6.0), (1.0, -4.0)):
        x = side * 0.07
        c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))

        def at(px: float, py: float, pz: float) -> tuple[float, float, float]:
            return (x + px * c - py * s, px * s + py * c, pz)

        mb.box((0.1, 0.29, 0.03), at(0.0, -0.02, 0.015), SOLE, rotation=(0.0, 0.0, turn), bevel=0.01)
        mb.sphere(0.06, at(0.0, -0.12, 0.05), LEATHER, segments=12, scale=(0.85, 1.3, 0.75))
        mb.box((0.085, 0.16, 0.08), at(0.0, -0.02, 0.07), LEATHER, rotation=(0.0, 0.0, turn), bevel=0.02)
        mb.cylinder(0.05, 0.2, at(0.0, 0.06, 0.2), LEATHER_WORN, segments=12)
        mb.lathe([(0.052, 0.0), (0.055, 0.01), (0.045, 0.01)], at(0.0, 0.06, 0.29), LEATHER, segments=12)
    boots = mb.finish("botas", tb.material("cuero", LEATHER), root)
    seam = tb.MeshBuilder(seed=462)
    seam.box((0.004, 0.09, 0.05), (0.07 + 0.05, 0.0, 0.08), "#1E1712", rotation=(0.0, 0.0, -4.0))
    seam_obj = seam.finish("costura", tb.material("cuero", "#1E1712"), root)
    tb.stain(boots, "#8A7A60", amount=0.5, scale=10.0, coverage=0.35, seed=461)
    tb.collision_box("botas", (0.28, 0.32, 0.3), (0.0, -0.02, 0.15), root)
    tb.paint({boots: None, seam_obj: None}, samples=10, ao=0.35, seed=461)
    return root


# --------------------------------------------------------------------------
# Del mostrador
# --------------------------------------------------------------------------


def build_wad() -> bpy.types.Object:
    """Un fajo de billetes doblados por la mitad con su ``faja`` de papel (ahí se
    escribe la cifra, desde Godot)."""
    rng = random.Random(471)
    root = tb.empty("billetes-fisico")
    mb = tb.MeshBuilder(seed=471)
    for k in range(6):
        mb.box((0.14, 0.065, 0.0025), (rng.uniform(-0.003, 0.003), rng.uniform(-0.002, 0.002), 0.0015 + k * 0.0026), rng.choice((NOTE, NOTE_PRINT, "#A89878")), rotation=(0.0, 0.0, rng.uniform(-2.0, 2.0)))
    notes = mb.finish("billetes", tb.material("papel", NOTE), root)
    band = tb.MeshBuilder(seed=472)
    band.box((0.04, 0.069, 0.019), (0.0, 0.0, 0.0085), BAND)
    band_obj = band.finish("faja", tb.material("papel", BAND), root)
    tb.collision_box("billetes", (0.14, 0.07, 0.018), (0.0, 0.0, 0.009), root)
    tb.paint({notes: None, band_obj: None}, samples=8, ao=0.25, seed=471)
    return root


def build_tag() -> bpy.types.Object:
    """Una etiqueta de cartón en blanco con su cordel. El ``carton`` es donde se
    escribe el precio (desde Godot), en la cara de arriba."""
    root = tb.empty("etiqueta-fisico")
    mb = tb.MeshBuilder(seed=481)
    mb.prism([(-0.045, -0.022), (0.03, -0.022), (0.045, -0.008), (0.045, 0.008), (0.03, 0.022), (-0.045, 0.022)], 0.0015, (0.0, 0.0, 0.00075), TAG)
    mb.cylinder(0.004, 0.0018, (0.034, 0.0, 0.0012), "#8A6A40", segments=8)
    mb.tube([(0.034, 0.0, 0.002), (0.06, 0.01, 0.002), (0.08, -0.01, 0.002), (0.1, 0.004, 0.002)], 0.0009, STRING, segments=4)
    tag = mb.finish("carton", tb.material("carton", TAG), root)
    tb.collision_box("etiqueta", (0.1, 0.05, 0.006), (0.02, 0.0, 0.003), root)
    tb.paint({tag: None}, samples=6, ao=0.2, seed=481)
    return root


# --------------------------------------------------------------------------
# De comer
# --------------------------------------------------------------------------


def build_soup() -> bpy.types.Object:
    """La sopa del puesto: cuenco de chapa esmaltada con su cuchara."""
    root = tb.empty("sopa-fisico")
    mb = tb.MeshBuilder(seed=491)
    mb.lathe([(0.0, 0.0), (0.045, 0.0), (0.075, 0.055), (0.08, 0.06), (0.074, 0.06), (0.068, 0.054), (0.04, 0.008), (0.0, 0.008)], (0.0, 0.0, 0.0), ENAMEL, segments=20)
    mb.lathe([(0.081, 0.057), (0.082, 0.061), (0.075, 0.062)], (0.0, 0.0, 0.0), ENAMEL_BLUE, segments=20)
    mb.cylinder(0.066, 0.004, (0.0, 0.0, 0.042), SOUP, segments=20)
    for k in range(5):
        angle = k * 1.3
        mb.sphere(0.008, (math.cos(angle) * 0.035, math.sin(angle) * 0.035, 0.045), "#C8A040", segments=6, scale=(1.0, 1.0, 0.5))
    mb.bar((0.02, 0.0, 0.045), (0.11, 0.03, 0.08), 0.004, STEEL, 6)
    mb.sphere(0.014, (0.02, 0.0, 0.044), STEEL, segments=8, scale=(1.4, 1.0, 0.35))
    bowl = mb.finish("cuenco", tb.material("metal", ENAMEL), root)
    tb.collision_box("cuenco", (0.16, 0.16, 0.065), (0.0, 0.0, 0.0325), root)
    tb.paint({bowl: None}, samples=10, ao=0.3, seed=491)
    return root


def build_bread() -> bpy.types.Object:
    """Medio pan negro, con el corte a la vista."""
    root = tb.empty("pan-fisico")
    mb = tb.MeshBuilder(seed=501)
    mb.sphere(0.07, (0.0, 0.0, 0.04), BREAD, segments=14, scale=(1.0, 1.25, 0.65), jitter=0.04)
    mb.box((0.13, 0.004, 0.08), (0.0, 0.0, 0.04), BREAD_CRUMB, rotation=(0.0, 0.0, 0.0))
    bread = mb.finish("pan", tb.material("pan", BREAD), root)
    for v in bread.data.vertices:
        if v.co.y < 0.0:
            v.co.y = max(v.co.y, -0.002)
    tb.collision_box("pan", (0.14, 0.09, 0.08), (0.0, 0.04, 0.04), root)
    tb.paint({bread: None}, samples=8, ao=0.3, seed=501)
    return root


def build_salo() -> bpy.types.Object:
    """Un trozo de salo (tocino salado) envuelto en papel de estraza atado con cordel: el
    cebo para la Jauría (F3-07, F3-10). Es comida: quien lo da, se queda sin ella."""
    root = tb.empty("salo-fisico")
    mb = tb.MeshBuilder(seed=505)
    # El tocino: blanco amarillento con la corteza parda y la sal por encima.
    mb.box((0.12, 0.07, 0.045), (0.0, 0.0, 0.0225), "#D9CBB0", bevel=0.01, jitter=0.03)
    mb.box((0.122, 0.072, 0.008), (0.0, 0.0, 0.004), "#7A5236", bevel=0.003)
    mb.box((0.11, 0.004, 0.02), (0.0, -0.036, 0.03), "#B98A6A")
    salo = mb.finish("salo", tb.material("pan", "#D9CBB0"), root)
    paper = tb.MeshBuilder(seed=506)
    paper.box((0.13, 0.08, 0.004), (-0.01, 0.01, 0.047), "#9C8466", rotation=(0.0, 4.0, -6.0), jitter=0.05)
    paper.box((0.004, 0.084, 0.05), (0.066, 0.0, 0.025), "#9C8466", rotation=(0.0, 0.0, -4.0), jitter=0.05)
    paper.bar((0.0, -0.045, 0.05), (0.0, 0.045, 0.05), 0.0025, "#6B5A40", 6)
    wrap = paper.finish("salo_papel", tb.material("papel", "#9C8466"), root)
    tb.collision_box("salo", (0.13, 0.08, 0.055), (0.0, 0.0, 0.0275), root)
    tb.paint({salo: None, wrap: None}, samples=8, ao=0.3, seed=505)
    return root


# --------------------------------------------------------------------------
# Mercancía
# --------------------------------------------------------------------------


def build_first_aid() -> bpy.types.Object:
    """El botiquín de chapa: caja verde oliva con la cruz roja pintada."""
    root = tb.empty("botiquin-fisico")
    mb = tb.MeshBuilder(seed=511)
    mb.box((0.22, 0.12, 0.08), (0.0, 0.0, 0.04), OLIVE, bevel=0.006, cuts=2)
    mb.box((0.06, 0.002, 0.018), (0.0, -0.061, 0.045), CROSS_RED)
    mb.box((0.018, 0.002, 0.06), (0.0, -0.061, 0.045), CROSS_RED)
    mb.box((0.04, 0.012, 0.01), (0.0, 0.0, 0.084), STEEL_DARK, bevel=0.003)
    box = mb.finish("botiquin", tb.material("metal", OLIVE), root)
    tb.stain(box, "#7E4A2F", amount=0.5, scale=12.0, coverage=0.3, seed=511)
    tb.collision_box("botiquin", (0.22, 0.12, 0.09), (0.0, 0.0, 0.045), root)
    tb.paint({box: None}, samples=8, ao=0.3, seed=511)
    return root


def build_bandages() -> bpy.types.Object:
    """Tres rollos de venda atados con una tira."""
    root = tb.empty("vendas-fisico")
    mb = tb.MeshBuilder(seed=521)
    for k in range(3):
        mb.cylinder(0.028, 0.06, (-0.06 + k * 0.06, 0.0, 0.028), GAUZE, rotation=(90.0, 0.0, 0.0), segments=14)
        mb.cylinder(0.008, 0.061, (-0.06 + k * 0.06, 0.0, 0.028), "#BDB6A2", rotation=(90.0, 0.0, 0.0), segments=8)
    mb.box((0.18, 0.012, 0.06), (0.0, 0.0, 0.03), "#C8C0A8")
    rolls = mb.finish("vendas", tb.material("tela", GAUZE), root)
    tb.collision_box("vendas", (0.18, 0.062, 0.058), (0.0, 0.0, 0.029), root)
    tb.paint({rolls: None}, samples=8, ao=0.3, seed=521)
    return root


def build_copper() -> bpy.types.Object:
    """Un manojo de cable de cobre pelado, enrollado: chatarra que se vende al peso."""
    rng = random.Random(531)
    root = tb.empty("chatarra_cobre-fisico")
    mb = tb.MeshBuilder(seed=531)
    for k in range(7):
        radius = 0.09 + rng.uniform(-0.015, 0.015)
        tilt = rng.uniform(-12, 12)
        points = []
        for j in range(25):
            a = 2.0 * math.pi * j / 24
            points.append((math.cos(a) * radius, math.sin(a) * radius, 0.012 + k * 0.006 + math.sin(a * 2.0 + k) * 0.004 + math.cos(a) * math.radians(tilt) * 0.1))
        mb.tube(points, 0.004, rng.choice((COPPER, "#9A5A30", "#C07A48")), segments=5, caps=False)
    coil = mb.finish("cobre", tb.material("metal", COPPER), root)
    tb.stain(coil, "#5E7A5A", amount=0.5, scale=25.0, coverage=0.25, seed=531)
    tb.collision_box("cobre", (0.2, 0.2, 0.06), (0.0, 0.0, 0.03), root)
    tb.paint({coil: None}, samples=8, ao=0.3, seed=531)
    return root


def models() -> dict:
    return {
        "bolsa_basura": build_trash_bag,
        "bolsa_plastico": build_plastic_bag,
        "papeles": build_papers,
        "trapo": build_rag,
        "botella_rota": build_broken_bottle,
        "lata_vacia": build_crushed_can,
        "carton_plegado": build_folded_cardboard,
        "bombilla": build_bulb,
        "bombilla_fundida": build_dead_bulb,
        "cerillas": build_matches,
        "lena": build_firewood,
        "destornillador": build_screwdriver,
        "cepillo_alambre": build_wire_brush,
        "aguja_hilo": build_needle,
        "radio_bolsillo": build_pocket_radio,
        "botas": build_boots,
        "billetes": build_wad,
        "etiqueta": build_tag,
        "sopa": build_soup,
        "pan": build_bread,
        "salo": build_salo,
        "botiquin": build_first_aid,
        "vendas": build_bandages,
        "chatarra_cobre": build_copper,
    }
