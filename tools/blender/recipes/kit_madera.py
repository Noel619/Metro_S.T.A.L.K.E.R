"""Kit de arquitectura: las casas de madera (la isba del barranco y el barracón obrero).

Una biblioteca, "kit_madera", con las casas enteras: sus medidas son fijas en el plano
(la isba, 9 × 8 m; el barracón, 30 × 11 m), así que no hacen falta vanos sueltos. Godot
escoge la que toca por su daño y su incendio y la coloca sobre la huella
(scripts/surface/kit_whole.gd). En Tumansk ardieron casi todas.

- La isba: troncos de 26 cm cruzados en las esquinas, un zócalo de piedra, tres
  ventanas a la calle con guardapolvos tallados y contraventanas, el piñón entablado con
  su ventanuco y las tablas talladas del alero, la estufa de ladrillo con su chimenea, el
  porche lateral y la cubierta de chapa. Estados: abandonada (dos), chamuscada, cascarón
  (los muros a media altura, sin cubierta) y quemada (la estufa y la chimenea en pie entre
  los troncos carbonizados, como en las aldeas quemadas).
- El barracón: dos plantas de tablas sobre un zócalo de hormigón, ventanas con su
  recercado de tablas, tres puertas con tejadillo, cubierta a dos aguas y cuatro
  chimeneas. Quemado, quedan los postes carbonizados y las chimeneas.

Coordenadas: el origen en el centro de la huella, en el suelo; x a lo largo del lado
largo, y a lo ancho y z hacia arriba. La fachada principal (el piñón de la isba, la
puerta central del barracón) mira hacia -x en la isba y hacia -y en el barracón.
"""

from __future__ import annotations

import math
import random

from mathutils import Matrix, Vector

import kit_bpy as kit
import tumansk_bpy as tb

LOG = "#5B4C3E"
LOG_DARK = "#4A3D31"
CHAR = "#1B1816"
ASH = "#3A3632"
STONE = "#57524B"
BRICK = "#7E4A39"
CASING = ("#C7C1B1", "#86A0AC", "#B7B39A")
SHUTTER = ("#5F7F8C", "#6D7F5E", "#7A4E44")
METAL_ROOF = ("#5A6058", "#6A5A4E", "#585B5C")
PLANK = "#76604B"
PLANK_DARK = "#4E3E30"
BOARD = "#7D5A43"  # tablas del barracón, pintadas de rojo óxido hace mucho
DARK = "#121110"
DOOR = "#3E3129"
TRIM = "#BDB39B"  # recercados, esquineras e impostas del barracón: crema, de hace mucho
CONCRETE = "#66615A"

# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------


def _facade(position: tuple[float, float, float], facing: str) -> Matrix:
    """El marco de una fachada: lo que se construye de cara a -y (como las piezas del kit)
    pasa a mirar hacia ``facing`` ("-x", "+x", "-y" o "+y"), con el muro en ``position``."""
    rotations = {
        "-y": Matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1))),
        "+y": Matrix(((-1, 0, 0), (0, -1, 0), (0, 0, 1))),
        "-x": Matrix(((0, 1, 0), (-1, 0, 0), (0, 0, 1))),
        "+x": Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1))),
    }
    return Matrix.Translation(Vector(position)) @ rotations[facing].to_4x4()


def _placed(mb: tb.MeshBuilder, matrix: Matrix, build) -> None:
    """Construye algo en el marco de una fachada y lo lleva a su sitio."""
    before = set(mb.bm.faces)
    build(mb)
    kit.transform_faces([f for f in mb.bm.faces if f not in before], matrix)


def _log(mb: tb.MeshBuilder, start: Vector, end: Vector, radius: float, color: str, rng: random.Random) -> None:
    """Un tronco entre dos puntos, algo irregular."""
    mb.cylinder(radius * rng.uniform(0.92, 1.06), (end - start).length, (start + end) / 2.0, color, rotation=[math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference((end - start).normalized()).to_euler()], segments=8, jitter=0.06)


def _log_wall(mb: tb.MeshBuilder, axis: str, offset: float, span: float, z0: float, courses: int, openings: list, rng: random.Random, *, color: str = LOG, overhang: float = 0.28, tops: list | None = None) -> None:
    """Un muro de troncos a lo largo de ``axis`` ("x" o "y"), en ``offset`` del otro eje.

    ``openings`` son huecos (u0, u1, z0, z1): los troncos se cortan alrededor. ``tops``
    (si se da) es la altura hasta la que llega el muro en cada tramo (muros quemados).
    """
    radius = 0.13
    for k in range(courses):
        z = z0 + k * 0.24
        cuts = sorted((u0, u1) for u0, u1, a, b in openings if a - 0.05 < z < b + 0.05)
        start = -span / 2.0 - overhang
        pieces = []
        for u0, u1 in cuts:
            pieces.append((start, u0))
            start = u1
        pieces.append((start, span / 2.0 + overhang))
        for a, b in pieces:
            if b - a < 0.15:
                continue
            if tops is not None:
                limit = tops[max(0, min(len(tops) - 1, int(((a + b) / 2.0 / span + 0.5) * len(tops))))]
                if z > limit:
                    continue
            if axis == "x":
                _log(mb, Vector((a, offset, z)), Vector((b, offset, z)), radius, color, rng)
            else:
                _log(mb, Vector((offset, a, z)), Vector((offset, b, z)), radius, color, rng)


