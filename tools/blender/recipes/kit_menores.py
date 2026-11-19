"""Kit de arquitectura: los edificios menores en los que se entra (F3-14).

Una biblioteca, "kit_menores", con los modelos enteros de lo pequeño que se saquea en La
Plaza y alrededores. Godot escoge el que toca por su tipo, su nombre y su daño, y lo
coloca sobre la huella a lo largo de su lado más largo (scripts/surface/kit_minor.gd);
los trasteros son una hilera de casetas. Cada modelo lleva su colisión hecha a mano
("<modelo>_colision", que no se dibuja) y lo que se mueve va aparte: las hojas de las
puertas ("<modelo>_puerta"), hechas en el marco de su bisagra, y el candado y la cadena.

- El quiosco de prensa (4 × 3 m): chapa pintada abajo, cristal arriba (roto a trozos,
  con periódicos pegados), la banda roja con ПЕЧАТЬ, el mostrador y los estantes. La
  puerta, detrás. Destrozado: sin cristales, la chapa abollada y el techo vencido.
- La tienda de la evacuación (9 × 7 m): lona del ejército sobre postes, con sus vientos
  y estacas, la puerta enrollada en un piñón, catres, mantas, maletas y la estufa.
  Caída (media tienda en el suelo) y de la Cruz Roja.
- El trastero (una caseta de 3 × 6 m de una hilera): tablas, cubierta de tela
  asfáltica a un agua, estantes con tarros. Hundido: la cubierta dentro.
- El palomar (5 × 5 m): el altillo sobre cuatro postes, la jaula, la plataforma con su
  barandilla y la escalera de mano.
- El transformador (8 × 6 m): ladrillo, rejillas, la puerta de chapa con el rayo, los
  aisladores y dentro los dos transformadores y el armario.
- El candado, la cadena y unos huesos (las señales de la Jauría).

Coordenadas: el origen en el centro de la huella, en el suelo; x a lo largo del lado
largo, y a lo ancho y z hacia arriba. La fachada principal mira hacia -y (en Godot,
+z). Las hojas de las puertas: el origen abajo, en el eje de la bisagra; x a lo largo
de la hoja, z arriba, y se abren hacia -y.
"""

from __future__ import annotations

import math
import random

from mathutils import Matrix, Vector

import kit_bpy as kit
import tumansk_bpy as tb

# Colores (sRGB).
KIOSK = "#4F6B6A"  # chapa pintada de verde azulado
KIOSK_DARK = "#3C5150"
CREAM = "#B9B29C"
SIGN_RED = "#7A2B25"
GLASS = "#1F2228"
SHARD = "#3A4046"
PAPER = ("#BDB49C", "#C9C0A6", "#A9A08A", "#8E8A7A")
CARTONS = ("#8E3B2E", "#4A5A6A", "#B59A5A", "#5A6A48", "#7A6A5A")
CANVAS = "#5D5A41"
CANVAS_DARK = "#4A4733"
CANVAS_WHITE = "#B8B3A0"
CROSS = "#8A2A22"
POLE = "#5A4A38"
ROPE = "#8A7A5C"
BLANKETS = ("#4E5442", "#5A5248", "#6A6A60", "#3E4438")
CASES = ("#5A4636", "#3F4A3C", "#6A5A44", "#4A3A30", "#565A5C", "#704A35")
PLANK = "#6B5844"
PLANK_DARK = "#4E3E30"
PLANKS = ("#6B5844", "#5A4432", "#7A6650", "#4E3D2E")
TAR = "#2E2B29"
JAR = "#7E8A6A"
BRICK = "#7A4A3A"
CONCRETE = "#6E6A62"
STEEL = "#4A4E50"
STEEL_LIGHT = "#7C807F"
RUST = "#6E3F2A"
YELLOW = "#B89A3A"
INK = "#1E1B19"
PORCELAIN = "#C8C2B4"
BONE = "#C9BFA6"
DARK = "#121110"

# El quiosco.
QL, QD = 4.0, 3.0
Q_PANEL = 1.0  # lo alto de la chapa de abajo
Q_GLASS = 2.4  # lo alto del cristal
Q_FASCIA = 2.9
Q_DOOR = (0.5, 1.3)  # el hueco de la puerta, detrás (+y), en x
Q_DOOR_H = 2.0
# La tienda.
TL, TD = 9.0, 7.0
T_WALL = 1.6
T_RIDGE = 2.7
T_DOOR = 0.75  # medio ancho de la puerta, en el piñón de -x
# El trastero.
SW, SD = 3.0, 6.0
S_FRONT, S_BACK = 2.5, 2.1
S_DOOR = 0.425
S_DOOR_H = 1.9
# El palomar.
P_POST = 1.1
P_FLOOR = 3.1
P_LOFT = 1.3
P_WALL = 1.9
P_DOOR = 0.35
# El transformador.
XL, XD = 8.0, 6.0
X_WALL = 0.38
X_TOP = 3.8
X_DOOR = 0.6
X_DOOR_H = 2.2


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------


def _panel(mb: tb.MeshBuilder, corners: list, outward: Vector, color: str, inside: str) -> None:
    """Un trozo de lona plano y convexo: su cara de fuera mirando hacia ``outward`` y, un
    dedo más adentro, la de dentro (material 1), para que se vea desde los dos lados."""
    points = [Vector(p) for p in corners]
    normal = (points[1] - points[0]).cross(points[-1] - points[0])
    if normal.length < 1e-9:
        return
    if normal.dot(outward) < 0.0:
        points.reverse()
        normal = -normal
    mb.polygon(points, color, jitter=0.04)
    offset = normal.normalized() * 0.012
    with mb.material(1):
        mb.polygon([p - offset for p in reversed(points)], inside, jitter=0.04)


def _cloth(mb: tb.MeshBuilder, rows: list, outward: Vector, color: str, inside: str) -> None:
    """Una lona: una rejilla de puntos (filas de igual largo), cara a cara con [_panel]."""
    for j in range(len(rows) - 1):
        for i in range(len(rows[j]) - 1):
            corners = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
            _panel(mb, corners, outward, color, inside)


def _sag(u: float, v: float, depth: float) -> float:
    """Lo que cede una lona entre sus apoyos (u y v de 0 a 1 en cada tramo)."""
    return depth * math.sin(math.pi * u) * math.sin(math.pi * v)


def _letters(mb: tb.MeshBuilder, text: str, center: tuple, height: float, color: str) -> None:
    """Letras de molde en relieve sobre una fachada que mira a -y (en x, z), de
    trazos rectos: П, Е, Ч, А, Т y Ь (las de ПЕЧАТЬ)."""
    w, s, gap = height * 0.62, height * 0.17, height * 0.22
    x = center[0] - (len(text) * w + (len(text) - 1) * gap) / 2.0
    y, z0, h = center[1], center[2] - height / 2.0, height

    def bar(x0: float, z_0: float, x1: float, z_1: float) -> None:
        mb.box((x1 - x0, 0.02, z_1 - z_0), (x + (x0 + x1) / 2.0, y - 0.01, z0 + (z_0 + z_1) / 2.0), color)

    for letter in text:
        if letter == "П":
            bar(0.0, 0.0, s, h)
            bar(w - s, 0.0, w, h)
            bar(0.0, h - s, w, h)
        elif letter == "Е":
            bar(0.0, 0.0, s, h)
            bar(0.0, h - s, w, h)
            bar(0.0, (h - s) / 2.0, w * 0.8, (h + s) / 2.0)
            bar(0.0, 0.0, w, s)
        elif letter == "Ч":
            bar(0.0, h * 0.45, s, h)
            bar(w - s, 0.0, w, h)
            bar(0.0, h * 0.45, w, h * 0.45 + s)
        elif letter == "А":
            for sign in (-1.0, 1.0):
                tilt = math.degrees(math.atan2(w * 0.4, h)) * sign
                mb.box((s, 0.02, h * 1.02), (x + w / 2.0 - sign * w * 0.22, y - 0.01, z0 + h / 2.0), color, rotation=(0.0, tilt, 0.0))
            bar(w * 0.2, h * 0.3, w * 0.8, h * 0.3 + s)
        elif letter == "Т":
            bar(0.0, h - s, w, h)
            bar((w - s) / 2.0, 0.0, (w + s) / 2.0, h)
        elif letter == "Ь":
            bar(0.0, 0.0, s, h)
            bar(0.0, h * 0.5, w, h * 0.5 + s)
            bar(0.0, 0.0, w, s)
            bar(w - s, 0.0, w, h * 0.5 + s)
        x += w + gap


