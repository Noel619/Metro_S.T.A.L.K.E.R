"""La red de tránsito de Tumansk: todo lo que se pisa para ir de un sitio a otro.

Calzadas, aceras, bordillos, plazas, isletas, alcorques, pasos de cebra, calles peatonales,
el camino del barranco, las sendas, el tablero del puente del Progreso, la Escalinata y las
escaleras de las sendas. Este módulo decide la forma en planta (con las mismas figuras de
shapely que valida el plano) y las alturas, y lo exporta a data/ciudad/transito.json; la
maqueta levanta con eso los modelos 3D (scripts/surface/city_transit.gd).

El suelo se reparte en GRUPOS: trozos de una clase de superficie (calzada, losas, peldaño…)
con una REGLA que da su altura y la orientación de su textura. Las reglas son:

- terreno: la rasante de tránsito (el terreno nivelado, sin escombros, con los muelles
  rellenos hasta el borde del agua) más el nivel de la clase. Es casi todo.
- plano: una altura fija o un plano inclinado (los peldaños, los rellanos).
- rampa: sube de una cota a otra a lo largo de una dirección (el tablero del puente).
- malla: la altura de cada vértice de su propia malla (los socavones, deterioro.py).

Niveles respecto a la rasante: lo peatonal (aceras, plazas, paseos, isletas) 3 cm por
encima; la calzada, un bordillo (15 cm) por debajo de la acera; las sendas, 5 cm por
encima, con un bordillo bajo; el camino de tierra, un poco hundido.

Entre los grupos y entre un grupo y el terreno están las ARISTAS, ya clasificadas:
bordillos (con las piezas que faltan), bordes, contrahuellas, escalones, muros de
contención, pretiles (el muelle, el puente, los rellanos en alto), roturas (los bordes del
vano hundido), derrumbes (el corte de la calle en el borde de un socavón) y bordes de
alcorque. Encima, las marcas viales, los detalles (tapas, sumideros) y el deterioro de
deterioro.py: grietas, baches, tapas abiertas, bordillos sueltos y matojos.
La maqueta no dibuja el terreno donde hay tránsito: lo recorta exacto y cierra el hueco
entre el borde del tránsito y el terreno con la cara de la arista.

Coordenadas del plano (x al este, y al norte), en metros.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import linemerge, unary_union

import datos as D
from geo import ALTO, ANCHO, a_eje, banda, circulo, eje

# ---------------------------------------------------------------------------
# Medidas
# ---------------------------------------------------------------------------
NIVEL_PEATON = 0.03
BORDILLO = 0.15
NIVEL_CALZADA = NIVEL_PEATON - BORDILLO
NIVEL_SENDA = 0.05
NIVEL_CAMINO = -0.03
NIVEL_ALCORQUE = -0.05
# Cuánto se rebaja como mínimo el terreno (y su colisión) bajo el tránsito.
REBAJE = 0.30
# Radio de las esquinas de los bordillos en los cruces.
RADIO_ESQUINA = 6.0
# Ancho de las sendas de los parques y de sus escaleras.
ANCHO_SENDA = 2.5
ANCHO_ESCALERA_SENDA = 3.0
# Arcén elevado a cada lado de los pasos de servicio (bordillo y un palmo de acera).
ARCEN_SERVICIO = 1.0
# Lo que se sale el tránsito por los bordes del mapa (las calles siguen en la niebla).
MARGEN_MAPA = 40.0
# Lado de los alcorques de los árboles de las aceras.
LADO_ALCORQUE = 1.2
# Ancho de la losa de los pasos a nivel (centrada en la vía, de lado a lado de la calle).
ANCHO_PASO_NIVEL = 6.0
# Ancho de la cama de cada vía del tranvía donde pisa algo peatonal (centrada en la vía).
ANCHO_CAMA_TRANVIA = 3.2
# Decimales de las coordenadas exportadas (milímetros).
DECIMALES = 3

# Clases de superficie: a qué nivel van respecto a su regla y si son calzada.
CLASES = {
    "calzada": {"nivel": NIVEL_CALZADA, "rodada": True},
    "adoquin": {"nivel": NIVEL_CALZADA, "rodada": True},
    "acera": {"nivel": NIVEL_PEATON, "rodada": False},
    "losas": {"nivel": NIVEL_PEATON, "rodada": False},
    "plaza": {"nivel": NIVEL_PEATON, "rodada": False},
    "paseo": {"nivel": NIVEL_PEATON, "rodada": False},
    "isleta": {"nivel": NIVEL_PEATON, "rodada": False},
    "alcorque": {"nivel": NIVEL_ALCORQUE, "rodada": False},
    "senda": {"nivel": NIVEL_SENDA, "rodada": False},
    "camino": {"nivel": NIVEL_CAMINO, "rodada": False},
    # Los peldaños y los rellanos de las escaleras: su regla ya da la altura de la pisada.
    "peldano": {"nivel": 0.0, "rodada": False},
    # Los andenes de la estación (y sus rampas): su regla da la altura.
    "anden": {"nivel": 0.0, "rodada": False},
    # La losa de hormigón de los pasos a nivel: a ras del carril, como la calzada.
    "paso_nivel": {"nivel": NIVEL_CALZADA, "rodada": True},
    # La cama del tranvía donde deja la calzada (la mediana de la Avenida, la Plaza): losas
    # de hormigón a la altura de la calzada, con los carriles a ras.
    "via_tranvia": {"nivel": NIVEL_CALZADA, "rodada": True},
    # El hueco de un socavón (deterioro.py): su regla es su malla (la altura de cada vértice).
    "socavon": {"nivel": 0.0, "rodada": False},
    # La base de un firme roto (firmes.py: grava y tierra entre las placas), con su malla.
    "firme": {"nivel": 0.0, "rodada": False},
}
# Las clases que son un hueco en la calle con su propia malla: su borde es un derrumbe.
CLASES_HUECO = ("socavon", "firme")
PEATONALES = ("acera", "losas", "plaza", "paseo", "isleta")
# Aceras de losas en el centro (la Plaza, la Avenida y el Centro); de asfalto en el resto.
ZONAS_LOSAS = (1, 3, 7)
# Calles empedradas: la ciudad vieja.
CALLES_ADOQUIN = ("fortaleza", "mercaderes", "pozo")
# Calles de la falda de la loma: se nivelan de lado a lado.
CALLES_NIVELADAS = ("muelle_norte", "paseo_parque", "bajada", "bulevar_rio")


# ---------------------------------------------------------------------------
# Utilidades de geometría
# ---------------------------------------------------------------------------
def poligonos(geom) -> list[Polygon]:
    """Los polígonos de cualquier geometría (vacía, simple o colección)."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if hasattr(geom, "geoms"):
        return [g for parte in geom.geoms for g in poligonos(parte)]
    return []


def lineas(geom) -> list[LineString]:
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [geom]
    if geom.geom_type == "LinearRing":
        return [LineString(geom.coords)]
    if hasattr(geom, "geoms"):
        return [g for parte in geom.geoms for g in lineas(parte)]
    return []


def limpiar(geom, minimo: float = 0.5):
    """Quita astillas (tiras de menos de 10 cm) y trozos de menos de `minimo` m²."""
    geom = geom.buffer(-0.05, join_style=2).buffer(0.05, join_style=2)
    return unary_union([p for p in poligonos(geom) if p.area >= minimo])


def redondear_esquinas(geom, radio: float):
    """Cierre morfológico: rellena las esquinas entrantes con un arco (las esquinas de los
    bordillos en los cruces) sin tocar las salientes."""
    return geom.buffer(radio, join_style=1, quad_segs=8).buffer(-radio, join_style=1, quad_segs=8)


def rect_eje(s0: float, s1: float, t0: float, t1: float) -> Polygon:
    return Polygon([eje(s0, t0), eje(s1, t0), eje(s1, t1), eje(s0, t1)])


