"""Edificios singulares: la Casa de los Sóviets (CEN-SOV) y su torre (CEN-SOVT).

La sede del antiguo gobierno de la ciudad, sin copiar ninguna real: un bloque estalinista de
100 × 60 m y diez plantas alrededor de dos patios, que cierra la perspectiva de la avenida.
Basamento de granito almohadillado de dos plantas; encima, un orden gigante de pilastras, el
entablamento, el ático y la balaustrada; los cuerpos de las esquinas, un poco adelantados y
más altos. En el centro de la fachada suroeste, la que mira a la plaza y a la avenida, un
pórtico de ocho columnas gigantes y, en lo alto, el escudo (el globo, la hoz y el martillo,
las espigas y la estrella). En medio del bloque se levanta la torre: tres cuerpos que se
estrechan hasta 94 m y la aguja con su estrella, hasta 110.

Ardió entera (incendio total): las ventanas negras con el hollín encima, el revoque caído,
dentro solo oscuridad. La onda reventó la fachada noreste, la que mira a la bomba: un
boquete de muchas plantas con los forjados colgando y el escombro dentro. La torre (daño 4)
perdió trozos del lado de la bomba y la aguja quedó doblada hacia el suroeste. En la planta
20, en la ventana que mira al río (al sur), el puesto del vigía de los saqueadores: sacos,
tablas y una lona.

Coordenadas: las del plano, con el origen en el «centro» de los dos (el mismo) y a su cota.
Se construye en un marco propio: u a lo largo de la fachada principal (hacia el sureste), v
de través (hacia el noreste: la dirección de la avenida) y z arriba; ``_to_plan`` lo gira.

Modelos (KitSingular): "soviets" (el bloque: una pieza por fachada de fuera, una por patio,
"soviets" con las esquinas, el pórtico y lo de dentro, "soviets_boquete" y
"soviets_colision") y "torre_soviets" (la torre: un cuerpo por pieza, "torre_soviets_aguja",
"torre_soviets_vigia" y "torre_soviets_colision").
"""

from __future__ import annotations

import math
import random

from mathutils import Matrix, Vector, noise

import kit_bpy as kit
import tumansk_bpy as tb

TURN = math.radians(-42.0)  # la dirección de u en el plano (la de la fachada principal)
HALF_U, HALF_V = 50.0, 30.0  # el bloque: 100 × 60 m
WING = 14.0  # el fondo de las alas
CENTRAL = 14.0  # medio ancho del cuerpo central (el de la torre)
BAY = 4.0
BASE_TOP = 9.0  # el basamento: dos plantas
GROUND = 5.0  # la planta baja
STOREY = 4.0
ORDER_TOP = 33.0  # lo alto del orden gigante
ATTIC = 37.0  # el arranque del ático
ROOF = 40.5
TOP = 42.0  # lo alto de la balaustrada
WALL = 0.7
CORNER_BAYS = 3  # los cuerpos de las esquinas, adelantados
CORNER_STEP = 0.8
PORTICO = 14.0  # medio ancho del pórtico (siete vanos)
BREACH = (-26.0, 10.0)  # el boquete de la fachada noreste (en u)
# Las alturas de las ventanas de cada planta (z0, z1) y su ancho.
ROWS = [(1.2, 4.2), (5.9, 8.0)] + [(BASE_TOP + 0.9 + STOREY * k, BASE_TOP + 3.3 + STOREY * k) for k in range(7)] + [(ATTIC + 0.9, ATTIC + 2.4)]
WINDOW_HALF = 0.9

# La torre: cuerpos (radio, de z0 a z1, lados) y la aguja.
TIERS = ((14.0, 40.0, 70.0, 24), (10.5, 70.0, 86.0, 16), (7.5, 86.0, 94.0, 8))
SPIRE = (94.0, 110.0)
BEND = (101.0, 34.0)  # dónde se dobla la aguja (z) y cuántos grados, hacia el suroeste
LOOKOUT = -math.pi / 4.0  # el lado del cuerpo medio que mira al río (al sur), en el marco (u, v)
BOMB = math.radians(51.0)  # hacia la zona cero, en el marco (u, v)

# Colores (sRGB).
GRANITE = "#57524D"
STUCCO = "#B39C78"
DETAIL = "#C8B996"
SOOT = "#191614"
DARK = "#151311"
CHAR = "#201C19"
CONCRETE = "#77726B"
BRONZE = "#6E5A3C"
RUBY = "#7A2B25"
COPPER = "#4F5C53"


# --------------------------------------------------------------------------
# Marcos y geometría auxiliar
# --------------------------------------------------------------------------


def _to_plan(mb: tb.MeshBuilder) -> None:
    kit.transform_faces(list(mb.bm.faces), Matrix.Rotation(TURN, 4, "Z"))


def _from_plan(position: Vector) -> Vector:
    return Matrix.Rotation(-TURN, 3, "Z") @ Vector(position)


def _placed(mb: tb.MeshBuilder, matrix: Matrix, build) -> None:
    before = set(mb.bm.faces)
    build(mb)
    kit.transform_faces([f for f in mb.bm.faces if f not in before], matrix)


def _facing(mb: tb.MeshBuilder, corners: list, color: str, outward: Vector, *, cuts: int = 0) -> None:
    a, b, c = (Vector(p) for p in corners[:3])
    if (b - a).cross(c - b).dot(Vector(outward)) < 0.0:
        corners = corners[::-1]
    mb.quad(corners, color, cuts=cuts)


