"""El plano de Tumansk: dónde está cada cosa.

Este archivo es la fuente de verdad de la ciudad. Todo lo que hay en la superficie
y bajo ella se decide aquí, con su posición en metros (x hacia el este, y hacia el
norte; ver geo.py). `plano.py` lo valida, calcula los daños, lo exporta a
data/ciudad/plano.json y dibuja los planos de docs/ciudad/.

Orden: catálogo, zonas, río, calles, ferrocarril y tranvía, edificios zona por
zona, patios, vallas y sendas, vehículos, hitos, puntos de interés, subsuelo,
amenazas, peligros, límites y rutas.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import relieve as R
from geo import (
    ALTO,
    ANCHO,
    a_eje,
    banda,
    caja,
    circulo,
    eje,
    elipse,
    forma_h,
    forma_l,
    poligono,
    rect,
    rect_eje,
    sector_anular,
)


def azar(clave: str) -> float:
    """Número fijo entre 0 y 1 para cada clave (no cambia entre ejecuciones)."""
    return int(hashlib.md5(clave.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Catálogo de tipos de edificio (medidas reales de las series soviéticas)
# ---------------------------------------------------------------------------
# grupo: vivienda, servicios, industria, especial, madera, ruina, menor
# planta: altura de cada piso en metros; extra: cubierta, remates o agujas.
TIPOS: dict[str, dict] = {
    "jrushchovka": {"nombre": "Jrushchovka: bloque de 5 plantas de los años 60", "grupo": "vivienda", "pisos": 5, "planta": 2.8, "extra": 1.5},
    "bloque9": {"nombre": "Bloque de paneles de 9 plantas (años 70)", "grupo": "vivienda", "pisos": 9, "planta": 2.8, "extra": 2.5},
    "torre16": {"nombre": "Torre de 16 plantas (años 80)", "grupo": "vivienda", "pisos": 16, "planta": 2.8, "extra": 3.5},
    "estalinka": {"nombre": "Casa estalinista: viviendas con comercios en los bajos", "grupo": "vivienda", "pisos": 7, "planta": 3.4, "extra": 3.0},
    "estalinka_baja": {"nombre": "Casa obrera estalinista de 2 o 3 plantas", "grupo": "vivienda", "pisos": 3, "planta": 3.2, "extra": 3.0},
    "prerrevolucion": {"nombre": "Casa de ladrillo anterior a la revolución", "grupo": "vivienda", "pisos": 3, "planta": 3.8, "extra": 2.5},
    "barracon": {"nombre": "Barracón de madera de 2 plantas (años 30)", "grupo": "madera", "pisos": 2, "planta": 3.0, "extra": 2.5},
    "casa_madera": {"nombre": "Casa de madera (isba) con huerto", "grupo": "madera", "pisos": 1, "planta": 3.0, "extra": 3.0},
    "torre_estalinista": {"nombre": "Torre estalinista con aguja", "grupo": "especial", "pisos": 14, "planta": 3.4, "extra": 14.0},
    "escuela": {"nombre": "Escuela de proyecto tipo", "grupo": "servicios", "pisos": 3, "planta": 3.6, "extra": 1.5},
    "guarderia": {"nombre": "Guardería de proyecto tipo", "grupo": "servicios", "pisos": 2, "planta": 3.3, "extra": 1.5},
    "comercio": {"nombre": "Pabellón comercial o de servicios", "grupo": "servicios", "pisos": 1, "planta": 4.5, "extra": 1.0},
    "publico": {"nombre": "Edificio público", "grupo": "servicios", "pisos": 3, "planta": 4.0, "extra": 3.0},
    "monumental": {"nombre": "Edificio público monumental", "grupo": "especial", "pisos": 4, "planta": 5.0, "extra": 6.0},
    "oficinas": {"nombre": "Oficinas", "grupo": "servicios", "pisos": 5, "planta": 3.5, "extra": 2.0},
    "hospital": {"nombre": "Edificio hospitalario", "grupo": "servicios", "pisos": 4, "planta": 3.5, "extra": 2.0},
    "hotel": {"nombre": "Hotel de los años 70", "grupo": "servicios", "pisos": 14, "planta": 3.0, "extra": 3.0},
    "nave": {"nombre": "Nave industrial con cubierta en diente de sierra", "grupo": "industria", "pisos": 1, "planta": 16.0, "extra": 2.0},
    "almacen": {"nombre": "Almacén", "grupo": "industria", "pisos": 1, "planta": 8.0, "extra": 2.0},
    "industrial": {"nombre": "Edificio industrial", "grupo": "industria", "pisos": 2, "planta": 5.0, "extra": 2.0},
    "deposito_circular": {"nombre": "Depósito, silo o tanque", "grupo": "industria", "pisos": 1, "planta": 15.0, "extra": 0.0},
    "torre_refrigeracion": {"nombre": "Torre de refrigeración", "grupo": "industria", "pisos": 1, "planta": 80.0, "extra": 0.0},
    "chimenea": {"nombre": "Chimenea", "grupo": "industria", "pisos": 1, "planta": 45.0, "extra": 0.0},
    "garajes": {"nombre": "Hilera de garajes de una cooperativa", "grupo": "menor", "pisos": 1, "planta": 2.8, "extra": 0.4},
    "cobertizo": {"nombre": "Cobertizo, trastero o caseta", "grupo": "menor", "pisos": 1, "planta": 2.6, "extra": 0.6},
    "transformador": {"nombre": "Centro de transformación", "grupo": "menor", "pisos": 1, "planta": 3.5, "extra": 0.5},
    "quiosco": {"nombre": "Quiosco", "grupo": "menor", "pisos": 1, "planta": 2.8, "extra": 0.4},
    "pabellon": {"nombre": "Pabellón", "grupo": "servicios", "pisos": 1, "planta": 5.0, "extra": 4.0},
    "iglesia": {"nombre": "Iglesia antigua", "grupo": "especial", "pisos": 1, "planta": 12.0, "extra": 8.0},
    "torre": {"nombre": "Torre o mástil", "grupo": "especial", "pisos": 1, "planta": 30.0, "extra": 0.0},
    "muralla": {"nombre": "Muralla", "grupo": "especial", "pisos": 1, "planta": 7.0, "extra": 0.0},
    "ruina": {"nombre": "Ruina: lo que queda en pie", "grupo": "ruina", "pisos": 2, "planta": 3.0, "extra": 0.0},
    "tienda_campana": {"nombre": "Tienda de campaña de la evacuación", "grupo": "menor", "pisos": 1, "planta": 2.6, "extra": 0.0},
    "monton": {"nombre": "Montones a cielo abierto (carbón, chatarra)", "grupo": "monton", "pisos": 1, "planta": 6.0, "extra": 0.0},
    "estadio": {"nombre": "Gradas del estadio", "grupo": "servicios", "pisos": 1, "planta": 9.0, "extra": 3.0},
}

GRUPOS = {
    "vivienda": "Viviendas",
    "servicios": "Comercio, servicios y equipamientos",
    "industria": "Industria y transporte",
    "especial": "Edificio singular",
    "madera": "Madera",
    "ruina": "Ruina",
    "menor": "Construcción menor",
    "monton": "Montones a cielo abierto",
}

# ---------------------------------------------------------------------------
# Zonas: de la estación hacia fuera. Cuanto más lejos, más peligro y más valor.
# ---------------------------------------------------------------------------
ZONAS: dict[int, dict] = {
    0: {"nombre": "La Estación", "salida": "—",
        "resumen": "Bajo la plaza del Trabajo: tu depósito, el pasillo, la escalera mecánica y la compuerta. Siempre segura."},
    1: {"nombre": "La Plaza", "salida": "10–20 min", "rotulo": (230, 172),
        "resumen": "La plaza redonda del Trabajo con el Monumento al Minero, las dos torres que abren la avenida, el vestíbulo "
        "del metro, el paso subterráneo, el primer patio y, al sur, la plaza de la Estación con el tren de la evacuación."},
    2: {"nombre": "Los Bloques", "salida": "20–40 min", "rotulo": (190, 438),
        "resumen": "Microdistrito de los años 60 a 80: jrushchovkas en hileras, bloques de 9 plantas, la Torre de 16, "
        "la escuela, dos guarderías, la sala de calderas, los garajes y la playa."},
    3: {"nombre": "La Avenida y el Mercado", "salida": "30–60 min", "rotulo": (760, 626),
        "resumen": "La avenida del Progreso hasta el puente: el Mercado Central con su cúpula, los Grandes Almacenes, "
        "el cine Cosmos, el depósito de trolebuses, el socavón y el paso subterráneo del Mercado."},
    4: {"nombre": "El Barrio Obrero", "salida": "30–50 min", "rotulo": (600, 58),
        "resumen": "El barrio que se levantó para la fábrica: el Palacio de la Cultura, la panificadora, los baños públicos, "
        "los bomberos con su torre, la comisaría, barracones de madera y la iglesia vieja junto a la vía."},
    5: {"nombre": "La Zona Industrial", "salida": "45–60 min", "rotulo": (1110, 290),
        "resumen": "La fábrica de maquinaria, la playa de vías, el puerto con sus grúas y el elevador de grano, "
        "la central térmica (una chimenea caída, una torre agrietada) y el parque de carbón, que aún humea."},
    6: {"nombre": "El Parque y el Hospital", "salida": "Unos 60 min", "rotulo": (190, 1056),
        "resumen": "Al otro lado del río, por el tubo o por el hielo: el parque de la Cultura con su colina, la torre de "
        "paracaídas y el estadio, y el Hospital Clínico Nº 3 con el campamento de la Cruz Roja."},
    7: {"nombre": "El Centro", "salida": "60–90 min", "rotulo": (1130, 850),
        "resumen": "Sobre la loma: la ciudad vieja (la fortaleza en el cabo del barranco y el barrio de los mercaderes) y el "
        "centro estalinista (la Escalinata, la plaza Central, la Casa de los Sóviets, el teatro, el hotel, el circo, la universidad). "
        "En el fondo del barranco, las casas de madera."},
    8: {"nombre": "La Zona Cero", "salida": "Gran expedición: 60 min – 3 h", "rotulo": (1430, 1000),
        "resumen": "Donde cayó la bomba: el nudo ferroviario y la Planta Nº 1 convertidos en cráter. Muy cerca, el "
        "Edificio Partido, el antiguo Instituto Nº 9. Aquí está la respuesta sobre tu padre."},
}


def _orilla_sur(x0: float, x1: float) -> list:
    paso = 25 if x1 > x0 else -25
    return [(x, float(R.orilla_sur(x))) for x in range(int(x0), int(x1) + paso, paso)]


def _orilla_norte(x0: float, x1: float) -> list:
    paso = 25 if x1 > x0 else -25
    return [(x, float(R.orilla_norte(x))) for x in range(int(x0), int(x1) + paso, paso)]


_BARRANCO_OESTE = [(608, 772), (612, 830), (626, 880), (648, 935), (662, 990), (662, 1045), (656, 1090), (650, 1200)]

ZONA_POLIGONOS: dict[int, Polygon] = {
    1: poligono([(305, 337), (305, 250), eje(-170, 54), eje(-262, 54), (150, 140), (150, 40), (352, 40), (352, 130),
                 (322.5, 130), (390, 205), (560, 205), (560, 322), (575, 321), (575, 424), eje(170, 0), (523, 490),
                 (345, 490), (345, 337)]),
    2: poligono([(0, 40), (150, 40), (150, 140), eje(-262, 54), eje(-170, 54), (305, 250), (305, 337), (345, 337)]
                + _orilla_sur(345, 0)),
    3: poligono([(345, 490), (523, 490), eje(170, 0), (575, 424), (575, 323), (848, 312)] + _orilla_sur(848, 345)),
    4: poligono([(352, 40), (848, 40), (848, 312), (560, 322), (560, 205), (390, 205), (322.5, 130), (352, 130)]),
    5: poligono([(848, 40), (1600, 40)] + _orilla_sur(1600, 848)),
    6: poligono(_orilla_norte(0, 600) + _BARRANCO_OESTE + [(0, 1200)]),
    7: poligono(_orilla_norte(600, 1245) + [(1245, 1200)] + list(reversed(_BARRANCO_OESTE))),
    8: poligono(_orilla_norte(1245, 1600) + [(1600, 1200), (1245, 1200)]),
}


def zona_de(x: float, y: float) -> int:
    p = Point(x, y)
    for numero, poly in ZONA_POLIGONOS.items():
        if poly.buffer(0.5).contains(p):
            return numero
    return 0


# ---------------------------------------------------------------------------
# El río
# ---------------------------------------------------------------------------
def _poligono_rio() -> Polygon:
    xs = list(range(-60, 1661, 10))
    return poligono([(x, float(R.orilla_sur(x))) for x in xs] + [(x, float(R.orilla_norte(x))) for x in reversed(xs)])


RIO = _poligono_rio()
ESTANQUE = elipse(240, 884, 62, 28, 8)

# ---------------------------------------------------------------------------
# Calles
# ---------------------------------------------------------------------------
# tipo: avenida, principal, calle, servicio, peatonal, puente, escalinata, camino
# ancho: de fachada a fachada (incluye las aceras).
CALLES: list[dict] = []


def calle(ident: str, nombre: str, tipo: str, ancho: float, puntos: list, rotulo: bool = True, **extra) -> None:
    CALLES.append({"id": ident, "nombre": nombre, "tipo": tipo, "ancho": ancho, "puntos": puntos, "rotulo": rotulo, **extra})


PLAZAS: list[dict] = []


def plaza(ident: str, nombre: str, forma: Polygon, rotulo: bool = True, **extra) -> None:
    PLAZAS.append({"id": ident, "nombre": nombre, "forma": forma, "rotulo": rotulo, **extra})


# --- Orilla sur ---
calle("avenida_progreso", "Avenida del Progreso", "avenida", 76, [eje(-262), eje(372)], calzada=54, mediana=16,
      notas="Ocho carriles con el tranvía por la mediana. Atasco de la evacuación hacia el metro y hacia el puente.")
calle("puente_progreso", "Puente del Progreso", "puente", 32, [eje(372), eje(632)], tablero=3.0, vano_hundido=(470, 545),
      notas="Tres vanos de hormigón. El central se hundió y descansa inclinado sobre el hielo.")
calle("mineros_oeste", "Calle de los Mineros", "principal", 40, [(-10, 345), (348, 336)])
calle("mineros_este", "Calle de los Mineros", "principal", 36, [(512, 326), (850, 312), (1300, 300), (1600, 296)])
calle("juventud", "Calle de la Juventud", "calle", 24, [(345, 336), (345, 640)])
calle("autovia_servicio", "Calle de la Autovía", "calle", 18, [(30, 40), (30, 690)])
calle("muelle_sur", "Muelle Sur", "calle", 22,
      [(-10, 659), (200, 647), (340, 632), (500, 614), (640, 606), (700, 604), (760, 606), (848, 612)])
calle("correo", "Calle del Correo", "calle", 18, [(345, 490), (523, 490)])
calle("corta", "Calle Corta", "servicio", 12, [(305, 318), (305, 248)])
calle("constructores", "Calle de los Constructores", "calle", 14, [(135, 100), (135, 318)])
calle("cine", "Calle del Cine", "calle", 18, [(575, 326), (575, 426)])
calle("deposito", "Calle del Depósito", "calle", 18, [(700, 320), (700, 606)])
calle("fabrica", "Calle de la Fábrica", "principal", 28, [(848, 40), (848, 650)])
calle("trabajo", "Calle del Trabajo", "calle", 18, [(370, 205), (848, 205)])
calle("octubre", "Calle de Octubre", "calle", 18, [(352, 130), (848, 130)])
calle("ferroviarios", "Calle de los Ferroviarios", "calle", 14, [(352, 70), (848, 68)])
calle("paz", "Calle de la Paz", "calle", 18, [(560, 70), (560, 322)])
calle("pioneros", "Calle de los Pioneros", "calle", 16, [(700, 70), (700, 320)])
calle("molino", "Calle del Molino", "servicio", 14, [(450, 70), (450, 205)])
calle("vias", "Calle de las Vías", "calle", 16, [(862, 181), (1290, 181)])
calle("puerto", "Calle del Puerto", "calle", 22, [(1228, 300), (1228, 612)])
calle("dique", "Calle del Dique", "calle", 16, [(862, 615), (1345, 615)])
calle("paso_bloques", "Paso de los Bloques", "servicio", 10, [(30, 398), (300, 398), (345, 398)], rotulo=False)
calle("escuela", "Calle de la Escuela", "servicio", 12, [(30, 582), (345, 582)])
calle("paso_garajes", "Paso de los Garajes", "servicio", 10, [(30, 140), (135, 140)], rotulo=False)
calle("paso_bloques_sur", "Paso de las Hileras", "servicio", 8, [(30, 240), (135, 240)], rotulo=False)
calle("paso_ribera", "Paso de la Ribera", "servicio", 10, [(709, 464), (834, 464)], rotulo=False)

# --- Orilla norte ---
calle("muelle_norte", "Muelle Norte", "calle", 22,
      [(330, 818), (500, 799), (640, 790), (800, 787), (1000, 796), (1200, 790), (1350, 773), (1545, 742)])
calle("paseo_parque", "Paseo del Parque", "peatonal", 10, [(-10, 853), (150, 839), (330, 818)])
calle("hospital", "Calle del Hospital", "calle", 24, [(340, 818), (340, 1205)])
calle("norte", "Calle Norte", "calle", 18, [(340, 1188), (720, 1188), (803, 1198)])
calle("escalinata", "La Escalinata", "escalinata", 40, [eje(632), eje(800)],
      notas="Escalera monumental con descansillos, en el eje de la avenida: sube 11 m por la loma.")
calle("bajada", "La Bajada", "calle", 16, [(850, 798), (780, 812), (752, 830), (775, 852), (815, 870), eje(700, 64)],
      notas="Rampa en zigzag por la que el tráfico y el tranvía suben del puente a la ciudad vieja.")
calle("bulevar_rio", "Bulevar del Río", "peatonal", 12,
      [(x, float(R.orilla_norte(x)) + 104.0) for x in range(890, 1250, 30)])
calle("sovietica", "Calle Soviética", "calle", 18, [eje(700, 64), eje(1088, 64)])
calle("ribera_alta", "Calle de la Ribera Alta", "calle", 18, [eje(812, -64), eje(1130, -64)])
calle("cosmonautas", "Calle de los Cosmonautas", "calle", 18, [eje(782, 184), eje(1003, 184)])
calle("barranco_alto", "Calle del Barranco Alto", "calle", 14, [eje(790, 303), eje(895, 303)])
calle("mirador", "Calle del Mirador", "calle", 18, [eje(791, -52), eje(791, 330)])
calle("teatro_n", "Calle del Teatro", "calle", 16, [eje(923, 60), eje(923, 262)])
calle("teatro_s", "Calle del Teatro", "calle", 16, [eje(923, -190), eje(923, -60)], rotulo=False)
calle("comite", "Calle del Comité", "calle", 16, [eje(998, -178), eje(998, 150)])
calle("planta", "Calle de la Planta", "calle", 26, [eje(990), (1180, 1100), (1262, 1092), (1340, 1066), (1392, 1040)],
      notas="Antiguo eje hacia la Planta Nº 1. Pasado el centro está cegada de escombros.")
calle("universidad", "Calle de la Universidad", "calle", 16, [eje(1108, -80), eje(1108, 60)])
calle("instituto", "Calle del Instituto", "calle", 16, [(1245, 930), (1320, 948), (1400, 960)])
calle("fortaleza", "Calle de la Fortaleza", "calle", 12, [eje(700, 64), (815, 908), (782, 936), (762, 975), (752, 1020), (747, 1075), (742, 1112)])
calle("mercaderes", "Calle de los Mercaderes", "calle", 12, [eje(791, 150), (812, 1000), (784, 984), (762, 975)])
calle("pozo", "Callejón del Pozo", "servicio", 8, [(782, 936), (812, 955), (830, 990), (848, 1018)])
calle("barranco", "Calle del Barranco", "camino", 6, [(652, 790), (660, 850), (676, 905), (694, 960), (700, 1015), (694, 1070)],
      notas="Camino de tierra por el fondo del barranco, entre las casas de madera.")

# --- Plazas ---
plaza("plaza_trabajo", "Plaza del Trabajo", circulo(430, 330, 85, 64),
      notas="Plaza redonda. Glorieta de 30 m de radio con el Monumento al Minero en la isleta.")
plaza("plaza_estacion", "Plaza de la Estación", caja(180, 66, 305, 140))
plaza("puente_sur", "Plaza del Puente", poligono([eje(352, -40), eje(392, -40), eje(392, 40), eje(352, 40)]), rotulo=False)
plaza("puente_norte", "Plaza del Puente Norte", poligono([eje(612, -46), eje(648, -46), eje(648, 46), eje(612, 46)]), rotulo=False)
plaza("plaza_central", "Plaza Central", rect_eje(800, 921, -55, 55))
plaza("plaza_palacio", "Plaza del Palacio", caja(588, 291, 672, 306), rotulo=False)
plaza("plaza_vieja", "Plaza Vieja", poligono([(790, 930), (812, 922), (826, 948), (800, 960)]), rotulo=False)


def _union_calles() -> Polygon:
    formas = [banda(c["puntos"], c["ancho"]) for c in CALLES if c["tipo"] != "camino"]
    return unary_union(formas + [p["forma"] for p in PLAZAS])


CALLES_UNION = _union_calles()

# ---------------------------------------------------------------------------
# Ferrocarril, tranvía, trolebús y tuberías
# ---------------------------------------------------------------------------
VIA_PRINCIPAL = [
    (-20, 34), (300, 34), (600, 37), (850, 42), (1100, 46), (1300, 52), (1430, 68), (1510, 105), (1550, 170),
    (1562, 260), (1562, 420), (1557, 560), (1552, 640), (1548, 740), (1538, 820), (1515, 920), (1492, 1010), (1480, 1060),
]
TERRAPLENES = [
    {"puntos": [(-20, 34), (300, 34), (600, 37), (860, 42)], "alto": 5.0, "corona": 14.0, "talud": 10.0},
    {"puntos": [(1480, 80), (1530, 130), (1556, 200), (1562, 300), (1562, 420), (1557, 560), (1554, 620)],
     "alto": 6.0, "corona": 10.0, "talud": 12.0},
    {"puntos": [(1548, 742), (1548, 760), (1538, 820), (1515, 920), (1492, 1010)], "alto": 4.0, "corona": 10.0,
     "talud": 10.0},
]
# Las vías del ferrocarril. Cada vía es un cuerpo (sus puntos: las esquinas se redondean
# con el radio de su clase) y, en cada punta, cómo se une a otra vía: con un desvío en la
# vía madre, "desde" al principio del cuerpo y "hasta" al final. El desvío se da con
# {"via": madre, "marca": "1/9" o "1/6", "radio": de la curva que lleva al cuerpo} y dónde
# está la aguja: en la madre a la altura de "x" o en la proyección del punto "en"; si no
# se da, donde haga falta para llegar al cuerpo con una sola curva ("entre" acota en x
# dónde buscarla). El trazado final lo hace ferrocarril.red(): el abanico de la playa de
# vías del plano no se puede construir con agujas (salían diez vías de un mismo punto), así
# que la playa entra por un escape en diagonal del que van saliendo sus vías.
VIAS: list[dict] = [
    {"id": "principal", "nombre": "Línea del ferrocarril", "puntos": VIA_PRINCIPAL, "tipo": "principal"},
    {"id": "anden_1", "nombre": "Vía de andén", "tipo": "secundaria", "puntos": [(120, 22), (330, 22)],
     "desde": {"via": "principal", "marca": "1/9", "x": -20.0, "radio": 300.0},
     "hasta": {"via": "principal", "marca": "1/9", "x": 478.0, "radio": 300.0}},
    {"id": "anden_2", "nombre": "Vía de andén", "tipo": "secundaria", "puntos": [(120, 44), (330, 44)],
     "desde": {"via": "principal", "marca": "1/9", "x": 8.0, "radio": 300.0},
     "hasta": {"via": "principal", "marca": "1/9", "x": 450.0, "radio": 300.0}},
    {"id": "fabrica", "nombre": "Apartadero de la fábrica", "tipo": "secundaria",
     "puntos": [(928, 210), (936, 300), (940, 372)],
     "desde": {"via": "principal", "marca": "1/6", "radio": 120.0, "entre": (760.0, 850.0)}},
    {"id": "escape_playa", "nombre": "Escape de la playa de vías", "tipo": "playa",
     "puntos": [(914.6, 56.1), (1093.5, 150.0), (1245.0, 150.0)],
     "desde": {"via": "principal", "marca": "1/6", "x": 860.0, "radio": 100.0}},
    {"id": "playa_1", "nombre": "Playa de vías", "tipo": "playa", "puntos": [(1040.0, 60.0), (1125.0, 60.0)],
     "desde": {"via": "principal", "marca": "1/9", "x": 885.0, "radio": 150.0},
     "hasta": {"via": "principal", "marca": "1/9", "x": 1280.0, "radio": 150.0}},
    {"id": "puerto", "nombre": "Vía del muelle", "tipo": "secundaria",
     "puntos": [(1302, 300), (1305.9, 636), (880, 636)],
     "desde": {"via": "escape_playa", "marca": "1/6", "radio": 120.0, "entre": (1120.0, 1240.0)}},
    {"id": "carbon", "nombre": "Apartadero del carbón", "tipo": "secundaria", "puntos": [(1480, 237), (1400, 240)],
     "desde": {"via": "principal", "marca": "1/6", "en": (1562.0, 345.0), "radio": 100.0}},
    {"id": "combustible", "nombre": "Apartadero del combustible", "tipo": "secundaria",
     "puntos": [(1360, 68), (1440, 84)],
     "desde": {"via": "principal", "marca": "1/6", "x": 1320.0, "radio": 200.0}},
]
# Las vías de la playa: rectas de 10 en 10 m, que salen del escape (la de arriba es el
# propio escape, que acaba en ella) y acaban en un tope.
for _i in range(1, 9):
    _y = 60.0 + 10.0 * _i
    VIAS.append({"id": f"playa_{_i + 1}", "nombre": "Playa de vías", "tipo": "playa",
                 "puntos": [(910.0 + 20.0 * _i + 60.0, _y), (1245.0, _y)],
                 "desde": {"via": "escape_playa", "marca": "1/6", "radio": 120.0, "entre": (880.0, 1100.0)}})

PUENTE_FERROCARRIL = {"puntos": [(1553, 622), (1548, 752)], "ancho": 14, "nombre": "Puente del Ferrocarril",
                      "notas": "Celosía de acero intacta. Muy cerca del rastro de la lluvia radiactiva."}

TRANVIAS: list[dict] = [
    {"id": "tranvia_1", "nombre": "Tranvía 1: Estación – Plaza – Centro – Planta",
     "puntos": [(250, 100), eje(-262), eje(-85), eje(0, -85), eje(85), eje(632), (850, 798), (780, 812), (752, 830), (775, 852),
                (815, 870), eje(700, 64), eje(998, 64), eje(998, 0), (1180, 1100), (1262, 1092), (1340, 1066)]},
    {"id": "tranvia_3", "nombre": "Tranvía 3: Plaza – Fábrica – Puerto",
     "puntos": [(515, 326), (850, 312), (1228, 302), (1228, 600), (1180, 615), (1100, 615)]},
]
TROLEBUSES: list[dict] = [
    {"id": "trolebus_2", "nombre": "Trolebús 2: Bloques – Plaza – Depósito",
     "puntos": [(30, 345), (348, 336), (512, 326), (700, 320), (700, 380)]},
]
TUBERIAS: list[dict] = [
    {"id": "magistral", "nombre": "Tubería magistral de calefacción", "puntos": [(1300, 324), (1100, 324), (866, 326)], "elevada": True},
    {"id": "bloques", "nombre": "Tubería de la sala de calderas",
     "puntos": [(75, 126), (100, 132), (100, 300), (100, 393), (140, 393), (240, 393)], "elevada": True,
     "notas": "Cruza la calle de los Mineros en un arco de tubos, a 5 m de altura."},
    {"id": "carbon", "nombre": "Cinta transportadora del carbón", "puntos": [(1462, 282), (1440, 345)], "elevada": True,
     "notas": "Galería elevada; se puede trepar por ella."},
    {"id": "tubo_rio", "nombre": "El tubo: tubería sobre el río", "puntos": [(322, 640), (324, 690), (326, 760), (330, 820)], "elevada": True,
     "notas": "Dos tubos aislados con una pasarela de servicio. La pasarela peatonal que iba al lado se cayó al río."},
]
LINEAS_ELECTRICAS = [
    {"id": "alta_tension", "nombre": "Línea de alta tensión", "puntos": [(1300, 230), (1240, 150), (1180, 30), (1170, -10)],
     "torres": [(1300, 230), (1240, 150), (1180, 30)]},
]

# ---------------------------------------------------------------------------
# Edificios
# ---------------------------------------------------------------------------
EDIFICIOS: list[dict] = []
_MANZANAS: dict[str, Polygon] = {}


def edificio(ident: str, tipo: str, nombre: str, huella: Polygon, zona: int, pisos: int | None = None, uso: str = "viviendas",
             altura: float | None = None, dano: int | None = None, incendio: str | None = None, notas: str = "",
             interior: str = "tipo", manzana: str | None = None, sotano: bool = True, **extra) -> dict | None:
    """Añade un edificio. Dentro de una misma `manzana`, cada edificio nuevo se recorta
    contra los anteriores (así las esquinas de las casas estalinistas encajan solas).

    interior: "tipo" (distribución de la serie, generada), "a_mano" (sitio clave hecho a
    mano), "nave" (espacio diáfano), "ninguno" (no se entra: torres, depósitos).
    """
    datos = TIPOS[tipo]
    if manzana is not None:
        previo = _MANZANAS.get(manzana)
        if previo is not None:
            huella = huella.difference(previo)
        _MANZANAS[manzana] = huella if previo is None else unary_union([previo, huella])
    if huella.is_empty:
        return None
    if huella.geom_type in ("MultiPolygon", "GeometryCollection"):
        huella = max((g for g in huella.geoms if g.geom_type == "Polygon"), key=lambda g: g.area)
    pisos = datos["pisos"] if pisos is None else pisos
    if altura is None:
        altura = round(pisos * datos["planta"] + datos["extra"], 1)
    registro = {"id": ident, "tipo": tipo, "nombre": nombre, "zona": zona, "pisos": pisos, "altura": altura, "uso": uso,
                "dano": dano, "incendio": incendio, "notas": notas, "interior": interior, "sotano": sotano, "huella": huella, **extra}
    EDIFICIOS.append(registro)
    return registro


def garajes(ident: str, nombre: str, forma: Polygon, zona: int, **extra) -> None:
    edificio(ident, "garajes", nombre, forma, zona, uso="garajes (3 × 6 m cada uno)", sotano=False, **extra)


def menor(ident: str, tipo: str, nombre: str, forma: Polygon, zona: int, uso: str = "", **extra) -> None:
    edificio(ident, tipo, nombre, forma, zona, uso=uso or nombre.lower(), sotano=False, **extra)


def manzana_perimetral(prefijo: str, bloque: Polygon, zona: int, fondo: float = 16.0, pisos=(6, 7, 8),
                       nombre: str = "Casa estalinista", clave: str | None = None, huecos: bool = True,
                       tipo: str = "estalinka") -> list[dict]:
    """Casas en el perímetro de una manzana, una por lado, con alturas distintas y algún
    hueco (un lado que nunca se construyó o que se vino abajo). Así se hicieron de verdad:
    por fases, cada lado con su proyecto."""
    if bloque.is_empty:
        return []
    if bloque.geom_type in ("MultiPolygon", "GeometryCollection"):
        partes = sorted((g for g in bloque.geoms if g.geom_type == "Polygon" and g.area > 400), key=lambda g: -g.area)
        creados = []
        for n, parte in enumerate(partes):
            creados += manzana_perimetral(f"{prefijo}{'abcdef'[n]}", parte, zona, fondo, pisos, nombre, clave, huecos, tipo)
        return creados
    bloque = orient(bloque.simplify(0.5), sign=1.0)
    pts = list(bloque.exterior.coords)[:-1]
    lados = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        largo = math.dist(a, b)
        if largo >= 14:
            lados.append((largo, i, a, b))
    lados.sort(reverse=True)
    creados = []
    clave = clave or prefijo
    for k, (largo, i, a, b) in enumerate(lados):
        r = azar(f"{prefijo}/{i}")
        if huecos and r < 0.14 and len(lados) > 3 and k > 0:
            continue
        ux, uy = (b[0] - a[0]) / largo, (b[1] - a[1]) / largo
        nx, ny = -uy, ux
        franja = Polygon([(a[0] - ux * fondo, a[1] - uy * fondo), (b[0] + ux * fondo, b[1] + uy * fondo),
                          (b[0] + ux * fondo + nx * fondo, b[1] + uy * fondo + ny * fondo),
                          (a[0] - ux * fondo + nx * fondo, a[1] - uy * fondo + ny * fondo)]).intersection(bloque)
        piso = pisos[int(azar(f"{prefijo}/{i}/p") * len(pisos)) % len(pisos)]
        e = edificio(f"{prefijo}-{len(creados) + 1}", tipo, f"{nombre} {len(creados) + 1}", franja, zona,
                     pisos=piso, manzana=clave, uso="viviendas; comercios en los bajos" if k < 2 else "viviendas")
        if e is not None and e["huella"].area < 120:
            EDIFICIOS.remove(e)
        elif e is not None:
            creados.append(e)
    return creados


# ===========================================================================
# ZONA 1 · LA PLAZA
# ===========================================================================
_PT = (430.0, 330.0)
edificio("PLZ-02", "torre_estalinista", "Torre Norte", rect_eje(76, 100, 38, 62), 1, pisos=14, altura=62.0, manzana="plz_norte",
         uso="viviendas", notas="Una de las dos torres que abren la avenida. Aguja con estrella.", hito=1)
edificio("PLZ-01", "estalinka", "Casa Curva Norte", sector_anular(*_PT, 85, 103, 89, 128), 1, manzana="plz_norte",
         uso="viviendas; Correos y Telégrafos Nº 1 y librería en los bajos", interior="a_mano",
         notas="Fachada curva. Arco al primer patio. La oficina de correos guarda paquetes sin repartir.")
edificio("PLZ-07", "estalinka", "Banco del Estado", rect_eje(100, 150, 38, 54), 1, pisos=6, manzana="plz_norte",
         uso="sucursal del Banco del Estado", interior="a_mano",
         notas="El dinero ya no vale nada, pero la cámara acorazada es un refugio casi perfecto: una sola puerta.")
edificio("PLZ-08", "estalinka", "Juventud 1", caja(357, 360, 373, 481).difference(circulo(*_PT, 103, 64)), 1, manzana="plz_norte")
edificio("PLZ-09", "estalinka", "Correo 2", caja(357, 465, 500, 481), 1, pisos=6, manzana="plz_norte")
edificio("PLZ-03", "torre_estalinista", "Torre Este", rect_eje(76, 100, -62, -38), 1, pisos=14, altura=62.0, manzana="plz_este",
         uso="viviendas", notas="Gemela de la Torre Norte. La estrella de la aguja cuelga torcida.", hito=1)
edificio("PLZ-04", "estalinka", "Casa de la Proa", rect_eje(100, 143, -54, -38), 1, pisos=8, manzana="plz_este",
         uso="viviendas; café Avenida y relojería en los bajos", notas="En la cubierta, las letras ¡GLORIA AL TRABAJO!, algunas caídas.", hito=2)
edificio("PLZ-13", "estalinka", "Mineros 2", caja(527, 346, 566, 362), 1, pisos=6, manzana="plz_este",
         uso="viviendas; restaurante Minero en los bajos")
edificio("PLZ-14", "estalinka", "Cine 1", caja(550, 346, 566, 392), 1, pisos=6, manzana="plz_este")
edificio("PLZ-05", "estalinka", "Casa Curva Sur", sector_anular(*_PT, 85, 103, 262, 340), 1, manzana="plz_sur",
         uso="viviendas; Gastronom Nº 1, farmacia Nº 1 y peluquería en los bajos", interior="a_mano",
         notas="El Gastronom tiene la persiana a medio arrancar y el almacén de atrás intacto.")
edificio("PLZ-10", "estalinka", "Paz 1", caja(535, 214, 551, 306), 1, pisos=6, manzana="plz_sur")
edificio("PLZ-11", "estalinka", "Trabajo 2", caja(376, 214, 551, 230).difference(banda([eje(-262), eje(0)], 108)), 1, pisos=5,
         manzana="plz_sur")
edificio("PLZ-12", "estalinka", "Avenida 11", rect_eje(-100, -78, -54, -38), 1, manzana="plz_sur", uso="viviendas; óptica y discos")
edificio("PLZ-06", "pabellon", "Vestíbulo del metro", poligono([(311, 317), (311, 255), (350.9, 298.9), (346, 317)]), 1,
         pisos=2, altura=20.0, uso="vestíbulo de la estación (tu salida)", interior="a_mano",
         notas="Rotonda con columnas y cúpula. Dentro, la compuerta. Sus otras puertas están soldadas desde abajo.")
edificio("PLZ-15", "estalinka", "Avenida 14", rect_eje(-205, -152, 38, 54), 1, uso="viviendas; panadería y zapatería")
edificio("PLZ-16", "estalinka", "Avenida 16", rect_eje(-252, -210, 38, 54), 1, uso="viviendas; farmacia Nº 9")
edificio("PLZ-17", "estalinka", "Avenida 13", rect_eje(-182, -150, -54, -38), 1, uso="viviendas; librería y relojería")
edificio("PLZ-18", "estalinka", "Avenida 15", rect_eje(-220, -188, -54, -38), 1, uso="viviendas; tienda de ropa")
edificio("PLZ-20", "monumental", "Estación de Tumansk", unary_union([caja(170, 46, 310, 64), rect(240, 56, 18, 18)]), 1,
         pisos=3, altura=45.0, uso="estación de ferrocarril", interior="a_mano", hito=4,
         notas="Torre del reloj parado a las 4:12. Vestíbulo lleno de equipaje de la evacuación.")
edificio("PLZ-21", "comercio", "Autoestación", caja(152, 74, 178, 128), 1, pisos=2, altura=9.0, uso="estación de autobuses",
         notas="Marquesinas hundidas por la nieve.")
edificio("PLZ-22", "estalinka", "Hotel Estación", caja(328, 66, 350, 118), 1, pisos=5, uso="hotel")
edificio("PLZ-23", "pabellon", "Entrada sellada del metro", rect(205, 132, 10, 6), 1, pisos=1, altura=4.0,
         uso="acceso a la estación Ferrocarril (fuera del mapa)", interior="ninguno",
         notas="Sellada por el gobierno civil. Al otro lado sigue la red habitada.")
edificio("PLZ-24", "pabellon", "Monumento al Minero", circulo(*_PT, 6), 1, pisos=1, altura=12.0, uso="monumento",
         interior="ninguno", sotano=False, hito=3, notas="Estatua de bronce sobre un pedestal de granito. Le falta el brazo.")
# Los quioscos del anillo de la Plaza (dos, apartados de la curva del tranvía).
for _i, _a in enumerate([100, 118, 280, 255, 350]):
    _x, _y = _PT[0] + 74 * math.cos(math.radians(_a)), _PT[1] + 74 * math.sin(math.radians(_a))
    menor(f"PLZ-Q{_i + 1}", "quiosco", "Quiosco", rect(_x, _y, 4, 3, _a), 1, uso="quiosco")
for _i, (_x, _y) in enumerate([(196, 82), (290, 84), (192, 130), (296, 128)]):
    menor(f"PLZ-Q{_i + 6}", "quiosco", "Quiosco", rect(_x, _y, 4, 3), 1, uso="quiosco")
for _i, (_x, _y) in enumerate([(214, 92), (226, 92), (214, 104), (226, 104)]):
    menor(f"PLZ-C{_i + 1}", "tienda_campana", "Tienda de la evacuación", rect(_x, _y, 9, 7), 1, uso="puesto de la evacuación")
# El primer patio (detrás de la Casa Curva Norte)
menor("PLZ-P1", "cobertizo", "Trasteros del primer patio", caja(380, 440, 398, 448), 1)
menor("PLZ-P2", "cobertizo", "Trasteros del primer patio", caja(410, 448, 440, 456), 1)
menor("PLZ-P3", "cobertizo", "Palomar", rect(404, 432, 5, 5), 1, uso="palomar")
menor("PLZ-T1", "transformador", "Centro de transformación", caja(522, 236, 530, 242), 1, uso="electricidad")
menor("PLZ-P4", "cobertizo", "Trasteros del patio sur", caja(490, 232, 516, 238), 1)

# ===========================================================================
# ZONA 2 · LOS BLOQUES
# ===========================================================================
# Bloques Norte: entre Mineros, la Juventud, la Autovía y el río.
edificio("BLQ-09", "bloque9", "Mineros 9", caja(48, 370, 128, 383), 2, uso="viviendas; oficina de correos de barrio")
edificio("BLQ-07", "bloque9", "Mineros 7", caja(146, 368, 242, 381), 2,
         uso="viviendas; farmacia Nº 14, universam y lavandería en los bajos", interior="a_mano", ocupante="inquilino_a",
         notas="El bloque con inquilino. La farmacia tiene antibióticos; el universam, conservas. Todo está a su alcance.")
edificio("BLQ-05", "bloque9", "Mineros 5", caja(262, 366, 326, 379), 2, uso="viviendas; ultramarinos")
edificio("BLQ-J4", "bloque9", "Juventud 4", caja(313, 425, 326, 505), 2)
edificio("BLQ-J6", "bloque9", "Juventud 6", caja(313, 520, 326, 568), 2, notas="Tres portales.")
edificio("BLQ-TORRE", "torre16", "La Torre", rect(300, 604, 26, 22), 2, interior="a_mano", hito=5,
         notas="La única de 16 plantas. La escalera está hundida en la planta 11: hace falta cuerda o tablón. "
         "Desde la azotea se ve toda la orilla sur y el otro lado del río.")
edificio("BLQ-K1", "jrushchovka", "Escuela 3", caja(64, 415, 76, 479), 2)
edificio("BLQ-K2", "jrushchovka", "Escuela 5", caja(64, 497, 76, 561), 2)
edificio("BLQ-K3", "jrushchovka", "Escuela 7", caja(109, 425, 121, 489), 2)
edificio("BLQ-K4", "jrushchovka", "Escuela 9", caja(109, 505, 121, 569), 2, notas="Jrushchovka de ladrillo (otra serie).")
edificio("BLQ-K5", "jrushchovka", "Escuela 11", caja(154, 410, 166, 474), 2)
edificio("BLQ-K6", "jrushchovka", "Escuela 13", caja(154, 500, 166, 548), 2, notas="Tres portales en vez de cuatro.")
edificio("BLQ-ESC", "escuela", "Escuela Nº 21", forma_h(240, 485, 84, 16, 54, 16, 0), 2, interior="a_mano",
         uso="escuela; refugio de defensa civil en el sótano",
         notas="En el sótano, el refugio de defensa civil: máscaras antiguas, filtros caducados y un dosímetro de manivela.")
edificio("BLQ-G7", "guarderia", "Guardería Nº 7 «Campanilla»", forma_h(120, 618, 50, 12, 30, 12, 0), 2,
         uso="guardería", notas="Los porches del patio son buenos escondites.")
for _i, _x in enumerate([84, 100, 140, 156]):
    menor(f"BLQ-G7P{_i + 1}", "cobertizo", "Porche de la guardería", rect(_x, 596, 8, 6), 2, uso="porche")
edificio("BLQ-R5", "bloque9", "Muelle Sur 5", caja(166, 603, 246, 616), 2)
edificio("BLQ-CTP", "industrial", "Punto de calor", caja(250, 416, 266, 428), 2, pisos=1, altura=5.0, uso="subestación de calefacción",
         interior="nave")
menor("BLQ-T1", "transformador", "Centro de transformación", caja(134, 408, 142, 414), 2, uso="electricidad")
menor("BLQ-T2", "transformador", "Centro de transformación", caja(196, 590, 204, 596), 2, uso="electricidad")
garajes("BLQ-GA4", "Garajes de chapa", caja(42, 420, 52, 560), 2, notas="Casetas metálicas de los vecinos.")
# Bloques Sur: entre la vía, la Autovía, Mineros y la avenida.
edificio("BLQ-08", "bloque9", "Mineros 8", caja(46, 296, 122, 309), 2, uso="viviendas; casa de comidas")
edificio("BLQ-06", "bloque9", "Mineros 6", caja(148, 298, 244, 311), 2, uso="viviendas; zapatero y reparación de radios")
edificio("BLQ-04", "bloque9", "Mineros 4", caja(256, 296, 292, 309), 2, notas="Dos portales.")
edificio("BLQ-K7", "jrushchovka", "Constructores 2", caja(64, 160, 76, 224), 2)
edificio("BLQ-K8", "jrushchovka", "Constructores 4", caja(108, 170, 120, 234), 2)
edificio("BLQ-K9", "jrushchovka", "Constructores 3", caja(152, 160, 164, 224), 2)
edificio("BLQ-K10", "jrushchovka", "Constructores 6", caja(64, 250, 76, 282), 2, notas="Bloque corto de dos portales.")
edificio("BLQ-K11", "jrushchovka", "Constructores 5", caja(194, 174, 206, 238), 2)
edificio("BLQ-G21", "guarderia", "Guardería Nº 21 «Estrellita»", forma_h(232, 262, 46, 12, 28, 12, 0), 2, uso="guardería")
edificio("BLQ-CAL", "industrial", "Sala de calderas Nº 4", caja(45, 108, 75, 126), 2, pisos=1, altura=10.0,
         uso="calefacción del microdistrito", interior="nave", notas="Montaña de carbón helada en el patio. La tubería sale de aquí.")
edificio("BLQ-CHI", "chimenea", "Chimenea de la sala de calderas", circulo(80, 118, 3), 2, altura=45.0, uso="chimenea",
         interior="ninguno", sotano=False, hito=6)
edificio("BLQ-BYT", "comercio", "Casa de servicios «Aurora»", caja(92, 100, 124, 126), 2, pisos=2, altura=9.0,
         uso="reparaciones, sastrería, estudio de fotografía y lavandería", notas="Herramientas, hilo, película fotográfica y relojes a medio arreglar.")
garajes("BLQ-GA1", "Cooperativa de garajes «Volga»", caja(45, 56, 132, 68), 2, notas="Madriguera de la Jauría.")
garajes("BLQ-GA2", "Cooperativa de garajes «Volga»", caja(45, 76, 132, 88), 2, notas="Madriguera de la Jauría.")
garajes("BLQ-GA3", "Cooperativa de garajes «Volga»", caja(86, 250, 96, 290), 2)
menor("BLQ-T3", "transformador", "Centro de transformación", caja(178, 196, 186, 202), 2, uso="electricidad")
menor("BLQ-PLY", "cobertizo", "Torre de socorristas", rect(250, 672, 4, 4), 2, uso="playa", altura=7.0)
menor("BLQ-VES", "cobertizo", "Vestuarios de la playa", caja(120, 664, 150, 670), 2, uso="playa")

# ===========================================================================
# ZONA 3 · LA AVENIDA Y EL MERCADO
# ===========================================================================
edificio("AVM-01", "monumental", "Mercado Central", rect_eje(192, 276, 44, 92), 3, pisos=1, altura=22.0, uso="mercado cubierto",
         interior="nave", hito=7, notas="Nave con cúpula de hormigón. Puestos de madera quemados; en el sótano, cámaras frigoríficas y ratas.")
edificio("AVM-03", "jrushchovka", "Juventud 9", caja(362, 505, 374, 569), 3)
edificio("AVM-08", "jrushchovka", "Juventud 11", caja(362, 580, 374, 610), 3, notas="Dos portales.")
edificio("AVM-04", "jrushchovka", "Correo 5", caja(390, 505, 454, 517), 3)
edificio("AVM-05", "publico", "Cine Cosmos", caja(385, 572, 445, 604), 3, pisos=2, altura=14.0, uso="cine", interior="a_mano",
         notas="Mosaico de cosmonautas en la fachada del río. La cabina de proyección cierra por dentro.")
garajes("AVM-06", "Garajes de la Juventud", caja(455, 528, 467, 590), 3)
edificio("AVM-10", "monumental", "Grandes Almacenes", rect_eje(190, 272, -86, -38), 3, pisos=4, altura=19.0, uso="grandes almacenes",
         interior="a_mano", hito=8, notas="Vigía de los saqueadores en la azotea, junto al letrero. Dentro: ropa, menaje, radios y juguetes.")
edificio("AVM-11", "estalinka", "Avenida 30", rect_eje(282, 326, -54, -38), 3, uso="viviendas; óptica y estanco")
edificio("AVM-16", "estalinka", "Mineros 14", caja(590, 344, 686, 360), 3, pisos=6, uso="viviendas; casa de comidas", manzana="avm_cine")
edificio("AVM-17", "estalinka", "Cine 6", caja(586, 344, 602, 428), 3, manzana="avm_cine")
edificio("AVM-20", "jrushchovka", "Depósito 1", caja(672, 372, 684, 436), 3)
garajes("AVM-21", "Garajes del Cine", caja(612, 372, 660, 382), 3)
menor("AVM-T1", "transformador", "Centro de transformación", caja(646, 398, 654, 404), 3, uso="electricidad")
edificio("AVM-12", "nave", "Depósito de trolebuses", caja(722, 380, 822, 440), 3, altura=12.0, uso="cocheras", interior="nave",
         notas="Veinte trolebuses en fila. Taller con fosos, baterías y herramientas.")
edificio("AVM-12B", "oficinas", "Oficinas del depósito", caja(722, 344, 790, 358), 3, pisos=2)
edificio("AVM-22", "comercio", "Gasolinera Nº 6", caja(800, 344, 830, 356), 3, pisos=1, altura=5.0, uso="gasolinera",
         notas="Depósitos enterrados con algo de gasóleo. Marquesina caída sobre los surtidores.")
edificio("AVM-14", "jrushchovka", "Depósito 8", caja(712, 480, 724, 544), 3)
edificio("AVM-19", "jrushchovka", "Depósito 3", caja(756, 480, 768, 544), 3)
edificio("AVM-23", "guarderia", "Guardería Nº 30 «Ardilla»", forma_h(796, 512, 46, 12, 24, 12, 90), 3, uso="guardería")
edificio("AVM-15", "jrushchovka", "Fábrica 4", caja(820, 478, 832, 542), 3)
edificio("AVM-13", "bloque9", "Ribera 3", caja(718, 572, 814, 585), 3)
edificio("AVM-18", "comercio", "Club náutico", caja(600, 618, 650, 632), 3, pisos=1, altura=6.0, uso="club de remo",
         notas="Botes y piraguas apilados. Cuerda, remos y lonas.")
for _i, (_x, _y, _a) in enumerate([(533, 488, 48), (604, 512, 48), (632, 590, 48)]):
    menor(f"AVM-Q{_i + 1}", "quiosco", "Quiosco", rect(_x, _y, 4, 3, _a), 3, uso="quiosco")

# ===========================================================================
# ZONA 4 · EL BARRIO OBRERO
# ===========================================================================
edificio("OBR-01", "monumental", "Palacio de la Cultura «Metalúrgico»", unary_union([caja(592, 236, 668, 280), caja(612, 280, 648, 290)]),
         4, pisos=3, altura=24.0, uso="palacio de la cultura: teatro, biblioteca, círculos", interior="a_mano", hito=11,
         notas="Pórtico de columnas a la plaza del Palacio. Biblioteca, cabina de proyección y almacén de defensa civil.")
edificio("OBR-02", "estalinka_baja", "Anexo del Palacio", caja(578, 214, 638, 228), 4, pisos=2, uso="círculos y talleres")
edificio("OBR-02B", "estalinka_baja", "Taller del Palacio", caja(650, 214, 688, 228), 4, pisos=1, uso="carpintería del teatro")
edificio("OBR-03", "industrial", "Panificadora Nº 1", caja(720, 238, 800, 282), 4, pisos=2, uso="fábrica de pan", interior="nave",
         notas="Hornos, sacos de harina podrida, azúcar en las tolvas. Muchas ratas.")
edificio("OBR-03B", "almacen", "Almacén de harina", caja(712, 216, 760, 230), 4, altura=7.0, interior="nave")
for _i, _y in enumerate([248, 262, 276]):
    edificio(f"OBR-03S{_i + 1}", "deposito_circular", "Silo de harina", circulo(814, _y, 5), 4, altura=18.0, uso="silo",
             interior="ninguno", sotano=False)
edificio("OBR-03C", "chimenea", "Chimenea de la panificadora", circulo(812, 226, 2), 4, altura=30.0, interior="ninguno", sotano=False)
edificio("OBR-04", "escuela", "Escuela Nº 2", forma_l(380, 146, 58, 44, 15), 4, pisos=4, uso="escuela (años 30)")
edificio("OBR-05", "estalinka_baja", "Trabajo 9", caja(462, 176, 546, 190), 4)
edificio("OBR-06", "estalinka_baja", "Octubre 12", caja(462, 143, 546, 157), 4)
edificio("OBR-07", "publico", "Baños públicos Nº 3", caja(580, 150, 630, 186), 4, pisos=2, altura=9.0, uso="baños",
         notas="Calderas, azulejo, bancos de madera. Las taquillas guardan ropa de abrigo.")
edificio("OBR-07C", "chimenea", "Chimenea de los baños", circulo(637, 160, 2), 4, altura=28.0, interior="ninguno", sotano=False)
edificio("OBR-08", "estalinka_baja", "Paz 14", caja(645, 143, 688, 157), 4)
edificio("OBR-09", "estalinka_baja", "Trabajo 13", caja(645, 178, 688, 192), 4)
edificio("OBR-10", "publico", "Parque de bomberos Nº 2", caja(712, 150, 772, 190), 4, pisos=2, altura=10.0, uso="bomberos",
         interior="a_mano", notas="Cuerdas, hachas, equipos de respiración y trajes ignífugos.")
edificio("OBR-11", "torre", "Torre de bomberos", rect(782, 184, 8, 8), 4, altura=30.0, uso="torre de vigilancia", interior="a_mano",
         sotano=False, hito=9, notas="Escalera interior hasta la garita: mirador sobre todo el sur.")
edificio("OBR-12", "estalinka_baja", "Fábrica 21", caja(794, 143, 832, 157), 4)
edificio("OBR-24", "estalinka_baja", "Pioneros 6", caja(794, 168, 830, 182), 4, pisos=2)
for _i, _c in enumerate([caja(362, 85, 392, 96), caja(362, 104, 392, 115), caja(402, 85, 432, 96), caja(402, 104, 432, 115)]):
    edificio(f"OBR-B{_i + 1}", "barracon", "Barracón", _c, 4, incendio="total" if _i == 2 else None, notas="Pasillo central y cocinas comunes.")
edificio("OBR-17", "publico", "Comisaría de la Milicia", caja(465, 84, 515, 114), 4, pisos=3, altura=11.0, uso="comisaría",
         interior="a_mano", notas="Armero vacío. En el depósito de pruebas: ganzúas, radios y pilas.")
garajes("OBR-18", "Garajes de la comisaría", caja(522, 84, 546, 114), 4)
edificio("OBR-19", "prerrevolucion", "Casa del Comerciante", caja(575, 84, 615, 112), 4, pisos=2, notas="La casa más vieja del barrio. Sótano abovedado.")
edificio("OBR-20", "prerrevolucion", "Ferroviarios 14", caja(625, 84, 688, 98), 4, pisos=2)
for _i, (_x, _y) in enumerate([(632, 110), (650, 110), (668, 110)]):
    edificio(f"OBR-M{_i + 1}", "casa_madera", "Casa de madera", rect(_x, _y, 9, 8), 4, incendio="total" if _i == 1 else None)
edificio("OBR-21", "iglesia", "Iglesia vieja", unary_union([rect(762, 100, 28, 16), rect(742, 100, 9, 9)]), 4, altura=36.0,
         uso="almacén (antes iglesia)", interior="a_mano", hito=10,
         notas="Usada como almacén desde los años 30. El campanario es un buen mirador sobre la vía y la playa de vías.")
for _i, _c in enumerate([caja(475, 162, 491, 168), caja(515, 162, 531, 168), caja(578, 114, 590, 120), caja(712, 110, 730, 116),
                         caja(366, 98, 380, 102), caja(410, 98, 428, 102)]):
    menor(f"OBR-C{_i + 1}", "cobertizo", "Cobertizos y palomares", _c, 4, uso="trasteros")

# ===========================================================================
# ZONA 5 · LA ZONA INDUSTRIAL
# ===========================================================================
# Al sur de Mineros: mercancías, locomotoras, camiones, hormigón, chatarra, subestación y carbón.
edificio("IND-07", "almacen", "Estación de mercancías", caja(870, 192, 900, 288), 5, altura=7.0, interior="nave",
         notas="Muelles de carga con vagones a medio descargar.")
edificio("IND-01", "nave", "Depósito de locomotoras", sector_anular(960, 212, 20, 44, 20, 160), 5, altura=12.0, uso="cocheras de locomotoras",
         interior="nave", notas="Rotonda con placa giratoria. Tres locomotoras dentro.")
edificio("IND-02", "nave", "Base de camiones", caja(1030, 200, 1110, 236), 5, altura=8.0, uso="garaje de camiones", interior="nave",
         notas="Combustible en bidones, baterías, neumáticos, herramientas.")
edificio("IND-02B", "oficinas", "Oficina de la base", caja(1030, 250, 1070, 264), 5, pisos=2)
edificio("IND-03", "torre", "Planta de hormigón", rect(1172, 232, 14, 14), 5, altura=38.0, uso="torre de mezcla", interior="a_mano", sotano=False)
edificio("IND-03B", "almacen", "Nave de áridos", caja(1135, 200, 1160, 262), 5, altura=8.0, interior="nave")
for _i, _y in enumerate([212, 228, 248]):
    edificio(f"IND-03S{_i + 1}", "deposito_circular", "Silo de cemento", circulo(1198, _y, 5), 5, altura=20.0, interior="ninguno", sotano=False)
edificio("IND-08", "monton", "Chatarrería", caja(1214, 192, 1246, 262), 5, altura=4.0, uso="montones de chatarra", interior="ninguno",
         sotano=False, notas="Coches aplastados, motores, cable. Mucho botín y mucho ruido al moverse por encima.")
edificio("IND-04", "industrial", "Subestación eléctrica", caja(1258, 262, 1298, 274), 5, pisos=1, altura=6.0, uso="sala de control",
         notas="Patio de transformadores vallado detrás (aceite derramado).")
edificio("IND-05", "monton", "Parque de carbón", caja(1390, 196, 1520, 280), 5, pisos=1, altura=9.0, uso="montañas de carbón",
         interior="ninguno", sotano=False, notas="El carbón arde por dentro desde la Noche. Humo constante; hace falta máscara.")
for _i, (_x, _y, _r) in enumerate([(1330, 106, 15), (1372, 106, 15), (1414, 112, 13), (1342, 146, 13)]):
    edificio(f"IND-06T{_i + 1}", "deposito_circular", "Tanque de combustible", circulo(_x, _y, _r), 5, altura=14.0, uso="combustible",
             interior="ninguno", sotano=False, notas="Reventado: mancha negra helada alrededor." if _i == 1 else "")
edificio("IND-06", "oficinas", "Oficina del depósito de combustible", caja(1300, 160, 1330, 172), 5, pisos=1)
# Al norte de Mineros: la fábrica.
edificio("IND-10", "nave", "Nave 1 (fundición)", caja(880, 336, 1060, 370), 5, altura=18.0, interior="nave")
edificio("IND-11", "nave", "Nave 2 (montaje)", caja(880, 384, 1060, 420), 5, altura=18.0, interior="nave",
         notas="Grúa puente caída sobre la cadena de montaje.")
edificio("IND-12", "nave", "Nave 3 (mecanizado)", caja(880, 434, 1060, 470), 5, altura=18.0, interior="nave",
         notas="Cubierta hundida: se camina por la nieve entre las máquinas.")
edificio("IND-09", "nave", "Nave 4 (forja)", caja(880, 484, 980, 520), 5, altura=14.0, interior="nave")
edificio("IND-09B", "industrial", "Compresores", caja(990, 484, 1030, 504), 5, pisos=1, altura=8.0)
edificio("IND-09C", "transformador", "Subestación de la fábrica", caja(1040, 484, 1060, 500), 5)
edificio("IND-09D", "almacen", "Almacén de modelos", caja(880, 530, 960, 552), 5, interior="nave")
edificio("IND-13", "oficinas", "Administración de la fábrica", caja(1080, 334, 1150, 350), 5, interior="a_mano",
         notas="Mosaico de obreros en el vestíbulo. Archivo, caja fuerte y la radio de la fábrica.")
edificio("IND-13B", "oficinas", "Laboratorio de la fábrica", caja(1160, 334, 1205, 350), 5, pisos=3)
edificio("IND-14", "industrial", "Comedor de la fábrica", caja(1080, 362, 1130, 386), 5, pisos=2, uso="comedor")
edificio("IND-14B", "industrial", "Garaje de la fábrica", caja(1140, 362, 1205, 386), 5, pisos=1, altura=6.0)
edificio("IND-15", "torre", "Depósito de agua de la fábrica", circulo(1190, 420, 7), 5, altura=34.0, uso="depósito de agua", interior="a_mano",
         sotano=False, hito=12)
edificio("IND-16", "nave", "Talleres", caja(1080, 400, 1170, 440), 5, altura=9.0, interior="nave")
edificio("IND-17", "almacen", "Almacén de la fábrica", caja(1080, 460, 1200, 500), 5, interior="nave")
menor("IND-18", "cobertizo", "Refugio de defensa civil de la fábrica", rect(1160, 522, 10, 6), 5, uso="acceso al búnker", interior="a_mano",
      notas="Escalera a un búnker para 300 personas: máscaras, filtros, raciones y dosímetros.")
menor("IND-19", "cobertizo", "Garita de la puerta", rect(1070, 336, 8, 5), 5, uso="control de acceso")
# El puerto
edificio("IND-20", "almacen", "Almacén 1", caja(885, 572, 985, 604), 5, interior="nave", notas="Cajas de conservas reventadas por el hielo.")
edificio("IND-21", "almacen", "Almacén 2", caja(1000, 572, 1100, 604), 5, interior="nave", notas="Frigorífico del puerto.")
edificio("IND-22", "almacen", "Almacén 3", caja(1115, 572, 1205, 604), 5, interior="a_mano", ocupante="saqueadores",
         notas="Guarida principal de los saqueadores: muros de contenedores, sacos terreros, fuego y guardia en la cubierta.")
edificio("IND-23", "industrial", "Elevador de grano", unary_union([caja(1256, 566, 1306, 600), rect(1248, 583, 12, 30)]), 5, pisos=1,
         altura=60.0, uso="silos de grano", interior="a_mano", hito=13, notas="Silos de 45 m y torre de 60. Vigía de los saqueadores arriba del todo.")
edificio("IND-24", "oficinas", "Oficina del puerto", caja(1312, 570, 1342, 592), 5, pisos=3)
for _i, _x in enumerate([930, 1020, 1110, 1200]):
    edificio(f"IND-G{_i + 1}", "torre", "Grúa del puerto", rect(_x, 640, 12, 10), 5, altura=35.0, uso="grúa pórtico", interior="a_mano",
             sotano=False, hito=14 if _i == 0 else None,
             notas="Cabina a 25 m con una sola escalera: buen mirador y buen refugio." if _i == 1 else "")
# La central térmica
edificio("IND-30", "industrial", "Sala de calderas y turbinas", caja(1300, 345, 1430, 405), 5, pisos=1, altura=45.0, uso="central térmica",
         interior="nave")
edificio("IND-31", "chimenea", "Chimenea de la central (en pie)", circulo(1478, 378, 7), 5, altura=150.0, interior="ninguno", sotano=False, hito=15)
edificio("IND-32", "chimenea", "Base de la chimenea caída", circulo(1452, 424, 7), 5, altura=12.0, interior="ninguno", sotano=False,
         notas="Cayó hacia el sur: el fuste cruza la calle de los Mineros como un puente y acaba en el parque de carbón.")
edificio("IND-32B", "ruina", "Fuste de la chimenea caída", poligono([(1446, 415), (1458, 415), (1452, 284), (1444, 284)]), 5, pisos=1,
         altura=9.0, dano=4, interior="ninguno", sotano=False, notas="Se puede caminar por encima… y por dentro.")
edificio("IND-33", "torre_refrigeracion", "Torre de refrigeración 1", circulo(1352, 482, 34), 5, altura=80.0, interior="nave", sotano=False, hito=16)
edificio("IND-34", "torre_refrigeracion", "Torre de refrigeración 2 (agrietada)", circulo(1462, 492, 34), 5, altura=66.0, interior="nave",
         sotano=False, hito=16, notas="Le falta un tercio de la corona.")
edificio("IND-35", "industrial", "Toma de agua", caja(1420, 590, 1462, 612), 5, pisos=2, uso="bombas del río")
edificio("IND-36", "industrial", "Tratamiento de agua", caja(1262, 520, 1300, 552), 5, pisos=2)
edificio("IND-37", "deposito_circular", "Tanque de fuel", circulo(1520, 350, 10), 5, altura=12.0, interior="ninguno", sotano=False)
edificio("IND-39", "deposito_circular", "Tanque de fuel", circulo(1520, 382, 10), 5, altura=12.0, interior="ninguno", sotano=False)
edificio("IND-38", "oficinas", "Administración de la central", caja(1250, 330, 1286, 350), 5, pisos=3)
edificio("IND-40", "industrial", "Sala de control de la central", caja(1250, 400, 1290, 430), 5, pisos=2)
edificio("IND-41", "almacen", "Almacén de la central", caja(1250, 440, 1300, 465), 5, interior="nave")
edificio("IND-42", "industrial", "Transformadores de la central", caja(1484, 418, 1540, 450), 5, pisos=1, altura=6.0, interior="ninguno")

# ===========================================================================
# ZONA 6 · EL PARQUE Y EL HOSPITAL
# ===========================================================================
edificio("PHO-01", "monumental", "Arco del Parque", caja(314, 944, 326, 976), 6, pisos=1, altura=14.0, uso="puerta del parque",
         interior="ninguno", sotano=False)
edificio("PHO-02", "torre", "Torre de paracaídas", circulo(105, 958, 4), 6, altura=35.0, uso="atracción", interior="a_mano", sotano=False,
         hito=19, notas="En lo alto de la colina. La plataforma ve el parque, el río y la orilla sur. Se oye todo desde lejos.")
edificio("PHO-03", "pabellon", "Monumento a los Caídos", circulo(216, 960, 6), 6, altura=18.0, uso="obelisco y llama", interior="ninguno", sotano=False)
edificio("PHO-04", "pabellon", "La Concha (escenario)", caja(236, 1046, 264, 1060), 6, altura=10.0, uso="escenario")
edificio("PHO-05", "pabellon", "Pista de baile", circulo(172, 1048, 16), 6, altura=4.0, uso="pista de baile vallada", sotano=False)
edificio("PHO-06", "pabellon", "Café «Primavera»", caja(290, 912, 312, 926), 6, altura=6.0, uso="café")
edificio("PHO-07", "pabellon", "Embarcadero del estanque", caja(296, 868, 312, 880), 6, altura=5.0, uso="barcas")
edificio("PHO-08", "pabellon", "Pabellón de ajedrez", rect(252, 1004, 14, 10), 6, altura=5.0, uso="ajedrez y dominó")
menor("PHO-09", "cobertizo", "Aseos del parque", caja(298, 1096, 310, 1104), 6, uso="aseos")
for _i, (_x, _y, _r) in enumerate([(290, 1012, 8), (276, 986, 7)]):
    edificio(f"PHO-A{_i + 1}", "pabellon", "Atracción", circulo(_x, _y, _r), 6, altura=8.0, uso="tiovivo y columpios", interior="ninguno", sotano=False)
_ESTADIO = (142.0, 1136.0)
_GRADAS = elipse(*_ESTADIO, 80, 52).difference(elipse(*_ESTADIO, 62, 36))
edificio("PHO-10", "estadio", "Estadio «Metalurg»: tribuna oeste", _GRADAS.difference(caja(142, 1000, 300, 1200)), 6, uso="gradas")
edificio("PHO-11", "estadio", "Estadio «Metalurg»: tribuna este", _GRADAS.difference(caja(0, 1000, 142, 1200)), 6, uso="gradas",
         ocupante="jauria_b", notas="Bajo las gradas, la madriguera de la segunda jauría.")
for _i, (_x, _y) in enumerate([(70, 1088), (214, 1088), (70, 1184), (214, 1184)]):
    edificio(f"PHO-F{_i + 1}", "torre", "Torre de focos del estadio", rect(_x, _y, 3, 3), 6, altura=40.0, interior="ninguno", sotano=False, hito=20)
edificio("PHO-12", "comercio", "Administración del parque", caja(280, 1150, 306, 1164), 6, pisos=1)
# Hospital Clínico Nº 3
edificio("HOS-01", "hospital", "Hospital Nº 3: edificio principal", forma_h(500, 1010, 104, 16, 74, 16, 0), 6, pisos=8, interior="a_mano",
         ocupante="inquilino_b", uso="hospital: plantas, quirófanos; farmacia en el sótano",
         notas="El edificio con el segundo inquilino. La farmacia del sótano guarda insulina y antibióticos.")
edificio("HOS-02", "hospital", "Policlínica", caja(380, 870, 444, 886), 6, pisos=4, uso="consultas")
edificio("HOS-03", "hospital", "Casa de Maternidad", caja(520, 880, 570, 894), 6, pisos=5, uso="maternidad")
edificio("HOS-04", "hospital", "Pabellón de infecciosos", caja(584, 1090, 596, 1130), 6, pisos=2, uso="aislamiento")
edificio("HOS-05", "hospital", "Morgue", caja(390, 1112, 414, 1124), 6, pisos=1, uso="anatomía patológica",
         notas="Radiación alta: aquí trajeron a los primeros muertos de la Noche.")
edificio("HOS-06", "industrial", "Calderas y lavandería", caja(505, 1124, 535, 1142), 6, pisos=1, altura=9.0, interior="nave")
edificio("HOS-06C", "chimenea", "Chimenea del hospital", circulo(542, 1150, 2), 6, altura=40.0, interior="ninguno", sotano=False)
edificio("HOS-07", "industrial", "Garaje de ambulancias", caja(432, 1146, 468, 1156), 6, pisos=1, altura=5.0)
edificio("HOS-10", "hospital", "Residencia de enfermeras", caja(368, 1040, 382, 1100), 6, pisos=5, uso="viviendas del personal")
edificio("HOS-11", "industrial", "Cocina del hospital", caja(566, 960, 596, 978), 6, pisos=1, altura=6.0)
edificio("HOS-12", "hospital", "Laboratorio", caja(566, 1058, 596, 1074), 6, pisos=2)
edificio("HOS-13", "almacen", "Almacén del hospital", caja(470, 1080, 520, 1094), 6, altura=6.0, interior="nave")
menor("HOS-08", "cobertizo", "Estación de oxígeno", caja(586, 1040, 594, 1048), 6, uso="botellas de oxígeno")
menor("HOS-09", "cobertizo", "Garita del hospital", rect(358, 962, 6, 4), 6, uso="control")
for _i, (_x, _y) in enumerate([(396, 930), (412, 930), (428, 930), (396, 944), (412, 944), (428, 944)]):
    menor(f"HOS-C{_i + 1}", "tienda_campana", "Tienda de la Cruz Roja", rect(_x, _y, 12, 8), 6, uso="hospital de campaña")

# ===========================================================================
# ZONA 7 · EL CENTRO
# ===========================================================================
# --- La ciudad vieja: la fortaleza en el cabo entre el barranco y el río, y el barrio
# de los mercaderes que creció junto a ella. Calles torcidas y casas bajas.
edificio("CEN-VIE", "torre", "Torre Vieja", circulo(760, 872, 8), 7, altura=22.0, uso="torre de la antigua fortaleza", interior="a_mano", manzana="fortaleza",
         hito=23, notas="Lo único que queda entero de la fortaleza que dio origen a la ciudad.")
edificio("CEN-MUR1", "muralla", "Muralla de la fortaleza", banda([(752, 878), (728, 900), (724, 928)], 3.5), 7, interior="ninguno",
         sotano=False, manzana="fortaleza")
edificio("CEN-MUR2", "muralla", "Muralla de la fortaleza", banda([(769, 875), (800, 880)], 3.5), 7, interior="ninguno", sotano=False,
         manzana="fortaleza")
edificio("CEN-CAT", "iglesia", "Catedral de la Fortaleza", unary_union([rect(770, 912, 28, 18, 25), circulo(785, 918, 8)]), 7, altura=34.0,
         uso="catedral (museo en tiempos soviéticos)", interior="a_mano", hito=31, manzana="fortaleza",
         notas="La cúpula se hundió. Desde el campanario se domina el barranco y el puente.")
edificio("CEN-MUS", "prerrevolucion", "Museo de la Ciudad", rect(748, 952, 26, 13, 80), 7, pisos=2, uso="museo", interior="a_mano",
         manzana="fortaleza",
         notas="Antigua casa del gobernador. Vitrinas rotas; en el sótano, el almacén del museo.")


def _franja_calle(bloque: Polygon, puntos: list, ancho_calle: float, fondo: float) -> Polygon:
    """La franja de una manzana que da a una calle (para las casas que miran a ella)."""
    from shapely.geometry import LineString

    linea = LineString(puntos)
    return bloque.intersection(linea.buffer(ancho_calle / 2 + 1.0 + fondo)).difference(linea.buffer(ancho_calle / 2 + 0.5))


def _partes(geom) -> list[Polygon]:
    if geom.is_empty:
        return []
    return [geom] if geom.geom_type == "Polygon" else [g for g in geom.geoms if g.geom_type == "Polygon"]


def casas_en_hilera(prefijo: str, bloque: Polygon, zona: int, tipo: str = "prerrevolucion", largos=(12, 22), fondos=(10, 12),
                    pisos=(2, 3), nombre: str = "Casa", clave: str | None = None, hueco: float = 1.0) -> list[dict]:
    """Casas una al lado de otra a lo largo de cada lado de la manzana, mirando a la calle.
    Cada una con su largo, su fondo y su número de plantas: así crecen las calles viejas."""
    bloque = orient(bloque.simplify(1.5), sign=1.0)
    pts = list(bloque.exterior.coords)[:-1]
    clave = clave or prefijo
    puestas: list[Polygon] = list(_partes(_MANZANAS.get(clave, Polygon())))
    creados = []
    dentro = bloque.buffer(0.3)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        largo_lado = math.dist(a, b)
        if largo_lado < 9:
            continue
        ux, uy = (b[0] - a[0]) / largo_lado, (b[1] - a[1]) / largo_lado
        nx, ny = -uy, ux
        angulo = math.degrees(math.atan2(uy, ux))
        pos = 1.0
        n = 0
        while pos < largo_lado - 6:
            r = azar(f"{prefijo}/{i}/{n}")
            largo = min(largos[0] + r * (largos[1] - largos[0]), largo_lado - pos - 1.0)
            fondo = fondos[0] + azar(f"{prefijo}/{i}/{n}/f") * (fondos[1] - fondos[0])
            if largo >= 7:
                cx = a[0] + ux * (pos + largo / 2) + nx * (fondo / 2 + 0.2)
                cy = a[1] + uy * (pos + largo / 2) + ny * (fondo / 2 + 0.2)
                casa = rect(cx, cy, largo, fondo, angulo)
                if casa.within(dentro) and not any(casa.intersection(o).area > 0.5 for o in puestas):
                    piso = pisos[int(azar(f"{prefijo}/{i}/{n}/p") * len(pisos)) % len(pisos)]
                    e = edificio(f"{prefijo}-{len(creados) + 1}", tipo, nombre, casa, zona, pisos=piso,
                                 uso="viviendas; tienda o taller en la planta baja" if n % 2 == 0 else "viviendas")
                    if e is not None:
                        creados.append(e)
                        puestas.append(casa)
            pos += max(largo, 7) + hueco * azar(f"{prefijo}/{i}/{n}/h") * 2
            n += 1
    return creados


_MERCADERES = next(c for c in CALLES if c["id"] == "mercaderes")
_TORRE_VIEJA = Point(760, 884)


def _ciudad_vieja(region: Polygon) -> None:
    bloques = sorted((g for g in _partes(region.difference(CALLES_UNION.buffer(1.0))) if g.area > 600), key=lambda g: -g.area)
    franjas = [_franja_calle(b, _MERCADERES["puntos"], _MERCADERES["ancho"], 12.0) for b in bloques]
    con_galeria = max(range(len(bloques)), key=lambda i: franjas[i].area if not bloques[i].contains(_TORRE_VIEJA) else 0)
    for k, b in enumerate(bloques):
        c = b.representative_point()
        s, t = a_eje(c.x, c.y)
        if b.contains(_TORRE_VIEJA):
            for n, (x, y, a) in enumerate([(722, 968, 75), (730, 992, 80), (790, 884, 5)]):
                edificio(f"CEN-FV{n + 1}", "casa_madera", "Casa junto a la muralla", rect(x, y, 9, 8, a), 7, manzana="fortaleza")
            continue
        if t < 60 and s > 690:
            casas_en_hilera("CEN-ESCA", b, 7, tipo="estalinka", largos=(28, 44), fondos=(15, 17), pisos=(6, 7),
                            nombre="Casa de la Escalinata", hueco=0.0)
            continue
        galeria = franjas[k]
        if k == con_galeria and galeria.area > 300:
            edificio("CEN-GAL", "comercio", "Galería de los Mercaderes", galeria, 7, pisos=2, altura=11.0, uso="soportales con tiendas",
                     interior="a_mano", manzana=f"vieja_{k}", notas="Soportales de ladrillo con tiendas, a la manera de los gostiny dvor.")
        casas_en_hilera(f"CEN-V{k + 1}", b, 7, nombre="Casa del barrio de los mercaderes", clave=f"vieja_{k}")


# --- El centro estalinista: la retícula sigue el eje. Manzanas cerradas hechas por
# tramos de alturas distintas, con patios.
def _region_centro() -> Polygon:
    cima = [(x, float(R.orilla_norte(x)) + 98.0) for x in range(600, 1301, 20)]
    meseta = poligono([(600, 1200), (1235, 1200)] + [(1235, float(R.orilla_norte(1235)) + 98.0)]
                      + [p for p in reversed(cima) if p[0] <= 1235])
    return meseta.difference(banda(R.BARRANCO, 92.0, puntas="round")).intersection(caja(680, 0, 1235, 1200))


REGION_CENTRO = _region_centro()
_ciudad_vieja(REGION_CENTRO.intersection(rect_eje(0, 782, -500, 700)))
_S_FRANJAS = [(800, 915), (931, 990), (1006, 1100), (1116, 1220)]
_T_FRANJAS = [(-300, -193), (-175, -73), (73, 175), (193, 295), (311, 430)]


def _bloque(i: int, j: int) -> Polygon:
    s0, s1 = _S_FRANJAS[i]
    t0, t1 = _T_FRANJAS[j]
    b = rect_eje(s0, s1, t0, t1).intersection(REGION_CENTRO).difference(CALLES_UNION.buffer(1.0))
    if b.geom_type in ("MultiPolygon", "GeometryCollection"):
        b = max((g for g in b.geoms if g.geom_type == "Polygon"), key=lambda g: g.area)
    return b


# Teatro (manzana 0-2: delante, a la plaza; detrás, un jardín)
edificio("CEN-TEA", "monumental", "Teatro de la Ópera", rect_eje(812, 892, 82, 140), 7, pisos=4, altura=30.0, uso="teatro",
         interior="a_mano", notas="Pórtico de ocho columnas a la plaza. La cubierta de la sala se hundió sobre el patio de butacas. "
         "Telas, cuerdas, focos y ropa de vestuario.")
# Comisariado y Casa de la Radio (manzana 0-3)
edificio("CEN-COM", "publico", "Comisariado Militar", rect_eje(812, 862, 205, 255), 7, pisos=4, altura=15.0, uso="oficina militar",
         interior="a_mano", manzana="cen_0_3", ocupante="saqueadores",
         notas="De su armería salieron las armas de los saqueadores. Hoy es su segunda guarida: patio con sacos terreros, alambre "
         "y un fuego encendido de noche.")
edificio("CEN-RAD", "publico", "Casa de la Radio", rect_eje(872, 908, 205, 250), 7, pisos=4, altura=16.0, uso="emisora", interior="a_mano",
         manzana="cen_0_3", notas="Estudios, discos, válvulas y baterías.")
edificio("CEN-MAS", "torre", "Mástil de la Casa de la Radio", circulo(*eje(890, 278), 3), 7, altura=70.0, interior="ninguno", sotano=False, hito=27,
         manzana="cen_0_3")
manzana_perimetral("CEN-M03", _bloque(0, 3), 7, clave="cen_0_3")
# Escuela Nº 1, en la franja junto al barranco (manzana 0-4)
edificio("CEN-ESC", "escuela", "Escuela Nº 1", rect_eje(812, 845, 316, 328), 7, pisos=4, manzana="cen_0_4",
         uso="escuela; refugio de defensa civil en el sótano")
# Hotel (manzana 0-1)
edificio("CEN-HOT", "hotel", "Hotel Tumán", rect_eje(835, 905, -96, -80), 7, interior="a_mano", manzana="cen_0_1", ocupante="inquilino_c",
         hito=28, notas="Catorce plantas con dos huecos de ascensor. El tercer inquilino recorre las plantas de noche.")
edificio("CEN-HOT2", "comercio", "Restaurante del hotel", rect_eje(850, 900, -130, -96).difference(CALLES_UNION.buffer(1.0)), 7, pisos=2,
         altura=9.0, uso="restaurante y cocinas", manzana="cen_0_1")
# Circo (manzana 1-1)
edificio("CEN-CIR", "monumental", "Circo", circulo(*eje(960, -124), 27), 7, pisos=1, altura=26.0, uso="circo", interior="a_mano", hito=32,
         notas="La cúpula se vino abajo sobre la pista. Jaulas vacías en los sótanos.")
# Telégrafo (manzana 1-2)
edificio("CEN-TEL", "monumental", "Telégrafo Central", rect_eje(936, 986, 80, 132), 7, pisos=6, altura=34.0, uso="telégrafo y teléfonos",
         interior="a_mano", manzana="cen_1_2", hito=26, notas="Globo de acero en la cubierta. Centralita, baterías y cable de cobre.")
manzana_perimetral("CEN-M12", _bloque(1, 2), 7, clave="cen_1_2")
manzana_perimetral("CEN-M13", _bloque(1, 3), 7, clave="cen_1_3")
manzana_perimetral("CEN-M10", _bloque(1, 0), 7, clave="cen_1_0", pisos=(5, 6))
# Universidad (manzana 2-1) y Biblioteca (manzana 2-2)
edificio("CEN-UNI", "monumental", "Universidad Politécnica", rect_eje(1012, 1094, -165, -80).intersection(REGION_CENTRO).difference(CALLES_UNION.buffer(1.0)), 7, pisos=6,
         altura=36.0, uso="universidad", interior="a_mano", manzana="cen_2_1",
         notas="Laboratorios de física y química: dosímetros, material de vidrio, reactivos.")
edificio("CEN-BIB", "monumental", "Biblioteca Central", rect_eje(1012, 1058, 80, 118), 7, pisos=4, altura=22.0, uso="biblioteca", manzana="cen_2_2")
manzana_perimetral("CEN-M22", _bloque(2, 2), 7, clave="cen_2_2", pisos=(5, 6, 7))
# Casa de los Sóviets y su torre, en el eje
edificio("CEN-SOVT", "torre_estalinista", "Torre de la Casa de los Sóviets", circulo(*eje(955, 0), 14), 7, pisos=24, altura=110.0,
         interior="a_mano", hito=25, ocupante="vigia", manzana="cen_sov",
         notas="La aguja quedó doblada hacia el suroeste. Vigía de los saqueadores en la planta 20: ve el río, los dos puentes y el hielo.")
edificio("CEN-SOV", "monumental", "Casa de los Sóviets", rect_eje(925, 985, -50, 50), 7, pisos=10, altura=42.0, manzana="cen_sov",
         uso="sede del antiguo gobierno de la ciudad", interior="a_mano", notas="Cierra la perspectiva de la avenida. Fachada noreste reventada.")
# Más allá de la Casa: dos manzanas a los lados de la calle de la Planta
manzana_perimetral("CEN-M2A", rect_eje(1006, 1100, 15, 55).intersection(REGION_CENTRO).difference(CALLES_UNION.buffer(1.0)), 7, fondo=14,
                   pisos=(6, 7), huecos=False)
manzana_perimetral("CEN-M2B", rect_eje(1006, 1100, -55, -15).intersection(REGION_CENTRO).difference(CALLES_UNION.buffer(1.0)), 7, fondo=14,
                   pisos=(6, 7), huecos=False)
manzana_perimetral("CEN-M3A", rect_eje(1116, 1220, -55, 55).intersection(REGION_CENTRO).difference(CALLES_UNION.buffer(1.0)), 7, fondo=14,
                   pisos=(5, 6), huecos=True)
# En la loma, junto al río
edificio("CEN-FLUT", "torre", "Aguja de la Estación Fluvial", circulo(955, 816, 3), 7, altura=40.0, interior="ninguno", sotano=False, hito=22,
         manzana="cen_flu")
edificio("CEN-FLU", "pabellon", "Estación Fluvial", caja(925, 806, 985, 826), 7, pisos=2, altura=12.0, uso="terminal de barcos",
         interior="a_mano", manzana="cen_flu", notas="Dos barcos de pasajeros atrapados en el hielo frente al muelle.")
for _i, (_x, _y) in enumerate([(1040, 818), (1070, 822), (1120, 820), (1160, 815)]):
    garajes(f"CEN-GL{_i + 1}", "Garajes excavados en la loma", rect(_x, _y, 24, 8, 0), 7)
# El barranco: el sector privado (casas de madera, la mayoría quemadas).
_CASAS_BARRANCO = [
    (636, 812), (672, 820), (640, 846), (680, 856), (656, 880), (694, 886), (668, 912), (708, 916), (684, 944),
    (716, 950), (690, 976), (724, 984), (696, 1008), (726, 1024), (690, 1040), (718, 1056), (684, 1074), (700, 1094),
]
for _i, (_x, _y) in enumerate(_CASAS_BARRANCO):
    edificio(f"CEN-B{_i + 1:02d}", "casa_madera", "Casa del barranco", rect(_x, _y, 9, 8, (_i * 17) % 30 - 15), 7,
             incendio="total" if _i % 3 != 1 else "parcial", uso="vivienda y huerto",
             notas="Bodega con conservas caseras." if _i in (4, 9, 15) else "")

# ===========================================================================
# ZONA 8 · LA ZONA CERO
# ===========================================================================
GZ = R.CRATER
edificio("ZC-01", "ruina", "El Edificio Partido (Instituto Nº 9)", rect(1292, 985, 36, 18, 31), 8, pisos=14, altura=46.0,
         uso="instituto de investigación", interior="a_mano", dano=4, hito=29,
         notas="La mitad que miraba a la bomba desapareció; la otra mitad sigue en pie con los pisos abiertos al cráter, "
         "como una casa de muñecas. Aquí termina el juego.")
edificio("ZC-02", "ruina", "Planta Nº 1: nave de montaje", caja(1380, 860, 1560, 905), 8, pisos=1, altura=8.0, dano=4, uso="fábrica militar",
         interior="nave", notas="Solo quedan los pórticos de acero retorcidos.")
edificio("ZC-03", "ruina", "Planta Nº 1: nave de pruebas", caja(1370, 972, 1416, 1020), 8, pisos=1, altura=6.0, dano=4, interior="nave")
edificio("ZC-04", "chimenea", "Muñón de la chimenea de la Planta", circulo(1430, 1000, 5), 8, altura=25.0, dano=4, interior="ninguno", sotano=False, hito=30)
edificio("ZC-05", "cobertizo", "Búnker de mando de la Planta", rect(1352, 925, 12, 8), 8, uso="acceso al búnker", dano=2, interior="a_mano",
         notas="Puerta blindada a medio abrir. Abajo: las mejores máscaras y filtros de la ciudad.")
edificio("ZC-06", "ruina", "Estación de metro Planta (vestíbulo)", circulo(1310, 1040, 9), 8, pisos=1, altura=4.0, dano=4, interior="a_mano",
         notas="Escaleras cegadas de escombros.")
_ZC_BLOQUES = [
    (1272, 1160, 56, 13, 20), (1300, 1124, 48, 13, 35), (1290, 880, 56, 13, 10), (1320, 830, 70, 13, 0), (1380, 800, 50, 13, -5),
    (1278, 1045, 30, 13, 60), (1352, 1150, 40, 13, 40), (1252, 880, 13, 40, 0), (1338, 1000, 30, 13, 70),
]
for _i, (_x, _y, _l, _f, _a) in enumerate(_ZC_BLOQUES):
    edificio(f"ZC-R{_i + 1}", "ruina", "Muñón de un bloque de viviendas", rect(_x, _y, _l, _f, _a), 8, pisos=2, altura=6.0, dano=4,
             notas="De nueve plantas quedan una o dos: los huesos de la ciudad.")
for _i, (_x, _y, _a) in enumerate([(1450, 790, 10), (1480, 805, 40), (1520, 785, -20), (1560, 840, 70), (1430, 830, 5), (1500, 830, 120)]):
    edificio(f"ZC-V{_i + 1}", "ruina", "Vagones volcados", rect(_x, _y, 26, 4, _a), 8, pisos=1, altura=4.0, dano=4, interior="ninguno", sotano=False)

# ---------------------------------------------------------------------------
# Patios: juegos, pistas, cajas de hockey, basuras y aparcamientos
# ---------------------------------------------------------------------------
PATIOS: list[dict] = []


def _rellenar_patios() -> None:
    """Coloca en cada patio lo que hay en todos los patios soviéticos: un parque infantil,
    contenedores y, si cabe, una pista o una caja de hockey (en invierno, pista de hielo)."""
    ocupado = unary_union([e["huella"].buffer(5.0) for e in EDIFICIOS] + [CALLES_UNION.buffer(1.5), RIO.buffer(3.0)])
    for zona in (1, 2, 3, 4, 7):
        libre = ZONA_POLIGONOS[zona].difference(ocupado)
        if zona == 7:
            libre = libre.difference(banda(R.BARRANCO, 92.0, puntas="round"))
        piezas = [libre] if libre.geom_type == "Polygon" else [g for g in libre.geoms if g.geom_type == "Polygon"]
        for n, pieza in enumerate(sorted(piezas, key=lambda g: -g.area)):
            if pieza.area < 700:
                continue
            interior = pieza.buffer(-2.0)
            if interior.is_empty:
                continue
            shapely.prepare(interior)
            puestos = []
            plan = [("juegos", 14, 10)]
            if pieza.area > 3000:
                plan.append(("hockey" if zona == 2 else "pista", 30, 15))
            plan.append(("basuras", 7, 3))
            for clase, l, f in plan:
                mejor = None
                c = pieza.representative_point()
                minx, miny, maxx, maxy = interior.bounds
                paso = 4.0
                y = miny
                while y <= maxy:
                    x = minx
                    while x <= maxx:
                        for ang in (0, 90, 48):
                            r = rect(x, y, l, f, ang)
                            if r.within(interior) and not any(r.buffer(3).intersects(p) for p in puestos):
                                d = math.dist((x, y), (c.x, c.y))
                                if clase == "basuras":
                                    d = interior.boundary.distance(Point(x, y))
                                elif clase in ("pista", "hockey") and puestos:
                                    d = -min(p.centroid.distance(Point(x, y)) for p in puestos)
                                if mejor is None or d < mejor[0]:
                                    mejor = (d, r)
                        x += paso
                    y += paso
                if mejor is not None:
                    puestos.append(mejor[1])
                    PATIOS.append({"tipo": clase, "zona": zona, "forma": mejor[1]})


_rellenar_patios()

# Pistas y sitios concretos (además de los automáticos)
PATIOS += [
    {"tipo": "pista", "zona": 2, "forma": caja(205, 525, 275, 560)},
    {"tipo": "aparcamiento", "zona": 2, "forma": caja(150, 385, 240, 392)},
    {"tipo": "aparcamiento", "zona": 2, "forma": caja(52, 386, 126, 392)},
    {"tipo": "aparcamiento", "zona": 2, "forma": caja(150, 312, 240, 318)},
    {"tipo": "aparcamiento", "zona": 3, "forma": caja(722, 444, 822, 460)},
    {"tipo": "carbon", "zona": 2, "forma": caja(46, 128, 70, 136)},
    {"tipo": "cementerio", "zona": 4, "forma": caja(786, 80, 830, 118)},
    {"tipo": "patio_transformadores", "zona": 5, "forma": caja(1258, 196, 1345, 256)},
    {"tipo": "acero", "zona": 5, "forma": caja(1080, 520, 1150, 552)},
    {"tipo": "huerto", "zona": 7, "forma": caja(628, 860, 648, 870)},
    {"tipo": "huerto", "zona": 7, "forma": caja(700, 1030, 716, 1046)},
]

# ---------------------------------------------------------------------------
# Vallas y sendas
# ---------------------------------------------------------------------------
VALLAS: list[dict] = [
    {"nombre": "Valla del hospital", "puntos": [(352, 958), (352, 840), (632, 840), (632, 1170), (352, 1170), (352, 968)]},
    {"nombre": "Valla de la fábrica", "puntos": [(1064, 330), (870, 330), (870, 558), (1212, 558), (1212, 330), (1078, 330)]},
    {"nombre": "Valla de la central", "puntos": [(1245, 318), (1545, 318), (1545, 565), (1245, 565), (1245, 318)]},
    {"nombre": "Valla del depósito de combustible", "puntos": [(1296, 86), (1440, 86), (1440, 176), (1296, 176), (1296, 86)]},
    {"nombre": "Valla de la subestación", "puntos": [(1255, 194), (1348, 194), (1348, 258), (1255, 258), (1255, 194)]},
    {"nombre": "Valla de la escuela Nº 21", "puntos": [(192, 452), (290, 452), (290, 566), (192, 566), (192, 452)]},
    {"nombre": "Valla de la guardería Nº 7", "puntos": [(78, 590), (162, 590), (162, 638), (78, 638), (78, 590)]},
    {"nombre": "Valla de la guardería Nº 21", "puntos": [(204, 244), (262, 244), (262, 286), (204, 286), (204, 244)]},
    {"nombre": "Valla de la guardería Nº 30", "puntos": [(780, 484), (812, 484), (812, 540), (780, 540), (780, 484)]},
    {"nombre": "Valla del ferrocarril", "puntos": [(-10, 50), (300, 50), (600, 52), (860, 56)]},
    {"nombre": "Tapia de la iglesia", "puntos": [(732, 78), (832, 78), (832, 120), (732, 120), (732, 78)]},
    {"nombre": "Valla del estadio", "puntos": [(58, 1080), (226, 1080), (226, 1192), (58, 1192), (58, 1080)]},
    {"nombre": "Valla del parque", "puntos": [(326, 820), (326, 942)]},
    {"nombre": "Valla del parque", "puntos": [(326, 978), (326, 1200)]},
    {"nombre": "Patio del Comisariado (sacos terreros)", "puntos": [eje(808, 200), eje(866, 200), eje(866, 262), eje(808, 262), eje(808, 200)]},
    {"nombre": "Muro de contenedores del Almacén 3", "puntos": [(1110, 566), (1210, 566), (1210, 608), (1110, 608), (1110, 566)]},
]
SENDAS: list[dict] = [
    {"nombre": "Paseo principal del parque", "puntos": [(314, 960), (216, 960), (150, 958), (112, 958)]},
    {"nombre": "Vuelta al estanque", "puntos": [(178, 884), (200, 860), (250, 852), (300, 864), (304, 890), (270, 912), (220, 914), (182, 900), (178, 884)]},
    {"nombre": "Senda del estadio", "puntos": [(216, 960), (205, 1010), (180, 1070), (160, 1084)]},
    {"nombre": "Senda de la Concha", "puntos": [(314, 960), (290, 1000), (260, 1040)]},
    {"nombre": "Senda de la colina", "puntos": [(150, 958), (130, 920), (112, 958), (120, 1000), (150, 958)]},
    {"nombre": "Paseo del hospital", "puntos": [(358, 962), (420, 965), (450, 975), (500, 990)]},
    {"nombre": "Senda de Los Bloques", "puntos": [(300, 398), (230, 450)]},
    {"nombre": "Senda de Los Bloques", "puntos": [(140, 405), (138, 500), (180, 576)]},
    {"nombre": "Senda de Los Bloques", "puntos": [(90, 240), (100, 300)]},
    {"nombre": "Senda de la playa", "puntos": [(30, 676), (200, 664), (340, 652)]},
    {"nombre": "Escaleras de la loma", "puntos": [(1100, 798), (1110, 830), (1120, 870)]},
    {"nombre": "Escaleras del barranco", "puntos": [(742, 1112), (720, 1100), (700, 1094)]},
]

# ---------------------------------------------------------------------------
# Zonas verdes y árboles
# ---------------------------------------------------------------------------
ZONAS_VERDES: dict[str, Polygon] = {
    "parque": poligono([(0, 840), (150, 830), (330, 808), (330, 1200), (0, 1200)]),
    "hospital": caja(352, 840, 632, 1170),
    "barranco": banda(R.BARRANCO, 92.0, puntas="round").difference(RIO),
    "playa": poligono([(0, 668), (340, 640), (345, 680), (0, 705)]).difference(RIO),
}


def _arboles(semilla: int = 7) -> list[dict]:
    """Árboles de los parques, los patios y las aceras de la avenida. A menos de 380 m de la
    bomba no queda ninguno; hasta 900 m están tumbados y todos apuntan lejos de ella (una
    pista para orientarse); más lejos siguen en pie, secos.

    `copa` es el radio de la copa de los que siguen en pie; `rumbo`, hacia dónde apunta la
    copa de los tumbados (grados desde el este). `_punta` solo la usa el dibujo."""
    rng = np.random.default_rng(semilla)
    verdes = ZONAS_VERDES
    areas = [
        (verdes["parque"].difference(ESTANQUE).difference(elipse(142, 1136, 82, 54)), 9.0),
        (verdes["hospital"], 13.0),
        (verdes["barranco"], 10.0),
        (ZONA_POLIGONOS[2], 15.0),
        (ZONA_POLIGONOS[4], 19.0),
        (ZONA_POLIGONOS[7].difference(verdes["barranco"]), 20.0),
        (ZONA_POLIGONOS[1], 22.0),
        (ZONA_POLIGONOS[3], 18.0),
    ]
    patios = unary_union([q["forma"].buffer(2.0) for q in PATIOS])
    edificios = unary_union([e["huella"] for e in EDIFICIOS])
    bloqueo = unary_union([CALLES_UNION, edificios.buffer(3.0), RIO.buffer(4.0), patios])
    xs, ys = [], []
    for area, paso in areas:
        minx, miny, maxx, maxy = area.bounds
        gx, gy = np.meshgrid(np.arange(minx, maxx, paso), np.arange(miny, maxy, paso))
        gx = gx.ravel() + rng.uniform(-0.45, 0.45, gx.size) * paso
        gy = gy.ravel() + rng.uniform(-0.45, 0.45, gy.size) * paso
        dentro = shapely.contains_xy(area, gx, gy) & ~shapely.contains_xy(bloqueo, gx, gy)
        xs.append(gx[dentro])
        ys.append(gy[dentro])
    # Hileras de árboles en las aceras de la avenida y del bulevar.
    for s in np.arange(-250, 365, 11.0):
        for t in (33.0, -33.0):
            x, y = eje(s, t)
            if math.hypot(x - 430, y - 330) > 95:
                xs.append(np.array([x]))
                ys.append(np.array([y]))
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    dist = np.hypot(x - GZ[0], y - GZ[1])
    ux = (x - GZ[0]) / np.maximum(dist, 1)
    uy = (y - GZ[1]) / np.maximum(dist, 1)
    arboles = []
    for xi, yi, di, uxi, uyi in zip(x, y, dist, ux, uy):
        if di < 380:
            continue
        if di < 900:
            arboles.append({"pos": (float(xi), float(yi)), "estado": "tumbado",
                            "rumbo": math.degrees(math.atan2(uyi, uxi)) % 360.0,
                            "_punta": (xi + uxi * 4.5, yi + uyi * 4.5)})
            continue
        arboles.append({"pos": (float(xi), float(yi)), "estado": "en_pie", "copa": 1.9 + rng.uniform(-0.3, 0.5)})
    return arboles


ARBOLES = _arboles()

# ---------------------------------------------------------------------------
# Vehículos: el atasco de la evacuación, los aparcados y los trenes
# ---------------------------------------------------------------------------
VEHICULOS: list[dict] = []
MEDIDAS = {"coche": (4.5, 1.8), "furgoneta": (5.2, 2.1), "autobus": (11.5, 2.6), "camion": (8.0, 2.5), "tranvia": (15.0, 2.6),
           "trolebus": (12.0, 2.6), "blindado": (7.5, 3.0), "vagon": (14.0, 3.0), "coche_tren": (24.0, 3.1), "locomotora": (17.0, 3.1),
           "barcaza": (60.0, 12.0), "remolcador": (22.0, 7.0), "barco": (36.0, 8.0), "barca": (5.0, 1.6), "bombero": (9.0, 2.5)}


def vehiculo(tipo: str, x: float, y: float, angulo: float, estado: str = "abandonado") -> None:
    VEHICULOS.append({"tipo": tipo, "pos": (round(x, 1), round(y, 1)), "angulo": round(angulo, 1), "estado": estado})


def atasco(clave: str, puntos: list, carriles: list[float], cada: float, mezcla: dict, quemados: float = 0.15) -> None:
    """Coches parados en fila por los carriles de una calle, con huecos al azar."""
    from shapely.geometry import LineString

    linea = LineString(puntos)
    for k, desplazamiento in enumerate(carriles):
        carril = linea.offset_curve(desplazamiento)
        pos = azar(f"{clave}/{k}") * cada
        n = 0
        while pos < carril.length:
            r = azar(f"{clave}/{k}/{n}")
            tipo = "coche"
            acumulado = 0.0
            for t, prob in mezcla.items():
                acumulado += prob
                if r < acumulado:
                    tipo = t
                    break
            p = carril.interpolate(pos)
            q = carril.interpolate(min(carril.length, pos + 1.0))
            ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x)) + (azar(f"{clave}/{k}/{n}/a") - 0.5) * 24
            estado = "quemado" if azar(f"{clave}/{k}/{n}/q") < quemados else "abandonado"
            if not RIO.contains(Point(p.x, p.y)):
                vehiculo(tipo, p.x, p.y, ang, estado)
            pos += MEDIDAS[tipo][0] + 1.5 + azar(f"{clave}/{k}/{n}/h") * cada
            n += 1


# El atasco de la evacuación: todos iban hacia el metro o hacia el puente.
atasco("av_sur", [eje(-255), eje(-90)], [-26.0, -19.0, -12.0, 12.0, 19.0, 26.0], 6.0, {"coche": 0.8, "furgoneta": 0.1, "autobus": 0.05, "camion": 0.05})
atasco("av_norte", [eje(100), eje(352)], [-26.0, -19.0, -12.0, 12.0, 19.0], 7.0, {"coche": 0.82, "furgoneta": 0.08, "autobus": 0.05, "camion": 0.05})
atasco("mineros_o", [(30, 342), (330, 338)], [-14.0, -7.0, 7.0], 8.0, {"coche": 0.85, "furgoneta": 0.1, "autobus": 0.05})
atasco("mineros_e", [(840, 314), (530, 325)], [-10.0, -4.0, 4.0], 10.0, {"coche": 0.7, "autobus": 0.12, "camion": 0.18})
atasco("juventud", [(345, 620), (345, 350)], [-5.0, 5.0], 12.0, {"coche": 0.9, "furgoneta": 0.1})
atasco("puente", [eje(380), eje(468)], [-8.0, 0.0, 8.0], 9.0, {"coche": 0.85, "camion": 0.15}, quemados=0.3)
atasco("bajada", [(850, 798), (780, 812), (752, 830)], [-3.0, 3.0], 10.0, {"coche": 0.9, "camion": 0.1}, quemados=0.5)
atasco("sovietica", [eje(710, 64), eje(1080, 64)], [-4.0, 4.0], 14.0, {"coche": 0.85, "autobus": 0.15}, quemados=0.6)
atasco("planta", [eje(1000), (1180, 1100), (1262, 1092)], [-6.0, 6.0], 10.0, {"coche": 0.8, "camion": 0.2}, quemados=0.9)
atasco("fabrica", [(848, 60), (848, 300)], [-6.0, 6.0], 16.0, {"coche": 0.6, "camion": 0.4})
atasco("muelle_n", [(500, 799), (800, 787), (1000, 796)], [-5.0, 5.0], 16.0, {"coche": 0.9, "furgoneta": 0.1}, quemados=0.3)
# Aparcados en Los Bloques
atasco("aparc_1", [(152, 388), (238, 388)], [0.0], 2.5, {"coche": 0.9, "furgoneta": 0.1}, quemados=0.05)
atasco("aparc_2", [(54, 389), (124, 389)], [0.0], 3.0, {"coche": 1.0}, quemados=0.05)
atasco("aparc_3", [(152, 315), (238, 315)], [0.0], 3.0, {"coche": 1.0}, quemados=0.05)
# Trolebuses en el patio del depósito
for _i in range(8):
    vehiculo("trolebus", 730 + _i * 12, 452, 90)
# Tranvías
vehiculo("tranvia", *eje(505, 2), 48.0 - 14.0, "volcado")
vehiculo("tranvia", *eje(860, 20), 48.0 + 75.0, "volcado")
vehiculo("tranvia", 252, 112, 0.0, "quemado")
vehiculo("tranvia", *eje(-30, -4), 48.0, "abandonado")
# Autobuses y camiones de la evacuación en la plaza de la Estación
for _i, (_x, _y, _a) in enumerate([(200, 120, 0), (285, 76, 0), (285, 92, 0), (190, 72, 90)]):
    vehiculo("autobus", _x, _y, _a)
vehiculo("camion", 255, 128, 10.0)
vehiculo("camion", 268, 74, -5.0)
# El control del ejército junto al metro
vehiculo("blindado", *eje(40, -30), 48.0 - 30.0)
vehiculo("camion", *eje(55, -18), 48.0)
# Bomberos y ambulancias
vehiculo("bombero", *eje(880, -30), 48.0 + 20, "quemado")
vehiculo("bombero", *eje(890, -40), 48.0 + 5, "quemado")
vehiculo("bombero", 742, 196, 0.0)
for _i in range(3):
    vehiculo("furgoneta", 440 + _i * 9, 1140, 90.0)
# Camiones en la base y en la fábrica
for _i in range(5):
    vehiculo("camion", 1040 + _i * 13, 244, 90.0)
for _i in range(3):
    vehiculo("furgoneta", 730 + _i * 10, 290, 90.0)
# Trenes: el de la evacuación y los vagones de la playa de vías
for _i in range(13):
    vehiculo("coche_tren", 70 + _i * 25.5, 34, 0.0, "quemado")
vehiculo("locomotora", 412, 34, 0.0, "quemado")
# Los vagones de la playa de vías los pone ferrocarril.red(), en lo recto de cada vía.
VAGONES_PLAYA = [60, 70, 90, 100, 120, 140, 150]
vehiculo("locomotora", 1225, 80, 0.0)
for _i in range(4):
    vehiculo("vagon", 1305, 360 + _i * 16, 90.0)
for _i in range(5):
    vehiculo("vagon", 890 + _i * 16, 636, 0.0)
# En el río
vehiculo("barcaza", 990, 672, 2.0)
vehiculo("barcaza", 1080, 676, -3.0)
vehiculo("barcaza", 1185, 668, -6.0)
vehiculo("remolcador", 1252, 664, -12.0)
vehiculo("barco", 948, 762, 4.0)
vehiculo("barco", 905, 758, -2.0)
for _i in range(5):
    vehiculo("barca", 610 + _i * 8, 640, 85.0)
for _i, (_x, _y) in enumerate([(230, 888), (262, 878), (252, 900)]):
    vehiculo("barca", _x, _y, 30.0 * _i)

# ---------------------------------------------------------------------------
# Hitos: lo que se ve de lejos y sirve para orientarse al dibujar el mapa
# ---------------------------------------------------------------------------
HITOS: dict[int, dict] = {
    1: {"nombre": "Torres de la Avenida", "pos": eje(88, 0), "notas": "Dos torres con aguja que enmarcan la avenida desde la plaza."},
    2: {"nombre": "¡Gloria al Trabajo!", "pos": eje(122, -46), "notas": "Letras en la cubierta de la Casa de la Proa; faltan algunas."},
    3: {"nombre": "Monumento al Minero", "pos": (430, 330), "notas": "Estatua de 12 m en la isleta de la glorieta. Le falta el brazo."},
    4: {"nombre": "Torre del reloj de la Estación", "pos": (240, 56), "notas": "45 m. El reloj se paró a las 4:12."},
    5: {"nombre": "La Torre", "pos": (300, 604), "notas": "16 plantas: lo más alto de la orilla sur después de las chimeneas."},
    6: {"nombre": "Chimenea de los Bloques", "pos": (80, 118), "notas": "45 m, de ladrillo, con anillos blancos y rojos desvaídos."},
    7: {"nombre": "Cúpula del Mercado", "pos": eje(234, 68), "notas": "Cúpula de hormigón con un agujero."},
    8: {"nombre": "Letrero de los Grandes Almacenes", "pos": eje(231, -62), "notas": "Letras metálicas sobre la azotea."},
    9: {"nombre": "Torre de bomberos", "pos": (782, 184), "notas": "30 m. Garita de vigilancia acristalada."},
    10: {"nombre": "Campanario de la iglesia vieja", "pos": (742, 100), "notas": "36 m. Sin campanas."},
    11: {"nombre": "Palacio de la Cultura", "pos": (630, 262), "notas": "Pórtico con estatuas en la cornisa."},
    12: {"nombre": "Depósito de agua de la fábrica", "pos": (1190, 420), "notas": "34 m, con forma de copa."},
    13: {"nombre": "Elevador de grano", "pos": (1278, 583), "notas": "60 m: lo más alto del puerto."},
    14: {"nombre": "Grúas del puerto", "pos": (1065, 640), "notas": "Cuatro grúas pórtico; una con el brazo caído."},
    15: {"nombre": "Chimeneas de la central", "pos": (1466, 400), "notas": "Una de 150 m en pie; la otra, caída sobre la calle."},
    16: {"nombre": "Torres de refrigeración", "pos": (1407, 487), "notas": "80 m. A la segunda le falta un tercio."},
    17: {"nombre": "Puente del Progreso", "pos": eje(508), "notas": "Vano central hundido sobre el hielo."},
    18: {"nombre": "Puente del Ferrocarril", "pos": (1550, 690), "notas": "Celosía de acero, intacta."},
    19: {"nombre": "Torre de paracaídas", "pos": (105, 958), "notas": "35 m sobre la colina, que ya tiene 13."},
    20: {"nombre": "Focos del estadio", "pos": (142, 1136), "notas": "Cuatro torres de 40 m; dos sin focos."},
    21: {"nombre": "Hospital Nº 3", "pos": (500, 1010), "notas": "Bloque en H de 8 plantas con la cruz roja en la cubierta."},
    22: {"nombre": "Estación Fluvial", "pos": (955, 816), "notas": "Aguja de 40 m al pie de la loma."},
    23: {"nombre": "Torre Vieja", "pos": (760, 872), "notas": "Torre de la fortaleza, en el borde de la loma."},
    24: {"nombre": "La Escalinata", "pos": eje(716), "notas": "De la orilla a la plaza Central, en el eje de la avenida."},
    25: {"nombre": "Casa de los Sóviets", "pos": eje(955), "notas": "110 m. La aguja doblada se ve desde toda la ciudad."},
    26: {"nombre": "Telégrafo Central", "pos": eje(961, 106), "notas": "Globo de acero en la cubierta."},
    27: {"nombre": "Mástil de la Radio", "pos": eje(890, 278), "notas": "70 m, atirantado. Una luz roja que ya no se enciende."},
    28: {"nombre": "Hotel Tumán", "pos": eje(870, -88), "notas": "14 plantas sobre el borde de la loma."},
    29: {"nombre": "El Edificio Partido", "pos": (1292, 985), "notas": "Medio edificio de 14 plantas abierto como una maqueta."},
    30: {"nombre": "El cráter", "pos": GZ, "notas": "190 m de diámetro. Borde levantado de 7 m. Muñón de la chimenea de la Planta."},
    31: {"nombre": "Catedral de la Fortaleza", "pos": (778, 915), "notas": "Cúpula hundida; el campanario sigue en pie."},
    32: {"nombre": "El Circo", "pos": eje(960, -124), "notas": "Cúpula caída sobre la pista."},
}

# ---------------------------------------------------------------------------
# Puntos de interés
# ---------------------------------------------------------------------------
# tipo: acceso, botin, refugio, padre, historia, mirador
PUNTOS: list[dict] = []


def punto(tipo: str, nombre: str, pos, notas: str = "", **extra) -> None:
    PUNTOS.append({"tipo": tipo, "nombre": nombre, "pos": (round(pos[0], 1), round(pos[1], 1)), "notas": notas, **extra})


SALIDA = (334, 296)
punto("acceso", "Tu salida: la compuerta del vestíbulo", SALIDA, "Escalera mecánica, compuerta y la rotonda.")
punto("acceso", "Paso subterráneo de la plaza", (430, 330),
      "Cruza la glorieta en cruz. Cuatro bocas y la isleta del monumento. La puerta al vestíbulo del metro está soldada.")
punto("acceso", "Paso subterráneo del Mercado", eje(232, 0), "Bajo la avenida. Quioscos y la entrada a la estación Mercado (inundada).")
punto("acceso", "El socavón", R.SOCAVON, "La calzada se hundió en el túnel de la línea 1: se baja con cuerda.")
punto("acceso", "Túnel peatonal de la estación de tren", (240, 40), "Del vestíbulo a los andenes, bajo las vías.")
punto("acceso", "Desagüe de la playa", (250, 690), "Boca del colector de pluviales sobre la playa.")
punto("acceso", "Desagüe del puerto", (1000, 660), "Boca del colector bajo el muelle. Se llega por el hielo.")
punto("acceso", "Boca del arroyo enterrado", (686, 1100), "El arroyo sale de un túnel de ladrillo en la cabecera del barranco.")
punto("acceso", "Paso bajo el puente norte", eje(622, 0), "El muelle Norte pasa bajo el último vano del puente.")
punto("botin", "Quioscos de la plaza", (412, 403), "Latas, tabaco, cerillas, periódicos.", peligro=1)
punto("botin", "Gastronom Nº 1", (470, 252), "El almacén de atrás no lo encontró nadie.", peligro=1)
punto("botin", "Correos Nº 1", (412, 415), "Paquetes sin repartir: de todo un poco.", peligro=1)
punto("botin", "Farmacia Nº 14 (Mineros 7)", (165, 374), "Antibióticos. En el bloque del inquilino.", peligro=3)
punto("botin", "Universam (Mineros 7)", (220, 374), "Conservas y azúcar. En el bloque del inquilino.", peligro=3)
punto("botin", "Refugio de la escuela Nº 21", (240, 485), "Máscaras antiguas, filtros caducados, un dosímetro.", peligro=2)
punto("botin", "Casa de servicios «Aurora»", (108, 113), "Herramientas, hilo, película, relojes.", peligro=2)
punto("botin", "Garajes «Volga»", (90, 72), "Herramientas, baterías, combustible. Territorio de la Jauría.", peligro=2)
punto("botin", "Grandes Almacenes", eje(231, -62), "Ropa de abrigo, radios, menaje. Vigía de saqueadores en la azotea.", peligro=4)
punto("botin", "Mercado Central", eje(234, 68), "Conservas en las cámaras del sótano; semillas.", peligro=3)
punto("botin", "Depósito de trolebuses", (772, 410), "Baterías, cable, herramientas de taller.", peligro=3)
punto("botin", "Gasolinera Nº 6", (815, 350), "Algo de gasóleo en los depósitos enterrados.", peligro=2)
punto("botin", "Parque de bomberos", (742, 170), "Cuerda, hachas, equipos de respiración.", peligro=2)
punto("botin", "Comisaría", (490, 99), "Ganzúas, radios y pilas del depósito de pruebas.", peligro=2)
punto("botin", "Panificadora", (760, 260), "Azúcar, sal, levadura seca.", peligro=2)
punto("botin", "Búnker de la fábrica", (1160, 522), "Máscaras, filtros, raciones, dosímetros.", peligro=4)
punto("botin", "Base de camiones", (1070, 218), "Combustible, baterías, neumáticos.", peligro=3)
punto("botin", "Chatarrería", (1230, 228), "Piezas, cable, baterías.", peligro=3)
punto("botin", "Vagones de la playa de vías", (1080, 100), "Carga sin abrir: depende del vagón.", peligro=3)
punto("botin", "Farmacia del hospital (sótano)", (500, 1010), "Insulina y antibióticos. Territorio del segundo inquilino.", peligro=5)
punto("botin", "Policlínica", (412, 878), "Vendas, jeringas, instrumental.", peligro=4)
punto("botin", "Bodegas del barranco", (676, 880), "Conservas caseras en las bodegas de las isbas.", peligro=3)
punto("botin", "Museo de la Ciudad", (748, 952), "Herramientas antiguas, lámparas de aceite, mapas viejos de la ciudad (anteriores a la guerra).", peligro=3)
punto("botin", "Universidad: laboratorios", eje(1053, -122), "Dosímetros, material de laboratorio, reactivos.", peligro=4)
punto("botin", "Comisariado Militar", eje(837, 230), "Máscaras militares y filtros. Guarida de saqueadores.", peligro=5)
punto("botin", "Búnker de mando de la Planta", (1352, 925), "Las mejores máscaras y filtros.", peligro=5)
punto("refugio", "Cámara acorazada del Banco", eje(125, 46), "Una sola puerta de acero. Sin ventanas: la luz no sale.")
punto("refugio", "Cabina de la grúa 2", (1020, 640), "Una escalera, a 25 m. Fría y muy expuesta al viento.")
punto("refugio", "Cabina de proyección del cine", (415, 600), "Cierra por dentro; ventanucos fáciles de tapar.")
punto("refugio", "Garita de la torre de bomberos", (782, 184), "Se ve venir todo. También te ven si enciendes luz.")
punto("refugio", "Tranvía volcado de la plaza Central", eje(860, 20), "Chapa fina: no aguanta nada, pero esconde.")
punto("refugio", "Bodega de la Casa del Comerciante", (595, 98), "Bóveda de ladrillo, una escalera.")
punto("refugio", "Cuarta planta de Escuela 7", (115, 457), "Un solo portal y la escalera tapiable.")
punto("refugio", "Torre Vieja", (760, 872), "Muros de un metro. Puerta de roble que se puede atrancar.")
punto("refugio", "Caseta del embarcadero del parque", (304, 874), "Lejos de todo; en territorio de la segunda jauría.")
punto("padre", "Una marca de tiza en el paso subterráneo", (452, 312), "Su símbolo, el mismo que hay en la puerta del depósito, señala al noreste.")
punto("padre", "Una cuerda con su nudo en el puente", eje(470, 10), "Atada a la barandilla, junto al vano hundido.")
punto("padre", "Una receta a su nombre en la Policlínica", (412, 878), "Para un medicamento que ya no existe en la estación.")
punto("padre", "Su linterna en la Estación Fluvial", (955, 816), "Apagada, con la pila gastada, mirando a la loma.")
punto("padre", "El Edificio Partido", (1292, 985), "La respuesta.")
punto("historia", "El atasco de la evacuación", eje(-200, 15), "Coches y autobuses en dirección a la plaza y al metro.")
punto("historia", "El tren que no salió", (150, 30), "Tren de pasajeros quemado en la vía 1, lleno de maletas.")
punto("historia", "Control del ejército", eje(40, -30), "Sacos terreros, vallas y un blindado sin ruedas junto al metro.")
punto("historia", "«Hemos ido al metro»", (230, 470), "Escrito con pintura en los portales de Los Bloques, con nombres y la hora.")
punto("historia", "Hospital de campaña de la Cruz Roja", (412, 937), "Tiendas hundidas por la nieve, camas plegables.")
punto("historia", "La zanja", (612, 960), "Detrás del hospital. Una tabla con fechas de las primeras semanas.")
punto("historia", "Tranvía volcado", eje(860, 20), "La onda lo tumbó en la plaza Central.")
punto("historia", "Las sombras", (1340, 1020), "Siluetas de personas marcadas en una pared por el destello.")
punto("historia", "Árboles tumbados", (1180, 960), "Todos apuntan en la misma dirección: lejos de la bomba.")
punto("historia", "Barricada del puente", eje(410, 0), "Bloques de hormigón y autobuses atravesados a la entrada del puente.")
punto("mirador", "Azotea de La Torre", (300, 604), "Toda la orilla sur y el otro lado del río.")
punto("mirador", "Campanario de la iglesia vieja", (742, 100), "La vía, la playa de vías y el barrio obrero.")
punto("mirador", "Torre de bomberos", (782, 184), "Todo el sur.")
punto("mirador", "Torre de paracaídas", (105, 958), "El parque, el río y la orilla sur.")
punto("mirador", "Campanario de la catedral", (770, 912), "El barranco, el puente y la orilla sur.")
punto("mirador", "Azotea del Telégrafo", eje(961, 106), "La plaza Central y la calle de la Planta.")
punto("mirador", "Borde de la loma (Bulevar del Río)", (1150, 885), "El río, el hielo y el puerto.")

# ---------------------------------------------------------------------------
# El subsuelo
# ---------------------------------------------------------------------------
METRO_LINEAS: list[dict] = [
    {"id": "linea_1", "nombre": "Línea 1 (roja)", "color": "#B4423A",
     "puntos": [eje(-420), eje(0), eje(232), eje(420), eje(508), eje(640), eje(860), eje(990), (1180, 1100), (1310, 1040), (1420, 1110)],
     "profundidad": [-25, -30, -18, -28, -36, -30, -22, -24, -24, -26, -30],
     "notas": "Bajo la avenida y bajo el río. Entre el Mercado y la orilla norte el túnel está inundado."},
    {"id": "linea_2", "nombre": "Línea 2 (azul)", "color": "#3A5A8C",
     "puntos": [(-20, 300), (200, 300), (430, 300), (700, 300), (1000, 300), (1300, 270), (1620, 240)],
     "profundidad": [-22, -22, -30, -20, -18, -18, -20],
     "notas": "Bajo la calle de los Mineros. Al oeste sigue la red habitada; al este, solo túneles muertos."},
]
METRO_ESTACIONES: list[dict] = [
    {"id": "S1", "nombre": "Plaza del Trabajo", "pos": eje(0), "estado": "habitada", "forma": rect_eje(-80, 80, -12, 12),
     "notas": "Tu estación. Correspondencia entre las dos líneas. La última habitada hacia el norte y el este."},
    {"id": "S2", "nombre": "Mercado", "pos": eje(232), "estado": "inundada", "forma": rect_eje(192, 272, -10, 10),
     "notas": "Agua helada hasta el andén. El Llamador duerme en el vestíbulo de arriba."},
    {"id": "S3", "nombre": "Plaza Central", "pos": eje(860), "estado": "hundida", "forma": rect_eje(820, 900, -10, 10),
     "notas": "El vestíbulo se hundió con la onda. Aire viciado. Se sale por el pozo de ventilación V4."},
    {"id": "S4", "nombre": "Planta", "pos": (1310, 1040), "estado": "destruida", "forma": rect(1310, 1040, 80, 20, 20),
     "notas": "Derrumbada e inundada. El túnel desde S3 está cortado por un hundimiento."},
    {"id": "S5", "nombre": "Fábrica", "pos": (1000, 300), "estado": "abandonada", "forma": rect(1000, 300, 80, 20, 0),
     "notas": "Evacuada tras la lluvia radiactiva. Oscura, con charcos helados y ratas. Sale a la puerta de la fábrica."},
]
METRO_REJAS: list[dict] = [
    {"nombre": "Reja Norte", "pos": eje(95), "notas": "Línea 1. Guardia del gobierno civil: deja salir a los stalkers con permiso."},
    {"nombre": "Reja Este", "pos": (560, 300), "notas": "Línea 2. Igual que la Reja Norte."},
]
POZOS: list[dict] = [
    {"id": "V1", "pos": (432, 446), "notas": "Pozo de ventilación en el primer patio: escalera de pates hasta el túnel."},
    {"id": "V2", "pos": (612, 640), "notas": "Caseta junto al club náutico. Baja al túnel antes del tramo inundado."},
    {"id": "V3", "pos": (842, 860), "notas": "En la loma, junto a la Bajada. Sube del túnel bajo el río."},
    {"id": "V4", "pos": eje(965, 70), "notas": "Detrás de la Casa de los Sóviets: la salida de la estación hundida."},
    {"id": "V5", "pos": (680, 286), "notas": "Línea 2, patio de la panificadora."},
    {"id": "V6", "pos": (150, 286), "notas": "Línea 2, en Los Bloques. Sellado por el gobierno civil."},
]
SUBSUELO: list[dict] = [
    {"id": "colector_calefaccion", "tipo": "galeria", "nombre": "Galería de la calefacción",
     "puntos": [(1290, 316), (870, 318), (512, 320), (430, 316), (345, 330), (100, 330), (100, 393)],
     "notas": "Galería de hormigón de 2 m bajo la acera de Mineros, con registros cada 100 m. Caliente en otro tiempo; hoy, helada."},
    {"id": "colector_avenida", "tipo": "galeria", "nombre": "Galería de la avenida", "puntos": [eje(-250, 30), eje(0, 30), eje(360, 30)],
     "notas": "Cables y tubos bajo la acera noroeste de la avenida."},
    {"id": "pluviales_sur", "tipo": "colector", "nombre": "Colector de pluviales del muelle Sur",
     "puntos": [(30, 655), (250, 645), (250, 690), (250, 645), (500, 612), (760, 604), (1000, 612), (1000, 660)],
     "notas": "Se camina agachado. Desagua en el río por la playa y bajo el puerto."},
    {"id": "arroyo", "tipo": "colector", "nombre": "El arroyo enterrado", "puntos": [(686, 1100), (690, 1140), (700, 1200)],
     "notas": "Túnel de ladrillo del siglo XIX por el que corre el arroyo bajo la ciudad vieja. Guarida del segundo Llamador."},
    {"id": "colector_centro", "tipo": "colector", "nombre": "Gran colector del centro", "puntos": [(742, 1112), eje(860, 120), eje(980, 120), eje(980, 0)],
     "notas": "Alcantarilla abovedada antigua. Une la cabecera del barranco con el centro."},
    {"id": "tunel_estacion", "tipo": "peatonal", "nombre": "Túnel de los andenes", "puntos": [(240, 64), (240, 20)], "notas": ""},
    {"id": "paso_plaza_1", "tipo": "peatonal", "nombre": "Paso subterráneo de la plaza", "puntos": [(330, 336), (530, 324)], "notas": ""},
    {"id": "paso_plaza_2", "tipo": "peatonal", "nombre": "Paso subterráneo de la plaza", "puntos": [eje(-95), eje(95)], "notas": ""},
    {"id": "paso_mercado", "tipo": "peatonal", "nombre": "Paso subterráneo del Mercado", "puntos": [eje(232, -48), eje(232, 48)], "notas": ""},
    {"id": "sotanos_bloques", "tipo": "sotano", "nombre": "Sótanos corridos de las jrushchovkas", "puntos": [(70, 415), (70, 479)],
     "notas": "Cada jrushchovka tiene un sótano de punta a punta con salida en cada portal."},
]
TRAMOS_INUNDADOS = [{"puntos": [eje(232), eje(420), eje(508), eje(600)], "notas": "Agua helada; en el punto más bajo, hasta el pecho."}]
TRAMOS_HUNDIDOS = [{"puntos": [eje(990), (1180, 1100), (1310, 1040)], "notas": "Bóveda caída: no se pasa."}]

# Socavones (como en Metro 2033): donde reventó lo que va bajo la calle, el agua se llevó la
# tierra y la calle cayó al hueco (tools/ciudad/deterioro.py). `radio` a lo largo de `rumbo`
# (grados desde el este; lo que reventó va así) y `ancho` de través, en metros; `hondo`, lo
# que baja el fondo bajo la calle; `causa`: metro (la bóveda del túnel), galeria (la de la
# calefacción), colector, arroyo (su bóveda de ladrillo) o agua (una tubería que se heló).
HUNDIMIENTOS: list[dict] = [
    {"id": "socavon_avenida", "nombre": "El socavón de la avenida", "pos": R.SOCAVON, "radio": 17.0, "ancho": 12.5,
     "rumbo": 48.0, "hondo": 11.0, "causa": "metro",
     "notas": "La bóveda del túnel de la línea 1 cedió: la calzada cayó dentro con las vías del tranvía y parte del "
              "atasco. Se baja con cuerda; por el fondo se entra en el túnel."},
    {"id": "calefaccion_fabrica", "nombre": "La galería de la calefacción, frente a la fábrica", "pos": (1102.0, 317.0),
     "radio": 7.5, "ancho": 3.2, "rumbo": 0.0, "hondo": 2.6, "causa": "galeria",
     "notas": "La galería se hundió a lo largo: se ven los dos tubos aislados, reventados por la helada."},
    {"id": "calefaccion_mineros", "nombre": "La galería de la calefacción en Mineros", "pos": (663.0, 319.0),
     "radio": 6.0, "ancho": 2.8, "rumbo": 2.0, "hondo": 2.4, "causa": "galeria", "notas": ""},
    {"id": "pluviales_muelle", "nombre": "El colector del Muelle Sur", "pos": (493.0, 613.0), "radio": 6.5,
     "ancho": 4.5, "rumbo": -7.5, "hondo": 3.6, "causa": "colector",
     "notas": "El colector de pluviales asoma roto en el fondo; el agua que bajaba al río se heló dentro."},
    {"id": "pluviales_puerto", "nombre": "El colector, camino del puerto", "pos": (770.0, 604.0), "radio": 4.2,
     "ancho": 3.2, "rumbo": 2.0, "hondo": 3.0, "causa": "colector", "notas": ""},
    {"id": "arroyo", "nombre": "La bóveda del arroyo", "pos": (698.0, 1188.0), "radio": 7.0, "ancho": 5.0,
     "rumbo": 80.0, "hondo": 5.0, "causa": "arroyo",
     "notas": "La bóveda de ladrillo del arroyo enterrado se abrió en la calle Norte: abajo corre el agua bajo el hielo."},
    {"id": "colector_centro", "nombre": "El gran colector", "pos": (1038.0, 1101.0), "radio": 4.0, "ancho": 3.0,
     "rumbo": -42.0, "hondo": 4.2, "causa": "colector", "notas": ""},
    {"id": "agua_juventud", "nombre": "Una tubería reventada en la calle de la Juventud", "pos": (345.0, 452.0),
     "radio": 3.4, "ancho": 2.6, "rumbo": 90.0, "hondo": 2.0, "causa": "agua", "notas": ""},
    {"id": "agua_fabrica", "nombre": "Una tubería reventada en la calle de la Fábrica", "pos": (846.0, 420.0),
     "radio": 4.0, "ancho": 3.0, "rumbo": 90.0, "hondo": 2.3, "causa": "agua", "notas": ""},
    {"id": "agua_hospital", "nombre": "Una tubería reventada frente al hospital", "pos": (340.0, 1002.0),
     "radio": 3.0, "ancho": 2.4, "rumbo": 90.0, "hondo": 1.8, "causa": "agua", "notas": ""},
]

# ---------------------------------------------------------------------------
# Amenazas: territorios, guaridas, patrullas y vigías
# ---------------------------------------------------------------------------
AMENAZAS: list[dict] = [
    {"id": "jauria_a", "nombre": "La Jauría (la de los garajes)", "especie": "jauria", "guarida": (88, 72),
     "territorio": poligono([(0, 40), (330, 40), (380, 220), (360, 340), (345, 680), (0, 700)]),
     "rutina": "Caza al amanecer y al atardecer; de noche duerme en los garajes; de día recorre Los Bloques, la playa y la plaza de la Estación.",
     "notas": "Seis perros guiados por una hembra."},
    {"id": "jauria_b", "nombre": "La segunda jauría (la del parque)", "especie": "jauria", "guarida": (190, 1136),
     "territorio": poligono([(0, 830), (330, 815), (360, 1200), (0, 1200)]),
     "rutina": "Igual que la primera. Baja al hielo a cazar en la orilla del parque; las dos manadas se pelean por la playa.",
     "notas": "Llega en la Fase 6."},
    {"id": "inquilino_a", "nombre": "El Inquilino de Mineros 7", "especie": "inquilino", "guarida": (194, 375),
     "territorio": caja(146, 368, 242, 381).buffer(4), "rutina": "De día quieto en el hueco del ascensor; de noche recorre las plantas.", "notas": ""},
    {"id": "inquilino_b", "nombre": "El Inquilino del Hospital", "especie": "inquilino", "guarida": (500, 1010),
     "territorio": forma_h(500, 1010, 104, 16, 74, 16, 0).buffer(4), "rutina": "Igual. Baja al sótano a comer.", "notas": ""},
    {"id": "inquilino_c", "nombre": "El Inquilino del Hotel Tumán", "especie": "inquilino", "guarida": eje(870, -88),
     "territorio": rect_eje(835, 905, -96, -80).buffer(4), "rutina": "Igual.", "notas": ""},
    {"id": "llamador_a", "nombre": "El Llamador del Mercado", "especie": "llamador", "guarida": eje(232),
     "territorio": poligono([eje(150, -100), eje(330, -100), eje(330, 110), eje(150, 110)]),
     "rutina": "Duerme de día en el vestíbulo de la estación inundada; al anochecer caza en el paso subterráneo y en el mercado.", "notas": ""},
    {"id": "llamador_b", "nombre": "El Llamador del Barranco", "especie": "llamador", "guarida": (690, 1120),
     "territorio": banda(R.BARRANCO, 110.0, puntas="round"),
     "rutina": "Duerme en el arroyo enterrado; de noche baja por el barranco hasta el río.", "notas": "Llega en la Fase 6."},
    {"id": "saqueadores_1", "nombre": "Saqueadores: el Almacén 3", "especie": "saqueadores", "guarida": (1160, 588),
     "territorio": poligono([(848, 300), (1300, 300), (1340, 660), (848, 660)]),
     "rutina": "Salen de día en grupos de tres a saquear y a relevar a los vigías; de noche, encerrados con guardia y fuego.",
     "notas": "Unas diez personas."},
    {"id": "saqueadores_2", "nombre": "Saqueadores: el Comisariado", "especie": "saqueadores", "guarida": eje(837, 230),
     "territorio": poligono([eje(700, 100), eje(1000, 100), eje(1000, 320), eje(700, 320)]),
     "rutina": "Igual. Llevan suministros entre las dos guaridas por el puente hundido.", "notas": "Unas seis personas."},
]
PATRULLAS: list[dict] = [
    {"id": "P1", "nombre": "Relevo del vigía de los Grandes Almacenes", "grupo": "saqueadores_1", "horario": "mañana y tarde",
     "puntos": [(1160, 610), (1228, 600), (1228, 310), (848, 316), (700, 322), (575, 330), eje(190, -60), eje(231, -62)]},
    {"id": "P2", "nombre": "Ruta de suministros entre guaridas", "grupo": "saqueadores_1", "horario": "cada dos días, a mediodía",
     "puntos": [(1160, 610), (862, 615), (760, 606), eje(372), eje(470), eje(545), eje(632), (850, 798), (780, 812), (752, 830),
                (775, 852), (815, 870), eje(700, 64), eje(791, 150), eje(837, 230)]},
    {"id": "P3", "nombre": "Relevo del vigía de la torre", "grupo": "saqueadores_2", "horario": "al amanecer y a mediodía",
     "puntos": [eje(837, 230), eje(791, 150), eje(791, 64), eje(860, 30), eje(940, 20)]},
    {"id": "P4", "nombre": "Ronda del puerto", "grupo": "saqueadores_1", "horario": "de día, cada hora",
     "puntos": [(1160, 610), (1300, 620), (1300, 560), (1228, 520), (1228, 330), (1100, 316), (1000, 316), (1000, 560), (1160, 610)]},
]
VIGIAS: list[dict] = [
    {"id": "vigia_almacenes", "nombre": "Vigía de los Grandes Almacenes", "pos": eje(240, -66), "rumbo": 228.0, "abertura": 160.0, "alcance": 380.0,
     "notas": "Ve la avenida de punta a punta, la plaza y el socavón."},
    {"id": "vigia_elevador", "nombre": "Vigía del elevador de grano", "pos": (1248, 583), "rumbo": 180.0, "abertura": 300.0, "alcance": 420.0,
     "notas": "Ve el puerto, la playa de vías, la fábrica y el hielo."},
    {"id": "vigia_torre", "nombre": "Vigía de la torre de la Casa de los Sóviets", "pos": eje(955), "rumbo": 250.0, "abertura": 140.0, "alcance": 520.0,
     "notas": "Ve el río, los dos puentes, el hielo, la Escalinata y la plaza Central. Solo de día."},
]

# ---------------------------------------------------------------------------
# Peligros del entorno
# ---------------------------------------------------------------------------
RASTRO_RADIACTIVO = [
    {"nivel": 1, "forma": poligono([(1380, 1200), (1600, 1200), (1600, 0), (1330, 0), (1300, 300), (1330, 700)])},
    {"nivel": 2, "forma": poligono([(1440, 1200), (1600, 1200), (1600, 60), (1440, 120), (1420, 500), (1430, 800)])},
    {"nivel": 3, "forma": poligono([(1500, 1200), (1600, 1200), (1600, 200), (1540, 300), (1520, 700), (1490, 900)])},
]
FOCOS_RADIACION = [
    {"nombre": "Morgue del hospital", "pos": (402, 1118), "radio": 25, "nivel": 2},
    {"nombre": "Camiones de bomberos en la plaza Central", "pos": eje(885, -35), "radio": 30, "nivel": 2},
    {"nombre": "Vagones del nudo ferroviario", "pos": (1480, 805), "radio": 70, "nivel": 3},
    {"nombre": "Cubiertas planas del centro (polvo acumulado)", "pos": eje(1050, 0), "radio": 120, "nivel": 1},
    {"nombre": "Sedimentos de la curva del río", "pos": (1350, 694), "radio": 50, "nivel": 2},
    {"nombre": "Tren de la evacuación", "pos": (150, 30), "radio": 40, "nivel": 1},
    {"nombre": "Socavón (agua de lluvia acumulada)", "pos": R.SOCAVON, "radio": 18, "nivel": 2},
]
ZONAS_MASCARA = [
    {"nombre": "Zona Cero: polvo radiactivo", "forma": circulo(*GZ, 330)},
    {"nombre": "Humo del parque de carbón", "forma": elipse(1455, 238, 120, 70, 15)},
    {"nombre": "Estación Plaza Central: aire viciado", "forma": rect_eje(800, 920, -30, 30)},
]
HIELO_FINO = [
    {"nombre": "Junto al puente hundido", "forma": elipse(*eje(508), 70, 40, 48)},
    {"nombre": "Bajo los desagües del puerto", "forma": elipse(1000, 668, 40, 12)},
    {"nombre": "Curva del río junto a la central", "forma": elipse(1420, 640, 60, 18, -10)},
    {"nombre": "Bajo la Autovía caída", "forma": elipse(10, 765, 30, 50)},
]
CRUCES_RIO = [
    {"nombre": "El tubo", "pos": (324, 730), "perfil": "Silencioso, estrecho, con viento. Se ve desde las dos orillas."},
    {"nombre": "El puente hundido", "pos": eje(508), "perfil": "Cuerda para bajar al vano caído y subir por el otro lado. Paso de los saqueadores."},
    {"nombre": "El hielo", "pos": (1050, 718), "perfil": "Rápido y abierto. Lo ven el vigía de la torre y el del elevador."},
    {"nombre": "El puente del ferrocarril", "pos": (1550, 690), "perfil": "Firme, pero dentro del rastro radiactivo."},
    {"nombre": "El túnel inundado", "pos": eje(470), "perfil": "Bajo el río, a oscuras, con el agua al pecho. El Llamador."},
]

# ---------------------------------------------------------------------------
# Límites del mapa (todos tienen una razón dentro del mundo)
# ---------------------------------------------------------------------------
LIMITES = [
    {"lado": "oeste", "nombre": "La Autovía caída", "pos": (14, 600),
     "notas": "Autovía elevada sobre pilares. La onda de la segunda bomba (al suroeste, fuera del mapa) la tiró: una muralla de hormigón y coches de 10 m."},
    {"lado": "sur", "nombre": "El terraplén del ferrocarril", "pos": (700, 22),
     "notas": "Terraplén de 5 m con la valla de hormigón y un tren quemado encima. Detrás, el Barrio Quemado: llano de ceniza sin nada en pie."},
    {"lado": "este", "nombre": "El rastro", "pos": (1588, 400),
     "notas": "Más allá de la vía del este, la lluvia radiactiva cayó entera: dosis mortal en minutos."},
    {"lado": "norte", "nombre": "La muralla de escombros", "pos": (900, 1196),
     "notas": "La onda tumbó los edificios del norte hacia el sur y cegó todas las calles. Más al este, el cráter."},
]

# ---------------------------------------------------------------------------
# Rutas: siempre hay varias para llegar al mismo sitio
# ---------------------------------------------------------------------------
RUTAS: list[dict] = [
    {"id": "R1a", "destino": "Farmacia de Mineros 7", "nombre": "Por la calle", "perfil": "rápida y expuesta", "minutos": 6,
     "puntos": [SALIDA, (320, 330), (250, 340), (170, 352), (165, 368)]},
    {"id": "R1b", "destino": "Farmacia de Mineros 7", "nombre": "Por los patios y el sótano", "perfil": "lenta y segura", "minutos": 14,
     "puntos": [SALIDA, (305, 325), (290, 392), (240, 398), (200, 394), (180, 386), (178, 381)],
     "notas": "Entra por el portal trasero; hay que cruzar el sótano corrido del bloque."},
    {"id": "R1c", "destino": "Farmacia de Mineros 7", "nombre": "Por la galería de la calefacción", "perfil": "a oscuras; exige palanca", "minutos": 12,
     "puntos": [(345, 330), (200, 330), (100, 330), (100, 393), (150, 393), (165, 381)]},
    {"id": "R2a", "destino": "Hospital Nº 3", "nombre": "Por el tubo", "perfil": "silenciosa y expuesta al viento", "minutos": 25,
     "puntos": [SALIDA, (320, 340), (330, 410), (330, 590), (322, 640), (326, 760), (330, 820), (340, 900), (358, 962), (450, 980)]},
    {"id": "R2b", "destino": "Hospital Nº 3", "nombre": "Por el hielo de la playa", "perfil": "rápida, abierta; la segunda jauría", "minutos": 22,
     "puntos": [SALIDA, (300, 340), (230, 420), (200, 600), (200, 670), (190, 760), (200, 830), (300, 900), (358, 962), (450, 980)]},
    {"id": "R2c", "destino": "Hospital Nº 3", "nombre": "Por el puente y el barranco", "perfil": "larga; cruza el paso de los saqueadores", "minutos": 40,
     "puntos": [SALIDA, eje(100), eje(372), eje(470), eje(545), eje(632), (700, 790), (652, 790), (660, 850), (676, 905), (640, 960),
                (600, 1000), (560, 1010)]},
    {"id": "R3a", "destino": "Plaza Central", "nombre": "Por la avenida y la Escalinata", "perfil": "directa; bajo el vigía de la torre", "minutos": 25,
     "puntos": [SALIDA, eje(100, 20), eje(372, 20), eje(470, 10), eje(545, 10), eje(632), eje(800)]},
    {"id": "R3b", "destino": "Plaza Central", "nombre": "Por el túnel inundado", "perfil": "a oscuras, con agua helada; el Llamador", "minutos": 35,
     "puntos": [eje(0), eje(95), eje(180), eje(232), eje(420), eje(508), eje(640), eje(860)]},
    {"id": "R3c", "destino": "Plaza Central", "nombre": "Por el hielo y el barranco", "perfil": "rodeo largo fuera de la vista del vigía", "minutos": 45,
     "puntos": [SALIDA, (345, 400), (345, 600), (500, 614), (620, 640), (630, 720), (645, 790), (660, 850), (690, 960), (700, 1010),
                (742, 1100), (762, 975), (782, 936), eje(700, 64), eje(800, 40)]},
    {"id": "R4a", "destino": "El Edificio Partido", "nombre": "Por el centro", "perfil": "la más corta; la más vigilada", "minutos": 60,
     "puntos": [SALIDA, eje(100, 20), eje(372, 20), eje(470, 10), eje(545, 10), eje(632), eje(800), eje(915, 64), eje(998, 64), eje(998, 0),
                (1180, 1100), (1262, 1092), (1280, 1010), (1292, 985)]},
    {"id": "R4b", "destino": "El Edificio Partido", "nombre": "Por el este", "perfil": "por el puerto y el puente del ferrocarril; mucha radiación", "minutos": 90,
     "puntos": [SALIDA, (512, 326), (850, 312), (1228, 302), (1228, 520), (1340, 560), (1500, 600), (1550, 640), (1548, 760), (1500, 800),
                (1400, 840), (1330, 900), (1300, 960), (1292, 985)]},
    {"id": "R4c", "destino": "El Edificio Partido", "nombre": "Por debajo", "perfil": "metro y colectores; oscura, fría y lenta", "minutos": 100,
     "puntos": [eje(0), eje(232), eje(508), eje(640), eje(860), eje(965, 70), eje(998, 64), (1180, 1100), (1262, 1092), (1292, 985)]},
    {"id": "R4d", "destino": "El Edificio Partido", "nombre": "Por el hielo", "perfil": "abierta; hielo fino junto al puerto", "minutos": 80,
     "puntos": [SALIDA, (512, 326), (848, 312), (862, 615), (1050, 640), (1080, 718), (1100, 790), (1110, 830), (1150, 880), (1200, 905),
                (1245, 930), (1292, 985)]},
    {"id": "R4e", "destino": "El Edificio Partido", "nombre": "Por el oeste", "perfil": "la más larga; la más tranquila hasta el centro", "minutos": 150,
     "puntos": [SALIDA, (320, 340), (330, 590), (326, 760), (340, 900), (340, 1188), (720, 1188), (803, 1198), eje(1003, 184), eje(1088, 64),
                (1240, 1120), (1270, 1040), (1292, 985)]},
]
