"""La superficie: un patio de Los Bloques bajo la nieve.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Las
fachadas miran hacia -Y (hacia la cámara); en Godot miran hacia +Z.

Todo usa el material "nevado": el shader blanquea lo que mira hacia arriba
(cornisas, balcones, techos de coches, ramas).
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

SNOW = "#D4D1C9"
DIRTY_SNOW = "#9C9890"
ASPHALT = "#3A3A3C"
PANEL = "#8E8B83"
PANEL_DARK = "#716E67"
PLINTH = "#6E6A64"
GLASS = "#262A30"
FRAME = "#C9C2B0"
FRAME_WOOD = "#6A5038"
DOOR = "#4A3A30"
RUST = "#8E4A2F"
CONCRETE = "#8F8C84"
METAL = "#4A5054"
BARK = "#3B3430"
BALCONY_COLORS = ("#7C93A0", "#8FA08A", "#B3A58A", "#9A7F7A", "#8C8C84")

FLOOR_H = 2.8
COL_W = 3.0
PLINTH_H = 0.8


def _snow_material() -> bpy.types.Material:
    return tb.material("nevado", SNOW)


# --------------------------------------------------------------------------
# Bloque de paneles
# --------------------------------------------------------------------------


def build_block(name: str, sections: int, floors: int, seed: int) -> bpy.types.Object:
    rng = random.Random(seed)
    root = tb.empty(f"{name}-estatico")
    cols = sections * 3
    width = cols * COL_W
    height = PLINTH_H + floors * FLOOR_H
    depth = 11.0
    x0 = -width / 2.0
    mb = tb.MeshBuilder(seed=seed)

    mb.box((width - 0.1, depth, height), (0.0, depth / 2.0 + 0.1, height / 2.0), PANEL_DARK)
    mb.box((width + 0.1, 0.4, PLINTH_H), (0.0, -0.05, PLINTH_H / 2.0), PLINTH, bevel=0.02)
    mb.box((width + 0.2, 0.5, 0.6), (0.0, 0.05, height + 0.3), PANEL_DARK, bevel=0.03)
    mb.box((4.0, 3.0, 2.4), (rng.uniform(-3, 3), 4.0, height + 1.2), PANEL_DARK, bevel=0.03)

    entrance_cols = {s * 3 + 1 for s in range(sections)}
    for c in range(cols):
        cx = x0 + COL_W * (c + 0.5)
        balcony_col = c % 3 != 1
        for f in range(floors):
            z0 = PLINTH_H + f * FLOOR_H
            zc = z0 + FLOOR_H / 2.0
            mb.box(
                (COL_W - 0.04, 0.25, FLOOR_H - 0.04),
                (cx, -0.125 + rng.uniform(-0.012, 0.012), zc),
                PANEL,
                bevel=0.02,
                jitter=0.07,
            )
            if c in entrance_cols and f == 0:
                _entrance(mb, cx, z0, rng)
                continue
            boarded = rng.random() < 0.18
            window_w = 1.1 if balcony_col else 1.5
            window_x = cx + (0.55 if balcony_col else 0.0)
            _window(mb, window_x, zc + 0.15, window_w, 1.45, rng, boarded)
            if balcony_col:
                _window(mb, cx - 0.75, zc - 0.05, 0.75, 2.1, rng, boarded=False, door=True)
                if f > 0:
                    _balcony(mb, cx, z0, rng)
    # Bajantes en las esquinas.
    for x in (x0 + 0.15, -x0 - 0.15):
        mb.bar((x, -0.32, 0.1), (x, -0.32, height), 0.06, METAL, 8)

    building = mb.finish("bloque", _snow_material(), root)
    tb.stain(building, RUST, amount=0.5, scale=1.2, coverage=0.25, seed=seed, stretch_z=0.15)
    tb.stain(building, "#4E4A45", amount=0.6, scale=0.5, coverage=0.45, seed=seed + 1, stretch_z=0.3)
    tb.stain(building, "#3F3B37", amount=0.5, scale=0.18, coverage=0.3, seed=seed + 2)
    tb.collision_box(name, (width, depth + 0.5, height), (0.0, depth / 2.0 - 0.2, height / 2.0), root)
    tb.paint({building: None}, samples=10, ao=0.45, ao_distance=0.8, cavity_dark=0.25, ground_z=0.0, seed=seed)
    return root


def _window(
    mb: tb.MeshBuilder,
    x: float,
    z: float,
    w: float,
    h: float,
    rng: random.Random,
    boarded: bool,
    door: bool = False,
) -> None:
    frame = FRAME if rng.random() < 0.6 else FRAME_WOOD
    y = -0.26
    mb.box((w, 0.02, h), (x, y, z), GLASS)
    for dz in (-h / 2.0, h / 2.0):
        mb.box((w + 0.1, 0.07, 0.07), (x, y - 0.02, z + dz), frame, bevel=0.01, jitter=0.05)
    for dx in (-w / 2.0, w / 2.0):
        mb.box((0.07, 0.07, h), (x + dx, y - 0.02, z), frame, bevel=0.01, jitter=0.05)
    if not door:
        mb.box((0.05, 0.05, h), (x, y - 0.02, z), frame)
        mb.box((w + 0.2, 0.18, 0.05), (x, y - 0.08, z - h / 2.0 - 0.05), PANEL_DARK, bevel=0.01)
    if boarded:
        for k in range(3):
            mb.box(
                (w + 0.15, 0.03, 0.16),
                (x, y - 0.07, z - h / 3.0 + k * h / 3.0),
                FRAME_WOOD,
                rotation=(0.0, rng.uniform(-14, 14), 0.0),
                bevel=0.008,
                jitter=0.1,
            )


def _balcony(mb: tb.MeshBuilder, cx: float, z0: float, rng: random.Random) -> None:
    color = rng.choice(BALCONY_COLORS)
    depth = 1.05
    mb.box((COL_W - 0.3, depth, 0.14), (cx, -0.25 - depth / 2.0, z0 + 0.07), PANEL_DARK, bevel=0.02)
    mb.box((COL_W - 0.3, 0.06, 0.95), (cx, -0.25 - depth + 0.03, z0 + 0.6), color, bevel=0.015, jitter=0.06)
    for side in (-1, 1):
        mb.box((0.06, depth, 0.95), (cx + side * (COL_W / 2.0 - 0.18), -0.25 - depth / 2.0, z0 + 0.6), color, bevel=0.015)
    mb.box((COL_W - 0.25, 0.08, 0.05), (cx, -0.25 - depth + 0.03, z0 + 1.1), METAL, bevel=0.01)
    if rng.random() < 0.35:
        # Balcón acristalado por los vecinos, con lo que tenían a mano.
        for k in range(4):
            mb.box((0.05, 0.05, 1.0), (cx - 1.2 + k * 0.8, -0.25 - depth + 0.03, z0 + 1.6), FRAME_WOOD, bevel=0.008)
        mb.box((COL_W - 0.35, 0.02, 0.95), (cx, -0.25 - depth + 0.05, z0 + 1.6), GLASS)
        mb.box((COL_W - 0.25, 0.08, 0.06), (cx, -0.25 - depth + 0.03, z0 + 2.12), FRAME_WOOD, bevel=0.008)
    if rng.random() < 0.4:
        mb.bar((cx - 1.0, -0.6, z0 + 2.0), (cx + 1.0, -0.6, z0 + 2.0), 0.008, "#2A2725", 4)


def _entrance(mb: tb.MeshBuilder, cx: float, z0: float, rng: random.Random) -> None:
    mb.box((1.3, 0.1, 2.2), (cx, -0.27, z0 + 1.1 - PLINTH_H + 0.25), DOOR, bevel=0.01, jitter=0.05)
    mb.box((0.06, 0.12, 2.2), (cx, -0.33, z0 + 1.1 - PLINTH_H + 0.25), "#3A2E26")
    mb.box((2.6, 1.6, 0.16), (cx, -0.95, z0 + 2.2), PANEL_DARK, bevel=0.03)
    for side in (-1, 1):
        mb.bar((cx + side * 1.15, -1.6, z0 + 2.15), (cx + side * 1.15, -1.6, 0.0), 0.05, METAL, 8)
    for k in range(3):
        mb.box((2.0, 0.35, 0.18), (cx, -0.45 - k * 0.32, 0.25 - k * 0.09), CONCRETE, bevel=0.02, jitter=0.05)
    mb.box((0.2, 0.12, 0.12), (cx, -0.32, z0 + 1.95), METAL, bevel=0.01)


# --------------------------------------------------------------------------
# Mobiliario urbano
# --------------------------------------------------------------------------


def build_street_lamp() -> bpy.types.Object:
    root = tb.empty("farola-estatico")
    mb = tb.MeshBuilder(seed=61)
    mb.cylinder(0.14, 7.5, (0.0, 0.0, 3.75), CONCRETE, radius_top=0.08, segments=8)
    mb.box((0.36, 0.36, 0.5), (0.0, 0.0, 0.25), CONCRETE, bevel=0.03)
    points = [(0.0, 0.0, 7.3), (0.4, 0.0, 7.75), (1.0, 0.0, 7.9), (1.6, 0.0, 7.8)]
    for a, b in zip(points, points[1:]):
        mb.bar(a, b, 0.045, METAL, 8)
    mb.box((0.7, 0.28, 0.14), (1.85, 0.0, 7.72), METAL, rotation=(0.0, -8.0, 0.0), bevel=0.04)
    mb.box((0.55, 0.22, 0.03), (1.86, 0.0, 7.64), "#8C9496", rotation=(0.0, -8.0, 0.0), bevel=0.01)
    lamp = mb.finish("farola", _snow_material(), root)
    tb.stain(lamp, RUST, amount=0.6, scale=2.0, coverage=0.3, seed=61)
    tb.collision_box("farola", (0.36, 0.36, 7.5), (0.0, 0.0, 3.75), root)
    tb.paint({lamp: None}, samples=12, seed=61)
    return root


def build_bench() -> bpy.types.Object:
    root = tb.empty("banco_parque-estatico")
    rng = random.Random(67)
    mb = tb.MeshBuilder(seed=67)
    for x in (-0.75, 0.75):
        mb.box((0.14, 0.5, 0.42), (x, 0.0, 0.21), CONCRETE, bevel=0.02, jitter=0.05)
        mb.box((0.12, 0.08, 0.5), (x, 0.24, 0.65), CONCRETE, rotation=(-12.0, 0.0, 0.0), bevel=0.02)
    for k, y in enumerate((-0.18, -0.03, 0.12)):
        if k == 1:
            continue  # falta un listón
        mb.box((1.9, 0.12, 0.04), (0.0, y, 0.44), "#6E5038", rotation=(0.0, rng.uniform(-1, 1), 0.0), bevel=0.01, jitter=0.1)
    mb.box((1.9, 0.04, 0.12), (0.0, 0.27, 0.62), "#6E5038", rotation=(-12.0, 0.0, 0.0), bevel=0.01, jitter=0.1)
    mb.box((1.1, 0.04, 0.12), (-0.35, 0.3, 0.78), "#6E5038", rotation=(-12.0, 4.0, 0.0), bevel=0.01, jitter=0.1)
    bench = mb.finish("banco", _snow_material(), root)
    tb.wobble(bench, amount=0.004, scale=3.0, seed=67)
    tb.collision_box("banco_parque", (1.9, 0.5, 0.45), (0.0, 0.0, 0.22), root)
    tb.paint({bench: None}, seed=67)
    return root


def _branch(mb: tb.MeshBuilder, rng: random.Random, start: Vector, direction: Vector, length: float, radius: float, depth: int) -> None:
    end = start + direction.normalized() * length
    mb.cylinder(
        radius,
        length,
        (start + end) / 2.0,
        BARK,
        rotation=[math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference(direction.normalized()).to_euler()],
        radius_top=radius * 0.72,
        segments=7,
        jitter=0.08,
    )
    if depth == 0:
        return
    for _ in range(rng.randint(2, 3)):
        twist = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.2, 1.0)))
        child = (direction.normalized() * 0.6 + twist.normalized() * 0.55).normalized()
        start_at = start.lerp(end, rng.uniform(0.6, 1.0))
        _branch(mb, rng, start_at, child, length * rng.uniform(0.55, 0.75), radius * 0.62, depth - 1)


def build_tree(name: str, seed: int, height: float) -> bpy.types.Object:
    rng = random.Random(seed)
    root = tb.empty(f"{name}-estatico")
    mb = tb.MeshBuilder(seed=seed)
    trunk_top = Vector((rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), height * 0.45))
    _branch(mb, rng, Vector((0, 0, -0.2)), trunk_top - Vector((0, 0, -0.2)), trunk_top.length + 0.2, 0.2, 0)
    for _ in range(3):
        direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(1.0, 2.2)))
        _branch(mb, rng, trunk_top, direction, height * 0.35, 0.12, 3)
    tree = mb.finish("arbol", _snow_material(), root)
    tb.collision_box(name, (0.4, 0.4, height * 0.45), (0.0, 0.0, height * 0.22), root)
    tb.paint({tree: None}, samples=8, ao=0.3, cavity_dark=0.1, seed=seed)
    return root


def build_car() -> bpy.types.Object:
    """Un turismo cualquiera, abandonado hace años. No es ningún modelo real."""
    root = tb.empty("coche-estatico")
    body_color = "#6F8C7E"
    mb = tb.MeshBuilder(seed=71)
    mb.box((4.2, 1.62, 0.62), (0.0, 0.0, 0.62), body_color, bevel=0.07, segments=2)
    cabin = mb.box((2.2, 1.46, 0.56), (-0.25, 0.0, 1.2), body_color, bevel=0.06, segments=2)
    for face in cabin:
        for vert in face.verts:
            if vert.co.z > 1.3:
                vert.co.x *= 0.86
                vert.co.y *= 0.9
    for x in (-1.15, 0.75):
        mb.box((0.04, 1.3, 0.4), (x + (0.18 if x > 0 else -0.12), 0.0, 1.22), GLASS, rotation=(0.0, -32.0 if x > 0 else 30.0, 0.0))
    for y in (-0.735, 0.735):
        mb.box((1.7, 0.02, 0.38), (-0.25, y, 1.22), GLASS)
    for x in (-2.1, 2.1):
        mb.box((0.1, 1.7, 0.14), (x, 0.0, 0.48), "#9AA0A2", bevel=0.03)
        for y in (-0.55, 0.55):
            mb.cylinder(0.09, 0.05, (x * 1.005, y, 0.68), "#C9C6B8", rotation=(0.0, 90.0, 0.0), segments=12)
    for x in (-1.35, 1.35):
        for y in (-0.72, 0.72):
            mb.cylinder(0.33, 0.22, (x, y, 0.3), "#232323", rotation=(90.0, 0.0, 0.0), segments=16)
    car = mb.finish("coche", _snow_material(), root)
    tb.stain(car, RUST, amount=0.7, scale=1.6, coverage=0.32, seed=71)
    tb.dent(car, (2.0, -0.6, 0.7), radius=0.5, depth=0.06)
    tb.collision_box("coche", (4.2, 1.7, 1.5), (0.0, 0.0, 0.75), root)
    tb.paint({car: None}, samples=14, seed=71)
    return root


def build_swing() -> bpy.types.Object:
    root = tb.empty("columpio-estatico")
    color = "#8E4038"
    mb = tb.MeshBuilder(seed=73)
    for x in (-1.3, 1.3):
        mb.bar((x, -0.8, 0.0), (x, 0.0, 2.3), 0.045, color, 8)
        mb.bar((x, 0.8, 0.0), (x, 0.0, 2.3), 0.045, color, 8)
    mb.bar((-1.4, 0.0, 2.3), (1.4, 0.0, 2.3), 0.05, color, 8)
    for x, tilt in ((-0.55, 0.0), (0.55, 24.0)):
        offset = math.sin(math.radians(tilt)) * 1.6
        for dx in (-0.22, 0.22):
            mb.bar((x + dx, 0.0, 2.28), (x + dx, -offset, 0.62), 0.01, METAL, 4)
        mb.box((0.5, 0.2, 0.04), (x, -offset, 0.6), "#6E5038", rotation=(tilt, 0.0, 0.0), bevel=0.01)
    swing = mb.finish("columpio", _snow_material(), root)
    tb.stain(swing, RUST, amount=0.7, scale=3.0, coverage=0.35, seed=73)
    tb.collision_box("columpio", (2.8, 1.6, 2.3), (0.0, 0.0, 1.15), root)
    tb.paint({swing: None}, samples=10, seed=73)
    return root


def build_container() -> bpy.types.Object:
    root = tb.empty("contenedor-estatico")
    color = "#3E4F3E"
    mb = tb.MeshBuilder(seed=79)
    body = mb.box((1.5, 1.0, 1.05), (0.0, 0.0, 0.6), color, bevel=0.03, jitter=0.04)
    for face in body:
        for vert in face.verts:
            if vert.co.z < 0.3:
                vert.co.x *= 0.9
                vert.co.y *= 0.88
    mb.box((1.55, 0.55, 0.05), (0.0, -0.22, 1.16), color, rotation=(12.0, 0.0, 0.0), bevel=0.02)
    mb.box((1.55, 0.5, 0.05), (0.0, 0.3, 1.2), color, rotation=(-28.0, 0.0, 0.0), bevel=0.02)
    rng = random.Random(79)
    for k in range(5):
        mb.box((0.5, 0.45, 0.4), (rng.uniform(-1.4, 1.4), rng.uniform(-1.1, -0.6), 0.18), "#2E2B2A", rotation=(rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(0, 90)), bevel=0.12, segments=2, jitter=0.15)
    bin_obj = mb.finish("contenedor", _snow_material(), root)
    tb.stain(bin_obj, RUST, amount=0.8, scale=2.2, coverage=0.4, seed=79)
    tb.collision_box("contenedor", (1.5, 1.0, 1.2), (0.0, 0.0, 0.6), root)
    tb.paint({bin_obj: None}, samples=12, seed=79)
    return root


def build_ground() -> bpy.types.Object:
    """El suelo del patio: nieve con un sendero pisado, bordillos y montículos."""
    rng = random.Random(83)
    root = tb.empty("suelo_patio-estatico")
    mb = tb.MeshBuilder(seed=83)
    size = 46.0
    mb.box((size, size, 0.3), (0.0, 0.0, -0.15), SNOW)
    ground = mb.finish("nieve", _snow_material(), root)
    # El cubo se subdivide para que la nieve pueda ondular.
    ground.data.update()
    path = tb.MeshBuilder(seed=84)
    for k in range(14):
        t = k / 13.0
        x = -14.0 + t * 26.0 + math.sin(t * 5.0) * 1.2
        y = 6.0 - t * 14.0
        path.box((2.4, 2.2, 0.06), (x, y, 0.0), DIRTY_SNOW, rotation=(0.0, 0.0, -28.0 + rng.uniform(-6, 6)), bevel=0.2, segments=2, jitter=0.08)
    mounds = tb.MeshBuilder(seed=85)
    for k in range(11):
        mounds.sphere(
            1.0,
            (rng.uniform(-16, 16), rng.uniform(-6, 9), -0.15),
            SNOW,
            segments=20,
            scale=(rng.uniform(1.2, 2.6), rng.uniform(0.9, 1.8), rng.uniform(0.45, 0.9)),
            jitter=0.03,
        )
    for k in range(6):
        path.box((rng.uniform(1.0, 2.5), rng.uniform(0.8, 1.6), 0.03), (rng.uniform(-12, 12), rng.uniform(-5, 8), 0.02), ASPHALT, rotation=(0.0, 0.0, rng.uniform(0, 90)), bevel=0.15, segments=2, jitter=0.1)
    for k in range(8):
        path.box((2.0, 0.25, 0.18), (-10.0 + k * 2.1, -7.4, 0.05), CONCRETE, rotation=(0.0, 0.0, rng.uniform(-2, 2)), bevel=0.03, jitter=0.06)
    details = path.finish("sendero", _snow_material(), root)
    tb.wobble(details, amount=0.06, scale=0.5, seed=83)
    heaps = mounds.finish("montones", _snow_material(), root)
    tb.wobble(heaps, amount=0.22, scale=0.8, seed=85)
    tb.collision_box("suelo_patio", (size, size, 0.3), (0.0, 0.0, -0.15), root)
    tb.paint({ground: None, details: None, heaps: None}, samples=8, ao=0.35, ao_distance=0.6, ground_z=None, mottling=0.04, seed=83)
    return root


def models() -> dict:
    return {
        "bloque_paneles": lambda: build_block("bloque_paneles", 2, 5, 89),
        "bloque_paneles_b": lambda: build_block("bloque_paneles_b", 1, 5, 97),
        "farola": build_street_lamp,
        "banco_parque": build_bench,
        "arbol_desnudo": lambda: build_tree("arbol_desnudo", 101, 7.0),
        "arbol_desnudo_b": lambda: build_tree("arbol_desnudo_b", 103, 5.0),
        "coche": build_car,
        "columpio": build_swing,
        "contenedor": build_container,
        "suelo_patio": build_ground,
    }
