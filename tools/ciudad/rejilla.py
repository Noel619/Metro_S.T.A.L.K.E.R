"""Lo que la red de tránsito cubre de la rejilla del relieve detallado de la maqueta.

La maqueta dibuja el terreno con una rejilla de 2 m: cada celda son dos triángulos, el del
noroeste (k = 0) y el del sureste (k = 1), partidos por la diagonal del suroeste al
noreste. Para cada triángulo, este módulo decide qué hace la maqueta con él:

- NINGUNO: sin tránsito; se dibuja el terreno.
- ENTERO: el tránsito lo cubre entero; el terreno no se dibuja.
- BORDE: el borde del tránsito lo cruza, pero lo que se pisa va por encima del terreno (una
  acera a 3 cm): se dibuja el terreno entero y la acera encima.
- HONDO: el borde lo cruza y lo que se pisa va por debajo del terreno (una calzada, un
  camino hundido, los peldaños excavados): el terreno no se dibuja y lo que queda sin
  tránsito se dibuja aparte (el relleno, exacto, que exporta este módulo).

Además: cuánto se rebaja la colisión del relieve en cada punto de la rejilla (bajo el
tránsito, para quedar por debajo de lo que se pisa; bajo un socavón, por debajo de su
fondo), qué triángulos visibles comparten un
punto rebajado (su colisión va aparte: ANILLO) y qué triángulos de cada grupo de tránsito
caen sobre una rasante plana (se dibujan enteros, sin cortar por la rejilla).

Todo con las alturas tal como las lee la maqueta (redondeadas al centímetro).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

from geo import ALTO, ANCHO

PASO = 2.0
NINGUNO, ENTERO, BORDE, HONDO = 0, 1, 2, 3
ANILLO = 4
# Lo mínimo que se rebaja la colisión bajo el tránsito; en el borde del tránsito solo se
# rebaja lo más hondo (el resto del punto es terreno que se ve).
REBAJE = 0.30
REBAJE_HONDO = 0.45
# Lo que puede separarse la rasante del plano de un triángulo para dibujarlo entero.
TOLERANCIA_PLANO = 0.003
# Clases que van por debajo de la rasante (cerca de ellas el terreno asomaría).
CLASES_HONDAS = ("calzada", "adoquin", "paso_nivel", "via_tranvia", "camino", "alcorque", "peldano")
# Resolución del rasterizado con el que se clasifican los triángulos que el borde no cruza.
PIXELES_POR_METRO = 2


@dataclass
class Rejilla:
    estados: np.ndarray  # (filas, columnas, 2): estado de cada triángulo, con ANILLO en el bit 2
    rebaje: np.ndarray  # (filas + 1, columnas + 1)
    rellenos: list  # [(id del triángulo, [(x, y) × 3]), ...]
    planos: list  # por grupo: cadena de '1' (plano) y '0', un carácter por triángulo
    rectas: list  # por grupo: cadena de '0'-'7': las aristas que van rectas (bits 0-2)


def cuantizar(h: np.ndarray) -> np.ndarray:
    """Las alturas como las lee la maqueta del PNG de 16 bits (centímetros)."""
    return np.clip(np.round((h + 50.0) * 100.0), 0, 65535) / 100.0 - 50.0


def vertices(valores: np.ndarray) -> np.ndarray:
    """Las alturas en los puntos de la rejilla (las esquinas de las celdas): la media de
    las cuatro celdas que rodean cada punto, como CityPlan.vertex_grid."""
    p = np.pad(valores, 1, mode="edge")
    return (p[:-1, :-1] + p[:-1, 1:] + p[1:, :-1] + p[1:, 1:]) / 4.0


def lineal(vert: np.ndarray, x, y) -> np.ndarray:
    """La altura lineal dentro de cada triángulo de la rejilla (como la malla)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    filas, columnas = vert.shape[0] - 1, vert.shape[1] - 1
    i = np.clip(np.floor(x / PASO).astype(int), 0, columnas - 1)
    j = np.clip(np.floor(y / PASO).astype(int), 0, filas - 1)
    u = x / PASO - i
    v = y / PASO - j
    so = vert[j, i]
    ne = vert[j + 1, i + 1]
    no = vert[j + 1, i]
    se = vert[j, i + 1]
    arriba = v >= u
    return np.where(arriba, so * (1 - v) + ne * u + no * (v - u), so * (1 - u) + ne * v + se * (u - v))


