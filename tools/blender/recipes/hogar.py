"""El rincón de vivir del depósito: la estufa, el catre y la radio.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. El
frente de cada mueble mira hacia -Y (en Godot, hacia +Z).

Las piezas que se mueven o se encienden en el juego son nodos propios con el
origen en su eje de giro: ver ``tb.set_origin``.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

INK = "#1B1A22"
IRON = "#62686A"
IRON_DARK = "#4A4F52"
IRON_WORN = "#858A88"
RUST = "#8E4A2F"
SOOT = "#26262A"
EMBER_OFF = "#4A2C20"
STEEL = "#8C918D"


def build_stove() -> bpy.types.Object:
    """Estufa de hierro de tres patas, con su tubo acodado hacia la pared del fondo.

    Las ``brasas`` (las rendijas de la puerta) son un nodo propio con el
    material "brasas": apagadas de serie; al encender la estufa, el juego les
    pone un material que emita luz.
    """
    rng = random.Random(109)
    root = tb.empty("estufa-estatico")
    radius, bottom, top = 0.205, 0.17, 0.7
    pipe = (0.0, 0.09)

    mb = tb.MeshBuilder(seed=109)
    # Panza: un barril algo abombado, con sus zunchos.
    steps = 8
    barrel = [(0.0, bottom), (radius - 0.035, bottom)]
    for i in range(steps + 1):
        t = i / steps
        barrel.append((radius - 0.012 * (2.0 * t - 1.0) ** 2, bottom + 0.03 + (top - bottom - 0.06) * t))
    barrel += [(radius - 0.035, top), (0.0, top)]
    mb.lathe(barrel, (0.0, 0.0, 0.0), IRON, segments=28, sharp_angle=35.0, jitter=0.04)
    for z in (bottom + 0.05, top - 0.07):
        mb.lathe(((radius - 0.006, z), (radius + 0.006, z + 0.004), (radius + 0.006, z + 0.022), (radius - 0.006, z + 0.026)), (0.0, 0.0, 0.0), IRON_DARK, segments=28)
    # Tapa de arriba, con el aro de cocinar y su asa.
    mb.lathe(((0.0, top - 0.004), (radius + 0.012, top - 0.004), (radius + 0.016, top + 0.004), (radius + 0.008, top + 0.016), (0.0, top + 0.016)), (0.0, 0.0, 0.0), IRON_DARK, segments=28, sharp_angle=35.0)
    lid = (0.0, -0.055, top + 0.016)
    mb.lathe(((0.0, 0.0), (0.085, 0.0), (0.085, 0.006), (0.07, 0.01), (0.0, 0.01)), lid, IRON, segments=20)
    mb.tube(tb.smooth_path(((-0.03, lid[1], lid[2] + 0.008), (-0.022, lid[1], lid[2] + 0.03), (0.022, lid[1], lid[2] + 0.03), (0.03, lid[1], lid[2] + 0.008)), 3), 0.005, IRON_DARK, segments=6)
    # Tres patas abiertas.
    for angle in (90.0, 210.0, 330.0):
        a = math.radians(angle)
        foot = Vector((0.24 * math.cos(a), 0.24 * math.sin(a), 0.0))
        mb.bar((0.14 * math.cos(a), 0.14 * math.sin(a), bottom + 0.03), foot + Vector((0.0, 0.0, 0.012)), 0.017, IRON_DARK, 8)
        mb.lathe(((0.0, 0.0), (0.03, 0.0), (0.03, 0.01), (0.018, 0.018), (0.0, 0.018)), foot, IRON_DARK, segments=10)
    # Puerta de carga, con bisagras y pestillo; debajo, el cenicero.
    door_z, front = 0.5, -radius + 0.012
    mb.box((0.23, 0.045, 0.2), (0.0, front - 0.008, door_z), IRON_DARK, bevel=0.012, segments=2)
    mb.box((0.19, 0.03, 0.16), (0.0, front - 0.028, door_z), IRON, rotation=(0.0, 0.0, rng.uniform(-1.0, 1.0)), bevel=0.01, segments=2, cuts=2)
    for z in (door_z - 0.06, door_z + 0.06):
        mb.cylinder(0.011, 0.04, (-0.105, front - 0.03, z), IRON_WORN, segments=8)
    mb.bar((0.045, front - 0.048, door_z + 0.01), (0.125, front - 0.04, door_z - 0.02), 0.007, IRON_WORN, 6)
    mb.lathe(((0.0, 0.0), (0.013, 0.0), (0.013, 0.012), (0.0, 0.012)), (0.05, front - 0.04, door_z + 0.01), IRON_WORN, rotation=(90.0, 0.0, 0.0), segments=10)
    mb.box((0.16, 0.035, 0.07), (0.0, front - 0.012, 0.285), IRON_DARK, bevel=0.01, segments=2)
    mb.lathe(((0.0, 0.0), (0.012, 0.0), (0.016, 0.012), (0.012, 0.022), (0.0, 0.022)), (0.0, front - 0.028, 0.285), IRON_WORN, rotation=(90.0, 0.0, 0.0), segments=10)
    # Tubo: tres tramos con sus collarines, la llave de tiro y el codo hacia la pared.
    mb.lathe(((0.075, top + 0.01), (0.075, top + 0.03), (0.06, top + 0.04)), (pipe[0], pipe[1], 0.0), IRON_DARK, segments=14)
    elbow_z = 1.78
    mb.tube(
        [(pipe[0], pipe[1], top + 0.02), (pipe[0], pipe[1] + rng.uniform(-0.006, 0.006), 1.2)]
        + tb.smooth_path(
            ((pipe[0], pipe[1], elbow_z - 0.06), (pipe[0], pipe[1] + 0.012, elbow_z + 0.05), (pipe[0], pipe[1] + 0.07, elbow_z + 0.115), (pipe[0], pipe[1] + 0.17, elbow_z + 0.13), (pipe[0], pipe[1] + 0.42, elbow_z + 0.135)),
            4,
        ),
        0.055,
        IRON,
        segments=14,
        jitter=0.04,
    )
    for z in (1.2, elbow_z - 0.07):
        mb.lathe(((0.056, z - 0.02), (0.061, z - 0.015), (0.061, z + 0.015), (0.056, z + 0.02)), (pipe[0], pipe[1], 0.0), IRON_DARK, segments=14)
    mb.lathe(((0.056, -0.02), (0.061, -0.015), (0.061, 0.015), (0.056, 0.02)), (pipe[0], pipe[1] + 0.2, elbow_z + 0.132), IRON_DARK, rotation=(-90.0, 0.0, 0.0), segments=14)
    mb.bar((pipe[0] - 0.085, pipe[1], 0.98), (pipe[0] + 0.07, pipe[1], 0.98), 0.005, IRON_WORN, 6)
    mb.box((0.012, 0.012, 0.05), (pipe[0] - 0.09, pipe[1], 0.965), IRON_WORN, bevel=0.003)
    stove = mb.finish("estufa", tb.material("metal", IRON), root)
    tb.stain(stove, RUST, amount=0.7, scale=5.0, coverage=0.3, seed=109)
    tb.stain(stove, SOOT, amount=0.6, scale=4.0, coverage=0.3, seed=110, stretch_z=0.35)
    tb.dent(stove, (0.03, pipe[1] - 0.05, 1.45), radius=0.09, depth=0.012)
    tb.wobble(stove, amount=0.003, scale=4.0, seed=109)

    embers = tb.MeshBuilder(seed=113)
    for index in range(4):
        embers.box((0.13, 0.006, 0.012), (0.0, front - 0.0445, door_z - 0.045 + index * 0.024), EMBER_OFF)
    embers_obj = embers.finish("brasas", tb.material("brasas", EMBER_OFF), root)
    tb.set_origin(embers_obj, (0.0, front - 0.0445, door_z))

    tb.collision_box("estufa_panza", (0.48, 0.5, top + 0.02), (0.0, -0.01, (top + 0.02) / 2.0), root)
    tb.collision_box("estufa_tubo", (0.13, 0.13, elbow_z + 0.2 - top), (pipe[0], pipe[1], (elbow_z + 0.2 + top) / 2.0), root)
    tb.collision_box("estufa_codo", (0.13, 0.42, 0.13), (pipe[0], pipe[1] + 0.21, elbow_z + 0.135), root)
    tb.paint({stove: None, embers_obj: None}, ao_distance=0.2, seed=109)
    return root


def models() -> dict:
    return {
        "estufa": build_stove,
    }
