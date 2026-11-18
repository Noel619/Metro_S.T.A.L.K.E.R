"""El Tumán en pleno invierno: helado de orilla a orilla casi todo el río, pero con agua
abierta donde la corriente o el calor no lo dejan cerrarse (README, «El Tumán helado, con
cinco cruces»; CIUDAD.md, «El río y sus cinco cruces»).

- El canal: a lo largo de la corriente (el río corre de este a oeste, relieve.py), una
  franja de agua negra que se abre y se cierra (hasta CANAL_ANCHO metros), cortada por
  puentes de hielo donde se cruza a pie: el tubo, el puente hundido (su vano caído descansa
  en el hielo) y el hielo frente al puerto.
- Las bolsas de agua abierta en el hielo fino del plano (datos.HIELO_FINO): el agua
  templada que suelta la central, la más grande, que corre río abajo pegada a la orilla sur;
  la de los desagües del puerto, donde se quedó una barcaza; las de los remolinos junto a
  las pilas del puente hundido y la de bajo la autovía caída.
- Alrededor del agua, el hielo es fino (oscuro, sin nieve, deja ver el agua) y en su borde
  está roto en témpanos, con el agua entre ellos; algunos van sueltos por el agua.
- El lecho: bajo el hielo y el agua, el fondo baja hasta LECHO_HONDO bajo el hielo en el
  centro del río (relieve.lecho_rio, en el relieve).

El hielo sigue a NIVEL_HIELO (lo que se pisa, como antes) y el agua, FRANCOBORDO más abajo.
Se exporta a data/ciudad/rio.json: la superficie del agua (triangulada, con cuánto aguanieve
hay junto al hielo en cada vértice) y las placas de hielo (el hielo de orilla, el fino, los
témpanos del borde y los sueltos), que la maqueta levanta con su grosor y su colisión.
"""

from __future__ import annotations

import json
import math
import random

import numpy as np
import shapely
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import datos as D
import relieve as R
from geo import eje

NIVEL_HIELO = R.NIVEL_HIELO
# Lo que asoma el hielo (con su nieve) sobre el agua, y el grosor de cada clase de placa.
FRANCOBORDO = 0.18
NIVEL_AGUA = NIVEL_HIELO - FRANCOBORDO
GROSOR = {"hielo": 0.5, "fino": 0.22, "temano": 0.35, "suelto": 0.28}
# El canal de la corriente: los tramos de río (en x) donde se abre, su ancho máximo y lo que
# tarda en cerrarse en cada punta.
CANAL_TRAMOS = [(40.0, 285.0), (365.0, 700.0), (840.0, 990.0), (1115.0, 1250.0)]
CANAL_ANCHO = 22.0
CANAL_PUNTAS = 35.0
# Hielo pegado a las orillas que nunca se abre (junto a los desagües del puerto, menos).
ORILLA = 5.0
ORILLA_DESAGUES = 2.0
# Los cruces a pie siguen helados (x de cada uno, y medio ancho) y el vano caído del puente
# descansa en el hielo.
CRUCES_HELADOS = [(324.0, 30.0), (1050.0, 40.0)]
# El hielo roto del borde del agua: la franja, el paso de los témpanos y su junta.
BANDA_ROTA = 3.2
PASO_TEMPANO = 2.3
JUNTA = 0.09
# Lo que se levantan algunos témpanos del borde (montados unos sobre otros por la corriente).
LEVANTADOS = 0.12
LEVANTA = (6.0, 18.0)
# Témpanos sueltos: uno por cada tantos m² de agua y sus radios.
SUELTOS_CADA = 140.0
SUELTO_RADIO = (0.7, 2.2)
# Hielo fino alrededor del agua (además del que marca el plano).
FINO_ALREDEDOR = 4.0
# Aguanieve en el agua junto al hielo: lo que entra.
AGUANIEVE = 2.5
DECIMALES = 2


def _semilla(clave: str) -> int:
    import deterioro as DT

    return DT._semilla(clave)


