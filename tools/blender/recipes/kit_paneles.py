"""Kit de arquitectura: los bloques de paneles (jrushchovka, bloque de 9 y torre de 16).

Una sola biblioteca, "kit_paneles", con todas las piezas. Godot monta cada bloque
del plano con ellas (scripts/surface/building_kit.gd); las medidas de aquí y las de
allí tienen que coincidir (lo comprueba tests/unit/test_building_kit.gd).

Las series reales que inspiran el kit (sin copiar ninguna): paneles de hormigón de
una habitación de ancho con las juntas selladas con masilla oscura, ventanas de
madera de doble hoja con ventanillo, balcones estrechos con barandilla de barrotes o
chapa ondulada (muchos acristalados por los vecinos), portales con marquesina y la
escalera iluminada por ventanas desfasadas media planta, zócalo con respiraderos del
sótano, cubierta plana con peto, antenas de televisión, salidas a la cubierta y, en
los bloques de 9, las casetas de los ascensores y la planta técnica.

Coordenadas: las de tools/blender/kit_bpy.py (x a lo largo de la fachada, z hacia
arriba, la cara exterior del muro en y = 0 y el muro hacia +y).
"""

from __future__ import annotations

import math
import random

import kit_bpy as kit
import tumansk_bpy as tb

# Medidas (las mismas que BuildingKit en Godot).
W = 3.2  # ancho de un vano: un panel por habitación
H = 2.8  # altura de una planta
T = 0.3  # espesor del panel
J = 0.03  # junta entre paneles
P = 0.9  # zócalo: del suelo a la primera planta
BELOW = 1.0  # lo que se entierran el zócalo y el portal (para las cuestas)
DEPTH = 0.1  # lo que se mete la carpintería desde la cara del muro
ROOM = 2.6  # fondo del falso interior
PARAPET = 0.6  # peto de la jrushchovka
TECH = 1.6  # planta técnica de los bloques altos
LOGGIA = 1.2  # fondo de las logias
SLAB = 0.22  # canto de los forjados

# Huecos (x0, z0, x1, z1) dentro de un vano.
WINDOW = (0.85, 0.85, 2.35, 2.3)
KITCHEN = (1.0, 0.85, 2.2, 2.3)
DOOR = (0.38, 0.05, 1.12, 2.3)
DOOR_WINDOW = (1.12, 0.85, 2.62, 2.3)
STAIR = (1.05, 0.9, 2.15, 2.0)
PORTAL = (0.95, 0.12, 2.25, 2.22)
PORTAL_H = P + H / 2.0  # el panel del portal llega hasta el primer descansillo
LOGGIA_OPEN = (0.3, 0.0, W - 0.3, H - 0.26)

# Colores (sRGB). El ensamblador tiñe cada bloque y cada panel por instancia.
PANEL = "#8C877E"
PANEL_INNER = "#7E7A72"
MASTIC = "#2C2926"
PLINTH = "#605C56"
SLAB_COLOR = "#706C65"
CONCRETE = "#7D7A73"
BRICK = "#7A4A3A"
DRIP = "#5F5850"
DARK = "#121110"
BENCH_WOOD = "#5B4634"
SIGN = "#2D4A8A"
SCREEN = "#B8B6AE"  # chapa de los balcones: blanca, la tiñe el ensamblador

WINDOW_STATES = ("intacta", "cortina", "rota", "tapiada", "plastico", "quemada", "vacia")
SHORT_STATES = ("intacta", "rota", "tapiada", "quemada", "vacia")


# --------------------------------------------------------------------------
# Muros
# --------------------------------------------------------------------------


def _panel(
    mb: tb.MeshBuilder,
    holes: list,
    z_range: tuple[float, float] = (0.0, H),
    *,
    back: bool = False,
    drips: list | None = None,
) -> None:
    """Un panel de hormigón con sus huecos y la junta de masilla alrededor.

    Cada vano lleva media junta por cada lado: los vecinos completan la otra mitad.
    Alrededor de cada hueco hay una fila de vértices cerca de la mocheta, para que su
    oclusión no manche medio panel, y cortes para los chorretones (``drips``).
    """
    # Sin bisel y con la masilla casi enrasada: la junta es una línea de color nítida.
    # Una ranura honda o un bisel dejan caras de menos de un píxel que el contorno de
    # tinta pilla a saltos, y de lejos las juntas salen punteadas.
    z0, z1 = z_range
    mb.slab(
        (J / 2.0, W - J / 2.0), (z0 + J / 2.0, z1 - J / 2.0), (0.0, T), PANEL,
        holes=holes, step=0.55, jitter=0.03, back=back, ring=0.1,
        extra_x=kit.drip_cuts(drips or []),
    )
    mb.slab((0.0, W), (z0, z1), (0.001, 0.06), MASTIC, holes=[(J / 2.0, z0 + J / 2.0, W - J / 2.0, z1 - J / 2.0)], back=False)


def _sill_drips(openings: list, rng: random.Random) -> list:
    """Los chorretones de óxido que bajan de los extremos de los alféizares de chapa."""
    result = []
    for (x0, z0, x1, _), kind in openings:
        if kind not in ("habitacion", "cocina", "escalera"):
            continue
        for x in (x0 - 0.012, x1 + 0.012):
            if rng.random() < 0.8:
                result.append((x, z0 - 0.03, rng.uniform(0.045, 0.075), rng.uniform(0.6, 1.4)))
    return result


def _neighbours(z_range: tuple[float, float] = (0.0, H)) -> list:
    """El contexto de un panel: los paneles lisos de al lado, de arriba y de abajo."""
    z0, z1 = z_range
    mb = tb.MeshBuilder(seed=1)
    for dx, dz in ((-W, 0.0), (W, 0.0), (0.0, z1 - z0), (0.0, -(z1 - z0))):
        mb.slab((dx + J / 2.0, dx + W - J / 2.0), (z0 + dz + J / 2.0, z1 + dz - J / 2.0), (0.0, T), PANEL, back=False)
    return [mb.finish("contexto_paneles")]


def _frame_context(openings: list[tuple[tuple[float, float, float, float], str]]) -> list:
    """Las carpinterías como contexto: oscurecen las mochetas como lo harán al montarlas."""
    mb = tb.MeshBuilder(seed=2)
    rng = random.Random(2)
    for opening, kind in openings:
        kit.window(mb, opening, kind, "intacta", rng, depth=DEPTH, wall=T)
    return [mb.finish("contexto_carpinteria")]


def _slab_context(z: float) -> list:
    """Un balcón encima (la losa de la planta de arriba)."""
    mb = tb.MeshBuilder(seed=3)
    mb.box((W - 0.24, 0.9, 0.13), (W / 2.0, -0.45, z - 0.095), SLAB_COLOR)
    return [mb.finish("contexto_balcon")]


def _wall(lib: kit.KitLibrary, name: str, openings: list, seed: int, *, balcony_above: bool = False) -> None:
    rng = random.Random(seed)
    mb = tb.MeshBuilder(seed=seed)
    drips = _sill_drips(openings, rng)
    _panel(mb, [o for o, _ in openings], drips=drips)
    piece = mb.finish(name, kit.materials("muro"))
    kit.drips(piece, drips)
    context = _neighbours() + _frame_context(openings)
    if balcony_above:
        context += _slab_context(H)
    lib.add(piece, context, alpha=kit.facade_faces, seed=seed)


