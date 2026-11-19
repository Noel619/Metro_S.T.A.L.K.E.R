"""La superficie: un patio de Los Bloques, años después de la guerra.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Las
fachadas miran hacia -Y (hacia la cámara); en Godot miran hacia +Z.

Casi todo usa el material "nevado": el shader cubre de nieve vieja (sucia, con
ceniza y hollín) lo que mira hacia arriba. Las ruinas del horizonte usan
"lejano": siluetas planas fundidas con el color del horizonte.

Nada debe parecer limpio: hollín sobre las ventanas quemadas, paneles caídos,
balcones desplomados, escombros, coches quemados y cables por el suelo.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

SNOW = "#B3AEA2"
DIRTY_SNOW = "#7A7266"
SOOT = "#1E1B19"
ASPHALT = "#34343A"
PANEL = "#7E7A72"
PANEL_DARK = "#625E58"
PLINTH = "#58544F"
GLASS = "#1F2228"
BURNT_GLASS = "#0D0C0E"
FRAME = "#A9A291"
FRAME_WOOD = "#5A4432"
DOOR = "#3E3129"
RUST = "#7E4128"
CONCRETE = "#7D7A73"
METAL = "#40464A"
BARK = "#34302C"
BRICK = "#7A4A3A"
REBAR = "#4A3426"
INTERIOR = "#141312"
BALCONY_COLORS = ("#6A7F8B", "#7D8C78", "#9A8F78", "#86706B", "#7A7A73")

FLOOR_H = 2.8
COL_W = 3.0
PLINTH_H = 0.8


def _snow_material() -> bpy.types.Material:
    return tb.material("nevado", SNOW)


def _hinged(center: tuple, hinge_y: float, hinge_z: float, angle: float) -> tuple:
    """Gira un punto alrededor de una bisagra horizontal (eje X)."""
    dy, dz = center[1] - hinge_y, center[2] - hinge_z
    a = math.radians(angle)
    return (center[0], hinge_y + dy * math.cos(a) - dz * math.sin(a), hinge_z + dy * math.sin(a) + dz * math.cos(a))


# --------------------------------------------------------------------------
# Bloque de paneles
# --------------------------------------------------------------------------


def build_block(name: str, sections: int, floors: int, seed: int, damage: float) -> bpy.types.Object:
    rng = random.Random(seed)
    root = tb.empty(f"{name}-estatico")
    cols = sections * 3
    width = cols * COL_W
    height = PLINTH_H + floors * FLOOR_H
    depth = 11.0
    x0 = -width / 2.0
    mb = tb.MeshBuilder(seed=seed)

    mb.box((width - 0.1, depth, height), (0.0, depth / 2.0 + 0.1, height / 2.0), PANEL_DARK)
    mb.box((width + 0.1, 0.4, PLINTH_H), (0.0, -0.05, PLINTH_H / 2.0), PLINTH, bevel=0.02, cuts=4)
    for c in range(cols):
        x = x0 + COL_W * (c + 0.5)
        if rng.random() < damage * 0.35:
            mb.box(
                (COL_W * rng.uniform(0.3, 0.6), 0.5, 0.35),
                (x + rng.uniform(-0.8, 0.8), 0.05, height + 0.15),
                PANEL_DARK,
                rotation=(rng.uniform(-8, 8), rng.uniform(-10, 10), 0.0),
                bevel=0.03,
            )
        else:
            mb.box((COL_W + 0.02, 0.5, 0.6), (x, 0.05, height + 0.3), PANEL_DARK, bevel=0.03, jitter=0.05)
    mb.box((4.0, 3.0, 2.4), (rng.uniform(-3, 3), 4.0, height + 1.2), PANEL_DARK, bevel=0.03)

    entrance_cols = {s * 3 + 1 for s in range(sections)}
    scorch_regions = []
    for c in range(cols):
        cx = x0 + COL_W * (c + 0.5)
        balcony_col = c % 3 != 1
        for f in range(floors):
            z0 = PLINTH_H + f * FLOOR_H
            zc = z0 + FLOOR_H / 2.0
            if f > 0 and c not in entrance_cols and rng.random() < damage * 0.09:
                _missing_panel(mb, cx, zc, rng)
                _debris_at_base(mb, cx, rng)
                continue
            mb.box(
                (COL_W - 0.04, 0.25, FLOOR_H - 0.04),
                (cx, -0.125 + rng.uniform(-0.012, 0.012), zc),
                PANEL,
                bevel=0.02,
                jitter=0.07,
                cuts=5,
            )
            if c in entrance_cols and f == 0:
                _entrance(mb, cx, z0, rng)
                continue
            burnt = rng.random() < damage * 0.32
            boarded = not burnt and rng.random() < 0.22
            window_w = 1.1 if balcony_col else 1.5
            window_x = cx + (0.55 if balcony_col else 0.0)
            _window(mb, window_x, zc + 0.15, window_w, 1.45, rng, boarded, burnt=burnt)
            if burnt:
                scorch_regions.append(((window_x, -0.26, zc + 0.15 + 0.72), window_w * 1.5, 2.4))
            if balcony_col:
                _window(mb, cx - 0.75, zc - 0.05, 0.75, 2.1, rng, boarded=False, door=True, burnt=burnt)
                if f > 0:
                    collapse = rng.uniform(24, 40) if rng.random() < damage * 0.2 else 0.0
                    _balcony(mb, cx, z0, rng, collapse)
    for x in (x0 + 0.15, -x0 - 0.15):
        mb.bar((x, -0.32, 0.1), (x, -0.32, height * rng.uniform(0.55, 1.0)), 0.06, METAL, 8)

    building = mb.finish("bloque", _snow_material(), root)
    tb.stain(building, RUST, amount=0.55, scale=1.2, coverage=0.28, seed=seed, stretch_z=0.15)
    tb.stain(building, "#3E3A36", amount=0.65, scale=0.5, coverage=0.5, seed=seed + 1, stretch_z=0.3)
    tb.stain(building, "#2F2C29", amount=0.5, scale=0.18, coverage=0.32, seed=seed + 2)
    if scorch_regions:
        tb.scorch(building, scorch_regions, SOOT)
    tb.collision_box(name, (width, depth + 0.5, height), (0.0, depth / 2.0 - 0.2, height / 2.0), root)
    tb.paint({building: None}, samples=10, ao=0.5, ao_distance=0.8, cavity_dark=0.3, ground_z=0.0, seed=seed)
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
    burnt: bool = False,
) -> None:
    frame = FRAME if rng.random() < 0.6 else FRAME_WOOD
    y = -0.26
    mb.box((w, 0.02, h), (x, y, z), BURNT_GLASS if burnt else GLASS)
    bars = [((w + 0.1, 0.07, 0.07), (x, y - 0.02, z + dz)) for dz in (-h / 2.0, h / 2.0)]
    bars += [((0.07, 0.07, h), (x + dx, y - 0.02, z)) for dx in (-w / 2.0, w / 2.0)]
    if not door:
        bars.append(((0.05, 0.05, h), (x, y - 0.02, z)))
    for size, center in bars:
        if burnt and rng.random() < 0.45:
            continue  # marco quemado: faltan trozos
        mb.box(size, center, SOOT if burnt else frame, bevel=0.01, jitter=0.05)
    if burnt and rng.random() < 0.5:
        mb.box((0.05, 0.05, h * 0.7), (x + rng.uniform(-0.3, 0.3), y - 0.12, z - h * 0.3), SOOT, rotation=(rng.uniform(-30, 30), 0.0, rng.uniform(-40, 40)))
    if not door:
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


def _missing_panel(mb: tb.MeshBuilder, cx: float, zc: float, rng: random.Random) -> None:
    """Un panel que se cayó: queda el hueco oscuro, restos del borde y las varillas."""
    mb.box((COL_W - 0.3, 0.1, FLOOR_H - 0.3), (cx, 0.4, zc), INTERIOR)
    mb.box((COL_W, 0.45, 0.22), (cx, 0.0, zc - FLOOR_H / 2.0 + 0.11), CONCRETE, bevel=0.02, jitter=0.05)
    for _ in range(rng.randint(2, 4)):
        side = rng.choice((-1, 1))
        mb.box(
            (rng.uniform(0.2, 0.6), 0.25, rng.uniform(0.4, 1.4)),
            (cx + side * (COL_W / 2.0 - 0.2), -0.12, zc + rng.uniform(-0.9, 0.9)),
            PANEL,
            rotation=(rng.uniform(-6, 6), 0.0, rng.uniform(-8, 8)),
            bevel=0.02,
            jitter=0.08,
        )
    for _ in range(rng.randint(5, 8)):
        start = Vector((cx + rng.uniform(-1.3, 1.3), -0.05, zc + rng.choice((-1, 1)) * rng.uniform(0.9, 1.3)))
        end = start + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.6, -0.2), rng.uniform(-0.3, 0.3)))
        mb.bar(start, end, 0.012, REBAR, 5)


def _debris_at_base(mb: tb.MeshBuilder, cx: float, rng: random.Random) -> None:
    for _ in range(rng.randint(6, 10)):
        size = rng.uniform(0.2, 0.7)
        mb.box(
            (size * rng.uniform(1.0, 2.0), size, size * rng.uniform(0.3, 0.6)),
            (cx + rng.uniform(-1.8, 1.8), -rng.uniform(0.6, 2.8), size * 0.2),
            rng.choice((PANEL, PANEL_DARK, CONCRETE)),
            rotation=(rng.uniform(-25, 25), rng.uniform(-25, 25), rng.uniform(0, 180)),
            bevel=0.02,
            jitter=0.08,
        )


def _balcony(mb: tb.MeshBuilder, cx: float, z0: float, rng: random.Random, collapse: float) -> None:
    """Balcón; con ``collapse`` > 0 se ha desplomado y cuelga de la bisagra."""
    color = rng.choice(BALCONY_COLORS)
    depth = 1.05
    hinge_y, hinge_z = -0.25, z0

    def piece(size: tuple, center: tuple, col: str, bevel: float = 0.015, jitter: float = 0.0) -> None:
        moved = _hinged(center, hinge_y, hinge_z, collapse) if collapse else center
        mb.box(size, moved, col, rotation=(collapse, 0.0, 0.0), bevel=bevel, jitter=jitter)

    piece((COL_W - 0.3, depth, 0.14), (cx, -0.25 - depth / 2.0, z0 + 0.07), PANEL_DARK, 0.02)
    piece((COL_W - 0.3, 0.06, 0.95), (cx, -0.25 - depth + 0.03, z0 + 0.6), color, 0.015, 0.06)
    for side in (-1, 1):
        piece((0.06, depth, 0.95), (cx + side * (COL_W / 2.0 - 0.18), -0.25 - depth / 2.0, z0 + 0.6), color)
    piece((COL_W - 0.25, 0.08, 0.05), (cx, -0.25 - depth + 0.03, z0 + 1.1), METAL, 0.01)
    if collapse:
        for _ in range(4):
            start = Vector((cx + rng.uniform(-1.2, 1.2), -0.25, z0 + 0.05))
            mb.bar(start, start + Vector((0.0, -rng.uniform(0.2, 0.5), -rng.uniform(0.1, 0.4))), 0.012, REBAR, 5)
        return
    if rng.random() < 0.35:
        for k in range(4):
            mb.box((0.05, 0.05, 1.0), (cx - 1.2 + k * 0.8, -0.25 - depth + 0.03, z0 + 1.6), FRAME_WOOD, bevel=0.008)
        mb.box((COL_W - 0.35, 0.02, 0.95), (cx, -0.25 - depth + 0.05, z0 + 1.6), GLASS)
        mb.box((COL_W - 0.25, 0.08, 0.06), (cx, -0.25 - depth + 0.03, z0 + 2.12), FRAME_WOOD, bevel=0.008)


def _entrance(mb: tb.MeshBuilder, cx: float, z0: float, rng: random.Random) -> None:
    mb.box((1.3, 0.1, 2.2), (cx, -0.27, z0 + 1.1 - PLINTH_H + 0.25), DOOR, bevel=0.01, jitter=0.05)
    mb.box((0.06, 0.12, 2.2), (cx, -0.33, z0 + 1.1 - PLINTH_H + 0.25), "#2A221D")
    mb.box((2.6, 1.6, 0.16), (cx, -0.95, z0 + 2.2), PANEL_DARK, rotation=(0.0, rng.uniform(-4, 4), 0.0), bevel=0.03)
    for side in (-1, 1):
        mb.bar((cx + side * 1.15, -1.6, z0 + 2.15), (cx + side * 1.15, -1.6, 0.0), 0.05, METAL, 8)
    for k in range(3):
        mb.box((2.0, 0.35, 0.18), (cx, -0.45 - k * 0.32, 0.25 - k * 0.09), CONCRETE, bevel=0.02, jitter=0.05)
    # Barricada de tablones ante la puerta.
    for k in range(4):
        mb.box((1.6, 0.05, 0.18), (cx, -0.4, 0.5 + k * 0.42), FRAME_WOOD, rotation=(0.0, rng.uniform(-12, 12), 0.0), bevel=0.01, jitter=0.12)


# --------------------------------------------------------------------------
# Mobiliario urbano y restos
# --------------------------------------------------------------------------


def build_street_lamp(name: str, seed: int, lean: float) -> bpy.types.Object:
    root = tb.empty(f"{name}-estatico")
    mb = tb.MeshBuilder(seed=seed)
    top = Vector((math.sin(math.radians(lean)) * 7.5, 0.0, 7.5 * math.cos(math.radians(lean))))
    mb.cylinder(0.14, 7.5, top / 2.0, CONCRETE, rotation=(0.0, lean, 0.0), radius_top=0.08, segments=8)
    mb.box((0.36, 0.36, 0.5), (0.0, 0.0, 0.25), CONCRETE, bevel=0.03)
    points = [top + Vector(p) for p in ((0.0, 0.0, -0.2), (0.4, 0.0, 0.25), (1.0, 0.0, 0.4), (1.6, 0.0, 0.3))]
    for a, b in zip(points, points[1:]):
        mb.bar(a, b, 0.045, METAL, 8)
    mb.box((0.7, 0.28, 0.14), points[-1] + Vector((0.25, 0.0, -0.08)), METAL, rotation=(0.0, -8.0, 0.0), bevel=0.04)
    lamp = mb.finish("farola", _snow_material(), root)
    tb.stain(lamp, RUST, amount=0.7, scale=2.0, coverage=0.35, seed=seed)
    tb.collision_box(name, (0.36, 0.36, 7.5), (0.0, 0.0, 3.75), root)
    tb.paint({lamp: None}, samples=12, seed=seed)
    return root


def build_bench() -> bpy.types.Object:
    root = tb.empty("banco_parque-estatico")
    rng = random.Random(67)
    mb = tb.MeshBuilder(seed=67)
    for x in (-0.75, 0.75):
        mb.box((0.14, 0.5, 0.42), (x, 0.0, 0.21), CONCRETE, bevel=0.02, jitter=0.05)
        mb.box((0.12, 0.08, 0.5), (x, 0.24, 0.65), CONCRETE, rotation=(-12.0, 0.0, 0.0), bevel=0.02)
    for y in (-0.18, 0.12):
        mb.box((1.9, 0.12, 0.04), (0.0, y, 0.44), "#5A4432", rotation=(0.0, rng.uniform(-1, 1), 0.0), bevel=0.01, jitter=0.1)
    mb.box((1.1, 0.04, 0.12), (-0.35, 0.3, 0.78), "#5A4432", rotation=(-12.0, 4.0, 0.0), bevel=0.01, jitter=0.1)
    mb.box((0.9, 0.04, 0.12), (0.6, 0.0, 0.08), "#5A4432", rotation=(0.0, 3.0, 25.0), bevel=0.01, jitter=0.1)
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
        if rng.random() < 0.15:
            continue  # rama rota
        _branch(mb, rng, start.lerp(end, rng.uniform(0.6, 1.0)), child, length * rng.uniform(0.55, 0.75), radius * 0.62, depth - 1)


def build_tree(name: str, seed: int, height: float) -> bpy.types.Object:
    rng = random.Random(seed)
    root = tb.empty(f"{name}-estatico")
    mb = tb.MeshBuilder(seed=seed)
    trunk_top = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), height * 0.45))
    _branch(mb, rng, Vector((0, 0, -0.2)), trunk_top - Vector((0, 0, -0.2)), trunk_top.length + 0.2, 0.2, 0)
    for _ in range(3):
        direction = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(1.0, 2.2)))
        _branch(mb, rng, trunk_top, direction, height * 0.35, 0.12, 3)
    tree = mb.finish("arbol", _snow_material(), root)
    tb.collision_box(name, (0.4, 0.4, height * 0.45), (0.0, 0.0, height * 0.22), root)
    tb.paint({tree: None}, samples=8, ao=0.3, cavity_dark=0.1, seed=seed)
    return root


def build_car(name: str, seed: int, burnt: bool) -> bpy.types.Object:
    """Un turismo cualquiera, abandonado o quemado. No es ningún modelo real."""
    root = tb.empty(f"{name}-estatico")
    body_color = "#2E2A27" if burnt else "#5E766B"
    glass = BURNT_GLASS if burnt else GLASS
    lift = -0.16 if burnt else 0.0
    mb = tb.MeshBuilder(seed=seed)
    mb.box((4.2, 1.62, 0.62), (0.0, 0.0, 0.62 + lift), body_color, bevel=0.07, segments=2, cuts=3)
    cabin = mb.box((2.2, 1.46, 0.56), (-0.25, 0.0, 1.2 + lift), body_color, bevel=0.06, segments=2, cuts=2)
    for face in cabin:
        for vert in face.verts:
            if vert.co.z > 1.3 + lift:
                vert.co.x *= 0.86
                vert.co.y *= 0.9
                if burnt:
                    vert.co.z -= 0.06
    for x in (-1.15, 0.75):
        mb.box((0.04, 1.3, 0.4), (x + (0.18 if x > 0 else -0.12), 0.0, 1.22 + lift), glass, rotation=(0.0, -32.0 if x > 0 else 30.0, 0.0))
    for y in (-0.735, 0.735):
        mb.box((1.7, 0.02, 0.38), (-0.25, y, 1.22 + lift), glass)
    for x in (-2.1, 2.1):
        if not burnt or x < 0:
            mb.box((0.1, 1.7, 0.14), (x, 0.0, 0.48 + lift), "#5A5E60" if burnt else "#8A9092", bevel=0.03)
    for x in (-1.35, 1.35):
        for y in (-0.72, 0.72):
            radius = 0.22 if burnt else 0.33
            mb.cylinder(radius, 0.22, (x, y, radius + (0.0 if burnt else -0.03)), "#1A1A1A", rotation=(90.0, 0.0, 0.0), segments=16)
    car = mb.finish("coche", _snow_material(), root)
    tb.stain(car, RUST, amount=0.9 if burnt else 0.7, scale=1.6, coverage=0.45 if burnt else 0.32, seed=seed)
    if burnt:
        tb.stain(car, SOOT, amount=0.8, scale=1.1, coverage=0.4, seed=seed + 1)
    tb.dent(car, (2.0, -0.6, 0.7 + lift), radius=0.5, depth=0.06)
    tb.collision_box(name, (4.2, 1.7, 1.5), (0.0, 0.0, 0.75), root)
    tb.paint({car: None}, samples=14, seed=seed)
    return root


def build_swing() -> bpy.types.Object:
    root = tb.empty("columpio-estatico")
    color = "#7E3E36"
    mb = tb.MeshBuilder(seed=73)
    for x in (-1.3, 1.3):
        mb.bar((x, -0.8, 0.0), (x, 0.0, 2.3), 0.045, color, 8)
        mb.bar((x, 0.8, 0.0), (x, 0.0, 2.3), 0.045, color, 8)
    mb.bar((-1.4, 0.0, 2.3), (1.4, 0.0, 2.3), 0.05, color, 8)
    for x, tilt in ((-0.55, 0.0), (0.55, 24.0)):
        offset = math.sin(math.radians(tilt)) * 1.6
        dxs = (-0.22, 0.22) if tilt == 0.0 else (-0.22,)
        for dx in dxs:
            mb.bar((x + dx, 0.0, 2.28), (x + dx, -offset, 0.62), 0.01, METAL, 4)
        mb.box((0.5, 0.2, 0.04), (x, -offset, 0.6), "#5A4432", rotation=(tilt, 12.0 if tilt else 0.0, 0.0), bevel=0.01)
    swing = mb.finish("columpio", _snow_material(), root)
    tb.stain(swing, RUST, amount=0.8, scale=3.0, coverage=0.45, seed=73)
    tb.collision_box("columpio", (2.8, 1.6, 2.3), (0.0, 0.0, 1.15), root)
    tb.paint({swing: None}, samples=10, seed=73)
    return root


def build_container() -> bpy.types.Object:
    root = tb.empty("contenedor-estatico")
    color = "#36463A"
    mb = tb.MeshBuilder(seed=79)
    body = mb.box((1.5, 1.0, 1.05), (0.0, 0.0, 0.6), color, bevel=0.03, jitter=0.04, cuts=3)
    for face in body:
        for vert in face.verts:
            if vert.co.z < 0.3:
                vert.co.x *= 0.9
                vert.co.y *= 0.88
    mb.box((1.55, 0.55, 0.05), (0.0, -0.22, 1.16), color, rotation=(12.0, 0.0, 0.0), bevel=0.02)
    rng = random.Random(79)
    for _ in range(7):
        mb.box(
            (0.5, 0.45, 0.4),
            (rng.uniform(-1.6, 1.6), rng.uniform(-1.4, -0.6), 0.16),
            rng.choice(("#2A2827", "#3A3530", "#4A4038")),
            rotation=(rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(0, 90)),
            bevel=0.12,
            segments=2,
            jitter=0.15,
        )
    bin_obj = mb.finish("contenedor", _snow_material(), root)
    tb.stain(bin_obj, RUST, amount=0.85, scale=2.2, coverage=0.45, seed=79)
    tb.collision_box("contenedor", (1.5, 1.0, 1.2), (0.0, 0.0, 0.6), root)
    tb.paint({bin_obj: None}, samples=12, seed=79)
    return root


def build_rubble(name: str, seed: int, radius: float) -> bpy.types.Object:
    """Montón de escombros: trozos de panel, ladrillos y varillas retorcidas."""
    rng = random.Random(seed)
    root = tb.empty(f"{name}-estatico")
    mb = tb.MeshBuilder(seed=seed)
    for _ in range(int(radius * 16)):
        r = radius * math.sqrt(rng.random())
        a = rng.uniform(0.0, math.tau)
        mound = radius * 0.5 * (1.0 - (r / radius) ** 2)
        size = rng.uniform(0.15, 0.6) * (1.25 if r < radius * 0.4 else 0.8)
        mb.box(
            (size * rng.uniform(0.8, 1.7), size * rng.uniform(0.6, 1.2), size * rng.uniform(0.3, 0.8)),
            (r * math.cos(a), r * math.sin(a), max(0.04, mound * rng.uniform(0.6, 1.0))),
            rng.choice((CONCRETE, PANEL, PANEL_DARK, "#6E6A63", "#5B5650")),
            rotation=(rng.uniform(-35, 35), rng.uniform(-35, 35), rng.uniform(0, 180)),
            bevel=0.02,
            jitter=0.08,
        )
    for _ in range(int(radius * 6)):
        r = radius * math.sqrt(rng.random())
        a = rng.uniform(0.0, math.tau)
        mb.box((0.25, 0.12, 0.07), (r * math.cos(a), r * math.sin(a), 0.05 + radius * 0.3 * (1.0 - r / radius)), BRICK, rotation=(rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(0, 180)), bevel=0.01, jitter=0.12)
    for _ in range(int(radius * 3)):
        start = Vector((rng.uniform(-0.6, 0.6) * radius, rng.uniform(-0.6, 0.6) * radius, rng.uniform(0.1, radius * 0.35)))
        end = start + Vector((rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7), rng.uniform(0.2, 0.9)))
        mb.bar(start, end, 0.012, REBAR, 5)
    rubble = mb.finish("escombros", _snow_material(), root)
    tb.stain(rubble, SOOT, amount=0.5, scale=1.5, coverage=0.3, seed=seed)
    # La colisión es un montículo que se sube andando (laderas de unos 40°): un
    # tronco de cono con la punta. Una caja dejaba paredes invisibles lejos del
    # borde, en las esquinas, y lo que caía cerca se quedaba flotando.
    hull = tb.MeshBuilder(seed=seed)
    hull.cylinder(radius * 0.92, radius * 0.36, (0.0, 0.0, radius * 0.18), CONCRETE, radius_top=radius * 0.5, segments=12)
    hull.box((0.1, 0.1, 0.04), (0.0, 0.0, radius * 0.47), CONCRETE)
    hull.finish(f"{name}-colconvexa", None, root)
    tb.paint({rubble: None}, samples=10, ao=0.55, seed=seed)
    return root


def build_power_lines() -> bpy.types.Object:
    """Dos postes con los cables vencidos; uno roto cuelga hasta el suelo."""
    rng = random.Random(107)
    root = tb.empty("postes_cables-estatico")
    mb = tb.MeshBuilder(seed=107)
    span = 18.0
    tops = []
    for x, lean in ((-span / 2.0, 0.0), (span / 2.0, 7.0)):
        top = Vector((x + math.sin(math.radians(lean)) * 8.0, 0.0, 8.0 * math.cos(math.radians(lean))))
        mb.cylinder(0.13, 8.0, (Vector((x, 0.0, 0.0)) + top) / 2.0, CONCRETE, rotation=(0.0, lean, 0.0), radius_top=0.09, segments=8)
        mb.box((0.12, 1.8, 0.12), top - Vector((0.0, 0.0, 0.4)), METAL, rotation=(lean, 0.0, 0.0), bevel=0.01)
        for y in (-0.8, 0.0, 0.8):
            mb.cylinder(0.04, 0.14, top + Vector((0.0, y, -0.28)), "#8F8A7E", segments=8)
        tops.append(top)
    for y in (-0.8, 0.8):
        a, b = tops[0] + Vector((0.0, y, -0.2)), tops[1] + Vector((0.0, y, -0.2))
        points = [a.lerp(b, k / 12.0) - Vector((0.0, 0.0, 1.6 * (1.0 - (2.0 * k / 12.0 - 1.0) ** 2))) for k in range(13)]
        for p, q in zip(points, points[1:]):
            mb.bar(p, q, 0.012, "#1E1C1B", 4)
    hang = tops[0] + Vector((0.0, 0.0, -0.2))
    points = [hang, hang + Vector((1.5, 0.0, -2.5)), hang + Vector((2.4, 0.0, -5.5)), Vector((hang.x + 2.6, 0.0, 0.05)), Vector((hang.x + 4.5, 0.6, 0.03)), Vector((hang.x + 5.5, -0.4, 0.03))]
    for p, q in zip(points, points[1:]):
        mb.bar(p, q, 0.012, "#1E1C1B", 4)
    poles = mb.finish("postes", _snow_material(), root)
    tb.stain(poles, RUST, amount=0.5, scale=2.0, coverage=0.3, seed=rng.randint(0, 99))
    tb.collision_box("poste_a", (0.3, 0.3, 8.0), (-span / 2.0, 0.0, 4.0), root)
    tb.paint({poles: None}, samples=8, seed=107)
    return root


def build_kiosk() -> bpy.types.Object:
    """Quiosco de prensa de chapa y cristal, cerrado desde hace años.

    El frente (la ventanilla y su repisa) mira hacia -Y; la puerta está detrás.
    Dentro hay una caja oscura para que los cristales rotos den a un interior
    en sombra.
    """
    rng = random.Random(107)
    root = tb.empty("quiosco-estatico")
    width, depth = 2.4, 1.8
    base_z, sill_z, head_z, top_z = 0.14, 1.0, 2.1, 2.46
    wall, post = 0.04, 0.07
    paint_color, paint_dark = "#5F7F86", "#4C676E"
    mb = tb.MeshBuilder(seed=107)

    mb.box((width + 0.25, depth + 0.25, base_z), (0.0, 0.0, base_z / 2.0), CONCRETE, bevel=0.02, cuts=3, jitter=0.05)
    mb.box((width - 0.1, depth - 0.1, head_z - base_z), (0.0, 0.0, (head_z + base_z) / 2.0), "#24262A")

    def side(axis: int, sign: float, bays: list[str]) -> None:
        """Una pared: ``axis`` 0 corre a lo largo de X (frente y trasera); 1, a lo largo de Y."""
        length = width if axis == 0 else depth
        fixed = sign * (depth if axis == 0 else width) / 2.0
        bay = length / len(bays)

        def at(u: float, z: float, out: float = 0.0) -> tuple[float, float, float]:
            return (u, fixed + sign * out, z) if axis == 0 else (fixed + sign * out, u, z)

        def dims(along: float, thick: float, tall: float) -> tuple[float, float, float]:
            return (along, thick, tall) if axis == 0 else (thick, along, tall)

        def turn(angle: float) -> tuple[float, float, float]:
            return (0.0, angle, 0.0) if axis == 0 else (angle, 0.0, 0.0)

        for index in range(len(bays) + 1):
            u = -length / 2.0 + index * bay
            mb.box(dims(post, post, head_z - base_z), at(u, (head_z + base_z) / 2.0), FRAME, bevel=0.008, jitter=0.05)
        mb.box(dims(length, post + 0.02, 0.06), at(0.0, sill_z), FRAME, bevel=0.01, cuts=3, jitter=0.04)
        for index, kind in enumerate(bays):
            u = -length / 2.0 + (index + 0.5) * bay
            inner = bay - post
            if kind == "door":
                mb.box(dims(inner, wall, head_z - base_z - 0.04), at(u, (head_z + base_z) / 2.0, -0.005), paint_dark, bevel=0.01, cuts=2, jitter=0.05)
                mb.box(dims(inner - 0.14, 0.012, 0.6), at(u, 0.62, 0.02), paint_color, bevel=0.006)
                mb.box(dims(inner - 0.14, 0.012, 0.7), at(u, 1.52, 0.02), paint_color, bevel=0.006)
                mb.box(dims(0.03, 0.05, 0.14), at(u + inner / 2.0 - 0.09, 1.08, 0.04), METAL, bevel=0.006)
                mb.box(dims(0.07, 0.03, 0.09), at(u + inner / 2.0 - 0.09, 0.98, 0.05), RUST, rotation=turn(rng.uniform(-10.0, 10.0)), bevel=0.01)
                continue
            mb.box(dims(inner, wall, sill_z - base_z), at(u, (sill_z + base_z) / 2.0, -0.005), paint_color, rotation=turn(rng.uniform(-0.6, 0.6)), bevel=0.012, cuts=2, jitter=0.07)
            mb.box(dims(inner - 0.12, 0.012, sill_z - base_z - 0.16), at(u, (sill_z + base_z) / 2.0, 0.018), paint_dark, bevel=0.006, jitter=0.05)
            glass_h = head_z - sill_z - 0.03
            glass_z = (head_z + sill_z) / 2.0 + 0.015
            if kind == "glass":
                mb.box(dims(inner, 0.016, glass_h), at(u, glass_z), GLASS, jitter=0.12)
                mb.box(dims(inner, 0.03, 0.03), at(u, sill_z + glass_h * 0.38), FRAME, bevel=0.005, jitter=0.05)
                # Portadas y avisos pegados por dentro, amarillos de años.
                for _ in range(rng.randint(0, 2)):
                    mb.box(
                        dims(rng.uniform(0.16, 0.24), 0.006, rng.uniform(0.2, 0.3)),
                        at(u + rng.uniform(-0.12, 0.12), glass_z + rng.uniform(-0.05, 0.32), 0.012),
                        rng.choice(("#CFC6AE", "#BDB294", "#D8D0B8")),
                        rotation=turn(rng.uniform(-7.0, 7.0)),
                        jitter=0.06,
                    )
            elif kind == "boards":
                mb.box(dims(inner, 0.02, glass_h), at(u, glass_z), "#8B7355", cuts=2, jitter=0.08)
                for z, tilt in ((glass_z + 0.25, rng.uniform(-6.0, 6.0)), (glass_z - 0.22, rng.uniform(-6.0, 6.0))):
                    mb.box(dims(bay + 0.06, 0.022, 0.11), at(u, z, 0.03), FRAME_WOOD, rotation=turn(tilt), bevel=0.006, jitter=0.1)
            elif kind == "broken":
                # Quedan los picos del cristal en las esquinas.
                for du, dz, angle in ((-1.0, -1.0, 38.0), (1.0, 1.0, 30.0), (1.0, -1.0, -42.0), (-1.0, 1.0, -25.0)):
                    mb.box(dims(0.34, 0.012, 0.2), at(u + du * (inner / 2.0 - 0.07), glass_z + dz * (glass_h / 2.0 - 0.06)), GLASS, rotation=turn(angle), jitter=0.12)
            elif kind == "window":
                # Ventanilla: cristal arriba, hueco abajo y repisa para el cambio.
                mb.box(dims(inner, 0.016, glass_h * 0.58), at(u, head_z - glass_h * 0.29 - 0.0), GLASS, jitter=0.1)
                mb.box(dims(inner, 0.03, 0.035), at(u, sill_z + glass_h * 0.42 + 0.03), FRAME, bevel=0.006)
                mb.box(dims(bay + 0.2, 0.34, 0.035), at(u, sill_z + 0.045, 0.17), FRAME, rotation=turn(0.0), bevel=0.012, cuts=2, jitter=0.05)
                for du in (-1.0, 1.0):
                    mb.box(dims(0.03, 0.26, 0.03), at(u + du * (bay / 2.0), sill_z - 0.1, 0.13), METAL, rotation=((-38.0 * sign, 0.0, 0.0) if axis == 0 else (0.0, 38.0 * sign, 0.0)), bevel=0.004)

    side(0, -1.0, ["glass", "window", "boards", "glass"])
    side(0, 1.0, ["glass", "door", "broken", "glass"])
    side(1, -1.0, ["glass", "broken", "boards"])
    side(1, 1.0, ["boards", "glass", "glass"])

    # Friso del rótulo y tejado en voladizo, algo caído hacia atrás.
    fascia = top_z - head_z
    for axis, sign in ((0, -1.0), (0, 1.0), (1, -1.0), (1, 1.0)):
        size = (width + 0.1, 0.06, fascia) if axis == 0 else (0.06, depth + 0.1, fascia)
        center = (0.0, sign * (depth / 2.0 + 0.02), head_z + fascia / 2.0) if axis == 0 else (sign * (width / 2.0 + 0.02), 0.0, head_z + fascia / 2.0)
        mb.box(size, center, paint_color, bevel=0.012, cuts=3, jitter=0.05)
    mb.box((width - 0.5, 0.03, fascia - 0.1), (0.0, -depth / 2.0 - 0.055, head_z + fascia / 2.0), "#D8D0B8", rotation=(0.0, rng.uniform(-1.2, 1.2), 0.0), bevel=0.006, cuts=2)
    x = -width / 2.0 + 0.42
    while x < width / 2.0 - 0.5:
        letter = rng.uniform(0.09, 0.17)
        mb.box((letter, 0.012, rng.uniform(0.11, 0.15)), (x + letter / 2.0, -depth / 2.0 - 0.073, head_z + fascia / 2.0), paint_dark, jitter=0.15)
        x += letter + rng.uniform(0.035, 0.07)
    mb.box((width + 0.7, depth + 0.7, 0.09), (0.0, 0.04, top_z + 0.05), "#6A6F70", rotation=(2.2, 0.0, rng.uniform(-0.4, 0.4)), bevel=0.02, cuts=4, jitter=0.04)
    mb.box((width + 0.2, depth + 0.2, 0.08), (0.0, 0.03, top_z + 0.13), "#5C6162", rotation=(2.2, 0.0, 0.0), bevel=0.02, cuts=3)
    # Chimenea de la estufilla y un cajón de periódicos junto a la puerta.
    mb.bar((width / 2.0 - 0.35, depth / 2.0 - 0.3, top_z + 0.1), (width / 2.0 - 0.35, depth / 2.0 - 0.3, top_z + 0.62), 0.05, RUST, 10)
    mb.cylinder(0.085, 0.05, (width / 2.0 - 0.35, depth / 2.0 - 0.3, top_z + 0.65), RUST, radius_top=0.02, segments=10)
    mb.box((0.55, 0.38, 0.32), (-width / 2.0 + 0.45, depth / 2.0 + 0.36, 0.16), FRAME_WOOD, rotation=(0.0, 0.0, rng.uniform(-12.0, 12.0)), bevel=0.012, jitter=0.08)

    kiosk = mb.finish("quiosco", _snow_material(), root)
    tb.stain(kiosk, RUST, amount=0.75, scale=2.4, coverage=0.3, seed=107)
    tb.stain(kiosk, "#3C4144", amount=0.5, scale=3.0, coverage=0.35, seed=108, stretch_z=0.25)
    tb.dent(kiosk, (width / 2.0, -0.2, 0.6), radius=0.35, depth=0.03)
    tb.wobble(kiosk, amount=0.006, scale=1.5, seed=107)
    tb.collision_box("quiosco", (width + 0.1, depth + 0.1, top_z + 0.15), (0.0, 0.0, (top_z + 0.15) / 2.0), root)
    tb.collision_box("quiosco_repisa", (0.8, 0.34, 0.05), (-0.3, -depth / 2.0 - 0.17, sill_z + 0.045), root)
    tb.paint({kiosk: None}, samples=14, ao_distance=0.4, seed=107)
    return root


def build_ground() -> bpy.types.Object:
    """El suelo del patio: nieve vieja con senderos de barro, montones y asfalto."""
    rng = random.Random(83)
    root = tb.empty("suelo_patio-estatico")
    mb = tb.MeshBuilder(seed=83)
    size = 46.0
    mb.box((size, size, 0.3), (0.0, 0.0, -0.15), SNOW, cuts=24)
    ground = mb.finish("nieve", _snow_material(), root)
    tb.wobble(ground, amount=0.05, scale=0.35, seed=82)
    tb.stain(ground, DIRTY_SNOW, amount=0.45, scale=0.12, coverage=0.4, seed=81)
    tb.stain(ground, SOOT, amount=0.25, scale=0.35, coverage=0.1, seed=80)
    path = tb.MeshBuilder(seed=84)
    for k in range(16):
        t = k / 15.0
        x = -15.0 + t * 28.0 + math.sin(t * 5.0) * 1.2
        y = 6.0 - t * 15.0
        path.box((2.6, 2.3, 0.06), (x, y, 0.01), DIRTY_SNOW, rotation=(0.0, 0.0, -28.0 + rng.uniform(-6, 6)), bevel=0.2, segments=2, jitter=0.12)
    for _ in range(9):
        path.box((rng.uniform(1.2, 3.0), rng.uniform(0.9, 1.8), 0.03), (rng.uniform(-14, 14), rng.uniform(-6, 9), 0.02), ASPHALT, rotation=(0.0, 0.0, rng.uniform(0, 90)), bevel=0.15, segments=2, jitter=0.1)
    for k in range(8):
        path.box((2.0, 0.25, 0.18), (-10.0 + k * 2.1, -7.4, 0.05), CONCRETE, rotation=(0.0, 0.0, rng.uniform(-2, 2)), bevel=0.03, jitter=0.06)
    details = path.finish("sendero", _snow_material(), root)
    tb.wobble(details, amount=0.06, scale=0.5, seed=83)
    mounds = tb.MeshBuilder(seed=85)
    for _ in range(11):
        mounds.sphere(
            1.0,
            (rng.uniform(-16, 16), rng.uniform(-6, 9), -0.15),
            SNOW,
            segments=20,
            scale=(rng.uniform(1.2, 2.6), rng.uniform(0.9, 1.8), rng.uniform(0.45, 0.9)),
            jitter=0.05,
        )
    heaps = mounds.finish("montones", _snow_material(), root)
    tb.wobble(heaps, amount=0.22, scale=0.8, seed=85)
    tb.stain(heaps, DIRTY_SNOW, amount=0.35, scale=0.5, coverage=0.35, seed=86)
    tb.collision_box("suelo_patio", (size, size, 0.3), (0.0, 0.0, -0.15), root)
    tb.paint({ground: None, details: None, heaps: None}, samples=8, ao=0.35, ao_distance=0.6, ground_z=None, mottling=0.05, seed=83)
    return root


# --------------------------------------------------------------------------
# Horizonte: ruinas y la Zona Cero
# --------------------------------------------------------------------------


def _tower(mb: tb.MeshBuilder, rng: random.Random, x: float, y: float, width: float, floors: int, broken: float) -> None:
    """Torre lejana: bloque con filas de ventanas y la parte de arriba rota."""
    floor_h = 3.0
    height = floors * floor_h
    intact = height * (1.0 - broken)
    mb.box((width, 14.0, intact), (x, y, intact / 2.0), "#8A8A8A")
    for f in range(int(intact / floor_h)):
        mb.box((width * 0.92, 0.3, 0.9), (x, y - 7.1, f * floor_h + 1.6), "#2A2A2A")
    teeth = rng.randint(3, 6)
    for k in range(teeth):
        tooth_w = width / teeth
        tooth_h = rng.uniform(0.0, height - intact)
        if tooth_h > 1.0:
            mb.box((tooth_w * rng.uniform(0.6, 1.0), 14.0 * rng.uniform(0.5, 1.0), tooth_h), (x - width / 2.0 + tooth_w * (k + 0.5), y, intact + tooth_h / 2.0), "#8A8A8A", rotation=(rng.uniform(-4, 4), rng.uniform(-6, 6), 0.0))


def build_skyline() -> bpy.types.Object:
    """Las ruinas de la ciudad en el horizonte, en dos capas de profundidad."""
    rng = random.Random(113)
    root = tb.empty("ruinas_horizonte")
    for layer, (radius, count) in enumerate(((95.0, 9), (150.0, 12))):
        mb = tb.MeshBuilder(seed=113 + layer)
        for k in range(count):
            angle = math.radians(-75.0 + 150.0 * (k + rng.uniform(0.2, 0.8)) / count)
            x, y = math.sin(angle) * radius, math.cos(angle) * radius
            _tower(mb, rng, x, y, rng.uniform(14, 34), rng.randint(9 if layer == 0 else 14, 18 if layer == 0 else 26), rng.uniform(0.1, 0.5))
        tb.material("lejano", "#8A8A8A")
        mb.finish(f"ruinas_capa_{layer}", tb.material(f"lejano_{layer}", "#8A8A8A"), root)
    return root


def build_ground_zero() -> bpy.types.Object:
    """El edificio partido por la mitad junto al cráter: el final del juego.

    Se ve desde lejos, siempre en el horizonte. Una mitad sigue en pie, con los
    forjados al aire y varillas colgando; la otra es una rampa de escombros.
    """
    rng = random.Random(127)
    root = tb.empty("zona_cero")
    mb = tb.MeshBuilder(seed=127)
    floors, floor_h, width = 32, 3.2, 26.0
    for f in range(floors):
        z = f * floor_h
        cut = width * (0.5 - 0.35 * (f / floors)) + rng.uniform(-1.5, 1.5)
        mb.box((cut, 18.0, floor_h - 0.5), (-width / 2.0 + cut / 2.0, 0.0, z + floor_h / 2.0), "#8A8A8A")
        mb.box((cut + rng.uniform(0.5, 3.0), 18.5, 0.45), (-width / 2.0 + cut / 2.0 + 0.8, 0.0, z + floor_h - 0.2), "#B0B0B0")
        mb.box((cut * 0.9, 0.3, 1.0), (-width / 2.0 + cut / 2.0, -9.2, z + 1.6), "#2A2A2A")
    for k in range(10):
        mb.box((rng.uniform(4, 9), rng.uniform(6, 14), rng.uniform(2, 7)), (rng.uniform(-2, 16), rng.uniform(-8, 8), rng.uniform(0, 6)), "#8A8A8A", rotation=(rng.uniform(-20, 20), rng.uniform(-25, 25), rng.uniform(0, 90)))
    mb.finish("zona_cero", tb.material("lejano_zona_cero", "#8A8A8A"), root)
    return root


def models() -> dict:
    return {
        "bloque_paneles": lambda: build_block("bloque_paneles", 2, 5, 89, damage=0.45),
        "bloque_paneles_b": lambda: build_block("bloque_paneles_b", 1, 5, 97, damage=0.6),
        "farola": lambda: build_street_lamp("farola", 61, 0.0),
        "farola_torcida": lambda: build_street_lamp("farola_torcida", 63, 11.0),
        "banco_parque": build_bench,
        "arbol_desnudo": lambda: build_tree("arbol_desnudo", 101, 7.0),
        "arbol_desnudo_b": lambda: build_tree("arbol_desnudo_b", 103, 5.0),
        "coche": lambda: build_car("coche", 71, burnt=False),
        "coche_quemado": lambda: build_car("coche_quemado", 72, burnt=True),
        "columpio": build_swing,
        "contenedor": build_container,
        "escombros": lambda: build_rubble("escombros", 109, 2.2),
        "escombros_grande": lambda: build_rubble("escombros_grande", 111, 3.5),
        "postes_cables": build_power_lines,
        "quiosco": build_kiosk,
        "suelo_patio": build_ground,
        "ruinas_horizonte": build_skyline,
        "zona_cero": build_ground_zero,
    }