def _padlock(mb: tb.MeshBuilder, at: Vector) -> None:
    """Un candado colgado de ``at`` (el punto de la armella)."""
    mb.box((0.05, 0.022, 0.045), (at.x, at.y, at.z - 0.06), STEEL_LIGHT, bevel=0.006)
    arc = [at + Vector((0.016 * math.cos(t), 0.0, -0.035 + 0.03 * math.sin(t))) for t in (math.pi * i / 6.0 for i in range(7))]
    mb.tube(arc, 0.0045, STEEL, segments=6)
    mb.box((0.006, 0.004, 0.012), (at.x, at.y - 0.012, at.z - 0.065), INK)


def _box_walls(mb: tb.MeshBuilder, x_range: tuple, y_range: tuple, z_range: tuple, thick: float, color: str, gaps: dict) -> None:
    """Cuatro muros de caja (para las colisiones): ``gaps`` dice qué huecos lleva cada
    lado ("-y", "+y", "-x", "+x": listas de (u0, u1, z0, z1) a lo largo del lado)."""
    x0, x1 = x_range
    y0, y1 = y_range
    z0, z1 = z_range
    sides = {
        "-y": ((x0, x1), lambda u, t: (u, y0 + t, 0.0)),
        "+y": ((x0, x1), lambda u, t: (u, y1 - t, 0.0)),
        "-x": ((y0, y1), lambda u, t: (x0 + t, u, 0.0)),
        "+x": ((y0, y1), lambda u, t: (x1 - t, u, 0.0)),
    }
    for side, ((u0, u1), point) in sides.items():
        cuts = sorted(gaps.get(side, []))
        pieces = []
        start = u0
        for a, b, c, d in cuts:
            pieces.append((start, a, z0, z1))
            if c > z0:
                pieces.append((a, b, z0, c))
            if d < z1:
                pieces.append((a, b, d, z1))
            start = b
        pieces.append((start, u1, z0, z1))
        for a, b, c, d in pieces:
            if b - a < 0.01 or d - c < 0.01:
                continue
            mid = point((a + b) / 2.0, thick / 2.0)
            size = (b - a, thick, d - c) if side in ("-y", "+y") else (thick, b - a, d - c)
            mb.box(size, (mid[0], mid[1], (c + d) / 2.0), color)


# --------------------------------------------------------------------------
# El quiosco
# --------------------------------------------------------------------------


def _kiosk(mb: tb.MeshBuilder, rng: random.Random, wrecked: bool) -> None:
    hx, hy = QL / 2.0, QD / 2.0
    # La losa, a ras del suelo.
    mb.box((QL + 0.3, QD + 0.3, 0.05), (0.0, 0.0, 0.025), CONCRETE, cuts=2, jitter=0.05)
    # Los postes de las esquinas y los montantes.
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            mb.box((0.08, 0.08, Q_FASCIA), (sx * (hx - 0.04), sy * (hy - 0.04), Q_FASCIA / 2.0), KIOSK_DARK)
    # La chapa de abajo, con sus nervios, en los cuatro lados (detrás, cortada por la puerta).
    spans = {
        "-y": [(-hx, hx)], "+y": [(-hx, Q_DOOR[0]), (Q_DOOR[1], hx)], "-x": [(-hy, hy)], "+x": [(-hy, hy)],
    }
    for side, pieces in spans.items():
        for u0, u1 in pieces:
            _kiosk_panel(mb, side, u0, u1, rng, wrecked)
    # El cristal de arriba, con montantes cada 65 cm.
    for side in ("-y", "+y", "-x", "+x"):
        _kiosk_glazing(mb, side, rng, wrecked)
    # La banda del rótulo, el techo y su vierteaguas.
    for side, (length, offset) in {"-y": (QL, -hy), "+y": (QL, hy), "-x": (QD, -hx), "+x": (QD, hx)}.items():
        color = SIGN_RED if side == "-y" else KIOSK
        if side in ("-y", "+y"):
            mb.box((length + 0.12, 0.08, Q_FASCIA - Q_GLASS), (0.0, offset * 1.01, (Q_GLASS + Q_FASCIA) / 2.0), color, cuts=2, jitter=0.05)
        else:
            mb.box((0.08, length + 0.12, Q_FASCIA - Q_GLASS), (offset * 1.01, 0.0, (Q_GLASS + Q_FASCIA) / 2.0), color, cuts=2, jitter=0.05)
    _letters(mb, "ПЕЧАТЬ", (0.0, -hy * 1.01 - 0.04, (Q_GLASS + Q_FASCIA) / 2.0), 0.3, CREAM)
    sag = 8.0 if wrecked else 0.0
    mb.box((QL + 0.5, QD + 0.5, 0.12), (0.0, 0.0, Q_FASCIA + 0.06), KIOSK_DARK, rotation=(sag * 0.4, -sag, 0.0), cuts=3, jitter=0.04)
    mb.box((QL + 0.56, 0.04, 0.1), (0.0, -hy - 0.27, Q_FASCIA + 0.02), CREAM)
    # La ventanilla de delante, con su repisa.
    mb.box((0.7, 0.2, 0.03), (0.0, -hy - 0.1, Q_PANEL + 0.01), CREAM)
    # Dentro: el mostrador, los estantes, los fajos de periódicos, el tabaco y la estufilla.
    with mb.material(2):
        mb.box((QL - 0.3, 0.5, 0.9), (0.0, -hy + 0.4, 0.45), KIOSK_DARK, cuts=1)
        mb.box((QL - 0.25, 0.56, 0.04), (0.0, -hy + 0.4, 0.92), CREAM)
        for sx in (-1.0, 1.0):
            for z in (0.9, 1.4, 1.9):
                mb.box((0.35, QD - 1.4, 0.03), (sx * (hx - 0.25), 0.35, z), PLANK)
        mb.box((0.4, 0.4, 0.45), (-0.9, 0.6, 0.23), PLANK_DARK)  # la banqueta
        mb.box((0.3, 0.18, 0.4), (1.5, 1.1, 0.2), STEEL)  # la estufilla
    fallen = 0.0 if not wrecked else 1.0
    for k in range(9):
        color = rng.choice(PAPER)
        x = rng.uniform(-1.6, 1.6)
        if wrecked and rng.random() < 0.6:
            mb.box((0.42, 0.3, 0.02), (x, rng.uniform(-0.8, 1.2), 0.06 + 0.02 * k), color, rotation=(0.0, 0.0, rng.uniform(0, 180)))
        else:
            mb.box((0.4, 0.3, rng.uniform(0.08, 0.2)), (x, -hy + 0.4, 0.98 + rng.uniform(0.0, 0.05)), color, rotation=(0.0, 0.0, rng.uniform(-12, 12)), jitter=0.06)
    for sx in (-1.0, 1.0):
        for z in (1.42, 1.92):
            for k in range(5):
                if rng.random() < 0.35 + fallen * 0.3:
                    continue
                mb.box((0.1, 0.18, 0.07), (sx * (hx - 0.25), -0.3 + k * 0.32, z + 0.05), rng.choice(CARTONS), jitter=0.08)


