"""Edificio singular: el vestíbulo del metro de la plaza del Trabajo (PLZ-06), tu salida.

Una rotonda de los años cincuenta, sin copiar ninguna real: un tambor de ladrillo revocado de
veinte lados rodeado de una columnata sobre un basamento de tres escalones, el entablamento
con su antepecho y sus jarrones, un tambor alto con los ventanales que dan luz a la sala y
una cúpula de chapa nervada con su linterna y la estrella. Sobre la entrada principal, que
mira a la avenida, una tabla con las letras МЕТРО; delante, el pilón de la «M» y el control
del ejército de la evacuación (sacos terreros, bloques, la barrera y la garita).

Dentro, la sala redonda: el suelo de granito a cuadros, el zócalo de mármol, las pilastras,
la cornisa, la cúpula de casetones con el óculo, la gran lámpara, los torniquetes, las
máquinas de cambio y el equipaje que dejó la evacuación. Sobre la boca de las escaleras
mecánicas, el gobierno civil levantó una esclusa de hormigón con la compuerta blindada por la
que sales (una pieza aparte, para poder moverla); detrás, las tres escaleras bajan hacia la
estación y se pierden en lo oscuro. Las otras puertas están soldadas desde abajo: chapas por
dentro. Las ventanas que daban a la esclusa, tapiadas.

Daño 1 (herido) e incendio parcial: cristales rotos, dos ventanas quemadas con el hollín
encima, por fuera y por dentro, el revoque caído junto a los huecos y nieve en lo alto.

Coordenadas: las del plano (x al este, y al norte, z arriba), con el origen en el «centro» de
PLZ-06 (data/ciudad/plano.json) y a su cota. Todo se construye en un marco propio, con la
rotonda en el origen, x a lo largo de la avenida hacia la plaza (por ahí bajan las escaleras,
hacia la estación) y la entrada principal hacia -y (la avenida), y se lleva al plano al final
(``_to_plan``).

Piezas: "vestibulo" (el edificio por fuera, con sus muros), "vestibulo_cupula",
"vestibulo_sala" (lo de dentro), "vestibulo_esclusa" (con las escaleras y el túnel),
"vestibulo_compuerta", "vestibulo_entorno" (el control, las farolas y la «M") y
"vestibulo_colision", la colisión, que no se dibuja: los escalones y las escaleras son
rampas, y el equipaje y los torniquetes, cajas. "vestibulo_hueco" tampoco se dibuja: es
dónde no va el terreno (el foso de las escaleras baja bajo la calle).
"""

from __future__ import annotations

import math
import random

from mathutils import Matrix, Vector, noise

import kit_bpy as kit
import tumansk_bpy as tb

ORIGIN = (326.7, 294.5)  # el «centro» de PLZ-06 en el plano
ROTUNDA = (326.0, 299.5)  # el centro de la rotonda, en el plano (a 15 m de la calle del oeste)
AVENUE = math.radians(47.73)  # la dirección de la avenida (y de la parcela que da a ella)

# Medidas (m). z = 0 es la acera; la sala está tres escalones por encima.
FLOOR = 0.48
BAYS = 20  # lados del tambor (y columnas)
R_IN, R_OUT = 9.0, 9.7  # el tambor (radios de las esquinas del polígono)
HALF = math.pi / BAYS
APOTHEM_OUT = R_OUT * math.cos(HALF)
APOTHEM_IN = R_IN * math.cos(HALF)
FACET = 2.0 * R_OUT * math.sin(HALF)  # el ancho de un lado del tambor por fuera
FACET_IN = 2.0 * R_IN * math.sin(HALF)  # y por dentro
WALL = APOTHEM_OUT - APOTHEM_IN
R_COL = 12.0  # el eje de las columnas (el peristilo, de 2 m)
PODIUM = 14.0  # el pie del basamento
COL_TOP = 8.9  # lo alto de los capiteles
ROOF = 10.5  # la azotea del peristilo
DRUM_TOP = 13.1  # lo alto del tambor: el arranque de la cúpula
DOME_BASE = 13.2
DOME_A, DOME_B = R_OUT + 0.25, 4.1  # la cúpula de fuera (semiejes de su elipse)
INNER_BASE = 12.9
INNER_A, INNER_B = R_IN, 3.6  # la cúpula de dentro
OCULUS = 1.35
LANTERN = 17.3  # el zócalo de la linterna
DADO = FLOOR + 1.1  # lo alto del zócalo de mármol de la sala (a la altura de los alféizares)

# Huecos de un lado del tambor, en el marco del lado (x a lo largo, z arriba).
DOOR = (-1.0, FLOOR, 1.0, FLOOR + 4.0)
WINDOW = (-0.85, FLOOR + 1.1, 0.85, FLOOR + 5.3)
CLERESTORY = (-0.65, ROOF + 0.55, 0.65, ROOF + 2.0)
ENTRANCE = (14, 15, 16)  # bajo la tabla de las letras, mirando a la avenida
MAIN = 15  # la puerta por la que sales, con una hoja abierta
MAIN_SWING = 84.0
WELDED = (0, 5, 10)  # las otras puertas, soldadas desde abajo
WALLED = (1, 19)  # las ventanas que daban a la esclusa
BURNT = (7, 8)  # las ventanas quemadas

# La esclusa, las escaleras y el túnel (en el marco de la rotonda).
LOCK_X = 1.6  # la cara del muro de la compuerta, hacia la sala
LOCK_FLAT = 5.4  # hasta aquí el tejado es plano; luego baja con las escaleras
LOCK_HALF = 3.3  # medio ancho, por fuera
LOCK_HEIGHT = 3.3
LOCK_WALL = 0.3
HATCH = (-0.8, FLOOR, 0.8, FLOOR + 2.2)  # el hueco de la compuerta, en el marco del muro
HATCH_SWING = 95.0
SLOPE = math.radians(30.0)
TAN = math.tan(SLOPE)
STAIR_TOP = LOCK_X + 2.1  # donde empiezan a bajar las escaleras
STAIR_RUN = 16.0  # lo que avanzan en horizontal (bajan 9,2 m)
CLEAR = 2.6  # la altura libre del túnel, en vertical, pasada la boca
PORTAL_X = 8.2  # el dintel de la boca del túnel, delante del muro del tambor
PIT_END = 8.95  # los muros de la esclusa acaban dentro del muro del tambor
LANES = (-1.5, 0.0, 1.5)
BALUSTRADES = (-2.25, -0.75, 0.75, 2.25)
TURNSTILE_X = -0.85
# Por donde pasas de la compuerta a la puerta: aquí no hay equipaje.
PATH = ((LOCK_X, 0.2), (TURNSTILE_X + 0.8, 0.55), (TURNSTILE_X - 0.8, 0.55), (-0.47, -7.4), (-0.47, -10.0))

# Colores (sRGB).
STUCCO = "#C6B18C"  # revoque ocre claro
DETAIL = "#D8CBAE"  # columnas, cornisas y recercados, más claros
GRANITE = "#6C6661"
GRANITE_DARK = "#4F4945"
MARBLE = "#8C7B66"
COPPER = "#56625A"  # la chapa de la cúpula, verdosa
DOME_IN = "#B9AE96"
BRONZE = "#7A6243"
RUBY = "#7A2B25"
CONCRETE = "#7B7770"
INFILL = "#7A766E"
STEEL = "#4A4E50"
RUST = "#6E3F2A"
DOOR_WOOD = "#4A3B2E"
FRAME_LIGHT = "#B3AC98"
BALUSTRADE = "#8A7E68"
GLOBE = "#9C9A90"
SOOT = "#1E1B19"
DARK = "#121110"
CASES = ("#5A4636", "#3F4A3C", "#6A5A44", "#4A3A30", "#565A5C", "#704A35")
BUNDLES = ("#6E6656", "#5C5A50", "#7A6E5C")


# --------------------------------------------------------------------------
# Marcos y geometría auxiliar
# --------------------------------------------------------------------------


