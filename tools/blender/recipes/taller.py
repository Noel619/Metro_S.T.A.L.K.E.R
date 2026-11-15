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
    width, depth, base_h = 0.56, 0.27, 0.105
    pivot = (0.0, 0.0, base_h + 0.07)
    head_r, head_t = 0.40, 0.085
    front = -head_t / 2.0

    mb = tb.MeshBuilder(seed=61)
    # Cuerpo de fundición esmaltada, sobre cuatro patas roscadas.
    mb.box((width, depth, base_h - 0.02), (0.0, 0.0, 0.02 + (base_h - 0.02) / 2.0), ENAMEL_BLUE, bevel=0.022, segments=3)
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
    mb.box((0.15, head_t + 0.02, 0.05), (0.0, 0.0, neck_z + 0.02), ENAMEL_BLUE, bevel=0.012, segments=2)
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
    for x, tilt in ((-0.18, rng.uniform(-1.0, 1.0)), (0.18, rng.uniform(-1.0, 1.0))):
        pans.lathe(((0.0, 0.0), (0.03, 0.0), (0.03, 0.006), (0.013, 0.012), (0.013, 0.06), (0.0, 0.06)), (x, 0.0, base_h + 0.015), STEEL_DARK, segments=12)
        for angle in (0.0, 90.0):
            pans.box((0.15, 0.022, 0.012), (x, 0.0, pan_z - 0.012), STEEL_DARK, rotation=(0.0, tilt, angle), bevel=0.004)
    pans.lathe(
        ((0.0, 0.0), (0.098, 0.0), (0.108, 0.004), (0.108, 0.012), (0.1, 0.015), (0.092, 0.011), (0.0, 0.011)),
        (-0.18, 0.0, pan_z - 0.006),
        ALUMINIUM,
        segments=28,
        jitter=0.03,
    )
    pans.lathe(
        (
            (0.0, 0.0), (0.05, 0.001), (0.1, 0.014), (0.135, 0.04), (0.148, 0.064), (0.154, 0.066),
            (0.153, 0.07), (0.145, 0.068), (0.13, 0.044), (0.096, 0.02), (0.048, 0.007), (0.0, 0.006),
        ),
        (0.18, 0.0, pan_z - 0.006),
        ALUMINIUM,
        segments=28,
        sharp_angle=60.0,
        jitter=0.03,
    )
    pans_obj = pans.finish("platos", tb.material("metal", ALUMINIUM), root)
    tb.stain(pans_obj, ALUMINIUM_DARK, amount=0.6, scale=7.0, coverage=0.35, seed=67)
    tb.dent(pans_obj, (0.3, -0.08, pan_z + 0.05), radius=0.06, depth=0.006)

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

    tb.collision_box("bascula_base", (width + 0.12, depth + 0.04, base_h + 0.16), (0.0, 0.0, (base_h + 0.16) / 2.0), root)
    tb.collision_box("bascula_esfera", (0.5, head_t + 0.02, head_r), (0.0, 0.0, pivot[2] + head_r / 2.0), root)
    tb.paint({body: None, pans_obj: None, needle_obj: None}, ao_distance=0.12, seed=61)
    return root


def models() -> dict:
    return {
        "bascula": build_scale,
    }
