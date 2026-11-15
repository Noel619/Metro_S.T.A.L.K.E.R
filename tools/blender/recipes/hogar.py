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
VENEER = "#7A4E33"
VENEER_DARK = "#5A3B2A"
BAKELITE_CREAM = "#CDBF9F"
BAKELITE_DARK = "#2E2B28"
CLOTH = "#9C8C66"
DIAL_CREAM = "#E9E2CC"
LEATHER = "#6B4A2B"
SIGNAL_RED = "#C8323C"

# Radio: la aguja del dial se desliza DIAL_TRAVEL metros a cada lado del centro.
DIAL_TRAVEL = 0.066


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


def build_radio() -> bpy.types.Object:
    """Radio de sobremesa: caja de chapa de madera, rejilla de tela y dial.

    Es la radio del depósito (sus tres mandos son los ajustes del juego) y
    también botín de los pisos. Nodos propios, con el origen en su eje:
    ``mando_volumen``, ``mando_brillo`` y ``mando_sensibilidad`` giran sobre su
    eje Y (en Godot, ``rotation.z``); ``aguja`` se desliza a lo largo de X por
    el dial, DIAL_TRAVEL metros a cada lado; ``piloto`` es la lámpara de encendido.
    """
    rng = random.Random(127)
    root = tb.empty("radio-fisico")
    width, depth, height, feet = 0.44, 0.17, 0.26, 0.012
    front = -depth / 2.0
    mid_z = feet + height / 2.0

    wood = tb.MeshBuilder(seed=127)
    wood.box((width, depth, height), (0.0, 0.0, mid_z), VENEER, bevel=0.016, segments=3, cuts=4, jitter=0.03)
    for x in (-width / 2.0 + 0.04, width / 2.0 - 0.04):
        for y in (-depth / 2.0 + 0.035, depth / 2.0 - 0.035):
            wood.cylinder(0.014, feet + 0.004, (x, y, feet / 2.0 + 0.002), "#2A2725", segments=10)
    # Frente: marco, tela del altavoz con sus lamas y ventana del dial.
    wood.box((width - 0.04, 0.008, height - 0.04), (0.0, front - 0.002, mid_z), BAKELITE_CREAM, bevel=0.003, cuts=2)
    speaker_x, speaker_w, speaker_h = -0.085, 0.21, 0.18
    wood.box((speaker_w, 0.004, speaker_h), (speaker_x, front - 0.007, mid_z), CLOTH, cuts=3, jitter=0.05)
    for index in range(10):
        x = speaker_x - speaker_w / 2.0 + 0.012 + index * (speaker_w - 0.024) / 9.0
        wood.box((0.007, 0.007, speaker_h + 0.004), (x, front - 0.011, mid_z), VENEER_DARK, rotation=(0.0, 0.0, rng.uniform(-0.5, 0.5)), bevel=0.002, jitter=0.08)
    for z in (mid_z - speaker_h / 2.0, mid_z + speaker_h / 2.0):
        wood.box((speaker_w + 0.016, 0.01, 0.01), (speaker_x, front - 0.011, z), VENEER_DARK, bevel=0.003)
    dial = (0.118, front - 0.008, mid_z + 0.055)
    wood.box((0.168, 0.006, 0.072), dial, "#33302C", bevel=0.003)
    wood.box((0.152, 0.004, 0.056), (dial[0], dial[1] - 0.003, dial[2]), DIAL_CREAM)
    for index in range(25):
        x = dial[0] - DIAL_TRAVEL + 2.0 * DIAL_TRAVEL * index / 24.0
        long_mark = index % 4 == 0
        wood.box((0.0022 if long_mark else 0.0012, 0.0015, 0.016 if long_mark else 0.009), (x, dial[1] - 0.0055, dial[2] + 0.012), INK)
    for index in range(7):
        wood.box((0.009 + rng.uniform(0.0, 0.008), 0.0015, 0.004), (dial[0] - 0.06 + index * 0.02, dial[1] - 0.0055, dial[2] - 0.014), "#6E6A5E")
    # Asa de cuero arriba y antena telescópica detrás.
    top = feet + height
    wood.ribbon(
        tb.smooth_path(((-0.1, 0.0, top - 0.002), (-0.09, 0.0, top + 0.012), (-0.05, 0.0, top + 0.03), (0.05, 0.0, top + 0.03), (0.09, 0.0, top + 0.012), (0.1, 0.0, top - 0.002)), 3),
        0.026,
        0.005,
        LEATHER,
        center=(0.0, 0.0, top - 0.1),
    )
    cabinet = wood.finish("caja", tb.material("madera", VENEER), root)
    tb.stain(cabinet, VENEER_DARK, amount=0.6, scale=7.0, coverage=0.4, seed=127, stretch_z=0.3)
    tb.stain(cabinet, "#4A4640", amount=0.5, scale=9.0, coverage=0.2, seed=128)
    tb.dent(cabinet, (width / 2.0, front, top), radius=0.04, depth=0.005)
    tb.wobble(cabinet, amount=0.0012, scale=6.0, seed=127)

    metal = tb.MeshBuilder(seed=131)
    for x in (-0.1, 0.1):
        metal.box((0.03, 0.034, 0.006), (x, 0.0, top + 0.002), STEEL, bevel=0.002)
    antenna = Vector((width / 2.0 - 0.035, depth / 2.0 - 0.02, top))
    lean = Vector((0.16, 0.05, 1.0)).normalized()
    metal.lathe(((0.0, 0.0), (0.011, 0.0), (0.011, 0.01), (0.007, 0.016), (0.0, 0.016)), antenna, STEEL, segments=10)
    reach = 0.012
    for length, radius in ((0.2, 0.0038), (0.17, 0.0028), (0.14, 0.0019)):
        metal.bar(antenna + lean * reach, antenna + lean * (reach + length), radius, STEEL, 6)
        reach += length
    metal.sphere(0.0045, antenna + lean * reach, STEEL, segments=8)
    # Trasera: tapa de cartón prensado con rendijas y el cable de la red.
    metal.box((width - 0.05, 0.006, height - 0.05), (0.0, depth / 2.0 + 0.001, mid_z), "#5E5346", bevel=0.002, cuts=2)
    for row in range(3):
        for column in range(6):
            metal.box((0.036, 0.004, 0.006), (-0.125 + column * 0.05, depth / 2.0 + 0.0035, mid_z + 0.045 - row * 0.022), INK)
    cord = Vector((-0.15, depth / 2.0 + 0.004, feet + 0.04))
    metal.cylinder(0.008, 0.012, cord, "#2A2725", rotation=(90.0, 0.0, 0.0), segments=8)
    metal.tube(
        tb.smooth_path((cord + Vector((0.0, 0.004, 0.0)), cord + Vector((-0.005, 0.04, -0.012)), (-0.19, depth / 2.0 + 0.075, 0.006), (-0.25, depth / 2.0 + 0.06, 0.004), (-0.3, depth / 2.0 + 0.1, 0.004)), 4),
        0.003,
        "#2A2725",
        segments=6,
    )
    metal_obj = metal.finish("herrajes", tb.material("metal", STEEL), root)

    parts = {cabinet: None, metal_obj: None}
    for index, name in enumerate(("mando_volumen", "mando_brillo", "mando_sensibilidad")):
        at = (0.058 + index * 0.06, front - 0.006, mid_z - 0.05)
        knob = tb.MeshBuilder(seed=137 + index)
        knob.lathe(((0.0, 0.0), (0.023, 0.0), (0.023, 0.003), (0.019, 0.005), (0.017, 0.018), (0.014, 0.021), (0.0, 0.021)), at, BAKELITE_DARK, rotation=(90.0, 0.0, 0.0), segments=18)
        pointer = rng.uniform(-70.0, 70.0)
        a = math.radians(pointer)
        knob.box((0.003, 0.003, 0.014), (at[0] + 0.01 * math.sin(a), at[1] - 0.0215, at[2] + 0.01 * math.cos(a)), DIAL_CREAM, rotation=(0.0, pointer, 0.0))
        knob_obj = knob.finish(name, tb.material("metal", BAKELITE_DARK), root)
        tb.set_origin(knob_obj, at)
        parts[knob_obj] = None
    needle = tb.MeshBuilder(seed=149)
    needle_at = (dial[0] - DIAL_TRAVEL * 0.35, dial[1] - 0.0065, dial[2])
    needle.box((0.0022, 0.0015, 0.05), needle_at, SIGNAL_RED)
    needle_obj = needle.finish("aguja", tb.material("metal", SIGNAL_RED), root)
    tb.set_origin(needle_obj, needle_at)
    lamp = tb.MeshBuilder(seed=151)
    lamp_at = (0.028, front - 0.006, mid_z - 0.05)
    lamp.lathe(((0.0, 0.0), (0.008, 0.0), (0.008, 0.003), (0.0, 0.003)), lamp_at, STEEL, rotation=(90.0, 0.0, 0.0), segments=10)
    lamp.sphere(0.0055, (lamp_at[0], lamp_at[1] - 0.003, lamp_at[2]), EMBER_OFF, segments=8)
    lamp_obj = lamp.finish("piloto", tb.material("piloto", EMBER_OFF), root)
    tb.set_origin(lamp_obj, lamp_at)
    parts[needle_obj] = None
    parts[lamp_obj] = None

    tb.collision_box("radio", (width, depth + 0.02, height + feet), (0.0, 0.0, (height + feet) / 2.0), root)
    tb.paint(parts, ao_distance=0.06, seed=127)
    return root


def models() -> dict:
    return {
        "estufa": build_stove,
        "radio": build_radio,
    }
