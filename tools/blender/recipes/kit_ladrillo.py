"""Kit de arquitectura: la casa de ladrillo anterior a la revolución (el barrio de los
mercaderes de la ciudad vieja).

Una biblioteca, "kit_ladrillo", con los muros y la decoración de ladrillo visto. Los
huecos miden lo mismo que en kit_estalinka (en una planta de 3,4 m que Godot estira a
los 3,8 m de estas casas), así que las carpinterías, los interiores, los cortes y la
cubierta son los de la estalinka: las monta scripts/surface/kit_masonry.gd con el estilo
"prerrevolucion".

Lo que las distingue (sin copiar ninguna casa real): el ladrillo rojo sin revocar; los
dinteles de arco rebajado con su guardapolvo encima; en la planta noble, recercados de
ladrillo con un frontoncillo escalonado; lesenas en las esquinas y entre vanos; una
imposta de dentellones en cada forjado; la cornisa de hiladas en saledizo con su fila de
dentellones; y los bajos de tiendas con arcos rebajados sobre un zócalo revocado.

Coordenadas: las de tools/blender/kit_bpy.py.
"""

from __future__ import annotations

import math
import random

from mathutils import Vector

import kit_bpy as kit
import tumansk_bpy as tb

# Las medidas y los huecos de la estalinka (las carpinterías son las suyas).
W = 3.2
H = 3.4
T = 0.64
P = 0.6
BELOW = 1.0
GROUND = P + H
WINDOW = (0.9, 0.85, 2.3, 3.05)
YARD_WINDOW = (1.0, 0.85, 2.2, 2.95)
STAIR = (1.1, 1.1, 2.1, 2.5)
SHOP = (0.45, 0.75, 2.75, 3.55)
PORTAL = (0.85, 0.3, 2.35, 3.55)
LOW_WINDOW = (0.9, 1.45, 2.3, 3.45)
BACK_DOOR = (1.0, 0.15, 2.2, 2.4)
BACK_H = P + H / 2.0
ARCH = (0.2, 0.0, 3.0)

# Colores (sRGB): el ladrillo lo tiñe el ensamblador casa por casa.
BRICK = "#8E513F"
BRICK_DARK = "#753F2F"
BRICK_LIGHT = "#9C5D48"
STONE = "#B4AA93"
RENDER = "#5C524B"  # el zócalo revocado
DARK = "#121110"
SLAB_COLOR = "#7A7368"
BEAM = "#3A3028"


def _neighbours(z_range: tuple[float, float] = (0.0, H)) -> list:
    z0, z1 = z_range
    mb = tb.MeshBuilder(seed=1)
    for dx, dz in ((-W, 0.0), (W, 0.0), (0.0, z1 - z0), (0.0, -(z1 - z0))):
        mb.slab((dx, dx + W), (z0 + dz, z1 + dz), (0.0, T), BRICK, back=False)
    return [mb.finish("contexto_muros")]


def _frames(openings: list) -> list:
    mb = tb.MeshBuilder(seed=2)
    rng = random.Random(2)
    for opening, kind in openings:
        kit.window(mb, opening, kind, "intacta", rng, depth=0.2, wall=T)
    return [mb.finish("contexto_carpinteria")]


