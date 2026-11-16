"""El trazado de la red de vías del ferrocarril: los desvíos y las curvas de enlace.

Cada vía de datos.VIAS es un cuerpo (sus puntos, con las esquinas redondeadas) y, en cada
punta, cómo se une a su vía madre: con un desvío. Un desvío sale tangente a la madre en la
aguja, gira con el radio de sus agujas hasta el ángulo de su marca (1/9 o 1/6) y sigue
recto hasta que las dos vías van cada una por su lado; desde ahí, una curva lleva la vía
hasta su cuerpo (con un tramo recto antes si hace falta: así se hacen también las vías que
salen y vuelven en paralelo, como las de los andenes). Las agujas van siempre en tramos
rectos de la madre y los desvíos seguidos no se pisan.

red() deja en datos.VIAS el trazado final de cada vía (el del plano queda en "diseno"),
pone los vagones de la playa de vías en lo recto de sus vías y calcula los topes de las
puntas sueltas. detalles() da, con las rasantes ya hechas, lo que la maqueta necesita para
levantar cada desvío (corazón, agujas, contracarriles, traviesas de madera y la palanca)
y los topes.
"""

from __future__ import annotations

import math

import numpy as np
from shapely.geometry import LineString, Point

import datos as D
import relieve as R
from geo import ALTO, ANCHO

# Desvíos: ángulo del corazón, radio de la curva de las agujas, largo por la vía desviada
# hasta donde cada vía va por su lado (ahí acaban las traviesas largas) y largo de las
# agujas. El 1/9 es el de la línea; el 1/6, el de los apartaderos y la playa.
DESVIOS = {
    "1/9": {"angulo": math.atan(1.0 / 9.0), "radio": 150.0, "largo": 27.5, "agujas": 8.0},
    "1/6": {"angulo": math.atan(1.0 / 6.0), "radio": 100.0, "largo": 21.0, "agujas": 6.0},
}
# Radio de las curvas donde quiebra el cuerpo de cada clase de vía.
RADIO_CURVAS = {"principal": 300.0, "secundaria": 150.0, "playa": 120.0}
# Medio ancho de vía hasta el eje de cada carril y ancho de la cabeza del carril (como en
# la maqueta: TransitRails).
CARRIL_EJE = 0.7975
CABEZA = 0.075
# Del eje del contracarril al del carril, y lo que mide.
CONTRACARRIL = 0.12
LARGO_CONTRACARRIL = 4.4
# El corazón: lo que ocupa antes y después del punto matemático (el modelo corazon_*).
CORAZON = (2.0, 2.5)
# Traviesas de madera de los desvíos: cada cuánto y su largo sin desvío; junto a la aguja,
# las dos primeras se alargan por el lado de la palanca.
PASO_TRAVIESA = 0.55
LARGO_TRAVIESA = 2.7
PALANCA = {"en": 0.6, "lado": 2.15, "alargue": 1.5}
# El tope ocupa los últimos metros de la vía.
LARGO_TOPE = 3.0
# Vagones de la playa: largo, separación entre ejes de vagón y margen en las puntas.
VAGON = {"largo": 14.0, "paso": 15.5, "margen": 9.0, "probabilidad": 0.82}

_RED: dict | None = None


# ---------------------------------------------------------------------------
# Geometría
# ---------------------------------------------------------------------------
def _dir(h: float) -> np.ndarray:
    return np.array([math.cos(h), math.sin(h)])


def _cruz(a, b) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


