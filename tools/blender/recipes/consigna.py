"""El depósito de la Fase 2: la antigua consigna de la estación (docs/DEPOSITO.md).

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba (en
Godot, la Y de Blender pasa a ser -Z). La sala mide 9 × 7 m: x de -4,5 a 4,5 e
y de -3,25 (el muro del pasillo, por dentro) a 3,75 (el fondo). Una bóveda
rebajada de ladrillo encalado va de 2,7 m en los muros a 3,4 m en el centro.

En el muro del pasillo están la ventanilla (x de -1,5 a 1,5, 2,3 m de alto),
con el mostrador dentro y la persiana por fuera, y la puerta de chapa (x de 3,4
a 4,3). Un tabique de tablas en y = 1,5 aparta el rincón donde se vive; se pasa
por una manta colgada.

Modelos: "consigna_sala" (suelo, muros, bóveda, tabique, zócalo de azulejos,
tuberías), "consigna_persiana" (el cajón y las guías, y la cortina: sus lamas
son nodos sueltos, "lama_00" arriba a "lama_22" abajo, para enrollarla desde
Godot), "consigna_puerta" (el marco y la hoja, con el origen en las bisagras),
"consigna_mostrador" (el de la ventanilla) y "consigna_baldas" (las baldas
numeradas de la consigna, que ahora son el almacén).
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Matrix, Vector

import tumansk_bpy as tb

# Paleta (docs/ESTILO.md: el depósito, cálido y gastado).
GROUT = "#3B3631"
FLOOR_A = "#8E857A"
FLOOR_B = "#7C746A"
FLOOR_WORN = "#9C9284"
FLOOR_CHIPPED = "#5E5850"
TILE = "#2F6F73"
TILE_CREAM = "#D3C8AC"
PLASTER = "#CDBF9F"
PLASTER_STAIN = "#9C8F72"
WHITEWASH = "#D8CCB0"
BRICK = "#8A5442"
BRICK_DARK = "#6E4033"
TRIM = "#5A3B2A"
PIPE_GREEN = "#4F5E52"
PIPE_RUST = "#6B4A3A"
RUST = "#8E4A2F"
METAL_GREEN = "#55615A"
SHUTTER = "#5F6E78"
SHUTTER_PAINT = "#6E7C84"
DOOR_GREEN = "#3F5248"
WOOD = "#8A5A3B"
WOOD_DARK = "#6E4A32"
WOOD_LIGHT = "#9A6845"
VARNISH = "#7A4A2C"
PLANK = "#7B5A3E"
PLANK_DARK = "#5E4430"
BLANKET = "#5B5C45"
BLANKET_DARK = "#474834"
ENAMEL = "#2E4F45"
ENAMEL_WHITE = "#E3DCC6"
IRON = "#3C3A37"

HALF_W = 4.5
FRONT = -3.25
BACK = 3.75
WALL = 0.3
SPRING = 2.7
CROWN = 3.4
SHUTTER_X = (-1.5, 1.5)
SHUTTER_H = 2.3
DOOR_X = (3.4, 4.3)
DOOR_H = 2.1
PARTITION_Y = 1.5
PARTITION_END = 1.2
DOORWAY = (-2.4, -1.4)
DOORWAY_H = 2.05
TILE_BAND = 1.35
# El radio de la bóveda (una cuerda de 9 m con 0,7 m de flecha).
VAULT_R = ((2.0 * HALF_W) ** 2 / 4.0 + (CROWN - SPRING) ** 2) / (2.0 * (CROWN - SPRING))


def vault_z(x: float) -> float:
    """La altura de la bóveda (por dentro) en ``x``."""
    x = max(-HALF_W, min(HALF_W, x))
    return SPRING + math.sqrt(VAULT_R ** 2 - x * x) - math.sqrt(VAULT_R ** 2 - HALF_W ** 2)


def _placed(mb: tb.MeshBuilder, matrix: Matrix, build) -> None:
    """Construye con ``build(mb)`` y lleva lo construido a su sitio con ``matrix``."""
    before = set(mb.bm.faces)
    build(mb)
    faces = [f for f in mb.bm.faces if f not in before]
    verts = list(dict.fromkeys(v for f in faces for v in f.verts))
    for v in verts:
        v.co = matrix @ v.co


# --------------------------------------------------------------------------
# La sala
# --------------------------------------------------------------------------


def _floor(root: bpy.types.Object, rng: random.Random) -> list:
    """Baldosas de 41 × 41 cm, cada una un poco torcida; el paso del mostrador al
    banco, más gastado. Por tiras de filas: una malla grande de golpe es lenta."""
    cols, rows = 22, 17
    width, depth = 2.0 * HALF_W, BACK - FRONT
    tile_x, tile_y = width / cols, depth / rows
    objects = []
    for start in range(0, rows, 3):
        mb = tb.MeshBuilder(seed=100 + start)
        end = min(rows, start + 3)
        y0, y1 = FRONT + start * tile_y, FRONT + end * tile_y
        mb.box((width, y1 - y0, 0.04), (0.0, (y0 + y1) / 2.0, -0.02), GROUT)
        for j in range(start, end):
            for i in range(cols):
                x = -HALF_W + (i + 0.5) * tile_x
                y = FRONT + (j + 0.5) * tile_y
                color = FLOOR_A if (i + j) % 2 == 0 else FLOOR_B
                if -1.2 < x < 3.6 and -3.0 < y < -0.2 and rng.random() < 0.7:
                    color = FLOOR_WORN
                if rng.random() < 0.05:
                    color = FLOOR_CHIPPED
                mb.box(
                    (tile_x - 0.008, tile_y - 0.008, 0.024),
                    (x, y, 0.012 + rng.uniform(-0.002, 0.002)),
                    color,
                    rotation=(rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(-1.0, 1.0)),
                    bevel=0.004,
                    jitter=0.06,
                )
        objects.append(mb.finish(f"suelo_{start // 3}", tb.material("sala", PLASTER), root))
    # El sumidero junto a la pila.
    mb = tb.MeshBuilder(seed=99)
    mb.box((0.32, 0.32, 0.012), (3.95, -1.75, 0.022), IRON, bevel=0.003)
    for k in range(6):
        mb.box((0.26, 0.018, 0.016), (3.95, -1.88 + k * 0.052, 0.026), "#2A2826")
    objects.append(mb.finish("sumidero", tb.material("metal", IRON), root))
    return objects


def _arch_outline(x0: float, x1: float, base: float, inset: float = 0.0) -> list:
    """El contorno (x, z) del tímpano de un muro de fondo: de ``base`` a la bóveda."""
    points = [(x0, base), (x1, base)]
    steps = 24
    for k in range(steps + 1):
        x = x1 - (x1 - x0) * k / steps
        points.append((x, vault_z(x) - inset))
    return points


def _walls(root: bpy.types.Object, rng: random.Random) -> list:
    mb = tb.MeshBuilder(seed=201)
    span = (-HALF_W - WALL, HALF_W + WALL)
    # El muro del pasillo: se construye mirando a -Y y se gira media vuelta, para
    # que su cara buena mire a la sala. Con el giro, x pasa a -x.
    front_holes = [
        (-SHUTTER_X[1], 0.0, -SHUTTER_X[0], SHUTTER_H),
        (-DOOR_X[1], 0.0, -DOOR_X[0], DOOR_H),
    ]
    _placed(
        mb,
        Matrix.Translation((0.0, FRONT, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
        lambda b: b.slab(span, (0.0, SPRING), (0.0, WALL), PLASTER, holes=front_holes, step=0.5, ring=0.12),
    )
    # El fondo.
    mb.slab(span, (0.0, SPRING), (BACK, BACK + WALL), PLASTER, step=0.5, back=False)
    # Los muros de los lados: hechos mirando a -Y y girados un cuarto de vuelta (el
    # izquierdo, a la izquierda: su cara buena mira a +X; el derecho, al revés).
    length = (FRONT - WALL, BACK + WALL)
    _placed(
        mb,
        Matrix.Translation((-HALF_W, 0.0, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
        lambda b: b.slab(length, (0.0, SPRING), (0.0, WALL), PLASTER, step=0.5, back=False),
    )
    _placed(
        mb,
        Matrix.Translation((HALF_W, 0.0, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
        lambda b: b.slab((-length[1], -length[0]), (0.0, SPRING), (0.0, WALL), PLASTER, step=0.5, back=False),
    )
    # Los tímpanos de los dos muros de fondo, hasta la bóveda.
    outline = _arch_outline(-HALF_W, HALF_W, SPRING - 0.01)
    mb.prism(outline, WALL, (0.0, FRONT - WALL / 2.0, 0.0), PLASTER, rotation=(90.0, 0.0, 0.0))
    mb.prism(outline, WALL, (0.0, BACK + WALL / 2.0, 0.0), PLASTER, rotation=(90.0, 0.0, 0.0))
    # Los dinteles de la ventanilla y de la puerta, de hormigón.
    mb.box((SHUTTER_X[1] - SHUTTER_X[0] + 0.3, 0.32, 0.18), (0.0, FRONT - WALL / 2.0, SHUTTER_H + 0.09), "#8C877D", bevel=0.01)
    mb.box((DOOR_X[1] - DOOR_X[0] + 0.24, 0.32, 0.16), ((DOOR_X[0] + DOOR_X[1]) / 2.0, FRONT - WALL / 2.0, DOOR_H + 0.08), "#8C877D", bevel=0.01)
    walls = mb.finish("muros", tb.material("sala", PLASTER), root)
    tb.stain(walls, PLASTER_STAIN, amount=0.55, scale=1.1, coverage=0.4, seed=202)
    return [walls]


def _vault(root: bpy.types.Object, rng: random.Random) -> list:
    """La bóveda encalada, con algún trozo donde se cayó la cal y asoma el ladrillo."""
    mb = tb.MeshBuilder(seed=301)
    columns, rows = 28, 14
    for i in range(columns):
        x0 = -HALF_W + 2.0 * HALF_W * i / columns
        x1 = -HALF_W + 2.0 * HALF_W * (i + 1) / columns
        for j in range(rows):
            y0 = FRONT + (BACK - FRONT) * j / rows
            y1 = FRONT + (BACK - FRONT) * (j + 1) / rows
            mb.quad(
                [(x0, y0, vault_z(x0)), (x0, y1, vault_z(x0)), (x1, y1, vault_z(x1)), (x1, y0, vault_z(x1))],
                WHITEWASH,
                cuts=1,
            )
    # Desconchones: ladrillos a la vista, un poco por debajo de la cal.
    for cx, cy, w, d in ((-2.6, -1.4, 0.9, 0.5), (1.9, 2.2, 0.7, 0.6), (3.3, -2.6, 0.5, 0.4), (-0.4, 0.6, 0.6, 0.35)):
        for row in range(int(d / 0.075)):
            y = cy - d / 2.0 + row * 0.075
            offset = 0.12 if row % 2 else 0.0
            x = cx - w / 2.0 - offset
            while x < cx + w / 2.0:
                if rng.random() < 0.85:
                    z = vault_z(x + 0.11) - 0.012
                    mb.box((0.23, 0.065, 0.02), (x + 0.115, y, z), rng.choice((BRICK, BRICK_DARK)), rotation=(0.0, math.degrees(math.atan2(-x, VAULT_R)), 0.0), bevel=0.003, jitter=0.08)
                x += 0.25
    vault = mb.finish("boveda", tb.material("sala", WHITEWASH), root)
    tb.stain(vault, PLASTER_STAIN, amount=0.6, scale=0.9, coverage=0.45, seed=302, stretch_z=0.2)
    return [vault]


def _wall_tiles(root: bpy.types.Object, rng: random.Random) -> list:
    """Zócalo de azulejos de metro (30 × 15 cm, a matacán) en los cuatro muros,
    con una fila crema arriba y alguno caído. Una malla por muro."""
    tile_w, tile_h, gap = 0.3, 0.15, 0.006
    rows = int(TILE_BAND / tile_h)
    walls = (
        # (nombre, largo, cómo colocar (u, v) -> (centro, giro), huecos en u)
        ("frente", 2.0 * HALF_W, lambda u, v: ((u, FRONT + 0.006, v), 0), [SHUTTER_X, DOOR_X]),
        ("fondo", 2.0 * HALF_W, lambda u, v: ((u, BACK - 0.006, v), 0), []),
        ("izquierda", BACK - FRONT, lambda u, v: ((-HALF_W + 0.006, u + (FRONT + BACK) / 2.0, v), 90), []),
        ("derecha", BACK - FRONT, lambda u, v: ((HALF_W - 0.006, u + (FRONT + BACK) / 2.0, v), 90), []),
    )
    objects = []
    for name, length, place, gaps in walls:
        mb = tb.MeshBuilder(seed=400 + len(objects))
        for row in range(rows):
            offset = (tile_w / 2.0) if row % 2 else 0.0
            u = -length / 2.0 - offset
            while u < length / 2.0:
                start, end = max(u, -length / 2.0), min(u + tile_w, length / 2.0)
                u += tile_w
                middle = (start + end) / 2.0
                if end - start < 0.04 or rng.random() < 0.025:
                    continue
                if any(g0 - 0.02 < middle < g1 + 0.02 for g0, g1 in gaps):
                    continue
                color = TILE_CREAM if row == rows - 1 else TILE
                center, turn = place(middle, row * tile_h + tile_h / 2.0)
                size = (end - start - gap, 0.012, tile_h - gap) if turn == 0 else (0.012, end - start - gap, tile_h - gap)
                mb.box(size, center, color, rotation=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.0), bevel=0.003, jitter=0.07)
        objects.append(mb.finish(f"azulejos_{name}", tb.material("sala", PLASTER), root))
    # La moldura de madera sobre el zócalo, que da la vuelta a la sala.
    mb = tb.MeshBuilder(seed=450)
    z = TILE_BAND + 0.03
    mb.box((2.0 * HALF_W, 0.03, 0.06), (0.0, BACK - 0.015, z), TRIM, bevel=0.008, jitter=0.05)
    mb.box((0.03, BACK - FRONT, 0.06), (-HALF_W + 0.015, (FRONT + BACK) / 2.0, z), TRIM, bevel=0.008, jitter=0.05)
    mb.box((0.03, BACK - FRONT, 0.06), (HALF_W - 0.015, (FRONT + BACK) / 2.0, z), TRIM, bevel=0.008, jitter=0.05)
    for x0, x1 in ((-HALF_W, SHUTTER_X[0]), (SHUTTER_X[1], DOOR_X[0]), (DOOR_X[1], HALF_W)):
        mb.box((x1 - x0, 0.03, 0.06), ((x0 + x1) / 2.0, FRONT + 0.015, z), TRIM, bevel=0.008, jitter=0.05)
    objects.append(mb.finish("moldura", tb.material("madera", TRIM), root))
    return objects


def _partition(root: bpy.types.Object, rng: random.Random) -> list:
    """El tabique de tablas que levantó el antiguo dueño, con el paso tapado por
    una manta militar colgada de una barra."""
    mb = tb.MeshBuilder(seed=501)
    plank = 0.165
    x = -HALF_W
    while x < PARTITION_END - 0.01:
        x1 = min(x + plank, PARTITION_END)
        middle = (x + x1) / 2.0
        top = vault_z(middle) - 0.01
        bottom = DOORWAY_H if DOORWAY[0] < middle < DOORWAY[1] else 0.0
        color = rng.choice((PLANK, PLANK_DARK, WOOD, "#6F5038"))
        mb.box((x1 - x - 0.012, 0.025, top - bottom), (middle, PARTITION_Y, (top + bottom) / 2.0), color, rotation=(0.0, rng.uniform(-0.3, 0.3), 0.0), bevel=0.004, jitter=0.08)
        x = x1
    # Los travesaños, por el lado de la sala, y el marco del paso.
    for z in (0.35, 1.25, 2.15):
        mb.box((PARTITION_END + HALF_W, 0.05, 0.08), ((PARTITION_END - HALF_W) / 2.0, PARTITION_Y - 0.04, z), WOOD_DARK, bevel=0.006)
    for x in DOORWAY:
        mb.box((0.07, 0.07, DOORWAY_H), (x, PARTITION_Y - 0.035, DOORWAY_H / 2.0), WOOD_DARK, bevel=0.008)
    mb.box((PARTITION_END - (-HALF_W) + 0.0, 0.07, 0.07), ((PARTITION_END - HALF_W) / 2.0, PARTITION_Y - 0.035, DOORWAY_H + 0.035), WOOD_DARK, bevel=0.008)
    # El poste del final del tabique.
    mb.box((0.08, 0.08, vault_z(PARTITION_END)), (PARTITION_END, PARTITION_Y, vault_z(PARTITION_END) / 2.0), WOOD_DARK, bevel=0.01)
    wood = mb.finish("tabique", tb.material("madera", PLANK), root)
    # La manta: un paño con pliegues colgado de la barra, recogido hacia un lado.
    cloth = tb.MeshBuilder(seed=502)
    cloth.bar((DOORWAY[0] - 0.05, PARTITION_Y - 0.09, DOORWAY_H - 0.06), (DOORWAY[1] + 0.05, PARTITION_Y - 0.09, DOORWAY_H - 0.06), 0.012, IRON, 8)
    folds = 18
    width = (DOORWAY[1] - DOORWAY[0]) * 0.72
    for k in range(folds):
        u0, u1 = k / folds, (k + 1) / folds
        x0 = DOORWAY[0] + 0.04 + width * u0
        x1 = DOORWAY[0] + 0.04 + width * u1
        d0 = 0.035 * math.sin(u0 * math.pi * 7.0)
        d1 = 0.035 * math.sin(u1 * math.pi * 7.0)
        top, bottom = DOORWAY_H - 0.07, 0.08
        y = PARTITION_Y - 0.1
        color = BLANKET if 0.15 < u0 < 0.25 else (BLANKET_DARK if k % 5 == 0 else BLANKET)
        cloth.quad([(x0, y + d0, bottom), (x1, y + d1, bottom), (x1, y + d1, top), (x0, y + d0, top)], color, cuts=3, jitter=0.04)
        cloth.quad([(x1, y + d1 + 0.004, bottom), (x0, y + d0 + 0.004, bottom), (x0, y + d0 + 0.004, top), (x1, y + d1 + 0.004, top)], BLANKET_DARK, cuts=1)
    # Las dos franjas de la manta.
    for z in (0.32, 0.42):
        cloth.box((width, 0.012, 0.03), (DOORWAY[0] + 0.04 + width / 2.0, PARTITION_Y - 0.13, z), "#7A6E4E")
    blanket = cloth.finish("manta", tb.material("tela", BLANKET), root)
    return [wood, blanket]


def _services(root: bpy.types.Object, rng: random.Random) -> list:
    """Tuberías y cables por la bóveda, la rejilla de ventilación del fondo (por
    donde sale el tubo de la estufa) y las abrazaderas."""
    mb = tb.MeshBuilder(seed=601)
    for x, z, radius, color in ((3.95, 2.52, 0.055, PIPE_GREEN), (4.18, 2.42, 0.04, PIPE_RUST), (-4.2, 2.48, 0.03, PIPE_RUST)):
        mb.bar((x, FRONT, z), (x, BACK, z), radius, color, 12)
        for y in (-2.6, -0.8, 1.0, 2.8):
            mb.box((0.03, 0.05, 0.16), (x, y, z + 0.08), RUST, bevel=0.004)
    # Un mazo de cables en su bandeja, por la clave.
    mb.box((0.18, BACK - FRONT, 0.02), (0.9, (FRONT + BACK) / 2.0, vault_z(0.9) - 0.12), IRON, bevel=0.003)
    for k in range(4):
        mb.bar((0.84 + k * 0.04, FRONT, vault_z(0.9) - 0.1), (0.84 + k * 0.04, BACK, vault_z(0.9) - 0.1), 0.009, "#2A2725", 6)
    # La rejilla del fondo (sobre la estufa) y la del muro del pasillo.
    for x, y, facing in ((-1.4, BACK - 0.02, 1.0), (-3.2, FRONT + 0.02, -1.0)):
        mb.box((0.5, 0.04, 0.32), (x, y, 2.35), IRON, bevel=0.006)
        for k in range(6):
            mb.box((0.44, 0.02, 0.025), (x, y - facing * 0.02, 2.22 + k * 0.05), "#2A2826", rotation=(30.0 * facing, 0.0, 0.0))
    services = mb.finish("instalaciones", tb.material("metal", PIPE_GREEN), root)
    tb.stain(services, RUST, amount=0.7, scale=2.0, coverage=0.35, seed=602)
    return [services]


def build_room() -> bpy.types.Object:
    rng = random.Random(13)
    root = tb.empty("consigna_sala-estatico")
    parts = []
    parts += _floor(root, rng)
    parts += _walls(root, rng)
    parts += _vault(root, rng)
    parts += _wall_tiles(root, rng)
    parts += _partition(root, rng)
    parts += _services(root, rng)
    # Colisiones: suelo, muros (el del pasillo, partido por los huecos), techo y tabique.
    middle_y = (FRONT + BACK) / 2.0
    tb.collision_box("suelo", (2.0 * HALF_W, BACK - FRONT, 0.1), (0.0, middle_y, -0.05), root)
    tb.collision_box("fondo", (2.0 * HALF_W, WALL, CROWN), (0.0, BACK + WALL / 2.0, CROWN / 2.0), root)
    tb.collision_box("izquierda", (WALL, BACK - FRONT, CROWN), (-HALF_W - WALL / 2.0, middle_y, CROWN / 2.0), root)
    tb.collision_box("derecha", (WALL, BACK - FRONT, CROWN), (HALF_W + WALL / 2.0, middle_y, CROWN / 2.0), root)
    for name, x0, x1 in (("frente_izq", -HALF_W, SHUTTER_X[0]), ("frente_medio", SHUTTER_X[1], DOOR_X[0]), ("frente_der", DOOR_X[1], HALF_W)):
        tb.collision_box(name, (x1 - x0, WALL, CROWN), ((x0 + x1) / 2.0, FRONT - WALL / 2.0, CROWN / 2.0), root)
    tb.collision_box("dintel", (SHUTTER_X[1] - SHUTTER_X[0], WALL, CROWN - SHUTTER_H), (0.0, FRONT - WALL / 2.0, (CROWN + SHUTTER_H) / 2.0), root)
    tb.collision_box("techo", (2.0 * HALF_W, BACK - FRONT, 0.1), (0.0, middle_y, CROWN + 0.05), root)
    for name, x0, x1 in (("tabique_izq", -HALF_W, DOORWAY[0]), ("tabique_der", DOORWAY[1], PARTITION_END)):
        tb.collision_box(name, (x1 - x0, 0.08, SPRING), ((x0 + x1) / 2.0, PARTITION_Y, SPRING / 2.0), root)
    tb.paint({part: None for part in parts}, samples=10, ao=0.5, ao_distance=0.4, ground_z=None, seed=13)
    return root


# --------------------------------------------------------------------------
# La persiana, la puerta, el mostrador y las baldas
# --------------------------------------------------------------------------

SLATS = 23
SLAT_H = SHUTTER_H / SLATS


def build_shutter() -> bpy.types.Object:
    """La persiana de la ventanilla, por fuera (el origen, en el centro del hueco a
    ras de suelo y del muro; la persiana sale hacia -Y, al pasillo).

    "marco" es el cajón y las guías; "cortina" lleva una lama por nodo, de arriba
    abajo, y una colisión que tapa el hueco: Godot sube las lamas al cajón una a
    una y sube la colisión con ellas."""
    rng = random.Random(701)
    root = tb.empty("consigna_persiana")
    width = SHUTTER_X[1] - SHUTTER_X[0]
    frame_root = tb.empty("marco-estatico", root)
    mb = tb.MeshBuilder(seed=702)
    # El cajón, de chapa remachada.
    mb.box((width + 0.3, 0.3, 0.34), (0.0, -0.17, SHUTTER_H + 0.17), SHUTTER, bevel=0.01, cuts=2, jitter=0.04)
    for k in range(9):
        mb.cylinder(0.008, 0.006, (-1.6 + k * 0.4, -0.322, SHUTTER_H + 0.04), IRON, rotation=(90.0, 0.0, 0.0), segments=8)
    # Las guías, en U.
    for x in (SHUTTER_X[0] - 0.045, SHUTTER_X[1] + 0.045):
        mb.box((0.09, 0.012, SHUTTER_H), (x, -0.09, SHUTTER_H / 2.0), SHUTTER, bevel=0.003)
        mb.box((0.012, 0.09, SHUTTER_H), (x - 0.04, -0.045, SHUTTER_H / 2.0), SHUTTER, bevel=0.003)
        mb.box((0.012, 0.09, SHUTTER_H), (x + 0.04, -0.045, SHUTTER_H / 2.0), SHUTTER, bevel=0.003)
    frame = mb.finish("cajon", tb.material("metal", SHUTTER), frame_root)
    tb.stain(frame, RUST, amount=0.8, scale=2.2, coverage=0.4, seed=703, stretch_z=0.5)
    tb.collision_box("cajon", (width + 0.3, 0.3, 0.34), (0.0, -0.17, SHUTTER_H + 0.17), frame_root)
    curtain_root = tb.empty("cortina-estatico", root)
    slats = []
    for k in range(SLATS):
        mb = tb.MeshBuilder(seed=710 + k)
        top = SHUTTER_H - k * SLAT_H
        z = top - SLAT_H / 2.0
        if k == SLATS - 1:
            # La barra de abajo, más gruesa, con su asa y su cerrojo.
            mb.box((width, 0.05, SLAT_H - 0.006), (0.0, -0.05, z), IRON, bevel=0.006)
            mb.bar((-0.25, -0.1, z), (0.25, -0.1, z), 0.012, IRON, 8)
            for x in (-0.25, 0.25):
                mb.box((0.024, 0.06, 0.024), (x, -0.075, z), IRON, bevel=0.003)
            mb.box((0.12, 0.03, 0.07), (0.9, -0.085, z), "#5C4A2E", bevel=0.005)
        else:
            paint = SHUTTER_PAINT if rng.random() < 0.8 else SHUTTER
            mb.box((width, 0.03, SLAT_H - 0.012), (0.0, -0.05, z), paint, bevel=0.008, jitter=0.05)
            mb.box((width, 0.012, 0.012), (0.0, -0.067, z + SLAT_H / 2.0 - 0.012), IRON)
        slat = mb.finish(f"lama_{k:02d}", tb.material("metal", SHUTTER), curtain_root)
        tb.stain(slat, RUST, amount=0.65, scale=2.5, coverage=0.3, seed=720 + k, stretch_z=0.6)
        slats.append(slat)
    tb.collision_box("cortina", (width, 0.06, SHUTTER_H), (0.0, -0.05, SHUTTER_H / 2.0), curtain_root)
    tb.paint({frame: None, **{slat: None for slat in slats}}, samples=10, ao=0.35, ground_z=0.0, seed=704)
    return root


def build_door() -> bpy.types.Object:
    """La puerta de chapa: el marco y la hoja, con el origen en el eje de las
    bisagras (lado de x = 4,3, a ras de suelo). Cerrada, la hoja va hacia -X; se
    abre hacia dentro (hacia +Y) girando en Z."""
    root = tb.empty("consigna_puerta")
    width = DOOR_X[1] - DOOR_X[0]
    frame_root = tb.empty("marco-estatico", root)
    mb = tb.MeshBuilder(seed=801)
    for x in (-width - 0.03, 0.03):
        mb.box((0.06, 0.18, DOOR_H + 0.03), (x, 0.0, (DOOR_H + 0.03) / 2.0), IRON, bevel=0.005)
    mb.box((width + 0.12, 0.18, 0.06), (-width / 2.0, 0.0, DOOR_H + 0.03), IRON, bevel=0.005)
    frame = mb.finish("marco", tb.material("metal", IRON), frame_root)
    leaf_root = tb.empty("hoja-estatico", root)
    mb = tb.MeshBuilder(seed=802)
    mb.box((width - 0.02, 0.045, DOOR_H - 0.02), (-width / 2.0, 0.0, DOOR_H / 2.0), DOOR_GREEN, bevel=0.006, cuts=3, jitter=0.03)
    # Los refuerzos en Z y el marco de la hoja.
    for z in (0.35, DOOR_H - 0.35):
        mb.box((width - 0.1, 0.02, 0.06), (-width / 2.0, -0.032, z), DOOR_GREEN, bevel=0.004)
    angle = math.degrees(math.atan2(DOOR_H - 0.7, width - 0.1))
    mb.box((math.hypot(DOOR_H - 0.7, width - 0.1), 0.02, 0.06), (-width / 2.0, -0.032, DOOR_H / 2.0), DOOR_GREEN, rotation=(0.0, -angle, 0.0), bevel=0.004)
    # El pomo, la mirilla y la placa "PRIVADO" que ya nadie lee.
    for side in (-1.0, 1.0):
        mb.cylinder(0.02, 0.05, (-width + 0.09, side * 0.05, 1.0), IRON, rotation=(90.0, 0.0, 0.0), segments=10)
        mb.box((0.03, 0.03, 0.12), (-width + 0.09, side * 0.085, 1.0), IRON, bevel=0.006)
    mb.cylinder(0.012, 0.06, (-width / 2.0, 0.0, 1.55), "#1E1C1A", rotation=(90.0, 0.0, 0.0), segments=10)
    mb.box((0.28, 0.008, 0.08), (-width / 2.0, -0.026, 1.72), ENAMEL_WHITE, bevel=0.003)
    mb.box((0.22, 0.004, 0.02), (-width / 2.0, -0.031, 1.72), "#7A2B25")
    for z in (0.3, DOOR_H - 0.3):
        mb.cylinder(0.018, 0.1, (0.0, 0.0, z), IRON, segments=10)
    leaf = mb.finish("hoja", tb.material("metal", DOOR_GREEN), leaf_root)
    tb.stain(leaf, RUST, amount=0.7, scale=2.0, coverage=0.35, seed=803, stretch_z=0.5)
    tb.collision_box("hoja", (width - 0.02, 0.05, DOOR_H - 0.02), (-width / 2.0, 0.0, DOOR_H / 2.0), leaf_root)
    tb.paint({frame: None, leaf: None}, samples=12, ao=0.4, ground_z=0.0, seed=804)
    return root


def build_counter() -> bpy.types.Object:
    """El mostrador de la ventanilla: 3 m de largo y 0,8 de fondo, con el tablero a
    0,95 m. El origen, en el centro de su cara del pasillo a ras de suelo; el
    mostrador entra en la sala hacia +Y. Por dentro, dos baldas abiertas."""
    rng = random.Random(901)
    root = tb.empty("consigna_mostrador-estatico")
    width, depth, height = SHUTTER_X[1] - SHUTTER_X[0] - 0.02, 0.8, 0.95
    mb = tb.MeshBuilder(seed=902)
    # El tablero: tablones barnizados, gastados donde se apoyan los codos.
    boards = 5
    for k in range(boards):
        y = 0.02 + (depth + 0.03) * (k + 0.5) / boards
        color = VARNISH if k not in (0, 1) else "#94643F"
        mb.box((width + 0.06, (depth + 0.03) / boards - 0.006, 0.045), (0.0, y, height - 0.0225), color, rotation=(rng.uniform(-0.3, 0.3), 0.0, 0.0), bevel=0.006, jitter=0.06)
    # El frente del pasillo: friso de tablas machihembradas con la pintura gastada.
    x = -width / 2.0
    while x < width / 2.0 - 0.01:
        x1 = min(x + 0.12, width / 2.0)
        mb.box((x1 - x - 0.006, 0.025, height - 0.08), ((x + x1) / 2.0, 0.035, (height - 0.08) / 2.0 + 0.03), rng.choice((ENAMEL, "#35584D", "#2B473F")), bevel=0.004, jitter=0.07)
        x = x1
    mb.box((width + 0.04, 0.04, 0.06), (0.0, 0.03, 0.03), WOOD_DARK, bevel=0.006)
    # La placa esmaltada de la vieja ventanilla.
    mb.box((0.36, 0.01, 0.16), (-0.9, 0.018, 0.68), ENAMEL_WHITE, bevel=0.004)
    mb.box((0.3, 0.006, 0.1), (-0.9, 0.012, 0.68), "#30475A")
    # Los costados y las baldas de dentro.
    for side in (-1.0, 1.0):
        mb.box((0.03, depth, height - 0.045), (side * (width / 2.0 - 0.015), depth / 2.0 + 0.02, (height - 0.045) / 2.0), WOOD_DARK, bevel=0.005)
    for z in (0.12, 0.5):
        mb.box((width - 0.06, depth - 0.1, 0.025), (0.0, depth / 2.0, z), WOOD, bevel=0.004, jitter=0.05)
    for x in (-0.5, 0.5):
        mb.box((0.025, depth - 0.1, height - 0.2), (x, depth / 2.0, (height - 0.2) / 2.0 + 0.05), WOOD_DARK, bevel=0.004)
    counter = mb.finish("mostrador", tb.material("madera", VARNISH), root)
    tb.stain(counter, "#3A2A20", amount=0.5, scale=1.4, coverage=0.35, seed=903)
    tb.collision_box("tablero", (width + 0.06, depth + 0.03, 0.05), (0.0, (depth + 0.03) / 2.0 + 0.005, height - 0.025), root)
    tb.collision_box("frente", (width, 0.05, height - 0.05), (0.0, 0.035, (height - 0.05) / 2.0), root)
    for index, z in enumerate((0.12, 0.5)):
        tb.collision_box(f"balda_{index}", (width - 0.06, depth - 0.1, 0.03), (0.0, depth / 2.0, z), root)
    tb.paint({counter: None}, samples=14, ao=0.45, ground_z=0.0, seed=904)
    return root


def build_racks() -> bpy.types.Object:
    """Las baldas de la consigna: un armazón de angular con cuatro pisos de tablas
    y cuatro compartimentos por piso, cada uno con su chapa numerada. 2 m de largo,
    0,55 de fondo y 2,2 de alto; el origen, en el centro a ras de suelo."""
    rng = random.Random(1001)
    root = tb.empty("consigna_baldas-estatico")
    width, depth, height = 2.0, 0.55, 2.2
    levels = (0.1, 0.62, 1.14, 1.66)
    mb = tb.MeshBuilder(seed=1002)
    for x in (-width / 2.0, -width / 4.0, 0.0, width / 4.0, width / 2.0):
        for y in (-depth / 2.0 + 0.02, depth / 2.0 - 0.02):
            mb.box((0.04, 0.04, height), (x, y, height / 2.0), METAL_GREEN, bevel=0.003)
    for z in (*levels, height - 0.02):
        for y in (-depth / 2.0 + 0.02, depth / 2.0 - 0.02):
            mb.box((width, 0.04, 0.035), (0.0, y, z - 0.02), METAL_GREEN, bevel=0.003)
    frame = mb.finish("armazon", tb.material("metal", METAL_GREEN), root)
    tb.stain(frame, RUST, amount=0.7, scale=2.4, coverage=0.3, seed=1003)
    wood = tb.MeshBuilder(seed=1004)
    for z in levels:
        for k in range(4):
            y = -depth / 2.0 + (k + 0.5) * depth / 4.0
            wood.box((width - 0.02, depth / 4.0 - 0.008, 0.022), (0.0, y, z + 0.011), rng.choice((WOOD, WOOD_LIGHT, "#7E5536")), rotation=(0.0, rng.uniform(-0.4, 0.4), 0.0), bevel=0.004, jitter=0.08)
    # Las chapas numeradas, por delante de cada compartimento.
    for z in levels:
        for bay in range(4):
            x = -width / 2.0 + (bay + 0.5) * width / 4.0
            wood.box((0.11, 0.006, 0.055), (x, -depth / 2.0 - 0.003, z - 0.045), ENAMEL_WHITE, rotation=(0.0, rng.uniform(-3.0, 3.0), 0.0), bevel=0.002)
            wood.box((0.07, 0.004, 0.025), (x, -depth / 2.0 - 0.007, z - 0.045), "#2B3A4A")
    boards = wood.finish("baldas", tb.material("madera", WOOD), root)
    for index, z in enumerate(levels):
        tb.collision_box(f"balda_{index}", (width, depth, 0.03), (0.0, 0.0, z + 0.008), root)
    for index, x in enumerate((-width / 2.0, width / 2.0)):
        tb.collision_box(f"costado_{index}", (0.04, depth, height), (x, 0.0, height / 2.0), root)
    tb.paint({frame: None, boards: None}, samples=14, ao=0.45, ground_z=0.0, seed=1005)
    return root


def models() -> dict:
    return {
        "consigna_sala": build_room,
        "consigna_persiana": build_shutter,
        "consigna_puerta": build_door,
        "consigna_mostrador": build_counter,
        "consigna_baldas": build_racks,
    }
