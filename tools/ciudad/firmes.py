"""El firme roto: tramos de calle que ya no son una superficie, sino placas sueltas.

Dos inviernos de helada sin que nadie toque la calle: el agua entra por las grietas, se
hiela, levanta el asfalto y lo parte en placas; cuando se funde, se lleva la grava de
debajo y las placas se hunden o se montan unas en otras. Cerca de la Zona Cero, la onda y
los incendios rompieron mucho más (README, «La ambientación de la superficie»).

Cada zona rota (`zonas`) es un hueco irregular dentro de una sola clase de superficie
(calzada, acera, losas, adoquín…), alargado a lo largo de la calle. El tránsito se corta
por su contorno y lo llena:

- La base: una malla propia (la clase "firme", con la regla "malla" de transito.py), la
  grava y la tierra de debajo, unos centímetros más baja que la calle. En el borde, la
  arista "derrumbe" pinta el corte de la calle.
- Las placas (`placas`): la costra rota en trozos (celdas de Voronoi con su junta
  abierta), cada uno con su inclinación; algunos faltan, y a lo largo de un lomo de
  presión se levantan y se apoyan unos contra otros. La maqueta las levanta como prismas
  (con su colisión): la calle deja de ser plana.

Todo determinista: el azar sale de la clave de cada cosa.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np
import shapely
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import datos as D
import deterioro as DT
from geo import banda

# Lo que baja la base de un firme roto (la grava y la tierra) bajo lo que se pisa.
BAJA = 0.12
# Por clase: metros cuadrados de clase por cada zona rota, el área de cada zona (de, a),
# el área de cada placa y su grosor (la costra que se ve en el canto).
CLASES = {
    "calzada": {"cada": 420.0, "area": (16.0, 150.0), "placa": 1.9, "grosor": 0.11},
    # Entre los carriles del tranvía: tiras estrechas (media anchura, como mucho).
    "via_tranvia": {"cada": 30.0, "area": (1.5, 5.0), "placa": 0.3, "grosor": 0.12, "estrecha": 0.4},
    "adoquin": {"cada": 350.0, "area": (8.0, 40.0), "placa": 0.6, "grosor": 0.13},
    "acera": {"cada": 550.0, "area": (5.0, 30.0), "placa": 0.9, "grosor": 0.08, "margen": 0.3},
    "losas": {"cada": 550.0, "area": (5.0, 26.0), "placa": 0.45, "grosor": 0.07, "margen": 0.3},
    "plaza": {"cada": 650.0, "area": (8.0, 70.0), "placa": 0.7, "grosor": 0.08},
    "isleta": {"cada": 500.0, "area": (4.0, 24.0), "placa": 0.45, "grosor": 0.07, "margen": 0.3},
    "paseo": {"cada": 800.0, "area": (6.0, 30.0), "placa": 0.45, "grosor": 0.07},
}
# Cuántas veces más zonas rotas (y más grandes) según la distancia a la Zona Cero.
ZONA_CERO = ((500.0, 4.0), (800.0, 2.6), (1100.0, 1.6))
MAS_ZONAS = 4.0
# Margen hasta el borde de su clase (el bordillo sigue en pie) y entre zonas.
MARGEN = 0.45
SEPARACION = 1.5
# Las placas: la junta que se abre entre ellas, las que faltan, cuánto suben o bajan y
# se inclinan, el lomo de presión (en cuántas zonas, cuánto se levantan las de junto a él
# y hasta dónde) y lo más alto que llegan sobre la calle.
JUNTA = (0.02, 0.12)
FALTAN = 0.1
SUBEN = (-0.06, 0.07)
INCLINACION = 0.2
LOMOS = 0.7
LOMO = (0.12, 0.3)
LOMO_ANCHO = 1.5
TECHO = 0.4
# Las zonas que se hunden en cubeta (el agua se llevó la grava de debajo) y cuánto.
HUNDIDAS = 0.3
HUNDE = (0.12, 0.32)


@dataclass
class Zona:
    """Una zona de firme roto: su clave, su clase, el contorno (antihorario), sus vértices,
    el centro y el rumbo de la calle (grados)."""

    clave: str
    clase: str
    contorno: Polygon
    borde: np.ndarray
    centro: tuple[float, float]
    rumbo: float
    # Lo que se hunde en el centro (0: no es una cubeta, se levanta).
    hundida: float = 0.0


def _factor(x: float, y: float) -> float:
    """Cuántas veces más rotura que en el resto de la ciudad, según la Zona Cero."""
    d = math.hypot(x - D.GZ[0], y - D.GZ[1])
    for radio, factor in ZONA_CERO:
        if d < radio:
            return factor
    return 1.0


def _rumbos():
    """Para saber hacia dónde va la calle en un punto: los tramos de los ejes."""
    tramos = [(LineString([a, b]), math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
              for c in D.CALLES if c["tipo"] not in ("camino", "escalinata")
              for a, b in zip(c["puntos"], c["puntos"][1:])]
    return shapely.STRtree([l for l, _ in tramos]), tramos


def huella_vehiculo(v: dict, margen: float = 0.0) -> Polygon:
    """Lo que ocupa un vehículo en planta (con un margen)."""
    from geo import rect

    largo, ancho = D.MEDIDAS.get(v["tipo"], (4.5, 1.8))
    return rect(v["pos"][0], v["pos"][1], largo + 2.0 * margen, ancho + 2.0 * margen, v["angulo"])


_HUELLAS = None


def _huellas_vehiculos():
    """Las huellas de los vehículos (con su árbol para buscarlas)."""
    global _HUELLAS
    if _HUELLAS is None:
        formas = [huella_vehiculo(v, 0.35) for v in D.VEHICULOS]
        _HUELLAS = (formas, shapely.STRtree(formas))
    return _HUELLAS


def _prohibido(t) -> object:
    """Donde no se rompe el firme: bajo los árboles, junto a los socavones y a las vías
    del tren y del tranvía. Bajo los vehículos sí (se quedan sin placas debajo)."""
    formas = [Point(a["pos"]).buffer(1.6) for a in D.ARBOLES]
    formas += [DT.huecos().buffer(1.5), unary_union([banda(v["puntos"], 6.0) for v in D.VIAS])]
    formas.append(DT.carriles_tranvia())
    return unary_union(formas)


def zonas(t) -> list[Zona]:
    """Las zonas de firme roto, clase a clase (sobre lo que se pisa ya cortado por los
    socavones): las sale al azar por su superficie (más cerca de la Zona Cero, donde
    también son más grandes), lejos del borde de su clase, de los vehículos, los árboles,
    las vías y los socavones, y sin tocarse entre ellas."""
    import ferrocarril as F

    arbol, tramos = _rumbos()
    ejes_tranvia = [eje for _, eje in F.ejes_tranvia()]
    largo_tranvia = sum(e.length for e in ejes_tranvia)
    prohibido = _prohibido(t)
    shapely.prepare(prohibido)
    hechas: list[Zona] = []
    ocupado = []
    for clase, cfg in CLASES.items():
        forma = t.superficies.get(clase)
        if forma is None or forma.is_empty:
            continue
        dentro = forma.buffer(-cfg.get("margen", MARGEN))
        if dentro.is_empty:
            continue
        shapely.prepare(dentro)
        rng = random.Random(DT._semilla("firmes/" + clase))
        x0, y0, x1, y1 = dentro.bounds
        intentos = int(forma.area / cfg["cada"] * MAS_ZONAS) + 1
        for k in range(intentos):
            sobre_eje = None
            if "estrecha" in cfg:
                # Entre los carriles: el centro, sobre el eje de una vía del tranvía.
                andado = rng.uniform(0.0, largo_tranvia)
                for eje in ejes_tranvia:
                    if andado <= eje.length:
                        sobre_eje = (eje, andado)
                        break
                    andado -= eje.length
                if sobre_eje is None:
                    continue
                p = sobre_eje[0].interpolate(sobre_eje[1])
                x, y = p.x, p.y
                if not shapely.contains_xy(dentro, x, y):
                    continue
            else:
                x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
                for _ in range(30):
                    if shapely.contains_xy(dentro, x, y):
                        break
                    x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
                else:
                    continue
            factor = _factor(x, y)
            if rng.random() > factor / MAS_ZONAS:
                continue
            area = rng.uniform(*cfg["area"]) * (1.0 + 0.35 * (factor - 1.0))
            largo = rng.uniform(1.2, 2.2)
            a = math.sqrt(area * largo / math.pi)
            b = area / (math.pi * a)
            if "estrecha" in cfg and b > cfg["estrecha"]:
                b = cfg["estrecha"]
                a = area / (math.pi * b)
            cerca = int(arbol.nearest(Point(x, y)))
            rumbo = tramos[cerca][1] + rng.uniform(-18.0, 18.0)
            if sobre_eje is not None:
                eje, andado = sobre_eje
                q = eje.interpolate(min(eje.length, andado + 0.5))
                r = eje.interpolate(max(0.0, andado - 0.5))
                rumbo = math.degrees(math.atan2(q.y - r.y, q.x - r.x))
            clave = f"firme/{clase}/{k}"
            for encoge in (1.0, 0.7, 0.5):
                borde = DT.borde_irregular(clave, (x, y), a * encoge, b * encoge, rumbo, 0.18, 0.9, 14)
                poligono = Polygon(borde)
                if not poligono.is_valid or not dentro.contains(poligono) or prohibido.intersects(poligono):
                    continue
                if any(poligono.distance(o) < SEPARACION for o in ocupado):
                    continue
                hundida = rng.uniform(*HUNDE) if rng.random() < HUNDIDAS else 0.0
                hechas.append(Zona(clave, clase, poligono, borde, (x, y), rumbo, hundida))
                ocupado.append(poligono)
                break
    return hechas


def malla(z: Zona, calle) -> DT.Malla:
    """La base de una zona rota: grava y tierra a BAJA bajo la calle (`calle(xs, ys)` da la
    altura de lo que se pisa), algo revuelta por dentro y, si la zona es una cubeta, más
    honda hacia el centro. Anillos del borde al centro."""
    rng = random.Random(DT._semilla(z.clave + "/base"))
    cx, cy = z.centro
    borde = z.borde
    n = len(borde)
    anillos = (1.0, 0.5)
    puntos = [np.array([cx, cy]) + (borde - np.array([cx, cy])) * f for f in anillos]
    puntos.append(np.array([[cx, cy]]))
    xy = np.concatenate(puntos)
    base = calle(xy[:, 0], xy[:, 1]) - BAJA
    revuelta = np.array([0.0] * n + [rng.uniform(-0.06, 0.02) for _ in range(len(xy) - n)])
    f = np.concatenate([np.full(n, a) for a in anillos] + [np.zeros(1)])
    z_base = base + revuelta - z.hundida * (1.0 - f * f)
    tris = []
    filas = len(anillos)
    for k in range(filas - 1):
        for i in range(n):
            j = (i + 1) % n
            tris += [(k * n + i, k * n + j, (k + 1) * n + j), (k * n + i, (k + 1) * n + j, (k + 1) * n + i)]
    centro = filas * n
    for i in range(n):
        tris.append(((filas - 1) * n + i, (filas - 1) * n + (i + 1) % n, centro))
    tris = np.array(tris, dtype=int)
    p0, p1, p2 = xy[tris[:, 0]], xy[tris[:, 1]], xy[tris[:, 2]]
    giro = (p1[:, 0] - p0[:, 0]) * (p2[:, 1] - p0[:, 1]) - (p1[:, 1] - p0[:, 1]) * (p2[:, 0] - p0[:, 0])
    tris[giro < 0] = tris[giro < 0][:, [0, 2, 1]]
    return DT.Malla(np.round(xy, 3), np.round(z_base, 3), tris, np.round(xy, 2), float(np.min(z_base)), 0.0)


def placas(z: Zona, calle) -> tuple[dict, list[Polygon]]:
    """Las placas de una zona rota: celdas de Voronoi de una rejilla movida (alineada con
    la calle), con su junta abierta; cada una sube, baja y se inclina a su aire, y junto a
    un lomo de presión (en la mayoría de las zonas, de través) se levantan hacia él; en las
    cubetas, caen hacia el centro. Devuelve lo que va a transito.json (la clase, el grosor,
    cuántas esquinas tiene cada placa y, seguidas, sus esquinas y la altura de cada una) y
    las formas (para poner matojos en las juntas)."""
    cfg = CLASES[z.clase]
    rng = random.Random(DT._semilla(z.clave + "/placas"))
    zona = z.contorno.buffer(-0.04)
    paso = math.sqrt(cfg["placa"])
    giro = math.radians(z.rumbo)
    c, s = math.cos(giro), math.sin(giro)
    cx, cy = z.centro
    x0, y0, x1, y1 = zona.bounds
    lado = math.hypot(x1 - x0, y1 - y0) / 2.0 + paso
    semillas = []
    for i in range(-int(lado / paso) - 1, int(lado / paso) + 2):
        for j in range(-int(lado / paso) - 1, int(lado / paso) + 2):
            u = (i + rng.uniform(-0.35, 0.35)) * paso
            v = (j + rng.uniform(-0.35, 0.35)) * paso
            px, py = cx + u * c - v * s, cy + u * s + v * c
            if zona.buffer(paso * 0.5).contains(Point(px, py)):
                semillas.append((px, py))
    datos = {"clase": z.clase, "grosor": cfg["grosor"], "caras": [], "puntos": [], "z": []}
    if len(semillas) < 3:
        return datos, []
    celdas = shapely.voronoi_polygons(MultiPoint(semillas), extend_to=zona.envelope.buffer(2.0 * paso))
    lomo = None
    radio = math.sqrt(z.contorno.area / math.pi)
    if z.hundida == 0.0 and rng.random() < LOMOS:
        a = giro + math.pi / 2.0 + rng.uniform(-0.6, 0.6)
        largo = lado * 2.0
        lomo = LineString([(cx - math.cos(a) * largo, cy - math.sin(a) * largo),
                           (cx + math.cos(a) * largo, cy + math.sin(a) * largo)])
    formas = []
    for celda in celdas.geoms:
        trozo = celda.intersection(zona)
        if trozo.is_empty:
            continue
        if trozo.geom_type != "Polygon":
            partes = [g for g in getattr(trozo, "geoms", []) if g.geom_type == "Polygon"]
            if not partes:
                continue
            trozo = max(partes, key=lambda g: g.area)
        placa = trozo.buffer(-rng.uniform(*JUNTA) / 2.0, join_style=2)
        if placa.is_empty or placa.geom_type != "Polygon" or placa.area < 0.05:
            continue
        if rng.random() < FALTAN:
            continue
        # Bajo un vehículo no queda placa: se hundió en la grava.
        formas_v, arbol_v = _huellas_vehiculos()
        if any(formas_v[int(i)].intersects(placa) for i in arbol_v.query(placa)):
            continue
        placa = orient(placa.simplify(0.03), sign=1.0)
        if placa.is_empty or placa.geom_type != "Polygon" or not placa.is_valid:
            continue
        centro = placa.centroid
        z_calle = float(calle([centro.x], [centro.y])[0])
        rumbo = rng.uniform(0.0, 2.0 * math.pi)
        pendiente = INCLINACION * rng.random() ** 2
        sube = rng.uniform(*SUBEN)
        if z.hundida > 0.0:
            # En una cubeta, todas caen hacia el centro.
            lejos = min(1.0, math.hypot(centro.x - cx, centro.y - cy) / radio)
            sube -= z.hundida * (1.0 - lejos * lejos)
            rumbo = math.atan2(cy - centro.y, cx - centro.x)
            pendiente = max(pendiente, 2.0 * z.hundida * lejos / radio)
        if lomo is not None:
            d = lomo.distance(centro)
            if d < LOMO_ANCHO:
                cerca = lomo.interpolate(lomo.project(centro))
                peso = 1.0 - d / LOMO_ANCHO
                sube += rng.uniform(*LOMO) * peso
                rumbo = math.atan2(cerca.y - centro.y, cerca.x - centro.x)
                pendiente = max(pendiente, rng.uniform(0.12, 0.3) * peso)
        esquinas = list(placa.exterior.coords)[:-1]
        alturas = []
        for x, y in esquinas:
            h = z_calle + sube + pendiente * ((x - centro.x) * math.cos(rumbo) + (y - centro.y) * math.sin(rumbo))
            alturas.append(min(z_calle + TECHO, max(z_calle - BAJA - z.hundida + 0.02, h)))
        datos["caras"].append(len(esquinas))
        datos["puntos"] += [round(v, 2) for xy in esquinas for v in xy]
        datos["z"] += [round(h, 2) for h in alturas]
        formas.append(placa)
    return datos, formas
