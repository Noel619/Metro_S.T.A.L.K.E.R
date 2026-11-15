"""Geometría del plano de Tumansk: marcos de referencia y figuras básicas.

Todas las medidas van en metros. El origen está en la esquina suroeste del mapa
jugable: x crece hacia el este y y hacia el norte.

La ciudad tiene un eje monumental (la avenida del Progreso) girado 48° respecto
al este. Une la estación de tren, la plaza del Trabajo, el puente, la Escalinata,
la plaza Central y la Casa de los Sóviets. Muchas piezas se colocan en el marco
de ese eje: `s` avanza por el eje hacia el noreste (0 = centro de la plaza del
Trabajo) y `t` se aparta de él (positivo hacia el noroeste).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ANCHO = 1600.0
ALTO = 1200.0
SECTOR = 200.0

EJE_ANGULO = 48.0
EJE_ORIGEN = (430.0, 330.0)
_C = math.cos(math.radians(EJE_ANGULO))
_S = math.sin(math.radians(EJE_ANGULO))

Punto = tuple[float, float]


def eje(s: float, t: float = 0.0) -> Punto:
    """Del marco del eje (s a lo largo, t de través) al mapa."""
    return (EJE_ORIGEN[0] + _C * s - _S * t, EJE_ORIGEN[1] + _S * s + _C * t)


def a_eje(x: float, y: float) -> Punto:
    """Del mapa al marco del eje."""
    dx = x - EJE_ORIGEN[0]
    dy = y - EJE_ORIGEN[1]
    return (dx * _C + dy * _S, -dx * _S + dy * _C)


def rect(cx: float, cy: float, largo: float, fondo: float, angulo: float = 0.0) -> Polygon:
    """Rectángulo centrado; el lado largo sigue `angulo` (grados desde el este)."""
    a = math.radians(angulo)
    ux, uy = math.cos(a) * largo / 2.0, math.sin(a) * largo / 2.0
    vx, vy = -math.sin(a) * fondo / 2.0, math.cos(a) * fondo / 2.0
    return Polygon(
        [
            (cx - ux - vx, cy - uy - vy),
            (cx + ux - vx, cy + uy - vy),
            (cx + ux + vx, cy + uy + vy),
            (cx - ux + vx, cy - uy + vy),
        ]
    )


def caja(x0: float, y0: float, x1: float, y1: float) -> Polygon:
    """Rectángulo alineado con el mapa, dado por dos esquinas."""
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def rect_eje(s0: float, s1: float, t0: float, t1: float) -> Polygon:
    """Rectángulo alineado con el eje monumental."""
    return Polygon([eje(s0, t0), eje(s1, t0), eje(s1, t1), eje(s0, t1)])


def poligono(puntos: Iterable[Punto]) -> Polygon:
    return Polygon(list(puntos))


def circulo(cx: float, cy: float, r: float, lados: int = 40) -> Polygon:
    return Point(cx, cy).buffer(r, quad_segs=max(4, lados // 4))


def elipse(cx: float, cy: float, rx: float, ry: float, angulo: float = 0.0) -> Polygon:
    figura = affinity.scale(Point(0, 0).buffer(1.0, quad_segs=16), rx, ry)
    figura = affinity.rotate(figura, angulo, origin=(0, 0))
    return affinity.translate(figura, cx, cy)


def sector_anular(
    cx: float, cy: float, r0: float, r1: float, a0: float, a1: float, pasos: int = 24
) -> Polygon:
    """Trozo de anillo entre los radios r0 y r1 y los rumbos a0 y a1 (grados)."""
    exterior = []
    for i in range(pasos + 1):
        a = math.radians(a0 + (a1 - a0) * i / pasos)
        exterior.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    for i in range(pasos, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / pasos)
        exterior.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a)))
    return Polygon(exterior)


def forma_h(
    cx: float, cy: float, largo: float, fondo: float, ala: float, ala_fondo: float, angulo: float
) -> Polygon:
    """Planta en H: un cuerpo central y dos alas perpendiculares en los extremos."""
    cuerpo = rect(0, 0, largo, fondo)
    ala_a = rect(-largo / 2 + ala_fondo / 2, 0, ala_fondo, ala)
    ala_b = rect(largo / 2 - ala_fondo / 2, 0, ala_fondo, ala)
    figura = unary_union([cuerpo, ala_a, ala_b])
    figura = affinity.rotate(figura, angulo, origin=(0, 0))
    return affinity.translate(figura, cx, cy)


def forma_l(
    x0: float, y0: float, largo_x: float, largo_y: float, fondo: float, giro: int = 0
) -> Polygon:
    """Planta en L con la esquina en (x0, y0); `giro` (0-3) la rota de 90 en 90°."""
    brazo_x = caja(0, 0, largo_x, fondo)
    brazo_y = caja(0, 0, fondo, largo_y)
    figura = affinity.rotate(unary_union([brazo_x, brazo_y]), 90 * giro, origin=(0, 0))
    return affinity.translate(figura, x0, y0)


def linea(puntos: Sequence[Punto]) -> LineString:
    return LineString(list(puntos))


def banda(puntos: Sequence[Punto], ancho: float, puntas: str = "flat") -> Polygon:
    """Franja de `ancho` alrededor de una polilínea (calles, vías, tuberías)."""
    estilo = {"flat": 2, "square": 3, "round": 1}[puntas]
    return LineString(list(puntos)).buffer(ancho / 2.0, cap_style=estilo, join_style=2)


def interpolar(puntos: Sequence[Punto], fraccion: float) -> Punto:
    p = LineString(list(puntos)).interpolate(fraccion, normalized=True)
    return (p.x, p.y)


def coords(geom) -> list:
    """Coordenadas redondeadas a 0,1 m para exportar a JSON."""
    if geom.geom_type == "Polygon":
        anillos = [[(round(x, 1), round(y, 1)) for x, y in geom.exterior.coords]]
        for hueco in geom.interiors:
            anillos.append([(round(x, 1), round(y, 1)) for x, y in hueco.coords])
        return anillos
    if geom.geom_type == "MultiPolygon":
        return [coords(p) for p in geom.geoms]
    if geom.geom_type == "LineString":
        return [(round(x, 1), round(y, 1)) for x, y in geom.coords]
    if geom.geom_type == "Point":
        return [round(geom.x, 1), round(geom.y, 1)]
    raise ValueError(f"Geometría sin exportar: {geom.geom_type}")


def sector_de(x: float, y: float) -> str:
    """Nombre del sector de 200 m (columnas A-H de oeste a este, filas 1-6 de sur a norte)."""
    columna = "ABCDEFGH"[min(7, max(0, int(x // SECTOR)))]
    fila = min(6, max(1, int(y // SECTOR) + 1))
    return f"{columna}{fila}"


def rumbo(origen: Punto, destino: Punto) -> float:
    """Rumbo de origen a destino en grados desde el este, en sentido antihorario."""
    return math.degrees(math.atan2(destino[1] - origen[1], destino[0] - origen[0])) % 360.0


def distancia(a: Punto, b: Punto) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])
