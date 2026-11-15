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
from mathutils import Vector

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
MUSTARD = "#9C8546"
MUSTARD_DARK = "#786537"
CHROME = "#A2A7A3"
BRASS = "#B59A5A"
BULB_OFF = "#D9D2B8"
RUBBER_GREY = "#646B63"
RUBBER_DARK = "#474C46"
STRAP = "#3D403B"
GLASS = "#262A30"
LABEL = "#D9CDB0"
LEATHER = "#7A5234"
LEATHER_DARK = "#4E3422"
BRASS_DARK = "#8A733F"
DYNAMO_GREEN = "#3F5A52"
DYNAMO_DARK = "#2C423C"
BINO_BODY = "#4A4F50"
BINO_DARK = "#35393B"
LEATHERETTE = "#3D3833"
BINO_BAND = "#6E6248"
CLOCK_ENAMEL = "#8FA08A"
CLOCK_DARK = "#6C7C68"
BELL = "#B0A77E"

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
    mb.box((width, length, height), (0.0, 0.0, height / 2.0), OLIVE, bevel=0.009, segments=2, cuts=6)
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


def build_flashlight() -> bpy.types.Object:
    """Linterna de pilas, de petaca: caja de hojalata esmaltada y reflector al frente.

    Se apoya de pie y alumbra hacia +Y (en Godot, hacia -Z: hacia delante). El
    nodo vacío ``foco`` marca dónde colgar la luz. La ``bombilla`` lleva el
    material "bombilla_apagada"; al encenderla, el juego le pone ``bombilla.tres``.
    """
    rng = random.Random(89)
    root = tb.empty("linterna-fisico")
    width, depth, height = 0.068, 0.038, 0.108
    head = (0.0, depth / 2.0, 0.07)

    mb = tb.MeshBuilder(seed=89)
    mb.box((width, depth, height), (0.0, 0.0, height / 2.0), MUSTARD, bevel=0.007, segments=2, cuts=5)
    # Tapa de las pilas: un cerco más oscuro abajo, con su bisagra y su cierre.
    mb.box((width + 0.002, depth + 0.002, 0.016), (0.0, 0.0, 0.01), MUSTARD_DARK, bevel=0.004, segments=2)
    mb.cylinder(0.003, width * 0.7, (0.0, -depth / 2.0 - 0.001, 0.019), STEEL, rotation=(0.0, 90.0, 0.0), segments=8)
    mb.box((0.014, 0.004, 0.02), (0.0, depth / 2.0 + 0.001, 0.016), STEEL, rotation=(rng.uniform(-3.0, 3.0), 0.0, 0.0), bevel=0.0015)
    # Costillas de agarre en los cantos.
    for side in (-1.0, 1.0):
        for index in range(5):
            mb.box((0.003, depth * 0.62, 0.0045), (side * (width / 2.0 + 0.0003), 0.0, 0.032 + index * 0.0085), MUSTARD_DARK, bevel=0.001)
    # Cabezal: aro cromado y reflector hundido.
    mb.lathe(
        (
            (0.027, -0.002), (0.0325, 0.0), (0.035, 0.004), (0.035, 0.013), (0.032, 0.017), (0.0285, 0.0165),
            (0.027, 0.013), (0.02, 0.0075), (0.011, 0.004), (0.0, 0.003),
        ),
        head,
        CHROME,
        rotation=(-90.0, 0.0, 0.0),
        segments=24,
        sharp_angle=50.0,
    )
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        mb.box((0.0035, 0.008, 0.002), (head[0] + 0.0355 * math.cos(a), head[1] + 0.0085, head[2] + 0.0355 * math.sin(a)), STEEL_DARK, rotation=(0.0, 90.0 - angle, 0.0))
    # Interruptor deslizante, arriba.
    mb.box((0.016, 0.026, 0.002), (0.0, 0.0, height + 0.0005), STEEL_DARK, bevel=0.0006)
    mb.box((0.011, 0.01, 0.006), (0.0, -0.006, height + 0.0035), CHROME, bevel=0.0015)
    for index in range(3):
        mb.box((0.011, 0.0012, 0.0012), (0.0, -0.009 + index * 0.003, height + 0.0068), STEEL_DARK)
    # Detrás: pinza para el cinturón y anilla para colgarla de un botón.
    mb.box((0.017, 0.0025, 0.062), (0.0, -depth / 2.0 - 0.0045, 0.062), CHROME, rotation=(-2.5, 0.0, rng.uniform(-1.0, 1.0)), bevel=0.001)
    mb.box((0.017, 0.006, 0.008), (0.0, -depth / 2.0 - 0.002, 0.09), CHROME, bevel=0.001)
    mb.tube(
        tb.smooth_path(
            (
                (-0.011, -depth / 2.0 + 0.004, height - 0.004), (-0.012, -depth / 2.0 - 0.001, height + 0.008),
                (-0.008, -depth / 2.0 - 0.003, height + 0.019), (0.0, -depth / 2.0 - 0.004, height + 0.023),
                (0.008, -depth / 2.0 - 0.003, height + 0.019), (0.012, -depth / 2.0 - 0.001, height + 0.008),
                (0.011, -depth / 2.0 + 0.004, height - 0.004),
            ),
            steps=3,
        ),
        0.0016,
        STEEL,
        segments=6,
    )
    body = mb.finish("cuerpo", tb.material("metal", MUSTARD), root)
    tb.stain(body, "#8E7A45", amount=0.5, scale=16.0, coverage=0.35, seed=89)
    tb.stain(body, RUST, amount=0.7, scale=22.0, coverage=0.3, seed=90)
    tb.dent(body, (width / 2.0, 0.0, 0.085), radius=0.02, depth=0.0025)
    tb.wobble(body, amount=0.0005, scale=12.0, seed=89)

    bulb = tb.MeshBuilder(seed=97)
    bulb.cylinder(0.0045, 0.006, (head[0], head[1] + 0.005, head[2]), BRASS, rotation=(-90.0, 0.0, 0.0), segments=8)
    bulb.sphere(0.0058, (head[0], head[1] + 0.0105, head[2]), BULB_OFF, segments=10, scale=(1.0, 1.2, 1.0))
    bulb_obj = bulb.finish("bombilla", tb.material("bombilla_apagada", BULB_OFF), root)
    tb.set_origin(bulb_obj, (head[0], head[1] + 0.0105, head[2]))
    focus = tb.empty("foco", root)
    focus.location = (head[0], head[1] + 0.017, head[2])

    tb.collision_box("linterna", (width + 0.004, depth + 0.02, height), (0.0, 0.006, height / 2.0), root)
    tb.paint({body: None, bulb_obj: None}, ao_distance=0.04, ao=0.5, seed=89)
    return root


