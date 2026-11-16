"""El ferrocarril y el tranvía de Tumansk: la rasante de cada vía, la plataforma y los
andenes de la estación, los pasos a nivel y lo que se exporta para que la maqueta levante
el balasto, las traviesas y los carriles.

Las vías no suben ni bajan como el terreno: la línea principal no pasa del 1,2 % y los
apartaderos del 2,5 %. La rasante de cada vía sale del terreno natural y de la coronación
que el plano pide en cada tramo en terraplén (datos.TERRAPLENES: su altura sobre la cota 0
de la vega), con el río salvado por el puente en línea recta entre sus estribos, y se
recorta donde subiría o bajaría demasiado deprisa: los terraplenes acaban en rampa y, al
norte del río, la línea entra en trinchera en la loma.
El relieve se nivela a esa rasante en una franja a lo largo de cada vía, con su talud,
como las calles de la falda de la loma: los terraplenes y las trincheras son del propio
relieve. Las vías que se cruzan con una calle van a ras de ella (paso a nivel): la calle
sube hasta el carril.

Medidas soviéticas: ancho de vía de 1520 mm, traviesas de hormigón de 2,75 m cada 0,55 m,
carril de 15 cm y andenes altos (1,10 m sobre el carril, con el borde a 1,92 m del eje).
"""

from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

import datos as D
import relieve as R
from geo import ALTO, ANCHO, banda

PASO = 2.0
# Del plano de formación (lo que se nivela) a lo alto del carril: balasto, traviesa y carril.
CARRIL = 0.57
# Andenes altos: sobre el carril y con el borde a esta distancia del eje de la vía.
ANDEN_ALTO = 1.10
ANDEN_BORDE = 1.92
# Rampas de los extremos de los andenes.
PENDIENTE_ANDEN = 0.12
# Cómo se traza cada clase de vía: media anchura de la franja nivelada, talud y pendiente.
TRAZADO = {
    "principal": {"media": 6.0, "talud": 10.0, "pendiente": 0.012},
    "secundaria": {"media": 3.0, "talud": 6.0, "pendiente": 0.025},
    "playa": {"media": 2.5, "talud": 5.0, "pendiente": 0.012},
}
# La plataforma de la estación: a la altura de la vía principal, para sus tres vías y los
# dos andenes isla (de x = 50 a x = 390, de y = 19 a y = 47).
PLATAFORMA = {"puntos": [(50.0, 33.0), (390.0, 33.0)], "media": 14.0, "talud": 6.0}
# Tramo de los andenes (a lo largo de la estación).
ANDENES_X = (120.0, 330.0)
# El cráter se llevó el final de la línea: las vías acaban en su borde.
RADIO_CRATER = R.CRATER_RADIO + 15.0
# Media anchura de la franja de cada paso a nivel (a cada lado del eje de la vía) y largo
# de la rampa de la calle hasta él.
PASO_NIVEL = 3.5
RAMPA_PASO = 10.0
# El terraplén de la calle junto al paso: talud (horizontal por vertical) y media anchura de
# la caja de la vía, que no se toca (el balasto; su pie queda enterrado junto al paso).
TALUD_PASO = 2.0
CAJA_VIA = 2.0
# El tranvía va por la calle: vía doble, con los ejes a 1,6 m del de la línea. Sus curvas
# tienen 20 m de radio (menos donde no caben) y los tramos de menos de 8 m del trazado se
# funden en una sola esquina.
TRANVIA_ENTREVIA = 1.6
RADIO_TRANVIA = 20.0
TRAMO_MINIMO_TRANVIA = 8.0


def _muestras(puntos) -> tuple[LineString, np.ndarray, np.ndarray, np.ndarray]:
    linea = LineString(puntos)
    n = max(2, int(math.ceil(linea.length / PASO)))
    s = np.linspace(0.0, linea.length, n + 1)
    xy = np.array([(p.x, p.y) for p in (linea.interpolate(v) for v in s)])
    return linea, s, xy[:, 0], xy[:, 1]


def _muestrear(h: np.ndarray, res: float, xs, ys) -> np.ndarray:
    from transito import muestrear

    return muestrear(h, res, np.clip(xs, 0.0, ANCHO), np.clip(ys, 0.0, ALTO))


