"""El taller: los instrumentos con los que se procesa el botín.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. El
frente de cada instrumento mira hacia -Y (en Godot, hacia +Z).

Las piezas que se mueven en el juego (agujas, tapas) son nodos propios con el
origen en su eje de giro: ver ``tb.set_origin``.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

INK = "#1B1A22"
ENAMEL_BLUE = "#7C93A0"
ENAMEL_DARK = "#5E7480"
DIAL_CREAM = "#E9E2CC"
ALUMINIUM = "#A9ADA8"
ALUMINIUM_DARK = "#8C918D"
STEEL_DARK = "#3F4A4F"
BRASS = "#B59A5A"
RUBBER = "#2A2725"
RUST = "#8E4A2F"
ENAMEL_WHITE = "#D5D0C0"
FRAME_GREEN = "#55615A"
WATER = "#4F6B62"
SIGNAL_RED = "#C8323C"

# Báscula: la aguja recorre SCALE_SWEEP grados a cada lado del centro.
SCALE_SWEEP = 32.0


def _sector(radius: float, half_angle: float, neck: float, steps: int = 14) -> list[tuple[float, float]]:
    """Contorno en abanico: un cuello estrecho abajo y un arco arriba (antihorario)."""
    points = [(-neck, 0.0), (neck, 0.0)]
    for i in range(steps + 1):
        angle = math.radians(half_angle - 2.0 * half_angle * i / steps)
        points.append((radius * math.sin(angle), radius * math.cos(angle)))
    return points


def build_scale() -> bpy.types.Object:
    """Báscula de mostrador de dos platos, con la esfera en abanico.

    La aguja es el nodo ``aguja``. En reposo marca el cero, a la izquierda
    vista desde el frente; a fondo de escala ha girado 2 × SCALE_SWEEP grados
    hacia la derecha (en Godot, ``rotation.z`` de 0 a -64°).
    """
    rng = random.Random(61)
    root = tb.empty("bascula-estatico")
    width, depth, base_h = 0.62, 0.27, 0.105
    # El abanico va sobre una columna, por encima de los platos: así no se tocan.
    pivot = (0.0, 0.0, base_h + 0.2)
    head_r, head_t = 0.36, 0.085
    pan_x, bowl = 0.235, 0.87
    front = -head_t / 2.0

    mb = tb.MeshBuilder(seed=61)
    # Cuerpo de fundición esmaltada, sobre cuatro patas roscadas.
    mb.box((width, depth, base_h - 0.02), (0.0, 0.0, 0.02 + (base_h - 0.02) / 2.0), ENAMEL_BLUE, bevel=0.022, segments=3, cuts=6)
    mb.box((width - 0.07, depth - 0.06, 0.02), (0.0, 0.0, base_h + 0.006), ENAMEL_DARK, bevel=0.008, segments=2)
    for x in (-width / 2.0 + 0.05, width / 2.0 - 0.05):
        for y in (-depth / 2.0 + 0.045, depth / 2.0 - 0.045):
            mb.lathe(((0.0, 0.0), (0.024, 0.0), (0.026, 0.006), (0.016, 0.012), (0.016, 0.024), (0.0, 0.024)), (x, y, 0.0), STEEL_DARK, segments=12)
    # Placa del fabricante y tornillo de nivelación.
    mb.box((0.11, 0.004, 0.034), (-0.13, -depth / 2.0 - 0.001, 0.058), BRASS, rotation=(0.0, 0.0, rng.uniform(-0.8, 0.8)), bevel=0.0015)
    for x in (-0.176, -0.084):
        mb.cylinder(0.004, 0.004, (x, -depth / 2.0 - 0.004, 0.058), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=8)
    mb.lathe(((0.0, 0.0), (0.02, 0.0), (0.022, 0.004), (0.022, 0.016), (0.018, 0.02), (0.0, 0.02)), (0.2, -depth / 2.0 - 0.001, 0.055), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=14)

    # Cabezal en abanico, con cerco y esfera por las dos caras (la del cliente también).
    neck_z = base_h + 0.01
    column_top = pivot[2] - 0.04
    mb.box((0.16, head_t + 0.03, 0.05), (0.0, 0.0, neck_z + 0.02), ENAMEL_BLUE, bevel=0.012, segments=2)
    mb.box((0.094, head_t - 0.012, column_top - neck_z), (0.0, 0.0, (column_top + neck_z) / 2.0), ENAMEL_BLUE, bevel=0.012, segments=2, cuts=2)
    mb.prism(_sector(head_r, SCALE_SWEEP + 9.0, 0.06), head_t, (0.0, 0.0, pivot[2] - 0.045), ENAMEL_BLUE, rotation=(90.0, 0.0, 0.0), bevel=0.012, segments=2)
    for side in (-1.0, 1.0):
        mb.prism(
            _sector(head_r - 0.028, SCALE_SWEEP + 5.5, 0.036),
            0.004,
            (0.0, side * (head_t / 2.0 + 0.001), pivot[2] - 0.018),
            DIAL_CREAM,
            rotation=(90.0, 0.0, 0.0),
        )
        # Marcas: una larga cada cinco.
        for index in range(41):
            angle = -SCALE_SWEEP + 2.0 * SCALE_SWEEP * index / 40.0
            long_mark = index % 5 == 0
            length = 0.04 if long_mark else 0.02
            radius = head_r - 0.06 - length / 2.0
            a = math.radians(angle)
            mb.box(
                (0.0045 if long_mark else 0.0025, 0.002, length),
                (radius * math.sin(a), side * (head_t / 2.0 + 0.0035), pivot[2] + radius * math.cos(a)),
                INK,
                rotation=(0.0, angle, 0.0),
            )
        # Franja de la zona de sobrecarga, al final de la escala.
        for index in range(4):
            angle = SCALE_SWEEP - 1.2 - index * 1.6
            a = math.radians(angle)
            radius = head_r - 0.118
            mb.box((0.009, 0.002, 0.014), (radius * math.sin(a), side * (head_t / 2.0 + 0.0035), pivot[2] + radius * math.cos(a)), "#8A5A3B", rotation=(0.0, angle, 0.0))
        mb.cylinder(0.02, 0.008, (0.0, side * (head_t / 2.0 + 0.004), pivot[2]), ENAMEL_DARK, rotation=(90.0, 0.0, 0.0), segments=14)
    body = mb.finish("cuerpo", tb.material("metal", ENAMEL_BLUE), root)
    tb.stain(body, RUST, amount=0.7, scale=5.0, coverage=0.2, seed=61)
    tb.stain(body, "#4E5A5E", amount=0.35, scale=9.0, coverage=0.3, seed=62)
    tb.wobble(body, amount=0.0012, scale=5.0, seed=61)

    # Platos: a la izquierda el de las pesas, plano; a la derecha el cuenco del género.
    pans = tb.MeshBuilder(seed=67)
    pan_z = base_h + 0.085
    for x, tilt in ((-pan_x, rng.uniform(-1.0, 1.0)), (pan_x, rng.uniform(-1.0, 1.0))):
        pans.lathe(((0.0, 0.0), (0.03, 0.0), (0.03, 0.006), (0.013, 0.012), (0.013, 0.06), (0.0, 0.06)), (x, 0.0, base_h + 0.015), STEEL_DARK, segments=12)
        for angle in (0.0, 90.0):
            pans.box((0.15, 0.022, 0.012), (x, 0.0, pan_z - 0.012), STEEL_DARK, rotation=(0.0, tilt, angle), bevel=0.004)
    pans.lathe(
        ((0.0, 0.0), (0.098, 0.0), (0.108, 0.004), (0.108, 0.012), (0.1, 0.015), (0.092, 0.011), (0.0, 0.011)),
        (-pan_x, 0.0, pan_z - 0.006),
        ALUMINIUM,
        segments=28,
        jitter=0.03,
    )
    pans.lathe(
        [
            (radius * bowl, z)
            for radius, z in (
                (0.0, 0.0), (0.05, 0.001), (0.1, 0.014), (0.135, 0.04), (0.148, 0.064), (0.154, 0.066),
                (0.153, 0.07), (0.145, 0.068), (0.13, 0.044), (0.096, 0.02), (0.048, 0.007), (0.0, 0.006),
            )
        ],
        (pan_x, 0.0, pan_z - 0.006),
        ALUMINIUM,
        segments=28,
        sharp_angle=60.0,
        jitter=0.03,
    )
    pans_obj = pans.finish("platos", tb.material("metal", ALUMINIUM), root)
    tb.stain(pans_obj, ALUMINIUM_DARK, amount=0.6, scale=7.0, coverage=0.35, seed=67)
    tb.dent(pans_obj, (pan_x + 0.1, -0.08, pan_z + 0.05), radius=0.06, depth=0.006)

    # Aguja (por las dos caras), con contrapeso. Se construye marcando el cero.
    needle = tb.MeshBuilder(seed=71)
    for side in (-1.0, 1.0):
        y = side * (head_t / 2.0 + 0.008)
        zero = -SCALE_SWEEP
        a = math.radians(zero)
        length = head_r - 0.075
        needle.box((0.006, 0.002, length), (pivot[0] + length / 2.0 * math.sin(a), y, pivot[2] + length / 2.0 * math.cos(a)), INK, rotation=(0.0, zero, 0.0))
        needle.box((0.012, 0.002, 0.045), (pivot[0] - 0.02 * math.sin(a), y, pivot[2] - 0.02 * math.cos(a)), INK, rotation=(0.0, zero, 0.0))
        needle.cylinder(0.011, 0.006, (pivot[0], y, pivot[2]), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=12)
    needle_obj = needle.finish("aguja", tb.material("metal", INK), root)
    tb.set_origin(needle_obj, pivot)

    tb.collision_box("bascula_base", (2.0 * pan_x + 0.28, depth + 0.04, base_h + 0.15), (0.0, 0.0, (base_h + 0.15) / 2.0), root)
    tb.collision_box("bascula_esfera", (0.46, head_t + 0.02, head_r + 0.045), (0.0, 0.0, pivot[2] - 0.045 + (head_r + 0.045) / 2.0), root)
    tb.paint({body: None, pans_obj: None, needle_obj: None}, ao_distance=0.12, seed=61)
    return root


def build_decon_sink() -> bpy.types.Object:
    """Pila de descontaminación: cubeta de chapa esmaltada sobre patas de ángulo.

    Nodos propios: ``llave`` (la cruceta del grifo, que gira sobre su eje Z: en
    Godot, ``rotation.y``) y ``agua`` (la lámina de agua, con el material
    "agua", para teñirla o vaciarla desde el juego).
    """
    rng = random.Random(173)
    root = tb.empty("pila_descontaminacion-estatico")
    width, depth, basin_h, rim_z = 0.76, 0.52, 0.3, 0.9
    wall = 0.022
    floor_z = rim_z - basin_h
    half_w, half_d = width / 2.0, depth / 2.0

    mb = tb.MeshBuilder(seed=173)
    # Cubeta: cuatro paredes, fondo y el borde vuelto.
    for y in (-half_d + wall / 2.0, half_d - wall / 2.0):
        mb.box((width, wall, basin_h), (0.0, y, floor_z + basin_h / 2.0), ENAMEL_WHITE, bevel=0.006, cuts=4, jitter=0.03)
    for x in (-half_w + wall / 2.0, half_w - wall / 2.0):
        mb.box((wall, depth - 2.0 * wall + 0.004, basin_h), (x, 0.0, floor_z + basin_h / 2.0), ENAMEL_WHITE, bevel=0.006, cuts=4, jitter=0.03)
    mb.box((width, depth, wall), (0.0, 0.0, floor_z + wall / 2.0), ENAMEL_WHITE, bevel=0.006, cuts=4)
    for y in (-half_d, half_d):
        mb.bar((-half_w - 0.004, y, rim_z), (half_w + 0.004, y, rim_z), 0.013, ENAMEL_WHITE, 8)
    for x in (-half_w, half_w):
        mb.bar((x, -half_d - 0.004, rim_z), (x, half_d + 0.004, rim_z), 0.013, ENAMEL_WHITE, 8)
    # Frontal contra las salpicaduras, con una placa de aviso sin rotular.
    mb.box((width, 0.016, 0.36), (0.0, half_d + 0.006, rim_z + 0.17), ENAMEL_WHITE, rotation=(rng.uniform(-0.6, 0.6), 0.0, 0.0), bevel=0.006, cuts=4, jitter=0.03)
    mb.box((0.11, 0.004, 0.11), (-0.22, half_d - 0.004, rim_z + 0.22), "#9C8546", rotation=(0.0, 45.0 + rng.uniform(-3.0, 3.0), 0.0), bevel=0.002)
    for x in (-half_w + 0.04, half_w - 0.04):
        mb.cylinder(0.008, 0.006, (x, half_d - 0.004, rim_z + 0.31), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=8)
    # Patas de ángulo, largueros y una balda de listones para el cubo.
    for x in (-half_w + 0.03, half_w - 0.03):
        for y in (-half_d + 0.03, half_d - 0.03):
            mb.box((0.04, 0.006, floor_z), (x, y + math.copysign(0.017, y), floor_z / 2.0), FRAME_GREEN, bevel=0.0015, cuts=2)
            mb.box((0.006, 0.04, floor_z), (x + math.copysign(0.017, x), y, floor_z / 2.0), FRAME_GREEN, bevel=0.0015, cuts=2)
    for y in (-half_d + 0.03, half_d - 0.03):
        mb.box((width - 0.04, 0.008, 0.04), (0.0, y, 0.16), FRAME_GREEN, bevel=0.002, cuts=2)
    for index in range(5):
        y = -half_d + 0.07 + index * (depth - 0.14) / 4.0
        mb.box((width - 0.08, 0.06, 0.018), (0.0, y, 0.19), rng.choice(("#8A5A3B", "#7A4E33", "#6E4A32")), rotation=(rng.uniform(-1.0, 1.0), 0.0, rng.uniform(-0.6, 0.6)), bevel=0.004, jitter=0.08)
    # Desagüe con su sifón, hacia la pared.
    mb.lathe(((0.03, 0.0), (0.03, 0.02), (0.024, 0.03)), (0.0, 0.0, floor_z - 0.03), STEEL_DARK, rotation=(180.0, 0.0, 0.0), segments=12)
    mb.tube(
        tb.smooth_path(((0.0, 0.0, floor_z - 0.02), (0.0, 0.0, floor_z - 0.13), (0.0, 0.04, floor_z - 0.2), (0.0, 0.1, floor_z - 0.17), (0.0, 0.14, floor_z - 0.11), (0.0, 0.2, floor_z - 0.1), (0.0, half_d + 0.03, floor_z - 0.1)), 4),
        0.022,
        STEEL_DARK,
        segments=10,
    )
    # Grifo de cuello de cisne.
    tap = Vector((0.16, half_d - 0.002, rim_z + 0.2))
    mb.lathe(((0.0, 0.0), (0.03, 0.0), (0.03, 0.008), (0.018, 0.014), (0.0, 0.014)), tap, BRASS, rotation=(90.0, 0.0, 0.0), segments=12)
    mb.tube(
        tb.smooth_path((tap, tap + Vector((0.0, -0.05, 0.012)), tap + Vector((0.0, -0.13, 0.05)), tap + Vector((0.0, -0.2, 0.035)), tap + Vector((0.0, -0.225, -0.025)), tap + Vector((0.0, -0.225, -0.06))), 4),
        0.012,
        BRASS,
        segments=10,
    )
    mb.cylinder(0.014, 0.05, tap + Vector((0.0, -0.035, 0.03)), BRASS, segments=10)
    # Cepillo de raíces, apoyado en el borde.
    brush = Vector((half_w - 0.14, -half_d + 0.01, rim_z + 0.026))
    mb.box((0.17, 0.05, 0.018), brush + Vector((0.0, 0.0, 0.012)), "#8A5A3B", rotation=(0.0, 0.0, 12.0), bevel=0.006)
    mb.box((0.15, 0.044, 0.022), brush + Vector((0.0, 0.0, -0.006)), "#C9A55A", rotation=(0.0, 0.0, 12.0), jitter=0.08)
    sink = mb.finish("pila", tb.material("metal", ENAMEL_WHITE), root)
    tb.stain(sink, RUST, amount=0.75, scale=5.0, coverage=0.28, seed=173, stretch_z=0.3)
    tb.stain(sink, "#6E7468", amount=0.5, scale=4.0, coverage=0.35, seed=174, stretch_z=0.5)
    tb.dent(sink, (-half_w, -0.1, floor_z + 0.12), radius=0.12, depth=0.012)
    tb.wobble(sink, amount=0.002, scale=4.0, seed=173)

    valve = tb.MeshBuilder(seed=179)
    stem = tap + Vector((0.0, -0.035, 0.055))
    valve.cylinder(0.006, 0.02, stem + Vector((0.0, 0.0, 0.008)), STEEL_DARK, segments=8)
    for angle in (0.0, 90.0):
        valve.box((0.07, 0.012, 0.008), stem + Vector((0.0, 0.0, 0.02)), SIGNAL_RED, rotation=(0.0, 0.0, angle + 20.0), bevel=0.003)
    valve_obj = valve.finish("llave", tb.material("metal", SIGNAL_RED), root)
    tb.set_origin(valve_obj, stem)

    water_z = rim_z - 0.09
    water = tb.box("agua", (width - 2.0 * wall + 0.004, depth - 2.0 * wall + 0.004, 0.006), (0.0, 0.0, water_z), cuts=5, mat=tb.material("agua", WATER), parent=root)
    tb.wobble(water, amount=0.0015, scale=9.0, seed=181)

    tb.collision_box("pila_cubeta", (width + 0.03, depth + 0.03, basin_h + 0.02), (0.0, 0.0, floor_z + basin_h / 2.0), root)
    tb.collision_box("pila_patas", (width - 0.02, depth - 0.02, floor_z), (0.0, 0.0, floor_z / 2.0), root)
    tb.collision_box("pila_frontal", (width, 0.03, 0.36), (0.0, half_d + 0.006, rim_z + 0.17), root)
    tb.paint({sink: None, valve_obj: None, water: WATER}, samples=20, ao_distance=0.2, seed=173)
    return root


def models() -> dict:
    return {
        "bascula": build_scale,
        "pila_descontaminacion": build_decon_sink,
    }