def _aim(direction: Vector) -> tuple[float, float, float]:
    """Giro (en grados) que lleva el eje Z de una pieza a ``direction``."""
    rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized()).to_euler()
    return tuple(math.degrees(a) for a in rotation)


def build_mask() -> bpy.types.Object:
    """Máscara antigás: careta de goma, dos oculares, válvula y filtro de bote.

    Se apoya sobre el filtro, mirando hacia -Y (en Godot, hacia +Z). Los
    ``cristales`` son un nodo propio, para poder empañarlos y agrietarlos.
    """
    root = tb.empty("mascara-fisico")
    rim_y, face_z = 0.04, 0.172
    face_r, face_d, wall = 0.098, 0.136, 0.0045

    def shape(x: float, y: float, z: float) -> Vector:
        """De la careta de revolución (eje hacia el frente) a la careta real: más estrecha y con barbilla."""
        chin = min(1.0, max(0.0, -y / face_r))
        return Vector((x * 0.86 * (1.0 - 0.2 * chin), rim_y - z, face_z + y * 1.12))

    def surface(polar: float, around: float, lift: float = 0.0) -> Vector:
        """Punto de la careta: ``polar`` grados desde la nariz y ``around`` grados sobre la horizontal."""
        p, a = math.radians(polar), math.radians(around)
        radius = (face_r + lift) * math.sin(p) ** 0.75
        return shape(radius * math.cos(a), radius * math.sin(a), (face_d + lift) * math.cos(p))

    def normal(polar: float, around: float) -> Vector:
        return (surface(polar, around, 0.01) - surface(polar, around)).normalized()

    # Careta: por dentro de la nariz al borde, y por fuera del borde a la nariz.
    rubber = tb.MeshBuilder(seed=101)
    steps = 9
    inner = [((face_r - wall) * math.sin(math.radians(90.0 * i / steps)) ** 0.75, (face_d - wall) * math.cos(math.radians(90.0 * i / steps))) for i in range(steps + 1)]
    outer = [(face_r * math.sin(math.radians(90.0 * i / steps)) ** 0.75, face_d * math.cos(math.radians(90.0 * i / steps))) for i in range(steps, -1, -1)]
    faces = rubber.lathe([*inner, (face_r - wall / 2.0, -0.004), *outer], (0.0, 0.0, 0.0), RUBBER_GREY, segments=28, sharp_angle=75.0)
    for vert in dict.fromkeys(v for face in faces for v in face.verts):
        vert.co = shape(*vert.co)
    # Válvula de voz, al frente y abajo.
    # La válvula sobresale de la careta: su base queda enterrada dentro y su frente, por delante de la nariz.
    snout = Vector((0.0, rim_y - 0.118, face_z - 0.058))
    rubber.lathe(((0.039, -0.06), (0.038, 0.022), (0.035, 0.036), (0.031, 0.04), (0.027, 0.037), (0.0, 0.037)), snout, RUBBER_GREY, rotation=(90.0, 0.0, 0.0), segments=20, sharp_angle=50.0)
    rubber.lathe(((0.03, -0.004), (0.031, 0.03), (0.027, 0.04), (0.0, 0.04)), snout + Vector((0.0, -0.016, -0.028)), RUBBER_GREY, rotation=(180.0, 0.0, 0.0), segments=18)
    # Correas: dos de sien, dos de mejilla y una de coronilla, unidas en la nuca.
    nape = Vector((0.0, rim_y + 0.092, face_z + 0.012))
    head = Vector((0.0, rim_y + 0.01, face_z))
    for side in (-1.0, 1.0):
        rubber.ribbon(tb.smooth_path((surface(88.0, 90.0 - side * 68.0, 0.001), (side * 0.07, rim_y + 0.05, face_z + 0.05), nape + Vector((side * 0.014, 0.0, 0.016))), 5), 0.018, 0.003, STRAP, center=head)
        rubber.ribbon(tb.smooth_path((surface(88.0, 90.0 - side * 128.0, 0.001), (side * 0.062, rim_y + 0.052, face_z - 0.045), nape + Vector((side * 0.014, 0.0, -0.018))), 5), 0.018, 0.003, STRAP, center=head)
        for z in (0.016, -0.018):
            rubber.box((0.006, 0.006, 0.022), nape + Vector((side * 0.02, -0.002, z)), STEEL_DARK, bevel=0.001)
    rubber.ribbon(tb.smooth_path((surface(88.0, 90.0, 0.001), (0.0, rim_y + 0.055, face_z + 0.098), nape + Vector((0.0, 0.0, 0.03))), 5), 0.018, 0.003, STRAP, center=head)
    rubber.box((0.05, 0.005, 0.066), nape, STRAP, bevel=0.002)
    rubber_obj = rubber.finish("careta", tb.material("goma", RUBBER_GREY), root)
    tb.stain(rubber_obj, RUBBER_DARK, amount=0.5, scale=13.0, coverage=0.35, seed=101)
    tb.wobble(rubber_obj, amount=0.0018, scale=11.0, seed=101)

    # Piezas de metal: cercos de los oculares, rejilla de la válvula y filtro.
    metal = tb.MeshBuilder(seed=103)
    glass = tb.MeshBuilder(seed=107)
    for side in (-1.0, 1.0):
        around = 90.0 - side * 58.0
        eye, facing = surface(29.0, around), normal(29.0, around)
        metal.lathe(((0.03, -0.008), (0.032, 0.0), (0.032, 0.011), (0.0285, 0.015), (0.025, 0.013), (0.025, 0.007)), eye, STEEL_DARK, rotation=_aim(facing), segments=20, sharp_angle=50.0)
        glass.lathe(((0.0255, 0.008), (0.014, 0.0106), (0.0, 0.0114)), eye, GLASS, rotation=_aim(facing), segments=20)
    metal.lathe(((0.0275, 0.0), (0.0275, 0.004), (0.0, 0.004)), snout + Vector((0.0, -0.036, 0.0)), STEEL, rotation=(90.0, 0.0, 0.0), segments=20)
    for radius in (0.021, 0.013):
        metal.lathe(((radius - 0.0025, 0.0), (radius - 0.0025, 0.003), (radius, 0.003), (radius, 0.0)), snout + Vector((0.0, -0.04, 0.0)), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=20, sharp_angle=30.0)
    metal.cylinder(0.005, 0.005, snout + Vector((0.0, -0.042, 0.0)), STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=8)
    can = Vector((0.0, snout.y - 0.016, 0.0))
    metal.lathe(
        ((0.0, 0.0), (0.045, 0.0), (0.051, 0.005), (0.051, 0.064), (0.047, 0.07), (0.026, 0.074), (0.026, 0.09), (0.0, 0.09)),
        can,
        OLIVE,
        segments=24,
        sharp_angle=30.0,
        jitter=0.04,
    )
    for z in (0.008, 0.052, 0.06):
        metal.lathe(((0.051, z), (0.0535, z + 0.002), (0.0535, z + 0.004), (0.051, z + 0.006)), can, OLIVE_DARK, segments=24)
    metal.lathe(((0.0515, 0.019), (0.0515, 0.046)), can, LABEL, segments=24)
    for index in range(3):
        metal.lathe(((0.052, 0.025 + index * 0.006), (0.052, 0.0275 + index * 0.006)), can, INK, segments=24)
    metal_obj = metal.finish("metal", tb.material("metal", OLIVE), root)
    tb.stain(metal_obj, RUST, amount=0.6, scale=14.0, coverage=0.22, seed=103)
    tb.dent(metal_obj, (0.05, can.y, 0.035), radius=0.03, depth=0.004)
    glass_obj = glass.finish("cristales", tb.material("vidrio", GLASS), root)

    tb.collision_box("mascara", (0.18, 0.26, face_z + 0.11), (0.0, 0.01, (face_z + 0.11) / 2.0), root)
    tb.paint({rubber_obj: None, metal_obj: None, glass_obj: None}, ao_distance=0.08, ao=0.6, seed=101)
    return root