def _arch_band(mb: tb.MeshBuilder, x0: float, x1: float, z: float, rise: float, thickness: float, depth: float, color: str, *, y: float = 0.0) -> None:
    """Un arco rebajado de ladrillo a sardinel sobre un hueco: banda curva entre dos arcos."""
    steps = 12
    span = (x1 - x0) / 2.0
    xc = (x0 + x1) / 2.0
    lower = [(xc + span * math.cos(math.pi * k / steps), z + rise * math.sin(math.pi * k / steps)) for k in range(steps + 1)]
    upper = [(xc + (span + thickness * 0.5) * math.cos(math.pi * k / steps), z + thickness + (rise + thickness * 0.3) * math.sin(math.pi * k / steps)) for k in range(steps + 1)]
    outline = kit.ccw(lower + upper[::-1])
    mb.prism(outline, depth, (0.0, y - depth / 2.0, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.03)


def _lintel(mb: tb.MeshBuilder, opening: tuple, *, fancy: bool = False) -> None:
    """El dintel de arco rebajado (asoma un poco) y el guardapolvo encima, en saledizo."""
    x0, z0, x1, z1 = opening
    # El tímpano entre el hueco recto y el arco, del ladrillo oscuro de los dinteles.
    _arch_band(mb, x0 - 0.06, x1 + 0.06, z1, 0.16, 0.24, 0.06, BRICK_DARK)
    _arch_band(mb, x0 - 0.16, x1 + 0.16, z1 + 0.12, 0.2, 0.12, 0.1, BRICK_LIGHT)
    for x in (x0 - 0.22, x1 + 0.22):  # los arranques del guardapolvo
        mb.box((0.16, 0.1, 0.1), (x, -0.05, z1 + 0.17), BRICK_LIGHT)
    # Alféizar de piedra, con nieve, y el delantal de ladrillo debajo.
    with mb.material(1):
        mb.box((x1 - x0 + 0.3, 0.14, 0.08), ((x0 + x1) / 2.0, -0.07, z0 - 0.04), STONE, jitter=0.03)
    mb.box((x1 - x0 + 0.1, 0.06, 0.35), ((x0 + x1) / 2.0, -0.03, z0 - 0.27), BRICK_LIGHT)
    if fancy:
        # Recercado de ladrillo: dos columnillas y un frontoncillo de hiladas escalonadas.
        for x in (x0 - 0.13, x1 + 0.13):
            mb.box((0.14, 0.1, z1 - z0 + 0.1), (x, -0.05, (z0 + z1) / 2.0), BRICK_LIGHT, jitter=0.03)
        base = z1 + 0.36
        for k in range(4):
            half = (x1 - x0) / 2.0 + 0.35 - k * 0.24
            mb.box((half * 2.0, 0.12 - k * 0.01, 0.1), ((x0 + x1) / 2.0, -0.06, base + 0.1 * k), BRICK_LIGHT, jitter=0.02)


def _wall(lib: kit.KitLibrary, name: str, openings: list, seed: int, *, fancy: bool = False, z_range=(0.0, H), lintels: bool = True) -> None:
    mb = tb.MeshBuilder(seed=seed)
    holes = [o for o, _ in openings]
    mb.slab((0.0, W), z_range, (0.0, T), BRICK, holes=holes, step=0.6, jitter=0.03, back=False, ring=0.12)
    if lintels:
        for opening, _ in openings:
            _lintel(mb, opening, fancy=fancy)
    piece = mb.finish(name, kit.materials("ladrillo", "nevado"))
    lib.add(piece, _neighbours(z_range) + _frames(openings), seed=seed)


def build_walls(lib: kit.KitLibrary) -> None:
    _wall(lib, "ladrillo_ventana", [(WINDOW, "alta")], 11)
    _wall(lib, "ladrillo_ventana_frontoncillo", [(WINDOW, "alta")], 12, fancy=True)
    # Ciego: una ventana cegada, rehundida en el muro con su dintel.
    mb = tb.MeshBuilder(seed=13)
    niche = WINDOW
    mb.slab((0.0, W), (0.0, H), (0.0, T), BRICK, holes=[niche], step=0.6, jitter=0.03, back=False, ring=0.12)
    mb.box((niche[2] - niche[0], 0.04, niche[3] - niche[1]), ((niche[0] + niche[2]) / 2.0, 0.13, (niche[1] + niche[3]) / 2.0), BRICK_DARK)
    _lintel(mb, niche)
    lib.add(mb.finish("ladrillo_ciego", kit.materials("ladrillo", "nevado")), _neighbours(), seed=13)
    _wall(lib, "ladrillo_patio_ventana", [(YARD_WINDOW, "alta")], 14)
    _wall(lib, "ladrillo_patio_ciego", [], 15)
    _wall(lib, "ladrillo_patio_escalera", [(STAIR, "escalera")], 16)
    _wall(lib, "ladrillo_patio_remate", [], 17, z_range=(0.0, H / 2.0))
    mb = tb.MeshBuilder(seed=18)
    mb.slab((0.0, W), (P, BACK_H), (0.0, T), BRICK, holes=[BACK_DOOR], step=0.6, jitter=0.03, back=False, ring=0.1)
    with mb.material(2):
        mb.slab((0.0, W), (-BELOW, P), (-0.05, T), RENDER, holes=[BACK_DOOR], jitter=0.03, back=False)
    _arch_band(mb, BACK_DOOR[0] - 0.06, BACK_DOOR[2] + 0.06, BACK_DOOR[3], 0.14, 0.24, 0.06, BRICK_DARK)
    with mb.material(1):
        mb.box((BACK_DOOR[2] - BACK_DOOR[0] + 0.5, 0.9, 0.18), ((BACK_DOOR[0] + BACK_DOOR[2]) / 2.0, -0.45, 0.06), SLAB_COLOR, jitter=0.04)
    lib.add(mb.finish("ladrillo_patio_puerta", kit.materials("ladrillo", "nevado", "estuco")), _neighbours((0.0, BACK_H)), ground_z=0.0, seed=18)


def _ground(lib: kit.KitLibrary, name: str, opening: tuple | None, seed: int, *, steps: bool = False) -> None:
    """Los bajos: zócalo revocado y oscuro, el muro de ladrillo hasta la imposta y el hueco
    con su arco rebajado."""
    mb = tb.MeshBuilder(seed=seed)
    holes = [opening] if opening else []
    with mb.material(2):
        mb.slab((0.0, W), (-BELOW, P), (-0.06, T), RENDER, holes=[(a, b, c, min(d, P)) for a, b, c, d in holes if b < P], step=0.8, jitter=0.03, back=False)
    mb.slab((0.0, W), (P, GROUND), (0.0, T), BRICK, holes=[(a, max(b, P), c, d) for a, b, c, d in holes if d > P], step=0.6, jitter=0.03, back=False, ring=0.12)
    if opening:
        x0, z0, x1, z1 = opening
        _arch_band(mb, x0 - 0.08, x1 + 0.08, z1, 0.22, 0.3, 0.07, BRICK_DARK)
        with mb.material(1):
            mb.box((0.22, 0.1, 0.3), ((x0 + x1) / 2.0, -0.05, z1 + 0.32), STONE)  # clave
        if steps:
            with mb.material(1):
                for k in range(2):
                    mb.box((x1 - x0 + 0.8 - k * 0.3, 0.45 - k * 0.15, 0.15), ((x0 + x1) / 2.0, -0.22 + k * 0.075, 0.075 + k * 0.15), STONE, jitter=0.04)
    piece = mb.finish(name, kit.materials("ladrillo", "nevado", "estuco"))
    lib.add(piece, _neighbours((0.0, GROUND)), ground_z=0.0, seed=seed)


def build_ground(lib: kit.KitLibrary) -> None:
    _ground(lib, "ladrillo_bajo_escaparate", SHOP, 31)
    _ground(lib, "ladrillo_bajo_portal", PORTAL, 32, steps=True)
    _ground(lib, "ladrillo_bajo_ventana", LOW_WINDOW, 33)
    _ground(lib, "ladrillo_bajo_ciego", None, 34)
    # El arco del patio, de medio punto, con el túnel a oscuras.
    x0, spring, x1 = ARCH
    radius = (x1 - x0) / 2.0
    xc = (x0 + x1) / 2.0
    arc_base = spring + 2.55
    top = arc_base + radius
    mb = tb.MeshBuilder(seed=35)
    with mb.material(2):
        mb.slab((0.0, W), (-BELOW, P), (-0.06, T), RENDER, holes=[(x0, -BELOW, x1, P)], jitter=0.03, back=False)
    mb.slab((0.0, W), (P, GROUND), (0.0, T), BRICK, holes=[(x0, P, x1, top)], step=0.6, jitter=0.03, back=False)
    arc = [(xc + radius * math.cos(math.pi * k / 16), arc_base + radius * math.sin(math.pi * k / 16)) for k in range(16, -1, -1)]
    mb.prism(kit.ccw([(x1, arc_base), (x1, top), (x0, top), (x0, arc_base), *arc[1:-1]]), T, (0.0, T / 2.0, 0.0), BRICK, rotation=(90.0, 0.0, 0.0))
    _arch_band(mb, x0 - 0.05, x1 + 0.05, arc_base, radius, 0.3, 0.06, BRICK_DARK)
    with mb.material(3):
        mb.box((x1 - x0, 7.0, top + 0.15), (xc, T + 3.5, (top - 0.2) / 2.0), DARK)
    piece = mb.finish("ladrillo_bajo_arco", kit.materials("ladrillo", "nevado", "estuco", "interior"))
    lib.add(piece, _neighbours((0.0, GROUND)), ground_z=0.0, seed=35)


def build_mouldings(lib: kit.KitLibrary) -> None:
    """Imposta de dentellones, cornisa de hiladas en saledizo, lesenas y esquinas."""
    def dentils(mb: tb.MeshBuilder, x0: float, x1: float, z: float, depth: float) -> None:
        count = max(1, round((x1 - x0) / 0.26))
        for k in range(count):
            x = x0 + (x1 - x0) * (k + 0.5) / count
            mb.box((0.13, depth, 0.09), (x, -depth / 2.0, z), BRICK_LIGHT)

    mb = tb.MeshBuilder(seed=41)
    mb.box((W, 0.1, 0.16), (W / 2.0, -0.05, 0.12), BRICK_LIGHT, jitter=0.02)
    dentils(mb, 0.0, W, -0.0, 0.08)
    mb.box((W, 0.14, 0.08), (W / 2.0, -0.07, 0.24), BRICK_LIGHT, jitter=0.02)
    lib.add(mb.finish("ladrillo_imposta", kit.materials("ladrillo")), _neighbours(), seed=41)
    mb = tb.MeshBuilder(seed=42)
    mb.box((0.14, 0.14, 0.32), (-0.07, -0.07, 0.12), BRICK_LIGHT)
    lib.add(mb.finish("ladrillo_imposta_esquina", kit.materials("ladrillo")), [], seed=42)
    # Cornisa: friso de nichos, hiladas que salen y una fila de dentellones.
    mb = tb.MeshBuilder(seed=43)
    for k in range(3):  # nichos del friso
        x = W * (k + 0.5) / 3
        mb.box((0.62, 0.05, 0.3), (x, 0.02, 0.2), BRICK_DARK)
    mb.slab((0.0, W), (0.0, 0.42), (-0.03, 0.0), BRICK, holes=[(W * (k + 0.5) / 3 - 0.31, 0.05, W * (k + 0.5) / 3 + 0.31, 0.35) for k in range(3)], back=False)
    courses = [(0.42, 0.08), (0.5, 0.15), (0.58, 0.22)]
    for z, out in courses:
        mb.box((W, out, 0.08), (W / 2.0, -out / 2.0, z + 0.04), BRICK_LIGHT, jitter=0.02)
    dentils(mb, 0.0, W, 0.71, 0.3)
    for z, out in ((0.76, 0.38), (0.84, 0.46)):
        mb.box((W, out, 0.08), (W / 2.0, -out / 2.0, z + 0.04), BRICK_LIGHT, jitter=0.02)
    with mb.material(1):
        mb.box((W, 0.6, 0.03), (W / 2.0, -0.18, 0.935), kit.GALVANIZED, rotation=(-6.0, 0.0, 0.0))
    piece = mb.finish("ladrillo_cornisa", kit.materials("ladrillo", "nevado"))
    lib.add(piece, _neighbours(), seed=43)
    mb = tb.MeshBuilder(seed=44)
    for z, out in ((0.46, 0.15), (0.54, 0.22), (0.62, 0.3), (0.8, 0.38), (0.88, 0.46)):
        mb.box((out, out, 0.08), (-out / 2.0, -out / 2.0, z), BRICK_LIGHT)
    mb.box((0.2, 0.2, 0.42), (-0.06, -0.06, 0.21), BRICK)
    lib.add(mb.finish("ladrillo_cornisa_esquina", kit.materials("ladrillo")), [], seed=44)
    # Lesena entre vanos (centrada en la junta) y la de las esquinas, en las dos caras.
    mb = tb.MeshBuilder(seed=45)
    mb.box((0.52, 0.12, H), (0.0, -0.06, H / 2.0), BRICK_LIGHT, cuts=2, jitter=0.02)
    lib.add(mb.finish("ladrillo_lesena", kit.materials("ladrillo")), _neighbours(), seed=45)
    for name, z0, z1, seed in (("ladrillo_esquina", 0.0, H, 46), ("ladrillo_esquina_bajos", -BELOW, GROUND, 47)):
        mb = tb.MeshBuilder(seed=seed)
        mb.box((0.62, 0.12, z1 - z0), (0.25, -0.06, (z0 + z1) / 2.0), BRICK_LIGHT, cuts=2, jitter=0.02)
        mb.box((0.12, 0.62, z1 - z0), (-0.06, 0.25, (z0 + z1) / 2.0), BRICK_LIGHT, cuts=2, jitter=0.02)
        lib.add(mb.finish(name, kit.materials("ladrillo")), [], seed=seed)


def build_damage(lib: kit.KitLibrary) -> None:
    """Muñones de ladrillo y un hueco en la fachada."""
    stubs = {
        "a": ((1.4, 2.6), (0.4, 0.9), (0.3, 0.9)),
        "b": ((0.3, 0.8), (0.3, 0.85), (1.3, 2.4)),
        "c": ((0.1, 0.5), (0.05, 0.45), (0.1, 0.5)),
        "d": ((1.5, 2.8), (0.6, 0.9), (1.2, 2.2)),
    }
    x0, z0, x1, _ = WINDOW
    for index, (letter, (left, middle, right)) in enumerate(stubs.items()):
        seed = 611 + index
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        for (a, b), (low, high) in (((0.0, x0), left), ((x0, x1), middle), ((x1, W), right)):
            kit.broken_slab(mb, (a, b), 0.0, kit.broken_edge(a, b, low, high, rng), (0.0, T), BRICK)
        for _ in range(rng.randint(5, 8)):
            kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.6, 2.8), 0.1), rng.uniform(0.12, 0.3), BRICK, rng)
        for _ in range(2):
            start = Vector((rng.uniform(0.3, W - 0.3), T, rng.uniform(0.0, 0.3)))
            mb.box((0.18, 2.6, 0.22), (start.x, start.y + 1.1, start.z + 0.4), BEAM, rotation=(rng.uniform(10, 25), 0.0, rng.uniform(-15, 15)), jitter=0.08)
        lib.add(mb.finish(f"ladrillo_roto_{letter}", kit.materials("ladrillo")), _neighbours((0.0, 1.0)), ground_z=0.0, seed=seed)
    rng = random.Random(641)
    mb = tb.MeshBuilder(seed=641)
    left = [(rng.uniform(0.25, 0.65), H * k / 8) for k in range(9)]
    right = [(W - rng.uniform(0.25, 0.65), H * k / 8) for k in range(9)]
    for edge, side in ((left, 0.0), (right, W)):
        mb.prism(kit.ccw([(side, 0.0), *edge, (side, H)]), T, (0.0, T / 2.0, 0.0), BRICK, rotation=(90.0, 0.0, 0.0))
    with mb.material(1):
        kit.room(mb, (0.1, W - 0.1), (0.0, H - 0.3), (T, T + 3.6), kit.WALLPAPERS[1])
        mb.box((1.6, 0.6, 1.9), (2.2, T + 3.0, 0.95), "#2A221C", rotation=(0.0, 0.0, -8.0), jitter=0.06)
    with mb.material(2):
        mb.box((W - 0.3, 1.4, 0.05), (W / 2.0, T + 0.6, 0.02), "#2A2724")
        for _ in range(7):
            kit.chunk(mb, (rng.uniform(0.3, W - 0.3), rng.uniform(-0.2, T + 1.5), 0.08), rng.uniform(0.12, 0.3), BRICK, rng)
    lib.add(mb.finish("ladrillo_hueco", kit.materials("ladrillo", "interior", "nevado")), _neighbours(), samples=12, ao_distance=0.8, seed=641)


def build_kit() -> object:
    lib = kit.KitLibrary("kit_ladrillo", spacing=8.0)
    build_walls(lib)
    build_ground(lib)
    build_mouldings(lib)
    build_damage(lib)
    return lib.root


def models() -> dict:
    return {"kit_ladrillo": build_kit}
