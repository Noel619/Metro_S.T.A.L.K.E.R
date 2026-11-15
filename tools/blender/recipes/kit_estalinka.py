"""Kit de arquitectura: las casas estalinistas (la estalinka y la casa obrera baja).

Una biblioteca, "kit_estalinka". Las monta scripts/surface/kit_masonry.gd, que sigue
cualquier huella del plano (rectas, curvas alrededor de la plaza, en L, recortadas).

Lo que hace estalinista a una casa de Tumansk (sin copiar ninguna real): muros de
ladrillo de 64 cm revocados en ocre, con los detalles en un tono más claro; bajos
almohadillados sobre un zócalo de granito, con escaparates, portales con su recercado
y algún arco al patio; una imposta encima de los bajos; ventanas altas con recercado,
algunas con cornisilla o frontón; pilastras de orden gigante; balcones de balaustres
en los vanos principales; una cornisa grande con canecillos y una cubierta de chapa a
cuatro aguas con buhardillas y chimeneas. La fachada del patio es sencilla: revoque
liso, ventanas sin adornos, la escalera de servicio con sus ventanas desfasadas y la
puerta trasera. El desgaste se lleva el revoque alrededor de los huecos y deja ver el
ladrillo (lo pinta el shader del material "estuco").

Coordenadas: las de tools/blender/kit_bpy.py (x a lo largo de la fachada, z hacia
arriba, la cara exterior del muro en y = 0 y el muro hacia +y).
"""

from __future__ import annotations

import math
import random

from mathutils import Vector

import kit_bpy as kit
import tumansk_bpy as tb

# Medidas (las mismas que KitMasonry en Godot).
W = 3.2  # vano
H = 3.4  # planta
T = 0.64  # muro de ladrillo revocado
P = 0.6  # zócalo de granito: del suelo a la planta baja
BELOW = 1.0
GROUND = P + H  # los bajos van del suelo a la imposta
DEPTH = 0.2  # retranqueo de las carpinterías (muros gruesos: mochetas hondas)
ROOM = 3.0
SLAB = 0.3
CORNICE = 0.75  # vuelo de la cornisa
CORNICE_H = 0.72

# Huecos (x0, z0, x1, z1).
WINDOW = (0.9, 0.85, 2.3, 3.05)  # ventana alta de las plantas
DOOR = (0.95, 0.05, 2.25, 2.95)  # puerta de balcón
YARD_WINDOW = (1.0, 0.85, 2.2, 2.95)  # ventana del patio, sin adornos
STAIR = (1.1, 1.1, 2.1, 2.5)  # ventana de la escalera de servicio (panel desfasado)
SHOP = (0.45, 0.75, 2.75, 3.55)  # escaparate (los bajos van desde el suelo)
PORTAL = (0.85, 0.3, 2.35, 3.55)  # portal de la escalera
LOW_WINDOW = (0.9, 1.45, 2.3, 3.45)  # ventana de los bajos
BACK_DOOR = (1.0, 0.15, 2.2, 2.4)  # puerta trasera (patio)
BACK_H = P + H / 2.0  # la escalera de servicio: panel de la puerta hasta el descansillo
ARCH = (0.2, 0.0, 3.0)  # arco del patio: x0, arranque (z), x1; radio = mitad del ancho

# Colores (sRGB). El ensamblador tiñe cada casa (ocre, salmón, crema, gris…).
PLASTER = "#B7A486"
DETAIL = "#D2C6AC"  # recercados, cornisas, pilastras: más claros, como en las de verdad
RUSTIC = "#A8987E"
GRANITE = "#5F5551"
GRANITE_DARK = "#4A4240"
YARD = "#A99A80"  # revoque del patio, más pobre
BRICK = "#7C4C3A"
MOULD_SHADOW = "#9A8B70"
SLAB_COLOR = "#7A7368"
DARK = "#121110"
BEAM = "#3A3028"

WINDOW_STATES = ("intacta", "cortina", "rota", "tapiada", "plastico", "quemada", "vacia")
SHORT_STATES = ("intacta", "rota", "tapiada", "quemada", "vacia")


# --------------------------------------------------------------------------
# Máscara del revoque y contexto
# --------------------------------------------------------------------------


def wear_mask(openings: list, *, bottom: float | None = None, reach: float = 1.15):
    """Dónde se cae antes el revoque (el alfa del color): junto a los huecos y, en los
    bajos, cerca del suelo (``bottom``), donde sube la humedad.

    Solo en la cara del muro (y = 0): los recercados y las cornisas aguantan.
    """

    def mask(position: Vector, normal: Vector) -> float:
        if normal.y > -0.9 or position.y > 0.004:
            return 0.0
        x, z = position.x, position.z
        near = 0.0
        for x0, z0, x1, z1 in openings:
            dx = max(x0 - x, 0.0, x - x1)
            dz = max(z0 - z, 0.0, z - z1)
            near = max(near, 1.0 - math.hypot(dx, dz) / reach)
        low = 0.0 if bottom is None else max(0.0, 1.0 - (z - bottom) / 1.4) * 0.7
        return min(1.0, 0.15 + 0.85 * max(near, low))

    return mask


def _neighbours(z_range: tuple[float, float] = (0.0, H)) -> list:
    """El contexto de un vano: los muros de al lado, de arriba y de abajo."""
    z0, z1 = z_range
    mb = tb.MeshBuilder(seed=1)
    for dx, dz in ((-W, 0.0), (W, 0.0), (0.0, z1 - z0), (0.0, -(z1 - z0))):
        mb.slab((dx, dx + W), (z0 + dz, z1 + dz), (0.0, T), PLASTER, back=False)
    return [mb.finish("contexto_muros")]


def _frames(openings: list) -> list:
    mb = tb.MeshBuilder(seed=2)
    rng = random.Random(2)
    for opening, kind in openings:
        kit.window(mb, opening, kind, "intacta", rng, depth=DEPTH, wall=T)
    return [mb.finish("contexto_carpinteria")]


