"""El botín del taller: lo que se encuentra en los garajes, los talleres, los
coches del atasco y los trasteros.

- Para trabajar: la cinta aislante, la caja de clavos, la llave inglesa y los
  alicates (las dos herramientas llevan el nodo ``agarre``).
- Electricidad: la pila de petaca de 4,5 V (la de la linterna), las válvulas de
  radio en su caja y la batería de un coche.
- Luz y fuego: el quinqué de queroseno (con el nodo ``foco``, donde iría su luz) y
  el hornillo de queroseno de latón.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Todo
descansa sobre z = 0 y enseña su frente hacia -Y. Las reglas del botín (nada
está intacto) están en tools/blender/botin_bpy.py.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Matrix, Vector

import botin_bpy as bb
import tumansk_bpy as tb

INK = "#1B1A22"
RUST = "#7E4128"
DIRT = "#4E4233"
GREASE = "#2E2A24"
STEEL = "#7D817E"
STEEL_LIGHT = "#9AA09C"
STEEL_DARK = "#4A4E4C"
TAPE_BLUE = "#2F4F7A"
TAPE_BLUE_DARK = "#26405F"
CORE = "#C8B88A"
CARDBOARD_GREY = "#8C8470"
LABEL = "#D6CDB0"
NAIL = "#8A8E8A"
BATTERY_BLUE = "#2F4A7A"
BATTERY_YELLOW = "#C8A040"
PITCH = "#1E1C1A"
BRASS = "#B59A5A"
BRASS_DARK = "#7E6A3A"
ZINC = "#8A8E8A"
CORROSION = "#B4C2AE"
VERDIGRIS = "#6E9A7E"
RUBBER_RED = "#9A3A2E"
RUBBER_RED_DARK = "#6E2A22"
GLASS = "#7E8C88"
GETTER = "#BDBFB8"
ANODE = "#3A3E40"
TUBE_BOX = "#C07A3A"
TUBE_BOX_DARK = "#8A5428"
LAMP_GREEN = "#3F5A4E"
LAMP_GREEN_DARK = "#2E443A"
CHIMNEY = "#C3C8BC"
SOOT = "#22201E"
STOVE_BRASS = "#9A7840"
TARNISH = "#6A5A3A"
EBONITE = "#262628"
MASTIC = "#151414"
LEAD = "#7C7C78"
CAP = "#2E2E30"


def _rust_and_dirt(obj: bpy.types.Object, seed: int, rust: float = 0.2, dirt: float = 0.2) -> None:
    tb.stain(obj, RUST, amount=0.75, scale=60.0, coverage=rust, seed=seed)
    tb.stain(obj, DIRT, amount=0.45, scale=35.0, coverage=dirt, seed=seed + 1)


# --------------------------------------------------------------------------
# Para trabajar
# --------------------------------------------------------------------------


def build_tape() -> bpy.types.Object:
    """Cinta aislante: el rollo azul de PVC tumbado, con su canuto de cartón y la
    punta despegada, de pie sobre su canto. Polvo pegado en los cantos."""
    root = tb.empty("cinta_aislante-fisico")
    outer, inner, core, w = 0.031, 0.0195, 0.0172, 0.019
    mb = tb.MeshBuilder(seed=801)
    side = [(outer - 0.003 * k, w) for k in range(5)]
    mb.lathe([(inner, 0.0), *[(outer - 0.003 * k, 0.0) for k in range(4, -1, -1)], (outer, w), *side[1:], (inner, w), (inner, 0.0)], (0.0, 0.0, 0.0), TAPE_BLUE, segments=36, sharp_angle=50.0)
    mb.lathe([(core, -0.0004), (inner, -0.0004), (inner, w + 0.0004), (core, w + 0.0004), (core, -0.0004)], (0.0, 0.0, 0.0), CORE, segments=36, sharp_angle=50.0)
    # La punta: tramos de cinta que salen tangentes al rollo y se curvan hacia fuera.
    start = 35.0
    point = bb.around(outer + 0.0003, start, 0.0)
    heading = math.radians(start)
    for k in range(7):
        length = 0.008
        direction = Vector((math.cos(heading), math.sin(heading), 0.0))
        middle = point + direction * (length / 2.0)
        mb.box((length + 0.0006, 0.0006, w), (middle.x, middle.y, w / 2.0), TAPE_BLUE, rotation=(0.0, 0.0, math.degrees(heading)))
        point = point + direction * length
        heading -= math.radians(9.0 + k * 2.0)
    roll = mb.finish("cinta", tb.material("plastico", TAPE_BLUE), root)

    def layers(co: Vector) -> str | None:
        radial = math.hypot(co.x, co.y)
        if inner + 0.001 < radial < outer - 0.001 and (co.z < 0.0005 or co.z > w - 0.0005):
            return TAPE_BLUE_DARK if int((radial - inner) / 0.003) % 2 else None
        return None

    bb.recolor(roll, layers)
    tb.stain(roll, "#7A7A72", amount=0.5, scale=90.0, coverage=0.25, seed=802)
    tb.stain(roll, DIRT, amount=0.4, scale=40.0, coverage=0.2, seed=803)
    tb.collision_box("cinta", (0.07, 0.07, w), (0.004, 0.004, w / 2.0), root)
    tb.paint({roll: None}, samples=12, ao=0.35, ao_distance=0.03, seed=801)
    return root


def _nail(mb: tb.MeshBuilder, head: Vector, tip: Vector, color: str) -> None:
    axis = (tip - head).normalized()
    mb.bar(head, tip - axis * 0.004, 0.0013, color, 6)
    mb.cylinder(0.0013, 0.004, tip - axis * 0.002, color, rotation=[math.degrees(r) for r in Vector((0.0, 0.0, 1.0)).rotation_difference(axis).to_euler()], radius_top=0.0002, segments=6)
    mb.cylinder(0.0033, 0.0009, head - axis * 0.00045, color, rotation=[math.degrees(r) for r in Vector((0.0, 0.0, 1.0)).rotation_difference(axis).to_euler()], segments=8)


def build_nails() -> bpy.types.Object:
    """Una caja de clavos de cartón gris, abierta, con la tapa al lado y los clavos
    revueltos; unos cuantos, caídos en la mesa. Alguno, oxidado."""
    rng = random.Random(811)
    root = tb.empty("clavos-fisico")
    w, d, h, t = 0.095, 0.058, 0.034, 0.0018
    box = tb.MeshBuilder(seed=811)
    box.box((w, d, t), (0.0, 0.0, t / 2.0), CARDBOARD_GREY, bevel=0.0006)
    for side in (-1.0, 1.0):
        box.box((w, t, h), (0.0, side * (d / 2.0 - t / 2.0), h / 2.0), CARDBOARD_GREY, bevel=0.0006, cuts=2)
        box.box((t, d - 2.0 * t, h), (side * (w / 2.0 - t / 2.0), 0.0, h / 2.0), CARDBOARD_GREY, bevel=0.0006)
    # La tapa, boca abajo al lado, con la etiqueta en lo que era su cara de arriba.
    lid_center = Vector((0.0, -0.004, 0.0))
    lid_x = w / 2.0 + 0.06
    box.box((w + 0.004, d + 0.004, 0.0018), (lid_x, lid_center.y, 0.0009), CARDBOARD_GREY, rotation=(0.0, 0.0, -12.0), bevel=0.0006)
    for side in (-1.0, 1.0):
        offset = Matrix.Rotation(math.radians(-12.0), 3, "Z") @ Vector((0.0, side * (d / 2.0 + 0.001), 0.0))
        box.box((w + 0.004, 0.0018, 0.012), (lid_x + offset.x, lid_center.y + offset.y, 0.006), CARDBOARD_GREY, rotation=(0.0, 0.0, -12.0), bevel=0.0005)
        offset = Matrix.Rotation(math.radians(-12.0), 3, "Z") @ Vector((side * (w / 2.0 + 0.001), 0.0, 0.0))
        box.box((0.0018, d + 0.004, 0.012), (lid_x + offset.x, lid_center.y + offset.y, 0.006), CARDBOARD_GREY, rotation=(0.0, 0.0, -12.0), bevel=0.0005)
    box.box((0.054, 0.0005, 0.02), (0.0, -d / 2.0 - 0.0003, h / 2.0), LABEL)
    for k in range(3):
        box.box((0.04 - k * 0.01, 0.0005, 0.0018), (-0.004, -d / 2.0 - 0.0007, h / 2.0 + 0.005 - k * 0.005), INK)
    carton = box.finish("caja", tb.material("carton", CARDBOARD_GREY), root)
    tb.stain(carton, "#A8987A", amount=0.5, scale=40.0, coverage=0.3, seed=812, stretch_z=0.5)
    tb.stain(carton, GREASE, amount=0.45, scale=60.0, coverage=0.22, seed=813)

    nails = tb.MeshBuilder(seed=814)
    for k in range(30):
        x = rng.uniform(-w / 2.0 + 0.012, w / 2.0 - 0.012)
        y = rng.uniform(-d / 2.0 + 0.008, d / 2.0 - 0.008)
        z = rng.uniform(h - 0.012, h - 0.002)
        turn = rng.uniform(-35.0, 35.0) + (180.0 if k % 2 else 0.0)
        tilt = rng.uniform(-8.0, 8.0)
        length = rng.uniform(0.045, 0.06)
        direction = Matrix.Rotation(math.radians(turn), 3, "Z") @ Vector((math.cos(math.radians(tilt)), 0.0, math.sin(math.radians(tilt))))
        center = Vector((x, y, z))
        head = center - direction * (length / 2.0)
        tip = center + direction * (length / 2.0)
        for point in (head, tip):
            point.x = max(-w / 2.0 + t + 0.002, min(w / 2.0 - t - 0.002, point.x))
            point.y = max(-d / 2.0 + t + 0.002, min(d / 2.0 - t - 0.002, point.y))
        _nail(nails, head, tip, NAIL if rng.random() > 0.25 else RUST)
    nails.box((w - 2.0 * t - 0.004, d - 2.0 * t - 0.004, h - 0.014), (0.0, 0.0, t + (h - 0.014) / 2.0), "#5A5C5A")
    for x, y, turn in ((-0.07, -0.045, 20.0), (-0.055, -0.058, -60.0), (0.02, -0.058, 5.0), (0.035, -0.05, 130.0), (-0.012, -0.066, 80.0)):
        direction = Vector((math.cos(math.radians(turn)), math.sin(math.radians(turn)), 0.0))
        center = Vector((x, y, 0.0014))
        _nail(nails, center - direction * 0.026, center + direction * 0.026, NAIL)
    nail_obj = nails.finish("clavos", tb.material("metal", NAIL), root)
    tb.stain(nail_obj, RUST, amount=0.6, scale=120.0, coverage=0.22, seed=815)
    tb.collision_box("caja", (w, d, h), (0.0, 0.0, h / 2.0), root)
    tb.paint({carton: None, nail_obj: None}, samples=10, ao=0.4, ao_distance=0.025, seed=811)
    return root


def build_wrench() -> bpy.types.Object:
    """Llave inglesa: tumbada, con las bocas hacia +X, el tornillo sinfín asomando y
    el agujero para colgarla. Acero con grasa vieja y óxido en las juntas."""
    root = tb.empty("llave_inglesa-fisico")
    mb = tb.MeshBuilder(seed=821)
    thick, head_thick = 0.0085, 0.013
    end = [(-0.125 + 0.011 * (1.0 - math.cos(math.radians(a))), 0.011 * math.sin(math.radians(a))) for a in range(-90, 91, 30)]
    handle = [(0.055, -0.0085), (0.055, 0.0085), *reversed(end)]
    mb.prism(handle, thick, (0.0, 0.0, thick / 2.0), STEEL, bevel=0.0018, segments=2)
    # Las acanaladuras del mango y el agujero para colgarla.
    for side in (-1.0, 1.0):
        mb.box((0.11, 0.0022, 0.0012), (-0.045, side * 0.0045, thick + 0.0002), STEEL_DARK, bevel=0.0005)
    bb.disc(mb, (-0.112, 0.0, thick), (0.0, 0.0, 1.0), 0.0045, INK, thickness=0.0006, segments=12)
    # La cabeza, la boca fija arriba y la móvil abajo.
    mb.prism(bb.rounded_rect(0.042, 0.036, 0.008, 3), head_thick, (0.074, 0.003, head_thick / 2.0), STEEL, bevel=0.0018, segments=2)
    fixed = [(0.07, 0.013), (0.112, 0.013), (0.117, 0.018), (0.115, 0.027), (0.09, 0.031), (0.07, 0.024)]
    mb.prism(fixed, head_thick - 0.002, (0.0, 0.0, head_thick / 2.0), STEEL_LIGHT, bevel=0.0015)
    moving = [(0.078, -0.023), (0.094, -0.026), (0.113, -0.019), (0.117, -0.011), (0.112, -0.005), (0.078, -0.005)]
    mb.prism(moving, head_thick - 0.003, (0.0, 0.0, head_thick / 2.0), STEEL_LIGHT, bevel=0.0015)
    # El sinfín, moleteado, en su ventana.
    worm = Vector((0.064, -0.014, head_thick * 0.55))
    mb.cylinder(0.0058, 0.016, worm, STEEL_DARK, rotation=(90.0, 0.0, 0.0), segments=12)
    for k in range(6):
        mb.lathe([(0.0058, -0.0008), (0.0068, 0.0), (0.0058, 0.0008)], worm + Vector((0.0, -0.0065 + k * 0.0026, 0.0)), STEEL, rotation=(90.0, 0.0, 0.0), segments=12)
    wrench = mb.finish("llave", tb.material("metal", STEEL), root)
    _rust_and_dirt(wrench, 822, rust=0.18, dirt=0.3)
    tb.stain(wrench, GREASE, amount=0.5, scale=45.0, coverage=0.2, seed=824)
    bb.grip(root, (-0.07, 0.0, thick / 2.0))
    tb.collision_box("llave", (0.245, 0.06, head_thick), (-0.003, 0.002, head_thick / 2.0), root)
    tb.paint({wrench: None}, samples=10, ao=0.35, ao_distance=0.025, seed=821)
    return root


def build_pliers() -> bpy.types.Object:
    """Alicates universales, tumbados y entreabiertos: mangos con la goma roja
    cuarteada y las bocas estriadas hacia +X."""
    root = tb.empty("alicates-fisico")
    mb = tb.MeshBuilder(seed=831)
    pivot = Vector((0.032, 0.0, 0.0))
    layer = 0.0058
    for side in (-1.0, 1.0):
        z = layer / 2.0
        spread = math.radians(side * 13.0)
        turn = Matrix.Rotation(spread, 3, "Z")

        def at(x: float, y: float) -> tuple[float, float]:
            p = pivot + turn @ (Vector((x, y, 0.0)) - pivot)
            return (p.x, p.y)

        # El mango: de la articulación hacia -X, curvado hacia fuera.
        handle = [at(0.024, side * 0.002), at(0.024, side * 0.009), at(-0.02, side * 0.017), at(-0.095, side * 0.019), at(-0.098, side * 0.012), at(-0.02, side * 0.006), at(0.0, side * 0.001)]
        if side < 0:
            handle = list(reversed(handle))
        mb.prism(handle, layer, (0.0, 0.0, z), STEEL, bevel=0.0012)
        # La boca: de la articulación hacia +X, afilándose.
        jaw = [at(0.024, 0.0), at(0.09, 0.0), at(0.09, side * 0.0035), at(0.05, side * 0.008), at(0.024, side * 0.012)]
        if side < 0:
            jaw = list(reversed(jaw))
        mb.prism(jaw, layer, (0.0, 0.0, z), STEEL_LIGHT, bevel=0.0012)
        for k in range(6):
            x, y = at(0.06 + k * 0.004, side * 0.0012)
            mb.box((0.0012, 0.0016, layer * 0.8), (x, y, z), STEEL_DARK, rotation=(0.0, 0.0, math.degrees(spread)))
        # La goma del mango, un poco más gruesa, con grietas.
        grip = [at(-0.006, side * 0.004), at(-0.006, side * 0.0115), at(-0.035, side * 0.0198), at(-0.098, side * 0.0215), at(-0.1, side * 0.0105), at(-0.035, side * 0.004)]
        if side < 0:
            grip = list(reversed(grip))
        mb.prism(grip, layer + 0.003, (0.0, 0.0, z), RUBBER_RED, bevel=0.0018, segments=2)
        for k in range(3):
            x, y = at(-0.05 - k * 0.017, side * 0.016)
            mb.box((0.0008, 0.006, 0.0008), (x, y, z + layer / 2.0 + 0.0015), RUBBER_RED_DARK, rotation=(0.0, 0.0, 70.0 + k * 20.0))
    mb.cylinder(0.0062, layer + 0.002, (pivot.x, pivot.y, layer / 2.0), STEEL_DARK, segments=14)
    mb.cylinder(0.0035, layer + 0.0028, (pivot.x, pivot.y, layer / 2.0), STEEL, segments=10)
    pliers = mb.finish("alicates", tb.material("metal", STEEL), root)
    _rust_and_dirt(pliers, 832, rust=0.15, dirt=0.3)
    bb.grip(root, (-0.05, 0.0, layer / 2.0))
    tb.collision_box("alicates", (0.2, 0.07, layer + 0.003), (-0.004, 0.0, (layer + 0.003) / 2.0), root)
    tb.paint({pliers: None}, samples=10, ao=0.35, ao_distance=0.02, seed=831)
    return root


# --------------------------------------------------------------------------
# Electricidad
# --------------------------------------------------------------------------


def build_flat_battery() -> bpy.types.Object:
    """Pila de petaca de 4,5 V (la de la linterna): papel azul con la banda amarilla
    y el rayo, la tapa de brea y las dos láminas de latón dobladas encima, verdes
    de sulfato en la base. El papel, rasgado en una esquina."""
    root = tb.empty("pila_petaca-fisico")
    w, d, h = 0.062, 0.022, 0.067
    mb = tb.MeshBuilder(seed=841)
    mb.box((w, d, h - 0.004), (0.0, 0.0, (h - 0.004) / 2.0), BATTERY_BLUE, bevel=0.0015, cuts=3)
    mb.box((w - 0.002, d - 0.002, 0.005), (0.0, 0.0, h - 0.0035), PITCH, bevel=0.0012)
    lift = 0.0004
    for side in (-1.0, 1.0):
        mb.box((w + 0.0002, lift, 0.013), (0.0, side * (d / 2.0 + lift / 2.0), 0.049), BATTERY_YELLOW)
        mb.box((lift, d + 0.0002, 0.013), (side * (w / 2.0 + lift / 2.0), 0.0, 0.049), BATTERY_YELLOW)
    bolt = [(-0.004, 0.034), (0.006, 0.034), (0.0015, 0.024), (0.008, 0.024), (-0.006, 0.006), (-0.0015, 0.019), (-0.008, 0.019)]
    mb.prism([(x - 0.012, y) for x, y in reversed(bolt)], 0.0006, (0.0, -d / 2.0 - 0.0006, 0.0), "#E6E0CC", rotation=(90.0, 0.0, 0.0))
    for k in range(3):
        mb.box((0.018 - k * 0.004, 0.0006, 0.0018), (0.018, -d / 2.0 - 0.0006, 0.03 - k * 0.0055), "#E6E0CC")
    # La esquina rasgada: asoma el cinc de las celdas.
    mb.box((0.012, 0.0008, 0.016), (-w / 2.0 + 0.007, -d / 2.0 - 0.0002, 0.009), ZINC)
    body = mb.finish("pila", tb.material("carton", BATTERY_BLUE), root)
    tb.stain(body, DIRT, amount=0.45, scale=50.0, coverage=0.25, seed=842)
    tb.stain(body, "#A89A72", amount=0.4, scale=70.0, coverage=0.2, seed=843)

    tabs = tb.MeshBuilder(seed=844)
    for x, length in ((-0.016, 0.034), (0.016, 0.017)):
        tabs.box((0.0065, 0.0007, 0.008), (x, 0.0, h + 0.004), BRASS, bevel=0.0002)
        tabs.box((0.0065, length, 0.0007), (x, length / 2.0 - 0.0004, h + 0.0081), BRASS, rotation=(4.0, 0.0, 0.0), bevel=0.0002)
        for k in range(4):
            tabs.sphere(0.0014, (x + (k - 1.5) * 0.002, (k % 2 - 0.5) * 0.002, h + 0.0005), CORROSION, segments=6)
    tab_obj = tabs.finish("laminas", tb.material("metal", BRASS), root)
    tb.stain(tab_obj, VERDIGRIS, amount=0.6, scale=150.0, coverage=0.3, seed=845)
    tb.collision_box("pila", (w, d + 0.016, h + 0.01), (0.0, 0.006, (h + 0.01) / 2.0), root)
    tb.paint({body: None, tab_obj: None}, samples=10, ao=0.35, ao_distance=0.02, seed=841)
    return root


def _tube(mb: tb.MeshBuilder, base: Vector, rotation: tuple[float, float, float]) -> list:
    """Una válvula de radio miniatura: la ampolla de vidrio con la punta de vaciado y
    las patillas abajo."""
    faces = mb.lathe(
        [(0.0, 0.0), (0.0094, 0.0), (0.0105, 0.0018), (0.0105, 0.012), (0.0105, 0.0125), (0.0105, 0.03), (0.0105, 0.039), (0.0105, 0.0395), (0.0105, 0.045), (0.009, 0.05), (0.005, 0.0525), (0.0016, 0.053), (0.0012, 0.0558), (0.0, 0.0565)],
        base, GLASS, rotation=rotation, segments=20, sharp_angle=60.0,
    )
    turn = Matrix.Identity(3)
    for axis, angle in zip("XYZ", rotation):
        turn = Matrix.Rotation(math.radians(angle), 3, axis) @ turn
    for k in range(9):
        a = 2.0 * math.pi * k / 10.0
        start = Vector((0.0068 * math.cos(a), 0.0068 * math.sin(a), 0.0))
        mb.bar(base + turn @ start, base + turn @ (start + Vector((0.0, 0.0, -0.006))), 0.0005, STEEL_LIGHT, 5)
    return faces


def build_radio_tubes() -> bpy.types.Object:
    """Válvulas de radio: una en su cajita de cartón, otra de pie sobre sus patillas
    y otra tumbada. El espejo plateado del getter arriba y las placas oscuras
    dentro del vidrio."""
    root = tb.empty("valvulas-fisico")
    glass = tb.MeshBuilder(seed=851)
    standing = Vector((0.016, 0.012, 0.006))
    _tube(glass, standing, (0.0, 0.0, 0.0))
    lying = Vector((-0.004, -0.032, 0.0106))
    _tube(glass, lying, (0.0, 90.0, 0.0))
    boxed = Vector((-0.024, 0.006, 0.016))
    _tube(glass, boxed, (0.0, 0.0, 0.0))
    tubes = glass.finish("valvulas", tb.material("vidrio", GLASS), root)
    bases = [(standing, (0.0, 0.0, 1.0)), (lying, (1.0, 0.0, 0.0)), (boxed, (0.0, 0.0, 1.0))]

    def inside(co: Vector) -> str | None:
        for base, axis in bases:
            along = (co - base).dot(Vector(axis))
            radial = ((co - base) - Vector(axis) * along).length
            if radial > 0.012 or along < -0.002 or along > 0.058:
                continue
            if along > 0.0395:
                return GETTER
            if along > 0.0125:
                return ANODE
            return None
        return None

    bb.recolor(tubes, inside)

    box = tb.MeshBuilder(seed=852)
    size, height, t = 0.026, 0.05, 0.0012
    center = Vector((boxed.x, boxed.y, 0.0))
    box.box((size, size, t), center + Vector((0.0, 0.0, t / 2.0)), TUBE_BOX)
    for side in (-1.0, 1.0):
        box.box((size, t, height), center + Vector((0.0, side * (size / 2.0 - t / 2.0), height / 2.0)), TUBE_BOX, bevel=0.0004)
        box.box((t, size - 2.0 * t, height), center + Vector((side * (size / 2.0 - t / 2.0), 0.0, height / 2.0)), TUBE_BOX, bevel=0.0004)
    box.box((size - 0.0004, t, 0.018), center + Vector((0.0, -size / 2.0 - 0.0045, height + 0.0075)), TUBE_BOX_DARK, rotation=(-28.0, 0.0, 0.0), bevel=0.0004)
    box.box((size + 0.0003, 0.0004, 0.008), center + Vector((0.0, -size / 2.0 - 0.0002, 0.03)), "#E2DACA")
    box.box((0.016, 0.0005, 0.0018), center + Vector((0.0, -size / 2.0 - 0.0005, 0.03)), INK)
    box.box((0.0003, size - 0.004, height - 0.004), center + Vector((size / 2.0 + 0.0002, 0.0, height / 2.0)), "#E2DACA")
    carton = box.finish("caja", tb.material("carton", TUBE_BOX), root)
    tb.stain(carton, DIRT, amount=0.5, scale=60.0, coverage=0.3, seed=853)
    tb.collision_box("valvulas", (0.07, 0.07, 0.066), (-0.002, -0.006, 0.033), root)
    tb.paint({tubes: None, carton: None}, samples=10, ao=0.3, ao_distance=0.02, seed=851)
    return root


def build_car_battery() -> bpy.types.Object:
    """La batería de un coche del atasco: caja de ebonita con los nervios de las seis
    celdas, la tapa de brea, los tapones y los puentes de plomo, y los bornes con
    costras blancas de sulfato. Pesa como un muerto."""
    rng = random.Random(861)
    root = tb.empty("bateria_coche-fisico")
    w, d, h = 0.24, 0.172, 0.19
    mb = tb.MeshBuilder(seed=861)
    mb.box((w, d, h - 0.012), (0.0, 0.0, (h - 0.012) / 2.0), EBONITE, bevel=0.006, segments=2, cuts=4)
    cell = w / 6.0
    for k in range(1, 6):
        x = -w / 2.0 + cell * k
        for side in (-1.0, 1.0):
            mb.box((0.006, 0.006, h - 0.03), (x, side * (d / 2.0 + 0.002), (h - 0.03) / 2.0 + 0.004), EBONITE, bevel=0.002)
    mb.box((w + 0.006, d + 0.006, 0.012), (0.0, 0.0, 0.006), EBONITE, bevel=0.003)
    # La tapa: brea entre los bordes de cada celda.
    mb.box((w - 0.008, d - 0.008, 0.012), (0.0, 0.0, h - 0.009), MASTIC, bevel=0.002)
    for k in range(6):
        x = -w / 2.0 + cell * (k + 0.5)
        mb.box((cell - 0.006, d - 0.02, 0.006), (x, 0.0, h - 0.004), "#1C1B1A", bevel=0.002)
    case = mb.finish("caja", tb.material("plastico", EBONITE), root)
    tb.stain(case, "#4A4640", amount=0.6, scale=20.0, coverage=0.35, seed=862)
    tb.stain(case, DIRT, amount=0.5, scale=35.0, coverage=0.3, seed=863)

    lead = tb.MeshBuilder(seed=864)
    top = h - 0.001
    for k in range(6):
        x = -w / 2.0 + cell * (k + 0.5)
        lead.lathe([(0.0, 0.0), (0.011, 0.0), (0.011, 0.006), (0.0095, 0.009), (0.0, 0.009)], (x, 0.0, top), CAP, segments=14)
        for j in range(6):
            a = math.radians(j * 60.0)
            lead.box((0.0025, 0.0045, 0.008), (x + 0.0105 * math.cos(a), 0.0105 * math.sin(a), top + 0.004), CAP, rotation=(0.0, 0.0, math.degrees(a)))
        # Puentes de plomo entre celdas, delante y detrás, alternando.
        if k < 5:
            y = (d / 2.0 - 0.03) * (1.0 if k % 2 == 0 else -1.0)
            lead.box((cell + 0.012, 0.012, 0.007), (x + cell / 2.0, y, top + 0.0035), LEAD, bevel=0.002)
    for x, radius in ((-w / 2.0 + cell * 0.5, 0.0095), (w / 2.0 - cell * 0.5, 0.0085)):
        y = -(d / 2.0 - 0.03) if x < 0.0 else (d / 2.0 - 0.03) * (-1.0)
        lead.lathe([(0.0, 0.0), (radius + 0.003, 0.0), (radius + 0.002, 0.004), (radius, 0.006), (radius * 0.86, 0.022), (radius * 0.7, 0.024), (0.0, 0.0245)], (x, y, top), LEAD, segments=14)
        for j in range(7):
            a = rng.uniform(0.0, 2.0 * math.pi)
            lead.sphere(rng.uniform(0.0025, 0.0045), (x + (radius + 0.004) * math.cos(a), y + (radius + 0.004) * math.sin(a), top + 0.002), CORROSION, segments=6)
    leads = lead.finish("plomo", tb.material("metal", LEAD), root)
    tb.stain(leads, "#4E4E4C", amount=0.5, scale=60.0, coverage=0.4, seed=865)
    tb.collision_box("bateria", (w + 0.008, d + 0.012, h + 0.024), (0.0, 0.0, (h + 0.024) / 2.0), root)
    tb.paint({case: None, leads: None}, samples=14, ao=0.4, ao_distance=0.06, seed=861)
    return root


# --------------------------------------------------------------------------
# Luz y fuego
# --------------------------------------------------------------------------


def build_kerosene_lamp() -> bpy.types.Object:
    """Quinqué: el depósito de hojalata esmaltada en verde, el mechero de latón con
    su ruedecilla y el tubo de vidrio, tiznado por arriba. ``foco`` marca dónde va
    la llama (y su luz)."""
    root = tb.empty("quinque-fisico")
    tank = tb.MeshBuilder(seed=871)
    tank.lathe([(0.0, 0.0), (0.056, 0.0), (0.059, 0.003), (0.055, 0.008), (0.042, 0.012), (0.04, 0.016), (0.05, 0.022), (0.062, 0.032), (0.065, 0.045), (0.06, 0.058), (0.044, 0.067), (0.026, 0.071), (0.0, 0.072)], (0.0, 0.0, 0.0), LAMP_GREEN, segments=28, sharp_angle=45.0)
    tank.lathe([(0.0655, 0.042), (0.067, 0.045), (0.0655, 0.048)], (0.0, 0.0, 0.0), LAMP_GREEN_DARK, segments=28)
    # Un asa de dedo en el costado del depósito.
    tank.tube(tb.smooth_path(((0.058, 0.0, 0.056), (0.078, 0.0, 0.058), (0.086, 0.0, 0.046), (0.078, 0.0, 0.034), (0.061, 0.0, 0.036)), 4), 0.0028, LAMP_GREEN_DARK, segments=6)
    body = tank.finish("deposito", tb.material("metal", LAMP_GREEN), root)
    tb.stain(body, RUST, amount=0.7, scale=60.0, coverage=0.22, seed=872)
    tb.stain(body, "#6A7A64", amount=0.45, scale=35.0, coverage=0.3, seed=873)

    burner = tb.MeshBuilder(seed=874)
    burner.lathe([(0.022, 0.07), (0.024, 0.074), (0.024, 0.084), (0.021, 0.087), (0.026, 0.09), (0.032, 0.091), (0.033, 0.095), (0.031, 0.096), (0.016, 0.097), (0.0, 0.097)], (0.0, 0.0, 0.0), BRASS, segments=24, sharp_angle=45.0)
    for k in range(8):
        a = math.radians(22.5 + k * 45.0)
        burner.box((0.006, 0.0014, 0.012), (0.0315 * math.sin(a), -0.0315 * math.cos(a), 0.1), BRASS, rotation=(0.0, 0.0, math.degrees(a)), bevel=0.0004)
    # La ruedecilla de la mecha, por delante.
    burner.bar((0.0, -0.022, 0.08), (0.0, -0.034, 0.08), 0.0016, BRASS_DARK, 6)
    burner.cylinder(0.0075, 0.0028, (0.0, -0.035, 0.08), BRASS, rotation=(90.0, 0.0, 0.0), segments=14)
    for k in range(10):
        a = 2.0 * math.pi * k / 10.0
        burner.box((0.0012, 0.003, 0.0012), (0.0076 * math.cos(a), -0.035, 0.08 + 0.0076 * math.sin(a)), BRASS_DARK, rotation=(0.0, -math.degrees(a), 0.0))
    brass = burner.finish("mechero", tb.material("metal", BRASS), root)
    tb.stain(brass, BRASS_DARK, amount=0.6, scale=60.0, coverage=0.35, seed=875)

    chimney = tb.MeshBuilder(seed=876)
    chimney.lathe([(0.0285, 0.096), (0.031, 0.1), (0.036, 0.11), (0.0405, 0.125), (0.0412, 0.138), (0.037, 0.155), (0.029, 0.172), (0.0225, 0.188), (0.0212, 0.205), (0.0212, 0.24), (0.0212, 0.262), (0.0218, 0.268), (0.0198, 0.27), (0.0192, 0.262)], (0.0, 0.0, 0.0), CHIMNEY, segments=24, sharp_angle=60.0)
    glass = chimney.finish("tubo", tb.material("vidrio", CHIMNEY), root)
    bb.recolor(glass, lambda co: "#3A3632" if co.z > 0.23 else ("#8C8A80" if co.z > 0.2 else None))
    tb.stain(glass, SOOT, amount=0.55, scale=40.0, coverage=0.35, seed=877, stretch_z=0.4)
    focus = tb.empty("foco", root)
    focus.location = (0.0, 0.0, 0.112)
    tb.collision_box("quinque", (0.13, 0.13, 0.27), (0.008, 0.0, 0.135), root)
    tb.paint({body: None, brass: None, glass: None}, samples=12, ao=0.35, ao_distance=0.05, seed=871)
    return root


def build_kerosene_stove() -> bpy.types.Object:
    """Hornillo de queroseno: el depósito de latón como una calabaza aplastada, la
    bomba en el costado, el tubo y el quemador con su sombrerete, y las tres patas
    que suben y hacen de parrilla. Latón ennegrecido y hollín."""
    root = tb.empty("hornillo-fisico")
    mb = tb.MeshBuilder(seed=881)
    mb.lathe([(0.0, 0.002), (0.05, 0.002), (0.056, 0.0), (0.06, 0.004), (0.072, 0.016), (0.08, 0.034), (0.082, 0.05), (0.077, 0.068), (0.062, 0.084), (0.036, 0.094), (0.0, 0.097)], (0.0, 0.0, 0.0), STOVE_BRASS, segments=32, sharp_angle=50.0)
    # Tapón de llenar, tornillo de purga y la bomba con su pomo.
    mb.lathe([(0.0, 0.0), (0.011, 0.0), (0.011, 0.007), (0.009, 0.009), (0.0, 0.009)], (0.032, 0.028, 0.086), STOVE_BRASS, segments=12)
    mb.cylinder(0.004, 0.012, (-0.03, 0.03, 0.092), STOVE_BRASS, segments=8)
    mb.bar((-0.036, 0.03, 0.099), (-0.024, 0.03, 0.099), 0.0018, STOVE_BRASS, 6)
    mb.cylinder(0.0075, 0.05, (0.095, -0.012, 0.05), STOVE_BRASS, rotation=(0.0, 90.0, 0.0), segments=12)
    mb.bar((0.12, -0.012, 0.05), (0.128, -0.012, 0.05), 0.002, STEEL, 6)
    mb.sphere(0.0085, (0.133, -0.012, 0.05), "#5A3A26", segments=10)
    # El tubo, la copa de precalentar y el quemador.
    mb.cylinder(0.0062, 0.06, (0.0, 0.0, 0.12), STOVE_BRASS, segments=12)
    mb.lathe([(0.0062, 0.112), (0.02, 0.114), (0.021, 0.12), (0.018, 0.12), (0.0062, 0.117)], (0.0, 0.0, 0.0), STOVE_BRASS, segments=16)
    mb.lathe([(0.006, 0.148), (0.022, 0.152), (0.026, 0.161), (0.0245, 0.164), (0.017, 0.16), (0.0, 0.158)], (0.0, 0.0, 0.0), STOVE_BRASS, segments=20)
    for k in range(12):
        a = math.radians(k * 30.0)
        bb.disc(mb, (0.021 * math.sin(a), -0.021 * math.cos(a), 0.1612), (0.0, 0.0, 1.0), 0.0012, SOOT, thickness=0.0004, segments=6)
    mb.cylinder(0.0018, 0.008, (0.0, 0.0, 0.163), STEEL_DARK, segments=6)
    mb.lathe([(0.0, 0.166), (0.02, 0.1665), (0.019, 0.169), (0.0, 0.17)], (0.0, 0.0, 0.0), STEEL_DARK, segments=16)
    brass = mb.finish("hornillo", tb.material("metal", STOVE_BRASS), root)

    legs = tb.MeshBuilder(seed=882)
    ring_z = 0.166
    ring = [Vector((0.068 * math.cos(2.0 * math.pi * k / 24.0), 0.068 * math.sin(2.0 * math.pi * k / 24.0), ring_z)) for k in range(25)]
    legs.tube(ring, 0.0028, STEEL_DARK, segments=6, caps=False)
    for k in range(3):
        a = math.radians(30.0 + k * 120.0)
        out = Vector((math.sin(a), -math.cos(a), 0.0))
        turn = math.degrees(a)
        # El montante: una pletina atornillada al costado del depósito que sube al aro.
        foot = out * 0.081 + Vector((0.0, 0.0, 0.05))
        head = out * 0.07 + Vector((0.0, 0.0, ring_z))
        span = head - foot
        tilt = math.degrees(math.atan2(span.dot(out), span.z))
        legs.box((0.012, 0.0035, span.length), (foot + head) / 2.0, STEEL_DARK, rotation=(tilt, 0.0, turn), bevel=0.0012)
        legs.cylinder(0.004, 0.006, out * 0.083 + Vector((0.0, 0.0, 0.056)), STEEL, rotation=(90.0, 0.0, turn), segments=8)
        # El brazo de la parrilla, hacia dentro, con dientes.
        arm_start, arm_end = out * 0.072 + Vector((0.0, 0.0, ring_z + 0.002)), out * 0.03 + Vector((0.0, 0.0, ring_z + 0.004))
        legs.box((0.0045, (arm_end - arm_start).length, 0.006), (arm_start + arm_end) / 2.0, STEEL_DARK, rotation=(0.0, 0.0, turn), bevel=0.0012)
        for j in range(3):
            legs.box((0.005, 0.0025, 0.004), out * (0.04 + j * 0.01) + Vector((0.0, 0.0, ring_z + 0.008)), STEEL_DARK, rotation=(0.0, 0.0, turn))
    leg_obj = legs.finish("patas", tb.material("metal", STEEL_DARK), root)
    tb.stain(brass, TARNISH, amount=0.7, scale=30.0, coverage=0.5, seed=883)
    tb.stain(brass, VERDIGRIS, amount=0.45, scale=70.0, coverage=0.12, seed=884)
    tb.scorch(brass, [((0.0, 0.0, 0.11), 0.06, 0.07)], strength=0.7)
    tb.stain(leg_obj, RUST, amount=0.7, scale=50.0, coverage=0.3, seed=885)
    tb.dent(brass, (-0.06, -0.05, 0.07), radius=0.02, depth=0.003)
    tb.collision_box("hornillo", (0.2, 0.18, 0.175), (0.022, 0.0, 0.0875), root)
    tb.paint({brass: None, leg_obj: None}, samples=14, ao=0.4, ao_distance=0.05, seed=881)
    return root


def models() -> dict:
    return {
        "cinta_aislante": build_tape,
        "clavos": build_nails,
        "llave_inglesa": build_wrench,
        "alicates": build_pliers,
        "pila_petaca": build_flat_battery,
        "valvulas": build_radio_tubes,
        "bateria_coche": build_car_battery,
        "quinque": build_kerosene_lamp,
        "hornillo": build_kerosene_stove,
    }