def _casing(mb: tb.MeshBuilder, opening: tuple, color: str, rng: random.Random, *, shutters: str | None = None) -> None:
    """Guardapolvo tallado (nalichnik) alrededor de una ventana, en el marco de su fachada,
    con las contraventanas abiertas contra el muro."""
    x0, z0, x1, z1 = opening
    for x in (x0 - 0.07, x1 + 0.07):
        mb.box((0.14, 0.06, z1 - z0 + 0.1), (x, -0.03, (z0 + z1) / 2.0), color, jitter=0.03)
    # La cabeza: un tablero con un arco y dientes, y su cornisilla.
    width = x1 - x0 + 0.4
    head = [(x0 - 0.2, z1), (x1 + 0.2, z1)]
    steps = 8
    for k in range(steps + 1):
        t = k / steps
        x = x1 + 0.2 - width * t
        bump = 0.18 * math.sin(math.pi * t) + (0.05 if k % 2 == 0 else 0.0)
        head.append((x, z1 + 0.22 + bump))
    mb.prism(kit.ccw(head), 0.05, (0.0, -0.035, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.03)
    kit.moulding(mb, (x0 - 0.25, x1 + 0.25), [(0.0, z1 + 0.56), (-0.13, z1 + 0.5), (-0.13, z1 + 0.46), (0.0, z1 + 0.41)], color)
    # El alféizar con su faldón dentado.
    skirt = [(x0 - 0.15, z0 - 0.04), (x1 + 0.15, z0 - 0.04)]
    for k in range(9):
        t = k / 8
        skirt.append((x1 + 0.15 - (x1 - x0 + 0.3) * t, z0 - 0.2 - (0.07 if k % 2 else 0.0)))
    mb.prism(kit.ccw(skirt), 0.05, (0.0, -0.035, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.03)
    kit.moulding(mb, (x0 - 0.175, x1 + 0.175), [(0.0, z0 + 0.01), (-0.14, z0 - 0.04), (-0.14, z0 - 0.07), (0.0, z0 - 0.11)], color)
    if shutters:
        leaf = (x1 - x0) / 2.0
        for side in (-1.0, 1.0):
            x = (x0 - 0.16 - leaf / 2.0) if side < 0 else (x1 + 0.16 + leaf / 2.0)
            mb.box((leaf, 0.04, z1 - z0), (x, -0.06, (z0 + z1) / 2.0), shutters, jitter=0.05)
            mb.box((leaf - 0.12, 0.012, (z1 - z0) * 0.4), (x, -0.085, z0 + (z1 - z0) * 0.7), "#2F2A26")


# --------------------------------------------------------------------------
# La isba
# --------------------------------------------------------------------------

L, D = 9.0, 8.0
BASE = 0.45
COURSES = 12
EAVE = BASE + 0.12 + COURSES * 0.24
RIDGE = 6.0
FRONT_WINDOWS = (-2.3, 0.0, 2.3)  # en la fachada del piñón (-x), a lo largo de y
SIDE_WINDOWS = (-2.6, 0.0, 2.6)  # en el lado -y, a lo largo de x
PORCH_WINDOWS = (-2.6, -0.4)  # en el lado +y; la puerta del porche va en x = 2.6
WIN_W, WIN_H, SILL = 0.8, 1.1, 1.35


def _isba_walls(mb: tb.MeshBuilder, rng: random.Random, *, tops: dict | None = None, color: str = LOG) -> None:
    """Los cuatro muros de troncos, cruzados en las esquinas, con sus huecos."""
    tops = tops or {}
    door = (2.15, 3.05, BASE, BASE + 2.0)
    front = [(-y - WIN_W / 2.0, -y + WIN_W / 2.0, SILL, SILL + WIN_H) for y in FRONT_WINDOWS]
    back = [(1.0, 1.0 + WIN_W, SILL, SILL + WIN_H)]
    side = [(x - WIN_W / 2.0, x + WIN_W / 2.0, SILL, SILL + WIN_H) for x in SIDE_WINDOWS]
    porch = [(x - WIN_W / 2.0, x + WIN_W / 2.0, SILL, SILL + WIN_H) for x in PORCH_WINDOWS] + [door]
    z_long, z_end = BASE + 0.12, BASE + 0.24
    _log_wall(mb, "x", -D / 2.0 + 0.13, L, z_long, COURSES, side, rng, color=color, tops=tops.get("-y"))
    _log_wall(mb, "x", D / 2.0 - 0.13, L, z_long, COURSES, porch, rng, color=color, tops=tops.get("+y"))
    _log_wall(mb, "y", -L / 2.0 + 0.13, D, z_end, COURSES, front, rng, color=color, tops=tops.get("-x"))
    _log_wall(mb, "y", L / 2.0 - 0.13, D, z_end, COURSES, back, rng, color=color, tops=tops.get("+x"))


def _isba_base(mb: tb.MeshBuilder) -> None:
    mb.box((L + 0.12, D + 0.12, BASE + 0.4), (0.0, 0.0, (BASE - 0.4) / 2.0), STONE, bevel=0.03, cuts=3, jitter=0.04)


def _stove(mb: tb.MeshBuilder, rng: random.Random, *, chimney_top: float = RIDGE + 0.7, burnt: bool = False) -> None:
    """La estufa rusa de ladrillo y su chimenea: lo único que aguanta un incendio."""
    with mb.material(3):
        mb.box((1.6, 1.3, 1.9), (0.9, 0.5, BASE + 0.95), BRICK, bevel=0.03, cuts=2, jitter=0.05)
        mb.box((0.62, 0.62, chimney_top - BASE - 1.9), (0.9, 0.7, (BASE + 1.9 + chimney_top) / 2.0), BRICK, cuts=3, jitter=0.05)
    mb.box((0.78, 0.78, 0.1), (0.9, 0.7, chimney_top + 0.05), "#5E5A54" if not burnt else "#3A3632")
    with mb.material(2):
        mb.box((0.5, 0.04, 0.4), (0.9, -0.15, BASE + 0.7), DARK)  # la boca del horno


def _roof(mb: tb.MeshBuilder, color: str, rng: random.Random, *, missing: float = 0.0) -> None:
    """Cubierta a dos aguas de chapa, con alero, y las tablas talladas de los piñones."""
    half = D / 2.0 + 0.5
    rise = RIDGE - EAVE
    slope = math.atan2(rise, D / 2.0)
    length = half / math.cos(slope)
    eave_z = EAVE - 0.5 * math.tan(slope)
    for side in (-1.0, 1.0):
        sheets = 6
        for k in range(sheets):
            if missing > 0.0 and side > 0 and rng.random() < missing:
                continue
            x0 = -L / 2.0 - 0.4 + (L + 0.8) * k / sheets
            x1 = -L / 2.0 - 0.4 + (L + 0.8) * (k + 1) / sheets
            center = Vector(((x0 + x1) / 2.0, side * half / 2.0, (eave_z + RIDGE) / 2.0 + 0.04))
            mb.box((x1 - x0 + 0.02, length, 0.05), center, color, rotation=(math.degrees(-side * slope), 0.0, 0.0), jitter=0.04, cuts=1)
    mb.box((L + 0.9, 0.16, 0.12), (0.0, 0.0, RIDGE + 0.06), color)  # cumbrera


def _gables(mb: tb.MeshBuilder, rng: random.Random, casing: str, *, attic: str = "intacta") -> None:
    """Los piñones entablados, con el ventanuco del frente y las tablas talladas."""
    for end in (-1.0, 1.0):
        x = end * (L / 2.0 - 0.02)
        triangle = kit.ccw([(-D / 2.0 + 0.05, EAVE), (D / 2.0 - 0.05, EAVE), (0.0, RIDGE - 0.05)])
        mb.prism(triangle, 0.06, (x, 0.0, 0.0), PLANK, rotation=(90.0, 0.0, 90.0), jitter=0.04)
        for k in range(-6, 7):  # tapajuntas verticales
            y = k * 0.55
            top = RIDGE - abs(y) * (RIDGE - EAVE) / (D / 2.0) - 0.1
            if top > EAVE + 0.15:
                mb.box((0.06, 0.07, top - EAVE), (x + end * 0.035, y, (top + EAVE) / 2.0), PLANK_DARK)
        _barge_boards(mb, end, casing)
    matrix = _facade((-L / 2.0 - 0.06, 0.0, 0.0), "-x")
    opening = (-0.3, EAVE + 0.65, 0.3, EAVE + 1.35)

    def attic_window(builder: tb.MeshBuilder) -> None:
        kit.window(builder, opening, "escalera", attic, rng, depth=0.03, wall=0.1, sill=False)
        _casing(builder, opening, casing, rng)
        with builder.material(2):
            builder.box((0.6, 0.02, 0.7), (0.0, 0.3, (opening[1] + opening[3]) / 2.0), DARK)

    _placed(mb, matrix, attic_window)


def _barge_boards(mb: tb.MeshBuilder, end: float, color: str) -> None:
    """Las prichelinas: dos tablas de festones bajo el borde de la chapa del piñón, y la
    toalla (polotenze) colgada del vértice, tapando la junta.

    Son tablas anchas y gruesas, no listones: un listón fino se dibujaría a puntos."""
    slope = math.atan2(RIDGE - EAVE, D / 2.0)
    sin, cos = math.sin(slope), math.cos(slope)
    run = (D / 2.0 + 0.5) / cos  # el largo del faldón, del vértice al alero
    apex = RIDGE + 0.03 - 0.025 / cos  # justo bajo la chapa
    width, lobe, period = 0.14, 0.07, 0.32
    lobes = max(1, round((run - 0.3) / period))
    for side in (-1.0, 1.0):

        def at(t: float, w: float, side: float = side) -> tuple[float, float]:
            # t a lo largo del faldón desde el vértice; w hacia abajo, perpendicular a él.
            return (side * (t * cos - w * sin), apex - t * sin - w * cos)

        lower = []
        for k in range(lobes * 6 + 1):
            phase = (k % 6) / 6.0
            lower.append(at(0.3 + (run - 0.3) * k / (lobes * 6), width + lobe * math.sqrt(1.0 - (2.0 * phase - 1.0) ** 2)))
        # Cortada en el eje (y = 0), donde se junta con la otra.
        outline = [(0.0, apex), at(run, 0.0), *reversed(lower), at(width * sin / cos, width)]
        mb.prism(kit.ccw(outline), 0.06, (end * (L / 2.0 + 0.37), 0.0, 0.0), color, rotation=(90.0, 0.0, 90.0))
    towel = [(-0.12, apex - 0.03), (0.12, apex - 0.03), (0.12, apex - 0.45), (0.05, apex - 0.52), (0.0, apex - 0.6), (-0.05, apex - 0.52), (-0.12, apex - 0.45)]
    mb.prism(kit.ccw(towel), 0.05, (end * (L / 2.0 + 0.43), 0.0, 0.0), color, rotation=(90.0, 0.0, 90.0))


def _windows(mb: tb.MeshBuilder, rng: random.Random, casing: str, shutter: str | None, states: list) -> None:
    """Las ventanas con sus guardapolvos, en los tres lados que las tienen."""
    groups = [
        ("-x", (-L / 2.0, 0.0, 0.0), [-y for y in FRONT_WINDOWS]),
        ("-y", (0.0, -D / 2.0, 0.0), list(SIDE_WINDOWS)),
        ("+y", (0.0, D / 2.0, 0.0), [-x for x in PORCH_WINDOWS]),
        ("+x", (L / 2.0, 0.0, 0.0), [1.0 + WIN_W / 2.0]),
    ]
    index = 0
    for facing, position, centres in groups:
        matrix = _facade(position, facing)
        for u in centres:
            state = states[index % len(states)]
            index += 1
            opening = (u - WIN_W / 2.0, SILL, u + WIN_W / 2.0, SILL + WIN_H)

            def build(builder: tb.MeshBuilder, opening=opening, state=state) -> None:
                kit.window(builder, opening, "escalera", state, rng, depth=0.08, wall=0.26, frame_color=casing, sill=False)
                if state != "vacia":
                    _casing(builder, opening, casing, rng, shutters=shutter if facing == "-x" else None)

            _placed(mb, matrix, build)


def _porch(mb: tb.MeshBuilder, rng: random.Random, color: str) -> None:
    """El porche de la puerta lateral: tarima, escalones, dos postes y un tejadillo."""
    matrix = _facade((0.0, D / 2.0, 0.0), "+y")

    def build(builder: tb.MeshBuilder) -> None:
        u0, u1 = -3.05, -2.15
        builder.box((u1 - u0 - 0.04, 0.05, 1.95), ((u0 + u1) / 2.0, 0.12, BASE + 1.0), DOOR, jitter=0.06)
        builder.box((2.0, 1.4, 0.1), ((u0 + u1) / 2.0, -0.7, BASE + 0.05), PLANK, jitter=0.05)
        builder.box((1.9, 1.3, BASE), ((u0 + u1) / 2.0, -0.7, BASE / 2.0), PLANK_DARK, jitter=0.05)  # el faldón
        for k in range(3):
            builder.box((1.2, 0.3, 0.15), ((u0 + u1) / 2.0, -1.55 - k * 0.3, BASE - 0.12 - k * 0.15), PLANK_DARK, jitter=0.06)
        for u in (u0 - 0.45, u1 + 0.45):
            builder.box((0.12, 0.12, 2.3), (u, -1.3, BASE + 1.15), PLANK_DARK)
        builder.box((2.3, 1.8, 0.05), ((u0 + u1) / 2.0, -0.8, BASE + 2.45), color, rotation=(14.0, 0.0, 0.0), jitter=0.04)

    _placed(mb, matrix, build)


def _interior(mb: tb.MeshBuilder) -> None:
    with mb.material(2):
        mb.box((L - 0.7, D - 0.7, 2.4), (0.0, 0.0, BASE + 1.3), DARK)


def build_isbas(lib: kit.KitLibrary) -> None:
    variants = (
        ("isba_a", 701, ["intacta", "cortina", "rota", "tapiada", "rota", "intacta", "vacia", "rota", "tapiada"]),
        ("isba_b", 702, ["tapiada", "rota", "vacia", "rota", "plastico", "rota", "tapiada", "vacia", "rota"]),
    )
    for name, seed, states in variants:
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        casing = CASING[seed % len(CASING)]
        _isba_base(mb)
        _isba_walls(mb, rng)
        _windows(mb, rng, casing, SHUTTER[seed % len(SHUTTER)], states)
        _gables(mb, rng, casing)
        _roof(mb, METAL_ROOF[seed % len(METAL_ROOF)], rng)
        _stove(mb, rng)
        _porch(mb, rng, METAL_ROOF[seed % len(METAL_ROOF)])
        _interior(mb)
        piece = mb.finish(name, kit.materials("nevado", "vidrio", "interior", "ladrillo"))
        tb.stain(piece, "#3A332B", amount=0.45, scale=1.4, coverage=0.4, seed=seed, stretch_z=0.3)
        lib.add(piece, [], samples=10, ao=0.5, ao_distance=0.5, ground_z=0.0, seed=seed)
    # Chamuscada: el frente ennegrecido, ventanas quemadas y media cubierta caída.
    rng = random.Random(703)
    mb = tb.MeshBuilder(seed=703)
    _isba_base(mb)
    _isba_walls(mb, rng, color=LOG_DARK)
    _windows(mb, rng, "#3A342D", None, ["quemada", "quemada", "rota", "vacia", "quemada", "rota", "vacia", "quemada", "vacia"])
    _gables(mb, rng, "#3A342D", attic="quemada")
    _roof(mb, METAL_ROOF[0], rng, missing=0.7)
    for k in range(5):  # las vigas quemadas que asoman donde falta la chapa
        x = -3.5 + k * 1.75
        mb.box((0.14, 4.6, 0.16), (x, 2.1, (EAVE + RIDGE) / 2.0 - 0.05), CHAR, rotation=(-math.degrees(math.atan2(RIDGE - EAVE, D / 2.0)), 0.0, 0.0), jitter=0.08)
    _stove(mb, rng, burnt=True)
    _porch(mb, rng, "#3A342D")
    _interior(mb)
    piece = mb.finish("isba_chamuscada", kit.materials("nevado", "vidrio", "interior", "ladrillo"))
    tb.stain(piece, CHAR, amount=0.85, scale=1.2, coverage=0.55, seed=703, stretch_z=0.4)
    lib.add(piece, [], samples=10, ao=0.5, ao_distance=0.5, ground_z=0.0, seed=703)
    # Cascarón: los muros a media altura, sin cubierta, la estufa en medio y los cabrios caídos.
    rng = random.Random(704)
    mb = tb.MeshBuilder(seed=704)
    _isba_base(mb)
    tops = {side: [rng.uniform(1.1, 2.6) for _ in range(6)] for side in ("-x", "+x", "-y", "+y")}
    _isba_walls(mb, rng, tops=tops, color=LOG_DARK)
    _stove(mb, rng, burnt=True)
    for _ in range(6):
        start = Vector((rng.uniform(-3.5, 3.5), rng.uniform(-3.0, 3.0), BASE))
        mb.box((0.14, rng.uniform(2.5, 4.5), 0.16), start + Vector((0.0, 0.0, 0.5)), CHAR, rotation=(rng.uniform(-35, 35), rng.uniform(-20, 20), rng.uniform(0, 180)), jitter=0.08)
    for _ in range(4):
        mb.box((1.6, 0.9, 0.04), (rng.uniform(-3, 3), rng.uniform(-3, 3), BASE + 0.25), kit.RUST, rotation=(rng.uniform(-25, 25), rng.uniform(-25, 25), rng.uniform(0, 180)), cuts=1)
    with mb.material(2):
        mb.box((L - 0.8, D - 0.8, 0.2), (0.0, 0.0, BASE + 0.1), ASH)
    piece = mb.finish("isba_cascaron", kit.materials("nevado", "vidrio", "interior", "ladrillo"))
    tb.stain(piece, CHAR, amount=0.9, scale=1.0, coverage=0.65, seed=704, stretch_z=0.5)
    lib.add(piece, [], samples=10, ao=0.5, ao_distance=0.6, ground_z=0.0, seed=704)
    # Quemadas del todo: la estufa y la chimenea entre los troncos carbonizados.
    for name, seed, height in (("isba_quemada_a", 705, (0.3, 1.1)), ("isba_quemada_b", 706, (0.0, 0.5))):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        _isba_base(mb)
        tops = {side: [rng.uniform(*height) for _ in range(6)] for side in ("-x", "+x", "-y", "+y")}
        _isba_walls(mb, rng, tops=tops, color=CHAR)
        _stove(mb, rng, chimney_top=RIDGE + 0.4 - (1.2 if seed == 706 else 0.0), burnt=True)
        for _ in range(9):
            centre = Vector((rng.uniform(-4.0, 4.0), rng.uniform(-3.5, 3.5), BASE + 0.2))
            _log(mb, centre - Vector((rng.uniform(0.5, 1.6), 0, 0)), centre + Vector((rng.uniform(0.5, 1.6), rng.uniform(-0.6, 0.6), rng.uniform(-0.1, 0.4))), 0.12, CHAR, rng)
        for _ in range(3):
            mb.box((1.5, 0.9, 0.04), (rng.uniform(-3.5, 3.5), rng.uniform(-3.5, 3.5), BASE + 0.12), kit.RUST, rotation=(rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(0, 180)), cuts=1)
        with mb.material(2):
            mb.box((L - 0.5, D - 0.5, 0.25), (0.0, 0.0, BASE + 0.12), ASH)
        piece = mb.finish(name, kit.materials("nevado", "vidrio", "interior", "ladrillo"))
        tb.stain(piece, CHAR, amount=0.9, scale=1.0, coverage=0.6, seed=seed)
        lib.add(piece, [], samples=10, ao=0.45, ao_distance=0.6, ground_z=0.0, seed=seed)


# --------------------------------------------------------------------------
# El barracón
# --------------------------------------------------------------------------

BL, BD = 30.0, 11.0
B_BASE = 0.5
B_FLOOR = 3.0
B_EAVE = B_BASE + 2 * B_FLOOR
B_RIDGE = 8.5
B_WIN = (1.0, 1.35)


def _barrack_casing(mb: tb.MeshBuilder, opening: tuple) -> None:
    """Recercado de tablas de una ventana, en el marco de su fachada: jambas, cabezal con
    vierteaguas y alféizar. Las caras de arriba y de abajo van inclinadas (kit.moulding)."""
    x0, z0, x1, z1 = opening
    for x in (x0 - 0.06, x1 + 0.06):
        mb.box((0.12, 0.06, z1 - z0 + 0.04), (x, -0.03, (z0 + z1) / 2.0 - 0.02), TRIM)
    kit.moulding(mb, (x0 - 0.15, x1 + 0.15), [(0.0, z1), (-0.09, z1), (-0.09, z1 + 0.12), (0.0, z1 + 0.18)], TRIM)
    kit.moulding(mb, (x0 - 0.16, x1 + 0.16), [(0.0, z0 + 0.01), (-0.11, z0 - 0.04), (-0.11, z0 - 0.08), (0.0, z0 - 0.14)], TRIM)


def _barrack_door(mb: tb.MeshBuilder, x0: float, x1: float, z1: float) -> None:
    """La puerta, en el marco de su fachada: hoja de tablas con su recercado, tejadillo de
    chapa sobre dos tornapuntas y la escalerilla de hormigón: el rellano y dos peldaños, tres
    contrahuellas de 16 cm."""
    middle = (x0 + x1) / 2.0
    mb.box((x1 - x0 - 0.05, 0.05, z1 - B_BASE - 0.02), (middle, 0.12, (B_BASE + z1) / 2.0), DOOR, jitter=0.06)
    for x in (x0 - 0.06, x1 + 0.06):
        mb.box((0.12, 0.06, z1 - B_BASE), (x, -0.03, (B_BASE + z1) / 2.0), TRIM)
    kit.moulding(mb, (x0 - 0.15, x1 + 0.15), [(0.0, z1), (-0.09, z1), (-0.09, z1 + 0.12), (0.0, z1 + 0.18)], TRIM)
    tilt = math.radians(12.0)
    mb.box((x1 - x0 + 0.8, 1.4, 0.05), (middle, -0.7, z1 + 0.45), METAL_ROOF[2], rotation=(12.0, 0.0, 0.0))
    # Las tornapuntas, del muro a la cara de abajo del tejadillo, cerca de su borde.
    top = Vector((0.0, -0.7 - 0.45 * math.cos(tilt), z1 + 0.45 - 0.45 * math.sin(tilt) - 0.03))
    foot = Vector((0.0, 0.02, z1 - 0.55))
    strut = top - foot
    for x in (x0 - 0.22, x1 + 0.22):
        centre = (top + foot) / 2.0 + Vector((x, 0.0, 0.0))
        mb.box((0.08, strut.length, 0.08), centre, PLANK_DARK, rotation=(math.degrees(math.atan2(strut.z, strut.y)) - 180.0, 0.0, 0.0))
    landing = B_BASE - 0.02
    mb.box((x1 - x0 + 0.8, 1.0, landing), (middle, -0.5, landing / 2.0), CONCRETE, cuts=1, jitter=0.04)
    for k, top in enumerate((landing * 2.0 / 3.0, landing / 3.0)):  # huellas de 30 cm
        mb.box((x1 - x0 + 0.6, 0.3, top), (middle, -1.15 - 0.3 * k, top / 2.0), CONCRETE, cuts=1, jitter=0.04)


def _barrack_wall(mb: tb.MeshBuilder, facing: str, length: float, windows: list, doors: list, rng: random.Random) -> None:
    """Un muro de tablas del barracón, con sus ventanas, en el marco de su fachada.

    Los muros largos se quedan a 20 cm de las esquinas: ahí llega el canto de los de los
    piñones (si se solaparan, sus caras coincidirían y titilarían). Sus esquineras, más
    anchas, tapan el canto de las de los piñones."""
    half = {"-y": BD, "+y": BD, "-x": BL, "+x": BL}[facing] / 2.0
    position = {"-y": (0.0, -half, 0.0), "+y": (0.0, half, 0.0), "-x": (-half, 0.0, 0.0), "+x": (half, 0.0, 0.0)}[facing]
    matrix = _facade(position, facing)
    long_side = facing in ("-y", "+y")
    holes = []
    for u in windows:
        for floor in range(2):
            z = B_BASE + floor * B_FLOOR + 0.9
            holes.append((u - B_WIN[0] / 2.0, z, u + B_WIN[0] / 2.0, z + B_WIN[1]))
    for u in doors:
        holes.append((u - 0.6, B_BASE, u + 0.6, B_BASE + 2.2))

    def build(builder: tb.MeshBuilder) -> None:
        reach = length / 2.0 - (0.2 if long_side else 0.0)
        # Tablas lisas con la junta enrasada: vistas de lejos y a ras, cualquier canto
        # asomaría a puntos.
        kit.banded_wall(builder, (-reach, reach), (B_BASE, B_EAVE), (0.0, 0.2), BOARD, holes=holes, band=0.3, gap=0.02, gap_color="#4C362A", step=3.0, ring=0.0)
        for x0, z0, x1, z1 in holes:
            if z0 <= B_BASE + 0.01:
                _barrack_door(builder, x0, x1, z1)
                continue
            state = rng.choice(("rota", "tapiada", "intacta", "vacia", "rota"))
            kit.window(builder, (x0, z0, x1, z1), "cocina", state, rng, depth=0.05, wall=0.2, frame_color="#B7B09B", sill=False)
            if state != "vacia":
                _barrack_casing(builder, (x0, z0, x1, z1))
        wrap = 0.06 if long_side else 0.0
        for side in (-1.0, 1.0):
            builder.box((0.16 + wrap, 0.06, B_EAVE - B_BASE), (side * (length / 2.0 - 0.08 + wrap / 2.0), -0.03, (B_BASE + B_EAVE) / 2.0), TRIM)
            if not long_side:
                # El canto de este muro hace de fachada larga junto a la esquina: entre banda y
                # banda, el hueco de la junta se cierra (2 mm por detrás de las bandas).
                builder.box((0.048, 0.198, B_EAVE - B_BASE), (side * (length / 2.0 - 0.026), 0.101, (B_BASE + B_EAVE) / 2.0), "#4C362A")

    _placed(mb, matrix, build)


def _barrack_gable(mb: tb.MeshBuilder) -> None:
    """El piñón del barracón, en el marco de su fachada: la imposta sobre el muro, los
    tapajuntas y el respiradero del desván, de lamas."""
    slope = (B_RIDGE - B_EAVE) / (BD / 2.0)
    reach = BD / 2.0 + 0.065  # 5 mm por delante de las esquineras de los muros largos
    kit.moulding(mb, (-reach, reach), [(0.0, B_EAVE - 0.12), (-0.08, B_EAVE - 0.07), (-0.08, B_EAVE + 0.02), (0.0, B_EAVE + 0.07)], TRIM)
    x0, z0, x1, z1 = -0.45, B_EAVE + 0.75, 0.45, B_EAVE + 1.3
    for k in range(-8, 9):
        x = k * 0.6
        bottom, top = B_EAVE + 0.07, B_RIDGE - abs(x) * slope - 0.12
        if abs(x) < x1:
            top = min(top, z0 - 0.1)
        if top - bottom > 0.15:
            mb.box((0.06, 0.06, top - bottom), (x, -0.03, (bottom + top) / 2.0), PLANK_DARK)
    with mb.material(2):
        mb.box((x1 - x0, 0.01, z1 - z0), (0.0, -0.005, (z0 + z1) / 2.0), DARK)
    for x in (x0, x1):
        mb.box((0.08, 0.06, z1 - z0), (x, -0.03, (z0 + z1) / 2.0), TRIM)
    kit.moulding(mb, (x0 - 0.08, x1 + 0.08), [(0.0, z1 - 0.04), (-0.08, z1 - 0.04), (-0.08, z1 + 0.06), (0.0, z1 + 0.11)], TRIM)
    kit.moulding(mb, (x0 - 0.08, x1 + 0.08), [(0.0, z0 + 0.04), (-0.08, z0), (-0.08, z0 - 0.04), (0.0, z0 - 0.1)], TRIM)
    for k in range(4):  # lamas caídas hacia fuera
        z = z0 + (k + 0.6) * (z1 - z0) / 4.4
        mb.box((x1 - x0 - 0.08, 0.13, 0.02), (0.0, -0.05, z), TRIM, rotation=(40.0, 0.0, 0.0))


def build_barracks(lib: kit.KitLibrary) -> None:
    rng = random.Random(801)
    mb = tb.MeshBuilder(seed=801)
    bays = [-BL / 2.0 + 1.5 + 3.0 * k for k in range(10)]
    _barrack_wall(mb, "-y", BL, [u for u in bays if abs(u) > 1.0], [0.0], rng)
    _barrack_wall(mb, "+y", BL, bays, [], rng)
    for facing in ("-x", "+x"):
        _barrack_wall(mb, facing, BD, [-3.5, 3.5], [0.0], rng)
    # Cubierta a dos aguas, con los piñones entablados y cuatro chimeneas.
    half = BD / 2.0 + 0.5
    slope = math.atan2(B_RIDGE - B_EAVE, BD / 2.0)
    length = half / math.cos(slope)
    eave_z = B_EAVE - 0.5 * math.tan(slope)
    # La chapa coge nieve (material 0).
    for side in (-1.0, 1.0):
        for k in range(8):
            x0 = -BL / 2.0 - 0.4 + (BL + 0.8) * k / 8
            x1 = -BL / 2.0 - 0.4 + (BL + 0.8) * (k + 1) / 8
            mb.box((x1 - x0 + 0.02, length, 0.05), ((x0 + x1) / 2.0, side * half / 2.0, (eave_z + B_RIDGE) / 2.0 + 0.04), METAL_ROOF[1], rotation=(math.degrees(-side * slope), 0.0, 0.0), jitter=0.04, cuts=1)
    mb.box((BL + 0.9, 0.16, 0.12), (0.0, 0.0, B_RIDGE + 0.06), METAL_ROOF[1])
    for end in (-1.0, 1.0):
        triangle = kit.ccw([(-BD / 2.0, B_EAVE), (BD / 2.0, B_EAVE), (0.0, B_RIDGE - 0.05)])
        mb.prism(triangle, 0.08, (end * (BL / 2.0 - 0.04), 0.0, 0.0), BOARD, rotation=(90.0, 0.0, 90.0), jitter=0.04)
        _placed(mb, _facade((end * BL / 2.0, 0.0, 0.0), "-x" if end < 0 else "+x"), _barrack_gable)
    # El zócalo de hormigón, su vierteaguas de chapa y la imposta entre las plantas dan la
    # vuelta a la casa con las esquinas a inglete. Sus caras de arriba y de abajo van
    # inclinadas: planas y estrechas, se dibujarían a puntos a lo largo de la fachada.
    footprint = (BL / 2.0, BD / 2.0)
    kit.ring(mb, footprint, [(0.06, -0.4), (0.06, B_BASE - 0.052), (-0.2, B_BASE - 0.052)], CONCRETE)
    kit.ring(mb, footprint, [(-0.01, B_BASE - 0.05), (0.13, B_BASE - 0.05), (0.13, B_BASE - 0.01), (-0.01, B_BASE + 0.07)], METAL_ROOF[2])
    belt = B_BASE + B_FLOOR
    kit.ring(mb, footprint, [(-0.01, belt - 0.14), (0.1, belt - 0.08), (0.1, belt + 0.02), (-0.01, belt + 0.08)], TRIM)
    for k in range(4):
        x = -BL / 2.0 + BL * (k + 0.5) / 4
        with mb.material(3):
            mb.box((0.6, 0.6, B_RIDGE - B_EAVE + 1.6), (x, 0.4, (B_EAVE + B_RIDGE + 1.6) / 2.0), BRICK, cuts=2, jitter=0.05)
        mb.box((0.76, 0.76, 0.08), (x, 0.4, B_RIDGE + 1.64), "#5E5A54")
    with mb.material(2):
        mb.box((BL - 0.6, BD - 0.6, 2 * B_FLOOR - 0.4), (0.0, 0.0, B_BASE + B_FLOOR), DARK)
    piece = mb.finish("barracon", kit.materials("nevado", "vidrio", "interior", "ladrillo"))
    tb.stain(piece, "#3A2F27", amount=0.5, scale=0.8, coverage=0.45, seed=801, stretch_z=0.3)
    lib.add(piece, [], samples=8, ao=0.5, ao_distance=0.6, ground_z=0.0, seed=801)
    # Quemado: el zócalo, los postes carbonizados, trozos de tabla y las chimeneas en pie.
    rng = random.Random(802)
    mb = tb.MeshBuilder(seed=802)
    mb.box((BL + 0.1, BD + 0.1, B_BASE + 0.3), (0.0, 0.0, (B_BASE - 0.3) / 2.0), "#5A564F", cuts=3, jitter=0.04)
    for u in [-BL / 2.0 + 3.0 * k for k in range(11)]:
        for y in (-BD / 2.0 + 0.1, BD / 2.0 - 0.1):
            height = rng.uniform(0.4, 4.5) if rng.random() < 0.8 else 0.0
            if height > 0.0:
                mb.box((0.2, 0.2, height), (u, y, B_BASE + height / 2.0), CHAR, rotation=(rng.uniform(-6, 6), rng.uniform(-6, 6), 0.0), jitter=0.08)
    for _ in range(14):
        u = rng.uniform(-BL / 2.0, BL / 2.0)
        y = rng.choice((-BD / 2.0 + 0.1, BD / 2.0 - 0.1))
        mb.box((rng.uniform(0.8, 2.5), 0.05, rng.uniform(0.3, 1.0)), (u, y, B_BASE + rng.uniform(0.2, 1.2)), CHAR, rotation=(0.0, rng.uniform(-20, 20), 0.0), jitter=0.1)
    for k in range(4):
        x = -BL / 2.0 + BL * (k + 0.5) / 4
        with mb.material(3):
            mb.box((1.3, 1.1, 1.6), (x, 0.4, B_BASE + 0.8), BRICK, cuts=2, jitter=0.05)
            mb.box((0.6, 0.6, B_RIDGE - B_BASE - 0.5), (x, 0.4, (B_BASE + B_RIDGE + 1.1) / 2.0), BRICK, cuts=3, jitter=0.05)
        mb.box((0.76, 0.76, 0.08), (x, 0.4, B_RIDGE + 0.6), "#5E5A54")
    for _ in range(18):
        centre = Vector((rng.uniform(-BL / 2.0 + 1, BL / 2.0 - 1), rng.uniform(-BD / 2.0 + 1, BD / 2.0 - 1), B_BASE + 0.2))
        _log(mb, centre - Vector((rng.uniform(0.6, 2.0), 0, 0)), centre + Vector((rng.uniform(0.6, 2.0), rng.uniform(-0.8, 0.8), rng.uniform(-0.1, 0.5))), 0.1, CHAR, rng)
    for _ in range(6):
        mb.box((2.0, 1.0, 0.04), (rng.uniform(-BL / 2.0 + 2, BL / 2.0 - 2), rng.uniform(-3.5, 3.5), B_BASE + 0.3), kit.RUST, rotation=(rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(0, 180)), cuts=1)
    with mb.material(2):
        mb.box((BL - 0.5, BD - 0.5, 0.3), (0.0, 0.0, B_BASE + 0.15), ASH)
    piece = mb.finish("barracon_quemado", kit.materials("nevado", "vidrio", "interior", "ladrillo"))
    tb.stain(piece, CHAR, amount=0.85, scale=0.9, coverage=0.6, seed=802)
    lib.add(piece, [], samples=8, ao=0.45, ao_distance=0.6, ground_z=0.0, seed=802)


def build_kit() -> object:
    lib = kit.KitLibrary("kit_madera", columns=4, spacing=36.0)
    build_isbas(lib)
    build_barracks(lib)
    return lib.root


def models() -> dict:
    return {"kit_madera": build_kit}