# --------------------------------------------------------------------------
# Adornos
# --------------------------------------------------------------------------


def _surround(mb: tb.MeshBuilder, opening: tuple, *, width: float = 0.15, depth: float = 0.085) -> None:
    """Recercado: el marco de molduras alrededor de un hueco, algo más claro que el muro.

    Las molduras sobresalen más que en la realidad: con 4 cm, su canto ocupa menos de un
    píxel a veinte metros y el contorno de tinta lo dibujaría a trozos."""
    x0, z0, x1, z1 = opening
    mb.slab((x0 - width, x1 + width), (z0 - (0.0 if z0 < 0.1 else width), z1 + width), (-depth, 0.0), DETAIL, holes=[opening], jitter=0.02, back=False)
    # Orejetas: el recercado se ensancha arriba, a la manera clásica.
    for side in (-1.0, 1.0):
        x = (x0 - width - 0.05) if side < 0 else (x1 + width + 0.05)
        mb.box((0.1, depth, 0.16), (x, -depth / 2.0, z1 + width - 0.08), DETAIL)


def _sill(mb: tb.MeshBuilder, opening: tuple) -> None:
    """Alféizar moldurado bajo una ventana (dos escalones de molduras)."""
    x0, z0, x1, _ = opening
    mb.box((x1 - x0 + 0.5, 0.13, 0.09), ((x0 + x1) / 2.0, -0.065, z0 - 0.17), DETAIL, jitter=0.02)
    mb.box((x1 - x0 + 0.3, 0.08, 0.07), ((x0 + x1) / 2.0, -0.04, z0 - 0.25), MOULD_SHADOW, jitter=0.02)
    for side in (-1.0, 1.0):  # ménsulas bajo el alféizar
        x = (x0 + 0.1) if side < 0 else (x1 - 0.1)
        mb.box((0.1, 0.1, 0.22), (x, -0.05, z0 - 0.4), DETAIL)


def _cornice_above(mb: tb.MeshBuilder, opening: tuple) -> None:
    """Cornisilla (sandrik) recta sobre una ventana, con su friso."""
    x0, _, x1, z1 = opening
    mb.box((x1 - x0 + 0.2, 0.05, 0.14), ((x0 + x1) / 2.0, -0.025, z1 + 0.2), DETAIL)
    mb.box((x1 - x0 + 0.55, 0.18, 0.1), ((x0 + x1) / 2.0, -0.09, z1 + 0.32), DETAIL, jitter=0.02)


def _pediment(mb: tb.MeshBuilder, opening: tuple) -> None:
    """Frontón triangular sobre una ventana principal, sobre dos ménsulas."""
    x0, _, x1, z1 = opening
    base = z1 + 0.2
    rise = 0.42
    left, right = x0 - 0.3, x1 + 0.3
    middle = (left + right) / 2.0
    outline = [(left, base), (right, base), (middle, base + rise)]
    mb.prism(kit.ccw(outline), 0.1, (0.0, -0.05, 0.0), DETAIL, rotation=(90.0, 0.0, 0.0), jitter=0.02)
    inner = [(left + 0.22, base + 0.05), (right - 0.22, base + 0.05), (middle, base + rise - 0.12)]
    mb.prism(kit.ccw(inner), 0.02, (0.0, -0.11, 0.0), MOULD_SHADOW, rotation=(90.0, 0.0, 0.0))
    mb.box((right - left + 0.06, 0.16, 0.09), (middle, -0.08, base - 0.02), DETAIL)
    for x in (x0 - 0.12, x1 + 0.12):
        mb.box((0.12, 0.13, 0.32), (x, -0.065, base - 0.2), DETAIL)


# --------------------------------------------------------------------------
# Muros de las plantas
# --------------------------------------------------------------------------


def _wall_piece(lib: kit.KitLibrary, name: str, openings: list, seed: int, *, extras=(), color: str = PLASTER, z_range=(0.0, H), drips: bool = True) -> None:
    rng = random.Random(seed)
    mb = tb.MeshBuilder(seed=seed)
    holes = [o for o, _ in openings]
    sources = []
    if drips:
        for (x0, z0, x1, _), _kind in openings:
            if z0 > 0.3:
                for x in (x0 + 0.05, x1 - 0.05):
                    if rng.random() < 0.7:
                        sources.append((x, z0 - 0.3, rng.uniform(0.05, 0.09), rng.uniform(0.6, 1.5)))
    mb.slab((0.0, W), z_range, (0.0, T), color, holes=holes, step=0.6, jitter=0.03, back=False, ring=0.12, extra_x=kit.drip_cuts(sources))
    for extra in extras:
        extra(mb)
    piece = mb.finish(name, kit.materials("estuco"))
    kit.drips(piece, sources, color="#6E6250", strength=0.4)
    lib.add(piece, _neighbours(z_range) + _frames(openings), alpha=wear_mask(holes), seed=seed)


