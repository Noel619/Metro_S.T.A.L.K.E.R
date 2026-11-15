"""La tienda: lo que hay junto a la persiana para atender a los clientes.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. El
lado del cliente mira hacia -Y (en Godot, hacia +Z); el del stalker, hacia +Y.

Las piezas que se mueven en el juego son nodos propios con el origen en su
eje: ver ``tb.set_origin``.
"""

from __future__ import annotations

import random

import bpy

import tumansk_bpy as tb

WOOD = "#8A5A3B"
WOOD_DARK = "#6E4A32"
WOOD_DEEP = "#553826"
WOODS = (WOOD, "#7A4E33", "#9A6845", "#80563A")
BRASS = "#B59A5A"
STEEL_DARK = "#3F4A4F"
FELT = "#4F6B55"

# Mostrador: el cajón de los rublos sale DRAWER_TRAVEL metros hacia el stalker.
DRAWER_TRAVEL = 0.3


def build_counter() -> bpy.types.Object:
    """Mostrador de tablas: frente machihembrado hacia el cliente y baldas por detrás.

    El ``cajon`` (la caja de los rublos) es un nodo propio: se abre deslizándolo
    DRAWER_TRAVEL metros hacia +Y (en Godot, hacia -Z).
    """
    rng = random.Random(163)
    root = tb.empty("mostrador-estatico")
    width, depth, height = 1.8, 0.6, 0.95
    top_t = 0.05
    body_h = height - top_t
    front, back = -depth / 2.0, depth / 2.0

    mb = tb.MeshBuilder(seed=163)
    # Tablero: tres tablones gruesos, gastados por el lado del cliente.
    planks = 3
    plank_d = (depth + 0.12) / planks
    for index in range(planks):
        y = front - 0.07 + (index + 0.5) * plank_d
        mb.box((width + 0.1, plank_d - 0.005, top_t), (0.0, y, height - top_t / 2.0), rng.choice((WOOD_DARK, "#7B5236", "#64432D")), rotation=(rng.uniform(-0.5, 0.5), 0.0, rng.uniform(-0.15, 0.15)), bevel=0.009, segments=2, cuts=4, jitter=0.06)
    # Frente machihembrado, con zócalo y moldura bajo el tablero.
    boards = 15
    board_w = (width - 0.06) / boards
    for index in range(boards):
        x = -width / 2.0 + 0.03 + (index + 0.5) * board_w
        mb.box((board_w - 0.004, 0.022, body_h - 0.1), (x, front + 0.011 + rng.uniform(-0.002, 0.002), 0.1 + (body_h - 0.1) / 2.0), rng.choice(WOODS), rotation=(0.0, rng.uniform(-0.35, 0.35), 0.0), bevel=0.004, cuts=2, jitter=0.08)
    mb.box((width, 0.035, 0.1), (0.0, front + 0.035, 0.05), WOOD_DEEP, bevel=0.006, cuts=3, jitter=0.05)
    mb.box((width + 0.03, 0.03, 0.055), (0.0, front - 0.004, body_h - 0.03), WOOD_DARK, bevel=0.01, segments=2, cuts=3)
    mb.box((width + 0.02, 0.024, 0.04), (0.0, front - 0.002, 0.32), WOOD_DARK, bevel=0.008, cuts=3)
    # Costados, trasera abierta con dos baldas y un montante.
    for x in (-width / 2.0 + 0.016, width / 2.0 - 0.016):
        mb.box((0.032, depth, body_h), (x, 0.0, body_h / 2.0), WOOD_DARK, bevel=0.006, cuts=3, jitter=0.06)
    for z in (0.11, 0.5):
        mb.box((width - 0.064, depth - 0.03, 0.024), (0.0, 0.012, z), rng.choice(WOODS), bevel=0.004, cuts=3, jitter=0.07)
    mb.box((0.028, depth - 0.03, body_h - 0.1), (-0.12, 0.012, 0.1 + (body_h - 0.1) / 2.0), WOOD_DARK, bevel=0.005, cuts=2)
    # Hueco del cajón: travesaño y guías.
    drawer_x, drawer_w, drawer_h = 0.38, 0.62, 0.15
    drawer_z = body_h - 0.03 - drawer_h / 2.0
    mb.box((width - 0.064, 0.03, 0.03), (0.0, back - 0.015, body_h - 0.015), WOOD_DARK, bevel=0.004)
    mb.box((drawer_w + 0.06, depth - 0.04, 0.02), (drawer_x, 0.01, drawer_z - drawer_h / 2.0 - 0.014), WOOD_DEEP, bevel=0.003)
    counter = mb.finish("mostrador", tb.material("madera", WOOD), root)
    tb.stain(counter, WOOD_DEEP, amount=0.55, scale=3.5, coverage=0.4, seed=163, stretch_z=0.3)
    tb.stain(counter, "#A07A54", amount=0.5, scale=5.0, coverage=0.2, seed=164)
    tb.dent(counter, (0.3, front - 0.02, height), radius=0.22, depth=0.006)
    tb.wobble(counter, amount=0.0025, scale=3.0, seed=163)

    drawer = tb.MeshBuilder(seed=167)
    face = (drawer_x, back - 0.011, drawer_z)
    drawer.box((drawer_w, 0.024, drawer_h), face, WOOD, rotation=(0.0, 0.0, rng.uniform(-0.3, 0.3)), bevel=0.006, segments=2, cuts=2)
    inner_d = depth - 0.12
    drawer.box((drawer_w - 0.04, inner_d, 0.012), (drawer_x, back - 0.022 - inner_d / 2.0, drawer_z - drawer_h / 2.0 + 0.012), WOOD_DARK)
    for x in (-1.0, 1.0):
        drawer.box((0.012, inner_d, drawer_h - 0.03), (drawer_x + x * (drawer_w / 2.0 - 0.026), back - 0.022 - inner_d / 2.0, drawer_z - 0.008), WOOD_DARK)
    drawer.box((drawer_w - 0.04, 0.012, drawer_h - 0.03), (drawer_x, back - 0.022 - inner_d + 0.006, drawer_z - 0.008), WOOD_DARK)
    # Fieltro verde en el fondo y separadores para los billetes.
    drawer.box((drawer_w - 0.066, inner_d - 0.014, 0.004), (drawer_x, back - 0.022 - inner_d / 2.0, drawer_z - drawer_h / 2.0 + 0.02), FELT)
    for x in (-0.1, 0.1):
        drawer.box((0.008, inner_d - 0.02, 0.05), (drawer_x + x, back - 0.022 - inner_d / 2.0, drawer_z - drawer_h / 2.0 + 0.044), WOOD)
    drawer.lathe(((0.0, 0.0), (0.02, 0.0), (0.014, 0.008), (0.012, 0.02), (0.02, 0.03), (0.016, 0.038), (0.0, 0.04)), (face[0], face[1] + 0.012, face[2]), BRASS, rotation=(-90.0, 0.0, 0.0), segments=14)
    drawer.box((0.05, 0.004, 0.06), (face[0], face[1] + 0.013, face[2] + 0.0), BRASS, bevel=0.0015)
    drawer_obj = drawer.finish("cajon", tb.material("madera", WOOD), root)
    tb.set_origin(drawer_obj, face)

    tb.collision_box("mostrador", (width + 0.1, depth + 0.12, height), (0.0, -0.01, height / 2.0), root)
    tb.paint({counter: None, drawer_obj: None}, samples=20, ao_distance=0.3, seed=163)
    return root


def models() -> dict:
    return {
        "mostrador": build_counter,
    }
