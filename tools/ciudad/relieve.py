"""Relieve de Tumansk: el río, las orillas, la loma del centro, el barranco, la
colina del parque y el cráter.

Alturas en metros sobre la cota 0, que es el nivel de la calle en la orilla sur
junto al río. El hielo del río está a -6 m. La orilla norte es alta y empinada
(la ciudad vieja creció encima, como en tantas ciudades rusas) y la orilla sur es
baja y llana (la vega: el puerto, la industria y los microdistritos).
"""

from __future__ import annotations

import numpy as np

# El Tumán corre de este a oeste. Su eje es una función de x.
RIO_EJE = [
    (-60, 769),
    (100, 762),
    (250, 748),
    (400, 728),
    (560, 712),
    (720, 706),
    (880, 712),
    (1040, 720),
    (1200, 712),
    (1350, 694),
    (1480, 676),
    (1660, 648),
]
NIVEL_HIELO = -6.0

# Muros de contención: donde la orilla es un muelle de granito u hormigón y no un talud.
MURO_SUR = (560.0, 1545.0)
MURO_NORTE = (520.0, 1545.0)

# El barranco: baja del centro al río entre el hospital y la ciudad vieja.
BARRANCO = [
    (648, 772),
    (655, 830),
    (668, 880),
    (688, 935),
    (700, 990),
    (698, 1045),
    (688, 1090),
    (680, 1112),
]
BARRANCO_FONDO = [1.0, 1.5, 3.0, 5.0, 6.5, 8.0, 9.0, 9.5]
BARRANCO_MEDIO_ANCHO = [46.0, 46.0, 44.0, 42.0, 40.0, 38.0, 32.0, 24.0]

COLINA = (105.0, 955.0)
CRATER = (1500.0, 1110.0)
CRATER_RADIO = 95.0
SOCAVON = (558.0, 455.0)

_RX = np.array([p[0] for p in RIO_EJE], dtype=float)
_RY = np.array([p[1] for p in RIO_EJE], dtype=float)


def rio_y(x):
    return np.interp(x, _RX, _RY)


def rio_ancho(x):
    return 124.0 - 20.0 * np.clip(np.asarray(x, dtype=float) / 1600.0, 0.0, 1.0)


def orilla_sur(x):
    return rio_y(x) - rio_ancho(x) / 2.0


def orilla_norte(x):
    return rio_y(x) + rio_ancho(x) / 2.0


def _smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _distancia_polilinea(x, y, puntos):
    """Distancia a una polilínea y fracción de su longitud en el punto más cercano."""
    pts = np.asarray(puntos, dtype=float)
    seg = pts[1:] - pts[:-1]
    largo = np.hypot(seg[:, 0], seg[:, 1])
    acumulado = np.concatenate([[0.0], np.cumsum(largo)])
    mejor = np.full(np.shape(x), np.inf)
    fraccion = np.zeros(np.shape(x))
    for i in range(len(seg)):
        ax, ay = pts[i]
        dx, dy = seg[i]
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / (largo[i] ** 2), 0.0, 1.0)
        d = np.hypot(x - (ax + t * dx), y - (ay + t * dy))
        cerca = d < mejor
        mejor = np.where(cerca, d, mejor)
        fraccion = np.where(cerca, (acumulado[i] + t * largo[i]) / acumulado[-1], fraccion)
    return mejor, fraccion


def distancia_polilinea(x, y, puntos):
    return _distancia_polilinea(np.asarray(x, float), np.asarray(y, float), puntos)[0]