def _envolver(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _arco(p, h: float, radio: float, giro: float, paso: float = 2.0) -> tuple[list, np.ndarray, float]:
    """Los puntos de un arco que sale de ``p`` con rumbo ``h`` y gira ``giro`` (positivo a
    la izquierda), sin el primero; el último y el rumbo final."""
    p = np.asarray(p, float)
    n = max(1, int(math.ceil(radio * abs(giro) / paso)))
    lado = 1.0 if giro > 0.0 else -1.0
    centro = p + radio * lado * np.array([-math.sin(h), math.cos(h)])
    puntos = []
    for i in range(1, n + 1):
        hi = h + giro * i / n
        puntos.append(centro + radio * lado * np.array([math.sin(hi), -math.cos(hi)]))
    return puntos, puntos[-1], h + giro


def redondear(puntos, radio: float, tramo_minimo: float = 0.0) -> list[tuple[float, float]]:
    """Una polilínea con las esquinas redondeadas: un arco de ``radio`` en cada una (más
    cerrado donde los tramos no dan para tanto; cada tramo se reparte a prorrata entre
    las curvas de sus dos puntas). Los tramos de menos de ``tramo_minimo`` se funden en
    una sola esquina."""
    pts = [np.asarray(p, float) for p in puntos]
    k = 1
    while k < len(pts) and len(pts) > 2:
        if np.linalg.norm(pts[k] - pts[k - 1]) >= tramo_minimo:
            k += 1
        elif k == 1:
            del pts[1]
        elif k == len(pts) - 1:
            del pts[k - 1]
        else:
            pts[k - 1] = (pts[k - 1] + pts[k]) / 2.0
            del pts[k]
    n = len(pts)
    if n < 3:
        return [tuple(map(float, p)) for p in pts]
    largos = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(n - 1)]
    rumbos = [(pts[i + 1] - pts[i]) / largos[i] for i in range(n - 1)]
    giros = [0.0] * n
    tangentes = [0.0] * n
    for i in range(1, n - 1):
        giros[i] = _envolver(math.atan2(rumbos[i][1], rumbos[i][0]) - math.atan2(rumbos[i - 1][1], rumbos[i - 1][0]))
        tangentes[i] = radio * math.tan(abs(giros[i]) / 2.0)
    limitadas = list(tangentes)
    for i in range(n - 1):
        suma = tangentes[i] + tangentes[i + 1]
        if suma > largos[i]:
            for j in (i, i + 1):
                limitadas[j] = min(limitadas[j], largos[i] * tangentes[j] / suma)
    resultado = [tuple(map(float, pts[0]))]
    for i in range(1, n - 1):
        if abs(giros[i]) < 1e-4 or limitadas[i] < 1e-3:
            resultado.append(tuple(map(float, pts[i])))
            continue
        r = limitadas[i] / math.tan(abs(giros[i]) / 2.0)
        inicio = pts[i] - rumbos[i - 1] * limitadas[i]
        h = math.atan2(rumbos[i - 1][1], rumbos[i - 1][0])
        resultado.append(tuple(map(float, inicio)))
        arco, _, _ = _arco(inicio, h, r, giros[i])
        resultado += [tuple(map(float, q)) for q in arco]
    resultado.append(tuple(map(float, pts[-1])))
    return resultado


def _rama(s_punto, h: float, lado: int, marca: dict) -> tuple[list, np.ndarray, float]:
    """La vía desviada de un desvío: de la aguja (sin ella) a su final, y su rumbo."""
    giro = lado * marca["angulo"]
    puntos, fin, rumbo = _arco(s_punto, h, marca["radio"], giro, paso=1.0)
    resto = marca["largo"] - marca["radio"] * marca["angulo"]
    fin = fin + _dir(rumbo) * resto
    return puntos + [fin], fin, rumbo


def _enlace(s_punto, h: float, lado: int, marca: dict, recta: float, radio: float, rumbo_cuerpo: float):
    """De la aguja al cuerpo: el desvío, un tramo recto y la curva hasta el rumbo del cuerpo."""
    puntos = [np.asarray(s_punto, float)]
    rama, fin, rumbo = _rama(s_punto, h, lado, marca)
    puntos += rama
    if recta > 1e-6:
        fin = fin + _dir(rumbo) * recta
        puntos.append(fin)
    giro = _envolver(rumbo_cuerpo - rumbo)
    if abs(giro) > 1e-6:
        arco, fin, _ = _arco(fin, rumbo, radio, giro)
        puntos += arco
    return puntos, fin