def build_walls(lib: kit.KitLibrary) -> None:
    """Los vanos de las plantas: calle (con recercados) y patio (lisos)."""
    window = [(WINDOW, "alta")]
    _wall_piece(lib, "estuco_ventana", window, 11, extras=[lambda mb: _surround(mb, WINDOW), lambda mb: _sill(mb, WINDOW)])
    _wall_piece(lib, "estuco_ventana_cornisa", window, 12, extras=[lambda mb: _surround(mb, WINDOW), lambda mb: _sill(mb, WINDOW), lambda mb: _cornice_above(mb, WINDOW)])
    _wall_piece(lib, "estuco_ventana_fronton", window, 13, extras=[lambda mb: _surround(mb, WINDOW), lambda mb: _sill(mb, WINDOW), lambda mb: _pediment(mb, WINDOW)])
    _wall_piece(lib, "estuco_balcon", [(DOOR, "puerta")], 14, extras=[lambda mb: _surround(mb, DOOR), lambda mb: _cornice_above(mb, DOOR)])

    # Ciego: un panel rehundido con su moldura, para que el muro no quede desnudo.
    def blind_panel(mb: tb.MeshBuilder) -> None:
        mb.slab((0.75, 2.45), (0.75, 2.95), (-0.08, 0.0), DETAIL, holes=[(0.92, 0.92, 2.28, 2.78)], back=False)

    _wall_piece(lib, "estuco_ciego", [], 15, extras=[blind_panel])
    _wall_piece(lib, "patio_ventana", [(YARD_WINDOW, "alta")], 16, color=YARD)
    _wall_piece(lib, "patio_ciego", [], 17, color=YARD)
    # La escalera de servicio del patio: panel desfasado media planta, como en los bloques.
    _wall_piece(lib, "patio_escalera", [(STAIR, "escalera")], 18, color=YARD)
    _wall_piece(lib, "patio_remate", [], 19, color=YARD, z_range=(0.0, H / 2.0))
    mb = tb.MeshBuilder(seed=20)
    mb.slab((0.0, W), (-BELOW, BACK_H), (0.0, T), YARD, holes=[BACK_DOOR], step=0.6, jitter=0.03, back=False, ring=0.1)
    mb.slab((0.0, W), (-BELOW, P), (-0.05, 0.0), GRANITE_DARK, holes=[BACK_DOOR], jitter=0.03, back=False)
    mb.box((BACK_DOOR[2] - BACK_DOOR[0] + 0.5, 0.9, 0.18), ((BACK_DOOR[0] + BACK_DOOR[2]) / 2.0, -0.45, 0.06), SLAB_COLOR, jitter=0.04)
    piece = mb.finish("patio_puerta", kit.materials("estuco"))
    lib.add(piece, _neighbours((0.0, BACK_H)), alpha=wear_mask([BACK_DOOR], bottom=0.0), ground_z=0.0, seed=20)


# --------------------------------------------------------------------------
# Bajos: almohadillado sobre granito
# --------------------------------------------------------------------------


def _ground_piece(lib: kit.KitLibrary, name: str, opening: tuple | None, seed: int, extras=()) -> None:
    mb = tb.MeshBuilder(seed=seed)
    holes = [opening] if opening else []
    # Zócalo de granito y, encima, las bandas del almohadillado hasta la imposta.
    granite_holes = [(a, b, c, min(d, P)) for a, b, c, d in holes if b < P]
    mb.slab((0.0, W), (-BELOW, P), (-0.08, T), GRANITE, holes=granite_holes, step=0.8, jitter=0.03, back=False)
    if not granite_holes:
        mb.box((W, 0.1, 0.06), (W / 2.0, -0.05, P + 0.03), GRANITE_DARK)
    kit.banded_wall(mb, (0.0, W), (P, GROUND), (0.0, T), RUSTIC, holes=[(a, max(b, P), c, d) for a, b, c, d in holes if d > P])
    for extra in extras:
        extra(mb)
    piece = mb.finish(name, kit.materials("estuco"))
    lib.add(piece, _neighbours((0.0, GROUND)), alpha=wear_mask(holes, bottom=P), ground_z=0.0, seed=seed)


