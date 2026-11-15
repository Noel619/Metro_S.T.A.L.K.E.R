"""El equipo del stalker: lo que se lleva encima en cada salida.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Los
aparatos de mano descansan sobre su base, con la cara de lectura hacia arriba
y el borde inferior hacia -Y (en Godot, hacia +Z).

Las piezas que se mueven en el juego (agujas, interruptores) son nodos propios
con el origen en su eje de giro: ver ``tb.set_origin``.
"""

from __future__ import annotations

import math
import random

import bpy

import tumansk_bpy as tb

INK = "#1B1A22"
OLIVE = "#5E6748"
OLIVE_DARK = "#454D38"
OLIVE_WORN = "#7C8262"
DIAL_CREAM = "#E9E2CC"
BAKELITE = "#2A2725"
STEEL = "#8C918D"
STEEL_DARK = "#3F4A4F"
ALUMINIUM = "#A9ADA8"
RUBBER = "#26241F"
RUST = "#8E4A2F"
SIGNAL_RED = "#C8323C"

# Dosímetro: la aguja recorre METER_SWEEP grados a cada lado del centro.
METER_SWEEP = 45.0


def build_dosimeter() -> bpy.types.Object:
    """Dosímetro de campo: caja de chapa, esfera de aguja y sonda en el costado.

    Nodos propios: ``aguja`` (en reposo marca el cero, a la izquierda; a fondo
    de escala ha girado 2 × METER_SWEEP grados: en Godot, ``rotation.y`` de 0 a
    -90°) y ``piloto``, la lámpara que parpadea con cada chasquido.
    """
    rng = random.Random(73)
    root = tb.empty("dosimetro-fisico")
    width, length, height = 0.13, 0.2, 0.062
    top = height + 0.004
    pivot = (0.0, 0.022, top + 0.0075)

    mb = tb.MeshBuilder(seed=73)
    mb.box((width, length, height), (0.0, 0.0, height / 2.0), OLIVE, bevel=0.009, segments=2)
    mb.box((width - 0.014, length - 0.014, 0.006), (0.0, 0.0, height + 0.001), OLIVE_DARK, bevel=0.002)
    for x in (-1.0, 1.0):
        for y in (-1.0, 1.0):
            mb.cylinder(0.0038, 0.003, (x * (width / 2.0 - 0.014), y * (length / 2.0 - 0.014), top + 0.001), STEEL, segments=8)
    # Esfera: cerco, fondo crema y marcas en arco.
    mb.box((0.104, 0.074, 0.009), (0.0, 0.047, top + 0.0035), BAKELITE, bevel=0.003, segments=2)
    mb.box((0.09, 0.06, 0.002), (0.0, 0.047, top + 0.0075), DIAL_CREAM)
    for index in range(21):
        angle = -METER_SWEEP + 2.0 * METER_SWEEP * index / 20.0
        long_mark = index % 5 == 0
        mark = 0.009 if long_mark else 0.005
        radius = 0.047 - mark / 2.0
        a = math.radians(angle)
        mb.box(
            (0.002 if long_mark else 0.0012, mark, 0.0008),
            (pivot[0] + radius * math.sin(a), pivot[1] + radius * math.cos(a), top + 0.0089),
            INK,
            rotation=(0.0, 0.0, -angle),
        )
    # Tramo final de la escala, en rojo: dosis peligrosa.
    for index in range(5):
        angle = METER_SWEEP - 2.0 - index * 4.4
        a = math.radians(angle)
        mb.box((0.0032, 0.003, 0.0008), (pivot[0] + 0.034 * math.sin(a), pivot[1] + 0.034 * math.cos(a), top + 0.0089), SIGNAL_RED, rotation=(0.0, 0.0, -angle))
    # Mandos: selector de escala, interruptor y rejilla del altavoz.
    knob = (-0.036, -0.036, top)
    mb.lathe(((0.0, 0.0), (0.021, 0.0), (0.021, 0.003), (0.017, 0.004), (0.016, 0.015), (0.013, 0.017), (0.0, 0.017)), knob, BAKELITE, segments=16)
    mb.box((0.004, 0.02, 0.004), (knob[0] - 0.005, knob[1] + 0.005, top + 0.018), DIAL_CREAM, rotation=(0.0, 0.0, 40.0), bevel=0.001)
    for index in range(5):
        a = math.radians(100.0 - index * 35.0)
        mb.cylinder(0.0018, 0.0012, (knob[0] + 0.027 * math.cos(a), knob[1] + 0.027 * math.sin(a), top + 0.0005), DIAL_CREAM, segments=6)
    switch = (0.014, -0.03, top)
    mb.lathe(((0.0, 0.0), (0.008, 0.0), (0.008, 0.003), (0.005, 0.005), (0.0, 0.005)), switch, STEEL, segments=10)
    mb.bar((switch[0], switch[1], top + 0.003), (switch[0], switch[1] + 0.009, top + 0.02), 0.0024, STEEL, 6)
    for index in range(4):
        mb.box((0.062 - index * 0.006, 0.0032, 0.0015), (0.0, -0.064 - index * 0.0075, top + 0.0003), INK, bevel=0.0005)
    # Asa abatible, en el extremo de la esfera.
    handle_y, handle_z = length / 2.0, height * 0.62
    mb.tube(
        (
            (-0.045, handle_y - 0.004, handle_z), (-0.045, handle_y + 0.02, handle_z - 0.004), (-0.036, handle_y + 0.033, handle_z - 0.008),
            (0.036, handle_y + 0.033, handle_z - 0.008), (0.045, handle_y + 0.02, handle_z - 0.004), (0.045, handle_y - 0.004, handle_z),
        ),
        0.0032,
        STEEL,
        segments=6,
    )
    for x in (-0.045, 0.045):
        mb.box((0.012, 0.005, 0.016), (x, handle_y + 0.002, handle_z), STEEL_DARK, bevel=0.0015)
    # Sonda en sus pinzas, con el cable hasta el prensaestopas del frente.
    probe_x, probe_z = width / 2.0 + 0.021, height * 0.55
    for y in (-0.04, 0.045):
        mb.box((0.012, 0.014, 0.036), (width / 2.0 + 0.004, y, probe_z), STEEL_DARK, bevel=0.002)
        mb.box((0.034, 0.012, 0.004), (probe_x - 0.002, y, probe_z + 0.018), STEEL_DARK, rotation=(0.0, rng.uniform(-4.0, 4.0), 0.0), bevel=0.0015)
    mb.cylinder(0.0145, 0.15, (probe_x, 0.005, probe_z), ALUMINIUM, rotation=(90.0, 0.0, 0.0), segments=14)
    mb.cylinder(0.0152, 0.034, (probe_x, 0.052, probe_z), OLIVE, rotation=(90.0, 0.0, 0.0), segments=14)
    mb.cylinder(0.0155, 0.01, (probe_x, 0.081, probe_z), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=14)
    mb.cylinder(0.009, 0.016, (probe_x, -0.077, probe_z), BAKELITE, rotation=(90.0, 0.0, 0.0), segments=10)
    gland = (-0.03, -length / 2.0, height * 0.5)
    mb.cylinder(0.008, 0.012, (gland[0], gland[1] - 0.005, gland[2]), STEEL, rotation=(90.0, 0.0, 0.0), segments=10)
    mb.tube(
        tb.smooth_path((
            (probe_x, -0.084, probe_z), (probe_x, -0.104, probe_z - 0.002), (probe_x - 0.012, -0.124, probe_z - 0.012),
            (probe_x - 0.04, -0.136, probe_z - 0.022), (0.02, -0.139, probe_z - 0.028), (-0.012, -0.134, probe_z - 0.022),
            (-0.027, -0.122, gland[2] - 0.004), (gland[0], gland[1] - 0.01, gland[2]),
        )),
        0.0032,
        RUBBER,
        segments=6,
    )
    body = mb.finish("cuerpo", tb.material("metal", OLIVE), root)
    tb.stain(body, OLIVE_WORN, amount=0.55, scale=14.0, coverage=0.32, seed=73)
    tb.stain(body, RUST, amount=0.6, scale=9.0, coverage=0.14, seed=74)
    tb.dent(body, (-width / 2.0, 0.06, height * 0.4), radius=0.035, depth=0.003)
    tb.wobble(body, amount=0.0006, scale=9.0, seed=73)

    needle = tb.MeshBuilder(seed=79)
    a = math.radians(-METER_SWEEP)
    needle.box((0.0016, 0.044, 0.0008), (pivot[0] + 0.019 * math.sin(a), pivot[1] + 0.019 * math.cos(a), pivot[2] + 0.0024), INK, rotation=(0.0, 0.0, METER_SWEEP))
    needle.cylinder(0.0055, 0.003, (pivot[0], pivot[1], pivot[2] + 0.002), STEEL_DARK, segments=10)
    needle_obj = needle.finish("aguja", tb.material("metal", INK), root)
    tb.set_origin(needle_obj, pivot)

    lamp = tb.MeshBuilder(seed=83)
    lamp_at = (0.044, -0.03, top)
    lamp.lathe(((0.0, 0.0), (0.009, 0.0), (0.009, 0.003), (0.0, 0.003)), lamp_at, STEEL_DARK, segments=12)
    lamp.sphere(0.0068, (lamp_at[0], lamp_at[1], top + 0.003), SIGNAL_RED, segments=10, scale=(1.0, 1.0, 0.8))
    lamp_obj = lamp.finish("piloto", tb.material("piloto", SIGNAL_RED), root)
    tb.set_origin(lamp_obj, lamp_at)

    tb.collision_box("dosimetro", (width + 0.04, length, height + 0.012), (0.018, 0.0, (height + 0.012) / 2.0), root)
    tb.paint({body: None, needle_obj: None, lamp_obj: None}, ao_distance=0.05, ao=0.5, seed=73)
    return root


def models() -> dict:
    return {
        "dosimetro": build_dosimeter,
    }