def _kiosk_panel(mb: tb.MeshBuilder, side: str, u0: float, u1: float, rng: random.Random, wrecked: bool) -> None:
    hx, hy = QL / 2.0, QD / 2.0
    length = u1 - u0
    mid = (u0 + u1) / 2.0
    dent = rng.uniform(-6.0, 6.0) if wrecked else 0.0
    if side in ("-y", "+y"):
        y = -hy if side == "-y" else hy
        mb.box((length, 0.04, Q_PANEL), (mid, y, Q_PANEL / 2.0), KIOSK, rotation=(dent, 0.0, 0.0), cuts=2, jitter=0.05)
        for k in range(1, max(2, round(length / 0.5))):
            mb.box((0.03, 0.03, Q_PANEL - 0.1), (u0 + length * k / max(2, round(length / 0.5)), y * 1.012, Q_PANEL / 2.0), KIOSK_DARK)
        mb.box((length, 0.06, 0.05), (mid, y * 1.01, Q_PANEL), CREAM)
    else:
        x = -hx if side == "-x" else hx
        mb.box((0.04, length, Q_PANEL), (x, mid, Q_PANEL / 2.0), KIOSK, rotation=(0.0, dent, 0.0), cuts=2, jitter=0.05)
        for k in range(1, max(2, round(length / 0.5))):
            mb.box((0.03, 0.03, Q_PANEL - 0.1), (x * 1.009, u0 + length * k / max(2, round(length / 0.5)), Q_PANEL / 2.0), KIOSK_DARK)
        mb.box((0.06, length, 0.05), (x * 1.008, mid, Q_PANEL), CREAM)


def _kiosk_glazing(mb: tb.MeshBuilder, side: str, rng: random.Random, wrecked: bool) -> None:
    """Los cristales de un lado entre sus montantes: enteros, rotos (con los picos en el
    marco), sin cristal o tapados con periódicos. Detrás, el hueco de la puerta."""
    hx, hy = QL / 2.0, QD / 2.0
    along = QL if side in ("-y", "+y") else QD
    panes = max(2, round(along / 0.65))
    for k in range(panes):
        u0 = -along / 2.0 + along * k / panes
        u1 = u0 + along / panes
        if side == "+y" and u1 > Q_DOOR[0] and u0 < Q_DOOR[1]:
            continue
        mid = (u0 + u1) / 2.0
        width = u1 - u0

        def at(u: float, inset: float) -> tuple:
            if side == "-y":
                return (u, -hy + inset)
            if side == "+y":
                return (u, hy - inset)
            if side == "-x":
                return (-hx + inset, u)
            return (hx - inset, u)

        # El montante.
        px, py = at(u0, 0.0)
        mb.box((0.04, 0.04, Q_GLASS - Q_PANEL), (px, py, (Q_PANEL + Q_GLASS) / 2.0), KIOSK_DARK)
        state = rng.choice(("vacio", "roto", "roto", "vacio")) if wrecked else rng.choice(("entero", "entero", "roto", "papel", "roto", "entero"))
        cx, cy = at(mid, 0.02)
        horizontal = side in ("-y", "+y")
        if state == "entero":
            with mb.material(1):
                mb.box((width - 0.05, 0.008, Q_GLASS - Q_PANEL - 0.06) if horizontal else (0.008, width - 0.05, Q_GLASS - Q_PANEL - 0.06), (cx, cy, (Q_PANEL + Q_GLASS) / 2.0), GLASS)
        elif state == "papel":
            with mb.material(1):
                mb.box((width - 0.05, 0.008, Q_GLASS - Q_PANEL - 0.06) if horizontal else (0.008, width - 0.05, Q_GLASS - Q_PANEL - 0.06), (cx, cy, (Q_PANEL + Q_GLASS) / 2.0), GLASS)
            sx, sy = at(mid, 0.035)
            for _ in range(2):
                z = rng.uniform(Q_PANEL + 0.3, Q_GLASS - 0.4)
                mb.box((width * 0.6, 0.004, 0.42) if horizontal else (0.004, width * 0.6, 0.42), (sx + (rng.uniform(-0.05, 0.05) if horizontal else 0.0), sy + (0.0 if horizontal else rng.uniform(-0.05, 0.05)), z), rng.choice(PAPER), rotation=(0.0, rng.uniform(-6, 6), 0.0) if horizontal else (rng.uniform(-6, 6), 0.0, 0.0))
        elif state == "roto":
            # Los picos que quedan en el marco, abajo y arriba.
            for z, up in ((Q_PANEL + 0.05, 1.0), (Q_GLASS - 0.05, -1.0)):
                for _ in range(2):
                    u = rng.uniform(u0 + 0.06, u1 - 0.06)
                    tip = rng.uniform(0.08, 0.3)
                    sx, sy = at(u, 0.02)
                    with mb.material(1):
                        mb.box((0.09, 0.006, tip) if horizontal else (0.006, 0.09, tip), (sx, sy, z + up * tip / 2.0), SHARD, rotation=(0.0, rng.uniform(-20, 20), 0.0) if horizontal else (rng.uniform(-20, 20), 0.0, 0.0))