def build_walls(lib: kit.KitLibrary) -> None:
    _wall(lib, "panel_ventana", [(WINDOW, "habitacion")], 11)
    _wall(lib, "panel_cocina", [(KITCHEN, "cocina")], 12)
    _wall(lib, "panel_balcon", [(DOOR, "puerta"), (DOOR_WINDOW, "habitacion")], 13, balcony_above=True)
    _wall(lib, "panel_escalera", [(STAIR, "escalera")], 14)
    _wall(lib, "panel_ciego", [], 15)

    # El portal: de la acera al primer descansillo, con la puerta abajo.
    mb = tb.MeshBuilder(seed=16)
    mb.slab((J / 2.0, W - J / 2.0), (-BELOW, PORTAL_H - J / 2.0), (0.0, T), PANEL, holes=[PORTAL], bevel=0.012, step=0.55, jitter=0.03, back=False)
    mb.slab((0.0, W), (-BELOW, PORTAL_H), (0.014, 0.06), MASTIC, holes=[(J / 2.0, -BELOW, W - J / 2.0, PORTAL_H - J / 2.0)], back=False)
    # La placa con el número del portal, junto a la puerta (el número lo pone Godot).
    mb.box((0.36, 0.02, 0.24), (2.62, -0.01, 1.95), SIGN, bevel=0.004)
    piece = mb.finish("panel_portal", kit.materials("muro"))
    lib.add(piece, _neighbours((0.0, PORTAL_H)), alpha=kit.facade_faces, ground_z=0.0, seed=16)

    # El remate de la escalera: media planta ciega bajo el peto.
    mb = tb.MeshBuilder(seed=17)
    _panel(mb, [], (0.0, H / 2.0))
    lib.add(mb.finish("panel_remate", kit.materials("muro")), _neighbours((0.0, H / 2.0)), alpha=kit.facade_faces, seed=17)


def build_loggia(lib: kit.KitLibrary) -> None:
    """La logia de los bloques altos: un balcón metido en la fachada, con la puerta y la
    ventana al fondo (donde van las carpinterías de "puerta_balcon", desplazadas)."""
    mb = tb.MeshBuilder(seed=18)
    lx0, lz0, lx1, lz1 = LOGGIA_OPEN
    _panel(mb, [LOGGIA_OPEN])
    # Paredes, suelo y techo de la logia.
    mb.box((0.12, LOGGIA - T + 0.02, lz1 - lz0), (lx0 + 0.06, (T + LOGGIA) / 2.0, (lz0 + lz1) / 2.0), PANEL_INNER, jitter=0.04, cuts=2)
    mb.box((0.12, LOGGIA - T + 0.02, lz1 - lz0), (lx1 - 0.06, (T + LOGGIA) / 2.0, (lz0 + lz1) / 2.0), PANEL_INNER, jitter=0.04, cuts=2)
    mb.box((lx1 - lx0, LOGGIA, 0.04), ((lx0 + lx1) / 2.0, LOGGIA / 2.0, lz0 - 0.02), SLAB_COLOR, cuts=2)
    mb.box((lx1 - lx0, LOGGIA, 0.04), ((lx0 + lx1) / 2.0, LOGGIA / 2.0, lz1 + 0.02), PANEL_INNER, cuts=2)
    # El fondo: un panel con la puerta y la ventana.
    mb.slab((lx0, lx1), (lz0, lz1), (LOGGIA, LOGGIA + T), PANEL_INNER, holes=[DOOR, DOOR_WINDOW], bevel=0.01, step=0.6, jitter=0.03, back=False)
    piece = mb.finish("panel_logia", kit.materials("muro"))
    frames = tb.MeshBuilder(seed=19)
    rng = random.Random(19)
    for opening, kind in ((DOOR, "puerta"), (DOOR_WINDOW, "habitacion")):
        kit.window(frames, opening, kind, "intacta", rng, depth=LOGGIA + DEPTH, wall=LOGGIA + T)
    lib.add(piece, [*_neighbours(), frames.finish("contexto_logia")], alpha=kit.facade_faces, seed=18)