def build_compass() -> bpy.types.Object:
    """Brújula de pulsera: caja de baquelita, bisel de latón con alzas y correa de cuero.

    Descansa boca arriba, con el norte de la esfera hacia +Y (en Godot, hacia
    -Z). Nodos propios: ``aguja`` (gira sobre su eje Z: en Godot,
    ``rotation.y``; en reposo marca el norte) y ``bisel`` (el aro giratorio).
    """
    rng = random.Random(257)
    root = tb.empty("brujula-fisico")
    lift = 0.0022  # la correa pasa por debajo de la caja
    dial_z = lift + 0.0092

    mb = tb.MeshBuilder(seed=257)
    mb.lathe(
        ((0.0, 0.0), (0.027, 0.0), (0.03, 0.003), (0.03, 0.0118), (0.0282, 0.0135), (0.0256, 0.0135), (0.0256, 0.009), (0.0, 0.009)),
        (0.0, 0.0, lift),
        BAKELITE,
        segments=28,
        sharp_angle=40.0,
        jitter=0.05,
    )
    mb.lathe(((0.0254, 0.0), (0.012, 0.0001), (0.0, 0.0002)), (0.0, 0.0, dial_z), DIAL_CREAM, segments=28)
    # Esfera: una marca cada 15°, más larga en los cuatro rumbos, y el norte en rojo.
    for index in range(24):
        angle = index * 15.0
        if index == 0:
            continue
        cardinal = index % 6 == 0
        mark = 0.007 if cardinal else 0.0035
        distance = 0.0235 - mark / 2.0
        a = math.radians(angle)
        mb.box((0.0016 if cardinal else 0.0009, mark, 0.0004), (distance * math.sin(a), distance * math.cos(a), dial_z + 0.0004), INK, rotation=(0.0, 0.0, -angle))
    mb.prism(((-0.0035, 0.0165), (0.0035, 0.0165), (0.0, 0.0238)), 0.0004, (0.0, 0.0, dial_z + 0.0004), SIGNAL_RED)
    mb.lathe(((0.0, 0.0), (0.0016, 0.0), (0.0016, 0.0024), (0.0, 0.0026)), (0.0, 0.0, dial_z + 0.0002), BRASS, segments=8)
    # Orejas de la correa.
    for side in (-1.0, 1.0):
        for x in (-0.0105, 0.0105):
            mb.box((0.003, 0.008, 0.005), (x, side * 0.0325, lift + 0.0035), BAKELITE, bevel=0.001)
        mb.bar((-0.0105, side * 0.0345, lift + 0.0035), (0.0105, side * 0.0345, lift + 0.0035), 0.0011, STEEL, 6)
    body = mb.finish("caja", tb.material("metal", BAKELITE), root)
    tb.stain(body, "#4A4038", amount=0.5, scale=60.0, coverage=0.3, seed=257)

    # Correa: pasa por debajo de la caja; un cabo lleva la hebilla y el otro, los agujeros.
    strap = tb.MeshBuilder(seed=263)
    strap.ribbon(
        tb.smooth_path(((0.0, -0.118, 0.0012), (0.0005, -0.07, 0.0012), (0.0, -0.036, 0.0013), (0.0, 0.0, 0.0011), (0.0, 0.036, 0.0013), (-0.0008, 0.08, 0.0012), (0.0, 0.142, 0.0012)), 4),
        0.018,
        0.0022,
        LEATHER,
        center=(0.0, 0.0, -1.0),
    )
    for index in range(5):
        strap.lathe(((0.0, 0.0), (0.0013, 0.0), (0.0, 0.0002)), (0.0, 0.086 + index * 0.011, 0.0024), INK, segments=6)
    strap.prism(((-0.009, 0.0), (0.009, 0.0), (0.0, 0.012)), 0.0022, (0.0, 0.142, 0.0012), LEATHER)
    buckle_y = -0.121
    for x in (-0.0115, 0.0115):
        strap.bar((x, buckle_y - 0.009, 0.0022), (x, buckle_y + 0.009, 0.0022), 0.0012, STEEL, 6)
    for y in (-0.009, 0.009):
        strap.bar((-0.0115, buckle_y + y, 0.0022), (0.0115, buckle_y + y, 0.0022), 0.0012, STEEL, 6)
    strap.bar((0.0, buckle_y + 0.008, 0.0026), (0.001, buckle_y - 0.012, 0.0032), 0.0009, STEEL, 6)
    strap.box((0.021, 0.006, 0.0032), (0.0, -0.1, 0.0018), LEATHER_DARK, bevel=0.0006)
    strap_obj = strap.finish("correa", tb.material("cuero", LEATHER), root)
    tb.stain(strap_obj, LEATHER_DARK, amount=0.55, scale=30.0, coverage=0.4, seed=263)

    bezel = tb.MeshBuilder(seed=269)
    bezel_z = lift + 0.0122
    bezel.lathe(((0.0288, 0.0), (0.0316, 0.0012), (0.0316, 0.0042), (0.0292, 0.0054), (0.0262, 0.0046), (0.0262, 0.0022)), (0.0, 0.0, bezel_z), BRASS, segments=28, sharp_angle=35.0)
    for index in range(28):
        a = math.radians(index * 360.0 / 28.0 + 6.0)
        bezel.box((0.0012, 0.0016, 0.0028), (0.0319 * math.cos(a), 0.0319 * math.sin(a), bezel_z + 0.0027), BRASS_DARK, rotation=(0.0, 0.0, math.degrees(a)))
    # Alzas para tomar rumbos: una ranura delante y un pínula detrás.
    bezel.box((0.007, 0.0022, 0.0075), (0.0, 0.0292, bezel_z + 0.0085), BRASS, bevel=0.0006)
    bezel.box((0.0012, 0.0026, 0.005), (0.0, 0.0292, bezel_z + 0.0095), INK)
    bezel.prism(((-0.0026, 0.0), (0.0026, 0.0), (0.0, 0.0075)), 0.002, (0.0, -0.0292, bezel_z + 0.0048), BRASS, rotation=(90.0, 0.0, 0.0))
    bezel_obj = bezel.finish("bisel", tb.material("metal", BRASS), root)
    tb.set_origin(bezel_obj, (0.0, 0.0, bezel_z))

    needle = tb.MeshBuilder(seed=271)
    needle_z = dial_z + 0.0026
    needle.prism(((-0.0024, 0.0), (0.0024, 0.0), (0.0, 0.0205)), 0.0006, (0.0, 0.0, needle_z), SIGNAL_RED)
    needle.prism(((0.0024, 0.0), (-0.0024, 0.0), (0.0, -0.0205)), 0.0006, (0.0, 0.0, needle_z), STEEL_DARK)
    needle.cylinder(0.0022, 0.0012, (0.0, 0.0, needle_z + 0.0004), BRASS, segments=8)
    needle_obj = needle.finish("aguja", tb.material("metal", SIGNAL_RED), root)
    tb.set_origin(needle_obj, (0.0, 0.0, needle_z))
    needle_obj.rotation_euler = (0.0, 0.0, math.radians(rng.uniform(-25.0, -12.0)))
    bpy.context.view_layer.update()

    tb.collision_box("brujula", (0.064, 0.064, lift + 0.022), (0.0, 0.0, (lift + 0.022) / 2.0), root)
    tb.collision_box("brujula_correa", (0.024, 0.275, 0.004), (0.0, 0.0115, 0.002), root)
    tb.paint({body: None, strap_obj: None, bezel_obj: None, needle_obj: None}, ao_distance=0.012, ao=0.5, seed=257)
    return root