def build_ground_floor(lib: kit.KitLibrary) -> None:
    def shop_frame(mb: tb.MeshBuilder) -> None:
        x0, z0, x1, z1 = SHOP
        mb.slab((x0 - 0.12, x1 + 0.12), (z0 - 0.05, z1 + 0.12), (-0.05, 0.0), GRANITE_DARK, holes=[SHOP], back=False)
        # El rótulo encima (el texto lo pondrá Godot): una tabla de chapa pintada.
        mb.box((x1 - x0 + 0.1, 0.04, 0.32), ((x0 + x1) / 2.0, -0.07, z1 + 0.32), "#5B4E3E")

    def portal_frame(mb: tb.MeshBuilder) -> None:
        x0, z0, x1, z1 = PORTAL
        for x in (x0 - 0.2, x1 + 0.2):
            mb.box((0.3, 0.14, z1 - z0 + 0.3), (x, -0.07, (z0 + z1) / 2.0 + 0.05), DETAIL, jitter=0.02)
        mb.box((x1 - x0 + 0.95, 0.24, 0.16), ((x0 + x1) / 2.0, -0.12, z1 + 0.3), DETAIL, jitter=0.02)
        mb.box((x1 - x0 + 0.6, 0.1, 0.22), ((x0 + x1) / 2.0, -0.05, z1 + 0.12), DETAIL)
        # Escalones de granito hasta la puerta.
        for k in range(2):
            mb.box((x1 - x0 + 0.9 - k * 0.3, 0.45 - k * 0.15, 0.15), ((x0 + x1) / 2.0, -0.22 + k * 0.075, 0.075 + k * 0.15), GRANITE, jitter=0.04)

    def window_frame(mb: tb.MeshBuilder) -> None:
        _surround(mb, LOW_WINDOW, width=0.11, depth=0.04)

    # El zócalo liso del patio y de la casa obrera (sin almohadillado).
    mb = tb.MeshBuilder(seed=30)
    mb.slab((0.0, W), (-BELOW, P), (-0.05, T), GRANITE_DARK, step=0.8, jitter=0.03, back=False)
    mb.box((W, 0.08, 0.05), (W / 2.0, -0.04, P + 0.025), MOULD_SHADOW)
    piece = mb.finish("zocalo_patio", kit.materials("estuco"))
    lib.add(piece, [], alpha=wear_mask([], bottom=0.0), ground_z=0.0, seed=30)
    _ground_piece(lib, "bajo_escaparate", SHOP, 31, extras=[shop_frame])
    _ground_piece(lib, "bajo_portal", PORTAL, 32, extras=[portal_frame])
    _ground_piece(lib, "bajo_ventana", LOW_WINDOW, 33, extras=[window_frame])
    _ground_piece(lib, "bajo_ciego", None, 34)

    # El arco al patio: hueco de medio punto con su dovela y el túnel a oscuras.
    x0, spring, x1 = ARCH
    radius = (x1 - x0) / 2.0
    xc = (x0 + x1) / 2.0
    top = spring + 2.55 + radius
    mb = tb.MeshBuilder(seed=35)
    opening = (x0, -BELOW, x1, top)
    mb.slab((0.0, W), (-BELOW, P), (-0.08, T), GRANITE, holes=[opening], jitter=0.03, back=False)
    kit.banded_wall(mb, (0.0, W), (P, GROUND), (0.0, T), RUSTIC, holes=[(x0, P, x1, top)])
    arc_base = spring + 2.55
    arc = [(xc + radius * math.cos(math.pi * k / 16), arc_base + radius * math.sin(math.pi * k / 16)) for k in range(16, -1, -1)]
    infill = kit.ccw([(x1, arc_base), (x1, top), (x0, top), (x0, arc_base), *arc[1:-1]])
    mb.prism(infill, T, (0.0, T / 2.0, 0.0), RUSTIC, rotation=(90.0, 0.0, 0.0))
    # Archivolta y clave.
    for k in range(17):
        angle = math.pi * k / 16
        inner = Vector((xc + (radius + 0.02) * math.cos(angle), 0.0, arc_base + (radius + 0.02) * math.sin(angle)))
        mb.box((0.2, 0.06, 0.12), (inner.x + 0.08 * math.cos(angle), -0.03, inner.z + 0.08 * math.sin(angle)), DETAIL, rotation=(0.0, -math.degrees(angle), 0.0))
    mb.box((0.34, 0.1, 0.42), (xc, -0.05, arc_base + radius + 0.12), DETAIL)
    with mb.material(1):
        mb.box((x1 - x0, 7.0, top - 0.05 + 0.2), (xc, T + 3.5, (top - 0.2) / 2.0), DARK)
    piece = mb.finish("bajo_arco", kit.materials("estuco", "interior"))
    lib.add(piece, _neighbours((0.0, GROUND)), alpha=wear_mask([(x0, 0.0, x1, top)], bottom=P), ground_z=0.0, seed=35)
    # La reja del arco (cerrada o abierta de par en par).
    for name, angle, seed in (("reja_arco", 0.0, 36), ("reja_arco_abierta", 80.0, 37)):
        mb = tb.MeshBuilder(seed=seed)
        for side in (-1.0, 1.0):
            before = set(mb.bm.faces)
            hinge_x = x0 + 0.05 if side < 0 else x1 - 0.05
            leaf_x0, leaf_x1 = (hinge_x, xc) if side < 0 else (xc, hinge_x)
            mb.box((leaf_x1 - leaf_x0, 0.04, 0.05), ((leaf_x0 + leaf_x1) / 2.0, 0.3, 2.5), "#2F3133")
            mb.box((leaf_x1 - leaf_x0, 0.04, 0.05), ((leaf_x0 + leaf_x1) / 2.0, 0.3, 0.15), "#2F3133")
            for k in range(8):
                x = leaf_x0 + (leaf_x1 - leaf_x0) * (k + 0.5) / 8
                mb.box((0.022, 0.022, 2.4), (x, 0.3, 1.3), "#2F3133")
            leaf = [f for f in mb.bm.faces if f not in before]
            if angle:
                kit.transform_faces(leaf, kit.hinge((hinge_x, 0.3, 0.0), "Z", side * angle))
        piece = mb.finish(name, kit.materials("nevado"))
        tb.stain(piece, kit.RUST, amount=0.7, scale=3.0, coverage=0.45, seed=seed)
        lib.add(piece, [], samples=6, ground_z=0.0, seed=seed)


# --------------------------------------------------------------------------
# Imposta, cornisas, pilastras y esquinas
# --------------------------------------------------------------------------


def _cornice_profile(mb: tb.MeshBuilder, x_range: tuple[float, float], *, brackets: bool = True) -> None:
    """La cornisa principal: friso, canecillos, corona en vuelo y cimacio."""
    x0, x1 = x_range
    mid = (x0 + x1) / 2.0
    length = x1 - x0
    mb.box((length, 0.1, 0.42), (mid, -0.05, 0.21), DETAIL, jitter=0.02)  # friso
    mb.box((length, 0.2, 0.08), (mid, -0.1, 0.46), MOULD_SHADOW)  # filete
    mb.box((length, CORNICE + 0.05, 0.16), (mid, -(CORNICE + 0.05) / 2.0 + 0.05, 0.6), DETAIL, jitter=0.02)  # corona
    mb.box((length, 0.14, 0.1), (mid, -CORNICE + 0.02, 0.72), DETAIL)  # cimacio
    if brackets:
        count = max(1, round(length / 0.45))
        for k in range(count):
            x = x0 + length * (k + 0.5) / count
            mb.box((0.1, CORNICE - 0.15, 0.1), (x, -(CORNICE - 0.15) / 2.0, 0.47), DETAIL)
            mb.box((0.1, 0.12, 0.16), (x, -0.06, 0.4), DETAIL)