def _en_la_linea(linea: LineString, s: float) -> tuple[np.ndarray, float]:
    """Punto y rumbo de una polilínea a ``s`` metros de su principio."""
    s = min(max(s, 0.0), linea.length)
    p = linea.interpolate(s)
    a = linea.interpolate(max(s - 0.05, 0.0))
    b = linea.interpolate(min(s + 0.05, linea.length))
    return np.array([p.x, p.y]), math.atan2(b.y - a.y, b.x - a.x)


def _recta_en(linea: LineString, s: float, largo: float, sentido: int) -> bool:
    """¿Va recta la polilínea de ``s`` a ``s + sentido * largo``?"""
    _, h0 = _en_la_linea(linea, s - sentido * 0.5)
    _, h1 = _en_la_linea(linea, s + sentido * largo)
    return abs(_envolver(h1 - h0)) < math.radians(0.3)


# ---------------------------------------------------------------------------
# La red
# ---------------------------------------------------------------------------
def red() -> dict:
    """Traza la red (una vez): el trazado final de cada vía queda en datos.VIAS."""
    global _RED
    if _RED is not None:
        return _RED
    hechas: dict[str, list] = {}
    desvios = []
    pendientes = list(D.VIAS)
    orden = []
    while pendientes:
        avance = False
        for via in list(pendientes):
            madres = [c["via"] for c in (via.get("desde"), via.get("hasta")) if c]
            if all(m in hechas for m in madres):
                hechas[via["id"]], nuevos = _trazar(via, hechas)
                desvios += nuevos
                orden.append(via["id"])
                pendientes.remove(via)
                avance = True
        if not avance:
            raise ValueError(f"Vías sin madre trazada: {[v['id'] for v in pendientes]}")
    _comprobar_desvios(desvios, hechas)
    for via in D.VIAS:
        via["diseno"] = via["puntos"]
        via["puntos"] = [(round(x, 3), round(y, 3)) for x, y in hechas[via["id"]]]
    _RED = {"orden": orden, "desvios": desvios, "topes": _topes()}
    _vagones_playa()
    return _RED


def _trazar(via: dict, hechas: dict) -> tuple[list, list]:
    radio = via.get("radio", RADIO_CURVAS[via["tipo"]])
    cuerpo = [np.asarray(p, float) for p in redondear(via["puntos"], radio)]
    desvios = []
    if "desde" in via:
        camino, desvio = _conectar(via, via["desde"], cuerpo, hechas, True)
        cuerpo = camino + cuerpo[1:]
        desvios.append(desvio)
    if "hasta" in via:
        camino, desvio = _conectar(via, via["hasta"], cuerpo, hechas, False)
        cuerpo = cuerpo[:-1] + list(reversed(camino))
        desvios.append(desvio)
    return [tuple(map(float, p)) for p in cuerpo], desvios