def build_plinth(lib: kit.KitLibrary) -> None:
    """El zócalo, del suelo a la primera planta (y enterrado por si hay cuesta)."""
    for name, vent, seed in (("zocalo", False, 21), ("zocalo_respiradero", True, 22)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        holes = [(W / 2.0 - 0.18, 0.3, W / 2.0 + 0.18, 0.52)] if vent else []
        mb.slab((0.0, W), (-BELOW, P), (-0.05, T), PLINTH, holes=holes, bevel=0.015, step=0.6, jitter=0.03, back=False)
        # Llaga entre las piezas del zócalo, a mitad de vano.
        mb.box((0.012, 0.01, P + BELOW), (W / 2.0 + (0.9 if vent else 0.0), -0.052, (P - BELOW) / 2.0), MASTIC)
        if vent:
            with mb.material(1):
                mb.box((0.36, 0.5, 0.22), (W / 2.0, 0.5, 0.41), DARK)
            for k in range(3):
                if rng.random() < 0.7:
                    x = W / 2.0 - 0.09 + k * 0.09
                    mb.box((0.012, 0.012, 0.22), (x, 0.08, 0.41), kit.RUST, rotation=(0.0, rng.uniform(-8, 8), 0.0))
        piece = mb.finish(name, kit.materials("muro", "interior"))
        tb.stain(piece, "#3E3A35", amount=0.5, scale=1.8, coverage=0.4, seed=seed, stretch_z=0.4)
        lib.add(piece, [], ground_z=0.0, seed=seed)
    # Esquina: tapa el hueco entre los dos zócalos que sobresalen.
    mb = tb.MeshBuilder(seed=23)
    mb.box((0.05, 0.05, P + BELOW), (-0.025, -0.025, (P - BELOW) / 2.0), PLINTH, jitter=0.03)
    lib.add(mb.finish("esquina_zocalo", kit.materials("muro")), [], ground_z=0.0, seed=23)


def build_parapets(lib: kit.KitLibrary) -> None:
    """El peto de la cubierta (con su albardilla de chapa) y la planta técnica."""
    for name, height, vents, seed in (("peto", PARAPET, False, 31), ("peto_tecnico", TECH, True, 32)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        holes = [(0.7, 0.55, 1.25, 0.8), (1.95, 0.55, 2.5, 0.8)] if vents else []
        drips = [(rng.uniform(0.3, W - 0.3), height - 0.02, rng.uniform(0.04, 0.07), rng.uniform(0.3, 0.6)) for _ in range(2)]
        _panel(mb, holes, (0.0, height), back=True, drips=drips)
        if vents:
            with mb.material(1):
                for x0, z0, x1, z1 in holes:
                    mb.box((x1 - x0, 0.4, z1 - z0), ((x0 + x1) / 2.0, T + 0.2, (z0 + z1) / 2.0), DARK)
            for x0, z0, x1, z1 in holes:
                for k in range(4):
                    mb.box((x1 - x0, 0.015, 0.02), ((x0 + x1) / 2.0, 0.06, z0 + 0.04 + k * 0.06), kit.METAL, rotation=(-30.0, 0.0, 0.0))
        mb.box((W, T + 0.11, 0.035), (W / 2.0, T / 2.0 - 0.035, height + 0.0175), kit.GALVANIZED, jitter=0.04)
        mb.box((W, 0.012, 0.07), (W / 2.0, -0.09, height - 0.01), kit.GALVANIZED, jitter=0.04)
        piece = mb.finish(name, kit.materials("muro", "interior"))
        kit.drips(piece, drips, strength=0.4)
        tb.stain(piece, kit.RUST, amount=0.35, scale=2.5, coverage=0.3, seed=seed, stretch_z=0.2)
        lib.add(piece, _neighbours((0.0, height)), alpha=kit.facade_faces, seed=seed)
        # La esquina de la albardilla.
        mb = tb.MeshBuilder(seed=seed + 5)
        mb.box((0.11, 0.11, 0.035), (-0.055, -0.055, height + 0.0175), kit.GALVANIZED)
        lib.add(mb.finish(f"esquina_{name}", kit.materials("muro")), [], seed=seed + 5)


# --------------------------------------------------------------------------
# Carpinterías e interiores
# --------------------------------------------------------------------------


def build_windows(lib: kit.KitLibrary) -> None:
    """Cada hueco con cada estado. Se montan en el mismo origen que su panel."""
    groups = (
        ("ventana", [(WINDOW, "habitacion")], WINDOW_STATES),
        ("cocina", [(KITCHEN, "cocina")], SHORT_STATES),
        ("puerta_balcon", [(DOOR, "puerta"), (DOOR_WINDOW, "habitacion")], SHORT_STATES),
        ("escalera", [(STAIR, "escalera")], ("intacta", "rota", "quemada", "vacia")),
    )
    seed = 100
    for prefix, openings, states in groups:
        for state in states:
            seed += 1
            rng = random.Random(seed)
            mb = tb.MeshBuilder(seed=seed)
            for opening, kind in openings:
                kit.window(mb, opening, kind, state, rng, depth=DEPTH, wall=T)
            piece = mb.finish(f"{prefix}_{state}", kit.materials("nevado", "vidrio", "interior"))
            if state == "quemada":
                tb.stain(piece, kit.SOOT, amount=0.8, scale=4.0, coverage=0.6, seed=seed)
            mb_wall = tb.MeshBuilder(seed=seed)
            _panel(mb_wall, [o for o, _ in openings])
            lib.add(piece, [mb_wall.finish("contexto_muro")], samples=10, ao_distance=0.3, seed=seed)
    # Las puertas del portal.
    for state in ("cerrada", "abierta", "tapiada", "arrancada"):
        seed += 1
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        x0, z0, x1, z1 = PORTAL
        if state == "arrancada":
            kit.window(mb, PORTAL, "portal", "vacia", rng, depth=DEPTH, wall=T)
        else:
            kit.window(
                mb, PORTAL, "portal", "rota" if state == "abierta" else "intacta", rng,
                depth=DEPTH, wall=T, frame_color="#4A3A2E", sill=False, inner=False, open_sash=1,
            )
        if state == "tapiada":
            # Barricada: tablones y una puerta de armario clavada encima.
            kit.planks(mb, PORTAL, 0.0, rng, count=6, overhang=0.12)
            mb.box((0.6, 0.03, 1.5), ((x0 + x1) / 2.0 + 0.1, -0.06, z0 + 0.8), "#6E5A44", rotation=(0.0, 4.0, 0.0), bevel=0.008, jitter=0.06)
        # El vestíbulo a oscuras detrás, con el primer tramo de escalera.
        with mb.material(2):
            kit.room(mb, (x0 - 0.3, x1 + 0.3), (z0 - 0.12, 2.6), (T, T + 2.2), "#262320")
            for k in range(5):
                mb.box((x1 - x0 + 0.4, 0.28, 0.16), ((x0 + x1) / 2.0, T + 1.0 + k * 0.28, z0 + 0.08 + k * 0.16), "#2C2925")
        piece = mb.finish(f"puerta_portal_{state}", kit.materials("nevado", "vidrio", "interior"))
        mb_wall = tb.MeshBuilder(seed=seed)
        mb_wall.slab((J / 2.0, W - J / 2.0), (-BELOW, PORTAL_H), (0.0, T), PANEL, holes=[PORTAL], back=False)
        lib.add(piece, [mb_wall.finish("contexto_muro")], samples=10, ao_distance=0.4, ground_z=0.0, seed=seed)


def build_rooms(lib: kit.KitLibrary) -> None:
    """El falso interior que se ve por los huecos: una caja oscura por vano y planta."""
    for index, wallpaper in enumerate(kit.WALLPAPERS[:3]):
        seed = 200 + index
        mb = tb.MeshBuilder(seed=seed)
        kit.room(mb, (0.12, W - 0.12), (0.0, H - 0.25), (T, T + ROOM), wallpaper)
        # Lo que se adivina dentro: un armario, una lámpara colgando, una puerta al pasillo.
        if index == 0:
            mb.box((0.9, 0.55, 1.9), (0.7, T + ROOM - 0.3, 0.95), "#2A221C", jitter=0.06)
        elif index == 1:
            mb.box((0.8, 0.02, 2.0), (W - 0.9, T + ROOM - 0.01, 1.0), "#171513")
            mb.bar((W / 2.0, T + 1.2, H - 0.25), (W / 2.0, T + 1.2, H - 0.7), 0.006, "#141312", 4)
            mb.cylinder(0.14, 0.1, (W / 2.0, T + 1.2, H - 0.75), "#3A3530", radius_top=0.05, segments=8)
        else:
            mb.box((1.4, 0.6, 0.45), (W / 2.0 + 0.4, T + ROOM - 0.35, 0.22), "#2D2620", jitter=0.06)
            mb.box((0.5, 0.08, 0.6), (0.5, T + 0.1, 0.35), "#3A3632")  # el radiador bajo la ventana
        piece = mb.finish(f"habitacion_{'abc'[index]}", kit.materials("interior"))
        lib.add(piece, [], samples=10, ao=0.6, ao_distance=0.8, cavity_dark=0.2, seed=seed)
    # Quemada: paredes negras, el suelo lleno de restos.
    rng = random.Random(210)
    mb = tb.MeshBuilder(seed=210)
    kit.room(mb, (0.12, W - 0.12), (0.0, H - 0.25), (T, T + ROOM), "#1A1715")
    for _ in range(6):
        kit.chunk(mb, (rng.uniform(0.4, W - 0.4), T + rng.uniform(0.3, ROOM - 0.3), 0.08), rng.uniform(0.15, 0.4), rng.choice(("#1E1B19", "#2A2522", kit.CHAR)), rng)
    lib.add(mb.finish("habitacion_quemada", kit.materials("interior")), [], samples=10, ao=0.6, ao_distance=0.8, seed=210)
    # La caja de la escalera, vista por sus ventanas: un tramo, el descansillo y la barandilla.
    mb = tb.MeshBuilder(seed=211)
    kit.room(mb, (0.1, W - 0.1), (-0.4, H + 0.2), (T, T + 2.8), "#33302B")
    landing = 0.45
    mb.box((W - 0.2, 1.2, 0.18), (W / 2.0, T + 0.6, landing - 0.09), "#3B3833")
    for k in range(9):
        mb.box((1.15, 0.26, 0.15), (W / 2.0 - 0.6, T + 1.2 + k * 0.17, landing + 0.075 + k * 0.155), "#36332E")
    mb.bar((W / 2.0, T + 1.1, landing + 0.95), (W / 2.0, T + 2.7, landing + 2.35), 0.02, "#22201D", 6)
    lib.add(mb.finish("escalera_interior", kit.materials("interior")), [], samples=10, ao=0.6, ao_distance=0.8, seed=211)


# --------------------------------------------------------------------------
# Balcones y logias
# --------------------------------------------------------------------------


def _balcony_slab(mb: tb.MeshBuilder, rng: random.Random) -> None:
    mb.box((W - 0.24, 0.9, 0.13), (W / 2.0, -0.45, -0.095), SLAB_COLOR, bevel=0.02, cuts=2, jitter=0.05)


def _side_rails(mb: tb.MeshBuilder, color: str, *, bars: bool) -> None:
    for x in (0.16, W - 0.16):
        mb.box((0.04, 0.84, 0.04), (x, -0.44, 1.0), color)
        mb.box((0.03, 0.84, 0.03), (x, -0.44, 0.06), color)
        if bars:
            for k in range(1, 4):
                mb.box((0.02, 0.02, 0.9), (x, -0.86 + k * 0.21, 0.53), color)


def build_balconies(lib: kit.KitLibrary) -> None:
    """Balcones de losa estrecha. Se colocan en el suelo de cada planta (salvo la baja)."""
    railing = "#6A716C"  # pintadas por los vecinos, ya desconchadas
    # De barrotes.
    rng = random.Random(301)
    mb = tb.MeshBuilder(seed=301)
    _balcony_slab(mb, rng)
    kit.railing(mb, (0.14, W - 0.14), -0.86, (-0.03, 1.02), railing)
    _side_rails(mb, railing, bars=True)
    piece = mb.finish("balcon_reja", kit.materials("nevado"))
    tb.stain(piece, kit.RUST, amount=0.7, scale=3.0, coverage=0.4, seed=301)
    lib.add(piece, _neighbours(), seed=301)
    # Con chapa: el bastidor; la chapa es otra pieza para teñirla.
    mb = tb.MeshBuilder(seed=302)
    _balcony_slab(mb, rng)
    for x in (0.16, W / 2.0, W - 0.16):
        mb.box((0.04, 0.04, 1.05), (x, -0.86, 0.5), railing)
    mb.box((W - 0.28, 0.06, 0.05), (W / 2.0, -0.86, 1.0), railing)
    _side_rails(mb, railing, bars=False)
    piece = mb.finish("balcon_chapa", kit.materials("nevado"))
    tb.stain(piece, kit.RUST, amount=0.6, scale=3.0, coverage=0.35, seed=302)
    lib.add(piece, _neighbours(), seed=302)
    mb = tb.MeshBuilder(seed=303)
    kit.corrugated(mb, (0.14, W - 0.14), -0.9, (0.0, 0.96), SCREEN)
    for x in (0.12, W - 0.12):
        mb.box((0.008, 0.82, 0.96), (x, -0.45, 0.48), SCREEN, jitter=0.03)
    piece = mb.finish("chapa_balcon", kit.materials("nevado"))
    tb.stain(piece, "#5E5B55", amount=0.5, scale=2.0, coverage=0.4, seed=303, stretch_z=0.25)
    lib.add(piece, [], samples=8, seed=303)
    # Acristalado por los vecinos: madera, cristal y un tejadillo de chapa.
    rng = random.Random(304)
    mb = tb.MeshBuilder(seed=304)
    _balcony_slab(mb, rng)
    for k in range(9):
        mb.box(((W - 0.3) / 9.0 - 0.01, 0.025, 0.98), (0.15 + (W - 0.3) * (k + 0.5) / 9.0, -0.88, 0.47), rng.choice(kit.PLANKS), rotation=(0.0, rng.uniform(-1.5, 1.5), 0.0), jitter=0.08)
    top = H - 0.2
    mb.box((W - 0.26, 0.07, 0.06), (W / 2.0, -0.86, 1.0), kit.FRAME_WOOD)
    mb.box((W - 0.26, 0.07, 0.06), (W / 2.0, -0.86, top), kit.FRAME_WOOD)
    panes = 4
    for k in range(panes + 1):
        x = 0.15 + (W - 0.3) * k / panes
        mb.box((0.06, 0.07, top - 1.0), (x, -0.86, (top + 1.0) / 2.0), kit.FRAME_WOOD)
    for x in (0.15, W - 0.15):
        mb.box((0.06, 0.84, 0.06), (x, -0.44, top), kit.FRAME_WOOD)
        mb.box((0.03, 0.82, 0.95), (x, -0.45, 0.48), rng.choice(kit.PLANKS))
    mb.box((W - 0.1, 1.02, 0.03), (W / 2.0, -0.5, top + 0.06), kit.GALVANIZED, rotation=(4.0, 0.0, 0.0), jitter=0.05)
    with mb.material(1):
        mb.box((W - 0.3, 0.006, top - 1.04), (W / 2.0, -0.85, (top + 1.02) / 2.0), kit.GLASS)
        for x in (0.15, W - 0.15):
            mb.box((0.006, 0.8, top - 1.04), (x, -0.45, (top + 1.02) / 2.0), kit.GLASS)
    piece = mb.finish("balcon_acristalado", kit.materials("nevado", "vidrio"))
    tb.stain(piece, "#3B342C", amount=0.5, scale=2.5, coverage=0.35, seed=304)
    lib.add(piece, _neighbours(), seed=304)
    # Caído: cuelga de la armadura, girado hacia abajo.
    rng = random.Random(305)
    mb = tb.MeshBuilder(seed=305)
    before = set(mb.bm.faces)
    _balcony_slab(mb, rng)
    kit.railing(mb, (0.14, W - 0.14), -0.86, (-0.03, 1.02), railing)
    _side_rails(mb, railing, bars=True)
    moved = [f for f in mb.bm.faces if f not in before]
    kit.transform_faces(moved, kit.hinge((0.0, 0.0, -0.03), "X", rng.uniform(38.0, 55.0)))
    for _ in range(7):
        kit.rebar(mb, (rng.uniform(0.3, W - 0.3), -0.02, -0.08), (0.0, -1.0, -0.4), rng.uniform(0.2, 0.45), rng)
    piece = mb.finish("balcon_caido", kit.materials("nevado"))
    tb.stain(piece, kit.RUST, amount=0.8, scale=3.0, coverage=0.45, seed=305)
    lib.add(piece, _neighbours(), seed=305)
    # Arrancado: queda un muñón de losa y las varillas dobladas.
    rng = random.Random(306)
    mb = tb.MeshBuilder(seed=306)
    edge = kit.broken_edge(0.12, W - 0.12, 0.06, 0.22, rng)
    outline = kit.ccw([(0.12, 0.0), *[(x, -d) for x, d in edge], (W - 0.12, 0.0)])
    mb.prism(outline, 0.13, (0.0, 0.0, -0.095), SLAB_COLOR, jitter=0.05)
    for _ in range(9):
        kit.rebar(mb, (rng.uniform(0.25, W - 0.25), -0.12, -0.08), (0.0, -1.0, -rng.uniform(0.1, 0.9)), rng.uniform(0.15, 0.4), rng)
    piece = mb.finish("balcon_arrancado", kit.materials("nevado"))
    lib.add(piece, _neighbours(), seed=306)
    # Los trastos de los balcones.
    for name, seed in (("trastos_a", 307), ("trastos_b", 308)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        if name == "trastos_a":
            for k in range(2):  # esquís apoyados en la pared
                mb.box((0.07, 0.02, 1.7), (0.4 + k * 0.1, -0.08, 0.85), rng.choice(("#5A3A2A", "#2F4A5A")), rotation=(-6.0, 0.0, 4.0 + k * 3.0))
            mb.box((0.45, 0.35, 0.3), (W - 0.6, -0.3, 0.15), "#6B5A45", rotation=(0.0, 0.0, 12.0), bevel=0.02)
            for k in range(4):  # tarros de conservas
                mb.cylinder(0.05, 0.14, (W - 1.2 + k * 0.12, -0.5, 0.07), "#3F4A44", segments=8)
            mb.bar((0.3, -0.75, 1.55), (W - 0.3, -0.75, 1.55), 0.005, "#222222", 4)  # tendedero
            mb.box((0.5, 0.01, 0.6), (1.3, -0.75, 1.25), "#7C7466", rotation=(0.0, 0.0, 3.0), cuts=2)
        else:
            mb.box((0.9, 0.5, 0.12), (1.0, -0.4, 0.06), "#4A3B2E", rotation=(0.0, 0.0, -6.0), bevel=0.01)  # trineo
            mb.box((0.4, 0.4, 0.42), (2.2, -0.35, 0.21), "#3A3A36", bevel=0.03)  # un televisor viejo
            mb.box((0.3, 0.02, 0.24), (2.2, -0.56, 0.24), "#1E2124")
            mb.cylinder(0.12, 0.3, (2.8, -0.3, 0.15), "#5A4A3A", radius_top=0.15, segments=10)  # maceta seca
            for k in range(3):
                mb.bar((2.8 + k * 0.03 - 0.03, -0.3, 0.3), (2.75 + k * 0.06 - 0.06, -0.32, 0.65), 0.006, "#3A3222", 4)
        piece = mb.finish(name, kit.materials("nevado"))
        lib.add(piece, _neighbours(), samples=8, seed=seed)


def build_loggia_fronts(lib: kit.KitLibrary) -> None:
    """El antepecho de la logia (se tiñe por instancia) y la logia acristalada."""
    lx0, lz0, lx1, lz1 = LOGGIA_OPEN
    rng = random.Random(311)
    mb = tb.MeshBuilder(seed=311)
    mb.slab((lx0 + 0.005, lx1 - 0.005), (lz0, 1.05), (0.0, 0.09), SCREEN, bevel=0.01, step=0.5, jitter=0.03)
    for k in range(1, 10):  # estrías verticales del hormigón
        mb.box((0.025, 0.01, 0.9), (lx0 + (lx1 - lx0) * k / 10.0, -0.004, 0.53), "#A9A79F")
    mb.box((lx1 - lx0 + 0.02, 0.14, 0.04), ((lx0 + lx1) / 2.0, 0.03, 1.07), kit.GALVANIZED)
    piece = mb.finish("antepecho_logia", kit.materials("nevado"))
    tb.stain(piece, "#5A5751", amount=0.5, scale=2.0, coverage=0.4, seed=311, stretch_z=0.2)
    lib.add(piece, _neighbours(), seed=311)
    # Roto: un trozo de antepecho y las varillas al aire.
    mb = tb.MeshBuilder(seed=312)
    edge = kit.broken_edge(lx0 + 0.005, lx0 + 1.1, 0.2, 0.9, rng)
    kit.broken_slab(mb, (lx0 + 0.005, lx0 + 1.1), lz0, edge, (0.0, 0.09), SCREEN)
    for _ in range(6):
        kit.rebar(mb, (rng.uniform(lx0 + 1.2, lx1 - 0.2), 0.04, 0.02), (0.0, -0.3, 1.0), rng.uniform(0.2, 0.5), rng)
    lib.add(mb.finish("antepecho_roto", kit.materials("nevado")), _neighbours(), seed=312)
    # Acristalada: carpintería de madera sobre el antepecho, hasta el techo.
    mb = tb.MeshBuilder(seed=313)
    top = lz1 - 0.02
    mb.box((lx1 - lx0, 0.07, 0.06), ((lx0 + lx1) / 2.0, 0.04, 1.1), kit.FRAME_WOOD)
    mb.box((lx1 - lx0, 0.07, 0.06), ((lx0 + lx1) / 2.0, 0.04, top - 0.03), kit.FRAME_WOOD)
    for k in range(5):
        mb.box((0.06, 0.07, top - 1.1), (lx0 + 0.03 + (lx1 - lx0 - 0.06) * k / 4.0, 0.04, (top + 1.1) / 2.0), kit.FRAME_WOOD)
    with mb.material(1):
        mb.box((lx1 - lx0, 0.006, top - 1.13), ((lx0 + lx1) / 2.0, 0.05, (top + 1.1) / 2.0), kit.GLASS)
    piece = mb.finish("logia_acristalada", kit.materials("nevado", "vidrio"))
    lib.add(piece, _neighbours(), seed=313)


# --------------------------------------------------------------------------
# Portal
# --------------------------------------------------------------------------


def build_entrance(lib: kit.KitLibrary) -> None:
    """Marquesina, escalones y el banco de las vecinas. Origen: el del panel del portal."""
    x0, _, x1, _ = PORTAL
    canopy_z = PORTAL_H
    rng = random.Random(401)
    mb = tb.MeshBuilder(seed=401)
    mb.box((x1 - x0 + 0.9, 1.35, 0.12), ((x0 + x1) / 2.0, -0.675, canopy_z + 0.03), CONCRETE, bevel=0.02, cuts=2, jitter=0.04)
    mb.box((x1 - x0 + 0.92, 0.03, 0.18), ((x0 + x1) / 2.0, -1.36, canopy_z + 0.0), kit.GALVANIZED, jitter=0.05)
    for x in (x0 - 0.35, x1 + 0.35):
        mb.bar((x, -1.25, canopy_z + 0.09), (x, -0.02, canopy_z + 1.15), 0.014, kit.METAL, 6)
    # La lámpara del portal, con su rejilla, y el cable.
    mb.cylinder(0.08, 0.12, ((x0 + x1) / 2.0, -0.12, canopy_z - 0.1), "#3A3E40", segments=10)
    mb.sphere(0.07, ((x0 + x1) / 2.0, -0.12, canopy_z - 0.17), "#4E504C", segments=10)
    for k in range(4):
        angle = k * math.pi / 2.0
        mb.bar(((x0 + x1) / 2.0 + 0.07 * math.cos(angle), -0.12 + 0.07 * math.sin(angle), canopy_z - 0.16), ((x0 + x1) / 2.0, -0.12, canopy_z - 0.26), 0.004, kit.METAL, 4)
    piece = mb.finish("marquesina", kit.materials("nevado"))
    tb.stain(piece, kit.RUST, amount=0.5, scale=2.5, coverage=0.35, seed=401, stretch_z=0.3)
    lib.add(piece, _neighbours((0.0, PORTAL_H)), seed=401)
    # Caída: la losa se ha soltado de un tirante y cuelga sobre la puerta.
    mb = tb.MeshBuilder(seed=402)
    before = set(mb.bm.faces)
    mb.box((x1 - x0 + 0.9, 1.35, 0.12), ((x0 + x1) / 2.0, -0.675, canopy_z + 0.03), CONCRETE, bevel=0.02, cuts=2, jitter=0.04)
    moved = [f for f in mb.bm.faces if f not in before]
    kit.transform_faces(moved, kit.hinge((x1 + 0.45, -0.02, canopy_z + 0.03), "Y", -28.0))
    mb.bar((x1 + 0.35, -1.25, canopy_z + 0.09), (x1 + 0.35, -0.02, canopy_z + 1.15), 0.014, kit.METAL, 6)
    mb.bar((x0 - 0.35, -0.02, canopy_z + 1.15), (x0 - 0.2, -0.5, canopy_z + 0.5), 0.014, kit.METAL, 6)
    for _ in range(5):
        kit.chunk(mb, ((x0 + x1) / 2.0 + rng.uniform(-1.0, 1.0), -rng.uniform(0.6, 1.8), 0.08), rng.uniform(0.12, 0.3), CONCRETE, rng)
    piece = mb.finish("marquesina_caida", kit.materials("nevado"))
    lib.add(piece, _neighbours((0.0, PORTAL_H)), ground_z=0.0, seed=402)
    # Escalones: la meseta y un peldaño, de hormigón gastado.
    mb = tb.MeshBuilder(seed=403)
    mb.box((x1 - x0 + 0.9, 1.3, 0.32), ((x0 + x1) / 2.0, -0.65, -0.04), CONCRETE, bevel=0.02, cuts=2, jitter=0.04)
    mb.box((x1 - x0 + 0.5, 0.32, 0.18), ((x0 + x1) / 2.0, -1.46, -0.03), CONCRETE, bevel=0.02, jitter=0.05)
    kit.chunk(mb, (x1 + 0.2, -1.2, 0.12), 0.14, CONCRETE, rng)
    piece = mb.finish("escalones", kit.materials("nevado"))
    tb.stain(piece, "#4A4741", amount=0.5, scale=2.0, coverage=0.4, seed=403)
    lib.add(piece, _neighbours((0.0, PORTAL_H)), ground_z=0.0, seed=403)
    # El banco junto al portal: patas de hormigón y tablas.
    mb = tb.MeshBuilder(seed=404)
    for x in (-0.65, 0.65):
        mb.box((0.12, 0.42, 0.4), (x, 0.0, 0.2), CONCRETE, bevel=0.02, jitter=0.05)
    for y, z, tilt in ((-0.12, 0.43, 0.0), (0.06, 0.43, 0.0), (0.2, 0.75, -14.0)):
        mb.box((1.6, 0.1, 0.035), (0.0, y, z), BENCH_WOOD, rotation=(tilt, rng.uniform(-1, 1), 0.0), bevel=0.008, jitter=0.1)
    for x in (-0.6, 0.6):
        mb.box((0.05, 0.05, 0.4), (x, 0.22, 0.6), kit.METAL, rotation=(-14.0, 0.0, 0.0))
    piece = mb.finish("banco_portal", kit.materials("nevado"))
    lib.add(piece, [], ground_z=0.0, seed=404)


# --------------------------------------------------------------------------
# Cubierta
# --------------------------------------------------------------------------


def _antenna(mb: tb.MeshBuilder, rng: random.Random, height: float, elements: int) -> None:
    """Antena de televisión: mástil con vientos y un dipolo con sus directores."""
    mb.box((0.3, 0.3, 0.12), (0.0, 0.0, 0.06), CONCRETE, bevel=0.01)
    top = (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), height)
    mb.bar((0.0, 0.0, 0.1), top, 0.022, kit.METAL, 8)
    boom = 1.3
    yaw = rng.uniform(0.0, math.pi)
    direction = (math.cos(yaw), math.sin(yaw))
    mb.bar((top[0] - direction[0] * boom * 0.3, top[1] - direction[1] * boom * 0.3, height - 0.1), (top[0] + direction[0] * boom * 0.7, top[1] + direction[1] * boom * 0.7, height - 0.1), 0.012, kit.METAL, 6)
    for k in range(elements):
        t = -0.3 + k / max(1, elements - 1)
        length = 0.9 - 0.35 * k / max(1, elements - 1)
        cx = top[0] + direction[0] * boom * t
        cy = top[1] + direction[1] * boom * t
        mb.bar((cx - direction[1] * length / 2.0, cy + direction[0] * length / 2.0, height - 0.1), (cx + direction[1] * length / 2.0, cy - direction[0] * length / 2.0, height - 0.1), 0.006, kit.METAL, 4)
    for k in range(3):
        angle = k * math.tau / 3.0 + 0.4
        mb.bar((top[0], top[1], height * 0.75), (math.cos(angle) * 1.4, math.sin(angle) * 1.4, 0.02), 0.004, "#2A2A2A", 4)
    # El cable de bajada, colgando.
    points = [(top[0], top[1], height - 0.15), (0.25, 0.1, height * 0.5), (0.5, 0.2, 0.05), (1.4, 0.4, 0.02)]
    mb.tube(tb.smooth_path(points, steps=3), 0.006, "#1C1C1C", segments=4)


def build_roof(lib: kit.KitLibrary) -> None:
    """Lo que hay sobre la cubierta. Origen: el centro de la base, sobre la cubierta."""
    for name, height, elements, seed in (("antena_a", 3.4, 6, 501), ("antena_b", 2.6, 4, 502)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        _antenna(mb, rng, height, elements)
        piece = mb.finish(name, kit.materials("nevado"))
        tb.stain(piece, kit.RUST, amount=0.7, scale=4.0, coverage=0.4, seed=seed)
        lib.add(piece, [], samples=6, ground_z=0.0, seed=seed)
    # Caída: el mástil doblado sobre la cubierta.
    rng = random.Random(503)
    mb = tb.MeshBuilder(seed=503)
    mb.box((0.3, 0.3, 0.12), (0.0, 0.0, 0.06), CONCRETE, bevel=0.01)
    points = [(0.0, 0.0, 0.1), (0.05, 0.0, 0.5), (0.6, 0.1, 0.35), (2.2, 0.3, 0.06), (3.0, 0.35, 0.05)]
    mb.tube(tb.smooth_path(points, steps=3), 0.022, kit.METAL, segments=8)
    mb.bar((2.4, -0.5, 0.05), (2.6, 0.9, 0.08), 0.012, kit.METAL, 6)
    for k in range(4):
        mb.bar((2.3 + k * 0.2, -0.3, 0.05), (2.5 + k * 0.2, 0.6, 0.06 + k * 0.03), 0.006, kit.METAL, 4)
    piece = mb.finish("antena_caida", kit.materials("nevado"))
    tb.stain(piece, kit.RUST, amount=0.8, scale=4.0, coverage=0.5, seed=503)
    lib.add(piece, [], samples=6, ground_z=0.0, seed=503)
    # Cabeza de ventilación de ladrillo, con su sombrerete.
    mb = tb.MeshBuilder(seed=504)
    rng = random.Random(504)
    with mb.material(1):
        mb.box((1.1, 0.5, 0.9), (0.0, 0.0, 0.45), BRICK, bevel=0.02, cuts=2, jitter=0.05)
    for x in (-0.3, 0.0, 0.3):
        with mb.material(2):
            mb.box((0.14, 0.52, 0.2), (x, 0.0, 0.72), DARK)
    for dx in (-0.45, 0.45):
        for dy in (-0.18, 0.18):
            mb.box((0.06, 0.06, 0.2), (dx, dy, 1.0), CONCRETE)
    mb.box((1.35, 0.75, 0.08), (0.0, 0.0, 1.14), CONCRETE, bevel=0.015, jitter=0.05)
    piece = mb.finish("ventilacion", kit.materials("nevado", "ladrillo", "interior"))
    tb.stain(piece, "#2A2522", amount=0.6, scale=3.0, coverage=0.45, seed=504, stretch_z=0.3)
    lib.add(piece, [], ground_z=0.0, seed=504)
    # Salida a la cubierta: una caseta de hormigón con la puerta de chapa entreabierta.
    mb = tb.MeshBuilder(seed=505)
    mb.box((1.6, 2.0, 1.9), (0.0, 0.0, 0.95), PANEL, bevel=0.015, cuts=3, jitter=0.03)
    mb.box((0.94, 0.06, 1.82), (0.0, -1.0, 0.91), "#3E4244", bevel=0.008)  # cerco de la puerta
    with mb.material(1):
        mb.box((0.8, 0.02, 1.72), (0.0, -1.025, 0.88), DARK)  # el hueco a oscuras
    door = mb.box((0.8, 0.04, 1.72), (0.4, -1.04, 0.88), "#4A4F50", bevel=0.006, jitter=0.05)
    kit.transform_faces(door, kit.hinge((0.4, -1.04, 0.0), "Z", 28.0))
    mb.box((1.9, 2.3, 0.1), (0.0, 0.0, 1.95), CONCRETE, rotation=(-4.0, 0.0, 0.0), bevel=0.015, jitter=0.04)
    piece = mb.finish("salida_cubierta", kit.materials("muro", "interior"))
    tb.stain(piece, kit.RUST, amount=0.5, scale=2.0, coverage=0.3, seed=505)
    lib.add(piece, [], ground_z=0.0, seed=505)
    # Caseta de los ascensores de los bloques altos: puerta de chapa, rejilla y escalerilla.
    mb = tb.MeshBuilder(seed=506)
    mb.box((3.0, 4.2, 2.7), (0.0, 0.0, 1.35), PANEL, bevel=0.015, cuts=4, jitter=0.03)
    mb.box((1.02, 0.06, 2.06), (-0.6, -2.1, 1.03), "#3E4244", bevel=0.008)
    mb.box((0.9, 0.05, 1.98), (-0.6, -2.13, 1.0), "#4F5456", bevel=0.006, jitter=0.05)
    with mb.material(1):
        mb.box((0.6, 0.02, 0.5), (0.8, -2.105, 2.0), DARK)
    for k in range(5):
        mb.box((0.56, 0.012, 0.03), (0.8, -2.13, 1.8 + k * 0.09), kit.METAL, rotation=(-35.0, 0.0, 0.0))
    for k in range(7):
        mb.box((0.42, 0.03, 0.03), (1.0, 2.13, 0.3 + k * 0.33), kit.METAL)
    for x in (0.8, 1.2):
        mb.box((0.03, 0.03, 2.5), (x, 2.13, 1.25), kit.METAL)
    mb.box((3.3, 4.5, 0.12), (0.0, 0.0, 2.76), CONCRETE, bevel=0.02, jitter=0.04)
    piece = mb.finish("caseta_ascensor", kit.materials("muro", "interior"))
    tb.stain(piece, kit.RUST, amount=0.45, scale=1.5, coverage=0.3, seed=506, stretch_z=0.2)
    lib.add(piece, [], ground_z=0.0, seed=506)


# --------------------------------------------------------------------------
# Daños
# --------------------------------------------------------------------------


def _ragged_column(mb: tb.MeshBuilder, x_edge: float, inner: float, z_range: tuple[float, float], rng: random.Random, side: float) -> None:
    """Un resto de panel en el borde del vano, con el canto roto hacia el hueco."""
    z0, z1 = z_range
    steps = 8
    edge = [(x_edge + side * rng.uniform(inner * 0.3, inner), z0 + (z1 - z0) * k / steps) for k in range(steps + 1)]
    outline = kit.ccw([(x_edge, z0), *edge, (x_edge, z1)])
    mb.prism(outline, T, (0.0, T / 2.0, 0.0), PANEL, rotation=(90.0, 0.0, 0.0), jitter=0.04)


def build_damage(lib: kit.KitLibrary) -> None:
    """Paneles caídos, muñones de las plantas hundidas y el corte de un bloque partido."""
    # Panel caído: el hueco a la habitación, los restos del panel y las varillas.
    rng = random.Random(601)
    mb = tb.MeshBuilder(seed=601)
    mb.slab((0.0, W), (0.0, H), (0.014, 0.06), MASTIC, holes=[(J / 2.0, J / 2.0, W - J / 2.0, H - J / 2.0)], back=False)
    _ragged_column(mb, J / 2.0, 0.4, (J / 2.0, H - J / 2.0), rng, 1.0)
    _ragged_column(mb, W - J / 2.0, 0.35, (J / 2.0, H - J / 2.0), rng, -1.0)
    kit.broken_slab(mb, (0.4, W - 0.4), J / 2.0, kit.broken_edge(0.4, W - 0.4, 0.15, 0.55, rng), (0.0, T), PANEL)
    mb.box((W, 0.4, SLAB), (W / 2.0, 0.2, -SLAB / 2.0 + 0.02), SLAB_COLOR, jitter=0.05)
    for _ in range(9):
        side = rng.choice((0.35, W - 0.35))
        kit.rebar(mb, (side + rng.uniform(-0.1, 0.1), 0.05, rng.uniform(0.3, H - 0.3)), (W / 2.0 - side, -0.5, rng.uniform(-0.4, 0.4)), rng.uniform(0.2, 0.45), rng)
    # La habitación al aire: papel pintado, un tabique, un armario volcado y nieve en el suelo.
    with mb.material(1):
        kit.room(mb, (0.06, W - 0.06), (0.0, H - 0.25), (T, T + 3.4), kit.WALLPAPERS[3])
        mb.box((0.1, 1.6, H - 0.25), (W * 0.62, T + 2.6, (H - 0.25) / 2.0), "#3B3530")
        mb.box((1.7, 0.6, 0.9), (1.0, T + 1.3, 0.35), "#2E241C", rotation=(0.0, 72.0, 15.0), jitter=0.06)
    with mb.material(2):
        mb.box((W - 0.2, 1.4, 0.05), (W / 2.0, T + 0.6, 0.02), "#2A2724")
        for _ in range(7):
            kit.chunk(mb, (rng.uniform(0.3, W - 0.3), T + rng.uniform(0.1, 1.6), 0.08), rng.uniform(0.12, 0.35), rng.choice((CONCRETE, PANEL, "#5B5650")), rng)
    piece = mb.finish("panel_caido", kit.materials("muro", "interior", "nevado"))
    lib.add(piece, _neighbours(), alpha=kit.facade_faces, samples=12, ao_distance=0.8, seed=601)
    # Muñones: lo que queda de una planta hundida encima de la última que sigue en pie.
    # Cada variante deja una silueta distinta (los pilares entre ventanas aguantan más que
    # los antepechos): alturas (mín, máx) del pilar izquierdo, del antepecho y del derecho.
    stubs = {
        "a": ((1.3, 2.3), (0.3, 0.8), (0.2, 0.7), False),
        "b": ((0.2, 0.6), (0.25, 0.75), (1.2, 2.2), False),
        "c": ((0.1, 0.45), (0.08, 0.4), (0.1, 0.45), True),
        "d": ((0.35, 0.85), (0.45, 0.85), (0.3, 0.8), False),
        "e": ((1.4, 2.4), (0.5, 0.85), (1.1, 2.0), False),
        "f": ((0.02, 0.25), (0.02, 0.2), (0.02, 0.25), False),
    }
    x0, z0, x1, _ = WINDOW
    for index, (letter, (left, middle, right, fallen)) in enumerate(stubs.items()):
        seed = 611 + index
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        kit.broken_slab(mb, (J / 2.0, x0), J / 2.0, kit.broken_edge(J / 2.0, x0, *left, rng), (0.0, T), PANEL)
        kit.broken_slab(mb, (x0, x1), J / 2.0, kit.broken_edge(x0, x1, *middle, rng), (0.0, T), PANEL)
        kit.broken_slab(mb, (x1, W - J / 2.0), J / 2.0, kit.broken_edge(x1, W - J / 2.0, *right, rng), (0.0, T), PANEL)
        if fallen:
            # Un panel entero, caído hacia dentro y apoyado en los escombros.
            mb.box((W * 0.7, T, 1.6), (W * 0.5, 1.4, 0.6), PANEL, rotation=(62.0, 4.0, 0.0), jitter=0.04)
        mb.slab((0.0, W), (0.0, 0.3), (0.001, 0.06), MASTIC, holes=[(J / 2.0, J / 2.0, W - J / 2.0, 0.3)], back=False)
        bars = 14 if letter == "f" else 6
        for _ in range(bars):
            top = max(left[1], middle[1], right[1]) * 0.5
            kit.rebar(mb, (rng.uniform(0.2, W - 0.2), T / 2.0, rng.uniform(0.0, top)), (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 1.0), rng.uniform(0.25, 0.7), rng)
        # Cascotes sobre el forjado.
        for _ in range(rng.randint(4, 7)):
            kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.4, 2.4), 0.1), rng.uniform(0.18, 0.45), rng.choice((CONCRETE, PANEL, "#5B5650")), rng)
        piece = mb.finish(f"panel_roto_{letter}", kit.materials("muro"))
        lib.add(piece, _neighbours((0.0, 1.0)), alpha=kit.facade_faces, ground_z=0.0, seed=seed)
    # El peto roto (sin albardilla) y el corte de un bloque partido.
    rng = random.Random(621)
    mb = tb.MeshBuilder(seed=621)
    kit.broken_slab(mb, (J / 2.0, W - J / 2.0), 0.0, kit.broken_edge(J / 2.0, W - J / 2.0, 0.05, PARAPET, rng), (0.0, T), PANEL)
    for _ in range(4):
        kit.rebar(mb, (rng.uniform(0.2, W - 0.2), T / 2.0, 0.2), (0.0, rng.uniform(-0.4, 0.4), 1.0), rng.uniform(0.2, 0.4), rng)
    lib.add(mb.finish("peto_roto", kit.materials("muro")), _neighbours((0.0, PARAPET)), alpha=kit.facade_faces, seed=621)
    for index, seed in enumerate((631, 632, 633)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        # El forjado cortado, con el canto mellado y las varillas, y las habitaciones abiertas.
        edge = kit.broken_edge(0.0, W, 0.0, 0.35, rng)
        outline = kit.ccw([(0.0, 2.6), (W, 2.6), *[(x, d) for x, d in reversed(edge)]])
        mb.prism(outline, SLAB, (0.0, 0.0, -SLAB / 2.0), SLAB_COLOR, jitter=0.05)
        for _ in range(5):
            kit.rebar(mb, (rng.uniform(0.1, W - 0.1), rng.uniform(0.0, 0.3), -0.1), (0.0, -1.0, rng.uniform(-0.6, 0.2)), rng.uniform(0.2, 0.5), rng)
        if index < 2:
            with mb.material(1):
                wall_y = rng.uniform(1.8, 2.5)
                kit.room(mb, (0.0, W), (0.0, H - SLAB), (0.3, wall_y), kit.WALLPAPERS[index])
                if rng.random() < 0.8:
                    x = rng.uniform(0.6, W - 0.6)
                    mb.box((0.1, wall_y - 0.3, H - SLAB), (x, 0.3 + (wall_y - 0.3) / 2.0, (H - SLAB) / 2.0), kit.WALLPAPERS[(index + 1) % 4])
                    mb.box((0.8, 0.03, 2.05), (x + 0.5, wall_y - 0.02, 1.02), "#151413")
            with mb.material(2):
                for _ in range(4):
                    kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.2, 1.4), 0.08), rng.uniform(0.1, 0.3), rng.choice((CONCRETE, PANEL)), rng)
        else:
            # Lo más alto del corte: tabiques rotos y el forjado al aire, con escombros.
            with mb.material(1):
                kit.broken_slab(mb, (0.0, W), 0.0, kit.broken_edge(0.0, W, 0.1, 1.2, rng), (2.2, 2.32), kit.WALLPAPERS[2])
            with mb.material(2):
                for _ in range(8):
                    kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.2, 2.2), 0.1), rng.uniform(0.15, 0.4), rng.choice((CONCRETE, PANEL, "#5B5650")), rng)
        piece = mb.finish(f"corte_{'abc'[index]}" if index < 2 else "corte_roto", kit.materials("muro", "interior", "nevado"))
        lib.add(piece, [], samples=10, ao_distance=0.8, seed=seed)


def build_kit() -> object:
    lib = kit.KitLibrary("kit_paneles")
    build_walls(lib)
    build_loggia(lib)
    build_plinth(lib)
    build_parapets(lib)
    build_windows(lib)
    build_rooms(lib)
    build_balconies(lib)
    build_loggia_fronts(lib)
    build_entrance(lib)
    build_roof(lib)
    build_damage(lib)
    return lib.root


def models() -> dict:
    return {"kit_paneles": build_kit}