def build_mouldings(lib: kit.KitLibrary) -> None:
    # Imposta sobre los bajos.
    mb = tb.MeshBuilder(seed=41)
    mb.box((W, 0.18, 0.2), (W / 2.0, -0.09, 0.1), DETAIL, jitter=0.02)
    mb.box((W, 0.1, 0.1), (W / 2.0, -0.05, -0.05), MOULD_SHADOW)
    piece = mb.finish("imposta", kit.materials("estuco"))
    lib.add(piece, _neighbours(), seed=41)
    mb = tb.MeshBuilder(seed=42)
    mb.box((0.18, 0.18, 0.2), (-0.09, -0.09, 0.1), DETAIL)
    lib.add(mb.finish("imposta_esquina", kit.materials("estuco")), [], seed=42)
    # Cornisa principal y su esquina.
    mb = tb.MeshBuilder(seed=43)
    _cornice_profile(mb, (0.0, W))
    piece = mb.finish("cornisa", kit.materials("estuco"))
    lib.add(piece, _neighbours(), seed=43)
    mb = tb.MeshBuilder(seed=44)
    mb.box((CORNICE + 0.05, CORNICE + 0.05, 0.16), (-(CORNICE + 0.05) / 2.0 + 0.05, -(CORNICE + 0.05) / 2.0 + 0.05, 0.6), DETAIL)
    mb.box((CORNICE - 0.0, CORNICE - 0.0, 0.1), (-CORNICE / 2.0 + 0.02, -CORNICE / 2.0 + 0.02, 0.72), DETAIL)
    mb.box((0.25, 0.25, 0.42), (-0.06, -0.06, 0.21), DETAIL)
    lib.add(mb.finish("cornisa_esquina", kit.materials("estuco")), [], seed=44)
    # Alero sencillo del patio y de la casa obrera.
    mb = tb.MeshBuilder(seed=45)
    mb.box((W, 0.42, 0.14), (W / 2.0, -0.16, 0.25), DETAIL, jitter=0.02)
    mb.box((W, 0.1, 0.2), (W / 2.0, -0.05, 0.1), MOULD_SHADOW)
    lib.add(mb.finish("alero", kit.materials("estuco")), _neighbours(), seed=45)
    mb = tb.MeshBuilder(seed=46)
    mb.box((0.42, 0.42, 0.14), (-0.16, -0.16, 0.25), DETAIL)
    lib.add(mb.finish("alero_esquina", kit.materials("estuco")), [], seed=46)
    # Pilastras de orden gigante: fuste, basa y capitel (centradas en la junta entre vanos).
    for name, base, capital, seed in (("pilastra", False, False, 47), ("pilastra_basa", True, False, 48), ("pilastra_capitel", False, True, 49)):
        mb = tb.MeshBuilder(seed=seed)
        mb.box((0.52, 0.15, H), (0.0, -0.075, H / 2.0), DETAIL, cuts=2, jitter=0.02)
        if base:
            mb.box((0.66, 0.23, 0.3), (0.0, -0.115, 0.15), DETAIL)
        if capital:
            mb.box((0.68, 0.25, 0.18), (0.0, -0.125, H - 0.09), DETAIL)
            mb.box((0.6, 0.2, 0.12), (0.0, -0.1, H - 0.25), MOULD_SHADOW)
        lib.add(mb.finish(name, kit.materials("estuco")), _neighbours(), seed=seed)
    # Esquina: sillares alternos del almohadillado (bajos) y cadena de esquina arriba.
    for name, height, seed in (("esquina_bajos", GROUND + BELOW, 50), ("esquina_planta", H, 51)):
        mb = tb.MeshBuilder(seed=seed)
        z0 = -BELOW if name == "esquina_bajos" else 0.0
        z = z0
        k = 0
        while z < z0 + height - 0.05:
            size = 0.42
            # Soga en una cara y tizón en la otra, alternando en cada hilada.
            here, there = (0.62, 0.4) if k % 2 == 0 else (0.4, 0.62)
            color = RUSTIC if name == "esquina_bajos" else DETAIL
            top = min(z + size - 0.03, z0 + height)
            mb.box((here, 0.06, top - z), (here / 2.0 - 0.06, -0.03, (z + top) / 2.0), color, jitter=0.03)
            mb.box((0.06, there, top - z), (-0.03, there / 2.0 - 0.06, (z + top) / 2.0), color, jitter=0.03)
            z += size
            k += 1
        lib.add(mb.finish(name, kit.materials("estuco")), [], seed=seed)


# --------------------------------------------------------------------------
# Balcones, carpinterías e interiores
# --------------------------------------------------------------------------