def _triangulo(i: int, j: int, k: int) -> Polygon:
    x, y = i * PASO, j * PASO
    if k == 0:
        return Polygon([(x, y), (x + PASO, y + PASO), (x, y + PASO)])
    return Polygon([(x, y), (x + PASO, y), (x + PASO, y + PASO)])


def _cruces(a: float, b: float) -> list[float]:
    if abs(b - a) < 1e-12:
        return []
    bajo, alto = min(a, b), max(a, b)
    return [(n * PASO - a) / (b - a) for n in range(math.floor(bajo / PASO) + 1, math.ceil(alto / PASO))]


def _marcar_borde(estados: np.ndarray, union) -> None:
    """Los triángulos que cruza el borde del tránsito: los de los puntos medios de cada
    tramo del borde partido por la rejilla (y los de al lado si el tramo va justo encima de
    una línea)."""
    filas, columnas = estados.shape[:2]
    medios = []
    for anillo in _anillos(union):
        pts = np.asarray(anillo.coords)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            ts = sorted({0.0, 1.0, *_cruces(x0, x1), *_cruces(y0, y1), *_cruces(x0 - y0, x1 - y1)})
            for t0, t1 in zip(ts, ts[1:]):
                if t1 - t0 < 1e-9:
                    continue
                t = (t0 + t1) / 2.0
                mx, my = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                dx, dy = x1 - x0, y1 - y0
                largo = math.hypot(dx, dy)
                nx, ny = -dy / largo * 1e-3, dx / largo * 1e-3
                medios += [(mx, my), (mx + nx, my + ny), (mx - nx, my - ny)]
    m = np.array(medios)
    i = np.floor(m[:, 0] / PASO).astype(int)
    j = np.floor(m[:, 1] / PASO).astype(int)
    k = np.where(m[:, 1] / PASO - j >= m[:, 0] / PASO - i, 0, 1)
    dentro = (i >= 0) & (j >= 0) & (i < columnas) & (j < filas)
    estados[j[dentro], i[dentro], k[dentro]] = BORDE


def _anillos(geom) -> list:
    resultado = []
    for p in getattr(geom, "geoms", [geom]):
        if p.is_empty:
            continue
        resultado.append(p.exterior)
        resultado += list(p.interiors)
    return resultado


