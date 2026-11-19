"""El botín de valor: lo que se paga bien en la estación, de lo raro a lo muy raro.

- Relojes: el de pulsera (para el relojero) y el de bolsillo, con la tapa abierta.
  Sus agujas son nodos propios (``aguja_horas``, ``aguja_minutos``) con el origen
  en el centro de la esfera; en reposo marcan las doce y aquí, las diez y diez.
- La cámara de fotos de telémetro y el microscopio de un laboratorio.
- La medalla en su estuche (la ``tapa`` gira sobre su bisagra), el samovar de latón
  de alguna casa de madera y un icono con su cubierta de metal, de la iglesia vieja.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Todo
descansa sobre z = 0 y enseña su frente hacia -Y; lo que está tumbado boca arriba
(las esferas, el icono) tiene las doce hacia +Y. Las reglas del botín (nada está
intacto) están en tools/blender/botin_bpy.py.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Matrix, Vector

import botin_bpy as bb
import tumansk_bpy as tb

INK = "#1B1A22"
DIRT = "#4E4233"
CHROME = "#B8BCB8"
CHROME_DARK = "#7A7E7A"
DIAL = "#E2DAC4"
HANDS = "#1E2430"
LEATHER = "#5A3A24"
LEATHER_DARK = "#3E2818"
CRACK = "#F0EEE4"
LEATHERETTE = "#2A2826"
LENS_GLASS = "#1E2228"
CASE_RED = "#5E2226"
CASE_RED_DARK = "#3E1418"
VELVET = "#2E1A22"
SATIN = "#D8CFC0"
RIBBON_GREY = "#7A7A78"
RIBBON_RED = "#8A2A2A"
RIBBON_YELLOW = "#B8962E"
GOLD = "#C8A050"
GOLD_DARK = "#8A6A2A"
BRASS = "#8E6C38"
TARNISH = "#56401F"
PATINA = "#5E7A5E"
WOOD_BLACK = "#2A2420"
ENAMEL_BLACK = "#1E1E22"
MIRROR = "#C8CCC8"
ICON_WOOD = "#5A4028"
OKLAD = "#A89A70"
OKLAD_DARK = "#6E6244"
ICON_GROUND = "#3A2418"
ICON_ROBE = "#5A1E16"
ICON_MANTLE = "#2E3A4A"
ICON_FACE = "#B08A58"
SILVER = "#B8B4A8"
SILVER_DARK = "#7E7A70"


def _hand(name: str, root: bpy.types.Object, center: Vector, length: float, width: float, angle: float, seed: int) -> bpy.types.Object:
    """Una aguja con el origen en el eje, apuntando a las doce (+Y) y girada ``angle``
    grados en el sentido del reloj."""
    mb = tb.MeshBuilder(seed=seed)
    mb.prism([(-width / 2.0, -length * 0.18), (width / 2.0, -length * 0.18), (width * 0.35, length * 0.82), (0.0, length), (-width * 0.35, length * 0.82)], 0.0004, center, HANDS)
    mb.cylinder(width * 0.9, 0.0008, center + Vector((0.0, 0.0, 0.0003)), HANDS, segments=10)
    hand = mb.finish(name, tb.material("metal", HANDS), root)
    tb.set_origin(hand, center)
    hand.rotation_euler = (0.0, 0.0, math.radians(-angle))
    return hand


def _dial_marks(mb: tb.MeshBuilder, center: Vector, radius: float, z: float, long: float, short: float, color: str = INK) -> None:
    for k in range(60):
        if k % 5:
            if radius < 0.015:
                continue
            size = (0.0004, short * 0.6, 0.0003)
        else:
            size = (0.0012 if k % 15 == 0 else 0.0008, long if k % 15 == 0 else short, 0.0003)
        a = math.radians(k * 6.0)
        distance = radius - size[1] / 2.0
        mb.box(size, center + Vector((distance * math.sin(a), distance * math.cos(a), z)), color, rotation=(0.0, 0.0, -k * 6.0))


# --------------------------------------------------------------------------
# Relojes
# --------------------------------------------------------------------------


def build_wristwatch() -> bpy.types.Object:
    """Reloj de pulsera de cuerda: caja cromada, esfera crema con sus marcas y la
    correa de cuero cuarteada con la hebilla. El cristal, rajado."""
    root = tb.empty("reloj_pulsera-fisico")
    lift = 0.0023
    r = 0.0175
    mb = tb.MeshBuilder(seed=1001)
    mb.lathe([(0.0, 0.0), (0.0155, 0.0), (r, 0.0022), (r + 0.0006, 0.0055), (r - 0.0004, 0.0084), (0.0152, 0.0088), (0.0148, 0.0072), (0.0, 0.0072)], (0.0, 0.0, lift), CHROME, segments=32, sharp_angle=35.0)
    mb.cylinder(0.0022, 0.004, (r + 0.0022, 0.0, lift + 0.0045), CHROME, rotation=(0.0, 90.0, 0.0), segments=10)
    for k in range(8):
        a = 2.0 * math.pi * k / 8.0
        mb.box((0.004, 0.0006, 0.0006), (r + 0.0022, 0.0022 * math.cos(a), lift + 0.0045 + 0.0022 * math.sin(a)), CHROME_DARK)
    for side in (-1.0, 1.0):
        for x in (-0.0082, 0.0082):
            mb.box((0.0028, 0.008, 0.0042), (x, side * (r + 0.0012), lift + 0.0035), CHROME, bevel=0.0009)
        mb.bar((-0.0082, side * (r + 0.004), lift + 0.0034), (0.0082, side * (r + 0.004), lift + 0.0034), 0.0008, CHROME_DARK, 6)
    case = mb.finish("caja", tb.material("metal", CHROME), root)
    tb.stain(case, CHROME_DARK, amount=0.5, scale=90.0, coverage=0.3, seed=1002)

    face = tb.MeshBuilder(seed=1003)
    dial_z = lift + 0.0076
    center = Vector((0.0, 0.0, dial_z))
    face.cylinder(0.0147, 0.0008, (0.0, 0.0, dial_z - 0.0004), DIAL, segments=32)
    _dial_marks(face, center, 0.0136, 0.0002, 0.0032, 0.0018)
    face.lathe([(0.0042, 0.0), (0.005, 0.0), (0.005, 0.0002), (0.0042, 0.0002), (0.0042, 0.0)], center + Vector((0.0, -0.0072, 0.0)), INK, segments=16)
    # La raja del cristal: dos líneas claras que cruzan la esfera.
    face.box((0.024, 0.0005, 0.0003), center + Vector((0.002, 0.003, 0.0012)), CRACK, rotation=(0.0, 0.0, 28.0))
    face.box((0.011, 0.0005, 0.0003), center + Vector((-0.004, -0.002, 0.0012)), CRACK, rotation=(0.0, 0.0, -40.0))
    dial = face.finish("esfera", tb.material("esmalte", DIAL), root)
    tb.stain(dial, "#B8A880", amount=0.45, scale=200.0, coverage=0.3, seed=1004)
    hours = _hand("aguja_horas", root, center + Vector((0.0, 0.0, 0.0006)), 0.0085, 0.0018, -60.0, 1005)
    minutes = _hand("aguja_minutos", root, center + Vector((0.0, 0.0, 0.0011)), 0.0125, 0.0013, 60.0, 1006)

    strap = tb.MeshBuilder(seed=1007)
    path = tb.smooth_path(((0.003, -0.108, 0.0011), (0.0, -0.066, 0.0012), (0.0, -0.026, 0.0012), (0.0, 0.0, 0.001), (0.0, 0.026, 0.0012), (-0.001, 0.07, 0.0012), (0.004, 0.128, 0.0011)), 4)
    bb.strap(strap, path, 0.016, 0.0022, LEATHER, center=(0.0, 0.0, -1.0))
    for k in range(5):
        strap.lathe([(0.0, 0.0), (0.0012, 0.0), (0.0, 0.0002)], (0.0, 0.078 + k * 0.01, 0.0023), INK, segments=6)
    buckle = -0.112
    for x in (-0.0105, 0.0105):
        strap.bar((x, buckle - 0.008, 0.0022), (x, buckle + 0.008, 0.0022), 0.0011, CHROME, 6)
    for y in (-0.008, 0.008):
        strap.bar((-0.0105, buckle + y, 0.0022), (0.0105, buckle + y, 0.0022), 0.0011, CHROME, 6)
    strap.bar((0.0, buckle + 0.007, 0.0026), (0.0008, buckle - 0.011, 0.0031), 0.0008, CHROME, 6)
    strap.box((0.019, 0.005, 0.0032), (0.0, -0.092, 0.0018), LEATHER_DARK, bevel=0.0006)
    leather = strap.finish("correa", tb.material("cuero", LEATHER), root)
    tb.stain(leather, LEATHER_DARK, amount=0.6, scale=40.0, coverage=0.4, seed=1008)
    tb.stain(leather, "#8A6A4A", amount=0.45, scale=110.0, coverage=0.2, seed=1009)
    tb.collision_box("reloj", (0.04, 0.245, 0.012), (0.0, 0.01, 0.006), root)
    tb.paint({case: None, dial: None, hours: None, minutes: None, leather: None}, samples=10, ao=0.35, ao_distance=0.02, seed=1001)
    return root


def build_pocket_watch() -> bpy.types.Object:
    """Reloj de bolsillo de plata, boca arriba y con la tapa abierta hacia la
    izquierda: la esfera de esmalte con los segundos abajo, el remontoir con su
    anilla y la cadena enroscada en la mesa. El cristal se perdió."""
    rng = random.Random(1011)
    root = tb.empty("reloj_bolsillo-fisico")
    r, t = 0.0245, 0.0115
    mb = tb.MeshBuilder(seed=1011)
    mb.lathe([(0.0, 0.0), (0.019, 0.0), (0.0235, 0.0018), (r, 0.0045), (r, 0.0075), (0.0238, 0.0098), (0.0222, t), (0.0212, t - 0.0006), (0.0205, t - 0.0025), (0.0, t - 0.0025)], (0.0, 0.0, 0.0), SILVER, segments=36, sharp_angle=40.0)
    # El remontoir y la anilla, a las doce.
    mb.cylinder(0.0036, 0.004, (0.0, r + 0.0018, t * 0.55), SILVER, rotation=(90.0, 0.0, 0.0), segments=12)
    mb.cylinder(0.0052, 0.005, (0.0, r + 0.0055, t * 0.55), SILVER, rotation=(90.0, 0.0, 0.0), segments=14)
    for k in range(12):
        a = 2.0 * math.pi * k / 12.0
        mb.box((0.0008, 0.0046, 0.0008), (0.0052 * math.cos(a), r + 0.0055, t * 0.55 + 0.0052 * math.sin(a)), SILVER_DARK)
    ring = [Vector((0.009 * math.cos(2.0 * math.pi * k / 24.0), r + 0.016 + 0.009 * math.sin(2.0 * math.pi * k / 24.0), t * 0.55)) for k in range(25)]
    mb.tube(ring, 0.0013, SILVER, segments=6, caps=False)
    # La bisagra, a las nueve.
    mb.cylinder(0.0022, 0.012, (-r - 0.0006, 0.0, t * 0.62), SILVER, rotation=(90.0, 0.0, 0.0), segments=10)
    case = mb.finish("caja", tb.material("metal", SILVER), root)
    tb.stain(case, SILVER_DARK, amount=0.6, scale=70.0, coverage=0.35, seed=1012)

    face = tb.MeshBuilder(seed=1013)
    dial_z = t - 0.0025
    center = Vector((0.0, 0.0, dial_z))
    face.cylinder(0.0207, 0.0008, (0.0, 0.0, dial_z + 0.0002), DIAL, segments=36)
    _dial_marks(face, center + Vector((0.0, 0.0, 0.0006)), 0.0195, 0.0, 0.0034, 0.0016)
    seconds = center + Vector((0.0, -0.0098, 0.0007))
    face.lathe([(0.0042, 0.0), (0.0048, 0.0), (0.0048, 0.0002), (0.0042, 0.0002), (0.0042, 0.0)], seconds, INK, segments=16)
    face.box((0.0004, 0.0036, 0.0003), seconds + Vector((0.0008, 0.0012, 0.0003)), HANDS, rotation=(0.0, 0.0, -25.0))
    dial = face.finish("esfera", tb.material("esmalte", DIAL), root)
    tb.stain(dial, "#C8B890", amount=0.4, scale=200.0, coverage=0.25, seed=1014)
    hours = _hand("aguja_horas", root, center + Vector((0.0, 0.0, 0.0012)), 0.011, 0.0022, -58.0, 1015)
    minutes = _hand("aguja_minutos", root, center + Vector((0.0, 0.0, 0.0017)), 0.0165, 0.0016, 62.0, 1016)

    # La tapa: un casquete de plata, abierta 125° sobre la bisagra de las nueve.
    lid = tb.MeshBuilder(seed=1017)
    hinge = Vector((-r - 0.0006, 0.0, t * 0.62))
    lid_base = Vector((0.0, 0.0, t * 0.62))
    lid.lathe([(0.0, 0.0032), (0.012, 0.0028), (0.0215, 0.0012), (r - 0.0008, -0.0006), (r, 0.0), (0.02, 0.0028), (0.012, 0.0042), (0.0, 0.0045)], lid_base, SILVER, segments=36, sharp_angle=40.0)
    lid_obj = lid.finish("tapa", tb.material("metal", SILVER), root)
    tb.stain(lid_obj, SILVER_DARK, amount=0.6, scale=70.0, coverage=0.4, seed=1018)
    tb.set_origin(lid_obj, hinge)
    lid_obj.rotation_euler = (0.0, math.radians(-125.0), 0.0)

    chain = tb.MeshBuilder(seed=1019)
    path = tb.smooth_path(((0.0, r + 0.024, t * 0.55), (0.008, r + 0.04, 0.003), (0.03, r + 0.05, 0.0018), (0.055, r + 0.035, 0.0018), (0.06, r + 0.005, 0.0018), (0.045, -0.012, 0.0018), (0.05, -0.035, 0.0018), (0.072, -0.04, 0.0018)), 6)
    for k, (a, b) in enumerate(zip(path, path[1:])):
        chain.sphere(0.0019, a.lerp(b, 0.5) + Vector((0.0, 0.0, rng.uniform(-0.0002, 0.0002))), SILVER if k % 2 else SILVER_DARK, segments=6, scale=(1.4, 1.0, 0.6))
    chain.tube(path, 0.0008, SILVER_DARK, segments=5)
    chain.box((0.016, 0.0028, 0.0028), (0.08, -0.04, 0.0016), SILVER, rotation=(0.0, 0.0, 10.0), bevel=0.0008)
    chain_obj = chain.finish("cadena", tb.material("metal", SILVER), root)
    tb.collision_box("reloj", (0.11, 0.1, t + 0.004), (0.015, 0.01, (t + 0.004) / 2.0), root)
    tb.paint({case: None, dial: None, hours: None, minutes: None, lid_obj: None, chain_obj: None}, samples=10, ao=0.35, ao_distance=0.02, seed=1011)
    return root


# --------------------------------------------------------------------------
# Aparatos
# --------------------------------------------------------------------------


def _knurled(mb: tb.MeshBuilder, center: Vector, radius: float, height: float, color: str, ridges: int = 16, rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> None:
    """Pomo moleteado: un cilindro con estrías alrededor."""
    mb.cylinder(radius, height, center, color, rotation=rotation, segments=max(12, ridges))
    turn = Matrix.Identity(3)
    for axis, angle in zip("XYZ", rotation):
        turn = Matrix.Rotation(math.radians(angle), 3, axis) @ turn
    for k in range(ridges):
        a = 2.0 * math.pi * k / ridges
        offset = turn @ Vector((radius * math.cos(a), radius * math.sin(a), 0.0))
        mb.box((0.0012, 0.0012, height * 0.9), center + offset, color, rotation=(rotation[0], rotation[1], rotation[2] + math.degrees(a)))


def build_camera() -> bpy.types.Object:
    """Cámara de fotos de telémetro: cuerpo forrado de piel sintética negra con las
    placas cromadas, el objetivo con su anillo de enfoque, los visores y los mandos.
    Pelada en las esquinas y con el cromo rayado."""
    root = tb.empty("camara_fotos-fisico")
    w, d = 0.136, 0.032
    outline = bb.rounded_rect(w, d, 0.012, steps=4)
    mb = tb.MeshBuilder(seed=1021)
    mb.prism(outline, 0.05, (0.0, 0.0, 0.037), LEATHERETTE, bevel=0.0015)
    plate = bb.rounded_rect(w + 0.002, d + 0.002, 0.013, steps=4)
    mb.prism(plate, 0.012, (0.0, 0.0, 0.006), CHROME, bevel=0.0018)
    mb.prism(plate, 0.016, (0.0, 0.0, 0.07), CHROME, bevel=0.002)
    # Los visores del telémetro, en el frente de la placa de arriba.
    mb.box((0.014, 0.0012, 0.008), (-0.043, -d / 2.0 - 0.0011, 0.07), LENS_GLASS, bevel=0.0004)
    mb.cylinder(0.0042, 0.0012, (0.043, -d / 2.0 - 0.0011, 0.07), LENS_GLASS, rotation=(90.0, 0.0, 0.0), segments=12)
    mb.box((0.006, 0.0012, 0.006), (0.024, -d / 2.0 - 0.0011, 0.07), CHROME_DARK, bevel=0.0004)
    # Arriba: rueda de velocidades, disparador, avance y rebobinado, y la zapata.
    _knurled(mb, Vector((0.028, 0.002, 0.081)), 0.009, 0.006, CHROME, ridges=20)
    mb.cylinder(0.0028, 0.005, (0.044, -0.007, 0.081), CHROME, segments=10)
    _knurled(mb, Vector((0.054, 0.002, 0.082)), 0.0105, 0.007, CHROME, ridges=20)
    _knurled(mb, Vector((-0.052, 0.002, 0.082)), 0.0095, 0.007, CHROME, ridges=18)
    mb.box((0.012, 0.0022, 0.0016), (-0.052, -0.004, 0.0865), CHROME_DARK, rotation=(0.0, 0.0, 30.0))
    mb.box((0.018, 0.016, 0.003), (-0.012, 0.0, 0.0795), CHROME_DARK, bevel=0.0006)
    # Las anillas de la correa y un trozo de correa.
    for side in (-1.0, 1.0):
        loop = [Vector((side * (w / 2.0 + 0.002) + side * 0.004 * math.cos(2.0 * math.pi * k / 16.0), 0.0, 0.066 + 0.004 * math.sin(2.0 * math.pi * k / 16.0))) for k in range(17)]
        mb.tube(loop, 0.0009, CHROME, segments=5, caps=False)
    body = mb.finish("cuerpo", tb.material("metal", CHROME), root)
    tb.stain(body, "#5A5650", amount=0.5, scale=60.0, coverage=0.3, seed=1022)
    tb.stain(body, CHROME_DARK, amount=0.5, scale=120.0, coverage=0.3, seed=1023)

    lens = tb.MeshBuilder(seed=1024)
    mount = Vector((0.0, -d / 2.0, 0.039))
    lens.lathe([(0.0215, -0.001), (0.0215, 0.004), (0.019, 0.005)], mount, CHROME, rotation=(90.0, 0.0, 0.0), segments=28)
    lens.lathe([(0.019, 0.005), (0.0195, 0.006), (0.0195, 0.013), (0.0178, 0.014)], mount, LEATHERETTE, rotation=(90.0, 0.0, 0.0), segments=28)
    for k in range(20):
        a = 2.0 * math.pi * k / 20.0
        lens.box((0.0016, 0.007, 0.0016), mount + Vector((0.0196 * math.cos(a), -0.0095, 0.0196 * math.sin(a))), LEATHERETTE, rotation=(0.0, -math.degrees(a), 0.0))
    lens.lathe([(0.0178, 0.014), (0.0172, 0.024), (0.016, 0.026), (0.016, 0.032), (0.0138, 0.033), (0.0128, 0.0315)], mount, CHROME, rotation=(90.0, 0.0, 0.0), segments=28)
    lens.lathe([(0.0128, 0.0315), (0.008, 0.0305), (0.0, 0.03)], mount, LENS_GLASS, rotation=(90.0, 0.0, 0.0), segments=28)
    for k in range(12):
        a = math.radians(k * 30.0)
        lens.box((0.0008, 0.0006, 0.0018), mount + Vector((0.0168 * math.cos(a), -0.0225, 0.0168 * math.sin(a))), INK, rotation=(0.0, -math.degrees(a), 0.0))
    lens_obj = lens.finish("objetivo", tb.material("metal", CHROME), root)
    tb.stain(lens_obj, CHROME_DARK, amount=0.45, scale=110.0, coverage=0.3, seed=1025)
    tb.collision_box("camara", (w + 0.008, d + 0.036, 0.088), (0.0, -0.016, 0.044), root)
    tb.paint({body: None, lens_obj: None}, samples=12, ao=0.35, ao_distance=0.03, seed=1021)
    return root


def build_microscope() -> bpy.types.Object:
    """Microscopio de laboratorio: pie de herradura, columna y brazo de esmalte negro,
    la platina con sus pinzas, el espejo debajo, el revólver con tres objetivos, el
    tubo y el ocular, y los mandos de enfoque. Esmalte saltado y polvo."""
    root = tb.empty("microscopio-fisico")
    black = tb.MeshBuilder(seed=1031)
    # Pie de herradura (en planta), con la abertura hacia delante.
    shoe = [(-0.055, -0.05), (-0.03, -0.05), (-0.026, -0.002), (0.026, -0.002), (0.03, -0.05), (0.055, -0.05), (0.06, 0.02), (0.045, 0.05), (-0.045, 0.05), (-0.06, 0.02)]
    black.prism(shoe, 0.018, (0.0, 0.0, 0.009), ENAMEL_BLACK, bevel=0.003, segments=2)
    # Columna, articulación y brazo curvo (de perfil, en el plano YZ).
    black.box((0.034, 0.026, 0.07), (0.0, 0.03, 0.053), ENAMEL_BLACK, bevel=0.004, segments=2)
    black.cylinder(0.011, 0.04, (0.0, 0.03, 0.09), ENAMEL_BLACK, rotation=(0.0, 90.0, 0.0), segments=16)
    arm = [(0.04, 0.085), (0.044, 0.12), (0.038, 0.17), (0.022, 0.215), (0.004, 0.235), (-0.006, 0.222), (0.012, 0.2), (0.022, 0.16), (0.024, 0.12), (0.02, 0.085)]
    black.prism([(y, z) for y, z in arm], 0.026, (0.0, 0.0, 0.0), ENAMEL_BLACK, rotation=(90.0, 0.0, 90.0), bevel=0.003, segments=2)
    # Platina cuadrada con su agujero, delante del brazo.
    black.box((0.085, 0.08, 0.006), (0.0, -0.005, 0.112), ENAMEL_BLACK, bevel=0.0018)
    black.box((0.012, 0.03, 0.02), (0.0, 0.026, 0.1), ENAMEL_BLACK, bevel=0.002)
    # Cremallera y soporte del tubo.
    black.box((0.022, 0.02, 0.05), (0.0, 0.006, 0.22), ENAMEL_BLACK, bevel=0.003)
    stand = black.finish("armazon", tb.material("metal", ENAMEL_BLACK), root)
    tb.stain(stand, "#6A6660", amount=0.6, scale=90.0, coverage=0.18, seed=1032)
    tb.stain(stand, DIRT, amount=0.5, scale=40.0, coverage=0.3, seed=1033)

    bright = tb.MeshBuilder(seed=1034)
    bb.disc(bright, (0.0, -0.005, 0.115), (0.0, 0.0, 1.0), 0.0075, INK, thickness=0.0004, segments=16)
    for side in (-1.0, 1.0):
        bright.bar((side * 0.028, 0.022, 0.1165), (side * 0.022, -0.026, 0.1158), 0.0011, CHROME, 6)
        bright.cylinder(0.0024, 0.004, (side * 0.028, 0.022, 0.117), CHROME, segments=8)
    # El espejo, en su horquilla, inclinado hacia la luz de delante.
    bright.bar((0.0, 0.006, 0.018), (0.0, -0.004, 0.05), 0.0025, CHROME, 8)
    bright.bar((-0.019, -0.004, 0.05), (0.019, -0.004, 0.05), 0.002, CHROME, 8)
    for side in (-1.0, 1.0):
        bright.bar((side * 0.019, -0.004, 0.05), (side * 0.019, -0.006, 0.07), 0.002, CHROME, 8)
    bright.lathe([(0.0, 0.0), (0.0175, 0.0), (0.0175, 0.004), (0.0155, 0.004), (0.0, 0.0028)], (0.0, -0.006, 0.07), MIRROR, rotation=(-40.0, 0.0, 0.0), segments=20)
    # El tubo, el ocular y el revólver con sus objetivos.
    tube_axis = Vector((0.0, -0.005, 0.0))
    bright.lathe([(0.0, 0.0), (0.0235, 0.002), (0.022, 0.012), (0.017, 0.016), (0.0, 0.017)], tube_axis + Vector((0.0, 0.0, 0.17)), CHROME, rotation=(180.0, 0.0, 0.0), segments=20)
    for k, angle in enumerate((0.0, 120.0, 240.0)):
        a = math.radians(angle)
        offset = Vector((0.011 * math.sin(a), -0.011 * math.cos(a), 0.0))
        length = 0.022 + k * 0.005
        bright.lathe([(0.0062, 0.0), (0.0062, length * 0.6), (0.0048, length), (0.0028, length + 0.002), (0.0, length + 0.002)], tube_axis + offset + Vector((0.0, 0.0, 0.158)), CHROME, rotation=(180.0, 0.0, 0.0), segments=12)
    bright.cylinder(0.0155, 0.09, tube_axis + Vector((0.0, 0.0, 0.215)), ENAMEL_BLACK, segments=20)
    bright.lathe([(0.0158, 0.0), (0.0165, 0.003), (0.0165, 0.008), (0.012, 0.012), (0.012, 0.028), (0.0138, 0.03), (0.0138, 0.034), (0.009, 0.035), (0.0, 0.034)], tube_axis + Vector((0.0, 0.0, 0.258)), CHROME, segments=20)
    bb.disc(bright, tube_axis + Vector((0.0, 0.0, 0.2925)), (0.0, 0.0, 1.0), 0.0075, INK, thickness=0.0004, segments=14)
    # Mandos de enfoque, a los dos lados de la columna.
    for side in (-1.0, 1.0):
        _knurled(bright, Vector((side * 0.026, 0.006, 0.212)), 0.016, 0.009, CHROME, ridges=18, rotation=(0.0, 90.0, 0.0))
        _knurled(bright, Vector((side * 0.024, 0.03, 0.09)), 0.009, 0.008, CHROME, ridges=12, rotation=(0.0, 90.0, 0.0))
    metal = bright.finish("cromado", tb.material("metal", CHROME), root)
    tb.stain(metal, CHROME_DARK, amount=0.5, scale=100.0, coverage=0.3, seed=1035)
    tb.collision_box("microscopio", (0.13, 0.11, 0.3), (0.0, 0.0, 0.15), root)
    tb.paint({stand: None, metal: None}, samples=14, ao=0.4, ao_distance=0.05, seed=1031)
    return root


# --------------------------------------------------------------------------
# Recuerdos
# --------------------------------------------------------------------------


def build_medal() -> bpy.types.Object:
    """Medalla en su estuche: la caja de piel granate abierta, terciopelo en la
    base y raso en la tapa; la medalla con su pasador pentagonal de cinta a rayas,
    la anilla y la estrella en relieve."""
    root = tb.empty("medalla-fisico")
    w, d, h = 0.062, 0.088, 0.018
    outline = bb.rounded_rect(w, d, 0.006, steps=3)
    mb = tb.MeshBuilder(seed=1041)
    mb.prism(outline, h, (0.0, 0.0, h / 2.0), CASE_RED, bevel=0.0018, segments=2)
    mb.prism(bb.rounded_rect(w - 0.006, d - 0.006, 0.004, steps=3), 0.0012, (0.0, 0.0, h + 0.0002), VELVET, bevel=0.0004)
    for side in (-1.0, 1.0):
        mb.cylinder(0.0018, 0.012, (side * 0.016, d / 2.0 + 0.0006, h), "#8A7A5A", rotation=(0.0, 90.0, 0.0), segments=8)
    mb.box((0.008, 0.002, 0.006), (0.0, -d / 2.0 - 0.0008, h - 0.004), "#8A7A5A", bevel=0.0005)
    base = mb.finish("estuche", tb.material("cuero", CASE_RED), root)
    tb.stain(base, CASE_RED_DARK, amount=0.5, scale=50.0, coverage=0.35, seed=1042)
    tb.stain(base, DIRT, amount=0.45, scale=35.0, coverage=0.25, seed=1043)

    lid = tb.MeshBuilder(seed=1044)
    lid_h = 0.012
    lid.prism(outline, lid_h, (0.0, 0.0, h + lid_h / 2.0), CASE_RED, bevel=0.0018, segments=2)
    lid.prism(bb.rounded_rect(w - 0.006, d - 0.006, 0.004, steps=3), 0.0012, (0.0, 0.0, h - 0.0004), SATIN, bevel=0.0004)
    lid.box((0.03, 0.012, 0.0004), (0.0, 0.01, h - 0.0011), GOLD_DARK)
    lid_obj = lid.finish("tapa", tb.material("cuero", CASE_RED), root)
    tb.stain(lid_obj, CASE_RED_DARK, amount=0.5, scale=50.0, coverage=0.35, seed=1045)
    hinge = Vector((0.0, d / 2.0, h))
    tb.set_origin(lid_obj, hinge)
    lid_obj.rotation_euler = (math.radians(-104.0), 0.0, 0.0)

    medal = tb.MeshBuilder(seed=1046)
    top = h + 0.0016
    ribbon = Vector((0.0, 0.018, top))
    pentagon = [(-0.0125, -0.003), (0.0, -0.016), (0.0125, -0.003), (0.0125, 0.012), (-0.0125, 0.012)]
    medal.prism(pentagon, 0.0024, ribbon + Vector((0.0, 0.0, 0.0012)), RIBBON_GREY, bevel=0.0006)
    for x, color in ((-0.0075, RIBBON_RED), (0.0, RIBBON_YELLOW), (0.0075, RIBBON_RED)):
        medal.box((0.0032, 0.0148, 0.0004), ribbon + Vector((x, 0.0045, 0.0025)), color)
    loop = [ribbon + Vector((0.0, -0.016 - 0.003 + 0.003 * math.cos(2.0 * math.pi * k / 16.0), 0.0012 + 0.003 * math.sin(2.0 * math.pi * k / 16.0))) for k in range(17)]
    medal.tube(loop, 0.0008, GOLD, segments=5, caps=False)
    disc_center = Vector((0.0, -0.016, top))
    medal.lathe([(0.0, 0.0), (0.0158, 0.0), (0.0164, 0.0012), (0.0158, 0.0026), (0.0148, 0.0026), (0.0142, 0.0018), (0.0, 0.0018)], disc_center, GOLD, segments=32, sharp_angle=40.0)
    medal.prism(bb.star(5, 0.0115, 0.0048), 0.0016, disc_center + Vector((0.0, 0.0, 0.0024)), GOLD, bevel=0.0004)
    medal.cylinder(0.0034, 0.0012, disc_center + Vector((0.0, 0.0, 0.0034)), RIBBON_RED, segments=14)
    medal_obj = medal.finish("medalla", tb.material("metal", GOLD), root)
    tb.stain(medal_obj, GOLD_DARK, amount=0.55, scale=150.0, coverage=0.35, seed=1047)
    tb.collision_box("estuche", (w, d + 0.02, h + 0.06), (0.0, 0.008, (h + 0.06) / 2.0), root)
    tb.paint({base: None, lid_obj: None, medal_obj: None}, samples=10, ao=0.35, ao_distance=0.02, seed=1041)
    return root


def build_samovar() -> bpy.types.Object:
    """Samovar de latón: el pie, el vaso con las medallas estampadas y los aros, las
    asas de madera negra, el grifo con su llave por delante y, arriba, la corona
    para la tetera y la chimenea. Abollado, ennegrecido y con cardenillo."""
    root = tb.empty("samovar-fisico")
    mb = tb.MeshBuilder(seed=1051)
    profile = [
        (0.0, 0.0), (0.072, 0.0), (0.076, 0.004), (0.074, 0.011), (0.058, 0.016), (0.042, 0.03), (0.037, 0.048), (0.044, 0.062),
        (0.07, 0.07), (0.095, 0.086), (0.112, 0.11), (0.121, 0.135), (0.124, 0.16), (0.122, 0.185), (0.117, 0.208), (0.108, 0.23),
        (0.096, 0.25), (0.083, 0.266), (0.076, 0.276), (0.079, 0.282), (0.076, 0.288), (0.062, 0.293), (0.045, 0.302),
        (0.033, 0.308), (0.031, 0.312), (0.031, 0.33), (0.035, 0.334), (0.0, 0.336),
    ]
    mb.lathe(profile, (0.0, 0.0, 0.0), BRASS, segments=36, sharp_angle=50.0)
    for z, radius in ((0.11, 0.1125), (0.208, 0.1175), (0.07, 0.0715)):
        mb.lathe([(radius, z - 0.003), (radius + 0.0035, z), (radius, z + 0.003)], (0.0, 0.0, 0.0), BRASS, segments=36)
    # Medallas estampadas en el hombro, por delante.
    for k, angle in enumerate((-36.0, -12.0, 12.0, 36.0)):
        z = 0.2
        radius = 0.1196
        at = bb.around(radius, angle, z)
        bb.disc(mb, at, bb.around(1.0, angle, 0.0) + Vector((0.0, 0.0, 0.35)), 0.0105, "#A88448", thickness=0.0009, segments=16)
        bb.disc(mb, at + bb.around(1.0, angle, 0.0) * 0.0009, bb.around(1.0, angle, 0.0) + Vector((0.0, 0.0, 0.35)), 0.0065, "#B8944E", thickness=0.0005, segments=12)
    # La corona para la tetera, sobre cuatro patitas, y el tapón de la chimenea.
    for k in range(4):
        a = math.radians(45.0 + k * 90.0)
        mb.bar((0.05 * math.sin(a), -0.05 * math.cos(a), 0.296), (0.055 * math.sin(a), -0.055 * math.cos(a), 0.345), 0.0028, BRASS, 8)
    mb.lathe([(0.05, 0.342), (0.064, 0.343), (0.066, 0.348), (0.062, 0.352), (0.05, 0.35), (0.05, 0.342)], (0.0, 0.0, 0.0), BRASS, segments=36)
    mb.lathe([(0.0, 0.336), (0.028, 0.336), (0.026, 0.344), (0.012, 0.35), (0.008, 0.36), (0.0, 0.362)], (0.0, 0.0, 0.0), BRASS, segments=20)
    # El grifo, por delante, con el caño hacia abajo y la llave.
    spout = [bb.around(0.1, 0.0, 0.098), bb.around(0.13, 0.0, 0.1), bb.around(0.152, 0.0, 0.096), bb.around(0.162, 0.0, 0.082), bb.around(0.164, 0.0, 0.07)]
    mb.tube(tb.smooth_path(spout, 4), 0.0072, BRASS, segments=10)
    mb.lathe([(0.0, 0.0), (0.0105, 0.0), (0.0115, 0.006), (0.009, 0.012), (0.0, 0.012)], bb.around(0.118, 0.0, 0.092), BRASS, segments=14)
    mb.bar(bb.around(0.118, 0.0, 0.104), bb.around(0.118, 0.0, 0.112), 0.0022, BRASS, 6)
    mb.prism([(-0.016, 0.0), (0.016, 0.0), (0.012, 0.006), (0.004, 0.008), (-0.004, 0.008), (-0.012, 0.006)], 0.004, bb.around(0.118, 0.0, 0.112), BRASS, rotation=(90.0, 0.0, 0.0), bevel=0.001)
    # Las asas: de latón, con el puño de madera negra.
    for side in (-1.0, 1.0):
        path = [(side * 0.093, 0.0, 0.252), (side * 0.13, 0.0, 0.26), (side * 0.155, 0.0, 0.246), (side * 0.16, 0.0, 0.218), (side * 0.155, 0.0, 0.194), (side * 0.12, 0.0, 0.184)]
        mb.tube(tb.smooth_path(path, 4), 0.0032, BRASS, segments=8)
    brass = mb.finish("samovar", tb.material("metal", BRASS), root)
    tb.stain(brass, TARNISH, amount=0.75, scale=18.0, coverage=0.55, seed=1052, stretch_z=0.6)
    tb.stain(brass, PATINA, amount=0.6, scale=40.0, coverage=0.22, seed=1053)
    tb.stain(brass, "#2E2620", amount=0.55, scale=60.0, coverage=0.2, seed=1054)
    tb.dent(brass, bb.around(0.122, 140.0, 0.15), radius=0.04, depth=0.006)
    tb.dent(brass, bb.around(0.118, -70.0, 0.19), radius=0.025, depth=0.004)

    wood = tb.MeshBuilder(seed=1055)
    for side in (-1.0, 1.0):
        wood.cylinder(0.0075, 0.038, (side * 0.16, 0.0, 0.219), WOOD_BLACK, segments=10)
    grips = wood.finish("asas", tb.material("madera", WOOD_BLACK), root)
    tb.stain(grips, "#5A4A3A", amount=0.4, scale=90.0, coverage=0.3, seed=1056)
    tb.collision_box("samovar", (0.34, 0.26, 0.362), (0.0, -0.02, 0.181), root)
    tb.paint({brass: None, grips: None}, samples=16, ao=0.45, ao_distance=0.07, seed=1051)
    return root


def build_icon() -> bpy.types.Object:
    """Un icono de la iglesia vieja, tumbado boca arriba: tabla de madera con la
    pintura oscurecida por el humo de las velas y la cubierta de metal repujado que
    solo deja ver la cara, el nimbo y las manos. Tiznado, con la tabla rajada."""
    rng = random.Random(1061)
    root = tb.empty("icono-fisico")
    W, H, D = 0.2, 0.26, 0.022
    mb = tb.MeshBuilder(seed=1061)
    # Se construye de pie (mirando a -Y) y al final se tumba boca arriba.
    mb.box((W, D, H), (0.0, -D / 2.0, H / 2.0), ICON_WOOD, bevel=0.003, segments=2, cuts=3)
    window = (-0.058, 0.07, 0.058, 0.205)
    front = -D - 0.0004
    # La pintura que asoma por la ventana de la cubierta.
    mb.box((0.118, 0.0008, 0.138), (0.0, front, 0.137), ICON_GROUND)
    mb.prism(bb.ellipse(0.096, 0.1, 20), 0.0008, (0.0, front - 0.0004, 0.096), ICON_ROBE, rotation=(90.0, 0.0, 0.0))
    mb.prism([(-0.05, 0.07), (-0.02, 0.07), (0.0, 0.108), (0.02, 0.07), (0.05, 0.07), (0.048, 0.1), (0.022, 0.13), (0.0, 0.135), (-0.022, 0.13), (-0.048, 0.1)], 0.0008, (0.0, front - 0.0008, 0.0), ICON_MANTLE, rotation=(90.0, 0.0, 0.0))
    bb.disc(mb, (0.0, front - 0.0006, 0.166), (0.0, -1.0, 0.0), 0.03, GOLD, thickness=0.0008, segments=24)
    bb.disc(mb, (0.0, front - 0.0014, 0.162), (0.0, -1.0, 0.0), 0.0145, ICON_FACE, thickness=0.0008, segments=18, squash=0.78)
    for side in (-1.0, 1.0):
        mb.box((0.004, 0.0006, 0.0012), (side * 0.0055, front - 0.0022, 0.166), "#3A2418")
    mb.box((0.0016, 0.0006, 0.008), (0.0, front - 0.0022, 0.16), "#8A6A40")
    for x, z in ((-0.024, 0.118), (0.02, 0.114)):
        bb.disc(mb, (x, front - 0.0014, z), (0.0, -1.0, 0.0), 0.0065, ICON_FACE, thickness=0.0008, segments=12, squash=0.7)
    painting = mb.finish("tabla", tb.material("madera", ICON_WOOD), root)
    tb.stain(painting, "#1E1612", amount=0.6, scale=30.0, coverage=0.35, seed=1062, stretch_z=0.5)

    cover = tb.MeshBuilder(seed=1063)
    oklad_y = (-D - 0.0024, -D - 0.0002)
    cover.slab((-W / 2.0 + 0.003, W / 2.0 - 0.003), (0.003, H - 0.003), oklad_y, OKLAD, holes=[window], bevel=0.0008, step=0.02)
    # El arco de la ventana: dos esquineras curvas arriba.
    corner = [(0.0, 0.0), (0.022, 0.0)] + [(0.022 - 0.022 * math.sin(math.radians(a)), 0.022 - 0.022 * math.cos(math.radians(a))) for a in range(15, 90, 15)] + [(0.0, 0.022)]
    for side in (-1.0, 1.0):
        x0 = window[2] if side > 0 else window[0]
        outline = [(x0 - side * u, window[3] - v) for u, v in corner]
        if side < 0:
            outline.reverse()
        cover.prism(outline, 0.0022, (0.0, (oklad_y[0] + oklad_y[1]) / 2.0, 0.0), OKLAD, rotation=(90.0, 0.0, 0.0))
    # Repujado: cordón de perlas alrededor, rosetas en las esquinas y el borde del nimbo.
    for k in range(34):
        t = k / 34.0
        perimeter = 2.0 * (W + H - 0.03)
        s = t * perimeter
        if s < W - 0.015:
            x, z = -W / 2.0 + 0.0075 + s, 0.0075
        elif s < W - 0.015 + H - 0.015:
            x, z = W / 2.0 - 0.0075, 0.0075 + (s - (W - 0.015))
        elif s < 2.0 * (W - 0.015) + H - 0.015:
            x, z = W / 2.0 - 0.0075 - (s - (W - 0.015 + H - 0.015)), H - 0.0075
        else:
            x, z = -W / 2.0 + 0.0075, H - 0.0075 - (s - (2.0 * (W - 0.015) + H - 0.015))
        cover.sphere(0.0022, (x, oklad_y[0], z), OKLAD, segments=6, scale=(1.0, 0.5, 1.0))
    for x in (-W / 2.0 + 0.022, W / 2.0 - 0.022):
        for z in (0.022, H - 0.022):
            for k in range(6):
                a = math.radians(k * 60.0)
                cover.sphere(0.0032, (x + 0.0055 * math.cos(a), oklad_y[0], z + 0.0055 * math.sin(a)), OKLAD, segments=6, scale=(1.0, 0.45, 1.0))
            cover.sphere(0.003, (x, oklad_y[0] - 0.0004, z), GOLD, segments=6, scale=(1.0, 0.5, 1.0))
    halo = [Vector((0.031 * math.cos(2.0 * math.pi * k / 32.0), oklad_y[0] - 0.0006, 0.166 + 0.031 * math.sin(2.0 * math.pi * k / 32.0))) for k in range(33)]
    cover.tube(halo, 0.0016, GOLD, segments=6, caps=False)
    for k in range(5):
        cover.box((0.11 - k * 0.018, 0.0006, 0.0016), (0.0, oklad_y[0] - 0.0002, 0.04 - k * 0.0045 + rng.uniform(-0.0004, 0.0004)), OKLAD_DARK)
    metal = cover.finish("cubierta", tb.material("metal", OKLAD), root)
    tb.stain(metal, OKLAD_DARK, amount=0.7, scale=40.0, coverage=0.45, seed=1064)
    tb.stain(metal, "#2A2420", amount=0.55, scale=25.0, coverage=0.25, seed=1065, stretch_z=0.5)

    # Tumbarlo boca arriba: la cara de delante (-Y) pasa a mirar a +Z.
    lay = Matrix.Rotation(math.radians(-90.0), 4, "X")
    shift = Matrix.Translation((0.0, -H / 2.0, 0.0))
    for obj in (painting, metal):
        obj.data.transform(shift @ lay)
        obj.data.update()
    tb.collision_box("icono", (W, H, D + 0.004), (0.0, 0.0, (D + 0.004) / 2.0), root)
    tb.paint({painting: None, metal: None}, samples=12, ao=0.4, ao_distance=0.03, seed=1061)
    return root


def models() -> dict:
    return {
        "reloj_pulsera": build_wristwatch,
        "camara_fotos": build_camera,
        "medalla": build_medal,
        "samovar": build_samovar,
        "microscopio": build_microscope,
        "icono": build_icon,
        "reloj_bolsillo": build_pocket_watch,
    }