def _irregular(cx: float, cy: float, rx: float, ry: float, angulo: float, clave: str, puntos: int = 40,
               irregular: float = 0.22) -> Polygon:
    """Una elipse de bordes irregulares (unos armónicos con fase de su clave)."""
    rng = random.Random(_semilla(clave))
    armonicos = [(k, rng.uniform(0.0, 2.0 * math.pi), rng.uniform(0.3, 1.0) / k) for k in (2, 3, 5, 7)]
    total = sum(a for _, _, a in armonicos)
    c, s = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
    anillo = []
    for i in range(puntos):
        t = 2.0 * math.pi * i / puntos
        f = 1.0 + irregular * sum(a * math.sin(k * t + fase) for k, fase, a in armonicos) / total
        x, y = math.cos(t) * rx * f, math.sin(t) * ry * f
        anillo.append((cx + x * c - y * s, cy + x * s + y * c))
    return Polygon(anillo)


def _ondas(x: float, fases: tuple[float, ...]) -> float:
    """Una curva suave entre -1 y 1 a lo largo del río."""
    return (math.sin(x / 97.0 + fases[0]) * 0.55 + math.sin(x / 41.0 + fases[1]) * 0.3
            + math.sin(x / 17.0 + fases[2]) * 0.15)


def canal() -> Polygon:
    """El canal de la corriente, por tramos: serpentea por el centro del río (hacia la
    orilla de fuera en las curvas) y se abre y se cierra."""
    piezas = []
    for x0, x1 in CANAL_TRAMOS:
        xs = np.arange(x0, x1 + 1e-6, 3.0)
        arriba, abajo = [], []
        for x in xs:
            puntas = min(1.0, (x - x0) / CANAL_PUNTAS, (x1 - x) / CANAL_PUNTAS)
            ancho = CANAL_ANCHO * max(0.0, puntas) * (0.55 + 0.45 * _ondas(x, (2.1, 0.4, 1.7)))
            centro = float(R.rio_y(x)) + 0.16 * float(R.rio_ancho(x)) * _ondas(x, (1.3, 2.6, 0.2))
            arriba.append((float(x), centro + ancho / 2.0 * (1.0 + 0.12 * math.sin(x / 7.3 + 1.1))))
            abajo.append((float(x), centro - ancho / 2.0 * (1.0 + 0.12 * math.sin(x / 6.1 + 2.3))))
        forma = Polygon(arriba + list(reversed(abajo))).buffer(0)
        if not forma.is_empty:
            piezas.append(forma)
    return unary_union(piezas)


def central() -> Polygon:
    """El agua templada de la central: sale por su desagüe en la curva (datos.HIELO_FINO) y
    corre río abajo, hacia el oeste, pegada a la orilla sur, cada vez más estrecha."""
    xs = np.arange(1230.0, 1471.0, 3.0)
    dentro, fuera = [], []
    for x in xs:
        sur = float(R.orilla_sur(x)) + ORILLA - 1.0
        ancho = float(np.interp(x, [1230, 1300, 1380, 1440, 1470], [6.0, 18.0, 34.0, 46.0, 24.0]))
        ancho *= 1.0 + 0.12 * math.sin(x / 11.0 + 0.7)
        dentro.append((float(x), sur))
        fuera.append((float(x), sur + ancho))
    return Polygon(dentro + list(reversed(fuera))).buffer(2.0).buffer(-2.0)


def bolsas() -> list[Polygon]:
    """Las otras bolsas de agua abierta: los desagües del puerto, la autovía caída y los
    remolinos junto a las pilas del puente hundido (en sus dos puntas)."""
    resultado = [
        _irregular(1000.0, 669.0, 24.0, 6.5, 0.0, "rio/puerto"),
        _irregular(14.0, 766.0, 13.0, 24.0, 0.0, "rio/autovia"),
    ]
    for s in (470.0, 545.0):
        for lado in (-1.0, 1.0):
            x, y = eje(s, lado * 23.0)
            resultado.append(_irregular(x, y, 5.5, 3.5, 0.0, f"rio/pila/{s}/{lado}", irregular=0.3))
    return resultado