def _rasterizar(union, filas: int, columnas: int) -> np.ndarray:
    """El tránsito rasterizado (para los triángulos que el borde no cruza basta con saber
    de qué lado cae su centro, que está a más de medio metro del borde)."""
    from PIL import Image, ImageDraw

    escala = PIXELES_POR_METRO
    ancho, alto = int(columnas * PASO * escala), int(filas * PASO * escala)
    img = Image.new("L", (ancho, alto), 0)
    d = ImageDraw.Draw(img)
    for p in getattr(union, "geoms", [union]):
        d.polygon([(x * escala, (ALTO - y) * escala) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors:
            d.polygon([(x * escala, (ALTO - y) * escala) for x, y in h.coords], fill=0)
    return np.flipud(np.array(img)) > 0


def calcular(t, alturas, grupos_exportados: list) -> Rejilla:
    """La rejilla frente al tránsito. `grupos_exportados` son los grupos tal como van a
    transito.json: (grupo, vértices, triángulos)."""
    import transito as T

    filas, columnas = int(ALTO / PASO), int(ANCHO / PASO)
    rasante = vertices(cuantizar(alturas.rasante))
    relieve = vertices(cuantizar(alturas.relieve))
    desnudo = vertices(alturas.desnudo)
    en_tierra = [g for g in t.grupos if not g.elevado]
    union = unary_union([g.forma for g in en_tierra]).intersection(shapely.box(0, 0, ANCHO, ALTO))
    estados = np.zeros((filas, columnas, 2), np.uint8)
    _marcar_borde(estados, union)
    # Los que el borde no cruza: dentro o fuera según su centro.
    mascara = _rasterizar(union, filas, columnas)
    j, i = np.mgrid[0:filas, 0:columnas]
    for k, (cu, cv) in enumerate(((2.0 / 3.0, 4.0 / 3.0), (4.0 / 3.0, 2.0 / 3.0))):
        px = ((i * PASO + cu) * PIXELES_POR_METRO).astype(int)
        py = ((j * PASO + cv) * PIXELES_POR_METRO).astype(int)
        dentro = mascara[py, px]
        sin_borde = estados[:, :, k] != BORDE
        estados[:, :, k] = np.where(sin_borde & dentro, ENTERO, estados[:, :, k])
    # Los del borde, hondos si tocan algo que va por debajo de la rasante o si el terreno
    # natural queda por encima de la rasante (la plaza de la cabeza, excavada).
    hondos = unary_union([g.forma for g in en_tierra
                          if g.clase in CLASES_HONDAS or g.regla["tipo"] != "terreno"])
    shapely.prepare(hondos)
    bj, bi, bk = np.nonzero(estados == BORDE)
    triangulos = np.array([_triangulo(i0, j0, k0) for i0, j0, k0 in zip(bi, bj, bk)], dtype=object)
    tocan = shapely.intersects(triangulos, hondos)
    so = desnudo[bj, bi] - rasante[bj, bi]
    ne = desnudo[bj + 1, bi + 1] - rasante[bj + 1, bi + 1]
    tercero = np.where(bk == 0, desnudo[bj + 1, bi] - rasante[bj + 1, bi], desnudo[bj, bi + 1] - rasante[bj, bi + 1])
    asoma = np.maximum(so, np.maximum(ne, tercero)) > T.NIVEL_PEATON - 0.01
    hondo = tocan | asoma
    estados[bj[hondo], bi[hondo], bk[hondo]] = HONDO
    # El relleno de los hondos: lo que no es tránsito, triangulado.
    rellenos = []
    huecos = shapely.difference(triangulos[hondo], union)
    for (i0, j0, k0), forma in zip(zip(bi[hondo], bj[hondo], bk[hondo]), huecos):
        ident = (int(j0) * columnas + int(i0)) * 2 + int(k0)
        for p in T.poligonos(forma):
            if p.area < 1e-5:
                continue
            for tri in shapely.constrained_delaunay_triangles(p).geoms:
                if tri.area < 1e-7:
                    continue
                esquinas = list(shapely.geometry.polygon.orient(tri, 1.0).exterior.coords)[:3]
                rellenos.append((ident, [(round(x, 3), round(y, 3)) for x, y in esquinas]))
    rebaje = _rebaje(estados, rasante, en_tierra, alturas)
    _rebaje_socavones(rebaje, relieve, en_tierra)
    _marcar_anillo(estados, rebaje)
    planos = [_planos(g, vert, tris, rasante) for g, vert, tris in grupos_exportados]
    rectas = _rectas(grupos_exportados, planos)
    return Rejilla(estados, rebaje, rellenos, planos, rectas)


def _rectas(grupos_exportados: list, planos: list) -> list:
    """En cada triángulo que se corta por la rejilla, las aristas que comparte con uno que
    se dibuja entero: esas van rectas (la altura, lineal entre sus extremos), para que las
    dos superficies casen exactas en la junta."""
    lados = {}
    for n, (g, vert, tris) in enumerate(grupos_exportados):
        for k in range(len(tris) // 3):
            for e in range(3):
                a, b = vert[tris[3 * k + e]], vert[tris[3 * k + (e + 1) % 3]]
                lados.setdefault((min(a, b), max(a, b)), []).append((n, k))
    resultado = []
    for n, (g, vert, tris) in enumerate(grupos_exportados):
        cadena = []
        for k in range(len(tris) // 3):
            mascara = 0
            if planos[n][k] == "0":
                for e in range(3):
                    a, b = vert[tris[3 * k + e]], vert[tris[3 * k + (e + 1) % 3]]
                    for m, j in lados[(min(a, b), max(a, b))]:
                        # La malla de un socavón no casa con nada: su borde va más bajo.
                        if (m, j) != (n, k) and planos[m][j] == "1" and grupos_exportados[m][0].malla is None:
                            mascara |= 1 << e
            cadena.append(str(mascara))
        resultado.append("".join(cadena))
    return resultado


def _rebaje(estados: np.ndarray, rasante: np.ndarray, en_tierra: list, alturas) -> np.ndarray:
    """Cuánto baja la colisión del relieve en cada punto de la rejilla: al menos REBAJE en
    los puntos cuyos seis triángulos son de tránsito (no se ven); más bajo los peldaños y
    los rellanos excavados, también en el borde."""
    filas, columnas = estados.shape[:2]
    oculto = (estados == ENTERO) | (estados == HONDO)
    # Cuántos de los seis triángulos de cada punto están ocultos.
    cuenta = np.zeros((filas + 1, columnas + 1), int)
    o0 = oculto[:, :, 0].astype(int)
    o1 = oculto[:, :, 1].astype(int)
    cuenta[:-1, :-1] += o0 + o1  # el punto es la esquina suroeste de la celda
    cuenta[1:, 1:] += o0 + o1  # noreste
    cuenta[1:, :-1] += o0  # noroeste (solo el triángulo del noroeste)
    cuenta[:-1, 1:] += o1  # sureste (solo el del sureste)
    rebaje = np.where(cuenta >= 6, REBAJE, 0.0)
    # Lo más bajo de los peldaños y rellanos junto a cada punto.
    minimo = np.full(rasante.shape, np.inf)
    for g in en_tierra:
        if g.regla["tipo"] != "plano":
            continue
        z = g.regla["z"] + 0.0
        x0, y0, x1, y1 = g.forma.bounds
        i0, i1 = max(0, int(x0 // PASO) - 1), min(columnas, int(x1 // PASO) + 2)
        j0, j1 = max(0, int(y0 // PASO) - 1), min(filas, int(y1 // PASO) + 2)
        cerca = g.forma.buffer(PASO * 1.5)
        jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
        dentro = shapely.contains_xy(cerca, ii * PASO, jj * PASO)
        bloque = minimo[j0:j1 + 1, i0:i1 + 1]
        bloque[dentro] = np.minimum(bloque[dentro], z)
    hondo = REBAJE + np.maximum(0.0, rasante - minimo - 0.12)
    hondo = np.where(np.isfinite(minimo), hondo, 0.0)
    rebaje = np.where(cuenta >= 6, np.maximum(rebaje, hondo), rebaje)
    rebaje = np.where((cuenta > 0) & (hondo > REBAJE_HONDO), np.maximum(rebaje, hondo), rebaje)
    return rebaje


def _rebaje_socavones(rebaje: np.ndarray, relieve: np.ndarray, en_tierra: list) -> None:
    """Bajo la malla de un socavón (y hasta celda y media alrededor), la colisión del
    relieve baja hasta 30 cm por debajo de lo más hondo de la malla que tiene cerca."""
    filas, columnas = rebaje.shape[0] - 1, rebaje.shape[1] - 1
    for g in en_tierra:
        if g.malla is None:
            continue
        x0, y0, x1, y1 = g.forma.bounds
        i0, i1 = max(0, int(x0 // PASO) - 2), min(columnas, int(x1 // PASO) + 3)
        j0, j1 = max(0, int(y0 // PASO) - 2), min(filas, int(y1 // PASO) + 3)
        jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
        px, py = (ii * PASO).ravel(), (jj * PASO).ravel()
        cerca = shapely.contains_xy(g.forma.buffer(PASO * 1.5), px, py)
        if not cerca.any():
            continue
        puntos, alturas = g.malla.puntos, g.malla.z
        d = np.hypot(px[cerca, None] - puntos[None, :, 0], py[cerca, None] - puntos[None, :, 1])
        minimo = np.where(d < PASO * 1.5, alturas[None, :], np.inf).min(axis=1)
        bloque = rebaje[j0:j1 + 1, i0:i1 + 1].ravel()
        alto = relieve[j0:j1 + 1, i0:i1 + 1].ravel()[cerca]
        bajo = np.where(np.isfinite(minimo), alto - (minimo - 0.3), 0.0)
        bloque[cerca] = np.maximum(bloque[cerca], bajo)
        rebaje[j0:j1 + 1, i0:i1 + 1] = bloque.reshape(jj.shape)


def _marcar_anillo(estados: np.ndarray, rebaje: np.ndarray) -> None:
    """Los triángulos que se ven (sin tránsito o con el terreno debajo) y tienen una esquina
    rebajada: su colisión va aparte, a la altura de verdad."""
    rebajado = rebaje > 0.0
    so = rebajado[:-1, :-1]
    ne = rebajado[1:, 1:]
    no = rebajado[1:, :-1]
    se = rebajado[:-1, 1:]
    for k, tercero in ((0, no), (1, se)):
        visible = (estados[:, :, k] == NINGUNO) | (estados[:, :, k] == BORDE)
        anillo = visible & (so | ne | tercero)
        estados[:, :, k] = np.where(anillo, estados[:, :, k] | ANILLO, estados[:, :, k])


def _planos(grupo, vert: list, tris: list, rasante: np.ndarray) -> str:
    """Para cada triángulo del grupo, si la rasante es plana debajo ('1': se dibuja entero)
    o no ('0': se corta por la rejilla). Lo que no sigue la rasante, siempre entero."""
    n = len(tris) // 3
    if grupo.regla["tipo"] != "terreno" or grupo.elevado:
        return "1" * n
    filas, columnas = rasante.shape[0] - 1, rasante.shape[1] - 1
    resultado = []
    for k in range(n):
        a, b, c = (vert[tris[3 * k + m]] for m in range(3))
        xs = np.array([a[0], b[0], c[0]])
        ys = np.array([a[1], b[1], c[1]])
        if xs.min() < 0 or ys.min() < 0 or xs.max() > ANCHO or ys.max() > ALTO:
            resultado.append("0")
            continue
        zs = lineal(rasante, xs, ys)
        p0 = np.array([xs[0], ys[0], zs[0]])
        normal = np.cross(np.array([xs[1], ys[1], zs[1]]) - p0, np.array([xs[2], ys[2], zs[2]]) - p0)
        if abs(normal[2]) < 1e-9:
            resultado.append("0")
            continue
        # Las esquinas de las celdas que toca el triángulo (con un margen de una celda).
        i0 = max(0, int(xs.min() // PASO))
        i1 = min(columnas, int(xs.max() // PASO) + 1)
        j0 = max(0, int(ys.min() // PASO))
        j1 = min(filas, int(ys.max() // PASO) + 1)
        jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
        px, py = ii * PASO, jj * PASO
        tri = Polygon([a, b, c]).buffer(PASO * 1.5)
        cerca = shapely.contains_xy(tri, px, py)
        plano = p0[2] - (normal[0] * (px - p0[0]) + normal[1] * (py - p0[1])) / normal[2]
        error = np.abs(plano - rasante[j0:j1 + 1, i0:i1 + 1])[cerca]
        resultado.append("1" if error.size == 0 or error.max() <= TOLERANCIA_PLANO else "0")
    return "".join(resultado)


def exportar_png(rejilla: Rejilla, carpeta) -> dict:
    """rejilla.png (8 bits: el estado del noroeste en los bits 0-2 y el del sureste en los
    3-5) y rebaje.png (16 bits: milímetros), con la primera fila al norte."""
    from PIL import Image

    e = rejilla.estados
    codigo = (e[:, :, 0] | (e[:, :, 1] << 3)).astype(np.uint8)
    Image.fromarray(np.flipud(codigo)).save(carpeta / "rejilla.png", optimize=True)
    mm = np.clip(np.round(rejilla.rebaje * 1000.0), 0, 65535).astype(np.uint16)
    Image.fromarray(np.flipud(mm)).save(carpeta / "rebaje.png")
    return {
        "rejilla": {"archivo": "rejilla.png", "paso": PASO,
                    "codificacion": "estado del triángulo noroeste en los bits 0-2 y del sureste en los 3-5",
                    "estados": {"ninguno": NINGUNO, "entero": ENTERO, "borde": BORDE, "hondo": HONDO,
                                "anillo": ANILLO},
                    "filas": "la primera fila es el borde norte"},
        "rebaje": {"archivo": "rebaje.png", "codificacion": "milímetros", "filas": "la primera fila es el borde norte"},
    }
