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
PLANK = "#7E6F5C"
PLANK_DARK = "#51463B"
PLANK_LIGHT = "#9C8E78"
PLANK_PAINT = "#7C93A0"
KNOT = "#55463A"
CROWBAR_PAINT = "#46535A"
CROWBAR_STEEL = "#868B88"
CUTTER_PAINT = "#4F5E52"
CUTTER_STEEL = "#4A5357"
RUBBER = "#2A2725"
BOLT = "#8C918D"


def _grip(root: bpy.types.Object, at: tuple[float, float, float]) -> None:
    marker = tb.empty("agarre", root)
    marker.location = at


def _ccw(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Devuelve el contorno en sentido antihorario, que es el que pide ``MeshBuilder.prism``."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))
    return points if area > 0.0 else list(reversed(points))


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


def build_plank() -> bpy.types.Object:
    """Tablón de andamio para tender puentes: 2,6 m, alabeado, con nudos, una raja y clavos viejos.

    Va tumbado a lo largo de X. Un extremo conserva la pintura con que lo
    marcaron en la obra.
    """
    rng = random.Random(241)
    root = tb.empty("tablon-fisico")
    length, width, thick = 2.6, 0.22, 0.042
    half_l = length / 2.0

    def warp(point: Vector) -> Vector:
        """Alabeo del tablón: algo arqueado a lo largo y retorcido de punta a punta."""
        t = point.x / half_l
        twist = math.radians(1.6) * t
        y, z = point.y, point.z - thick / 2.0
        return Vector((
            point.x,
            y * math.cos(twist) - z * math.sin(twist) + 0.008 * (1.0 - t * t),
            y * math.sin(twist) + z * math.cos(twist) + thick / 2.0 + 0.011 * (1.0 - t * t) + 0.004,
        ))

    mb = tb.MeshBuilder(seed=241)
    mb.box((length, width, thick), (0.0, 0.0, thick / 2.0), PLANK, bevel=0.004, segments=2, cuts=11, jitter=0.03)
    # Pintura de obra en un extremo y una franja desvaída más adentro.
    mb.box((0.262, width + 0.0012, thick + 0.0012), (-half_l + 0.1295, 0.0, thick / 2.0), PLANK_PAINT, bevel=0.004, segments=2, cuts=3, jitter=0.05)
    mb.box((0.05, width + 0.0008, thick + 0.0008), (-half_l + 0.36, 0.0, thick / 2.0), PLANK_PAINT, bevel=0.004, segments=2, cuts=3, jitter=0.08)
    # Veta: trazos cortos y oscuros a lo largo de la cara de arriba.
    for _ in range(26):
        streak = rng.uniform(0.07, 0.2)
        mb.box((streak, rng.uniform(0.0012, 0.0024), 0.0012), (rng.uniform(-half_l + 0.42, half_l - 0.12), rng.uniform(-width / 2.0 + 0.012, width / 2.0 - 0.012), thick + 0.0001), PLANK_DARK, rotation=(0.0, 0.0, rng.uniform(-0.5, 0.5)), jitter=0.2)
    # Nudos y una raja que entra desde la otra punta.
    for _ in range(4):
        knot = (rng.uniform(-half_l + 0.5, half_l - 0.3), rng.uniform(-width / 2.0 + 0.04, width / 2.0 - 0.04))
        size = rng.uniform(0.012, 0.022)
        mb.lathe(((0.0, 0.0), (size, 0.0), (size * 0.6, 0.0006), (0.0, 0.0008)), (knot[0], knot[1], thick), KNOT, segments=10)
        mb.lathe(((0.0, 0.0), (size * 0.45, 0.0), (0.0, 0.0006)), (knot[0], knot[1], thick + 0.0007), INK, segments=8)
    mb.box((0.34, 0.0035, thick + 0.0012), (half_l - 0.17, 0.028, thick / 2.0), INK, rotation=(0.0, 0.0, -1.8))
    mb.box((0.12, 0.0025, thick + 0.0012), (half_l - 0.06, -0.05, thick / 2.0), INK, rotation=(0.0, 0.0, 2.5))
    # Clavos viejos: uno derecho y otro doblado a martillazos.
    nail_x = -half_l + 0.5
    mb.bar((nail_x, 0.05, thick - 0.004), (nail_x, 0.05, thick + 0.028), 0.0022, STEEL_DARK, 6)
    mb.cylinder(0.0055, 0.002, (nail_x, 0.05, thick + 0.029), STEEL_DARK, segments=8)
    mb.tube(tb.smooth_path(((nail_x + 0.09, -0.04, thick - 0.004), (nail_x + 0.09, -0.04, thick + 0.012), (nail_x + 0.096, -0.036, thick + 0.02), (nail_x + 0.112, -0.028, thick + 0.0125)), 3), 0.0022, RUST, segments=6)
    for vert in mb.bm.verts:
        vert.co = warp(vert.co)
    plank = mb.finish("tablon", tb.material("madera", PLANK), root)
    tb.stain(plank, PLANK_DARK, amount=0.6, scale=2.2, coverage=0.45, seed=241)
    tb.stain(plank, PLANK_LIGHT, amount=0.5, scale=6.0, coverage=0.3, seed=242)
    tb.dent(plank, (0.4, width / 2.0, thick), radius=0.09, depth=0.008)
    tb.wobble(plank, amount=0.0006, scale=2.0, seed=241)

    tb.collision_box("tablon", (length, width, thick + 0.016), (0.0, 0.004, (thick + 0.016) / 2.0 + 0.004), root)
    tb.paint({plank: None}, samples=16, ao_distance=0.08, ao=0.45, seed=241)
    return root


def build_crowbar() -> bpy.types.Object:
    """Palanca de barra hexagonal: cuello de cisne con uña en una punta y boca de cincel en la otra.

    Va tumbada a lo largo de X, con el cuello hacia +X curvándose hacia +Y.
    """
    root = tb.empty("palanca-fisico")
    radius = 0.009
    z = radius

    mb = tb.MeshBuilder(seed=251)
    # Barra y cuello de cisne, de una pieza.
    bend, bend_r = Vector((0.2, 0.046)), 0.046
    # Con un anillo cada 3 cm, para que la barra recoja el óxido y el desgaste.
    path = [(-0.31 + 0.03 * index, 0.0, z) for index in range(18)]
    for index in range(1, 9):
        angle = math.radians(-90.0 + 160.0 * index / 8.0)
        path.append((bend.x + bend_r * math.cos(angle), bend.y + bend_r * math.sin(angle), z))
    mb.tube(path, radius, CROWBAR_PAINT, segments=6, jitter=0.03)
    end_angle = math.radians(70.0)
    neck_end = Vector((bend.x + bend_r * math.cos(end_angle), bend.y + bend_r * math.sin(end_angle)))
    along = Vector((-math.sin(end_angle), math.cos(end_angle)))
    across = Vector((along.y, -along.x))

    def tongue(start: Vector, along: Vector, across: Vector, length: float, base: float, tip: float, lift: float) -> list[tuple[float, float]]:
        """Contorno de una lengüeta que se afila: de ``base`` de ancho a ``tip`` en la punta, algo desviada."""
        far = start + along * length + across * lift
        points = [start + across * (base / 2.0), far + across * (tip / 2.0), far - across * (tip / 2.0), start - across * (base / 2.0)]
        area = sum(a.x * b.y - b.x * a.y for a, b in zip(points, points[1:] + points[:1]))
        if area < 0.0:
            points.reverse()
        return [tuple(point) for point in points]

    # Uña: se aplana y se abre en dos dientes para sacar clavos.
    mb.prism(tongue(neck_end - along * 0.006, along, across, 0.05, 0.017, 0.004, -0.004), 0.024, (0.0, 0.0, z), CROWBAR_STEEL, bevel=0.002)
    tip = neck_end + along * 0.044 - across * 0.004
    mb.prism(tongue(tip - along * 0.014, along, across, 0.016, 0.0015, 0.007, 0.0), 0.0075, (0.0, 0.0, z), INK)
    # Boca de cincel en la otra punta, algo girada.
    mb.prism(tongue(Vector((-0.304, 0.0)), Vector((-1.0, 0.0)), Vector((0.0, 1.0)), 0.07, 0.017, 0.0025, 0.012), 0.022, (0.0, 0.0, z), CROWBAR_STEEL, bevel=0.002)
    bar = mb.finish("palanca", tb.material("metal", CROWBAR_PAINT), root)
    tb.stain(bar, STEEL_WORN, amount=0.55, scale=16.0, coverage=0.3, seed=251)
    tb.stain(bar, RUST, amount=0.7, scale=9.0, coverage=0.28, seed=252)

    _grip(root, (-0.08, 0.0, z))
    tb.collision_box("palanca_barra", (0.59, 0.022, 0.024), (-0.085, 0.004, z), root)
    tb.collision_box("palanca_cuello", (0.075, 0.13, 0.024), (0.215, 0.062, z), root)
    tb.paint({bar: None}, ao_distance=0.03, ao=0.45, seed=251)
    return root


def build_bolt_cutter() -> bpy.types.Object:
    """Cizalla de dos manos para cadenas y alambradas, tumbada: las bocas hacia +X y los mangos, entreabiertos, hacia -X.

    Lleva dos nodos vacíos, ``agarre`` y ``agarre_2``, uno por empuñadura.
    """
    rng = random.Random(293)
    root = tb.empty("cizalla-fisico")
    mid_z = 0.016

    mb = tb.MeshBuilder(seed=293)
    for side in (-1.0, 1.0):
        # Mango: barra redonda con su empuñadura de goma; entra en un casquillo de la cabeza.
        grip_end = Vector((-0.45, side * 0.088, mid_z))
        along = (Vector((0.03, side * 0.025, mid_z)) - grip_end).normalized()
        span = 0.458
        rings = 16
        mb.tube([grip_end + along * (span * index / rings) for index in range(rings + 1)], 0.0105, CUTTER_PAINT, segments=10, jitter=0.04)
        mb.tube([grip_end + along * (span - 0.022), grip_end + along * (span - 0.018), grip_end + along * (span + 0.012), grip_end + along * (span + 0.016)], [0.0115, 0.0132, 0.0132, 0.0115], CUTTER_STEEL, segments=10)
        mb.tube([grip_end - along * 0.004, grip_end + along * 0.002, grip_end + along * 0.15, grip_end + along * 0.154], [0.011, 0.0138, 0.0138, 0.012], RUBBER, segments=12)
        for index in range(4):
            mb.tube([grip_end + along * (0.03 + index * 0.03), grip_end + along * (0.036 + index * 0.03)], 0.0147, RUBBER, segments=12)
        # Cabeza del mango: pletina que lleva al eje central y al de su boca.
        mb.prism(
            _ccw([(0.0, side * 0.037), (0.0, side * 0.014), (0.07, side * 0.0022), (0.112, side * 0.004), (0.112, side * 0.024), (0.06, side * 0.035)]),
            0.012,
            (0.0, 0.0, mid_z),
            CUTTER_STEEL,
            bevel=0.002,
            jitter=0.05,
        )
        # Boca: pico corto y grueso, con el filo en bisel.
        mb.prism(
            _ccw([(0.094, side * 0.003), (0.186, side * 0.0016), (0.207, side * 0.0042), (0.201, side * 0.019), (0.172, side * 0.031), (0.13, side * 0.035), (0.094, side * 0.029)]),
            0.016,
            (0.0, 0.0, mid_z),
            CUTTER_STEEL,
            bevel=0.0025,
            jitter=0.05,
        )
        mb.box((0.088, 0.0026, 0.0166), (0.142, side * 0.0032, mid_z), BOLT, rotation=(0.0, 0.0, side * -0.9))
        # Tornillos de los ejes de las bocas.
        for x in (0.108, 0.148):
            bolt_y = side * (0.016 if x < 0.12 else 0.017)
            mb.cylinder(0.0062, 0.005, (x, bolt_y, mid_z + 0.0135), BOLT, rotation=(0.0, 0.0, rng.uniform(0.0, 60.0)), segments=6)
            mb.cylinder(0.006, 0.004, (x, bolt_y, mid_z - 0.013), BOLT, rotation=(0.0, 0.0, rng.uniform(0.0, 60.0)), segments=6)
    # Bridas que unen las dos bocas, arriba y abajo.
    for z in (mid_z + 0.0095, mid_z - 0.0095):
        mb.box((0.026, 0.062, 0.003), (0.148, 0.0, z), CUTTER_STEEL, bevel=0.001, jitter=0.05)
    # Eje central de los mangos y tornillo de tope.
    mb.lathe(((0.0, -0.0072), (0.0125, -0.0072), (0.0125, 0.0072), (0.0, 0.0072)), (0.072, 0.0, mid_z), CUTTER_STEEL, segments=14)
    mb.cylinder(0.0075, 0.005, (0.072, 0.0, mid_z + 0.0095), BOLT, rotation=(0.0, 0.0, 20.0), segments=6)
    mb.cylinder(0.0072, 0.004, (0.072, 0.0, mid_z - 0.009), BOLT, segments=6)
    mb.bar((0.012, 0.029, mid_z), (0.012, 0.009, mid_z), 0.003, BOLT, 6)
    mb.cylinder(0.0055, 0.004, (0.012, 0.0125, mid_z), BOLT, rotation=(90.0, 0.0, 0.0), segments=6)
    cutter = mb.finish("cizalla", tb.material("metal", CUTTER_PAINT), root)
    tb.stain(cutter, RUST, amount=0.7, scale=11.0, coverage=0.3, seed=293)
    tb.stain(cutter, STEEL_WORN, amount=0.45, scale=18.0, coverage=0.25, seed=294)

    _grip(root, (-0.375, 0.077, mid_z))
    second = tb.empty("agarre_2", root)
    second.location = (-0.375, -0.077, mid_z)
    tb.collision_box("cizalla_mangos", (0.48, 0.2, 0.03), (-0.215, 0.0, mid_z), root)
    tb.collision_box("cizalla_cabeza", (0.21, 0.078, 0.032), (0.105, 0.0, mid_z), root)
    tb.paint({cutter: None}, ao_distance=0.03, ao=0.5, seed=293)
    return root


def models() -> dict:
    return {
        "martillo": build_hammer,
        "tablon": build_plank,
        "palanca": build_crowbar,
        "cizalla": build_bolt_cutter,
    }