def _conectar(via: dict, union: dict, cuerpo: list, hechas: dict, al_principio: bool) -> tuple[list, dict]:
    """El camino de la aguja al cuerpo (que acaba en su primer o su último tramo) y el
    desvío. El cuerpo se recorta o se alarga hasta donde llega el camino."""
    madre = LineString(hechas[union["via"]])
    marca = DESVIOS[union["marca"]]
    radio = union.get("radio", RADIO_CURVAS[via["tipo"]])
    b0, b1 = (cuerpo[0], cuerpo[1]) if al_principio else (cuerpo[-1], cuerpo[-2])
    recta_cuerpo = b1 - b0
    largo_cuerpo = float(np.linalg.norm(recta_cuerpo))
    rumbo_cuerpo = math.atan2(recta_cuerpo[1], recta_cuerpo[0])
    sentido_cuerpo = recta_cuerpo / largo_cuerpo

    def pose(s: float) -> tuple[np.ndarray, float, int]:
        punto, h = _en_la_linea(madre, s)
        if float(np.dot(_dir(h), b0 - punto)) < 0.0:
            h += math.pi
        lado = 1 if _cruz(_dir(h), b0 - punto) > 0.0 else -1
        return punto, h, lado

    def fuera(s: float, recta: float) -> float:
        punto, h, lado = pose(s)
        _, fin = _enlace(punto, h, lado, marca, recta, radio, rumbo_cuerpo)
        return _cruz(sentido_cuerpo, fin - b0)

    if "x" in union or "en" in union:
        if "en" in union:
            s = madre.project(Point(union["en"]))
        else:
            corte = madre.intersection(LineString([(union["x"], -1e4), (union["x"], 1e4)]))
            s = madre.project(corte if corte.geom_type == "Point" else corte.geoms[0])
        f0, f1 = fuera(s, 0.0), fuera(s, 1.0)
        recta = -f0 / (f1 - f0)
        if recta < -1e-6:
            raise ValueError(f"{via['id']}: la aguja está demasiado cerca del cuerpo (recta {recta:.1f} m)")
        recta = max(recta, 0.0)
    else:
        s = _buscar_aguja(madre, union, fuera, pose, marca, b0)
        recta = 0.0
    punto, h, lado = pose(s)
    sentido = _sentido(madre, s, h)
    if not _recta_en(madre, s, marca["largo"], sentido):
        raise ValueError(f"{via['id']}: la aguja de su desvío cae en una curva de {union['via']}")
    camino, fin = _enlace(punto, h, lado, marca, recta, radio, rumbo_cuerpo)
    if float(np.dot(fin - b0, sentido_cuerpo)) > largo_cuerpo - 0.5:
        raise ValueError(f"{via['id']}: la curva de enlace se pasa del primer tramo del cuerpo")
    desvio = {
        "via": union["via"], "rama": via["id"], "marca": union["marca"], "aguja": tuple(map(float, punto)),
        "rumbo": h, "lado": lado, "s": s, "al_principio": al_principio,
    }
    return camino, desvio


def _buscar_aguja(madre: LineString, union: dict, fuera, pose, marca: dict, b0) -> float:
    """Dónde poner la aguja (sin tramo recto) para que la curva acabe en el cuerpo: se
    recorre la madre por sus tramos rectos y, si hay varias, la más cercana al cuerpo."""
    x0, x1 = union.get("entre", (-1e9, 1e9))
    raices = []
    anterior = None
    for s in np.arange(0.0, madre.length, 1.0):
        punto, h, _ = pose(float(s))
        if not (x0 <= punto[0] <= x1) or not _recta_en(madre, float(s), marca["largo"], _sentido(madre, float(s), h)):
            anterior = None
            continue
        valor = fuera(float(s), 0.0)
        # Solo cuenta un cambio de signo sin salto: con la misma orientación del desvío a
        # los dos lados (si no, es la aguja dándose la vuelta, no una raíz).
        mismo = anterior is not None and _misma_pose(pose(anterior[0]), pose(float(s)))
        if mismo and (anterior[1] > 0.0) != (valor > 0.0):
            a, b = anterior[0], float(s)
            fa = anterior[1]
            for _ in range(60):
                m = (a + b) / 2.0
                fm = fuera(m, 0.0)
                if (fa > 0.0) == (fm > 0.0):
                    a, fa = m, fm
                else:
                    b = m
            if abs(fuera((a + b) / 2.0, 0.0)) < 0.01:
                raices.append((a + b) / 2.0)
        anterior = (float(s), valor)
    if not raices:
        raise ValueError(f"No hay dónde poner la aguja en {union['via']}")
    return min(raices, key=lambda s: float(np.linalg.norm(pose(s)[0] - b0)))


def _misma_pose(a: tuple, b: tuple) -> bool:
    return a[2] == b[2] and abs(_envolver(a[1] - b[1])) < 0.5


def _comprobar_desvios(desvios: list, hechas: dict) -> None:
    """Dos desvíos en la misma vía no se pisan."""
    for madre in {d["via"] for d in desvios}:
        tramos = []
        for d in desvios:
            if d["via"] == madre:
                sentido = _sentido(LineString(hechas[madre]), d["s"], d["rumbo"])
                largo = DESVIOS[d["marca"]]["largo"]
                tramos.append((min(d["s"], d["s"] + sentido * largo), max(d["s"], d["s"] + sentido * largo), d["rama"]))
        tramos.sort()
        for a, b in zip(tramos, tramos[1:]):
            if b[0] < a[1] - 0.05:
                raise ValueError(f"Los desvíos de {a[2]} y {b[2]} se pisan en {madre}")