def protegido():
    """Lo que nunca se abre: los cruces a pie y el vano hundido del puente con su margen."""
    import transito as T

    rio = D.RIO.bounds
    cruces = [box(x - medio, rio[1] - 10.0, x + medio, rio[3] + 10.0) for x, medio in CRUCES_HELADOS]
    return unary_union(cruces + [T._hueco_puente().buffer(2.0)])


def agua_abierta():
    """Todo el agua abierta: el canal, la central y las bolsas, lejos de las orillas (menos
    junto a los desagües) y nunca en los cruces."""
    lejos = D.RIO.buffer(-ORILLA)
    puerto, *otras = bolsas()
    agua = unary_union([canal().intersection(lejos), central().intersection(lejos)]
                       + [b.intersection(lejos) for b in otras]
                       + [puerto.intersection(D.RIO.buffer(-ORILLA_DESAGUES))])
    agua = agua.difference(protegido()).buffer(0.6).buffer(-0.6)
    return unary_union([p for p in _poligonos(agua) if p.area > 6.0])


def _poligonos(forma) -> list[Polygon]:
    if forma.is_empty:
        return []
    if forma.geom_type == "Polygon":
        return [forma]
    return [g for g in getattr(forma, "geoms", []) if g.geom_type == "Polygon" and not g.is_empty]


def zonas() -> dict:
    """El río repartido: el agua abierta, la franja de hielo roto de su borde, el hielo fino
    y el hielo de orilla."""
    import transito as T

    agua = agua_abierta()
    # Bajo el vano caído del puente el hielo aguanta entero (descansa en él).
    rota = agua.buffer(BANDA_ROTA).difference(agua).intersection(D.RIO.buffer(-0.8)).difference(
        T._hueco_puente())
    fino = unary_union([m["forma"] for m in D.HIELO_FINO] + [agua.buffer(BANDA_ROTA + FINO_ALREDEDOR)])
    fino = fino.intersection(D.RIO).difference(agua).difference(rota)
    hielo = D.RIO.difference(agua).difference(rota).difference(fino)
    return {"agua": agua, "rota": rota, "fino": fino, "hielo": hielo}


def _plano(rng: random.Random, inclina: tuple[float, float]) -> tuple[float, float]:
    """La pendiente (gx, gy) de una placa inclinada `inclina` grados (de .. a) en un rumbo
    cualquiera."""
    grados = rng.uniform(*inclina)
    rumbo = rng.uniform(0.0, 2.0 * math.pi)
    t = math.tan(math.radians(grados))
    return t * math.cos(rumbo), t * math.sin(rumbo)


def tempanos(rota) -> list[dict]:
    """El hielo roto del borde del agua: celdas de Voronoi de una rejilla movida, con la junta
    abierta; cada uno algo hundido y ladeado, y alguno montado sobre los demás."""
    if rota.is_empty:
        return []
    minx, miny, maxx, maxy = rota.bounds
    rng = random.Random(_semilla("rio/tempanos"))
    semillas = []
    shapely.prepare(rota)
    for px in np.arange(minx, maxx + PASO_TEMPANO, PASO_TEMPANO):
        for py in np.arange(miny, maxy + PASO_TEMPANO, PASO_TEMPANO):
            x = px + rng.uniform(-0.45, 0.45) * PASO_TEMPANO
            y = py + rng.uniform(-0.45, 0.45) * PASO_TEMPANO
            if shapely.contains_xy(rota, x, y):
                semillas.append(Point(x, y))
    celdas = shapely.voronoi_polygons(shapely.MultiPoint(semillas), extend_to=rota.envelope.buffer(5.0))
    resultado = []
    for celda in celdas.geoms:
        for pieza in _poligonos(celda.intersection(rota).buffer(-JUNTA)):
            if pieza.area < 0.25:
                continue
            c = pieza.centroid
            r = random.Random(_semilla(f"rio/tempano/{c.x:.2f}/{c.y:.2f}"))
            levantado = r.random() < LEVANTADOS
            gx, gy = _plano(r, LEVANTA if levantado else (0.0, 3.0))
            z = NIVEL_HIELO - r.uniform(0.02, 0.1) + (0.12 if levantado else 0.0)
            resultado.append(_placa("temano", pieza, z, gx, gy))
    return resultado