def _recortar(z: np.ndarray, s: np.ndarray, pendiente: float) -> np.ndarray:
    """La rasante más alta que no pasa de `z` y no sube ni baja más de `pendiente`: lo que
    sube o baja demasiado deprisa se recorta (las rampas de los terraplenes)."""
    z = z.copy()
    for i in range(1, len(z)):
        z[i] = min(z[i], z[i - 1] + pendiente * (s[i] - s[i - 1]))
    for i in range(len(z) - 2, -1, -1):
        z[i] = min(z[i], z[i + 1] + pendiente * (s[i + 1] - s[i]))
    return z


def _rellenar(z: np.ndarray, s: np.ndarray, pendiente: float, fijos: dict) -> np.ndarray:
    """Sube la rasante alrededor de los puntos fijos (donde la vía sale de otra) para que
    llegue a ellos con la pendiente permitida (un terraplén en rampa)."""
    z = z.copy()
    for i, valor in fijos.items():
        z = np.maximum(z, valor - pendiente * np.abs(s - s[i]))
    return z


def _diseno(linea: LineString, s: np.ndarray, xs: np.ndarray, ys: np.ndarray, natural: np.ndarray,
            res: float) -> np.ndarray:
    """La altura que pide el plano: en los tramos en terraplén, su coronación (la altura del
    terraplén sobre la cota 0 de la vega, o el terreno si va más alto); en el resto, el
    terreno natural. Sobre el río, el puente: una recta entre sus estribos."""
    z = _muestrear(natural, res, xs, ys)
    corona = np.full_like(z, -np.inf)
    for t in D.TERRAPLENES:
        cerca = R.distancia_polilinea(xs, ys, t["puntos"]) < t["corona"] / 2.0
        corona = np.where(cerca, np.maximum(corona, t["alto"]), corona)
    z = np.maximum(z, corona)
    a, b = (linea.project(Point(p)) for p in D.PUENTE_FERROCARRIL["puntos"])
    if linea.distance(Point(D.PUENTE_FERROCARRIL["puntos"][0])) < 5.0:
        s0, s1 = min(a, b) - 10.0, max(a, b) + 10.0
        dentro = (s > s0) & (s < s1)
        if dentro.any():
            z0 = float(np.interp(s0, s, z))
            z1 = float(np.interp(s1, s, z))
            z[dentro] = z0 + (z1 - z0) * (s[dentro] - s0) / (s1 - s0)
    return z


def _fuera_del_crater(puntos) -> list:
    """La vía hasta el borde del cráter (lo que quedaba dentro, lo arrancó la bomba)."""
    linea = LineString(puntos).difference(Point(R.CRATER).buffer(RADIO_CRATER, 64))
    partes = [g for g in getattr(linea, "geoms", [linea]) if g.length > 0]
    if not partes:
        return list(puntos)
    return list(max(partes, key=lambda g: g.length).coords)


def perfiles(natural: np.ndarray, res: float) -> dict:
    """La rasante de cada vía (la principal primero; las que salen de otra, sujetas a ella
    en el empalme) y la de la plataforma de la estación."""
    resultado = {}
    orden = sorted(D.VIAS, key=lambda v: 0 if v["id"] == "principal" else (1 if v["tipo"] == "playa" else 2))
    for via in orden:
        puntos = _fuera_del_crater(via["puntos"])
        trazado = TRAZADO[via["tipo"]]
        linea, s, xs, ys = _muestras(puntos)
        z = _diseno(linea, s, xs, ys, natural, res)
        if via["id"].startswith("anden") and "principal" in resultado:
            # Las vías de andén van a la altura de la principal, en paralelo.
            z = _a_la_altura_de(resultado["principal"], xs, ys)
        else:
            fijos = {}
            for i in (0, len(s) - 1):
                empalme = _empalme(resultado, xs[i], ys[i])
                if empalme is not None:
                    fijos[i] = empalme
            z = _rellenar(z, s, trazado["pendiente"], fijos)
            z = _recortar(z, s, trazado["pendiente"])
            for i, valor in fijos.items():
                z[i] = valor
        resultado[via["id"]] = {"s": s / linea.length, "z": z, "puntos": puntos, "media": trazado["media"],
                                "talud": trazado["talud"], "largo": linea.length,
                                "sin_nivelar": _tramo_del_puente(linea)}
    x0, x1 = PLATAFORMA["puntos"][0][0], PLATAFORMA["puntos"][1][0]
    xs = np.linspace(x0, x1, 41)
    ys = np.full_like(xs, PLATAFORMA["puntos"][0][1])
    z = _a_la_altura_de(resultado["principal"], xs, ys)
    resultado["plataforma"] = {"s": np.linspace(0.0, 1.0, 41), "z": z, "puntos": PLATAFORMA["puntos"],
                               "media": PLATAFORMA["media"], "talud": PLATAFORMA["talud"], "largo": x1 - x0}
    return resultado