# ---------------------------------------------------------------------------
# Topes y vagones
# ---------------------------------------------------------------------------
def _topes() -> list[dict]:
    """Un tope en cada punta suelta de vía: las que no salen de un desvío, no se van del
    mapa ni acaban en el cráter."""
    resultado = []
    radio_crater = R.CRATER_RADIO + 15.0
    for via in D.VIAS:
        puntos = via["puntos"]
        for al_principio, union in ((True, via.get("desde")), (False, via.get("hasta"))):
            if union is not None:
                continue
            fin = np.asarray(puntos[0] if al_principio else puntos[-1], float)
            antes = np.asarray(puntos[1] if al_principio else puntos[-2], float)
            if not (0.0 <= fin[0] <= ANCHO and 0.0 <= fin[1] <= ALTO):
                continue
            if math.dist(fin, R.CRATER) < radio_crater:
                continue
            fuera = (fin - antes) / float(np.linalg.norm(fin - antes))
            resultado.append({"via": via["id"], "fin": tuple(map(float, fin)),
                              "rumbo": math.atan2(fuera[1], fuera[0])})
    return resultado


def _vagones_playa() -> None:
    """Los vagones abandonados de la playa: en fila por lo recto de cada vía, con huecos."""
    for k, y in enumerate(D.VAGONES_PLAYA):
        recto = []
        for via in D.VIAS:
            if via["tipo"] != "playa":
                continue
            xs = [x for x, yy in via["puntos"] if abs(yy - y) < 0.01]
            if len(xs) >= 2:
                recto = [min(xs), max(xs)]
                if via["id"] in {t["via"] for t in _RED["topes"]}:
                    recto[1] -= LARGO_TOPE
                break
        if not recto:
            raise ValueError(f"No hay vía de playa recta a y = {y}")
        x = recto[0] + VAGON["margen"] + D.azar(f"playa/{k}") * VAGON["paso"]
        while x < recto[1] - VAGON["margen"]:
            if D.azar(f"playa/{k}/{x:.0f}") < VAGON["probabilidad"]:
                D.vehiculo("vagon", x, y, 0.0, "abandonado")
            x += VAGON["paso"]


# ---------------------------------------------------------------------------
# Lo que necesita la maqueta
# ---------------------------------------------------------------------------
def detalles(perfiles: dict, z_en, carril: float) -> dict:
    """Con las rasantes hechas: cada desvío en 3D (corazón, agujas, contracarriles,
    traviesas de madera y palanca), los topes, y por vía los tramos de carril que no se
    dibujan (los ponen las agujas y el corazón) y los que van sin traviesas."""
    datos = red()
    huecos: dict[str, list] = {}
    sin_traviesas: dict[str, list] = {}
    desvios = []
    for d in datos["desvios"]:
        desvios.append(_desvio_3d(d, perfiles, z_en, carril, huecos, sin_traviesas))
    topes = []
    for t in datos["topes"]:
        fin = np.asarray(t["fin"])
        origen = fin - _dir(t["rumbo"]) * LARGO_TOPE
        z = float(z_en(perfiles[t["via"]], [tuple(origen)])[0]) + carril
        topes.append({"pos": _r(origen), "z": round(z, 3), "rumbo": round(math.degrees(t["rumbo"]), 3)})
    return {"desvios": desvios, "topes": topes, "huecos": huecos, "sin_traviesas": sin_traviesas}


def _r(p) -> list[float]:
    return [round(float(c), 3) for c in p]


def _sentido(linea: LineString, s: float, h: float) -> int:
    return 1 if math.cos(_envolver(h - _en_la_linea(linea, s)[1])) > 0.0 else -1


def _carril(lado_en_la_via: int) -> int:
    """El carril de una vía: 0 el de la izquierda (en su sentido), 1 el de la derecha."""
    return 0 if lado_en_la_via > 0 else 1


