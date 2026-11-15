"""Herramientas de acceso: lo que abre, fuerza, clava y tiende puentes.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Las
herramientas descansan tumbadas sobre la mesa o el suelo.

Las que se empuñan llevan un nodo vacío ``agarre`` en el punto por donde las
coge la mano.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

INK = "#1B1A22"
STEEL = "#6E7478"
STEEL_WORN = "#A2A7A3"
STEEL_DARK = "#3F4A4F"
RUST = "#8E4A2F"
ASH_WOOD = "#B08A5A"
GRIME = "#6E5038"


def _grip(root: bpy.types.Object, at: tuple[float, float, float]) -> None:
    marker = tb.empty("agarre", root)
    marker.location = at


def build_hammer() -> bpy.types.Object:
    """Martillo de uña con mango de fresno, tumbado: el mango hacia -Y y la boca hacia +X."""
    rng = random.Random(233)
    root = tb.empty("martillo-fisico")
    mid_z = 0.0148
    head_y = 0.125

    wood = tb.MeshBuilder(seed=233)
    profile = ((-0.168, 0.008), (-0.162, 0.0142), (-0.13, 0.0155), (-0.08, 0.0145), (-0.02, 0.0125), (0.05, 0.0115), (0.11, 0.0112), (head_y + 0.0165, 0.0112))
    faces = wood.tube([(0.0, y, mid_z) for y, _ in profile], [radius for _, radius in profile], ASH_WOOD, segments=12, jitter=0.04)
    # Sección ovalada: más ancha que gruesa, para que no gire en la mano.
    for vert in dict.fromkeys(v for face in faces for v in face.verts):
        vert.co.z = mid_z + (vert.co.z - mid_z) * 0.74
    wood.box((0.016, 0.0016, 0.006), (0.0, head_y + 0.0168, mid_z), STEEL_DARK, rotation=(0.0, rng.uniform(-12.0, 12.0), 0.0))
    handle = wood.finish("mango", tb.material("madera", ASH_WOOD), root)
    tb.stain(handle, GRIME, amount=0.6, scale=14.0, coverage=0.45, seed=233)
    tb.wobble(handle, amount=0.0006, scale=14.0, seed=233)

    metal = tb.MeshBuilder(seed=239)
    metal.box((0.03, 0.03, 0.026), (0.0, head_y, mid_z), STEEL, bevel=0.004, segments=2, cuts=2)
    # Cuello y boca, hacia +X.
    metal.lathe(
        ((0.0118, 0.0), (0.0098, 0.012), (0.0106, 0.02), (0.0142, 0.025), (0.0145, 0.037), (0.0128, 0.0405), (0.0, 0.0405)),
        (0.012, head_y, mid_z),
        STEEL,
        rotation=(0.0, 90.0, 0.0),
        segments=16,
        sharp_angle=35.0,
    )
    metal.lathe(((0.0, 0.0), (0.0122, 0.0), (0.0, 0.0006)), (0.0527, head_y, mid_z), STEEL_WORN, rotation=(0.0, 90.0, 0.0), segments=16)
    # Uña: dos dientes que se curvan hacia el mango, con la ranura de sacar clavos entre ellos.
    metal.box((0.016, 0.026, 0.0245), (-0.018, head_y - 0.002, mid_z), STEEL, bevel=0.003, segments=2)
    centre, radius, steps = Vector((-0.014, head_y - 0.055)), 0.055, 9
    outer, inner = [], []
    for index in range(steps + 1):
        t = index / steps
        angle = math.radians(92.0 + 76.0 * t)
        width = 0.021 * (1.0 - t) + 0.0045 * t
        direction = Vector((math.cos(angle), math.sin(angle)))
        outer.append(tuple(centre + direction * (radius + width / 2.0)))
        inner.append(tuple(centre + direction * (radius - width / 2.0)))
    for side in (-1.0, 1.0):
        metal.prism(outer + list(reversed(inner)), 0.0092, (0.0, 0.0, mid_z + side * 0.0077), STEEL, bevel=0.0012)
    head = metal.finish("cabeza", tb.material("metal", STEEL), root)
    tb.stain(head, STEEL_DARK, amount=0.6, scale=30.0, coverage=0.4, seed=239)
    tb.stain(head, RUST, amount=0.65, scale=22.0, coverage=0.22, seed=240)

    _grip(root, (0.0, -0.09, mid_z))
    tb.collision_box("martillo_mango", (0.032, 0.31, 0.026), (0.0, -0.02, mid_z), root)
    tb.collision_box("martillo_cabeza", (0.125, 0.072, 0.03), (-0.008, head_y - 0.016, mid_z), root)
    tb.paint({handle: None, head: None}, ao_distance=0.03, ao=0.5, seed=233)
    return root


def models() -> dict:
    return {
        "martillo": build_hammer,
    }