def _frame(origin: tuple, normal: tuple) -> Matrix:
    """El marco de una fachada: x a lo largo (de izquierda a derecha, vista desde fuera), y
    hacia dentro y z arriba, con el origen en su plano (``normal`` mira afuera)."""
    n = Vector((normal[0], normal[1], 0.0)).normalized()
    x = Vector((0.0, 0.0, 1.0)).cross(n)
    return Matrix(((x.x, -n.x, 0.0, origin[0]), (x.y, -n.y, 0.0, origin[1]), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _soot(mb: tb.MeshBuilder, faces: list, sources: list, height: float = 3.2) -> None:
    """Hollín de las ventanas quemadas en el color base de unas caras (en el marco de su
    fachada): cada fuente (x, z, ancho) sube desde un dintel, se abre y se apaga."""
    target = Vector(int(SOOT[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
    buckets: dict = {}
    for source in sources:
        buckets.setdefault(math.floor(source[0] / 2.0), []).append(source)
    for face in faces:
        for loop in face.loops:
            co = loop.vert.co
            weight = 0.0
            key = math.floor(co.x / 2.0)
            for x, z, width in buckets.get(key - 1, []) + buckets.get(key, []) + buckets.get(key + 1, []):
                rise = co.z - z
                if rise < -0.3 or rise > height or abs(co.x - x) > width * 1.4:
                    continue
                spread = width * (0.5 + 0.45 * max(rise, 0.0) / height)
                side = abs(co.x - x) / spread + 0.3 * noise.noise(Vector((co.x * 1.9, co.z * 0.7, x)))
                weight = max(weight, (1.0 - max(rise, 0.0) / height) * max(0.0, 1.0 - side * side))
            if weight > 0.0:
                base = Vector(loop[mb.base][:3])
                loop[mb.base] = (*base.lerp(target, min(1.0, 0.95 * weight)), 1.0)


def _star_points(radius: float, inner: float, center: tuple, turn: float = 0.0) -> list:
    cx, cz = center
    return [
        (cx + (radius if i % 2 == 0 else inner) * math.cos(math.pi / 2.0 + turn + i * math.pi / 5.0),
         cz + (radius if i % 2 == 0 else inner) * math.sin(math.pi / 2.0 + turn + i * math.pi / 5.0))
        for i in range(10)
    ]


def _arc_band(mb: tb.MeshBuilder, center: tuple, radius: float, width: float, a0: float, a1: float, depth: float, color: str, *, splay: float = 0.04, samples: int = 24) -> None:
    """Una banda en arco en relieve, de una pieza (la hoz, las espigas): el canto de fuera y
    el de dentro en derrame, la cara de delante y los extremos (en el marco de un muro: la
    cara en y = 0 y lo de fuera hacia -y)."""
    cx, cz = center
    rails = ((radius + splay, 0.0), (radius, depth), (radius - width, depth), (radius - width - splay, 0.0))

    def point(a: float, r: float, d: float) -> tuple:
        return (cx + r * math.cos(a), -d, cz + r * math.sin(a))

    for i in range(samples):
        t0, t1 = a0 + (a1 - a0) * i / samples, a0 + (a1 - a0) * (i + 1) / samples
        mid = (t0 + t1) / 2.0
        radial = Vector((math.cos(mid), 0.0, math.sin(mid)))
        for k, outward in enumerate((radial + Vector((0, -1, 0)), Vector((0, -1, 0)), -radial + Vector((0, -1, 0)))):
            (r0, d0), (r1, d1) = rails[k], rails[k + 1]
            _facing(mb, [point(t0, r0, d0), point(t1, r0, d0), point(t1, r1, d1), point(t0, r1, d1)], color, outward)
    for a, sign in ((a0, -1.0), (a1, 1.0)):  # los extremos, cerrados
        tangent = Vector((-math.sin(a), 0.0, math.cos(a))) * sign * (1.0 if a1 > a0 else -1.0)
        corners = [point(a, r, d) for r, d in (rails[0], rails[1], rails[2], rails[3])]
        _facing(mb, corners, color, tangent + Vector((0, -0.3, 0)))


# --------------------------------------------------------------------------
# El bloque: fachadas
# --------------------------------------------------------------------------


def _facades() -> list:
    """Las fachadas del bloque: (nombre, origen, normal, largo, exterior). Las de fuera
    llevan orden gigante; las de los patios, solo ventanas."""
    result = [
        ("suroeste", (0.0, -HALF_V), (0.0, -1.0), 2.0 * HALF_U, True),
        ("noreste", (0.0, HALF_V), (0.0, 1.0), 2.0 * HALF_U, True),
        ("noroeste", (-HALF_U, 0.0), (-1.0, 0.0), 2.0 * HALF_V, True),
        ("sureste", (HALF_U, 0.0), (1.0, 0.0), 2.0 * HALF_V, True),
    ]
    inner = HALF_V - WING
    for sign in (-1.0, 1.0):
        u_near, u_far = sign * CENTRAL, sign * (HALF_U - WING)
        middle = (u_near + u_far) / 2.0
        length = abs(u_far - u_near)
        result += [
            ("patio", (middle, -inner), (0.0, 1.0), length, False),
            ("patio", (middle, inner), (0.0, -1.0), length, False),
            ("patio", (u_far, 0.0), (-sign, 0.0), 2.0 * inner, False),
            ("patio", (u_near, 0.0), (sign, 0.0), 2.0 * inner, False),
        ]
    return result


def _openings(name: str, length: float, exterior: bool) -> list:
    """Los huecos de una fachada (x0, z0, x1, z1), vano a vano y planta a planta; en la
    principal, las tres puertas del pórtico."""
    holes = []
    bays = int(length // BAY)
    rows = ROWS if exterior else ROWS[1:-1]
    for b in range(bays):
        x = -bays * BAY / 2.0 + (b + 0.5) * BAY  # los vanos, centrados en el muro
        for z0, z1 in rows:
            if name == "suroeste" and abs(x) < PORTICO and z1 < BASE_TOP:
                continue  # el basamento del pórtico, con sus puertas
            holes.append((x - WINDOW_HALF, z0, x + WINDOW_HALF, z1))
    if name == "suroeste":
        for x in (-4.0, 0.0, 4.0):
            holes.append((x - 1.2, 0.0, x + 1.2, 5.2))
    return holes


def _facade_wall(mb: tb.MeshBuilder, name: str, length: float, exterior: bool, rng: random.Random) -> list:
    """El muro de una fachada con sus huecos, el hollín encima de cada uno y, en la
    noreste, el boquete. Devuelve los huecos."""
    holes = _openings(name, length, exterior)
    top = TOP if exterior else ROOF
    before = set(mb.bm.faces)
    with mb.material(3):
        mb.slab((-length / 2.0, length / 2.0), (-0.3, top), (0.0, WALL), STUCCO, holes=holes + _gaps(name), step=1.5 if exterior else 2.0, jitter=0.02)
    faces = [f for f in mb.bm.faces if f not in before]
    sources = [((h[0] + h[2]) / 2.0, h[3], h[2] - h[0]) for h in holes if rng.random() < 0.85]
    _soot(mb, faces, sources)
    return holes


def _gaps(name: str) -> list:
    """Lo que falta de una fachada (x0, z0, x1, z1): el boquete de la noreste."""
    if name == "noreste":
        return [(-BREACH[1], BASE_TOP - 0.5, -BREACH[0], TOP + 5.0)]
    return []


def _run(mb: tb.MeshBuilder, length: float, profile: list, color: str, name: str, *, corner: bool = True) -> None:
    """Una moldura corrida a lo largo de una fachada, partida por el boquete, con su
    esquina a inglete en el extremo izquierdo (cada fachada pone la suya)."""
    z_low, z_high = min(z for _, z in profile), max(z for _, z in profile)
    cuts = [g for g in _gaps(name) if g[1] < z_high and g[3] > z_low]
    kit.moulding_run(mb, (-length / 2.0, length / 2.0), profile, color, holes=cuts, jitter=0.02)
    if corner:
        _placed(mb, Matrix.Translation((-length / 2.0, 0.0, 0.0)), lambda b: kit.corner(b, profile, color))


def _rustication(mb: tb.MeshBuilder, length: float, holes: list, name: str) -> None:
    """El almohadillado del basamento: hiladas de granito de 60 cm con las juntas en V (los
    cantos en derrame), partidas por los huecos."""
    z = 0.0
    while z < BASE_TOP - 0.05:
        profile = [(0.0, z + 0.02), (-0.07, z + 0.09), (-0.07, z + 0.51), (0.0, z + 0.58)]
        cuts = [h for h in holes if h[1] < z + 0.6 and h[3] > z]
        kit.moulding_run(mb, (-length / 2.0, length / 2.0), profile, GRANITE, holes=cuts, jitter=0.03)
        z += 0.6
    _run(mb, length, [(0.0, BASE_TOP - 0.05), (-0.25, BASE_TOP + 0.05), (-0.25, BASE_TOP + 0.25), (0.0, BASE_TOP + 0.45)], GRANITE, name)


def _order(mb: tb.MeshBuilder, length: float, name: str) -> None:
    """El orden gigante: pilastras entre los vanos, del basamento al entablamento, con su basa
    y su capitel; el entablamento y la cornisa; el ático y la balaustrada."""
    bays = int(round(length / BAY))
    gaps = _gaps(name)
    for b in range(bays + 1):
        x = -length / 2.0 + b * BAY
        if name == "suroeste" and abs(x) < PORTICO + 0.1 or any(g[0] - 0.7 < x < g[2] + 0.7 for g in gaps):
            continue
        kit.block(mb, (x - 0.45, BASE_TOP + 0.45, x + 0.45, ORDER_TOP - 0.9), 0.32, DETAIL, splay=0.05)
        kit.block(mb, (x - 0.58, BASE_TOP + 0.45, x + 0.58, BASE_TOP + 1.0), 0.4, DETAIL, splay=0.05)
        kit.block(mb, (x - 0.62, ORDER_TOP - 0.9, x + 0.62, ORDER_TOP), 0.42, DETAIL, splay=0.06)
    _run(mb, length, [(0.0, ORDER_TOP), (-0.45, ORDER_TOP + 0.05), (-0.45, ORDER_TOP + 1.2), (-0.38, ORDER_TOP + 1.3), (0.0, ORDER_TOP + 1.35)], DETAIL, name)
    cornice = [(0.0, ATTIC - 1.6), (-0.4, ATTIC - 1.5), (-1.2, ATTIC - 0.6), (-1.2, ATTIC - 0.2), (-0.9, ATTIC + 0.05), (0.0, ATTIC + 0.25)]
    _run(mb, length, cornice, DETAIL, name)
    # La balaustrada: plinto, balaustres y pasamanos, partida en tramos por pedestales.
    _run(mb, length, [(0.0, ROOF), (-0.2, ROOF + 0.05), (-0.2, ROOF + 0.25), (0.0, ROOF + 0.3)], DETAIL, name)
    for b in range(bays):
        x0, x1 = -length / 2.0 + b * BAY + 0.4, -length / 2.0 + (b + 1) * BAY - 0.4
        if any(g[0] < x1 and x0 < g[2] for g in gaps):
            continue
        kit.balusters(mb, Vector((x0, -0.12, 0.0)), Vector((x1, -0.12, 0.0)), ROOF + 0.3, 0.95, DETAIL, spacing=0.38, segments=5)
    for b in range(bays + 1):
        x = -length / 2.0 + b * BAY
        if not any(g[0] - 0.4 < x < g[2] + 0.4 for g in gaps):
            mb.box((0.7, 0.5, TOP - ROOF + 0.1), (x, 0.0, (ROOF + TOP) / 2.0), DETAIL, jitter=0.02)
    _run(mb, length, [(0.05, TOP - 0.2), (-0.25, TOP - 0.15), (-0.25, TOP + 0.02), (0.05, TOP + 0.1)], DETAIL, name, corner=False)


def _window_dressing(mb: tb.MeshBuilder, holes: list, exterior: bool, rng: random.Random) -> None:
    """Recercados y alféizares; frontones sobre las ventanas de la planta noble; las
    carpinterías quemadas o vacías. En los patios, nada: los huecos quedan negros."""
    if not exterior:
        return  # los patios ardieron por dentro: huecos negros, sin carpintería ni recercado
    for x0, z0, x1, z1 in holes:
        if z1 <= BASE_TOP:
            kit.outline(mb, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], [(0.0, 0.0), (0.0, 0.12), (0.14, 0.12), (0.2, 0.0)], GRANITE, step=3.0)
        else:
            kit.outline(mb, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], [(0.0, 0.0), (0.0, 0.08), (0.1, 0.08), (0.14, 0.0)], DETAIL, step=3.0)
            kit.moulding(mb, (x0 - 0.25, x1 + 0.25), [(0.0, z0 - 0.05), (-0.16, z0 - 0.08), (-0.16, z0 - 0.16), (0.0, z0 - 0.26)], DETAIL, mitre=True)
        if exterior and abs(z0 - ROWS[2][0]) < 0.01:  # la planta noble: frontón triangular
            peak = [(x0 - 0.35, z1 + 0.25), (x1 + 0.35, z1 + 0.25), ((x0 + x1) / 2.0, z1 + 0.85)]
            kit.raised(mb, peak, 0.18, DETAIL, splay=0.05)
        state = rng.choice(("quemada", "quemada", "quemada", "vacia", "vacia"))
        kind = "portal" if z0 < 0.5 else "alta"
        with mb.material(0):
            kit.window(mb, (x0, z0, x1, z1), kind, state, rng, depth=0.2, wall=WALL, frame_color="#3A2E24", sill=False)


def _liner(mb: tb.MeshBuilder, u0: float, u1: float, v0: float, v1: float, z0: float, z1: float) -> None:
    """Lo de dentro de un ala quemada: una caja oscura vista desde dentro (por las ventanas
    solo se ve negro)."""
    corners = {
        "abajo": [(u0, v0, z0), (u1, v0, z0), (u1, v1, z0), (u0, v1, z0)],
        "arriba": [(u0, v0, z1), (u1, v0, z1), (u1, v1, z1), (u0, v1, z1)],
        "u0": [(u0, v0, z0), (u0, v1, z0), (u0, v1, z1), (u0, v0, z1)],
        "u1": [(u1, v0, z0), (u1, v1, z0), (u1, v1, z1), (u1, v0, z1)],
        "v0": [(u0, v0, z0), (u1, v0, z0), (u1, v0, z1), (u0, v0, z1)],
        "v1": [(u0, v1, z0), (u1, v1, z0), (u1, v1, z1), (u0, v1, z1)],
    }
    inward = {"abajo": (0, 0, 1), "arriba": (0, 0, -1), "u0": (1, 0, 0), "u1": (-1, 0, 0), "v0": (0, 1, 0), "v1": (0, -1, 0)}
    for key, quad in corners.items():
        _facing(mb, quad, DARK if key != "abajo" else CHAR, Vector(inward[key]), cuts=3)


def _wings(mb: tb.MeshBuilder) -> None:
    """Las cajas oscuras de las alas (menos donde está el boquete) y los tejados."""
    inset = WALL + 1.2
    inner = HALF_V - WING
    boxes = [
        (-HALF_U + inset, HALF_U - inset, -HALF_V + inset, -inner - 0.3),
        (-HALF_U + inset, BREACH[0], inner + 0.3, HALF_V - inset),
        (BREACH[1], HALF_U - inset, inner + 0.3, HALF_V - inset),
        (-HALF_U + inset, -HALF_U + WING - 0.3, -inner + 0.3, inner - 0.3),
        (HALF_U - WING + 0.3, HALF_U - inset, -inner + 0.3, inner - 0.3),
        (-CENTRAL + 0.3, CENTRAL - 0.3, -inner + 0.3, inner - 0.3),
    ]
    for u0, u1, v0, v1 in boxes:
        _liner(mb, u0, u1, v0, v1, 0.2, ROOF - 0.3)
    # Los tejados planos, detrás de la balaustrada (en el boquete, nada).
    with mb.material(0):
        for u0, u1, v0, v1 in (
            (-HALF_U, HALF_U, -HALF_V, -inner), (-HALF_U, BREACH[0], inner, HALF_V), (BREACH[1], HALF_U, inner, HALF_V),
            (-HALF_U, -HALF_U + WING, -inner, inner), (HALF_U - WING, HALF_U, -inner, inner), (-CENTRAL, CENTRAL, -inner, inner),
        ):
            _facing(mb, [(u0, v0, ROOF), (u1, v0, ROOF), (u1, v1, ROOF), (u0, v1, ROOF)], "#4E4944", Vector((0, 0, 1)), cuts=4)


def _portico(mb: tb.MeshBuilder) -> None:
    """El pórtico de la fachada principal: ocho columnas gigantes, del suelo al entablamento,
    delante de las tres puertas; su entablamento y el ático con el escudo."""
    v = -HALF_V - 3.2
    for k in range(8):
        u = -PORTICO + k * (2.0 * PORTICO / 7.0)
        profile = [  # del suelo al entablamento: plinto, basa, fuste con éntasis y capitel
            (0.0, 0.0), (1.7, 0.0), (1.7, 0.9), (1.5, 1.1), (1.5, 1.4), (1.25, 1.65), (1.24, 10.0),
            (1.06, ORDER_TOP - 2.4), (1.0, ORDER_TOP - 2.2), (1.08, ORDER_TOP - 2.05), (1.35, ORDER_TOP - 1.0),
            (1.62, ORDER_TOP - 0.6), (1.62, ORDER_TOP), (0.0, ORDER_TOP),
        ]
        mb.lathe(profile, (u, v, 0.0), DETAIL, segments=24, sharp_angle=35.0, jitter=0.02)
    # El entablamento que vuela sobre las columnas, metido en la fachada.
    mb.box((2.0 * PORTICO + 3.0, 4.6, ATTIC - ORDER_TOP), (0.0, v + 1.0, (ORDER_TOP + ATTIC) / 2.0), DETAIL, jitter=0.02)
    mb.box((2.0 * PORTICO + 3.6, 5.4, 0.5), (0.0, v + 1.1, ATTIC - 0.1), DETAIL, jitter=0.02)
    # El ático del escudo, más alto que la balaustrada.
    _placed(mb, Matrix.Translation((0.0, v - 0.9, 0.0)), lambda b: b.slab((-9.0, 9.0), (ATTIC, 46.5), (0.0, 3.0), DETAIL, step=1.5, jitter=0.02))
    _placed(mb, Matrix.Translation((0.0, v - 0.9, 0.0)), _arms)


def _arms(mb: tb.MeshBuilder) -> None:
    """El escudo, en relieve sobre el ático (en el marco de su cara: y = 0, lo de fuera
    hacia -y): el globo con sus paralelos, la hoz y el martillo, las dos gavillas de espigas,
    la cinta y la estrella."""
    cx, cz = 0.0, 41.6
    mb.lathe([(2.3, 0.0), (2.15, 0.25), (1.9, 0.38), (0.0, 0.42)], (cx, 0.0, cz), BRONZE, rotation=(90.0, 0.0, 0.0), segments=32, sharp_angle=35.0)
    for k in (-1.0, 1.0):  # dos paralelos del globo
        center = -90.0 if k > 0 else 90.0
        _arc_band(mb, (cx, cz + k * 3.2), 3.9, 0.1, math.radians(center - 32.0), math.radians(center + 32.0), 0.46, BRONZE, splay=0.02)
    # La hoz: un arco abierto con su mango; el martillo, cruzado.
    _arc_band(mb, (cx + 0.2, cz + 0.2), 1.45, 0.32, math.radians(-30.0), math.radians(200.0), 0.62, RUBY, samples=28)
    kit.raised(mb, [(cx - 1.25, cz - 0.6), (cx - 0.95, cz - 0.75), (cx - 1.75, cz - 1.7), (cx - 2.05, cz - 1.55)], 0.62, RUBY, splay=0.04)
    kit.raised(mb, [(cx - 1.0, cz - 1.25), (cx - 0.75, cz - 1.45), (cx + 1.25, cz + 1.0), (cx + 1.0, cz + 1.2)], 0.7, RUBY, splay=0.04)
    kit.raised(mb, [(cx + 0.55, cz + 1.05), (cx + 1.25, cz + 0.4), (cx + 1.75, cz + 0.95), (cx + 1.05, cz + 1.6)], 0.74, RUBY, splay=0.04)
    # Las gavillas: dos arcos de espigas a los lados.
    for sign in (-1.0, 1.0):
        a0, a1 = (math.radians(200.0), math.radians(110.0)) if sign < 0 else (math.radians(-20.0), math.radians(70.0))
        _arc_band(mb, (cx, cz - 0.4), 3.4, 0.55, a0, a1, 0.3, BRONZE, samples=20)
        for k in range(7):
            t = a0 + (a1 - a0) * (k + 0.5) / 7.0
            px, pz = cx + 3.6 * math.cos(t), cz - 0.4 + 3.6 * math.sin(t)
            kit.raised(mb, [(px - 0.18, pz - 0.18), (px + 0.18, pz - 0.18), (px + 0.18, pz + 0.18), (px - 0.18, pz + 0.18)], 0.36, BRONZE, splay=0.05)
    # La cinta de abajo y la estrella de arriba.
    kit.raised(mb, [(cx - 3.2, cz - 3.4), (cx + 3.2, cz - 3.4), (cx + 2.6, cz - 2.7), (cx - 2.6, cz - 2.7)], 0.28, RUBY, splay=0.04)
    kit.raised(mb, _star_points(0.9, 0.38, (cx, cz + 3.4)), 0.34, RUBY, splay=0.03)


def _corners(mb: tb.MeshBuilder) -> None:
    """Los cuerpos de las esquinas: un ático escalonado más alto que la balaustrada."""
    for su in (-1.0, 1.0):
        for sv in (-1.0, 1.0):
            u0 = su * HALF_U
            u1 = su * (HALF_U - CORNER_BAYS * BAY)
            lo, hi = sorted((u0, u1))
            v = sv * HALF_V
            mb.box((hi - lo + 2.0 * CORNER_STEP + 0.6, 2.0 * CORNER_STEP + 0.6, 2.2), ((lo + hi) / 2.0, v, TOP + 1.1), DETAIL, jitter=0.02)
            mb.box((hi - lo + 2.0 * CORNER_STEP - 1.2, 2.0 * CORNER_STEP - 0.6, 1.4), ((lo + hi) / 2.0, v, TOP + 2.9), DETAIL, jitter=0.02)


def _breach(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """El boquete de la fachada noreste: los forjados rotos que asoman de los muros que
    quedan, colgando, con la ferralla; el muro del patio al fondo, quemado; vigas
    carbonizadas; el escombro amontonado dentro."""
    u0, u1 = BREACH
    inner = HALF_V - WING
    for k in range(8):
        z = BASE_TOP + STOREY * k
        for side, u in ((1.0, u0), (-1.0, u1)):
            reach = rng.uniform(1.5, 5.0)
            edge = kit.broken_edge(inner + 0.4, HALF_V - 0.6, reach - 0.8, reach + 0.6, rng, step=0.6)
            outline = kit.ccw([(0.0, inner + 0.4), *[(d, v) for v, d in edge], (0.0, HALF_V - 0.6)])
            before = set(mb.bm.faces)
            mb.prism(outline, 0.25, (0.0, 0.0, -0.125), CHAR, jitter=0.05)
            hang = Matrix.Translation((u, 0.0, z)) @ Matrix.Rotation(math.radians(rng.uniform(5.0, 35.0)) * side, 4, "Y") @ Matrix.Scale(side, 4, Vector((1.0, 0.0, 0.0)))
            faces = [f for f in mb.bm.faces if f not in before]
            kit.transform_faces(faces, hang)
            if side < 0.0:
                mb.flip(faces)  # el espejo les da la vuelta
            for _ in range(3):
                start = (u + side * reach * rng.uniform(0.6, 1.0), rng.uniform(inner + 1.0, HALF_V - 1.0), z - 0.2)
                kit.rebar(mb, start, (side, rng.uniform(-0.3, 0.3), -0.6), rng.uniform(0.5, 1.2), rng, radius=0.014)
    # Lo que deja ver el boquete: la cabeza del cuerpo central y los muros de través del ala
    # que queda a los lados, quemados, con sus huecos.
    walls = [
        ((max(u0, -CENTRAL) + min(u1, CENTRAL)) / 2.0, inner, (0.0, 1.0), min(u1, CENTRAL) - max(u0, -CENTRAL)),
        (u0, (inner + HALF_V) / 2.0, (1.0, 0.0), HALF_V - inner - WALL),
        (u1, (inner + HALF_V) / 2.0, (-1.0, 0.0), HALF_V - inner - WALL),
    ]
    for uc, vc, normal, length in walls:

        def build(builder: tb.MeshBuilder, length=length) -> None:
            holes = []
            for k in range(8):
                z = BASE_TOP + STOREY * k
                for i in range(int((length - 2.0) // 4.0) + 1):
                    x = -length / 2.0 + 2.0 + 4.0 * i
                    if rng.random() < 0.8:
                        holes.append((x - 0.6, z + 0.2, x + 0.6, z + 2.4))
            builder.slab((-length / 2.0, length / 2.0), (0.0, ROOF), (0.0, 0.4), CHAR, holes=holes, step=2.0, jitter=0.05)

        _placed(mb, _frame((uc, vc), normal), build)
    for _ in range(14):  # vigas carbonizadas cruzadas
        a = Vector((rng.uniform(u0 + 1.0, u1 - 1.0), rng.uniform(inner + 1.0, HALF_V - 1.0), rng.uniform(BASE_TOP, 30.0)))
        b = a + Vector((rng.uniform(-4.0, 4.0), rng.uniform(-3.0, 3.0), rng.uniform(-6.0, -1.0)))
        mb.box(((b - a).length, 0.3, 0.4), (a + b) / 2.0, CHAR, rotation=[math.degrees(r) for r in Vector((1, 0, 0)).rotation_difference((b - a).normalized()).to_euler()], jitter=0.08)
    # El montón dentro.
    for k in range(260):
        u = rng.uniform(u0 + 0.5, u1 - 0.5)
        v = rng.uniform(inner + 0.5, HALF_V + 4.0)
        height = 9.0 * max(0.0, 1.0 - abs(v - (HALF_V - 2.0)) / 9.0) * (0.6 + 0.4 * math.sin(math.pi * (u - u0) / (u1 - u0)))
        kit.chunk(mb, (u, v, rng.uniform(0.0, height)), rng.uniform(0.4, 1.1), rng.choice((CONCRETE, CHAR, "#6E5848", STUCCO)), rng)


def _block_outline_collision(mb: tb.MeshBuilder) -> None:
    """La colisión del bloque: los muros de fuera y de los patios (macizos), el pórtico y
    el escombro del boquete, como una rampa."""
    inner = HALF_V - WING
    for v in (-HALF_V + WALL / 2.0, HALF_V - WALL / 2.0):
        mb.box((2.0 * HALF_U, WALL, TOP + 0.3), (0.0, v, (TOP - 0.3) / 2.0), CONCRETE)
    for u in (-HALF_U + WALL / 2.0, HALF_U - WALL / 2.0):
        mb.box((WALL, 2.0 * HALF_V, TOP + 0.3), (u, 0.0, (TOP - 0.3) / 2.0), CONCRETE)
    for sign in (-1.0, 1.0):
        u_near, u_far = sign * CENTRAL, sign * (HALF_U - WING)
        lo, hi = sorted((u_near, u_far))
        mb.box((hi - lo, 2.0 * inner, ROOF), ((lo + hi) / 2.0, 0.0, ROOF / 2.0), CONCRETE)  # el patio: macizo hasta el tejado
    for k in range(8):
        u = -PORTICO + k * (2.0 * PORTICO / 7.0)
        mb.cylinder(1.5, ORDER_TOP, (u, -HALF_V - 3.2, ORDER_TOP / 2.0), CONCRETE, segments=8)


# --------------------------------------------------------------------------
# La torre
# --------------------------------------------------------------------------


def _tier(mb: tb.MeshBuilder, radius: float, z0: float, z1: float, sides: int, rng: random.Random, tier: int) -> None:
    """Un cuerpo de la torre: un polígono de ``sides`` lados con una ventana por lado y
    planta, pilastras en las esquinas y su cornisa; del lado de la bomba (+v) le faltan
    trozos."""
    half = math.pi / sides
    apothem = radius * math.cos(half)
    width = 2.0 * radius * math.sin(half)
    floors = max(1, int(round((z1 - z0) / STOREY)))
    for k in range(sides):
        angle = 2.0 * math.pi * k / sides
        facing_bomb = math.cos(angle - BOMB) > 0.6
        holes = []
        sources = []
        for f in range(floors):
            fz = z0 + f * (z1 - z0) / floors
            if tier == 2:
                holes.append((-width * 0.22, fz + 1.0, width * 0.22, z1 - 1.0))
                break
            holes.append((-width * 0.2, fz + 1.0, width * 0.2, fz + 3.0))
            sources.append((0.0, fz + 3.0, width * 0.4))
        damage = []
        if facing_bomb and tier < 2 and rng.random() < 0.7:
            f = rng.randrange(max(1, floors - 1))
            fz = z0 + f * (z1 - z0) / floors
            damage.append((-width / 2.0 + 0.25, fz + 0.6, width / 2.0 - 0.25, min(z1 - 0.8, fz + rng.uniform(4.5, 8.0))))
        windows = [h for h in holes if not any(d[0] < h[2] and h[0] < d[2] and d[1] < h[3] and h[1] < d[3] for d in damage)]
        frame = _frame((apothem * math.cos(angle), apothem * math.sin(angle)), (math.cos(angle), math.sin(angle)))

        def build(builder: tb.MeshBuilder, windows=windows, damage=damage, sources=sources) -> None:
            before = set(builder.bm.faces)
            with builder.material(3):
                builder.slab((-width / 2.0, width / 2.0), (z0, z1), (0.0, 0.6), STUCCO, holes=windows + damage, step=1.2, jitter=0.02)
            _soot(builder, [f for f in builder.bm.faces if f not in before], sources, height=2.6)
            with builder.material(3):
                for x0, hz0, x1, hz1 in windows:
                    kit.outline(builder, [(x0, hz0), (x1, hz0), (x1, hz1), (x0, hz1)], [(0.0, 0.0), (0.0, 0.07), (0.09, 0.07), (0.13, 0.0)], DETAIL)
            for x0, hz0, x1, hz1 in windows:
                state = "vacia" if tier == 2 else rng.choice(("quemada", "vacia", "rota"))
                kit.window(builder, (x0, hz0, x1, hz1), "alta", state, rng, depth=0.15, wall=0.6, frame_color="#3A2E24", sill=False)

        _placed(mb, frame, build)
        # La pilastra de la esquina.
        corner = angle + half
        r = radius - 0.05
        with mb.material(3):
            mb.box((0.5, 0.7, z1 - z0 - 0.4), (r * math.cos(corner), r * math.sin(corner), (z0 + z1) / 2.0 - 0.2), DETAIL, rotation=(0.0, 0.0, math.degrees(corner)), jitter=0.02)
    # Lo de dentro, oscuro, y la cornisa.
    mb.lathe([(apothem - 0.8, z1 - 0.3), (apothem - 0.8, z0 + 0.1)], (0.0, 0.0, 0.0), DARK, segments=sides, sharp_angle=10.0)
    with mb.material(3):
        cornice = [(apothem - 0.3, z1 - 0.6), (radius + 0.4, z1 - 0.35), (radius + 0.9, z1 + 0.1), (radius + 0.9, z1 + 0.35), (radius + 0.4, z1 + 0.6), (0.0, z1 + 0.6)]
        mb.lathe(cornice, (0.0, 0.0, 0.0), DETAIL, segments=max(32, sides * 2), sharp_angle=30.0, jitter=0.02)


def _spire(mb: tb.MeshBuilder) -> None:
    """La aguja: un tronco de pirámide de ocho lados con nervios, doblado por la onda hacia
    el suroeste, y la estrella torcida en la punta."""
    z0, z1 = SPIRE
    profile = [(4.2, z0), (4.2, z0 + 1.2), (3.6, z0 + 1.6), (3.2, z0 + 4.0), (2.6, z0 + 4.4), (2.2, z0 + 6.5), (1.4, BEND[0])]
    mb.lathe(profile, (0.0, 0.0, 0.0), COPPER, segments=8, sharp_angle=20.0, jitter=0.03)
    before = set(mb.bm.faces)
    mb.lathe([(1.4, BEND[0]), (1.1, BEND[0] + 3.0), (0.8, z1 - 2.0), (0.5, z1 - 1.0), (0.0, z1)], (0.0, 0.0, 0.0), COPPER, segments=8, sharp_angle=20.0, jitter=0.03)
    mb.lathe([(0.0, z1 - 0.05), (0.18, z1 + 0.1), (0.0, z1 + 0.6)], (0.0, 0.0, 0.0), BRONZE, segments=8)
    for turn in (0.0, 90.0):  # la estrella doble, encima de la punta y un poco torcida
        mb.prism(kit.ccw(_star_points(1.3, 0.55, (0.0, 0.0))), 0.25, (0.0, 0.0, z1 + 1.9), RUBY, rotation=(90.0, 12.0, turn))
    # El trozo de arriba (con la estrella) se dobla sobre BEND hacia -v (el suroeste).
    top = [f for f in mb.bm.faces if f not in before]
    bend = Matrix.Translation((0.0, 0.0, BEND[0])) @ Matrix.Rotation(math.radians(BEND[1]), 4, "X") @ Matrix.Translation((0.0, 0.0, -BEND[0]))
    kit.transform_faces(top, bend)
    # Los nervios de las aristas del tronco de abajo.
    for k in range(8):
        a = 2.0 * math.pi * k / 8
        mb.tube([(4.25 * math.cos(a), 4.25 * math.sin(a), z0 + 1.2), (3.25 * math.cos(a), 3.25 * math.sin(a), z0 + 4.0), (2.25 * math.cos(a), 2.25 * math.sin(a), z0 + 6.5), (1.45 * math.cos(a), 1.45 * math.sin(a), BEND[0])], 0.09, BRONZE, segments=5)


def _lookout(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """El puesto del vigía en la planta 20, en la ventana que mira al río: sacos terreros en
    el antepecho, una plataforma de tablas que vuela y una lona tendida."""
    radius, _, _, sides = TIERS[1]
    apothem = radius * math.cos(math.pi / sides)
    z = 83.0  # el alféizar de la planta 20
    frame = Matrix.Translation((apothem * math.cos(LOOKOUT), apothem * math.sin(LOOKOUT), z)) @ Matrix.Rotation(LOOKOUT + math.pi / 2.0, 4, "Z")

    def build(builder: tb.MeshBuilder) -> None:
        for row in range(3):
            for i in range(3 - row % 2):
                builder.box((0.5, 0.34, 0.2), (-0.5 + i * 0.5 + 0.25 * (row % 2), 0.3, 0.1 + row * 0.19), rng.choice(("#6B6550", "#5E5A47")), rotation=(0.0, 0.0, rng.uniform(-6, 6)), bevel=0.06, segments=2, jitter=0.08)
        for i in range(6):  # las tablas de la plataforma, volando hacia fuera
            builder.box((0.22, 2.2, 0.05), (-1.3 + i * 0.25, -1.4, -0.05), rng.choice(kit.PLANKS), rotation=(rng.uniform(-3, 3), 0.0, rng.uniform(-4, 4)), jitter=0.1)
        builder.box((2.8, 0.06, 1.6), (0.0, -2.2, 1.0), "#4E5644", rotation=(-25.0, 0.0, 0.0), jitter=0.06)  # la lona
        for x in (-1.35, 1.35):
            builder.bar((x, -2.4, -0.1), (x, -2.5, 1.9), 0.03, "#5A4432", 5)

    _placed(mb, frame, build)


def _tower_collision(mb: tb.MeshBuilder) -> None:
    for radius, z0, z1, sides in TIERS:
        mb.cylinder(radius, z1 - z0 + 0.6, (0.0, 0.0, (z0 + z1) / 2.0 + 0.3), CONCRETE, segments=sides)


# --------------------------------------------------------------------------
# La biblioteca
# --------------------------------------------------------------------------


def _wear(position: Vector, normal: Vector) -> float:
    """El revoque se cae por todas partes (ardió), más junto a los huecos y abajo."""
    p = _from_plan(position)
    if abs(normal.z) > 0.5 or p.y < -HALF_V - 0.5:
        return 0.0  # ni lo horizontal ni el pórtico (sus columnas, de piedra artificial, aguantan)
    low = max(0.0, 1.0 - (p.z - BASE_TOP) / 4.0)
    return 0.2 + 0.45 * low


def _facade_piece(lib: kit.KitLibrary, piece: str, group: list, rng: random.Random, seed: int) -> None:
    """Una pieza con una o varias fachadas (en mallas aparte: cada primitiva del constructor
    recorre las caras que ya tiene, y el bloque entero en una sola malla tardaría horas)."""
    mb = tb.MeshBuilder(seed=seed)
    for name, origin, normal, length, exterior in group:

        def build(builder: tb.MeshBuilder, name=name, length=length, exterior=exterior) -> None:
            holes = _facade_wall(builder, name, length, exterior, rng)
            breach = _gaps(name)
            visible = [h for h in holes if not any(g[0] < (h[0] + h[2]) / 2.0 < g[2] and h[1] > BASE_TOP - 1.0 for g in breach)]
            with builder.material(3):
                if exterior:
                    _rustication(builder, length, visible, name)
                    _order(builder, length, name)
                _window_dressing(builder, visible, exterior, rng)

        _placed(mb, _frame(origin, normal), build)
    _to_plan(mb)
    obj = mb.finish(piece, kit.materials("nevado", "vidrio", "interior", "estuco", "metal"))
    tb.stain(obj, "#1E1A17", amount=0.55, scale=0.5, coverage=0.45, seed=seed, stretch_z=0.3)
    lib.add(obj, [], alpha=_wear, samples=5, ao=0.45, ao_distance=1.0, ground_z=0.0, seed=seed)


def build_kit() -> object:
    lib = kit.KitLibrary("singular_soviets", columns=4, spacing=140.0)
    rng = random.Random(701)
    # El bloque: cada fachada de fuera, una pieza; los dos patios, otra cada uno.
    facades = _facades()
    for k, facade in enumerate(facades[:4]):
        _facade_piece(lib, "soviets_" + facade[0], [facade], rng, 701 + k)
    for k in range(2):
        _facade_piece(lib, "soviets_patio%d" % (k + 1), facades[4 + 4 * k : 8 + 4 * k], rng, 706 + k)
    # Las esquinas, el pórtico con el escudo y lo de dentro de las alas, con sus tejados.
    mb = tb.MeshBuilder(seed=708)
    with mb.material(3):
        _corners(mb)
        _portico(mb)
    _wings(mb)
    _to_plan(mb)
    piece = mb.finish("soviets", kit.materials("nevado", "vidrio", "interior", "estuco", "metal"))
    tb.stain(piece, "#1E1A17", amount=0.45, scale=0.6, coverage=0.4, seed=708, stretch_z=0.3)
    lib.add(piece, [], alpha=_wear, samples=5, ao=0.45, ao_distance=1.0, ground_z=0.0, seed=708)
    # El boquete.
    mb = tb.MeshBuilder(seed=702)
    _breach(mb, random.Random(702))
    _to_plan(mb)
    piece = mb.finish("soviets_boquete", kit.materials("nevado"))
    lib.add(piece, [], samples=5, ao=0.55, ao_distance=1.0, ground_z=0.0, seed=702)
    mb = tb.MeshBuilder(seed=703)
    _block_outline_collision(mb)
    _to_plan(mb)
    lib.add(mb.finish("soviets_colision", kit.materials("colision")), [], samples=1, seed=703)
    # La torre: un cuerpo por pieza, la aguja y el vigía.
    rng = random.Random(711)
    for tier, (radius, z0, z1, sides) in enumerate(TIERS):
        mb = tb.MeshBuilder(seed=711 + tier)
        _tier(mb, radius, z0, z1, sides, rng, tier)
        _to_plan(mb)
        name = "torre_soviets" if tier == 0 else "torre_soviets_cuerpo%d" % (tier + 1)
        piece = mb.finish(name, kit.materials("nevado", "vidrio", "interior", "estuco", "metal"))
        tb.stain(piece, "#1E1A17", amount=0.5, scale=0.6, coverage=0.4, seed=711 + tier, stretch_z=0.3)
        lib.add(piece, [], alpha=_wear, samples=5, ao=0.45, ao_distance=1.0, seed=711 + tier)
    mb = tb.MeshBuilder(seed=715)
    _spire(mb)
    _to_plan(mb)
    piece = mb.finish("torre_soviets_aguja", kit.materials("nevado"))
    lib.add(piece, [], samples=6, ao=0.4, ao_distance=0.8, seed=715)
    mb = tb.MeshBuilder(seed=716)
    _lookout(mb, random.Random(716))
    _to_plan(mb)
    lib.add(mb.finish("torre_soviets_vigia", kit.materials("nevado")), [], samples=6, seed=716)
    mb = tb.MeshBuilder(seed=717)
    _tower_collision(mb)
    _to_plan(mb)
    lib.add(mb.finish("torre_soviets_colision", kit.materials("colision")), [], samples=1, seed=717)
    return lib.root


def models() -> dict:
    return {"singular_soviets": build_kit}