def _tramo(s: float, sentido: int, desde: float, hasta: float) -> list[float]:
    a, b = s + sentido * desde, s + sentido * hasta
    return [round(min(a, b), 3), round(max(a, b), 3)]


def _desvio_3d(d: dict, perfiles: dict, z_en, carril: float, huecos: dict, sin_traviesas: dict) -> dict:
    marca = DESVIOS[d["marca"]]
    madre = LineString(perfiles[d["via"]]["puntos"])
    rama = LineString(perfiles[d["rama"]]["puntos"])
    aguja = np.asarray(d["aguja"])
    h, lado = d["rumbo"], d["lado"]
    adelante = _dir(h)
    izquierda = np.array([-adelante[1], adelante[0]])
    s_madre = madre.project(Point(aguja))
    s_rama = rama.project(Point(aguja))
    sentido_madre = _sentido(madre, s_madre, h)
    sentido_rama = 1 if d["al_principio"] else -1
    perfil_madre = perfiles[d["via"]]

    def z(punto) -> float:
        return float(z_en(perfil_madre, [tuple(punto)])[0])

    def desviada(u: float) -> np.ndarray:
        """El eje de la vía desviada a ``u`` metros de la aguja (por ella)."""
        q = rama.interpolate(min(max(s_rama + sentido_rama * u, 0.0), rama.length))
        return np.array([q.x, q.y])

    def normal_rama(u: float) -> np.ndarray:
        """La normal izquierda de la vía desviada (en el sentido del desvío) a ``u`` metros."""
        _, rumbo = _en_la_linea(rama, min(max(s_rama + sentido_rama * u, 0.0), rama.length))
        if sentido_rama < 0:
            rumbo += math.pi
        return np.array([-math.sin(rumbo), math.cos(rumbo)])

    def separacion(u: float) -> float:
        punto = aguja + adelante * u
        return float(np.dot(desviada_en_la_madre(u) - punto, izquierda)) * lado

    def desviada_en_la_madre(u: float) -> np.ndarray:
        """Donde corta la vía desviada la perpendicular a la madre a ``u`` metros."""
        punto = aguja + adelante * u
        corte = rama.intersection(LineString([punto - izquierda * 8.0, punto + izquierda * 8.0]))
        if corte.is_empty:
            return punto
        puntos = [corte] if corte.geom_type == "Point" else list(getattr(corte, "geoms", []))
        mejor = min(puntos, key=lambda q: abs(rama.project(q) - (s_rama + sentido_rama * u)))
        return np.array([mejor.x, mejor.y])

    # El punto matemático del corazón: donde se cruzan el carril de la madre del lado del
    # desvío y el carril de la desviada del otro lado.
    u_corazon = None
    anterior = None
    for u in np.arange(0.0, marca["largo"] + 5.0, 0.05):
        valor = separacion(float(u)) - 2.0 * CARRIL_EJE
        if anterior is not None and anterior[1] < 0.0 <= valor:
            u_corazon = anterior[0] + (float(u) - anterior[0]) * (-anterior[1]) / (valor - anterior[1])
            break
        anterior = (float(u), valor)
    if u_corazon is None:
        raise ValueError(f"Desvío de {d['rama']}: no se encuentra el corazón")
    punto_corazon = aguja + adelante * u_corazon + izquierda * lado * CARRIL_EJE
    rumbo_corazon = h + lado * marca["angulo"] / 2.0
    s_corazon_rama = rama.project(Point(punto_corazon))

    # Carriles que no se dibujan: las agujas y el corazón.
    hueco_madre = huecos.setdefault(d["via"], [])
    hueco_rama = huecos.setdefault(d["rama"], [])
    carril_madre_desvio = _carril(lado * sentido_madre)
    carril_rama_opuesto = _carril(-lado * sentido_rama)
    hueco_madre.append([carril_madre_desvio, *_tramo(s_madre, sentido_madre, 0.0, marca["agujas"])])
    hueco_madre.append([carril_madre_desvio, *_tramo(s_madre, sentido_madre, u_corazon - CORAZON[0],
                                                     u_corazon + CORAZON[1])])
    hueco_rama.append([carril_rama_opuesto, *_tramo(s_rama, sentido_rama, 0.0, marca["agujas"])])
    u_rama = abs(s_corazon_rama - s_rama)
    hueco_rama.append([carril_rama_opuesto, *_tramo(s_rama, sentido_rama, u_rama - CORAZON[0], u_rama + CORAZON[1])])
    sin_traviesas.setdefault(d["via"], []).append(_tramo(s_madre, sentido_madre, -0.6, marca["largo"] + 0.3))
    sin_traviesas.setdefault(d["rama"], []).append(_tramo(s_rama, sentido_rama, 0.0, marca["largo"] + 0.3))

    # Las agujas: la recta (el carril de la madre del lado del desvío) y la curva (el de
    # la desviada del otro lado), afiladas en la punta y pegadas a su contraaguja.
    agujas = []
    for propia in (True, False):
        puntos = []
        for u in np.linspace(0.0, marca["agujas"], 13):
            f = float(u) / marca["agujas"]
            escala = 0.25 + 0.75 * f
            sep = separacion(float(u))
            empuje = max(0.0, CABEZA * (1.0 + escala) / 2.0 - sep)
            if propia:
                centro = aguja + adelante * float(u) + izquierda * lado * (CARRIL_EJE - empuje)
            else:
                eje = desviada_en_la_madre(float(u))
                centro = eje - normal_rama(float(u)) * lado * (CARRIL_EJE - empuje)
            puntos.append([*_r(centro), round(z(centro) + carril - 0.006 * (1.0 - f), 3), round(escala, 3)])
        agujas.append(puntos)

    # Los contracarriles: frente al corazón, por dentro del carril de cada vía que no se
    # corta, con las puntas abiertas.
    contracarriles = []
    for en_la_madre in (True, False):
        puntos = []
        for u in np.linspace(u_corazon - LARGO_CONTRACARRIL / 2.0, u_corazon + LARGO_CONTRACARRIL / 2.0, 9):
            punta = min(abs(float(u) - (u_corazon - LARGO_CONTRACARRIL / 2.0)),
                        abs(float(u) - (u_corazon + LARGO_CONTRACARRIL / 2.0)))
            abre = 0.03 * max(0.0, 1.0 - punta / 0.6)
            if en_la_madre:
                centro = aguja + adelante * float(u) - izquierda * lado * (CARRIL_EJE - CONTRACARRIL - abre)
            else:
                eje = desviada_en_la_madre(float(u))
                centro = eje + normal_rama(float(u)) * lado * (CARRIL_EJE - CONTRACARRIL - abre)
            puntos.append([*_r(centro), round(z(centro) + carril, 3)])
        contracarriles.append(puntos)

    # Las traviesas de madera, de la aguja al final del desvío, cada vez más largas.
    maderas = []
    u = -0.4
    while u <= marca["largo"]:
        punto = aguja + adelante * u
        sep = max(0.0, separacion(max(u, 0.0)))
        largo = LARGO_TRAVIESA + sep
        centro = punto + izquierda * lado * sep / 2.0
        if u < PALANCA["en"] + 0.6:
            largo += PALANCA["alargue"]
            centro = centro - izquierda * lado * PALANCA["alargue"] / 2.0
        maderas.append([*_r(centro), round(z(centro) + carril - 0.15, 3), round(largo, 3)])
        u += PASO_TRAVIESA
    palanca = aguja + adelante * PALANCA["en"] - izquierda * lado * PALANCA["lado"]
    return {
        "via": d["via"], "rama": d["rama"], "marca": d["marca"],
        "rumbo": round(math.degrees(h), 3), "lado": lado,
        "corazon": {"pos": _r(punto_corazon), "z": round(z(punto_corazon) + carril, 3),
                    "rumbo": round(math.degrees(rumbo_corazon), 3)},
        "agujas": agujas, "contracarriles": contracarriles, "maderas": maderas,
        "palanca": {"pos": _r(palanca), "z": round(z(palanca) + carril - 0.15, 3)},
    }