def _tramo_del_puente(linea: LineString):
    """El tramo de la vía que va por el puente (en fracción de su largo): ahí no se nivela
    el terreno (debajo está el río)."""
    a, b = D.PUENTE_FERROCARRIL["puntos"]
    if linea.distance(Point(a)) > 5.0:
        return None
    s0, s1 = sorted((linea.project(Point(a)), linea.project(Point(b))))
    return ((s0 - 2.0) / linea.length, (s1 + 2.0) / linea.length)


def _a_la_altura_de(perfil: dict, xs, ys) -> np.ndarray:
    """La altura de una rasante en la proyección de cada punto sobre su vía."""
    d, f = R._distancia_polilinea(np.asarray(xs, float), np.asarray(ys, float), perfil["puntos"])
    return np.interp(f, perfil["s"], perfil["z"])


def _empalme(hechos: dict, x: float, y: float):
    """La altura de la vía ya trazada que pasa por el punto (un empalme), si alguna pasa."""
    for perfil in hechos.values():
        d, f = R._distancia_polilinea(np.array([x]), np.array([y]), perfil["puntos"])
        if d[0] < 3.0:
            return float(np.interp(f[0], perfil["s"], perfil["z"]))
    return None


def carril_en(perfiles_vias: dict, x: float, y: float, alcance: float = 2.0):
    """Lo alto del carril de la vía que pasa por el punto (la más cercana, a menos de
    `alcance`), o None si no pasa ninguna."""
    mejor = None
    for ident, perfil in perfiles_vias.items():
        if ident == "plataforma":
            continue
        d, f = R._distancia_polilinea(np.array([x], float), np.array([y], float), perfil["puntos"])
        if d[0] < alcance and (mejor is None or d[0] < mejor[0]):
            mejor = (d[0], float(np.interp(f[0], perfil["s"], perfil["z"])) + CARRIL)
    return None if mejor is None else mejor[1]


def z_en(perfil: dict, puntos) -> np.ndarray:
    """La rasante de una vía en puntos de su trazado."""
    xy = np.asarray(puntos, float)
    return _a_la_altura_de(perfil, xy[:, 0], xy[:, 1])


# ---------------------------------------------------------------------------
# Pasos a nivel: la calle sube hasta el carril
# ---------------------------------------------------------------------------
def cruces(perfiles_vias: dict, calles) -> list[dict]:
    """Donde una vía de tren cruza el tránsito (una calle, una plaza): el tramo y la altura
    del carril."""
    resultado = []
    for ident, perfil in perfiles_vias.items():
        if ident == "plataforma":
            continue
        linea = LineString(perfil["puntos"])
        corte = linea.intersection(calles)
        for tramo in getattr(corte, "geoms", [corte]):
            if tramo.is_empty or tramo.length < 0.5 or tramo.geom_type != "LineString":
                continue
            puntos = list(tramo.coords)
            z = z_en(perfil, puntos)
            largo = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(np.asarray(puntos), axis=0).T))])
            resultado.append({"via": ident, "tramo": puntos, "s": largo / largo[-1],
                              "carril": z + CARRIL})
    return resultado


def subir_pasos(rasante: np.ndarray, res: float, pasos: list[dict], nivel_calzada: float) -> np.ndarray:
    """La rasante del tránsito en los pasos a nivel: sube hasta que la calzada llega al
    carril (al de cada punto del paso, que la vía puede ir en pendiente), en una franja a lo
    largo de la vía y con una rampa a cada lado."""
    from transito import _rejilla

    gx, gy = _rejilla(rasante.shape, res)
    resultado = rasante.copy()
    for paso in pasos:
        pts = np.asarray(paso["tramo"], float)
        alcance = PASO_NIVEL + RAMPA_PASO + 30.0
        caja = ((gx >= pts[:, 0].min() - alcance) & (gx <= pts[:, 0].max() + alcance)
                & (gy >= pts[:, 1].min() - alcance) & (gy <= pts[:, 1].max() + alcance))
        d, f = R._distancia_polilinea(gx[caja], gy[caja], paso["tramo"])
        t = np.clip((d - PASO_NIVEL) / RAMPA_PASO, 0.0, 1.0)
        peso = 1.0 - t * t * (3.0 - 2.0 * t)
        objetivo = np.interp(f, paso["s"], paso["carril"]) - nivel_calzada
        valores = resultado[caja]
        resultado[caja] = np.maximum(valores, valores + (objetivo - valores) * peso)
    return resultado