def build_balconies(lib: kit.KitLibrary) -> None:
    """Balcón de losa moldurada sobre ménsulas, con balaustres torneados."""
    for name, broken, seed in (("balcon_balaustre", False, 61), ("balcon_balaustre_roto", True, 62)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        x0, x1 = 0.35, W - 0.35
        mb.box((x1 - x0, 0.85, 0.16), (W / 2.0, -0.425, -0.08), DETAIL, cuts=2, jitter=0.02)
        mb.box((x1 - x0 + 0.08, 0.12, 0.08), (W / 2.0, -0.86, -0.14), MOULD_SHADOW)
        for x in (x0 + 0.25, W / 2.0, x1 - 0.25):
            outline = kit.ccw([(0.0, 0.0), (-0.75, 0.0), (-0.75, -0.08), (-0.25, -0.18), (0.0, -0.5)])
            mb.prism([(y, z) for y, z in outline], 0.14, (x, 0.0, 0.0), DETAIL, rotation=(90.0, 0.0, 90.0))
        # Pedestales, balaustres y pasamanos.
        posts = [Vector((x0 + 0.08, -0.77, 0.0)), Vector((x1 - 0.08, -0.77, 0.0))]
        for post in posts:
            mb.box((0.16, 0.16, 0.95), (post.x, post.y, 0.475), DETAIL)
        kept = [(posts[0] + Vector((0.12, 0, 0)), posts[1] - Vector((0.12, 0, 0)))]
        for start, end in kept:
            if broken:
                cut = start.lerp(end, rng.uniform(0.35, 0.6))
                kit.balusters(mb, start, cut, 0.0, 0.78, DETAIL)
                mb.box(((cut - start).length, 0.18, 0.12), ((start.x + cut.x) / 2.0, start.y, 0.85), DETAIL)
                for _ in range(4):
                    kit.chunk(mb, (rng.uniform(cut.x, end.x), rng.uniform(-0.7, -0.3), 0.08), 0.14, DETAIL, rng)
            else:
                kit.balusters(mb, start, end, 0.0, 0.78, DETAIL)
                mb.box(((end - start).length + 0.24, 0.2, 0.12), ((start.x + end.x) / 2.0, start.y, 0.85), DETAIL, jitter=0.02)
        for x in (x0 + 0.08, x1 - 0.08):
            kit.balusters(mb, Vector((x, -0.62, 0.0)), Vector((x, -0.08, 0.0)), 0.0, 0.78, DETAIL)
            mb.box((0.16, 0.6, 0.12), (x, -0.38, 0.85), DETAIL)
        piece = mb.finish(name, kit.materials("estuco"))
        lib.add(piece, _neighbours(), samples=10, seed=seed)


def build_windows(lib: kit.KitLibrary) -> None:
    groups = (
        ("ventana_alta", [(WINDOW, "alta")], WINDOW_STATES, "#B5AE9C"),
        ("ventana_patio", [(YARD_WINDOW, "alta")], SHORT_STATES, kit.FRAME),
        ("puerta_balcon_e", [(DOOR, "puerta")], SHORT_STATES, "#B5AE9C"),
        ("ventana_baja", [(LOW_WINDOW, "alta")], SHORT_STATES, "#B5AE9C"),
        ("escalera_e", [(STAIR, "escalera")], ("intacta", "rota", "quemada", "vacia"), kit.FRAME),
        ("escaparate", [(SHOP, "escaparate")], ("intacta", "rota", "tapiada", "quemada", "vacia"), "#3C3A36"),
    )
    seed = 100
    for prefix, openings, states, frame in groups:
        for state in states:
            seed += 1
            rng = random.Random(seed)
            mb = tb.MeshBuilder(seed=seed)
            for opening, kind in openings:
                kit.window(mb, opening, kind, state, rng, depth=DEPTH, wall=T, frame_color=frame)
            piece = mb.finish(f"{prefix}_{state}", kit.materials("nevado", "vidrio", "interior"))
            if state == "quemada":
                tb.stain(piece, kit.SOOT, amount=0.8, scale=4.0, coverage=0.6, seed=seed)
            wall = tb.MeshBuilder(seed=seed)
            wall.slab((0.0, W), (-1.0, GROUND), (0.0, T), PLASTER, holes=[o for o, _ in openings], back=False)
            lib.add(piece, [wall.finish("contexto_muro")], samples=10, ao_distance=0.35, seed=seed)
    for state in ("cerrada", "abierta", "tapiada", "arrancada"):
        seed += 1
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        x0, z0, x1, z1 = PORTAL
        if state == "arrancada":
            kit.window(mb, PORTAL, "portal", "vacia", rng, depth=DEPTH, wall=T)
        else:
            kit.window(mb, PORTAL, "portal", "rota" if state == "abierta" else "intacta", rng, depth=DEPTH, wall=T, frame_color="#3E3027", sill=False, open_sash=0)
        if state == "tapiada":
            kit.planks(mb, PORTAL, 0.0, rng, count=7, overhang=0.15)
        with mb.material(2):
            kit.room(mb, (x0 - 0.4, x1 + 0.4), (z0 - 0.2, 3.9), (T, T + 2.6), "#2A2620")
            for k in range(4):
                mb.box((x1 - x0 + 0.6, 0.3, 0.16), ((x0 + x1) / 2.0, T + 1.0 + k * 0.3, z0 + 0.08 + k * 0.16), "#2F2B26")
        piece = mb.finish(f"puerta_e_{state}", kit.materials("nevado", "vidrio", "interior"))
        lib.add(piece, [], samples=10, ao_distance=0.4, ground_z=0.0, seed=seed)
    # La puerta trasera del patio.
    for state in ("cerrada", "tapiada", "arrancada"):
        seed += 1
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        x0, z0, x1, z1 = BACK_DOOR
        if state == "arrancada":
            kit.window(mb, BACK_DOOR, "puerta", "vacia", rng, depth=0.12, wall=T)
        else:
            mb.box((x1 - x0 - 0.04, 0.05, z1 - z0 - 0.02), ((x0 + x1) / 2.0, 0.14, (z0 + z1) / 2.0), "#4A3B2F", bevel=0.006, jitter=0.06)
            mb.box((0.08, 0.03, 0.12), (x1 - 0.2, 0.1, z0 + 1.05), kit.METAL)
            if state == "tapiada":
                kit.planks(mb, BACK_DOOR, 0.0, rng, count=5)
        with mb.material(2):
            kit.room(mb, (x0 - 0.3, x1 + 0.3), (z0 - 0.1, 3.0), (T, T + 2.0), "#262320")
        piece = mb.finish(f"puerta_patio_{state}", kit.materials("nevado", "vidrio", "interior"))
        lib.add(piece, [], samples=8, ao_distance=0.4, ground_z=0.0, seed=seed)


def build_rooms(lib: kit.KitLibrary) -> None:
    """Interiores falsos: más altos que en los bloques (techos de 3 m), y la tienda."""
    for index, wallpaper in enumerate(kit.WALLPAPERS[:3]):
        seed = 200 + index
        mb = tb.MeshBuilder(seed=seed)
        kit.room(mb, (0.15, W - 0.15), (0.0, H - SLAB), (T, T + ROOM), wallpaper)
        mb.box((W - 0.3, 0.03, 0.18), (W / 2.0, T + ROOM - 0.02, H - SLAB - 0.15), "#3A3530")  # moldura del techo
        if index == 0:
            mb.box((1.0, 0.6, 2.2), (0.75, T + ROOM - 0.32, 1.1), "#2A221C", jitter=0.06)
        elif index == 1:
            mb.box((0.9, 0.03, 2.3), (W - 0.9, T + ROOM - 0.02, 1.15), "#171513")
            mb.bar((W / 2.0, T + 1.4, H - SLAB), (W / 2.0, T + 1.4, H - SLAB - 0.6), 0.006, "#141312", 4)
            for k in range(5):
                angle = k * math.tau / 5
                mb.bar((W / 2.0, T + 1.4, H - SLAB - 0.6), (W / 2.0 + 0.3 * math.cos(angle), T + 1.4 + 0.3 * math.sin(angle), H - SLAB - 0.75), 0.008, "#3A3530", 4)
        else:
            mb.box((1.6, 0.7, 0.8), (W / 2.0 + 0.3, T + ROOM - 0.4, 0.4), "#2D2620", jitter=0.06)
        lib.add(mb.finish(f"habitacion_e_{'abc'[index]}", kit.materials("interior")), [], samples=10, ao=0.6, ao_distance=0.9, seed=seed)
    rng = random.Random(210)
    mb = tb.MeshBuilder(seed=210)
    kit.room(mb, (0.15, W - 0.15), (0.0, H - SLAB), (T, T + ROOM), "#1A1715")
    for _ in range(6):
        kit.chunk(mb, (rng.uniform(0.4, W - 0.4), T + rng.uniform(0.3, ROOM - 0.3), 0.08), rng.uniform(0.15, 0.4), rng.choice(("#1E1B19", "#2A2522", kit.CHAR)), rng)
    lib.add(mb.finish("habitacion_e_quemada", kit.materials("interior")), [], samples=10, ao=0.6, ao_distance=0.9, seed=210)
    # La tienda: mostrador, estanterías vacías y el suelo lleno de papeles.
    rng = random.Random(211)
    mb = tb.MeshBuilder(seed=211)
    kit.room(mb, (0.05, W - 0.05), (0.0, GROUND - 0.4), (T, T + 5.0), "#2E2B25")
    mb.box((W - 0.6, 0.6, 1.0), (W / 2.0, T + 2.4, 0.5), "#3A3128", jitter=0.06)
    for k in range(4):
        mb.box((W - 0.4, 0.4, 0.04), (W / 2.0, T + 4.7, 0.6 + k * 0.6), "#33291F")
    for _ in range(12):
        mb.box((0.2, 0.28, 0.005), (rng.uniform(0.3, W - 0.3), T + rng.uniform(0.3, 2.0), 0.01), "#6E685A", rotation=(0.0, 0.0, rng.uniform(0, 180)))
    lib.add(mb.finish("tienda_interior", kit.materials("interior")), [], samples=10, ao=0.6, ao_distance=1.0, seed=211)
    # La caja de la escalera de servicio.
    mb = tb.MeshBuilder(seed=212)
    kit.room(mb, (0.1, W - 0.1), (-0.5, H + 0.4), (T, T + 2.8), "#34302A")
    for k in range(10):
        mb.box((1.2, 0.28, 0.16), (W / 2.0 - 0.6, T + 1.0 + k * 0.17, 0.4 + k * 0.17), "#38342E")
    lib.add(mb.finish("escalera_e_interior", kit.materials("interior")), [], samples=10, ao=0.6, ao_distance=0.9, seed=212)


# --------------------------------------------------------------------------
# Cubierta
# --------------------------------------------------------------------------


def build_roof(lib: kit.KitLibrary) -> None:
    """Buhardilla y chimenea. Origen: el centro de su base, sobre el faldón."""
    # Buhardilla de chapa con un ventanuco: mira hacia -y (hacia la calle).
    mb = tb.MeshBuilder(seed=71)
    width, depth, height = 1.3, 1.6, 1.35
    front = [(-width / 2.0, 0.0), (width / 2.0, 0.0), (width / 2.0, height - 0.45), (0.0, height), (-width / 2.0, height - 0.45)]
    mb.prism(kit.ccw(front), depth, (0.0, depth / 2.0 - 0.1, 0.0), "#5C5F5A", rotation=(90.0, 0.0, 0.0), jitter=0.03)
    for side in (-1.0, 1.0):
        mb.box((0.04, depth + 0.2, 0.62), (side * 0.36, depth / 2.0 - 0.15, height - 0.22), "#565953", rotation=(0.0, side * 34.0, 0.0), jitter=0.04)
    with mb.material(1):
        mb.box((0.6, 0.02, 0.55), (0.0, -0.11, 0.55), DARK)
    for k in range(4):
        mb.box((0.62, 0.02, 0.025), (0.0, -0.13, 0.32 + k * 0.15), "#3A3C3A", rotation=(-25.0, 0.0, 0.0))
    piece = mb.finish("buhardilla", kit.materials("nevado", "interior"))
    tb.stain(piece, kit.RUST, amount=0.6, scale=3.0, coverage=0.4, seed=71)
    lib.add(piece, [], ground_z=0.0, seed=71)
    # Chimenea de ladrillo con su remate.
    mb = tb.MeshBuilder(seed=72)
    with mb.material(1):
        mb.box((0.9, 0.55, 2.0), (0.0, 0.0, 0.7), BRICK, cuts=2, jitter=0.04)
    mb.box((1.05, 0.7, 0.1), (0.0, 0.0, 1.75), "#6A665E")
    with mb.material(2):
        for x in (-0.22, 0.22):
            mb.box((0.2, 0.2, 0.02), (x, 0.0, 1.805), DARK)
    piece = mb.finish("chimenea", kit.materials("nevado", "ladrillo", "interior"))
    tb.stain(piece, "#201C1A", amount=0.7, scale=2.0, coverage=0.5, seed=72, stretch_z=0.3)
    lib.add(piece, [], ground_z=0.0, seed=72)


# --------------------------------------------------------------------------
# Daños
# --------------------------------------------------------------------------


def build_damage(lib: kit.KitLibrary) -> None:
    """Muñones de ladrillo, el corte de una casa partida y un hueco en la fachada."""
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
            edge = kit.broken_edge(a, b, low, high, rng)
            kit.broken_slab(mb, (a, b), 0.0, edge, (0.0, 0.03), PLASTER)  # el revoque
            with mb.material(1):
                kit.broken_slab(mb, (a, b), 0.0, [(x, z + rng.uniform(0.0, 0.15)) for x, z in edge], (0.03, T), BRICK)
        with mb.material(1):
            for _ in range(rng.randint(5, 8)):
                kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.6, 2.8), 0.1), rng.uniform(0.12, 0.3), BRICK, rng)
        for _ in range(2):  # vigas quemadas del forjado caído
            start = Vector((rng.uniform(0.3, W - 0.3), T, rng.uniform(0.0, 0.3)))
            mb.box((0.18, 2.6, 0.22), (start.x, start.y + 1.1, start.z + 0.4), BEAM, rotation=(rng.uniform(10, 25), 0.0, rng.uniform(-15, 15)), jitter=0.08)
        piece = mb.finish(f"estuco_roto_{letter}", kit.materials("estuco", "ladrillo"))
        lib.add(piece, _neighbours((0.0, 1.0)), alpha=wear_mask([(x0, z0, x1, 3.0)]), ground_z=0.0, seed=seed)
    # El corte: el muro de ladrillo partido, el forjado y las habitaciones al aire.
    for index, seed in enumerate((631, 632, 633)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        edge = kit.broken_edge(0.0, W, 0.0, 0.4, rng)
        outline = kit.ccw([(0.0, 3.0), (W, 3.0), *[(x, d) for x, d in reversed(edge)]])
        mb.prism(outline, SLAB, (0.0, 0.0, -SLAB / 2.0), SLAB_COLOR, jitter=0.05)
        for _ in range(4):
            mb.box((0.16, 0.7, 0.2), (rng.uniform(0.2, W - 0.2), -0.15, -0.12), BEAM, rotation=(rng.uniform(-20, 5), 0.0, rng.uniform(-12, 12)), jitter=0.08)
        if index < 2:
            with mb.material(1):
                wall_y = rng.uniform(2.2, 3.0)
                kit.room(mb, (0.0, W), (0.0, H - SLAB), (0.3, wall_y), kit.WALLPAPERS[index])
                if rng.random() < 0.8:
                    x = rng.uniform(0.7, W - 0.7)
                    mb.box((0.14, wall_y - 0.3, H - SLAB), (x, 0.3 + (wall_y - 0.3) / 2.0, (H - SLAB) / 2.0), kit.WALLPAPERS[(index + 1) % 4])
                    mb.box((0.85, 0.03, 2.3), (x + 0.6, wall_y - 0.02, 1.15), "#151413")
            with mb.material(2):
                for _ in range(4):
                    kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.2, 1.5), 0.08), rng.uniform(0.1, 0.3), BRICK, rng)
        else:
            with mb.material(1):
                kit.broken_slab(mb, (0.0, W), 0.0, kit.broken_edge(0.0, W, 0.1, 1.3, rng), (2.4, 2.54), kit.WALLPAPERS[2])
            with mb.material(2):
                for _ in range(8):
                    kit.chunk(mb, (rng.uniform(0.2, W - 0.2), rng.uniform(0.2, 2.4), 0.1), rng.uniform(0.15, 0.35), rng.choice((BRICK, PLASTER)), rng)
        name = f"corte_e_{'abc'[index]}" if index < 2 else "corte_e_roto"
        lib.add(mb.finish(name, kit.materials("estuco", "interior", "nevado")), [], samples=10, ao_distance=0.8, seed=seed)
    # Hueco: un trozo de fachada caído, con el ladrillo roto alrededor y la habitación al aire.
    rng = random.Random(641)
    mb = tb.MeshBuilder(seed=641)
    left = [(rng.uniform(0.25, 0.65), H * k / 8) for k in range(9)]
    right = [(W - rng.uniform(0.25, 0.65), H * k / 8) for k in range(9)]
    for edge, side in ((left, 0.0), (right, W)):
        outline = kit.ccw([(side, 0.0), *edge, (side, H)])
        mb.prism(outline, 0.03, (0.0, 0.015, 0.0), PLASTER, rotation=(90.0, 0.0, 0.0))
        with mb.material(1):
            inner = [(x + (0.08 if side == 0.0 else -0.08), z) for x, z in edge]
            mb.prism(kit.ccw([(side, 0.0), *inner, (side, H)]), T - 0.03, (0.0, 0.03 + (T - 0.03) / 2.0, 0.0), BRICK, rotation=(90.0, 0.0, 0.0))
    with mb.material(2):
        kit.room(mb, (0.1, W - 0.1), (0.0, H - SLAB), (T, T + 3.6), kit.WALLPAPERS[3])
        mb.box((1.8, 0.7, 1.0), (1.4, T + 1.5, 0.4), "#2E241C", rotation=(0.0, 70.0, 12.0), jitter=0.06)
    with mb.material(3):
        mb.box((W - 0.3, 1.4, 0.05), (W / 2.0, T + 0.6, 0.02), "#2A2724")
        for _ in range(7):
            kit.chunk(mb, (rng.uniform(0.3, W - 0.3), rng.uniform(-0.2, T + 1.5), 0.08), rng.uniform(0.12, 0.3), rng.choice((BRICK, PLASTER)), rng)
    piece = mb.finish("estuco_hueco", kit.materials("estuco", "ladrillo", "interior", "nevado"))
    lib.add(piece, _neighbours(), alpha=wear_mask([(0.6, 0.0, W - 0.6, H)]), samples=12, ao_distance=0.8, seed=641)


def build_kit() -> object:
    lib = kit.KitLibrary("kit_estalinka", spacing=8.0)
    build_walls(lib)
    build_ground_floor(lib)
    build_mouldings(lib)
    build_balconies(lib)
    build_windows(lib)
    build_rooms(lib)
    build_roof(lib)
    build_damage(lib)
    return lib.root


def models() -> dict:
    return {"kit_estalinka": build_kit}