def sueltos(agua) -> list[dict]:
    """Témpanos sueltos por el agua abierta: placas pequeñas y redondeadas, sin tocarse."""
    resultado = []
    puestos: list[tuple[float, float, float]] = []
    piezas = sorted(_poligonos(agua), key=lambda p: (round(p.centroid.x, 1), round(p.centroid.y, 1)))
    for k, pieza in enumerate(piezas):
        dentro = pieza.buffer(-1.0)
        quiere = int(pieza.area / SUELTOS_CADA)
        if dentro.is_empty or quiere == 0:
            continue
        shapely.prepare(dentro)
        rng = random.Random(_semilla(f"rio/sueltos/{k}"))
        minx, miny, maxx, maxy = dentro.bounds
        aqui = 0
        for _ in range(quiere * 4):
            if aqui >= quiere:
                break
            x, y = rng.uniform(minx, maxx), rng.uniform(miny, maxy)
            r = rng.uniform(*SUELTO_RADIO)
            if not shapely.contains_xy(dentro, x, y) or any(
                    math.hypot(x - a, y - b) < r + q + 0.6 for a, b, q in puestos):
                continue
            forma = _irregular(x, y, r, r * rng.uniform(0.6, 1.0), rng.uniform(0.0, 180.0),
                               f"rio/suelto/{x:.2f}/{y:.2f}", puntos=9, irregular=0.3)
            for p in _poligonos(forma.intersection(pieza.buffer(-0.2))):
                if p.area > 0.4:
                    gx, gy = _plano(rng, (0.0, 2.0))
                    resultado.append(_placa("suelto", p, NIVEL_AGUA + 0.06, gx, gy))
            puestos.append((x, y, r))
            aqui += 1
    return resultado


def _placa(clase: str, forma: Polygon, z: float, gx: float = 0.0, gy: float = 0.0) -> dict:
    """Una placa de hielo: su forma (con huecos), el plano de su cara de arriba (z en su
    centro y pendiente) y su grosor."""
    c = forma.centroid
    return {"clase": clase, "forma": forma, "z": z, "gx": gx, "gy": gy, "cx": c.x, "cy": c.y,
            "grosor": GROSOR[clase]}


def _triangulos(forma: Polygon) -> tuple[list, list]:
    import transito as T

    return T._triangular(forma)


def _malla_agua(zonas_rio: dict) -> dict:
    """La superficie del agua: el agua abierta y, bajo los témpanos del borde, lo que se ve
    entre ellos (un poco más allá, para que no quede rendija). Con anillos hacia dentro para
    que el aguanieve de junto al hielo (1 en el borde, 0 a AGUANIEVE metros) tenga vértices."""
    agua = zonas_rio["agua"]
    superficie = unary_union([agua, zonas_rio["rota"]]).buffer(0.4).intersection(D.RIO.buffer(-0.3))
    anillos = [superficie, agua.buffer(-1.0), agua.buffer(-AGUANIEVE)]
    piezas = [shapely.set_precision(a, 10 ** -DECIMALES)
              for a in (anillos[0].difference(anillos[1]), anillos[1].difference(anillos[2]), anillos[2])]
    borde = agua.boundary
    puntos, triangulos, orilla = [], [], []
    indice = {}
    for pieza in piezas:
        for p in _poligonos(pieza):
            vertices, tris = _triangulos(p)
            mapa = []
            for x, y in vertices:
                clave = (round(x, DECIMALES), round(y, DECIMALES))
                if clave not in indice:
                    indice[clave] = len(puntos)
                    puntos.append(clave)
                    dentro = agua.contains(Point(x, y))
                    d = borde.distance(Point(x, y)) if dentro else 0.0
                    orilla.append(round(max(0.0, 1.0 - d / AGUANIEVE), 2))
                mapa.append(indice[clave])
            triangulos += [mapa[i] for i in tris]
    return {"puntos": [v for p in puntos for v in p], "triangulos": triangulos, "orilla": orilla}