def build_dynamo_flashlight() -> bpy.types.Object:
    """Linterna de dinamo: cuerpo de baquelita con la manivela en el costado derecho.

    Descansa sobre su base y alumbra hacia +Y (en Godot, hacia -Z). Nodos
    propios: ``manivela`` (gira sobre su eje X: en Godot, ``rotation.x``),
    ``bombilla`` (material "bombilla_apagada") y el vacío ``foco``, donde
    colgar la luz.
    """
    rng = random.Random(277)
    root = tb.empty("linterna_dinamo-fisico")
    width, length, height = 0.058, 0.105, 0.05
    mid_z = height / 2.0
    head = (0.0, length / 2.0, mid_z)

    mb = tb.MeshBuilder(seed=277)
    mb.box((width, length, height), (0.0, 0.0, mid_z), DYNAMO_GREEN, bevel=0.013, segments=3, cuts=5, jitter=0.03)
    # Estrías para los dedos, arriba, y la placa del fabricante en el costado izquierdo.
    for index in range(6):
        mb.box((0.03, 0.0042, 0.003), (0.0, -0.04 + index * 0.0095, height + 0.0006), DYNAMO_DARK, bevel=0.001)
    mb.box((0.0016, 0.04, 0.015), (-width / 2.0 - 0.0004, -0.008, mid_z), BRASS, rotation=(rng.uniform(-1.5, 1.5), 0.0, 0.0), bevel=0.0006)
    for y in (-0.024, 0.008):
        mb.cylinder(0.0018, 0.0016, (-width / 2.0 - 0.0012, y, mid_z), STEEL_DARK, rotation=(0.0, 90.0, 0.0), segments=6)
    # Cabezal: aro cromado y reflector hundido.
    mb.lathe(
        (
            (0.02, -0.002), (0.0228, 0.0), (0.0245, 0.003), (0.0245, 0.0095), (0.0226, 0.0125), (0.0202, 0.0122),
            (0.019, 0.0095), (0.014, 0.0055), (0.008, 0.003), (0.0, 0.0022),
        ),
        head,
        CHROME,
        rotation=(-90.0, 0.0, 0.0),
        segments=24,
        sharp_angle=50.0,
    )
    # Asiento de la manivela y ojal del cordón.
    hub = Vector((width / 2.0, -0.006, mid_z))
    mb.lathe(((0.016, -0.002), (0.016, 0.0028), (0.013, 0.0032), (0.0, 0.0032)), hub, DYNAMO_DARK, rotation=(0.0, 90.0, 0.0), segments=18, sharp_angle=35.0)
    eyelet = Vector((0.0, -length / 2.0, mid_z + 0.006))
    mb.lathe(((0.0055, -0.001), (0.0055, 0.004), (0.003, 0.005), (0.0, 0.005)), eyelet, STEEL, rotation=(90.0, 0.0, 0.0), segments=10)
    mb.tube(
        tb.smooth_path(
            (
                eyelet + Vector((0.0035, -0.0055, 0.0)), (0.012, -length / 2.0 - 0.02, 0.012), (0.03, -length / 2.0 - 0.05, 0.0024),
                (0.02, -length / 2.0 - 0.1, 0.0022), (-0.02, -length / 2.0 - 0.105, 0.0022), (-0.036, -length / 2.0 - 0.06, 0.0024),
                (-0.014, -length / 2.0 - 0.022, 0.012), eyelet + Vector((-0.0035, -0.0055, 0.0)),
            ),
            5,
        ),
        0.0018,
        RUBBER,
        segments=6,
    )
    body = mb.finish("cuerpo", tb.material("metal", DYNAMO_GREEN), root)
    tb.stain(body, "#5F776E", amount=0.5, scale=20.0, coverage=0.3, seed=277)
    tb.stain(body, DYNAMO_DARK, amount=0.5, scale=13.0, coverage=0.3, seed=278)
    tb.dent(body, (-width / 2.0, 0.03, height * 0.75), radius=0.018, depth=0.002)

    crank = tb.MeshBuilder(seed=281)
    reach = Vector((0.0, -math.cos(math.radians(22.0)), math.sin(math.radians(22.0))))
    crank.lathe(((0.011, 0.0), (0.011, 0.0035), (0.007, 0.0065), (0.0, 0.0065)), hub + Vector((0.0032, 0.0, 0.0)), CHROME, rotation=(0.0, 90.0, 0.0), segments=16, sharp_angle=35.0)
    crank.box((0.0036, 0.05, 0.0095), hub + Vector((0.0058, 0.0, 0.0)) + reach * 0.02, CHROME, rotation=(-22.0, 0.0, 0.0), bevel=0.0012)
    crank.lathe(((0.0042, 0.0), (0.0062, 0.004), (0.0066, 0.015), (0.005, 0.019), (0.0, 0.019)), hub + Vector((0.0076, 0.0, 0.0)) + reach * 0.04, BAKELITE, rotation=(0.0, 90.0, 0.0), segments=12)
    crank_obj = crank.finish("manivela", tb.material("metal", CHROME), root)
    tb.set_origin(crank_obj, hub + Vector((0.0032, 0.0, 0.0)))

    bulb = tb.MeshBuilder(seed=283)
    bulb.cylinder(0.0036, 0.005, (head[0], head[1] + 0.0045, head[2]), BRASS, rotation=(-90.0, 0.0, 0.0), segments=8)
    bulb.sphere(0.0046, (head[0], head[1] + 0.0085, head[2]), BULB_OFF, segments=10, scale=(1.0, 1.2, 1.0))
    bulb_obj = bulb.finish("bombilla", tb.material("bombilla_apagada", BULB_OFF), root)
    tb.set_origin(bulb_obj, (head[0], head[1] + 0.0085, head[2]))
    focus = tb.empty("foco", root)
    focus.location = (head[0], head[1] + 0.013, head[2])

    tb.collision_box("linterna_dinamo", (width, length + 0.012, height), (0.0, 0.006, mid_z), root)
    tb.collision_box("linterna_dinamo_manivela", (0.03, 0.055, 0.03), (width / 2.0 + 0.015, -0.025, mid_z + 0.007), root)
    tb.paint({body: None, crank_obj: None, bulb_obj: None}, ao_distance=0.03, ao=0.5, seed=277)
    return root