def _facet(angle: float, apothem: float = APOTHEM_OUT) -> Matrix:
    """El marco de un lado que mira hacia ``angle``: x a lo largo (en sentido antihorario),
    y hacia dentro y z arriba, con el origen en el centro de su cara de fuera. Con
    ``apothem`` = R_IN es el marco de una esquina de dentro (y hacia la sala)."""
    c, s = math.cos(angle), math.sin(angle)
    return Matrix(((-s, -c, 0.0, apothem * c), (c, -s, 0.0, apothem * s), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _inner(angle: float) -> Matrix:
    """El marco de la cara de dentro de un lado: x a lo largo (de izquierda a derecha, visto
    desde la sala), y hacia el muro y z arriba, con el origen en el centro de la cara."""
    c, s = math.cos(angle), math.sin(angle)
    a = APOTHEM_IN
    return Matrix(((s, c, 0.0, a * c), (-c, s, 0.0, a * s), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _front() -> Matrix:
    """El marco del muro de la compuerta: x a lo largo (visto desde la sala), y hacia la
    esclusa (+x) y z arriba, con el origen en su cara de la sala."""
    return Matrix(((0.0, 1.0, 0.0, LOCK_X), (-1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def _tilted() -> Matrix:
    """El marco de las escaleras: x baja por la pendiente hacia la estación, y de lado y z
    perpendicular a la pendiente, con el origen en la línea de los peldaños, arriba."""
    return Matrix.Translation((STAIR_TOP, 0.0, FLOOR)) @ Matrix.Rotation(SLOPE, 4, "Y")


def _hatch_frame() -> Matrix:
    """La compuerta abierta: gira sobre el canto del hueco que da a -y, hacia la sala."""
    return Matrix.Translation((LOCK_X, HATCH[0], 0.0)) @ Matrix.Rotation(math.radians(HATCH_SWING), 4, "Z")


def _bay_angle(k: int) -> float:
    return 2.0 * math.pi * k / BAYS


def _column_angle(k: int) -> float:
    return 2.0 * math.pi * (k + 0.5) / BAYS


def _step_z(x: float) -> float:
    """La altura de la línea de los peldaños en ``x``."""
    return FLOOR - (x - STAIR_TOP) * TAN


def _tunnel_start() -> float:
    """Dónde empieza el techo del túnel (en el marco de las escaleras): bajo el dintel."""
    ceiling = CLEAR * math.cos(SLOPE)
    return (PORTAL_X - STAIR_TOP - ceiling * math.sin(SLOPE)) / math.cos(SLOPE)


def _tunnel_end() -> float:
    return STAIR_RUN / math.cos(SLOPE) + 1.5


def _placed(mb: tb.MeshBuilder, matrix: Matrix, build) -> None:
    """Construye algo en un marco y lo lleva a su sitio."""
    before = set(mb.bm.faces)
    build(mb)
    kit.transform_faces([f for f in mb.bm.faces if f not in before], matrix)


def _to_plan(mb: tb.MeshBuilder) -> None:
    """Del marco de la rotonda al del plano, con el origen en el centro de PLZ-06."""
    shift = Vector((ROTUNDA[0] - ORIGIN[0], ROTUNDA[1] - ORIGIN[1], 0.0))
    kit.transform_faces(list(mb.bm.faces), Matrix.Translation(shift) @ Matrix.Rotation(AVENUE, 4, "Z"))


def _from_plan(position: Vector) -> Vector:
    """Del plano al marco de la rotonda (para las máscaras, que se pintan al final)."""
    shift = Vector((ROTUNDA[0] - ORIGIN[0], ROTUNDA[1] - ORIGIN[1], 0.0))
    return Matrix.Rotation(-AVENUE, 3, "Z") @ (Vector(position) - shift)


def _facing(mb: tb.MeshBuilder, corners: list, color: str, outward: Vector) -> None:
    """Una cara de cuatro esquinas que mira hacia ``outward``."""
    a, b, c = (Vector(p) for p in corners[:3])
    if (b - a).cross(c - b).dot(outward) < 0.0:
        corners = corners[::-1]
    mb.quad(corners, color)


def _sweep(mb: tb.MeshBuilder, path: list, sections: list, color: str, outward) -> None:
    """Una banda que sigue ``path`` (puntos) con la sección que da ``sections[i]`` en cada
    punto (los puntos de la sección, de un canto al otro). ``outward(i, j)`` dice hacia
    dónde mira la cara j del tramo i."""
    for i in range(len(path) - 1):
        for j in range(len(sections[i]) - 1):
            corners = [sections[i][j], sections[i + 1][j], sections[i + 1][j + 1], sections[i][j + 1]]
            _facing(mb, [tuple(p) for p in corners], color, outward(i, j))


def _shade(color: str, factor: float) -> str:
    value = color.lstrip("#")
    rgb = [min(255, max(0, round(int(value[i : i + 2], 16) * factor))) for i in (0, 2, 4)]
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _clip(points: list, a: float, b: float, c: float) -> list:
    """La parte de un polígono convexo donde a·x + b·y + c >= 0 (Sutherland-Hodgman)."""
    result: list = []
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0.0:
            result.append(p)
        if (fp >= 0.0) != (fq >= 0.0):
            t = fp / (fp - fq)
            result.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    clean: list = []
    for p in result:
        if not clean or math.dist(p, clean[-1]) > 1e-6:
            clean.append(p)
    if len(clean) > 1 and math.dist(clean[0], clean[-1]) <= 1e-6:
        clean.pop()
    return clean


def _area(points: list) -> float:
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))


def _outside_lock(points: list) -> list:
    """Un polígono convexo del suelo sin lo que queda dentro de la esclusa: tres trozos
    convexos como mucho (delante del muro de la compuerta y a los dos lados)."""
    x0, half = LOCK_X + 0.02, LOCK_HALF - 0.02
    beyond = _clip(points, 1.0, 0.0, -x0)
    pieces = [_clip(points, -1.0, 0.0, x0), _clip(beyond, 0.0, 1.0, -half), _clip(beyond, 0.0, -1.0, -half)]
    return [p for p in pieces if len(p) >= 3 and _area(p) > 1e-5]


def _segment_distance(p: Vector, a: Vector, b: Vector) -> float:
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


# --------------------------------------------------------------------------
# Adornos de fachada (en el marco de un lado: la cara del muro en y = 0)
# --------------------------------------------------------------------------


def _surround(mb: tb.MeshBuilder, opening: tuple, *, width: float = 0.15, depth: float = 0.09) -> None:
    x0, z0, x1, z1 = opening
    kit.outline(mb, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], [(0.0, 0.0), (0.0, depth), (width - 0.05, depth), (width, 0.0)], DETAIL)


def _sill(mb: tb.MeshBuilder, opening: tuple) -> None:
    x0, z0, x1, _ = opening
    section = [(0.0, z0 - 0.06), (-0.17, z0 - 0.1), (-0.17, z0 - 0.18), (-0.09, z0 - 0.23), (0.0, z0 - 0.3)]
    kit.moulding(mb, (x0 - 0.3, x1 + 0.3), section, DETAIL, jitter=0.02, mitre=True)


def _cornice_above(mb: tb.MeshBuilder, opening: tuple, *, reach: float = 0.32) -> None:
    x0, _, x1, z1 = opening
    kit.block(mb, (x0 - 0.08, z1 + 0.18, x1 + 0.08, z1 + 0.3), 0.05, DETAIL, splay=0.03)
    section = [(0.0, z1 + 0.28), (-0.2, z1 + 0.34), (-0.2, z1 + 0.42), (0.0, z1 + 0.5)]
    kit.moulding(mb, (x0 - reach, x1 + reach), section, DETAIL, jitter=0.02, mitre=True)


def _star_points(radius: float, inner: float, center: tuple[float, float], turn: float = 0.0) -> list:
    """Los diez vértices de una estrella de cinco puntas (x, z), la primera punta arriba."""
    cx, cz = center
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else inner
        a = math.pi / 2.0 + turn + i * math.pi / 5.0
        points.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return points


def _star_relief(mb: tb.MeshBuilder, radius: float, center: tuple[float, float], depth: float, color: str) -> None:
    """Una estrella en relieve, de una pieza (con piezas sueltas, sus juntas se dibujan y la
    estrella se lee como una cruz): el contorno de diez lados con los cantos en derrame."""
    kit.raised(mb, _star_points(radius, radius * 0.42, center), depth, color, splay=0.012)


def _medallion(mb: tb.MeshBuilder, z: float) -> None:
    """Medallón con la estrella sobre un hueco: un disco de canto en derrame."""
    profile = [(0.6, 0.0), (0.52, 0.1), (0.46, 0.1), (0.41, 0.06), (0.0, 0.06)]
    mb.lathe(profile, (0.0, 0.0, z), DETAIL, rotation=(90.0, 0.0, 0.0), segments=24, sharp_angle=35.0)
    _star_relief(mb, 0.3, (0.0, z), 0.12, DETAIL)


def _soot(mb: tb.MeshBuilder, faces: list, x: float, z: float, width: float, height: float) -> None:
    """Hollín de un hueco quemado en el color base de unas caras (en el marco del lado): sube
    desde el dintel (x, z), se abre y se apaga; por fuera y por dentro."""
    target = Vector(int(SOOT[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
    for face in faces:
        for loop in face.loops:
            co = loop.vert.co
            rise = co.z - z
            if rise < -0.5 or rise > height:
                continue
            spread = width * (0.5 + 0.45 * max(rise, 0.0) / height)
            side = abs(co.x - x) / spread + 0.3 * noise.noise(Vector((co.x * 2.2, co.z * 0.9, x + co.y * 3.0)))
            weight = (1.0 - max(rise, 0.0) / height) * max(0.0, 1.0 - side * side)
            if rise < 0.0:
                weight *= 1.0 + rise / 0.5
            if weight > 0.0:
                base = Vector(loop[mb.base][:3])
                loop[mb.base] = (*base.lerp(target, min(1.0, 0.92 * weight)), 1.0)


def _wear(position: Vector, normal: Vector) -> float:
    """Dónde se cae antes el revoque del tambor (el alfa del color): junto a los huecos y
    abajo, donde sube la humedad; por fuera y por dentro. Los adornos aguantan."""
    p = _from_plan(position)
    n = _from_plan(position + normal) - p
    k = round(math.atan2(p.y, p.x) / (2.0 * math.pi / BAYS)) % BAYS
    direction = Vector((math.cos(_bay_angle(k)), math.sin(_bay_angle(k)), 0.0))
    distance = p.dot(direction)
    outside = abs(distance - APOTHEM_OUT) < 0.004 and n.dot(direction) > 0.9
    inside = abs(distance - APOTHEM_IN) < 0.004 and n.dot(direction) < -0.9
    if not (outside or inside):
        return 0.0
    x = p.dot(Vector((-direction.y, direction.x, 0.0)))
    lower = DOOR if k in ENTRANCE or k in WELDED else WINDOW
    near = 0.0
    for x0, z0, x1, z1 in (lower, CLERESTORY):
        dx = max(x0 - x, 0.0, x - x1)
        dz = max(z0 - p.z, 0.0, p.z - z1)
        near = max(near, 1.0 - math.hypot(dx, dz) / 1.15)
    low = max(0.0, 1.0 - (p.z - FLOOR) / 1.4) * 0.7
    return min(1.0, 0.1 + 0.5 * max(near, low))


# --------------------------------------------------------------------------
# Por fuera
# --------------------------------------------------------------------------


def _podium(mb: tb.MeshBuilder) -> None:
    """El basamento de granito: tres escalones de 16 cm alrededor de toda la rotonda. Por
    dentro del tambor no sigue: allí está el suelo de la sala (y el foso de la esclusa)."""
    profile = [(PODIUM, -0.4), (PODIUM, 0.16), (PODIUM - 0.35, 0.16), (PODIUM - 0.35, 0.32), (PODIUM - 0.7, 0.32), (PODIUM - 0.7, FLOOR), (APOTHEM_IN - 0.1, FLOOR)]
    mb.lathe(profile, (0.0, 0.0, 0.0), GRANITE, segments=96, sharp_angle=30.0, jitter=0.03)


def _drum(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """El tambor: un muro de veinte lados de la sala al arranque de la cúpula, con sus
    huecos, recercados, alféizares, cornisillas y medallones, y las carpinterías."""
    for k in range(BAYS):
        door = k in ENTRANCE or k in WELDED
        lower = DOOR if door else WINDOW
        # Los huecos de las puertas bajan hasta el pie del muro: el umbral es el basamento.
        holes = [(DOOR[0], FLOOR - 0.4, DOOR[2], DOOR[3]) if door else WINDOW, CLERESTORY]
        burnt = k in BURNT

        def build(builder: tb.MeshBuilder, k=k, door=door, lower=lower, holes=holes, burnt=burnt) -> None:
            before = set(builder.bm.faces)
            with builder.material(3):
                builder.slab(
                    (-FACET / 2.0, FACET / 2.0), (FLOOR - 0.35, DRUM_TOP), (0.0, WALL), STUCCO,
                    holes=holes, step=0.5 if burnt else 1.2, ring=0.2 if burnt else 0.0, jitter=0.02,
                )
                _surround(builder, lower)
                if not door:
                    _sill(builder, lower)
                _cornice_above(builder, lower, reach=0.36 if door else 0.32)
                _medallion(builder, lower[3] + 1.25)
                _surround(builder, CLERESTORY, width=0.12, depth=0.07)
            if burnt:
                faces = [f for f in builder.bm.faces if f not in before]
                _soot(builder, faces, 0.0, lower[3], 1.6, 4.4)
                _soot(builder, faces, 0.0, CLERESTORY[3], 1.2, 1.4)
            _openings(builder, k, door, lower, rng)

        _placed(mb, _facet(_bay_angle(k)), build)


def _openings(builder: tb.MeshBuilder, k: int, door: bool, lower: tuple, rng: random.Random) -> None:
    """Las carpinterías de un lado: la puerta de salida, entornada; las otras de la entrada,
    cerradas; las soldadas, con su chapa por dentro; las ventanas en su estado (las de la
    esclusa, tapiadas con bloques) y el ventanal de arriba."""
    if k in WALLED:
        x0, z0, x1, z1 = lower
        builder.box((x1 - x0, WALL - 0.12, z1 - z0), (0.0, 0.12 + (WALL - 0.12) / 2.0, (z0 + z1) / 2.0), INFILL, cuts=2, jitter=0.04)
    elif k in ENTRANCE:
        state = "rota" if k == MAIN else "intacta"
        kit.window(
            builder, DOOR, "portal", state, rng, depth=0.18, wall=WALL, frame_color=DOOR_WOOD,
            sill=False, open_sash=0, open_angle=MAIN_SWING,
        )
    elif door:
        kit.window(builder, DOOR, "portal", "intacta", rng, depth=0.18, wall=WALL, frame_color=DOOR_WOOD, sill=False)
        with builder.material(4):
            builder.box((2.1, 0.03, 4.1), (0.0, WALL - 0.08, FLOOR + 2.0), RUST, cuts=2, jitter=0.08)
    else:
        state = "quemada" if k in BURNT else rng.choice(("rota", "rota", "vacia", "intacta", "tapiada", "rota"))
        kit.window(builder, lower, "alta", state, rng, depth=0.16, wall=WALL, frame_color=FRAME_LIGHT, sill=False)
    high = "quemada" if k in BURNT else rng.choice(("rota", "intacta", "rota", "vacia"))
    kit.window(builder, CLERESTORY, "escalera", high, rng, depth=0.12, wall=WALL, frame_color=FRAME_LIGHT, sill=False)


def _column(mb: tb.MeshBuilder, angle: float) -> None:
    """Una columna de fuste liso con éntasis, basa y capitel redondo (sin caras planas
    estrechas: el plinto y el ábaco llevan el canto en derrame)."""
    z = FLOOR
    profile = [
        (0.0, z), (0.62, z), (0.62, z + 0.14), (0.56, z + 0.2), (0.56, z + 0.3), (0.47, z + 0.38),
        (0.465, z + 2.4), (0.43, COL_TOP - 0.78), (0.4, COL_TOP - 0.66), (0.44, COL_TOP - 0.6),
        (0.44, COL_TOP - 0.52), (0.6, COL_TOP - 0.24), (0.68, COL_TOP - 0.16), (0.68, COL_TOP), (0.0, COL_TOP),
    ]
    mb.lathe(profile, (R_COL * math.cos(angle), R_COL * math.sin(angle), 0.0), DETAIL, segments=20, sharp_angle=40.0, jitter=0.03)


def _entablature(mb: tb.MeshBuilder) -> None:
    """El arquitrabe, el friso, la cornisa y el antepecho del peristilo, con su azotea:
    una sola pieza de revolución, con vierteaguas y caras de abajo en derrame. Por dentro
    arranca metida en el muro del tambor (que es un polígono: no deja rendijas)."""
    c, w = R_COL, APOTHEM_OUT - 0.2
    profile = [
        (w, COL_TOP), (c + 0.52, COL_TOP), (c + 0.52, COL_TOP + 0.52), (c + 0.46, COL_TOP + 0.58),
        (c + 0.46, COL_TOP + 1.0), (c + 0.88, COL_TOP + 1.24), (c + 0.88, COL_TOP + 1.4), (c + 0.42, COL_TOP + 1.6),
        (c + 0.42, ROOF + 0.62), (c + 0.5, ROOF + 0.68), (c + 0.5, ROOF + 0.76), (c + 0.05, ROOF + 0.84),
        (c + 0.05, ROOF + 0.12), (w, ROOF),
    ]
    mb.lathe(profile, (0.0, 0.0, 0.0), DETAIL, segments=96, sharp_angle=30.0, jitter=0.02)


def _vases(mb: tb.MeshBuilder) -> None:
    """Jarrones de piedra sobre el antepecho, encima de cada columna (menos detrás de la
    tabla de las letras)."""
    profile = [
        (0.0, 0.0), (0.22, 0.0), (0.22, 0.08), (0.14, 0.14), (0.12, 0.2), (0.24, 0.42), (0.26, 0.55),
        (0.18, 0.7), (0.1, 0.74), (0.13, 0.8), (0.0, 0.86),
    ]
    for k in range(BAYS):
        if k in (14, 15):
            continue
        phi = _column_angle(k)
        r = R_COL + 0.24
        mb.lathe(profile, (r * math.cos(phi), r * math.sin(phi), ROOF + 0.8), DETAIL, segments=16, sharp_angle=40.0, jitter=0.03)


def _tablet(mb: tb.MeshBuilder) -> None:
    """La tabla sobre la entrada principal con las letras МЕТРО, de trazos en relieve."""
    reach = 3.2

    def build(builder: tb.MeshBuilder) -> None:
        builder.slab((-reach, reach), (ROOF - 0.25, 12.9), (0.0, 1.0), DETAIL, step=1.0, jitter=0.02)
        kit.moulding(builder, (-reach - 0.12, reach + 0.12), [(0.0, 12.86), (-0.14, 12.92), (-0.14, 13.04), (0.0, 13.14)], DETAIL, mitre=True)
        kit.moulding(builder, (-reach + 0.1, reach - 0.1), [(0.0, 11.12), (-0.07, 11.16), (-0.07, 11.22), (0.0, 11.26)], DETAIL, mitre=True)
        _letters(builder, "METPO", 11.42, 1.3)  # МЕТРО, con las letras latinas que se le parecen

    _placed(mb, _facet(3.0 * math.pi / 2.0, R_COL + 0.45), build)


def _stroke(p: tuple, q: tuple, width: float) -> list:
    """Un trazo recto de ``p`` a ``q`` (un paralelogramo)."""
    d = Vector((q[0] - p[0], q[1] - p[1])).normalized()
    n = Vector((-d.y, d.x)) * (width / 2.0)
    return [(p[0] - n.x, p[1] - n.y), (q[0] - n.x, q[1] - n.y), (q[0] + n.x, q[1] + n.y), (p[0] + n.x, p[1] + n.y)]


def _relief_ring(
    mb: tb.MeshBuilder, center: tuple, rx: float, rz: float, width: float, depth: float, color: str, *, splay: float = 0.03, samples: int = 40
) -> None:
    """Un anillo elíptico en relieve, de una pieza (hecho de trozos, sus juntas se dibujarían):
    el canto de fuera y el de dentro en derrame y la cara de delante, en el marco de un muro
    (la cara en y = 0 y lo de fuera hacia -y)."""
    cx, cz = center
    rails = ((0.0, splay, 0.0), (0.0, 0.0, depth), (width, 0.0, depth), (width, -splay, 0.0))

    def point(a: float, shrink: float, push: float, d: float) -> tuple:
        normal = Vector((math.cos(a) / rx, math.sin(a) / rz)).normalized()
        return (cx + (rx - shrink) * math.cos(a) + normal.x * push, -d, cz + (rz - shrink) * math.sin(a) + normal.y * push)

    for i in range(samples):
        a0, a1 = 2.0 * math.pi * i / samples, 2.0 * math.pi * (i + 1) / samples
        n = Vector((math.cos((a0 + a1) / 2.0) / rx, math.sin((a0 + a1) / 2.0) / rz)).normalized()
        radial = Vector((n.x, 0.0, n.y))
        for r, outward in enumerate((radial + Vector((0.0, -1.0, 0.0)), Vector((0.0, -1.0, 0.0)), -radial + Vector((0.0, -1.0, 0.0)))):
            corners = [point(a0, *rails[r]), point(a1, *rails[r]), point(a1, *rails[r + 1]), point(a0, *rails[r + 1])]
            _facing(mb, corners, color, outward)


def _letters(mb: tb.MeshBuilder, text: str, z0: float, height: float) -> None:
    """Letras de trazos convexos en relieve (las que se cruzan, a fondos distintos para que
    sus caras no coincidan)."""
    w, s, gap = 0.98, 0.21, 0.3
    x = -(len(text) * w + (len(text) - 1) * gap) / 2.0
    h = height
    for letter in text:
        strokes: list[tuple[list, float]] = []
        rect = lambda a, b, c, d: [(x + a, z0 + b), (x + c, z0 + b), (x + c, z0 + d), (x + a, z0 + d)]  # noqa: E731
        if letter == "M":
            strokes += [(rect(0.0, 0.0, s, h), 0.16), (rect(w - s, 0.0, w, h), 0.16)]
            strokes += [(_stroke((x + s * 0.5, z0 + h - s * 0.6), (x + w / 2.0, z0 + h * 0.38), s), 0.15)]
            strokes += [(_stroke((x + w / 2.0, z0 + h * 0.38), (x + w - s * 0.5, z0 + h - s * 0.6), s), 0.14)]
        elif letter == "E":
            strokes += [(rect(0.0, 0.0, s, h), 0.16), (rect(s, h - s, w * 0.92, h), 0.15)]
            strokes += [(rect(s, (h - s) / 2.0, w * 0.78, (h + s) / 2.0), 0.15), (rect(s, 0.0, w * 0.92, s), 0.15)]
        elif letter == "T":
            strokes += [(rect(0.0, h - s, w, h), 0.16), (rect((w - s) / 2.0, 0.0, (w + s) / 2.0, h - s), 0.16)]
        elif letter == "P":  # la Р cirílica: el asta y el ojo, sin pata
            strokes += [(rect(0.0, 0.0, s, h), 0.16), (rect(s, h - s, w * 0.72, h), 0.15)]
            strokes += [(rect(s, h * 0.42, w * 0.72, h * 0.42 + s), 0.15), (rect(w - s, h * 0.52, w, h - s * 1.2), 0.15)]
            strokes += [(_stroke((x + w * 0.72, z0 + h - s * 0.5), (x + w - s * 0.5, z0 + h - s * 1.2), s), 0.14)]
            strokes += [(_stroke((x + w * 0.72, z0 + h * 0.42 + s * 0.5), (x + w - s * 0.5, z0 + h * 0.52), s), 0.14)]
        elif letter == "O":
            _relief_ring(mb, (x + w / 2.0, z0 + h / 2.0), w / 2.0, h / 2.0, s, 0.16, RUBY, splay=0.025)
        for polygon, depth in strokes:
            kit.raised(mb, polygon, depth, RUBY, splay=0.025)
        x += w + gap


def _dome(mb: tb.MeshBuilder) -> None:
    """La cornisa del tambor, la cúpula de chapa con sus veinte nervios y la linterna con la
    estrella. La linterna está abierta por abajo: desde la sala, por el óculo, se ven sus
    pilares, el cielo entre ellos y el cupulín por dentro."""
    cornice = [(APOTHEM_OUT - 0.2, 12.7), (R_OUT + 0.45, 12.94), (R_OUT + 0.45, 13.08), (R_OUT + 0.22, DOME_BASE)]
    with mb.material(1):
        mb.lathe(cornice, (0.0, 0.0, 0.0), DETAIL, segments=96, sharp_angle=30.0)
    top = math.acos(1.6 / DOME_A)
    samples = [top * i / 16 for i in range(17)]
    profile = [(DOME_A * math.cos(t), DOME_BASE + DOME_B * math.sin(t)) for t in samples]
    mb.lathe([(R_OUT + 0.2, DOME_BASE - 0.02), *profile], (0.0, 0.0, 0.0), COPPER, segments=96, sharp_angle=60.0, jitter=0.03)
    # Nervios: bandas de canto en derrame sobre la chapa, de abajo a la linterna.
    for k in range(BAYS):
        phi = _column_angle(k)
        radial = Vector((math.cos(phi), math.sin(phi), 0.0))
        lateral = Vector((-math.sin(phi), math.cos(phi), 0.0))
        path, sections = [], []
        for t in samples:
            point = radial * (DOME_A * math.cos(t)) + Vector((0.0, 0.0, DOME_BASE + DOME_B * math.sin(t)))
            normal = (radial * (DOME_B * math.cos(t)) + Vector((0.0, 0.0, DOME_A * math.sin(t)))).normalized()
            path.append(point)
            sections.append([point - lateral * 0.22, point - lateral * 0.13 + normal * 0.15, point + lateral * 0.13 + normal * 0.15, point + lateral * 0.22])

        def outward(i: int, j: int, path=path, lateral=lateral) -> Vector:
            mid = (path[i] + path[i + 1]) / 2.0
            normal = (mid - Vector((0.0, 0.0, DOME_BASE - 2.0))).normalized()
            return normal - lateral if j == 0 else (normal + lateral if j == 2 else normal)

        _sweep(mb, path, sections, COPPER, outward)
    # La linterna: el zócalo (un anillo sobre el óculo), ocho pilares, la cornisa, el
    # cupulín con la aguja y la estrella doble.
    mb.lathe([(1.75, LANTERN - 0.15), (1.75, LANTERN + 0.12), (1.58, LANTERN + 0.2), (OCULUS, LANTERN + 0.2)], (0.0, 0.0, 0.0), COPPER, segments=32, sharp_angle=40.0)
    for i in range(8):
        a = math.pi / 8.0 + i * math.pi / 4.0
        mb.box((0.26, 0.26, 1.3), (1.4 * math.cos(a), 1.4 * math.sin(a), LANTERN + 0.85), DETAIL, rotation=(0.0, 0.0, math.degrees(a)))
    cap = [(1.6, LANTERN + 1.5), (1.6, LANTERN + 1.66), (1.82, LANTERN + 1.78), (1.82, LANTERN + 1.9), (1.5, LANTERN + 1.98)]
    cap += [(1.5 * math.cos(t), LANTERN + 1.98 + 0.75 * math.sin(t)) for t in (0.4, 0.8, 1.15, 1.4)]
    cap += [(0.16, LANTERN + 2.78), (0.1, LANTERN + 3.2), (0.0, LANTERN + 3.3)]
    mb.lathe(cap, (0.0, 0.0, 0.0), COPPER, segments=32, sharp_angle=40.0)
    inside = [(0.0, LANTERN + 2.55), (0.8, LANTERN + 2.42), (1.25, LANTERN + 2.12), (1.5, LANTERN + 1.78), (1.6, LANTERN + 1.5)]
    mb.lathe(inside, (0.0, 0.0, 0.0), "#3C4440", segments=32, sharp_angle=40.0)
    star_z = LANTERN + 3.75
    for turn in (0.0, 90.0):
        before = set(mb.bm.faces)
        mb.prism(kit.ccw(_star_points(0.55, 0.23, (0.0, 0.0))), 0.12, (0.0, 0.0, 0.0), RUBY, rotation=(90.0, 0.0, 0.0))
        kit.transform_faces([f for f in mb.bm.faces if f not in before], Matrix.Translation((0.0, 0.0, star_z)) @ Matrix.Rotation(math.radians(turn), 4, "Z"))


# --------------------------------------------------------------------------
# Por dentro: la sala
# --------------------------------------------------------------------------

FLOOR_RINGS = (0.0, 1.6, 2.6, 3.6, 4.6, 5.6, 6.6, 7.6, R_IN + 0.05)


def _floor_tiles(rings: tuple, sectors) -> list:
    """Las baldosas del suelo en anillos y sectores: (polígono en sentido antihorario,
    anillo, sector). ``sectors(i)`` dice cuántas lleva el anillo i."""
    tiles = []
    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        count = sectors(i)
        for j in range(count):
            a0, a1 = 2.0 * math.pi * j / count, 2.0 * math.pi * (j + 1) / count
            outer = [(r1 * math.cos(a0), r1 * math.sin(a0)), (r1 * math.cos(a1), r1 * math.sin(a1))]
            if r0 <= 0.0:
                polygon = [(0.0, 0.0), *outer]
            else:
                polygon = [(r0 * math.cos(a0), r0 * math.sin(a0)), outer[0], outer[1], (r0 * math.cos(a1), r0 * math.sin(a1))]
            tiles.append((polygon, i, j))
    return tiles


def _floor(mb: tb.MeshBuilder) -> None:
    """El suelo de la sala: granito a cuadros en anillos, con un rosetón rojo en el centro.
    Donde está la esclusa no hay suelo: allí está su rellano y el foso de las escaleras."""
    light, dark, red = "#8D857A", "#5E5852", "#6E3A30"
    for polygon, i, j in _floor_tiles(FLOOR_RINGS, lambda i: 8 if i == 0 else BAYS * (1 if i < 3 else 2)):
        color = (red if j % 2 == 0 else dark) if i == 0 else (light if (i + j) % 2 == 0 else dark)
        color = _shade(color, 1.0 + mb.rng.uniform(-0.04, 0.04))
        for piece in _outside_lock(polygon):
            mb.polygon([(x, y, FLOOR + 0.004) for x, y in piece], color)


# La pilastra por alturas: (z, sección). Las secciones son trapecios (x a lo largo, y lo que
# sale del muro) de lados paralelos, para que las caras de los cambios queden planas.
PILASTER_BASE = ((-0.42, 0.0), (-0.30, 0.24), (0.30, 0.24), (0.42, 0.0))
PILASTER_SHAFT = ((-0.32, 0.0), (-0.24, 0.16), (0.24, 0.16), (0.32, 0.0))
PILASTER_CAPITAL = ((-0.44, 0.0), (-0.305, 0.27), (0.305, 0.27), (0.44, 0.0))
PILASTER = (
    (FLOOR, PILASTER_BASE), (FLOOR + 0.3, PILASTER_BASE), (FLOOR + 0.42, PILASTER_SHAFT),
    (9.12, PILASTER_SHAFT), (9.3, PILASTER_CAPITAL), (10.0, PILASTER_CAPITAL),
)


def _pilaster(mb: tb.MeshBuilder, phi: float) -> None:
    """Una pilastra en una esquina de dentro del tambor: basa, fuste y capitel, con los
    cantos en derrame y los cambios de sección inclinados. Acaba dentro de la cornisa."""
    frame = _facet(phi, R_IN)
    turn = frame.to_3x3()
    for (z0, low), (z1, high) in zip(PILASTER, PILASTER[1:]):
        for i in range(len(low) - 1):
            a, b, c, d = low[i], low[i + 1], high[i + 1], high[i]
            out = Vector((-(b[1] - a[1]), b[0] - a[0], 0.0))  # la sección va en sentido horario
            corners = [frame @ Vector((p[0], p[1], z)) for p, z in ((a, z0), (b, z0), (c, z1), (d, z1))]
            _facing(mb, corners, DETAIL, turn @ out)


def _dado(mb: tb.MeshBuilder) -> None:
    """El zócalo de mármol de la sala hasta los alféizares, con una franja de granito abajo y
    su moldura arriba: placas a ras del muro (cambios de color, sin cantos que se vean de
    canto), cortadas por las puertas."""
    reach = FACET_IN / 2.0 + 0.1
    cap = [(0.0, DADO - 0.07), (-0.05, DADO - 0.02), (-0.05, DADO + 0.03), (0.0, DADO + 0.1)]
    for k in range(BAYS):
        if k == 0:
            continue  # dentro de la esclusa
        door = k in ENTRANCE or k in WELDED

        def build(builder: tb.MeshBuilder, door=door) -> None:
            spans = [(-reach, DOOR[0], (False, True)), (DOOR[2], reach, (True, False))] if door else [(-reach, reach, (False, False))]
            for x0, x1, mitre in spans:
                for z0, z1, color in ((FLOOR - 0.01, FLOOR + 0.16, GRANITE_DARK), (FLOOR + 0.16, DADO, MARBLE)):
                    builder.quad([(x0, -0.003, z0), (x1, -0.003, z0), (x1, -0.003, z1), (x0, -0.003, z1)], color, cuts=1, jitter=0.03)
                kit.moulding(builder, (x0, x1), cap, MARBLE, jitter=0.02, mitre=mitre)

        _placed(mb, _inner(_bay_angle(k)), build)


def _hall(mb: tb.MeshBuilder) -> None:
    """Pilastras, zócalo, cornisa, la cúpula de dentro con sus casetones y el óculo."""
    for k in range(BAYS):
        _pilaster(mb, _column_angle(k))
    _dado(mb)
    # La cornisa de dentro, de arriba abajo: las caras miran a la sala.
    cornice = [(R_IN + 0.05, 10.4), (R_IN - 0.48, 10.28), (R_IN - 0.48, 10.06), (R_IN - 0.12, 9.72), (R_IN + 0.05, 9.66)]
    mb.lathe(cornice, (0.0, 0.0, 0.0), DETAIL, segments=96, sharp_angle=30.0)
    # La cúpula de dentro (de arriba abajo, para que mire a la sala), metida en el muro.
    top = math.acos(OCULUS / INNER_A)
    samples = [top * i / 14 for i in range(15)]
    inner = [(INNER_A * math.cos(t), INNER_BASE + INNER_B * math.sin(t)) for t in samples]
    mb.lathe([(R_IN + 0.1, INNER_BASE - 0.4), *inner][::-1], (0.0, 0.0, 0.0), DOME_IN, segments=96, sharp_angle=60.0, jitter=0.02)
    # Casetones: veinte nervios y dos anillos que salen hacia la sala, de canto en derrame.
    center = Vector((0.0, 0.0, INNER_BASE - 3.0))
    for k in range(BAYS):
        phi = _column_angle(k)
        radial = Vector((math.cos(phi), math.sin(phi), 0.0))
        lateral = Vector((-math.sin(phi), math.cos(phi), 0.0))
        path, sections = [], []
        for t in samples:
            point = radial * (INNER_A * math.cos(t)) + Vector((0.0, 0.0, INNER_BASE + INNER_B * math.sin(t)))
            inward = -(radial * (INNER_B * math.cos(t)) + Vector((0.0, 0.0, INNER_A * math.sin(t)))).normalized()
            path.append(point)
            sections.append([point - lateral * 0.24, point - lateral * 0.14 + inward * 0.16, point + lateral * 0.14 + inward * 0.16, point + lateral * 0.24])

        def facing(i: int, j: int, path=path, lateral=lateral) -> Vector:
            mid = (path[i] + path[i + 1]) / 2.0
            inward = (center - mid).normalized()
            return inward - lateral if j == 0 else (inward + lateral if j == 2 else inward)

        _sweep(mb, path, sections, DETAIL, facing)
    for t in (samples[5], samples[10]):
        r, z = INNER_A * math.cos(t), INNER_BASE + INNER_B * math.sin(t)
        n = Vector((INNER_B * math.cos(t), INNER_A * math.sin(t))).normalized()  # hacia fuera
        along = Vector((-n.y, n.x))  # cúpula arriba
        p = Vector((r, z))
        band = [p + along * 0.2, p - n * 0.14 + along * 0.12, p - n * 0.14 - along * 0.12, p - along * 0.2]
        mb.lathe([tuple(q) for q in band], (0.0, 0.0, 0.0), DETAIL, segments=96, sharp_angle=30.0)
    # El óculo: el anillo y el pozo hasta la linterna.
    mb.lathe([(OCULUS, LANTERN + 0.2), (OCULUS, INNER_BASE + INNER_B - 0.05), (OCULUS + 0.3, INNER_BASE + INNER_B - 0.2)], (0.0, 0.0, 0.0), DETAIL, segments=32, sharp_angle=40.0)


def _chandelier(mb: tb.MeshBuilder) -> None:
    """La gran lámpara: un aro de bronce con dieciséis globos (dos rotos), un cuenco en el
    centro con sus brazos y ocho cadenas hasta el anillo del óculo."""
    z = 8.6
    ring = [(2.28, z + 0.18), (2.1, z + 0.18), (2.1, z + 0.1), (2.25, z - 0.06), (2.45, z), (2.45, z + 0.18), (2.28, z + 0.18)]
    mb.lathe(ring, (0.0, 0.0, 0.0), BRONZE, segments=48, sharp_angle=40.0)
    for i in range(16):
        a = 2.0 * math.pi * i / 16
        c, s = math.cos(a), math.sin(a)
        mb.bar((2.28 * c, 2.28 * s, z - 0.04), (2.28 * c, 2.28 * s, z - 0.3), 0.015, BRONZE, 5)
        if i in (3, 11):  # dos globos rotos: queda el casquillo
            mb.lathe([(0.0, -0.08), (0.06, -0.06), (0.06, 0.0), (0.0, 0.0)], (2.28 * c, 2.28 * s, z - 0.3), BRONZE, segments=8)
            continue
        with mb.material(1):
            mb.lathe([(0.0, -0.17), (0.15, -0.1), (0.17, 0.02), (0.11, 0.14), (0.0, 0.17)], (2.28 * c, 2.28 * s, z - 0.47), GLOBE, segments=12)
    mb.lathe([(0.0, z - 0.9), (0.55, z - 0.6), (0.7, z - 0.25), (0.62, z - 0.1), (0.0, z - 0.1)], (0.0, 0.0, 0.0), BRONZE, segments=24, sharp_angle=40.0)
    for i in range(8):
        a = math.pi / 8.0 + i * math.pi / 4.0
        c, s = math.cos(a), math.sin(a)
        mb.bar((0.66 * c, 0.66 * s, z - 0.3), (2.1 * c, 2.1 * s, z + 0.05), 0.02, BRONZE, 6)
        mb.bar((2.28 * c, 2.28 * s, z + 0.18), (1.55 * c, 1.55 * s, INNER_BASE + INNER_B - 0.14), 0.015, BRONZE, 5)


def _turnstiles(mb: tb.MeshBuilder, solids: list) -> None:
    """Siete torniquetes con el lector de fichas hacia la sala; se pasa entre ellos."""
    profile = kit.ccw([(-0.55, 0.0), (0.55, 0.0), (0.55, 0.98), (-0.25, 0.98), (-0.55, 0.82)])
    normal = Vector((-0.16, 0.0, 0.3)).normalized()
    for i in range(7):
        y = -3.3 + i * 1.1
        with mb.material(3):
            mb.prism(profile, 0.24, (TURNSTILE_X, y, FLOOR), "#6C6E6A", rotation=(90.0, 0.0, 0.0), jitter=0.04)
        a = Vector((TURNSTILE_X - 0.55, y, FLOOR + 0.82))
        b = Vector((TURNSTILE_X - 0.25, y, FLOOR + 0.98))
        corners = [a.lerp(b, t) + normal * 0.003 + Vector((0.0, side * 0.08, 0.0)) for t, side in ((0.2, -1), (0.8, -1), (0.8, 1), (0.2, 1))]
        _facing(mb, corners, "#2A2C2A", normal)
        solids.append(((1.1, 0.24, 0.98), (TURNSTILE_X, y, FLOOR + 0.49), 0.0))


def _machines(mb: tb.MeshBuilder, solids: list) -> None:
    """Las máquinas de cambio, arrimadas al muro de la esclusa cuando la levantaron."""
    west = Vector((-1.0, 0.0, 0.0))
    for y in (1.55, 2.2, 2.85):
        x = LOCK_X - 0.33
        with mb.material(3):
            mb.box((0.62, 0.6, 1.74), (x, y, FLOOR + 0.87), "#5D6B70", bevel=0.03, jitter=0.05)
        front = x - 0.31 - 0.003
        _facing(mb, [(front, y - 0.2, FLOOR + 1.0), (front, y + 0.2, FLOOR + 1.0), (front, y + 0.2, FLOOR + 1.5), (front, y - 0.2, FLOOR + 1.5)], "#2A2C2A", west)
        _facing(mb, [(front, y - 0.24, FLOOR + 1.56), (front, y + 0.24, FLOOR + 1.56), (front, y + 0.24, FLOOR + 1.68), (front, y - 0.24, FLOOR + 1.68)], "#8E8A7A", west)
        mb.box((0.14, 0.3, 0.1), (front - 0.06, y, FLOOR + 0.85), "#3A3C3A")
        solids.append(((0.62, 0.6, 1.74), (x, y, FLOOR + 0.87), 0.0))


def _pram(mb: tb.MeshBuilder, solids: list) -> None:
    """Un cochecito de niño volcado junto a la entrada."""
    at, yaw = Vector((2.7, -6.2, FLOOR)), 35.0
    pivot = Matrix.Translation((0.0, -0.3, 0.0)) @ Matrix.Rotation(math.radians(80.0), 4, "X") @ Matrix.Translation((0.0, 0.3, 0.0))
    place = Matrix.Translation(at) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ pivot

    def build(builder: tb.MeshBuilder) -> None:
        body, dark, steel = "#3D4B5C", "#1C1C1C", "#4A4E50"
        builder.box((0.8, 0.44, 0.32), (0.0, 0.0, 0.6), body, bevel=0.08, segments=2, jitter=0.04)
        builder.box((0.34, 0.46, 0.36), (-0.25, 0.0, 0.84), _shade(body, 0.85), bevel=0.15, segments=3, jitter=0.04)
        for x in (-0.27, 0.27):
            for y in (-0.25, 0.25):
                builder.cylinder(0.16, 0.05, (x, y, 0.16), dark, rotation=(90.0, 0.0, 0.0), segments=14)
                builder.bar((x, y * 0.92, 0.16), (x * 0.7, y * 0.6, 0.46), 0.015, steel, 5)
        for y in (-0.19, 0.19):
            builder.bar((0.38, y, 0.62), (0.62, y, 0.98), 0.016, steel, 6)
        builder.bar((0.62, -0.2, 0.98), (0.62, 0.2, 0.98), 0.02, dark, 6)

    _placed(mb, place, build)
    center = at + Matrix.Rotation(math.radians(yaw), 3, "Z") @ Vector((0.1, -0.75, 0.0))
    solids.append(((1.3, 1.0, 0.6), (center.x, center.y, FLOOR + 0.3), yaw))


def _luggage(mb: tb.MeshBuilder, rng: random.Random, solids: list) -> None:
    """Maletas y fardos de la evacuación: sobre todo ante los torniquetes y junto a la
    entrada, nunca en el paso de la compuerta a la puerta."""
    path = [Vector(p) for p in PATH]
    placed = [(Vector((2.75, -6.85)), 0.8)]  # el cochecito

    def free(at: Vector, radius: float) -> bool:
        if at.length > 7.6 - radius:
            return False
        if min(_segment_distance(at, a, b) for a, b in zip(path, path[1:])) < 0.75 + radius:
            return False
        if TURNSTILE_X - 0.75 < at.x < LOCK_X + 0.1 and abs(at.y) < 4.2:
            return False
        return all((at - p).length > radius + r for p, r in placed)

    count, attempts = 0, 0
    while count < 30 and attempts < 800:
        attempts += 1
        if rng.random() < 0.55:
            at = Vector((rng.uniform(-3.6, TURNSTILE_X - 0.75), rng.uniform(-4.6, 4.6)))
        else:
            at = Vector((rng.uniform(-3.8, 3.4), rng.uniform(-8.0, -4.6)))
        bundle = rng.random() < 0.22
        if bundle:
            size = (rng.uniform(0.5, 0.8), rng.uniform(0.4, 0.6), 0.4)
        else:
            size = (rng.uniform(0.45, 0.8), rng.uniform(0.18, 0.32), rng.uniform(0.32, 0.55))
            if rng.random() < 0.65:
                size = (size[0], size[2], size[1])  # tumbada
        radius = 0.5 * math.hypot(size[0], size[1])
        turn = rng.uniform(0.0, 180.0)
        tilt = (rng.uniform(-6.0, 6.0), rng.uniform(-6.0, 6.0))
        color = rng.choice(BUNDLES if bundle else CASES)
        if not free(at, radius):
            continue
        center = (at.x, at.y, FLOOR + size[2] / 2.0)
        if bundle:
            mb.box(size, center, color, rotation=(tilt[0], tilt[1], turn), bevel=0.12, segments=2, jitter=0.08)
        else:
            mb.box(size, center, color, rotation=(0.0, 0.0, turn), bevel=0.02, jitter=0.08)
            _handle(mb, size, (at.x, at.y, FLOOR + size[2]), turn)
        placed.append((at, radius))
        solids.append((size, center, turn))
        count += 1


def _handle(mb: tb.MeshBuilder, size: tuple, top: tuple, turn: float) -> None:
    """El asa de una maleta, encima, a lo largo de su lado mayor."""
    a = math.radians(turn)
    along = Vector((math.cos(a), math.sin(a), 0.0)) * min(0.09, size[0] * 0.2)
    center, lift = Vector(top), Vector((0.0, 0.0, 0.035))
    for end in (-1.0, 1.0):
        mb.bar(center + along * end, center + along * end + lift, 0.01, "#2A2420", 5)
    mb.bar(center - along + lift, center + along + lift, 0.012, "#2A2420", 6)


def _fittings(mb: tb.MeshBuilder, rng: random.Random, solids: list) -> None:
    _turnstiles(mb, solids)
    _machines(mb, solids)
    _pram(mb, solids)
    _luggage(mb, rng, solids)


# --------------------------------------------------------------------------
# La esclusa, las escaleras y el túnel
# --------------------------------------------------------------------------


def _lock_front(builder: tb.MeshBuilder) -> None:
    """El muro de la compuerta, en su marco (el hueco baja hasta su pie: el umbral es el
    rellano)."""
    hole = (HATCH[0], FLOOR - 0.8, HATCH[2], HATCH[3])
    builder.slab((-LOCK_HALF, LOCK_HALF), (FLOOR - 0.75, FLOOR + LOCK_HEIGHT), (0.0, LOCK_WALL), CONCRETE, holes=[hole], step=1.0, jitter=0.03)


def _roof_z(x: float) -> float:
    """La cara de abajo del tejado de la esclusa en ``x``."""
    return FLOOR + LOCK_HEIGHT - max(0.0, x - LOCK_FLAT) * TAN


def _lock_shell(mb: tb.MeshBuilder, color: str) -> None:
    """El muro de la compuerta, los de los lados (del fondo del foso al tejado), el tejado,
    que baja con las escaleras hasta el muro del tambor, y el dintel de la boca del túnel."""
    _placed(mb, _front(), _lock_front)
    top = FLOOR + LOCK_HEIGHT
    side = kit.ccw([
        (LOCK_X, FLOOR - 0.75), (STAIR_TOP, FLOOR - 0.75), (PIT_END, _step_z(PIT_END) - 0.75),
        (PIT_END, _roof_z(PIT_END)), (LOCK_FLAT, top), (LOCK_X, top),
    ])
    for sign in (-1.0, 1.0):
        mb.prism(side, LOCK_WALL, (0.0, sign * (LOCK_HALF - LOCK_WALL / 2.0), 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.03)
    roof = kit.ccw([
        (LOCK_X - 0.3, top), (LOCK_FLAT, top), (PIT_END, _roof_z(PIT_END)),
        (PIT_END, _roof_z(PIT_END) + 0.3), (LOCK_FLAT, top + 0.3), (LOCK_X - 0.3, top + 0.3),
    ])
    mb.prism(roof, 2.0 * LOCK_HALF, (0.0, 0.0, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.03)
    mouth = _step_z(PORTAL_X) + CLEAR
    lintel = kit.ccw([(PORTAL_X, mouth), (PIT_END, mouth), (PIT_END, _roof_z(PIT_END)), (PORTAL_X, _roof_z(PORTAL_X))])
    mb.prism(lintel, 2.0 * (LOCK_HALF - LOCK_WALL), (0.0, 0.0, 0.0), color, rotation=(90.0, 0.0, 0.0), jitter=0.03)


def _tunnel_shell(builder: tb.MeshBuilder, color: str) -> None:
    """El túnel de las escaleras pasado el dintel, en el marco de las escaleras: los muros,
    el techo y, debajo de todo, el fondo del foso."""
    s0, s1 = _tunnel_start(), _tunnel_end()
    ceiling = CLEAR * math.cos(SLOPE)
    length, mid = s1 - s0, (s0 + s1) / 2.0
    for sign in (-1.0, 1.0):
        builder.box((length, LOCK_WALL, ceiling + 0.9), (mid, sign * (LOCK_HALF - LOCK_WALL / 2.0), (ceiling - 0.3) / 2.0), color)
    builder.box((length, 2.0 * LOCK_HALF, 0.3), (mid, 0.0, ceiling + 0.15), color)
    builder.box((s1 + 0.5, 2.0 * (LOCK_HALF - LOCK_WALL), 0.1), ((s1 - 0.5) / 2.0, 0.0, -0.55), "#2A2826")


def _tunnel_details(builder: tb.MeshBuilder) -> None:
    """Las vigas del techo y las pilastras del túnel y, al fondo, la oscuridad."""
    s0, s1 = _tunnel_start(), _tunnel_end()
    ceiling = CLEAR * math.cos(SLOPE)
    inner = LOCK_HALF - LOCK_WALL
    s = s0 + 0.6
    while s < s1 - 0.6:
        builder.box((0.3, 2.0 * inner, 0.18), (s, 0.0, ceiling - 0.09), CONCRETE, jitter=0.03)
        for sign in (-1.0, 1.0):
            builder.box((0.3, 0.15, ceiling + 0.5), (s, sign * (inner - 0.075), (ceiling - 0.5) / 2.0), CONCRETE, jitter=0.03)
        s += 2.4
    with builder.material(2):
        builder.box((0.2, 2.0 * inner, ceiling + 0.6), (s1 - 0.3, 0.0, (ceiling - 0.6) / 2.0), DARK)


def _escalators(mb: tb.MeshBuilder) -> None:
    """El rellano, las tres escaleras mecánicas (paradas desde la evacuación) con sus
    balaustradas, pasamanos y farolas, y las repisas de los lados."""
    inner = LOCK_HALF - LOCK_WALL
    width = 1.5 - 0.18
    rise = 0.4 * TAN
    with mb.material(3):
        mb.box((STAIR_TOP - LOCK_X - 0.02, 2.0 * inner, 0.754), ((LOCK_X + 0.02 + STAIR_TOP) / 2.0, 0.0, FLOOR + 0.004 - 0.377), "#3C3A36", cuts=2)
        for lane in LANES:
            for i in range(int(round(STAIR_RUN / 0.4))):
                x, z = STAIR_TOP + i * 0.4, FLOOR - i * rise
                mb.box((0.4, width, 0.06), (x + 0.2, lane, z - 0.03), "#3A3C3A")
                mb.box((0.04, width, rise - 0.06), (x + 0.38, lane, z - 0.06 - (rise - 0.06) / 2.0), "#2C2E2C")
    length = STAIR_RUN / math.cos(SLOPE)

    def rails(builder: tb.MeshBuilder) -> None:
        for y in BALUSTRADES:
            builder.box((length, 0.18, 0.95), (length / 2.0, y, 0.475), BALUSTRADE, jitter=0.03)
            with builder.material(3):
                builder.box((length + 0.3, 0.12, 0.08), (length / 2.0, y, 0.99), "#1E1D1B")
        for sign in (-1.0, 1.0):
            builder.box((length, inner - 2.34, 0.1), (length / 2.0, sign * (inner + 2.34) / 2.0, 0.9), BALUSTRADE, jitter=0.03)
        _tunnel_shell(builder, CONCRETE)
        _tunnel_details(builder)

    _placed(mb, _tilted(), rails)
    for y in BALUSTRADES:  # el arranque de las balaustradas, en el rellano
        mb.box((1.55, 0.18, 0.95), (STAIR_TOP - 0.225, y, FLOOR + 0.475), BALUSTRADE, jitter=0.03)
        with mb.material(3):
            mb.box((1.55, 0.12, 0.08), (STAIR_TOP - 0.225, y, FLOOR + 0.99), "#1E1D1B")
    for y in (-0.75, 0.75):  # farolas de pie sobre las balaustradas de en medio
        for s in (3.0, 6.3, 11.1, 15.9):
            base = _tilted() @ Vector((s, y, 1.03))
            mb.bar(base, base + Vector((0.0, 0.0, 0.8)), 0.03, BRONZE, 6)
            with mb.material(1):
                mb.lathe([(0.0, -0.18), (0.13, -0.09), (0.15, 0.06), (0.1, 0.16), (0.0, 0.2)], (base.x, base.y, base.z + 0.98), GLOBE, segments=10)


def _hazard_band(builder: tb.MeshBuilder) -> None:
    """Franjas de peligro amarillas y negras alrededor de la compuerta, pintadas (a ras del
    muro, en el marco del muro: la cara en y = 0 y la sala hacia -y)."""
    x0, _, x1, z1 = HATCH
    inner, outer, width = 0.14, 0.4, 0.15
    rects = (
        (x0 - outer, FLOOR, x0 - inner, z1 + inner),
        (x1 + inner, FLOOR, x1 + outer, z1 + inner),
        (x0 - outer, z1 + inner, x1 + outer, z1 + outer),
    )
    for rx0, rz0, rx1, rz1 in rects:
        box = [(rx0, rz0), (rx1, rz0), (rx1, rz1), (rx0, rz1)]
        k = math.floor((rx0 - rz1) / (2.0 * width)) - 1
        while k * 2.0 * width < rx1 - rz0:
            for start, color in ((0.0, "#B8962E"), (width, "#22201E")):
                c = k * 2.0 * width + start
                piece = _clip(_clip(box, 1.0, -1.0, -c), -1.0, 1.0, c + width)
                if len(piece) >= 3 and _area(piece) > 1e-5:
                    builder.polygon([(x, -0.002, z) for x, z in piece], color)
            k += 1


def _civil_defence_sign(builder: tb.MeshBuilder) -> None:
    """La placa de la defensa civil sobre la compuerta: «ГО» en rojo sobre blanco."""
    x0, x1, z0, z1 = -0.45, 0.45, HATCH[3] + 0.52, HATCH[3] + 0.98
    builder.quad([(x0, -0.002, z0), (x1, -0.002, z0), (x1, -0.002, z1), (x0, -0.002, z1)], "#C9C4B4", cuts=1, jitter=0.03)
    h, s, base = 0.3, 0.06, z0 + 0.08
    strokes = [[(-0.3, base), (-0.3 + s, base), (-0.3 + s, base + h), (-0.3, base + h)]]  # Г
    strokes.append([(-0.3 + s, base + h - s), (-0.1, base + h - s), (-0.1, base + h), (-0.3 + s, base + h)])
    cx, cz, rx, rz = 0.15, base + h / 2.0, 0.11, h / 2.0  # О
    for i in range(8):
        a0, a1 = math.pi * 2.0 * i / 8 + math.pi / 8, math.pi * 2.0 * (i + 1) / 8 + math.pi / 8
        outer = [(cx + rx * math.cos(a), cz + rz * math.sin(a)) for a in (a0, a1)]
        inner = [(cx + (rx - s) * math.cos(a), cz + (rz - s) * math.sin(a)) for a in (a1, a0)]
        strokes.append(outer + inner)
    for polygon in strokes:
        builder.polygon([(x, -0.004, z) for x, z in kit.ccw(polygon)], "#8E2A22")


def _airlock(mb: tb.MeshBuilder) -> None:
    """La esclusa con el marco de acero de la compuerta, sus franjas, la placa y el aplique,
    las escaleras y el túnel."""
    _lock_shell(mb, CONCRETE)

    def front(builder: tb.MeshBuilder) -> None:
        x0, z0, x1, z1 = HATCH
        with builder.material(3):
            kit.outline(builder, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], [(0.0, 0.0), (0.0, 0.1), (0.1, 0.1), (0.14, 0.0)], STEEL)
            builder.box((0.24, 0.12, 0.18), (x1 + 0.75, -0.06, z1 + 0.25), "#3A3C3A")
        _hazard_band(builder)
        _civil_defence_sign(builder)
        with builder.material(1):
            builder.box((0.18, 0.02, 0.12), (x1 + 0.75, -0.125, z1 + 0.25), GLOBE)

    _placed(mb, _front(), front)
    _escalators(mb)


def _hatch(mb: tb.MeshBuilder) -> None:
    """La compuerta blindada, abierta hacia la sala: una hoja de acero con su volante, sus
    bisagras y sus cerrojos."""

    def build(builder: tb.MeshBuilder) -> None:
        width = HATCH[2] - HATCH[0]
        builder.box((0.14, width, HATCH[3] - HATCH[1]), (-0.07, width / 2.0, (HATCH[1] + HATCH[3]) / 2.0), STEEL, cuts=2, jitter=0.04)
        for z in (FLOOR + 0.35, FLOOR + 1.85):  # bisagras
            builder.box((0.2, 0.16, 0.28), (-0.05, 0.0, z), "#2E3032")
        hub = Vector((-0.2, width / 2.0, FLOOR + 1.15))
        builder.bar((-0.14, hub.y, hub.z), hub, 0.04, "#2E3032", 8)
        for i in range(4):
            a = math.pi / 4.0 + i * math.pi / 2.0
            builder.bar(hub, hub + Vector((0.0, 0.3 * math.cos(a), 0.3 * math.sin(a))), 0.022, "#3A3C3E", 6)
        rim = [(0.31, -0.025), (0.33, -0.025), (0.33, 0.025), (0.29, 0.025), (0.29, -0.025), (0.31, -0.025)]
        builder.lathe(rim, hub, "#3A3C3E", rotation=(0.0, 90.0, 0.0), segments=20)
        for z in (FLOOR + 0.5, FLOOR + 1.15, FLOOR + 1.8):  # cerrojos
            builder.box((0.08, 0.36, 0.08), (-0.18, width - 0.28, z), "#2E3032")

    _placed(mb, _hatch_frame(), build)


# --------------------------------------------------------------------------
# Alrededor: el control del ejército, las farolas y la «M»
# --------------------------------------------------------------------------

SANDBAG_WALLS = (
    ((-6.2, -15.4), (-2.2, -16.6), 4), ((-6.2, -15.4), (-7.3, -13.5), 4),
    ((2.2, -16.6), (6.2, -15.4), 4), ((6.2, -15.4), (7.3, -13.5), 3),
)
BLOCKS = ((-3.6, -18.5, 8.0), (3.4, -18.6, -12.0), (-9.6, -16.4, 40.0), (9.3, -16.9, -35.0))
LAMPS = ((-10.4, -16.6), (12.0, -15.9), (-15.6, 4.0), (14.8, 6.0))
SENTRY = (8.4, -18.2)
PYLON = (13.9, -12.9)
BARRIER = (-2.6, -17.8)


def _sandbags(mb: tb.MeshBuilder, rng: random.Random, start: Vector, end: Vector, rows: int) -> None:
    """Un muro de sacos terreros de ``start`` a ``end``, a hiladas trabadas."""
    along = end - start
    count = max(2, int(along.length / 0.62))
    angle = math.degrees(math.atan2(along.y, along.x))
    for row in range(rows):
        for i in range(count - (row % 2)):
            t = (i + 0.5 + 0.5 * (row % 2)) / count
            at = start.lerp(end, t)
            mb.box((0.6, 0.36, 0.2), (at.x, at.y, 0.1 + row * 0.19), rng.choice(("#6B6550", "#5E5A47", "#736C55")), rotation=(rng.uniform(-3, 3), rng.uniform(-3, 3), angle + rng.uniform(-6, 6)), bevel=0.06, segments=2, jitter=0.08)


def _lamp_post(mb: tb.MeshBuilder, at: Vector) -> None:
    """Farola de fundición: basa, fuste, cruceta y dos faroles de globo."""
    with mb.material(1):
        mb.lathe([(0.0, 0.0), (0.22, 0.0), (0.22, 0.35), (0.12, 0.6), (0.09, 0.8), (0.07, 3.6), (0.1, 3.75), (0.0, 3.8)], (at.x, at.y, 0.0), "#2C2E2E", segments=12)
        mb.box((1.5, 0.08, 0.08), (at.x, at.y, 3.7), "#2C2E2E")
    for side in (-0.7, 0.7):
        with mb.material(2):
            mb.lathe([(0.0, -0.22), (0.17, -0.12), (0.2, 0.05), (0.13, 0.2), (0.0, 0.22)], (at.x + side, at.y, 3.48), GLOBE, segments=12)


def _surroundings(mb: tb.MeshBuilder, rng: random.Random, solids: list) -> None:
    """El control ante la escalinata (sacos, bloques, la barrera levantada y la garita), las
    farolas de la explanada, el pilón de la «M» y el equipaje tirado fuera."""
    for start, end, rows in SANDBAG_WALLS:
        a, b = Vector((*start, 0.0)), Vector((*end, 0.0))
        _sandbags(mb, rng, a, b, rows)
        height = 0.1 + rows * 0.19
        turn = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        solids.append((((b - a).length + 0.3, 0.42, height), ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0, height / 2.0), turn))
    for x, y, turn in BLOCKS:
        mb.box((1.6, 0.6, 0.85), (x, y, 0.425), "#7A766E", rotation=(0.0, 0.0, turn), bevel=0.05, cuts=1, jitter=0.05)
        solids.append(((1.6, 0.6, 0.85), (x, y, 0.425), turn))
    with mb.material(1):
        mb.box((0.25, 0.25, 1.05), (BARRIER[0], BARRIER[1], 0.52), "#3A3C3C")
        for i in range(8):  # la barrera, a franjas rojas y blancas, levantada
            mb.box((0.62, 0.1, 0.1), (BARRIER[0] + 0.4 + i * 0.6, BARRIER[1], 1.15 + i * 0.6 * math.tan(math.radians(14.0))), "#9A2C24" if i % 2 == 0 else "#C9C2B2", rotation=(0.0, -14.0, 0.0))
    solids.append(((0.25, 0.25, 1.05), (BARRIER[0], BARRIER[1], 0.52), 0.0))
    # La garita: tablas pintadas, un ventanuco y un tejadillo a un agua.
    sx, sy = SENTRY
    mb.box((1.3, 1.3, 2.3), (sx, sy, 1.15), "#5D6650", cuts=1, jitter=0.05)
    _facing(mb, [(sx - 0.35, sy - 0.653, 1.4), (sx + 0.35, sy - 0.653, 1.4), (sx + 0.35, sy - 0.653, 1.9), (sx - 0.35, sy - 0.653, 1.9)], DARK, Vector((0.0, -1.0, 0.0)))
    mb.box((1.6, 1.6, 0.08), (sx, sy, 2.42), "#3E4438", rotation=(-8.0, 0.0, 0.0))
    solids.append(((1.3, 1.3, 2.3), (sx, sy, 1.15), 0.0))
    for x, y in LAMPS:
        _lamp_post(mb, Vector((x, y, 0.0)))
        solids.append(((0.3, 0.3, 3.8), (x, y, 1.9), 0.0))
    # El pilón de la «M»: una caja de luz roja, apagada, sobre un poste de piedra.
    px, py = PYLON
    mb.box((0.55, 0.55, 3.6), (px, py, 1.8), DETAIL, cuts=2, jitter=0.03)
    mb.box((1.5, 0.5, 1.5), (px, py, 4.35), "#2E2C2A", bevel=0.04)
    solids.append(((0.55, 0.55, 3.6), (px, py, 1.8), 0.0))

    def letter(builder: tb.MeshBuilder) -> None:
        w, h, s = 1.0, 1.0, 0.2
        strokes = [[(-w / 2, 3.85), (-w / 2 + s, 3.85), (-w / 2 + s, 3.85 + h), (-w / 2, 3.85 + h)]]
        strokes += [[(w / 2 - s, 3.85), (w / 2, 3.85), (w / 2, 3.85 + h), (w / 2 - s, 3.85 + h)]]
        strokes += [_stroke((-w / 2 + s * 0.5, 3.85 + h - s * 0.6), (0.0, 3.85 + h * 0.36), s)]
        strokes += [_stroke((0.0, 3.85 + h * 0.36), (w / 2 - s * 0.5, 3.85 + h - s * 0.6), s)]
        for i, polygon in enumerate(strokes):
            kit.raised(builder, polygon, 0.08 - 0.005 * i, "#8E2A22", splay=0.02)

    for turn in (0.0, math.pi):
        frame = Matrix.Translation((px, py, 0.0)) @ Matrix.Rotation(turn, 4, "Z") @ Matrix.Translation((0.0, -0.25, 0.0))
        _placed(mb, frame, letter)
    # Equipaje tirado delante del control, lejos del paso.
    obstacles = [(Vector((x, y)), 1.0) for x, y, _ in BLOCKS] + [(Vector(SENTRY), 1.1), (Vector(BARRIER), 0.4)]
    obstacles += [(Vector(p), 0.5) for p in LAMPS]
    count, attempts = 0, 0
    while count < 10 and attempts < 300:
        attempts += 1
        at = Vector((rng.uniform(-8.5, 8.0), rng.uniform(-18.7, -17.0)))
        size = (rng.uniform(0.45, 0.8), rng.uniform(0.3, 0.5), 0.28)
        turn = rng.uniform(0.0, 180.0)
        color = rng.choice(CASES[:4])
        radius = 0.5 * math.hypot(size[0], size[1])
        if abs(at.x + 0.47) < 1.6 or any((at - p).length < r + radius for p, r in obstacles):
            continue
        if any(_segment_distance(at, Vector(a), Vector(b)) < 0.3 + radius for a, b, _ in SANDBAG_WALLS):
            continue
        mb.box(size, (at.x, at.y, 0.14), color, rotation=(0.0, 0.0, turn), bevel=0.02, jitter=0.08)
        _handle(mb, size, (at.x, at.y, 0.28), turn)
        obstacles.append((at, radius))
        solids.append((size, (at.x, at.y, 0.14), turn))
        count += 1


# --------------------------------------------------------------------------
# Colisión y contexto
# --------------------------------------------------------------------------


def _drum_walls(mb: tb.MeshBuilder, holes_of) -> None:
    """Los veinte lados del tambor sin adornos (``holes_of(k)``: sus huecos)."""
    for k in range(BAYS):
        holes = holes_of(k)

        def build(builder: tb.MeshBuilder, holes=holes) -> None:
            builder.slab((-FACET / 2.0, FACET / 2.0), (FLOOR - 0.35, DRUM_TOP), (0.0, WALL), STUCCO, holes=holes)

        _placed(mb, _facet(_bay_angle(k)), build)


def _collision(mb: tb.MeshBuilder, solids: list) -> None:
    """Lo que se pisa y lo que para: el basamento (los escalones, una rampa), el suelo de la
    sala, el tambor con la puerta de salida abierta y su hoja, las columnas, la esclusa (sin
    la hoja de la compuerta, que se mueve en el juego), el rellano y las escaleras (otra
    rampa, entre sus balaustradas), el túnel y las cosas sueltas de dentro y de fuera."""
    mb.lathe([(PODIUM + 0.05, -0.4), (PODIUM + 0.05, 0.0), (PODIUM - 0.7, FLOOR), (APOTHEM_IN - 0.1, FLOOR)], (0.0, 0.0, 0.0), GRANITE, segments=48)
    for polygon, _, _ in _floor_tiles((0.0, 3.0, 6.0, R_IN + 0.05), lambda i: BAYS):
        for piece in _outside_lock(polygon):
            mb.polygon([(x, y, FLOOR) for x, y in piece], GRANITE)
    _drum_walls(mb, lambda k: [(DOOR[0], FLOOR, 0.05, DOOR[3])] if k == MAIN else [])
    # La hoja abierta de la puerta de salida: gira sobre su canto izquierdo (x0 + marco).
    hinge = Vector((DOOR[0] + 0.06, 0.18))
    tip = hinge + Vector((math.cos(math.radians(-MAIN_SWING)), math.sin(math.radians(-MAIN_SWING)))) * 0.94
    mid = (hinge + tip) / 2.0
    _placed(mb, _facet(_bay_angle(MAIN)), lambda b: b.box((0.94, 0.08, 3.5), (mid.x, mid.y, FLOOR + 1.81), DOOR_WOOD, rotation=(0.0, 0.0, -MAIN_SWING)))
    for k in range(BAYS):
        phi = _column_angle(k)
        mb.cylinder(0.5, COL_TOP - FLOOR, (R_COL * math.cos(phi), R_COL * math.sin(phi), (COL_TOP + FLOOR) / 2.0), DETAIL, segments=8)
    _lock_shell(mb, CONCRETE)
    # La compuerta no: se abre y se cierra en el juego, con su propia colisión (F3-14).
    inner = LOCK_HALF - LOCK_WALL
    mb.box((STAIR_TOP + 0.2 - LOCK_X, 2.0 * inner, 0.3), ((LOCK_X + STAIR_TOP + 0.2) / 2.0, 0.0, FLOOR - 0.15), CONCRETE)
    length = STAIR_RUN / math.cos(SLOPE)

    def slope(builder: tb.MeshBuilder) -> None:
        # La rampa pasa por en medio de los peldaños (un dedo por encima de sus narices).
        builder.box((length - 0.2, 2.0 * inner, 0.1), (0.2 + (length - 0.2) / 2.0, 0.0, 0.05), CONCRETE)
        for y in BALUSTRADES:
            builder.box((length, 0.18, 0.95), (length / 2.0, y, 0.475), CONCRETE)
        for sign in (-1.0, 1.0):
            builder.box((length, inner - 2.34, 0.95), (length / 2.0, sign * (inner + 2.34) / 2.0, 0.475), CONCRETE)
        _tunnel_shell(builder, CONCRETE)
        ceiling = CLEAR * math.cos(SLOPE)
        builder.box((0.3, 2.0 * LOCK_HALF, ceiling + 0.6), (_tunnel_end() - 0.3, 0.0, (ceiling - 0.6) / 2.0), CONCRETE)

    _placed(mb, _tilted(), slope)
    for y in BALUSTRADES:
        mb.box((1.55, 0.18, 0.95), (STAIR_TOP - 0.225, y, FLOOR + 0.475), CONCRETE)
    for size, center, turn in solids:
        mb.box(size, center, CONCRETE, rotation=(0.0, 0.0, turn))


def _ground_hole(mb: tb.MeshBuilder) -> None:
    """Dónde no va el terreno: el disco del basamento. Dentro están el suelo de la sala y el
    foso de las escaleras, que bajan bajo la cota de la calle; el borde dentado de la
    rejilla del terreno queda debajo del basamento."""
    r = PODIUM - 0.15
    mb.polygon([(r * math.cos(2.0 * math.pi * i / 32), r * math.sin(2.0 * math.pi * i / 32), 0.0) for i in range(32)], GRANITE)


def _context() -> object:
    """Los muros del tambor y la esclusa, para pintar la sombra que echan sobre la sala."""
    mb = tb.MeshBuilder(seed=600)

    def holes(k: int) -> list:
        if k in WALLED:
            return [CLERESTORY]
        door = k in ENTRANCE or k in WELDED
        return [(DOOR[0], FLOOR - 0.4, DOOR[2], DOOR[3]) if door else WINDOW, CLERESTORY]

    _drum_walls(mb, holes)
    _lock_shell(mb, CONCRETE)
    _to_plan(mb)
    return mb.finish("contexto_vestibulo")


# --------------------------------------------------------------------------
# La biblioteca
# --------------------------------------------------------------------------


def build_kit() -> object:
    lib = kit.KitLibrary("singular_vestibulo", columns=4, spacing=60.0)
    inside: list = []
    outside: list = []
    # Por fuera: basamento, tambor, columnata, entablamento, jarrones y la tabla.
    mb = tb.MeshBuilder(seed=601)
    _podium(mb)
    _drum(mb, random.Random(601))
    with mb.material(3):
        for k in range(BAYS):
            _column(mb, _column_angle(k))
        _entablature(mb)
        _vases(mb)
        _tablet(mb)
    _to_plan(mb)
    piece = mb.finish("vestibulo", kit.materials("nevado", "vidrio", "interior", "estuco", "metal"))
    tb.stain(piece, "#2A2522", amount=0.5, scale=0.9, coverage=0.35, seed=601, stretch_z=0.35)
    lib.add(piece, [], alpha=_wear, samples=10, ao=0.45, ao_distance=0.8, ground_z=0.0, seed=601)
    # La cúpula, la linterna y la estrella.
    mb = tb.MeshBuilder(seed=602)
    _dome(mb)
    _to_plan(mb)
    piece = mb.finish("vestibulo_cupula", kit.materials("nevado", "estuco"))
    tb.stain(piece, "#3A4038", amount=0.35, scale=1.2, coverage=0.3, seed=602, stretch_z=0.5)
    lib.add(piece, [], samples=8, ao=0.4, ao_distance=0.6, seed=602)
    # La sala por dentro, con sus cosas (pintada con la sombra de los muros).
    mb = tb.MeshBuilder(seed=603)
    _floor(mb)
    _hall(mb)
    _chandelier(mb)
    _fittings(mb, random.Random(603), inside)
    _to_plan(mb)
    piece = mb.finish("vestibulo_sala", kit.materials("sala", "vidrio", "interior", "metal"))
    tb.stain(piece, "#3A332C", amount=0.3, scale=1.4, coverage=0.3, seed=603)
    lib.add(piece, [_context()], samples=10, ao=0.55, ao_distance=1.2, seed=603)
    # La esclusa con las escaleras y el túnel, y la compuerta (aparte, para poder moverla).
    mb = tb.MeshBuilder(seed=604)
    _airlock(mb)
    _to_plan(mb)
    piece = mb.finish("vestibulo_esclusa", kit.materials("sala", "vidrio", "interior", "metal"))
    tb.stain(piece, "#2E2A26", amount=0.4, scale=1.1, coverage=0.35, seed=604, stretch_z=0.4)
    lib.add(piece, [], samples=8, ao=0.55, ao_distance=1.0, seed=604)
    mb = tb.MeshBuilder(seed=605)
    _hatch(mb)
    _to_plan(mb)
    lib.add(mb.finish("vestibulo_compuerta", kit.materials("metal")), [], samples=6, seed=605)
    # Alrededor.
    mb = tb.MeshBuilder(seed=606)
    _surroundings(mb, random.Random(606), outside)
    _to_plan(mb)
    piece = mb.finish("vestibulo_entorno", kit.materials("nevado", "metal", "vidrio"))
    tb.stain(piece, "#2A2522", amount=0.4, scale=1.5, coverage=0.3, seed=606)
    lib.add(piece, [], samples=8, ao=0.5, ao_distance=0.8, ground_z=0.0, seed=606)
    # La colisión (no se dibuja).
    mb = tb.MeshBuilder(seed=607)
    _collision(mb, inside + outside)
    _to_plan(mb)
    lib.add(mb.finish("vestibulo_colision", kit.materials("colision")), [], samples=1, seed=607)
    # El hueco del terreno (tampoco se dibuja).
    mb = tb.MeshBuilder(seed=608)
    _ground_hole(mb)
    _to_plan(mb)
    lib.add(mb.finish("vestibulo_hueco", kit.materials("hueco")), [], samples=1, seed=608)
    return lib.root


def models() -> dict:
    return {"singular_vestibulo": build_kit}