def altura_natural(x, y):
    """Relieve sin obras humanas (sin terraplenes ni escombros)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    centro = rio_y(x)
    medio = rio_ancho(x) / 2.0
    sur = centro - medio
    norte = centro + medio

    # --- Orilla sur: la vega sube despacio hacia la vía del tren ---
    vega = np.interp(y, [0, 60, 150, 400, 600, 800], [5.0, 5.0, 4.0, 1.5, 0.0, 0.0])
    tierra_sur = sur - y  # metros tierra adentro desde el borde del agua
    muro_s = (x >= MURO_SUR[0]) & (x <= MURO_SUR[1])
    talud_s = NIVEL_HIELO + (0.0 - NIVEL_HIELO) * _smooth(0.0, 30.0, tierra_sur)
    orilla_s = np.where(muro_s, np.where(tierra_sur > 1.0, 0.0, NIVEL_HIELO), talud_s)
    h_sur = np.minimum(vega, orilla_s)

    # --- Orilla norte: muelle bajo, la loma y la meseta ---
    tierra_norte = y - norte
    pie = np.interp(x, [0, 450, 700, 1350, 1600], [25.0, 25.0, 32.0, 32.0, 30.0])
    cima = np.interp(x, [0, 450, 700, 1350, 1600], [190.0, 165.0, 110.0, 112.0, 120.0])
    meseta = np.interp(x, [0, 450, 700, 1350, 1600], [10.0, 11.0, 12.0, 12.5, 13.0])
    meseta = meseta + 4.0 * np.clip((y - 900.0) / 300.0, 0.0, 1.0)
    loma = 1.0 + (meseta - 1.0) * _smooth(pie, cima, tierra_norte)
    muro_n = (x >= MURO_NORTE[0]) & (x <= MURO_NORTE[1])
    talud_n = NIVEL_HIELO + (1.0 - NIVEL_HIELO) * _smooth(0.0, 22.0, tierra_norte)
    orilla_n = np.where(muro_n, np.where(tierra_norte > 1.0, 1.0, NIVEL_HIELO), talud_n)
    h_norte = np.where(tierra_norte < pie, np.minimum(orilla_n, 1.0), loma)

    h = np.where(y < centro, h_sur, h_norte)
    h = np.where((y >= sur) & (y <= norte), NIVEL_HIELO, h)

    # --- La colina del parque ---
    r = np.hypot(x - COLINA[0], y - COLINA[1])
    h = h + np.where(y > norte, 13.0 * np.exp(-((r / 78.0) ** 2)), 0.0)

    # --- El barranco ---
    d, f = _distancia_polilinea(x, y, BARRANCO)
    marcas = np.linspace(0.0, 1.0, len(BARRANCO))
    fondo = np.interp(f, marcas, BARRANCO_FONDO)
    medio_ancho = np.interp(f, marcas, BARRANCO_MEDIO_ANCHO)
    valle = fondo + (h - fondo) * _smooth(9.0, medio_ancho, d)
    h = np.where(y > norte, np.minimum(h, valle), h)

    # --- El cráter: cuenco y borde levantado ---
    r = np.hypot(x - CRATER[0], y - CRATER[1])
    cuenco = 34.0 * np.clip(1.0 - (r / CRATER_RADIO) ** 2, 0.0, 1.0)
    borde = 7.0 * np.exp(-(((r - CRATER_RADIO - 12.0) / 20.0) ** 2))
    eyecta = 2.0 * np.exp(-(((r - 170.0) / 60.0) ** 2))
    h = h - cuenco + borde + eyecta

    # --- El socavón de la avenida (la calle se hundió en el túnel del metro) ---
    r = np.hypot(x - SOCAVON[0], y - SOCAVON[1])
    h = h - 11.0 * _smooth(15.0, 6.0, r)
    return h


def terraplen(x, y, puntos, alto: float, corona: float, talud: float):
    """Altura que añade un terraplén (de la vía o de un acceso) a lo largo de una polilínea."""
    d = distancia_polilinea(x, y, puntos)
    return alto * (1.0 - _smooth(corona / 2.0, corona / 2.0 + talud, d))


def sombreado(alturas: np.ndarray, resolucion: float, azimut: float = 315.0, elevacion: float = 40.0):
    """Sombreado del relieve (1 = plena luz). Luz del noroeste, como en los mapas clásicos."""
    gy, gx = np.gradient(alturas, resolucion)
    pendiente = np.arctan(np.hypot(gx, gy))
    orientacion = np.arctan2(-gx, gy)
    az = np.radians(360.0 - azimut + 90.0)
    el = np.radians(elevacion)
    luz = np.sin(el) * np.cos(pendiente) + np.cos(el) * np.sin(pendiente) * np.cos(az - orientacion)
    return np.clip(luz, 0.0, 1.0)
