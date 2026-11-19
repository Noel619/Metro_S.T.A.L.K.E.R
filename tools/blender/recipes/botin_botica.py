"""El botín de la botica: medicinas y lo que hace falta para respirar ahí arriba.
Lo que más se busca y lo que más se paga, de lo común a lo muy raro.

- El filtro de recambio de la máscara (el mismo bote que lleva ``mascara``).
- Las pastillas para el dolor, el frasco de yodo y la jeringa de cristal en su
  estuche de acero.
- Los antibióticos en sus viales, las pastillas antirradiación de la defensa
  civil y el botiquín individual naranja del ejército.
- La insulina: lo más difícil de encontrar.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. Todo
descansa sobre z = 0 y enseña su frente hacia -Y. Las reglas del botín (nada
está intacto) están en tools/blender/botin_bpy.py.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

import botin_bpy as bb
import tumansk_bpy as tb

INK = "#1B1A22"
RUST = "#7E4128"
DIRT = "#4E4233"
OLIVE = "#5E6748"
OLIVE_DARK = "#454D38"
LABEL = "#D9CDB0"
RUBBER = "#2A2A28"
PAPER_WHITE = "#E2DCC8"
PHARMA_GREEN = "#4A7A5A"
PHARMA_RED = "#A8302A"
TABLET = "#ECE8DC"
STRIP = "#D6D0BE"
IODINE_GLASS = "#5A3018"
IODINE = "#4A1C0C"
CAP_BLACK = "#1E1E1E"
STEEL = "#9AA0A0"
STEEL_DARK = "#6A7070"
SYRINGE_GLASS = "#BFC8C4"
VIAL_GLASS = "#BCC6C0"
POWDER = "#ECE8DC"
STOPPER = "#6A6E70"
CRIMP = "#A8ACAA"
CIVIL_YELLOW = "#D2A830"
FOIL = "#B8BAB4"
ARMY_ORANGE = "#B4602E"
ARMY_ORANGE_DARK = "#9A4A1E"
INSULIN_BLUE = "#3A5A8A"
INSULIN_CAP = "#C86A2A"


def _box(mb: tb.MeshBuilder, center: Vector, size: tuple[float, float, float], color: str, *, top: bool = True, wall: float = 0.0012) -> None:
    """Caja de cartón abierta por arriba (o cerrada con ``top``), de paredes finas."""
    w, d, h = size
    mb.box((w, d, wall), center + Vector((0.0, 0.0, wall / 2.0)), color)
    for side in (-1.0, 1.0):
        mb.box((w, wall, h), center + Vector((0.0, side * (d / 2.0 - wall / 2.0), h / 2.0)), color, bevel=0.0003)
        mb.box((wall, d - 2.0 * wall, h), center + Vector((side * (w / 2.0 - wall / 2.0), 0.0, h / 2.0)), color, bevel=0.0003)
    if top:
        mb.box((w, d, wall), center + Vector((0.0, 0.0, h - wall / 2.0)), color)


def _vial(mb: tb.MeshBuilder, base: Vector, radius: float, height: float, rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> None:
    """Vial de vidrio con el tapón de goma y la cápsula de aluminio engarzada."""
    neck = radius * 0.62
    mb.lathe(
        [(0.0, 0.0), (radius - 0.0008, 0.0), (radius, 0.001), (radius, height * 0.68), (radius * 0.9, height * 0.76), (neck, height * 0.8), (neck, height * 0.84), (0.0, height * 0.84)],
        base, VIAL_GLASS, rotation=rotation, segments=14, sharp_angle=50.0,
    )


# --------------------------------------------------------------------------
# Para respirar
# --------------------------------------------------------------------------


def build_filter() -> bpy.types.Object:
    """Filtro de recambio de la máscara: el mismo bote verde oliva, con la etiqueta,
    la rosca tapada con su tapón de goma y abolladuras de haber rodado."""
    root = tb.empty("filtro-fisico")
    mb = tb.MeshBuilder(seed=901)
    profile = [(0.0, 0.0), (0.045, 0.0), (0.051, 0.005)]
    profile += [(0.051, 0.005 + 0.059 * k / 8.0) for k in range(1, 9)]
    profile += [(0.047, 0.07), (0.026, 0.074), (0.026, 0.078), (0.0, 0.078)]
    mb.lathe(profile, (0.0, 0.0, 0.0), OLIVE, segments=28, sharp_angle=30.0, jitter=0.04)
    for z in (0.008, 0.052, 0.06):
        mb.lathe([(0.051, z), (0.0535, z + 0.002), (0.0535, z + 0.004), (0.051, z + 0.006)], (0.0, 0.0, 0.0), OLIVE_DARK, segments=28)
    bb.band(mb, 0.0515, 0.019, 0.046, LABEL, start=-150.0, end=150.0, segments=28, rows=3, torn=6.0, seed=902)
    bb.ink_lines(mb, 0.052, (0.025, 0.031, 0.037), start=-40.0, end=40.0, thickness=0.0024)
    can = mb.finish("bote", tb.material("metal", OLIVE), root)
    tb.stain(can, RUST, amount=0.65, scale=40.0, coverage=0.22, seed=903)
    tb.stain(can, DIRT, amount=0.45, scale=30.0, coverage=0.25, seed=904)
    tb.dent(can, (0.051 * math.sin(math.radians(130.0)), -0.051 * math.cos(math.radians(130.0)), 0.03), radius=0.022, depth=0.004)

    cap = tb.MeshBuilder(seed=905)
    cap.lathe([(0.0255, 0.074), (0.0292, 0.0745), (0.0295, 0.089), (0.027, 0.0925), (0.0, 0.0925)], (0.0, 0.0, 0.0), RUBBER, segments=24, sharp_angle=40.0)
    for k in range(16):
        a = 2.0 * math.pi * k / 16.0
        cap.box((0.0018, 0.0024, 0.012), (0.0298 * math.cos(a), 0.0298 * math.sin(a), 0.082), RUBBER, rotation=(0.0, 0.0, math.degrees(a)), bevel=0.0005)
    cap_obj = cap.finish("tapon", tb.material("goma", RUBBER), root)
    tb.stain(cap_obj, "#5A5852", amount=0.4, scale=60.0, coverage=0.25, seed=906)
    tb.collision_box("filtro", (0.108, 0.108, 0.093), (0.0, 0.0, 0.0465), root)
    tb.paint({can: None, cap_obj: None}, samples=12, ao=0.4, ao_distance=0.04, seed=901)
    return root


# --------------------------------------------------------------------------
# De la farmacia
# --------------------------------------------------------------------------


def build_painkillers() -> bpy.types.Object:
    """Pastillas para el dolor: la cajita de cartón blanca con la franja verde,
    abierta por un lado, y la tira de papel con ocho pastillas sacada a medias."""
    root = tb.empty("analgesicos-fisico")
    w, d, h = 0.074, 0.044, 0.017
    mb = tb.MeshBuilder(seed=911)
    _box(mb, Vector((0.0, 0.0, 0.0)), (w, d, h), PAPER_WHITE, top=True)
    lift = 0.0004
    mb.box((w + 0.0002, 0.012, lift), (0.0, -0.008, h + lift / 2.0), PHARMA_GREEN)
    mb.box((0.012, 0.0035, lift), (-0.024, 0.012, h + lift / 2.0), PHARMA_RED)
    mb.box((0.0035, 0.012, lift), (-0.024, 0.012, h + lift / 2.0), PHARMA_RED)
    for k in range(3):
        mb.box((0.03 - k * 0.008, 0.0016, lift), (0.012, 0.004 + k * 0.0045, h + lift), INK)
    # La solapa del extremo, abierta.
    mb.box((0.0012, d - 0.002, 0.014), (w / 2.0 + 0.006, 0.0, h + 0.004), PAPER_WHITE, rotation=(0.0, 50.0, 0.0))
    box = mb.finish("caja", tb.material("carton", PAPER_WHITE), root)
    tb.stain(box, "#B8A884", amount=0.55, scale=50.0, coverage=0.3, seed=912)
    tb.stain(box, DIRT, amount=0.35, scale=70.0, coverage=0.2, seed=913)

    strip = tb.MeshBuilder(seed=914)
    origin = Vector((0.055, -0.012, 0.0012))
    strip.box((0.072, 0.024, 0.0012), origin, STRIP, rotation=(0.0, 0.0, -14.0), bevel=0.0003)
    turn = math.radians(-14.0)
    for i in range(4):
        for j in range(2):
            local = Vector((-0.027 + i * 0.018, -0.0055 + j * 0.011, 0.0))
            at = origin + Vector((local.x * math.cos(turn) - local.y * math.sin(turn), local.x * math.sin(turn) + local.y * math.cos(turn), 0.0006))
            strip.sphere(0.0046, at, TABLET, segments=10, scale=(1.0, 1.0, 0.42))
    strip.box((0.05, 0.0012, 0.0004), origin + Vector((0.0, -0.011, 0.0008)), PHARMA_GREEN, rotation=(0.0, 0.0, -14.0))
    strip_obj = strip.finish("tira", tb.material("papel_viejo", STRIP), root)
    tb.stain(strip_obj, "#A89878", amount=0.4, scale=60.0, coverage=0.2, seed=915)
    tb.collision_box("analgesicos", (0.13, 0.05, 0.02), (0.025, -0.004, 0.01), root)
    tb.paint({box: None, strip_obj: None}, samples=10, ao=0.35, ao_distance=0.02, seed=911)
    return root


def build_iodine() -> bpy.types.Object:
    """Frasco de yodo: vidrio marrón, tapón negro de rosca y la etiqueta con la raya
    roja, manchada por los chorretones que se escaparon del tapón."""
    root = tb.empty("yodo-fisico")
    mb = tb.MeshBuilder(seed=921)
    mb.lathe([(0.0, 0.0), (0.0128, 0.0), (0.0142, 0.0018), (0.0142, 0.016), (0.0142, 0.032), (0.0142, 0.046), (0.0128, 0.051), (0.0082, 0.056), (0.0076, 0.059), (0.0076, 0.064), (0.0, 0.064)], (0.0, 0.0, 0.0), IODINE_GLASS, segments=20, sharp_angle=50.0)
    bottle = mb.finish("frasco", tb.material("vidrio", IODINE_GLASS), root)

    paper = tb.MeshBuilder(seed=922)
    bb.band(paper, 0.0145, 0.012, 0.04, LABEL, start=-120.0, end=120.0, segments=20, rows=4, torn=4.0, seed=923)
    bb.band(paper, 0.0148, 0.031, 0.036, PHARMA_RED, start=-110.0, end=110.0, segments=20)
    bb.ink_lines(paper, 0.0148, (0.018, 0.023), start=-35.0, end=35.0, thickness=0.0018)
    for k, (angle, length) in enumerate(((-20.0, 0.026), (15.0, 0.018), (60.0, 0.032), (-75.0, 0.012))):
        top = 0.05
        paper.tube([bb.around(0.0146 + 0.0002 * k, angle, top), bb.around(0.015, angle + 2.0, top - length * 0.5), bb.around(0.015, angle + 1.0, top - length)], 0.0011, IODINE, segments=5)
    label = paper.finish("etiqueta", tb.material("etiqueta", LABEL), root)
    tb.stain(label, "#8A5A2A", amount=0.6, scale=60.0, coverage=0.3, seed=924, stretch_z=0.5)

    cap = tb.MeshBuilder(seed=925)
    cap.lathe([(0.0074, 0.0565), (0.0094, 0.057), (0.0096, 0.0705), (0.0084, 0.073), (0.0, 0.073)], (0.0, 0.0, 0.0), CAP_BLACK, segments=18, sharp_angle=40.0)
    for k in range(12):
        a = 2.0 * math.pi * k / 12.0
        cap.box((0.0012, 0.0016, 0.011), (0.0098 * math.cos(a), 0.0098 * math.sin(a), 0.064), CAP_BLACK, rotation=(0.0, 0.0, math.degrees(a)))
    cap_obj = cap.finish("tapon", tb.material("plastico", CAP_BLACK), root)
    tb.stain(cap_obj, IODINE, amount=0.6, scale=80.0, coverage=0.35, seed=926)
    tb.collision_box("yodo", (0.03, 0.03, 0.073), (0.0, 0.0, 0.0365), root)
    tb.paint({bottle: None, label: None, cap_obj: None}, samples=10, ao=0.3, ao_distance=0.02, seed=921)
    return root


def build_syringe() -> bpy.types.Object:
    """Jeringa de cristal en su estuche de acero, para hervirla: la caja abierta con
    la jeringa y su aguja dentro y la tapa al lado, boca arriba."""
    root = tb.empty("jeringa-fisico")
    w, d, h, r = 0.132, 0.04, 0.016, 0.009
    case = tb.MeshBuilder(seed=931)
    outline = bb.rounded_rect(w, d, r, steps=4)
    case.prism(outline, 0.0016, (0.0, 0.0, 0.0008), STEEL, bevel=0.0005)
    path = [Vector((x, y, h / 2.0)) for x, y in outline]
    path.append(path[0])
    bb.strap(case, path, h, 0.0012, STEEL, center=(0.0, 0.0, h / 2.0))
    # La tapa, al lado, boca arriba: un poco más grande y abombada.
    lid_center = Vector((0.004, -d - 0.012, 0.0))
    lid_outline = bb.rounded_rect(w + 0.004, d + 0.004, r + 0.002, steps=4)
    case.prism(lid_outline, 0.0016, lid_center + Vector((0.0, 0.0, 0.0008)), STEEL, bevel=0.0005)
    lid_path = [lid_center + Vector((x, y, 0.006)) for x, y in lid_outline]
    lid_path.append(lid_path[0])
    bb.strap(case, lid_path, 0.012, 0.0012, STEEL, center=lid_center + Vector((0.0, 0.0, 0.006)))
    steel = case.finish("estuche", tb.material("metal", STEEL), root)
    tb.stain(steel, STEEL_DARK, amount=0.5, scale=40.0, coverage=0.3, seed=932)
    tb.stain(steel, RUST, amount=0.55, scale=90.0, coverage=0.12, seed=933)

    syringe = tb.MeshBuilder(seed=934)
    axis_z = 0.0072
    syringe.cylinder(0.0055, 0.068, (-0.006, 0.0, axis_z), SYRINGE_GLASS, rotation=(0.0, 90.0, 0.0), segments=14)
    for k in range(11):
        x = -0.034 + k * 0.0055
        syringe.box((0.0006, 0.0022 if k % 5 else 0.004, 0.0004), (x, -0.0045, axis_z + 0.0038), INK, rotation=(48.0, 0.0, 0.0))
    syringe.box((0.003, 0.021, 0.008), (-0.041, 0.0, axis_z), STEEL, bevel=0.001)
    syringe.cylinder(0.0016, 0.03, (-0.052, 0.0, axis_z), STEEL, rotation=(0.0, 90.0, 0.0), segments=8)
    syringe.cylinder(0.0065, 0.0022, (-0.0665, 0.0, axis_z), STEEL, rotation=(0.0, 90.0, 0.0), segments=12)
    syringe.lathe([(0.0055, 0.0), (0.0035, 0.004), (0.002, 0.008), (0.0012, 0.012), (0.0, 0.012)], (0.028, 0.0, axis_z), STEEL, rotation=(0.0, 90.0, 0.0), segments=10)
    syringe.bar((0.039, 0.0, axis_z), (0.058, 0.0, axis_z - 0.001), 0.0005, STEEL_DARK, 5)
    glass = syringe.finish("jeringa", tb.material("vidrio", SYRINGE_GLASS), root)
    tb.collision_box("jeringa", (w + 0.006, 2.0 * d + 0.02, h), (0.002, -0.024, h / 2.0), root)
    tb.paint({steel: None, glass: None}, samples=10, ao=0.35, ao_distance=0.02, seed=931)
    return root


def build_antibiotics() -> bpy.types.Object:
    """Antibióticos: la caja de diez viales de polvo, abierta, con nueve dentro y uno
    tumbado fuera. Tapones de goma con la cápsula de aluminio."""
    root = tb.empty("antibioticos-fisico")
    w, d, h = 0.08, 0.04, 0.03
    mb = tb.MeshBuilder(seed=941)
    _box(mb, Vector((0.0, 0.0, 0.0)), (w, d, h), PAPER_WHITE, top=False)
    lift = 0.0004
    for side in (-1.0, 1.0):
        mb.box((w + 0.0002, lift, 0.008), (0.0, side * (d / 2.0 + lift / 2.0), 0.012), PHARMA_GREEN)
        mb.box((w + 0.0002, lift, 0.0025), (0.0, side * (d / 2.0 + lift / 2.0), 0.0205), PHARMA_RED)
    for k in range(2):
        mb.box((0.04 - k * 0.012, lift, 0.0016), (-0.012, -d / 2.0 - lift, 0.026 - k * 0.0034), INK)
    hinge = Vector((0.0, d / 2.0, h))
    mb.box((w - 0.001, 0.0012, d), hinge + Vector((0.0, 0.004, d / 2.0 - 0.002)), PAPER_WHITE, rotation=(-8.0, 0.0, 0.0))
    mb.box((w - 0.001, lift, 0.008), hinge + Vector((0.0, 0.0034, 0.014)), PHARMA_GREEN, rotation=(-8.0, 0.0, 0.0))
    box = mb.finish("caja", tb.material("carton", PAPER_WHITE), root)
    tb.stain(box, "#B8A884", amount=0.55, scale=45.0, coverage=0.3, seed=942)
    tb.stain(box, DIRT, amount=0.4, scale=70.0, coverage=0.22, seed=943)

    glass = tb.MeshBuilder(seed=944)
    caps = tb.MeshBuilder(seed=945)
    radius, height = 0.0068, 0.034
    bases = []
    for i in range(5):
        for j in range(2):
            if (i, j) == (4, 0):
                continue
            base = Vector((-w / 2.0 + 0.0085 + i * 0.0158, -d / 2.0 + 0.0105 + j * 0.019, 0.0012))
            _vial(glass, base, radius, height)
            bases.append((base, Vector((0.0, 0.0, 1.0))))
            caps.cylinder(radius * 0.68, height * 0.12, base + Vector((0.0, 0.0, height * 0.9)), CRIMP, segments=12)
            caps.cylinder(radius * 0.4, height * 0.04, base + Vector((0.0, 0.0, height * 0.97)), STOPPER, segments=10)
    lying = Vector((0.052, -0.03, radius))
    _vial(glass, lying, radius, height, rotation=(0.0, 90.0, 0.0))
    bases.append((lying, Vector((1.0, 0.0, 0.0))))
    caps.cylinder(radius * 0.68, height * 0.12, lying + Vector((height * 0.9, 0.0, 0.0)), CRIMP, rotation=(0.0, 90.0, 0.0), segments=12)
    caps.cylinder(radius * 0.4, height * 0.04, lying + Vector((height * 0.97, 0.0, 0.0)), STOPPER, rotation=(0.0, 90.0, 0.0), segments=10)
    vials = glass.finish("viales", tb.material("vidrio", VIAL_GLASS), root)

    def powder(co: Vector) -> str | None:
        for base, axis in bases:
            along = (co - base).dot(axis)
            if 0.0 <= along < height * 0.38 and ((co - base) - axis * along).length < radius + 0.001:
                return POWDER
        return None

    bb.recolor(vials, powder)
    cap_obj = caps.finish("capsulas", tb.material("metal", CRIMP), root)
    tb.collision_box("antibioticos", (0.105, 0.075, 0.07), (0.012, -0.005, 0.035), root)
    tb.paint({box: None, vials: None, cap_obj: None}, samples=10, ao=0.35, ao_distance=0.02, seed=941)
    return root


def build_antirad_pills() -> bpy.types.Object:
    """Pastillas antirradiación de la defensa civil: la cajita amarilla con el trébol
    negro y la raya roja, y una tira de aluminio con las pastillas al lado."""
    root = tb.empty("pastillas_antirradiacion-fisico")
    w, d, h = 0.07, 0.046, 0.018
    mb = tb.MeshBuilder(seed=951)
    mb.box((w, d, h), (0.0, 0.0, h / 2.0), CIVIL_YELLOW, bevel=0.0012, cuts=2)
    top = h + 0.0003
    center = Vector((-0.012, 0.002, top))
    for a0 in (60.0, 180.0, 300.0):
        mb.prism(bb.sector(0.0046, 0.0145, a0, a0 + 60.0, steps=6), 0.0005, center, INK)
    mb.cylinder(0.003, 0.0005, center, INK, segments=12)
    mb.box((w + 0.0002, 0.006, 0.0005), (0.0, -d / 2.0 + 0.0045, top), PHARMA_RED)
    for k in range(3):
        mb.box((0.018 - k * 0.004, 0.0016, 0.0005), (0.021, 0.012 - k * 0.005, top), INK)
    box = mb.finish("caja", tb.material("carton", CIVIL_YELLOW), root)
    tb.stain(box, "#8A7A4A", amount=0.55, scale=45.0, coverage=0.3, seed=952)
    tb.stain(box, DIRT, amount=0.4, scale=70.0, coverage=0.22, seed=953)

    strip = tb.MeshBuilder(seed=954)
    origin = Vector((0.006, -0.046, 0.0008))
    strip.box((0.058, 0.022, 0.0012), origin, FOIL, rotation=(0.0, 0.0, 8.0), bevel=0.0003)
    turn = math.radians(8.0)
    for i in range(5):
        local = Vector((-0.022 + i * 0.011, 0.0, 0.0))
        at = origin + Vector((local.x * math.cos(turn), local.x * math.sin(turn), 0.0006))
        strip.sphere(0.0042, at, FOIL, segments=10, scale=(1.0, 1.0, 0.45))
    strip.box((0.05, 0.003, 0.0003), origin + Vector((0.0, -0.008, 0.0006)), PHARMA_RED, rotation=(0.0, 0.0, 8.0))
    foil = strip.finish("tira", tb.material("metal", FOIL), root)
    tb.collision_box("pastillas", (0.075, 0.08, 0.02), (0.002, -0.014, 0.01), root)
    tb.paint({box: None, foil: None}, samples=10, ao=0.35, ao_distance=0.02, seed=951)
    return root


def build_army_kit() -> bpy.types.Object:
    """Botiquín individual del ejército: la cajita de plástico naranja con la tapa de
    bisagra, el cierre y la etiqueta en relieve. Rayada y desteñida."""
    root = tb.empty("botiquin_militar-fisico")
    w, d, h = 0.092, 0.106, 0.022
    mb = tb.MeshBuilder(seed=961)
    outline = bb.rounded_rect(w, d, 0.012, steps=4)
    mb.prism(outline, h, (0.0, 0.0, h / 2.0), ARMY_ORANGE, bevel=0.003, segments=2)
    # La junta de la tapa, el panel en relieve, la etiqueta y el cierre.
    seam = [Vector((x * 1.002, y * 1.002, 0.0145)) for x, y in outline]
    seam.append(seam[0])
    bb.strap(mb, seam, 0.0012, 0.0006, ARMY_ORANGE_DARK, center=(0.0, 0.0, 0.0145))
    mb.prism(bb.rounded_rect(0.068, 0.078, 0.008, steps=3), 0.0012, (0.0, 0.004, h + 0.0006), ARMY_ORANGE, bevel=0.0005)
    mb.box((0.04, 0.016, 0.0008), (0.0, 0.02, h + 0.0014), "#E0D6BC")
    for k in range(2):
        mb.box((0.028 - k * 0.008, 0.0016, 0.0004), (0.0, 0.023 - k * 0.0045, h + 0.002), INK)
    mb.box((0.016, 0.004, 0.012), (0.0, -d / 2.0 - 0.0012, 0.0145), ARMY_ORANGE_DARK, bevel=0.0012)
    for side in (-1.0, 1.0):
        mb.cylinder(0.003, 0.016, (side * 0.026, d / 2.0 + 0.0008, 0.0145), ARMY_ORANGE_DARK, rotation=(0.0, 90.0, 0.0), segments=10)
    kit = mb.finish("botiquin", tb.material("plastico", ARMY_ORANGE), root)
    tb.stain(kit, "#E0A060", amount=0.4, scale=30.0, coverage=0.35, seed=962)
    tb.stain(kit, DIRT, amount=0.6, scale=45.0, coverage=0.38, seed=963)
    tb.stain(kit, "#5A3A22", amount=0.5, scale=120.0, coverage=0.15, seed=964)
    tb.collision_box("botiquin", (w, d + 0.004, h + 0.002), (0.0, 0.0, (h + 0.002) / 2.0), root)
    tb.paint({kit: None}, samples=12, ao=0.35, ao_distance=0.025, seed=961)
    return root


def build_insulin() -> bpy.types.Object:
    """Insulina: la cajita blanca con la franja azul, abierta, con tres viales altos de
    cápsula naranja y etiqueta, y otro de pie al lado. Lo que más vale ahí arriba."""
    root = tb.empty("insulina-fisico")
    w, d, h = 0.062, 0.042, 0.032
    mb = tb.MeshBuilder(seed=971)
    _box(mb, Vector((0.0, 0.0, 0.0)), (w, d, h), PAPER_WHITE, top=False)
    lift = 0.0004
    for side in (-1.0, 1.0):
        mb.box((w + 0.0002, lift, 0.01), (0.0, side * (d / 2.0 + lift / 2.0), 0.013), INSULIN_BLUE)
        mb.box((lift, d + 0.0002, 0.01), (side * (w / 2.0 + lift / 2.0), 0.0, 0.013), INSULIN_BLUE)
    for k in range(2):
        mb.box((0.03 - k * 0.01, lift, 0.0016), (-0.01, -d / 2.0 - lift, 0.025 - k * 0.0034), INK)
    hinge = Vector((0.0, -d / 2.0, h))
    mb.box((w - 0.001, 0.0012, 0.022), hinge + Vector((0.0, -0.0105, 0.0035)), PAPER_WHITE, rotation=(70.0, 0.0, 0.0))
    box = mb.finish("caja", tb.material("carton", PAPER_WHITE), root)
    tb.stain(box, "#B8A884", amount=0.5, scale=45.0, coverage=0.28, seed=972)
    tb.stain(box, DIRT, amount=0.35, scale=70.0, coverage=0.2, seed=973)

    glass = tb.MeshBuilder(seed=974)
    parts = tb.MeshBuilder(seed=975)
    radius, height = 0.0068, 0.044
    spots = [Vector((-0.018, 0.004, 0.0012)), Vector((-0.002, 0.004, 0.0012)), Vector((0.014, 0.004, 0.0012)), Vector((0.05, -0.012, 0.0))]
    for base in spots:
        _vial(glass, base, radius, height)
        parts.cylinder(radius * 0.72, height * 0.13, base + Vector((0.0, 0.0, height * 0.9)), INSULIN_CAP, segments=12)
        parts.lathe([(0.0, 0.0), (radius * 0.72, 0.0), (radius * 0.6, 0.0015), (0.0, 0.0018)], base + Vector((0.0, 0.0, height * 0.965)), INSULIN_CAP, segments=12)
        bb.band(parts, radius + 0.0003, base.z + 0.008, base.z + 0.024, "#E6E0CC", center=(base.x, base.y, 0.0), start=-150.0, end=150.0, segments=14, rows=2)
        bb.band(parts, radius + 0.0005, base.z + 0.013, base.z + 0.017, INSULIN_BLUE, center=(base.x, base.y, 0.0), start=-140.0, end=140.0, segments=14)
    vials = glass.finish("viales", tb.material("vidrio", VIAL_GLASS), root)
    labels = parts.finish("capsulas", tb.material("plastico", INSULIN_CAP), root)
    tb.stain(labels, "#A89878", amount=0.4, scale=90.0, coverage=0.2, seed=976)
    tb.collision_box("insulina", (0.09, 0.07, 0.045), (0.012, -0.008, 0.0225), root)
    tb.paint({box: None, vials: None, labels: None}, samples=10, ao=0.35, ao_distance=0.02, seed=971)
    return root


def models() -> dict:
    return {
        "filtro": build_filter,
        "analgesicos": build_painkillers,
        "yodo": build_iodine,
        "jeringa": build_syringe,
        "antibioticos": build_antibiotics,
        "pastillas_antirradiacion": build_antirad_pills,
        "botiquin_militar": build_army_kit,
        "insulina": build_insulin,
    }