def subir_terreno(h: np.ndarray, res: float, antes: np.ndarray, despues: np.ndarray, pavimento,
                  nivel: float) -> np.ndarray:
    """El terreno junto a los pasos a nivel sube con la calle, como el terraplén de sus
    rampas: hasta la acera en el borde de lo pavimentado y con un talud de TALUD_PASO hacia
    fuera. La caja de las vías (a menos de CAJA_VIA de su eje) se queda como estaba."""
    from transito import _rejilla

    resultado = h.copy()
    sube = (despues - antes) > 0.005
    if not sube.any():
        return resultado
    gx, gy = _rejilla(h.shape, res)
    xs, ys = gx[sube], gy[sube]
    shapely.prepare(pavimento)
    fuera = shapely.distance(pavimento, shapely.points(xs, ys))
    via = np.full(xs.shape, np.inf)
    for v in D.VIAS:
        via = np.minimum(via, R.distancia_polilinea(xs, ys, v["puntos"]))
    objetivo = despues[sube] + nivel - fuera / TALUD_PASO
    nuevo = np.maximum(h[sube], objetivo)
    resultado[sube] = np.where(via < CAJA_VIA, h[sube], nuevo)
    return resultado


# ---------------------------------------------------------------------------
# Los andenes de la estación
# ---------------------------------------------------------------------------
def andenes(perfiles_vias: dict) -> list[dict]:
    """Los dos andenes isla de la estación (entre la vía principal y cada vía de andén),
    con una rampa en cada punta: polígono, altura y, en las rampas, la pendiente."""
    principal = perfiles_vias["principal"]
    x0, x1 = ANDENES_X
    resultado = []
    for via in ("anden_1", "anden_2"):
        perfil = perfiles_vias[via]
        y_via = float(np.mean([p[1] for p in perfil["puntos"] if x0 <= p[0] <= x1]))
        y_principal = float(np.interp((x0 + x1) / 2, [p[0] for p in principal["puntos"]],
                                      [p[1] for p in principal["puntos"]]))
        bajo, alto = sorted((y_via, y_principal))
        y_sur, y_norte = bajo + ANDEN_BORDE, alto - ANDEN_BORDE
        carril = float(z_en(principal, [((x0 + x1) / 2, y_principal)])[0]) + CARRIL
        z = carril + ANDEN_ALTO
        rampa = (z - (carril - CARRIL)) / PENDIENTE_ANDEN
        resultado.append({"forma": Polygon([(x0, y_sur), (x1, y_sur), (x1, y_norte), (x0, y_norte)]), "z": z,
                          "nombre": f"Andén de la {via}"})
        for extremo, signo in ((x0, -1.0), (x1, 1.0)):
            fin = extremo + signo * rampa
            forma = Polygon([(extremo, y_sur), (fin, y_sur), (fin, y_norte), (extremo, y_norte)])
            # Baja hacia fuera: z en el extremo del andén, la plataforma en la punta.
            resultado.append({"forma": forma.buffer(0), "z": z, "gx": -signo * PENDIENTE_ANDEN, "ox": extremo,
                              "nombre": f"Rampa del andén de la {via}"})
    return resultado


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------
def tramos(perfiles_vias: dict, transito) -> list[dict]:
    """Cada vía partida en tramos: abiertos (balasto, traviesas y carriles, a la altura de
    su rasante) y embebidos (a ras de la calle o la plaza que cruzan)."""
    resultado = []
    for via in D.VIAS:
        perfil = perfiles_vias[via["id"]]
        linea = LineString(perfil["puntos"])
        embebida = linea.intersection(transito)
        abierta = linea.difference(transito)
        partes = []
        for tipo, geom in (("abierta", abierta), ("embebida", embebida)):
            for tramo in getattr(geom, "geoms", [geom]):
                if tramo.is_empty or tramo.length < 0.3 or tramo.geom_type != "LineString":
                    continue
                puntos = _densificar(list(tramo.coords), 4.0)
                z = z_en(perfil, puntos)
                partes.append({"tipo": tipo, "puntos": [(round(x, 3), round(y, 3), round(float(v), 3))
                                                         for (x, y), v in zip(puntos, z)]})
        resultado.append({"id": via["id"], "tipo": via["tipo"], "tramos": partes})
    return resultado