def build_binoculars() -> bpy.types.Object:
    """Prismáticos de prismas de Porro, tumbados: los objetivos hacia +Y (en Godot, hacia -Z) y los oculares hacia -Y.

    Nodos propios: ``lentes`` (los cuatro cristales, con el material
    ``vidrio``: son los que pueden delatarte con un reflejo) y
    ``rueda_enfoque`` (gira sobre su eje Y: en Godot, ``rotation.z``).
    """
    rng = random.Random(317)
    root = tb.empty("prismaticos-fisico")
    mid_z = 0.0276
    hinge_z = mid_z + 0.004
    house_x, house_y = 0.052, -0.012

    body = tb.MeshBuilder(seed=317)
    glass = tb.MeshBuilder(seed=331)
    for side in (-1.0, 1.0):
        # Caja de los prismas, forrada, con sus dos tapas atornilladas.
        # Es ancha: el objetivo cae en su mitad de fuera y el ocular, en la de dentro.
        body.box((0.068, 0.05, 0.05), (side * house_x, house_y, mid_z), LEATHERETTE, bevel=0.012, segments=2, cuts=3, jitter=0.05)
        for face in (-1.0, 1.0):
            plate_y = house_y + face * 0.0255
            body.box((0.056, 0.003, 0.038), (side * house_x, plate_y, mid_z), BINO_BODY, bevel=0.0012)
            for dx, dz in ((-0.023, 0.014), (0.023, -0.014)):
                body.cylinder(0.0016, 0.0012, (side * house_x + dx, plate_y + face * 0.0017, mid_z + dz), STEEL, rotation=(90.0, 0.0, 0.0), segments=6)
        # Tubo del objetivo, con su aro delantero.
        objective = (side * 0.06, house_y + 0.0245, mid_z)
        body.lathe(
            ((0.0235, 0.0), (0.0235, 0.004), (0.0222, 0.007), (0.0245, 0.042), (0.027, 0.048), (0.027, 0.062), (0.0256, 0.0652), (0.0236, 0.0635), (0.0226, 0.057)),
            objective,
            BINO_BODY,
            rotation=(-90.0, 0.0, 0.0),
            segments=22,
            sharp_angle=35.0,
            jitter=0.04,
        )
        body.lathe(((0.0272, 0.05), (0.0277, 0.0515), (0.0277, 0.0585), (0.0272, 0.06)), objective, BINO_BAND, rotation=(-90.0, 0.0, 0.0), segments=22)
        glass.lathe(((0.0228, 0.0572), (0.012, 0.0592), (0.0, 0.0598)), objective, GLASS, rotation=(-90.0, 0.0, 0.0), segments=22)
        # Ocular, más cerca del centro que el objetivo, con su concha.
        eyepiece = (side * 0.034, house_y - 0.024, mid_z)
        body.lathe(
            ((0.0132, 0.0), (0.0132, 0.011), (0.0156, 0.013), (0.0156, 0.02), (0.0136, 0.022), (0.014, 0.029), (0.0176, 0.035), (0.0176, 0.0385), (0.0152, 0.0398), (0.0128, 0.036)),
            eyepiece,
            BINO_DARK,
            rotation=(90.0, 0.0, 0.0),
            segments=18,
            sharp_angle=35.0,
        )
        glass.lathe(((0.013, 0.0362), (0.006, 0.0357), (0.0, 0.0355)), eyepiece, GLASS, rotation=(90.0, 0.0, 0.0), segments=18)
        # Brazos de la bisagra y anilla de la correa.
        for arm_y in (house_y - 0.016, house_y + 0.016):
            body.box((0.02, 0.0135, 0.011), (side * 0.012, arm_y, hinge_z), BINO_BODY, bevel=0.002)
        body.box((0.0045, 0.011, 0.007), (side * (house_x + 0.0358), house_y - 0.008, mid_z + 0.012), STEEL, bevel=0.001)
    # Eje de la bisagra, con su tapa, y puente de los oculares.
    body.lathe(((0.0, 0.0), (0.0062, 0.0), (0.0078, 0.002), (0.0078, 0.048), (0.0062, 0.05), (0.0, 0.05)), (0.0, house_y - 0.025, hinge_z), BINO_DARK, rotation=(-90.0, 0.0, 0.0), segments=14)
    body.bar((-0.034, house_y - 0.037, hinge_z), (0.034, house_y - 0.037, hinge_z), 0.0042, BINO_BODY, 8)
    body.bar((0.0, house_y - 0.037, hinge_z), (0.0, house_y - 0.025, hinge_z), 0.0036, BINO_BODY, 8)
    body_obj = body.finish("cuerpo", tb.material("metal", BINO_BODY), root)
    tb.stain(body_obj, BRASS_DARK, amount=0.45, scale=30.0, coverage=0.2, seed=317)
    tb.stain(body_obj, "#5A5F60", amount=0.4, scale=18.0, coverage=0.3, seed=318)
    tb.dent(body_obj, (0.06, house_y + 0.064, mid_z + 0.027), radius=0.02, depth=0.002)
    glass_obj = glass.finish("lentes", tb.material("vidrio", GLASS), root)

    wheel = tb.MeshBuilder(seed=337)
    wheel_at = (0.0, house_y, hinge_z)
    wheel.lathe(((0.0, -0.0085), (0.0115, -0.0085), (0.0125, -0.007), (0.0125, 0.007), (0.0115, 0.0085), (0.0, 0.0085)), wheel_at, BINO_DARK, rotation=(-90.0, 0.0, 0.0), segments=20, sharp_angle=35.0)
    for index in range(20):
        a = math.radians(index * 18.0 + 4.0)
        wheel.box((0.0014, 0.013, 0.0016), (0.0127 * math.cos(a), house_y, hinge_z + 0.0127 * math.sin(a)), BINO_BODY, rotation=(0.0, 90.0 - math.degrees(a), 0.0))
    wheel_obj = wheel.finish("rueda_enfoque", tb.material("metal", BINO_DARK), root)
    tb.set_origin(wheel_obj, wheel_at)

    # Correa: de anilla a anilla, tendida sobre la mesa por detrás de los oculares.
    strap = tb.MeshBuilder(seed=347)
    lug_y, lug_z = house_y - 0.008, mid_z + 0.012
    sway = rng.uniform(-0.01, 0.01)
    strap.ribbon(
        tb.smooth_path(
            (
                (-0.0905, lug_y, lug_z), (-0.1, lug_y - 0.006, lug_z - 0.004), (-0.112, lug_y - 0.03, 0.006), (-0.108, lug_y - 0.07, 0.0014),
                (-0.07 + sway, lug_y - 0.125, 0.0012), (0.0, lug_y - 0.15, 0.0012), (0.07, lug_y - 0.12 + sway, 0.0012),
                (0.109, lug_y - 0.07, 0.0014), (0.112, lug_y - 0.03, 0.006), (0.1, lug_y - 0.006, lug_z - 0.004), (0.0905, lug_y, lug_z),
            ),
            5,
        ),
        0.011,
        0.0018,
        LEATHER,
        center=(0.0, lug_y - 0.04, -0.6),
    )
    strap_obj = strap.finish("correa", tb.material("cuero", LEATHER), root)
    tb.stain(strap_obj, LEATHER_DARK, amount=0.55, scale=25.0, coverage=0.4, seed=347)

    tb.collision_box("prismaticos", (0.18, 0.15, 0.056), (0.0, 0.006, 0.028), root)
    tb.paint({body_obj: None, glass_obj: None, wheel_obj: None, strap_obj: None}, ao_distance=0.03, ao=0.5, seed=317)
    return root