def _kiosk_door(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """La hoja de la puerta del quiosco, en el marco de su bisagra: marco de chapa, el
    panel de abajo, el cristal de arriba (roto) y el pasador con su armella."""
    w, h = Q_DOOR[1] - Q_DOOR[0] - 0.02, Q_DOOR_H - 0.02
    for x in (0.03, w - 0.03):
        mb.box((0.06, 0.04, h), (x, 0.0, h / 2.0), KIOSK_DARK)
    for z in (0.03, Q_PANEL, h - 0.03):
        mb.box((w, 0.04, 0.06), (w / 2.0, 0.0, z), KIOSK_DARK)
    mb.box((w - 0.08, 0.03, Q_PANEL - 0.06), (w / 2.0, 0.0, Q_PANEL / 2.0), KIOSK, cuts=1, jitter=0.05)
    with mb.material(1):
        mb.box((w - 0.1, 0.006, 0.35), (w / 2.0, 0.0, Q_PANEL + 0.2), GLASS)
        mb.box((0.2, 0.006, 0.3), (w * 0.3, 0.0, h - 0.25), SHARD, rotation=(0.0, 18.0, 0.0))
    with mb.material(2):
        mb.box((0.12, 0.03, 0.05), (w - 0.1, -0.035, 1.0), STEEL_LIGHT)
        mb.box((0.03, 0.05, 0.03), (w - 0.1, -0.05, 1.08), STEEL_LIGHT)
    del rng


def _kiosk_collision(mb: tb.MeshBuilder, wrecked: bool) -> None:
    hx, hy = QL / 2.0, QD / 2.0
    door = [(Q_DOOR[0], Q_DOOR[1], 0.0, Q_DOOR_H)]
    if wrecked:
        # Sin cristales: se puede entrar encaramándose por cualquier lado.
        _box_walls(mb, (-hx, hx), (-hy, hy), (0.0, Q_PANEL), 0.06, DARK, {"+y": door})
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                mb.box((0.1, 0.1, Q_FASCIA), (sx * (hx - 0.05), sy * (hy - 0.05), Q_FASCIA / 2.0), DARK)
        _box_walls(mb, (-hx, hx), (-hy, hy), (Q_GLASS, Q_FASCIA), 0.08, DARK, {})
        mb.box((0.8, 0.06, Q_GLASS - Q_DOOR_H), (sum(Q_DOOR) / 2.0, hy - 0.03, (Q_DOOR_H + Q_GLASS) / 2.0), DARK)
    else:
        _box_walls(mb, (-hx, hx), (-hy, hy), (0.0, Q_FASCIA), 0.06, DARK, {"+y": door})
    mb.box((QL + 0.5, QD + 0.5, 0.12), (0.0, 0.0, Q_FASCIA + 0.06), DARK)
    mb.box((QL - 0.3, 0.5, 0.92), (0.0, -hy + 0.4, 0.46), DARK)
    for sx in (-1.0, 1.0):
        for z in (0.9, 1.4, 1.9):
            mb.box((0.35, QD - 1.4, 0.04), (sx * (hx - 0.25), 0.35, z), DARK)


def build_kiosks(lib: kit.KitLibrary) -> None:
    for name, wrecked, seed in (("quiosco", False, 901), ("quiosco_roto", True, 902)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        _kiosk(mb, rng, wrecked)
        piece = mb.finish(name, kit.materials("nevado", "vidrio", "interior"))
        tb.stain(piece, "#2E2A26", amount=0.6 if wrecked else 0.4, scale=0.7, coverage=0.4, seed=seed, stretch_z=0.4)
        lib.add(piece, [], samples=8, ao=0.5, ao_distance=0.5, ground_z=0.0, seed=seed)
        mb = tb.MeshBuilder(seed=seed + 10)
        _kiosk_collision(mb, wrecked)
        lib.add(mb.finish(name + "_colision", kit.materials("colision")), [], samples=1, seed=seed)
    mb = tb.MeshBuilder(seed=903)
    _kiosk_door(mb, random.Random(903))
    lib.add(mb.finish("quiosco_puerta", kit.materials("nevado", "vidrio", "metal")), [], samples=6, seed=903)


# --------------------------------------------------------------------------
# La tienda de la evacuación
# --------------------------------------------------------------------------


def _tent_points(collapsed: bool, rng: random.Random) -> dict:
    """Las lonas de la tienda como rejillas de puntos: los dos faldones, los dos tejados y
    los dos piñones. Caída, la mitad de +x está en el suelo."""
    hx, hy = TL / 2.0, TD / 2.0
    spans = 6
    xs = [-hx + TL * i / (spans * 2) for i in range(spans * 2 + 1)]

    def height_scale(x: float) -> float:
        if not collapsed or x <= 0.6:
            return 1.0
        return max(0.08, 1.0 - (x - 0.6) / (hx - 0.6) * 0.95)

    walls, roofs = [], []
    for sign in (-1.0, 1.0):
        rows = []
        for v in (0.0, 0.5, 1.0):
            row = []
            for i, x in enumerate(xs):
                mid = 0.5 if i % 2 else 0.0
                scale = height_scale(x)
                z = v * T_WALL * scale
                out = sign * (hy + 0.12 * (1.0 - v) - _sag(mid, v, 0.08))
                row.append((x, out, z + rng.uniform(-0.01, 0.01)))
            rows.append(row)
        walls.append((rows, Vector((0.0, sign, 0.0))))
        rows = []
        for v in (0.0, 0.33, 0.66, 1.0):
            row = []
            for i, x in enumerate(xs):
                mid = 0.5 if i % 2 else 0.0
                scale = height_scale(x)
                y = sign * hy * (1.0 - v)
                z = (T_WALL + (T_RIDGE - T_WALL) * v) * scale - _sag(mid, v, 0.1)
                row.append((x, y, z))
            rows.append(row)
        roofs.append((rows, Vector((0.0, sign * 0.4, 1.0))))
    return {"walls": walls, "roofs": roofs, "scale": height_scale}


def _tent(mb: tb.MeshBuilder, rng: random.Random, collapsed: bool, red_cross: bool) -> None:
    hx, hy = TL / 2.0, TD / 2.0
    shape = _tent_points(collapsed, rng)
    for rows, outward in shape["walls"] + shape["roofs"]:
        _cloth(mb, rows, outward, CANVAS, CANVAS_DARK)
    scale = shape["scale"]
    # Los piñones: el de -x con la puerta enrollada; el de +x, entero (o en el suelo).
    for end in (-1.0, 1.0):
        x = end * hx
        s = scale(x)
        ridge = T_RIDGE * s
        wall = T_WALL * s
        if end < 0:
            pieces = [
                [(x, -hy, 0.0), (x, -T_DOOR, 0.0), (x, -T_DOOR, 1.95), (x, -hy, wall)],
                [(x, T_DOOR, 0.0), (x, hy, 0.0), (x, hy, wall), (x, T_DOOR, 1.95)],
                [(x, -hy, wall), (x, -T_DOOR, 1.95), (x, 0.0, ridge)],
                [(x, T_DOOR, 1.95), (x, hy, wall), (x, 0.0, ridge)],
                [(x, -T_DOOR, 1.95), (x, T_DOOR, 1.95), (x, 0.0, ridge)],
            ]
        else:
            pieces = [
                [(x, hy, 0.0), (x, -hy, 0.0), (x, -hy, wall), (x, hy, wall)],
                [(x, hy, wall), (x, -hy, wall), (x, 0.0, ridge)],
            ]
        for corners in pieces:
            _panel(mb, corners, Vector((end, 0.0, 0.0)), CANVAS, CANVAS_DARK)
    # La puerta enrollada sobre el hueco y atada.
    mb.cylinder(0.11, T_DOOR * 2.0 + 0.1, (-hx - 0.06, 0.0, 2.0), CANVAS_DARK, rotation=(90.0, 0.0, 0.0), segments=8, jitter=0.05)
    if red_cross:
        _crosses(mb, scale)
    # Los postes, la cumbrera, los vientos y las estacas.
    for x in (-hx + 0.05, -1.5, 1.5, hx - 0.05):
        s = scale(x)
        if s < 0.9:
            mb.box((0.08, 0.08, 2.6), (x, rng.uniform(-1.2, 1.2), 0.06), POLE, rotation=(90.0, 0.0, rng.uniform(-30, 30)))
            continue
        mb.box((0.08, 0.08, T_RIDGE - 0.05), (x, 0.0, (T_RIDGE - 0.05) / 2.0), POLE, jitter=0.06)
    mb.box((TL * (0.55 if collapsed else 1.0), 0.06, 0.06), (-hx * 0.45 if collapsed else 0.0, 0.0, T_RIDGE - 0.08), POLE)
    for k in range(7):
        x = -hx + TL * k / 6.0
        s = scale(x)
        for sign in (-1.0, 1.0):
            top = Vector((x, sign * (hy + 0.05), T_WALL * s))
            stake = Vector((x, sign * (hy + 1.3), 0.0))
            mb.bar(top, stake, 0.008, ROPE, segments=4)
            mb.box((0.04, 0.04, 0.25), (stake.x, stake.y, 0.08), POLE, rotation=(sign * 15.0, 0.0, 0.0))
    # La chimenea de la estufa, por el tejado.
    if not collapsed:
        mb.cylinder(0.07, 1.6, (-2.4, 1.6, 2.1), STEEL, segments=8)
        mb.cylinder(0.13, 0.12, (-2.4, 1.6, 2.95), STEEL, radius_top=0.05, segments=8)
    _tent_inside(mb, rng, collapsed)


def _crosses(mb: tb.MeshBuilder, scale) -> None:
    """La cruz roja sobre un cuadro blanco, en los dos tejados y en el piñón de +x."""
    hy = TD / 2.0
    for sign in (-1.0, 1.0):
        v = 0.5
        z = T_WALL + (T_RIDGE - T_WALL) * v + 0.02
        y = sign * hy * (1.0 - v)
        tilt = math.degrees(math.atan2(T_RIDGE - T_WALL, hy)) * -sign
        mb.box((1.6, 1.6, 0.01), (0.0, y, z), CANVAS_WHITE, rotation=(tilt, 0.0, 0.0))
        for size in ((1.2, 0.36, 0.012), (0.36, 1.2, 0.012)):
            mb.box(size, (0.0, y, z + 0.006), CROSS, rotation=(tilt, 0.0, 0.0))
    del scale


def _tent_inside(mb: tb.MeshBuilder, rng: random.Random, collapsed: bool) -> None:
    """Catres en dos filas, mantas, maletas y fardos, la mesa con su quinqué y la estufa."""
    hx, hy = TL / 2.0, TD / 2.0
    with mb.material(2):
        for sign in (-1.0, 1.0):
            for k in range(4):
                x = -hx + 1.6 + k * 1.9
                if collapsed and x > 1.0:
                    continue
                y = sign * (hy - 1.15)
                for dx in (-0.85, 0.85):
                    for dy in (-0.32, 0.32):
                        mb.bar((x + dx, y + dy, 0.0), (x + dx * 0.9, y + dy * 0.9, 0.42), 0.015, STEEL)
                mb.box((1.9, 0.7, 0.05), (x, y, 0.43), CANVAS_DARK)
                if rng.random() < 0.75:
                    mb.box((1.5, 0.65, 0.12), (x + rng.uniform(-0.15, 0.15), y, 0.52), rng.choice(BLANKETS), rotation=(0.0, 0.0, rng.uniform(-6, 6)), bevel=0.04, segments=2, jitter=0.08)
                if rng.random() < 0.5:
                    size = (rng.uniform(0.45, 0.7), rng.uniform(0.3, 0.4), rng.uniform(0.18, 0.28))
                    mb.box(size, (x + rng.uniform(-0.6, 0.6), y - sign * 0.6, size[2] / 2.0), rng.choice(CASES), rotation=(0.0, 0.0, rng.uniform(0, 180)), bevel=0.02, jitter=0.08)
        # La mesa y la estufa (la burzhuika).
        mb.box((1.2, 0.7, 0.04), (-1.2, 0.0, 0.74), PLANK)
        for dx in (-0.55, 0.55):
            for dy in (-0.3, 0.3):
                mb.box((0.04, 0.04, 0.72), (-1.2 + dx, dy, 0.36), PLANK_DARK)
        mb.cylinder(0.05, 0.22, (-1.0, 0.1, 0.87), STEEL_LIGHT, segments=8)
        if not collapsed:
            mb.box((0.5, 0.4, 0.45), (-2.4, 1.6, 0.25), STEEL, bevel=0.02)
            mb.cylinder(0.07, 1.15, (-2.4, 1.6, 0.98), STEEL, segments=8)


def _tent_collision(mb: tb.MeshBuilder, collapsed: bool) -> None:
    hx, hy = TL / 2.0, TD / 2.0
    door = [(-T_DOOR, T_DOOR, 0.0, 1.95)]
    if not collapsed:
        _box_walls(mb, (-hx, hx), (-hy, hy), (0.0, T_WALL), 0.08, DARK, {"-x": door})
        for sign in (-1.0, 1.0):
            run = math.hypot(hy, T_RIDGE - T_WALL)
            tilt = math.degrees(math.atan2(T_RIDGE - T_WALL, hy)) * -sign
            mb.box((TL, run, 0.08), (0.0, sign * hy / 2.0, (T_WALL + T_RIDGE) / 2.0), DARK, rotation=(tilt, 0.0, 0.0))
        for end in (-1.0, 1.0):
            mb.box((0.08, TD * 0.6, T_RIDGE - T_WALL), (end * hx, 0.0, (T_WALL + T_RIDGE) / 2.0), DARK)
        for x in (-1.5, 1.5):
            mb.box((0.1, 0.1, T_RIDGE), (x, 0.0, T_RIDGE / 2.0), DARK)
    else:
        _box_walls(mb, (-hx, 0.6), (-hy, hy), (0.0, T_WALL), 0.08, DARK, {"-x": door})
        for sign in (-1.0, 1.0):
            run = math.hypot(hy, T_RIDGE - T_WALL)
            tilt = math.degrees(math.atan2(T_RIDGE - T_WALL, hy)) * -sign
            mb.box(((hx + 0.6), run, 0.08), ((-hx + 0.6) / 2.0, sign * hy / 2.0, (T_WALL + T_RIDGE) / 2.0), DARK, rotation=(tilt, 0.0, 0.0))
        # La mitad caída: una cuña de lona del borde al suelo.
        drop = math.degrees(math.atan2(T_RIDGE, hx - 0.6))
        mb.box((math.hypot(hx - 0.6, T_RIDGE), TD, 0.1), ((hx + 0.6) / 2.0, 0.0, T_RIDGE / 2.0), DARK, rotation=(0.0, drop, 0.0))
        mb.box((0.1, 0.1, T_RIDGE), (-1.5, 0.0, T_RIDGE / 2.0), DARK)
    for sign in (-1.0, 1.0):
        for k in range(4):
            x = -hx + 1.6 + k * 1.9
            if collapsed and x > 1.0:
                continue
            mb.box((1.9, 0.7, 0.5), (x, sign * (hy - 1.15), 0.25), DARK)
    mb.box((1.2, 0.7, 0.76), (-1.2, 0.0, 0.38), DARK)


def build_tents(lib: kit.KitLibrary) -> None:
    for name, collapsed, cross, seed in (("tienda", False, False, 911), ("tienda_caida", True, False, 912), ("tienda_cruz", False, True, 913)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        _tent(mb, rng, collapsed, cross)
        piece = mb.finish(name, kit.materials("nevado", "interior", "interior"))
        tb.stain(piece, "#2E2A22", amount=0.45, scale=1.1, coverage=0.4, seed=seed, stretch_z=0.6)
        lib.add(piece, [], samples=8, ao=0.55, ao_distance=0.8, ground_z=0.0, seed=seed)
        if name != "tienda_cruz":
            mb = tb.MeshBuilder(seed=seed + 10)
            _tent_collision(mb, collapsed)
            lib.add(mb.finish(name + "_colision", kit.materials("colision")), [], samples=1, seed=seed)


# --------------------------------------------------------------------------
# El trastero
# --------------------------------------------------------------------------


def _roof_z(y: float) -> float:
    """La cubierta a un agua del trastero: alta delante (-y), baja detrás."""
    return S_FRONT + (S_BACK - S_FRONT) * (y + SD / 2.0) / SD


def _boards(mb: tb.MeshBuilder, x_range: tuple, y: float, z0: float, top, rng: random.Random, skip: tuple | None = None, gone: float = 0.0) -> None:
    """Tablas de pie a lo largo de x en ``y`` (``top(x)``: hasta dónde llegan). ``skip``
    es un hueco (x0, x1) sin tablas; ``gone``, la parte de tablas que faltan."""
    x = x_range[0]
    while x < x_range[1] - 0.02:
        width = min(rng.uniform(0.14, 0.2), x_range[1] - x)
        mid = x + width / 2.0
        if (skip is None or not (skip[0] < mid < skip[1])) and rng.random() >= gone:
            height = top(mid) - z0
            mb.box((width - 0.012, 0.025, height), (mid, y, z0 + height / 2.0), rng.choice(PLANKS), jitter=0.08)
        x += width


def _side_boards(mb: tb.MeshBuilder, x: float, rng: random.Random) -> None:
    y = -SD / 2.0
    while y < SD / 2.0 - 0.02:
        width = min(rng.uniform(0.14, 0.2), SD / 2.0 - y)
        mid = y + width / 2.0
        height = _roof_z(mid) - 0.15
        mb.box((0.025, width - 0.012, height), (x, mid, 0.15 + height / 2.0), rng.choice(PLANKS), jitter=0.08)
        y += width


def _shed(mb: tb.MeshBuilder, rng: random.Random, caved: bool) -> None:
    hx, hy = SW / 2.0, SD / 2.0
    # El zócalo de ladrillo.
    mb.box((SW, SD, 0.15), (0.0, 0.0, 0.075), BRICK, cuts=2, jitter=0.06)
    door = (-S_DOOR, S_DOOR)
    _boards(mb, (-hx, hx), -hy, 0.15, lambda x: S_FRONT if abs(x) > S_DOOR else 0.15 + S_DOOR_H + 0.4, rng, skip=door, gone=0.25 if caved else 0.0)
    # Sobre la puerta, un dintel de tabla y tablas hasta la cubierta.
    mb.box((S_DOOR * 2.0 + 0.1, 0.04, 0.12), (0.0, -hy - 0.02, 0.15 + S_DOOR_H + 0.06), PLANK_DARK)
    _boards(mb, (-S_DOOR, S_DOOR), -hy, 0.15 + S_DOOR_H + 0.12, lambda x: S_FRONT, rng)
    _boards(mb, (-hx, hx), hy, 0.15, lambda x: S_BACK, rng)
    for x in (-hx + 0.015, hx - 0.015):
        _side_boards(mb, x, rng)
    # Postes de las esquinas y la cubierta de tela asfáltica con sus listones.
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            z = _roof_z(sy * hy)
            mb.box((0.1, 0.1, z), (sx * (hx - 0.05), sy * (hy - 0.05), z / 2.0), PLANK_DARK)
    tilt = math.degrees(math.atan2(S_FRONT - S_BACK, SD))
    if caved:
        mb.box((SW + 0.2, SD * 0.55, 0.05), (0.0, -hy * 0.45, 1.3), TAR, rotation=(-28.0, 4.0, 0.0), cuts=2, jitter=0.06)
        mb.box((SW + 0.2, SD * 0.45, 0.05), (0.0, hy * 0.5, (S_BACK + 0.4) / 2.0 + 0.4), TAR, rotation=(18.0, -3.0, 0.0), cuts=2, jitter=0.06)
    else:
        mb.box((SW + 0.24, SD + 0.6, 0.05), (0.0, 0.0, (S_FRONT + S_BACK) / 2.0 + 0.05), TAR, rotation=(-tilt, 0.0, 0.0), cuts=3, jitter=0.05)
        for k in range(5):
            x = -hx + SW * (k + 0.5) / 5.0
            mb.box((0.04, SD + 0.6, 0.03), (x, 0.0, (S_FRONT + S_BACK) / 2.0 + 0.09), PLANK_DARK, rotation=(-tilt, 0.0, 0.0))
    # Dentro: estantes al fondo con tarros, leña, un saco y una rueda de bicicleta.
    with mb.material(2):
        for z in (0.7, 1.25, 1.8):
            mb.box((SW - 0.3, 0.35, 0.03), (0.0, hy - 0.25, z), PLANK)
            for k in range(6):
                if rng.random() < 0.4:
                    continue
                x = -hx + 0.35 + k * 0.45
                with mb.material(3):
                    mb.cylinder(0.06, 0.18, (x, hy - 0.25, z + 0.1), JAR, segments=8, jitter=0.1)
                mb.cylinder(0.062, 0.02, (x, hy - 0.25, z + 0.2), RUST, segments=8)
        for k in range(14):
            y = rng.uniform(-1.0, 1.6)
            z = 0.2 + (k % 4) * 0.13
            mb.cylinder(0.06, 0.45, (hx - 0.4, y, z), PLANK, rotation=(90.0, 0.0, rng.uniform(-8, 8)), segments=6, jitter=0.1)
        mb.box((0.45, 0.35, 0.5), (-hx + 0.4, 0.6, 0.4), "#6E6656", bevel=0.1, segments=2)
        ring = [(-hx + 0.08, -1.0 + 0.32 * math.cos(t), 1.2 + 0.32 * math.sin(t)) for t in (math.pi * i / 8.0 for i in range(17))]
        mb.tube(ring, 0.014, INK, segments=4)


def _shed_door(mb: tb.MeshBuilder, rng: random.Random) -> None:
    """La puerta de tablas del trastero, en el marco de su bisagra: tablas de pie, la Z
    de travesaños, las bisagras de chapa y la armella del candado."""
    w, h = S_DOOR * 2.0 - 0.02, S_DOOR_H - 0.03
    x = 0.0
    while x < w - 0.02:
        width = min(rng.uniform(0.14, 0.19), w - x)
        mb.box((width - 0.01, 0.025, h), (x + width / 2.0, 0.0, h / 2.0), rng.choice(PLANKS), jitter=0.08)
        x += width
    for z in (0.25, h - 0.25):
        mb.box((w, 0.03, 0.1), (w / 2.0, 0.026, z), PLANK_DARK)
    diagonal = math.degrees(math.atan2(h - 0.5, w))
    mb.box((math.hypot(w, h - 0.5), 0.03, 0.09), (w / 2.0, 0.026, h / 2.0), PLANK_DARK, rotation=(0.0, -diagonal, 0.0))
    with mb.material(2):
        for z in (0.25, h - 0.25):
            mb.box((0.35, 0.008, 0.04), (0.17, -0.016, z), RUST)
        mb.box((0.14, 0.006, 0.035), (w - 0.07, -0.016, 1.1), RUST)
        mb.box((0.03, 0.04, 0.03), (w - 0.13, -0.035, 1.12), STEEL)


def _shed_collision(mb: tb.MeshBuilder, caved: bool) -> None:
    hx, hy = SW / 2.0, SD / 2.0
    door = [(-S_DOOR, S_DOOR, 0.0, 0.15 + S_DOOR_H)]
    _box_walls(mb, (-hx, hx), (-hy, hy), (0.0, S_BACK), 0.06, DARK, {"-y": door})
    mb.box((SW, 0.06, S_FRONT - S_BACK), (0.0, -hy + 0.03, (S_FRONT + S_BACK) / 2.0), DARK)
    tilt = math.degrees(math.atan2(S_FRONT - S_BACK, SD))
    if caved:
        mb.box((SW, SD * 0.55, 0.08), (0.0, -hy * 0.45, 1.3), DARK, rotation=(-28.0, 0.0, 0.0))
    else:
        mb.box((SW + 0.2, SD + 0.5, 0.08), (0.0, 0.0, (S_FRONT + S_BACK) / 2.0 + 0.05), DARK, rotation=(-tilt, 0.0, 0.0))
    # Los estantes: las tablas (el botín se apoya en ellas) y sus costados.
    for z in (0.7, 1.25, 1.8):
        mb.box((SW - 0.3, 0.35, 0.04), (0.0, hy - 0.25, z), DARK)
    for x in (-hx + 0.17, hx - 0.17):
        mb.box((0.04, 0.35, 1.85), (x, hy - 0.25, 0.93), DARK)


def build_sheds(lib: kit.KitLibrary) -> None:
    for name, caved, seed in (("trastero", False, 921), ("trastero_hundido", True, 922)):
        rng = random.Random(seed)
        mb = tb.MeshBuilder(seed=seed)
        _shed(mb, rng, caved)
        piece = mb.finish(name, kit.materials("nevado", "vidrio", "interior", "vidrio"))
        tb.stain(piece, "#2E2A26", amount=0.5, scale=0.8, coverage=0.45, seed=seed, stretch_z=0.4)
        lib.add(piece, [], samples=8, ao=0.55, ao_distance=0.6, ground_z=0.0, seed=seed)
        mb = tb.MeshBuilder(seed=seed + 10)
        _shed_collision(mb, caved)
        lib.add(mb.finish(name + "_colision", kit.materials("colision")), [], samples=1, seed=seed)
    mb = tb.MeshBuilder(seed=923)
    _shed_door(mb, random.Random(923))
    lib.add(mb.finish("trastero_puerta", kit.materials("nevado", "vidrio", "metal")), [], samples=6, seed=923)


# --------------------------------------------------------------------------
# El palomar
# --------------------------------------------------------------------------


def _dovecote(mb: tb.MeshBuilder, rng: random.Random) -> None:
    h = P_LOFT
    # Los cuatro postes con sus tornapuntas.
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            mb.box((0.15, 0.15, P_FLOOR), (sx * P_POST, sy * P_POST, P_FLOOR / 2.0), PLANK_DARK, jitter=0.05)
            mb.box((0.08, 0.08, 1.3), (sx * (P_POST - 0.35), sy * P_POST, P_FLOOR - 0.45), PLANK_DARK, rotation=(0.0, sx * 40.0, 0.0))
    # El suelo del altillo, la plataforma de delante (+x) y su barandilla.
    mb.box((2 * h + 0.2, 2 * h + 0.2, 0.1), (0.0, 0.0, P_FLOOR - 0.05), PLANK, cuts=2, jitter=0.06)
    mb.box((1.0, 1.4, 0.08), (h + 0.5, 0.0, P_FLOOR - 0.04), PLANK, cuts=1, jitter=0.06)
    for y in (-0.7, 0.7):
        mb.box((0.06, 0.06, P_FLOOR + 0.9), (h + 0.97, y, (P_FLOOR + 0.9) / 2.0), PLANK_DARK)
        mb.box((1.0, 0.04, 0.05), (h + 0.5, y, P_FLOOR + 0.88), PLANK_DARK)
        mb.box((1.0, 0.03, 0.04), (h + 0.5, y, P_FLOOR + 0.45), PLANK_DARK)
    # Las paredes del altillo (tablas), con la puerta en +x y las trampillas de las palomas.
    for side in ("-x", "+x", "-y", "+y"):
        _loft_wall(mb, side, rng)
    # La cubierta a dos aguas, de chapa.
    ridge = P_FLOOR + P_WALL + 0.9
    for sign in (-1.0, 1.0):
        run = math.hypot(h + 0.3, 0.9)
        tilt = math.degrees(math.atan2(0.9, h + 0.3)) * -sign
        mb.box((2 * h + 0.6, run, 0.04), (0.0, sign * (h + 0.3) / 2.0, P_FLOOR + P_WALL + 0.45), "#5A6058", rotation=(tilt, 0.0, 0.0), cuts=2, jitter=0.05)
    for end in (-1.0, 1.0):
        triangle = kit.ccw([(-h, P_FLOOR + P_WALL), (h, P_FLOOR + P_WALL), (0.0, ridge - 0.05)])
        mb.prism(triangle, 0.04, (end * h, 0.0, 0.0), PLANK, rotation=(90.0, 0.0, 90.0), jitter=0.05)
    # La jaula de malla, por -y.
    with mb.material(2):
        for x in (-h, 0.0, h):
            for y in (-h, -h - 1.0):
                mb.box((0.04, 0.04, 1.5), (x, y, P_FLOOR + 0.75), STEEL)
        for z in (P_FLOOR, P_FLOOR + 1.5):
            mb.box((2 * h, 0.04, 0.04), (0.0, -h - 1.0, z), STEEL)
            for x in (-h, h):
                mb.box((0.04, 1.0, 0.04), (x, -h - 0.5, z), STEEL)
        for k in range(13):
            x = -h + 2 * h * k / 12.0
            mb.box((0.006, 0.006, 1.5), (x, -h - 1.0, P_FLOOR + 0.75), STEEL_LIGHT)
        mb.box((2 * h, 1.0, 0.04), (0.0, -h - 0.5, P_FLOOR + 1.52), "#5A6058")
    # La escalera de mano, de la nieve al borde de la plataforma.
    x = h + 1.02
    for y in (-0.24, 0.24):
        mb.box((0.06, 0.05, P_FLOOR + 0.8), (x, y, (P_FLOOR + 0.8) / 2.0), PLANK_DARK, jitter=0.05)
    z = 0.3
    while z < P_FLOOR - 0.05:
        mb.box((0.04, 0.5, 0.04), (x, 0.0, z), PLANK, jitter=0.08)
        z += 0.3
    # Dentro: las perchas, los comederos y los prismáticos del palomero en su clavo.
    with mb.material(2):
        for k in range(4):
            mb.box((2 * h - 0.3, 0.04, 0.04), (0.0, h - 0.2, P_FLOOR + 0.5 + k * 0.35), PLANK_DARK)
        mb.box((0.8, 0.18, 0.1), (-0.4, -h + 0.25, P_FLOOR + 0.05), PLANK)


def _loft_wall(mb: tb.MeshBuilder, side: str, rng: random.Random) -> None:
    h = P_LOFT
    z0, z1 = P_FLOOR, P_FLOOR + P_WALL
    u = -h
    while u < h - 0.02:
        width = min(rng.uniform(0.14, 0.2), h - u)
        mid = u + width / 2.0
        if side == "+x" and abs(mid) < P_DOOR:
            u += width
            continue
        if side == "-y" and 0.4 < (mid + h) % 0.9 < 0.6 and rng.random() < 0.7:
            # Una trampilla de las palomas, con su tabla para posarse.
            mb.box((width, 0.025, 0.5), (mid, -h, z1 - 0.25), rng.choice(PLANKS), jitter=0.08)
            mb.box((width, 0.025, 0.9), (mid, -h, z0 + 0.45), rng.choice(PLANKS), jitter=0.08)
            mb.box((0.2, 0.2, 0.02), (mid, -h - 0.1, z0 + 0.92), PLANK)
        else:
            color = rng.choice(PLANKS)
            if side in ("-y", "+y"):
                mb.box((width - 0.01, 0.025, z1 - z0), (mid, h if side == "+y" else -h, (z0 + z1) / 2.0), color, jitter=0.08)
            else:
                mb.box((0.025, width - 0.01, z1 - z0), (h if side == "+x" else -h, mid, (z0 + z1) / 2.0), color, jitter=0.08)
        u += width
    if side == "+x":
        mb.box((0.04, P_DOOR * 2.0 + 0.1, z1 - z0 - 1.65), (h, 0.0, z0 + 1.65 + (z1 - z0 - 1.65) / 2.0), PLANK_DARK)


def _loft_door(mb: tb.MeshBuilder, rng: random.Random) -> None:
    w, h = P_DOOR * 2.0 - 0.02, 1.62
    x = 0.0
    while x < w - 0.02:
        width = min(rng.uniform(0.13, 0.18), w - x)
        mb.box((width - 0.01, 0.025, h), (x + width / 2.0, 0.0, h / 2.0), rng.choice(PLANKS), jitter=0.08)
        x += width
    for z in (0.2, h - 0.2):
        mb.box((w, 0.03, 0.09), (w / 2.0, 0.026, z), PLANK_DARK)
    with mb.material(2):
        mb.box((0.12, 0.006, 0.03), (w - 0.06, -0.016, 0.9), RUST)


def _dovecote_collision(mb: tb.MeshBuilder) -> None:
    h = P_LOFT
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            mb.box((0.16, 0.16, P_FLOOR), (sx * P_POST, sy * P_POST, P_FLOOR / 2.0), DARK)
    mb.box((2 * h + 0.2, 2 * h + 0.2, 0.12), (0.0, 0.0, P_FLOOR - 0.06), DARK)
    mb.box((1.0, 1.4, 0.1), (h + 0.5, 0.0, P_FLOOR - 0.05), DARK)
    for y in (-0.72, 0.72):
        mb.box((1.0, 0.06, 0.9), (h + 0.5, y, P_FLOOR + 0.45), DARK)
    door = [(-P_DOOR, P_DOOR, P_FLOOR, P_FLOOR + 1.65)]
    _box_walls(mb, (-h, h), (-h, h), (P_FLOOR, P_FLOOR + P_WALL), 0.05, DARK, {"+x": door})
    mb.box((2 * h + 0.4, 2 * h + 0.4, 0.1), (0.0, 0.0, P_FLOOR + P_WALL + 0.3), DARK)
    mb.box((2 * h, 1.0, 1.5), (0.0, -h - 0.5, P_FLOOR + 0.75), DARK)


def build_dovecote(lib: kit.KitLibrary) -> None:
    rng = random.Random(931)
    mb = tb.MeshBuilder(seed=931)
    _dovecote(mb, rng)
    piece = mb.finish("palomar", kit.materials("nevado", "vidrio", "interior"))
    tb.stain(piece, "#2E2A26", amount=0.5, scale=0.7, coverage=0.45, seed=931, stretch_z=0.4)
    lib.add(piece, [], samples=8, ao=0.5, ao_distance=0.6, ground_z=0.0, seed=931)
    mb = tb.MeshBuilder(seed=932)
    _dovecote_collision(mb)
    lib.add(mb.finish("palomar_colision", kit.materials("colision")), [], samples=1, seed=932)
    mb = tb.MeshBuilder(seed=933)
    _loft_door(mb, random.Random(933))
    lib.add(mb.finish("palomar_puerta", kit.materials("nevado", "vidrio", "metal")), [], samples=6, seed=933)


# --------------------------------------------------------------------------
# El transformador
# --------------------------------------------------------------------------


def _transformer(mb: tb.MeshBuilder, rng: random.Random) -> None:
    hx, hy = XL / 2.0, XD / 2.0
    door = [(-X_DOOR, X_DOOR, 0.0, X_DOOR_H)]
    vents = {"-x": [(-1.2, -0.2, 2.6, 3.3), (0.2, 1.2, 2.6, 3.3)], "+x": [(-0.5, 0.5, 2.6, 3.3)], "+y": [(-2.0, -1.0, 2.6, 3.3), (1.0, 2.0, 2.6, 3.3)]}
    gaps = {"-y": door, **vents}
    with mb.material(3):
        _box_walls(mb, (-hx, hx), (-hy, hy), (0.0, X_TOP), X_WALL, BRICK, gaps)
    # El zuncho de hormigón, la cubierta y su albardilla.
    mb.box((XL + 0.06, XD + 0.06, 0.3), (0.0, 0.0, X_TOP + 0.15), CONCRETE, cuts=3, jitter=0.04)
    mb.box((XL + 0.3, XD + 0.3, 0.08), (0.0, 0.0, X_TOP + 0.34), TAR, cuts=3)
    mb.box((1.6, 0.1, 0.2), (0.0, -hy - 0.05, X_DOOR_H + 0.1), CONCRETE)
    # Las rejillas de lamas en sus huecos.
    with mb.material(4):
        for side, holes in vents.items():
            for u0, u1, z0, z1 in holes:
                for k in range(6):
                    z = z0 + (z1 - z0) * (k + 0.5) / 6.0
                    if side == "+y":
                        mb.box((u1 - u0, 0.04, 0.09), ((u0 + u1) / 2.0, hy - 0.05, z), STEEL, rotation=(35.0, 0.0, 0.0))
                    else:
                        x = -hx + 0.05 if side == "-x" else hx - 0.05
                        mb.box((0.04, u1 - u0, 0.09), (x, (u0 + u1) / 2.0, z), STEEL, rotation=(0.0, 35.0 if side == "-x" else -35.0, 0.0))
        # Los aisladores y los cables del lado de +x.
        for k in range(3):
            y = -0.8 + k * 0.8
            mb.box((0.5, 0.08, 0.08), (hx + 0.25, y, 3.45), STEEL)
            for j in range(3):
                mb.cylinder(0.07 - 0.012 * j, 0.06, (hx + 0.45, y, 3.52 + j * 0.06), PORCELAIN, segments=8)
            mb.bar((hx + 0.45, y, 3.72), (hx + 0.02, y, 3.0), 0.012, INK, segments=4)
    # Dentro (a oscuras): los dos transformadores con sus aletas y el armario abierto.
    with mb.material(2):
        for x in (-2.0, 1.2):
            mb.box((1.6, 1.1, 1.5), (x, 0.6, 0.75), "#3E4446", bevel=0.03)
            for k in range(7):
                mb.box((0.03, 1.3, 1.2), (x - 0.7 + k * 0.23, 0.6, 0.75), STEEL)
            for k in range(3):
                mb.cylinder(0.06, 0.4, (x - 0.5 + k * 0.5, 0.6, 1.7), PORCELAIN, segments=8)
        mb.box((1.4, 0.45, 2.0), (2.9, -2.4, 1.0), "#4A5052", bevel=0.02)
        mb.box((0.04, 0.5, 1.8), (2.2, -2.75, 1.0), "#4A5052", rotation=(0.0, 0.0, 60.0))
        for k in range(4):
            mb.box((0.9, 0.3, 0.02), (-1.0 + k * 0.6, -1.2, 0.01), INK)
    # El cartel del rayo en la puerta va en la hoja; aquí, el del muro.
    _danger_sign(mb, Vector((1.4, -hy - 0.02, 1.7)), 4)
    del rng


def _danger_sign(mb: tb.MeshBuilder, center: Vector, slot: int) -> None:
    """El triángulo amarillo con el rayo negro (cuidado: alta tensión)."""
    with mb.material(slot):
        triangle = kit.ccw([(-0.22, -0.16), (0.22, -0.16), (0.0, 0.22)])
        mb.prism(triangle, 0.01, (center.x, center.y, center.z), YELLOW, rotation=(90.0, 0.0, 0.0))
        bolt = [(-0.03, 0.12), (0.04, 0.02), (-0.01, 0.02), (0.04, -0.12), (-0.05, -0.01), (0.0, -0.01)]
        for a, b in zip(bolt, bolt[1:]):
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            mb.box((length + 0.015, 0.012, 0.022), (center.x + mid[0], center.y - 0.008, center.z + mid[1]), INK, rotation=(0.0, -angle, 0.0))


def _transformer_door(mb: tb.MeshBuilder) -> None:
    w, h = X_DOOR * 2.0 - 0.02, X_DOOR_H - 0.02
    mb.box((w, 0.05, h), (w / 2.0, 0.0, h / 2.0), "#4A5052", cuts=2, jitter=0.05)
    for z in (0.3, h / 2.0, h - 0.3):
        mb.box((w - 0.1, 0.02, 0.06), (w / 2.0, -0.032, z), STEEL)
    with mb.material(2):
        mb.box((0.04, 0.05, 0.25), (w - 0.12, -0.05, 1.05), STEEL_LIGHT)
        mb.box((0.14, 0.006, 0.035), (w - 0.07, -0.03, 1.15), RUST)
        _danger_sign(mb, Vector((w / 2.0, -0.04, 1.6)), 2)


def _transformer_collision(mb: tb.MeshBuilder) -> None:
    hx, hy = XL / 2.0, XD / 2.0
    _box_walls(mb, (-hx, hx), (-hy, hy), (0.0, X_TOP + 0.3), X_WALL, DARK, {"-y": [(-X_DOOR, X_DOOR, 0.0, X_DOOR_H)]})
    mb.box((XL + 0.3, XD + 0.3, 0.38), (0.0, 0.0, X_TOP + 0.19), DARK)
    for x in (-2.0, 1.2):
        mb.box((1.7, 1.3, 1.6), (x, 0.6, 0.8), DARK)
    mb.box((1.4, 0.45, 2.0), (2.9, -2.4, 1.0), DARK)


def build_transformer(lib: kit.KitLibrary) -> None:
    rng = random.Random(941)
    mb = tb.MeshBuilder(seed=941)
    _transformer(mb, rng)
    piece = mb.finish("transformador", kit.materials("nevado", "vidrio", "interior", "ladrillo", "metal"))
    tb.stain(piece, "#2A2522", amount=0.5, scale=0.8, coverage=0.4, seed=941, stretch_z=0.4)
    lib.add(piece, [], samples=8, ao=0.5, ao_distance=0.6, ground_z=0.0, seed=941)
    mb = tb.MeshBuilder(seed=942)
    _transformer_collision(mb)
    lib.add(mb.finish("transformador_colision", kit.materials("colision")), [], samples=1, seed=942)
    mb = tb.MeshBuilder(seed=943)
    _transformer_door(mb)
    lib.add(mb.finish("transformador_puerta", kit.materials("nevado", "vidrio", "metal")), [], samples=6, seed=943)


# --------------------------------------------------------------------------
# El candado, la cadena y los huesos
# --------------------------------------------------------------------------


def build_small(lib: kit.KitLibrary) -> None:
    mb = tb.MeshBuilder(seed=951)
    _padlock(mb, Vector((0.0, 0.0, 0.0)))
    lib.add(mb.finish("candado", kit.materials("metal")), [], samples=4, seed=951)
    # La cadena: eslabones colgando de la hoja al marco, con su candado abajo.
    mb = tb.MeshBuilder(seed=952)
    count = 9
    for k in range(count):
        t = k / (count - 1)
        x = -0.12 + 0.24 * t
        z = -0.18 * math.sin(math.pi * t)
        turn = 90.0 if k % 2 else 0.0
        link = [Vector((0.022 * math.cos(a), 0.0, 0.012 * math.sin(a))) for a in (2.0 * math.pi * i / 10.0 for i in range(11))]
        rot = Matrix.Rotation(math.radians(turn), 3, "X")
        points = [(rot @ p) + Vector((x, 0.0, z)) for p in link]
        mb.tube(points, 0.004, STEEL_LIGHT if k % 3 else STEEL, segments=4)
    _padlock(mb, Vector((0.0, -0.01, -0.19)))
    lib.add(mb.finish("cadena", kit.materials("metal")), [], samples=4, seed=952)
    # Huesos roídos: un fémur, costillas y una vértebra, en la nieve.
    rng = random.Random(953)
    mb = tb.MeshBuilder(seed=953)
    mb.bar((-0.2, 0.0, 0.025), (0.2, 0.05, 0.03), 0.018, BONE, segments=6)
    for end in ((-0.2, 0.0), (0.2, 0.05)):
        mb.sphere(0.03, (end[0], end[1], 0.03), BONE, segments=8)
    for k in range(5):
        a = rng.uniform(0.0, math.tau)
        start = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.25, 0.25), 0.012))
        arc = [start + Vector((math.cos(a) * 0.04 * i, math.sin(a) * 0.04 * i, 0.03 * math.sin(math.pi * i / 6.0))) for i in range(7)]
        mb.tube(arc, 0.007, BONE, segments=4)
    mb.cylinder(0.03, 0.04, (0.1, -0.2, 0.02), BONE, segments=8)
    lib.add(mb.finish("huesos", kit.materials("nevado")), [], samples=4, seed=953)


def build_kit() -> object:
    lib = kit.KitLibrary("kit_menores", columns=4, spacing=14.0)
    build_kiosks(lib)
    build_tents(lib)
    build_sheds(lib)
    build_dovecote(lib)
    build_transformer(lib)
    build_small(lib)
    return lib.root


def models() -> dict:
    return {"kit_menores": build_kit}