def eje_tranvia(puntos) -> list[tuple[float, float]]:
    """El eje de una línea de tranvía con las esquinas redondeadas: un arco de
    RADIO_TRANVIA en cada una (más cerrado donde los tramos no dan para tanto)."""
    pts = [np.asarray(p, float) for p in puntos]
    # Los tramos muy cortos (un quiebro del trazado) se funden en una esquina.
    k = 1
    while k < len(pts):
        if np.linalg.norm(pts[k] - pts[k - 1]) >= TRAMO_MINIMO_TRANVIA or len(pts) <= 2:
            k += 1
        elif k == 1:
            del pts[1]
        elif k == len(pts) - 1:
            del pts[k - 1]
        else:
            pts[k - 1] = (pts[k - 1] + pts[k]) / 2.0
            del pts[k]
    n = len(pts)
    largos = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(n - 1)]
    direcciones = [(pts[i + 1] - pts[i]) / largos[i] for i in range(n - 1)]
    giros = [0.0] * n
    tangentes = [0.0] * n
    for i in range(1, n - 1):
        u, v = direcciones[i - 1], direcciones[i]
        giros[i] = math.acos(float(np.clip(np.dot(u, v), -1.0, 1.0)))
        tangentes[i] = RADIO_TRANVIA * math.tan(giros[i] / 2.0)
    # Cada tramo se reparte entre las curvas de sus dos puntas, a prorrata.
    limitadas = list(tangentes)
    for i in range(n - 1):
        suma = tangentes[i] + tangentes[i + 1]
        if suma > largos[i]:
            for j in (i, i + 1):
                limitadas[j] = min(limitadas[j], largos[i] * tangentes[j] / suma)
    resultado = [tuple(pts[0])]
    for i in range(1, n - 1):
        if giros[i] < 1e-4 or limitadas[i] < 1e-3:
            resultado.append(tuple(pts[i]))
            continue
        u, v = direcciones[i - 1], direcciones[i]
        radio = limitadas[i] / math.tan(giros[i] / 2.0)
        inicio = pts[i] - u * limitadas[i]
        lado = 1.0 if u[0] * v[1] - u[1] * v[0] > 0.0 else -1.0
        centro = inicio + np.array([-u[1], u[0]]) * lado * radio
        angulo = math.atan2(inicio[1] - centro[1], inicio[0] - centro[0])
        pasos = max(2, int(math.ceil(radio * giros[i] / 2.0)))
        for k in range(pasos + 1):
            a = angulo + lado * giros[i] * k / pasos
            resultado.append((float(centro[0] + radio * math.cos(a)), float(centro[1] + radio * math.sin(a))))
    resultado.append(tuple(pts[-1]))
    return resultado


def ejes_tranvia() -> list[tuple[str, LineString]]:
    """Los ejes de las vías del tranvía: dos por línea (ida y vuelta), a cada lado del de la
    línea."""
    resultado = []
    for linea in D.TRANVIAS:
        eje = LineString(eje_tranvia(linea["puntos"]))
        for lado in (-1.0, 1.0):
            resultado.append((linea["id"], eje.offset_curve(lado * TRANVIA_ENTREVIA, join_style=2, mitre_limit=3.0)))
    return resultado


def tranvias(transito) -> list[dict]:
    """Las vías del tranvía, por la calle (a ras): lo que de cada una cae en el tránsito."""
    resultado = []
    for ident, via in ejes_tranvia():
        dentro = via.intersection(transito)
        for tramo in getattr(dentro, "geoms", [dentro]):
            if tramo.is_empty or tramo.length < 1.0 or tramo.geom_type != "LineString":
                continue
            resultado.append({"linea": ident, "puntos": [(round(x, 3), round(y, 3)) for x, y in tramo.coords]})
    return resultado


def puente(perfiles_vias: dict) -> dict:
    """El tablero del puente del ferrocarril: la rasante de la principal en sus dos puntas."""
    a, b = D.PUENTE_FERROCARRIL["puntos"]
    z = z_en(perfiles_vias["principal"], [a, b])
    return {"z": [round(float(z[0]), 3), round(float(z[1]), 3)]}


def _densificar(puntos: list, paso: float) -> list:
    resultado = [puntos[0]]
    for a, b in zip(puntos, puntos[1:]):
        n = max(1, int(math.ceil(math.dist(a, b) / paso)))
        for k in range(1, n + 1):
            resultado.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return resultado