def build_alarm_clock() -> bpy.types.Object:
    """Despertador de cuerda de dos campanas, de pie sobre sus tres patas, con la esfera hacia -Y.

    Nodos propios, con el origen en su eje: ``aguja_horas``, ``aguja_minutos``
    y ``aguja_alarma`` (giran en el sentido del reloj con ``rotation.z``
    negativo en Godot; a 0° marcan las doce), ``martillo`` (el badajo, que
    oscila entre las campanas con ``rotation.z``) y ``llave_cuerda`` (gira
    sobre su eje Y: en Godot, ``rotation.z``).
    """
    rng = random.Random(349)
    root = tb.empty("despertador-fisico")
    radius, half_d = 0.052, 0.023
    centre = Vector((0.0, 0.0, 0.068))
    dial_y = -(half_d - 0.004)  # la esfera va hundida tras el aro

    def face(distance: float, angle: float, y: float) -> tuple[float, float, float]:
        """Punto de la esfera a ``distance`` del centro y ``angle`` grados desde las doce, en el sentido del reloj."""
        a = math.radians(angle)
        return (centre.x + distance * math.sin(a), y, centre.z + distance * math.cos(a))

    mb = tb.MeshBuilder(seed=349)
    # Caja esmaltada, aro cromado y esfera.
    mb.lathe(
        ((0.0, -half_d), (radius - 0.007, -half_d), (radius, -half_d + 0.005), (radius, half_d - 0.007), (radius - 0.0045, half_d - 0.004), (0.0, half_d - 0.004)),
        centre,
        CLOCK_ENAMEL,
        rotation=(90.0, 0.0, 0.0),
        segments=32,
        sharp_angle=35.0,
        jitter=0.03,
    )
    mb.lathe(
        ((radius + 0.0005, half_d - 0.008), (radius + 0.0026, half_d - 0.006), (radius + 0.0026, half_d - 0.001), (radius - 0.001, half_d + 0.0012), (radius - 0.0046, half_d - 0.0003), (radius - 0.0046, half_d - 0.004)),
        centre,
        CHROME,
        rotation=(90.0, 0.0, 0.0),
        segments=32,
        sharp_angle=35.0,
    )
    mb.lathe(((radius - 0.0047, half_d - 0.0039), (0.02, half_d - 0.0038), (0.0, half_d - 0.0037)), centre, DIAL_CREAM, rotation=(90.0, 0.0, 0.0), segments=32)
    for index in range(60):
        angle = index * 6.0
        if index % 5 == 0:
            quarter = index % 15 == 0
            length = 0.009 if quarter else 0.0065
            mb.box((0.0032 if quarter else 0.0018, 0.0005, length), face(radius - 0.009 - length / 2.0, angle, dial_y - 0.0003), INK, rotation=(0.0, angle, 0.0))
        else:
            mb.box((0.0007, 0.0005, 0.0022), face(radius - 0.0105, angle, dial_y - 0.0003), INK, rotation=(0.0, angle, 0.0))
    # Tres patas: dos delante y una detrás.
    for foot in (Vector((-0.036, -0.012, 0.0055)), Vector((0.036, -0.012, 0.0055)), Vector((0.0, 0.034, 0.0055))):
        top = Vector((foot.x * 0.72, foot.y * 0.55, centre.z - radius + 0.012 + abs(foot.x) * 0.18))
        mb.bar(top, foot, 0.0034, CHROME, 8)
        mb.sphere(0.0055, foot, CHROME, segments=10)
    # Campanas sobre sus postes, y el asa que las une.
    bell_r, lean = 0.023, 33.0
    tops = []
    for side in (-1.0, 1.0):
        axis = Vector((side * math.sin(math.radians(lean)), 0.0, math.cos(math.radians(lean))))
        base = centre + axis * (radius + 0.02)
        mb.bar(centre + axis * (radius - 0.003), base + axis * 0.004, 0.0032, CHROME, 8)
        mb.lathe(
            ((0.0, 0.0012), (bell_r - 0.002, 0.0006), (bell_r, 0.0), (bell_r + 0.0005, 0.004), (bell_r - 0.0025, 0.011), (bell_r - 0.009, 0.0175), (0.006, 0.0205), (0.0, 0.021)),
            base,
            BELL,
            rotation=_aim(axis),
            segments=24,
            sharp_angle=50.0,
            jitter=0.04,
        )
        mb.lathe(((0.0, 0.0), (0.0048, 0.0), (0.0048, 0.003), (0.003, 0.0055), (0.0, 0.0055)), base + axis * 0.0205, CHROME, rotation=_aim(axis), segments=8)
        tops.append(base + axis * 0.0255)
    arch = centre.z + radius + 0.058
    mb.tube(tb.smooth_path((tops[0], (-0.04, 0.0, arch - 0.01), (-0.02, 0.0, arch - 0.002), (0.0, 0.0, arch), (0.02, 0.0, arch - 0.002), (0.04, 0.0, arch - 0.01), tops[1]), 4), 0.0026, CHROME, segments=8)
    # Trasera: mandos de poner en hora y la palanca de la alarma; segunda llave, la del timbre.
    back = half_d
    for x in (-0.014, 0.014):
        mb.lathe(((0.0, 0.0), (0.0045, 0.0), (0.0045, 0.006), (0.0, 0.006)), (x, back, centre.z + 0.02), CHROME, rotation=(-90.0, 0.0, 0.0), segments=10)
    mb.box((0.004, 0.006, 0.012), (0.0, back + 0.002, centre.z + 0.036), CHROME, rotation=(0.0, rng.uniform(-18.0, 18.0), 0.0), bevel=0.001)

    def key(builder: tb.MeshBuilder, at: Vector, turn: float) -> None:
        """Llave de mariposa en la trasera."""
        builder.cylinder(0.0022, 0.012, at + Vector((0.0, 0.006, 0.0)), CHROME, rotation=(90.0, 0.0, 0.0), segments=8)
        builder.prism(((-0.011, -0.004), (-0.004, -0.0065), (0.004, -0.0065), (0.011, -0.004), (0.011, 0.004), (0.004, 0.0065), (-0.004, 0.0065), (-0.011, 0.004)), 0.0022, at + Vector((0.0, 0.012, 0.0)), CHROME, rotation=(90.0, turn, 0.0), bevel=0.0007)

    key(mb, Vector((0.022, back, centre.z - 0.014)), 25.0)
    body = mb.finish("caja", tb.material("metal", CLOCK_ENAMEL), root)
    tb.stain(body, CLOCK_DARK, amount=0.5, scale=22.0, coverage=0.3, seed=349)
    tb.stain(body, RUST, amount=0.6, scale=17.0, coverage=0.16, seed=350)
    tb.dent(body, (radius * 0.7, 0.0, centre.z - radius * 0.7), radius=0.022, depth=0.0025)

    parts = {body: None}
    hands = (
        ("aguja_alarma", 0.022, 0.0022, 0.0012, BRASS_DARK, 212.0),
        ("aguja_horas", 0.026, 0.0046, 0.0024, INK, 304.5),
        ("aguja_minutos", 0.039, 0.003, 0.0036, INK, 54.0),
    )
    for name, length, width, lift, color, shown in hands:
        hand = tb.MeshBuilder(seed=353)
        y = dial_y - lift
        hand.prism(((-width / 2.0, -0.006), (width / 2.0, -0.006), (width * 0.3, length - 0.004), (0.0, length), (-width * 0.3, length - 0.004)), 0.0006, (centre.x, y, centre.z), color, rotation=(90.0, 0.0, 0.0))
        hand.cylinder(0.003 if name != "aguja_minutos" else 0.0042, 0.0008 if name != "aguja_minutos" else 0.0018, (centre.x, y - (0.0 if name != "aguja_minutos" else 0.0006), centre.z), BRASS if name == "aguja_minutos" else color, rotation=(90.0, 0.0, 0.0), segments=10)
        hand_obj = hand.finish(name, tb.material("metal", color), root)
        tb.set_origin(hand_obj, (centre.x, y, centre.z))
        # Un giro positivo sobre Y, en Blender, va en el sentido del reloj visto de frente.
        hand_obj.rotation_euler = (0.0, math.radians(shown), 0.0)
        parts[hand_obj] = None

    hammer = tb.MeshBuilder(seed=359)
    pivot = centre + Vector((0.0, 0.0, radius - 0.002))
    hammer.bar(pivot, pivot + Vector((0.0, 0.0, 0.024)), 0.0018, CHROME, 6)
    hammer.sphere(0.0058, pivot + Vector((0.0, 0.0, 0.027)), CHROME, segments=10)
    hammer_obj = hammer.finish("martillo", tb.material("metal", CHROME), root)
    tb.set_origin(hammer_obj, pivot)
    parts[hammer_obj] = None

    wind = tb.MeshBuilder(seed=367)
    wind_at = Vector((-0.022, back, centre.z - 0.014))
    key(wind, wind_at, -40.0)
    wind_obj = wind.finish("llave_cuerda", tb.material("metal", CHROME), root)
    tb.set_origin(wind_obj, wind_at)
    parts[wind_obj] = None
    bpy.context.view_layer.update()

    tb.collision_box("despertador", (0.125, 0.07, arch + 0.003), (0.0, 0.006, (arch + 0.003) / 2.0), root)
    tb.paint(parts, ao_distance=0.03, ao=0.5, seed=349)
    return root


def models() -> dict:
    return {
        "dosimetro": build_dosimeter,
        "linterna": build_flashlight,
        "mascara": build_mask,
        "brujula": build_compass,
        "linterna_dinamo": build_dynamo_flashlight,
        "prismaticos": build_binoculars,
        "despertador": build_alarm_clock,
    }