def _exportar_placas(placas: list[dict]) -> dict:
    """Las placas por columnas: su clase, su plano, su grosor, los anillos de su contorno
    (exterior y huecos, en orden) y los triángulos de su cara de arriba."""
    clases = sorted({p["clase"] for p in placas})
    resultado = {"clases": clases, "clase": [], "z": [], "gx": [], "gy": [], "cx": [], "cy": [], "grosor": [],
                 "puntos": [], "anillos": [], "triangulos": []}
    for p in placas:
        forma = p["forma"]
        anillos = [list(forma.exterior.coords)[:-1]] + [list(h.coords)[:-1] for h in forma.interiors]
        indice = {}
        planos = []
        tamanos = []
        for anillo in anillos:
            tamanos.append(len(anillo))
            for x, y in anillo:
                clave = (round(x, DECIMALES), round(y, DECIMALES))
                indice.setdefault(clave, len(planos))
                planos.append(clave)
        vertices, tris = _triangulos(forma)
        extra = []
        mapa = []
        for x, y in vertices:
            clave = (round(x, DECIMALES), round(y, DECIMALES))
            if clave not in indice:
                indice[clave] = len(planos) + len(extra)
                extra.append(clave)
            mapa.append(indice[clave])
        resultado["clase"].append(clases.index(p["clase"]))
        resultado["z"].append(round(p["z"], 3))
        resultado["gx"].append(round(p["gx"], 4))
        resultado["gy"].append(round(p["gy"], 4))
        resultado["cx"].append(round(p["cx"], DECIMALES))
        resultado["cy"].append(round(p["cy"], DECIMALES))
        resultado["grosor"].append(p["grosor"])
        resultado["puntos"].append([v for q in planos + extra for v in q])
        resultado["anillos"].append(tamanos)
        resultado["triangulos"].append([mapa[i] for i in tris])
    return resultado


def calcular() -> dict:
    """El río entero: sus zonas, sus placas de hielo y la superficie del agua."""
    z = zonas()
    placas = []
    for clase, nivel in (("hielo", NIVEL_HIELO), ("fino", NIVEL_HIELO - 0.06)):
        for p in _poligonos(z[clase]):
            if p.area > 0.5:
                placas.append(_placa(clase, p, nivel))
    placas += tempanos(z["rota"])
    placas += sueltos(z["agua"])
    # En la rejilla de 1 cm (la de rio.json): el contorno y los triángulos, con los mismos
    # vértices.
    limpias = []
    for p in placas:
        for forma in _poligonos(shapely.set_precision(p["forma"], 10 ** -DECIMALES)):
            if forma.area > 0.2:
                limpias.append({**p, "forma": orient(forma, sign=1.0)})
    return {"zonas": z, "placas": limpias, "agua": _malla_agua(z)}


def nivel_en(rio: dict, x: float, y: float) -> float:
    """Lo que hay arriba en un punto del río: el agua o el hielo."""
    return NIVEL_AGUA if rio["zonas"]["agua"].contains(Point(x, y)) else NIVEL_HIELO


def exportar(rio: dict, carpeta) -> dict:
    """Escribe data/ciudad/rio.json; devuelve las cifras."""
    z = rio["zonas"]
    datos = {"version": 1, "hielo": NIVEL_HIELO, "agua": NIVEL_AGUA,
             "superficie": rio["agua"], "placas": _exportar_placas(rio["placas"])}
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    (carpeta / "rio.json").write_text(texto, encoding="utf-8")
    cuenta = {}
    for p in rio["placas"]:
        cuenta[p["clase"]] = cuenta.get(p["clase"], 0) + 1
    return {"archivo": "rio.json", "agua_m2": round(z["agua"].area), "fino_m2": round(z["fino"].area),
            "rota_m2": round(z["rota"].area), "placas": cuenta, "kb": round(len(texto) / 1024)}