def angulo_de(a, b) -> float:
    """Dirección de a hacia b, en grados desde el este."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def azar(clave: str) -> float:
    """Número fijo entre 0 y 1 para cada clave (el mismo que plano.azar)."""
    import hashlib

    return int(hashlib.md5(clave.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Calles
# ---------------------------------------------------------------------------
def anchos(calle: dict) -> tuple[float, float]:
    """Ancho de la calzada y de cada acera (de fachada a fachada es `ancho`)."""
    ancho = calle["ancho"]
    tipo = calle["tipo"]
    if tipo == "servicio":
        return ancho - 2 * ARCEN_SERVICIO, ARCEN_SERVICIO
    if tipo == "puente":
        return 21.0, (ancho - 21.0) / 2
    if "calzada" in calle:
        return calle["calzada"], (ancho - calle["calzada"]) / 2
    acera = min(5.0, max(2.0, round(ancho * 0.2, 1)))
    return ancho - 2 * acera, acera


@dataclass
class Grupo:
    """Un trozo de suelo de una clase, con su regla de altura y la orientación de la
    textura (grados desde el este). Los grupos elevados (el tablero del puente) van por el
    aire: no recortan el terreno."""

    clase: str
    forma: object
    regla: dict
    angulo: float = 0.0
    elevado: bool = False
    # La malla de un socavón (deterioro.Malla): sus triángulos van tal cual a transito.json.
    malla: object = None


@dataclass
class Arista:
    """Una línea entre dos grupos o entre un grupo y el terreno: `izq` queda a la izquierda
    según se recorre y `der` a la derecha (-1 si es terreno)."""

    puntos: list
    tipo: str
    izq: int
    der: int
    # Los tramos (de, a: metros desde el principio) en los que falta el bordillo, y los de
    # las piezas movidas (de, a, lo que sube cada punta, lo que se sale hacia la calzada).
    huecos: list = field(default_factory=list)
    movidos: list = field(default_factory=list)


@dataclass
class Trazado:
    """La red de tránsito: primero en planta (clases) y después en grupos y aristas."""

    superficies: dict = field(default_factory=dict)  # clase -> (Multi)Polygon
    calles: dict = field(default_factory=dict)  # id -> {"calle", "entera", "calzada", "eje"}
    zona_escalinata: object = None
    escaleras_sendas: list = field(default_factory=list)  # [{"nombre", "puntos", "huella"}]
    alcorques: list = field(default_factory=list)  # [{"pos", "angulo", "forma"}]
    grupos: list = field(default_factory=list)
    aristas: list = field(default_factory=list)
    muros: list = field(default_factory=list)
    barandillas: list = field(default_factory=list)
    socavones: list = field(default_factory=list)  # [{"socavon", "grupo", "piezas"}]
    firmes: list = field(default_factory=list)  # firmes.Zona
    placas: list = field(default_factory=list)  # por zona: {"clase", "grosor", "caras", "puntos", "z"}
    formas_placas: list = field(default_factory=list)  # Polygon de cada placa
    grietas: list = field(default_factory=list)  # [{"puntos", "ancho", "clase"}]
    escaleras: list = field(default_factory=list)
    marcas: dict = field(default_factory=dict)
    detalles: dict = field(default_factory=dict)
    puente: dict = field(default_factory=dict)
    tendido: dict = field(default_factory=dict)  # {"lineas": [{"grosor", "puntos"}], "cifras"}


def _calles_rodadas() -> list[dict]:
    """Las calles con calzada (también el puente)."""
    return [c for c in D.CALLES if c["tipo"] in ("avenida", "principal", "calle", "servicio", "puente")]


def _pie_terraplenes():
    """La huella de los terraplenes del ferrocarril: las calles se cortan al pie."""
    return unary_union([banda(t["puntos"], t["corona"] + 2 * t["talud"]) for t in D.TERRAPLENES])


def _mapa():
    return box(-MARGEN_MAPA, -MARGEN_MAPA, ANCHO + MARGEN_MAPA, ALTO + MARGEN_MAPA)


def _calle(ident: str) -> dict:
    return next(c for c in D.CALLES if c["id"] == ident)


def trazar_calles(t: Trazado) -> None:
    """Banda entera (de fachada a fachada) y calzada de cada calle."""
    mapa = _mapa()
    pie = _pie_terraplenes()
    for c in _calles_rodadas():
        calzada, _ = anchos(c)
        entera = banda(c["puntos"], c["ancho"]).intersection(mapa).difference(pie)
        puntos = c["puntos"]
        if c["id"] == "avenida_progreso":
            # La calzada ancha acaba donde empieza el embudo hacia el puente.
            puntos = [eje(-262.0), eje(FIN_CALZADA_AVENIDA)]
        elif c["id"] == "puente_progreso":
            # Y la del puente, dentro de la del Muelle Norte (no asoma a la acera de enfrente).
            puntos = [eje(372.0), eje(FIN_CALZADA_PUENTE)]
        rodada = banda(puntos, calzada).intersection(mapa).difference(pie)
        t.calles[c["id"]] = {"calle": c, "entera": entera, "calzada": rodada, "eje": LineString(c["puntos"])}


# ---------------------------------------------------------------------------
# Cruces especiales: la glorieta, los estribos del puente y la plaza de la Estación
# ---------------------------------------------------------------------------
CENTRO_GLORIETA = (430.0, 330.0)
FIN_CALZADA_AVENIDA = 344.0
FIN_CALZADA_PUENTE = 622.0
RADIO_ISLETA = 30.0
RADIO_ANILLO = 50.0


def _mediana_avenida() -> Polygon:
    """La mediana de la avenida, con el tranvía: de la plaza de la Estación al puente,
    cortada por la glorieta y rematada en punta redondeada a cada lado."""
    media = _calle("avenida_progreso")["mediana"] / 2
    tramos = []
    for s0, s1 in ((-246.0, -RADIO_ANILLO - 4.0), (RADIO_ANILLO + 4.0, 346.0)):
        cuerpo = rect_eje(s0 + media, s1 - media, -media, media)
        puntas = [circulo(*eje(s0 + media), media, 32), circulo(*eje(s1 - media), media, 32)]
        tramos.append(unary_union([cuerpo, *puntas]))
    return unary_union(tramos)


def calzadas_especiales() -> dict:
    """Las piezas de calzada que no salen de una calle: el anillo de la glorieta, la
    entrada de Mineros a la glorieta, el estrechamiento de la avenida hacia el puente y la
    explanada de autobuses de la estación."""
    anillo = circulo(*CENTRO_GLORIETA, RADIO_ANILLO, 96).difference(circulo(*CENTRO_GLORIETA, RADIO_ISLETA, 96))
    entradas = []
    for c in D.CALLES:
        if c["id"] in ("mineros_oeste", "mineros_este"):
            calzada, _ = anchos(c)
            extremo = c["puntos"][-1] if c["id"] == "mineros_oeste" else c["puntos"][0]
            entradas.append(banda([extremo, CENTRO_GLORIETA], calzada))
    # Del ancho de la avenida (dos calzadas de 19 m) al del puente (21 m), en 36 m.
    media_av = _calle("avenida_progreso")["calzada"] / 2
    media_pu = anchos(_calle("puente_progreso"))[0] / 2
    embudo = Polygon([
        eje(FIN_CALZADA_AVENIDA, -media_av), eje(380.0, -media_pu), eje(380.0, media_pu),
        eje(FIN_CALZADA_AVENIDA, media_av),
    ])
    # La explanada de la estación: autobuses, taxis y el final del tranvía.
    explanada = Polygon([(244.0, 68.0), (304.0, 68.0), (304.0, 140.0), (244.0, 140.0)])
    return {"anillo": anillo, "entradas": unary_union(entradas), "embudo": embudo, "explanada": explanada}


# La Bajada arranca del Muelle Norte en la cabeza del puente y sube por la loma casi en
# paralelo. Mientras comparte la banda del muelle va a su altura (es la boca del cruce) y
# empieza a subir al separarse, así que no hace falta muro entre las dos.
def arranque_bajada(t: Trazado):
    """La parte de la Bajada que va por dentro de la banda del Muelle Norte."""
    return t.calles["bajada"]["entera"].intersection(t.calles["muelle_norte"]["entera"].buffer(2.0))


def _corredor_puente() -> Polygon:
    """Lo que ocupa el puente del Progreso sobre el río (también el vano hundido)."""
    puente = _calle("puente_progreso")
    return banda(puente["puntos"], puente["ancho"])


def _hasta_las_fachadas(pavimento):
    """Cierra los huecos de menos de 2,5 m entre el pavimento y las fachadas cercanas."""
    cerca = pavimento.buffer(3.0)
    fachadas = unary_union([e["huella"] for e in D.EDIFICIOS if e["huella"].intersects(cerca)])
    cerrado = unary_union([pavimento, fachadas]).buffer(1.25, join_style=2).buffer(-1.25, join_style=2)
    return unary_union([pavimento, cerrado.difference(fachadas).intersection(cerca)])


def _hueco_puente() -> Polygon:
    puente = _calle("puente_progreso")
    s0, s1 = puente["vano_hundido"]
    return rect_eje(s0, s1, -puente["ancho"], puente["ancho"])


# ---------------------------------------------------------------------------
# La Escalinata y la plaza del Puente Norte
# ---------------------------------------------------------------------------
# La Escalinata sube por la loma desde la plaza del Puente Norte (a la cota del Muelle
# Norte) hasta su cabeza, donde la cruza el Bulevar del Río, y sigue llana hasta la acera
# de la calle del Mirador. Los tramos van horizontales de lado a lado y la ladera cae de
# través (un 14 %): a un lado la escalera va excavada, con muro de contención, y al otro
# en alto, con muro y pretil. La parte de la plaza del Puente Norte que queda al pie de la
# ladera (entre el muelle, la Bajada y el primer tramo) es el rellano de abajo, a la cota
# del muelle; lo que la plaza tenía ladera arriba, al otro lado de la Bajada, queda en
# tierra.
ESCALINATA_INICIO = 648.0
ESCALINATA_CABEZA = 744.0
ESCALINATA_FIN = 782.0
ESCALINATA_MEDIA = 20.0
# La cota del Muelle Norte en la cabeza del puente.
COTA_MUELLE_NORTE = 1.0


def _rellano_y_tramos(t: Trazado):
    """Lo que ocupa la Escalinata con su rellano de abajo."""
    caja = rect_eje(612.0, ESCALINATA_CABEZA, -ESCALINATA_MEDIA, ESCALINATA_MEDIA)
    fuera = unary_union([t.calles["muelle_norte"]["entera"], t.calles["bajada"]["entera"], D.RIO])
    tramos = rect_eje(ESCALINATA_INICIO, ESCALINATA_CABEZA, -ESCALINATA_MEDIA, ESCALINATA_MEDIA)
    return unary_union([p for p in poligonos(caja.difference(fuera)) if p.intersects(tramos)])


def cabeza_escalinata() -> Polygon:
    """La plaza de la cabeza: de lo alto de la Escalinata a la calle del Mirador."""
    return rect_eje(ESCALINATA_CABEZA, ESCALINATA_FIN, -ESCALINATA_MEDIA, ESCALINATA_MEDIA)


def _ladera_puente_norte(t: Trazado):
    """Lo que la plaza del Puente Norte tenía ladera arriba de la Bajada: queda en tierra."""
    plaza = next(p for p in D.PLAZAS if p["id"] == "puente_norte")["forma"]
    fuera = unary_union([t.calles["muelle_norte"]["entera"], t.calles["bajada"]["entera"], D.RIO])
    resto = plaza.difference(fuera)
    return unary_union([p for p in poligonos(resto) if p.representative_point().y > 795.0])


# ---------------------------------------------------------------------------
# Superficies
# ---------------------------------------------------------------------------
def trazar_superficies(t: Trazado) -> None:
    """Reparte el suelo transitable en clases que no se solapan."""
    mapa = _mapa()
    pie = _pie_terraplenes()
    puente_hueco = _hueco_puente()
    especiales = calzadas_especiales()
    plazas = unary_union([p["forma"] for p in D.PLAZAS] + [cabeza_escalinata()])
    isleta_glorieta = circulo(*CENTRO_GLORIETA, RADIO_ISLETA, 96)
    mediana = _mediana_avenida()

    # Calzada: la de cada calle, más las piezas especiales; esquinas redondeadas. La Bajada
    # arranca del Muelle Norte casi en paralelo pero subiendo: solo se funden en el arranque.
    arranque = arranque_bajada(t)
    bajada = t.calles["bajada"]
    rodadas = [d["calzada"] for i, d in t.calles.items() if i != "bajada"]
    rodadas.append(bajada["calzada"].intersection(arranque))
    calzada = unary_union(rodadas + [especiales["anillo"], especiales["entradas"], especiales["embudo"],
                                     especiales["explanada"]])
    calzada = redondear_esquinas(calzada, RADIO_ESQUINA)
    calzada = unary_union([calzada, redondear_esquinas(bajada["calzada"], RADIO_ESQUINA).difference(arranque)])
    # Las piezas que se tocan se funden (sin rendijas de micras entre ellas).
    calzada = calzada.buffer(0.02, join_style=2).buffer(-0.02, join_style=2)
    calzada = calzada.difference(mediana).difference(isleta_glorieta).difference(puente_hueco)
    calzada = limpiar(calzada.intersection(mapa).difference(pie), 2.0)

    # Todo lo pavimentado: calles de fachada a fachada, plazas y calles peatonales. El
    # pavimento llega hasta las fachadas que quedan a menos de 2,5 m.
    peatonales = [banda(c["puntos"], c["ancho"]) for c in D.CALLES if c["tipo"] == "peatonal"]
    enteras = [d["entera"] for d in t.calles.values()]
    pavimento = unary_union(enteras + peatonales + [plazas, mediana, isleta_glorieta, calzada])
    pavimento = _hasta_las_fachadas(pavimento)
    pavimento = pavimento.difference(D.RIO.difference(_corredor_puente()))
    pavimento = pavimento.difference(puente_hueco).intersection(mapa).difference(pie)
    # La Escalinata (con su rellano de abajo) va aparte; la ladera de la plaza, en tierra.
    t.zona_escalinata = _rellano_y_tramos(t)
    pavimento = pavimento.difference(t.zona_escalinata).difference(_ladera_puente_norte(t))
    junto = t.zona_escalinata.buffer(1.0)
    pavimento = unary_union([p for p in poligonos(pavimento) if p.area > 150 or not p.intersects(junto)])
    calzada = calzada.difference(t.zona_escalinata)

    # Lo peatonal: lo pavimentado que no es calzada, por clases.
    peaton = pavimento.difference(calzada)
    isletas = peaton.intersection(unary_union([mediana, isleta_glorieta]))
    plaza = peaton.intersection(plazas).difference(isletas)
    paseo = peaton.intersection(unary_union(peatonales)).difference(plaza).difference(isletas)
    aceras = peaton.difference(unary_union([isletas, plaza, paseo]))
    centro = unary_union([D.ZONA_POLIGONOS[z] for z in ZONAS_LOSAS]).buffer(1.0)
    losas = aceras.intersection(centro)
    asfalto = aceras.difference(centro)

    # Calzada empedrada en la ciudad vieja (los cruces con calles asfaltadas, asfalto).
    viejas = unary_union([d["entera"] for i, d in t.calles.items() if i in CALLES_ADOQUIN])
    asfaltadas = unary_union([d["calzada"] for i, d in t.calles.items() if i not in CALLES_ADOQUIN])
    adoquin = calzada.intersection(viejas).difference(asfaltadas.buffer(RADIO_ESQUINA * 0.5))
    calzada = calzada.difference(adoquin)

    # Lo que queda suelto al otro lado de un terraplén, pegado al borde del mapa, sobra.
    sueltos = [p for p in poligonos(pavimento) if p.area < 4000 and not p.within(box(0, 0, ANCHO, ALTO))]
    if sueltos:
        fuera = unary_union(sueltos)
        calzada = calzada.difference(fuera)
        isletas, plaza, paseo = (g.difference(fuera) for g in (isletas, plaza, paseo))
        losas, asfalto, adoquin = (g.difference(fuera) for g in (losas, asfalto, adoquin))

    t.superficies = {"calzada": calzada, "adoquin": adoquin, "acera": asfalto, "losas": losas, "plaza": plaza,
                     "paseo": paseo, "isleta": isletas}
    _trazar_sendas_y_camino(t, pavimento)
    _fuera_de_las_vias(t)
    _cama_del_tranvia(t)
    _separar_clases(t)


def _fuera_de_las_vias(t: Trazado) -> None:
    """Nada del tránsito pisa la vía del tren salvo en los pasos a nivel (donde la cruza
    una calzada): lo demás que llega a ella (una esquina de acera, un retal de plaza) se
    recorta a 3 m de su eje, lo que la losa del paso. En el paso, una losa de hormigón a ras
    del carril cruza la calle de lado a lado (las aceras bajan a ella por su bordillo)."""
    import vias as V

    V.red()
    vias = unary_union([banda(v["puntos"], ANCHO_PASO_NIVEL) for v in D.VIAS])
    pasos = vias.intersection(t.superficies["calzada"]).buffer(8.0)
    fuera = vias.difference(pasos)
    for clase, forma in t.superficies.items():
        if clase not in ("calzada", "adoquin"):
            t.superficies[clase] = forma.difference(fuera)
    todo = unary_union(list(t.superficies.values()))
    losas = unary_union([banda(v["puntos"], ANCHO_PASO_NIVEL) for v in D.VIAS])
    losas = limpiar(losas.intersection(pasos).intersection(todo), 1.0)
    for clase in list(t.superficies):
        t.superficies[clase] = t.superficies[clase].difference(losas)
    t.superficies["paso_nivel"] = losas


def _cama_del_tranvia(t: Trazado) -> None:
    """El tranvía va por la calzada, a ras. Donde su vía la deja (la mediana de la Avenida,
    la Plaza, una curva que corta una esquina), una cama de losas a la altura de la calzada
    le abre paso: los carriles siguen a ras y lo de al lado queda tras un bordillo. Nunca
    sobre el río (el vano hundido del puente), la Escalinata ni un edificio."""
    import ferrocarril as F

    vias = [via for _, via in F.ejes_tranvia()]
    cama = unary_union([v.buffer(ANCHO_CAMA_TRANVIA / 2.0, cap_style=2, join_style=2) for v in vias])
    rodado = unary_union([t.superficies[c] for c in ("calzada", "adoquin", "paso_nivel")])
    edificios = unary_union([e["huella"] for e in D.EDIFICIOS])
    cama = cama.intersection(_mapa()).difference(rodado).difference(D.RIO).difference(edificios)
    cama = limpiar(cama.difference(t.zona_escalinata), 1.0)
    for clase in list(t.superficies):
        if clase not in ("calzada", "adoquin", "paso_nivel"):
            t.superficies[clase] = t.superficies[clase].difference(cama)
    t.superficies["via_tranvia"] = cama


def _separar_clases(t: Trazado) -> None:
    """Deja las clases sin astillas y sin solaparse (las rodadas mandan)."""
    ocupado = Polygon()
    for clase in ("paso_nivel", "calzada", "adoquin", "via_tranvia", "isleta", "plaza", "paseo", "losas", "acera",
                  "senda", "camino"):
        forma = t.superficies[clase].difference(ocupado)
        minimo = 1.0 if CLASES[clase]["rodada"] else 0.5
        forma = limpiar(forma, minimo).intersection(forma)
        t.superficies[clase] = unary_union(poligonos(forma))
        ocupado = ocupado.union(t.superficies[clase])


def _trazar_sendas_y_camino(t: Trazado, pavimento) -> None:
    """Las sendas de los parques y el camino de tierra del barranco, cortados donde llegan
    a una calle (se unen a la acera). Las escaleras de las sendas van aparte."""
    mapa = _mapa()
    escaleras = [s for s in D.SENDAS if s["nombre"].startswith("Escaleras")]
    sendas = [banda(s["puntos"], ANCHO_SENDA, puntas="round") for s in D.SENDAS if s not in escaleras]
    t.escaleras_sendas = []
    huellas = []
    for s in escaleras:
        huella = banda(s["puntos"], ANCHO_ESCALERA_SENDA).difference(pavimento)
        huella = max(poligonos(huella), key=lambda p: p.area)
        t.escaleras_sendas.append({"nombre": s["nombre"], "puntos": s["puntos"], "huella": huella})
        huellas.append(huella)
    ocupado = unary_union([pavimento, t.zona_escalinata, *huellas])
    senda = unary_union(sendas).difference(ocupado).difference(D.RIO).intersection(mapa)
    camino = unary_union([banda(c["puntos"], c["ancho"], puntas="round") for c in D.CALLES if c["tipo"] == "camino"])
    camino = camino.difference(ocupado).difference(D.RIO)
    t.superficies["senda"] = senda.difference(camino)
    t.superficies["camino"] = camino


# ---------------------------------------------------------------------------
# Alcorques: los árboles de las aceras y las plazas
# ---------------------------------------------------------------------------
def trazar_alcorques(t: Trazado) -> None:
    """Un alcorque cuadrado (tierra, más baja que la acera) alrededor de cada árbol que
    cae dentro de lo peatonal, orientado con la calle más cercana."""
    peaton = unary_union([t.superficies[c] for c in PEATONALES])
    dentro = peaton.buffer(-0.15)
    ejes = [(LineString([a, b]), angulo_de(a, b)) for c in D.CALLES if c["tipo"] not in ("camino", "escalinata")
            for a, b in zip(c["puntos"], c["puntos"][1:])]
    arbol_ejes = STRtree([e for e, _ in ejes])
    t.alcorques = []
    for a in D.ARBOLES:
        punto = Point(a["pos"])
        if not dentro.contains(punto):
            continue
        cercano = int(arbol_ejes.nearest(punto))
        angulo = ejes[cercano][1]
        lado = LADO_ALCORQUE / 2
        c, s = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
        esquinas = [(a["pos"][0] + c * u - s * v, a["pos"][1] + s * u + c * v)
                    for u, v in ((-lado, -lado), (lado, -lado), (lado, lado), (-lado, lado))]
        forma = Polygon(esquinas)
        if not dentro.contains(forma):
            continue
        t.alcorques.append({"pos": a["pos"], "angulo": angulo, "forma": forma})
    huecos = unary_union([a["forma"] for a in t.alcorques])
    for clase in PEATONALES:
        t.superficies[clase] = t.superficies[clase].difference(huecos)
    t.superficies["alcorque"] = huecos


def abrir_socavones(t: Trazado) -> None:
    """Los socavones (deterioro.py) cortan todo lo que se pisa: dentro queda el hueco, que
    llena la malla de cada uno (trazar_grupos)."""
    import deterioro as DT

    huecos = DT.huecos()
    for clase in list(t.superficies):
        t.superficies[clase] = t.superficies[clase].difference(huecos)


def abrir_firmes(t: Trazado) -> None:
    """Las zonas de firme roto (firmes.py) cortan su clase: dentro van su base y sus
    placas (trazar_grupos)."""
    import firmes as FR

    t.firmes = FR.zonas(t)
    rotas = unary_union([z.contorno for z in t.firmes])
    for clase in list(t.superficies):
        t.superficies[clase] = t.superficies[clase].difference(rotas)


def trazar() -> Trazado:
    """El trazado en planta (sin alturas)."""
    t = Trazado()
    trazar_calles(t)
    trazar_superficies(t)
    trazar_alcorques(t)
    abrir_socavones(t)
    abrir_firmes(t)
    return t


# ---------------------------------------------------------------------------
# Alturas: calles niveladas, rasante de tránsito y escaleras
# ---------------------------------------------------------------------------
# Talud con el que el terreno se ajusta a una calle nivelada.
TALUD_NIVELADA = 8.0
# Pendiente máxima de las rampas (la Bajada lleva tranvía).
PENDIENTE_RAMPA = 0.08
# Hasta dónde se rellena la rasante de los muelles hacia el río (más que una celda).
RELLENO_MUELLE = 4.0


def _media_movil(valores: np.ndarray, ventana: int) -> np.ndarray:
    if ventana <= 1 or len(valores) < 3:
        return valores.copy()
    relleno = np.pad(valores, ventana, mode="edge")
    nucleo = np.ones(2 * ventana + 1) / (2 * ventana + 1)
    return np.convolve(relleno, nucleo, mode="same")[ventana:-ventana]


def _limitar_pendiente(z: np.ndarray, paso: float, pendiente: float) -> np.ndarray:
    """Rasante que no supera `pendiente`: corta lo que sube de más hacia delante y rellena
    hacia atrás (como un movimiento de tierras)."""
    z = z.copy()
    for i in range(1, len(z)):
        z[i] = min(z[i], z[i - 1] + pendiente * paso)
    for i in range(len(z) - 2, -1, -1):
        z[i] = max(z[i], z[i + 1] - pendiente * paso)
    return z


def muestrear(h: np.ndarray, res: float, xs, ys) -> np.ndarray:
    """Altura bilineal en puntos del mapa (h[j, i] es el centro de la celda (i, j))."""
    fx = np.clip(np.asarray(xs, float) / res - 0.5, 0.0, h.shape[1] - 1.0001)
    fy = np.clip(np.asarray(ys, float) / res - 0.5, 0.0, h.shape[0] - 1.0001)
    i0 = np.floor(fx).astype(int)
    j0 = np.floor(fy).astype(int)
    tx = fx - i0
    ty = fy - j0
    return (h[j0, i0] * (1 - tx) * (1 - ty) + h[j0, i0 + 1] * tx * (1 - ty)
            + h[j0 + 1, i0] * (1 - tx) * ty + h[j0 + 1, i0 + 1] * tx * ty)


def rasantes(terreno: np.ndarray, res: float) -> dict:
    """La rasante (altura a lo largo del eje) de cada calle nivelada, sacada del terreno
    natural y suavizada. La Bajada va a ras del Muelle Norte mientras comparte su banda y
    después sube con pendiente acotada."""
    resultado = {}
    paso = 2.0
    for ident in CALLES_NIVELADAS:
        c = _calle(ident)
        linea = LineString(c["puntos"])
        n = max(2, int(linea.length / paso))
        s = np.linspace(0.0, linea.length, n + 1)
        puntos = [linea.interpolate(v) for v in s]
        xs = np.array([p.x for p in puntos])
        ys = np.array([p.y for p in puntos])
        z = muestrear(terreno, res, np.clip(xs, 0, ANCHO), np.clip(ys, 0, ALTO))
        z = _media_movil(z, int(20 / paso))
        if ident == "bajada":
            muelle = banda(_calle("muelle_norte")["puntos"], 22.0)
            dentro = shapely.contains_xy(muelle, xs, ys)
            salida = int(np.argmin(dentro)) if not dentro.all() else len(z)
            z[:salida] = z[0]
            z = np.maximum.accumulate(z)
            z = _limitar_pendiente(z, linea.length / n, PENDIENTE_RAMPA)
        resultado[ident] = {"s": s / linea.length, "z": z, "puntos": c["puntos"], "media": c["ancho"] / 2.0}
    return resultado


def _rejilla(forma, res: float):
    """Centros de las celdas del relieve: (gx, gy)."""
    ny, nx = forma
    xs = (np.arange(nx) + 0.5) * res
    ys = (np.arange(ny) + 0.5) * res
    return np.meshgrid(xs, ys)


def nivelar(terreno: np.ndarray, res: float, ferrocarril: dict | None = None) -> np.ndarray:
    """El terreno con las calles de la loma y las vías del tren niveladas: dentro de la
    franja, la rasante (de lado a lado); fuera, se funde con el terreno en un talud (de
    TALUD_NIVELADA metros en las calles; el suyo en cada vía). Las vías hacen así sus
    terraplenes y sus trincheras."""
    import relieve as R

    gx, gy = _rejilla(terreno.shape, res)
    resultado = terreno.copy()
    peso_max = np.zeros_like(terreno)
    franjas = list(rasantes(terreno, res).values()) + list((ferrocarril or {}).values())
    for datos in franjas:
        talud = datos.get("talud", TALUD_NIVELADA)
        pts = np.asarray(datos["puntos"], float)
        alcance = datos["media"] + talud
        caja = ((gx >= pts[:, 0].min() - alcance) & (gx <= pts[:, 0].max() + alcance)
                & (gy >= pts[:, 1].min() - alcance) & (gy <= pts[:, 1].max() + alcance))
        d, f = R._distancia_polilinea(gx[caja], gy[caja], datos["puntos"])
        z = np.interp(f, datos["s"], datos["z"])
        t = np.clip((d - datos["media"]) / talud, 0.0, 1.0)
        peso = 1.0 - t * t * (3.0 - 2.0 * t)
        if datos.get("sin_nivelar"):
            # Bajo el puente del ferrocarril, el río sigue a su altura.
            a, b = datos["sin_nivelar"]
            peso = np.where((f > a) & (f < b), 0.0, peso)
        actual = peso_max[caja]
        mejor = peso > actual
        valores = resultado[caja]
        valores[mejor] = terreno[caja][mejor] * (1.0 - peso[mejor]) + z[mejor] * peso[mejor]
        resultado[caja] = valores
        peso_max[caja] = np.maximum(actual, peso)
    return resultado


def rasante_transito(terreno: np.ndarray, res: float) -> np.ndarray:
    """La rasante del tránsito: el terreno nivelado y sin escombros, con dos arreglos que
    solo valen para lo que se pisa (el terreno que se ve no cambia):

    - En los muelles de granito la orilla cae a pico al hielo, y en la rejilla de 2 m ese
      escalón se reparte en una celda: las aceras del muelle se hundirían hacia el río. Se
      rellena la orilla hasta la cota del muelle, y el pretil cierra el borde.
    - La plaza de la cabeza de la Escalinata se allana: horizontal de lado a lado en lo alto
      de la escalera y unida a la calle del Mirador al otro lado."""
    import relieve as R

    gx, gy = _rejilla(terreno.shape, res)
    rasante = terreno.copy()
    # Muelles: hasta RELLENO_MUELLE metros hacia dentro del río, la cota de su orilla.
    centro = R.rio_y(gx)
    medio = R.rio_ancho(gx) / 2.0
    sur = (gy < centro) & (gy > centro - medio - 1.5) & (gy < centro - medio + RELLENO_MUELLE)
    norte = (gy > centro) & (gy < centro + medio + 1.5) & (gy > centro + medio - RELLENO_MUELLE)
    muro_s = (gx >= R.MURO_SUR[0]) & (gx <= R.MURO_SUR[1])
    muro_n = (gx >= R.MURO_NORTE[0]) & (gx <= R.MURO_NORTE[1])
    rasante = np.where(sur & muro_s, 0.0, rasante)
    rasante = np.where(norte & muro_n, 1.0, rasante)
    # La cabeza de la Escalinata (con 3 m de más por cada lado, para que la plaza no tome
    # alturas de fuera al interpolar).
    s, tt = a_eje_np(gx, gy)
    caja = ((s > ESCALINATA_CABEZA - 3.0) & (s < ESCALINATA_FIN + 3.0)
            & (np.abs(tt) < ESCALINATA_MEDIA + 3.0))
    abajo = cota_cabeza_escalinata(terreno, res)
    arriba = muestrear(terreno, res, *_eje_xy(np.full_like(tt, ESCALINATA_FIN), tt))
    f = np.clip((s - ESCALINATA_CABEZA) / (ESCALINATA_FIN - ESCALINATA_CABEZA), 0.0, 1.0)
    rasante = np.where(caja, abajo + (arriba - abajo) * f, rasante)
    return rasante


def a_eje_np(x, y):
    """Del mapa al marco del eje monumental (con arrays)."""
    from geo import EJE_ANGULO, EJE_ORIGEN

    c, s = math.cos(math.radians(EJE_ANGULO)), math.sin(math.radians(EJE_ANGULO))
    dx = np.asarray(x, float) - EJE_ORIGEN[0]
    dy = np.asarray(y, float) - EJE_ORIGEN[1]
    return dx * c + dy * s, -dx * s + dy * c


def _eje_xy(s, t):
    from geo import EJE_ANGULO, EJE_ORIGEN

    c, sn = math.cos(math.radians(EJE_ANGULO)), math.sin(math.radians(EJE_ANGULO))
    s = np.asarray(s, float)
    t = np.asarray(t, float)
    return EJE_ORIGEN[0] + c * s - sn * t, EJE_ORIGEN[1] + sn * s + c * t


def cota_cabeza_escalinata(terreno: np.ndarray, res: float) -> float:
    """La cota de lo alto de la Escalinata: la del Bulevar del Río donde la cruza."""
    x, y = _eje_xy(ESCALINATA_CABEZA - 12.0, 0.0)
    return round(float(muestrear(terreno, res, [x], [y])[0]), 2)


def colocar_peldanos(perfil_s: np.ndarray, perfil_z: np.ndarray, z0: float, z1: float,
                     contrahuella: float = 0.15, huella: float = 0.38, max_tramo: int = 12,
                     descanso: float = 1.6) -> list[tuple[float, float, float]]:
    """Peldaños de una escalera que sigue el terreno, de s=perfil_s[0] a perfil_s[-1] y de
    z0 a z1 (subiendo). Los peldaños se agrupan en tramos de huella normal y cada tramo se
    centra donde el terreno alcanza su altura media: donde el terreno sube hay tramos, y lo
    llano queda en descansillos. Devuelve las pisadas como (s_inicio, s_fin, z), con los
    descansillos incluidos."""
    s0, s1 = float(perfil_s[0]), float(perfil_s[-1])
    if z1 - z0 < contrahuella * 0.5:
        return [(s0, s1, z1)]
    n = max(1, int(round((z1 - z0) / contrahuella)))
    alto = (z1 - z0) / n
    tramos = math.ceil(n / max_tramo)
    base, resto = divmod(n, tramos)
    peldanos = [base + (1 if i < resto else 0) for i in range(tramos)]
    largo = s1 - s0
    # Si no cabe todo con la huella normal, se acorta (nunca por debajo de 28 cm).
    huella = max(0.28, min(huella, (largo - descanso * (tramos - 1)) / (n + 1)))
    subida = np.maximum.accumulate(np.asarray(perfil_z, float))
    subida = z0 + (subida - subida[0]) * (z1 - z0) / max(1e-6, subida[-1] - subida[0])
    centros, hechos = [], 0
    for k in peldanos:
        z_medio = z0 + (hechos + k / 2.0) * alto
        centros.append(float(np.interp(z_medio, subida, perfil_s)))
        hechos += k
    # Cada tramo, centrado en su sitio; luego se separan para que quepan los descansillos.
    inicios = [c - k * huella / 2.0 for c, k in zip(centros, peldanos)]
    for _ in range(3):
        inicios[0] = max(inicios[0], s0 + huella)
        for i in range(1, tramos):
            inicios[i] = max(inicios[i], inicios[i - 1] + peldanos[i - 1] * huella + descanso)
        fin = inicios[-1] + peldanos[-1] * huella
        if fin > s1 - huella:
            inicios[-1] -= fin - (s1 - huella)
        for i in range(tramos - 2, -1, -1):
            inicios[i] = min(inicios[i], inicios[i + 1] - peldanos[i] * huella - descanso)
    pisadas, z, desde = [], z0, s0
    for inicio, k in zip(inicios, peldanos):
        for j in range(k):
            borde = inicio + j * huella
            pisadas.append((desde, borde, z))
            desde, z = borde, z + alto
    pisadas.append((desde, s1, z1))
    return pisadas


class Alturas:
    """Las alturas del tránsito: la rasante (lo que se pisa) y el relieve (el terreno que se
    ve, con los escombros), muestreados como en la maqueta (bilineal entre los centros de
    las celdas de 2 m)."""

    def __init__(self, rasante: np.ndarray, relieve: np.ndarray, desnudo: np.ndarray, res: float = 2.0,
                 ferrocarril: dict | None = None):
        self.rasante = rasante
        self.relieve = relieve
        # Las rasantes de las vías del tren (ferrocarril.perfiles).
        self.ferrocarril = ferrocarril or {}
        # El terreno nivelado sin escombros: con él se decide si un borde es muro (los
        # montones de escombros caen encima de la acera, no la contienen).
        self.desnudo = desnudo
        self.res = res

    def base(self, regla: dict, xs, ys) -> np.ndarray:
        xs = np.asarray(xs, float)
        ys = np.asarray(ys, float)
        tipo = regla["tipo"]
        if tipo == "terreno":
            return muestrear(self.rasante, self.res, xs, ys)
        if tipo == "plano":
            gx, gy = regla.get("g", (0.0, 0.0))
            x0, y0 = regla.get("o", (0.0, 0.0))
            return regla["z"] + gx * (xs - x0) + gy * (ys - y0)
        if tipo == "rampa":
            (x0, y0), (dx, dy) = regla["o"], regla["d"]
            f = np.clip(((xs - x0) * dx + (ys - y0) * dy) / regla["largo"], 0.0, 1.0)
            return regla["z0"] + (regla["z1"] - regla["z0"]) * f
        if tipo == "malla":
            return regla["malla"].z_en(xs, ys)
        raise ValueError(tipo)

    def z(self, grupo: Grupo, xs, ys) -> np.ndarray:
        return self.base(grupo.regla, xs, ys) + CLASES[grupo.clase]["nivel"]

    def terreno(self, xs, ys) -> np.ndarray:
        return muestrear(self.relieve, self.res, np.asarray(xs, float), np.asarray(ys, float))

    def terreno_desnudo(self, xs, ys) -> np.ndarray:
        return muestrear(self.desnudo, self.res, np.asarray(xs, float), np.asarray(ys, float))


# ---------------------------------------------------------------------------
# Grupos: orientación de las texturas, el puente y las escaleras
# ---------------------------------------------------------------------------
def _angulo_dominante(forma) -> float:
    """Dirección del lado más largo del rectángulo mínimo que la contiene."""
    rect = forma.minimum_rotated_rectangle
    pts = list(rect.exterior.coords)
    lados = [(math.dist(pts[i], pts[i + 1]), angulo_de(pts[i], pts[i + 1])) for i in range(4)]
    return max(lados)[1]


def _particion_orientada() -> list[tuple[object, float]]:
    """Trozos del mapa con la dirección de lo que ordena el pavimento (para orientar las
    losas, los adoquines y las juntas): las plazas, con la suya; después cada tramo recto de
    cada calle, por orden de importancia. Lo que no cae en ninguno toma la del tramo más
    cercano."""
    piezas = []
    ocupado = Polygon()
    for p in D.PLAZAS:
        piezas.append((p["forma"].difference(ocupado), _angulo_dominante(p["forma"])))
        ocupado = ocupado.union(p["forma"])
    cabeza = cabeza_escalinata()
    piezas.append((cabeza.difference(ocupado), _angulo_dominante(cabeza)))
    ocupado = ocupado.union(cabeza)
    orden = {"avenida": 0, "puente": 1, "principal": 2, "calle": 3, "peatonal": 4, "servicio": 5}
    for c in sorted((c for c in D.CALLES if c["tipo"] in orden), key=lambda c: orden[c["tipo"]]):
        for a, b in zip(c["puntos"], c["puntos"][1:]):
            tramo = banda([a, b], c["ancho"] + 2.0).difference(ocupado)
            if not tramo.is_empty:
                piezas.append((tramo, angulo_de(a, b)))
                ocupado = ocupado.union(tramo)
    return piezas


def _orientar(forma, particion) -> list[tuple[object, float]]:
    """La forma repartida por la partición orientada; lo que no cae en ninguna pieza toma
    la dirección del tramo de calle más cercano."""
    piezas, arbol, union, ejes, ejes_arbol = particion
    resultado = []
    if forma.is_empty:
        return resultado
    for j in arbol.query(forma, predicate="intersects"):
        pieza, angulo = piezas[int(j)]
        parte = unary_union(poligonos(forma.intersection(pieza)))
        if parte.area > 0.01:
            resultado.append((parte, angulo))
    for p in poligonos(forma.difference(union)):
        if p.area < 0.01:
            continue
        cercano = int(ejes_arbol.nearest(p.representative_point()))
        resultado.append((p, ejes[cercano][1]))
    return resultado


def _al_milimetro(geom):
    """La geometría sin trozos de menos de 10 cm². Las coordenadas no se redondean aquí
    (el redondeo de shapely mueve los vértices de cada grupo por su cuenta y abre solapes
    entre vecinos): se redondean al exportar, vértice a vértice, igual a los dos lados de
    cada linde."""
    return unary_union([p for p in poligonos(geom) if p.area > 0.001])


def regla_puente() -> dict:
    """El tablero del puente del Progreso sobre el río: de la cota del Muelle Sur (0) a la
    del Muelle Norte (1), en línea recta de orilla a orilla (las dos orillas son muelles
    horizontales, así que el tablero llega a ras a cada una)."""
    import relieve as R

    puente = _calle("puente_progreso")
    linea = LineString(puente["puntos"])
    cruce = linea.intersection(D.RIO)
    x_medio = cruce.centroid.x
    y_sur = float(R.orilla_sur(x_medio))
    y_norte = float(R.orilla_norte(x_medio))
    return {"tipo": "rampa", "o": (x_medio, y_sur), "d": (0.0, 1.0), "largo": y_norte - y_sur,
            "z0": 0.0, "z1": COTA_MUELLE_NORTE}


def trazar_grupos(t: Trazado, alturas: Alturas) -> None:
    """Reparte las clases en grupos: el tablero del puente, aparte y en el aire; lo
    pavimentado, por la orientación de su calle; los peldaños, uno por pisada."""
    piezas = _particion_orientada()
    ejes = [(LineString([a, b]), angulo_de(a, b)) for c in D.CALLES if c["tipo"] not in ("camino", "escalinata")
            for a, b in zip(c["puntos"], c["puntos"][1:])]
    particion = (piezas, STRtree([p for p, _ in piezas]), unary_union([p for p, _ in piezas]), ejes,
                 STRtree([e for e, _ in ejes]))
    rio = D.RIO
    puente = regla_puente()
    grupos = []
    for clase, forma in t.superficies.items():
        if forma.is_empty:
            continue
        en_rio = forma.intersection(rio)
        en_tierra = forma.difference(rio)
        trozos = []
        if clase in ("calzada", "senda", "camino", "alcorque"):
            trozos.append((en_tierra, 0.0, False))
            trozos.append((en_rio, 0.0, True))
        else:
            trozos += [(g, a, False) for g, a in _orientar(en_tierra, particion)]
            trozos += [(g, a, True) for g, a in _orientar(en_rio, particion)]
        for geom, angulo, elevado in trozos:
            geom = _al_milimetro(geom)
            if geom.is_empty:
                continue
            regla = puente if elevado else {"tipo": "terreno"}
            grupos.append(Grupo(clase, geom, regla, round(angulo % 180.0, 2), elevado))
    t.grupos = grupos
    t.puente = {"regla": puente}
    _escalinata(t, alturas)
    _escaleras_sendas(t, alturas)
    _andenes(t, alturas)
    _socavones(t, alturas)
    _firmes(t, alturas)


def _firmes(t: Trazado, alturas: Alturas) -> None:
    """Un grupo por zona de firme roto, con la malla de su base, y sus placas."""
    import firmes as FR

    t.placas = []
    t.formas_placas = []
    for z in t.firmes:
        nivel = CLASES[z.clase]["nivel"]

        def calle(xs, ys, nivel=nivel):
            return muestrear(alturas.rasante, alturas.res, np.asarray(xs, float), np.asarray(ys, float)) + nivel

        base = FR.malla(z, calle)
        t.grupos.append(Grupo("firme", z.contorno, {"tipo": "malla", "malla": base}, 0.0, False, base))
        datos, formas = FR.placas(z, calle)
        if datos["caras"]:
            t.placas.append(datos)
        t.formas_placas += formas


def _socavones(t: Trazado, alturas: Alturas) -> None:
    """Un grupo por socavón, con su malla: el borde, CAPA bajo lo que se pisa al otro lado
    (la calzada, la acera…), y de ahí al fondo. También las piezas que caen dentro."""
    import deterioro as DT

    partes, duenos = [], []
    for i, g in enumerate(t.grupos):
        if g.elevado:
            continue
        for p in poligonos(g.forma):
            partes.append(p)
            duenos.append(i)
    arbol = STRtree(partes)
    t.socavones = []
    for s in DT.socavones():
        borde = s.borde
        fuera = borde + (borde - np.array(s.centro)) / np.hypot(*(borde - np.array(s.centro)).T)[:, None] * 0.05
        z = muestrear(alturas.rasante, alturas.res, borde[:, 0], borde[:, 1]) + NIVEL_CALZADA
        rodado = np.zeros(len(borde), bool)
        a, b = arbol.query(shapely.points(fuera[:, 0], fuera[:, 1]), predicate="intersects")
        visto = np.zeros(len(borde), bool)
        for k, j in zip(a, b):
            if visto[k]:
                continue
            visto[k] = True
            g = t.grupos[duenos[j]]
            z[k] = float(alturas.z(g, [borde[k, 0]], [borde[k, 1]])[0])
            rodado[k] = g.clase in ("calzada", "adoquin")
        malla = DT.malla(s, z - DT.CAPA)
        regla = {"tipo": "malla", "malla": malla}
        t.grupos.append(Grupo("socavon", s.contorno, regla, 0.0, False, malla))
        t.socavones.append({"socavon": s, "grupo": len(t.grupos) - 1,
                            "piezas": DT.piezas(s, malla, float(np.mean(rodado)))})


def _andenes(t: Trazado, alturas: Alturas) -> None:
    """Los andenes isla de la estación de tren, con sus rampas, a 1,10 m sobre el carril."""
    import ferrocarril as F

    if "principal" not in alturas.ferrocarril:
        return
    for anden in F.andenes(alturas.ferrocarril):
        regla = {"tipo": "plano", "z": round(anden["z"], 3)}
        if "gx" in anden:
            regla.update({"g": (anden["gx"], 0.0), "o": (anden["ox"], 0.0)})
        t.grupos.append(Grupo("anden", anden["forma"], regla, 0.0))


def _pisadas_en_grupos(t: Trazado, huella, pisadas, marco, angulo: float, nombre: str) -> list[int]:
    """Un grupo de peldaño por pisada: la huella cortada entre s_inicio y s_fin del marco
    (una función que da el rectángulo de la escalera entre dos s)."""
    indices = []
    for k, (s0, s1, z) in enumerate(pisadas):
        forma = _al_milimetro(huella.intersection(marco(s0, s1)))
        if forma.is_empty:
            continue
        t.grupos.append(Grupo("peldano", forma, {"tipo": "plano", "z": round(z, 3)}, round(angulo % 180.0, 2)))
        indices.append(len(t.grupos) - 1)
    return indices


def _escalinata(t: Trazado, alturas: Alturas) -> None:
    """Los peldaños y los rellanos de la Escalinata y sus muros laterales con pretil."""
    s = np.arange(ESCALINATA_INICIO, ESCALINATA_CABEZA + 0.5, 1.0)
    xs, ys = _eje_xy(s, np.zeros_like(s))
    perfil = alturas.base({"tipo": "terreno"}, xs, ys)
    z0 = COTA_MUELLE_NORTE + NIVEL_PEATON
    z1 = cota_cabeza_escalinata(alturas.rasante, alturas.res) + NIVEL_PEATON
    pisadas = colocar_peldanos(s, perfil, z0, z1)
    # El rellano de abajo empieza en la plaza.
    pisadas[0] = (560.0, pisadas[0][1], pisadas[0][2])

    def marco(s0, s1):
        return rect_eje(s0, s1, -ESCALINATA_MEDIA - 1.0, ESCALINATA_MEDIA + 1.0)

    indices = _pisadas_en_grupos(t, t.zona_escalinata, pisadas, marco, 48.0, "Escalinata")
    t.escaleras.append({"nombre": "La Escalinata", "grupos": indices,
                        "pisadas": [(round(a, 3), round(b, 3), round(z, 3)) for a, b, z in pisadas]})
    # Muros laterales, por fuera de la huella: siguen la línea de los peldaños, con pretil.
    for lado in (-1.0, 1.0):
        borde = LineString([eje(560.0, lado * ESCALINATA_MEDIA), eje(ESCALINATA_CABEZA, lado * ESCALINATA_MEDIA)])
        for tramo in lineas(borde.intersection(t.zona_escalinata.buffer(0.01))):
            s_a, _ = a_eje(*tramo.coords[0])
            s_b, _ = a_eje(*tramo.coords[-1])
            t_muro = lado * (ESCALINATA_MEDIA + MURO_ESCALINATA["grosor"] / 2.0)
            linea = LineString([eje(min(s_a, s_b), t_muro), eje(max(s_a, s_b), t_muro)])
            _muro(t, linea, pisadas, lambda p: a_eje(p.x, p.y)[0], MURO_ESCALINATA)


# Muros de las escaleras: grosor, altura del pretil sobre la línea de los peldaños y lo
# mínimo que asoman sobre el terreno (al otro lado del muro).
MURO_ESCALINATA = {"grosor": 0.6, "pretil": 1.0, "sobre_terreno": 0.5, "material": "granito"}
MURO_SENDA = {"grosor": 0.25, "pretil": 0.12, "sobre_terreno": 0.1, "material": "hormigon"}


def _muro(t: Trazado, linea: LineString, pisadas, proyectar, medidas: dict) -> None:
    """Un muro a lo largo de `linea`, con la altura de la línea de los peldaños en cada
    punto (`proyectar` da la s de la escalera de un punto del plano)."""
    puntos = []
    n = max(1, int(math.ceil(linea.length / 0.5)))
    for i in range(n + 1):
        p = linea.interpolate(i * linea.length / n)
        puntos.append((round(p.x, 2), round(p.y, 2), round(_linea_de_paso(pisadas, proyectar(p)), 3)))
    t.muros.append({"puntos": _simplificar_3d(puntos), **medidas})


def _linea_de_paso(pisadas, s: float) -> float:
    """La línea que une las aristas de los peldaños: sube recta en los tramos y va llana en
    los descansillos (por ella van los pretiles y las barandillas)."""
    xs, zs = [], []
    for s0, s1, z in pisadas:
        xs.append(s0)
        zs.append(z)
        if s1 - s0 > 1.0:
            xs.append(s1 - 0.3)
            zs.append(z)
    xs.append(pisadas[-1][1])
    zs.append(pisadas[-1][2])
    return float(np.interp(s, xs, zs))


def _simplificar_3d(puntos: list, tolerancia: float = 0.005) -> list:
    """Quita los puntos alineados (en planta y en altura)."""
    if len(puntos) < 3:
        return puntos
    resultado = [puntos[0]]
    for i in range(1, len(puntos) - 1):
        a = np.array(resultado[-1])
        b = np.array(puntos[i])
        c = np.array(puntos[i + 1])
        ac = c - a
        largo = np.linalg.norm(ac)
        if largo < 1e-9:
            continue
        f = np.dot(b - a, ac) / (largo * largo)
        if np.linalg.norm(a + ac * f - b) > tolerancia:
            resultado.append(puntos[i])
    resultado.append(puntos[-1])
    return resultado


def _escaleras_sendas(t: Trazado, alturas: Alturas) -> None:
    """Las escaleras de las sendas (la de la loma y la del barranco): de hormigón, con
    descansillo en el codo y barandilla de tubo a los dos lados."""
    for esc in t.escaleras_sendas:
        pts = esc["puntos"]
        linea = LineString(pts)
        largo = linea.length
        s = np.arange(0.0, largo + 0.01, 0.5)
        s[-1] = min(s[-1], largo)
        puntos = [linea.interpolate(v) for v in s]
        perfil = alturas.base({"tipo": "terreno"}, [p.x for p in puntos], [p.y for p in puntos])
        # Sube siempre: si la senda baja, se recorre al revés.
        if perfil[-1] < perfil[0]:
            pts = list(reversed(pts))
            linea = LineString(pts)
            perfil = perfil[::-1]
        # Las puntas a ras de lo que tocan (la acera o el camino); el codo, en descansillo.
        codos = np.cumsum([0.0] + [math.dist(a, b) for a, b in zip(pts, pts[1:])])
        z0 = float(perfil[0]) + NIVEL_PEATON
        z1 = float(perfil[-1]) + NIVEL_PEATON
        pisadas = []
        z_codos = [z0] + [float(np.interp(c, s, perfil)) + NIVEL_PEATON for c in codos[1:-1]] + [z1]
        z_codos = list(np.maximum.accumulate(z_codos))
        for k in range(len(pts) - 1):
            a, b = codos[k], codos[k + 1]
            dentro = (s >= a) & (s <= b)
            tramo = colocar_peldanos(s[dentro], perfil[dentro], z_codos[k], z_codos[k + 1])
            if pisadas:
                # El descansillo del codo: el final del tramo anterior y el principio de este.
                anterior = pisadas.pop()
                tramo[0] = (anterior[0], tramo[0][1], tramo[0][2])
            pisadas += tramo
        huella = esc["huella"]
        segmentos = list(zip(pts, pts[1:]))

        def marco(s0, s1, segmentos=segmentos, codos=codos):
            partes = []
            for k, (a, b) in enumerate(segmentos):
                lo, hi = max(s0, codos[k]), min(s1, codos[k + 1])
                if s0 <= codos[k] and k > 0:
                    lo = codos[k] - ANCHO_ESCALERA_SENDA  # el codo entero
                if s1 >= codos[k + 1] and k < len(segmentos) - 1:
                    hi = codos[k + 1] + ANCHO_ESCALERA_SENDA
                if hi <= lo:
                    continue
                d = (b[0] - a[0], b[1] - a[1])
                n = math.hypot(*d)
                u = (d[0] / n, d[1] / n)
                v = (-u[1], u[0])
                w = ANCHO_ESCALERA_SENDA
                o = (a[0] - u[0] * codos[k], a[1] - u[1] * codos[k])
                esquinas = [(o[0] + u[0] * ss + v[0] * tt, o[1] + u[1] * ss + v[1] * tt)
                            for ss, tt in ((lo, -w), (hi, -w), (hi, w), (lo, w))]
                partes.append(Polygon(esquinas))
            return unary_union(partes) if partes else Polygon()

        # Cada pisada se recorta contra la de antes (en el codo se solapan los marcos).
        hecho = Polygon()
        indices = []
        for s0, s1, z in pisadas:
            forma = huella.intersection(marco(s0, s1)).difference(hecho)
            forma = _al_milimetro(forma)
            if forma.is_empty:
                continue
            hecho = hecho.union(forma)
            k = min(len(segmentos) - 1, int(np.searchsorted(codos, (s0 + s1) / 2.0) - 1))
            angulo = angulo_de(*segmentos[max(0, k)])
            t.grupos.append(Grupo("peldano", forma, {"tipo": "plano", "z": round(z, 3)}, round(angulo % 180.0, 2)))
            indices.append(len(t.grupos) - 1)
        t.escaleras.append({"nombre": esc["nombre"], "grupos": indices,
                            "pisadas": [(round(a, 3), round(b, 3), round(z, 3)) for a, b, z in pisadas]})
        # Muros bajos a los lados (contienen el terreno donde la escalera va excavada) y
        # barandillas de tubo a 0,3 m de cada lado, a 0,9 m sobre la línea de los peldaños.
        # El muro va solo a lo largo de la huella (no entra en la acera de cada punta).
        dentro = max(lineas(linea.intersection(huella)), key=lambda l: l.length)
        for lado in (-1.0, 1.0):
            borde = dentro.offset_curve(lado * (ANCHO_ESCALERA_SENDA / 2.0 + MURO_SENDA["grosor"] / 2.0), join_style=2)
            _muro(t, borde, pisadas, linea.project, MURO_SENDA)
            desplazada = linea.offset_curve(lado * (ANCHO_ESCALERA_SENDA / 2.0 - 0.3), join_style=2)
            puntos3 = []
            n = max(1, int(math.ceil(desplazada.length / 0.5)))
            for i in range(n + 1):
                p = desplazada.interpolate(i * desplazada.length / n)
                sp = linea.project(p)
                puntos3.append((round(p.x, 2), round(p.y, 2), round(_linea_de_paso(pisadas, sp) + 0.9, 3)))
            t.barandillas.append({"puntos": _simplificar_3d(puntos3)})


# ---------------------------------------------------------------------------
# Aristas
# ---------------------------------------------------------------------------
# Diferencias de altura que separan una junta, un escalón y un muro.
JUNTA = 0.02
ESCALON = 0.25
# Entre lo peatonal y el terreno: hasta aquí, un bordillo de jardín; más, un muro.
BORDE_MAXIMO = 0.4


def _anillos(forma) -> list[LineString]:
    """Los anillos de una forma, con el interior a la izquierda."""
    resultado = []
    for p in poligonos(forma):
        p = orient(p, sign=1.0)
        resultado.append(LineString(p.exterior.coords))
        resultado += [LineString(h.coords) for h in p.interiors]
    return resultado


def _densificar(puntos: list, paso: float = 2.0) -> list:
    resultado = [puntos[0]]
    for a, b in zip(puntos, puntos[1:]):
        n = max(1, int(math.ceil(math.dist(a, b) / paso)))
        for k in range(1, n + 1):
            resultado.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return resultado


def trazar_aristas(t: Trazado, alturas: Alturas) -> None:
    """Las aristas entre grupos y entre un grupo y el terreno, clasificadas por lo que hay a
    cada lado y por la diferencia de altura."""
    partes = []
    duenos = []
    for i, g in enumerate(t.grupos):
        for p in poligonos(g.forma):
            partes.append(p)
            duenos.append(i)
    arbol = STRtree(partes)
    interior = box(-MARGEN_MAPA + 0.5, -MARGEN_MAPA + 0.5, ANCHO + MARGEN_MAPA - 0.5, ALTO + MARGEN_MAPA - 0.5)
    hueco = _hueco_puente().exterior.buffer(0.05)
    fachadas = unary_union([e["huella"] for e in D.EDIFICIOS]).buffer(0.3)
    crudas = []
    for i, g in enumerate(t.grupos):
        for anillo in _anillos(g.forma):
            pts = list(anillo.coords)
            a = np.array(pts[:-1])
            b = np.array(pts[1:])
            d = b - a
            largo = np.hypot(d[:, 0], d[:, 1])
            ok = largo > 1e-6
            normal = np.zeros_like(d)
            normal[ok] = np.stack([-d[ok, 1], d[ok, 0]], axis=1) / largo[ok, None]
            medio = (a + b) / 2.0
            derecha = medio - normal * 0.004
            vecino = np.full(len(a), -1)
            consulta = arbol.query(shapely.points(derecha), predicate="intersects")
            for k, j in zip(*consulta):
                if duenos[j] != i:
                    vecino[k] = duenos[j]
            # Tramos seguidos con el mismo vecino.
            inicio = 0
            for k in range(1, len(a) + 1):
                if k == len(a) or vecino[k] != vecino[inicio] or not ok[k]:
                    if ok[inicio]:
                        crudas.append((pts[inicio:k + 1], i, int(vecino[inicio])))
                    inicio = k
    aristas = []
    for puntos, izq, der in crudas:
        linea = LineString(puntos)
        for tramo in lineas(linea.intersection(interior)):
            aristas += _clasificar(t, alturas, list(tramo.coords), izq, der, hueco, fachadas)
    t.aristas = _unir_aristas(aristas)


def _clasificar(t: Trazado, alturas: Alturas, puntos, izq: int, der: int, hueco, fachadas) -> list[Arista]:
    """El tipo de una arista (o de sus trozos, si cambia por el camino)."""
    gi = t.grupos[izq]
    ci = gi.clase
    if der >= 0:
        gd = t.grupos[der]
        cd = gd.clase
        if ci in CLASES_HUECO or cd in CLASES_HUECO:
            # El corte de la calle en el borde de un socavón o de un firme roto: se guarda una
            # vez, con lo que se pisa a la izquierda y el hueco a la derecha.
            return [Arista(puntos, "derrumbe", izq, der)] if cd in CLASES_HUECO and ci not in CLASES_HUECO else []
        rod_i, rod_d = CLASES[ci]["rodada"], CLASES[cd]["rodada"]
        if rod_i != rod_d:
            # Bordillo: se guarda una vez, con la calzada a la izquierda.
            return [Arista(puntos, "bordillo", izq, der)] if rod_i else []
        pts = _densificar(puntos, 1.0)
        xs = np.array([p[0] for p in pts])
        ys = np.array([p[1] for p in pts])
        dz = alturas.z(gi, xs, ys) - alturas.z(gd, xs, ys)
        # Se guarda una vez: con el lado alto a la izquierda (si es llana, desde el menor).
        if abs(float(np.mean(dz))) < JUNTA:
            return []
        if float(np.mean(dz)) < 0:
            return []
        if ci == "alcorque" or cd == "alcorque":
            return [Arista(puntos, "alcorque", izq, der)]
        if ci == "peldano" and cd == "peldano":
            return [Arista(puntos, "contrahuella", izq, der)]
        tipo = "escalon" if float(np.max(dz)) <= ESCALON else "muro"
        if ci == "peldano" or cd == "peldano":
            tipo = "contrahuella" if float(np.max(dz)) <= ESCALON else "muro"
        return [Arista(puntos, tipo, izq, der)]
    # Contra el terreno.
    if gi.elevado:
        linea = LineString(puntos)
        resultado = []
        for tramo in lineas(linea.difference(hueco)):
            resultado.append(Arista(list(tramo.coords), "pretil", izq, -1))
        for tramo in lineas(linea.intersection(hueco)):
            if tramo.length > 0.05:
                resultado.append(Arista(list(tramo.coords), "rotura", izq, -1))
        return resultado
    if ci == "paso_nivel":
        # La punta de la losa, donde la vía sale de la calle: una cara hasta el balasto.
        return [Arista(puntos, "paso_nivel", izq, -1)]
    if CLASES[ci]["rodada"]:
        return [Arista(puntos, "bordillo", izq, -1)]
    if ci == "anden":
        return [Arista(puntos, "anden", izq, -1)]
    if ci == "peldano":
        return [Arista(puntos, "muro_escalera", izq, -1)]
    if ci == "senda":
        return [Arista(puntos, "bordillo_bajo", izq, -1)]
    if ci == "camino":
        return [Arista(puntos, "tierra", izq, -1)]
    # Lo peatonal contra el terreno: junto a una fachada, nada; si no, un bordillo de
    # jardín, un pretil (el terreno cae) o un muro de contención (el terreno sube).
    linea = LineString(puntos)
    resultado = []
    for tramo in lineas(linea.intersection(fachadas)):
        if tramo.length > 0.05:
            resultado.append(Arista(list(tramo.coords), "fachada", izq, -1))
    for tramo in lineas(linea.difference(fachadas)):
        if tramo.length < 0.05:
            continue
        resultado += _por_desnivel(alturas, gi, list(tramo.coords), izq)
    return resultado


def _por_desnivel(alturas: Alturas, grupo: Grupo, puntos: list, izq: int) -> list[Arista]:
    """Parte una arista de lo peatonal contra el terreno según el desnivel: borde,
    pretil o contención."""
    pts = _densificar(puntos, 1.0)
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    dz = alturas.z(grupo, xs, ys) - alturas.terreno_desnudo(xs, ys)
    tipos = np.where(dz > BORDE_MAXIMO, "pretil", np.where(dz < -BORDE_MAXIMO, "contencion", "borde"))
    trozos = []
    inicio = 0
    for k in range(1, len(pts)):
        if tipos[k] != tipos[inicio] or k == len(pts) - 1:
            trozos.append([pts[inicio:k + 1], str(tipos[inicio])])
            inicio = k
    # Los trozos de menos de 1,5 m se juntan con el anterior (sin cambios de un palmo).
    limpio = []
    for tramo, tipo in trozos:
        if limpio and LineString(tramo).length < 1.5:
            limpio[-1][0] += tramo[1:]
            continue
        limpio.append([list(tramo), tipo])
    return [Arista(_simplificar_2d(t), tipo, izq, -1) for t, tipo in limpio if len(t) > 1]


def _simplificar_2d(puntos: list) -> list:
    if len(puntos) < 3:
        return puntos
    return list(LineString(puntos).simplify(0.002).coords)


def _unir_aristas(aristas: list[Arista]) -> list[Arista]:
    """Junta las aristas seguidas del mismo tipo y los mismos grupos."""
    por_clave = {}
    for a in aristas:
        por_clave.setdefault((a.tipo, a.izq, a.der), []).append(LineString(a.puntos))
    resultado = []
    for (tipo, izq, der), ls in por_clave.items():
        for l in lineas(linemerge(ls)):
            if l.length > 0.02:
                resultado.append(Arista([(round(x, 3), round(y, 3)) for x, y in l.coords], tipo, izq, der))
    return resultado


# ---------------------------------------------------------------------------
# Marcas viales y detalles: pasos de cebra, ejes, tapas, sumideros
# ---------------------------------------------------------------------------
TIPOS_CON_CEBRA = ("avenida", "principal", "calle")
LARGO_CEBRA = 4.0
ANCHO_FRANJA = 0.5
# Las franjas de los pasos de cebra que ya no se ven (de cada una).
FRANJAS_PERDIDAS = 0.25


def _cruces() -> list[tuple[dict, dict, Point]]:
    """Cada cruce entre dos calles con calzada (sin pasos de servicio): (a, b, punto)."""
    calles = [c for c in D.CALLES if c["tipo"] in TIPOS_CON_CEBRA]
    resultado = []
    for i, a in enumerate(calles):
        la = LineString(a["puntos"])
        for b in calles[i + 1:]:
            lb = LineString(b["puntos"])
            if la.distance(lb) > 1.0:
                # ¿Acaba una en la otra (un cruce en T)?
                for c1, c2, l2 in ((a, b, lb), (b, a, la)):
                    for extremo in (c1["puntos"][0], c1["puntos"][-1]):
                        if l2.distance(Point(extremo)) < c2["ancho"] / 2 + 1:
                            resultado.append((c1, c2, l2.interpolate(l2.project(Point(extremo)))))
                continue
            inter = la.intersection(lb)
            puntos = [inter] if inter.geom_type == "Point" else [g for g in getattr(inter, "geoms", []) if g.geom_type == "Point"]
            for p in puntos:
                resultado.append((a, b, p))
            for c1, c2, l2 in ((a, b, lb), (b, a, la)):
                for extremo in (c1["puntos"][0], c1["puntos"][-1]):
                    pe = Point(extremo)
                    if l2.distance(pe) < c2["ancho"] / 2 + 1 and all(pe.distance(p) > 3 for p in puntos):
                        resultado.append((c1, c2, l2.interpolate(l2.project(pe))))
    return resultado


def trazar_marcas(t: Trazado, alturas: Alturas) -> None:
    """Pasos de cebra en los brazos de los cruces (y en las entradas de la glorieta) y la
    línea discontinua del eje de las calles principales y del puente."""
    calzada = t.superficies["calzada"]
    adentro = calzada.buffer(-0.3)
    otras_bandas = {c["id"]: banda(c["puntos"], c["ancho"]) for c in D.CALLES if c["tipo"] in TIPOS_CON_CEBRA}
    pasos = []
    vistos = []

    def poner(centro, direccion, ancho_calle):
        """Un paso de cebra centrado en `centro`, cruzando una calle que va en `direccion`."""
        ux, uy = direccion
        vx, vy = -uy, ux
        if any(math.dist(centro, v) < 6.0 for v in vistos):
            return
        cruce = LineString([(centro[0] - vx * ancho_calle, centro[1] - vy * ancho_calle),
                            (centro[0] + vx * ancho_calle, centro[1] + vy * ancho_calle)])
        franjas = []
        for tramo in lineas(cruce.intersection(adentro)):
            if tramo.length < 2.5:
                continue
            (x0, y0), (x1, y1) = tramo.coords[0], tramo.coords[-1]
            largo = tramo.length
            n = int((largo - 0.2) // 1.0)
            if n < 2:
                continue
            margen = (largo - (n * 1.0 - 0.5)) / 2.0
            for k in range(n):
                f = (margen + k * 1.0 + ANCHO_FRANJA / 2.0) / largo
                cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                franjas.append((round(cx, 2), round(cy, 2)))
        if len(franjas) < 3:
            return
        # La pintura se ha ido a trozos: faltan franjas enteras (las ruedas, el hielo).
        franjas = [f for f in franjas if azar(f"franja/{f[0]}/{f[1]}") >= FRANJAS_PERDIDAS]
        angulo = math.degrees(math.atan2(uy, ux))
        pasos.append({"centro": (round(centro[0], 2), round(centro[1], 2)), "angulo": round(angulo, 2),
                      "largo": LARGO_CEBRA, "ancho": ANCHO_FRANJA, "franjas": franjas})
        vistos.append(centro)

    cruces = _cruces()
    for a, b, punto in cruces + [(b, a, p) for a, b, p in cruces]:
        la = LineString(a["puntos"])
        s = la.project(punto)
        for sentido in (-1.0, 1.0):
            d = b["ancho"] / 2.0 + 1.0 + LARGO_CEBRA / 2.0
            sp = s + sentido * d
            if sp < 6.0 or sp > la.length - 6.0:
                continue
            c = la.interpolate(sp)
            delante = la.interpolate(min(la.length, sp + 0.5))
            detras = la.interpolate(max(0.0, sp - 0.5))
            dx, dy = delante.x - detras.x, delante.y - detras.y
            n = math.hypot(dx, dy)
            if n < 1e-6 or not adentro.contains(c):
                continue
            # Que no caiga dentro de otra calle (en medio de otro cruce).
            if any(banda_o.buffer(1.0).contains(c) for ident, banda_o in otras_bandas.items() if ident != a["id"]):
                continue
            poner((c.x, c.y), (dx / n, dy / n), a["ancho"])
    # Entradas de la glorieta: la avenida y Mineros, a 58 m del centro.
    for angulo in (48.0, 228.0, 0.0, 180.0):
        r = math.radians(angulo)
        c = (CENTRO_GLORIETA[0] + math.cos(r) * (RADIO_ANILLO + 8.0), CENTRO_GLORIETA[1] + math.sin(r) * (RADIO_ANILLO + 8.0))
        if adentro.contains(Point(c)):
            poner(c, (math.cos(r), math.sin(r)), 80.0)
    # Ejes: línea discontinua por el centro de las calles principales y del puente.
    ejes = []
    zonas_cruce = unary_union([Point(p.x, p.y).buffer(max(a["ancho"], b["ancho"]) / 2.0 + 4.0) for a, b, p in cruces])
    cebras = zonas_cebra(pasos, 1.0)
    for c in D.CALLES:
        if c["tipo"] not in ("principal", "puente"):
            continue
        linea = LineString(c["puntos"])
        if c["id"] == "puente_progreso":
            linea = LineString([eje(372.0), eje(FIN_CALZADA_PUENTE)])
        libre = linea.intersection(calzada.buffer(-1.0)).difference(zonas_cruce).difference(cebras)
        for tramo in lineas(libre):
            if tramo.length > 6.0:
                ejes.append({"puntos": [(round(x, 2), round(y, 2)) for x, y in tramo.coords],
                             "tipo": "continua" if c["id"] == "puente_progreso" else "discontinua"})
    t.marcas = {"pasos": pasos, "ejes": ejes}


def zonas_cebra(pasos: list, margen: float):
    """Lo que ocupan los pasos de cebra (con un margen)."""
    zonas = []
    for p in pasos:
        if p["franjas"]:
            zonas.append(shapely.MultiPoint(p["franjas"]).convex_hull.buffer(LARGO_CEBRA / 2.0 + margen))
    return unary_union(zonas)


def trazar_detalles(t: Trazado, alturas: Alturas) -> None:
    """Tapas de registro (redondas en la calzada, cuadradas en la acera), sumideros junto a
    los bordillos y los alcorques, todo con su altura."""
    calzada = unary_union([t.superficies["calzada"], t.superficies["adoquin"]])
    libre_calzada = calzada.buffer(-0.9)
    cebras = zonas_cebra(t.marcas.get("pasos", []), 1.0)
    peaton = unary_union([t.superficies[c] for c in ("acera", "losas")]).buffer(-0.5)
    tapas = []
    for c in D.CALLES:
        if c["tipo"] not in ("avenida", "principal", "calle", "servicio", "puente"):
            continue
        ancho_calzada, acera = anchos(c)
        linea = LineString(c["puntos"])
        paso = 46.0
        s = paso * azar(c["id"] + "/tapas")
        k = 0
        while s < linea.length:
            p = linea.interpolate(s)
            q = linea.interpolate(min(linea.length, s + 1.0))
            dx, dy = q.x - p.x, q.y - p.y
            n = math.hypot(dx, dy) or 1.0
            lado = 1.0 if k % 2 == 0 else -1.0
            desvio = ancho_calzada / 4.0 * lado
            punto = Point(p.x - dy / n * desvio, p.y + dx / n * desvio)
            if libre_calzada.contains(punto) and not cebras.contains(punto):
                tapas.append(("redonda", punto, azar(f"{c['id']}/tapa/{k}") * 360.0))
            if acera >= 2.0 and k % 2 == 1:
                desvio_a = (ancho_calzada / 2.0 + acera * 0.5) * -lado
                punto_a = Point(p.x - dy / n * desvio_a, p.y + dx / n * desvio_a)
                if peaton.contains(punto_a):
                    tapas.append(("cuadrada", punto_a, math.degrees(math.atan2(dy, dx))))
            s += paso
            k += 1
    sumideros = []
    for a in t.aristas:
        if a.tipo != "bordillo":
            continue
        linea = LineString(a.puntos)
        s = 12.0 * azar(f"sumidero/{a.puntos[0]}")
        while s < linea.length - 1.0:
            p = linea.interpolate(s)
            q = linea.interpolate(min(linea.length, s + 0.5))
            dx, dy = q.x - p.x, q.y - p.y
            n = math.hypot(dx, dy) or 1.0
            # La calzada queda a la izquierda: el sumidero, pegado al bordillo.
            punto = Point(p.x - dy / n * 0.3, p.y + dx / n * 0.3)
            if calzada.buffer(-0.05).contains(punto) and not cebras.contains(punto):
                sumideros.append((punto, math.degrees(math.atan2(dy, dx))))
            s += 32.0
    t.detalles = {
        "tapas": [{"tipo": tipo, "pos": (round(p.x, 2), round(p.y, 2)), "angulo": round(ang, 1),
                   "z": round(float(_z_en(t, alturas, p.x, p.y)), 3)} for tipo, p, ang in tapas],
        "sumideros": [{"pos": (round(p.x, 2), round(p.y, 2)), "angulo": round(ang, 1),
                       "z": round(float(_z_en(t, alturas, p.x, p.y)), 3)} for p, ang in sumideros],
        "alcorques": [{"pos": (round(a["pos"][0], 2), round(a["pos"][1], 2)), "angulo": round(a["angulo"], 1),
                       "lado": LADO_ALCORQUE} for a in t.alcorques],
    }


def _z_en(t: Trazado, alturas: Alturas, x: float, y: float) -> float:
    """La altura de lo que se pisa en un punto (el grupo que lo contiene, o el terreno)."""
    grupo = _grupo_en(t, x, y)
    if grupo is None:
        return float(alturas.terreno([x], [y])[0])
    return float(alturas.z(t.grupos[grupo], [x], [y])[0])


def _grupo_en(t: Trazado, x: float, y: float):
    if not hasattr(t, "_arbol"):
        partes, duenos = [], []
        for i, g in enumerate(t.grupos):
            for p in poligonos(g.forma):
                partes.append(p)
                duenos.append(i)
        t._arbol = (STRtree(partes), duenos)
    arbol, duenos = t._arbol
    candidatos = arbol.query(Point(x, y), predicate="intersects")
    return duenos[int(candidatos[0])] if len(candidatos) else None


def superficie_en(t: Trazado, alturas: Alturas, xs, ys) -> np.ndarray:
    """La altura de lo que se pisa en varios puntos: el tránsito si lo hay (sin el tablero
    del puente, que se ve aparte) y si no el terreno, siempre por encima de los escombros."""
    resultado = []
    for x, y in zip(xs, ys):
        terreno = float(alturas.terreno([x], [y])[0])
        grupo = _grupo_en(t, x, y)
        if grupo is None:
            resultado.append(terreno)
        else:
            resultado.append(max(terreno, float(alturas.z(t.grupos[grupo], [x], [y])[0])))
    return np.array(resultado)


# ---------------------------------------------------------------------------
# Todo junto
# ---------------------------------------------------------------------------
def trazar_completo(alturas: Alturas, t: Trazado | None = None) -> Trazado:
    """El trazado con sus grupos, aristas, marcas y detalles (sobre el trazado en planta, si
    ya está hecho)."""
    t = t or trazar()
    trazar_grupos(t, alturas)
    trazar_aristas(t, alturas)
    lineas_muros = unary_union([LineString([p[:2] for p in m["puntos"]]) for m in t.muros]).buffer(0.45)
    t.aristas = [a for a in t.aristas
                 if not (a.tipo == "muro_escalera" and LineString(a.puntos).within(lineas_muros))]
    trazar_marcas(t, alturas)
    trazar_detalles(t, alturas)
    import deterioro as DT

    t.grietas = DT.grietas(t)
    DT.estropear_tapas(t, alturas)
    t.detalles["baches"] = DT.baches(t, alturas)
    t.detalles["bordillos_sueltos"] = DT.romper_bordillos(t, alturas)
    t.detalles["matojos"] = DT.matojos(t, alturas)
    import restos as RS

    t.detalles["restos"] = RS.restos(t, alturas) + RS.farolas(t, alturas)
    import tendido as TD

    postes, lineas, cifras = TD.tendido(t, alturas)
    t.detalles["restos"] += postes
    t.tendido = {"lineas": lineas, "cifras": cifras}
    return t


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------
def _triangular(forma) -> tuple[list, list]:
    """Vértices (x, y) y triángulos (índices) de una forma, por Delaunay restringido."""
    vertices = []
    indice = {}
    triangulos = []
    for p in poligonos(forma):
        for tri in shapely.constrained_delaunay_triangles(p).geoms:
            if tri.area < 1e-6:
                continue
            esquinas = list(orient(tri, sign=1.0).exterior.coords)[:3]
            ids = []
            for x, y in esquinas:
                clave = (round(x, DECIMALES), round(y, DECIMALES))
                if clave not in indice:
                    indice[clave] = len(vertices)
                    vertices.append(clave)
                ids.append(indice[clave])
            if len(set(ids)) == 3:
                triangulos += ids
    return vertices, triangulos


def _exportar_ferrocarril(t: Trazado, alturas: Alturas) -> dict:
    """Las vías del tren (por tramos: abiertos o a ras de la calle) y del tranvía."""
    import ferrocarril as F

    if not alturas.ferrocarril:
        return {}
    import deterioro as DT
    import vias as V

    transito = unary_union([g.forma for g in t.grupos if not g.elevado])
    detalles = V.detalles(alturas.ferrocarril, F.z_en, F.CARRIL)
    # El tranvía no cruza los socavones: sus carriles se cortan en el borde (y asoman).
    por_calle = unary_union([g.forma for g in t.grupos if g.clase != "socavon"])
    return {
        "vias": F.tramos(alturas.ferrocarril, transito, detalles),
        "tranvias": F.tranvias(por_calle, DT.huecos(), DT.VOLADIZO_CARRIL),
        "puente_ferrocarril": F.puente(alturas.ferrocarril),
        "ferrocarril": {"carril": F.CARRIL, "anden": F.ANDEN_ALTO, "desvios": detalles["desvios"],
                        "topes": detalles["topes"]},
    }


def _socavon_json(item: dict, nuevo: dict) -> dict:
    """Un socavón para transito.json: su contorno, su grupo y las piezas que caen dentro."""
    s = item["socavon"]
    h = s.datos
    return {"id": h["id"], "nombre": h["nombre"], "causa": h["causa"], "centro": [round(v, 3) for v in s.centro],
            "hondo": h["hondo"], "grupo": nuevo.get(item["grupo"], -1),
            "contorno": [float(v) for v in s.borde.ravel()], "piezas": item["piezas"]}


def columnas(items: list[dict], campos: dict) -> dict:
    """Una lista de piezas (diccionarios con los mismos campos) por columnas, que pesa mucho
    menos en transito.json: cada campo, una lista (las posiciones, x e y seguidas), con los
    decimales de `campos` (None: tal cual). Los modelos van por su número en "modelos"."""
    resultado = {}
    if any("modelo" in item for item in items):
        modelos = sorted({item["modelo"] for item in items})
        resultado["modelos"] = modelos
        indice = {m: k for k, m in enumerate(modelos)}
        resultado["modelo"] = [indice[item["modelo"]] for item in items]
    for campo, decimales in campos.items():
        if campo == "pos":
            resultado["pos"] = [round(v, decimales) for item in items for v in item["pos"]]
            continue
        valores = [item.get(campo, 1.0 if campo in ("escala", "estira", "alto") else 0.0) for item in items]
        if decimales == 0:
            resultado[campo] = [int(round(v)) for v in valores]
        else:
            resultado[campo] = [round(v, decimales) for v in valores]
    return resultado


PIEZAS = {"pos": 2, "z": 2, "rumbo": 0, "cabeceo": 0, "alabeo": 0, "escala": 2}


def _regla_json(regla: dict) -> dict:
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in regla.items() if k != "malla"}


def exportar(t: Trazado, alturas: Alturas, carpeta) -> dict:
    """Escribe data/ciudad/transito.json, rejilla.png y rebaje.png. Devuelve las cifras."""
    import rejilla as RJ

    grupos = []
    nuevo = {}
    triangulados = []
    for i, g in enumerate(t.grupos):
        if g.malla is not None:
            vertices = [(float(x), float(y)) for x, y in g.malla.puntos]
            triangulos = [int(v) for v in g.malla.triangulos.ravel()]
        else:
            vertices, triangulos = _triangular(g.forma)
        if not triangulos:
            continue
        nuevo[i] = len(grupos)
        triangulados.append((g, vertices, triangulos))
        registro = {
            "clase": g.clase,
            "regla": _regla_json(g.regla),
            "angulo": g.angulo,
            "elevado": g.elevado,
            "puntos": [v for xy in vertices for v in xy],
            "triangulos": triangulos,
        }
        if g.malla is not None:
            registro["z"] = [round(float(v), 2 if g.clase == "firme" else 3) for v in g.malla.z]
            # La textura, si no es la del plano (la del firme roto lo es: no hace falta).
            if g.clase != "firme":
                registro["uv"] = [float(v) for v in g.malla.uv.ravel()]
        grupos.append(registro)
    malla = RJ.calcular(t, alturas, triangulados)
    for registro, planos, rectas in zip(grupos, malla.planos, malla.rectas):
        # Las mallas propias van enteras: no les hacen falta.
        if "z" not in registro:
            registro["planos"] = planos
            registro["rectas"] = rectas
    meta_rejilla = RJ.exportar_png(malla, carpeta)
    aristas = [{"tipo": a.tipo, "izq": nuevo[a.izq], "der": nuevo.get(a.der, -1) if a.der >= 0 else -1,
                "puntos": [v for xy in a.puntos for v in (round(xy[0], DECIMALES), round(xy[1], DECIMALES))],
                **({"huecos": a.huecos} if a.huecos else {}),
                **({"movidos": a.movidos} if a.movidos else {})}
               for a in t.aristas if a.izq in nuevo]
    datos = {
        "version": 1,
        "niveles": {c: v["nivel"] for c, v in CLASES.items()},
        "rodadas": [c for c, v in CLASES.items() if v["rodada"]],
        "rebaje": REBAJE,
        "rasante": {"archivo": "rasante.png", "codificacion": "metros = valor / 100 - 50",
                    "filas": "la primera fila es el borde norte"},
        "grupos": grupos,
        "aristas": aristas,
        "muros": t.muros,
        "barandillas": t.barandillas,
        "escaleras": [{**e, "grupos": [nuevo[i] for i in e["grupos"] if i in nuevo]} for e in t.escaleras],
        "marcas": t.marcas,
        "detalles": {**{k: v for k, v in t.detalles.items() if k not in ("restos", "matojos", "baches")},
                     "restos": columnas(t.detalles.get("restos", []), PIEZAS),
                     "matojos": columnas(t.detalles.get("matojos", []),
                                         {"pos": 2, "z": 2, "angulo": 0, "escala": 2, "alto": 2}),
                     "baches": columnas(t.detalles.get("baches", []),
                                        {"pos": 2, "z": 3, "angulo": 0, "escala": 2, "gx": 3, "gy": 3})},
        "puente": {**t.puente, "regla": _regla_json(t.puente["regla"]),
                   "vano_hundido": list(_calle("puente_progreso")["vano_hundido"]),
                   "tablero": _calle("puente_progreso")["tablero"]},
        **meta_rejilla,
        **_exportar_ferrocarril(t, alturas),
        "socavones": [_socavon_json(item, nuevo) for item in t.socavones],
        "placas": t.placas,
        "grietas": t.grietas,
        "tendido": {"lineas": [{"grosor": c["grosor"], "puntos": c["puntos"]} for c in t.tendido.get("lineas", [])]},
        "relleno": {"triangulos": [ident for ident, _ in malla.rellenos],
                    "puntos": [v for _, esquinas in malla.rellenos for xy in esquinas for v in xy]},
    }
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    (carpeta / "transito.json").write_text(texto, encoding="utf-8")
    estados = malla.estados & 3
    return {
        "grupos": len(grupos),
        "triangulos": sum(len(g["triangulos"]) // 3 for g in grupos),
        "aristas": len(aristas),
        "rejilla": {"enteros": int((estados == RJ.ENTERO).sum()), "borde": int((estados == RJ.BORDE).sum()),
                    "hondos": int((estados == RJ.HONDO).sum()), "anillo": int(((malla.estados & RJ.ANILLO) > 0).sum()),
                    "rellenos": len(malla.rellenos)},
        "tendido": t.tendido.get("cifras", {}),
        "kb": round(len(texto) / 1024),
    }


# ---------------------------------------------------------------------------
# Comprobaciones
# ---------------------------------------------------------------------------
def comprobar(t: Trazado, alturas: Alturas) -> list[str]:
    """Lo que tiene que cumplir la red de tránsito (lo usa `plano.py --comprobar`)."""
    problemas = []
    partes, duenos = [], []
    for i, g in enumerate(t.grupos):
        if not g.forma.is_valid:
            problemas.append(f"Tránsito: el grupo {i} ({g.clase}) no es válido")
        for p in poligonos(g.forma):
            partes.append(p)
            duenos.append(i)
    arbol = STRtree(partes)
    a, b = arbol.query(partes, predicate="intersects")
    for i, j in zip(a, b):
        if i < j and duenos[i] != duenos[j]:
            comun = partes[i].intersection(partes[j]).area
            if comun > 0.05:
                problemas.append(f"Tránsito: los grupos {duenos[i]} y {duenos[j]} se solapan {comun:.2f} m²")
    for e in t.escaleras:
        pisadas = e["pisadas"]
        for (s0, s1, z), (_, _, z_sig) in zip(pisadas, pisadas[1:]):
            if not 0.12 <= z_sig - z <= 0.18:
                problemas.append(f"{e['nombre']}: contrahuella de {z_sig - z:.3f} m en s = {s1:.1f}")
        for s0, s1, _ in pisadas[1:-1]:
            if s1 - s0 < 0.27 or 0.40 < s1 - s0 < 1.0:
                problemas.append(f"{e['nombre']}: huella de {s1 - s0:.2f} m en s = {s0:.1f}")
    # Lo alto de la Escalinata, a ras de la plaza de la cabeza.
    x, y = eje(ESCALINATA_CABEZA + 1.0)
    cabeza = float(alturas.base({"tipo": "terreno"}, [x], [y])[0]) + NIVEL_PEATON
    alto = t.escaleras[0]["pisadas"][-1][2]
    if abs(cabeza - alto) > JUNTA:
        problemas.append(f"La Escalinata acaba a {alto:.2f} m y la plaza de la cabeza está a {cabeza:.2f} m")
    for arista in t.aristas:
        if arista.tipo == "bordillo" and not CLASES[t.grupos[arista.izq].clase]["rodada"]:
            problemas.append(f"Tránsito: bordillo sin calzada a la izquierda en {arista.puntos[0]}")
    rio = D.RIO.buffer(0.5)
    for i, g in enumerate(t.grupos):
        if g.elevado and not g.forma.within(rio):
            problemas.append(f"Tránsito: el grupo elevado {i} ({g.clase}) se sale del río")
    import deterioro as DT

    pavimento = unary_union([g.forma for g in t.grupos if not g.elevado and g.clase != "socavon"])
    problemas += DT.comprobar(unary_union([pavimento, DT.huecos()]))
    for item in t.socavones:
        g = t.grupos[item["grupo"]]
        z_borde = alturas.z(g, *g.malla.puntos[: len(item["socavon"].borde)].T)
        calle = float(np.mean(z_borde)) + DT.CAPA
        fondo = float(np.min(g.malla.z))
        if calle - fondo < 0.9 * item["socavon"].datos["hondo"]:
            problemas.append(f"Socavón {item['socavon'].ident}: solo baja {calle - fondo:.2f} m")
    return problemas
