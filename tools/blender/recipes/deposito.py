"""El depósito: la sala y su mobiliario.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba.
(En Godot, la Y de Blender pasa a ser -Z: el fondo de la sala queda en -Z.)

La sala mide 4,4 × 3,6 m y 2,9 m de alto. Es un antiguo cuarto técnico de la
estación: zócalo de azulejos de metro, yeso por encima, suelo de baldosas y una
persiana metálica que da al pasillo de la estación.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

# Paleta del depósito (docs/ESTILO.md).
GROUT = "#3B3631"
FLOOR_A = "#8E857A"
FLOOR_B = "#7C746A"
FLOOR_CHIPPED = "#5E5850"
TILE = "#2F6F73"
TILE_CREAM = "#D3C8AC"
PLASTER = "#CDBF9F"
PLASTER_STAIN = "#9C8F72"
TRIM = "#5A3B2A"
CONCRETE = "#8C877D"
PIPE_GREEN = "#4F5E52"
PIPE_RUST = "#6B4A3A"
RUST = "#8E4A2F"
METAL_GREEN = "#55615A"
WOOD = "#8A5A3B"
WOOD_DARK = "#6E4A32"
SHUTTER = "#5F6E78"
ENAMEL = "#2E4F45"
ENAMEL_INSIDE = "#E9E2CC"
BULB = "#FFF1CC"
CORD = "#2A2725"

ROOM_W = 4.4
ROOM_D = 3.6
ROOM_H = 2.9
TILE_BAND = 1.45
SHUTTER_X = 0.6
SHUTTER_W = 2.2
SHUTTER_H = 2.3


# --------------------------------------------------------------------------
# La sala
# --------------------------------------------------------------------------


def _wall_tiles(mb: tb.MeshBuilder, rng: random.Random, length: float, place) -> None:
    """Azulejos de metro en hilada a matacán. ``place(u, v)`` da centro y giro."""
    tile_w, tile_h, gap = 0.24, 0.12, 0.006
    rows = int(TILE_BAND / tile_h)
    for row in range(rows):
        offset = (tile_w / 2.0) if row % 2 else 0.0
        u = -length / 2.0 - offset
        while u < length / 2.0:
            start, end = max(u, -length / 2.0), min(u + tile_w, length / 2.0)
            u += tile_w
            if end - start < 0.03 or rng.random() < 0.02:
                continue  # azulejo caído
            color = TILE_CREAM if row == rows - 2 else TILE
            center, rotation = place((start + end) / 2.0, row * tile_h + tile_h / 2.0)
            mb.box(
                (end - start - gap, 0.012, tile_h - gap) if rotation == 0 else (0.012, end - start - gap, tile_h - gap),
                center,
                color,
                rotation=(rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0.0),
                bevel=0.003,
                jitter=0.07,
            )


def build_room() -> bpy.types.Object:
    rng = random.Random(5)
    root = tb.empty("deposito_sala-estatico")
    half_w, half_d = ROOM_W / 2.0, ROOM_D / 2.0

    # Suelo: lecho de mortero y baldosas, cada una un poco torcida.
    floor = tb.MeshBuilder(seed=1)
    floor.box((ROOM_W, ROOM_D, 0.04), (0.0, 0.0, -0.02), GROUT)
    cols, rows = 14, 12
    tile_x, tile_y = ROOM_W / cols, ROOM_D / rows
    for i in range(cols):
        for j in range(rows):
            color = FLOOR_A if (i + j) % 2 == 0 else FLOOR_B
            if rng.random() < 0.06:
                color = FLOOR_CHIPPED
            floor.box(
                (tile_x - 0.008, tile_y - 0.008, 0.024),
                (-half_w + (i + 0.5) * tile_x, -half_d + (j + 0.5) * tile_y, 0.012 + rng.uniform(-0.002, 0.002)),
                color,
                rotation=(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-1.2, 1.2)),
                bevel=0.004,
                jitter=0.06,
            )
    floor_obj = floor.finish("suelo", tb.material("sala", PLASTER), root)

    # Muros de yeso, techo, viga y tuberías.
    walls = tb.MeshBuilder(seed=2)
    t = 0.15
    walls.box((ROOM_W + 2 * t, t, ROOM_H), (0.0, half_d + t / 2.0, ROOM_H / 2.0), PLASTER)
    walls.box((t, ROOM_D, ROOM_H), (-half_w - t / 2.0, 0.0, ROOM_H / 2.0), PLASTER)
    walls.box((t, ROOM_D, ROOM_H), (half_w + t / 2.0, 0.0, ROOM_H / 2.0), PLASTER)
    left_end = SHUTTER_X - SHUTTER_W / 2.0
    right_start = SHUTTER_X + SHUTTER_W / 2.0
    walls.box((left_end + half_w, t, ROOM_H), ((left_end - half_w) / 2.0, -half_d - t / 2.0, ROOM_H / 2.0), PLASTER)
    walls.box((half_w - right_start, t, ROOM_H), ((right_start + half_w) / 2.0, -half_d - t / 2.0, ROOM_H / 2.0), PLASTER)
    walls.box((SHUTTER_W, t, ROOM_H - SHUTTER_H), (SHUTTER_X, -half_d - t / 2.0, (ROOM_H + SHUTTER_H) / 2.0), PLASTER)
    walls.box((ROOM_W + 2 * t, ROOM_D + 2 * t, 0.12), (0.0, 0.0, ROOM_H + 0.06), CONCRETE)
    walls.box((ROOM_W, 0.3, 0.25), (0.0, 0.25, ROOM_H - 0.125), CONCRETE, bevel=0.01)
    # Moldura de madera sobre el zócalo.
    for center, size in (
        ((0.0, half_d - 0.015, TILE_BAND + 0.03), (ROOM_W, 0.03, 0.06)),
        ((-half_w + 0.015, 0.0, TILE_BAND + 0.03), (0.03, ROOM_D, 0.06)),
        ((half_w - 0.015, 0.0, TILE_BAND + 0.03), (0.03, ROOM_D, 0.06)),
    ):
        walls.box(size, center, TRIM, bevel=0.008, jitter=0.05)
    walls.bar((-half_w, half_d - 0.25, ROOM_H - 0.32), (half_w, half_d - 0.25, ROOM_H - 0.32), 0.05, PIPE_GREEN, 12)
    walls.bar((-half_w, half_d - 0.12, ROOM_H - 0.48), (half_w, half_d - 0.12, ROOM_H - 0.48), 0.035, PIPE_RUST, 10)
    for x in (-1.6, -0.2, 1.2):
        walls.box((0.04, 0.3, 0.03), (x, half_d - 0.15, ROOM_H - 0.26), RUST, bevel=0.005)
    walls_obj = walls.finish("muros", tb.material("sala", PLASTER), root)
    tb.stain(walls_obj, PLASTER_STAIN, amount=0.55, scale=1.3, coverage=0.35, seed=3)

    # Zócalo de azulejos en el fondo y en los laterales.
    tiles = tb.MeshBuilder(seed=3)
    _wall_tiles(tiles, rng, ROOM_W, lambda u, v: ((u, half_d - 0.006, v), 0))
    _wall_tiles(tiles, rng, ROOM_D, lambda u, v: ((-half_w + 0.006, u, v), 90))
    _wall_tiles(tiles, rng, ROOM_D, lambda u, v: ((half_w - 0.006, u, v), 90))
    tiles_obj = tiles.finish("azulejos", tb.material("sala", PLASTER), root)

    # Colisiones: suelo, muros y techo.
    tb.collision_box("suelo", (ROOM_W, ROOM_D, 0.1), (0.0, 0.0, -0.05), root)
    tb.collision_box("fondo", (ROOM_W, t, ROOM_H), (0.0, half_d + t / 2.0, ROOM_H / 2.0), root)
    tb.collision_box("izquierda", (t, ROOM_D, ROOM_H), (-half_w - t / 2.0, 0.0, ROOM_H / 2.0), root)
    tb.collision_box("derecha", (t, ROOM_D, ROOM_H), (half_w + t / 2.0, 0.0, ROOM_H / 2.0), root)
    tb.collision_box("frente_izq", (left_end + half_w, t, ROOM_H), ((left_end - half_w) / 2.0, -half_d - t / 2.0, ROOM_H / 2.0), root)
    tb.collision_box("frente_der", (half_w - right_start, t, ROOM_H), ((right_start + half_w) / 2.0, -half_d - t / 2.0, ROOM_H / 2.0), root)
    tb.collision_box("techo", (ROOM_W, ROOM_D, 0.12), (0.0, 0.0, ROOM_H + 0.06), root)

    tb.paint({floor_obj: None, walls_obj: None, tiles_obj: None}, samples=12, ao=0.5, ao_distance=0.35, ground_z=None, seed=5)
    return root


# --------------------------------------------------------------------------
# Mobiliario
# --------------------------------------------------------------------------


def build_shelf() -> bpy.types.Object:
    """Estantería metálica de ángulos ranurados, algo vencida por el peso."""
    root = tb.empty("estanteria_metalica-estatico")
    width, depth, height = 1.0, 0.4, 1.9
    mb = tb.MeshBuilder(seed=7)
    for x in (-width / 2.0 + 0.02, width / 2.0 - 0.02):
        for y in (-depth / 2.0 + 0.02, depth / 2.0 - 0.02):
            mb.box((0.04, 0.004, height), (x, y + math.copysign(0.018, y), height / 2.0), METAL_GREEN, bevel=0.001)
            mb.box((0.004, 0.04, height), (x + math.copysign(0.018, x), y, height / 2.0), METAL_GREEN, bevel=0.001)
    for z in (0.08, 0.5, 0.92, 1.34, 1.76):
        mb.box((width, depth, 0.016), (0.0, 0.0, z), METAL_GREEN, bevel=0.003, jitter=0.04)
        for y in (-depth / 2.0, depth / 2.0):
            mb.box((width, 0.012, 0.035), (0.0, y, z - 0.01), METAL_GREEN, bevel=0.003)
    shelf = mb.finish("estanteria", tb.material("metal", METAL_GREEN), root)
    # Las baldas se comban un poco por el centro.
    for v in shelf.data.vertices:
        if abs(v.co.x) < width / 2.0 - 0.05:
            v.co.z -= 0.012 * (1.0 - (2.0 * v.co.x / width) ** 2)
    tb.stain(shelf, RUST, amount=0.75, scale=2.5, coverage=0.28, seed=7)
    tb.collision_box("estanteria_metalica", (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({shelf: None}, samples=20, seed=7)
    return root


def build_crate(name: str, seed: int) -> bpy.types.Object:
    """Caja de madera de tablas, con listones en las esquinas."""
    rng = random.Random(seed)
    root = tb.empty(f"{name}-fisico")
    width, depth, height = 0.62, 0.44, 0.44
    plank_h, gap = (height - 0.02) / 3.0, 0.012
    mb = tb.MeshBuilder(seed=seed)
    woods = (WOOD, "#7A4E33", "#9A6845")
    for k in range(3):
        z = 0.01 + plank_h * (k + 0.5)
        for y in (-depth / 2.0 + 0.009, depth / 2.0 - 0.009):
            mb.box((width - 0.06, 0.018, plank_h - gap), (0.0, y, z), rng.choice(woods), rotation=(rng.uniform(-1, 1), 0, 0), bevel=0.004, jitter=0.08)
        for x in (-width / 2.0 + 0.009, width / 2.0 - 0.009):
            mb.box((0.018, depth - 0.06, plank_h - gap), (x, 0.0, z), rng.choice(woods), rotation=(0, rng.uniform(-1, 1), 0), bevel=0.004, jitter=0.08)
    for x in (-width / 2.0 + 0.025, width / 2.0 - 0.025):
        for y in (-depth / 2.0 + 0.025, depth / 2.0 - 0.025):
            mb.box((0.05, 0.05, height), (x, y, height / 2.0), WOOD_DARK, bevel=0.006, jitter=0.06)
    for k in range(4):
        mb.box((width / 4.0 - 0.01, depth - 0.02, 0.018), (-width / 2.0 + (k + 0.5) * width / 4.0, 0.0, height - 0.009), rng.choice(woods), rotation=(0, rng.uniform(-1.5, 1.5), 0), bevel=0.004, jitter=0.08)
    crate = mb.finish("caja", tb.material("madera", WOOD), root)
    tb.wobble(crate, amount=0.002, scale=4.0, seed=seed)
    tb.collision_box(name, (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({crate: None}, seed=seed)
    return root


def build_workbench() -> bpy.types.Object:
    """Banco de trabajo de tablones gruesos, con tornillo de banco y balda."""
    rng = random.Random(13)
    root = tb.empty("banco_trabajo-estatico")
    width, depth, height = 1.6, 0.7, 0.9
    mb = tb.MeshBuilder(seed=13)
    planks = 4
    for k in range(planks):
        y = -depth / 2.0 + (k + 0.5) * depth / planks
        mb.box((width, depth / planks - 0.006, 0.06), (0.0, y, height - 0.03), rng.choice((WOOD_DARK, "#7B5236", "#5F4029")), rotation=(rng.uniform(-0.6, 0.6), 0, 0), bevel=0.008, jitter=0.07)
    for x in (-width / 2.0 + 0.08, width / 2.0 - 0.08):
        for y in (-depth / 2.0 + 0.07, depth / 2.0 - 0.07):
            mb.box((0.08, 0.08, height - 0.06), (x, y, (height - 0.06) / 2.0), WOOD_DARK, bevel=0.008, jitter=0.05)
        mb.box((0.05, depth - 0.1, 0.06), (x, 0.0, 0.18), WOOD_DARK, bevel=0.006)
    for k in range(3):
        mb.box((width - 0.2, depth / 3.0 - 0.01, 0.025), (0.0, -depth / 2.0 + 0.05 + (k + 0.5) * (depth - 0.1) / 3.0, 0.22), rng.choice((WOOD, "#7A4E33")), bevel=0.004, jitter=0.07)
    # Tornillo de banco.
    vise_x = -width / 2.0 + 0.25
    mb.box((0.22, 0.12, 0.1), (vise_x, -depth / 2.0 - 0.02, height + 0.05), "#3F4A4F", bevel=0.01)
    mb.box((0.22, 0.04, 0.12), (vise_x, -depth / 2.0 - 0.12, height + 0.04), "#3F4A4F", bevel=0.01)
    mb.bar((vise_x, -depth / 2.0 - 0.3, height + 0.04), (vise_x, -depth / 2.0 + 0.04, height + 0.04), 0.012, "#2C3236")
    mb.bar((vise_x - 0.1, -depth / 2.0 - 0.3, height + 0.04), (vise_x + 0.1, -depth / 2.0 - 0.3, height + 0.04), 0.008, "#2C3236")
    bench = mb.finish("banco", tb.material("madera", WOOD), root)
    tb.wobble(bench, amount=0.002, scale=3.0, seed=13)
    tb.collision_box("banco_trabajo", (width, depth, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({bench: None}, seed=13)
    return root


def build_lamp() -> bpy.types.Object:
    """Lámpara colgante de pantalla esmaltada. El origen es el punto del techo."""
    root = tb.empty("lampara_colgante-estatico")
    drop = 0.62
    mb = tb.MeshBuilder(seed=17)
    mb.cylinder(0.05, 0.03, (0.0, 0.0, -0.015), CORD)
    mb.bar((0.0, 0.0, -0.02), (0.0, 0.0, -drop), 0.006, CORD, 6)
    mb.cylinder(0.028, 0.06, (0.0, 0.0, -drop - 0.02), "#3A3632")
    shade_z = -drop - 0.1
    mb.cylinder(0.22, 0.17, (0.0, 0.0, shade_z), ENAMEL, radius_top=0.05, segments=24, caps=False)
    inner = mb.cylinder(0.214, 0.165, (0.0, 0.0, shade_z), ENAMEL_INSIDE, radius_top=0.046, segments=24, caps=False)
    mb.flip(inner)
    mb.cylinder(0.224, 0.012, (0.0, 0.0, shade_z - 0.085), "#24302B", segments=24)
    lamp = mb.finish("lampara", tb.material("metal", ENAMEL), root)
    bulb = tb.MeshBuilder(seed=18)
    bulb.sphere(0.045, (0.0, 0.0, shade_z - 0.05), BULB, segments=14)
    bulb_obj = bulb.finish("bombilla", tb.material("bombilla", BULB), root)
    tb.paint({lamp: None, bulb_obj: None}, ground_z=None, ao=0.35, seed=17)
    return root


def build_shutter(name: str, open_shutter: bool) -> bpy.types.Object:
    """Persiana metálica de lamas. Cerrada deja una rendija abajo; abierta queda enrollada."""
    rng = random.Random(19)
    root = tb.empty(f"{name}-estatico")
    width, height, slat = SHUTTER_W, SHUTTER_H, 0.08
    mb = tb.MeshBuilder(seed=19)
    mb.box((width + 0.2, 0.32, 0.32), (0.0, 0.1, height + 0.12), SHUTTER, bevel=0.02, jitter=0.03)
    for x in (-width / 2.0 - 0.03, width / 2.0 + 0.03):
        mb.box((0.06, 0.08, height), (x, 0.0, height / 2.0), "#4A555C", bevel=0.006)
    if open_shutter:
        mb.box((width, 0.05, 0.06), (0.0, 0.0, height - 0.03), "#4A555C", bevel=0.008)
    else:
        gap = 0.14
        z = gap
        while z < height - 0.02:
            mb.box((width - 0.02, 0.025, slat - 0.006), (0.0, rng.uniform(-0.004, 0.004), z + slat / 2.0), SHUTTER, rotation=(rng.uniform(-2, 2), 0, rng.uniform(-0.3, 0.3)), bevel=0.008, jitter=0.06)
            z += slat
        mb.box((width - 0.02, 0.05, 0.05), (0.0, 0.0, gap - 0.02), "#4A555C", bevel=0.008)
        for x in (-0.5, 0.5):
            mb.box((0.12, 0.04, 0.03), (x, -0.04, gap + 0.02), "#2C3236", bevel=0.006)
    shutter = mb.finish("persiana", tb.material("metal", SHUTTER), root)
    tb.stain(shutter, RUST, amount=0.8, scale=1.8, coverage=0.3, seed=19)
    if not open_shutter:
        tb.dent(shutter, (0.4, 0.0, 1.0), radius=0.35, depth=0.02)
        tb.collision_box(name, (width, 0.06, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({shutter: None}, ground_z=0.0, seed=19)
    return root


# --------------------------------------------------------------------------
# Objetos pequeños
# --------------------------------------------------------------------------


def build_drum() -> bpy.types.Object:
    root = tb.empty("bidon-fisico")
    radius, height = 0.29, 0.88
    mb = tb.MeshBuilder(seed=23)
    mb.cylinder(radius, height, (0.0, 0.0, height / 2.0), "#8A3A2E", segments=28)
    for z in (0.02, height / 3.0, 2.0 * height / 3.0, height - 0.02):
        mb.cylinder(radius + 0.008, 0.025, (0.0, 0.0, z), "#7A3328", segments=28)
    mb.cylinder(0.035, 0.02, (0.14, 0.0, height + 0.01), "#5A2A22", segments=10)
    drum = mb.finish("bidon", tb.material("metal", "#8A3A2E"), root)
    tb.stain(drum, RUST, amount=0.8, scale=3.0, coverage=0.35, seed=23)
    tb.dent(drum, (radius, 0.0, 0.4), radius=0.15, depth=0.02)
    tb.collision_box("bidon", (2 * radius, 2 * radius, height), (0.0, 0.0, height / 2.0), root)
    tb.paint({drum: None}, seed=23)
    return root


def build_bucket() -> bpy.types.Object:
    root = tb.empty("cubo-fisico")
    mb = tb.MeshBuilder(seed=29)
    mb.cylinder(0.12, 0.26, (0.0, 0.0, 0.13), "#9AA0A0", radius_top=0.15, segments=20, caps=False)
    inner = mb.cylinder(0.115, 0.255, (0.0, 0.0, 0.13), "#7D8282", radius_top=0.145, segments=20, caps=False)
    mb.flip(inner)
    mb.cylinder(0.12, 0.01, (0.0, 0.0, 0.005), "#8C9292", segments=20)
    mb.cylinder(0.153, 0.012, (0.0, 0.0, 0.258), "#B0B5B5", segments=20)
    for angle in range(0, 180, 20):
        a0, a1 = math.radians(angle), math.radians(angle + 20)
        mb.bar((0.15 * math.cos(a0), 0.0, 0.26 + 0.12 * math.sin(a0)), (0.15 * math.cos(a1), 0.0, 0.26 + 0.12 * math.sin(a1)), 0.004, "#5B6060", 6)
    bucket = mb.finish("cubo", tb.material("metal", "#9AA0A0"), root)
    tb.stain(bucket, "#6E6A5E", amount=0.6, scale=4.0, coverage=0.3, seed=29)
    tb.collision_box("cubo", (0.3, 0.3, 0.27), (0.0, 0.0, 0.135), root)
    tb.paint({bucket: None}, seed=29)
    return root


def build_bottle(name: str, color: str, seed: int) -> bpy.types.Object:
    root = tb.empty(f"{name}-fisico")
    mb = tb.MeshBuilder(seed=seed)
    mb.cylinder(0.038, 0.17, (0.0, 0.0, 0.085), color, segments=14)
    mb.cylinder(0.038, 0.05, (0.0, 0.0, 0.195), color, radius_top=0.015, segments=14)
    mb.cylinder(0.014, 0.07, (0.0, 0.0, 0.255), color, segments=10)
    mb.cylinder(0.017, 0.012, (0.0, 0.0, 0.29), "#A89A80", segments=10)
    mb.cylinder(0.0385, 0.07, (0.0, 0.0, 0.09), "#D9CDB0", segments=14)
    bottle = mb.finish("botella", tb.material("vidrio", color), root)
    tb.collision_box(name, (0.08, 0.08, 0.3), (0.0, 0.0, 0.15), root)
    tb.paint({bottle: None}, ao=0.3, seed=seed)
    return root


def build_can() -> bpy.types.Object:
    root = tb.empty("lata-fisico")
    mb = tb.MeshBuilder(seed=31)
    mb.cylinder(0.037, 0.112, (0.0, 0.0, 0.056), "#A9A49A", segments=16)
    mb.cylinder(0.0375, 0.07, (0.0, 0.0, 0.056), "#9A3A30", segments=16)
    mb.cylinder(0.039, 0.006, (0.0, 0.0, 0.11), "#BDB8AE", segments=16)
    mb.cylinder(0.039, 0.006, (0.0, 0.0, 0.003), "#BDB8AE", segments=16)
    can = mb.finish("lata", tb.material("metal", "#A9A49A"), root)
    tb.collision_box("lata", (0.076, 0.076, 0.114), (0.0, 0.0, 0.057), root)
    tb.paint({can: None}, ao=0.3, seed=31)
    return root


def build_broom() -> bpy.types.Object:
    root = tb.empty("escoba-fisico")
    mb = tb.MeshBuilder(seed=37)
    mb.bar((0.0, 0.0, 0.12), (0.0, 0.0, 1.35), 0.014, "#B08A5A", 8)
    mb.box((0.3, 0.06, 0.05), (0.0, 0.0, 0.14), "#7A5A3A", bevel=0.008)
    rng = random.Random(37)
    for k in range(18):
        x = -0.13 + k * 0.0155
        mb.box((0.012, 0.05, 0.12), (x, rng.uniform(-0.004, 0.004), 0.06), "#C9A55A", rotation=(rng.uniform(-6, 6), rng.uniform(-8, 8), 0), jitter=0.1)
    broom = mb.finish("escoba", tb.material("madera", "#B08A5A"), root)
    tb.collision_box("escoba", (0.3, 0.06, 1.35), (0.0, 0.0, 0.675), root)
    tb.paint({broom: None}, ao=0.35, seed=37)
    return root


# --------------------------------------------------------------------------
# Herramientas y objetos del oficio (F1-08)
# --------------------------------------------------------------------------


def build_scale() -> bpy.types.Object:
    """Báscula de mostrador con esfera, como las de las tiendas de la época.

    La esfera mira hacia -Y (hacia la cámara; en Godot, hacia +Z)."""
    root = tb.empty("bascula-fisico")
    green = "#4F5F55"
    mb = tb.MeshBuilder(seed=59)
    mb.box((0.42, 0.30, 0.09), (0.0, 0.0, 0.045), green, bevel=0.012, jitter=0.03)
    mb.box((0.06, 0.06, 0.02), (0.0, -0.03, 0.098), "#3A3E3B", bevel=0.004)
    mb.box((0.34, 0.24, 0.012), (0.0, -0.03, 0.112), "#A9ABA4", bevel=0.004)
    mb.box((0.11, 0.07, 0.22), (0.0, 0.11, 0.19), green, bevel=0.01, jitter=0.03)
    center = Vector((0.0, 0.11, 0.37))
    mb.cylinder(0.145, 0.08, center, green, rotation=(90, 0, 0), segments=28)
    mb.cylinder(0.153, 0.014, center + Vector((0.0, -0.041, 0.0)), "#8D9089", rotation=(90, 0, 0), segments=28)
    mb.cylinder(0.128, 0.004, center + Vector((0.0, -0.043, 0.0)), "#E6DEC6", rotation=(90, 0, 0), segments=28)
    for k in range(21):
        angle = math.radians(-120 + k * 12)
        outer = 0.12 if k % 5 == 0 else 0.113
        a = center + Vector((0.104 * math.sin(angle), -0.046, 0.104 * math.cos(angle)))
        b = center + Vector((outer * math.sin(angle), -0.046, outer * math.cos(angle)))
        mb.bar(a, b, 0.0018, "#2A2A28", 4)
    needle = math.radians(28)
    mb.box((0.005, 0.003, 0.095), center + Vector((0.042 * math.sin(needle), -0.048, 0.042 * math.cos(needle))), "#A03028", rotation=(0, 28, 0))
    mb.cylinder(0.009, 0.006, center + Vector((0.0, -0.049, 0.0)), "#2A2A28", rotation=(90, 0, 0), segments=10)
    body = mb.finish("bascula", tb.material("metal", green), root)
    tb.stain(body, RUST, amount=0.5, scale=4.0, coverage=0.25, seed=59)
    tb.collision_box("bascula", (0.42, 0.30, 0.52), (0.0, 0.02, 0.26), root)
    tb.paint({body: None}, ao=0.35, seed=59)
    return root


def build_gas_mask() -> bpy.types.Object:
    """Máscara antigás de goma (de capucha), con dos visores y el filtro enroscado.

    De pie, como puesta: los visores miran hacia -Y."""
    root = tb.empty("mascara_gas-fisico")
    rubber = "#3F4641"
    mb = tb.MeshBuilder(seed=61)
    mb.sphere(0.1, (0.0, 0.0, 0.15), rubber, segments=22, scale=(0.95, 0.88, 1.28))
    for x in (-0.043, 0.043):
        mb.cylinder(0.034, 0.014, (x, -0.081, 0.18), "#6A6E69", rotation=(98, 0, 0), segments=18)
    mb.cylinder(0.026, 0.034, (0.0, -0.082, 0.08), "#2E3330", rotation=(112, 0, 0), segments=14)
    mb.cylinder(0.05, 0.085, (0.0, -0.12, 0.035), "#5A6340", rotation=(122, 0, 0), segments=20)
    mb.cylinder(0.052, 0.012, (0.0, -0.096, 0.05), "#474D33", rotation=(122, 0, 0), segments=20)
    for side in (-1.0, 1.0):
        mb.bar((side * 0.09, 0.0, 0.19), (side * 0.07, 0.07, 0.25), 0.007, "#2A2C28", 6)
        mb.bar((side * 0.07, 0.07, 0.25), (0.0, 0.09, 0.27), 0.007, "#2A2C28", 6)
    mask = mb.finish("mascara", tb.material("base", rubber), root)
    tb.stain(mask, "#2B2E2B", amount=0.6, scale=6.0, coverage=0.4, seed=61)
    glass = tb.MeshBuilder(seed=62)
    for x in (-0.043, 0.043):
        glass.cylinder(0.027, 0.012, (x, -0.083, 0.18), "#2A3238", rotation=(98, 0, 0), segments=18)
    lenses = glass.finish("visores", tb.material("vidrio", "#2A3238"), root)
    tb.collision_box("mascara_gas", (0.2, 0.26, 0.3), (0.0, -0.03, 0.15), root)
    tb.paint({mask: None, lenses: None}, ao=0.4, seed=61)
    return root


def build_dosimeter() -> bpy.types.Object:
    """Dosímetro de campaña: caja caqui con esfera y mando, y la sonda unida por un cable."""
    root = tb.empty("dosimetro-fisico")
    khaki = "#6A6A48"
    mb = tb.MeshBuilder(seed=67)
    mb.box((0.20, 0.11, 0.09), (0.0, 0.0, 0.045), khaki, bevel=0.01, jitter=0.03)
    mb.box((0.205, 0.115, 0.022), (0.0, 0.0, 0.1), "#58583B", bevel=0.006)
    mb.cylinder(0.036, 0.01, (-0.045, -0.008, 0.114), "#2A2A26", segments=22)
    mb.cylinder(0.03, 0.006, (-0.045, -0.008, 0.118), "#E3DCC2", segments=22)
    mb.box((0.003, 0.026, 0.002), (-0.05, -0.012, 0.1215), "#1E1E1C", rotation=(0, 0, 35))
    mb.cylinder(0.015, 0.02, (0.05, -0.01, 0.12), "#1E1E1C", segments=12)
    mb.box((0.004, 0.02, 0.004), (0.05, -0.01, 0.131), "#C8C0A8")
    for x in (-0.08, 0.08):
        mb.box((0.02, 0.008, 0.07), (x, 0.06, 0.07), "#3B3A2A", bevel=0.002)
    probe_z = 0.02
    mb.cylinder(0.018, 0.16, (0.01, -0.12, probe_z), "#3B3D38", rotation=(0, 90, 0), segments=14)
    mb.cylinder(0.021, 0.03, (0.095, -0.12, probe_z), "#2A2B28", rotation=(0, 90, 0), segments=14)
    cable = [(-0.07, -0.12, probe_z), (-0.115, -0.1, 0.012), (-0.13, -0.05, 0.01), (-0.11, -0.01, 0.03)]
    for a, b in zip(cable, cable[1:]):
        mb.bar(a, b, 0.004, "#1E1E1C", 6)
    device = mb.finish("dosimetro", tb.material("metal", khaki), root)
    tb.stain(device, "#4C4B33", amount=0.5, scale=5.0, coverage=0.35, seed=67)
    tb.collision_box("dosimetro", (0.24, 0.26, 0.13), (0.0, -0.05, 0.065), root)
    tb.paint({device: None}, ao=0.35, seed=67)
    return root


def build_flashlight() -> bpy.types.Object:
    """Linterna de pilas de cuerpo metálico, tumbada. La cabeza mira hacia +X."""
    root = tb.empty("linterna-fisico")
    body = "#3B403C"
    r = 0.019
    z = r * 1.55
    mb = tb.MeshBuilder(seed=71)
    mb.cylinder(r, 0.14, (0.0, 0.0, z), body, rotation=(0, 90, 0), segments=16, jitter=0.03)
    mb.cylinder(r, 0.045, (0.092, 0.0, z), body, rotation=(0, 90, 0), radius_top=r * 1.55, segments=16)
    mb.cylinder(r * 1.6, 0.012, (0.118, 0.0, z), "#8C8F88", rotation=(0, 90, 0), segments=16)
    mb.cylinder(r * 1.04, 0.012, (-0.072, 0.0, z), "#2A2D2A", rotation=(0, 90, 0), segments=16)
    mb.box((0.022, 0.012, 0.008), (0.02, 0.0, z + r + 0.003), "#7A3A30", bevel=0.002)
    for k in range(6):
        mb.cylinder(r * 1.02, 0.003, (-0.05 + k * 0.012, 0.0, z), "#2E322F", rotation=(0, 90, 0), segments=16)
    torch = mb.finish("linterna", tb.material("metal", body), root)
    tb.stain(torch, "#6E6A5E", amount=0.4, scale=8.0, coverage=0.3, seed=71)
    lens = tb.MeshBuilder(seed=72)
    lens.cylinder(r * 1.45, 0.004, (0.125, 0.0, z), "#E8E0B8", rotation=(0, 90, 0), segments=16)
    glass = lens.finish("cristal", tb.material("vidrio", "#E8E0B8"), root)
    tb.collision_box("linterna", (0.26, 0.06, 0.06), (0.02, 0.0, z), root)
    tb.paint({torch: None, glass: None}, ao=0.3, seed=71)
    return root


def models() -> dict:
    return {
        "deposito_sala": build_room,
        "estanteria_metalica": build_shelf,
        "caja_madera": lambda: build_crate("caja_madera", 41),
        "caja_madera_b": lambda: build_crate("caja_madera_b", 43),
        "banco_trabajo": build_workbench,
        "lampara_colgante": build_lamp,
        "persiana_cerrada": lambda: build_shutter("persiana_cerrada", False),
        "persiana_abierta": lambda: build_shutter("persiana_abierta", True),
        "bidon": build_drum,
        "cubo": build_bucket,
        "botella_verde": lambda: build_bottle("botella_verde", "#3E6B45", 47),
        "botella_marron": lambda: build_bottle("botella_marron", "#6B4A2B", 53),
        "lata": build_can,
        "escoba": build_broom,
        "bascula": build_scale,
        "mascara_gas": build_gas_mask,
        "dosimetro": build_dosimeter,
        "linterna": build_flashlight,
    }
