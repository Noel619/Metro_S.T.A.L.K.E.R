"""La mochila del stalker (F3-03): la que se llena en el depósito antes de subir.

Está tumbada boca arriba, con la boca hacia +Z: lo de arriba de la mochila (el
asa y la bisagra de la tapa) hacia +Y y el fondo hacia -Y, de cara a quien la
mira. Por dentro, el fondo está cosido en una cuadrícula de 6 × 5 compartimentos
de cincha (CELL de lado): es la cuadrícula de la mochila del juego
(scripts/depot/backpack_grid.gd). La ``tapa`` es un nodo propio con el origen en
la bisagra: en reposo está cerrada y se abre girando ``rotation.x`` hasta -202°
(pasa por encima y cae hacia atrás, hasta el suelo). Las correas de los hombros
asoman por detrás, tiradas en el suelo.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

import botin_bpy as bb
import tumansk_bpy as tb

CANVAS = "#646650"
CANVAS_DARK = "#50563F"
CANVAS_INSIDE = "#5A5444"
FLOOR = "#7E7660"
WEBBING = "#4A4636"
LEATHER = "#3E2C21"
LEATHER_WORN = "#5F4532"
STEEL = "#7D817E"
THREAD = "#2E2A22"
PATCH = "#7A6A4E"
MUD = "#4E4233"
DUST = "#8B8576"

# La cuadrícula del juego: 6 × 5 casillas de CELL metros (BackpackGrid.SIZE).
CELL = 0.075
COLUMNS, ROWS = 6, 5
INNER_W, INNER_D = COLUMNS * CELL, ROWS * CELL
WALL = 0.06
OUTER_W, OUTER_D = INNER_W + 2.0 * WALL, INNER_D + 2.0 * WALL
HEIGHT = 0.12
FLOOR_Z = 0.02
LID = 0.02


def _ring_path(width: float, depth: float, radius: float, z: float) -> list[Vector]:
    points = [Vector((x, y, z)) for x, y in bb.rounded_rect(width, depth, radius, steps=4)]
    points.append(points[0])
    return points


def build_backpack() -> bpy.types.Object:
    """La mochila de lona, tumbada y cerrada (ver el docstring del módulo)."""
    root = tb.empty("mochila-fisico")
    body = tb.MeshBuilder(seed=1101)
    # El fondo (la espalda de la mochila, contra el suelo) y las paredes acolchadas.
    body.prism(bb.rounded_rect(OUTER_W, OUTER_D, 0.07, steps=5), FLOOR_Z, (0.0, 0.0, FLOOR_Z / 2.0), CANVAS, bevel=0.008, segments=2)
    middle = _ring_path(OUTER_W - WALL, OUTER_D - WALL, 0.045, HEIGHT / 2.0)
    bb.strap(body, middle, HEIGHT, WALL, CANVAS, center=(0.0, 0.0, HEIGHT / 2.0))
    # El ribete cosido de la boca y del fondo.
    for width, depth, radius, z in ((OUTER_W, OUTER_D, 0.072, HEIGHT), (INNER_W, INNER_D, 0.018, HEIGHT), (OUTER_W, OUTER_D, 0.072, 0.012)):
        body.tube(_ring_path(width, depth, radius, z), 0.0085, CANVAS_DARK, segments=6, caps=False)
    # Un bolsillo delante, con su tapeta y la hebilla, y uno a cada lado.
    front = -OUTER_D / 2.0
    body.box((0.26, 0.05, 0.1), (0.0, front - 0.02, 0.062), CANVAS_DARK, bevel=0.018, segments=2, cuts=3)
    body.box((0.27, 0.03, 0.035), (0.0, front - 0.035, 0.108), CANVAS, rotation=(-12.0, 0.0, 0.0), bevel=0.01, segments=2)
    body.box((0.024, 0.006, 0.04), (0.0, front - 0.052, 0.082), LEATHER, bevel=0.002)
    body.box((0.026, 0.004, 0.018), (0.0, front - 0.055, 0.068), STEEL, bevel=0.0015)
    for side in (-1.0, 1.0):
        x = side * (OUTER_W / 2.0 + 0.018)
        body.box((0.05, 0.2, 0.1), (x, -0.03, 0.06), CANVAS_DARK, bevel=0.018, segments=2, cuts=3)
        body.box((0.006, 0.18, 0.004), (x + side * 0.026, -0.03, 0.085), THREAD)
    # Un remiendo en la pared de la izquierda, con sus puntadas.
    body.box((0.004, 0.08, 0.06), (-OUTER_W / 2.0 - 0.0005, 0.13, 0.08), PATCH)
    for k in range(9):
        body.box((0.0045, 0.002, 0.007), (-OUTER_W / 2.0 - 0.002, 0.092 + k * 0.0095, 0.111), THREAD)
    # El asa de arriba.
    top_edge = OUTER_D / 2.0
    body.tube(tb.smooth_path(((-0.06, top_edge - 0.01, HEIGHT - 0.02), (-0.05, top_edge + 0.035, HEIGHT - 0.01), (0.05, top_edge + 0.035, HEIGHT - 0.01), (0.06, top_edge - 0.01, HEIGHT - 0.02)), 4), 0.008, LEATHER, segments=8)
    # El cuello fruncido de arriba, con su cordón y el pasador.
    throat = [Vector((x, top_edge - 0.004, HEIGHT - 0.035 + 0.012 * math.cos(x * 40.0))) for x in [-0.2 + 0.4 * k / 16.0 for k in range(17)]]
    body.tube(throat, 0.018, CANVAS_DARK, segments=8)
    body.tube(tb.smooth_path(((0.03, top_edge + 0.01, HEIGHT - 0.02), (0.06, top_edge + 0.05, HEIGHT - 0.03), (0.09, top_edge + 0.07, 0.03), (0.13, top_edge + 0.06, 0.004)), 4), 0.0028, THREAD, segments=5)
    body.box((0.016, 0.022, 0.012), (0.06, top_edge + 0.05, HEIGHT - 0.03), LEATHER, rotation=(0.0, 30.0, 40.0), bevel=0.003)
    # Las correas de los hombros: salen de debajo, junto a las esquinas de arriba, y
    # se quedan tiradas en el suelo a los lados.
    for side in (-1.0, 1.0):
        x = side * (OUTER_W / 2.0 - 0.06)
        path = [
            Vector((x, top_edge - 0.08, 0.004)),
            Vector((x + side * 0.08, top_edge - 0.04, 0.006)),
            Vector((x + side * 0.15, top_edge - 0.14, 0.006)),
            Vector((x + side * 0.15, -0.08, 0.006)),
            Vector((x + side * 0.1, -0.2, 0.006)),
            Vector((x + side * 0.04, -0.24, 0.005)),
        ]
        bb.strap(body, tb.smooth_path(path, 4), 0.055, 0.014, CANVAS_DARK, center=(path[2].x, path[2].y, -1.0))
        bb.strap(body, tb.smooth_path([p + Vector((0.0, 0.0, 0.007)) for p in path[2:5]], 3), 0.02, 0.004, LEATHER, center=(path[3].x, path[3].y, -1.0))
        body.box((0.034, 0.014, 0.008), path[4] + Vector((0.0, 0.0, 0.01)), STEEL, rotation=(0.0, 0.0, side * 30.0), bevel=0.002)
    bag = body.finish("mochila", tb.material("lona", CANVAS), root)
    tb.apply_bulge(bag, (0.0, 0.0, HEIGHT / 2.0), (OUTER_W / 2.0, OUTER_D / 2.0, HEIGHT / 2.0), 0.016)
    tb.wobble(bag, amount=0.006, scale=9.0, seed=1102)
    tb.stain(bag, MUD, amount=0.6, scale=16.0, coverage=0.3, seed=1103, stretch_z=0.6)
    tb.stain(bag, DUST, amount=0.4, scale=40.0, coverage=0.25, seed=1104)

    # Por dentro: el fondo de lona clara cosido en compartimentos de cincha.
    inside = tb.MeshBuilder(seed=1105)
    inside.box((INNER_W + 0.004, INNER_D + 0.004, 0.004), (0.0, 0.0, FLOOR_Z + 0.002), FLOOR, cuts=4)
    lift = FLOOR_Z + 0.0055
    for k in range(1, COLUMNS):
        x = -INNER_W / 2.0 + k * CELL
        inside.box((0.007, INNER_D, 0.004), (x, 0.0, lift), WEBBING, bevel=0.001)
    for k in range(1, ROWS):
        y = -INNER_D / 2.0 + k * CELL
        inside.box((INNER_W, 0.007, 0.004), (0.0, y, lift), WEBBING, bevel=0.001)
    # La cara de dentro de las paredes, más oscura.
    inner_ring = _ring_path(INNER_W + 0.002, INNER_D + 0.002, 0.012, (HEIGHT + FLOOR_Z) / 2.0)
    faces = bb.strap(inside, inner_ring, HEIGHT - FLOOR_Z - 0.004, 0.002, CANVAS_INSIDE, center=(0.0, 0.0, (HEIGHT + FLOOR_Z) / 2.0))
    inside.flip(faces)
    lining = inside.finish("forro", tb.material("lona", FLOOR), root)
    tb.stain(lining, "#6A624E", amount=0.45, scale=25.0, coverage=0.3, seed=1106)

    # La tapa, cerrada, con el origen en la bisagra: sus dos correas bajan por delante.
    lid = tb.MeshBuilder(seed=1107)
    hinge = Vector((0.0, OUTER_D / 2.0 - 0.012, HEIGHT))
    dome_a, dome_b, dome_h = OUTER_W / 2.0 + 0.012, OUTER_D / 2.0 + 0.01, 0.045

    def on_dome(x: float, y: float, lift: float = 0.0) -> Vector:
        inside = max(0.0, 1.0 - (x / dome_a) ** 2 - ((y + 0.004) / dome_b) ** 2)
        return Vector((x, y, HEIGHT - 0.012 + dome_h * math.sqrt(inside) + lift))

    lid.sphere(1.0, (0.0, -0.004, HEIGHT - 0.012), CANVAS, segments=32, scale=(dome_a, dome_b, dome_h))
    lid.tube([on_dome(dome_a * 0.985 * math.cos(2.0 * math.pi * k / 40.0), (dome_b * 0.985) * math.sin(2.0 * math.pi * k / 40.0) - 0.004, 0.002) for k in range(41)], 0.0075, CANVAS_DARK, segments=6, caps=False)
    for side in (-1.0, 1.0):
        x = side * 0.15
        strap_path = [on_dome(x, y, 0.003) for y in (0.12, 0.04, -0.06, -0.14, -0.19)]
        strap_path += [Vector((x, front - 0.008, HEIGHT - 0.006)), Vector((x, front - 0.014, HEIGHT - 0.05))]
        bb.strap(lid, tb.smooth_path(strap_path, 3), 0.026, 0.004, LEATHER, center=(x, 0.0, HEIGHT - 0.08))
        buckle = Vector((x, front - 0.018, HEIGHT - 0.058))
        for dx in (-0.017, 0.017):
            lid.bar(buckle + Vector((dx, 0.0, -0.012)), buckle + Vector((dx, 0.0, 0.012)), 0.0016, STEEL, 6)
        for dz in (-0.012, 0.012):
            lid.bar(buckle + Vector((-0.017, 0.0, dz)), buckle + Vector((0.017, 0.0, dz)), 0.0016, STEEL, 6)
        # El otro cabo de la correa, cosido a la pared de delante.
        lid.box((0.024, 0.004, 0.05), (x, front - 0.006, 0.06), LEATHER_WORN, bevel=0.0015)
    lid_obj = lid.finish("tapa", tb.material("lona", CANVAS), root)
    tb.wobble(lid_obj, amount=0.003, scale=10.0, seed=1108)
    tb.stain(lid_obj, MUD, amount=0.5, scale=14.0, coverage=0.25, seed=1109)
    tb.stain(lid_obj, DUST, amount=0.45, scale=35.0, coverage=0.3, seed=1110)
    tb.set_origin(lid_obj, hinge)

    tb.collision_box("mochila", (OUTER_W, OUTER_D, HEIGHT), (0.0, 0.0, HEIGHT / 2.0), root)
    tb.paint({bag: None, lining: None, lid_obj: None}, samples=14, ao=0.45, ao_distance=0.08, seed=1101)
    return root


def models() -> dict:
    return {"mochila": build_backpack}


# Se usa al montar la mochila en Godot (scripts/depot/backpack.gd) con estas mismas medidas.
assert math.isclose(INNER_W, 0.45) and math.isclose(INNER_D, 0.375)
